"""
Entity definitions for AI search optimization (AI Overviews, LLM citation, Knowledge Graph).
Each entity is a concept Pipeleap should own in the semantic web.
Format: DefinedTerm schema + concise definition + related entities.
"""
from __future__ import annotations
from typing import Any

ENTITIES: dict[str, dict[str, Any]] = {
    "workflow-orchestration": {
        "term": "Workflow Orchestration",
        "slug": "workflow-orchestration",
        "definition": (
            "Workflow orchestration is the automated coordination of multiple processes, tools, and data flows "
            "into a single governed execution system. In SaaS outbound sales, workflow orchestration connects "
            "signal detection, lead enrichment, outreach sequencing, CRM routing, and reply handling into one "
            "automated pipeline that operates without manual intervention."
        ),
        "short_definition": (
            "Workflow orchestration automates the coordination of sales tools, data, and processes into a "
            "single governed execution system — eliminating manual handoffs and creating predictable pipeline."
        ),
        "related_terms": ["outbound automation", "revenue operations", "pipeline generation", "signal-based outbound"],
        "pipeleap_context": "Pipeleap is a workflow orchestration system for SaaS organizations.",
        "schema_type": "DefinedTerm",
        "keywords": ["workflow orchestration", "workflow orchestration saas", "sales workflow orchestration", "outbound workflow orchestration"],
    },
    "outbound-automation": {
        "term": "Outbound Automation",
        "slug": "outbound-automation",
        "definition": (
            "Outbound automation is the use of software workflows to replace manual outbound sales execution — "
            "including prospect research, email sequencing, follow-up scheduling, CRM updates, and reply routing. "
            "When outbound is automated, sales teams generate more pipeline with less manual effort and achieve "
            "consistent execution regardless of individual rep performance."
        ),
        "short_definition": (
            "Outbound automation replaces manual sales tasks — research, sequencing, follow-up, CRM updates — "
            "with automated workflows that generate pipeline consistently at scale."
        ),
        "related_terms": ["workflow orchestration", "sdr automation", "email sequence automation", "pipeline generation"],
        "pipeleap_context": "Pipeleap orchestrates outbound automation end-to-end for SaaS organizations.",
        "schema_type": "DefinedTerm",
        "keywords": ["outbound automation", "outbound automation saas", "automated outbound sales", "b2b outbound automation"],
    },
    "signal-based-outbound": {
        "term": "Signal-Based Outbound",
        "slug": "signal-based-outbound",
        "definition": (
            "Signal-based outbound is a selling approach where outreach workflows are triggered by real-time "
            "buying signals rather than static lead lists. Signals include website visits, intent data matches, "
            "job changes, funding announcements, technology installations, and CRM field changes. "
            "Signal-based outbound produces higher reply rates because outreach reaches prospects at moments "
            "of genuine buying intent."
        ),
        "short_definition": (
            "Signal-based outbound triggers automated outreach workflows when prospects show buying intent — "
            "producing higher reply rates than static list-based campaigns."
        ),
        "related_terms": ["intent data", "buying signals", "workflow orchestration", "outbound automation"],
        "pipeleap_context": "Pipeleap enables signal-based outbound through its workflow orchestration engine.",
        "schema_type": "DefinedTerm",
        "keywords": ["signal based outbound", "signal based selling", "intent based outbound", "buying signal automation"],
    },
    "pipeline-generation": {
        "term": "Pipeline Generation",
        "slug": "pipeline-generation",
        "definition": (
            "Pipeline generation is the systematic process of identifying, qualifying, and engaging prospective "
            "customers to create a predictable flow of sales opportunities. In SaaS organizations, automated "
            "pipeline generation replaces manual SDR prospecting with orchestrated workflows that operate "
            "continuously — generating qualified pipeline without proportional headcount growth."
        ),
        "short_definition": (
            "Pipeline generation is the systematic process of creating a predictable flow of sales opportunities. "
            "Automated pipeline generation runs these workflows continuously without manual SDR effort."
        ),
        "related_terms": ["outbound automation", "lead generation", "demand generation", "workflow orchestration"],
        "pipeleap_context": "Pipeleap is built specifically for predictable pipeline generation through workflow orchestration.",
        "schema_type": "DefinedTerm",
        "keywords": ["pipeline generation", "saas pipeline generation", "automated pipeline generation", "predictable pipeline"],
    },
    "revenue-operations": {
        "term": "Revenue Operations (RevOps)",
        "slug": "revenue-operations",
        "definition": (
            "Revenue operations (RevOps) is the function responsible for aligning sales, marketing, and customer "
            "success operations to maximize revenue growth. RevOps teams govern the tools, data, processes, "
            "and workflows that enable predictable revenue generation. Workflow automation is increasingly "
            "central to RevOps — replacing manual execution with governed systems that scale."
        ),
        "short_definition": (
            "Revenue operations (RevOps) aligns sales, marketing, and CS processes to maximize revenue. "
            "Workflow automation is the operational backbone of modern RevOps."
        ),
        "related_terms": ["workflow orchestration", "sales operations", "pipeline generation", "CRM automation"],
        "pipeleap_context": "Pipeleap serves RevOps teams by automating the workflow execution layer.",
        "schema_type": "DefinedTerm",
        "keywords": ["revenue operations", "revops automation", "revenue operations saas", "revops workflow"],
    },
    "sdr-automation": {
        "term": "SDR Automation",
        "slug": "sdr-automation",
        "definition": (
            "SDR automation is the replacement of manual sales development representative tasks — prospecting, "
            "enrichment, email outreach, follow-up, and CRM logging — with automated workflow systems. "
            "SDR automation does not replace SDRs; it eliminates the manual tasks that consume 60-70% of "
            "SDR time, allowing reps to focus on conversations and qualification instead of administrative work."
        ),
        "short_definition": (
            "SDR automation replaces the manual tasks that consume 60-70% of SDR time — prospecting, "
            "enrichment, follow-up, CRM logging — freeing reps to focus on conversations."
        ),
        "related_terms": ["outbound automation", "workflow orchestration", "pipeline generation", "AI SDR"],
        "pipeleap_context": "Pipeleap automates SDR workflows end-to-end, from signal detection to CRM routing.",
        "schema_type": "DefinedTerm",
        "keywords": ["sdr automation", "sdr workflow automation", "automate sdr tasks", "sdr productivity automation"],
    },
    "lead-enrichment": {
        "term": "Lead Enrichment",
        "slug": "lead-enrichment",
        "definition": (
            "Lead enrichment is the automated process of appending company, contact, technographic, and "
            "firmographic data to prospect records before outreach. Enriched prospects receive more relevant, "
            "personalized outreach — improving reply rates and conversion. In automated outbound workflows, "
            "enrichment happens at intake, in real time, without any manual research effort."
        ),
        "short_definition": (
            "Lead enrichment automatically appends company and contact data to prospect records, "
            "enabling personalized outreach without manual research."
        ),
        "related_terms": ["outbound automation", "data enrichment", "prospecting", "workflow orchestration"],
        "pipeleap_context": "Pipeleap runs lead enrichment as a governed workflow stage before any outreach fires.",
        "schema_type": "DefinedTerm",
        "keywords": ["lead enrichment", "lead enrichment automation", "saas lead enrichment", "automated lead enrichment"],
    },
    "crm-automation": {
        "term": "CRM Automation",
        "slug": "crm-automation",
        "definition": (
            "CRM automation is the use of workflow triggers to automatically update CRM records, route "
            "prospects between pipeline stages, assign owners, and log activity — without manual data entry. "
            "CRM automation eliminates the data quality problems caused by inconsistent manual updates, "
            "ensuring the pipeline reflects real-time execution state at all times."
        ),
        "short_definition": (
            "CRM automation uses workflow triggers to update records, route prospects, and log activity "
            "automatically — eliminating manual data entry and keeping pipeline data accurate."
        ),
        "related_terms": ["workflow orchestration", "revenue operations", "pipeline generation", "sales automation"],
        "pipeleap_context": "Pipeleap governs CRM automation as part of the end-to-end outbound workflow.",
        "schema_type": "DefinedTerm",
        "keywords": ["crm automation", "crm workflow automation", "saas crm automation", "automated crm updates"],
    },
}

def get_entity(slug: str) -> dict[str, Any] | None:
    return ENTITIES.get(slug)

def all_entity_slugs() -> list[str]:
    return list(ENTITIES.keys())

def entity_schema(entity: dict[str, Any], site_url: str) -> dict[str, Any]:
    return {
        "@context": "https://schema.org",
        "@type": "DefinedTerm",
        "name": entity["term"],
        "description": entity["short_definition"],
        "url": f"{site_url}/glossary/{entity['slug']}",
        "inDefinedTermSet": {
            "@type": "DefinedTermSet",
            "name": "Pipeleap SaaS Growth Glossary",
            "url": f"{site_url}/glossary",
        },
    }
