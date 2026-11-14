"""
Write to the static site checkout.

Two responsibilities:
  1. Foundation: robots.txt, sitemap.xml, canonical tags, structured data, enquiry
     tracking, IndexNow key and redirects. Applied idempotently inside marked
     blocks, so hand-edited pages can keep changing around them.
  2. Articles: render approved drafts into the site's own header, footer and
     styles, plus an index page that links to them.

The loop never edits copy on hand-authored pages.
"""
from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from growth.ledger import Ledger
from growth.site import SiteModel, normalize_path

GENERATOR = "pipeleap-growth-loop"
HEAD_OPEN, HEAD_CLOSE = "<!-- growth:seo -->", "<!-- /growth:seo -->"
BODY_OPEN, BODY_CLOSE = "<!-- growth:track -->", "<!-- /growth:track -->"
CONSENT_OPEN, CONSENT_CLOSE = "<!-- growth:consent -->", "<!-- /growth:consent -->"
ROBOTS_MARK = f"# managed by {GENERATOR}"


class PublishError(RuntimeError):
    pass


def _esc(value: str) -> str:
    return html.escape(value, quote=True)


def _url(site_url: str, path: str) -> str:
    return site_url.rstrip("/") + ("/" if path == "/" else path)


def _jsonld(data: dict[str, Any]) -> str:
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "</script>"


def _replace_block(source: str, open_mark: str, close_mark: str, block: str, before: str) -> str:
    """Insert or replace a marked block immediately before the first `before` tag."""
    wrapped = f"{open_mark}\n{block}\n{close_mark}\n" if block else ""
    pattern = re.compile(re.escape(open_mark) + r".*?" + re.escape(close_mark) + r"\n?", re.S)
    if pattern.search(source):
        return pattern.sub(lambda _: wrapped, source, count=1)
    index = source.lower().find(before)
    if index < 0 or not wrapped:
        return source
    return source[:index] + wrapped + source[index:]


def _replace_head_start_block(source: str, open_mark: str, close_mark: str, block: str) -> str:
    """Insert or replace a marked block at the very start of <head> (after the charset meta, if any)."""
    wrapped = f"{open_mark}\n{block}\n{close_mark}\n" if block else ""
    pattern = re.compile(re.escape(open_mark) + r".*?" + re.escape(close_mark) + r"\n?", re.S)
    if pattern.search(source):
        return pattern.sub(lambda _: wrapped, source, count=1)
    if not wrapped:
        return source
    match = re.search(r"<meta\s+charset=[^>]*>\s*\n?", source, re.I) or re.search(r"<head\b[^>]*>\s*\n?", source, re.I)
    if not match:
        return source
    return source[:match.end()] + wrapped + source[match.end():]


def consent_block(growth: dict[str, Any]) -> str:
    """Termly consent banner. Must be the first script on the page so it can block tags until consent."""
    uuid = str(growth.get("consent", {}).get("termly_website_uuid", "") or "").strip()
    if not re.fullmatch(r"[0-9a-fA-F-]{32,40}", uuid):
        return ""
    auto_block = "on" if growth.get("consent", {}).get("auto_block", True) else "off"
    return (f'<script type="text/javascript" src="https://app.termly.io/resource-blocker/{uuid}'
            f'?autoBlock={auto_block}"></script>')


# ── foundation ─────────────────────────────────────────────────────────────
def organization(growth: dict[str, Any], site_url: str) -> dict[str, Any]:
    org = growth.get("organization", {})
    data: dict[str, Any] = {"@type": "Organization", "@id": site_url + "/#organization",
                            "name": growth.get("brand", "Pipeleap"), "url": site_url + "/"}
    for key in ("logo", "email", "description"):
        if org.get(key):
            data[key] = org[key] if key != "logo" else _url(site_url, org[key])
    if org.get("same_as"):
        data["sameAs"] = org["same_as"]
    return data


def head_block(page_path: str, source: str, site: SiteModel, growth: dict[str, Any]) -> str:
    site_url = site.site_url
    url = _url(site_url, page_path)
    outside = re.sub(re.escape(HEAD_OPEN) + r".*?" + re.escape(HEAD_CLOSE), "", source, flags=re.S)
    lines = []
    if not re.search(r'<link[^>]+rel="canonical"', outside, re.I):
        lines.append(f'<link rel="canonical" href="{_esc(url)}">')
    if not re.search(r'property="og:url"', outside, re.I):
        lines.append(f'<meta property="og:url" content="{_esc(url)}">')
    if not re.search(r'property="og:site_name"', outside, re.I):
        lines.append(f'<meta property="og:site_name" content="{_esc(growth.get("brand", "Pipeleap"))}">')
    image = growth.get("organization", {}).get("social_image", "")
    if image and (site.root / image.lstrip("/")).exists() and not re.search(r'property="og:image"', outside, re.I):
        lines.append(f'<meta property="og:image" content="{_esc(_url(site_url, image))}">')
        lines.append(f'<meta name="twitter:image" content="{_esc(_url(site_url, image))}">')

    graph: list[dict[str, Any]] = []
    if page_path == "/":
        graph.append(organization(growth, site_url))
        graph.append({"@type": "WebSite", "@id": site_url + "/#website", "url": site_url + "/",
                      "name": growth.get("brand", "Pipeleap"), "publisher": {"@id": site_url + "/#organization"}})
        description = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', source, re.I)
        graph.append({"@type": "SoftwareApplication", "name": growth.get("brand", "Pipeleap"),
                      "applicationCategory": "BusinessApplication", "operatingSystem": "Web",
                      "url": site_url + "/", "description": html.unescape(description.group(1)) if description else "",
                      "publisher": {"@id": site_url + "/#organization"}})
    else:
        title = re.search(r"<title[^>]*>(.*?)</title>", source, re.S | re.I)
        graph.append({"@type": "WebPage", "@id": url + "#webpage", "url": url,
                      "name": html.unescape(title.group(1).strip()) if title else "",
                      "isPartOf": {"@id": site_url + "/#website"}})
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": site_url + "/"},
            {"@type": "ListItem", "position": 2, "name": html.unescape(title.group(1).strip()) if title else page_path, "item": url}]})
    faq = _faq_pairs(source)
    if faq:
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    lines.append(_jsonld({"@context": "https://schema.org", "@graph": graph}))

    measurement_id = growth.get("analytics", {}).get("ga4_measurement_id", "")
    if measurement_id and "googletagmanager.com/gtag" not in outside:
        lines.append(f'<script async src="https://www.googletagmanager.com/gtag/js?id={_esc(measurement_id)}"></script>')
        lines.append("<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
                     f"gtag('js',new Date());gtag('config','{measurement_id}');</script>")
    return "\n".join(lines)


def _faq_pairs(source: str) -> list[tuple[str, str]]:
    pairs = []
    strip = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
    for block in re.findall(r"<details\b[^>]*>(.*?)</details>", source, re.S | re.I):
        summary = re.search(r"<summary\b[^>]*>(.*?)</summary>", block, re.S | re.I)
        if not summary:
            continue
        question = strip(summary.group(1))
        answer = strip(block.replace(summary.group(0), ""))
        if question and answer:
            pairs.append((question, answer))
    return pairs


def tracking_block(growth: dict[str, Any]) -> str:
    """Report every click on the scheduler link as an enquiry event, with where it was clicked."""
    analytics = growth.get("analytics", {})
    hosts = growth.get("cta", {}).get("hosts", [])
    if not analytics.get("ga4_measurement_id") or not hosts:
        return ""
    event = analytics.get("enquiry_event", "book_walkthrough")
    return ("<script>(function(){var h=" + json.dumps(hosts) + ";document.addEventListener('click',function(e){"
            "var a=e.target.closest&&e.target.closest('a[href]');if(!a)return;"
            "var m=a.href.indexOf('mailto:')===0;if(!m&&!h.some(function(x){return a.href.indexOf(x)>-1;}))return;"
            "var s=a.closest('section[id],header[id],footer[id]');"
            f"if(window.gtag)gtag('event',m?'email_click':'{event}',"
            "{cta_location:s?s.id:'page',cta_label:(a.textContent||a.getAttribute('aria-label')||'').trim().slice(0,60),"
            "page_path:location.pathname});},true);})();</script>")


def foundation_gaps(site: SiteModel, growth: dict[str, Any]) -> list[dict[str, Any]]:
    """What is missing for search engines to crawl, understand and measure the site."""
    gaps: list[dict[str, Any]] = []
    if not site.pages:
        return [{"title": "Site checkout not found", "auto": False, "order": 0,
                 "why": f"No HTML found under {site.root}. The loop cannot see or change the site."}]
    indexable = {_url(site.site_url, p.path) for p in site.indexable_pages()}
    if not site.has_robots:
        gaps.append({"title": "Add robots.txt", "order": 1,
                     "why": "The site has no robots.txt, so crawlers get no pointer to the sitemap."})
    if not site.has_sitemap:
        gaps.append({"title": "Add sitemap.xml", "order": 2,
                     "why": "The site has no sitemap. Search Console still holds the old one listing URLs that no longer exist."})
    elif set(site.sitemap_urls) != indexable:
        gaps.append({"title": "Update sitemap.xml", "order": 2,
                     "why": "The sitemap does not match the pages that exist."})
    for page in site.pages:
        if page.managed:
            continue
        missing = []
        if not page.canonical:
            missing.append("canonical URL")
        if not page.jsonld_types:
            missing.append("structured data")
        if missing:
            gaps.append({"title": f"Add {' and '.join(missing)} to {page.path}", "path": page.path, "order": 3,
                         "why": "Without these, Google has to guess the preferred URL and what the page is about."})
    key = growth.get("indexnow", {}).get("key", "")
    if key and not (site.root / f"{key}.txt").exists():
        gaps.append({"title": "Publish the IndexNow key file", "order": 4,
                     "why": "Bing and Yandex reject IndexNow submissions unless the key file is served by the site."})
    if not any(p.has_analytics for p in site.pages):
        configured = bool(growth.get("analytics", {}).get("ga4_measurement_id"))
        gaps.append({"title": "Install analytics and enquiry tracking", "order": 5, "auto": configured,
                     "why": ("The site has no analytics, so visits and walkthrough clicks are invisible. "
                             + ("The loop will add the GA4 tag and click tracking."
                                if configured else
                                "Set analytics.ga4_measurement_id in growth.yaml and the loop installs the tag and click tracking."))})
    if growth.get("analytics", {}).get("ga4_measurement_id") and not consent_block(growth):
        gaps.append({"title": "Add a cookie consent banner", "order": 8, "auto": False,
                     "why": "The site sets analytics cookies without asking. Set consent.termly_website_uuid in "
                            "growth.yaml and the loop adds the Termly banner as the first script on every page."})
    section = growth.get("publish", {}).get("section", "resources")
    if any(p.managed for p in site.pages) and not any(
            f"/{section}" in p.internal_links for p in site.pages if not p.managed):
        gaps.append({"title": f"Link /{section} from the site navigation or footer", "order": 7, "auto": False,
                     "why": f"Published pages are only reachable through the sitemap. One link to /{section} from the "
                            "hand-authored pages lets visitors and crawlers reach them and passes authority."})
    wanted = {r["source"]: r["destination"] for r in growth.get("redirects", [])}
    have = {r.get("source"): r.get("destination") for r in site.redirects}
    absent = [s for s, d in wanted.items() if have.get(s) != d]
    if absent:
        gaps.append({"title": f"Redirect {len(absent)} URL pattern(s) from the previous site", "order": 6,
                     "why": "The previous site's URLs now return 404. Any links, bookmarks and rankings they had are lost without redirects."})
    return gaps


def apply_foundation(site: SiteModel, growth: dict[str, Any], ledger: Ledger, today: date) -> list[str]:
    """Bring the checkout up to the foundation. Returns the files changed."""
    root, changed = site.root, []

    def write(rel: str, content: str) -> None:
        target = root / rel
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            changed.append(rel)

    for page in site.pages:
        if page.managed:
            continue
        file = root / page.file
        source = file.read_text(encoding="utf-8")
        updated = _replace_block(source, HEAD_OPEN, HEAD_CLOSE, head_block(page.path, source, site, growth), "</head>")
        updated = _replace_block(updated, BODY_OPEN, BODY_CLOSE, tracking_block(growth), "</body>")
        updated = _replace_head_start_block(updated, CONSENT_OPEN, CONSENT_CLOSE, consent_block(growth))
        if updated != source:
            file.write_text(updated, encoding="utf-8")
            changed.append(page.file)

    key = growth.get("indexnow", {}).get("key", "")
    if key:
        write(f"{key}.txt", key)

    robots = root / "robots.txt"
    if not robots.exists() or ROBOTS_MARK in robots.read_text(encoding="utf-8"):
        write("robots.txt", f"{ROBOTS_MARK}\nUser-agent: *\nAllow: /\n\nSitemap: {site.site_url}/sitemap.xml\n")

    wanted = growth.get("redirects", [])
    if wanted:
        vercel = root / "vercel.json"
        config = json.loads(vercel.read_text(encoding="utf-8")) if vercel.exists() else {}
        sources = {r["source"] for r in wanted}
        kept = [r for r in config.get("redirects", []) if r.get("source") not in sources]
        config["redirects"] = kept + [{"source": r["source"], "destination": r["destination"], "permanent": True}
                                      for r in wanted]
        write("vercel.json", json.dumps(config, indent=2) + "\n")

    fresh = SiteModel.load(root, site.site_url)
    write("sitemap.xml", build_sitemap(fresh, ledger, today))
    return changed


def build_sitemap(site: SiteModel, ledger: Ledger, today: date) -> str:
    """lastmod is the date the loop last saw the page content change, not the run date."""
    import hashlib
    seen = ledger.data.setdefault("content_hashes", {})
    entries = []
    for page in sorted(site.indexable_pages(), key=lambda p: (p.path != "/", p.path)):
        digest = hashlib.sha256(page.text.encode("utf-8")).hexdigest()[:16]
        record = seen.get(page.path)
        if not record or record["hash"] != digest:
            record = seen[page.path] = {"hash": digest, "lastmod": today.isoformat()}
        entries.append(f"  <url><loc>{_esc(_url(site.site_url, page.path))}</loc><lastmod>{record['lastmod']}</lastmod></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(entries) + "\n</urlset>\n")


# ── articles ───────────────────────────────────────────────────────────────
ARTICLE_CSS = """
@layer sections {
main { padding-top: 68px; }
.art { max-width: 46rem; margin-inline: auto; padding-block: clamp(40px, 6vw, 88px); }
.art__crumb { color: var(--color-4); margin-bottom: 20px; }
.art__crumb a { text-decoration: underline; text-underline-offset: 3px; }
.art h1 { margin-bottom: 18px; text-wrap: balance; }
.art__lead { color: var(--color-4); margin-bottom: 14px; }
.art__meta { color: var(--color-4); margin-bottom: clamp(28px, 4vw, 48px); }
.art__body { font-size: 17px; line-height: 1.65; }
.art__body > * + * { margin-top: 1.1em; }
.art__body h2 { font-family: var(--font-1); font-size: clamp(24px, 2.4vw, 32px); line-height: 1.12; font-weight: 500; letter-spacing: -0.02em; margin-top: 2em; text-wrap: balance; }
.art__body h3 { font-family: var(--font-1); font-size: 20px; line-height: 1.2; font-weight: 500; margin-top: 1.6em; }
.art__body a { color: var(--color-7); text-decoration: underline; text-underline-offset: 3px; }
.art__body ul, .art__body ol { padding-left: 1.3em; display: grid; gap: .45em; }
.art__body ul { list-style: disc; } .art__body ol { list-style: decimal; }
.art__body blockquote { border-left: 3px solid var(--color-7); padding-left: 1em; color: var(--color-4); }
.art__body table { width: 100%; border-collapse: collapse; font-size: 15px; display: block; overflow-x: auto; }
.art__body th, .art__body td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--color-6); vertical-align: top; }
.art__cta { margin-top: clamp(36px, 5vw, 64px); padding: clamp(22px, 3vw, 36px); display: grid; gap: 14px; justify-items: start; }
.art__list { display: grid; gap: 14px; margin-top: 28px; }
.art__item { display: grid; gap: 6px; padding: 20px 22px; }
.art__item p { color: var(--color-4); }
}
"""


def load_chrome(site: SiteModel, growth: dict[str, Any]) -> dict[str, str]:
    """Borrow head assets, header and footer from an existing page so articles match the site."""
    publish = growth.get("publish", {})
    file = site.root / publish.get("chrome_from", "pilot.html")
    if not file.exists():
        raise PublishError(f"chrome page {file.name} not found in the site checkout")
    source = file.read_text(encoding="utf-8")
    head = source[: source.lower().find("</head>")]
    exclude = set(publish.get("chrome_exclude_styles", []))
    styles = []
    for match in re.finditer(r"<style\b([^>]*)>.*?</style>", head, re.S | re.I):
        part = re.search(r'data-8b-part="([^"]+)"', match.group(1))
        if not (part and part.group(1) in exclude):
            styles.append(match.group(0))
    links = re.findall(r'<link\b[^>]+rel="(?:icon|preconnect|preload)"[^>]*>', head, re.I)
    header = re.search(r'<header\b[^>]*id="site-nav".*?</header>', source, re.S | re.I)
    footer = re.search(r'<footer\b[^>]*id="site-footer".*?</footer>', source, re.S | re.I)
    if not header or not footer:
        raise PublishError(f"{file.name} has no #site-nav header or #site-footer footer to reuse")
    script = re.search(r'<script data-8b-part="section-script:site-nav">.*?</script>', source, re.S | re.I)

    def absolute(fragment: str) -> str:
        fragment = re.sub(r'(src|href)="(?!https?:|/|#|mailto:|data:)([^"]+)"', r'\1="/\2"', fragment)
        return fragment.replace(' aria-current="page"', "")

    return {"links": absolute("\n".join(links)), "styles": "\n".join(styles),
            "header": absolute(header.group(0)), "footer": absolute(footer.group(0)),
            "script": script.group(0) if script else ""}


def _page_shell(*, chrome: dict[str, str], site: SiteModel, growth: dict[str, Any], path: str, title: str,
                description: str, graph: list[dict[str, Any]], main: str, og_type: str = "article") -> str:
    brand = growth.get("brand", "Pipeleap")
    url = _url(site.site_url, path)
    full_title = title if brand.lower() in title.lower() else f"{title} · {brand}"
    measurement_id = growth.get("analytics", {}).get("ga4_measurement_id", "")
    analytics = ""
    if measurement_id:
        analytics = (f'<script async src="https://www.googletagmanager.com/gtag/js?id={_esc(measurement_id)}"></script>\n'
                     "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
                     f"gtag('js',new Date());gtag('config','{measurement_id}');</script>\n")
    consent = consent_block(growth)
    consent = f"{CONSENT_OPEN}\n{consent}\n{CONSENT_CLOSE}\n" if consent else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
{consent}<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(full_title)}</title>
<meta name="description" content="{_esc(description)}">
<meta name="generator" content="{GENERATOR}">
<link rel="canonical" href="{_esc(url)}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{_esc(title)}">
<meta property="og:description" content="{_esc(description)}">
<meta property="og:url" content="{_esc(url)}">
<meta property="og:site_name" content="{_esc(brand)}">
<meta name="twitter:card" content="summary">
{chrome['links']}
{chrome['styles']}
<style data-8b-part="article">{ARTICLE_CSS}</style>
{_jsonld({"@context": "https://schema.org", "@graph": graph})}
{analytics}</head>
<body>
{chrome['header']}
<main>
{main}
</main>
{chrome['footer']}
{chrome['script']}
{tracking_block(growth)}
</body>
</html>
"""


def render_article(*, site: SiteModel, growth: dict[str, Any], chrome: dict[str, str], path: str, title: str,
                   description: str, markdown_body: str, published: date, modified: date) -> str:
    import markdown as md
    body = md.markdown(markdown_body, extensions=["extra", "sane_lists"], output_format="html")
    section = growth.get("publish", {}).get("section", "resources")
    label = growth.get("publish", {}).get("section_label", "Resources")
    cta = growth.get("cta", {})
    url = _url(site.site_url, path)
    graph = [
        {"@type": "Article", "@id": url + "#article", "headline": title, "description": description,
         "datePublished": published.isoformat(), "dateModified": modified.isoformat(), "mainEntityOfPage": url,
         "author": {"@id": site.site_url + "/#organization"}, "publisher": {"@id": site.site_url + "/#organization"}},
        organization(growth, site.site_url),
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": site.site_url + "/"},
            {"@type": "ListItem", "position": 2, "name": label, "item": _url(site.site_url, f"/{section}")},
            {"@type": "ListItem", "position": 3, "name": title, "item": url}]},
    ]
    main = f"""<article class="art wrap">
  <p class="art__crumb m-text-3"><a href="/">Home</a> / <a href="/{section}">{_esc(label)}</a></p>
  <h1 class="m-text-5">{_esc(title)}</h1>
  <p class="art__lead m-text-2">{_esc(description)}</p>
  <p class="art__meta m-text-3">Updated <time datetime="{modified.isoformat()}">{modified.strftime('%d %B %Y').lstrip('0')}</time></p>
  <div class="art__body">
{body}
  </div>
  <aside id="article-cta" class="art__cta m-surface">
    <h2 class="m-text-6">{_esc(cta.get('heading', ''))}</h2>
    <p>{_esc(cta.get('text', ''))}</p>
    <a class="m-btn" href="{_esc(cta.get('url', ''))}" target="_blank" rel="noopener"><span class="m-btn__label">{_esc(cta.get('label', 'Book a walkthrough'))}</span></a>
  </aside>
</article>"""
    return _page_shell(chrome=chrome, site=site, growth=growth, path=path, title=title,
                       description=description, graph=graph, main=main)


def render_index(*, site: SiteModel, growth: dict[str, Any], chrome: dict[str, str],
                 articles: list[dict[str, str]]) -> str:
    publish = growth.get("publish", {})
    section, label = publish.get("section", "resources"), publish.get("section_label", "Resources")
    description = publish.get("section_description", "")
    items = "\n".join(
        f'    <a class="art__item m-surface" href="{_esc(a["path"])}"><h2 class="m-text-6">{_esc(a["title"])}</h2>'
        f'<p>{_esc(a["description"])}</p></a>' for a in articles)
    url = _url(site.site_url, f"/{section}")
    graph = [{"@type": "CollectionPage", "@id": url + "#page", "url": url, "name": label, "description": description,
              "isPartOf": {"@id": site.site_url + "/#website"}}]
    main = f"""<section class="art wrap">
  <p class="art__crumb m-text-3"><a href="/">Home</a></p>
  <h1 class="m-text-5">{_esc(publish.get('section_heading', label))}</h1>
  <p class="art__lead m-text-2">{_esc(description)}</p>
  <div class="art__list">
{items}
  </div>
</section>"""
    return _page_shell(chrome=chrome, site=site, growth=growth, path=f"/{section}", title=label,
                       description=description, graph=graph, main=main, og_type="website")


def save_source(sources_dir: Path, *, path: str, title: str, description: str, query: str,
                cluster: str, markdown_body: str) -> Path:
    """Article sources live in this repository; the site's HTML is rendered from them."""
    sources_dir.mkdir(parents=True, exist_ok=True)
    file = sources_dir / (normalize_path(path).strip("/").replace("/", "__") + ".md")
    front = {"path": normalize_path(path), "title": title, "description": description,
             "query": query, "cluster": cluster}
    file.write_text("\n".join(f"{k}: {v}" for k, v in front.items()) + "\n---\n" + markdown_body.strip() + "\n",
                    encoding="utf-8")
    return file


def read_source(file: Path) -> dict[str, str]:
    front, _, body = file.read_text(encoding="utf-8").partition("\n---\n")
    data = dict(line.split(": ", 1) for line in front.splitlines() if ": " in line)
    data["markdown"] = body.strip()
    return data


def sync_articles(site: SiteModel, growth: dict[str, Any], ledger: Ledger, sources_dir: Path,
                  today: date) -> list[str]:
    """Render every article source with the site's current chrome. Returns files changed."""
    sources = [read_source(f) for f in sorted(sources_dir.glob("*.md"))] if sources_dir.is_dir() else []
    if not sources:
        return []
    chrome = load_chrome(site, growth)
    changed: list[str] = []

    def write(rel: str, content: str) -> None:
        target = site.root / rel
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            changed.append(rel)

    listing = []
    for source in sources:
        path = source["path"]
        if path not in ledger.data["pages"]:
            ledger.register_page(path, kind="article", cluster=source.get("cluster", ""),
                                 target_query=source.get("query", ""), today=today)
        meta = ledger.data["pages"][path]
        meta.update({"title": source["title"], "description": source["description"]})
        write(path.strip("/") + ".html", render_article(
            site=site, growth=growth, chrome=chrome, path=path, title=source["title"],
            description=source["description"], markdown_body=source["markdown"],
            published=date.fromisoformat(meta["published_at"]),
            modified=date.fromisoformat(meta["last_changed_at"])))
        listing.append({"path": path, "title": source["title"], "description": source["description"],
                        "published_at": meta["published_at"]})
    listing.sort(key=lambda a: a["published_at"], reverse=True)
    section = growth.get("publish", {}).get("section", "resources")
    write(f"{section}.html", render_index(site=site, growth=growth, chrome=chrome, articles=listing))
    return changed
