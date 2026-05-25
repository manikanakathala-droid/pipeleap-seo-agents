from __future__ import annotations

"""
Entry point for the SERP Visibility Agent.
Run by daily_serp_run.yml in pipeleap-seo-workflows.
"""

import json
import logging
import sys
from pathlib import Path

from agents.serp_visibility_agent import SerpVisibilityAgent
from utils.config_loader import ConfigError, load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

logger = logging.getLogger("run_serp_visibility")


def main() -> int:
    Path("outputs").mkdir(parents=True, exist_ok=True)

    config_path = "config.yaml"
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        logger.error("Config load failed: %s", exc)
        print(json.dumps({"error": str(exc)}, indent=2))
        return 1

    dry_run = "--dry-run" in sys.argv
    if dry_run:
        logger.info("Dry-run mode — outputs will be written but not committed")

    agent = SerpVisibilityAgent(config)
    result = agent.run_once()

    print(json.dumps(result, indent=2, default=str))
    logger.info("SERP Visibility Agent complete — %d output files", len(result.get("output_files", [])))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
