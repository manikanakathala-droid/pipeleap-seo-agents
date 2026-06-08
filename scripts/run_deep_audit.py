"""Run deep SEO audit locally."""

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.WARNING, stream=sys.stdout)
logger = logging.getLogger(__name__)

from connectors.crawler import SiteCrawler
from core.audit_engine import AuditEngine

print("=== PHASE 3: Deep SEO Audit ===")
print("Crawling www.pipeleap.com...")
crawler = SiteCrawler({"site_url": "https://www.pipeleap.com"}, logger)
report = crawler.crawl("https://www.pipeleap.com", max_pages=80, max_depth=2)
print(f"Crawled {len(report.pages)} pages, {len(report.crawl_errors)} errors")

for p in report.pages[:10]:
    title = (p.title or "")[:60]
    print(f"  {p.status_code} {p.url} [{title}]")

print("\nRunning AuditEngine with all checks...")
engine = AuditEngine(
    {"integrations": {"pagespeed": {"api_key": ""}}}, logger
)
issues = engine.run(report)
issues.sort(key=lambda x: x.impact_score, reverse=True)

critical = [i for i in issues if i.severity == "critical"]
high = [i for i in issues if i.severity == "high"]
medium = [i for i in issues if i.severity == "medium"]
low = [i for i in issues if i.severity == "low"]

print(f"\n=== {len(issues)} Issues ===")
print(f"Critical: {len(critical)}, High: {len(high)}, Medium: {len(medium)}, Low: {len(low)}")

for i, issue in enumerate(issues[:40], 1):
    print(
        f"{i:>2}. [{issue.severity.upper():>8}] "
        f"[{issue.category:>18}] [score={issue.impact_score:>2}] "
        f"{issue.title}"
    )

out_dir = Path("outputs")
out_dir.mkdir(exist_ok=True)
output = []
for i in issues:
    d = {
        "title": i.title,
        "severity": i.severity,
        "category": i.category,
        "impact_score": i.impact_score,
        "description": i.description,
    }
    try:
        d["affected_urls"] = list(i.affected_urls) if i.affected_urls else []
    except AttributeError:
        d["affected_urls"] = []
    output.append(d)

(out_dir / "deep_audit_results.json").write_text(
    json.dumps(output, indent=2, default=str), encoding="utf-8"
)
print("\nSaved to outputs/deep_audit_results.json")
