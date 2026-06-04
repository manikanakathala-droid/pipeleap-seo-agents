"""Core pain point library and Pipeleap positioning rules."""
from __future__ import annotations

# Pipeleap is / is-not enforcement — inject into all generated content
POSITIONING = {
    "is": "the operational layer that eliminates non-selling work so revenue teams can focus on selling",
    "is_not": ["a CRM", "a sales engagement tool", "a reporting or dashboard tool", "an outbound tool", "a sales automation platform", "an email sender", "a sequencer"],
    "does": [
        "eliminates manual data work that consumes 60-80% of rep time",
        "connects CRM, enrichment, and sequencing into one governed layer",
        "removes manual execution dependency",
        "creates repeatable pipeline systems",
    ],
    "tagline": "Eliminate non-selling work. Focus on selling.",
}

CORE_PAIN_POINTS: list[str] = [
    "unpredictable pipeline generation quarter over quarter",
    "heavy reliance on manual outbound and SDR execution",
    "fragmented tools with no unified workflow execution layer",
    "lack of workflow orchestration across outbound motions",
    "inconsistent execution across sales teams and territories",
    "poor visibility into outbound workflow performance",
    "inability to scale outbound without proportional headcount growth",
    "stagnant conversion rates due to lack of personalization at scale",
    "high SDR turnover from burnout on repetitive manual tasks",
    "dirty CRM data from inconsistent manual entry and logging",
    "delayed follow-ups on high-intent inbound signals",
    "missing the window of opportunity on prospect job changes",
    "over-reliance on top-performing reps rather than repeatable systems",
    "inefficient lead routing resulting in lost meeting opportunities",
]

HOW_IT_WORKS: list[dict] = [
    {
        "step": 1,
        "title": "Intelligent Signal Capture",
        "body": "Pipeleap monitors real-time buying signals — website visits, intent data, and job changes — routing them into the engine automatically.",
        "variants": [
            "We capture high-intent signals across your entire stack, ensuring no prospect intent goes unnoticed.",
            "Our engine monitors 50+ signal sources to identify accounts in an active buying window.",
        ]
    },
    {
        "step": 2,
        "title": "Automated Enrichment & Qualification",
        "body": "Each signal is automatically qualified and enriched with company, role, and intent data — zero manual research.",
        "variants": [
            "Pipeleap waterfalls through multiple data providers to ensure 98% contact accuracy before any outreach.",
            "We verify every lead against your Ideal Customer Profile (ICP) automatically using real-time technographic data.",
        ]
    },
    {
        "step": 3,
        "title": "Governed Sequence Execution",
        "body": "The workflow engine triggers role-specific, personalized outreach sequences automatically across channels.",
        "variants": [
            "Outreach is triggered based on the specific signal detected, ensuring maximum relevance and reply rates.",
            "Our multi-channel sequences coordinate email, LinkedIn, and phone tasks into one unified flow.",
        ]
    },
    {
        "step": 4,
        "title": "Smart Reply Routing",
        "body": "Interested responses are automatically routed to the right rep or booked directly into calendar — no manual intervention.",
        "variants": [
            "We classify every reply using AI to prioritize interested prospects and filter out noise.",
            "Meetings are booked directly on the correct rep's calendar based on territory or round-robin rules.",
        ]
    },
    {
        "step": 5,
        "title": "Performance Feedback Loop",
        "body": "Pipeleap tracks every workflow stage and feeds learnings back into the system to improve conversion over time.",
        "variants": [
            "The system identifies which signals produce the highest ROI and doubles down on winning workflows.",
            "We provide full visibility into the 'black box' of outbound execution, allowing for continuous optimization.",
        ]
    },
]

BEFORE_AFTER: list[tuple[str, str, str]] = [
    ("Lead sourcing", "Reps manually build lists in spreadsheets and LinkedIn", "Automated enrichment from signals at intake"),
    ("Qualification", "Manual research per prospect — hours per day", "Auto-qualified by workflow engine in real time"),
    ("Outreach", "Reps write and send emails one by one", "Personalized sequences triggered automatically"),
    ("Follow-ups", "Manual tracking via sticky notes and reminders", "Automated cadences with zero missed steps"),
    ("CRM updates", "Manual logging after every call or email", "Real-time write-back on every workflow trigger"),
    ("Reply handling", "Reps sort inbox and route manually", "Auto-classified and routed to the right rep"),
    ("Reporting", "Stitching together 5+ dashboards manually", "Unified workflow visibility in real time"),
    ("Scalability", "More pipeline = more SDR headcount", "Scales without proportional headcount increase"),
    ("Data Accuracy", "Outdated lists and high bounce rates", "Real-time verification at the moment of outreach"),
    ("Speed to Lead", "Hours or days to follow up on website signals", "Sub-2 minute response time for high-intent triggers"),
]

USE_CASE_EXAMPLES: list[dict] = [
    {
        "title": "Founder-Led Pipeline Generation",
        "description": "A 5-person SaaS startup uses Pipeleap to run outbound before hiring their first SDR — automated enrichment, sequencing, and reply routing from day one.",
        "outcome": "Pipeline on autopilot while the founder focuses on closing.",
    },
    {
        "title": "RevOps Workflow Orchestration",
        "description": "A Series B SaaS company's RevOps team uses Pipeleap to replace 6 disconnected tools with one governed execution layer — enrichment, CRM sync, and sequencing unified.",
        "outcome": "60% reduction in RevOps maintenance time.",
    },
    {
        "title": "Enterprise Outbound Governance",
        "description": "A scale-stage SaaS company uses Pipeleap to enforce consistent outbound playbooks across 4 sales territories — every rep runs the same winning workflow automatically.",
        "outcome": "Consistent pipeline generation across all markets.",
    },
    {
        "title": "Signal-Based Expansion",
        "description": "A PLG company uses Pipeleap to detect when users reach a specific usage threshold and automatically triggers an expansion sequence to the account owner.",
        "outcome": "25% increase in expansion pipeline from existing accounts.",
    },
    {
        "title": "Job Change Tracking",
        "description": "A marketing agency uses Pipeleap to monitor when past champions move to new companies, automatically triggering a 'congratulations' and intro sequence.",
        "outcome": "40% meeting booking rate on former customers.",
    },
    {
        "title": "Pricing Page Retargeting",
        "description": "A fintech SaaS uses Pipeleap to identify when anonymous accounts visit their pricing page and automatically finds the right personas to start an outbound sequence.",
        "outcome": "High-intent pipeline generated from existing web traffic.",
    },
]

