"""
Build a comprehensive tool database.

Reads existing tools from frontend TS files, then uses LLM (GitHub Models) to generate
additional tools per category. Merges and deduplicates by slug and website domain.
Outputs tool_database.json for the ToolsPageGenerator to consume.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from connectors.llm_client import LLMClient

FRONTEND_TOOLS_DIR = Path(__file__).resolve().parent.parent / "temp_frontend_repo" / "src" / "data" / "tools"
DATABASE_PATH = Path(__file__).resolve().parent.parent / "modules" / "pipeleap_seo_engine" / "data" / "tool_database.json"

CATEGORY_MAP = {
    "ai-sdr-tools": "AI SDR Tools",
    "cold-email-tools": "Cold Email Tools",
    "sales-engagement-tools": "Sales Engagement Platforms",
    "prospecting-tools": "Prospecting Tools",
    "lead-enrichment-tools": "Lead Enrichment Tools",
    "crm-tools": "CRM Platforms",
    "call-recording-tools": "Call Recording & Conversation Intelligence Tools",
    "revenue-intelligence-tools": "Revenue Intelligence Platforms",
    "linkedin-automation-tools": "LinkedIn Automation Tools",
    "ai-outbound-agents": "AI Outbound Agents",
    "workflow-automation-tools": "Workflow Automation Tools",
    "sales-analytics-tools": "Sales Analytics Tools",
    "gtm-engineering-tools": "GTM Engineering Tools",
}

CATEGORY_PROMPTS = {
    "ai-sdr-tools": "AI-powered sales development representative (SDR) tools that automate prospecting, outreach, and follow-up",
    "cold-email-tools": "Cold email outreach and deliverability tools for B2B sales teams",
    "sales-engagement-tools": "Sales engagement platforms for managing multi-channel sequences, cadences, and rep activity",
    "prospecting-tools": "B2B prospecting and contact database tools for finding and targeting potential customers",
    "lead-enrichment-tools": "Lead enrichment and data append tools that add firmographic, technographic, and contact data to leads",
    "crm-tools": "Customer relationship management (CRM) platforms for tracking contacts, deals, and pipeline",
    "call-recording-tools": "Call recording and conversation intelligence tools for sales call analysis and coaching",
    "revenue-intelligence-tools": "Revenue intelligence and forecasting platforms that consolidate sales signals for pipeline accuracy",
    "linkedin-automation-tools": "LinkedIn automation tools for scaling connection requests, messages, and profile engagement",
    "ai-outbound-agents": "Autonomous AI outbound agents that orchestrate end-to-end outbound workflows without human intervention",
    "workflow-automation-tools": "Workflow automation and orchestration platforms for connecting sales tools and automating processes",
    "sales-analytics-tools": "Sales analytics and business intelligence tools for reporting, forecasting, and pipeline analysis",
    "gtm-engineering-tools": "GTM engineering and data infrastructure tools for signal-based go-to-market motions",
}


def parse_ts_tool_entries(text: str) -> list[dict]:
    """Extract tool entries from a TypeScript Tool[] file."""
    tools = []
    slug_pattern = re.compile(r"slug:\s*\"([^\"]+)\"")
    name_pattern = re.compile(r"name:\s*\"([^\"]+)\"")
    website_pattern = re.compile(r"website:\s*\"([^\"]+)\"")
    category_slug_pattern = re.compile(r"categorySlug:\s*\"([^\"]+)\"")

    blocks = re.split(r"},\s*\{", text)
    for block in blocks:
        slug_m = slug_pattern.search(block)
        name_m = name_pattern.search(block)
        website_m = website_pattern.search(block)
        cat_m = category_slug_pattern.search(block)
        if slug_m and name_m:
            tools.append({
                "slug": slug_m.group(1),
                "name": name_m.group(1),
                "website": website_m.group(1) if website_m else "",
                "categorySlug": cat_m.group(1) if cat_m else "",
            })
    return tools


def load_existing_tools() -> dict[str, dict]:
    """Load all existing tools from frontend TS files. Returns dict keyed by slug."""
    slug_map: dict[str, dict] = {}
    for cat_slug in CATEGORY_MAP:
        ts_path = FRONTEND_TOOLS_DIR / f"{cat_slug}.ts"
        if not ts_path.exists():
            print(f"  WARNING: Category file not found: {ts_path.name}")
            continue
        text = ts_path.read_text(encoding="utf-8")
        entries = parse_ts_tool_entries(text)
        for t in entries:
            if t["slug"] in slug_map:
                print(f"  WARNING: Duplicate slug '{t['slug']}' found in {ts_path.name}")
            t["_source"] = "existing"
            slug_map[t["slug"]] = t
    print(f"  Loaded {len(slug_map)} existing tools from {len(CATEGORY_MAP)} category files")
    return slug_map


def build_domain_map(slug_map: dict[str, dict]) -> dict[str, str]:
    """Map domain → slug for dedup."""
    dmap: dict[str, str] = {}
    for slug, t in slug_map.items():
        if t.get("website"):
            domain = extract_domain(t["website"])
            if domain:
                dmap[domain] = slug
    return dmap


def extract_domain(url: str) -> str:
    m = re.search(r"https?://([^/]+)", url)
    return m.group(1).lower().removeprefix("www.") if m else ""


def normalize_name(name: str) -> str:
    return name.strip().lower().replace(".", "").replace("-", " ").replace("  ", " ")


def llm_prompt_for_category(cat_slug: str, cat_name: str, description: str, llm: LLMClient) -> str:
    prompt = f"""You are building a comprehensive database of B2B sales and marketing tools.

Category: {cat_name} ({cat_slug})
Description: {description}

List 50-80 B2B tools in this category. For each tool provide:
- name (exact product name)
- description (1-2 sentences explaining what the tool does)
- website URL (the tool's official website)
- pricing_model: one of "Free", "Freemium", "Paid", "Contact"
- starting_price: e.g. "$49/mo", "$15,000/yr", or "" if unknown
- has_free_tier: true/false
- pricing_url: direct URL to the tool's pricing page (usually tool.com/pricing)

Return ONLY valid JSON. Format:
[
  {{
    "name": "Tool Name",
    "description": "What it does...",
    "website": "https://tool.com",
    "pricing_model": "Paid",
    "starting_price": "$49/mo",
    "has_free_tier": false,
    "pricing_url": "https://tool.com/pricing"
  }}
]

Include well-known tools first. Focus on real, active products. Do NOT include placeholder or invented tools."""
    return llm.generate(prompt)


def parse_llm_response(text: str) -> list[dict]:
    """Parse JSON from LLM response. Handles markdown code fences."""
    if not text:
        return []
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    bracket_start = text.find("[")
    bracket_end = text.rfind("]")
    if bracket_start != -1 and bracket_end > bracket_start:
        try:
            data = json.loads(text[bracket_start:bracket_end+1])
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
    return []


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def main():
    print("=" * 60)
    print("Tool Database Builder")
    print("=" * 60)

    llm = LLMClient()
    if not llm.is_configured:
        print("ERROR: No GitHub token (GITHUB_TOKEN / LAUNCHPAD_DEPLOY_TOKEN) set. Cannot generate tool database.")
        sys.exit(1)

    # Step 1: Load existing tools
    print("\n[1/4] Loading existing tools from frontend...")
    slug_map = load_existing_tools()
    domain_map = build_domain_map(slug_map)
    existing_slugs = set(slug_map.keys())

    # Step 2: Generate new tools per category via LLM
    print("\n[2/4] Generating tools per category via LLM (GitHub Models)...")
    all_new_tools: list[dict] = []
    for cat_slug, cat_name in CATEGORY_MAP.items():
        desc = CATEGORY_PROMPTS[cat_slug]
        print(f"\n  --- {cat_name} ---")
        print(f"  Asking LLM for tools...")
        resp = llm_prompt_for_category(cat_slug, cat_name, desc, llm)
        new_tools = parse_llm_response(resp)
        print(f"  Got {len(new_tools)} tools from LLM")

        # Tag with category
        for t in new_tools:
            t["categorySlug"] = cat_slug
            t["slug"] = slugify(t.get("name", ""))
            t["_source"] = "llm"

        # Filter: skip if slug or domain already exists
        before = len(new_tools)
        filtered = []
        for t in new_tools:
            s = t["slug"]
            if s in existing_slugs:
                continue
            if t.get("website"):
                domain = extract_domain(t["website"])
                if domain and domain in domain_map:
                    continue
            filtered.append(t)

        # Also dedup among new tools in this batch
        batch_slugs: set[str] = set()
        unique_filtered = []
        for t in filtered:
            s = t["slug"]
            if s in batch_slugs:
                continue
            batch_slugs.add(s)
            unique_filtered.append(t)

        skipped = before - len(unique_filtered)
        if skipped:
            print(f"  Skipped {skipped} duplicates")
        all_new_tools.extend(unique_filtered)
        print(f"  Added {len(unique_filtered)} new tools")

        # Rate limit respect
        if cat_slug != list(CATEGORY_MAP.keys())[-1]:
            time.sleep(2)

    # Step 3: Build merged list
    print(f"\n[3/4] Building merged database...")
    merged_tools: list[dict] = []

    # Add existing tools first
    for slug, t in slug_map.items():
        merged_tools.append({
            "slug": t["slug"],
            "name": t["name"],
            "categorySlug": t.get("categorySlug", ""),
            "description": "",
            "website": t.get("website", ""),
            "pricing_model": "Contact",
            "starting_price": "",
            "has_free_tier": False,
            "pricing_url": "",
            "_source": "existing",
        })
    print(f"  Existing: {len(slug_map)}")

    # Add new tools
    for t in all_new_tools:
        merged_tools.append({
            "slug": t["slug"],
            "name": t.get("name", ""),
            "categorySlug": t.get("categorySlug", ""),
            "description": t.get("description", ""),
            "website": t.get("website", ""),
            "pricing_model": t.get("pricing_model", "Contact"),
            "starting_price": t.get("starting_price", ""),
            "has_free_tier": bool(t.get("has_free_tier", False)),
            "pricing_url": t.get("pricing_url", ""),
            "_source": "llm",
        })
    print(f"  New from LLM: {len(all_new_tools)}")
    print(f"  Total merged: {len(merged_tools)}")

    # Step 4: Write database
    print(f"\n[4/4] Writing tool_database.json...")
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    db = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "categories": list(CATEGORY_MAP.keys()),
        "total_tools": len(merged_tools),
        "tools": merged_tools,
    }
    DATABASE_PATH.write_text(json.dumps(db, indent=2), encoding="utf-8")
    print(f"  Written to {DATABASE_PATH}")
    print(f"\n{'=' * 60}")
    print(f"Done! Database has {len(merged_tools)} tools across {len(CATEGORY_MAP)} categories")
    print(f"  Existing:  {len(slug_map)}")
    print(f"  New:       {len(all_new_tools)}")


if __name__ == "__main__":
    main()
