---
name: seo-brand-trust
description: >-
  Brand search and trust signals (E-E-A-T) for www.pipeleap.com: makes sure a search for "pipeleap"
  shows Pipeleap first with the right description, logo and sitelinks, and builds the pages and
  signals that show Google, AI assistants and buyers a real, credible company stands behind the
  product (About page, founder and author profiles, bylines, a security and data page, contact
  details, consistent company facts and official profiles). Use whenever the user mentions branded
  search, "people can't find us when they search Pipeleap", Knowledge Panel, sitelinks, E-E-A-T,
  trust, credibility, an About page, author bios, founder profile, security page, or why Google or AI
  doesn't trust or recognise the brand.
---

# Brand search and trust

Read `.claude/skills/pipeleap-seo/references/business-context.md` and `guardrails.md` first.

Two jobs, closely linked:
1. **Branded search.** When a buyer hears about Pipeleap (a podcast, a referral, a LinkedIn post) and searches the name, they must land on www.pipeleap.com, see an accurate description and find the walkthrough. On the old site, "pipeleap" didn't rank at all. Every other channel leaks if this one is broken.
2. **Trust (Google calls it E-E-A-T: experience, expertise, authoritativeness, trust).** Search engines and AI assistants favour content from identifiable people and real companies, and B2B buyers check who is behind a product before they book. A four-page site with no About page, no named people and no security information gives them little to go on.

## Step 1: Check the brand results

Search for each of these on Google and Bing (web search, or the user's Chrome), and in a fresh AI assistant chat:
- `pipeleap`, `pipeleap.com`, `pipeleap sales`, `pipeleap reviews`, `pipeleap pricing`, `what is pipeleap`
- common misspellings: `pipe leap`, `pipleap`, `pipeleep`

Record in `seo-work/brand/brand-serp.md` (dated, so later runs can compare):
- position of www.pipeleap.com, and whether sitelinks, the logo and the right title and description show
- what else ranks: old URLs, other companies with similar names, directory profiles, social profiles
- whether a Knowledge Panel appears and what it says
- what the AI assistants say Pipeleap is (hand inaccuracies to `seo-ai-visibility`)
- branded impressions, clicks and position from Search Console (queries containing "pipeleap")

If the site isn't first for its own name, treat it as the top priority: check the homepage is indexed (URL Inspection), the Organization structured data is complete, and the official profiles below exist and link to the site. Mostly it's a matter of authority: referring domains and consistent profiles (`seo-link-building`).

## Step 2: The company facts and official profiles

Keep one source of truth in `seo-work/brand/entity.md`: the exact company name, the one-line description ("a sales productivity and sales stack optimization platform…"), the category, the founding year and location, the founder's name and role, the logo URL, the contact email, and the list of official profiles. Get anything not already in business-context.md from the user; never guess it.

Official profiles worth having (the user creates the accounts; Claude prepares the copy from entity.md):
- LinkedIn company page, and the founder's LinkedIn profile naming Pipeleap
- Crunchbase
- G2 and Capterra (also link-building foundations)
- X/Twitter and YouTube, only if they will actually be used
- Wikidata only once independent coverage exists that meets its notability rules; don't create one on thin grounds

Once a profile exists, add its URL to the `sameAs` list in the homepage Organization structured data (a PR via `site-workflow.md`). Make sure Organization has `name`, `url`, `logo` (a square image at least 112×112 px), `description`, `email`, `founder` and `sameAs`. Every profile should use the same name, description, logo and website URL, because Google and AI assistants trust facts that agree across sources.

## Step 3: Trust pages

Propose these to the user as content work (`seo-content` writes them, following its brief step). Each needs real facts from the user; leave a section out rather than invent it.

| Page | What it must contain | Why |
|---|---|---|
| **About** (`/about`) | Why Pipeleap exists (the point of view in the founder's words), who is behind it with a photo and real background, where the company is based, the founding pilot stage stated plainly, contact details | The page Google, assistants and buyers check first for "who is this company" |
| **Founder and author profile** (a section on About, or `/about/<name>` once there are several authors) | Name, role, relevant sales or operations experience, LinkedIn link, the topics they write about; Person structured data with `sameAs` | Lets guides carry a named author with real experience, the strongest E-E-A-T signal for a new site |
| **Security and data** (`/security`) | How data flows (the CRM stays the source of truth), bring-your-own AI key, roles, AI spend caps, reps approving everything, where data is stored and how access is controlled, a security contact. Only what is true; no certifications that don't exist | Finance and IT approvers look for it; assistants are asked "is Pipeleap secure" |
| **Contact** (a section or page) | Email, what to contact about, response expectations | Basic trust signal; also the natural home of the booking CTA |

Also:
- **Bylines on guides.** Every guide or article shows the author's name (linked to their profile), the date it was published and the date it was last updated, with matching `author`, `datePublished` and `dateModified` in its Article structured data.
- **Real experience in the content.** Guides are stronger when they include first-hand detail the founder can supply: what they've seen in sales teams, how pilots measure selling time. Ask for it in the brief; never make it up.
- **Footer basics on every page:** company name, contact email, links to About, Security, Privacy and Cookie policies.

## Step 4: Fix and track

- Site changes (structured data, footer links, new pages) go through `site-workflow.md` as a PR.
- Profile creation and edits are tasks for the user, with the copy ready in `seo-work/brand/profiles/<site>.md`.
- Re-run Step 1 monthly as part of the operating calendar, and report branded position, branded clicks and anything wrong in the brand results to `seo-reporting`.

## Rules

On top of the guardrails:
- No invented team members, advisors, investors, press mentions, awards or certifications. No stock photos presented as staff.
- No "As seen in" logos unless the coverage is real and the user approves using them.
- Don't create a Wikipedia page for Pipeleap; it would break Wikipedia's conflict-of-interest rules and get deleted.
