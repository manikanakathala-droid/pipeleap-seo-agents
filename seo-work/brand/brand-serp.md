# Brand search check

## 2026-11-20 (foundation baseline)

**Result: Pipeleap does not rank for its own name.** This is priority 1 in the plan.

| Check | Finding | Source |
|---|---|---|
| Web search "pipeleap" | No pipeleap.com result in the top 10. Results are Pipedream/Pipedrive + "Leap" integration pages, Gleap docs and similar names. The search engine treats "pipeleap" as a probable misspelling of other brands | WebSearch, 2026-11-20 |
| Search Console, query "pipeleap" (last 28 days) | 4 impressions, 0 clicks | GSC Performance, sc-domain:pipeleap.com |
| Search Console, all queries (last 28 days) | 1 click, 9 impressions, average position 11.4 | GSC Performance |
| Indexed pages | 16 indexed, but several are retired old URLs being dropped, plus app.pipeleap.com | GSC Pages |
| Knowledge Panel | None | — |
| Official profiles linking to the site | None known (no `sameAs` in Organization schema) | Site source |

Not checked yet (need the user's browser, signed out, per country): Google results for "pipeleap" in us/gb/in, the misspellings ("pipe leap", "pipleap"), and what AI assistants say Pipeleap is (seo-ai-visibility, first panel run).

### Why it doesn't rank
1. **No external signals.** No referring domains and no official profiles (LinkedIn, Crunchbase, G2) pointing at the site, so search engines can't confirm "Pipeleap" is a real entity, and fold the query into similar brands.
2. **The homepage barely says the name with context.** The H1 is the single word "Pipeleap"; there is no About page tying the name to a company, a founder and a location (`/about` currently redirects to `/`).
3. **app.pipeleap.com is indexed** and splits the brand results.

### Fix (see plan.md, priority 1)
- Create the official profiles with identical facts (seo-brand-trust step 2): LinkedIn company page and founder profile, Crunchbase, G2, Capterra. User creates accounts; copy prepared in `seo-work/brand/profiles/`.
- Add `sameAs`, `logo`, `founder`, `email` to Organization schema once profiles exist.
- Build `/about` (remove the `/about` → `/` redirect).
- Noindex app.pipeleap.com.
- Earn the first referring domains (directories first).
- Re-check monthly.
