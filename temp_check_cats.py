"""Check categories.ts format."""
from pathlib import Path

text = (Path("temp_frontend_repo/src/data/tools/categories.ts")).read_text(encoding="utf-8")
# Find all category entries
count = 0
for line in text.split("\n"):
    if "slug:" in line:
        count += 1
print(f"Total category entries: {count}")

# Show first entry
start = text.index("{") + 1
end = text.index("},", start) + 2
first_entry = text[start - 1 : end]
print("---First entry---")
print(first_entry[:600])

# Check what quote style slug uses
if "`ai-sdr-tools`" in text:
    print("Categories use: BACKTICKS")
elif '"ai-sdr-tools"' in text:
    print("Categories use: QUOTES")
else:
    print("Cannot determine format")
