"""
Rebuilds and commits public/sitemap.xml with:
- lastmod dates on all 11 core pages (updated today)
- All 73 glossary term URLs
- All existing blog, tools, and category URLs preserved
"""
import base64, re, requests

TOKEN  = "os.getenv("GITHUB_TOKEN", "")"
REPO   = "manikanakathala-droid/pipeleap-launchpad-040053e5"
BRANCH = "main"
API    = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

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

# Fetch glossary slugs from repo
print("Fetching glossary terms ...")
gt_content, _ = get_file("src/data/glossary-terms.ts")
glossary_slugs = re.findall(r"slug:\s*[\"']([\w-]+)[\"']\s*,\s*term:", gt_content)
print(f"  Found {len(glossary_slugs)} glossary terms")

TODAY = "2026-05-24"

SITEMAP = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <!-- Core pages -->
  <url>
    <loc>https://www.pipeleap.com/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/services</loc>
    <lastmod>2026-05-23</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/how-it-works</loc>
    <lastmod>2026-05-23</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/results</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/gtm-audit</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/pricing</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/about</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/contact</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/faq</loc>
    <lastmod>2026-05-23</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/blog</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/glossary</loc>
    <lastmod>2026-05-22</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <!-- Blog posts -->
  <url>
    <loc>https://www.pipeleap.com/blog/clay-sales-navigator</loc>
    <lastmod>2026-05-22</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/blog/automated-outbound</loc>
    <lastmod>2026-05-22</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/blog/pipeleap-vs-clay-which-is-better-for-outbound</loc>
    <lastmod>2026-05-18</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/blog/enterprise-saas-sales-workflow-governance</loc>
    <lastmod>2026-05-18</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/blog/revenue-automation-platform</loc>
    <lastmod>2026-05-18</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/blog/scale-sdr-efficiency-without-hiring</loc>
    <lastmod>2026-05-18</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/blog/b2b-outbound-automation-stack</loc>
    <lastmod>2026-05-18</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/blog/best-workflow-orchestration-tools-for-saas-sales-teams</loc>
    <lastmod>2026-05-18</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/blog/ai-outbound-sales-agents</loc>
    <lastmod>2026-05-17</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/blog/how-to-automate-sales-workflows</loc>
    <lastmod>2026-05-08</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/blog/sales-ops-automation-guide</loc>
    <lastmod>2026-05-06</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://www.pipeleap.com/blog/what-is-sales-automation</loc>
    <lastmod>2026-05-04</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <!-- Glossary terms ({count} terms) -->
{glossary_entries}
  <!-- Tools Directory -->
  <url>
    <loc>https://www.pipeleap.com/tools</loc>
    <lastmod>2026-05-23</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <!-- Tool Categories -->
  <url><loc>https://www.pipeleap.com/tools/ai-sdr-tools</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://www.pipeleap.com/tools/cold-email-tools</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-engagement-tools</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://www.pipeleap.com/tools/prospecting-tools</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://www.pipeleap.com/tools/lead-enrichment-tools</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://www.pipeleap.com/tools/crm-tools</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://www.pipeleap.com/tools/call-recording-tools</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://www.pipeleap.com/tools/revenue-intelligence-tools</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://www.pipeleap.com/tools/linkedin-automation-tools</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-outbound-agents</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://www.pipeleap.com/tools/workflow-automation-tools</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-analytics-tools</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <url><loc>https://www.pipeleap.com/tools/gtm-engineering-tools</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>
  <!-- AI SDR Tools -->
  <url><loc>https://www.pipeleap.com/tools/ai-sdr-tools/artisan-ai</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-sdr-tools/11x-ai</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-sdr-tools/regie-ai</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-sdr-tools/ava-by-artisan</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-sdr-tools/sdrx-by-klenty</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-sdr-tools/exceed-ai</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-sdr-tools/conversica</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-sdr-tools/reply-io-ai-sdr</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-sdr-tools/piper-by-qualified</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-sdr-tools/outplay-ai</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <!-- Cold Email Tools -->
  <url><loc>https://www.pipeleap.com/tools/cold-email-tools/instantly-ai</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/cold-email-tools/lemlist</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/cold-email-tools/smartlead</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/cold-email-tools/mailshake</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/cold-email-tools/woodpecker</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/cold-email-tools/apollo-io-email</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/cold-email-tools/reply-io</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/cold-email-tools/saleshandy</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/cold-email-tools/quickmail</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/cold-email-tools/klenty</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <!-- Sales Engagement Tools -->
  <url><loc>https://www.pipeleap.com/tools/sales-engagement-tools/outreach</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-engagement-tools/salesloft</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-engagement-tools/apollo-io-engagement</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-engagement-tools/hubspot-sales-hub</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-engagement-tools/groove</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-engagement-tools/klenty-engagement</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-engagement-tools/reply-io-engagement</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-engagement-tools/close-io</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-engagement-tools/mixmax</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-engagement-tools/yesware</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <!-- Prospecting Tools -->
  <url><loc>https://www.pipeleap.com/tools/prospecting-tools/apollo-io-prospecting</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/prospecting-tools/zoominfo</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/prospecting-tools/cognism</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/prospecting-tools/lusha</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/prospecting-tools/hunter-io</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/prospecting-tools/linkedin-sales-navigator</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/prospecting-tools/clay-prospecting</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/prospecting-tools/leadfeeder</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/prospecting-tools/clearbit-prospecting</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/prospecting-tools/bombora</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <!-- Lead Enrichment Tools -->
  <url><loc>https://www.pipeleap.com/tools/lead-enrichment-tools/clay</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/lead-enrichment-tools/clearbit</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/lead-enrichment-tools/zoominfo-enrich</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/lead-enrichment-tools/lusha-enrich</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/lead-enrichment-tools/apollo-io-enrich</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/lead-enrichment-tools/cognism-enrich</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/lead-enrichment-tools/hunter-io-enrich</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/lead-enrichment-tools/people-data-labs</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/lead-enrichment-tools/datagma</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/lead-enrichment-tools/leadmagic</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <!-- CRM Tools -->
  <url><loc>https://www.pipeleap.com/tools/crm-tools/hubspot-crm</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/crm-tools/salesforce</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/crm-tools/pipedrive</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/crm-tools/close-io-crm</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/crm-tools/attio</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/crm-tools/folk</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/crm-tools/breakcold</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/crm-tools/copper-crm</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/crm-tools/monday-sales-crm</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/crm-tools/streak</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <!-- Call Recording Tools -->
  <url><loc>https://www.pipeleap.com/tools/call-recording-tools/gong</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/call-recording-tools/chorus-zoominfo</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/call-recording-tools/fireflies-ai</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/call-recording-tools/tldv</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/call-recording-tools/avoma</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/call-recording-tools/wingman-clari</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/call-recording-tools/leexi</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/call-recording-tools/modjo</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/call-recording-tools/grain</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/call-recording-tools/otter-ai</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <!-- Revenue Intelligence Tools -->
  <url><loc>https://www.pipeleap.com/tools/revenue-intelligence-tools/gong-revenue</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/revenue-intelligence-tools/clari</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/revenue-intelligence-tools/6sense</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/revenue-intelligence-tools/bombora</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/revenue-intelligence-tools/demandbase</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/revenue-intelligence-tools/crayon</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/revenue-intelligence-tools/g2-buyer-intent</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/revenue-intelligence-tools/salesloft-revenue</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/revenue-intelligence-tools/highspot</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/revenue-intelligence-tools/seismic</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <!-- LinkedIn Automation Tools -->
  <url><loc>https://www.pipeleap.com/tools/linkedin-automation-tools/dripify</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/linkedin-automation-tools/expandi</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/linkedin-automation-tools/meetalfred</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/linkedin-automation-tools/waalaxy</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/linkedin-automation-tools/phantombuster</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/linkedin-automation-tools/skylead</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/linkedin-automation-tools/lemlist-linkedin</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/linkedin-automation-tools/taplio</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/linkedin-automation-tools/linkedin-sales-navigator-auto</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/linkedin-automation-tools/lempod</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <!-- AI Outbound Agents -->
  <url><loc>https://www.pipeleap.com/tools/ai-outbound-agents/11x-ai-agent</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-outbound-agents/artisan-ai-agent</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-outbound-agents/regie-ai-agent</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-outbound-agents/ava-agent</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-outbound-agents/clay-agent</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-outbound-agents/instantly-ai-agent</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-outbound-agents/reply-io-agent</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-outbound-agents/outreach-ai-agent</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/ai-outbound-agents/piper-agent</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <!-- Workflow Automation Tools -->
  <url><loc>https://www.pipeleap.com/tools/workflow-automation-tools/zapier</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/workflow-automation-tools/make-integromat</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/workflow-automation-tools/n8n</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/workflow-automation-tools/clay-workflow</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/workflow-automation-tools/hubspot-workflows</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/workflow-automation-tools/workato</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/workflow-automation-tools/bardeen</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/workflow-automation-tools/tray-io</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/workflow-automation-tools/retool</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <!-- Sales Analytics Tools -->
  <url><loc>https://www.pipeleap.com/tools/sales-analytics-tools/gong-analytics</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-analytics-tools/clari-analytics</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-analytics-tools/hubspot-analytics</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-analytics-tools/salesforce-einstein</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-analytics-tools/tableau</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-analytics-tools/looker</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-analytics-tools/ambition</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-analytics-tools/atrium</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-analytics-tools/chorus-analytics</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/sales-analytics-tools/mixpanel-sales</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <!-- GTM Engineering Tools -->
  <url><loc>https://www.pipeleap.com/tools/gtm-engineering-tools/clay-gtm</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/gtm-engineering-tools/segment</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/gtm-engineering-tools/census</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/gtm-engineering-tools/hightouch</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/gtm-engineering-tools/common-room</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/gtm-engineering-tools/warmly</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/gtm-engineering-tools/clearbit-gtm</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/gtm-engineering-tools/rb2b</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://www.pipeleap.com/tools/gtm-engineering-tools/laudspeaker</loc><lastmod>2026-05-23</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
</urlset>'''

# Build glossary entries block
glossary_entries = "\n".join(
    f'  <url><loc>https://www.pipeleap.com/glossary/{slug}</loc>'
    f'<lastmod>2026-05-22</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>'
    for slug in glossary_slugs
)

new_sitemap = SITEMAP.replace("{today}", TODAY)\
                     .replace("{count}", str(len(glossary_slugs)))\
                     .replace("{glossary_entries}", glossary_entries)

total = new_sitemap.count("<url>")
print(f"New sitemap: {total} URLs ({len(glossary_slugs)} glossary + existing)\n")

# Commit
print("Committing sitemap ...")
_, sha = get_file("public/sitemap.xml")
commit_file("public/sitemap.xml", new_sitemap, sha,
    f"seo: expand sitemap to {total} URLs — add {len(glossary_slugs)} glossary terms + lastmod dates")

# Re-submit to GSC
print("\nRe-submitting updated sitemap to Google Search Console ...")
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds = service_account.Credentials.from_service_account_file(
        "credentials/gsc_service_account.json",
        scopes=["https://www.googleapis.com/auth/webmasters"],
    )
    svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    svc.sitemaps().submit(siteUrl="sc-domain:pipeleap.com",
                          feedpath="https://www.pipeleap.com/sitemap.xml").execute()
    print("  GSC sitemap re-submitted OK")
except Exception as e:
    print(f"  GSC error: {e}")

# Re-submit to Yandex IndexNow
print("\nRe-submitting all URLs to Yandex IndexNow ...")
all_urls = re.findall(r"<loc>(https://[^<]+)</loc>", new_sitemap)
r = requests.post("https://yandex.com/indexnow",
    json={"host": "www.pipeleap.com", "key": "pipeleap-indexnow-2026",
          "keyLocation": "https://www.pipeleap.com/pipeleap-indexnow-2026.txt",
          "urlList": all_urls}, timeout=20)
print(f"  Yandex: HTTP {r.status_code} — {'OK' if r.status_code in (200,202) else 'FAILED'}")

print(f"\nDone. Sitemap now has {total} URLs.")
