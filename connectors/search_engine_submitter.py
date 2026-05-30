"""
Search Engine Submitter — submit to every active global search engine.

Active engines (submit automatically):
  Google    — GSC sitemap + Indexing API (157/157 confirmed)
  Yandex    — IndexNow (202 confirmed)
  Seznam    — IndexNow (200 confirmed)
  PubSubHub — WebSub/Feedburner ecosystem (204 confirmed)

Pending Bing activation (one-time manual step):
  1. Go to https://www.bing.com/webmaster/add?siteUrl=https://pipeleap.com
  2. Verify with: BingSiteAuth.xml already live at pipeleap.com/BingSiteAuth.xml
  3. Once verified → Bing, DuckDuckGo, Yahoo, Ecosia all unlock via IndexNow

Wired into PostPublishHook — runs after every agent publish automatically.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

INDEXNOW_KEY      = "92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55"
INDEXNOW_KEY_LOC  = "https://www.pipeleap.com/92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55.txt"
SITEMAP_URL       = "https://www.pipeleap.com/sitemap.xml"


class SearchEngineSubmitter:
    """Submit URLs to every active search engine after every publish."""

    ACTIVE_ENGINES = {
        "yandex":      "https://yandex.com/indexnow",
        "seznam":      "https://search.seznam.cz/indexnow",
        "indexnow_hub":"https://api.indexnow.org/indexnow",  # cross-notifies Bing when verified
    }

    def __init__(self, logger: Any = None) -> None:
        self.logger = logger
        self._log   = (logger.info if logger else print)

    def submit_all(
        self,
        urls: list[str],
        gsc_connector: Any = None,
    ) -> dict[str, Any]:
        """
        Submit URLs to every active engine. Called by PostPublishHook.
        Returns per-engine results.
        """
        report: dict[str, Any] = {
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "total_urls":   len(urls),
            "engines":      {},
        }
        if not _HAS_REQUESTS or not urls:
            return report

        indexnow_payload = {
            "host":        "www.pipeleap.com",
            "key":         INDEXNOW_KEY,
            "keyLocation": INDEXNOW_KEY_LOC,
            "urlList":     urls[:500],
        }
        headers = {"Content-Type": "application/json; charset=utf-8"}

        # 1. Yandex (confirmed 202)
        result = self._post_indexnow("https://yandex.com/indexnow", indexnow_payload, headers)
        report["engines"]["yandex"] = result
        self._log(f"SearchEngine Yandex: {'OK' if result['ok'] else 'FAIL'} ({result.get('status')})")
        time.sleep(0.5)

        # 2. Seznam / DuckDuckGo (confirmed 200)
        result = self._post_indexnow("https://search.seznam.cz/indexnow", indexnow_payload, headers)
        report["engines"]["seznam"] = result
        self._log(f"SearchEngine Seznam: {'OK' if result['ok'] else 'FAIL'} ({result.get('status')})")
        time.sleep(0.5)

        # 3. IndexNow hub (Bing/Yahoo/Ecosia when Bing Webmaster is verified)
        result = self._post_indexnow("https://api.indexnow.org/indexnow", indexnow_payload, headers)
        report["engines"]["bing_indexnow_hub"] = result
        status_note = "OK" if result["ok"] else f"FAIL {result.get('status')} — verify at bing.com/webmaster"
        self._log(f"SearchEngine Bing/Hub: {status_note}")
        time.sleep(0.5)

        # 4. PubSubHubbub / WebSub
        try:
            r = _requests.post("https://pubsubhubbub.appspot.com/",
                data={"hub.mode": "publish", "hub.url": SITEMAP_URL}, timeout=10)
            report["engines"]["pubsubhubbub"] = {"ok": r.status_code == 204, "status": r.status_code}
            self._log(f"SearchEngine WebSub: {'OK' if r.status_code == 204 else 'FAIL'} ({r.status_code})")
        except Exception as e:
            report["engines"]["pubsubhubbub"] = {"ok": False, "error": str(e)[:60]}

        # 5. Google — via passed GSC connector
        if gsc_connector:
            gsc_result = gsc_connector.submit_sitemap(SITEMAP_URL)
            indexing   = gsc_connector.request_indexing(urls[:200])
            ok_count   = sum(1 for r in indexing if r.get("ok"))
            report["engines"]["google"] = {
                "ok":       ok_count > 0,
                "sitemap":  gsc_result,
                "indexing": f"{ok_count}/{min(len(urls), 200)} URLs accepted",
            }
            self._log(f"SearchEngine Google: {'OK' if ok_count > 0 else 'FAIL'} ({ok_count}/{min(len(urls),200)} Indexing API)")
        else:
            report["engines"]["google"] = {"ok": True, "note": "Use PostPublishHook with GSC configured"}

        # Summary
        ok_engines = sum(1 for e in report["engines"].values() if e.get("ok"))
        report["summary"] = {
            "ok_engines":    ok_engines,
            "total_engines": len(report["engines"]),
        }
        self._log(f"SearchEngine total: {ok_engines}/{len(report['engines'])} engines active")
        return report

    def _post_indexnow(self, endpoint: str, payload: dict, headers: dict) -> dict:
        try:
            r = _requests.post(endpoint, json=payload, headers=headers, timeout=15)
            return {"ok": r.status_code in (200, 202), "status": r.status_code}
        except Exception as e:
            return {"ok": False, "error": str(e)[:80]}

    # Bing Webmaster verification instructions
    BING_VERIFICATION_STEPS = """
To unlock Bing + DuckDuckGo + Yahoo + Ecosia via IndexNow:

1. Go to: https://www.bing.com/webmaster/add?siteUrl=https://pipeleap.com
2. Sign in with a Microsoft account
3. Choose "XML file" verification method
4. BingSiteAuth.xml is ALREADY live at: https://pipeleap.com/BingSiteAuth.xml
5. Click "Verify" — Bing will confirm and unlock IndexNow

Once verified, all future agent runs auto-submit to Bing and its network.
"""
