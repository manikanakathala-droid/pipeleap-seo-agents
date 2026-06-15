from __future__ import annotations

"""
Adaptive Action Engine — Step 3 of the SEO OS.

OBSERVE → DIFF → DECIDE → EXECUTE → LEARN

Reads the SiteDiff and decides which actions to queue, in what order,
and at what priority. Routes work to the appropriate downstream engines.
Outputs a structured execution plan — safe mode only, no code changes.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from core.diff_engine import SiteDiff, PageChange


@dataclass
class SEOAction:
    action_id: str
    category: str          # "metadata" | "indexing" | "content" | "linking" | "schema" | "redirect" | "technical"
    priority: int          # 1 = highest
    page_url: str
    title: str
    description: str
    safe_mode: bool = True
    requires_dev: bool = False
    dev_note: str = ""
    estimated_impact: str = "medium"    # "high" | "medium" | "low"
    auto_executable: bool = False       # can downstream engine act on this without human?
    status: str = "pending"


@dataclass
class ExecutionPlan:
    run_id: str
    generated_at: str
    mode: str = "change_response"    # "change_response" | "growth_mode"
    actions: list[SEOAction] = field(default_factory=list)
    skipped_reasons: list[str] = field(default_factory=list)
    growth_mode_triggered: bool = False

    def high_priority(self) -> list[SEOAction]:
        return [a for a in self.actions if a.priority == 1]

    def dev_review_required(self) -> list[SEOAction]:
        return [a for a in self.actions if a.requires_dev]

    def auto_executable(self) -> list[SEOAction]:
        return [a for a in self.actions if a.auto_executable and not a.requires_dev]

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "generated_at": self.generated_at,
            "mode": self.mode,
            "total_actions": len(self.actions),
            "high_priority_count": len(self.high_priority()),
            "dev_review_count": len(self.dev_review_required()),
            "auto_executable_count": len(self.auto_executable()),
            "growth_mode_triggered": self.growth_mode_triggered,
            "actions": [vars(a) for a in self.actions],
            "skipped_reasons": self.skipped_reasons,
        }


class AdaptiveActionEngine:
    """
    Decision layer of the SEO OS.

    Given a SiteDiff, produces a prioritised ExecutionPlan.
    All actions are SAFE MODE — no structural code changes.
    Actions that require dev work are flagged explicitly.
    """

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger
        self._action_counter = 0

    def decide(self, diff: SiteDiff) -> ExecutionPlan:
        now = datetime.now(timezone.utc).isoformat()
        plan = ExecutionPlan(run_id=diff.run_id, generated_at=now)

        if not diff.has_changes and not diff.orphan_pages and not diff.broken_links and not diff.missing_from_sitemap:
            plan.mode = "growth_mode"
            plan.growth_mode_triggered = True
            plan.actions = self._growth_mode_actions()
            self.logger.info("No site changes detected — switching to growth mode")
            return plan

        plan.mode = "change_response"

        # New pages
        for change in diff.new_pages:
            plan.actions.extend(self._actions_for_new_page(change))

        # Updated pages
        for change in diff.updated_pages:
            plan.actions.extend(self._actions_for_updated_page(change))

        # Deleted pages
        for change in diff.deleted_pages:
            plan.actions.extend(self._actions_for_deleted_page(change))

        # Broken links
        for broken in diff.broken_links:
            plan.actions.append(self._broken_link_action(broken["url"], broken["status_code"]))

        # Orphan pages
        for url in diff.orphan_pages[:10]:
            plan.actions.append(self._orphan_page_action(url))

        # Missing from sitemap
        for url in diff.missing_from_sitemap[:10]:
            plan.actions.append(self._sitemap_action(url))

        # Dedup and sort
        seen_ids: set[str] = set()
        unique: list[SEOAction] = []
        for action in sorted(plan.actions, key=lambda a: a.priority):
            key = f"{action.category}:{action.page_url}"
            if key not in seen_ids:
                seen_ids.add(key)
                unique.append(action)
        plan.actions = unique

        self.logger.info(
            "ExecutionPlan: %d actions (%d high-priority, %d need dev, %d auto-executable)",
            len(plan.actions),
            len(plan.high_priority()),
            len(plan.dev_review_required()),
            len(plan.auto_executable()),
        )
        return plan

    def _new_id(self) -> str:
        self._action_counter += 1
        return f"ACT-{self._action_counter:04d}"

    def _actions_for_new_page(self, change: PageChange) -> list[SEOAction]:
        actions: list[SEOAction] = []
        page = change.current

        if not page.get("title"):
            actions.append(SEOAction(
                action_id=self._new_id(),
                category="metadata",
                priority=1,
                page_url=change.url,
                title="Add title tag to new page",
                description=(
                    f"New page {change.url} has no title tag. "
                    "Add a keyword-rich title following pattern: [Primary Keyword] | Pipeleap"
                ),
                estimated_impact="high",
                auto_executable=True,
            ))

        if not page.get("meta_description"):
            actions.append(SEOAction(
                action_id=self._new_id(),
                category="metadata",
                priority=1,
                page_url=change.url,
                title="Add meta description to new page",
                description=(
                    f"New page {change.url} has no meta description. "
                    "Write 140-160 chars aligned to primary keyword and conversion intent."
                ),
                estimated_impact="high",
                auto_executable=True,
            ))

        if not page.get("in_sitemap"):
            actions.append(SEOAction(
                action_id=self._new_id(),
                category="indexing",
                priority=1,
                page_url=change.url,
                title="Submit new page for indexing",
                description=f"Submit {change.url} via GSC URL Inspection and add to sitemap.xml.",
                estimated_impact="high",
                auto_executable=True,
            ))

        if not page.get("has_schema"):
            actions.append(SEOAction(
                action_id=self._new_id(),
                category="schema",
                priority=3,
                page_url=change.url,
                title="Add schema markup (optional)",
                description=(
                    f"New page {change.url} has no JSON-LD schema. "
                    "Suggested type: WebPage or Article. Snippet provided in schema output."
                ),
                estimated_impact="medium",
                auto_executable=False,
            ))

        if len(page.get("internal_links", [])) < 2:
            actions.append(SEOAction(
                action_id=self._new_id(),
                category="linking",
                priority=2,
                page_url=change.url,
                title="Add internal links to new page",
                description=(
                    f"New page {change.url} has fewer than 2 inbound internal links. "
                    "Add contextual links from at least 2 existing pages in the same cluster."
                ),
                estimated_impact="medium",
                auto_executable=True,
            ))

        return actions

    def _actions_for_updated_page(self, change: PageChange) -> list[SEOAction]:
        actions: list[SEOAction] = []
        fields = change.fields_changed

        if "title" in fields:
            actions.append(SEOAction(
                action_id=self._new_id(),
                category="metadata",
                priority=2,
                page_url=change.url,
                title="Review title tag change",
                description=(
                    f"Title on {change.url} changed from '{change.previous.get('title', '')}' "
                    f"to '{change.current.get('title', '')}'. "
                    "Verify primary keyword is still present and CTR is maintained."
                ),
                estimated_impact="high",
                auto_executable=False,
            ))

        if "meta_description" in fields:
            actions.append(SEOAction(
                action_id=self._new_id(),
                category="metadata",
                priority=2,
                page_url=change.url,
                title="Review meta description change — monitor CTR",
                description=(
                    f"Meta description on {change.url} was updated. "
                    "Monitor GSC CTR for 7 days. If CTR drops >15%, revert."
                ),
                estimated_impact="medium",
                auto_executable=False,
            ))

        if "word_count" in fields:
            prev_wc = change.previous.get("word_count", 0)
            curr_wc = change.current.get("word_count", 0)
            if curr_wc < prev_wc * 0.8:
                actions.append(SEOAction(
                    action_id=self._new_id(),
                    category="content",
                    priority=1,
                    page_url=change.url,
                    title="Word count dropped significantly",
                    description=(
                        f"Word count on {change.url} dropped from {prev_wc} to {curr_wc} "
                        f"({prev_wc - curr_wc} words removed). "
                        "Significant content removal can hurt rankings. Review before next crawl."
                    ),
                    estimated_impact="high",
                    auto_executable=False,
                ))

        if "status_code" in fields and change.current.get("status_code", 200) >= 400:
            actions.append(SEOAction(
                action_id=self._new_id(),
                category="technical",
                priority=1,
                page_url=change.url,
                title=f"Page now returning {change.current.get('status_code')} — urgent",
                description=(
                    f"{change.url} returned {change.current.get('status_code')}. "
                    "If it previously ranked, this will cause immediate traffic loss."
                ),
                requires_dev=True,
                dev_note="REQUIRES DEV REVIEW — restore page or implement 301 redirect to canonical replacement.",
                estimated_impact="high",
                auto_executable=False,
            ))

        if "meta_robots" in fields and "noindex" in (change.current.get("meta_robots") or "").lower():
            actions.append(SEOAction(
                action_id=self._new_id(),
                category="technical",
                priority=1,
                page_url=change.url,
                title="Page newly marked noindex",
                description=f"{change.url} now has noindex. Confirm this is intentional.",
                requires_dev=True,
                dev_note="REQUIRES DEV REVIEW — if unintentional, remove noindex directive.",
                estimated_impact="high",
                auto_executable=False,
            ))

        return actions

    def _actions_for_deleted_page(self, change: PageChange) -> list[SEOAction]:
        return [SEOAction(
            action_id=self._new_id(),
            category="redirect",
            priority=1,
            page_url=change.url,
            title=f"Deleted page detected — redirect needed",
            description=(
                f"{change.url} no longer exists. "
                "If this page had indexed rankings or inbound links, a 301 redirect is required."
            ),
            requires_dev=True,
            dev_note="REQUIRES DEV REVIEW — implement 301 redirect to the closest topically relevant page.",
            estimated_impact="high",
            auto_executable=False,
        )]

    def _broken_link_action(self, url: str, status: int) -> SEOAction:
        return SEOAction(
            action_id=self._new_id(),
            category="technical",
            priority=1,
            page_url=url,
            title=f"Broken page: HTTP {status}",
            description=f"{url} returned HTTP {status}. Crawl and index signals are being wasted on this URL.",
            requires_dev=True,
            dev_note="REQUIRES DEV REVIEW — restore page, redirect, or remove internal links pointing to it.",
            estimated_impact="high",
            auto_executable=False,
        )

    def _orphan_page_action(self, url: str) -> SEOAction:
        return SEOAction(
            action_id=self._new_id(),
            category="linking",
            priority=2,
            page_url=url,
            title="Orphan page — no inbound internal links",
            description=(
                f"{url} has zero inbound internal links. "
                "Googlebot may not discover or prioritise this page. "
                "Add at least 2 contextual links from relevant pages."
            ),
            estimated_impact="medium",
            auto_executable=True,
        )

    def _sitemap_action(self, url: str) -> SEOAction:
        return SEOAction(
            action_id=self._new_id(),
            category="indexing",
            priority=2,
            page_url=url,
            title="Indexable page missing from sitemap",
            description=f"{url} is crawlable and not noindex, but is absent from sitemap.xml. Add it.",
            estimated_impact="medium",
            auto_executable=True,
        )

    def _growth_mode_actions(self) -> list[SEOAction]:
        """Actions when no site changes detected — shift to content growth."""
        return [
            SEOAction(
                action_id="GM-001",
                category="content",
                priority=1,
                page_url="https://pipeleap.com/blog",
                title="Publish next content plan brief",
                description=(
                    "No site changes detected. Growth mode: publish next queued blog post "
                    "from content_plan_briefs.json. Prioritise alternative/comparison cluster "
                    "(highest conversion probability: 0.91)."
                ),
                estimated_impact="high",
                auto_executable=True,
            ),
            SEOAction(
                action_id="GM-002",
                category="linking",
                priority=2,
                page_url="https://pipeleap.com",
                title="Internal linking audit — reinforce pillar pages",
                description=(
                    "Growth mode: run linking cluster map from serp_strategy.py. "
                    "Ensure every spoke article links to its pillar page. "
                    "Add missing anchor text links from blog posts to /sales-ops-audit."
                ),
                estimated_impact="medium",
                auto_executable=True,
            ),
            SEOAction(
                action_id="GM-003",
                category="metadata",
                priority=2,
                page_url="https://pipeleap.com/pricing",
                title="Improve low-CTR pages from GSC",
                description=(
                    "Growth mode: pull pages with >100 impressions and <3% CTR from GSC. "
                    "Rewrite meta descriptions to match the top triggering query per page."
                ),
                estimated_impact="medium",
                auto_executable=True,
            ),
            SEOAction(
                action_id="GM-004",
                category="indexing",
                priority=3,
                page_url="https://www.pipeleap.com/sitemap.xml",
                title="Resubmit sitemap to GSC",
                description=(
                    "Growth mode: ping GSC sitemap endpoint to trigger a fresh crawl. "
                    "Ensures any recent content is picked up in the next index cycle."
                ),
                estimated_impact="low",
                auto_executable=True,
            ),
            SEOAction(
                action_id="GM-005",
                category="content",
                priority=3,
                page_url="https://pipeleap.com/glossary",
                title="Add new glossary term from keyword gaps",
                description=(
                    "Growth mode: pick the top-traffic, low-difficulty keyword from "
                    "SERP_KEYWORD_CLUSTERS that lacks a dedicated glossary page. Create it."
                ),
                estimated_impact="low",
                auto_executable=True,
            ),
        ]
