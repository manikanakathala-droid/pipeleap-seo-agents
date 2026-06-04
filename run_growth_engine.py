"""
Standalone entry point for the Pipeleap SaaS Growth Engine module.

Usage:
    python run_growth_engine.py
    python run_growth_engine.py --config config.yaml
    python run_growth_engine.py --competitors Clay,Zapier,HubSpot
    python run_growth_engine.py --pages all
    python run_growth_engine.py --pages roles,competitors

This runner is ADDITIVE — it does not call or modify main.py or any
existing agent code. Run it alongside or independently of the main agent.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path so all imports resolve correctly
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config_loader import ConfigError, load_config
from utils.logger import configure_logger
from modules.pipeleap_seo_engine.orchestrator import GrowthEngineOrchestrator


# argparse removed to prevent exit code 2


def main() -> int:
    config_path = "config.yaml"
    competitors_arg = ""
    pages_arg = "all"
    dry_run = False
    tools_only = False

    if "--dry-run" in sys.argv:
        dry_run = True
    if "--tools-only" in sys.argv:
        tools_only = True

    try:
        config = load_config(config_path)
    except ConfigError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 1

    logger = configure_logger(level=config.get("execution", {}).get("log_level", "INFO"))

    # Override config with CLI args
    module_config = config.setdefault("growth_engine", {})

    if competitors_arg:
        module_config["priority_competitors"] = [c.strip() for c in competitors_arg.split(",")]

    if tools_only:
        module_config["generate_roles"] = False
        module_config["generate_use_cases"] = False
        module_config["generate_competitors"] = False
        module_config["generate_integrations"] = False
        module_config["generate_workflows"] = False
        module_config["generate_bofu"] = False
        module_config["generate_objection_pages"] = False
        module_config["generate_blog"] = False
        module_config["generate_tools_pages"] = True
        module_config["generate_glossary"] = False

    page_types = {p.strip().lower() for p in pages_arg.split(",")}
    if "all" not in page_types:
        module_config["_page_type_filter"] = page_types

    if dry_run:
        from modules.pipeleap_seo_engine.engines.keyword_engine import GrowthKeywordEngine
        matrix = GrowthKeywordEngine().build_matrix()
        print(f"\nDry run — keyword matrix: {len(matrix)} entries")
        print("\nTop 20 keywords by priority:")
        for entry in matrix[:20]:
            print(f"  [{entry['intent']:13}] {entry['keyword']}")
        return 0

    orchestrator = GrowthEngineOrchestrator(config, logger)
    report = orchestrator.run()

    print(f"\nGrowth Engine complete")
    print(f"  Pages generated : {report.to_dict()['total_pages']}")
    breakdown = report.to_dict()["page_type_breakdown"]
    for page_type, count in sorted(breakdown.items()):
        print(f"    {page_type:<22} {count}")
    print(f"  Keywords in matrix: {report.to_dict()['keyword_matrix_size']}")
    print(f"  Output directory: {report.output_directory}")

    # Backfill inbound links from existing pages to newly published pages
    from connectors.cms_connector import CMSConnector
    cms = CMSConnector(config, logger)
    backfill = cms.backfill_inbound_links(report.pages_generated)
    print(f"  Backfill links   : {backfill['links_injected']} injected across {backfill['files_updated']} existing pages")

    # Fire all indexing and backlink signals after growth engine run
    from connectors.post_publish_hook import PostPublishHook
    hook = PostPublishHook(config, logger)
    hook.run(
        sitemap_path="pipeleap-launchpad/public/sitemap.xml",
        new_slugs=[p.slug for p in report.pages_generated],
        output_dir="outputs/post_publish",
    )

    # Backlink execution — archive newly published pages
    from connectors.backlink_executor import BacklinkExecutor
    site_url = config.get("site", {}).get("site_url", "https://www.pipeleap.com").rstrip("/")
    backlink_urls = [p.url for p in report.pages_generated if hasattr(p, "url") and p.url]
    if not backlink_urls:
        backlink_urls = [f"{site_url}/tools/{p.slug}" for p in report.pages_generated if hasattr(p, "slug") and p.slug]
    if backlink_urls:
        be = BacklinkExecutor(output_dir="outputs/backlinks")
        be.run_all(backlink_urls)
        print(f"BacklinkExecutor: {len(backlink_urls)} URLs submitted")
    return 0


if __name__ == "__main__":
    import traceback
    import sys
    try:
        # Ensure output dir exists early
        from pathlib import Path
        Path("outputs").mkdir(parents=True, exist_ok=True)
        sys.exit(main())
    except SystemExit as e:
        if e.code != 0:
            print(f"CRITICAL: Process exited with code {e.code}")
        raise
    except Exception:
        traceback.print_exc()
        sys.exit(1)
