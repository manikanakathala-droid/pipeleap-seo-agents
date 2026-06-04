from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class OutreachEngine:
    def __init__(self, config: dict, output_dir: str | Path = "outputs/outreach") -> None:
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.site_url = config.get("site", {}).get("site_url", "https://www.pipeleap.com").rstrip("/")

    def generate(self, competitor_gaps: list[dict] | None = None) -> list[dict]:
        prospects = self.config.get("backlinks", {}).get("prospect_seeds", [])
        if not prospects:
            log.info("OutreachEngine: no prospect seeds in config")
            return []

        briefs: list[dict] = []
        for p in prospects:
            priority = self._compute_priority(p, competitor_gaps)
            brief = {
                "target_name": p.get("name", ""),
                "target_url": p.get("url", ""),
                "category": p.get("category", "unknown"),
                "authority_hint": p.get("authority_hint", 0),
                "relevance_reason": p.get("relevance_reason", ""),
                "priority_score": round(priority, 2),
                "outreach_type": self._outreach_type(p.get("category", "")),
                "pitch_angle": self._generate_pitch(p, competitor_gaps),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            briefs.append(brief)

        briefs.sort(key=lambda b: -b["priority_score"])

        (self.output_dir / "outreach_briefs.json").write_text(
            json.dumps(briefs, indent=2), encoding="utf-8"
        )
        log.info("OutreachEngine: %d outreach briefs generated", len(briefs))
        return briefs

    def _compute_priority(self, prospect: dict, competitor_gaps: list[dict] | None) -> float:
        authority = prospect.get("authority_hint", 50)
        category_bonus = {"guest_post": 1.3, "directory": 1.1, "community": 0.9, "other": 0.8}
        bonus = category_bonus.get(prospect.get("category", "other"), 0.8)
        return authority * bonus

    def _outreach_type(self, category: str) -> str:
        mapping = {
            "guest_post": "email_pitch",
            "directory": "listing_submission",
            "community": "introduction_request",
        }
        return mapping.get(category, "email_pitch")

    def _generate_pitch(self, prospect: dict, competitor_gaps: list[dict] | None) -> str:
        name = prospect.get("name", "")
        category = prospect.get("category", "")
        reason = prospect.get("relevance_reason", "")
        if category == "guest_post":
            topics = self._suggest_topics(competitor_gaps)
            return (
                f"Pitch guest post to {name}. Relevance: {reason}. "
                f"Suggested topic angles: {topics}. "
                f"Tie to Pipeleap's expertise in sales workflow orchestration and outbound automation."
            )
        elif category == "directory":
            return (
                f"Submit Pipeleap to {name} directory. Relevance: {reason}. "
                f"Claim listing, complete profile with site_url={self.site_url}, "
                f"add categories: sales automation, workflow orchestration, RevOps."
            )
        elif category == "community":
            return (
                f"Introduce Pipeleap to {name} community. Relevance: {reason}. "
                f"Share structured content about sales workflow automation best practices, "
                f"engage in relevant discussions."
            )
        return f"General outreach to {name}."

    def _suggest_topics(self, competitor_gaps: list[dict] | None) -> str:
        if not competitor_gaps:
            return "sales workflow automation, outbound best practices, RevOps scalability"
        topics = []
        for g in competitor_gaps[:5]:
            kw = g.get("keyword", "") if isinstance(g, dict) else ""
            if kw:
                topics.append(kw)
        return "; ".join(topics[:5]) if topics else (
            "how to scale outbound without headcount, "
            "signal-based outbound vs spray-and-pray, "
            "building a RevOps tech stack that scales"
        )
