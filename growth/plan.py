"""
Decide what to do next, under explicit guards.

The guards are the point. The previous system published hundreds of pages with
no evidence any were indexed. Here, new pages are rationed, paused when earlier
ones are not being indexed, and capped while no search data is flowing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from growth.icp import ICPModel
from growth.learn import Opportunity
from growth.ledger import Ledger
from growth.measure import Measurement
from growth.site import SiteModel


@dataclass
class Action:
    kind: str                 # foundation | redirect | new_page | refresh | snippet | review
    title: str
    why: str
    path: str = ""
    priority: float = 0.0
    auto: bool = False        # True: the loop executes it. False: needs a person.
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    actions: list[Action] = field(default_factory=list)
    holds: list[str] = field(default_factory=list)       # reasons new content is paused or capped
    weights: dict[str, float] = field(default_factory=dict)
    new_page_budget: int = 0

    def auto(self) -> list[Action]:
        return [a for a in self.actions if a.auto]

    def manual(self) -> list[Action]:
        return [a for a in self.actions if not a.auto]


def slugify(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:70].strip("-")


def _already_redirected(path: str, growth: dict[str, Any], ledger: Ledger) -> bool:
    if path in ledger.data.get("redirects", {}):
        return True
    for rule in growth.get("redirects", []):
        source = rule["source"]
        prefix = source.split("/:")[0]
        if path == source or (prefix != source and (path == prefix or path.startswith(prefix + "/"))):
            return True
    return False


def new_page_budget(ledger: Ledger, measurement: Measurement, today: date,
                    rules: dict[str, Any]) -> tuple[int, list[str]]:
    holds: list[str] = []
    managed = {p: m for p, m in ledger.data["pages"].items() if m.get("kind") == "article"}
    per_week = int(rules.get("max_new_pages_per_week", 2))
    recent = sum(1 for m in managed.values()
                 if (today - date.fromisoformat(m["published_at"])).days < 7)
    budget = max(0, per_week - recent)
    if recent >= per_week:
        holds.append(f"Weekly limit reached: {recent} page(s) published in the last 7 days (limit {per_week}).")

    if not measurement.search.ok:
        cap = int(rules.get("max_pages_without_search_data", 3))
        if len(managed) >= cap:
            budget = 0
            holds.append(f"No search data is flowing ({measurement.search.detail}). "
                         f"Holding at {len(managed)} published page(s) until results can be measured.")
        else:
            budget = min(budget, cap - len(managed))
    else:
        grace = int(rules.get("indexing_grace_days", 21))
        mature = [p for p, m in managed.items() if (today - date.fromisoformat(m["published_at"])).days >= grace]
        seen = [p for p in mature if ledger.latest_metrics(p).get("impressions", 0) > 0]
        if len(mature) >= 2 and len(seen) / len(mature) < float(rules.get("min_indexed_share", 0.5)):
            budget = 0
            holds.append(f"Only {len(seen)} of {len(mature)} pages older than {grace} days have any impressions. "
                         "New pages are paused: the constraint is indexing and authority, not content volume.")
    return budget, holds


def build_plan(*, site: SiteModel, ledger: Ledger, measurement: Measurement, icp: ICPModel,
               opportunities: list[Opportunity], foundation_gaps: list[dict[str, Any]],
               weights: dict[str, float], growth: dict[str, Any], today: date,
               writer_available: bool) -> Plan:
    rules = growth.get("guards", {})
    cooldown = int(rules.get("cooldown_days", 21))
    plan = Plan(weights=weights)
    plan.new_page_budget, plan.holds = new_page_budget(ledger, measurement, today, rules)
    if not writer_available:
        plan.holds.append("No LLM credentials in this environment: pages cannot be drafted, so briefs are written instead.")

    def cooling(path: str) -> bool:
        age = ledger.days_since_change(path, today)
        return ledger.has_open_experiment(path) or (age is not None and age < cooldown)

    # 1. Site foundation: deterministic, always first.
    for gap in foundation_gaps:
        plan.actions.append(Action("foundation", gap["title"], gap["why"], path=gap.get("path", ""),
                                   priority=100 - gap.get("order", 0), auto=gap.get("auto", True),
                                   payload=gap))

    # 2. Evidence-backed moves from search data.
    candidates: list[tuple[float, str, str, str, str, dict[str, Any]]] = []  # value, query, cluster, why, source, evidence
    for opp in opportunities:
        page = site.page(opp.path)
        managed = bool(page and page.managed)
        if opp.kind == "legacy_url":
            if _already_redirected(opp.path, growth, ledger):
                continue
            plan.actions.append(Action("redirect", f"Redirect {opp.path}", opp.rationale, path=opp.path,
                                       priority=60 + min(20, opp.value), auto=True, payload=opp.evidence))
        elif opp.kind == "content_gap":
            candidates.append((opp.value * (0.5 + weights.get(opp.cluster, 0.5)), opp.query, opp.cluster,
                               opp.rationale, "search data", opp.evidence))
        elif opp.kind in ("striking_distance", "decay", "low_ctr") and managed and not cooling(opp.path):
            plan.actions.append(Action("refresh", f"Refresh {opp.path}" + (f" for “{opp.query}”" if opp.query else ""),
                                       opp.rationale, path=opp.path, priority=50 + min(30, opp.value),
                                       auto=writer_available, payload={"query": opp.query, "cluster": opp.cluster,
                                                                       "evidence": opp.evidence}))
        else:
            # Hand-authored pages and judgement calls go to a person, with the evidence attached.
            label = {"striking_distance": "Strengthen", "decay": "Investigate decline on", "low_ctr": "Improve snippet of",
                     "cannibalization": "Resolve overlap on", "converter": "Double down on",
                     "leaky_page": "Fix conversion on"}.get(opp.kind, "Review")
            plan.actions.append(Action("review", f"{label} {opp.path}" + (f" (“{opp.query}”)" if opp.query else ""),
                                       opp.rationale, path=opp.path, priority=20 + min(25, opp.value),
                                       payload={"signal": opp.kind, "evidence": opp.evidence}))

    # 3. Backlog of hypotheses, ranked by ICP fit and what the clusters have earned so far.
    for item in growth.get("backlog", []):
        qual = icp.qualify(item["query"])
        if not qual.qualified:
            continue
        cluster = item.get("cluster") or qual.cluster
        candidates.append((10 * qual.fit * (0.5 + weights.get(cluster, 0.5)), item["query"], cluster,
                           item.get("angle", "Backlog hypothesis; no search evidence yet."), "backlog", {}))

    existing = {m.get("target_query", "").lower() for m in ledger.data["pages"].values()}
    existing_paths = {p.path for p in site.pages}
    seen: set[str] = set()
    remaining = plan.new_page_budget
    for value, query, cluster, why, source, evidence in sorted(candidates, key=lambda c: c[0], reverse=True):
        slug = slugify(query)
        path = f"/{growth.get('publish', {}).get('section', 'resources')}/{slug}"
        if query.lower() in existing or query.lower() in seen or path in existing_paths:
            continue
        seen.add(query.lower())
        can_write = remaining > 0 and writer_available
        plan.actions.append(Action(
            "new_page", f"Publish a page for “{query}”", f"{why} (source: {source})", path=path,
            priority=(40 if can_write else 10) + min(25, value), auto=can_write,
            payload={"query": query, "cluster": cluster, "evidence": evidence, "source": source}))
        if can_write:
            remaining -= 1

    plan.actions.sort(key=lambda a: a.priority, reverse=True)
    return plan
