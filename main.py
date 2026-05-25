from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agents.seo_orchestrator import SEOOrchestrator
from utils.config_loader import ConfigError, load_config


def main() -> int:
    # Ensure outputs directory exists immediately
    Path("outputs").mkdir(parents=True, exist_ok=True)
    Path("outputs/post_publish").mkdir(parents=True, exist_ok=True)
    
    # Write a heartbeat file so artifacts never fail
    Path("outputs/.heartbeat").write_text(json.dumps({"started_at": sys.version}), encoding="utf-8")

    config_path = "config.yaml"
    mode = "once"
    disable_crawl = False
    if "--disable-crawl" in sys.argv:
        disable_crawl = True

    try:
        config = load_config(config_path)
    except ConfigError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 1

    if disable_crawl:
        config["execution"]["crawl_enabled"] = False

    orchestrator = SEOOrchestrator(config)
    if mode == "schedule":
        interval = config.get("schedule", {}).get("interval_minutes", 1440)
        orchestrator.run_forever(interval)
        return 0

    result = orchestrator.run_once()
    print(json.dumps(result, indent=2))

    # Fire all indexing and backlink signals after every SEO agent run
    from connectors.post_publish_hook import PostPublishHook
    import logging
    hook = PostPublishHook(config, logging.getLogger("pipeleap_seo_agent"))
    sitemap_path = "pipeleap-launchpad/public/sitemap.xml"
    
    # Pass generated slugs to ensure indexing signals target new content
    new_slugs = [asset.get("slug") for asset in result.get("assets_generated", []) if isinstance(asset, dict)]
    hook.run(sitemap_path=sitemap_path, new_slugs=new_slugs, output_dir="outputs/post_publish")
    return 0


if __name__ == "__main__":
    import traceback
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
