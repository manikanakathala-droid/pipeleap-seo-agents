# Changing the website

The site is plain static HTML in `manikanakathala-droid/Pipeleap-web-redesign`, deployed by Vercel from its default branch. Changes go through a pull request so the owner can check the Vercel preview before anything is live.

## 1. Get a working copy

```bash
# Reuse a sibling checkout if one exists, otherwise clone next to this repo
cd ..
[ -d Pipeleap-web-redesign ] || gh repo clone manikanakathala-droid/Pipeleap-web-redesign
cd Pipeleap-web-redesign
git switch main 2>/dev/null || git switch master
git pull
git switch -c seo/<short-description>
```

Look at the repo first (`ls`, `vercel.json`, `sitemap.xml`, the page you are changing). Never assume its structure from memory; it changes.

## 2. Edit existing pages

- Change only what the task needs: `<title>`, `<meta name="description">`, Open Graph and Twitter tags, headings, copy, internal links, JSON-LD.
- Keep the title, `og:title` and `twitter:title` consistent, and the same for descriptions.
- If the page has JSON-LD that repeats visible text (such as the FAQPage), update both together. Structured data must match what's on the page.

## 3. Add a new page

1. Copy `pilot.html` (the simplest full page) to `<slug>.html`. With `cleanUrls`, it is served at `/<slug>`.
2. Keep everything in `<head>` that isn't page-specific: the Termly consent script first, GA4, fonts, styles, favicon. Keep the header navigation and the footer.
3. Replace the page-specific parts: `<title>`, meta description, canonical (`https://www.pipeleap.com/<slug>`), `og:url`, `og:title`, `og:description`, `twitter:*`, the `<main>` content and the JSON-LD.
4. Reuse the site's existing CSS classes and section patterns instead of inventing new styles, so the page looks native. If the content needs a pattern the site doesn't have, keep the markup simple and semantic, and say so in the PR.
5. Add a `<url>` entry to `sitemap.xml` with `<loc>` and today's `<lastmod>`.
6. Link to the new page from at least one relevant existing page in body copy. Adding it to the nav or footer is a design decision: propose it, don't do it silently.
7. The booking CTAs keep their exact `href` values, so the `book_walkthrough` click tracking keeps working.

## 4. Check before opening the PR

```bash
python -m http.server 8000   # in the site folder, in the background
python <this repo>/.claude/skills/seo-technical-audit/scripts/audit_site.py --url http://localhost:8000/<slug>.html
```

Fix any errors the audit reports (missing title, missing canonical, more than one H1, broken links, invalid JSON-LD). Then stop the server.

## 5. Open the pull request

```bash
git add -A && git commit -m "<what changed and why>"
git push -u origin HEAD
gh pr create --title "<short title>" --body "<what changed, target keyword, how to check it>"
```

In the PR description list: the target query, the title and description before and after, new URLs, and what the reviewer should look at in the Vercel preview. Give the user the PR link. Don't merge it yourself.

## 6. After the owner merges

Tell search engines about new or changed URLs:

```bash
curl -s -X POST https://api.indexnow.org/indexnow -H "Content-Type: application/json; charset=utf-8" \
  --data '{"host":"www.pipeleap.com","key":"92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55","keyLocation":"https://www.pipeleap.com/92dd2f32d73275ee15cc3962bb19802ea100bc9c1acba36838239c0d4f6d9d55.txt","urlList":["https://www.pipeleap.com/<slug>"]}'
```

IndexNow covers Bing, Yandex and others. Google doesn't use it: offer to request indexing in Search Console (URL Inspection → Request indexing) through the browser.
