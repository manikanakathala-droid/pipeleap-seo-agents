from __future__ import annotations

from typing import Iterable


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def normalize(value: float, max_value: float, default: float = 0.0) -> float:
    if max_value <= 0:
        return default
    return clamp(value / max_value)


def weighted_average(values: Iterable[tuple[float, float]], default: float = 0.0) -> float:
    numerator = 0.0
    denominator = 0.0
    for value, weight in values:
        numerator += value * weight
        denominator += weight
    if denominator == 0:
        return default
    return numerator / denominator


def revenue_priority_score(
    conversion_probability: float,
    business_fit: float,
    traffic_potential: float,
    speed_to_rank: float,
    average_position: float | None = None,
) -> float:
    position_bonus = 0.2
    if average_position is not None:
        if average_position <= 10:
            position_bonus = 1.0
        elif average_position <= 20:
            position_bonus = 0.8
        elif average_position <= 40:
            position_bonus = 0.55
        else:
            position_bonus = 0.3

    score = weighted_average(
        [
            (conversion_probability, 0.32),
            (business_fit, 0.26),
            (traffic_potential, 0.18),
            (speed_to_rank, 0.14),
            (position_bonus, 0.10),
        ]
    )
    return round(score * 100.0, 2)


def label_revenue_impact(score: float) -> str:
    if score >= 75:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"


def label_ranking_difficulty(score: float | None) -> str:
    if score is None:
        return "Unknown"
    if score >= 65:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def label_speed_to_rank(score: float) -> str:
    if score >= 0.66:
        return "Fast"
    if score >= 0.4:
        return "Moderate"
    return "Slow"


def label_effort(score: float) -> str:
    if score <= 0.33:
        return "Easy"
    if score <= 0.66:
        return "Medium"
    return "Hard"
