"""
GEO Agent Orchestrator — Generative Engine Optimization for Pipeleap.

Runs independently alongside the existing SEO agent.
Does NOT modify any existing agent files.

Full run sequence per execution:
  1.  SERP AI check     — detect which target queries have AI Overviews / PAA
  2.  Citation gaps     — find queries where Pipeleap should appear but doesn't
  3.  Entity audit      — score and improve entity authority signals
  4.  Semantic coverage — audit topical completeness per pillar
  5.  Answer blocks     — generate / score AI-citation-ready answer blocks
  6.  GEO pages         — generate new answer-first pages for un-covered queries
  7.  Comparison opt    — score and improve comparison page citation eligibility
  8.  AI visibility     — update visibility matrix with SERP feature data
  9.  Mention tracker   — report outreach priorities
  10. Publish           — write GEO pages to launchpad src/data/seo/
  11. Schema injection  — write entity authority schemas to outputs/
  12. Reports           — JSON + Markdown per run
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from geo_agent.engines.answer_block_engine import AnswerBlockEngine
from geo_agent.engines.citation_gap_engine import CitationGapEngine
from geo_agent.engines.entity_authority_engine import EntityAuthorityEngine
from geo_agent.engines.ai_visibility_engine import AIVisibilityEngine
from geo_agent.engines.semantic_coverage_engine import SemanticCoverageEngine
from geo_agent.engines.comparison_optimizer import ComparisonOptimizer
from geo_agent.generators.geo_page_generator import GEOPageGenerator
from geo_agent.generators.global_market_generator import GlobalMarketGenerator
from geo_agent.generators.listing_generator import ListingGenerator
from geo_agent.generators.quora_generator import QuoraGenerator
from geo_agent.generators.outreach_generator import OutreachGenerator
from geo_agent.connectors.serp_ai_connector import SERPAIConnector
from geo_agent.connectors.mention_tracker import MentionTracker
from geo_agent.engines.shared_registry import SharedRegistry
from geo_agent.data.geo_entities import GEO_TARGET_QUERIES
from geo_agent.data.ai_source_sites import citation_score
from geo_agent.models import GEORunReport, GEOPage


class GEOOrchestrator:
    """
    Main orchestrator for Pipeleap's Generative Engine Optimization agent.
    Self-contained — no imports from or modifications to the existing SEO agent.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.site_url  = config.get("site", {}).get("site_url", "https://pipeleap.com")
        self.output_dir = self._resolve_output_dir()
        self.cms_dir    = config.get("integrations", {}).get("cms", {}).get("publish_dir", "")

        # Connectors
        self.serp_connector = SERPAIConnector()
        self.mention_tracker = MentionTracker(
            registry_path=str(self.output_dir / "mention_registry.json")
        )
        # Shared registry — combines SEO SQLite + filesystem so GEO never
        # regenerates slugs already published by the SEO agent (and vice versa)
        seo_db = self._resolve_seo_db_path()
        self.shared_registry = SharedRegistry(
            seo_db_path=seo_db,
            cms_publish_dir=self.cms_dir,
        )

        # Wikipedia connector for entity enrichment
        try:
            from connectors.wikipedia_connector import WikipediaConnector
            self._wikipedia = WikipediaConnector()
        except ImportError:
            self._wikipedia = None

        # Engines
        self.answer_engine    = AnswerBlockEngine()
        self.citation_engine  = CitationGapEngine()
        self.entity_engine    = EntityAuthorityEngine(wikipedia=self._wikipedia)
        self.visibility_engine= AIVisibilityEngine(
            registry_path=str(self.output_dir / "visibility_registry.json")
        )
        self.coverage_engine  = SemanticCoverageEngine()
        self.comparison_engine= ComparisonOptimizer()
        self.page_generator      = GEOPageGenerator()
        self.global_market_gen   = GlobalMarketGenerator()
        self.listing_generator = ListingGenerator()
        self.quora_generator   = QuoraGenerator()
        self.outreach_generator= OutreachGenerator()

        self._log = self._make_logger()

    def run(self) -> GEORunReport:
        self._log("GEO Agent starting...")
        run_id  = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = self.output_dir / run_id
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        run_dir.mkdir(parents=True, exist_ok=True)

        # ── 1. SERP AI feature detection ──────────────────────────────────────
        from geo_agent.data.global_queries import all_global_queries
        all_queries = (
            [q for queries in GEO_TARGET_QUERIES.values() for q in queries]
            + all_global_queries()
        )
        self._log(f"  SERP check: {len(all_queries)} GEO queries ({len(all_global_queries())} global)")
        serp_results = self.serp_connector.check_queries(all_queries[:30], delay=0.3)
        ai_ov_count = len(self.serp_connector.ai_overview_queries(serp_results))
        paa_count   = len(self.serp_connector.paa_queries(serp_results))
        self._log(f"  SERP results: {ai_ov_count} AI Overviews, {paa_count} PAA detected (free heuristics)")

        # ── 2. Citation gap detection ─────────────────────────────────────────
        published_slugs = self._get_published_slugs()
        citation_gaps   = self.citation_engine.detect(
            published_slugs=published_slugs,
            serp_data=serp_results,
            cms_publish_dir=self.cms_dir,
        )
        critical_gaps = sum(1 for g in citation_gaps if g.priority_score >= 0.8)
        self._log(f"  Citation gaps: {len(citation_gaps)} ({critical_gaps} critical)")

        # ── 3. Entity authority audit ─────────────────────────────────────────
        entity_audit = self.entity_engine.audit()
        self._log(f"  Entity score:  {entity_audit['overall_entity_score']}/100")

        # ── 4. Semantic coverage audit ────────────────────────────────────────
        coverage_audit: dict[str, Any] = {}
        if self.cms_dir and Path(self.cms_dir).exists():
            coverage_audit = self.coverage_engine.audit_all_pillars(self.cms_dir)
            self._log(f"  Semantic cov:  {coverage_audit.get('overall_coverage_pct', 0)}%")
        else:
            self._log("  Semantic coverage skipped — cms_dir not available")

        # ── 5. Answer block generation ────────────────────────────────────────
        answer_blocks = self.answer_engine.generate_all()
        eligible_blocks = sum(1 for b in answer_blocks if b.get("eligible_for_ai_overview"))
        self._log(f"  Answer blocks: {len(answer_blocks)} ({eligible_blocks} AIO-eligible)")

        # ── 6. GEO page generation ────────────────────────────────────────────
        geo_pages = self.page_generator.generate_all(set(published_slugs))
        self._log(f"  GEO pages:     {len(geo_pages)} new pages generated")

        # ── 6b. Global market GEO pages ───────────────────────────────────────
        global_pages = self.global_market_gen.generate_all(set(published_slugs))
        geo_pages.extend(global_pages)
        self._log(f"  Global pages:  {len(global_pages)} international market pages")

        # ── 7. Comparison optimization ────────────────────────────────────────
        comp_schemas = self.comparison_engine.all_comparison_schemas()
        self._log(f"  Comparison:    {len(comp_schemas)} comparison schema sets generated")

        # ── 8. AI visibility update ───────────────────────────────────────────
        if serp_results:
            ai_coverage = self.visibility_engine.check_ai_overview_coverage(serp_results)
            self._log(f"  AI coverage:   {len(ai_coverage['ai_overview_present'])} queries with AI Overviews")
        else:
            ai_coverage = {}

        # ── 9b. Mention tracker report ────────────────────────────────────────
        outreach_targets = self.mention_tracker.priority_outreach_list()
        self._log(f"  Outreach:      {len(outreach_targets)} citation targets outstanding")

        # ── 10. Publish GEO pages ─────────────────────────────────────────────
        published_count = 0
        if self.cms_dir and geo_pages:
            published_count = self._publish_pages(geo_pages)
            self._log(f"  Published:     {published_count} GEO pages to {self.cms_dir}")

        # Register GEO pages in SEO SQLite after publishing
        if published_count > 0:
            registered = self.shared_registry.register_geo_pages(geo_pages, run_id)
            self._log(f"  Slug registry:  {registered} GEO slugs registered in SEO SQLite")
            # Also persist GEO keywords into keyword_snapshots so organic keyword
            # metrics in AnalyticsEngine include GEO-generated content
            kw_registered = self.shared_registry.register_geo_keywords(geo_pages, run_id)
            self._log(f"  Keyword registry: {kw_registered} GEO keywords written to SEO SQLite")

        # ── 10c. Citation score improvement assets ────────────────────────────
        listing_results  = self.listing_generator.generate_all(run_dir)
        quora_results    = self.quora_generator.generate_all(run_dir)
        outreach_results = self.outreach_generator.generate_all(run_dir)
        self._log(
            f"  Citation assets:  {len(listing_results)} listings, "
            f"{len(quora_results)} Quora answers, "
            f"{len(outreach_results)} outreach emails written to {run_dir}"
        )

        # ── 11. Write schema payloads ─────────────────────────────────────────
        schema_payloads = self.entity_engine.generate_schema_payloads()
        (run_dir / "entity_schemas.json").write_text(
            json.dumps(schema_payloads, indent=2), encoding="utf-8"
        )

        # ── 12. Build recommendations ─────────────────────────────────────────
        recommendations = self._build_recommendations(
            entity_audit, citation_gaps, outreach_targets, coverage_audit
        )

        # ── 13. Write run reports ─────────────────────────────────────────────
        entity_signals = self.entity_engine.entity_signals()
        report = GEORunReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            pages_generated=geo_pages,
            citation_gaps=citation_gaps,
            entity_signals=entity_signals,
            ai_overview_queries=ai_coverage.get("ai_overview_present", []),
            citation_score=citation_score(),
            recommendations=recommendations,
            output_directory=str(run_dir),
        )
        self._write_reports(run_dir, report, answer_blocks, coverage_audit, ai_coverage)

        total_pages = len(geo_pages)
        self._log(f"GEO Agent complete. {total_pages} pages -> {run_dir}")
        return report

    # ── Publishing ─────────────────────────────────────────────────────────────

    def _publish_pages(self, pages: list[GEOPage]) -> int:
        cms_root = Path(self.cms_dir)
        count = 0
        for page in pages:
            page_dir = cms_root / page.slug
            page_dir.mkdir(parents=True, exist_ok=True)
            (page_dir / "index.md").write_text(page.body_markdown, encoding="utf-8")
            (page_dir / "metadata.json").write_text(
                json.dumps({
                    "slug":             page.slug,
                    "page_type":        page.page_type,
                    "seo_title":        page.title,
                    "meta_description": page.meta_description,
                    "schema_markup":    page.schema_markup,
                    "source_keywords":  [page.primary_query],
                    "geo_query":        page.primary_query,
                    "geo_category":     page.query_category,
                    "answer_block":     page.answer_block,
                    "target_ai_engines":page.target_ai_engines,
                    "publish_date":     page.publish_date,
                }, indent=2),
                encoding="utf-8",
            )
            count += 1
        return count

    # ── Reports ────────────────────────────────────────────────────────────────

    def _write_reports(
        self,
        run_dir: Path,
        report: GEORunReport,
        answer_blocks: list[dict],
        coverage_audit: dict,
        ai_coverage: dict,
    ) -> None:
        (run_dir / "geo_report.json").write_text(
            json.dumps(report.to_dict(), indent=2), encoding="utf-8"
        )
        (run_dir / "answer_blocks.json").write_text(
            json.dumps(answer_blocks, indent=2), encoding="utf-8"
        )
        if coverage_audit:
            (run_dir / "semantic_coverage.json").write_text(
                json.dumps(coverage_audit, indent=2), encoding="utf-8"
            )
        if ai_coverage:
            (run_dir / "ai_overview_coverage.json").write_text(
                json.dumps(ai_coverage, indent=2), encoding="utf-8"
            )

        # Markdown reports
        gap_md = self.citation_engine.coverage_report(report.citation_gaps)
        vis_md = self.visibility_engine.visibility_report_md()
        men_md = self.mention_tracker.report_md()
        cov_md = self.coverage_engine.report_md(coverage_audit) if coverage_audit else "Coverage audit not run."

        weekly_md = "\n\n---\n\n".join([
            "# Pipeleap GEO Agent — Weekly Report",
            f"**Run:** {report.generated_at}",
            f"**Entity score:** {report.citation_score}/100",
            f"**Pages generated:** {len(report.pages_generated)}",
            f"**Citation gaps:** {len(report.citation_gaps)}",
            "",
            "## Recommendations",
            "\n".join(f"- {r}" for r in report.recommendations),
            gap_md, vis_md, men_md, cov_md,
        ])
        (run_dir / "geo_weekly_report.md").write_text(weekly_md, encoding="utf-8")

    # ── Recommendations ────────────────────────────────────────────────────────

    def _build_recommendations(
        self,
        entity_audit: dict,
        citation_gaps: list,
        outreach_targets: list,
        coverage_audit: dict,
    ) -> list[str]:
        recs = list(entity_audit.get("recommendations", []))
        critical = [g for g in citation_gaps if g.priority_score >= 0.8]
        if critical:
            recs.insert(0,
                f"CRITICAL: {len(critical)} queries have AI Overviews but no Pipeleap content. "
                "Create GEO answer-block pages immediately."
            )
        if outreach_targets:
            top_target = outreach_targets[0]
            recs.append(
                f"Next outreach: {top_target['site']} ({top_target['action']})"
            )
        if coverage_audit:
            weak = coverage_audit.get("weakest_pillars", [])
            if weak:
                recs.append(f"Expand semantic coverage for: {', '.join(weak[:3])}")
        return recs

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _get_published_slugs(self) -> set[str]:
        """Load slugs from BOTH SEO SQLite + filesystem via SharedRegistry."""
        return self.shared_registry.all_slugs()

    def _resolve_seo_db_path(self) -> Path:
        """Find the SEO agent's SQLite memory DB (used as shared slug registry)."""
        configured = self.config.get("execution", {}).get(
            "memory_db", "outputs/pipeleap_seo_memory.sqlite"
        )
        p = Path(configured)
        if p.is_absolute():
            return p
        return (Path(__file__).resolve().parent.parent / p).resolve()

    def _resolve_output_dir(self) -> Path:
        base = self.config.get("execution", {}).get("output_dir", "outputs")
        path = Path(base)
        if not path.is_absolute():
            path = (Path(__file__).resolve().parent.parent / path).resolve()
        return path / "geo-agent"

    def _make_logger(self):
        import logging
        logger = logging.getLogger("pipeleap_geo_agent")
        if not logger.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            )
        return logger.info
