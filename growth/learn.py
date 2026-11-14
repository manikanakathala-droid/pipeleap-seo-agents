"""
Turn measurements into knowledge.

  observe()               store today's page and query metrics
  evaluate_experiments()  judge past changes against their baselines
  update_priors()         fold verdicts into per-cluster beliefs (Beta posteriors)
  cluster_weights()       Thompson-sample those beliefs to decide where to invest
  find_opportunities()    read the search data for specific, evidenced next moves
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from growth.icp import ICPModel, tokens
from growth.ledger import Ledger
from growth.measure import Measurement
from growth.site import SiteModel, normalize_path

# Typical organic CTR by average position; used only to spot under-performing snippets.
EXPECTED_CTR = {1: 0.28, 2: 0.15, 3: 0.10, 4: 0.07, 5: 0.05, 6: 0.04, 7: 0.03, 8: 0.025, 9: 0.02, 10: 0.018}
CHECKPOINT_DAYS = (14, 28, 56)


def expected_ctr(position: float) -> float:
    return EXPECTED_CTR.get(max(1, min(10, round(position))), 0.01) if position <= 10.5 else 0.008


@dataclass
class Opportunity:
    kind: str
    path: str
    rationale: str
    query: str = ""
    cluster: str = ""
    fit: float = 0.0
    value: float = 0.0            # estimated extra qualified clicks per window; for ranking only
    evidence: dict[str, Any] = field(default_factory=dict)


# ── observe ────────────────────────────────────────────────────────────────
def observe(ledger: Ledger, measurement: Measurement) -> None:
    if not (measurement.search.ok or measurement.analytics.ok):
        return
    ledger.record_observations(measurement.day, measurement.per_page())
    today = measurement.day.isoformat()
    queries = ledger.data["queries"]
    for row in measurement.rows:
        query = row.get("query", "")
        if not query:
            continue
        entry = queries.setdefault(query, {"first_seen": today})
        entry.update({"impressions": row.get("impressions", 0), "clicks": row.get("clicks", 0),
                      "position": round(float(row.get("position", 0)), 1),
                      "page": normalize_path(row.get("page", "")), "last_seen": today})


# ── experiments ────────────────────────────────────────────────────────────
def evaluate_experiments(ledger: Ledger, measurement: Measurement, today: date,
                         thresholds: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Add checkpoints to open experiments and close those with enough evidence."""
    if not measurement.search.ok:
        return []  # no data, no judgement
    t = {"min_clicks_win": 3, "min_impressions_alive": 20, "relative_change": 0.2, **(thresholds or {})}
    pages = measurement.per_page()
    updated = []
    for exp in ledger.open_experiments():
        age = (today - date.fromisoformat(exp["started_at"])).days
        due = [d for d in CHECKPOINT_DAYS if d <= age and d not in {c["day"] for c in exp["checkpoints"]}]
        if not due:
            continue
        now = pages.get(exp["path"], {"impressions": 0, "clicks": 0, "position": 0.0, "enquiries": 0})
        checkpoint = {"day": max(due), "at": today.isoformat(),
                      "metrics": {k: now.get(k, 0) for k in ("impressions", "clicks", "position", "enquiries")}}
        verdict = _verdict(exp, now, max(due), t)
        checkpoint["verdict"] = verdict
        exp["checkpoints"].append(checkpoint)
        if verdict in ("won", "lost") or max(due) >= CHECKPOINT_DAYS[-1]:
            exp["status"] = verdict if verdict in ("won", "lost") else "inconclusive"
        updated.append(exp)
    return updated


def _verdict(exp: dict[str, Any], now: dict[str, float], day: int, t: dict[str, Any]) -> str:
    base = exp.get("baseline", {})
    if now.get("enquiries", 0) > base.get("enquiries", 0):
        return "won"
    if exp["kind"] == "new_page":
        if now.get("clicks", 0) >= t["min_clicks_win"]:
            return "won"
        if day >= 56 and now.get("impressions", 0) < t["min_impressions_alive"]:
            return "lost"
        return "pending"
    if day < 28:
        return "pending"
    base_clicks, clicks = base.get("clicks", 0), now.get("clicks", 0)
    gained = clicks - base_clicks
    if gained >= t["min_clicks_win"] and clicks >= base_clicks * (1 + t["relative_change"]):
        return "won"
    base_pos, pos = base.get("position", 0), now.get("position", 0)
    if base_pos and pos and base_pos - pos >= 2 and now.get("impressions", 0) >= base.get("impressions", 0):
        return "won"
    if base_clicks >= t["min_clicks_win"] and clicks <= base_clicks * (1 - t["relative_change"]):
        return "lost"
    return "pending"


def reward(exp: dict[str, Any]) -> float:
    """0..1 score of how much an experiment contributed toward enquiries."""
    last = exp["checkpoints"][-1]["metrics"] if exp["checkpoints"] else {}
    base = exp.get("baseline", {})
    impressions = max(0.0, last.get("impressions", 0) - base.get("impressions", 0))
    clicks = max(0.0, last.get("clicks", 0) - base.get("clicks", 0))
    enquiries = max(0.0, last.get("enquiries", 0) - base.get("enquiries", 0))
    return round(0.2 * min(1.0, impressions / 200) + 0.4 * min(1.0, clicks / 10) + 0.4 * min(1.0, enquiries), 3)


def update_priors(ledger: Ledger) -> None:
    priors = ledger.data["priors"]
    for exp in ledger.data["experiments"]:
        if exp["status"] == "open" or exp.get("credited") or not exp.get("cluster"):
            continue
        prior = priors.setdefault(exp["cluster"], {"alpha": 1.0, "beta": 1.0, "experiments": 0})
        r = reward(exp)
        prior["alpha"] = round(prior["alpha"] + r, 3)
        prior["beta"] = round(prior["beta"] + (1 - r), 3)
        prior["experiments"] += 1
        exp["credited"] = True


def cluster_weights(ledger: Ledger, clusters: list[str], seed: str) -> dict[str, float]:
    """Thompson sampling: proven clusters usually win, unproven ones still get explored."""
    rng = random.Random(seed)
    weights = {}
    for cluster in clusters:
        prior = ledger.data["priors"].get(cluster, {"alpha": 1.0, "beta": 1.0})
        weights[cluster] = round(rng.betavariate(prior["alpha"], prior["beta"]), 4)
    return weights


# ── opportunities ──────────────────────────────────────────────────────────
def find_opportunities(measurement: Measurement, site: SiteModel, icp: ICPModel,
                       thresholds: dict[str, Any] | None = None) -> list[Opportunity]:
    t = {"min_query_impressions": 20, "min_page_impressions": 100, "decay_drop": 0.4,
         "min_sessions_leaky": 50, **(thresholds or {})}
    found: list[Opportunity] = []
    live_paths = {p.path for p in site.pages}
    pages = measurement.per_page()
    previous = measurement.per_page(measurement.previous_rows)

    by_query: dict[str, list[dict[str, Any]]] = {}
    for row in measurement.rows:
        if row.get("query"):
            by_query.setdefault(row["query"], []).append(row)

    for query, rows in by_query.items():
        qual = icp.qualify(query)
        total = sum(r["impressions"] for r in rows)
        top = max(rows, key=lambda r: r["impressions"])
        path = normalize_path(top["page"])
        if not qual.qualified or qual.stage == "navigational" or total < t["min_query_impressions"]:
            continue
        position = float(top["position"])
        ctr = top["clicks"] / top["impressions"] if top["impressions"] else 0.0
        evidence = {"impressions": total, "clicks": sum(r["clicks"] for r in rows), "position": round(position, 1)}

        # Two pages splitting one query: consolidate.
        rivals = [r for r in rows if r["impressions"] >= 0.2 * total]
        if len(rivals) >= 2:
            found.append(Opportunity(
                "cannibalization", path, query=query, cluster=qual.cluster, fit=qual.fit,
                value=total * 0.02 * qual.fit, evidence={**evidence, "pages": [normalize_path(r["page"]) for r in rivals]},
                rationale=f"{len(rivals)} pages share impressions for this query; one clear owner should rank instead."))

        page = site.page(path)
        covered = page is not None and _covers(page.title + " " + page.h1 + " " + " ".join(page.h2s), query)
        if 4.5 <= position <= 20 and covered:
            found.append(Opportunity(
                "striking_distance", path, query=query, cluster=qual.cluster, fit=qual.fit,
                value=total * max(0.0, expected_ctr(3) - ctr) * qual.fit, evidence=evidence,
                rationale=f"Ranks at {position:.1f} for a qualified query; deepening the page can move it into the top results."))
        elif not covered and path in live_paths:
            found.append(Opportunity(
                "content_gap", path, query=query, cluster=qual.cluster, fit=qual.fit,
                value=total * expected_ctr(5) * qual.fit, evidence=evidence,
                rationale=f"Google shows {path} for this query but no page is actually about it; a dedicated page should own it."))

    for path, now in pages.items():
        if path not in live_paths:
            if now["impressions"] > 0 or now.get("sessions", 0) > 0:
                found.append(Opportunity(
                    "legacy_url", path, value=now["clicks"] + now["impressions"] * 0.01, evidence=dict(now),
                    rationale="URL no longer exists on the site but still earns impressions; redirect it to the closest live page."))
            continue
        if (now["impressions"] >= t["min_page_impressions"] and 0 < now["position"] <= 8
                and now["ctr"] < 0.5 * expected_ctr(now["position"])):
            found.append(Opportunity(
                "low_ctr", path, value=now["impressions"] * (expected_ctr(now["position"]) - now["ctr"]),
                evidence=dict(now),
                rationale=f"CTR {now['ctr']:.1%} at position {now['position']} is under half the norm; the title and description are not earning the click."))
        before = previous.get(path)
        if before and before["impressions"] >= 50 and now["impressions"] <= before["impressions"] * (1 - t["decay_drop"]):
            found.append(Opportunity(
                "decay", path, value=(before["clicks"] - now["clicks"]) or 1,
                evidence={"impressions": now["impressions"], "previous_impressions": before["impressions"]},
                rationale=f"Impressions fell from {before['impressions']:.0f} to {now['impressions']:.0f} window over window."))
        if now.get("enquiries", 0) > 0:
            found.append(Opportunity(
                "converter", path, value=10 * now["enquiries"], evidence=dict(now),
                rationale="This page produces enquiries; send it more internal links and build adjacent pages in its cluster."))
        elif now.get("sessions", 0) >= t["min_sessions_leaky"]:
            found.append(Opportunity(
                "leaky_page", path, value=now["sessions"] * 0.02, evidence=dict(now),
                rationale=f"{now['sessions']} sessions and no enquiries; the offer or call-to-action on this page is not landing."))

    found.sort(key=lambda o: o.value, reverse=True)
    return found


def _covers(page_text: str, query: str) -> bool:
    """True when the page's title and headings contain most of the query's meaningful words."""
    stop = {"a", "an", "the", "to", "for", "of", "in", "and", "or", "how", "what", "is", "do", "does", "best", "with"}
    wanted = [w for w in tokens(query) if w not in stop]
    have = set(tokens(page_text))
    if not wanted:
        return True
    hits = sum(1 for w in wanted if w in have or w.rstrip("s") in have or w + "s" in have)
    return hits / len(wanted) >= 0.6
