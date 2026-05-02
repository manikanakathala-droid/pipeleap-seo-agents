"""
Persistent cross-run content memory for the Pipeleap Growth Engine.

Bridges the gap between the in-memory uniqueness engine (which resets every run)
and the SQLite storage layer (which only tracks slugs and reports).

Persists across every daily run:
  - content_fingerprints  — page-level SHA-256 hashes + shingle corpus texts
  - paragraph_hashes      — paragraph MD5 hashes for L2 dedup
  - topic_ownership       — canonical topic → slug map
  - angle_registry        — semantic angle → slug map (L3)
  - intent_registry       — keyword → (intent, page_type) map (L4)
  - cta_registry          — normalised CTA text → usage count (L5)

On every run:
  1. load() hydrates all registries from SQLite
  2. assess() checks each new page against loaded + in-run corpus
  3. register() persists accepted pages back to SQLite
  4. report() returns a dedup summary for the run report
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modules.pipeleap_seo_engine.engines.uniqueness_engine import GrowthUniquenessEngine


class ContentMemory:
    """
    Persistent cross-run uniqueness registry.

    All six uniqueness layers persist to SQLite so each run inherits
    the full history of published content — not just slug names.
    """

    SCHEMA_VERSION = 2

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = GrowthUniquenessEngine()

        # In-memory registries (hydrated from DB on load())
        self.corpus_texts:    list[str]                  = []   # raw text for L1 Jaccard
        self.paragraph_hashes_set: set[str]              = set() # L2 paragraph hashes
        self.angle_registry:  dict[str, str]             = {}   # angle_key → slug
        self.intent_registry: dict[str, tuple[str, str]] = {}   # keyword → (intent, page_type)
        self.cta_registry:    dict[str, int]             = {}   # normalised_cta → count
        self.topic_ownership: dict[str, dict]            = {}   # topic_key → {slug, page_type}

        # Stats for the current run
        self._run_accepted = 0
        self._run_rejected = 0
        self._run_flags: list[dict] = []

        self._init_schema()

    # ── Schema ────────────────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS cm_fingerprints (
                    slug        TEXT PRIMARY KEY,
                    page_type   TEXT NOT NULL,
                    text_body   TEXT NOT NULL,
                    sha256      TEXT NOT NULL,
                    created_at  TEXT NOT NULL,
                    run_id      TEXT NOT NULL
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS cm_paragraph_hashes (
                    hash        TEXT PRIMARY KEY,
                    slug        TEXT NOT NULL,
                    created_at  TEXT NOT NULL
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS cm_angle_registry (
                    angle_key   TEXT PRIMARY KEY,
                    slug        TEXT NOT NULL,
                    page_type   TEXT NOT NULL,
                    created_at  TEXT NOT NULL
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS cm_intent_registry (
                    keyword     TEXT PRIMARY KEY,
                    intent      TEXT NOT NULL,
                    page_type   TEXT NOT NULL,
                    slug        TEXT NOT NULL,
                    created_at  TEXT NOT NULL
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS cm_cta_registry (
                    cta_key     TEXT PRIMARY KEY,
                    use_count   INTEGER NOT NULL DEFAULT 1,
                    last_slug   TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                )""")
            c.execute("""
                CREATE TABLE IF NOT EXISTS cm_topic_ownership (
                    topic_key   TEXT PRIMARY KEY,
                    slug        TEXT NOT NULL,
                    page_type   TEXT NOT NULL,
                    created_at  TEXT NOT NULL
                )""")
            conn.commit()

    # ── Load from DB ──────────────────────────────────────────────────────────

    def load(self) -> None:
        """Hydrate all in-memory registries from the SQLite store."""
        with self._connect() as conn:
            c = conn.cursor()

            # L1: corpus texts (load up to 300 most recent to bound memory)
            c.execute("SELECT text_body FROM cm_fingerprints ORDER BY created_at DESC LIMIT 300")
            self.corpus_texts = [row[0] for row in c.fetchall()]

            # L2: paragraph hashes
            c.execute("SELECT hash FROM cm_paragraph_hashes")
            self.paragraph_hashes_set = {row[0] for row in c.fetchall()}

            # L3: angle registry
            c.execute("SELECT angle_key, slug FROM cm_angle_registry")
            self.angle_registry = {row[0]: row[1] for row in c.fetchall()}

            # L4: intent registry
            c.execute("SELECT keyword, intent, page_type FROM cm_intent_registry")
            self.intent_registry = {row[0]: (row[1], row[2]) for row in c.fetchall()}

            # L5: CTA registry
            c.execute("SELECT cta_key, use_count FROM cm_cta_registry")
            self.cta_registry = {row[0]: row[1] for row in c.fetchall()}

            # L6: topic ownership
            c.execute("SELECT topic_key, slug, page_type FROM cm_topic_ownership")
            self.topic_ownership = {
                row[0]: {"slug": row[1], "page_type": row[2]}
                for row in c.fetchall()
            }

    # ── Assess a page ─────────────────────────────────────────────────────────

    def assess(self, page: Any) -> dict[str, Any]:
        """
        Run all six uniqueness layers against the page.
        Uses the loaded corpus + in-run pages registered so far.
        Returns an assessment report with publish decision.
        """
        report = self.engine.assess(
            page=page,
            corpus_texts=self.corpus_texts,
            angle_registry=self.angle_registry,
            intent_registry=self.intent_registry,
            cta_registry=self.cta_registry,
            topic_ownership=self.topic_ownership,
        )

        # L2 augment: check against persisted paragraph hashes
        body = getattr(page, "body_markdown", "")
        candidate_para_hashes = self.engine.paragraph_hashes(body)
        shared_paras = candidate_para_hashes & self.paragraph_hashes_set
        if candidate_para_hashes:
            overlap = len(shared_paras) / len(candidate_para_hashes)
            report["paragraph_overlap_persisted"] = round(overlap, 3)
            if overlap > 0.6 and report["publish"]:
                report["flags"].append(
                    f"L2b:persisted_paragraph_overlap={overlap:.0%} "
                    "paragraphs exist in published history"
                )
                if overlap > 0.75:
                    report["publish"] = False

        report["flag_count"] = len(report["flags"])
        return report

    # ── Register accepted page ────────────────────────────────────────────────

    def register(self, page: Any, run_id: str) -> None:
        """
        Persist an accepted page into all six registries.
        Call this ONLY for pages that pass assess() with publish=True.
        """
        now = datetime.now(timezone.utc).isoformat()
        slug      = getattr(page, "slug", "")
        body      = getattr(page, "body_markdown", "")
        page_type = getattr(page, "page_type", "")
        kw        = getattr(page, "primary_keyword", "").lower()
        intent    = getattr(page, "intent", "commercial")
        cta       = getattr(page, "call_to_action", "")
        pillar    = getattr(page, "topical_pillar", "")
        title     = getattr(page, "title", "")
        sha256    = self.engine.fingerprint(body)

        with self._connect() as conn:
            c = conn.cursor()

            # L1: fingerprint + raw text
            c.execute("""
                INSERT OR REPLACE INTO cm_fingerprints
                (slug, page_type, text_body, sha256, created_at, run_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (slug, page_type, body, sha256, now, run_id))
            self.corpus_texts.insert(0, body)  # prepend so newest is first

            # L2: paragraph hashes
            para_hashes = self.engine.paragraph_hashes(body)
            for ph in para_hashes:
                c.execute("""
                    INSERT OR IGNORE INTO cm_paragraph_hashes (hash, slug, created_at)
                    VALUES (?, ?, ?)
                """, (ph, slug, now))
            self.paragraph_hashes_set |= para_hashes

            # L3: angle registry
            angle = self.engine.extract_angle(title, kw)
            if angle:
                c.execute("""
                    INSERT OR REPLACE INTO cm_angle_registry
                    (angle_key, slug, page_type, created_at)
                    VALUES (?, ?, ?, ?)
                """, (angle, slug, page_type, now))
                self.angle_registry[angle] = slug

            # L4: intent registry (one entry per keyword)
            if kw:
                c.execute("""
                    INSERT OR REPLACE INTO cm_intent_registry
                    (keyword, intent, page_type, slug, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (kw, intent, page_type, slug, now))
                self.intent_registry[kw] = (intent, page_type)

            # L5: CTA registry
            cta_key = self.engine.normalise_cta(cta)
            if cta_key:
                c.execute("""
                    INSERT INTO cm_cta_registry (cta_key, use_count, last_slug, updated_at)
                    VALUES (?, 1, ?, ?)
                    ON CONFLICT(cta_key) DO UPDATE SET
                        use_count  = use_count + 1,
                        last_slug  = excluded.last_slug,
                        updated_at = excluded.updated_at
                """, (cta_key, slug, now))
                self.cta_registry[cta_key] = self.cta_registry.get(cta_key, 0) + 1

            # L6: topic ownership
            if kw and pillar:
                topic_key = self.engine.topic_key(kw, pillar)
                c.execute("""
                    INSERT OR IGNORE INTO cm_topic_ownership
                    (topic_key, slug, page_type, created_at)
                    VALUES (?, ?, ?, ?)
                """, (topic_key, slug, page_type, now))
                if topic_key not in self.topic_ownership:
                    self.topic_ownership[topic_key] = {"slug": slug, "page_type": page_type}

            conn.commit()

        self._run_accepted += 1

    def record_rejection(self, page: Any, report: dict) -> None:
        """Track rejected pages for reporting."""
        self._run_rejected += 1
        self._run_flags.append({
            "slug":       getattr(page, "slug", ""),
            "page_type":  getattr(page, "page_type", ""),
            "flags":      report.get("flags", []),
            "score":      report.get("page_similarity_score", 0),
        })

    # ── Run report ────────────────────────────────────────────────────────────

    def run_report(self) -> dict[str, Any]:
        return {
            "accepted":          self._run_accepted,
            "rejected":          self._run_rejected,
            "rejection_rate":    round(
                self._run_rejected / max(self._run_accepted + self._run_rejected, 1), 3
            ),
            "corpus_size":       len(self.corpus_texts),
            "angle_registry_size": len(self.angle_registry),
            "topic_ownership_size": len(self.topic_ownership),
            "rejected_pages":    self._run_flags,
        }

    def report_markdown(self) -> str:
        r = self.run_report()
        lines = [
            "## Content Uniqueness Report",
            "",
            f"**Accepted:** {r['accepted']}  |  "
            f"**Rejected:** {r['rejected']}  |  "
            f"**Rejection rate:** {r['rejection_rate']:.0%}",
            f"**Corpus size (cross-run):** {r['corpus_size']} pages",
            f"**Topics owned:** {r['topic_ownership_size']}  |  "
            f"**Angles registered:** {r['angle_registry_size']}",
            "",
        ]
        if r["rejected_pages"]:
            lines += ["### Rejected pages", ""]
            for rej in r["rejected_pages"]:
                lines += [
                    f"- **{rej['slug']}** (score={rej['score']:.3f})",
                    *[f"  - {flag}" for flag in rej["flags"]],
                ]
        return "\n".join(lines)

    # ── Cross-run keyword cannibalization (replaces CannibalizationDetector) ─

    def detect_cannibalization(
        self,
        new_pages: list[Any],
    ) -> list[dict[str, Any]]:
        """
        Full cross-run cannibalization: checks new pages against ALL
        historically published pages (not just the current run).
        """
        issues: list[dict] = []
        from modules.pipeleap_seo_engine.engines.refresh_engine import CannibalizationDetector

        # Load all published page dicts from DB
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("SELECT slug, page_type FROM cm_fingerprints")
            historical = [
                {"slug": row[0], "page_type": row[1],
                 "primary_keyword": "", "target_keywords": []}
                for row in c.fetchall()
            ]
            # Also load intent registry for keyword-level conflicts
            c.execute("SELECT keyword, page_type, slug FROM cm_intent_registry")
            kw_map = {row[0]: {"page_type": row[1], "slug": row[2]} for row in c.fetchall()}

        # Check new pages against historical keyword claims
        for page in new_pages:
            kw = getattr(page, "primary_keyword", "").lower()
            existing = kw_map.get(kw)
            if existing and existing["slug"] != getattr(page, "slug", ""):
                issues.append({
                    "type":    "cross_run_keyword_conflict",
                    "keyword": kw,
                    "new_slug": getattr(page, "slug", ""),
                    "existing_slug": existing["slug"],
                    "existing_page_type": existing["page_type"],
                    "recommendation": (
                        f"'{getattr(page, 'slug', '')}' targets '{kw}' which is already "
                        f"owned by '{existing['slug']}' ({existing['page_type']}). "
                        "Differentiate by intent, audience, or keyword modifier."
                    ),
                    "severity": "HIGH",
                })

        # In-run cannibalization (existing logic)
        detector = CannibalizationDetector()
        new_page_dicts = [
            p.to_dict() if hasattr(p, "to_dict") else {}
            for p in new_pages
        ]
        in_run_issues = detector.detect(new_page_dicts)

        return issues + in_run_issues
