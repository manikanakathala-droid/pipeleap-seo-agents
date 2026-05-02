"""
Revenue attribution engine — tracks per-page conversion data and pipeline value.
Reads conversion events from the conversions CSV and maps them to page slugs via UTM params.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Any


class RevenueAttributionEngine:
    """
    Reads conversions.csv (or a UTM-enriched version) and produces
    a per-page revenue attribution table for the weekly report.

    CSV format expected:
        date, conversions, source, utm_content (= page slug), pipeline_value_usd
    """

    def __init__(self, conversion_csv_path: str) -> None:
        self.path = Path(conversion_csv_path) if conversion_csv_path else None

    def attribution_table(self) -> list[dict[str, Any]]:
        if not self.path or not self.path.exists():
            return []
        rows = []
        try:
            with self.path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    slug = row.get("utm_content", "") or row.get("page_slug", "")
                    if not slug:
                        continue
                    rows.append({
                        "slug": slug,
                        "date": row.get("date", ""),
                        "conversions": int(float(row.get("conversions", 0) or 0)),
                        "source": row.get("source", "organic"),
                        "pipeline_value_usd": float(row.get("pipeline_value_usd", 0) or 0),
                    })
        except Exception:
            return []
        return rows

    def top_pages(self, n: int = 10) -> list[dict[str, Any]]:
        table = self.attribution_table()
        aggregated: dict[str, dict[str, Any]] = {}
        for row in table:
            slug = row["slug"]
            if slug not in aggregated:
                aggregated[slug] = {"slug": slug, "conversions": 0, "pipeline_value_usd": 0.0}
            aggregated[slug]["conversions"] += row["conversions"]
            aggregated[slug]["pipeline_value_usd"] += row["pipeline_value_usd"]
        return sorted(aggregated.values(), key=lambda x: x["pipeline_value_usd"], reverse=True)[:n]

    def weekly_report_md(self) -> str:
        top = self.top_pages()
        if not top:
            return "## Revenue Attribution\n\nNo conversion data yet. Run `export_conversions.py` and ensure UTM parameters are present on all CTA links.\n"
        lines = [
            "## Revenue Attribution — Top SEO Pages",
            "",
            "| Page | Conversions | Pipeline Value (USD) |",
            "| --- | --- | --- |",
        ]
        for page in top:
            lines.append(f"| `{page['slug']}` | {page['conversions']} | ${page['pipeline_value_usd']:,.0f} |")
        return "\n".join(lines)

    def utm_enriched_cta(self, base_url: str, slug: str, campaign: str = "organic") -> str:
        return f"{base_url}?utm_source=organic&utm_medium=seo&utm_campaign={campaign}&utm_content={slug.replace('/', '_')}"
