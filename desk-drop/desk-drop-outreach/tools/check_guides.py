#!/usr/bin/env python3
"""Check the call guides and cards against the plan, and the calls, sending, tracking and handoff docs against the hard rules.

    python3 tools/check_guides.py
"""
import os
import re
import sys
sys.dont_write_bytecode = True   # no __pycache__ in the deliverable folder (review round 3, R3-11)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from build_call_cards import plan_questions   # noqa: E402

fails = []


def ok(label, cond):
    print(("ok   " if cond else "FAIL ") + label)
    if not cond:
        fails.append(label)


office, brand, probe = plan_questions()
og = open(os.path.join(ROOT, "calls", "office-call-guide.md"), encoding="utf-8").read()
bg = open(os.path.join(ROOT, "calls", "brand-call-guide.md"), encoding="utf-8").read()
cards = open(os.path.join(ROOT, "_work", "partB", "print", "call-cards.html"), encoding="utf-8").read()
cards_txt = re.sub(r"<[^>]+>", "", cards).replace("&quot;", '"').replace("&#x27;", "'").replace("&amp;", "&")
for i, q in enumerate(office, start=1):
    if i == 6:
        ok(f"office Q6 budget probe verbatim in guide", probe in og)
        ok(f"office Q6 budget probe verbatim on card", probe in cards_txt)
        continue
    ok(f"office Q{i} verbatim in guide", q in og)
    ok(f"office Q{i} verbatim on card", q in cards_txt)
for i, q in enumerate(brand, start=1):
    core = q.split(" Let them name")[0]
    ok(f"brand Q{i} verbatim in guide", core in bg)
    ok(f"brand Q{i} verbatim on card", core in cards_txt)
# the brand close and the founding answer say the same on the card as in the guide (review round 1, R1-10 and R1-03)
close = "Can I send you the details once the first offices have said yes, probably the week of November 16?"
ok("brand close in guide", close in bg)
ok("brand close on card", close in cards_txt)
ok("no stale brand close on card ('once five offices have signed')", "once five offices have signed" not in cards_txt)
ok("founding note-and-case-study term in brand guide", "short note" in bg and "case study" in bg)
ok("founding note-and-case-study term on brand card", "short note" in cards_txt and "case study" in cards_txt)
ok("office guide lists five survey responses", "five survey responses" in og)
# review round 2 (R2-20): two shelf photos on the card as in the guide; "asking", not "talking to", fifteen people
ok("office opening says two shelf photos in guide", "two shelf photos" in og)
ok("office opening says two shelf photos on card", "two shelf photos" in cards_txt and "a shelf photo" not in cards_txt)
ok("no 'talking to about fifteen' in the guides", "talking to about fifteen" not in og + bg)
ok("brand check 5 asks for $1 million per occurrence", "$1 million per occurrence" in bg)
# question order in the guides follows the plan
pos = [og.find(q if i != 6 else probe) for i, q in enumerate(office, start=1)]
ok("office questions in plan order", pos == sorted(pos) and -1 not in pos)
pos = [bg.find(q.split(" Let them name")[0]) for q in brand]
ok("brand questions in plan order", pos == sorted(pos) and -1 not in pos)

# hard rules across the calls, sending, tracking and handoff documents
docs = ["calls/office-call-guide.md", "calls/brand-call-guide.md", "calls/post-call-note-template.md",
        "sending/sending-setup.md", "tracking/how-the-tracker-works.md", "handoff/how-to-fill-handoff-files.md"]
banned = [r"\bconversions?\b", r"\bROI\b", r"sales lift", r"\bacquisition\b", r"guarantee(d)? sales"]
for d in docs:
    t = open(os.path.join(ROOT, d), encoding="utf-8").read()
    for b in banned:
        for m in re.finditer(b, t, flags=re.I):
            line = t[t.rfind("\n", 0, m.start()) + 1: t.find("\n", m.end())]
            allowed = any(w in line for w in ("Never", "never", "Not a sales guarantee", "No column", "not claim", "post-call conversion", "conversion path",
                                               "conversion sequence", "-conversion", "conversion.md", "Phase 1 conversion", "\"Lift\"", "lift is a must", "would not claim",
                                               "will not claim", "No field", "no sales guarantee", "Do you guarantee", "not measured", "objection"))
            ok(f"{d}: '{m.group(0)}' only in a 'never' or naming context", allowed)
    for ph in re.findall(r"\[[A-Z][A-Z ]+\]", t):
        ok(f"{d}: placeholder {ph} is a CONTRACTS form", ph in ("[FOUNDER NAME]", "[PHONE]", "[EMAIL]", "[POSTAL ADDRESS]", "[WEBSITE]", "[DOMAIN]", "[TIME]",
                                                               "[PHONE OR LINK]", "[ONE-PAGER]", "[ROSTER LINE]", "[OFFICE OPENER]", "[INSURANCE LINE]"))
    for dt_ in re.findall(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (20\d\d-\d\d-\d\d)", t):
        import datetime as _dt
        d0 = _dt.date.fromisoformat(dt_[1])
        ok(f"{d}: weekday {dt_[0]} matches {dt_[1]}", d0.strftime("%a") == dt_[0])
    for m in re.finditer(r"DROP DATE: (\w{3}) (20\d\d-\d\d-\d\d)", t):
        import datetime as _dt
        d0 = _dt.date.fromisoformat(m.group(2))
        ok(f"{d}: drop date {m.group(2)} is a Tuesday or Wednesday", d0.weekday() in (1, 2))
print(f"RESULT: {len(fails)} failing")
sys.exit(1 if fails else 0)
