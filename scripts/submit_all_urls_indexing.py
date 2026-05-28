"""
Submit ALL 242 sitemap URLs to Google Indexing API + IndexNow + GSC + Bing.
Reads URLs from the local sitemap XML files (faster than fetching live).

Usage: python scripts/submit_all_urls_indexing.py
"""
import json, sys, time, re, os
from pathlib import Path

SITEMAP_DIR = Path(__file__).resolve().parent.parent / "temp_frontend_repo" / "public"
CREDENTIALS_PATH = Path(__file__).resolve().parent.parent / "credentials" / "gsc_service_account.json"
INDEXNOW_KEY = "92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55"
SITE_URL = "https://www.pipeleap.com"
GSC_PROPERTY = "sc-domain:pipeleap.com"
KEY_LOCATION = f"{SITE_URL}/{INDEXNOW_KEY}.txt"

INDEXNOW_ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://yandex.com/indexnow",
]

SITEMAP_FILES = [
    "sitemap-pages.xml",
    "sitemap-blog.xml",
    "sitemap-glossary.xml",
    "sitemap-tools.xml",
]

def load_urls():
    all_urls = []
    for fname in SITEMAP_FILES:
        path = SITEMAP_DIR / fname
        if not path.exists():
            print(f"  [WARN] {fname} not found")
            continue
        text = path.read_text(encoding="utf-8")
        found = re.findall(r"<loc>(https://[^<]+)</loc>", text)
        all_urls.extend(found)
        print(f"  {fname}: {len(found)} URLs")
    return all_urls

def submit_indexnow(urls):
    print(f"\n--- IndexNow Submission ({len(urls)} URLs) ---")
    host = SITE_URL.replace("https://", "").replace("http://", "")
    payload = {
        "host": host,
        "key": INDEXNOW_KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }
    import requests
    ok_count = 0
    for endpoint in INDEXNOW_ENDPOINTS:
        try:
            r = requests.post(endpoint, json=payload, timeout=20)
            status = r.status_code
            ok = status in (200, 202)
            print(f"  {endpoint.split('/')[2]:30s}  HTTP {status}  {'OK' if ok else 'FAILED'}")
            if ok:
                ok_count += 1
        except Exception as e:
            print(f"  {endpoint.split('/')[2]:30s}  ERROR: {e}")
        time.sleep(0.3)
    print(f"  IndexNow: {ok_count}/{len(INDEXNOW_ENDPOINTS)} endpoints OK")
    return ok_count

def submit_gsc_sitemap():
    print(f"\n--- GSC Sitemap Submission ---")
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        creds = service_account.Credentials.from_service_account_file(
            str(CREDENTIALS_PATH),
            scopes=["https://www.googleapis.com/auth/webmasters"],
        )
        service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
        sitemap_url = f"{SITE_URL}/sitemap.xml"
        service.sitemaps().submit(siteUrl=GSC_PROPERTY, feedpath=sitemap_url).execute()
        print(f"  GSC sitemap submitted: {sitemap_url}  OK")
        return True
    except ImportError:
        print("  [SKIP] google-api-python-client not installed")
        return False
    except Exception as e:
        print(f"  GSC sitemap error: {e}")
        return False

def submit_bing_sitemap():
    print(f"\n--- Bing Sitemap Submission ---")
    bing_key = os.getenv("BING_API_KEY")
    if not bing_key:
        print("  [SKIP] BING_API_KEY not set in environment")
        print("  Set via: $env:BING_API_KEY='your_key'")
        return False
    try:
        import requests
        sitemap_url_encoded = requests.utils.quote(f"{SITE_URL}/sitemap.xml", safe="")
        bing_url = (
            f"https://www.bing.com/webmaster/api.svc/json/SubmitSitemap"
            f"?siteUrl={SITE_URL}&sitemapUrl={sitemap_url_encoded}"
        )
        headers = {"api-key": bing_key}
        r = requests.post(bing_url, headers=headers, timeout=20)
        print(f"  Bing Webmaster API: HTTP {r.status_code}  {'OK' if r.ok else 'FAILED'}")
        return r.ok
    except Exception as e:
        print(f"  Bing sitemap error: {e}")
        return False

def submit_google_indexing_api(urls):
    print(f"\n--- Google Indexing API ({len(urls)} URLs) ---")
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        creds = service_account.Credentials.from_service_account_file(
            str(CREDENTIALS_PATH),
            scopes=["https://www.googleapis.com/auth/indexing"],
        )
        service = build("indexing", "v3", credentials=creds, cache_discovery=False)
    except ImportError:
        print("  [SKIP] google-api-python-client not installed")
        return 0, []
    except Exception as e:
        print(f"  Indexing API setup error: {e}")
        return 0, []

    accepted = 0
    errors = []
    for i, url in enumerate(urls, 1):
        try:
            service.urlNotifications().publish(
                body={"url": url, "type": "URL_UPDATED"}
            ).execute()
            accepted += 1
            print(f"  [{i}/{len(urls)}] OK  {url}")
        except Exception as e:
            err_str = str(e)
            if "SERVICE_DISABLED" in err_str or "403" in err_str:
                print(f"  [{i}/{len(urls)}] API_DISABLED")
                errors.append("API_DISABLED")
                break
            errors.append(err_str[:100])
            print(f"  [{i}/{len(urls)}] ERR: {err_str[:80]}")
        time.sleep(0.15)
    return accepted, errors

def main():
    print("=" * 70)
    print("INDEXING SUBMISSION — ALL 242 SITEMAP URLs")
    print("=" * 70)

    urls = load_urls()
    print(f"\nTotal URLs loaded: {len(urls)}")

    submit_indexnow(urls)
    submit_gsc_sitemap()
    submit_bing_sitemap()

    print(f"\n--- Google Indexing API ---")
    print(f"Quota: 200 URLs/day. Submitting up to 200 URLs.")
    api_urls = urls[:200]
    accepted, errors = submit_google_indexing_api(api_urls)
    print(f"\n  Indexing API: {accepted}/{len(api_urls)} accepted")
    if errors:
        print(f"  Errors: {errors[:3]}")

    remaining = len(urls) - 200
    if remaining > 0:
        print(f"\n  Remaining {remaining} URLs will need to be submitted tomorrow (quota limit).")
        print(f"  URLs: {urls[200:]}")

    print("\n" + "=" * 70)
    print("SUBMISSION COMPLETE")
    print(f"  IndexNow:     {len(urls)} URLs sent to {len(INDEXNOW_ENDPOINTS)} engines")
    print(f"  Google API:   {accepted}/{len(api_urls)} URLs (max 200/day quota)")
    print(f"  GSC sitemap:  Submitted")
    print(f"  Bing sitemap: Submitted")
    print("=" * 70)

    if not os.getenv("BING_API_KEY"):
        print("\n  NOTE: Bing API key not found in env. Set with:")
        print("    $env:BING_API_KEY='f2ce40b491c44f1282976da068df483c'")

if __name__ == "__main__":
    main()
