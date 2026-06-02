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
    ("https://www.pipeleap.com/results", "monthly", "0.8"),
    ("https://www.pipeleap.com/gtm-audit", "monthly", "0.9"),
    ("https://www.pipeleap.com/pricing", "monthly", "0.8"),
    ("https://www.pipeleap.com/about", "monthly", "0.7"),
    ("https://www.pipeleap.com/contact", "monthly", "0.8"),
    ("https://www.pipeleap.com/faq", "monthly", "0.7"),
    ("https://www.pipeleap.com/blog", "weekly", "0.9"),
    ("https://www.pipeleap.com/glossary", "monthly", "0.8"),
    ("https://www.pipeleap.com/privacy", "monthly", "0.3"),
]

blog_posts = [
    ("ai-outbound-sales-agents", "2026-05-17"),
    ("automated-outbound", "2026-05-22"),
    ("b2b-outbound-automation-stack", "2026-05-18"),
    ("best-workflow-orchestration-tools-for-saas-sales-teams", "2026-05-18"),
    ("clay-sales-navigator", "2026-05-22"),
    ("enterprise-saas-sales-workflow-governance", "2026-05-18"),
    ("how-to-automate-outbound-emails", "2026-05-26"),
    ("how-to-automate-sales-workflows", "2026-05-08"),
    ("lead-enrichment-workflows", "2026-05-26"),
    ("pipeleap", "2026-05-26"),
    ("pipeleap-vs-clay-which-is-better-for-outbound", "2026-05-18"),
    ("revenue-automation-platform", "2026-05-18"),
    ("saas-sales-team-workflow-automation", "2026-05-26"),
    ("sales-ops-automation-guide", "2026-05-06"),
    ("scale-sdr-efficiency-without-hiring", "2026-05-18"),
    ("what-is-sales-automation", "2026-05-04"),
]

tool_categories = [
    "ai-sdr-tools", "cold-email-tools", "sales-engagement-tools", "prospecting-tools",
    "lead-enrichment-tools", "crm-tools", "call-recording-tools", "revenue-intelligence-tools",
    "linkedin-automation-tools", "ai-outbound-agents", "workflow-automation-tools",
    "sales-analytics-tools", "gtm-engineering-tools",
]

# Map category -> list of tool slugs
tools_by_category = {
    "ai-sdr-tools": ["artisan-ai", "11x-ai", "regie-ai", "ava-by-artisan", "sdrx-by-klenty", "exceed-ai", "conversica", "reply-io-ai-sdr", "piper-by-qualified", "outplay-ai"],
    "cold-email-tools": ["instantly-ai", "lemlist", "smartlead", "mailshake", "woodpecker", "apollo-io-email", "reply-io", "saleshandy", "quickmail", "klenty"],
    "sales-engagement-tools": ["outreach", "salesloft", "apollo-io-engagement", "hubspot-sales-hub", "groove", "klenty-engagement", "reply-io-engagement", "close-io", "mixmax", "yesware"],
    "prospecting-tools": ["apollo-io-prospecting", "zoominfo", "cognism", "lusha", "hunter-io", "linkedin-sales-navigator", "clay-prospecting", "leadfeeder", "clearbit-prospecting", "bombora"],
    "lead-enrichment-tools": ["clay", "clearbit", "zoominfo-enrich", "lusha-enrich", "apollo-io-enrich", "cognism-enrich", "hunter-io-enrich", "people-data-labs", "datagma", "leadmagic"],
    "crm-tools": ["hubspot-crm", "salesforce", "pipedrive", "close-io-crm", "attio", "folk", "breakcold", "copper-crm", "monday-sales-crm", "streak"],
    "call-recording-tools": ["gong", "chorus-zoominfo", "fireflies-ai", "tldv", "avoma", "wingman-clari", "leexi", "modjo", "grain", "otter-ai"],
    "revenue-intelligence-tools": ["gong-revenue", "clari", "6sense", "bombora", "demandbase", "crayon", "g2-buyer-intent", "salesloft-revenue", "highspot", "seismic"],
    "linkedin-automation-tools": ["dripify", "expandi", "meetalfred", "waalaxy", "phantombuster", "skylead", "lemlist-linkedin", "taplio", "linkedin-sales-navigator-auto", "lempod"],
    "ai-outbound-agents": ["11x-ai-agent", "artisan-ai-agent", "regie-ai-agent", "ava-agent", "clay-agent", "instantly-ai-agent", "reply-io-agent", "outreach-ai-agent", "piper-agent"],
    "workflow-automation-tools": ["zapier", "make-integromat", "n8n", "clay-workflow", "hubspot-workflows", "workato", "bardeen", "tray-io", "retool"],
    "sales-analytics-tools": ["gong-analytics", "clari-analytics", "hubspot-analytics", "salesforce-einstein", "tableau", "looker", "ambition", "atrium", "chorus-analytics", "mixpanel-sales"],
    "gtm-engineering-tools": ["clay-gtm", "segment", "census", "hightouch", "common-room", "warmly", "clearbit-gtm", "rb2b", "laudspeaker"],
}

# ── Build sub-sitemaps ────────────────────────────────────────────────
pages_entries = [url(loc, TODAY, freq, pri) for loc, freq, pri in core_pages]
pages_xml = urlset(pages_entries)

blog_entries = [url(f"https://www.pipeleap.com/blog/{slug}", dt, "weekly" if dt >= "2026-05-26" else "monthly") for slug, dt in blog_posts]
blog_xml = urlset(blog_entries)

glossary_entries = [url_inline(f"https://www.pipeleap.com/glossary/{slug}", "2026-05-22", priority="0.6") for slug in glossary_slugs]
glossary_xml = urlset(glossary_entries)

tool_entries = [url(f"https://www.pipeleap.com/tools/{slug}", "2026-05-23", priority="0.8") for slug in tool_categories]
for cat, tools in tools_by_category.items():
    for tool_slug in tools:
        tool_entries.append(url_inline(f"https://www.pipeleap.com/tools/{cat}/{tool_slug}", "2026-05-23"))
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
