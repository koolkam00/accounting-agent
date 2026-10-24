#!/usr/bin/env python3
"""Publish preflight. Run from website/ before uploading the site to production:
    python3 tools/preflight.py
Exit code 0 = nothing blocks publishing. Every line marked BLOCK must be fixed first.
"""
import os, re, sys
WEB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(WEB, "site")
DESK = os.path.dirname(WEB)
blocks, warns = [], []
cfg = open(os.path.join(SITE, "site.config.js"), encoding="utf-8").read()
def val(key):
    m = re.search(key + r':\s*"([^"]*)"', cfg); return m.group(1) if m else ""
if re.search(r"STAGING:\s*true", cfg): blocks.append("site.config.js: STAGING is still true")
ep = val("FORM_ENDPOINT")
if not re.match(r"^https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec$", ep):
    blocks.append("site.config.js: FORM_ENDPOINT is not a deployed Apps Script /exec URL (SETUP.md section 3)")
if not re.match(r"^https://[a-z0-9-]+\.goatcounter\.com/count$", val("ENDPOINT")):
    warns.append("site.config.js: ANALYTICS.ENDPOINT is empty or not a GoatCounter /count URL (no visit counts)")
for k in ("DOMAIN", "CONTACT_EMAIL", "POSTAL_ADDRESS", "FOUNDER_NAME", "COMPANY_LEGAL_NAME"):
    if not val(k) or val(k).startswith("["): blocks.append("site.config.js: %s is still a placeholder" % k)
robots = open(os.path.join(SITE, "robots.txt"), encoding="utf-8").read()
if re.search(r"(?m)^Disallow:\s*/\s*$", robots): blocks.append("robots.txt: still the staging version (run tools/make_production.py)")
if not os.path.exists(os.path.join(SITE, "sitemap.xml")) or "[DOMAIN]" in open(os.path.join(SITE, "sitemap.xml"), encoding="utf-8").read():
    blocks.append("sitemap.xml: missing or still has [DOMAIN] (run tools/make_production.py)")
if "X-Robots-Tag" in open(os.path.join(SITE, "_headers"), encoding="utf-8").read(): blocks.append("_headers: still sends X-Robots-Tag noindex")
for page in ("privacy.html", "survey-privacy.html", "brands.html", "offices.html"):
    s = open(os.path.join(SITE, page), encoding="utf-8").read()
    if "[DATE]" in s: blocks.append(page + ": [DATE] not filled in")
    if "Map slot:" in s: blocks.append(page + ": map slot not replaced (run tools/build_map.py)")
    if "Draft for attorney review" in s: blocks.append(page + ": still marked 'Draft for attorney review'; publish only after the attorney clears it, then remove the heading")
gate = os.path.join(DESK, "desk-drop-legal-pack", "name-check-log.md")
if os.path.exists(gate):
    g = open(gate, encoding="utf-8").read()
    if re.search(r"HOLD for any print run \(D\) and any public launch \(C\)|Public launch \(C\) \| \*\*HOLD\*\*", g):
        blocks.append("name gate: desk-drop-legal-pack/name-check-log.md still says HOLD for a public launch")
else:
    warns.append("name gate file not found; confirm the name is cleared before publishing")
for w in warns: print("WARN  ", w)
for b in blocks: print("BLOCK ", b)
print("\n%d blocking, %d warnings" % (len(blocks), len(warns)))
sys.exit(1 if blocks else 0)
