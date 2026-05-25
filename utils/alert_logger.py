import json
import logging
import datetime
import urllib.request
from pathlib import Path
from typing import Any

class AlertLogger:
    def __init__(self, config: dict[str, Any]):
        self.config = config.get("alerts", {})
        self.webhook_url = self.config.get("webhook_url", "")
        
        # Setup local structured JSONL logger
        self.log_dir = Path("outputs/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"{today}.jsonl"

    def _log_structured(self, level: str, message: str, context: dict[str, Any]) -> None:
        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "context": context
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _send_webhook(self, message: str) -> None:
        if not self.webhook_url:
            return
        payload = {"text": f"🚨 **SEO Pipeline Alert** 🚨\n{message}"}
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req) as resp:
                pass
        except Exception as e:
            logging.error("Failed to send alert webhook: %s", e)

    def alert_circuit_breaker(self, message: str) -> None:
        self._log_structured("CRITICAL", message, {"alert_type": "circuit_breaker"})
        if self.config.get("alert_on_circuit_break", True):
            self._send_webhook(message)

    def alert_github_conflict(self, message: str) -> None:
        self._log_structured("WARNING", message, {"alert_type": "github_conflict"})
        if self.config.get("alert_on_github_conflict", True):
            self._send_webhook(message)

    def alert_quota_exhaustion(self, message: str) -> None:
        self._log_structured("ERROR", message, {"alert_type": "quota_exhaustion"})
        if self.config.get("alert_on_quota_exhaustion", True):
            self._send_webhook(message)
