from __future__ import annotations

import time
from typing import Any

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
_USER_AGENT = "PipeleapSEO/1.0 (seo@pipeleap.com)"
_REQUEST_DELAY = 1.0


class WikipediaConnector:
    """
    MediaWiki API connector for Wikipedia entity enrichment.

    Provides entity search, page summaries, Wikidata lookups, and
    category discovery — all from the free, open MediaWiki API.
    No API key required.

    Rate-limited to 1 req/s per Wikipedia's User-Agent policy.
    Always available (is_configured = True). Falls back to empty
    dicts/lists on any error.
    """

    def __init__(self) -> None:
        self.is_configured = _HAS_REQUESTS
        self._last_request: float = 0.0

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < _REQUEST_DELAY:
            time.sleep(_REQUEST_DELAY - elapsed)
        self._last_request = time.time()

    def _get(self, params: dict[str, str]) -> dict[str, Any]:
        if not self.is_configured:
            return {}
        self._rate_limit()
        try:
            resp = _requests.get(
                WIKIPEDIA_API,
                params={"format": "json", **params},
                headers={"User-Agent": _USER_AGENT},
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json()
            return {}
        except Exception:
            return {}

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if not query.strip():
            return []
        data = self._get({
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": str(min(limit, 50)),
        })
        results: list[dict[str, Any]] = []
        for page in data.get("query", {}).get("search", []):
            results.append({
                "title": page.get("title", ""),
                "page_id": page.get("pageid", 0),
                "snippet": page.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", ""),
                "word_count": page.get("wordcount", 0),
                "timestamp": page.get("timestamp", ""),
            })
        return results

    def get_summary(self, title: str) -> dict[str, Any]:
        if not title.strip():
            return {}
        data = self._get({
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "exintro": "1",
            "explaintext": "1",
        })
        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            if page_id == "-1":
                return {"status": "not_found", "title": title}
            return {
                "status": "found",
                "title": page.get("title", title),
                "page_id": int(page_id) if page_id.isdigit() else 0,
                "extract": page.get("extract", ""),
                "url": f"https://en.wikipedia.org/wiki/{page.get('title', title).replace(' ', '_')}",
            }
        return {"status": "not_found", "title": title}

    def get_wikidata_id(self, title: str) -> dict[str, Any]:
        if not title.strip():
            return {}
        data = self._get({
            "action": "query",
            "titles": title,
            "prop": "pageprops",
            "ppprop": "wikibase_item",
        })
        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            if page_id == "-1":
                return {"status": "not_found", "title": title}
            wikidata_id = page.get("pageprops", {}).get("wikibase_item", "")
            return {
                "status": "found" if wikidata_id else "no_wikidata",
                "title": page.get("title", title),
                "wikidata_id": wikidata_id,
                "wikidata_url": f"https://www.wikidata.org/entity/{wikidata_id}" if wikidata_id else "",
            }
        return {"status": "not_found", "title": title}

    def get_categories(self, title: str) -> list[str]:
        if not title.strip():
            return []
        data = self._get({
            "action": "query",
            "titles": title,
            "prop": "categories",
            "cllimit": "50",
        })
        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            if page_id == "-1":
                return []
            return [
                cat.get("title", "").replace("Category:", "")
                for cat in page.get("categories", [])
            ]
        return []

    def get_entity_info(self, title: str) -> dict[str, Any]:
        summary = self.get_summary(title)
        if summary.get("status") != "found":
            return summary
        wikidata = self.get_wikidata_id(title)
        categories = self.get_categories(title)
        return {
            "status": "found",
            "title": summary.get("title", title),
            "extract": summary.get("extract", ""),
            "url": summary.get("url", ""),
            "page_id": summary.get("page_id", 0),
            "wikidata_id": wikidata.get("wikidata_id", ""),
            "wikidata_url": wikidata.get("wikidata_url", ""),
            "categories": categories,
        }

    def enrich_entity(self, brand_name: str) -> dict[str, Any]:
        info = self.get_entity_info(brand_name)
        if info.get("status") == "found":
            info["has_wikipedia_page"] = True
            info["wikipedia_url"] = info["url"]
            return info
        info["has_wikipedia_page"] = False
        info["wikipedia_url"] = ""
        return info
