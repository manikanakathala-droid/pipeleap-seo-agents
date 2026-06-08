from __future__ import annotations

from datetime import date as _date
from typing import Any

from core.blog_content_engine import BlogContentEngine
from utils.models import ContentAsset, ContentBrief, KeywordCluster, LinkSuggestion
from utils.stage_messaging import STAGES, STAGE_CTA, STAGE_BEFORE_AFTER
from utils.text import slugify, title_case_keyword


import re as _re


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

_EXTRA_FAQS: list[tuple[str, str]] = [
    (
        "How long does implementation take?",
        "Most teams are running their first workflow within 48 hours. The full operational layer — enrichment, CRM sync, routing, and workflow governance — typically goes live within one week, depending on CRM complexity.",
    ),
    (
        "Do I need technical skills to build workflows?",
        "No. Pipeleap uses a visual workflow builder that non-technical sales ops and growth teams can configure without engineering support. For advanced custom logic, the underlying n8n engine is fully accessible.",
    ),
    (
        "Can Pipeleap replace my existing CRM?",
        "Pipeleap complements your CRM rather than replacing it. It acts as an operational layer on top, handling enrichment, routing, and workflow governance while writing clean, structured data back into your CRM in real time.",
    ),
    (
        "What data sources does Pipeleap support?",
        "Pipeleap connects to all major enrichment providers, CRMs, sequencers, and intent data platforms. Custom integrations are available via the n8n connector library, which supports 400+ apps.",
    ),
    (
        "How does Pipeleap handle data compliance?",
        "All data is processed under configurable governance rules. You can set suppression lists, region-based routing, GDPR opt-out enforcement, and field-level write permissions to ensure compliance at every workflow step.",
    ),
]


class ContentEngine:
    """Generates Pipeleap-specific revenue-first SEO content assets."""

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger
        self.site = config.get("site", {})
        self.cta = self.site.get("cta", {})
        self.personas = self.site.get("target_personas", ["Sales ops teams"])
        self.features = self.site.get("core_features", [])
        self.conversion_pages = config.get("seo", {}).get("conversion_pages", [])
        # Tracks 600-char intro samples to detect near-duplicate bodies at runtime
        self._generated_samples: list[str] = []
        # Advanced GSC-aware content engine , replaces template renderers for blogs,
        # comparisons, and use-case pages.
        self._blog_engine = BlogContentEngine(config, logger)

    def build_brief(self, cluster: KeywordCluster, page_type: str) -> ContentBrief:
        persona = self._persona_for_cluster(cluster.cluster_name)
        unique_angle = self._unique_angle(cluster, page_type)
        schema_types = {
            "blog_post": ["Article", "FAQPage"],
            "landing_page": ["WebPage", "SoftwareApplication", "FAQPage"],
            # comparison_page schema removed
            "use_case_page": ["WebPage", "FAQPage"],
            "case_study": ["Article", "FAQPage"],
        }.get(page_type, ["WebPage"])

        internal_targets = [page["url"] for page in self.conversion_pages[:3] if isinstance(page, dict) and page.get("url")]
        stage = self._detect_stage(cluster.primary_keyword)

        return ContentBrief(
            primary_keyword=cluster.primary_keyword,
            keyword_cluster=cluster.cluster_name,
            secondary_keywords=[item.keyword for item in cluster.opportunities[1:5]],
            target_persona=persona,
            page_type=page_type,
            funnel_stage=cluster.opportunities[0].funnel_stage,
            conversion_goal=cluster.conversion_goal,
            unique_angle=unique_angle,
            internal_link_targets=internal_targets,
            cta_label=self._get_safe_cta(page_type),
            schema_types=schema_types,
            stage=stage,
        )

    def _get_safe_cta(self, page_type: str) -> str:
        label = self.cta.get("primary_label", "Book a demo")
        if page_type == "blog_post":
            # Strict user requirement: No hard-sell CTAs on blogs
            bad_ctas = ["book a demo", "free trial", "start free trial", "get a demo"]
            if label.lower() in bad_ctas:
                return "See how Pipeleap works"
        return label

    def generate_blog_post(self, cluster: KeywordCluster) -> ContentAsset:
        # ── Delegate to advanced GSC-aware engine ──────────────────────────
        asset = self._blog_engine.generate_blog(cluster)

        # Dedup gate against session-level samples
        if self._is_near_duplicate(asset.body_markdown):
            self.logger.warning("Near-duplicate detected , suppressing blog: %s", cluster.primary_keyword)
            asset.uniqueness_score = 0.0
            return asset

        # One CTA per blog , cta_variants must be empty so the CMS renders no extra buttons
        asset.cta_variants = []
        asset.hreflang_hints = self._hreflang_hints(asset.slug)
        asset.body_markdown = _strip_formatting(asset.body_markdown)
        return asset

    def generate_use_case_page(self, cluster: KeywordCluster) -> ContentAsset:
        asset = self._blog_engine.generate_use_case(cluster)
        if self._is_near_duplicate(asset.body_markdown):
            self.logger.warning("Near-duplicate detected , suppressing use-case: %s", cluster.primary_keyword)
            asset.uniqueness_score = 0.0
            return asset
        asset.cta_variants = []
        asset.hreflang_hints = self._hreflang_hints(asset.slug)
        asset.body_markdown = _strip_formatting(asset.body_markdown)
        return asset

    def generate_case_study_page(self, cluster: KeywordCluster) -> ContentAsset:
        asset = self._blog_engine.generate_case_study(cluster)
        if self._is_near_duplicate(asset.body_markdown):
            self.logger.warning("Near-duplicate detected, suppressing case-study: %s", cluster.primary_keyword)
            asset.uniqueness_score = 0.0
            return asset
        asset.cta_variants = []
        asset.hreflang_hints = self._hreflang_hints(asset.slug)
        asset.body_markdown = _strip_formatting(asset.body_markdown)
        return asset

    # ── Legacy template renderers , BLOCKED ───────────────────────────────────
    # The methods below (_render_blog_body, _render_use_case_body)
    # are no longer called by any production path.
    # All generation now routes through BlogContentEngine.
    # They are retained here only as an audit trail and will be removed once
    # the new engine has completed a full production cycle.

    def _render_blog_body(self, brief: ContentBrief, title: str) -> str:
        secondary = ", ".join(brief.secondary_keywords[:2]) if brief.secondary_keywords else "workflow orchestration"
        
        # Unique Intro Hooks
        intro_variations = [
            f"Revenue teams searching for **{brief.primary_keyword}** do not want another disconnected tool. They need a system that connects targeting, enrichment, CRM updates, routing, and follow-up without operational drag.",
            f"If you are evaluating **{brief.primary_keyword}**, you've likely hit the 'fragmentation ceiling' where your sales stack is too complex to manage. You need a unified layer that governs your entire pipeline.",
            f"Mastering **{brief.primary_keyword}** is the difference between a scaling revenue engine and a manual bottleneck. Most teams struggle because they stitch tools together; we believe in one unified OS.",
            f"The goal of **{brief.primary_keyword}** is simple: more pipeline with less manual effort. But achieving this requires more than just a sequence; it requires a governed revenue workflow."
        ]
        intro = intro_variations[len(brief.primary_keyword) % len(intro_variations)]

        # RevOps Pain Variations
        pain_variations = [
            f"Most teams hit a ceiling when sales operations live across spreadsheets, enrichment tools, point integrations, and manual CRM cleanup. {self.site.get('brand', 'Pipeleap')} positions this motion as one orchestrated revenue workflow.",
            f"Scaling sales operations is impossible when your data and execution layers are disconnected. {self.site.get('brand', 'Pipeleap')} solves the {brief.primary_keyword} bottleneck by unifying targeting, enrichment, and CRM sync into a single governed system.",
            f"Fragmented sales stacks create 'tool fatigue' and high operational drag. For teams looking at {brief.primary_keyword}, the goal isn't more software, it's a unified operating model that drives predictable pipeline."
        ]
        pain_point = pain_variations[len(brief.primary_keyword) % len(pain_variations)]

        # Section variations to reduce duplication
        gaps_variations = [
            [
                "- Lead data arrives too late for fast revenue execution.",
                "- CRM ownership and stage updates are inconsistent.",
                "- Sequencing logic is brittle and hard to govern.",
                "- RevOps cannot scale experiments without rebuilding workflows."
            ],
            [
                "- Manual research slows down the sales cycle.",
                "- Data decay leads to wasted effort and poor contact quality.",
                "- Fragmented tools create data silos and poor reporting.",
                "- SDRs spend more time clicking than having conversations."
            ],
            [
                "- Technical debt in your automation prevents fast pivot.",
                "- Enrichment costs are high but utilization is low.",
                "- Inaccurate routing leads to lost demo opportunities.",
                "- Reporting on pipeline velocity is nearly impossible."
            ]
        ]
        # Use a stable random selection based on the keyword
        gaps = gaps_variations[len(brief.primary_keyword) % len(gaps_variations)]

        # Workflow variations
        workflow_variations = [
            [
                "- Triggering from intent, form fills, lists, or enrichment sources.",
                "- Multi-step data enrichment and qualification.",
                "- CRM write-back with ownership, stage, and lifecycle logic.",
                "- Reply routing, task creation, and demo-booking handoffs."
            ],
            [
                "- Automated signal capture from 1st and 3rd party sources.",
                "- Account-level scoring and persona-based filtering.",
                "- Real-time CRM syncing to prevent duplicate outreach.",
                "- Multi-channel outreach triggered by clean, enriched data."
            ],
            [
                "- Governance layers to ensure data compliance and quality.",
                "- Dynamic routing based on account owner or sales territory.",
                "- Feedback loops that update lead status based on engagement.",
                "- Unified reporting across all automation touchpoints."
            ]
        ]
        workflow = workflow_variations[len(brief.primary_keyword) % len(workflow_variations)]

        # Sequence variations
        sequence_variations = [
            [
                "1. Define the signal that should trigger the workflow.",
                "2. Add enrichment layers before any outreach step fires.",
                "3. Write structured lifecycle data back into the CRM.",
                "4. Route ready accounts into the right workflow.",
                "5. Review reply, bounce, and demo-booking feedback weekly."
            ],
            [
                "1. Map your manual process to identify automation bottlenecks.",
                "2. Integrate your CRM with a unified workflow engine.",
                "3. Configure data validation rules to maintain hygiene.",
                "4. Launch a small-scale pilot for a specific segment.",
                "5. Optimize based on pipeline conversion, not just volume."
            ]
        ]
        sequence = sequence_variations[len(brief.primary_keyword) % len(sequence_variations)]

        # Stage-specific sections (empty strings are filtered out by the join)
        snippet = self._stage_featured_snippet(brief.stage, brief.primary_keyword) if brief.stage else ""
        stage_data = STAGES.get(brief.stage, {})
        stage_context = (
            f"\n> **{stage_data.get('label', '')} context ({stage_data.get('arr_range', '')}):** "
            f"{stage_data.get('hero_stat', '')}"
        ) if brief.stage else ""

        sections = [
            f"# {title}",
            "",
            *(([snippet, ""] if snippet else [])),
            intro,
            stage_context,
            "",
            f"## Why {brief.primary_keyword} matters for {brief.target_persona}",
            pain_point,
            "",
            "## The operational gaps that block pipeline",
            *gaps,
            "",
            "## What a production-ready workflow should include",
            *workflow,
            "",
            f"## How {self.site.get('brand', 'Pipeleap')} turns {brief.primary_keyword} into a repeatable system",
            f"{brief.unique_angle}",
            "",
            "### Workflow blueprint",
            "```text",
            "Intent or prospect source",
            "  -> Enrichment and validation",
            "  -> Account and contact scoring",
            "  -> CRM sync and ownership routing",
            "  -> Sequencing and workflow execution",
            "  -> Reply handling and meeting creation",
            "  -> Reporting back to RevOps and growth teams",
            "```",
            "",
            "## Recommended implementation sequence",
            *sequence,
            "",
            f"## Related keywords and supporting angles",
            f"Use this page to support adjacent demand such as {secondary}.",
            "",
            "## FAQ",
            f"### Is {brief.primary_keyword} only useful for large sales teams?",
            [
                "No. The fastest ROI usually comes from small RevOps and founder-led teams that need more leverage without growing headcount.",
                "While enterprise teams see massive efficiency gains, the system is designed to help growth-stage startups scale their revenue operations without the technical debt.",
                "It works for any team where manual data movement is slowing down the sales cycle. Small teams actually gain the most 'leverage' from this automation."
            ][len(brief.primary_keyword) % 3],
            "",
            f"### What makes {self.site.get('brand', 'Pipeleap')} different?",
            [
                "It keeps automation close to the actual revenue workflow instead of treating sales, CRM updates, and data movement as separate systems.",
                "We unify the entire revenue operating system, targeting, enrichment, and execution, into one governed layer, replacing fragmented point solutions.",
                "Pipeleap is built for production-grade revenue workflows. It handles the 'edge cases' of CRM sync and routing that simpler tools miss."
            ][len(brief.primary_keyword) % 3],
            "",
            "## Next step",
            self._cta_block(brief.stage),
        ]
        return "\n".join(sections)

    def _render_use_case_body(self, brief: ContentBrief) -> str:

        intro_variations = [
            f"This page targets teams evaluating **{brief.primary_keyword}** because they need a specific outcome: more qualified pipeline with less manual revenue operations work.",
            f"The **{brief.primary_keyword}** use case is critical for modern growth teams. It focuses on taking raw signals and turning them into demo-ready opportunities through governed automation.",
            f"Why is **{brief.primary_keyword}** such a high-priority motion? Because it connects the highest-intent data points directly to your sales sequences without manual handoffs."
        ]
        intro = intro_variations[len(brief.primary_keyword) % len(intro_variations)]

        return "\n".join(
            [
                f"# {title_case_keyword(brief.primary_keyword)}",
                "",
                intro,
                "",
                "## The use case",
                f"{brief.unique_angle}",
                "",
                "## What the workflow should automate",
                "- Prospect intake and list normalization.",
                "- Data enrichment and scoring.",
                "- CRM updates and owner routing.",
                "- Sequence entry and suppression logic.",
                "- Slack, inbox, or task notifications for human handoff.",
                "",
                "## Text-based workflow diagram",
                "```text",
                "Prospect source -> Validation -> Enrichment -> Qualification -> CRM sync ->",
                "Sequence assignment -> Reply routing -> Demo follow-up",
                "```",
                "",
                "## Why this use case converts well",
                "High-intent visitors on use-case pages are already connecting a business problem to a workflow category, which makes these pages strong bridges into demo requests.",
                "",
                "## CTA",
                self._cta_block(brief.stage),
            ]
        )

    def _schema_markup(self, brief: ContentBrief, seo_title: str, meta_description: str) -> list[dict[str, Any]]:
        today = _date.today().isoformat()
        brand = self.site.get("brand", "Pipeleap")
        site_url = self.site.get("site_url", "https://pipeleap.com")
        page_url = f"{site_url.rstrip('/')}/{slugify(brief.primary_keyword)}"
        org_ref = {"@type": "Organization", "name": brand, "url": site_url}

        schema = [
            {
                "@context": "https://schema.org",
                "@type": brief.schema_types[0],
                "name": seo_title,
                "description": meta_description,
                "url": page_url,
                "datePublished": today,
                "dateModified": today,
                "author": org_ref,
                "publisher": org_ref,
            }
        ]
        if "FAQPage" in brief.schema_types:
            schema.append(
                {
                    "@context": "https://schema.org",
                    "@type": "FAQPage",
                    "mainEntity": [
                        {
                            "@type": "Question",
                            "name": f"What is the fastest way to operationalize {brief.primary_keyword}?",
                            "acceptedAnswer": {
                                "@type": "Answer",
                                "text": "Build the workflow end to end so enrichment, CRM sync, and routing share one operating model.",
                            },
                        }
                    ],
                }
            )
        return schema

    def _cta_block(self, stage: str = "") -> str:
        # ONE CTA per post , no secondary link, no alternatives.
        stage_cta = STAGE_CTA.get(stage, {})
        primary_label = stage_cta.get("primary_label") or self.cta.get("primary_label", "Book a demo")
        primary_url = self.cta.get("primary_url", self.site.get("site_url", "https://pipeleap.com"))
        subtext = stage_cta.get("primary_subtext", "")
        cta = f"[{primary_label}]({primary_url})"
        if subtext:
            cta += f", {subtext}"
        return cta

    def _persona_for_cluster(self, cluster_name: str) -> str:
        cluster_lower = cluster_name.lower()
        if "outbound" in cluster_lower or "sdr" in cluster_lower:
            return "Growth marketers and SDR leaders"
        if "crm" in cluster_lower or "revenue" in cluster_lower:
            return "Sales ops teams"
        if "n8n" in cluster_lower:
            return "Technical founders and automation operators"
        return self.personas[0]

    def _unique_angle(self, cluster: KeywordCluster, page_type: str, stage: str = "") -> str:
        base = (
            f"Pipeleap solves the 'tool fatigue' problem for {cluster.cluster_name}. Instead of stitching together "
            f"fragile point solutions for enrichment and CRM routing, teams use Pipeleap's unified n8n-powered "
            f"engine to govern the entire revenue lifecycle in one place."
        )
        if "outbound" in cluster.primary_keyword.lower():
            base = f"Non-selling work is the hidden tax on revenue teams. Pipeleap solves this for {cluster.cluster_name} by unifying signal capture and execution in a single n8n-powered engine."
        elif "enrichment" in cluster.primary_keyword.lower():
            base = f"Enrichment without execution is just more noise. Pipeleap ensures that {cluster.cluster_name} results in actual CRM-ready pipeline by connecting data directly to automated workflows."
        
        if stage:
            stage_data = STAGES.get(stage, {})
            stage_label = stage_data.get("label", "")
            stage_pain = stage_data.get("pain_points", [""])
            stage_outcome = stage_data.get("desired_outcomes", [""])
            if stage_label:
                base = (
                    f"For {stage_label} teams, {base.lower()} "
                    f"The primary pain: {stage_pain[0]}. "
                    f"The outcome: {stage_outcome[0]}."
                )

        if page_type == "use_case_page":
            return f"{base} The use case should show how signal capture, enrichment, routing, and sequencing work flawlessly together when they share the same architecture."
        return base

    @staticmethod
    def _detect_stage(keyword: str) -> str:
        """Infer SaaS stage from keyword signals. Returns 'early', 'growth', 'scale', or ''."""
        kw = keyword.lower()
        early_signals = {"startup", "early stage", "pre-sdr", "founder", "early-stage", "0 to 1", "pre-seed", "seed"}
        growth_signals = {"scale", "series a", "series b", "growing", "sdr team", "growth stage", "growth-stage"}
        scale_signals = {"enterprise", "revops", "multi-territory", "10m", "governance", "at scale"}
        if any(s in kw for s in early_signals):
            return "early"
        if any(s in kw for s in scale_signals):
            return "scale"
        if any(s in kw for s in growth_signals):
            return "growth"
        return ""

    def _stage_featured_snippet(self, stage: str, keyword: str) -> str:
        """Returns a featured-snippet-optimised paragraph (40-60 words) for the given stage."""
        stage_data = STAGES.get(stage, {})
        context = stage_data.get("featured_snippet_context", "")
        if not context:
            return ""
        return (
            f"**What is {keyword}?**\n\n"
            f"{context}\n"
        )

    # ------------------------------------------------------------------ #
    # SGE / Direct answer (P2)                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _direct_answer_block(keyword: str, page_type: str) -> str:
        """40-60 word TL;DR block optimised for Google's AI Overviews and featured snippets."""
        # comparison_page config removed

    def _hreflang_hints(self, slug: str) -> list[dict[str, str]]:
        """Returns hreflang link annotations for the global markets in config."""
        location_codes: list[int] = self.config.get("growth_engine", {}).get(
            "dataforseo_global_location_codes", []
        )
        site_url = self.site.get("site_url", "https://pipeleap.com").rstrip("/")
        page_url = f"{site_url}/{slug}"
        hints: list[dict[str, str]] = [
            {"hreflang": "x-default", "href": page_url},
            {"hreflang": "en", "href": page_url},
        ]
        for code in location_codes:
            lang = self._LOCATION_TO_HREFLANG.get(code)
            if lang:
                hints.append({"hreflang": lang, "href": page_url})
        return hints

    # ------------------------------------------------------------------ #
    # CTA A/B variants (P2)                                               #
    # ------------------------------------------------------------------ #

    def _cta_variants(self, page_type: str, stage: str = "") -> list[dict[str, Any]]:
        """Returns 3 CTA variants for A/B testing. Caller picks one; all are tracked."""
        primary_url = self.cta.get("primary_url", self.site.get("site_url", "https://pipeleap.com"))
        secondary_url = self.cta.get("secondary_url", primary_url)
        funnel_stage = "TOFU" if page_type == "blog_post" else "BOFU" if page_type == "landing_page" else "MOFU"
        variants_by_funnel: dict[str, list[dict[str, Any]]] = {
            "TOFU": [
                {"label": "See how teams build predictable pipeline", "url": secondary_url, "variant": "A"},
                {"label": "Explore the workflow framework", "url": secondary_url, "variant": "B"},
                {"label": "Watch a 3-minute workflow walkthrough", "url": secondary_url, "variant": "C"},
            ],
            "MOFU": [
                {"label": "See how Pipeleap works for your team", "url": primary_url, "variant": "A"},
                {"label": "See Pipeleap in your stack", "url": primary_url, "variant": "B"},
                {"label": "Get a free workflow audit", "url": primary_url, "variant": "C"},
            ],
            "BOFU": [
                {"label": "Book a demo", "url": primary_url, "variant": "A"},
                {"label": "Get a free sales ops audit", "url": primary_url, "variant": "B"},
                {"label": "Book a 30-minute strategy call", "url": primary_url, "variant": "C"},
            ],
        }
        return variants_by_funnel.get(funnel_stage, variants_by_funnel["MOFU"])

    # ------------------------------------------------------------------ #
    # E-E-A-T proof checklist (P1)                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _eeat_checklist(page_type: str) -> list[dict[str, Any]]:
        """Structured proof checklist , each item has a label, status, and instructions."""
        base = [
            {"item": "Author byline", "status": "missing", "instructions": "Add a real RevOps or growth operator byline with LinkedIn or bio link."},
            {"item": "Publication date", "status": "auto-filled", "instructions": "datePublished and dateModified are set in schema. Verify CMS renders them in the HTML head."},
            {"item": "Workflow screenshot", "status": "missing", "instructions": "Insert at least one real product screenshot showing the workflow builder or CRM sync output."},
            {"item": "Outcome proof point", "status": "missing", "instructions": "Add a quantified result: e.g. '40% reply rate lift', 'CRM hygiene improved in 2 weeks', or a named customer quote."},
            {"item": "Last-reviewed date", "status": "missing", "instructions": "Update dateModified each time the page is refreshed. Set a 90-day review reminder."},
        ]
        if page_type == "landing_page":
            base.append({
                "item": "Third-party validation",
                "status": "missing",
                "instructions": "Link to a G2 review, Capterra listing, or press mention on this page.",
            })
        if page_type == "blog_post":
            base.append({
                "item": "Related resource link",
                "status": "missing",
                "instructions": "Link to a case study, template, or documented workflow that supports the post's claims.",
            })
        return base

    # ------------------------------------------------------------------ #
    # Deduplication                                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _word_jaccard(text_a: str, text_b: str) -> float:
        a = set(text_a.lower().split())
        b = set(text_b.lower().split())
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def _is_near_duplicate(self, body: str) -> bool:
        """Returns True if the body is ≥75% similar to a previously generated body."""
        sample = body[:600]
        for existing in self._generated_samples:
            if self._word_jaccard(sample, existing) >= 0.75:
                return True
        self._generated_samples.append(sample)
        return False


    # ------------------------------------------------------------------ #
    # E-E-A-T notes                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _eeat_notes() -> list[str]:
        return [
            "Add a real operator byline tied to RevOps or growth experience.",
            "Include screenshots or workflow diagrams from the actual product before publishing.",
            "Attach proof points such as time saved, reply lift, or CRM hygiene outcomes.",
        ]
