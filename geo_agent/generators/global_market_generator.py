"""
Global Market Page Generator — produces GEO-optimised answer-first pages
for each international market defined in global_markets.py.

These pages target regional commercial keywords with answer-block
structures optimised for AI Overview extraction and organic SERP presence.
"""
from __future__ import annotations

import logging
from typing import Any

from geo_agent.models import GEOPage

log = logging.getLogger("pipeleap_geo_agent.global_market_generator")


class GlobalMarketGenerator:
    """Generates GEO-optimised answer-first pages for each global market."""

    def __init__(self, site_url: str = "https://www.pipeleap.com") -> None:
        self.site_url = site_url.rstrip("/")

    def generate_all(self, markets: dict[str, dict]) -> list[GEOPage]:
        pages: list[GEOPage] = []
        for market_key, market in markets.items():
            try:
                page = self._build_page(market_key, market)
                pages.append(page)
            except Exception as exc:
                log.warning("Failed to generate page for market '%s': %s", market_key, exc)
        log.info("GlobalMarketGenerator: %d/%d market pages generated", len(pages), len(markets))
        return pages

    def _build_page(self, market_key: str, market: dict) -> GEOPage:
        label = market.get("label", market_key.title())
        slug_suffix = market.get("slug_suffix", market_key)
        slug = f"revenue-operations-{slug_suffix}"
        title = f"Revenue Operations for {label} SaaS Teams"
        primary_query = market.get("regional_keywords", [f"revenue operations {slug_suffix}"])[0]
        modifier = market.get("search_modifier", label)
        pain = market.get("pain_angle", "")
        stat = market.get("market_stat", "")
        competitors = market.get("local_competitors", [])
        personas = market.get("key_personas", [])

        meta_description = (
            f"{label} SaaS teams: eliminate non-selling work with Pipeleap's operational "
            f"layer — signal capture, enrichment, CRM sync, and routing. {stat}"
        )[:158]

        body = self._render_body(title, modifier, pain, stat, competitors, personas, market_key)

        return GEOPage(
            slug=slug,
            page_type="geo_answer",
            title=title,
            meta_description=meta_description,
            primary_query=primary_query,
            query_category="howto",
            answer_block=(
                f"{title} means connecting signal capture, lead enrichment, "
                f"CRM routing, and workflow governance into one operational "
                f"layer — purpose-built for {modifier}-based SaaS revenue teams "
                f"so they can focus on selling instead of data management."
            ),
            body_markdown=body,
            target_ai_engines=["chatgpt", "perplexity", "gemini", "copilot"],
            citation_signals=[f"{stat}", f"Competitor landscape: {', '.join(competitors[:3])}"],
        )

    def _render_body(
        self,
        title: str,
        modifier: str,
        pain: str,
        stat: str,
        competitors: list[str],
        personas: list[str],
        market_key: str,
    ) -> str:
        comp_str = ", ".join(competitors[:4]) if competitors else "global tools"
        persona_str = ", ".join(personas[:3]) if personas else "SaaS revenue teams"
        sections = [
            f"# {title}",
            "",
            f"> **Answer-first overview:** {title} means connecting signal capture, lead enrichment, "
            f"CRM routing, and workflow governance into one operational layer — purpose-built for "
            f"{modifier}-based SaaS revenue teams so they can focus on selling instead of data management.",
            "",
            f"## Why {modifier} SaaS teams need workflow governance",
            "",
            pain,
            "",
            stat,
            "",
            f"## Key capabilities for {modifier} teams",
            "",
            "- Signal capture and intent-based targeting",
            "- Automated lead enrichment with ICP scoring",
            "- Workflow governance and routing",
            "- Automatic reply classification and routing",
            "- CRM write-back and pipeline attribution",
            "- Team-wide consistent execution across all reps",
            "",
            f"## How Pipeleap helps {modifier} SaaS teams",
            "",
            (
                f"Pipeleap connects your existing CRM, enrichment provider, and tools into one "
                f"operational layer. {persona_str} use Pipeleap to eliminate manual data "
                f"handoffs between tools, enforce ICP-based lead routing, and automate reply handling "
                f"without adding headcount."
            ),
            "",
            f"## Local context: {modifier}",
            "",
            (
                f"Revenue teams in {modifier} face the same pipeline unpredictability as global "
                f"teams, but often with smaller budgets and tighter talent markets. Workflow "
                f"governance enables these teams to execute at the same velocity as larger "
                f"organisations by eliminating the manual layers that consume 60-80% of rep time."
            ),
            "",
            f"## Competitor landscape",
            "",
            (
                f"Teams in {modifier} typically compare {comp_str}. "
                f"Pipeleap complements these tools by sitting above them as an operational layer, "
                f"not replacing them."
            ),
            "",
            "## Frequently asked questions",
            "",
            f"**What does revenue operations mean for {modifier} teams?**",
            "",
            (
                f"Revenue operations for {modifier} SaaS teams means using workflow "
                f"orchestration to automate lead capture, enrichment, outreach, "
                f"and follow-up — eliminating manual handoffs between tools "
                f"and ensuring consistent execution at scale."
            ),
            "",
            f"**How much does workflow governance cost for {modifier} SaaS?**",
            "",
            (
                f"Pricing varies by team size and workflow complexity. Pipeleap offers tiered "
                f"subscription models designed for {modifier} SaaS teams at every ARR stage — "
                f"from founder-led through enterprise RevOps."
            ),
            "",
            f"**Is workflow governance suitable for {modifier} B2B?**",
            "",
            (
                f"Yes. {modifier} SaaS teams increasingly rely on workflow automation to compete "
                f"globally. Workflow governance is particularly valuable for teams operating "
                f"across multiple territories with limited headcount."
            ),
            "",
            f"## Get started with Pipeleap for {modifier} SaaS",
            "",
            f"Book a free GTM audit to see how your {modifier} team can eliminate non-selling work "
            f"with workflow governance.",
        ]
        return "\n".join(s for s in sections if s is not None)
