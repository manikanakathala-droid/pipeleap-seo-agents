"""
Pipeleap GEO Agent — entry point.

Standalone runner for Generative Engine Optimization.
Reads config_geo.yaml and runs the full GEO orchestration pipeline.

Usage:
    python run_geo_agent.py
    python run_geo_agent.py --config config_geo.yaml
    python run_geo_agent.py --dry-run     # analyse only, no page publishing
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def load_config(config_path: str = "config_geo.yaml") -> dict:
    from utils.config_loader import load_config as _load
    return _load(config_path)


def main() -> None:
    config_path = "config_geo.yaml"
    dry_run = False
    
    if "--dry-run" in sys.argv:
        dry_run = True

    print("=" * 60)
    print("Pipeleap GEO Agent — Generative Engine Optimization")
    print("=" * 60)

    config = load_config(config_path)

    if dry_run:
        print("[DRY RUN] Analysis only — pages will not be published")
        config.setdefault("geo_engine", {})["publish_pages"] = False

    from geo_agent.geo_orchestrator import GEOOrchestrator
    orchestrator = GEOOrchestrator(config)
    report = orchestrator.run()

    report_dict = report.to_dict()
    print()
    print("GEO Agent run complete")
    print(f"  Pages generated  : {report_dict['total_pages']}")
    print(f"  Citation gaps    : {len(report_dict['citation_gaps'])}")
    print(f"  Citation score   : {report_dict['citation_score']}/100")
    print(f"  AI OV queries    : {len(report_dict['ai_overview_queries'])}")
    print(f"  Output           : {report_dict['output_directory']}")
    print()
    print("Top recommendations:")
    for rec in report_dict["recommendations"][:3]:
        print(f"  - {rec[:100]}")

    if not dry_run:
        # Fire indexing and backlink signals only after a publishing run.
        from connectors.post_publish_hook import PostPublishHook
        import logging as _logging
        hook = PostPublishHook(config, _logging.getLogger("pipeleap_geo_agent"))
        new_slugs = [p.slug for p in report.pages_generated]
        hook.run(
            sitemap_path="pipeleap-launchpad/public/sitemap.xml",
            new_slugs=new_slugs,
            output_dir="outputs/post_publish",
        )


if __name__ == "__main__":
    import traceback
    try:
        from pathlib import Path
        Path("outputs").mkdir(parents=True, exist_ok=True)
        main()
    except SystemExit as e:
        if e.code != 0:
            print(f"CRITICAL: Process exited with code {e.code}")
        raise
    except Exception:
        traceback.print_exc()
        sys.exit(1)
