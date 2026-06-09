"""
Submit sitemap to Bing via Webmaster API + IndexNow + URL batch.
Cleans stale feeds, dedups URL submission, and persists bing_submitted_urls.json.

Usage:
    python scripts/submit_bing_sitemap.py

Requires:
  - BING_API_KEY env var (for Bing Webmaster API)
  - IndexNow key deployed at site root
"""
import json, os, re, sys, time
from pathlib import Path

import requests

SITE_URL      = "https://www.pipeleap.com"
SITEMAP_URL   = "https://www.pipeleap.com/sitemap.xml"

# Resolve launchpad public dir — works locally (temp_frontend_repo) and in CI (pipeleap-launchpad)
_script_dir = os.path.dirname(__file__)
_launchpad_candidates = [
    os.path.join(_script_dir, "..", "temp_frontend_repo", "public"),
    os.path.join(_script_dir, "..", "pipeleap-launchpad", "public"),
    os.path.join(_script_dir, "..", "public"),
]
LOCAL_SITEMAP_DIR = next((p for p in _launchpad_candidates if os.path.isdir(p)), _launchpad_candidates[0])
LOCAL_SITEMAP = os.path.join(LOCAL_SITEMAP_DIR, "sitemap.xml")
UA            = "pipeleap-seo-bot/1.0"
INDEXNOW_KEY  = "92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55"
API_BASE      = "https://ssl.bing.com/webmaster/api.svc/json"

BING_SUBMITTED_FILE = Path("outputs/bing_submitted_urls.json")
BATCH_QUOTA = 100  # Bing's daily SubmitUrlBatch limit

# Current expected sitemap feed URLs
CURRENT_FEEDS = {
    SITEMAP_URL,
    "https://www.pipeleap.com/sitemap-pages.xml",
    "https://www.pipeleap.com/sitemap-blog.xml",
    "https://www.pipeleap.com/sitemap-tools.xml",
    "https://www.pipeleap.com/sitemap-glossary.xml",
}

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


def _load_bing_submitted():
    """Load previously Bing-submitted URLs from bing_submitted_urls.json."""
    if BING_SUBMITTED_FILE.exists():
        try:
            data = json.loads(BING_SUBMITTED_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return set(data)
        except Exception:
            pass
    return set()


def _save_bing_submitted(urls: set):
    """Persist Bing-submitted URL set to bing_submitted_urls.json."""
    BING_SUBMITTED_FILE.parent.mkdir(parents=True, exist_ok=True)
    BING_SUBMITTED_FILE.write_text(
        json.dumps(sorted(urls), indent=2), encoding="utf-8"
    )


# ── 1. Get all URLs first ──────────────────────────────────────────
print("Loading sitemap URLs ...")
all_urls, sub_sitemap_urls = _get_all_sitemap_urls()
print(f"  {len(all_urls)} page URLs across {len(sub_sitemap_urls)} sub-sitemaps")

if not api_key:
    print("No BING_API_KEY set — can only use IndexNow")
    sys.exit(1)

# ── 2. GetFeeds → RemoveFeed stale entries ──────────────────────────
print("\n--- Cleaning stale sitemap feeds from Bing ---")
ok, feeds_result = _api("GetFeeds", method="GET", data={"siteUrl": SITE_URL})
if ok and "d" in feeds_result:
    feeds = feeds_result["d"]
    if feeds:
        for feed in feeds:
            feed_url = feed.get("Url", "")
            feed_name = feed_url.rsplit("/", 1)[-1]
            if feed_url not in CURRENT_FEEDS:
                print(f"  STALE: {feed_name} — removing ...")
                rm_ok, _ = _api("RemoveFeed", data={"siteUrl": SITE_URL, "feedUrl": feed_url})
                if rm_ok:
                    print(f"    Removed {feed_name}")
                else:
                    failed += 1
            else:
                print(f"  CURRENT: {feed_name} — keeping")
    else:
        print("  No existing feeds found.")
else:
    print("  Could not list feeds.")

# ── 3. Submit sitemap index + each sub-sitemap individually ────────
print("\n--- Submitting sitemap index + sub-sitemaps to Bing ---")

all_feeds = [SITEMAP_URL] + sub_sitemap_urls
for feed_url in all_feeds:
    name = feed_url.rsplit("/", 1)[-1]
    print(f"  SubmitFeed: {name}")
    ok, _ = _api("SubmitFeed", data={"siteUrl": SITE_URL, "feedUrl": feed_url})
    if not ok:
        failed += 1

# ── 4. FetchUrl - force Bing to immediately crawl each sub-sitemap --
print("\n--- Forcing Bing to fetch sub-sitemaps immediately ---")
for feed_url in sub_sitemap_urls:
    name = feed_url.rsplit("/", 1)[-1]
    print(f"  FetchUrl: {name}")
    ok, _ = _api("FetchUrl", data={"siteUrl": SITE_URL, "url": feed_url})
    if not ok:
        failed += 1
    time.sleep(0.5)

# ── 5. SubmitUrlBatch - deduped, respects Bing's 100/day quota ────
print(f"\n--- SubmitUrlBatch (Bing quota: {BATCH_QUOTA}/day) ---")
already_submitted = _load_bing_submitted()
print(f"  Already submitted (historical): {len(already_submitted)} URLs")
fresh_urls = [u for u in all_urls if u not in already_submitted]
print(f"  Fresh (not yet submitted via SubmitUrlBatch): {len(fresh_urls)} URLs")

if fresh_urls:
    submit_batch = fresh_urls[:BATCH_QUOTA]
    print(f"  Submitting first {len(submit_batch)} URLs (quota allows {BATCH_QUOTA}) ...")
    ok, _ = _api("SubmitUrlBatch", data={"siteUrl": SITE_URL, "urlList": submit_batch})
    if ok:
        already_submitted.update(submit_batch)
        _save_bing_submitted(already_submitted)
        print(f"  ✓ {len(submit_batch)} URLs marked as submitted")
    else:
        failed += 1

    skipped = len(fresh_urls) - len(submit_batch)
    if skipped > 0:
        print(f"  ⏳ {skipped} URLs deferred to next run (quota full)")
else:
    print("  No fresh URLs to submit — all already submitted via SubmitUrlBatch before.")

print(f"\n  Total tracked in bing_submitted_urls.json: {len(already_submitted)}")

# ── 6. IndexNow (all 266, no quota) ─────────────────────────────────
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
