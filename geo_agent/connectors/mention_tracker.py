"""
Mention Tracker — tracks Pipeleap's external citations and brand mentions
across high-authority sites that LLMs use as training and reference sources.

Tracks:
  - New external links to pipeleap.com (via GSC or Ahrefs)
  - Brand mentions across monitored sites
  - Citation status per AI source site

Outputs a citation registry that feeds into EntityAuthorityEngine scoring.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from geo_agent.data.ai_source_sites import AI_SOURCE_SITES


class MentionTracker:
    """
    Maintains a persistent registry of Pipeleap's external citations.
    Updated manually or via API integrations (GSC, Ahrefs).
    """

    def __init__(self, registry_path: str | None = None) -> None:
        self.registry_path = Path(
            registry_path or "outputs/geo/mention_registry.json"
        )
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._registry: dict[str, Any] = self._load()

    # ── Public API ─────────────────────────────────────────────────────────────

    def record_mention(
        self,
        site: str,
        url: str,
        mention_type: str,     # "backlink" | "review" | "editorial" | "directory"
        anchor_text: str = "",
        includes_pipeleap_link: bool = False,
        context: str = "",
    ) -> None:
        """Record a new external mention of Pipeleap."""
        key = f"{site}::{url}"
        self._registry[key] = {
            "site":                   site,
            "url":                    url,
            "mention_type":           mention_type,
            "anchor_text":            anchor_text,
            "includes_pipeleap_link": includes_pipeleap_link,
            "context":                context,
            "recorded_at":            datetime.now(timezone.utc).isoformat(),
        }
        self._save()

    def update_site_status(self, site_name: str, status: str) -> None:
        """Update the listing status for a site in AI_SOURCE_SITES."""
        for site in AI_SOURCE_SITES:
            if site["site"] == site_name:
                site["status"] = status
                break
        key = f"status::{site_name}"
        self._registry[key] = {
            "site": site_name,
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save()

    def citation_summary(self) -> dict[str, Any]:
        """Return a summary of all tracked mentions."""
        mentions = [v for k, v in self._registry.items() if not k.startswith("status::")]
        by_type: dict[str, int] = {}
        for m in mentions:
            t = m.get("mention_type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1

        with_links = sum(1 for m in mentions if m.get("includes_pipeleap_link"))

        return {
            "total_mentions":       len(mentions),
            "mentions_with_links":  with_links,
            "by_type":              by_type,
            "high_authority_mentions": [
                m for m in mentions
                if any(s["site"].lower() in m.get("site", "").lower()
                       for s in AI_SOURCE_SITES
                       if s.get("citation_weight", 0) >= 8)
            ],
        }

    def priority_outreach_list(self) -> list[dict]:
        """
        Return prioritised list of sites to pursue for new citations.
        Sorted by LLM citation weight, filtered to not-yet-mentioned.
        """
        status_updates = {
            v["site"]: v["status"]
            for k, v in self._registry.items()
            if k.startswith("status::")
        }
        result = []
        for site in sorted(AI_SOURCE_SITES, key=lambda s: s.get("citation_weight", 0), reverse=True):
            current_status = status_updates.get(site["site"], site["status"])
            if current_status in ("not_listed", "not_mentioned", "not_present"):
                result.append({
                    **site,
                    "current_status": current_status,
                    "outreach_template": self._outreach_template(site),
                })
        return result

    def report_md(self) -> str:
        summary = self.citation_summary()
        lines = [
            "## Citation & Mention Tracker Report",
            "",
            f"**Total external mentions tracked:** {summary['total_mentions']}",
            f"**Mentions with Pipeleap backlinks:** {summary['mentions_with_links']}",
            f"**By type:** {summary['by_type']}",
            "",
            "### Priority Outreach Targets",
            "",
            "| Site | Priority | Citation Weight | Action |",
            "| --- | --- | --- | --- |",
        ]
        for site in self.priority_outreach_list()[:10]:
            lines.append(
                f"| {site['site']} | {site['priority']} | "
                f"{site['citation_weight']}/10 | {site['action'][:60]} |"
            )
        return "\n".join(lines)

    # ── Internals ──────────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if self.registry_path.exists():
            try:
                return json.loads(self.registry_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save(self) -> None:
        self.registry_path.write_text(
            json.dumps(self._registry, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _outreach_template(site: dict) -> str:
        templates = {
            "software_review": f"Request a listing review on {site['site']} — share client outcomes as proof points",
            "editorial":       f"Pitch a guest article on {site['site']} about workflow orchestration for SaaS outbound",
            "community_qa":    f"Answer questions about outbound automation on {site['site']} with workflow orchestration context",
            "community":       f"Participate in relevant threads on {site['site']} — share Pipeleap use cases authentically",
            "product_directory": f"Ensure {site['site']} listing is complete with description, screenshots, and category tags",
            "tech_stack":      f"Add Pipeleap as a tool on {site['site']} with use case description",
        }
        return templates.get(site.get("category", ""), site.get("action", ""))
