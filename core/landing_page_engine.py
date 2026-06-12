from __future__ import annotations

from datetime import date as _date
from typing import Any

from utils.models import ContentAsset, KeywordCluster
from utils.stage_messaging import STAGES, STAGE_CTA, STAGE_BEFORE_AFTER
from utils.text import slugify, title_case_keyword

_LOCATION_TO_HREFLANG: dict[int, str] = {
    2840: "en-us",
    2826: "en-gb",
    2036: "en-au",
    2124: "en-ca",
    2356: "en-in",
    2702: "en-sg",
}


class LandingPageEngine:
    """Generates high-intent landing pages for Pipeleap's revenue workflows."""

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger
        self.site = config.get("site", {})
        self.cta = self.site.get("cta", {})
        self.features = self.site.get("core_features", [])

    def generate(self, clusters: list[KeywordCluster], limit: int = 5) -> list[ContentAsset]:
        high_intent_clusters = [
            cluster
            for cluster in clusters
            if cluster.recommended_asset_type == "landing_page"
        ][:limit]
        return [self._generate_landing_page(cluster) for cluster in high_intent_clusters]

    def _generate_landing_page(self, cluster: KeywordCluster) -> ContentAsset:
        keyword = cluster.primary_keyword
        keyword_title = title_case_keyword(keyword)
        slug = slugify(keyword)
        stage = self._detect_stage(keyword)
        stage_data = STAGES.get(stage, {})

        # Stage-specific headline and framing
        if stage == "early":
            title = f"{keyword_title} - Eliminate Non-Selling Work Before You Scale"
            target_persona = "Founders and early-stage teams"
        elif stage == "growth":
            title = f"{keyword_title} - Reclaim 11 Hours Per Rep Per Week"
            target_persona = "VP Sales and sales managers at growth-stage companies"
        elif stage == "scale":
            title = f"{keyword_title} - Sales Operations Platform for Enterprise Revenue Teams"
            target_persona = "CROs and sales ops leaders"
        else:
            title = f"{keyword_title} for Revenue Teams That Need More Selling Time"
            target_persona = "Sales ops teams and growth operators"

        seo_title = f"{keyword_title} | Pipeleap Sales Operations Platform"
        meta_description = (
            f"Launch {keyword} with Pipeleap's sales operations platform for enrichment, CRM governance, "
            f"routing, and automated execution - reclaiming selling time for your team."
        )[:158]

        # Stage context callout
        stage_callout = ""
        if stage_data:
            stage_callout = (
                f"\n> **Built for {stage_data.get('label', '')} ({stage_data.get('arr_range', '')}):** "
                f"{stage_data.get('hero_stat', '')}\n"
            )

        # Stage-specific pain points
        if stage_data.get("pain_points"):
            pain_items = "\n".join(f"- {p}" for p in stage_data["pain_points"][:4])
        else:
            pain_items = (
                "- Manual enrichment and CRM data management that doesn't scale.\n"
                "- Fragmented tools with no unified execution layer.\n"
                "- No repeatable revenue operations playbook.\n"
                "- Poor visibility into which workflows drive pipeline."
            )

        before_after_block = ""

        direct_answer = (
            f"> **TL;DR — {keyword_title}:** A production-ready {keyword} system captures intent signals, "
            f"enriches and qualifies contacts, writes clean data to the CRM, and triggers outreach "
            f"sequences automatically — replacing fragmented point tools with one governed revenue workflow.\n"
        )

        body = "\n".join(filter(None, [
            direct_answer,
            f"# {keyword_title}",
            "",
            stage_callout,
            f"Teams evaluating **{keyword}** are already close to choosing a system. This page connects that demand directly to Pipeleap's workflow automation value.",
            "",
            f"## The problem with fragmented {cluster.cluster_name}",
            f"Most {'early-stage' if stage == 'early' else 'growing' if stage == 'growth' else 'enterprise' if stage == 'scale' else 'revenue'} teams have the pieces but not the operating system.",
            pain_items,
            "",
            "## The Pipeleap solution",
            f"Pipeleap gives teams a workflow layer built for enrichment, CRM automation, pipeline acceleration, and eliminating non-selling work — replacing fragmented point solutions with one governed execution system.",
            "",
            "## How Pipeleap works",
            "1. Capture the trigger or account signal.",
            "2. Enrich and score the account or contact.",
            "3. Sync clean data into the CRM with routing logic.",
            "4. Trigger outreach or follow-up workflows.",
            "5. Push replies, demos, and task states back into reporting.",
            "",
            before_after_block,
            "",
            "## Workflow diagram",
            "```text",
            "Signal -> Enrichment -> Qualification -> CRM update -> Outbound step -> Reply routing -> Demo booked",
            "```",
            "",
            "## Why teams pick Pipeleap",
            "- n8n-based flexibility without losing revenue workflow structure.",
            "- Built for CRM automation, enrichment-heavy workflows, and sales operations.",
            "- Fast iteration for growth and RevOps teams.",
            "",
            "## FAQ",
            f"### Who should use {keyword}?",
            "Teams that need a governed operations and workflow system, not one-off automations.",
            "",
            f"### What makes Pipeleap different in {cluster.cluster_name}?",
            "It maps the keyword directly to the revenue workflow that has to execute after traffic converts.",
            "",
            "## CTA",
            self._cta_block(stage),
        ]))

        today = _date.today().isoformat()
        brand = self.site.get("brand", "Pipeleap")
        site_url = self.site.get("site_url", "https://pipeleap.com")
        page_url = f"{site_url.rstrip('/')}/{slug}"
        org_ref = {"@type": "Organization", "name": brand, "url": site_url}

        schema_markup = [
            {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": seo_title,
                "description": meta_description,
                "url": page_url,
                "datePublished": today,
                "dateModified": today,
                "author": org_ref,
                "publisher": org_ref,
            },
            {
                "@context": "https://schema.org",
                "@type": "SoftwareApplication",
                "name": brand,
                "applicationCategory": "BusinessApplication",
                "description": self.site.get(
                    "product_summary",
                    "Workflow automation engine for revenue teams — eliminating non-selling work.",
                ),
            },
        ]


        return ContentAsset(
            slug=slug,
            page_type="landing_page",
            title=title,
            seo_title=seo_title,
            meta_description=meta_description,
            h1=title,
            body_markdown=body,
            schema_markup=schema_markup,
            internal_link_suggestions=[],
            call_to_action=self._cta_block(stage),
            source_keywords=[keyword, *[item.keyword for item in cluster.opportunities[1:4]]],
            target_persona=target_persona,
            eeat_notes=[
                "Add a product screenshot and a real workflow example for this landing page.",
                "Add outcome proof tied to demos, reply rates, or operational lift.",
            ],
            stage=stage,
            industry="Sales Operations",
            date_published=today,
            date_modified=today,
            author_name=self.config.get("growth_engine", {}).get("default_author", "Pipeleap Team"),
            cta_variants=self._lp_cta_variants(stage),
            hreflang_hints=self._lp_hreflang_hints(slug),
            eeat_checklist=[
                {"item": "Author byline", "status": "missing", "instructions": "Add a RevOps or growth operator byline with a LinkedIn or bio link."},
                {"item": "Publication date", "status": "auto-filled", "instructions": "datePublished set in schema. Verify CMS renders it in the HTML head."},
                {"item": "Product screenshot", "status": "missing", "instructions": "Insert at least one real product screenshot showing the workflow builder or CRM sync output."},
                {"item": "Outcome proof point", "status": "missing", "instructions": "Add a quantified result: reply rate lift, CRM hygiene improvement, or a named customer quote."},
                {"item": "Third-party validation", "status": "missing", "instructions": "Link to a G2 review, Capterra listing, or press mention."},
            ],
        )

    def _lp_hreflang_hints(self, slug: str) -> list[dict[str, str]]:
        location_codes: list[int] = self.config.get("growth_engine", {}).get(
            "dataforseo_global_location_codes", []
        )
        site_url = self.site.get("site_url", "https://pipeleap.com").rstrip("/")
        page_url = f"{site_url}/{slug}"
        hints: list[dict[str, str]] = [
            {"hreflang": "x-default", "href": page_url},
            {"hreflang": "en", "href": page_url},
        ]
        for code in location_codes:
            lang = _LOCATION_TO_HREFLANG.get(code)
            if lang:
                hints.append({"hreflang": lang, "href": page_url})
        return hints

    def _lp_cta_variants(self, stage: str = "") -> list[dict[str, Any]]:
        primary_url = self.cta.get("primary_url", self.site.get("site_url", "https://pipeleap.com"))
        return [
            {"label": "Book a demo", "url": primary_url, "variant": "A"},
            {"label": "Get a free sales ops audit", "url": primary_url, "variant": "B"},
            {"label": "Book a demo", "url": primary_url, "variant": "C"},
        ]

    @staticmethod
    def _detect_stage(keyword: str) -> str:
        kw = keyword.lower()
        early_signals = {"startup", "early stage", "pre-sdr", "founder", "early-stage", "0 to 1", "pre-seed", "seed"}
        growth_signals = {"series a", "series b", "growing", "sdr team", "growth stage", "growth-stage"}
        scale_signals = {"enterprise", "revops", "multi-territory", "governance", "at scale", "enterprise-saas"}
        if any(s in kw for s in early_signals):
            return "early"
        if any(s in kw for s in scale_signals):
            return "scale"
        if any(s in kw for s in growth_signals):
            return "growth"
        return ""

    def _cta_block(self, stage: str = "") -> str:
        stage_cta = STAGE_CTA.get(stage, {})
        primary_label = stage_cta.get("primary_label") or self.cta.get("primary_label", "Book a demo")
        primary_url = self.cta.get("primary_url", self.site.get("site_url", "https://pipeleap.com"))
        secondary_label = self.cta.get("secondary_label", "See how it works")
        secondary_url = self.cta.get("secondary_url", self.site.get("site_url", "https://pipeleap.com"))
        urgency = stage_cta.get("urgency", "")
        subtext = stage_cta.get("primary_subtext", "")
        cta = f"[{primary_label}]({primary_url})"
        if subtext:
            cta += f" — {subtext}"
        cta += f" or [{secondary_label}]({secondary_url}) to start building immediately."
        if urgency:
            cta += f"\n\n_{urgency}_"
        return cta
