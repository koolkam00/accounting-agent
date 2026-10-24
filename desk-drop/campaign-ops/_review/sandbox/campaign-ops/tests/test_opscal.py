#!/usr/bin/env python3
"""Calendar tests against CONTRACTS section 3. Run: python3 tests/test_opscal.py"""
import datetime as dt, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import opscal as C

fails = []
def eq(a, b, what):
    if a != b:
        fails.append("%s: got %s, want %s" % (what, a, b))

# 1. Every CONTRACTS holiday is computed.
for s in C.CONTRACTS_HOLIDAYS:
    if not C.is_holiday(dt.date.fromisoformat(s)):
        fails.append("holiday missing " + s)
# 2. Campaign zero, CONTRACTS section 3.
s = C.sop_dates("2027-01-12")
eq(C.problems("2027-01-12"), [], "campaign zero valid")
eq(s["ship_by"].isoformat(), "2026-12-28", "hard T-10")
eq(s["ship_by_requested"].isoformat(), "2026-12-22", "requested ship-by")
eq(s["receive"].isoformat(), "2027-01-05", "T-5")
eq(s["window_end"].isoformat(), "2027-01-19", "T+4 (MLK skipped)")
eq(s["report_due"].isoformat(), "2027-01-22", "T+7 = Gate 2")
eq(s["debrief"].isoformat(), "2027-01-27", "T+10")
eq(s["redemption_check"].isoformat(), "2027-02-11", "T+30 calendar")
# 3. Stretch option and standard runs are valid; stretch window must close by Thu 2026-12-17.
for d in ("2026-12-08", "2027-02-09", "2027-02-23", "2027-03-23", "2027-04-06"):
    eq(C.problems(d), [], "valid " + d)
eq(C.window("2026-12-09")[-1].isoformat(), "2026-12-15", "Wed 9 Dec window")
eq(bool(C.problems("2026-12-15")), True, "Tue 15 Dec window overlaps 18 Dec")
# 4. Refusals: Monday, Friday, Thursday, blackouts, holiday.
for d in ("2027-01-11", "2027-01-15", "2027-01-14", "2026-12-22", "2026-12-16", "2027-07-06",
          "2027-08-17", "2027-08-24", "2026-11-11", "2027-12-15"):
    eq(bool(C.problems(d)), True, "refused " + d)
# 5. July 4 week 2027: 4 July is a Sunday, observed Monday 5 July, blackout Mon 5 to Fri 9 July.
eq([x.isoformat() for x in C.july4_week(2027)], ["2027-07-05", "2027-07-09"], "July 4 week 2027")
eq([x.isoformat() for x in C.july4_week(2026)], ["2026-06-29", "2026-07-03"], "July 4 week 2026 (Sat, obs Fri 3)")
eq(bool(C.problems("2027-06-29")), True, "Tue 29 Jun 2027: window reaches Tue 6 Jul, inside the 5-9 Jul blackout")
eq(C.problems("2027-06-22"), [], "Tue 22 Jun 2027 window ends Mon 28 Jun")
# 6. Exhaustive: no valid date in 2026-10-24..2028-12-31 is a Mon/Fri/holiday or touches a blackout.
d = dt.date(2026, 10, 24); n = 0
while d <= dt.date(2028, 12, 31):
    if C.is_valid(d):
        n += 1
        if d.weekday() not in (1, 2): fails.append("valid non Tue/Wed " + d.isoformat())
        for x in C.window(d):
            if C.blackout_hits(x, x): fails.append("valid window in blackout " + d.isoformat())
            if not C.is_business_day(x): fails.append("window day not business " + d.isoformat())
        if C.slip(d) <= d or not C.is_valid(C.slip(d)): fails.append("slip " + d.isoformat())
    d += dt.timedelta(days=1)
# 7. window_day
eq(C.window_day("2027-01-12", "2027-01-19"), 5, "day 5 across MLK")
eq(C.window_day("2027-01-12", "2027-01-13"), 2, "day 2")
print("valid drop days 2026-10-24..2028-12-31:", n)

if fails:
    print("FAIL"); [print("  -", f) for f in fails]; sys.exit(1)
print("PASS test_opscal")
