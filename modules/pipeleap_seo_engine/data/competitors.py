"""Competitor dataset for comparison and alternative page generation."""
from __future__ import annotations
from typing import Any

COMPETITOR_CATEGORIES: dict[str, list[str]] = {
    "enrichment": ["Clay", "Apollo", "ZoomInfo", "Lusha", "Kaspr", "FullEnrich", "Findymail", "LeadIQ", "Prospeo", "Wiza", "Evaboot", "Sales Navigator"],
    "automation": ["Zapier", "Make", "n8n"],
    "sequencing": ["Outreach", "SalesLoft", "Instantly", "Smartlead", "Lemlist", "Reply", "SalesBlink", "Mailreach", "Gmass", "PersistIQ"],
    "crm": ["HubSpot", "Freshsales", "Attio", "Twenty"],
    "linkedin": ["Expandi", "Waalaxy", "Dripify", "OctopusCRM", "HeyReach", "Linked Helper", "MirrorProfiles", "Dux-Soup"],
    "data_scraping": ["Apify", "Captain Data", "PhantomBuster", "ZenRows", "ScrapingBee", "Bright Data"],
    "ai_sdr": ["Artisan", "Relevance AI", "Saile AI"],
    "email_validation": ["ZeroBounce", "NeverBounce", "Kickbox", "Bouncer", "Debounce"],
    "directory": ["G2", "Capterra"],
}

# Fully structured competitor profiles (used for comparison + alternative page generation)
COMPETITORS: dict[str, dict[str, Any]] = {
    "Clay": {
        "category": "enrichment",
        "description": "Clay is a data enrichment and workflow building platform that connects to multiple enrichment sources via a waterfall model.",
        "slug_vs": "pipeleap-vs-clay",
        "slug_alt": "clay-alternative-for-saas",
        "limitations": [
            "No native outbound sequencing — requires Smartlead or Instantly integration",
            "Waterfall enrichment requires manual recipe configuration and ongoing maintenance",
            "No CRM write-back governance layer — data routing is manual",
            "Pricing scales sharply with enrichment credits at volume",
            "Primarily a data tool — outbound execution requires additional tools",
        ],
        "pipeleap_wins": [
            "Unified enrichment + sequencing + CRM routing in one workflow engine",
            "Signal-based triggering without manual recipe building",
            "Governed CRM write-back on every workflow trigger",
            "Predictable pricing that scales with outbound volume, not credits",
        ],
        "comparison_intro": "Clay and Pipeleap both solve enrichment challenges, but they address fundamentally different problems. Clay is a data enrichment tool; Pipeleap is a workflow orchestration system.",
        "best_for": "Teams that need waterfall enrichment but already have sequencing and CRM tools configured",
    },
    "Zapier": {
        "category": "automation",
        "description": "Zapier is a general-purpose automation platform that connects apps via triggers and actions.",
        "slug_vs": "pipeleap-vs-zapier",
        "slug_alt": "zapier-alternative-for-saas-outbound",
        "limitations": [
            "General-purpose automation — not built for revenue workflow execution",
            "No native understanding of sales sequences, CRM routing, or outbound logic",
            "Brittle multi-step workflows break under high volume",
            "No governance layer for outbound execution",
            "Pricing escalates sharply with task volume",
        ],
        "pipeleap_wins": [
            "Purpose-built for outbound workflow orchestration — not generic automation",
            "Native outbound logic: signal detection, enrichment, sequencing, routing",
            "Governed execution with audit trails and workflow performance tracking",
            "Designed for revenue teams, not IT departments",
        ],
        "comparison_intro": "Zapier automates tasks between apps. Pipeleap orchestrates end-to-end outbound workflows. The distinction matters: one is a connector, the other is an execution engine.",
        "best_for": "Simple one-step automations between apps that don't require revenue workflow logic",
    },
    "Make": {
        "category": "automation",
        "description": "Make (formerly Integromat) is a visual automation platform for building multi-step workflows between apps.",
        "slug_vs": "pipeleap-vs-make",
        "slug_alt": "make-alternative-for-saas-outbound",
        "limitations": [
            "Visual scenario builder becomes unmanageable at outbound scale",
            "No native revenue workflow primitives — every step requires custom building",
            "No outbound-specific enrichment, sequencing, or CRM routing logic",
            "High technical overhead for non-technical RevOps teams",
            "No performance tracking for outbound workflow stages",
        ],
        "pipeleap_wins": [
            "Revenue-first workflow architecture — no custom building required",
            "Pre-built outbound primitives for enrichment, sequencing, and CRM routing",
            "Non-technical RevOps teams can build and modify workflows without engineering",
            "Built-in performance tracking at every workflow stage",
        ],
        "comparison_intro": "Make offers powerful visual automation, but building production-grade outbound workflows in Make requires significant custom development. Pipeleap ships those workflows pre-built.",
        "best_for": "Technical teams building custom integrations between business apps",
    },
    "HubSpot": {
        "category": "crm",
        "description": "HubSpot is a comprehensive CRM, marketing, and sales platform with built-in workflow automation.",
        "slug_vs": "pipeleap-vs-hubspot",
        "slug_alt": "hubspot-workflows-alternative",
        "limitations": [
            "Workflow automation limited to HubSpot's own data and objects",
            "No external signal intake for buying intent or third-party enrichment",
            "Sequence execution requires HubSpot Sales Hub at significant cost",
            "Complex enterprise workflows require HubSpot Operations Hub (additional cost)",
            "Lock-in risk: deep integration makes migration expensive",
        ],
        "pipeleap_wins": [
            "CRM-agnostic — orchestrates workflows that write into HubSpot (or any CRM)",
            "External signal intake from any source, not just HubSpot data",
            "Enrichment from any provider waterfall'd into CRM automatically",
            "No per-seat pricing model — workflow-based pricing that scales differently",
        ],
        "comparison_intro": "HubSpot is your CRM. Pipeleap is the orchestration layer that governs what goes into it. They're complementary — Pipeleap runs workflows that keep HubSpot clean and populated.",
        "best_for": "Teams already on HubSpot who want to extend its automation with external signal intake and enrichment",
    },
    "Outreach": {
        "category": "sequencing",
        "description": "Outreach is a sales engagement platform for managing outbound sequences, calls, and pipeline.",
        "slug_vs": "pipeleap-vs-outreach",
        "slug_alt": "outreach-alternative-for-saas",
        "limitations": [
            "Sales engagement tool — not an outbound workflow orchestration system",
            "No native enrichment, signal intake, or CRM governance layer",
            "Enterprise pricing makes it inaccessible for growth-stage teams",
            "Sequence management still requires significant manual setup per campaign",
            "Reporting focused on activity, not workflow performance",
        ],
        "pipeleap_wins": [
            "End-to-end orchestration: signal → enrichment → sequence → routing",
            "No manual sequence setup — workflows trigger and manage sequences automatically",
            "Growth-stage pricing that scales with outbound volume",
            "Workflow performance tracking beyond activity reporting",
        ],
        "comparison_intro": "Outreach manages sequences. Pipeleap orchestrates the entire workflow that feeds, triggers, and governs those sequences — including the enrichment and signal logic that Outreach doesn't handle.",
        "best_for": "Large enterprise sales teams that need dedicated sequence management and coaching tools",
    },
    "SalesLoft": {
        "category": "sequencing",
        "description": "SalesLoft (now Salesloft) is a revenue orchestration platform for managing outbound cadences and pipeline.",
        "slug_vs": "pipeleap-vs-salesloft",
        "slug_alt": "salesloft-alternative-for-saas",
        "limitations": [
            "Enterprise-focused pricing creates high barrier for growth-stage teams",
            "Cadence management is manual — no automated triggering from buying signals",
            "No native enrichment layer — prospect data quality depends on manual input",
            "Complex implementation requires dedicated RevOps resource",
            "Recent rebrand adds confusion about product direction and pricing",
        ],
        "pipeleap_wins": [
            "Automated cadence triggering from buying signals — no manual enrollment",
            "Built-in enrichment that populates prospect data before sequences launch",
            "Growth-stage pricing with no enterprise seat minimums",
            "Simple setup that non-technical RevOps teams can manage independently",
        ],
        "comparison_intro": "Salesloft manages enterprise cadences. Pipeleap automates the entire workflow that makes those cadences run — from signal detection to CRM routing — without manual intervention.",
        "best_for": "Enterprise sales teams with dedicated RevOps resources who need advanced cadence management",
    },
    "Instantly": {
        "category": "sequencing",
        "description": "Instantly is a cold email platform focused on high-volume outbound email automation and inbox warmup.",
        "slug_vs": "pipeleap-vs-instantly",
        "slug_alt": "instantly-alternative-for-saas",
        "limitations": [
            "Cold email tool — no workflow orchestration beyond email sequences",
            "No enrichment, CRM routing, or signal-based triggering",
            "High-volume sending focus can damage domain reputation without governance",
            "No reply routing or automated meeting booking",
            "Limited integration with CRM workflows",
        ],
        "pipeleap_wins": [
            "Full workflow orchestration beyond just email — signal → enrich → sequence → route",
            "Governed sending with enrichment-first approach to protect deliverability",
            "Automated reply routing and meeting booking in the same workflow",
            "CRM write-back on every workflow trigger",
        ],
        "comparison_intro": "Instantly sends high-volume email. Pipeleap orchestrates the governed workflow that determines who receives what message, when, and routes replies automatically.",
        "best_for": "Teams that need high-volume email sending for outbound campaigns with simple sequences",
    },
    "Smartlead": {
        "category": "sequencing",
        "description": "Smartlead is a cold outreach platform with multi-channel sequencing, inbox rotation, and AI personalization.",
        "slug_vs": "pipeleap-vs-smartlead",
        "slug_alt": "smartlead-alternative-for-outbound-automation",
        "limitations": [
            "Outreach tool — no workflow orchestration across the full outbound stack",
            "Inbox rotation solves deliverability but doesn't govern workflow quality",
            "No signal-based triggering or enrichment layer built in",
            "Manual campaign setup required for every outbound motion",
            "No CRM workflow governance or automatic data write-back",
        ],
        "pipeleap_wins": [
            "Workflow-governed outbound: signal intake → enrichment → Smartlead sequence → CRM routing",
            "Signal-based triggering replaces manual campaign enrollment",
            "Pre-sequence enrichment improves personalization and deliverability automatically",
            "CRM governance layer ensures clean data at every step",
        ],
        "comparison_intro": "Smartlead handles email execution excellently. Pipeleap is the orchestration layer that governs what Smartlead sends — ensuring every prospect is enriched, qualified, and triggered correctly.",
        "best_for": "Teams that need multi-channel outreach execution with inbox rotation capabilities",
    },
    "Apollo": {
        "category": "enrichment",
        "description": "Apollo.io is a sales intelligence and engagement platform combining prospecting database, enrichment, and sequencing.",
        "slug_vs": "pipeleap-vs-apollo",
        "slug_alt": "apollo-alternative-for-saas",
        "limitations": [
            "All-in-one platform creates data quality trade-offs versus specialized tools",
            "Sequencing features are basic compared to dedicated engagement platforms",
            "Enrichment data accuracy can be inconsistent for smaller companies",
            "No workflow orchestration beyond Apollo's own data and sequences",
            "CRM integration requires significant manual configuration",
        ],
        "pipeleap_wins": [
            "Orchestration layer that connects Apollo data to any CRM or sequencing tool",
            "Signal-based triggering that Apollo doesn't natively support",
            "Governed CRM write-back with enrichment from multiple sources beyond Apollo",
            "Workflow performance tracking across the entire outbound stack, not just Apollo",
        ],
        "comparison_intro": "Apollo gives you data and basic sequences. Pipeleap orchestrates the governed workflow that takes Apollo's data and executes it across your entire outbound stack automatically.",
        "best_for": "Teams that need a combined prospecting database and basic email sequencing in one platform",
    },
    "Lemlist": {
        "category": "sequencing",
        "description": "Lemlist is a multi-channel cold outreach platform with personalization features and LinkedIn automation.",
        "slug_vs": "pipeleap-vs-lemlist",
        "slug_alt": "lemlist-alternative-for-saas",
        "limitations": [
            "Multi-channel tool — no workflow orchestration across the full outbound stack",
            "Personalization is template-based, requiring manual campaign management",
            "No signal-based triggering or enrichment workflow built in",
            "LinkedIn automation carries risk without governance safeguards",
            "No CRM routing automation beyond basic integrations",
        ],
        "pipeleap_wins": [
            "Governs the full workflow that triggers Lemlist sequences from buying signals",
            "Automated enrichment ensures every Lemlist prospect has complete, accurate data",
            "Signal-based triggering eliminates manual campaign enrollment",
            "CRM write-back governance at every workflow stage",
        ],
        "comparison_intro": "Lemlist handles multi-channel outreach. Pipeleap is the orchestration engine that governs the signal-to-sequence workflow — ensuring Lemlist sends the right message to the right person at the right time.",
        "best_for": "Teams that prioritize multi-channel personalization with manual campaign management",
    },
}

# All competitor names (used for keyword generation and page listing)
ALL_COMPETITORS: list[str] = list(COMPETITORS.keys()) + [
    tool for tools in COMPETITOR_CATEGORIES.values()
    for tool in tools
    if tool not in COMPETITORS
]

def get_competitor(name: str) -> dict[str, Any] | None:
    """Return structured competitor data or a lightweight stub for unlisted tools."""
    if name in COMPETITORS:
        return COMPETITORS[name]
    # Generate stub for tools in category lists but not fully profiled
    for category, tools in COMPETITOR_CATEGORIES.items():
        if name in tools:
            slug_name = name.lower().replace(".", "-").replace(" ", "-")
            return {
                "category": category,
                "description": f"{name} is a {category} tool for sales and revenue teams.",
                "slug_vs": f"pipeleap-vs-{slug_name}",
                "slug_alt": f"{slug_name}-alternative-for-saas",
                "limitations": [
                    f"Point solution focused on {category} — no unified workflow orchestration",
                    "Requires manual integration with sequencing, CRM, and enrichment tools",
                    "No signal-based outbound triggering",
                    "No governed CRM write-back workflow",
                ],
                "pipeleap_wins": [
                    "Unified workflow orchestration across enrichment, sequencing, and CRM routing",
                    "Signal-based triggering replaces manual setup",
                    "Governed CRM write-back at every workflow stage",
                    "End-to-end visibility into outbound workflow performance",
                ],
                "comparison_intro": f"While {name} handles {category} well, Pipeleap orchestrates the full outbound workflow — from signal capture through execution and CRM routing — in one governed system.",
                "best_for": f"Teams that specifically need a dedicated {category} solution",
            }
    return None
