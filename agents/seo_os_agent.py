from __future__ import annotations

"""
SEO OS Agent — Autonomous, self-adapting SEO operating system for Pipeleap.com.

OBSERVE -> DIFF -> DECIDE -> EXECUTE -> LEARN

Runs in SAFE MODE: never modifies core website code.

11-Step Daily Execution:
  Step 1:  Website snapshot
  Step 2:  Change diff
  Step 3:  Adaptive action engine
  Step 4:  Technical SEO (safe mode)
  Step 5:  Keyword engine (20 keywords: 10 high-intent, 5 competitor gaps, 5 long-tail)
   Step 6:  Content engine (respects config per-run limits: blog_posts, use_case_pages + 3 glossary stubs)
  Step 7:  On-page optimisation (3 pages: titles, meta, headers)
  Step 8:  Internal linking strategy
  Step 9:  Competitor analysis (2 competitors, keyword gaps)
  Step 10: Indexing recommendations
  Step 11: Self-improvement loop (prioritise, de-duplicate, score)

Output: structured JSON report + human-readable daily briefing
"""

import json
import logging
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.content_coverage import ContentCoverage, detect_content_gaps
from core.snapshot_engine import SnapshotEngine, SiteSnapshot
from core.diff_engine import DiffEngine, SiteDiff
from core.adaptive_action_engine import AdaptiveActionEngine, ExecutionPlan


@dataclass
class SEOScore:
    overall: int = 0
    technical: int = 0
    content: int = 0
    authority: int = 0
    indexing: int = 0
    breakdown: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "overall": self.overall,
            "technical": self.technical,
            "content": self.content,
            "authority": self.authority,
            "indexing": self.indexing,
            "breakdown": self.breakdown,
        }


@dataclass
class SEOOSResult:
    run_id: str
    generated_at: str
    mode: str = ""
    website_changes: dict = field(default_factory=dict)
    safe_actions: list[dict] = field(default_factory=list)
    dev_review_items: list[dict] = field(default_factory=list)
    keyword_opportunities: list[dict] = field(default_factory=list)
    content_generated: list[dict] = field(default_factory=list)
    tools_generated: list[dict] = field(default_factory=list)
    pages_optimized: list[dict] = field(default_factory=list)
    linking_suggestions: list[dict] = field(default_factory=list)
    indexing_actions: list[dict] = field(default_factory=list)
    gsc_insights: list[dict] = field(default_factory=list)
    content_gaps: list[dict] = field(default_factory=list)
    content_gap_clusters: list[dict] = field(default_factory=list)
    latent_keywords: list[dict] = field(default_factory=list)
    risks_and_missed: list[dict] = field(default_factory=list)
    seo_score: SEOScore = field(default_factory=SEOScore)
    next_day_plan: list[str] = field(default_factory=list)
    output_files: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "generated_at": self.generated_at,
            "mode": self.mode,
            "website_changes": self.website_changes,
            "safe_actions": self.safe_actions,
            "dev_review_items": self.dev_review_items,
            "keyword_opportunities": self.keyword_opportunities,
            "content_generated": self.content_generated,
            "tools_generated": self.tools_generated,
            "pages_optimized": self.pages_optimized,
            "linking_suggestions": self.linking_suggestions,
            "indexing_actions": self.indexing_actions,
            "gsc_insights": self.gsc_insights,
            "content_gaps": self.content_gaps,
            "content_gap_clusters": self.content_gap_clusters,
            "latent_keywords": self.latent_keywords,
            "risks_and_missed": self.risks_and_missed,
            "seo_score": self.seo_score.to_dict(),
            "next_day_plan": self.next_day_plan,
            "output_files": self.output_files,
            "errors": self.errors,
        }


class SEOOSAgent:
    """
    Autonomous SEO operating system. Runs all 11 steps in sequence,
    persists state between runs, and outputs a daily briefing.
    """

    VERSION = "1.0.0"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.logger = logging.getLogger("seo_os_agent")
        self.site_url = config.get("site", {}).get("site_url", "https://www.pipeleap.com").rstrip("/")
        self.output_root = Path(config.get("execution", {}).get("output_dir", "outputs"))

        self.snapshot_engine = SnapshotEngine(config, self.logger)
        self.diff_engine = DiffEngine(config, self.logger)
        self.action_engine = AdaptiveActionEngine(config, self.logger)

        self._state_dir = self.output_root / "seo_os_state"
        self._state_dir.mkdir(parents=True, exist_ok=True)

    def run_once(self) -> dict:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_dir = self.output_root / run_id
        output_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info("SEO OS Agent v%s — run_id=%s", self.VERSION, run_id)

        result = SEOOSResult(
            run_id=run_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        # ── Step 1: Website Snapshot ──────────────────────────────────────────
        self.logger.info("Step 1: Website snapshot")
        previous_snapshot = self._load_previous_snapshot()
        try:
            current_snapshot = self.snapshot_engine.capture(run_id=run_id, previous_snapshot=previous_snapshot)
            self._save_snapshot(current_snapshot)
        except Exception as exc:
            self.logger.error("Snapshot failed: %s", exc)
            result.errors.append(f"snapshot: {exc}")
            current_snapshot = self.snapshot_engine._synthetic_snapshot(run_id, datetime.now(timezone.utc).isoformat())

        # ── Step 2: Diff Engine ───────────────────────────────────────────────
        self.logger.info("Step 2: Change diff")
        try:
            diff: SiteDiff = self.diff_engine.diff(current_snapshot, previous_snapshot)
            result.website_changes = diff.summary()
            self._write_json(output_dir / "site_diff.json", diff.to_dict())
        except Exception as exc:
            self.logger.error("Diff failed: %s", exc)
            result.errors.append(f"diff: {exc}")
            from core.diff_engine import SiteDiff
            diff = SiteDiff(run_id=run_id, previous_run_id="none")

        # ── Step 3: Adaptive Action Engine ───────────────────────────────────
        self.logger.info("Step 3: Adaptive action engine")
        try:
            plan: ExecutionPlan = self.action_engine.decide(diff)
            result.mode = plan.mode
            result.safe_actions = [vars(a) for a in plan.auto_executable()]
            result.dev_review_items = [vars(a) for a in plan.dev_review_required()]
            self._write_json(output_dir / "execution_plan.json", plan.to_dict())
        except Exception as exc:
            self.logger.error("Action engine failed: %s", exc)
            result.errors.append(f"action_engine: {exc}")

        # ── Step 4: Technical SEO ─────────────────────────────────────────────
        self.logger.info("Step 4: Technical SEO")
        audit_issues: list = []
        try:
            technical_issues = self._run_technical_audit(current_snapshot, diff)
            for issue in technical_issues:
                if issue.get("requires_dev"):
                    result.dev_review_items.append(issue)
                else:
                    result.safe_actions.append(issue)
            audit_issues = technical_issues
        except Exception as exc:
            self.logger.warning("Technical audit skipped: %s", exc)

        # ── Step 4e: Auto-fix applicable audit issues ─────────────────────────
        self.logger.info("Step 4e: Auto-fix")
        try:
            from core.auto_fixer import AutoFixer
            launchpad_path = Path(__file__).resolve().parent.parent / "temp_frontend_repo"
            fixer = AutoFixer(launchpad_path, self.config, self.logger)
            fixes = fixer.apply(audit_issues)
            if fixes:
                self.logger.info("Auto-fix: %d fixes applied", len(fixes))
        except Exception as exc:
            self.logger.warning("Auto-fix skipped: %s", exc)

        # ── Step 4h: Event-Triggered Content Detection ─────────────────────────
        self.logger.info("Step 4h: Event-triggered content detection")
        try:
            event_opportunities = self._detect_event_content_opportunities()
            if event_opportunities:
                self.logger.info("Event-triggered: %d content opportunities detected", len(event_opportunities))
                result.keyword_opportunities = self._merge_keyword_opportunities(
                    result.keyword_opportunities, event_opportunities
                )
                self._write_json(output_dir / "event_content_opportunities.json", event_opportunities)
        except Exception as exc:
            self.logger.warning("Event content detection skipped: %s", exc)

        # ── Step 4b: GSC Performance Audit ───────────────────────────────────
        self.logger.info("Step 4b: GSC performance audit")
        raw_gsc_rows: list[dict] = []
        try:
            gsc_insights, raw_gsc_rows = self._run_gsc_performance_audit()
            result.gsc_insights = gsc_insights
            self._write_json(output_dir / "gsc_insights.json", gsc_insights)
        except Exception as exc:
            self.logger.warning("GSC audit skipped: %s", exc)
            raw_gsc_rows = []

        # ── Step 4c: GA4 Analytics Audit ─────────────────────────────────────
        self.logger.info("Step 4c: GA4 analytics audit")
        try:
            ga4_insights = self._run_ga4_audit()
            result.gsc_insights.extend(ga4_insights)
            self._write_json(output_dir / "ga4_insights.json", ga4_insights)
        except Exception as exc:
            self.logger.warning("GA4 audit skipped: %s", exc)

        # ── Step 4d: Content Coverage Analysis ───────────────────────────────
        self.logger.info("Step 4d: Content coverage analysis")
        content_gap_clusters: list = []
        try:
            coverage = self._build_content_coverage()
            if coverage:
                result.content_gaps = coverage.get("gaps", [])
                result.latent_keywords = coverage.get("latent_keywords", [])
                self._write_json(output_dir / "content_coverage.json", coverage.get("report", {}))
                if result.latent_keywords:
                    self._write_json(output_dir / "latent_keywords.json", result.latent_keywords)

                # Cluster gaps by topic + intent for strategic prioritization
                from core.content_gap_clustering import cluster_content_gaps
                topic_map = self.config.get("seo", {}).get("topic_map", {})
                content_gap_clusters = cluster_content_gaps(result.content_gaps, topic_map)
                result.content_gap_clusters = [
                    {
                        "cluster_name": c.cluster_name,
                        "intent": c.intent,
                        "funnel_stage": c.funnel_stage,
                        "recommended_asset_type": c.recommended_asset_type,
                        "conversion_goal": c.conversion_goal,
                        "keyword_count": c.count,
                        "aggregate_difficulty": c.aggregate_difficulty,
                        "aggregate_priority": c.aggregate_priority,
                        "top_keywords": [g.get("keyword", "") for g in c.keywords[:5]],
                        "strategic_rationale": c.strategic_rationale,
                    }
                    for c in content_gap_clusters
                ]
                self._write_json(output_dir / "content_gap_clusters.json", result.content_gap_clusters)
                self.logger.info("Content gap clusters: %d clusters from %d gaps",
                                 len(content_gap_clusters), len(result.content_gaps))
        except Exception as exc:
            self.logger.warning("Content coverage skipped: %s", exc)

        # ── Step 5: Keyword Engine ────────────────────────────────────────────
        self.logger.info("Step 5: Keyword engine")
        try:
            keywords = self._run_keyword_engine(diff, gsc_rows=raw_gsc_rows)
            result.keyword_opportunities = keywords
            self._write_json(output_dir / "keyword_opportunities.json", keywords)
        except Exception as exc:
            self.logger.warning("Keyword engine skipped: %s", exc)
            result.errors.append(f"keyword_engine: {exc}")

        # ── Step 6: Content Engine ────────────────────────────────────────────
        self.logger.info("Step 6: Content engine")
        try:
            content = self._run_content_engine(diff, run_id, keywords)
            result.content_generated = content
            self._write_json(output_dir / "content_generated.json", content)
        except Exception as exc:
            self.logger.warning("Content engine skipped: %s", exc)
            result.errors.append(f"content_engine: {exc}")

        # ── Step 6b: Tool Directory Engine ────────────────────────────────────
        self.logger.info("Step 6b: Tool directory engine")
        try:
            tool_results = self._run_tool_engine()
            result.tools_generated = tool_results
            self._write_json(output_dir / "tools_generated.json", tool_results)
        except Exception as exc:
            self.logger.warning("Tool engine skipped: %s", exc)
            result.errors.append(f"tool_engine: {exc}")

        # ── Step 7: On-Page Optimisation ─────────────────────────────────────
        self.logger.info("Step 7: On-page optimisation")
        try:
            optimised = self._run_onpage_optimizer(current_snapshot, diff)
            result.pages_optimized = optimised
            self._write_json(output_dir / "pages_optimized.json", optimised)
        except Exception as exc:
            self.logger.warning("On-page optimizer skipped: %s", exc)
            result.errors.append(f"onpage: {exc}")

        # ── Step 8: Internal Linking ──────────────────────────────────────────
        self.logger.info("Step 8: Internal linking")
        try:
            linking = self._run_linking_engine(current_snapshot, diff)
            result.linking_suggestions = linking
            self._write_json(output_dir / "linking_suggestions.json", linking)
        except Exception as exc:
            self.logger.warning("Linking engine skipped: %s", exc)

        # ── Step 9: (removed - competitor analysis) ──────────────────────────

        # ── Step 10: Indexing ─────────────────────────────────────────────────
        self.logger.info("Step 10: Indexing recommendations")
        try:
            indexing = self._build_indexing_actions(diff, current_snapshot)
            result.indexing_actions = indexing
            self._write_json(output_dir / "indexing_actions.json", indexing)
        except Exception as exc:
            self.logger.warning("Indexing step skipped: %s", exc)

        # ── Post-Publish Signals (IndexNow, GSC, Indexing API) ────────────────
        pp_report: dict | None = None
        try:
            from connectors.post_publish_hook import PostPublishHook
            hook = PostPublishHook(self.config, self.logger)
            launchpad_sitemap = Path(__file__).resolve().parent.parent / "temp_frontend_repo" / "public" / "sitemap.xml"
            new_content = [c for c in result.content_generated if c.get("slug")]
            pp_report = hook.run(sitemap_path=str(launchpad_sitemap) if launchpad_sitemap.exists() else None,
                                 new_slugs_or_assets=new_content,
                                 output_dir=str(output_dir))
            self.logger.info("Post-publish signals fired for %d new slugs", len(new_content))
        except Exception as exc:
            self.logger.warning("Post-publish signals skipped: %s", exc)

        # ── Indexing verification ─────────────────────────────────────────────
        try:
            from core.indexing_verifier import IndexingVerifier
            verifier = IndexingVerifier(self.config, self.logger)
            verifier.submitted_urls = hook.submitted_urls if pp_report else set()
            if pp_report:
                new_urls = [f"{self.site_url}/blog/{c.get('slug', '')}" for c in new_content]
                verification = verifier.verify_post_publish(
                    post_publish_report=pp_report,
                    new_urls=new_urls,
                    sitemap_path=str(launchpad_sitemap) if launchpad_sitemap.exists() else None,
                    output_dir=str(output_dir),
                )
                self.logger.info("Indexing verification: overall_ok=%s", verification.get("overall_ok"))
        except Exception as exc:
            self.logger.warning("Indexing verification skipped: %s", exc)

        # ── War Room: ingest audit issues + indexing failures ─────────────────
        try:
            from core.war_room import WarRoom
            warroom = WarRoom(self.config, self.logger)
            all_issues = []
            if audit_issues:
                all_issues.extend(warroom.ingest_audit_issues(audit_issues, source="seo_os"))
            warroom.archive_stale(max_age_days=3)
            summary = warroom.summary()
            self.logger.info("WarRoom: %d active alerts (%d critical)", summary.get("active_count", 0), summary.get("critical_count", 0))
        except Exception as exc:
            self.logger.warning("WarRoom skipped: %s", exc)

        # ── GitHub publish (blog posts only — structured outputs handled by repo_writer) ──
        try:
            from connectors.github_publisher import GitHubPublisher
            gh_cfg = self.config.get("integrations", {}).get("github", {})
            publisher = GitHubPublisher(
                token=gh_cfg.get("token", ""),
                repo=gh_cfg.get("repo", ""),
                branch=gh_cfg.get("branch", "main"),
            )
            if publisher.is_configured():
                for item in result.content_generated:
                    item_type = item.get("type", "")
                    if item_type == "blog_post" and item.get("slug"):
                        publisher.publish_blog_post(item)
        except Exception as exc:
            self.logger.warning("GitHub publish skipped: %s", exc)

        # ── Step 4f: Backlink Execution ──────────────────────────────────────
        backlink_urls: list[str] = []
        try:
            from connectors.backlink_executor import BacklinkExecutor
            for item in result.content_generated:
                slug = item.get("slug", "")
                ptype = item.get("type", "blog_post")
                if slug:
                    if ptype == "blog_post":
                        backlink_urls.append(f"{self.site_url}/blog/{slug}")
                    elif ptype in ("glossary_term", "glossary_page"):
                        backlink_urls.append(f"{self.site_url}/glossary/{slug}")
                    elif ptype == "tool":
                        backlink_urls.append(f"{self.site_url}/tools/{slug}")
                    elif ptype in ("landing_page", "use_case_page"):
                        backlink_urls.append(f"{self.site_url}/{slug}")
                    # comparison pages not published to blog — skip backlinks
                    elif ptype == "case_study":
                        backlink_urls.append(f"{self.site_url}/case-studies/{slug}")
                    else:
                        backlink_urls.append(f"{self.site_url}/blog/{slug}")
            if backlink_urls:
                be = BacklinkExecutor(output_dir=str(output_dir / "backlinks"))
                be.run_all(backlink_urls)
                self.logger.info("BacklinkExecutor: %d URLs submitted to archive/ping services", len(backlink_urls))
        except Exception as exc:
            self.logger.warning("Backlink execution skipped: %s", exc)

        # ── Step 4g: Package Publishing (npm / PyPI / crates.io) ────────────
        try:
            from scripts import publish_packages
            pp_results = publish_packages.main_in_process(str(output_dir / "backlinks"))
            self.logger.info("PackagePublisher: %d/%d generated, %d/%d published",
                pp_results.get("generated", 0), 3,
                pp_results.get("published", 0), 3)
        except Exception as exc:
            self.logger.warning("Package publishing skipped: %s", exc)

        # ── Step 4h: Outreach Brief Generation ──────────────────────────────
        try:
            from core.outreach_engine import OutreachEngine
            oe = OutreachEngine(self.config, output_dir=str(output_dir / "outreach"))
            briefs = oe.generate(competitor_gaps=result.content_gaps)
            self.logger.info("OutreachEngine: %d briefs generated", len(briefs))
        except Exception as exc:
            self.logger.warning("Outreach brief generation skipped: %s", exc)

        # ── Step 11: Self-Improvement Loop ────────────────────────────────────
        self.logger.info("Step 11: Self-improvement loop")
        result.risks_and_missed = self._identify_risks(diff, current_snapshot, result)
        result.seo_score = self._compute_seo_score(diff, current_snapshot, result)
        result.next_day_plan = self._build_next_day_plan(result)

        # ── Output ────────────────────────────────────────────────────────────
        master = result.to_dict()
        self._write_json(output_dir / "seo_os_report.json", master)
        result.output_files.append(str(output_dir / "seo_os_report.json"))

        try:
            briefing = self._build_daily_briefing(result, diff, plan)
            (output_dir / "daily_briefing.md").write_text(briefing, encoding="utf-8")
            result.output_files.append(str(output_dir / "daily_briefing.md"))
        except Exception as exc:
            self.logger.warning("Briefing write failed: %s", exc)

        self._update_learning_log(run_id, result)

        self.logger.info(
            "SEO OS complete — score=%d mode=%s actions=%d errors=%d",
            result.seo_score.overall, result.mode,
            len(result.safe_actions), len(result.errors),
        )
        return master

    # ── Step implementations ───────────────────────────────────────────────────

    def _run_technical_audit(self, snapshot: SiteSnapshot, diff: SiteDiff) -> list[dict]:
        crawl_report = getattr(snapshot, "crawl_report", None)
        if crawl_report is None:
            return []

        # Optional Playwright rendering — enriches PageSnapshot before AuditEngine runs
        if self.config.get("execution", {}).get("use_renderer", False):
            try:
                from connectors.renderer import PlaywrightRenderer
                renderer = PlaywrightRenderer()
                if renderer.available:
                    urls = [p.url for p in crawl_report.pages[:10]]
                    render_map = {r.url: r for r in renderer.render_pages(urls)}
                    for page in crawl_report.pages:
                        rr = render_map.get(page.url)
                        if rr and not rr.error:
                            page.is_soft_404 = rr.is_soft_404
                            page.has_fullscreen_overlay = rr.has_fullscreen_overlay
                    self.logger.info("Playwright renderer completed for %d pages", len(urls))
                else:
                    self.logger.info("Playwright not installed — skipping render scan")
            except Exception as exc:
                self.logger.warning("Renderer skipped: %s", exc)

        from core.audit_engine import AuditEngine
        engine = AuditEngine(self.config, self.logger)
        audit_issues = engine.run(crawl_report)
        # cache on snapshot so _compute_seo_score can use it without re-running
        snapshot.audit_issues = audit_issues  # type: ignore[attr-defined]
        _SEVERITY_PRIORITY = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
        result: list[dict] = []
        for issue in audit_issues[:30]:  # cap at top 30 by impact_score (AuditEngine already sorts)
            requires_dev = issue.severity in ("Critical", "High")
            result.append({
                "category": issue.category,
                "page_url": issue.url,
                "title": issue.title,
                "description": issue.description,
                "fix_instructions": issue.fix_instructions,
                "auto_fix_script": issue.auto_fix_script,
                "impact_score": issue.impact_score,
                "severity": issue.severity,
                "requires_dev": requires_dev,
                "dev_note": f"REQUIRES DEV REVIEW — {issue.fix_instructions}" if requires_dev else "",
                "priority": _SEVERITY_PRIORITY.get(issue.severity, 4),
                "safe_mode": not requires_dev,
            })
        return result

    def _build_content_coverage(self) -> dict | None:
        launchpad_dir = Path(__file__).resolve().parent.parent / "temp_frontend_repo"
        if not launchpad_dir.exists():
            self.logger.warning("Launchpad dir not found at %s — skipping content coverage", launchpad_dir)
            return None

        # Pull latest to avoid stale coverage
        try:
            subprocess.run(
                ["git", "pull", "--rebase"],
                cwd=str(launchpad_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )
        except Exception as exc:
            self.logger.warning("git pull in temp_frontend_repo failed (non-fatal): %s", exc)

        try:
            coverage = ContentCoverage.build(str(launchpad_dir))
            gaps = detect_content_gaps(self._get_all_keyword_candidates(), coverage, min_confidence=0.4)
            latent = coverage.mine_latent_keywords(data_dir=launchpad_dir / "src" / "data", top_n=20)
            return {
                "gaps": gaps,
                "latent_keywords": latent,
                "report": {
                    "total_pages": len(coverage.page_index),
                    "total_keywords_checked": len(self._get_all_keyword_candidates()),
                    "gaps_found": len(gaps),
                    "latent_keywords_found": len(latent),
                    "by_type": {
                        pt: len([p for p in coverage.page_index.values() if p.page_type == pt])
                        for pt in {p.page_type for p in coverage.page_index.values()}
                    },
                },
            }
        except Exception as exc:
            self.logger.warning("Content coverage build failed: %s", exc)
            return None

    def _get_all_keyword_candidates(self) -> list[dict]:
        # Derive from config seed keywords instead of hardcoding
        seed = self.config.get("seo", {}).get("seed_keywords", {})
        keywords: list[dict] = []
        seen: set[str] = set()
        for category, kws in seed.items():
            if category == "pain_point":
                continue  # pain_points are woven into existing pages, not generated as articles
            for kw in kws:
                if kw not in seen:
                    seen.add(kw)
                    keywords.append({"keyword": kw, "cluster": category, "type": category})
        return keywords

    def _run_keyword_engine(self, diff: SiteDiff, gsc_rows: list[dict] | None = None) -> list[dict]:
        from core.keyword_engine import KeywordEngine as RealKeywordEngine
        from core.content_coverage import ContentCoverage

        engine = RealKeywordEngine(self.config, self.logger)
        existing_slugs = self._load_existing_slugs()

        # Build content coverage so engine can skip covered keywords
        coverage = None
        launchpad_dir = Path(__file__).resolve().parent.parent / "temp_frontend_repo"
        if launchpad_dir.exists():
            try:
                coverage = ContentCoverage.build(str(launchpad_dir))
            except Exception:
                pass

        clusters, _ = engine.discover(
            gsc_rows or [],
            pages=[],
            existing_slugs=existing_slugs,
            content_coverage=coverage,
        )

        results: list[dict] = []
        for cluster in clusters:
            for opp in cluster.opportunities[:3]:
                results.append({
                    "keyword": opp.keyword,
                    "type": opp.intent,
                    "cluster": cluster.cluster_name,
                    "difficulty": opp.estimated_difficulty,
                    "conversion_probability": opp.conversion_probability,
                    "recommended_page_type": cluster.recommended_asset_type,
                    "revenue_priority": opp.revenue_priority_score,
                    "coverage_status": opp.notes[-1] if opp.notes and "Coverage:" in opp.notes[-1] else "pending",
                })
        return results[:20]

    def _load_existing_slugs(self) -> set[str]:
        slugs: set[str] = set()
        state_path = self._state_dir / "latest_snapshot.json"
        if state_path.exists():
            try:
                data = json.loads(state_path.read_text(encoding="utf-8"))
                for p in data.get("pages", []):
                    url = p.get("url", "").rstrip("/")
                    slug = url.split("/")[-1] if url else ""
                    if slug:
                        slugs.add(slug)
            except Exception:
                pass
        return slugs

    def _run_content_engine(self, diff: SiteDiff, run_id: str, keywords: list[dict] | None = None) -> list[dict]:
        from agents.content_agent import ContentAgent
        from core.blog_content_engine import BlogContentEngine
        from core.content_engine import ContentEngine
        from utils.models import ContentAsset, KeywordCluster, KeywordOpportunity

        engine = ContentEngine(self.config, self.logger)
        blog_engine = BlogContentEngine(self.config, self.logger)

        generated: list[dict] = []

        # ── Build clusters from all keyword opportunities ──────────────────
        kw_source = keywords or getattr(self, 'keyword_opportunities', []) or []
        clusters: list[KeywordCluster] = []
        for i, kw in enumerate(kw_source):
            intent = kw.get("type", "informational")
            kw_lower = kw.get("keyword", "").lower()
            if intent in ("commercial", "transactional"):
                recommended = "blog_post"
            elif ("use case" in kw_lower
                  or "for" in kw_lower.split()[:1]):
                recommended = "use_case_page"
            elif any(term in kw_lower for term in ("case study", "client story", "success story", "how x", "how we", "roi of")):
                recommended = "case_study"
            else:
                recommended = "blog_post"
            cluster = KeywordCluster(
                cluster_name=kw.get("cluster", "general"),
                primary_keyword=kw.get("keyword", ""),
                intent=intent,
                recommended_asset_type=recommended,
                conversion_goal="Capture problem-aware pipeline",
                opportunities=[
                    KeywordOpportunity(
                        keyword=kw.get("keyword", ""),
                        topic_cluster=kw.get("cluster", "general"),
                        intent=intent,
                        funnel_stage=kw.get("funnel_stage", "awareness"),
                        source="seo_os",
                    )
                ],
            )
            clusters.append(cluster)

        self.logger.info(
            "ContentEngine: %d keyword opportunities available in %d clusters",
            len(kw_source), len(clusters),
        )

        # ── Delegate to ContentAgent which respects config per-run limits ──
        agent = ContentAgent(self.config, engine, self.logger)
        assets: list[ContentAsset] = agent.generate(clusters)
        limit_b = self.config.get("execution", {}).get("blog_posts_per_run", 4)
        limit_u = self.config.get("execution", {}).get("use_case_pages_per_run", 2)
        self.logger.info(
            "ContentAgent produce config limits: blog=%d use_case=%d | actual=%d assets",
            limit_b, limit_u, len(assets),
        )

        for asset in assets:
            generated.append({
                "type": asset.page_type,
                "style": "NEPQ" if asset.page_type == "blog_post" else "standard",
                "slug": asset.slug,
                "title": asset.title,
                "body_markdown": asset.body_markdown,
                "target_keyword": "",
                "meta_description": asset.meta_description or "",
                "internal_links": [],
                "status": "generated" if asset.body_markdown else "brief_ready",
            })

        # Log asset-type breakdown
        type_counts: dict[str, int] = {}
        for a in assets:
            type_counts[a.page_type] = type_counts.get(a.page_type, 0) + 1
        self.logger.info("ContentEngine output breakdown: %s", type_counts)

        # 3 glossary pages (hardcoded stubs are acceptable — these are reference content)
        glossary_terms = [
            {
                "type": "glossary_page",
                "slug": "outbound-sales-automation",
                "title": "Outbound Sales Automation",
                "definition": (
                    "Outbound sales automation is the use of software and AI to execute prospecting, "
                    "lead enrichment, personalised outreach, and follow-up sequences without manual rep effort."
                ),
                "related_terms": ["ICP scoring", "sales orchestration", "sales ops audit"],
                "internal_links": ["/", "/sales-ops-audit", "/glossary/icp-scoring"],
            },
            {
                "type": "glossary_page",
                "slug": "sales-orchestration",
                "title": "Sales Orchestration",
                "definition": (
                    "Sales orchestration is the coordination of every component in an outbound sales system — "
                    "lead sourcing, enrichment, personalisation, sequencing, reply handling, and CRM handoff — "
                    "into a single governed workflow."
                ),
                "related_terms": ["outbound sales automation", "sales ops", "sales operations"],
                "internal_links": ["/about", "/", "/glossary/outbound-sales-automation"],
            },
            {
                "type": "glossary_page",
                "slug": "sales-ops-audit",
                "title": "Sales Ops Audit",
                "definition": (
                    "A sales ops audit is a structured review of a company's outbound sales motion, "
                    "covering ICP definition, lead targeting, messaging quality, outreach workflow, and pipeline health."
                ),
                "related_terms": ["ICP scoring", "outbound sales automation", "sales ops"],
                "internal_links": ["/sales-ops-audit", "/glossary/icp-scoring", "/glossary/outbound-sales-automation"],
            },
        ]
        generated.extend(glossary_terms)

        # Final summary
        self.logger.info(
            "_run_content_engine total: %d assets (%d non-glossary + 3 glossary stubs)",
            len(generated), len(generated) - 3,
        )
        return generated

    def _run_tool_engine(self) -> list[dict]:
        """Generate tool entries for categories that need them."""
        from core.tool_content_engine import ToolContentEngine
        from connectors.github_publisher import GitHubPublisher

        import json
        from pathlib import Path

        exec_cfg = self.config.get("execution", {})
        tools_per_run = exec_cfg.get("tools_per_run", 0)
        if not tools_per_run or tools_per_run <= 0:
            self.logger.info("Tool generation disabled (tools_per_run=%d)", tools_per_run)
            return []

        frontend_dir = Path(__file__).resolve().parent.parent / "temp_frontend_repo"
        tools_data_dir = frontend_dir / "src" / "data" / "tools"

        if not tools_data_dir.exists():
            self.logger.warning("Tools data directory not found at %s", tools_data_dir)
            return []

        # ── Read existing tool slugs ──
        existing_slugs: set[str] = set()
        existing_names: set[str] = set()
        for ts_file in tools_data_dir.glob("*.ts"):
            if ts_file.name in ("index.ts", "categories.ts"):
                continue
            text = ts_file.read_text(encoding="utf-8")
            for m in re.finditer(r"slug:\s*`([^`]+)`", text):
                existing_slugs.add(m.group(1))
            for m in re.finditer(r"name:\s*`([^`]+)`", text):
                existing_names.add(m.group(1).lower())

        self.logger.info(
            "ToolEngine: %d existing slugs, %d existing names",
            len(existing_slugs), len(existing_names),
        )

        # ── Read existing category slugs ──
        cat_file = tools_data_dir / "categories.ts"
        existing_cats: set[str] = set()
        if cat_file.exists():
            text = cat_file.read_text(encoding="utf-8")
            for m in re.finditer(r"slug:\s*`([^`]+)`", text):
                existing_cats.add(m.group(1))

        # ── Determine which categories need tools ──
        from core.tool_content_engine import CATEGORY_DESCRIPTIONS

        needed_cats: list[str] = []
        for cat_slug in CATEGORY_DESCRIPTIONS:
            cat_file_path = tools_data_dir / f"{cat_slug}.ts"
            count_in_cat = 0
            if cat_file_path.exists():
                text = cat_file_path.read_text(encoding="utf-8")
                count_in_cat = len(re.findall(r"slug:\s*`", text))
            target = 40
            if count_in_cat < target:
                needed_cats.append(cat_slug)

        self.logger.info(
            "ToolEngine: %d/%d categories need tools (target=%d per cat)",
            len(needed_cats), len(CATEGORY_DESCRIPTIONS), target,
        )

        if not needed_cats:
            self.logger.info("ToolEngine: all categories at target — nothing to generate")
            return []

        engine = ToolContentEngine(self.config, self.logger)
        publisher = GitHubPublisher()

        # Round-robin across needed categories
        total_new = 0
        results: list[dict] = []
        per_cat = max(1, tools_per_run // len(needed_cats))

        for cat_slug in needed_cats:
            if total_new >= tools_per_run:
                break

            batch = engine.generate(
                category_slug=cat_slug,
                count=per_cat,
                existing_slugs=existing_slugs,
                existing_names=existing_names,
            )

            if not batch:
                continue

            # Write to local TS files
            publisher.publish_tool_data_local(
                tools=batch,
                category_slug=cat_slug,
                frontend_dir=str(frontend_dir),
            )

            for t in batch:
                slug = t.get("slug", "?")
                existing_slugs.add(slug)
                existing_slugs.add(f"tools/{cat_slug}/{slug}")
                existing_names.add(t.get("name", "").lower())
                results.append({
                    "type": "tool",
                    "slug": slug,
                    "name": t.get("name", ""),
                    "categorySlug": cat_slug,
                    "tagline": t.get("tagline", ""),
                    "status": "generated",
                })
            total_new += len(batch)
            self.logger.info("ToolEngine: %d tools generated for category %s", len(batch), cat_slug)

        self.logger.info("ToolEngine complete: %d new tools across %d categories", total_new, len(results))
        return results

    def _run_onpage_optimizer(self, snapshot: SiteSnapshot, diff: SiteDiff) -> list[dict]:
        from modules.pipeleap_seo_engine.data.serp_strategy import META_TARGETS

        optimised: list[dict] = []
        page_index = snapshot.page_index()

        priority_paths = ["/sales-ops-audit", "/", "/pricing"]
        for path in priority_paths:
            url = self.site_url + path
            page = page_index.get(url) or page_index.get(self.site_url + path + "/")
            meta = next((m for m in META_TARGETS if m["path"] == path), None)

            if not meta:
                continue

            current_title = page.title if page else ""
            current_meta = page.meta_description if page else ""
            issues: list[str] = []

            if current_title != meta["title"]:
                issues.append(f"Title: update to '{meta['title']}'")
            if current_meta != meta["meta_description"]:
                issues.append(f"Meta: update to '{meta['meta_description']}'")
            if page and not page.h1:
                issues.append("H1: missing — add keyword-anchored H1")

            if issues:
                optimised.append({
                    "page_url": url,
                    "recommended_title": meta["title"],
                    "recommended_meta": meta["meta_description"],
                    "current_title": current_title,
                    "current_meta": current_meta,
                    "optimisation_actions": issues,
                    "safe_mode": True,
                    "note": "Metadata only — no structural code changes required.",
                })

        return optimised[:3]

    def _run_linking_engine(self, snapshot: SiteSnapshot, diff: SiteDiff) -> list[dict]:
        from modules.pipeleap_seo_engine.data.serp_strategy import LINKING_CLUSTERS

        published = self._load_published_urls_from_launchpad()

        def _slug(p: str) -> str:
            raw = p.rstrip("/")
            if not raw:
                return "index"
            seg = raw.rsplit("/", 1)[-1]
            return seg if seg else "index"

        def _url_exists(url: str) -> bool:
            slug = _slug(url)
            return slug in published

        suggestions: list[dict] = []
        for cluster_def in LINKING_CLUSTERS:
            for spoke in cluster_def["spoke_articles"]:
                if not (_url_exists(spoke) and _url_exists(cluster_def["pillar_page"])):
                    continue
                suggestions.append({
                    "from_page": spoke,
                    "to_page": cluster_def["pillar_page"],
                    "anchor_text": cluster_def["cluster"].lower(),
                    "placement": "First 200 words or within the most relevant section",
                    "cluster": cluster_def["cluster"],
                    "priority": "high",
                    "note": "Content-level link only — no structural changes needed.",
                })
            for glossary in cluster_def.get("glossary_links", []):
                if not (_url_exists(cluster_def["pillar_page"]) and _url_exists(glossary)):
                    continue
                suggestions.append({
                    "from_page": cluster_def["pillar_page"],
                    "to_page": glossary,
                    "anchor_text": glossary.split("/")[-1].replace("-", " "),
                    "placement": "Inline where the term is first mentioned",
                    "cluster": cluster_def["cluster"],
                    "priority": "medium",
                })
        return suggestions

    def _load_published_urls_from_launchpad(self) -> set[str]:
        import re
        launchpad_root = Path(__file__).resolve().parent.parent / "temp_frontend_repo"
        data_dir = launchpad_root / "src" / "data"
        slugs: set[str] = set()

        blog_path = data_dir / "blog-articles.ts"
        if blog_path.exists():
            slugs.update(re.findall(r'slug["`\']?\s*:\s*["`\']([a-z0-9-]+)["`\']', blog_path.read_text(encoding="utf-8")))

        glossary_path = data_dir / "glossary-terms.ts"
        if glossary_path.exists():
            slugs.update(re.findall(r'slug:\s*["`]([a-z0-9-]+)["`]', glossary_path.read_text(encoding="utf-8")))

        tools_dir = data_dir / "tools"
        if tools_dir.is_dir():
            for tf in tools_dir.iterdir():
                if tf.suffix == ".ts":
                    slugs.update(re.findall(r'slug["`\']?\s*:\s*["`\']([a-z0-9-]+)["`\']', tf.read_text(encoding="utf-8")))

        slugs.update([
            "index", "services", "how-it-works", "results",
            "sales-ops-audit", "pricing", "about", "contact", "faq", "privacy",
        ])
        return slugs

    def _run_ga4_audit(self) -> list[dict]:
        from connectors.ga4_connector import GA4Connector
        ga4 = GA4Connector(self.config, self.logger)
        if not ga4.is_connected():
            return []

        insights: list[dict] = []

        # High-bounce pages — engaged session rate < 20% and >= 100 sessions
        pages = ga4.fetch_top_pages(start_date="28daysAgo", end_date="today", limit=50)
        for page in pages:
            sessions = page.get("sessions", 0)
            bounce   = page.get("bounce_rate", 0.0)
            if sessions >= 100 and bounce > 0.80:
                insights.append({
                    "source": "GA4",
                    "type": "high_bounce_rate",
                    "severity": "High" if bounce > 0.90 else "Medium",
                    "page": page["page_path"],
                    "sessions": sessions,
                    "bounce_rate_pct": round(bounce * 100, 1),
                    "recommendation": (
                        f"Bounce rate is {round(bounce*100,1)}% on {sessions} sessions. "
                        "Users are leaving without engaging. Audit page intent match, "
                        "CTA placement, and load speed."
                    ),
                })

        # Channel summary — flag if Organic Search < 20% of total sessions
        channels = ga4.fetch_channel_summary(start_date="28daysAgo", end_date="today")
        total_sessions = sum(c.get("sessions", 0) for c in channels)
        organic = next((c for c in channels if "organic" in c.get("channel", "").lower()), {})
        organic_sessions = organic.get("sessions", 0)
        if total_sessions > 0:
            organic_pct = round(organic_sessions / total_sessions * 100, 1)
            if organic_pct < 20:
                insights.append({
                    "source": "GA4",
                    "type": "low_organic_share",
                    "severity": "High" if organic_pct < 10 else "Medium",
                    "organic_sessions": organic_sessions,
                    "total_sessions": total_sessions,
                    "organic_pct": organic_pct,
                    "recommendation": (
                        f"Organic Search is only {organic_pct}% of traffic ({organic_sessions}/{total_sessions} sessions). "
                        "SEO investment is under-delivering. Prioritise content velocity and technical fixes."
                    ),
                })

        insights.sort(key=lambda x: 0 if x.get("severity") == "High" else 1)
        self.logger.info("GA4 audit: %d insights", len(insights))
        return insights[:15]

    def _run_gsc_performance_audit(self) -> tuple[list[dict], list[dict]]:
        from connectors.gsc_connector import GoogleSearchConsoleConnector
        gsc = GoogleSearchConsoleConnector(self.config, self.logger)
        site_url = gsc.site_url or "unknown"
        current_rows, previous_rows = gsc.fetch_two_periods(days_per_period=28, row_limit=500)
        if not current_rows:
            self.logger.warning("GSC returned 0 rows for site_url=%s — check credentials and property", site_url)
            return [], []

        def _aggregate(rows: list[dict]) -> dict[str, dict]:
            agg: dict[str, dict] = {}
            for row in rows:
                page = row.get("page", "")
                if not page:
                    continue
                if page not in agg:
                    agg[page] = {"clicks": 0, "impressions": 0, "position_sum": 0.0, "position_count": 0}
                agg[page]["clicks"] += row.get("clicks", 0)
                agg[page]["impressions"] += row.get("impressions", 0)
                agg[page]["position_sum"] += row.get("position", 0.0)
                agg[page]["position_count"] += 1
            for d in agg.values():
                d["position"] = d["position_sum"] / d["position_count"] if d["position_count"] else 0.0
            return agg

        current = _aggregate(current_rows)
        previous = _aggregate(previous_rows)
        insights: list[dict] = []

        for page, curr in current.items():
            prev = previous.get(page, {})
            prev_imp = prev.get("impressions", 0)
            curr_imp = curr["impressions"]
            curr_pos = curr["position"]
            prev_pos = prev.get("position", 0.0)

            # Position drop — page moved down > 5 spots vs previous period
            if prev_imp >= 10 and prev_pos > 0 and curr_pos - prev_pos > 5:
                insights.append({
                    "type": "position_drop",
                    "severity": "High" if curr_pos - prev_pos > 10 else "Medium",
                    "page": page,
                    "current_position": round(curr_pos, 1),
                    "previous_position": round(prev_pos, 1),
                    "drop": round(curr_pos - prev_pos, 1),
                    "impressions": curr_imp,
                    "recommendation": (
                        f"Position dropped {round(curr_pos - prev_pos, 1)} spots "
                        f"({round(prev_pos,1)} → {round(curr_pos,1)}). "
                        "Refresh content, strengthen E-E-A-T signals, and audit competing SERP pages."
                    ),
                })

            # Low CTR — ≥100 impressions but CTR < 1%
            if curr_imp >= 100 and curr["clicks"] < curr_imp * 0.01:
                ctr_pct = round(curr["clicks"] / curr_imp * 100, 2)
                insights.append({
                    "type": "low_ctr",
                    "severity": "Medium",
                    "page": page,
                    "impressions": curr_imp,
                    "clicks": curr["clicks"],
                    "ctr_percent": ctr_pct,
                    "avg_position": round(curr_pos, 1),
                    "recommendation": (
                        f"CTR is {ctr_pct}% on {curr_imp} impressions at position {round(curr_pos,1)}. "
                        "Rewrite title and meta description to match search intent and improve click appeal."
                    ),
                })

        # Impression decay — page was visible last period, largely gone now
        for page, prev in previous.items():
            if prev["impressions"] < 50:
                continue
            curr_imp = current.get(page, {}).get("impressions", 0)
            decay_pct = round((1 - curr_imp / prev["impressions"]) * 100, 1)
            if decay_pct > 50:
                insights.append({
                    "type": "impression_decay",
                    "severity": "High",
                    "page": page,
                    "previous_impressions": prev["impressions"],
                    "current_impressions": curr_imp,
                    "decay_percent": decay_pct,
                    "recommendation": (
                        f"Impressions dropped {decay_pct}% "
                        f"({prev['impressions']} → {curr_imp}). "
                        "Check URL Inspection for de-indexing, crawl errors, or SERP feature cannibalisation."
                    ),
                })

        insights.sort(key=lambda x: (0 if x["severity"] == "High" else 1, -x.get("impressions", 0)))
        return insights[:20], current_rows

    def _detect_event_content_opportunities(self) -> list[dict]:
        """Detect upcoming sales events and generate targeted content opportunities."""
        now = datetime.now(timezone.utc)
        month = now.month
        day = now.day

        events: list[dict] = []

        # SKO season (Jan-Feb): sales kickoff planning
        if month in (1, 2):
            events.append({
                "keyword": "sales kickoff productivity initiatives",
                "type": "event_trigger",
                "cluster": "sales productivity",
                "difficulty": 25,
                "conversion_probability": 0.6,
                "recommended_page_type": "blog_post",
                "revenue_priority": 65,
                "coverage_status": "pending",
            })
            events.append({
                "keyword": "reduce non-selling time before sales kickoff",
                "type": "event_trigger",
                "cluster": "reducing non-selling time",
                "difficulty": 20,
                "conversion_probability": 0.5,
                "recommended_page_type": "blog_post",
                "revenue_priority": 60,
                "coverage_status": "pending",
            })

        # QBR cycles (Mar, Jun, Sep, Dec — quarter-end)
        if month in (3, 6, 9, 12) and day >= 15:
            events.append({
                "keyword": "QBR sales process improvements",
                "type": "event_trigger",
                "cluster": "sales workflow operations",
                "difficulty": 28,
                "conversion_probability": 0.65,
                "recommended_page_type": "blog_post",
                "revenue_priority": 70,
                "coverage_status": "pending",
            })
            events.append({
                "keyword": "pipeline review operational bottlenecks",
                "type": "event_trigger",
                "cluster": "sales workflow operations",
                "difficulty": 22,
                "conversion_probability": 0.55,
                "recommended_page_type": "blog_post",
                "revenue_priority": 62,
                "coverage_status": "pending",
            })

        # Mid-year review (Jun-Jul)
        if month in (6, 7):
            events.append({
                "keyword": "mid year sales productivity review",
                "type": "event_trigger",
                "cluster": "sales productivity",
                "difficulty": 24,
                "conversion_probability": 0.6,
                "recommended_page_type": "blog_post",
                "revenue_priority": 64,
                "coverage_status": "pending",
            })

        # Revenue planning (Nov-Dec)
        if month in (11, 12):
            events.append({
                "keyword": "revenue planning operational efficiency",
                "type": "event_trigger",
                "cluster": "sales workflow operations",
                "difficulty": 30,
                "conversion_probability": 0.7,
                "recommended_page_type": "blog_post",
                "revenue_priority": 75,
                "coverage_status": "pending",
            })

        # Pipeline review (always relevant, boosted quarter-end)
        if month in (1, 4, 7, 10) and day <= 15:
            events.append({
                "keyword": "pipeline review meeting preparation",
                "type": "event_trigger",
                "cluster": "sales productivity",
                "difficulty": 18,
                "conversion_probability": 0.5,
                "recommended_page_type": "blog_post",
                "revenue_priority": 55,
                "coverage_status": "pending",
            })

        return events

    @staticmethod
    def _merge_keyword_opportunities(existing: list[dict], new: list[dict]) -> list[dict]:
        seen = {kw.get("keyword", "") for kw in existing if kw.get("keyword")}
        for item in new:
            if item.get("keyword", "") not in seen:
                existing.append(item)
                seen.add(item["keyword"])
        return existing

    def _build_indexing_actions(self, diff: SiteDiff, snapshot: SiteSnapshot) -> list[dict]:
        from connectors.gsc_connector import GoogleSearchConsoleConnector
        gsc = GoogleSearchConsoleConnector(self.config, self.logger)
        actions: list[dict] = []

        # (new-pages Indexing API + GSC sitemap removed — handled by PostPublishHook)

        # Pages missing from sitemap — flag for manual addition
        for url in diff.missing_from_sitemap[:5]:
            actions.append({
                "action": "add_to_sitemap",
                "url": url,
                "reason": "Indexable page absent from sitemap.xml",
                "priority": 2,
            })

        # Updated pages with key SEO field changes — request re-crawl
        updated_urls = [
            c.url for c in diff.updated_pages
            if any(f in c.fields_changed for f in ["title", "meta_description", "h1"])
        ]
        if updated_urls:
            reindex_results = gsc.request_indexing(updated_urls[:5])
            for res in reindex_results:
                actions.append({
                    "action": "refresh_index",
                    "url": res["url"],
                    "reason": "Key SEO fields updated — re-crawl requested via Indexing API",
                    "status": "submitted" if res.get("ok") else f"failed: {res.get('error', '')}",
                    "priority": 2,
                })

        return actions

    def _identify_risks(self, diff: SiteDiff, snapshot: SiteSnapshot, result: SEOOSResult) -> list[dict]:
        risks: list[dict] = []

        if diff.broken_links:
            risks.append({
                "type": "broken_pages",
                "severity": "critical",
                "description": f"{len(diff.broken_links)} pages returning 4xx/5xx — immediate ranking risk.",
                "urls": [b["url"] for b in diff.broken_links],
            })

        if len(diff.orphan_pages) > 5:
            risks.append({
                "type": "orphan_pages",
                "severity": "warning",
                "description": f"{len(diff.orphan_pages)} orphan pages detected. Google may deprioritise discovery.",
                "urls": diff.orphan_pages[:5],
            })

        if diff.deleted_pages:
            risks.append({
                "type": "deleted_pages",
                "severity": "critical",
                "description": f"{len(diff.deleted_pages)} pages were deleted. Check for 301 redirect needs.",
                "urls": [p.url for p in diff.deleted_pages],
            })

        missing_canonical = [p for p in snapshot.pages if not p.canonical and p.status_code == 200]
        if missing_canonical:
            risks.append({
                "type": "missing_canonical",
                "severity": "warning",
                "description": f"{len(missing_canonical)} pages are missing a canonical URL — search engines may cluster incorrectly.",
                "urls": [p.url for p in missing_canonical[:5]],
            })

        noindex_pages = [p for p in snapshot.pages if "noindex" in p.meta_robots.lower() and p.status_code == 200]
        if noindex_pages:
            risks.append({
                "type": "noindex_detected",
                "severity": "info",
                "description": f"{len(noindex_pages)} pages have a 'noindex' robots meta tag and will not be indexed by search engines.",
                "urls": [p.url for p in noindex_pages[:5]],
            })

        no_schema = [p for p in snapshot.pages if not p.has_schema and p.status_code == 200]
        if len(no_schema) > 3:
            risks.append({
                "type": "missing_schema",
                "severity": "info",
                "description": f"{len(no_schema)} pages lack schema markup — missed rich result eligibility.",
                "urls": [p.url for p in no_schema[:3]],
            })

        return risks

    def _compute_seo_score(self, diff: SiteDiff, snapshot: SiteSnapshot, result: SEOOSResult) -> SEOScore:
        score = SEOScore()

        # Technical: start from audit engine results when available, else use heuristics
        audit_issues = getattr(snapshot, "audit_issues", [])
        critical_count = sum(1 for i in audit_issues if i.severity == "Critical")
        high_count = sum(1 for i in audit_issues if i.severity == "High")
        medium_count = sum(1 for i in audit_issues if i.severity == "Medium")
        tech = 100
        tech -= critical_count * 12
        tech -= high_count * 5
        tech -= medium_count * 2
        tech -= len(diff.broken_links) * 8
        tech -= 10 if not snapshot.robots_present else 0
        tech -= len(diff.deleted_pages) * 4
        tech = max(0, min(100, tech))

        # Content: pages with title + meta + h1
        pages_with_meta = sum(1 for p in snapshot.pages if p.title and p.meta_description and p.h1)
        content = int((pages_with_meta / max(len(snapshot.pages), 1)) * 100)

        # Indexing: sitemap coverage
        in_sitemap = sum(1 for p in snapshot.pages if p.in_sitemap and p.status_code == 200)
        indexing = int((in_sitemap / max(len(snapshot.pages), 1)) * 100)

        # Authority: schema coverage proxy
        with_schema = sum(1 for p in snapshot.pages if p.has_schema)
        authority = int((with_schema / max(len(snapshot.pages), 1)) * 100)

        overall = int(tech * 0.30 + content * 0.30 + indexing * 0.25 + authority * 0.15)

        score.technical = tech
        score.content = content
        score.indexing = indexing
        score.authority = authority
        score.overall = overall
        score.breakdown = {
            "pages_with_full_metadata": pages_with_meta,
            "total_pages": len(snapshot.pages),
            "pages_in_sitemap": in_sitemap,
            "pages_with_schema": with_schema,
            "broken_pages": len(diff.broken_links),
            "orphan_pages": len(diff.orphan_pages),
            "audit_critical": critical_count,
            "audit_high": high_count,
            "audit_medium": medium_count,
            "audit_total": len(audit_issues),
        }
        return score

    def _build_next_day_plan(self, result: SEOOSResult) -> list[str]:
        plan: list[str] = []

        high = [a for a in result.safe_actions if a.get("priority") == 1]
        if high:
            plan.append(f"Execute {len(high)} high-priority safe actions from execution_plan.json")

        if result.dev_review_items:
            plan.append(f"Flag {len(result.dev_review_items)} items for dev review — see daily_briefing.md")

        if result.content_generated:
            plan.append(f"Publish {len(result.content_generated)} content pieces — start with blog post (highest conversion cluster)")

        if result.indexing_actions:
            submit = [a for a in result.indexing_actions if a.get("priority") == 1]
            if submit:
                plan.append(f"Submit {len(submit)} new/updated pages in GSC URL Inspection")

        gsc_high = [i for i in result.gsc_insights if i.get("severity") == "High"]
        if gsc_high:
            plan.append(f"Address {len(gsc_high)} High-severity GSC signal(s): position drops and impression decay — see gsc_insights.json")
        low_ctr = [i for i in result.gsc_insights if i.get("type") == "low_ctr"]
        if low_ctr:
            plan.append(f"Rewrite title/meta for {len(low_ctr)} page(s) with CTR < 1% despite high impressions")
        plan.append("Monitor GSC for CTR changes on any updated meta descriptions (48-hour window)")

        if result.seo_score.overall < 60:
            plan.append("SEO score below 60 — prioritise technical fixes before content expansion")

        return plan[:7]

    def _build_daily_briefing(self, result: SEOOSResult, diff: SiteDiff, plan: ExecutionPlan) -> str:
        score = result.seo_score
        score_bar = "█" * (score.overall // 10) + "░" * (10 - score.overall // 10)
        prev = self._load_previous_run_summary()

        def _trend(current: int, previous_key: str) -> str:
            p = prev.get(previous_key, 0)
            if not p:
                return ""
            d = current - p
            if d > 0:
                return f" ▲ +{d}"
            if d < 0:
                return f" ▼ {d}"
            return "  —"

        score_trend = _trend(score.overall, "seo_score")
        tech_trend = _trend(score.technical, "technical")
        content_trend = _trend(score.content, "content")
        idx_trend = _trend(score.indexing, "indexing")
        auth_trend = _trend(score.authority, "authority")
        prev_top = prev.get("top_keywords", [])

        lines = [
            f"# Pipeleap SEO OS — Daily Briefing",
            f"**Run ID:** {result.run_id}  |  **Mode:** {result.mode.upper()}  |  **Generated:** {result.generated_at}",
            "",
            f"## Score: {score.overall}/100  [{score_bar}]{score_trend}",
            f"| Dimension | Score | Change |",
            f"|---|---|---|",
            f"| Technical | {score.technical}/100 |{tech_trend} |",
            f"| Content | {score.content}/100 |{content_trend} |",
            f"| Indexing | {score.indexing}/100 |{idx_trend} |",
            f"| Authority | {score.authority}/100 |{auth_trend} |",
        ]

        # ── What Changed Since Yesterday ──────────────────────────────────────
        deltas: list[str] = []
        if prev:
            prev_content = prev.get("content_pieces", 0)
            cur_content = len(result.content_generated)
            if cur_content > prev_content:
                deltas.append(f"**+{cur_content - prev_content}** new content piece(s) generated")
            elif cur_content < prev_content:
                deltas.append(f"Content pieces dropped from {prev_content} → {cur_content}")
            prev_gaps = prev.get("content_gaps", 0)
            cur_gaps = len(result.content_gaps)
            if cur_gaps > prev_gaps:
                deltas.append(f"**+{cur_gaps - prev_gaps}** new content gap(s) detected ({cur_gaps} total)")
            elif cur_gaps > 0 and cur_gaps == prev_gaps:
                deltas.append(f"Content gap count unchanged: {cur_gaps} gaps remain open")
            prev_latent = prev.get("latent_keywords", 0)
            cur_latent = len(result.latent_keywords)
            if cur_latent > prev_latent:
                deltas.append(f"**+{cur_latent - prev_latent}** new latent keyword(s) mined from existing content")
            prev_actions = prev.get("actions_generated", 0)
            cur_actions = len(result.safe_actions)
            if cur_actions > prev_actions:
                deltas.append(f"**+{cur_actions - prev_actions}** new safe SEO action(s) available")
            prev_opt = prev.get("pages_optimized", 0)
            cur_opt = len(result.pages_optimized)
            if cur_opt > prev_opt:
                deltas.append(f"**+{cur_opt - prev_opt}** page(s) optimized since last run")
            if result.errors and len(result.errors) != prev.get("errors", 0):
                deltas.append(f"**⚠ {len(result.errors)} error(s)** — check logs")

        if not deltas:
            deltas.append("No measurable changes since last run — growth mode holding steady.")

        lines += ["", "---", "", "## Δ What Changed Since Yesterday"]
        for d in deltas:
            lines.append(f"- {d}")

        # ── 1. Website Changes ────────────────────────────────────────────────
        changes = result.website_changes
        if changes.get("has_changes"):
            lines += ["", "---", "", "## 1. Website Changes"]
            lines += [
                f"- New pages: **{changes.get('new_pages', 0)}**",
                f"- Updated pages: **{changes.get('updated_pages', 0)}**",
                f"- Deleted pages: **{changes.get('deleted_pages', 0)}**",
                f"- Broken links: **{changes.get('broken_links', 0)}**",
                f"- Orphan pages: **{changes.get('orphan_pages', 0)}**",
            ]

        # ── 2. Safe SEO Actions ──────────────────────────────────────────────
        if result.safe_actions:
            lines += ["", "---", "", "## 2. Safe SEO Actions"]
            for action in result.safe_actions[:8]:
                lines.append(f"- [{action.get('category','').upper()}] **{action.get('title','')}** — `{action.get('page_url','')}`")

        # ── 3. Dev Review ────────────────────────────────────────────────────
        if result.dev_review_items:
            lines += ["", "---", "", "## 3. REQUIRES DEV REVIEW"]
            critical_high = [i for i in result.dev_review_items if i.get("severity") in ("Critical", "High")]
            for item in result.dev_review_items:
                lines.append(f"- **{item.get('title','')}** — `{item.get('page_url','')}` — {item.get('dev_note','')}")
            if critical_high:
                lines += ["", "### Critical / High Issues"]
                for issue in critical_high[:8]:
                    fix = issue.get("fix_instructions", "")
                    lines.append(f"- [{issue['severity'].upper()}] **{issue.get('title','')}** — `{issue.get('page_url','')}`")
                    if fix:
                        lines.append(f"  > {fix[:120]}{'…' if len(fix) > 120 else ''}")

        # ── 4. Keywords + Gaps ───────────────────────────────────────────────
        if result.keyword_opportunities:
            lines += ["", "---", "", "## 4. Keyword Opportunities"]
            for kw in result.keyword_opportunities[:10]:
                t = kw.get("type", "")
                kw_name = kw.get("keyword", "")
                new_badge = ""
                if prev_top and kw_name not in prev_top:
                    new_badge = " 🆕"
                lines.append(f"- [{t}]{new_badge} **{kw_name}** — {kw.get('cluster', kw.get('gap_source',''))}")

        if result.content_gaps:
            lines += ["", "---", "", "## 4b. Content Gaps (Uncovered)"]
            for gap in result.content_gaps[:8]:
                kw = gap.get("keyword", "")
                diff_val = gap.get("difficulty", "?")
                lines.append(f"- **{kw}** (difficulty: {diff_val})")
            if len(result.content_gaps) > 8:
                lines.append(f"- … and {len(result.content_gaps) - 8} more — see content_coverage.json")

        if result.latent_keywords:
            lines += ["", "---", "", "## 4c. Latent Keywords (Mined from Content)"]
            for lk in result.latent_keywords[:10]:
                lines.append(f"- **{lk.get('keyword','')}** (freq: {lk.get('frequency',0)}, score: {lk.get('score',0)})")
            if len(result.latent_keywords) > 10:
                lines.append(f"- … and {len(result.latent_keywords) - 10} more — see latent_keywords.json")

        # ── 5. Content Generated ────────────────────────────────────────────
        if result.content_generated:
            lines += ["", "---", "", "## 5. Content Generated"]
            for item in result.content_generated:
                lines.append(f"- [{item.get('type','')}] **{item.get('title', item.get('slug',''))}**")

        # ── 6. Pages Optimized ──────────────────────────────────────────────
        if result.pages_optimized:
            lines += ["", "---", "", "## 6. Pages Optimized"]
            for page in result.pages_optimized:
                lines.append(f"- `{page.get('page_url','')}` — {' | '.join(page.get('optimisation_actions', []))}")

        # ── 7. Internal Linking ─────────────────────────────────────────────
        if result.linking_suggestions:
            lines += ["", "---", "", "## 7. Internal Linking"]
            for link in result.linking_suggestions[:5]:
                lines.append(f"- `{link.get('from_page','')}` → `{link.get('to_page','')}` via \"{link.get('anchor_text','')}\"")

        # ── 8. Indexing Actions ─────────────────────────────────────────────
        if result.indexing_actions:
            lines += ["", "---", "", "## 8. Indexing Actions"]
            for action in result.indexing_actions[:6]:
                status = action.get("status", "")
                status_str = f" → **{status}**" if status else ""
                lines.append(f"- [{action.get('action','')}] `{action.get('url','')}` — {action.get('reason','')}{status_str}")

        # ── 9b. GSC Performance ─────────────────────────────────────────────
        if result.gsc_insights:
            lines += ["", "---", "", "## 9. GSC Performance Signals"]
            high = [i for i in result.gsc_insights if i.get("severity") == "High"]
            med  = [i for i in result.gsc_insights if i.get("severity") == "Medium"]
            if high:
                lines.append(f"**{len(high)} High-severity signal(s):**")
                for insight in high[:5]:
                    lines.append(f"- [{insight['type'].upper()}] `{insight['page']}`")
                    lines.append(f"  > {insight.get('recommendation', '')}")
            if med:
                lines.append(f"**{len(med)} Medium-severity signal(s):**")
                for insight in med[:5]:
                    lines.append(f"- [{insight['type'].upper()}] `{insight['page']}`")
                    lines.append(f"  > {insight.get('recommendation', '')}")

        # ── 10. Risks ───────────────────────────────────────────────────────
        if result.risks_and_missed:
            lines += ["", "---", "", "## 10. Risks / Missed Opportunities"]
            for risk in result.risks_and_missed:
                sev = risk.get("severity","").upper()
                lines.append(f"- [{sev}] **{risk.get('type','')}** — {risk.get('description','')}")

        # ── 11. Tomorrow's Plan ─────────────────────────────────────────────
        lines += ["", "---", "", "## 11. Tomorrow's Plan"]
        if result.next_day_plan:
            for i, item in enumerate(result.next_day_plan, 1):
                lines.append(f"{i}. {item}")
        else:
            lines.append("No actionable items — system idle.")

        lines += ["", "---", f"*SEO OS v{SEOOSAgent.VERSION} — {result.mode} — {result.run_id}*"]
        return "\n".join(lines)

    # ── State persistence ──────────────────────────────────────────────────────

    def _save_snapshot(self, snapshot: SiteSnapshot) -> None:
        path = self._state_dir / "latest_snapshot.json"
        path.write_text(json.dumps(snapshot.to_dict(), indent=2, default=str), encoding="utf-8")

    def _load_previous_snapshot(self) -> SiteSnapshot | None:
        path = self._state_dir / "latest_snapshot.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            from core.snapshot_engine import PageSEOState
            snap = SiteSnapshot(
                run_id=data.get("run_id", ""),
                site_url=data.get("site_url", ""),
                captured_at=data.get("captured_at", ""),
            )
            snap.sitemap_urls = data.get("sitemap_urls", [])
            snap.robots_present = data.get("robots_present", False)
            snap.total_pages = data.get("total_pages", 0)
            snap.pages = [PageSEOState(**{k: v for k, v in p.items() if k in PageSEOState.__dataclass_fields__}) for p in data.get("pages", [])]
            return snap
        except Exception as exc:
            self.logger.warning("Could not load previous snapshot: %s", exc)
            return None

    def _update_learning_log(self, run_id: str, result: SEOOSResult) -> None:
        log_path = self._state_dir / "learning_log.jsonl"
        entry = {
            "run_id": run_id,
            "generated_at": result.generated_at,
            "seo_score": result.seo_score.overall,
            "technical": result.seo_score.technical,
            "content": result.seo_score.content,
            "indexing": result.seo_score.indexing,
            "authority": result.seo_score.authority,
            "mode": result.mode,
            "actions_generated": len(result.safe_actions),
            "dev_items": len(result.dev_review_items),
            "content_pieces": len(result.content_generated),
            "content_gaps": len(result.content_gaps),
            "latent_keywords": len(result.latent_keywords),
            "top_keywords": [kw.get("keyword", "") for kw in result.keyword_opportunities[:5]],
            "pages_optimized": len(result.pages_optimized),
            "errors": len(result.errors),
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _load_previous_run_summary(self) -> dict:
        """Load the most recent completed run from learning log for trend comparison."""
        log_path = self._state_dir / "learning_log.jsonl"
        if not log_path.exists():
            return {}
        try:
            entries = []
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
            if len(entries) < 2:
                return {}
            return entries[-2]
        except Exception:
            return {}

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
