"""
Ghost mode — post-generation transformations that make template-built content
read more naturally. Activated by the /ghost command (config ghost_mode: true).

Design:
- Every transform is optional, idempotent, and safe on already-human text.
- Transforms only touch body copy (paragraphs, list items, intro text).
- No meta tags, schema, headings, URLs, or SEO infrastructure is modified.
- The seed_hash ensures consistent output per keyword (same keyword = same ghost).
"""

from __future__ import annotations

import re
import zlib
from typing import Any

# ── Contractions ──────────────────────────────────────────────────────────────

_CONTRACTIONS: dict[str, str] = {
    " do not ": " don't ",
    " does not ": " doesn't ",
    " did not ": " didn't ",
    " have not ": " haven't ",
    " has not ": " hasn't ",
    " had not ": " hadn't ",
    " is not ": " isn't ",
    " are not ": " aren't ",
    " was not ": " wasn't ",
    " were not ": " weren't ",
    " will not ": " won't ",
    " would not ": " wouldn't ",
    " could not ": " couldn't ",
    " should not ": " shouldn't ",
    " might not ": " mightn't ",
    " cannot ": " can't ",
    " it is ": " it's ",
    " there is ": " there's ",
    " there are ": " there's ",
    " that is ": " that's ",
    " here is ": " here's ",
    " you are ": " you're ",
    " they are ": " they're ",
    " we are ": " we're ",
    " we have ": " we've ",
    " they have ": " they've ",
    " I have ": " I've ",
    " I am ": " I'm ",
    " I will ": " I'll ",
    " you will ": " you'll ",
    " they will ": " they'll ",
    " we will ": " we'll ",
    " that will ": " that'll ",
}

_CONTRACTION_RE = re.compile(
    "|".join(re.escape(k) for k in sorted(_CONTRACTIONS, key=len, reverse=True)),
    re.IGNORECASE,
)


def _apply_contractions(text: str, rate: float = 0.6) -> str:
    """Replace a random subset of expandable phrases with contractions."""
    def _maybe_replace(m: re.Match) -> str:
        key = m.group(0).lower()
        replacement = _CONTRACTIONS.get(key)
        if replacement is None:
            return m.group(0)
        return replacement
    return _CONTRACTION_RE.sub(_maybe_replace, text)


# ── Sentence length variation ────────────────────────────────────────────────

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

_FILLER_INSERTS = [
    "Look, ",
    "Here's the thing: ",
    "The reality is, ",
    "Honestly, ",
    "Here's what that means: ",
    "Think about it: ",
    "The truth is, ",
    "Here's the kicker: ",
    "And here's why that matters: ",
]

_SHORT_CONNECTORS = [
    "But ",
    "So ",
    "And ",
    "Yet ",
    "Still, ",
    "Which means ",
]


def _vary_sentence_structure(text: str, seed: int) -> str:
    """Occasionally break long sentences, add conversational connectors."""
    rng = _zlib.crc32(str(seed).encode())
    sentences = _SENTENCE_SPLIT_RE.split(text)
    result: list[str] = []
    for i, s in enumerate(sentences):
        words = s.split()
        if len(words) > 18 and (rng + i) % 5 == 0:
            # Split long sentence mid-way
            mid = len(words) // 2
            first = " ".join(words[:mid])
            second = " ".join(words[mid:])
            result.append(first + ".")
            connector = _SHORT_CONNECTORS[(rng + i) % len(_SHORT_CONNECTORS)]
            result.append(connector + second[0].lower() + second[1:])
        elif len(words) > 8 and (rng + i) % 7 == 0:
            # Add a conversational opener to a meaty sentence
            filler = _FILLER_INSERTS[(rng + i) % len(_FILLER_INSERTS)]
            result.append(filler + s[0].lower() + s[1:])
        else:
            result.append(s)
    return " ".join(result)


# ── Opinionated / experiential inserts ────────────────────────────────────────

_OPINION_INSERTS = [
    " In our experience working with revenue teams, ",
    " What we have found is that ",
    " Most teams we work with underestimate ",
    " One thing that consistently surprises people is ",
    " The hard truth is, ",
    " After building dozens of these systems, we can tell you that ",
    " Here is what most guides will not tell you: ",
    " If you are serious about this, ",
    " The mistake we see most often is ",
]


def _add_opinionated_language(text: str, seed: int) -> str:
    """Insert expert-opinion phrases at natural break points."""
    paragraphs = text.split("\n\n")
    rng = _zlib.crc32(str(seed + 1).encode())
    result: list[str] = []
    for i, para in enumerate(paragraphs):
        if len(para) > 60 and (rng + i) % 4 == 0:
            insert = _OPINION_INSERTS[(rng + i) % len(_OPINION_INSERTS)]
            # Insert mid-paragraph after first sentence
            dot = para.find(". ")
            if dot > 20 and dot < len(para) - 30:
                para = para[:dot+1] + insert + para[dot+2:]
        result.append(para)
    return "\n\n".join(result)


# ── Sentence fragment inserts (natural cadence) ──────────────────────────────

_FRAGMENTS = [
    " Makes sense?",
    " Exactly.",
    " Simple.",
    " That is the difference.",
    " Worth testing.",
    " It adds up fast.",
]


def _add_natural_fragments(text: str, seed: int) -> str:
    """Add short fragment sentences at paragraph ends."""
    paragraphs = text.split("\n\n")
    rng = _zlib.crc32(str(seed + 2).encode())
    result: list[str] = []
    for i, para in enumerate(paragraphs):
        result.append(para)
        if len(para) > 80 and (rng + i) % 6 == 3 and not para.endswith(("?", "!", ":", ";")):
            result.append(_FRAGMENTS[(rng + i) % len(_FRAGMENTS)])
    return "\n\n".join(result)


# ── Concrete detail injection (generic → specific) ──────────────────────────

_DETAIL_MAP: dict[str, list[str]] = {
    "enrich": ["pulling 12+ data points per contact", "enrichment failure rates near 15% on raw lists", "watering through 8 providers per row"],
    "crm": ["CRM hygiene scores below 60% are the norm", "CRM sync breaks on 1 in 4 pipeline updates", "most CRMs have 20%+ duplicate rates"],
    "sequence": ["sequence reply rates average 3-8% on cold lists", "multi-channel sequences lift reply rates by 40%", "sequence drop-off is highest between touch 2 and 3"],
    "outreach": ["outbound reply rates average 3-8% after 6 touches", "personalised outreach lifts reply rates by 2x", "most teams send 4-6 touches before giving up"],
    "email": ["cold email deliverability averages 85-92% for clean domains", "inbox rotation cuts spam placement by 60%", "email open rates plateau after 3 sends"],
    "lead": ["lead scoring cuts pipeline noise by 40%", "ICP-fit leads convert at 3x the rate of broad lists", "lead enrichment takes 12 seconds per contact manually"],
    "workflow": ["workflow automation cuts manual steps by 70%", "most workflows have 4-6 handoff points that break silently", "automation reduces data entry errors by 80%"],
    "pipeline": ["pipeline velocity drops 30% without automated routing", "stale pipeline costs 15% of quarterly revenue in SaaS", "automated pipeline hygiene recovers 10-20% of stalled deals"],
    "revenue": ["revenue teams waste 60% of time on non-selling work", "automated RevOps stacks grow pipeline 2x faster", "revenue leakage from manual handoffs averages 12%"],
    "data": ["data decay runs at 2-3% per month on B2B contacts", "enriched data decays 50% slower than raw lists", "clean data improves close rates by measurable margins"],
}


def _inject_concrete_details(text: str, seed: int) -> str:
    """Replace generic statements with specific, credible-sounding details."""
    rng = _zlib.crc32(str(seed + 3).encode())
    lowered = text.lower()
    matches = []
    for trigger, options in _DETAIL_MAP.items():
        if trigger in lowered:
            matches.append(trigger)
    if not matches:
        return text
    trigger = matches[rng % len(matches)]
    detail = _DETAIL_MAP[trigger][rng % len(_DETAIL_MAP[trigger])]
    # Replace a generic sentence-ending assertion with a specific one
    paragraphs = text.split("\n\n")
    for i, para in enumerate(paragraphs):
        if trigger in para.lower() and (rng + i) % 3 == 0:
            sentences = para.rstrip(".").split(". ")
            for j in range(len(sentences) - 1, -1, -1):
                if trigger in sentences[j].lower():
                    sentences[j] = sentences[j].rstrip(".") + f" — {detail}"
                    paragraphs[i] = ". ".join(sentences) + "."
                    break
            break
    return "\n\n".join(paragraphs)


# ── Main transform entry point ────────────────────────────────────────────────

def transform(body: str, keyword: str = "", ghost_config: dict[str, Any] | None = None) -> str:
    """
    Apply ghost-mode transformations to post-rendered body copy.

    Args:
        body: The fully-rendered blog body markdown.
        keyword: Primary keyword (used for deterministic seed).
        ghost_config: Optional config dict with overrides:
            - enabled (bool): master toggle
            - contraction_rate (float): 0.0-1.0
            - sentence_vary (bool): toggle sentence length variation
            - opinion_language (bool): toggle opinionated inserts
            - natural_fragments (bool): toggle fragment inserts
            - concrete_details (bool): toggle concrete detail injection

    Returns:
        Transformed body if enabled, original body otherwise.
    """
    if ghost_config is None:
        ghost_config = {}
    if not ghost_config.get("enabled", False):
        return body

    seed = abs(zlib.crc32(keyword.encode())) if keyword else 42

    if ghost_config.get("contraction_rate", 0.6):
        body = _apply_contractions(body, ghost_config.get("contraction_rate", 0.6))

    if ghost_config.get("sentence_vary", True):
        body = _vary_sentence_structure(body, seed)

    if ghost_config.get("opinion_language", True):
        body = _add_opinionated_language(body, seed)

    if ghost_config.get("natural_fragments", True):
        body = _add_natural_fragments(body, seed)

    if ghost_config.get("concrete_details", True):
        body = _inject_concrete_details(body, seed)

    return body
