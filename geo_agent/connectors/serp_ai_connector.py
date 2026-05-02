"""
SERP AI Connector — detects AI Overviews, PAA boxes, and AI-generated features
in Google SERPs using DataForSEO's organic/advanced endpoint.

Feeds the CitationGapEngine and AIVisibilityEngine with real SERP feature data.
"""
from __future__ import annotations

import os
import time
from typing import Any

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

BASE_URL = "https://api.dataforseo.com/v3"
DEFAULT_LOCATION = 2840  # US
DEFAULT_LANGUAGE = "en"


class SERPAIConnector:
    """
    Queries DataForSEO to detect AI-generated SERP features for GEO target queries.
    Falls back to empty results when not configured — never crashes the agent.
    """

    # DataForSEO SERP item types that signal AI answer presence
    AI_FEATURE_TYPES = {
        "ai_overview",
        "generative_answer",
        "featured_snippet",
        "people_also_ask",
        "knowledge_graph",
        "rich_snippet",
        "discussions_and_forums",
    }

    def __init__(self, login: str = "", password: str = "") -> None:
        import base64
        self.login    = login    or os.environ.get("DATAFORSEO_LOGIN", "")
        self.password = password or os.environ.get("DATAFORSEO_PASSWORD", "")
        self._configured = bool(self.login and self.password and _HAS_REQUESTS)
        if self._configured:
            token = base64.b64encode(f"{self.login}:{self.password}".encode()).decode()
            self._headers = {
                "Authorization": f"Basic {token}",
                "Content-Type": "application/json",
            }

    @property
    def is_configured(self) -> bool:
        return self._configured

    def check_queries(
        self,
        queries: list[str],
        location_code: int = DEFAULT_LOCATION,
        delay: float = 0.25,
    ) -> list[dict[str, Any]]:
        """
        Check a list of queries for AI-generated SERP features.

        Returns list of dicts:
          keyword, has_ai_overview, has_paa, has_featured_snippet,
          has_knowledge_graph, item_types (all types found)
        """
        if not self.is_configured:
            return self._empty_results(queries)

        results = []
        for query in queries:
            result = self._check_single(query, location_code)
            results.append(result)
            if delay:
                time.sleep(delay)

        return results

    def check_queries_batch(
        self,
        queries: list[str],
        location_code: int = DEFAULT_LOCATION,
        batch_size: int = 5,
    ) -> list[dict[str, Any]]:
        """Batch check — groups queries to minimise API calls."""
        all_results = []
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            all_results.extend(self.check_queries(batch, location_code, delay=0.2))
        return all_results

    def ai_overview_queries(self, results: list[dict]) -> list[str]:
        """Return only queries where an AI Overview was detected."""
        return [r["keyword"] for r in results if r.get("has_ai_overview")]

    def paa_queries(self, results: list[dict]) -> list[str]:
        """Return queries where People Also Ask boxes are present."""
        return [r["keyword"] for r in results if r.get("has_paa")]

    def featured_snippet_queries(self, results: list[dict]) -> list[str]:
        """Return queries where a featured snippet is present (position-0 opportunity)."""
        return [r["keyword"] for r in results if r.get("has_featured_snippet")]

    # ── Internals ──────────────────────────────────────────────────────────────

    def _check_single(self, query: str, location_code: int) -> dict[str, Any]:
        payload = [{
            "keyword": query,
            "location_code": location_code,
            "language_code": DEFAULT_LANGUAGE,
            "device": "desktop",
        }]
        try:
            resp = _requests.post(
                f"{BASE_URL}/serp/google/organic/live/advanced",
                json=payload,
                headers=self._headers,
                timeout=20,
            )
            if resp.status_code == 403:
                body = resp.text
                if "40104" in body or "verify" in body.lower():
                    return self._empty_result(query, error="account_not_verified")
            resp.raise_for_status()
            data = resp.json()

            item_types: set[str] = set()
            for task in data.get("tasks", []):
                for result in (task.get("result") or []):
                    for item in (result.get("items") or []):
                        item_types.add(item.get("type", ""))

            return {
                "keyword":              query,
                "has_ai_overview":      "ai_overview" in item_types or "generative_answer" in item_types,
                "has_paa":              "people_also_ask" in item_types,
                "has_featured_snippet": "featured_snippet" in item_types,
                "has_knowledge_graph":  "knowledge_graph" in item_types,
                "item_types":           sorted(item_types & self.AI_FEATURE_TYPES),
                "source":               "dataforseo",
            }
        except Exception as exc:
            return self._empty_result(query, error=str(exc))

    @staticmethod
    def _empty_result(query: str, error: str = "") -> dict[str, Any]:
        return {
            "keyword":              query,
            "has_ai_overview":      False,
            "has_paa":              False,
            "has_featured_snippet": False,
            "has_knowledge_graph":  False,
            "item_types":           [],
            "source":               "not_configured" if not error else "error",
            "error":                error,
        }

    @staticmethod
    def _empty_results(queries: list[str]) -> list[dict[str, Any]]:
        return [SERPAIConnector._empty_result(q, error="not_configured") for q in queries]
