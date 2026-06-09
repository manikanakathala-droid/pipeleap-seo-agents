"""
LLM-powered sales tool content engine.

Generates Tool[] entries that match the existing frontend data model in
temp_frontend_repo/src/types/tool.ts. Designed for batch generation per
category with dedup against existing entries.

Governance rules (enforced at generation & validation):
- Pipeleap is never described as an alternative to any tool
- pipeLeapContext describes orchestration (never replacement)
- No em dashes, asterisks, markdown, or emojis in any string field
- Natural human tone — no "delve", "unleash", "game-changer"
- Every tool has: min 3 features, 2 pros, 2 cons, 2 useCases
- alternatives[] reference other real tool slugs
- pricing.model must be one of: Free, Freemium, Paid, Contact
- All required fields populated (faqs may be empty array)
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

from connectors.llm_client import LLMClient

_EXISTING_TOOL_SLUGS: set[str] = set()

CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "ai-sdr-tools": "AI-powered sales development representatives",
    "cold-email-tools": "Cold email outreach and deliverability",
    "sales-engagement-tools": "Multi-channel sales engagement platforms",
    "prospecting-tools": "B2B prospecting and contact databases",
    "lead-enrichment-tools": "Lead enrichment and data append",
    "crm-tools": "Customer relationship management platforms",
    "call-recording-tools": "Call recording and conversation intelligence",
    "revenue-intelligence-tools": "Revenue intelligence and forecasting",
    "linkedin-automation-tools": "LinkedIn automation for outreach",
    "ai-outbound-agents": "Autonomous AI outbound agents",
    "workflow-automation-tools": "Workflow automation and orchestration",
    "sales-analytics-tools": "Sales analytics and BI for pipeline",
    "gtm-engineering-tools": "GTM engineering and data infrastructure",
    "intent-data-tools": "Buyer intent data and predictive scoring platforms",
    "data-providers": "B2B company and contact data providers",
    "list-building-tools": "Lead list building and account research tools",
    "email-deliverability-tools": "Email deliverability and infrastructure",
    "email-validation-tools": "Email verification and validation tools",
    "meeting-scheduling-tools": "Meeting scheduling and booking platforms",
    "demo-platforms": "Product demo and interactive walkthrough tools",
    "video-prospecting-tools": "Video messaging for sales prospecting",
    "ipaas-tools": "Integration platform as a service for sales stack",
    "cdp-tools": "Customer data platforms for unified sales data",
    "conversation-intelligence-tools": "Sales conversation analysis and coaching",
    "sales-coaching-tools": "Sales coaching and training platforms",
    "sales-copilot-tools": "AI sales copilots and assistive tools",
    "chatbots-live-chat": "Chatbots and live chat for website engagement",
    "forecasting-tools": "Sales forecasting and revenue intelligence",
    "pipeline-analytics-tools": "Pipeline analytics and inspection tools",
    "sales-enablement-tools": "Sales enablement and content management",
    "proposal-tools": "Proposal generation and document management",
    "e-signature-tools": "E-signature and contract approval platforms",
    "payment-tools": "Payment processing and billing platforms",
    "deal-desk-tools": "Deal desk and pricing optimization tools",
    "cpq-tools": "Configure price quote platforms",
    "contract-management-tools": "Contract lifecycle management tools",
    "content-management-tools": "Content management for sales teams",
}

_SLUG_VARIANTS: dict[str, str] = {
    "clearbit-enrich": "clearbit",
    "apollo": "apollo-io-enrich",
    "salesforce-crm": "salesforce",
    "hubspot-crm": "hubspot-crm",
}

_STRIP_RE = re.compile(r"[\*\_\[\]\(\)]")
_EM_DASH_RE = re.compile(r"—|--")
_EMOJI_RE = re.compile(r"[^\x00-\x7F\x80-\xFF\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\-_,.;:!?\'\"()\[\]{}\/@#\$%\^&\+=<>~\s]")


def _normalize_field(text: str) -> str:
    text = _EM_DASH_RE.sub("-", text)
    text = _STRIP_RE.sub("", text)
    text = _EMOJI_RE.sub("", text)
    return text.strip()


def _validate_tool(entry: dict, existing_slugs: set[str]) -> list[str]:
    errors: list[str] = []
    slug = entry.get("slug", "")

    if not slug:
        errors.append("Missing slug")
    if not entry.get("name"):
        errors.append("Missing name")
    if not entry.get("categorySlug"):
        errors.append("Missing categorySlug")
    if not entry.get("tagline") or len(entry.get("tagline", "")) > 120:
        errors.append("tagline missing or >120 chars")
    if not entry.get("description") or len(entry.get("description", "")) > 160:
        errors.append("description missing or >160 chars")
    if not entry.get("longDescription"):
        errors.append("Missing longDescription")
    elif len(entry.get("longDescription", "")) < 200:
        errors.append(f"longDescription too short ({len(entry.get('longDescription', ''))} chars, need >=200)")
    if not entry.get("website"):
        errors.append("Missing website")

    pricing = entry.get("pricing", {})
    if pricing.get("model") not in ("Free", "Freemium", "Paid", "Contact"):
        errors.append(f"Invalid pricing.model: {pricing.get('model')}")

    for field in ("features", "pros", "cons", "useCases"):
        items = entry.get(field, [])
        if not isinstance(items, list) or len(items) < (3 if field == "features" else 2):
            errors.append(f"{field}: need at least {'3' if field == 'features' else '2'} items, got {len(items) if isinstance(items, list) else 'not a list'}")

    best_for = entry.get("bestFor", [])
    if not isinstance(best_for, list) or len(best_for) < 2:
        errors.append("bestFor: need at least 2 items")

    alt_list = entry.get("alternatives", [])
    if not isinstance(alt_list, list):
        errors.append("alternatives must be a list")

    pipeleap = str(entry.get("pipeLeapContext", "") or "")
    lower_pipeleap = pipeleap.lower()
    if "alternative" in lower_pipeleap or "replacement" in lower_pipeleap or "instead of" in lower_pipeleap:
        errors.append("pipeLeapContext must not frame Pipeleap as alternative/replacement")

    faqs = entry.get("faqs", [])
    if not isinstance(faqs, list):
        errors.append("faqs must be a list")

    if slug and slug in existing_slugs:
        errors.append(f"Duplicate slug: {slug}")

    return errors


class ToolContentEngine:
    """Generates Tool[] entries via LLM for a given category."""

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger
        self.llm = LLMClient()

    def generate(
        self,
        category_slug: str,
        count: int = 10,
        existing_slugs: set[str] | None = None,
        existing_names: set[str] | None = None,
    ) -> list[dict]:
        """Generate tool entries for a category."""
        if not self.llm.is_configured:
            self.logger.warning("LLM not configured — cannot generate tool entries")
            return []

        cat_description = CATEGORY_DESCRIPTIONS.get(category_slug, category_slug.replace("-", " ").title())
        cat_display_name = category_slug.replace("-", " ").title()

        existing = existing_slugs or set()
        existing_names_set = existing_names or set()

        prompt = f"""You are a sales technology research analyst. Generate {count} real, well-known sales tools for the category "{cat_display_name}" ({cat_description}).

Return a JSON array of tool objects. Each object must have these exact fields:
- slug: URL-friendly unique ID (e.g. "clay", "clearbit", "zoominfo"). Use lowercase kebab-case. Do NOT use any of these existing slugs: {', '.join(sorted(existing)[:5])}
- name: Display name (e.g. "Clay", "Clearbit", "ZoomInfo")
- categorySlug: "{category_slug}"
- tagline: Short one-liner, max 120 chars
- description: Meta description, max 160 chars
- longDescription: 2-4 sentence detailed body
- website: Full URL starting with https://
- pricing: {{"model": "Free"|"Freemium"|"Paid"|"Contact", "startingAt": "$X/mo" or "Contact" (optional), "hasFree": true/false}}
- bestFor: Array of 2-3 ideal user descriptions
- features: Array of 4-5 key features
- pros: Array of 3-4 advantages
- cons: Array of 2-3 disadvantages
- alternatives: Array of 2-3 slug strings of well-known competitor tools in the same category
- useCases: Array of 3-4 use case descriptions
- pipeLeapContext: String describing how this tool fits with Pipeleap's workflow orchestration layer. Pipeleap is an orchestration layer that connects tools — NOT an alternative or competitor. Never say "alternative to Pipeleap" or "Pipeleap replacement".
- faqs: Array of {{"q": "question", "a": "answer"}} objects (can be empty)
- publishedAt: "2026-06-09"

TOOL ENTRY RULES (scrict - follow exactly):
1. No em dashes (— or --) — use plain hyphens
2. No asterisks, bold, italics, or markdown in ANY string
3. No emojis
4. No AI-sounding language: never use "delve", "unleash", "game-changer", "revolutionary", "cutting-edge"
5. Natural human tone, factual descriptions
6. features must have 4-5 items, pros 3-4, cons 2-3, useCases 3-4
7. pricing.model must be exactly "Free", "Freemium", "Paid", or "Contact"
8. pipeLeapContext MUST NOT say Pipeleap is an alternative, replacement, or competitor to this tool. Pipeleap sits ABOVE tools as an orchestration layer.

Return ONLY the JSON array. No explanation, no markdown fences."""

        try:
            raw = self.llm.generate(prompt, model="gpt-4o-mini", max_tokens=4096, temperature=0.7)
            if not raw:
                self.logger.warning("LLM returned empty for category %s", category_slug)
                return []

            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[-1]
                if clean.endswith("```"):
                    clean = clean[:-3]
                clean = clean.strip()

            entries = json.loads(clean)
            if isinstance(entries, dict):
                entries = [entries]

            valid: list[dict] = []
            for entry in entries:
                for k, v in list(entry.items()):
                    if isinstance(v, str):
                        entry[k] = _normalize_field(v)
                    elif isinstance(v, list):
                        entry[k] = [_normalize_field(i) if isinstance(i, str) else i for i in v]
                    elif isinstance(v, dict):
                        entry[k] = {sk: _normalize_field(sv) if isinstance(sv, str) else sv for sk, sv in v.items()}

                errs = _validate_tool(entry, existing)
                slug = entry.get("slug", "?")
                name = entry.get("name", "?")

                if entry.get("name", "").lower() in existing_names_set:
                    self.logger.info("Tool '%s' (%s) skipped — name already exists", slug, name)
                    continue

                if errs:
                    self.logger.warning("Tool '%s' (%s) validation errors: %s", slug, name, errs)
                    continue

                valid.append(entry)
                existing.add(slug)
                existing_names_set.add(entry.get("name", "").lower())

            self.logger.info("ToolEngine: %d/%d entries valid for category %s", len(valid), len(entries), category_slug)
            return valid

        except json.JSONDecodeError as exc:
            self.logger.warning("ToolEngine JSON parse failed for %s: %s", category_slug, exc)
            return []
        except Exception as exc:
            self.logger.warning("ToolEngine generation failed for %s: %s", category_slug, exc)
            return []
