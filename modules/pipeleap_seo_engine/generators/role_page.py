"""Role-based page generator for the Pipeleap SaaS Growth Engine."""
from __future__ import annotations

from typing import Any

from modules.pipeleap_seo_engine.data.roles import ROLES
from modules.pipeleap_seo_engine.data.pain_points import USE_CASE_EXAMPLES
from modules.pipeleap_seo_engine.data.authors import get_author_for_page_type
from modules.pipeleap_seo_engine.engines.content_engine import GrowthContentEngine
from modules.pipeleap_seo_engine.models import GrowthPage

# Role-specific before/after tables — each role sees the dimensions most
# relevant to their day-to-day, preventing identical sections across pages.
ROLE_BEFORE_AFTER: dict[str, list[tuple[str, str, str]]] = {
    "cro": [
        ("Pipeline predictability", "Dependent on individual rep activity, misses targets quarterly", "Governed workflow engine produces consistent pipeline regardless of rep"),
        ("Headcount to scale", "Every pipeline target requires proportional SDR headcount growth", "Automated workflows scale output without adding headcount cost"),
        ("Outbound visibility", "No unified view across execution — 5+ dashboards, none complete", "Single workflow execution layer with full-funnel visibility"),
        ("Revenue forecasting", "Forecasts miss because pipeline data is unreliable and stale", "Clean, real-time workflow data makes forecasts accurate and defensible"),
        ("Market coverage", "Coverage gaps in territories because execution is rep-dependent", "Every territory runs the same governed workflow automatically"),
    ],
    "cso": [
        ("Execution consistency", "Top reps carry everyone — each person runs a different process", "Every rep runs the best-performing workflow automatically"),
        ("Tool governance", "6–8 point solutions with no unified execution layer", "One orchestration layer connecting all tools with governed logic"),
        ("Rep onboarding", "3–6 month ramp because reps must learn 6 tools and the process", "New reps get the workflow from day one — ramp drops to 6–8 weeks"),
        ("Organisation-wide coverage", "Sales motions differ by region, segment, and rep preference", "Consistent motions across the full sales organization"),
        ("Admin overhead", "65%+ of rep time spent on manual admin tasks", "Admin automated — reps focus 100% on conversations and closing"),
    ],
    "vp_sales": [
        ("Playbook consistency", "Top rep's playbook lives in their head — unreplicable", "Best playbook encoded in automated workflows every rep runs"),
        ("Pipeline per rep", "Pipeline generated varies wildly between team members", "Consistent pipeline per rep because every workflow runs the same"),
        ("Sequence management", "VP manually reviews and updates sequences — weekly overhead", "Sequences governed by workflow engine — optimizations take minutes"),
        ("New rep ramp", "3–4 months before new reps reach quota contribution", "Governed playbooks cut ramp time by 40–60%"),
        ("CRM hygiene", "Manual logging creates gaps, duplicates, and outdated pipeline data", "Every workflow trigger writes structured data to CRM automatically"),
    ],
    "sales_manager": [
        ("Execution gaps", "Bottom performers have no system — rely on top performers to copy", "Every rep runs the same automated workflow regardless of seniority"),
        ("Activity tracking", "Manually tracking outreach across inbox, CRM, and spreadsheet", "All outreach tracked automatically at every workflow stage"),
        ("Follow-up consistency", "Reps forget follow-ups — deals stall waiting for human action", "Automated cadences fire on schedule with zero missed steps"),
        ("Coaching time", "70% of time firefighting execution problems, 30% actually coaching", "No execution fires — manager time shifts entirely to coaching"),
        ("Sequence performance", "No clear data on which sequences, segments, messages convert", "Full performance data per sequence, segment, and rep in real time"),
    ],
    "founder": [
        ("Founder time on outbound", "4–6 hours/day on manual outbound tasks — no time for product or closing", "Full outbound workflow automated — founder invests 0 hours on admin"),
        ("Pipeline before SDR hire", "No pipeline system = can't prove what works before hiring", "Automated pipeline system running before first sales hire"),
        ("Scaling outbound", "More outbound = more founder time — hard ceiling with no team", "Volume scales without adding founder time or headcount"),
        ("System handoff", "When first rep joins, they start from scratch on process and tools", "Rep inherits a documented, governed workflow system from day one"),
        ("Tool sprawl", "Apollo + Gmail + Sheets + 3 others with no connected logic", "Single orchestration layer replacing the disconnected stack"),
    ],
}

# Role-specific use-case examples — distinct from the generic USE_CASE_EXAMPLES
ROLE_USE_CASES: dict[str, list[dict]] = {
    "cro": [
        {"title": "Predictable Pipeline Across All Markets",
         "description": "A SaaS CRO uses Pipeleap to govern outbound execution across 3 regional SDR teams, ensuring consistent workflow logic runs in every market — eliminating territory performance variance.",
         "outcome": "Pipeline generation becomes consistent and predictable across all markets and territories."},
        {"title": "Headcount-Independent Revenue Growth",
         "description": "Instead of adding 3 SDRs to hit the next pipeline target, the CRO deploys Pipeleap to automate the manual execution gap — scaling workflow output without proportional headcount cost.",
         "outcome": "3× pipeline output with the same SDR headcount."},
    ],
    "cso": [
        {"title": "Organisation-Wide Playbook Enforcement",
         "description": "A CSO at a 50-person SaaS company uses Pipeleap to encode the top-performing rep's outbound playbook into governed workflows that run automatically across the entire sales org.",
         "outcome": "Every rep runs the best playbook. Execution is consistent across segments."},
        {"title": "Tech Stack Consolidation",
         "description": "The CSO replaces 7 disconnected sales tools with Pipeleap as the unified orchestration layer — enrichment, sequencing, routing, and CRM sync all governed in one system.",
         "outcome": "60% reduction in RevOps maintenance time. Full execution visibility for the first time."},
    ],
    "vp_sales": [
        {"title": "Scaling Top-Rep Performance Across the Team",
         "description": "A VP Sales encodes the sequences and signals from their #1 rep into Pipeleap workflows — every SDR now runs the same winning motion automatically from week one.",
         "outcome": "Bottom-quartile SDRs reach quota at the same rate as top performers within 60 days."},
        {"title": "New Rep Ramp Time Reduction",
         "description": "VP Sales uses Pipeleap to remove the 6-tool learning curve from new rep onboarding. Reps start with a fully built workflow — they focus on conversations, not setup.",
         "outcome": "Ramp time drops from 4 months to 6 weeks."},
    ],
    "sales_manager": [
        {"title": "Eliminating Follow-Up Gaps",
         "description": "A sales manager automates follow-up cadences in Pipeleap so no prospect falls through the cracks between manual touchpoints — every deal gets the right follow-up at the right time.",
         "outcome": "Reply rate increases 30% as follow-up consistency improves across the team."},
        {"title": "Real-Time Sequence Performance Visibility",
         "description": "Instead of guessing which sequences work, the manager uses Pipeleap's workflow-level performance data to identify underperforming segments and optimize in real time.",
         "outcome": "Sequence optimization cycle drops from 6 weeks to 3 days."},
    ],
    "founder": [
        {"title": "Founder-Led Pipeline Before Series A",
         "description": "A pre-seed SaaS founder uses Pipeleap to run outbound automatically — capturing intent signals, enriching prospects, sending personalized sequences — while spending zero hours on manual outbound admin.",
         "outcome": "10 demos/month booked on autopilot. Founder spends 100% of time on product and closing."},
        {"title": "Pipeline System Ready to Hand Off",
         "description": "As the founder prepares to hire their first sales rep, they use Pipeleap to document and automate the outbound workflow so the new hire inherits a proven system, not a blank slate.",
         "outcome": "First rep is productive from week 1 with a governed workflow system."},
    ],
}


class RolePageGenerator:

    def __init__(self, content_engine: GrowthContentEngine) -> None:
        self.ce = content_engine

    def generate_all(self, existing_slugs: set[str]) -> list[GrowthPage]:
        pages = []
        for role_key, role in ROLES.items():
            if role["slug"] in existing_slugs:
                continue
            page = self._generate(role_key, role)
            pages.append(page)
            existing_slugs.add(role["slug"])
        return pages

    def _generate(self, role_key: str, role: dict[str, Any]) -> GrowthPage:
        headline = role["headlines"][0]
        slug = role["slug"]
        page_url = f"{self.ce.site_url}/{slug}"

        # Featured snippet
        snippet = self.ce.featured_snippet_block(
            f"What is the best outbound automation solution for a SaaS {role['abbreviation']}?",
            f"{self.ce.brand} is a workflow orchestration system built for SaaS {role['label']}s who need predictable pipeline without manual execution or additional SDR headcount. "
            f"It orchestrates signal capture, enrichment, sequencing, and CRM routing automatically.",
        )

        # Section: Hero
        hero = self.ce.hero_section(
            headline=headline,
            hero_stat=role["hero_stat"],
            subhead=f"Built for SaaS {role['label']}s who need **{role['desired_outcomes'][0]}**.",
            cta_label=role["cta_label"],
        )

        # Section: Problem
        problem = self.ce.problem_section(
            pain_points=role["pain_points"],
            context=f"As a SaaS {role['label']}, you're responsible for {role['desired_outcomes'][0].lower()}. "
                    f"But the systems most organizations rely on make this nearly impossible.",
        )

        # Section: Solution
        solution = self.ce.solution_section(
            role_context=f"For SaaS {role['label']}s specifically, {self.ce.brand} delivers: "
                         + " and ".join(f"**{o}**" for o in role["desired_outcomes"][:2]) + ".",
        )

        # Section: How it works (role-specific subhead)
        how_it_works = self.ce.how_it_works_section(slug=slug)

        # Section: Before vs after — inject role-specific rows so every role
        # page has a distinct table rather than the identical generic version.
        role_ba_rows = ROLE_BEFORE_AFTER.get(role_key)
        before_after = self.ce.before_after_section(custom_rows=role_ba_rows)

        # Section: Use cases — inject role-specific examples
        role_uc_examples = ROLE_USE_CASES.get(role_key)
        use_cases = self.ce.use_cases_section(custom_cases=role_uc_examples)

        # Section: Positioning callout
        positioning = self.ce.positioning_callout()

        # Section: FAQ
        faq = self.ce.faq_section(role["faq"])

        # Section: CTA
        cta = self.ce.cta_section(
            label=role["cta_label"],
            urgency=f"Join SaaS {role['label']}s building predictable pipeline with {self.ce.brand}.",
        )

        stats = self.ce.statistics_section()
        author_byline = self.ce.author_byline(get_author_for_page_type("role_page"))
        body = "\n".join([
            snippet, author_byline, hero, stats, problem,
            solution, how_it_works, before_after, use_cases, positioning, faq, cta,
        ])

        schema = [
            self.ce.webpage_schema(role["page_title"], role["meta_description"], page_url),
            self.ce.howto_schema(f"How Pipeleap works for SaaS {role['label']}s", role["meta_description"], page_url),
            self.ce.breadcrumb_schema([
                ("Home", self.ce.site_url),
                ("For " + role["label"] + "s", page_url),
            ]),
            self.ce.software_application_schema(),
            *self.ce.faq_schema(role["faq"], page_url),
        ]
        author = get_author_for_page_type("role_page")

        return GrowthPage(
            slug=slug,
            page_type="role_page",
            title=role["page_title"],
            seo_title=role["page_title"],
            meta_description=role["meta_description"],
            canonical_url=page_url,
            og_meta=self.ce.og_meta(role["page_title"], role["meta_description"], page_url),
            twitter_meta=self.ce.twitter_meta(role["page_title"], role["meta_description"]),
            h1=headline,
            role=role_key,
            intent="transactional",
            topical_pillar="pipeline-generation",
            body_markdown=body,
            schema_markup=schema,
            call_to_action=self.ce.cta_section(label=role["cta_label"], slug=slug, campaign="role_page"),
            primary_keyword=role["keywords"][0],
            target_keywords=role["keywords"],
            internal_links=[],
            author_name=author["name"],
            author_slug=author["slug"],
            breadcrumbs=[("Home", self.ce.site_url), (role["label"], page_url)],
            industry="SaaS",
            pain_points=role["pain_points"],
        )
