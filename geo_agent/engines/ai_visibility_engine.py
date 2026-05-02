"""
AI Visibility Engine — tracks whether Pipeleap appears in AI-generated answers.

Tests visibility across:
  - Google AI Overviews (via DataForSEO SERP check)
  - Perplexity AI (via API or manual tracking)
  - ChatGPT / Bing Copilot (manual tracking registry)

Outputs a visibility matrix: which queries mention Pipeleap, which don't,
and what's needed to earn a citation on each.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from geo_agent.data.geo_entities import GEO_TARGET_QUERIES


class AIVisibilityEngine:
    """
    Tracks Pipeleap's current visibility across AI-powered search engines.
    Reads from a persistent visibility_registry.json and updates it each run.
    """

    def __init__(self, registry_path: str | None = None) -> None:
        self.registry_path = Path(registry_path or "outputs/geo/visibility_registry.json")
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._registry: dict[str, Any] = self._load_registry()

    # ── Public API ─────────────────────────────────────────────────────────────

    def check_ai_overview_coverage(
        self,
        serp_data: list[dict],
    ) -> dict[str, Any]:
        """
        Cross-reference DataForSEO SERP results against GEO target queries.
        Returns which queries have AI Overviews and Pipeleap's estimated eligibility.
        """
        results: dict[str, Any] = {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "total_queries": 0,
            "ai_overview_present": [],
            "paa_present": [],
            "no_ai_features": [],
            "pipeleap_eligible": [],
        }

        serp_lookup = {r.get("keyword", "").lower(): r for r in serp_data}
        all_queries = [q for queries in GEO_TARGET_QUERIES.values() for q in queries]
        results["total_queries"] = len(all_queries)

        for query in all_queries:
            serp = serp_lookup.get(query.lower(), {})
            has_aio  = serp.get("has_ai_overview", False)
            has_paa  = serp.get("has_paa", False)

            if has_aio:
                results["ai_overview_present"].append(query)
            if has_paa:
                results["paa_present"].append(query)
            if not has_aio and not has_paa:
                results["no_ai_features"].append(query)

            # Estimate eligibility: queries where Pipeleap content matches the answer format
            if has_aio or has_paa:
                category = self._get_query_category(query)
                if category in ("definition", "comparison", "how_to"):
                    results["pipeleap_eligible"].append(query)

        return results

    def record_manual_check(
        self,
        query: str,
        ai_engine: str,
        pipeleap_mentioned: bool,
        mention_context: str = "",
        citation_position: int | None = None,
    ) -> None:
        """
        Record a manual visibility check result.
        Call this after manually querying ChatGPT, Perplexity, etc.
        """
        key = f"{ai_engine}::{query.lower()}"
        self._registry[key] = {
            "query":             query,
            "ai_engine":         ai_engine,
            "pipeleap_mentioned": pipeleap_mentioned,
            "mention_context":   mention_context,
            "citation_position": citation_position,
            "checked_at":        datetime.now(timezone.utc).isoformat(),
        }
        self._save_registry()

    def visibility_matrix(self) -> dict[str, Any]:
        """
        Return current visibility across all tracked AI engines and queries.
        """
        by_engine: dict[str, list] = {}
        for record in self._registry.values():
            engine = record.get("ai_engine", "unknown")
            by_engine.setdefault(engine, []).append(record)

        summary: dict[str, Any] = {}
        for engine, records in by_engine.items():
            total    = len(records)
            mentioned = sum(1 for r in records if r.get("pipeleap_mentioned"))
            summary[engine] = {
                "total_checked":      total,
                "pipeleap_mentioned": mentioned,
                "visibility_rate":    round(mentioned / max(total, 1) * 100, 1),
                "not_mentioned":      [r["query"] for r in records if not r.get("pipeleap_mentioned")],
            }
        return summary

    def visibility_report_md(self) -> str:
        """Generate a markdown visibility report for the run output."""
        matrix = self.visibility_matrix()
        lines = [
            "## AI Visibility Report",
            "",
            f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
        ]

        if not matrix:
            lines += [
                "No manual visibility checks recorded yet.",
                "",
                "**How to record checks:**",
                "```python",
                "from geo_agent.engines.ai_visibility_engine import AIVisibilityEngine",
                "engine = AIVisibilityEngine()",
                "engine.record_manual_check(",
                "    query='What is the best outbound automation for SaaS?',",
                "    ai_engine='chatgpt',",
                "    pipeleap_mentioned=False,",
                "    mention_context='',",
                ")",
                "```",
            ]
            return "\n".join(lines)

        lines += ["| AI Engine | Checked | Mentioned | Visibility Rate |", "| --- | --- | --- | --- |"]
        for engine, data in sorted(matrix.items()):
            lines.append(
                f"| {engine} | {data['total_checked']} | "
                f"{data['pipeleap_mentioned']} | {data['visibility_rate']}% |"
            )

        lines += ["", "### Queries where Pipeleap is NOT mentioned", ""]
        for engine, data in sorted(matrix.items()):
            not_mentioned = data.get("not_mentioned", [])
            if not_mentioned:
                lines.append(f"**{engine}:**")
                for q in not_mentioned[:5]:
                    lines.append(f"  - {q}")

        return "\n".join(lines)

    def action_plan(self) -> list[str]:
        """
        Return prioritised actions to improve AI visibility.
        """
        matrix = self.visibility_matrix()
        actions = []

        for engine, data in sorted(matrix.items(), key=lambda x: x[1].get("visibility_rate", 0)):
            rate = data.get("visibility_rate", 0)
            if rate < 20:
                actions.append(
                    f"CRITICAL: {engine} visibility at {rate}% — "
                    "create answer-block pages for all uncovered queries"
                )
            elif rate < 50:
                actions.append(
                    f"HIGH: {engine} visibility at {rate}% — "
                    "improve existing page answer blocks and FAQPage schema"
                )

        if not actions:
            actions = [
                "Start recording manual AI visibility checks via record_manual_check()",
                "Run DataForSEO SERP checks on all GEO target queries to detect AI Overviews",
            ]
        return actions

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load_registry(self) -> dict:
        if self.registry_path.exists():
            try:
                return json.loads(self.registry_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_registry(self) -> None:
        self.registry_path.write_text(
            json.dumps(self._registry, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _get_query_category(query: str) -> str:
        for cat, queries in GEO_TARGET_QUERIES.items():
            if query in queries:
                return cat
        return "unknown"
