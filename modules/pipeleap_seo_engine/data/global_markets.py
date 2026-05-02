"""
Global market definitions for Pipeleap SEO and GEO agents.

Pipeleap targets SaaS organizations globally. English is the primary language
of SaaS operations in all tier-1 and tier-2 markets — even in non-English-
speaking countries, the SaaS buyer reads, searches, and evaluates tools in English.

Market tiers (by SaaS revenue + outbound automation maturity):
  Tier 1  — US (primary), UK, Australia, Canada, India
  Tier 2  — Singapore, Ireland, New Zealand, UAE (Dubai), South Africa
  Tier 3  — Germany, Netherlands, Israel, France, Nordics (SaaS-heavy, EN-search)

DataForSEO location codes for multi-region keyword research:
  2840 = US, 2826 = UK, 2036 = AU, 2124 = CA, 2356 = IN
  2702 = SG, 2372 = IE, 2554 = NZ, 2784 = AE, 2710 = ZA
  2276 = DE, 2528 = NL, 2376 = IL, 2250 = FR, 2578 = NO, 2752 = SE
"""
from __future__ import annotations

GLOBAL_MARKETS: dict[str, dict] = {

    # ── Tier 1 ────────────────────────────────────────────────────────────────
    "uk": {
        "label": "United Kingdom",
        "region": "EMEA",
        "tier": 1,
        "dataforseo_code": 2826,
        "currency": "GBP",
        "slug_suffix": "uk",
        "search_modifier": "UK",
        "local_terms": ["B2B outbound UK", "SaaS sales UK", "SDR UK", "pipeline UK", "CRM UK"],
        "pain_angle": "UK SaaS teams face the same pipeline unpredictability as US teams but with smaller SDR budgets and tighter talent markets.",
        "market_stat": "UK has Europe's largest SaaS market — £40B+ and growing.",
        "local_competitors": ["Cognism", "Kaspr", "Lusha UK"],
        "key_personas": ["UK VP Sales", "UK RevOps", "UK SaaS founders"],
        "regional_keywords": [
            "outbound automation uk", "saas pipeline generation uk", "b2b outbound uk saas",
            "uk sales workflow automation", "outbound sales tools uk", "crm automation uk",
            "revops uk saas", "sdr automation uk", "pipeline software uk",
            "signal based outbound uk", "b2b saas uk outbound", "workflow orchestration uk",
        ],
    },
    "australia": {
        "label": "Australia",
        "region": "APAC",
        "tier": 1,
        "dataforseo_code": 2036,
        "currency": "AUD",
        "slug_suffix": "australia",
        "search_modifier": "Australia",
        "local_terms": ["B2B outbound Australia", "SaaS sales AU", "pipeline AU"],
        "pain_angle": "Australian SaaS teams often lack dedicated SDR teams and need outbound automation to compete internationally.",
        "market_stat": "Australia's SaaS market reached $15B in 2024 — outbound automation adoption is accelerating.",
        "local_competitors": ["Cognism", "Apollo", "Instantly"],
        "key_personas": ["AU SaaS founders", "AU VP Sales", "AU RevOps"],
        "regional_keywords": [
            "outbound automation australia", "saas pipeline australia", "b2b outbound australia",
            "sales workflow automation australia", "outbound sales tools australia",
            "sdr automation australia", "crm automation australia", "revops australia saas",
            "workflow orchestration australia", "saas outbound australia",
        ],
    },
    "canada": {
        "label": "Canada",
        "region": "Americas",
        "tier": 1,
        "dataforseo_code": 2124,
        "currency": "CAD",
        "slug_suffix": "canada",
        "search_modifier": "Canada",
        "local_terms": ["B2B outbound Canada", "SaaS sales CA", "pipeline Canada"],
        "pain_angle": "Canadian SaaS teams (especially in Toronto and Vancouver) compete globally and need workflow automation to match US team output.",
        "market_stat": "Canada is the 3rd-largest English SaaS market — $12B+ with Toronto as North America's 2nd tech hub.",
        "local_competitors": ["Apollo", "Clay", "Zapier"],
        "key_personas": ["Canadian VP Sales", "Canadian CRO", "Toronto/Vancouver SaaS founders"],
        "regional_keywords": [
            "outbound automation canada", "saas pipeline canada", "b2b outbound canada",
            "sales automation canada", "workflow orchestration canada", "sdr automation canada",
            "crm automation canada", "revops canada", "pipeline generation canada",
        ],
    },
    "india": {
        "label": "India",
        "region": "APAC",
        "tier": 1,
        "dataforseo_code": 2356,
        "currency": "INR",
        "slug_suffix": "india",
        "search_modifier": "India",
        "local_terms": ["B2B outbound India", "SaaS sales India", "SDR India", "pipeline India"],
        "pain_angle": "Indian SaaS companies (Bangalore, Hyderabad, Pune) are scaling globally and need outbound automation to compete with US-native teams.",
        "market_stat": "India's SaaS revenue is projected to reach $50B by 2030 — B2B outbound is a top GTM challenge.",
        "local_competitors": ["LeadSquared", "Freshsales", "Apollo"],
        "key_personas": ["Indian SaaS founders", "India VP Sales", "Indian RevOps", "B2B SaaS India"],
        "regional_keywords": [
            "outbound automation india", "saas pipeline india", "b2b outbound india",
            "sales workflow automation india", "sdr automation india", "crm automation india",
            "revops india saas", "pipeline generation india", "b2b saas outbound india",
            "workflow orchestration india", "outbound sales tools india",
        ],
    },

    # ── Tier 2 ────────────────────────────────────────────────────────────────
    "singapore": {
        "label": "Singapore",
        "region": "APAC",
        "tier": 2,
        "dataforseo_code": 2702,
        "currency": "SGD",
        "slug_suffix": "singapore",
        "search_modifier": "Singapore",
        "local_terms": ["B2B outbound Singapore", "SaaS sales APAC", "GTM Singapore"],
        "pain_angle": "Singapore is APAC's GTM hub — SaaS teams here run regional outbound across 12+ markets and need orchestrated, multi-territory workflows.",
        "market_stat": "Singapore hosts 4,000+ tech startups and serves as APAC HQ for most global SaaS companies.",
        "local_competitors": ["Apollo", "Clay"],
        "key_personas": ["APAC VP Sales", "Singapore SaaS CRO", "APAC RevOps"],
        "regional_keywords": [
            "outbound automation singapore", "saas pipeline singapore", "b2b outbound apac",
            "sales automation singapore", "workflow orchestration apac", "revops singapore",
            "crm automation singapore", "sdr automation apac", "pipeline generation singapore",
        ],
    },
    "uae": {
        "label": "UAE (Dubai)",
        "region": "MENA",
        "tier": 2,
        "dataforseo_code": 2784,
        "currency": "AED",
        "slug_suffix": "uae",
        "search_modifier": "UAE",
        "local_terms": ["B2B outbound UAE", "SaaS Dubai", "GTM Middle East"],
        "pain_angle": "UAE-based SaaS teams target MENA and global enterprise buyers — manual outbound doesn't scale across Arabic and English-speaking markets simultaneously.",
        "market_stat": "Dubai is the MENA SaaS hub — $3B+ market growing 25% annually.",
        "local_competitors": ["Apollo", "Outreach"],
        "key_personas": ["UAE VP Sales", "Dubai SaaS founders", "MENA RevOps"],
        "regional_keywords": [
            "outbound automation uae", "saas pipeline uae", "b2b outbound uae",
            "sales automation dubai", "workflow orchestration uae", "revops uae",
            "pipeline generation mena", "sdr automation uae",
        ],
    },

    # ── Tier 3 (EN-search, high SaaS density) ────────────────────────────────
    "germany": {
        "label": "Germany",
        "region": "DACH",
        "tier": 3,
        "dataforseo_code": 2276,
        "currency": "EUR",
        "slug_suffix": "germany",
        "search_modifier": "Germany",
        "local_terms": ["B2B outbound Germany", "SaaS sales DACH", "Vertriebsautomatisierung"],
        "pain_angle": "German SaaS companies operate in one of Europe's largest B2B markets but evaluate tools in English — outbound automation adoption is growing rapidly.",
        "market_stat": "Germany is Europe's largest SaaS market after the UK — €20B+ with strong B2B outbound demand.",
        "local_competitors": ["HubSpot DE", "Pipedrive", "Dealfront"],
        "key_personas": ["German VP Sales", "DACH SaaS CRO", "German RevOps"],
        "regional_keywords": [
            "outbound automation germany", "b2b sales automation germany", "saas pipeline germany",
            "workflow orchestration germany", "crm automation dach", "revops germany",
            "sdr automation germany", "outbound sales tools germany", "b2b outbound dach",
        ],
    },
    "europe": {
        "label": "Europe (Pan-EU)",
        "region": "EMEA",
        "tier": 2,
        "dataforseo_code": 2826,  # Use UK as proxy for European English searches
        "currency": "EUR",
        "slug_suffix": "europe",
        "search_modifier": "Europe",
        "local_terms": ["B2B outbound Europe", "SaaS sales Europe", "European GTM"],
        "pain_angle": "European SaaS teams must run outbound across multiple markets, languages, and compliance environments — workflow orchestration is essential for consistent execution.",
        "market_stat": "European SaaS market exceeded $100B in 2024 — cross-border outbound automation is a top priority.",
        "local_competitors": ["Cognism", "Lemlist", "Lusha"],
        "key_personas": ["European VP Sales", "EU SaaS CRO", "EMEA RevOps"],
        "regional_keywords": [
            "outbound automation europe", "b2b outbound europe", "saas pipeline europe",
            "workflow orchestration europe", "crm automation europe", "revops europe",
            "sdr automation europe", "pipeline generation europe", "european saas outbound",
            "b2b sales automation emea", "outbound tools europe",
        ],
    },
}

# Flat list of all regional keywords across all markets
def all_regional_keywords() -> list[dict]:
    entries = []
    for market_key, market in GLOBAL_MARKETS.items():
        for kw in market["regional_keywords"]:
            entries.append({
                "keyword":      kw,
                "market":       market_key,
                "region":       market["region"],
                "tier":         market["tier"],
                "intent":       "commercial",
                "source":       f"global:{market_key}",
                "page_type":    "use_case_page",
                "funnel_stage": "solution-aware",
                "dataforseo_code": market["dataforseo_code"],
            })
    return entries

# All DataForSEO location codes for multi-region SERP checks
GLOBAL_DATAFORSEO_CODES: list[int] = sorted({
    m["dataforseo_code"] for m in GLOBAL_MARKETS.values()
})

# Markets for hreflang (en = all English, specific for major markets)
HREFLANG_MARKETS: list[dict] = [
    {"hreflang": "x-default", "href_suffix": ""},
    {"hreflang": "en",        "href_suffix": ""},
    {"hreflang": "en-us",     "href_suffix": ""},
    {"hreflang": "en-gb",     "href_suffix": ""},
    {"hreflang": "en-au",     "href_suffix": ""},
    {"hreflang": "en-ca",     "href_suffix": ""},
    {"hreflang": "en-in",     "href_suffix": ""},
    {"hreflang": "en-sg",     "href_suffix": ""},
]
