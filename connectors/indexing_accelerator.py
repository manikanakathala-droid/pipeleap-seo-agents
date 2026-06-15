"""
Indexing Accelerator — coordinates all indexing and discovery signals in one run.

Execution order (fastest to slowest indexing):
  1. IndexNow  → Bing/Yandex/DuckDuckGo (minutes–hours, no auth needed)
  2. GSC sitemap submission → Google crawl queue (hours–days)
  3. Google Indexing API → direct URL notification (minutes if API enabled)
  4. Search engine pings → all major engines via standard ping protocol
  5. Backlink action report → actionable list of authority sites to submit to

Run this after every content publish for maximum indexing speed.
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


class IndexingAccelerator:
    """Coordinates all indexing acceleration signals in one call."""

    # Sitemap ping endpoints — all deprecated (Google 2023, Bing 2024).
    # IndexNow + GSC sitemap API cover all major engines.

    def __init__(
        self,
        site_url: str,
        sitemap_url: str,
        gsc_connector: Any | None = None,
        indexnow_connector: Any | None = None,
    ) -> None:
        self.site_url         = site_url.rstrip("/")
        self.sitemap_url      = sitemap_url
        self.gsc              = gsc_connector
        self.indexnow         = indexnow_connector

    def run_all(
        self,
        new_urls: list[str] | None = None,
        sitemap_path: str | Path | None = None,
        output_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Run all indexing acceleration signals.

        Args:
            new_urls:     Specific new/updated URLs to submit (optional — uses sitemap if None)
            sitemap_path: Local sitemap file path for IndexNow batch submission
            output_dir:   Where to write the acceleration report

        Returns: Full report dict with status of each signal.
        """
        report: dict[str, Any] = {
            "run_at":   datetime.now(timezone.utc).isoformat(),
            "site_url": self.site_url,
            "signals":  {},
        }

        # ── 1. IndexNow (fastest — covers Bing/Yandex/DuckDuckGo) ───────────
        if self.indexnow and sitemap_path and Path(sitemap_path).exists():
            result = self.indexnow.submit_sitemap_urls(sitemap_path)
            report["signals"]["indexnow"] = result
            urls_count = result.get("urls_submitted", 0)
            endpoints  = result.get("endpoints_ok", 0)
        elif self.indexnow and new_urls:
            result = self.indexnow.submit_all_endpoints(new_urls[:500])
            report["signals"]["indexnow"] = result
        else:
            report["signals"]["indexnow"] = {"ok": False, "error": "IndexNow not configured or no URLs"}

        # ── 2. GSC Sitemap Submission ─────────────────────────────────────────
        if self.gsc:
            result = self.gsc.submit_sitemap(self.sitemap_url)
            report["signals"]["gsc_sitemap"] = result
        else:
            report["signals"]["gsc_sitemap"] = {"ok": False, "error": "GSC not configured"}

        # ── 3. Google Indexing API (if enabled in GCP) ────────────────────────
        if self.gsc and new_urls:
            batch = new_urls[:200]  # daily quota cap
            results = self.gsc.request_indexing(batch)
            ok  = sum(1 for r in results if r.get("ok"))
            err = sum(1 for r in results if not r.get("ok"))
            # Check if API is disabled (not a credential error — a GCP setup issue)
            api_disabled = any("SERVICE_DISABLED" in str(r.get("error", "")) for r in results)
            report["signals"]["google_indexing_api"] = {
                "ok": ok > 0 and not api_disabled,
                "submitted": len(batch),
                "accepted": ok,
                "errors": err,
                "api_disabled": api_disabled,
                "fix_url": "https://console.developers.google.com/apis/api/indexing.googleapis.com/overview?project=873204905433" if api_disabled else None,
            }
        else:
            report["signals"]["google_indexing_api"] = {"ok": False, "error": "no URLs or GSC not configured"}

        # ── 5. Backlink action report ─────────────────────────────────────────
        report["backlink_actions"] = self._backlink_action_report()

        # ── Summary ───────────────────────────────────────────────────────────
        signals_ok = sum(
            1 for sig in report["signals"].values()
            if isinstance(sig, dict) and sig.get("ok")
        )
        report["summary"] = {
            "signals_fired":     len(report["signals"]),
            "signals_ok":        signals_ok,
            "indexing_velocity": self._estimate_velocity(report["signals"]),
        }

        # ── Write report ──────────────────────────────────────────────────────
        if output_dir:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / "indexing_acceleration_report.json").write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )
            (out / "indexing_acceleration_report.md").write_text(
                self._report_md(report), encoding="utf-8"
            )

        return report

    # ── Backlink action report ────────────────────────────────────────────────

    def _backlink_action_report(self) -> list[dict]:
        """
        Returns prioritised list of backlink actions that will reduce indexing
        time — high-DA backlinks signal to Google that the site is authoritative
        and accelerate crawl frequency.
        """
        return [
            {
                "action": "Submit G2 listing",
                "url": "https://sell.g2.com/",
                "da_estimate": 93,
                "indexing_impact": "HIGH — G2 is crawled daily, backlinks from G2 signal enterprise SaaS legitimacy",
                "time_to_complete": "30 minutes",
                "content_ready": "outputs/geo-agent/*/listings/g2_listing.md",
            },
            {
                "action": "Submit Capterra listing",
                "url": "https://www.capterra.com/vendors/sign-up",
                "da_estimate": 90,
                "indexing_impact": "HIGH — Capterra backlink accelerates Google trust signals",
                "time_to_complete": "20 minutes",
                "content_ready": "outputs/geo-agent/*/listings/capterra_listing.md",
            },
            {
                "action": "Submit Product Hunt listing",
                "url": "https://www.producthunt.com/",
                "da_estimate": 91,
                "indexing_impact": "HIGH — Product Hunt backlink + social signals boost crawl rate",
                "time_to_complete": "45 minutes",
                "content_ready": "Complete existing listing with screenshots and tags",
            },
            {
                "action": "Post on Quora (5 answers)",
                "url": "https://www.quora.com/",
                "da_estimate": 93,
                "indexing_impact": "MEDIUM — Quora answer with site link drives referral traffic and indexing signal",
                "time_to_complete": "2 hours",
                "content_ready": "outputs/geo-agent/*/quora/quora_*.txt",
            },
            {
                "action": "Submit Crunchbase company profile",
                "url": "https://www.crunchbase.com/add/company",
                "da_estimate": 91,
                "indexing_impact": "MEDIUM — Crunchbase is a trusted entity source Google uses for Knowledge Graph",
                "time_to_complete": "15 minutes",
                "content_ready": "outputs/geo-agent/*/listings/crunchbase_listing.md",
            },
            {
                "action": "Submit to StackShare",
                "url": "https://stackshare.io/submit",
                "da_estimate": 79,
                "indexing_impact": "MEDIUM — Tech stack citation from StackShare",
                "time_to_complete": "15 minutes",
                "content_ready": "outputs/geo-agent/*/listings/stackshare_listing.md",
            },
            {
                "action": "Submit to AlternativeTo",
                "url": "https://alternativeto.net/submit/",
                "da_estimate": 72,
                "indexing_impact": "MEDIUM — Competitive category listing drives comparison traffic",
                "time_to_complete": "10 minutes",
                "content_ready": "outputs/geo-agent/*/listings/alternativeto_listing.md",
            },
            {
                "action": "Guest post pitch: Sales Hacker",
                "url": "https://www.saleshacker.com/",
                "da_estimate": 84,
                "indexing_impact": "HIGH — Editorial backlink from DA84 drives significant crawl boost",
                "time_to_complete": "Email pitch + 2-3 weeks for acceptance",
                "content_ready": "outputs/geo-agent/*/outreach/sales_hacker_outreach.md",
            },
            {
                "action": "LinkedIn article publication",
                "url": "https://www.linkedin.com/",
                "da_estimate": 98,
                "indexing_impact": "HIGH — LinkedIn DA98 backlinks are extremely powerful for entity recognition",
                "time_to_complete": "1 hour to write, publish immediately",
                "content_ready": "Write 800-word article on outbound automation, link to pipeleap.com/blog",
            },
        ]

    # ── Reporting ─────────────────────────────────────────────────────────────

    def _estimate_velocity(self, signals: dict) -> str:
        ok = sum(1 for s in signals.values() if isinstance(s, dict) and s.get("ok"))
        if ok >= 3:   return "FAST — multiple signals active, expect indexing within 24-72 hours"
        if ok >= 1:   return "MODERATE — 1-2 signals active, expect indexing within 3-7 days"
        return "SLOW — no active signals, indexing depends on organic crawl discovery"

    def _report_md(self, report: dict) -> str:
        sig = report.get("signals", {})
        summary = report.get("summary", {})
        lines = [
            "# Indexing Acceleration Report",
            "",
            f"**Run:** {report['run_at']}",
            f"**Signals fired:** {summary.get('signals_fired', 0)}",
            f"**Signals OK:** {summary.get('signals_ok', 0)}",
            f"**Velocity estimate:** {summary.get('indexing_velocity', 'unknown')}",
            "",
            "## Signal Status",
            "",
            "| Signal | Status | Detail |",
            "| --- | --- | --- |",
        ]
        for name, result in sig.items():
            if not isinstance(result, dict):
                continue
            ok     = result.get("ok", False)
            status = "OK" if ok else "FAILED"
            detail = ""
            if name == "indexnow":
                detail = f"{result.get('urls_submitted', 0)} URLs to {result.get('endpoints_ok', 0)} engines"
            elif name == "gsc_sitemap":
                detail = result.get("sitemap_url", result.get("error", ""))[:60]
            elif name == "google_indexing_api":
                if result.get("api_disabled"):
                    detail = f"API disabled — enable at GCP Console (project 873204905433)"
                    status = "ACTION REQUIRED"
                else:
                    detail = f"{result.get('accepted', 0)}/{result.get('submitted', 0)} URLs accepted"
            elif name == "sitemap_pings":
                engines_ok = sum(1 for v in result.values() if isinstance(v, dict) and v.get("ok"))
                detail = f"{engines_ok}/{len(result)} engines responded OK"
                ok = engines_ok > 0
                status = "OK" if ok else "FAILED"
            lines.append(f"| {name} | {status} | {detail} |")

        lines += [
            "",
            "## Backlink Actions (prioritised by DA)",
            "",
            "| Action | DA | Impact | Time | Content |",
            "| --- | --- | --- | --- | --- |",
        ]
        for action in report.get("backlink_actions", []):
            lines.append(
                f"| {action['action']} | {action['da_estimate']} | "
                f"{action['indexing_impact'].split(' — ')[0]} | "
                f"{action['time_to_complete']} | {'Ready' if 'outputs' in action.get('content_ready','') else 'Manual'} |"
            )

        lines += [
            "",
            "## Required Manual Action",
            "",
            "**Google Indexing API is disabled** — enable it at:",
            "https://console.developers.google.com/apis/api/indexing.googleapis.com/overview?project=873204905433",
            "",
            "Once enabled, the daily agent will automatically submit all new pages.",
        ]
        return "\n".join(lines)
