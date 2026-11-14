"""Read-only model of the live site, built from its source checkout."""
from __future__ import annotations

import html as _html
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

_TAG = re.compile(r"<[^>]+>")
_STRIP_BLOCKS = re.compile(r"<(script|style|svg|noscript)\b.*?</\1>", re.S | re.I)


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(_TAG.sub(" ", fragment))).strip()


def _first(pattern: str, source: str) -> str:
    match = re.search(pattern, source, re.S | re.I)
    return _html.unescape(match.group(1)).strip() if match else ""


@dataclass
class Page:
    file: str                      # path relative to the site root, e.g. "pilot.html"
    path: str                      # public path, e.g. "/pilot"
    url: str
    title: str = ""
    meta_description: str = ""
    h1: str = ""
    h2s: list[str] = field(default_factory=list)
    text: str = ""
    word_count: int = 0
    canonical: str = ""
    robots: str = ""
    jsonld_types: list[str] = field(default_factory=list)
    internal_links: list[str] = field(default_factory=list)
    cta_links: int = 0
    has_analytics: bool = False
    managed: bool = False          # written by the growth loop (vs hand-authored)

    @property
    def indexable(self) -> bool:
        return "noindex" not in self.robots.lower()


@dataclass
class SiteModel:
    root: Path
    site_url: str
    pages: list[Page] = field(default_factory=list)
    has_robots: bool = False
    has_sitemap: bool = False
    sitemap_urls: list[str] = field(default_factory=list)
    redirects: list[dict] = field(default_factory=list)

    # ── loading ────────────────────────────────────────────────────────────
    @classmethod
    def load(cls, root: str | Path, site_url: str, cta_hosts: tuple[str, ...] = ()) -> "SiteModel":
        root = Path(root)
        site_url = site_url.rstrip("/")
        model = cls(root=root, site_url=site_url)
        if not root.is_dir():
            return model
        for file in sorted(root.rglob("*.html")):
            rel = file.relative_to(root).as_posix()
            if rel.startswith((".", "node_modules/")) or "/." in rel:
                continue
            model.pages.append(_parse_page(file, rel, site_url, cta_hosts))
        model.has_robots = (root / "robots.txt").exists()
        sitemap = root / "sitemap.xml"
        model.has_sitemap = sitemap.exists()
        if model.has_sitemap:
            model.sitemap_urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sitemap.read_text(encoding="utf-8"))
        vercel = root / "vercel.json"
        if vercel.exists():
            try:
                model.redirects = json.loads(vercel.read_text(encoding="utf-8")).get("redirects", [])
            except json.JSONDecodeError:
                model.redirects = []
        return model

    # ── queries ────────────────────────────────────────────────────────────
    def page(self, path_or_url: str) -> Page | None:
        key = normalize_path(path_or_url, self.site_url)
        return next((p for p in self.pages if p.path == key), None)

    def indexable_pages(self) -> list[Page]:
        return [p for p in self.pages if p.indexable]

    def faq(self) -> list[tuple[str, str]]:
        """Question/answer pairs published on the site (used for grounding and FAQ schema)."""
        pairs: list[tuple[str, str]] = []
        for page in self.pages:
            source = (self.root / page.file).read_text(encoding="utf-8")
            for block in re.findall(r"<details\b[^>]*>(.*?)</details>", source, re.S | re.I):
                question = _text(_first(r"<summary\b[^>]*>(.*?)</summary>", block))
                answer = _text(re.sub(r"<summary\b.*?</summary>", "", block, flags=re.S | re.I))
                if question and answer and (question, answer) not in pairs:
                    pairs.append((question, answer))
        return pairs

    def facts(self, max_chars: int = 6000, exclude: tuple[str, ...] | list[str] = ()) -> str:
        """Plain-text digest of what the site says. The only allowed source of product claims.

        The homepage comes first so it is never cut off; legal pages are listed in `exclude`.
        """
        parts: list[str] = []
        for page in sorted(self.pages, key=lambda p: (p.path != "/", p.path)):
            if page.managed or page.path in exclude:
                continue
            parts.append(f"[{page.path}] {page.title}\n{page.meta_description}\n{page.text}")
        return "\n\n".join(parts)[:max_chars]


def normalize_path(path_or_url: str, site_url: str = "") -> str:
    value = path_or_url.strip()
    value = re.sub(r"^https?://[^/]+", "", value)
    value = value.split("#")[0].split("?")[0]
    value = re.sub(r"(/index)?\.html$", "", value)
    value = "/" + value.strip("/")
    return "/" if value in ("/index", "/") else value


def _parse_page(file: Path, rel: str, site_url: str, cta_hosts: tuple[str, ...]) -> Page:
    source = file.read_text(encoding="utf-8", errors="replace")
    head = source[: source.lower().find("</head>")] if "</head>" in source.lower() else source
    path = normalize_path(rel)
    body = _STRIP_BLOCKS.sub(" ", source[len(head):])
    text = _text(body)
    hrefs = re.findall(r"<a\b[^>]*\bhref=\"([^\"]+)\"", source, re.I)
    internal = sorted({normalize_path(h, site_url) for h in hrefs
                       if h.startswith("/") or h.startswith(site_url)} - {path})
    jsonld = re.findall(r"<script[^>]+application/ld\+json[^>]*>(.*?)</script>", source, re.S | re.I)
    types = sorted(set(re.findall(r'"@type"\s*:\s*"([^"]+)"', " ".join(jsonld))))
    return Page(
        file=rel,
        path=path,
        url=site_url + ("" if path == "/" else path) + ("/" if path == "/" else ""),
        title=_text(_first(r"<title[^>]*>(.*?)</title>", head)),
        meta_description=_first(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', head),
        h1=_text(_first(r"<h1\b[^>]*>(.*?)</h1>", body)),
        h2s=[_text(h) for h in re.findall(r"<h2\b[^>]*>(.*?)</h2>", body, re.S | re.I)],
        text=text,
        word_count=len(text.split()),
        canonical=_first(r'<link[^>]+rel="canonical"[^>]+href="([^"]*)"', head),
        robots=_first(r'<meta[^>]+name="robots"[^>]+content="([^"]*)"', head),
        jsonld_types=types,
        internal_links=internal,
        cta_links=sum(1 for h in hrefs if any(host in h for host in cta_hosts)),
        has_analytics=any(k in source for k in ("googletagmanager.com", "gtag(", "/_vercel/insights", "plausible.io")),
        managed='name="generator" content="pipeleap-growth-loop"' in head,
    )
