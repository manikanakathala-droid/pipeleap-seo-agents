from __future__ import annotations

import subprocess
import sys


COMMANDS = [
    [sys.executable, "scripts/audit_duplicates.py"],
    [sys.executable, "-m", "compileall", "-q", "main.py", "run_growth_engine.py", "run_geo_agent.py", "agents", "connectors", "core", "geo_agent", "modules", "utils"],
    [sys.executable, "run_growth_engine.py", "--dry-run"],
]


def main() -> int:
    for command in COMMANDS:
        print(f"Running: {' '.join(command)}")
        subprocess.run(command, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
