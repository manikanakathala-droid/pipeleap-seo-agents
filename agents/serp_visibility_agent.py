from __future__ import annotations

"""
SERP Visibility Agent — Orchestrates all 7 pillars of the off-page/content
search visibility strategy for Pipeleap.com.

This agent is intentionally non-destructive: it NEVER modifies the website
codebase. All outputs are content briefs, action queues, and reports that
a human (or downstream automation) acts on.

Pillars covered:
  1. SERP snippet optimisation (titles, meta, CTR variants)
  2. Breadcrumb visibility (content hierarchy signals)
  3. Search demand capture (keyword clusters, content plan)
  4. SERP presence expansion (directories, guest posts, communities)
  5. GSC analysis (CTR rules, page-2 opportunities, indexing actions)
  6. Internal linking (cluster map, spoke-to-pillar recommendations)
  7. Authority building (tiered backlink strategy, brand monitoring)

Outputs:
  - outputs/{run_id}/serp_visibility_report.json
  - outputs/{run_id}/serp_snippet_recommendations.json
  - outputs/{run_id}/offpage_action_queue.json
  - outputs/{run_id}/linkedin_content_briefs.json
  - outputs/{run_id}/content_plan_briefs.json
  - outputs/{run_id}/weekly_serp_report.md
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.serp_snippet_engine import SerpSnippetEngine, SnippetReport
from core.offpage_engine import OffPageEngine, OffPageReport
from modules.pipeleap_seo_engine.data.serp_strategy import (
    CONTENT_PLAN,
    LINKING_CLUSTERS,
    SERP_KEYWORD_CLUSTERS,
)
from utils.config_loader import load_config
from utils.storage import SEOStorage


@dataclass
class SerpVisibilityResult:
    run_id: str
    generated_at: str
    snippet_report: dict = field(default_factory=dict)
    offpage_report: dict = field(default_factory=dict)
    content_briefs_generated: int = 0
    keyword_clusters_loaded: int = 0
    linking_clusters_loaded: int = 0
    output_files: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "generated_at": self.generated_at,
            "content_briefs_generated": self.content_briefs_generated,
            "keyword_clusters_loaded": self.keyword_clusters_loaded,
            "linking_clusters_loaded": self.linking_clusters_loaded,
            "output_files": self.output_files,
            "errors": self.errors,
        }


class SerpVisibilityAgent:
    """
    Runs the full SERP visibility strategy as an automated pipeline.

    Usage:
        agent = SerpVisibilityAgent(config)
        result = agent.run_once()
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.logger = logging.getLogger("serp_visibility_agent")
        self.site_url = config.get("site", {}).get("site_url", "https://pipeleap.com")
        self.output_root = Path(config.get("execution", {}).get("output_dir", "outputs"))
        self.snippet_engine = SerpSnippetEngine(config, self.logger)
        self.offpage_engine = OffPageEngine(config, self.logger)

        db_path = config.get("execution", {}).get("memory_db", "outputs/pipeleap_seo_memory.db")
        self.storage: SEOStorage | None = None
        try:
            self.storage = SEOStorage(db_path, self.logger)
        except Exception as exc:
            self.logger.warning("Storage init failed, running without persistence: %s", exc)

    def run_once(self) -> dict:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_dir = self.output_root / run_id
        output_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info("SerpVisibilityAgent run_id=%s started", run_id)
        result = SerpVisibilityResult(
            run_id=run_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        # Fetch GSC page-level data if available
        gsc_page_data = self._fetch_gsc_data()

        # Pillar 1, 2, 5 — snippet optimisation, breadcrumbs, GSC rules
        try:
            snippet_report: SnippetReport = self.snippet_engine.run(
                gsc_page_data=gsc_page_data,
                run_id=run_id,
            )
            result.snippet_report = snippet_report.to_dict()
            self._write_json(output_dir / "serp_snippet_recommendations.json", result.snippet_report)
            result.output_files.append(str(output_dir / "serp_snippet_recommendations.json"))
        except Exception as exc:
            self.logger.error("SnippetEngine failed: %s", exc)
            result.errors.append(f"snippet_engine: {exc}")

        # Pillars 3, 4, 7 — off-page expansion, authority, LinkedIn
        try:
            now = datetime.now(timezone.utc)
            week_number = now.isocalendar()[1]
            actioned_dirs = self._load_actioned_directories()
            actioned_pubs = self._load_actioned_publications()

            offpage_report: OffPageReport = self.offpage_engine.run(
                run_id=run_id,
                week_number=week_number,
                actioned_directories=actioned_dirs,
                actioned_publications=actioned_pubs,
            )
            result.offpage_report = offpage_report.to_dict()

            self._write_json(output_dir / "offpage_action_queue.json", {
                "directory_queue": [vars(d) for d in offpage_report.directory_queue],
                "guest_post_pitches": [vars(g) for g in offpage_report.guest_post_pitches],
                "authority_actions": [vars(a) for a in offpage_report.authority_actions],
                "brand_monitoring_setup": offpage_report.brand_monitoring_setup,
            })
            self._write_json(output_dir / "linkedin_content_briefs.json", [
                vars(lb) for lb in offpage_report.linkedin_briefs
            ])
            result.output_files.extend([
                str(output_dir / "offpage_action_queue.json"),
                str(output_dir / "linkedin_content_briefs.json"),
            ])
        except Exception as exc:
            self.logger.error("OffPageEngine failed: %s", exc)
            result.errors.append(f"offpage_engine: {exc}")

        # Pillar 3 — content plan briefs
        try:
            self._write_json(output_dir / "content_plan_briefs.json", CONTENT_PLAN)
            result.content_briefs_generated = len(CONTENT_PLAN)
            result.output_files.append(str(output_dir / "content_plan_briefs.json"))
        except Exception as exc:
            self.logger.error("Content plan write failed: %s", exc)
            result.errors.append(f"content_plan: {exc}")

        # Pillar 6 — internal linking cluster map
        try:
            self._write_json(output_dir / "internal_linking_clusters.json", LINKING_CLUSTERS)
            result.linking_clusters_loaded = len(LINKING_CLUSTERS)
            result.output_files.append(str(output_dir / "internal_linking_clusters.json"))
        except Exception as exc:
            self.logger.error("Linking cluster write failed: %s", exc)
            result.errors.append(f"linking_clusters: {exc}")

        result.keyword_clusters_loaded = len(SERP_KEYWORD_CLUSTERS)

        # Master report
        master_report = result.to_dict()
        self._write_json(output_dir / "serp_visibility_report.json", master_report)
        result.output_files.append(str(output_dir / "serp_visibility_report.json"))

        # Human-readable weekly summary
        try:
            md = self._build_weekly_markdown(result, snippet_report, offpage_report)
            (output_dir / "weekly_serp_report.md").write_text(md, encoding="utf-8")
            result.output_files.append(str(output_dir / "weekly_serp_report.md"))
        except Exception as exc:
            self.logger.warning("Markdown report failed: %s", exc)

        self.logger.info(
            "SerpVisibilityAgent complete: %d output files, %d errors",
            len(result.output_files), len(result.errors),
        )
        return master_report

    def _fetch_gsc_data(self) -> list[dict]:
        try:
            from connectors.gsc_connector import GoogleSearchConsoleConnector
            from datetime import date, timedelta
            gsc = GoogleSearchConsoleConnector(self.config, self.logger)
            end = date.today().isoformat()
            start = (date.today() - timedelta(days=28)).isoformat()
            return gsc.fetch_page_performance(start_date=start, end_date=end) or []
        except Exception as exc:
            self.logger.warning("GSC fetch skipped: %s", exc)
            return []

    def _load_actioned_directories(self) -> set[str]:
        if not self.storage:
            return set()
        try:
            return self.storage.fetch_actioned_directory_urls()
        except Exception:
            return set()

    def _load_actioned_publications(self) -> set[str]:
        if not self.storage:
            return set()
        try:
            return self.storage.fetch_actioned_publication_urls()
        except Exception:
            return set()

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def _build_weekly_markdown(
        self,
        result: SerpVisibilityResult,
        snippet_report: SnippetReport,
        offpage_report: OffPageReport,
    ) -> str:
        lines = [
            f"# Pipeleap SERP Visibility Report",
            f"**Run ID:** {result.run_id}",
            f"**Generated:** {result.generated_at}",
            "",
            "---",
            "",
            "## Snippet Optimisation (Pillar 1 + 2 + 5)",
            "",
        ]

        high_recs = [r for r in snippet_report.snippet_recommendations if r.priority == "high"]
        if high_recs:
            lines.append(f"### High-Priority Meta Updates ({len(high_recs)} pages)")
            for rec in high_recs:
                lines += [
                    f"**Page:** `{rec.page_path}`",
                    f"- Impressions: {rec.impressions:,} | CTR: {rec.current_ctr:.1%} | Position: {rec.average_position:.1f}",
                    f"- **Recommended title:** {rec.recommended_title}",
                    f"- **Recommended meta:** {rec.recommended_meta}",
                    f"- Reason: {rec.reason}",
                    "",
                ]

        if snippet_report.page_two_opportunities:
            lines += [
                "### Page 2 Opportunities",
                *[
                    f"- `{o['page']}` — position {o['position']:.1f}, {o['impressions']} impressions"
                    for o in snippet_report.page_two_opportunities[:5]
                ],
                "",
            ]

        lines += [
            "---",
            "",
            "## Off-Page Action Queue (Pillars 3 + 4 + 7)",
            "",
            f"### Directory Submissions — {len([d for d in offpage_report.directory_queue if d.status == 'pending'])} pending",
        ]
        for d in offpage_report.directory_queue[:5]:
            if d.status == "pending":
                lines.append(f"- **{d.name}** (DA {d.da}) — Priority {d.priority} — {d.category}")
        lines.append("")

        lines += [
            f"### Guest Post Pitches — {len(offpage_report.guest_post_pitches)} ready",
        ]
        for p in offpage_report.guest_post_pitches[:3]:
            lines.append(f"- **{p.publication}** (DA {p.da}) — {p.pitch_angle}")
        lines.append("")

        lines += [
            "### LinkedIn Content This Week",
        ]
        for lb in offpage_report.linkedin_briefs:
            lines += [
                f"**{lb.day} ({lb.format}):** {lb.hook}",
                f"CTA: {lb.cta}",
                "",
            ]

        lines += [
            "---",
            "",
            "## Content Plan (Pillar 3)",
            f"{result.content_briefs_generated} blog post briefs queued. See `content_plan_briefs.json` for full details.",
            "",
            "| Priority | Slug | Target Keyword |",
            "|---|---|---|",
        ]
        for brief in CONTENT_PLAN[:5]:
            lines.append(f"| 1 | `{brief['slug']}` | {brief['target_keyword']} |")

        lines += [
            "",
            "---",
            "",
            "## Internal Linking Clusters (Pillar 6)",
        ]
        for cluster in LINKING_CLUSTERS:
            lines += [
                f"**{cluster['cluster']}** — Pillar: `{cluster['pillar_page']}`",
                "Spokes: " + ", ".join(f"`{s}`" for s in cluster["spoke_articles"]),
                "",
            ]

        lines += [
            "---",
            "",
            "## Authority Building (Pillar 7)",
        ]
        for action in offpage_report.authority_actions[:6]:
            lines.append(f"- [Tier {action.tier}] **{action.tactic}**")

        lines += [
            "",
            "---",
            "",
            f"_Generated by SerpVisibilityAgent — run {result.run_id}_",
        ]

        return "\n".join(lines)
