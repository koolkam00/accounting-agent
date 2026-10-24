#!/usr/bin/env python3
"""Mechanical consistency checks for the whole legal pack.

Run from desk-drop/:  python3 desk-drop-legal-pack/_work/check_pack.py
Prints one line per finding and exits 1 if there are any.
"""
import datetime as dt
import pathlib
import re
import sys

PACK = pathlib.Path(__file__).resolve().parent.parent
HEADING = "Draft for attorney review. Not legal advice."
VERSION = r"Version (0\.\d+) · (\d{4}-\d{2}-\d{2})"
NAME = "Desk Drop"
SLOT = "[COMPANY NAME: Desk Drop LLC]"
BRAND_LINE = "`BRAND_NAME = Desk Drop`"
TRADING_NAME_FILES = {"01-name-check-log.md", "02-email-footer-and-checklist.md", "name-check-log.md"}
STORAGE = "off the floor, away from heat and as the label directs"
STORAGE_FILES = {"06", "07", "10", "11"}
# how long cases are held, stated to the broker, the state, the accountant and the brand's broker (review round 2)
HOLD = "up to about four around the December holidays; leftover units the brand asks back can wait up to ten more business days for its return label"
HOLD_FILES = {"06", "07", "09", "11"}
# the federal storage question: every file that offers storage outside the home must point to it (review round 3)
FDA = "21 CFR 1.227"
FDA_FILES = {"06", "07", "08"}
# the filing rule: never file before the attorney hour, so no file may still tie filing to Gate 0 (review round 2)
STALE_FILING = [r"(?:around|near) Gate 0", r"Filed at Gate 0", r"FILING DATE: about 2026-11-13"]
PLACEHOLDER_CASE = r"\[(founder name|phone|email|postal address|website|domain)\]"
BANNED = [r"\bconversions?\b", r"\bROI\b", r"sales lift", r"\blift\b", r"\bacquisition\b", r"\bguarantee[sd]?\b"]
WEEKDAYS = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

docs = sorted(PACK.glob("[0-9][0-9]-*.md"))
numbers = {p.name[:2] for p in docs}
REQUIRED = ["README.md", "REPORT.md", "HANDOFF.md"]  # CONTRACTS section 1
# a reference counts only if its target really exists
names = {p.name for p in PACK.iterdir() if p.is_file()}
findings = []
warnings = []
for req in REQUIRED:
    if not (PACK / req).is_file():
        findings.append(f"{req}: missing (CONTRACTS section 1 requires it)")


def flag(p, msg):
    findings.append(f"{p.name}: {msg}")


def strip_code(text):
    """Text with fenced blocks and inline code removed, for prose checks."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


for p in docs + [PACK / "name-check-log.md"]:
    t = p.read_text()
    prose = strip_code(t)
    if not t.startswith(f"**{HEADING}**"):
        flag(p, "does not open with the review heading")
    for marker in ("AGREEMENT", "NOTICE"):
        for m in re.finditer(rf"<!-- {marker} START -->(.*?)<!-- {marker} END -->", t, re.S):
            if HEADING not in m.group(1):
                flag(p, f"{marker} block lacks the review heading")
    vm = re.search(VERSION, t)
    if not vm:
        flag(p, "version line missing or in the wrong form")
    else:
        for m in re.finditer(r"<!-- AGREEMENT START -->(.*?)<!-- AGREEMENT END -->", t, re.S):
            bm = re.search(r"Version (0\.\d+)\.", m.group(1))
            if bm and bm.group(1) != vm.group(1):
                flag(p, f"agreement block says version {bm.group(1)}, file says {vm.group(1)}")
    # one name per document; index may have none
    n = t.count(NAME)
    if p.name == "00-index.md":
        if n > 1:
            flag(p, f"working name appears {n} times (want 0 or 1)")
    elif n != 1:
        flag(p, f"working name appears {n} times (want 1)")
    if p.name in TRADING_NAME_FILES:
        if n == 1 and BRAND_LINE not in t:
            flag(p, "trading name not set in the form `BRAND_NAME = Desk Drop`")
    elif p.name != "00-index.md" and n == 1 and SLOT not in t:
        flag(p, f"legal name not set in the slot form {SLOT}")
    if "Desk Drop LLC" in t.replace(SLOT, ""):
        flag(p, "bare legal name outside the slot")
    # heading number matches the file number
    m = re.search(r"^# (\d{2}) · ", t, re.M)
    if p.name[:2].isdigit() and (not m or m.group(1) != p.name[:2]):
        flag(p, "H1 number does not match the file number")
    if p.name[:2].isdigit() and p.name != "00-index.md" and "\n## Changelog\n" not in t:
        flag(p, "no changelog section")
    for m in re.finditer(PLACEHOLDER_CASE, t):
        flag(p, f"placeholder in wrong case: {m.group(0)}")
    for pat in BANNED:
        for m in re.finditer(pat, prose, re.I):
            line = prose[prose.rfind("\n", 0, m.start()) + 1: prose.find("\n", m.end())]
            if "guarantee" in m.group(0).lower() and re.search(r"(do not|does not|no|never|not)\b[^.]{0,40}guarantee", line, re.I):
                continue
            flag(p, f"ladder word '{m.group(0)}': {line.strip()[:100]}")
    for m in re.finditer(r"TODO|TBD|XXX", t):
        flag(p, f"stray {m.group(0)}")
    if re.search(r"part [AB] of this pack|part [AB]'s", t, re.I):
        flag(p, "mentions part A or part B")
    # dollar signs must be escaped outside code (GitHub and pandoc read $..$ as math)
    for i, line in enumerate(strip_code(t).split("\n"), 1):
        if re.search(r"(?<!\\)\$", line):
            flag(p, f"unescaped $ on a prose line: {line.strip()[:80]}")
            break
    # cross-references resolve
    for m in re.finditer(r"\b(\d{2}-[a-z0-9-]+\.md)\b", t):
        if m.group(1) not in names:
            flag(p, f"reference to missing file {m.group(1)}")
    for m in re.finditer(r"\b[Ff]iles? (\d{2}(?:(?:, | and | or | to )\d{2})*)\b", t):
        for num in re.findall(r"\d{2}", m.group(1)):
            if num not in numbers:
                flag(p, f"'file {num}' does not exist")
    # weekday names match their dates
    for m in re.finditer(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\.? (\d{4}-\d{2}-\d{2})\b", t):
        d = dt.date.fromisoformat(m.group(2))
        if d.weekday() != WEEKDAYS[m.group(1)]:
            flag(p, f"{m.group(0)} is really a {d.strftime('%A')}")
    if p.name[:2] in STORAGE_FILES and STORAGE not in t:
        flag(p, "shared storage sentence missing")
    if p.name[:2] in HOLD_FILES and (HOLD not in t or t.count("up to about four around") != t.count(HOLD)):
        flag(p, "shared holding-time sentence missing, or a holding time stated without the return-label wait")
    if p.name[:2] in FDA_FILES and FDA not in t:
        flag(p, "FDA food facility registration question (21 CFR 1.227) missing (file 07, follow-up 7)")
    for pat in STALE_FILING:
        for m in re.finditer(pat, t):
            flag(p, f"filing tied to Gate 0 ('{m.group(0)}'); file after the attorney hour (file 04)")

# README, REPORT, HANDOFF: heading, version, escaped dollars, references, weekdays
for req in REQUIRED:
    p = PACK / req
    if not p.is_file():
        continue
    t = p.read_text()
    if not t.startswith(f"**{HEADING}**"):
        flag(p, "does not open with the review heading")
    if not re.search(VERSION, t):
        flag(p, "version line missing or in the wrong form")
    for i, line in enumerate(strip_code(t).split("\n"), 1):
        if re.search(r"(?<!\\)\$", line):
            flag(p, f"unescaped $ on a prose line: {line.strip()[:80]}")
            break
    for m in re.finditer(r"\b(\d{2}-[a-z0-9-]+\.md)\b", t):
        if m.group(1) not in names and req != "HANDOFF.md":
            flag(p, f"reference to missing file {m.group(1)}")
    for m in re.finditer(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\.? (\d{4}-\d{2}-\d{2})\b", t):
        d = dt.date.fromisoformat(m.group(2))
        if d.weekday() != WEEKDAYS[m.group(1)]:
            flag(p, f"{m.group(0)} is really a {d.strftime('%A')}")

# other workstreams' references to this pack (warnings only: their files, not ours)
# (old wording, what it is now, a phrase whose presence on the same line means the line is already current)
STALE_TERMS = [
    ("every office's placement photo",
     "placement confirmation is our email by T+1 listing the offices where the product was placed, each with its photo; an office not placed by T+1 is refunded or credited", None),
    ("on or after it, we keep",
     "add the cut-off: no cancellation from the drop day on", "drop day"),
    ("After that, we keep 50%",
     "add the cut-off: no cancellation from the drop day on; the full price is then due", "drop day"),
]
ROOT = PACK.parent
for f in ROOT.rglob("*"):
    if not f.is_file() or PACK in f.parents or "node_modules" in f.parts or f.suffix not in {".md", ".js", ".json", ".html", ".csv", ".txt"}:
        continue
    try:
        txt = f.read_text(errors="ignore")
    except OSError:
        continue
    for i, line in enumerate(txt.split("\n"), 1):
        for m in re.finditer(r"desk-drop-legal-pack/([0-9]{2}-[a-z0-9-]+\.md)", line):
            if m.group(1) not in names:
                warnings.append(f"WARNING {f.relative_to(ROOT)}:{i} cites missing desk-drop-legal-pack/{m.group(1)}")
        # brand terms restated elsewhere in their pre-round-2 form (file 10, sections 3 and 8)
        for old, new, current in STALE_TERMS:
            if old in line and "_review" not in f.parts and not (current and current in line):
                warnings.append(f"WARNING {f.relative_to(ROOT)}:{i} restates an old brand term ('{old}'); now: {new}")

# figures.csv shape (CONTRACTS 6.7)
import csv
with open(PACK / "figures.csv", newline="") as fh:
    rows = list(csv.DictReader(fh))
want = ["item", "low_usd", "high_usd", "working_usd", "status", "source_url", "source_date", "timing", "notes"]
if not rows or list(rows[0].keys()) != want:
    findings.append("figures.csv: header differs from CONTRACTS 6.7")
for r in rows:
    if not re.fullmatch(r"plan estimate|needs quote|verified \d{4}-\d{2}-\d{2}", r["status"]):
        findings.append(f"figures.csv: {r['item']} has status '{r['status']}'")
    for c in ("low_usd", "high_usd", "working_usd"):
        if not re.fullmatch(r"\d+|unknown", r[c]):
            findings.append(f"figures.csv: {r['item']} {c} = '{r[c]}'")
    for pat in STALE_FILING:
        if re.search(pat, r["timing"] + r["notes"]):
            findings.append(f"figures.csv: {r['item']} ties filing to Gate 0")
    for m in re.finditer(r"\b(\d{2}-[a-z0-9-]+\.md)\b", r["notes"] + r["timing"]):
        if m.group(1) not in names:
            findings.append(f"figures.csv: {r['item']} refers to missing {m.group(1)}")

for f in findings:
    print(f)
for w in sorted(set(warnings)):
    print(w)
print(f"{len(docs) + 1} documents, {sum((PACK / r).is_file() for r in REQUIRED)} of {len(REQUIRED)} required files and figures.csv checked, "
      f"{len(findings)} findings, {len(set(warnings))} warnings about other folders")
sys.exit(1 if findings else 0)
