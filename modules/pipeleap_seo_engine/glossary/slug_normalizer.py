"""
Slug normalization and synonym resolution for the glossary engine.

Rules:
- lowercase + hyphenated, no special chars
- acronyms expanded to full canonical forms
- synonyms mapped to a single canonical slug
- deterministic: same input always produces same slug
"""
from __future__ import annotations

import re
import unicodedata

# Acronym → canonical full-form slug
ACRONYM_MAP: dict[str, str] = {
    "abm": "account-based-marketing",
    "aov": "average-order-value",
    "arr": "annual-recurring-revenue",
    "bofu": "bottom-of-funnel",
    "bdr": "business-development-representative",
    "cac": "customer-acquisition-cost",
    "clv": "customer-lifetime-value",
    "ltv": "customer-lifetime-value",
    "crm": "customer-relationship-management",
    "cro": "conversion-rate-optimization",
    "cta": "call-to-action",
    "cvr": "conversion-rate",
    "dql": "data-qualified-lead",
    "gtm": "go-to-market",
    "icp": "ideal-customer-profile",
    "kpi": "key-performance-indicator",
    "mql": "marketing-qualified-lead",
    "mrr": "monthly-recurring-revenue",
    "mofu": "middle-of-funnel",
    "ndr": "net-dollar-retention",
    "nrr": "net-revenue-retention",
    "pql": "product-qualified-lead",
    "pls": "product-led-sales",
    "plg": "product-led-growth",
    "revops": "revenue-operations",
    "roi": "return-on-investment",
    "saas": "software-as-a-service",
    "sdr": "sales-development-representative",
    "seo": "search-engine-optimization",
    "sql": "sales-qualified-lead",
    "tam": "total-addressable-market",
    "tofu": "top-of-funnel",
}

# Synonym/alternate phrasing → canonical slug
SYNONYM_MAP: dict[str, str] = {
    # outbound automation
    "sales automation": "outbound-automation",
    "automated outbound": "outbound-automation",
    "outbound sales automation": "outbound-automation",
    "b2b outbound automation": "outbound-automation",
    # workflow orchestration
    "workflow management": "workflow-orchestration",
    "workflow engine": "workflow-orchestration",
    "process orchestration": "workflow-orchestration",
    "sales workflow automation": "workflow-orchestration",
    # pipeline generation
    "demand generation": "pipeline-generation",
    "lead generation": "pipeline-generation",
    "pipeline building": "pipeline-generation",
    # signal-based outbound
    "intent-based outbound": "signal-based-outbound",
    "trigger-based outbound": "signal-based-outbound",
    "signal based selling": "signal-based-outbound",
    # sdr automation
    "sdr productivity": "sdr-automation",
    "sales development automation": "sdr-automation",
    # revenue operations
    "sales operations": "revenue-operations",
    "go-to-market operations": "revenue-operations",
    "gtm ops": "revenue-operations",
    # icp
    "ideal customer": "ideal-customer-profile",
    "target customer": "ideal-customer-profile",
    "buyer profile": "ideal-customer-profile",
    # crm automation
    "crm integration": "crm-automation",
    "crm workflow": "crm-automation",
    # lead enrichment
    "data enrichment": "lead-enrichment",
    "prospect enrichment": "lead-enrichment",
    "contact enrichment": "lead-enrichment",
    # cold email
    "cold outreach": "cold-email-outreach",
    "cold emailing": "cold-email-outreach",
    "email prospecting": "cold-email-outreach",
    # account based marketing
    "account based selling": "account-based-marketing",
    "abm strategy": "account-based-marketing",
    # product led growth
    "plg motion": "product-led-growth",
    "product led sales": "product-led-sales",
}


def _slugify(text: str) -> str:
    """Convert arbitrary text to a clean hyphenated slug."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")


def normalize_slug(raw: str) -> str:
    """
    Normalize a term or slug to its canonical form.
    Expands acronyms, resolves synonyms, then slugifies.
    """
    cleaned = raw.strip().lower()

    # 1. Direct acronym expansion
    if cleaned in ACRONYM_MAP:
        return ACRONYM_MAP[cleaned]

    slug = _slugify(cleaned)

    # 2. Check slugified acronym
    if slug in ACRONYM_MAP:
        return ACRONYM_MAP[slug]

    # 3. Synonym resolution (on original cleaned text)
    if cleaned in SYNONYM_MAP:
        return SYNONYM_MAP[cleaned]

    # 4. Synonym resolution on slugified form
    for synonym, canonical in SYNONYM_MAP.items():
        if _slugify(synonym) == slug:
            return canonical

    return slug


def resolve_synonym(term: str) -> str | None:
    """Return the canonical slug if term is a known synonym, else None."""
    cleaned = term.strip().lower()
    if cleaned in SYNONYM_MAP:
        return SYNONYM_MAP[cleaned]
    slug = _slugify(cleaned)
    for synonym, canonical in SYNONYM_MAP.items():
        if _slugify(synonym) == slug:
            return canonical
    return None
