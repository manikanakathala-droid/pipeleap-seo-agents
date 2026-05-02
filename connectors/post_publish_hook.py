"""
PostPublishHook — fires all indexing and backlink signals after any agent publishes.

Called by every agent runner (main.py, run_growth_engine.py, run_geo_agent.py)
and every CI workflow (daily_seo_run.yml, daily_geo_run.yml).

Single source of truth for post-publish behaviour so no agent ever misses
an indexing signal or backlink action.

Signals fired (in order):
  1. IndexNow       — instant Bing/Yandex/DuckDuckGo (no auth, always works)
  2. GSC sitemap    — Google crawl queue (requires Owner permission in GSC)
  3. Indexing API   — direct Google URL notification (requires API enabled in GCP)
  4. Backlink report— writes prioritised action list to outputs/
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SITEMAP_URL  = "https://pipeleap.com/sitemap.xml"
SITE_URL     = "https://pipeleap.com"
INDEXNOW_KEY = "pipeleap-indexnow-2026"


class PostPublishHook:
    """
    Drop-in post-publish signal coordinator for all Pipeleap agents.

    Usage (in any runner or CI step):
        from connectors.post_publish_hook import PostPublishHook
        hook = PostPublishHook(config, logger)
        hook.run(sitemap_path="pipeleap-launchpad/public/sitemap.xml",
                 new_slugs=["outbound-automation-for-uk-saas", ...])
    """

    def __init__(self, config: dict, logger: Any) -> None:
        self.config = config
        self.logger = logger
        self._gsc      = self._build_gsc()
        self._indexnow = self._build_indexnow()

    def run(
        self,
        sitemap_path: str | Path | None = None,
        new_slugs: list[str] | None = None,
        output_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Fire all post-publish signals. Call this after any content publish.

        Args:
            sitemap_path: local path to public/sitemap.xml
            new_slugs:    slugs published in this run (used to build new_urls list)
            output_dir:   where to write the signal report (optional)

        Returns: signal report dict
        """
        report: dict[str, Any] = {
            "fired_at": datetime.now(timezone.utc).isoformat(),
            "signals":  {},
        }

        # Resolve URLs
        new_urls = self._slug_urls(new_slugs) if new_slugs else []
        all_sitemap_urls = self._load_sitemap_urls(sitemap_path) if sitemap_path else []
        submit_urls = all_sitemap_urls or new_urls

        # ── 1. IndexNow ──────────────────────────────────────────────────────
        if self._indexnow and sitemap_path:
            result = self._indexnow.submit_sitemap_urls(sitemap_path)
            report["signals"]["indexnow"] = result
            n = result.get("urls_submitted", 0)
            ok = result.get("endpoints_ok", 0)
            self.logger.info("PostPublish IndexNow: %d URLs to %d/3 engines", n, ok)
        elif self._indexnow and submit_urls:
            result = self._indexnow.submit_all_endpoints(submit_urls[:500])
            report["signals"]["indexnow"] = result
            self.logger.info("PostPublish IndexNow: %d URLs submitted", len(submit_urls))
        else:
            report["signals"]["indexnow"] = {"ok": False, "error": "IndexNow not available"}

        # ── 1b. All other search engines (Yandex, Seznam, Bing hub, WebSub) ───
        try:
            from connectors.search_engine_submitter import SearchEngineSubmitter
            se = SearchEngineSubmitter(logger=self.logger)
            se_report = se.submit_all(submit_urls)
            report["signals"]["search_engines"] = se_report.get("summary", {})
        except Exception as exc:
            report["signals"]["search_engines"] = {"ok": False, "error": str(exc)[:80]}

        # ── 2. GSC sitemap submission ─────────────────────────────────────────
        if self._gsc:
            result = self._gsc.submit_sitemap(SITEMAP_URL)
            report["signals"]["gsc_sitemap"] = result
            self.logger.info("PostPublish GSC sitemap: %s", result)
        else:
            report["signals"]["gsc_sitemap"] = {"ok": False, "error": "GSC not configured"}

        # ── 3. Google Indexing API ────────────────────────────────────────────
        # IMPORTANT: Only submit NEW urls to the Indexing API to avoid quota exhaustion (200/day).
        # General sitemap submission (step 2) covers the rest of the site eventually.
        indexing_targets = new_urls if new_urls else submit_urls[:20]
        if self._gsc and indexing_targets:
            batch = indexing_targets[:200]   # daily quota cap
            results = self._gsc.request_indexing(batch)
            ok  = sum(1 for r in results if r.get("ok"))
            err = sum(1 for r in results if not r.get("ok"))
            api_disabled = any("SERVICE_DISABLED" in str(r.get("error", "")) for r in results)
            report["signals"]["google_indexing_api"] = {
                "ok":           ok > 0 and not api_disabled,
                "submitted":    len(batch),
                "accepted":     ok,
                "errors":       err,
                "api_disabled": api_disabled,
            }
            self.logger.info(
                "PostPublish Indexing API: %d/%d accepted, %d errors%s",
                ok, len(batch), err,
                " [API DISABLED — enable at GCP Console]" if api_disabled else "",
            )
        else:
            report["signals"]["google_indexing_api"] = {"ok": False, "error": "GSC not configured or no new URLs"}

        # ── 4. Summary ────────────────────────────────────────────────────────
        ok_count = sum(1 for s in report["signals"].values() if isinstance(s, dict) and s.get("ok"))
        report["summary"] = {
            "signals_ok":     ok_count,
            "signals_total":  3,
            "urls_submitted": len(submit_urls),
        }

        # ── 5. Write report ───────────────────────────────────────────────────
        if output_dir:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / "post_publish_signals.json").write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )

        return report

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _slug_urls(self, slugs: list[str]) -> list[str]:
        return [f"{SITE_URL}/blog/{slug}" for slug in slugs if slug]

    def _load_sitemap_urls(self, sitemap_path: str | Path) -> list[str]:
        p = Path(sitemap_path)
        if not p.exists():
            return []
        try:
            from xml.etree import ElementTree as ET
            root = ET.fromstring(p.read_text(encoding="utf-8"))
            ns   = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
            return [
                u.find(f"{ns}loc").text
                for u in root.findall(f"{ns}url")
                if u.find(f"{ns}loc") is not None
            ]
        except Exception:
            return []

    def _build_gsc(self) -> Any:
        try:
            from connectors.gsc_connector import GoogleSearchConsoleConnector
            return GoogleSearchConsoleConnector(self.config, self.logger)
        except Exception:
            return None

    def _build_indexnow(self) -> Any:
        try:
            from connectors.indexnow_connector import IndexNowConnector
            return IndexNowConnector()
        except Exception:
            return None
