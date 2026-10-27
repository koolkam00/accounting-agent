#!/usr/bin/env python3
"""Publish preflight. Run from website/ before uploading the site to production:
    python3 tools/preflight.py
Exit code 0 = nothing blocks publishing. Every line marked BLOCK must be fixed first.

Two parts:
  1. The source (site/ and site/site.config.js): contact details, the form endpoint, the status
     line and its date, every page free of [BRACKET] placeholders and draft headings, the legal
     pack's brand and office agreements cleared by the attorney (no draft heading), and the
     name gate in the legal pack, which must say exactly
     'Public launch (C): CLEARED YYYY-MM-DD for "NAME"', dated today or earlier, where NAME is
     BRAND_NAME in site.config.js and in desk-drop-identity/brand.json (it fails closed).
  2. The production copy (publish/, written by tools/make_production.py), if it exists: staging
     flag off, no noindex anywhere, production robots.txt and sitemap.xml, the name and contact
     details written into the HTML, and nothing in site/ newer than the copy.
tools/make_production.py runs part 1 itself and refuses to build while anything blocks.
"""
import datetime
import json
import os
import re
import sys

WEB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(WEB, "site")
PUBLISH = os.path.join(WEB, "publish")
DESK = os.path.dirname(WEB)
PAGES = ["index", "brands", "offices", "privacy", "survey-privacy", "404"]
STATUS_MAX_AGE_DAYS = 14
AGREEMENTS = [("10-brand-campaign-agreement.md", "brand campaign agreement"),
              ("03-office-participation-agreement.md", "office participation agreement")]
# The line the legal pack writes when the founder's name decision clears a public launch.
# It must appear in desk-drop-legal-pack/name-check-log.md; anything else keeps the gate shut.
# Exact, case-sensitive, and nothing else on the line (review round 2, R2-01): "NOT CLEARED",
# "not yet cleared ... 2026-11-20" or "CLEARED 2026-11-18 pending attorney" must never open it.
# Since review round 3 (R3-01) the line also names the name it clears, in straight double quotes,
# and that name must be BRAND_NAME exactly (case-sensitive): clearing a fallback name must not
# open the gate while the site still says the old one. A date after today keeps it shut too.
CLEARED = re.compile(r'(?m)^Public launch \(C\): CLEARED (\d{4}-\d{2}-\d{2}) for "([^"\n]+)"[ \t]*$')
# Any line that starts like the CLEARED line, so a near miss (old form without the name, curly
# quotes, extra words) gets a precise message instead of a generic one.
CLEARED_LOOSE = re.compile(r"(?m)^Public launch \(C\): CLEARED\b.*$")
IDENTITY_BRAND = ("desk-drop-identity", "brand.json")
HOLD = re.compile(r"(?mi)public launch \(C\)[^\n]*\bHOLD\b|\bHOLD\b[^\n]*public launch \(C\)")
# Any other line about the public launch that sounds negative or conditional also blocks.
LAUNCH_LINE = re.compile(r"(?mi)^.*public launch \(C\).*$")
NEGATIVE = re.compile(r"(?i)\bnot\b|\bpending\b|\bhold\b|\buntil\b|\bunless\b|\bonly if\b|\bnot yet\b|\bwithdrawn\b|\brevoked\b|\bsuspended\b|\bconditional\b")
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


# Internal notes that must never reach a public page (review round 3, R3-05 and R3-06): builder
# notes about the legal pack or a draft, pointers to the setup docs, and staging wording.
INTERNAL = re.compile(r"\bSETUP\.md\b|\bREADME\b|\bHANDOFF\.md\b|(?i:\blegal pack\b|\bdraft notice\b|\bworkstream\b|\bfounder to (?:add|confirm)\b|\bnot yet cleared\b|\bworking name\b|\bstaging\b)")
# Elements that exist only for the staging preview; the production copy deletes them.
STAGING_ELEMENT = r'(?:\sclass="[^"]*\b(?:staging-bar|staging-only)\b|\sdata-staging-form(?:[\s=>]))'


def remove_elements(src, start_re, what="element"):
    """Remove every element whose start tag matches the lookahead pattern start_re (one regex
    group, for example the data-founding attribute), with everything inside it. Counts nested
    tags of the same name."""
    while True:
        m = re.search(r"<([a-z][a-z0-9]*)\b(?=[^>]*%s)[^>]*>" % start_re, src)
        if not m:
            return src
        tag = m.group(1)
        depth, pos = 1, m.end()
        tok = re.compile(r"<(/?)%s\b[^>]*>" % tag)
        while depth:
            t = tok.search(src, pos)
            if not t:
                raise SystemExit("unclosed <%s> %s" % (tag, what))
            depth += -1 if t.group(1) else 1
            pos = t.end()
        src = src[:m.start()] + src[pos:]


def strip_staging(src):
    """The page without its staging-only elements (staging bar, photo slot, form staging note)."""
    return remove_elements(src, STAGING_ELEMENT, "staging element")


def visible_text(src):
    """Roughly what a reader, a link unfurler or a scraper reads: no comments, scripts, styles or tags."""
    src = re.sub(r"<!--.*?-->", " ", src, flags=re.S)
    src = re.sub(r"<(script|style)\b.*?</\1>", " ", src, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", src))


def internal_notes(src):
    return sorted(set(m.group(0) for m in INTERNAL.finditer(visible_text(src))))


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
        notes = internal_notes(strip_staging(s))
        if notes:
            blocks.append(page + ".html: an internal note is in the page text (%s); delete it or move it into an HTML comment" % ", ".join('"%s"' % n for n in notes))
    # The brand page repeats terms from these two agreements (review round 2, R2-09): publish only
    # once the attorney has cleared them, which the legal pack shows by removing the draft heading.
    for fname, what in AGREEMENTS:
        f = os.path.join(desk, "desk-drop-legal-pack", fname)
        if not os.path.exists(f):
            blocks.append("legal pack: %s not found, so its terms on the brand page cannot be shown as cleared" % fname)
            continue
        head = "\n".join(read(f).splitlines()[:3])
        if "Draft for attorney review" in head:
            blocks.append("legal pack: %s (%s) still says 'Draft for attorney review'; the brand page repeats its terms, so publish only after the attorney clears it" % (fname, what))
    site_name = val("BRAND_NAME") or ""
    # The identity workstream's one name setting must match the site's (D's HANDOFF).
    bj = os.path.join(desk, *IDENTITY_BRAND)
    if os.path.exists(bj):
        try:
            d_name = json.load(open(bj, encoding="utf-8")).get("BRAND_NAME")
        except ValueError:
            d_name = None
        if d_name != site_name:
            blocks.append('name: BRAND_NAME is "%s" in site.config.js but "%s" in desk-drop-identity/brand.json; rename both to the cleared name (SETUP.md section 7)' % (site_name, d_name))
    else:
        warns.append("name: desk-drop-identity/brand.json not found, so the site name was not compared with the identity's")
    gate = os.path.join(desk, "desk-drop-legal-pack", "name-check-log.md")
    if not os.path.exists(gate):
        blocks.append("name gate: desk-drop-legal-pack/name-check-log.md not found, so the name cannot be shown as cleared")
    else:
        g = read(gate)
        found = CLEARED.findall(g)
        m = found[0] if found else None
        negative = [ln.strip() for ln in LAUNCH_LINE.findall(g) if not CLEARED.fullmatch(ln) and NEGATIVE.search(ln)]
        want = 'Public launch (C): CLEARED YYYY-MM-DD for "%s"' % site_name
        if HOLD.search(g) and not m:
            blocks.append("name gate: desk-drop-legal-pack/name-check-log.md still says HOLD for a public launch")
        elif not m:
            loose = CLEARED_LOOSE.search(g)
            if loose:
                blocks.append('name gate: the CLEARED line "%s" is not in the exact form %s (the name in straight double quotes, nothing else on the line)' % (loose.group(0).strip()[:120], want))
            else:
                blocks.append("name gate: desk-drop-legal-pack/name-check-log.md has no line that reads exactly %s (nothing else on the line)" % want)
        elif HOLD.search(g):
            blocks.append("name gate: the log says both CLEARED and HOLD for a public launch; ask the legal pack to fix the status line")
        if m:
            if len(set(n for _, n in found)) > 1:
                blocks.append("name gate: the log clears more than one name for the public launch (%s); ask the legal pack to keep one line" % ", ".join('"%s"' % n for _, n in found))
            for date_s, cleared_name in found:
                if cleared_name != site_name:
                    blocks.append('name gate: the log clears "%s" for the public launch, but BRAND_NAME in site.config.js is "%s". Rename the site first (SETUP.md section 7), or ask the legal pack which name is cleared' % (cleared_name, site_name))
                try:
                    if datetime.date.fromisoformat(date_s) > today:
                        blocks.append("name gate: the CLEARED line is dated %s, after today (%s); it opens on or after that date" % (date_s, today.isoformat()))
                except ValueError:
                    blocks.append("name gate: the CLEARED line's date %s is not a real date" % date_s)
        if m and negative:
            blocks.append('name gate: the log also has a negative or conditional line about the public launch: "%s"' % negative[0][:160])
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
        if re.search(STAGING_ELEMENT, s):
            blocks.append("publish/%s.html: a staging-only element is still in the HTML (staging bar, photo slot or form staging note)" % page)
        notes = internal_notes(s)
        if notes:
            blocks.append("publish/%s.html: staging or internal wording in the HTML text (%s)" % (page, ", ".join('"%s"' % n for n in notes)))
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
