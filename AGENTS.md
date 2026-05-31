# Session Reminders

## Today (May 28, 2026)

### 4. Verify Core Web Vitals
After latest deploy completes, check LCP/FID/CLS via PSI or CrUX.

### 5. P2 SEO fixes completed
- Non-render-blocking Google Fonts
- Preconnect + dns-prefetch for GTM and Clarity
- Self-referencing hreflang=en on every page via SEO.tsx
- BreadcrumbList JSON-LD schema on glossary term pages
- <h1> on /how-it-works: already present inside OutboundWorkflowDiagram (false positive, no fix needed)

### 6. Email notifications configured
Email notifications are sent via GitHub Actions after each scheduled run:

| Workflow | Email subject | When |
|---|---|---|
| Daily SEO Agent Run | `SEO Agent Run #N — status` | Daily ~12:00 UTC |
| Daily SEO OS Run | `SEO OS Briefing #N — status` | ~5 min after SEO run |
| Daily GEO Agent Run | `GEO Agent Run #N — status` | ~5 min after SEO run |
| Weekly Tool Generation | `Weekly Tool Generation #N — status` | Monday ~06:00 UTC |

**Secrets stored in GitHub** (`pipeleap-seo-agents` → Settings → Secrets → Actions):
- `MAIL_SERVER` — `smtp.gmail.com`
- `MAIL_PORT` — `587`
- `MAIL_USERNAME` — `manik.anakathala@gmail.com`
- `MAIL_PASSWORD` — Gmail app password (generated at https://myaccount.google.com/apppasswords)
- `MAIL_TO` — `manik.anakathala@gmail.com`

**Tested:** Test email sent and confirmed received (May 28, 2026).

**If emails stop arriving:**
1. Check GitHub Actions run logs for `Send email notification` step
2. Verify `MAIL_PASSWORD` hasn't expired (app passwords don't expire unless revoked)
3. Check spam folder

### 7. Schedule reliability fixes deployed
**Problem:** GitHub Actions `schedule` cron is unreliable on free tier — runs can be delayed by hours or skipped entirely. Pushing workflow file changes cancels pending schedule runs.

**Fix — 3-layer redundancy:**

| Layer | Mechanism | Catch time |
|---|---|---|
| Primary | `0 12 * * *` (daily 12:00 UTC) | Scheduled |
| Backup | `0 0 * * *` (daily midnight) | Catches missed primary |
| Safety net | `daily_scheduler_health.yml` — runs every 6h, checks API for today's run, triggers `workflow_dispatch` if missing | Within ~6h worst case |

**Files changed:**
- `.github/workflows/daily_seo_run.yml` — dual cron + `check-skip` job (prevents double runs via proper job dependency)
- `.github/workflows/daily_scheduler_health.yml` — new: `actions: write` permission, checks API, triggers recovery dispatch

**Tested:** Health check triggered a recovery run (May 28, 17:04 UTC, #35). All steps passed including TypeScript validation; run marked failure only due to Bing Webmaster API returning HTTP 404 (non-functional endpoint).

### 8. Bing Webmaster API failure (fixed May 28)
**Problem:** `Submit sitemap to Bing Webmaster API` step returns HTTP 404 on `ssl.bing.com/webmaster/api.svc/json/SubmitSitemap`. This step exists in 3 workflows and was causing every SEO/GEO/weekly run to be marked **failure** despite all meaningful work succeeding.

**Root cause:** The Bing Webmaster API endpoint appears deprecated or changed. Our IndexNow submission (via `submit_urls.py`) already notifies Bing — this step was redundant.

**Fix:** Wrapped the Bing API call in try/except in all 3 workflows — HTTP errors are now logged as non-fatal warnings instead of failing the run.

**Files changed:**
- `.github/workflows/daily_seo_run.yml` — `urllib.error.HTTPError` + `Exception` catch
- `.github/workflows/daily_geo_run.yml` — same fix
- `.github/workflows/weekly_tool_generation.yml` — same fix

### 9. Node.js 20 deprecation fixed (May 28)
**Problem:** GitHub Actions warned that Node.js 20 is deprecated. Actions targeting Node.js 20 (`actions/checkout@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4`, `dawidd6/action-send-mail@v3`) were being force-run on Node.js 24 via `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`.

**Fix:** Upgraded all 4 actions across all 7 workflow files to versions that natively support Node.js 24, then removed the `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` env var.

| Action | Old | New |
|---|---|---|
| `actions/checkout` | `@v4` | `@v6` |
| `actions/setup-python` | `@v5` | `@v6` |
| `actions/upload-artifact` | `@v4` | `@v7` |
| `dawidd6/action-send-mail` | `@v3` | `@v17` |

**Files changed (8 workflow files total):**
- `.github/workflows/daily_seo_run.yml`, `daily_geo_run.yml`, `weekly_tool_generation.yml`, `daily_seo_os_run.yml`, `daily_serp_run.yml`, `daily_scheduler_health.yml`, `validate.yml`, `deploy_dashboard.yml`

### 10. Vercel deploy trigger consolidated to SEO OS (May 31)
**Problem:** Three workflows (`daily_seo_run.yml`, `daily_geo_run.yml`, `weekly_tool_generation.yml`) each independently triggered a Vercel deploy after pushing to the launchpad repo. The SEO OS workflow (`daily_seo_os_run.yml`) also pushed content but had no trigger. Result: **2–3 deploys per day** instead of 1.

**Fix:** Removed the `curl -X POST ${{ secrets.VERCEL_DEPLOY_HOOK }}` step from `daily_seo_run.yml`, `daily_geo_run.yml`, and `weekly_tool_generation.yml`. Added it to `daily_seo_os_run.yml` (the last workflow in the daily chain, triggered by `workflow_run` on SEO Agent completion). Now exactly **1 deploy per content cycle**.

**Deploy chain (consolidated):**
1. SEO Agent runs → pushes to launchpad → no deploy
2. SEO OS + GEO Agent run simultaneously → both push → SEO OS triggers **1 deploy** (GEO has no hook)
3. Weekly tool gen (Monday standalone) → pushes to launchpad → no deploy (SEO OS handles deploy later)

### 11. Always push fixes immediately (May 30)
**Rule:** Every fix or change must be committed and pushed immediately after applying. Unpushed changes are wasted work — they don't deploy, don't fix broken workflows, and don't improve the site.

**Checklist before declaring a fix done:**
1. Apply the change
2. Stage + commit (with meaningful message)
3. `git pull --rebase` if push is rejected (remote has new commits)
4. `git push`
5. For the **launchpad repo** (`temp_frontend_repo/`), repeat steps 2-4 in that directory

**Two repos to manage:**
| Repo | Directory | Purpose |
|---|---|---|
| `pipeleap-seo-agents` | `.` | Workflows, agents, SEO content |
| `pipeleap-launchpad-040053e5` | `temp_frontend_repo/` | Website frontend (Vercel deploy) |

---

## Anchored Summary (May 30, 2026)

**Goal:** Build a content-aware keyword planning engine that reads live site data, detects keyword coverage gaps, and mines existing content for latent keyword opportunities.

**Constraints:**
- All fixes committed & pushed immediately (AGENTS.md §11).
- Two repos: `pipeleap-seo-agents` (workflows/agents) and `pipeleap-launchpad-040053e5` (Vercel frontend at `temp_frontend_repo/`).
- Content coverage reads from local `temp_frontend_repo/` data files on each SEO OS run.
- `git pull --rebase` of `temp_frontend_repo/` before coverage build (added May 30).

**Done:**
- `core/content_coverage.py` — reads launchpad data files (blog-articles.ts, glossary-terms.ts, tools/*.ts) and builds a coverage map of **252 pages** (16 blogs, 87 glossary, 126 tools, 13 tool categories, 10 static pages).
- Text extraction methods: `_extract_blog_text()`, `_extract_glossary_text()`, `_extract_tool_text()` — parse body content/definitions/descriptions from TypeScript data files.
- `mine_latent_keywords(top_n=20)` — TF n-gram extraction (bigrams + trigrams), comprehensive stop word filtering, coverage dedup, intent scoring (1.5× bonus for commercial/transactional phrases).
- Modified `core/keyword_engine.py` — `discover()` accepts `content_coverage` parameter, skips covered keywords, tags `coverage_status` on each `KeywordOpportunity`, adds `detect_content_gaps()` method.
- Modified `agents/seo_os_agent.py` — **Step 4d** (content coverage analysis before Step 5 keyword engine), `_build_content_coverage()` with `git pull --rebase`, `_get_all_keyword_candidates()` method, content gaps + latent keywords output to daily briefing and `content_coverage.json` / `latent_keywords.json`.
- Fixed blog article count from 12→16 (regex handles both `"slug":` and backtick-slug), tool file parsing from 9→126 (indentation bug), slug prefix matching (prefix length ≥ 3).
- First SEO OS run with content coverage: 252 pages, 391 covered slugs, 2 gaps ("Apollo.io alternatives" from SERP clusters + competitor gaps).
- Test of `mine_latent_keywords()` on 473K char corpus: 20 clean keywords — top results: "real time" (freq=113), "multi channel" (freq=105), "mid market" (freq=70), "crm sync" (freq=52), "conversation intelligence" (freq=50).
- Commit `f4205a3` pushed with latent mining + git pull freshness.
- **GSC connection fix** — `connectors/gsc_connector.py` now reads `GSC_SITE_URL` env var as fallback (was being ignored in CI/CD, causing empty data every run).
- **Sitemap URL mismatch fix** — `connectors/post_publish_hook.py` and `connectors/search_engine_submitter.py` now use `https://www.pipeleap.com/sitemap.xml` (was missing `www.`, causing 301 redirect — Google silently dropped the sitemap).
- **Self-diagnosing GSC failure** — `agents/seo_os_agent.py` now logs warning with `site_url` when GSC returns 0 rows.
- Commit `079c9bb` pushed with all 4 GSC + sitemap fixes.
- **Index verification** — GSC inspection confirmed: only homepage (`www.pipeleap.com/`) is PASS/indexed. All other www pages return "URL is unknown to Google". The non-www versions (`pipeleap.com/blog`, `pipeleap.com/glossary/*`) ARE indexed — Google picked non-www as canonical before the redirect was stable.
- **Resubmitted** — Sitemap re-pushed to GSC (www URL, 20 pages sent to Indexing API, IndexNow+Bing hub notified). All 20/20 accepted.
- Commit `093a681` pushed with all GSC + sitemap + resubmit fixes.

**In Progress:**
- **www canonicalization** — Google has indexed `pipeleap.com/*` (non-www) for most pages. The 301 redirect + sitemap resubmission + Indexing API should migrate them to `www.pipeleap.com/*` over time. Monitor in GSC.

**Key Decisions:**
- Content coverage from local data files (fast, ~1s) over live HTTP crawl.
- Title/slug/heading match for coverage checking; body text mining is separate extraction for latent keywords.
- Coverage runs before keyword engine (Step 4d, not after) so engine can skip covered keywords.
- Threshold of 0.4 confidence for gap detection.
- Latent mining uses comprehensive stop word list (400+ terms: common English + domain-specific) to filter noise.

**Relevant Files:**
- `core/content_coverage.py` — ContentCoverage class, text extraction, n-gram mining, gap detection.
- `core/keyword_engine.py` — KeywordEngine.discover() accepts coverage param.
- `agents/seo_os_agent.py` — Step 4d, git pull, latent keywords in briefing.
- `temp_frontend_repo/src/data/blog-articles.ts` — 16 blog articles source.
- `temp_frontend_repo/src/data/glossary-terms.ts` — 87 glossary terms.
- `temp_frontend_repo/src/data/tools/*.ts` — 126 tools + 13 categories.
- `content/blogs/apollo-clay-pipeleap-comparison.md` — draft content brief (outline, not full article).
- `content/glossary/outbound-sales-automation.md`, `sales-orchestration.md`, `gtm-audit.md` — glossary briefs with full definitions (publishable but deprioritized).
