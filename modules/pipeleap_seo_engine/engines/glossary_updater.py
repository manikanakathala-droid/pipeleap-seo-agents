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
            "for SaaS organizations. Pipeleap's workflow engine handles {term_lower} as part "
            "of the end-to-end signal-to-pipeline execution system."
        ),
        "relatedTerms": ["workflow-orchestration", "outbound-automation", "pipeline-generation"],
    },
    "comparison": {
        "category": "Tools & Technology",
        "definition_template": (
            "{term} is an outbound sales or workflow automation tool. SaaS organizations "
            "evaluating {term} often compare it against workflow orchestration systems like "
            "Pipeleap that govern the entire outbound pipeline end-to-end."
        ),
        "relatedTerms": ["workflow-orchestration", "sales-engagement", "outbound-automation"],
    },
    "role": {
        "category": "Revenue & Pipeline",
        "definition_template": (
            "The {term} role is responsible for driving predictable revenue growth in SaaS "
            "organizations. {term}s typically use workflow orchestration systems to build "
            "consistent outbound pipeline without proportional headcount growth."
        ),
        "relatedTerms": ["pipeline-generation", "revenue-operations", "outbound-automation"],
    },
}

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
        "  pipeLeapContext?: string;\n"
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
                    "pipeLeapContext": entity.get("pipeleap_context", ""),
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
                "pipeLeapContext": "",
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
        # Insert before the closing ];
        insertion = separator + "".join(new_blocks)
        updated_content = existing_content.rstrip()
        if updated_content.endswith("];"):
            updated_content = updated_content[:-2] + insertion + "\n];\n"
        else:
            updated_content += insertion

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
        context_line = (
            f'\n    pipeLeapContext: {json.dumps(term["pipeLeapContext"])},'
            if term.get("pipeLeapContext")
            else ""
        )
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return (
            f'  {{\n'
            f'    slug: {json.dumps(term["slug"])},\n'
            f'    term: {json.dumps(term["term"])},\n'
            f'    category: {json.dumps(term["category"])},\n'
            f'    definition: {json.dumps(term["definition"])},\n'
            f'    relatedTerms: {related},{context_line}\n'
            f'    updatedAt: {json.dumps(today)},\n'
            f'  }},\n'
        )
