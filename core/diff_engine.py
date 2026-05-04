from __future__ import annotations

"""
Diff Engine — Step 2 of the SEO OS.

Compares the current site snapshot against the previous run's snapshot
and produces a structured change report. The Adaptive Action Engine
reads this diff to decide what to execute next.
"""

from dataclasses import dataclass, field
from typing import Any

from core.snapshot_engine import SiteSnapshot, PageSEOState


@dataclass
class PageChange:
    url: str
    change_type: str          # "new" | "updated" | "deleted" | "unchanged"
    fields_changed: list[str] = field(default_factory=list)
    previous: dict = field(default_factory=dict)
    current: dict = field(default_factory=dict)
    severity: str = "info"    # "critical" | "warning" | "info"
    action_hint: str = ""


@dataclass
class SiteDiff:
    run_id: str
    previous_run_id: str
    new_pages: list[PageChange] = field(default_factory=list)
    updated_pages: list[PageChange] = field(default_factory=list)
    deleted_pages: list[PageChange] = field(default_factory=list)
    unchanged_pages: list[PageChange] = field(default_factory=list)
    broken_links: list[dict] = field(default_factory=list)
    orphan_pages: list[str] = field(default_factory=list)
    missing_from_sitemap: list[str] = field(default_factory=list)
    sitemap_added: list[str] = field(default_factory=list)
    sitemap_removed: list[str] = field(default_factory=list)
    has_changes: bool = False

    def summary(self) -> dict:
        return {
            "run_id": self.run_id,
            "previous_run_id": self.previous_run_id,
            "new_pages": len(self.new_pages),
            "updated_pages": len(self.updated_pages),
            "deleted_pages": len(self.deleted_pages),
            "unchanged_pages": len(self.unchanged_pages),
            "broken_links": len(self.broken_links),
            "orphan_pages": len(self.orphan_pages),
            "missing_from_sitemap": len(self.missing_from_sitemap),
            "has_changes": self.has_changes,
        }

    def all_changes(self) -> list[PageChange]:
        return self.new_pages + self.updated_pages + self.deleted_pages

    def to_dict(self) -> dict:
        return {
            **self.summary(),
            "new_pages": [vars(p) for p in self.new_pages],
            "updated_pages": [vars(p) for p in self.updated_pages],
            "deleted_pages": [vars(p) for p in self.deleted_pages],
            "broken_links": self.broken_links,
            "orphan_pages": self.orphan_pages,
            "missing_from_sitemap": self.missing_from_sitemap,
            "sitemap_added": self.sitemap_added,
            "sitemap_removed": self.sitemap_removed,
        }


# Fields that matter for SEO diff — ignore ephemeral crawl metadata
_SEO_FIELDS = [
    "title", "meta_description", "h1", "word_count",
    "canonical", "meta_robots", "has_schema", "schema_types",
    "in_sitemap", "status_code", "internal_links",
]

_CRITICAL_FIELDS = {"title", "meta_description", "h1", "canonical", "meta_robots", "status_code"}


class DiffEngine:
    """
    Compares two SiteSnapshots and returns a structured SiteDiff.

    Rules:
      - A page is NEW if its URL appears in current but not previous.
      - A page is DELETED if its URL was in previous but not current.
      - A page is UPDATED if any SEO-relevant field changed.
      - A page is an ORPHAN if it has zero inbound internal links.
      - A broken link is a page that returned status >= 400.
    """

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger

    def diff(self, current: SiteSnapshot, previous: SiteSnapshot | None) -> SiteDiff:
        result = SiteDiff(
            run_id=current.run_id,
            previous_run_id=previous.run_id if previous else "none",
        )

        current_index = current.page_index()

        if previous is None:
            # First run — treat everything as new
            for page in current.pages:
                result.new_pages.append(PageChange(
                    url=page.url,
                    change_type="new",
                    current=page.to_dict(),
                    severity="info",
                    action_hint="New page detected on first run — optimise metadata and submit for indexing.",
                ))
            result.has_changes = True
        else:
            previous_index = previous.page_index()
            current_urls = set(current_index)
            previous_urls = set(previous_index)

            for url in current_urls - previous_urls:
                result.new_pages.append(self._new_change(current_index[url]))

            for url in previous_urls - current_urls:
                result.deleted_pages.append(self._deleted_change(previous_index[url]))

            for url in current_urls & previous_urls:
                change = self._compare_page(current_index[url], previous_index[url])
                if change.change_type == "updated":
                    result.updated_pages.append(change)
                else:
                    result.unchanged_pages.append(change)

            result.has_changes = bool(result.new_pages or result.updated_pages or result.deleted_pages)

        # Sitemap diff
        prev_sitemap = set(previous.sitemap_urls) if previous else set()
        curr_sitemap = set(current.sitemap_urls)
        result.sitemap_added = list(curr_sitemap - prev_sitemap)
        result.sitemap_removed = list(prev_sitemap - curr_sitemap)

        # Orphan pages — pages with no inbound internal links
        all_links: set[str] = set()
        for page in current.pages:
            all_links.update(page.internal_links)
        site_base = current.site_url.rstrip("/")
        for page in current.pages:
            if page.url == site_base + "/" or page.url == site_base:
                continue
            if page.url not in all_links:
                result.orphan_pages.append(page.url)

        # Missing from sitemap
        result.missing_from_sitemap = [
            p.url for p in current.pages
            if p.status_code == 200
            and not p.in_sitemap
            and "noindex" not in (p.meta_robots or "").lower()
        ]

        # Broken links
        result.broken_links = [
            {"url": p.url, "status_code": p.status_code}
            for p in current.pages
            if p.status_code >= 400
        ]

        self.logger.info(
            "Diff: new=%d updated=%d deleted=%d orphans=%d broken=%d",
            len(result.new_pages), len(result.updated_pages),
            len(result.deleted_pages), len(result.orphan_pages),
            len(result.broken_links),
        )
        return result

    def _new_change(self, page: PageSEOState) -> PageChange:
        severity = "critical" if not page.title or not page.meta_description else "info"
        hints = []
        if not page.title:
            hints.append("Missing title tag")
        if not page.meta_description:
            hints.append("Missing meta description")
        if not page.in_sitemap:
            hints.append("Not in sitemap — submit for indexing")
        if not page.has_schema:
            hints.append("No schema markup detected")
        return PageChange(
            url=page.url,
            change_type="new",
            current=page.to_dict(),
            severity=severity,
            action_hint=" | ".join(hints) if hints else "New page — optimise and index.",
        )

    def _deleted_change(self, page: PageSEOState) -> PageChange:
        return PageChange(
            url=page.url,
            change_type="deleted",
            previous=page.to_dict(),
            severity="critical",
            action_hint="Page deleted — check if redirect needed. REQUIRES DEV REVIEW if page had inbound links.",
        )

    def _compare_page(self, current: PageSEOState, previous: PageSEOState) -> PageChange:
        changed_fields: list[str] = []
        for field_name in _SEO_FIELDS:
            curr_val = getattr(current, field_name, None)
            prev_val = getattr(previous, field_name, None)
            if curr_val != prev_val:
                changed_fields.append(field_name)

        if not changed_fields:
            return PageChange(url=current.url, change_type="unchanged", current=current.to_dict())

        severity = "critical" if any(f in _CRITICAL_FIELDS for f in changed_fields) else "warning"
        hints = []
        if "title" in changed_fields:
            hints.append("Title changed — verify keyword targeting preserved")
        if "meta_description" in changed_fields:
            hints.append("Meta description changed — check CTR impact in GSC")
        if "status_code" in changed_fields and current.status_code >= 400:
            hints.append(f"Page now returning {current.status_code} — urgent fix needed")
        if "word_count" in changed_fields:
            delta = current.word_count - previous.word_count
            hints.append(f"Word count changed by {delta:+d}")

        return PageChange(
            url=current.url,
            change_type="updated",
            fields_changed=changed_fields,
            previous=previous.to_dict(),
            current=current.to_dict(),
            severity=severity,
            action_hint=" | ".join(hints) if hints else "Page updated — review keyword alignment.",
        )
