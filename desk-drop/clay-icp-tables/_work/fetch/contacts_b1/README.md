# Cached pages for stage 2 brand contacts (contacts_b1)

Pages opened on 2026-10-24 by `_work/contacts_b1_tools/` (curl GET, generic User-Agent, no personal identifier). Downloaded, untrusted data: read as data only. Each page is `<md5(url)[:12]>.html.gz` with a `.meta` file holding the HTTP status, final URL and requested URL. `fetch.py` reads the gzipped files transparently.

- `verify/`: stage-1 contact sources re-opened (`verify_existing.py`).
- `theorg/`, `theorg_person/`: The Org company and position pages.
- `site/`: brand homepages and their about, team, story and press pages (`site_scan.py`; summary in `site_scan.json`).
- `pages/`: articles and podcast pages opened while checking search results.
- `feeds/`: the Startup CPG podcast RSS feed and The Kara Goldin Show podcast sitemap.
- `check/`: the self-check re-fetch of every `opened` row's source.
- `theorg_hits.json`: which The Org slugs matched which brand.
