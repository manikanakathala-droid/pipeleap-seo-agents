from __future__ import annotations

from typing import Iterable

from utils.scoring import clamp


def estimate_cpc(keyword: str, intent: str) -> float:
    keyword_lower = keyword.lower()
    base = {
        "transactional": 18.0,
        "commercial": 14.0,
        "informational": 6.0,
        "navigational": 3.0,
    }.get(intent, 10.0)

    boosts = {
        "outbound": 3.5,
        "sales": 3.0,
        "automation": 2.5,
        "crm": 2.0,
        "lead": 2.0,
        "enrichment": 3.0,
        "ai": 1.5,
        "sdr": 2.5,
        "n8n": 1.5,
        "revenue": 2.0,
        "platform": 2.5,
        "workflow": 1.0,
    }
    matched = [weight for term, weight in boosts.items() if term in keyword_lower]
    modifier = sum(matched[:4]) * 0.65
    long_tail_bonus = 1.5 if len(keyword_lower.split()) >= 4 else 0.0
    return round(max(2.0, min(60.0, base + modifier + long_tail_bonus)), 2)


def estimate_difficulty(keyword: str, intent: str, competitor_names: Iterable[str]) -> float:
    keyword_lower = keyword.lower()
    words = keyword_lower.split()
    score = 55.0

    if len(words) >= 4:
        score -= 12.0
    if keyword_lower.startswith("how to"):
        score -= 8.0
    if any(term in keyword_lower for term in ("platform", "software", "automation")):
        score += 6.0
    if "n8n" in keyword_lower:
        score -= 4.0
    if intent == "transactional":
        score += 3.0
    if any(competitor.lower() in keyword_lower for competitor in competitor_names):
        score += 4.0

    return round(max(18.0, min(88.0, score)), 1)


def estimate_conversion_probability(keyword: str, intent: str) -> float:
    keyword_lower = keyword.lower()
    base = {
        "transactional": 0.73,
        "commercial": 0.64,
        "informational": 0.34,
        "navigational": 0.5,
    }.get(intent, 0.5)

    boosters = 0.0
    if any(term in keyword_lower for term in ("demo", "pricing", "platform", "software")):
        boosters += 0.12
    if any(term in keyword_lower for term in ("outbound", "sales", "crm", "lead enrichment", "ai sdr")):
        boosters += 0.08
    if keyword_lower.startswith("how to"):
        boosters -= 0.05

    return round(clamp(base + boosters), 2)


def estimate_business_fit(keyword: str, brand_terms: Iterable[str], feature_terms: Iterable[str]) -> float:
    keyword_lower = keyword.lower()
    term_hits = sum(1 for term in brand_terms if term.lower() in keyword_lower)
    feature_hits = sum(1 for term in feature_terms if term.lower() in keyword_lower)
    raw = 0.3 + min(0.4, term_hits * 0.08) + min(0.3, feature_hits * 0.06)
    return round(clamp(raw), 2)


def estimate_traffic_potential(
    intent: str,
    current_impressions: int = 0,
    current_ctr: float = 0.0,
    average_position: float | None = None,
) -> float:
    if current_impressions > 0:
        target_ctr = 0.12
        if average_position is not None:
            if average_position > 10:
                target_ctr = 0.06
            if average_position > 20:
                target_ctr = 0.04
        ctr_gap = max(target_ctr - current_ctr, 0.02)
        lift_signal = min(1.0, (current_impressions * ctr_gap) / 1200.0)
        if average_position is not None and 8 <= average_position <= 20:
            lift_signal = min(1.0, lift_signal + 0.15)
        return round(clamp(lift_signal), 2)

    fallback = {
        "transactional": 0.62,
        "commercial": 0.68,
        "informational": 0.46,
        "navigational": 0.2,
    }.get(intent, 0.5)
    return round(fallback, 2)


def estimate_speed_to_rank(estimated_difficulty: float | None, average_position: float | None) -> float:
    difficulty_component = 0.5
    if estimated_difficulty is not None:
        difficulty_component = clamp(1.0 - (estimated_difficulty / 100.0))

    position_component = 0.45
    if average_position is not None:
        if average_position <= 10:
            position_component = 0.9
        elif average_position <= 20:
            position_component = 0.75
        elif average_position <= 40:
            position_component = 0.55
        else:
            position_component = 0.3

    return round(clamp((difficulty_component * 0.55) + (position_component * 0.45)), 2)
