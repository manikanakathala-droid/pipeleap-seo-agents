import os
import re
import requests
import base64
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

API = "https://api.github.com"

class SitemapRegenerator:
    def __init__(self, token: str, repo: str, branch: str = "main"):
        self.token = token
        self.repo = repo
        self.branch = branch

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _get_file(self, path: str) -> tuple[str, str]:
        url = f"{API}/repos/{self.repo}/contents/{path}"
        resp = requests.get(url, headers=self._headers(), params={"ref": self.branch}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        decoded = base64.b64decode(data["content"]).decode("utf-8")
        return decoded, data["sha"]

    def _update_file(self, path: str, content: str, sha: str, message: str) -> bool:
        url = f"{API}/repos/{self.repo}/contents/{path}"
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "sha": sha,
            "branch": self.branch,
        }
        resp = requests.put(url, headers=self._headers(), json=payload, timeout=15)
        if resp.status_code in (200, 201):
            log.info("GitHub: committed %s", path)
            return True
        log.warning("GitHub commit failed %s: %s %s", path, resp.status_code, resp.text[:200])
        return False

    def _get_commit_date(self, path: str) -> str:
        url = f"{API}/repos/{self.repo}/commits"
        params = {"path": path, "sha": self.branch, "per_page": 1}
        resp = requests.get(url, headers=self._headers(), params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data and len(data) > 0:
                date_str = data[0]["commit"]["committer"]["date"]
                # Parse ISO8601 to YYYY-MM-DD
                return date_str.split("T")[0]
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def run(self):
        try:
            content, sha = self._get_file("public/sitemap.xml")
            
            blog_date = self._get_commit_date("src/data/blog-articles.ts")
            tools_date = self._get_commit_date("src/data/tools-data.ts")
            
            def replacer(match):
                url = match.group(1)
                old_lastmod = match.group(2)
                new_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                if "/blog/" in url:
                    new_date = blog_date
                elif "/tools/" in url:
                    new_date = tools_date
                return match.group(0).replace(old_lastmod, new_date)

            updated_content = re.sub(r"<url>\s*<loc>(.*?)</loc>\s*<lastmod>(.*?)</lastmod>", replacer, content)
            
            if updated_content != content:
                self._update_file("public/sitemap.xml", updated_content, sha, "chore(seo): update sitemap lastmod dates")
                log.info("Sitemap updated with correct lastmod dates")
            else:
                log.info("Sitemap lastmod dates already up to date")
                
        except Exception as e:
            log.error("Failed to regenerate sitemap: %s", e)

if __name__ == "__main__":
    import yaml
    from pathlib import Path
    config_path = Path(__file__).resolve().parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    gh_cfg = config.get("integrations", {}).get("github", {})
    token = gh_cfg.get("token") or os.getenv("GITHUB_TOKEN")
    repo = gh_cfg.get("repo")
    
    if token and repo:
        regenerator = SitemapRegenerator(token, repo, gh_cfg.get("branch", "main"))
        regenerator.run()
    else:
        log.error("GitHub token or repo not configured")
