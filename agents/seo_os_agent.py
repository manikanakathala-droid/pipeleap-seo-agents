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
  Step 6:  Content engine (1 NEPQ blog + 3 glossary pages)
  Step 7:  On-page optimisation (3 pages: titles, meta, headers)
  Step 8:  Internal linking strategy
  Step 9:  Competitor analysis (2 competitors, keyword gaps)
  Step 10: Indexing recommendations
  Step 11: Self-improvement loop (prioritise, de-duplicate, score)

Output: structured JSON report + human-readable daily briefing
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    pages_optimized: list[dict] = field(default_factory=list)
    linking_suggestions: list[dict] = field(default_factory=list)
    competitor_insights: list[dict] = field(default_factory=list)
    indexing_actions: list[dict] = field(default_factory=list)
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
            "pages_optimized": self.pages_optimized,
            "linking_suggestions": self.linking_suggestions,
            "competitor_insights": self.competitor_insights,
            "indexing_actions": self.indexing_actions,
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
        self.site_url = config.get("site", {}).get("site_url", "https://pipeleap.com").rstrip("/")
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
        try:
            technical_issues = self._run_technical_audit(current_snapshot, diff)
            for issue in technical_issues:
                if issue.get("requires_dev"):
                    result.dev_review_items.append(issue)
                else:
                    result.safe_actions.append(issue)
        except Exception as exc:
            self.logger.warning("Technical audit skipped: %s", exc)

        # ── Step 5: Keyword Engine ────────────────────────────────────────────
        self.logger.info("Step 5: Keyword engine")
        try:
            keywords = self._run_keyword_engine(diff)
            result.keyword_opportunities = keywords
            self._write_json(output_dir / "keyword_opportunities.json", keywords)
        except Exception as exc:
            self.logger.warning("Keyword engine skipped: %s", exc)
            result.errors.append(f"keyword_engine: {exc}")

        # ── Step 6: Content Engine ────────────────────────────────────────────
        self.logger.info("Step 6: Content engine")
        try:
            content = self._run_content_engine(diff, run_id)
            result.content_generated = content
            self._write_json(output_dir / "content_generated.json", content)
        except Exception as exc:
            self.logger.warning("Content engine skipped: %s", exc)
            result.errors.append(f"content_engine: {exc}")

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

        # ── Step 9: Competitor Analysis ───────────────────────────────────────
        self.logger.info("Step 9: Competitor analysis")
        try:
            competitors = self._run_competitor_analysis()
            result.competitor_insights = competitors
            self._write_json(output_dir / "competitor_insights.json", competitors)
        except Exception as exc:
            self.logger.warning("Competitor analysis skipped: %s", exc)

        # ── Step 10: Indexing ─────────────────────────────────────────────────
        self.logger.info("Step 10: Indexing recommendations")
        try:
            indexing = self._build_indexing_actions(diff, current_snapshot)
            result.indexing_actions = indexing
            self._write_json(output_dir / "indexing_actions.json", indexing)
        except Exception as exc:
            self.logger.warning("Indexing step skipped: %s", exc)

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
        from core.audit_engine import AuditEngine
        engine = AuditEngine(self.config, self.logger)
        audit_issues = engine.run(crawl_report)
        # cache on snapshot so _compute_seo_score can use it without re-running
        snapshot.audit_issues = audit_issues  # type: ignore[attr-defined]
        _SEVERITY_PRIORITY = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
        result: list[dict] = []
        for issue in audit_issues:
            requires_dev = issue.severity in ("Critical", "High")
            result.append({
                "category": issue.category,
                "page_url": issue.url,
                "title": issue.title,
                "description": issue.description,
                "fix_instructions": issue.fix_instructions,
                "impact_score": issue.impact_score,
                "severity": issue.severity,
                "requires_dev": requires_dev,
                "dev_note": f"REQUIRES DEV REVIEW — {issue.fix_instructions}" if requires_dev else "",
                "priority": _SEVERITY_PRIORITY.get(issue.severity, 4),
                "safe_mode": not requires_dev,
            })
        return result

    def _run_keyword_engine(self, diff: SiteDiff) -> list[dict]:
        from modules.pipeleap_seo_engine.data.serp_strategy import SERP_KEYWORD_CLUSTERS

        keywords: list[dict] = []

        # 10 high-intent
        high_intent_sources = [c for c in SERP_KEYWORD_CLUSTERS if c["intent"] in ("transactional", "commercial")]
        for cluster in high_intent_sources:
            for kw in cluster["keywords"][:3]:
                keywords.append({
                    "keyword": kw,
                    "type": "high_intent",
                    "cluster": cluster["cluster_name"],
                    "difficulty": cluster["estimated_difficulty"],
                    "conversion_probability": cluster["conversion_probability"],
                    "recommended_page_type": "landing_page" if cluster["intent"] == "transactional" else "blog_post",
                })
            if len([k for k in keywords if k["type"] == "high_intent"]) >= 10:
                break

        # 5 competitor gap keywords
        competitor_gaps = [
            {"keyword": "Apollo.io alternatives", "gap_source": "Apollo.io", "type": "competitor_gap"},
            {"keyword": "Clay alternatives for sales", "gap_source": "Clay", "type": "competitor_gap"},
            {"keyword": "Outreach.io alternatives", "gap_source": "Outreach", "type": "competitor_gap"},
            {"keyword": "Salesloft competitors", "gap_source": "Salesloft", "type": "competitor_gap"},
            {"keyword": "sales engagement platform alternatives", "gap_source": "multiple", "type": "competitor_gap"},
        ]
        keywords.extend(competitor_gaps[:5])

        # 5 long-tail
        long_tail = [
            {"keyword": "how to build outbound sales system for B2B SaaS", "type": "long_tail", "funnel_stage": "awareness"},
            {"keyword": "outbound sales automation for small sales teams", "type": "long_tail", "funnel_stage": "consideration"},
            {"keyword": "what is managed outbound sales service", "type": "long_tail", "funnel_stage": "awareness"},
            {"keyword": "how long does GTM implementation take", "type": "long_tail", "funnel_stage": "consideration"},
            {"keyword": "outbound pipeline predictability metrics", "type": "long_tail", "funnel_stage": "awareness"},
        ]
        keywords.extend(long_tail[:5])

        return keywords[:20]

    def _run_content_engine(self, diff: SiteDiff, run_id: str) -> list[dict]:
        from modules.pipeleap_seo_engine.data.serp_strategy import CONTENT_PLAN

        generated: list[dict] = []

        # 1 NEPQ-style blog post
        blog_brief = CONTENT_PLAN[0]
        generated.append({
            "type": "blog_post",
            "style": "NEPQ",
            "slug": blog_brief["slug"],
            "title": blog_brief["title"],
            "target_keyword": blog_brief["target_keyword"],
            "structure": [
                "H1: " + blog_brief["title"],
                "Problem frame: What most teams get wrong about " + blog_brief["target_keyword"],
                "Implication: What happens if this stays broken (pipeline, quota, headcount)",
                "Solution reveal: How the right system changes the outcome",
                "Evidence: Workflow architecture + outcome metrics",
                "CTA: Internal link to /gtm-audit or /contact",
            ],
            "internal_links": blog_brief.get("internal_links", []),
            "persona": blog_brief.get("persona", ""),
            "eeat_notes": blog_brief.get("eeat_notes", []),
            "status": "brief_ready",
        })

        # 3 glossary pages
        glossary_terms = [
            {
                "type": "glossary_page",
                "slug": "outbound-sales-automation",
                "title": "Outbound Sales Automation",
                "definition": (
                    "Outbound sales automation is the use of software and AI to execute prospecting, "
                    "lead enrichment, personalised outreach, and follow-up sequences without manual rep effort. "
                    "An automated outbound system runs continuously, learns from reply signals, and routes "
                    "qualified prospects into the CRM pipeline."
                ),
                "related_terms": ["ICP scoring", "sales orchestration", "GTM audit"],
                "internal_links": ["/", "/gtm-audit", "/glossary/icp-scoring"],
            },
            {
                "type": "glossary_page",
                "slug": "sales-orchestration",
                "title": "Sales Orchestration",
                "definition": (
                    "Sales orchestration is the coordination of every component in an outbound sales system — "
                    "lead sourcing, enrichment, personalisation, sequencing, reply handling, and CRM handoff — "
                    "into a single governed workflow. Unlike point tools that automate one slice, "
                    "an orchestrated system manages the entire motion as one continuous pipeline."
                ),
                "related_terms": ["outbound sales automation", "GTM implementation", "revenue operations"],
                "internal_links": ["/about", "/", "/glossary/outbound-sales-automation"],
            },
            {
                "type": "glossary_page",
                "slug": "gtm-audit",
                "title": "GTM Audit",
                "definition": (
                    "A GTM (go-to-market) audit is a structured review of a company's outbound sales motion, "
                    "covering ICP definition, lead targeting, messaging quality, outreach workflow, and pipeline health. "
                    "The output is a prioritised list of gaps and fixes that improve pipeline predictability."
                ),
                "related_terms": ["ICP scoring", "outbound sales automation", "GTM implementation"],
                "internal_links": ["/gtm-audit", "/glossary/icp-scoring", "/glossary/outbound-sales-automation"],
            },
        ]
        generated.extend(glossary_terms)

        return generated

    def _run_onpage_optimizer(self, snapshot: SiteSnapshot, diff: SiteDiff) -> list[dict]:
        from modules.pipeleap_seo_engine.data.serp_strategy import META_TARGETS

        optimised: list[dict] = []
        page_index = snapshot.page_index()

        priority_paths = ["/gtm-audit", "/", "/pricing"]
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

        suggestions: list[dict] = []
        for cluster_def in LINKING_CLUSTERS:
            for spoke in cluster_def["spoke_articles"]:
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
                suggestions.append({
                    "from_page": cluster_def["pillar_page"],
                    "to_page": glossary,
                    "anchor_text": glossary.split("/")[-1].replace("-", " "),
                    "placement": "Inline where the term is first mentioned",
                    "cluster": cluster_def["cluster"],
                    "priority": "medium",
                })
        return suggestions

    def _run_competitor_analysis(self) -> list[dict]:
        from modules.pipeleap_seo_engine.data.competitors import COMPETITORS

        insights: list[dict] = []
        top_2 = list(COMPETITORS.items())[:2]

        for name, profile in top_2:
            insights.append({
                "competitor": name,
                "category": profile.get("category", ""),
                "their_strength": profile.get("description", ""),
                "pipeleap_wins": profile.get("pipeleap_wins", []),
                "limitations": profile.get("limitations", []),
                "keyword_gaps_to_target": [
                    f"{name} alternatives",
                    f"{name} vs Pipeleap",
                    f"better than {name}",
                    f"{name} competitors 2025",
                ],
                "content_to_outrank": f"Publish '{name} vs Pipeleap' comparison page targeting transactional intent. Lead with concrete outcome differentials.",
                "best_for": profile.get("best_for", ""),
            })

        return insights

    def _build_indexing_actions(self, diff: SiteDiff, snapshot: SiteSnapshot) -> list[dict]:
        actions: list[dict] = []

        for change in diff.new_pages:
            actions.append({
                "action": "submit_url",
                "url": change.url,
                "reason": "New page — submit via GSC URL Inspection",
                "priority": 1,
            })

        for url in diff.missing_from_sitemap[:5]:
            actions.append({
                "action": "add_to_sitemap",
                "url": url,
                "reason": "Indexable page absent from sitemap.xml",
                "priority": 2,
            })

        for change in diff.updated_pages:
            if any(f in change.fields_changed for f in ["title", "meta_description", "h1"]):
                actions.append({
                    "action": "refresh_index",
                    "url": change.url,
                    "reason": "Key SEO fields updated — request re-crawl in GSC",
                    "priority": 2,
                })

        actions.append({
            "action": "resubmit_sitemap",
            "url": self.site_url + "/sitemap.xml",
            "reason": "Weekly sitemap resubmission to GSC keeps index fresh",
            "priority": 3,
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

        if result.competitor_insights:
            plan.append(f"Begin comparison page for {result.competitor_insights[0]['competitor']} — targets transactional 'alternatives' cluster")

        plan.append("Monitor GSC for CTR changes on any updated meta descriptions (48-hour window)")

        if result.seo_score.overall < 60:
            plan.append("SEO score below 60 — prioritise technical fixes before content expansion")

        return plan[:7]

    def _build_daily_briefing(self, result: SEOOSResult, diff: SiteDiff, plan: ExecutionPlan) -> str:
        score = result.seo_score
        score_bar = "█" * (score.overall // 10) + "░" * (10 - score.overall // 10)

        lines = [
            f"# Pipeleap SEO OS — Daily Briefing",
            f"**Run ID:** {result.run_id}  |  **Mode:** {result.mode.upper()}  |  **Generated:** {result.generated_at}",
            "",
            f"## SEO Score: {score.overall}/100  [{score_bar}]",
            f"| Dimension | Score |",
            f"|---|---|",
            f"| Technical | {score.technical}/100 |",
            f"| Content | {score.content}/100 |",
            f"| Indexing | {score.indexing}/100 |",
            f"| Authority | {score.authority}/100 |",
            "",
            "---",
            "",
            "## 1. Website Changes Detected",
        ]

        changes = result.website_changes
        if changes.get("has_changes"):
            lines += [
                f"- New pages: **{changes.get('new_pages', 0)}**",
                f"- Updated pages: **{changes.get('updated_pages', 0)}**",
                f"- Deleted pages: **{changes.get('deleted_pages', 0)}**",
                f"- Broken links: **{changes.get('broken_links', 0)}**",
                f"- Orphan pages: **{changes.get('orphan_pages', 0)}**",
            ]
        else:
            lines.append("No structural changes detected — growth mode active.")

        lines += ["", "---", "", "## 2. Safe SEO Actions (No Code Impact)"]
        for action in result.safe_actions[:8]:
            lines.append(f"- [{action.get('category','').upper()}] **{action.get('title','')}** — `{action.get('page_url','')}`")

        if result.dev_review_items:
            lines += ["", "---", "", "## 3. REQUIRES DEV REVIEW"]
            for item in result.dev_review_items:
                lines.append(f"- **{item.get('title','')}** — `{item.get('page_url','')}` — {item.get('dev_note','')}")

        lines += ["", "---", "", "## 4. Keyword Opportunities (Top 10)"]
        for kw in result.keyword_opportunities[:10]:
            t = kw.get("type", "")
            lines.append(f"- [{t}] **{kw.get('keyword','')}** — cluster: {kw.get('cluster', kw.get('gap_source',''))}")

        lines += ["", "---", "", "## 5. Content Generated"]
        for item in result.content_generated:
            lines.append(f"- [{item.get('type','')}] **{item.get('title', item.get('slug',''))}**")

        lines += ["", "---", "", "## 6. Pages Optimized"]
        for page in result.pages_optimized:
            lines.append(f"- `{page.get('page_url','')}` — {' | '.join(page.get('optimisation_actions', []))}")

        lines += ["", "---", "", "## 7. Internal Linking (Top 5)"]
        for link in result.linking_suggestions[:5]:
            lines.append(f"- `{link.get('from_page','')}` → `{link.get('to_page','')}` via \"{link.get('anchor_text','')}\"")

        lines += ["", "---", "", "## 8. Competitor Insights"]
        for comp in result.competitor_insights:
            lines += [
                f"**{comp['competitor']}**",
                f"- Keywords to target: {', '.join(comp.get('keyword_gaps_to_target', [])[:2])}",
                f"- Content to publish: {comp.get('content_to_outrank','')}",
                "",
            ]

        lines += ["", "---", "", "## 9. Indexing Actions"]
        for action in result.indexing_actions[:6]:
            lines.append(f"- [{action.get('action','')}] `{action.get('url','')}` — {action.get('reason','')}")

        if result.risks_and_missed:
            lines += ["", "---", "", "## 10. Risks / Missed Opportunities"]
            for risk in result.risks_and_missed:
                sev = risk.get("severity","").upper()
                lines.append(f"- [{sev}] **{risk.get('type','')}** — {risk.get('description','')}")

        lines += ["", "---", "", "## 11. Tomorrow's Plan"]
        for i, item in enumerate(result.next_day_plan, 1):
            lines.append(f"{i}. {item}")

        lines += ["", "---", f"*SEO OS v{SEOOSAgent.VERSION} — Safe Mode — {result.run_id}*"]
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
            "mode": result.mode,
            "actions_generated": len(result.safe_actions),
            "dev_items": len(result.dev_review_items),
            "content_pieces": len(result.content_generated),
            "errors": len(result.errors),
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
