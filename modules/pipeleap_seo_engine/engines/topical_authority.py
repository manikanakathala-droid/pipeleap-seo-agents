"""Topical authority mapper — tracks pillar coverage and prioritizes spoke generation."""
from __future__ import annotations
from typing import Any

PILLARS: dict[str, dict[str, Any]] = {
    "outbound-automation": {
        "label": "Outbound Automation",
        "pillar_slug": "automate-saas-outbound",
        "target_spoke_count": 20,
        "spoke_templates": [
            "how to automate {role} outbound",
            "outbound automation for {industry} {role}",
            "{tool} alternative for saas outbound",
            "best outbound automation tools for {role}",
            "automate outbound without sdrs {stage}",
        ],
    },
    "pipeline-generation": {
        "label": "Pipeline Generation",
        "pillar_slug": "saas-pipeline-generation-automation",
        "target_spoke_count": 15,
        "spoke_templates": [
            "predictable pipeline for saas {role}",
            "pipeline generation without sdrs",
            "saas pipeline automation {stage}",
            "how to build pipeline for {role}",
        ],
    },
    "workflow-orchestration": {
        "label": "Workflow Orchestration",
        "pillar_slug": "saas-workflow-orchestration",
        "target_spoke_count": 15,
        "spoke_templates": [
            "workflow orchestration for {role}",
            "saas workflow automation {use_case}",
            "outbound workflow recipe {trigger}",
            "workflow orchestration vs {tool}",
        ],
    },
    "competitor-comparison": {
        "label": "Competitor Comparisons",
        "pillar_slug": "why-saas-outbound-fails",
        "target_spoke_count": 20,
        "spoke_templates": [
            "pipeleap vs {tool}",
            "{tool} alternative for saas",
            "best {tool} alternative outbound",
            "{tool1} vs {tool2} vs pipeleap",
        ],
    },
    "glossary": {
        "label": "Glossary / Entity SEO",
        "pillar_slug": "glossary",
        "target_spoke_count": 30,
        "spoke_templates": [
            "what is {term}",
            "{term} definition saas",
            "{term} for revenue teams",
        ],
    },
    "integrations": {
        "label": "Integration Pages",
        "pillar_slug": "integrations",
        "target_spoke_count": 20,
        "spoke_templates": [
            "pipeleap {tool} integration",
            "pipeleap + {tool} workflow",
            "connect pipeleap with {tool}",
        ],
    },
}


class TopicalAuthorityMapper:

    def __init__(self) -> None:
        self._coverage: dict[str, list[str]] = {p: [] for p in PILLARS}

    def register_page(self, page_slug: str, pillar: str) -> None:
        if pillar in self._coverage:
            self._coverage[pillar].append(page_slug)

    def register_pages(self, pages: list[Any]) -> None:
        for page in pages:
            pillar = getattr(page, "topical_pillar", "") or self._infer_pillar(page)
            if pillar:
                self.register_page(page.slug, pillar)

    def coverage_report(self) -> dict[str, Any]:
        report = {}
        for pillar_key, pillar in PILLARS.items():
            covered = len(self._coverage.get(pillar_key, []))
            target = pillar["target_spoke_count"]
            gap = max(0, target - covered)
            report[pillar_key] = {
                "label": pillar["label"],
                "covered": covered,
                "target": target,
                "gap": gap,
                "coverage_pct": round(covered / max(target, 1) * 100, 1),
                "priority": "HIGH" if covered < target * 0.3 else "MEDIUM" if covered < target * 0.7 else "LOW",
            }
        return report

    def prioritized_pillars(self) -> list[str]:
        report = self.coverage_report()
        return sorted(report.keys(), key=lambda k: report[k]["coverage_pct"])

    def weekly_report_md(self) -> str:
        report = self.coverage_report()
        lines = ["## Topical Authority Coverage", ""]
        total_covered = sum(v["covered"] for v in report.values())
        total_target = sum(v["target"] for v in report.values())
        lines.append(f"**Overall coverage: {total_covered}/{total_target} pages ({round(total_covered/max(total_target,1)*100)}%)**")
        lines.append("")
        lines.append("| Pillar | Covered | Target | Gap | Priority |")
        lines.append("| --- | --- | --- | --- | --- |")
        for key, data in report.items():
            lines.append(f"| {data['label']} | {data['covered']} | {data['target']} | {data['gap']} | {data['priority']} |")
        return "\n".join(lines)

    @staticmethod
    def _infer_pillar(page: Any) -> str:
        slug = getattr(page, "slug", "")
        page_type = getattr(page, "page_type", "")
        if page_type == "glossary_page" or slug.startswith("glossary"):
            return "glossary"
        if page_type == "integration_page" or slug.startswith("integrations"):
            return "integrations"
        if page_type in ("comparison_page", "alternative_page", "multi_comparison_page"):
            return "competitor-comparison"
        if page_type == "workflow_recipe" or slug.startswith("workflows"):
            return "workflow-orchestration"
        if "pipeline" in slug:
            return "pipeline-generation"
        return "outbound-automation"
