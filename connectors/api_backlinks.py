"""
API Backlink Publisher — programmatic backlinks via platform APIs.
No browser, no CAPTCHA, no form submissions.

Platforms (require one-time free credentials):
  GitHub      DA95 — create public repos + gists that link to pipeleap.com
  WordPress   DA94 — publish via WordPress.com REST API (free blog, app password)
  PyPI        DA85 — publish pipeleap-tools Python package (generate + run `twine upload`)
  Blogger     DA74 — Google-owned platform, instant Google indexing, free Blogger API
  Reddit      DA91 — post to relevant subreddits via free Reddit API
  GitLab      DA95 — public project + README with backlinks (GITLAB_TOKEN, free account)
  npm         DA92 — publish pipeleap-tools npm package (generate + run `npm publish`)
  Crates.io   DA72 — publish pipeleap-tools Rust crate (generate + run `cargo publish`)
  Mastodon    DA72 — public posts on mastodon.social, Fediverse distribution (MASTODON_TOKEN)

Zero-credential platforms (always run, no setup needed):
  Wayback     DA95 — archive every page on archive.org (real DA95 backlinks, Google-indexed)
  BlogPing    N/A  — XML-RPC pings to 12 endpoints → 30+ blog directories notified
  WebSub      N/A  — PubSubHubbub hub pings (Google hub + Superfeedr → Feedly, NewsBlur, etc.)
  Telegraph   DA76 — publishes articles on telegra.ph with backlinks (zero-credential API)
  FeedDirs    N/A  — submits RSS feed to 6 free feed directories and aggregators

Setup (one-time per platform):
  GitHub:    GITHUB_TOKEN env var
  WordPress: create free blog at wordpress.com → Users → Security → Application Passwords
             set WP_SITE_URL, WP_USERNAME, WP_APP_PASSWORD
  Blogger:   create blog at blogger.com, enable Blogger API in n8n-xamplify, set BLOGGER_BLOG_ID
  Reddit:    reddit.com/prefs/apps → script app → set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
             REDDIT_USERNAME, REDDIT_PASSWORD
  GitLab:    free account at gitlab.com → Preferences → Access Tokens → set GITLAB_TOKEN
  npm:       npmjs.com free account → `npm login` → `npm publish`
  Crates.io: crates.io free account → `cargo login <token>` → `cargo publish`
  Mastodon:  mastodon.social free account → Settings → Development → New Application
             set MASTODON_TOKEN
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
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("LAUNCHPAD_DEPLOY_TOKEN") or ""
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


# ── Reddit Publisher (DA91) ───────────────────────────────────────────────────

class RedditPublisher:
    """
    Posts articles to relevant SaaS/sales subreddits via the Reddit API.
    DA91 — Reddit ranks extremely well in Google; posts appear in search results.
    Free API — no paid tier needed.

    One-time setup:
      1. Go to https://www.reddit.com/prefs/apps → "create another app"
      2. Choose "script" type, set redirect URI to http://localhost:8080
      3. Copy client_id (under app name) and client_secret
      4. Set env vars:
           REDDIT_CLIENT_ID     = your app client_id
           REDDIT_CLIENT_SECRET = your app client_secret
           REDDIT_USERNAME      = your Reddit username
           REDDIT_PASSWORD      = your Reddit password

    Posts as link posts (URL posts) to subreddits — each post is a backlink.
    """
    TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
    API       = "https://oauth.reddit.com"
    USER_AGENT = "pipeleap-seo-agent/1.0 (by /u/{username})"

    # Subreddits relevant to Pipeleap's audience
    SUBREDDITS = [
        "r/SaaS",
        "r/sales",
        "r/entrepreneur",
        "r/startups",
        "r/Entrepreneur",
    ]

    def __init__(self) -> None:
        self.client_id     = os.environ.get("REDDIT_CLIENT_ID", "")
        self.client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
        self.username      = os.environ.get("REDDIT_USERNAME", "")
        self.password      = os.environ.get("REDDIT_PASSWORD", "")

    @property
    def configured(self) -> bool:
        return bool(
            self.client_id and self.client_secret
            and self.username and self.password
            and _HAS_REQUESTS
        )

    def _get_token(self) -> str:
        r = _requests.post(
            self.TOKEN_URL,
            data={"grant_type": "password", "username": self.username, "password": self.password},
            auth=(self.client_id, self.client_secret),
            headers={"User-Agent": self.USER_AGENT.format(username=self.username)},
            timeout=10,
        )
        return r.json().get("access_token", "")

    def publish_articles(self) -> list[dict]:
        if not self.configured:
            return [{"ok": False, "error": (
                "Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD — "
                "create app at reddit.com/prefs/apps (script type)"
            )}]

        try:
            token = self._get_token()
            if not token:
                return [{"ok": False, "error": "Reddit auth failed — check credentials"}]
        except Exception as e:
            return [{"ok": False, "error": f"Reddit token error: {e}"}]

        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": self.USER_AGENT.format(username=self.username),
        }
        results = []
        for article in ARTICLES:
            for subreddit in self.SUBREDDITS[:2]:  # 2 subreddits per run to avoid spam flags
                sub = subreddit.lstrip("r/")
                payload = {
                    "sr":      sub,
                    "kind":    "link",
                    "title":   article["title"],
                    "url":     article["canonical"],
                    "resubmit": False,
                    "nsfw":    False,
                }
                try:
                    r = _requests.post(
                        f"{self.API}/api/submit",
                        data=payload,
                        headers=headers,
                        timeout=15,
                    )
                    data = r.json()
                    if data.get("success") or data.get("jquery"):
                        post_url = data.get("data", {}).get("url", "")
                        results.append({"ok": True, "url": post_url, "subreddit": sub, "title": article["title"]})
                        print(f"  [Reddit OK] r/{sub} - {article['title'][:50]}")
                    else:
                        err = str(data.get("json", {}).get("errors", data))[:120]
                        results.append({"ok": False, "subreddit": sub, "error": err})
                        print(f"  [Reddit FAIL] r/{sub}: {err[:80]}")
                except Exception as e:
                    results.append({"ok": False, "subreddit": sub, "error": str(e)})
                time.sleep(3)
        return results


# ── WordPress.com Publisher (DA94) ────────────────────────────────────────────

class WordPressPublisher:
    """
    Publishes articles to a free WordPress.com blog via the REST API v2.
    DA94 — one of the highest-authority free platforms available.
    Sets canonical link back to pipeleap.com via a footer link in content.

    One-time setup (5 minutes):
      1. Create a free blog at https://wordpress.com (e.g. pipeleap.wordpress.com)
      2. Go to Users → Security → Application Passwords → Add New
      3. Copy the generated password (shown once)
      4. Set env vars:
           WP_SITE_URL  = https://pipeleap.wordpress.com
           WP_USERNAME  = your WordPress.com username
           WP_APP_PASSWORD = the application password (spaces OK)

    Docs: https://developer.wordpress.com/docs/api/
    """

    def __init__(
        self,
        site_url: str = "",
        username: str = "",
        app_password: str = "",
    ) -> None:
        self.site_url     = (site_url     or os.environ.get("WP_SITE_URL", "")).rstrip("/")
        self.username     = username      or os.environ.get("WP_USERNAME", "")
        self.app_password = app_password  or os.environ.get("WP_APP_PASSWORD", "")

    @property
    def configured(self) -> bool:
        return bool(self.site_url and self.username and self.app_password and _HAS_REQUESTS)

    def publish_articles(self) -> list[dict]:
        if not self.configured:
            return [{"ok": False, "error": (
                "Set WP_SITE_URL, WP_USERNAME, WP_APP_PASSWORD — "
                "create free blog at wordpress.com, then Users → Security → Application Passwords"
            )}]

        import base64
        token = base64.b64encode(f"{self.username}:{self.app_password}".encode()).decode()
        headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}
        api = f"{self.site_url}/wp-json/wp/v2/posts"

        results = []
        for article in ARTICLES:
            # Append canonical backlink footer to content
            body_html = str(article["body"]).replace("\n\n", "</p><p>")
            body_html = (
                f"<p>{body_html}</p>"
                f'<p><em>Originally published at '
                f'<a href="{article["canonical"]}">{article["canonical"]}</a></em></p>'
            )
            payload = {
                "title":   article["title"],
                "content": body_html,
                "status":  "publish",
                "tags":    article["tags"][:10],
            }
            try:
                r = _requests.post(api, json=payload, headers=headers, timeout=20)
                if r.status_code == 201:
                    data = r.json()
                    post_url = data.get("link", "")
                    results.append({"ok": True, "url": post_url, "title": article["title"]})
                    print(f"  [WordPress OK] {post_url}")
                elif r.status_code == 403:
                    results.append({"ok": False, "error": "Auth failed — check WP_USERNAME and WP_APP_PASSWORD"})
                else:
                    results.append({"ok": False, "status": r.status_code, "error": r.text[:150]})
                    print(f"  [WordPress FAIL] {r.status_code}: {r.text[:80]}")
            except Exception as e:
                results.append({"ok": False, "error": str(e)})
            time.sleep(2)
        return results


# ── Blogger Publisher (DA74, Google-owned) ────────────────────────────────────

class BloggerPublisher:
    """
    Publishes articles to a Blogger (blogspot.com) blog via Google Blogger API v3.
    Uses the existing gsc_service_account.json — no extra credentials needed.
    Google-owned platform: pages are indexed by Google within hours.

    One-time setup:
      1. Create a free blog at https://www.blogger.com
      2. Enable Blogger API in GCP console (project n8n-xamplify)
      3. Add service account pipeleap-seo@n8n-xamplify.iam.gserviceaccount.com
         as Author in your Blogger blog Settings → Permissions
      4. Set BLOGGER_BLOG_ID env var (found in Blogger Settings → Basic → Blog ID)
    """
    API = "https://www.googleapis.com/blogger/v3"

    def __init__(self, blog_id: str = "", credentials_path: str = "") -> None:
        self.blog_id = blog_id or os.environ.get("BLOGGER_BLOG_ID", "")
        self.credentials_path = credentials_path or "credentials/gsc_service_account.json"

    @property
    def configured(self) -> bool:
        from pathlib import Path as _Path
        return bool(
            self.blog_id
            and _Path(self.credentials_path).exists()
            and _HAS_REQUESTS
        )

    def _get_token(self) -> str:
        try:
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/blogger"],
            )
            import google.auth.transport.requests as _transport
            creds.refresh(_transport.Request())
            return creds.token or ""
        except Exception:
            return ""

    def publish_articles(self) -> list[dict]:
        if not self.configured:
            return [{"ok": False, "error": (
                "Set BLOGGER_BLOG_ID env var. One-time setup: create blog at blogger.com, "
                "enable Blogger API in GCP project n8n-xamplify, add "
                "pipeleap-seo@n8n-xamplify.iam.gserviceaccount.com as Author."
            )}]

        token = self._get_token()
        if not token:
            return [{"ok": False, "error": "Could not obtain access token from service account"}]

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        results = []
        for article in ARTICLES:
            # Convert markdown to basic HTML for Blogger
            body_html = str(article["body"]).replace("\n\n", "</p><p>").replace("**", "<strong>")
            body_html = f"<p>{body_html}</p>"
            body_html += (
                f'<p>Originally published at <a href="{article["canonical"]}" rel="canonical">'
                f'{article["canonical"]}</a></p>'
            )
            payload = {
                "title":   article["title"],
                "content": body_html,
                "labels":  article["tags"][:10],
            }
            try:
                r = _requests.post(
                    f"{self.API}/blogs/{self.blog_id}/posts/",
                    json=payload,
                    headers=headers,
                    timeout=20,
                )
                if r.status_code == 200:
                    data = r.json()
                    post_url = data.get("url", "")
                    results.append({"ok": True, "url": post_url, "title": article["title"]})
                    print(f"  [Blogger OK] {post_url}")
                else:
                    results.append({"ok": False, "status": r.status_code, "error": r.text[:150]})
                    print(f"  [Blogger FAIL] {r.status_code}: {r.text[:80]}")
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


# ── Zero-credential publishers ────────────────────────────────────────────────

# All pages that should be archived / pinged
_ALL_SITE_PAGES = [
    "",
    "/blog",
    "/how-it-works",
    "/pricing",
    "/gtm-audit",
    "/glossary",
    "/about",
    "/contact",
    "/integrations",
    "/case-studies",
    "/blog/why-do-outbound-workflows-need-orchestration",
    "/blog/signal-based-outbound-sales",
    "/blog/outbound-sales-automation-guide",
    "/blog/what-is-a-sales-development-representative",
    "/blog/how-to-build-a-saas-outbound-engine",
]


class WaybackMachinePublisher:
    """
    Saves every Pipeleap page to the Internet Archive (archive.org).

    Each saved page is publicly accessible at:
      https://web.archive.org/web/<TIMESTAMP>/https://www.pipeleap.com/<path>

    Google crawls archive.org (DA95+). No credentials, no account, no cost.
    Rate limit: ~1 save/second — the class enforces 1.5 s between requests.
    """

    SAVE_URL = "https://web.archive.org/save/"
    is_configured = True

    def save_all(self, pages: list[str] | None = None) -> dict[str, Any]:
        if not _HAS_REQUESTS:
            return {"ok": False, "error": "requests not installed"}

        urls = [f"{SITE_URL}{p}" for p in (pages or _ALL_SITE_PAGES)]
        saved, failed = [], []

        for url in urls:
            try:
                resp = _requests.get(
                    f"{self.SAVE_URL}{url}",
                    headers={"User-Agent": "Mozilla/5.0 (compatible; PipeleapSEOBot/1.0)"},
                    timeout=30,
                    allow_redirects=True,
                )
                archived = resp.headers.get("Content-Location", "")
                if resp.status_code in (200, 302) or archived:
                    archive_url = f"https://web.archive.org{archived}" if archived else f"https://web.archive.org/web/*/{url}"
                    saved.append({"url": url, "archived_at": archive_url})
                    print(f"    ✓ {url}")
                else:
                    failed.append({"url": url, "status": resp.status_code})
                    print(f"    ✗ {url} (HTTP {resp.status_code})")
            except Exception as exc:
                failed.append({"url": url, "error": str(exc)})
                print(f"    ✗ {url} ({exc})")
            time.sleep(1.5)

        return {"ok": True, "saved": saved, "failed": failed, "total": len(urls)}


class BlogPingPublisher:
    """
    Sends XML-RPC pings to 20+ blog directories and aggregators.

    Ping-o-Matic distributes to: Weblogs.com, Technorati, My Yahoo!, Bloglines,
    NewsGator, Google Blog Search, BlogRolling, Feedster, and 15+ more.

    No credentials. No account. Free forever.
    Each ping notifies directories that Pipeleap has new content → crawl triggered.
    """

    # Ping endpoints that accept XML-RPC weblogUpdates.ping
    PING_TARGETS = [
        "http://rpc.pingomatic.com/",           # distributes to 30+ services
        "http://ping.blogs.com/weblogscom/ping", # Weblogs.com
        "http://blogsearch.google.com/ping/RPC2",# Google Blog Search
        "http://ping.feedburner.com/",           # FeedBurner / Google Feeds
        "http://www.blogdigger.com/RPC2",        # Blogdigger
        "http://www.blogstreet.com/xrbin/xmlrpc.cgi",
        "http://topicexchange.com/RPC2",
        "http://ping.syndic8.com/xmlrpc.php",
        "http://www.newsisfree.com/RPCCloud",
        "http://ping.blo.gs/",
        "http://api.moreover.com/ping",
        "http://www.feedsubmitter.com/",
    ]

    XML_TEMPLATE = """<?xml version="1.0"?>
<methodCall>
  <methodName>weblogUpdates.ping</methodName>
  <params>
    <param><value><string>{title}</string></value></param>
    <param><value><string>{url}</string></value></param>
  </params>
</methodCall>"""

    is_configured = True

    def ping_all(self) -> dict[str, Any]:
        if not _HAS_REQUESTS:
            return {"ok": False, "error": "requests not installed"}

        payload = self.XML_TEMPLATE.format(
            title="Pipeleap — Outbound Sales Automation for SaaS",
            url=SITE_URL,
        ).encode("utf-8")

        headers = {
            "Content-Type": "text/xml",
            "User-Agent": "Mozilla/5.0 (compatible; PipeleapSEOBot/1.0)",
        }

        success, failed = [], []
        for endpoint in self.PING_TARGETS:
            try:
                resp = _requests.post(endpoint, data=payload, headers=headers, timeout=8)
                if resp.status_code == 200:
                    success.append(endpoint)
                    print(f"    ✓ {endpoint}")
                else:
                    failed.append({"endpoint": endpoint, "status": resp.status_code})
                    print(f"    ✗ {endpoint} (HTTP {resp.status_code})")
            except Exception as exc:
                failed.append({"endpoint": endpoint, "error": str(exc)})
                print(f"    ✗ {endpoint} ({exc})")
            time.sleep(0.3)

        return {"ok": True, "pinged": success, "failed": failed, "total": len(self.PING_TARGETS)}


class WebSubPublisher:
    """
    PubSubHubbub (WebSub W3C standard) hub pings.

    Notifies hub.google.com, pubsubhubbub.appspot.com, and Superfeedr that
    Pipeleap's RSS/Atom feed has new content. Hubs then push the feed to all
    subscribed readers (Feedly, NewsBlur, Inoreader, etc.) immediately.

    - Feedly has 30M+ users. Getting into their index creates crawl + backlink signals.
    - Google's own hub (hub.google.com) prioritises fast indexing of updated feeds.
    - No credentials. Standard HTTP POST per the W3C WebSub spec.
    """

    HUBS = [
        "https://hub.google.com/",
        "https://pubsubhubbub.appspot.com/",
        "https://superfeedr.com/hubbub",
    ]

    FEED_URL  = f"{SITE_URL}/feed.xml"
    TOPIC_URL = f"{SITE_URL}/blog"

    is_configured = True

    def ping_all(self) -> dict[str, Any]:
        if not _HAS_REQUESTS:
            return {"ok": False, "error": "requests not installed"}

        success, failed = [], []
        for hub in self.HUBS:
            try:
                resp = _requests.post(
                    hub,
                    data={
                        "hub.mode":  "publish",
                        "hub.url":   self.TOPIC_URL,
                        "hub.topic": self.FEED_URL,
                    },
                    headers={"User-Agent": "Mozilla/5.0 (compatible; PipeleapSEOBot/1.0)"},
                    timeout=10,
                )
                # WebSub spec: 2xx = accepted
                if resp.status_code in range(200, 300):
                    success.append(hub)
                    print(f"    ✓ {hub}")
                else:
                    failed.append({"hub": hub, "status": resp.status_code})
                    print(f"    ✗ {hub} (HTTP {resp.status_code})")
            except Exception as exc:
                failed.append({"hub": hub, "error": str(exc)})
                print(f"    ✗ {hub} ({exc})")
            time.sleep(0.2)

        return {"ok": True, "notified": success, "failed": failed, "total": len(self.HUBS)}


# ── Additional publishers ─────────────────────────────────────────────────────

class TelegraphPublisher:
    """
    Telegram's open blogging platform — telegra.ph (DA76).

    Completely zero-credential: createAccount returns a one-time access_token
    on the fly, no login or email required. Pages are public, permanently hosted,
    and crawled by Google within hours.

    Each article gets a URL like: https://telegra.ph/article-title-MM-DD
    """

    API = "https://api.telegra.ph"
    is_configured = True

    ARTICLES = [
        {
            "title": "Why Your SaaS Outbound Stack Has a Governance Problem",
            "content": [
                {"tag": "p", "children": ["Most B2B sales teams have the same stack: Apollo or Clay for data, HubSpot or Salesforce as CRM, Outreach or Instantly for sequencing. And yet pipeline is still unpredictable."]},
                {"tag": "p", "children": ["The problem isn't the tools. It's the absence of an orchestration layer."]},
                {"tag": "h3", "children": ["What workflow orchestration actually means"]},
                {"tag": "p", "children": ["A sequencer fires emails automatically. An enrichment tool finds contact data. A CRM stores pipeline records. None of these tools govern how they work together."]},
                {"tag": "p", "children": ["When a signal fires, someone still has to research the prospect, build or update the list, enroll them in the right sequence, monitor replies, and route interested ones to the right rep. That's not a tooling gap — it's a governance gap."]},
                {"tag": "h3", "children": ["What Pipeleap does differently"]},
                {"tag": "p", "children": ["Pipeleap sits above your existing tools as a workflow orchestration layer. It captures intent signals, triggers enrichment, routes leads into sequences, classifies replies, and writes outcomes to the CRM — all without human intervention."]},
                {"tag": "p", "children": [{"tag": "a", "attrs": {"href": "https://www.pipeleap.com", "target": "_blank"}, "children": ["Pipeleap — outbound sales automation for SaaS"]}]},
            ],
        },
        {
            "title": "Signal-Based Outbound: The Framework SaaS Teams Are Switching To",
            "content": [
                {"tag": "p", "children": ["Traditional outbound is dead. Cold lists, spray-and-pray sequences, and manual research have single-digit reply rates for a reason: buyers tune out untargeted noise immediately."]},
                {"tag": "p", "children": ["Signal-based outbound flips this. Instead of building lists and hoping for relevance, you monitor buying signals — website visits, job changes, funding announcements, product reviews — and reach out only when a prospect is already in-market."]},
                {"tag": "h3", "children": ["The five signals that matter most"]},
                {"tag": "p", "children": ["1. Website visit intent — a prospect on your pricing page is 11× more likely to respond. 2. ICP trigger events — new funding, headcount growth, CRM migration. 3. Technology install signals — they just added HubSpot, they need rev ops tooling. 4. Competitive research signals — they're reading G2 reviews of your category. 5. Content engagement — they opened your email four times but didn't reply."]},
                {"tag": "p", "children": [{"tag": "a", "attrs": {"href": "https://www.pipeleap.com/blog/signal-based-outbound-sales", "target": "_blank"}, "children": ["Read the full framework at Pipeleap"]}]},
            ],
        },
        {
            "title": "The Complete Guide to Outbound Sales Automation for SaaS in 2026",
            "content": [
                {"tag": "p", "children": ["Outbound sales automation for SaaS has evolved from simple email sequences into full-stack orchestration pipelines. Here's what a modern automated outbound motion looks like in 2026."]},
                {"tag": "h3", "children": ["Layer 1: Signal capture"]},
                {"tag": "p", "children": ["Tools like Clearbit Reveal, Warmly, and RB2B identify anonymous website visitors. Intent data from Bombora or G2 Buyer Intent surfaces in-market accounts. Job change alerts from LinkedIn Sales Navigator or Surfe trigger rep outreach."]},
                {"tag": "h3", "children": ["Layer 2: Enrichment waterfall"]},
                {"tag": "p", "children": ["Clay orchestrates an enrichment waterfall across Apollo, Hunter, LinkedIn, and ZoomInfo. You only pay for data you actually need — most records are enriched fully in the first two hops."]},
                {"tag": "h3", "children": ["Layer 3: Orchestration"]},
                {"tag": "p", "children": ["This is the layer most teams skip. Pipeleap sits here — turning raw signals into qualified, enrolled, replied-to pipeline without a human in the loop."]},
                {"tag": "p", "children": [{"tag": "a", "attrs": {"href": "https://www.pipeleap.com/blog/outbound-sales-automation-guide", "target": "_blank"}, "children": ["Full automation guide at Pipeleap.com"]}]},
            ],
        },
    ]

    def publish_all(self) -> dict[str, Any]:
        if not _HAS_REQUESTS:
            return {"ok": False, "error": "requests not installed"}

        published = []
        for article in self.ARTICLES:
            result = self._publish_one(article)
            if result.get("ok"):
                published.append(result)
                print(f"    ✓ {result['url']}")
            else:
                print(f"    ✗ {article['title'][:50]} — {result.get('error')}")
            time.sleep(1.0)

        return {"ok": True, "published": published, "total": len(self.ARTICLES)}

    def _publish_one(self, article: dict) -> dict[str, Any]:
        try:
            # Step 1: create a throwaway account (returns access_token instantly, no email)
            acc = _requests.post(
                f"{self.API}/createAccount",
                json={"short_name": "Pipeleap", "author_name": "Pipeleap Team", "author_url": SITE_URL},
                timeout=10,
            ).json()
            if not acc.get("ok"):
                return {"ok": False, "error": acc.get("error", "createAccount failed")}
            token = acc["result"]["access_token"]

            # Step 2: publish page
            page = _requests.post(
                f"{self.API}/createPage",
                json={
                    "access_token": token,
                    "title": article["title"],
                    "content": article["content"],
                    "return_content": False,
                },
                timeout=10,
            ).json()
            if not page.get("ok"):
                return {"ok": False, "error": page.get("error", "createPage failed")}
            return {"ok": True, "url": page["result"]["url"], "title": article["title"]}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


class NpmPackagePublisher:
    """
    Generates an npm package (pipeleap-tools) with homepage pointing to pipeleap.com.

    npmjs.com is DA92. The package README + homepage field creates a permanent
    backlink from npm's registry pages.

    User runs: cd outputs/backlinks/npm/pipeleap-tools && npm publish --access public
    (requires free npmjs.com account + `npm login`)
    """

    is_configured = True

    def create_package(self, output_dir: str = "outputs/backlinks/npm") -> dict[str, Any]:
        pkg = Path(output_dir) / "pipeleap-tools"
        pkg.mkdir(parents=True, exist_ok=True)

        (pkg / "package.json").write_text(json.dumps({
            "name": "pipeleap-tools",
            "version": "0.1.0",
            "description": "Outbound sales automation utilities for SaaS revenue teams — companion to Pipeleap",
            "main": "index.js",
            "scripts": {"test": "echo \"No tests\" && exit 0"},
            "keywords": ["outbound", "sales", "automation", "saas", "workflow", "crm", "pipeline", "revops"],
            "author": "Pipeleap <hello@pipeleap.com>",
            "license": "MIT",
            "homepage": "https://www.pipeleap.com",
            "repository": {"type": "git", "url": "https://github.com/manikanakathala-droid/pipeleap-launchpad"},
            "bugs": {"url": "https://www.pipeleap.com/contact"},
        }, indent=2), encoding="utf-8")

        (pkg / "index.js").write_text("""\
/**
 * pipeleap-tools
 * Utilities for outbound sales automation workflows.
 * Companion to https://www.pipeleap.com
 */

function slugify(text) {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function estimateReadTime(text, wpm = 220) {
  return Math.max(1, Math.round(text.split(/\\s+/).length / wpm));
}

function cleanKeyword(kw) {
  return kw.trim().toLowerCase().replace(/\\s+/g, ' ');
}

module.exports = { slugify, estimateReadTime, cleanKeyword };
""", encoding="utf-8")

        (pkg / "README.md").write_text(f"""\
# pipeleap-tools

Utility library for outbound sales automation, built to complement [Pipeleap](https://www.pipeleap.com).

## What is Pipeleap?

[Pipeleap](https://www.pipeleap.com) is the workflow orchestration layer that sits above your existing GTM stack (Apollo, Clay, HubSpot, Outreach) and automates the entire outbound motion — signal capture, enrichment, sequencing, reply routing, and CRM write-back — without human intervention.

## Installation

```bash
npm install pipeleap-tools
```

## Usage

```js
const {{ slugify, estimateReadTime, cleanKeyword }} = require('pipeleap-tools');

slugify("How to automate outbound sales")
// → "how-to-automate-outbound-sales"

estimateReadTime("Your article content...")
// → 3

cleanKeyword("  outbound automation  ")
// → "outbound automation"
```

## Links

- Website: https://www.pipeleap.com
- How it works: https://www.pipeleap.com/how-it-works
- GTM Audit: https://www.pipeleap.com/gtm-audit
- Blog: https://www.pipeleap.com/blog
""", encoding="utf-8")

        print(f"  npm package created at: {pkg}")
        print(f"  To publish: cd {pkg} && npm login && npm publish --access public")
        return {"ok": True, "path": str(pkg), "package_name": "pipeleap-tools"}


class GitLabPublisher:
    """
    Creates a public GitLab project (DA95) with a README that links to pipeleap.com.

    Requires a free GitLab account + personal access token (GITLAB_TOKEN env var).
    Free tier: unlimited public repos, no credit card.
    """

    API = "https://gitlab.com/api/v4"

    def __init__(self) -> None:
        self.token = os.environ.get("GITLAB_TOKEN", "")

    @property
    def configured(self) -> bool:
        return bool(self.token)

    def create_project(self) -> dict[str, Any]:
        if not _HAS_REQUESTS or not self.configured:
            return {"ok": False, "error": "Set GITLAB_TOKEN (free account at gitlab.com)"}

        headers = {"PRIVATE-TOKEN": self.token, "Content-Type": "application/json"}

        # Create project
        proj = _requests.post(f"{self.API}/projects", headers=headers, json={
            "name": "pipeleap-sales-automation",
            "description": "Outbound sales automation resources for SaaS revenue teams — pipeleap.com",
            "visibility": "public",
            "initialize_with_readme": False,
        }, timeout=15).json()

        if "id" not in proj:
            return {"ok": False, "error": proj.get("message", "Project creation failed")}

        pid = proj["id"]
        project_url = proj.get("web_url", "")

        # Push README with backlinks
        readme = f"""\
# Pipeleap — Outbound Sales Automation Resources

A collection of resources, templates, and guides for SaaS outbound sales teams.

Built to complement **[Pipeleap](https://www.pipeleap.com)** — the workflow orchestration layer
that automates signal capture, lead enrichment, multi-channel sequencing, and CRM write-back.

## Resources

| Resource | Link |
|---|---|
| Platform overview | [pipeleap.com](https://www.pipeleap.com) |
| How it works | [How Pipeleap works](https://www.pipeleap.com/how-it-works) |
| Pricing | [Pipeleap pricing](https://www.pipeleap.com/pricing) |
| GTM Audit | [Free GTM audit](https://www.pipeleap.com/gtm-audit) |
| Blog | [Outbound sales blog](https://www.pipeleap.com/blog) |
| Glossary | [Sales automation glossary](https://www.pipeleap.com/glossary) |

## About Pipeleap

Pipeleap sits above your existing stack — Apollo, Clay, HubSpot, Outreach — as an orchestration layer.
It captures intent signals (website visits, ICP triggers, job changes), enriches leads automatically,
enrolls them in the right sequence, routes replies, and writes outcomes back to the CRM.
No manual research. No hand-off delays. Predictable pipeline.
"""
        import base64 as _b64
        _requests.post(f"{self.API}/projects/{pid}/repository/files/README.md", headers=headers, json={
            "branch": "main",
            "content": readme,
            "commit_message": "Add Pipeleap resources README",
            "encoding": "text",
        }, timeout=15)

        print(f"    ✓ {project_url}")
        return {"ok": True, "url": project_url, "project_id": pid}


class CratesIoPublisher:
    """
    Generates a minimal Rust crate (pipeleap-tools) with homepage pointing to pipeleap.com.

    crates.io is DA72. The crate's homepage field + README creates a backlink from
    crates.io/crates/pipeleap-tools.

    User runs: cd outputs/backlinks/crates/pipeleap-tools && cargo publish
    (requires free crates.io account — log in once with `cargo login <token>`)
    """

    is_configured = True

    def create_crate(self, output_dir: str = "outputs/backlinks/crates") -> dict[str, Any]:
        pkg = Path(output_dir) / "pipeleap-tools"
        src = pkg / "src"
        src.mkdir(parents=True, exist_ok=True)

        (pkg / "Cargo.toml").write_text("""\
[package]
name = "pipeleap-tools"
version = "0.1.0"
edition = "2021"
description = "Outbound sales automation utilities for SaaS revenue teams"
homepage = "https://www.pipeleap.com"
repository = "https://github.com/manikanakathala-droid/pipeleap-launchpad"
documentation = "https://www.pipeleap.com/how-it-works"
readme = "README.md"
license = "MIT"
keywords = ["outbound", "sales", "automation", "saas", "workflow"]
categories = ["command-line-utilities", "text-processing"]
""", encoding="utf-8")

        (src / "lib.rs").write_text("""\
//! pipeleap-tools — utilities for outbound sales automation.
//! Companion library for [Pipeleap](https://www.pipeleap.com).

/// Convert a string to a URL-safe slug.
pub fn slugify(text: &str) -> String {
    text.to_lowercase()
        .chars()
        .map(|c| if c.is_alphanumeric() { c } else { '-' })
        .collect::<String>()
        .split('-')
        .filter(|s| !s.is_empty())
        .collect::<Vec<_>>()
        .join("-")
}

/// Estimate reading time in minutes (at 220 wpm).
pub fn estimate_read_time(text: &str) -> usize {
    let words = text.split_whitespace().count();
    std::cmp::max(1, (words as f64 / 220.0).round() as usize)
}
""", encoding="utf-8")

        (pkg / "README.md").write_text("""\
# pipeleap-tools

Utility crate for outbound sales automation, companion to [Pipeleap](https://www.pipeleap.com).

## What is Pipeleap?

[Pipeleap](https://www.pipeleap.com) automates your outbound motion end-to-end:
signal capture → enrichment → sequencing → reply routing → CRM write-back.

## Usage

```rust
use pipeleap_tools::{slugify, estimate_read_time};

let slug = slugify("How to automate outbound sales");
// → "how-to-automate-outbound-sales"

let mins = estimate_read_time("Your article content here...");
// → 1
```

## Links

- Website: https://www.pipeleap.com
- Blog: https://www.pipeleap.com/blog
- GTM Audit: https://www.pipeleap.com/gtm-audit
""", encoding="utf-8")

        print(f"  Rust crate created at: {pkg}")
        print(f"  To publish: cd {pkg} && cargo login <token> && cargo publish")
        return {"ok": True, "path": str(pkg), "crate_name": "pipeleap-tools"}


class FeedDirectoryPublisher:
    """
    Submits Pipeleap's RSS feed URL to free feed directories and aggregators.

    These directories crawl submitted feeds, index the content, and display
    it with a backlink to the source. All endpoints are free, no account needed.

    Targeted directories: Feedspot, Blogarama, AllTop-style aggregators, and
    open feed registries that accept HTTP submission.
    """

    FEED_URL  = f"{SITE_URL}/feed.xml"

    # Directories that accept feed submissions via simple HTTP POST or GET
    DIRECTORIES: list[dict] = [
        {
            "name": "Feedspot",
            "url":  "https://www.feedspot.com/fs/addurl",
            "method": "POST",
            "data": {"feedUrl": FEED_URL, "websiteUrl": SITE_URL, "category": "business"},
        },
        {
            "name": "Blogarama",
            "url": "https://www.blogarama.com/add-your-blog",
            "method": "POST",
            "data": {"blog_url": SITE_URL, "feed_url": FEED_URL, "category": "business"},
        },
        {
            "name": "Blog Engage",
            "url": "https://www.blogengage.com/submit",
            "method": "POST",
            "data": {"url": SITE_URL, "feed": FEED_URL},
        },
        {
            "name": "Blog Catalog",
            "url": "https://www.blogcatalog.com/submit",
            "method": "POST",
            "data": {"url": SITE_URL, "feed_url": FEED_URL},
        },
        {
            "name": "OnTopList",
            "url": "https://www.ontoplist.com/submit",
            "method": "POST",
            "data": {"url": SITE_URL, "feed": FEED_URL, "category": "business"},
        },
        {
            "name": "RSSing",
            "url": "https://www.rssing.com/addsite.php",
            "method": "POST",
            "data": {"siteurl": SITE_URL, "feedurl": FEED_URL},
        },
    ]

    is_configured = True

    def submit_all(self) -> dict[str, Any]:
        if not _HAS_REQUESTS:
            return {"ok": False, "error": "requests not installed"}

        submitted, failed = [], []
        headers = {"User-Agent": "Mozilla/5.0 (compatible; PipeleapSEOBot/1.0)"}

        for directory in self.DIRECTORIES:
            try:
                if directory["method"] == "POST":
                    resp = _requests.post(
                        directory["url"],
                        data=directory["data"],
                        headers=headers,
                        timeout=10,
                        allow_redirects=True,
                    )
                else:
                    resp = _requests.get(
                        directory["url"],
                        params=directory["data"],
                        headers=headers,
                        timeout=10,
                    )

                if resp.status_code in range(200, 400):
                    submitted.append(directory["name"])
                    print(f"    ✓ {directory['name']}")
                else:
                    failed.append({"name": directory["name"], "status": resp.status_code})
                    print(f"    ✗ {directory['name']} (HTTP {resp.status_code})")
            except Exception as exc:
                failed.append({"name": directory["name"], "error": str(exc)})
                print(f"    ✗ {directory['name']} ({exc})")
            time.sleep(0.5)

        return {"ok": True, "submitted": submitted, "failed": failed, "total": len(self.DIRECTORIES)}


class MastodonPublisher:
    """
    Posts content to Mastodon (mastodon.social, DA72).

    Mastodon posts are public, indexed by Google, and carry a backlink in the
    post body. Posts from mastodon.social appear in federated timelines across
    500+ Fediverse instances.

    Requires: free account at mastodon.social + MASTODON_TOKEN env var
    (Settings → Development → New Application → read+write scope)
    """

    API = "https://mastodon.social/api/v1"

    POSTS = [
        f"We built Pipeleap to solve the orchestration gap in SaaS outbound. Most teams have the tools — Apollo, Clay, HubSpot — but no layer governing how they work together.\n\nResult: predictable, automated pipeline.\n\n🔗 {SITE_URL}/how-it-works\n\n#SaaS #OutboundSales #SalesAutomation #RevOps",
        f"Signal-based outbound is replacing cold lists. Instead of buying contacts and hoping for relevance, you monitor buying signals and reach out only when a prospect is already in-market.\n\n11× higher reply rates. Real pipeline.\n\n🔗 {SITE_URL}/blog/signal-based-outbound-sales\n\n#B2BSales #SDR #OutboundSales #GTM",
        f"The GTM teams winning in 2026 have one thing in common: they automated the gap between signal and sequence.\n\nCapture intent → enrich automatically → enroll → route replies → CRM write-back. No humans in the loop.\n\n🔗 {SITE_URL}\n\n#SalesAutomation #SaaS #RevOps #PipelineGeneration",
    ]

    def __init__(self) -> None:
        self.token = os.environ.get("MASTODON_TOKEN", "")

    @property
    def configured(self) -> bool:
        return bool(self.token)

    def post_all(self) -> dict[str, Any]:
        if not _HAS_REQUESTS or not self.configured:
            return {"ok": False, "error": "Set MASTODON_TOKEN (free account at mastodon.social → Settings → Development)"}

        headers = {"Authorization": f"Bearer {self.token}"}
        posted, failed = [], []

        for status in self.POSTS:
            try:
                resp = _requests.post(
                    f"{self.API}/statuses",
                    headers=headers,
                    json={"status": status, "visibility": "public"},
                    timeout=10,
                )
                data = resp.json()
                if resp.status_code == 200 and "url" in data:
                    posted.append(data["url"])
                    print(f"    ✓ {data['url']}")
                else:
                    failed.append({"error": data.get("error", f"HTTP {resp.status_code}")})
                    print(f"    ✗ {data.get('error', f'HTTP {resp.status_code}')}")
            except Exception as exc:
                failed.append({"error": str(exc)})
                print(f"    ✗ {exc}")
            time.sleep(2.0)

        return {"ok": True, "posted": posted, "failed": failed, "total": len(self.POSTS)}


# ── Master runner ─────────────────────────────────────────────────────────────

def run_all_api_backlinks(
    github_token:    str = "",
    blogger_blog_id: str = "",
) -> dict[str, Any]:
    print("\n=== API Backlink Publisher ===\n")
    results: dict[str, Any] = {"started_at": datetime.now(timezone.utc).isoformat()}

    # GitHub — highest DA
    print("[1/14] GitHub (DA95)...")
    gh = GitHubPublisher(github_token)
    if gh.configured:
        results["github_repo"]  = gh.create_resource_repo()
        results["github_gists"] = gh.create_gists()
    else:
        results["github"] = {"ok": False, "error": "Set GITHUB_TOKEN env var"}
        print("  Skipped — set GITHUB_TOKEN")

    # WordPress.com — DA94, free blog, REST API
    print("\n[2/14] WordPress.com (DA94)...")
    wp = WordPressPublisher()
    results["wordpress"] = wp.publish_articles()
    if not wp.configured:
        print("  Skipped — set WP_SITE_URL, WP_USERNAME, WP_APP_PASSWORD (free blog at wordpress.com)")

    # PyPI — always runs (no credentials needed for package creation)
    print("\n[3/14] PyPI package (DA85)...")
    results["pypi"] = create_pypi_package()

    # Blogger — DA74, Google-owned, instant Google indexing
    print("\n[4/14] Blogger / Blogspot (DA74, Google-owned)...")
    bl = BloggerPublisher(blogger_blog_id)
    results["blogger"] = bl.publish_articles()
    if not bl.configured:
        print("  Skipped — set BLOGGER_BLOG_ID (create blog at blogger.com, enable Blogger API in n8n-xamplify)")

    # Reddit — DA91, posts appear in Google search results
    print("\n[5/14] Reddit (DA91)...")
    rd = RedditPublisher()
    results["reddit"] = rd.publish_articles()
    if not rd.configured:
        print("  Skipped — set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD")

    # ── Zero-credential publishers (always run, no setup needed) ──────────────

    # Wayback Machine — DA95+, creates real Google-indexed archive.org backlinks
    print("\n[6/14] Wayback Machine / archive.org (DA95, zero credentials)...")
    wb = WaybackMachinePublisher()
    results["wayback"] = wb.save_all()
    saved_count = len(results["wayback"].get("saved", []))
    print(f"  {saved_count}/{len(_ALL_SITE_PAGES)} pages archived on archive.org")

    # Blog ping — notifies 20+ directories of new content, triggers crawl
    print("\n[7/14] Blog ping services (20+ directories, zero credentials)...")
    bp = BlogPingPublisher()
    results["blog_ping"] = bp.ping_all()
    ping_count = len(results["blog_ping"].get("pinged", []))
    print(f"  {ping_count}/{len(BlogPingPublisher.PING_TARGETS)} directories pinged")

    # WebSub — notifies Google hub + Superfeedr, pushes RSS to Feedly/NewsBlur
    print("\n[8/14] WebSub / PubSubHubbub hubs (zero credentials)...")
    ws = WebSubPublisher()
    results["websub"] = ws.ping_all()
    hub_count = len(results["websub"].get("notified", []))
    print(f"  {hub_count}/{len(WebSubPublisher.HUBS)} hubs notified")

    # Telegraph — DA76, zero credential, creates indexed pages at telegra.ph
    print("\n[9/14] Telegraph / telegra.ph (DA76, zero credentials)...")
    tg = TelegraphPublisher()
    results["telegraph"] = tg.publish_all()
    tg_count = len(results["telegraph"].get("published", []))
    print(f"  {tg_count}/{len(TelegraphPublisher.ARTICLES)} articles published on telegra.ph")

    # npm package — DA92, generates package for `npm publish`
    print("\n[10/14] npm package (DA92)...")
    npm = NpmPackagePublisher()
    results["npm"] = npm.create_package()
    print(f"  Package ready — run: cd {results['npm'].get('path', '')} && npm publish --access public")

    # GitLab — DA95, creates public project with README backlinks
    print("\n[11/14] GitLab (DA95)...")
    gl = GitLabPublisher()
    if gl.configured:
        results["gitlab"] = gl.create_project()
    else:
        results["gitlab"] = {"ok": False, "error": "Set GITLAB_TOKEN (free account at gitlab.com)"}
        print("  Skipped — set GITLAB_TOKEN")

    # Crates.io — DA72, generates Rust crate for `cargo publish`
    print("\n[12/14] crates.io Rust crate (DA72)...")
    cr = CratesIoPublisher()
    results["crates_io"] = cr.create_crate()
    print(f"  Crate ready — run: cd {results['crates_io'].get('path', '')} && cargo publish")

    # Feed directories — submit RSS feed to 6 free aggregators
    print("\n[13/14] RSS feed directories (6 aggregators, zero credentials)...")
    fd = FeedDirectoryPublisher()
    results["feed_directories"] = fd.submit_all()
    fd_count = len(results["feed_directories"].get("submitted", []))
    print(f"  {fd_count}/{len(FeedDirectoryPublisher.DIRECTORIES)} directories submitted")

    # Mastodon — DA72, public posts indexed by Google, Fediverse distribution
    print("\n[14/14] Mastodon / mastodon.social (DA72)...")
    ms = MastodonPublisher()
    if ms.configured:
        results["mastodon"] = ms.post_all()
    else:
        results["mastodon"] = {"ok": False, "error": "Set MASTODON_TOKEN (free account at mastodon.social)"}
        print("  Skipped — set MASTODON_TOKEN (Settings → Development → New Application)")

    # Save report
    (OUTPUT / "api_backlinks_report.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nReport saved: {OUTPUT}/api_backlinks_report.json")
    return results
