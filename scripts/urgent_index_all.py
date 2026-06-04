"""
Urgent: Fire ALL indexing signals across ALL channels for EVERY known URL.
Run this immediately after any period of indexing inactivity.
"""
import json
import os
import sys
import time
from pathlib import Path

INDEXNOW_KEY = "92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55"
SITE_URL = "https://www.pipeleap.com"
SITEMAP_URL = f"{SITE_URL}/sitemap.xml"

def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

# ── 1. Load all URLs from sitemap ────────────────────────────────────────
def load_sitemap_urls(sitemap_path: str) -> list[str]:
    from xml.etree import ElementTree as ET
    p = Path(sitemap_path)
    if not p.exists():
        log("Sitemap not found at " + sitemap_path)
        return []
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    root = ET.fromstring(p.read_text(encoding="utf-8"))
    urls: list[str] = []
    if root.tag == f"{ns}sitemapindex":
        parent_dir = p.parent
        for sm in root.findall(f"{ns}sitemap"):
            loc = sm.find(f"{ns}loc")
            if loc is not None and loc.text:
                sub_path = parent_dir / loc.text.rstrip("/").rsplit("/", 1)[-1]
                if sub_path.exists():
                    urls.extend(load_sitemap_urls(str(sub_path)))
    elif root.tag == f"{ns}urlset":
        urls = [
            u.find(f"{ns}loc").text
            for u in root.findall(f"{ns}url")
            if u.find(f"{ns}loc") is not None and u.find(f"{ns}loc").text
        ]
    return urls

# ── 2. IndexNow ──────────────────────────────────────────────────────────
def submit_indexnow(urls: list[str]) -> dict:
    import requests
    results = {}
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
                    "keyLocation": f"{SITE_URL}/{INDEXNOW_KEY}.txt",
                    "urlList": urls[:500],
                },
                timeout=15,
            )
            ok = r.status_code in (200, 202, 204)
            results[hub] = {"status": r.status_code, "ok": ok}
            log(f"IndexNow {hub}: HTTP {r.status_code} ({'OK' if ok else 'FAIL'})")
        except Exception as e:
            results[hub] = {"error": str(e)[:80]}
            log(f"IndexNow {hub}: ERROR {e}")
    return results

# ── 3. WebSub ────────────────────────────────────────────────────────────
def submit_websub() -> dict:
    import requests
    try:
        r = requests.post(
            "https://pubsubhubbub.appspot.com/",
            data={"hub.mode": "publish", "hub.url": SITEMAP_URL},
            timeout=10,
        )
        ok = r.status_code == 204
        log(f"WebSub: HTTP {r.status_code} ({'OK' if ok else 'FAIL'})")
        return {"ok": ok, "status": r.status_code}
    except Exception as e:
        log(f"WebSub: ERROR {e}")
        return {"ok": False, "error": str(e)[:80]}

# ── 4. GSC sitemap submission ───────────────────────────────────────────
def submit_gsc_sitemap(config_path: str) -> dict:
    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from connectors.gsc_connector import GoogleSearchConsoleConnector
        import logging
        gsc = GoogleSearchConsoleConnector(config, logging.getLogger("urgent"))
        result = gsc.submit_sitemap(SITEMAP_URL)
        log(f"GSC sitemap: {result}")
        return result
    except Exception as e:
        log(f"GSC sitemap: ERROR {e}")
        return {"ok": False, "error": str(e)[:200]}

# ── 5. Google Indexing API (top 20 priority URLs) ───────────────────────
def submit_indexing_api(config_path: str, priority_urls: list[str]) -> list[dict]:
    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from connectors.gsc_connector import GoogleSearchConsoleConnector
        import logging
        gsc = GoogleSearchConsoleConnector(config, logging.getLogger("urgent"))
        results = gsc.request_indexing(priority_urls[:20])
        ok = sum(1 for r in results if r.get("ok"))
        log(f"Indexing API: {ok}/{len(results)} accepted")
        return results
    except Exception as e:
        log(f"Indexing API: ERROR {e}")
        return []

# ── 6. URL Inspection on homepage ────────────────────────────────────────
def inspect_homepage(config_path: str) -> dict:
    try:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from connectors.gsc_connector import GoogleSearchConsoleConnector
        import logging
        gsc = GoogleSearchConsoleConnector(config, logging.getLogger("urgent"))
        result = gsc.inspect_url(SITE_URL + "/")
        log(f"Homepage inspection: {result.get('ok')}")
        if result.get("ok"):
            verdict = result["result"].get("inspectionResult", {}).get("indexStatusResult", {})
            log(f"  coverageState={verdict.get('coverageState')} indexState={verdict.get('indexingState')}")
        return result
    except Exception as e:
        log(f"Homepage inspection: ERROR {e}")
        return {"ok": False, "error": str(e)[:200]}

# ── Main ──────────────────────────────────────────────────────────────────
def main():
    log("=" * 50)
    log("URGENT: Firing all indexing signals")
    log("=" * 50)

    sitemap_path = str(Path(__file__).resolve().parent.parent / "temp_frontend_repo" / "public" / "sitemap.xml")
    config_path = str(Path(__file__).resolve().parent.parent / "config.yaml")

    all_urls = load_sitemap_urls(sitemap_path)
    log(f"Loaded {len(all_urls)} URLs from sitemap")

    # Priority: homepage + blog posts first
    priority_urls = [u for u in all_urls if any(p in u for p in ["/blog/", "/glossary/", "/tools/"])]
    priority_urls = [SITE_URL + "/"] + [u for u in priority_urls if u != SITE_URL + "/"]
    log(f"Priority URLs: {len(priority_urls)}")

    report: dict = {
        "run_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_urls": len(all_urls),
        "priority_urls": len(priority_urls),
    }

    # 1. IndexNow (all URLs)
    log("\n--- IndexNow ---")
    report["indexnow"] = submit_indexnow(all_urls)

    # 2. WebSub
    log("\n--- WebSub ---")
    report["websub"] = submit_websub()

    # 3. GSC sitemap
    log("\n--- GSC Sitemap ---")
    report["gsc_sitemap"] = submit_gsc_sitemap(config_path)

    # 4. Google Indexing API
    log("\n--- Google Indexing API ---")
    report["google_indexing_api"] = submit_indexing_api(config_path, priority_urls)

    # 5. Homepage URL Inspection
    log("\n--- Homepage Inspection ---")
    report["homepage_inspection"] = inspect_homepage(config_path)

    # Save report
    out_dir = Path(__file__).resolve().parent.parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "urgent_indexing_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log(f"\nReport saved to {report_path}")

    log("\n" + "=" * 50)
    log("DONE")
    log("=" * 50)

if __name__ == "__main__":
    main()
