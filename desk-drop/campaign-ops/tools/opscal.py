#!/usr/bin/env python3
"""Campaign calendar and drop-date validator (CONTRACTS section 3).

Every other tool in this folder takes its dates from here, so none of them can
produce a Monday, Friday, holiday or blackout drop.

Rules (CONTRACTS section 3, "derived, founder to confirm"):
  * A drop day T is a Tuesday or Wednesday that is a business day.
  * Business days: Monday to Friday, not a US federal holiday (observed dates).
  * T-n and T+n count business days. T is day 1 of the window, T+4 is day 5 and closes it.
  * Report due T+7, debrief T+10, redemption check T+30 *calendar* days.
  * Blackouts: no drop day in one, and no day of the five-business-day window in one:
      - 18 to 31 December inclusive;
      - the Monday-to-Friday week that contains 4 July or its observed holiday;
      - 18 to 31 August inclusive.

Command line (run from desk-drop/campaign-ops/):
  python3 tools/opscal.py check 2027-01-12        # OK, or the reasons it is refused (exit 2)
  python3 tools/opscal.py dates 2027-01-12        # every SOP date for that drop
  python3 tools/opscal.py next 2027-01-12 [n]     # the next n valid drop days on or after a date
  python3 tools/opscal.py slip 2027-01-12         # the slip rule: one week later, or the first clear Tue/Wed
  python3 tools/opscal.py holidays 2027
"""
import datetime as dt
import sys

D = dt.date
ONE = dt.timedelta(days=1)

# CONTRACTS section 3 lists these for 2026-27. holidays() computes the same rule for any
# year; tests/test_opscal.py checks that the computed list contains every listed date.
CONTRACTS_HOLIDAYS = [
    "2026-11-11", "2026-11-26", "2026-12-25", "2027-01-01", "2027-01-18", "2027-02-15",
    "2027-05-31", "2027-06-18", "2027-07-05", "2027-09-06",
]


def parse(s):
    if isinstance(s, dt.datetime):
        return s.date()
    if isinstance(s, D):
        return s
    return D.fromisoformat(str(s).strip()[:10])


def _nth_weekday(year, month, weekday, n):
    """n-th weekday (Mon=0) of a month; n=-1 is the last one."""
    if n > 0:
        d = D(year, month, 1)
        while d.weekday() != weekday:
            d += ONE
        return d + dt.timedelta(weeks=n - 1)
    d = D(year, month + 1, 1) - ONE if month < 12 else D(year, 12, 31)
    while d.weekday() != weekday:
        d -= ONE
    return d


def _observed(d):
    if d.weekday() == 5:   # Saturday -> Friday
        return d - ONE
    if d.weekday() == 6:   # Sunday -> Monday
        return d + ONE
    return d


def holidays(year):
    """US federal holidays (observed) that fall in `year`, as {date: name}."""
    out = {}

    def add(d, name):
        if d.year == year:
            out[d] = name

    for y in (year, year + 1):   # New Year's Day on a Saturday is observed on 31 December
        add(_observed(D(y, 1, 1)), "New Year's Day (observed)" if _observed(D(y, 1, 1)) != D(y, 1, 1) else "New Year's Day")
    add(_nth_weekday(year, 1, 0, 3), "Martin Luther King Jr. Day")
    add(_nth_weekday(year, 2, 0, 3), "Washington's Birthday")
    add(_nth_weekday(year, 5, 0, -1), "Memorial Day")
    j = D(year, 6, 19)
    add(_observed(j), "Juneteenth" + (" (observed)" if _observed(j) != j else ""))
    i = D(year, 7, 4)
    add(_observed(i), "Independence Day" + (" (observed)" if _observed(i) != i else ""))
    add(_nth_weekday(year, 9, 0, 1), "Labor Day")
    add(_nth_weekday(year, 10, 0, 2), "Columbus Day")
    v = D(year, 11, 11)
    add(_observed(v), "Veterans Day" + (" (observed)" if _observed(v) != v else ""))
    add(_nth_weekday(year, 11, 3, 4), "Thanksgiving Day")
    c = D(year, 12, 25)
    add(_observed(c), "Christmas Day" + (" (observed)" if _observed(c) != c else ""))
    return out


_HOL_CACHE = {}


def is_holiday(d):
    if d.year not in _HOL_CACHE:
        _HOL_CACHE[d.year] = holidays(d.year)
    return d in _HOL_CACHE[d.year]


def is_business_day(d):
    return d.weekday() < 5 and not is_holiday(d)


def add_bd(d, n):
    """Move n business days (n may be negative). add_bd(T, 0) is T itself."""
    d = parse(d)
    step = ONE if n >= 0 else -ONE
    left = abs(n)
    while left:
        d += step
        if is_business_day(d):
            left -= 1
    return d


def july4_week(year):
    obs = _observed(D(year, 7, 4))
    monday = obs - dt.timedelta(days=obs.weekday())
    return monday, monday + dt.timedelta(days=4)


def blackouts(year):
    """List of (start, end, reason) blackout ranges for a year, inclusive."""
    m, f = july4_week(year)
    return [
        (m, f, "week of 4 July (observed %s)" % _observed(D(year, 7, 4)).isoformat()),
        (D(year, 8, 18), D(year, 8, 31), "last two weeks of August"),
        (D(year, 12, 18), D(year, 12, 31), "last two weeks of December"),
    ]


def blackout_hits(start, end):
    """Blackout ranges that overlap [start, end]."""
    hits = []
    for y in range(start.year, end.year + 1):
        for b0, b1, why in blackouts(y):
            if b0 <= end and b1 >= start:
                hits.append((b0, b1, why))
    return hits


def window(T):
    T = parse(T)
    return [add_bd(T, i) for i in range(5)]


def problems(T):
    """Reasons a drop day is refused. Empty list = valid."""
    T = parse(T)
    out = []
    if T.weekday() not in (1, 2):
        out.append("%s is a %s. Drop days are Tuesday or Wednesday only." % (T.isoformat(), T.strftime("%A")))
    if is_holiday(T):
        out.append("%s is a federal holiday (%s)." % (T.isoformat(), _HOL_CACHE[T.year][T]))
    w = window(T)
    for b0, b1, why in blackout_hits(T, w[-1]):
        out.append("The window %s to %s overlaps a blackout: %s, %s to %s." % (
            w[0].isoformat(), w[-1].isoformat(), why, b0.isoformat(), b1.isoformat()))
    return out


def is_valid(T):
    return not problems(T)


def next_valid(after, n=1, include=True):
    """The next n valid drop days on or after `after`."""
    d = parse(after)
    if not include:
        d += ONE
    out = []
    while len(out) < n:
        if is_valid(d):
            out.append(d)
        d += ONE
    return out


def slip(T):
    """Slip rule (brand agreement section 8): one week later; if that window overlaps a blackout
    (or is otherwise invalid), the first Tuesday or Wednesday after it whose window is clear."""
    T = parse(T)
    cand = T + dt.timedelta(days=7)
    if is_valid(cand):
        return cand
    return next_valid(cand, 1)[0]


# The SOP offsets. Business days unless 'cal' says calendar days. Each row is
# (key, offset, kind, label). kind: 'bd' business days from T, 'cal' calendar days from T,
# 'cal_after' calendar days after another key.
SOP_DATES = [
    ("approvals_due", -10, "bd", "Office approvals in (explicit yes for an office's first three drops)"),
    ("ship_by", -10, "bd", "Brand ships units plus 10% reserve (hard T-10; also the cancel-by date)"),
    ("receive", -5, "bd", "Receive and count; best-by, lots, damage; allergen line checked against the package"),
    ("kit_print", -3, "bd", "Not arrived = slip one week. Print cards and labels; send offices window and Slack post"),
    ("confirm", -1, "bd", "Text each pantry owner; pack one labeled case per office per brand; baseline link counts"),
    ("drop", 0, "bd", "Drop day: route 8 to 11 am, place, photograph, count, log"),
    ("placement_confirm", 1, "bd", "Placement confirmation email to each brand (standard: balance invoice)"),
    ("check_day3", 2, "bd", "Day 3: photo and count from each office; top up from reserve; nudge offices under 5 responses"),
    ("close", 4, "bd", "Day 5: survey closes; leftovers collected or released; final photo, count and link reading"),
    ("pass_on", 5, "bd", "Newsletter list passed to the brand once; unticked emails deleted; reserve reconciled"),
    ("report_due", 7, "bd", "Report PDF to the brand; office summaries to each office"),
    ("debrief", 10, "bd", "Brand debrief (20 min) and renewal proposal; actuals exported for the financial model"),
    ("return_label_deadline", 14, "bd", "No prepaid return label by now (10 business days after T+4): reserve to roster offices"),
    ("redemption_check", 30, "cal", "Day-30 code redemption check with the brand (calendar days)"),
]


def sop_dates(T):
    T = parse(T)
    out = {}
    for key, off, kind, label in SOP_DATES:
        if kind == "bd":
            out[key] = add_bd(T, off)
        else:
            out[key] = T + dt.timedelta(days=off)
    out["window_start"] = T
    out["window_end"] = add_bd(T, 4)
    out["newsletter_delete"] = out["pass_on"] + dt.timedelta(days=30)
    out["answers_delete"] = _add_months(out["window_end"], 12)
    out["coi_cover_until"] = _add_months(out["window_end"], 12)
    # Holiday freight: CONTRACTS section 3 asks brands to ship early when T-10..T-5 crosses the
    # December blackout (campaign zero: ship by Tue 2026-12-22, hard T-10 Mon 2026-12-28).
    ship = out["ship_by"]
    hits = blackout_hits(ship, out["receive"])
    out["ship_by_requested"] = ship
    if hits:
        b0 = min(h[0] for h in hits)
        req = b0 + dt.timedelta(days=4)            # 18 Dec + 4 = 22 Dec, the campaign-zero date
        while not is_business_day(req) or req > ship:
            req -= ONE
        out["ship_by_requested"] = req
    return out


def _add_months(d, m):
    y, mo = d.year + (d.month - 1 + m) // 12, (d.month - 1 + m) % 12 + 1
    day = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mo - 1])
    return D(y, mo, day)


def window_day(T, d):
    """Day number of date d in the window of T: 1..5 inside, 0 before T, 6+ after (business days)."""
    T, d = parse(T), parse(d)
    if d < T:
        return 0
    n, x = 1, T
    while x < d:
        x += ONE
        if is_business_day(x):
            n += 1
    return n


def require_valid(T):
    p = problems(T)
    if p:
        raise ValueError("Drop date refused: " + " ".join(p))
    return parse(T)


def _fmt(d):
    return d.strftime("%a %Y-%m-%d")


def main(argv):
    if len(argv) < 3 and not (len(argv) == 2 and argv[1] in ("-h", "--help")):
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd in ("-h", "--help"):
        print(__doc__)
        return 0
    arg = argv[2]
    if cmd == "check":
        p = problems(arg)
        if p:
            print("REFUSED " + arg)
            for x in p:
                print("  - " + x)
            print("  Next valid drop days: " + ", ".join(_fmt(d) for d in next_valid(arg, 3)))
            return 2
        print("OK %s: window %s to %s" % (_fmt(parse(arg)), _fmt(window(arg)[0]), _fmt(window(arg)[-1])))
        return 0
    if cmd == "dates":
        p = problems(arg)
        if p:
            print("REFUSED " + arg + ": " + " ".join(p))
            return 2
        s = sop_dates(arg)
        for key, off, kind, label in SOP_DATES:
            tag = ("T%+d" % off if off else "T") + (" cal" if kind == "cal" else "")
            print("%-24s %-9s %s  %s" % (key, tag, _fmt(s[key]), label))
        for k in ("ship_by_requested", "window_end", "newsletter_delete", "answers_delete", "coi_cover_until"):
            print("%-24s %-9s %s" % (k, "", _fmt(s[k])))
        return 0
    if cmd == "next":
        n = int(argv[3]) if len(argv) > 3 else 5
        for d in next_valid(arg, n):
            print(_fmt(d))
        return 0
    if cmd == "slip":
        print(_fmt(slip(arg)))
        return 0
    if cmd == "holidays":
        for d, name in sorted(holidays(int(arg)).items()):
            print(_fmt(d), name)
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
