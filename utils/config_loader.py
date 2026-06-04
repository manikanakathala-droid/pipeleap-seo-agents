from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any


ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")
WINDOWS_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")


class ConfigError(RuntimeError):
    """Raised when the runtime configuration cannot be loaded."""


DEFAULT_CONFIG: dict[str, Any] = {
    "site": {
        "brand": "Pipeleap",
        "site_url": "https://pipeleap.com",
        "domain": "pipeleap.com",
        "cta": {
            "primary_label": "Book a demo",
            "secondary_label": "See how it works",
            "primary_url": "https://pipeleap.com/",
            "secondary_url": "https://pipeleap.com/",
        },
        "target_personas": [
            "Founders",
            "RevOps teams",
            "Growth marketers",
            "SaaS companies",
            "Outbound agencies",
        ],
        "core_features": [
            "n8n-based workflow automation",
            "outbound sequencing",
            "lead enrichment pipelines",
            "CRM automation",
            "revenue automation playbooks",
        ],
    },
    "execution": {
        "crawl_enabled": True,
        "max_pages": 25,
        "max_depth": 2,
        "landing_pages_per_run": 5,
        "blog_posts_per_run": 4,
        "comparison_pages_per_run": 2,
        "use_case_pages_per_run": 2,
        "case_studies_per_run": 0,
        "output_dir": "outputs",
        "memory_db": "outputs/pipeleap_seo_memory.sqlite",
        "log_level": "INFO",
    },
    "schedule": {"continuous": False, "interval_minutes": 1440},
    "integrations": {
        "gsc": {"site_url": "", "credentials_path": "", "data_export_path": ""},
        "analytics": {"conversion_export_path": ""},
        "cms": {"mode": "filesystem", "publish_dir": "published", "webhook_url": ""},
        "pagespeed": {"api_key": ""},
    },
    "seo": {
        "allow_estimated_keyword_metrics": True,
        "seed_keywords": {},
        "topic_map": {},
        "semantic_expansions": {},
        "conversion_pages": [],
        "competitors": [],
        "keyword_overrides": {},
    },
    "backlinks": {"prospect_seeds": []},
}


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return ENV_PATTERN.sub(lambda match: os.getenv(match.group(1), ""), value)
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    return value


def _deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _normalize_runtime_paths(config: dict[str, Any], config_dir: Path) -> None:
    """Resolve file publish paths relative to the checked-out agent directory."""
    cms_config = config.get("integrations", {}).get("cms", {})
    publish_dir = cms_config.get("publish_dir", "")
    if not publish_dir:
        return

    launchpad_override = os.getenv("PIPELEAP_LAUNCHPAD_DIR")
    if launchpad_override:
        cms_config["publish_dir"] = str((Path(launchpad_override) / "src" / "data" / "seo").resolve())
        return

    local_launchpad_dir = config_dir / "pipeleap-launchpad"
    sibling_launchpad_dir = config_dir.parent / "pipeleap-launchpad"

    publish_text = str(publish_dir)
    if WINDOWS_ABSOLUTE_PATTERN.match(publish_text):
        launchpad_dir = local_launchpad_dir if local_launchpad_dir.exists() else sibling_launchpad_dir
        cms_config["publish_dir"] = str((launchpad_dir / "src" / "data" / "seo").resolve())
        return

    publish_path = Path(publish_text)
    if not publish_path.is_absolute():
        resolved = config_dir / publish_path
        if publish_text.startswith("pipeleap-launchpad/") and not local_launchpad_dir.exists():
            resolved = config_dir.parent / publish_path
        cms_config["publish_dir"] = str(resolved.resolve())


def load_config(config_path: str | os.PathLike[str]) -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    raw_text = path.read_text(encoding="utf-8")
    data: dict[str, Any] | None = None

    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(raw_text)
        if isinstance(loaded, dict):
            data = loaded
    except ModuleNotFoundError:
        data = None
    except Exception as exc:  # pragma: no cover
        raise ConfigError(f"Failed to parse YAML config: {exc}") from exc

    if data is None:
        try:
            loaded_json = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ConfigError(
                "PyYAML is not installed and config.yaml is not valid JSON/YAML subset."
            ) from exc
        if not isinstance(loaded_json, dict):
            raise ConfigError("Configuration root must be a mapping/object.")
        data = loaded_json

    merged = _deep_merge(DEFAULT_CONFIG, _expand_env(data))
    if not merged["site"].get("site_url"):
        raise ConfigError("site.site_url is required.")
    _normalize_runtime_paths(merged, path.resolve().parent)
    return merged
