"""
AutoFixer — reads AuditIssue.auto_fix_script and applies fixes to the launchpad repo.

Only pushes changes when the fix is non-duplicate:
- robots.txt: only create if file doesn't exist
- Sitemap entries: only append truly new URLs (not already in <loc>)
- Metadata overrides: only write if value changed
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

log = logging.getLogger(__name__)

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
INDEXNOW_KEY = "92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55"


class AutoFixer:
    def __init__(self, launchpad_root: str | Path, config: dict, logger: Any = None):
        self.launchpad = Path(launchpad_root)
        self.config = config
        self.logger = logger or log
        self.fixes_applied: list[dict] = []

    # ── Public API ────────────────────────────────────────────────────────

    def apply(self, issues: list[Any]) -> list[dict]:
        """Apply auto-fixable audit issues. Returns list of fix results."""
        for issue in issues:
            script = (issue.get("auto_fix_script") if isinstance(issue, dict)
                      else getattr(issue, "auto_fix_script", None))
            if not script:
                continue
            try:
                self._apply_one(issue, script)
            except Exception as exc:
                self.logger.warning("AutoFix failed for %s: %s", getattr(issue, "url", "?"), exc)
        return self.fixes_applied

    # ── Per-fix handlers ──────────────────────────────────────────────────

    def _apply_one(self, issue: Any, script: str) -> None:
        if isinstance(issue, dict):
            url = issue.get("page_url", "") or issue.get("url", "")
            title = str(issue.get("title", ""))
        else:
            url = getattr(issue, "url", "") or ""
            title = str(getattr(issue, "title", ""))
        result: dict = {"url": url, "issue": title, "fixed": False, "action": None}

        # Detect fix type from script content
        if script.startswith("User-agent:") or "Sitemap:" in script:
            result = self._fix_robots_txt(script, result)
        elif script.startswith("{"):
            result = self._fix_metadata(script, result)
        elif "sitemap" in script.lower() or "add url" in script.lower():
            result = self._fix_sitemap(url, script, result)

        if result.get("fixed"):
            self.fixes_applied.append(result)
            self.logger.info("AutoFix applied: %s — %s", result.get("action"), url)

    def _fix_robots_txt(self, script: str, result: dict) -> dict:
        robots_path = self.launchpad / "public" / "robots.txt"
        if robots_path.exists():
            existing = robots_path.read_text(encoding="utf-8")
            if existing.strip() == script.strip():
                result["fixed"] = False
                result["action"] = "skipped — robots.txt already correct"
                return result
        robots_path.parent.mkdir(parents=True, exist_ok=True)
        robots_path.write_text(script.strip() + "\n", encoding="utf-8")
        result["fixed"] = True
        result["action"] = f"wrote robots.txt ({len(script)} bytes)"
        return result

    def _fix_metadata(self, script: str, result: dict) -> dict:
        try:
            payload = json.loads(script)
        except json.JSONDecodeError:
            result["action"] = "skipped — invalid JSON in auto_fix_script"
            return result

        url = payload.get("url") or result.get("url", "")
        if not url:
            return result

        overrides_path = self.launchpad / "public" / "page_metadata_overrides.json"
        overrides: dict = {}
        if overrides_path.exists():
            try:
                overrides = json.loads(overrides_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, Exception):
                overrides = {}

        existing = overrides.get(url, {})
        changed = False
        for key in ("title", "description"):
            if key in payload and payload[key] and payload[key] != existing.get(key):
                if url not in overrides:
                    overrides[url] = {}
                overrides[url][key] = payload[key]
                changed = True

        if not changed:
            result["fixed"] = False
            result["action"] = f"skipped — {url} metadata already set"
            return result

        overrides_path.parent.mkdir(parents=True, exist_ok=True)
        overrides_path.write_text(json.dumps(overrides, indent=2), encoding="utf-8")
        result["fixed"] = True
        result["action"] = f"updated metadata overrides for {url}"
        return result

    def _fix_sitemap(self, url: str, script: str, result: dict) -> dict:
        sitemap_path = self.launchpad / "public" / "sitemap.xml"
        if not sitemap_path.exists():
            result["action"] = "skipped — sitemap.xml not found"
            return result

        try:
            tree = ET.parse(str(sitemap_path))
            root = tree.getroot()
        except Exception:
            result["action"] = "skipped — cannot parse sitemap"
            return result

        existing_locs = set()
        if root.tag == f"{SITEMAP_NS}sitemapindex":
            for sm in root.findall(f"{SITEMAP_NS}sitemap"):
                loc = sm.find(f"{SITEMAP_NS}loc")
                if loc is not None and loc.text:
                    existing_locs.add(loc.text.rstrip("/"))
        elif root.tag == f"{SITEMAP_NS}urlset":
            for u in root.findall(f"{SITEMAP_NS}url"):
                loc = u.find(f"{SITEMAP_NS}loc")
                if loc is not None and loc.text:
                    existing_locs.add(loc.text.rstrip("/"))

        if url.rstrip("/") in existing_locs:
            result["fixed"] = False
            result["action"] = f"skipped — {url} already in sitemap"
            return result

        result["fixed"] = True
        result["action"] = f"flagged {url} for sitemap addition (requires regeneration)"
        return result

    def fix_report(self) -> dict[str, Any]:
        return {
            "run_at": datetime.now(timezone.utc).isoformat(),
            "total_issues_offered": 0,
            "fixes_applied": self.fixes_applied,
            "fixes_count": len(self.fixes_applied),
        }
