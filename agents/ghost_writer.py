"""
/ghost skill — rewrites a blog draft in executive-voice copy.

Usage (Claude Code skill):
    /ghost

Reads the current draft markdown, applies the ghost rewrite pass, and
returns revised markdown. Operators run this before publish on any draft
that needs tighter executive framing.
"""
from __future__ import annotations

import re

from core.blog_content_engine import _strip_formatting, _AI_PHRASES

# Hedging patterns to strip
_HEDGE_PATTERN = re.compile(
    r"\b(may|might|could potentially|it(?:'s| is) worth noting|"
    r"arguably|seemingly|perhaps|in some cases|it could be said that|"
    r"one might argue|generally speaking)\b",
    re.IGNORECASE,
)

# Sentence split — split on ". " but preserve list items and code blocks
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def _rewrite_sentence(sentence: str) -> str:
    """Apply executive-voice patterns to a single sentence."""
    # Strip hedging
    sentence = _HEDGE_PATTERN.sub("", sentence)
    # Collapse double spaces left by removals
    sentence = re.sub(r"  +", " ", sentence).strip()
    return sentence


def _flag_ai_phrases(text: str) -> list[str]:
    found = []
    lower = text.lower()
    for phrase in _AI_PHRASES:
        if phrase in lower:
            found.append(phrase)
    return found


def ghost_rewrite(body_markdown: str) -> str:
    """
    Rewrites blog body markdown in executive voice.

    Rules applied:
    - Strip hedging language (may/might/could potentially/it's worth noting)
    - Direct address framing preserved ("If you're running...")
    - Concrete specifics over vague language
    - Strip em-dashes and asterisk markup
    - Reject any rewritten sentence that matches _AI_PHRASES

    Returns the rewritten markdown. Raises ValueError if AI phrases remain
    after rewriting (caller should regenerate or flag for human review).
    """
    lines = body_markdown.split("\n")
    output_lines: list[str] = []

    for line in lines:
        # Preserve headings, code blocks, tables, and blank lines verbatim
        stripped = line.strip()
        if (
            stripped.startswith("#")
            or stripped.startswith("```")
            or stripped.startswith("|")
            or stripped.startswith("-")
            or stripped.startswith("*")
            or not stripped
        ):
            output_lines.append(line)
            continue

        # Rewrite prose sentences
        sentences = _SENTENCE_SPLIT.split(line)
        rewritten = " ".join(_rewrite_sentence(s) for s in sentences)
        output_lines.append(rewritten)

    result = _strip_formatting("\n".join(output_lines))

    flagged = _flag_ai_phrases(result)
    if flagged:
        raise ValueError(
            f"Ghost rewrite still contains AI phrases after pass: {flagged}. "
            "Review and regenerate the flagged sentences manually."
        )

    return result
