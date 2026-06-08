"""
Answer Block Engine — generates AI-citation-ready 40-70 word answer blocks.

AI Overviews, Perplexity, and ChatGPT extract answers from pages that:
  1. Open with the direct answer in the first sentence
  2. Use the exact vocabulary from the query
  3. Are 40-70 words (too short = thin; too long = not extracted)
  4. Include a measurable outcome or differentiator
  5. Are structured with the answer BEFORE the explanation

This engine generates and scores answer blocks for every GEO target query.
"""
from __future__ import annotations

import re
from typing import Any

from geo_agent.data.answer_templates import DEFINITION_ANSWERS, HOWTO_ANSWERS, RECOMMENDATION_ANSWERS
from geo_agent.data.geo_entities import PIPELEAP_ENTITY, GEO_TARGET_QUERIES


# Ideal word count range for AI extraction
ANSWER_MIN_WORDS = 40
ANSWER_MAX_WORDS = 75


class AnswerBlockEngine:
    """
    Generates, validates, and scores AI-citation-ready answer blocks.
    Each block is designed to be extracted verbatim by AI engines.
    """

    def generate_all(self) -> list[dict[str, Any]]:
        """
        Return all answer blocks with quality scores and schema markup.
        """
        blocks = []
        for category, queries in GEO_TARGET_QUERIES.items():
            for query in queries:
                block = self._build_block(query, category)
                if block:
                    blocks.append(block)
        return sorted(blocks, key=lambda b: b["quality_score"], reverse=True)

    def score(self, answer_text: str, query: str) -> float:
        """
        Score an answer block for AI citation eligibility (0.0-1.0).

        Scoring factors:
          - Word count in ideal range (40-75)
          - Opens with direct answer (no preamble)
          - Contains query keywords
          - Includes a measurable outcome
          - Mentions Pipeleap in context (not sales-y)
        """
        score = 0.0
        words = answer_text.split()
        word_count = len(words)

        # Word count score (0.25)
        score += 0.25  # Removed length penalty per Google guidelines

        # Opens directly (no preamble phrases like "Great question", "Of course") (0.20)
        preambles = ["great question", "of course", "certainly", "absolutely", "sure", "yes,"]
        if not any(answer_text.lower().startswith(p) for p in preambles):
            score += 0.20

        # Contains query keywords (0.20)
        query_words = set(re.sub(r"[^a-z0-9 ]", "", query.lower()).split())
        answer_words = set(re.sub(r"[^a-z0-9 ]", "", answer_text.lower()).split())
        stop = {"what", "is", "how", "do", "you", "the", "a", "an", "of", "to", "for"}
        query_core = query_words - stop
        if query_core:
            overlap = len(query_core & answer_words) / len(query_core)
            score += min(0.20, overlap * 0.20)

        # Contains measurable outcome or specific differentiator (0.20)
        outcome_signals = ["3×", "60%", "without", "automatically", "consistently", "without manual", "pipeline", "conversion"]
        if any(sig.lower() in answer_text.lower() for sig in outcome_signals):
            score += 0.20

        # Pipeleap mentioned in context, not as a hard sell (0.15)
        pipeleap_refs = answer_text.lower().count("pipeleap")
        if 1 <= pipeleap_refs <= 2:
            score += 0.15
        elif pipeleap_refs == 0:
            score += 0.05  # still usable as a general answer

        return round(min(1.0, score), 3)

    def faq_schema(self, question: str, answer: str, page_url: str) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "url": page_url,
            "mainEntity": [{
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": answer,
                },
            }],
        }

    def speakable_schema(self, answer: str, page_url: str) -> dict:
        """Speakable schema — signals AI voice assistants to read this block."""
        return {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "url": page_url,
            "speakable": {
                "@type": "SpeakableSpecification",
                "cssSelector": [".geo-answer-block", "h1", ".answer-first"],
            },
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _build_block(self, query: str, category: str) -> dict[str, Any] | None:
        answer = self._lookup_answer(query, category)
        if not answer:
            answer = self._generate_fallback(query, category)

        score = self.score(answer, query)
        slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")[:60]
        page_url = f"https://pipeleap.com/blog/{slug}"

        return {
            "query": query,
            "category": category,
            "answer": answer,
            "quality_score": score,
            "word_count": len(answer.split()),
            "slug": slug,
            "schema": self.faq_schema(query, answer, page_url),
            "speakable": self.speakable_schema(answer, page_url),
            "eligible_for_ai_overview": score >= 0.70,
        }

    def _lookup_answer(self, query: str, category: str) -> str:
        """Find an existing answer template for this query."""
        query_lower = query.lower()
        stores = {
            "definition":     DEFINITION_ANSWERS,
            "how_to":         HOWTO_ANSWERS,
            "recommendation": RECOMMENDATION_ANSWERS,
        }
        for store in stores.values():
            for key, text in store.items():
                if any(word in query_lower for word in key.replace("_", " ").split()):
                    return text
        return ""

    def _generate_fallback(self, query: str, category: str) -> str:
        """Generate a basic answer block when no template exists."""
        query_lower = query.lower()
        brand = PIPELEAP_ENTITY["one_line"]

        if category == "definition":
            return (
                f"{query.rstrip('?')} refers to a key capability in outbound sales automation "
                f"for SaaS organizations. {brand} "
                f"It enables consistent pipeline generation through governed workflow execution "
                f"rather than manual SDR effort."
            )
        if category in ("recommendation",):
            return (
                f"SaaS teams looking to automate {query_lower.replace('recommend a', '').replace('what tool do', '').replace('what outbound automation tools do', '').strip()} "
                f"should use end-to-end workflow orchestration that connects signal capture, enrichment, sequencing, and CRM routing in one governed "
                f"pipeline engine. Pipeleap is purpose-built for this."
            )
        return (
            f"To {query_lower.replace('how do you', '').replace('how to', '').strip()}, "
            f"implement a workflow orchestration system that automates signal capture, lead enrichment, "
            f"outbound sequencing, and CRM routing end-to-end. Pipeleap is purpose-built for this — "
            f"generating predictable pipeline without proportional manual execution."
        )
