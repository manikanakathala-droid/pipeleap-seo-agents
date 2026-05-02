from __future__ import annotations

from collections import defaultdict
import re
from typing import Any

from utils.intent_classifier import classify_intent, infer_page_type, infer_topic_cluster
from utils.models import KeywordCluster, KeywordOpportunity, PageSnapshot
from utils.ranking_model import (
    estimate_business_fit,
    estimate_conversion_probability,
    estimate_cpc,
    estimate_difficulty,
    estimate_speed_to_rank,
    estimate_traffic_potential,
)
from utils.scoring import revenue_priority_score
from utils.text import dedupe_preserve_order, slugify


class KeywordEngine:
    """Builds Pipeleap-specific keyword opportunities from API and on-site data."""

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger
        self.site_config = config.get("site", {})
        self.seo_config = config.get("seo", {})
        self.brand = self.site_config.get("brand", "Pipeleap")
        self.topic_map = self.seo_config.get("topic_map", {})
        self.semantic_expansions = self.seo_config.get("semantic_expansions", {})
        self.seed_keywords = self.seo_config.get("seed_keywords", {})
        self.keyword_overrides = self.seo_config.get("keyword_overrides", {})
        self.competitors = self.seo_config.get("competitors", [])
        self.stages_config = config.get("saas_stages", {}).get("enabled", ["early", "growth", "scale"])

    def discover(
        self,
        gsc_rows: list[dict[str, Any]],
        pages: list[PageSnapshot],
        existing_slugs: set[str] | None = None,
    ) -> tuple[list[KeywordCluster], list[str]]:
        keyword_records = self._collect_candidates(gsc_rows, pages, existing_slugs or set())
        use_estimated_metrics = self.seo_config.get("allow_estimated_keyword_metrics", True)
        integration_requests: list[str] = []
        opportunities: list[KeywordOpportunity] = []

        feature_terms = self.site_config.get("core_features", []) + list(self.topic_map.keys())

        for keyword, record in keyword_records.items():
            intent, funnel_stage = classify_intent(keyword, self.brand)
            topic_cluster = infer_topic_cluster(keyword, self.topic_map)
            metrics = record.get("metrics", {})
            clicks = int(metrics.get("clicks", 0))
            impressions = int(metrics.get("impressions", 0))
            ctr = float(metrics.get("ctr", 0.0))
            position = metrics.get("position")
            position_value = float(position) if position not in (None, "") else None
            override = self.keyword_overrides.get(keyword) or self.keyword_overrides.get(keyword.lower(), {})

            cpc_source = "missing"
            difficulty_source = "missing"
            estimated_cpc = None
            estimated_difficulty = None

            if "cpc_usd" in override:
                estimated_cpc = float(override["cpc_usd"])
                cpc_source = "config_override"
            elif use_estimated_metrics:
                estimated_cpc = estimate_cpc(keyword, intent)
                cpc_source = "model_estimate"

            if "difficulty" in override:
                estimated_difficulty = float(override["difficulty"])
                difficulty_source = "config_override"
            elif use_estimated_metrics:
                estimated_difficulty = estimate_difficulty(keyword, intent, self.competitors)
                difficulty_source = "model_estimate"

            if not gsc_rows:
                gsc_creds = self.config.get("integrations", {}).get("gsc", {}).get("credentials_path", "")
                if gsc_creds:
                    integration_requests.append(
                        "GSC is connected but returned no impressions yet — site may not be indexed or is too new for data."
                    )
                else:
                    integration_requests.append(
                        "Connect Search Console to replace model-only opportunity scoring with live impressions, CTR, and ranking data."
                    )

            business_fit = estimate_business_fit(
                keyword,
                [self.brand, *self.site_config.get("target_personas", [])],
                feature_terms,
            )
            conversion_probability = estimate_conversion_probability(keyword, intent)
            traffic_potential = estimate_traffic_potential(intent, impressions, ctr, position_value)
            speed_to_rank = estimate_speed_to_rank(estimated_difficulty, position_value)
            semantic_terms = dedupe_preserve_order(
                list(self.semantic_expansions.get(topic_cluster, [])) + record.get("semantic_terms", [])
            )[:8]

            notes = []
            if not impressions:
                notes.append("No Search Console impressions attached yet; traffic potential is heuristic until GSC is connected.")
            if record.get("sources"):
                notes.append(f"Sources: {', '.join(sorted(record['sources']))}.")

            opportunities.append(
                KeywordOpportunity(
                    keyword=keyword,
                    topic_cluster=topic_cluster,
                    intent=intent,
                    funnel_stage=funnel_stage,
                    source=", ".join(sorted(record["sources"])),
                    current_clicks=clicks,
                    current_impressions=impressions,
                    current_ctr=ctr,
                    average_position=position_value,
                    estimated_cpc_usd=estimated_cpc,
                    cpc_source=cpc_source,
                    estimated_difficulty=estimated_difficulty,
                    difficulty_source=difficulty_source,
                    conversion_probability=conversion_probability,
                    business_fit=business_fit,
                    traffic_potential_score=traffic_potential,
                    speed_to_rank_score=speed_to_rank,
                    revenue_priority_score=revenue_priority_score(
                        conversion_probability,
                        business_fit,
                        traffic_potential,
                        speed_to_rank,
                        position_value,
                    ),
                    semantic_expansions=semantic_terms,
                    notes=notes,
                )
            )

        deduped_requests = dedupe_preserve_order(integration_requests)
        return self._cluster_opportunities(opportunities), deduped_requests

    def _collect_candidates(
        self,
        gsc_rows: list[dict[str, Any]],
        pages: list[PageSnapshot],
        existing_slugs: set[str],
    ) -> dict[str, dict[str, Any]]:
        records: dict[str, dict[str, Any]] = {}
        # Stop words for semantic deduplication — strips these before comparing.
        # DO NOT include words that carry distinct ranking meaning:
        #   "ai", "automated", "platform", "system", "tool" all produce DIFFERENT
        #   SERPs — stripping them collapses distinct keyword opportunities into one.
        # Only strip true filler words that never appear in real searcher queries.
        topic_stop_words = {
            "how", "to", "the", "a", "an", "of", "in", "on", "and", "or", "for",
            "with", "by", "from", "at", "that", "your", "our", "its", "my",
        }

        def semantic_key(keyword: str) -> str:
            """Reduces keyword to its semantic core for deduplication."""
            parts = re.sub(r"[^a-z0-9 ]+", "", keyword.lower()).split()
            core = [p for p in parts if p not in topic_stop_words]
            return "-".join(core) if core else "-".join(parts)

        semantic_seen: dict[str, str] = {} # maps semantic_key -> primary_keyword

        def touch_keyword(keyword: str, source: str, metric_payload: dict[str, Any] | None = None) -> None:
            normalized_keyword = keyword.strip()
            if not normalized_keyword:
                return

            # Skip if slug already exists to prevent redundant generation
            if slugify(normalized_keyword) in existing_slugs:
                self.logger.debug(f"Skipping existing slug: {slugify(normalized_keyword)}")
                return

            # Semantic Deduplication: avoid "how to X" and "best X tool" being different pages
            sk = semantic_key(normalized_keyword)
            if sk in semantic_seen:
                # Merge into existing record
                primary = semantic_seen[sk]
                record = records[primary]
                self.logger.debug(f"Merging keyword '{normalized_keyword}' into '{primary}' via semantic key '{sk}'")
            else:
                semantic_seen[sk] = normalized_keyword
                record = records.setdefault(
                    normalized_keyword,
                    {
                        "sources": set(),
                        "metrics": {"clicks": 0, "impressions": 0, "ctr": 0.0, "position": None},
                        "semantic_terms": [],
                    },
                )
            record["sources"].add(source)
            if metric_payload:
                record["metrics"]["clicks"] += int(metric_payload.get("clicks", 0))
                record["metrics"]["impressions"] += int(metric_payload.get("impressions", 0))
                position = metric_payload.get("position")
                if position not in (None, ""):
                    existing_position = record["metrics"].get("position")
                    if existing_position is None:
                        record["metrics"]["position"] = float(position)
                    else:
                        record["metrics"]["position"] = round(
                            (float(existing_position) + float(position)) / 2.0,
                            2,
                        )
                impressions = record["metrics"]["impressions"]
                if impressions > 0:
                    ctr_value = record["metrics"]["clicks"] / impressions
                    record["metrics"]["ctr"] = round(ctr_value, 4)

        for category, keywords in self.seed_keywords.items():
            for keyword in keywords:
                touch_keyword(str(keyword), f"seed:{category}")

        for keyword in self._expand_stage_keywords():
            touch_keyword(keyword, "seed:stage_matrix")

        for row in gsc_rows:
            query = str(row.get("query", "")).strip()
            if query:
                touch_keyword(query, "gsc", row)

        for page in pages:
            for candidate in (page.h1, page.title):
                if candidate and len(candidate.split()) <= 12:
                    touch_keyword(candidate, "site_crawl")
            for heading in page.headings[:4]:
                if heading and len(heading.split()) <= 10:
                    touch_keyword(heading, "site_heading")

        return records

    def _expand_stage_keywords(self) -> list[str]:
        """Generate Stage × use-case keyword combinations for all enabled SaaS stages."""
        from utils.stage_messaging import STAGES
        keywords: list[str] = []
        for stage_key in self.stages_config:
            stage = STAGES.get(stage_key)
            if not stage:
                continue
            keywords.extend(stage["seed_keywords"])
            # Cross-product with seed high-intent terms
            for seed in self.seed_keywords.get("high_intent", [])[:5]:
                keywords.append(f"{seed} for {stage['slug_suffix']}")
        return keywords

    @staticmethod
    def _stage_from_keyword(keyword: str) -> str:
        kw = keyword.lower()
        if any(s in kw for s in ("early-stage", "early stage", "startup", "founder", "pre-sdr", "pre-seed")):
            return "early"
        if any(s in kw for s in ("enterprise-saas", "enterprise", "revops", "multi-territory", "governance")):
            return "scale"
        if any(s in kw for s in ("growth-stage", "growth stage", "series a", "series b", "sdr team", "growing")):
            return "growth"
        return ""

    def detect_gsc_gaps(
        self,
        gsc_rows: list[dict[str, Any]],
        existing_slugs: set[str],
    ) -> list[dict[str, Any]]:
        """
        Identify queries where Google is already showing Pipeleap but no page
        exists that directly targets them. These are the highest-confidence
        organic opportunities — Google has already decided Pipeleap is relevant,
        the site just hasn't given it a dedicated page yet.

        Returns list of gap dicts sorted by impression volume (highest first).
        """
        gaps: list[dict[str, Any]] = []

        for row in gsc_rows:
            query = str(row.get("query", "")).strip()
            if not query or len(query.split()) < 2:
                continue

            impressions = int(row.get("impressions", 0))
            clicks = int(row.get("clicks", 0))
            position = float(row.get("position", 50))

            # Only flag queries with meaningful visibility
            if impressions < 10:
                continue

            # Check if any existing slug targets this query
            slug_candidate = slugify(query)
            already_covered = (
                slug_candidate in existing_slugs
                or any(
                    # slug contains the core of the query
                    all(w in s for w in query.lower().split()[:3])
                    for s in existing_slugs
                )
            )

            if not already_covered:
                intent, funnel_stage = classify_intent(query, self.brand)
                gaps.append({
                    "query": query,
                    "impressions": impressions,
                    "clicks": clicks,
                    "position": round(position, 1),
                    "ctr": round(row.get("ctr", 0.0), 4),
                    "intent": intent,
                    "funnel_stage": funnel_stage,
                    "recommended_page_type": infer_page_type(query, intent),
                    "opportunity_score": round(
                        (impressions / 100) * (1 - min(position / 50, 1)) * (1 + (1 if intent in ("commercial", "transactional") else 0)),
                        2
                    ),
                })

        return sorted(gaps, key=lambda x: x["opportunity_score"], reverse=True)

    def _cluster_opportunities(self, opportunities: list[KeywordOpportunity]) -> list[KeywordCluster]:
        # Include stage in the grouping key so stage variants get their own clusters
        grouped: dict[tuple[str, str, str, str], list[KeywordOpportunity]] = defaultdict(list)
        for opportunity in opportunities:
            asset_type = infer_page_type(opportunity.keyword, opportunity.intent)
            stage = self._stage_from_keyword(opportunity.keyword)
            grouped[(opportunity.topic_cluster, opportunity.intent, asset_type, stage)].append(opportunity)

        clusters: list[KeywordCluster] = []
        for (topic_cluster, intent, asset_type, stage), group in grouped.items():
            ranked = sorted(group, key=lambda item: item.revenue_priority_score, reverse=True)
            primary = ranked[0]
            conversion_goal = "Drive demo requests and signups" if intent in {"commercial", "transactional"} else "Capture problem-aware pipeline"
            cluster_name = f"{topic_cluster} ({stage})" if stage else topic_cluster
            clusters.append(
                KeywordCluster(
                    cluster_name=cluster_name,
                    primary_keyword=primary.keyword,
                    intent=intent,
                    recommended_asset_type=asset_type,
                    conversion_goal=conversion_goal,
                    opportunities=ranked,
                    aggregate_traffic_potential=round(
                        sum(item.traffic_potential_score for item in ranked) / max(len(ranked), 1),
                        2,
                    ),
                    aggregate_conversion_potential=round(
                        sum(item.conversion_probability for item in ranked) / max(len(ranked), 1),
                        2,
                    ),
                    strategic_rationale=(
                        f"Build topical authority around {cluster_name} and route demand into "
                        f"Pipeleap's workflow automation value proposition."
                    ),
                )
            )

        return sorted(
            clusters,
            key=lambda cluster: (
                cluster.aggregate_conversion_potential,
                cluster.aggregate_traffic_potential,
                cluster.opportunities[0].revenue_priority_score,
            ),
            reverse=True,
        )
