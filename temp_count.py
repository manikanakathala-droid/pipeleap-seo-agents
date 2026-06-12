"""Count tools per category."""
from pathlib import Path
import re

tools_dir = Path("temp_frontend_repo/src/data/tools")
total = 0
for f in sorted(tools_dir.glob("*.ts")):
    if f.name in ("categories.ts", "index.ts"):
        continue
    text = f.read_text()
    slugs = re.findall(r'slug:\s*"([^"]+)"', text)
    names = re.findall(r'name:\s*"([^"]+)"', text)
    count = len(slugs)
    total += count
    status = ""
    if count == 0:
        status = "  !! EMPTY"
    print(f"{f.stem}: {count} tools{status}")
    if count == 0:
        for s, n in zip(slugs, names):
            print(f"    {s}: {n}")

# Check categories.ts
cat_text = (tools_dir / "categories.ts").read_text()
cat_count = len(re.findall(r'slug:\s*"([^"]+)"', cat_text))
print(f"\ncategories.ts: {cat_count} entries")
print(f"Total tool entries: {total}")
