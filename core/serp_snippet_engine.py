from __future__ import annotations

"""
SERP Snippet Engine — Pillar 1, 2, 5 of the SERP visibility strategy.

Responsibilities:
  - Detect pages with high impressions / low CTR and generate optimised meta copy
  - Flag pages eligible for FAQ rich results and produce schema-ready FAQ blocks
  - Recommend breadcrumb structures for content pages
  - Apply GSC CTR rules from serp_strategy data
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from modules.pipeleap_seo_engine.data.serp_strategy import (
    CTR_VARIANTS,
    FAQ_RICH_RESULT_TOPICS,
    GSC_CTR_RULES,
    META_TARGETS,
    LINKING_CLUSTERS,
)


@dataclass
class SnippetRecommendation:
    page_path: str
    current_title: str
    current_meta: str
    recommended_title: str
    recommended_meta: str
    reason: str
    priority: str  # "high" | "medium" | "low"
    ctr_variant: str = ""
    impressions: int = 0
    current_ctr: float = 0.0
    average_position: float = 0.0


@dataclass
class FaqRichResultBrief:
    page_path: str
    questions: list[str] = field(default_factory=list)
    schema_ready: bool = False
    action: str = ""


@dataclass
class BreadcrumbRecommendation:
    page_path: str
    breadcrumb_chain: list[str] = field(default_factory=list)
    cluster: str = ""


@dataclass
class SnippetReport:
    run_id: str
    generated_at: str
    snippet_recommendations: list[SnippetRecommendation] = field(default_factory=list)
    faq_briefs: list[FaqRichResultBrief] = field(default_factory=list)
    breadcrumb_recommendations: list[BreadcrumbRecommendation] = field(default_factory=list)
    ctr_improvement_actions: list[dict] = field(default_factory=list)
    page_two_opportunities: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "generated_at": self.generated_at,
            "snippet_recommendations": [vars(r) for r in self.snippet_recommendations],
            "faq_briefs": [vars(f) for f in self.faq_briefs],
            "breadcrumb_recommendations": [vars(b) for b in self.breadcrumb_recommendations],
            "ctr_improvement_actions": self.ctr_improvement_actions,
            "page_two_opportunities": self.page_two_opportunities,
        }


class SerpSnippetEngine:
    """
    Analyses GSC page/query data and crawl snapshots to produce:
      - Optimised title + meta recommendations for every tracked page
      - FAQ rich result briefs for pages with informational content
      - Breadcrumb chain recommendations per content cluster
      - CTR improvement action queue from GSC rules
    """

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger
        self.site_url = config.get("site", {}).get("site_url", "https://pipeleap.com").rstrip("/")

    def run(
        self,
        gsc_page_data: list[dict],
        run_id: str,
    ) -> SnippetReport:
        generated_at = datetime.now(timezone.utc).isoformat()
        report = SnippetReport(run_id=run_id, generated_at=generated_at)

        report.snippet_recommendations = self._build_snippet_recommendations(gsc_page_data)
        report.faq_briefs = self._build_faq_briefs(gsc_page_data)
        report.breadcrumb_recommendations = self._build_breadcrumb_recommendations()
        report.ctr_improvement_actions = self._apply_ctr_rules(gsc_page_data)
        report.page_two_opportunities = self._find_page_two_opportunities(gsc_page_data)

        self.logger.info(
            "SnippetEngine: %d meta recs | %d FAQ briefs | %d CTR actions | %d page-2 opps",
            len(report.snippet_recommendations),
            len(report.faq_briefs),
            len(report.ctr_improvement_actions),
            len(report.page_two_opportunities),
        )
        return report

    def _build_snippet_recommendations(
        self, gsc_page_data: list[dict]
    ) -> list[SnippetRecommendation]:
        recs: list[SnippetRecommendation] = []
        gsc_index: dict[str, dict] = {}
        for row in gsc_page_data:
            path = row.get("page", "").replace(self.site_url, "").rstrip("/") or "/"
            gsc_index[path] = row

        for target in META_TARGETS:
            path = target["path"]
            gsc_row = gsc_index.get(path, {})
            impressions = int(gsc_row.get("impressions", 0))
            ctr = float(gsc_row.get("ctr", 0.0))
            position = float(gsc_row.get("position", 0.0))

            current_title = gsc_row.get("title", "")
            current_meta = gsc_row.get("meta_description", "")

            if impressions > 100 and ctr < 0.03:
                priority = "high"
                reason = f"High impressions ({impressions}) but low CTR ({ctr:.1%}) — meta copy not matching searcher intent"
            elif position > 10 and impressions > 50:
                priority = "medium"
                reason = f"Page ranking position {position:.1f} — better snippet can lift to page one"
            else:
                priority = "low"
                reason = "Proactive optimisation — align copy with primary keyword cluster"

            variant = CTR_VARIANTS[hash(path) % len(CTR_VARIANTS)]["headline"]

            recs.append(SnippetRecommendation(
                page_path=path,
                current_title=current_title,
                current_meta=current_meta,
                recommended_title=target["title"],
                recommended_meta=target["meta_description"],
                reason=reason,
                priority=priority,
                ctr_variant=variant,
                impressions=impressions,
                current_ctr=ctr,
                average_position=position,
            ))

        return sorted(recs, key=lambda r: {"high": 0, "medium": 1, "low": 2}[r.priority])

    def _build_faq_briefs(self, gsc_page_data: list[dict]) -> list[FaqRichResultBrief]:
        briefs: list[FaqRichResultBrief] = []
        faq_pages = ["/faq", "/sales-ops-audit", "/"]

        for path in faq_pages:
            questions = [q for q in FAQ_RICH_RESULT_TOPICS if self._question_fits_page(q, path)]
            briefs.append(FaqRichResultBrief(
                page_path=path,
                questions=questions[:5],
                schema_ready=True,
                action=(
                    "Add FAQPage JSON-LD schema. Each answer must be a standalone paragraph. "
                    "No CTA-only text. No navigation links as answers."
                ),
            ))

        return briefs

    @staticmethod
    def _question_fits_page(question: str, path: str) -> bool:
        q = question.lower()
        if path == "/faq":
            return True
        if path == "/sales-ops-audit":
            return any(kw in q for kw in ["sales ops", "audit", "implementation", "partner"])
        if path == "/":
            return any(kw in q for kw in ["outbound", "automation", "pipeline", "automated"])
        return False

    def _build_breadcrumb_recommendations(self) -> list[BreadcrumbRecommendation]:
        recs: list[BreadcrumbRecommendation] = []
        for cluster_def in LINKING_CLUSTERS:
            pillar = cluster_def["pillar_page"]
            cluster_name = cluster_def["cluster"]
            for spoke in cluster_def["spoke_articles"]:
                slug = spoke.split("/")[-1].replace("-", " ").title()
                recs.append(BreadcrumbRecommendation(
                    page_path=spoke,
                    breadcrumb_chain=["Home", "Blog", cluster_name, slug],
                    cluster=cluster_name,
                ))
            for glossary in cluster_def.get("glossary_links", []):
                term = glossary.split("/")[-1].replace("-", " ").title()
                recs.append(BreadcrumbRecommendation(
                    page_path=glossary,
                    breadcrumb_chain=["Home", "Glossary", term],
                    cluster=cluster_name,
                ))

        return recs

    def _apply_ctr_rules(self, gsc_page_data: list[dict]) -> list[dict]:
        actions: list[dict] = []
        for row in gsc_page_data:
            impressions = int(row.get("impressions", 0))
            ctr = float(row.get("ctr", 0.0))
            page = row.get("page", "")

            for rule in GSC_CTR_RULES:
                if rule["rule"] == "high_impression_low_ctr":
                    if impressions > 100 and ctr < 0.03:
                        actions.append({
                            "rule": rule["rule"],
                            "page": page,
                            "impressions": impressions,
                            "ctr": ctr,
                            "action": rule["action"],
                        })
        return actions

    def _find_page_two_opportunities(self, gsc_page_data: list[dict]) -> list[dict]:
        opps: list[dict] = []
        for row in gsc_page_data:
            position = float(row.get("position", 0.0))
            impressions = int(row.get("impressions", 0))
            if 11 <= position <= 20 and impressions > 30:
                opps.append({
                    "page": row.get("page", ""),
                    "position": position,
                    "impressions": impressions,
                    "top_query": row.get("query", ""),
                    "action": GSC_CTR_RULES[1]["action"],
                })
        return sorted(opps, key=lambda x: x["impressions"], reverse=True)
