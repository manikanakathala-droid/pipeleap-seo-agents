"""
Index a newly published blog to all search engines.
Usage: python scripts/index_blog.py <blog_url>
"""
import json, os, sys, requests

BLOG_URL = sys.argv[1] if len(sys.argv) > 1 else "https://www.pipeleap.com/blog/gtm-strategy-saas-pipeleap"
SITEMAP_URL = "https://www.pipeleap.com/sitemap.xml"
INDEXNOW_KEY = "92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55"

results = []

print("--- IndexNow ---")
for hub in [
    "https://api.indexnow.org",
    "https://www.bing.com/indexnow",
    "https://yandex.com/indexnow",
]:
    try:
        r = requests.post(
            hub,
            json={
                "host": "www.pipeleap.com",
                "key": INDEXNOW_KEY,
                "keyLocation": f"https://www.pipeleap.com/{INDEXNOW_KEY}.txt",
                "urlList": [BLOG_URL],
            },
            timeout=15,
        )
        ok = r.status_code in (200, 202)
        status = f"HTTP {r.status_code} ({'OK' if ok else 'FAIL'})"
        print(f"  {hub}: {status}")
        results.append({"hub": hub, "status": r.status_code, "ok": ok})
    except Exception as e:
        print(f"  {hub}: ERROR {e}")
        results.append({"hub": hub, "error": str(e)})

print()
print("--- Google Indexing API ---")
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        "credentials/gsc_service_account.json",
        scopes=["https://www.googleapis.com/auth/indexing"],
    )
    svc = build("indexing", "v3", credentials=creds, cache_discovery=False)
    body = {"url": BLOG_URL, "type": "URL_UPDATED"}
    resp = svc.urlNotifications().publish(body=body).execute()
    meta = resp.get("urlNotificationMetadata", {})
    url = meta.get("latestUpdate", {}).get("url", "") or meta.get("latestRemove", {}).get("url", "")
    print(f"  OK: {url}")
    results.append({"google_indexing_api": "OK", "url": url})
except Exception as e:
    print(f"  ERROR: {e}")
    results.append({"google_indexing_api": "ERROR", "error": str(e)[:200]})

print()
print("--- GSC Sitemap Submit ---")
try:
    creds2 = service_account.Credentials.from_service_account_file(
        "credentials/gsc_service_account.json",
        scopes=["https://www.googleapis.com/auth/webmasters"],
    )
    svc2 = build("searchconsole", "v1", credentials=creds2, cache_discovery=False)
    svc2.sitemaps().submit(siteUrl="sc-domain:pipeleap.com", feedpath=SITEMAP_URL).execute()
    print("  OK")
    results.append({"gsc_sitemap": "OK"})
except Exception as e:
    print(f"  ERROR: {e}")
    results.append({"gsc_sitemap": "ERROR", "error": str(e)[:200]})

print()
print("--- WebSub ---")
try:
    r = requests.post(
        "https://pubsubhubbub.appspot.com",
        data={"hub.url": SITEMAP_URL, "hub.mode": "publish"},
        timeout=15,
    )
    print(f"  HTTP {r.status_code}")
    results.append({"websub": r.status_code})
except Exception as e:
    print(f"  ERROR: {e}")
    results.append({"websub": "ERROR", "error": str(e)[:200]})

print()
print(json.dumps(results, indent=2))
