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

    if keyword_lower == brand_lower or keyword_lower.startswith(f"{brand_lower} "):
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
    if any(term in keyword_lower for term in COMPARISON_TERMS):
        return "comparison_page"
    if "for " in keyword_lower or "use case" in keyword_lower:
        return "use_case_page"
    if intent in {"transactional", "commercial"}:
        return "landing_page"
    return "blog_post"


def keyword_matches_terms(keyword: str, terms: Iterable[str]) -> int:
    keyword_lower = keyword.lower()
    return sum(1 for term in terms if term.lower() in keyword_lower)
