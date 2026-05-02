from __future__ import annotations

from typing import Any

from utils.models import ContentAsset, KeywordCluster, LinkSuggestion, PageSnapshot
from utils.text import title_case_keyword


class LinkingEngine:
    """Builds a conversion-focused internal link graph for topical authority."""

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger
        self.site_url = config.get("site", {}).get("site_url", "").rstrip("/")
        self.conversion_pages = config.get("seo", {}).get("conversion_pages", [])

    def suggest(
        self,
        existing_pages: list[PageSnapshot],
        generated_assets: list[ContentAsset],
        clusters: list[KeywordCluster],
    ) -> list[LinkSuggestion]:
        suggestions: list[LinkSuggestion] = []
        landing_targets = [
            asset for asset in generated_assets if asset.page_type == "landing_page"
        ]
        conversion_targets = [
            page.get("url")
            for page in self.conversion_pages
            if isinstance(page, dict) and page.get("url")
        ]

        for asset in generated_assets:
            source_url = f"{self.site_url}/{asset.slug}".rstrip("/")
            cluster = self._find_cluster_for_asset(asset, clusters)
            primary_anchor = title_case_keyword(cluster.primary_keyword) if cluster else asset.title

            if asset.page_type == "blog_post" and landing_targets:
                target = self._best_landing_target(asset, landing_targets)
                suggestions.append(
                    LinkSuggestion(
                        source_url=source_url,
                        target_url=f"{self.site_url}/{target.slug}".rstrip("/"),
                        anchor_text=title_case_keyword(target.source_keywords[0]),
                        reason="Every blog should route to a high-intent landing page in the same topic cluster.",
                        confidence=0.91,
                        placement_hint="Add within the first supporting section and again near the CTA.",
                    )
                )

            if conversion_targets:
                suggestions.append(
                    LinkSuggestion(
                        source_url=source_url,
                        target_url=conversion_targets[0],
                        anchor_text=primary_anchor,
                        reason="Each content asset should point into a conversion path for demo or signup intent.",
                        confidence=0.88,
                        placement_hint="Place in the final CTA section.",
                    )
                )

        for page in existing_pages:
            if len(page.internal_links) >= 2:
                continue
            target_cluster = clusters[0] if clusters else None
            if not target_cluster:
                continue
            suggestions.append(
                LinkSuggestion(
                    source_url=page.url,
                    target_url=f"{self.site_url}/{generated_assets[0].slug}".rstrip("/") if generated_assets else self.site_url,
                    anchor_text=title_case_keyword(target_cluster.primary_keyword),
                    reason="Existing thin-link pages should reinforce the strongest current pillar page.",
                    confidence=0.72,
                    placement_hint="Add a contextual link above the fold or in a related resources block.",
                )
            )

        return suggestions

    def _find_cluster_for_asset(
        self,
        asset: ContentAsset,
        clusters: list[KeywordCluster],
    ) -> KeywordCluster | None:
        asset_keywords = set(keyword.lower() for keyword in asset.source_keywords)
        for cluster in clusters:
            if cluster.primary_keyword.lower() in asset_keywords:
                return cluster
        return clusters[0] if clusters else None

    @staticmethod
    def _best_landing_target(asset: ContentAsset, landing_targets: list[ContentAsset]) -> ContentAsset:
        asset_terms = " ".join(asset.source_keywords).lower()
        scored = []
        for target in landing_targets:
            overlap = sum(1 for term in target.source_keywords if term.lower() in asset_terms)
            scored.append((overlap, target))
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[0][1]
