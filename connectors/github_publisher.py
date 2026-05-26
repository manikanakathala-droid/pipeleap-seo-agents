"""GitHub publisher — pushes generated content into the Lovable project's TypeScript data files."""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
import random
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import requests

from connectors.indexing_trigger import IndexingTrigger

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
        tools_data_path: str = "src/data/tools/index.ts",
    ) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("LAUNCHPAD_DEPLOY_TOKEN") or ""
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
            success = self._update_file(
                self.blog_data_path,
                updated,
                sha,
                f"feat(seo): add blog post '{slug}'",
            )
            if success:
                pub_date = getattr(asset, "date_published", "") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
                url = f"https://www.pipeleap.com/blog/{slug}"
                self.update_sitemap([(url, pub_date)])
                try:
                    trigger = IndexingTrigger()
                    trigger.submit_urls([url])
                except Exception as e:
                    log.warning("Indexing trigger failed: %s", e)
            return success
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
            success = self._update_file(
                self.tools_data_path,
                updated,
                sha,
                f"feat(seo): add tool page '{slug}'",
            )
            if success:
                pub_date = getattr(page, "date_published", "") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
                url = f"https://www.pipeleap.com/tools/{slug}"
                self.update_sitemap([(url, pub_date)])
                try:
                    trigger = IndexingTrigger()
                    trigger.submit_urls([url])
                except Exception as e:
                    log.warning("Indexing trigger failed: %s", e)
            return success
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

    def _update_file(self, path: str, content: str, sha: str, message: str, max_retries: int = 5) -> bool:
        """Commit updated content back to the repo."""
        url = f"{_API}/repos/{self.repo}/contents/{path}"
        
        for attempt in range(max_retries):
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
                
            if resp.status_code == 409:  # Conflict - SHA stale
                log.warning("GitHub 409 conflict for %s, attempt %d/%d", path, attempt + 1, max_retries)
                time.sleep(2 ** attempt + random.uniform(0, 1))
                try:
                    latest_content, sha = self._get_file(path)
                    content = self._reapply_diff(latest_content, content, path)
                except Exception as exc:
                    log.error("Failed to refetch and reapply diff for %s: %s", path, exc)
                    return False
                continue
                
            log.warning("GitHub commit failed %s: %s %s", path, resp.status_code, resp.text[:200])
            break
        return False

    def _reapply_diff(self, latest_content: str, our_content: str, path: str) -> str:
        """Merge our new entry into the latest content fetched after a 409 conflict."""
        if path.endswith(".xml") and "sitemap" in path:
            existing_urls = set(re.findall(r"<loc>(https://[^<]+)</loc>", latest_content))
            our_urls = re.findall(r"(<url>\s*<loc>https://[^<]+</loc>.*?</url>)", our_content, re.DOTALL)
            
            new_entries = []
            for url_block in our_urls:
                loc_match = re.search(r"<loc>(https://[^<]+)</loc>", url_block)
                if loc_match and loc_match.group(1) not in existing_urls:
                    new_entries.append(url_block)
            
            if not new_entries:
                return latest_content
                
            return latest_content.replace("</urlset>", "\n".join(new_entries) + "\n</urlset>")
        
        elif path.endswith(".ts"):
            match = re.search(r"(\s*\{.*?\},\s*)\];$", our_content, re.DOTALL)
            if match:
                our_last_entry_str = match.group(1)
                last_bracket = latest_content.rfind("];")
                if last_bracket != -1:
                    return latest_content[:last_bracket] + our_last_entry_str + latest_content[last_bracket:]
            return our_content
        return our_content

    def _sitemap_path_for_url(self, url: str) -> str:
        if "/blog/" in url:
            return "public/sitemap-blog.xml"
        if "/tools/" in url:
            return "public/sitemap-tools.xml"
        if "/glossary/" in url:
            return "public/sitemap-glossary.xml"
        return "public/sitemap-pages.xml"

    def update_sitemap(self, urls_with_dates: list[tuple[str, str]]) -> bool:
        """Append new URLs to the appropriate sub-sitemap in the Lovable repo.
        urls_with_dates: list of (url, lastmod_iso_date) tuples.
        """
        if not self.is_configured():
            return False

        by_path: dict[str, list[tuple[str, str]]] = {}
        for url, lastmod in urls_with_dates:
            sp = self._sitemap_path_for_url(url)
            by_path.setdefault(sp, []).append((url, lastmod))

        all_ok = True
        for sitemap_path, entries in by_path.items():
            try:
                content, sha = self._get_file(sitemap_path)
                existing = set(re.findall(r"<loc>(https://[^<]+)</loc>", content))

                new_entries = []
                for url, lastmod in entries:
                    if url not in existing:
                        new_entries.append(
                            f"  <url>\n    <loc>{url}</loc>\n"
                            f"    <lastmod>{lastmod}</lastmod>\n"
                            f"    <changefreq>weekly</changefreq>\n"
                            f"    <priority>0.7</priority>\n  </url>"
                        )

                if not new_entries:
                    continue

                updated = content.replace("</urlset>", "\n".join(new_entries) + "\n</urlset>")
                ok = self._update_file(sitemap_path, updated, sha, f"feat(seo): add {len(new_entries)} URLs to sitemap")
                if not ok:
                    all_ok = False
            except Exception as exc:
                log.warning("GitHub update sitemap %s failed: %s", sitemap_path, exc)
                all_ok = False
        return all_ok

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
        Supports both `];` (direct array) and `allTools: Tool[] = [...existing]` (spread import) patterns.
        Skips if an entry with the same `slug` already exists.
        """
        slug = entry.get("slug", "")
        if slug:
            existing_slugs = re.findall(rf"slug:\s*`[^`]+`", ts_content)
            for found in existing_slugs:
                if f"`{slug}`" in found:
                    log.warning("Skipping duplicate tool entry — slug `%s` already exists", slug)
                    return ts_content
        entry_str = self._dict_to_ts_object(entry)

        # Spread import pattern: ...SomeModule,\n];
        spread_match = re.search(r"(\.\.\.\w+),\s*\]", ts_content)
        if spread_match:
            last_spread = ts_content.rfind("...")
            insert_pos = ts_content.find("]", last_spread)
            return ts_content[:insert_pos].rstrip(",\n\r ").rstrip() + f",\n  {entry_str},\n" + ts_content[insert_pos:]

        # Standard direct array: ...\n];
        last_bracket = ts_content.rfind("];")
        if last_bracket == -1:
            raise ValueError("Could not find closing ]; in TypeScript data file")
        return ts_content[:last_bracket].rstrip(",\n\r ").rstrip() + f"  {entry_str},\n" + ts_content[last_bracket:]

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
        clean_slug = re.sub(r"^blog/", "", slug)
        body = getattr(asset, "body_markdown", "")
        keywords = getattr(asset, "source_keywords", [])
        word_count = len(body.split())

        read_minutes = max(1, round(word_count / 200))
        read_time = f"{read_minutes} min read"

        category = self._derive_category(keywords, getattr(asset, "seo_title", "") or getattr(asset, "title", ""))

        pub_date = getattr(asset, "date_published", "")
        if not pub_date:
            pub_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        content_sections = self._body_to_blog_sections(body)

        return {
            "slug": clean_slug,
            "title": getattr(asset, "seo_title", "") or getattr(asset, "title", ""),
            "description": getattr(asset, "meta_description", ""),
            "category": category,
            "publishedAt": pub_date,
            "readTime": read_time,
            "content": content_sections,
        }

    def _derive_category(self, keywords: list[str], title: str) -> str:
        text = " ".join(keywords).lower() + " " + title.lower()
        mapping = [
            ("cold outreach", "Cold Outreach"),
            ("cold email", "Cold Outreach"),
            ("gtm", "GTM Strategy"),
            ("revops", "RevOps Systems"),
            ("revenue ops", "RevOps Systems"),
            ("revenue operation", "RevOps Systems"),
            ("pipeline", "Pipeline Generation"),
            ("outbound", "Outbound Automation"),
        ]
        for keyword, cat in mapping:
            if keyword in text:
                return cat
        return "Outbound Automation"

    def _body_to_blog_sections(self, body_markdown: str) -> list[dict[str, Any]]:
        sections: list[dict[str, Any]] = []
        lines = body_markdown.strip().split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)

            if line.startswith("## "):
                sections.append({"text": line[3:].strip(), "type": "h2"})
                i += 1
                continue

            if line.startswith("- ") or line.startswith("* "):
                items: list[str] = []
                while i < len(lines):
                    l = lines[i].strip()
                    if l.startswith("- ") or l.startswith("* "):
                        item_text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", l[2:].strip())
                        items.append(item_text)
                        i += 1
                    else:
                        break
                sections.append({"items": items, "type": "list"})
                continue

            sections.append({"text": line, "type": "paragraph"})
            i += 1

        if sections and sections[-1].get("type") != "cta":
            last_text = sections[-1].get("text", "")
            if any(kw in last_text.lower() for kw in ("audit", "strategy call", "book", "get in touch", "talk to us", "schedule")):
                sections[-1] = {"text": last_text, "type": "cta"}
            else:
                sections.append({"text": "Ready to see what this looks like in your stack?", "type": "cta"})

        if sections and sections[0].get("type") == "paragraph":
            sections[0]["type"] = "intro"

        return sections

    def _tool_entry(self, page: Any) -> dict[str, Any]:
        slug = getattr(page, "slug", "")
        clean_slug = re.sub(r"^tools/", "", slug)
        pub_date = getattr(page, "date_published", "")
        if not pub_date:
            pub_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        cat_slug = getattr(page, "category_slug", "") or getattr(page, "categorySlug", "")
        if not cat_slug:
            cat_slug = "ai-outbound-agents"

        return {
            "slug": clean_slug,
            "name": getattr(page, "name", "") or getattr(page, "seo_title", "") or getattr(page, "title", ""),
            "categorySlug": cat_slug,
            "tagline": getattr(page, "meta_description", ""),
            "description": getattr(page, "meta_description", ""),
            "longDescription": getattr(page, "body_markdown", ""),
            "website": getattr(page, "website_url", "") or getattr(page, "website", "") or "",
            "pricing": getattr(page, "pricing", {"model": "Contact", "hasFree": False}),
            "bestFor": getattr(page, "best_for", []) or getattr(page, "bestFor", []),
            "features": getattr(page, "features", []),
            "pros": getattr(page, "pros", []),
            "cons": getattr(page, "cons", []),
            "alternatives": getattr(page, "alternatives", []),
            "useCases": getattr(page, "use_cases", []) or getattr(page, "useCases", []),
            "pipeLeapContext": getattr(page, "pipeleap_context", "") or getattr(page, "pipeLeapContext", ""),
            "faqs": getattr(page, "faqs", []),
            "publishedAt": pub_date,
        }
