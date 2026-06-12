"""
Revenue Path Linker — TOFU → MOFU → BOFU → SQL internal linking engine.

This engine injects funnel-progression links into generated page markdown.
Every page should pull readers one stage closer to a demo.

Rules:
  TOFU pages  → link to 1–2 MOFU pages (use case or role) + 1 BOFU page
  MOFU pages  → link to 1–2 BOFU pages (comparison or demo) + 1 objection page
  BOFU pages  → link directly to sales ops audit CTA + 1 objection page (trust)
  Glossary    → link to the most relevant MOFU use-case page
  All pages   → avoid linking DOWN the funnel (BOFU → TOFU creates confusion)

The linker also handles:
  - Anchor text rules: descriptive, keyword-rich, no "click here"
  - Link deduplication: max 1 link per destination per page
  - Injection point: bottom of each section, not inline mid-paragraph
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.pipeleap_seo_engine.models import GrowthPage

from modules.pipeleap_seo_engine.data.funnel_stages import (
    stage_for, PAGE_TYPE_STAGE, FUNNEL_STAGES
)

SITE_URL = "https://pipeleap.com"
AUDIT_URL = f"{SITE_URL}/sales-ops-audit"


# ── Revenue path link rules ────────────────────────────────────────────────────

FUNNEL_LINK_RULES: dict[str, dict] = {
    "TOFU": {
        "link_to_stages":   [],
        "max_stage_links":  0,
        "include_audit":    False,
        "audit_anchor":     None,
    },
    "MOFU": {
        "link_to_stages":   [],
        "max_stage_links":  0,
        "include_audit":    True,
        "audit_anchor":     "get a free sales ops audit",
    },
    "BOFU": {
        "link_to_stages":   [],
        "max_stage_links":  0,
        "include_audit":    True,
        "audit_anchor":     "get your free sales ops audit and workflow blueprint",
    },
    "SQL": {
        "link_to_stages":   [],
        "max_stage_links":  0,
        "include_audit":    True,
        "audit_anchor":     "book your Pipeleap demo",
    },
}

# Canonical next-step CTAs injected as a "nurture block" at page bottom
NURTURE_BLOCKS: dict[str, str] = {
    "TOFU": (
        "\n\n---\n\n"
        "**Next step:** If you're evaluating whether Pipeleap fits your outbound motion, "
        "the resources on our site show it in practice — "
        "or [get a free sales ops audit]({audit_url}) to get a workflow blueprint in 48 hours.\n"
    ),
    "MOFU": (
        "\n\n---\n\n"
        "**Ready to see this for your team?** "
        "[Get a free sales ops audit]({audit_url}) — we'll map your exact workflow and "
        "show you the 3 highest-leverage automation points for your stack.\n\n"
        "_Most teams have a working automated workflow running within 2 weeks of their audit._\n"
    ),
    "BOFU": (
        "\n\n---\n\n"
        "**[Get your free sales ops audit →]({audit_url})**\n\n"
        "We'll review your current outbound motion, identify your workflow gaps, "
        "and deliver a custom workflow blueprint — within 48 hours, no commitment required.\n"
    ),
    "SQL": (
        "\n\n---\n\n"
        "**[Book your Pipeleap demo →]({demo_url})**\n\n"
        "30 minutes. We'll walk through a live workflow built specifically for your use case.\n"
    ),
}


class RevenueLinkingEngine:
    """
    Injects revenue-path internal links and nurture blocks into generated page markdown.
    Operates after all pages are generated so it can reference the full page inventory.
    """

    def __init__(self, site_url: str = SITE_URL) -> None:
        self.site_url = site_url.rstrip("/")

    def inject(self, pages: list["GrowthPage"]) -> list["GrowthPage"]:
        """
        In-place enrichment of each page's body_markdown with:
        1. Funnel-progression internal links (cross-stage references)
        2. Nurture block at bottom of page (soft CTA + next-step link)
        """
        stage_buckets = self._bucket_pages(pages)

        for page in pages:
            stage = stage_for(page.page_type)
            rule = FUNNEL_LINK_RULES.get(stage, FUNNEL_LINK_RULES["TOFU"])

            # 1. Inject funnel links into existing "Next Steps" or "Related" section
            funnel_links = self._select_funnel_links(page, stage, rule, stage_buckets)
            if funnel_links:
                page.body_markdown = self._inject_related_links(
                    page.body_markdown, funnel_links
                )

            # 2. Append nurture block
            mofu_url = self._best_mofu_url(stage_buckets)
            nurture = self._build_nurture_block(stage, mofu_url)
            if nurture and not self._already_has_nurture(page.body_markdown):
                page.body_markdown = page.body_markdown.rstrip() + nurture

        return pages

    def build_link_report(self, pages: list["GrowthPage"]) -> dict[str, list[dict]]:
        """Return a slug → [{anchor, url, target_stage}] map for audit/reporting."""
        stage_buckets = self._bucket_pages(pages)
        report: dict[str, list[dict]] = {}

        for page in pages:
            stage = stage_for(page.page_type)
            rule = FUNNEL_LINK_RULES.get(stage, FUNNEL_LINK_RULES["TOFU"])
            links = self._select_funnel_links(page, stage, rule, stage_buckets)
            report[page.slug] = links

        return report

    # ── Link selection ─────────────────────────────────────────────────────────

    def _select_funnel_links(
        self, page: "GrowthPage", stage: str, rule: dict,
        buckets: dict[str, list["GrowthPage"]]
    ) -> list[dict]:
        links: list[dict] = []
        seen_urls: set[str] = set()
        max_links = rule["max_stage_links"]

        for target_stage in rule["link_to_stages"]:
            candidates = buckets.get(target_stage, [])
            for candidate in candidates:
                if candidate.slug == page.slug:
                    continue
                url = f"{self.site_url}/blog/{candidate.slug}"
                if url in seen_urls:
                    continue
                anchor = self._generate_anchor(candidate, target_stage)
                links.append({"anchor": anchor, "url": url, "target_stage": target_stage})
                seen_urls.add(url)
                if len(links) >= max_links:
                    break
            if len(links) >= max_links:
                break

        # Always add sales ops audit link for MOFU/BOFU/SQL
        if rule.get("include_audit") and rule.get("audit_anchor"):
            audit_link = {
                "anchor": rule["audit_anchor"],
                "url": f"{AUDIT_URL}?utm_source=organic&utm_medium=seo&utm_campaign=revenue_path&utm_content={page.slug}",
                "target_stage": "SQL",
            }
            if audit_link["url"] not in seen_urls:
                links.append(audit_link)

        return links

    # ── Markdown injection ────────────────────────────────────────────────────

    def _inject_related_links(self, markdown: str, links: list[dict]) -> str:
        if not links:
            return markdown

        # If a "Related" or "Next Steps" section already exists, append links there
        related_pattern = re.compile(
            r"(##\s+(?:Related|Next Steps?|See Also|Further Reading)[^\n]*\n)",
            re.IGNORECASE
        )
        match = related_pattern.search(markdown)

        link_lines = "\n".join(
            f"- [{link['anchor']}]({link['url']})" for link in links
        )

        if match:
            insert_pos = match.end()
            return markdown[:insert_pos] + link_lines + "\n" + markdown[insert_pos:]

        # Otherwise append a new "Related resources" section before the final CTA block
        # (identified by the last "---" separator)
        last_hr = markdown.rfind("\n---\n")
        if last_hr > 0:
            section = f"\n\n## Related resources\n\n{link_lines}\n"
            return markdown[:last_hr] + section + markdown[last_hr:]

        return markdown + f"\n\n## Related resources\n\n{link_lines}\n"

    # ── Nurture block ─────────────────────────────────────────────────────────

    def _build_nurture_block(self, stage: str, mofu_url: str) -> str:
        template = NURTURE_BLOCKS.get(stage, "")
        if not template:
            return ""
        audit_url = f"{AUDIT_URL}?utm_source=organic&utm_medium=seo&utm_campaign=nurture_{stage.lower()}"
        demo_url = f"{self.site_url}/contact?utm_source=organic&utm_medium=seo&utm_campaign=nurture_{stage.lower()}"
        return template.format(audit_url=audit_url, demo_url=demo_url, mofu_url=mofu_url)

    @staticmethod
    def _already_has_nurture(markdown: str) -> bool:
        return "get your free sales ops audit" in markdown.lower() or "Book your Pipeleap demo" in markdown

    # ── Anchor text generation ────────────────────────────────────────────────

    @staticmethod
    def _generate_anchor(page: "GrowthPage", target_stage: str) -> str:
        title_short = page.title.split("|")[0].strip()

        if target_stage == "BOFU":
            if page.page_type == "bofu_page":
                return f"see a live demo for {page.use_case or 'your use case'}"
            if page.page_type == "objection_page":
                return f"common questions before deciding"

        if target_stage == "MOFU":
            if page.page_type == "role_page":
                return f"how {page.role or 'your team'} uses Pipeleap"
            if page.page_type == "use_case_page":
                return f"the {page.use_case or 'use case'} workflow in practice"
            if page.page_type == "integration_page":
                return f"Pipeleap + {page.integration_partner or 'your stack'}"

        # Fallback: clean title (no pipe branding, lowercase first word)
        words = title_short.split()
        if words:
            words[0] = words[0].lower()
        return " ".join(words)[:60]

    # ── Bucketing ─────────────────────────────────────────────────────────────

    @staticmethod
    def _bucket_pages(pages: list["GrowthPage"]) -> dict[str, list["GrowthPage"]]:
        buckets: dict[str, list] = {"TOFU": [], "MOFU": [], "BOFU": [], "SQL": []}
        for page in pages:
            stage = stage_for(page.page_type)
            if stage in buckets:
                buckets[stage].append(page)
        return buckets

    def _best_mofu_url(self, buckets: dict) -> str:
        mofu_pages = buckets.get("MOFU", [])
        if mofu_pages:
            return f"{self.site_url}/blog/{mofu_pages[0].slug}"
        return f"{self.site_url}/how-it-works"
