"""Retired entry point for the former Pipeleap growth loop."""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "The Pipeleap growth loop has been retired. This entry point no longer runs.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
