#!/usr/bin/env python3
"""Check the whole outreach folder for the things that drift when two halves are joined.

    python3 tools/check_folder.py          # from desk-drop/desk-drop-outreach/

It reads every document the founder uses (README, HANDOFF, messages/, calls/, sending/, tracking/, handoff/)
and fails (exit 1) on:
  - a date whose weekday is wrong, a drop date that is not a Tuesday or Wednesday or whose five-day window
    touches a blackout, or a Gate 0 date other than Fri 2026-11-13 (CONTRACTS section 3);
  - a bracketed slot that is neither a CONTRACTS placeholder, a slot in messages/04-slot-table.csv, nor one of
    the fill-in markers listed below (catches renamed or misspelled slots);
  - a `next_action`, `reply_type`, `status` or `sequence` value that is not in the shared lists
    (tracking/csv/clay_tracking_columns.csv and CONTRACTS section 4);
  - a switch or count named as `key = ...` that is not in messages/04-slot-state.csv;
  - "Part A" or "Part B" outside a changelog line (the founder sees one folder);
  - a ladder word renamed softer (conversions, ROI, sales lift, acquisition) outside a "never" sentence;
  - the A/B variant rule stated two different ways;
  - a shipped file that README.md does not list;
  - compiled Python bytecode (__pycache__, *.pyc) anywhere outside _work/.
No network access. Standard library only.
"""
import csv
import datetime as dt
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
fails, checks = [], 0


def ok(label, cond):
    global checks
    checks += 1
    if not cond:
        fails.append(label)
        print("FAIL " + label)


def rel(p):
    return os.path.relpath(p, ROOT)


DOCS = []
for top in ("README.md", "HANDOFF.md"):
    if os.path.exists(os.path.join(ROOT, top)):
        DOCS.append(os.path.join(ROOT, top))
for sub in ("messages", "calls", "sending", "tracking", "handoff", os.path.join("messages", "_render")):
    d = os.path.join(ROOT, sub)
    for f in sorted(os.listdir(d)):
        if f.endswith(".md"):
            DOCS.append(os.path.join(d, f))
extra = [a for a in sys.argv[1:] if os.path.exists(a)]      # e.g. a draft of the report text
DOCS += [os.path.abspath(a) for a in extra]

HOLIDAYS = {dt.date.fromisoformat(d) for d in ["2026-11-11", "2026-11-26", "2026-12-25", "2027-01-01", "2027-01-18",
                                                "2027-02-15", "2027-05-31", "2027-06-18", "2027-07-05", "2027-09-06"]}


def bd_add(d, n):
    x, k = d, 0
    while k < n:
        x += dt.timedelta(1)
        if x.weekday() < 5 and x not in HOLIDAYS:
            k += 1
    return x


def blackout(d):
    if (d.month == 12 and d.day >= 18) or (d.month == 8 and d.day >= 18):
        return True
    j4 = dt.date(d.year, 7, 4)
    obs = j4 - dt.timedelta(1) if j4.weekday() == 5 else (j4 + dt.timedelta(1) if j4.weekday() == 6 else j4)
    mon = obs - dt.timedelta(obs.weekday())
    return mon <= d <= mon + dt.timedelta(4)


def drop_ok(d):
    if d.weekday() not in (1, 2):
        return False
    day, end = d, bd_add(d, 4)
    while day <= end:
        if blackout(day):
            return False
        day += dt.timedelta(1)
    return True


# ------------------------------------------------------------------ shared lists
slot_table = list(csv.DictReader(open(os.path.join(ROOT, "messages", "04-slot-table.csv"), encoding="utf-8")))
SLOT_NAMES = set()
for r in slot_table:
    for part in re.findall(r"\[([^\]]+)\]", r["slot"]):
        SLOT_NAMES.add(part.split(":")[0].strip())
state_keys = {r["key"] for r in csv.DictReader(open(os.path.join(ROOT, "messages", "04-slot-state.csv"), encoding="utf-8"))}
clay = {r["column"]: r for r in csv.DictReader(open(os.path.join(ROOT, "tracking", "csv", "clay_tracking_columns.csv"), encoding="utf-8"))}
NEXT_ACTIONS = {v.strip() for v in clay["next_action"]["allowed_values"].split(",")}
REPLY_TYPES = {v.strip() for v in clay["reply_type"]["allowed_values"].split(",")}
STATUSES = {"new", "queued", "contacted", "replied", "call_booked", "call_done", "yes_in_principle", "materials_sent",
            "signed", "paid", "not_now", "no", "wrong_person", "do_not_contact"}
PLACEHOLDERS = {"FOUNDER NAME", "PHONE", "EMAIL", "POSTAL ADDRESS", "WEBSITE", "DOMAIN", "LINKEDIN URL"}
# fill-in markers the founder replaces by hand (not tracker slots)
MARKERS = {
    "SLOT", "SLOTS", "TIME", "PHONE OR LINK", "MONTH", "CONNECTOR FIRST NAME", "REFERRED NAME", "REFERRED COMPANY",
    "RUNS THE PANTRY THERE / RUNS MARKETING THERE", "PANTRY OR SAMPLING", "ONE TRUE REASON", "OFFICE", "BRAND",
    "ONE THING THEY SAID THAT CHANGED YOUR THINKING", "ALLERGEN LINE, VERBATIM FROM THE LABEL", "WHAT ARRIVED",
    "WHAT IS MISSING, BY NUMBER", "BRAND LEGAL NAME", "BRAND ADDRESS", "PRODUCT NAME AND SKU", "COVER-UNTIL DATE",
    "MONTH THEY NAMED, or", "N", "H", "Name", "NOT CLEARED TO NAME", "ROSTER LINE LOCKED",
    # Startup CPG post slots (messages/12, filled from the tracker's post-numbers block)
    "OFFICE CONVERSATIONS", "BRAND CONVERSATIONS", "N GET BRAND OFFERS", "WHAT HAPPENS TO IT", "N ONE PERSON DECIDES",
    "WHO ELSE DECIDES", "TOP YES REASON", "TOP NO REASON", "N WOULD PHOTO AND SURVEY", "TUESDAY RANGE", "N USE A SERVICE",
    "BRAND SPEND RANGE", "WHO SIGNS OFF", "N SEEDED OFFICES", "WHAT HAPPENED", "MEDIAN NUMBER NAMED", "TOP REPORT NEED",
    "TOP BLOCKER", "TOP REPORTING COMPLAINT", "ONE SENTENCE THE NOTES SUPPORT", "QUOTE",
    "SECOND REPORT NEED", "THIRD REPORT NEED", "N TOP NEED", "N SECOND NEED", "N THIRD NEED",
}
SOFT = [r"\bconversions\b", r"\bconversion rates?\b", r"\bROI\b", r"sales lift", r"\bacquisition\b"]   # "post-call conversion" (the brief's own name for the sequences) is allowed
SOFT_OK = ("never", "Never", "No field", "No column", "not ", "Not ", "post-call conversion", "conversion path",
           "-conversion", "conversion.md", "conversion sequence", "Conversion sequences", "conversion step", "conversion emails",
           "Post-call conversion", "Conversion path", "conversion,", "conversion)", "banned", "lift is a must", "\"Lift\"")

for p in DOCS:
    t = open(p, encoding="utf-8").read()
    name = rel(p)
    lines = t.split("\n")
    body_lines = [l for l in lines if not re.match(r"\s*- (Round|Merge)\b", l)]
    body = "\n".join(body_lines)
    # dates
    for m in re.finditer(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? (20\d\d-\d\d-\d\d)", t):
        d = dt.date.fromisoformat(m.group(2))
        ok(f"{name}: '{m.group(0)}' weekday", d.strftime("%a") == m.group(1)[:3])
    for m in re.finditer(r"(?:NEXT )?DROP DATE: \w{3} (20\d\d-\d\d-\d\d)", t):
        ok(f"{name}: drop date {m.group(1)} legal", drop_ok(dt.date.fromisoformat(m.group(1))))
    for m in re.finditer(r"Gate 0[^.\n]{0,25}?\(?(?:Fri )?(20\d\d-\d\d-\d\d)", t):
        ok(f"{name}: Gate 0 date {m.group(1)}", m.group(1) == "2026-11-13")
    # slots
    for m in re.finditer(r"\[([A-Z][A-Za-z0-9 ,'/\-]*?)(?::[^\]]*)?\]", body):
        s = m.group(1).strip()
        if s in PLACEHOLDERS or s in SLOT_NAMES or s in MARKERS:
            continue
        ok(f"{name}: unknown slot [{s}]", False)
    # shared values
    for m in re.finditer(r"`?next_action`? ?(?:=|is) ?`([a-z_]+)`", body):
        ok(f"{name}: next_action {m.group(1)}", m.group(1) in NEXT_ACTIONS)
    for m in re.finditer(r"`?reply_type`? ?= ?`([a-z_]+)`", body):
        ok(f"{name}: reply_type {m.group(1)}", m.group(1) in REPLY_TYPES)
    for m in re.finditer(r"(?<![a-z_])`?status`? ?= ?`([a-z_]+)`", body):
        ok(f"{name}: status {m.group(1)}", m.group(1) in STATUSES)
    for m in re.finditer(r"`((?:office|brand)-(?:[a-z]+)-[A-Z])`", body):
        ok(f"{name}: sequence {m.group(1)}", re.fullmatch(r"(office|brand)-(discovery|selling|conversion)-[A-Z]", m.group(1)) is not None)
    for m in re.finditer(r"`([a-z_]+)(?: = |` = )(?:Y|N|`Y`|`N`)", body):
        k = m.group(1)
        if k in ("do_not_contact", "yes_in_principle", "known_to_founder", "referrer_ok_to_name", "quote_ok_to_share",
                 "shortlist", "controls_budget", "include_sample", "price_1500_mentioned", "budget_probe_asked", "clay_updated",
                 "pantry_owner_named", "owner_can_say_yes_alone", "qual_not_excluded", "founding_roster_named", "public_naming_ok",
                 "newsletter_option", "email_status", "startup_cpg_member", "uses_snack_service", "q3_brands_reach_out",
                 "q3_seeded_offices", "q5_photo_and_survey", "verified_not_excluded", "seen_on_shelf",
                 "office_approvals_complete", "hold_before_outreach"):     # Clay row columns, not state keys
            continue
        if k.startswith(("verified_", "qual_", "q")):
            continue
        ok(f"{name}: state key {k} in 04-slot-state.csv", k in state_keys)
    # one folder, one voice
    for i, l in enumerate(body_lines):
        if re.search(r"\bPart [AB]\b|\bpart [AB]\b", l) and "_work/part" not in l:
            ok(f"{name}: 'Part A/B' in body text: {l.strip()[:80]}", False)
    # ladder words
    for pat in SOFT:
        for m in re.finditer(pat, body, flags=re.I):
            line = body[body.rfind("\n", 0, m.start()) + 1: body.find("\n", m.end())]
            ok(f"{name}: '{m.group(0)}' outside a never/naming context: {line.strip()[:80]}", any(w in line for w in SOFT_OK))

# the variant rule, said once
v05 = open(os.path.join(ROOT, "messages", "05-office-cold-emails.md"), encoding="utf-8").read()
vsend = open(os.path.join(ROOT, "sending", "sending-setup.md"), encoding="utf-8").read()
ok("variant rule in 05 (about 40 each, twice and four more)", "about 40" in v05 and "twice" in v05 and "four more" in v05)
ok("variant rule in sending 6.4 (about 40 each, twice and four more)", "about 40" in vsend and "twice" in vsend and "four more" in vsend)

# README lists every shipped file
readme_p = os.path.join(ROOT, "README.md")
if os.path.exists(readme_p):
    readme = open(readme_p, encoding="utf-8").read()
    for dirpath, dirs, files in os.walk(ROOT):
        # _review/ is the orchestrator's audit folder and REPORT.md is saved by the orchestrator (review round 1, R1-21)
        dirs[:] = [d for d in dirs if d not in ("_work", "__pycache__", "drafts", "_review")]
        if os.path.relpath(dirpath, ROOT).startswith(os.path.join("messages", "examples")):
            continue
        for f in files:
            r = os.path.relpath(os.path.join(dirpath, f), ROOT)
            if r in ("README.md", "REPORT.md"):
                continue
            ok(f"README lists {r}", f"`{r}`" in readme or f"`{f}`" in readme)
    ok("README lists messages/examples/", "messages/examples/" in readme)
    ok("README lists _work/", "_work/" in readme)
else:
    ok("README.md exists", False)
ok("HANDOFF.md exists", os.path.exists(os.path.join(ROOT, "HANDOFF.md")))
# no compiled bytecode ships (review round 3, R3-11): the tools set sys.dont_write_bytecode and .gitignore keeps it out
pyc = [os.path.relpath(os.path.join(dp, f), ROOT) for dp, ds, fs in os.walk(ROOT) for f in fs + ds
       if (f.endswith(".pyc") or f == "__pycache__") and not os.path.relpath(dp, ROOT).startswith("_work")]
ok("no __pycache__ or .pyc outside _work/: " + ", ".join(pyc[:5]), not pyc)
gi = os.path.join(ROOT, ".gitignore")
ok(".gitignore keeps __pycache__/ and *.pyc out", os.path.exists(gi) and "__pycache__/" in open(gi).read() and "*.pyc" in open(gi).read())

print(f"{checks} checks on {len(DOCS)} documents; {len(fails)} failing")
sys.exit(1 if fails else 0)
