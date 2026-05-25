from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional


class SEOStorage:
    """Simple SQLite persistence for keyword history and generated assets."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.fallback_root = self.db_path.parent / f"{self.db_path.stem}_fallback"
        self.mode = "sqlite"
        self.lock = threading.Lock()
        try:
            self._init_schema()
        except sqlite3.Error:
            self.mode = "jsonl"
            self.fallback_root.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS keyword_snapshots (
                    run_id TEXT NOT NULL,
                    keyword TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_keyword_snapshots_keyword ON keyword_snapshots(keyword)"
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS assets (
                    run_id TEXT NOT NULL,
                    slug TEXT NOT NULL,
                    page_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS run_reports (
                    run_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            # Content uniqueness tables — persist cross-run dedup state
            # so the uniqueness engine has full history on every run.
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS content_fingerprints (
                    slug        TEXT PRIMARY KEY,
                    page_type   TEXT NOT NULL,
                    sha256      TEXT NOT NULL,
                    primary_keyword TEXT NOT NULL DEFAULT '',
                    topical_pillar  TEXT NOT NULL DEFAULT '',
                    intent          TEXT NOT NULL DEFAULT 'commercial',
                    word_count      INTEGER NOT NULL DEFAULT 0,
                    created_at  TEXT NOT NULL,
                    run_id      TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_cfp_page_type ON content_fingerprints(page_type)"
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS topic_ownership (
                    topic_key   TEXT PRIMARY KEY,
                    slug        TEXT NOT NULL,
                    page_type   TEXT NOT NULL,
                    intent      TEXT NOT NULL DEFAULT '',
                    created_at  TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS angle_registry (
                    angle_key   TEXT PRIMARY KEY,
                    slug        TEXT NOT NULL,
                    page_type   TEXT NOT NULL,
                    created_at  TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cta_patterns (
                    cta_key     TEXT PRIMARY KEY,
                    use_count   INTEGER NOT NULL DEFAULT 1,
                    last_slug   TEXT NOT NULL DEFAULT '',
                    updated_at  TEXT NOT NULL
                )
                """
            )
            # ── Organic keyword metrics time-series ────────────────────────
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS organic_keyword_metrics (
                    run_id              TEXT PRIMARY KEY,
                    period_start        TEXT NOT NULL,
                    period_end          TEXT NOT NULL,
                    total_ranking       INTEGER NOT NULL DEFAULT 0,
                    new_keywords        INTEGER NOT NULL DEFAULT 0,
                    lost_keywords       INTEGER NOT NULL DEFAULT 0,
                    gained_5plus        INTEGER NOT NULL DEFAULT 0,
                    lost_5plus          INTEGER NOT NULL DEFAULT 0,
                    avg_position        REAL,
                    created_at          TEXT NOT NULL
                )
                """
            )
            # ── Organic traffic time-series ────────────────────────────────
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS organic_traffic_history (
                    run_id          TEXT PRIMARY KEY,
                    period_start    TEXT NOT NULL,
                    period_end      TEXT NOT NULL,
                    total_clicks    INTEGER NOT NULL DEFAULT 0,
                    total_impressions INTEGER NOT NULL DEFAULT 0,
                    avg_ctr         REAL NOT NULL DEFAULT 0.0,
                    avg_position    REAL,
                    created_at      TEXT NOT NULL
                )
                """
            )
            # ── Backlink contact tracker ───────────────────────────────────
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS backlink_contacts (
                    prospect_url    TEXT PRIMARY KEY,
                    prospect_name   TEXT NOT NULL DEFAULT '',
                    category        TEXT NOT NULL DEFAULT '',
                    status          TEXT NOT NULL DEFAULT 'pending',
                    last_contacted  TEXT,
                    run_id          TEXT NOT NULL DEFAULT '',
                    created_at      TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_bc_status ON backlink_contacts(status)"
            )
            connection.commit()

    @staticmethod
    def _payload_for(item: Any) -> dict[str, Any]:
        if hasattr(item, "to_dict"):
            return item.to_dict()
        if isinstance(item, dict):
            return item
        raise TypeError(f"Unsupported storage payload type: {type(item)!r}")

    def save_keyword_snapshots(self, run_id: str, created_at: str, opportunities: list[Any]) -> None:
        if self.mode != "sqlite":
            self._append_jsonl(
                self.fallback_root / "keyword_snapshots.jsonl",
                [
                    {
                        "run_id": run_id,
                        "keyword": self._payload_for(item)["keyword"],
                        "payload": self._payload_for(item),
                        "created_at": created_at,
                    }
                    for item in opportunities
                ],
            )
            return

        with self.lock:
            with self._connect() as connection:
                cursor = connection.cursor()
                cursor.executemany(
                    """
                    INSERT INTO keyword_snapshots (run_id, keyword, payload, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    [
                        (
                            run_id,
                            self._payload_for(item)["keyword"],
                            json.dumps(self._payload_for(item)),
                            created_at,
                        )
                        for item in opportunities
                    ],
                )
                connection.commit()

    def save_assets(self, run_id: str, created_at: str, assets: list[Any]) -> None:
        if self.mode != "sqlite":
            self._append_jsonl(
                self.fallback_root / "assets.jsonl",
                [
                    {
                        "run_id": run_id,
                        "slug": self._payload_for(asset)["slug"],
                        "page_type": self._payload_for(asset)["page_type"],
                        "payload": self._payload_for(asset),
                        "created_at": created_at,
                    }
                    for asset in assets
                ],
            )
            return

        with self.lock:
            with self._connect() as connection:
                cursor = connection.cursor()
                cursor.executemany(
                    """
                    INSERT INTO assets (run_id, slug, page_type, payload, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            run_id,
                            self._payload_for(asset)["slug"],
                            self._payload_for(asset)["page_type"],
                            json.dumps(self._payload_for(asset)),
                            created_at,
                        )
                        for asset in assets
                    ],
                )
                connection.commit()

    def save_run_report(self, run_id: str, created_at: str, report: dict[str, Any]) -> None:
        if self.mode != "sqlite":
            report_dir = self.fallback_root / "run_reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            (report_dir / f"{run_id}.json").write_text(
                json.dumps({"run_id": run_id, "created_at": created_at, "payload": report}, indent=2),
                encoding="utf-8",
            )
            return

        with self.lock:
            with self._connect() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO run_reports (run_id, payload, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (run_id, json.dumps(report), created_at),
                )
                connection.commit()

    def fetch_previous_keyword(self, keyword: str) -> Optional[dict[str, Any]]:
        if self.mode != "sqlite":
            path = self.fallback_root / "keyword_snapshots.jsonl"
            if not path.exists():
                return None
            lines = path.read_text(encoding="utf-8").splitlines()
            for line in reversed(lines):
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("keyword") == keyword:
                    return record.get("payload")
            return None

        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT payload
                FROM keyword_snapshots
                WHERE keyword = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (keyword,),
            )
            row = cursor.fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def fetch_recent_reports(self, limit: int = 5) -> list[dict[str, Any]]:
        if self.mode != "sqlite":
            report_dir = self.fallback_root / "run_reports"
            if not report_dir.exists():
                return []
            files = sorted(report_dir.glob("*.json"), reverse=True)[:limit]
            return [json.loads(file.read_text(encoding="utf-8"))["payload"] for file in files]

        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT payload
                FROM run_reports
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
        return [json.loads(row[0]) for row in rows]

    def fetch_all_asset_slugs(self) -> set[str]:
        if self.mode != "sqlite":
            path = self.fallback_root / "assets.jsonl"
            if not path.exists():
                return set()
            lines = path.read_text(encoding="utf-8").splitlines()
            slugs = set()
            for line in lines:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("slug"):
                    slugs.add(record.get("slug"))
            return slugs

        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT slug FROM assets")
            rows = cursor.fetchall()
        return {row[0] for row in rows}

    # ── Content uniqueness helpers ─────────────────────────────────────────────

    def save_content_fingerprint(
        self,
        run_id: str,
        slug: str,
        page_type: str,
        sha256: str,
        primary_keyword: str = "",
        topical_pillar: str = "",
        intent: str = "commercial",
        word_count: int = 0,
        created_at: str = "",
    ) -> None:
        if self.mode != "sqlite":
            return
        from datetime import datetime, timezone
        ts = created_at or datetime.now(timezone.utc).isoformat()
        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO content_fingerprints
                    (slug, page_type, sha256, primary_keyword, topical_pillar, intent, word_count, created_at, run_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (slug, page_type, sha256, primary_keyword, topical_pillar, intent, word_count, ts, run_id),
                )
                conn.commit()

    def fetch_published_fingerprints(self, limit: int = 500) -> list[dict[str, Any]]:
        """Load published page metadata for cross-run uniqueness checks."""
        if self.mode != "sqlite":
            return []
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT slug, page_type, sha256, primary_keyword, topical_pillar, intent, word_count, created_at
                FROM content_fingerprints
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
        return [
            {
                "slug": r[0], "page_type": r[1], "sha256": r[2],
                "primary_keyword": r[3], "topical_pillar": r[4],
                "intent": r[5], "word_count": r[6], "created_at": r[7],
            }
            for r in rows
        ]

    def fetch_all_published_keywords(self) -> dict[str, dict[str, str]]:
        """Return {keyword: {slug, page_type, intent}} for all published pages."""
        if self.mode != "sqlite":
            return {}
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT primary_keyword, slug, page_type, intent FROM content_fingerprints WHERE primary_keyword != ''"
            )
            rows = cursor.fetchall()
        return {
            r[0]: {"slug": r[1], "page_type": r[2], "intent": r[3]}
            for r in rows
        }

    # ── Organic keyword metrics ────────────────────────────────────────────────

    def save_organic_keyword_metrics(
        self,
        run_id: str,
        period_start: str,
        period_end: str,
        total_ranking: int,
        new_keywords: int,
        lost_keywords: int,
        gained_5plus: int,
        lost_5plus: int,
        avg_position: float | None,
        created_at: str,
    ) -> None:
        if self.mode != "sqlite":
            self._append_jsonl(
                self.fallback_root / "organic_keyword_metrics.jsonl",
                [{"run_id": run_id, "period_start": period_start, "period_end": period_end,
                  "total_ranking": total_ranking, "new_keywords": new_keywords,
                  "lost_keywords": lost_keywords, "gained_5plus": gained_5plus,
                  "lost_5plus": lost_5plus, "avg_position": avg_position, "created_at": created_at}],
            )
            return
        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO organic_keyword_metrics
                    (run_id, period_start, period_end, total_ranking, new_keywords,
                     lost_keywords, gained_5plus, lost_5plus, avg_position, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (run_id, period_start, period_end, total_ranking, new_keywords,
                     lost_keywords, gained_5plus, lost_5plus, avg_position, created_at),
                )
                conn.commit()

    def fetch_organic_keyword_history(self, limit: int = 12) -> list[dict[str, Any]]:
        if self.mode != "sqlite":
            return []
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT run_id, period_start, period_end, total_ranking, new_keywords,
                       lost_keywords, gained_5plus, lost_5plus, avg_position, created_at
                FROM organic_keyword_metrics
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {"run_id": r[0], "period_start": r[1], "period_end": r[2],
             "total_ranking": r[3], "new_keywords": r[4], "lost_keywords": r[5],
             "gained_5plus": r[6], "lost_5plus": r[7], "avg_position": r[8],
             "created_at": r[9]}
            for r in rows
        ]

    def fetch_previous_organic_keyword_metrics(self) -> dict[str, Any] | None:
        rows = self.fetch_organic_keyword_history(limit=2)
        return rows[1] if len(rows) >= 2 else (rows[0] if rows else None)

    # ── Organic traffic history ────────────────────────────────────────────────

    def save_organic_traffic(
        self,
        run_id: str,
        period_start: str,
        period_end: str,
        total_clicks: int,
        total_impressions: int,
        avg_ctr: float,
        avg_position: float | None,
        created_at: str,
    ) -> None:
        if self.mode != "sqlite":
            self._append_jsonl(
                self.fallback_root / "organic_traffic_history.jsonl",
                [{"run_id": run_id, "period_start": period_start, "period_end": period_end,
                  "total_clicks": total_clicks, "total_impressions": total_impressions,
                  "avg_ctr": avg_ctr, "avg_position": avg_position, "created_at": created_at}],
            )
            return
        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO organic_traffic_history
                    (run_id, period_start, period_end, total_clicks, total_impressions,
                     avg_ctr, avg_position, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (run_id, period_start, period_end, total_clicks, total_impressions,
                     avg_ctr, avg_position, created_at),
                )
                conn.commit()

    def fetch_organic_traffic_history(self, limit: int = 12) -> list[dict[str, Any]]:
        if self.mode != "sqlite":
            return []
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT run_id, period_start, period_end, total_clicks, total_impressions,
                       avg_ctr, avg_position, created_at
                FROM organic_traffic_history
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {"run_id": r[0], "period_start": r[1], "period_end": r[2],
             "total_clicks": r[3], "total_impressions": r[4],
             "avg_ctr": r[5], "avg_position": r[6], "created_at": r[7]}
            for r in rows
        ]

    # ── Backlink contact tracker ───────────────────────────────────────────────

    def upsert_backlink_contact(
        self,
        prospect_url: str,
        prospect_name: str,
        category: str,
        status: str,
        run_id: str,
        created_at: str,
    ) -> None:
        if self.mode != "sqlite":
            return
        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO backlink_contacts
                        (prospect_url, prospect_name, category, status, last_contacted, run_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(prospect_url) DO UPDATE SET
                        status        = excluded.status,
                        last_contacted = excluded.last_contacted,
                        run_id        = excluded.run_id
                    """,
                    (prospect_url, prospect_name, category, status, created_at, run_id, created_at),
                )
                conn.commit()

    def fetch_contacted_prospect_urls(self, within_days: int = 30) -> set[str]:
        """Returns URLs contacted within the last `within_days` days."""
        if self.mode != "sqlite":
            return set()
        from datetime import datetime, timedelta, timezone
        cutoff = (datetime.now(timezone.utc) - timedelta(days=within_days)).isoformat()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT prospect_url FROM backlink_contacts WHERE last_contacted >= ?",
                (cutoff,),
            ).fetchall()
        return {r[0] for r in rows}

    def fetch_backlink_contact_summary(self) -> dict[str, int]:
        if self.mode != "sqlite":
            return {}
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) FROM backlink_contacts GROUP BY status"
            ).fetchall()
        return {r[0]: r[1] for r in rows}

    # ── Cross-run keyword diff ─────────────────────────────────────────────────

    def fetch_keyword_set_for_run(self, run_id: str) -> set[str]:
        if self.mode != "sqlite":
            return set()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT keyword FROM keyword_snapshots WHERE run_id = ?", (run_id,)
            ).fetchall()
        return {r[0] for r in rows}

    def fetch_latest_run_id(self) -> str | None:
        if self.mode != "sqlite":
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT run_id FROM run_reports ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
        return row[0] if row else None

    def fetch_actioned_directory_urls(self) -> set[str]:
        return set()

    def fetch_actioned_publication_urls(self) -> set[str]:
        return set()

    @staticmethod
    def _append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row))
                handle.write("\n")
