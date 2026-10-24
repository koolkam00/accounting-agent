#!/usr/bin/env python3
"""Check the call guides and cards against the plan, and the Part B docs against the hard rules.

    python3 tools/check_guides.py
"""
import os
import re
import sys

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
# question order in the guides follows the plan
pos = [og.find(q if i != 6 else probe) for i, q in enumerate(office, start=1)]
ok("office questions in plan order", pos == sorted(pos) and -1 not in pos)
pos = [bg.find(q.split(" Let them name")[0]) for q in brand]
ok("brand questions in plan order", pos == sorted(pos) and -1 not in pos)

# hard rules across Part B documents
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
