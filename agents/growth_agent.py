from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from utils.models import (
    AuditIssue,
    BacklinkOpportunity,
    ContentAsset,
    ExecutionAction,
    KeywordCluster,
    LinkSuggestion,
    RoadmapStep,
)
from utils.scoring import (
    label_effort,
    label_ranking_difficulty,
    label_revenue_impact,
    label_speed_to_rank,
)


class GrowthAgent:
    """Turns SEO findings into a Pipeleap-specific growth plan."""

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger

    def build_plan(
        self,
        keyword_clusters: list[KeywordCluster],
        audit_issues: list[AuditIssue],
        link_suggestions: list[LinkSuggestion],
        backlink_opportunities: list[BacklinkOpportunity],
        assets: list[ContentAsset],
    ) -> tuple[list[ExecutionAction], list[RoadmapStep], list[dict[str, Any]]]:
        actions: list[ExecutionAction] = []

        for cluster in keyword_clusters[:5]:
            top_opportunity = cluster.opportunities[0]
            actions.append(
                ExecutionAction(
                    title=f"Publish {cluster.primary_keyword}",
                    description=(
                        f"Create or ship a {cluster.recommended_asset_type.replace('_', ' ')} for {cluster.primary_keyword} "
                        f"to capture {cluster.cluster_name} demand and route it into demo intent."
                    ),
                    revenue_impact=label_revenue_impact(top_opportunity.revenue_priority_score),
                    ranking_difficulty=label_ranking_difficulty(top_opportunity.estimated_difficulty),
                    speed_to_rank=label_speed_to_rank(top_opportunity.speed_to_rank_score),
                    effort=label_effort(0.45 if cluster.recommended_asset_type == "landing_page" else 0.35),
                    owner="SEO content",
                    related_keywords=[item.keyword for item in cluster.opportunities[:5]],
                    due_window="Next 7 days",
                    rationale=cluster.strategic_rationale,
                )
            )

        for issue in audit_issues[:5]:
            effort_hint = 0.25 if issue.category in {"metadata", "heading"} else 0.6
            actions.append(
                ExecutionAction(
                    title=f"Fix: {issue.title or issue.category}",
                    description=issue.fix_instructions,
                    revenue_impact="High" if issue.severity == "Critical" else "Medium",
                    ranking_difficulty="Low",
                    speed_to_rank="Fast",
                    effort=label_effort(effort_hint),
                    owner="Engineering",
                    supporting_urls=[issue.url],
                    due_window="Next 14 days",
                    rationale=issue.description,
                )
            )

        if link_suggestions:
            actions.append(
                ExecutionAction(
                    title="Apply conversion-first internal links",
                    description="Route blogs and use-case pages into high-intent landing pages and conversion destinations.",
                    revenue_impact="High",
                    ranking_difficulty="Low",
                    speed_to_rank="Fast",
                    effort="Easy",
                    owner="SEO",
                    supporting_urls=[item.target_url for item in link_suggestions[:5]],
                    due_window="This week",
                    rationale="Internal links help authority flow and push more organic visitors toward demo or signup paths.",
                )
            )

        if backlink_opportunities:
            actions.append(
                ExecutionAction(
                    title="Launch backlink outreach sprint",
                    description="Pitch workflow-led content and directory profiles aligned to Pipeleap's highest-intent topics.",
                    revenue_impact="Medium",
                    ranking_difficulty="Medium",
                    speed_to_rank="Moderate",
                    effort="Medium",
                    owner="Growth",
                    supporting_urls=[item.prospect_url for item in backlink_opportunities[:5]],
                    due_window="Weeks 2-4",
                    rationale="Authority growth compounds landing page and comparison page rankings.",
                )
            )

        prioritized_actions = sorted(
            actions,
            key=lambda action: (
                {"High": 3, "Medium": 2, "Low": 1}.get(action.revenue_impact, 0),
                {"Fast": 3, "Moderate": 2, "Slow": 1}.get(action.speed_to_rank, 0),
                {"Easy": 3, "Medium": 2, "Hard": 1}.get(action.effort, 0),
            ),
            reverse=True,
        )

        return prioritized_actions[:12], self._roadmap(keyword_clusters, audit_issues, backlink_opportunities), self._content_calendar(assets)

    def _roadmap(
        self,
        keyword_clusters: list[KeywordCluster],
        audit_issues: list[AuditIssue],
        backlink_opportunities: list[BacklinkOpportunity],
    ) -> list[RoadmapStep]:
        top_cluster = keyword_clusters[0] if keyword_clusters else None
        top_audit = audit_issues[0].title if audit_issues else "technical cleanup"
        backlink_count = min(5, len(backlink_opportunities))

        return [
            RoadmapStep(
                timebox="Week 1",
                objective="Fix crawl, indexing, and metadata blockers",
                outputs=[top_audit, "robots/sitemap validation", "CTR-focused metadata refresh"],
                success_metric="All critical technical issues resolved on priority pages",
            ),
            RoadmapStep(
                timebox="Week 2",
                objective="Ship high-intent landing pages",
                outputs=[
                    f"Publish landing pages for {top_cluster.primary_keyword}" if top_cluster else "Publish top landing page",
                    "Add conversion CTAs and schema markup",
                    "Link new pages from product and blog surfaces",
                ],
                success_metric="Priority landing pages indexed and linked internally",
            ),
            RoadmapStep(
                timebox="Week 3",
                objective="Expand supporting cluster content",
                outputs=["Publish blogs and use-case pages", "Build pillar-to-cluster linking", "Refresh comparison pages"],
                success_metric="Every pillar page has at least two supporting assets",
            ),
            RoadmapStep(
                timebox="Week 4",
                objective="Improve authority and learning loops",
                outputs=[f"Send {backlink_count} outreach pitches", "Review CTR gaps", "Update next month's content roadmap"],
                success_metric="Ranking movement logged and next content sprint prioritized by conversion intent",
            ),
        ]

    def _content_calendar(self, assets: list[ContentAsset]) -> list[dict[str, Any]]:
        start = date.today()
        calendar = []
        for index, asset in enumerate(assets[:8]):
            publish_date = start + timedelta(days=index * 3)
            calendar.append(
                {
                    "publish_date": publish_date.isoformat(),
                    "asset_type": asset.page_type,
                    "title": asset.title,
                    "primary_keyword": asset.source_keywords[0] if asset.source_keywords else "",
                    "goal": "Drive demo requests and signups",
                }
            )
        return calendar
