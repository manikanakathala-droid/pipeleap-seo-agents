from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        Metric,
        RunReportRequest,
    )
    from google.oauth2 import service_account
    import google.auth as _google_auth_ga4
    GA4_AVAILABLE = True
except ImportError:
    GA4_AVAILABLE = False
    _google_auth_ga4 = None  # type: ignore


class GA4Connector:
    """
    Fetches Google Analytics 4 data for Pipeleap.

    Capabilities:
    - fetch_top_pages()       : sessions, engaged sessions, bounce rate per page
    - fetch_channel_summary() : traffic by channel (organic, direct, referral, etc.)
    - fetch_conversions()     : goal/event conversion counts by page
    - is_connected()          : quick connectivity check
    """

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.logger = logger
        analytics_cfg = config.get("integrations", {}).get("analytics", {})
        self.property_id: str = analytics_cfg.get("ga4_property_id", "").strip()
        self.credentials_path: str = analytics_cfg.get("credentials_path", "").strip()

    def is_connected(self) -> bool:
        if not GA4_AVAILABLE:
            self.logger.warning("GA4: google-analytics-data not installed")
            return False
        if not self.property_id:
            self.logger.warning("GA4: ga4_property_id not set in config")
            return False
        # Accept either a key file OR ADC (gcloud auth application-default login)
        if self.credentials_path and Path(self.credentials_path).exists():
            return True
        if _google_auth_ga4 is not None:
            try:
                _google_auth_ga4.default()
                return True
            except Exception:
                pass
        self.logger.warning("GA4: no credentials — place key file at %s or run: gcloud auth application-default login", self.credentials_path)
        return False

    def _client(self) -> "BetaAnalyticsDataClient":
        _scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
        if self.credentials_path and Path(self.credentials_path).exists():
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path, scopes=_scopes
            )
        else:
            creds, _ = _google_auth_ga4.default(scopes=_scopes)
        return BetaAnalyticsDataClient(credentials=creds)

    def fetch_top_pages(
        self, start_date: str = "28daysAgo", end_date: str = "today", limit: int = 50
    ) -> list[dict[str, Any]]:
        """Returns sessions, engaged sessions, bounce rate per page path."""
        if not self.is_connected():
            return []
        try:
            client = self._client()
            request = RunReportRequest(
                property=self.property_id,
                dimensions=[Dimension(name="pagePath")],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="engagedSessions"),
                    Metric(name="bounceRate"),
                    Metric(name="averageSessionDuration"),
                ],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                limit=limit,
                order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
            )
            response = client.run_report(request)
            rows = []
            for row in response.rows:
                dims = [d.value for d in row.dimension_values]
                vals = [m.value for m in row.metric_values]
                rows.append({
                    "page_path": dims[0] if dims else "",
                    "sessions": int(vals[0]) if vals else 0,
                    "engaged_sessions": int(vals[1]) if len(vals) > 1 else 0,
                    "bounce_rate": round(float(vals[2]), 4) if len(vals) > 2 else 0.0,
                    "avg_session_duration_s": round(float(vals[3]), 1) if len(vals) > 3 else 0.0,
                })
            self.logger.info("GA4: fetched %d pages", len(rows))
            return rows
        except Exception as exc:
            self.logger.warning("GA4 fetch_top_pages failed: %s", exc)
            return []

    def fetch_channel_summary(
        self, start_date: str = "28daysAgo", end_date: str = "today"
    ) -> list[dict[str, Any]]:
        """Returns sessions and conversions broken down by default channel group."""
        if not self.is_connected():
            return []
        try:
            client = self._client()
            request = RunReportRequest(
                property=self.property_id,
                dimensions=[Dimension(name="sessionDefaultChannelGroup")],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="conversions"),
                    Metric(name="totalRevenue"),
                ],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
            )
            response = client.run_report(request)
            rows = []
            for row in response.rows:
                dims = [d.value for d in row.dimension_values]
                vals = [m.value for m in row.metric_values]
                rows.append({
                    "channel": dims[0] if dims else "",
                    "sessions": int(vals[0]) if vals else 0,
                    "conversions": int(float(vals[1])) if len(vals) > 1 else 0,
                    "revenue": round(float(vals[2]), 2) if len(vals) > 2 else 0.0,
                })
            return rows
        except Exception as exc:
            self.logger.warning("GA4 fetch_channel_summary failed: %s", exc)
            return []

    def fetch_conversions(
        self, start_date: str = "28daysAgo", end_date: str = "today"
    ) -> list[dict[str, Any]]:
        """Returns conversion event counts by page path."""
        if not self.is_connected():
            return []
        try:
            client = self._client()
            request = RunReportRequest(
                property=self.property_id,
                dimensions=[Dimension(name="pagePath"), Dimension(name="eventName")],
                metrics=[Metric(name="eventCount"), Metric(name="conversions")],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimension_filter={
                    "filter": {
                        "field_name": "isKeyEvent",
                        "string_filter": {"value": "true"},
                    }
                },
                limit=100,
            )
            response = client.run_report(request)
            rows = []
            for row in response.rows:
                dims = [d.value for d in row.dimension_values]
                vals = [m.value for m in row.metric_values]
                rows.append({
                    "page_path": dims[0] if dims else "",
                    "event_name": dims[1] if len(dims) > 1 else "",
                    "event_count": int(vals[0]) if vals else 0,
                    "conversions": int(float(vals[1])) if len(vals) > 1 else 0,
                })
            return rows
        except Exception as exc:
            self.logger.warning("GA4 fetch_conversions failed: %s", exc)
            return []
