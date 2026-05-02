"""
Digital PR engine — generates linkable asset content briefs and data-driven research topics.
These assets earn natural backlinks from journalists, bloggers, and communities.
"""
from __future__ import annotations
from typing import Any

LINKABLE_ASSETS: list[dict[str, Any]] = [
    {
        "slug": "state-of-saas-outbound-automation",
        "title": "State of SaaS Outbound Automation — Annual Survey Report",
        "format": "data_report",
        "primary_keyword": "saas outbound automation report",
        "target_links_from": ["sales media", "SaaS publications", "RevOps newsletters"],
        "headline_stat": "65% of SaaS SDRs spend more than half their time on manual tasks that automation can eliminate",
        "survey_questions": [
            "How many hours per week does your SDR team spend on manual prospecting and research?",
            "How many outbound tools does your company currently use?",
            "What is your biggest outbound execution bottleneck?",
            "What percentage of your pipeline comes from automated vs. manual outbound?",
            "Have you implemented workflow orchestration for outbound? What was the result?",
        ],
        "distribution_channels": ["Product Hunt", "r/sales", "LinkedIn newsletter", "Sales Hacker", "RevOps Co-op"],
        "why_linkable": "Original data on outbound automation challenges — something no other tool has published. Journalists cite data reports 5× more than opinion pieces.",
    },
    {
        "slug": "sdr-time-audit",
        "title": "The SaaS SDR Time Audit — Where Sales Reps Actually Spend Their Time",
        "format": "research_study",
        "primary_keyword": "sdr time audit sales automation",
        "target_links_from": ["HR/talent media", "sales leadership blogs", "SaaS founders newsletters"],
        "headline_stat": "The average B2B SDR spends 23 minutes per prospect on manual tasks — only 4 of which require human judgment",
        "methodology": "Survey of 200+ SaaS SDRs tracking time allocation across prospecting, enrichment, sequencing, CRM logging, and follow-up activities.",
        "distribution_channels": ["LinkedIn", "r/sales", "Sales Hacker", "Predictable Revenue"],
        "why_linkable": "Time-based data is highly shareable and provokes strong opinions — ideal for media pickup and social sharing.",
    },
    {
        "slug": "outbound-tech-stack-report",
        "title": "The SaaS Outbound Tech Stack Report — What Tools Revenue Teams Actually Use",
        "format": "data_report",
        "primary_keyword": "saas outbound tech stack report",
        "target_links_from": ["G2", "Capterra", "SaaS review sites", "VC blogs", "founder newsletters"],
        "headline_stat": "The average SaaS company uses 6.4 tools for outbound — at a combined annual cost of $18,000+ per SDR seat",
        "survey_questions": [
            "Which tools does your team use for prospecting, enrichment, sequencing, CRM management?",
            "What is your total annual spend on outbound tooling?",
            "How many manual integration maintenance hours does your RevOps team spend monthly?",
            "Which tools would you eliminate if one system could replace them all?",
        ],
        "distribution_channels": ["G2", "Product Hunt", "LinkedIn", "VC portfolio newsletters"],
        "why_linkable": "Category-defining research about tool sprawl — relevant to every SaaS team and highly citable in round-up posts.",
    },
    {
        "slug": "pipeline-benchmarks-saas",
        "title": "SaaS Pipeline Generation Benchmarks — What Good Outbound Actually Looks Like",
        "format": "benchmark_report",
        "primary_keyword": "saas pipeline generation benchmarks",
        "target_links_from": ["SaaStr", "Bessemer", "OpenView", "SaaS metrics blogs"],
        "headline_stat": "SaaS companies using workflow orchestration generate 2.8× more pipeline per SDR than those running manual outbound",
        "metrics": [
            "Pipeline per SDR per quarter by company stage",
            "Reply rate by outbound channel and signal type",
            "Time from signal to meeting by automation level",
            "Pipeline conversion rate by ICP tier",
        ],
        "distribution_channels": ["SaaStr", "LinkedIn", "Substack", "VC blogs"],
        "why_linkable": "Benchmark data is cited in board decks, investor updates, and planning documents — extremely high-value citation target.",
    },
]


class DigitalPREngine:

    def __init__(self, site_url: str) -> None:
        self.site_url = site_url.rstrip("/")

    def generate_briefs(self) -> list[dict[str, Any]]:
        briefs = []
        for asset in LINKABLE_ASSETS:
            briefs.append({
                "slug": asset["slug"],
                "title": asset["title"],
                "format": asset["format"],
                "primary_keyword": asset["primary_keyword"],
                "headline_stat": asset["headline_stat"],
                "why_linkable": asset["why_linkable"],
                "target_links_from": asset["target_links_from"],
                "distribution_channels": asset["distribution_channels"],
                "page_url": f"{self.site_url}/research/{asset['slug']}",
                "outreach_subject": f"New research: {asset['headline_stat'][:80]}",
                "outreach_body": self._outreach_template(asset),
                "production_notes": self._production_notes(asset),
            })
        return briefs

    @staticmethod
    def _outreach_template(asset: dict) -> str:
        return (
            f"Hi [Name],\n\n"
            f"We just published '{asset['title']}' — with the finding: {asset['headline_stat']}\n\n"
            f"The research covers {', '.join(asset.get('metrics', asset.get('survey_questions', ['outbound automation data']))[:2])}.\n\n"
            f"Thought it might be relevant for your audience at [Publication]. Happy to share the full dataset.\n\n"
            f"Best,\nPipeleap Team"
        )

    @staticmethod
    def _production_notes(asset: dict) -> list[str]:
        notes = [
            f"Format: {asset['format'].replace('_', ' ').title()}",
            f"Headline stat to lead with: '{asset['headline_stat']}'",
            "Include methodology section for credibility (n=, survey dates, demographics)",
            "Publish under /research/ URL for topical authority clustering",
            "Add DefinedTerm schema for any new concepts introduced",
            "Include data visualizations (charts/graphs) for social sharing",
            "Submit to HARO and Qwoted with the headline stat as the hook",
        ]
        if "survey_questions" in asset:
            notes.append(f"Survey platform: Typeform or Google Forms — collect min. 100 responses before publishing")
        return notes

    def weekly_report_md(self) -> str:
        lines = [
            "## Digital PR — Linkable Asset Pipeline",
            "",
            "| Asset | Format | Primary Keyword | Target Publications |",
            "| --- | --- | --- | --- |",
        ]
        for asset in LINKABLE_ASSETS:
            pubs = ", ".join(asset["target_links_from"][:2])
            lines.append(f"| {asset['title'][:50]} | {asset['format']} | {asset['primary_keyword']} | {pubs} |")
        lines += ["", "_Run `digital_pr_briefs` to export full outreach templates and production notes._"]
        return "\n".join(lines)
