"""Orchestrator: MEASURE -> LEARN -> PLAN -> ACT -> REPORT."""
from __future__ import annotations

import json
import logging
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any, Callable

import yaml

from growth import learn, publish, scorecard
from growth.icp import ICPModel
from growth.ledger import Ledger
from growth.measure import Measurement, collect
from growth.plan import Action, build_plan
from growth.site import SiteModel, normalize_path
from growth.write import Writer, build_brief, default_llm

MAX_BRIEFS_PER_RUN = 3


def load_growth_config(path: str | Path = "growth.yaml") -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def best_destination(path: str, site: SiteModel, icp: ICPModel, ledger: Ledger) -> str:
    """Closest live page for a URL that no longer exists."""
    cluster, _ = icp.cluster_for(path.replace("-", " ").replace("/", " "))
    if cluster:
        for candidate, meta in ledger.data["pages"].items():
            if meta.get("cluster") == cluster and site.page(candidate):
                return candidate
    return "/"


def run(*, site_dir: str | Path, state_dir: str | Path = "growth_state", growth: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None, today: date | None = None, dry_run: bool = False,
        offline: bool = False, llm: Callable[[str], str] | None | bool = False,
        measurement: Measurement | None = None, logger: logging.Logger | None = None) -> dict[str, Any]:
    logger = logger or logging.getLogger("growth")
    today = today or date.today()
    growth = deepcopy(growth if growth is not None else load_growth_config())
    config = config or {}
    state_dir = Path(state_dir)
    sources_dir = state_dir / "articles"
    ledger = Ledger(state_dir / "ledger.json")
    icp = ICPModel(growth)
    site_url = growth.get("site_url", "https://www.pipeleap.com")
    cta_hosts = tuple(growth.get("cta", {}).get("hosts", []))
    site = SiteModel.load(site_dir, site_url, cta_hosts)
    writer = Writer(default_llm() if llm is False else (llm or None), growth)

    # An experiment's clock starts when the change is live. If the site checkout does not contain it yet
    # (for example the change is waiting on a branch to be merged), restart the clock instead of judging it.
    for exp in ledger.open_experiments():
        live = site.has_sitemap if exp["kind"] == "foundation" else site.page(exp["path"]) is not None
        if site.pages and not live and not dry_run:
            exp["started_at"] = today.isoformat()
            if exp["path"] in ledger.data["pages"] and exp["kind"] == "new_page":
                ledger.data["pages"][exp["path"]]["published_at"] = today.isoformat()

    # ── MEASURE ────────────────────────────────────────────────────────────
    measurement = measurement or collect(config, growth, state_dir, today, logger, offline=offline)
    logger.info("search=%s analytics=%s", measurement.search.state, measurement.analytics.state)

    # ── LEARN ──────────────────────────────────────────────────────────────
    learn.observe(ledger, measurement)
    judged = learn.evaluate_experiments(ledger, measurement, today, growth.get("thresholds"))
    closed = [e for e in judged if e["status"] != "open"]
    learn.update_priors(ledger)
    opportunities = learn.find_opportunities(measurement, site, icp, growth.get("thresholds"))
    weights = learn.cluster_weights(ledger, list(growth.get("clusters", {})), seed=today.isoformat())

    # ── PLAN ───────────────────────────────────────────────────────────────
    growth["redirects"] = _merged_redirects(growth, ledger)
    plan = build_plan(site=site, ledger=ledger, measurement=measurement, icp=icp, opportunities=opportunities,
                      foundation_gaps=publish.foundation_gaps(site, growth), weights=weights, growth=growth,
                      today=today, writer_available=writer.available)

    # ── ACT ────────────────────────────────────────────────────────────────
    executed: list[dict[str, Any]] = []
    changed_files: list[str] = []
    if site.pages and not dry_run:
        baseline_pages = measurement.per_page()
        facts = site.facts(exclude=growth.get("site", {}).get("facts_exclude", []))
        existing_texts = {p.path: p.text for p in site.pages}
        briefs_written = 0
        for action in plan.actions:
            if action.kind == "redirect" and action.auto:
                destination = best_destination(action.path, site, icp, ledger)
                ledger.data.setdefault("redirects", {})[action.path] = destination
                executed.append({"title": action.title, "result": f"301 to {destination}"})
            elif action.kind in ("new_page", "refresh"):
                result = _write_page(action, writer=writer, site=site, growth=growth, ledger=ledger, icp=icp,
                                     measurement=measurement, facts=facts, existing_texts=existing_texts,
                                     sources_dir=sources_dir, state_dir=state_dir, today=today,
                                     baseline=baseline_pages.get(action.path, {}),
                                     allow_brief=briefs_written < MAX_BRIEFS_PER_RUN)
                if result:
                    briefs_written += result.pop("brief", 0)
                    executed.append(result)
        growth["redirects"] = _merged_redirects(growth, ledger)
        try:
            changed_files += publish.sync_articles(site, growth, ledger, sources_dir, today)
        except publish.PublishError as exc:
            executed.append({"title": "Render articles", "result": f"failed: {exc}"})
        site = SiteModel.load(site_dir, site_url, cta_hosts)
        foundation_files = publish.apply_foundation(site, growth, ledger, today)
        changed_files += foundation_files
        if foundation_files:
            executed.append({"title": "Site foundation", "result": "updated " + ", ".join(sorted(set(foundation_files)))})
            if not any(e["kind"] == "foundation" for e in ledger.data["experiments"]):
                ledger.open_experiment(
                    kind="foundation", path="/", cluster="", today=today, baseline=baseline_pages.get("/", {}),
                    hypothesis="With a sitemap, canonicals, structured data and redirects in place, the new site's "
                               "pages get indexed and the homepage starts earning impressions for its own positioning.")
        site = SiteModel.load(site_dir, site_url, cta_hosts)

    # ── REPORT ─────────────────────────────────────────────────────────────
    briefing, report = scorecard.render(site=site, measurement=measurement, ledger=ledger, plan=plan, icp=icp,
                                        executed=executed, closed=closed, today=today)
    changed_urls = sorted({site_url + normalize_path(f) for f in changed_files if f.endswith(".html")})
    report.update({"changed_files": sorted(set(changed_files)), "changed_urls": changed_urls,
                   "opportunities": [vars(o) for o in opportunities[:25]],
                   "queue": [{"kind": a.kind, "title": a.title, "auto": a.auto, "priority": round(a.priority, 1)}
                             for a in plan.actions[:25]]})
    if not dry_run:
        ledger.record_run({"funnel": report["funnel"], "sources": report["sources"],
                           "executed": len(executed), "changed_files": len(set(changed_files))})
        ledger.save()
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "briefing.md").write_text(briefing, encoding="utf-8")
        (state_dir / "report.json").write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    report["briefing"] = briefing
    return report


def _merged_redirects(growth: dict[str, Any], ledger: Ledger) -> list[dict[str, str]]:
    merged = {r["source"]: r["destination"] for r in growth.get("redirects", [])}
    for source, destination in ledger.data.get("redirects", {}).items():
        merged.setdefault(source, destination)
    return [{"source": s, "destination": d} for s, d in merged.items()]


def _write_page(action: Action, *, writer: Writer, site: SiteModel, growth: dict[str, Any], ledger: Ledger,
                icp: ICPModel, measurement: Measurement, facts: str, existing_texts: dict[str, str],
                sources_dir: Path, state_dir: Path, today: date, baseline: dict[str, float],
                allow_brief: bool) -> dict[str, Any] | None:
    query = action.payload.get("query") or ledger.data["pages"].get(action.path, {}).get("target_query", "")
    cluster = action.payload.get("cluster", "")
    if not query:
        return None
    related = [r["query"] for r in sorted(measurement.rows, key=lambda r: r["impressions"], reverse=True)
               if r.get("query") and r["query"] != query and icp.qualify(r["query"]).cluster == cluster]
    section = growth.get("publish", {}).get("section", "resources")
    targets = [(t["path"], t["label"]) for t in growth.get("publish", {}).get("link_targets", [])]
    targets += [(p, m.get("title", p)) for p, m in ledger.data["pages"].items()
                if m.get("kind") == "article" and p != action.path and m.get("cluster") == cluster]
    brief = build_brief(query=query, cluster=cluster, cluster_spec=growth.get("clusters", {}).get(cluster, {}),
                        evidence=action.payload.get("evidence", {}), related_queries=related,
                        link_targets=targets, site_facts=facts, growth=growth)
    slug = action.path.rsplit("/", 1)[-1]

    if not action.auto:
        if not allow_brief or action.kind != "new_page":
            return None
        briefs = state_dir / "briefs"
        briefs.mkdir(parents=True, exist_ok=True)
        (briefs / f"{slug}.md").write_text(brief, encoding="utf-8")
        return {"title": action.title, "result": f"not published; brief saved to growth_state/briefs/{slug}.md", "brief": 1}

    others = {p: t for p, t in existing_texts.items() if p != action.path}
    try:
        draft = writer.draft(brief, query=query, cluster=cluster, site_facts=facts, existing_texts=others)
    except Exception as exc:  # provider outage or quota: report it, publish nothing
        return {"title": action.title, "result": f"not published; the model call failed ({type(exc).__name__}: {str(exc)[:120]})"}
    if draft is None:
        return None
    if not draft.report.passed:
        rejected = state_dir / "rejected"
        rejected.mkdir(parents=True, exist_ok=True)
        (rejected / f"{slug}.md").write_text(
            f"Rejected {today}: {draft.report.summary()}\n\nTITLE: {draft.title}\nDESCRIPTION: {draft.description}\n---\n{draft.markdown}\n",
            encoding="utf-8")
        return {"title": action.title,
                "result": f"draft rejected by the quality gate after {draft.attempts} attempt(s): {draft.report.summary()}"}
    publish.save_source(sources_dir, path=action.path, title=draft.title, description=draft.description,
                        query=query, cluster=cluster, markdown_body=draft.markdown)
    ledger.register_page(action.path, kind="article", cluster=cluster, target_query=query, today=today)
    existing_texts[action.path] = draft.markdown
    hypothesis = (f"A dedicated page earns clicks from “{query}” and adjacent {cluster} searches."
                  if action.kind == "new_page" else f"Deepening the page moves “{query}” into the top results.")
    ledger.open_experiment(kind=action.kind, path=action.path, cluster=cluster, hypothesis=hypothesis, today=today,
                           baseline=baseline, detail={"query": query, "words": draft.report.word_count})
    return {"title": action.title, "result": f"published ({draft.report.word_count} words, gate passed on attempt {draft.attempts})"}
