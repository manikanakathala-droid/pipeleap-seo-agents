"""
Directory Submission Content Generator

Generates submission-ready content for high-DA software directories.
Outputs a markdown file with copy-paste text for each directory.
Some directories offer APIs — those are flagged and handled separately.

Usage:
    python scripts/directory_submission_content.py [--output outputs/directory_submissions/]

Output:
    outputs/directory_submissions/submissions.md      — copy-paste content for all directories
    outputs/directory_submissions/submissions.json    — structured data for API-based submissions
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Site profile — single source of truth for all directory entries
# ---------------------------------------------------------------------------

@dataclass
class SiteProfile:
    brand: str = "Pipeleap"
    url: str = "https://www.pipeleap.com"
    tagline: str = "Sales Operations Platform for Outbound Teams"
    short_desc: str = (
        "Pipeleap is a sales operations platform that eliminates non-selling work "
        "by connecting enrichment, CRM sync, routing, and execution into one governed system."
    )
    long_desc: str = (
        "Pipeleap is a sales operations platform that eliminates non-selling work from your team's day. "
        "It orchestrates enrichment, CRM sync, routing, and execution into one governed system. "
        "Eleven connected modules run competitor research, ICP scoring, lead extraction, "
        "personalized outreach, sequence routing, and clean CRM handoff. "
        "Your team sells instead of administers."
    )
    categories: list[str] = field(default_factory=lambda: [
        "Sales Operations",
        "Sales Automation",
        "Revenue Operations",
        "Outbound Sales",
        "Workflow Automation",
        "Lead Enrichment",
        "CRM Automation",
    ])
    tags: list[str] = field(default_factory=lambda: [
        "sales ops",
        "outbound automation",
        "CRM sync",
        "lead enrichment",
        "sequence management",
        "sales workflow",
        "revenue operations",
        "pipeline generation",
    ])
    competitors: list[str] = field(default_factory=lambda: [
        "Clay", "Apollo.io", "Outreach", "Salesloft", "HubSpot", "Zenly", "Lemlist",
    ])
    tech_stack: list[str] = field(default_factory=lambda: [
        "n8n", "Python", "React", "Vite", "Supabase", "Vercel", "TypeScript", "Tailwind CSS",
    ])
    founded: str = "2024"
    headquarters: str = "Hyderabad, India"
    employees: str = "2"
    pricing: str = "Subscription-based"
    email: str = "info@pipeleap.com"
    social_linkedin: str = "https://linkedin.com/company/Pipeleap-com"
    social_twitter: str = "https://twitter.com/pipeleap"
    logo_url: str = "https://www.pipeleap.com/og-image.png"


# ---------------------------------------------------------------------------
# Directory definitions
# ---------------------------------------------------------------------------

SITEPROFILE = SiteProfile()

DIRECTORIES: list[dict[str, Any]] = [
    {
        "name": "G2",
        "url": "https://www.g2.com/products/pipeleap",
        "da": 90,
        "priority": 1,
        "status": "done",
        "type": "review_platform",
        "has_api": True,
        "submission_method": "User dashboard at g2.com/products/new",
        "category": "Sales Operations / Revenue Operations",
        "notes": "Listing already created. Update description, add screenshots, request reviews.",
        "fields": {
            "product_name": "Pipeleap",
            "tagline": "Sales Operations Platform for Outbound Teams",
            "description_short": "Pipeleap is a sales operations platform that connects enrichment, CRM sync, routing, and execution into one governed system.",
            "description_long": SITEPROFILE.long_desc,
            "categories": ["Sales Operations", "Revenue Operations", "Sales Automation"],
            "competitors": ["Clay", "Apollo.io", "Outreach", "Salesloft"],
            "pricing_model": "Subscription",
            "starting_price": "",
            "website": "https://www.pipeleap.com",
        },
    },
    {
        "name": "Crunchbase",
        "url": "https://www.crunchbase.com/organization/pipeleap",
        "da": 88,
        "priority": 1,
        "status": "done",
        "type": "company_database",
        "has_api": True,
        "submission_method": "Crunchbase Dashboard — claimed profile",
        "category": "Company Profile",
        "notes": "Profile claimed. Update description, add funding status, verify categories.",
        "fields": {
            "legal_name": "Pipeleap",
            "description_short": SITEPROFILE.short_desc,
            "description_long": SITEPROFILE.long_desc,
            "categories": ["Sales Automation", "Workflow Automation", "Revenue Operations"],
            "founded": "2024",
            "headquarters": "Hyderabad, India",
            "employees": "2",
            "website": "https://www.pipeleap.com",
        },
    },
    {
        "name": "Capterra",
        "url": "https://www.capterra.com",
        "da": 88,
        "priority": 1,
        "status": "pending",
        "type": "review_platform",
        "has_api": True,
        "submission_method": "capterra.com/customers/add-a-product — create vendor listing",
        "category": "Sales Automation Software",
        "notes": "Create listing in Sales Automation category. Part of Gartner network — syncs with GetApp and Software Advice.",
        "fields": {
            "product_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "description_long": SITEPROFILE.long_desc,
            "categories": ["Sales Automation", "Revenue Operations", "CRM Automation"],
            "competitors": ["Clay", "Apollo.io", "Outreach", "Salesloft", "HubSpot"],
            "pricing_model": "Subscription",
            "website": SITEPROFILE.url,
            "founded": "2024",
            "headquarters": SITEPROFILE.headquarters,
            "employees": SITEPROFILE.employees,
        },
    },
    {
        "name": "Product Hunt",
        "url": "https://www.producthunt.com",
        "da": 91,
        "priority": 1,
        "status": "pending",
        "type": "launch_platform",
        "has_api": True,
        "submission_method": "producthunt.com/posts/new — requires maker profile + product listing",
        "category": "Sales Operations / Productivity",
        "notes": "Create maker profile first. List Pipeleap as upcoming product. Coordinate launch for max visibility.",
        "fields": {
            "product_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "description_long": SITEPROFILE.long_desc,
            "categories": ["Sales Operations", "Productivity", "Automation"],
            "topics": ["sales", "automation", "SaaS", "B2B", "revenue operations"],
            "website": SITEPROFILE.url,
            "twitter_url": SITEPROFILE.social_twitter,
            "logo_url": SITEPROFILE.logo_url,
        },
    },
    {
        "name": "TrustRadius",
        "url": "https://www.trustradius.com",
        "da": 84,
        "priority": 1,
        "status": "pending",
        "type": "review_platform",
        "has_api": False,
        "submission_method": "trustradius.com/vendors/add — create vendor profile",
        "category": "Sales Operations / Revenue Operations",
        "notes": "Create vendor profile. Complete all sections for best visibility.",
        "fields": {
            "product_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "description_long": SITEPROFILE.long_desc,
            "categories": ["Sales Operations", "Revenue Operations", "Sales Automation"],
            "competitors": ["Clay", "Apollo.io", "HubSpot"],
            "website": SITEPROFILE.url,
            "founded": "2024",
            "headquarters": SITEPROFILE.headquarters,
        },
    },
    {
        "name": "AlternativeTo",
        "url": "https://www.alternativeto.net",
        "da": 78,
        "priority": 2,
        "status": "pending",
        "type": "alternative_listing",
        "has_api": False,
        "submission_method": "alternativeto.net — create software entry, then suggest as alternative",
        "category": "Sales Automation",
        "notes": "Create Pipeleap software entry. Then suggest as alternative to Clay, Apollo, Outreach, Salesloft.",
        "fields": {
            "product_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "description_long": SITEPROFILE.long_desc,
            "categories": ["Sales Operations", "Sales Automation", "Workflow Automation"],
            "tags": SITEPROFILE.tags,
            "competitors": ["Clay", "Apollo.io", "Outreach", "Salesloft", "Lemlist", "Zenly"],
            "website": SITEPROFILE.url,
            "license": "Commercial",
            "platforms": ["Web"],
        },
    },
    {
        "name": "SaaSWorthy",
        "url": "https://www.saasworthy.com",
        "da": 72,
        "priority": 2,
        "status": "pending",
        "type": "software_directory",
        "has_api": False,
        "submission_method": "saasworthy.com/add-product — create product listing",
        "category": "Sales Automation / Revenue Operations",
        "notes": "Create listing in Sales Automation or Revenue Operations categories.",
        "fields": {
            "product_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "description_long": SITEPROFILE.long_desc,
            "categories": ["Sales Automation", "Revenue Operations", "CRM"],
            "tags": SITEPROFILE.tags,
            "pricing_model": "Subscription",
            "website": SITEPROFILE.url,
            "founded": "2024",
            "headquarters": SITEPROFILE.headquarters,
        },
    },
    {
        "name": "Stackshare",
        "url": "https://www.stackshare.io",
        "da": 66,
        "priority": 2,
        "status": "pending",
        "type": "tech_stack",
        "has_api": False,
        "submission_method": "stackshare.io — create company profile, add Pipeleap's tech stack",
        "category": "Developer / Tech Stack",
        "notes": "Create company profile and list tools Pipeleap uses. Good for developer audience backlinks.",
        "fields": {
            "company_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "website": SITEPROFILE.url,
            "tech_stack": SITEPROFILE.tech_stack,
            "categories": ["Sales", "Automation", "Revenue Operations"],
        },
    },
    {
        "name": "SourceForge",
        "url": "https://sourceforge.net",
        "da": 78,
        "priority": 3,
        "status": "pending",
        "type": "software_directory",
        "has_api": False,
        "submission_method": "sourceforge.net — create project listing in Business / Sales category",
        "category": "Business / Sales Software",
        "notes": "Create open source / commercial project listing.",
        "fields": {
            "product_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "description_long": SITEPROFILE.long_desc,
            "categories": ["Sales", "CRM", "Business"],
            "tags": SITEPROFILE.tags,
            "website": SITEPROFILE.url,
            "license": "Commercial",
            "platforms": ["Web"],
        },
    },
    {
        "name": "GetApp",
        "url": "https://www.getapp.com",
        "da": 86,
        "priority": 2,
        "status": "pending",
        "type": "review_platform",
        "has_api": True,
        "submission_method": "Part of Capterra/Gartner network — listing may propagate automatically from Capterra",
        "category": "Sales Automation",
        "notes": "Part of Gartner Digital Markets (same network as Capterra + Software Advice). Check if listing auto-propagates after Capterra submission.",
        "fields": {
            "product_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "description_long": SITEPROFILE.long_desc,
            "categories": ["Sales Automation", "Revenue Operations"],
            "competitors": ["Clay", "Apollo.io", "Outreach", "Salesloft"],
            "pricing_model": "Subscription",
            "website": SITEPROFILE.url,
        },
    },
    {
        "name": "Software Advice",
        "url": "https://www.softwareadvice.com",
        "da": 83,
        "priority": 2,
        "status": "pending",
        "type": "review_platform",
        "has_api": True,
        "submission_method": "Same Gartner network as Capterra. Verify listing auto-propagates.",
        "category": "Sales Automation",
        "notes": "Same Gartner network as Capterra. Check if propagation is automatic after Capterra submission.",
        "fields": {
            "product_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "description_long": SITEPROFILE.long_desc,
            "categories": ["Sales Automation", "Revenue Operations"],
            "competitors": ["Clay", "Apollo.io", "Outreach", "Salesloft"],
            "pricing_model": "Subscription",
            "website": SITEPROFILE.url,
        },
    },
    {
        "name": "Slashdot",
        "url": "https://slashdot.org",
        "da": 82,
        "priority": 3,
        "status": "pending",
        "type": "software_directory",
        "has_api": False,
        "submission_method": "slashdot.org — submit to software directory section",
        "category": "Business / Technology",
        "notes": "Submit to software directory. Slashdot has a technology news audience.",
        "fields": {
            "product_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "description_long": SITEPROFILE.long_desc,
            "categories": ["Sales", "Automation", "Business Software"],
            "tags": SITEPROFILE.tags,
            "website": SITEPROFILE.url,
        },
    },
    {
        "name": "GetLatka",
        "url": "https://www.getlatka.com",
        "da": 68,
        "priority": 3,
        "status": "pending",
        "type": "saas_database",
        "has_api": False,
        "submission_method": "getlatka.com — claim SaaS company profile",
        "category": "SaaS Company Database",
        "notes": "Claim Pipeleap's SaaS company profile on GetLatka (SaaS revenue database).",
        "fields": {
            "company_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "description_long": SITEPROFILE.long_desc,
            "categories": ["Sales Operations", "Revenue Operations", "SaaS"],
            "website": SITEPROFILE.url,
            "founded": "2024",
            "headquarters": SITEPROFILE.headquarters,
            "employees": SITEPROFILE.employees,
        },
    },
    {
        "name": "LinkedIn",
        "url": "https://linkedin.com/company/pipeleap",
        "da": 95,
        "priority": 1,
        "status": "pending",
        "type": "social_profile",
        "has_api": True,
        "submission_method": "linkedin.com/company — update company page with website URL",
        "category": "Company Profile",
        "notes": "Ensure company page has website URL in profile. This creates a backlink from LinkedIn's DA95 domain.",
        "fields": {
            "company_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "description_long": SITEPROFILE.long_desc,
            "website": SITEPROFILE.url,
            "categories": ["Sales Operations", "Software", "Technology"],
            "founded": "2024",
            "headquarters": SITEPROFILE.headquarters,
            "employees": SITEPROFILE.employees,
        },
    },
    {
        "name": "Glassdoor",
        "url": "https://www.glassdoor.com",
        "da": 85,
        "priority": 3,
        "status": "pending",
        "type": "employer_profile",
        "has_api": False,
        "submission_method": "glassdoor.com — create employer profile",
        "category": "Employer / Company Profile",
        "notes": "Create employer profile for Pipeleap. Requires company verification.",
        "fields": {
            "company_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "description_long": SITEPROFILE.long_desc,
            "website": SITEPROFILE.url,
            "founded": "2024",
            "headquarters": SITEPROFILE.headquarters,
            "employees": SITEPROFILE.employees,
            "categories": ["Software", "Sales", "Technology"],
        },
    },
    {
        "name": "Clutch.co",
        "url": "https://clutch.co",
        "da": 82,
        "priority": 1,
        "status": "pending",
        "type": "b2b_directory",
        "has_api": False,
        "submission_method": "clutch.co — create company profile in Sales / GTM category",
        "category": "Sales Consulting / GTM",
        "notes": "Create B2B company profile. Good for agency/service positioning backlinks.",
        "fields": {
            "company_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "description_long": SITEPROFILE.long_desc,
            "categories": ["Sales Operations", "Revenue Operations", "GTM"],
            "website": SITEPROFILE.url,
            "founded": "2024",
            "headquarters": SITEPROFILE.headquarters,
            "employees": SITEPROFILE.employees,
        },
    },
    {
        "name": "Trustpilot",
        "url": "https://www.trustpilot.com",
        "da": 92,
        "priority": 2,
        "status": "pending",
        "type": "review_platform",
        "has_api": True,
        "submission_method": "trustpilot.com — create business profile",
        "category": "Business Services",
        "notes": "Create business profile and request reviews from early users. DA92 backlink.",
        "fields": {
            "company_name": "Pipeleap",
            "website": SITEPROFILE.url,
            "categories": ["Sales", "Software", "Business Services"],
        },
    },
    {
        "name": "Indie Hackers",
        "url": "https://www.indiehackers.com",
        "da": 74,
        "priority": 3,
        "status": "pending",
        "type": "community",
        "has_api": False,
        "submission_method": "indiehackers.com — create founder story / product page",
        "category": "Founder Story",
        "notes": "Create founder story post about Pipeleap. Links from IH are nofollow but drive referral traffic.",
        "fields": {
            "company_name": "Pipeleap",
            "tagline": SITEPROFILE.tagline,
            "description_short": SITEPROFILE.short_desc,
            "website": SITEPROFILE.url,
            "founded": "2024",
        },
    },
]


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def build_markdown(dirs: list[dict]) -> str:
    lines = [
        "# Directory Submission Content — Pipeleap",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "---",
        "",
        "## Site Profile (use for all directories)",
        "",
        f"| Field | Value |",
        "|---|---|",
        f"| Company | {SITEPROFILE.brand} |",
        f"| URL | {SITEPROFILE.url} |",
        f"| Tagline | {SITEPROFILE.tagline} |",
        f"| Short Description | {SITEPROFILE.short_desc} |",
        f"| Categories | {', '.join(SITEPROFILE.categories)} |",
        f"| Tags | {', '.join(SITEPROFILE.tags)} |",
        f"| Competitors | {', '.join(SITEPROFILE.competitors)} |",
        f"| Tech Stack | {', '.join(SITEPROFILE.tech_stack)} |",
        f"| Founded | {SITEPROFILE.founded} |",
        f"| HQ | {SITEPROFILE.headquarters} |",
        f"| Employees | {SITEPROFILE.employees} |",
        f"| Pricing | {SITEPROFILE.pricing} |",
        f"| Email | {SITEPROFILE.email} |",
        f"| LinkedIn | {SITEPROFILE.social_linkedin} |",
        "",
        "---",
        "",
        "## Directory Breakdown",
        "",
    ]

    pending = [d for d in dirs if d["status"] == "pending"]
    done = [d for d in dirs if d["status"] == "done"]

    if pending:
        lines.append(f"### Pending ({len(pending)} directories)")
        lines.append("")
        for d in pending:
            fields = d["fields"]
            lines.append(f"#### {d['name']} (DA {d['da']})")
            lines.append("")
            lines.append(f"**URL:** {d['url']}")
            lines.append(f"**Priority:** P{d['priority']}")
            lines.append(f"**Type:** {d['type']}")
            lines.append(f"**Category on platform:** {d['category']}")
            lines.append(f"**Submission:** {d['submission_method']}")
            lines.append(f"**Notes:** {d['notes']}")
            lines.append(f"**Has API:** {'Yes' if d['has_api'] else 'No — manual browser submission'}")
            lines.append("")
            lines.append("**Description (short):**")
            lines.append("```")
            lines.append(fields.get("description_short", ""))
            lines.append("```")
            lines.append("")
            if "description_long" in fields:
                lines.append("**Description (long):**")
                lines.append("```")
                lines.append(fields["description_long"])
                lines.append("```")
                lines.append("")
            if "categories" in fields:
                lines.append(f"**Categories to select:** {', '.join(fields['categories'])}")
            if "tags" in fields:
                lines.append(f"**Tags:** {', '.join(fields['tags'])}")
            if "competitors" in fields:
                lines.append(f"**Competitors to list:** {', '.join(fields['competitors'])}")
            if "tagline" in fields:
                lines.append(f"**Tagline:** {fields['tagline']}")
            if "pricing_model" in fields:
                lines.append(f"**Pricing model:** {fields['pricing_model']}")
            if "headquarters" in fields:
                lines.append(f"**Location:** {fields.get('headquarters', SITEPROFILE.headquarters)}")
            if "founded" in fields:
                lines.append(f"**Founded:** {fields.get('founded', SITEPROFILE.founded)}")
            if "employees" in fields:
                lines.append(f"**Employees:** {fields.get('employees', SITEPROFILE.employees)}")
            if "tech_stack" in fields:
                lines.append(f"**Tech stack:** {', '.join(fields['tech_stack'])}")
            if "platforms" in fields:
                lines.append(f"**Platforms:** {', '.join(fields['platforms'])}")
            lines.append("")
            lines.append("**Screenshot suggestions:**")
            lines.append("- Pipeleap dashboard — main workflow overview")
            lines.append("- Outbound sequence builder / editor view")
            lines.append("- Integration settings page (showing connected tools)")
            lines.append("- Pipeline / analytics dashboard")
            lines.append("")
            lines.append("---")
            lines.append("")

    if done:
        lines.append(f"### Done ({len(done)} directories)")
        lines.append("")
        for d in done:
            lines.append(f"- **{d['name']}** (DA {d['da']}) — {d['url']}")
        lines.append("")

    return "\n".join(lines)


def build_json(dirs: list[dict]) -> list[dict]:
    result = []
    for d in dirs:
        entry = {
            "name": d["name"],
            "url": d["url"],
            "da": d["da"],
            "priority": d["priority"],
            "status": d["status"],
            "type": d["type"],
            "has_api": d["has_api"],
            "submission_method": d["submission_method"],
            "category": d["category"],
            "notes": d["notes"],
            "fields": d["fields"],
        }
        result.append(entry)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate directory submission content for Pipeleap"
    )
    parser.add_argument(
        "--output",
        default="outputs/directory_submissions",
        help="Output directory (default: outputs/directory_submissions)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Markdown output
    md = build_markdown(DIRECTORIES)
    md_path = output_dir / "submissions.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"Written: {md_path}")

    # JSON output
    js = build_json(DIRECTORIES)
    js_path = output_dir / "submissions.json"
    js_path.write_text(json.dumps(js, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written: {js_path}")

    # Summary
    total = len(DIRECTORIES)
    pending = sum(1 for d in DIRECTORIES if d["status"] == "pending")
    done = total - pending
    with_api = sum(1 for d in DIRECTORIES if d["has_api"] and d["status"] == "pending")
    print(f"\nSummary: {total} directories — {done} done, {pending} pending")
    print(f"Pending with API access: {with_api} (can be automated)")
    print(f"Pending manual submission: {pending - with_api}")


if __name__ == "__main__":
    main()
