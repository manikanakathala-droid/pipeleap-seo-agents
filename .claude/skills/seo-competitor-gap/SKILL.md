---
name: seo-competitor-gap
description: >-
  Competitor and SERP gap analysis for www.pipeleap.com: identifies who ranks for the searches
  Pipeleap's buyers make (direct competitors in sales productivity and sales stack tools, plus the
  publishers and review sites that own the results), studies what their ranking pages do, and lists
  the topics, page types and links Pipeleap is missing. Use whenever the user mentions competitors,
  "who ranks for X", "why do they outrank us", comparison or alternatives pages, SERP analysis,
  content gaps or backlink gaps, even if they don't use the word "gap".
---

# Competitor and SERP gap analysis

Read `.claude/skills/pipeleap-seo/references/business-context.md` and `guardrails.md` first. Use `seo-work/keywords/keyword-map.csv` if it exists. Without it, do a quick keyword pass first (or run `seo-keyword-research`), because "competitor" in SEO means whoever ranks for our buyers' searches, not just companies that sell something similar.

## Step 1: Two kinds of competitor

1. **Business competitors**: products a sales leader might buy instead of, or alongside, Pipeleap. Find them by searching the category and problem keywords, plus "alternatives to X" and review-site category pages (G2, Capterra). Likely groups: sales productivity overlays and CRM assistants, revenue intelligence and forecasting tools, sales performance management and rep visibility tools (rep scorecards, activity and time analytics, conversation intelligence; coaching platforms are adjacent, not direct competitors, since Pipeleap doesn't coach), sales engagement platforms, and AI SDR or agent tools. Cover all three buyer intents in business-context.md (productivity, revenue, rep performance): the revenue and performance searches are often owned by different companies and publishers than the productivity ones. Confirm each with its own website; don't rely on memory, because this market changes monthly.
2. **Search competitors**: whoever holds the top 10 for our top 20 clusters, including review sites, publishers, agencies and CRM vendor blogs. These set the bar a new page must beat.

Keep 5 to 8 business competitors and note the 5 domains that show up most often in the results.

For the **admin vs selling time** topic (the one Pipeleap should own, see business-context.md), always study who ranks for the main searches and what they offer (surveys, calculators, guides), because beating them is the top content goal.

## Step 2: Study the results for each top cluster

For each of the top 10 to 15 clusters in the keyword map, search the primary keyword and open the top 3 to 5 organic results. Record:
- page type and format (listicle, product page, guide, comparison, calculator)
- the angle and the questions it answers
- roughly how deep it goes (sections, word count, original data, visuals, tools)
- freshness (date shown)
- what it misses that Pipeleap can genuinely offer: the "tools you already own" angle, small-team focus, measured selling time, rep approval and control, bring-your-own AI key

That last column is the reason to make a page at all. If there's no real angle, mark the cluster "skip for now".

## Step 3: Study the competitors' sites

For each business competitor, from their public pages:
- which solution, use-case, persona and comparison pages they have (look at the navigation, footer and sitemap.xml)
- whether they run "X vs Y" or "alternatives" pages, and which competitors they target
- the resources that seem to earn links: reports, benchmarks, templates, calculators
- where they are listed: G2 and Capterra categories, integration marketplaces, directories (these become link-building prospects)

Backlink counts need a paid tool. If the user has Ahrefs or Semrush, ask for a referring-domains export and compare. Otherwise note the visible link sources instead and don't guess numbers.

## Step 4: Write the gap list

Save `seo-work/competitors/competitors.md` (one short profile per competitor, with the date and source links) and `seo-work/competitors/gaps.md`, laid out like this:

```markdown
# Gap analysis, <date>

## Content gaps (ranked by expected meetings)
| Cluster | Who ranks now | What they miss | Pipeleap page to build | Page type | Priority |

## Comparison and alternatives opportunities
<Which "X alternatives" / "X vs Y" pages are worth making, and why it's credible for Pipeleap to make them>

## Link gaps
<Directories, review sites, marketplaces and publications that list competitors but not Pipeleap>

## Positioning notes
<How competitors describe themselves, and where Pipeleap's message is different and clearer>
```

Comparison pages must follow the guardrails: fair, sourced from the competitor's own public pages, dated, and only claiming what Pipeleap really does. Since Pipeleap works on top of existing tools, "works with X" or "get more from X" angles are often more honest and convert better than "X alternative".

Hand the content gaps to `seo-content`, the link gaps to `seo-link-building`, and update `seo-work/keywords/keyword-map.csv` with new clusters found.
