---
name: seo-link-building
description: >-
  White-hat link building and off-page SEO for www.pipeleap.com: finds legitimate places to earn
  backlinks and mentions (software directories and review sites, sales and RevOps publications,
  podcasts, communities, journalist requests, unlinked brand mentions, partner pages), prepares
  listing copy and personalised outreach drafts for the user to send, and tracks every prospect. Use
  whenever the user mentions backlinks, domain authority, referring domains, link building,
  directories, G2 or Capterra listings, guest posts, PR, podcasts, mentions or "getting other sites to
  link to us".
---

# Link building and off-page SEO

Read `.claude/skills/pipeleap-seo/references/business-context.md` and `guardrails.md` first. The link rules in the guardrails are firm: no paid links, no link schemes, no fake reviews. The old site had zero referring domains, which is a big reason branded searches for "pipeleap" didn't rank; the fix is earning real links steadily, not shortcuts that risk a penalty.

Claude researches, prepares and tracks. The user creates accounts, submits listings and sends every message from their own accounts.

## The tracker

Everything goes in `seo-work/backlinks/prospects.csv`:

```
domain,url,type,relevance(1-3),why_relevant,contact_or_submit_url,status,next_action,date_updated,link_live_url,notes
```

`type` is one of: directory, review-site, publication, podcast, community, journalist-request, unlinked-mention, partner, resource-page. `status` moves through: researched → drafted → sent/submitted → replied → live, or → declined / no-reply. Check the tracker before adding a prospect, so nobody gets pitched twice.

## Tactics, in the order to work them

1. **Foundations (do once).** Legitimate software directories and profiles that buyers actually browse: G2, Capterra / GetApp / Software Advice, TrustRadius, Product Hunt (a planned launch, not a quiet listing), SaaSHub, AlternativeTo, Crunchbase, the LinkedIn company page, and any integration marketplaces of the tools Pipeleap connects to (only once the integration is confirmed live). For each, prepare the listing copy in `seo-work/backlinks/listings/<site>.md`: category, short and long description, features, screenshots needed, and the URL to use. Use only facts from business-context.md. Reviews must come from real pilot users who choose to leave them; you can draft the request email, never the review.
2. **Unlinked mentions.** Search for "pipeleap" mentions that don't link to the site, and draft a short, friendly note asking for a link.
3. **Journalist and expert requests.** Check expert-source platforms the user has joined (for example Qwoted, Featured, Help a B2B Writer) for questions about sales productivity, tool sprawl, RevOps, AI in sales, revenue growth, sales rep performance, and especially how much time reps spend on admin vs selling (the topic Pipeleap should own). Draft concise, specific expert answers in the founder's voice for the user to submit.
4. **Podcasts and communities.** Pick outlets by the persona they reach (business-context.md): executive audiences (CRO and revenue-leader podcasts, founder and CEO shows), sales leadership and management audiences, and sales operations and transformation audiences (RevOps, sales excellence, GTM systems). Find sales, RevOps and founder podcasts and newsletters that interview guests, and draft a pitch with two or three concrete talking points (the core point of view: less busywork means more conversations, more pipeline and faster sales velocity; plus tool sprawl costs, measuring selling time, rep-approved AI, growing revenue without adding headcount, how much of a rep's week goes on admin vs selling, giving managers visibility into which reps need help). In communities (RevOps, sales leadership groups), contribute answers, never drop links. List them as relationship targets, not link sources.
5. **Guest articles.** Publications for sales leaders and RevOps that accept genuinely editorial contributions. The pitch offers an idea their readers need, not a link. Never pay for placement.
6. **Linkable assets.** When a page worth linking to exists (a calculator, original data from pilots shared with permission, a strong buyer's guide), find the resource pages and authors who cover that topic and draft outreach. If no such asset exists yet, recommend one to `seo-content`, because link building without something worth linking to is mostly wasted.
7. **Competitor link gaps.** Use `seo-work/competitors/gaps.md`: places that list several competitors but not Pipeleap are the warmest prospects.

## Finding and qualifying prospects

Use web search with operators, for example `"sales productivity" "tools" intitle:best`, `"revops" "write for us"`, `"sales podcast" "be a guest"`, `"pipeleap" -site:pipeleap.com`. Qualify each prospect before adding it:
- real audience of sales leaders, RevOps or founders (relevance 2 or 3); skip generic "write for us" sites with no audience
- a real editorial site, not a link farm (it has a real audience, original writing, authors and no "sponsored post" price list)
- a realistic reason they'd say yes

Quality beats volume: ten relevant links outperform a hundred directory links.

## Outreach drafts

Save drafts in `seo-work/backlinks/outreach/<domain>.md`. Each draft is:
- addressed to a named person when one can be found from public pages
- short (under 120 words), specific to their content, with a clear reason it helps their readers
- honest about who is writing and why; no fake familiarity, no "I'm a big fan" without specifics
- one follow-up draft at most, about a week later

Give the user the list of drafts ready to send. Update the tracker when they say what they sent.

## Weekly batch (from the operating calendar)

Each week: add about ten qualified prospects, draft outreach for the best five, check whether earlier links went live, and report the counts (new prospects, sent, live this week, total referring domains).
