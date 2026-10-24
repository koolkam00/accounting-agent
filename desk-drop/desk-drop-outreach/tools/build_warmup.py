#!/usr/bin/env python3
"""Build sending/warmup-schedule.csv and check it.

The schedule is a recommendation (judgment, not a published standard; see sending/sending-setup.md section 3).
Worst case assumed: nobody replies, so every first touch by email also gets touch 2 (+3 business days) and
touch 3 (+7 business days), the timing in messages/ (Part A). The script fails if any day breaks its cap,
if cold email starts before DMARC is published, or if anything is sent on a weekend or federal holiday.
"""
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
START = D(2026, 10, 26)
FIRST_COLD = D(2026, 11, 2)            # Monday of week 2, after SPF, DKIM and DMARC have passed for 48 hours
END = D(2026, 12, 11)                  # Gate 1


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


# new cold first touches by email, per business day (both sides together)
PLAN = {
    2: [3, 4, 5, 5, 5],
    3: [6, 7, None, 8, 8],             # Wed 2026-11-11 is a federal holiday: no cold email
    4: [8, 8, 9, 9, 10],
    5: [8, 8, 0, None, 0],             # Thanksgiving week
    6: [8, 10, 10, 10, 10],
    7: [10, 10, 10, 10, 10],
}
CAP = {2: 20, 3: 20, 4: 30, 5: 30, 6: 40, 7: 40}   # all cold email from [DOMAIN] in a day: new + touch 2 + touch 3


def phase(d):
    if d <= D(2026, 11, 13):
        return "discovery (weeks 1 to 3)"
    return "recruit and sell (weeks 4 to 7)"


def main():
    days = []
    d = START
    while d <= END:
        if d.weekday() < 5:
            days.append(d)
        d += dt.timedelta(days=1)
    new = {}
    for d in days:
        w = week(d)
        if d < FIRST_COLD or not bd(d) or d in LIGHT:
            new[d] = 0
            continue
        v = PLAN[w][d.weekday()]
        new[d] = 0 if v is None else v
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
    for d in days:
        w = week(d)
        total = new[d] + t2[d] + t3[d]
        cap = CAP.get(w, 0)
        note = ""
        if d in HOLIDAYS and d not in NOSEND:
            note = "Federal holiday (CONTRACTS section 3): no cold email; follow-ups move to the next business day."
        elif d in LIGHT:
            note = LIGHT[d]
        elif w == 1:
            note = {0: "Setup day: domain, Workspace, SPF; warm asks from your existing address, phone or LinkedIn.",
                    1: "Walk sessions 1 and 2 (B's walk.csv), 8 to 11 am; walk-in asks; LinkedIn invitations without a note.",
                    2: "Walk sessions 3 and 4; DKIM key generated and published (24 to 72 hours after Gmail was turned on).",
                    3: "Check SPF and DKIM pass on a test email to your own Gmail (Show original). LinkedIn messages to accepted invitations.",
                    4: "First Friday scorecard. DMARC (p=none) goes in once SPF and DKIM have passed for 48 hours: today or Monday before the first send."}[d.weekday()]
        elif d == FIRST_COLD:
            note = "First cold email from [DOMAIN]. Confirm DMARC is published and a test email shows SPF, DKIM and DMARC = PASS."
        if total > cap and w >= 2:
            problems.append(f"{d} total {total} > cap {cap}")
        if (new[d] or t2[d] or t3[d]) and not bd(d):
            problems.append(f"{d} sends on a non-business day")
        if new[d] and d < FIRST_COLD:
            problems.append(f"{d} cold email before {FIRST_COLD}")
        discovery = d <= D(2026, 11, 13)
        other = (0 if (d in HOLIDAYS and not discovery) else (10 - new[d])) if discovery else ""
        if d == START:
            other = 5
        rows.append({
            "date": d.isoformat(), "weekday": d.strftime("%a"), "week": w, "phase": phase(d),
            "cold_email_first_touches": new[d], "email_touch_2_due": t2[d], "email_touch_3_due": t3[d],
            "cold_email_total_worst_case": total, "cold_email_daily_cap": cap if w >= 2 else 0,
            "other_channel_first_touches_target": other,
            "total_first_touches_target": (new[d] + other) if discovery else "",
            "notes": note,
        })
    out = os.path.join(ROOT, "sending", "warmup-schedule.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w_ = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w_.writeheader()
        w_.writerows(rows)
    disc = [r for r in rows if r["date"] <= "2026-11-13"]
    print(f"wrote {out}: {len(rows)} days")
    print("discovery first touches (weeks 1-3):", sum(int(r["total_first_touches_target"] or 0) for r in disc),
          "of which cold email:", sum(r["cold_email_first_touches"] for r in disc))
    print("max cold email in a day:", max(r["cold_email_total_worst_case"] for r in rows))
    for wk in range(2, 8):
        print(f"  week {wk}: max {max(r['cold_email_total_worst_case'] for r in rows if r['week'] == wk)} (cap {CAP[wk]})")
    if problems:
        print("PROBLEMS:", *problems, sep="\n  ")
        sys.exit(1)
    print("checks: no day over its cap; nothing on weekends or holidays; no cold email before", FIRST_COLD)


if __name__ == "__main__":
    main()
