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
