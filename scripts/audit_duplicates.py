from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path


IGNORED_PREFIXES = (
    ".git/",
    ".venv/",
    "build/",
    "dashboard/",
    "dist/",
    "outputs/",
    "pipeleap-launchpad/",
    "seo/",
    "__pycache__/",
)


def git_files() -> list[str]:
    output = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        text=True,
    )
    return [
        item
        for item in output.splitlines()
        if item and not item.startswith(IGNORED_PREFIXES) and Path(item).is_file()
    ]


def file_hash(path: str) -> tuple[str, int] | None:
    data = Path(path).read_bytes()
    if not data:
        return None
    return hashlib.sha256(data).hexdigest(), len(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit exact duplicate files.")
    parser.parse_args()

    groups: dict[tuple[str, int], list[str]] = {}
    for path in git_files():
        meta = file_hash(path)
        if meta is None:
            continue
        groups.setdefault(meta, []).append(path)

    duplicates = {meta: paths for meta, paths in groups.items() if len(paths) > 1}
    if not duplicates:
        print("Duplicate audit passed: no exact duplicate files found.")
        return 0

    print("Duplicate audit failed: exact duplicate files found.", file=sys.stderr)
    for (digest, size), paths in duplicates.items():
        print(f"\nsha256={digest} size={size} bytes", file=sys.stderr)
        for path in paths:
            print(f"  {path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
