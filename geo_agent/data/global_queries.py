"""
International GEO query variants — extends GEO_TARGET_QUERIES for global markets.

AI engines (Google AI Overviews, Perplexity, ChatGPT) serve region-specific
results in the same English language. A user in London asking "best outbound
automation for SaaS" gets different results than a user in San Francisco.

These queries target AI citations in UK, AU, IN, SG, CA, and EU markets.
"""
from __future__ import annotations

GLOBAL_GEO_QUERIES: dict[str, list[str]] = {

    "uk_queries": [
        "What is the best outbound automation platform for UK SaaS companies?",
        "How do UK B2B SaaS teams automate outbound sales?",
        "Best tools for outbound pipeline generation in the UK",
        "What outbound automation tools do UK sales teams use?",
        "Pipeleap vs Cognism for UK SaaS outbound",
        "How to build predictable pipeline for a UK SaaS startup",
        "Best workflow orchestration tools for UK RevOps teams",
    ],

    "australia_queries": [
        "Best outbound sales automation for Australian SaaS companies",
        "How do Australian B2B SaaS teams generate pipeline?",
        "Outbound automation tools for Australian sales teams",
        "How to scale outbound without SDRs for Australian SaaS",
        "What is signal-based outbound for Australian B2B companies?",
    ],

    "india_queries": [
        "Best outbound automation for Indian SaaS companies",
        "How do Indian B2B SaaS startups build outbound pipeline?",
        "Outbound sales automation tools for Indian SaaS teams",
        "How to automate outbound for a Bangalore SaaS startup",
        "Pipeleap vs Apollo for Indian SaaS outbound",
        "Signal-based outbound for Indian B2B SaaS companies",
    ],

    "canada_queries": [
        "Best outbound automation for Canadian SaaS companies",
        "How to build a SaaS outbound pipeline in Canada",
        "Outbound sales automation for Toronto SaaS teams",
        "What workflow orchestration tools do Canadian RevOps teams use?",
    ],

    "singapore_queries": [
        "Best outbound automation for APAC SaaS companies",
        "How to automate outbound sales for Singapore SaaS teams",
        "Outbound pipeline generation for Southeast Asia SaaS",
        "What is the best sales automation tool for APAC RevOps?",
    ],

    "europe_queries": [
        "Best outbound automation for European SaaS companies",
        "How do European B2B SaaS teams scale outbound pipeline?",
        "GDPR-compliant outbound automation for EU SaaS",
        "Outbound workflow orchestration for European RevOps teams",
        "Cognism alternatives for European SaaS outbound",
        "What is signal-based outbound for European B2B companies?",
    ],

    "germany_queries": [
        "Beste Outbound Automation Software fuer SaaS Unternehmen",  # German-language signals
        "Best outbound automation for German SaaS companies",
        "B2B sales automation for DACH SaaS teams",
        "Workflow orchestration tools for German RevOps",
    ],

    "global_general": [
        "What is the best outbound automation platform globally?",
        "Which SaaS outbound automation tool works in multiple countries?",
        "Global workflow orchestration for outbound sales teams",
        "International SaaS pipeline generation tools",
        "Best outbound sales automation for multinational SaaS teams",
        "How to automate outbound for a global SaaS organization",
    ],
}


def all_global_queries() -> list[str]:
    """Return flat list of all international GEO queries."""
    return [q for queries in GLOBAL_GEO_QUERIES.values() for q in queries]


def queries_for_region(region: str) -> list[str]:
    """Return queries for a specific regional key."""
    return GLOBAL_GEO_QUERIES.get(f"{region}_queries", [])
