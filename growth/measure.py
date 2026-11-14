"""
Collect outcome data. Every source reports its own status; nothing is estimated.

Sources:
  search    Google Search Console API, or a CSV export dropped in growth_state/imports/
  analytics GA4 sessions and enquiry (key) events by page
"""
from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from growth.site import normalize_path


@dataclass
class SourceStatus:
    name: str
    state: str            # ok | empty | unavailable | error
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.state in ("ok", "empty")


@dataclass
class Measurement:
    day: date
    window_days: int = 28
    search: SourceStatus = field(default_factory=lambda: SourceStatus("search", "unavailable", "not collected"))
    analytics: SourceStatus = field(default_factory=lambda: SourceStatus("analytics", "unavailable", "not collected"))
    rows: list[dict[str, Any]] = field(default_factory=list)           # current window: query x page
    previous_rows: list[dict[str, Any]] = field(default_factory=list)  # window before that
    sessions: dict[str, int] = field(default_factory=dict)             # path -> sessions
    enquiries: dict[str, int] = field(default_factory=dict)            # path -> enquiry events

    def per_page(self, rows: list[dict[str, Any]] | None = None) -> dict[str, dict[str, float]]:
        """Aggregate query rows to page level, impression-weighting position."""
        pages: dict[str, dict[str, float]] = {}
        for row in self.rows if rows is None else rows:
            path = normalize_path(row.get("page", ""))
            agg = pages.setdefault(path, {"impressions": 0, "clicks": 0, "_pos": 0.0})
            impressions = float(row.get("impressions", 0))
            agg["impressions"] += impressions
            agg["clicks"] += float(row.get("clicks", 0))
            agg["_pos"] += float(row.get("position", 0)) * impressions
        for path, agg in pages.items():
            agg["position"] = round(agg.pop("_pos") / agg["impressions"], 1) if agg["impressions"] else 0.0
            agg["ctr"] = round(agg["clicks"] / agg["impressions"], 4) if agg["impressions"] else 0.0
        if rows is None:
            for path in set(self.sessions) | set(self.enquiries):
                pages.setdefault(path, {"impressions": 0, "clicks": 0, "position": 0.0, "ctr": 0.0})
            for path, agg in pages.items():
                agg["sessions"] = self.sessions.get(path, 0)
                agg["enquiries"] = self.enquiries.get(path, 0)
        return pages

    def totals(self) -> dict[str, float]:
        return {
            "impressions": sum(float(r.get("impressions", 0)) for r in self.rows),
            "clicks": sum(float(r.get("clicks", 0)) for r in self.rows),
            "sessions": sum(self.sessions.values()),
            "enquiries": sum(self.enquiries.values()),
        }


def _read_csv(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            low = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
            query = low.get("query") or low.get("top queries") or ""
            page = low.get("page") or low.get("top pages") or low.get("url") or ""
            if not (query or page):
                continue
            rows.append({
                "query": query,
                "page": page,
                "clicks": float(low.get("clicks") or 0),
                "impressions": float(low.get("impressions") or 0),
                "position": float(low.get("position") or 0),
            })
    return rows


def collect(config: dict[str, Any], growth: dict[str, Any], state_dir: Path,
            today: date, logger: logging.Logger, offline: bool = False) -> Measurement:
    window = int(growth.get("measurement", {}).get("window_days", 28))
    measurement = Measurement(day=today, window_days=window)
    imports = state_dir / "imports"

    # ── search ─────────────────────────────────────────────────────────────
    current_csv, previous_csv = imports / "gsc_current.csv", imports / "gsc_previous.csv"
    if current_csv.exists():
        measurement.rows = _read_csv(current_csv)
        measurement.previous_rows = _read_csv(previous_csv) if previous_csv.exists() else []
        measurement.search = SourceStatus("search", "ok" if measurement.rows else "empty",
                                          f"CSV import ({len(measurement.rows)} rows)")
    elif offline:
        measurement.search = SourceStatus("search", "unavailable", "offline run")
    else:
        measurement.search = _collect_gsc(config, measurement, today, window, logger)

    # ── analytics ──────────────────────────────────────────────────────────
    if offline:
        measurement.analytics = SourceStatus("analytics", "unavailable", "offline run")
    else:
        measurement.analytics = _collect_ga4(config, growth, measurement, window, logger)
    return measurement


def _collect_gsc(config: dict[str, Any], measurement: Measurement, today: date,
                 window: int, logger: logging.Logger) -> SourceStatus:
    try:
        from connectors.gsc_connector import GoogleSearchConsoleConnector
        gsc = GoogleSearchConsoleConnector(config, logger)
    except Exception as exc:  # missing google libs
        return SourceStatus("search", "unavailable", f"Search Console client not importable: {exc}")
    if not gsc._is_auth_available():
        return SourceStatus("search", "unavailable", "no Search Console credentials in this environment")
    # Search Console data lags ~2 days; end the window there so periods are comparable.
    end = today - timedelta(days=2)
    start = end - timedelta(days=window - 1)
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=window - 1)
    rows, errors = gsc.fetch_query_data(start.isoformat(), end.isoformat(), row_limit=5000)
    if errors:
        return SourceStatus("search", "error", "; ".join(errors)[:300])
    previous, _ = gsc.fetch_query_data(prev_start.isoformat(), prev_end.isoformat(), row_limit=5000)
    measurement.rows, measurement.previous_rows = rows, previous
    if not rows:
        return SourceStatus("search", "empty",
                            f"Search Console returned no rows for {gsc.site_url} ({start} to {end})")
    return SourceStatus("search", "ok", f"{len(rows)} query-page rows, {start} to {end}")


def _collect_ga4(config: dict[str, Any], growth: dict[str, Any], measurement: Measurement,
                 window: int, logger: logging.Logger) -> SourceStatus:
    try:
        from connectors.ga4_connector import GA4Connector
        ga4 = GA4Connector(config, logger)
    except Exception as exc:
        return SourceStatus("analytics", "unavailable", f"GA4 client not importable: {exc}")
    if not ga4.is_connected():
        return SourceStatus("analytics", "unavailable", "no GA4 credentials or property configured")
    start = f"{window}daysAgo"
    pages = ga4.fetch_top_pages(start_date=start, end_date="today", limit=500)
    for row in pages:
        path = normalize_path(row.get("page_path", ""))
        measurement.sessions[path] = measurement.sessions.get(path, 0) + int(row.get("sessions", 0))
    enquiry_events = set(growth.get("measurement", {}).get("enquiry_events", []))
    for row in ga4.fetch_conversions(start_date=start, end_date="today"):
        if enquiry_events and row.get("event_name") not in enquiry_events:
            continue
        path = normalize_path(row.get("page_path", ""))
        measurement.enquiries[path] = measurement.enquiries.get(path, 0) + int(row.get("event_count", 0))
    if not pages:
        return SourceStatus("analytics", "empty", "GA4 returned no sessions for the window")
    return SourceStatus("analytics", "ok", f"{len(pages)} pages with sessions")
