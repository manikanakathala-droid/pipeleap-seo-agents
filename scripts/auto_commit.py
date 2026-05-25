from __future__ import annotations

import os
import subprocess
import sys


def run(command: list[str], capture: bool = False) -> str:
    result = subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout or ""


def main() -> int:
    run([sys.executable, "scripts/validate_repo.py"])
    run(["git", "add", "--all"])
    status = run(["git", "status", "--porcelain"], capture=True).strip()
    if not status:
        print("No validated changes to commit.")
        return 0
    message = os.getenv("AUTO_COMMIT_MESSAGE", "chore: auto-commit validated SEO agent changes")
    run(["git", "commit", "-m", message])
    run(["git", "push", "origin", "HEAD"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
