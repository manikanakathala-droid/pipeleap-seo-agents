"""
IndexNow Connector — instant URL submission to Bing, Yandex, Seznam, Naver.

IndexNow is a free open protocol that instantly notifies search engines when
content is published or updated — no GCP setup, no daily quotas, no service
account required. Google has confirmed they're monitoring IndexNow signals.

How it works:
  1. Place a key file at https://pipeleap.com/{key}.txt
  2. POST new/updated URLs to the IndexNow API
  3. Bing, Yandex, Naver, Seznam index the URLs within minutes-hours

Key advantages over Google Indexing API:
  - No API enablement required
  - No daily quota (Bing recommends batches of 10,000)
  - Covers Bing (3B+ searches/month), Yandex, DuckDuckGo (uses Bing)
  - Instant — typically indexed within 24 hours

Docs: https://www.indexnow.org/
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

# IndexNow endpoints (all cross-notify each other)
INDEXNOW_ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://yandex.com/indexnow",
]

# Pipeleap's IndexNow key — must match the key file at https://pipeleap.com/{key}.txt
INDEXNOW_KEY = "pipeleap-indexnow-2026"
KEY_LOCATION  = f"https://pipeleap.com/{INDEXNOW_KEY}.txt"
SITE_URL      = "https://pipeleap.com"


class IndexNowConnector:
    """
    Submits URLs to Bing/Yandex/DuckDuckGo via IndexNow protocol.
    Requires a key file to be placed at: pipeleap.com/{INDEXNOW_KEY}.txt
    """

    def __init__(self) -> None:
        self.key          = INDEXNOW_KEY
        self.key_location = KEY_LOCATION
        self.site_url     = SITE_URL

    @property
    def key_file_content(self) -> str:
        """Content of the key file that must be placed at the domain root."""
        return self.key

    def submit_urls(
        self,
        urls: list[str],
        endpoint: str = INDEXNOW_ENDPOINTS[0],
    ) -> dict[str, Any]:
        """
        Submit a batch of URLs to IndexNow.
        Returns {"ok": True, "submitted": N} or {"ok": False, "error": str}.
        """
        if not _HAS_REQUESTS:
            return {"ok": False, "error": "requests library not installed"}
        if not urls:
            return {"ok": True, "submitted": 0}

        payload = {
            "host":        self.site_url.replace("https://", "").replace("http://", ""),
            "key":         self.key,
            "keyLocation": self.key_location,
            "urlList":     urls[:10000],  # IndexNow max per request
        }

        try:
            resp = _requests.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=15,
            )
            if resp.status_code in (200, 202):
                return {"ok": True, "submitted": len(urls), "status": resp.status_code}
            return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def submit_all_endpoints(self, urls: list[str]) -> list[dict]:
        """Submit to all IndexNow endpoints for maximum coverage."""
        results = []
        for endpoint in INDEXNOW_ENDPOINTS:
            result = self.submit_urls(urls, endpoint)
            result["endpoint"] = endpoint
            results.append(result)
            time.sleep(0.5)
        return results

    def submit_sitemap_urls(self, sitemap_path: str | Path) -> dict[str, Any]:
        """Extract all URLs from a sitemap file and submit them."""
        try:
            from xml.etree import ElementTree as ET
            content = Path(sitemap_path).read_text(encoding="utf-8")
            root    = ET.fromstring(content)
            ns      = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
            urls    = [
                u.find(f"{ns}loc").text
                for u in root.findall(f"{ns}url")
                if u.find(f"{ns}loc") is not None
            ]
            if not urls:
                return {"ok": False, "error": "no URLs found in sitemap"}
            results = self.submit_all_endpoints(urls)
            ok_count = sum(1 for r in results if r.get("ok"))
            return {
                "ok": ok_count > 0,
                "urls_submitted": len(urls),
                "endpoints_ok": ok_count,
                "endpoints_total": len(INDEXNOW_ENDPOINTS),
                "results": results,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def generate_key_file(self, output_dir: str | Path) -> str:
        """
        Write the IndexNow key file to public/ directory.
        This file must be deployed at https://pipeleap.com/{key}.txt
        """
        path = Path(output_dir) / f"{self.key}.txt"
        path.write_text(self.key, encoding="utf-8")
        return str(path)
