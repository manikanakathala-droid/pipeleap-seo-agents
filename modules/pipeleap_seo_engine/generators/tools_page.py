"""Tools page generator — differentiated operator guides, one per category."""
from __future__ import annotations

from modules.pipeleap_seo_engine.data.tools_data import TOOLS_DATA
from modules.pipeleap_seo_engine.data.authors import get_author_for_page_type
from modules.pipeleap_seo_engine.engines.content_engine import GrowthContentEngine
from modules.pipeleap_seo_engine.models import GrowthPage


class ToolsPageGenerator:

    def __init__(self, content_engine: GrowthContentEngine) -> None:
        self.ce = content_engine

    def generate_all(self, existing_slugs: set[str]) -> list[GrowthPage]:
        pages = []
        for tool in TOOLS_DATA:
            slug = f"tools/{tool['slug']}"
            if slug in existing_slugs:
                continue
            pages.append(self._generate(tool))
            existing_slugs.add(slug)
        return pages

    def _generate(self, tool: dict) -> GrowthPage:
        slug = f"tools/{tool['slug']}"
        page_url = f"{self.ce.site_url}/{slug}"
        title = f"{tool['title']} | Pipeleap"
        meta = (
            f"{tool['tool_name']} in a governed outbound stack: what it does, where it breaks at scale, "
            f"and how Pipeleap's workflow engine connects around it."
        )[:158]
        author = get_author_for_page_type("tools_page")

        # Comparison table
        comparison_rows = "\n".join([
            f"| {row[0]} | {row[1]} | {row[2]} |"
            for row in tool["comparison_rows"]
        ])
        comparison_table = "\n".join([
            f"| Capability | {tool['tool_name']} | With Pipeleap governance |",
            "| --- | --- | --- |",
            comparison_rows,
        ])

        # FAQ section
        faq_md = "\n\n".join([
            f"**{q}**\n\n{a}"
            for q, a in tool["faqs"]
        ])

        body = "\n".join([
            self.ce.ai_answer_block(
                question=f"How do revenue teams use {tool['tool_name']} in a governed outbound stack?",
                answer=(
                    f"{tool['tool_name']} handles {tool['category'].lower()}. "
                    f"Pipeleap's workflow engine governs the intake, qualification, CRM write-back, "
                    f"and reply routing layer that surrounds it."
                ),
            ),
            f"# {tool['h1']}",
            "",
            f"*By [{author['name']}]({self.ce.site_url}/team/{author['slug']}), {author['title']}*",
            "",
            f"## What {tool['tool_name']} does",
            "",
            tool["tool_what"],
            "",
            f"## Where {tool['tool_name']} breaks at scale",
            "",
            tool["tool_where_it_breaks"],
            "",
            "## The operational gap",
            "",
            tool["pipeleap_layer"],
            "",
            "## Capability breakdown",
            "",
            comparison_table,
            "",
            "## Common questions",
            "",
            faq_md,
            "",
            self.ce.cta_section(
                label=f"See how Pipeleap connects around {tool['tool_name']}",
                urgency=tool["pain"],
                slug=slug,
                campaign="tools_page",
            ),
        ])

        schema = [
            self.ce.webpage_schema(title, meta, page_url),
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a},
                    }
                    for q, a in tool["faqs"]
                ],
            },
            self.ce.breadcrumb_schema([
                ("Home", self.ce.site_url),
                ("Tools", f"{self.ce.site_url}/tools"),
                (tool["title"], page_url),
            ]),
        ]

        return GrowthPage(
            slug=slug,
            page_type="tools_page",
            title=title,
            seo_title=title,
            meta_description=meta,
            canonical_url=page_url,
            og_meta=self.ce.og_meta(title, meta, page_url),
            twitter_meta=self.ce.twitter_meta(title, meta),
            h1=tool["h1"],
            body_markdown=body,
            schema_markup=schema,
            call_to_action=self.ce.cta_section(slug=slug, campaign="tools_page"),
            primary_keyword=tool["primary_keyword"],
            target_keywords=tool["keywords"],
            internal_links=[],
            author_name=author["name"],
            author_slug=author["slug"],
            industry="SaaS",
            intent="informational",
            topical_pillar=tool["topical_pillar"],
            breadcrumbs=[
                ("Home", self.ce.site_url),
                ("Tools", f"{self.ce.site_url}/tools"),
                (tool["title"], page_url),
            ],
        )
