---
name: seo-content
description: >-
  Plans, briefs and writes new search-driven pages for www.pipeleap.com (solution pages, problem
  pages, comparison and alternatives pages, buyer's guides, calculators) aimed at the sales buying
  group from managers to executives (CRO, VP Sales, sales directors, sales managers) and sales
  operations transformation leaders (RevOps, sales operations, sales excellence), looking for sales
  productivity and sales stack optimization software, ways to grow sales revenue, or ways to improve
  sales rep performance, each built to rank and to book walkthroughs and founding pilots. Use whenever
  the user asks for a new page, landing page, article, guide, blog post, comparison page, content
  brief, content calendar or "content to rank for X", even if they don't mention SEO.
---

# Content: brief, write, publish

Read `.claude/skills/pipeleap-seo/references/business-context.md`, `guardrails.md` and `site-workflow.md` first. Pick the topic from `seo-work/keywords/keyword-map.csv` (rows with `page_status = create`) and `seo-work/competitors/gaps.md`. If the user names a topic that isn't in the map, check it has real buying intent and business potential before writing; if it doesn't, say so and suggest a better one.

The old site published hundreds of thin pages and none of them ranked. Here, every page must be the best answer on the internet for its query and must make booking a walkthrough the obvious next step.

## Step 1: The brief

Write `seo-work/briefs/<slug>.md` before drafting. Briefs are where a traditional SEO team caught bad ideas cheaply, so keep that habit:

```markdown
# Brief: <working title>
- Primary keyword: <one>   · Secondary: <3 to 8 from the same cluster>
- Search intent: <buy / solve / learn>, and what the searcher wants to walk away with
- Reader: <one primary persona tier from business-context.md (executive, senior leadership, management, sales operations transformation, finance or IT)>, their situation in one sentence, and who else in the buying group the page must also convince
- URL: /<slug>   · Page type: <solution / problem / comparison / guide / calculator>
- What ranks now: <top 3 results, the format they use, what they miss>
- Our angle: <what this page says that the top results don't, and why Pipeleap can credibly say it>
- Outline: H1, then H2s and H3s, with one line each on what the section must do
- Proof we can use: <only facts from business-context.md and sources we have read and will link>
- Internal links: <from which existing pages, and to which>
- CTA plan: <where "Book a walkthrough" and "Apply for a founding pilot" appear>
- Title tag (≤60 chars) and meta description (120–160 chars)
- Structured data: <type>
- Success measure: <query and position target, CTA clicks per month>
```

Show the brief to the user and get a yes before writing the page, unless they have asked you to go straight through.

## Step 2: Page types that tend to convert for this product

| Type | When | Notes |
|---|---|---|
| Solution page | Category keywords ("sales productivity software for small teams") | Problem, how Pipeleap solves it, how it works, who it's for, FAQ, CTA. The closest to a sales page |
| Problem page | Pain keywords ("reps spend too much time on admin", "why sales reps miss quota", "how to grow revenue without hiring") | Diagnose the problem with specifics, show the options honestly (including doing nothing and process fixes), then where Pipeleap fits |
| Comparison or alternatives | "X vs Y", "X alternatives", "tools like X" | Fair, dated, sourced from competitors' own pages. Often the most honest angle is "use X with Pipeleap", since it works on top of existing tools |
| Buyer's guide | "how to choose…", "best … tools" | Criteria, honest options and a checklist. Include Pipeleap where it genuinely fits; don't rank it first by default |
| Calculator or tool | ROI, "cost of unused licences", "selling time lost to admin", "pipeline capacity per rep" | Earns links and captures leads. Inputs and formulas visible; assumptions labelled as estimates |

Don't put new pages under `/blog/`, `/glossary/` or `/tools/` (those paths were removed on purpose). Use `/<slug>` for solution and comparison pages, and propose a `/guides/<slug>` section only once there are at least three guides.

## Revenue and rep-performance topics

Pages for the revenue and performance intents (see business-context.md) start further from the product. Structure them as: the real causes of the problem (with honest options, including hiring, training, process and pricing fixes), then the cause that's usually missed, told through Pipeleap's point of view (busywork crowds out conversations, fewer conversations mean less pipeline and slower deals), then how Pipeleap removes that busywork. That bridge is what makes a broad page convert. Claim the mechanism, never a revenue or quota result (guardrails), and frame performance as giving managers visibility into which reps need help and what kind, never as monitoring. Pipeleap doesn't coach; the manager does, with better information.

## Writing for the persona

Match the page to its primary persona (business-context.md):
- **Executive:** lead with the business case and the point of view; short, numbers that matter at board level (with sources), the cost of doing nothing. CTA framed as seeing the numbers on their own stack.
- **Senior sales leadership:** pipeline, capacity and quota across the team; what changes for their reps and managers; the walkthrough as a working session on their setup.
- **Sales management:** their week: which reps need help and what kind, overdue work, deals that stalled. Concrete and practical.
- **Sales operations transformation:** how it works on the existing stack, data flow, CRM as source of truth, rollout with nothing to migrate, adoption, controls. They need detail an executive would skip.
- **Finance and IT:** spend on unused licences, security and AI controls. Usually a section or FAQ on another page rather than a page of its own.

## The point of view in every page

Every page, whatever its topic, should carry Pipeleap's belief at least once in plain words: remove the busywork around reps and they have more conversations, which builds more pipeline and faster sales velocity. Make it concrete for the page's reader (which busywork, which conversations, what happens to pipeline), and present it as a belief and an argument, not a measured result (guardrails).

Consider a cornerstone page that sets out the argument in full. The strongest candidate is **admin time vs selling time**, the topic Pipeleap should own (see business-context.md): a definitive guide to where reps' time goes, how to measure it and how to win it back, paired with a selling-time calculator. A sales velocity page is the second candidate. Other pages link to it, and it is the natural target for links earned through outreach. Propose it in the content calendar; don't build it without the user's yes.

## Step 3: Write the page

- Follow the voice rules in the guardrails: plain, direct, specific, no hype, no AI disclaimers, platform not agency.
- Open by answering the query within the first two or three sentences. Searchers leave pages that make them scroll for the answer.
- Use the reader's words from the search results and "People also ask". Use the primary keyword naturally in the H1, the first paragraph and at least one H2; never stuff it.
- Every claim about Pipeleap must trace back to `business-context.md`. Every external statistic gets a link to a source you opened. When you lack proof, describe how Pipeleap measures the result instead of stating one.
- Add a short FAQ built from real questions (People also ask, Search Console queries), with FAQPage JSON-LD that mirrors it exactly.
- Make the page skimmable: descriptive H2s, short paragraphs, tables where they compare things.
- Length follows intent: as long as it takes to beat the current top results on usefulness, no longer.

## Step 4: Build and publish

Build the HTML by following `pipeleap-seo/references/site-workflow.md` (copy the page shell, keep the consent script, analytics, navigation and footer, reuse the site's CSS patterns, add the page to `sitemap.xml`, add internal links). Run the audit script on the local file, fix its errors, and open a PR. Before the PR, read the page top to bottom as the target buyer: would you book a walkthrough after reading it?

After merge: notify search engines (step 6 of `site-workflow.md`), set the brief's status to `published` with the URL and date, and set the keyword map row's `page_status` to `exists`.

## Content calendar

When asked for a content calendar, take the highest-priority `create` rows and lay out roughly two pages a month, buying-intent pages first. Save it in `seo-work/plan.md` under "Content calendar", with the target keyword, page type and success measure for each.
