"""
Content engine for the Pipeleap SaaS Growth Engine.
Provides the 8-section template and rendering utilities.
Target: 1,800–2,500 words per page minimum.
"""
from __future__ import annotations

from typing import Any

import random

from modules.pipeleap_seo_engine.data.pain_points import (
    POSITIONING, HOW_IT_WORKS, BEFORE_AFTER, USE_CASE_EXAMPLES,
)

# UTM template — injected on every CTA link
_UTM = "utm_source=organic&utm_medium=seo&utm_campaign={campaign}&utm_content={slug}"


class GrowthContentEngine:
    """Renders all page sections using the expanded 8-section template (1800+ words)."""

    def __init__(self, site_config: dict[str, Any]) -> None:
        self.site_url = site_config.get("site_url", "https://pipeleap.com").rstrip("/")
        self.brand = site_config.get("brand", "Pipeleap")
        self.cta = site_config.get("cta", {})
        self.primary_cta_label = self.cta.get("primary_label", "Book a demo")
        self.primary_cta_url = self.cta.get("primary_url", self.site_url)
        self.secondary_cta_label = self.cta.get("secondary_label", "See how it works")
        self.secondary_cta_url = self.cta.get("secondary_url", self.site_url)

    # ─── UTM helpers ──────────────────────────────────────────────────────────

    def _utm_url(self, base_url: str, campaign: str, slug: str) -> str:
        utm = _UTM.format(campaign=campaign.replace(" ", "_"), slug=slug.replace("-", "_"))
        sep = "&" if "?" in base_url else "?"
        return f"{base_url}{sep}{utm}"

    def _cta_url(self, slug: str, campaign: str = "role_page") -> str:
        return self._utm_url(self.primary_cta_url, campaign, slug)

    def _secondary_url(self, slug: str, campaign: str = "role_page") -> str:
        return self._utm_url(self.secondary_cta_url, campaign, slug)

    # ─── Section 1: Hero ──────────────────────────────────────────────────────

    def hero_section(self, headline: str, hero_stat: str, subhead: str = "",
                     cta_label: str = "", slug: str = "", campaign: str = "hero") -> str:
        cta = cta_label or self.primary_cta_label
        cta_url = self._cta_url(slug, campaign)
        sec_url = self._secondary_url(slug, campaign)
        lines = [
            f"# {headline}",
            "",
            f"> **{hero_stat}**",
            "",
        ]
        if subhead:
            lines += [subhead, ""]
        lines += [
            f"[{cta}]({cta_url}) or [{self.secondary_cta_label}]({sec_url}) to start building immediately.",
            "",
        ]
        return "\n".join(lines)

    # ─── Section 2: Problem ───────────────────────────────────────────────────

    def problem_section(self, pain_points: list[str], context: str = "") -> str:
        intros = [
            "SaaS sales execution consistently underperforms because it is built on manual data work, fragmented tools, and no repeatable system.",
            "The biggest bottleneck in modern SaaS pipeline generation isn't a lack of tools—it's a lack of orchestration.",
            "Why do so many sales campaigns fail to generate consistent meetings? The answer usually lies in fragmented operations.",
            "Revenue teams are often trapped in a cycle of manual research and disjointed tools, preventing scalable pipeline growth.",
            "In the race for market share, the bottleneck is rarely the quantity of leads, but the quality of the orchestration layer.",
            "Modern sales teams need more than just tools; they need a governed system that connects signals to sequences automatically.",
            "Fragmented sales operations is the 'silent killer' of predictable revenue in B2B SaaS organizations.",
            "When every SDR runs their own process, scaling becomes a management nightmare rather than a growth lever.",
            "The transition from manual operations to orchestrated workflows is the hallmark of high-performance revenue teams.",
            "Most SaaS companies are sitting on a goldmine of intent signals but lack the engine to turn them into meetings.",
        ]
        intro = context or random.choice(intros)
        lines = [
            "## The Problem",
            "",
            intro,
            "",
        ]
        pain_explanations = {
            "unpredictable pipeline generation quarter over quarter": (
                "**Unpredictable pipeline** is the most costly symptom. When pipeline generation depends on "
                "individual rep effort rather than governed workflows, results vary wildly between quarters. "
                "One strong quarter masks the structural problem until a top rep leaves or headcount lags demand."
            ),
            "heavy reliance on manual data work": (
                "**Manual data work** creates a ceiling. Every additional unit of pipeline requires "
                "proportional manual effort — research, writing, sending, following up, logging. "
                "This ceiling appears early and cannot be broken without automation."
            ),
            "fragmented tools with no unified workflow execution layer": (
                "**Fragmented tooling** is the root cause most teams misdiagnose. The average SaaS sales stack "
                "runs across 6–8 disconnected tools. Data moves between them manually, errors compound at each "
                "handoff, and RevOps spends more time maintaining integrations than building strategy."
            ),
            "lack of workflow orchestration across revenue operations": (
                "**No orchestration layer** means every revenue motion is a one-off project. "
                "There is no system that governs signal intake, enrichment logic, sequencing rules, "
                "CRM routing, and performance feedback in a single, repeatable execution model."
            ),
            "inconsistent execution across sales teams and territories": (
                "**Inconsistent execution** is a people problem that looks like a people problem but is actually "
                "a systems problem. When the best sales process lives in one rep's head, it cannot be "
                "replicated. Every rep reinvents the wheel. Every territory runs a slightly different play."
            ),
            "poor visibility into workflow performance": (
                "**Poor visibility** prevents improvement. Teams cannot fix what they cannot measure. "
                "Without workflow-level performance data — which stages convert, which sequences perform, "
                "which segments respond — revenue teams optimize based on gut feel and activity metrics "
                "that don't correlate to pipeline."
            ),
            "inability to scale without proportional headcount growth": (
                "**The headcount trap** is the most expensive consequence of unorchestrated operations. "
                "Every pipeline target increase triggers a headcount request. Without automation, "
                "the only lever is more people — more cost, more ramp time, more management overhead."
            ),
        }
        for pain in pain_points:
            explanation = pain_explanations.get(pain)
            if explanation:
                lines += [explanation, ""]
            else:
                lines += [f"**{pain.capitalize()}** is a critical execution barrier that workflow orchestration directly eliminates.", ""]
        return "\n".join(lines)

    # ─── Section 3: Solution ─────────────────────────────────────────────────

    def solution_section(self, role_context: str = "") -> str:
        is_not_list = " or ".join(f"**{x}**" for x in POSITIONING["is_not"])
        does_list = "\n".join(f"- {d}" for d in POSITIONING["does"])
        lines = [
            "## The Solution: Workflow Orchestration",
            "",
            f"{self.brand} is {POSITIONING['is']}.",
            "",
            f"It is not {is_not_list}. This distinction is important: Pipeleap does not replace your CRM, "
            f"your sequencer, or your enrichment tool. It sits above them — orchestrating how they work together "
            f"into one governed, automated, end-to-end revenue execution system.",
            "",
            f"Specifically, {self.brand}:",
            "",
            does_list,
            "",
            (
                f"The result is a repeatable pipeline system that runs without manual intervention. "
                f"Signals are captured automatically. Prospects are enriched and qualified without research time. "
                f"Sequences fire without manual enrollment. CRM data stays clean without manual updates. "
                f"Replies are routed without inbox management. Meetings get booked without scheduling overhead."
            ),
            "",
        ]
        if role_context:
            lines += [role_context, ""]
        return "\n".join(lines)

    # ─── Section 4: How It Works ──────────────────────────────────────────────

    def how_it_works_section(self, slug: str = "") -> str:
        lines = [
            "## How Pipeleap Works",
            "",
            (
                "The Pipeleap workflow engine runs a five-stage orchestration model. "
                "Each stage is automated, connected to the next, and produces structured output "
                "that feeds into the stage that follows. There are no manual handoffs, no data gaps, "
                "and no steps that depend on individual rep effort."
            ),
            "",
            "```text",
            "Signal Capture → Enrichment & Qualification → Sequence Execution → Reply Routing → Performance Loop",
            "```",
            "",
        ]
        step_expansions = {
            1: (
                "When a prospect visits your pricing page, opens a specific email, matches an ICP filter, "
                "appears in an intent data feed, or triggers any configurable signal condition, Pipeleap "
                "captures that event and enters it into the workflow queue. Signal sources can include "
                "website visitor data, third-party intent platforms, CRM field changes, form submissions, "
                "list imports, or API triggers from any connected tool."
            ),
            2: (
                "Every signal-qualified prospect is automatically enriched before any outreach step fires. "
                "Pipeleap pulls company data, contact information, technographic signals, and firmographic "
                "context from configured enrichment sources — then scores the prospect against your ICP "
                "criteria. Only prospects that pass qualification thresholds enter the sequence stage. "
                "Enrichment happens in real time, at intake, without any SDR research time."
            ),
            3: (
                "Qualified prospects are entered into the appropriate workflow sequence automatically "
                "based on their segment, intent signal, industry, or role. Pipeleap handles multi-step, "
                "multi-channel sequences — email, LinkedIn, phone task creation — with full personalization "
                "using the enriched data collected in step two. Sequence selection, timing, and suppression "
                "logic are all governed by the workflow engine, not by individual rep decisions."
            ),
            4: (
                "Replies are classified automatically — interested, not interested, out of office, referral. "
                "Interested replies are routed to the correct rep or territory owner immediately, with context. "
                "Meeting links can be included in the sequence for direct booking. The workflow engine handles "
                "all routing logic, ensuring no reply goes unactioned and no meeting opportunity falls through "
                "a manual handoff gap."
            ),
            5: (
                "Every workflow stage produces structured performance data: which signals converted, "
                "which enrichment sources performed, which sequences generated replies, which routing paths "
                "produced meetings. This data feeds back into the workflow engine to improve future runs. "
                "Over time, the system learns which combinations of signal, enrichment, and sequencing "
                "produce the highest pipeline conversion — and weights future execution accordingly."
            ),
        }
        for step in HOW_IT_WORKS:
            expansion = step_expansions.get(step["step"], "")
            variant = random.choice(step.get("variants", [""]))
            lines += [
                f"### Step {step['step']}: {step['title']}",
                "",
                step["body"],
                "",
                variant,
                "",
                expansion,
                "",
            ]
        return "\n".join(lines)

    # ─── Section 5: Before vs After ───────────────────────────────────────────

    def before_after_section(self, custom_rows: list[tuple[str, str, str]] | None = None) -> str:
        rows = custom_rows or BEFORE_AFTER
        lines = [
            "## Before Pipeleap vs. With Pipeleap",
            "",
            (
                "The difference between manual execution and orchestrated execution is not incremental — "
                "it is structural. The table below shows how the same revenue motion looks before "
                "workflow orchestration and after it. Every row represents a category where manual "
                "execution creates a bottleneck, and where automation eliminates it."
            ),
            "",
            "| Dimension | Before Pipeleap | With Pipeleap |",
            "| --- | --- | --- |",
        ]
        for dimension, before, after in rows:
            lines.append(f"| {dimension} | {before} | {after} |")
        lines += [
            "",
            (
                "The compounding effect of these improvements is what produces predictable pipeline. "
                "When every dimension of revenue execution is governed by automated workflows, "
                "the system performs consistently regardless of which rep runs it, which territory "
                "it runs in, or how many prospects it runs against."
            ),
            "",
        ]
        return "\n".join(lines)

    # ─── Section 6: Use Cases ─────────────────────────────────────────────────

    def use_cases_section(self, custom_cases: list[dict] | None = None) -> str:
        cases = custom_cases or USE_CASE_EXAMPLES
        lines = [
            "## Real-World Use Cases",
            "",
            (
                "Workflow orchestration is not a theoretical concept — it is a practical execution model "
                "that SaaS teams at every stage deploy to build predictable pipeline. The following "
                "examples show how different types of SaaS organizations use Pipeleap."
            ),
            "",
        ]
        for case in cases:
            lines += [
                f"### {case['title']}",
                "",
                case["description"],
                "",
                (
                    f"The workflow in this scenario: signal detection identifies the right prospect "
                    f"at the right time, enrichment populates the contact record automatically, "
                    f"the sequence fires with full personalization, and the reply is routed to the "
                    f"appropriate person without manual monitoring."
                ),
                "",
                f"**Outcome:** {case['outcome']}",
                "",
            ]
        return "\n".join(lines)

    # ─── Section 7: FAQ ───────────────────────────────────────────────────────

    def faq_section(self, qa_pairs: list[tuple[str, str]]) -> str:
        lines = [
            "## Frequently Asked Questions",
            "",
            (
                "The following questions come from SaaS revenue leaders who have evaluated "
                "Pipeleap alongside point solutions and broader platforms. "
                "They reflect the most common decision-stage concerns."
            ),
            "",
        ]
        for question, answer in qa_pairs:
            lines += [f"### {question}", "", answer, ""]
        return "\n".join(lines)

    # ─── Section 8: Stage-aware CTA ───────────────────────────────────────────
    # CTA copy is governed by funnel stage — no hard-sell "Start free trial" on
    # TOFU/informational pages. Stage is passed in; defaults to MOFU if unknown.

    def cta_section(self, label: str = "", urgency: str = "",
                    slug: str = "", campaign: str = "cta",
                    funnel_stage: str = "MOFU", page_type: str = "") -> str:
        from modules.pipeleap_seo_engine.data.funnel_stages import FUNNEL_STAGES, stage_for

        stage = stage_for(page_type) if page_type else funnel_stage
        stage_config = FUNNEL_STAGES.get(stage, FUNNEL_STAGES["MOFU"])

        cta_label = label or stage_config["cta_primary"]
        cta_url_base = stage_config["cta_url_primary"]
        sec_label = stage_config["cta_secondary"]
        sec_url_base = stage_config["cta_url_secondary"]
        urgency_text = urgency or stage_config.get("cta_urgency", "")

        # Strict user constraint: No hard-sell CTAs on informational pages/blogs
        bad_ctas = ["book a demo", "free trial", "start free trial", "get a demo"]
        if stage in ("TOFU", "MOFU") or page_type in ("blog_post", "glossary_page"):
            if cta_label.lower() in bad_ctas:
                cta_label = "See how Pipeleap works"

        utm = f"utm_source=organic&utm_medium=seo&utm_campaign={campaign}&utm_content={slug}"
        cta_url = f"{cta_url_base}?{utm}" if "?" not in cta_url_base else f"{cta_url_base}&{utm}"
        sec_url = f"{sec_url_base}?{utm}_sec" if "?" not in sec_url_base else f"{sec_url_base}&{utm}_sec"

        # Stage-specific section copy
        section_bodies = {
            "TOFU": (
                "Understanding the problem is the first step. When you're ready to see how "
                "workflow orchestration eliminates it for your specific team and stack, "
                "the resources below show it in practice."
            ),
            "MOFU": (
                "Most teams have the right instinct about automation but lack the workflow "
                "architecture to make it consistent. Pipeleap provides the orchestration layer "
                "that governs your entire revenue motion end-to-end."
            ),
            "BOFU": (
                "Every week that revenue runs on manual execution is a week of compounding "
                "pipeline inefficiency. The GTM audit maps exactly where your workflow breaks "
                "down and delivers a custom automation blueprint — within 48 hours."
            ),
            "SQL": (
                "You know what you want to build. The demo shows it running live — "
                "your exact use case, your stack, your workflow."
            ),
        }

        body = section_bodies.get(stage, section_bodies["MOFU"])

        lines = [
            "## Next Step",
            "",
            body,
            "",
            f"[{cta_label}]({cta_url})",
            "",
            f"Or [{sec_label}]({sec_url}) to discuss your use case first.",
            "",
        ]
        if urgency_text:
            lines += [f"_{urgency_text}_", ""]
        return "\n".join(lines)

    # ─── PAA block (People Also Ask) ─────────────────────────────────────────

    def paa_section(self, topic: str = "workflow_orchestration", limit: int = 4) -> str:
        """
        Generates a People Also Ask section targeting common PAA questions for this topic.
        Placed near the bottom of the page, before the CTA section.
        Structured for Google's PAA extraction: H3 question + short answer paragraph.
        """
        from modules.pipeleap_seo_engine.data.funnel_stages import paa_questions_for

        questions = paa_questions_for(topic, limit=limit)
        if not questions:
            return ""

        topic_display = topic.replace("_", " ").title()
        lines = [
            "## People Also Ask",
            "",
            f"_Common questions from SaaS teams researching {topic_display}:_",
            "",
        ]

        answers = {
            "What is sales workflow orchestration?": (
                "Sales workflow orchestration uses governed automation to handle the non-selling work that "
                "drains revenue teams — prospect research, enrichment, email sequences, follow-ups, and CRM logging — "
                "so sellers spend their time on conversations, not clicks."
            ),
            "How do you automate B2B sales emails?": (
                "B2B sales email automation requires: (1) a signal trigger to identify the right "
                "prospect at the right time, (2) automated enrichment to personalise the message, "
                "(3) a governed workflow that fires automatically, and (4) reply classification to "
                "route interested responses without manual inbox monitoring."
            ),
            "What is signal-based outreach?": (
                "Signal-based outreach triggers prospecting and sequencing from real-time buying signals "
                "— website visits, intent data, job changes, funding events — rather than static lists. "
                "It ensures outreach reaches the right account at the moment of highest intent."
            ),
            "What is predictable pipeline generation?": (
                "Predictable pipeline generation is a systematic model where pipeline output "
                "is governed by automated workflows rather than individual rep effort. The same workflow "
                "runs consistently every day, producing stable pipeline regardless of which rep manages it."
            ),
            "What is workflow orchestration in sales?": (
                "Sales workflow orchestration is the practice of governing how multiple sales tools and "
                "execution steps work together as a single automated system — from signal capture through "
                "enrichment, sequencing, reply routing, and CRM sync — rather than running them in isolation."
            ),
            "How does Pipeleap compare to Clay?": (
                "Clay is a data enrichment and waterfall tool. Pipeleap is a workflow orchestration system "
                "that governs the full revenue pipeline — including Clay as an enrichment data source. "
                "Clay enriches contacts; Pipeleap governs when, how, and to whom that enriched data flows."
            ),
        }

        for q in questions:
            answer = answers.get(q, (
                f"See Pipeleap's full guide on [workflow orchestration](https://pipeleap.com/blog) "
                f"for a detailed answer to this question with workflow examples."
            ))
            lines += [f"### {q}", "", answer, ""]

        return "\n".join(lines)

    # ─── Schema markup ────────────────────────────────────────────────────────

    def webpage_schema(self, title: str, description: str, page_url: str,
                       page_type: str = "WebPage") -> dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": page_type,
            "@id": f"{page_url}#webpage",
            "name": title,
            "description": description,
            "url": page_url,
            "isPartOf": {"@type": "WebSite", "@id": f"{self.site_url}/#website", "url": self.site_url, "name": self.brand},
            "publisher": {"@type": "Organization", "@id": f"{self.site_url}/#organization", "name": self.brand, "url": self.site_url},
        }

    def article_schema(self, title: str, description: str, page_url: str,
                       author_name: str = "", author_url: str = "") -> dict[str, Any]:
        schema: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "url": page_url,
            "publisher": {"@type": "Organization", "@id": f"{self.site_url}/#organization", "name": self.brand, "url": self.site_url},
        }
        if author_name:
            schema["author"] = {"@type": "Person", "name": author_name, "url": author_url or self.site_url}
        return schema

    def howto_schema(self, name: str, description: str, page_url: str) -> dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": name,
            "description": description,
            "url": page_url,
            "step": [
                {
                    "@type": "HowToStep",
                    "position": step["step"],
                    "name": step["title"],
                    "text": step["body"],
                }
                for step in HOW_IT_WORKS
            ],
        }

    def breadcrumb_schema(self, crumbs: list[tuple[str, str]]) -> dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "name": name,
                    "item": url,
                }
                for i, (name, url) in enumerate(crumbs)
            ],
        }

    def software_application_schema(self) -> dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "@id": f"{self.site_url}/#software",
            "name": self.brand,
            "applicationCategory": "BusinessApplication",
            "operatingSystem": "Web",
            "url": self.site_url,
            "description": POSITIONING["is"],
            "offers": {"@type": "Offer", "priceCurrency": "USD", "url": f"{self.site_url}/pricing"},
            "featureList": POSITIONING["does"],
        }

    def organization_schema(self) -> dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": f"{self.site_url}/#organization",
            "name": self.brand,
            "url": self.site_url,
            "description": POSITIONING["is"],
            "knowsAbout": [
                "Outbound Sales Automation",
                "Workflow Orchestration",
                "SaaS Pipeline Generation",
                "Revenue Operations Automation",
                "Signal-Based Outbound",
            ],
            "sameAs": [
                "https://www.linkedin.com/company/pipeleap",
                "https://www.g2.com/products/pipeleap",
                "https://www.producthunt.com/products/pipeleap",
            ],
        }

    def person_schema(self, author: dict[str, Any]) -> dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": "Person",
            "@id": f"{self.site_url}/team/{author.get('slug', '')}#person",
            "name": author.get("name", ""),
            "url": f"{self.site_url}/team/{author.get('slug', '')}",
            "jobTitle": author.get("title", ""),
            "description": author.get("bio", ""),
            "knowsAbout": author.get("expertise", []),
            "sameAs": author.get("social_urls", []),
        }

    def faq_schema(self, qa_pairs: list[tuple[str, str]], page_url: str) -> list[dict[str, Any]]:
        return [
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "url": page_url,
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in qa_pairs
                ],
            }
        ]

    def item_list_schema(self, items: list[dict[str, str]], list_name: str, page_url: str) -> dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": list_name,
            "url": page_url,
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": item.get("name", ""), "url": item.get("url", "")}
                for i, item in enumerate(items)
            ],
        }

    # ─── OG + Twitter card meta ───────────────────────────────────────────────

    def og_meta(self, title: str, description: str, page_url: str,
                og_type: str = "article") -> dict[str, str]:
        return {
            "og:type": og_type,
            "og:title": title[:95],
            "og:description": description[:200],
            "og:url": page_url,
            "og:site_name": self.brand,
            "og:image": f"{self.site_url}/og-image.png",
            "og:image:width": "1200",
            "og:image:height": "630",
        }

    def twitter_meta(self, title: str, description: str) -> dict[str, str]:
        return {
            "twitter:card": "summary_large_image",
            "twitter:title": title[:70],
            "twitter:description": description[:200],
            "twitter:image": f"{self.site_url}/og-image.png",
        }

    # ─── Author byline ────────────────────────────────────────────────────────

    def author_byline(self, author: dict) -> str:
        name = author.get("name", "Pipeleap Team")
        title = author.get("title", "")
        slug = author.get("slug", "")
        url = f"{self.site_url}/team/{slug}" if slug else self.site_url
        byline = f"*By [{name}]({url})*"
        if title:
            byline += f" — {title}"
        return byline

    # ─── AI Overview / Featured Snippet block ────────────────────────────────

    def ai_answer_block(self, question: str, answer: str, entity: str = "") -> str:
        """
        Structured 50-60 word direct answer block.
        Formatted for AI Overview citation and featured snippet capture.
        Placed at the top of each page, before the H1.
        """
        entity_ref = f" As a {entity}," if entity else ""
        return (
            f"**{question}**\n\n"
            f"{answer.rstrip('.')}.{entity_ref}\n"
        )

    def featured_snippet_block(self, question: str, answer: str) -> str:
        return self.ai_answer_block(question, answer)

    # ─── Positioning guard ────────────────────────────────────────────────────

    def positioning_callout(self) -> str:
        is_not = " or ".join(POSITIONING["is_not"])
        return (
            f"> **What Pipeleap is not:** {is_not}. "
            f"{self.brand} is {POSITIONING['is']} — "
            f"the operational layer that governs your revenue execution end-to-end.\n"
        )

    def statistics_section(self, stats: list[dict[str, str]] | None = None) -> str:
        default_stats = [
            {"stat": "65%", "context": "of SDR time is spent on manual tasks that workflow automation eliminates"},
            {"stat": "3×", "context": "more pipeline generated by SaaS teams using workflow orchestration vs. manual execution"},
            {"stat": "82%", "context": "of B2B buyers accept meetings from well-timed, personalized outreach"},
            {"stat": "6–8", "context": "disconnected tools in the average SaaS sales stack — all replaceable by one operational layer"},
            {"stat": "40%", "context": "increase in reply rates when outreach is triggered by real-time intent signals"},
            {"stat": "2.5x", "context": "faster ramp time for new SDRs when using governed workflow playbooks"},
        ]
        data = random.sample(stats or default_stats, min(len(stats or default_stats), 4))
        lines = ["## The Numbers Behind the Problem", ""]
        for item in data:
            lines += [f"- **{item['stat']}** — {item['context']}"]
        lines.append("")
        return "\n".join(lines)

    # ─── Quality & Brand Protection ───────────────────────────────────────────
    def apply_quality_filters(self, content: str) -> str:
        """
        Final pass to remove broken sentences, filler, and negative positioning.
        Also enforces the 'One internal link + Glossary for definitions' rule.
        """
        # 1. Remove common 'AI filler' phrases
        filler_phrases = [
            "In conclusion,", "At the end of the day,", "It's important to note that",
            "This ensures that", "By doing this,", "Furthermore,", "Moreover,"
        ]
        for phrase in filler_phrases:
            content = content.replace(phrase, "")

        # 2. Prevent negative brand positioning
        negative_patterns = {
            "Pipeleap might": "Pipeleap does",
            "Pipeleap could": "Pipeleap will",
            "Pipeleap tries to": "Pipeleap focuses on",
            "maybe Pipeleap": "Pipeleap",
            "if Pipeleap works": "when Pipeleap runs",
            "broken outbound": "governed execution",
            "failing pipeline": "underperforming pipeline",
            "weak brand": "brand identity",
        }
        for pattern, replacement in negative_patterns.items():
            content = content.replace(pattern, replacement)

        # 3. Link enforcement: Max 1 internal /blog/ link, others must be glossary
        content = self._strip_excessive_links(content)

        # 4. Structural cleanup
        import re
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = "\n".join(line.strip() for line in content.split("\n"))

        return content

    def _strip_excessive_links(self, content: str) -> str:
        """
        Regex-based pass to enforce:
        - Only one primary internal link (to /blog/ or /role/ or /use-case/)
        - Definitions must link only to the Glossary
        - Strip everything else back to plain text
        """
        import re
        # Find all markdown links [text](url)
        all_links = list(re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", content))
        
        has_primary_link = False
        glossary_count = 0
        
        # Sort matches backwards to replace without shifting offsets
        for match in reversed(all_links):
            text = match.group(1)
            url = match.group(2)
            
            # 1. Always keep conversion links (audit, demo, pipeleap.com root)
            if "gtm-audit" in url or url.endswith("pipeleap.com") or url.endswith("pipeleap.com/"):
                continue
                
            # 2. Keep up to 3 glossary links
            if "/glossary" in url:
                if glossary_count < 3:
                    glossary_count += 1
                    continue
                else:
                    # Strip excessive glossary links
                    content = content[:match.start()] + text + content[match.end():]
                    continue

            # 3. Handle internal links (/blog/, /role/, etc)
            if "/blog/" in url or any(x in url for x in ["/role/", "/use-case/", "/comparison/"]):
                if not has_primary_link:
                    # Keep the FIRST (last in reversed) internal link as the 'meaningful' one
                    # Wait, if I'm reversed, the 'first' in the text is the 'last' in the list
                    pass 
                else:
                    # Strip all other internal links
                    content = content[:match.start()] + text + content[match.end():]
                    continue

        # Second pass to ensure only the FIRST internal link is kept
        # Re-run findall since content has changed
        internal_links = list(re.finditer(r"\[([^\]]+)\]\(([^)]*\/blog\/[^)]*|[^)]*\/role\/[^)]*|[^)]*\/use-case\/[^)]*)\)", content))
        if len(internal_links) > 1:
            for match in reversed(internal_links[1:]): # Keep index 0
                text = match.group(1)
                content = content[:match.start()] + text + content[match.end():]

        return content
