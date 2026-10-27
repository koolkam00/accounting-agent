#!/usr/bin/env python3
"""Build sending/warmup-schedule.csv and check it.

    python3 tools/build_warmup.py                          # default start: first cold email Mon 2026-11-09
    python3 tools/build_warmup.py --first-cold 2026-11-16  # the late start (sending-setup.md section 0)

The schedule is a recommendation (judgment, not a published standard; see sending/sending-setup.md section 3).
Worst case assumed: nobody replies, so every first touch by email also gets touch 2 (+3 business days) and
touch 3 (+7 business days), the timing in messages/05 and 06.

Week 1 and week 2 send no cold email at all. From Thu 2026-10-29 (SPF and DKIM pass) the new address carries
real two-way mail only: warm asks, replies to accepted LinkedIn contacts, walk-in follow-ups and post-call emails
(column warm_email_from_domain_target). Cold email starts on a Monday no earlier than Mon 2026-11-09, and only once
the four conditions in sending-setup.md section 0 hold.

The script fails (exit 1) if, for the start it writes AND for both the default and the late start:
  - any day's cold email (new + touch 2 + touch 3) goes over its cap;
  - anything is scheduled on a weekend, a federal holiday or a no-send day;
  - any cold email is scheduled before the first cold day, or the first cold day is before Mon 2026-11-09
    or is not a Monday;
  - warm mail from the new address is scheduled before Thu 2026-10-29.
"""
import argparse
import csv
import datetime as dt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = dt.date
HOLIDAYS = {D(2026, 11, 11), D(2026, 11, 26), D(2026, 12, 25), D(2027, 1, 1)}   # CONTRACTS section 3
LIGHT = {D(2026, 11, 25): "Day before Thanksgiving: no new cold first touches; due follow-ups still go.",
         D(2026, 11, 27): "Day after Thanksgiving: many people out. No cold email at all; follow-ups due today go on Monday."}
NOSEND = {D(2026, 11, 27)}             # a business day in CONTRACTS, but a no-send day in this calendar
START = D(2026, 10, 26)                # week 1 Monday; the domain is bought today (sending-setup.md section 1)
DOMAIN_BOUGHT = D(2026, 10, 26)
DOMAIN_AUTH = D(2026, 10, 29)          # SPF and DKIM pass on a test email: warm mail from [DOMAIN] may start
EARLIEST_COLD = D(2026, 11, 9)         # review round 1: never earlier than the Monday of week 3
DEFAULT_COLD = D(2026, 11, 9)
LATE_COLD = D(2026, 11, 16)            # if fewer than 10 two-way threads by Fri 2026-11-06
NRD_DAYS = 32                          # Palo Alto "Newly-Registered Domains" window (sending-setup.md 3.2, S17)
END = D(2026, 12, 11)                  # Gate 1
GATE0 = D(2026, 11, 13)

# new cold first touches by email, per business day (both sides together), by week of the ramp
# (ramp week 1 is the week of the first cold email)
RAMP = {1: [3, 4, 5, 5, 5], 2: [6, 7, 8, 8, 8], 3: [8, 8, 9, 9, 10]}
RAMP_LATER = [10, 10, 10, 10, 10]
CAP = {1: 20, 2: 20, 3: 30, 4: 30}     # all cold email from [DOMAIN] in a day: new + touch 2 + touch 3
CAP_LATER = 40
WARM_TARGET_EARLY = {D(2026, 10, 29): 3, D(2026, 10, 30): 3}   # first two days the address is authenticated
WARM_TARGET_BEFORE_COLD = 5            # each sending day of week 2 (and week 3 on the late start)
WARM_TARGET_AFTER_COLD = 3             # keep real two-way mail in the mix once cold email runs


def bd(d):
    return d.weekday() < 5 and d not in HOLIDAYS and d not in NOSEND


def add_bd(d, n):
    k = 0
    while k < n:
        d += dt.timedelta(days=1)
        if bd(d):
            k += 1
    return d


def week(d):
    return (d - START).days // 7 + 1


def phase(d):
    return "discovery (weeks 1 to 3)" if d <= GATE0 else "recruit and sell (weeks 4 to 7)"


def build(first_cold):
    days = []
    d = START
    while d <= END:
        if d.weekday() < 5:
            days.append(d)
        d += dt.timedelta(days=1)
    w0 = week(first_cold)
    new = {}
    for d in days:
        if d < first_cold or not bd(d) or d in LIGHT:
            new[d] = 0
            continue
        r = week(d) - w0 + 1
        new[d] = (RAMP.get(r) or RAMP_LATER)[d.weekday()]
    t2 = {d: 0 for d in days}
    t3 = {d: 0 for d in days}
    for d, n in new.items():
        if n:
            a, b = add_bd(d, 3), add_bd(d, 7)
            if a in t2:
                t2[a] += n
            if b in t3:
                t3[b] += n
    rows, problems = [], []
    nrd_noted = False
    if first_cold < EARLIEST_COLD:
        problems.append(f"first cold day {first_cold} is before {EARLIEST_COLD}")
    if first_cold.weekday() != 0:
        problems.append(f"first cold day {first_cold} is not a Monday")
    for d in days:
        w = week(d)
        r = w - w0 + 1
        total = new[d] + t2[d] + t3[d]
        cap = (CAP.get(r, CAP_LATER)) if d >= first_cold else 0
        if not bd(d):
            warm = 0
        elif d < DOMAIN_AUTH:
            warm = 0
        elif d in WARM_TARGET_EARLY:
            warm = WARM_TARGET_EARLY[d]
        elif d < first_cold:
            warm = WARM_TARGET_BEFORE_COLD
        else:
            warm = WARM_TARGET_AFTER_COLD
        age = (d - DOMAIN_BOUGHT).days
        note = ""
        if d in HOLIDAYS and d not in NOSEND:
            note = "Federal holiday (CONTRACTS section 3): no email from [DOMAIN]; follow-ups move to the next business day."
        elif d in LIGHT:
            note = LIGHT[d]
        elif w == 1:
            note = {0: "Setup day: domain, Workspace, MX, SPF. Warm asks from your existing address, phone or LinkedIn (the new address is not authenticated yet).",
                    1: "Walk sessions 1 and 2 (B's walk.csv), 8 to 11 am; walk-in asks; LinkedIn invitations without a note. Warm asks still from your existing address.",
                    2: "Walk sessions 3 and 4; DKIM key generated and published (24 to 72 hours after Gmail was turned on). Warm asks still from your existing address.",
                    3: "Test email to your own Gmail: SPF and DKIM PASS. From today every warm ask, walk-in follow-up, LinkedIn contact who asked for email and post-call email goes from [EMAIL].",
                    4: "First Friday scorecard. DMARC (p=none) goes in once SPF and DKIM have passed for 48 hours: today or Monday. Count your two-way threads from [EMAIL]."}[d.weekday()]
        elif d < first_cold and w == 2:
            note = {0: "No cold email this week. Walk sessions 5 to 8 on Tuesday and Wednesday; LinkedIn messages to accepted invitations; warm asks and referrals from [EMAIL].",
                    1: "Walk sessions 5 and 6, 8 to 11 am. Walk-in follow-ups go from [EMAIL] the same day.",
                    2: "Walk sessions 7 and 8. DMARC must be published by today for a Mon 2026-11-09 start (3 business days before).",
                    3: "Inbox test: one email from [EMAIL] to your own Gmail and Outlook.com accounts. Both must land in the inbox.",
                    4: "Decision day: are all four conditions met (sending-setup.md section 0)? Yes: cold email starts Monday. No: rebuild with --first-cold 2026-11-16."}[d.weekday()]
        elif d < first_cold:
            note = "Late start: no cold email yet. Same mix as week 2: walk sessions, LinkedIn, warm asks and referrals from [EMAIL]."
        elif d == first_cold:
            note = ("First cold email from [DOMAIN], at 3, only if all four conditions hold (sending-setup.md section 0): "
                    "SPF, DKIM and DMARC PASS; DMARC published 3 business days ago; inbox at Gmail and Outlook.com; 10 or more two-way threads.")
        if age > NRD_DAYS and bd(d) and not nrd_noted and not note:
            nrd_noted = True
            note = f"[DOMAIN] is {age} days old today: past the 32-day 'newly registered' window some corporate web filters block (section 3.2). Links to [DOMAIN] are still kept out of first touches."
        if d >= first_cold and total > cap:
            problems.append(f"{d} total {total} > cap {cap}")
        if (new[d] or t2[d] or t3[d] or warm) and not bd(d):
            problems.append(f"{d} sends on a non-business or no-send day")
        if (new[d] or t2[d] or t3[d]) and d < first_cold:
            problems.append(f"{d} cold email before {first_cold}")
        if warm and d < DOMAIN_AUTH:
            problems.append(f"{d} warm mail from [DOMAIN] before SPF and DKIM pass ({DOMAIN_AUTH})")
        discovery = d <= GATE0
        other = (10 - new[d]) if discovery else ""
        if d == START:
            other = 5
        rows.append({
            "date": d.isoformat(), "weekday": d.strftime("%a"), "week": w, "phase": phase(d),
            "domain_age_days": age,
            "cold_email_first_touches": new[d], "email_touch_2_due": t2[d], "email_touch_3_due": t3[d],
            "cold_email_total_worst_case": total, "cold_email_daily_cap": cap,
            "warm_email_from_domain_target": warm,
            "other_channel_first_touches_target": other,
            "total_first_touches_target": (new[d] + other) if discovery else "",
            "notes": note,
        })
    return rows, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--first-cold", default=DEFAULT_COLD.isoformat(),
                    help="Monday of the first cold email (default 2026-11-09; the late start is 2026-11-16)")
    a = ap.parse_args()
    first_cold = D.fromisoformat(a.first_cold)
    rows, problems = build(first_cold)
    # both planned starts must pass the checks, whichever one is written
    for alt in (DEFAULT_COLD, LATE_COLD):
        if alt != first_cold:
            _, p2 = build(alt)
            problems += [f"(start {alt}) {p}" for p in p2]
    out = os.path.join(ROOT, "sending", "warmup-schedule.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w_ = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w_.writeheader()
        w_.writerows(rows)
    disc = [r for r in rows if r["date"] <= GATE0.isoformat()]
    print(f"wrote {out}: {len(rows)} days, first cold email {first_cold}")
    print("discovery first touches (weeks 1-3):", sum(int(r["total_first_touches_target"] or 0) for r in disc),
          "of which cold email:", sum(r["cold_email_first_touches"] for r in disc))
    print("warm emails from [DOMAIN] before the first cold email (target):",
          sum(r["warm_email_from_domain_target"] for r in rows if r["date"] < first_cold.isoformat()))
    print("max cold email in a day:", max(r["cold_email_total_worst_case"] for r in rows))
    for wk in range(week(first_cold), 8):
        sub = [r for r in rows if r["week"] == wk]
        print(f"  week {wk}: max {max(r['cold_email_total_worst_case'] for r in sub)} (cap {max(r['cold_email_daily_cap'] for r in sub)})")
    if problems:
        print("PROBLEMS:", *problems, sep="\n  ")
        sys.exit(1)
    print(f"checks (start {DEFAULT_COLD} and late start {LATE_COLD}): no day over its cap; nothing on weekends, "
          f"holidays or no-send days; no cold email before the first cold day; no first cold day before {EARLIEST_COLD}; "
          f"no warm mail from [DOMAIN] before {DOMAIN_AUTH}")


if __name__ == "__main__":
    main()
