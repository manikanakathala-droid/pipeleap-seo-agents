"""Competitor comparison and alternative page generator."""
from __future__ import annotations

from typing import Any

from modules.pipeleap_seo_engine.data.competitors import COMPETITORS, get_competitor
from modules.pipeleap_seo_engine.engines.content_engine import GrowthContentEngine
from modules.pipeleap_seo_engine.models import GrowthPage


class CompetitorPageGenerator:

    def __init__(self, content_engine: GrowthContentEngine) -> None:
        self.ce = content_engine

    def generate_vs_pages(
        self,
        competitor_names: list[str],
        existing_slugs: set[str],
    ) -> list[GrowthPage]:
        pages = []
        for name in competitor_names:
            data = get_competitor(name)
            if not data:
                continue
            if data["slug_vs"] not in existing_slugs:
                page = self._generate_vs(name, data)
                pages.append(page)
                existing_slugs.add(data["slug_vs"])
        return pages

    def generate_alternative_pages(
        self,
        competitor_names: list[str],
        existing_slugs: set[str],
    ) -> list[GrowthPage]:
        pages = []
        for name in competitor_names:
            data = get_competitor(name)
            if not data:
                continue
            if data["slug_alt"] not in existing_slugs:
                page = self._generate_alternative(name, data)
                pages.append(page)
                existing_slugs.add(data["slug_alt"])
        return pages

    # ─── vs page ─────────────────────────────────────────────────────────────

    def _generate_vs(self, name: str, data: dict[str, Any]) -> GrowthPage:
        slug = data["slug_vs"]
        page_url = f"{self.ce.site_url}/{slug}"
        title = f"Pipeleap vs {name} for SaaS Outbound Automation"
        meta = f"Pipeleap vs {name}: an honest comparison for SaaS outbound teams. See which system actually orchestrates end-to-end outbound workflows vs. handling one step."[:158]

        # Featured snippet
        snippet = self.ce.featured_snippet_block(
            f"What is the difference between Pipeleap and {name}?",
            f"Pipeleap is a workflow orchestration system that governs end-to-end outbound execution — signal capture, enrichment, sequencing, CRM routing, and reply handling. "
            f"{name} is a {data['category']} tool focused on a specific part of the outbound stack. "
            f"They solve different problems at different layers.",
        )

        # Intro
        intro = f"## Pipeleap vs {name}: Which Is Right for Your SaaS Outbound Stack?\n\n{data['comparison_intro']}\n"

        # Comparison table
        comparison_table = self._comparison_table(name, data)

        # Limitations block
        limitations = self._limitations_block(name, data["limitations"])

        # Where Pipeleap wins
        wins = self._wins_block(data["pipeleap_wins"])

        # Best for
        default_best_for = f"{name} is the right choice for teams that only need a dedicated {data['category']} solution and already have the rest of the outbound stack covered."
        best_for = f"## When {name} Is the Right Choice\n\n{data.get('best_for', default_best_for)}\n"

        # Positioning
        positioning = self.ce.positioning_callout()

        # FAQ
        faq_pairs = [
            (f"Does Pipeleap replace {name}?", f"Not necessarily. Pipeleap is an orchestration layer that can work alongside {name} — governing the workflow that determines when and how {name} executes. For teams that want to eliminate {name} and consolidate, Pipeleap handles {data['category']} as part of the unified workflow."),
            (f"What does Pipeleap do that {name} doesn't?", f"Pipeleap orchestrates the entire outbound workflow end-to-end — signal detection, enrichment, sequencing, CRM routing, and reply handling. {name} handles {data['category']} specifically. Pipeleap is the execution layer that governs all of this in one system."),
            ("Is Pipeleap a CRM?", "No. Pipeleap is a workflow orchestration system, not a CRM. It governs the workflows that populate and update your CRM with clean, enriched pipeline data automatically."),
            (f"Is Pipeleap more expensive than {name}?", f"Pricing depends on outbound volume and workflow complexity. Pipeleap replaces multiple point solutions — the total cost of {name} plus the other tools you need is often higher than Pipeleap's unified orchestration pricing."),
        ]
        faq = self.ce.faq_section(faq_pairs)

        # CTA
        cta = self.ce.cta_section(
            label="See How Pipeleap Orchestrates Outbound",
            urgency=f"Stop managing {name} plus 4 other tools. Orchestrate everything in one workflow engine.",
        )

        stats = self.ce.statistics_section()
        from modules.pipeleap_seo_engine.data.authors import get_author_for_page_type
        author = get_author_for_page_type("comparison_page")
        body = "\n".join([snippet, self.ce.author_byline(author), intro, stats, comparison_table, limitations, wins, best_for, positioning, faq, cta])

        schema = [
            self.ce.webpage_schema(title, meta, page_url),
            self.ce.breadcrumb_schema([("Home", self.ce.site_url), ("Compare", f"{self.ce.site_url}/compare"), (f"Pipeleap vs {name}", page_url)]),
            *self.ce.faq_schema(faq_pairs, page_url),
        ]

        return GrowthPage(
            slug=slug,
            page_type="comparison_page",
            title=title,
            seo_title=f"Pipeleap vs {name} | SaaS Outbound Automation Comparison",
            meta_description=meta,
            canonical_url=page_url,
            og_meta=self.ce.og_meta(title, meta, page_url),
            twitter_meta=self.ce.twitter_meta(title, meta),
            h1=f"Pipeleap vs {name}",
            body_markdown=body,
            schema_markup=schema,
            call_to_action=self.ce.cta_section(label="See Pipeleap in action", slug=slug, campaign="comparison"),
            primary_keyword=f"pipeleap vs {name.lower()}",
            target_keywords=[f"pipeleap vs {name.lower()}", f"{name.lower()} vs pipeleap", f"pipeleap vs {name.lower()} for saas"],
            internal_links=[],
            author_name=author["name"], author_slug=author["slug"],
            breadcrumbs=[("Home", self.ce.site_url), ("Compare", f"{self.ce.site_url}/compare"), (f"Pipeleap vs {name}", page_url)],
            competitor=name, industry="SaaS", intent="commercial",
            topical_pillar="competitor-comparison",
        )

    # ─── alternative page ─────────────────────────────────────────────────────

    def _generate_alternative(self, name: str, data: dict[str, Any]) -> GrowthPage:
        slug = data["slug_alt"]
        page_url = f"{self.ce.site_url}/{slug}"
        title = f"{name} Alternative for SaaS Outbound Automation"
        meta = f"Looking for a {name} alternative? See why SaaS teams switch to Pipeleap's workflow orchestration system for predictable outbound pipeline."[:158]

        snippet = self.ce.featured_snippet_block(
            f"What is the best {name} alternative for SaaS outbound?",
            f"The best {name} alternative for SaaS teams that need end-to-end outbound workflow orchestration is Pipeleap. "
            f"Unlike {name}, Pipeleap orchestrates signal capture, enrichment, sequencing, CRM routing, and reply handling in one governed workflow — not just {data['category']}.",
        )

        intro = (
            f"## Why SaaS Teams Look for a {name} Alternative\n\n"
            f"Teams searching for a {name} alternative are typically hitting one of these limitations:\n\n"
            + "\n".join(f"- {lim}" for lim in data["limitations"]) + "\n"
        )

        pipeleap_diff = (
            f"## What Pipeleap Does Differently\n\n"
            f"Pipeleap isn't just another {data['category']} tool — it's a workflow orchestration system "
            f"that replaces your entire fragmented outbound stack with one governed execution layer.\n\n"
            + "\n".join(f"- {win}" for win in data["pipeleap_wins"]) + "\n"
        )

        how_it_works = self.ce.how_it_works_section()
        before_after = self.ce.before_after_section()
        positioning = self.ce.positioning_callout()

        faq_pairs = [
            (f"Why do teams switch from {name} to Pipeleap?", f"Teams switch when they realize {name} handles {data['category']} but doesn't orchestrate the full outbound workflow. Pipeleap replaces the need for {name} plus 3–5 other tools by governing enrichment, sequencing, CRM routing, and reply handling in one system."),
            (f"Is Pipeleap a drop-in replacement for {name}?", f"Pipeleap replaces {name}'s {data['category']} function while also handling everything {name} doesn't — signal detection, workflow orchestration, CRM governance, and performance tracking."),
            ("Does Pipeleap integrate with my existing CRM?", "Yes. Pipeleap writes structured, enriched data back into any CRM on every workflow trigger — keeping your pipeline data clean and current automatically."),
            (f"Is Pipeleap more expensive than {name}?", "Pipeleap replaces multiple point solutions, so the total cost comparison should account for all the tools Pipeleap replaces — not just one-to-one pricing."),
        ]
        faq = self.ce.faq_section(faq_pairs)
        cta = self.ce.cta_section(
            label=f"See Why Teams Switch From {name}",
            urgency=f"Replace {name} and your fragmented outbound stack with one orchestration engine.",
        )

        from modules.pipeleap_seo_engine.data.authors import get_author_for_page_type
        author = get_author_for_page_type("alternative_page")
        stats = self.ce.statistics_section()
        body = "\n".join([snippet, self.ce.author_byline(author), intro, stats, pipeleap_diff, how_it_works, before_after, positioning, faq, cta])
        schema = [
            self.ce.webpage_schema(title, meta, page_url),
            self.ce.breadcrumb_schema([("Home", self.ce.site_url), ("Alternatives", f"{self.ce.site_url}/alternatives"), (f"{name} Alternative", page_url)]),
            *self.ce.faq_schema(faq_pairs, page_url),
        ]

        return GrowthPage(
            slug=slug,
            page_type="alternative_page",
            title=title,
            seo_title=f"{name} Alternative | Pipeleap Outbound Workflow Orchestration",
            meta_description=meta,
            canonical_url=page_url,
            og_meta=self.ce.og_meta(title, meta, page_url),
            twitter_meta=self.ce.twitter_meta(title, meta),
            h1=f"{name} Alternative for SaaS",
            body_markdown=body,
            schema_markup=schema,
            call_to_action=self.ce.cta_section(label=f"Switch from {name}", slug=slug, campaign="alternative"),
            primary_keyword=f"{name.lower()} alternative",
            target_keywords=[f"{name.lower()} alternative", f"{name.lower()} alternative for saas", f"best {name.lower()} alternative"],
            internal_links=[],
            author_name=author["name"], author_slug=author["slug"],
            breadcrumbs=[("Home", self.ce.site_url), ("Alternatives", f"{self.ce.site_url}/alternatives"), (f"{name} Alternative", page_url)],
            competitor=name,
            industry="SaaS",
            topical_pillar="competitor-comparison",
            intent="commercial",
        )

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _comparison_table(self, name: str, data: dict[str, Any]) -> str:
        rows = [
            ("End-to-end workflow orchestration", "Yes — signal to meeting", f"Partial — {data['category']} only"),
            ("Signal-based triggering", "Yes — any signal source", "No native support"),
            ("Built-in enrichment", "Yes — governed workflow", "Varies"),
            ("CRM write-back governance", "Yes — automatic on every trigger", "Manual / limited"),
            ("Sequencing", "Yes — within workflow engine", "Depends on tool category"),
            ("Reply routing & booking", "Yes — automated", "No"),
            ("Workflow performance tracking", "Yes — every stage", "Basic"),
            ("SaaS-specific design", "Yes — revenue workflow-first", "General purpose"),
        ]
        lines = [
            f"## Pipeleap vs {name}: Feature Comparison",
            "",
            "| Capability | Pipeleap | " + name + " |",
            "| --- | --- | --- |",
        ]
        for cap, pipeleap, competitor in rows:
            lines.append(f"| {cap} | {pipeleap} | {competitor} |")
        lines.append("")
        return "\n".join(lines)

    def _limitations_block(self, name: str, limitations: list[str]) -> str:
        lines = [f"## {name} Limitations for SaaS Outbound Teams", ""]
        for lim in limitations:
            lines.append(f"- {lim}")
        lines.append("")
        return "\n".join(lines)

    def _wins_block(self, wins: list[str]) -> str:
        lines = ["## Where Pipeleap Wins", ""]
        for win in wins:
            lines.append(f"- {win}")
        lines.append("")
        return "\n".join(lines)
