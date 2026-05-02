"""
GSC Decay Detector for Pipeleap SEO.

Detects pages where organic performance is declining by comparing
two GSC periods (current 28 days vs previous 28 days).

Decay signals:
  - Position regression: page was in top 10, now > 15
  - Impression drop: impressions fell > 30% month-over-month
  - CTR collapse: CTR dropped significantly with stable impressions
  - Click decay: clicks dropped > 25% with no impression explanation

Output: prioritised refresh queue with decay reason, severity, and recommended action.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DecaySignal:
    url: str
    slug: str
    primary_keyword: str
    decay_type: str              # "position_drop" | "impression_drop" | "ctr_collapse" | "click_decay"
    severity: str                # "critical" | "high" | "medium"
    current_position: float
    previous_position: float
    current_impressions: int
    previous_impressions: int
    current_ctr: float
    previous_ctr: float
    current_clicks: int
    previous_clicks: int
    recommended_action: str
    priority_score: float = 0.0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "slug": self.slug,
            "primary_keyword": self.primary_keyword,
            "decay_type": self.decay_type,
            "severity": self.severity,
            "current_position": round(self.current_position, 1),
            "previous_position": round(self.previous_position, 1),
            "position_change": round(self.current_position - self.previous_position, 1),
            "current_impressions": self.current_impressions,
            "impression_change_pct": self._pct_change(self.previous_impressions, self.current_impressions),
            "current_ctr": round(self.current_ctr * 100, 2),
            "ctr_change_pct": self._pct_change(self.previous_ctr, self.current_ctr),
            "current_clicks": self.current_clicks,
            "click_change_pct": self._pct_change(self.previous_clicks, self.current_clicks),
            "recommended_action": self.recommended_action,
            "priority_score": round(self.priority_score, 3),
            "notes": self.notes,
        }

    @staticmethod
    def _pct_change(old: float, new: float) -> float:
        if old == 0:
            return 0.0
        return round((new - old) / old * 100, 1)


class DecayDetector:
    """
    Compares two GSC data periods to detect decaying pages.

    Usage:
        detector = DecayDetector(thresholds={...})
        signals = detector.detect(current_rows, previous_rows, published_slugs)
        refresh_queue = detector.prioritise(signals)
    """

    DEFAULT_THRESHOLDS = {
        "position_drop_min_impressions": 50,   # only flag position drops with visible traffic
        "position_regression_delta": 5.0,      # position worsened by 5+ places
        "position_critical_from": 10.0,        # was in top 10, now dropped
        "position_critical_to": 15.0,          # and fell beyond position 15
        "impression_drop_pct": 30.0,           # impressions fell >30%
        "impression_min_absolute": 100,        # minimum impressions for flag to be meaningful
        "ctr_collapse_pct": 25.0,              # CTR dropped >25%
        "ctr_min_impressions": 200,            # only flag CTR on pages with real exposure
        "click_decay_pct": 25.0,               # clicks dropped >25%
        "click_min_absolute": 10,              # minimum clicks to flag
    }

    def __init__(self, thresholds: dict | None = None) -> None:
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}

    def detect(
        self,
        current_rows: list[dict[str, Any]],
        previous_rows: list[dict[str, Any]],
        published_slugs: set[str] | None = None,
    ) -> list[DecaySignal]:
        """
        Compare two GSC periods and return decay signals.

        Both current_rows and previous_rows should be lists of dicts with keys:
          page, query, clicks, impressions, ctr, position
        """
        current_by_page = self._aggregate_by_page(current_rows)
        previous_by_page = self._aggregate_by_page(previous_rows)

        signals: list[DecaySignal] = []

        for page_url, curr in current_by_page.items():
            prev = previous_by_page.get(page_url)
            if not prev:
                continue  # new page — no decay possible

            slug = self._url_to_slug(page_url)
            if published_slugs and slug not in published_slugs:
                continue  # only monitor pages we manage

            signal = self._analyse(page_url, slug, curr, prev)
            if signal:
                signals.append(signal)

        return self.prioritise(signals)

    def prioritise(self, signals: list[DecaySignal]) -> list[DecaySignal]:
        """Score and sort decay signals by revenue impact priority."""
        for s in signals:
            score = 0.0
            # Higher impressions = more traffic at stake
            score += min(s.current_impressions / 1000, 0.3)
            # Better current position = more valuable to recover
            if s.current_position <= 20:
                score += 0.2
            if s.current_position <= 10:
                score += 0.2
            # Severity weight
            score += {"critical": 0.3, "high": 0.2, "medium": 0.1}.get(s.severity, 0.0)
            # Was previously very visible
            if s.previous_impressions > 500:
                score += 0.1
            s.priority_score = min(1.0, score)

        return sorted(signals, key=lambda x: x.priority_score, reverse=True)

    def report_markdown(self, signals: list[DecaySignal], limit: int = 10) -> str:
        if not signals:
            return "No decay signals detected in this period. All monitored pages are stable."

        lines = [
            "## Content Decay Report",
            "",
            f"**{len(signals)} pages with declining organic performance detected.**",
            "Prioritised by traffic impact and recovery potential.",
            "",
            "| Priority | URL | Decay Type | Severity | Position Change | Impression Change | Action |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]

        for i, s in enumerate(signals[:limit], 1):
            pos_delta = s.current_position - s.previous_position
            imp_delta = s._pct_change(s.previous_impressions, s.current_impressions)
            lines.append(
                f"| {i} | /blog/{s.slug} | {s.decay_type.replace('_', ' ')} | "
                f"{s.severity} | +{pos_delta:.1f} | {imp_delta:.0f}% | "
                f"{s.recommended_action[:40]}... |"
            )

        lines += [
            "",
            "### Recommended actions",
            "",
        ]
        for s in signals[:5]:
            lines += [
                f"**/{s.slug}** ({s.severity} — {s.decay_type.replace('_', ' ')}):",
                f"- {s.recommended_action}",
                *(f"- {n}" for n in s.notes),
                "",
            ]

        return "\n".join(lines)

    # ── Internal analysis ─────────────────────────────────────────────────────

    def _analyse(
        self, page_url: str, slug: str, curr: dict, prev: dict
    ) -> DecaySignal | None:
        t = self.thresholds
        signals_found: list[tuple[str, str, str]] = []  # (decay_type, severity, action)

        c_pos = curr["position"]
        p_pos = prev["position"]
        c_imp = curr["impressions"]
        p_imp = prev["impressions"]
        c_ctr = curr["ctr"]
        p_ctr = prev["ctr"]
        c_clicks = curr["clicks"]
        p_clicks = prev["clicks"]

        # ── Position regression
        if c_imp >= t["position_drop_min_impressions"]:
            pos_delta = c_pos - p_pos
            if pos_delta >= t["position_regression_delta"]:
                was_top10 = p_pos <= t["position_critical_from"]
                now_below = c_pos >= t["position_critical_to"]
                severity = "critical" if (was_top10 and now_below) else "high" if pos_delta >= 10 else "medium"
                signals_found.append((
                    "position_drop", severity,
                    f"Refresh content depth and freshness. Add updated statistics. "
                    f"Review SERP competitors for new content that outranked this page."
                ))

        # ── Impression drop
        if p_imp >= t["impression_min_absolute"] and c_imp >= 10:
            imp_drop = (p_imp - c_imp) / p_imp * 100
            if imp_drop >= t["impression_drop_pct"]:
                severity = "critical" if imp_drop >= 50 else "high" if imp_drop >= 35 else "medium"
                signals_found.append((
                    "impression_drop", severity,
                    "Expand topical depth with new H2 sections. Add related keywords. "
                    "Review for technical indexing issues (canonical, noindex)."
                ))

        # ── CTR collapse (impressions stable, CTR dropped)
        if c_imp >= t["ctr_min_impressions"] and p_ctr > 0:
            ctr_drop = (p_ctr - c_ctr) / p_ctr * 100
            if ctr_drop >= t["ctr_collapse_pct"]:
                severity = "high" if ctr_drop >= 40 else "medium"
                signals_found.append((
                    "ctr_collapse", severity,
                    "Rewrite title tag and meta description. Test power words and year in title. "
                    "Add FAQ schema to compete for rich result space."
                ))

        # ── Click decay
        if p_clicks >= t["click_min_absolute"]:
            click_drop = (p_clicks - c_clicks) / p_clicks * 100 if p_clicks > 0 else 0
            if click_drop >= t["click_decay_pct"] and c_pos <= 20:
                severity = "medium"
                signals_found.append((
                    "click_decay", severity,
                    "Review title and meta for relevance. Check if featured snippet was lost. "
                    "Add structured data to compete for rich results."
                ))

        if not signals_found:
            return None

        # Use the highest-severity signal as primary
        severity_order = {"critical": 3, "high": 2, "medium": 1}
        primary = max(signals_found, key=lambda x: severity_order.get(x[1], 0))

        notes = []
        if c_pos > 20:
            notes.append(f"Page now at position {c_pos:.0f} — below first page threshold.")
        if len(signals_found) > 1:
            notes.append(f"Multiple decay signals: {', '.join(s[0] for s in signals_found)}.")
        if p_pos < 5:
            notes.append(f"Was previously in top 5 (position {p_pos:.1f}) — high-value recovery target.")

        keyword = self._keyword_from_page(page_url, curr)

        return DecaySignal(
            url=page_url,
            slug=slug,
            primary_keyword=keyword,
            decay_type=primary[0],
            severity=primary[1],
            current_position=c_pos,
            previous_position=p_pos,
            current_impressions=c_imp,
            previous_impressions=p_imp,
            current_ctr=c_ctr,
            previous_ctr=p_ctr,
            current_clicks=c_clicks,
            previous_clicks=p_clicks,
            recommended_action=primary[2],
            notes=notes,
        )

    # ── Aggregation helpers ────────────────────────────────────────────────────

    @staticmethod
    def _aggregate_by_page(rows: list[dict]) -> dict[str, dict]:
        """Collapse query-level rows into page-level aggregates."""
        pages: dict[str, dict] = {}
        for row in rows:
            page = row.get("page", "")
            if not page:
                continue
            if page not in pages:
                pages[page] = {"clicks": 0, "impressions": 0, "ctr_sum": 0.0,
                               "position_sum": 0.0, "row_count": 0, "top_query": ""}
            p = pages[page]
            p["clicks"] += int(row.get("clicks", 0))
            p["impressions"] += int(row.get("impressions", 0))
            p["position_sum"] += float(row.get("position", 50))
            p["row_count"] += 1
            if not p["top_query"] and row.get("query"):
                p["top_query"] = row["query"]

        result = {}
        for page, data in pages.items():
            rc = max(data["row_count"], 1)
            imp = max(data["impressions"], 1)
            result[page] = {
                "clicks": data["clicks"],
                "impressions": data["impressions"],
                "ctr": data["clicks"] / imp,
                "position": data["position_sum"] / rc,
                "top_query": data["top_query"],
            }
        return result

    @staticmethod
    def _url_to_slug(url: str) -> str:
        url = url.rstrip("/")
        parts = url.split("/blog/")
        return parts[-1] if len(parts) > 1 else url.split("/")[-1]

    @staticmethod
    def _keyword_from_page(url: str, page_data: dict) -> str:
        if page_data.get("top_query"):
            return page_data["top_query"]
        slug = url.rstrip("/").split("/")[-1]
        return slug.replace("-", " ")
