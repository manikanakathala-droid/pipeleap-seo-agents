"""Generate tool entries for categories needing them."""
import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Get gh token
result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
token = result.stdout.strip()
if token:
    os.environ["GITHUB_TOKEN"] = token
    print(f"GITHUB_TOKEN set from gh auth ({len(token)} chars)")
else:
    print("ERROR: No GitHub token available")
    sys.exit(1)

sys.path.insert(0, ".")
from core.tool_content_engine import ToolContentEngine, CATEGORY_DESCRIPTIONS
from connectors.github_publisher import GitHubPublisher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tools_dir = Path("temp_frontend_repo/src/data/tools")

# Collect existing slugs and names from ALL tool files to avoid dupes
existing_slugs = set()
existing_names = set()
for f in tools_dir.glob("*.ts"):
    if f.name in ("categories.ts", "index.ts"):
        continue
    text = f.read_text(encoding="utf-8")
    for m in re.finditer(r'slug:\s*"([^"]+)"', text):
        existing_slugs.add(m.group(1))
    for m in re.finditer(r'name:\s*"([^"]+)"', text):
        existing_names.add(m.group(1).lower())

print(f"\nExisting slugs: {len(existing_slugs)}, names: {len(existing_names)}")

# Find categories below target (40 tools each) - focus on empty ones
TARGET = 40
EMPTY_ONLY = True  # Set to False to fill all up to TARGET
needed = []
for slug in sorted(CATEGORY_DESCRIPTIONS.keys()):
    f = tools_dir / f"{slug}.ts"
    count = 0
    if f.exists():
        text = f.read_text(encoding="utf-8")
        count = len(re.findall(r'slug:\s*"', text))
    if count < TARGET:
        if not EMPTY_ONLY or count == 0:
            needed.append((slug, count))

print(f"\nCategories needing tools:")
for s, c in needed:
    status = "EMPTY" if c == 0 else f"{c} tools"
    print(f"  {s}: {status}")

# Initialize engine
config = {}
engine = ToolContentEngine(config, logger)
publisher = GitHubPublisher()
publisher.logger = logger

tools_per_run = 15
per_cat = 5  # 5 attempts per category for empty ones
total_generated = 0

print(f"\nGenerating up to {tools_per_run} tools across {len(needed)} categories ({per_cat} per cat)...")

for cat_slug, current_count in needed:
    if total_generated >= tools_per_run:
        break

    batch = engine.generate(
        category_slug=cat_slug,
        count=per_cat if current_count > 0 else min(per_cat, 10),
        existing_slugs=existing_slugs,
        existing_names=existing_names,
    )

    if not batch:
        print(f"  {cat_slug}: no tools generated")
        continue

    publisher.publish_tool_data_local(
        tools=batch,
        category_slug=cat_slug,
        frontend_dir="temp_frontend_repo",
    )

    total_generated += len(batch)
    for t in batch:
        existing_slugs.add(t["slug"])
        existing_names.add(t["name"].lower())

    print(f"  {cat_slug}: generated {len(batch)} tools (total: {total_generated})")

print(f"\nDone! Generated {total_generated} new tools.")
