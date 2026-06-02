"""
WarRoom — alert hub that deduplicates by (issue_type, page_url, date).

Tiers:
  Critical (Slack + email)  — indexing failures, broken pages, noindex on live
  Warning  (email only)     — slow pages, missing metadata, orphan pages
  Info     (dashboard only) — low-priority suggestions
"""
from __future__ import annotations

import json
import logging
import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

SEVERITY_TIER = {
    "critical": "critical",
    "high": "critical",
    "medium": "warning",
    "low": "info",
}


class WarRoom:
    def __init__(self, config: dict, logger: Any = None):
        self.config = config
        self.logger = logger or log
        self.dashboard_dir = Path(__file__).resolve().parent.parent / "dashboard"

    def ingest_audit_issues(self, issues: list[Any], source: str = "audit") -> list[dict]:
        """Convert AuditIssue objects to alert dicts, dedup against dashboard/alerts.json."""
        existing = self._load_alerts()
        existing_map = {
            (a["issue_type"], a.get("page_url", ""), a.get("date", ""))
            for a in existing.get("active_alerts", [])
        }

        new_alerts: list[dict] = []
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        for issue in issues:
            if isinstance(issue, dict):
                sev = issue.get("severity", "low") or "low"
                url = issue.get("page_url", "") or issue.get("url", "") or ""
                title = str(issue.get("title", ""))
                desc = str(issue.get("description", ""))[:200]
            else:
                sev = getattr(issue, "severity", "low") or "low"
                url = getattr(issue, "url", "") or ""
                title = str(getattr(issue, "title", ""))
                desc = str(getattr(issue, "description", ""))[:200]
            tier = SEVERITY_TIER.get(sev.lower(), "info")
            key = (tier, url, today)
            if key in existing_map:
                continue
            alert = {
                "issue_type": tier,
                "page_url": url,
                "date": today,
                "title": title,
                "description": desc,
                "source": source,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            new_alerts.append(alert)

        if not new_alerts:
            return []

        existing["active_alerts"].extend(new_alerts)
        existing["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._write_alerts(existing)
        self.logger.info("WarRoom: %d new alerts ingested", len(new_alerts))
        return new_alerts

    def ingest_indexing_failures(self, verification_report: dict[str, Any]) -> list[dict]:
        """Convert indexing verification failures into alerts."""
        alerts: list[dict] = []
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        for channel, result in verification_report.get("channels", {}).items():
            if isinstance(result, dict) and not result.get("ok", True):
                alerts.append({
                    "issue_type": "critical",
                    "page_url": "",
                    "date": today,
                    "title": f"Indexing signal failed: {channel}",
                    "description": f"All retries exhausted for {channel}. Last error: {result.get('error', 'unknown')}",
                    "source": "indexing_verifier",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })

        if alerts:
            existing = self._load_alerts()
            existing["active_alerts"].extend(alerts)
            existing["last_updated"] = datetime.now(timezone.utc).isoformat()
            self._write_alerts(existing)

        return alerts

    def archive_stale(self, max_age_days: int = 3) -> int:
        """Move alerts older than max_age_days to archive."""
        existing = self._load_alerts()
        fresh: list[dict] = []
        archived: list[dict] = []
        cutoff = datetime.now(timezone.utc).timestamp() - max_age_days * 86400

        for alert in existing.get("active_alerts", []):
            created = alert.get("created_at", "")
            try:
                ts = datetime.fromisoformat(created).timestamp()
            except (ValueError, TypeError):
                ts = 0
            if ts < cutoff:
                archived.append(alert)
            else:
                fresh.append(alert)

        if archived:
            existing["active_alerts"] = fresh
            existing.setdefault("alert_history", []).extend(archived)
            existing["last_updated"] = datetime.now(timezone.utc).isoformat()
            self._write_alerts(existing)

        return len(archived)

    def notify_critical(self, alerts: list[dict]) -> None:
        """Send email for Critical alerts."""
        critical = [a for a in alerts if a.get("issue_type") == "critical"]
        if not critical:
            return

        body_lines = ["The following critical issues were detected:\n"]
        for a in critical:
            page = a.get("page_url", "") or "(no page)"
            title = a.get("title", "")
            desc = a.get("description", "")
            body_lines.append(f"  - {title}")
            body_lines.append(f"    Page: {page}")
            body_lines.append(f"    Detail: {desc}")
            body_lines.append("")

        subject = f"Critical SEO Alert — {len(critical)} issue(s)"
        self._send_email(subject, "\n".join(body_lines))

    def notify_warnings(self, alerts: list[dict]) -> None:
        """Send email digest for Warning alerts (max 10 per run)."""
        warnings = [a for a in alerts if a.get("issue_type") == "warning"][:10]
        if not warnings:
            return

        body_lines = ["SEO warning summary:\n"]
        for a in warnings:
            page = a.get("page_url", "") or "(no page)"
            body_lines.append(f"  - {a.get('title', '')} @ {page}")

        subject = f"SEO Warning Digest — {len(warnings)} issue(s)"
        self._send_email(subject, "\n".join(body_lines))

    # ── Helpers ───────────────────────────────────────────────────────────

    def _load_alerts(self) -> dict:
        path = self.dashboard_dir / "alerts.json"
        if not path.exists():
            return {"last_updated": "", "active_alerts": [], "alert_history": []}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            return {"last_updated": "", "active_alerts": [], "alert_history": []}

    def _write_alerts(self, data: dict) -> None:
        self.dashboard_dir.mkdir(parents=True, exist_ok=True)
        path = self.dashboard_dir / "alerts.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _send_email(self, subject: str, body: str) -> None:
        mail_to = os.getenv("MAIL_TO", "")
        if not mail_to:
            self.logger.info("WarRoom email skipped: MAIL_TO not set")
            return
        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg["Subject"] = subject
            msg["From"] = os.getenv("MAIL_USERNAME", "manik.anakathala@gmail.com")
            msg["To"] = mail_to

            server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
            port = int(os.getenv("MAIL_PORT", "587"))
            user = os.getenv("MAIL_USERNAME", "manik.anakathala@gmail.com")
            pwd = os.getenv("MAIL_PASSWORD", "")

            with smtplib.SMTP(server, port, timeout=15) as smtp:
                smtp.starttls()
                smtp.login(user, pwd)
                smtp.send_message(msg)
            self.logger.info("WarRoom email sent: %s", subject)
        except Exception as exc:
            self.logger.warning("WarRoom email failed: %s", exc)

    def summary(self) -> dict[str, Any]:
        data = self._load_alerts()
        return {
            "active_count": len(data.get("active_alerts", [])),
            "critical_count": sum(1 for a in data.get("active_alerts", []) if a.get("issue_type") == "critical"),
            "warning_count": sum(1 for a in data.get("active_alerts", []) if a.get("issue_type") == "warning"),
            "info_count": sum(1 for a in data.get("active_alerts", []) if a.get("issue_type") == "info"),
            "last_updated": data.get("last_updated", ""),
        }
