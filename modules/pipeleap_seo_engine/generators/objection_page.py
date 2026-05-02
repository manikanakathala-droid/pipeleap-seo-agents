"""
Objection handling page generator for Pipeleap.

Creates trust-building, late-funnel pages that address the exact doubts
a buyer has just before making a decision. These pages are designed to
rank for queries like:
  - "Is Pipeleap worth it"
  - "Pipeleap review"
  - "Pipeleap pricing too expensive"
  - "Should I use Pipeleap or build my own automation"
  - "Pipeleap vs hiring another SDR"

These pages are the highest-intent, lowest-volume pages in the site —
and the ones that most directly influence whether a warm lead converts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from modules.pipeleap_seo_engine.data.funnel_stages import FUNNEL_STAGES, ROLE_JOURNEYS
from modules.pipeleap_seo_engine.data.objections import (
    UNIVERSAL_OBJECTIONS, PRICING_OBJECTIONS, get_objections_for_competitor
)
from modules.pipeleap_seo_engine.models import GrowthPage

SITE_URL = "https://pipeleap.com"
AUDIT_URL = f"{SITE_URL}/gtm-audit"


OBJECTION_PAGES = [
    {
        "slug": "is-pipeleap-right-for-my-saas",
        "title": "Is Pipeleap Right for My SaaS Team? Honest Evaluation Guide",
        "keywords": ["is pipeleap worth it", "pipeleap review", "should i use pipeleap", "pipeleap evaluation"],
        "angle": "fit_guide",
        "meta": (
            "Honest guide to deciding if Pipeleap fits your SaaS outbound motion. "
            "Who it works best for, what it doesn't do, and how to evaluate it for your team."
        ),
    },
    {
        "slug": "pipeleap-vs-hiring-another-sdr",
        "title": "Pipeleap vs Hiring Another SDR — Which Builds More Pipeline Faster?",
        "keywords": ["pipeleap vs hiring sdr", "outbound automation vs sdr hire", "should i hire sdr or automate"],
        "angle": "vs_hire",
        "meta": (
            "Compare the cost, timeline, and pipeline output of hiring an SDR vs. implementing "
            "Pipeleap workflow orchestration. Data-driven breakdown for SaaS founders and VP Sales."
        ),
    },
    {
        "slug": "pipeleap-implementation-questions",
        "title": "Pipeleap Implementation — What Really Happens in the First 30 Days",
        "keywords": ["pipeleap implementation", "how long does pipeleap take", "pipeleap onboarding", "pipeleap setup time"],
        "angle": "implementation",
        "meta": (
            "What actually happens in weeks 1–4 of Pipeleap implementation: GTM audit, "
            "workflow design, build, and live monitoring. No surprises — full transparency."
        ),
    },
    {
        "slug": "build-vs-buy-outbound-automation",
        "title": "Build Your Own Outbound Automation vs Buy Pipeleap — Full Comparison",
        "keywords": ["build vs buy outbound automation", "n8n vs pipeleap", "diy sales automation vs pipeleap", "build outbound workflow"],
        "angle": "build_vs_buy",
        "meta": (
            "Should you build outbound automation with n8n or buy Pipeleap? "
            "Real cost, time, and maintenance comparison for SaaS teams making the build-vs-buy decision."
        ),
    },
]


class ObjectionPageGenerator:
    """Generates objection-handling trust pages for Pipeleap's late funnel."""

    def __init__(self, content_engine: Any) -> None:
        self.ce = content_engine
        self.site_url = getattr(content_engine, "site_url", SITE_URL)
        self.bofu = FUNNEL_STAGES["BOFU"]
        self.publish_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def generate_all(self, existing_slugs: set[str]) -> list[GrowthPage]:
        pages = []
        for page_def in OBJECTION_PAGES:
            if page_def["slug"] not in existing_slugs:
                page = self._build(page_def)
                pages.append(page)
                existing_slugs.add(page_def["slug"])
        return pages

    def _build(self, defn: dict) -> GrowthPage:
        angle = defn["angle"]
        renderers = {
            "fit_guide":     self._render_fit_guide,
            "vs_hire":       self._render_vs_hire,
            "implementation":self._render_implementation,
            "build_vs_buy":  self._render_build_vs_buy,
        }
        body = renderers.get(angle, self._render_fit_guide)(defn)
        schemas = self._schemas(defn)

        return GrowthPage(
            slug=defn["slug"],
            page_type="objection_page",
            title=defn["title"],
            seo_title=f"{defn['title']} | Pipeleap",
            meta_description=defn["meta"],
            h1=defn["title"],
            body_markdown=body,
            schema_markup=schemas,
            call_to_action=self.bofu["cta_primary"],
            primary_keyword=defn["keywords"][0],
            target_keywords=defn["keywords"],
            internal_links=[],
            canonical_url=f"{self.site_url}/blog/{defn['slug']}",
            publish_date=self.publish_date,
            intent="transactional",
            topical_pillar="pipeline-generation",
        )

    def _cta(self, slug: str, label: str | None = None) -> str:
        cta_label = label or self.bofu["cta_primary"]
        return f"[{cta_label}]({AUDIT_URL}?utm_source=organic&utm_medium=seo&utm_campaign=objection_page&utm_content={slug})"

    # ── Page renderers ─────────────────────────────────────────────────────────

    def _render_fit_guide(self, defn: dict) -> str:
        slug = defn["slug"]
        cta = self._cta(slug)

        lines = [
            "**Honest answer:** Pipeleap works best for SaaS teams with a defined ICP, "
            "an existing outbound motion (even manual), and at least one person who owns GTM execution. "
            "If that's you, read on.",
            "",
            f"# {defn['title']}",
            "",
            "## Who Pipeleap works best for",
            "",
            "**Strong fit:**",
            "- SaaS teams at any ARR stage running outbound manually and want to automate it",
            "- Founders doing outbound themselves before their first sales hire",
            "- RevOps teams managing 3+ disconnected outbound tools",
            "- VP Sales who need consistent outbound execution across a team",
            "- CROs who want predictable pipeline without proportional headcount growth",
            "",
            "**Weaker fit (be honest with yourself):**",
            "- Teams with no defined ICP — automation scales outreach to the wrong people",
            "- Teams where the primary acquisition channel is inbound or product-led",
            "- Solo founders at very early stage with fewer than 50 target accounts identified",
            "- Companies where sales cycles are entirely inbound and referral-driven",
            "",
            "## The three questions to ask before evaluating",
            "",
            "**1. Do you have a defined ICP with at least 500 reachable accounts?**",
            "If yes: Pipeleap can start generating pipeline immediately.",
            "If no: The GTM audit includes ICP definition as step one.",
            "",
            "**2. Are you currently doing outbound — even manually?**",
            "If yes: Pipeleap replaces your manual execution with automated workflows.",
            "If no: Pipeleap can build your first outbound motion from scratch.",
            "",
            "**3. Do you have at least one person who owns GTM execution?**",
            "Pipeleap is not fully autonomous — it needs a human to review workflow performance, "
            "approve sequence changes, and respond to routed leads. You need someone who owns this.",
            "",
            "## What Pipeleap does not do",
            "",
            "Being clear about limitations builds more trust than overselling:",
            "",
            "- **Pipeleap is not a CRM** — it writes to your CRM (HubSpot, Salesforce) but doesn't replace it",
            "- **Pipeleap is not a sequencer** — it governs your existing sequencer (Outreach, Instantly, Smartlead)",
            "- **Pipeleap is not a data provider** — it orchestrates your enrichment tools (Clay, Apollo, ZoomInfo)",
            "- **Pipeleap does not write your sequences for you** — you own the messaging, Pipeleap automates the execution",
            "- **Pipeleap does not guarantee pipeline** — it removes execution barriers; results depend on your ICP, messaging, and offer",
            "",
            "## Common questions from teams evaluating Pipeleap",
            "",
        ]

        for obj in UNIVERSAL_OBJECTIONS[:5]:
            lines += [
                f"### {obj['objection']}",
                "",
                obj["rebuttal"],
                "",
                f"_{obj['proof_point']}_",
                "",
            ]

        lines += [
            "## The lowest-risk way to evaluate",
            "",
            "The GTM audit is free and takes 48 hours. It maps:",
            "- Your current outbound workflow (even if it's informal)",
            "- The 3 highest-leverage automation points for your stack",
            "- A projected ROI model for your team size and target pipeline",
            "",
            "If Pipeleap isn't the right fit after the audit, we'll tell you — "
            "and recommend what is. We'd rather lose a deal than waste your time.",
            "",
            f"{cta}",
        ]

        return "\n".join(lines)

    def _render_vs_hire(self, defn: dict) -> str:
        slug = defn["slug"]
        cta = self._cta(slug)

        lines = [
            "**Short answer:** A Pipeleap workflow generates the equivalent output of 1.5–2 additional "
            "SDRs from your existing team — at a fraction of the cost and without the ramp time.",
            "",
            f"# {defn['title']}",
            "",
            "## The cost comparison",
            "",
            "| Factor | Hiring an SDR | Pipeleap Workflow Orchestration |",
            "| --- | --- | --- |",
            "| Upfront cost | $0 (salary starts at hire) | GTM audit + setup fee |",
            "| Ramp time to productivity | 3–6 months | 2–3 weeks |",
            "| Fully-loaded annual cost | $80K–$130K | Fraction of one SDR |",
            "| Pipeline at month 3 | $0–$50K (ramp) | $150K–$300K (running) |",
            "| Scalability | Linear (each SDR = same cost) | Non-linear (same cost, more volume) |",
            "| Consistency | Variable (rep-dependent) | Consistent (governed workflows) |",
            "| Risk | High (wrong hire, churn, ramp cost) | Low (workflow can be adjusted) |",
            "",
            "## What a new SDR hire actually delivers in year one",
            "",
            "A realistic SDR hire timeline:",
            "",
            "- **Month 1:** Onboarding, tool access, ICP training — zero pipeline",
            "- **Month 2–3:** Learning the motion, first sequences live — 10–20% of quota",
            "- **Month 4–6:** Ramping — 50–70% of quota",
            "- **Month 7+:** Full productivity if they're still there (30% of SDRs leave in year one)",
            "",
            "**The math:** If your SDR quota is $400K pipeline/year, you're looking at "
            "$100–$150K in pipeline in the first 6 months. A Pipeleap workflow running "
            "across your existing reps produces pipeline from week 3.",
            "",
            "## When to hire an SDR instead",
            "",
            "Hiring is the right move when:",
            "- You've proven outbound works and need human relationship-building at scale",
            "- Your deal complexity requires multi-stakeholder engagement that automation can't replicate",
            "- You've automated execution and now need strategic territory management",
            "",
            "The right answer for most SaaS teams at 1–10M ARR: **automate first, hire second**.",
            "Automation gives you the pipeline data to know exactly what kind of SDR you need.",
            "",
            f"{cta}",
        ]

        return "\n".join(lines)

    def _render_implementation(self, defn: dict) -> str:
        slug = defn["slug"]
        cta = self._cta(slug, "Start your GTM audit — see your workflow blueprint in 48 hours")

        lines = [
            "**Timeline:** Most teams have a live automated workflow running by the end of week 2.",
            "",
            f"# {defn['title']}",
            "",
            "## Week 1: GTM audit and workflow design",
            "",
            "**Day 1–2: Intake and discovery**",
            "- 60-minute GTM audit call to map your current outbound motion",
            "- Stack review: CRM, enrichment tools, sequencer, signal sources",
            "- ICP validation: confirm target segments and reachable signal volume",
            "",
            "**Day 3–4: Workflow blueprint**",
            "- Pipeleap team designs your custom workflow architecture",
            "- Documents: signal triggers, enrichment logic, ICP scoring rules, sequence routing, CRM write-back",
            "- Identifies the 3 highest-ROI automation points for your specific use case",
            "",
            "**Day 5: Blueprint review**",
            "- 45-minute call to walk through the workflow design",
            "- Adjustments based on your feedback",
            "- Sign-off on the build spec",
            "",
            "## Week 2: Build and test",
            "",
            "**Day 6–9: Workflow build**",
            "- Pipeleap engineers build the n8n workflow against the approved spec",
            "- Integrations connected: your CRM, enrichment source, and sequencer",
            "- Test data runs against your ICP to verify enrichment quality and routing logic",
            "",
            "**Day 10: Live test run**",
            "- First live workflow run against a small segment of your ICP (50–100 accounts)",
            "- Review enrichment output, sequence enrollment, CRM write-back",
            "- Sign-off on workflow performance",
            "",
            "## Week 3: Go live and monitor",
            "",
            "- Full ICP segment entered into workflow",
            "- Daily monitoring for first 5 business days",
            "- Performance dashboard live: signals captured, enrichments completed, sequences enrolled, replies routed",
            "- First optimization round based on initial reply data",
            "",
            "## What you need to provide",
            "",
            "- Access to your CRM (read + write), enrichment tool, and sequencer",
            "- Your ICP definition (we can help refine this if needed)",
            "- Your outbound messaging (at least a draft — we can advise on optimization)",
            "- One person to own the workflow on your side (can be founder, VP Sales, or RevOps)",
            "",
            "## What happens after week 3",
            "",
            "- Weekly performance reviews for the first 30 days",
            "- Workflow optimizations based on reply rate and pipeline data",
            "- Expansion to additional segments or sequences as performance proves out",
            "",
            f"{cta}",
        ]

        return "\n".join(lines)

    def _render_build_vs_buy(self, defn: dict) -> str:
        slug = defn["slug"]
        cta = self._cta(slug)

        lines = [
            "**Short answer:** Building with n8n takes 3–6 months and 400+ engineering hours "
            "to reach production quality. Pipeleap is live in 2 weeks. The cost comparison "
            "changes dramatically when you include engineering time.",
            "",
            f"# {defn['title']}",
            "",
            "## The build option: what it actually costs",
            "",
            "If you build your own outbound automation with n8n, Zapier, or Make, here's what you're signing up for:",
            "",
            "**Engineering time estimates:**",
            "- Signal capture and webhook infrastructure: 40–80 hours",
            "- Enrichment waterfall logic (multiple data sources, fallback routing): 60–100 hours",
            "- ICP scoring and qualification rules: 30–50 hours",
            "- Sequencer integration (API connections, enrollment logic): 40–80 hours",
            "- CRM write-back and data hygiene rules: 40–60 hours",
            "- Reply classification and routing logic: 50–80 hours",
            "- Error handling, retry logic, alerting: 30–50 hours",
            "- Documentation and handoff: 20–30 hours",
            "",
            "**Total: 310–530 engineering hours** before a production-grade outbound workflow exists.",
            "",
            "At a $150/hr contractor rate, that's **$46K–$80K in engineering cost**.",
            "At a $180K/yr internal engineer, that's **3–6 months of dedicated engineering time**.",
            "",
            "## The ongoing maintenance cost",
            "",
            "Self-built automation has ongoing costs that compound over time:",
            "",
            "- API changes from enrichment providers break workflows (Clay, Apollo, ZoomInfo update APIs regularly)",
            "- Rate limit changes require re-engineering waterfall logic",
            "- Sequencer API updates break enrollment logic",
            "- CRM schema changes break write-back workflows",
            "- Every new outbound sequence requires engineering changes",
            "",
            "Teams that build their own outbound automation spend **5–10 hours/week** on ongoing maintenance.",
            "Over 12 months, that's 260–520 hours of engineering time — every year.",
            "",
            "## What Pipeleap provides that a build doesn't",
            "",
            "| Capability | DIY Build | Pipeleap |",
            "| --- | --- | --- |",
            "| Pre-built signal-to-sequence framework | Build from scratch | Included |",
            "| Enrichment waterfall templates | Build from scratch | Included |",
            "| API maintenance as providers update | Your engineering team | Pipeleap team |",
            "| Workflow performance monitoring | Build your own dashboards | Included |",
            "| GTM strategy guidance | None | Included in audit |",
            "| Time to first live workflow | 3–6 months | 2 weeks |",
            "",
            "## When to build instead of buy",
            "",
            "Building makes sense when:",
            "- You have a strong internal platform engineering team with capacity",
            "- Your outbound workflow has unique requirements that off-the-shelf tools can't meet",
            "- You're building outbound automation as a core product feature, not a GTM tool",
            "",
            "For most SaaS GTM teams, buying and orchestrating is the right answer — "
            "the expertise is in selling, not in building automation infrastructure.",
            "",
            f"{cta}",
        ]

        return "\n".join(lines)

    # ── Schema ─────────────────────────────────────────────────────────────────

    def _schemas(self, defn: dict) -> list[dict]:
        page_url = f"{self.site_url}/blog/{defn['slug']}"
        return [
            {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": defn["title"],
                "description": defn["meta"],
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
                    for obj in UNIVERSAL_OBJECTIONS[:4]
                ],
            },
        ]
