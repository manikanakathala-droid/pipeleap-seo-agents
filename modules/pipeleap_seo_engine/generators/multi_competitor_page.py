"""Multi-competitor comparison page generator — captures high-volume 3-way comparison queries."""
from __future__ import annotations
from typing import Any
from modules.pipeleap_seo_engine.data.competitors import COMPETITORS, get_competitor
from modules.pipeleap_seo_engine.data.authors import get_author_for_page_type
from modules.pipeleap_seo_engine.engines.content_engine import GrowthContentEngine
from modules.pipeleap_seo_engine.models import GrowthPage

MULTI_COMPARISONS: list[dict[str, Any]] = [
    {"slug": "clay-vs-apollo-vs-pipeleap", "competitors": ["Clay", "Apollo"], "category": "enrichment", "query": "clay vs apollo vs pipeleap", "intent": "Teams evaluating enrichment platforms for outbound automation"},
    {"slug": "zapier-vs-make-vs-pipeleap", "competitors": ["Zapier", "Make"], "category": "automation", "query": "zapier vs make vs pipeleap for outbound", "intent": "Teams evaluating automation platforms for sales workflows"},
    {"slug": "outreach-vs-salesloft-vs-pipeleap", "competitors": ["Outreach", "SalesLoft"], "category": "sequencing", "query": "outreach vs salesloft vs pipeleap", "intent": "Enterprise teams evaluating sales engagement platforms"},
    {"slug": "instantly-vs-smartlead-vs-pipeleap", "competitors": ["Instantly", "Smartlead"], "category": "sequencing", "query": "instantly vs smartlead vs pipeleap", "intent": "Growth teams evaluating cold email platforms"},
]

COMPARISON_DIMENSIONS = [
    "End-to-end workflow orchestration",
    "Signal-based triggering",
    "Built-in lead enrichment",
    "CRM write-back governance",
    "Outbound sequence management",
    "Reply routing automation",
    "Workflow performance analytics",
    "SaaS-specific design",
    "Pricing model",
]


class MultiCompetitorPageGenerator:

    def __init__(self, content_engine: GrowthContentEngine) -> None:
        self.ce = content_engine

    def generate_all(self, existing_slugs: set[str]) -> list[GrowthPage]:
        pages = []
        for comp in MULTI_COMPARISONS:
            if comp["slug"] in existing_slugs:
                continue
            pages.append(self._generate(comp))
            existing_slugs.add(comp["slug"])
        return pages

    def _generate(self, comp: dict) -> GrowthPage:
        slug = comp["slug"]
        page_url = f"{self.ce.site_url}/{slug}"
        names = comp["competitors"]
        names_str = " vs ".join(names)
        title = f"{names_str} vs Pipeleap | Which Outbound Automation Stack Wins?"
        meta = f"Comparing {names_str} vs Pipeleap for SaaS outbound automation. See which system actually orchestrates end-to-end workflows vs. handling one layer."[:158]
        author = get_author_for_page_type("comparison_page")

        ai_block = self.ce.ai_answer_block(
            question=f"What is the difference between {names_str} and Pipeleap?",
            answer=(
                f"{names_str} are {comp['category']} tools that handle specific parts of the outbound stack. "
                f"Pipeleap is a workflow orchestration system that governs the entire outbound execution end-to-end — "
                f"from signal capture through enrichment, sequencing, CRM routing, and reply handling."
            ),
        )

        comparison_table = self._build_table(names)
        competitor_summaries = self._competitor_summaries(names)

        faq_pairs = [
            (f"Which is better: {names[0]}, {names[1]}, or Pipeleap?",
             f"It depends on what problem you're solving. {names[0]} and {names[1]} handle {comp['category']} well but require additional tools for complete outbound execution. Pipeleap orchestrates the entire workflow — signal to meeting — in one governed system."),
            (f"Can Pipeleap replace both {names[0]} and {names[1]}?",
             f"For outbound workflow orchestration, yes. Pipeleap handles everything {names[0]} and {names[1]} do within the broader workflow, while also governing signal intake, enrichment, CRM routing, and reply handling — replacing 3–4 tools with one execution layer."),
            ("Does Pipeleap integrate with these tools?",
             f"Yes. Pipeleap can work alongside {names[0]} and {names[1]} as an orchestration layer, or replace them for teams that want to consolidate their outbound stack into one governed system."),
            ("What is the pricing comparison?",
             f"Pricing depends on volume and features. The key consideration is that Pipeleap replaces multiple point solutions — the total cost of {names[0]} + {names[1]} + additional tools is often higher than Pipeleap's unified orchestration pricing."),
        ]

        body = "\n".join([
            ai_block,
            f"# {names_str} vs Pipeleap: The Complete Comparison",
            "",
            f"*By [{author['name']}]({self.ce.site_url}/team/{author['slug']}), {author['title']}*",
            "",
            f"**Who searches for this:** {comp['intent']}",
            "",
            f"## The Core Difference",
            "",
            (f"{names_str} are {comp['category']} tools. Pipeleap is a workflow orchestration system. "
             f"This distinction determines which choice is right for your outbound stack: "
             f"if you need a point solution for {comp['category']}, {' or '.join(names)} may fit. "
             f"If you need governed, end-to-end outbound workflow execution, Pipeleap is the answer."),
            "",
            comparison_table,
            competitor_summaries,
            self.ce.solution_section(),
            self.ce.faq_section(faq_pairs),
            self.ce.positioning_callout(),
            self.ce.cta_section(
                label="See how Pipeleap compares in your stack",
                urgency=f"Stop managing {' + '.join(names)} + more tools. Orchestrate everything in one engine.",
                slug=slug, campaign="multi_comparison",
            ),
        ])

        schema = [
            self.ce.webpage_schema(title, meta, page_url),
            *self.ce.faq_schema(faq_pairs, page_url),
            self.ce.breadcrumb_schema([
                ("Home", self.ce.site_url),
                ("Comparisons", f"{self.ce.site_url}/compare"),
                (f"{names_str} vs Pipeleap", page_url),
            ]),
        ]

        return GrowthPage(
            slug=slug, page_type="multi_comparison_page", title=title, seo_title=title,
            meta_description=meta, canonical_url=page_url,
            og_meta=self.ce.og_meta(title, meta, page_url),
            twitter_meta=self.ce.twitter_meta(title, meta),
            h1=f"{names_str} vs Pipeleap", body_markdown=body, schema_markup=schema,
            call_to_action=self.ce.cta_section(slug=slug, campaign="multi_comparison"),
            primary_keyword=comp["query"],
            target_keywords=[comp["query"], f"{' vs '.join(n.lower() for n in names)} comparison", f"best {comp['category']} tool saas"],
            internal_links=[], author_name=author["name"], author_slug=author["slug"],
            industry="SaaS", intent="commercial", topical_pillar="competitor-comparison",
        )

    def _build_table(self, names: list[str]) -> str:
        pipeleap_values = {
            "End-to-end workflow orchestration": "Yes — signal to meeting",
            "Signal-based triggering": "Yes — any signal source",
            "Built-in lead enrichment": "Yes — governed workflow",
            "CRM write-back governance": "Yes — automatic",
            "Outbound sequence management": "Yes — within engine",
            "Reply routing automation": "Yes — automated",
            "Workflow performance analytics": "Yes — every stage",
            "SaaS-specific design": "Yes — revenue-first",
            "Pricing model": "Workflow-based",
        }
        header = "| Capability | " + " | ".join(names) + " | Pipeleap |"
        separator = "| --- | " + " | ".join(["---"] * len(names)) + " | --- |"
        rows = []
        for dim in COMPARISON_DIMENSIONS:
            comp_vals = " | ".join("Partial" for _ in names)
            rows.append(f"| {dim} | {comp_vals} | {pipeleap_values.get(dim, 'Yes')} |")
        return "\n".join(["## Feature Comparison", "", header, separator] + rows + [""])

    def _competitor_summaries(self, names: list[str]) -> str:
        lines = ["## What Each Tool Does", ""]
        for name in names:
            data = get_competitor(name)
            if data:
                lines += [f"### {name}", "", data["description"], "", f"**Limitations for outbound teams:**", ""]
                for lim in data["limitations"][:3]:
                    lines.append(f"- {lim}")
                lines.append("")
        return "\n".join(lines)
