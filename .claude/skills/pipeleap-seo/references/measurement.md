# Measurement

SEO here is judged by meetings booked, so the tracking chain from search to meeting has to be intact. Check it before reporting anything.

## The chain

```
Search impressions → clicks → landing page visit → CTA click (book_walkthrough) → meeting booked → pilot started → paid customer
   Search Console       Search Console     GA4               GA4 event              Apollo         user's records    user's records
```

| Metric | Source | How to get it |
|---|---|---|
| Impressions, clicks, CTR, position, by query, page and country | Google Search Console | API, browser, or a CSV export from the user |
| Bing impressions and clicks | Bing Webmaster Tools | Browser or CSV export |
| Organic landing sessions, `/pilot` visits | GA4 (`G-GW7CB348F3`) | Browser or the GA4 Data API (needs the numeric property ID) |
| CTA clicks | GA4 event `book_walkthrough` (params `cta_location`, `cta_label`, `page_path`) | Filter by session default channel group = Organic Search |
| Meetings booked | Apollo meetings (the booking link is an Apollo meet link) | Apollo.io connector if connected, or ask the user |
| Pilots started, paid customers | The user's CRM or records | Ask the user; record the answer in the report |

## Data access options, in order of preference

1. **API.** `connectors/gsc_connector.py` and `connectors/ga4_connector.py` in this repo read Search Console and GA4 when a service-account JSON is available (env `GSC_SERVICE_ACCOUNT_JSON` or `GOOGLE_APPLICATION_CREDENTIALS`). The `pipeleap.com` Search Console property was re-created in November 2026, so that service account must be added again as a user on the property (Settings → Users and permissions) before the API returns data.
2. **Browser.** Use the Claude in Chrome tools to open Search Console, GA4 or Bing Webmaster Tools in the user's signed-in Chrome and read the numbers. Read only; don't change settings unless asked.
3. **Export.** Ask the user for a CSV export (Search Console → Performance → Export).

Say which source each number came from and the date range. Never estimate a figure and present it as measured.

## Setup checks (do these during the foundation phase)

- GA4: `book_walkthrough` is marked as a **key event** (Admin → Events), so it appears in acquisition reports by channel.
- GA4: the default channel group separates Organic Search from Direct (consent mode can push organic into "Unassigned" when consent is declined; note this as a known gap).
- Search Console: the sitemap `https://www.pipeleap.com/sitemap.xml` is submitted and shows no errors.
- Bing Webmaster Tools: the site is verified (it can import from Search Console) and the sitemap submitted.
- Apollo: the booking form asks "How did you hear about us?" with a "Google / search" option. Booking links don't reliably carry UTMs, so this answer is the cleanest way to tie meetings back to search.

## Attribution rule of thumb

Organic search rarely gets the last click on a B2B purchase. Count a meeting as SEO-sourced when either the first session or the session where `book_walkthrough` fired came from organic search, or the person answered "search" when booking. Report both counts if they differ, and state the rule used.
