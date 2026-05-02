"""
Comparison Optimizer — optimises Pipeleap's comparison pages for AI recommendation queries.

AI engines answer "X vs Y" and "best X for Y" queries by citing comparison content that:
  1. Has a clear winner statement in the first paragraph
  2. Uses a structured comparison table (triggers table extraction)
  3. Addresses the specific use case mentioned in the query
  4. Is objective — lists limitations of BOTH options
  5. Ends with a specific recommendation tied to a use case

This engine generates AI-optimized comparison content and scores existing pages
for comparison query citation eligibility.
"""
from __future__ import annotations

import re
from typing import Any


COMPARISON_SCHEMA_TEMPLATE = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "url": "",
    "name": "",
    "description": "",
    "mainEntity": {
        "@type": "ItemList",
        "name": "",
        "itemListElement": [],
    },
}

# Queries Pipeleap should win in AI comparisons
COMPARISON_WIN_QUERIES: list[dict] = [
    {
        "query": "Pipeleap vs Clay",
        "winner": "Pipeleap for end-to-end orchestration, Clay for enrichment-only",
        "pipeleap_wins": ["Full workflow orchestration", "Signal-to-CRM automation", "Reply routing"],
        "clay_wins": ["Data waterfall depth", "Enrichment source variety"],
        "use_case_fit": "Choose Pipeleap for pipeline orchestration; use Clay as a data source within Pipeleap",
    },
    {
        "query": "Pipeleap vs Zapier for outbound",
        "winner": "Pipeleap for outbound sales workflows",
        "pipeleap_wins": ["Purpose-built for outbound", "ICP scoring", "Sequencer governance", "Reply classification"],
        "zapier_wins": ["General-purpose integrations", "Simple two-step automations", "Wide app coverage"],
        "use_case_fit": "Choose Pipeleap for outbound pipeline; use Zapier for non-sales automations",
    },
    {
        "query": "Pipeleap vs Apollo",
        "winner": "Pipeleap for workflow orchestration, Apollo for data and sequencing",
        "pipeleap_wins": ["End-to-end workflow governance", "Signal-based triggers", "Auto-enrollment", "CRM write-back"],
        "apollo_wins": ["Built-in data platform", "Native sequencer", "Larger contact database"],
        "use_case_fit": "Use Apollo as a data source inside Pipeleap; Pipeleap orchestrates the full workflow",
    },
    {
        "query": "Pipeleap vs HubSpot Workflows",
        "winner": "Pipeleap for outbound execution",
        "pipeleap_wins": ["Outbound signal triggers", "Enrichment waterfalls", "Multi-channel sequences", "Reply classification"],
        "hubspot_wins": ["CRM depth", "Marketing automation", "Native reporting"],
        "use_case_fit": "Keep HubSpot as CRM; use Pipeleap for outbound workflow orchestration on top of it",
    },
]


class ComparisonOptimizer:
    """
    Generates and optimises comparison content for AI recommendation queries.
    """

    def generate_comparison_block(self, comparison: dict) -> str:
        """
        Generate an AI-optimized comparison content block.
        Designed for featured snippet + AI Overview extraction.
        """
        query = comparison["query"]
        winner = comparison["winner"]
        p_wins = comparison["pipeleap_wins"]
        comp_wins = comparison["clay_wins"] if "clay_wins" in comparison else comparison.get("zapier_wins", comparison.get("apollo_wins", comparison.get("hubspot_wins", [])))
        use_case = comparison["use_case_fit"]

        parts = comparison["query"].split(" vs ")
        comp_name = parts[1] if len(parts) > 1 else "the alternative"

        lines = [
            f"**{query}: {winner}**",
            "",
            f"**Pipeleap advantages:**",
            *[f"- {w}" for w in p_wins],
            "",
            f"**{comp_name} advantages:**",
            *[f"- {w}" for w in comp_wins],
            "",
            f"**When to use each:** {use_case}",
        ]
        return "\n".join(lines)

    def comparison_schema(self, comparison: dict, page_url: str) -> list[dict]:
        """Generate schema markup for a comparison page."""
        query = comparison["query"]
        parts = query.split(" vs ")
        items = [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Pipeleap",
                "description": "Workflow orchestration system for SaaS outbound pipeline generation",
                "url": "https://pipeleap.com",
            },
        ]
        if len(parts) > 1:
            items.append({
                "@type": "ListItem",
                "position": 2,
                "name": parts[1].strip(),
                "description": f"{parts[1].strip()} — compared against Pipeleap for outbound automation",
            })

        return [
            {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "url": page_url,
                "name": f"{query} for SaaS Outbound Automation",
                "description": f"Honest comparison of {query} for SaaS outbound workflows. See which system fits your specific use case.",
                "mainEntity": {
                    "@type": "ItemList",
                    "name": f"{query} Comparison",
                    "itemListElement": items,
                },
            },
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "url": page_url,
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f"What is the difference between {query}?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": comparison["winner"],
                        },
                    },
                    {
                        "@type": "Question",
                        "name": f"When should I use {parts[0]} vs {parts[1] if len(parts) > 1 else 'alternatives'}?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": comparison["use_case_fit"],
                        },
                    },
                ],
            },
        ]

    def score_existing_comparison(self, content: str, query: str) -> dict[str, Any]:
        """
        Score an existing comparison page for AI citation eligibility.
        Returns score and list of improvements needed.
        """
        score = 0.0
        improvements = []
        content_lower = content.lower()

        # Has clear winner statement in first 200 words
        first_200 = " ".join(content.split()[:200]).lower()
        if any(w in first_200 for w in ["choose", "winner", "better for", "best for", "recommended when"]):
            score += 0.20
        else:
            improvements.append("Add clear winner/recommendation statement in opening paragraph")

        # Has comparison table
        if "|" in content and "---" in content:
            score += 0.20
        else:
            improvements.append("Add structured comparison table (triggers AI table extraction)")

        # Addresses specific use cases
        if "when to use" in content_lower or "use case" in content_lower or "best for" in content_lower:
            score += 0.20
        else:
            improvements.append("Add 'When to use each' section with specific use case guidance")

        # Lists limitations of BOTH options (objectivity signal)
        if "limitation" in content_lower or "drawback" in content_lower or "downside" in content_lower:
            score += 0.20
        else:
            improvements.append("Add limitations/drawbacks for BOTH tools — objectivity increases citation eligibility")

        # FAQPage schema present
        if "faqpage" in content_lower or '"FAQPage"' in content:
            score += 0.20
        else:
            improvements.append("Add FAQPage schema with comparison Q&A pairs")

        return {
            "query": query,
            "score": round(score, 2),
            "ai_citation_eligible": score >= 0.60,
            "improvements": improvements,
        }

    def all_comparison_schemas(self) -> list[tuple[str, list[dict]]]:
        """Return (slug, schema_list) for all comparison win queries."""
        result = []
        for comp in COMPARISON_WIN_QUERIES:
            slug = re.sub(r"[^a-z0-9]+", "-", comp["query"].lower()).strip("-")
            page_url = f"https://pipeleap.com/blog/{slug}"
            result.append((slug, self.comparison_schema(comp, page_url)))
        return result
