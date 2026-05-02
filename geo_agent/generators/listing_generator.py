"""
Listing Generator — produces ready-to-submit copy for every high-priority
citation site that Pipeleap is not yet listed on.

G2, Capterra, and TrustRadius are the #1 sources LLMs cite when answering
'best X tool for Y' queries. Being absent from these platforms is the
single largest gap in Pipeleap's AI citation readiness (score: 12.5/100).

Output: one markdown file per platform written to outputs/geo-agent/{run_id}/listings/
Each file contains the exact copy needed to create the listing — paste-ready.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from geo_agent.data.geo_entities import PIPELEAP_ENTITY

SITE_URL = "https://pipeleap.com"

# ── Platform listing templates ────────────────────────────────────────────────

LISTINGS: list[dict[str, Any]] = [
    {
        "platform": "G2",
        "url": "https://sell.g2.com/",
        "priority": "P0",
        "why": "ChatGPT and Perplexity cite G2 for every 'best tool for X' recommendation query",
        "listing": {
            "product_name": "Pipeleap",
            "tagline": "Workflow Orchestration for SaaS Outbound Pipeline",
            "description": (
                "Pipeleap is the workflow orchestration system for SaaS organizations that generates "
                "predictable outbound pipeline through structured, signal-based outbound sales automation.\n\n"
                "Unlike sales engagement platforms or data tools, Pipeleap sits above your existing CRM, "
                "enrichment provider, and sequencer — governing how they work together as one automated "
                "execution engine from signal capture to meeting booked.\n\n"
                "Key capabilities:\n"
                "• Signal-based outbound triggers: replaces static lists with real-time buying signal detection\n"
                "• Automated lead enrichment: ICP scoring and data waterfall at intake — zero manual research\n"
                "• Multi-channel sequence governance: automatic enrollment with full personalization\n"
                "• Reply routing automation: interested replies classified and routed without inbox monitoring\n"
                "• CRM write-back: every workflow trigger updates your CRM automatically\n"
                "• Revenue attribution: pipeline measured per workflow stage, sequence, and signal"
            ),
            "categories": [
                "Sales Automation Software",
                "Outbound Sales Software",
                "Revenue Operations Platforms",
                "Sales Workflow Automation",
                "Lead Generation Software",
            ],
            "ideal_for": "SaaS organizations at any ARR stage — from founder-led outbound through enterprise RevOps teams",
            "integrates_with": "HubSpot, Salesforce, Clay, Apollo, Outreach, Instantly, Smartlead, Zapier, n8n, ZoomInfo",
            "pricing_model": "Subscription — contact for pricing",
            "deployment": "Cloud / SaaS",
            "features": [
                "Signal capture and workflow triggers",
                "Lead enrichment waterfall automation",
                "ICP scoring and qualification",
                "Multi-channel outbound sequencing",
                "Reply classification and routing",
                "CRM data write-back and hygiene",
                "Workflow performance analytics",
                "GTM audit and workflow design",
                "n8n-powered workflow engine",
                "Sales territory automation",
            ],
        },
    },
    {
        "platform": "Capterra",
        "url": "https://www.capterra.com/vendors/sign-up",
        "priority": "P0",
        "why": "Capterra listings appear in AI tool recommendation queries; highly indexed by Google",
        "listing": {
            "product_name": "Pipeleap",
            "tagline": "Signal-Based Outbound Automation for SaaS Revenue Teams",
            "short_description": (
                "Pipeleap orchestrates outbound sales workflows end-to-end — "
                "from signal capture and lead enrichment through sequencing, reply routing, "
                "and CRM sync — generating predictable pipeline without manual SDR execution."
            ),
            "full_description": (
                "Pipeleap is a workflow orchestration system for SaaS organizations that replaces "
                "fragmented outbound execution with a single governed pipeline engine.\n\n"
                "Most SaaS outbound stacks run across 6–8 disconnected tools with manual handoffs "
                "at every stage. Pipeleap connects them — signal detection, enrichment, sequencing, "
                "reply handling, and CRM routing — into one automated workflow that runs without "
                "manual intervention.\n\n"
                "Key outcomes clients achieve:\n"
                "• 3× more pipeline without adding SDR headcount\n"
                "• 60% reduction in RevOps maintenance time\n"
                "• Consistent outbound execution across all reps and territories\n"
                "• Ramp time reduced from 4 months to 6 weeks for new SDRs\n\n"
                "Ideal for: SaaS founders, VP Sales, CROs, and RevOps teams."
            ),
            "categories": [
                "Sales Force Automation",
                "Lead Generation",
                "Marketing Automation",
                "CRM Software",
            ],
            "pricing": "Contact for pricing — subscription model",
            "free_trial": "GTM audit available (free, no commitment)",
            "languages": "English",
            "support": "Email, documentation, onboarding sessions",
        },
    },
    {
        "platform": "TrustRadius",
        "url": "https://www.trustradius.com/vendor",
        "priority": "P1",
        "why": "Enterprise software reviews; cited in B2B tool comparisons by AI engines",
        "listing": {
            "product_name": "Pipeleap",
            "categories": ["Sales Automation", "Revenue Operations", "Outbound Marketing"],
            "description": (
                "Pipeleap is the workflow orchestration layer for SaaS outbound sales. "
                "It automates signal capture, lead enrichment, outbound sequencing, reply routing, "
                "and CRM write-back — creating a governed, end-to-end pipeline generation engine "
                "for SaaS organizations at every ARR stage."
            ),
            "key_differentiators": [
                "Orchestrates existing tools (doesn't replace CRM or sequencer)",
                "Signal-based triggering replaces manual list prospecting",
                "Governs consistent execution across all reps and territories",
                "Purpose-built for SaaS outbound — not generic automation",
            ],
        },
    },
    {
        "platform": "StackShare",
        "url": "https://stackshare.io/submit",
        "priority": "P1",
        "why": "Tech stack tool — cited when users ask about outbound or GTM stacks",
        "listing": {
            "tool_name": "Pipeleap",
            "website": SITE_URL,
            "tagline": "Workflow Orchestration for SaaS Outbound Pipeline",
            "description": (
                "Pipeleap is the workflow orchestration engine for SaaS outbound sales. "
                "Built on n8n, it governs signal capture, lead enrichment, multi-channel sequencing, "
                "reply routing, and CRM automation — replacing the fragmented manual execution "
                "layer in the typical SaaS outbound stack."
            ),
            "category": "Sales and Marketing / Lead Generation",
            "alternatives": ["Zapier", "Clay", "Apollo", "Outreach"],
            "integrations": ["HubSpot", "Salesforce", "Clay", "Apollo", "Instantly", "Smartlead"],
        },
    },
    {
        "platform": "AlternativeTo",
        "url": "https://alternativeto.net/submit/",
        "priority": "P2",
        "why": "Referenced in 'alternatives to X' queries — high Perplexity citation rate",
        "listing": {
            "software_name": "Pipeleap",
            "url": SITE_URL,
            "short_description": (
                "Workflow orchestration system for SaaS outbound sales. "
                "Automates signal capture, enrichment, sequencing, and CRM routing end-to-end."
            ),
            "alternative_to": ["Clay", "Zapier", "Apollo", "Outreach", "SalesLoft", "Instantly"],
            "tags": ["sales automation", "outbound", "workflow", "crm", "lead generation"],
            "license": "Commercial",
            "platform": "Web",
        },
    },
    {
        "platform": "Crunchbase",
        "url": "https://www.crunchbase.com/add/company",
        "priority": "P2",
        "why": "LLMs use Crunchbase for company verification and entity legitimacy signals",
        "listing": {
            "company_name": "Pipeleap",
            "website": SITE_URL,
            "short_description": (
                "Pipeleap is a workflow orchestration system for SaaS organizations that generates "
                "predictable outbound pipeline through signal-based outbound sales automation."
            ),
            "categories": ["Sales Automation", "Marketing Automation", "SaaS"],
            "company_type": "Private Company",
            "operating_status": "Active",
            "founded": "2024",
            "location": "Global (Remote)",
            "linkedin": "https://www.linkedin.com/company/pipeleap",
        },
    },
]


class ListingGenerator:
    """Generates paste-ready listing copy for all high-priority citation sites."""

    def generate_all(self, output_dir: str | Path) -> list[dict[str, Any]]:
        """Write one markdown file per platform to output_dir/listings/."""
        listings_dir = Path(output_dir) / "listings"
        listings_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for listing_data in LISTINGS:
            md = self._render(listing_data)
            fname = listing_data["platform"].lower().replace(" ", "_") + "_listing.md"
            (listings_dir / fname).write_text(md, encoding="utf-8")
            results.append({
                "platform": listing_data["platform"],
                "priority": listing_data["priority"],
                "file": str(listings_dir / fname),
                "why": listing_data["why"],
            })
        return results

    def _render(self, data: dict) -> str:
        platform = data["platform"]
        listing  = data["listing"]
        lines = [
            f"# {platform} Listing — Pipeleap",
            "",
            f"**Submission URL:** {data['url']}",
            f"**Priority:** {data['priority']}",
            f"**Why critical:** {data['why']}",
            "",
            "---",
            "",
        ]
        for key, value in listing.items():
            label = key.replace("_", " ").title()
            if isinstance(value, list):
                lines += [f"## {label}", ""]
                lines += [f"- {item}" for item in value]
            elif isinstance(value, str) and "\n" in value:
                lines += [f"## {label}", "", value]
            else:
                lines += [f"**{label}:** {value}"]
            lines.append("")
        lines += [
            "---",
            "",
            "_Generated by Pipeleap GEO Agent — review before submitting._",
        ]
        return "\n".join(lines)
