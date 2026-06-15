from __future__ import annotations

"""
Snapshot Engine — Step 1 of the SEO OS.

Crawls or simulates the site and captures a full SEO attribute snapshot
per page. Persists snapshots to storage so the diff engine can compare
current vs previous state on every run.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
import hashlib
import json


@dataclass
class PageSEOState:
    url: str
    title: str = ""
    meta_description: str = ""
    h1: str = ""
    h2s: list[str] = field(default_factory=list)
    word_count: int = 0
    internal_links: list[str] = field(default_factory=list)
    external_links: list[str] = field(default_factory=list)
    canonical: str = ""
    meta_robots: str = ""
    has_schema: bool = False
    schema_types: list[str] = field(default_factory=list)
    in_sitemap: bool = False
    status_code: int = 200
    response_time_ms: int = 0
    content_hash: str = ""
    captured_at: str = ""

    def fingerprint(self) -> str:
        key = "|".join([self.title, self.meta_description, self.h1, str(self.word_count), self.content_hash])
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SiteSnapshot:
    run_id: str
    site_url: str
    captured_at: str
    pages: list[PageSEOState] = field(default_factory=list)
    total_pages: int = 0
    sitemap_urls: list[str] = field(default_factory=list)
    robots_present: bool = False
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "site_url": self.site_url,
            "captured_at": self.captured_at,
            "total_pages": self.total_pages,
            "sitemap_urls": self.sitemap_urls,
            "robots_present": self.robots_present,
            "pages": [p.to_dict() for p in self.pages],
            "errors": self.errors,
        }

    def page_index(self) -> dict[str, PageSEOState]:
        return {p.url: p for p in self.pages}


class SnapshotEngine:
    """
    Captures a full per-page SEO state snapshot on each run.
    Wraps the existing crawler; enriches with schema detection, word count,
    link counts, sitemap membership.
    """

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger
        self.site_url = config.get("site", {}).get("site_url", "https://www.pipeleap.com").rstrip("/")
        self.max_pages = config.get("execution", {}).get("max_crawl_pages", 80)

    def capture(self, run_id: str, previous_snapshot: SiteSnapshot | None = None) -> SiteSnapshot:
        now = datetime.now(timezone.utc).isoformat()

        crawl_enabled = self.config.get("execution", {}).get("crawl_enabled", True)
        if not crawl_enabled:
            self.logger.info("Crawl disabled by config — using synthetic snapshot")
            snap = self._synthetic_snapshot(run_id, now)
            snap.is_synthetic = True  # type: ignore[attr-defined]
            return snap

        snapshot = SiteSnapshot(run_id=run_id, site_url=self.site_url, captured_at=now)

        try:
            from connectors.crawler import SiteCrawler
            crawler = SiteCrawler(self.config, self.logger)
            crawl_report = crawler.crawl(self.site_url, max_pages=self.max_pages)
            sitemap_urls = crawl_report.sitemap_urls or []
            snapshot.robots_present = crawl_report.robots_txt_present
            snapshot.sitemap_urls = sitemap_urls
            snapshot.crawl_report = crawl_report  # type: ignore[attr-defined]
            sitemap_set = set(sitemap_urls)

            for page in crawl_report.pages[: self.max_pages]:
                schema_types = page.schema_types or []
                state = PageSEOState(
                    url=page.url,
                    title=page.title or "",
                    meta_description=page.meta_description or "",
                    h1=page.h1 or "",
                    h2s=getattr(page, "h2s", []),
                    word_count=page.word_count,
                    internal_links=page.internal_links or [],
                    external_links=getattr(page, "external_links", []),
                    canonical=page.canonical or "",
                    meta_robots=page.meta_robots or "",
                    has_schema=bool(schema_types),
                    schema_types=schema_types,
                    in_sitemap=page.url in sitemap_set,
                    status_code=page.status_code,
                    response_time_ms=page.response_time_ms,
                    content_hash=page.content_hash or "",
                    captured_at=now,
                )
                snapshot.pages.append(state)

        except Exception as exc:
            import traceback
            tb = traceback.format_exc()
            self.logger.warning("Crawler unavailable, using synthetic snapshot\n  type=%s\n  msg=%s\n  traceback=%s", type(exc).__name__, exc, tb)
            snapshot = self._synthetic_snapshot(run_id, now)
            snapshot.is_synthetic = True  # type: ignore[attr-defined]
            snapshot.crawl_diagnostics = {"error_type": type(exc).__name__, "error_msg": str(exc)}  # type: ignore[attr-defined]

        snapshot.total_pages = len(snapshot.pages)
        self.logger.info("Snapshot captured: %d pages, %d sitemap URLs", snapshot.total_pages, len(snapshot.sitemap_urls))
        return snapshot

    def _synthetic_snapshot(self, run_id: str, now: str) -> SiteSnapshot:
        """Fallback: build snapshot from known Pipeleap page structure."""
        known_pages = [
            ("/",                  "Pipeleap - Outbound Sales Automation & Sales Ops",             "outbound sales automation"),
            ("/about",             "About Pipeleap - Sales Orchestration That Learns",             "about pipeleap"),
            ("/sales-ops-audit",   "Free Sales Ops Audit | Pipeleap",                             "sales ops audit"),
            ("/faq",               "Outbound Sales Automation FAQ - Pipeleap",                     "faq"),
            ("/pricing",           "Outbound Sales Automation Pricing | Pipeleap",                 "pricing"),
            ("/blog",              "Blog | Pipeleap",                                               "blog"),
            ("/glossary",          "Outbound Sales Glossary | Pipeleap",                           "glossary"),
            ("/contact",           "Contact Pipeleap",                                             "contact"),
            ("/how-it-works",      "How Pipeleap Works",                                           "how it works"),
            ("/services",          "Outbound Sales Services | Pipeleap",                           "services"),
        ]
        base = self.site_url.rstrip("/")
        pages = []
        for path, title, topic in known_pages:
            pages.append(PageSEOState(
                url=f"{base}{path}",
                title=title,
                h1=title.split("|")[0].strip(),
                word_count=600,
                in_sitemap=True,
                status_code=200,
                captured_at=now,
            ))
        snap = SiteSnapshot(run_id=run_id, site_url=base, captured_at=now)
        snap.pages = pages
        snap.total_pages = len(pages)
        snap.robots_present = True
        snap.sitemap_urls = [f"{base}{p}" for p, _, _ in known_pages]
        return snap
