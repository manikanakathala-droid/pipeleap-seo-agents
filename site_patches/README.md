# Site patches

`seo-foundation.patch` is what the growth loop changes in the site repository
(`Pipeleap-web-redesign`) on its first run: `robots.txt`, `sitemap.xml`, canonical tags,
structured data (Organization, WebSite, SoftwareApplication, FAQPage, breadcrumbs),
the IndexNow key file and redirects for the previous site's core URLs.

It was generated against commit `729195d`. The loop regenerates the same changes against
whatever is current, so applying this by hand is only needed to ship them before the
workflow has push access:

```bash
git apply seo-foundation.patch
```
