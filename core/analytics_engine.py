from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from utils.models import KeywordCluster
from utils.storage import SEOStorage


class AnalyticsEngine:
    """Summarizes performance and creates the weekly learning loop."""

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger
        self.analytics_config = config.get("integrations", {}).get("analytics", {})

    def detect_decay(
        self,
        gsc_rows: list[dict[str, Any]],
        storage: SEOStorage,
    ) -> list[dict[str, Any]]:
        """Compares live GSC rows against stored history to flag ranking/impression decay."""
        thresholds = self.config.get("growth_engine", {}).get("decay_thresholds", {})
        pos_delta_min = float(thresholds.get("position_regression_delta", 5.0))
        pos_crit_from = float(thresholds.get("position_critical_from", 10.0))
        pos_crit_to = float(thresholds.get("position_critical_to", 15.0))
        imp_drop_pct = float(thresholds.get("impression_drop_pct", 30.0))
        imp_min = int(thresholds.get("impression_min_absolute", 100))
        min_impressions = int(thresholds.get("position_drop_min_impressions", 50))

        decayed: list[dict[str, Any]] = []
        for row in gsc_rows:
            keyword = row.get("query", "")
            impressions = int(row.get("impressions", 0))
            position = row.get("position")
            if not keyword or position is None or impressions < min_impressions:
                continue
            previous = storage.fetch_previous_keyword(keyword)
            if not previous:
                continue
            prev_position = previous.get("average_position")
            prev_impressions = int(previous.get("current_impressions", 0))
            if prev_position is None:
                continue

            reasons: list[str] = []
            severity = "medium"
            pos_drop = float(position) - float(prev_position)  # positive = dropped

            if pos_drop >= pos_delta_min:
                reasons.append(
                    f"Position dropped {pos_drop:.1f} ranks (was {float(prev_position):.1f}, now {float(position):.1f})"
                )
                if float(prev_position) <= pos_crit_from and float(position) >= pos_crit_to:
                    severity = "critical"

            if prev_impressions >= imp_min:
                imp_change = (prev_impressions - impressions) / prev_impressions * 100
                if imp_change >= imp_drop_pct:
                    reasons.append(f"Impressions fell {imp_change:.0f}% ({prev_impressions} → {impressions})")
                    if imp_change >= imp_drop_pct * 1.5:
                        severity = "critical"

            if reasons:
                decayed.append({
                    "keyword": keyword,
                    "severity": severity,
                    "current_position": round(float(position), 1),
                    "previous_position": round(float(prev_position), 1),
                    "position_delta": round(pos_drop, 1),
                    "current_impressions": impressions,
                    "previous_impressions": prev_impressions,
                    "reasons": reasons,
                    "refresh_action": (
                        f"Refresh '{keyword}': update title/meta, add new FAQ section, "
                        f"strengthen internal links, and verify page is indexed."
                    ),
                })

        return sorted(decayed, key=lambda x: x["position_delta"], reverse=True)[:20]

    def summarize(
        self,
        keyword_clusters: list[KeywordCluster],
        storage: SEOStorage,
        gsc_rows: list[dict[str, Any]] | None = None,
        run_id: str = "",
        period_start: str = "",
        period_end: str = "",
    ) -> tuple[dict[str, Any], str]:
        opportunities = [item for cluster in keyword_clusters for item in cluster.opportunities]
        total_clicks = sum(item.current_clicks for item in opportunities)
        total_impressions = sum(item.current_impressions for item in opportunities)
        average_ctr = round((total_clicks / total_impressions), 4) if total_impressions else 0.0

        positions = [item.average_position for item in opportunities if item.average_position is not None]
        average_position = round(mean(positions), 2) if positions else None

        rising_queries: list[dict[str, Any]] = []
        low_ctr_queries: list[dict[str, Any]] = []
        gained_5plus = 0
        lost_5plus = 0

        # Per-keyword comparison against previous run snapshot
        for item in opportunities[:200]:
            previous = storage.fetch_previous_keyword(item.keyword)
            if previous:
                prev_pos = previous.get("average_position")
                if prev_pos is not None and item.average_position is not None:
                    delta = round(float(prev_pos) - float(item.average_position), 2)
                    if delta >= 5:
                        gained_5plus += 1
                    elif delta <= -5:
                        lost_5plus += 1
                    if delta > 0:
                        rising_queries.append({"keyword": item.keyword, "position_gain": delta})
            if item.current_impressions >= 50 and item.current_ctr < 0.03:
                low_ctr_queries.append({
                    "keyword": item.keyword,
                    "ctr": item.current_ctr,
                    "position": item.average_position,
                })

        # Keyword diff: new vs. lost since last run
        keyword_diff = self._compute_keyword_diff(
            current_keywords={item.keyword for item in opportunities if item.current_impressions > 0},
            storage=storage,
            run_id=run_id,
        )

        conversions = self._load_conversions()
        traffic_to_signup_ratio = None
        if conversions and total_clicks:
            traffic_to_signup_ratio = round(conversions / total_clicks, 4)

        decay_signals = self.detect_decay(gsc_rows, storage) if gsc_rows else []
        if decay_signals:
            self.logger.warning(
                "Decay detected on %d keywords (%d critical)",
                len(decay_signals),
                sum(1 for d in decay_signals if d["severity"] == "critical"),
            )

        # Persist organic keyword metrics time-series
        now_iso = datetime.now(timezone.utc).isoformat()
        if run_id:
            try:
                storage.save_organic_keyword_metrics(
                    run_id=run_id,
                    period_start=period_start,
                    period_end=period_end,
                    total_ranking=len([o for o in opportunities if o.current_impressions > 0]),
                    new_keywords=keyword_diff["new"],
                    lost_keywords=keyword_diff["lost"],
                    gained_5plus=gained_5plus,
                    lost_5plus=lost_5plus,
                    avg_position=average_position,
                    created_at=now_iso,
                )
                storage.save_organic_traffic(
                    run_id=run_id,
                    period_start=period_start,
                    period_end=period_end,
                    total_clicks=total_clicks,
                    total_impressions=total_impressions,
                    avg_ctr=average_ctr,
                    avg_position=average_position,
                    created_at=now_iso,
                )
                self.logger.info(
                    "Organic metrics persisted: %d ranking, +%d new, -%d lost, %d clicks, %d impressions",
                    len([o for o in opportunities if o.current_impressions > 0]),
                    keyword_diff["new"], keyword_diff["lost"],
                    total_clicks, total_impressions,
                )
            except Exception as exc:
                self.logger.warning("Failed to persist organic metrics: %s", exc)

        # Fetch trend for report
        kw_history = storage.fetch_organic_keyword_history(limit=3)
        traffic_history = storage.fetch_organic_traffic_history(limit=3)

        summary = {
            "clicks": total_clicks,
            "impressions": total_impressions,
            "ctr": average_ctr,
            "average_position": average_position,
            "traffic_to_signup_ratio": traffic_to_signup_ratio,
            "rising_queries": rising_queries[:10],
            "low_ctr_queries": low_ctr_queries[:10],
            "decay_signals": decay_signals,
            "keyword_diff": keyword_diff,
            "gained_5plus_positions": gained_5plus,
            "lost_5plus_positions": lost_5plus,
            "organic_keyword_history": kw_history,
            "organic_traffic_history": traffic_history,
            "notes": self._notes(total_impressions, conversions),
        }
        return summary, self._weekly_report_markdown(summary, keyword_clusters)

    @staticmethod
    def _compute_keyword_diff(
        current_keywords: set[str],
        storage: SEOStorage,
        run_id: str,
    ) -> dict[str, int]:
        """Compares current ranking keywords against the previous run's keyword set."""
        prev_run_id = storage.fetch_latest_run_id()
        if not prev_run_id or prev_run_id == run_id:
            return {"new": 0, "lost": 0}
        previous_keywords = storage.fetch_keyword_set_for_run(prev_run_id)
        if not previous_keywords:
            return {"new": len(current_keywords), "lost": 0}
        new_kws = current_keywords - previous_keywords
        lost_kws = previous_keywords - current_keywords
        return {"new": len(new_kws), "lost": len(lost_kws)}

    def _load_conversions(self) -> int | None:
        path_value = self.analytics_config.get("conversion_export_path")
        if not path_value:
            return None

        path = Path(path_value)
        if not path.exists():
            return None

        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return int(payload.get("conversions", 0))
            if isinstance(payload, list):
                return sum(int(item.get("conversions", 0)) for item in payload if isinstance(item, dict))

        if path.suffix.lower() == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                return sum(int(float(row.get("conversions", 0) or 0)) for row in reader)

        return None

    def _notes(self, total_impressions: int, conversions: int | None) -> list[str]:
        notes = []
        if total_impressions == 0:
            gsc_creds = self.config.get("integrations", {}).get("gsc", {}).get("credentials_path", "")
            if gsc_creds:
                notes.append("GSC is connected but the site has no search impressions yet — scoring uses heuristic traffic potential until the site is indexed.")
            else:
                notes.append("Search Console is not configured; keyword scoring uses heuristic traffic potential.")
        if conversions is None:
            export_path = self.analytics_config.get("conversion_export_path", "")
            if export_path:
                notes.append(f"Conversion file configured at '{export_path}' but not found — run export_conversions.py to generate it.")
            else:
                notes.append("Conversion export is not configured; traffic-to-signup analysis is incomplete.")
        return notes

    def _weekly_report_markdown(
        self,
        summary: dict[str, Any],
        keyword_clusters: list[KeywordCluster],
    ) -> str:
        top_clusters = keyword_clusters[:5]
        diff = summary.get("keyword_diff", {})
        kw_history = summary.get("organic_keyword_history", [])
        traffic_history = summary.get("organic_traffic_history", [])

        lines = [
            "# Weekly Pipeleap SEO Report",
            "",
            "## Organic traffic snapshot",
            f"- Clicks (28-day): {summary['clicks']:,}",
            f"- Impressions (28-day): {summary['impressions']:,}",
            f"- CTR: {summary['ctr']:.2%}",
            f"- Average position: {summary['average_position']}",
            f"- Traffic to signup ratio: {summary['traffic_to_signup_ratio']}",
        ]

        # MoM traffic trend
        if len(traffic_history) >= 2:
            curr_clicks = traffic_history[0]["total_clicks"]
            prev_clicks = traffic_history[1]["total_clicks"]
            if prev_clicks > 0:
                delta_pct = round((curr_clicks - prev_clicks) / prev_clicks * 100, 1)
                trend = "▲" if delta_pct >= 0 else "▼"
                lines.append(f"- Click trend vs. previous run: {trend} {abs(delta_pct)}%")

        lines += [
            "",
            "## Organic keyword tracking",
            f"- Keywords with impressions this run: {kw_history[0]['total_ranking'] if kw_history else 'N/A'}",
            f"- New keywords vs. previous run: +{diff.get('new', 0)}",
            f"- Lost keywords vs. previous run: -{diff.get('lost', 0)}",
            f"- Keywords gained 5+ positions: {summary.get('gained_5plus_positions', 0)}",
            f"- Keywords lost 5+ positions: {summary.get('lost_5plus_positions', 0)}",
        ]

        # Keyword count trend
        if len(kw_history) >= 2:
            curr_kw = kw_history[0]["total_ranking"]
            prev_kw = kw_history[1]["total_ranking"]
            kw_delta = curr_kw - prev_kw
            trend = "▲" if kw_delta >= 0 else "▼"
            lines.append(f"- Keyword count trend: {trend} {abs(kw_delta)} vs. previous run")

        lines += ["", "## Top keyword clusters"]
        for cluster in top_clusters:
            lines.append(
                f"- {cluster.cluster_name}: {cluster.primary_keyword} "
                f"(traffic {cluster.aggregate_traffic_potential:.2f}, conversion {cluster.aggregate_conversion_potential:.2f})"
            )

        # Rising queries
        rising = summary.get("rising_queries", [])
        if rising:
            lines += ["", "## Rising queries (position gains this run)"]
            for r in rising[:5]:
                lines.append(f"- **{r['keyword']}** +{r['position_gain']} positions")

        # Low CTR opportunities
        low_ctr = summary.get("low_ctr_queries", [])
        if low_ctr:
            lines += ["", "## Low CTR opportunities (title/meta refresh needed)"]
            for q in low_ctr[:5]:
                lines.append(
                    f"- **{q['keyword']}** — CTR {q['ctr']:.1%} at position "
                    f"{q['position'] or 'N/A'}"
                )

        # Decay alerts
        decay = summary.get("decay_signals", [])
        if decay:
            lines += ["", "## Ranking decay alerts (content refresh required)"]
            for signal in decay[:10]:
                tag = "🔴" if signal["severity"] == "critical" else "🟡"
                lines.append(
                    f"{tag} **{signal['keyword']}** — pos {signal['previous_position']} → "
                    f"{signal['current_position']} (+{signal['position_delta']} drop). "
                    f"{signal['refresh_action']}"
                )

        lines += ["", "## Notes"]
        for note in summary.get("notes", []):
            lines.append(f"- {note}")
        return "\n".join(lines)
