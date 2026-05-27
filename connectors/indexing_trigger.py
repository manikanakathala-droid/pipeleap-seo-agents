import json
import logging
import os
import urllib.request
from typing import Any

log = logging.getLogger(__name__)

class IndexingTrigger:
    def submit_urls(self, urls: list[str]) -> dict[str, Any]:
        results: dict[str, Any] = {}
        
        # We try each platform without failing the whole process
        try:
            results["google"] = self._submit_google(urls)
        except Exception as e:
            log.error("Google Indexing API failed: %s", e)
            results["google"] = {"error": str(e)}

        try:
            results["bing"] = self._submit_bing(urls)
        except Exception as e:
            log.error("Bing SubmitUrlBatch failed: %s", e)
            results["bing"] = {"error": str(e)}

        try:
            results["yandex"] = self._submit_indexnow_yandex(urls)
        except Exception as e:
            log.error("Yandex IndexNow failed: %s", e)
            results["yandex"] = {"error": str(e)}

        return results

    def _submit_google(self, urls: list[str]) -> Any:
        # Placeholder for Google Indexing API
        # Needs google.oauth2.service_account and googleapiclient.discovery
        # We will stub it since we don't have the library imported or credentials setup fully here.
        log.info("Google Indexing API called for %d URLs", len(urls))
        return {"status": "skipped", "reason": "Not fully implemented without google-api-python-client"}

    def _submit_bing(self, urls: list[str]) -> Any:
        api_key = os.getenv("BING_API_KEY", "")
        if not api_key:
            return {"status": "skipped", "reason": "No BING_API_KEY"}
            
        endpoint = f"https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlbatch?apikey={api_key}"
        site_url = "https://www.pipeleap.com"
        
        payload = {
            "siteUrl": site_url,
            "urlList": urls
        }
        
        req = urllib.request.Request(endpoint, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def _submit_indexnow_yandex(self, urls: list[str]) -> Any:
        key = os.getenv("INDEXNOW_KEY", "")
        if not key:
            return {"status": "skipped", "reason": "No INDEXNOW_KEY set"}
        host = "www.pipeleap.com"
        
        payload = {
            "host": host,
            "key": key,
            "keyLocation": f"https://{host}/{key}.txt",
            "urlList": urls
        }
        
        endpoint = "https://yandex.com/indexnow"
        req = urllib.request.Request(endpoint, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as resp:
            return {"status": resp.status, "message": "IndexNow submitted"}
