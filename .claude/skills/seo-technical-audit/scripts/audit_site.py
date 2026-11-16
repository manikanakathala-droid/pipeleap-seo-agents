#!/usr/bin/env python3
"""Technical SEO audit for a small static site. Standard library only.

Reads robots.txt and sitemap.xml, fetches every page (or one --url), and checks
status, redirects, title, meta description, headings, canonical, robots
directives, Open Graph, JSON-LD, hreflang, image alt text, internal links and
host/protocol redirects. Optionally queries PageSpeed Insights.

Usage:
  python audit_site.py --site https://www.pipeleap.com --out seo-work/audits/2026-11-15
  python audit_site.py --url http://localhost:8000/new-page.html
  python audit_site.py --site https://www.pipeleap.com --psi   # adds PageSpeed (env PAGESPEED_API_KEY optional)

Writes <out>.json (full data) and <out>.md (issues by severity) when --out is
given; always prints the Markdown summary.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

UA = "Mozilla/5.0 (compatible; PipeleapSEOAudit/1.0)"
TITLE_RANGE = (30, 60)
DESC_RANGE = (120, 160)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # surface 3xx instead of following
        return None


def fetch(url: str, follow: bool = True, method: str = "GET", timeout: int = 20) -> dict:
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method=method)
    t0 = time.time()
    try:
        with opener.open(req, timeout=timeout) as r:
            body = r.read() if method == "GET" else b""
            return {"status": r.status, "final_url": r.geturl(), "headers": dict(r.headers),
                    "body": body.decode("utf-8", errors="replace"), "ms": int((time.time() - t0) * 1000),
                    "bytes": len(body)}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "final_url": url, "headers": dict(e.headers or {}), "body": "",
                "location": (e.headers or {}).get("Location"), "ms": int((time.time() - t0) * 1000), "bytes": 0}
    except Exception as e:  # DNS, TLS, timeout
        return {"status": 0, "final_url": url, "headers": {}, "body": "", "error": str(e),
                "ms": int((time.time() - t0) * 1000), "bytes": 0}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self._in = None
        self._buf = []
        self.meta = {}
        self.links = []
        self.canonical = []
        self.hreflang = []
        self.headings = []
        self.imgs_no_alt = 0
        self.imgs = 0
        self.jsonld = []
        self.lang = None
        self.text_parts = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self._in, self._buf = "title", []
        elif tag in ("h1", "h2", "h3"):
            self._in, self._buf = tag, []
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            rel = a.get("rel", "").lower()
            if "canonical" in rel:
                self.canonical.append(a.get("href", ""))
            if "alternate" in rel and a.get("hreflang"):
                self.hreflang.append((a["hreflang"], a.get("href", "")))
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "img":
            self.imgs += 1
            if "alt" not in a:
                self.imgs_no_alt += 1
        elif tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self._in, self._buf = "jsonld", []
        if tag in ("script", "style", "noscript", "svg") and self._in != "jsonld":
            self._skip += 1

    def handle_endtag(self, tag):
        if self._in == "title" and tag == "title":
            self.title = "".join(self._buf).strip()
            self._in = None
        elif self._in in ("h1", "h2", "h3") and tag == self._in:
            self.headings.append((self._in, re.sub(r"\s+", " ", "".join(self._buf)).strip()))
            self._in = None
        elif self._in == "jsonld" and tag == "script":
            self.jsonld.append("".join(self._buf))
            self._in = None
        elif tag in ("script", "style", "noscript", "svg") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._in:
            self._buf.append(data)
        if not self._skip:
            self.text_parts.append(data)


def norm(u: str) -> str:
    """Treat https://host and https://host/ as the same page; drop fragments."""
    parts = urllib.parse.urlsplit(u.split("#")[0])
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))


def schema_types(blob) -> list[str]:
    out = []
    if isinstance(blob, list):
        for b in blob:
            out += schema_types(b)
    elif isinstance(blob, dict):
        t = blob.get("@type")
        if t:
            out += t if isinstance(t, list) else [t]
        for b in blob.get("@graph", []) or []:
            out += schema_types(b)
    return out


def audit_page(url: str, host: str) -> dict:
    r = fetch(url)
    page = {"url": url, "status": r["status"], "final_url": r["final_url"], "ms": r["ms"],
            "bytes": r["bytes"], "issues": []}
    issue = lambda sev, msg: page["issues"].append({"severity": sev, "message": msg})
    if r.get("error"):
        issue("error", f"Fetch failed: {r['error']}")
        return page
    if r["status"] >= 400:
        issue("error", f"HTTP {r['status']}")
        return page
    if r["final_url"].rstrip("/") != url.rstrip("/"):
        issue("warning", f"Redirects to {r['final_url']} (link to the final URL instead)")

    p = PageParser()
    p.feed(r["body"])
    words = len(re.findall(r"[A-Za-z][A-Za-z'-]+", " ".join(p.text_parts)))
    h1 = [t for lvl, t in p.headings if lvl == "h1"]
    desc = p.meta.get("description")
    robots = (p.meta.get("robots", "") + " " + r["headers"].get("X-Robots-Tag", "")).lower()
    types, ld_errors = [], 0
    for blob in p.jsonld:
        try:
            types += schema_types(json.loads(blob))
        except Exception:
            ld_errors += 1

    internal, external = set(), set()
    for href in p.links:
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absu = norm(urllib.parse.urljoin(r["final_url"], href))
        (internal if urllib.parse.urlparse(absu).netloc == host else external).add(absu)

    page.update({
        "title": p.title, "title_len": len(p.title or ""),
        "description": desc, "description_len": len(desc or ""),
        "h1": h1, "h2": [t for lvl, t in p.headings if lvl == "h2"],
        "canonical": p.canonical, "robots": robots.strip(), "lang": p.lang,
        "og": {k: v for k, v in p.meta.items() if k.startswith(("og:", "twitter:"))},
        "schema_types": sorted(set(types)), "hreflang": p.hreflang,
        "images": p.imgs, "images_missing_alt": p.imgs_no_alt, "word_count": words,
        "internal_links": sorted(internal), "external_links": sorted(external),
    })

    if not p.title:
        issue("error", "Missing <title>")
    elif not TITLE_RANGE[0] <= len(p.title) <= TITLE_RANGE[1]:
        issue("warning", f"Title is {len(p.title)} chars (aim {TITLE_RANGE[0]}-{TITLE_RANGE[1]})")
    if not desc:
        issue("error", "Missing meta description")
    elif not DESC_RANGE[0] <= len(desc) <= DESC_RANGE[1]:
        issue("warning", f"Meta description is {len(desc)} chars (aim {DESC_RANGE[0]}-{DESC_RANGE[1]})")
    if len(h1) != 1:
        issue("error" if not h1 else "warning", f"{len(h1)} <h1> tags (want exactly 1)")
    elif len(h1[0].split()) < 2:
        issue("warning", f"H1 is a single word ('{h1[0]}'), so it says nothing about what the page is about")
    if not p.canonical:
        issue("error", "Missing canonical link")
    elif len(p.canonical) > 1:
        issue("error", f"{len(p.canonical)} canonical links")
    elif p.canonical[0].rstrip("/") != r["final_url"].rstrip("/") and "localhost" not in url:
        issue("warning", f"Canonical points elsewhere: {p.canonical[0]}")
    if "noindex" in robots:
        issue("error", "Page is noindex")
    if not p.lang:
        issue("warning", "<html> has no lang attribute")
    for k in ("og:title", "og:description", "og:image"):
        if k not in p.meta:
            issue("warning", f"Missing {k}")
    if ld_errors:
        issue("error", f"{ld_errors} JSON-LD block(s) do not parse")
    if not types:
        issue("info", "No structured data")
    if p.imgs_no_alt:
        issue("warning", f"{p.imgs_no_alt} image(s) without alt attribute")
    if words < 300:
        issue("info", f"Only ~{words} words of visible text")
    if r["ms"] > 1500:
        issue("warning", f"Slow response: {r['ms']} ms")
    return page


def sitemap_urls(site: str) -> list[str]:
    r = fetch(urllib.parse.urljoin(site, "/sitemap.xml"))
    if r["status"] != 200:
        return []
    try:
        root = ET.fromstring(r["body"])
    except ET.ParseError:
        return []
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    locs = [e.text.strip() for e in root.iter(f"{ns}loc") if e.text]
    if root.tag.endswith("sitemapindex"):
        out = []
        for sm in locs:
            sr = fetch(sm)
            try:
                out += [e.text.strip() for e in ET.fromstring(sr["body"]).iter(f"{ns}loc") if e.text]
            except ET.ParseError:
                pass
        return out
    return locs


def psi(url: str) -> dict:
    q = {"url": url, "strategy": "mobile", "category": "performance"}
    if os.getenv("PAGESPEED_API_KEY"):
        q["key"] = os.environ["PAGESPEED_API_KEY"]
    r = fetch("https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + urllib.parse.urlencode(q), timeout=90)
    try:
        d = json.loads(r["body"])
        lh = d["lighthouseResult"]
        audits = lh["audits"]
        field = d.get("loadingExperience", {}).get("metrics", {})
        return {
            "performance_score": round(lh["categories"]["performance"]["score"] * 100),
            "lab_lcp": audits["largest-contentful-paint"]["displayValue"],
            "lab_cls": audits["cumulative-layout-shift"]["displayValue"],
            "lab_tbt": audits["total-blocking-time"]["displayValue"],
            "field_data": {k: v.get("category") for k, v in field.items()} or "none (not enough traffic)",
        }
    except Exception as e:
        hint = " (rate-limited: set PAGESPEED_API_KEY)" if r["status"] == 429 else ""
        return {"error": f"PageSpeed unavailable, HTTP {r['status']}{hint}"}


def site_checks(site: str, host: str) -> list[dict]:
    issues = []
    rob = fetch(urllib.parse.urljoin(site, "/robots.txt"))
    if rob["status"] != 200:
        issues.append({"severity": "error", "message": f"robots.txt returns HTTP {rob['status']}"})
    else:
        if re.search(r"(?im)^disallow:\s*/\s*$", rob["body"]):
            issues.append({"severity": "error", "message": "robots.txt blocks the whole site (Disallow: /)"})
        if "sitemap:" not in rob["body"].lower():
            issues.append({"severity": "warning", "message": "robots.txt does not reference the sitemap"})
    bare = host[4:] if host.startswith("www.") else host
    for variant in {f"http://{host}/", f"https://{bare}/", f"http://{bare}/"} - {site.rstrip('/') + '/'}:
        r = fetch(variant, follow=False)
        loc = r.get("location") or r["headers"].get("Location", "")
        if r["status"] not in (301, 308):
            issues.append({"severity": "warning", "message": f"{variant} returns {r['status']} (want 301/308 to the canonical host)"})
        elif loc and urllib.parse.urlparse(urllib.parse.urljoin(variant, loc)).netloc != host:
            issues.append({"severity": "warning", "message": f"{variant} redirects to {loc}, not to {host}"})
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", help="Site root, e.g. https://www.pipeleap.com (crawls the sitemap plus linked pages)")
    ap.add_argument("--url", action="append", help="Audit only this URL (repeatable)")
    ap.add_argument("--max-pages", type=int, default=200)
    ap.add_argument("--psi", action="store_true", help="Add PageSpeed Insights (mobile) per page")
    ap.add_argument("--out", help="Output path prefix, writes <out>.json and <out>.md")
    a = ap.parse_args()
    if not a.site and not a.url:
        ap.error("give --site or --url")

    base = a.site or a.url[0]
    host = urllib.parse.urlparse(base).netloc
    report = {"site": a.site, "generated": time.strftime("%Y-%m-%d %H:%M"), "site_issues": [], "pages": []}

    if a.site:
        report["site_issues"] = site_checks(a.site, host)
        in_sitemap = sitemap_urls(a.site)
        report["sitemap_urls"] = in_sitemap
        if not in_sitemap:
            report["site_issues"].append({"severity": "error", "message": "sitemap.xml missing, empty or invalid"})
        queue = list(dict.fromkeys(norm(u) for u in (in_sitemap or [a.site])))
    else:
        in_sitemap, queue = [], [norm(u) for u in a.url]

    seen, linked_to = set(), {}
    while queue and len(seen) < a.max_pages:
        u = norm(queue.pop(0))
        if u in seen:
            continue
        seen.add(u)
        page = audit_page(u, host)
        report["pages"].append(page)
        if a.psi and page["status"] == 200:
            page["pagespeed"] = psi(u)
        for link in page.get("internal_links", []):
            linked_to.setdefault(link.rstrip("/"), set()).add(u)
            if a.site and link not in seen and not re.search(r"\.(png|jpe?g|svg|webp|gif|pdf|css|js|ico|txt|xml|woff2?)$", link):
                queue.append(link)

    if a.site:
        crawled = {p["url"].rstrip("/"): p for p in report["pages"]}
        for link, sources in linked_to.items():
            p = crawled.get(link)
            if p and p["status"] >= 400:
                report["site_issues"].append({"severity": "error", "message": f"Broken internal link {link} (HTTP {p['status']}) from {', '.join(sorted(sources))}"})
        for u in in_sitemap:
            p = crawled.get(u.rstrip("/"))
            if p and (p["status"] != 200 or p["final_url"].rstrip("/") != u.rstrip("/")):
                report["site_issues"].append({"severity": "error", "message": f"Sitemap lists {u} but it returns {p['status']} / {p['final_url']}"})
            home = a.site.rstrip("/")
            if u.rstrip("/") != home and u.rstrip("/") not in linked_to:
                report["site_issues"].append({"severity": "warning", "message": f"{u} is in the sitemap but no crawled page links to it (orphan)"})
        for p in report["pages"]:
            if p["status"] == 200 and p["url"] not in in_sitemap and p["url"].rstrip("/") + "/" not in in_sitemap and p["url"].rstrip("/") not in [s.rstrip("/") for s in in_sitemap]:
                report["site_issues"].append({"severity": "warning", "message": f"{p['url']} is linked internally but missing from the sitemap"})
        for field in ("title", "description"):
            groups = {}
            for p in report["pages"]:
                if p.get(field):
                    groups.setdefault(p[field], []).append(p["url"])
            for val, urls in groups.items():
                if len(urls) > 1:
                    report["site_issues"].append({"severity": "warning", "message": f"Duplicate {field} on {', '.join(urls)}"})

    order = {"error": 0, "warning": 1, "info": 2}
    lines = [f"# Technical SEO audit: {a.site or ', '.join(a.url)}", f"Generated {report['generated']}", ""]
    counts = {"error": 0, "warning": 0, "info": 0}
    for i in report["site_issues"] + [x for p in report["pages"] for x in p["issues"]]:
        counts[i["severity"]] += 1
    lines.append(f"**{counts['error']} errors, {counts['warning']} warnings, {counts['info']} notes** across {len(report['pages'])} pages.\n")
    if report["site_issues"]:
        lines.append("## Site-wide")
        for i in sorted(report["site_issues"], key=lambda x: order[x["severity"]]):
            lines.append(f"- **{i['severity']}**: {i['message']}")
        lines.append("")
    lines.append("## Pages")
    for p in report["pages"]:
        lines.append(f"### {p['url']}  (HTTP {p['status']}, {p['ms']} ms)")
        if p["status"] == 200 and "title" in p:
            lines.append(f"- Title ({p['title_len']}): {p['title']}")
            lines.append(f"- Description ({p['description_len']}): {p['description']}")
            lines.append(f"- H1: {' | '.join(p['h1']) or '(none)'}")
            lines.append(f"- H2s: {len(p['h2'])} · words: ~{p['word_count']} · schema: {', '.join(p['schema_types']) or 'none'}")
        if p.get("pagespeed"):
            lines.append(f"- PageSpeed (mobile): {p['pagespeed']}")
        for i in sorted(p["issues"], key=lambda x: order[x["severity"]]):
            lines.append(f"- **{i['severity']}**: {i['message']}")
        lines.append("")
    md = "\n".join(lines)

    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        with open(a.out + ".json", "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=list)
        with open(a.out + ".md", "w", encoding="utf-8") as fh:
            fh.write(md)
    sys.stdout.reconfigure(encoding="utf-8")
    print(md)
    return 1 if counts["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
