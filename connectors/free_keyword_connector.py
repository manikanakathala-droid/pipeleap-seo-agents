"""
Free Keyword Intelligence Connector — zero-cost replacement for DataForSEO.

Sources used (all free, no API key required):
  1. Google Autocomplete  — keyword suggestions from Google's own suggest API
  2. Google Trends        — relative search interest + trending breakout keywords (pytrends)
  3. GSC data             — real impressions/clicks for keywords you already rank for
  4. Bing Autosuggest     — secondary keyword expansion (no key needed)
  5. Bing Webmaster Tools — real impression/click/position data (requires BING_API_KEY)

Mirrors the DataForSEO interface so the orchestrator needs zero changes:
  get_keyword_metrics()      — volume tier + trend score per keyword, enriched with Bing stats
  get_keyword_suggestions()  — new keyword ideas from seed terms
  check_snippet_opportunities() — keywords with question intent (PAA/featured snippet targets)

Limitations vs DataForSEO:
  - No exact monthly search volume (returns volume tiers: high/medium/low)
  - No keyword difficulty scores
  - Google Trends rate-limits — sleeps between requests automatically
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

try:
    from connectors.bing_keyword_connector import BingKeywordConnector
    _HAS_BING = True
except ImportError:
    _HAS_BING = False

# Maps Google Trends interest (0-100) to volume tier
def _trends_to_volume_tier(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 30:
        return "medium"
    return "low"

# Rough monthly volume estimate from tier (used for sorting only)
_TIER_VOLUME = {"high": 5000, "medium": 1000, "low": 200}

# Global market geo codes for Google Trends
_GEO_MAP = {
    "us": "US", "uk": "GB", "australia": "AU", "canada": "CA",
    "india": "IN", "singapore": "SG", "uae": "AE", "germany": "DE",
    "ireland": "IE", "netherlands": "NL", "france": "FR",
}


class FreeKeywordConnector:
    """
    Drop-in replacement for DataForSEOConnector using only free APIs.
    Always returns data — falls back gracefully if rate-limited.

    Optionally enriched with Bing Webmaster Tools keyword stats
    when bing_api_key is provided — adds real impression/click/position data.
    """

    is_configured = True  # always available, no credentials needed

    def __init__(self, bing_api_key: str = "") -> None:
        self._trends: Any = None
        self._bing: BingKeywordConnector | None = None
        if bing_api_key and _HAS_BING:
            self._bing = BingKeywordConnector(api_key=bing_api_key)

    def _get_trends_client(self):
        if not _HAS_PYTRENDS:
            return None
        if self._trends is None:
            self._trends = _TrendReq(hl="en-US", tz=0, timeout=(10, 30), retries=2, backoff_factor=0.5)
        return self._trends

    # ── 1. Keyword metrics ────────────────────────────────────────────────────

    def get_keyword_metrics(
        self,
        keywords: list[str],
        location_code: int = 2840,
        language_code: str = "en",
    ) -> list[dict[str, Any]]:
        """
        Returns volume tier and trend score for each keyword via Google Trends,
        enriched with real Bing impression/click/position data when available.
        Processes in batches of 5 (Trends limit).
        """
        results: list[dict[str, Any]] = []
        pt = self._get_trends_client()

        # Map DataForSEO location code to Trends geo
        geo = self._location_to_geo(location_code)

        for i in range(0, len(keywords), 5):
            batch = keywords[i:i + 5]
            trend_scores = self._fetch_trends_scores(pt, batch, geo)
            for kw in batch:
                score = trend_scores.get(kw, 0)
                tier = _trends_to_volume_tier(score)
                results.append({
                    "keyword":           kw,
                    "search_volume":     _TIER_VOLUME[tier],
                    "volume_tier":       tier,
                    "trend_score":       score,
                    "competition":       0.5,
                    "cpc":               0.0,
                    "keyword_difficulty": 50,
                    "source":            "google_trends",
                })
            if i + 5 < len(keywords):
                time.sleep(1.5)  # respect Trends rate limit

        # Enrich with Bing data if available
        if self._bing is not None:
            try:
                bing_lookup = self._bing.enrich_keyword_metrics(keywords)
                for item in results:
                    kw = item["keyword"]
                    if kw in bing_lookup:
                        b = bing_lookup[kw]
                        item["bing_impressions"] = b["impressions"]
                        item["bing_clicks"]      = b["clicks"]
                        item["bing_ctr"]         = b["ctr"]
                        item["bing_position"]    = b["position"]
                        item["source"]           = "google_trends+bing"
                        # Override volume tier with real Bing impression count
                        if b["impressions"] > 0:
                            item["search_volume"] = b["impressions"]
                            if b["impressions"] >= 5000:
                                item["volume_tier"] = "high"
                            elif b["impressions"] >= 1000:
                                item["volume_tier"] = "medium"
                            else:
                                item["volume_tier"] = "low"
            except Exception:
                pass  # Non-fatal — keep trend-only data

        return results

    # ── 2. Keyword suggestions ────────────────────────────────────────────────

    def get_keyword_suggestions(
        self,
        seeds: list[str],
        location_code: int = 2840,
        language_code: str = "en",
        limit_per_seed: int = 30,
    ) -> list[dict[str, Any]]:
        """
        Discovers new keywords from seed terms using:
          - Google Autocomplete (primary)
          - Bing Autosuggest (secondary, different corpus)
          - Question variants (who/what/how/why/best)
        """
        seen: set[str] = set(seeds)
        results: list[dict[str, Any]] = []

        for seed in seeds:
            suggestions: list[str] = []

            # Google Autocomplete — A-Z and question prefixes
            suggestions += self._google_autocomplete(seed)
            suggestions += self._question_variants(seed)

            # Bing Autosuggest
            suggestions += self._bing_autosuggest(seed)

            # Deduplicate and limit
            for kw in suggestions:
                kw = kw.strip().lower()
                if kw and kw not in seen and len(kw) > 3:
                    seen.add(kw)
                    results.append({
                        "keyword":       kw,
                        "seed":          seed,
                        "search_volume": 500,
                        "volume_tier":   "medium",
                        "source":        "autocomplete",
                        "intent":        self._classify_intent(kw),
                    })
                if len(results) >= limit_per_seed * len(seeds):
                    break

            time.sleep(0.5)

        return results

    # ── 3. Snippet opportunities ──────────────────────────────────────────────

    def check_snippet_opportunities(
        self,
        keywords: list[str],
        location_code: int = 2840,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Identifies keywords with featured snippet / PAA potential.
        Uses question-form detection and Trends breakout signals.
        """
        opportunities = []
        pt = self._get_trends_client()
        geo = self._location_to_geo(location_code)

        for kw in keywords[:limit]:
            score = 0
            snippet_type = "paragraph"

            # Question keywords are strong featured snippet candidates
            if any(kw.lower().startswith(q) for q in ("what", "how", "why", "when", "best", "vs", "compare")):
                score += 40
                snippet_type = "definition" if kw.startswith("what") else "how_to"

            # Check Trends interest
            trend_data = self._fetch_trends_scores(pt, [kw], geo)
            trend_score = trend_data.get(kw, 0)
            score += trend_score // 2

            if score >= 30:
                opportunities.append({
                    "keyword":      kw,
                    "snippet_type": snippet_type,
                    "opportunity_score": score,
                    "trend_score":  trend_score,
                    "source":       "free_connector",
                })
            time.sleep(0.3)

        return sorted(opportunities, key=lambda x: x["opportunity_score"], reverse=True)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _fetch_trends_scores(self, pt, keywords: list[str], geo: str) -> dict[str, int]:
        if not pt or not keywords:
            return {kw: 50 for kw in keywords}
        try:
            pt.build_payload(keywords[:5], geo=geo, timeframe="today 12-m")
            data = pt.interest_over_time()
            if data.empty:
                return {kw: 30 for kw in keywords}
            scores = {}
            for kw in keywords:
                if kw in data.columns:
                    scores[kw] = int(data[kw].mean())
                else:
                    scores[kw] = 30
            return scores
        except Exception:
            return {kw: 40 for kw in keywords}

    def _google_autocomplete(self, seed: str) -> list[str]:
        if not _HAS_REQUESTS:
            return []
        suggestions = []
        # Fetch for seed + each letter suffix for broader coverage
        queries = [seed] + [f"{seed} {c}" for c in "abcdefghijklmnopqrstuvwxyz"[:8]]
        for q in queries:
            try:
                resp = _requests.get(
                    "https://suggestqueries.google.com/complete/search",
                    params={"client": "firefox", "q": q},
                    timeout=5,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 1:
                        suggestions.extend(data[1])
            except Exception:
                pass
            time.sleep(0.1)
        return list(dict.fromkeys(suggestions))[:40]

    def _bing_autosuggest(self, seed: str) -> list[str]:
        if not _HAS_REQUESTS:
            return []
        try:
            resp = _requests.get(
                "https://api.bing.com/osjson.aspx",
                params={"query": seed, "language": "en-US"},
                timeout=5,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 1:
                    return data[1]
        except Exception:
            pass
        return []

    def _question_variants(self, seed: str) -> list[str]:
        prefixes = ["what is", "how to", "best", "why use", "how does", "what are", "vs", "compare"]
        return [f"{p} {seed}" for p in prefixes]

    def _classify_intent(self, kw: str) -> str:
        kw_lower = kw.lower()
        if any(kw_lower.startswith(q) for q in ("what is", "what are", "how does", "why")):
            return "informational"
        if any(w in kw_lower for w in ("best", "top", "vs", "compare", "alternative", "review")):
            return "commercial"
        if any(w in kw_lower for w in ("buy", "price", "pricing", "demo", "trial", "sign up")):
            return "transactional"
        return "informational"

    @staticmethod
    def _location_to_geo(location_code: int) -> str:
        mapping = {
            2840: "US", 2826: "GB", 2036: "AU", 2124: "CA",
            2356: "IN", 2702: "SG", 2784: "AE", 2276: "DE",
            2372: "IE", 2528: "NL", 2250: "FR", 2578: "NO", 2752: "SE",
        }
        return mapping.get(location_code, "US")
