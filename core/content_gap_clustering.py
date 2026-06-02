from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from utils.intent_classifier import classify_intent, infer_page_type, infer_topic_cluster

INTENT_PRIORITY = {"commercial": 0, "transactional": 1, "informational": 2, "navigational": 3}


@dataclass
class ContentGapCluster:
    cluster_name: str
    intent: str
    funnel_stage: str
    recommended_asset_type: str
    conversion_goal: str
    keywords: list[dict[str, Any]] = field(default_factory=list)
    aggregate_difficulty: float = 0.0
    aggregate_priority: float = 0.0
    strategic_rationale: str = ""
    count: int = 0


def cluster_content_gaps(
    gaps: list[dict[str, Any]],
    topic_map: dict[str, list[str]] | None = None,
) -> list[ContentGapCluster]:
    if not gaps:
        return []

    topic_map = topic_map or {}

    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for gap in gaps:
        kw = gap.get("keyword", "")
        intent, stage = classify_intent(kw)
        cluster = infer_topic_cluster(kw, topic_map)
        asset_type = infer_page_type(kw, intent)
        key = (cluster, intent, asset_type)
        groups.setdefault(key, []).append(gap)

    clusters: list[ContentGapCluster] = []
    for (cluster, intent, asset_type), members in groups.items():
        priorities = [g.get("priority", 5) for g in members]
        difficulties = [g.get("difficulty", 50) for g in members]
        avg_priority = sum(priorities) / len(priorities)
        avg_difficulty = sum(difficulties) / len(difficulties)

        primary = members[0]
        keywords_list = [g.get("keyword", "") for g in members]

        rationale = _build_rationale(cluster, intent, asset_type, len(members), keywords_list)

        conv_goal = "Drive demo requests and signups" if intent in ("commercial", "transactional") else "Capture problem-aware pipeline"
        cluster_obj = ContentGapCluster(
            cluster_name=cluster,
            intent=intent,
            funnel_stage=stage,
            recommended_asset_type=asset_type,
            conversion_goal=conv_goal,
            keywords=members,
            aggregate_difficulty=round(avg_difficulty, 1),
            aggregate_priority=round(avg_priority, 1),
            strategic_rationale=rationale,
            count=len(members),
        )
        clusters.append(cluster_obj)

    clusters.sort(key=lambda c: (INTENT_PRIORITY.get(c.intent, 9), c.aggregate_priority, c.count))
    return clusters


def _build_rationale(cluster: str, intent: str, asset_type: str, count: int, keywords: list[str]) -> str:
    top = keywords[:3]
    kw_list = ", ".join(f'"{k}"' for k in top)

    parts = []
    if intent == "commercial" and asset_type == "comparison_page":
        parts.append(f"High-intent comparison cluster ({count} keywords).")
        parts.append(f"Target: {kw_list}. Comparison pages drive decision-stage conversions and capture competitor search traffic.")
    elif intent == "commercial":
        parts.append(f"Commercial cluster ({count} keywords).")
        parts.append(f"Target: {kw_list}. These signal purchase readiness and should be addressed with a dedicated landing or comparison page.")
    elif intent == "transactional":
        parts.append(f"Transactional cluster ({count} keywords).")
        parts.append(f"Target: {kw_list}. Users are evaluating tools/platforms. A landing page with pricing or feature focus will convert.")
    elif intent == "informational":
        if asset_type == "blog_post":
            parts.append(f"Informational blog cluster ({count} keywords).")
            parts.append(f"Target: {kw_list}. Blog content captures problem-aware traffic and feeds into the conversion funnel via internal links.")
        else:
            parts.append(f"Informational use-case cluster ({count} keywords).")
            parts.append(f"Target: {kw_list}. A use-case guide or landing page with educational content will capture early-funnel traffic.")
    else:
        parts.append(f"{intent.capitalize()} cluster ({count} keywords).")
        parts.append(f"Keywords: {kw_list}.")

    parts.append("Commercial/transactional clusters should be prioritized over informational.")
    return " ".join(parts)
