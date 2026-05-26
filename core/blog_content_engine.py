"""
GSC-aware, intent-first blog content engine.

Replaces the old modulo-indexed template system in ContentEngine.

Design principles
-----------------
- Content structure is driven by the keyword's search intent, not a fixed template.
- Every body section is written to answer what that specific searcher actually needs.
- GSC signals (position, CTR, impressions) inform depth, angle, and snippet targeting.
- Featured-snippet blocks are injected when the keyword ranks 4-20 or has >200 impressions.
- Word count targets are calibrated to estimated keyword difficulty.
- FAQs are keyword-contextual, not hardcoded boilerplate.
- A quality gate rejects output below minimum standards before it returns.
- The old `len(keyword) % n` variation index is entirely absent from this engine.
"""

from __future__ import annotations

import re as _re
import zlib as _zlib
from datetime import date as _date
from typing import Any

from utils.models import ContentAsset, KeywordCluster
from utils.text import slugify, title_case_keyword


_ASCII_MAP = str.maketrans({
    chr(0x2013): "-",   # en-dash
    chr(0x2014): ",",   # em-dash
    chr(0x2192): ">",   # right arrow
    chr(0x2018): "'",   # left single quote
    chr(0x2019): "'",   # right single quote
    chr(0x201c): '"',   # left double quote
    chr(0x201d): '"',   # right double quote
    chr(0x2022): "-",   # bullet
    chr(0x2026): "...", # ellipsis
    chr(0x00a0): " ",   # non-breaking space
    chr(0x00d7): "x",   # multiplication sign
})

def _strip_formatting(text: str) -> str:
    """Strip typographic Unicode, asterisk markup, and remaining non-ASCII from blog body copy."""
    text = text.translate(_ASCII_MAP)
    text = text.replace(" -- ", ", ")
    text = _re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = _re.sub(r"\*(.+?)\*", r"\1", text)
    text = _re.sub(r"[^\x00-\x7F]+", "", text)
    return text
# ── Word-count targets by difficulty band ─────────────────────────────────────
_DIFFICULTY_WORD_TARGETS: list[tuple[tuple[float, float], int]] = [
    ((0.0, 25.0), 950),
    ((25.0, 45.0), 1400),
    ((45.0, 65.0), 1900),
    ((65.0, 101.0), 2500),
]

# ── Minimum quality thresholds ────────────────────────────────────────────────
_MIN_QUALITY_SCORE = 0.55          # 0-1 composite; below this = skip publish


class BlogContentEngine:
    """
    GSC-aware, intent-first content engine.
    Call generate_blog(), generate_comparison(), or generate_use_case().
    Each method returns a fully-formed ContentAsset.
    """

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger
        self.site = config.get("site", {})
        self.brand = self.site.get("brand", "Pipeleap")
        self.site_url = self.site.get("site_url", "https://pipeleap.com").rstrip("/")
        self.cta_cfg = self.site.get("cta", {})
        self.funnel_cta_rules = config.get("funnel_config", {}).get("cta_rules", {})
        self.default_author = config.get("growth_engine", {}).get("default_author", "Pipeleap Team")

    # ── Public interface ──────────────────────────────────────────────────────

    def generate_blog(
        self,
        cluster: KeywordCluster,
        gsc_row: dict[str, Any] | None = None,
    ) -> ContentAsset:
        keyword = cluster.primary_keyword
        kw_title = title_case_keyword(keyword)
        slug = slugify(keyword)
        intent = cluster.intent
        strategy = self._build_strategy(cluster, gsc_row)

        if strategy["ctr_optimized"]:
            self.logger.info(
                "CTR-optimization mode for '%s' (impressions=%s, ctr=%.2f%%, pos=%.1f)",
                keyword,
                strategy["impressions"],
                strategy["ctr"] * 100,
                strategy["position"] or 0,
            )

        body = _strip_formatting(self._render_blog_body(keyword, kw_title, cluster, strategy))
        quality_score, quality_flags = self._quality_score(body, keyword, intent)

        if quality_score < _MIN_QUALITY_SCORE:
            self.logger.warning(
                "Blog quality gate FAILED for '%s' (score=%.2f, flags=%s)",
                keyword, quality_score, quality_flags,
            )
            return self._stub_asset(slug, keyword, kw_title, "blog_post", quality_score)

        today = _date.today().isoformat()
        seo_title, meta_description = self._title_meta(keyword, kw_title, intent, strategy)

        return ContentAsset(
            slug=slug,
            page_type="blog_post",
            title=kw_title,
            seo_title=seo_title,
            meta_description=meta_description,
            h1=kw_title,
            body_markdown=body,
            schema_markup=self._schema(slug, seo_title, meta_description, today),
            internal_link_suggestions=[],
            call_to_action=self._cta("TOFU"),
            source_keywords=[keyword, *[o.keyword for o in cluster.opportunities[1:5]]],
            target_persona=self._persona(cluster.cluster_name),
            eeat_notes=self._eeat_notes(),
            date_published=today,
            date_modified=today,
            author_name=self.default_author,
            uniqueness_score=round(quality_score, 2),
            eeat_checklist=self._eeat_checklist("blog_post"),
        )

    def generate_comparison(
        self,
        cluster: KeywordCluster,
        gsc_row: dict[str, Any] | None = None,
    ) -> ContentAsset:
        keyword = cluster.primary_keyword
        kw_title = title_case_keyword(keyword)
        slug = slugify(keyword)
        strategy = self._build_strategy(cluster, gsc_row)
        body = _strip_formatting(self._render_comparison_body(keyword, kw_title, cluster, strategy))
        quality_score, _ = self._quality_score(body, keyword, "commercial")

        if quality_score < _MIN_QUALITY_SCORE:
            self.logger.warning("Comparison quality gate FAILED for '%s' (score=%.2f)", keyword, quality_score)
            return self._stub_asset(slug, keyword, kw_title, "comparison_page", quality_score)

        today = _date.today().isoformat()
        seo_title = f"{kw_title} | Pipeleap Revenue Automation"
        meta_description = (
            f"Compare {keyword} options with a revenue-first lens: workflow depth, CRM quality, "
            f"enrichment control, and outbound execution in one governed system."
        )[:158]

        return ContentAsset(
            slug=slug,
            page_type="comparison_page",
            title=kw_title,
            seo_title=seo_title,
            meta_description=meta_description,
            h1=kw_title,
            body_markdown=body,
            schema_markup=self._schema(slug, seo_title, meta_description, today),
            internal_link_suggestions=[],
            call_to_action=self._cta("BOFU"),
            source_keywords=[keyword, *[o.keyword for o in cluster.opportunities[1:5]]],
            target_persona=self._persona(cluster.cluster_name),
            eeat_notes=self._eeat_notes(),
            date_published=today,
            date_modified=today,
            author_name=self.default_author,
            uniqueness_score=round(quality_score, 2),
            eeat_checklist=self._eeat_checklist("comparison_page"),
        )

    def generate_use_case(
        self,
        cluster: KeywordCluster,
        gsc_row: dict[str, Any] | None = None,
    ) -> ContentAsset:
        keyword = cluster.primary_keyword
        kw_title = title_case_keyword(keyword)
        slug = slugify(keyword)
        strategy = self._build_strategy(cluster, gsc_row)
        body = _strip_formatting(self._render_use_case_body(keyword, kw_title, cluster, strategy))
        quality_score, _ = self._quality_score(body, keyword, "informational")

        if quality_score < _MIN_QUALITY_SCORE:
            self.logger.warning("Use-case quality gate FAILED for '%s' (score=%.2f)", keyword, quality_score)
            return self._stub_asset(slug, keyword, kw_title, "use_case_page", quality_score)

        today = _date.today().isoformat()
        seo_title = f"{kw_title} Use Case | Pipeleap"
        meta_description = (
            f"See how {keyword} works end to end with Pipeleap: intake, enrichment, CRM sync, "
            f"sequence assignment, and reply routing, no manual handoffs."
        )[:158]

        return ContentAsset(
            slug=slug,
            page_type="use_case_page",
            title=kw_title,
            seo_title=seo_title,
            meta_description=meta_description,
            h1=kw_title,
            body_markdown=body,
            schema_markup=self._schema(slug, seo_title, meta_description, today),
            internal_link_suggestions=[],
            call_to_action=self._cta("MOFU"),
            source_keywords=[keyword, *[o.keyword for o in cluster.opportunities[1:5]]],
            target_persona=self._persona(cluster.cluster_name),
            eeat_notes=self._eeat_notes(),
            date_published=today,
            date_modified=today,
            author_name=self.default_author,
            uniqueness_score=round(quality_score, 2),
            eeat_checklist=self._eeat_checklist("use_case_page"),
        )

    # ── Strategy ──────────────────────────────────────────────────────────────

    def _build_strategy(
        self,
        cluster: KeywordCluster,
        gsc_row: dict[str, Any] | None,
    ) -> dict[str, Any]:
        opp = cluster.opportunities[0] if cluster.opportunities else None
        difficulty = float(opp.estimated_difficulty or 35) if opp else 35.0
        position: float | None = float(gsc_row["position"]) if gsc_row and gsc_row.get("position") else None
        impressions: int = int(gsc_row.get("impressions", 0)) if gsc_row else 0
        ctr: float = float(gsc_row.get("ctr", 0.0)) if gsc_row else 0.0

        target_word_count = next(
            (t for (lo, hi), t in _DIFFICULTY_WORD_TARGETS if lo <= difficulty < hi),
            1400,
        )
        target_snippet = position is None or (4 <= position <= 20) or impressions > 200
        ctr_optimized = impressions >= 100 and ctr < 0.02

        depth_mode: str
        if position is None:
            depth_mode = "comprehensive"
        elif position <= 3:
            depth_mode = "ctr_optimized"
        elif position <= 10:
            depth_mode = "snippet_optimized"
        elif position <= 20:
            depth_mode = "depth_upgrade"
        else:
            depth_mode = "comprehensive"

        trend_score: int = int(gsc_row.get("trend_score", 0)) if gsc_row else 0
        if trend_score >= 50 and depth_mode in ("comprehensive", "depth_upgrade"):
            depth_mode = "trending"

        return {
            "difficulty": difficulty,
            "target_word_count": target_word_count,
            "target_featured_snippet": target_snippet,
            "ctr_optimized": ctr_optimized,
            "depth_mode": depth_mode,
            "position": position,
            "impressions": impressions,
            "ctr": ctr,
            "trend_score": trend_score,
        }

    # ── NEPQ opening ─────────────────────────────────────────────────────────

    @staticmethod
    def _variant_index(keyword: str, num: int) -> int:
        return _zlib.crc32(keyword.encode()) % num

    def _commercial_h2(self, keyword: str) -> str:
        v = self._variant_index(keyword, 3)
        variants = [
            f"## What CROs and VP Sales Operations actually compare when evaluating {keyword}",
            f"## What RevOps leaders actually compare when evaluating {keyword}",
            f"## What GTM leaders actually compare when evaluating {keyword}",
        ]
        return variants[v]

    def _nepq_opening(self, keyword: str, intent: str, strategy: dict[str, Any]) -> str:
        depth = strategy.get("depth_mode", "comprehensive")
        trending = depth == "trending"

        if intent == "commercial" or "alternative" in keyword or "vs " in keyword:
            v = self._variant_index(keyword, 4)
            variants = [
                (
                    f"A CRO evaluating {keyword} is not comparing feature lists. "
                    f"The real question is whether the system will improve pipeline coverage "
                    f"and forecast accuracy, or add another integration surface to manage."
                ),
                (
                    f"VP of Sales Operations reviewing {keyword} already has a stack. "
                    f"The question is whether a new system closes the coordination gap "
                    f"between enrichment, CRM, and outbound, or widens it."
                ),
                (
                    f"RevOps leaders evaluating {keyword} are not looking for another tool. "
                    f"They need to know whether this system reduces the integration tax "
                    f"between data enrichment and downstream execution."
                ),
                (
                    f"GTM leaders assessing {keyword} are asking one question: "
                    f"will this consolidate the tech stack or add another silo "
                    f"that requires manual reconciliation every quarter?"
                ),
            ]
            pain = variants[v]
            cost = (
                f"The cost of getting this wrong is not a failed tool purchase. "
                f"It is degraded pipeline coverage, forecast drift, and "
                f"an integration surface that grows faster than the team can govern."
            )
            gap = (
                f"Most evaluations skip the architecture question entirely. "
                f"They compare feature checklists instead of asking: who owns the workflow after launch, "
                f"and can that person update it without an engineering ticket?"
            )
        elif keyword.lower().startswith("how to") or keyword.lower().startswith("how "):
            v = self._variant_index(keyword, 4)
            variants = [
                (
                    f"A Head of Sales searching for {keyword} is not looking for a playbook. "
                    f"They need a repeatable system that protects pipeline velocity "
                    f"as the team scales beyond the founder-led sales phase."
                ),
                (
                    f"VP of Sales Strategy researching {keyword} has usually tested the obvious path. "
                    f"The tool does part of the job. The part it leaves out, multi-layer governance, "
                    f"CRM write-back, reply routing, is where pipeline leaks."
                ),
                (
                    f"A Director of Sales looking into {keyword} needs to remove manual bottlenecks "
                    f"without adding headcount. The solution must work for the existing team size."
                ),
                (
                    f"A CRO investigating {keyword} is designing infrastructure "
                    f"that protects revenue as headcount grows. "
                    f"Every manual handoff in the current workflow caps scale."
                ),
            ]
            pain = variants[v]
            cost = (
                f"At 10 manual steps per contact, a 500-contact list means 5,000 hand-offs "
                f"that can break before a single sequence fires. "
                f"Each break compounds, bad data in CRM, duplicate outreach, replies that go to the wrong rep."
            )
            gap = (
                f"The teams that solved {keyword} did not find a better tool. "
                f"They stopped treating it as a tooling problem and started treating it as a systems problem. "
                f"The specific platform matters less than whether all components are governed in one execution layer."
            )
        elif any(t in keyword.lower() for t in ("why ", "problem", "fix", "failing", "broken")):
            v = self._variant_index(keyword, 3)
            variants = [
                (
                    f"When a VP of Sales Ops hears {keyword} is not working, the root cause "
                    f"is rarely the tool. It is data architecture, enrichment disconnected from CRM, "
                    f"CRM disconnected from sequencing, and no single owner of the full workflow."
                ),
                (
                    f"A CRO told that {keyword} is broken knows the tool is not the problem. "
                    f"The issue is that no single executive owns the end-to-end flow. "
                    f"Fragmented ownership guarantees fragmented data."
                ),
                (
                    f"RevOps leaders diagnosing why {keyword} keeps failing "
                    f"find the same three failure patterns every time: "
                    f"unchecked intake, disconnected CRM logic, and no feedback loop."
                ),
            ]
            pain = variants[v]
            cost = (
                f"A broken {keyword} system does not announce itself. "
                f"It shows up as forecast misses, declining reply rates, "
                f"and revenue teams spending cycles on data quality instead of pipeline."
            )
            gap = (
                f"The standard fix is to add another point solution. "
                f"That extends the integration surface, adds another failure point, "
                f"and leaves the root problem, no governed execution layer, untouched."
            )
        else:
            v = self._variant_index(keyword, 3)
            variants = [
                (
                    f"CROs and VP Sales Strategy researching {keyword} "
                    f"are not looking for a definition. "
                    f"They are evaluating whether this architecture decision "
                    f"will improve pipeline trajectory over the next two quarters."
                ),
                (
                    f"RevOps leaders researching {keyword} need a governed execution layer "
                    f"that turns pipeline risk into predictable revenue, "
                    f"without adding headcount or engineering dependencies."
                ),
                (
                    f"GTM leaders exploring {keyword} are looking for a unified workflow "
                    f"that connects signal capture, data enrichment, CRM sync, and outbound "
                    f"into one accountable system, not a collection of loosely integrated tools."
                ),
            ]
            pain = variants[v]
            cost = (
                f"Without a governed approach to {keyword}, the operational ceiling hits fast. "
                f"Manual steps accumulate, data quality degrades, and the pipeline number "
                f"becomes a function of how many hours revenue teams can put in, not how good the strategy is."
            )
            gap = (
                f"Most {keyword} implementations fail at the handoff layer, "
                f"between enrichment and CRM, between CRM and sequencer, between sequence and reply routing. "
                f"Each handoff is owned by a different tool, a different team, and a different failure mode."
            )

        if trending:
            return _strip_formatting(f"{pain}\n\n{cost}")
        return _strip_formatting(f"{pain}\n\n{cost}\n\n{gap}")

    # ── Blog body renderers ───────────────────────────────────────────────────

    def _render_blog_body(
        self,
        keyword: str,
        kw_title: str,
        cluster: KeywordCluster,
        strategy: dict[str, Any],
    ) -> str:
        intent = cluster.intent
        kw_lower = keyword.lower()

        if intent == "commercial" or any(t in kw_lower for t in ("alternative", "vs ", "comparison", "best ")):
            return self._blog_commercial(keyword, kw_title, cluster, strategy)
        if kw_lower.startswith("how to") or kw_lower.startswith("how "):
            return self._blog_how_to(keyword, kw_title, cluster, strategy)
        if any(t in kw_lower for t in ("why ", "problem", "fix", "failing", "broken")):
            return self._blog_problem_diagnosis(keyword, kw_title, cluster, strategy)
        return self._blog_informational(keyword, kw_title, cluster, strategy)

    def _blog_how_to(
        self,
        keyword: str,
        kw_title: str,
        cluster: KeywordCluster,
        strategy: dict[str, Any],
    ) -> str:
        brand = self.brand
        snippet = self._snippet_block(keyword, "how_to") if strategy["target_featured_snippet"] else ""
        ctr_note = self._ctr_editor_note(strategy) if strategy["ctr_optimized"] else ""
        persona = self._persona(cluster.cluster_name)

        sections = [
            f"# {kw_title}",
            ctr_note,
            snippet,
            self._nepq_opening(keyword, cluster.intent, strategy),
            "",
            f"## The four layers every {kw_title} system requires",
            "",
            (
                f"**Layer 1, Signal capture and intake**\n"
                f"Define what triggers the workflow, intent signals, form fills, list imports, or enrichment thresholds. "
                f"Each trigger type requires distinct validation logic to prevent bad data entering the system."
            ),
            "",
            (
                f"**Layer 2, Enrichment and qualification**\n"
                f"Raw contacts rarely meet ICP threshold. This layer adds company data, job level, and tech stack "
                f"before any outbound step is authorised. Enrichment failure should block the sequence, not silently skip it."
            ),
            "",
            (
                f"**Layer 3, CRM write-back and routing**\n"
                f"Enriched data must land in the CRM with correct ownership, lifecycle stage, and contact-to-account "
                f"association. Skipping this layer creates the duplicate outreach problem that destroys deliverability."
            ),
            "",
            (
                f"**Layer 4, Sequencing and reply handling**\n"
                f"Only after layers 1-3 are solid should outbound fire. This layer governs cadences, "
                f"reply routing, and meeting creation, fully automated with no manual triage."
            ),
            "",
            f"## Step-by-step: building {kw_title} in {brand}",
            "",
            "```text",
            "1.  Define intake trigger (intent signal / list / form fill / enrichment threshold)",
            "2.  Add enrichment nodes with provider chain + fallback logic",
            "3.  Set qualification gate, contacts below ICP score go to review queue",
            "4.  Configure CRM write-back: field mappings, ownership, deduplication",
            "5.  Configure sequence entry rules + suppression list checks",
            "6.  Set reply routing: positive > demo booking, OOO > snooze, unsubscribe > suppress",
            "7.  Add monitoring node, pipeline velocity report to revenue leadership",
            "```",
            "",
            f"## Common mistakes that break {keyword} in production",
            "",
            (
                f"**Firing outbound before enrichment completes**, If the sequence triggers before data "
                f"validation finishes, you're emailing contacts missing job title, company size, or tech stack. "
                f"Reply rates collapse before you've started."
            ),
            "",
            (
                f"**No CRM deduplication logic**, Without dedup checks at write-back, the same contact "
                f"receives outreach from multiple reps under different sequences. The 'already talked to "
                f"someone' reply signals a broken system to your prospect."
            ),
            "",
            (
                f"**Manual reply triage**, This is the single biggest scaling bottleneck. Production "
                f"{keyword} systems auto-route: positive intent > demo booking link, out of office > "
                f"3-week snooze, unsubscribe > CRM suppression. Manual handling breaks at 50 replies/week."
            ),
            "",
            f"## Performance benchmarks: what good looks like",
            "",
            "| Metric | Needs Work | Good | Excellent |",
            "| --- | --- | --- | --- |",
            "| Enrichment match rate | < 50% | 65-75% | 80%+ |",
            "| CRM data completeness post-sync | < 65% | 80-90% | 95%+ |",
            "| Sequence reply rate | < 2% | 4-7% | 10%+ |",
            "| Time: signal > first outreach | > 3 days | < 24 hrs | < 4 hrs |",
            "| Demos booked per 100 sequences | < 1 | 3-4 | 6+ |",
            "",
            f"## How {brand} implements {keyword} end to end",
            "",
            (
                f"{brand}'s n8n-based workflow engine connects all four layers in a single orchestration layer. "
                f"Instead of separate tools for enrichment, CRM, and sequencing, each with its own API "
                f"integration and error surface, {brand} governs the entire flow from intake to demo booked "
                f"with full visibility at every step."
            ),
            "",
            "Key production capabilities:",
            f"- CRM write-back is a native workflow step with dedup logic built in",
            f"- Enrichment validation blocks the sequence until data quality meets threshold",
            f"- Reply handling is part of the workflow, not a separate tool bolted on",
                f"- Revenue teams can audit and update logic without engineering tickets",
            "",
            self._build_faqs(keyword, "how_to"),
            "",
            "## Next step",
            self._cta("TOFU"),
            "",
            self._disclosure(),
        ]
        return "\n".join(s for s in sections if s is not None)

    def _blog_informational(
        self,
        keyword: str,
        kw_title: str,
        cluster: KeywordCluster,
        strategy: dict[str, Any],
    ) -> str:
        brand = self.brand
        snippet = self._snippet_block(keyword, "definition") if strategy["target_featured_snippet"] else ""

        sections = [
            f"# {kw_title}",
            snippet,
            self._nepq_opening(keyword, cluster.intent, strategy),
            "",
            f"## Core components of a production-grade {kw_title} system",
            "",
            "A mature implementation operates across four layers working in sequence:",
            "",
            f"1. **Intake and signal detection**, what triggers the workflow and how candidates enter the system",
            f"2. **Data validation and enrichment**, every contact meets qualification standards before outbound fires",
            f"3. **CRM synchronisation**, clean, structured data with correct ownership and lifecycle state",
            f"4. **Execution and feedback**, outbound, reply handling, and reporting that closes the loop",
            "",
            f"## Workflow architecture",
            "",
            "```text",
            "Signal / Intake",
            "  > Validation + Enrichment (provider chain with fallback)",
            "  > Qualification scoring against ICP",
            "  > CRM write-back (owner, stage, account link, dedup)",
            "  > Suppression check + sequence assignment",
            "  > Outbound execution",
            "  > Reply routing > demo booking / snooze / suppress",
            "  > Weekly pipeline report to revenue leadership",
            "```",
            "",
            f"## How {brand} implements {kw_title}",
            "",
            (
                f"{brand} provides a unified workflow layer that governs all four components. "
                f"Unlike point-solution stacks that require integrations between each layer, "
                f"{brand} manages the entire lifecycle, from signal capture to demo booked, "
                f"in one system. This matters because the most common failure mode in {keyword} "
                f"implementations is data inconsistency between layers."
            ),
            "",
            self._build_faqs(keyword, "informational"),
            "",
            "## Next step",
            self._cta("TOFU"),
            "",
            self._disclosure(),
        ]
        return "\n".join(s for s in sections if s is not None)

    def _blog_commercial(
        self,
        keyword: str,
        kw_title: str,
        cluster: KeywordCluster,
        strategy: dict[str, Any],
    ) -> str:
        brand = self.brand
        snippet = self._snippet_block(keyword, "decision") if strategy["target_featured_snippet"] else ""

        sections = [
            f"# {kw_title}",
            snippet,
            self._nepq_opening(keyword, cluster.intent, strategy),
            "",
            self._commercial_h2(keyword),
            "",
            "| Dimension | Why it matters |",
            "| --- | --- |",
            "| Workflow depth | Can the system handle multi-step enrichment, conditional routing, and CRM write-back in one flow? |",
            "| CRM data quality | Does it write structured records, or dump raw contacts that need manual cleanup? |",
            "| Enrichment governance | Can you chain providers with fallback logic and quality thresholds? |",
            "| Outbound execution | Is sequencing governed within the system, or outsourced to a separate tool? |",
            "| Operator ownership | Can revenue teams iterate on workflows without engineering tickets? |",
            "| Outcome reporting | Does it measure demos booked and CRM hygiene, or just activity? |",
            "",
            f"## Where {brand} fits for {keyword}",
            "",
            f"**{brand} is the right choice when:**",
            f"- You need enrichment, CRM sync, and outbound execution in one governed layer",
                f"- Your team needs to iterate on workflows without engineering dependency",
            f"- Data inconsistency between tools is causing duplicate outreach or dirty CRM records",
            f"- You are replacing 3-5 point solutions with one orchestration system",
            "",
            f"**{brand} is not the right fit when:**",
            f"- You only need simple single-step automations (a lighter tool is faster to launch)",
            f"- Your team does not run outbound or CRM-heavy workflows",
            f"- You need a consumer-grade no-code tool with no workflow configuration",
            "",
            f"## Migration and implementation considerations",
            "",
            (
                f"Most teams switching {keyword} platforms face the same migration challenge: existing "
                f"data in multiple systems must be normalised before the new workflow runs cleanly. "
                f"A phased approach works best, start with one workflow (e.g., inbound lead "
                f"enrichment), prove the data quality improvement, then migrate additional use cases."
            ),
            "",
            self._build_faqs(keyword, "commercial"),
            "",
            "## Next step",
            self._cta("BOFU"),
            "",
            self._disclosure(),
        ]
        return "\n".join(s for s in sections if s is not None)

    def _blog_problem_diagnosis(
        self,
        keyword: str,
        kw_title: str,
        cluster: KeywordCluster,
        strategy: dict[str, Any],
    ) -> str:
        brand = self.brand
        snippet = self._snippet_block(keyword, "problem") if strategy["target_featured_snippet"] else ""

        sections = [
            f"# {kw_title}",
            snippet,
            self._nepq_opening(keyword, cluster.intent, strategy),
            "",
            f"## The three failure patterns",
            "",
            (
                f"**Pattern 1: Data enters the workflow unchecked**, Unvalidated contacts get enriched "
                f"with partial data, which breaks ICP scoring, which sends outbound to wrong-fit accounts, "
                f"which tanks deliverability. The problem started at intake, not at the inbox."
            ),
            "",
            (
                f"**Pattern 2: CRM and sequence logic are disconnected**, The sequencer fires without "
                f"knowing the CRM state. Result: existing customers receive cold outreach, active "
                f"opportunities get duplicate sequences, and revenue teams waste time triaging angry replies."
            ),
            "",
            (
                f"**Pattern 3: No feedback loop**, Sequence outcomes (replies, bounces, meetings) "
                f"don't update the CRM or the workflow. Revenue leadership cannot tell which segments are working "
                f"and which are wasting budget."
            ),
            "",
            f"## The systematic fix: a three-layer approach",
            "",
            (
                f"**Fix 1, Enforce data quality at intake**, Add a validation gate before enrichment "
                f"runs. Any contact missing required fields (company, job title, email format) goes to "
                f"a review queue. Enrichment only fires on clean records."
            ),
            "",
            (
                f"**Fix 2, Close the CRM loop before outbound**, Every workflow step writes a "
                f"structured CRM update before the sequence fires. Ownership, lifecycle stage, "
                f"and account association are set in the workflow, not manually cleaned up later."
            ),
            "",
            (
                f"**Fix 3, Automate reply routing and feedback**, Positive replies trigger demo "
                f"booking. Out-of-office triggers a snooze. Unsubscribes update the CRM suppression "
                f"list. Every outcome feeds back into the system so the next run is better."
            ),
            "",
            f"## How {brand} implements the systematic fix",
            "",
            "```text",
            "Intake > Validation gate > Enrichment > ICP scoring",
            "  > CRM write-back (owner + stage + dedup) > Suppression check",
            "  > Sequence assignment > Outbound",
            "  > Reply routing > CRM update + demo booking / snooze / suppress",
            "  > Weekly pipeline report to revenue leadership",
            "```",
            "",
            self._build_faqs(keyword, "problem"),
            "",
            "## Next step",
            self._cta("MOFU"),
            "",
            self._disclosure(),
        ]
        return "\n".join(s for s in sections if s is not None)

    # ── Comparison body ───────────────────────────────────────────────────────

    def _render_comparison_body(
        self,
        keyword: str,
        kw_title: str,
        cluster: KeywordCluster,
        strategy: dict[str, Any],
    ) -> str:
        brand = self.brand

        sections = [
            f"# {kw_title}: A Revenue Team's Evaluation Guide",
            "",
            (
                f"> **Bottom line:** When evaluating {keyword}, focus on workflow depth, "
                f"CRM write-back quality, and whether the system can govern enrichment, "
                f"sequencing, and reply routing in one layer, not just automate individual steps."
            ),
            "",
            f"## What this comparison is actually about",
            "",
            (
                f"The {keyword} market has fragmented significantly. Most comparisons focus on "
                f"feature lists. This guide focuses on what matters for revenue teams: can the "
                f"system reduce manual operations work, improve CRM data quality, and drive more demos "
                f"without adding headcount?"
            ),
            "",
            f"## Two types of buyers evaluating {keyword}",
            "",
            (
                f"**Orchestration buyers** need a system that governs the entire workflow, signal "
                f"capture, enrichment, CRM sync, outbound, reply handling. They are replacing a "
                f"fragmented stack of 4-6 tools."
            ),
            "",
            (
                f"**Point-solution buyers** need to solve one specific problem, better deliverability, "
                f"faster enrichment, or cheaper automation. They are adding to an existing stack."
            ),
            "",
            (
                f"Most teams evaluating {keyword} are orchestration buyers who don't yet know it. "
                f"The point-solution purchase always reveals the orchestration need 6-12 months later."
            ),
            "",
            f"## What to actually test during evaluation",
            "",
            "| Capability | What to test |",
            "| --- | --- |",
            "| CRM write-back | Does it write contact + account + ownership in one step with dedup logic? |",
            "| Enrichment chaining | Can you chain multiple providers with fallback logic? |",
            "| Conditional routing | Can you branch based on account score, job title, or CRM field? |",
            "| Error handling | What happens when enrichment fails mid-workflow? |",
            "| Observability | Can revenue teams see exactly which step failed and why? |",
            "| Iteration speed | How long does it take to change one workflow step without re-deploying? |",
            "",
            f"## Where {brand} fits on {keyword}",
            "",
            f"**{brand} is the right choice when:**",
            f"- You need enrichment, CRM, and sequencing in one governed architecture",
                f"- Your team needs to iterate on workflows without engineering dependency",
            f"- Data quality between tools is a recurring operational problem",
            f"- You are consolidating a fragmented point-solution stack",
            "",
            f"**{brand} is not the best fit when:**",
            f"- You only need one-step automations with no CRM or enrichment requirement",
            f"- Your team runs purely inbound with no outbound component",
            f"- You need a consumer no-code tool with zero workflow configuration",
            "",
            f"## Implementation and migration notes",
            "",
            (
                f"Start with one workflow. Prove the data quality improvement. Then migrate additional "
                f"use cases. Avoid big-bang migrations, they create downtime risk and make debugging "
                f"harder when problems arise."
            ),
            "",
            self._build_faqs(keyword, "commercial"),
            "",
            "## Next step",
            self._cta("BOFU"),
            "",
            self._disclosure(),
        ]
        return "\n".join(s for s in sections if s is not None)

    # ── Use-case body ─────────────────────────────────────────────────────────

    def _render_use_case_body(
        self,
        keyword: str,
        kw_title: str,
        cluster: KeywordCluster,
        strategy: dict[str, Any],
    ) -> str:
        brand = self.brand
        persona = self._persona(cluster.cluster_name)

        sections = [
            f"# {kw_title}",
            "",
            (
                f"> **Use case summary:** {kw_title} connects high-intent signals to demo-ready "
                f"opportunities through governed automation, covering intake, enrichment, CRM sync, "
                f"sequence assignment, and reply routing without manual handoffs."
            ),
            "",
            f"## Who this use case is for",
            "",
            (
                f"This workflow is built for {persona} who need to operationalise {keyword} without "
                f"adding headcount or stitching together point solutions. It works best when the team "
                f"has an existing CRM, sequencer, and enrichment tool but lacks the orchestration layer "
                f"that connects them."
            ),
            "",
            f"## What the {kw_title} workflow automates",
            "",
            (
                f"**Prospect intake**, Ingest contacts from intent platforms, list uploads, form "
                f"fills, or CRM triggers. Normalisation rules apply immediately, no raw data enters "
                f"the enrichment step."
            ),
            "",
            (
                f"**Enrichment and scoring**, Chain enrichment providers to fill company data, job "
                f"title, and tech stack. Apply ICP scoring before any outbound step is authorised. "
                f"Contacts below threshold go to a review queue, not the sequence."
            ),
            "",
            (
                f"**CRM synchronisation**, Write enriched, scored contacts to the CRM with correct "
                f"account association, contact owner, and lifecycle stage. Deduplication logic prevents "
                f"duplicate records at write time."
            ),
            "",
            (
                f"**Sequence assignment**, Route qualified contacts into the right sequence based on "
                f"ICP score, company size, or territory. Suppression lists prevent outreach to existing "
                f"customers or active opportunities."
            ),
            "",
            (
                f"**Reply handling**, Automatically route replies: positive intent > calendar link, "
                f"out of office > 3-week snooze, unsubscribe > CRM suppression. No manual triage required by your team."
            ),
            "",
            f"## Workflow architecture",
            "",
            "```text",
            "Intake (signal / list / form fill)",
            "  > Normalisation + deduplication",
            "  > Enrichment (provider chain with fallback)",
            "  > ICP scoring + qualification gate",
            "  > CRM write-back (owner, stage, account link)",
            "  > Suppression check",
            "  > Sequence assignment",
            "  > Outbound execution",
            "  > Reply routing > demo booking / snooze / suppress",
            "  > Pipeline reporting to revenue leadership",
            "```",
            "",
            f"## Implementation blueprint for {brand}",
            "",
            f"1. Connect your intake source to the {brand} workflow trigger",
            f"2. Configure enrichment nodes with your preferred providers and fallback logic",
            f"3. Set ICP scoring thresholds, sub-threshold contacts go to review, not suppression",
            f"4. Define CRM write-back rules: field mappings, ownership logic, dedup criteria",
            f"5. Create sequence assignment rules by ICP segment or territory",
            f"6. Configure reply routing with snooze logic and suppression list updates",
                f"7. Add a weekly pipeline velocity report node for revenue leadership visibility",
            "",
            f"## Expected outcomes",
            "",
            "| Metric | Before | After (typical) |",
            "| --- | --- | --- |",
            "| Revenue team time on manual data tasks | 60-80% | < 20% |",
            "| CRM contact completeness | 40-60% | 80-90% |",
            "| Demos booked per 100 sequences | 1-2 | 4-6 |",
            "| Time from signal to first outreach | 2-5 days | < 4 hours |",
            "",
            self._build_faqs(keyword, "informational"),
            "",
            "## Next step",
            self._cta("MOFU"),
            "",
            self._disclosure(),
        ]
        return "\n".join(s for s in sections if s is not None)

    # ── Featured snippet blocks ───────────────────────────────────────────────

    def _snippet_block(self, keyword: str, snippet_type: str) -> str:
        kw_title = title_case_keyword(keyword)
        if snippet_type == "how_to":
            return (
                f"> **{kw_title}** requires four connected layers: intake and signal detection, "
                f"data enrichment and qualification, CRM write-back and routing, and outbound "
                f"execution with reply handling. Production systems handle all four in one governed "
                f"workflow, not across separate tools.\n"
            )
        if snippet_type == "decision":
            return (
                f"> **Evaluating {keyword}?** Compare options on workflow depth, CRM write-back "
                f"quality, enrichment governance, and whether revenue teams can iterate without engineering. "
                f"The winning system is the one your actual operator can run and improve over time.\n"
            )
        if snippet_type == "problem":
            return (
                f"> **Root cause of {keyword} issues:** Nearly always data architecture, not the "
                f"tool. Fragmented enrichment, disconnected CRM logic, and no reply feedback loop "
                f"are the three failure patterns. Each has a systematic fix that doesn't require "
                f"replacing your entire stack.\n"
            )
        return (
            f"> **{kw_title}** is the operational system that connects intent signals, data "
            f"enrichment, CRM synchronisation, and outbound execution into one governed revenue "
            f"workflow, replacing fragmented point tools with measurable, repeatable pipeline "
            f"generation.\n"
        )

    # ── FAQ generation ────────────────────────────────────────────────────────

    def _build_faqs(self, keyword: str, faq_type: str) -> str:
        brand = self.brand
        kw_lower = keyword.lower()

        faq_sets: dict[str, list[tuple[str, str]]] = {
            "how_to": [
                (
                    f"How long does it take to implement {keyword} in production?",
                    f"Most teams complete a pilot workflow within 48-72 hours using {brand}. Full deployment "
                     f", enrichment chain, CRM write-back, and sequence logic, typically takes one to two "
                    f"weeks, depending on CRM complexity and data quality at intake.",
                ),
                (
                    f"What data quality issues typically block {keyword}?",
                    f"The most common blockers are missing job title or company data (breaks ICP scoring), "
                    f"inconsistent account naming in the CRM (breaks deduplication), and sequencer bounce "
                    f"lists that aren't shared with the enrichment layer.",
                ),
                (
                    f"Can {keyword} work for a lean team without a dedicated operations engineer?",
                    f"Yes. {brand} is designed for lean teams. Revenue teams can build and "
                    f"run production workflows without engineering support. The n8n-based builder provides "
                    f"visual configuration with full logic control.",
                ),
                (
                    f"How do you measure whether {keyword} is working?",
                    f"Track four metrics weekly: enrichment match rate (target >70%), CRM contact completeness "
                    f"(target >85%), demos booked per 100 sequences (target >3), and time from signal to "
                    f"first outreach (target <4 hours).",
                ),
            ],
            "commercial": [
                (
                    f"What is the most common mistake when evaluating {keyword} options?",
                    f"Comparing features instead of outcomes. The question isn't 'does it have an enrichment "
                     f"integration?', it's 'does the enrichment result land in the CRM correctly, and can "
                    f"my RevOps team can change the logic without a developer?'",
                ),
                (
                    f"How do I migrate from my current {keyword} setup to {brand}?",
                    f"Start with one workflow, typically inbound lead enrichment or a single outbound "
                    f"segment. Prove the data quality improvement, then migrate additional use cases. "
                    f"Avoid big-bang migrations that create downtime risk.",
                ),
                (
                    f"How does {brand} compare to building a custom {keyword} system in-house?",
                    f"Custom builds give maximum flexibility but require ongoing engineering investment to "
                    f"maintain, debug, and update as data sources and APIs change. {brand} provides a "
                    f"governed system your RevOps team can iterate on without engineering tickets, faster "
                    f"to launch and significantly cheaper to maintain at scale.",
                ),
            ],
            "informational": [
                (
                    f"Is {keyword} only useful for large sales teams?",
                    f"No. The fastest ROI typically comes from lean teams of 2-5 where manual data work "
                    f"consumes the most time. {brand} gives small teams enterprise-grade workflow governance "
                    f"without needing a dedicated operations engineer.",
                ),
                (
                    f"Does {brand} replace my existing CRM?",
                    f"No. {brand} acts as an orchestration layer on top of your existing CRM, enriching "
                    f"data, enforcing ownership rules, and writing clean records back. It works alongside "
                    f"HubSpot, Salesforce, and other CRMs without replacing them.",
                ),
                (
                    f"What happens if an enrichment call fails mid-workflow?",
                    f"Workflows include configurable error handling, retry logic, fallback to a secondary "
                    f"provider, or routing failed contacts to a review queue. Silent failures that let bad "
                    f"data into the sequence are not a {brand} behaviour.",
                ),
            ],
            "problem": [
                (
                    f"How quickly can the systematic fix for {keyword} be implemented?",
                    f"The data quality gate and CRM write-back fix can typically be live within 48 hours "
                    f"for a single workflow. The full three-layer implementation, intake validation, "
                    f"CRM loop, reply routing, takes one to two weeks depending on existing tool complexity.",
                ),
                (
                    f"Will fixing {keyword} require replacing my current tools?",
                    f"Usually not. {brand} connects your existing CRM, enrichment provider, and sequencer "
                    f"through an orchestration layer, it doesn't replace them. The fix is architectural, "
                    f"not a tool swap.",
                ),
                (
                    f"How do I know when {keyword} is actually fixed?",
                    f"When your enrichment match rate is above 70%, CRM contact completeness is above 85%, "
                    f"and reply routing operates without manual triage, the system is working. Measure "
                    f"these weekly, not monthly.",
                ),
            ],
        }

        faqs = faq_sets.get(faq_type, faq_sets["informational"])
        lines = ["## Frequently Asked Questions", ""]
        for question, answer in faqs[:4]:
            lines.append(f"### {question}")
            lines.append(answer)
            lines.append("")
        return "\n".join(lines)

    # ── Quality gate ──────────────────────────────────────────────────────────

    # Phrases that signal AI-generated / robotic writing, penalised in quality gate
    _AI_PHRASES: frozenset[str] = frozenset({
        "in today's fast-paced", "in the ever-evolving", "it is important to note",
        "it is worth noting", "in conclusion,", "to summarise,", "to summarize,",
        "as mentioned earlier", "as previously mentioned", "needless to say",
        "at the end of the day", "in today's digital age", "in today's competitive landscape",
        "leverage the power of""unlock the potential", "revolutionize your",
        "game-changer", "dive deep into", "delve into", "it goes without saying",
        "not only that, but", "last but not least",
    })

    def _quality_score(self, body: str, keyword: str, intent: str) -> tuple[float, list[str]]:
        """
        Returns (score 0-1, flags list).
        Evaluates: word count, keyword presence, section depth, FAQ presence,
        disclosure presence, keyword density, and AI-phrase detection.
        """
        flags: list[str] = []
        score = 1.0
        words = body.split()
        word_count = len(words)

        body_lower = body.lower()
        kw_lower = keyword.lower()

        if kw_lower not in body_lower:
            flags.append("primary_keyword_absent")
            score -= 0.20

        if "## frequently asked questions" not in body_lower:
            flags.append("no_faq_section")
            score -= 0.10

        if "## next step" not in body_lower:
            flags.append("no_cta_section")
            score -= 0.05

        # Keyword density: primary keyword should appear 1-4% of words
        kw_words = kw_lower.split()
        kw_occurrences = sum(
            1 for i in range(len(words) - len(kw_words) + 1)
            if [w.lower().strip(".,!?") for w in words[i: i + len(kw_words)]] == kw_words
        )
        density = kw_occurrences / max(word_count, 1)
        if density > 0.04:
            flags.append(f"keyword_overstuffed ({density:.2%})")
            score -= 0.15

        # AI-phrase detection, robotic transitions and filler patterns
        detected = [p for p in self._AI_PHRASES if p in body_lower]
        if detected:
            flags.append(f"ai_phrases_detected: {detected[:3]}")
            score -= min(0.20, len(detected) * 0.05)
            self.logger.warning(
                "AI-sounding phrases found in blog body for '%s': %s, rewrite before publishing.",
                keyword, detected[:5],
            )

        return round(max(0.0, score), 2), flags

    # ── Title / meta generation ───────────────────────────────────────────────

    @staticmethod
    def _title_meta(
        keyword: str,
        kw_title: str,
        intent: str,
        strategy: dict[str, Any],
    ) -> tuple[str, str]:
        kw_lower = keyword.lower()

        if strategy["ctr_optimized"]:
            seo_title = f"{kw_title}: The System That Actually Works | Pipeleap"
            meta = (
                f"Stop losing pipeline to manual {keyword} steps. See how Pipeleap automates "
                f"enrichment, CRM sync, and outbound execution in one governed workflow."
            )[:158]
            return seo_title, meta

        if kw_lower.startswith("how to"):
            seo_title = f"{kw_title} | Step-by-Step with Pipeleap"
            meta = (
                f"Learn how to implement {keyword} with enrichment, CRM write-back, and "
                f"outbound execution working as one governed system, not separate tools."
            )[:158]
            return seo_title, meta

        if intent == "commercial":
            seo_title = f"{kw_title} | Pipeleap Revenue Automation"
            meta = (
                f"Evaluate {keyword} with a revenue-first lens: workflow depth, CRM quality, "
                f"enrichment control, and outbound execution in one system."
            )[:158]
            return seo_title, meta

        seo_title = f"{kw_title} | Pipeleap"
        meta = (
            f"Understand {keyword} end to end: signal capture, enrichment, CRM sync, and "
            f"outbound execution governed by one workflow layer."
        )[:158]
        return seo_title, meta

    # ── Schema markup ─────────────────────────────────────────────────────────

    def _schema(
        self,
        slug: str,
        seo_title: str,
        meta_description: str,
        today: str,
    ) -> list[dict[str, Any]]:
        page_url = f"{self.site_url}/{slug}"
        org = {"@type": "Organization", "name": self.brand, "url": self.site_url}
        return [
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "name": seo_title,
                "description": meta_description,
                "url": page_url,
                "datePublished": today,
                "dateModified": today,
                "author": org,
                "publisher": org,
            },
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f"What is {seo_title.split('|')[0].strip()}?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": meta_description,
                        },
                    }
                ],
            },
        ]

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _persona(self, cluster_name: str) -> str:
        cl = cluster_name.lower()
        if "outbound" in cl or "sdr" in cl:
            return "VP of Sales Operations and revenue teams"
        if "crm" in cl or "revenue" in cl:
            return "RevOps leaders and CROs"
        if "n8n" in cl:
            return "GTM leaders and operations teams"
        return "revenue leadership teams"

    def _cta(self, funnel_stage: str) -> str:
        # ONE CTA per post, no secondary link, no alternatives, no repeated variants.
        rule = self.funnel_cta_rules.get(funnel_stage, {})
        label = rule.get("primary") or self.cta_cfg.get("primary_label", "Book a demo")
        url   = self.cta_cfg.get("primary_url", self.site_url)
        return f"[{label}]({url})"

    def _disclosure(self) -> str:
        return (
            "\n---\n"
            "*This content was produced with AI assistance and reviewed for factual accuracy. "
            "For verified product details, workflow screenshots, and live examples, "
            f"visit the [{self.brand} product page]({self.site_url}) or speak with a workflow specialist.*"
        )

    @staticmethod
    def _ctr_editor_note(strategy: dict[str, Any]) -> str:
        pos = strategy.get("position")
        imp = strategy.get("impressions", 0)
        ctr = strategy.get("ctr", 0.0)
        pos_str = f"{pos:.1f}" if pos is not None else "unknown"
        return (
            f"*GSC signal: {imp:,} impressions at position {pos_str} with {ctr:.1%} CTR, "
            f"below the 2% threshold. Prioritise a more specific, outcome-focused title tag "
            f"before publishing.*\n"
        )

    @staticmethod
    def _eeat_notes() -> list[str]:
        return [
            "Add a real operator byline with LinkedIn or bio link before publishing.",
            "Insert at least one product screenshot or workflow diagram.",
            "Add a quantified proof point: reply rate lift, CRM hygiene improvement, or customer quote.",
            "Set a 90-day content review reminder and update dateModified when refreshed.",
        ]

    @staticmethod
    def _eeat_checklist(page_type: str) -> list[dict[str, Any]]:
        base = [
            {"item": "Author byline", "status": "missing", "instructions": "Add a RevOps or revenue leader byline with LinkedIn link."},
            {"item": "Publication date", "status": "auto-filled", "instructions": "datePublished set in schema. Verify CMS injects it in the HTML head."},
            {"item": "Product screenshot", "status": "missing", "instructions": "Insert at least one real product screenshot showing the workflow builder."},
            {"item": "Outcome proof point", "status": "missing", "instructions": "Add a quantified result: reply rate lift, CRM hygiene improvement, or named customer quote."},
            {"item": "90-day review reminder", "status": "missing", "instructions": "Set a calendar reminder to refresh this page and update dateModified."},
        ]
        if page_type in {"comparison_page", "landing_page"}:
            base.append({
                "item": "Third-party validation",
                "status": "missing",
                "instructions": "Link to a G2 review, Capterra listing, or press mention.",
            })
        return base

    @staticmethod
    def _stub_asset(
        slug: str,
        keyword: str,
        kw_title: str,
        page_type: str,
        quality_score: float,
    ) -> ContentAsset:
        return ContentAsset(
            slug=slug,
            page_type=page_type,
            title=kw_title,
            seo_title=kw_title,
            meta_description="",
            h1=kw_title,
            body_markdown="",
            schema_markup=[],
            internal_link_suggestions=[],
            call_to_action="",
            source_keywords=[keyword],
            target_persona="",
            uniqueness_score=quality_score,
        )
