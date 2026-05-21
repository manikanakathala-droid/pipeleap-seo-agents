from __future__ import annotations

import hashlib
import json
from collections import deque
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse
from xml.etree import ElementTree

import requests

import time
from utils.models import CrawlerReport, PageSnapshot


class SEOHTMLParser(HTMLParser):
    """Extracts SEO-relevant HTML features without external parser dependencies."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta_description = ""
        self.canonical = ""
        self.meta_robots = ""
        self.h1 = ""
        self.headings: list[str] = []
        self.links: list[str] = []
        self.text_chunks: list[str] = []
        self.schema_types: list[str] = []
        self.image_count = 0
        self.images_without_alt = 0
        self.script_count = 0
        self.stylesheet_count = 0
        self.has_viewport_meta = False

        self._capture_title = False
        self._capture_heading = ""
        self._heading_buffer: list[str] = []
        self._capture_json_ld = False
        self._json_ld_buffer: list[str] = []
        self._skip_text_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key.lower(): value or "" for key, value in attrs}
        tag_lower = tag.lower()

        if tag_lower == "title":
            self._capture_title = True
        elif tag_lower in {"h1", "h2", "h3", "h4"}:
            self._capture_heading = tag_lower
            self._heading_buffer = []
        elif tag_lower == "meta":
            meta_name = attr_map.get("name", "").lower()
            if meta_name == "description":
                self.meta_description = attr_map.get("content", "").strip()
            if meta_name == "robots":
                self.meta_robots = attr_map.get("content", "").strip()
            if meta_name == "viewport":
                self.has_viewport_meta = True
        elif tag_lower == "link":
            rel = attr_map.get("rel", "").lower()
            if "canonical" in rel:
                self.canonical = attr_map.get("href", "").strip()
            if "stylesheet" in rel:
                self.stylesheet_count += 1
        elif tag_lower == "a":
            href = attr_map.get("href", "").strip()
            if href:
                self.links.append(href)
        elif tag_lower == "img":
            self.image_count += 1
            if not attr_map.get("alt", "").strip():
                self.images_without_alt += 1
        elif tag_lower == "script":
            self.script_count += 1
            script_type = attr_map.get("type", "").lower()
            if "ld+json" in script_type:
                self._capture_json_ld = True
                self._json_ld_buffer = []
            self._skip_text_depth += 1
        elif tag_lower == "style":
            self._skip_text_depth += 1

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower == "title":
            self._capture_title = False
            self.title = self.title.strip()
        elif tag_lower == self._capture_heading:
            heading_text = " ".join(self._heading_buffer).strip()
            if heading_text:
                self.headings.append(heading_text)
                if tag_lower == "h1" and not self.h1:
                    self.h1 = heading_text
            self._capture_heading = ""
            self._heading_buffer = []
        elif tag_lower == "script":
            if self._capture_json_ld:
                self._extract_schema_types("".join(self._json_ld_buffer))
                self._capture_json_ld = False
                self._json_ld_buffer = []
            self._skip_text_depth = max(0, self._skip_text_depth - 1)
        elif tag_lower == "style":
            self._skip_text_depth = max(0, self._skip_text_depth - 1)

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if not stripped:
            return

        if self._capture_title:
            self.title += f" {stripped}"
        elif self._capture_heading:
            self._heading_buffer.append(stripped)
        elif self._capture_json_ld:
            self._json_ld_buffer.append(data)
        elif self._skip_text_depth == 0:
            self.text_chunks.append(stripped)

    def _extract_schema_types(self, raw_json: str) -> None:
        try:
            payload = json.loads(raw_json)
        except Exception:
            return

        def collect_types(node: Any) -> None:
            if isinstance(node, dict):
                schema_type = node.get("@type")
                if isinstance(schema_type, str):
                    self.schema_types.append(schema_type)
                elif isinstance(schema_type, list):
                    self.schema_types.extend(item for item in schema_type if isinstance(item, str))
                for value in node.values():
                    collect_types(value)
            elif isinstance(node, list):
                for item in node:
                    collect_types(item)

        collect_types(payload)


class SiteCrawler:
    """Small-footprint SEO crawler for HTML, robots.txt, and sitemap checks."""

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "PipeleapSEOAgent/1.0 (+https://pipeleap.com)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )

    def crawl(self, site_url: str, max_pages: int = 25, max_depth: int = 2) -> CrawlerReport:
        parsed_site = urlparse(site_url)
        site_root = f"{parsed_site.scheme}://{parsed_site.netloc}"
        pages: list[PageSnapshot] = []
        crawl_errors: list[str] = []
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(self._normalize_url(site_url), 0)])

        robots_present, robots_rules, sitemap_urls = self._fetch_site_controls(site_root)

        while queue and len(pages) < max_pages:
            url, depth = queue.popleft()
            if url in visited or depth > max_depth:
                continue
            visited.add(url)

            try:
                response = self.session.get(url, timeout=10)
                response_time_ms = int(response.elapsed.total_seconds() * 1000)
                if response.status_code >= 500:
                    self.logger.warning("HTTP 5xx error at %s. Slowing down crawl to avoid overloading server.", url)
                    time.sleep(5)
            except requests.RequestException as exc:
                crawl_errors.append(f"{url}: {exc}")
                continue

            content_type = response.headers.get("Content-Type", "")
            if "html" not in content_type.lower():
                continue

            parser = SEOHTMLParser()
            parser.feed(response.text)

            internal_links: list[str] = []
            external_links: list[str] = []
            for href in parser.links:
                normalized = self._normalize_url(urljoin(url, href))
                if not normalized:
                    continue
                if urlparse(normalized).netloc == parsed_site.netloc:
                    internal_links.append(normalized)
                    if normalized not in visited and depth < max_depth:
                        queue.append((normalized, depth + 1))
                else:
                    external_links.append(normalized)

            visible_text = " ".join(parser.text_chunks)
            content_hash = hashlib.sha256(visible_text.encode("utf-8")).hexdigest()
            pages.append(
                PageSnapshot(
                    url=url,
                    status_code=response.status_code,
                    title=parser.title.strip(),
                    meta_description=parser.meta_description.strip(),
                    canonical=parser.canonical.strip(),
                    h1=parser.h1.strip(),
                    headings=parser.headings,
                    meta_robots=parser.meta_robots.strip(),
                    word_count=len(visible_text.split()),
                    response_time_ms=response_time_ms,
                    internal_links=sorted(set(internal_links)),
                    external_links=sorted(set(external_links)),
                    content_hash=content_hash,
                    schema_types=sorted(set(parser.schema_types)),
                    image_count=parser.image_count,
                    images_without_alt=parser.images_without_alt,
                    script_count=parser.script_count,
                    stylesheet_count=parser.stylesheet_count,
                    has_viewport_meta=parser.has_viewport_meta,
                )
            )

        return CrawlerReport(
            site_url=site_url,
            pages=pages,
            robots_txt_present=robots_present,
            robots_rules=robots_rules,
            sitemap_urls=sitemap_urls,
            crawl_errors=crawl_errors,
            discovered_at=datetime.now(timezone.utc).isoformat(),
        )

    def _fetch_site_controls(self, site_root: str) -> tuple[bool, list[str], list[str]]:
        robots_url = urljoin(site_root, "/robots.txt")
        robots_rules: list[str] = []
        sitemap_urls: list[str] = []
        robots_present = False

        try:
            response = self.session.get(robots_url, timeout=10)
            if response.ok:
                robots_present = True
                robots_rules = [line.strip() for line in response.text.splitlines() if line.strip()]
                sitemap_urls.extend(
                    line.split(":", 1)[1].strip()
                    for line in robots_rules
                    if line.lower().startswith("sitemap:")
                )
        except requests.RequestException as exc:
            self.logger.warning("robots.txt fetch failed: %s", exc)

        if not sitemap_urls:
            sitemap_urls.append(urljoin(site_root, "/sitemap.xml"))

        discovered_urls: list[str] = []
        for sitemap_url in sitemap_urls:
            try:
                response = self.session.get(sitemap_url, timeout=10)
                if not response.ok:
                    continue
                root = ElementTree.fromstring(response.text)
                namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                locs = root.findall(".//sm:loc", namespace)
                if not locs:
                    locs = root.findall(".//loc")
                discovered_urls.extend([loc.text.strip() for loc in locs if loc.text])
            except Exception:
                continue

        return robots_present, robots_rules, sorted(set(discovered_urls))

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return ""
        normalized_path = parsed.path or "/"
        if normalized_path != "/" and normalized_path.endswith("/"):
            normalized_path = normalized_path[:-1]
        clean = parsed._replace(params="", query="", fragment="", path=normalized_path)
        return urlunparse(clean)
