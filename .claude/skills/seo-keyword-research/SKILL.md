---
name: seo-keyword-research
description: >-
  Keyword research and keyword mapping for www.pipeleap.com: finds what sales leaders, RevOps and
  sales managers around the world type into search when they need sales productivity or sales stack
  optimization software, want to grow revenue from their sales team, lead or transform sales
  operations, oversee sales at executive level, or are worried about sales rep performance and quota
  attainment, groups the searches into topics, scores them by how likely they are to lead to a booked
  walkthrough or pilot, and maps each to an existing or new page. Use whenever the user asks about
  keywords, search terms, topics to target, search demand, "what are people searching for", content
  ideas grounded in search, or keyword research for any country, even if they don't say "keyword
  research".
---

# Keyword research and keyword map

Before starting, read `.claude/skills/pipeleap-seo/references/business-context.md` and `guardrails.md`. If `seo-work/keywords/keyword-map.csv` exists, you are refreshing it: keep the existing rows, update them, and add new ones.

A traditional team did this with seed lists, Keyword Planner, Ahrefs or Semrush and a big spreadsheet. We do the same steps with free sources, and use paid-tool data when the user has it.

## Step 1: Seeds from the buyer's head, not ours

Write 20 to 40 seed phrases across these buckets. Think about how a VP Sales or RevOps lead describes the pain before they know Pipeleap exists:

| Bucket | Why it matters | Examples |
|---|---|---|
| Category (ready to buy) | They're comparing software now | sales productivity software, sales productivity platform, sales stack optimization, sales tech stack consolidation, revenue operations platform for small teams |
| Problem (feels the pain) | Next in line to buy | reduce sales admin time, reps spend too much time on CRM, too many sales tools, sales tool sprawl, increase selling time |
| Job to be done | Specific capabilities | automate CRM data entry, automate account research, sales meeting prep, sales email reply classification, unified sales inbox |
| Comparison and alternatives | Very high intent | tools that sit on top of the CRM, alternatives to adding another sales tool, overlays like the ones in the competitor gap file |
| Revenue growth | Leaders under revenue pressure; earlier in the journey but large | increase sales revenue without hiring, increase sales capacity, improve pipeline velocity, why deals stall, improve sales forecast accuracy, more pipeline from the same team |
| Pipeline and velocity (our point of view) | Every step of the busywork → conversations → pipeline → velocity chain is a search someone makes | sales velocity, how to increase sales velocity, how to build more pipeline, how to increase sales conversations, how much time do sales reps spend selling, sales rep time management, repetitive sales tasks to automate |
| Admin vs selling time (the topic to own) | Pipeleap should be the go-to answer here; highest priority | how much time do sales reps spend selling, sales rep time spent on admin, admin vs selling time, increase selling time, non-selling activities, sales rep time audit, measure selling time, time spent on CRM updates |
| Rep performance | Managers worried about quota attainment and which reps need help | improve sales rep performance, underperforming sales reps, how to know which reps need help, sales rep KPIs, sales team performance dashboard, ramp new sales reps faster |
| Persona and role | Matches who books; cover every tier in business-context.md | Executive: CRO priorities, sales headcount ROI, revenue per rep, sales tech stack ROI. Senior leadership: VP Sales dashboard, sales director KPIs, how to scale a sales team. Management: sales manager visibility into rep activity, team performance. Transformation: sales operations transformation, sales excellence programme, sales tech stack audit, sales process automation, GTM systems consolidation |
| Measurement and ROI | Leaders justifying spend | sales tech stack ROI, cost of unused software licences, sales productivity metrics |

Include spelling variants (optimization/optimisation, licence/license) because the market is global.

## Step 2: Expand with real searches

Run the bundled script to pull Google's autocomplete suggestions for each seed in several English-speaking markets. Suggestions only appear for things people actually search, so it's a free demand signal:

```bash
python .claude/skills/seo-keyword-research/scripts/autocomplete.py \
  --seeds-file seo-work/keywords/seeds.txt \
  --countries us,gb,ca,au,in,sg,ae \
  --expand questions \
  --out seo-work/keywords/autocomplete.csv
```

`--expand questions` also tries "how to / best / tools for / vs" forms; `--expand alphabet` tries seed + a..z (slower, use for the 5 most important seeds only). Save seeds to `seo-work/keywords/seeds.txt` first, one per line.

Add other sources where available:
- **Search Console** queries the site already gets impressions for (see `pipeleap-seo/references/measurement.md`). These are proven and the cheapest wins.
- **"People also ask" and related searches**: use web search on the top 10 seeds and note the questions shown.
- **Paid tool exports**: if the user has Ahrefs, Semrush or Keyword Planner, ask for a CSV and use its volume and difficulty columns. Without one, don't invent search volumes; use the relative signals below.

## Step 3: Judge each keyword

For each candidate, look at the actual search results (web search) for the main ones, because the results show what Google thinks the intent is:

| Field | How to set it |
|---|---|
| `intent` | `buy` (software lists, vendor pages, comparisons rank), `solve` (how-to guides rank), `learn` (definitions, theory), `navigate` (a brand) |
| `business_potential` | 3 = Pipeleap is the answer, 2 = Pipeleap is a strong part of the answer, 1 = loosely related, 0 = no fit |
| `demand_signal` | high / medium / low: appears in autocomplete in several countries, has related searches, shows in Search Console, or has volume in a paid tool |
| `difficulty_signal` | low / medium / high: who ranks in the top 10? Forums, small sites and thin pages = low. G2, HubSpot, Salesforce, Gartner everywhere = high |
| `countries` | Where suggestions appeared |
| `serp_format` | What ranks: listicle, product page, guide, comparison, tool or calculator, video |

**Priority score** = business_potential × intent weight (buy 3, solve 2, learn 1, navigate 0) × demand (high 3, medium 2, low 1) ÷ difficulty (low 1, medium 2, high 3). Treat it as a sorting aid, not truth, and adjust by judgement with a note.

For revenue and performance keywords, judge business_potential by how tightly they are tied to B2B sales teams. "Increase sales team revenue without hiring" or "sales rep performance metrics" can be 2 or 3; "how to increase revenue" or "employee performance review" are 0 or 1, because the searchers are mostly small-business owners, marketers or HR. Pipeleap doesn't provide coaching: searches about coaching programmes, courses, certifications, coaching jobs or "sales coach near me" are business potential 0, and generic "sales coaching platform" searches are at most 1. Searches about knowing which reps need help, and where their time goes, fit well. Add a `persona` column (executive, senior-leadership, management, transformation, finance-it) naming the primary reader for each keyword. Tag each row with its buyer intent (`productivity`, `revenue`, `performance` or `selling-time`) in a `theme` column; `selling-time` rows get business potential 3 when they fit.

Some of our words are ambiguous on their own: "pipeline" returns DevOps and data-engineering searches, and "selling time" returns timeshare and stock-trading searches. Always qualify them with sales context ("sales pipeline", "sales rep selling time") in seeds and in page copy, and score unqualified variants 0.

Drop keywords with business_potential 0. The old site chased low-fit terms by the hundred and got nothing.

## Step 4: Cluster and map

Group keywords that one page can satisfy (same intent, same results) into a cluster. Each cluster gets one page:
- an existing page (`/` or `/pilot`) if it already fits, or
- a new page with a proposed slug and page type (solution page, problem page, comparison, guide, calculator).

One cluster, one page: two pages chasing the same cluster compete with each other.

## Output

Write `seo-work/keywords/keyword-map.csv` with columns:

```
keyword,cluster,theme,persona,intent,business_potential,demand_signal,difficulty_signal,priority_score,countries,serp_format,target_url,page_status,notes
```

`page_status` is `exists`, `optimize` or `create`. Then write `seo-work/keywords/summary.md`:
1. The top 10 clusters by priority (make sure all three themes are represented, and say if one has little demand), each with its primary keyword, the target URL and one sentence on why it should produce meetings.
2. Quick wins: keywords the site already has impressions for in positions 5 to 20.
3. Market notes by country (where demand showed up and any wording differences).
4. What data was missing (for example no volume data) and how that limits confidence.

Finish by recommending the next step, usually `seo-competitor-gap` or `seo-content` for the top cluster.
