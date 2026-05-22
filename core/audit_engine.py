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

        _current_agents: list[str] = []
        for _line in crawl_report.robots_rules:
            _lower = _line.lower().strip()
            if _lower.startswith("user-agent:"):
                _agent = _lower.split(":", 1)[1].strip()
                _current_agents.append(_agent)
            elif _lower == "disallow: /" and ("*" in _current_agents or "googlebot" in _current_agents):
                issues.append(
                    AuditIssue(
                        severity="Critical",
                        category="robots",
                        url=f"{crawl_report.site_url.rstrip('/')}/robots.txt",
                        title="robots.txt blocks all Googlebot crawling (Disallow: /)",
                        description=(
                            "The robots.txt file contains 'Disallow: /' under User-agent: * or User-agent: Googlebot, "
                            "which prevents Googlebot from crawling any page on the site. "
                            "This will remove all pages from Google's index over time."
                        ),
                        fix_instructions=(
                            "Remove or narrow the 'Disallow: /' rule. To allow all crawling: "
                            "'Allow: /'. To block only specific paths: 'Disallow: /admin/' "
                            "rather than blocking the entire site."
                        ),
                        impact_score=91.0,
                    )
                )
                break

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

        if crawl_report.sitemap_cross_host_child_count > 0:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="sitemap",
                    url=f"{crawl_report.site_url.rstrip('/')}/sitemap.xml",
                    title=f"Sitemap index references cross-host child sitemaps ({crawl_report.sitemap_cross_host_child_count})",
                    description=(
                        f"The sitemap index file references {crawl_report.sitemap_cross_host_child_count} child sitemap(s) "
                        "hosted on a different domain than the index itself. "
                        "Per the sitemaps protocol, referenced sitemaps must be on the same host as the index "
                        "unless cross-site submission is explicitly configured in Search Console."
                    ),
                    fix_instructions=(
                        "Move child sitemaps to the same host as the sitemap index, or set up cross-site sitemap "
                        "submission in Google Search Console by verifying ownership of each host and submitting "
                        "the index there."
                    ),
                    impact_score=55.0,
                )
            )

        total_page_images = sum(p.image_count for p in pages)
        if total_page_images > 0 and crawl_report.sitemap_image_count == 0:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="sitemap",
                    url=f"{crawl_report.site_url.rstrip('/')}/sitemap.xml",
                    title=f"No image sitemap detected ({total_page_images} images found on crawled pages)",
                    description=(
                        f"The crawled pages contain {total_page_images} images but the sitemap declares no "
                        "<image:image> entries. Google relies on image sitemaps to discover images loaded via "
                        "JavaScript or rendered after page load, which Googlebot may not see in the initial HTML pass."
                    ),
                    fix_instructions=(
                        "Add image sitemap extensions to the existing sitemap using the "
                        "xmlns:image=\"http://www.google.com/schemas/sitemap-image/1.1\" namespace. "
                        "For each <url> entry, nest <image:image><image:loc>https://...</image:loc></image:image> "
                        "for every key image on that page."
                    ),
                    impact_score=44.0,
                )
            )

        if crawl_report.sitemap_deprecated_image_tag_count > 0:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="sitemap",
                    url=f"{crawl_report.site_url.rstrip('/')}/sitemap.xml",
                    title=f"Deprecated image sitemap tags in use ({crawl_report.sitemap_deprecated_image_tag_count} occurrences)",
                    description=(
                        f"The sitemap uses {crawl_report.sitemap_deprecated_image_tag_count} deprecated image tag(s) "
                        "(<image:caption>, <image:geo_location>, <image:title>, or <image:license>). "
                        "Google removed these tags in May 2022 — they are ignored and add unnecessary sitemap weight."
                    ),
                    fix_instructions=(
                        "Remove all <image:caption>, <image:geo_location>, <image:title>, and <image:license> tags "
                        "from the sitemap. Only <image:image> and <image:loc> are currently supported."
                    ),
                    impact_score=30.0,
                )
            )

        if crawl_report.sitemap_news_missing_required_tags > 0:
            issues.append(
                AuditIssue(
                    severity="High",
                    category="sitemap",
                    url=f"{crawl_report.site_url.rstrip('/')}/sitemap.xml",
                    title=f"News sitemap entries missing required tags ({crawl_report.sitemap_news_missing_required_tags} entries)",
                    description=(
                        f"{crawl_report.sitemap_news_missing_required_tags} <news:news> entry/entries are missing "
                        "a required <news:publication_date> or <news:title> tag. "
                        "Google requires both tags on every news entry — incomplete entries may be rejected by Google News."
                    ),
                    fix_instructions=(
                        "Ensure every <news:news> element contains <news:publication>, <news:publication_date> "
                        "(in W3C format, e.g. 2024-01-15T09:00:00Z), and <news:title> (exact article title as it appears on the page). "
                        "Do not include author name or publication name inside <news:title>."
                    ),
                    impact_score=76.0,
                )
            )

        if crawl_report.sitemap_news_article_count > 1000:
            issues.append(
                AuditIssue(
                    severity="High",
                    category="sitemap",
                    url=f"{crawl_report.site_url.rstrip('/')}/sitemap.xml",
                    title=f"News sitemap exceeds 1,000 article limit ({crawl_report.sitemap_news_article_count} entries)",
                    description=(
                        f"The news sitemap contains {crawl_report.sitemap_news_article_count} <news:news> entries, "
                        "exceeding Google's hard limit of 1,000 per news sitemap file. "
                        "Entries beyond the limit are ignored by Google News."
                    ),
                    fix_instructions=(
                        "Split the news sitemap into multiple files, each containing ≤ 1,000 <news:news> entries. "
                        "Reference all split files from a sitemap index and submit the index to Search Console. "
                        "Also remove any entries older than two days — news sitemaps should only contain recent articles."
                    ),
                    impact_score=72.0,
                )
            )

        if crawl_report.sitemap_news_stale_article_count > 0:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="sitemap",
                    url=f"{crawl_report.site_url.rstrip('/')}/sitemap.xml",
                    title=f"News sitemap contains stale articles ({crawl_report.sitemap_news_stale_article_count} entries older than 2 days)",
                    description=(
                        f"{crawl_report.sitemap_news_stale_article_count} article(s) in the news sitemap have a "
                        "<news:publication_date> more than 2 days old. "
                        "Google's news sitemap spec requires only articles published within the last two days — "
                        "stale entries are ignored and bloat the sitemap unnecessarily."
                    ),
                    fix_instructions=(
                        "Remove <url> entries (or their <news:news> metadata blocks) for articles older than 48 hours. "
                        "Automate this with a daily job that regenerates the news sitemap from only the most recent articles."
                    ),
                    impact_score=57.0,
                )
            )

        if not any(p.has_favicon for p in pages):
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="branding",
                    url=crawl_report.site_url,
                    title="No favicon detected on any crawled page",
                    description=(
                        "No <link rel='icon'> (or apple-touch-icon) tag was found across crawled pages. "
                        "Google displays the site favicon next to search results — a missing favicon "
                        "means Google falls back to a generic globe icon, reducing brand recognition in SERPs."
                    ),
                    fix_instructions=(
                        "Add <link rel='icon' href='/favicon.ico'> in the <head> of every page. "
                        "Use a square image at least 48x48px. Ensure the favicon file is not blocked by robots.txt "
                        "so Googlebot-Image can crawl it."
                    ),
                    impact_score=38.0,
                )
            )

        if not any("WebSite" in p.schema_types for p in pages):
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="structured_data",
                    url=crawl_report.site_url,
                    title="No WebSite structured data detected",
                    description=(
                        "No WebSite JSON-LD schema was found across crawled pages. "
                        "Google uses WebSite structured data (with name and url properties) to determine "
                        "the preferred site name shown in search results. Without it, Google may display "
                        "an inaccurate or sub-optimal site name."
                    ),
                    fix_instructions=(
                        "Add WebSite JSON-LD to the homepage only:\n"
                        '{"@context":"https://schema.org","@type":"WebSite",'
                        '"name":"Pipeleap","url":"https://pipeleap.com"}\n'
                        "Only one WebSite schema per domain is supported."
                    ),
                    impact_score=36.0,
                )
            )

        from urllib.parse import urlparse as _urlparse
        _GENERIC_TLDS = {
            ".com", ".net", ".org", ".io", ".co", ".app", ".dev", ".ai",
            ".tech", ".online", ".site", ".store", ".shop", ".info", ".biz",
        }
        site_host = _urlparse(crawl_report.site_url).netloc.lower().lstrip("www.")
        site_tld = "." + site_host.rsplit(".", 1)[-1] if "." in site_host else ""
        site_is_cctld = site_tld not in _GENERIC_TLDS and len(site_tld) <= 3
        if site_is_cctld and not any(p.hreflang_link_count > 0 for p in pages):
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="international",
                    url=crawl_report.site_url,
                    title=f"ccTLD domain ({site_tld}) without hreflang annotations",
                    description=(
                        f"The site uses a country-code TLD ({site_tld}), which signals geo-targeting to Google. "
                        "However, no hreflang annotations were detected on any crawled page. "
                        "If the site has language or regional variants, hreflang is required to prevent "
                        "duplicate content penalties and ensure the correct version appears in each market."
                    ),
                    fix_instructions=(
                        "If the site targets only one country/language, no action needed — the ccTLD is sufficient. "
                        "If you have language variants (e.g. English + local language), add "
                        "<link rel='alternate' hreflang='[lang]' href='[url]'> to every page variant "
                        "and ensure each page includes a self-referencing hreflang entry."
                    ),
                    impact_score=42.0,
                )
            )

        if crawl_report.sitemap_urls and crawl_report.sitemap_urls_without_lastmod == len(crawl_report.sitemap_urls):
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="sitemap",
                    url=f"{crawl_report.site_url.rstrip('/')}/sitemap.xml",
                    title="No sitemap URLs have a <lastmod> tag",
                    description=(
                        f"The sitemap contains {len(crawl_report.sitemap_urls)} URL(s) but none include a "
                        "<lastmod> tag. Google uses <lastmod> to detect updated content and prioritize recrawls — "
                        "without it, Google must discover updates through its own crawl schedule, "
                        "which can delay indexing of new or changed pages."
                    ),
                    fix_instructions=(
                        "Add a <lastmod> tag to every <url> entry in the sitemap, set to the date the page "
                        "was last meaningfully updated (e.g. <lastmod>2024-06-15</lastmod>). "
                        "Use W3C date format (YYYY-MM-DD or YYYY-MM-DDThh:mm:ss+TZD). "
                        "Automate this so the value reflects real content changes, not the sitemap generation time."
                    ),
                    impact_score=43.0,
                )
            )

        if crawl_report.sitemap_hreflang_missing_self_ref > 0:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="sitemap",
                    url=f"{crawl_report.site_url.rstrip('/')}/sitemap.xml",
                    title=f"Sitemap hreflang URLs missing self-referencing entry ({crawl_report.sitemap_hreflang_missing_self_ref} URLs)",
                    description=(
                        f"{crawl_report.sitemap_hreflang_missing_self_ref} URL(s) in the sitemap declare "
                        "<xhtml:link rel=\"alternate\" hreflang=\"...\"> annotations but do not include a "
                        "self-referencing entry pointing back to the URL itself. "
                        "Google's hreflang spec requires every URL in a localized set to list all alternate "
                        "versions including itself — without the self-reference, the annotation set is incomplete "
                        "and Google may ignore the hreflang signals for that URL."
                    ),
                    fix_instructions=(
                        "For every <url> that uses <xhtml:link rel=\"alternate\">, add an entry where href matches "
                        "the URL's own <loc> value, with the appropriate hreflang language code. "
                        "Example: <xhtml:link rel=\"alternate\" hreflang=\"en\" href=\"https://example.com/page.html\"/> "
                        "on the URL https://example.com/page.html itself."
                    ),
                    impact_score=63.0,
                )
            )

        if crawl_report.sitemap_video_missing_required_tags > 0:
            issues.append(
                AuditIssue(
                    severity="High",
                    category="sitemap",
                    url=f"{crawl_report.site_url.rstrip('/')}/sitemap.xml",
                    title=f"Video sitemap entries missing required tags ({crawl_report.sitemap_video_missing_required_tags} entries)",
                    description=(
                        f"{crawl_report.sitemap_video_missing_required_tags} <video:video> entry/entries are missing "
                        "one or more required tags. Google requires <video:thumbnail_loc>, <video:title>, "
                        "<video:description>, and at least one of <video:content_loc> or <video:player_loc> on "
                        "every video entry — incomplete entries may be rejected from video search results."
                    ),
                    fix_instructions=(
                        "Ensure every <video:video> element contains: <video:thumbnail_loc> (absolute URL to thumbnail), "
                        "<video:title> (video title, HTML-escaped), <video:description> (max 2048 chars), and either "
                        "<video:content_loc> (direct video file URL) or <video:player_loc> (embed player URL). "
                        "For YouTube/Vimeo embeds use <video:player_loc> with the embed URL."
                    ),
                    impact_score=74.0,
                )
            )

        if crawl_report.sitemap_video_deprecated_tag_count > 0:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="sitemap",
                    url=f"{crawl_report.site_url.rstrip('/')}/sitemap.xml",
                    title=f"Deprecated video sitemap tags in use ({crawl_report.sitemap_video_deprecated_tag_count} occurrences)",
                    description=(
                        f"The sitemap uses {crawl_report.sitemap_video_deprecated_tag_count} deprecated video tag(s) "
                        "(<video:category>, <video:gallery_loc>, <video:price>, or <video:tvshow>). "
                        "Google removed these tags in May 2022 — they are ignored and add unnecessary sitemap weight."
                    ),
                    fix_instructions=(
                        "Remove all <video:category>, <video:gallery_loc>, <video:price>, and <video:tvshow> tags "
                        "from the video sitemap. Also remove the autoplay and allow_embed attributes from "
                        "<video:player_loc> if present."
                    ),
                    impact_score=31.0,
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
        elif page.canonical and not page.canonical.startswith(("http://", "https://")):
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="canonical",
                    url=page.url,
                    title="Canonical URL is a relative path",
                    description=(
                        f"The canonical tag value '{page.canonical}' is a relative URL. "
                        "Google supports relative canonicals but they risk resolving incorrectly "
                        "on staging or mirror domains, potentially canonicalising to the wrong host."
                    ),
                    fix_instructions=(
                        "Replace the relative canonical with a fully-qualified absolute URL, "
                        f"e.g. <link rel=\"canonical\" href=\"{page.url}\">."
                    ),
                    impact_score=46.0,
                )
            )
        elif page.canonical.startswith("http://") and page.url.startswith("https://"):
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="canonical",
                    url=page.url,
                    title="Canonical points to HTTP while page is served over HTTPS",
                    description=(
                        f"The page is served over HTTPS but its canonical tag points to the HTTP version "
                        f"('{page.canonical}'). Google prefers HTTPS as canonical — an HTTP canonical "
                        "overrides that preference and may cause the HTTP version to be indexed instead."
                    ),
                    fix_instructions=(
                        "Update the canonical tag to reference the HTTPS URL: "
                        f"<link rel=\"canonical\" href=\"{page.url}\">."
                    ),
                    impact_score=61.0,
                )
            )
        if page.canonical and "#" in page.canonical:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="canonical",
                    url=page.url,
                    title="Canonical URL contains a URL fragment (#)",
                    description=(
                        f"The canonical tag value '{page.canonical}' contains a # fragment. "
                        "Google does not support URL fragments in canonical tags — the fragment is ignored, "
                        "which may cause the wrong URL to be treated as canonical."
                    ),
                    fix_instructions=(
                        "Remove the fragment from the canonical URL. Canonical tags should reference "
                        "the base URL without any # anchor, e.g. strip '#section' from the href."
                    ),
                    impact_score=44.0,
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

        _ARTICLE_SCHEMA_TYPES = {"Article", "NewsArticle", "BlogPosting", "TechArticle", "ScholarlyArticle", "Report"}
        if any(t in _ARTICLE_SCHEMA_TYPES for t in page.schema_types) and not page.schema_has_article_date:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="structured_data",
                    url=page.url,
                    title="Article schema missing datePublished / dateModified",
                    description=(
                        "The page declares an Article (or NewsArticle/BlogPosting) schema type but the JSON-LD "
                        "contains no datePublished or dateModified property. "
                        "Google uses these dates to display byline dates in search results and to determine "
                        "content freshness — missing dates may cause Google to infer an incorrect publication date."
                    ),
                    fix_instructions=(
                        "Add datePublished and dateModified to the Article JSON-LD in ISO 8601 format with timezone: "
                        '"datePublished": "2024-06-01T09:00:00+00:00", '
                        '"dateModified": "2024-06-15T12:00:00+00:00". '
                        "Ensure the dates match the visible date shown on the page."
                    ),
                    impact_score=62.0,
                )
            )

        if page.schema_parse_errors > 0:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="structured_data",
                    url=page.url,
                    title=f"Malformed JSON-LD detected ({page.schema_parse_errors} block(s) failed to parse)",
                    description=(
                        f"{page.schema_parse_errors} <script type='application/ld+json'> block(s) on this page "
                        "contain invalid JSON that could not be parsed. Google cannot process malformed structured "
                        "data — the page loses any rich result eligibility those blocks were intended to provide."
                    ),
                    fix_instructions=(
                        "Validate all JSON-LD blocks using the Schema Markup Validator at "
                        "https://validator.schema.org or the Rich Results Test. "
                        "Common errors: unescaped quotes inside string values, trailing commas, "
                        "or invalid Unicode characters. Fix syntax errors and retest."
                    ),
                    impact_score=45.0,
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

        if page.hreflang_missing_self_ref:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="international",
                    url=page.url,
                    title="hreflang annotations missing self-referencing entry",
                    description=(
                        "The page declares hreflang alternate links but does not include a self-referencing "
                        "entry pointing back to its own URL. Google requires that every URL in a hreflang "
                        "set references itself — without the self-reference the annotation set may be ignored."
                    ),
                    fix_instructions=(
                        "Add a <link rel='alternate' hreflang='[lang]' href='[this-page-url]'> entry "
                        "to the hreflang block on this page, where [lang] is the language code for this "
                        "version and [this-page-url] is the canonical URL of this page."
                    ),
                    impact_score=64.0,
                )
            )

        if page.hreflang_relative_urls > 0:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="international",
                    url=page.url,
                    title=f"hreflang tags use relative URLs ({page.hreflang_relative_urls} links)",
                    description=(
                        f"{page.hreflang_relative_urls} hreflang <link> tag(s) on this page use relative "
                        "href values instead of fully-qualified absolute URLs. Google requires absolute URLs "
                        "with protocol in hreflang annotations — relative paths may resolve incorrectly "
                        "across mirrors or staging environments."
                    ),
                    fix_instructions=(
                        "Replace all relative hreflang hrefs with absolute URLs including protocol and host, "
                        "e.g. change href='/de/page' to href='https://example.com/de/page'."
                    ),
                    impact_score=47.0,
                )
            )

        if page.geo_meta_tags > 0:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="international",
                    url=page.url,
                    title=f"Geotargeting meta tags detected ({page.geo_meta_tags} tags ignored by Google)",
                    description=(
                        f"The page contains {page.geo_meta_tags} geotargeting meta tag(s) such as "
                        "geo.position, geo.region, ICBM, or distribution. "
                        "Google explicitly ignores these tags — they add HTML weight with no SEO benefit."
                    ),
                    fix_instructions=(
                        "Remove geo.position, geo.region, geo.placename, ICBM, and distribution meta tags. "
                        "Use hreflang annotations or country-code domains/subdirectories to signal "
                        "geo-targeting to Google instead."
                    ),
                    impact_score=28.0,
                )
            )

        if page.non_crawlable_href_links > 0:
            issues.append(
                AuditIssue(
                    severity="Low",
                    category="internal_linking",
                    url=page.url,
                    title=f"Non-crawlable navigation links ({page.non_crawlable_href_links} links use javascript: or void())",
                    description=(
                        f"{page.non_crawlable_href_links} link(s) on this page use href='javascript:...' or "
                        "href='void(...)'. Googlebot requires <a href='...'> with a real URL to follow a link — "
                        "JavaScript-protocol hrefs are never crawled, so any pages reachable only through "
                        "these links will not be discovered or indexed."
                    ),
                    fix_instructions=(
                        "Replace javascript: and void() hrefs with real URL paths. "
                        "If the link triggers an action, use a <button> element for the action and a "
                        "separate <a href='/path'> for any page navigation. "
                        "For SPA routing, use the History API (pushState) with real URL paths."
                    ),
                    impact_score=47.0,
                )
            )

        if page.images_with_data_src > 0:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="lazy_loading",
                    url=page.url,
                    title=f"Images using custom data-src lazy-loading ({page.images_with_data_src} images)",
                    description=(
                        f"{page.images_with_data_src} image(s) on this page have a data-src attribute but no "
                        "real src attribute. Custom JavaScript lazy-loaders that swap data-src → src on scroll "
                        "are invisible to Googlebot, which does not interact with pages. "
                        "These images will not appear in Google Image Search and their alt text "
                        "won't contribute to page relevance signals."
                    ),
                    fix_instructions=(
                        "Use the browser-native lazy-loading attribute instead: "
                        "<img src='image.jpg' loading='lazy' alt='...'> — this keeps a real src attribute "
                        "so Googlebot can discover the image, while modern browsers defer loading until "
                        "the image enters the viewport. Alternatively use the IntersectionObserver API "
                        "with a valid src fallback."
                    ),
                    impact_score=58.0,
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

        if page.is_soft_404:
            issues.append(
                AuditIssue(
                    severity="High",
                    category="indexing",
                    url=page.url,
                    title="Soft 404 — page returns 200 but renders error content",
                    description=(
                        "The page returns HTTP 200 (success) but the rendered content signals that the page "
                        "does not exist or has an error. Google's algorithms detect this and exclude the page "
                        "from search results. Users arriving from search see a broken experience."
                    ),
                    fix_instructions=(
                        "If the content is genuinely gone: return a real 404 or 410 status code. "
                        "If the page should exist: fix the server error causing the empty/error render. "
                        "If the page moved: return a 301 redirect to the new URL. "
                        "Use the URL Inspection tool in Search Console to verify the fix."
                    ),
                    impact_score=82.0,
                )
            )

        if page.has_fullscreen_overlay:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="page_experience",
                    url=page.url,
                    title="Fullscreen overlay / interstitial detected",
                    description=(
                        "A large fixed or absolute-positioned element was detected covering most of the viewport "
                        "on page load. Google penalises intrusive interstitials that obstruct content — "
                        "they also make it harder for Googlebot to understand the page's main content."
                    ),
                    fix_instructions=(
                        "Replace fullscreen overlays with smaller banners that take up a fraction of the screen. "
                        "Age gates and legally required interstitials are exempt — use overlay-on-page rather than "
                        "a separate gate page. Cookie consent banners should be slim and dismissible. "
                        "Verify with the URL Inspection tool that Googlebot can see the main content."
                    ),
                    impact_score=67.0,
                )
            )

        if page.vary_accept_language and page.hreflang_link_count == 0:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="international",
                    url=page.url,
                    title="Page serves different content by Accept-Language but has no hreflang annotations",
                    description=(
                        "The server sends a Vary: Accept-Language response header, indicating the page "
                        "content changes based on the visitor's language preference. However, no hreflang "
                        "alternate links are declared. Googlebot crawls without an Accept-Language header "
                        "(originating from the US), so it may only ever see one language version — "
                        "other language variants will be invisible to Google."
                    ),
                    fix_instructions=(
                        "Either (a) switch to separate URLs per language and annotate with hreflang, or "
                        "(b) ensure Googlebot can access all language versions by using geo-distributed "
                        "crawling hints. The recommended approach is separate locale URLs: "
                        "example.com/en/, example.com/de/, each with hreflang self-references and alternates."
                    ),
                    impact_score=61.0,
                )
            )

        if page.page_size_bytes > 100_000:
            size_kb = page.page_size_bytes // 1024
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="crawl_efficiency",
                    url=page.url,
                    title=f"Large HTML page ({size_kb} KB) — crawl budget drain",
                    description=(
                        f"The HTML response for this page is {size_kb} KB. "
                        "Google's crawlers are limited by bandwidth and time per crawl session — "
                        "oversized HTML consumes disproportionate crawl budget per URL and slows "
                        "Googlebot's ability to discover and index other pages on the site."
                    ),
                    fix_instructions=(
                        "Reduce HTML payload: remove inline scripts and styles (move to external files), "
                        "avoid embedding large data blobs or base64 images in HTML, "
                        "enable server-side gzip/Brotli compression, and trim unnecessary markup. "
                        "Target under 100 KB for the raw HTML response."
                    ),
                    impact_score=54.0,
                )
            )

        if page.redirect_hops >= 2:
            issues.append(
                AuditIssue(
                    severity="Medium",
                    category="crawl_efficiency",
                    url=page.url,
                    title=f"Redirect chain detected ({page.redirect_hops} hops to reach this URL)",
                    description=(
                        f"Reaching this URL required following {page.redirect_hops} redirect(s). "
                        "Long redirect chains slow down Googlebot — each hop costs crawl budget and adds latency. "
                        "Google recommends keeping redirect chains to a single hop wherever possible."
                    ),
                    fix_instructions=(
                        "Collapse the redirect chain to a single 301 pointing directly from the original URL "
                        "to the final destination. Update any internal links and sitemap entries to point "
                        "directly to the canonical URL to avoid the chain entirely."
                    ),
                    impact_score=56.0,
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
