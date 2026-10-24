#!/usr/bin/env python3
"""Write the production copy of the site into website/publish/. Run from website/:
    python3 tools/make_production.py
Then upload the publish/ folder (not site/) to the production environment (SETUP.md section 10).

site/ stays the staging source and is never changed. The copy differs from it in these ways:
  - site.config.js has STAGING: false.
  - Every page: the noindex robots tag is removed; the name, tagline, contact details and status
    line from site.config.js are written into the HTML (title, og:site_name, header, footer,
    notices), so visitors without JavaScript and link previews (Slack, LinkedIn, iMessage) see
    them; canonical and og:url links point at extension-less URLs (/brands, not /brands.html),
    because Cloudflare Pages redirects .html to those.
  - 404.html uses root-absolute links (/assets/..., /brands), because Cloudflare Pages serves it
    for missing nested paths such as /brands/x, where relative links would break.
  - robots.txt and sitemap.xml are the production versions from tools/production/, with DOMAIN.
  - _headers loses its STAGING ONLY block (X-Robots-Tag: noindex).
A rename is still one edit: change BRAND_NAME in site/site.config.js and run this again.

It first runs the source checks in tools/preflight.py and stops if anything blocks.
Options (for tests and previews only; never upload such a copy):
  --draft          build even though the preflight blocks, into publish-draft/ by default
  --out DIR        write somewhere else
  --config FILE    use another site.config.js (the tests pass one filled with SAMPLE values)
"""
import argparse
import html
import os
import re
import shutil
import sys

WEB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(WEB, "site")
sys.path.insert(0, os.path.join(WEB, "tools"))
import preflight  # noqa: E402

PAGES = ["index", "brands", "offices", "privacy", "survey-privacy", "404"]
MARK = "PRODUCTION COPY written by tools/make_production.py"


def js_value(cfg, key):
    m = re.search(r"(?m)^\s*" + key + r':\s*"([^"]*)"', cfg)
    if m:
        return m.group(1)
    m = re.search(r"(?m)^\s*" + key + r":\s*(true|false)", cfg)
    return (m.group(1) == "true") if m else None


def placeholder(v):
    return isinstance(v, str) and bool(re.fullmatch(r"\s*\[[^\]]+\]\s*", v))


def add_class(attrs, cls):
    if re.search(r'\bclass="', attrs):
        return re.sub(r'\bclass="([^"]*)"', lambda m: 'class="%s %s"' % (m.group(1), cls), attrs, count=1)
    return attrs + ' class="%s"' % cls


def stamp(page, src, cfg, domain):
    """Write config values into one page's HTML (the same fills boot.js makes at run time)."""
    name = js_value(cfg, "BRAND_NAME") or ""
    # Robots: production is indexable.
    src = re.sub(r'<meta name="robots"[^>]*>(<!--.*?-->)?\n?', "", src)
    # Title suffix and og:site_name.
    src = re.sub(r"<title>(.*?)</title>", lambda m: "<title>%s</title>" % (
        m.group(1) if name in html.unescape(m.group(1)) else m.group(1) + " · " + html.escape(name)), src, count=1)
    head_add = '<meta property="og:site_name" content="%s">\n' % html.escape(name, quote=True)
    if domain and page != "404":
        url = "https://%s/%s" % (domain, "" if page == "index" else page)
        head_add += '<link rel="canonical" href="%s">\n<meta property="og:url" content="%s">\n' % (url, url)
    src = src.replace('<meta property="og:type" content="website">\n', '<meta property="og:type" content="website">\n' + head_add, 1)

    # data-config elements are empty in the source: fill them.
    def fill(m):
        tag, attrs = m.group(1), m.group(2)
        key = re.search(r'data-config="([A-Z_]+)"', attrs).group(1)
        v = js_value(cfg, key)
        if not isinstance(v, str):
            return m.group(0)
        text = v
        ph = placeholder(v)
        if ph:
            attrs = add_class(attrs, "is-placeholder")
        elif "data-config-mailto" in attrs:
            attrs += ' href="mailto:%s"' % html.escape(v, quote=True)
        elif "data-config-tel" in attrs:
            attrs += ' href="tel:%s"' % re.sub(r"[^0-9+]", "", v)
        elif "data-config-url" in attrs and v.startswith("https://"):
            attrs += ' href="%s"' % html.escape(v, quote=True)
            text = re.sub(r"^https?://(www\.)?", "", v).rstrip("/")
        return "<%s%s>%s</%s>" % (tag, attrs, html.escape(text), tag)
    src = re.sub(r'<(span|a|p|b|strong)(\s[^>]*\bdata-config="[A-Z_]+"[^>]*)></\1>', fill, src)

    # A line whose value is "" is hidden (for example no phone number).
    def line(m):
        key = m.group(2)
        v = js_value(cfg, key)
        return m.group(0) if (not isinstance(v, str) or v.strip()) else m.group(1) + " hidden" + m.group(3)
    src = re.sub(r'(<[a-z]+\s[^>]*data-config-line="([A-Z_]+)")([^>]*>)', line, src)

    if page == "404":
        def absolute(m):
            attr, url = m.group(1), m.group(2)
            if url == "index.html":
                url = "/"
            elif re.fullmatch(r"[a-z-]+\.html(#.*)?", url):
                url = "/" + re.sub(r"\.html", "", url, count=1)
            else:
                url = "/" + url
            return '%s="%s"' % (attr, url)
        src = re.sub(r'\b(href|src)="((?:assets/|site\.config\.js|[a-z-]+\.html)[^"]*)"', absolute, src)
    return src.replace("<!doctype html>", "<!doctype html>\n<!-- %s -->" % MARK, 1)


def main():
    ap = argparse.ArgumentParser(description="Write the production copy of site/ into publish/.")
    ap.add_argument("--draft", action="store_true", help="build even if the preflight blocks (never upload it)")
    ap.add_argument("--out", help="output folder (default publish/, or publish-draft/ with --draft)")
    ap.add_argument("--config", help="use this site.config.js instead of site/site.config.js")
    args = ap.parse_args()
    out = os.path.abspath(args.out or os.path.join(WEB, "publish-draft" if args.draft else "publish"))
    cfg_path = os.path.abspath(args.config) if args.config else os.path.join(SITE, "site.config.js")
    cfg = open(cfg_path, encoding="utf-8").read()

    if not args.draft:
        blocks, warns = preflight.check_source()
        for w in warns:
            print("WARN  ", w)
        if blocks:
            for b in blocks:
                print("BLOCK ", b)
            sys.exit("\n%d blocking: nothing written. Fix these, then run this again." % len(blocks))

    domain = js_value(cfg, "DOMAIN") or ""
    domain = "" if placeholder(domain) else re.sub(r"^https?://", "", domain).strip().strip("/")

    if os.path.exists(out):
        cfg_old = os.path.join(out, "site.config.js")
        if not os.path.exists(cfg_old) or MARK not in open(cfg_old, encoding="utf-8").read():
            sys.exit("%s exists and is not a copy this script wrote; not touching it." % out)
        shutil.rmtree(out)
    shutil.copytree(SITE, out)

    # Settings: the chosen config, with STAGING off.
    new_cfg = re.sub(r"STAGING:\s*true", "STAGING: false", cfg, count=1)
    open(os.path.join(out, "site.config.js"), "w", encoding="utf-8").write("// %s. Edit site/site.config.js, not this file.\n%s" % (MARK, new_cfg))

    for page in PAGES:
        p = os.path.join(out, page + ".html")
        text = open(p, encoding="utf-8").read()
        open(p, "w", encoding="utf-8").write(stamp(page, text, cfg, domain))

    dom = domain or "[DOMAIN]"
    for name in ("robots.txt", "sitemap.xml"):
        s = open(os.path.join(WEB, "tools", "production", name), encoding="utf-8").read().replace("[DOMAIN]", dom)
        open(os.path.join(out, name), "w", encoding="utf-8").write(s)
    h = open(os.path.join(out, "_headers"), encoding="utf-8").read()
    open(os.path.join(out, "_headers"), "w", encoding="utf-8").write(re.sub(r"# STAGING ONLY:.*\Z", "", h, flags=re.S).rstrip() + "\n")

    print("wrote %s (%s)" % (os.path.relpath(out, WEB), "DRAFT: do not upload" if args.draft else "production copy"))
    if not args.draft:
        blocks, _ = preflight.check_build(out)
        for b in blocks:
            print("BLOCK ", b)
        if blocks:
            sys.exit("The copy failed its own checks; do not upload it.")
        print("Checks passed. Upload the publish/ folder to the production environment (SETUP.md section 10, step 6).")


if __name__ == "__main__":
    main()
