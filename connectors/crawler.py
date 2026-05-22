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


_GENERIC_ANCHOR_TEXTS = {
    "click here", "here", "read more", "learn more", "more", "click", "link",
    "this", "page", "website", "article", "continue", "go", "visit", "view",
}

_NON_INDEXABLE_EXTENSIONS = {
    # Archives / installers
    ".zip", ".gz", ".tar", ".rar", ".7z", ".bz2", ".xz", ".iso",
    ".exe", ".dmg", ".pkg", ".deb", ".rpm", ".msi", ".bin", ".apk",
    # Audio (not in Google's indexable file-type list)
    ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma",
    # Raw data / misc binary
    ".dat", ".db", ".sqlite",
}


_GEO_META_NAMES = frozenset({
    "geo.position", "geo.region", "geo.placename", "icbm",
    "distribution", "geo.country",
})


class SEOHTMLParser(HTMLParser):
    """Extracts SEO-relevant HTML features without external parser dependencies."""

    def __init__(self, page_url: str = "") -> None:
        super().__init__(convert_charrefs=True)
        self._page_url = page_url.rstrip("/")
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
        self.links_without_anchor_text = 0
        self.links_with_generic_anchor = 0
        self.external_links_without_rel = 0
        self.non_indexable_file_links = 0
        self.links_with_hash_routing = 0
        self.script_count = 0
        self.stylesheet_count = 0
        self.has_viewport_meta = False
        self.has_favicon = False
        self.non_crawlable_href_links = 0
        self.images_with_data_src = 0
        self.schema_has_article_date = False
        self.schema_parse_errors = 0
        self.hreflang_link_count = 0
        self.hreflang_relative_urls = 0
        self.geo_meta_tags = 0
        self._hreflang_has_self_ref = False

        self._capture_title = False
        self._capture_heading = ""
        self._heading_buffer: list[str] = []
        self._capture_json_ld = False
        self._json_ld_buffer: list[str] = []
        self._skip_text_depth = 0
        self._pending_anchor_href: str = ""
        self._anchor_has_text: bool = False
        self._anchor_text_buffer: list[str] = []

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
            if meta_name in _GEO_META_NAMES:
                self.geo_meta_tags += 1
        elif tag_lower == "link":
            rel = attr_map.get("rel", "").lower()
            if "canonical" in rel:
                self.canonical = attr_map.get("href", "").strip()
            if "stylesheet" in rel:
                self.stylesheet_count += 1
            if "icon" in rel.split():
                self.has_favicon = True
            if "alternate" in rel.split() and attr_map.get("hreflang"):
                href = attr_map.get("href", "").strip()
                self.hreflang_link_count += 1
                if not href.startswith(("http://", "https://")):
                    self.hreflang_relative_urls += 1
                if self._page_url and href.rstrip("/") == self._page_url:
                    self._hreflang_has_self_ref = True
        elif tag_lower == "a":
            href = attr_map.get("href", "").strip()
            if href.lower().startswith(("javascript:", "void(")):
                self.non_crawlable_href_links += 1
            elif href:
                self.links.append(href)
                self._pending_anchor_href = href
                self._anchor_text_buffer = []
                self._anchor_has_text = bool(attr_map.get("aria-label", "").strip()) or bool(attr_map.get("title", "").strip())
                parsed_href = urlparse(href)
                if parsed_href.scheme in {"http", "https"} and parsed_href.netloc:
                    rel_vals = {v.strip() for v in attr_map.get("rel", "").lower().split()}
                    if not rel_vals & {"nofollow", "sponsored", "ugc"}:
                        self.external_links_without_rel += 1
            ext = "." + href.rsplit(".", 1)[-1].lower().split("?")[0] if "." in href.rsplit("/", 1)[-1] else ""
            if ext in _NON_INDEXABLE_EXTENSIONS:
                self.non_indexable_file_links += 1
            if href.startswith("#/") or ("/#/" in href):
                self.links_with_hash_routing += 1
        elif tag_lower == "img":
            self.image_count += 1
            alt = attr_map.get("alt", "").strip()
            if not alt:
                self.images_without_alt += 1
            src = attr_map.get("src", "").strip()
            if "data-src" in attr_map and (not src or src.startswith("data:")):
                self.images_with_data_src += 1
            if self._pending_anchor_href and alt:
                self._anchor_has_text = True
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
        if tag_lower == "a":
            if self._pending_anchor_href and not self._anchor_has_text:
                self.links_without_anchor_text += 1
            elif self._pending_anchor_href and self._anchor_has_text:
                anchor_text = " ".join(self._anchor_text_buffer).strip().lower()
                if anchor_text in _GENERIC_ANCHOR_TEXTS:
                    self.links_with_generic_anchor += 1
            self._pending_anchor_href = ""
            self._anchor_has_text = False
            self._anchor_text_buffer = []
        elif tag_lower == "title":
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

        if self._pending_anchor_href:
            if not self._anchor_has_text:
                self._anchor_has_text = True
            self._anchor_text_buffer.append(stripped)
        if self._capture_title:
            self.title += f" {stripped}"
        elif self._capture_heading:
            self._heading_buffer.append(stripped)
        elif self._capture_json_ld:
            self._json_ld_buffer.append(data)
        elif self._skip_text_depth == 0:
            self.text_chunks.append(stripped)

    _ARTICLE_DATE_KEYS = frozenset({"datePublished", "dateModified"})

    def _extract_schema_types(self, raw_json: str) -> None:
        try:
            payload = json.loads(raw_json)
        except Exception:
            self.schema_parse_errors += 1
            return

        def collect_types(node: Any) -> None:
            if isinstance(node, dict):
                schema_type = node.get("@type")
                if isinstance(schema_type, str):
                    self.schema_types.append(schema_type)
                elif isinstance(schema_type, list):
                    self.schema_types.extend(item for item in schema_type if isinstance(item, str))
                if self._ARTICLE_DATE_KEYS & node.keys():
                    self.schema_has_article_date = True
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

        robots_present, robots_rules, sitemap_urls, sitemap_relative_url_count, sitemap_index_detected, sitemap_cross_host_child_count, sitemap_image_count, sitemap_deprecated_image_tag_count, sitemap_news_article_count, sitemap_news_stale_article_count, sitemap_news_missing_required_tags, sitemap_video_count, sitemap_video_missing_required_tags, sitemap_video_deprecated_tag_count, sitemap_hreflang_url_count, sitemap_hreflang_missing_self_ref, sitemap_urls_without_lastmod = self._fetch_site_controls(site_root)

        while queue and len(pages) < max_pages:
            url, depth = queue.popleft()
            if url in visited or depth > max_depth:
                continue
            visited.add(url)

            try:
                response = self.session.get(url, timeout=10)
                response_time_ms = int(response.elapsed.total_seconds() * 1000)
                redirect_hops = len(response.history)
                page_size_bytes = len(response.content)
                vary_accept_language = "accept-language" in response.headers.get("Vary", "").lower()
                if response.status_code >= 500:
                    self.logger.warning("HTTP 5xx error at %s. Slowing down crawl to avoid overloading server.", url)
                    time.sleep(5)
            except requests.RequestException as exc:
                crawl_errors.append(f"{url}: {exc}")
                continue

            content_type = response.headers.get("Content-Type", "")
            if "html" not in content_type.lower():
                continue

            parser = SEOHTMLParser(page_url=url)
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
                    links_without_anchor_text=parser.links_without_anchor_text,
                    links_with_generic_anchor=parser.links_with_generic_anchor,
                    external_links_without_rel=parser.external_links_without_rel,
                    non_indexable_file_links=parser.non_indexable_file_links,
                    links_with_hash_routing=parser.links_with_hash_routing,
                    script_count=parser.script_count,
                    stylesheet_count=parser.stylesheet_count,
                    has_viewport_meta=parser.has_viewport_meta,
                    has_favicon=parser.has_favicon,
                    vary_accept_language=vary_accept_language,
                    redirect_hops=redirect_hops,
                    page_size_bytes=page_size_bytes,
                    non_crawlable_href_links=parser.non_crawlable_href_links,
                    images_with_data_src=parser.images_with_data_src,
                    schema_has_article_date=parser.schema_has_article_date,
                    schema_parse_errors=parser.schema_parse_errors,
                    hreflang_link_count=parser.hreflang_link_count,
                    hreflang_missing_self_ref=parser.hreflang_link_count > 0 and not parser._hreflang_has_self_ref,
                    hreflang_relative_urls=parser.hreflang_relative_urls,
                    geo_meta_tags=parser.geo_meta_tags,
                )
            )

        return CrawlerReport(
            site_url=site_url,
            pages=pages,
            robots_txt_present=robots_present,
            robots_rules=robots_rules,
            sitemap_urls=sitemap_urls,
            sitemap_relative_url_count=sitemap_relative_url_count,
            sitemap_index_detected=sitemap_index_detected,
            sitemap_cross_host_child_count=sitemap_cross_host_child_count,
            sitemap_image_count=sitemap_image_count,
            sitemap_deprecated_image_tag_count=sitemap_deprecated_image_tag_count,
            sitemap_news_article_count=sitemap_news_article_count,
            sitemap_news_stale_article_count=sitemap_news_stale_article_count,
            sitemap_news_missing_required_tags=sitemap_news_missing_required_tags,
            sitemap_video_count=sitemap_video_count,
            sitemap_video_missing_required_tags=sitemap_video_missing_required_tags,
            sitemap_video_deprecated_tag_count=sitemap_video_deprecated_tag_count,
            sitemap_hreflang_url_count=sitemap_hreflang_url_count,
            sitemap_hreflang_missing_self_ref=sitemap_hreflang_missing_self_ref,
            sitemap_urls_without_lastmod=sitemap_urls_without_lastmod,
            crawl_errors=crawl_errors,
            discovered_at=datetime.now(timezone.utc).isoformat(),
        )

    def _fetch_site_controls(self, site_root: str) -> tuple[bool, list[str], list[str], int, bool, int, int, int, int, int, int, int, int, int, int, int, int]:
        robots_url = urljoin(site_root, "/robots.txt")
        robots_rules: list[str] = []
        sitemap_urls: list[str] = []
        robots_present = False
        sitemap_relative_url_count = 0
        sitemap_index_detected = False
        sitemap_cross_host_child_count = 0
        sitemap_image_count = 0
        sitemap_deprecated_image_tag_count = 0
        sitemap_news_article_count = 0
        sitemap_news_stale_article_count = 0
        sitemap_news_missing_required_tags = 0
        sitemap_video_count = 0
        sitemap_video_missing_required_tags = 0
        sitemap_video_deprecated_tag_count = 0

        _IMAGE_NS = "http://www.google.com/schemas/sitemap-image/1.1"
        _DEPRECATED_IMAGE_TAGS = {"caption", "geo_location", "title", "license"}
        _NEWS_NS = "http://www.google.com/schemas/sitemap-news/0.9"
        _VIDEO_NS = "http://www.google.com/schemas/sitemap-video/1.1"
        _DEPRECATED_VIDEO_TAGS = {"category", "gallery_loc", "price", "tvshow"}
        _XHTML_NS = "http://www.w3.org/1999/xhtml"
        sitemap_hreflang_url_count = 0
        sitemap_hreflang_missing_self_ref = 0
        sitemap_urls_without_lastmod = 0

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
        pending_sitemaps: list[str] = list(sitemap_urls)
        fetched_sitemaps: set[str] = set()

        while pending_sitemaps:
            sitemap_url = pending_sitemaps.pop(0)
            if sitemap_url in fetched_sitemaps:
                continue
            fetched_sitemaps.add(sitemap_url)
            try:
                response = self.session.get(sitemap_url, timeout=10)
                if not response.ok:
                    continue
                root = ElementTree.fromstring(response.text)
                root_tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
                namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

                if root_tag == "sitemapindex":
                    sitemap_index_detected = True
                    child_locs = root.findall("sm:sitemap/sm:loc", namespace)
                    if not child_locs:
                        child_locs = root.findall("sitemap/loc")
                    index_netloc = urlparse(sitemap_url).netloc
                    for loc in child_locs:
                        if not loc.text:
                            continue
                        child_url = loc.text.strip()
                        if not child_url.startswith(("http://", "https://")):
                            sitemap_relative_url_count += 1
                            continue
                        if urlparse(child_url).netloc != index_netloc:
                            sitemap_cross_host_child_count += 1
                        pending_sitemaps.append(child_url)
                else:
                    locs = root.findall(".//sm:loc", namespace)
                    if not locs:
                        locs = root.findall(".//loc")
                    for loc in locs:
                        if not loc.text:
                            continue
                        url_text = loc.text.strip()
                        if url_text.startswith(("http://", "https://")):
                            discovered_urls.append(url_text)
                        else:
                            sitemap_relative_url_count += 1
                    image_ns_prefix = f"{{{_IMAGE_NS}}}"
                    for elem in root.iter():
                        local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                        if elem.tag.startswith(image_ns_prefix):
                            if local == "loc":
                                sitemap_image_count += 1
                            elif local in _DEPRECATED_IMAGE_TAGS:
                                sitemap_deprecated_image_tag_count += 1
                    news_news_tag = f"{{{_NEWS_NS}}}news"
                    news_pub_date_tag = f"{{{_NEWS_NS}}}publication_date"
                    news_title_tag = f"{{{_NEWS_NS}}}title"
                    url_elems = root.findall("sm:url", namespace) or root.findall("url")
                    for url_elem in url_elems:
                        news_elem = url_elem.find(news_news_tag)
                        if news_elem is None:
                            continue
                        sitemap_news_article_count += 1
                        pub_date_elem = news_elem.find(news_pub_date_tag)
                        title_elem = news_elem.find(news_title_tag)
                        if pub_date_elem is None or title_elem is None:
                            sitemap_news_missing_required_tags += 1
                        elif pub_date_elem.text:
                            try:
                                pub_date = datetime.strptime(pub_date_elem.text.strip()[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                                if (datetime.now(timezone.utc) - pub_date).days > 2:
                                    sitemap_news_stale_article_count += 1
                            except Exception:
                                pass
                    lastmod_tag_sm = "sm:lastmod"
                    for url_elem in url_elems:
                        if url_elem.find(lastmod_tag_sm, namespace) is None and url_elem.find("lastmod") is None:
                            sitemap_urls_without_lastmod += 1
                    xhtml_link_tag = f"{{{_XHTML_NS}}}link"
                    for url_elem in url_elems:
                        loc_elem = url_elem.find("sm:loc", namespace) or url_elem.find("loc")
                        loc_text = loc_elem.text.strip() if loc_elem is not None and loc_elem.text else ""
                        hreflang_links = [
                            child for child in url_elem.findall(xhtml_link_tag)
                            if child.get("rel") == "alternate" and child.get("hreflang")
                        ]
                        if not hreflang_links:
                            continue
                        sitemap_hreflang_url_count += 1
                        hrefs = {child.get("href", "").strip() for child in hreflang_links}
                        if loc_text and loc_text not in hrefs:
                            sitemap_hreflang_missing_self_ref += 1
                    video_video_tag = f"{{{_VIDEO_NS}}}video"
                    video_required = {
                        f"{{{_VIDEO_NS}}}thumbnail_loc",
                        f"{{{_VIDEO_NS}}}title",
                        f"{{{_VIDEO_NS}}}description",
                    }
                    video_loc_tags = {f"{{{_VIDEO_NS}}}content_loc", f"{{{_VIDEO_NS}}}player_loc"}
                    for url_elem in url_elems:
                        for video_elem in url_elem.findall(video_video_tag):
                            sitemap_video_count += 1
                            child_tags = {child.tag for child in video_elem}
                            missing = not video_required.issubset(child_tags) or not child_tags & video_loc_tags
                            if missing:
                                sitemap_video_missing_required_tags += 1
                            for child in video_elem:
                                local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                                if child.tag.startswith(f"{{{_VIDEO_NS}}}") and local in _DEPRECATED_VIDEO_TAGS:
                                    sitemap_video_deprecated_tag_count += 1
            except Exception:
                continue

        return robots_present, robots_rules, sorted(set(discovered_urls)), sitemap_relative_url_count, sitemap_index_detected, sitemap_cross_host_child_count, sitemap_image_count, sitemap_deprecated_image_tag_count, sitemap_news_article_count, sitemap_news_stale_article_count, sitemap_news_missing_required_tags, sitemap_video_count, sitemap_video_missing_required_tags, sitemap_video_deprecated_tag_count, sitemap_hreflang_url_count, sitemap_hreflang_missing_self_ref, sitemap_urls_without_lastmod

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
