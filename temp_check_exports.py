"""Check tool file export names vs index.ts imports."""
from pathlib import Path
import re

tools_dir = Path("temp_frontend_repo/src/data/tools")

print("=== Tool file export names ===")
for f in sorted(tools_dir.glob("*.ts")):
    if f.name in ("categories.ts", "index.ts"):
        continue
    text = f.read_text()
    exports = re.findall(r"export const (\w+)", text)
    if exports:
        print(f"  {f.stem}: exports {exports[0]}")
    else:
        print(f"  {f.stem}: NO EXPORT FOUND!")

print("\n=== Tool slugs per file ===")
for f in sorted(tools_dir.glob("*.ts")):
    if f.name in ("categories.ts", "index.ts"):
        continue
    text = f.read_text()
    slugs = re.findall(r'slug:\s*"([^"]+)"', text)
    if slugs:
        print(f"  {f.stem}: {len(slugs)} tools - {', '.join(slugs[:3])}...")
    else:
        print(f"  {f.stem}: 0 tools")
