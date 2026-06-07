"""
CTR Engineering Engine for Pipeleap SEO.

Responsibilities:
1. Generate A/B title variants per page to test in GSC (stored in metadata)
2. Inject PAA (People Also Ask) blocks into page markdown
3. Structure featured snippet candidates (paragraph, list, table)
4. Score each page's snippet eligibility and assign a snippet_type target

Usage:
    engine = CTREngine()
    metadata = engine.enrich(page, gsc_rows)
    # Returns page with:
    #   page.title_variants     — list of 3 alternative SEO titles to test
    #   page.snippet_type       — "paragraph" | "list" | "table" | "none"
    #   page.paa_block          — markdown PAA section to append to body
    #   page.ctr_score          — estimated snippet eligibility score (0–1)
"""
from __future__ import annotations

import re
from typing import Any

from modules.pipeleap_seo_engine.data.funnel_stages import (
    stage_for, PAA_BANKS, paa_questions_for
)


# ── CTR title templates by intent ─────────────────────────────────────────────

TITLE_TEMPLATES: dict[str, list[str]] = {
    "informational": [
        "{keyword} — Complete Guide for SaaS Teams ({year})",
        "What Is {keyword}? Definition + How It Works",
        "How to {action}: {keyword} Step-by-Step",
        "{keyword}: Everything SaaS Revenue Teams Need to Know",
        "The {keyword} Playbook for B2B SaaS ({year})",
    ],
    "commercial": [
        "{keyword} — Best Platform for SaaS Teams",
        "Best {keyword} Tools for SaaS ({year} Comparison)",
        "{keyword} for {persona}: How Pipeleap Does It",
        "How {persona} Teams Use {keyword} to Build Pipeline",
        "{keyword}: Features, Pricing, and Use Cases",
    ],
    "transactional": [
        "{keyword} — Get a Free GTM Audit",
        "Book a {keyword} Demo — See It Live in 30 Minutes",
        "{keyword} for SaaS: See How It Works for Your Team",
        "Pipeleap {keyword} — Start Building Predictable Pipeline",
        "Get Your {keyword} — Free 48-Hour Assessment",
    ],
    # comparison titles removed
}

# Featured snippet structure targets by page type
SNIPPET_TARGETS: dict[str, str] = {
    "blog_post":            "paragraph",   # definition/answer at top
    "glossary_page":        "paragraph",   # "What is X?" direct answer
    "problem_page":         "list",        # numbered root causes
    "use_case_page":        "paragraph",   # "X allows you to..."
    "role_page":            "paragraph",   # "For VP Sales, X means..."
    "integration_page":     "list",        # what the integration does
    "workflow_page":        "list",        # numbered workflow steps
    "workflow_recipe":      "list",
    "bofu_page":            "paragraph",   # direct answer to the BOFU question
    "objection_page":       "paragraph",   # clear rebuttal at top
    "landing_page":         "paragraph",
    "glossary_index":       "list",
}

# Power words by funnel stage
POWER_WORDS: dict[str, list[str]] = {
    "TOFU": ["Complete", "Step-by-Step", "Guide", "How to", "Everything", "Playbook"],
    "MOFU": ["Best", "Top", "For SaaS Teams", "Comparison", "Features"],
    "BOFU": ["Free", "Live", "Book", "See It", "Get", "Start", "Demo", "Audit"],
    "SQL":  ["Book", "Schedule", "Start", "Get Started", "See It Live"],
}


class CTREngine:
    """Enriches generated pages with CTR-optimised titles, PAA blocks, and snippet structure."""

    def __init__(self, year: int | None = None) -> None:
        from datetime import datetime
        self.year = year or datetime.now().year

    # ── Public API ─────────────────────────────────────────────────────────────

    def enrich_page(self, page: Any, gsc_rows: list[dict] | None = None) -> dict:
        """
        Returns a dict of CTR enrichment data to merge into the page's metadata.json.

        Keys:
          title_variants      — list[str] of 3 A/B title options
          snippet_type        — "paragraph" | "list" | "table"
          paa_block           — markdown string to append to body
          ctr_score           — float 0–1 snippet eligibility estimate
          meta_description_variant — alternative meta description
        """
        stage = stage_for(page.page_type)
        intent = self._intent_from_stage(stage)
        snippet_type = SNIPPET_TARGETS.get(page.page_type, "paragraph")

        title_variants = self._generate_title_variants(
            page.primary_keyword, page.page_type, intent, stage
        )
        paa_block = self._paa_block(page.primary_keyword, page.page_type)
        ctr_score = self._score(page.page_type, snippet_type, gsc_rows or [])
        meta_variant = self._meta_variant(page.primary_keyword, stage, page.meta_description)

        return {
            "title_variants": title_variants,
            "snippet_type": snippet_type,
            "paa_block": paa_block,
            "ctr_score": round(ctr_score, 3),
            "meta_description_variant": meta_variant,
        }

    def inject_snippet_block(self, markdown: str, page_type: str, keyword: str) -> str:
        """
        Prepends a snippet-optimised answer block to existing markdown.
        The block is 40–60 words targeting Google's featured snippet extraction.
        """
        snippet_type = SNIPPET_TARGETS.get(page_type, "paragraph")
        block = self._build_snippet_block(keyword, page_type, snippet_type)
        if block and not markdown.startswith(block[:20]):
            return block + "\n\n" + markdown
        return markdown

    # ── Title variant generation ───────────────────────────────────────────────

    def _generate_title_variants(
        self, keyword: str, page_type: str, intent: str, stage: str
    ) -> list[str]:
        templates = TITLE_TEMPLATES.get(intent, TITLE_TEMPLATES["informational"])
        variants = []
        persona = self._persona_from_page_type(page_type)
        competitor = ""
        action = self._action_from_keyword(keyword)
        kw_clean = self._clean_keyword(keyword)
        kw_title = kw_clean.title()

        for tmpl in templates[:4]:
            title = (
                tmpl
                .replace("{keyword}", kw_title)
                .replace("{year}", str(self.year))
                .replace("{persona}", persona)
                .replace("{competitor}", competitor)
                .replace("{action}", action)
            )
            # Remove duplicate words that arise when the keyword already contains
            # a word that the template adds (e.g. "Demo Demo", "Guide Guide").
            title = self._deduplicate_adjacent_words(title)
            if len(title) <= 70 and title not in variants:
                variants.append(title)

        return variants[:3]

    @staticmethod
    def _deduplicate_adjacent_words(title: str) -> str:
        """Remove immediately repeated words: 'Demo Demo' → 'Demo'."""
        words = title.split()
        deduped = [words[0]] if words else []
        for word in words[1:]:
            if word.lower() != deduped[-1].lower():
                deduped.append(word)
        return " ".join(deduped)

    # ── PAA block injection ───────────────────────────────────────────────────

    def _paa_block(self, keyword: str, page_type: str) -> str:
        topic = self._topic_from_keyword(keyword)
        questions = paa_questions_for(topic, limit=4)
        if not questions:
            return ""

        lines = [
            "## People Also Ask",
            "",
            "_Common questions SaaS teams ask about this topic:_",
            "",
        ]
        for q in questions:
            lines += [
                f"**{q}**",
                "",
                f"See the full answer in our [{topic.replace('_', ' ')} guide]"
                f"(https://pipeleap.com/blog/{topic.replace('_', '-')}).",
                "",
            ]
        return "\n".join(lines)

    # ── Featured snippet blocks ────────────────────────────────────────────────

    def _build_snippet_block(self, keyword: str, page_type: str, snippet_type: str) -> str:
        kw = self._clean_keyword(keyword)

        if snippet_type == "paragraph":
            return (
                f"**{kw.title()}** is Pipeleap's core capability for SaaS revenue teams: "
                f"automating outbound workflows from signal capture through enrichment, "
                f"sequencing, and reply routing — so pipeline generation runs consistently "
                f"without manual SDR execution. Pipeleap orchestrates your existing CRM, "
                f"enrichment tool, and sequencer rather than replacing them."
            )

        if snippet_type == "list":
            return (
                f"**{kw.title()} with Pipeleap — key steps:**\n\n"
                "1. Configure signal capture triggers (website visits, intent data, ICP match)\n"
                "2. Set enrichment rules (ICP scoring, data waterfall, qualification threshold)\n"
                "3. Map sequence routing (which segment → which sequence → which rep)\n"
                "4. Define reply classification (interested / not interested / referral)\n"
                "5. Activate CRM write-back and performance monitoring"
            )

        if snippet_type == "table":
            return (
                f"**{kw.title()} comparison:**\n\n"
                "| Dimension | Manual Execution | With Pipeleap |\n"
                "| --- | --- | --- |\n"
                "| Lead sourcing | Manual research (3+ hrs/day) | Automated from signals |\n"
                "| Sequence enrollment | Manual (rep by rep) | Automatic on qualification |\n"
                "| Reply handling | Manual inbox monitoring | Auto-classified and routed |\n"
                "| CRM updates | Manual logging | Real-time write-back |\n"
                "| Pipeline visibility | Fragmented across tools | Unified workflow view |"
            )

        return ""

    # ── Meta description variant ───────────────────────────────────────────────

    def _meta_variant(self, keyword: str, stage: str, existing_meta: str) -> str:
        kw = self._clean_keyword(keyword)
        if stage == "TOFU":
            return (
                f"Learn how SaaS teams use {kw} to build predictable outbound pipeline "
                f"without manual SDR execution. Step-by-step guide with real workflow examples."
            )[:160]
        if stage == "MOFU":
            return (
                f"See how Pipeleap handles {kw} for SaaS revenue teams. "
                f"Live workflow examples, integration details, and team-specific use cases."
            )[:160]
        if stage in ("BOFU", "SQL"):
            return (
                f"Book a Pipeleap demo for {kw}. "
                f"We'll map your exact workflow in 30 minutes — free GTM audit included."
            )[:160]
        return existing_meta[:160]

    # ── CTR score ─────────────────────────────────────────────────────────────

    def _score(self, page_type: str, snippet_type: str, gsc_rows: list[dict]) -> float:
        base = {
            "glossary_page": 0.85,
            "blog_post": 0.7,
            "problem_page": 0.75,
            "use_case_page": 0.6,
            "workflow_page": 0.7,
            "bofu_page": 0.5,
            "objection_page": 0.45,
        }.get(page_type, 0.5)

        # GSC data bonus: if impressions > 0 on related queries, the topic is visible
        impression_bonus = 0.0
        if gsc_rows:
            avg_position = sum(r.get("position", 50) for r in gsc_rows[:10]) / max(len(gsc_rows[:10]), 1)
            if avg_position < 20:
                impression_bonus = 0.1
            elif avg_position < 10:
                impression_bonus = 0.2

        return min(1.0, base + impression_bonus)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _intent_from_stage(stage: str) -> str:
        return {"TOFU": "informational", "MOFU": "commercial",
                "BOFU": "transactional", "SQL": "transactional"}.get(stage, "informational")

    @staticmethod
    def _persona_from_page_type(page_type: str) -> str:
        return {"role_page": "Sales Leaders", "use_case_page": "SaaS Teams",
                "bofu_page": "SaaS Teams"}.get(page_type, "SaaS Teams")

    @staticmethod
    def _action_from_keyword(keyword: str) -> str:
        actions = {
            "automate": "Automate Your",
            "build": "Build",
            "scale": "Scale",
            "generate": "Generate",
            "improve": "Improve",
        }
        kw_lower = keyword.lower()
        for trigger, action in actions.items():
            if trigger in kw_lower:
                return action
        return "Implement"

    @staticmethod
    def _clean_keyword(keyword: str) -> str:
        return re.sub(r"\s+", " ", keyword.strip().lower())

    @staticmethod
    def _topic_from_keyword(keyword: str) -> str:
        kw = keyword.lower()
        if any(w in kw for w in ["revops", "revenue ops", "revenue operations"]):
            return "revops"
        if any(w in kw for w in ["workflow", "orchestrat"]):
            return "workflow_orchestration"
        if any(w in kw for w in ["pipeline"]):
            return "pipeline_generation"
        return "outbound_automation"
