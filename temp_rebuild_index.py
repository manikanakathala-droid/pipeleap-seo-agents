"""Rebuild index.ts with correct export names from each tool file."""
from pathlib import Path
import re

tools_dir = Path("temp_frontend_repo/src/data/tools")
index_file = tools_dir / "index.ts"

# Collect all tool data files and their export names
entries = []
for f in sorted(tools_dir.glob("*.ts")):
    if f.name in ("categories.ts", "index.ts"):
        continue
    text = f.read_text()
    exports = re.findall(r"export const (\w+)", text)
    if exports:
        var_name = exports[0]
        entries.append((f.stem, var_name))

# Sort: put existing (camelCase) first, then new (snake_case) 
# but actually just sort alphabetically by slug
entries.sort(key=lambda x: x[0])

# Build index.ts
lines = [
    'import type { Tool } from "@/types/tool";',
    'import { toolCategories, TOOL_CATEGORY_MAP } from "./categories";',
]
for slug, var_name in entries:
    lines.append(f'import {{ {var_name} }} from "./{slug}";')

lines.append("")
lines.append("export const allTools: Tool[] = [")
for _, var_name in entries:
    lines.append(f"  ...{var_name},")
lines.append("];")
lines.append("")
lines.append("export const TOOL_MAP = Object.fromEntries(")
lines.append("  allTools.map((t) => [t.slug, t])")
lines.append(") as Record<string, Tool>;")
lines.append("")
lines.append("export { toolCategories, TOOL_CATEGORY_MAP };")
lines.append("")

content = "\n".join(lines)
index_file.write_text(content, encoding="utf-8")
print(f"Written index.ts with {len(entries)} entries")
for slug, var_name in entries:
    print(f"  {slug}: {var_name}")
