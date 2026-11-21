# Pipeleap SEO plan: 90 days (2026-11-20 to 2027-02-18)

Status: **draft for the user's approval.** Nothing here goes live without a yes; site changes come as pull requests.

## Baseline (2026-11-20)

| Measure | Now | Source |
|---|---|---|
| Google clicks / impressions, last 28 days | 1 / 9 | Search Console |
| Branded "pipeleap": position for own name | Not in the top 10 (4 impressions, 0 clicks) | Web search, Search Console |
| Indexed pages (live site) | 4 live pages; old URLs still dropping out | Search Console |
| Referring domains | 0 known | — |
| Walkthroughs booked from organic | Not measurable yet: `book_walkthrough` isn't a GA4 key event | GA4 |
| Mobile PageSpeed (home) | 91 perf, 100 accessibility / best practices / SEO | pagespeed.web.dev |
| AI assistants mentioning Pipeleap | Not measured yet | — |

Honest starting point: the site is technically healthy and fast, but Google doesn't yet recognise "Pipeleap" as a brand and the site has four pages, none written for what buyers search. The first 90 days are about **becoming findable by name, owning the admin vs selling time topic, and earning the first links**.

## 90-day targets

| Target | By |
|---|---|
| "pipeleap" returns www.pipeleap.com first on Google and Bing | Day 45 |
| 5 official profiles live with identical facts (LinkedIn, Crunchbase, G2, Capterra, founder LinkedIn) | Day 30 |
| 8+ referring domains (directories plus 2–3 editorial) | Day 90 |
| Admin vs selling time guide and calculator live and indexed | Day 45 |
| 4 new search pages live (see content calendar) | Day 90 |
| Non-branded impressions growing month on month; first non-branded clicks | Day 90 |
| First walkthrough booked that started from organic search | Day 90 (stretch) |

Rankings for competitive terms take longer than 90 days for a new domain with no links; the plan is built so the early work (brand, trust, cornerstone asset, links) is what makes later ranking possible.

## Priority 1: measurement and brand (weeks 1–3)

| # | Task | Who | Skill |
|---|---|---|---|
| 1 | ~~Mark `book_walkthrough` as a GA4 key event~~ **Done 2026-11-21** | Claude (approved) | measurement |
| 2 | Add "How did you hear about us?" with a "Google / search" option to the Apollo booking form | **User** | measurement |
| 3 | ~~Noindex app.pipeleap.com~~ **Done 2026-11-21**: pipeleap-frontend PR #32 (meta robots, X-Robots-Tag, robots.txt allowing crawl); live | Claude (approved) | technical audit |
| 4 | Fill the **NEEDED** facts in `seo-work/brand/entity.md` (logo, founding year, HQ, founder name, role, LinkedIn, background) | **User** | brand-trust |
| 5 | Create LinkedIn company page, Crunchbase, G2, Capterra (copy prepared from entity.md) | **User** creates accounts | brand-trust, link-building |
| 6 | On-page PR #1 (site): homepage meta description; titles and descriptions for /pilot and policy pages; og:image on all pages (needs a 1200×630 image); twitter:card; text for the icon-only links; a link home and booking CTA on the 404 page; `/llms.txt`; Organization schema with logo, email, founder and sameAs | **Done 2026-11-21** (Pipeleap-web-redesign PR #9, live; IndexNow sent, homepage recrawl requested). og:image added 2026-11-21 (site PR #10, live). Still open: sameAs (needs profiles) | on-page, ai-visibility |
| 7 | Homepage H1 and section headings: propose an H1 that says what Pipeleap is in the buyer's words (for example "Pipeleap: less admin, more selling time for your sales team") and H2s in buyers' words. **Brand decision** — show before/after, ask first | H1 **done 2026-11-21**: "The sales productivity platform that gives your reps more selling time" (user chose option A; wordmark kept as visual). Section H2s still to propose | on-page |
| 8 | Run the AI assistant prompt panel for the first time (baseline) | Claude via the user's Chrome | ai-visibility |

## Priority 2: own admin vs selling time (weeks 2–7)

| # | Task | Notes |
|---|---|---|
| 9 | Brief → page: `/admin-vs-selling-time` cornerstone guide (hub) | Beats current results by explaining why published figures conflict (28% to 39% depending on definition), giving a one-week method to measure your own team, and linking time to conversations, pipeline and velocity. Named author byline (founder) |
| 10 | Brief → page: `/selling-time-calculator` | Unlike existing calculators (Skipcall, Attio, Vablet, ClickUp), converts recovered hours into conversations and pipeline; inputs and assumptions visible; estimates labelled |
| 11 | Outreach for the guide and calculator: journalist and expert requests, sales/RevOps newsletters, resource pages that cite selling-time statistics | Drafts for the user to send |

## Priority 3: trust pages (weeks 3–6)

| # | Task | Notes |
|---|---|---|
| 12 | `/about`: why Pipeleap exists, founder, location, pilot stage, contact | Needs the `/about` → `/` redirect removed from `vercel.json` (**needs a yes**) and the entity facts |
| 13 | `/security`: data flow, CRM as source of truth, bring-your-own AI key, roles, spend caps, reps approve everything | Only true facts; for finance and IT approvers |

## Priority 4: buying and problem pages (weeks 6–13)

See the content calendar. Each starts with a brief for approval.

## Content calendar

| Month | Page | Primary keyword | Type | Persona | Success measure |
|---|---|---|---|---|---|
| Dec 2026 | `/admin-vs-selling-time` | how much time do sales reps spend selling | Cornerstone guide | Senior sales leadership | Indexed; impressions for the cluster in 4 weeks; first links |
| Dec 2026 | `/selling-time-calculator` | selling time calculator | Calculator | Senior sales leadership, executive | Used by visitors; linked from outreach |
| Jan 2027 | `/about` and `/security` | pipeleap (brand) | Trust pages | All; finance and IT | Brand results; sitelinks |
| Jan 2027 | `/too-many-sales-tools` | too many sales tools / sales tool sprawl | Problem page | Sales operations transformation | Impressions; CTA clicks |
| Feb 2027 | `/sales-productivity-software` | sales productivity software for small teams | Solution page | Senior sales leadership | Impressions; CTA clicks |
| Feb 2027 | `/sales-team-performance-dashboard` | sales team performance dashboard (+ how to know which sales reps need help, sales rep kpis) | Problem/solution page | Sales management | Impressions; CTA clicks |

Then (quarter 2): `/sales-velocity` guide (with revenue-without-hiring as a section), `/revops-automation`, and the first "get more from <tool>" pages once integrations are confirmed. Page priorities come from `seo-work/keywords/keyword-map.csv` (summed priority: admin vs selling time 27, sales productivity software 19, performance dashboard 19, too many tools 18, sales velocity 17).

## Site structure

Hub 1 (first): **admin vs selling time** — `/admin-vs-selling-time` with the calculator, the reps-need-help page and later guides linking to it. Hubs for stack optimization and revenue/velocity follow once each has three pages. New pages at `/<slug>`; nothing under `/blog/`, `/glossary/` or `/tools/`. Navigation changes proposed when a hub has three pages.

## Link building

Week 1–4: directory foundations (`seo-work/backlinks/prospects.csv`: LinkedIn, Crunchbase, G2, Capterra, TrustRadius, SaaSHub, Product Hunt launch plan). From week 4: weekly batch of ~10 prospects and 5 drafts, focused on the selling-time guide and calculator.

## Waiting on the user

- [ ] Approve this plan (or change it)
- [x] GA4: star `book_walkthrough` as a key event
- [ ] Apollo booking form: "How did you hear about us?"
- [x] Yes/no: noindex app.pipeleap.com (yes, done)
- [ ] Fill the NEEDED facts in `seo-work/brand/entity.md`
- [ ] Create LinkedIn company page, Crunchbase, G2, Capterra
- [x] A 1200×630 share image (og:image): designed by Claude in the site style, live at /assets/og-image.png
- [ ] Yes/no: remove the `/about` redirect so an About page can be built
- [x] Decide on the homepage H1 proposal (task 7): option A, live
- [ ] Optional: PAGESPEED_API_KEY for automated speed checks; re-add the Search Console service account to the `pipeleap.com` property for API access

## Search engine updates log

| Dates | Update | Notes |
|---|---|---|
| | | (weekly routine fills this in) |

## Change log

- 2026-11-20: Foundation phase run. Audit `seo-work/audits/2026-11-20.md`, keywords `seo-work/keywords/`, gaps `seo-work/competitors/gaps.md`, brand `seo-work/brand/`.
- 2026-11-21: GA4 key event set; app.pipeleap.com noindexed (frontend PR #32); on-page fixes live (site PR #9: H1, meta, 404 page, llms.txt); IndexNow sent; homepage recrawl requested. Interactive sessions may now merge after a preview check (guardrails).
- 2026-11-21: Share image (og:image, large Twitter card) live on all pages (site PR #10).
- 2026-11-21: Share image redesigned (site PR #11): ends on the homepage wordmark; animated MP4/GIF at /assets/pipeleap-share.mp4 and .gif for posts. Source in seo-work/brand/share-image/.
