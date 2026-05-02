from __future__ import annotations

from typing import Any

from core.content_engine import ContentEngine
from utils.models import ContentAsset, KeywordCluster

_QUALITY_FLOOR = 0.0   # assets at exactly 0.0 failed the quality gate — suppress them


class ContentAgent:
    """
    Chooses which non-landing assets to create on each run.

    Quality gate: assets that failed BlogContentEngine's internal quality
    check (uniqueness_score == 0.0) are filtered out before returning.
    Per-asset quality signals are logged for observability.
    """

    def __init__(self, config: dict[str, Any], content_engine: ContentEngine, logger) -> None:
        self.config = config
        self.content_engine = content_engine
        self.logger = logger
        self.execution = config.get("execution", {})

    def generate(self, clusters: list[KeywordCluster]) -> list[ContentAsset]:
        blog_limit = self.execution.get("blog_posts_per_run", 4)
        comparison_limit = self.execution.get("comparison_pages_per_run", 2)
        use_case_limit = self.execution.get("use_case_pages_per_run", 2)

        blog_clusters = [c for c in clusters if c.recommended_asset_type == "blog_post"][:blog_limit]
        comparison_clusters = [c for c in clusters if c.recommended_asset_type == "comparison_page"][:comparison_limit]
        use_case_clusters = [c for c in clusters if c.recommended_asset_type == "use_case_page"][:use_case_limit]

        raw: list[ContentAsset] = []
        for cluster in blog_clusters:
            try:
                raw.append(self.content_engine.generate_blog_post(cluster))
            except Exception as exc:
                self.logger.error("Blog generation failed for '%s': %s", cluster.primary_keyword, exc)

        for cluster in comparison_clusters:
            try:
                raw.append(self.content_engine.generate_comparison_page(cluster))
            except Exception as exc:
                self.logger.error("Comparison generation failed for '%s': %s", cluster.primary_keyword, exc)

        for cluster in use_case_clusters:
            try:
                raw.append(self.content_engine.generate_use_case_page(cluster))
            except Exception as exc:
                self.logger.error("Use-case generation failed for '%s': %s", cluster.primary_keyword, exc)

        # Log quality signals and filter out quality-gate failures
        passed: list[ContentAsset] = []
        for asset in raw:
            word_count = len(asset.body_markdown.split()) if asset.body_markdown else 0
            self.logger.info(
                "Asset quality | slug=%-45s type=%-16s score=%.2f words=%d",
                asset.slug, asset.page_type, asset.uniqueness_score, word_count,
            )
            if asset.uniqueness_score <= _QUALITY_FLOOR:
                self.logger.warning(
                    "Quality gate suppressed asset: %s (score=%.2f)", asset.slug, asset.uniqueness_score
                )
            else:
                passed.append(asset)

        self.logger.info(
            "ContentAgent: %d/%d assets passed quality gate",
            len(passed), len(raw),
        )
        return passed
