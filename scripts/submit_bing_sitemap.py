"""
Submit sitemap URLs to Bing via IndexNow (free, no API key needed).

Usage:
    python scripts/submit_bing_sitemap.py

The IndexNow key file must be deployed at the site root:
    https://www.pipeleap.com/92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55.txt
"""
import re, sys
import requests

SITE_URL    = "https://www.pipeleap.com"
SITEMAP_URL = "https://www.pipeleap.com/sitemap.xml"
INDEXNOW_KEY = "92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55"

# Fetch all URLs from the live sitemap
print("Fetching sitemap URLs ...")
resp = requests.get(SITEMAP_URL, timeout=15)
resp.raise_for_status()
urls = re.findall(r"<loc>(https://[^<]+)</loc>", resp.text)
urls = [re.sub(r"<.*", "", u).strip() for u in urls]
print(f"  {len(urls)} URLs found\n")

# Submit to Bing IndexNow endpoint
print(f"Submitting {len(urls)} URLs to Bing IndexNow ...")
payload = {
    "host": "www.pipeleap.com",
    "key": INDEXNOW_KEY,
    "keyLocation": f"https://www.pipeleap.com/{INDEXNOW_KEY}.txt",
    "urlList": urls,
}
r = requests.post("https://www.bing.com/indexnow", json=payload, timeout=20)
ok = r.status_code in (200, 202)
print(f"  HTTP {r.status_code}  {'OK' if ok else 'FAILED'}")
if ok:
    print(f"  URLs submitted to Bing IndexNow successfully.")
else:
    print(f"  Error: {r.text[:300]}")
    sys.exit(1)
