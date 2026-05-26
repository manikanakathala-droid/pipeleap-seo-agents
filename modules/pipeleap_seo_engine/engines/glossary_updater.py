"""
GlossaryUpdater — automatically maintains src/data/glossary-terms.ts.

Runs at the end of every growth engine orchestration run and:
  1. Loads all existing terms from glossary-terms.ts
  2. Runs DuplicateDetector to prevent near-duplicate entries
  3. Collects new terms from: entities.py, generated page primary_keywords
  4. Appends new terms (never deletes existing ones); updates updated_at on changed terms
  5. Writes the updated glossary-terms.ts to the launchpad src/data/ directory
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Fallback definitions for terms the agent discovers but doesn't have in entities.py ──
_GENERATED_TERM_TEMPLATES: dict[str, dict] = {
    "default": {
        "category": "Workflow & Automation",
        "definition_template": (
            "{term} is a key concept in outbound sales automation and workflow orchestration "
            "for SaaS organizations. Understanding {term_lower} helps revenue teams build "
            "more efficient and scalable outbound processes."
        ),
        "relatedTerms": ["workflow-orchestration", "outbound-automation", "pipeline-generation"],
    },
    "comparison": {
        "category": "Tools & Technology",
        "definition_template": (
            "{term} is an outbound sales or workflow automation tool used by B2B organizations. "
            "SaaS teams evaluating {term} typically assess its fit within their existing "
            "tech stack and workflow automation infrastructure."
        ),
        "relatedTerms": ["workflow-orchestration", "sales-engagement", "outbound-automation"],
    },
    "role": {
        "category": "Revenue & Pipeline",
        "definition_template": (
            "The {term} role is responsible for driving predictable revenue growth in SaaS "
            "organizations. Professionals in this role typically use workflow orchestration "
            "systems to build consistent outbound pipeline without proportional headcount growth."
        ),
        "relatedTerms": ["pipeline-generation", "revenue-operations", "outbound-automation"],
    },
}

# ── Research-based seed terms: high-intent, executive-level, Pipeleap-domain ─
# Keyed by slug; each entry has the fields GlossaryUpdater._term_to_ts() expects.
SEED_GLOSSARY_TERMS: list[dict] = [
    # Pipeline
    {
        "slug": "pipeline-coverage-ratio",
        "term": "Pipeline Coverage Ratio",
        "category": "Revenue & Pipeline",
        "definition": (
            "Pipeline coverage ratio is the multiple of open pipeline value relative to quota "
            "for a given period — typically expressed as 3x or 4x. RevOps leaders use it to "
            "determine whether the current pipeline is sufficient to hit the revenue target, "
            "accounting for average win rates. Maintaining healthy coverage ratios requires "
            "continuously generating qualified pipeline through efficient outbound processes."
        ),
        "relatedTerms": ["pipeline-velocity", "forecast-accuracy", "outbound-governance"],
    },
    {
        "slug": "pipeline-velocity",
        "term": "Pipeline Velocity",
        "category": "Revenue & Pipeline",
        "definition": (
            "Pipeline velocity measures how quickly opportunities move through the sales funnel "
            "to closed-won, calculated as (number of deals x average deal value x win rate) / "
            "sales cycle length. VP Sales Strategy teams track it as a leading indicator of "
            "revenue health. Reducing manual handoff latency between enrichment, sequencing, and "
            "CRM update steps is a proven way to improve pipeline velocity."
        ),
        "relatedTerms": ["pipeline-coverage-ratio", "sales-cycle-compression", "revenue-operations"],
    },
    {
        "slug": "pipeline-hygiene",
        "term": "Pipeline Hygiene",
        "category": "Revenue & Pipeline",
        "definition": (
            "Pipeline hygiene refers to the discipline of keeping CRM opportunity records "
            "accurate, complete, and up to date — including correct stage, close date, contact "
            "association, and activity history. Poor pipeline hygiene degrades forecast accuracy "
            "and creates duplicate outreach. Enforcing pipeline hygiene at the workflow level "
            "by writing structured, validated records to CRM on every contact action is a key "
            "RevOps best practice."
        ),
        "relatedTerms": ["crm-hygiene", "forecast-accuracy", "revenue-operations"],
    },
    {
        "slug": "forecast-accuracy",
        "term": "Forecast Accuracy",
        "category": "Revenue & Pipeline",
        "definition": (
            "Forecast accuracy is the degree to which a revenue team's projected bookings match "
            "actual closed-won results within a given period. CROs and VP Sales Ops teams treat "
            "it as a proxy for data quality and process discipline. Common causes of low forecast "
            "accuracy include inconsistent pipeline hygiene, manual stage updates, and lack of "
            "signal-level visibility into deal progression."
        ),
        "relatedTerms": ["pipeline-hygiene", "pipeline-coverage-ratio", "revenue-operations"],
    },
    {
        "slug": "sales-cycle-compression",
        "term": "Sales Cycle Compression",
        "category": "Revenue & Pipeline",
        "definition": (
            "Sales cycle compression is the strategic reduction of average time from first "
            "contact to closed-won, achieved through faster qualification, earlier multi-threading, "
            "and automated follow-up workflows. Revenue leaders target cycle compression to improve "
            "pipeline velocity without increasing headcount. Eliminating manual handoffs between "
            "enrichment, outreach, and CRM update steps is the primary operational lever for "
            "achieving cycle compression."
        ),
        "relatedTerms": ["pipeline-velocity", "outbound-governance", "workflow-orchestration"],
    },
    # RevOps
    {
        "slug": "revenue-operations",
        "term": "Revenue Operations",
        "category": "Revenue & Pipeline",
        "definition": (
            "Revenue operations (RevOps) is the organizational function that aligns sales, "
            "marketing, and customer success around shared data, processes, and technology to "
            "drive predictable revenue growth. RevOps leaders own the GTM tech stack, pipeline "
            "data quality, and workflow governance across the full customer lifecycle. Pipeleap "
            "is built for RevOps-owned outbound orchestration."
        ),
        "relatedTerms": ["gtm-motion", "pipeline-hygiene", "workflow-orchestration"],
    },
    {
        "slug": "gtm-motion",
        "term": "GTM Motion",
        "category": "Revenue & Pipeline",
        "definition": (
            "GTM motion describes the repeatable set of activities, channels, and workflows a "
            "revenue team uses to take a product to market and generate pipeline. Common GTM "
            "motions include product-led growth, outbound-led, and inbound-led. GTM Executives "
            "design and govern the motion; RevOps builds the operational infrastructure "
            "that executes it at scale."
        ),
        "relatedTerms": ["revenue-operations", "outbound-governance", "signal-based-outbound"],
    },
    {
        "slug": "sales-marketing-alignment",
        "term": "Sales-Marketing Alignment",
        "category": "Revenue & Pipeline",
        "definition": (
            "Sales-marketing alignment is the operational state where sales and marketing teams "
            "share a common definition of ICP, agree on lead qualification criteria, and use "
            "shared pipeline data to measure campaign effectiveness. Misalignment is a primary "
            "driver of wasted pipeline — marketing generates volume that sales cannot convert. "
            "Pipeleap's enrichment-first workflow model enforces ICP qualification before any "
            "lead enters the sales motion."
        ),
        "relatedTerms": ["revenue-operations", "gtm-motion", "pipeline-hygiene"],
    },
    {
        "slug": "revenue-architecture",
        "term": "Revenue Architecture",
        "category": "Revenue & Pipeline",
        "definition": (
            "Revenue architecture is the system design layer that connects data sources, "
            "workflow automation, CRM structure, and reporting into a coherent, governed revenue "
            "machine. Unlike point-solution stacks, a revenue architecture is owned end-to-end "
            "by RevOps and is designed to scale without proportional headcount growth. "
            "Pipeleap functions as the execution layer within a modern revenue architecture."
        ),
        "relatedTerms": ["revenue-operations", "workflow-orchestration", "tech-stack-rationalization"],
    },
    # Outbound
    {
        "slug": "signal-based-outbound",
        "term": "Signal-Based Outbound",
        "category": "Outbound & Prospecting",
        "definition": (
            "Signal-based outbound is an outreach methodology that triggers prospecting actions "
            "based on real-time buying signals — such as job changes, technology installs, "
            "funding announcements, or intent data — rather than static lists. It improves "
            "reply rates and reduces wasted outreach by targeting accounts at the moment of "
            "highest receptivity. Pipeleap is built around signal-based workflow triggers as "
            "the primary intake mechanism."
        ),
        "relatedTerms": ["intent-data", "outbound-governance", "enrichment-waterfall"],
    },
    {
        "slug": "intent-data",
        "term": "Intent Data",
        "category": "Outbound & Prospecting",
        "definition": (
            "Intent data is behavioral signal data indicating that a company or individual is "
            "actively researching a product category — derived from web browsing patterns, "
            "content consumption, and search activity. B2B revenue teams use intent data to "
            "prioritize outbound sequences toward accounts showing in-market behavior. "
            "Pipeleap ingests intent signals as workflow triggers for automated, timely outreach."
        ),
        "relatedTerms": ["signal-based-outbound", "account-based-outreach", "enrichment-waterfall"],
    },
    {
        "slug": "account-based-outreach",
        "term": "Account-Based Outreach",
        "category": "Outbound & Prospecting",
        "definition": (
            "Account-based outreach (ABO) is a prospecting strategy that coordinates "
            "multi-channel, multi-threaded outreach across multiple contacts within a single "
            "target account rather than treating each contact independently. VP Sales Enablement "
            "teams implement ABO to improve enterprise win rates by engaging all key stakeholders "
            "simultaneously. Pipeleap orchestrates account-level sequences with CRM deduplication "
            "to prevent conflicting outreach across the same account."
        ),
        "relatedTerms": ["signal-based-outbound", "intent-data", "outbound-governance"],
    },
    {
        "slug": "enrichment-waterfall",
        "term": "Enrichment Waterfall",
        "category": "Outbound & Prospecting",
        "definition": (
            "An enrichment waterfall is a sequential data enrichment strategy that queries "
            "multiple providers in priority order, stopping when sufficient data quality is "
            "reached. If Provider A cannot match a contact, Provider B is queried automatically. "
            "RevOps teams use enrichment waterfalls to maximize match rates while controlling "
            "data costs. Pipeleap's workflow engine implements enrichment waterfalls natively "
            "with per-field quality thresholds and fallback logic."
        ),
        "relatedTerms": ["intent-data", "crm-hygiene", "workflow-orchestration"],
    },
    {
        "slug": "outbound-governance",
        "term": "Outbound Governance",
        "category": "Outbound & Prospecting",
        "definition": (
            "Outbound governance is the set of rules, controls, and audit mechanisms that "
            "ensure outbound sequences run only when data quality, ICP fit, and suppression "
            "criteria are met. Without governance, outbound systems email existing customers, "
            "send duplicate sequences, and degrade deliverability. Pipeleap enforces outbound "
            "governance at the workflow level — sequences cannot fire until all upstream "
            "validation gates pass."
        ),
        "relatedTerms": ["signal-based-outbound", "pipeline-hygiene", "workflow-orchestration"],
    },
    # Sales process
    {
        "slug": "nepq",
        "term": "NEPQ",
        "category": "Sales Process",
        "definition": (
            "NEPQ (Neuro-Emotional Persuasion Questioning) is a sales methodology developed by "
            "Jeremy Miner that uses emotionally-aware questioning to surface a prospect's pain, "
            "consequences of inaction, and desired outcomes before presenting a solution. "
            "VP Sales Enablement teams adopt NEPQ frameworks to move reps away from feature "
            "pitching toward consultative discovery. NEPQ-structured narratives are used in "
            "Pipeleap's content system to mirror the language revenue leaders already use "
            "when diagnosing their own problems."
        ),
        "relatedTerms": ["meddic", "champion-mapping", "sales-cycle-compression"],
    },
    {
        "slug": "meddic",
        "term": "MEDDIC",
        "category": "Sales Process",
        "definition": (
            "MEDDIC is a B2B sales qualification framework — Metrics, Economic Buyer, Decision "
            "Criteria, Decision Process, Identify Pain, Champion — used by enterprise sales "
            "teams to qualify opportunities rigorously before investing resources. CROs implement "
            "MEDDIC to improve forecast accuracy and reduce late-stage deal slippage. Pipeleap "
            "surfaces MEDDIC-relevant contact and account data automatically through its "
            "enrichment and CRM write-back workflows."
        ),
        "relatedTerms": ["spiced", "champion-mapping", "forecast-accuracy"],
    },
    {
        "slug": "champion-mapping",
        "term": "Champion Mapping",
        "category": "Sales Process",
        "definition": (
            "Champion mapping is the process of identifying, qualifying, and enabling an internal "
            "advocate within a target account who can navigate the buying process on behalf of "
            "the vendor. VP Sales Strategy teams treat champion development as the single highest-"
            "leverage activity in enterprise deals. Multi-threading workflows in Pipeleap "
            "support champion mapping by tracking contact engagement across all stakeholders "
            "within an account."
        ),
        "relatedTerms": ["meddic", "account-based-outreach", "multi-threading"],
    },
    {
        "slug": "multi-threading",
        "term": "Multi-Threading",
        "category": "Sales Process",
        "definition": (
            "Multi-threading is the practice of building relationships with multiple stakeholders "
            "across a target account simultaneously, rather than relying on a single point of "
            "contact. It reduces deal risk by ensuring that a single champion departure cannot "
            "kill the opportunity. Pipeleap's account-based outreach workflows support "
            "multi-threading with CRM deduplication to prevent conflicting sequences across "
            "the same account."
        ),
        "relatedTerms": ["champion-mapping", "account-based-outreach", "outbound-governance"],
    },
    # Tech/ops
    {
        "slug": "crm-hygiene",
        "term": "CRM Hygiene",
        "category": "Workflow & Automation",
        "definition": (
            "CRM hygiene is the ongoing practice of maintaining accurate, complete, and "
            "deduplicated records in a CRM system — covering contacts, accounts, opportunities, "
            "and activity history. Poor CRM hygiene causes duplicate outreach, inaccurate "
            "forecasting, and broken handoffs between sales and marketing. Pipeleap enforces "
            "CRM hygiene at the workflow level by validating and structuring data before "
            "every write-back."
        ),
        "relatedTerms": ["pipeline-hygiene", "enrichment-waterfall", "revenue-operations"],
    },
    {
        "slug": "tech-stack-rationalization",
        "term": "Tech Stack Rationalization",
        "category": "Workflow & Automation",
        "definition": (
            "Tech stack rationalization is the process of auditing, consolidating, and removing "
            "redundant or underperforming tools from a revenue team's software stack to reduce "
            "cost, integration overhead, and operational complexity. RevOps leaders undertake "
            "rationalization exercises to replace fragmented point solutions with governed "
            "orchestration platforms. Pipeleap is positioned as the consolidation layer that "
            "replaces 3–5 separate enrichment, sequencing, and CRM tools."
        ),
        "relatedTerms": ["workflow-orchestration", "revenue-architecture", "revenue-operations"],
    },
    {
        "slug": "workflow-orchestration",
        "term": "Workflow Orchestration",
        "category": "Workflow & Automation",
        "definition": (
            "Workflow orchestration is the automated coordination of multi-step processes across "
            "systems, APIs, and data sources in a defined sequence with conditional logic, error "
            "handling, and audit trails. In the context of B2B sales, orchestration governs the "
            "flow from signal intake through enrichment, CRM write-back, sequencing, and reply "
            "routing. Pipeleap's n8n-based workflow engine is purpose-built for outbound sales "
            "orchestration."
        ),
        "relatedTerms": ["outbound-governance", "enrichment-waterfall", "revenue-architecture"],
    },
    {
        "slug": "sequencer",
        "term": "Sequencer",
        "category": "Workflow & Automation",
        "definition": (
            "A sequencer is a sales engagement tool that automates multi-touch outreach cadences "
            "across email, LinkedIn, and phone — managing timing, personalisation, and follow-up "
            "logic. VP Sales Ops teams use sequencers to scale outbound without proportional SDR "
            "headcount. In a governed workflow architecture, the sequencer is one component in "
            "a broader orchestration layer that also handles enrichment, CRM sync, and reply "
            "routing — all of which Pipeleap manages end-to-end."
        ),
        "relatedTerms": ["outbound-governance", "workflow-orchestration", "signal-based-outbound"],
    },
]

# Terms that should never be auto-generated (too generic or off-topic)
_BLOCKLIST = {
    "saas", "b2b", "crm", "api", "email", "linkedin", "sales", "marketing",
    "demo", "audit", "pipeleap", "blog", "resource", "guide", "playbook",
}


class GlossaryUpdater:
    """
    Discovers new glossary terms from each agent run and appends them
    to src/data/glossary-terms.ts for the /glossary React page.
    """

    # Minimum confidence for a fuzzy duplicate match (85%)
    DUPLICATE_THRESHOLD = 0.85

    TS_HEADER = (
        "// AUTO-GENERATED — updated on every agent run by GlossaryUpdater.\n"
        "// Do not edit manually. Add new terms via the Python agent (glossary_updater.py) or entities.py.\n"
        "// The agent appends new terms and never deletes existing ones.\n\n"
        "export interface GlossaryTerm {\n"
        "  slug: string;\n"
        "  term: string;\n"
        "  category: string;\n"
        "  definition: string;\n"
        "  relatedTerms: string[];\n"
        "  updatedAt?: string;\n"
        "}\n\n"
    )

    def __init__(self, launchpad_root: str | Path) -> None:
        self.launchpad_root = Path(launchpad_root)
        self.terms_file = self.launchpad_root / "src" / "data" / "glossary-terms.ts"

    def run(
        self,
        generated_pages: list[Any],
        entities_data: dict | None = None,
    ) -> dict[str, Any]:
        """
        Main entry point. Call after content generation.

        Args:
            generated_pages: list of GrowthPage objects from the current run
            entities_data: ENTITIES dict from entities.py (optional, auto-imported if None)

        Returns: dict with added_count, total_count, new_terms list
        """
        if not self.terms_file.exists():
            return {"added_count": 0, "total_count": 0, "error": "glossary-terms.ts not found"}

        # Load existing slugs from TS file
        existing_content = self.terms_file.read_text(encoding="utf-8")
        existing_slugs = set(re.findall(r'slug:\s*"([a-z0-9-]+)"', existing_content))

        # Initialise duplicate detector against current corpus
        try:
            from modules.pipeleap_seo_engine.glossary.duplicate_detector import DuplicateDetector
            detector = DuplicateDetector(existing_slugs, threshold=self.DUPLICATE_THRESHOLD)
        except Exception:
            detector = None

        # Collect candidate new terms from this run
        candidates: list[dict] = []

        # 0. Research-based seed terms (highest priority — always injected if not already present)
        for seed in SEED_GLOSSARY_TERMS:
            if seed["slug"] not in existing_slugs:
                candidates.append({**seed, "_source": "seed"})
                existing_slugs.add(seed["slug"])

        # 1. From entities.py
        if entities_data is None:
            try:
                from modules.pipeleap_seo_engine.data.entities import ENTITIES
                entities_data = ENTITIES
            except Exception:
                entities_data = {}

        for slug, entity in (entities_data or {}).items():
            if slug not in existing_slugs:
                candidates.append({
                    "slug": slug,
                    "term": entity.get("term", slug.replace("-", " ").title()),
                    "category": "Workflow & Automation",
                    "definition": entity.get("definition", entity.get("short_definition", "")),
                    "relatedTerms": entity.get("related_terms", []),
                    "_source": "entities.py",
                })

        # 2. From generated page primary keywords (use as glossary stubs if new)
        for page in generated_pages:
            kw = getattr(page, "primary_keyword", "").strip().lower()
            if not kw or len(kw.split()) > 5:
                continue
            slug = re.sub(r"[^a-z0-9]+", "-", kw).strip("-")
            if slug in existing_slugs or slug in _BLOCKLIST:
                continue
            # Run duplicate detection — skip if already covered by a canonical term
            if detector:
                result = detector.check(kw)
                if result.is_duplicate:
                    continue
            if any(s in slug for s in _BLOCKLIST):
                continue
            page_type = getattr(page, "page_type", "")
            template_key = (
                "comparison" if "comparison" in page_type or "alternative" in page_type
                else "role" if "role" in page_type
                else "default"
            )
            tmpl = _GENERATED_TERM_TEMPLATES[template_key]
            term_display = kw.replace("-", " ").title()
            candidates.append({
                "slug": slug,
                "term": term_display,
                "category": tmpl["category"],
                "definition": tmpl["definition_template"].format(
                    term=term_display, term_lower=kw
                ),
                "relatedTerms": tmpl["relatedTerms"],
                "_source": f"page:{getattr(page, 'slug', '')}",
            })
            existing_slugs.add(slug)  # prevent duplicates within this run

        # Deduplicate candidates
        seen: set[str] = set()
        unique_candidates = []
        for c in candidates:
            if c["slug"] not in seen:
                seen.add(c["slug"])
                unique_candidates.append(c)

        if not unique_candidates:
            total = len(existing_slugs)
            return {"added_count": 0, "total_count": total, "new_terms": []}

        # Append new term blocks to the TS file
        new_blocks = [self._term_to_ts(c) for c in unique_candidates]
        separator = "\n  // ── Auto-added " + datetime.now(timezone.utc).strftime("%Y-%m-%d") + " ──\n"
        insertion = separator + "".join(new_blocks)
        # Insert into the glossaryTerms array (before its closing ];) not at end of file
        # The file has glossaryCategories after glossaryTerms.
        marker = "];"
        idx = existing_content.rfind(marker + "\nexport const glossaryCategories")
        if idx == -1:
            idx = existing_content.rfind(marker)
        if idx != -1:
            updated_content = existing_content[:idx] + insertion + "\n" + marker + existing_content[idx + len(marker):]
        else:
            updated_content = existing_content + insertion

        # Regenerate categories export
        all_slugs_after = set(re.findall(r'slug:\s*"([a-z0-9-]+)"', updated_content))
        self.terms_file.write_text(updated_content, encoding="utf-8")

        return {
            "added_count": len(unique_candidates),
            "total_count": len(all_slugs_after),
            "new_terms": [c["slug"] for c in unique_candidates],
        }

    @staticmethod
    def _term_to_ts(term: dict) -> str:
        """Convert a term dict to a TypeScript object literal."""
        related = json.dumps(term.get("relatedTerms", []))
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return (
            f'  {{\n'
            f'    slug: {json.dumps(term["slug"])},\n'
            f'    term: {json.dumps(term["term"])},\n'
            f'    category: {json.dumps(term["category"])},\n'
            f'    definition: {json.dumps(term["definition"])},\n'
            f'    relatedTerms: {related},\n'
            f'    updatedAt: {json.dumps(today)},\n'
            f'  }},\n'
        )
