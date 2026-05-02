"""
DataForSEO API connector — full integration for Pipeleap SEO agent.

Capabilities:
  get_keyword_metrics()       — real search volume, CPC, competition for known keywords
  get_keyword_suggestions()   — discover NEW keywords from seed terms (keyword ideas API)
  get_competitor_keywords()   — keywords a competitor domain ranks for
  get_serp_features()         — detect featured snippet, AI Overview, PAA for a keyword
  get_keyword_difficulty()    — DataForSEO keyword difficulty scores

Credentials:
  Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD as GitHub Actions secrets.
  config.yaml references them via ${DATAFORSEO_LOGIN} / ${DATAFORSEO_PASSWORD}.
  Falls back to heuristic estimates when not configured — zero breaking changes.

Docs: https://docs.dataforseo.com/v3/
Pricing: ~$0.0005–$0.002 per keyword for volume; $0.002 per SERP check.
"""
from __future__ import annotations

import base64
import os
import time
from typing import Any

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


class DataForSEOConnector:
    BASE_URL = "https://api.dataforseo.com/v3"

    # Default US location; 2826 = UK, 2036 = Australia, 2124 = Canada
    DEFAULT_LOCATION = 2840
    DEFAULT_LANGUAGE = "en"

    # DataForSEO batch limit per request task array
    _BATCH_SIZE = 100

    def __init__(self, login: str = "", password: str = "") -> None:
        self.login = login or os.environ.get("DATAFORSEO_LOGIN", "")
        self.password = password or os.environ.get("DATAFORSEO_PASSWORD", "")
        self._configured = bool(self.login and self.password)

    @property
    def is_configured(self) -> bool:
        return self._configured and _HAS_REQUESTS

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _auth_header(self) -> dict[str, str]:
        token = base64.b64encode(f"{self.login}:{self.password}".encode()).decode()
        return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

    def _post(self, endpoint: str, payload: list[dict], timeout: int = 45) -> dict:
        url = f"{self.BASE_URL}/{endpoint}"
        resp = _requests.post(url, json=payload, headers=self._auth_header(), timeout=timeout)
        if resp.status_code == 403:
            body = resp.text
            if "40104" in body or "verify your account" in body.lower():
                raise RuntimeError(
                    "DataForSEO account not verified. "
                    "Go to https://app.dataforseo.com and complete verification, "
                    "then retry. Credentials are correct."
                )
        resp.raise_for_status()
        return resp.json()

    # ── 1. Search volume + CPC for known keywords ─────────────────────────────

    def get_keyword_metrics(
        self,
        keywords: list[str],
        location_code: int = DEFAULT_LOCATION,
    ) -> list[dict[str, Any]]:
        """
        Fetch real search volume, CPC, and competition for a list of known keywords.
        Batches requests automatically (100 keywords per API task).
        Falls back to heuristic estimates if not configured.
        """
        if not self.is_configured:
            return self._heuristic_fallback(keywords)

        results: list[dict] = []
        try:
            # Split into batches of _BATCH_SIZE
            for i in range(0, len(keywords), self._BATCH_SIZE):
                batch = keywords[i:i + self._BATCH_SIZE]
                payload = [{
                    "keywords": batch,
                    "location_code": location_code,
                    "language_code": self.DEFAULT_LANGUAGE,
                    "search_partners": False,
                }]
                data = self._post("keywords_data/google_ads/search_volume/live", payload)
                for task in data.get("tasks", []):
                    # DataForSEO returns keyword objects directly in result[], not nested under items[]
                    for kw_item in (task.get("result") or []):
                        kw = kw_item.get("keyword", "")
                        if not kw:
                            continue
                        results.append({
                            "keyword":           kw,
                            "search_volume":     kw_item.get("search_volume") or 0,
                            "cpc":               round(float(kw_item.get("cpc") or 0), 2),
                            "competition":       kw_item.get("competition", ""),        # "LOW"/"MEDIUM"/"HIGH"
                            "competition_index": kw_item.get("competition_index") or 0, # 0-100
                            "low_bid":           round(float(kw_item.get("low_top_of_page_bid") or 0), 2),
                            "high_bid":          round(float(kw_item.get("high_top_of_page_bid") or 0), 2),
                            "monthly_searches":  kw_item.get("monthly_searches") or [],
                            "source":            "dataforseo",
                        })
                # Respect rate limits between batches
                if i + self._BATCH_SIZE < len(keywords):
                    time.sleep(0.5)
        except Exception as exc:
            return self._heuristic_fallback(keywords, error=str(exc))

        return results

    # ── 2. Keyword discovery from seed terms ──────────────────────────────────

    def get_keyword_suggestions(
        self,
        seed_keywords: list[str],
        location_code: int = DEFAULT_LOCATION,
        limit_per_seed: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Discover NEW keyword ideas from seed terms using DataForSEO's
        Keywords for Keywords API. Returns related keywords with real volume.

        This is the most valuable endpoint — it finds organic keywords
        the seed list doesn't know about yet.
        """
        if not self.is_configured:
            return []

        discovered: list[dict] = []
        seen: set[str] = set()

        try:
            for seed in seed_keywords[:20]:  # cap at 20 seeds per run to manage cost
                payload = [{
                    "keywords": [seed],
                    "location_code": location_code,
                    "language_code": self.DEFAULT_LANGUAGE,
                    "limit": limit_per_seed,
                    "filters": [
                        ["search_volume", ">", 10],       # only keywords with real traffic
                        ["competition_level", "<>", "HIGH"],  # avoid highly competitive
                    ],
                }]
                data = self._post("keywords_data/google_ads/keywords_for_keywords/live", payload)
                for task in data.get("tasks", []):
                    # Same flat structure as search_volume: result[] contains keyword objects directly
                    for kw_item in (task.get("result") or []):
                        kw = (kw_item.get("keyword") or "").strip().lower()
                        if not kw or kw in seen:
                            continue
                        seen.add(kw)
                        discovered.append({
                            "keyword":           kw,
                            "search_volume":     kw_item.get("search_volume") or 0,
                            "cpc":               round(float(kw_item.get("cpc") or 0), 2),
                            "competition":       kw_item.get("competition", ""),
                            "competition_index": kw_item.get("competition_index") or 0,
                            "seed_keyword":      seed,
                            "source":            "dataforseo_suggestions",
                        })
                time.sleep(0.3)
        except Exception as exc:
            # Non-fatal — keyword discovery is best-effort
            pass

        # Sort by search volume descending
        return sorted(discovered, key=lambda x: x["search_volume"], reverse=True)

    # ── 3. Competitor keyword analysis ────────────────────────────────────────

    def get_competitor_keywords(
        self,
        domain: str,
        location_code: int = DEFAULT_LOCATION,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Find keywords a competitor domain ranks for that Pipeleap doesn't.
        Used by the backlink_gap and keyword gap analysis engines.
        """
        if not self.is_configured:
            return []

        try:
            payload = [{
                "target": domain.replace("https://", "").replace("http://", "").strip("/"),
                "location_code": location_code,
                "language_code": self.DEFAULT_LANGUAGE,
                "limit": limit,
                "filters": [["search_volume", ">", 50]],
                "order_by": ["search_volume,desc"],
            }]
            data = self._post("keywords_data/google_ads/keywords_for_site/live", payload)
            results = []
            for task in data.get("tasks", []):
                for item in (task.get("result") or []):
                    for kw_item in (item.get("items") or []):
                        kw = kw_item.get("keyword", "").strip()
                        if kw:
                            results.append({
                                "keyword":       kw,
                                "search_volume": kw_item.get("search_volume") or 0,
                                "cpc":           round(float(kw_item.get("cpc") or 0), 2),
                                "competitor":    domain,
                                "source":        "dataforseo_competitor",
                            })
            return results
        except Exception:
            return []

    # ── 4. SERP feature detection ─────────────────────────────────────────────

    def get_serp_features(
        self,
        keyword: str,
        location_code: int = DEFAULT_LOCATION,
    ) -> dict[str, Any]:
        """
        Detect which SERP features appear for a keyword:
        featured_snippet, people_also_ask, knowledge_graph, ai_overview, images, etc.
        Used by CTREngine to validate snippet targets and adjust ctr_score.
        """
        if not self.is_configured:
            return {"keyword": keyword, "features": [], "has_featured_snippet": False, "source": "not_configured"}

        try:
            payload = [{
                "keyword": keyword,
                "location_code": location_code,
                "language_code": self.DEFAULT_LANGUAGE,
                "device": "desktop",
                "os": "windows",
            }]
            data = self._post("serp/google/organic/live/advanced", payload)

            features = set()
            featured_snippet_present = False
            paa_count = 0
            ai_overview_present = False

            for task in data.get("tasks", []):
                for result in (task.get("result") or []):
                    for item in (result.get("items") or []):
                        item_type = item.get("type", "")
                        if item_type == "featured_snippet":
                            features.add("featured_snippet")
                            featured_snippet_present = True
                        elif item_type == "people_also_ask":
                            features.add("people_also_ask")
                            paa_count += 1
                        elif item_type == "knowledge_graph":
                            features.add("knowledge_graph")
                        elif item_type in ("ai_overview", "generative_answer"):
                            features.add("ai_overview")
                            ai_overview_present = True
                        elif item_type in ("images", "videos", "local_pack"):
                            features.add(item_type)

            return {
                "keyword":                keyword,
                "features":               sorted(features),
                "has_featured_snippet":   featured_snippet_present,
                "has_paa":                paa_count > 0,
                "paa_count":              paa_count,
                "has_ai_overview":        ai_overview_present,
                "source":                 "dataforseo",
            }
        except Exception as exc:
            return {"keyword": keyword, "features": [], "has_featured_snippet": False,
                    "source": "error", "error": str(exc)}

    # ── 5. Keyword difficulty scores ──────────────────────────────────────────

    def get_keyword_difficulty(
        self,
        keywords: list[str],
        location_code: int = DEFAULT_LOCATION,
    ) -> list[dict[str, Any]]:
        """
        Fetch DataForSEO's keyword difficulty score (0–100) for a list of keywords.
        More accurate than heuristic difficulty estimates for prioritisation.
        """
        if not self.is_configured:
            return []

        results = []
        try:
            for i in range(0, len(keywords), self._BATCH_SIZE):
                batch = keywords[i:i + self._BATCH_SIZE]
                payload = [{
                    "keywords": batch,
                    "location_code": location_code,
                    "language_code": self.DEFAULT_LANGUAGE,
                }]
                data = self._post("keywords_data/dataforseo_labs/google/keyword_difficulty/live", payload)
                for task in data.get("tasks", []):
                    for kw_item in (task.get("result") or []):
                        kw = (kw_item.get("keyword") or "").strip()
                        difficulty = kw_item.get("keyword_difficulty")
                        if kw and difficulty is not None:
                            results.append({
                                "keyword":    kw,
                                "difficulty": round(float(difficulty), 1),
                                "source":     "dataforseo",
                            })
                if i + self._BATCH_SIZE < len(keywords):
                    time.sleep(0.3)
        except Exception:
            pass

        return results

    # ── 6. Bulk SERP feature check for keyword matrix ─────────────────────────

    def check_snippet_opportunities(
        self,
        keywords: list[str],
        location_code: int = DEFAULT_LOCATION,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Check a batch of keywords for featured snippet and PAA opportunities.
        Limits to `limit` keywords to manage API cost.
        Returns only keywords where snippet opportunities exist.
        """
        if not self.is_configured:
            return []

        opportunities = []
        for kw in keywords[:limit]:
            features = self.get_serp_features(kw, location_code)
            if features.get("has_featured_snippet") or features.get("has_paa"):
                opportunities.append(features)
            time.sleep(0.2)  # DataForSEO SERP endpoint rate limit

        return opportunities

    # ── Heuristic fallback ────────────────────────────────────────────────────

    @staticmethod
    def _heuristic_fallback(keywords: list[str], error: str = "") -> list[dict[str, Any]]:
        from utils.ranking_model import estimate_cpc, estimate_difficulty
        results = []
        for kw in keywords:
            intent = "commercial"
            if any(t in kw for t in ["how to", "what is", "guide", "why"]):
                intent = "informational"
            elif any(t in kw for t in ["pricing", "demo", "buy", "alternative"]):
                intent = "transactional"
            results.append({
                "keyword":       kw,
                "search_volume": None,
                "cpc":           estimate_cpc(kw, intent),
                "competition":   estimate_difficulty(kw, intent, []) / 100,
                "source":        "heuristic_fallback",
                "note":          error or "DataForSEO credentials not set",
            })
        return results

    # ── Connection test ───────────────────────────────────────────────────────

    def test_connection(self) -> dict[str, Any]:
        """
        Verify credentials and return account info.
        Run this manually to confirm your API key is working:
          python test_dataforseo.py
        """
        if not self.is_configured:
            return {"ok": False, "error": "DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD not set"}
        try:
            resp = _requests.get(
                f"{self.BASE_URL}/appendix/user_data",
                headers=self._auth_header(),
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            tasks = data.get("tasks", [{}])
            result = (tasks[0].get("result") or [{}])[0] if tasks else {}
            return {
                "ok":       True,
                "email":    result.get("login", ""),
                "balance":  result.get("money", {}).get("balance", "unknown"),
                "currency": result.get("money", {}).get("currency", "USD"),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _check_verified(self, response_body: str) -> bool:
        """Returns False if the account verification error (40104) is in the response."""
        return "40104" not in response_body and "verify your account" not in response_body.lower()
