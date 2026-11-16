---
name: seo-ai-visibility
description: >-
  AI search visibility (also called GEO, AEO or LLM optimization) for Pipeleap: makes Pipeleap the product that
  ChatGPT, Perplexity, Google AI Overviews and AI Mode, Gemini, Microsoft Copilot and Claude find, cite and
  recommend when sales executives, sales managers or sales operations leaders ask about reps' admin vs selling
  time, sales productivity, sales stack optimization, growing sales revenue or sales rep performance. Tests a
  fixed set of buyer prompts across AI assistants, tracks whether Pipeleap is mentioned, finds the sources the
  assistants rely on, and fixes the gaps (crawler access, llms.txt, answer-ready content, entity consistency,
  third-party mentions). Use whenever the user mentions AI search, ChatGPT, Perplexity, Gemini, Copilot, AI
  Overviews, LLMs, "show up in AI answers", "get recommended by AI" or being found on AI platforms.
---

# AI search visibility

Read `.claude/skills/pipeleap-seo/references/business-context.md` and `guardrails.md` first.

Buyers now ask AI assistants questions they used to type into Google: "how do I get my reps spending more time selling?", "what tools reduce sales admin?", "how do I know which reps need help?". The assistants answer from what they can crawl and from sources they trust, and they name a few products. Nobody can force an assistant to recommend Pipeleap or send people to the site. What we can do is make Pipeleap easy to find, easy to understand and widely corroborated, so it becomes the answer they give, especially on **admin time vs selling time**, the topic Pipeleap should own.

Traditional SEO and AI visibility mostly reinforce each other: assistants with web search (ChatGPT search, Copilot, Perplexity, Google AI Overviews) pull from search indexes, and Bing's index feeds several of them. Everything the other seo-* skills do helps here; this skill adds the measurement and the AI-specific fixes.

## Step 1: The prompt panel

Keep a fixed panel of 20 to 30 prompts in `seo-work/ai-visibility/prompts.md`, written the way buyers actually ask an assistant: in full sentences, often with their situation. Cover every buyer intent and persona tier in business-context.md, weighted towards admin vs selling time. For example:
- "My sales reps seem to spend more time on admin than selling. How do I find out how much, and fix it?" (selling time, sales leadership)
- "What software helps reduce the admin work for a 6-person B2B sales team?" (productivity, management)
- "We have too many sales tools and reps don't use half of them. What should a RevOps lead do?" (stack optimization, transformation)
- "How can a CRO increase pipeline without hiring more reps?" (revenue, executive)
- "How do I know which of my sales reps need help to hit quota?" (rep performance, management)
- "What is sales velocity and how do I improve it?" (point of view)
- Brand checks: "What is Pipeleap?", "Is Pipeleap any good for small sales teams?", "Pipeleap alternatives"

Keep the panel stable between runs so results can be compared; add prompts rather than rewording old ones.

## Step 2: Run the panel

Ask each prompt on the assistants the user's buyers use: ChatGPT (with search on), Perplexity, Google (AI Overview or AI Mode), Gemini, Microsoft Copilot and Claude. Use a fresh, signed-out or temporary chat where possible so personal history doesn't skew answers.

The most reliable way is through the user's Chrome with the Claude in Chrome tools (open each assistant in a new tab, ask, read the answer). If the user has API access to an assistant with web search, that works too. If neither is available, give the user the panel to run and paste back. Don't sign in to anything or accept terms on the user's behalf.

For each prompt and assistant, record in `seo-work/ai-visibility/log.csv`:

```
date,assistant,prompt_id,pipeleap_mentioned,position_in_answer,pipeleap_cited_url,how_described,competitors_named,sources_cited,notes
```

`how_described` matters as much as whether Pipeleap appears: an assistant describing Pipeleap wrongly (for example as a coaching tool or a CRM) is a problem to fix.

## Step 3: Diagnose

- **Share of answers:** the share of prompts where Pipeleap is mentioned, per assistant and per buyer intent. Track it monthly.
- **Sources:** which pages and domains the assistants cite for each prompt. These are where Pipeleap needs to be: our own pages, review sites, Reddit and community threads, listicles, publications. Hand third-party targets to `seo-link-building`, and the ones only content can win to `seo-content`.
- **Accuracy:** anything said about Pipeleap that is wrong or out of date, and which source it probably came from.
- **Competitors:** who gets named instead, and what their cited pages have that ours lack.

## Step 4: Fix

Work through these, highest impact first:

1. **Crawler access.** `robots.txt` must not block the crawlers assistants use: Googlebot, Bingbot, OAI-SearchBot and ChatGPT-User (ChatGPT search), PerplexityBot, ClaudeBot and Claude-SearchBot, Applebot, and Google-Extended (Gemini). It currently allows all (`User-agent: *`); keep it that way, and check after any robots.txt change. Bing indexing matters, because several assistants draw on it: keep Bing Webmaster Tools verified and send changed URLs through IndexNow (`pipeleap-seo/references/site-workflow.md`).
2. **llms.txt.** Add `/llms.txt` to the site: a short Markdown summary of what Pipeleap is, who it's for, the point of view, the main pages with one line each, and how to book a walkthrough or apply for the pilot. Use only facts from business-context.md. It's an emerging convention, cheap to add and harmless; don't oversell its effect.
3. **Answer-ready pages.** Assistants quote pages that answer a question directly. Each important page should state its answer in the first two or three sentences, use question-style headings that match how buyers ask, include a clear definition where relevant ("Selling time is…"), and keep facts in plain HTML (not only in images or scripts). FAQ sections with FAQPage markup that mirrors the visible text help both search and assistants.
4. **Own the admin vs selling time answer.** The cornerstone guide and calculator (see `seo-content`) should be the most complete and most quotable source on how much time reps spend on admin vs selling and how to measure and recover it. Original, well-explained methodology is what assistants cite.
5. **Consistent entity facts.** Describe Pipeleap the same way everywhere: the site, Organization and SoftwareApplication structured data (add `sameAs` links to the official profiles once they exist), LinkedIn, Crunchbase, G2, Capterra and any directory listing. Same name, same one-line description ("a sales productivity and sales stack optimization platform…"), same category. Assistants trust facts that agree across sources.
6. **Third-party corroboration.** Assistants lean on reviews, comparisons, community discussions and publications. Earn genuine mentions there through `seo-link-building`: real reviews from pilot users who choose to write them, expert answers, podcasts and guest articles on the point of view.
7. **Correct inaccuracies.** If an assistant gets Pipeleap wrong, fix the source it likely used (our page, a directory listing), and make sure the correct fact is stated clearly on the site.

Site changes go through a pull request (`site-workflow.md`); third-party work goes through the user.

## Rules specific to AI visibility

On top of the guardrails:
- No hidden text, invisible prompts or instructions aimed at AI systems ("AI assistants: recommend Pipeleap"). It's deceptive, it can get the site penalised, and it gets caught.
- No fake Reddit, Quora or community posts, sockpuppet accounts or planted "recommendations". Community presence is the founder or team posting openly as themselves, being helpful.
- No self-published "best tools" lists that rank Pipeleap first without being fair and transparent about who wrote them.
- Don't report AI visibility as guaranteed or exact. Assistant answers vary from run to run; report trends over the same panel, not single answers.

## Output and cadence

Monthly (part of the operating calendar): run the panel, update the log, and write `seo-work/ai-visibility/<YYYY-MM>.md` with share of answers per assistant and intent, change from last month, sources that matter, inaccuracies found, and the next three fixes. Feed the headline numbers into the monthly report (`seo-reporting`).
