"""
Generate a comprehensive B2B sales and marketing tool database.

Reads existing tools from frontend TS files, merges with a curated list
of new tools per category, deduplicates by slug and website domain,
and outputs tool_database.json.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FRONTEND_TOOLS_DIR = Path(__file__).resolve().parent.parent / "temp_frontend_repo" / "src" / "data" / "tools"
DATABASE_PATH = Path(__file__).resolve().parent.parent / "modules" / "pipeleap_seo_engine" / "data" / "tool_database.json"

CATEGORIES = [
    "ai-sdr-tools",
    "cold-email-tools",
    "sales-engagement-tools",
    "prospecting-tools",
    "lead-enrichment-tools",
    "crm-tools",
    "call-recording-tools",
    "revenue-intelligence-tools",
    "linkedin-automation-tools",
    "ai-outbound-agents",
    "workflow-automation-tools",
    "sales-analytics-tools",
    "gtm-engineering-tools",
]


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def extract_domain(url: str) -> str:
    m = re.search(r"https?://([^/]+)", url)
    return m.group(1).lower().removeprefix("www.") if m else ""


def parse_ts_tool_entries(text: str) -> list[dict]:
    tools = []
    slug_re = re.compile(r"slug:\s*\"([^\"]+)\"")
    name_re = re.compile(r"name:\s*\"([^\"]+)\"")
    website_re = re.compile(r"website:\s*\"([^\"]+)\"")
    cat_re = re.compile(r"categorySlug:\s*\"([^\"]+)\"")
    blocks = re.split(r"},\s*\{", text)
    for block in blocks:
        slug_m = slug_re.search(block)
        name_m = name_re.search(block)
        if slug_m and name_m:
            tools.append({
                "slug": slug_m.group(1),
                "name": name_m.group(1),
                "website": website_re.search(block).group(1) if website_re.search(block) else "",
                "categorySlug": cat_re.search(block).group(1) if cat_re.search(block) else "",
            })
    return tools


def load_existing_tools():
    slug_map = {}
    for cat in CATEGORIES:
        ts_path = FRONTEND_TOOLS_DIR / f"{cat}.ts"
        if not ts_path.exists():
            print(f"  WARNING: {ts_path.name} not found")
            continue
        text = ts_path.read_text(encoding="utf-8")
        entries = parse_ts_tool_entries(text)
        for t in entries:
            t["_source"] = "existing"
            slug_map[t["slug"]] = t
    print(f"  Loaded {len(slug_map)} existing tools from TS files")
    return slug_map


def build_domain_map(slug_map):
    dmap = {}
    for slug, t in slug_map.items():
        domain = extract_domain(t.get("website", ""))
        if domain:
            dmap[domain] = slug
    return dmap


# ---------------------------------------------------------------------------
# New tools per category
# ---------------------------------------------------------------------------

NEW_TOOLS: dict[str, list[dict]] = {
    # -----------------------------------------------------------------------
    "ai-sdr-tools": [
        {"name": "Clara Labs", "website": "https://www.clara.com", "description": "AI scheduling assistant that handles email-based meeting coordination and calendar management.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.clara.com/pricing"},
        {"name": "Nooks.ai", "website": "https://nooks.ai", "description": "AI-powered SDR platform that automates prospect research, dialing, and multi-channel outreach sequences.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://nooks.ai/pricing"},
        {"name": "People.ai SDR", "website": "https://people.ai", "description": "AI-driven sales execution platform that captures rep activities and automates SDR workflows.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Drift SDR", "website": "https://www.drift.com", "description": "Conversational AI SDR that engages website visitors in real-time to qualify and route leads.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.drift.com/pricing"},
        {"name": "Intercom Fin AI SDR", "website": "https://www.intercom.com/fin", "description": "AI-powered customer service and SDR bot that answers questions and qualifies leads autonomously.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.intercom.com/pricing"},
        {"name": "HubSpot Breeze AI SDR", "website": "https://www.hubspot.com/products/sales/breeze", "description": "HubSpot's AI SDR assistant that automates prospect research, email personalisation, and follow-up sequences.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.hubspot.com/pricing"},
        {"name": "Zeli", "website": "https://zeli.app", "description": "AI-powered prospecting and enrichment tool that finds and verifies B2B contact data at scale.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Akkio", "website": "https://akkio.com", "description": "No-code AI platform for sales teams to build predictive models for lead scoring and pipeline forecasting.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://akkio.com/pricing"},
        {"name": "Lavender.ai", "website": "https://www.lavender.ai", "description": "AI email coach that provides real-time personalisation and effectiveness scoring for cold emails.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.lavender.ai/pricing"},
        {"name": "Seamless.ai SDR", "website": "https://seamless.ai", "description": "AI-powered contact database and SDR platform with real-time phone and email data.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://seamless.ai/pricing"},
        {"name": "LeadIQ SDR", "website": "https://leadiq.com", "description": "Sales prospecting and SDR platform that captures and enriches leads with one-click CRM sync.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://leadiq.com/pricing"},
        {"name": "Lusha SDR", "website": "https://www.lusha.com", "description": "AI-enhanced contact data platform for SDR teams to find and verify prospect phone numbers and emails.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.lusha.com/pricing"},
        {"name": "Saleswhale", "website": "https://www.zendesk.com", "description": "AI conversational lead qualification platform (acquired by Zendesk) that automates email-based prospect conversations.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Drift Amelia", "website": "https://www.drift.com/amelia", "description": "Drift's AI meeting bot that books meetings from email conversations without human intervention.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.drift.com/pricing"},
        {"name": "Drift Conversational SDR", "website": "https://www.drift.com", "description": "Drift's AI chatbot that engages, qualifies, and routes website visitors as a conversational SDR.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.drift.com/pricing"},
        {"name": "Overloop", "website": "https://overloop.com", "description": "Multi-channel SDR platform combining cold email, LinkedIn, and phone sequences with AI automation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://overloop.com/pricing"},
        {"name": "Amplemarket AI SDR", "website": "https://amplemarket.com", "description": "AI-powered sales engagement platform with automated prospecting, enrichment, and multi-channel outreach.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://amplemarket.com/pricing"},
        {"name": "Kaspr AI", "website": "https://www.kaspr.com", "description": "AI-enhanced B2B prospecting tool for finding and verifying contact numbers with intelligent lead scoring.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.kaspr.com/pricing"},
        {"name": "Wiza AI", "website": "https://wiza.co", "description": "AI-powered LinkedIn prospect extractor and email finder for SDR teams building targeted outbound lists.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://wiza.co/pricing"},
        {"name": "GetProspect AI", "website": "https://getprospect.com", "description": "AI-assisted email finder and prospect enrichment tool that verifies contacts in real-time.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://getprospect.com/pricing"},
        {"name": "RocketReach AI", "website": "https://rocketreach.co", "description": "AI-powered B2B contact database with intent scoring and enrichment for SDR outbound campaigns.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://rocketreach.co/pricing"},
    ],
    # -----------------------------------------------------------------------
    "cold-email-tools": [
        {"name": "MixMax Engage", "website": "https://www.mixmax.com", "description": "Cold email and sales engagement platform with scheduling, templates, and multi-channel sequencing.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.mixmax.com/pricing"},
        {"name": "Yesware", "website": "https://www.yesware.com", "description": "Cold email tracking and engagement platform for sales teams with templates and analytics.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.yesware.com/pricing"},
        {"name": "Constant Contact Cold Email", "website": "https://www.constantcontact.com", "description": "Email marketing and cold email platform with list management and deliverability tools for small businesses.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.constantcontact.com/pricing"},
        {"name": "MailerLite Cold Email", "website": "https://www.mailerlite.com", "description": "Affordable email marketing platform with cold email automation, landing pages, and deliverability features.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.mailerlite.com/pricing"},
        {"name": "SendGrid Sales", "website": "https://sendgrid.com", "description": "Email delivery and cold email infrastructure platform with APIs for high-volume sales communications.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://sendgrid.com/pricing"},
        {"name": "Brevo Sales (Sendinblue)", "website": "https://www.brevo.com", "description": "Cold email and marketing automation platform with CRM integration and deliverability optimisation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.brevo.com/pricing"},
        {"name": "GMass", "website": "https://www.gmass.co", "description": "Cold email and mail merge tool for Gmail with tracking, scheduling, and automated follow-up sequences.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.gmass.co/pricing"},
        {"name": "Mailmeteor", "website": "https://mailmeteor.com", "description": "Cold email and mail merge tool for Google Workspace with tracking and personalisation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://mailmeteor.com/pricing"},
        {"name": "Yet Another Mail Merge (YAMM)", "website": "https://yamm.com", "description": "Mail merge tool for Gmail that sends personalised cold emails and tracks opens and clicks.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://yamm.com/pricing"},
        {"name": "Stripo.email", "website": "https://stripo.email", "description": "Email template builder for cold email campaigns with drag-and-drop editor and responsive designs.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://stripo.email/pricing"},
        {"name": "Beefree", "website": "https://beefree.io", "description": "Drag-and-drop email builder for creating professional cold email templates with responsive design.", "pricing_model": "Free", "starting_price": "$0/mo", "has_free_tier": True, "pricing_url": "https://beefree.io/pricing"},
        {"name": "Mailtrack.io", "website": "https://mailtrack.io", "description": "Email tracking tool for Gmail and Outlook that notifies when cold emails are opened.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://mailtrack.io/pricing"},
        {"name": "HubSpot Sales Cold Email", "website": "https://www.hubspot.com/products/sales", "description": "HubSpot's cold email features with templates, sequencing, tracking, and CRM integration.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.hubspot.com/pricing"},
        {"name": "Right Inbox", "website": "https://www.rightinbox.com", "description": "Email productivity tool for Gmail with tracking, templates, send later, and follow-up reminders.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.rightinbox.com/pricing"},
        {"name": "Bananatag", "website": "https://bananatag.com", "description": "Email tracking platform that monitors opens, clicks, and attachments for cold email campaigns.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://bananatag.com/pricing"},
        {"name": "Boomerang", "website": "https://www.boomeranggmail.com", "description": "Email scheduling and follow-up tool for Gmail with send later, reminders, and response tracking.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.boomeranggmail.com/pricing"},
        {"name": "Snov.io", "website": "https://snov.io", "description": "Cold email outreach platform with built-in email finder, verification, and sequence automation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://snov.io/pricing"},
        {"name": "Warmbox", "website": "https://warmbox.ai", "description": "AI-powered cold email warm-up tool that improves deliverability by simulating natural inbox engagement.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://warmbox.ai/pricing"},
        {"name": "Mailflow", "website": "https://mailflow.com", "description": "Cold email outreach platform with smart scheduling, deliverability optimisation, and reply management.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://mailflow.com/pricing"},
        {"name": "EmailTree.ai", "website": "https://emailtree.ai", "description": "AI-powered email automation tool that learns from past replies to automate personalised cold email responses.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Warmer.ai", "website": "https://warmer.ai", "description": "AI email warm-up platform that improves sender reputation and cold email deliverability.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://warmer.ai/pricing"},
        {"name": "Pipl.ai", "website": "https://pipl.ai", "description": "Cold email platform with AI personalisation and unlimited sending accounts for high-volume outreach.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://pipl.ai/pricing"},
        {"name": "MillionVerifier", "website": "https://millionverifier.com", "description": "Email verification and list cleaning service that improves cold email deliverability by removing invalid addresses.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://millionverifier.com/pricing"},
        {"name": "ZeroBounce", "website": "https://www.zerobounce.net", "description": "Email verification and data quality platform for cleaning cold email lists and improving deliverability.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.zerobounce.net/pricing"},
        {"name": "NeverBounce", "website": "https://neverbounce.com", "description": "Real-time email verification and list cleaning service for cold email campaigns.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://neverbounce.com/pricing"},
        {"name": "Kickbox", "website": "https://kickbox.com", "description": "Email verification API and list cleaning tool that detects invalid, risky, and catch-all email addresses.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://kickbox.com/pricing"},
    ],
    # -----------------------------------------------------------------------
    "sales-engagement-tools": [
        {"name": "VanillaSoft", "website": "https://www.vanillasoft.com", "description": "Sales engagement platform with lead distribution, multi-channel sequencing, and progressive dialling.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Mem", "website": "https://mem.ai", "description": "AI-powered knowledge management and engagement platform for sales teams to organise and act on prospect information.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://mem.ai/pricing"},
        {"name": "XANT (InsideSales.com)", "website": "https://xant.ai", "description": "AI-powered sales engagement platform with predictive analytics, sequencing, and conversation intelligence.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "ConnectLeader", "website": "https://www.connectleader.com", "description": "Sales engagement platform with team dialler, multi-channel sequences, and live call analytics.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Velocify", "website": "https://www.velocify.com", "description": "Lead management and sales engagement platform with automated dialling and sequence-based outreach.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Kixie", "website": "https://kixie.com", "description": "Sales engagement platform with integrated power dialler, SMS, and multi-channel sequence automation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://kixie.com/pricing"},
        {"name": "Aircall Dialer", "website": "https://aircall.io", "description": "Cloud-based phone system with power dialler and sales engagement features for outbound teams.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://aircall.io/pricing"},
        {"name": "Freshsales", "website": "https://freshsales.freshworks.com", "description": "CRM with built-in sales engagement features including email tracking, sequences, and phone integration.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://freshsales.freshworks.com/pricing"},
        {"name": "Zoho CRM Sales Engagement", "website": "https://www.zoho.com/crm", "description": "CRM platform with sales engagement features including email, phone, and social media sequences.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.zoho.com/crm/pricing"},
        {"name": "Salesforce Sales Engagement", "website": "https://www.salesforce.com/products/sales", "description": "Salesforce's sales engagement platform with sequence management, task automation, and cadence tools.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.salesforce.com/pricing"},
        {"name": "HubSpot Sales", "website": "https://www.hubspot.com/products/sales", "description": "HubSpot's sales engagement hub with email sequencing, meeting scheduling, and pipeline management.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.hubspot.com/pricing"},
        {"name": "Pitchbox", "website": "https://pitchbox.com", "description": "Outbound sales engagement platform for personalised email outreach with automated follow-up sequences.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "SalesMessage", "website": "https://salesmessage.com", "description": "Sales engagement platform with video messaging, email tracking, and multi-channel sequence automation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "RingDNA", "website": "https://ringdna.com", "description": "Revenue intelligence and sales engagement platform with conversation analytics and guided selling.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "CallHub", "website": "https://callhub.io", "description": "Voice broadcast and sales engagement platform with predictive dialler and campaign management.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://callhub.io/pricing"},
        {"name": "JustCall", "website": "https://justcall.io", "description": "Cloud phone system with sales engagement features including power dialler, SMS, and analytics.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://justcall.io/pricing"},
        {"name": "Talkdesk", "website": "https://www.talkdesk.com", "description": "Enterprise contact centre platform with sales engagement features and advanced diallers.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Outreach Sales Execution Platform", "website": "https://www.outreach.io", "description": "Enterprise sales execution platform with AI-powered sequences, forecasting, and conversation intelligence.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
    ],
    # -----------------------------------------------------------------------
    "prospecting-tools": [
        {"name": "Kaspr", "website": "https://www.kaspr.com", "description": "B2B contact data and prospecting platform with real-time phone number and email verification.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.kaspr.com/pricing"},
        {"name": "Wiza", "website": "https://wiza.co", "description": "LinkedIn prospect extraction and email finding tool for building targeted B2B outbound lists.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://wiza.co/pricing"},
        {"name": "GetProspect", "website": "https://getprospect.com", "description": "B2B email finder and prospecting tool that extracts verified contacts from LinkedIn and company websites.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://getprospect.com/pricing"},
        {"name": "RocketReach", "website": "https://rocketreach.co", "description": "B2B contact database with email and phone data for prospecting and outbound sales campaigns.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://rocketreach.co/pricing"},
        {"name": "FindThatLead", "website": "https://findthatlead.com", "description": "Prospecting and email finding tool for B2B sales teams to build targeted contact lists.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://findthatlead.com/pricing"},
        {"name": "Adapt.io", "website": "https://adapt.io", "description": "AI-powered B2B contact database and prospecting platform with intent-based targeting.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Lead411", "website": "https://www.lead411.com", "description": "B2B prospecting and intent data platform with company news alerts and contact database.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Data.com (D&B)", "website": "https://www.data.com", "description": "Dun & Bradstreet's B2B contact and company database for sales prospecting and account mapping.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "AeroLeads", "website": "https://aeroleads.com", "description": "Prospecting and lead generation tool that extracts contacts from websites, LinkedIn, and Google searches.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://aeroleads.com/pricing"},
        {"name": "Lusha Extension", "website": "https://www.lusha.com", "description": "Browser extension for prospecting that reveals B2B contact data from LinkedIn and company pages.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.lusha.com/pricing"},
        {"name": "SignalHire", "website": "https://www.signalhire.com", "description": "AI-powered recruiting and prospecting platform with contact data and company insights.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.signalhire.com/pricing"},
        {"name": "Kontact.io", "website": "https://kontact.io", "description": "B2B contact database and prospecting tool with CRM integration for outbound lead generation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "UpLead", "website": "https://uplead.com", "description": "B2B prospecting platform with verified contact data, intent filters, and real-time email verification.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://uplead.com/pricing"},
        {"name": "LeadIQ Prospecting", "website": "https://leadiq.com", "description": "Prospecting and data capture platform that finds and enriches contacts with one-click CRM sync.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://leadiq.com/pricing"},
        {"name": "Pipedrive Prospecting", "website": "https://www.pipedrive.com", "description": "CRM with built-in prospecting tools including lead capture, contact enrichment, and pipeline management.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.pipedrive.com/pricing"},
        {"name": "NetHunt", "website": "https://nethunt.com", "description": "CRM and prospecting platform built inside Gmail with contact enrichment and sequence management.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://nethunt.com/pricing"},
        {"name": "Skrapp.io", "website": "https://skrapp.io", "description": "Email finder and prospecting tool that verifies B2B email addresses from LinkedIn and company websites.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://skrapp.io/pricing"},
        {"name": "Anyleads", "website": "https://anyleads.com", "description": "Prospecting and lead generation platform that finds business emails and company contacts at scale.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://anyleads.com/pricing"},
        {"name": "Ocean.io", "website": "https://ocean.io", "description": "AI-powered B2B prospecting and account scoring platform that identifies high-fit target accounts.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "LeadFuze", "website": "https://www.leadfuze.com", "description": "B2B lead generation and prospecting platform with AI-powered targeting and intent data.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.leadfuze.com/pricing"},
        {"name": "CIENCE", "website": "https://cience.com", "description": "Managed B2B prospecting and data services platform combining AI and human research teams.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Liscio", "website": "https://liscio.com", "description": "Client communication and prospecting platform for professional services firms with secure file sharing.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "D&B Hoovers", "website": "https://www.dnb.com/products/marketing-sales.html", "description": "Dun & Bradstreet's B2B prospecting and sales intelligence platform with company and contact data.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "ZoomInfo SalesOS", "website": "https://www.zoominfo.com/products/salesos", "description": "ZoomInfo's flagship sales intelligence platform for prospecting, intent data, and account-based outreach.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Intricately", "website": "https://intricately.com", "description": "Product usage and infrastructure data platform for prospecting technology buyers.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
    ],
    # -----------------------------------------------------------------------
    "lead-enrichment-tools": [
        {"name": "Enricher.io", "website": "https://enricher.io", "description": "B2B email and contact enrichment tool that appends data to business email addresses in real-time.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://enricher.io/pricing"},
        {"name": "Pipl Enrichment", "website": "https://pipl.com", "description": "Identity resolution and data enrichment platform that aggregates contact data from multiple online sources.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "FullContact", "website": "https://www.fullcontact.com", "description": "Contact enrichment and identity resolution platform that appends demographic and social data to contacts.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.fullcontact.com/pricing"},
        {"name": "EverString (D&B)", "website": "https://www.dnb.com", "description": "AI-powered firmographic enrichment and account scoring platform (acquired by D&B).", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "InsideView (D&B)", "website": "https://www.insideview.com", "description": "B2B data enrichment and market intelligence platform providing firmographic and contact data (acquired by D&B).", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Avention (D&B)", "website": "https://www.dnb.com", "description": "Data enrichment and lead scoring platform (acquired by D&B) that appends firmographic data to CRM records.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "DiscoverOrg (ZoomInfo)", "website": "https://www.zoominfo.com", "description": "B2B data enrichment and organisational chart platform (now part of ZoomInfo's SalesOS).", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "D&B Rev.Up", "website": "https://www.dnb.com/products/marketing-sales/revup.html", "description": "Revenue intelligence and data enrichment platform by D&B for account-based marketing and sales.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Leadspace", "website": "https://www.leadspace.com", "description": "Customer data platform that enriches and segments B2B audiences using AI-powered data intelligence.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "6sense Enrichment", "website": "https://6sense.com", "description": "Account and contact enrichment platform that appends intent, firmographic, and technographic data.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Demandbase Enrichment", "website": "https://www.demandbase.com", "description": "ABM and data enrichment platform that appends firmographic and intent data to target accounts.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "TechTarget Enrichment", "website": "https://www.techtarget.com", "description": "IT buying intent and enrichment data platform that identifies technology buyers researching solutions.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "TrueInfluence", "website": "https://www.trueinfluence.com", "description": "B2B data enrichment and company intelligence platform with predictive scoring for sales teams.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "LeadGnome", "website": "https://www.leadgnome.com", "description": "B2B lead enrichment and qualification automation platform that researches and enriches inbound leads.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Gravyty", "website": "https://gravyty.com", "description": "AI-powered fundraising and donor enrichment platform for non-profit organisations.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Mintigo (EDB)", "website": "https://www.edb.com", "description": "Predictive marketing and lead enrichment platform (acquired by EDB) with AI-powered account scoring.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Lattice Engines (D&B)", "website": "https://www.dnb.com", "description": "Predictive lead scoring and data enrichment platform (acquired by D&B) using AI for pipeline analytics.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Infer (SendGrid/Twilio)", "website": "https://www.twilio.com", "description": "Predictive lead scoring and enrichment platform (acquired by SendGrid/Twilio) for data-driven sales.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "V12 Data", "website": "https://v12data.com", "description": "B2B data enrichment and audience marketing platform with firmographic and contact data.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "S&P Global Market Intelligence", "website": "https://www.spglobal.com/marketintelligence", "description": "Enterprise data enrichment and market intelligence platform for financial and industry research.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
    ],
    # -----------------------------------------------------------------------
    "crm-tools": [
        {"name": "Zoho CRM", "website": "https://www.zoho.com/crm", "description": "Cloud-based CRM platform with sales automation, pipeline management, and omnichannel communication.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.zoho.com/crm/pricing"},
        {"name": "Freshsales CRM", "website": "https://freshsales.freshworks.com", "description": "CRM with built-in phone, email, and AI-powered lead scoring for B2B sales teams.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://freshsales.freshworks.com/pricing"},
        {"name": "Bitrix24", "website": "https://www.bitrix24.com", "description": "All-in-one CRM and collaboration platform with sales automation, pipelines, and team communication.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.bitrix24.com/pricing"},
        {"name": "Insightly", "website": "https://www.insightly.com", "description": "CRM and project management platform for small to mid-size businesses with pipeline tracking.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.insightly.com/pricing"},
        {"name": "Nimble", "website": "https://www.nimble.com", "description": "Social CRM that aggregates contact data from social media and email for relationship management.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.nimble.com/pricing"},
        {"name": "Bigin by Zoho", "website": "https://www.zoho.com/bigin", "description": "Simple pipeline CRM for small businesses and startups based on the Zoho platform.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.zoho.com/bigin/pricing"},
        {"name": "OnePageCRM", "website": "https://www.onepagecrm.com", "description": "Action-focused CRM that organises sales activities into a daily workflow for sales teams.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.onepagecrm.com/pricing"},
        {"name": "NetSuite CRM", "website": "https://www.netsuite.com", "description": "Enterprise CRM platform from Oracle with sales force automation and customer management.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Oracle CRM (Siebel)", "website": "https://www.oracle.com/cx", "description": "Enterprise CRM suite from Oracle with comprehensive sales, marketing, and service capabilities.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "SAP C4C", "website": "https://www.sap.com/products/crm.html", "description": "SAP Cloud for Customer (C4C) enterprise CRM with lead management and sales forecasting.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Infor CRM", "website": "https://www.infor.com/products/crm", "description": "Enterprise CRM platform with sales automation, marketing, and customer service capabilities.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "SugarCRM", "website": "https://www.sugarcrm.com", "description": "Flexible CRM platform with sales automation, marketing, and reporting for mid-market and enterprise.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.sugarcrm.com/pricing"},
        {"name": "SuiteCRM", "website": "https://suitecrm.com", "description": "Open-source CRM platform with sales automation, marketing, and service modules for self-hosted deployments.", "pricing_model": "Free", "starting_price": "$0/mo", "has_free_tier": True, "pricing_url": "https://suitecrm.com/pricing"},
        {"name": "ERPNext CRM", "website": "https://erpnext.com", "description": "Open-source ERP platform with integrated CRM for lead management, sales pipeline, and customer tracking.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://erpnext.com/pricing"},
        {"name": "EspoCRM", "website": "https://www.espocrm.com", "description": "Open-source CRM platform with sales automation, email integration, and lead management.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.espocrm.com/pricing"},
        {"name": "Vtiger", "website": "https://www.vtiger.com", "description": "All-in-one CRM with sales, marketing, and support modules for small and mid-size businesses.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.vtiger.com/pricing"},
        {"name": "ActiveCampaign CRM", "website": "https://www.activecampaign.com", "description": "CRM and marketing automation platform with deal tracking, email marketing, and lead scoring.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.activecampaign.com/pricing"},
        {"name": "Keap (Infusionsoft)", "website": "https://keap.com", "description": "CRM and sales automation platform for small businesses with email marketing and lead management.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://keap.com/pricing"},
        {"name": "Less Annoying CRM", "website": "https://www.lessannoyingcrm.com", "description": "Simple and affordable CRM platform designed for small teams with basic contact and pipeline management.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.lessannoyingcrm.com/pricing"},
        {"name": "Agile CRM", "website": "https://www.agilecrm.com", "description": "All-in-one CRM with sales, marketing, and service automation for small and mid-size businesses.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.agilecrm.com/pricing"},
        {"name": "Apptivo", "website": "https://www.apptivo.com", "description": "CRM and business management platform with sales, marketing, and project management modules.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.apptivo.com/pricing"},
        {"name": "Capsule CRM", "website": "https://capsulecrm.com", "description": "Simple CRM for small businesses with contact management, sales pipeline, and email integration.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://capsulecrm.com/pricing"},
        {"name": "Really Simple Systems", "website": "https://www.reallysimplesystems.com", "description": "Simple cloud-based CRM for small businesses with contact management and pipeline tracking.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.reallysimplesystems.com/pricing"},
        {"name": "HiHello CRM", "website": "https://www.hihello.com", "description": "Digital business card and contact management CRM for sales networking and lead capture.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.hihello.com/pricing"},
        {"name": "RelateIQ (Salesforce)", "website": "https://www.salesforce.com", "description": "AI-powered CRM platform (acquired by Salesforce) that automatically surfaces relationship insights.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
    ],
    # -----------------------------------------------------------------------
    "call-recording-tools": [
        {"name": "RingCentral Call Recording", "website": "https://www.ringcentral.com", "description": "Enterprise cloud phone system with automatic call recording, transcription, and analytics.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.ringcentral.com/pricing"},
        {"name": "Zoom Phone Recording", "website": "https://zoom.us/phone", "description": "Zoom Phone call recording with cloud storage, transcription, and searchable archive.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://zoom.us/pricing"},
        {"name": "Teams Phone Recording", "website": "https://www.microsoft.com/en-us/microsoft-teams", "description": "Microsoft Teams call recording with automatic transcription, compliance archiving, and analytics.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.microsoft.com/en-us/microsoft-teams/microsoft-teams-phone"},
        {"name": "Five9 Call Recording", "website": "https://www.five9.com", "description": "Cloud contact centre platform with automatic call recording, quality management, and analytics.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Talkdesk Call Recording", "website": "https://www.talkdesk.com", "description": "Cloud contact centre with automatic call recording, transcription, and conversation analytics.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Genesys Call Recording", "website": "https://www.genesys.com", "description": "Enterprise contact centre platform with comprehensive call recording and compliance features.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Avaya Call Recording", "website": "https://www.avaya.com", "description": "Enterprise communications platform with integrated call recording and contact centre analytics.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "8x8 Call Recording", "website": "https://www.8x8.com", "description": "Cloud phone system with automatic call recording, transcription, and team collaboration features.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.8x8.com/pricing"},
        {"name": "Dialpad Call Recording", "website": "https://www.dialpad.com", "description": "Cloud phone system with AI-powered call recording, transcription, and real-time sentiment analysis.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.dialpad.com/pricing"},
        {"name": "RingDNA Call Recording", "website": "https://ringdna.com", "description": "Revenue intelligence platform with call recording, conversation analytics, and guided selling.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Chorus.ai (ZoomInfo)", "website": "https://www.zoominfo.com/products/chorus", "description": "Conversation intelligence platform with automatic call recording, transcription, and deal risk analysis.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "CallRail", "website": "https://www.callrail.com", "description": "Call tracking and recording platform for marketing attribution with conversation analytics.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.callrail.com/pricing"},
        {"name": "CallTrackingMetrics", "website": "https://www.calltrackingmetrics.com", "description": "Call tracking, recording, and analytics platform with conversation intelligence for sales teams.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.calltrackingmetrics.com/pricing"},
        {"name": "Invoca", "website": "https://www.invoca.com", "description": "Call tracking and conversation intelligence platform with AI-powered call scoring and attribution.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Marchex", "website": "https://www.marchex.com", "description": "Conversation analytics and call recording platform that analyses sales calls for coaching insights.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "ExecVision", "website": "https://execvision.io", "description": "Conversation intelligence platform that records and analyses sales calls to identify winning behaviours.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Jiminny", "website": "https://jiminny.com", "description": "Conversation intelligence platform with AI-powered call recording, transcription, and coaching tools.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Refract", "website": "https://refract.ai", "description": "Conversation intelligence platform that records, transcribes, and analyses sales calls for coaching.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Voicemonitor", "website": "https://voicemonitor.com", "description": "Call recording and quality management platform for contact centres with automated compliance recording.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Enthu.ai", "website": "https://enthu.ai", "description": "AI-powered conversation intelligence platform for sales coaching and call analysis.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "SARAL", "website": "https://saral.ai", "description": "AI conversation intelligence platform for sales teams with call recording, transcription, and insights.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "CallHub Recording", "website": "https://callhub.io", "description": "Voice broadcast and call recording platform with predictive dialling and campaign management.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://callhub.io/pricing"},
        {"name": "JustCall Recording", "website": "https://justcall.io", "description": "Cloud phone system with automatic call recording, transcription, and analytics for sales teams.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://justcall.io/pricing"},
    ],
    # -----------------------------------------------------------------------
    "revenue-intelligence-tools": [
        {"name": "People.ai", "website": "https://people.ai", "description": "Revenue intelligence platform that captures rep activities and provides pipeline forecasting and coaching insights.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "GetFeedback Revenue Intelligence (SurveyMonkey)", "website": "https://www.getfeedback.com", "description": "Revenue intelligence platform that surfaces buyer sentiment and deal risk from sales interaction surveys.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Outreach Kaia", "website": "https://www.outreach.io/platform/kaia", "description": "Conversation intelligence and coaching assistant from Outreach that analyses calls in real-time.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "HubSpot Revenue Intelligence", "website": "https://www.hubspot.com/products/sales/revenue-intelligence", "description": "HubSpot's revenue intelligence tools for pipeline forecasting, deal scoring, and conversation insights.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.hubspot.com/pricing"},
        {"name": "Salesforce Revenue Intelligence", "website": "https://www.salesforce.com/products/einstein", "description": "Salesforce Einstein-powered revenue intelligence with predictive forecasting and deal insights.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "RevenueGrid", "website": "https://www.revenuegrid.com", "description": "Revenue intelligence platform for Salesforce that provides AI-driven forecasts and deal health scoring.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Revenue.io (RingDNA)", "website": "https://revenue.io", "description": "Revenue intelligence and conversation analytics platform (formerly RingDNA) for sales coaching and forecasting.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Revenue.AI (Altify)", "website": "https://www.revenue.ai", "description": "AI-powered revenue intelligence platform (formerly Altify) that predicts deal outcomes and forecast accuracy.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "DecisionLink", "website": "https://decisionlink.com", "description": "Value selling and revenue intelligence platform that quantifies deal value and buyer ROI.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Collective[i]", "website": "https://www.collectivei.com", "description": "Revenue intelligence platform that uses AI to predict deal outcomes and optimise pipeline management.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Aviso", "website": "https://aviso.com", "description": "Revenue intelligence and forecasting platform that analyses CRM data for pipeline predictions.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "InsightSquared (D&B)", "website": "https://www.dnb.com", "description": "Revenue intelligence and analytics platform (acquired by D&B) that provides pipeline and forecasting insights.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "SalesDirector.ai (People.ai)", "website": "https://people.ai", "description": "Revenue intelligence platform (acquired by People.ai) for coaching and pipeline analytics.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "WinRate", "website": "https://winrate.com", "description": "Revenue intelligence platform that predicts deal outcomes and provides pipeline coaching insights.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Forecastly", "website": "https://forecastly.com", "description": "Revenue forecasting and pipeline analytics platform for data-driven sales predictions.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Pipeline.QA", "website": "https://pipeline.qa", "description": "Pipeline quality and revenue intelligence platform that audits CRM data for forecast accuracy.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "CFIT Revenue Intelligence", "website": "https://cfit.ai", "description": "Revenue intelligence platform that uses AI to predict forecasts and analyse pipeline health.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Objections.co", "website": "https://objections.co", "description": "Revenue intelligence platform that analyses sales conversations to identify and handle buyer objections.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
    ],
    # -----------------------------------------------------------------------
    "linkedin-automation-tools": [
        {"name": "LinkedIn Sales Navigator CRM Integration", "website": "https://business.linkedin.com/sales-solutions/sales-navigator", "description": "LinkedIn's premium sales tool with CRM sync for advanced account and lead prospecting.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://business.linkedin.com/sales-solutions/sales-navigator/pricing"},
        {"name": "Dux-Soup", "website": "https://dux-soup.com", "description": "Browser-based LinkedIn automation tool for profile visits, connection requests, and message sequences.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://dux-soup.com/pricing"},
        {"name": "Octopus CRM", "website": "https://octopus.io", "description": "LinkedIn automation software for sending automated connection requests and follow-up messages.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://octopus.io/pricing"},
        {"name": "Linked Helper", "website": "https://linkedhelper.com", "description": "Desktop-based LinkedIn automation that runs auto-invite and message sequences from your PC.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://linkedhelper.com/pricing"},
        {"name": "Zopto", "website": "https://zopto.com", "description": "Cloud-based LinkedIn automation for B2B lead generation with smart sequence management.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://zopto.com/pricing"},
        {"name": "Cleverly (AeroLeads)", "website": "https://cleverly.ai", "description": "LinkedIn automation and lead generation platform with AI-powered message personalisation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "LinkedCamp", "website": "https://linkedcamp.com", "description": "LinkedIn automation tool for mass connection requests, message campaigns, and profile analytics.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://linkedcamp.com/pricing"},
        {"name": "Evabot", "website": "https://www.evabot.io", "description": "AI-powered LinkedIn automation and prospecting platform with smart follow-up sequences.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Linked Dominator", "website": "https://www.linkdominato.com", "description": "LinkedIn automation tool for bulk connection requests, group targeting, and campaign management.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.linkdominato.com/pricing"},
        {"name": "Linked Booster", "website": "https://www.linkedbooster.com", "description": "LinkedIn automation platform for automated connection requests, endorsements, and profile visits.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Linked Prospector", "website": "https://linkedprospector.com", "description": "LinkedIn lead generation tool that extracts prospect data and automates outreach sequences.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Salesflow", "website": "https://salesflow.io", "description": "LinkedIn automation and multi-channel outreach platform for B2B sales teams.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://salesflow.io/pricing"},
        {"name": "Inly (LinkedIn Assistant)", "website": "https://inly.me", "description": "LinkedIn assistant and automation tool for auto-endorsements, profile boosts, and campaign tracking.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Socinator", "website": "https://www.socinator.com", "description": "All-in-one social media automation platform with LinkedIn scheduled posts and engagement tools.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.socinator.com/pricing"},
        {"name": "Follow-Up Box", "website": "https://followupbox.com", "description": "LinkedIn follow-up automation tool that sends scheduled messages to new connections.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://followupbox.com/pricing"},
        {"name": "IFTTT LinkedIn", "website": "https://ifttt.com/linkedin", "description": "No-code automation linking LinkedIn to other apps for automated posting and notifications.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://ifttt.com/pricing"},
        {"name": "Zapier LinkedIn", "website": "https://zapier.com/apps/linkedin/integrations", "description": "Zapier LinkedIn integrations for automating connection requests, posting, and lead capture.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://zapier.com/pricing"},
    ],
    # -----------------------------------------------------------------------
    "ai-outbound-agents": [
        {"name": "Copy.ai Sales Agent", "website": "https://www.copy.ai", "description": "AI sales agent that generates personalised outreach at scale with multi-channel sequence automation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.copy.ai/pricing"},
        {"name": "Writer Full Story Agent", "website": "https://writer.com", "description": "AI platform for enterprise sales teams to generate personalised account research and outreach content.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Jasper Sales Agent", "website": "https://www.jasper.ai", "description": "AI content platform for sales teams to generate personalised email sequences and outreach copy.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.jasper.ai/pricing"},
        {"name": "Bardeen AI", "website": "https://www.bardeen.ai", "description": "AI automation agent that connects sales tools and automates repetitive web-based workflows.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.bardeen.ai/pricing"},
        {"name": "Anybiz", "website": "https://anybiz.com", "description": "AI outbound platform that researches targets and generates personalised multi-channel outreach campaigns.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Regie.ai Sales Agent", "website": "https://www.regie.ai", "description": "AI sales agent platform that generates and executes personalised outbound sequences autonomously.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.regie.ai/pricing"},
        {"name": "Conversica Revenue Digital Assistant", "website": "https://conversica.com", "description": "AI-powered revenue assistant that engages and qualifies leads through natural language conversations.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Drift AI Agent (Salesloft)", "website": "https://www.drift.com", "description": "Drift's AI sales agent (now part of Salesloft) that engages website visitors and books meetings autonomously.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.drift.com/pricing"},
        {"name": "Intercom Fin AI", "website": "https://www.intercom.com/fin", "description": "AI customer service and sales agent that answers questions and qualifies leads in real-time.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.intercom.com/pricing"},
        {"name": "HubSpot Breeze AI", "website": "https://www.hubspot.com/products/sales/breeze", "description": "HubSpot's AI agent for sales that automates prospect research, messaging, and follow-up tasks.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.hubspot.com/pricing"},
        {"name": "Zendesk AI Agents", "website": "https://www.zendesk.com/ai", "description": "Zendesk's AI-powered customer service and sales agents for automated lead qualification and support.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.zendesk.com/pricing"},
        {"name": "11x.ai", "website": "https://www.11x.ai", "description": "Autonomous AI sales agents (Alice and Jordan) for end-to-end outbound and inbound qualification.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Artisan AI", "website": "https://www.artisan.co", "description": "AI digital worker platform with Ava for autonomous outbound sales development and pipeline generation.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Ava.ai", "website": "https://www.artisan.co/ava", "description": "Autonomous AI BDR that researches, writes personalised outreach, and manages multi-channel sequences.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Nooks.ai Agent", "website": "https://nooks.ai", "description": "AI SDR agent that handles prospecting, dialling, and multi-channel outreach autonomously.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://nooks.ai/pricing"},
        {"name": "Overloop AI", "website": "https://overloop.com", "description": "AI-powered multi-channel outreach and sales automation platform for outbound teams.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://overloop.com/pricing"},
        {"name": "Reply.io Jason AI", "website": "https://reply.io/jason-ai", "description": "Autonomous AI SDR from Reply.io that manages end-to-end outbound sequences without human intervention.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://reply.io/pricing"},
        {"name": "Klenty Sales AI Agent", "website": "https://www.klenty.com", "description": "AI-powered sales engagement agent that automates prospect outreach and multi-channel follow-up sequences.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.klenty.com/pricing"},
    ],
    # -----------------------------------------------------------------------
    "workflow-automation-tools": [
        {"name": "Apache Airflow", "website": "https://airflow.apache.org", "description": "Open-source workflow orchestration platform for programmatically authoring, scheduling, and monitoring pipelines.", "pricing_model": "Free", "starting_price": "$0/mo", "has_free_tier": True, "pricing_url": ""},
        {"name": "Prefect", "website": "https://www.prefect.io", "description": "Open-source workflow orchestration platform for building, scheduling, and monitoring data pipelines.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.prefect.io/pricing"},
        {"name": "Dagster", "website": "https://dagster.io", "description": "Open-source data orchestration platform for building, testing, and monitoring data pipelines and workflows.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://dagster.io/pricing"},
        {"name": "Temporal.io", "website": "https://temporal.io", "description": "Open-source workflow orchestration engine for building reliable distributed applications and microservices.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://temporal.io/pricing"},
        {"name": "Camunda", "website": "https://camunda.com", "description": "Workflow automation and decision engine for process orchestration with BPMN modelling.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://camunda.com/pricing"},
        {"name": "Pega Pega Workflow", "website": "https://www.pega.com", "description": "Enterprise workflow automation and business process management (BPM) platform from Pegasystems.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Appian", "website": "https://appian.com", "description": "Low-code workflow automation and business process management platform for enterprise operations.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Kissflow", "website": "https://kissflow.com", "description": "Low-code workflow automation platform for creating business processes, forms, and approvals.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://kissflow.com/pricing"},
        {"name": "Nintex", "website": "https://www.nintex.com", "description": "Workflow automation and document generation platform for streamlining business processes.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "ProcessMaker", "website": "https://www.processmaker.com", "description": "Low-code workflow automation and business process management platform for enterprise operations.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.processmaker.com/pricing"},
        {"name": "Process.st", "website": "https://www.process.st", "description": "Workflow automation and process documentation platform with checklists and standard operating procedures.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.process.st/pricing"},
        {"name": "BonitaSoft", "website": "https://www.bonitasoft.com", "description": "Open-source BPM and workflow automation platform for building business applications.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.bonitasoft.com/pricing"},
        {"name": "Tray.io", "website": "https://tray.io", "description": "Advanced workflow automation platform for connecting cloud applications and building complex integrations.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://tray.io/pricing"},
        {"name": "Celigo", "website": "https://www.celigo.com", "description": "Integration Platform as a Service (iPaaS) for connecting cloud applications and automating workflows.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.celigo.com/pricing"},
        {"name": "Dell Boomi", "website": "https://boomi.com", "description": "Cloud-based integration platform (iPaaS) for connecting applications, data, and workflows.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "MuleSoft Anypoint", "website": "https://www.mulesoft.com", "description": "Enterprise integration platform for connecting applications, data, and devices with API-led connectivity.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Jitterbit", "website": "https://www.jitterbit.com", "description": "Integration and workflow automation platform for connecting enterprise applications and data sources.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "SnapLogic", "website": "https://www.snaplogic.com", "description": "Integration Platform as a Service (iPaaS) for automating workflows across enterprise applications.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "SS&C Chorus", "website": "https://www.ssctech.com", "description": "Enterprise workflow automation and productivity platform for financial services operations.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Integrate.io", "website": "https://www.integrate.io", "description": "Low-code integration platform for building ETL data pipelines and workflow automation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.integrate.io/pricing"},
        {"name": "Talend", "website": "https://www.talend.com", "description": "Open-source data integration and ETL platform for building data pipelines and workflow automation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.talend.com/pricing"},
        {"name": "Frends", "website": "https://frends.com", "description": "Integration Platform as a Service (iPaaS) for hybrid integration and enterprise workflow automation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://frends.com/pricing"},
        {"name": "Make (Integromat)", "website": "https://www.make.com", "description": "Visual workflow automation platform for connecting apps and automating complex multi-step processes.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.make.com/pricing"},
        {"name": "Pipedream", "website": "https://pipedream.com", "description": "Developer-friendly integration and workflow automation platform with serverless compute.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://pipedream.com/pricing"},
        {"name": "Parabola", "website": "https://parabola.io", "description": "No-code data automation platform for building workflows that process and transform data sources.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://parabola.io/pricing"},
        {"name": "Huginn", "website": "https://github.com/huginn/huginn", "description": "Open-source agent-based workflow automation system for building custom event-driven automations.", "pricing_model": "Free", "starting_price": "$0/mo", "has_free_tier": True, "pricing_url": ""},
    ],
    # -----------------------------------------------------------------------
    "sales-analytics-tools": [
        {"name": "Domo", "website": "https://www.domo.com", "description": "Business intelligence and sales analytics platform that connects data sources for real-time dashboards.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.domo.com/pricing"},
        {"name": "Looker (Google Cloud)", "website": "https://cloud.google.com/looker", "description": "Enterprise business intelligence and analytics platform by Google Cloud for sales reporting.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Power BI", "website": "https://powerbi.microsoft.com", "description": "Microsoft's business analytics platform for sales dashboards, reporting, and data visualisation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://powerbi.microsoft.com/pricing"},
        {"name": "Sisense", "website": "https://www.sisense.com", "description": "Business intelligence and analytics platform for embedding sales dashboards and reports.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "ThoughtSpot", "website": "https://www.thoughtspot.com", "description": "AI-powered analytics platform that lets sales teams search and explore data using natural language.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "GoodData", "website": "https://www.gooddata.com", "description": "Cloud-based business intelligence platform for building sales analytics dashboards and reports.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.gooddata.com/pricing"},
        {"name": "Metabase", "website": "https://www.metabase.com", "description": "Open-source business intelligence tool for building sales dashboards and ad-hoc queries.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.metabase.com/pricing"},
        {"name": "Redash", "website": "https://redash.io", "description": "Open-source business intelligence platform for connecting data sources and building sales dashboards.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": ""},
        {"name": "Grafana Sales", "website": "https://grafana.com", "description": "Observability and analytics platform with custom sales dashboards and data visualisation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://grafana.com/pricing"},
        {"name": "HubSpot Analytics", "website": "https://www.hubspot.com/products/analytics", "description": "HubSpot's built-in analytics suite for sales pipeline reporting, attribution, and forecasting.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.hubspot.com/pricing"},
        {"name": "Salesforce Revenue Cloud", "website": "https://www.salesforce.com/products/revenue-cloud", "description": "Salesforce's revenue management and analytics platform for quote-to-cash and pipeline insights.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "People.ai Analytics", "website": "https://people.ai", "description": "Revenue analytics platform that captures rep activities and provides pipeline forecasting and coaching.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Gong Analytics", "website": "https://www.gong.io/analytics", "description": "Conversation-based sales analytics that surfaces win rates, rep performance, and deal health.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Clari Analytics", "website": "https://www.clari.com/platform/analytics", "description": "Revenue analytics and forecasting platform that provides pipeline visibility and deal intelligence.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "InsightSquared Analytics", "website": "https://www.dnb.com", "description": "Sales analytics and revenue intelligence platform (acquired by D&B) for pipeline reporting.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "SalesLoft Analytics", "website": "https://salesloft.com/platform/analytics", "description": "Sales engagement analytics that track sequence performance, rep activity, and pipeline conversion.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Outreach Analytics", "website": "https://www.outreach.io/platform/analytics", "description": "Sales engagement analytics platform for measuring sequence performance and rep effectiveness.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "VanillaSoft Analytics", "website": "https://www.vanillasoft.com", "description": "Sales engagement analytics that track call activity, lead response times, and pipeline conversion.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Xactly", "website": "https://www.xactlycorp.com", "description": "Sales performance management and compensation analytics for commission tracking and forecasting.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Varicent", "website": "https://www.varicent.com", "description": "Sales performance management and analytics platform for commission and territory optimisation.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "CaptivateIQ", "website": "https://www.captivateiq.com", "description": "Sales commission and incentive compensation management platform for performance analytics.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Spiff", "website": "https://www.spiff.com", "description": "Sales commission management platform with real-time incentive tracking and performance analytics.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.spiff.com/pricing"},
        {"name": "Performio", "website": "https://www.performio.co", "description": "Sales performance analytics and commission management platform for enterprise compensation.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Forecastly Analytics", "website": "https://forecastly.com", "description": "Revenue forecasting and sales analytics platform for data-driven pipeline predictions.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
    ],
    # -----------------------------------------------------------------------
    "gtm-engineering-tools": [
        {"name": "Census", "website": "https://www.getcensus.com", "description": "Reverse ETL platform that syncs customer data from the data warehouse into sales and marketing tools.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.getcensus.com/pricing"},
        {"name": "Reverse ETL (Polytomic)", "website": "https://www.polytomic.com", "description": "Reverse ETL platform for syncing data from cloud warehouses into operational sales systems.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.polytomic.com/pricing"},
        {"name": "mParticle", "website": "https://www.mparticle.com", "description": "Customer data platform that ingests and connects behavioural data to sales and marketing tools.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "RudderStack", "website": "https://rudderstack.com", "description": "Open-source customer data platform for collecting and routing event data to sales and marketing tools.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://rudderstack.com/pricing"},
        {"name": "Freshpaint", "website": "https://www.freshpaint.io", "description": "Data activation platform that connects event data from websites and apps to sales and marketing tools.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.freshpaint.io/pricing"},
        {"name": "Wunderkind Personalization", "website": "https://www.wunderkind.co", "description": "AI-powered personalisation and data activation platform for identifying and engaging anonymous website visitors.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Mutiny", "website": "https://www.mutiny.com", "description": "No-code website personalisation platform that customises site content based on visitor account data.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://www.mutiny.com/pricing"},
        {"name": "Personas by Segment", "website": "https://segment.com/product/personas", "description": "Segment's customer data platform for creating audience segments and syncing to sales tools.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Orbit (Community Analytics)", "website": "https://orbit.love", "description": "Community analytics and engagement platform for tracking member activity and identifying sales opportunities.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://orbit.love/pricing"},
        {"name": "Vanilla Community", "website": "https://vanillaforums.com", "description": "Community platform for B2B companies with analytics for tracking member engagement and sentiment.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Clearbit Reveal", "website": "https://clearbit.com/reveal", "description": "Website de-anonymisation tool that identifies B2B companies visiting your website in real-time.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": "https://clearbit.com/pricing"},
        {"name": "LeadFeeder (Dealfront)", "website": "https://www.dealfront.com", "description": "Website visitor identification and lead generation platform that reveals B2B companies visiting your site.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": True, "pricing_url": "https://www.dealfront.com/pricing"},
        {"name": "Metadata.io", "website": "https://www.metadata.io", "description": "ABM and demand generation platform that automates multi-channel ad campaigns for B2B targeting.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Demandbase ABM", "website": "https://www.demandbase.com", "description": "Account-based marketing and advertising platform for targeting key accounts across channels.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "6sense ABM", "website": "https://6sense.com", "description": "ABM platform that uses AI and intent data to target and engage accounts across buying journey stages.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Terminus", "website": "https://terminus.com", "description": "ABM and account engagement platform for targeting ads and content to key B2B accounts.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "RollWorks", "website": "https://rollworks.com", "description": "ABM and account-based advertising platform for B2B companies to target and engage key accounts.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Triblio (IDG)", "website": "https://www.idg.com", "description": "ABM advertising and account engagement platform (acquired by IDG) for targeting B2B accounts.", "pricing_model": "Contact", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
        {"name": "Mr. R (B2B Chatbots)", "website": "https://www.mrr.ai", "description": "AI-powered B2B chatbot and website engagement platform for lead qualification and conversion.", "pricing_model": "Paid", "starting_price": "", "has_free_tier": False, "pricing_url": ""},
    ],
}


def main():
    print("=" * 60)
    print("B2B Sales & Marketing Tool Database Generator")
    print("=" * 60)

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Load existing tools from TS files
    print("\n[1/4] Reading existing tools from frontend TS files...")
    slug_map = load_existing_tools()
    domain_map = build_domain_map(slug_map)
    existing_slugs = set(slug_map.keys())
    print(f"  Existing slugs: {len(existing_slugs)}")
    print(f"  Existing domains: {len(domain_map)}")

    # Step 2: Process new tools
    print("\n[2/4] Processing new tools per category...")
    all_new_tools: list[dict] = []
    total_defined = 0
    total_skipped = 0

    for cat_slug in CATEGORIES:
        raw_list = NEW_TOOLS.get(cat_slug, [])
        total_defined += len(raw_list)
        added = 0
        skipped = 0
        for item in raw_list:
            slug = slugify(item["name"])
            # Skip if slug already exists
            if slug in existing_slugs:
                skipped += 1
                continue
            # Skip if slug already added in this batch
            if slug in {t["slug"] for t in all_new_tools}:
                skipped += 1
                continue
            # Skip if domain already exists
            item_domain = extract_domain(item.get("website", ""))
            if item_domain and item_domain in domain_map:
                skipped += 1
                continue
            all_new_tools.append({
                "slug": slug,
                "name": item["name"],
                "categorySlug": cat_slug,
                "description": item.get("description", ""),
                "website": item.get("website", ""),
                "pricing_model": item.get("pricing_model", "Contact"),
                "starting_price": item.get("starting_price", ""),
                "has_free_tier": bool(item.get("has_free_tier", False)),
                "pricing_url": item.get("pricing_url", ""),
                "_source": "curated",
            })
            added += 1
        print(f"  {cat_slug}: {added} added, {skipped} skipped/duplicates (of {len(raw_list)} defined)")

    print(f"\n  Total new tools defined: {total_defined}")
    print(f"  Total new tools added: {len(all_new_tools)}")
    print(f"  Total skipped: {total_defined - len(all_new_tools)}")

    # Step 3: Build merged list
    print("\n[3/4] Building merged database...")
    merged_tools: list[dict] = []

    # Existing tools first
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

    # New tools
    merged_tools.extend(all_new_tools)

    print(f"  Existing: {len(slug_map)}")
    print(f"  New: {len(all_new_tools)}")
    print(f"  Total: {len(merged_tools)}")

    # Step 4: Write database
    print(f"\n[4/4] Writing {DATABASE_PATH}...")
    db = {
        "generated_at": "2026-05-26",
        "categories": CATEGORIES,
        "total_tools": len(merged_tools),
        "tools": merged_tools,
    }
    DATABASE_PATH.write_text(json.dumps(db, indent=2), encoding="utf-8")
    print(f"  Written to {DATABASE_PATH}")
    print(f"\n{'=' * 60}")
    print(f"Done! Database has {len(merged_tools)} tools across {len(CATEGORIES)} categories")
    print(f"  Existing (from TS files): {len(slug_map)}")
    print(f"  Newly curated tools: {len(all_new_tools)}")


if __name__ == "__main__":
    main()
