#!/usr/bin/env python3
"""Tests for tools/preflight.py and tools/make_production.py (QA.md P19). No network.
Proves the publish gate can open once the founder's steps are done, and that each missing step
keeps it shut: placeholders typed into any page, a stale status line, a name gate that does not
say CLEARED, a CLEARED line for another name or a later date (review round 3), an internal note
in a page's text, and a production copy that still carries staging settings or staging text.
Usage (from website/): python3 tests/test_preflight.py
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WEB, "tools"))
import preflight  # noqa: E402

TODAY = datetime.date(2026, 10, 24)
passed, failed = [], []


def t(name, cond, detail=""):
    (passed if cond else failed).append(name + ("" if cond else " :: " + detail))


FILLED = {
    "DOMAIN": "sample.example", "CONTACT_EMAIL": "hello@sample.example", "PHONE": "", "POSTAL_ADDRESS": "SAMPLE 1 Example Street",
    "FOUNDER_NAME": "SAMPLE Founder", "FOUNDER_LINKEDIN": "https://www.linkedin.com/in/sample", "COMPANY_LEGAL_NAME": "SAMPLE Company LLC",
    "FORM_ENDPOINT": "https://script.google.com/macros/s/SAMPLEabc123/exec", "ROSTER_STATUS_DATE": "2026-10-20",
}


def set_cfg(cfg, key, value):
    new, n = re.subn(r'(?m)^(\s*%s:\s*)"[^"]*"' % key, lambda m: m.group(1) + '"%s"' % value, cfg, count=1)
    assert n == 1, key
    return new


CLEARED_LINE = 'Public launch (C): CLEARED 2026-10-20 for "Desk Drop"'


def write_brand_json(tmp, name):
    d = os.path.join(tmp, "desk-drop-identity")
    os.makedirs(d, exist_ok=True)
    json.dump({"BRAND_NAME": name, "TAGLINE": "SAMPLE"}, open(os.path.join(d, "brand.json"), "w", encoding="utf-8"))


def make_ready(tmp):
    """A copy of site/ with every founder step done, the identity's brand.json on the same name,
    and a legal pack whose gate says CLEARED for that name."""
    site = os.path.join(tmp, "website", "site")
    shutil.copytree(os.path.join(WEB, "site"), site)
    p = os.path.join(site, "site.config.js")
    cfg = open(p, encoding="utf-8").read()
    for k, v in FILLED.items():
        cfg = set_cfg(cfg, k, v)
    open(p, "w", encoding="utf-8").write(cfg)
    for page in preflight.PAGES:
        f = os.path.join(site, page + ".html")
        s = open(f, encoding="utf-8").read()
        s = re.sub(r'<p class="draft-flag">Draft for attorney review\. Not legal advice\.</p>\n?', "", s)
        s = s.replace('<span class="ph">[DATE]</span>', "2026-12-01")
        s = re.sub(r'<span class="ph">\[BRAND PRIVACY POLICY URL\]</span>', "the privacy policy linked from the survey", s)
        s = re.sub(r'<span class="ph">\[BRAND\]</span>', "the brand named on the card", s)
        open(f, "w", encoding="utf-8").write(s)
    os.makedirs(os.path.join(tmp, "desk-drop-legal-pack"))
    for fname, _ in preflight.AGREEMENTS:  # cleared by the attorney: no draft heading
        open(os.path.join(tmp, "desk-drop-legal-pack", fname), "w", encoding="utf-8").write("# SAMPLE agreement, cleared\n")
    write_brand_json(tmp, "Desk Drop")
    gate = os.path.join(tmp, "desk-drop-legal-pack", "name-check-log.md")
    open(gate, "w", encoding="utf-8").write("# Name-check log\n\n" + CLEARED_LINE + "\n")
    return site, tmp, gate


with tempfile.TemporaryDirectory() as tmp:
    site, desk, gate = make_ready(tmp)
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("every founder step done: source checks pass (gate can open)", b == [], "; ".join(b))

    # The shipped site/ is blocked today, including the name gate.
    b, _ = preflight.check_source(today=TODAY)
    t("shipped site/: blocked (placeholders, draft headings, name gate HOLD)", any("HOLD" in x for x in b) and any("FORM_ENDPOINT" in x for x in b), "; ".join(b))

    # Name gate fails closed.
    open(gate, "w", encoding="utf-8").write("Gate status: HOLD for any print run (D) and any public launch (C).\n")
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("name gate HOLD blocks", any("HOLD" in x for x in b), "; ".join(b))
    open(gate, "w", encoding="utf-8").write("Gate status: reworded, for example 'pending for print (D) and public launch (C)'.\n")
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("name gate reworded without CLEARED still blocks", any("CLEARED" in x for x in b), "; ".join(b))
    # Review round 2 (R2-01): negative or conditional wordings that contain "cleared" and a date
    # must keep the gate shut. Only the exact line opens it.
    for wording in [
        "Public launch (C): NOT CLEARED as of 2026-11-18",
        "Public launch (C): not cleared 2026-11-18",
        "Public launch (C): CLEARED 2026-11-18 pending attorney",
        "public launch (C) not yet cleared; decision expected 2026-11-20",
        "public launch (c): cleared 2026-11-18",
        "**Public launch (C): CLEARED 2026-10-20 for \"Desk Drop\"**",
        "Public launch (C): CLEARED",
        # Review round 3 (R3-01): the line must name the name, in straight double quotes.
        "Public launch (C): CLEARED 2026-10-20",
        "Public launch (C): CLEARED 2026-10-20 for Desk Drop",
        "Public launch (C): CLEARED 2026-10-20 for \u201cDesk Drop\u201d",
        "Public launch (C): CLEARED 2026-10-20 for \"Desk Drop\" pending attorney",
        "Public launch (C): CLEARED 2026-10-20 for \"desk drop\"",
    ]:
        open(gate, "w", encoding="utf-8").write("# Name-check log\n\n" + wording + "\n")
        b, _ = preflight.check_source(site, desk, today=TODAY)
        t("name gate blocks on: " + wording, any(x.startswith("name gate") for x in b), "; ".join(b))
    open(gate, "w", encoding="utf-8").write(CLEARED_LINE + "\nNote: public launch (C) only if the attorney agrees.\n")
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("name gate blocks when a CLEARED line sits beside a conditional line about the launch", any("negative or conditional" in x for x in b), "; ".join(b))
    open(gate, "w", encoding="utf-8").write("# Name-check log\n\n" + CLEARED_LINE + "  \n\nPrint run (D): CLEARED 2026-10-20\n")
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("the exact line (trailing spaces allowed) opens the name gate", not any(x.startswith("name gate") for x in b), "; ".join(b))

    # Review round 3 (R3-01): the gate is bound to the name and the date.
    # The legal pack's recommended path: "Desk Drop" treated as taken, a fallback cleared, and the
    # founder forgets the rename. The site still says "Desk Drop", so the gate must stay shut.
    open(gate, "w", encoding="utf-8").write('# Name-check log\n\n**Name checked:** `BRAND_NAME = Pantry Relay` (fallback; Desk Drop treated as taken)\n\n'
                                            'Public launch (C): CLEARED 2026-10-20 for "Pantry Relay"\n')
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("a CLEARED line for a different name (fallback cleared, site not renamed) blocks", any('clears "Pantry Relay"' in x for x in b), "; ".join(b))
    open(gate, "w", encoding="utf-8").write('Public launch (C): CLEARED 2099-01-01 for "Desk Drop"\n')
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("a CLEARED line dated after today blocks", any("after today" in x for x in b), "; ".join(b))
    open(gate, "w", encoding="utf-8").write('Public launch (C): CLEARED 2026-10-24 for "Desk Drop"\n')
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("the same name with today's date opens the name gate", b == [], "; ".join(b))
    open(gate, "w", encoding="utf-8").write('Public launch (C): CLEARED 2026-10-20 for "Desk Drop"\nPublic launch (C): CLEARED 2026-10-21 for "Pantry Relay"\n')
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("a log that clears two different names blocks", any("more than one name" in x for x in b), "; ".join(b))
    # The identity's brand.json must carry the same name (D's HANDOFF).
    open(gate, "w", encoding="utf-8").write(CLEARED_LINE + "\n")
    write_brand_json(desk, "Pantry Relay")
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("brand.json on another name than site.config.js blocks", any("brand.json" in x for x in b), "; ".join(b))
    # The full rename path opens: site renamed, brand.json renamed, the log clears the new name.
    cp0 = os.path.join(site, "site.config.js")
    cfg0 = open(cp0, encoding="utf-8").read()
    open(cp0, "w", encoding="utf-8").write(set_cfg(cfg0, "BRAND_NAME", "Pantry Relay"))
    open(gate, "w", encoding="utf-8").write('Public launch (C): CLEARED 2026-10-20 for "Pantry Relay"\n')
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("rename done everywhere and the log clears the new name: the gate opens", b == [], "; ".join(b))
    open(cp0, "w", encoding="utf-8").write(cfg0)
    write_brand_json(desk, "Desk Drop")
    open(gate, "w", encoding="utf-8").write(CLEARED_LINE + "\n")
    os.remove(gate)
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("name gate file missing blocks", any("not found" in x for x in b), "; ".join(b))
    open(gate, "w", encoding="utf-8").write(CLEARED_LINE + "\n")

    # Agreements whose terms the brand page repeats (R2-09).
    g10 = os.path.join(desk, "desk-drop-legal-pack", "10-brand-campaign-agreement.md")
    open(g10, "w", encoding="utf-8").write("**Draft for attorney review. Not legal advice.**\n\n# 10 SAMPLE\n")
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("brand agreement (G 10) still marked draft blocks", any("10-brand-campaign-agreement.md" in x for x in b), "; ".join(b))
    os.remove(g10)
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("brand agreement (G 10) missing blocks", any("10-brand-campaign-agreement.md" in x and "not found" in x for x in b), "; ".join(b))
    open(g10, "w", encoding="utf-8").write("# SAMPLE agreement, cleared\n")
    b, _ = preflight.check_source(today=TODAY)
    t("shipped legal pack today: both agreements still drafts, so publishing blocks", sum("legal pack:" in x for x in b) == 2, "; ".join(b))

    # Status line freshness.
    b, _ = preflight.check_source(site, desk, today=TODAY + datetime.timedelta(days=30))
    t("status line older than 14 days blocks", any("ROSTER_STATUS_DATE" in x for x in b), "; ".join(b))

    # Placeholders typed into a page (the survey notice's brand slots), outside the mock-ups.
    sp = os.path.join(site, "survey-privacy.html")
    orig = open(sp, encoding="utf-8").read()
    open(sp, "w", encoding="utf-8").write(orig.replace("the brand named on the card", '<span class="ph">[BRAND]</span>', 1))
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("a [BRAND] slot left in survey-privacy.html blocks", any("[BRAND]" in x for x in b), "; ".join(b))
    open(sp, "w", encoding="utf-8").write(orig)
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("the report and card mock-ups' [n] and [CODE] are not counted as placeholders", b == [], "; ".join(b))

    # Internal notes in a page's text (review round 3, R3-06), outside comments and staging-only elements.
    open(sp, "w", encoding="utf-8").write(orig.replace('<p class="muted">This is the notice the anonymous employee survey links to.</p>',
        '<p class="muted">Its text is the legal pack\'s draft notice (version 0.6), unchanged.</p>', 1))
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("a builder note about the legal pack's draft notice in a page blocks", any("internal note" in x and "legal pack" in x for x in b), "; ".join(b))
    open(sp, "w", encoding="utf-8").write(orig)
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("staging-only elements and HTML comments are not counted as internal notes in site/", not any("internal note" in x for x in b), "; ".join(b))

    # Optional contact lines: "" hides, a bracket blocks.
    cp = os.path.join(site, "site.config.js")
    cfg = open(cp, encoding="utf-8").read()
    open(cp, "w", encoding="utf-8").write(set_cfg(cfg, "PHONE", "[PHONE]"))
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("PHONE left as [PHONE] blocks", any("PHONE" in x for x in b), "; ".join(b))
    open(cp, "w", encoding="utf-8").write(cfg)

    # The production copy: a SAMPLE build passes its checks; site/ itself (staging) does not.
    out = os.path.join(tmp, "publish")
    subprocess.run([sys.executable, os.path.join(WEB, "tools", "make_production.py"), "--draft", "--out", out, "--config", cp], check=True, capture_output=True)
    b, _ = preflight.check_build(out)
    t("production copy (SAMPLE settings) passes the build checks", b == [], "; ".join(b))
    # Review round 3 (R3-05): no staging element or staging wording in the production HTML.
    raw = {pg: open(os.path.join(out, pg + ".html"), encoding="utf-8").read() for pg in preflight.PAGES}
    t("production copy: no staging bar, photo slot, form staging note or HTML comment (other than its own mark)",
      not any(re.search(r"staging-bar|staging-only|data-staging-form|Staging|not yet cleared|SETUP\.md", h) or h.count("<!--") != 1 for h in raw.values()),
      ", ".join(pg for pg, h in raw.items() if re.search(r"staging-bar|staging-only|data-staging-form|Staging|not yet cleared|SETUP\.md", h) or h.count("<!--") != 1))
    bp = os.path.join(out, "brands.html")
    open(bp, "w", encoding="utf-8").write(raw["brands"].replace("<main", '<p class="staging-bar">Staging preview, not public. The name is a working name and not yet cleared.</p>\n<main', 1))
    b, _ = preflight.check_build(out)
    t("a staging bar left in the production copy blocks", any("staging" in x.lower() and "brands.html" in x for x in b), "; ".join(b))
    open(bp, "w", encoding="utf-8").write(raw["brands"])
    b, _ = preflight.check_build(os.path.join(WEB, "site"))
    t("site/ used as if it were the production copy is blocked (staging flag, noindex, robots)", any("STAGING" in x for x in b) and any("noindex" in x for x in b), "; ".join(b))
    # make_production refuses to overwrite a folder it did not write.
    stray = os.path.join(tmp, "stray")
    os.makedirs(stray)
    open(os.path.join(stray, "keep.txt"), "w").write("x")
    r = subprocess.run([sys.executable, os.path.join(WEB, "tools", "make_production.py"), "--draft", "--out", stray, "--config", cp], capture_output=True, text=True)
    t("make_production.py will not delete a folder it did not write", r.returncode != 0 and os.path.exists(os.path.join(stray, "keep.txt")), r.stderr)
    # Non-draft build refuses while the real preflight blocks.
    r = subprocess.run([sys.executable, os.path.join(WEB, "tools", "make_production.py"), "--out", os.path.join(tmp, "p2")], capture_output=True, text=True)
    t("make_production.py writes nothing while the preflight blocks", r.returncode != 0 and not os.path.exists(os.path.join(tmp, "p2")), r.stdout[-300:])

for p in passed:
    print("ok -", p)
for f in failed:
    print("FAIL -", f)
print(f"\n{len(passed)} passed, {len(failed)} failed")
sys.exit(1 if failed else 0)
