from __future__ import annotations

"""
Dashboard Writer — Live SEO command centre data layer.

Reads agent outputs and writes three dashboard files to /dashboard/:

  summary.json      — daily metrics, SEO score, action totals, trend series
  activity-log.json — every action with full standard schema
  alerts.json       — critical issues + dev-review items

Every record written conforms to the mandatory standard schema:
  {
    "timestamp":   ISO-8601 string,
    "category":    "keywords" | "content" | "technical" | "linking" | "indexing" | "competitor" | "metadata",
    "action_type": "create" | "update" | "fix" | "suggest",
    "priority":    "high" | "medium" | "low",
    "status":      "pending" | "completed" | "requires_review",
    "impact_score": 1-10 integer
  }

Trend series structure (for charts):
  { "date": "YYYY-MM-DD", "value": int, "series": str }
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("dashboard_writer")

_REPO_ROOT: Path = Path(".")
_DASHBOARD_DIR: Path = Path("dashboard")

# Category map from agent action categories to dashboard categories
_CATEGORY_MAP: dict[str, str] = {
    "metadata":      "metadata",
    "indexing":      "indexing",
    "content":       "content",
    "linking":       "linking",
    "technical":     "technical",
    "canonical":     "technical",
    "robots":        "technical",
    "performance":   "technical",
    "redirect":      "technical",
    "schema":        "technical",
    "broken_page":   "technical",
    "keywords":      "keywords",
    "competitor":    "competitor",
}

_PRIORITY_MAP: dict[int, str] = {1: "high", 2: "medium", 3: "low"}

_IMPACT_MAP: dict[str, int] = {
    "high":    8,
    "medium":  5,
    "low":     3,
    "critical": 10,
    "warning": 6,
    "info":    3,
}


def configure(repo_root: str | Path) -> None:
    global _REPO_ROOT, _DASHBOARD_DIR
    _REPO_ROOT = Path(repo_root)
    _DASHBOARD_DIR = _REPO_ROOT / "dashboard"
    _DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    _init_dashboard_files()


def _init_dashboard_files() -> None:
    _init_json("dashboard/summary.json", {
        "last_updated": "",
        "current_score": 0,
        "score_history": [],
        "daily_metrics": [],
        "category_totals": {},
        "content_velocity": [],
        "keyword_growth": [],
        "technical_trend": [],
        "indexing_trend": [],
    })
    _init_json("dashboard/activity-log.json", [])
    _init_json("dashboard/alerts.json", {
        "last_updated": "",
        "active_alerts": [],
        "alert_history": [],
    })


def _init_json(rel_path: str, default: Any) -> None:
    path = _REPO_ROOT / rel_path
    if not path.exists():
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")


def _read_json(rel_path: str) -> Any:
    path = _REPO_ROOT / rel_path
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _write_json(rel_path: str, data: Any) -> None:
    (_REPO_ROOT / rel_path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _normalise_action(raw: dict, run_id: str) -> dict:
    """Convert any agent action dict to the mandatory standard schema."""
    category_raw = raw.get("category", "technical")
    category = _CATEGORY_MAP.get(category_raw, category_raw)

    priority_int = raw.get("priority", 2)
    if isinstance(priority_int, int):
        priority = _PRIORITY_MAP.get(priority_int, "medium")
    else:
        priority = str(priority_int).lower() if priority_int else "medium"
        if priority not in ("high", "medium", "low"):
            priority = "medium"

    requires_dev = raw.get("requires_dev", raw.get("requires_dev_review", False))
    status = "requires_review" if requires_dev else "pending"

    estimated_impact = raw.get("estimated_impact", raw.get("severity", "medium"))
    impact_score = _IMPACT_MAP.get(str(estimated_impact).lower(), 5)
    # Override: critical issues always score 9-10
    if requires_dev and category == "technical":
        impact_score = max(impact_score, 9)

    # Determine action_type from context
    title = (raw.get("title") or "").lower()
    if any(kw in title for kw in ["add", "create", "new", "publish", "generate"]):
        action_type = "create"
    elif any(kw in title for kw in ["fix", "broken", "error", "missing", "repair"]):
        action_type = "fix"
    elif any(kw in title for kw in ["update", "refresh", "change", "improve", "optimis"]):
        action_type = "update"
    else:
        action_type = "suggest"

    return {
        "id": f"{run_id}-{abs(hash(raw.get('page_url','') + raw.get('title',''))) % 100000:05d}",
        "run_id": run_id,
        "timestamp": raw.get("generated_at", _now_iso()),
        "category": category,
        "action_type": action_type,
        "priority": priority,
        "status": status,
        "impact_score": impact_score,
        "page_url": raw.get("page_url", raw.get("url", "")),
        "title": raw.get("title", ""),
        "description": raw.get("description", raw.get("action", "")),
        "requires_dev": requires_dev,
        "dev_note": raw.get("dev_note", ""),
        "safe_mode": raw.get("safe_mode", not requires_dev),
    }


# ── Activity Log ───────────────────────────────────────────────────────────────

def write_activity_log(run_id: str, result: dict) -> str:
    """
    Append every action from this run to /dashboard/activity-log.json
    Each entry has the full standard schema.
    """
    log: list[dict] = _read_json("dashboard/activity-log.json") or []
    timestamp = _now_iso()

    sources = [
        (result.get("safe_actions", []),      "safe"),
        (result.get("dev_review_items", []),   "dev_review"),
        (result.get("pages_optimized", []),    "metadata"),
        (result.get("indexing_actions", []),   "indexing"),
        (result.get("linking_suggestions", []), "linking"),
    ]

    new_entries: list[dict] = []
    for items, source_hint in sources:
        for raw in items:
            if not isinstance(raw, dict):
                continue
            entry = _normalise_action(raw, run_id)
            entry["source"] = source_hint
            entry["timestamp"] = timestamp
            new_entries.append(entry)

    # Content generated
    for item in result.get("content_generated", []):
        if not isinstance(item, dict):
            continue
        new_entries.append({
            "id": f"{run_id}-cnt-{item.get('slug','x')}",
            "run_id": run_id,
            "timestamp": timestamp,
            "category": "content",
            "action_type": "create",
            "priority": "high",
            "status": "pending",
            "impact_score": 7,
            "page_url": f"/blog/{item.get('slug', '')}",
            "title": f"Content draft: {item.get('title', item.get('slug', ''))}",
            "description": f"Type: {item.get('type','')} | Keyword: {item.get('target_keyword', '')}",
            "requires_dev": False,
            "dev_note": "",
            "safe_mode": True,
            "source": "content_engine",
        })

    # Keywords researched
    for kw in result.get("keyword_opportunities", []):
        if not isinstance(kw, dict):
            continue
        new_entries.append({
            "id": f"{run_id}-kw-{abs(hash(kw.get('keyword',''))) % 100000:05d}",
            "run_id": run_id,
            "timestamp": timestamp,
            "category": "keywords",
            "action_type": "suggest",
            "priority": "high" if kw.get("type") == "high_intent" else "medium",
            "status": "pending",
            "impact_score": 8 if kw.get("type") == "high_intent" else 5,
            "page_url": "",
            "title": f"Keyword: {kw.get('keyword', '')}",
            "description": f"Type: {kw.get('type','')} | Cluster: {kw.get('cluster', kw.get('gap_source',''))}",
            "requires_dev": False,
            "dev_note": "",
            "safe_mode": True,
            "source": "keyword_engine",
        })

    log.extend(new_entries)

    # Keep log bounded — retain last 2000 entries
    if len(log) > 2000:
        log = log[-2000:]

    _write_json("dashboard/activity-log.json", log)
    logger.info("Activity log: +%d entries, %d total", len(new_entries), len(log))
    return "dashboard/activity-log.json"


# ── Alerts ─────────────────────────────────────────────────────────────────────

def write_alerts(run_id: str, result: dict) -> str:
    """
    Write critical issues and dev-review items to /dashboard/alerts.json
    Active alerts are current unresolved issues.
    Alert history is appended indefinitely.
    """
    store: dict = _read_json("dashboard/alerts.json") or {"active_alerts": [], "alert_history": []}
    timestamp = _now_iso()
    today = _today()

    new_alerts: list[dict] = []

    # Dev-review items = alerts requiring human action
    for raw in result.get("dev_review_items", []):
        if not isinstance(raw, dict):
            continue
        new_alerts.append({
            "id": f"{run_id}-alert-{abs(hash(raw.get('page_url','') + raw.get('title',''))) % 100000:05d}",
            "run_id": run_id,
            "timestamp": timestamp,
            "date": today,
            "category": _CATEGORY_MAP.get(raw.get("category", "technical"), "technical"),
            "action_type": "fix",
            "priority": "high",
            "status": "requires_review",
            "impact_score": 9,
            "page_url": raw.get("page_url", raw.get("url", "")),
            "title": raw.get("title", ""),
            "description": raw.get("description", ""),
            "dev_note": raw.get("dev_note", "REQUIRES DEV REVIEW"),
            "resolved": False,
        })

    # Risks and missed opportunities
    for risk in result.get("risks_and_missed", []):
        if not isinstance(risk, dict):
            continue
        severity = risk.get("severity", "warning")
        new_alerts.append({
            "id": f"{run_id}-risk-{abs(hash(risk.get('type','') + risk.get('description',''))) % 100000:05d}",
            "run_id": run_id,
            "timestamp": timestamp,
            "date": today,
            "category": "technical",
            "action_type": "fix",
            "priority": "high" if severity == "critical" else "medium",
            "status": "requires_review" if severity == "critical" else "pending",
            "impact_score": _IMPACT_MAP.get(severity, 5),
            "page_url": (risk.get("urls") or [""])[0],
            "title": f"[{severity.upper()}] {risk.get('type', '').replace('_', ' ').title()}",
            "description": risk.get("description", ""),
            "dev_note": "",
            "affected_urls": risk.get("urls", []),
            "resolved": False,
        })

    # Merge active alerts — keep previous unresolved, replace if same run updates them
    existing_active = [a for a in store.get("active_alerts", []) if not a.get("resolved", False)]
    existing_ids = {a["id"] for a in existing_active}

    for alert in new_alerts:
        if alert["id"] not in existing_ids:
            existing_active.append(alert)

    store["active_alerts"] = existing_active
    store["alert_history"].extend(new_alerts)
    store["last_updated"] = timestamp

    # Keep history bounded
    if len(store["alert_history"]) > 500:
        store["alert_history"] = store["alert_history"][-500:]

    _write_json("dashboard/alerts.json", store)
    logger.info("Alerts: %d active, +%d new", len(existing_active), len(new_alerts))
    return "dashboard/alerts.json"


# ── Summary ────────────────────────────────────────────────────────────────────

def write_summary(run_id: str, result: dict) -> str:
    """
    Update /dashboard/summary.json with today's metrics and trend series.

    Trend series power:
      score_history      → SEO score line chart (daily)
      daily_metrics      → action count bar chart (daily, by category)
      content_velocity   → content pieces created per day
      keyword_growth     → keywords discovered per day
      technical_trend    → technical issues per day
      indexing_trend     → indexing actions per day
    """
    summary: dict = _read_json("dashboard/summary.json") or {}
    timestamp = _now_iso()
    today = _today()
    score = result.get("seo_score", {})
    overall = score.get("overall", 0)

    # Count actions by category for today
    log: list[dict] = _read_json("dashboard/activity-log.json") or []
    today_entries = [e for e in log if e.get("timestamp", "").startswith(today)]

    category_counts: dict[str, int] = {}
    for entry in today_entries:
        cat = entry.get("category", "other")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    total_actions = len(today_entries)
    alerts_store: dict = _read_json("dashboard/alerts.json") or {}
    active_alerts = len(alerts_store.get("active_alerts", []))

    # ── Score history (daily point) ───────────────────────────────────────
    score_history: list[dict] = summary.get("score_history", [])
    existing_today_score = next((s for s in score_history if s.get("date") == today), None)
    score_point = {
        "date": today,
        "value": overall,
        "technical": score.get("technical", 0),
        "content": score.get("content", 0),
        "indexing": score.get("indexing", 0),
        "authority": score.get("authority", 0),
        "run_id": run_id,
    }
    if existing_today_score:
        score_history[score_history.index(existing_today_score)] = score_point
    else:
        score_history.append(score_point)
    score_history = score_history[-90:]  # 90-day window

    # ── Daily metrics (action counts per category per day) ────────────────
    daily_metrics: list[dict] = summary.get("daily_metrics", [])
    existing_today_metrics = next((d for d in daily_metrics if d.get("date") == today), None)
    day_metrics = {
        "date": today,
        "run_id": run_id,
        "total_actions": total_actions,
        "active_alerts": active_alerts,
        "categories": category_counts,
        "safe_actions": len(result.get("safe_actions", [])),
        "dev_review": len(result.get("dev_review_items", [])),
        "mode": result.get("mode", ""),
    }
    if existing_today_metrics:
        daily_metrics[daily_metrics.index(existing_today_metrics)] = day_metrics
    else:
        daily_metrics.append(day_metrics)
    daily_metrics = daily_metrics[-90:]

    # ── Content velocity (pieces per day) ─────────────────────────────────
    content_velocity: list[dict] = summary.get("content_velocity", [])
    content_today = len(result.get("content_generated", []))
    existing_cv = next((c for c in content_velocity if c.get("date") == today), None)
    cv_point = {"date": today, "value": content_today, "series": "content_pieces", "run_id": run_id}
    if existing_cv:
        content_velocity[content_velocity.index(existing_cv)] = cv_point
    else:
        content_velocity.append(cv_point)
    content_velocity = content_velocity[-90:]

    # ── Keyword growth (keywords discovered per day) ───────────────────────
    keyword_growth: list[dict] = summary.get("keyword_growth", [])
    kw_today = len(result.get("keyword_opportunities", []))
    existing_kg = next((k for k in keyword_growth if k.get("date") == today), None)
    kg_point = {"date": today, "value": kw_today, "series": "keywords_discovered", "run_id": run_id}
    if existing_kg:
        keyword_growth[keyword_growth.index(existing_kg)] = kg_point
    else:
        keyword_growth.append(kg_point)
    keyword_growth = keyword_growth[-90:]

    # ── Technical issue trend ─────────────────────────────────────────────
    technical_trend: list[dict] = summary.get("technical_trend", [])
    tech_today = category_counts.get("technical", 0)
    existing_tt = next((t for t in technical_trend if t.get("date") == today), None)
    tt_point = {"date": today, "value": tech_today, "series": "technical_issues", "run_id": run_id}
    if existing_tt:
        technical_trend[technical_trend.index(existing_tt)] = tt_point
    else:
        technical_trend.append(tt_point)
    technical_trend = technical_trend[-90:]

    # ── Indexing trend ────────────────────────────────────────────────────
    indexing_trend: list[dict] = summary.get("indexing_trend", [])
    idx_today = len(result.get("indexing_actions", []))
    existing_it = next((i for i in indexing_trend if i.get("date") == today), None)
    it_point = {"date": today, "value": idx_today, "series": "indexing_actions", "run_id": run_id}
    if existing_it:
        indexing_trend[indexing_trend.index(existing_it)] = it_point
    else:
        indexing_trend.append(it_point)
    indexing_trend = indexing_trend[-90:]

    # ── Assemble final summary ────────────────────────────────────────────
    updated_summary = {
        "last_updated": timestamp,
        "current_run_id": run_id,

        # Live scoreboard
        "current_score": overall,
        "current_score_breakdown": {
            "technical": score.get("technical", 0),
            "content": score.get("content", 0),
            "indexing": score.get("indexing", 0),
            "authority": score.get("authority", 0),
        },

        # Today's snapshot
        "today": {
            "date": today,
            "total_actions": total_actions,
            "safe_actions": len(result.get("safe_actions", [])),
            "dev_review_items": len(result.get("dev_review_items", [])),
            "content_pieces": content_today,
            "keywords_found": kw_today,
            "indexing_actions": idx_today,
            "active_alerts": active_alerts,
            "mode": result.get("mode", ""),
            "pages_total": result.get("website_changes", {}).get("total_pages", 0),
            "pages_new": result.get("website_changes", {}).get("new_pages", 0),
            "pages_updated": result.get("website_changes", {}).get("updated_pages", 0),
            "broken_pages": result.get("website_changes", {}).get("broken_links", 0),
            "orphan_pages": result.get("website_changes", {}).get("orphan_pages", 0),
        },

        # Category totals (all-time)
        "category_totals": _merge_category_totals(
            summary.get("category_totals", {}), category_counts
        ),

        # Trend series — 90-day rolling windows
        "score_history": score_history,
        "daily_metrics": daily_metrics,
        "content_velocity": content_velocity,
        "keyword_growth": keyword_growth,
        "technical_trend": technical_trend,
        "indexing_trend": indexing_trend,

        # Metadata
        "next_day_plan": result.get("next_day_plan", []),
        "errors": result.get("errors", []),
    }

    _write_json("dashboard/summary.json", updated_summary)
    logger.info("Summary written: score=%d actions=%d alerts=%d", overall, total_actions, active_alerts)
    return "dashboard/summary.json"


def _merge_category_totals(existing: dict, today_counts: dict) -> dict:
    merged = dict(existing)
    for cat, count in today_counts.items():
        merged[cat] = merged.get(cat, 0) + count
    return merged


# ── Master orchestrator ────────────────────────────────────────────────────────

def write_dashboard(run_id: str, result: dict, repo_root: str | Path = ".") -> list[str]:
    """
    Single call — writes all three dashboard files.
    Call this after repo_writer.write_all() in run_seo_os.py.
    Returns list of relative paths written.
    """
    configure(repo_root)
    written: list[str] = []

    try:
        written.append(write_activity_log(run_id, result))
    except Exception as exc:
        logger.error("Activity log failed: %s", exc)

    try:
        written.append(write_alerts(run_id, result))
    except Exception as exc:
        logger.error("Alerts failed: %s", exc)

    try:
        written.append(write_summary(run_id, result))
    except Exception as exc:
        logger.error("Summary failed: %s", exc)

    logger.info("Dashboard write complete: %d files for run %s", len(written), run_id)
    return written
