"""Final count check."""
from pathlib import Path
import re

tools_dir = Path("temp_frontend_repo/src/data/tools")
total = 0
empty = []
for f in sorted(tools_dir.glob("*.ts")):
    if f.name in ("categories.ts", "index.ts"):
        continue
    count = len(re.findall(r'slug:\s*"', f.read_text()))
    total += count
    if count == 0:
        empty.append(f.stem)
print(f"Total: {total} tools across 37 categories")
if empty:
    print(f"STILL EMPTY: {empty}")
else:
    print("All 37 categories have at least 1 tool!")

# Verify index.ts is valid
idx = (tools_dir / "index.ts").read_text()
print(f"index.ts: {len(re.findall(r'import \{', idx))} imports, {len(re.findall(r'\.\.\.', idx))} spreads")
