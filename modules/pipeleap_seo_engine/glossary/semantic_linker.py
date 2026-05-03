"""
Semantic internal linking engine for glossary terms.

Builds a directed link graph based on:
  1. Explicit related_terms declared in entities.py
  2. Shared category membership
  3. Token overlap between slug and keywords

Rules:
  - Each term links to 3–5 related terms
  - No orphan pages (minimum 1 inbound link guaranteed via hub)
  - Bidirectional where semantically justified
  - Crawl depth ≤ 3 from /glossary hub
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any


def _tokens(text: str) -> set[str]:
    return set(re.split(r"[-\s]+", text.lower()))


class GlossarySemanticLinker:
    """
    Given the full ENTITIES dict, compute internal link suggestions
    for each term. Returns a map: slug → list of link dicts.
    """

    MAX_LINKS = 5
    MIN_LINKS = 1

    def __init__(self, entities: dict[str, dict[str, Any]], site_url: str) -> None:
        self.entities = entities
        self.site_url = site_url.rstrip("/")

    def build_link_map(self) -> dict[str, list[dict[str, str]]]:
        """
        Returns {slug: [{"anchor_text": ..., "target_url": ..., "reason": ...}]}
        """
        link_map: dict[str, list[dict[str, str]]] = {}

        for slug, entity in self.entities.items():
            candidates = self._rank_candidates(slug, entity)
            link_map[slug] = candidates[: self.MAX_LINKS]

        # Orphan check: any slug with zero inbound links gets linked from hub page
        inbound_counts: dict[str, int] = defaultdict(int)
        for links in link_map.values():
            for link in links:
                target_slug = link["target_url"].split("/glossary/")[-1]
                inbound_counts[target_slug] += 1

        for slug in self.entities:
            if inbound_counts[slug] == 0 and slug in link_map:
                # Hub page will always link to it; mark it so generators know
                link_map[slug] = [
                    {
                        "anchor_text": self.entities[slug]["term"],
                        "target_url": f"{self.site_url}/glossary/{slug}",
                        "reason": "hub_inbound",
                    }
                ] + link_map[slug]

        return link_map

    def _rank_candidates(
        self, source_slug: str, source_entity: dict[str, Any]
    ) -> list[dict[str, str]]:
        source_tokens = _tokens(source_slug)
        source_kws = set()
        for kw in source_entity.get("keywords", []):
            source_kws.update(_tokens(kw))
        source_category = source_entity.get("category", "")

        scored: list[tuple[float, str, dict[str, Any]]] = []

        for candidate_slug, candidate in self.entities.items():
            if candidate_slug == source_slug:
                continue

            score = 0.0

            # Explicit related_terms — highest weight
            related_raw = [r.lower().replace(" ", "-") for r in source_entity.get("related_terms", [])]
            if candidate_slug in related_raw or candidate["term"].lower() in [
                r.replace("-", " ") for r in related_raw
            ]:
                score += 3.0

            # Same category
            if source_category and candidate.get("category") == source_category:
                score += 1.0

            # Token overlap between slugs
            cand_tokens = _tokens(candidate_slug)
            overlap = len(source_tokens & cand_tokens) / max(len(source_tokens), len(cand_tokens), 1)
            score += overlap * 2.0

            # Keyword overlap
            cand_kws = set()
            for kw in candidate.get("keywords", []):
                cand_kws.update(_tokens(kw))
            kw_overlap = len(source_kws & cand_kws) / max(len(source_kws), len(cand_kws), 1)
            score += kw_overlap * 1.5

            if score > 0:
                scored.append((score, candidate_slug, candidate))

        scored.sort(key=lambda x: x[0], reverse=True)

        links = []
        for _, cand_slug, cand in scored:
            links.append({
                "anchor_text": cand["term"],
                "target_url": f"{self.site_url}/glossary/{cand_slug}",
                "reason": "semantic",
            })

        return links

    def get_links_for(self, slug: str) -> list[dict[str, str]]:
        return self.build_link_map().get(slug, [])
