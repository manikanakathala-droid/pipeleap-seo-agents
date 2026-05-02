"""SaaS company stage definitions for segmented SEO content generation."""
from __future__ import annotations

from typing import Any

STAGES: dict[str, dict[str, Any]] = {
    "early": {
        "label": "Early-Stage SaaS",
        "arr_range": "0–1M ARR",
        "slug_suffix": "early-stage-saas",
        "description": "Pre-PMF to seed stage — founder-led sales, no dedicated SDR team, manual everything",
        "team_profile": "1–5 person go-to-market team, founder closing most deals",
        "pain_points": [
            "building pipeline without budget for a dedicated SDR team",
            "founder spending 80% of time on manual outbound instead of product and closing",
            "no repeatable outbound system to hand off when the first sales hire joins",
            "tool sprawl with no unified workflow — Sheets, Apollo, Gmail all disconnected",
            "zero visibility into which outbound motions are actually generating pipeline",
        ],
        "desired_outcomes": [
            "outbound pipeline running on autopilot before the first SDR hire",
            "repeatable playbook the founder can hand off without rebuilding from scratch",
            "automated enrichment, sequencing, and routing from day one",
            "pipeline metrics that prove what's working so you can double down",
        ],
        "budget_signal": "lean budget, high ROI sensitivity, time-to-value critical",
        "cta_angle": "Start automating outbound before you hire",
        "hero_stat": "Build a pipeline engine before you hire your first rep.",
        "featured_snippet_context": (
            "Early-stage SaaS founders typically spend 60–80% of sales time on manual outbound. "
            "Workflow automation eliminates this bottleneck by connecting enrichment, sequencing, "
            "and CRM routing into a single automated system — no SDR team required."
        ),
        "seed_keywords": [
            "outbound automation for early stage saas",
            "pipeline automation without sdr team",
            "founder-led sales automation",
            "saas startup outbound system",
            "automate outbound before hiring sdrs",
            "pre-seed saas pipeline generation",
            "outbound automation for saas startups",
            "how to build pipeline without a sales team",
            "early stage saas lead generation automation",
            "founder sales automation saas",
        ],
        "topic_cluster_modifiers": ["startup", "founder-led", "pre-sdr", "lean team", "0 to 1"],
    },
    "growth": {
        "label": "Growth-Stage SaaS",
        "arr_range": "1–10M ARR",
        "slug_suffix": "growth-stage-saas",
        "description": "Series A/B — small SDR team in place, need to scale what's working and fix execution gaps",
        "team_profile": "5–20 person sales org, 2–5 SDRs, VP Sales recently hired",
        "pain_points": [
            "inconsistent performance across the SDR team — top reps carry everyone else",
            "outbound playbooks that live in reps' heads, not in a governed system",
            "CRM hygiene breaking down as data volume grows",
            "SDRs spending 50%+ of time on manual admin instead of prospecting",
            "inability to identify which sequences and segments are driving pipeline",
        ],
        "desired_outcomes": [
            "every rep running the best-performing outbound playbook — automatically",
            "CRM data that's always clean, complete, and current without manual cleanup",
            "full visibility into which sequences, segments, and reps generate pipeline",
            "SDR productivity doubled without adding headcount",
        ],
        "budget_signal": "growth budget available, scaling ROI, team efficiency focus",
        "cta_angle": "Scale what's working. Automate what isn't.",
        "hero_stat": "Turn your top rep's playbook into every rep's default workflow.",
        "featured_snippet_context": (
            "Growth-stage SaaS companies (1–10M ARR) typically see uneven SDR performance "
            "because outbound playbooks aren't systematised. Workflow automation solves this "
            "by encoding best-performing sequences into governed, automated playbooks every rep runs automatically."
        ),
        "seed_keywords": [
            "scale saas outbound team automation",
            "sdr productivity automation saas",
            "growth stage saas pipeline automation",
            "outbound automation for growing saas",
            "saas sales team workflow automation",
            "series a saas outbound system",
            "scale sdr efficiency without hiring",
            "sales playbook automation saas",
            "consistent pipeline generation growth stage",
            "outbound workflow for saas series b",
        ],
        "topic_cluster_modifiers": ["scale", "series a", "series b", "sdr team", "growing team"],
    },
    "scale": {
        "label": "Scale-Stage / Enterprise SaaS",
        "arr_range": "10M+ ARR",
        "slug_suffix": "enterprise-saas",
        "description": "Series C+ or enterprise — large sales org, RevOps team, complex multi-territory workflows",
        "team_profile": "20+ person sales org, dedicated RevOps, multiple segments and territories",
        "pain_points": [
            "fragmented tooling across 8+ point solutions with no unified execution layer",
            "RevOps spending majority of time maintaining integrations instead of building strategy",
            "no unified visibility across outbound execution in multiple territories",
            "inability to run controlled experiments on outbound motions at scale",
            "governance gaps — reps running off-playbook with no enforcement layer",
        ],
        "desired_outcomes": [
            "single orchestration layer replacing the fragmented 8-tool stack",
            "RevOps building strategy instead of maintaining integrations",
            "full execution visibility across all territories and segments",
            "governed outbound playbooks with measurable performance at scale",
        ],
        "budget_signal": "enterprise budget, compliance and governance requirements, integration depth",
        "cta_angle": "Replace your fragmented stack with a single orchestration layer.",
        "hero_stat": "One workflow engine to govern outbound across every territory and segment.",
        "featured_snippet_context": (
            "Enterprise SaaS organizations (10M+ ARR) often run 8–12 disconnected sales tools "
            "with no unified execution layer. Revenue workflow orchestration consolidates "
            "enrichment, sequencing, CRM routing, and reporting into one governed system — "
            "giving RevOps full visibility and control at scale."
        ),
        "seed_keywords": [
            "enterprise saas outbound automation",
            "revops workflow orchestration platform",
            "enterprise sales automation saas",
            "revenue workflow orchestration enterprise",
            "saas enterprise pipeline system",
            "outbound automation for enterprise saas",
            "revops automation platform saas",
            "scale outbound enterprise revenue team",
            "enterprise saas sales workflow governance",
            "multi-territory outbound automation",
        ],
        "topic_cluster_modifiers": ["enterprise", "revops", "multi-territory", "at scale", "governance"],
    },
}

# Stage × Role affinity — which roles are most relevant at each stage
STAGE_ROLE_AFFINITY: dict[str, list[str]] = {
    "early": ["founder", "vp_sales"],
    "growth": ["vp_sales", "sales_manager", "cso"],
    "scale": ["cro", "cso", "vp_sales"],
}

# Stage-specific CTA configurations
STAGE_CTA: dict[str, dict[str, str]] = {
    "early": {
        "primary_label": "Build your pipeline system",
        "primary_subtext": "No SDR team needed",
        "urgency": "Start automating outbound today — before you make your first sales hire.",
    },
    "growth": {
        "primary_label": "Scale your outbound system",
        "primary_subtext": "Double SDR output without adding headcount",
        "urgency": "See how growth-stage teams use Pipeleap to build consistent pipeline.",
    },
    "scale": {
        "primary_label": "Book a workflow assessment",
        "primary_subtext": "For RevOps and sales leadership at 10M+ ARR",
        "urgency": "Replace your fragmented stack with one orchestration layer.",
    },
}

# Comparison dimensions for Before/After tables, keyed by stage
STAGE_BEFORE_AFTER: dict[str, list[tuple[str, str, str]]] = {
    "early": [
        ("Lead sourcing", "Founder manually building lists in spreadsheets", "Automated enrichment from signals at intake"),
        ("Outreach", "Founder writing emails one-by-one in Gmail", "Personalized sequences triggered automatically"),
        ("Follow-ups", "Sticky notes and calendar reminders", "Automated cadence with zero missed steps"),
        ("CRM updates", "Logging calls and emails manually after each conversation", "Real-time write-back on every workflow trigger"),
        ("Reporting", "Counting emails sent in spreadsheet", "Pipeline velocity tracked across every stage"),
        ("Scalability", "Can't hire until pipeline is proven", "Pipeline system ready to hand off to first rep"),
    ],
    "growth": [
        ("Playbook consistency", "Top rep's playbook lives in their head", "Every rep runs the same winning workflow"),
        ("Lead enrichment", "SDRs manually researching each prospect", "Automated at intake — zero SDR research time"),
        ("CRM hygiene", "Weekly manual cleanup by RevOps", "Real-time write-back keeps CRM always current"),
        ("Sequence performance", "No visibility into which sequences work", "Full analytics on every sequence and segment"),
        ("Ramp time", "New SDRs take 3–4 months to reach quota", "Governed playbooks cut ramp to 6–8 weeks"),
        ("Pipeline predictability", "Miss forecasts because data is inconsistent", "Consistent execution = reliable pipeline forecasts"),
    ],
    "scale": [
        ("Tool stack", "8+ disconnected point solutions", "Single orchestration layer replacing them all"),
        ("RevOps capacity", "80% maintaining integrations", "80% building strategy and running experiments"),
        ("Territory execution", "Each territory runs different playbooks", "Governed workflows enforce consistency everywhere"),
        ("Experiment velocity", "Weeks to launch a new outbound motion", "New workflows live in hours, not weeks"),
        ("Compliance & governance", "No enforcement layer — reps go off-script", "Governed execution with full audit trail"),
        ("Reporting", "Stitching together 5 dashboards to see pipeline", "Unified visibility across all motions and territories"),
    ],
}
