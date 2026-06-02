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


INDEXNOW_KEY = "92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55"

def _site_url_from_config(config: dict) -> str:
    return config.get("site", {}).get("site_url", "https://www.pipeleap.com").rstrip("/")

def _sitemap_url_from_config(config: dict) -> str:
    return _site_url_from_config(config) + "/sitemap.xml"


class PostPublishHook:
    """
    Drop-in post-publish signal coordinator for all Pipeleap agents.

    Usage (in any runner or CI step):
        from connectors.post_publish_hook import PostPublishHook
        hook = PostPublishHook(config, logger)
        hook.run(sitemap_path="pipeleap-launchpad/public/sitemap.xml",
                 new_slugs=["outbound-automation-for-uk-saas", ...])
    """

    def __init__(self, config: dict, logger: Any, submitted_today: set[str] | None = None) -> None:
        self.config = config
        self.logger = logger
        self.site_url = _site_url_from_config(config)
        self.sitemap_url = _sitemap_url_from_config(config)
        self._gsc      = self._build_gsc()
        self._indexnow = self._build_indexnow()
        self.submitted_today: set[str] = submitted_today or set()

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
        # ── Dedup: filter out URLs already submitted today ─────────────────
        fresh_new_urls = [u for u in new_urls if u not in self.submitted_today]
        self.submitted_today.update(fresh_new_urls)
        self.logger.info("PostPublish: %d new URLs after dedup (%d already submitted today)",
                         len(fresh_new_urls), len(new_urls) - len(fresh_new_urls))

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

        # ── 1b. WebSub only (IndexNow covers Bing/Yandex/Seznam already above) ──
        try:
            import requests as _req
            r = _req.post("https://pubsubhubbub.appspot.com/",
                data={"hub.mode": "publish", "hub.url": self.sitemap_url}, timeout=10)
            report["signals"]["websub"] = {"ok": r.status_code == 204, "status": r.status_code}
            self.logger.info("WebSub: %s (%d)", "OK" if r.status_code == 204 else "FAIL", r.status_code)
        except Exception as exc:
            report["signals"]["websub"] = {"ok": False, "error": str(exc)[:80]}

        # ── 2. GSC sitemap submission ─────────────────────────────────────────
        if self._gsc:
            result = self._gsc.submit_sitemap(self.sitemap_url)
            report["signals"]["gsc_sitemap"] = result
            self.logger.info("PostPublish GSC sitemap: %s", result)
        else:
            report["signals"]["gsc_sitemap"] = {"ok": False, "error": "GSC not configured"}

        # ── 3. Google Indexing API ────────────────────────────────────────────
        # IMPORTANT: Only submit NEW urls to the Indexing API to avoid quota exhaustion (200/day).
        # General sitemap submission (step 2) covers the rest of the site eventually.
        indexing_targets = fresh_new_urls if fresh_new_urls else (submit_urls if not new_urls else [])[:20]
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

    def _slug_urls(self, slugs_or_assets: list[str | dict]) -> list[str]:
        _PATH_MAP = {
            "blog_post": "/blog/",
            "glossary_term": "/glossary/",
            "glossary_page": "/glossary/",
            "tool": "/tools/",
            "tool_category": "/tools/",
            "landing_page": "/",
            "comparison_page": "/blog/",
            "use_case_page": "/",
            "role_page": "/",
            "integration_page": "/",
            "workflow_page": "/",
            "bofu_page": "/",
            "objection_page": "/",
        }
        urls: list[str] = []
        for item in slugs_or_assets:
            if isinstance(item, dict):
                slug = item.get("slug", "")
                if not slug:
                    continue
                ptype = item.get("page_type", "blog_post") or "blog_post"
                prefix = _PATH_MAP.get(ptype, "/")
                urls.append(f"{self.site_url}{prefix}{slug}")
            elif item:
                urls.append(f"{self.site_url}/blog/{item}")
        return urls

    def _load_sitemap_urls(self, sitemap_path: str | Path) -> list[str]:
        p = Path(sitemap_path)
        if not p.exists():
            return []
        try:
            from xml.etree import ElementTree as ET
            ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
            root = ET.fromstring(p.read_text(encoding="utf-8"))
            urls: list[str] = []
            if root.tag == f"{ns}sitemapindex":
                parent_dir = p.parent
                for sm in root.findall(f"{ns}sitemap"):
                    loc = sm.find(f"{ns}loc")
                    if loc is not None and loc.text:
                        sub_filename = loc.text.rstrip("/").rsplit("/", 1)[-1]
                        sub_path = parent_dir / sub_filename
                        if sub_path.exists():
                            urls.extend(self._load_sitemap_urls(sub_path))
            elif root.tag == f"{ns}urlset":
                urls = [
                    u.find(f"{ns}loc").text
                    for u in root.findall(f"{ns}url")
                    if u.find(f"{ns}loc") is not None and u.find(f"{ns}loc").text
                ]
            return urls
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
