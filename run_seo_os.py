from __future__ import annotations

"""
Entry point for the SEO OS Agent.
Run by daily_seo_os_run.yml in pipeleap-seo-workflows.

Pipeline:
  1. SEOOSAgent.run_once()      — 11-step autonomous execution
   2. repo_writer.write_all()    — structured /seo/ and /content/ outputs
"""

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

logger = logging.getLogger("run_seo_os")


def main() -> int:
    Path("outputs").mkdir(parents=True, exist_ok=True)
    Path("outputs/seo_os_state").mkdir(parents=True, exist_ok=True)

    # Initialise repo structure (idempotent)
    import scripts.init_repo_structure  # noqa

    from utils.config_loader import ConfigError, load_config
    config_path = "config.yaml"
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        logger.error("Config load failed: %s", exc)
        print(json.dumps({"error": str(exc)}, indent=2))
        return 1

    disable_crawl = "--disable-crawl" in sys.argv
    if disable_crawl:
        config["execution"]["crawl_enabled"] = False
        logger.info("Crawl disabled — using synthetic snapshot")

    # -- Step A: Run SEO OS (11 steps) -----------------------------------------
    from agents.seo_os_agent import SEOOSAgent
    agent = SEOOSAgent(config)
    result = agent.run_once()
    run_id = result.get("run_id", "unknown")

    # -- Step B: Write structured /seo/ and /content/ repo outputs ------------
    try:
        from core.repo_writer import write_all
        written = write_all(run_id=run_id, result=result, repo_root=".")
        logger.info("Repo writer: %d files written", len(written))
        result["repo_files_written"] = written
    except Exception as exc:
        logger.error("Repo writer failed: %s", exc)
        result.setdefault("errors", []).append(f"repo_writer: {exc}")
    print(json.dumps(result, indent=2, default=str))
    logger.info(
        "SEO OS complete — score=%d mode=%s repo=%d",
        result.get("seo_score", {}).get("overall", 0),
        result.get("mode", ""),
        len(result.get("repo_files_written", [])),
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
