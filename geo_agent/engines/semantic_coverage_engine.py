"""
Semantic Coverage Engine — ensures Pipeleap's content covers every subtopic
an AI engine would expect to find on an authoritative source.

AI engines only cite pages as authoritative when the content is semantically
complete — covering the main topic AND all expected related subtopics.
A page about 'outbound automation' that doesn't cover signal-based triggering,
enrichment, sequencing, AND reply routing will rank below a page that does all four.

This engine:
  1. Defines expected subtopic coverage for each topical pillar
  2. Audits published pages for coverage completeness
  3. Scores semantic completeness per page (0-100)
  4. Flags pages that need expansion to reach AI citation threshold
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


# Expected subtopics per topical pillar
PILLAR_SUBTOPICS: dict[str, list[str]] = {
    "outbound-automation": [
        "signal capture", "lead enrichment", "sequence execution",
        "reply routing", "crm automation", "icp scoring",
        "workflow orchestration", "pipeline generation",
        "manual vs automated", "roi", "implementation",
    ],
    "pipeline-generation": [
        "signal-based outbound", "predictable pipeline", "workflow orchestration",
        "sdr productivity", "pipeline metrics", "pipeline velocity",
        "outbound without sdrs", "pipeline at scale",
    ],
    "workflow-orchestration": [
        "n8n", "signal capture", "enrichment waterfall", "sequence routing",
        "crm sync", "reply classification", "end-to-end automation",
        "governed execution", "workflow governance",
    ],
    "competitor-comparison": [
        "vs clay", "vs zapier", "vs apollo", "vs hubspot",
        "alternatives", "feature comparison", "pricing comparison",
        "when to use each", "integration capabilities",
    ],
    "glossary": [
        "workflow orchestration definition", "outbound automation definition",
        "signal-based outbound definition", "pipeline generation definition",
        "revenue operations definition", "sdr automation definition",
        "lead enrichment definition", "crm automation definition",
    ],
    "integrations": [
        "hubspot integration", "salesforce integration", "clay integration",
        "apollo integration", "outreach integration", "instantly integration",
        "n8n integration", "zapier pipeleap integration",
    ],
}

# Minimum semantic coverage score required for AI citation eligibility
AI_CITATION_THRESHOLD = 60.0


class SemanticCoverageEngine:
    """
    Audits and scores semantic completeness of Pipeleap's published content.
    """

    def audit_pillar(
        self,
        pillar: str,
        cms_publish_dir: str,
    ) -> dict[str, Any]:
        """
        Audit all published pages under a topical pillar for semantic completeness.
        Returns per-page scores and overall pillar coverage.
        """
        seo_dir = Path(cms_publish_dir)
        if not seo_dir.exists():
            return {"pillar": pillar, "error": "cms_publish_dir not found"}

        expected_subtopics = PILLAR_SUBTOPICS.get(pillar, [])
        page_scores: list[dict] = []
        covered_subtopics: set[str] = set()

        for content_dir in seo_dir.iterdir():
            if not content_dir.is_dir():
                continue
            md_path = content_dir / "index.md"
            if not md_path.exists():
                continue

            content = md_path.read_text(encoding="utf-8", errors="ignore").lower()

            # Check which expected subtopics this page covers
            page_covered = []
            for subtopic in expected_subtopics:
                if all(word in content for word in subtopic.split()):
                    page_covered.append(subtopic)
                    covered_subtopics.add(subtopic)

            score = round(len(page_covered) / max(len(expected_subtopics), 1) * 100, 1)
            page_scores.append({
                "slug": content_dir.name,
                "subtopics_covered": page_covered,
                "coverage_score": score,
                "ai_citation_eligible": score >= AI_CITATION_THRESHOLD,
                "needs_expansion": [s for s in expected_subtopics if s not in page_covered],
            })

        pillar_coverage = round(
            len(covered_subtopics) / max(len(expected_subtopics), 1) * 100, 1
        )
        missing_pillar_subtopics = [s for s in expected_subtopics if s not in covered_subtopics]

        return {
            "pillar": pillar,
            "expected_subtopics": len(expected_subtopics),
            "covered_subtopics": len(covered_subtopics),
            "pillar_coverage_pct": pillar_coverage,
            "ai_citation_ready": pillar_coverage >= AI_CITATION_THRESHOLD,
            "missing_subtopics": missing_pillar_subtopics,
            "pages_audited": len(page_scores),
            "pages_eligible": sum(1 for p in page_scores if p["ai_citation_eligible"]),
            "page_scores": sorted(page_scores, key=lambda p: p["coverage_score"], reverse=True),
        }

    def audit_all_pillars(self, cms_publish_dir: str) -> dict[str, Any]:
        """Run semantic coverage audit across all topical pillars."""
        results = {}
        for pillar in PILLAR_SUBTOPICS:
            results[pillar] = self.audit_pillar(pillar, cms_publish_dir)
        overall = round(
            sum(r["pillar_coverage_pct"] for r in results.values()) / max(len(results), 1), 1
        )
        return {
            "overall_coverage_pct": overall,
            "pillars": results,
            "weakest_pillars": [
                p for p, r in sorted(results.items(), key=lambda x: x[1]["pillar_coverage_pct"])
                if r["pillar_coverage_pct"] < AI_CITATION_THRESHOLD
            ],
        }

    def expansion_priorities(self, audit_result: dict) -> list[dict[str, Any]]:
        """
        Return prioritised list of content expansions needed to reach AI citation threshold.
        """
        priorities = []
        for pillar, data in audit_result.get("pillars", {}).items():
            for missing in data.get("missing_subtopics", []):
                priorities.append({
                    "pillar": pillar,
                    "missing_subtopic": missing,
                    "recommended_action": (
                        f"Add a '## {missing.title()}' section to the {pillar} pillar page "
                        f"with a 150-200 word explanation and a 50-word answer block"
                    ),
                    "priority": "HIGH" if data["pillar_coverage_pct"] < 40 else "MEDIUM",
                })
        return sorted(
            priorities,
            key=lambda p: (p["priority"] == "HIGH", p["pillar"]),
            reverse=True,
        )

    def report_md(self, audit_result: dict) -> str:
        lines = [
            "## Semantic Coverage Report",
            "",
            f"**Overall coverage:** {audit_result['overall_coverage_pct']}%",
            f"**Weak pillars (< {AI_CITATION_THRESHOLD}%):** "
            f"{', '.join(audit_result.get('weakest_pillars', [])) or 'None'}",
            "",
            "| Pillar | Coverage | AI-Eligible | Missing Subtopics |",
            "| --- | --- | --- | --- |",
        ]
        for pillar, data in audit_result.get("pillars", {}).items():
            lines.append(
                f"| {pillar} | {data['pillar_coverage_pct']}% | "
                f"{'Yes' if data['ai_citation_ready'] else 'No'} | "
                f"{len(data.get('missing_subtopics', []))} |"
            )
        return "\n".join(lines)
