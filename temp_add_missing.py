"""Add missing categories to categories.ts, create tool data files, update index.ts."""
from pathlib import Path
import re
import sys

sys.path.insert(0, ".")
from core.tool_content_engine import CATEGORY_DESCRIPTIONS

tools_dir = Path("temp_frontend_repo/src/data/tools")
cat_file = tools_dir / "categories.ts"
index_file = tools_dir / "index.ts"

# Read current files
cat_text = cat_file.read_text(encoding="utf-8")
idx_text = index_file.read_text(encoding="utf-8") if index_file.exists() else ""

# Get existing category slugs
existing_cats = set()
for m in re.finditer(r'slug:\s*"([^"]+)"', cat_text):
    existing_cats.add(m.group(1))

missing_cats = sorted(set(CATEGORY_DESCRIPTIONS.keys()) - existing_cats)
print(f"Categories to add to categories.ts: {len(missing_cats)}")
for s in missing_cats:
    print(f"  {s}")

# First: add missing tool data files and index.ts entries
# Then: add missing categories to categories.ts

# --- Step 1: Create missing tool data files ---
files_created = 0
for slug in missing_cats:
    fpath = tools_dir / f"{slug}.ts"
    if fpath.exists():
        continue
    var_name = slug.replace("-", "_") + "Tools"
    ts_content = f"""import type {{ Tool }} from "@/types/tool";

export const {var_name}: Tool[] = [
];
"""
    fpath.write_text(ts_content, encoding="utf-8")
    print(f"  Created {fpath.name}")
    files_created += 1

print(f"\nCreated {files_created} tool data files")

# --- Step 2: Update index.ts for all missing ---
lines = idx_text.split("\n")
marker_line = None
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.endswith(",") and "from" not in stripped and "..." not in stripped and "export" not in stripped:
        # Find the last import or spread line
        pass
    if "..." in stripped and stripped.strip().startswith("..."):
        if "..." and stripped.strip().startswith("..."):
            continue

import_lines_added = 0
spread_lines_added = 0

# Find position for imports: after last existing import
last_import_idx = -1
for i, line in enumerate(lines):
    if line.strip().startswith("import ") and "from" in line:
        last_import_idx = i

# Find position for spread: before the closing ]; of allTools
all_tools_end = -1
for i in range(len(lines) - 1, -1, -1):
    if lines[i].strip() == "];":
        # Check if the surrounding context is the allTools export
        for j in range(max(0, i-20), i):
            if "allTools" in lines[j]:
                all_tools_end = i
                break
        if all_tools_end >= 0:
            break

# Find the last spread line before allTools_end
last_spread_idx = -1
for i in range(last_import_idx + 1 if last_import_idx >= 0 else 0, all_tools_end if all_tools_end >= 0 else len(lines)):
    stripped = lines[i].strip()
    if stripped.startswith("...") and stripped.endswith(","):
        last_spread_idx = i

for slug in missing_cats:
    var_name = slug.replace("-", "_") + "Tools"
    import_line = f'import {{ {var_name} }} from "./{slug}";'
    spread_line = f"  ...{var_name},"

    # Add import
    if import_line not in idx_text:
        if last_import_idx >= 0:
            lines.insert(last_import_idx + 1, import_line)
            last_import_idx += 1
        import_lines_added += 1

    # Add spread
    if spread_line not in idx_text:
        if all_tools_end >= 0:
            lines.insert(all_tools_end, spread_line)
            all_tools_end += 1
        spread_lines_added += 1

new_idx = "\n".join(lines)
index_file.write_text(new_idx, encoding="utf-8")
print(f"\nUpdated index.ts: {import_lines_added} imports added, {spread_lines_added} spreads added")

# --- Step 3: Add category entries to categories.ts ---
# Build entries for all missing cats
entries = []
for slug in missing_cats:
    desc = CATEGORY_DESCRIPTIONS.get(slug, slug.replace("-", " ").title())
    name = slug.replace("-", " ").title()
    plural = name + ("s" if not name.endswith("s") else "")

    entry = f"""  {{
    slug: "{slug}",
    name: "{name}",
    pluralName: "{plural}",
    metaDescription: "The best {desc.lower()} for sales teams.",
    intro: "Browse our curated list of {desc.lower()} to find the right fit for your sales stack.",
    body: "This category covers {desc.lower()} that help sales operations teams build a complete outbound motion.",
    tools: [],
    relatedCategories: [],
    pipeLeapAngle: "Pipeleap orchestrates the workflow around {desc.lower()} - routing signals, syncing data, and governing the flow between tools.",
    faqs: [],
  }},"""
    entries.append(entry)

# Insert before the closing ]; of toolCategories
end_pos = cat_text.rfind("];")
if end_pos >= 0:
    # Find the last entry before ]; and add a comma if needed
    before_end = cat_text[:end_pos].rstrip()
    if not before_end.endswith(","):
        # Need to add comma to the last existing entry
        before_end = before_end + ","
    else:
        before_end = before_end
    
    new_cat_text = before_end + "\n" + "\n".join(entries) + "\n" + cat_text[end_pos:]
    cat_file.write_text(new_cat_text, encoding="utf-8")
    print(f"\nAdded {len(entries)} category entries to categories.ts")

print("\nDone!")
