"""Persistent memory of the growth loop. One JSON file, committed to the repo."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
MAX_OBSERVATION_DAYS = 180
MAX_RUNS = 120


def _empty() -> dict[str, Any]:
    return {
        "schema": SCHEMA_VERSION,
        "pages": {},          # path -> {kind, cluster, target_query, published_at, last_changed_at}
        "experiments": [],    # see open_experiment()
        "observations": {},   # iso date -> {path: {impressions, clicks, position, sessions, enquiries}}
        "priors": {},         # cluster -> {alpha, beta, pages, impressions, clicks, enquiries}
        "queries": {},        # query -> {impressions, clicks, position, page, first_seen, last_seen}
        "runs": [],           # compact per-run summaries
    }


class Ledger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.data = _empty()
        if self.path.exists():
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            self.data.update(loaded)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        days = sorted(self.data["observations"])
        for stale in days[:-MAX_OBSERVATION_DAYS]:
            del self.data["observations"][stale]
        self.data["runs"] = self.data["runs"][-MAX_RUNS:]
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # ── pages ──────────────────────────────────────────────────────────────
    def register_page(self, path: str, *, kind: str, cluster: str, target_query: str, today: date) -> None:
        entry = self.data["pages"].setdefault(path, {"published_at": today.isoformat()})
        entry.update({"kind": kind, "cluster": cluster, "target_query": target_query,
                      "last_changed_at": today.isoformat()})

    def days_since_change(self, path: str, today: date) -> int | None:
        entry = self.data["pages"].get(path)
        if not entry or not entry.get("last_changed_at"):
            return None
        return (today - date.fromisoformat(entry["last_changed_at"])).days

    # ── observations ───────────────────────────────────────────────────────
    def record_observations(self, day: date, per_page: dict[str, dict[str, float]]) -> None:
        if per_page:
            self.data["observations"][day.isoformat()] = per_page

    def latest_metrics(self, path: str) -> dict[str, float]:
        for day in sorted(self.data["observations"], reverse=True):
            if path in self.data["observations"][day]:
                return self.data["observations"][day][path]
        return {}

    # ── experiments ────────────────────────────────────────────────────────
    def open_experiment(self, *, kind: str, path: str, cluster: str, hypothesis: str,
                        today: date, baseline: dict[str, float] | None = None,
                        detail: dict[str, Any] | None = None) -> dict[str, Any]:
        experiment = {
            "id": f"{today.isoformat()}-{kind}-{path.strip('/').replace('/', '_') or 'home'}",
            "kind": kind,                 # new_page | refresh | snippet | foundation
            "path": path,
            "cluster": cluster,
            "hypothesis": hypothesis,
            "started_at": today.isoformat(),
            "baseline": baseline or {},
            "detail": detail or {},
            "checkpoints": [],
            "status": "open",             # open | won | lost | inconclusive
            "credited": False,            # whether the verdict has been folded into the priors
        }
        self.data["experiments"] = [e for e in self.data["experiments"] if e["id"] != experiment["id"]]
        self.data["experiments"].append(experiment)
        return experiment

    def open_experiments(self) -> list[dict[str, Any]]:
        return [e for e in self.data["experiments"] if e["status"] == "open"]

    def has_open_experiment(self, path: str) -> bool:
        return any(e["path"] == path for e in self.open_experiments())

    # ── runs ───────────────────────────────────────────────────────────────
    def record_run(self, summary: dict[str, Any]) -> None:
        summary = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **summary}
        self.data["runs"].append(summary)

    def previous_run(self) -> dict[str, Any]:
        return self.data["runs"][-1] if self.data["runs"] else {}
