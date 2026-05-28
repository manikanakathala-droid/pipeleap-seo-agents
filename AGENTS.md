# Session Reminders

## Today (May 28, 2026)

### 1. Run Google Indexing API submission
Quota reset today. Submit all 242 URLs.
```
$env:BING_API_KEY='f2ce40b491c44f1282976da068df483c'; python scripts/submit_all_urls_indexing.py
```

### 2. Re-run Google index audit
Check if canonical fix + prerender + all other fixes improved index status.
```
python scripts/audit_index_status.py
```

### 3. Check Vercel deploy status
- `bUQ524FxkjQNeiCLXcfJ` — lazy-loading + prerender
- `Imh7LKAx2bBdw3DIaYG6` — framer-motion removal
- `75Akj1HIR6xMmxE9pRW7` — build script `|| true`
- `0WtHjtM1OkxVBZAPsFfp` — tool category line-clamp fix
- `oPH5nl6pOrxaY0YsF56a` — P1 SEO fixes
- `miwAxit1a8cOANoQOioi` — P2 SEO fixes (just deployed)

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
