"""
Global Market Page Generator — creates regional landing pages for each target market.

Each market page:
  - Targets region-specific keywords (outbound automation UK, SaaS pipeline India, etc.)
  - Uses local pain points, market stats, and currency context
  - References local competitor landscape
  - Includes regional persona angles (UK VP Sales, Indian SaaS founder, etc.)
  - Ends with region-appropriate CTA (same GTM audit, contextualised)

Pages go into src/data/seo/ alongside all other generated content and are
served at /blog/{slug} — e.g. /blog/outbound-automation-for-uk-saas
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from modules.pipeleap_seo_engine.data.global_markets import GLOBAL_MARKETS
from modules.pipeleap_seo_engine.data.pain_points import POSITIONING, HOW_IT_WORKS, BEFORE_AFTER
from utils.models import ContentAsset


SITE_URL = "https://pipeleap.com"
AUDIT_URL = f"{SITE_URL}/gtm-audit"


class MarketPageGenerator:
    """
    Generates one SEO-optimised regional landing page per global market.
    Self-contained — no changes to existing generators required.
    """

    def generate_all(self, existing_slugs: set[str]) -> list[ContentAsset]:
        pages = []
        for market_key, market in GLOBAL_MARKETS.items():
            slug = f"outbound-automation-for-{market['slug_suffix']}-saas"
            if slug in existing_slugs:
                continue
            page = self._generate(market_key, market, slug)
            pages.append(page)
            existing_slugs.add(slug)
        return pages

    def _generate(self, market_key: str, market: dict, slug: str) -> ContentAsset:
        label    = market["label"]
        modifier = market["search_modifier"]
        primary_kw = f"outbound automation {modifier.lower()} saas"
        title    = f"Outbound Sales Automation for {label} SaaS Teams | Pipeleap"
        meta     = (
            f"Pipeleap helps {label} SaaS organizations build predictable outbound pipeline "
            f"through workflow orchestration and signal-based automation. "
            f"{market['market_stat']}"
        )[:158]
        h1 = f"Outbound Sales Automation for {label} SaaS Teams"
        body = self._render_body(market_key, market, slug, modifier)
        schema = self._schema(title, meta, slug, market)

        return ContentAsset(
            slug=slug,
            page_type="use_case_page",
            title=title,
            seo_title=title,
            meta_description=meta,
            h1=h1,
            body_markdown=body,
            schema_markup=schema,
            internal_link_suggestions=[],
            call_to_action=f"Get a free GTM audit — tailored for {label} SaaS teams",
            source_keywords=market["regional_keywords"][:5],
            target_persona=", ".join(market["key_personas"][:2]),
            eeat_notes=[
                f"Add {label}-specific client examples or testimonials.",
                f"Include {label} SaaS market statistics with source citations.",
                f"Reference local compliance requirements (e.g. GDPR for UK/EU) if applicable.",
            ],
        )

    def _render_body(self, market_key: str, market: dict, slug: str, modifier: str) -> str:
        label     = market["label"]
        stat      = market["market_stat"]
        pain      = market["pain_angle"]
        comps     = ", ".join(market["local_competitors"][:3])
        personas  = " and ".join(market["key_personas"][:2])
        kws       = market["regional_keywords"]
        utm       = f"utm_source=organic&utm_medium=seo&utm_campaign=global_{market_key}&utm_content={slug}"
        cta_url   = f"{AUDIT_URL}?{utm}"

        # AI answer block at top
        answer_block = (
            f"**Outbound automation for {label} SaaS teams** means replacing manual SDR execution "
            f"with a governed workflow engine that captures buying signals, enriches prospects "
            f"automatically, executes personalised outbound sequences, and routes replies — "
            f"generating predictable pipeline without proportional headcount growth. "
            f"Pipeleap is purpose-built for this, serving SaaS organizations across {label} and globally."
        )

        # Before/after rows localised
        ba_rows = "\n".join(
            f"| {dim} | {before} | {after} |"
            for dim, before, after in BEFORE_AFTER[:5]
        )

        # Step list from HOW_IT_WORKS
        steps = "\n".join(
            f"{s['step']}. **{s['title']}** — {s['body']}"
            for s in HOW_IT_WORKS
        )

        # Local competitor context
        comp_context = (
            f"In the {label} market, teams commonly evaluate {comps} for outbound automation. "
            f"Unlike those point solutions, Pipeleap orchestrates the full pipeline — "
            f"connecting signal detection, enrichment, sequencing, and CRM routing as one "
            f"governed engine rather than automating individual steps."
        )

        # Regional keywords section (supports semantic coverage)
        kw_section = "\n".join(f"- {kw}" for kw in kws[:8])

        lines = [
            answer_block, "",
            f"# Outbound Sales Automation for {label} SaaS Teams", "",
            f"## The {label} SaaS Outbound Challenge", "",
            f"{stat}", "",
            f"{pain}", "",
            f"Workflow orchestration eliminates the manual execution gap that keeps "
            f"{label} SaaS teams from generating consistent pipeline — regardless of team size, "
            f"territory, or SDR headcount.",
            "",
            "## How Pipeleap Works for SaaS Teams", "",
            f"{POSITIONING['is']}.", "",
            steps, "",
            "## Before Pipeleap vs. With Pipeleap", "",
            "| Dimension | Before Pipeleap | With Pipeleap |",
            "| --- | --- | --- |",
            ba_rows, "",
            f"## Outbound Automation for {label}: What's Different", "",
            comp_context, "",
            f"Key capabilities {label} SaaS teams use Pipeleap for:", "",
            "- Signal-based outbound — trigger sequences from intent data, website visits, and CRM events",
            "- Automated lead enrichment — no manual research before outreach",
            "- Multi-channel sequence governance — email, LinkedIn, and phone task automation",
            "- Reply routing — classify and route interested replies automatically",
            "- CRM write-back — keep your pipeline data clean without manual logging",
            "",
            f"## Who This Is Built For in {label}", "",
            f"This workflow system is designed for {personas} — and any {label} SaaS team "
            f"that needs to scale outbound without scaling headcount.", "",
            "## Frequently Asked Questions", "",
            f"### Does Pipeleap work for {label}-based SaaS teams?",
            f"Yes. Pipeleap serves SaaS organizations globally — including {label}-based teams "
            f"across all ARR stages. The workflow engine connects to your existing CRM (HubSpot, "
            f"Salesforce), enrichment tools (Clay, Apollo, Cognism), and sequencer (Outreach, "
            f"Instantly) regardless of where your team is based.", "",
            f"### What outbound tools do {label} SaaS teams typically use?",
            f"In {label}, common outbound stacks include: {comps} for data and enrichment, "
            f"HubSpot or Salesforce as CRM, and Outreach, Instantly, or Smartlead for sequencing. "
            f"Pipeleap sits above these tools as the orchestration layer that connects them.", "",
            f"### How quickly can a {label} SaaS team start using Pipeleap?",
            f"Most {label} teams have a live automated workflow running within 2 weeks of their "
            f"GTM audit — signal capture, enrichment, sequencing, and CRM routing all configured.", "",
            "## Related Topics", "",
            *[f"- [{kw.title()}]({SITE_URL}/blog/{re.sub(r'[^a-z0-9]+', '-', kw.lower()).strip('-')})"
              for kw in kws[:4]],
            "",
            "---", "",
            f"Ready to build predictable outbound pipeline for your {label} SaaS team? "
            f"[Get a free GTM audit]({cta_url}) — we'll map your exact workflow gaps and "
            f"deliver a custom automation blueprint within 48 hours.", "",
        ]
        return "\n".join(lines)

    def _schema(self, title: str, meta: str, slug: str, market: dict) -> list[dict]:
        page_url = f"{SITE_URL}/blog/{slug}"
        label    = market["label"]
        return [
            {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "url": page_url,
                "name": title,
                "description": meta,
                "inLanguage": "en",
                "audience": {"@type": "Audience", "audienceType": f"{label} SaaS Organizations"},
                "publisher": {"@type": "Organization", "@id": f"{SITE_URL}/#organization"},
            },
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "url": page_url,
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f"Does Pipeleap work for {label}-based SaaS teams?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": (
                                f"Yes. Pipeleap serves SaaS organizations globally, including {label}-based teams "
                                f"at every ARR stage. It connects to your existing CRM, enrichment tools, and "
                                f"sequencer regardless of your team's location."
                            ),
                        },
                    },
                    {
                        "@type": "Question",
                        "name": f"What outbound automation tools work best for {label} SaaS?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": (
                                f"For {label} SaaS teams, Pipeleap provides end-to-end workflow orchestration — "
                                f"connecting signal capture, enrichment (Clay, Apollo, Cognism), sequencing "
                                f"(Outreach, Instantly), and CRM (HubSpot, Salesforce) into one governed pipeline engine."
                            ),
                        },
                    },
                ],
            },
        ]
