"""
Submit sitemap to Bing Webmaster Tools via API.

Usage:
  BING_WEBMASTER_API_KEY=your_key python scripts/submit_bing_sitemap.py

API key: Bing Webmaster Tools → Settings → API access
"""
import os, sys
import requests

SITE_URL    = "https://www.pipeleap.com/"
SITEMAP_URL = "https://www.pipeleap.com/sitemap.xml"
API_KEY     = os.getenv("BING_WEBMASTER_API_KEY", "")

if not API_KEY:
    print("ERROR: Set BING_WEBMASTER_API_KEY env var first.")
    print("  Find it in Bing Webmaster Tools → Settings → API access")
    sys.exit(1)

print(f"Submitting sitemap to Bing Webmaster Tools ...")
print(f"  Site:    {SITE_URL}")
print(f"  Sitemap: {SITEMAP_URL}")

r = requests.post(
    "https://ssl.bing.com/webmaster/api.svc/json/SubmitSitemap",
    params={"apikey": API_KEY, "siteUrl": SITE_URL},
    json={"sitemapUrl": SITEMAP_URL},
    headers={"Content-Type": "application/json"},
    timeout=15,
)

if r.status_code == 200:
    print(f"  [OK] Sitemap submitted. HTTP {r.status_code}")
    print(f"  Response: {r.text[:200]}")
else:
    print(f"  [FAIL] HTTP {r.status_code}: {r.text[:300]}")
    sys.exit(1)

# Also submit via IndexNow (Bing endpoint)
print("\nSubmitting all URLs via IndexNow to Bing ...")
import re
resp = requests.get(SITEMAP_URL, timeout=15)
urls = re.findall(r"<loc>(https://[^<]+)</loc>", resp.text)
urls = [re.sub(r"<.*", "", u).strip() for u in urls]
print(f"  {len(urls)} URLs from sitemap")

payload = {
    "host": "www.pipeleap.com",
    "key": "pipeleap-indexnow-2026",
    "keyLocation": "https://www.pipeleap.com/pipeleap-indexnow-2026.txt",
    "urlList": urls,
}
r2 = requests.post("https://www.bing.com/indexnow", json=payload, timeout=20)
print(f"  IndexNow HTTP {r2.status_code}: {r2.text[:150]}")
