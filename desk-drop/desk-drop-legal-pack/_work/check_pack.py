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
VERSION = "Version 0.5 · 2026-10-24"
NAME = "Desk Drop"
SLOT = "[COMPANY NAME: Desk Drop LLC]"
BRAND_LINE = "`BRAND_NAME = Desk Drop`"
TRADING_NAME_FILES = {"01-name-check-log.md", "02-email-footer-and-checklist.md", "name-check-log.md"}
STORAGE = "off the floor, away from heat and as the label directs"
STORAGE_FILES = {"06", "07", "10", "11"}
PLACEHOLDER_CASE = r"\[(founder name|phone|email|postal address|website|domain)\]"
BANNED = [r"\bconversions?\b", r"\bROI\b", r"sales lift", r"\blift\b", r"\bacquisition\b", r"\bguarantee[sd]?\b"]
WEEKDAYS = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

docs = sorted(PACK.glob("[0-9][0-9]-*.md"))
numbers = {p.name[:2] for p in docs}
names = {p.name for p in docs} | {"name-check-log.md", "figures.csv", "README.md", "REPORT.md", "HANDOFF.md"}
findings = []


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
    if VERSION not in t:
        flag(p, "version line missing or different")
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
    for m in re.finditer(r"\b(\d{2}-[a-z0-9-]+\.md)\b", r["notes"] + r["timing"]):
        if m.group(1) not in names:
            findings.append(f"figures.csv: {r['item']} refers to missing {m.group(1)}")

for f in findings:
    print(f)
print(f"{len(docs) + 1} documents and figures.csv checked, {len(findings)} findings")
sys.exit(1 if findings else 0)
