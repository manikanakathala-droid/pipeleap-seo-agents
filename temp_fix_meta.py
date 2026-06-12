"""Fix meta descriptions in categories.ts so they don't start with 'The best enhance...' etc."""
from pathlib import Path
import re

cat_path = Path("temp_frontend_repo/src/data/tools/categories.ts")
text = cat_path.read_text(encoding="utf-8")

def fix_meta(match):
    full = match.group(0)
    inner = match.group(1)
    # If meta starts with "The best " and the following text starts with a verb (lowercase),
    # generate a cleaner meta from the intro text
    if inner.startswith("The best ") and inner[9].islower():
        # Use the intro field to craft a cleaner meta
        # Find the intro for this entry
        entry_start = text.rfind(match.group(0))
        # Simple approach: just strip "The best " and " for sales teams." and replace
        cleaned = inner.replace("The best ", "").rstrip(".")
        # Check if "for sales teams" is at the end
        if cleaned.endswith(" for sales teams"):
            cleaned = cleaned[: -len(" for sales teams")]
        # Remove duplicate "for sales teams" patterns
        cleaned = cleaned.replace(" for sales teams for sales teams", " for sales teams")
        # Capitalize first letter
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]
        new_meta = f'    metaDescription: "{cleaned} for sales teams.",'
        if new_meta != full:
            return new_meta
    return full

text = re.sub(r'    metaDescription: "([^"]+)",', fix_meta, text)
cat_path.write_text(text, encoding="utf-8")
print("Fixed meta descriptions")
