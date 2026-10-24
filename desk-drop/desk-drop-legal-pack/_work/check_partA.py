#!/usr/bin/env python3
"""Mechanical checks on part A files. Run: python3 desk-drop-legal-pack/_work/check_partA.py
Fails loudly; prints one line per finding."""
import pathlib, re, sys

PACK = pathlib.Path(__file__).resolve().parent.parent
FILES = sorted([p for p in PACK.glob("1[0-9]-*.md")] + [p for p in PACK.glob("3[0-9]-*.md")])
HEADING = "Draft for attorney review. Not legal advice."
ALLOWED_PLACEHOLDERS = {"[FOUNDER NAME]", "[PHONE]", "[EMAIL]", "[POSTAL ADDRESS]", "[WEBSITE]", "[DOMAIN]"}
# words that must not appear as claims (ladder rule, CONTRACTS section 2)
BANNED = [r"\bconversions?\b", r"\bROI\b", r"sales lift", r"\blift\b", r"\bacquisition\b", r"\bguarantee[sd]?\b"]
bad = 0
for p in FILES:
    t = p.read_text()
    n = t.count("Desk Drop")
    if n != 1:
        print(f"{p.name}: company name appears {n} times (want 1)"); bad += 1
    if not t.lstrip().startswith(f"**{HEADING}**"):
        print(f"{p.name}: does not open with the review heading"); bad += 1
    for marker in ("AGREEMENT", "NOTICE"):
        m = re.search(rf"<!-- {marker} START -->(.*?)<!-- {marker} END -->", t, re.S)
        if m and HEADING not in m.group(1):
            print(f"{p.name}: {marker} block lacks the review heading"); bad += 1
    # lower-case or odd-form versions of the shared placeholders
    for m in re.finditer(r"\[(founder name|phone|email|postal address|website|domain)\]", t):
        print(f"{p.name}: placeholder in wrong case: {m.group(0)}"); bad += 1
    for pat in BANNED:
        for m in re.finditer(pat, t, re.I):
            line = t[t.rfind("\n", 0, m.start())+1 : t.find("\n", m.end())]
            # "guarantee" is allowed only in a negation ("do not guarantee", "no guarantee", "never ... guaranteed")
            if "guarantee" in m.group(0).lower() and re.search(r"(do not|does not|no|never|not)\b[^.]{0,40}guarantee", line, re.I):
                continue
            print(f"{p.name}: check wording '{m.group(0)}': {line.strip()[:120]}"); bad += 1
    # stray TODOs
    for m in re.finditer(r"TODO|TBD|XXX", t):
        print(f"{p.name}: stray {m.group(0)}"); bad += 1
print(f"{len(FILES)} files checked, {bad} findings")
sys.exit(1 if bad else 0)
