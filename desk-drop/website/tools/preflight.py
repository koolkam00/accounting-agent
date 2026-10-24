#!/usr/bin/env python3
"""Publish preflight. Run from website/ before uploading the site to production:
    python3 tools/preflight.py
Exit code 0 = nothing blocks publishing. Every line marked BLOCK must be fixed first.

Two parts:
  1. The source (site/ and site/site.config.js): contact details, the form endpoint, the status
     line and its date, every page free of [BRACKET] placeholders and draft headings, and the
     name gate in the legal pack, which must say CLEARED (it fails closed).
  2. The production copy (publish/, written by tools/make_production.py), if it exists: staging
     flag off, no noindex anywhere, production robots.txt and sitemap.xml, the name and contact
     details written into the HTML, and nothing in site/ newer than the copy.
tools/make_production.py runs part 1 itself and refuses to build while anything blocks.
"""
import datetime
import os
import re
import sys

WEB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(WEB, "site")
PUBLISH = os.path.join(WEB, "publish")
DESK = os.path.dirname(WEB)
PAGES = ["index", "brands", "offices", "privacy", "survey-privacy", "404"]
STATUS_MAX_AGE_DAYS = 14
# The line the legal pack writes when the founder's name decision clears a public launch.
# It must appear in desk-drop-legal-pack/name-check-log.md; anything else keeps the gate shut.
CLEARED = re.compile(r"(?mi)^.*public launch \(C\)[^\n]*\bCLEARED\b[^\n]*\b(\d{4}-\d{2}-\d{2})\b")
HOLD = re.compile(r"(?mi)public launch \(C\)[^\n]*\bHOLD\b|HOLD[^\n]*public launch \(C\)")
# A placeholder typed into a page: [DATE], [EMAIL], [BRAND PRIVACY POLICY URL], [COMPANY NAME: ...].
BRACKET = re.compile(r"\[[A-Z][A-Z0-9 .:/,'&-]*\]|\[COMPANY NAME:[^\]]*\]")


def read(p):
    return open(p, encoding="utf-8").read()


def config_values(cfg_text):
    def val(key):
        m = re.search(r"(?m)^\s*" + key + r':\s*"([^"]*)"', cfg_text)
        return m.group(1) if m else None
    return val


def is_placeholder(v):
    return v is None or bool(re.fullmatch(r"\s*\[[^\]]+\]\s*", v))


def strip_mocks(html):
    """Remove the parts of a page where brackets are deliberate: the report and card mock-ups
    (labeled "Illustrative placeholders"), HTML comments, scripts and styles."""
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r"<(script|style)\b.*?</\1>", "", html, flags=re.S)
    html = re.sub(r'<figure class="mock">.*?</figure>', "", html, flags=re.S)
    return html


def check_source(site=SITE, desk=DESK, today=None):
    blocks, warns = [], []
    today = today or datetime.date.today()
    cfg = read(os.path.join(site, "site.config.js"))
    val = config_values(cfg)
    if not re.match(r"^https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec$", val("FORM_ENDPOINT") or ""):
        blocks.append("site.config.js: FORM_ENDPOINT is not a deployed Apps Script /exec URL (SETUP.md section 3)")
    if not re.match(r"^https://[a-z0-9-]+\.goatcounter\.com/count$", val("ENDPOINT") or ""):
        warns.append("site.config.js: ANALYTICS.ENDPOINT is empty or not a GoatCounter /count URL (no visit counts)")
    for k in ("DOMAIN", "CONTACT_EMAIL", "POSTAL_ADDRESS", "FOUNDER_NAME", "COMPANY_LEGAL_NAME", "BRAND_NAME"):
        v = val(k)
        if not v or is_placeholder(v):
            blocks.append("site.config.js: %s is still a placeholder" % k)
    for k in ("PHONE", "FOUNDER_LINKEDIN"):  # optional: "" hides the line
        v = val(k)
        if v is None or (v.strip() and is_placeholder(v)):
            blocks.append('site.config.js: %s is still a placeholder (fill it, or set it to "" to hide that line)' % k)
    li = val("FOUNDER_LINKEDIN") or ""
    if li.strip() and not is_placeholder(li) and not li.startswith("https://"):
        blocks.append("site.config.js: FOUNDER_LINKEDIN must be a full https:// link")
    status_date = val("ROSTER_STATUS_DATE") or ""
    try:
        d = datetime.date.fromisoformat(status_date)
        age = (today - d).days
        if age > STATUS_MAX_AGE_DAYS:
            blocks.append("site.config.js: ROSTER_STATUS_DATE is %s, %d days ago. Re-read ROSTER_STATUS (\"%s\"), make it true today, and set the date"
                          % (status_date, age, val("ROSTER_STATUS")))
        elif age < 0:
            blocks.append("site.config.js: ROSTER_STATUS_DATE %s is in the future" % status_date)
    except ValueError:
        blocks.append("site.config.js: ROSTER_STATUS_DATE is missing or not YYYY-MM-DD")
    for page in PAGES:
        s = read(os.path.join(site, page + ".html"))
        if "Map slot:" in s:
            blocks.append(page + ".html: map slot not replaced (run tools/build_map.py)")
        if "Draft for attorney review" in s:
            blocks.append(page + ".html: still marked 'Draft for attorney review'; publish only after the attorney clears it, then remove the heading")
        body = strip_mocks(s)
        found = sorted(set(BRACKET.findall(body)))
        if found:
            blocks.append(page + ".html: placeholders typed into the page: " + ", ".join(found))
        if re.search(r'class="[^"]*\bph\b', body):
            blocks.append(page + '.html: a highlighted placeholder (class="ph") is still in the page')
    gate = os.path.join(desk, "desk-drop-legal-pack", "name-check-log.md")
    if not os.path.exists(gate):
        blocks.append("name gate: desk-drop-legal-pack/name-check-log.md not found, so the name cannot be shown as cleared")
    else:
        g = read(gate)
        m = CLEARED.search(g)
        if HOLD.search(g) and not m:
            blocks.append("name gate: desk-drop-legal-pack/name-check-log.md still says HOLD for a public launch")
        elif not m:
            blocks.append('name gate: desk-drop-legal-pack/name-check-log.md has no line "Public launch (C): CLEARED YYYY-MM-DD"')
        elif HOLD.search(g):
            blocks.append("name gate: the log says both CLEARED and HOLD for a public launch; ask the legal pack to fix the status line")
    return blocks, warns


def check_build(out=PUBLISH, site=SITE):
    blocks, warns = [], []
    if not os.path.isdir(out):
        return ["publish/: no production copy yet (run tools/make_production.py)"], warns
    cfg = read(os.path.join(out, "site.config.js"))
    if not re.search(r"STAGING:\s*false", cfg):
        blocks.append("publish/site.config.js: STAGING is not false")
    robots = read(os.path.join(out, "robots.txt")) if os.path.exists(os.path.join(out, "robots.txt")) else ""
    if re.search(r"(?m)^Disallow:\s*/\s*$", robots) or "Sitemap:" not in robots or "[DOMAIN]" in robots:
        blocks.append("publish/robots.txt: not the production version (run tools/make_production.py)")
    sm = os.path.join(out, "sitemap.xml")
    if not os.path.exists(sm) or "[DOMAIN]" in read(sm) or ".html<" in read(sm):
        blocks.append("publish/sitemap.xml: missing, still has [DOMAIN], or lists .html URLs")
    if "X-Robots-Tag" in read(os.path.join(out, "_headers")):
        blocks.append("publish/_headers: still sends X-Robots-Tag noindex")
    for page in PAGES:
        s = read(os.path.join(out, page + ".html"))
        if re.search(r'<meta name="robots"', s):
            blocks.append("publish/%s.html: still has a noindex robots tag" % page)
        if 'property="og:site_name"' not in s:
            blocks.append("publish/%s.html: name not written into the page (og:site_name missing)" % page)
        if page != "404" and 'rel="canonical"' not in s:
            blocks.append("publish/%s.html: no canonical link" % page)
    if re.search(r'(href|src)="(assets/|site\.config\.js|[a-z-]+\.html)', read(os.path.join(out, "404.html"))):
        blocks.append("publish/404.html: relative links left (they break on nested missing paths)")
    built = os.path.getmtime(os.path.join(out, "site.config.js"))
    newer = [os.path.relpath(os.path.join(r, f), site) for r, _, fs in os.walk(site) for f in fs
             if os.path.getmtime(os.path.join(r, f)) > built + 1]
    if newer:
        blocks.append("publish/ is older than site/ (changed since: %s). Run tools/make_production.py again" % ", ".join(sorted(newer)[:5]))
    return blocks, warns


def main():
    blocks, warns = check_source()
    b2, w2 = check_build()
    blocks += b2
    warns += w2
    for w in warns:
        print("WARN  ", w)
    for b in blocks:
        print("BLOCK ", b)
    print("\n%d blocking, %d warnings" % (len(blocks), len(warns)))
    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
