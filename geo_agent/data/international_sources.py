"""
International citation sources — extends AI_SOURCE_SITES for global markets.

LLMs serving UK, EU, AU, IN, and APAC users cite region-specific sources.
A UK user asking ChatGPT about outbound tools will see Cognism, G2 UK,
and Sales Hacker Europe references — not just US-centric sources.

These sources are required to rank in global AI-generated answers.
"""
from __future__ import annotations

INTERNATIONAL_SOURCES: list[dict] = [

    # ── UK / EMEA ─────────────────────────────────────────────────────────────
    {
        "site": "Cognism Blog",
        "url": "https://www.cognism.com/blog",
        "region": "UK",
        "category": "editorial",
        "priority": "P1",
        "citation_weight": 8,
        "why": "Cognism is the UK's leading B2B data platform — their blog is highly indexed by UK AI results",
        "action": "Guest post or get mentioned in a Cognism comparison article",
        "status": "not_mentioned",
    },
    {
        "site": "The Trailblazer (Revenue Collective UK)",
        "url": "https://www.revenuecollective.com/",
        "region": "UK/EMEA",
        "category": "community",
        "priority": "P1",
        "citation_weight": 7,
        "why": "UK/EU Revenue Collective community — cited in EMEA outbound automation queries",
        "action": "Participate in community, share workflow automation insights",
        "status": "not_present",
    },
    {
        "site": "G2 UK Market",
        "url": "https://www.g2.com/products/pipeleap",
        "region": "UK",
        "category": "software_review",
        "priority": "P0",
        "citation_weight": 9,
        "why": "G2 serves UK and EU buyers — same listing, UK-specific reviews needed",
        "action": "Request reviews from UK/EU clients specifically",
        "status": "not_listed",
    },
    {
        "site": "SalesLoft Blog (EMEA)",
        "url": "https://salesloft.com/resources/blog/",
        "region": "EMEA",
        "category": "editorial",
        "priority": "P2",
        "citation_weight": 7,
        "why": "SalesLoft content cited for EU/UK outbound sales automation queries",
        "action": "Get mentioned as a complementary workflow orchestration tool",
        "status": "not_mentioned",
    },

    # ── India / APAC ──────────────────────────────────────────────────────────
    {
        "site": "SaaSBoomi",
        "url": "https://saasboomi.com/",
        "region": "India",
        "category": "community",
        "priority": "P1",
        "citation_weight": 8,
        "why": "India's premier SaaS community — heavily indexed for Indian SaaS queries",
        "action": "Participate in SaaSBoomi events, contribute case study on outbound automation",
        "status": "not_present",
    },
    {
        "site": "iSPIRT / Indian Software Product Industry",
        "url": "https://ispirt.in/",
        "region": "India",
        "category": "community",
        "priority": "P2",
        "citation_weight": 6,
        "why": "India SaaS industry association — cited in Indian SaaS tool recommendations",
        "action": "Contribute thought leadership on GTM automation for Indian SaaS",
        "status": "not_present",
    },
    {
        "site": "YourStory (India Tech)",
        "url": "https://yourstory.com/",
        "region": "India",
        "category": "editorial",
        "priority": "P1",
        "citation_weight": 7,
        "why": "India's largest startup media — cited in Indian SaaS product recommendations",
        "action": "Feature Pipeleap story or guest post on outbound automation for Indian SaaS",
        "status": "not_mentioned",
    },
    {
        "site": "Sifted (European Startup News)",
        "url": "https://sifted.eu/",
        "region": "Europe",
        "category": "editorial",
        "priority": "P2",
        "citation_weight": 7,
        "why": "European startup media — cited in EU AI product recommendations",
        "action": "Feature Pipeleap in a European SaaS sales automation article",
        "status": "not_mentioned",
    },

    # ── Australia ─────────────────────────────────────────────────────────────
    {
        "site": "StartupSmart (Australia)",
        "url": "https://www.startupsmart.com.au/",
        "region": "Australia",
        "category": "editorial",
        "priority": "P2",
        "citation_weight": 6,
        "why": "Australian startup media — AI results for AU SaaS tool queries reference this",
        "action": "Pitch article on outbound automation for Australian SaaS companies",
        "status": "not_mentioned",
    },
    {
        "site": "Finder.com.au (Business Software)",
        "url": "https://www.finder.com.au/business-software",
        "region": "Australia",
        "category": "software_review",
        "priority": "P2",
        "citation_weight": 6,
        "why": "Australian software comparison site — cited in AU SaaS tool queries",
        "action": "List Pipeleap in the sales automation category",
        "status": "not_listed",
    },

    # ── Canada ────────────────────────────────────────────────────────────────
    {
        "site": "Betakit (Canadian Tech)",
        "url": "https://betakit.com/",
        "region": "Canada",
        "category": "editorial",
        "priority": "P2",
        "citation_weight": 6,
        "why": "Canadian tech media — cited in CA SaaS tool recommendations",
        "action": "Pitch Pipeleap story for Canadian SaaS founder audience",
        "status": "not_mentioned",
    },

    # ── Singapore / APAC ──────────────────────────────────────────────────────
    {
        "site": "e27 (Southeast Asia Tech)",
        "url": "https://e27.co/",
        "region": "Singapore/APAC",
        "category": "editorial",
        "priority": "P2",
        "citation_weight": 6,
        "why": "APAC startup media — cited in APAC SaaS tool queries",
        "action": "Pitch outbound automation for APAC SaaS article",
        "status": "not_mentioned",
    },

    # ── Global Product Directories ────────────────────────────────────────────
    {
        "site": "Capterra Global",
        "url": "https://www.capterra.com/",
        "region": "Global",
        "category": "software_review",
        "priority": "P0",
        "citation_weight": 9,
        "why": "Capterra serves global markets — critical for international AI tool citations",
        "action": "Create listing + request international reviews",
        "status": "not_listed",
    },
    {
        "site": "Software Advice",
        "url": "https://www.softwareadvice.com/",
        "region": "Global",
        "category": "software_review",
        "priority": "P1",
        "citation_weight": 7,
        "why": "Gartner-owned global directory — cited across all English-speaking markets",
        "action": "Create listing in Sales Force Automation category",
        "status": "not_listed",
    },
    {
        "site": "GetApp Global",
        "url": "https://www.getapp.com/",
        "region": "Global",
        "category": "software_review",
        "priority": "P1",
        "citation_weight": 7,
        "why": "Global SMB software discovery — cited in non-US English AI results",
        "action": "Create listing with global pricing and features",
        "status": "not_listed",
    },
]


def get_sources_by_region(region: str) -> list[dict]:
    region_lower = region.lower()
    return [
        s for s in INTERNATIONAL_SOURCES
        if region_lower in s.get("region", "").lower()
    ]


def get_unlisted_international() -> list[dict]:
    return [
        s for s in INTERNATIONAL_SOURCES
        if s["status"] in ("not_listed", "not_mentioned", "not_present")
    ]
