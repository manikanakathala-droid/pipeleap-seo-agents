---
name: seo-technical-audit
description: >-
  Technical SEO audit of www.pipeleap.com: crawls the sitemap and pages and checks indexability,
  redirects, canonical tags, titles, meta descriptions, H1/H2 structure, structured data, Open Graph
  tags, broken links, orphan pages, robots.txt, sitemap health, page speed and Core Web Vitals, then
  fixes what it can through a pull request. Use whenever the user asks for a site audit, SEO health
  check, "why isn't this page indexed", meta tags, schema, speed, Core Web Vitals, crawl errors or
  Search Console coverage problems, or before and after any site change.
---

# Technical SEO audit

Read `.claude/skills/pipeleap-seo/references/guardrails.md` first, and `site-workflow.md` before fixing anything.

A technical problem can quietly cancel every other SEO effort (a stray noindex, a broken CTA, a page missing from the sitemap), so this runs first and then monthly.

## Step 1: Crawl and check

```bash
python .claude/skills/seo-technical-audit/scripts/audit_site.py \
  --site https://www.pipeleap.com --psi \
  --out seo-work/audits/$(date +%F)
```

The script reads robots.txt and the sitemap, crawls every page it finds, and checks status codes, redirects, www and https host redirects, title and description length, H1 count, canonical tags, noindex, `lang`, the mobile viewport tag, Open Graph and Twitter tags, JSON-LD validity and required fields (and that FAQ markup matches the visible questions), images (alt text, broken, over 200 KB, old formats, missing width and height), mixed content, HSTS and nosniff headers, links with no text or generic anchor text, the custom 404 page (and soft 404s), broken internal links, orphan pages, sitemap mismatches and duplicate titles or descriptions. `--psi` adds PageSpeed Insights mobile scores (set `PAGESPEED_API_KEY` for higher limits; it works without one at low volume). It exits non-zero if it finds errors.

Use `--url <page>` to check a single page, including a local file served with `python -m http.server`.

## Step 2: Check what the script can't

- **Search Console** (browser or API, see `pipeleap-seo/references/measurement.md`): Pages report (indexed vs not indexed, and why), sitemap status, Core Web Vitals field data, manual actions, security issues. Inspect the key URLs (`/`, `/pilot` and every page in the keyword map) and note any "Discovered/Crawled – currently not indexed".
- **Bing Webmaster Tools**: same checks if access is available.
- **Rendering**: the site is static HTML, so content should be in the source. If a page builds content with JavaScript, confirm the text appears in the raw HTML.
- **Conversion path**: every page has a visible booking CTA, its `href` is the Apollo meeting link or `/pilot`, and the link works. Treat a broken CTA as the most severe issue, because it loses meetings directly.
- **AI crawlers**: robots.txt does not block OAI-SearchBot, ChatGPT-User, PerplexityBot, ClaudeBot, Claude-SearchBot, Google-Extended, Applebot or Bingbot, and `/llms.txt` exists (see `seo-ai-visibility`).
- **Old URLs**: a sample of old `/blog/`, `/glossary/` and `/tools/` URLs still returns 404 or 410, and old main pages still redirect (see `vercel.json`).
- **Structured data**: for important pages, check the JSON-LD matches the visible content (for example, the FAQ answers on the page), and run the homepage and any new page type through Google's Rich Results Test (search.google.com/test/rich-results) in the browser.
- **Accessibility basics**: headings in order (no H3 before the first H2), visible keyboard focus, enough colour contrast on CTAs, form fields with labels. Accessible pages are easier for crawlers to parse and for every buyer to use; Lighthouse's accessibility score (PageSpeed Insights) is a quick check.
- **Links pointing in**: in Search Console → Links, look for sudden bursts of links from unrelated or spammy domains. Usually ignore them (Google discounts most spam links); only consider a disavow file if there is a manual action for unnatural links, and only with the user's yes.

## Step 3: Prioritise

Group the findings:
1. **Blocks indexing or conversions**: noindex, 4xx/5xx, wrong canonical, broken CTA, robots.txt blocks, page missing from the sitemap.
2. **Weakens ranking**: missing or poor titles and descriptions, H1 problems, slow mobile LCP, missing structured data, orphan pages.
3. **Polish**: alt text, Open Graph, minor length warnings.

A length warning on a well-written title is not worth a PR on its own. Use judgement, and say why something is or isn't worth fixing.

## Step 4: Fix

For fixes in the site's HTML, `sitemap.xml`, `robots.txt` or `vercel.json`, follow `pipeleap-seo/references/site-workflow.md`: branch, edit, re-run the audit locally, open a PR. Explain each change in the PR. Anything that affects indexing (robots, canonicals, redirects, noindex) needs the user's explicit yes first (guardrails).

Fixes outside the code (Search Console settings, GA4 key events, Vercel settings) go in the report as tasks for the user, with click-by-click steps.

## Output

Save the script output in `seo-work/audits/<date>.md` and `.json`, then append a short **"Actions"** section to the Markdown: each issue, its priority, and its status (fixed in PR #n / needs user / won't fix, with the reason). Compare with the previous audit, if one exists, and call out anything new or regressed.
