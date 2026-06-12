from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


class CMSConnector:
    """Publishes generated assets either to disk or a webhook endpoint."""

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.logger = logger
        self.config = config.get("integrations", {}).get("cms", {})
        self.site_url = config.get("site", {}).get("site_url", "")

    def publish_assets(self, run_directory: str, assets: list[Any]) -> dict[str, Any]:
        mode = self.config.get("mode", "filesystem")
        if mode == "webhook" and self.config.get("webhook_url"):
            return self._publish_via_webhook(assets)
        
        result = self._publish_to_filesystem(run_directory, assets)
        self._update_sitemap_and_robots(result["publish_root"])
        return result

    def _publish_to_filesystem(self, run_directory: str, assets: list[Any]) -> dict[str, Any]:
        configured_root = self.config.get("publish_dir", "")
        publish_root = Path(configured_root) if configured_root else Path(run_directory) / "published"
        if not publish_root.is_absolute():
            publish_root = Path(run_directory) / publish_root
        publish_root.mkdir(parents=True, exist_ok=True)
        count = 0

        for asset in assets:
            slug = getattr(asset, "slug", "asset").strip("/") or "asset"
            asset_dir = publish_root / slug
            asset_dir.mkdir(parents=True, exist_ok=True)
            markdown_path = asset_dir / "index.md"
            metadata_path = asset_dir / "metadata.json"

            # Inject approved internal link suggestions directly into markdown body
            body = getattr(asset, "body_markdown", "")
            suggestions = getattr(asset, "internal_link_suggestions", [])
            if suggestions:
                body = self._inject_internal_links(body, suggestions)
                applied = sum(1 for s in suggestions if s.anchor_text.lower() in body.lower())
                self.logger.debug("Internal links injected: %d/%d for %s", applied, len(suggestions), slug)

            markdown_path.write_text(body, encoding="utf-8")
            metadata_path.write_text(
                json.dumps(
                    {
                        "slug": getattr(asset, "slug", ""),
                        "page_type": getattr(asset, "page_type", ""),
                        "seo_title": getattr(asset, "seo_title", ""),
                        "meta_description": getattr(asset, "meta_description", ""),
                        "schema_markup": getattr(asset, "schema_markup", []),
                        "source_keywords": getattr(asset, "source_keywords", []),
                        "internal_link_suggestions": [
                            suggestion.to_dict() if hasattr(suggestion, "to_dict") else suggestion
                            for suggestion in getattr(asset, "internal_link_suggestions", [])
                        ],
                        "eeat_notes": getattr(asset, "eeat_notes", []),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            asset.publish_path = str(markdown_path)
            count += 1

        return {"mode": "filesystem", "published_count": count, "publish_root": str(publish_root)}

    # Pages that have confirmed React routes in App.tsx.
    # Only these URLs are written to sitemap.xml.
    # Blog/glossary slugs are appended dynamically from the actual data files.
    _STATIC_PAGES = [
        ("/",               "1.0", "daily"),
        ("/services",       "0.9", "weekly"),
        ("/how-it-works",   "0.9", "weekly"),
        ("/sales-ops-audit",      "0.9", "weekly"),
        ("/pricing",        "0.9", "weekly"),
        ("/about",          "0.8", "monthly"),
        ("/contact",        "0.8", "monthly"),
        ("/faq",            "0.8", "monthly"),
        ("/blog",           "0.8", "daily"),
        ("/glossary",       "0.9", "monthly"),
        ("/tools",          "0.9", "weekly"),
        ("/case-studies",   "0.9", "weekly"),
        ("/terms",          "0.3", "monthly"),
        # Blog articles that exist in src/data/blog-articles.ts
        ("/blog/why-your-pipeline-looks-full-but-rarely-converts", "0.8", "monthly"),
        ("/blog/the-hidden-reason-deals-dont-move",                "0.8", "monthly"),
        ("/blog/why-outbound-effort-gets-wasted",                  "0.8", "monthly"),
        ("/blog/the-gap-between-activity-and-revenue",             "0.8", "monthly"),
        ("/blog/why-forecasting-keeps-breaking",                   "0.8", "monthly"),
        ("/blog/your-gtm-strategy-is-a-document-not-a-system",     "0.8", "monthly"),
        ("/blog/what-your-gtm-motion-looks-like-from-the-buyers-side", "0.8", "monthly"),
        ("/blog/buying-signals-are-not-what-most-teams-think-they-are", "0.8", "monthly"),
        ("/blog/the-timing-problem-nobody-talks-about-in-outbound", "0.8", "monthly"),
        # Glossary terms that exist in src/data/glossary-terms.ts
        ("/glossary/workflow-orchestration",      "0.8", "monthly"),
        ("/glossary/outbound-automation",         "0.8", "monthly"),
        ("/glossary/signal-based-outbound",       "0.8", "monthly"),
        ("/glossary/pipeline-generation",         "0.8", "monthly"),
        ("/glossary/revenue-operations",          "0.8", "monthly"),
        ("/glossary/ideal-customer-profile",      "0.8", "monthly"),
        ("/glossary/sales-qualified-lead",        "0.8", "monthly"),
        ("/glossary/marketing-qualified-lead",    "0.8", "monthly"),
        ("/glossary/crm-automation",              "0.8", "monthly"),
        ("/glossary/sdr-automation",              "0.8", "monthly"),
        ("/glossary/lead-enrichment",             "0.8", "monthly"),
        ("/glossary/intent-data",                 "0.8", "monthly"),
        ("/glossary/buying-signals",              "0.8", "monthly"),
        ("/glossary/account-based-marketing",     "0.8", "monthly"),
        ("/glossary/cold-email-outreach",         "0.8", "monthly"),
        ("/glossary/email-deliverability",        "0.8", "monthly"),
        ("/glossary/ai-sdr",                      "0.8", "monthly"),
        ("/glossary/product-led-growth",          "0.8", "monthly"),
        ("/glossary/go-to-market-strategy",       "0.8", "monthly"),
        ("/glossary/annual-recurring-revenue",    "0.8", "monthly"),
        ("/glossary/monthly-recurring-revenue",   "0.8", "monthly"),
        ("/glossary/customer-acquisition-cost",   "0.8", "monthly"),
        ("/glossary/customer-lifetime-value",     "0.8", "monthly"),
        ("/glossary/net-revenue-retention",       "0.8", "monthly"),
        ("/glossary/sales-cadence",               "0.8", "monthly"),
        ("/glossary/outreach-personalization",    "0.8", "monthly"),
        ("/glossary/content-marketing",           "0.8", "monthly"),
        ("/glossary/conversion-rate-optimization","0.8", "monthly"),
        ("/glossary/sales-engagement-platform",   "0.8", "monthly"),
    ]

    # Prefix used when backfilling internal links — NOT used for sitemap.
    _SEO_URL_PREFIX = "/blog"

    def _update_sitemap_and_robots(self, publish_root_str: str) -> None:
        publish_root = Path(publish_root_str)
        # publish_dir is .../pipeleap-launchpad/src/data/seo
        # public_dir is .../pipeleap-launchpad/public
        public_dir = publish_root.parents[2] / "public"

        if not public_dir.exists():
            self.logger.warning(f"Public directory not found at {public_dir}. Skipping sitemap generation.")
            return

        self.logger.info(f"Updating sitemap.xml in {public_dir}")

        today = datetime.now().strftime("%Y-%m-%d")
        site_url = self.site_url.rstrip("/")

        # hreflang alternate links for all major English-speaking markets
        _hreflang_tags = lambda loc: "\n".join([
            f'    <xhtml:link rel="alternate" hreflang="x-default" href="{loc}"/>',
            f'    <xhtml:link rel="alternate" hreflang="en" href="{loc}"/>',
            f'    <xhtml:link rel="alternate" hreflang="en-us" href="{loc}"/>',
            f'    <xhtml:link rel="alternate" hreflang="en-gb" href="{loc}"/>',
            f'    <xhtml:link rel="alternate" hreflang="en-au" href="{loc}"/>',
            f'    <xhtml:link rel="alternate" hreflang="en-ca" href="{loc}"/>',
            f'    <xhtml:link rel="alternate" hreflang="en-in" href="{loc}"/>',
            f'    <xhtml:link rel="alternate" hreflang="en-sg" href="{loc}"/>',
        ])

        sitemap_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
            '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
        ]

        # 1. Static / core pages — always present, highest priority
        for path, priority, changefreq in self._STATIC_PAGES:
            loc = f"{site_url}{path}" if path != "/" else f"{site_url}/"
            sitemap_lines.extend([
                "  <url>",
                f"    <loc>{loc}</loc>",
                _hreflang_tags(loc),
                f"    <lastmod>{today}</lastmod>",
                f"    <changefreq>{changefreq}</changefreq>",
                f"    <priority>{priority}</priority>",
                "  </url>",
            ])

        # 2. Generated SEO content.
        #
        # IMPORTANT: generated pages are stored in src/data/seo/ as markdown/JSON
        # research artifacts. They are NOT wired to any React route in App.tsx and
        # therefore return a 404 (NotFound) for every URL. Adding them to the sitemap
        # causes Google to crawl, find 404s, and flag them in Search Console coverage.
        #
        # Generated pages are intentionally EXCLUDED from sitemap.xml.
        # To surface a generated page as a real indexed URL:
        #   1. Add its slug to src/data/blog-articles.ts (blog content pipeline), OR
        #   2. Add a dedicated React route for it in App.tsx.
        # Until one of those is done, the page must not appear in the sitemap.

        sitemap_lines.append("</urlset>")

        sitemap_path = public_dir / "sitemap.xml"
        sitemap_path.write_text("\n".join(sitemap_lines), encoding="utf-8")
        self.logger.info(f"sitemap.xml written: {len(self._STATIC_PAGES)} static pages (generated pages excluded — no React routes).")

        # robots.txt — allow all bots including AI crawlers; point at sitemap.
        robots_path = public_dir / "robots.txt"
        robots_content = "\n".join([
            "User-agent: *",
            "Allow: /",
            "",
            "# Allow major AI crawlers so Pipeleap content is indexed by LLMs",
            "User-agent: GPTBot",
            "Allow: /",
            "",
            "User-agent: ClaudeBot",
            "Allow: /",
            "",
            "User-agent: Google-Extended",
            "Allow: /",
            "",
            "User-agent: PerplexityBot",
            "Allow: /",
            "",
            "User-agent: FacebookBot",
            "Allow: /",
            "",
            f"Sitemap: {site_url}/sitemap.xml",
        ])
        robots_path.write_text(robots_content, encoding="utf-8")
        self.logger.info("robots.txt updated with AI-crawler allowances.")

    def _inject_internal_links(self, body: str, suggestions: list[Any]) -> str:
        """
        Injects internal link suggestions into markdown body text.

        Strategy per suggestion:
        - Find the first plain-text occurrence of the anchor_text in the body.
        - Replace it with a markdown link [anchor_text](target_url).
        - Only replace the first occurrence to avoid over-linking.
        - Skip if the anchor is already wrapped in a markdown link or code block.
        - Sort suggestions by confidence descending so highest-value links
          are applied first when anchor texts overlap.
        """
        import re

        # Sort highest confidence first
        ordered = sorted(
            suggestions,
            key=lambda s: getattr(s, "confidence", 0.0),
            reverse=True,
        )

        for suggestion in ordered:
            anchor = getattr(suggestion, "anchor_text", "").strip()
            target = getattr(suggestion, "target_url", "").strip()
            if not anchor or not target:
                continue

            # Skip if anchor is already a markdown link somewhere in the body
            already_linked = re.search(
                r'\[' + re.escape(anchor) + r'\]\(',
                body,
                re.IGNORECASE,
            )
            if already_linked:
                continue

            # Match plain anchor text not already inside a markdown link or code span.
            # Use re.IGNORECASE instead of inline (?i) flag (must be first in pattern).
            pattern = r'(?<!\[)(?<!`)' + re.escape(anchor) + r'(?!`)'
            replacement = f"[{anchor}]({target})"

            new_body, count = re.subn(pattern, replacement, body, count=1, flags=re.IGNORECASE)
            if count:
                body = new_body

        return body

    def backfill_inbound_links(self, new_pages: list[Any]) -> dict[str, Any]:
        """
        Scan all existing published pages and inject a contextual link to each
        newly published page where the page's primary keyword appears as plain
        text. Ensures new content inherits inbound PageRank from the first run.
        """
        from types import SimpleNamespace

        publish_dir = self.config.get("publish_dir", "")
        publish_root = Path(publish_dir) if publish_dir else None
        if publish_root and not publish_root.is_absolute():
            publish_root = Path.cwd() / publish_root
        if not publish_root or not publish_root.exists():
            self.logger.warning("backfill_inbound_links: publish_root not found, skipping.")
            return {"files_updated": 0, "links_injected": 0}

        # Build link targets for each new page
        new_page_links = []
        for page in new_pages:
            slug = getattr(page, "slug", "").strip("/")
            keywords = getattr(page, "source_keywords", [])
            anchor = keywords[0] if keywords else getattr(page, "seo_title", "")
            if not slug or not anchor:
                continue
            new_page_links.append(SimpleNamespace(
                slug=slug,
                anchor_text=anchor,
                target_url=f"{self.site_url}/blog/{slug}",
                confidence=0.7,
            ))

        if not new_page_links:
            return {"files_updated": 0, "links_injected": 0}

        new_slugs = {link.slug for link in new_page_links}
        files_updated = 0
        links_injected = 0

        for slug_dir in sorted(publish_root.iterdir()):
            if not slug_dir.is_dir() or slug_dir.name in new_slugs:
                continue
            index_md = slug_dir / "index.md"
            if not index_md.exists():
                continue

            original = index_md.read_text(encoding="utf-8")
            updated = original
            injected_this_page = 0

            for link in new_page_links:
                # Skip if a link to this slug already exists in the page
                if f"/{link.slug})" in updated:
                    continue
                candidate = self._inject_internal_links(updated, [link])
                if candidate != updated:
                    updated = candidate
                    injected_this_page += 1
                    if injected_this_page >= 2:
                        break

            if updated != original:
                index_md.write_text(updated, encoding="utf-8")
                files_updated += 1
                links_injected += injected_this_page
                self.logger.debug("Backfill: %d link(s) → %s", injected_this_page, slug_dir.name)

        self.logger.info(
            "Backfill complete: %d links injected across %d existing pages.",
            links_injected,
            files_updated,
        )
        return {"files_updated": files_updated, "links_injected": links_injected}

    def _publish_via_webhook(self, assets: list[Any]) -> dict[str, Any]:
        endpoint = self.config["webhook_url"]
        payload = [item.to_dict() if hasattr(item, "to_dict") else item for item in assets]
        response = requests.post(endpoint, json={"assets": payload}, timeout=20)
        response.raise_for_status()
        return {"mode": "webhook", "published_count": len(payload), "status_code": response.status_code}
