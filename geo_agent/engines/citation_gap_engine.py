"""
Citation Gap Engine — identifies queries where Pipeleap should be cited by AI engines but isn't.

Works in three modes:
  1. SERP mode (DataForSEO): checks which target queries have AI Overviews and whether
     pipeleap.com content would be eligible for citation based on SERP features present
  2. Structural mode (no API): analyses page structure to flag citation readiness gaps
  3. Coverage mode: cross-references GEO_TARGET_QUERIES against published pages to find
     queries with no targeting content at all
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from geo_agent.data.geo_entities import GEO_TARGET_QUERIES
from geo_agent.models import CitationGap


class CitationGapEngine:
    """
    Detects citation gaps across all GEO target queries.
    Prioritises by: query volume signal, AI Overview presence, content coverage.
    """

    # Minimum quality signals needed for AI citation eligibility
    CITATION_REQUIREMENTS = {
        "answer_block_present": "Page opens with a 40-70 word direct answer",
        "faq_schema":           "FAQPage JSON-LD schema with the query as a question",
        "heading_matches_query":"H1 or H2 contains the exact query phrasing",
        "internal_links_in":    "At least 3 other pages link to this page",
    }

    def detect(
        self,
        published_slugs: set[str],
        serp_data: list[dict] | None = None,
        cms_publish_dir: str | None = None,
    ) -> list[CitationGap]:
        """
        Main detection method. Returns CitationGaps sorted by priority score.

        Args:
            published_slugs: set of slugs present in src/data/seo/
            serp_data: optional DataForSEO results with ai_overview/paa flags
            cms_publish_dir: path to src/data/seo/ for content inspection
        """
        gaps: list[CitationGap] = []
        serp_lookup = {r.get("keyword", "").lower(): r for r in (serp_data or [])}

        for category, queries in GEO_TARGET_QUERIES.items():
            for query in queries:
                gap = self._analyse_query(
                    query, category, published_slugs, serp_lookup, cms_publish_dir
                )
                if gap:
                    gaps.append(gap)

        return self._prioritise(gaps)

    def coverage_report(self, gaps: list[CitationGap]) -> str:
        """Generate a markdown coverage report for the run output."""
        lines = [
            "## GEO Citation Gap Report",
            "",
            f"**Total gaps identified:** {len(gaps)}",
            f"**Critical (no content + AI Overview):** {sum(1 for g in gaps if g.priority_score >= 0.8)}",
            f"**High priority (no content):** {sum(1 for g in gaps if 0.5 <= g.priority_score < 0.8)}",
            "",
            "### Top 10 Priority Gaps",
            "",
            "| Query | Category | AI Overview | Status | Action |",
            "| --- | --- | --- | --- | --- |",
        ]
        for gap in gaps[:10]:
            lines.append(
                f"| {gap.query[:50]} | {gap.query_category} | "
                f"{'Yes' if gap.has_ai_overview else 'No'} | "
                f"{gap.current_status} | {gap.recommended_action[:60]} |"
            )
        lines += ["", "### All Gaps by Category", ""]
        by_category: dict[str, list[CitationGap]] = {}
        for gap in gaps:
            by_category.setdefault(gap.query_category, []).append(gap)
        for cat, cat_gaps in sorted(by_category.items()):
            lines += [f"**{cat.upper()} ({len(cat_gaps)} gaps)**", ""]
            for g in cat_gaps:
                lines.append(f"- {g.query} — {g.recommended_action}")
            lines.append("")
        return "\n".join(lines)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _analyse_query(
        self,
        query: str,
        category: str,
        published_slugs: set[str],
        serp_lookup: dict,
        cms_publish_dir: str | None,
    ) -> CitationGap | None:
        slug_candidate = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")[:60]
        serp = serp_lookup.get(query.lower(), {})
        has_ai_overview = serp.get("has_ai_overview", False)
        has_paa = serp.get("has_paa", False)
        search_volume = serp.get("search_volume", 0)

        # Check if any published page covers this query
        covered = any(
            self._slug_covers_query(slug, query)
            for slug in published_slugs
        )

        if covered and not has_ai_overview:
            # Content exists and no AI Overview — lower priority
            return None

        if covered and has_ai_overview:
            # Content exists but we need to verify citation quality
            issues = self._inspect_content_quality(slug_candidate, cms_publish_dir)
            if not issues:
                return None
            status = "content_exists_quality_gaps"
            action = f"Improve citation quality: {'; '.join(issues[:2])}"
            score = 0.55
        elif not covered and has_ai_overview:
            status = "no_content_ai_overview_exists"
            action = f"Create GEO page targeting: '{query}' — AI Overview present, no Pipeleap content"
            score = 0.90
        else:
            # No content, no AI Overview detected (or no SERP data)
            status = "no_content"
            action = f"Create answer-block page for: '{query}'"
            score = 0.40 + (0.20 if category in ("recommendation",) else 0.0)

        # Boost score for high-value categories
        if category == "recommendation":
            score = min(1.0, score + 0.10)
        if has_ai_overview:
            score = min(1.0, score + 0.20)
        if has_paa:
            score = min(1.0, score + 0.10)

        return CitationGap(
            query=query,
            query_category=category,
            ai_engine="google_ai_overview" if has_ai_overview else "all",
            expected_position="should be cited",
            current_status=status,
            recommended_action=action,
            priority_score=round(score, 3),
            has_ai_overview=has_ai_overview,
            has_paa=has_paa,
            search_volume=search_volume,
        )

    def _slug_covers_query(self, slug: str, query: str) -> bool:
        """Check if a slug is likely to cover a query based on keyword overlap."""
        query_words = set(re.sub(r"[^a-z0-9 ]", "", query.lower()).split())
        slug_words  = set(slug.replace("-", " ").split())
        stop = {"what", "is", "how", "do", "you", "the", "a", "an", "to", "for", "best"}
        query_core = query_words - stop
        if not query_core:
            return False
        overlap = len(query_core & slug_words) / len(query_core)
        return overlap >= 0.4

    def _inspect_content_quality(
        self, slug: str, cms_dir: str | None
    ) -> list[str]:
        """Check if an existing page has the required citation quality signals."""
        if not cms_dir:
            return []
        issues = []
        content_path = Path(cms_dir) / slug / "index.md"
        if not content_path.exists():
            return []
        content = content_path.read_text(encoding="utf-8", errors="ignore")
        words = content.split()

        # Check for answer block (starts with bold or direct statement in first 80 words)
        first_200 = " ".join(words[:80]).lower()
        if not any(w in first_200 for w in ["is a", "is the", "refers to", "means"]):
            issues.append("no direct answer block in opening")
        # Check for FAQ section
        if "## frequently asked" not in content.lower() and "## faq" not in content.lower():
            issues.append("no FAQ section for PAA eligibility")
        return issues

    @staticmethod
    def _prioritise(gaps: list[CitationGap]) -> list[CitationGap]:
        return sorted(gaps, key=lambda g: g.priority_score, reverse=True)
