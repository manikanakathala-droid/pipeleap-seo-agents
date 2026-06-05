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

# ── Page data ─────────────────────────────────────────────────────────
core_pages = [
    ("https://www.pipeleap.com/", "weekly", "1.0"),
    ("https://www.pipeleap.com/services", "monthly", "0.9"),
    ("https://www.pipeleap.com/how-it-works", "monthly", "0.8"),
    ("https://www.pipeleap.com/gtm-audit", "monthly", "0.9"),
    ("https://www.pipeleap.com/pricing", "monthly", "0.8"),
    ("https://www.pipeleap.com/about", "monthly", "0.7"),
    ("https://www.pipeleap.com/contact", "monthly", "0.8"),
    ("https://www.pipeleap.com/faq", "monthly", "0.7"),
    ("https://www.pipeleap.com/blog", "weekly", "0.9"),
    ("https://www.pipeleap.com/glossary", "monthly", "0.8"),
    ("https://www.pipeleap.com/tools", "weekly", "0.9"),
    ("https://www.pipeleap.com/case-studies", "weekly", "0.9"),
    ("https://www.pipeleap.com/privacy", "monthly", "0.3"),
    ("https://www.pipeleap.com/terms", "monthly", "0.3"),
]

blog_slugs = [
    "ai-outbound-sales-agents",
    "automated-outbound",
    "b2b-outbound-automation-stack",
    "best-workflow-orchestration-tools-for-saas-sales-teams",
    "clay-sales-navigator",
    "enterprise-saas-sales-workflow-governance",
    "how-to-automate-outbound-emails",
    "how-to-automate-sales-workflows",
    "lead-enrichment-workflows",
    "pipeleap",
    "pipeleap-vs-clay-which-is-better-for-outbound",
    "revenue-automation-platform",
    "saas-sales-team-workflow-automation",
    "sales-ops-automation-guide",
    "scale-sdr-efficiency-without-hiring",
    "what-is-sales-automation",
]

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
    ("public/sitemap-blog.xml", blog_xml, f"seo: rebuild sitemap-blog.xml — {len(blog_posts)} blog URL(s)"),
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

total = len(core_pages) + len(blog_posts) + len(glossary_slugs) + len(tool_entries)
print(f"\nTotal: {total} URLs across 4 sub-sitemaps")

# ── Re-submit to GSC ──────────────────────────────────────────────────
print("\nRe-submitting sitemap index to Google Search Console ...")
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds = service_account.Credentials.from_service_account_file(
        "credentials/gsc_service_account.json",
        scopes=["https://www.googleapis.com/auth/webmasters"],
    )
    svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    for sub in ["pages", "blog", "tools", "glossary"]:
        url_sub = f"https://www.pipeleap.com/sitemap-{sub}.xml"
        svc.sitemaps().submit(siteUrl="sc-domain:pipeleap.com", feedpath=url_sub).execute()
        print(f"  OK sitemap-{sub}.xml submitted to GSC")
    svc.sitemaps().submit(siteUrl="sc-domain:pipeleap.com",
                          feedpath="https://www.pipeleap.com/sitemap.xml").execute()
    print("  OK sitemap index submitted to GSC")
except Exception as e:
    print(f"  GSC error: {e}")

# ── Re-submit to Yandex IndexNow ──────────────────────────────────────
print("\nRe-submitting all URLs to Yandex IndexNow ...")
all_locs = []
for xml in [pages_xml, blog_xml, glossary_xml, tools_xml]:
    all_locs.extend(re.findall(r"<loc>(https://[^<]+)</loc>", xml))
r = requests.post("https://yandex.com/indexnow",
    json={"host": "www.pipeleap.com", "key": "92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55",
          "keyLocation": "https://www.pipeleap.com/92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55.txt",
          "urlList": all_locs}, timeout=20)
print(f"  Yandex: HTTP {r.status_code} — {'OK' if r.status_code in (200,202) else 'FAILED'}")

print(f"\nDone. {total} URLs across 4 sub-sitemaps + index.")
