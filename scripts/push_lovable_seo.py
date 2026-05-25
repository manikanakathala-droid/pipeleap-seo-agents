"""
One-shot script — adds JSON-LD schema to 5 Lovable pages that were missing it.
Pages: Results, GTMAudit, Pricing, About, Contact.
Commits each file directly to the Lovable GitHub repo via the Contents API.
"""
import base64, json, os, sys
import requests

TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO  = "manikanakathala-droid/pipeleap-launchpad-040053e5"
BRANCH = "main"
API = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def get_file(path):
    r = requests.get(f"{API}/repos/{REPO}/contents/{path}", headers=HEADERS, params={"ref": BRANCH})
    r.raise_for_status()
    data = r.json()
    return base64.b64decode(data["content"]).decode("utf-8"), data["sha"]


def commit_file(path, content, sha, message):
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "sha": sha,
        "branch": BRANCH,
    }
    r = requests.put(f"{API}/repos/{REPO}/contents/{path}", headers=HEADERS, json=payload)
    if r.status_code in (200, 201):
        print(f"  [OK] {path}")
        return True
    print(f"  [FAIL] {path}: {r.status_code} {r.text[:120]}")
    return False


# ── Patches ──────────────────────────────────────────────────────────────────

PATCHES = [
    # ── Results.tsx ──────────────────────────────────────────────────────────
    {
        "path": "src/pages/Results.tsx",
        "message": "seo: add WebPage + BreadcrumbList schema to /results",
        "find": '''      <SEO
        title="B2B Outbound Sales Results & Case Studies"
        description="Real B2B outbound sales results: 3× more meetings, 2–4× pipeline growth, and 30% higher reply rates. See how Pipeleap's automation drives revenue."
        path="/results"
      />''',
        "replace": '''      <SEO
        title="B2B Outbound Sales Results & Case Studies"
        description="Real B2B outbound sales results: 3x more meetings, 2-4x pipeline growth, and 30% higher reply rates. See how Pipeleap automation drives revenue."
        path="/results"
        jsonLd={[
          {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "url": "https://www.pipeleap.com/results",
            "name": "B2B Outbound Sales Results & Case Studies | Pipeleap",
            "description": "Real outbound automation results: 3x meetings booked, 2.5x pipeline growth, 45% improvement in reply rates within 90 days.",
            "breadcrumb": {
              "@type": "BreadcrumbList",
              "itemListElement": [
                { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.pipeleap.com" },
                { "@type": "ListItem", "position": 2, "name": "Results", "item": "https://www.pipeleap.com/results" }
              ]
            }
          }
        ]}
      />''',
    },

    # ── GTMAudit.tsx ─────────────────────────────────────────────────────────
    {
        "path": "src/pages/GTMAudit.tsx",
        "message": "seo: add Service schema (free offer) to /gtm-audit",
        "find": '''      <SEO
        title="Free GTM Audit for Outbound Sales"
        description="Get a free GTM audit for your outbound sales process. Pipeleap identifies pipeline bottlenecks and recommends automation strategies to scale revenue."
        path="/gtm-audit"
      />''',
        "replace": '''      <SEO
        title="Free GTM Audit for Outbound Sales"
        description="Get a free GTM audit for your outbound sales process. Pipeleap identifies pipeline bottlenecks and recommends automation strategies to scale revenue."
        path="/gtm-audit"
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "Service",
          "name": "Free GTM Automation Audit",
          "provider": { "@type": "Organization", "name": "Pipeleap", "url": "https://www.pipeleap.com" },
          "description": "A complimentary 20-minute audit examining outbound workflow efficiency, lead sourcing, campaigns, CRM configuration, and automation opportunities. Deliverables include workflow assessment, pipeline problem identification, automation roadmap, and tech stack recommendations.",
          "url": "https://www.pipeleap.com/gtm-audit",
          "areaServed": "Worldwide",
          "serviceType": "GTM Automation Consulting",
          "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" }
        }}
      />''',
    },

    # ── Pricing.tsx ──────────────────────────────────────────────────────────
    {
        "path": "src/pages/Pricing.tsx",
        "message": "seo: add PriceSpecification schema to /pricing",
        "find": "import Navbar from \"@/components/layout/Navbar\";\nimport Footer from \"@/components/layout/Footer\";\nimport SEO from \"@/components/SEO\";\nimport PricingTiers from \"@/components/pricing/PricingTiers\";\n\nconst Pricing = () => {\n  return (\n    <div className=\"min-h-screen\">\n      <SEO\n        title=\"Sales Automation Pricing | Pipeleap\"\n        description=\"Pipeleap pricing for outbound sales automation. Done-for-you outbound engine - lead intelligence, sequences, and pipeline generation for B2B revenue teams.\"\n        path=\"/pricing\"\n      />",
        "replace": '''import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import SEO from "@/components/SEO";
import PricingTiers from "@/components/pricing/PricingTiers";

const pricingJsonLd = {
  "@context": "https://schema.org",
  "@type": "WebPage",
  "url": "https://www.pipeleap.com/pricing",
  "name": "Sales Automation Pricing | Pipeleap",
  "description": "Pipeleap pricing: Starter from $2,500, Growth from $5,000, Advanced from $10,000. Outbound automation systems built and managed for B2B SaaS teams.",
  "mainEntity": [
    { "@type": "Offer", "name": "Starter", "price": "2500", "priceCurrency": "USD", "description": "Outbound automation for early-stage SaaS teams" },
    { "@type": "Offer", "name": "Growth", "price": "5000", "priceCurrency": "USD", "description": "Full outbound workflow system for scaling SaaS teams" },
    { "@type": "Offer", "name": "Advanced", "price": "10000", "priceCurrency": "USD", "description": "Enterprise outbound orchestration for mature revenue teams" }
  ]
};

const Pricing = () => {
  return (
    <div className="min-h-screen">
      <SEO
        title="Sales Automation Pricing | Pipeleap"
        description="Pipeleap pricing for outbound sales automation. Done-for-you outbound engine - lead intelligence, sequences, and pipeline generation for B2B revenue teams."
        path="/pricing"
        jsonLd={pricingJsonLd}
      />''',
    },

    # ── About.tsx ────────────────────────────────────────────────────────────
    {
        "path": "src/pages/About.tsx",
        "message": "seo: add Person + Organization schema to /about",
        "find": '''      <SEO
        title="About Pipeleap - Sales Orchestration That Learns"
        description="Pipeleap deploys your entire outbound system: eleven connected modules, built and operated for you. One working outbound engine."
        path="/about"
      />''',
        "replace": '''      <SEO
        title="About Pipeleap - Sales Orchestration That Learns"
        description="Pipeleap deploys your entire outbound system: eleven connected modules, built and operated for you. One working outbound engine."
        path="/about"
        jsonLd={[
          {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "url": "https://www.pipeleap.com/about",
            "name": "About Pipeleap - GTM Implementation Partner"
          },
          {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": "Rajeev Manik",
            "jobTitle": "GTM Partner",
            "worksFor": { "@type": "Organization", "name": "Pipeleap", "url": "https://www.pipeleap.com" },
            "url": "https://www.pipeleap.com/about",
            "sameAs": ["https://www.linkedin.com/company/pipeleap-com"]
          },
          {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Pipeleap",
            "url": "https://www.pipeleap.com",
            "foundingDate": "2024",
            "description": "GTM implementation partner that designs and automates outbound sales workflows for B2B SaaS teams.",
            "contactPoint": { "@type": "ContactPoint", "contactType": "sales", "email": "info@pipeleap.com" }
          }
        ]}
      />''',
    },

    # ── Contact.tsx ──────────────────────────────────────────────────────────
    {
        "path": "src/pages/Contact.tsx",
        "message": "seo: add ContactPage schema to /contact",
        "find": '''      <SEO
        title="Contact Pipeleap - Book a Strategy Call"
        description="Book a strategy call with Pipeleap. Discuss how outbound sales automation and GTM implementation can accelerate your pipeline and revenue growth."
        path="/contact"
      />''',
        "replace": '''      <SEO
        title="Contact Pipeleap - Book a Strategy Call"
        description="Book a strategy call with Pipeleap. Discuss how outbound sales automation and GTM implementation can accelerate your pipeline and revenue growth."
        path="/contact"
        jsonLd={{
          "@context": "https://schema.org",
          "@type": "ContactPage",
          "url": "https://www.pipeleap.com/contact",
          "name": "Contact Pipeleap",
          "description": "Contact Pipeleap to book a strategy call or discuss your outbound automation setup.",
          "mainEntity": {
            "@type": "Organization",
            "name": "Pipeleap",
            "email": "info@pipeleap.com",
            "url": "https://www.pipeleap.com",
            "contactPoint": {
              "@type": "ContactPoint",
              "contactType": "sales",
              "email": "info@pipeleap.com",
              "url": "https://cal.com/pipeleap/15min"
            }
          }
        }}
      />''',
    },
]


def main():
    print(f"Pushing SEO schema to {REPO} ...\n")
    ok = 0
    for patch in PATCHES:
        path = patch["path"]
        print(f"Processing {path} ...")
        try:
            content, sha = get_file(path)
        except Exception as e:
            print(f"  [SKIP] Could not fetch {path}: {e}")
            continue

        if patch["find"] not in content:
            # Try a relaxed match for the SEO block in case of minor whitespace diffs
            print(f"  [WARN] Exact match not found in {path} — skipping to avoid corruption")
            continue

        new_content = content.replace(patch["find"], patch["replace"], 1)
        if commit_file(path, new_content, sha, patch["message"]):
            ok += 1

    print(f"\nDone: {ok}/{len(PATCHES)} files updated.")


if __name__ == "__main__":
    main()
