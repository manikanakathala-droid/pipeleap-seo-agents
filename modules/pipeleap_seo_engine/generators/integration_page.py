"""Integration page generator — high-converting long-tail pages for stack-fit queries."""
from __future__ import annotations
from modules.pipeleap_seo_engine.data.integrations import INTEGRATIONS
from modules.pipeleap_seo_engine.data.authors import get_author_for_page_type
from modules.pipeleap_seo_engine.engines.content_engine import GrowthContentEngine
from modules.pipeleap_seo_engine.models import GrowthPage


class IntegrationPageGenerator:

    def __init__(self, content_engine: GrowthContentEngine) -> None:
        self.ce = content_engine

    def generate_all(self, existing_slugs: set[str]) -> list[GrowthPage]:
        pages = []
        for integration in INTEGRATIONS:
            slug = f"integrations/pipeleap-{integration['slug']}"
            if slug in existing_slugs:
                continue
            pages.append(self._generate(integration))
            existing_slugs.add(slug)
        return pages

    def _generate(self, intg: dict) -> GrowthPage:
        name = intg["name"]
        slug = f"integrations/pipeleap-{intg['slug']}"
        page_url = f"{self.ce.site_url}/{slug}"
        title = f"Pipeleap + {name} Integration | Automate Your Outbound Workflow"
        meta = f"Connect Pipeleap with {name} to automate your outbound workflow end-to-end. {intg['description'][:100]}"[:158]
        author = get_author_for_page_type("integration_page")

        ai_block = self.ce.ai_answer_block(
            question=f"How does Pipeleap integrate with {name}?",
            answer=f"Pipeleap integrates with {name} as part of its end-to-end workflow orchestration engine. {intg['description']}"
        )

        body = "\n".join([
            ai_block,
            f"# Pipeleap + {name}: Automated Outbound Workflow Orchestration",
            "",
            f"*By [{author['name']}]({self.ce.site_url}/team/{author['slug']}), {author['title']}*",
            "",
            f"## What This Integration Does",
            "",
            intg["description"],
            "",
            intg["use_case"],
            "",
            f"## The Problem This Integration Solves",
            "",
            f"Most teams use {name} as a standalone tool — manually exporting data, importing lists, "
            f"and triggering actions one-by-one. This creates the same bottleneck every time: "
            f"more pipeline requires more manual effort. The Pipeleap + {name} integration eliminates "
            f"every manual handoff between signal detection and outbound execution.",
            "",
            self.ce.how_it_works_section(slug=slug),
            self.ce.before_after_section(),
            f"## How the Pipeleap + {name} Workflow Runs",
            "",
            f"```text",
            f"Signal detected → Pipeleap workflow triggered → {name} action executed → CRM updated → Reply routed",
            f"```",
            "",
            f"Every step is automatic. Every handoff is governed. No manual intervention required.",
            "",
            self.ce.faq_section(self._faq_pairs(name)),
            self.ce.positioning_callout(),
            self.ce.cta_section(
                label=f"Set up your Pipeleap + {name} workflow",
                urgency=f"Replace manual {name} management with governed workflow orchestration.",
                slug=slug,
                campaign="integration",
            ),
        ])

        schema = [
            self.ce.webpage_schema(title, meta, page_url),
            self.ce.howto_schema(f"How to integrate Pipeleap with {name}", intg["description"], page_url),
            self.ce.breadcrumb_schema([
                ("Home", self.ce.site_url),
                ("Integrations", f"{self.ce.site_url}/integrations"),
                (f"Pipeleap + {name}", page_url),
            ]),
            *self.ce.faq_schema(self._faq_pairs(name), page_url),
        ]

        return GrowthPage(
            slug=slug, page_type="integration_page", title=title, seo_title=title,
            meta_description=meta, canonical_url=page_url,
            og_meta=self.ce.og_meta(title, meta, page_url),
            twitter_meta=self.ce.twitter_meta(title, meta),
            h1=f"Pipeleap + {name} Integration",
            body_markdown=body, schema_markup=schema,
            call_to_action=self.ce.cta_section(slug=slug, campaign="integration"),
            primary_keyword=intg["keywords"][0],
            target_keywords=intg["keywords"],
            internal_links=[], author_name=author["name"], author_slug=author["slug"],
            integration_partner=intg["slug"], industry="SaaS", intent="transactional",
            topical_pillar="integrations",
            breadcrumbs=[("Home", self.ce.site_url), ("Integrations", f"{self.ce.site_url}/integrations"), (f"Pipeleap + {name}", page_url)],
        )

    @staticmethod
    def _faq_pairs(name: str) -> list[tuple[str, str]]:
        return [
            (f"Does Pipeleap integrate natively with {name}?", f"Yes. Pipeleap's workflow engine connects to {name} as a governed workflow step — enabling automatic data flow, signal-triggered actions, and CRM write-back without manual configuration per campaign."),
            (f"Does this replace {name} or work alongside it?", f"Pipeleap orchestrates {name} — it governs when and how {name} executes within the broader outbound workflow. It does not replace {name}; it makes {name} part of an automated, end-to-end execution system."),
            ("How long does setup take?", "Most Pipeleap integrations are live within a day. The workflow engine is configured around your existing stack, not against it."),
            ("Will this work with my existing CRM?", "Yes. Pipeleap is CRM-agnostic. It writes structured, enriched data back to HubSpot, Salesforce, or any CRM via its governed write-back workflow."),
        ]
