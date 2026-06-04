from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

try:  # pragma: no cover
    from google.oauth2 import service_account  # type: ignore
    from googleapiclient.discovery import build  # type: ignore
    import google.auth as _google_auth  # type: ignore
    GOOGLE_LIBS_AVAILABLE = True
except Exception:  # pragma: no cover
    service_account = None
    build = None
    _google_auth = None  # type: ignore
    GOOGLE_LIBS_AVAILABLE = False

# Scope notes:
#   webmasters.readonly  — analytics queries only
#   webmasters            — read + write (required for sitemap submission and URL inspection)
#   indexing              — Google Indexing API (requires API to be enabled in GCP Console at
#                           https://console.developers.google.com/apis/api/indexing.googleapis.com/)
_GSC_SCOPES          = ["https://www.googleapis.com/auth/webmasters"]
_GSC_READONLY_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
_INDEXING_SCOPES     = ["https://www.googleapis.com/auth/indexing"]


class GoogleSearchConsoleConnector:
    """
    Fetches Search Console data and drives indexing signals for Pipeleap.

    Capabilities:
    - fetch_query_data()      : search analytics (queries, pages, CTR, position)
    - submit_sitemap()        : submit sitemap.xml to GSC
    - fetch_coverage()        : index coverage stats (indexed, not indexed, excluded)
    - request_indexing()      : request URL indexing via the Indexing API (new/updated pages)
    - fetch_crawl_errors()    : crawl errors and URL inspection results
    """

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.logger = logger
        self.config = config.get("integrations", {}).get("gsc", {})
        self.site_url = (
            self.config.get("site_url")
            or config.get("site", {}).get("site_url", "")
            or os.getenv("GSC_SITE_URL", "")
        )
        self.plain_site_url = (
            config.get("site", {}).get("site_url", "")
            or os.getenv("GSC_SITE_URL", "")
        ).rstrip("/")
        self.credentials_path = self.config.get("credentials_path", "")
        self.data_export_path = self.config.get("data_export_path", "")

    def _get_credentials(self, scopes: list[str]):
        """
        Credential resolution order:
        1. GSC_SERVICE_ACCOUNT_JSON env var (JSON string — used in CI/CD via GitHub Actions secret)
        2. Service account key file at credentials_path
        3. Application Default Credentials (ADC) — after: gcloud auth application-default login
        """
        sa_json = os.getenv("GSC_SERVICE_ACCOUNT_JSON", "")
        if sa_json:
            info = json.loads(sa_json)
            return service_account.Credentials.from_service_account_info(info, scopes=scopes)
        if self.credentials_path and Path(self.credentials_path).exists():
            return service_account.Credentials.from_service_account_file(
                self.credentials_path, scopes=scopes
            )
        if _google_auth is not None:
            creds, _ = _google_auth.default(scopes=scopes)
            return creds
        raise RuntimeError(
            "No credentials available. Set GSC_SERVICE_ACCOUNT_JSON, place a key file at "
            f"{self.credentials_path!r}, or run: gcloud auth application-default login"
        )

    def _is_auth_available(self) -> bool:
        if not GOOGLE_LIBS_AVAILABLE:
            return False
        if os.getenv("GSC_SERVICE_ACCOUNT_JSON"):
            return True
        if self.credentials_path and Path(self.credentials_path).exists():
            return True
        try:
            _google_auth.default()
            return True
        except Exception:
            return False

    def fetch_query_data(
        self,
        start_date: str,
        end_date: str,
        row_limit: int = 250,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        if self.data_export_path and Path(self.data_export_path).exists():
            rows = self._load_export(Path(self.data_export_path))
            return rows[:row_limit], []

        if self._is_auth_available():
            self.logger.info("Connecting to GSC API (key file: %s, ADC fallback available)",
                             bool(self.credentials_path))
            try:
                return self._fetch_from_api(start_date, end_date, row_limit), []
            except Exception as exc:
                message = f"GSC API request failed: {exc}"
                self.logger.warning(message)
                return [], [message]
        else:
            self.logger.info("GSC API conditions not met: creds=%s, sa=%s, build=%s", 
                             self.credentials_path, service_account is not None, build is not None)

        requests = [
            "Connect Google Search Console via a service account or provide a local export file "
            "at integrations.gsc.data_export_path for live query, CTR, and position data."
        ]
        return [], requests

    def _load_export(self, path: Path) -> list[dict[str, Any]]:
        self.logger.info("Loading Search Console export from %s", path)
        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return [self._normalize_row(row) for row in payload if isinstance(row, dict)]
            if isinstance(payload, dict):
                rows = payload.get("rows", [])
                if isinstance(rows, list):
                    return [self._normalize_row(row) for row in rows if isinstance(row, dict)]
            return []

        if path.suffix.lower() == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                return [self._normalize_row(row) for row in reader]

        raise ValueError(f"Unsupported GSC export format: {path.suffix}")

    # ── Sitemap submission ────────────────────────────────────────────────────

    def submit_sitemap(self, sitemap_url: str | None = None) -> dict[str, Any]:
        """Submit sitemap to GSC. Works with key file or ADC."""
        if not self._is_auth_available():
            return {"ok": False, "error": "no credentials — run: gcloud auth application-default login"}
        url = sitemap_url or f"{self.plain_site_url}/sitemap.xml"
        try:
            credentials = self._get_credentials(_GSC_SCOPES)
            service = build("searchconsole", "v1", credentials=credentials, cache_discovery=True)
            service.sitemaps().submit(siteUrl=self.site_url, feedpath=url).execute()
            self.logger.info("Sitemap submitted to GSC: %s", url)
            return {"ok": True, "sitemap_url": url}
        except json.JSONDecodeError:
            self.logger.warning("GSC sitemap submission failed: JSON decode error (empty API response)")
            return {"ok": False, "error": "GSC API returned empty response"}
        except Exception as exc:
            self.logger.warning("GSC sitemap submission failed: %s", exc)
            return {"ok": False, "error": str(exc)}

    # ── Index coverage ────────────────────────────────────────────────────────

    def fetch_coverage(self) -> dict[str, Any]:
        """Returns index coverage via URL Inspection API."""
        if not self._is_auth_available():
            return {"ok": False, "error": "no credentials"}
        try:
            credentials = self._get_credentials(_GSC_SCOPES)
            service = build("searchconsole", "v1", credentials=credentials, cache_discovery=True)
            result = (
                service.urlInspection()
                .index()
                .inspect(body={"inspectionUrl": self.plain_site_url, "siteUrl": self.site_url})
                .execute()
            )
            return {"ok": True, "inspection": result}
        except Exception as exc:
            self.logger.warning("GSC coverage fetch failed: %s", exc)
            return {"ok": False, "error": str(exc)}

    # ── Indexing API — request indexing for new / updated pages ──────────────

    def request_indexing(self, page_urls: list[str]) -> list[dict[str, Any]]:
        """Signal new/updated URLs via the Google Indexing API. Works with key file or ADC."""
        if not self._is_auth_available():
            return [{"url": u, "ok": False, "error": "no credentials"} for u in page_urls]
        results: list[dict[str, Any]] = []
        try:
            credentials = self._get_credentials(_INDEXING_SCOPES)
            service = build("indexing", "v3", credentials=credentials, cache_discovery=True)
            for url in page_urls:
                try:
                    resp = service.urlNotifications().publish(
                        body={"url": url, "type": "URL_UPDATED"}
                    ).execute()
                    results.append({"url": url, "ok": True, "response": resp})
                    self.logger.info("Indexing API: requested %s", url)
                except Exception as exc:
                    self.logger.warning("Indexing API failed for %s: %s", url, exc)
                    results.append({"url": url, "ok": False, "error": str(exc)})
        except Exception as exc:
            self.logger.warning("Indexing API setup failed: %s", exc)
            return [{"url": u, "ok": False, "error": str(exc)} for u in page_urls]
        return results

    # ── URL Inspection ────────────────────────────────────────────────────────

    def inspect_url(self, page_url: str) -> dict[str, Any]:
        """Run URL Inspection for a single page. Works with key file or ADC."""
        if not self._is_auth_available():
            return {"ok": False, "error": "no credentials"}
        try:
            credentials = self._get_credentials(_GSC_SCOPES)
            service = build("searchconsole", "v1", credentials=credentials, cache_discovery=True)
            result = (
                service.urlInspection()
                .index()
                .inspect(body={"inspectionUrl": page_url, "siteUrl": self.site_url})
                .execute()
            )
            verdict = result.get("inspectionResult", {}).get("indexStatusResult", {})
            self.logger.info(
                "URL inspection %s → coverageState=%s indexState=%s",
                page_url,
                verdict.get("coverageState", "unknown"),
                verdict.get("indexingState", "unknown"),
            )
            return {"ok": True, "url": page_url, "result": result}
        except Exception as exc:
            self.logger.warning("URL inspection failed for %s: %s", page_url, exc)
            return {"ok": False, "url": page_url, "error": str(exc)}

    # ── Performance data with extended dimensions ─────────────────────────────

    def fetch_page_performance(
        self, start_date: str, end_date: str, row_limit: int = 500
    ) -> list[dict[str, Any]]:
        """Fetch page-level performance (impressions, clicks, position) without query dimension."""
        if not self._is_auth_available():
            return []
        try:
            credentials = self._get_credentials(_GSC_SCOPES)
            service = build("searchconsole", "v1", credentials=credentials, cache_discovery=True)
            response = (
                service.searchanalytics()
                .query(
                    siteUrl=self.site_url,
                    body={
                        "startDate": start_date,
                        "endDate": end_date,
                        "dimensions": ["page"],
                        "rowLimit": row_limit,
                        "dataState": "all",
                    },
                )
                .execute()
            )
            rows = []
            for row in response.get("rows", []):
                keys = row.get("keys", [])
                rows.append({
                    "page": keys[0] if keys else "",
                    "clicks": row.get("clicks", 0),
                    "impressions": row.get("impressions", 0),
                    "ctr": row.get("ctr", 0.0),
                    "position": row.get("position", 0.0),
                })
            return rows
        except Exception as exc:
            self.logger.warning("GSC page performance fetch failed: %s", exc)
            return []

    # ── Decay detection: fetch two periods and compare ────────────────────────

    def fetch_two_periods(
        self, days_per_period: int = 28, row_limit: int = 500
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Fetch two consecutive GSC periods for decay comparison.

        Returns (current_rows, previous_rows) where:
          current  = last `days_per_period` days
          previous = the `days_per_period` days before that

        Both share the same dimensions (query, page) so they can be compared.
        """
        from datetime import timedelta, date as _date

        today = _date.today()
        current_end   = (today - timedelta(days=1)).isoformat()
        current_start = (today - timedelta(days=days_per_period)).isoformat()
        previous_end  = (today - timedelta(days=days_per_period + 1)).isoformat()
        previous_start= (today - timedelta(days=days_per_period * 2)).isoformat()

        self.logger.info(
            "Fetching GSC decay periods: current=%s–%s, previous=%s–%s",
            current_start, current_end, previous_start, previous_end,
        )

        current_rows, _ = self.fetch_query_data(current_start, current_end, row_limit)
        previous_rows, _ = self.fetch_query_data(previous_start, previous_end, row_limit)

        return current_rows, previous_rows

    def save_gsc_periods(
        self, output_dir: str, days_per_period: int = 28
    ) -> dict[str, Any]:
        """
        Fetch two GSC periods and save them to disk for the decay detector.
        Files: {output_dir}/gsc_current_period.json, gsc_previous_period.json
        """
        import os

        current, previous = self.fetch_two_periods(days_per_period)
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        (out / "gsc_current_period.json").write_text(
            json.dumps(current, indent=2), encoding="utf-8"
        )
        (out / "gsc_previous_period.json").write_text(
            json.dumps(previous, indent=2), encoding="utf-8"
        )
        self.logger.info(
            "GSC periods saved: current=%d rows, previous=%d rows",
            len(current), len(previous)
        )
        return {"current_rows": len(current), "previous_rows": len(previous)}

    def _fetch_from_api(self, start_date: str, end_date: str, row_limit: int) -> list[dict[str, Any]]:
        credentials = self._get_credentials(_GSC_READONLY_SCOPES)
        service = build("searchconsole", "v1", credentials=credentials, cache_discovery=True)  # type: ignore[misc]
        request = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["query", "page"],
            "rowLimit": row_limit,
        }
        response = (
            service.searchanalytics()  # type: ignore[union-attr]
            .query(siteUrl=self.site_url, body=request)
            .execute()
        )
        rows = []
        for row in response.get("rows", []):
            keys = row.get("keys", [])
            rows.append(
                {
                    "query": keys[0] if len(keys) > 0 else "",
                    "page": keys[1] if len(keys) > 1 else "",
                    "clicks": row.get("clicks", 0),
                    "impressions": row.get("impressions", 0),
                    "ctr": row.get("ctr", 0.0),
                    "position": row.get("position", 0.0),
                }
            )
        return rows

    @staticmethod
    def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
        query = row.get("query") or row.get("keyword") or ""
        return {
            "query": str(query).strip(),
            "page": str(row.get("page", "")).strip(),
            "clicks": int(float(row.get("clicks", 0) or 0)),
            "impressions": int(float(row.get("impressions", 0) or 0)),
            "ctr": float(row.get("ctr", 0) or 0.0),
            "position": float(row.get("position", 0) or 0.0),
        }
