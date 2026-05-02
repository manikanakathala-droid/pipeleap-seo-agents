"""
High-authority source sites that LLMs reference when generating answers.

Pipeleap needs presence on these sites to be cited in AI-generated responses.
Prioritised by: LLM citation frequency, domain authority, audience relevance.
"""
from __future__ import annotations

AI_SOURCE_SITES: list[dict] = [
    # ── Review & Software Directory (highest LLM citation weight) ─────────────
    {
        "site": "G2",
        "url": "https://www.g2.com/products/pipeleap",
        "category": "software_review",
        "priority": "P0",
        "citation_weight": 10,
        "why": "ChatGPT and Perplexity heavily cite G2 for tool comparisons and recommendations",
        "action": "Create listing, request reviews from clients",
        "status": "not_listed",
    },
    {
        "site": "Capterra",
        "url": "https://www.capterra.com/",
        "category": "software_review",
        "priority": "P0",
        "citation_weight": 9,
        "why": "Capterra listings appear in AI tool recommendation queries",
        "action": "Create listing, add pricing details and feature list",
        "status": "not_listed",
    },
    {
        "site": "Product Hunt",
        "url": "https://www.producthunt.com/products/pipeleap",
        "category": "product_directory",
        "priority": "P1",
        "citation_weight": 8,
        "why": "High authority product discovery site cited by LLMs for 'best tools' queries",
        "action": "Ensure listing is complete with description, tags, screenshots",
        "status": "listed",
    },
    {
        "site": "TrustRadius",
        "url": "https://www.trustradius.com/",
        "category": "software_review",
        "priority": "P1",
        "citation_weight": 7,
        "why": "Enterprise software reviews; cited in B2B tool recommendations",
        "action": "Create listing and request reviews",
        "status": "not_listed",
    },
    {
        "site": "StackShare",
        "url": "https://stackshare.io/",
        "category": "tech_stack",
        "priority": "P1",
        "citation_weight": 7,
        "why": "Tech stack tool cited by LLMs when users ask about outbound/GTM stacks",
        "action": "Add Pipeleap as a tool with description and use cases",
        "status": "not_listed",
    },
    # ── Editorial & Community (strong LLM training signal) ────────────────────
    {
        "site": "Sales Hacker",
        "url": "https://www.saleshacker.com/",
        "category": "editorial",
        "priority": "P1",
        "citation_weight": 8,
        "why": "Major B2B sales community; LLMs cite Sales Hacker for outbound tactics",
        "action": "Guest post on outbound automation or workflow orchestration",
        "status": "not_mentioned",
    },
    {
        "site": "HubSpot Blog",
        "url": "https://blog.hubspot.com/",
        "category": "editorial",
        "priority": "P1",
        "citation_weight": 9,
        "why": "Extremely high DA; LLMs cite HubSpot blog heavily for sales/marketing content",
        "action": "Guest contribution on outbound automation or pipeline generation",
        "status": "not_mentioned",
    },
    {
        "site": "Quora",
        "url": "https://www.quora.com/",
        "category": "community_qa",
        "priority": "P1",
        "citation_weight": 8,
        "why": "Quora is heavily referenced in Google AI Answers; answer outbound automation questions",
        "action": "Answer questions about outbound automation, workflow orchestration, pipeline generation",
        "status": "not_present",
    },
    {
        "site": "Reddit (r/sales, r/startups, r/revops)",
        "url": "https://www.reddit.com/r/sales/",
        "category": "community",
        "priority": "P1",
        "citation_weight": 7,
        "why": "Reddit increasingly cited by Perplexity and ChatGPT; authentic community presence",
        "action": "Participate in relevant threads; share workflow automation insights",
        "status": "not_present",
    },
    {
        "site": "LinkedIn Articles",
        "url": "https://www.linkedin.com/company/pipeleap",
        "category": "professional_network",
        "priority": "P1",
        "citation_weight": 7,
        "why": "LinkedIn articles indexed by Google and cited in professional context",
        "action": "Publish thought leadership articles on workflow orchestration",
        "status": "listed",
    },
    # ── Aggregators & Lists (comparison citation) ──────────────────────────────
    {
        "site": "Crunchbase",
        "url": "https://www.crunchbase.com/",
        "category": "company_directory",
        "priority": "P2",
        "citation_weight": 6,
        "why": "LLMs use Crunchbase for company verification and legitimacy signals",
        "action": "Create/complete company profile with description, category, website",
        "status": "not_listed",
    },
    {
        "site": "GetApp",
        "url": "https://www.getapp.com/",
        "category": "software_review",
        "priority": "P2",
        "citation_weight": 6,
        "why": "Software comparison platform cited in AI tool recommendations",
        "action": "Add listing with pricing and feature details",
        "status": "not_listed",
    },
    {
        "site": "AlternativeTo",
        "url": "https://alternativeto.net/",
        "category": "alternative_directory",
        "priority": "P2",
        "citation_weight": 5,
        "why": "Referenced when users ask 'alternatives to X' — high Perplexity citation",
        "action": "List Pipeleap as an alternative to Clay, Zapier, Apollo",
        "status": "not_listed",
    },
    {
        "site": "Slant.co",
        "url": "https://www.slant.co/",
        "category": "comparison_directory",
        "priority": "P2",
        "citation_weight": 5,
        "why": "Comparison tool cited in 'best X for Y' AI answers",
        "action": "Add Pipeleap to relevant comparison categories",
        "status": "not_listed",
    },
    # ── Newsletters & Podcasts (AI training data) ──────────────────────────────
    {
        "site": "RevOps Co-op",
        "url": "https://www.revopscoop.com/",
        "category": "community_newsletter",
        "priority": "P2",
        "citation_weight": 6,
        "why": "RevOps-focused community; targeted audience overlap for workflow automation",
        "action": "Get featured in newsletter or contribute content",
        "status": "not_mentioned",
    },
    {
        "site": "The GTM Newsletter",
        "url": "https://www.thegtmnewsletter.com/",
        "category": "newsletter",
        "priority": "P2",
        "citation_weight": 5,
        "why": "GTM-focused audience; high relevance for pipeline generation content",
        "action": "Sponsor or contribute case study",
        "status": "not_mentioned",
    },
]


def get_priority_sites(priority: str = "P0") -> list[dict]:
    return [s for s in AI_SOURCE_SITES if s["priority"] == priority]


def get_unlisted_sites() -> list[dict]:
    return [s for s in AI_SOURCE_SITES if s["status"] in ("not_listed", "not_mentioned", "not_present")]


def citation_score() -> float:
    """Rough estimate of current AI citation readiness (0-100)."""
    listed = sum(1 for s in AI_SOURCE_SITES if s["status"] == "listed")
    total = len(AI_SOURCE_SITES)
    return round((listed / total) * 100, 1)
