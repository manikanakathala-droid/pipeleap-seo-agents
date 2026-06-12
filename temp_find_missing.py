"""Find which categories are missing from categories.ts and add them."""
from pathlib import Path
import re
import sys

sys.path.insert(0, ".")
from core.tool_content_engine import CATEGORY_DESCRIPTIONS

tools_dir = Path("temp_frontend_repo/src/data/tools")
cat_file = tools_dir / "categories.ts"
cat_text = cat_file.read_text(encoding="utf-8")

# Extract existing slugs from categories.ts
existing_cats = set()
for m in re.finditer(r'slug:\s*"([^"]+)"', cat_text):
    existing_cats.add(m.group(1))

# CATEGORY_DESCRIPTIONS has 37 keys
all_keys = set(CATEGORY_DESCRIPTIONS.keys())
missing = sorted(all_keys - existing_cats)

# also check which have files
print(f"Categories in categories.ts: {len(existing_cats)}")
print(f"Total CATEGORY_DESCRIPTIONS: {len(all_keys)}")
print(f"Missing from categories.ts: {len(missing)}")
for s in missing:
    has_file = (tools_dir / f"{s}.ts").exists()
    print(f"  {s} (file: {'YES' if has_file else 'NO'})")
