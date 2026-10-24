#!/usr/bin/env python3
"""Tests for tools/preflight.py and tools/make_production.py (QA.md P19). No network.
Proves the publish gate can open once the founder's steps are done, and that each missing step
keeps it shut: placeholders typed into any page, a stale status line, a name gate that does not
say CLEARED, and a production copy that still carries staging settings.
Usage (from website/): python3 tests/test_preflight.py
"""
import datetime
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


def make_ready(tmp):
    """A copy of site/ with every founder step done, and a legal pack whose gate says CLEARED."""
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
    gate = os.path.join(tmp, "desk-drop-legal-pack", "name-check-log.md")
    open(gate, "w", encoding="utf-8").write("# Name-check log\n\nPublic launch (C): CLEARED 2026-11-18\n")
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
    os.remove(gate)
    b, _ = preflight.check_source(site, desk, today=TODAY)
    t("name gate file missing blocks", any("not found" in x for x in b), "; ".join(b))
    open(gate, "w", encoding="utf-8").write("Public launch (C): CLEARED 2026-11-18\n")

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
