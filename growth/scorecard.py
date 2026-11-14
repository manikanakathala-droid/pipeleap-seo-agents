"""
The briefing. Reports outcomes, not activity.

There is no composite score. The funnel either has numbers in it or it says
why it does not.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from growth.icp import ICPModel
from growth.ledger import Ledger
from growth.measure import Measurement
from growth.plan import Plan
from growth.site import SiteModel


def funnel(site: SiteModel, measurement: Measurement) -> dict[str, Any]:
    live = {p.path for p in site.indexable_pages()}
    pages = measurement.per_page()
    totals = measurement.totals()
    search, analytics = measurement.search.ok, measurement.analytics.ok
    return {
        "indexable_pages": len(live),
        "pages_with_impressions": sum(1 for p, m in pages.items() if p in live and m["impressions"] > 0) if search else None,
        "impressions": int(totals["impressions"]) if search else None,
        "clicks": int(totals["clicks"]) if search else None,
        "sessions": int(totals["sessions"]) if analytics else None,
        "enquiries": int(totals["enquiries"]) if analytics else None,
    }


def query_mix(measurement: Measurement, icp: ICPModel) -> dict[str, Any]:
    qualified, unqualified, brand = [], 0.0, 0.0
    for row in measurement.rows:
        if not row.get("query"):
            continue
        qual = icp.qualify(row["query"])
        if qual.stage == "navigational":
            brand += row["impressions"]
        elif qual.qualified:
            qualified.append((row["impressions"], row["query"], qual.cluster, row.get("position", 0), row.get("clicks", 0)))
        else:
            unqualified += row["impressions"]
    qualified.sort(reverse=True)
    return {"qualified_impressions": sum(q[0] for q in qualified), "unqualified_impressions": unqualified,
            "brand_impressions": brand, "top_qualified": qualified[:10]}


def _cell(value: Any, previous: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(previous, (int, float)) and previous != value:
        return f"{value:,} ({value - previous:+,})"
    return f"{value:,}"


def render(*, site: SiteModel, measurement: Measurement, ledger: Ledger, plan: Plan, icp: ICPModel,
           executed: list[dict[str, Any]], closed: list[dict[str, Any]], today: date) -> tuple[str, dict[str, Any]]:
    now = funnel(site, measurement)
    before = ledger.previous_run().get("funnel", {})
    mix = query_mix(measurement, icp)
    lines = [f"# Pipeleap growth briefing — {today.isoformat()}", "", f"Site: {site.site_url} ({len(site.pages)} pages in the checkout)", ""]

    # Headline: the single most important true statement.
    if not site.pages:
        headline = "The site checkout was not found, so nothing could be measured or changed."
    elif now["enquiries"]:
        headline = f"{now['enquiries']} enquiry event(s) in the last {measurement.window_days} days."
    elif now["enquiries"] is None and now["clicks"] is None:
        headline = "Neither search nor enquiry data is reachable. The loop is running blind and has limited itself accordingly."
    elif now["enquiries"] is None:
        headline = f"{now['clicks']} organic click(s) in {measurement.window_days} days; enquiries are not being measured yet."
    elif now["clicks"] is None:
        headline = (f"No enquiries recorded in {measurement.window_days} days, and search data is unavailable "
                    f"({measurement.search.state}).")
    else:
        headline = f"{now['clicks']} organic click(s) and no enquiries in {measurement.window_days} days."
    lines += [f"**{headline}**", ""]

    lines += ["## Funnel", "", f"Last {measurement.window_days} days. Change since the previous run in brackets.", "",
              "| Stage | Value |", "|---|---|"]
    labels = {"indexable_pages": "Indexable pages on the site", "pages_with_impressions": "Pages shown in search",
              "impressions": "Search impressions", "clicks": "Organic clicks", "sessions": "Sessions (all channels)",
              "enquiries": "Enquiries (walkthrough clicks)"}
    for key, label in labels.items():
        lines.append(f"| {label} | {_cell(now[key], before.get(key))} |")
    lines += ["", "## Data sources", ""]
    for source in (measurement.search, measurement.analytics):
        lines.append(f"- **{source.name}**: {source.state}. {source.detail}")
    if not any(p.has_analytics for p in site.pages) and site.pages:
        lines.append("- The site has no analytics tag, so sessions and enquiries cannot be recorded at all.")

    if measurement.search.state == "ok":
        total = mix["qualified_impressions"] + mix["unqualified_impressions"] + mix["brand_impressions"]
        lines += ["", "## Who is finding the site", ""]
        if total:
            lines.append(f"Of {total:,.0f} impressions: {mix['qualified_impressions'] / total:.0%} from qualified buyer queries, "
                         f"{mix['brand_impressions'] / total:.0%} brand, {mix['unqualified_impressions'] / total:.0%} unqualified.")
        if mix["top_qualified"]:
            lines += ["", "| Qualified query | Cluster | Impressions | Clicks | Position |", "|---|---|---|---|---|"]
            for impressions, query, cluster, position, clicks in mix["top_qualified"]:
                lines.append(f"| {query} | {cluster} | {impressions:,.0f} | {clicks:,.0f} | {position:.1f} |")

    lines += ["", "## What the loop has learned", ""]
    if closed:
        for exp in closed:
            last = exp["checkpoints"][-1]
            lines.append(f"- **{exp['status']}**: {exp['kind']} on {exp['path']} after {last['day']} days. "
                         f"Hypothesis: {exp['hypothesis']} Result: {last['metrics']}.")
    priors = ledger.data["priors"]
    if priors:
        lines += ["", "| Cluster | Experiments | Belief it produces qualified demand |", "|---|---|---|"]
        for cluster, p in sorted(priors.items(), key=lambda kv: kv[1]["alpha"] / (kv[1]["alpha"] + kv[1]["beta"]), reverse=True):
            lines.append(f"| {cluster} | {p['experiments']} | {p['alpha'] / (p['alpha'] + p['beta']):.0%} |")
    open_count = len(ledger.open_experiments())
    if not closed and not priors:
        lines.append(f"Nothing yet. {open_count} experiment(s) are open; the first verdicts come 14 to 56 days after each change.")
    elif open_count:
        lines.append(f"\n{open_count} experiment(s) still open.")

    if plan.holds:
        lines += ["", "## Holds", ""] + [f"- {hold}" for hold in plan.holds]

    lines += ["", "## Done this run", ""]
    lines += [f"- {item['title']}: {item['result']}" for item in executed] or ["- Nothing changed."]

    manual = plan.manual()
    people = [a for a in manual if a.kind != "new_page"]
    queued = [a for a in manual if a.kind == "new_page"]
    if people:
        lines += ["", "## Needs a person", ""]
        for action in people[:12]:
            lines.append(f"- **{action.title}**. {action.why}")
    if queued:
        lines += ["", "## Content queue (not published)", "",
                  f"{len(queued)} candidate page(s) are waiting on the holds above. Highest priority first:", ""]
        for action in queued[:5]:
            lines.append(f"- “{action.payload.get('query', '')}” ({action.payload.get('cluster', '')}; {action.payload.get('source', '')})")
    lines += ["", "---", "Generated by the growth loop. Unknown means the data source was unreachable, not zero."]

    report = {"date": today.isoformat(), "headline": headline, "funnel": now,
              "sources": {"search": measurement.search.state, "analytics": measurement.analytics.state},
              "holds": plan.holds, "executed": executed,
              "manual": [{"title": a.title, "why": a.why, "kind": a.kind} for a in manual],
              "weights": plan.weights}
    return "\n".join(lines) + "\n", report
