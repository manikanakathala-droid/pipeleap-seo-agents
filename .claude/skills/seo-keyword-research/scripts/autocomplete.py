#!/usr/bin/env python3
"""Expand seed keywords with Google autocomplete suggestions, per country.

Autocomplete only returns phrases people actually search, so it works as a free
demand signal when no keyword tool is available. Standard library only.

Usage:
  python autocomplete.py --seeds "sales productivity software,reduce sales admin" \
      --countries us,gb,in --expand questions --out autocomplete.csv
  python autocomplete.py --seeds-file seeds.txt --countries us
"""
from __future__ import annotations

import argparse
import csv
import json
import string
import sys
import time
import urllib.parse
import urllib.request

ENDPOINT = "https://suggestqueries.google.com/complete/search"
QUESTION_FORMS = [
    "{s}",
    "best {s}",
    "how to {s}",
    "{s} tools",
    "{s} for small teams",
    "{s} vs",
    "what is {s}",
    "why {s}",
]


def suggest(query: str, country: str, delay: float) -> list[str]:
    params = urllib.parse.urlencode({"client": "firefox", "q": query, "hl": "en", "gl": country})
    req = urllib.request.Request(f"{ENDPOINT}?{params}", headers={"User-Agent": "Mozilla/5.0 (keyword-research)"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            time.sleep(delay)
            return [s for s in data[1] if isinstance(s, str)]
        except Exception as exc:  # network hiccup or rate limit: back off
            if attempt == 2:
                print(f"warn: {country} '{query}': {exc}", file=sys.stderr)
                return []
            time.sleep(delay * (attempt + 2) * 2)
    return []


def variants(seed: str, mode: str) -> list[str]:
    if mode == "questions":
        return [f.format(s=seed) for f in QUESTION_FORMS]
    if mode == "alphabet":
        return [seed] + [f"{seed} {c}" for c in string.ascii_lowercase]
    return [seed]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--seeds", help="Comma-separated seed phrases")
    p.add_argument("--seeds-file", help="File with one seed per line")
    p.add_argument("--countries", default="us", help="Comma-separated country codes, e.g. us,gb,ca,au,in")
    p.add_argument("--expand", choices=["none", "questions", "alphabet"], default="none")
    p.add_argument("--delay", type=float, default=0.4, help="Seconds between requests (be polite)")
    p.add_argument("--out", help="CSV output path (default: stdout)")
    a = p.parse_args()

    seeds: list[str] = []
    if a.seeds:
        seeds += [s.strip() for s in a.seeds.split(",") if s.strip()]
    if a.seeds_file:
        with open(a.seeds_file, encoding="utf-8") as fh:
            seeds += [l.strip() for l in fh if l.strip() and not l.startswith("#")]
    if not seeds:
        p.error("give --seeds or --seeds-file")

    countries = [c.strip().lower() for c in a.countries.split(",") if c.strip()]
    found: dict[tuple[str, str], dict] = {}
    for seed in seeds:
        for q in variants(seed, a.expand):
            for country in countries:
                for s in suggest(q, country, a.delay):
                    key = (seed, s.lower())
                    row = found.setdefault(key, {"seed": seed, "suggestion": s.lower(), "countries": set(), "hits": 0})
                    row["countries"].add(country)
                    row["hits"] += 1

    rows = sorted(found.values(), key=lambda r: (r["seed"], -len(r["countries"]), -r["hits"], r["suggestion"]))
    out = open(a.out, "w", newline="", encoding="utf-8") if a.out else sys.stdout
    w = csv.writer(out)
    w.writerow(["seed", "suggestion", "country_count", "countries", "hits"])
    for r in rows:
        w.writerow([r["seed"], r["suggestion"], len(r["countries"]), " ".join(sorted(r["countries"])), r["hits"]])
    if a.out:
        out.close()
        print(f"{len(rows)} suggestions from {len(seeds)} seeds x {len(countries)} countries -> {a.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
