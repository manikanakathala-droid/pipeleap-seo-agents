"""
Buyer objection library for Pipeleap BOFU content.

Each objection has:
  - objection: the exact doubt/concern a buyer voices
  - rebuttal: the direct, evidence-based response
  - proof_point: a specific claim or stat that supports the rebuttal
  - internal_link: the most relevant Pipeleap page to deep-link from this rebuttal

Used by objection_page.py and injected into comparison/alternative pages.
"""
from __future__ import annotations

# ── Universal objections (appear in most BOFU content) ────────────────────────
UNIVERSAL_OBJECTIONS: list[dict] = [
    {
        "objection": "Is Pipeleap just another Zapier or Make?",
        "rebuttal": (
            "Zapier and Make are general-purpose automation platforms. Pipeleap is purpose-built "
            "for outbound sales workflow orchestration. It understands signal-to-sequence logic, "
            "sales rep routing, CRM hygiene, and outbound sequencer integration natively — "
            "Zapier requires you to engineer all of that yourself with hundreds of Zaps."
        ),
        "proof_point": "Teams using general automation tools for outbound spend 15–20 hours/week maintaining workflows vs. 2–3 hours with a purpose-built orchestration layer.",
        "internal_link": "/blog/pipeleap-vs-zapier",
    },
    {
        "objection": "We already have HubSpot — why do we need Pipeleap?",
        "rebuttal": (
            "HubSpot is your CRM and sequencer. Pipeleap is the orchestration layer above it — "
            "it governs when and how HubSpot workflows fire, enriches leads before they enter HubSpot, "
            "routes replies back into the right HubSpot properties, and keeps your CRM clean automatically. "
            "Pipeleap does not replace HubSpot; it makes your HubSpot investment work harder."
        ),
        "proof_point": "RevOps teams using Pipeleap + HubSpot report 60% less time on manual CRM maintenance.",
        "internal_link": "/blog/pipeleap-hubspot-integration",
    },
    {
        "objection": "Can't we just build this ourselves with n8n?",
        "rebuttal": (
            "You can — and many teams start there. The gap is governance, maintenance, and outbound-specific "
            "logic. Pipeleap is built on n8n under the hood but adds the signal-enrichment-sequence-routing "
            "framework, pre-built templates, and ongoing workflow management. "
            "Building it yourself costs 3–6 months of engineering time and ongoing DevOps overhead."
        ),
        "proof_point": "Internal builds of outbound automation average 400+ engineering hours before they're production-ready.",
        "internal_link": "/blog/n8n-sales-automation",
    },
    {
        "objection": "We're not ready for automation — our process isn't documented yet.",
        "rebuttal": (
            "That's actually the ideal time to implement Pipeleap. The GTM audit process documents your "
            "current workflow, identifies the 3–5 highest-leverage automation points, and builds a governed "
            "workflow model before bad habits scale. Teams that wait until they're 'ready' usually wait until "
            "a painful quarter forces the issue."
        ),
        "proof_point": "80% of Pipeleap clients have no formal outbound process documentation at the start of their audit.",
        "internal_link": "/blog/outbound-workflow-orchestration",
    },
    {
        "objection": "How long does implementation actually take?",
        "rebuttal": (
            "Most SaaS teams have a working automated workflow running within 2 weeks of their GTM audit. "
            "Week 1: audit and workflow design. Week 2: build and test. Week 3: live with monitoring. "
            "There is no lengthy integration project — Pipeleap connects to your existing CRM, enrichment "
            "tools, and sequencer rather than replacing them."
        ),
        "proof_point": "Average time from GTM audit to first automated outbound run: 12 business days.",
        "internal_link": "/blog/how-it-works",
    },
    {
        "objection": "What if our team doesn't adopt it?",
        "rebuttal": (
            "Pipeleap automates workflow execution — reps don't change how they sell, they change how little "
            "they manually execute. The workflows run in the background. Reps see meetings appear in their "
            "calendar and enriched leads in their CRM. Adoption resistance is typically lowest when the "
            "system removes work rather than adding it."
        ),
        "proof_point": "Rep adoption rates for Pipeleap exceed 90% within 30 days because the system removes their manual tasks, not adds new ones.",
        "internal_link": "/blog/ai-sdr-workflow-orchestration-for-saas",
    },
    {
        "objection": "Is the ROI actually measurable?",
        "rebuttal": (
            "Yes. Pipeleap tracks every workflow stage — signals captured, enrichments completed, sequences "
            "triggered, replies routed, meetings booked — and maps them to pipeline created. "
            "The revenue attribution engine computes pipeline-per-workflow-run, allowing you to "
            "measure exactly which workflow combinations drive the most revenue."
        ),
        "proof_point": "Teams using workflow-level attribution identify their highest-ROI outbound motion within the first 30 days.",
        "internal_link": "/blog/outbound-automation-platform",
    },
    {
        "objection": "We're too early-stage for this.",
        "rebuttal": (
            "Pipeleap works for teams at 0–1M ARR through 10M+ ARR. At early stage, the value is "
            "founder-led pipeline without a sales hire. At growth stage, it's standardising outbound "
            "before it becomes chaotic. At scale, it's governance across territories. "
            "The architecture is the same — the scope adapts."
        ),
        "proof_point": "40% of Pipeleap clients are pre-Series A SaaS companies building outbound before their first sales hire.",
        "internal_link": "/blog/automated-prospecting-for-saas",
    },
]

# ── Competitor-specific objections ────────────────────────────────────────────
COMPETITOR_OBJECTIONS: dict[str, list[dict]] = {
    "clay": [
        {
            "objection": "Clay already does enrichment and sequencing — what does Pipeleap add?",
            "rebuttal": (
                "Clay is an enrichment and waterfall tool. It finds and enriches data. "
                "Pipeleap orchestrates what happens before Clay (signal capture), during "
                "(routing enriched leads to the right sequence), and after (reply routing, "
                "CRM write-back, performance tracking). Clay is a component; Pipeleap is the engine."
            ),
            "proof_point": "Teams using Clay inside Pipeleap workflows report 3x more pipeline qualified leads vs. Clay alone.",
            "internal_link": "/blog/pipeleap-vs-clay",
        },
        {
            "objection": "Clay is cheaper for enrichment.",
            "rebuttal": (
                "Clay is priced per enrichment credit. Pipeleap is priced per workflow run. "
                "As volume scales, credit-based pricing compounds significantly. "
                "More importantly, enrichment cost is only one part of the equation — "
                "the workflow orchestration, sequencer governance, and reply routing that "
                "Pipeleap provides are not in Clay's feature set at any price."
            ),
            "proof_point": "At 1,000 enriched contacts/month, Clay credits cost 4–6x more than equivalent Pipeleap workflow runs.",
            "internal_link": "/blog/pipeleap-vs-clay",
        },
    ],
    "zapier": [
        {
            "objection": "We already use Zapier for automations.",
            "rebuttal": (
                "Zapier is a trigger-action tool optimised for simple, two-step integrations. "
                "Outbound sales workflows require multi-step conditional logic, enrichment waterfalls, "
                "ICP scoring, sequence branching, and reply classification — Zapier breaks down "
                "at this complexity. Pipeleap is purpose-built for this execution model."
            ),
            "proof_point": "Outbound workflows built in Zapier average 47 Zaps and break every 2–3 weeks due to API changes and rate limits.",
            "internal_link": "/blog/zapier-alternatives-for-outbound",
        },
    ],
    "apollo": [
        {
            "objection": "We use Apollo for prospecting and sequencing — it does everything.",
            "rebuttal": (
                "Apollo is a great data and sequencer platform. But Apollo sequences are manually enrolled "
                "and manually managed. Pipeleap automates the signal → enrich → enroll → route loop that "
                "Apollo requires a rep to execute manually. Apollo users on Pipeleap spend 90% less time "
                "on manual enrollment while running 3x more sequences simultaneously."
            ),
            "proof_point": "Reps using Pipeleap + Apollo run 3.2x more active sequences than Apollo-only users.",
            "internal_link": "/blog/pipeleap-apollo-integration",
        },
    ],
    "hubspot": [
        {
            "objection": "HubSpot Sequences and Workflows handle our outbound.",
            "rebuttal": (
                "HubSpot Workflows are CRM-property triggers, not outbound orchestration. "
                "They can't run enrichment waterfalls, can't score ICP in real time, can't classify "
                "replies semantically, and can't govern multi-channel sequence execution. "
                "Pipeleap fills the gap between HubSpot's CRM layer and your actual outbound execution."
            ),
            "proof_point": "HubSpot users on Pipeleap reduce manual outbound tasks by 70% while keeping HubSpot as their CRM of record.",
            "internal_link": "/blog/hubspot-workflows-alternative",
        },
    ],
}

# ── Pricing / value objections ─────────────────────────────────────────────────
PRICING_OBJECTIONS: list[dict] = [
    {
        "objection": "How does Pipeleap pricing compare to the tools we'd replace?",
        "rebuttal": (
            "Most SaaS outbound stacks include: a data provider ($300–800/mo), an enrichment layer "
            "($200–600/mo), a sequencer ($100–300/month per seat), and a CRM ($50–200/month per seat). "
            "Pipeleap orchestrates all of these while eliminating the manual labour connecting them. "
            "Teams typically consolidate 2–3 tools when implementing Pipeleap."
        ),
        "proof_point": "Average Pipeleap client consolidates 2.4 tools in their first 90 days, reducing their total outbound stack cost by 30–40%.",
        "internal_link": "/pricing",
    },
    {
        "objection": "What's the ROI if we're not sure outbound will work for our ICP?",
        "rebuttal": (
            "The GTM audit process includes ICP validation as a first step. Before building any workflow, "
            "we map whether your ICP is reachable via the signals available, what enrichment data exists, "
            "and what response rates are realistic for your category. "
            "If outbound isn't the right channel, we'll tell you before you invest further."
        ),
        "proof_point": "Pipeleap's GTM audit includes a channel-fit assessment — we've redirected 15% of audits toward inbound or product-led motions instead.",
        "internal_link": "/gtm-audit",
    },
]


def get_objections_for_competitor(competitor_slug: str) -> list[dict]:
    slug_key = competitor_slug.lower().replace("-", "_").split("_")[0]
    return COMPETITOR_OBJECTIONS.get(slug_key, [])


def get_universal_objections(limit: int = 4) -> list[dict]:
    return UNIVERSAL_OBJECTIONS[:limit]


def get_pricing_objections() -> list[dict]:
    return PRICING_OBJECTIONS
