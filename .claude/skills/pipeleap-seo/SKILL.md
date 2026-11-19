---
name: pipeleap-seo
description: >-
  Pipeleap's SEO playbook and operating calendar, the hub for every SEO task on www.pipeleap.com. Use
  it whenever the user asks about SEO, organic traffic, rankings, Google or Bing visibility, reaching
  teams that want more revenue or better sales rep performance, reaching sales executives, sales
  managers or sales operations and transformation leaders, "getting more visitors", "more
  demos/meetings/pilots from search", an SEO plan, roadmap or monthly SEO run, or asks "what should we
  do for SEO this week/month". It holds the business context, guardrails and measurement plan that the
  other seo-* skills rely on, and routes the work to them (keyword research, competitor gap, technical
  audit, on-page, content, link building, brand search and trust, AI search visibility, reporting).
  Also use it for questions about showing up in ChatGPT, Perplexity, Gemini or other AI assistants.
---

# Pipeleap SEO playbook

This skill set does the work a traditional SEO team did by hand (research, audits, on-page fixes, content, outreach and reporting), with Claude doing the legwork and a person approving anything that goes live or leaves the building.

The goal is not traffic for its own sake. It is **booked walkthroughs and founding pilot applications from sales teams that need what Pipeleap does**, then paid customers. We reach them through three buyer intents (detailed in `references/business-context.md`):
1. **Sales productivity and stack optimization**: too much admin, too many tools, unused licences.
2. **Revenue growth**: missing targets, thin pipeline, stalled deals, more revenue without more headcount.
3. **Sales rep performance**: reps missing quota, uneven results, managers not knowing which rep needs help or what kind. Pipeleap gives managers that visibility; it doesn't coach.

The topic Pipeleap should own outright is **admin time vs selling time**: anyone worried about how long reps spend on admin instead of selling should find Pipeleap first. It gets top content priority (see `references/business-context.md`).

The buyers are everyone from sales managers up to the executive team who oversees sales (CRO, VP Sales, CEO or founder), plus the leaders transforming sales operations (RevOps, sales operations, sales excellence and transformation). Each page targets one of these personas (see `references/business-context.md`).

All three are tied together by Pipeleap's point of view: **remove the busywork around reps, and they have more conversations, which builds more pipeline and faster sales velocity.** That chain is the argument every page, pitch and plan should make (see `references/business-context.md`).
 Every decision is judged by how directly it moves that number. A page with 50 visits a month from RevOps leads who book a call beats a page with 5,000 visits from students.

## Read these first (every time)

1. `references/business-context.md`: what Pipeleap is, who buys it, the funnel, the site and the CTAs. Every skill depends on it, and getting a fact wrong here spreads into every page.
2. `references/guardrails.md`: what we never claim, never publish without approval, and never do for links. The previous website was buried by thin mass-produced pages; these rules exist so that never happens again.

Read `references/measurement.md` when the task involves numbers, tracking or reporting, and `references/site-workflow.md` before changing anything on the website.

## Shared workspace

All skills read and write to `seo-work/` in this repository, so each job builds on the last one, the way an SEO team's shared drive did:

| Path | Owner skill | Contents |
|---|---|---|
| `seo-work/keywords/keyword-map.csv` | seo-keyword-research | Every target keyword, its cluster, intent, priority and the page it maps to |
| `seo-work/competitors/` | seo-competitor-gap | Competitor profiles and the gap list |
| `seo-work/audits/` | seo-technical-audit | Dated audit reports (`YYYY-MM-DD.md` + `.json`) |
| `seo-work/briefs/` | seo-content | One brief per page (`<slug>.md`) |
| `seo-work/backlinks/prospects.csv` | seo-link-building | Link prospects, status and outreach drafts |
| `seo-work/reports/` | seo-reporting | Monthly reports (`YYYY-MM.md`) |
| `seo-work/ai-visibility/` | seo-ai-visibility | Prompt panel, answer log and monthly AI visibility notes |
| `seo-work/brand/` | seo-brand-trust | Brand search results log, company facts (`entity.md`), profile copy |
| `seo-work/onpage-log.csv` | seo-on-page | Every page change with its baseline, for judging results later |
| `seo-work/rank-tracking.csv` | seo-reporting | Monthly positions for the target keywords, by country |
| `seo-work/plan.md` | this skill | The current 90-day plan and this month's task list |

Create a folder when it's first needed. Before starting any task, check whether earlier output exists and build on it instead of redoing it.

## Which skill for which job

| The user wants... | Use |
|---|---|
| Keywords, topics, "what do people search", search demand by country | `seo-keyword-research` |
| Who ranks instead of us, what competitors cover that we don't | `seo-competitor-gap` |
| Site health, indexing, meta tags, speed, schema, broken links | `seo-technical-audit` |
| Improve an existing page for a keyword, titles, descriptions, headings | `seo-on-page` |
| A new page, guide, comparison or article, or a content brief | `seo-content` |
| Backlinks, directories, guest posts, PR, mentions | `seo-link-building` |
| How SEO is doing, monthly report, did it produce meetings | `seo-reporting` |
| Being found and recommended by ChatGPT, Perplexity, Gemini, Copilot, Google AI Overviews | `seo-ai-visibility` |
| Searches for "pipeleap", Knowledge Panel, About page, author bios, security page, trust and E-E-A-T | `seo-brand-trust` |
| Pages losing traffic, two pages competing, refreshing or retiring old pages | `seo-on-page` (content upkeep) |
| A plan, a roadmap, "run this month's SEO" | This skill: follow the calendar below |

When a request spans several jobs, do them in the order of the calendar and say which skill each step used.

## The operating calendar

This is the rhythm an in-house SEO team keeps. When asked to "run SEO", "do this month's SEO" or "make a plan", work out where we are in it from `seo-work/` and do the next due items.

**Foundation (once, then whenever the site changes a lot)**
1. Check measurement works (`references/measurement.md`): GA4 records `book_walkthrough`, and Search Console is verified with the sitemap submitted. Without this, nothing later can be judged.
2. Technical audit of the whole site (`seo-technical-audit`).
3. Keyword research and keyword map (`seo-keyword-research`).
4. Competitor gap analysis (`seo-competitor-gap`).
5. Brand search check, company facts and trust pages plan (`seo-brand-trust`): if "pipeleap" doesn't bring up the site first, that goes to the top of the plan.
6. Write `seo-work/plan.md`: a 90-day plan listing the pages to optimize, the pages to create (highest buying intent first), the link-building targets, and the number we expect each to move.

**Every week**
- Ship one or two pieces of work from the plan: a new page (`seo-content`) or an improved page (`seo-on-page`). Two strong pages a month beat ten weak ones.
- One link-building batch: research about ten prospects and draft outreach for the user to send (`seo-link-building`).
- A quick Search Console look: new queries, pages that dropped, indexing errors. Note anything odd in `plan.md`.
- Check the Google Search Status Dashboard (status.search.google.com) and Bing's webmaster blog for core or spam updates. If one rolled out, note its dates in `plan.md` so ranking changes in the report can be read against it, and don't react to movement until the rollout has finished.

**Every month**
- Run the AI assistant prompt panel and fix the gaps (`seo-ai-visibility`).
- Monthly report (`seo-reporting`), tied to walkthroughs and pilots booked, not just clicks.
- Striking-distance pass: pages ranking in positions 5 to 20 for buying-intent queries get an on-page refresh, because moving them up is cheaper than ranking something new.
- Re-run the technical audit and fix new issues.
- Brand search check (`seo-brand-trust`, step 1).
- Content upkeep pass (`seo-on-page`, content upkeep mode): pages losing clicks, pages competing for the same query, guides due a refresh.
- Conversion review: booking-CTA click rate for each landing page (`seo-reporting`); the weakest page with real traffic gets a conversion fix (`seo-on-page`).
- Update `plan.md`: what shipped, what moved, what is next.

**Every quarter**
- Refresh keyword research and the competitor gap. Retire tactics that did not produce meetings and double down on the ones that did.
- Review the site structure (`seo-content`, site structure): are the topic hubs still the right ones, does every page sit two clicks or fewer from the homepage, does the navigation need a section yet.
- Review video (`seo-content`, video): if the search results for the top clusters show videos, plan one.

## Prioritisation rule

When choosing between tasks, rank them by expected meetings, not expected traffic:

1. Fix anything that stops pages being crawled, indexed or converting (broken CTA, noindex, missing from the sitemap), and make sure a search for "pipeleap" finds the site (`seo-brand-trust`).
   Then the **admin vs selling time** cluster: the topic Pipeleap should own.
2. Pages for searches where the person is choosing a product now: "sales productivity software", "tools to reduce sales admin", "tools to track sales rep selling time", "sales performance tools", comparisons and alternatives.
3. Pages for searches where the person has the problem and is looking for how to fix it: "reps spend too much time on CRM updates", "too many sales tools", "how to increase sales without hiring more reps", "why are my sales reps missing quota", "how to improve sales rep performance".
   Keep all three buyer intents in the mix; revenue and rep-performance searches are often bigger than the product-category ones.
4. Educational content that earns links and trust: guides, benchmarks, calculators.
5. Everything else.

## Automation

Each skill can run when asked, or on a schedule using the `schedule` skill. The intended setup is one weekly routine that runs this calendar's weekly items (and the monthly items in the first week of each month), saves its output in `seo-work/` on a branch, opens one pull request on this repository with the week's findings and drafts, and opens site pull requests for any fixes. Scheduled runs prepare work and drafts. They never merge, publish or send; a person approves those (see guardrails). Steps that need the user's signed-in browser (Search Console, GA4, AI assistant checks) are listed in the weekly PR for the next interactive session when the routine can't reach the data. The retired `growth/` loop in this repository is not part of this skill set; don't run or revive it.

## Finishing a task

End every task with:
- what was done and where the output is saved in `seo-work/`
- anything waiting on the user (a PR to review, emails to send, data only they can supply)
- the next item due on the calendar
