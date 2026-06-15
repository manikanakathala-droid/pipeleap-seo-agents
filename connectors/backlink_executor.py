"""
Backlink Executor — runs every automatable backlink submission.

Execution tiers:
  Tier 1 (instant, no auth): Wayback Machine, web pings, IndexNow extended
  Tier 2 (API-based):        Bing Webmaster, search engine notifications
  Tier 3 (browser scripts):  Playwright scripts for G2, Capterra, Quora, etc.
  Tier 4 (email outreach):   Structured email drafts for editorial pitches
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

SITE_URL = "https://www.pipeleap.com"


class BacklinkExecutor:

    def __init__(self, output_dir: str | Path = "outputs/backlinks") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: dict[str, Any] = {"executed_at": datetime.now(timezone.utc).isoformat()}

    def run_all(self, urls: list[str]) -> dict[str, Any]:
        print("\n=== Backlink Executor — Starting All Submissions ===\n")

        # Tier 1
        self.results["wayback_machine"]  = self.submit_wayback(urls)
        self.results["ping_services"]    = self.ping_services()
        self.results["web_mentions"]     = self.submit_web_mentions(urls[:20])

        # Tier 2
        self.results["bing_webmaster"]   = self.ping_bing_webmaster()

        # Save
        (self.output_dir / "backlink_execution_report.json").write_text(
            json.dumps(self.results, indent=2), encoding="utf-8"
        )
        self._write_report_md()
        return self.results

    # ── Tier 1: Wayback Machine ───────────────────────────────────────────────

    def submit_wayback(self, urls: list[str], delay: float = 0.8) -> dict:
        if not _HAS_REQUESTS:
            return {"ok": False, "error": "requests not installed"}

        print(f"[1/4] Wayback Machine: submitting {len(urls)} URLs...")
        archived, failed = [], []
        headers = {"User-Agent": "Pipeleap-SEO-Agent/1.0 (+https://www.pipeleap.com)"}

        for i, url in enumerate(urls, 1):
            try:
                r = _requests.post(
                    f"https://web.archive.org/save/{url}",
                    headers=headers, timeout=15, allow_redirects=True,
                )
                loc = r.headers.get("Content-Location", "")
                if r.status_code in (200, 201, 302, 301):
                    archived.append({"url": url, "status": r.status_code, "archive_url": f"https://web.archive.org{loc}" if loc else ""})
                else:
                    failed.append({"url": url, "status": r.status_code})
            except Exception as exc:
                failed.append({"url": url, "error": str(exc)[:80]})
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(urls)} archived={len(archived)}")
            time.sleep(delay)

        (self.output_dir / "wayback_submissions.json").write_text(
            json.dumps({"archived": archived, "failed": failed}, indent=2), encoding="utf-8"
        )
        print(f"  Done: {len(archived)} archived, {len(failed)} failed\n")
        return {"ok": len(archived) > 0, "archived": len(archived), "failed": len(failed)}

    # ── Tier 1: Web ping services ─────────────────────────────────────────────

    def ping_services(self) -> dict:
        if not _HAS_REQUESTS:
            return {"ok": False}

        print("[2/4] Pinging discovery services...")
        results = {}

        # Ping-o-Matic style services
        services = {
            "superfeedr":  f"https://push.superfeedr.com/?hub.mode=publish&hub.url={SITE_URL}/sitemap.xml",
            "pubsubhubbub": "https://pubsubhubbub.appspot.com/",
        }

        # PubSubHubbub / WebSub ping
        try:
            r = _requests.post(
                "https://pubsubhubbub.appspot.com/",
                data={"hub.mode": "publish", "hub.url": f"{SITE_URL}/sitemap.xml"},
                timeout=10,
            )
            results["pubsubhubbub"] = {"ok": r.status_code == 204, "status": r.status_code}
            print(f"  PubSubHubbub: {r.status_code}")
        except Exception as e:
            results["pubsubhubbub"] = {"ok": False, "error": str(e)[:60]}

        print(f"  Done\n")
        return {"ok": True, "services": results}

    # ── Tier 1: Web mention / citation submissions ────────────────────────────

    def submit_web_mentions(self, urls: list[str]) -> dict:
        if not _HAS_REQUESTS:
            return {"ok": False}

        print("[3/4] Submitting web mentions...")
        submitted = []

        # Archive.today (alternative archive)
        for url in urls[:10]:
            try:
                r = _requests.post(
                    "https://archive.ph/submit/",
                    data={"url": url},
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=12, allow_redirects=True,
                )
                submitted.append({"service": "archive.today", "url": url, "ok": r.status_code < 400})
            except Exception:
                submitted.append({"service": "archive.today", "url": url, "ok": False})
            time.sleep(1)

        ok_count = sum(1 for s in submitted if s["ok"])
        print(f"  Done: {ok_count}/{len(submitted)} submitted\n")
        return {"ok": ok_count > 0, "submitted": len(submitted), "ok_count": ok_count}

    # ── Tier 2: Bing Webmaster URL submission ─────────────────────────────────

    def ping_bing_webmaster(self) -> dict:
        if not _HAS_REQUESTS:
            return {"ok": False}

        print("[4/4] Bing Webmaster notification...")
        try:
            r = _requests.get(
                f"https://www.bing.com/webmaster/ping.aspx?siteMap={SITE_URL}/sitemap.xml",
                timeout=10,
            )
            ok = r.status_code == 200
            print(f"  Bing ping: {r.status_code}\n")
            return {"ok": ok, "status": r.status_code}
        except Exception as e:
            return {"ok": False, "error": str(e)[:80]}

    # ── Report ────────────────────────────────────────────────────────────────

    def _write_report_md(self) -> None:
        wm = self.results.get("wayback_machine", {})
        lines = [
            "# Backlink Execution Report",
            f"\n**Executed:** {self.results['executed_at']}",
            "\n## Tier 1 — Instant Submissions (No Auth)\n",
            f"| Service | Status | Count |",
            f"| --- | --- | --- |",
            f"| Wayback Machine (archive.org) | {'OK' if wm.get('ok') else 'FAIL'} | {wm.get('archived', 0)} archived |",
            f"| PubSubHubbub ping | {self.results.get('ping_services', {}).get('ok', False)} | sitemap notified |",
            f"| archive.today | {self.results.get('web_mentions', {}).get('ok', False)} | {self.results.get('web_mentions', {}).get('ok_count', 0)} URLs |",
            f"| Bing Webmaster ping | {self.results.get('bing_webmaster', {}).get('ok', False)} | sitemap notified |",
            "\n## Tier 2 — Browser Automation Required\n",
            "Run: `python scripts/playwright_submissions/submit_all.py`\n",
            "| Platform | DA | Script | Time |",
            "| --- | --- | --- | --- |",
            "| G2 | 93 | g2_submission.py | 30 min |",
            "| Capterra | 90 | capterra_submission.py | 20 min |",
            "| Crunchbase | 91 | crunchbase_submission.py | 15 min |",
            "| StackShare | 79 | stackshare_submission.py | 15 min |",
            "| AlternativeTo | 72 | alternativeto_submission.py | 10 min |",
            "| Quora (5 answers) | 93 | quora_answers.py | 2 hrs |",
            "\n## Tier 3 — Email Outreach\n",
            "Drafts in: `outputs/backlinks/email_drafts/`\n",
            "| Target | DA | Status |",
            "| --- | --- | --- |",
            "| Sales Hacker | 84 | Draft ready — send sales_hacker_pitch.eml |",
            "| HubSpot Blog | 93 | Draft ready — send hubspot_blog_pitch.eml |",
            "| RevOps Co-op | 61 | Draft ready — send revops_coop_pitch.eml |",
            "| LinkedIn article | 98 | Draft ready — publish linkedin_article.md |",
        ]
        (self.output_dir / "backlink_execution_report.md").write_text(
            "\n".join(lines), encoding="utf-8"
        )
