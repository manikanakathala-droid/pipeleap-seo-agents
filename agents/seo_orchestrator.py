from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agents.content_agent import ContentAgent
from agents.growth_agent import GrowthAgent
from connectors.cms_connector import CMSConnector
from connectors.github_publisher import GitHubPublisher
from connectors.crawler import SiteCrawler
from connectors.gsc_connector import GoogleSearchConsoleConnector
from core.analytics_engine import AnalyticsEngine
from core.audit_engine import AuditEngine
from core.backlink_engine import BacklinkEngine
from core.content_engine import ContentEngine
from core.keyword_engine import KeywordEngine
from core.landing_page_engine import LandingPageEngine
from core.linking_engine import LinkingEngine
from utils.logger import configure_logger
from utils.models import RunResult
from utils.storage import SEOStorage
from utils.telemetry import Telemetry
from utils.text import dedupe_preserve_order, slugify


class SEOOrchestrator:
    """Runs Pipeleap's autonomous SEO workflow end to end."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.execution = config.get("execution", {})
        self.site_url = config.get("site", {}).get("site_url", "")
        self.logger = configure_logger(level=self.execution.get("log_level", "INFO"))
        self.storage = SEOStorage(self._resolve_path(self.execution.get("memory_db", "outputs/pipeleap_seo_memory.sqlite")))
        self._resolve_integration_paths(config)

        self.gsc_connector = GoogleSearchConsoleConnector(config, self.logger)
        self.crawler = SiteCrawler(config, self.logger)
        self.cms_connector = CMSConnector(config, self.logger)
        self.keyword_engine = KeywordEngine(config, self.logger)
        self.content_engine = ContentEngine(config, self.logger)
        self.landing_page_engine = LandingPageEngine(config, self.logger)
        self.audit_engine = AuditEngine(config, self.logger)
        self.linking_engine = LinkingEngine(config, self.logger)
        self.backlink_engine = BacklinkEngine(config, self.logger)
        self.analytics_engine = AnalyticsEngine(config, self.logger)
        self.content_agent = ContentAgent(config, self.content_engine, self.logger)
        self.growth_agent = GrowthAgent(config, self.logger)
        self.telemetry = Telemetry(config)
        gh_cfg = config.get("integrations", {}).get("github", {})
        self.github_publisher = GitHubPublisher(
            token=gh_cfg.get("token", ""),
            repo=gh_cfg.get("repo", ""),
            branch=gh_cfg.get("branch", "main"),
            blog_data_path=gh_cfg.get("blog_data_path", "src/data/blog-articles.ts"),
            tools_data_path=gh_cfg.get("tools_data_path", "src/data/tools-data.ts"),
        )

    def run_once(self) -> dict[str, Any]:
        generated_at = datetime.now(timezone.utc).isoformat()
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_directory = self._prepare_run_directory(run_id)
        integration_requests: list[str] = []

        self.telemetry.run_start(run_id, agent_type="seo_agent")

        # ── Stage 1: Crawl ────────────────────────────────────────────────
        crawl_enabled = self.execution.get("crawl_enabled", True)
        try:
            with self.telemetry.timed_stage("crawl", run_id):
                crawl_report = self._crawl_site()
        except Exception as exc:
            self.logger.error("Crawl failed — continuing with empty report: %s", exc)
            from utils.models import CrawlerReport
            crawl_report = CrawlerReport(site_url=self.site_url, pages=[], discovered_at=generated_at)
        if not crawl_enabled:
            integration_requests.append("Live crawl is disabled; technical SEO findings are omitted for this run.")

        # ── Stage 2: GSC data ─────────────────────────────────────────────
        end_date = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        start_date = (datetime.now(timezone.utc).date() - timedelta(days=28)).isoformat()
        try:
            with self.telemetry.timed_stage("gsc_fetch", run_id):
                gsc_rows, gsc_requests = self._fetch_gsc_rows()
            integration_requests.extend(gsc_requests)
        except Exception as exc:
            self.logger.error("GSC fetch failed — continuing without live data: %s", exc)
            self.telemetry.capture_exception(exc, run_id=run_id, stage="gsc_fetch")
            gsc_rows, gsc_requests = [], [f"GSC fetch error: {exc}"]
            integration_requests.extend(gsc_requests)

        # ── Slug deduplication registry ───────────────────────────────────
        existing_slugs = self.storage.fetch_all_asset_slugs()
        cms_dir = self.config.get("integrations", {}).get("cms", {}).get("publish_dir", "")
        if cms_dir:
            cms_path = Path(cms_dir)
            if cms_path.exists():
                for d in cms_path.iterdir():
                    if d.is_dir() and d.name:
                        existing_slugs.add(d.name)
        for page in crawl_report.pages:
            url_slug = page.url.rstrip("/").split("/")[-1]
            if url_slug:
                existing_slugs.add(url_slug)
        self.logger.info("Slug registry: %d total known slugs (SQLite + filesystem)", len(existing_slugs))

        # ── Stage 3: Keyword discovery ────────────────────────────────────
        try:
            with self.telemetry.timed_stage("keyword_discovery", run_id):
                keyword_clusters, keyword_requests = self.keyword_engine.discover(
                    gsc_rows, crawl_report.pages, existing_slugs
                )
            integration_requests.extend(keyword_requests)
        except Exception as exc:
            self.logger.error("Keyword discovery failed: %s", exc)
            self.telemetry.capture_exception(exc, run_id=run_id, stage="keyword_discovery")
            keyword_clusters, keyword_requests = [], []

        gsc_gaps: list[dict[str, Any]] = []
        try:
            gsc_gaps = self.keyword_engine.detect_gsc_gaps(gsc_rows, existing_slugs)
            if gsc_gaps:
                self.logger.info(
                    "GSC content gaps: %d queries have impressions but no targeting page", len(gsc_gaps)
                )
        except Exception as exc:
            self.logger.warning("GSC gap detection failed: %s", exc)

        # ── Stage 4: Content generation ───────────────────────────────────
        landing_pages: list = []
        content_assets: list = []
        try:
            with self.telemetry.timed_stage("landing_pages", run_id):
                landing_pages = self.landing_page_engine.generate(
                    keyword_clusters,
                    limit=self.execution.get("landing_pages_per_run", 5),
                )
        except Exception as exc:
            self.logger.error("Landing page generation failed: %s", exc)
            self.telemetry.capture_exception(exc, run_id=run_id, stage="landing_pages")

        try:
            with self.telemetry.timed_stage("content_generation", run_id):
                content_assets = self.content_agent.generate(keyword_clusters)
        except Exception as exc:
            self.logger.error("Content agent failed: %s", exc)
            self.telemetry.capture_exception(exc, run_id=run_id, stage="content_generation")

        assets = landing_pages + content_assets
        self.telemetry.track_assets(run_id, assets)

        # ── Stage 5: Linking ──────────────────────────────────────────────
        link_suggestions: list = []
        try:
            with self.telemetry.timed_stage("linking", run_id):
                link_suggestions = self.linking_engine.suggest(crawl_report.pages, assets, keyword_clusters)
                self._attach_internal_link_suggestions(assets, link_suggestions)
        except Exception as exc:
            self.logger.warning("Linking engine failed: %s", exc)

        # ── Stage 6: Technical audit ──────────────────────────────────────
        audit_issues: list = []
        try:
            with self.telemetry.timed_stage("technical_audit", run_id):
                audit_issues = self.audit_engine.run(crawl_report) if crawl_enabled else []
        except Exception as exc:
            self.logger.warning("Audit engine failed: %s", exc)

        # ── Stage 7: Backlinks — with storage dedup ───────────────────────
        backlink_opportunities: list = []
        try:
            with self.telemetry.timed_stage("backlinks", run_id):
                backlink_opportunities = self.backlink_engine.build(
                    keyword_clusters,
                    storage=self.storage,
                    run_id=run_id,
                )
        except Exception as exc:
            self.logger.warning("Backlink engine failed: %s", exc)

        # ── Stage 8: Analytics — persists organic metrics ─────────────────
        try:
            with self.telemetry.timed_stage("analytics", run_id):
                analytics_summary, weekly_report = self.analytics_engine.summarize(
                    keyword_clusters,
                    self.storage,
                    gsc_rows,
                    run_id=run_id,
                    period_start=start_date,
                    period_end=end_date,
                )
        except Exception as exc:
            self.logger.error("Analytics failed: %s", exc)
            self.telemetry.capture_exception(exc, run_id=run_id, stage="analytics")
            analytics_summary, weekly_report = {"error": str(exc)}, "# Analytics failed\n"

        # ── Stage 9: Growth plan ──────────────────────────────────────────
        try:
            with self.telemetry.timed_stage("growth_plan", run_id):
                execution_plan, roadmap, content_calendar = self.growth_agent.build_plan(
                    keyword_clusters, audit_issues, link_suggestions, backlink_opportunities, assets
                )
        except Exception as exc:
            self.logger.error("Growth agent failed: %s", exc)
            execution_plan, roadmap, content_calendar = [], [], []

        # ── Stage 10: Publish ─────────────────────────────────────────────
        publish_result: dict[str, Any] = {}
        try:
            with self.telemetry.timed_stage("cms_publish", run_id):
                publish_result = self.cms_connector.publish_assets(run_directory, assets)
        except Exception as exc:
            self.logger.error("CMS publish failed: %s", exc)
            publish_result = {"error": str(exc)}

        # ── Stage 10b: GitHub publish ─────────────────────────────────────
        if self.github_publisher.is_configured():
            for asset in assets:
                if getattr(asset, "page_type", "") == "blog_post":
                    self.github_publisher.publish_blog_post(asset)

        # ── Stage 11: Post-publish URL validation ─────────────────────────
        publish_validation: list[dict[str, Any]] = []
        try:
            with self.telemetry.timed_stage("publish_validation", run_id):
                publish_validation = self._validate_published_urls(assets)
        except Exception as exc:
            self.logger.warning("Post-publish URL validation failed: %s", exc)

        # ── Assemble report ───────────────────────────────────────────────
        report = RunResult(
            site=self.site_url,
            generated_at=generated_at,
            seo_growth_opportunities=keyword_clusters,
            execution_plan=execution_plan,
            assets_generated=assets,
            audit_issues=audit_issues,
            internal_links=link_suggestions,
            backlink_opportunities=backlink_opportunities,
            analytics_summary={
                **analytics_summary,
                "publish_result": publish_result,
                "publish_validation": publish_validation,
            },
            roadmap_30_day=roadmap,
            content_calendar=content_calendar,
            integration_requests=dedupe_preserve_order(integration_requests),
            output_directory=run_directory,
        )

        report_dict = report.to_dict()
        self._write_outputs(run_directory, report_dict, weekly_report, crawl_report.to_dict())
        if gsc_gaps:
            Path(run_directory).joinpath("gsc_content_gaps.json").write_text(
                json.dumps(gsc_gaps[:50], indent=2), encoding="utf-8"
            )
        self._persist_run(run_id, generated_at, keyword_clusters, assets, report_dict)

        self.logger.info(
            "Run %s complete — %d assets, %d issues, %d backlinks, %d decay signals",
            run_id, len(assets), len(audit_issues), len(backlink_opportunities),
            len(analytics_summary.get("decay_signals", [])),
        )

        # Emit final run telemetry and flush before returning
        self.telemetry.run_complete(
            run_id=run_id,
            analytics_summary=analytics_summary,
            assets=assets,
            audit_issues=audit_issues,
            backlink_opportunities=backlink_opportunities,
        )
        self.telemetry.flush()

        return report_dict

    def run_forever(self, interval_minutes: int, max_consecutive_failures: int = 3) -> None:
        import signal
        import threading
        
        shutdown = threading.Event()
        
        def signal_handler(signum, frame):
            self.logger.info("Shutdown signal received")
            shutdown.set()
            
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        self.logger.info("Starting continuous SEO mode with %s minute intervals", interval_minutes)
        consecutive_failures = 0
        while not shutdown.is_set():
            try:
                self.run_once()
                consecutive_failures = 0
            except Exception as exc:  # pragma: no cover
                consecutive_failures += 1
                self.logger.exception("Scheduled run failed (%d/%d): %s", consecutive_failures, max_consecutive_failures, exc)
                if consecutive_failures >= max_consecutive_failures:
                    self.logger.critical("Circuit breaker triggered — stopping continuous mode")
                    break
            shutdown.wait(timeout=max(interval_minutes, 1) * 60)

    def _crawl_site(self):
        if not self.execution.get("crawl_enabled", True):
            self.logger.info("Site crawl disabled by configuration")
            from utils.models import CrawlerReport

            return CrawlerReport(site_url=self.site_url, pages=[], discovered_at=datetime.now(timezone.utc).isoformat())
        return self.crawler.crawl(
            self.site_url,
            max_pages=self.execution.get("max_pages", 25),
            max_depth=self.execution.get("max_depth", 2),
        )

    def _validate_published_urls(self, assets: list) -> list[dict[str, Any]]:
        """
        Spot-checks a sample of published URLs to verify they return HTTP 200.
        Handles all page types: blog, glossary, tool, landing, comparison, use-case.
        Logs failures — does not block the run.
        """
        import urllib.request
        site_url = self.site_url.rstrip("/")
        _PAGE_PATH = {
            "blog_post": "/blog/",
            "glossary_term": "/glossary/",
            "glossary_page": "/glossary/",
            "tool": "/tools/",
            "tool_category": "/tools/",
            "landing_page": "/",
            "comparison_page": "/blog/",
            "use_case_page": "/",
        }
        results: list[dict[str, Any]] = []
        checked = 0
        for asset in assets:
            if checked >= 5:
                break
            if not asset.slug or asset.uniqueness_score == 0.0:
                continue
            prefix = _PAGE_PATH.get(getattr(asset, "page_type", ""), "/")
            url = f"{site_url}{prefix}{asset.slug}"
            try:
                req = urllib.request.Request(url, method="HEAD")
                with urllib.request.urlopen(req, timeout=6) as resp:
                    status = resp.status
            except Exception as exc:
                status = 0
                self.logger.warning("Post-publish check FAIL %s — %s", url, exc)
            results.append({"url": url, "status": status, "ok": status == 200})
            checked += 1
        ok_count = sum(1 for r in results if r["ok"])
        if results:
            self.logger.info(
                "Post-publish validation: %d/%d URLs returned 200", ok_count, len(results)
            )
        return results

    def _fetch_gsc_rows(self) -> tuple[list[dict[str, Any]], list[str]]:
        end_date = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        start_date = (datetime.now(timezone.utc).date() - timedelta(days=28)).isoformat()
        # GSC API maximum is 25,000 rows per request — use the full limit so
        # long-tail keywords are included in organic metrics and content decisions.
        return self.gsc_connector.fetch_query_data(start_date=start_date, end_date=end_date, row_limit=25000)

    def _attach_internal_link_suggestions(self, assets, suggestions) -> None:
        site_root = self.site_url.rstrip("/")
        asset_map = {f"{site_root}/{asset.slug}".rstrip("/"): asset for asset in assets}
        for suggestion in suggestions:
            asset = asset_map.get(suggestion.source_url.rstrip("/"))
            if asset:
                asset.internal_link_suggestions.append(suggestion)

    def _persist_run(self, run_id: str, created_at: str, keyword_clusters, assets, report_dict: dict[str, Any]) -> None:
        opportunities = [item for cluster in keyword_clusters for item in cluster.opportunities]
        self.storage.save_keyword_snapshots(run_id, created_at, opportunities)
        self.storage.save_assets(run_id, created_at, assets)
        self.storage.save_run_report(run_id, created_at, report_dict)

    def _write_outputs(
        self,
        run_directory: str,
        report_dict: dict[str, Any],
        weekly_report: str,
        crawl_report: dict[str, Any],
    ) -> None:
        output_root = Path(run_directory)
        (output_root / "report.json").write_text(json.dumps(report_dict, indent=2), encoding="utf-8")
        (output_root / "weekly_report.md").write_text(weekly_report, encoding="utf-8")
        (output_root / "crawl_report.json").write_text(json.dumps(crawl_report, indent=2), encoding="utf-8")

    def _prepare_run_directory(self, run_id: str) -> str:
        output_root = Path(self._resolve_path(self.execution.get("output_dir", "outputs")))
        run_directory = output_root / run_id
        run_directory.mkdir(parents=True, exist_ok=True)
        return str(run_directory)

    def _resolve_integration_paths(self, config: dict[str, Any]) -> None:
        """Convert relative integration file paths to absolute so connectors work regardless of CWD."""
        gsc = config.get("integrations", {}).get("gsc", {})
        for key in ("credentials_path", "data_export_path"):
            if gsc.get(key):
                gsc[key] = self._resolve_path(gsc[key])
        analytics = config.get("integrations", {}).get("analytics", {})
        for key in ("credentials_path", "conversion_export_path"):
            if analytics.get(key):
                analytics[key] = self._resolve_path(analytics[key])

    def _resolve_path(self, path_value: str) -> str:
        path = Path(path_value)
        if path.is_absolute():
            return str(path)
        return str((Path(__file__).resolve().parent.parent / path).resolve())
