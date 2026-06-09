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

SITE_URL      = "https://www.pipeleap.com"
SITEMAP_URL   = "https://www.pipeleap.com/sitemap.xml"
LOCAL_SITEMAP = os.path.join(os.path.dirname(__file__), "..", "temp_frontend_repo", "public", "sitemap.xml")
UA            = "pipeleap-seo-bot/1.0"
INDEXNOW_KEY  = "92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55"

failed = 0

# ── 1. Bing Webmaster API sitemap submission ─────────────────────
api_key = os.environ.get("BING_API_KEY", "")
if api_key:
    print("Submitting sitemap to Bing Webmaster API ...")
    payload = {
        "siteUrl": SITE_URL,
        "feedUrl": SITEMAP_URL,
    }
    endpoint = f"https://ssl.bing.com/webmaster/api.svc/json/SubmitFeed?apikey={api_key}"
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
LOCAL_SITEMAP_DIR = os.path.join(os.path.dirname(__file__), "..", "temp_frontend_repo", "public")

def _get_all_sitemap_urls():
    """Get all URLs from sitemap index + sub-sitemaps (local if available)."""
    if os.path.exists(LOCAL_SITEMAP):
        with open(LOCAL_SITEMAP, "r", encoding="utf-8") as f:
            sitemap_content = f.read()
        print(f"  Using local sitemap: {LOCAL_SITEMAP}")
        # Get sub-sitemap filenames from local index
        sub_paths = re.findall(r"<loc>https://[^<]+/(sitemap-[^<]+\.xml)</loc>", sitemap_content)
        all_urls = []
        for sub in sub_paths:
            sub_path = os.path.join(LOCAL_SITEMAP_DIR, sub)
            if os.path.exists(sub_path):
                with open(sub_path, "r", encoding="utf-8") as f:
                    sub_content = f.read()
                sub_urls = re.findall(r"<loc>(https://[^<]+)</loc>", sub_content)
                all_urls.extend(sub_urls)
        return all_urls
    else:
        r = requests.get(SITEMAP_URL, timeout=15, headers={"User-Agent": UA})
        r.raise_for_status()
        sitemap_content = r.text
        print(f"  Using live sitemap: {SITEMAP_URL}")
        # Fetch each sub-sitemap to get all URLs
        sub_paths = re.findall(r"<loc>(https://[^<]+/sitemap-[^<]+\.xml)</loc>", sitemap_content)
        all_urls = []
        for sub_url in sub_paths:
            r2 = requests.get(sub_url, timeout=15, headers={"User-Agent": UA})
            r2.raise_for_status()
            sub_urls = re.findall(r"<loc>(https://[^<]+)</loc>", r2.text)
            all_urls.extend(sub_urls)
        return all_urls

print("\nSubmitting URLs to Bing IndexNow ...")
urls = _get_all_sitemap_urls()
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
