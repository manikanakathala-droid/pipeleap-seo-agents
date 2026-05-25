"""
Initialises the SEO workflows repo directory structure.
Run once on first checkout — safe to re-run (idempotent).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(".")

DIRS = [
    "content/blogs",
    "content/glossary",
    "seo",
    "seo/history",
    "outputs/seo_os_state",
]

JSON_SCAFFOLDS = {
    "seo/metadata-updates.json": [],
    "seo/internal-links.json": [],
    "seo/keywords.json": [],
    "seo/indexing-queue.json": [],
    "seo/competitor-insights.json": [],
    "seo/run-log.json": [],
}

MARKDOWN_SCAFFOLDS = {
    "seo/technical-audit.md": (
        "# Pipeleap Technical SEO Audit Log\n\n"
        "Appended on every SEO OS run. Each section is timestamped and versioned by run_id.\n"
        "Labels: **SAFE TO APPLY** | **REQUIRES DEV REVIEW**\n"
    ),
    "content/blogs/.gitkeep": "",
    "content/glossary/.gitkeep": "",
}

for d in DIRS:
    (ROOT / d).mkdir(parents=True, exist_ok=True)
    print(f"  dir:  {d}")

for rel_path, content in JSON_SCAFFOLDS.items():
    p = ROOT / rel_path
    if not p.exists():
        p.write_text(json.dumps(content, indent=2), encoding="utf-8")
        print(f"  json: {rel_path}")
    else:
        print(f"  skip: {rel_path} (exists)")

for rel_path, content in MARKDOWN_SCAFFOLDS.items():
    p = ROOT / rel_path
    if not p.exists():
        p.write_text(content, encoding="utf-8")
        print(f"  md:   {rel_path}")
    else:
        print(f"  skip: {rel_path} (exists)")

print("\nRepo structure initialised.")
