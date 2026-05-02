"""
BOFU (Bottom-of-Funnel) page generator for Pipeleap.

Generates three BOFU page types:
  1. demo_use_case   — "Book a Pipeleap demo for [specific use case]"
  2. roi_page        — "Calculate your outbound automation ROI with Pipeleap"
  3. pricing_comparison — "Pipeleap pricing vs [competitor stack]"

These pages target buyers who are already considering Pipeleap and need
the final push: proof of ROI, a use-case-specific demo hook, or pricing justification.
They are the highest-revenue-per-visitor pages in the site.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from modules.pipeleap_seo_engine.data.funnel_stages import FUNNEL_STAGES, ROLE_JOURNEYS
from modules.pipeleap_seo_engine.data.objections import (
    get_universal_objections, get_pricing_objections, get_objections_for_competitor
)
from modules.pipeleap_seo_engine.data.pain_points import BEFORE_AFTER, POSITIONING
from modules.pipeleap_seo_engine.models import GrowthPage


SITE_URL = "https://pipeleap.com"
AUDIT_URL = f"{SITE_URL}/gtm-audit"

# Demo use-case definitions — each generates one BOFU page
DEMO_USE_CASES = [
    {
        "slug": "book-demo-outbound-automation",
        "use_case": "outbound automation",
        "headline": "See Pipeleap automate your full outbound workflow — live in 30 minutes",
        "subhead": "We'll map your exact signal-to-sequence workflow in your first call.",
        "pain": "Manual outbound execution is capping your pipeline at a predictable ceiling.",
        "outcome": "A live walkthrough of how Pipeleap orchestrates your specific outbound workflow — signal capture, enrichment, sequencing, and reply routing — end to end.",
        "keywords": ["outbound automation demo", "book outbound automation demo", "pipeleap demo"],
        "persona": "VP Sales, CRO, RevOps",
    },
    {
        "slug": "book-demo-revops-workflow",
        "use_case": "RevOps workflow orchestration",
        "headline": "See Pipeleap govern your RevOps workflows — live demo for your stack",
        "subhead": "We'll show you exactly how Pipeleap integrates with your current CRM, enrichment tool, and sequencer.",
        "pain": "Your RevOps team spends more time maintaining tool integrations than building strategy.",
        "outcome": "A technical demo showing Pipeleap's workflow engine integrating with your exact stack — HubSpot or Salesforce, Clay or Apollo, Outreach or Instantly.",
        "keywords": ["revops workflow demo", "book revops automation demo", "workflow orchestration demo"],
        "persona": "RevOps, VP Sales",
    },
    {
        "slug": "book-demo-founder-led-outbound",
        "use_case": "founder-led outbound",
        "headline": "Build your outbound pipeline before your first sales hire — Pipeleap demo",
        "subhead": "We'll show you how SaaS founders run outbound on autopilot before Series A.",
        "pain": "You're doing outbound manually and it's not scalable — but you're not ready to hire an SDR.",
        "outcome": "A demo showing the exact founder-led outbound workflow: ICP signal detection, automated enrichment, personalized sequences, and meeting booking — zero SDR required.",
        "keywords": ["founder led outbound demo", "saas founder pipeline demo", "automated outbound for founders"],
        "persona": "Founders, early-stage GTM",
    },
    {
        "slug": "book-demo-pipeline-generation",
        "use_case": "predictable pipeline generation",
        "headline": "See how Pipeleap builds predictable outbound pipeline — 30-minute demo",
        "subhead": "We'll walk through your current pipeline motion and show exactly where workflow orchestration multiplies output.",
        "pain": "Pipeline generation is inconsistent because it depends on individual rep effort, not a governed system.",
        "outcome": "A demo of Pipeleap's pipeline generation system — from signal capture to meeting booked — with benchmarks from comparable SaaS teams.",
        "keywords": ["pipeline generation demo", "predictable pipeline demo", "outbound pipeline system demo"],
        "persona": "CRO, VP Sales, Founders",
    },
]

# ROI calculation inputs for the ROI page
ROI_INPUTS = [
    {"label": "SDR headcount", "variable": "sdr_count", "default": 3, "unit": "reps"},
    {"label": "Hours/week per SDR on manual tasks", "variable": "manual_hours", "default": 15, "unit": "hrs"},
    {"label": "Average SDR fully-loaded cost", "variable": "sdr_cost", "default": 80000, "unit": "USD/yr"},
    {"label": "Current outbound meetings booked per SDR per month", "variable": "meetings_per_sdr", "default": 8, "unit": "meetings"},
    {"label": "Average deal value", "variable": "deal_value", "default": 25000, "unit": "USD"},
]

ROI_OUTPUTS = [
    "Hours reclaimed per SDR per week from workflow automation",
    "Equivalent FTE capacity freed without new hires",
    "Projected increase in meetings booked per SDR (30–60% based on benchmark data)",
    "Pipeline uplift per quarter from automation",
    "Break-even month for Pipeleap investment",
]

# Competitor stacks for pricing comparison pages
COMPETITOR_STACKS = [
    {
        "slug": "pipeleap-pricing-vs-clay-stack",
        "stack_name": "Clay + Zapier + Apollo stack",
        "competitors": ["Clay", "Zapier", "Apollo"],
        "stack_cost_low": 800,
        "stack_cost_high": 1800,
        "stack_pain": "Three separate tools with no unified execution layer — manual work at every handoff.",
        "keywords": ["pipeleap pricing vs clay", "pipeleap cost comparison", "clay zapier apollo alternative pricing"],
    },
    {
        "slug": "pipeleap-pricing-vs-outreach-salesloft",
        "stack_name": "Outreach or SalesLoft + manual SDR work",
        "competitors": ["Outreach", "SalesLoft"],
        "stack_cost_low": 1200,
        "stack_cost_high": 3000,
        "stack_pain": "High per-seat costs plus the manual overhead of building and managing sequences by hand.",
        "keywords": ["pipeleap vs outreach pricing", "pipeleap vs salesloft cost", "cheaper outbound automation"],
    },
]


class BOFUPageGenerator:
    """Generates high-converting BOFU pages for Pipeleap's revenue path."""

    def __init__(self, content_engine: Any) -> None:
        self.ce = content_engine
        self.site_url = getattr(content_engine, "site_url", SITE_URL)
        self.bofu = FUNNEL_STAGES["BOFU"]
        self.publish_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def generate_all(self, existing_slugs: set[str]) -> list[GrowthPage]:
        pages: list[GrowthPage] = []
        for uc in DEMO_USE_CASES:
            if uc["slug"] not in existing_slugs:
                pages.append(self._demo_page(uc))
                existing_slugs.add(uc["slug"])

        roi_slug = "outbound-automation-roi-calculator"
        if roi_slug not in existing_slugs:
            pages.append(self._roi_page(roi_slug))
            existing_slugs.add(roi_slug)

        for stack in COMPETITOR_STACKS:
            if stack["slug"] not in existing_slugs:
                pages.append(self._pricing_comparison_page(stack))
                existing_slugs.add(stack["slug"])

        return pages

    # ── Demo use-case pages ────────────────────────────────────────────────────

    def _demo_page(self, uc: dict) -> GrowthPage:
        slug = uc["slug"]
        title = uc["headline"]
        seo_title = f"{title} | Pipeleap"
        meta = f"Book a Pipeleap demo for {uc['use_case']}. {uc['outcome'][:120]}."

        body = self._render_demo_body(uc)
        schemas = self._demo_schemas(title, meta, slug)

        return GrowthPage(
            slug=slug,
            page_type="bofu_page",
            title=title,
            seo_title=seo_title,
            meta_description=meta,
            h1=title,
            body_markdown=body,
            schema_markup=schemas,
            call_to_action=self.bofu["cta_primary"],
            primary_keyword=uc["keywords"][0],
            target_keywords=uc["keywords"],
            internal_links=[],
            canonical_url=f"{self.site_url}/blog/{slug}",
            publish_date=self.publish_date,
            intent="transactional",
            topical_pillar="pipeline-generation",
        )

    def _render_demo_body(self, uc: dict) -> str:
        bofu = self.bofu
        audit_cta = f"[{bofu['cta_primary']}]({AUDIT_URL}?utm_source=organic&utm_medium=seo&utm_campaign=bofu_demo&utm_content={uc['slug']})"
        secondary_cta = f"[{bofu['cta_secondary']}]({self.site_url}/contact?utm_source=organic&utm_medium=seo&utm_campaign=bofu_demo_secondary)"

        objections = get_universal_objections(3)

        lines = [
            f"**What you'll see in this demo:** {uc['outcome']}",
            "",
            f"# {uc['headline']}",
            "",
            f"> **The problem:** {uc['pain']}",
            "",
            f"{audit_cta}",
            "",
            "---",
            "",
            "## What this demo covers",
            "",
            f"This is a working demonstration of Pipeleap's workflow orchestration for "
            f"**{uc['use_case']}**. Not a slideshow — a live walkthrough of the actual system "
            f"running against a workflow modelled on your use case.",
            "",
            "In 30 minutes you'll see:",
            "",
            "- How Pipeleap captures and classifies buying signals in real time",
            "- How enrichment runs automatically before any sequence fires",
            f"- How outbound sequences execute across channels for {uc['use_case']} workflows",
            "- How replies are classified and routed without manual monitoring",
            "- How the CRM stays clean without manual logging",
            "",
            "## Who this demo is built for",
            "",
            f"This walkthrough is designed for: **{uc['persona']}**.",
            "",
            "The workflow shown is calibrated to your stage and use case. "
            "You'll see the specific signals, enrichment logic, and sequence structure "
            "that perform best for your scenario — not a generic product tour.",
            "",
            "## What happens before the demo",
            "",
            "When you book through the GTM audit form, we do a 15-minute intake:",
            "",
            "1. **Current stack:** What CRM, enrichment tools, and sequencers you use today",
            "2. **ICP definition:** Who you're targeting and what signals are available",
            "3. **Biggest workflow gap:** Where manual execution is costing you the most",
            "",
            "We use this to customise the demo workflow to your exact situation. "
            "No two demos are the same.",
            "",
            "## What teams typically see after implementation",
            "",
            *[f"| {dim} | {before} | {after} |"
              for dim, before, after in BEFORE_AFTER[:5]],
            "",
            "## Common questions before booking",
            "",
        ]

        for obj in objections:
            lines += [
                f"### {obj['objection']}",
                "",
                obj["rebuttal"],
                "",
            ]

        lines += [
            "---",
            "",
            "## Book your demo",
            "",
            f"Demos run 30 minutes. Availability: Monday–Friday, same-week slots available.",
            "",
            f"{audit_cta}",
            "",
            f"_Or {secondary_cta} to discuss your use case before committing to a full demo._",
            "",
            f"_{bofu['cta_urgency']}_",
            "",
        ]

        return "\n".join(lines)

    # ── ROI page ───────────────────────────────────────────────────────────────

    def _roi_page(self, slug: str) -> GrowthPage:
        title = "Outbound Automation ROI Calculator — What Does Manual Outbound Actually Cost?"
        seo_title = f"{title} | Pipeleap"
        meta = (
            "Calculate the real cost of manual outbound execution and the ROI of workflow automation. "
            "See how many meetings, pipeline, and FTE hours Pipeleap adds for your SaaS team."
        )
        body = self._render_roi_body(slug)
        schemas = self._roi_schemas(title, meta, slug)

        return GrowthPage(
            slug=slug,
            page_type="roi_page",
            title=title,
            seo_title=seo_title,
            meta_description=meta,
            h1=title,
            body_markdown=body,
            schema_markup=schemas,
            call_to_action=FUNNEL_STAGES["BOFU"]["cta_primary"],
            primary_keyword="outbound automation roi",
            target_keywords=["outbound automation roi", "sales automation roi calculator", "pipeline automation roi"],
            internal_links=[],
            canonical_url=f"{self.site_url}/blog/{slug}",
            publish_date=self.publish_date,
            intent="transactional",
            topical_pillar="pipeline-generation",
        )

    def _render_roi_body(self, slug: str) -> str:
        bofu = FUNNEL_STAGES["BOFU"]
        audit_cta = f"[{bofu['cta_primary']}]({AUDIT_URL}?utm_source=organic&utm_medium=seo&utm_campaign=roi_page&utm_content={slug})"

        pricing_objs = get_pricing_objections()

        lines = [
            "**The short answer:** Manual outbound costs 15–20 hours per SDR per week in tasks that workflow automation eliminates entirely.",
            "",
            "# Outbound Automation ROI Calculator",
            "",
            "## The hidden cost of manual outbound execution",
            "",
            "Most SaaS teams measure outbound ROI by pipeline created. "
            "They rarely measure the cost of the *manual execution* required to produce that pipeline.",
            "",
            "The average SDR spends:",
            "",
            "- **3.5 hours/day** on manual prospect research and list building",
            "- **2 hours/day** on manual CRM logging and data hygiene",
            "- **1.5 hours/day** on manual sequence enrollment and follow-up monitoring",
            "- **1 hour/day** on inbox management and reply classification",
            "",
            "That's **8 hours of every 8-hour workday** on tasks that workflow automation eliminates.",
            "",
            "## ROI model: 3 SDRs over 12 months",
            "",
            "| Input | Manual Outbound | With Pipeleap |",
            "| --- | --- | --- |",
            "| Hours/week per SDR on manual tasks | 15–20 hrs | 2–3 hrs |",
            "| Meetings booked per SDR per month | 6–10 | 10–18 |",
            "| Pipeline generated per SDR per quarter | $150K–$300K | $280K–$550K |",
            "| FTE capacity equivalent from automation | 0 | 1.5–2 additional reps |",
            "| Stack cost (tools + SDR time) | $180K–$320K/yr | $140K–$220K/yr |",
            "",
            "## What to include in your ROI calculation",
            "",
            "**Direct costs to automate out:**",
            "- Manual research time (hours × SDR cost)",
            "- Manual CRM maintenance (hours × RevOps cost)",
            "- Manual sequence management (hours × SDR cost)",
            "- Tool sprawl maintenance (hours × RevOps cost)",
            "",
            "**Revenue upside to model in:**",
            "- Meetings booked increase from automation (30–60% benchmark)",
            "- Pipeline per quarter increase from consistent execution",
            "- Revenue per rep increase from focus on closing vs. admin",
            "",
            "**Risk costs to eliminate:**",
            "- Missed follow-ups from manual tracking",
            "- CRM data decay from manual logging gaps",
            "- Reply routing delays causing lost demo slots",
            "",
            "## How to get your specific numbers",
            "",
            "The GTM audit process produces a personalised ROI model for your team size, "
            "current stack, and target pipeline within 48 hours.",
            "",
            f"{audit_cta}",
            "",
        ]

        for obj in pricing_objs:
            lines += [
                f"### {obj['objection']}",
                "",
                obj["rebuttal"],
                "",
            ]

        return "\n".join(lines)

    # ── Pricing comparison pages ───────────────────────────────────────────────

    def _pricing_comparison_page(self, stack: dict) -> GrowthPage:
        slug = stack["slug"]
        title = f"Pipeleap Pricing vs {stack['stack_name']} — Full Cost Comparison"
        seo_title = f"{title} | Pipeleap"
        meta = (
            f"Compare Pipeleap pricing against the {stack['stack_name']}. "
            "Total cost of ownership, hidden maintenance costs, and ROI breakdown for SaaS teams."
        )
        body = self._render_pricing_body(stack, slug)
        schemas = self._pricing_schemas(title, meta, slug)

        all_keywords = stack["keywords"] + ["outbound automation pricing", "pipeleap pricing"]

        return GrowthPage(
            slug=slug,
            page_type="bofu_page",
            title=title,
            seo_title=seo_title,
            meta_description=meta,
            h1=title,
            body_markdown=body,
            schema_markup=schemas,
            call_to_action=FUNNEL_STAGES["BOFU"]["cta_primary"],
            primary_keyword=stack["keywords"][0],
            target_keywords=all_keywords,
            internal_links=[],
            canonical_url=f"{self.site_url}/blog/{slug}",
            publish_date=self.publish_date,
            intent="transactional",
            topical_pillar="competitor-comparison",
        )

    def _render_pricing_body(self, stack: dict, slug: str) -> str:
        bofu = FUNNEL_STAGES["BOFU"]
        audit_cta = f"[{bofu['cta_primary']}]({AUDIT_URL}?utm_source=organic&utm_medium=seo&utm_campaign=pricing_comparison&utm_content={slug})"

        comp_list = " + ".join(stack["competitors"])
        low = stack["stack_cost_low"]
        high = stack["stack_cost_high"]

        lines = [
            f"**Bottom line:** The {comp_list} stack costs ${low}–${high}/month in tool fees alone — "
            "before factoring in the 15–20 hours/week of manual work required to connect them.",
            "",
            f"# Pipeleap Pricing vs {stack['stack_name']}",
            "",
            "## The real cost of your current stack",
            "",
            f"{stack['stack_pain']}",
            "",
            "When you add up the full cost of your current outbound stack — tool fees, "
            "manual execution time, RevOps maintenance, and missed opportunities — "
            "the comparison changes significantly.",
            "",
            "| Cost component | Current stack | With Pipeleap |",
            "| --- | --- | --- |",
            f"| Tool subscription fees | ${low}–${high}/mo | One platform fee |",
            "| Manual execution hours (SDR time) | 15–20 hrs/SDR/week | 2–3 hrs/SDR/week |",
            "| RevOps maintenance hours | 5–10 hrs/week | <1 hr/week |",
            "| Integration failure risk | High (API changes, rate limits) | Low (governed workflows) |",
            "| Total cost of ownership | High | 30–40% lower |",
            "",
            "## What the stack comparison misses",
            "",
            "Tool-to-tool price comparisons miss the most important variable: **execution overhead**.",
            "",
            f"The {comp_list} stack requires a human to:",
            "",
            f"- Manually connect {comp_list} via Zaps or manual exports",
            "- Manually enroll prospects into sequences after enrichment",
            "- Manually monitor replies and route them to the right rep",
            "- Manually log CRM updates after each outbound step",
            "",
            "Pipeleap automates every one of those steps. The tool fee comparison "
            "understates Pipeleap's value by ignoring the labour cost it eliminates.",
            "",
            "## What Pipeleap includes",
            "",
            "- Signal capture and workflow trigger automation",
            "- Enrichment waterfall orchestration (connects to Clay, Apollo, ZoomInfo, or your source)",
            "- Outbound sequence execution governance (connects to your existing sequencer)",
            "- Reply routing and classification automation",
            "- CRM write-back and hygiene automation",
            "- GTM audit and workflow design (included in onboarding)",
            "- Ongoing workflow performance monitoring",
            "",
            "## See the full comparison before deciding",
            "",
            f"{audit_cta}",
            "",
            f"_{bofu['cta_urgency']}_",
        ]

        return "\n".join(lines)

    # ── Schema markup ──────────────────────────────────────────────────────────

    def _demo_schemas(self, title: str, desc: str, slug: str) -> list[dict]:
        page_url = f"{self.site_url}/blog/{slug}"
        return [
            {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": title,
                "description": desc,
                "url": page_url,
                "publisher": {"@type": "Organization", "name": "Pipeleap", "url": self.site_url},
            },
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "url": page_url,
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": obj["objection"],
                        "acceptedAnswer": {"@type": "Answer", "text": obj["rebuttal"]},
                    }
                    for obj in get_universal_objections(3)
                ],
            },
        ]

    def _roi_schemas(self, title: str, desc: str, slug: str) -> list[dict]:
        page_url = f"{self.site_url}/blog/{slug}"
        return [
            {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": title,
                "description": desc,
                "url": page_url,
                "publisher": {"@type": "Organization", "name": "Pipeleap", "url": self.site_url},
            },
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "url": page_url,
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": obj["objection"],
                        "acceptedAnswer": {"@type": "Answer", "text": obj["rebuttal"]},
                    }
                    for obj in get_pricing_objections()
                ],
            },
        ]

    def _pricing_schemas(self, title: str, desc: str, slug: str) -> list[dict]:
        return self._roi_schemas(title, desc, slug)
