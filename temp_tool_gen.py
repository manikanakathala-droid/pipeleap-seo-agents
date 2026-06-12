"""Check format of existing tool files and categories."""
import json
import re
from pathlib import Path

tools_dir = Path("temp_frontend_repo/src/data/tools")

# Check categories.ts format
cat_text = (tools_dir / "categories.ts").read_text(encoding="utf-8")
bt = cat_text.count("`")
dq = cat_text.count('"')
print(f"categories.ts: backticks={bt}, double-quotes={dq}")

# Check a tool data file
tool_text = (tools_dir / "ai-sdr-tools.ts").read_text(encoding="utf-8")
bt2 = tool_text.count("`")
dq2 = tool_text.count('"')
print(f"ai-sdr-tools.ts: backticks={bt2}, double-quotes={dq2}")
# Show first 300 chars
print("---ai-sdr-tools.ts top---")
print(tool_text[:300])

# Check index.ts
index_text = (tools_dir / "index.ts").read_text(encoding="utf-8")
print("\n---index.ts top---")
print(index_text[:500])

# List all .ts files
for f in sorted(tools_dir.glob("*.ts")):
    print(f.name)
