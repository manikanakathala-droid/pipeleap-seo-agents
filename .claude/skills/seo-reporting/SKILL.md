---
name: seo-reporting
description: >-
  SEO performance reporting for www.pipeleap.com that ties search to revenue: pulls Search Console,
  Bing Webmaster, GA4 and Apollo meeting data, and reports rankings, clicks, countries, walkthroughs
  booked, founding pilots and paid customers from organic search, with what worked, what didn't and
  what to do next. Use whenever the user asks how SEO is doing, for a monthly or weekly SEO report,
  traffic or ranking numbers, "did SEO bring any meetings", Search Console or GA4 numbers, or ROI of
  SEO.
---

# SEO reporting

Read `.claude/skills/pipeleap-seo/references/measurement.md` first; it lists every data source and how to reach it. Read `business-context.md` for the funnel.

The report answers one question first: **did organic search produce walkthroughs, pilots and customers, and is that trend going up?** Traffic and rankings come second, as explanations.

## Step 1: Gather the data

For the reporting period (default: last full calendar month, compared with the month before and, when available, the same month last year):

| Data | Source | Detail |
|---|---|---|
| Clicks, impressions, CTR, average position | Search Console | Totals, top 20 queries, top pages, by country, branded ("pipeleap") vs non-branded |
| Indexing | Search Console Pages report | Indexed count, new "not indexed" reasons |
| Bing clicks and impressions | Bing Webmaster Tools | Totals and top queries |
| Organic sessions, landing pages, `/pilot` visits | GA4 | Filter default channel group = Organic Search |
| `book_walkthrough` events from organic sessions | GA4 | Split by `cta_label` (walkthrough vs pilot) and by landing page |
| Meetings booked | Apollo (connector if connected) or the user | Count, and how many said "search" or came from organic sessions |
| Pilots started, paid customers | The user | Ask; never guess |
| Referring domains and new links | `seo-work/backlinks/prospects.csv` (status `live`) | Count new this month |
| Work shipped | `seo-work/onpage-log.csv`, published briefs, merged PRs | What changed this month |
| AI assistant visibility | `seo-work/ai-visibility/` (from `seo-ai-visibility`) | Share of buyer prompts where Pipeleap is mentioned, per assistant; GA4 referrals from chatgpt.com, perplexity.ai, gemini.google.com and copilot.microsoft.com |
| Brand search | `seo-work/brand/brand-serp.md` (from `seo-brand-trust`) and Search Console | Position for "pipeleap", branded clicks, anything wrong in the brand results |
| Target keyword positions | `seo-work/rank-tracking.csv` | See "Rank tracking" below |
| Search engine updates | `seo-work/plan.md` | Dates of any Google or Bing core or spam update during the period |

Use the API, the browser or a CSV export, in the order given in measurement.md. When a source is unavailable, say so in the report rather than leaving a silent gap.

## Rank tracking

Search Console only shows queries the site already appears for. Keep `seo-work/rank-tracking.csv` (`date,keyword,country,position,url,source`) for the top 20 to 30 keywords in the keyword map (business_potential 3 first, and every cluster with a page):
- Where Search Console has the query, use its average position for the month, by country.
- Where it doesn't, record a spot check: search the keyword (web search, or the user's Chrome with a country set and signed out) and note whether a pipeleap.com page appears in the top 50 and where. Mark these `source=spot-check`; single searches are noisy, so watch the trend over months.
- If the user has a rank-tracking tool, use its export instead.

## Step 2: Analyse

- **Funnel:** impressions → clicks → organic sessions → CTA clicks → meetings → pilots → paid, with conversion rates between steps. Find the weakest step; that's where next month's effort goes.
- **Non-branded growth:** the clearest sign SEO is reaching new buyers rather than people who already know the name.
- **Winners and losers:** queries and pages that moved most in clicks or position, and whether earlier on-page changes (onpage-log baseline vs now) worked.
- **Countries:** where impressions and clicks come from, and whether those markets book meetings.
- **Striking distance:** buying-intent queries at positions 5 to 20; hand them to `seo-on-page`.
- **Attribution:** state the rule from measurement.md and show both counts if they differ.
- **Conversion by landing page:** organic sessions, `book_walkthrough` clicks and click rate per landing page. A page with visits but few clicks goes to `seo-on-page` (conversion fixes); a page with a good rate but few visits needs ranking or links.
- **Brand:** is "pipeleap" first, and are branded searches growing (a sign that podcasts, outreach and word of mouth are working)?
- **Updates:** if a search engine update rolled out in the period, read ranking moves against its dates before calling them wins or losses.

At low volume (a new site often has single-digit clicks), don't over-read percentages: "3 clicks to 6" is not "100% growth" in any useful sense. Say what's signal and what's noise.

## Step 3: Write the report

Save `seo-work/reports/<YYYY-MM>.md`:

```markdown
# Pipeleap SEO report, <month year>

## Headline
<Two sentences: meetings and pilots from organic this month vs last, and the single most important thing that changed.>

## Pipeline from search
| | This month | Last month | Change |
| Walkthroughs booked from organic | | | |
| Pilot applications from organic | | | |
| Pilots started (user-reported) | | | |
| Paid customers (user-reported) | | | |

## Search visibility
<Clicks, impressions, CTR, position. Branded vs non-branded. Google vs Bing. Top countries.>

## What worked / what didn't
<Specific pages, queries and changes, with numbers.>

## Work shipped this month
<Pages published, pages optimized, links earned, technical fixes.>

## Next month
<Three to five actions ranked by expected meetings, each tied to the skill that will do it.>

## Data notes
<Sources, date ranges, anything missing or estimated.>
```

If the user wants to share it with a team, offer to publish the report as a page, and keep the Markdown file as the record. Then update `seo-work/plan.md` with the "Next month" actions.
