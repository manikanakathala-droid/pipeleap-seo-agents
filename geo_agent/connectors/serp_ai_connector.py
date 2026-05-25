"""
SERP AI Connector — detects AI Overview, PAA, and featured snippet candidates
using free signals: Google Autocomplete, question-intent analysis, and Trends.

No paid API required. Falls back gracefully on network errors.
"""
from __future__ import annotations

import time
from typing import Any

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

try:
    from pytrends.request import TrendReq as _TrendReq
    _HAS_PYTRENDS = True
except ImportError:
    _HAS_PYTRENDS = False

DEFAULT_LOCATION = 2840
DEFAULT_LANGUAGE = "en"

# Question prefixes that strongly correlate with PAA / featured snippets
_PAA_PREFIXES = ("what is", "what are", "how to", "how does", "why", "when", "which", "can i", "does")
_SNIPPET_PREFIXES = ("what is", "what are", "how to", "how does", "define", "meaning of")
_AI_OVERVIEW_SIGNALS = ("best", "vs", "compare", "review", "top", "alternative")


class SERPAIConnector:
    """
    Free replacement for the DataForSEO SERP connector.
    Uses question-intent heuristics + Google Autocomplete to detect
    AI Overview / PAA / featured snippet opportunities.
    Always configured — no credentials needed.
    """

    is_configured = True

    def __init__(self, login: str = "", password: str = "") -> None:  # noqa: ARG002
        self._trends = None

    def _get_trends(self):
        if not _HAS_PYTRENDS or self._trends is not None:
            return self._trends
        try:
            self._trends = _TrendReq(hl="en-US", tz=0, timeout=(10, 25), retries=2, backoff_factor=0.5)
        except Exception:
            pass
        return self._trends

    def check_queries(
        self,
        queries: list[str],
        location_code: int = DEFAULT_LOCATION,  # noqa: ARG002
        delay: float = 0.25,
    ) -> list[dict[str, Any]]:
        results = []
        for query in queries:
            results.append(self._check_single(query))
            if delay:
                time.sleep(delay)
        return results

    def check_queries_batch(
        self,
        queries: list[str],
        location_code: int = DEFAULT_LOCATION,  # noqa: ARG002
        batch_size: int = 5,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        return self.check_queries(queries, location_code, delay=0.2)

    def ai_overview_queries(self, results: list[dict]) -> list[str]:
        return [r["keyword"] for r in results if r.get("has_ai_overview")]

    def paa_queries(self, results: list[dict]) -> list[str]:
        return [r["keyword"] for r in results if r.get("has_paa")]

    def featured_snippet_queries(self, results: list[dict]) -> list[str]:
        return [r["keyword"] for r in results if r.get("has_featured_snippet")]

    # ── Internals ─────────────────────────────────────────────────────────────

    def _check_single(self, query: str) -> dict[str, Any]:
        q = query.lower().strip()

        has_paa = any(q.startswith(p) for p in _PAA_PREFIXES)
        has_featured_snippet = any(q.startswith(p) for p in _SNIPPET_PREFIXES)
        has_ai_overview = any(w in q for w in _AI_OVERVIEW_SIGNALS) or has_featured_snippet

        # Boost signals using Google Autocomplete question expansions
        ac_questions = self._autocomplete_questions(query)
        if ac_questions:
            has_paa = True

        # Trends interest as proxy for AI Overview likelihood
        trend_score = self._trends_score(query)
        if trend_score >= 60:
            has_ai_overview = True

        return {
            "keyword":              query,
            "has_ai_overview":      has_ai_overview,
            "has_paa":              has_paa,
            "has_featured_snippet": has_featured_snippet,
            "has_knowledge_graph":  False,
            "item_types":           self._item_types(has_ai_overview, has_paa, has_featured_snippet),
            "trend_score":          trend_score,
            "paa_questions":        ac_questions[:5],
            "source":               "free_heuristic",
        }

    def _autocomplete_questions(self, seed: str) -> list[str]:
        if not _HAS_REQUESTS:
            return []
        questions = []
        for prefix in ("what is", "how to", "why", "best"):
            try:
                resp = _requests.get(
                    "https://suggestqueries.google.com/complete/search",
                    params={"client": "firefox", "q": f"{prefix} {seed}"},
                    timeout=4,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 1:
                        questions.extend(data[1][:3])
            except Exception:
                pass
            time.sleep(0.1)
        return list(dict.fromkeys(questions))

    def _trends_score(self, query: str) -> int:
        pt = self._get_trends()
        if not pt:
            return 40
        try:
            pt.build_payload([query], geo="US", timeframe="today 12-m")
            data = pt.interest_over_time()
            if not data.empty and query in data.columns:
                return int(data[query].mean())
        except Exception:
            pass
        return 40

    @staticmethod
    def _item_types(ai_overview: bool, paa: bool, snippet: bool) -> list[str]:
        types = []
        if ai_overview:
            types.append("ai_overview")
        if paa:
            types.append("people_also_ask")
        if snippet:
            types.append("featured_snippet")
        return types
