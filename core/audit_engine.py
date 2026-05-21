from __future__ import annotations

import json
from collections import defaultdict
from urllib.parse import urlparse
from typing import Any

from utils.models import AuditIssue, CrawlerReport, PageSnapshot


class AuditEngine:
    """Runs a practical technical SEO audit against the crawled Pipeleap site."""

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger
        self.pagespeed_config = config.get("integrations", {}).get("pagespeed", {})

    def run(self, crawl_report: CrawlerReport) -> list[AuditIssue]:
        issues: list[AuditIssue] = []
        pages = crawl_report.pages

        if not pages:
            issues.append(
                AuditIssue(
                    severity="Critical",
                    category="crawl",
                    url=crawl_report.site_url,
                    title="Site crawl returned no HTML pages",
                    description="The crawler could not fetch any HTML pages, so technical SEO checks are incomplete.",
                    fix_instructions="Verify the site is reachable from the runtime, confirm DNS/TLS, and rerun the crawl.",
                    impact_score=95.0,
                )
            )
            return issues

        if not crawl_report.robots_txt_present:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="robots",
                    url=f"{crawl_report.site_url.rstrip('/')}/robots.txt",
                    title="Missing robots.txt",
                    description="robots.txt was not detected during the crawl.",
                    fix_instructions="Add a robots.txt file that allows key public pages and references the sitemap.",
                    impact_score=58.0,
                    auto_fix_script="User-agent: *\nAllow: /\nSitemap: https://pipeleap.com/sitemap.xml\n",
                )
            )

        if not crawl_report.sitemap_urls:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="sitemap",
                    url=f"{crawl_report.site_url.rstrip('/')}/sitemap.xml",
                    title="Missing or unreadable sitemap",
                    description="No sitemap URLs were discovered from robots.txt or sitemap.xml.",
                    fix_instructions="Publish a sitemap containing canonical landing pages, blog posts, and product pages.",
                    impact_score=62.0,
                )
            )

        if crawl_report.robots_txt_present and not any(
            line.lower().startswith("sitemap:") for line in crawl_report.robots_rules
        ):
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="sitemap",
                    url=f"{crawl_report.site_url.rstrip('/')}/robots.txt",
                    title="robots.txt does not reference a sitemap",
                    description=(
                        "robots.txt is present but contains no Sitemap: directive. "
                        "Referencing the sitemap in robots.txt is a reliable passive discovery path — "
                        "Google reads it on every robots.txt fetch without requiring a manual Search Console submission."
                    ),
                    fix_instructions=(
                        "Add a Sitemap: line to robots.txt pointing to the absolute sitemap URL, e.g.:\n"
                        "Sitemap: https://pipeleap.com/sitemap.xml"
                    ),
                    impact_score=52.0,
                )
            )

        if len(crawl_report.sitemap_urls) > 50_000:
            issues.append(
                AuditIssue(
                    severity="High",
                    category="sitemap",
                    url=f"{crawl_report.site_url.rstrip('/')}/sitemap.xml",
                    title=f"Sitemap exceeds 50,000 URL limit ({len(crawl_report.sitemap_urls):,} URLs)",
                    description=(
                        f"The sitemap contains {len(crawl_report.sitemap_urls):,} URLs, exceeding the "
                        "50,000 URL per-file limit defined by the sitemaps protocol. "
                        "Google will stop processing the sitemap at the limit, leaving excess URLs undiscovered."
                    ),
                    fix_instructions=(
                        "Split the sitemap into multiple files (each ≤ 50,000 URLs, ≤ 50 MB uncompressed) "
                        "and create a sitemap index file that references them. "
                        "Submit the index file to Search Console."
                    ),
                    impact_score=75.0,
                )
            )

        if crawl_report.sitemap_relative_url_count > 0:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="sitemap",
                    url=f"{crawl_report.site_url.rstrip('/')}/sitemap.xml",
                    title=f"Sitemap contains relative URLs ({crawl_report.sitemap_relative_url_count} entries)",
                    description=(
                        f"{crawl_report.sitemap_relative_url_count} URL(s) in the sitemap are relative paths "
                        "rather than fully-qualified absolute URLs. "
                        "Google's sitemaps protocol requires absolute URLs — relative entries may be ignored entirely."
                    ),
                    fix_instructions=(
                        "Replace all relative sitemap entries with fully-qualified absolute URLs, "
                        "e.g. change /blog/post to https://pipeleap.com/blog/post."
                    ),
                    impact_score=60.0,
                )
            )

        if not self.pagespeed_config.get("api_key"):
            issues.append(
                AuditIssue(
                    severity="Critical",
                    category="core_web_vitals",
                    url=crawl_report.site_url,
                    title="PageSpeed API not configured — Core Web Vitals blind spot",
                    description=(
                        "LCP, CLS, and INP are confirmed Google ranking signals. Without the PageSpeed Insights API, "
                        "the audit cannot measure or flag CWV regressions. This creates a ranking blind spot "
                        "that cannot be resolved by server-response heuristics alone."
                    ),
                    fix_instructions=(
                        "Add integrations.pagespeed.api_key in config.yaml. "
                        "Get a free key at https://developers.google.com/speed/docs/insights/v5/get-started. "
                        "Once set, the audit will report LCP, CLS, and INP scores per page."
                    ),
                    impact_score=87.0,
                )
            )

        title_map: dict[str, list[str]] = defaultdict(list)
        meta_map: dict[str, list[str]] = defaultdict(list)
        content_map: dict[str, list[str]] = defaultdict(list)

        for page in pages:
            title_map[page.title].append(page.url)
            meta_map[page.meta_description].append(page.url)
            content_map[page.content_hash].append(page.url)
            issues.extend(self._page_level_issues(page))

        issues.extend(self._duplicate_issues(title_map, "title", "Title tag"))
        issues.extend(self._duplicate_issues(meta_map, "meta_description", "Meta description"))
        issues.extend(self._duplicate_issues(content_map, "content", "Page body"))

        return sorted(issues, key=lambda item: item.impact_score, reverse=True)

    def _page_level_issues(self, page: PageSnapshot) -> list[AuditIssue]:
        issues: list[AuditIssue] = []
        if page.status_code >= 400:
            issues.append(
                AuditIssue(
                    severity="Critical",
                    category="broken_page",
                    url=page.url,
                    title="Broken page response",
                    description=f"Page returned HTTP {page.status_code}.",
                    fix_instructions="Restore the page, redirect it to the canonical replacement, or remove internal references.",
                    impact_score=96.0,
                )
            )

        if not page.title:
            issues.append(
                self._metadata_issue(
                    page,
                    field_name="title",
                    title="Missing title tag",
                    impact_score=84.0,
                    suggestion=f"{page.h1 or 'Pipeleap'} | Pipeleap",
                )
            )
        elif len(page.title) < 30:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="metadata",
                    url=page.url,
                    title=f"Title too short ({len(page.title)} chars)",
                    description="AI-generated or auto-populated titles under 30 characters are unlikely to be descriptive enough for search snippets.",
                    fix_instructions="Expand the title to 50-65 characters with the primary keyword and brand name (e.g., 'Keyword | Pipeleap').",
                    impact_score=61.0,
                )
            )
        elif len(page.title) > 65:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="metadata",
                    url=page.url,
                    title=f"Title too long ({len(page.title)} chars)",
                    description="Titles over 65 characters are truncated in search results, causing the brand or CTA to be cut off.",
                    fix_instructions="Shorten the title to under 65 characters while keeping the primary keyword and brand name.",
                    impact_score=44.0,
                )
            )

        if not page.meta_description:
            issues.append(
                self._metadata_issue(
                    page,
                    field_name="meta_description",
                    title="Missing meta description",
                    impact_score=73.0,
                    suggestion="Write a 140-160 character description tied to the page keyword and CTA.",
                )
            )
        elif len(page.meta_description) < 70:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="metadata",
                    url=page.url,
                    title=f"Meta description too short ({len(page.meta_description)} chars)",
                    description="Short meta descriptions (under 70 characters) waste the snippet space and reduce click-through rates.",
                    fix_instructions="Expand to 140-160 characters with a keyword, value proposition, and CTA.",
                    impact_score=38.0,
                )
            )
        elif len(page.meta_description) > 160:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="metadata",
                    url=page.url,
                    title=f"Meta description too long ({len(page.meta_description)} chars)",
                    description="Meta descriptions over 160 characters are truncated by Google, cutting off the CTA.",
                    fix_instructions="Trim to under 160 characters. Put the CTA at the end for best snippet performance.",
                    impact_score=35.0,
                )
            )

        if not page.h1:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="heading",
                    url=page.url,
                    title="Missing H1",
                    description="The page does not expose a primary H1 heading.",
                    fix_instructions="Add one H1 that reflects the primary keyword and user intent.",
                    impact_score=60.0,
                )
            )

        if not page.canonical:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="canonical",
                    url=page.url,
                    title="Missing canonical",
                    description="The page does not define a canonical URL.",
                    fix_instructions="Add a self-referencing canonical tag to reduce duplicate indexing ambiguity.",
                    impact_score=55.0,
                )
            )

        if not page.has_viewport_meta:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="mobile",
                    url=page.url,
                    title="Missing viewport meta tag",
                    description='The page has no <meta name="viewport"> tag. Mobile browsers render it at desktop width, harming Core Web Vitals and mobile UX.',
                    fix_instructions='Add <meta name="viewport" content="width=device-width, initial-scale=1"> in the <head> of every page.',
                    impact_score=68.0,
                )
            )

        if page.meta_robots and "noindex" in page.meta_robots.lower():
            issues.append(
                AuditIssue(
                    severity="Critical",
                    category="indexing",
                    url=page.url,
                    title="Indexed page is marked noindex",
                    description="The crawler detected a noindex directive.",
                    fix_instructions="Remove noindex from pages that should rank, or confirm it is intentionally excluded.",
                    impact_score=92.0,
                )
            )

        if page.response_time_ms > 4000:
            issues.append(
                AuditIssue(
                    severity="Critical",
                    category="performance",
                    url=page.url,
                    title="Very slow page response",
                    description=f"HTML response time was {page.response_time_ms}ms.",
                    fix_instructions="Profile backend latency, cache HTML where possible, and defer heavy third-party scripts.",
                    impact_score=88.0,
                )
            )
        elif page.response_time_ms > 2500:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="performance",
                    url=page.url,
                    title="Slow page response",
                    description=f"HTML response time was {page.response_time_ms}ms.",
                    fix_instructions="Reduce server latency, optimize render path, and audit script weight.",
                    impact_score=63.0,
                )
            )

        if page.word_count > 0 and page.word_count < 300:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="thin_content",
                    url=page.url,
                    title="Thin content — below 300 words",
                    description=f"Page body contains only {page.word_count} words. Thin pages rarely satisfy user intent and are unlikely to be cited in AI Overviews.",
                    fix_instructions="Expand with unique expert insight, first-hand experience, or structured data that goes beyond what any AI model could generate without your input.",
                    impact_score=71.0,
                )
            )

        if page.image_count > 0 and page.images_without_alt > 0:
            ratio = page.images_without_alt / page.image_count
            severity = "Medium" if ratio >= 0.5 else "Low"
            issues.append(
                AuditIssue(
                    severity=severity,
                    category="accessibility",
                    url=page.url,
                    title=f"Images missing alt text ({page.images_without_alt}/{page.image_count})",
                    description=(
                        f"{page.images_without_alt} of {page.image_count} images lack alt attributes. "
                        "Alt text is required for screen readers, Google image indexing, and AI agents that parse the accessibility tree."
                    ),
                    fix_instructions="Add descriptive alt text to every image. Decorative images should use alt=\"\" to signal they can be skipped.",
                    impact_score=52.0 if severity == "Low" else 66.0,
                )
            )

        if not page.h1 and len(page.headings) > 0:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="heading_structure",
                    url=page.url,
                    title="Heading hierarchy starts below H1",
                    description="The page uses H2–H4 headings but has no H1. AI agents and screen readers rely on a logical heading tree starting at H1.",
                    fix_instructions="Add a single H1 that declares the primary topic. Subordinate headings should follow as H2 → H3.",
                    impact_score=58.0,
                )
            )

        if not page.schema_types:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="structured_data",
                    url=page.url,
                    title="No structured data (JSON-LD) detected",
                    description=(
                        "The page has no JSON-LD schema markup. Structured data is required for rich results "
                        "(FAQ, HowTo, Article, Product) and helps Google understand page context for AI Overviews."
                    ),
                    fix_instructions=(
                        "Add a relevant JSON-LD block in the <head>. For blog posts use Article or BlogPosting; "
                        "for product/landing pages use SoftwareApplication or Product; for FAQ sections use FAQPage."
                    ),
                    impact_score=53.0,
                )
            )

        if page.script_count > 10:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="javascript",
                    url=page.url,
                    title=f"High script count ({page.script_count} scripts) — JavaScript rendering risk",
                    description=(
                        f"The page loads {page.script_count} <script> tags. Pages that depend heavily on JavaScript "
                        "risk content being invisible to Googlebot if any script is unsupported or fails to execute. "
                        "Googlebot renders JavaScript in a second wave, which delays indexing."
                    ),
                    fix_instructions=(
                        "Ensure critical content (headings, body text, links) is present in the initial HTML response. "
                        "Audit scripts with the URL Inspection tool in Search Console to verify Googlebot renders the full page."
                    ),
                    impact_score=59.0,
                )
            )

        if page.links_without_anchor_text > 0:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="internal_linking",
                    url=page.url,
                    title=f"Links missing anchor text ({page.links_without_anchor_text} links)",
                    description=(
                        f"{page.links_without_anchor_text} links on this page have no visible anchor text or aria-label. "
                        "Googlebot uses anchor text to understand what the linked page is about — empty anchors pass no ranking signal."
                    ),
                    fix_instructions=(
                        "Add descriptive anchor text to every link. For image links, ensure the <img> has a relevant alt attribute. "
                        "For icon-only links (e.g. social icons), add aria-label describing the destination."
                    ),
                    impact_score=41.0,
                )
            )

        if page.links_with_generic_anchor > 0:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="internal_linking",
                    url=page.url,
                    title=f"Generic anchor text detected ({page.links_with_generic_anchor} links)",
                    description=(
                        f"{page.links_with_generic_anchor} link(s) on this page use generic anchor text "
                        "such as 'click here', 'read more', or 'here'. Generic anchors pass no keyword signal "
                        "to the linked page and give users no context about what they will find."
                    ),
                    fix_instructions=(
                        "Replace generic anchor text with a concise description of the linked page's content "
                        "(e.g. 'click here' → 'how to close deals faster'). "
                        "Good anchor text should make sense out of context."
                    ),
                    impact_score=48.0,
                )
            )

        url_path = urlparse(page.url).path
        if "_" in url_path:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="url_structure",
                    url=page.url,
                    title="URL contains underscores — use hyphens",
                    description=(
                        "Google treats hyphens as word separators but underscores join words into one token. "
                        "A URL like /my_page ranks 'mypage' not 'my page', reducing keyword match surface."
                    ),
                    fix_instructions=(
                        "Rename the URL path to use hyphens instead of underscores (e.g. /my-page). "
                        "Set up a 301 redirect from the old underscore URL to the new hyphen URL."
                    ),
                    impact_score=45.0,
                )
            )

        if url_path != url_path.lower():
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="url_structure",
                    url=page.url,
                    title="URL contains uppercase letters",
                    description=(
                        "Uppercase characters in URLs create duplicate-content risk: /Page and /page are "
                        "treated as different URLs by servers, splitting crawl budget and link equity."
                    ),
                    fix_instructions=(
                        "Normalize the URL path to lowercase and set up 301 redirects from mixed-case variants. "
                        "Configure the web server to enforce lowercase URL routing."
                    ),
                    impact_score=42.0,
                )
            )

        if page.external_links_without_rel > 3:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="outbound_links",
                    url=page.url,
                    title=f"Unqualified external links ({page.external_links_without_rel} links missing rel attribute)",
                    description=(
                        f"{page.external_links_without_rel} absolute external links on this page have no rel='nofollow', "
                        "rel='sponsored', or rel='ugc' attribute. Google's guidance requires qualifying outbound links "
                        "so PageRank is not unintentionally passed to unvetted third-party pages."
                    ),
                    fix_instructions=(
                        "Add rel='nofollow' to external links you have not editorially vouched for. "
                        "Use rel='sponsored' for paid/affiliate links and rel='ugc' for user-generated content links."
                    ),
                    impact_score=37.0,
                )
            )

        if page.non_indexable_file_links > 0:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="file_types",
                    url=page.url,
                    title=f"Links to non-indexable file types ({page.non_indexable_file_links} links)",
                    description=(
                        f"{page.non_indexable_file_links} link(s) on this page point to file types Google cannot index "
                        "(e.g. .zip, .exe, .mp3, .dmg). Google will follow these links but cannot extract or rank content "
                        "from them, so any link equity spent on them returns no search visibility."
                    ),
                    fix_instructions=(
                        "Replace direct file links with descriptive landing pages (e.g. a download page for a .zip, "
                        "or a podcast page for an .mp3). The landing page is indexable and can rank; "
                        "link the actual file from there."
                    ),
                    impact_score=33.0,
                )
            )

        if page.links_with_hash_routing > 0:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="url_structure",
                    url=page.url,
                    title=f"Hash-routing links detected ({page.links_with_hash_routing} links use #/ fragments)",
                    description=(
                        f"{page.links_with_hash_routing} link(s) on this page use hash-fragment routing "
                        "(e.g. href='#/route'). Google Search does not follow URL fragments, so these destinations "
                        "are invisible to Googlebot — they cannot be crawled, indexed, or ranked."
                    ),
                    fix_instructions=(
                        "Replace hash-based routing with the History API (pushState/replaceState) so each view "
                        "has a real, crawlable URL path. Update internal links to reference these real paths."
                    ),
                    impact_score=65.0,
                )
            )

        url_path_segments = urlparse(page.url).path.strip("/").split("/")
        non_descriptive_segments = [
            s for s in url_path_segments
            if s.isdigit() and len(s) >= 4 or (len(s) >= 32 and all(c in "0123456789abcdefABCDEF-" for c in s))
        ]
        if non_descriptive_segments:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="url_structure",
                    url=page.url,
                    title="URL path contains non-descriptive ID segments",
                    description=(
                        f"The URL path contains segment(s) that look like database IDs or UUIDs "
                        f"({', '.join(non_descriptive_segments[:3])}). ID-only URLs provide no keyword signal "
                        "and are harder for users and Google to understand than descriptive slugs."
                    ),
                    fix_instructions=(
                        "Replace numeric or UUID path segments with descriptive, hyphen-separated slugs "
                        "(e.g. /posts/12345 → /posts/how-to-close-deals-faster). "
                        "Set up 301 redirects from old ID URLs to new slug URLs."
                    ),
                    impact_score=40.0,
                )
            )

        if len(page.internal_links) == 0 and page.url.rstrip("/") != self.config.get("site", {}).get("site_url", "").rstrip("/"):
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="internal_linking",
                    url=page.url,
                    title="Page has no internal links out",
                    description="The page does not link deeper into the site, which weakens crawl flow and conversion routing.",
                    fix_instructions="Add contextual links to a product page, related cluster content, and one conversion-focused landing page.",
                    impact_score=34.0,
                )
            )

        return issues

    def _metadata_issue(
        self,
        page: PageSnapshot,
        field_name: str,
        title: str,
        impact_score: float,
        suggestion: str,
    ) -> AuditIssue:
        payload = json.dumps({"url": page.url, field_name: suggestion}, indent=2)
        return AuditIssue(
            severity="Critical" if field_name == "title" else "Medium",
            category="metadata",
            url=page.url,
            title=title,
            description=f"The page is missing a {field_name.replace('_', ' ')}.",
            fix_instructions=f"Add a unique {field_name.replace('_', ' ')} aligned to the primary keyword and CTA.",
            impact_score=impact_score,
            auto_fix_script=payload,
        )

    def _duplicate_issues(self, duplicates: dict[str, list[str]], category: str, label: str) -> list[AuditIssue]:
        issues: list[AuditIssue] = []
        for value, urls in duplicates.items():
            if not value or len(urls) <= 1:
                continue
            for url in urls[1:]:
                issues.append(
                    AuditIssue(
                        severity="Medium",
                        category=category,
                        url=url,
                        title=f"Duplicate {label.lower()}",
                        description=f"{label} duplicates another crawled page.",
                        fix_instructions=f"Rewrite the {label.lower()} to target the page's distinct keyword and intent.",
                        impact_score=57.0 if category != "content" else 69.0,
                    )
                )
        return issues
