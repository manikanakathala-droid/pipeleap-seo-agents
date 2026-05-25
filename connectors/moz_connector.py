from __future__ import annotations

import base64
import os
from typing import Any

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

MOZ_BASE = "https://lsapi.seomoz.com/v2"


class MozConnector:
    """
    Moz Links API V2 connector for Domain Authority, Page Authority, and Spam Score.

    Uses Basic Auth with Access ID (username) and Secret Key (password).
    Free tier: 50 rows/month — enough for Pipeleap's competitor set.
    Falls back gracefully when not configured or quota exhausted.
    """

    def __init__(
        self,
        access_id: str = "",
        secret_key: str = "",
    ) -> None:
        self.access_id = access_id or os.environ.get("MOZ_API_ACCESS_ID", "")
        self.secret_key = secret_key or os.environ.get("MOZ_API_SECRET_KEY", "")
        self._auth_header = self._build_auth()
        self.is_configured = bool(self.access_id and self.secret_key and _HAS_REQUESTS)
        self._row_estimate: int = 0

    def _build_auth(self) -> str:
        if not self.access_id or not self.secret_key:
            return ""
        raw = f"{self.access_id}:{self.secret_key}"
        return f"Basic {base64.b64encode(raw.encode()).decode()}"

    def get_url_metrics(
        self,
        targets: list[str],
    ) -> dict[str, dict[str, Any]]:
        """
        Fetch Moz metrics for a list of domains or URLs.

        Returns dict of {target: {domain_authority, page_authority, spam_score,
                                  linking_root_domains, linking_pages}}
        """
        if not self.is_configured or not targets:
            return {}

        try:
            resp = _requests.post(
                f"{MOZ_BASE}/url_metrics",
                headers={
                    "Authorization": self._auth_header,
                    "Content-Type": "application/json",
                },
                json={"targets": targets[:50]},
                timeout=15,
            )
            if resp.status_code != 200:
                return {}

            data = resp.json()
            results: dict[str, dict[str, Any]] = {}
            raw_results = data.get("results", [])
            for i, item in enumerate(raw_results):
                domain = targets[i] if i < len(targets) else item.get("root_domain", "")
                if not domain:
                    continue
                results[domain] = {
                    "domain_authority":          round(float(item.get("domain_authority", 0)), 1),
                    "page_authority":            round(float(item.get("page_authority", 0)), 1),
                    "spam_score":                int(item.get("spam_score", 0)),
                    "linking_root_domains":      int(item.get("root_domains_to_page", 0)),
                    "linking_pages":             int(item.get("external_pages_to_page", 0)),
                    "source":                    "moz",
                }
            self._row_estimate += len(results)
            return results
        except Exception:
            return {}

    def enrich_backlink_targets(
        self,
        targets: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Take a list of backlink target dicts (with 'domain' key) and overwrite
        their 'authority' field with live Moz Domain Authority.
        """
        if not self.is_configured or not targets:
            return targets

        domains = [t["domain"] for t in targets]
        moz_data = self.get_url_metrics(domains)

        enriched = []
        for t in targets:
            d = t["domain"]
            if d in moz_data:
                t["authority"] = moz_data[d]["domain_authority"]
                t["moz_spam_score"] = moz_data[d]["spam_score"]
                t["moz_linking_root_domains"] = moz_data[d]["linking_root_domains"]
                t["moz_linking_pages"] = moz_data[d]["linking_pages"]
            enriched.append(t)

        enriched.sort(key=lambda x: x.get("authority", 0), reverse=True)
        return enriched
