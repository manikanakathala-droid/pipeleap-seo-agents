"""
Submit sitemap to Bing via Webmaster API + IndexNow fallback.

Usage:
    python scripts/submit_bing_sitemap.py

Requires either:
  - BING_API_KEY env var (for Webmaster API sitemap submission)
  - IndexNow key deployed at site root (free, no API key needed)
"""
import json, os, re, sys

import requests

SITE_URL    = "https://www.pipeleap.com"
SITEMAP_URL = "https://www.pipeleap.com/sitemap.xml"
UA          = "pipeleap-seo-bot/1.0"
INDEXNOW_KEY = "92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55"

failed = 0

# ── 1. Bing Webmaster API sitemap submission ─────────────────────
api_key = os.environ.get("BING_API_KEY", "")
if api_key:
    print("Submitting sitemap to Bing Webmaster API ...")
    payload = {
        "siteUrl": SITE_URL,
        "feedpath": SITEMAP_URL,
    }
    endpoint = f"https://ssl.bing.com/webmaster/api.svc/json/SubmitSitemap?apikey={api_key}"
    try:
        r = requests.post(endpoint, json=payload, timeout=15)
        result = r.json()
        print(f"  HTTP {r.status_code} — {result}")
        if r.ok:
            print(f"  Sitemap submitted to Bing Webmaster API OK")
        else:
            print(f"  Bing Webmaster API error")
            failed += 1
    except Exception as e:
        print(f"  Bing Webmaster API request failed: {e}")
        failed += 1
else:
    print("No BING_API_KEY set — skipping Webmaster API submission")

# ── 2. IndexNow (URL-level notification, no key needed) ──────────
print("\nSubmitting URLs to Bing IndexNow ...")
r = requests.get(SITEMAP_URL, timeout=15, headers={"User-Agent": UA})
r.raise_for_status()
urls = re.findall(r"<loc>(https://[^<]+)</loc>", r.text)
urls = [re.sub(r"<.*", "", u).strip() for u in urls]
print(f"  {len(urls)} URLs found in sitemap")

BATCH_SIZE = 500
ok_count = 0
for i in range(0, len(urls), BATCH_SIZE):
    batch = urls[i:i + BATCH_SIZE]
    payload = {
        "host": "www.pipeleap.com",
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": batch,
    }
    try:
        r = requests.post("https://www.bing.com/indexnow", json=payload, timeout=20)
        if r.status_code in (200, 202):
            ok_count += len(batch)
            print(f"  Batch {i//BATCH_SIZE + 1}: HTTP {r.status_code} OK ({len(batch)} URLs)")
        else:
            print(f"  Batch {i//BATCH_SIZE + 1}: HTTP {r.status_code} — {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  Batch {i//BATCH_SIZE + 1}: {e}")
        failed += 1

print(f"\nIndexNow: {ok_count}/{len(urls)} URLs submitted to Bing")
if ok_count != len(urls):
    failed += 1

sys.exit(1 if failed > 0 else 0)
