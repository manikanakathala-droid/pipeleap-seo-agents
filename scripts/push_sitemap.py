"""
Full rebuild of all 5 sitemap files (index + 4 sub-sitemaps) from hardcoded URL data.
Commits all 5 files to the launchpad repo, then re-submits to GSC + Yandex IndexNow.

Usage:
    # API mode (standalone — reads from GitHub, commits via API):
    python scripts/push_sitemap.py

    # Local mode (reads from local checkout, writes files in-place):
    python scripts/push_sitemap.py --local-dir path/to/launchpad
"""
import argparse
import base64
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

TOKEN  = os.getenv("GITHUB_TOKEN", "")
REPO   = "manikanakathala-droid/pipeleap-launchpad-040053e5"
BRANCH = "main"
API    = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
TODAY = datetime.now().strftime("%Y-%m-%d")

# ── Persistent lastmod store ───────────────────────────────────────────
LASTMOD_PATH = os.path.join(os.path.dirname(__file__), "..", "outputs", "sitemap_lastmod.json")
lastmod_store: dict[str, str] = {}
if os.path.exists(LASTMOD_PATH):
    try:
        with open(LASTMOD_PATH, "r") as f:
            lastmod_store = json.load(f)
    except Exception as e:
        print(f"  Warning: could not load {LASTMOD_PATH}: {e}")

def get_lastmod(url: str) -> str:
    """Return stored lastmod if known, otherwise today (saved for future runs)."""
    if url not in lastmod_store:
        lastmod_store[url] = TODAY
    return lastmod_store[url]

def save_lastmod_store() -> None:
    os.makedirs(os.path.dirname(LASTMOD_PATH), exist_ok=True)
    with open(LASTMOD_PATH, "w") as f:
        json.dump(lastmod_store, f, indent=2)
    print(f"  Saved {len(lastmod_store)} lastmod entries to {LASTMOD_PATH}")

NS = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'

def url(loc, lastmod, changefreq="monthly", priority="0.7"):
    return f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>{changefreq}</changefreq>\n    <priority>{priority}</priority>\n  </url>"

def url_inline(loc, lastmod, changefreq="monthly", priority="0.7"):
    return f'  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod><changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>'

def urlset(entries):
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset {NS}>\n' + "\n".join(entries) + "\n</urlset>\n"

def sitemap_entry(loc, lastmod):
    return f'  <sitemap><loc>{loc}</loc><lastmod>{lastmod}</lastmod></sitemap>'


def read_file_local(local_dir: str, path: str) -> str:
    """Read a file from local checkout."""
    full = Path(local_dir) / path
    if not full.exists():
        return ""
    return full.read_text(encoding="utf-8")


def read_file_api(path: str) -> str:
    """Read a file from GitHub API."""
    r = requests.get(f"{API}/repos/{REPO}/contents/{path}", headers=HEADERS, params={"ref": BRANCH})
    r.raise_for_status()
    return base64.b64decode(r.json()["content"]).decode("utf-8")


# ── Slug extraction helpers ───────────────────────────────────────────

def extract_glossary_slugs(content: str) -> list[str]:
    return re.findall(r"slug:\s*[\"']([\w-]+)[\"']\s*,\s*term:", content)

def extract_blog_slugs(content: str) -> list[str]:
    return re.findall(r'"slug":\s*"([^"]+)"', content) + re.findall(r'slug:\s*`([^`]+)`', content)

def extract_case_study_slugs(content: str) -> list[str]:
    return re.findall(r"slug:\s*[\"']([\w-]+)[\"']", content)

def extract_static_routes(content: str) -> list[str]:
    routes = re.findall(r'path="/([a-z][\w/()-]*)"', content)
    return [r for r in routes if ':' not in r and r != '*']

def extract_tool_slugs(content: str):
    """Return (categories_list, tools_by_category_dict)."""
    tool_blocks = re.findall(
        r"slug:\s*[\"']([\w-]+)[\"']\s*,\s*name:\s*[\"']([^\"']+)[\"']"
        r"[\s\S]*?tools:\s*\[([^\]]+)\]",
        content,
    )
    categories = []
    by_cat: dict[str, list[str]] = {}
    for cat_slug, cat_name, tools_list in tool_blocks:
        categories.append(cat_slug)
        by_cat[cat_slug] = re.findall(r"[\"']([\w-]+)[\"']", tools_list)
    return categories, by_cat


# ── Build XML ──────────────────────────────────────────────────────────

def build_sitemaps(local_dir: str | None = None) -> dict[str, str]:
    """
    Build all 5 sitemap XML files.
    Returns dict of filename -> XML content.
    """
    if local_dir:
        read_fn = lambda path: read_file_local(local_dir, path)
    else:
        import requests as _req
        global requests
        requests = _req
        read_fn = read_file_api

    # Fetch glossary slugs
    print("Fetching glossary terms ...")
    gt_content = read_fn("src/data/glossary-terms.ts")
    glossary_slugs = extract_glossary_slugs(gt_content) if gt_content else []
    print(f"  Found {len(glossary_slugs)} glossary terms")

    # Fetch blog slugs
    print("Fetching blog slugs ...")
    blog_content = read_fn("src/data/blog-articles.ts")
    blog_slugs = extract_blog_slugs(blog_content) if blog_content else []
    print(f"  Found {len(blog_slugs)} blog slugs")

    # Fetch case study slugs
    print("Fetching case study slugs ...")
    cs_content = read_fn("src/data/case-studies.ts")
    case_study_slugs = extract_case_study_slugs(cs_content) if cs_content else []
    print(f"  Found {len(case_study_slugs)} case study slugs")

    # Fetch static routes from App.tsx
    print("Fetching static routes from App.tsx ...")
    app_content = read_fn("src/App.tsx")
    static_routes_no_param = extract_static_routes(app_content) if app_content else []
    print(f"  Found {len(static_routes_no_param)} static routes")

    # Fetch tool slugs
    print("Fetching tool categories and slugs ...")
    cat_content = read_fn("src/data/tools/categories.ts")
    tool_categories, tools_by_category = extract_tool_slugs(cat_content) if cat_content else ([], {})
    print(f"  Found {len(tool_categories)} tool categories, {sum(len(v) for v in tools_by_category.values())} tools")

    # ── Page data ─────────────────────────────────────────────────────────
    core_pages = [
        ("https://www.pipeleap.com/", "weekly", "1.0"),
    ]
    route_priorities = {
        'services': ('monthly', '0.9'), 'how-it-works': ('monthly', '0.8'),
        'sales-ops-audit': ('monthly', '0.9'), 'pricing': ('monthly', '0.8'),
        'about': ('monthly', '0.7'), 'contact': ('monthly', '0.8'),
        'faq': ('monthly', '0.7'), 'blog': ('weekly', '0.9'),
        'glossary': ('monthly', '0.8'), 'tools': ('weekly', '0.9'),
        'case-studies': ('weekly', '0.9'), 'outbound-automation': ('weekly', '0.8'),
        'privacy': ('monthly', '0.3'), 'terms': ('monthly', '0.3'),
    }
    for route in static_routes_no_param:
        freq, pri = route_priorities.get(route, ('monthly', '0.7'))
        core_pages.append((f"https://www.pipeleap.com/{route}", freq, pri))

    for slug in case_study_slugs:
        core_pages.append((f"https://www.pipeleap.com/case-studies/{slug}", "monthly", "0.7"))

    pages_entries = [url(loc, get_lastmod(loc), changefreq, priority) for loc, changefreq, priority in core_pages]
    pages_xml = urlset(pages_entries)

    blog_entries = [
        url(f"https://www.pipeleap.com/blog/{slug}", get_lastmod(f"https://www.pipeleap.com/blog/{slug}"), "weekly")
        for slug in blog_slugs
    ]
    blog_xml = urlset(blog_entries)

    glossary_entries = [
        url_inline(f"https://www.pipeleap.com/glossary/{slug}", get_lastmod(f"https://www.pipeleap.com/glossary/{slug}"), priority="0.6")
        for slug in glossary_slugs
    ]
    glossary_xml = urlset(glossary_entries)

    tool_entries = [
        url(f"https://www.pipeleap.com/tools/{slug}", get_lastmod(f"https://www.pipeleap.com/tools/{slug}"), priority="0.8")
        for slug in tool_categories
    ]
    for cat, tools in tools_by_category.items():
        for tool_slug in tools:
            tool_entries.append(
                url_inline(f"https://www.pipeleap.com/tools/{cat}/{tool_slug}", get_lastmod(f"https://www.pipeleap.com/tools/{cat}/{tool_slug}"))
            )
    tools_xml = urlset(tool_entries)

    # ── Build sitemap index ───────────────────────────────────────────────
    index_xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex {NS}>\n'
    for sub in ["pages", "blog", "tools", "glossary"]:
        url_idx = f"https://www.pipeleap.com/sitemap-{sub}.xml"
        index_xml += sitemap_entry(url_idx, get_lastmod(url_idx)) + "\n"
    index_xml += "</sitemapindex>\n"

    total = len(core_pages) + len(blog_slugs) + len(glossary_slugs) + len(tool_entries)
    print(f"\nTotal: {total} URLs across 4 sub-sitemaps")

    return {
        "sitemap.xml": index_xml,
        "sitemap-pages.xml": pages_xml,
        "sitemap-blog.xml": blog_xml,
        "sitemap-glossary.xml": glossary_xml,
        "sitemap-tools.xml": tools_xml,
    }


# ── Commit helpers (API mode only) ────────────────────────────────────

def get_file(path):
    r = requests.get(f"{API}/repos/{REPO}/contents/{path}", headers=HEADERS, params={"ref": BRANCH})
    r.raise_for_status()
    d = r.json()
    return base64.b64decode(d["content"]).decode("utf-8"), d["sha"]

def commit_file(path, content, sha, message):
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "sha": sha, "branch": BRANCH,
    }
    r = requests.put(f"{API}/repos/{REPO}/contents/{path}", headers=HEADERS, json=payload)
    ok = r.status_code in (200, 201)
    print(f"  [{'OK' if ok else 'FAIL'}] {path}" + ("" if ok else f": {r.status_code} {r.text[:120]}"))
    return ok


# ── GSC submission ────────────────────────────────────────────────────

def submit_to_gsc() -> None:
    print("\nCleaning stale sitemaps from Google Search Console ...")
    GSC_SITE = "sc-domain:pipeleap.com"
    CURRENT_GSC_SITEMAPS = {
        "https://www.pipeleap.com/sitemap.xml",
        "https://www.pipeleap.com/sitemap-pages.xml",
        "https://www.pipeleap.com/sitemap-blog.xml",
        "https://www.pipeleap.com/sitemap-tools.xml",
        "https://www.pipeleap.com/sitemap-glossary.xml",
    }
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        creds = service_account.Credentials.from_service_account_file(
            "credentials/gsc_service_account.json",
            scopes=["https://www.googleapis.com/auth/webmasters"],
        )
        svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

        listed = svc.sitemaps().list(siteUrl=GSC_SITE).execute()
        existing = listed.get("sitemap", [])
        stale_count = 0
        for entry in existing:
            path = entry.get("path", "")
            if path not in CURRENT_GSC_SITEMAPS:
                print(f"  STALE: {path} — deleting ...")
                try:
                    svc.sitemaps().delete(siteUrl=GSC_SITE, feedpath=path).execute()
                    print(f"    Deleted {path}")
                    stale_count += 1
                except HttpError as e:
                    print(f"    Delete error: {e}")
            else:
                print(f"  CURRENT: {path} — keeping")
        if stale_count == 0:
            print("  No stale sitemaps found.")

        print("\nSubmitting current sitemaps to GSC ...")
        for sub in ["pages", "blog", "tools", "glossary"]:
            url_sub = f"https://www.pipeleap.com/sitemap-{sub}.xml"
            svc.sitemaps().submit(siteUrl=GSC_SITE, feedpath=url_sub).execute()
            print(f"  OK sitemap-{sub}.xml submitted to GSC")
        svc.sitemaps().submit(siteUrl=GSC_SITE,
                              feedpath="https://www.pipeleap.com/sitemap.xml").execute()
        print("  OK sitemap index submitted to GSC")
    except Exception as e:
        print(f"  GSC error: {e}")


# ── Main ──────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild sitemap files")
    parser.add_argument("--local-dir", type=str, default=None,
                        help="Local launchpad checkout directory (reads files from disk, writes XML in-place)")
    parser.add_argument("--commit", action="store_true",
                        help="Also commit and push sitemap changes to git origin, then submit to GSC")
    args = parser.parse_args()

    local_dir = args.local_dir

    sitemaps = build_sitemaps(local_dir=local_dir)

    if local_dir:
        # Local mode: write XML files directly into the checkout
        public_dir = Path(local_dir) / "public"
        public_dir.mkdir(parents=True, exist_ok=True)
        for filename, xml_content in sitemaps.items():
            (public_dir / filename).write_text(xml_content, encoding="utf-8")
            print(f"  Written {public_dir / filename}")
        save_lastmod_store()

        if args.commit:
            # Commit sitemap files to the local git checkout
            import subprocess
            try:
                subprocess.run(
                    ["git", "add", "-f"] + [str(public_dir / f) for f in sitemaps],
                    cwd=local_dir, check=True, capture_output=True, timeout=30,
                )
                result = subprocess.run(
                    ["git", "diff", "--cached", "--quiet"],
                    cwd=local_dir, capture_output=True, timeout=15,
                )
                if result.returncode != 0:
                    subprocess.run(
                        ["git", "commit", "-m", f"seo: rebuild sitemap — {len(sitemaps)} files"],
                        cwd=local_dir, check=True, capture_output=True, timeout=30,
                    )
                    print("  Committed sitemap files to local git checkout")
                    for attempt in range(3):
                        subprocess.run(
                            ["git", "pull", "--rebase", "origin", "main"],
                            cwd=local_dir, capture_output=True, timeout=30,
                        )
                        push = subprocess.run(
                            ["git", "push", "origin", "main"],
                            cwd=local_dir, capture_output=True, timeout=60,
                        )
                        if push.returncode == 0:
                            print("  Pushed sitemap commit to origin")
                            break
                        print(f"  Push attempt {attempt+1} failed, retrying...")
                        subprocess.run(["git", "rebase", "--abort"], cwd=local_dir, capture_output=True, timeout=10)
                        import time; time.sleep((attempt + 1) * 10)
                else:
                    print("  No sitemap changes to commit (files unchanged)")
            except Exception as e:
                print(f"  Git commit/push skipped: {e}")

            # Submit to GSC when sitemap is committed
            submit_to_gsc()

        return 0

    # API mode: commit via GitHub API
    import requests as _req
    global requests
    requests = _req

    files = [
        ("public/sitemap-pages.xml", sitemaps["sitemap-pages.xml"]),
        ("public/sitemap-blog.xml", sitemaps["sitemap-blog.xml"]),
        ("public/sitemap-glossary.xml", sitemaps["sitemap-glossary.xml"]),
        ("public/sitemap-tools.xml", sitemaps["sitemap-tools.xml"]),
        ("public/sitemap.xml", sitemaps["sitemap.xml"]),
    ]

    print("\nCommitting sitemap files ...")
    for path, content in files:
        try:
            _, sha = get_file(path)
            commit_file(path, content, sha, f"seo: rebuild {path} — auto")
        except Exception as e:
            print(f"  [SKIP] {path}: {e}")

    save_lastmod_store()

    submit_to_gsc()
    print(f"\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
