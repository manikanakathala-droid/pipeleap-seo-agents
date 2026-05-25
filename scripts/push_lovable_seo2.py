"""
Round 2 fixes:
1. Blog.tsx — add CollectionPage JSON-LD to /blog index
2. Index.tsx — add SoftwareApplication schema alongside existing Organization + WebSite
"""
import base64, os, requests

TOKEN  = os.getenv("GITHUB_TOKEN", "")
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

PATCHES = [
    # ── 1. Blog index — add CollectionPage JSON-LD ───────────────────────────
    {
        "path": "src/pages/Blog.tsx",
        "message": "seo: add CollectionPage schema to /blog index",
        "find": (
            "const Blog = () => {\n"
            "  const [activeCategory, setActiveCategory] = useState<string | null>(null);\n"
            "\n"
            "  const filtered = activeCategory\n"
            "    ? allArticles.filter((a) => a.category === activeCategory)\n"
            "    : allArticles;\n"
            "\n"
            "  return (\n"
            "    <div className=\"min-h-screen\">\n"
            "      <SEO\n"
            "        title=\"Sales Automation Blog | Pipeleap\"\n"
            "        description=\"How-to guides, playbooks, and insights on sales workflow automation, RevOps, outbound sales automation, and pipeline generation for B2B revenue teams.\"\n"
            "        path=\"/blog\"\n"
            "      />"
        ),
        "replace": (
            "const blogJsonLd = [\n"
            "  {\n"
            "    \"@context\": \"https://schema.org\",\n"
            "    \"@type\": \"CollectionPage\",\n"
            "    \"name\": \"Sales Automation Blog | Pipeleap\",\n"
            "    \"description\": \"How-to guides, playbooks, and insights on sales workflow automation, RevOps, outbound sales automation, and pipeline generation for B2B revenue teams.\",\n"
            "    \"url\": \"https://www.pipeleap.com/blog\",\n"
            "    \"publisher\": { \"@type\": \"Organization\", \"name\": \"Pipeleap\", \"url\": \"https://www.pipeleap.com\" },\n"
            "    \"breadcrumb\": {\n"
            "      \"@type\": \"BreadcrumbList\",\n"
            "      \"itemListElement\": [\n"
            "        { \"@type\": \"ListItem\", \"position\": 1, \"name\": \"Home\", \"item\": \"https://www.pipeleap.com\" },\n"
            "        { \"@type\": \"ListItem\", \"position\": 2, \"name\": \"Blog\", \"item\": \"https://www.pipeleap.com/blog\" }\n"
            "      ]\n"
            "    }\n"
            "  }\n"
            "];\n"
            "\n"
            "const Blog = () => {\n"
            "  const [activeCategory, setActiveCategory] = useState<string | null>(null);\n"
            "\n"
            "  const filtered = activeCategory\n"
            "    ? allArticles.filter((a) => a.category === activeCategory)\n"
            "    : allArticles;\n"
            "\n"
            "  return (\n"
            "    <div className=\"min-h-screen\">\n"
            "      <SEO\n"
            "        title=\"Sales Automation Blog | Pipeleap\"\n"
            "        description=\"How-to guides, playbooks, and insights on sales workflow automation, RevOps, outbound sales automation, and pipeline generation for B2B revenue teams.\"\n"
            "        path=\"/blog\"\n"
            "        jsonLd={blogJsonLd}\n"
            "      />"
        ),
    },

    # ── 2. Index.tsx — add SoftwareApplication to existing jsonLd array ───────
    {
        "path": "src/pages/Index.tsx",
        "message": "seo: add SoftwareApplication schema to homepage",
        "find": (
            '          {\n'
            '            "@context": "https://schema.org",\n'
            '            "@type": "WebSite",\n'
            '            "@id": "https://www.pipeleap.com/#website",\n'
            '            "name": "Pipeleap",\n'
            '            "url": "https://www.pipeleap.com",\n'
            '            "potentialAction": {\n'
            '              "@type": "SearchAction",\n'
            '              "target": {\n'
            '                "@type": "EntryPoint",\n'
            '                "urlTemplate": "https://www.pipeleap.com/blog?q={search_term_string}"\n'
            '              },\n'
            '              "query-input": "required name=search_term_string"\n'
            '            }\n'
            '          }\n'
            '        ]}'
        ),
        "replace": (
            '          {\n'
            '            "@context": "https://schema.org",\n'
            '            "@type": "WebSite",\n'
            '            "@id": "https://www.pipeleap.com/#website",\n'
            '            "name": "Pipeleap",\n'
            '            "url": "https://www.pipeleap.com",\n'
            '            "potentialAction": {\n'
            '              "@type": "SearchAction",\n'
            '              "target": {\n'
            '                "@type": "EntryPoint",\n'
            '                "urlTemplate": "https://www.pipeleap.com/blog?q={search_term_string}"\n'
            '              },\n'
            '              "query-input": "required name=search_term_string"\n'
            '            }\n'
            '          },\n'
            '          {\n'
            '            "@context": "https://schema.org",\n'
            '            "@type": "SoftwareApplication",\n'
            '            "name": "Pipeleap",\n'
            '            "applicationCategory": "BusinessApplication",\n'
            '            "operatingSystem": "Web",\n'
            '            "description": "Outbound sales workflow automation platform for B2B SaaS teams. Signal-based prospecting, enrichment orchestration, and CRM governance.",\n'
            '            "url": "https://www.pipeleap.com",\n'
            '            "offers": {\n'
            '              "@type": "AggregateOffer",\n'
            '              "priceCurrency": "USD",\n'
            '              "lowPrice": "2500",\n'
            '              "highPrice": "10000",\n'
            '              "offerCount": "3"\n'
            '            }\n'
            '          }\n'
            '        ]}'
        ),
    },
]

print(f"Pushing round-2 SEO fixes to {REPO} ...\n")
ok = 0
for p in PATCHES:
    print(f"Processing {p['path']} ...")
    try:
        content, sha = get_file(p["path"])
    except Exception as e:
        print(f"  [SKIP] fetch failed: {e}")
        continue
    if p["find"] not in content:
        print(f"  [WARN] exact match not found — skipping to avoid corruption")
        continue
    new_content = content.replace(p["find"], p["replace"], 1)
    if commit_file(p["path"], new_content, sha, p["message"]):
        ok += 1

print(f"\nDone: {ok}/{len(PATCHES)} files updated.")
