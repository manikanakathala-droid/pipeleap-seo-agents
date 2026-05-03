"""
Duplicate detection for glossary terms.

Three-pass detection before any term is published:
  1. Exact slug match
  2. Fuzzy similarity >= threshold (SequenceMatcher, no external deps)
  3. Synonym/acronym equivalence via slug_normalizer

On collision: returns the canonical slug so caller can UPDATE instead of INSERT.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from .slug_normalizer import normalize_slug, SYNONYM_MAP, ACRONYM_MAP


_DEFAULT_THRESHOLD = 0.85


def _token_set(slug: str) -> set[str]:
    return set(re.split(r"-+", slug))


class DuplicateDetector:
    """
    Detects duplicate glossary terms against an existing term corpus.

    Usage:
        detector = DuplicateDetector(existing_slugs)
        result = detector.check("sdr productivity")
        if result.is_duplicate:
            update_canonical(result.canonical_slug)
        else:
            create_new(result.proposed_slug)
    """

    def __init__(
        self,
        existing_slugs: set[str] | list[str],
        threshold: float = _DEFAULT_THRESHOLD,
    ) -> None:
        self.existing: set[str] = set(existing_slugs)
        self.threshold = threshold

    def check(self, raw_term: str) -> "CheckResult":
        proposed = normalize_slug(raw_term)

        # Pass 1 — exact slug match
        if proposed in self.existing:
            return CheckResult(
                proposed_slug=proposed,
                canonical_slug=proposed,
                is_duplicate=True,
                detection_method="exact",
                similarity=1.0,
            )

        # Pass 2 — synonym / acronym resolution
        normalized_canonical = self._synonym_check(proposed)
        if normalized_canonical and normalized_canonical in self.existing:
            return CheckResult(
                proposed_slug=proposed,
                canonical_slug=normalized_canonical,
                is_duplicate=True,
                detection_method="synonym",
                similarity=1.0,
            )

        # Pass 3 — fuzzy match
        best_slug, best_score = self._fuzzy_check(proposed)
        if best_score >= self.threshold:
            return CheckResult(
                proposed_slug=proposed,
                canonical_slug=best_slug,
                is_duplicate=True,
                detection_method="fuzzy",
                similarity=best_score,
            )

        return CheckResult(
            proposed_slug=proposed,
            canonical_slug=proposed,
            is_duplicate=False,
            detection_method=None,
            similarity=best_score,
        )

    def add(self, slug: str) -> None:
        """Register a newly created slug so subsequent checks see it."""
        self.existing.add(slug)

    def _synonym_check(self, slug: str) -> str | None:
        for synonym_raw, canonical in SYNONYM_MAP.items():
            if normalize_slug(synonym_raw) == slug:
                return canonical
        for acronym, canonical in ACRONYM_MAP.items():
            if slug == acronym or slug == normalize_slug(acronym):
                return canonical
        return None

    def _fuzzy_check(self, proposed: str) -> tuple[str, float]:
        best_slug = ""
        best_score = 0.0
        proposed_tokens = _token_set(proposed)

        for existing_slug in self.existing:
            # SequenceMatcher on the hyphenated strings
            seq_score = SequenceMatcher(None, proposed, existing_slug).ratio()

            # Token overlap bonus — catches reordered words
            existing_tokens = _token_set(existing_slug)
            if proposed_tokens and existing_tokens:
                overlap = len(proposed_tokens & existing_tokens) / max(len(proposed_tokens), len(existing_tokens))
                score = max(seq_score, overlap)
            else:
                score = seq_score

            if score > best_score:
                best_score = score
                best_slug = existing_slug

        return best_slug, best_score

    def batch_check(self, raw_terms: list[str]) -> list["CheckResult"]:
        results = []
        for term in raw_terms:
            result = self.check(term)
            if not result.is_duplicate:
                self.add(result.proposed_slug)
            results.append(result)
        return results

    def collision_log(self, raw_terms: list[str]) -> list[dict[str, Any]]:
        results = self.batch_check(raw_terms)
        return [
            {
                "input": term,
                "proposed_slug": r.proposed_slug,
                "canonical_slug": r.canonical_slug,
                "is_duplicate": r.is_duplicate,
                "method": r.detection_method,
                "similarity": round(r.similarity, 3),
            }
            for term, r in zip(raw_terms, results)
        ]


class CheckResult:
    __slots__ = ("proposed_slug", "canonical_slug", "is_duplicate", "detection_method", "similarity")

    def __init__(
        self,
        proposed_slug: str,
        canonical_slug: str,
        is_duplicate: bool,
        detection_method: str | None,
        similarity: float,
    ) -> None:
        self.proposed_slug = proposed_slug
        self.canonical_slug = canonical_slug
        self.is_duplicate = is_duplicate
        self.detection_method = detection_method
        self.similarity = similarity

    def __repr__(self) -> str:
        return (
            f"CheckResult(proposed={self.proposed_slug!r}, "
            f"canonical={self.canonical_slug!r}, "
            f"duplicate={self.is_duplicate}, method={self.detection_method})"
        )
