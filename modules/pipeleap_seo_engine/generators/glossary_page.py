"""Glossary and entity definition page generator — AI Overview + featured snippet capture."""
from __future__ import annotations
from modules.pipeleap_seo_engine.data.entities import ENTITIES, entities_by_category, entity_schema
from modules.pipeleap_seo_engine.data.authors import get_author_for_page_type
from modules.pipeleap_seo_engine.engines.content_engine import GrowthContentEngine
from modules.pipeleap_seo_engine.models import GrowthPage

_CATEGORY_META = {
    "automation": {
        "label": "Workflow & Automation",
        "slug": "glossary/automation",
        "title": "Workflow Automation Glossary | SaaS Automation Terms Defined",
        "meta": "Definitions for every key workflow and automation term — workflow orchestration, outbound automation, CRM automation, SDR automation, and more.",
        "h1": "Workflow & Automation Glossary",
        "keywords": ["workflow automation glossary", "outbound automation terms", "saas automation glossary"],
    },
    "sales": {
        "label": "Sales",
        "slug": "glossary/sales",
        "title": "B2B Sales Glossary | Key Sales Terms for SaaS Teams",
        "meta": "Clear definitions for every B2B sales term — SQLs, cold email, buying signals, sales cadences, AI SDRs, and more — from Pipeleap.",
        "h1": "B2B Sales Glossary",
        "keywords": ["b2b sales glossary", "saas sales terms", "sales terminology b2b"],
    },
    "marketing": {
        "label": "Marketing",
        "slug": "glossary/marketing",
        "title": "B2B Marketing Glossary | Marketing Terms for SaaS Revenue Teams",
        "meta": "Definitions for every key B2B marketing term — MQLs, intent data, ABM, content marketing, CRO — as they apply to SaaS pipeline generation.",
        "h1": "B2B Marketing Glossary",
        "keywords": ["b2b marketing glossary", "saas marketing terms", "marketing terminology saas"],
    },
    "revops": {
        "label": "Revenue Operations",
        "slug": "glossary/revops",
        "title": "RevOps Glossary | Revenue Operations Terms Defined",
        "meta": "Definitions for every key revenue operations term — ARR, MRR, NRR, CAC, LTV, ICP, GTM strategy — as they apply to SaaS growth.",
        "h1": "Revenue Operations (RevOps) Glossary",
        "keywords": ["revops glossary", "revenue operations terms", "saas revops terminology"],
    },
}


class GlossaryPageGenerator:

    def __init__(self, content_engine: GrowthContentEngine) -> None:
        self.ce = content_engine
        try:
            from modules.pipeleap_seo_engine.glossary.semantic_linker import GlossarySemanticLinker
            self._linker = GlossarySemanticLinker(ENTITIES, self.ce.site_url)
            self._link_map = self._linker.build_link_map()
        except Exception:
            self._link_map = {}

    def generate_index(self, existing_slugs: set[str]) -> list[GrowthPage]:
        pages = []
        for slug, entity in ENTITIES.items():
            page_slug = f"glossary/{slug}"
            if page_slug in existing_slugs:
                continue
            pages.append(self._generate_term_page(slug, entity))
            existing_slugs.add(page_slug)

        # Hub index page
        if "glossary" not in existing_slugs:
            pages.append(self._generate_index_page())
            existing_slugs.add("glossary")

        # Category index pages
        for cat_key, cat_meta in _CATEGORY_META.items():
            cat_slug = cat_meta["slug"]
            if cat_slug not in existing_slugs:
                pages.append(self._generate_category_page(cat_key, cat_meta))
                existing_slugs.add(cat_slug)

        return pages

    def _generate_term_page(self, slug: str, entity: dict) -> GrowthPage:
        page_slug = f"glossary/{slug}"
        page_url = f"{self.ce.site_url}/{page_slug}"
        title = f"What is {entity['term']}? | Definition for SaaS Revenue Teams"
        meta = f"{entity['short_definition'][:158]}"
        author = get_author_for_page_type("glossary_page")

        ai_block = self.ce.ai_answer_block(
            question=f"What is {entity['term']}?",
            answer=entity["short_definition"],
        )

        # Semantic links for this term (computed graph, not manual list)
        sem_links = self._link_map.get(slug, [])

        body_parts = [
            ai_block,
            f"# What is {entity['term']}?",
            "",
            f"*By [{author['name']}]({self.ce.site_url}/team/{author['slug']}), {author['title']}*",
            "",
            "## Definition",
            "",
            entity["definition"],
            "",
            f"## {entity['term']} in the Context of Pipeleap",
            "",
            entity["pipeleap_context"],
            "",
            (
                f"When SaaS revenue teams implement {entity['term'].lower()} through Pipeleap's workflow "
                f"orchestration engine, the result is predictable pipeline generation that compounds over time — "
                f"without proportional manual effort or headcount growth."
            ),
            "",
            f"## Related Concepts",
            "",
        ]
        # Use semantic linker output when available; fall back to declared related_terms
        if sem_links:
            for link in sem_links[:5]:
                body_parts.append(f"- **[{link['anchor_text']}]({link['target_url']})**")
        else:
            for related in entity.get("related_terms", []):
                rel_slug = related.lower().replace(" ", "-")
                body_parts.append(f"- **[{related}]({self.ce.site_url}/glossary/{rel_slug})**")
        body_parts += [
            "",
            f"## How SaaS Teams Use {entity['term']}",
            "",
            self._use_context(entity),
            "",
            self.ce.faq_section(self._faq_pairs(entity)),
            self.ce.cta_section(
                label="See Pipeleap in action",
                urgency=f"See how {entity['term'].lower()} powers Pipeleap's outbound orchestration engine.",
                slug=page_slug,
                campaign="glossary",
            ),
        ]

        body = "\n".join(body_parts)
        schema = [
            self.ce.webpage_schema(title, meta, page_url),
            entity_schema(entity, self.ce.site_url),
            self.ce.breadcrumb_schema([
                ("Home", self.ce.site_url),
                ("Glossary", f"{self.ce.site_url}/glossary"),
                (entity["term"], page_url),
            ]),
            *self.ce.faq_schema(self._faq_pairs(entity), page_url),
        ]

        return GrowthPage(
            slug=page_slug,
            page_type="glossary_page",
            title=title,
            seo_title=title,
            meta_description=meta,
            canonical_url=page_url,
            og_meta=self.ce.og_meta(title, meta, page_url),
            twitter_meta=self.ce.twitter_meta(title, meta),
            h1=f"What is {entity['term']}?",
            body_markdown=body,
            schema_markup=schema,
            call_to_action=self.ce.cta_section(slug=page_slug, campaign="glossary"),
            primary_keyword=entity["keywords"][0] if entity.get("keywords") else slug,
            target_keywords=entity.get("keywords", [slug]),
            internal_links=[],
            author_name=author["name"],
            author_slug=author["slug"],
            breadcrumbs=[("Home", self.ce.site_url), ("Glossary", f"{self.ce.site_url}/glossary"), (entity["term"], page_url)],
            glossary_term=slug,
            industry="SaaS",
            intent="informational",
            topical_pillar="glossary",
        )

    def _generate_category_page(self, cat_key: str, cat_meta: dict) -> GrowthPage:
        page_url = f"{self.ce.site_url}/{cat_meta['slug']}"
        title = cat_meta["title"]
        meta = cat_meta["meta"]
        author = get_author_for_page_type("glossary_page")
        cat_entities = entities_by_category(cat_key)

        term_list = "\n".join(
            f"- **[{e['term']}]({self.ce.site_url}/glossary/{s})** — {e['short_definition']}"
            for s, e in cat_entities.items()
        )

        body = "\n".join([
            f"# {cat_meta['h1']}",
            "",
            f"*By [{author['name']}]({self.ce.site_url}/team/{author['slug']})*",
            "",
            meta,
            "",
            "## Terms",
            "",
            term_list or "_No terms in this category yet._",
            "",
            f"[← Back to full glossary]({self.ce.site_url}/glossary)",
            "",
            self.ce.cta_section(label=f"See how Pipeleap applies these concepts", slug=cat_meta["slug"], campaign="glossary_category"),
        ])

        items = [{"name": e["term"], "url": f"{self.ce.site_url}/glossary/{s}"} for s, e in cat_entities.items()]
        schema = [
            self.ce.webpage_schema(title, meta, page_url),
            self.ce.item_list_schema(items, cat_meta["h1"], page_url),
            self.ce.breadcrumb_schema([
                ("Home", self.ce.site_url),
                ("Glossary", f"{self.ce.site_url}/glossary"),
                (cat_meta["label"], page_url),
            ]),
        ]

        return GrowthPage(
            slug=cat_meta["slug"],
            page_type="glossary_page",
            title=title,
            seo_title=title,
            meta_description=meta,
            canonical_url=page_url,
            og_meta=self.ce.og_meta(title, meta, page_url, og_type="website"),
            twitter_meta=self.ce.twitter_meta(title, meta),
            h1=cat_meta["h1"],
            body_markdown=body,
            schema_markup=schema,
            call_to_action=self.ce.cta_section(slug=cat_meta["slug"], campaign="glossary_category"),
            primary_keyword=cat_meta["keywords"][0],
            target_keywords=cat_meta["keywords"],
            internal_links=[],
            author_name=author["name"],
            author_slug=author["slug"],
            breadcrumbs=[
                ("Home", self.ce.site_url),
                ("Glossary", f"{self.ce.site_url}/glossary"),
                (cat_meta["label"], page_url),
            ],
            industry="SaaS",
            intent="informational",
            topical_pillar="glossary",
        )

    def _generate_index_page(self) -> GrowthPage:
        page_url = f"{self.ce.site_url}/glossary"
        title = "SaaS Outbound Automation Glossary | Key Terms for Revenue Teams"
        meta = "Definitions for every key term in SaaS outbound automation, workflow orchestration, and pipeline generation — from Pipeleap."
        author = get_author_for_page_type("glossary_page")

        term_list = "\n".join(
            f"- **[{e['term']}](/{self.ce.site_url}/glossary/{slug})** — {e['short_definition']}"
            for slug, e in ENTITIES.items()
        )

        body = "\n".join([
            f"# SaaS Outbound Automation Glossary",
            "",
            f"*By [{author['name']}]({self.ce.site_url}/team/{author['slug']})*",
            "",
            "A comprehensive glossary of key terms for SaaS revenue teams building automated outbound pipeline systems. Every definition includes context for how the term applies to workflow orchestration and predictable pipeline generation.",
            "",
            "## Terms",
            "",
            term_list,
            "",
            self.ce.cta_section(label="See how these concepts power Pipeleap", slug="glossary", campaign="glossary_index"),
        ])

        items = [{"name": e["term"], "url": f"{self.ce.site_url}/glossary/{s}"} for s, e in ENTITIES.items()]
        schema = [
            self.ce.webpage_schema(title, meta, page_url),
            self.ce.item_list_schema(items, "SaaS Outbound Automation Glossary", page_url),
        ]

        return GrowthPage(
            slug="glossary",
            page_type="glossary_page",
            title=title,
            seo_title=title,
            meta_description=meta,
            canonical_url=page_url,
            og_meta=self.ce.og_meta(title, meta, page_url, og_type="website"),
            twitter_meta=self.ce.twitter_meta(title, meta),
            h1="SaaS Outbound Automation Glossary",
            body_markdown=body,
            schema_markup=schema,
            call_to_action=self.ce.cta_section(slug="glossary", campaign="glossary_index"),
            primary_keyword="saas outbound automation glossary",
            target_keywords=["saas outbound glossary", "outbound automation terms", "workflow orchestration glossary"],
            internal_links=[],
            author_name=author["name"],
            author_slug=author["slug"],
            industry="SaaS",
            intent="informational",
            topical_pillar="glossary",
        )

    @staticmethod
    def _use_context(entity: dict) -> str:
        contexts = {
            "workflow-orchestration": "SaaS revenue teams implement workflow orchestration to replace fragmented point-solution stacks with one governed execution layer. RevOps teams use it to build repeatable outbound systems. Founders use it to generate pipeline before hiring SDRs. VP Sales use it to give every rep the same winning playbook.",
            "outbound-automation": "Growth-stage SaaS companies use outbound automation to scale pipeline without proportional SDR headcount. Early-stage teams use it to run outbound before making their first sales hire. Enterprise teams use it to enforce consistent execution across territories.",
            "signal-based-outbound": "B2B SaaS teams use signal-based outbound to reach prospects at moments of genuine buying intent — when they visit the pricing page, when they install a competitor, or when their company raises a funding round. Reply rates for signal-triggered outreach are typically 3–5× higher than static list campaigns.",
        }
        return contexts.get(entity.get("slug", ""), (
            f"SaaS revenue teams use {entity['term'].lower()} to build more efficient, "
            f"consistent, and scalable outbound pipeline systems. The core benefit is the "
            f"same regardless of company stage: more pipeline with less manual execution."
        ))

    @staticmethod
    def _faq_pairs(entity: dict) -> list[tuple[str, str]]:
        term = entity["term"]
        return [
            (f"What is {term} in simple terms?", entity["short_definition"]),
            (f"How does Pipeleap use {term}?", entity["pipeleap_context"] + " " + "This means every outbound workflow runs through a governed, automated engine that produces consistent pipeline without manual intervention."),
            (f"Why is {term} important for SaaS revenue teams?", f"{term} is important because it replaces manual execution — the primary bottleneck in SaaS outbound — with automated, governed workflows that scale without proportional headcount growth."),
        ]
