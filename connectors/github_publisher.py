"""GitHub publisher — pushes generated content into the Lovable project's TypeScript data files."""
from __future__ import annotations

import base64
import json
import logging
import os
import re
from typing import TYPE_CHECKING, Any

import requests

if TYPE_CHECKING:
    from utils.models import ContentAsset
    from modules.pipeleap_seo_engine.models import GrowthPage

log = logging.getLogger(__name__)

_API = "https://api.github.com"


class GitHubPublisher:
    """Appends content entries to TypeScript data files in a Lovable GitHub repo."""

    def __init__(
        self,
        token: str = "",
        repo: str = "",
        branch: str = "main",
        blog_data_path: str = "src/data/blog-articles.ts",
        tools_data_path: str = "src/data/tools-data.ts",
    ) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.repo = repo or os.getenv("GITHUB_REPO", "")
        self.branch = branch
        self.blog_data_path = blog_data_path
        self.tools_data_path = tools_data_path

    def is_configured(self) -> bool:
        return bool(self.token and self.repo)

    # ── Public publish methods ────────────────────────────────────────────────

    def publish_blog_post(self, asset: Any) -> bool:
        """Append a blog post entry to the Lovable blog-articles TypeScript data file."""
        if not self.is_configured():
            return False
        try:
            content, sha = self._get_file(self.blog_data_path)
            entry = self._blog_entry(asset)
            updated = self._append_ts_entry(content, entry)
            slug = getattr(asset, "slug", "unknown")
            return self._update_file(
                self.blog_data_path,
                updated,
                sha,
                f"feat(seo): add blog post '{slug}'",
            )
        except Exception as exc:
            log.warning("GitHub publish blog failed: %s", exc)
            return False

    def publish_tool_page(self, page: Any) -> bool:
        """Append a tool page entry to the Lovable tools-data TypeScript data file."""
        if not self.is_configured():
            return False
        try:
            content, sha = self._get_file(self.tools_data_path)
            entry = self._tool_entry(page)
            updated = self._append_ts_entry(content, entry)
            slug = getattr(page, "slug", "unknown")
            return self._update_file(
                self.tools_data_path,
                updated,
                sha,
                f"feat(seo): add tool page '{slug}'",
            )
        except Exception as exc:
            log.warning("GitHub publish tool page failed: %s", exc)
            return False

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_file(self, path: str) -> tuple[str, str]:
        """Return (decoded_content, sha) for a file in the repo."""
        url = f"{_API}/repos/{self.repo}/contents/{path}"
        resp = requests.get(url, headers=self._headers(), params={"ref": self.branch}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        decoded = base64.b64decode(data["content"]).decode("utf-8")
        return decoded, data["sha"]

    def _update_file(self, path: str, content: str, sha: str, message: str) -> bool:
        """Commit updated content back to the repo."""
        url = f"{_API}/repos/{self.repo}/contents/{path}"
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "sha": sha,
            "branch": self.branch,
        }
        resp = requests.put(url, headers=self._headers(), json=payload, timeout=15)
        if resp.status_code in (200, 201):
            log.info("GitHub: committed %s", path)
            return True
        log.warning("GitHub commit failed %s: %s %s", path, resp.status_code, resp.text[:200])
        return False

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    # ── TypeScript data file manipulation ─────────────────────────────────────

    def _append_ts_entry(self, ts_content: str, entry: dict[str, Any]) -> str:
        """
        Append a new object literal into the last array export in a TypeScript file.
        Finds the final `];` and inserts the serialized entry before it.
        """
        entry_str = self._dict_to_ts_object(entry)
        # Find the last closing bracket of an exported array
        last_bracket = ts_content.rfind("];")
        if last_bracket == -1:
            raise ValueError("Could not find closing ]; in TypeScript data file")
        # Insert entry before the closing bracket
        return ts_content[:last_bracket] + f"  {entry_str},\n" + ts_content[last_bracket:]

    def _dict_to_ts_object(self, obj: dict[str, Any], indent: int = 2) -> str:
        """Convert a Python dict to a TypeScript object literal string."""
        lines = ["{"]
        pad = " " * (indent + 2)
        close_pad = " " * indent
        for k, v in obj.items():
            lines.append(f"{pad}{k}: {self._ts_value(v)},")
        lines.append(f"{close_pad}}}")
        return "\n".join(lines)

    def _ts_value(self, v: Any) -> str:
        if isinstance(v, str):
            escaped = v.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
            return f"`{escaped}`"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, list):
            items = ", ".join(self._ts_value(i) for i in v)
            return f"[{items}]"
        if isinstance(v, dict):
            return self._dict_to_ts_object(v)
        return f"`{v}`"

    # ── Entry builders ────────────────────────────────────────────────────────

    def _blog_entry(self, asset: Any) -> dict[str, Any]:
        slug = getattr(asset, "slug", "")
        # Strip "blog/" prefix if present — Lovable routes handle the segment
        clean_slug = re.sub(r"^blog/", "", slug)
        schema = getattr(asset, "schema_markup", [])
        return {
            "slug": clean_slug,
            "title": getattr(asset, "seo_title", "") or getattr(asset, "title", ""),
            "excerpt": getattr(asset, "meta_description", ""),
            "content": getattr(asset, "body_markdown", ""),
            "publishedAt": getattr(asset, "date_published", ""),
            "keywords": getattr(asset, "source_keywords", []),
            "schemaMarkup": json.dumps(schema, ensure_ascii=False),
        }

    def _tool_entry(self, page: Any) -> dict[str, Any]:
        slug = getattr(page, "slug", "")
        clean_slug = re.sub(r"^tools/", "", slug)
        schema = getattr(page, "schema_markup", [])
        return {
            "slug": clean_slug,
            "title": getattr(page, "seo_title", "") or getattr(page, "title", ""),
            "excerpt": getattr(page, "meta_description", ""),
            "content": getattr(page, "body_markdown", ""),
            "publishedAt": getattr(page, "date_published", ""),
            "keywords": getattr(page, "target_keywords", []),
            "schemaMarkup": json.dumps(schema, ensure_ascii=False),
        }
