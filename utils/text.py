from __future__ import annotations

import re


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "page"


def title_case_keyword(keyword: str) -> str:
    replacements = {
        "ai": "AI",
        "crm": "CRM",
        "sdr": "SDR",
        "saas": "SaaS",
        "n8n": "n8n",
        "revops": "RevOps",
        "gtm": "GTM",
        "hubspot": "HubSpot",
        "pipeleap": "Pipeleap",
    }
    stop_words = {"to", "for", "with", "and", "or", "of", "in", "on", "vs"}
    parts = []
    for index, part in enumerate(keyword.split()):
        clean = re.sub(r"[^a-z0-9.]+", "", part.lower())
        if clean in replacements:
            parts.append(replacements[clean])
        elif index > 0 and clean in stop_words:
            parts.append(clean)
        elif "." in part:
            parts.append(part[0].upper() + part[1:])
        else:
            parts.append(part.capitalize())
    return " ".join(parts)


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped
