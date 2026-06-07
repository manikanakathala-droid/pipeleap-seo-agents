from __future__ import annotations

from typing import Iterable


COMPARISON_TERMS = {"alternative", "alternatives", "vs", "versus", "compare", "comparison"}
TRANSACTIONAL_TERMS = {
    "pricing",
    "demo",
    "trial",
    "book",
    "platform",
    "software",
    "tool",
    "system",
    "solution",
    "service",
}
INFORMATIONAL_TERMS = {
    "how to",
    "guide",
    "workflow",
    "workflows",
    "template",
    "templates",
    "playbook",
    "automate",
    "setup",
    "build",
    "scale",
}


def classify_intent(keyword: str, brand: str = "Pipeleap") -> tuple[str, str]:
    keyword_lower = keyword.lower().strip()
    brand_lower = brand.lower().strip()

    if keyword_lower == brand_lower:
        return "navigational", "decision"
    if any(term in keyword_lower for term in COMPARISON_TERMS):
        return "commercial", "decision"
    if any(term in keyword_lower for term in TRANSACTIONAL_TERMS):
        return "transactional", "decision"
    if keyword_lower.startswith("how ") or any(term in keyword_lower for term in INFORMATIONAL_TERMS):
        return "informational", "problem-aware"
    return "commercial", "solution-aware"


def infer_topic_cluster(keyword: str, topic_map: dict[str, list[str]]) -> str:
    keyword_lower = keyword.lower()
    best_cluster = "revenue automation"
    best_score = 0

    for cluster, markers in topic_map.items():
        score = 0
        for marker in markers:
            marker_lower = marker.lower().strip()
            if marker_lower in keyword_lower:
                score += len(marker_lower.split())
        if score > best_score:
            best_cluster = cluster
            best_score = score

    return best_cluster


def infer_page_type(keyword: str, intent: str) -> str:
    keyword_lower = keyword.lower()
    if "for " in keyword_lower or "use case" in keyword_lower:
        return "use_case_page"
    if intent in {"transactional", "commercial"}:
        return "landing_page"
    return "blog_post"


def keyword_matches_terms(keyword: str, terms: Iterable[str]) -> int:
    keyword_lower = keyword.lower()
    return sum(1 for term in terms if term.lower() in keyword_lower)


# Pillar-level brand markers for Pipeleap's core topic areas.
# Mirrors topical_authority.PILLARS but expressed as flat keyword signals
# so the guard works without importing the full pillar registry.
_BRAND_MARKERS: dict[str, list[str]] = {
    "outbound-automation": [
        "outbound", "cold email", "cold outreach", "sdr", "bdr", "sequencing",
        "sales engagement", "cadence",
    ],
    "pipeline-generation": [
        "pipeline", "leads", "prospecting", "demand generation", "top of funnel",
        "qualified leads", "pipeline velocity",
    ],
    "workflow-orchestration": [
        "workflow", "automation", "orchestration", "n8n", "zapier", "make",
        "clay", "playbook", "recipe",
    ],
    "competitor-comparison": [
        "vs", "versus", "alternative", "alternatives", "compare", "comparison",
        "pipeleap", "salesloft", "outreach", "apollo", "instantly",
    ],
    "revops": [
        "revops", "revenue operations", "crm", "hubspot", "salesforce",
        "sales ops", "go-to-market", "gtm",
    ],
    "glossary": [
        "what is", "definition", "meaning", "glossary",
    ],
    "integrations": [
        "integration", "connect", "sync", "api", "webhook",
    ],
}


def check_topic_relevance(keyword: str) -> dict:
    """
    "Why" intent guard — validates whether a keyword is on-brand for Pipeleap
    before content is commissioned.

    Returns a dict with:
        is_on_brand: bool
        matched_pillar: str | None
        warning: str | None   — present when is_on_brand is False
    """
    keyword_lower = keyword.lower().strip()
    best_pillar: str | None = None
    best_score = 0

    for pillar, markers in _BRAND_MARKERS.items():
        score = sum(1 for m in markers if m in keyword_lower)
        if score > best_score:
            best_score = score
            best_pillar = pillar

    if best_score > 0:
        return {"is_on_brand": True, "matched_pillar": best_pillar, "warning": None}

    return {
        "is_on_brand": False,
        "matched_pillar": None,
        "warning": (
            f"'{keyword}' does not match any of Pipeleap's core topic pillars "
            "(outbound automation, pipeline generation, workflow orchestration, "
            "RevOps, competitor comparisons, glossary, integrations). "
            "Publishing off-brand content primarily for search traffic is a "
            "search-engine-first behaviour Google penalises. "
            "Confirm this topic serves an existing audience need before commissioning."
        ),
    }
