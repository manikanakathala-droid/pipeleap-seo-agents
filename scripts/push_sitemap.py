"""
Full rebuild of all 5 sitemap files (index + 4 sub-sitemaps) from hardcoded URL data.
Commits all 5 files to the launchpad repo, then re-submits to GSC + Yandex IndexNow.
"""
import base64, os, re, requests
from datetime import datetime

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

NS = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'

def url(loc, lastmod, changefreq="monthly", priority="0.7"):
    return f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>{changefreq}</changefreq>\n    <priority>{priority}</priority>\n  </url>"

def url_inline(loc, lastmod, changefreq="monthly", priority="0.7"):
    return f'  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod><changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>'

def urlset(entries):
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset {NS}>\n' + "\n".join(entries) + "\n</urlset>\n"

def sitemap_entry(loc, lastmod):
    return f'  <sitemap><loc>{loc}</loc><lastmod>{lastmod}</lastmod></sitemap>'

# ── Fetch glossary slugs ──────────────────────────────────────────────
print("Fetching glossary terms ...")
r = requests.get(f"{API}/repos/{REPO}/contents/src/data/glossary-terms.ts", headers=HEADERS, params={"ref": BRANCH})
r.raise_for_status()
gt_content = base64.b64decode(r.json()["content"]).decode("utf-8")
glossary_slugs = re.findall(r"slug:\s*[\"']([\w-]+)[\"']\s*,\s*term:", gt_content)
print(f"  Found {len(glossary_slugs)} glossary terms")

# ── Fetch blog slugs ──────────────────────────────────────────────
print("Fetching blog slugs ...")
r_b = requests.get(f"{API}/repos/{REPO}/contents/src/data/blog-articles.ts", headers=HEADERS, params={"ref": BRANCH})
r_b.raise_for_status()
blog_content = base64.b64decode(r_b.json()["content"]).decode("utf-8")
blog_slugs = re.findall(r'"slug":\s*"([^"]+)"', blog_content) + re.findall(r'slug:\s*`([^`]+)`', blog_content)
print(f"  Found {len(blog_slugs)} blog slugs")

# ── Fetch case study slugs ────────────────────────────────────────────
print("Fetching case study slugs ...")
r_cs = requests.get(f"{API}/repos/{REPO}/contents/src/data/case-studies.ts", headers=HEADERS, params={"ref": BRANCH})
r_cs.raise_for_status()
cs_content = base64.b64decode(r_cs.json()["content"]).decode("utf-8")
case_study_slugs = re.findall(r"slug:\s*[\"']([\w-]+)[\"']", cs_content)
print(f"  Found {len(case_study_slugs)} case study slugs")

# ── Fetch App.tsx for static routes ───────────────────────────────────
print("Fetching static routes from App.tsx ...")
r_a = requests.get(f"{API}/repos/{REPO}/contents/src/App.tsx", headers=HEADERS, params={"ref": BRANCH})
r_a.raise_for_status()
app_content = base64.b64decode(r_a.json()["content"]).decode("utf-8")
static_routes = re.findall(r'path="/([a-z][\w/()-]*)"', app_content)
static_routes_no_param = [r for r in static_routes if ':' not in r and r != '*']

# ── Fetch tool slugs ──────────────────────────────────────────────
print("Fetching tool categories and slugs ...")
r2 = requests.get(f"{API}/repos/{REPO}/contents/src/data/tools/categories.ts", headers=HEADERS, params={"ref": BRANCH})
r2.raise_for_status()
cat_content = base64.b64decode(r2.json()["content"]).decode("utf-8")
# Extract category slug + tool list from each block
tool_blocks = re.findall(r"slug:\s*[\"']([\w-]+)[\"']\s*,\s*name:\s*[\"']([^\"']+)[\"'][\s\S]*?tools:\s*\[([^\]]+)\]", cat_content)
tool_categories = []
tools_by_category: dict[str, list[str]] = {}
for cat_slug, cat_name, tools_list in tool_blocks:
    tool_categories.append(cat_slug)
    tool_slugs = re.findall(r"[\"']([\w-]+)[\"']", tools_list)
    tools_by_category[cat_slug] = tool_slugs
print(f"  Found {len(tool_categories)} tool categories, {sum(len(v) for v in tools_by_category.values())} tools")

# ── Page data ─────────────────────────────────────────────────────────
core_pages = [
    ("https://www.pipeleap.com/", "weekly", "1.0"),
]
# Add routes from App.tsx, filtering out param routes
route_priorities = {
    'services': ('monthly', '0.9'), 'how-it-works': ('monthly', '0.8'),
    'gtm-audit': ('monthly', '0.9'), 'pricing': ('monthly', '0.8'),
    'about': ('monthly', '0.7'), 'contact': ('monthly', '0.8'),
    'faq': ('monthly', '0.7'), 'blog': ('weekly', '0.9'),
    'glossary': ('monthly', '0.8'), 'tools': ('weekly', '0.9'),
    'case-studies': ('weekly', '0.9'), 'outbound-automation': ('weekly', '0.8'),
    'privacy': ('monthly', '0.3'), 'terms': ('monthly', '0.3'),
}
for route in static_routes_no_param:
    freq, pri = route_priorities.get(route, ('monthly', '0.7'))
    core_pages.append((f"https://www.pipeleap.com/{route}", freq, pri))

# Add case study detail pages
for slug in case_study_slugs:
    core_pages.append((f"https://www.pipeleap.com/case-studies/{slug}", "monthly", "0.7"))

pages_entries = [url(loc, TODAY, changefreq, priority) for loc, changefreq, priority in core_pages]
pages_xml = urlset(pages_entries)

blog_entries = [url(f"https://www.pipeleap.com/blog/{slug}", TODAY, "weekly") for slug in blog_slugs]
blog_xml = urlset(blog_entries)

glossary_entries = [url_inline(f"https://www.pipeleap.com/glossary/{slug}", TODAY, priority="0.6") for slug in glossary_slugs]
glossary_xml = urlset(glossary_entries)

tool_entries = [url(f"https://www.pipeleap.com/tools/{slug}", TODAY, priority="0.8") for slug in tool_categories]
for cat, tools in tools_by_category.items():
    for tool_slug in tools:
        tool_entries.append(url_inline(f"https://www.pipeleap.com/tools/{cat}/{tool_slug}", TODAY))
tools_xml = urlset(tool_entries)

# ── Build sitemap index ───────────────────────────────────────────────
index_xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex {NS}>\n'
for sub in ["pages", "blog", "tools", "glossary"]:
    index_xml += sitemap_entry(f"https://www.pipeleap.com/sitemap-{sub}.xml", TODAY) + "\n"
index_xml += "</sitemapindex>\n"

# ── Commit all 5 files ───────────────────────────────────────────────
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

files = [
    ("public/sitemap-pages.xml", pages_xml, f"seo: rebuild sitemap-pages.xml — {len(core_pages)} core URL(s)"),
    ("public/sitemap-blog.xml", blog_xml, f"seo: rebuild sitemap-blog.xml — {len(blog_slugs)} blog URL(s)"),
    ("public/sitemap-glossary.xml", glossary_xml, f"seo: rebuild sitemap-glossary.xml — {len(glossary_slugs)} glossary URL(s)"),
    ("public/sitemap-tools.xml", tools_xml, f"seo: rebuild sitemap-tools.xml — {len(tool_entries)} tool URL(s)"),
    ("public/sitemap.xml", index_xml, "seo: rebuild sitemap index -> 4 sub-sitemaps"),
]

print("\nCommitting sitemap files ...")
for path, content, msg in files:
    try:
        _, sha = get_file(path)
        commit_file(path, content, sha, msg)
    except Exception as e:
        print(f"  [SKIP] {path}: {e}")

total = len(core_pages) + len(blog_slugs) + len(glossary_slugs) + len(tool_entries)
print(f"\nTotal: {total} URLs across 4 sub-sitemaps")

# ── Re-submit to GSC (clean stale entries first) ──────────────────────
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

    # List existing sitemaps
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

    # Submit current sitemaps
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

# Bing sitemap submission handled by PostPublishHook — not duplicated here.

print(f"\nDone. {total} URLs across 4 sub-sitemaps + index.")
