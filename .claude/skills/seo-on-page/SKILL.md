---
name: seo-on-page
description: >-
  On-page SEO optimization of existing www.pipeleap.com pages: rewrites title tags, meta descriptions,
  H1 and H2 headings, intro copy, internal links, structured data and CTAs so a page ranks for its
  target keyword cluster and turns visitors into booked walkthroughs or pilot applications. Use
  whenever the user wants to improve, optimize or refresh a page, fix titles, descriptions or
  headings, improve click-through rate from search, push a page from page 2 to page 1, or asks why a
  specific page isn't ranking, even without the words "on-page SEO".
---

# On-page optimization

Read `.claude/skills/pipeleap-seo/references/business-context.md`, `guardrails.md` and `site-workflow.md` first. Find the page's target cluster in `seo-work/keywords/keyword-map.csv`. If the page has no cluster yet, pick one with the user before editing; optimizing for a guessed keyword wastes the change.

## Step 1: Understand the page and its competition

1. Run `python .claude/skills/seo-technical-audit/scripts/audit_site.py --url <page>` to get the current title, description, headings, schema and issues.
2. Read the page's visible text in full.
3. If Search Console data is available, note the queries the page already gets impressions for, with position and CTR. Those queries tell you what Google already associates with it.
4. Search the primary keyword and read the top 3 to 5 results: which subtopics they all cover, which questions they answer, and how their titles are phrased.

## Step 2: Plan the changes

Work through this list and write down, for each item, what should change and why:

| Element | Good practice for this site |
|---|---|
| Title tag | 30 to 60 characters. Primary keyword near the start, then a reason to click. Brand at the end ("· Pipeleap") only if there is room. Each page unique |
| Meta description | 120 to 160 characters. Restate the searcher's problem, give the specific answer and end with the next step (walkthrough or free pilot). It doesn't affect ranking directly, but it decides clicks |
| H1 | One per page, says what the page is about in the buyer's words. A brand-only or slogan-only H1 wastes the strongest on-page signal |
| H2 and H3 | Cover the subtopics the top results cover, plus Pipeleap's distinctive angle. Phrase some as the questions buyers ask |
| First 100 words | Name the problem and the keyword naturally; say who the page is for |
| Body | Answer the query better than the current top results. Add what only Pipeleap can say (works on the tools you already own, reps approve everything, measured selling time). Cut filler |
| Internal links | Link to the page from other relevant pages with descriptive anchor text, and from it to `/pilot` and to related pages |
| CTA | "Book a walkthrough" near the top for ready buyers, and "Apply for a founding pilot" after the explanation. Keep the existing `href` values so tracking works |
| Structured data | Keep it consistent with the visible content: Organization and SoftwareApplication on home, BreadcrumbList and WebPage on inner pages, FAQPage only where a visible FAQ exists |
| Social tags | `og:title`, `og:description` and `og:image` (a 1200×630 image) so links shared on LinkedIn look right |

Keep the meaning and positioning of copy you change. On-page work sharpens the message; it doesn't rewrite the product story. When a proposed change touches the homepage hero or the brand line, show the before and after and ask first, because those are brand decisions as much as SEO ones.

## Step 3: Make the changes

Follow `pipeleap-seo/references/site-workflow.md`: branch, edit, re-run the audit on the local copy, open a PR. The PR description includes a before-and-after table for the title, description, H1 and changed H2s, the target cluster, and what to check in the preview.

## Step 4: Record and follow up

Add a row to `seo-work/onpage-log.csv` (`date,url,target_keyword,change_summary,pr_link,baseline_position,baseline_ctr`). Record the baseline position and CTR from Search Console when available, so the reporting skill can judge the change 4 to 8 weeks later. After the PR merges, notify search engines (step 6 of `site-workflow.md`).

## Striking-distance mode

When asked for a "striking-distance pass" (part of the monthly calendar), pull the queries ranking in positions 5 to 20 with business_potential 2 or 3 in the keyword map. For each page involved, make the smallest change that better matches those queries: a title tweak, a new H2 section answering the query, an internal link with that anchor text. Batch them into one PR.
