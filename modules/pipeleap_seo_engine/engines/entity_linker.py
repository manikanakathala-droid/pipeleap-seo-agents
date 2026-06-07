"""
Semantic entity linker — scans page body text and injects contextual anchor links
for known entities (competitors, glossary terms, role pages, use case pages).
"""
from __future__ import annotations
import re
from typing import Any

from modules.pipeleap_seo_engine.data.entities import ENTITIES
from modules.pipeleap_seo_engine.data.roles import ROLES


def _build_entity_map(site_url: str) -> dict[str, str]:
    """
    Returns {entity_text_lower: url} for known glossary entities ONLY.
    Rule: All term-based definitions must link only to the Glossary page.
    """
    entity_map: dict[str, str] = {}
    # Glossary terms — use hash anchors on /glossary page
    for slug, entity in ENTITIES.items():
        entity_map[entity["term"].lower()] = f"{site_url}/glossary#{slug}"
    # REMOVED: Competitor and Role page links to satisfy 'one internal link' rule
    return entity_map


class SemanticEntityLinker:
    """
    Injects contextual anchor links into page body markdown.
    Rules:
    - Link each entity at most once per page (first occurrence only)
    - Never link text inside headings, code blocks, or existing links
    - Never link the page's own primary keyword back to itself
    """

    def __init__(self, site_url: str) -> None:
        self.site_url = site_url.rstrip("/")
        self._entity_map = _build_entity_map(self.site_url)

    def inject(self, body: str, page_slug: str, primary_keyword: str = "") -> tuple[str, int]:
        """
        Returns (updated_body, links_injected_count).
        Preserves code blocks, headings, and existing markdown links.
        """
        # Extract protected regions (code blocks, headings, existing links)
        protected = self._find_protected_regions(body)
        linked: set[str] = set()
        count = 0

        for entity_text, entity_url in sorted(self._entity_map.items(), key=lambda x: -len(x[0])):
            # Skip if this entity URL is the current page
            if entity_url.rstrip("/").endswith(page_slug.rstrip("/")):
                continue
            # Skip if matches primary keyword to avoid self-referencing loops
            if primary_keyword and entity_text in primary_keyword.lower():
                continue
            # Skip already linked
            if entity_text in linked:
                continue

            pattern = re.compile(rf"\b({re.escape(entity_text)})\b", re.IGNORECASE)
            match = pattern.search(body)
            if not match:
                continue

            # Check if match is in a protected region
            start = match.start()
            if any(p_start <= start <= p_end for p_start, p_end in protected):
                continue

            # Inject link (first occurrence only)
            original = match.group(0)
            replacement = f"[{original}]({entity_url})"
            body = body[:start] + replacement + body[start + len(original):]
            linked.add(entity_text)
            count += 1

            # Rebuild protected regions after injection (offsets shifted)
            if count >= 3:  # max 3 glossary links per page
                break

        return body, count

    @staticmethod
    def _find_protected_regions(body: str) -> list[tuple[int, int]]:
        regions = []
        # Code blocks
        for m in re.finditer(r"```[\s\S]*?```", body):
            regions.append((m.start(), m.end()))
        # Inline code
        for m in re.finditer(r"`[^`]+`", body):
            regions.append((m.start(), m.end()))
        # Existing markdown links
        for m in re.finditer(r"\[([^\]]+)\]\([^\)]+\)", body):
            regions.append((m.start(), m.end()))
        # Headings
        for m in re.finditer(r"^#{1,6} .+$", body, re.MULTILINE):
            regions.append((m.start(), m.end()))
        return regions
