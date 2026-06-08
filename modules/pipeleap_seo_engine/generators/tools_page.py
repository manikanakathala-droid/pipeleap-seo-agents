"""Tools page generator — overview/review pages, one per tool, no Pipeleap mentions."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modules.pipeleap_seo_engine.data.authors import get_author_for_page_type
from modules.pipeleap_seo_engine.engines.content_engine import GrowthContentEngine
from modules.pipeleap_seo_engine.models import GrowthPage

DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "tool_database.json"


def _load_tool_database() -> list[dict]:
    try:
        db = json.loads(DATABASE_PATH.read_text(encoding="utf-8"))
        return db.get("tools", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "ai-sdr-tools": "AI-powered sales development representative tool",
    "cold-email-tools": "cold email outreach platform",
    "sales-engagement-tools": "sales engagement platform",
    "prospecting-tools": "B2B prospecting and contact database tool",
    "lead-enrichment-tools": "lead enrichment and data append tool",
    "crm-tools": "customer relationship management platform",
    "call-recording-tools": "call recording and conversation intelligence tool",
    "revenue-intelligence-tools": "revenue intelligence platform",
    "linkedin-automation-tools": "LinkedIn automation tool",
    "ai-outbound-agents": "AI outbound agent platform",
    "workflow-automation-tools": "workflow automation platform",
    "sales-analytics-tools": "sales analytics and business intelligence tool",
    "gtm-engineering-tools": "GTM engineering and data infrastructure tool",
}

CATEGORY_PAINS: dict[str, str] = {
    "ai-sdr-tools": "manually researching and writing personalised outreach at scale",
    "cold-email-tools": "managing deliverability and inbox reputation across cold email campaigns",
    "sales-engagement-tools": "orchestrating multi-channel sequences while keeping CRM data in sync",
    "prospecting-tools": "finding accurate contact data and building targeted prospect lists",
    "lead-enrichment-tools": "keeping CRM contact data accurate and up to date",
    "crm-tools": "choosing a CRM that scales with your sales process",
    "call-recording-tools": "capturing and analysing sales calls for coaching and deal intelligence",
    "revenue-intelligence-tools": "consolidating sales signals for accurate pipeline forecasting",
    "linkedin-automation-tools": "scaling LinkedIn outreach while staying within platform limits",
    "ai-outbound-agents": "designing and executing outbound sequences without manual rep effort",
    "workflow-automation-tools": "connecting sales tools into automated, reliable workflows",
    "sales-analytics-tools": "building accurate pipeline reports from raw CRM data",
    "gtm-engineering-tools": "building signal-based go-to-market motions with data infrastructure",
}

CATEGORY_FEATURES: dict[str, list[str]] = {
    "ai-sdr-tools": ["AI-powered prospect research and personalisation", "Automated multi-channel outreach", "CRM integration and activity logging", "Reply and meeting detection", "Campaign analytics"],
    "cold-email-tools": ["Multi-channel email sequences", "Inbox warm-up and rotation", "Deliverability monitoring", "A/B testing and analytics", "CRM integration"],
    "sales-engagement-tools": ["Multi-channel sequence builder", "CRM bi-directional sync", "Call logging and task management", "Team performance analytics", "AI-powered email writing"],
    "prospecting-tools": ["B2B contact database with advanced filters", "Email verification and enrichment", "Intent data and buying signals", "CRM integration and data sync"],
    "lead-enrichment-tools": ["Multi-source data enrichment", "Email and phone finding", "CRM data append and deduplication", "Real-time enrichment via API", "Data quality scoring"],
    "crm-tools": ["Contact and account management", "Deal tracking and pipeline management", "Reporting and dashboards", "Email and calendar integration", "Workflow automation"],
    "call-recording-tools": ["Call recording and transcription", "Conversation analysis and scoring", "Deal risk detection", "Coaching and feedback tools", "CRM integration"],
    "revenue-intelligence-tools": ["Conversation intelligence and analysis", "Forecast management and accuracy", "Buyer intent signals", "Deal risk scoring", "Pipeline analytics"],
    "linkedin-automation-tools": ["Connection request automation", "Message sequence automation", "Profile visit and engagement", "CRM sync", "Campaign analytics"],
    "ai-outbound-agents": ["Autonomous prospect research", "AI-generated personalised messaging", "Multi-channel sequence execution", "Reply handling and routing", "CRM write-back"],
    "workflow-automation-tools": ["Visual workflow builder", "API and webhook connectors", "Conditional logic and branching", "Error handling and monitoring", "CRM integration"],
    "sales-analytics-tools": ["Pipeline and forecast reporting", "Rep performance analytics", "Custom dashboard builder", "CRM data integration", "Revenue forecasting models"],
    "gtm-engineering-tools": ["Data pipeline and ETL infrastructure", "Signal-based lead scoring", "Reverse ETL and data activation", "Web de-anonymisation and identification", "CRM and sales tool integration"],
}

CATEGORY_PRO_TEMPLATES: dict[str, list[str]] = {
    "ai-sdr-tools": ["Reduces manual prospect research time significantly", "Scales personalised outreach without headcount growth", "Integrates well with existing sales engagement platforms"],
    "cold-email-tools": ["Strong deliverability infrastructure and inbox management", "Scales cold outreach without damaging domain reputation", "Includes warm-up and rotation features"],
    "sales-engagement-tools": ["Centralises multi-channel outreach in a single platform", "Strong CRM sync and data consistency", "Provides clear rep activity analytics"],
    "prospecting-tools": ["Large contact database with broad coverage", "Advanced search filters for precise targeting", "Saves significant manual research time"],
    "lead-enrichment-tools": ["Automates data enrichment at scale", "Improves CRM data quality", "Reduces manual research overhead"],
    "crm-tools": ["Central system of record for all revenue activity", "Configurable to match any sales process", "Essential for pipeline reporting and forecasting"],
    "call-recording-tools": ["Captures call data automatically without rep effort", "Surfaces deal risks that would otherwise go unnoticed", "Provides coaching opportunities from real calls"],
    "revenue-intelligence-tools": ["Improves forecast accuracy significantly", "Consolidates signals from multiple data sources", "Surfaces pipeline risks before they hit forecasts"],
    "linkedin-automation-tools": ["Scales LinkedIn outreach beyond manual capacity", "Multi-channel sequences improve reply rates", "Saves hours of manual profile work daily"],
    "ai-outbound-agents": ["Reduces manual sequence design and execution work", "Scales outbound without proportional headcount growth", "Operates 24/7 without rep fatigue"],
    "workflow-automation-tools": ["Eliminates manual data transfer between tools", "Reduces error-prone manual processes", "Frees up ops teams for higher-value work"],
    "sales-analytics-tools": ["Turns raw CRM data into actionable reporting", "Reveals pipeline trends and bottlenecks", "Provides single source of truth for revenue reporting"],
    "gtm-engineering-tools": ["Bridges data infrastructure gaps in the sales stack", "Enables signal-based, automated GTM motions", "Reduces dependency on manual data work"],
}

CATEGORY_CON_TEMPLATES: dict[str, list[str]] = {
    "ai-sdr-tools": ["AI output quality varies significantly by ICP", "Requires clean CRM data to work effectively", "Cannot handle complex multi-stakeholder deals"],
    "cold-email-tools": ["Deliverability depends on domain reputation more than the tool", "Per-seat pricing adds up at scale", "Most tools lack native LinkedIn or phone outreach"],
    "sales-engagement-tools": ["Enterprise pricing can be expensive for larger teams", "CRM integration quality varies between platforms", "Requires consistent rep adoption to generate reliable data"],
    "prospecting-tools": ["Data accuracy varies by region and industry", "Enterprise pricing can be prohibitive for smaller teams", "Mobile number coverage is inconsistent"],
    "lead-enrichment-tools": ["Data freshness varies between providers", "Enrichment costs scale with contact volume", "Match rates drop for international or niche contacts"],
    "crm-tools": ["Implementation and migration require significant effort", "Admin overhead grows with team size", "Customisation flexibility comes at a cost"],
    "call-recording-tools": ["Enterprise pricing is expensive for small teams", "AI analysis quality varies between platforms", "Requires rep buy-in for consistent call logging"],
    "revenue-intelligence-tools": ["Requires clean, consistent CRM data to be accurate", "Multiple tools in this category create conflicting signals", "Enterprise contracts are expensive and multi-year"],
    "linkedin-automation-tools": ["LinkedIn actively restricts automated activity", "Account bans are a real risk at higher volumes", "Cloud-based tools carry higher ban risk than browser-based"],
    "ai-outbound-agents": ["Output quality is inconsistent without careful monitoring", "Brand risk requires human oversight before sending", "Enterprise multi-stakeholder deals still need human strategy"],
    "workflow-automation-tools": ["Complex workflows can be difficult to debug when they break", "Maintaining integrations as APIs change requires ongoing effort", "Sales-specific logic must be custom-built in general-purpose tools"],
    "sales-analytics-tools": ["Reports are only as good as the CRM data feeding them", "Dedicated BI tools require data engineering investment", "Multiple analytics tools can create conflicting narratives"],
    "gtm-engineering-tools": ["Requires technical skills beyond typical sales ops capacity", "Tooling complexity increases with the number of data sources", "Signal quality depends on data volume and accuracy"],
}


def _build_template_content(tool: dict) -> dict:
    """Generate overview/review content from tool metadata using templates."""
    name = tool.get("name", "")
    cat_slug = tool.get("categorySlug", "")
    cat_desc = CATEGORY_DESCRIPTIONS.get(cat_slug, "B2B sales tool")
    pain = CATEGORY_PAINS.get(cat_slug, "managing B2B sales workflows")
    website = tool.get("website", "")
    pricing = {
        "model": tool.get("pricing_model", "Contact"),
        "startingAt": tool.get("starting_price", ""),
        "hasFree": bool(tool.get("has_free_tier", False)),
    }
    if not pricing["startingAt"]:
        del pricing["startingAt"]

    description = tool.get("description") or f"{name} is a {cat_desc} that helps sales teams with {pain}."

    tagline = f"{name} - {cat_desc} for B2B sales teams"

    long_description = (
        f"{name} is a {cat_desc} designed to help revenue teams with {pain}. "
        f"It provides tools and features that reduce manual effort and improve sales workflow efficiency. "
        f"Sales operations leaders evaluate {name} based on its integration quality, feature depth, "
        f"and how well it fits into the existing technology stack."
    )

    features = CATEGORY_FEATURES.get(cat_slug, ["Core platform features", "Sales workflow automation", "CRM integration", "Analytics and reporting", "Team collaboration tools"])

    pros = CATEGORY_PRO_TEMPLATES.get(cat_slug, [f"Purpose-built for {cat_desc} functionality", "Integrates with existing sales stacks", "Reduces manual effort in the workflow"])
    cons = CATEGORY_CON_TEMPLATES.get(cat_slug, ["Requires consistent data quality to function reliably", "Integration quality varies between platforms", "May need complementary tools for full coverage"])

    use_cases = [
        f"Streamlining {pain}",
        f"Integrating {name} into the existing sales technology stack",
        f"Improving team efficiency and reducing manual data work",
        f"Building scalable, repeatable sales workflows",
    ]

    best_for = [
        f"B2B sales operations teams managing {cat_desc} workflows",
        f"Revenue teams looking to reduce manual effort in their sales process",
        f"SaaS companies standardising their {cat_desc} approach",
        f"Sales leaders evaluating {cat_desc} for their team",
    ]

    faqs = [
        {"q": f"What is {name}?", "a": f"{name} is a {cat_desc} that helps B2B sales teams with {pain}. It provides features designed to improve efficiency and reduce manual work in the sales process."},
        {"q": f"How does {name} fit into the sales stack?", "a": f"{name} integrates with existing CRM, engagement, and data tools as a {cat_desc}. Most teams use it alongside their current CRM and sales engagement platforms."},
        {"q": f"What should teams consider before choosing {name}?", "a": f"Teams should evaluate {name} based on their specific needs around {pain}, the quality of its integrations with their existing stack, and whether its feature set matches the team's scale and workflow complexity."},
    ]

    return {
        "tagline": tagline,
        "description": description,
        "longDescription": long_description,
        "website": website,
        "pricing": pricing,
        "bestFor": best_for,
        "features": features,
        "pros": pros,
        "cons": cons,
        "useCases": use_cases,
        "pipeLeapContext": "",
        "faqs": faqs,
    }


def _build_body_markdown(name: str, cat_slug: str, content: dict, slug: str) -> str:
    """Build a plain-text overview body."""
    cat_name = CATEGORY_DESCRIPTIONS.get(cat_slug, "B2B sales tool")
    lines = [
        f"# {name} Overview",
        "",
        content["longDescription"],
        "",
        f"## Key Features",
        "",
    ]
    for f in content["features"]:
        lines.append(f"- {f}")
    lines.append("")
    lines.append("## Pros")
    lines.append("")
    for p in content["pros"]:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("## Cons")
    lines.append("")
    for c in content["cons"]:
        lines.append(f"- {c}")
    lines.append("")
    lines.append("## Best For")
    lines.append("")
    for b in content["bestFor"]:
        lines.append(f"- {b}")
    lines.append("")
    lines.append("## Use Cases")
    lines.append("")
    for u in content["useCases"]:
        lines.append(f"- {u}")
    lines.append("")
    lines.append("## Frequently Asked Questions")
    lines.append("")
    for faq in content["faqs"]:
        lines.append(f"**{faq['q']}**")
        lines.append("")
        lines.append(f"{faq['a']}")
        lines.append("")
    lines.append("---")
    lines.append(f"*Visit the official {name} website at [{content['website']}]({content['website']}) for current pricing and feature details.*")
    return "\n".join(lines)


class ToolsPageGenerator:

    def __init__(self, content_engine: GrowthContentEngine) -> None:
        self.ce = content_engine

    def generate_all(self, existing_slugs: set[str], batch_size: int = 20) -> list[GrowthPage]:
        all_tools = _load_tool_database()
        if not all_tools:
            return []

        pages = []
        for tool in all_tools:
            tool_slug = tool.get("slug", "")
            slug = f"tools/{tool_slug}"
            if slug in existing_slugs:
                continue
            if len(pages) >= batch_size:
                break
            pages.append(self._generate(tool))
            existing_slugs.add(slug)

        return pages

    def generate_for_tools(self, tool_slugs: list[str], existing_slugs: set[str]) -> list[GrowthPage]:
        """Generate pages for specific tool slugs (for retry/single-run scenarios)."""
        all_tools = _load_tool_database()
        tool_index = {t.get("slug", ""): t for t in all_tools}
        pages = []
        for slug in tool_slugs:
            tool = tool_index.get(slug)
            if not tool:
                continue
            page_slug = f"tools/{slug}"
            if page_slug in existing_slugs:
                continue
            pages.append(self._generate(tool))
            existing_slugs.add(page_slug)
        return pages

    def _generate(self, tool: dict) -> GrowthPage:
        name = tool.get("name", "")
        tool_slug = tool.get("slug", "")
        cat_slug = tool.get("categorySlug", "")
        slug = f"tools/{tool_slug}"
        page_url = f"{self.ce.site_url}/{slug}"
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        content = _build_template_content(tool)

        title = f"{name} Review - Features, Pricing, and Use Cases"
        seo_title = f"{name} Review | Features, Pricing, Pros & Cons ({today})"
        meta = content["description"][:158]

        body = _build_body_markdown(name, cat_slug, content, tool_slug)

        schema = [
            self.ce.webpage_schema(seo_title, meta, page_url),
            self.ce.breadcrumb_schema([
                ("Home", self.ce.site_url),
                ("Tools", f"{self.ce.site_url}/tools"),
                (f"{name} Review", page_url),
            ]),
        ]
        # Add FAQ schema if faqs present
        if content["faqs"]:
            schema.append({
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q["q"],
                        "acceptedAnswer": {"@type": "Answer", "text": q["a"]},
                    }
                    for q in content["faqs"]
                ],
            })

        author = get_author_for_page_type("tools_page")

        page = GrowthPage(
            slug=slug,
            page_type="tools_page",
            title=title,
            seo_title=seo_title,
            meta_description=meta,
            canonical_url=page_url,
            og_meta=self.ce.og_meta(seo_title, meta, page_url),
            twitter_meta=self.ce.twitter_meta(seo_title, meta),
            h1=f"{name} Review",
            body_markdown=body,
            schema_markup=schema,
            call_to_action="",
            primary_keyword=f"{name.lower()} review",
            target_keywords=[
                f"{name.lower()} features",
                f"{name.lower()} pricing",
                f"{name.lower()} pros and cons",
                f"what is {name.lower()}",
                f"{name.lower()} for sales",
            ],
            internal_links=[],
            author_name=author.get("name", ""),
            author_slug=author.get("slug", ""),
            industry="SaaS",
            intent="informational",
            publish_date=today,
            breadcrumbs=[
                ("Home", self.ce.site_url),
                ("Tools", f"{self.ce.site_url}/tools"),
                (f"{name} Review", page_url),
            ],
        )

        # Set dynamic attributes for _tool_entry() in github_publisher.py
        page.category_slug = cat_slug
        page.website_url = content["website"]
        page.pricing = content["pricing"]
        page.best_for = content["bestFor"]
        page.features = content["features"]
        page.pros = content["pros"]
        page.cons = content["cons"]
        page.use_cases = content["useCases"]
        page.pipeleap_context = ""
        page.faqs = content["faqs"]
        page.date_published = today
        page.name = name

        return page
