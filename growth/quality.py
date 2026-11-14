"""
Quality gate. A draft that fails is never published.

It checks the things that made the previous content worthless or risky:
invented statistics, claims the site does not make, near-duplicate pages,
banned phrasing, and pages with no path to an enquiry.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from growth.icp import tokens

_STAT = re.compile(r"(\d[\d,.]*\s?%|\$\s?\d[\d,.]*\s?[kKmMbB]?\b|\b\d[\d,.]*\s?(?:x|times)\b|\b\d{2,}[\d,.]*\s+(?:hours|minutes|reps|companies|teams|deals)\b)")
_LINK = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")


@dataclass
class QualityReport:
    passed: bool
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    word_count: int = 0

    def summary(self) -> str:
        return "passed" if self.passed else "; ".join(self.failures)


def shingles(text: str, size: int = 5) -> set[tuple[str, ...]]:
    words = tokens(text)
    return {tuple(words[i:i + size]) for i in range(max(0, len(words) - size + 1))}


def similarity(a: str, b: str) -> float:
    sa, sb = shingles(a), shingles(b)
    return len(sa & sb) / len(sa | sb) if sa and sb else 0.0


def unsupported_statistics(markdown: str, site_facts: str) -> list[str]:
    """Numeric claims with no source link in the same paragraph and not present on the site itself."""
    flagged = []
    for paragraph in re.split(r"\n\s*\n", markdown):
        if _LINK.search(paragraph):
            continue
        for match in _STAT.finditer(paragraph):
            claim = match.group(0).strip()
            if claim not in site_facts and claim not in flagged:
                flagged.append(claim)
    return flagged


def check(markdown: str, *, title: str, description: str, query: str, site_facts: str,
          existing_texts: dict[str, str], rules: dict[str, Any], cta_url: str) -> QualityReport:
    failures: list[str] = []
    warnings: list[str] = []
    words = len(tokens(markdown))
    lower = markdown.lower()

    min_words = int(rules.get("min_words", 800))
    if words < min_words:
        failures.append(f"too short: {words} words (minimum {min_words})")
    if len(re.findall(r"^##\s+\S", markdown, re.M)) < 3:
        failures.append("fewer than three H2 sections")
    if re.search(r"^#\s+\S", markdown, re.M):
        failures.append("body contains an H1; the title is rendered by the template")

    wanted = [w for w in tokens(query) if len(w) > 2]
    if wanted and sum(1 for w in wanted if w in tokens(title)) / len(wanted) < 0.5:
        failures.append("title does not reflect the target query")
    if not 30 <= len(title) <= 65:
        warnings.append(f"title length {len(title)} is outside 30-65 characters")
    if not 110 <= len(description) <= 160:
        failures.append(f"meta description length {len(description)} is outside 110-160 characters")

    for phrase in rules.get("banned_phrases", []):
        if phrase.lower() in lower:
            failures.append(f"banned phrase: “{phrase}”")

    stats = unsupported_statistics(markdown, site_facts)
    if stats:
        failures.append("statistics without a cited source: " + ", ".join(stats[:6]))

    # The call-to-action block is added by the page template; the body must link into the site itself.
    needed = int(rules.get("min_internal_links", 2))
    internal = len(re.findall(r"\]\(/[^)]*\)", markdown))
    if internal < needed:
        failures.append(f"{internal} internal link(s); at least {needed} required")
    if cta_url and cta_url in markdown:
        warnings.append("body links to the scheduler directly; the template already adds the call-to-action")

    limit = float(rules.get("max_similarity", 0.35))
    for path, text in existing_texts.items():
        score = similarity(markdown, text)
        if score > limit:
            failures.append(f"{score:.0%} overlap with {path}")

    return QualityReport(passed=not failures, failures=failures, warnings=warnings, word_count=words)
