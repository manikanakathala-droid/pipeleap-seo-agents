"""
API Backlink Publisher — programmatic backlinks via platform APIs.
No browser, no CAPTCHA, no form submissions.

Platforms:
  GitHub  DA95 — create public repos + gists that link to pipeleap.com
  DEV.to  DA74 — publish full articles via API key
  Hashnode DA73 — publish blog posts via GraphQL token
  Medium  DA96 — publish via integration token
  PyPI    DA85 — publish pipeleap-tools Python package

Setup (one-time per platform):
  GitHub:   use GITHUB_TOKEN env var (same one used for launchpad pushes)
  DEV.to:   get API key at https://dev.to/settings/extensions → "DEV Community API Keys"
  Hashnode: get token at https://hashnode.com/settings/developer → "Generate new token"
  Medium:   get token at https://medium.com/me/settings/security → "Integration tokens"
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

SITE_URL = "https://pipeleap.com"
OUTPUT   = Path("outputs/backlinks/api_submissions")
OUTPUT.mkdir(parents=True, exist_ok=True)


# ── Article content (same article, repurposed per platform) ───────────────────

ARTICLES = [
    {
        "slug":    "why-saas-outbound-has-governance-problem",
        "title":   "Why Your SaaS Outbound Stack Has a Governance Problem (Not a Tooling Problem)",
        "tags":    ["sales", "saas", "automation", "outbound", "revops"],
        "canonical": f"{SITE_URL}/blog/why-do-outbound-workflows-need-orchestration",
        "body": f"""Most B2B sales teams I talk to have the same stack: Apollo or Clay for data, HubSpot or Salesforce as CRM, Outreach or Instantly for sequencing. And yet pipeline is still unpredictable.

**The problem isn't the tools. It's the absence of an orchestration layer.**

## What "workflow orchestration" actually means

A sequencer fires emails automatically. An enrichment tool finds contact data. A CRM stores pipeline records. None of these tools govern how they work together.

When a signal fires, someone still has to:
- Research the prospect manually
- Build or update the list
- Enroll them in the right sequence by hand
- Monitor the inbox for replies
- Route interested replies to the right rep
- Log the outcome in the CRM

**That manual work between tools is the governance gap.** And it's where most outbound fails.

## The 5-stage orchestration model

A governed outbound workflow looks like this:

1. **Signal Capture** — detect buying intent automatically
2. **Enrichment** — append firmographics at intake, no manual research
3. **Sequence Routing** — qualify and enroll automatically based on segment
4. **Reply Routing** — classify and route without inbox monitoring
5. **CRM Write-Back** — log every touchpoint automatically

When all five are connected, pipeline becomes predictable. The same process runs every day regardless of which rep manages it.

## What this means for your stack

You don't need to replace your existing tools. You need an orchestration layer *above* them that governs the full execution.

This is what we built at [Pipeleap]({SITE_URL}) — a workflow orchestration system that connects your CRM, enrichment tool, and sequencer into one governed pipeline engine. The result: predictable pipeline without proportional headcount growth.

---

*Pipeleap — workflow orchestration for SaaS outbound. [Learn more]({SITE_URL}/how-it-works)*
""",
    },
    {
        "slug":    "signal-based-outbound-guide",
        "title":   "Signal-Based Outbound: How SaaS Teams Replace Static Lists with Real-Time Intent",
        "tags":    ["sales", "outbound", "b2b", "saas", "automation"],
        "canonical": f"{SITE_URL}/blog/what-is-signal-based-outbound",
        "body": f"""Static lead lists are the biggest source of outbound inefficiency in B2B SaaS. You build a list, work it for 30 days, and move on — regardless of whether those accounts are actually in a buying moment.

Signal-based outbound flips this. Instead of asking "who should we reach out to this month?", you ask "who is showing buying intent right now?"

## What counts as a buying signal?

- Website visit to your pricing or feature pages
- Intent data showing competitor research
- Job posting for a role your product supports
- LinkedIn activity suggesting evaluation
- Funding announcement (new budget)
- Technology stack change (switching tools)
- CRM field change indicating a trigger event

## How it works in practice

When any of these signals fire, an automated workflow triggers:

1. The account is enriched automatically (company data, contacts, firmographics)
2. ICP scoring runs instantly — only qualified accounts proceed
3. The right sequence is selected based on segment, signal type, and persona
4. Outreach fires automatically with full personalization
5. Replies are classified and routed without manual monitoring

The result: outreach reaches prospects at the moment of highest intent. Reply rates run 2–3× higher than cold list-based campaigns because timing is right.

## The tooling question

Signal-based outbound requires connecting multiple systems: signal sources (intent data, website visitor tools, CRM triggers), enrichment providers (Clay, Apollo, ZoomInfo), sequencers (Outreach, Instantly), and your CRM.

Most teams try to connect these with Zapier or manual exports. The problem: this creates manual handoffs at every stage, which defeats the purpose.

A workflow orchestration system like [Pipeleap]({SITE_URL}) governs the full signal-to-sequence-to-CRM pipeline as one connected engine. You configure the signals and routing logic once; the system runs continuously.

---

*Learn how Pipeleap handles signal-based outbound: [{SITE_URL}/blog/what-is-signal-based-outbound]({SITE_URL}/blog/what-is-signal-based-outbound)*
""",
    },
    {
        "slug":    "scale-outbound-without-sdrs",
        "title":   "How to Scale SaaS Outbound Without Hiring More SDRs",
        "tags":    ["saas", "sales", "hiring", "automation", "startups"],
        "canonical": f"{SITE_URL}/blog/how-to-automate-outbound-without-hiring-sdrs",
        "body": f"""The standard SaaS outbound growth plan: hire SDRs. Each SDR generates X pipeline. Need 2X pipeline? Hire more SDRs.

The problem: this model hits a ceiling fast. Each new SDR costs $80–130K fully loaded, takes 3–6 months to ramp, and produces inconsistent output depending on their individual effort.

There's a better model: workflow automation.

## Where SDR time actually goes

The average SDR spends 60–70% of their day on tasks that aren't selling:

- **Research**: 3–4 hours/day building lists and finding contacts
- **Enrollment**: Manual sequence enrollment after research
- **Monitoring**: Watching inbox for replies
- **Logging**: CRM updates after every call and email

Automate these four and each existing SDR can run 2–3× more pipeline without working harder.

## What to automate

**Lead intake**: Signal-based triggers replace manual list-building. Prospects enter your workflow when they show buying intent, not when someone remembers to add them.

**Enrichment**: Firmographics, technographics, and contact data run automatically at intake. No manual research.

**Sequence enrollment**: Prospects are enrolled in the right sequence automatically based on their ICP score and signal type. No manual enrollment.

**Reply classification**: Interested replies are classified and routed automatically. No inbox monitoring.

**CRM updates**: Every touchpoint logged in real time. No manual logging.

## The math

If an SDR currently spends 15 hours/week on manual tasks, automation reclaims that time for selling. At 3 SDRs, that's 45 hours/week of recovered capacity — equivalent to hiring a fourth SDR at zero cost.

[Pipeleap]({SITE_URL}) orchestrates all five automation stages as one connected workflow — signal capture through CRM sync — so SaaS teams generate more pipeline without proportional headcount growth.

*Get a free GTM audit: [{SITE_URL}/gtm-audit]({SITE_URL}/gtm-audit)*
""",
    },
]


# ── GitHub Publisher (uses existing GITHUB_TOKEN) ─────────────────────────────

class GitHubPublisher:
    API = "https://api.github.com"

    def __init__(self, token: str = "") -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

    @property
    def configured(self) -> bool:
        return bool(self.token and _HAS_REQUESTS)

    def create_gists(self) -> list[dict]:
        """Create public gists containing outbound automation content with pipeleap.com links."""
        if not self.configured:
            return [{"ok": False, "error": "GITHUB_TOKEN not set"}]

        results = []
        for article in ARTICLES:
            payload = {
                "description": article["title"],
                "public": True,
                "files": {
                    f"{article['slug']}.md": {
                        "content": f"# {article['title']}\n\n{article['body']}"
                    }
                },
            }
            try:
                r = _requests.post(f"{self.API}/gists", json=payload, headers=self.headers, timeout=15)
                if r.status_code == 201:
                    data = r.json()
                    results.append({"ok": True, "url": data["html_url"], "title": article["title"]})
                    print(f"  [GIST OK] {data['html_url']}")
                else:
                    results.append({"ok": False, "status": r.status_code, "error": r.text[:100]})
                    print(f"  [GIST FAIL] {r.status_code}: {r.text[:60]}")
            except Exception as e:
                results.append({"ok": False, "error": str(e)})
            time.sleep(1)
        return results

    def create_resource_repo(self) -> dict:
        """Create a public repo: pipeleap-gtm-resources with README linking to pipeleap.com."""
        if not self.configured:
            return {"ok": False, "error": "GITHUB_TOKEN not set"}

        readme = f"""# Pipeleap GTM Resources

A collection of outbound sales automation resources for SaaS revenue teams.

## About Pipeleap

[Pipeleap]({SITE_URL}) is the workflow orchestration system for SaaS organizations that builds
predictable outbound pipeline through structured, signal-based outbound sales automation.

## Resources

- [What is Signal-Based Outbound?]({SITE_URL}/blog/what-is-signal-based-outbound)
- [How to Scale Outbound Without Hiring SDRs]({SITE_URL}/blog/how-to-automate-outbound-without-hiring-sdrs)
- [Outbound Automation Glossary]({SITE_URL}/glossary)
- [Free GTM Audit]({SITE_URL}/gtm-audit)

## Outbound Automation Workflow

```
Signal Capture → Lead Enrichment → Sequence Execution → Reply Routing → CRM Sync
```

Each stage is automated end-to-end. No manual handoffs. No SDR admin overhead.

## Links

- Website: {SITE_URL}
- Resources: {SITE_URL}/blog
- Glossary: {SITE_URL}/glossary
- LinkedIn: https://www.linkedin.com/company/pipeleap
"""
        # Get authenticated user
        try:
            me = _requests.get(f"{self.API}/user", headers=self.headers, timeout=10).json()
            username = me.get("login", "")

            # Create repo
            repo_payload = {
                "name": "pipeleap-gtm-resources",
                "description": "Outbound sales automation resources for SaaS revenue teams — by Pipeleap",
                "private": False,
                "auto_init": False,
            }
            r = _requests.post(f"{self.API}/user/repos", json=repo_payload, headers=self.headers, timeout=15)
            if r.status_code == 201:
                repo = r.json()
                # Add README
                import base64
                content_b64 = base64.b64encode(readme.encode()).decode()
                _requests.put(
                    f"{self.API}/repos/{username}/pipeleap-gtm-resources/contents/README.md",
                    json={"message": "Add GTM resources README", "content": content_b64},
                    headers=self.headers, timeout=15,
                )
                print(f"  [REPO OK] {repo['html_url']}")
                return {"ok": True, "url": repo["html_url"], "clone_url": repo["clone_url"]}
            elif r.status_code == 422:  # Already exists
                repo_url = f"https://github.com/{username}/pipeleap-gtm-resources"
                print(f"  [REPO EXISTS] {repo_url}")
                return {"ok": True, "url": repo_url, "note": "repo already exists"}
            else:
                print(f"  [REPO FAIL] {r.status_code}: {r.text[:80]}")
                return {"ok": False, "status": r.status_code}
        except Exception as e:
            return {"ok": False, "error": str(e)}


# ── DEV.to Publisher ──────────────────────────────────────────────────────────

class DevToPublisher:
    API = "https://dev.to/api"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.environ.get("DEVTO_API_KEY", "")
        self.headers = {"api-key": self.api_key, "Content-Type": "application/json"}

    @property
    def configured(self) -> bool:
        return bool(self.api_key and _HAS_REQUESTS)

    def publish_articles(self) -> list[dict]:
        if not self.configured:
            return [{"ok": False, "error": "DEVTO_API_KEY not set — get it at https://dev.to/settings/extensions"}]

        results = []
        for article in ARTICLES:
            payload = {
                "article": {
                    "title":            article["title"],
                    "body_markdown":    article["body"],
                    "published":        True,
                    "tags":             article["tags"][:4],
                    "canonical_url":    article["canonical"],
                    "description":      article["body"].split("\n\n")[0][:150],
                }
            }
            try:
                r = _requests.post(f"{self.API}/articles", json=payload, headers=self.headers, timeout=20)
                if r.status_code == 201:
                    data = r.json()
                    results.append({"ok": True, "url": data.get("url", ""), "title": article["title"]})
                    print(f"  [DEV.to OK] {data.get('url', '')}")
                elif r.status_code == 422:
                    results.append({"ok": False, "error": "Already published or validation error", "body": r.text[:100]})
                else:
                    results.append({"ok": False, "status": r.status_code, "error": r.text[:100]})
                    print(f"  [DEV.to FAIL] {r.status_code}")
            except Exception as e:
                results.append({"ok": False, "error": str(e)})
            time.sleep(2)
        return results


# ── Hashnode Publisher ────────────────────────────────────────────────────────

class HashnodePublisher:
    API = "https://gql.hashnode.com/"

    def __init__(self, token: str = "", publication_id: str = "") -> None:
        self.token          = token          or os.environ.get("HASHNODE_TOKEN", "")
        self.publication_id = publication_id or os.environ.get("HASHNODE_PUBLICATION_ID", "")
        self.headers        = {"Authorization": self.token, "Content-Type": "application/json"}

    @property
    def configured(self) -> bool:
        return bool(self.token and self.publication_id and _HAS_REQUESTS)

    def publish_articles(self) -> list[dict]:
        if not self.configured:
            return [{"ok": False, "error": (
                "HASHNODE_TOKEN + HASHNODE_PUBLICATION_ID not set — "
                "get token at https://hashnode.com/settings/developer, "
                "publication ID from your blog URL"
            )}]

        results = []
        for article in ARTICLES:
            query = """
            mutation PublishPost($input: PublishPostInput!) {
              publishPost(input: $input) {
                post { url title }
              }
            }"""
            variables = {"input": {
                "title":         article["title"],
                "contentMarkdown": article["body"],
                "tags":          [{"slug": t, "name": t} for t in article["tags"][:5]],
                "originalArticleURL": article["canonical"],
                "publicationId": self.publication_id,
            }}
            try:
                r = _requests.post(
                    self.API,
                    json={"query": query, "variables": variables},
                    headers=self.headers, timeout=20,
                )
                data = r.json()
                if "errors" not in data and data.get("data", {}).get("publishPost"):
                    post_url = data["data"]["publishPost"]["post"]["url"]
                    results.append({"ok": True, "url": post_url, "title": article["title"]})
                    print(f"  [Hashnode OK] {post_url}")
                else:
                    err = str(data.get("errors", data))[:100]
                    results.append({"ok": False, "error": err})
                    print(f"  [Hashnode FAIL] {err}")
            except Exception as e:
                results.append({"ok": False, "error": str(e)})
            time.sleep(2)
        return results


# ── PyPI Package Creator ──────────────────────────────────────────────────────

def create_pypi_package(output_dir: str = "outputs/pypi_package") -> dict:
    """
    Create a publishable PyPI package 'pipeleap-tools' that links to pipeleap.com.
    DA85 backlink from pypi.org. User runs 'pip install build twine && python -m build && twine upload dist/*'
    """
    pkg = Path(output_dir)
    src = pkg / "pipeleap_tools"
    src.mkdir(parents=True, exist_ok=True)

    # pyproject.toml
    (pkg / "pyproject.toml").write_text("""[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "pipeleap-tools"
version = "0.1.0"
description = "Outbound sales automation utilities for SaaS revenue teams"
readme = "README.md"
license = {text = "MIT"}
keywords = ["outbound", "sales", "automation", "saas", "crm", "workflow"]
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Topic :: Office/Business :: Financial :: Spreadsheet",
    "Intended Audience :: Developers",
]
requires-python = ">=3.8"

[project.urls]
Homepage = "https://pipeleap.com"
Documentation = "https://pipeleap.com/how-it-works"
Repository = "https://github.com/manikanakathala-droid/pipeleap-launchpad"
""", encoding="utf-8")

    # README.md
    (pkg / "README.md").write_text(f"""# pipeleap-tools

Utility library for outbound sales automation workflows, built to complement [Pipeleap](https://pipeleap.com).

## What is Pipeleap?

[Pipeleap](https://pipeleap.com) is the workflow orchestration system for SaaS organizations that builds
predictable outbound pipeline through signal-based outbound sales automation.

It automates:
- Signal capture (website visits, intent data, ICP triggers)
- Lead enrichment (Clay, Apollo, ZoomInfo waterfall)
- Multi-channel outbound sequencing
- Reply routing and classification
- CRM write-back (HubSpot, Salesforce)

## Installation

```bash
pip install pipeleap-tools
```

## Usage

```python
from pipeleap_tools import slugify, estimate_read_time, clean_keyword

# Slug generation for outbound content
slug = slugify("How to automate outbound sales for SaaS")
# → "how-to-automate-outbound-sales-for-saas"

# Read time estimation
mins = estimate_read_time("Your article content here...")
# → 3

# Keyword cleaning
kw = clean_keyword("  outbound automation platform  ")
# → "outbound automation platform"
```

## Links

- Website: https://pipeleap.com
- Docs: https://pipeleap.com/how-it-works
- GTM Audit: https://pipeleap.com/gtm-audit
- Glossary: https://pipeleap.com/glossary
""", encoding="utf-8")

    # Package __init__.py
    (src / "__init__.py").write_text('''"""
pipeleap-tools — utilities for outbound sales automation workflows.
Companion library for https://pipeleap.com
"""
from __future__ import annotations
import re


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def estimate_read_time(text: str, wpm: int = 220) -> int:
    """Estimate reading time in minutes."""
    return max(1, round(len(text.split()) / wpm))


def clean_keyword(kw: str) -> str:
    """Clean and normalise a keyword string."""
    return re.sub(r"\\s+", " ", kw.strip().lower())


def extract_keywords(text: str, min_length: int = 3) -> list[str]:
    """Extract unique words from text as keyword candidates."""
    words = re.findall(r"\\b[a-z]{3,}\\b", text.lower())
    seen, result = set(), []
    for w in words:
        if w not in seen and len(w) >= min_length:
            seen.add(w)
            result.append(w)
    return result
''', encoding="utf-8")

    print(f"  PyPI package created at: {pkg}")
    print(f"  To publish: cd {pkg} && pip install build twine && python -m build && twine upload dist/*")
    return {"ok": True, "path": str(pkg), "package_name": "pipeleap-tools"}


# ── Master runner ─────────────────────────────────────────────────────────────

def run_all_api_backlinks(
    github_token:    str = "",
    devto_key:       str = "",
    hashnode_token:  str = "",
    hashnode_pub_id: str = "",
) -> dict[str, Any]:
    print("\n=== API Backlink Publisher ===\n")
    results: dict[str, Any] = {"started_at": datetime.now(timezone.utc).isoformat()}

    # GitHub — highest DA, try first
    print("[1/4] GitHub (DA95)...")
    gh = GitHubPublisher(github_token)
    if gh.configured:
        results["github_repo"]   = gh.create_resource_repo()
        results["github_gists"]  = gh.create_gists()
    else:
        results["github"] = {"ok": False, "error": "Set GITHUB_TOKEN env var"}
        print("  Skipped — set GITHUB_TOKEN")

    # PyPI — always runs (no credentials needed for package creation)
    print("\n[2/4] PyPI package (DA85)...")
    results["pypi"] = create_pypi_package()

    # DEV.to
    print("\n[3/4] DEV.to (DA74)...")
    devto = DevToPublisher(devto_key)
    results["devto"] = devto.publish_articles()
    if not devto.configured:
        print("  Skipped — set DEVTO_API_KEY (free at dev.to/settings/extensions)")

    # Hashnode
    print("\n[4/4] Hashnode (DA73)...")
    hn = HashnodePublisher(hashnode_token, hashnode_pub_id)
    results["hashnode"] = hn.publish_articles()
    if not hn.configured:
        print("  Skipped — set HASHNODE_TOKEN + HASHNODE_PUBLICATION_ID")

    # Save report
    (OUTPUT / "api_backlinks_report.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nReport saved: {OUTPUT}/api_backlinks_report.json")
    return results
