#!/usr/bin/env python3
"""Static checks over site/ (QA.md P13, P15, P17 and the handoffs). No network.

  1. Header and footer blocks are identical on every page.
  2. Every internal link, asset and #fragment resolves; no root-absolute or protocol-relative
     URL; no external script, stylesheet or font (the site works from any subfolder).
  3. The working name appears in no site file except site.config.js (rename = one edit).
  4. tokens.css is an exact copy of desk-drop-identity/tokens/tokens.css.
  5. Claims: exact prices and terms present; banned words only inside approved negations;
     ladder words present; the attorney-review heading under each form and on each privacy page.
  6. survey-privacy.html carries the legal pack's Part C text word for word.
  7. Form field names, required flags and option values match the SCHEMA in apps-script/Code.gs.
  8. Staging files agree with site.config.js (robots.txt, _headers).
  9. Review round 3: brand terms match G 10 v0.8 (photo day, card text, sales tax, the
     outside-events exit), notices name the short notification email, the office form keeps
     health details out, the thank-you messages promise nothing to a sender who is ruled out,
     no internal note in any page's text, and the map matches B's current file
     (tools/build_map.py --check).
Usage (from website/): python3 tests/check_site.py
"""
import html
import json
import os
import re
import sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(HERE)
SITE = os.path.join(WEB, "site")
DESK = os.path.dirname(WEB)
PAGES = ["index", "brands", "offices", "privacy", "survey-privacy", "404"]
problems = []
passes = []


def check(cond, ok_msg, bad_msg):
    (passes if cond else problems).append(ok_msg if cond else bad_msg)


def read(p):
    return open(p, encoding="utf-8").read()


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.ids, self.text, self.skip = [], set(), [], 0
        self.inputs = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for k in ("href", "src"):
            if k in a and a[k] is not None:
                self.refs.append((tag, k, a[k], a.get("rel", "")))
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("input", "select", "textarea"):
            self.inputs.append((tag, a))

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, d):
        if not self.skip:
            self.text.append(d)


def parse(name):
    c = Collector()
    c.feed(read(os.path.join(SITE, name + ".html")))
    c.full_text = re.sub(r"\s+", " ", " ".join(c.text))
    return c


docs = {p: parse(p) for p in PAGES}
raw = {p: read(os.path.join(SITE, p + ".html")) for p in PAGES}

# 1. shared header and footer
for block in ("HEADER", "FOOTER"):
    blocks = {p: re.search(r"<!-- %s:START.*?<!-- %s:END -->" % (block, block), raw[p], re.S).group(0) for p in PAGES}
    first = blocks["index"]
    same = [p for p in PAGES if blocks[p] == first]
    check(len(same) == len(PAGES), f"{block.lower()} identical on all {len(PAGES)} pages", f"{block.lower()} differs on: {[p for p in PAGES if p not in same]}")

# 2. links and portability
bad = []
for p, d in docs.items():
    for tag, attr, url, rel in d.refs:
        if url.startswith(("mailto:", "tel:")):
            continue
        if url.startswith("//") or url.startswith("/"):
            bad.append(f"{p}: root-absolute or protocol-relative {url}")
            continue
        if re.match(r"https?://", url):
            if tag in ("script", "link", "img"):
                bad.append(f"{p}: external {tag} {url}")
            continue
        path, _, frag = url.partition("#")
        path = path.split("?")[0]
        target = path or (p + ".html")
        if not os.path.exists(os.path.join(SITE, target)):
            bad.append(f"{p}: missing {url}")
            continue
        if frag and target.endswith(".html"):
            tname = target[:-5]
            if tname in docs and frag not in docs[tname].ids:
                bad.append(f"{p}: missing #{frag} in {target}")
for css in ("assets/css/site.css", "assets/css/tokens.css"):
    for u in re.findall(r"url\(([^)]+)\)", read(os.path.join(SITE, css))):
        u = u.strip("'\"")
        if re.match(r"(https?:)?//", u):
            bad.append(f"{css}: external url {u}")
        elif not u.startswith("data:") and not os.path.exists(os.path.normpath(os.path.join(SITE, os.path.dirname(css), u))):
            bad.append(f"{css}: missing {u}")
check(not bad, "every internal link, asset and fragment resolves; no root-absolute URLs; no external scripts, styles or fonts", "; ".join(bad))

# 3. the working name lives only in site.config.js
hits = []
for root, _, files in os.walk(SITE):
    for f in files:
        fp = os.path.join(root, f)
        if f == "site.config.js" or f.endswith((".woff2", ".png", ".txt")) and "fonts" in root:
            continue
        try:
            s = open(fp, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        # Folder names fixed by CONTRACTS (desk-drop-identity/, desk-drop-legal-pack/) are paths, not the name.
        if re.search(r"desk\s*-?\s*drop(?!-(identity|legal-pack|outreach)\b)", s, re.I):
            hits.append(os.path.relpath(fp, SITE))
check(not hits, "working name appears in no site file except site.config.js", "working name found in: " + ", ".join(hits))

# 4. tokens copy
d_tokens = os.path.join(DESK, "desk-drop-identity", "tokens", "tokens.css")
if os.path.exists(d_tokens):
    check(read(d_tokens) == read(os.path.join(SITE, "assets", "css", "tokens.css")), "tokens.css matches desk-drop-identity/tokens/tokens.css exactly", "tokens.css differs from the identity workstream's copy: run tools/sync_tokens.py")

# 5. claims
brands, offices, home = docs["brands"].full_text, docs["offices"].full_text, docs["index"].full_text
for phrase in ["$600", "for 5 offices ($120 per office)", "Paid in full up front.", "Price locked for your next two campaigns",
               "$1,500", "for 10 offices ($150 per office)", "50% at signature.", "50% at placement confirmation", "$150", "per office",
               "No free pilots.", "first three brands only",
               "500 units into 10 New York offices in one week, within walking distance of the stores that carry you, with photos, feedback and a report."]:
    check(phrase in brands, f"brands page states: {phrase}", f"brands page is missing: {phrase}")
# Terms that review round 1 found missing or softened (G 10 v0.8 sections 3 and 8; plan "Excluded in the first six months").
for phrase in ["From the drop day on, the full price is due.", "Before the cancel-by date, 10 business days before the drop",
               "$120 per office, for up to 10 offices (any more at $150)", "we say you were a founding brand at a founding price",
               "about 550 for 10 offices (500 plus 50)", "Who runs this:"]:
    check(phrase in brands, f"brands page states: {phrase}", f"brands page is missing: {phrase}")
for phrase in ["Under 30 or over 250, we can't take you yet.", "Offices with fewer than 30 or more than 250 people in on a Tuesday.",
               "Companies inside a coworking space, on their own", "Run by "]:
    check(phrase in offices, f"offices page states: {phrase}", f"offices page is missing: {phrase}")
# Review round 2: wording matched to G 10 v0.8 section 1 and 8 and G 03 section 3, exact notices, lead time.
for phrase in ["at eye level where the pantry allows", "to help us reach five or more responses (no one has to answer)",
               "If we cancel, we refund everything you paid.", "Your proposal names a drop date, usually three to four weeks out.",
               "beyond the name and title of the person who approves the budget if it isn't you"]:
    check(phrase in brands, f"brands page states: {phrase}", f"brands page is missing: {phrase}")
for phrase in ["commits to posting the link once and to five or more responses", "Five business days later the survey closes"]:
    check(phrase not in brands + offices, f"old wording gone: {phrase}", f"old wording still on a page: {phrase}")
check("beyond the pantry owner's name and title if it isn't you" in offices and "On day 5 of the window the survey closes" in offices,
      "offices page: exact form notice and day-5 survey close", "offices page: notice or day-5 wording missing")
check("They ask nothing about other employees or customers." in docs["privacy"].full_text, "privacy page: exact about the pantry owner and budget approver",
      "privacy page: still says the forms ask about no one else")
check(re.search(r"Able to ship <span data-founding>275</span><span data-standard-only>550</span> units", read(os.path.join(SITE, "brands.html"))) is not None
      and read(os.path.join(SITE, "brands.html")).count("<span data-founding>275</span><span data-standard-only>550</span>") == 2,
      "check 4 and question 4 follow the founding tier (275 or 550 units)", "check 4 or question 4 does not follow the founding tier")
check("After that, we keep 50%" not in brands or "From the drop day on" in brands, "cancellation answer carries the drop-day cut-off", "cancellation answer lacks the drop-day cut-off")
check("Vetted emerging snacks and drinks, free, roughly monthly." in offices and "You pick the categories and can veto anything. All we ask: on the shelf the day it arrives, one photo, and three questions for your team." in offices,
      "offices page states the office pitch word for word", "office pitch missing or changed")
money = set()
for p, d in docs.items():
    money |= set(re.findall(r"\$\d{1,3}(?:,\d{3})*(?:\.\d+)?M?", d.full_text))
check(money <= {"$600", "$120", "$1,500", "$150", "$100", "$1M"}, f"only plan prices and terms appear: {sorted(money)}", f"unexpected money amounts: {sorted(money - {'$600', '$120', '$1,500', '$150', '$100', '$1M'})}")
ALLOWED = [
    "Sales, lift or new customers.",
    "A scan is never reported as a sale, and we do not claim lift.",
    "Do you guarantee sales?",
    "No free pilots.",
    "No. We don't run free pilots.",
    "We don't run free pilots.",
    "If we deliver everything promised, you give us a short, honest written statement and let us publish a case study from your report.",
    "Can we run a free trial first?",
    "Nothing in the report is counted as a sale unless it is a redemption of your code, and even then some of those people would have bought anyway.",
]
BANNED = r"\b(conversions?|convert|ROI|lift|acquisition|acquire|guarantee[ds]?|free pilots?|free trial|testimonials?|trusted by|case stud(y|ies)|proven|the best|best-in-class|boost|increase(s|d)? sales|drive(s)? sales|sales lift)\b"
viol = []
for p, d in docs.items():
    sentences = re.split(r"(?<=[.?!])\s+", d.full_text)
    for s in sentences:
        if re.search(BANNED, s, re.I) and not any(a in s for a in ALLOWED):
            viol.append(f"{p}: {s.strip()[:140]}")
check(not viol, "banned words appear only inside approved negations", "claim lint: " + " | ".join(viol))
for w in ["Delivered", "Placed", "Depleted", "Responded", "Scanned", "Purchased", "Incremental"]:
    check(w in brands, f"ladder rung shown: {w}", f"ladder rung missing: {w}")
DRAFT = "Draft for attorney review. Not legal advice."
for p in ("brands", "offices", "privacy", "survey-privacy"):
    check(DRAFT in docs[p].full_text, f"{p}: attorney-review heading present", f"{p}: attorney-review heading missing")
for p in ("brands", "offices"):
    i = raw[p].find('class="form-notice"')
    j = raw[p].find("</form>")
    check(0 < j < i and DRAFT in raw[p][i:i + 600], f"{p}: notice under the form says what is collected and why, with the review heading", f"{p}: form notice missing or not under the form")
check("free" in offices and "payment" in offices, "office page says free and that payment is never asked", "office page lacks the no-payment statement")

# 6. survey notice word for word
def norm(s):
    s = html.unescape(s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("**", "").replace("#### ", "").replace("### ", "")
    s = re.sub(r"(?m)^\s*-\s+", " ", s)
    s = s.replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip()

gmd = os.path.join(DESK, "desk-drop-legal-pack", "13-survey-privacy-notice.md")
if os.path.exists(gmd):
    g = read(gmd)
    part = g[g.index("<!-- NOTICE START -->") + len("<!-- NOTICE START -->"):g.index("<!-- NOTICE END -->")]
    part = part[part.index("Last updated"):]
    page = raw["survey-privacy"]
    mine = page[page.index("<!-- NOTICE START"):page.index("<!-- NOTICE END -->")]
    # Slots the site fills from site.config.js stand for the legal pack's own placeholders.
    company_slot = re.search(r"\[COMPANY NAME:[^\]]*\]", part)
    slot_for = {"COMPANY_LEGAL_NAME": company_slot.group(0) if company_slot else "[COMPANY NAME]",
                "CONTACT_EMAIL": "[EMAIL]", "POSTAL_ADDRESS": "[POSTAL ADDRESS]"}
    mine = re.sub(r'<(span|a)[^>]*\bdata-config="([A-Z_]+)"[^>]*></\1>', lambda m: slot_for.get(m.group(2), "{" + m.group(2) + "}"), mine)
    mine = mine[mine.index("Last updated"):]
    a, b = norm(part), norm(mine)
    if a != b:
        k = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), min(len(a), len(b)))
        problems.append("survey notice differs from the legal pack at: ...%s... vs ...%s..." % (a[max(0, k - 40):k + 40], b[max(0, k - 40):k + 40]))
    else:
        passes.append("survey-privacy.html carries Part C of 13-survey-privacy-notice.md word for word (%d characters)" % len(a))

# 7. forms vs schema
code = read(os.path.join(WEB, "apps-script", "Code.gs"))
schema = json.loads(re.search(r"/\*SCHEMA-JSON-START\*/(.*?)/\*SCHEMA-JSON-END\*/", code, re.S).group(1))
for kind, page in (("office", "offices"), ("brand", "brands")):
    spec = schema["forms"][kind]["fields"]
    names, values, req = set(), {}, {}
    for tag, a in docs[page].inputs:
        n = a.get("name")
        if not n or n.startswith("ui_") or n == "hp_url":
            continue
        names.add(n)
        if a.get("type") in ("radio", "checkbox") and a.get("value"):
            values.setdefault(n, set()).add(a["value"])
        if "required" in a or "data-required-if" in a:
            req[n] = True
    sel = re.search(r'<select[^>]*name="category".*?</select>', raw[page], re.S)
    if sel:
        values["category"] = set(v for v in re.findall(r'value="([^"]*)"', sel.group(0)) if v)
    if kind == "office":
        names.add("receiving_window")  # composed from ui_receiving_window
        req["receiving_window"] = True
        req["categories_wanted"] = True  # "Any of them" sends all keys
    check(names == set(spec), f"{kind} form fields = schema fields ({len(names)})", f"{kind} form fields differ from schema: extra {sorted(names - set(spec))}, missing {sorted(set(spec) - names)}")
    for n, s in spec.items():
        need = bool(s.get("required") or s.get("required_if"))
        if need != bool(req.get(n)):
            problems.append(f"{kind}.{n}: required in schema={need}, in form={bool(req.get(n))}")
        if s.get("enum") and n in values and values[n] != set(s["enum"]):
            problems.append(f"{kind}.{n}: option values {sorted(values[n])} != schema {s['enum']}")
    passes.append(f"{kind} form: required flags and option values checked against the schema")

# 8. staging files agree with the config
cfg = read(os.path.join(SITE, "site.config.js"))
staging = re.search(r"STAGING:\s*(true|false)", cfg).group(1) == "true"
robots = read(os.path.join(SITE, "robots.txt"))
headers = read(os.path.join(SITE, "_headers"))
check(staging, "site.config.js keeps STAGING = true (production is the separate copy from tools/make_production.py)", "site/site.config.js has STAGING = false; site/ is the staging source, leave it true")
no_meta = [p for p in PAGES if not re.search(r'<meta name="robots" content="noindex, nofollow">', raw[p])]
check(not no_meta and "X-Robots-Tag: noindex" in headers and not re.search(r"(?m)^Disallow:\s*/\s*$", robots),
      "staging: every page carries a static noindex robots tag, _headers sends X-Robots-Tag noindex, and robots.txt lets crawlers fetch pages so they can see both",
      "staging noindex incomplete: pages without the robots tag %s, or _headers lacks X-Robots-Tag, or robots.txt blocks crawling (which hides the noindex)" % no_meta)

# Review round 2 (R2-02): the placeholder uploaded first to the public production address.
ph_dir = os.path.join(WEB, "tools", "production", "placeholder")
ph = read(os.path.join(ph_dir, "index.html")) if os.path.exists(os.path.join(ph_dir, "index.html")) else ""
ph_h = read(os.path.join(ph_dir, "_headers")) if os.path.exists(os.path.join(ph_dir, "_headers")) else ""
check(ph and '<meta name="robots" content="noindex, nofollow">' in ph and "X-Robots-Tag: noindex" in ph_h
      and not re.search(r"desk\s*-?\s*drop", ph + ph_h, re.I) and not re.search(r"(?m)^Disallow:\s*/\s*$", read(os.path.join(ph_dir, "robots.txt"))),
      "production placeholder (tools/production/placeholder/): noindex in the page and header, crawlable robots.txt, no name",
      "production placeholder missing, indexable, or carrying the working name")

# 9. Review round 3.
import subprocess  # noqa: E402
sys.path.insert(0, os.path.join(WEB, "tools"))
import preflight  # noqa: E402
for phrase in ["Two photos per office: one on the day your product is placed, and a second on day 3 or day 5.",
               "You sign, pay, and see the card text before it is printed.",
               "We send you the card text before anything is printed. We may edit or decline a sentence that makes a health claim.",
               "Prices do not include sales tax; if any applies, it is shown on the invoice.",
               "If events outside our control move a drop more than once, or by more than three weeks in all, you may cancel for a full refund.",
               "If the seven checks fit, we will suggest a 20-minute call",
               "a short email (your brand and email address only)", "we delete your answers and that email within 12 months"]:
    check(phrase in brands, f"brands page states (G 10 v0.8, R3): {phrase}", f"brands page is missing (R3): {phrase}")
for phrase in ["the placement on drop day", "approve the card text", "card text to approve", "Next step: a 20-minute call"]:
    check(phrase not in brands, f"old brand wording gone (R3): {phrase}", f"old brand wording still on the brand page (R3): {phrase}")
for phrase in ["Name the ingredient, not the person: please don't tell us who has an allergy.",
               "Please don't include anyone's health or personal details.",
               "Please don't tell us about anyone's health: a veto by ingredient is enough.",
               "If your office fits (40 to 250 people on a Tuesday, inside the area on the map), that email carries the one-page participation agreement.",
               "a short email (your company and email address only)", "we delete your answers and that email within 12 months"]:
    check(phrase in offices, f"offices page states (R3): {phrase}", f"offices page is missing (R3): {phrase}")
check("Next, we will email you from" not in offices, "office thank-you no longer promises the agreement to every sender (R3)",
      "office thank-you still promises the agreement to every sender (R3)")
check("and the notification email about them, within 12 months" in docs["privacy"].full_text
      and "we delete the Sheet row and the notification email, and reply to confirm" in docs["privacy"].full_text,
      "privacy page: deletion covers the notification email; deletion requests answered (R3)", "privacy page: notification email missing from retention or deletion (R3)")
notes = {p: preflight.internal_notes(preflight.strip_staging(raw[p])) for p in PAGES}
notes = {p: n for p, n in notes.items() if n}
check(not notes, "no internal note (legal pack, draft notice, SETUP.md, staging...) in any page's text outside staging-only elements",
      "internal notes in page text: %s" % notes)
r = subprocess.run([sys.executable, os.path.join(WEB, "tools", "build_map.py"), "--check"], capture_output=True, text=True)
check(r.returncode == 0, "store map and list match B's current map-public.geojson (%s)" % r.stdout.strip().splitlines()[-1],
      "store map is stale against B's map-public.geojson: run python3 tools/build_map.py, then tools/export_copy.py. " + " | ".join(r.stdout.strip().splitlines()))

for p in passes:
    print("ok -", p)
for p in problems:
    print("FAIL -", p)
print(f"\n{len(passes)} passed, {len(problems)} failed")
sys.exit(1 if problems else 0)
