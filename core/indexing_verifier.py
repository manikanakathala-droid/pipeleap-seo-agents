"""
IndexingVerifier — verifies that indexing signals actually landed after content publish.

Features:
- Tracks submitted_urls set per run — never re-submits a URL within the same cycle
- 3x retry with exponential backoff (2s, 4s, 8s) on each channel
- Post-submit GSC Inspection API check for newly submitted URLs
- Generates indexing_verification_report.json
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

SUBMITTED_URLS_FILE = "outputs/submitted_urls.json"


class IndexingVerifier:
    def __init__(
        self,
        config: dict,
        logger: Any = None,
        gsc=None,
        indexnow=None,
    ):
        self.config = config
        self.logger = logger or log
        self.site_url = config.get("site", {}).get("site_url", "https://www.pipeleap.com").rstrip("/")
        self._gsc = gsc
        self._indexnow = indexnow
        self.submitted_urls: set[str] = self._load_submitted_urls()

    def verify_post_publish(
        self,
        post_publish_report: dict[str, Any],
        new_urls: list[str],
        sitemap_path: str | None = None,
        output_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Verify that indexing signals landed. Retries failed channels 3x.
        Only inspects URLs not already verified in this cycle.

        Args:
            post_publish_report: output from PostPublishHook.run()
            new_urls: list of newly published URLs
            sitemap_path: path to local sitemap XML (for IndexNow retry)
            output_dir: where to write verification report
        """
        report: dict[str, Any] = {
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "channels": {},
            "new_urls_inspected": [],
            "overall_ok": True,
        }

        signals = post_publish_report.get("signals", {})
        has_signals = bool(signals)

        # ── 1. Verify IndexNow ─────────────────────────────────────────────
        channel = "indexnow"
        indexnow_result = signals.get("indexnow", {})
        indexnow_fixed = self._retry_channel(
            channel, indexnow_result,
            retry_fn=lambda: self._retry_indexnow(sitemap_path, new_urls),
            allow_retry=has_signals,
        )
        report["channels"][channel] = indexnow_fixed

        # ── 2. Verify WebSub ───────────────────────────────────────────────
        channel = "websub"
        websub_result = signals.get("websub", {})
        websub_fixed = self._retry_channel(
            channel, websub_result,
            retry_fn=lambda: self._retry_websub(),
            allow_retry=has_signals,
        )
        report["channels"][channel] = websub_fixed

        # ── 3. Verify GSC Sitemap ──────────────────────────────────────────
        channel = "gsc_sitemap"
        gsc_result = signals.get("gsc_sitemap", {})
        gsc_fixed = self._retry_channel(
            channel, gsc_result,
            retry_fn=lambda: self._retry_gsc_sitemap(),
            allow_retry=has_signals,
        )
        report["channels"][channel] = gsc_fixed

        # ── 4. Verify Google Indexing API ──────────────────────────────────
        channel = "google_indexing_api"
        indexing_result = signals.get("google_indexing_api", {})
        indexing_fixed = self._retry_channel(
            channel, indexing_result,
            retry_fn=lambda: self._retry_indexing_api(new_urls),
            allow_retry=has_signals,
        )
        report["channels"][channel] = indexing_fixed

        # ── 5. Post-submit GSC Inspection (only for newly submitted URLs) ──
        urls_to_inspect = [u for u in new_urls if u not in self.submitted_urls]
        if urls_to_inspect and self._gsc:
            self.logger.info("Verifier: inspecting %d new URLs via GSC API", len(urls_to_inspect))
            inspected = []
            for url in urls_to_inspect[:5]:
                try:
                    insp = self._gsc.inspect_url(url)
                    if isinstance(insp, dict):
                        insp["url"] = url
                        inspected.append(insp)
                    self.submitted_urls.add(url)
                except Exception as exc:
                    inspected.append({"url": url, "ok": False, "error": str(exc)[:100]})
                time.sleep(0.3)
            report["new_urls_inspected"] = inspected
        else:
            report["new_urls_inspected"] = []

        # ── 6. Overall status ──────────────────────────────────────────────
        all_ok = True
        any_failed = False
        for ch, res in report["channels"].items():
            ok = res.get("ok") if isinstance(res, dict) else None
            if ok is False:
                all_ok = False
                any_failed = True
            elif ok is None:
                all_ok = None
        report["overall_ok"] = all_ok if all_ok is not None else (not any_failed if any_failed else None)

        self._save_submitted_urls()

        if output_dir:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / "indexing_verification_report.json").write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )

        return report

    # ── Submitted-urls persistence (shared with PostPublishHook) ─────────

    def _load_submitted_urls(self) -> set[str]:
        try:
            p = Path(SUBMITTED_URLS_FILE)
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return set(data)
        except Exception:
            pass
        return set()

    def _save_submitted_urls(self) -> None:
        try:
            p = Path(SUBMITTED_URLS_FILE)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(sorted(self.submitted_urls), indent=2), encoding="utf-8")
        except Exception as exc:
            self.logger.warning("IndexingVerifier: failed to persist submitted_urls: %s", exc)

    # ── Per-channel retry ─────────────────────────────────────────────────

    def _retry_channel(self, name: str, initial_result: dict, retry_fn, allow_retry: bool = True) -> dict:
        # Already succeeded — no retry needed
        if isinstance(initial_result, dict) and initial_result.get("ok", False):
            return {"ok": True, "source": "initial", **initial_result}

        # No signal was attempted in this cycle — skip retry entirely
        if not allow_retry or not initial_result:
            return {"ok": None, "source": "not_attempted", "note": "no post-publish data to verify"}

        # Initial failed — retry with exponential backoff (2s, 4s, 8s)
        delays = [2, 4, 8]
        for attempt, delay in enumerate(delays, 1):
            self.logger.info("Verifier retry %s attempt %d/%d (wait %ds)", name, attempt, len(delays), delay)
            time.sleep(delay)
            try:
                result = retry_fn()
                if isinstance(result, dict) and result.get("ok", False):
                    return {"ok": True, "source": f"retry_{attempt}", **result}
            except Exception as exc:
                self.logger.warning("Verifier retry %s attempt %d failed: %s", name, attempt, exc)

        return {"ok": False, "source": "all_retries_failed", **initial_result}

    def _retry_indexnow(self, sitemap_path: str | None, new_urls: list[str]) -> dict:
        if self._indexnow and sitemap_path:
            result = self._indexnow.submit_sitemap_urls(sitemap_path)
            return result if isinstance(result, dict) else {"ok": False}
        if self._indexnow and new_urls:
            fresh = [u for u in new_urls if u not in self.submitted_urls]
            if fresh:
                result = self._indexnow.submit_all_endpoints(fresh[:500])
                self.submitted_urls.update(fresh)
                return result if isinstance(result, dict) else {"ok": False}
        return {"ok": False, "error": "IndexNow not available"}

    def _retry_websub(self) -> dict:
        try:
            import requests
            sitemap_url = f"{self.site_url}/sitemap.xml"
            r = requests.post(
                "https://pubsubhubbub.appspot.com/",
                data={"hub.mode": "publish", "hub.url": sitemap_url},
                timeout=10,
            )
            return {"ok": r.status_code == 204, "status": r.status_code}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:80]}

    def _retry_gsc_sitemap(self) -> dict:
        if self._gsc:
            result = self._gsc.submit_sitemap(f"{self.site_url}/sitemap.xml")
            return result if isinstance(result, dict) else {"ok": False, "error": "invalid gsc response"}
        return {"ok": False, "error": "GSC not configured"}

    def _retry_indexing_api(self, new_urls: list[str]) -> dict:
        fresh = [u for u in new_urls if u not in self.submitted_urls]
        if not fresh:
            return {"ok": True, "submitted": 0, "note": "all URLs already submitted"}
        if self._gsc:
            batch = fresh[:200]
            results = self._gsc.request_indexing(batch)
            ok = sum(1 for r in results if r.get("ok"))
            self.submitted_urls.update(batch)
            return {
                "ok": ok > 0,
                "submitted": len(batch),
                "accepted": ok,
                "errors": len(batch) - ok,
            }
        return {"ok": False, "error": "GSC not configured"}
