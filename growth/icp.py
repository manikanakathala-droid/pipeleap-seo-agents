"""
Qualify a search query against Pipeleap's ICP.

Traffic is not the goal; enquiries from B2B sales leaders and RevOps are. Every
query is scored for how likely the searcher is someone who could buy, and
assigned to a topic cluster so learning can generalise across queries.
All vocabulary comes from growth.yaml, so positioning changes need no code.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_WORD = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _contains(query: str, phrase: str) -> bool:
    return re.search(rf"\b{re.escape(phrase.lower())}\b", query) is not None


@dataclass
class Qualification:
    query: str
    fit: float                    # 0..1 likelihood the searcher is in the ICP with a relevant problem
    cluster: str                  # topic cluster id, "" when none matches
    stage: str                    # problem | solution | product | navigational | unqualified
    reasons: list[str] = field(default_factory=list)

    @property
    def qualified(self) -> bool:
        return self.stage != "unqualified" and self.fit >= 0.45


class ICPModel:
    def __init__(self, config: dict[str, Any]) -> None:
        icp = config.get("icp", {})
        self.brand = config.get("brand", "pipeleap").lower()
        self.personas = [p.lower() for p in icp.get("persona_terms", [])]
        self.context = [c.lower() for c in icp.get("context_terms", [])]
        self.disqualifiers = [d.lower() for d in icp.get("disqualifiers", [])]
        self.solution_terms = [s.lower() for s in icp.get("solution_terms", [])]
        self.problem_terms = [p.lower() for p in icp.get("problem_terms", [])]
        self.clusters: dict[str, dict[str, Any]] = config.get("clusters", {})

    def cluster_for(self, query: str) -> tuple[str, int]:
        best, best_hits = "", 0
        for cluster_id, spec in self.clusters.items():
            hits = sum(1 for term in spec.get("terms", []) if _contains(query, term))
            if hits > best_hits:
                best, best_hits = cluster_id, hits
        return best, best_hits

    def qualify(self, query: str) -> Qualification:
        q = " ".join(tokens(query))
        reasons: list[str] = []

        if self.brand and self.brand in q:
            return Qualification(query, 1.0, "brand", "navigational", ["brand query"])

        for term in self.disqualifiers:
            if _contains(q, term):
                return Qualification(query, 0.0, "", "unqualified", [f"disqualified by '{term}'"])

        cluster, hits = self.cluster_for(q)
        score = 0.0
        if cluster:
            score += 0.35 + min(hits - 1, 2) * 0.08
            reasons.append(f"matches cluster '{cluster}' ({hits} term{'s' if hits > 1 else ''})")

        if any(_contains(q, term) for term in self.context):
            score += 0.2
            reasons.append("B2B sales context")
        if any(_contains(q, term) for term in self.personas):
            score += 0.15
            reasons.append("names an ICP persona")

        stage = "problem"
        if any(_contains(q, term) for term in self.solution_terms):
            stage = "solution"
            score += 0.2
            reasons.append("solution-seeking intent")
        elif any(_contains(q, term) for term in self.problem_terms):
            score += 0.12
            reasons.append("problem-aware intent")

        if len(q.split()) <= 1:
            score -= 0.25
            reasons.append("single-word query is too broad to qualify")
        if not cluster:
            stage = "unqualified"
            reasons.append("no topic cluster matches what Pipeleap does")

        return Qualification(query, round(max(0.0, min(1.0, score)), 3), cluster, stage, reasons)
