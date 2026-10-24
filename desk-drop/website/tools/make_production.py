#!/usr/bin/env python3
"""Switch the site files from staging to production, except site.config.js (you set STAGING to
false there yourself, as the deliberate last step). Run from website/:
    python3 tools/make_production.py
It: writes site/robots.txt and site/sitemap.xml from tools/production/ with your DOMAIN filled in,
and removes the STAGING ONLY block (X-Robots-Tag) from site/_headers. Then run tools/preflight.py.
"""
import os, re, sys
WEB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(WEB, "site")
cfg = open(os.path.join(SITE, "site.config.js"), encoding="utf-8").read()
domain = re.search(r'DOMAIN:\s*"([^"]*)"', cfg).group(1).strip()
if not domain or domain.startswith("["):
    sys.exit('Set DOMAIN in site/site.config.js first (for example "example.com").')
domain = re.sub(r"^https?://", "", domain).strip("/")
for name in ("robots.txt", "sitemap.xml"):
    s = open(os.path.join(WEB, "tools", "production", name), encoding="utf-8").read().replace("[DOMAIN]", domain)
    open(os.path.join(SITE, name), "w", encoding="utf-8").write(s)
    print("wrote site/" + name)
h = open(os.path.join(SITE, "_headers"), encoding="utf-8").read()
h2 = re.sub(r"# STAGING ONLY:.*\Z", "", h, flags=re.S).rstrip() + "\n"
open(os.path.join(SITE, "_headers"), "w", encoding="utf-8").write(h2)
print("removed the staging noindex header from site/_headers" if h2 != h else "site/_headers had no staging block")
print("Now set STAGING: false in site/site.config.js, then run: python3 tools/preflight.py")
