"""
Entry point for the growth loop.

  python run_growth_loop.py --site-dir site            full run
  python run_growth_loop.py --site-dir site --dry-run  plan and report only, change nothing
  python run_growth_loop.py --ping                     notify search engines of URLs changed by the last run
                                                       (call only after the site change is deployed)
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--site-dir", default="site")
    parser.add_argument("--state-dir", default="growth_state")
    parser.add_argument("--config", default="growth.yaml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--offline", action="store_true", help="skip Search Console and GA4")
    parser.add_argument("--ping", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    logger = logging.getLogger("growth")

    if args.ping:
        report = json.loads((Path(args.state_dir) / "report.json").read_text(encoding="utf-8"))
        urls = report.get("changed_urls", [])
        if not urls:
            logger.info("No changed URLs to submit.")
            return 0
        from connectors.indexnow_connector import IndexNowConnector
        for result in IndexNowConnector().submit_all_endpoints(urls):
            logger.info("IndexNow %s -> %s", result.get("endpoint"), result.get("status"))
        return 0

    from growth.run import load_growth_config, run
    integrations: dict = {}
    try:
        from utils.config_loader import load_config
        integrations = load_config("config.yaml")
    except Exception as exc:
        logger.warning("config.yaml not loaded (%s); Search Console and GA4 settings unavailable", exc)

    report = run(site_dir=args.site_dir, state_dir=args.state_dir, growth=load_growth_config(args.config),
                 config=integrations, dry_run=args.dry_run, offline=args.offline, logger=logger)
    print(report["briefing"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
