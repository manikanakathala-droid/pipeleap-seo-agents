"""
Backlink gap analysis connector.
Uses Ahrefs or Majestic API to find domains that link to competitors but not Pipeleap.
Set AHREFS_API_KEY in config or env vars.
When Moz API credentials are provided, enriches fallback targets with live Domain Authority.
Falls back to a curated priority target list when API is not configured.
"""
from __future__ import annotations
import os
from typing import Any

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

try:
    from connectors.moz_connector import MozConnector
    _HAS_MOZ = True
except ImportError:
    _HAS_MOZ = False

# High-authority outreach targets known to link to SaaS outbound automation tools
# Curated fallback for teams without Ahrefs API
PRIORITY_GAP_TARGETS: list[dict[str, Any]] = [
    {"domain": "blog.hubspot.com", "authority": 93, "category": "guest_post", "angle": "SaaS outbound automation guide"},
    {"domain": "saleshacker.com", "authority": 84, "category": "guest_post", "angle": "Workflow orchestration for revenue teams"},
    {"domain": "revopscoop.com", "authority": 61, "category": "community", "angle": "RevOps automation systems"},
    {"domain": "predictablerevenue.com", "authority": 72, "category": "guest_post", "angle": "Predictable pipeline through workflow orchestration"},
    {"domain": "g2.com", "authority": 90, "category": "directory", "angle": "Outbound automation software listing"},
    {"domain": "capterra.com", "authority": 88, "category": "directory", "angle": "Workflow orchestration software listing"},
    {"domain": "producthunt.com", "authority": 91, "category": "community", "angle": "Product launch and review"},
    {"domain": "reddit.com/r/sales", "authority": 91, "category": "community", "angle": "Outbound automation discussion"},
    {"domain": "medium.com", "authority": 95, "category": "publication", "angle": "SaaS pipeline automation deep-dive"},
    {"domain": "substack.com", "authority": 91, "category": "publication", "angle": "Revenue automation newsletter"},
    {"domain": "saastr.com", "authority": 78, "category": "media", "angle": "Outbound automation for SaaS founders"},
    {"domain": "getlatka.com", "authority": 68, "category": "directory", "angle": "SaaS revenue automation tool listing"},
]


class BacklinkGapConnector:

    def __init__(
        self,
        api_key: str = "",
        target_domain: str = "pipeleap.com",
        moz_access_id: str = "",
        moz_secret_key: str = "",
    ) -> None:
        self.api_key = api_key or os.environ.get("AHREFS_API_KEY", "")
        self.target_domain = target_domain
        self._moz: MozConnector | None = None
        if moz_access_id and moz_secret_key and _HAS_MOZ:
            self._moz = MozConnector(access_id=moz_access_id, secret_key=moz_secret_key)

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key) and _HAS_REQUESTS

    def gap_analysis(self, competitor_domains: list[str]) -> list[dict[str, Any]]:
        """Return domains that link to competitors but not to target_domain."""
        if not self.is_configured:
            return self._enriched_fallback()
        try:
            return self._ahrefs_gap(competitor_domains)
        except Exception:
            return self._enriched_fallback()

    def _enriched_fallback(self) -> list[dict[str, Any]]:
        """Return curated fallback targets, enriched with live Moz DA when available."""
        targets = self._curated_fallback()
        if self._moz is not None:
            try:
                return self._moz.enrich_backlink_targets(targets)
            except Exception:
                pass
        return targets

    def _ahrefs_gap(self, competitors: list[str]) -> list[dict[str, Any]]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        results = []
        for comp in competitors[:5]:
            params = {"target": comp, "mode": "domain", "limit": 50, "select": "domain_rating,referring_domain"}
            resp = _requests.get("https://api.ahrefs.com/v3/site-explorer/referring-domains", headers=headers, params=params, timeout=15)
            if resp.status_code == 200:
                for item in resp.json().get("refdomains", []):
                    domain = item.get("referring_domain", "")
                    dr = item.get("domain_rating", 0)
                    if dr >= 40 and domain:
                        results.append({
                            "domain": domain,
                            "authority": dr,
                            "links_to_competitor": comp,
                            "category": "organic",
                            "angle": f"Links to {comp} — pitch Pipeleap as the orchestration layer",
                        })
        seen = set()
        deduped = []
        for item in sorted(results, key=lambda x: x["authority"], reverse=True):
            if item["domain"] not in seen:
                seen.add(item["domain"])
                deduped.append(item)
        return deduped[:30]

    @staticmethod
    def _curated_fallback() -> list[dict[str, Any]]:
        return PRIORITY_GAP_TARGETS

    def outreach_brief(self, gap_target: dict[str, Any]) -> dict[str, str]:
        domain = gap_target["domain"]
        angle = gap_target["angle"]
        return {
            "target_domain": domain,
            "authority": gap_target.get("authority", "N/A"),
            "email_subject": f"Contribution idea for {domain}: {angle}",
            "email_body": (
                f"Hi,\n\n"
                f"I'm reaching out from Pipeleap — a workflow orchestration system for SaaS revenue teams. "
                f"We help SaaS organizations build predictable outbound pipeline through automated workflows.\n\n"
                f"I noticed you cover {angle.lower()} and thought your readers would find value in a piece on "
                f"how workflow orchestration is replacing fragmented outbound tool stacks.\n\n"
                f"I'd love to contribute an article titled: '{angle} — How Workflow Orchestration Changes Everything'\n\n"
                f"Would this be a good fit?\n\nBest,\nPipeleap Team"
            ),
        }
