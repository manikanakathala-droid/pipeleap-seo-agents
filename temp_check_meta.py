"""Quick check of categories.ts after fixes."""
from pathlib import Path
import re

text = Path("temp_frontend_repo/src/data/tools/categories.ts").read_text()

# Check for duplicate entries
slugs = re.findall(r'slug:\s*"([^"]+)"', text)
dupes = set(s for s in slugs if slugs.count(s) > 1)
if dupes:
    print(f"DUPLICATE slugs: {dupes}")
else:
    print("No duplicates!")

# Count entries
count = len(slugs)
print(f"Total category entries: {count}")

# Check names with odd casing
names = re.findall(r'name:\s*"([^"]+)"', text)
for name in names:
    # Check for lowercase first letter
    if name[0].islower():
        print(f"  LOWERCASE name: {name}")
    # Check for "Tools" plural issues
    if name.endswith(" Tools") and name.count(" ") > 2:
        print(f"  Long name: {name}")

# Check meta descriptions still with issues
for m in re.findall(r'metaDescription:\s*"([^"]+)"', text):
    if "The best " in m and len(m) > 0 and m[9:10] and m[9].islower():
        print(f"  BAD META (starts with verb): {m[:80]}...")

print("\nDone!")
