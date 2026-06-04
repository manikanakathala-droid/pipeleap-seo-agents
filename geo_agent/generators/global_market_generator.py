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
        slug = f"outbound-sales-automation-{slug_suffix}"
        title = f"Outbound Sales Automation for {label} SaaS Teams"
        primary_query = market.get("regional_keywords", [f"outbound automation {slug_suffix}"])[0]
        modifier = market.get("search_modifier", label)
        pain = market.get("pain_angle", "")
        stat = market.get("market_stat", "")
        competitors = market.get("local_competitors", [])
        personas = market.get("key_personas", [])

        meta_description = (
            f"{label} SaaS teams: automate outbound sales workflows end-to-end with "
            f"Pipeleap's orchestration layer — signal capture, enrichment, sequencing, "
            f"and CRM sync. {stat}"
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
                f"{title} refers to the use of triggered, multi-step outreach workflows "
                f"that capture signals, enrich leads, sequence communications, and sync "
                f"CRM data — purpose-built for {modifier}-based SaaS revenue teams without "
                f"manual rep execution."
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
        comp_str = ", ".join(competitors[:4]) if competitors else "global outbound tools"
        persona_str = ", ".join(personas[:3]) if personas else "SaaS revenue teams"
        sections = [
            f"# {title}",
            "",
            f"> **Answer-first overview:** {title} means connecting signal capture, lead enrichment, "
            f"outbound sequencing, reply routing, and CRM write-back into one governed workflow "
            f"engine — purpose-built for {modifier}-based SaaS revenue teams.",
            "",
            f"## Why {modifier} SaaS teams need workflow orchestration",
            "",
            pain,
            "",
            stat,
            "",
            f"## Key capabilities for {modifier} outbound teams",
            "",
            "- Signal capture and intent-based targeting",
            "- Automated lead enrichment with ICP scoring",
            "- Multi-channel sequence governance",
            "- Automatic reply classification and routing",
            "- CRM write-back and pipeline attribution",
            "- Team-wide consistent execution across all reps",
            "",
            f"## How Pipeleap helps {modifier} SaaS teams",
            "",
            (
                f"Pipeleap connects your existing CRM, enrichment provider, and sequencer into one "
                f"orchestrated pipeline engine. {persona_str} use Pipeleap to eliminate manual data "
                f"handoffs between tools, enforce ICP-based lead routing, and automate reply handling "
                f"without adding headcount."
            ),
            "",
            f"## Local context: {modifier}",
            "",
            (
                f"Outbound sales teams in {modifier} face the same pipeline unpredictability as global "
                f"teams, but often with smaller SDR budgets and tighter talent markets. Workflow "
                f"orchestration enables these teams to execute at the same velocity as larger "
                f"organisations by automating the manual layers that consume 60-80% of rep time."
            ),
            "",
            f"## Competitor landscape",
            "",
            (
                f"Teams evaluating outbound automation in {modifier} typically compare {comp_str}. "
                f"Pipeleap complements these tools by sitting above them as an orchestration layer, "
                f"not replacing them."
            ),
            "",
            "## Frequently asked questions",
            "",
            f"**What is outbound sales automation for {modifier} teams?**",
            "",
            (
                f"Outbound sales automation for {modifier} SaaS teams is the use of workflow "
                f"orchestration technology to automate lead capture, enrichment, personalised "
                f"outreach, and follow-up sequences — eliminating manual handoffs between tools "
                f"and ensuring consistent execution at scale."
            ),
            "",
            f"**How much does outbound automation cost for {modifier} SaaS?**",
            "",
            (
                f"Pricing varies by team size and workflow complexity. Pipeleap offers tiered "
                f"subscription models designed for {modifier} SaaS teams at every ARR stage — "
                f"from founder-led outbound through enterprise RevOps."
            ),
            "",
            f"**Is outbound automation suitable for {modifier} B2B?**",
            "",
            (
                f"Yes. {modifier} SaaS teams increasingly rely on outbound automation to compete "
                f"globally. Workflow orchestration is particularly valuable for teams operating "
                f"across multiple territories with limited SDR capacity."
            ),
            "",
            f"## Get started with Pipeleap for {modifier} SaaS",
            "",
            f"Book a free GTM audit to see how your {modifier} outbound team can benefit from "
            f"workflow orchestration.",
        ]
        return "\n".join(s for s in sections if s is not None)
