"""
Audit Google index status for all sitemap URLs using URL Inspection API.

Usage: python scripts/audit_index_status.py

Requires: credentials/gsc_service_account.json with GSC "Full" permission
          pip install google-api-python-client google-auth
"""
import json, os, sys, time, re
from pathlib import Path
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

SITEMAP_DIR = Path(__file__).resolve().parent.parent / "temp_frontend_repo" / "public"
CREDENTIALS_PATH = Path(__file__).resolve().parent.parent / "credentials" / "gsc_service_account.json"
GSC_PROPERTY = "sc-domain:pipeleap.com"
SLEEP_SEC = 0.1
MAX_WORKERS = 5

SITEMAP_FILES = [
    "sitemap-pages.xml",
    "sitemap-blog.xml",
    "sitemap-glossary.xml",
    "sitemap-tools.xml",
]

def load_urls():
    urls_by_type = {}
    for fname in SITEMAP_FILES:
        path = SITEMAP_DIR / fname
        if not path.exists():
            print(f"  [WARN] {fname} not found at {path}")
            continue
        text = path.read_text(encoding="utf-8")
        found = re.findall(r"<loc>(https://[^<]+)</loc>", text)
        ptype = fname.replace("sitemap-", "").replace(".xml", "")
        urls_by_type[ptype] = found
    return urls_by_type

def get_credentials():
    from google.oauth2 import service_account
    scopes = ["https://www.googleapis.com/auth/webmasters"]
    return service_account.Credentials.from_service_account_file(
        str(CREDENTIALS_PATH), scopes=scopes
    )

def build_service():
    creds = get_credentials()
    from googleapiclient.discovery import build
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)

def short_label(state):
    if not state:
        return "UNKNOWN"
    sl = state.lower()
    if "indexed" in sl and "submitted" in sl:
        return "INDEXED"
    if "indexed" in sl and "crawled" not in sl:
        return "INDEXED"
    if "crawled" in sl and "not indexed" in sl:
        return "CRAWLED_NOT_INDEXED"
    if "discovered" in sl:
        return "DISCOVERED"
    if "not found" in sl or "404" in sl:
        return "NOT_FOUND"
    if "soft 404" in sl:
        return "SOFT_404"
    if "redirect" in sl:
        return "REDIRECT"
    if "noindex" in sl:
        return "BLOCKED_NOINDEX"
    if "robots" in sl:
        return "BLOCKED_ROBOTS"
    if "duplicate" in sl and "canonical" in sl:
        return "DUPLICATE_CANONICAL"
    if "duplicate" in sl:
        return "DUPLICATE"
    if "error" in sl:
        return "PAGE_ERROR"
    if "anomaly" in sl:
        return "CRAWL_ANOMALY"
    return state[:30]

def needs_attention(label):
    return label in (
        "CRAWLED_NOT_INDEXED", "DISCOVERED", "NOT_FOUND", "SOFT_404",
        "REDIRECT", "BLOCKED_NOINDEX", "BLOCKED_ROBOTS",
        "PAGE_ERROR", "CRAWL_ANOMALY",
    )

def inspect_url(service, url):
    try:
        from googleapiclient.http import HttpRequest
        request = service.urlInspection().index().inspect(
            body={"inspectionUrl": url, "siteUrl": GSC_PROPERTY}
        )
        result = request.execute()
        inspected = result.get("inspectionResult", {})
        status = inspected.get("indexStatusResult", {})
        raw_state = status.get("coverageState", "UNKNOWN")
        return {
            "ok": True,
            "coverageState": raw_state,
            "label": short_label(raw_state),
            "indexingState": status.get("indexingState", "UNKNOWN"),
            "crawledAs": status.get("crawledAs", ""),
            "googleCanonical": status.get("googleCanonical", ""),
            "pageFetchState": inspected.get("siteFetchResult", {}).get("fetchState", ""),
            "robotsTxtState": inspected.get("robotsTxtResult", {}).get("robotsTxtState", ""),
            "verdict": inspected.get("verdict", ""),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def main():
    print("=" * 70)
    print("GOOGLE INDEX STATUS AUDIT")
    print("=" * 70)

    urls_by_type = load_urls()
    all_urls = []
    for ptype, urls in urls_by_type.items():
        for u in urls:
            all_urls.append((ptype, u))
    total = len(all_urls)
    print(f"\nFound {total} URLs across {len(urls_by_type)} sitemaps:")
    for ptype, urls in urls_by_type.items():
        print(f"  {ptype}: {len(urls)}")

    print(f"\nAuthenticating with service account...")
    if not CREDENTIALS_PATH.exists():
        print(f"  [ERROR] Credentials not found at {CREDENTIALS_PATH}")
        sys.exit(1)

    print(f"\nInspecting {total} URLs with {MAX_WORKERS} concurrent workers...")
    results = [None] * total
    errors = 0
    done_count = 0
    batch_start = time.time()

    def process_one(ptype, url, idx):
        svc = build_service()
        res = inspect_url(svc, url)
        res["type"] = ptype
        res["url"] = url
        return idx, res

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        fut_map = {}
        for idx, (ptype, url) in enumerate(all_urls):
            time.sleep(SLEEP_SEC)
            fut = pool.submit(process_one, ptype, url, idx)
            fut_map[fut] = idx

        for fut in as_completed(fut_map):
            idx, res = fut.result()
            results[idx] = res
            done_count += 1
            if not res["ok"]:
                errors += 1
            elapsed = time.time() - batch_start
            label = res.get("label", res.get("coverageState", "ERROR"))
            truncated = res["url"][:55]
            rate = done_count / max(elapsed, 1)
            eta = (total - done_count) / max(rate, 1)
            sys.stdout.write(
                f"\r  [{done_count}/{total}] {label:25s} {truncated:55s} "
                f"({rate:.1f}/s, ETA {eta:.0f}s)"
            )
            sys.stdout.flush()

    elapsed = time.time() - batch_start
    print(f"\n\nAudit finished in {elapsed:.0f}s")
    ok_results = [r for r in results if r["ok"]]

    print(f"\n{'='*70}")
    print(f"AUDIT COMPLETE: {total} URLs checked, {errors} errors, {len(ok_results)} inspected")
    print(f"{'='*70}")

    by_label = Counter(r["label"] for r in ok_results)
    by_category = defaultdict(Counter)
    for r in ok_results:
        by_category[r["type"]][r["label"]] += 1

    print(f"\n--- OVERALL INDEX STATUS ---")
    for lbl, count in by_label.most_common():
        pct = count / len(ok_results) * 100
        print(f"  {lbl:30s} {count:3d} ({pct:5.1f}%)")

    indexed = sum(1 for r in ok_results if r["label"] == "INDEXED")
    not_indexed = sum(1 for r in ok_results if r["label"] in ("CRAWLED_NOT_INDEXED", "DISCOVERED"))
    excluded = sum(1 for r in ok_results if r["label"] in
                   ("NOT_FOUND", "SOFT_404", "REDIRECT", "BLOCKED_NOINDEX",
                    "BLOCKED_ROBOTS", "DUPLICATE", "DUPLICATE_CANONICAL",
                    "PAGE_ERROR", "CRAWL_ANOMALY"))
    other = len(ok_results) - indexed - not_indexed - excluded
    print(f"\n  {'INDEXED':30s} {indexed:3d} ({indexed/max(len(ok_results),1)*100:.1f}%)")
    print(f"  {'NOT INDEXED (queued)':30s} {not_indexed:3d} ({not_indexed/max(len(ok_results),1)*100:.1f}%)")
    print(f"  {'EXCLUDED / PROBLEM':30s} {excluded:3d} ({excluded/max(len(ok_results),1)*100:.1f}%)")
    print(f"  {'OTHER':30s} {other:3d} ({other/max(len(ok_results),1)*100:.1f}%)")

    print(f"\n--- BY PAGE TYPE ---")
    for ptype in ["pages", "blog", "glossary", "tools"]:
        if ptype not in by_category:
            continue
        counts = by_category[ptype]
        t = sum(counts.values())
        print(f"\n  [{ptype.upper()} - {t} pages]")
        for lbl, c in counts.most_common():
            print(f"    {lbl:30s} {c:3d}")

    attention_urls = [r for r in ok_results if needs_attention(r["label"])]
    if attention_urls:
        print(f"\n--- URLs THAT NEED ATTENTION ({len(attention_urls)} total) ---")
        for r in attention_urls:
            print(f"  [{r['label']:25s}] ({r['type']:6s}) {r['url']}")

    summary_path = Path("outputs") / "index_audit_report.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "total": len(results),
        "errors": errors,
        "inspected": len(ok_results),
        "indexed": indexed,
        "not_indexed_queued": not_indexed,
        "excluded": excluded,
        "other": other,
        "by_label": dict(by_label.most_common()),
        "by_page_type": {k: dict(v.most_common()) for k, v in by_category.items()},
        "attention_urls": [
            {"url": r["url"], "type": r["type"], "label": r["label"],
             "coverageState": r.get("coverageState", "")}
            for r in attention_urls
        ],
        "details": [
            {
                "url": r["url"],
                "type": r["type"],
                "label": r.get("label", r.get("coverageState", "ERROR")),
                "coverageState": r.get("coverageState", "ERROR"),
            }
            for r in results
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nFull report saved to: {summary_path}")

if __name__ == "__main__":
    main()
