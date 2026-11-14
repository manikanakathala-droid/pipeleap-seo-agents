"""Tests for the growth loop. No network, no credentials."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml

from growth import learn, publish, quality
from growth.icp import ICPModel
from growth.ledger import Ledger
from growth.measure import Measurement, SourceStatus
from growth.plan import build_plan, new_page_budget
from growth.run import run
from growth.site import SiteModel, normalize_path

ROOT = Path(__file__).resolve().parent.parent
TODAY = date(2026, 11, 14)
SITE_URL = "https://www.pipeleap.com"

CHROME = """<header id="site-nav" class="nav"><a href="/#opening"><img src="favicon.svg" alt=""></a>
<a href="/pilot" aria-current="page">Pilot</a><a class="m-btn" href="https://app.apollo.io/#/meet/x">Book a walkthrough</a></header>"""
FOOTER = '<footer id="site-footer"><a href="mailto:info@pipeleap.com">info@pipeleap.com</a></footer>'


def page(title: str, description: str, body: str, extra_style: str = "") -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<meta name="description" content="{description}">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<style data-8b-part="tokens">:root{{--color-1:#fff}}</style>{extra_style}
</head><body>{CHROME}<main>{body}</main>{FOOTER}
<script data-8b-part="section-script:site-nav">/*nav*/</script></body></html>"""


@pytest.fixture
def growth() -> dict:
    return yaml.safe_load((ROOT / "growth.yaml").read_text(encoding="utf-8"))


@pytest.fixture
def site_dir(tmp_path: Path) -> Path:
    root = tmp_path / "site"
    root.mkdir()
    (root / "index.html").write_text(page(
        "Pipeleap: Less admin. More selling time.",
        "Pipeleap is a sales productivity and sales stack optimization platform.",
        "<section id='opening'><h1>Pipeleap</h1><p>Less admin. More selling time.</p></section>"
        "<section id='faq'><h2>Questions</h2><details><summary>Does Pipeleap replace our CRM?</summary>"
        "<p>No. Your CRM stays the source of truth.</p></details></section>"), encoding="utf-8")
    (root / "pilot.html").write_text(page(
        "Founding pilot · Pipeleap", "A free 30-day founding pilot.",
        "<section><h1>Build Pipeleap with us.</h1><p>Thirty days.</p></section>",
        '<style data-8b-part="pilot">.hero{color:red}</style>'), encoding="utf-8")
    (root / "vercel.json").write_text('{"cleanUrls": true}', encoding="utf-8")
    return root


def measurement(rows=None, previous=None, sessions=None, enquiries=None, search="ok", analytics="ok") -> Measurement:
    return Measurement(day=TODAY, search=SourceStatus("search", search), analytics=SourceStatus("analytics", analytics),
                       rows=rows or [], previous_rows=previous or [], sessions=sessions or {}, enquiries=enquiries or {})


def row(query, page_path, impressions, clicks=0, position=10.0):
    return {"query": query, "page": SITE_URL + page_path, "impressions": impressions, "clicks": clicks, "position": position}


GOOD_BODY = "\n\n".join(
    [f"## Section {i}\n\n" + " ".join(f"Reps move between the CRM and prospecting tool number {i} point {j} every hour."
                                      for j in range(60)) for i in range(4)]
    + ["See the [overview](/) and the [founding pilot](/pilot)."])


# ── site model ─────────────────────────────────────────────────────────────
def test_normalize_path():
    assert normalize_path("https://www.pipeleap.com/") == "/"
    assert normalize_path("index.html") == "/"
    assert normalize_path("/resources/a-b.html") == "/resources/a-b"
    assert normalize_path("https://www.pipeleap.com/pilot?x=1#y") == "/pilot"


def test_site_model_reads_pages_and_faq(site_dir):
    site = SiteModel.load(site_dir, SITE_URL, ("app.apollo.io",))
    assert {p.path for p in site.pages} == {"/", "/pilot"}
    home = site.page("/")
    assert home.h1 == "Pipeleap" and home.cta_links == 1 and not home.canonical and not home.has_analytics
    assert site.faq() == [("Does Pipeleap replace our CRM?", "No. Your CRM stays the source of truth.")]
    assert "sales stack optimization" in site.facts()


# ── ICP ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("query,qualified,cluster", [
    ("how to reduce sales admin work for reps", True, "selling_time"),
    ("sales tech stack consolidation", True, "stack_sprawl"),
    ("how to get sales reps to update the crm", True, "crm_upkeep"),
    ("sales operations manager salary", False, ""),
    ("revenue operations jobs", False, ""),
    ("crm", False, ""),
    ("best pizza near me", False, ""),
])
def test_icp_qualification(growth, query, qualified, cluster):
    result = ICPModel(growth).qualify(query)
    assert result.qualified is qualified, result.reasons
    if qualified:
        assert result.cluster == cluster


def test_brand_queries_are_navigational(growth):
    assert ICPModel(growth).qualify("pipeleap pricing").stage == "navigational"


def test_every_backlog_item_qualifies(growth):
    icp = ICPModel(growth)
    for item in growth["backlog"]:
        result = icp.qualify(item["query"])
        assert result.qualified and result.cluster == item["cluster"], (item, result)


# ── learning ───────────────────────────────────────────────────────────────
def test_no_judgement_without_search_data(tmp_path):
    ledger = Ledger(tmp_path / "l.json")
    ledger.open_experiment(kind="new_page", path="/resources/x", cluster="selling_time", hypothesis="h",
                           today=TODAY - timedelta(days=60))
    assert learn.evaluate_experiments(ledger, measurement(search="unavailable"), TODAY) == []
    assert ledger.open_experiments()


def test_new_page_wins_on_clicks_and_updates_prior(tmp_path):
    ledger = Ledger(tmp_path / "l.json")
    ledger.open_experiment(kind="new_page", path="/resources/x", cluster="selling_time", hypothesis="h",
                           today=TODAY - timedelta(days=30))
    m = measurement(rows=[row("reduce sales admin work", "/resources/x", 300, clicks=12, position=6)])
    learn.evaluate_experiments(ledger, m, TODAY)
    exp = ledger.data["experiments"][0]
    assert exp["status"] == "won" and exp["checkpoints"][-1]["day"] == 28
    learn.update_priors(ledger)
    prior = ledger.data["priors"]["selling_time"]
    assert prior["alpha"] > prior["beta"] and prior["experiments"] == 1
    learn.update_priors(ledger)  # idempotent: a verdict is credited once
    assert ledger.data["priors"]["selling_time"]["experiments"] == 1


def test_new_page_lost_when_never_shown(tmp_path):
    ledger = Ledger(tmp_path / "l.json")
    ledger.open_experiment(kind="new_page", path="/resources/x", cluster="stack_roi", hypothesis="h",
                           today=TODAY - timedelta(days=57))
    learn.evaluate_experiments(ledger, measurement(), TODAY)
    assert ledger.data["experiments"][0]["status"] == "lost"
    learn.update_priors(ledger)
    prior = ledger.data["priors"]["stack_roi"]
    assert prior["beta"] > prior["alpha"]


def test_enquiry_beats_everything(tmp_path):
    ledger = Ledger(tmp_path / "l.json")
    ledger.open_experiment(kind="refresh", path="/resources/x", cluster="crm_upkeep", hypothesis="h",
                           today=TODAY - timedelta(days=15), baseline={"clicks": 5, "enquiries": 0})
    learn.evaluate_experiments(ledger, measurement(enquiries={"/resources/x": 1}), TODAY)
    assert ledger.data["experiments"][0]["status"] == "won"


def test_cluster_weights_favour_proven_clusters(tmp_path):
    ledger = Ledger(tmp_path / "l.json")
    ledger.data["priors"] = {"good": {"alpha": 30.0, "beta": 2.0}, "bad": {"alpha": 2.0, "beta": 30.0}}
    wins = sum(1 for day in range(200)
               if (w := learn.cluster_weights(ledger, ["good", "bad", "new"], seed=str(day)))["good"] > w["bad"])
    assert wins > 190
    assert learn.cluster_weights(ledger, ["good"], "s") == learn.cluster_weights(ledger, ["good"], "s")


def test_opportunities(site_dir, growth):
    site = SiteModel.load(site_dir, SITE_URL)
    m = measurement(
        rows=[row("how to reduce sales admin work", "/", 120, clicks=1, position=14),   # homepage is not about this
              row("pipeleap", "/", 500, clicks=3, position=1.2),                        # brand, low CTR at top
              row("sales operations salary", "/", 400, position=3),                     # unqualified: ignored
              row("automate crm data entry", "/blog/old-post", 80, clicks=4, position=9)],
        previous=[row("pipeleap", "/pilot", 200, clicks=20, position=2)],
        sessions={"/pilot": 90})
    found = learn.find_opportunities(m, site, ICPModel(growth))
    kinds = {(o.kind, o.path) for o in found}
    assert ("content_gap", "/") in kinds
    assert ("low_ctr", "/") in kinds
    assert ("legacy_url", "/blog/old-post") in kinds
    assert ("leaky_page", "/pilot") in kinds
    assert not any("salary" in o.query for o in found)


# ── planning guards ────────────────────────────────────────────────────────
def _published(ledger, n, days_ago):
    for i in range(n):
        ledger.register_page(f"/resources/p{i}", kind="article", cluster="selling_time", target_query=f"q{i}",
                             today=TODAY - timedelta(days=days_ago))


def test_budget_capped_without_search_data(tmp_path, growth):
    ledger = Ledger(tmp_path / "l.json")
    _published(ledger, 3, 30)
    budget, holds = new_page_budget(ledger, measurement(search="unavailable"), TODAY, growth["guards"])
    assert budget == 0 and "No search data" in holds[0]


def test_budget_paused_when_pages_not_indexed(tmp_path, growth):
    ledger = Ledger(tmp_path / "l.json")
    _published(ledger, 4, 30)
    ledger.record_observations(TODAY, {"/resources/p0": {"impressions": 5}})
    budget, holds = new_page_budget(ledger, measurement(), TODAY, growth["guards"])
    assert budget == 0 and "indexing" in holds[0]


def test_weekly_limit(tmp_path, growth):
    ledger = Ledger(tmp_path / "l.json")
    _published(ledger, 2, 2)
    assert new_page_budget(ledger, measurement(), TODAY, growth["guards"])[0] == 0
    fresh = Ledger(tmp_path / "f.json")
    assert new_page_budget(fresh, measurement(), TODAY, growth["guards"])[0] == 2


def test_plan_prefers_evidence_over_backlog(site_dir, growth, tmp_path):
    site, icp, ledger = SiteModel.load(site_dir, SITE_URL), ICPModel(growth), Ledger(tmp_path / "l.json")
    m = measurement(rows=[row("sales tool adoption problems", "/", 900, position=12)])
    opps = learn.find_opportunities(m, site, icp)
    plan = build_plan(site=site, ledger=ledger, measurement=m, icp=icp, opportunities=opps, foundation_gaps=[],
                      weights={c: 0.5 for c in growth["clusters"]}, growth=growth, today=TODAY, writer_available=True)
    pages = [a for a in plan.actions if a.kind == "new_page"]
    assert pages[0].payload["query"] == "sales tool adoption problems" and pages[0].auto
    assert sum(1 for a in pages if a.auto) == growth["guards"]["max_new_pages_per_week"]


# ── quality gate ───────────────────────────────────────────────────────────
def _check(body, growth, **kw):
    args = dict(title="How to reduce sales admin work for reps", description="x" * 130,
                query="reduce sales admin work", site_facts="", existing_texts={}, rules=growth["quality"],
                cta_url=growth["cta"]["url"])
    args.update(kw)
    return quality.check(body, **args)


def test_gate_passes_clean_draft(growth):
    report = _check(GOOD_BODY, growth)
    assert report.passed, report.failures


def test_gate_rejects_invented_statistics(growth):
    report = _check(GOOD_BODY + "\n\nReps waste 65% of their week and it costs $2,500 a month.", growth)
    assert not report.passed and "65%" in report.summary()


def test_gate_allows_cited_statistics_and_site_facts(growth):
    cited = GOOD_BODY + "\n\nOne study found 28% of time is spent selling ([source](https://example.org/report))."
    assert _check(cited, growth).passed
    assert _check(GOOD_BODY + "\n\nThe pilot runs for 30 days.", growth).passed
    stated = GOOD_BODY + "\n\nSetup takes 45 minutes."
    assert not _check(stated, growth).passed
    assert _check(stated, growth, site_facts="Setup takes 45 minutes.").passed


def test_gate_rejects_thin_duplicate_banned_and_unlinked(growth):
    assert "too short" in _check("## A\n\nshort", growth).summary()
    assert "overlap" in _check(GOOD_BODY, growth, existing_texts={"/resources/old": GOOD_BODY}).summary()
    assert "banned phrase" in _check(GOOD_BODY + "\n\nThis content was produced with AI assistance.", growth).summary()
    assert "internal link" in _check(GOOD_BODY.replace("](/", "](https://x.com/"), growth).summary()
    assert "title does not reflect" in _check(GOOD_BODY, growth, title="Ten things about marketing today okay").summary()


# ── publishing ─────────────────────────────────────────────────────────────
def test_foundation_is_idempotent_and_preserves_hand_edits(site_dir, growth, tmp_path):
    growth["analytics"]["ga4_measurement_id"] = ""
    ledger = Ledger(tmp_path / "l.json")
    site = SiteModel.load(site_dir, SITE_URL)
    gaps = {g["title"] for g in publish.foundation_gaps(site, growth)}
    assert {"Add robots.txt", "Add sitemap.xml", "Install analytics and enquiry tracking"} <= gaps

    first = publish.apply_foundation(site, growth, ledger, TODAY)
    assert {"index.html", "pilot.html", "robots.txt", "sitemap.xml", "vercel.json"} <= set(first)
    assert publish.apply_foundation(SiteModel.load(site_dir, SITE_URL), growth, ledger, TODAY + timedelta(days=1)) == []

    home = (site_dir / "index.html").read_text()
    assert '<link rel="canonical" href="https://www.pipeleap.com/">' in home
    assert home.count(publish.HEAD_OPEN) == 1 and "FAQPage" in home and "Organization" in home
    assert "googletagmanager" not in home  # no measurement id configured: nothing is injected
    assert '<link rel="canonical" href="https://www.pipeleap.com/pilot">' in (site_dir / "pilot.html").read_text()

    # The owner edits the page; the next run keeps the edit and still manages only its own block.
    (site_dir / "index.html").write_text(home.replace("<h1>Pipeleap</h1>", "<h1>Less admin</h1>"))
    publish.apply_foundation(SiteModel.load(site_dir, SITE_URL), growth, ledger, TODAY + timedelta(days=2))
    edited = (site_dir / "index.html").read_text()
    assert "<h1>Less admin</h1>" in edited and edited.count(publish.HEAD_OPEN) == 1

    sitemap = (site_dir / "sitemap.xml").read_text()
    assert "<loc>https://www.pipeleap.com/</loc>" in sitemap and "<loc>https://www.pipeleap.com/pilot</loc>" in sitemap
    assert f"<lastmod>{TODAY + timedelta(days=2)}</lastmod>" in sitemap and f"<lastmod>{TODAY}</lastmod>" in sitemap
    config = json.loads((site_dir / "vercel.json").read_text())
    assert config["cleanUrls"] is True
    assert {"source": "/pricing", "destination": "/pilot", "permanent": True} in config["redirects"]
    assert "Sitemap: https://www.pipeleap.com/sitemap.xml" in (site_dir / "robots.txt").read_text()


def test_tracking_installed_only_when_configured(site_dir, growth, tmp_path):
    growth["analytics"]["ga4_measurement_id"] = "G-TEST123456"
    publish.apply_foundation(SiteModel.load(site_dir, SITE_URL), growth, Ledger(tmp_path / "l.json"), TODAY)
    home = (site_dir / "index.html").read_text()
    assert "gtag/js?id=G-TEST123456" in home and "book_walkthrough" in home and "app.apollo.io" in home
    assert SiteModel.load(site_dir, SITE_URL).page("/").has_analytics


def test_existing_robots_is_not_overwritten(site_dir, growth, tmp_path):
    (site_dir / "robots.txt").write_text("User-agent: *\nDisallow: /private\n")
    publish.apply_foundation(SiteModel.load(site_dir, SITE_URL), growth, Ledger(tmp_path / "l.json"), TODAY)
    assert "Disallow: /private" in (site_dir / "robots.txt").read_text()


def test_articles_render_in_site_chrome(site_dir, growth, tmp_path):
    ledger, sources = Ledger(tmp_path / "l.json"), tmp_path / "articles"
    publish.save_source(sources, path="/resources/reduce-sales-admin", title="How to reduce sales admin work",
                        description="d" * 120, query="reduce sales admin work", cluster="selling_time",
                        markdown_body=GOOD_BODY)
    site = SiteModel.load(site_dir, SITE_URL)
    changed = publish.sync_articles(site, growth, ledger, sources, TODAY)
    assert set(changed) == {"resources/reduce-sales-admin.html", "resources.html"}
    article = (site_dir / "resources/reduce-sales-admin.html").read_text()
    assert 'id="site-nav"' in article and 'id="site-footer"' in article
    assert 'src="/favicon.svg"' in article and "aria-current" not in article
    assert 'data-8b-part="tokens"' in article and 'data-8b-part="pilot"' not in article
    assert '"@type":"Article"' in article and growth["cta"]["url"] in article
    assert "<h2>Section 0</h2>" in article and article.count("<h1") == 1
    assert publish.sync_articles(SiteModel.load(site_dir, SITE_URL), growth, ledger, sources, TODAY) == []

    reloaded = SiteModel.load(site_dir, SITE_URL)
    assert reloaded.page("/resources/reduce-sales-admin").managed
    titles = {g["title"] for g in publish.foundation_gaps(reloaded, growth)}
    assert "Link /resources from the site navigation or footer" in titles


# ── end to end ─────────────────────────────────────────────────────────────
def fake_llm(prompt: str) -> str:
    import re
    query = re.search(r'They searched for: "([^"]+)"', prompt).group(1)
    tag = "v" + str(abs(hash(query)) % 9973)
    body = GOOD_BODY.replace("Section", "Step")
    for word in ("Reps", "between", "CRM", "prospecting", "number", "every"):
        body = body.replace(word, f"{word} {tag}")
    return f"TITLE: {query.capitalize()}: a guide\nDESCRIPTION: " + "A practical guide. " * 7 + "\n---\n" + body


def test_full_loop_publishes_measures_and_learns(site_dir, growth, tmp_path):
    state = tmp_path / "state"
    first = run(site_dir=site_dir, state_dir=state, growth=growth, today=TODAY, llm=fake_llm,
                measurement=measurement(search="unavailable", analytics="unavailable"))
    published = [e for e in first["executed"] if e["result"].startswith("published")]
    assert len(published) == 2                                   # weekly limit, not the whole backlog
    assert first["funnel"]["clicks"] is None                      # unknown is not zero
    assert (state / "briefing.md").exists() and (site_dir / "sitemap.xml").exists()
    ledger = Ledger(state / "ledger.json")
    article_paths = [p for p, m in ledger.data["pages"].items() if m["kind"] == "article"]
    assert len(article_paths) == 2 and len(ledger.open_experiments()) == 3   # two pages + foundation
    assert all(f"<loc>{SITE_URL}{p}</loc>" in (site_dir / "sitemap.xml").read_text() for p in article_paths)

    # 30 days later one page has traction, the other never surfaced.
    later = TODAY + timedelta(days=30)
    winner, loser = article_paths
    second = run(site_dir=site_dir, state_dir=state, growth=growth, today=later, llm=fake_llm,
                 measurement=Measurement(day=later, search=SourceStatus("search", "ok"),
                                         analytics=SourceStatus("analytics", "ok"),
                                         rows=[row("sales admin work for reps", winner, 400, clicks=15, position=5)],
                                         sessions={winner: 20}, enquiries={winner: 1}))
    ledger = Ledger(state / "ledger.json")
    first_bets = {e["path"]: e for e in ledger.data["experiments"] if e["kind"] == "new_page" and e["started_at"] == TODAY.isoformat()}
    assert first_bets[winner]["status"] == "won" and first_bets[loser]["status"] == "open"
    assert ledger.data["priors"][ledger.data["pages"][winner]["cluster"]]["alpha"] > 1.5
    assert second["funnel"]["enquiries"] == 1 and "1 enquiry event" in second["headline"]
    assert "won" in second["briefing"]


def test_loop_without_llm_writes_briefs_not_pages(site_dir, growth, tmp_path):
    state = tmp_path / "state"
    report = run(site_dir=site_dir, state_dir=state, growth=growth, today=TODAY, llm=None,
                 measurement=measurement(search="unavailable", analytics="unavailable"))
    assert not (site_dir / "resources.html").exists()
    assert len(list((state / "briefs").glob("*.md"))) == 3
    assert any("No LLM credentials" in h for h in report["holds"])


def test_rejected_drafts_are_not_published(site_dir, growth, tmp_path):
    state = tmp_path / "state"
    bad = lambda prompt: "TITLE: How to reduce sales admin work for reps\nDESCRIPTION: short\n---\n## A\n\n90% of reps agree."
    report = run(site_dir=site_dir, state_dir=state, growth=growth, today=TODAY, llm=bad,
                 measurement=measurement(search="unavailable", analytics="unavailable"))
    assert not (site_dir / "resources.html").exists()
    assert any("rejected by the quality gate" in e["result"] for e in report["executed"])
    assert list((state / "rejected").glob("*.md"))


def test_dry_run_changes_nothing(site_dir, growth, tmp_path):
    before = {f.name: f.read_text() for f in site_dir.iterdir()}
    run(site_dir=site_dir, state_dir=tmp_path / "state", growth=growth, today=TODAY, llm=fake_llm, dry_run=True,
        measurement=measurement())
    assert {f.name: f.read_text() for f in site_dir.iterdir()} == before
    assert not (tmp_path / "state").exists()


def test_headline_when_only_search_is_missing(site_dir, growth, tmp_path):
    report = run(site_dir=site_dir, state_dir=tmp_path / "state", growth=growth, today=TODAY, llm=None, dry_run=True,
                 measurement=measurement(search="error", analytics="empty"))
    assert report["headline"].startswith("No enquiries recorded") and "Unknown" not in report["headline"]


def test_termly_banner_is_first_script_and_reaches_articles(site_dir, growth, tmp_path):
    uuid = "0f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0"
    growth["consent"] = {"termly_website_uuid": uuid, "auto_block": True}
    growth["analytics"]["ga4_measurement_id"] = "G-TEST123456"
    ledger = Ledger(tmp_path / "l.json")
    publish.apply_foundation(SiteModel.load(site_dir, SITE_URL), growth, ledger, TODAY)
    home = (site_dir / "index.html").read_text()
    termly = home.find(f"app.termly.io/resource-blocker/{uuid}?autoBlock=on")
    assert 0 < termly < home.find("<script") + 200 and termly < home.find("googletagmanager")
    assert home.count(publish.CONSENT_OPEN) == 1
    publish.apply_foundation(SiteModel.load(site_dir, SITE_URL), growth, ledger, TODAY)
    assert (site_dir / "index.html").read_text() == home

    sources = tmp_path / "articles"
    publish.save_source(sources, path="/resources/x", title="How to reduce sales admin work", description="d" * 120,
                        query="q", cluster="selling_time", markdown_body=GOOD_BODY)
    publish.sync_articles(SiteModel.load(site_dir, SITE_URL), growth, ledger, sources, TODAY)
    article = (site_dir / "resources/x.html").read_text()
    assert article.find("app.termly.io") < article.find("googletagmanager")


def test_no_banner_and_a_reminder_without_termly_id(site_dir, growth, tmp_path):
    growth["consent"] = {"termly_website_uuid": ""}
    growth["analytics"]["ga4_measurement_id"] = "G-TEST123456"
    site = SiteModel.load(site_dir, SITE_URL)
    assert "Add a cookie consent banner" in {g["title"] for g in publish.foundation_gaps(site, growth)}
    publish.apply_foundation(site, growth, Ledger(tmp_path / "l.json"), TODAY)
    assert "termly" not in (site_dir / "index.html").read_text()


def test_facts_put_homepage_first_and_skip_legal_pages(site_dir):
    (site_dir / "cookie-policy.html").write_text(page("Cookie Policy", "How cookies are used.",
                                                      "<h1>Cookie Policy</h1><p>Cookies are small data files.</p>"))
    site = SiteModel.load(site_dir, SITE_URL)
    facts = site.facts(exclude=["/cookie-policy"])
    assert facts.startswith("[/]") and "Cookies are small data files" not in facts
    assert "Cookies are small data files" in site.facts()
