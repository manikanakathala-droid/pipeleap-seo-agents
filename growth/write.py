"""
Draft pages with an LLM, grounded in what the site says, revised against the quality gate.

There is no template fallback. Without model credentials the loop writes a
brief for a person instead of publishing filler.

Provider: any OpenAI-compatible chat endpoint.
  LLM_API_KEY / LLM_BASE_URL / LLM_MODEL   explicit provider
  GITHUB_MODELS_TOKEN or GITHUB_TOKEN       GitHub Models (default endpoint)
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Callable

from growth import quality

GITHUB_MODELS_URL = "https://models.github.ai/inference"


@dataclass
class Draft:
    query: str
    cluster: str
    title: str
    description: str
    markdown: str
    report: quality.QualityReport
    attempts: int


def default_llm() -> Callable[[str], str] | None:
    key = os.getenv("LLM_API_KEY") or os.getenv("GITHUB_MODELS_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not key:
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None
    client = OpenAI(api_key=key, base_url=os.getenv("LLM_BASE_URL") or GITHUB_MODELS_URL)
    model = os.getenv("LLM_MODEL") or "openai/gpt-4o"

    def generate(prompt: str) -> str:
        response = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}], temperature=0.6)
        return response.choices[0].message.content or ""

    return generate


def build_brief(*, query: str, cluster: str, cluster_spec: dict[str, Any], evidence: dict[str, Any],
                related_queries: list[str], link_targets: list[tuple[str, str]], site_facts: str,
                growth: dict[str, Any]) -> str:
    rules = growth.get("quality", {})
    links = "\n".join(f"- {path}: {label}" for path, label in link_targets)
    related = "\n".join(f"- {q}" for q in related_queries[:12]) or "- (none observed yet)"
    return f"""You are writing one page for {growth.get('brand', 'Pipeleap')}'s website.

READER
{growth.get('icp', {}).get('description', '')}
They searched for: "{query}"
Topic cluster: {cluster}. {cluster_spec.get('angle', '')}

WHAT THE PAGE MUST DO
Answer the search fully and practically, so a sales leader or RevOps lead could act on it without
buying anything. Then show, in one short section near the end, where the product fits. A reader
who recognises their own team in the page is the outcome that matters.

RELATED SEARCHES PEOPLE ACTUALLY MAKE (cover the relevant ones as sections or questions)
{related}

PRODUCT FACTS: the only claims you may make about the product. Do not add features, prices,
customers, integrations or results that are not stated here.
---
{site_facts}
---

INTERNAL LINKS (use at least {rules.get('min_internal_links', 2)}, as Markdown links with these exact paths)
{links}

RULES
- {rules.get('min_words', 800)} to {rules.get('max_words', 1600)} words of Markdown. Start with a 2-3 sentence direct answer.
- Use ## for sections (at least three) and ### below that. No # heading; the template renders the title.
- No statistics, percentages, money amounts or study references unless you link the source in the same paragraph.
  If you are not certain of a source, describe the point qualitatively instead.
- No invented anecdotes, customers, quotes or first-person experience.
- Plain, specific language. Name the actual tasks, tools and handoffs. No filler, no hype.
- Never use: {', '.join(rules.get('banned_phrases', []))}.

OUTPUT FORMAT (exactly)
TITLE: <30-65 characters, contains the search phrase naturally>
DESCRIPTION: <110-160 characters, says what the reader gets>
---
<markdown body>
"""


def parse(response: str) -> tuple[str, str, str]:
    title = re.search(r"^TITLE:\s*(.+)$", response, re.M)
    description = re.search(r"^DESCRIPTION:\s*(.+)$", response, re.M)
    body = response.split("\n---", 1)[1] if "\n---" in response else ""
    return (title.group(1).strip() if title else "", description.group(1).strip() if description else "",
            body.strip().removeprefix("```markdown").removesuffix("```").strip())


class Writer:
    def __init__(self, llm: Callable[[str], str] | None, growth: dict[str, Any]) -> None:
        self.llm = llm
        self.growth = growth

    @property
    def available(self) -> bool:
        return self.llm is not None

    def draft(self, brief: str, *, query: str, cluster: str, site_facts: str,
              existing_texts: dict[str, str], max_attempts: int = 3) -> Draft | None:
        if self.llm is None:
            return None
        rules = self.growth.get("quality", {})
        cta = self.growth.get("cta", {}).get("url", "")
        prompt, best = brief, None
        for attempt in range(1, max_attempts + 1):
            title, description, body = parse(self.llm(prompt))
            report = quality.check(body, title=title, description=description, query=query,
                                   site_facts=site_facts, existing_texts=existing_texts,
                                   rules=rules, cta_url=cta)
            best = Draft(query, cluster, title, description, body, report, attempt)
            if report.passed:
                break
            prompt = (f"{brief}\n\nYour previous draft was rejected for these reasons:\n- "
                      + "\n- ".join(report.failures)
                      + "\n\nRewrite the full page fixing every one of them. Previous draft:\n\n"
                      + f"TITLE: {title}\nDESCRIPTION: {description}\n---\n{body}")
        return best
