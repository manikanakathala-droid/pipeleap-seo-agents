"""
Submit sitemap to Bing via Webmaster API + IndexNow + URL batch.

Usage:
    python scripts/submit_bing_sitemap.py

Requires:
  - BING_API_KEY env var (for Bing Webmaster API)
  - IndexNow key deployed at site root
"""
import json, os, re, sys, time

import requests

SITE_URL      = "https://www.pipeleap.com"
SITEMAP_URL   = "https://www.pipeleap.com/sitemap.xml"
LOCAL_SITEMAP_DIR = os.path.join(os.path.dirname(__file__), "..", "temp_frontend_repo", "public")
LOCAL_SITEMAP = os.path.join(LOCAL_SITEMAP_DIR, "sitemap.xml")
UA            = "pipeleap-seo-bot/1.0"
INDEXNOW_KEY  = "92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55"
API_BASE      = "https://ssl.bing.com/webmaster/api.svc/json"

failed = 0
api_key = os.environ.get("BING_API_KEY", "")

def _api(endpoint, method="POST", data=None):
    url = f"{API_BASE}/{endpoint}?apikey={api_key}"
    try:
        r = requests.request(method, url, json=data, timeout=30)
        result = r.json() if r.text.strip() else {}
        print(f"    HTTP {r.status_code} — {result}")
        return r.ok, result
    except Exception as e:
        print(f"    Failed: {e}")
        return False, {"error": str(e)}

def _get_all_sitemap_urls():
    """Get all URLs from local sitemap index + sub-sitemaps."""
    if not os.path.exists(LOCAL_SITEMAP):
        print("  ERROR: Local sitemap not found")
        return [], []

    with open(LOCAL_SITEMAP, "r", encoding="utf-8") as f:
        sitemap_content = f.read()

    sub_paths = re.findall(r"<loc>https://[^<]+/(sitemap-[^<]+\.xml)</loc>", sitemap_content)
    sub_urls_full = [f"https://www.pipeleap.com/{s}" for s in sub_paths]
    all_urls = []
    for sub in sub_paths:
        sub_path = os.path.join(LOCAL_SITEMAP_DIR, sub)
        if os.path.exists(sub_path):
            with open(sub_path, "r", encoding="utf-8") as f:
                sub_content = f.read()
            sub_urls = re.findall(r"<loc>(https://[^<]+)</loc>", sub_content)
            all_urls.extend(sub_urls)

    return all_urls, sub_urls_full

# ── 1. Get all URLs first ──────────────────────────────────────────
print("Loading sitemap URLs ...")
all_urls, sub_sitemap_urls = _get_all_sitemap_urls()
print(f"  {len(all_urls)} page URLs across {len(sub_sitemap_urls)} sub-sitemaps")

if not api_key:
    print("No BING_API_KEY set — can only use IndexNow")
    sys.exit(1)

# ── 2. Submit sitemap index + each sub-sitemap individually ────────
print("\n--- Submitting sitemap index + sub-sitemaps to Bing ---")

all_feeds = [SITEMAP_URL] + sub_sitemap_urls
for feed_url in all_feeds:
    name = feed_url.rsplit("/", 1)[-1]
    print(f"  SubmitFeed: {name}")
    ok, _ = _api("SubmitFeed", data={"siteUrl": SITE_URL, "feedUrl": feed_url})
    if not ok:
        failed += 1

# ── 3. FetchUrl - force Bing to immediately crawl each sub-sitemap --
print("\n--- Forcing Bing to fetch sub-sitemaps immediately ---")
for feed_url in sub_sitemap_urls:
    name = feed_url.rsplit("/", 1)[-1]
    print(f"  FetchUrl: {name}")
    ok, _ = _api("FetchUrl", data={"siteUrl": SITE_URL, "url": feed_url})
    if not ok:
        failed += 1
    time.sleep(0.5)

# ── 4. SubmitUrlBatch - push all 266 URLs directly ────────────────
print(f"\n--- Submitting {len(all_urls)} URLs via SubmitUrlBatch ---")
BATCH_SIZE = 100  # 100 per batch for reliability
ok_count = 0
for i in range(0, len(all_urls), BATCH_SIZE):
    batch = all_urls[i:i + BATCH_SIZE]
    print(f"  Batch {i//BATCH_SIZE + 1}: {len(batch)} URLs ...")
    ok, _ = _api("SubmitUrlBatch", data={"siteUrl": SITE_URL, "urlList": batch})
    if ok:
        ok_count += len(batch)
    else:
        failed += 1
    time.sleep(0.5)

print(f"\n  SubmitUrlBatch: {ok_count}/{len(all_urls)} URLs accepted")

# ── 5. IndexNow (redundant but harmless) ──────────────────────────
print("\n--- IndexNow (Bing) ---")
ok_count = 0
for i in range(0, len(all_urls), 500):
    batch = all_urls[i:i + 500]
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
            print(f"  Batch {i//500 + 1}: HTTP {r.status_code} OK ({len(batch)} URLs)")
        else:
            print(f"  Batch {i//500 + 1}: HTTP {r.status_code} — {r.text[:200]}")
            failed += 1
    except Exception as e:
        print(f"  Batch {i//500 + 1}: {e}")
        failed += 1

print(f"\nIndexNow: {ok_count}/{len(all_urls)} URLs submitted")

print(f"\n{'='*50}")
print(f"DONE — {'ALL OK' if failed == 0 else f'{failed} failures'}")
print(f"{'='*50}")
sys.exit(1 if failed > 0 else 0)
