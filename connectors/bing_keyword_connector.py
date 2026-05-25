from __future__ import annotations

import os
from typing import Any

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

BING_API_BASE = "https://ssl.bing.com/webmaster/api.svc/json"


class BingKeywordConnector:
    """
    Bing Webmaster Tools API connector for keyword performance data.

    Provides real impression, click, CTR, and position data for keywords
    that Bing has search data on for the verified site.

    Uses simple API key auth (Settings → API Access in Bing Webmaster Tools).
    Falls back gracefully when not configured or on error.
    """

    def __init__(
        self,
        api_key: str = "",
        site_url: str = "https://pipeleap.com",
    ) -> None:
        self.api_key = api_key or os.environ.get("BING_API_KEY", "")
        self.site_url = site_url.rstrip("/")
        self.is_configured = bool(self.api_key and _HAS_REQUESTS)

    def get_query_stats(self) -> list[dict[str, Any]]:
        """
        Fetch keyword-level search performance from Bing for the last 30 days.

        Returns list of dicts with keys:
          query, impressions, clicks, ctr, position
        """
        if not self.is_configured:
            return []

        try:
            resp = _requests.get(
                f"{BING_API_BASE}/GetQueryStats",
                params={"apikey": self.api_key, "siteUrl": self.site_url},
                timeout=15,
            )
            if resp.status_code != 200:
                return []

            data = resp.json()
            raw = data.get("d", [])
            results = []
            for item in raw:
                query = item.get("Query", "").strip().lower()
                if not query:
                    continue
                results.append({
                    "query":       query,
                    "impressions": int(item.get("Impressions", 0)),
                    "clicks":      int(item.get("Clicks", 0)),
                    "ctr":         round(float(item.get("CTR", 0)), 4),
                    "position":    round(float(item.get("P_Position", 0)), 1),
                    "source":      "bing_webmaster",
                })
            return results
        except Exception:
            return []

    def enrich_keyword_metrics(
        self,
        keywords: list[str],
    ) -> dict[str, dict[str, Any]]:
        """
        Build a lookup dict of {keyword: {impressions, clicks, ctr, position}}
        from Bing data for the given keyword list.
        """
        stats = self.get_query_stats()
        return {s["query"]: s for s in stats if s["query"] in keywords}
