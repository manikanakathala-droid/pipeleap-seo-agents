"""
Keyword engine for the Pipeleap SaaS Growth Engine.
Generates Role × SaaS × Use Case × Competitor × Industry × Long-tail keyword matrix.
Self-contained — does not import from or modify the existing keyword engine.

Sources:
  - Role keywords (from ROLES data)
  - Use case keywords
  - Competitor vs / alternative keywords
  - Problem page keywords
  - Role × Use Case cross-product
  - Role × Competitor cross-product
  - Long-tail expansion from head terms
  - Question-format keywords (what is, how to, why does, when should)
  - Industry vertical keywords (fintech, healthtech, proptech, etc.)
  - BOFU keywords (demo, ROI, pricing queries)
  - Stage-specific natural language keywords
"""
from __future__ import annotations

from typing import Any

from modules.pipeleap_seo_engine.data.roles import ROLES
from modules.pipeleap_seo_engine.data.competitors import COMPETITORS, COMPETITOR_CATEGORIES
from modules.pipeleap_seo_engine.data.use_cases import USE_CASES, PROBLEM_PAGES


class GrowthKeywordEngine:
    """
    Generates the full keyword matrix for the Pipeleap SaaS Growth Engine.
    Produces Role × Use Case × Competitor × Industry × Long-tail combinations prioritized by:
    - intent (transactional > commercial > informational)
    - competition (long-tail preferred)
    - SaaS specificity
    """

    SAAS_MODIFIERS = ["saas", "b2b saas", "saas company", "revenue team", "saas startup"]

    # Industry verticals for cross-product keyword expansion
    INDUSTRY_VERTICALS = [
        "fintech", "healthtech", "proptech", "edtech", "hr tech",
        "martech", "legaltech", "insurtech", "logistic saas", "b2b marketplace",
    ]

    # Long-tail modifiers that produce naturally-searchable variants
    LONG_TAIL_MODIFIERS = [
        "without hiring sdrs",
        "without an sdr team",
        "for a small sales team",
        "at scale",
        "step by step",
        "in 2025",
        "in 2026",
        "for startups",
        "for enterprise",
        "using n8n",
        "using ai",
        "with hubspot",
        "with salesforce",
        "for b2b companies",
        "that actually works",
    ]

    # Question prefixes targeting PAA and featured snippet formats
    QUESTION_PREFIXES = [
        "what is",
        "how to",
        "how do you",
        "why is",
        "when should you",
        "how does",
        "what are the best",
        "what does",
    ]

    # BOFU query patterns for demo, ROI, and pricing intent
    BOFU_QUERIES = [
        ("book outbound automation demo",               "SQL",   "bofu_page"),
        ("outbound automation roi calculator",          "SQL",   "roi_page"),
        ("outbound automation pricing comparison",      "BOFU",  "bofu_page"),
        ("pipeleap demo",                               "SQL",   "bofu_page"),
        ("pipeleap pricing",                            "BOFU",  "bofu_page"),
        ("pipeleap vs hiring sdr",                      "BOFU",  "objection_page"),
        ("is pipeleap worth it",                        "BOFU",  "objection_page"),
        ("pipeleap review",                             "BOFU",  "objection_page"),
        ("outbound automation for saas implementation", "BOFU",  "objection_page"),
        ("build vs buy outbound automation",            "BOFU",  "objection_page"),
        ("how long does outbound automation take",      "BOFU",  "objection_page"),
        ("outbound automation cost",                    "BOFU",  "bofu_page"),
        ("sales automation platform demo",              "SQL",   "bofu_page"),
        ("predictable pipeline demo",                   "SQL",   "bofu_page"),
        ("workflow orchestration pricing",              "BOFU",  "bofu_page"),
    ]

    # Short-tail core terms (1-2 words) for broad commercial capture
    SHORT_TAIL_TERMS = [
        "outbound automation",
        "sales automation",
        "pipeline generation",
        "workflow orchestration",
        "lead enrichment",
        "crm automation",
        "sdr automation",
        "revops automation",
        "cold outreach",
        "sales workflow",
        "revenue operations",
        "signal based outbound",
        "sales engagement",
        "gtm automation",
    ]

    # Medium-tail patterns that expand core terms into natural 3-4 word phrases
    MEDIUM_TAIL_PATTERNS = [
        ("{term} platform",               "commercial",     "landing_page",    "solution-aware"),
        ("{term} software",               "commercial",     "comparison_page", "solution-aware"),
        ("{term} tools",                  "commercial",     "comparison_page", "solution-aware"),
        ("{term} system",                 "commercial",     "use_case_page",   "solution-aware"),
        ("best {term}",                   "commercial",     "comparison_page", "solution-aware"),
        ("{term} for b2b",               "commercial",     "use_case_page",   "solution-aware"),
        ("{term} for saas companies",     "commercial",     "use_case_page",   "solution-aware"),
        ("{term} for startups",           "commercial",     "use_case_page",   "solution-aware"),
        ("{term} 2026",                   "informational",  "blog_post",       "problem-aware"),
        ("{term} pricing",                "transactional",  "bofu_page",       "decision"),
        ("{term} demo",                   "transactional",  "bofu_page",       "decision"),
        ("{term} guide",                  "informational",  "blog_post",       "problem-aware"),
    ]

    # Local market keywords — positions pipeleap as the best global platform,
    # while capturing local search intent (e.g. "best outbound automation in uk").
    LOCAL_MARKETS = [
        ("uk",        ["in uk", "for uk businesses", "uk"]),
        ("australia", ["in australia", "for australian businesses", "australia"]),
        ("canada",    ["in canada", "for canadian businesses", "canada"]),
        ("india",     ["in india", "for indian businesses", "india"]),
        ("singapore", ["in singapore", "for singapore businesses", "singapore"]),
    ]

    # Navigational queries for brand-aware searchers
    NAVIGATIONAL_TERMS = [
        "pipeleap",
        "pipeleap pricing",
        "pipeleap demo",
        "pipeleap login",
        "pipeleap reviews",
        "pipeleap platform",
        "pipeleap gtm audit",
        "pipeleap outbound automation",
        "pipeleap workflow orchestration",
    ]

    # Core terms to generate question + long-tail variants from
    CORE_TERMS = [
        "outbound sales automation",
        "outbound automation",
        "signal-based outbound",
        "sales workflow automation",
        "pipeline generation",
        "workflow orchestration",
        "lead enrichment automation",
        "crm automation",
        "sdr automation",
        "revenue operations automation",
        "automated outbound emails",
        "outbound without an sdr",
        "predictable pipeline",
        "n8n sales automation",
        "outbound sequencing automation",
    ]

    def build_matrix(self) -> list[dict[str, Any]]:
        """Return the full keyword matrix with intent and source tags."""
        entries: list[dict[str, Any]] = []

        entries.extend(self._role_keywords())
        entries.extend(self._use_case_keywords())
        entries.extend(self._competitor_keywords())
        entries.extend(self._problem_keywords())
        entries.extend(self._role_x_use_case_keywords())
        entries.extend(self._role_x_competitor_keywords())
        entries.extend(self._short_tail_keywords())
        entries.extend(self._medium_tail_keywords())
        entries.extend(self._navigational_keywords())
        entries.extend(self._local_market_keywords())
        # Existing gap fixes
        entries.extend(self._long_tail_keywords())
        entries.extend(self._question_keywords())
        entries.extend(self._industry_vertical_keywords())
        entries.extend(self._bofu_keywords())
        entries.extend(self._stage_natural_language_keywords())

        seen: set[str] = set()
        deduped = []
        for entry in entries:
            kw = entry["keyword"].lower().strip()
            if kw not in seen:
                seen.add(kw)
                deduped.append(entry)

        return sorted(deduped, key=lambda e: self._priority_score(e), reverse=True)

    # ─── Role keywords ────────────────────────────────────────────────────────

    def _role_keywords(self) -> list[dict[str, Any]]:
        entries = []
        for role_key, role in ROLES.items():
            for kw in role["keywords"]:
                entries.append({
                    "keyword": kw,
                    "intent": "transactional",
                    "source": f"role:{role_key}",
                    "role": role_key,
                    "page_type": "role_page",
                    "slug": role["slug"],
                    "funnel_stage": "decision",
                })
            # Cross with SaaS modifiers
            for mod in self.SAAS_MODIFIERS[:2]:
                entries.append({
                    "keyword": f"outbound automation {mod} {role['abbreviation'].lower()}",
                    "intent": "commercial",
                    "source": f"role:{role_key}:saas_matrix",
                    "role": role_key,
                    "page_type": "role_page",
                    "slug": role["slug"],
                    "funnel_stage": "solution-aware",
                })
        return entries

    # ─── Use case keywords ────────────────────────────────────────────────────

    def _use_case_keywords(self) -> list[dict[str, Any]]:
        entries = []
        for uc in USE_CASES:
            for kw in uc["keywords"]:
                entries.append({
                    "keyword": kw,
                    "intent": "transactional",
                    "source": f"use_case:{uc['slug']}",
                    "use_case": uc["slug"],
                    "page_type": "use_case_page",
                    "slug": uc["slug"],
                    "funnel_stage": "decision",
                })
        return entries

    # ─── Competitor keywords ──────────────────────────────────────────────────

    def _competitor_keywords(self) -> list[dict[str, Any]]:
        entries = []
        for name, data in COMPETITORS.items():
            slug_name = name.lower().replace(".", "-").replace(" ", "-")
            # vs pages
            for kw in [
                f"pipeleap vs {name.lower()}",
                f"{name.lower()} vs pipeleap",
                f"pipeleap vs {name.lower()} for saas",
                f"pipeleap vs {name.lower()} comparison",
            ]:
                entries.append({
                    "keyword": kw,
                    "intent": "commercial",
                    "source": f"competitor:{name}:vs",
                    "competitor": name,
                    "page_type": "comparison_page",
                    "slug": data["slug_vs"],
                    "funnel_stage": "decision",
                })
            # alternative pages
            for kw in [
                f"{name.lower()} alternative",
                f"{name.lower()} alternative for saas",
                f"best {name.lower()} alternative",
                f"{name.lower()} alternative outbound automation",
                f"replace {name.lower()} with pipeleap",
                f"switch from {name.lower()} to pipeleap",
            ]:
                entries.append({
                    "keyword": kw,
                    "intent": "commercial",
                    "source": f"competitor:{name}:alt",
                    "competitor": name,
                    "page_type": "alternative_page",
                    "slug": data["slug_alt"],
                    "funnel_stage": "decision",
                })
        # Category-level keywords
        for category, tools in COMPETITOR_CATEGORIES.items():
            entries.append({
                "keyword": f"best {category} tools for saas outbound",
                "intent": "commercial",
                "source": f"category:{category}",
                "page_type": "comparison_page",
                "funnel_stage": "solution-aware",
                "slug": f"best-{category}-tools-saas",
            })
        return entries

    # ─── Problem page keywords ────────────────────────────────────────────────

    def _problem_keywords(self) -> list[dict[str, Any]]:
        entries = []
        for pp in PROBLEM_PAGES:
            for kw in pp["keywords"]:
                entries.append({
                    "keyword": kw,
                    "intent": "informational",
                    "source": f"problem:{pp['slug']}",
                    "page_type": "problem_page",
                    "slug": pp["slug"],
                    "funnel_stage": "problem-aware",
                })
        return entries

    # ─── Role × Use Case cross-product ───────────────────────────────────────

    def _role_x_use_case_keywords(self) -> list[dict[str, Any]]:
        entries = []
        for role_key, role in ROLES.items():
            for uc in USE_CASES[:3]:  # top 3 use cases per role
                kw = f"{uc['primary_keyword']} for {role['abbreviation'].lower()}"
                entries.append({
                    "keyword": kw,
                    "intent": "transactional",
                    "source": f"matrix:role×uc:{role_key}:{uc['slug']}",
                    "role": role_key,
                    "use_case": uc["slug"],
                    "page_type": "use_case_page",
                    "slug": uc["slug"],
                    "funnel_stage": "decision",
                })
        return entries

    # ─── Role × Competitor cross-product ─────────────────────────────────────

    def _role_x_competitor_keywords(self) -> list[dict[str, Any]]:
        entries = []
        top_competitors = list(COMPETITORS.keys())[:5]
        for role_key, role in ROLES.items():
            for name in top_competitors:
                slug_name = name.lower().replace(".", "-")
                kw = f"{name.lower()} alternative for {role['abbreviation'].lower()}"
                entries.append({
                    "keyword": kw,
                    "intent": "commercial",
                    "source": f"matrix:role×comp:{role_key}:{name}",
                    "role": role_key,
                    "competitor": name,
                    "page_type": "alternative_page",
                    "slug": f"{slug_name}-alternative-for-{ROLES[role_key]['slug'].split('for-')[1]}",
                    "funnel_stage": "decision",
                })
        return entries

    # ─── Long-tail expansion ──────────────────────────────────────────────────
    # Generates 4-6 word variants from core terms using natural modifiers.
    # These are the lowest-competition, highest-conversion keywords because
    # they match very specific search intent with minimal competing pages.

    def _long_tail_keywords(self) -> list[dict[str, Any]]:
        entries = []
        for term in self.CORE_TERMS:
            for mod in self.LONG_TAIL_MODIFIERS:
                kw = f"{term} {mod}"
                entries.append({
                    "keyword": kw,
                    "intent": "commercial" if any(w in mod for w in ["without", "using", "with", "for"]) else "informational",
                    "source": "long_tail:expansion",
                    "page_type": "use_case_page",
                    "funnel_stage": "solution-aware",
                    "word_count": len(kw.split()),
                })
        return entries

    # ─── Question keyword patterns ────────────────────────────────────────────
    # Systematically generates "what is X", "how to X", "why is X" variants.
    # These target Google's PAA boxes, featured snippets, and voice search.

    def _question_keywords(self) -> list[dict[str, Any]]:
        entries = []
        for prefix in self.QUESTION_PREFIXES:
            for term in self.CORE_TERMS[:8]:  # top 8 terms to avoid explosion
                kw = f"{prefix} {term}"
                intent = "informational" if prefix in ("what is", "what does", "why is", "how does") else "commercial"
                entries.append({
                    "keyword": kw,
                    "intent": intent,
                    "source": "question:pattern",
                    "page_type": "glossary_page" if prefix in ("what is", "what does") else "blog_post",
                    "funnel_stage": "problem-aware",
                    "snippet_format": "paragraph" if prefix.startswith("what") else "list",
                })
        # High-value individual questions not covered by the matrix
        specific_questions = [
            ("what is a workflow orchestration system",         "glossary_page"),
            ("what is signal-based outbound sales",             "glossary_page"),
            ("what is predictable pipeline generation",         "glossary_page"),
            ("why does outbound have low reply rates",          "blog_post"),
            ("why is my outbound email reply rate low",         "blog_post"),
            ("how do sdrs spend their time",                    "blog_post"),
            ("how many outbound emails should an sdr send",     "blog_post"),
            ("when should saas companies hire an sdr",          "blog_post"),
            ("what is a good outbound conversion rate for saas","blog_post"),
            ("how to build an outbound sales team from scratch","blog_post"),
            ("what tools do revops teams use for outbound",     "blog_post"),
            ("how to scale outbound without hiring more sdrs",  "blog_post"),
            ("what is the best outbound stack for saas 2025",   "comparison_page"),
            ("how to automate lead enrichment for b2b sales",   "use_case_page"),
            ("what is the difference between zapier and n8n for sales", "comparison_page"),
        ]
        for kw, page_type in specific_questions:
            intent = "commercial" if page_type in ("comparison_page", "use_case_page") else "informational"
            entries.append({
                "keyword": kw,
                "intent": intent,
                "source": "question:specific",
                "page_type": page_type,
                "funnel_stage": "problem-aware",
            })
        return entries

    # ─── Industry vertical keywords ───────────────────────────────────────────
    # Generates industry-specific variants of core terms.
    # "outbound automation for fintech" etc. have near-zero competition.

    def _industry_vertical_keywords(self) -> list[dict[str, Any]]:
        entries = []
        top_terms = ["outbound automation", "pipeline generation", "sales workflow automation", "lead enrichment automation"]
        for term in top_terms:
            for industry in self.INDUSTRY_VERTICALS:
                kw = f"{term} for {industry}"
                entries.append({
                    "keyword": kw,
                    "intent": "commercial",
                    "source": f"industry:{industry}",
                    "page_type": "use_case_page",
                    "funnel_stage": "solution-aware",
                    "industry": industry,
                })
        return entries

    # ─── BOFU keywords ────────────────────────────────────────────────────────
    # Registers demo, ROI, pricing, and objection query targets in the matrix.
    # These were missing — BOFU pages were generated but not keyword-tracked.

    def _bofu_keywords(self) -> list[dict[str, Any]]:
        entries = []
        stage_to_funnel = {"SQL": "decision", "BOFU": "decision"}
        stage_to_intent = {"SQL": "transactional", "BOFU": "commercial"}
        for kw, stage, page_type in self.BOFU_QUERIES:
            entries.append({
                "keyword": kw,
                "intent": stage_to_intent.get(stage, "commercial"),
                "source": f"bofu:{stage.lower()}",
                "page_type": page_type,
                "funnel_stage": stage_to_funnel.get(stage, "decision"),
            })
        return entries

    # ─── Short-tail keywords ───────────────────────────────────────────────────
    # Generates broad 1-2 word commercial terms for category-level capture.
    # These have high competition but signal topical authority to search engines.

    def _short_tail_keywords(self) -> list[dict[str, Any]]:
        entries = []
        for term in self.SHORT_TAIL_TERMS:
            entries.append({
                "keyword": term,
                "intent": "commercial",
                "source": "short_tail:core",
                "page_type": "use_case_page",
                "funnel_stage": "solution-aware",
                "word_count": len(term.split()),
            })
        return entries

    # ─── Medium-tail keywords ──────────────────────────────────────────────────
    # Expands core terms into natural 3-4 word phrases using pattern templates.
    # These bridge short-tail breadth and long-tail specificity.

    def _medium_tail_keywords(self) -> list[dict[str, Any]]:
        entries = []
        for term in self.CORE_TERMS:
            for template, intent, page_type, funnel_stage in self.MEDIUM_TAIL_PATTERNS:
                kw = template.format(term=term)
                entries.append({
                    "keyword": kw,
                    "intent": intent,
                    "source": "medium_tail:pattern",
                    "page_type": page_type,
                    "funnel_stage": funnel_stage,
                    "word_count": len(kw.split()),
                })
        return entries

    # ─── Navigational keywords ─────────────────────────────────────────────────
    # Captures brand-aware searchers who already know Pipeleap.
    # Low volume initially but essential as brand awareness grows.

    def _navigational_keywords(self) -> list[dict[str, Any]]:
        entries = []
        for kw in self.NAVIGATIONAL_TERMS:
            entries.append({
                "keyword": kw,
                "intent": "navigational",
                "source": "brand:navigational",
                "page_type": "landing_page",
                "funnel_stage": "decision",
            })
        return entries

    # ─── Local market keywords ─────────────────────────────────────────────────
    # Positions pipeleap globally while capturing country-level search intent.
    # "best outbound automation platform in uk" — not "uk-specific tool".

    def _local_market_keywords(self) -> list[dict[str, Any]]:
        entries = []
        local_terms = [
            "outbound automation platform",
            "sales automation platform",
            "pipeline generation platform",
            "workflow orchestration platform",
            "lead enrichment platform",
            "sdr automation platform",
        ]
        for term in local_terms:
            entries.append({
                "keyword": f"best {term}",
                "intent": "commercial",
                "source": "local_market:global",
                "page_type": "landing_page",
                "funnel_stage": "solution-aware",
            })
            for market_key, modifiers in self.LOCAL_MARKETS:
                for mod in modifiers:
                    kw = f"best {term} {mod}"
                    entries.append({
                        "keyword": kw,
                        "intent": "commercial",
                        "source": f"local_market:{market_key}",
                        "page_type": "landing_page",
                        "funnel_stage": "solution-aware",
                        "market": market_key,
                    })
        return entries

    # ─── Stage-specific natural language keywords ─────────────────────────────
    # Replaces the old slug-based stage matrix that produced unnatural queries
    # like "outbound automation platform for enterprise-saas".

    def _stage_natural_language_keywords(self) -> list[dict[str, Any]]:
        entries = []
        stage_patterns = [
            # (keyword_template, intent, page_type, funnel_stage)
            ("outbound automation for {arr} arr saas",          "commercial", "use_case_page",    "solution-aware"),
            ("{persona} outbound automation",                   "transactional", "role_page",     "decision"),
            ("pipeline generation for {stage_label}",          "commercial", "use_case_page",    "solution-aware"),
            ("outbound without {negative}",                    "commercial", "use_case_page",    "solution-aware"),
            ("sales automation for {stage_label} companies",   "commercial", "use_case_page",    "solution-aware"),
        ]
        stage_fills = [
            {"arr": "0-1m", "stage_label": "early stage saas", "persona": "founder", "negative": "an sdr team"},
            {"arr": "1-10m", "stage_label": "growth stage saas", "persona": "vp sales", "negative": "adding headcount"},
            {"arr": "10m+", "stage_label": "enterprise saas", "persona": "cro", "negative": "tool fragmentation"},
        ]
        for tmpl, intent, page_type, funnel_stage in stage_patterns:
            for fills in stage_fills:
                try:
                    kw = tmpl.format(**fills)
                    entries.append({
                        "keyword": kw,
                        "intent": intent,
                        "source": "stage:natural_language",
                        "page_type": page_type,
                        "funnel_stage": funnel_stage,
                    })
                except KeyError:
                    pass
        return entries

    @staticmethod
    def _priority_score(entry: dict[str, Any]) -> int:
        intent_scores = {"transactional": 3, "commercial": 2, "informational": 1}
        stage_scores = {"decision": 3, "solution-aware": 2, "problem-aware": 1}
        # Long-tail bonus: 4+ word queries have lower competition
        kw = entry.get("keyword", "")
        long_tail_bonus = 1 if len(kw.split()) >= 4 else 0
        return (
            intent_scores.get(entry.get("intent", ""), 0) +
            stage_scores.get(entry.get("funnel_stage", ""), 0) +
            long_tail_bonus
        )
