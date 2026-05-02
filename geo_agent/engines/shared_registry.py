"""
Shared Slug Registry — single source of truth for published slugs.

Problem it solves:
  The SEO agent reads slugs from SQLite (assets table).
  The GEO agent reads slugs from the filesystem (src/data/seo/).
  Both write to src/data/seo/ but neither knows about the other's output.
  Result: 64 GEO slugs were invisible to the SEO agent → collision risk.

Solution:
  SharedRegistry combines BOTH sources on every read:
    1. SEO agent SQLite (assets + content_fingerprints tables)
    2. Filesystem scan of cms_publish_dir (catches all agents' output)
  Both agents import this class and use it for existing_slugs.

  After GEO publishes, it calls register_geo_pages() which writes GEO
  slugs back into the SEO agent's SQLite so the SEO agent won't
  regenerate the same content on its next run.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SharedRegistry:
    """
    Canonical slug registry shared by both the SEO agent and GEO agent.
    Read once at the start of any run; write after publishing.
    """

    def __init__(
        self,
        seo_db_path: str | Path,
        cms_publish_dir: str | Path,
        content_memory_db: str | Path | None = None,
    ) -> None:
        self.seo_db      = Path(seo_db_path)
        self.cms_dir     = Path(cms_publish_dir)
        self.memory_db   = Path(content_memory_db) if content_memory_db else None

    # ── Primary API ───────────────────────────────────────────────────────────

    def all_slugs(self) -> set[str]:
        """
        Return every published slug from ALL agents — SQLite + filesystem combined.
        Call this at the start of any agent run.
        """
        slugs: set[str] = set()
        slugs |= self._slugs_from_sqlite()
        slugs |= self._slugs_from_filesystem()
        return slugs

    def register_geo_pages(
        self,
        pages: list[Any],          # list of GEOPage objects
        run_id: str,
    ) -> int:
        """
        Write GEO-published pages back into the SEO agent's SQLite `assets` table
        so the SEO agent's `fetch_all_asset_slugs()` returns them on its next run.
        Returns the number of rows inserted.
        """
        if not self.seo_db.exists():
            return 0

        import json
        now = datetime.now(timezone.utc).isoformat()
        rows = []
        for page in pages:
            slug      = getattr(page, "slug", "")
            page_type = getattr(page, "page_type", "geo_answer")
            payload   = json.dumps({
                "slug":        slug,
                "page_type":   page_type,
                "seo_title":   getattr(page, "title", ""),
                "primary_keyword": getattr(page, "primary_query", ""),
                "source":      "geo_agent",
            })
            rows.append((run_id, slug, page_type, payload, now))

        try:
            with sqlite3.connect(self.seo_db) as conn:
                conn.executemany(
                    """
                    INSERT OR IGNORE INTO assets
                    (run_id, slug, page_type, payload, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    rows,
                )
                conn.commit()
            return len(rows)
        except Exception:
            return 0

    def register_geo_keywords(
        self,
        pages: list[Any],
        run_id: str,
    ) -> int:
        """
        Write GEO page keywords into the SEO agent's keyword_snapshots table
        so organic keyword metrics include GEO-generated pages.

        Each GEO page contributes one keyword_snapshot row using its
        primary_query as the keyword with estimated metrics.
        """
        if not self.seo_db.exists():
            return 0

        import json
        now = datetime.now(timezone.utc).isoformat()
        rows = []
        for page in pages:
            keyword = getattr(page, "primary_query", "") or getattr(page, "slug", "")
            if not keyword:
                continue
            payload = json.dumps({
                "keyword":             keyword,
                "topic_cluster":       getattr(page, "query_category", "geo"),
                "intent":              "informational",
                "funnel_stage":        "problem-aware",
                "source":              "geo_agent",
                "current_clicks":      0,
                "current_impressions": 0,
                "current_ctr":         0.0,
                "average_position":    None,
                "estimated_difficulty": 35.0,
                "revenue_priority_score": 0.0,
            })
            rows.append((run_id, keyword, payload, now))

        if not rows:
            return 0
        try:
            with sqlite3.connect(self.seo_db) as conn:
                conn.executemany(
                    """
                    INSERT INTO keyword_snapshots (run_id, keyword, payload, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    rows,
                )
                conn.commit()
            return len(rows)
        except Exception:
            return 0

    def register_seo_pages_to_memory(
        self,
        pages: list[Any],
        run_id: str,
    ) -> None:
        """
        Write SEO-generated pages into the shared ContentMemory so GEO agent
        sees them during its dedup check.
        Only runs if a shared content_memory_db path is configured.
        """
        if not self.memory_db:
            return
        try:
            from modules.pipeleap_seo_engine.engines.content_memory import ContentMemory
            memory = ContentMemory(db_path=str(self.memory_db))
            for page in pages:
                memory.register(page, run_id)
        except Exception:
            pass

    def slug_owner(self, slug: str) -> str:
        """
        Return which agent published a slug: 'seo_agent' | 'geo_agent' | 'unknown'.
        """
        if not self.seo_db.exists():
            return "unknown"
        try:
            with sqlite3.connect(self.seo_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT payload FROM assets WHERE slug = ? LIMIT 1",
                    (slug,),
                )
                row = cursor.fetchone()
            if row:
                import json
                payload = json.loads(row[0])
                return payload.get("source", "seo_agent")
        except Exception:
            pass
        return "unknown"

    def stats(self) -> dict[str, int]:
        sqlite_slugs = self._slugs_from_sqlite()
        fs_slugs     = self._slugs_from_filesystem()
        return {
            "sqlite_slugs":     len(sqlite_slugs),
            "filesystem_slugs": len(fs_slugs),
            "total_unique":     len(sqlite_slugs | fs_slugs),
            "fs_only":          len(fs_slugs - sqlite_slugs),   # GEO-only risk
            "sqlite_only":      len(sqlite_slugs - fs_slugs),   # orphan risk
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _slugs_from_sqlite(self) -> set[str]:
        if not self.seo_db.exists():
            return set()
        try:
            with sqlite3.connect(self.seo_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT slug FROM assets")
                rows = cursor.fetchall()
            return {row[0] for row in rows if row[0]}
        except Exception:
            return set()

    def _slugs_from_filesystem(self) -> set[str]:
        if not self.cms_dir.exists():
            return set()
        return {d.name for d in self.cms_dir.iterdir() if d.is_dir()}
