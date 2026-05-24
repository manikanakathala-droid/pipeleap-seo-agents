"""
Pipeleap SaaS Growth Engine — Module Orchestrator.
Drives all page generation, linking, uniqueness scoring, entity linking, and publishing.
Completely self-contained. Modifies NOTHING in the existing agent.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modules.pipeleap_seo_engine.data.authors import get_author_for_page_type
from modules.pipeleap_seo_engine.data.competitors import COMPETITORS
from modules.pipeleap_seo_engine.engines.content_engine import GrowthContentEngine
from modules.pipeleap_seo_engine.engines.entity_linker import SemanticEntityLinker
from modules.pipeleap_seo_engine.engines.keyword_engine import GrowthKeywordEngine
from modules.pipeleap_seo_engine.engines.linking_engine import GrowthLinkingEngine
from modules.pipeleap_seo_engine.engines.refresh_engine import ContentRefreshEngine, CannibalizationDetector
from modules.pipeleap_seo_engine.engines.revenue_attribution import RevenueAttributionEngine
from modules.pipeleap_seo_engine.engines.topical_authority import TopicalAuthorityMapper
from modules.pipeleap_seo_engine.engines.uniqueness_engine import GrowthUniquenessEngine
from modules.pipeleap_seo_engine.engines.ctr_engine import CTREngine
from modules.pipeleap_seo_engine.engines.decay_detector import DecayDetector
from modules.pipeleap_seo_engine.engines.revenue_linker import RevenueLinkingEngine
from modules.pipeleap_seo_engine.engines.content_memory import ContentMemory
from modules.pipeleap_seo_engine.engines.glossary_updater import GlossaryUpdater
from modules.pipeleap_seo_engine.generators.competitor_page import CompetitorPageGenerator
from modules.pipeleap_seo_engine.generators.digital_pr import DigitalPREngine
from modules.pipeleap_seo_engine.generators.glossary_page import GlossaryPageGenerator
from modules.pipeleap_seo_engine.generators.integration_page import IntegrationPageGenerator
from modules.pipeleap_seo_engine.generators.multi_competitor_page import MultiCompetitorPageGenerator
from modules.pipeleap_seo_engine.generators.role_page import RolePageGenerator
from modules.pipeleap_seo_engine.generators.use_case_page import UseCasePageGenerator, ProblemPageGenerator
from modules.pipeleap_seo_engine.generators.tools_page import ToolsPageGenerator
from modules.pipeleap_seo_engine.generators.workflow_recipe import WorkflowRecipeGenerator
from modules.pipeleap_seo_engine.generators.bofu_page import BOFUPageGenerator
from modules.pipeleap_seo_engine.generators.objection_page import ObjectionPageGenerator
from modules.pipeleap_seo_engine.generators.market_page import MarketPageGenerator
from modules.pipeleap_seo_engine.models import GrowthPage, GrowthEngineReport
from modules.pipeleap_seo_engine.connectors.pagespeed import PageSpeedConnector
from modules.pipeleap_seo_engine.connectors.backlink_gap import BacklinkGapConnector
from connectors.free_keyword_connector import FreeKeywordConnector


class GrowthEngineOrchestrator:
    """
    Main orchestrator for the Pipeleap SaaS Growth Engine.
    Runs independently alongside the existing SEO agent.
    """

    def __init__(self, config: dict[str, Any], logger=None) -> None:
        self.config = config
        self.logger = logger
        self.site_config = config.get("site", {})
        self.execution = config.get("execution", {})
        self.module_config = config.get("growth_engine", {})
        self.output_dir = self._resolve_output_dir()
        self._log = self._make_logger()

        # Content engine (shared across all generators)
        content_engine = GrowthContentEngine(self.site_config)

        # Page generators
        self.role_gen = RolePageGenerator(content_engine)
        self.use_case_gen = UseCasePageGenerator(content_engine)
        self.problem_gen = ProblemPageGenerator(content_engine)
        self.competitor_gen = CompetitorPageGenerator(content_engine)
        self.glossary_gen = GlossaryPageGenerator(content_engine)
        self.integration_gen = IntegrationPageGenerator(content_engine)
        self.workflow_gen = WorkflowRecipeGenerator(content_engine)
        self.tools_gen = ToolsPageGenerator(content_engine)
        self.multi_comp_gen = MultiCompetitorPageGenerator(content_engine)
        # BOFU, objection, and global market generators
        self.bofu_gen = BOFUPageGenerator(content_engine)
        self.objection_gen = ObjectionPageGenerator(content_engine)
        self.market_gen = MarketPageGenerator()

        # Engines
        self.keyword_engine = GrowthKeywordEngine()
        self.linking_engine = GrowthLinkingEngine()
        self.uniqueness_engine = GrowthUniquenessEngine()
        self.entity_linker = SemanticEntityLinker(self.site_config.get("site_url", "https://pipeleap.com"))
        self.topical_mapper = TopicalAuthorityMapper()
        self.refresh_engine = ContentRefreshEngine()
        self.cannibalization_detector = CannibalizationDetector()
        self.revenue_engine = RevenueAttributionEngine(
            config.get("integrations", {}).get("analytics", {}).get("conversion_export_path", "")
        )
        self.digital_pr = DigitalPREngine(self.site_config.get("site_url", "https://pipeleap.com"))
        # Revenue-path engines
        self.ctr_engine = CTREngine()
        self.decay_detector = DecayDetector(
            thresholds=config.get("growth_engine", {}).get("decay_thresholds", {})
        )
        self.revenue_linker = RevenueLinkingEngine(
            site_url=self.site_config.get("site_url", "https://pipeleap.com")
        )
        # Content memory — persistent cross-run uniqueness registry
        memory_db = self._resolve_output_dir() / "content_memory.sqlite"
        self.content_memory = ContentMemory(db_path=str(memory_db))
        # Shared registry — canonical slug source shared with GEO agent
        from geo_agent.engines.shared_registry import SharedRegistry
        seo_db_path = self.config.get("execution", {}).get(
            "memory_db", "outputs/pipeleap_seo_memory.sqlite"
        )
        cms_dir = self.config.get("integrations", {}).get("cms", {}).get("publish_dir", "")
        self.shared_registry = SharedRegistry(
            seo_db_path=self._resolve_output_dir().parent / Path(seo_db_path).name,
            cms_publish_dir=cms_dir,
        )
        self.glossary_updater = self._make_glossary_updater()

        growth_cfg = self.module_config
        self.keyword_connector = FreeKeywordConnector()
        from modules.pipeleap_seo_engine.connectors.dataforseo import DataForSEOConnector
        self.dataforseo = DataForSEOConnector(
            login=growth_cfg.get("dataforseo_login", ""),
            password=growth_cfg.get("dataforseo_password", ""),
        )
        self.pagespeed = PageSpeedConnector(
            config.get("integrations", {}).get("pagespeed", {}).get("api_key", "")
        )
        self.backlink_gap = BacklinkGapConnector(
            growth_cfg.get("ahrefs_api_key", ""),
            self.site_config.get("domain", "pipeleap.com"),
        )

    def run(self) -> GrowthEngineReport:
        self._log("Growth Engine starting...")
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = self.output_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Load ALL published slugs from both SQLite + filesystem so the growth
        # engine never regenerates pages already published by any agent.
        existing_slugs: set[str] = self.shared_registry.all_slugs()
        self._log(f"  Shared registry:  {len(existing_slugs)} slugs loaded (SEO + GEO combined)")
        all_pages: list[GrowthPage] = []
        mc = self.module_config

        # ── 1. Core pages ────────────────────────────────────────────────────
        role_pages = self.role_gen.generate_all(existing_slugs)[:mc.get("role_pages_per_run", 5)]
        uc_pages = self.use_case_gen.generate_all(existing_slugs)[:mc.get("use_case_pages_per_run", 5)]
        prob_pages = self.problem_gen.generate_all(existing_slugs)[:mc.get("problem_pages_per_run", 2)]
        all_pages.extend(role_pages + uc_pages + prob_pages)
        self._log(f"  Core pages:       {len(role_pages)} role, {len(uc_pages)} use-case, {len(prob_pages)} problem")

        # ── 2. Competitor pages ──────────────────────────────────────────────
        priority_competitors = mc.get("priority_competitors", list(COMPETITORS.keys()))
        vs_pages = self.competitor_gen.generate_vs_pages(priority_competitors, existing_slugs)[:mc.get("competitor_vs_pages_per_run", 5)]
        alt_pages = self.competitor_gen.generate_alternative_pages(priority_competitors, existing_slugs)[:mc.get("competitor_alt_pages_per_run", 5)]
        multi_pages = self.multi_comp_gen.generate_all(existing_slugs)[:mc.get("multi_competitor_pages_per_run", 4)]
        all_pages.extend(vs_pages + alt_pages + multi_pages)
        self._log(f"  Competitor pages: {len(vs_pages)} vs, {len(alt_pages)} alt, {len(multi_pages)} multi")

        # ── 3. Glossary pages — disabled; glossary is a static frontend feature ─

        # ── 4. Integration pages ──────────────────────────────────────────────
        if mc.get("generate_integrations", True):
            int_pages = self.integration_gen.generate_all(existing_slugs)[:mc.get("integration_pages_per_run", 10)]
            all_pages.extend(int_pages)
            self._log(f"  Integration pages:{len(int_pages)}")

        # ── 5. Workflow recipe pages ──────────────────────────────────────────
        if mc.get("generate_workflows", True):
            wf_pages = self.workflow_gen.generate_all(existing_slugs)[:mc.get("workflow_pages_per_run", 5)]
            all_pages.extend(wf_pages)
            self._log(f"  Workflow recipes: {len(wf_pages)}")

        # ── 5a. Tools pages — differentiated operator guides, one per category ─
        if mc.get("generate_tools_pages", True):
            tools_pages = self.tools_gen.generate_all(existing_slugs)[:mc.get("tools_pages_per_run", 8)]
            all_pages.extend(tools_pages)
            self._log(f"  Tools pages:      {len(tools_pages)}")

        # ── 5b. BOFU pages (demo, ROI, pricing comparison) ───────────────────
        if mc.get("generate_bofu", True):
            bofu_pages = self.bofu_gen.generate_all(existing_slugs)[:mc.get("bofu_pages_per_run", 8)]
            all_pages.extend(bofu_pages)
            self._log(f"  BOFU pages:       {len(bofu_pages)}")

        # ── 5c. Objection / trust pages ──────────────────────────────────────
        if mc.get("generate_objection_pages", True):
            obj_pages = self.objection_gen.generate_all(existing_slugs)[:mc.get("objection_pages_per_run", 4)]
            all_pages.extend(obj_pages)
            self._log(f"  Objection pages:  {len(obj_pages)}")

        # ── 5d. Global market landing pages ──────────────────────────────────
        if mc.get("generate_market_pages", True):
            market_pages_limit = mc.get("market_pages_per_run", 8)
            market_assets = self.market_gen.generate_all(existing_slugs)[:market_pages_limit]
            # Convert ContentAsset → GrowthPage for unified pipeline
            from modules.pipeleap_seo_engine.models import GrowthPage
            for asset in market_assets:
                gp = GrowthPage(
                    slug=asset.slug, page_type=asset.page_type,
                    title=asset.seo_title, seo_title=asset.seo_title,
                    meta_description=asset.meta_description, h1=asset.h1,
                    body_markdown=asset.body_markdown, schema_markup=asset.schema_markup or [],
                    call_to_action=asset.call_to_action, primary_keyword=asset.source_keywords[0] if asset.source_keywords else asset.slug,
                    target_keywords=asset.source_keywords, internal_links=[],
                    intent="commercial", topical_pillar="outbound-automation",
                )
                all_pages.append(gp)
                existing_slugs.add(asset.slug)
            self._log(f"  Market pages:     {len(market_assets)} global market pages")

        # ── 6. Wire author info & Apply Quality Filters ───────────────────────
        for page in all_pages:
            if not page.author_name:
                author = get_author_for_page_type(page.page_type)
                page.author_name = author["name"]
                page.author_slug = author["slug"]
            # Apply quality filters to remove broken sentences and negative positioning
            page.body_markdown = self.role_gen.ce.apply_quality_filters(page.body_markdown)

        # ── 7. Content uniqueness — six-layer pre-publish gate ───────────────
        # Load full cross-run history from persistent ContentMemory.
        # Fix applied: corpus_texts stores RAW TEXT not SHA-256 hashes.
        # The old code stored hashes → _shingle(hash) = one token → Jaccard
        # similarity was always 0 → every page scored 1.0 (dedup never fired).
        self.content_memory.load()
        accepted_pages: list[GrowthPage] = []
        rejected_pages: list[GrowthPage] = []

        for page in all_pages:
            assessment = self.content_memory.assess(page)
            score = assessment.get("page_similarity_score", 1.0)
            page.uniqueness_score = score

            if assessment["publish"]:
                accepted_pages.append(page)
                self.content_memory.register(page, run_id)
            else:
                rejected_pages.append(page)
                self.content_memory.record_rejection(page, assessment)
                self._log(
                    f"  REJECTED {page.slug}: "
                    + "; ".join(assessment.get("flags", ["low uniqueness"]))[:120]
                )

        all_pages = accepted_pages
        mem_report = self.content_memory.run_report()
        avg_unique = round(
            sum(p.uniqueness_score for p in all_pages) / max(len(all_pages), 1), 3
        )
        self._log(
            f"  Uniqueness gate:  {mem_report['accepted']} accepted, "
            f"{mem_report['rejected']} rejected "
            f"(avg score={avg_unique}, cross-run corpus={mem_report['corpus_size']})"
        )

        # ── 8. Semantic entity linking ────────────────────────────────────────
        total_links_injected = 0
        for page in all_pages:
            updated_body, count = self.entity_linker.inject(page.body_markdown, page.slug, page.primary_keyword)
            page.body_markdown = updated_body
            total_links_injected += count
        self._log(f"  Entity links:     {total_links_injected} injected across {len(all_pages)} pages")

        # ── 9. Internal linking — structural rules ────────────────────────────
        link_map = self.linking_engine.build(all_pages)
        for page in all_pages:
            page.internal_links = link_map.get(page.slug, [])

        # ── 9b. Revenue path linking — TOFU→MOFU→BOFU nurture blocks ─────────
        all_pages = self.revenue_linker.inject(all_pages)
        self._log(f"  Revenue path links injected across {len(all_pages)} pages")

        # ── 10. Topical authority tracking ────────────────────────────────────
        self.topical_mapper.register_pages(all_pages)
        topical_coverage = self.topical_mapper.coverage_report()

        # ── 11. Cannibalization — in-run + cross-run ─────────────────────────
        page_dicts = [p.to_dict() for p in all_pages]
        cannibalization_issues = self.cannibalization_detector.detect(page_dicts)
        # Cross-run: check new pages against ALL historically published keywords
        cross_run_issues = self.content_memory.detect_cannibalization(all_pages)
        cannibalization_issues = cannibalization_issues + [
            i for i in cross_run_issues if i not in cannibalization_issues
        ]
        if cannibalization_issues:
            self._log(f"  Cannibalization:  {len(cannibalization_issues)} issues "
                      f"({sum(1 for i in cross_run_issues)} cross-run)")

        # ── 12. Refresh analysis + GSC decay detection ────────────────────────
        existing_pages = self._load_existing_pages()
        refresh_queue = self.refresh_engine.analyze(existing_pages, [])
        if refresh_queue:
            self._log(f"  Refresh queue:    {len(refresh_queue)} pages need updating")

        # GSC decay detection: compare current vs previous period (if GSC data available)
        decay_signals = []
        gsc_current: list[dict] = []
        try:
            gsc_current = self._load_gsc_period("current")
            gsc_previous = self._load_gsc_period("previous")
            if gsc_current and gsc_previous:
                published_slugs = {p.slug for p in all_pages}
                decay_signals = self.decay_detector.detect(gsc_current, gsc_previous, published_slugs)
                if decay_signals:
                    self._log(f"  Decay signals:    {len(decay_signals)} pages with declining performance")
        except Exception as exc:
            self._log(f"  Decay detection skipped: {exc}")

        # ── 12a. Refresh stale / decayed pages ───────────────────────────────
        refreshed_pages = []
        if refresh_queue:
            from core.blog_content_engine import BlogContentEngine
            blog_engine = BlogContentEngine(self.config, self.logger or __import__("logging").getLogger(__name__))
            gsc_map = {row["query"].lower(): row for row in (gsc_current or []) if row.get("query")}
            for entry in refresh_queue[:mc.get("refresh_per_run", 3)]:
                primary_kw = entry.get("primary_keyword", "")
                if not primary_kw:
                    continue
                cluster = self._make_refresh_cluster(primary_kw, entry.get("page_type", "blog_post"))
                gsc_row = gsc_map.get(primary_kw.lower())
                try:
                    from datetime import date as _rdate
                    asset = blog_engine.generate_blog(cluster, gsc_row)
                    if asset.body_markdown:
                        asset.date_modified = _rdate.today().isoformat()
                        refreshed_pages.append(asset)
                except Exception as exc:
                    self._log(f"  Refresh failed for '{primary_kw}': {exc}")
            self._log(f"  Refreshed:        {len(refreshed_pages)} pages regenerated")

        # ── 12b. CTR enrichment — inject title variants + PAA + snippet type ─
        ctr_enrichments: dict[str, dict] = {}
        for page in all_pages:
            try:
                enrichment = self.ctr_engine.enrich_page(page)
                ctr_enrichments[page.slug] = enrichment
                # Inject snippet block at top of body for eligible pages
                if enrichment.get("ctr_score", 0) > 0.6:
                    page.body_markdown = self.ctr_engine.inject_snippet_block(
                        page.body_markdown, page.page_type, page.primary_keyword
                    )
            except Exception:
                pass
        if ctr_enrichments:
            self._log(f"  CTR enrichments:  {len(ctr_enrichments)} pages enriched with title variants + PAA")

        # ── 13. Keyword matrix enrichment (Google Trends + Autocomplete) ─────
        keyword_matrix = self.keyword_engine.build_matrix()

        # 13a. Enrich top-200 keywords with Trends-based volume tiers
        top_kws = [e["keyword"] for e in keyword_matrix[:200]]
        enriched = self.dataforseo.get_keyword_metrics(top_kws)
        kw_lookup = {r["keyword"]: r for r in enriched}
        for entry in keyword_matrix[:200]:
            real = kw_lookup.get(entry["keyword"], {})
            entry["search_volume"] = real.get("search_volume")
            entry["volume_tier"]   = real.get("volume_tier", "medium")
            entry["trend_score"]   = real.get("trend_score", 0)
            entry["data_source"]   = real.get("source", "google_trends")
        self._log(f"  Keyword volume:   {len(enriched)} keywords enriched via Google Trends")

        # 13b. Discover NEW keywords from top seed terms via autocomplete
        mc_seeds = mc.get("keyword_discovery_seeds", []) or [e["keyword"] for e in keyword_matrix[:5]]
        discovered = self.keyword_connector.get_keyword_suggestions(mc_seeds, limit_per_seed=30)
        if discovered:
            existing_kws = {e["keyword"] for e in keyword_matrix}
            new_entries = [
                {
                    "keyword":       d["keyword"],
                    "intent":        d.get("intent", "informational"),
                    "source":        "autocomplete_discovery",
                    "page_type":     "blog_post",
                    "funnel_stage":  "solution-aware",
                    "search_volume": d["search_volume"],
                    "data_source":   "google_autocomplete",
                }
                for d in discovered
                if d["keyword"] not in existing_kws
            ]
            keyword_matrix.extend(new_entries)
            self._log(f"  Keyword discovery: {len(new_entries)} new keywords from autocomplete")

        # 13c. SERP feature check on top-20 keywords for snippet targeting
        snippet_kws = [e["keyword"] for e in keyword_matrix[:20]]
        snippet_opps = self.keyword_connector.check_snippet_opportunities(snippet_kws, limit=20)
        if snippet_opps:
            snippet_lookup = {s["keyword"]: s for s in snippet_opps}
            for entry in keyword_matrix[:20]:
                serp = snippet_lookup.get(entry["keyword"], {})
                entry["has_featured_snippet"] = serp.get("opportunity_score", 0) >= 50
                entry["has_paa"]              = any(kw.lower().startswith(("what", "how", "why")) for kw in [entry["keyword"]])
                entry["has_ai_overview"]      = False
            self._log(f"  Snippet opps:     {len(snippet_opps)} keywords checked; {sum(1 for s in snippet_opps if s.get('opportunity_score', 0) >= 50)} high-opportunity")

        self._log(f"  Keyword matrix:   {len(keyword_matrix)} total entries")

        # ── 14. Core Web Vitals audit (if configured) ─────────────────────────
        cwv_results = []
        if self.pagespeed.is_configured and mc.get("run_cwv_audit", False):
            site_url = self.site_config.get("site_url", "")
            if site_url:
                cwv_results.append(self.pagespeed.audit(site_url))
                self._log(f"  CWV audit:        score={cwv_results[0].get('performance_score', 'N/A')}")

        # ── 15. Backlink gap analysis ─────────────────────────────────────────
        backlink_gaps = []
        if mc.get("run_backlink_gap", True):
            comp_domains = [f"{c.lower()}.com" for c in priority_competitors[:5]]
            backlink_gaps = self.backlink_gap.gap_analysis(comp_domains)
            self._log(f"  Backlink gaps:    {len(backlink_gaps)} targets identified")

        # ── 16. Publish pages ─────────────────────────────────────────────────
        self._publish(run_dir, all_pages)
        if mc.get("publish_via_cms", True):
            self._publish_to_cms(run_dir, all_pages)

        # ── 17. Generate supplementary reports ───────────────────────────────
        pr_briefs = self.digital_pr.generate_briefs()
        self._write_supplementary(run_dir, cannibalization_issues, refresh_queue,
                                   backlink_gaps, cwv_results, pr_briefs,
                                   decay_signals, ctr_enrichments)

        # ── 18. Write main report ─────────────────────────────────────────────
        report = GrowthEngineReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            pages_generated=all_pages,
            keyword_matrix=keyword_matrix[:100],
            internal_link_map=link_map,
            topical_coverage=topical_coverage,
            integration_notes=self._integration_notes(cannibalization_issues, refresh_queue),
            output_directory=str(run_dir),
        )
        (run_dir / "growth_engine_report.json").write_text(
            json.dumps(report.to_dict(), indent=2), encoding="utf-8"
        )
        self._write_weekly_report(run_dir, report, topical_coverage)

        # ── 19. Update glossary-terms.ts with any new terms from this run ────
        if self.glossary_updater:
            try:
                glossary_result = self.glossary_updater.run(all_pages)
                if glossary_result.get("added_count", 0) > 0:
                    self._log(
                        f"  Glossary updated:  +{glossary_result['added_count']} new terms "
                        f"({glossary_result['total_count']} total) -> glossary-terms.ts"
                    )
                    (run_dir / "glossary_update.json").write_text(
                        json.dumps(glossary_result, indent=2), encoding="utf-8"
                    )
            except Exception as exc:
                self._log(f"  Glossary update skipped: {exc}")

        self._log(f"Growth Engine complete. {len(all_pages)} pages -> {run_dir}")
        return report

    # ─── Publishing ──────────────────────────────────────────────────────────

    def _publish(self, run_dir: Path, pages: list[GrowthPage]) -> None:
        published_dir = run_dir / "published"
        published_dir.mkdir(parents=True, exist_ok=True)
        for page in pages:
            page_dir = published_dir / page.slug.replace("/", "_")
            page_dir.mkdir(parents=True, exist_ok=True)
            (page_dir / "index.md").write_text(self._render_markdown(page), encoding="utf-8")
            (page_dir / "metadata.json").write_text(json.dumps(self._metadata(page), indent=2, ensure_ascii=False), encoding="utf-8")

    def _publish_to_cms(self, run_dir: Path, pages: list[GrowthPage]) -> None:
        try:
            from connectors.cms_connector import CMSConnector
            from utils.logger import configure_logger
            connector = CMSConnector(self.config, configure_logger())
            content_assets = [p.to_content_asset() for p in pages]
            connector.publish_assets(str(run_dir), content_assets)
        except Exception as exc:
            self._log(f"  CMS publish skipped: {exc}")

        try:
            import os
            from connectors.github_publisher import GitHubPublisher
            gh_cfg = self.config.get("integrations", {}).get("github", {})
            gh = GitHubPublisher(
                token=gh_cfg.get("token", ""),
                repo=gh_cfg.get("repo", ""),
                branch=gh_cfg.get("branch", "main"),
                blog_data_path=gh_cfg.get("blog_data_path", "src/data/blog-articles.ts"),
                tools_data_path=gh_cfg.get("tools_data_path", "src/data/tools-data.ts"),
            )
            if gh.is_configured():
                for page in pages:
                    if page.page_type == "tools_page":
                        gh.publish_tool_page(page)
                    elif page.page_type == "blog_post":
                        gh.publish_blog_post(page)
        except Exception as exc:
            self._log(f"  GitHub publish skipped: {exc}")

    @staticmethod
    def _render_markdown(page: GrowthPage) -> str:
        og = "\n".join(f'{k}: "{v}"' for k, v in page.og_meta.items()) if page.og_meta else ""
        tw = "\n".join(f'{k}: "{v}"' for k, v in page.twitter_meta.items()) if page.twitter_meta else ""
        front_matter_parts = [
            "---",
            f'title: "{page.title}"',
            f'seo_title: "{page.seo_title}"',
            f'meta_description: "{page.meta_description}"',
            f'canonical: "{page.canonical_url}"',
            f'primary_keyword: "{page.primary_keyword}"',
            f'page_type: "{page.page_type}"',
            f'module: "{page.module}"',
            f'industry: "{page.industry}"',
            f'publish_date: "{page.publish_date}"',
            f'modified_date: "{page.modified_date}"',
            f'author: "{page.author_name}"',
            f'word_count: {page.word_count}',
            f'uniqueness_score: {page.uniqueness_score}',
            *(([f'role: "{page.role}"'] if page.role else [])),
            *(([f'competitor: "{page.competitor}"'] if page.competitor else [])),
            *(([f'use_case: "{page.use_case}"'] if page.use_case else [])),
            *(([og] if og else [])),
            *(([tw] if tw else [])),
            "---",
        ]
        return "\n".join(front_matter_parts) + "\n\n" + page.body_markdown

    @staticmethod
    def _metadata(page: GrowthPage) -> dict:
        return page.to_dict()

    def _write_supplementary(self, run_dir: Path, cannibalization: list, refresh: list,
                               backlinks: list, cwv: list, pr_briefs: list,
                               decay_signals: list | None = None,
                               ctr_enrichments: dict | None = None) -> None:
        (run_dir / "cannibalization_issues.json").write_text(json.dumps(cannibalization, indent=2), encoding="utf-8")
        (run_dir / "refresh_queue.json").write_text(json.dumps(refresh, indent=2), encoding="utf-8")
        (run_dir / "backlink_gap_targets.json").write_text(json.dumps(backlinks, indent=2), encoding="utf-8")
        if cwv:
            (run_dir / "cwv_audit.json").write_text(json.dumps(cwv, indent=2), encoding="utf-8")
        (run_dir / "digital_pr_briefs.json").write_text(json.dumps(pr_briefs, indent=2), encoding="utf-8")
        # Revenue-path outputs
        if decay_signals:
            decay_dicts = [s.to_dict() if hasattr(s, "to_dict") else s for s in decay_signals]
            (run_dir / "decay_signals.json").write_text(json.dumps(decay_dicts, indent=2), encoding="utf-8")
            decay_md = self.decay_detector.report_markdown(decay_signals)
            (run_dir / "decay_report.md").write_text(decay_md, encoding="utf-8")
        if ctr_enrichments:
            (run_dir / "ctr_enrichments.json").write_text(json.dumps(ctr_enrichments, indent=2), encoding="utf-8")
        # Content memory report
        mem_md = self.content_memory.report_markdown()
        (run_dir / "content_uniqueness_report.md").write_text(mem_md, encoding="utf-8")
        (run_dir / "content_memory_stats.json").write_text(
            json.dumps(self.content_memory.run_report(), indent=2), encoding="utf-8"
        )
        # Revenue link map
        try:
            link_report = self.revenue_linker.build_link_report([])
            (run_dir / "revenue_link_map.json").write_text(json.dumps(link_report, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _write_weekly_report(self, run_dir: Path, report: GrowthEngineReport, topical_coverage: dict) -> None:
        breakdown = report.to_dict()["page_type_breakdown"]
        avg_wc = report.to_dict()["avg_word_count"]
        lines = [
            "# Pipeleap Growth Engine — Weekly SEO Report",
            f"\n**Run:** {report.generated_at}",
            f"**Pages generated:** {report.to_dict()['total_pages']} (avg {avg_wc} words)",
            "",
            "## Page Breakdown",
            "",
        ]
        for pt, count in sorted(breakdown.items()):
            lines.append(f"- **{pt.replace('_', ' ').title()}:** {count}")
        lines += [
            "",
            self.topical_mapper.weekly_report_md(),
            "",
            self.revenue_engine.weekly_report_md(),
            "",
            self.digital_pr.weekly_report_md(),
        ]
        (run_dir / "weekly_report.md").write_text("\n".join(lines), encoding="utf-8")

    def _load_gsc_period(self, period: str) -> list[dict]:
        """Load saved GSC rows for 'current' or 'previous' 28-day period."""
        try:
            gsc_file = self.output_dir / f"gsc_{period}_period.json"
            if gsc_file.exists():
                return json.loads(gsc_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        return []

    def _load_existing_pages(self) -> list[dict]:
        try:
            pages = []
            for run_dir in sorted(self.output_dir.iterdir()):
                report_file = run_dir / "growth_engine_report.json"
                if report_file.exists():
                    data = json.loads(report_file.read_text(encoding="utf-8"))
                    pages.extend(data.get("pages_generated", []))
            return pages
        except Exception:
            return []

    @staticmethod
    def _integration_notes(cannibalization: list, refresh: list) -> list[str]:
        notes = ["All pages generated by module: pipeleap-seo-engine. Existing agent output is unchanged."]
        if cannibalization:
            notes.append(f"{len(cannibalization)} keyword cannibalization issues detected — see cannibalization_issues.json.")
        if refresh:
            notes.append(f"{len(refresh)} pages flagged for refresh — see refresh_queue.json.")
        notes.append("Keyword volume powered by Google Trends + Autocomplete (free, no API key needed).")
        notes.append("Set PAGESPEED_API_KEY in config for Core Web Vitals monitoring.")
        notes.append("Set AHREFS_API_KEY in config for live backlink gap analysis.")
        return notes

    def _resolve_output_dir(self) -> Path:
        base = self.execution.get("output_dir", "outputs")
        path = Path(base)
        if not path.is_absolute():
            path = (Path(__file__).resolve().parent.parent.parent / path).resolve()
        return path / "growth-engine"

    def _make_logger(self):
        if self.logger:
            return self.logger.info
        return print

    def _make_glossary_updater(self) -> "GlossaryUpdater | None":
        import os
        env = os.getenv("PIPELEAP_LAUNCHPAD_DIR")
        if env and (Path(env) / "src" / "data" / "glossary-terms.ts").exists():
            return GlossaryUpdater(env)
        pub = self.config.get("integrations", {}).get("cms", {}).get("publish_dir", "")
        if pub:
            root = Path(pub).parent.parent.parent
            if (root / "src" / "data" / "glossary-terms.ts").exists():
                return GlossaryUpdater(root)
        sibling = Path(__file__).resolve().parent.parent.parent.parent / "pipeleap-launchpad"
        if (sibling / "src" / "data" / "glossary-terms.ts").exists():
            return GlossaryUpdater(sibling)
        return None

    def _make_refresh_cluster(self, keyword: str, page_type: str):
        from utils.models import KeywordCluster
        intent_map = {
            "blog_post": "informational",
            "comparison_page": "commercial",
            "use_case_page": "informational",
            "landing_page": "commercial",
        }
        intent = intent_map.get(page_type, "informational")
        return KeywordCluster(
            cluster_name=keyword,
            primary_keyword=keyword,
            intent=intent,
            recommended_asset_type=page_type,
            conversion_goal="demo_booking",
        )
