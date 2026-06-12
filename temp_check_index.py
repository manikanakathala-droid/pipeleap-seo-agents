"""Check index.ts for correct imports and check 0-tool categories."""
from pathlib import Path
import re

index_path = Path("temp_frontend_repo/src/data/tools/index.ts")
text = index_path.read_text()

# Extract all imports
imports = re.findall(r'import\s*\{\s*(\w+)\s*\}', text)
# Remove the first one (Tool type)
tool_import = imports[0] if imports else ""
imports = imports[1:] if len(imports) > 1 else []

print(f"Total imports: {len(imports)}")
for imp in imports:
    print(f"  {imp}")

# Extract all spreads
spreads = re.findall(r'\.\.\.(\w+),', text)
print(f"\nTotal spreads: {len(spreads)}")
for s in spreads:
    print(f"  {s}")

# Check for mismatches
for imp in imports:
    if imp not in spreads:
        print(f"  MISSING spread for: {imp}")
for s in spreads:
    if s not in imports:
        print(f"  EXTRA spread for: {s}")

# Check for duplicate import lines
import_lines = re.findall(r'^import.*$', text, re.MULTILINE)
dupes = [l for l in import_lines if import_lines.count(l) > 1]
if dupes:
    print(f"\nDuplicate imports:")
    for d in set(dupes):
        print(f"  {d}")
