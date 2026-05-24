"""
Full indexing submission script — runs once to submit all 164 sitemap URLs to:
1. IndexNow  → Bing / Yandex / DuckDuckGo (instant, free)
2. GSC sitemap → Google crawl queue
3. Google Search Console individual URL inspection (request indexing)

Run from repo root:  python scripts/submit_all_indexing.py
"""
import json, sys, time, re, os
from pathlib import Path

import requests

# ── Config ────────────────────────────────────────────────────────────────────
SITE_URL      = "https://www.pipeleap.com"
SITEMAP_URL   = "https://www.pipeleap.com/sitemap.xml"
INDEXNOW_KEY  = "pipeleap-indexnow-2026"
KEY_LOCATION  = f"{SITE_URL}/{INDEXNOW_KEY}.txt"

INDEXNOW_ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://yandex.com/indexnow",
]

GSC_CREDENTIALS = "credentials/gsc_service_account.json"
GSC_PROPERTY    = "sc-domain:pipeleap.com"

# ── 1. Fetch URLs from live sitemap ───────────────────────────────────────────
print("Fetching sitemap ...")
resp = requests.get(SITEMAP_URL, timeout=15)
resp.raise_for_status()
urls = re.findall(r"<loc>(https://[^<]+)</loc>", resp.text)
# Strip any trailing XML tags that crept into URLs (sitemap formatting artifact)
urls = [re.sub(r"<.*", "", u).strip() for u in urls]
print(f"  Found {len(urls)} URLs\n")

# ── 2. IndexNow submission ────────────────────────────────────────────────────
print("Submitting to IndexNow (Bing / Yandex / DuckDuckGo) ...")
host = SITE_URL.replace("https://", "").replace("http://", "")
payload = {
    "host": host,
    "key": INDEXNOW_KEY,
    "keyLocation": KEY_LOCATION,
    "urlList": urls,
}
indexnow_ok = 0
for endpoint in INDEXNOW_ENDPOINTS:
    try:
        r = requests.post(endpoint, json=payload, timeout=20)
        status = r.status_code
        # 200 = accepted, 202 = accepted (queued)
        ok = status in (200, 202)
        print(f"  {endpoint.split('/')[2]:30s}  HTTP {status}  {'OK' if ok else 'FAILED'}")
        if ok:
            indexnow_ok += 1
    except Exception as e:
        print(f"  {endpoint:50s}  ERROR: {e}")
    time.sleep(0.5)
print(f"  IndexNow: {indexnow_ok}/{len(INDEXNOW_ENDPOINTS)} endpoints accepted\n")

# ── 3. GSC sitemap submission ─────────────────────────────────────────────────
print("Submitting sitemap to Google Search Console ...")
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        GSC_CREDENTIALS,
        scopes=["https://www.googleapis.com/auth/webmasters"],
    )
    service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    service.sitemaps().submit(siteUrl=GSC_PROPERTY, feedpath=SITEMAP_URL).execute()
    print(f"  GSC sitemap submitted: {SITEMAP_URL}  OK\n")
except ImportError:
    print("  [SKIP] google-api-python-client not installed — GSC submission skipped")
    print("         Install with: pip install google-api-python-client google-auth\n")
except Exception as e:
    print(f"  GSC sitemap error: {e}\n")

# ── 4. Google Indexing API (request crawl for top-priority pages) ─────────────
print("Requesting indexing via Google Indexing API (top-priority pages) ...")
priority_urls = [u for u in urls if not any(
    seg in u for seg in [
        "/tools/ai-sdr-tools/", "/tools/cold-email-tools/", "/tools/sales-engagement-tools/",
        "/tools/prospecting-tools/", "/tools/lead-enrichment-tools/", "/tools/crm-tools/",
        "/tools/call-recording-tools/", "/tools/revenue-intelligence-tools/",
        "/tools/linkedin-automation-tools/", "/tools/ai-outbound-agents/",
        "/tools/workflow-automation-tools/", "/tools/sales-analytics-tools/",
        "/tools/gtm-engineering-tools/",
    ]
)]
print(f"  Priority URLs (non-tool-detail): {len(priority_urls)}")
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    indexing_creds = service_account.Credentials.from_service_account_file(
        GSC_CREDENTIALS,
        scopes=["https://www.googleapis.com/auth/indexing"],
    )
    indexing_service = build("indexing", "v3", credentials=indexing_creds, cache_discovery=False)
    accepted = 0
    errors   = []
    for url in priority_urls:
        try:
            indexing_service.urlNotifications().publish(
                body={"url": url, "type": "URL_UPDATED"}
            ).execute()
            accepted += 1
            time.sleep(0.1)
        except Exception as e:
            err_str = str(e)
            if "SERVICE_DISABLED" in err_str or "403" in err_str:
                errors.append("API_DISABLED")
                break
            errors.append(err_str[:80])

    if "API_DISABLED" in errors:
        print("  [ACTION REQUIRED] Google Indexing API is disabled for this project.")
        print("  Enable it here (takes 2 minutes):")
        print("  https://console.developers.google.com/apis/api/indexing.googleapis.com/overview?project=873204905433")
    else:
        print(f"  Indexing API: {accepted}/{len(priority_urls)} URLs submitted")
        if errors:
            print(f"  Errors: {errors[:3]}")

except ImportError:
    print("  [SKIP] google-api-python-client not installed")
except Exception as e:
    print(f"  Indexing API error: {e}")

print("\n" + "="*60)
print(f"SUBMISSION COMPLETE")
print(f"  IndexNow:     {indexnow_ok}/{len(INDEXNOW_ENDPOINTS)} engines  ({len(urls)} URLs)")
print(f"  GSC sitemap:  see above")
print(f"  Google API:   see above")
print("="*60)
print("\nNext steps:")
print("  1. Check GSC Coverage report in 24-48 hours")
print("  2. Check Bing Webmaster Tools — URLs appear within hours")
print("  3. Enable Google Indexing API if it showed ACTION REQUIRED above")
