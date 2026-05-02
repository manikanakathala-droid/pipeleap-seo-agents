"""Workflow recipe page generator — uncontested long-tail keyword category."""
from __future__ import annotations
from modules.pipeleap_seo_engine.data.workflows import WORKFLOW_RECIPES
from modules.pipeleap_seo_engine.data.authors import get_author_for_page_type
from modules.pipeleap_seo_engine.engines.content_engine import GrowthContentEngine
from modules.pipeleap_seo_engine.models import GrowthPage


class WorkflowRecipeGenerator:

    def __init__(self, content_engine: GrowthContentEngine) -> None:
        self.ce = content_engine

    def generate_all(self, existing_slugs: set[str]) -> list[GrowthPage]:
        pages = []
        for recipe in WORKFLOW_RECIPES:
            slug = f"workflows/{recipe['slug']}"
            if slug in existing_slugs:
                continue
            pages.append(self._generate(recipe))
            existing_slugs.add(slug)
        return pages

    def _generate(self, recipe: dict) -> GrowthPage:
        slug = f"workflows/{recipe['slug']}"
        page_url = f"{self.ce.site_url}/{slug}"
        title = f"{recipe['title']} | Pipeleap Outbound Automation"
        meta = f"Step-by-step workflow recipe: {recipe['h1']}. Automated, governed, and production-ready for SaaS revenue teams."[:158]
        author = get_author_for_page_type("workflow_recipe")

        # Build HowTo steps
        howto_steps = "\n".join([
            f"### Step {s['step']}: {s['title']}\n\n{s['body']}\n"
            for s in recipe["steps"]
        ])

        # Workflow diagram
        step_titles = " → ".join(s["title"] for s in recipe["steps"])

        body = "\n".join([
            self.ce.ai_answer_block(
                question=f"How do you {recipe['primary_keyword'].replace('workflow', '').replace('automation', '').strip()}?",
                answer=f"Use Pipeleap's workflow engine to automate {recipe['primary_keyword']}. The workflow triggers on {recipe['trigger'].lower()}, then enriches, sequences, and routes the prospect automatically — no manual work required.",
            ),
            f"# {recipe['h1']}",
            "",
            f"*By [{author['name']}]({self.ce.site_url}/team/{author['slug']}), {author['title']}*",
            "",
            "## The Problem This Workflow Solves",
            "",
            f"Most SaaS teams deal with **{recipe['pain']}**. This creates a consistent bottleneck: "
            f"high-intent signals get missed, follow-up is inconsistent, and pipeline suffers. "
            f"This workflow recipe eliminates every manual step between signal detection and booked meeting.",
            "",
            "## Workflow Overview",
            "",
            f"**Trigger:** {recipe['trigger']}",
            "",
            f"```text",
            step_titles,
            "```",
            "",
            "**End result:** " + recipe["outcome"],
            "",
            "## Step-by-Step Workflow",
            "",
            howto_steps,
            "## Why This Workflow Produces Better Pipeline",
            "",
            (
                f"Manual execution of this workflow produces inconsistent results because it depends on "
                f"individual rep attention, timing, and data quality. When the same workflow runs through "
                f"Pipeleap's orchestration engine, every trigger produces the same outcome: enriched, "
                f"personalized, CRM-logged outreach that fires at the right moment without manual effort."
            ),
            "",
            self.ce.before_after_section(),
            self.ce.statistics_section(),
            self.ce.faq_section([
                (f"How long does it take to set up this workflow?", "Most teams have this workflow running within 24 hours. Pipeleap's workflow engine is configured around your existing tools — no rip-and-replace required."),
                ("Does this work with my existing CRM?", "Yes. Pipeleap writes structured data to HubSpot, Salesforce, or any CRM automatically as part of the workflow execution."),
                ("Can I customize the sequence copy and timing?", "Yes. Every sequence step, timing window, and suppression rule is fully configurable within the Pipeleap workflow engine."),
                ("What signals can trigger this workflow?", "Any signal your stack can produce: website visits, intent data matches, list imports, form fills, CRM field changes, LinkedIn activity, or API events from connected tools."),
            ]),
            self.ce.positioning_callout(),
            self.ce.cta_section(
                label="Deploy this workflow in Pipeleap",
                urgency=f"Replace manual {recipe['pain']} with this automated workflow.",
                slug=slug,
                campaign="workflow_recipe",
            ),
        ])

        howto_schema = {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": recipe["h1"],
            "description": meta,
            "url": page_url,
            "step": [
                {"@type": "HowToStep", "position": s["step"], "name": s["title"], "text": s["body"]}
                for s in recipe["steps"]
            ],
        }

        schema = [
            self.ce.webpage_schema(title, meta, page_url),
            howto_schema,
            self.ce.breadcrumb_schema([
                ("Home", self.ce.site_url),
                ("Workflow Recipes", f"{self.ce.site_url}/workflows"),
                (recipe["title"], page_url),
            ]),
        ]

        return GrowthPage(
            slug=slug, page_type="workflow_recipe", title=title, seo_title=title,
            meta_description=meta, canonical_url=page_url,
            og_meta=self.ce.og_meta(title, meta, page_url),
            twitter_meta=self.ce.twitter_meta(title, meta),
            h1=recipe["h1"], body_markdown=body, schema_markup=schema,
            call_to_action=self.ce.cta_section(slug=slug, campaign="workflow_recipe"),
            primary_keyword=recipe["primary_keyword"],
            target_keywords=recipe["keywords"],
            internal_links=[], author_name=author["name"], author_slug=author["slug"],
            industry="SaaS", intent="informational", topical_pillar="workflow-orchestration",
            breadcrumbs=[("Home", self.ce.site_url), ("Workflows", f"{self.ce.site_url}/workflows"), (recipe["title"], page_url)],
        )
