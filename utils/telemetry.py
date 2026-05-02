"""
Agent telemetry — PostHog events + Sentry error tracking.

PostHog tracks agent execution health:
  - agent_run_started / agent_run_complete / agent_run_failed
  - agent_stage_complete (per pipeline stage with duration_ms)
  - asset_generated (quality score, word count, page type)
  - decay_detected (keyword, severity, position delta)
  - agent_error (exception type + message)

Sentry captures full exception stack traces with run context.

Graceful degradation: all methods are safe no-ops when:
  - posthog / sentry-sdk packages are not installed
  - POSTHOG_API_KEY / SENTRY_DSN are not set

Configuration (environment variables take precedence over config.yaml):
  POSTHOG_API_KEY   — PostHog project API key
  POSTHOG_HOST      — PostHog host (default: https://us.i.posthog.com)
  SENTRY_DSN        — Sentry project DSN

Setup:
  pip install posthog sentry-sdk
  export POSTHOG_API_KEY=phc_...
  export SENTRY_DSN=https://...@sentry.io/...
"""
from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Any, Generator

# PostHog — optional dependency
try:
    import posthog as _posthog  # type: ignore
    _POSTHOG_AVAILABLE = True
except ImportError:
    _posthog = None  # type: ignore
    _POSTHOG_AVAILABLE = False

# Sentry — optional dependency
try:
    import sentry_sdk as _sentry  # type: ignore
    _SENTRY_AVAILABLE = True
except ImportError:
    _sentry = None  # type: ignore
    _SENTRY_AVAILABLE = False


class Telemetry:
    """
    Unified telemetry client for all Pipeleap SEO agents.

    Instantiate once per process in the orchestrator __init__:
        self.telemetry = Telemetry(config)

    All public methods are safe to call regardless of whether the SDKs
    are installed or the keys are configured.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        tel_cfg = config.get("telemetry", {})
        self._distinct_id = config.get("site", {}).get("domain", "pipeleap.com")
        self._environment = tel_cfg.get("environment", "production")

        # ── PostHog setup ─────────────────────────────────────────────────
        ph_key = (
            tel_cfg.get("posthog_api_key")
            or os.environ.get("POSTHOG_API_KEY", "")
        )
        ph_host = (
            tel_cfg.get("posthog_host")
            or os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com")
        )
        self._ph_enabled = bool(ph_key and _POSTHOG_AVAILABLE)
        if self._ph_enabled and _posthog:
            _posthog.project_api_key = ph_key
            _posthog.host = ph_host
            _posthog.debug = False
            _posthog.disabled = False

        # ── Sentry setup ──────────────────────────────────────────────────
        sentry_dsn = (
            tel_cfg.get("sentry_dsn")
            or os.environ.get("SENTRY_DSN", "")
        )
        self._sentry_enabled = bool(sentry_dsn and _SENTRY_AVAILABLE)
        if self._sentry_enabled and _sentry:
            _sentry.init(
                dsn=sentry_dsn,
                traces_sample_rate=0.05,
                environment=self._environment,
                release=tel_cfg.get("release", ""),
            )

        # Run-level start time registry for duration calculation
        self._run_start: dict[str, float] = {}

    # ── Run lifecycle ─────────────────────────────────────────────────────────

    def run_start(self, run_id: str, agent_type: str = "seo_agent") -> None:
        """Call at the very beginning of a run."""
        self._run_start[run_id] = time.monotonic()
        self._capture("agent_run_started", {
            "run_id": run_id,
            "agent_type": agent_type,
            "environment": self._environment,
        })

    def run_complete(
        self,
        run_id: str,
        analytics_summary: dict[str, Any],
        assets: list[Any],
        audit_issues: list[Any],
        backlink_opportunities: list[Any],
    ) -> None:
        """Call at the end of a successful run."""
        duration_ms = self._pop_duration(run_id)
        kw_diff = analytics_summary.get("keyword_diff", {})
        decay = analytics_summary.get("decay_signals", [])

        self._capture("agent_run_complete", {
            "run_id": run_id,
            "duration_ms": duration_ms,
            "assets_generated": len(assets),
            "assets_passed_quality_gate": sum(
                1 for a in assets
                if getattr(a, "uniqueness_score", 1.0) > 0.0
            ),
            "clicks": analytics_summary.get("clicks", 0),
            "impressions": analytics_summary.get("impressions", 0),
            "avg_ctr": round(analytics_summary.get("ctr", 0.0), 4),
            "avg_position": analytics_summary.get("average_position"),
            "keywords_ranking": (
                analytics_summary.get("organic_keyword_history", [{}])[0].get("total_ranking", 0)
                if analytics_summary.get("organic_keyword_history") else 0
            ),
            "new_keywords": kw_diff.get("new", 0),
            "lost_keywords": kw_diff.get("lost", 0),
            "gained_5plus_positions": analytics_summary.get("gained_5plus_positions", 0),
            "lost_5plus_positions": analytics_summary.get("lost_5plus_positions", 0),
            "decay_signals": len(decay),
            "critical_decay": sum(1 for d in decay if d.get("severity") == "critical"),
            "audit_issues": len(audit_issues),
            "audit_critical": sum(1 for i in audit_issues if getattr(i, "severity", "") == "Critical"),
            "backlinks_queued": len(backlink_opportunities),
            "rising_queries": len(analytics_summary.get("rising_queries", [])),
            "low_ctr_queries": len(analytics_summary.get("low_ctr_queries", [])),
        })

        # Emit individual decay events for alert-level monitoring
        for signal in decay:
            if signal.get("severity") == "critical":
                self._capture("decay_detected", {
                    "run_id": run_id,
                    "keyword": signal.get("keyword", ""),
                    "severity": signal.get("severity", ""),
                    "position_delta": signal.get("position_delta", 0),
                    "current_position": signal.get("current_position"),
                    "previous_position": signal.get("previous_position"),
                })

    def run_failed(self, run_id: str, error: str, stage: str = "") -> None:
        """Call when a run exits with an unrecoverable error."""
        duration_ms = self._pop_duration(run_id)
        self._capture("agent_run_failed", {
            "run_id": run_id,
            "duration_ms": duration_ms,
            "error": error[:500],
            "stage": stage,
        })

    # ── Stage timing ──────────────────────────────────────────────────────────

    @contextmanager
    def timed_stage(
        self, stage_name: str, run_id: str = ""
    ) -> Generator[None, None, None]:
        """
        Context manager that emits agent_stage_complete with duration_ms.

        Usage:
            with self.telemetry.timed_stage("crawl", run_id):
                crawl_report = self._crawl_site()

        Exceptions propagate normally — the outer try/except still handles them.
        The stage is marked success=False if an exception is raised.
        """
        t0 = time.monotonic()
        success = True
        error_msg = ""
        try:
            yield
        except Exception as exc:
            success = False
            error_msg = str(exc)[:300]
            raise
        finally:
            self._capture("agent_stage_complete", {
                "run_id": run_id,
                "stage_name": stage_name,
                "duration_ms": int((time.monotonic() - t0) * 1000),
                "success": success,
                "error": error_msg,
            })

    # ── Asset events ──────────────────────────────────────────────────────────

    def track_assets(self, run_id: str, assets: list[Any]) -> None:
        """Emit one asset_generated event per asset (batched)."""
        for asset in assets:
            slug = getattr(asset, "slug", "")
            page_type = getattr(asset, "page_type", "")
            score = getattr(asset, "uniqueness_score", 1.0)
            word_count = len(getattr(asset, "body_markdown", "").split())
            self._capture("asset_generated", {
                "run_id": run_id,
                "slug": slug,
                "page_type": page_type,
                "quality_score": round(score, 2),
                "word_count": word_count,
                "passed_gate": score > 0.0,
            })

    # ── Error capture ─────────────────────────────────────────────────────────

    def capture_exception(
        self,
        exc: Exception,
        run_id: str = "",
        stage: str = "",
    ) -> None:
        """Send exception to Sentry and log it as a PostHog error event."""
        if self._sentry_enabled and _sentry:
            try:
                with _sentry.new_scope() as scope:
                    scope.set_extra("run_id", run_id)
                    scope.set_extra("stage", stage)
                    _sentry.capture_exception(exc)
            except Exception:
                pass

        self._capture("agent_error", {
            "run_id": run_id,
            "stage": stage,
            "error_type": type(exc).__name__,
            "error_message": str(exc)[:500],
        })

    # ── Flush ─────────────────────────────────────────────────────────────────

    def flush(self) -> None:
        """Flush PostHog event queue. Call before process exit."""
        if self._ph_enabled and _posthog:
            try:
                _posthog.flush()
            except Exception:
                pass

    # ── Internals ─────────────────────────────────────────────────────────────

    def _capture(self, event: str, properties: dict[str, Any]) -> None:
        if not self._ph_enabled or not _posthog:
            return
        try:
            _posthog.capture(
                self._distinct_id,
                event,
                {**properties, "environment": self._environment},
            )
        except Exception:
            pass  # telemetry must never crash the agent

    def _pop_duration(self, run_id: str) -> int:
        start = self._run_start.pop(run_id, None)
        return int((time.monotonic() - start) * 1000) if start else 0


# Singleton no-op for use when telemetry is not initialised
class _NoOpTelemetry(Telemetry):
    """Zero-config Telemetry that never calls any external service."""

    def __init__(self) -> None:  # type: ignore[override]
        self._ph_enabled = False
        self._sentry_enabled = False
        self._run_start: dict[str, float] = {}
        self._distinct_id = ""
        self._environment = "production"


NOOP = _NoOpTelemetry()
