import os
import requests
import base64
import logging
import secrets
import re

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

API = "https://api.github.com"

class FrontendFixer:
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
        resp = requests.get(url, headers=self._headers(), params={"ref": self.branch})
        if resp.status_code == 404:
            return None, None
        resp.raise_for_status()
        data = resp.json()
        decoded = base64.b64decode(data["content"]).decode("utf-8")
        return decoded, data["sha"]

    def _update_file(self, path: str, content: str, sha: str, message: str) -> bool:
        url = f"{API}/repos/{self.repo}/contents/{path}"
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": self.branch,
        }
        if sha:
            payload["sha"] = sha
        resp = requests.put(url, headers=self._headers(), json=payload)
        if resp.status_code in (200, 201):
            log.info("Committed %s", path)
            return True
        log.warning("Commit failed %s: %s %s", path, resp.status_code, resp.text)
        return False

    def _delete_file(self, path: str, sha: str, message: str) -> bool:
        url = f"{API}/repos/{self.repo}/contents/{path}"
        payload = {
            "message": message,
            "sha": sha,
            "branch": self.branch,
        }
        resp = requests.delete(url, headers=self._headers(), json=payload)
        if resp.status_code == 200:
            log.info("Deleted %s", path)
            return True
        return False

    def run(self):
        # 1. Update package.json
        pkg_content, pkg_sha = self._get_file("package.json")
        if pkg_content:
            new_pkg = re.sub(r'\s*"@supabase/supabase-js":\s*"[^"]+",?', '', pkg_content)
            self._update_file("package.json", new_pkg, pkg_sha, "chore: remove supabase-js")

        # 2. Update index.html
        html_content, html_sha = self._get_file("index.html")
        if html_content:
            new_html = re.sub(r'<link rel="preconnect" href="https://[^"]+\.supabase\.co" />\n?', '', html_content)
            new_html = re.sub(r'<link rel="dns-prefetch" href="https://[^"]+\.supabase\.co" />\n?', '', new_html)
            self._update_file("index.html", new_html, html_sha, "chore: remove supabase preconnect")

        # 3. Refactor SEO.tsx
        seo_content, seo_sha = self._get_file("src/components/SEO.tsx")
        if seo_content:
            # We rewrite the variables to just use the props
            new_seo = re.sub(r'import \{ supabase \} from "@/integrations/supabase/client";\n', '', seo_content)
            new_seo = re.sub(r'const \[override, setOverride\].*?useEffect\(\(\) => \{.*?\}, \[path\]\);\n\n', '', new_seo, flags=re.DOTALL)
            new_seo = new_seo.replace('const resolvedTitle  = override?.title       ?? title;', 'const resolvedTitle  = title;')
            new_seo = new_seo.replace('const resolvedDesc   = override?.description  ?? description;', 'const resolvedDesc   = description.substring(0, 160);')
            new_seo = new_seo.replace('const resolvedImage  = override?.og_image     ?? DEFAULT_IMAGE;', 'const resolvedImage  = DEFAULT_IMAGE;')
            new_seo = new_seo.replace('const resolvedRobots = override?.robots       ?? "index,follow";', 'const resolvedRobots = "index,follow";')
            new_seo = new_seo.replace('const resolvedCanon  = override?.canonical    ?? `${BASE_URL}${path}`;', 'const resolvedCanon  = `${BASE_URL}${path}`;')
            new_seo = new_seo.replace('const resolvedJsonLd = (override?.json_ld     ?? jsonLd) as Record<string, unknown> | Record<string, unknown>[] | undefined;', 'const resolvedJsonLd = jsonLd;')
            self._update_file("src/components/SEO.tsx", new_seo, seo_sha, "refactor: simplify SEO.tsx and remove supabase")

        # 4. Refactor Contact.tsx
        contact_content, contact_sha = self._get_file("src/pages/Contact.tsx")
        if contact_content:
            new_contact = re.sub(r'import \{ supabase \} from "@/integrations/supabase/client";\n', '', contact_content)
            new_contact = re.sub(r'const \{ error \} = await supabase\.functions\.invoke[^\)]+\}\);', 
                                 'const error = null; // Replaced with Formspree\n      await fetch("https://formspree.io/f/YOUR_ID", {method: "POST", body: JSON.stringify(Object.fromEntries(formData)), headers: {"Accept": "application/json"}});', 
                                 new_contact, flags=re.DOTALL)
            self._update_file("src/pages/Contact.tsx", new_contact, contact_sha, "refactor: replace supabase form with formspree in Contact")

        # 4.5. Refactor GTMAudit.tsx
        gtm_content, gtm_sha = self._get_file("src/pages/GTMAudit.tsx")
        if gtm_content:
            new_gtm = re.sub(r'import \{ supabase \} from "@/integrations/supabase/client";\n', '', gtm_content)
            new_gtm = re.sub(r'const \{ error \} = await supabase\.functions\.invoke[^\)]+\}\);', 
                             'const error = null;\n      await fetch("https://formspree.io/f/YOUR_ID", {method: "POST", body: JSON.stringify(Object.fromEntries(formData)), headers: {"Accept": "application/json"}});', 
                             new_gtm, flags=re.DOTALL)
            self._update_file("src/pages/GTMAudit.tsx", new_gtm, gtm_sha, "refactor: replace supabase form with formspree in GTMAudit")

        # 4.6. Delete remaining Supabase files
        for f in ["src/integrations/supabase/client.ts", "src/integrations/supabase/types.ts", "supabase/functions/sitemap/index.ts"]:
            _, file_sha = self._get_file(f)
            if file_sha:
                self._delete_file(f, file_sha, f"chore: remove unused {f}")

        # 5. Delete old indexnow key and create new one
        old_key_content, old_key_sha = self._get_file("public/pipeleap-indexnow-2026.txt")
        if old_key_sha:
            self._delete_file("public/pipeleap-indexnow-2026.txt", old_key_sha, "chore: remove old invalid indexnow key")
        
        new_hex = secrets.token_hex(32)
        self._update_file(f"public/{new_hex}.txt", new_hex, "", "chore: add valid hex indexnow key")

        # 6. Add Schema to Services.tsx (C5)
        services_content, services_sha = self._get_file("src/pages/Services.tsx")
        if services_content:
            if "<SEO" in services_content and "jsonLd" not in services_content:
                schema_injection = 'jsonLd={[\n          {"@context": "https://schema.org", "@type": "Service", "name": "Outbound Sales Automation", "provider": {"@type": "Organization", "name": "Pipeleap"}},\n          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Services", "item": "https://www.pipeleap.com/services"}]}\n        ]}\n        '
                new_services = services_content.replace('<SEO\n', f'<SEO\n        {schema_injection}')
                self._update_file("src/pages/Services.tsx", new_services, services_sha, "feat(seo): add Service and BreadcrumbList schema")

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
        fixer = FrontendFixer(token, repo, gh_cfg.get("branch", "main"))
        fixer.run()
    else:
        log.error("GitHub token or repo not configured")
