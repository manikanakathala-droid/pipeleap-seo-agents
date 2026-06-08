from __future__ import annotations

"""
Repo Writer — Output-to-repo mapping layer for the SEO OS.

All agent outputs are written to versioned, structured paths in the
workflows repo. Nothing overwrites blindly — every write is timestamped
and appended or merged so the repo is the single source of truth for
all SEO work.

Output paths:
  /content/blogs/{slug}.md            — blog post markdown
  /content/glossary/{slug}.md         — glossary page markdown
  /seo/metadata-updates.json          — on-page meta recommendations (append)
  /seo/internal-links.json            — internal linking map (merge by URL)
  /seo/keywords.json                  — keyword research (append by run_id)
  /seo/technical-audit.md             — technical audit log (append by run_id)
  /seo/indexing-queue.json         — indexing actions (append, mark status)


STRICT RULES:
  - Never modify /src/, /public/, or any core website path
  - Always timestamp entries
  - Tag unsafe changes as REQUIRES_DEV_REVIEW
  - Keep all JSON machine-readable (no prose fields in arrays)
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("repo_writer")

# Absolute root of the workflows repo checkout (set at runtime by the agent)
_REPO_ROOT: Path = Path(".")

# Paths that must never be touched
_PROTECTED_PREFIXES = [
    "src/", "public/", "index.html", "package.json",
    "tailwind.config", "vite.config", "tsconfig",
    "components.json", "postcss.config",
]


def configure(repo_root: str | Path) -> None:
    """Call once at startup with the absolute path to the workflows repo root."""
    global _REPO_ROOT
    _REPO_ROOT = Path(repo_root)
    _ensure_structure()


def _ensure_structure() -> None:
    for d in [
        "content/blogs",
        "content/glossary",
        "seo",
        "seo/history",
    ]:
        (_REPO_ROOT / d).mkdir(parents=True, exist_ok=True)
    # Ensure base JSON files exist with empty structures
    _init_json("seo/metadata-updates.json", [])
    _init_json("seo/internal-links.json", [])
    _init_json("seo/keywords.json", [])
    _init_json("seo/indexing-queue.json", [])
    _init_json("seo/run-log.json", [])


def _init_json(rel_path: str, default: Any) -> None:
    path = _REPO_ROOT / rel_path
    if not path.exists():
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")


def _safe_path(rel_path: str) -> Path:
    for prefix in _PROTECTED_PREFIXES:
        if rel_path.startswith(prefix):
            raise ValueError(
                f"FAILSAFE: attempted write to protected path '{rel_path}'. "
                "Log under REQUIRES_DEV_REVIEW instead."
            )
    return _REPO_ROOT / rel_path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── 1. Blog content ────────────────────────────────────────────────────────────

def write_blog(run_id: str, brief: dict) -> str:
    """
    Write a blog post brief as markdown to /content/blogs/{slug}.md
    Returns the relative path written.
    """
    slug = brief.get("slug", "untitled")
    path = _safe_path(f"content/blogs/{slug}.md")

    # Don't overwrite a fully-published post — append a new draft section
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    timestamp = _now()

    structure = brief.get("structure", [])
    eeat = brief.get("eeat_notes", [])
    links = brief.get("internal_links", [])

    md_lines = [
        f"---",
        f"run_id: {run_id}",
        f"generated_at: {timestamp}",
        f"slug: {slug}",
        f"title: \"{brief.get('title', '')}\"",
        f"seo_title: \"{brief.get('seo_title', brief.get('title', ''))}\"",
        f"meta_description: \"{brief.get('meta_description', '')}\"",
        f"target_keyword: \"{brief.get('target_keyword', '')}\"",
        f"cluster: \"{brief.get('cluster', '')}\"",
        f"persona: \"{brief.get('persona', '')}\"",
        f"status: draft",
        f"---",
        "",
        f"# {brief.get('title', '')}",
        "",
        f"**Target keyword:** {brief.get('target_keyword', '')}  ",
        f"**Persona:** {brief.get('persona', '')}  ",
        f"**Pillar page:** [{brief.get('pillar_link', '/')}]({brief.get('pillar_link', '/')})",
        "",
        "## Content Structure",
        "",
    ]
    for item in structure:
        md_lines.append(f"- {item}")

    md_lines += [
        "",
        "## Internal Links",
        "",
    ]
    for link in links:
        md_lines.append(f"- [{link}]({link})")

    md_lines += [
        "",
        "## E-E-A-T Requirements",
        "",
    ]
    for note in eeat:
        md_lines.append(f"- {note}")

    md_lines += [
        "",
        "---",
        f"*SEO OS draft — run {run_id} — {timestamp}*",
    ]

    content = "\n".join(md_lines)
    if existing:
        content = existing.rstrip() + "\n\n<!-- NEW DRAFT " + run_id + " -->\n\n" + content
    path.write_text(content, encoding="utf-8")
    logger.info("Blog written: %s", path)
    return f"content/blogs/{slug}.md"


# ── 2. Glossary content ────────────────────────────────────────────────────────

def write_glossary(run_id: str, term: dict) -> str:
    """
    Write a glossary term to /content/glossary/{slug}.md
    Returns the relative path written.
    """
    slug = term.get("slug", "untitled")
    path = _safe_path(f"content/glossary/{slug}.md")
    timestamp = _now()
    links = term.get("internal_links", [])
    related = term.get("related_terms", [])

    md_lines = [
        f"---",
        f"run_id: {run_id}",
        f"generated_at: {timestamp}",
        f"slug: {slug}",
        f"title: \"{term.get('title', '')}\"",
        f"status: draft",
        f"---",
        "",
        f"# {term.get('title', '')}",
        "",
        "## Definition",
        "",
        term.get("definition", ""),
        "",
        "## Related Terms",
        "",
    ]
    for rt in related:
        md_lines.append(f"- {rt}")

    md_lines += [
        "",
        "## Internal Links",
        "",
    ]
    for link in links:
        md_lines.append(f"- [{link}]({link})")

    md_lines += [
        "",
        "---",
        f"*SEO OS glossary — run {run_id} — {timestamp}*",
    ]

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        content = existing.rstrip() + "\n\n<!-- UPDATED " + run_id + " -->\n\n" + "\n".join(md_lines)
    else:
        content = "\n".join(md_lines)

    path.write_text(content, encoding="utf-8")
    logger.info("Glossary written: %s", path)
    return f"content/glossary/{slug}.md"


# ── 3. Metadata updates ────────────────────────────────────────────────────────

def write_metadata_updates(run_id: str, optimised_pages: list[dict]) -> str:
    """
    Append on-page SEO recommendations to /seo/metadata-updates.json
    Each entry is versioned with run_id and timestamp.
    Schema:
      { run_id, generated_at, url, title, meta_description, recommended_changes[], safe_to_apply }
    """
    path = _safe_path("seo/metadata-updates.json")
    existing: list[dict] = json.loads(path.read_text(encoding="utf-8"))
    existing_urls = {e["url"] for e in existing}

    timestamp = _now()
    for page in optimised_pages:
        url = page.get("page_url", "")
        entry = {
            "run_id": run_id,
            "generated_at": timestamp,
            "url": url,
            "current_title": page.get("current_title", ""),
            "current_meta": page.get("current_meta", ""),
            "title": page.get("recommended_title", ""),
            "meta_description": page.get("recommended_meta", ""),
            "recommended_changes": page.get("optimisation_actions", []),
            "safe_to_apply": page.get("safe_mode", True),
            "requires_dev_review": page.get("requires_dev", False),
        }
        # Always append — reviewer can see history across runs
        existing.append(entry)

    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Metadata updates written: %d entries total", len(existing))
    return "seo/metadata-updates.json"


# ── 4. Internal links ──────────────────────────────────────────────────────────

def write_internal_links(run_id: str, links: list[dict]) -> str:
    """
    Merge internal linking recommendations into /seo/internal-links.json
    De-duplicates by (from_page, to_page) pair — updates existing entries.
    Schema:
      { from_page, to_page, anchor_text, placement, cluster, priority, run_id, updated_at }
    """
    path = _safe_path("seo/internal-links.json")
    existing: list[dict] = json.loads(path.read_text(encoding="utf-8"))

    index: dict[str, dict] = {
        f"{e['from_page']}|||{e['to_page']}": e for e in existing
    }
    timestamp = _now()

    for link in links:
        key = f"{link.get('from_page', '')}|||{link.get('to_page', '')}"
        entry = {
            "from_page": link.get("from_page", ""),
            "to_page": link.get("to_page", ""),
            "anchor_text": link.get("anchor_text", ""),
            "placement": link.get("placement", ""),
            "cluster": link.get("cluster", ""),
            "priority": link.get("priority", "medium"),
            "note": link.get("note", "Content-level link only."),
            "run_id": run_id,
            "updated_at": timestamp,
        }
        index[key] = entry

    merged = list(index.values())
    path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Internal links written: %d entries total", len(merged))
    return "seo/internal-links.json"


# ── 5. Keywords ────────────────────────────────────────────────────────────────

def write_keywords(run_id: str, keywords: list[dict]) -> str:
    """
    Append keyword research to /seo/keywords.json
    Each run appends a versioned block — no overwriting of prior research.
    """
    path = _safe_path("seo/keywords.json")
    existing: list[dict] = json.loads(path.read_text(encoding="utf-8"))

    block = {
        "run_id": run_id,
        "generated_at": _now(),
        "count": len(keywords),
        "keywords": keywords,
    }
    existing.append(block)

    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Keywords written: %d keywords in run %s", len(keywords), run_id)
    return "seo/keywords.json"


# ── 6. Technical audit ────────────────────────────────────────────────────────

def write_technical_audit(run_id: str, issues: list[dict], seo_score: dict) -> str:
    """
    Append technical audit results to /seo/technical-audit.md
    Each run appends a dated section — never overwrites prior audits.
    """
    path = _safe_path("seo/technical-audit.md")
    timestamp = _now()

    safe_issues = [i for i in issues if not i.get("requires_dev_review", i.get("requires_dev", False))]
    dev_issues = [i for i in issues if i.get("requires_dev_review", i.get("requires_dev", False))]

    score = seo_score or {}

    lines = [
        f"\n\n---\n",
        f"## Audit Run: {run_id}",
        f"**Date:** {timestamp}  ",
        f"**SEO Score:** {score.get('overall', 'N/A')}/100  ",
        f"| Technical | Content | Indexing | Authority |",
        f"|---|---|---|---|",
        f"| {score.get('technical', '-')}/100 | {score.get('content', '-')}/100 | {score.get('indexing', '-')}/100 | {score.get('authority', '-')}/100 |",
        "",
        "### SAFE TO APPLY",
        "",
    ]

    if safe_issues:
        for issue in safe_issues:
            lines.append(f"- **[{issue.get('category', '').upper()}]** `{issue.get('page_url', '')}` — {issue.get('title', '')}")
    else:
        lines.append("- No safe-mode issues detected this run.")

    lines += [
        "",
        "### REQUIRES DEV REVIEW",
        "",
    ]

    if dev_issues:
        for issue in dev_issues:
            lines.append(
                f"- **[{issue.get('category', '').upper()}]** `{issue.get('page_url', '')}` — "
                f"{issue.get('title', '')}  "
            )
            if issue.get("dev_note"):
                lines.append(f"  > {issue['dev_note']}")
    else:
        lines.append("- No dev-review items this run.")

    existing = path.read_text(encoding="utf-8") if path.exists() else "# Pipeleap Technical SEO Audit Log\n\nAppended on every SEO OS run.\n"
    path.write_text(existing + "\n".join(lines), encoding="utf-8")
    logger.info("Technical audit written for run %s", run_id)
    return "seo/technical-audit.md"


# ── 7. Indexing queue ─────────────────────────────────────────────────────────

def write_indexing_queue(run_id: str, actions: list[dict]) -> str:
    """
    Append indexing actions to /seo/indexing-queue.json
    Each entry gets a status field: pending | submitted | done
    Never removes prior entries — status updates flow forward.
    """
    path = _safe_path("seo/indexing-queue.json")
    existing: list[dict] = json.loads(path.read_text(encoding="utf-8"))

    existing_urls = {e["url"]: i for i, e in enumerate(existing)}
    timestamp = _now()

    for action in actions:
        url = action.get("url", "")
        entry = {
            "run_id": run_id,
            "queued_at": timestamp,
            "url": url,
            "action": action.get("action", "submit_url"),
            "reason": action.get("reason", ""),
            "priority": action.get("priority", 3),
            "status": "pending",
        }
        if url in existing_urls:
            # Only add if this run has a new/different action type
            prev = existing[existing_urls[url]]
            if prev.get("action") != entry["action"] or prev.get("status") == "done":
                existing.append(entry)
        else:
            existing.append(entry)

    # Sort: pending first, then by priority
    existing.sort(key=lambda x: (0 if x["status"] == "pending" else 1, x.get("priority", 3)))
    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Indexing queue written: %d entries total", len(existing))
    return "seo/indexing-queue.json"


# ── 9. Run log ────────────────────────────────────────────────────────────────

def write_run_log(run_id: str, result_summary: dict) -> str:
    """
    Append a summary entry to /seo/run-log.json after every run.
    This is the master audit trail.
    """
    path = _safe_path("seo/run-log.json")
    existing: list[dict] = json.loads(path.read_text(encoding="utf-8"))

    entry = {
        "run_id": run_id,
        "generated_at": _now(),
        "seo_score": result_summary.get("seo_score", {}).get("overall", 0),
        "mode": result_summary.get("mode", ""),
        "website_changes": result_summary.get("website_changes", {}),
        "safe_actions": len(result_summary.get("safe_actions", [])),
        "dev_review_items": len(result_summary.get("dev_review_items", [])),
        "content_generated": len(result_summary.get("content_generated", [])),
        "keywords_researched": len(result_summary.get("keyword_opportunities", [])),
        "indexing_actions": len(result_summary.get("indexing_actions", [])),
        "errors": result_summary.get("errors", []),
        "output_files": result_summary.get("output_files", []),
    }
    existing.append(entry)

    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Run log updated: %d total runs", len(existing))
    return "seo/run-log.json"


# ── Master write orchestrator ─────────────────────────────────────────────────

def write_all(run_id: str, result: dict, repo_root: str | Path = ".") -> list[str]:
    """
    Single call that maps all agent outputs to correct repo paths.
    Returns list of relative paths written.
    Safe mode enforced: any path outside allowed prefixes raises ValueError.
    """
    configure(repo_root)
    written: list[str] = []
    timestamp = _now()

    # Content
    for item in result.get("content_generated", []):
        try:
            if item.get("type") == "blog_post":
                written.append(write_blog(run_id, item))
            elif item.get("type") == "glossary_page":
                written.append(write_glossary(run_id, item))
        except Exception as exc:
            logger.error("Content write failed for %s: %s", item.get("slug", "?"), exc)

    # Metadata
    if result.get("pages_optimized"):
        try:
            written.append(write_metadata_updates(run_id, result["pages_optimized"]))
        except Exception as exc:
            logger.error("Metadata write failed: %s", exc)

    # Internal links
    if result.get("linking_suggestions"):
        try:
            written.append(write_internal_links(run_id, result["linking_suggestions"]))
        except Exception as exc:
            logger.error("Links write failed: %s", exc)

    # Keywords
    if result.get("keyword_opportunities"):
        try:
            written.append(write_keywords(run_id, result["keyword_opportunities"]))
        except Exception as exc:
            logger.error("Keywords write failed: %s", exc)

    # Technical audit
    all_issues = result.get("safe_actions", []) + result.get("dev_review_items", [])
    technical_issues = [i for i in all_issues if i.get("category") in ("technical", "metadata", "canonical", "robots", "performance")]
    if technical_issues or result.get("seo_score"):
        try:
            written.append(write_technical_audit(run_id, technical_issues, result.get("seo_score", {})))
        except Exception as exc:
            logger.error("Technical audit write failed: %s", exc)

    # Indexing queue
    if result.get("indexing_actions"):
        try:
            written.append(write_indexing_queue(run_id, result["indexing_actions"]))
        except Exception as exc:
            logger.error("Indexing queue write failed: %s", exc)

    # Run log — always last
    try:
        written.append(write_run_log(run_id, result))
    except Exception as exc:
        logger.error("Run log write failed: %s", exc)

    logger.info("repo_writer.write_all complete: %d files written for run %s", len(written), run_id)
    return written
