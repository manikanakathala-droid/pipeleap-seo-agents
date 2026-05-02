"""
PageSpeed Insights / Core Web Vitals connector.
Set PAGESPEED_API_KEY in config or env.
"""
from __future__ import annotations
import os
from typing import Any

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

CWV_THRESHOLDS = {
    "lcp": {"good": 2.5, "needs_improvement": 4.0},   # seconds
    "cls": {"good": 0.1, "needs_improvement": 0.25},   # score
    "inp": {"good": 200, "needs_improvement": 500},    # ms
    "fcp": {"good": 1.8, "needs_improvement": 3.0},    # seconds
    "ttfb": {"good": 0.8, "needs_improvement": 1.8},   # seconds
}


class PageSpeedConnector:
    API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.environ.get("PAGESPEED_API_KEY", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key) and _HAS_REQUESTS

    def audit(self, url: str, strategy: str = "mobile") -> dict[str, Any]:
        if not self.is_configured:
            return {"url": url, "status": "not_configured", "issues": ["Set PAGESPEED_API_KEY to enable Core Web Vitals monitoring."]}
        try:
            params = {"url": url, "strategy": strategy, "key": self.api_key, "category": ["performance", "seo", "accessibility"]}
            resp = _requests.get(self.API_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_result(url, data)
        except Exception as exc:
            return {"url": url, "status": "error", "error": str(exc)}

    def _parse_result(self, url: str, data: dict) -> dict[str, Any]:
        cats = data.get("lighthouseResult", {}).get("categories", {})
        perf_score = round((cats.get("performance", {}).get("score", 0) or 0) * 100)
        seo_score = round((cats.get("seo", {}).get("score", 0) or 0) * 100)
        audits = data.get("lighthouseResult", {}).get("audits", {})
        metrics = self._extract_cwv(audits)
        issues = self._flag_issues(metrics, perf_score, seo_score)
        return {
            "url": url,
            "status": "ok",
            "performance_score": perf_score,
            "seo_score": seo_score,
            "metrics": metrics,
            "issues": issues,
        }

    @staticmethod
    def _extract_cwv(audits: dict) -> dict[str, float | None]:
        def numeric(key: str) -> float | None:
            item = audits.get(key, {})
            v = item.get("numericValue")
            return round(v / 1000, 2) if v and "milliseconds" in item.get("numericUnit", "") else (round(v, 3) if v else None)
        return {
            "lcp": numeric("largest-contentful-paint"),
            "cls": round(audits.get("cumulative-layout-shift", {}).get("numericValue", 0) or 0, 3),
            "inp": numeric("interaction-to-next-paint"),
            "fcp": numeric("first-contentful-paint"),
            "ttfb": numeric("server-response-time"),
        }

    @staticmethod
    def _flag_issues(metrics: dict, perf: int, seo: int) -> list[str]:
        issues = []
        if perf < 50:
            issues.append(f"CRITICAL: Performance score {perf}/100 — immediate action required")
        elif perf < 75:
            issues.append(f"WARNING: Performance score {perf}/100 — needs improvement")
        if seo < 80:
            issues.append(f"WARNING: SEO score {seo}/100 — check meta, headings, and crawlability")
        lcp = metrics.get("lcp")
        if lcp and lcp > CWV_THRESHOLDS["lcp"]["needs_improvement"]:
            issues.append(f"CRITICAL: LCP {lcp}s — exceeds 4s threshold, ranking impact likely")
        elif lcp and lcp > CWV_THRESHOLDS["lcp"]["good"]:
            issues.append(f"WARNING: LCP {lcp}s — above 2.5s good threshold")
        cls = metrics.get("cls")
        if cls and cls > CWV_THRESHOLDS["cls"]["needs_improvement"]:
            issues.append(f"CRITICAL: CLS {cls} — severe layout instability")
        elif cls and cls > CWV_THRESHOLDS["cls"]["good"]:
            issues.append(f"WARNING: CLS {cls} — above 0.1 good threshold")
        return issues
