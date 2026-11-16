# Guardrails

These rules protect the domain, the brand and the user's accounts. They come from what went wrong on the old site and from search engine spam policies. When a request conflicts with one, say so and suggest the closest safe alternative.

## Nothing goes live or leaves without a person's approval

| Action | What Claude does | What the person does |
|---|---|---|
| Change the website | Opens a pull request on `Pipeleap-web-redesign` (see `site-workflow.md`) | Reviews the Vercel preview and merges |
| Outreach for links, PR or guest posts | Drafts the email or message into `seo-work/backlinks/` | Sends it from their own account |
| Directory or review-site listings | Prepares the listing copy and the field values | Creates the account and submits |
| Search Console actions (removals, indexing requests) | Can do them in the browser when asked | Has asked for it in this conversation |

Scheduled runs prepare work. They never merge, publish or send.

## Content rules

- **Only claim what is true.** Use the facts in `business-context.md`. Never invent customers, logos, testimonials, case studies, results ("saves 10 hours a week"), integrations, certifications, awards or pricing. In the pilot stage, describe how value is measured, not outcomes that haven't been measured.
- **Revenue and performance claims go through the mechanism, never a promised result.** Say how Pipeleap gives reps more selling time, keeps follow-ups from slipping and shows managers which reps need help and what kind. Don't say it "increases revenue by X%", "guarantees quota" or "makes reps hit target". Frame rep performance as giving managers visibility and removing admin, never as monitoring or surveilling reps.
- **Pipeleap doesn't coach.** Never call it a coaching platform, coaching tool or training product, or say it "coaches reps". The accurate claim is that it shows managers who needs help and what kind, so the manager can help each rep reach target.
- **State the point of view as a belief, not a proven statistic.** "We believe less busywork means more conversations and more pipeline" is fine and should run through our content. "Pipeleap customers get 30% more conversations" is not, until pilots have measured it and the user has approved publishing the figure.
- **Third-party statistics need a real, linked source** that you have opened and read. If you can't verify a number, leave it out. A wrong statistic in a buyer's guide costs more trust than it earns.
- **Describe competitors fairly**, using their own public pages, and date the comparison. No disparaging claims you can't support.
- **No AI disclaimers** such as "this content was produced with AI assistance". The owner has banned them site-wide; accuracy comes from the review step instead.
- **Platform, not agency.** Pipeleap is software. Avoid service-company language ("we'll run it for you", "our team builds", "strategy call", "retainer", "done-for-you"). The CTA is "Book a walkthrough" or "Apply for a founding pilot".
- **Match the site's voice:** plain, direct, short sentences, concrete nouns, no hype words ("revolutionary", "game-changing", "supercharge"), no emojis. Follow the spelling already used on the page you are editing.
- **Every page must earn its place.** Before creating a page, name the query it answers better than the current top results, and why a buyer would book after reading it. If you can't, don't create it. No bulk or templated page generation (city pages, "X for every industry" pages, glossary dumps); that is what buried the old site.

## Link-building rules (search engine spam policies)

Never do or recommend:
- buying or selling links, or paying for "guest posts" whose purpose is a dofollow link
- private blog networks, link farms, automated link schemes, comment or forum spam
- large-scale link exchanges ("link to me and I'll link to you")
- fake, incentivised or self-written reviews on G2, Capterra or anywhere else
- creating fake personas or sockpuppet accounts

Do: earn links with things worth linking to (original data, calculators, honest guides), listings on legitimate directories, real relationships, podcasts and guest articles that are genuinely editorial, and asking for links where Pipeleap is already mentioned.

## Technical rules

- Don't touch the Termly consent script's position (it must stay the first script) or the GA4 snippet, except to fix a confirmed tracking bug.
- Don't add `noindex`, change canonicals, robots.txt or redirects without explaining the effect and getting a yes.
- Don't recreate URLs under `/blog/`, `/glossary/` or `/tools/` without a deliberate decision (they were removed from search on purpose).
- Keep credentials out of files and output. Read API keys from environment variables; never print them.
