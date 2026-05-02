"""Use case and problem page generators for the Pipeleap SaaS Growth Engine."""
from __future__ import annotations

from typing import Any

from modules.pipeleap_seo_engine.data.use_cases import USE_CASES, PROBLEM_PAGES
from modules.pipeleap_seo_engine.data.pain_points import BEFORE_AFTER
from modules.pipeleap_seo_engine.engines.content_engine import GrowthContentEngine
from modules.pipeleap_seo_engine.models import GrowthPage

# Use-case-specific before/after rows — prevents every use case page from
# showing the same generic comparison table.
USE_CASE_BEFORE_AFTER: dict[str, list[tuple[str, str, str]]] = {
    "saas-pipeline-generation-automation": [
        ("Pipeline source", "Manually built lists from LinkedIn + spreadsheets", "Automated intake from signals, enrichment, and ICP scoring"),
        ("Execution consistency", "Depends on which rep is running it — varies weekly", "Same workflow runs identically every day"),
        ("Scaling pipeline", "Every increase requires more SDR headcount or founder time", "Volume scales through workflow, not headcount"),
        ("Time to first outreach", "2–3 days from signal to first touchpoint", "Minutes — signal triggers workflow automatically"),
        ("Pipeline visibility", "Manual reporting from fragmented tools", "Real-time workflow-level pipeline tracking"),
    ],
    "automate-saas-outbound": [
        ("Outreach volume", "Limited by SDR bandwidth — 30–50 outreaches/day manual maximum", "Automated workflows handle 200+ personalised outreaches/day"),
        ("Personalisation quality", "Generic templates because no time for research", "Enriched data drives automatic personalisation at every touchpoint"),
        ("Follow-up rate", "60%+ of prospects never receive a second touch", "100% follow-up cadence — no prospect falls through"),
        ("Reply routing", "Reps manually monitor inbox and route replies by hand", "Replies auto-classified and routed to the right rep instantly"),
        ("CRM hygiene", "Logging done after calls, often missed or incomplete", "Every touchpoint written to CRM automatically at trigger time"),
    ],
    "saas-workflow-orchestration": [
        ("Tool integration", "Data moves between tools via manual export/import", "Single orchestration layer connects all tools with governed logic"),
        ("Workflow governance", "Each rep makes their own workflow decisions", "Workflow rules enforced centrally — consistent across all reps"),
        ("Execution visibility", "No unified view — 5 dashboards that don't agree", "One workflow view with all execution data in real time"),
        ("Playbook replication", "Best practices stay in top rep's head", "Best practices encoded in automated workflows for everyone"),
        ("Error rate", "Frequent manual errors — wrong sequence, missed data, duplicate sends", "Zero manual execution errors — workflow engine enforces logic"),
    ],
    "signal-based-outbound-automation": [
        ("Prospect timing", "Outreach goes out on a schedule — not when the prospect is ready", "Signal triggers outreach at moment of highest buying intent"),
        ("ICP targeting accuracy", "Static lists go stale — some contacts left, some changed roles", "Real-time signal validation ensures list is always current and relevant"),
        ("Relevance of outreach", "Generic opening — no reference to buying signal", "Every message references the specific signal that triggered it"),
        ("Pipeline quality", "Outbound generates volume but low conversion to meeting", "Signal-qualified prospects convert at 3× the rate of static lists"),
        ("Signal monitoring", "Manual monitoring of intent feeds and website visitors", "Automated signal capture runs 24/7 with no monitoring required"),
    ],
    "outbound-pipeline-without-sdrs": [
        ("Headcount requirement", "Every pipeline increment needs one more SDR", "Workflow automation generates pipeline without SDR headcount"),
        ("Founder time on sales", "4–6 hours/day on outbound admin tasks", "0 hours on manual outbound — system runs autonomously"),
        ("Pipeline at early stage", "Pipeline depends entirely on founder energy", "Automated pipeline system runs regardless of founder availability"),
        ("Cost of pipeline generation", "Fully loaded SDR cost $80K–130K/yr per pipeline tier", "Workflow automation generates equivalent pipeline at fraction of the cost"),
        ("System handoff", "No documented process to hand off to first hire", "Governed workflow system is ready to hand off on day one of first hire"),
    ],
}

# Problem-page-specific before/after rows
PROBLEM_BEFORE_AFTER: dict[str, list[tuple[str, str, str]]] = {
    "why-saas-outbound-fails": [
        ("Root cause", "Treated as a messaging or channel problem — fixed with new templates", "Treated as a systems problem — fixed with workflow orchestration"),
        ("Execution model", "Manual — each rep builds their own process", "Governed — one workflow logic runs across all reps"),
        ("Tooling", "6–8 disconnected point solutions with manual handoffs", "Unified orchestration layer connecting all tools"),
        ("Measurement", "Activity metrics (emails sent, calls made) that don't correlate to pipeline", "Outcome metrics (pipeline created per workflow stage) in real time"),
        ("Scalability", "Can't scale without more headcount or founder time", "Scales through workflow, not people"),
    ],
    "manual-vs-automated-outbound": [
        ("Execution speed", "2–5 days from signal to first outreach", "Minutes — automated from signal detection to sequence enrollment"),
        ("Consistency", "Best practices live in top performers' heads", "Best practices enforced in automated workflows for every rep"),
        ("Error rate", "High — wrong segment, duplicate sends, missed follow-ups", "Zero — workflow engine enforces rules on every execution"),
        ("Capacity ceiling", "Hard ceiling at SDR bandwidth", "No ceiling — volume scales through workflow automation"),
        ("ROI tracking", "Activity tracked, pipeline attribution unclear", "Pipeline attributed to specific workflow, signal, and sequence automatically"),
    ],
}


class UseCasePageGenerator:

    def __init__(self, content_engine: GrowthContentEngine) -> None:
        self.ce = content_engine

    def generate_all(self, existing_slugs: set[str]) -> list[GrowthPage]:
        pages = []
        for uc in USE_CASES:
            if uc["slug"] in existing_slugs:
                continue
            pages.append(self._generate(uc))
            existing_slugs.add(uc["slug"])
        return pages

    def _generate(self, uc: dict[str, Any]) -> GrowthPage:
        slug = uc["slug"]
        page_url = f"{self.ce.site_url}/{slug}"

        snippet = self.ce.featured_snippet_block(
            f"What is {uc['primary_keyword']}?",
            f"{uc['primary_keyword'].capitalize()} means replacing manual outbound execution with "
            f"governed workflow automation — so {uc['outcome']}.",
        )

        hero = self.ce.hero_section(
            headline=uc["h1"],
            hero_stat=uc["outcome"].capitalize() + ".",
            subhead=f"The core pain this page solves: **{uc['pain_focus']}**.",
        )

        problem = self.ce.problem_section(
            pain_points=[uc["pain_focus"], "fragmented tools with no unified workflow layer", "inability to scale without adding headcount"],
        )

        solution = self.ce.solution_section()

        workflow_diagram = (
            f"## How the Workflow Runs\n\n"
            f"```text\n{uc['workflow_example']}\n```\n\n"
            f"Every step is automated — no manual intervention required.\n"
        )

        how_it_works = self.ce.how_it_works_section(slug=slug)
        # Inject use-case-specific before/after so each page has a distinct table
        uc_ba_rows = USE_CASE_BEFORE_AFTER.get(slug)
        before_after = self.ce.before_after_section(custom_rows=uc_ba_rows)

        # Audience section tailored to the use case's pain_focus
        use_cases_section = (
            f"## Who Needs {uc['primary_keyword'].title()}\n\n"
            f"This workflow is designed for SaaS organizations where **{uc['pain_focus']}** "
            f"is the primary bottleneck. Specifically:\n\n"
            "- **SaaS Founders (0–1M ARR):** Building pipeline before the first SDR hire\n"
            "- **VP Sales (1–10M ARR):** Scaling consistent pipeline without proportional headcount\n"
            "- **CROs (10M+ ARR):** Replacing fragmented execution with governed workflow orchestration\n"
            "- **RevOps teams:** Replacing 6+ point solutions with one unified execution layer\n"
        )

        positioning = self.ce.positioning_callout()

        faq_pairs = [
            (f"What does '{uc['primary_keyword']}' mean for a SaaS company?",
             f"It means running {uc['primary_keyword']} through governed workflow automation — so {uc['outcome']} without manual intervention."),
            ("How is Pipeleap different from a sales engagement tool?",
             "Sales engagement tools manage sequences. Pipeleap orchestrates the full workflow — signal capture, enrichment, sequencing, CRM routing, and reply handling — automatically."),
            ("Can Pipeleap integrate with our existing CRM and tools?",
             "Yes. Pipeleap sits above your existing stack and writes enriched, structured data back to your CRM on every workflow trigger. It complements your tools rather than replacing them all."),
            ("How quickly can we implement this workflow?",
             "Most teams have their first automated workflow running within a week. Pipeleap is designed for rapid iteration — not months-long implementation projects."),
        ]
        faq = self.ce.faq_section(faq_pairs)
        cta = self.ce.cta_section(urgency=f"Start automating {uc['primary_keyword']} today.")

        stats = self.ce.statistics_section()
        from modules.pipeleap_seo_engine.data.authors import get_author_for_page_type
        author = get_author_for_page_type("use_case_page")
        author_byline = self.ce.author_byline(author)
        body = "\n".join([snippet, author_byline, hero, stats, problem, solution, workflow_diagram, how_it_works, before_after, use_cases_section, positioning, faq, cta])
        schema = [
            self.ce.webpage_schema(uc["page_title"], uc["meta_description"], page_url),
            self.ce.howto_schema(uc["h1"], uc["meta_description"], page_url),
            self.ce.breadcrumb_schema([("Home", self.ce.site_url), ("Use Cases", f"{self.ce.site_url}/use-cases"), (uc["h1"], page_url)]),
            *self.ce.faq_schema(faq_pairs, page_url),
        ]

        return GrowthPage(
            slug=slug,
            page_type="use_case_page",
            title=uc["page_title"],
            seo_title=uc["page_title"],
            meta_description=uc["meta_description"],
            canonical_url=page_url,
            og_meta=self.ce.og_meta(uc["page_title"], uc["meta_description"], page_url),
            twitter_meta=self.ce.twitter_meta(uc["page_title"], uc["meta_description"]),
            h1=uc["h1"],
            body_markdown=body,
            schema_markup=schema,
            call_to_action=self.ce.cta_section(slug=slug, campaign="use_case"),
            primary_keyword=uc["primary_keyword"],
            target_keywords=uc["keywords"],
            internal_links=[],
            author_name=author["name"], author_slug=author["slug"],
            breadcrumbs=[("Home", self.ce.site_url), ("Use Cases", f"{self.ce.site_url}/use-cases"), (uc["h1"], page_url)],
            use_case=uc["slug"],
            industry="SaaS",
            pain_points=[uc["pain_focus"]],
            intent="transactional",
            topical_pillar="outbound-automation",
        )


class ProblemPageGenerator:

    def __init__(self, content_engine: GrowthContentEngine) -> None:
        self.ce = content_engine

    def generate_all(self, existing_slugs: set[str]) -> list[GrowthPage]:
        pages = []
        for pp in PROBLEM_PAGES:
            if pp["slug"] in existing_slugs:
                continue
            pages.append(self._generate(pp))
            existing_slugs.add(pp["slug"])
        return pages

    def _generate(self, pp: dict[str, Any]) -> GrowthPage:
        slug = pp["slug"]
        page_url = f"{self.ce.site_url}/{slug}"

        snippet = self.ce.featured_snippet_block(
            pp["h1"] + "?",
            f"SaaS outbound fails because of manual execution, fragmented tools, and no repeatable workflow system. "
            f"The fix is workflow orchestration — automating signal capture, enrichment, sequencing, and routing in one governed engine.",
        )

        hero = self.ce.hero_section(
            headline=pp["h1"],
            hero_stat="Most SaaS outbound problems share one root cause: no governed workflow orchestration.",
        )

        if pp["slug"] == "why-saas-outbound-fails" and pp.get("reasons"):
            reasons_md = "## The 5 Real Reasons SaaS Outbound Fails\n\n"
            for reason in pp["reasons"]:
                reasons_md += f"### {reason['title']}\n\n{reason['description']}\n\n"
        else:
            reasons_md = self.ce.problem_section(
                pain_points=[
                    "manual execution that doesn't scale",
                    "fragmented tools with no unified workflow layer",
                    "no repeatable playbooks for consistent pipeline",
                    "over-reliance on individual rep performance",
                    "zero visibility into underperforming workflow stages",
                ],
            )

        solution = self.ce.solution_section()
        how_it_works = self.ce.how_it_works_section(slug=slug)
        pp_ba_rows = PROBLEM_BEFORE_AFTER.get(slug)
        before_after = self.ce.before_after_section(custom_rows=pp_ba_rows)
        positioning = self.ce.positioning_callout()

        faq_pairs = [
            ("Why does SaaS outbound consistently underperform?",
             "Because it's built on manual execution and fragmented tools. Without a governed workflow orchestration layer, outbound can't scale, can't be replicated, and can't be measured accurately."),
            ("What's the fastest way to fix SaaS outbound?",
             "Implement workflow orchestration — automate signal capture, enrichment, sequencing, and CRM routing in one system. Pipeleap can have your first automated workflow running within a week."),
            ("Is the problem SDRs or systems?",
             "Usually systems. When outbound is governed by automated workflows, average performers execute like top performers. The bottleneck is almost always the system, not the people."),
            ("How do I measure if outbound is improving?",
             "Track pipeline velocity at each workflow stage — signal to qualification, qualification to sequence, sequence to reply, reply to meeting. Pipeleap gives you this visibility automatically."),
        ]
        faq = self.ce.faq_section(faq_pairs)
        cta = self.ce.cta_section(urgency="Fix your outbound execution with workflow orchestration.")

        from modules.pipeleap_seo_engine.data.authors import get_author_for_page_type
        author = get_author_for_page_type("problem_page")
        stats = self.ce.statistics_section()
        body = "\n".join([snippet, self.ce.author_byline(author), hero, stats, reasons_md, solution, how_it_works, before_after, positioning, faq, cta])
        schema = [
            self.ce.webpage_schema(pp["page_title"], pp["meta_description"], page_url),
            self.ce.breadcrumb_schema([("Home", self.ce.site_url), ("Resources", f"{self.ce.site_url}/resources"), (pp["h1"], page_url)]),
            *self.ce.faq_schema(faq_pairs, page_url),
        ]

        return GrowthPage(
            slug=slug,
            page_type="problem_page",
            title=pp["page_title"],
            seo_title=pp["page_title"],
            meta_description=pp["meta_description"],
            canonical_url=page_url,
            og_meta=self.ce.og_meta(pp["page_title"], pp["meta_description"], page_url),
            twitter_meta=self.ce.twitter_meta(pp["page_title"], pp["meta_description"]),
            h1=pp["h1"],
            body_markdown=body,
            schema_markup=schema,
            call_to_action=self.ce.cta_section(slug=slug, campaign="problem_page"),
            primary_keyword=pp["primary_keyword"],
            target_keywords=pp["keywords"],
            internal_links=[],
            author_name=author["name"], author_slug=author["slug"],
            breadcrumbs=[("Home", self.ce.site_url), ("Resources", f"{self.ce.site_url}/resources"), (pp["h1"], page_url)],
            industry="SaaS",
            intent="informational",
            topical_pillar="outbound-automation",
        )
