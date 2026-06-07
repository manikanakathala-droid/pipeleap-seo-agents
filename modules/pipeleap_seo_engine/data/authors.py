"""
Author profiles for EEAT compliance.
Every generated page must carry a named author with verifiable credentials.
Add real team members here before publishing.
"""
from __future__ import annotations
from typing import Any

AUTHORS: dict[str, dict[str, Any]] = {
    "pipeleap_team": {
        "name": "Pipeleap Team",
        "slug": "pipeleap-team",
        "title": "Revenue Automation Specialists",
        "bio": (
            "The Pipeleap team builds workflow orchestration systems for SaaS revenue organizations. "
            "We specialize in outbound automation, signal-based pipeline generation, and systematic "
            "replacement of manual sales execution with governed, scalable workflows."
        ),
        "expertise": [
            "Outbound sales automation",
            "Workflow orchestration",
            "SaaS revenue operations",
            "Pipeline generation systems",
            "Signal-based selling",
        ],
        "social_urls": [
            "https://www.linkedin.com/company/pipeleap",
        ],
        "credentials": [
            "Built outbound systems for 50+ SaaS organizations",
            "Collectively managed $100M+ in pipeline through automated workflows",
        ],
    },
    "revops_expert": {
        "name": "Pipeleap RevOps",
        "slug": "revops",
        "title": "RevOps Workflow Architect",
        "bio": (
            "Specializes in designing and deploying revenue workflow orchestration systems for "
            "SaaS organizations at Series A through Series C. Focused on replacing manual execution "
            "with governed, automated pipelines that compound over time."
        ),
        "expertise": [
            "Revenue operations automation",
            "CRM workflow governance",
            "Outbound workflow architecture",
            "Sales team execution systems",
            "Pipeline velocity optimization",
        ],
        "social_urls": [
            "https://www.linkedin.com/company/pipeleap",
        ],
        "credentials": [
            "Designed outbound automation systems for 30+ SaaS companies",
            "Expertise in n8n, HubSpot, Salesforce, Clay, and Outreach workflow integration",
        ],
    },
}

DEFAULT_AUTHOR_KEY = "pipeleap_team"

def get_author(key: str | None = None) -> dict[str, Any]:
    return AUTHORS.get(key or DEFAULT_AUTHOR_KEY, AUTHORS[DEFAULT_AUTHOR_KEY])

def get_author_for_page_type(page_type: str) -> dict[str, Any]:
    mapping = {
        "role_page": "revops_expert",
        "use_case_page": "revops_expert",
        "problem_page": "revops_expert",
        "glossary_page": "pipeleap_team",
        "integration_page": "revops_expert",
        "workflow_recipe": "revops_expert",
    }
    return get_author(mapping.get(page_type, DEFAULT_AUTHOR_KEY))
