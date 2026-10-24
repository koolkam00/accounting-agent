#!/usr/bin/env python3
"""The SOP for one drop, dated: a checklist and a calendar file (.ics) to import into your calendar.

  python3 tools/make_calendar.py DROP_DATE MODEL OUT_DIR [--drop-id DRP-001]
  python3 tools/make_calendar.py TRACKER.xlsx DROP_ID OUT_DIR

MODEL is founder, courier or direct-ship. The drop date is checked first: a Monday, Friday,
federal holiday or a window touching a blackout is refused (exit 2) with the next valid dates.
Writes OUT_DIR/sop-<drop>.html, .pdf and .ics. Importing the .ics needs your calendar login.
"""
import datetime as dt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402
import opscal  # noqa: E402
import sop_steps as SS  # noqa: E402

E = common.E


def esc(x):
    return x.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def short(what):
    head = what.split(":")[0] if ":" in what[:70] else what[:60]
    return head.strip()


def ics(drop_id, model, T, ds, company):
    now = dt.datetime(2026, 10, 24, 12, 0).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//campaign-ops//sop//EN", "CALSCALE:GREGORIAN"]
    for st in SS.STEPS:
        if st[0] not in ds:
            continue
        d = ds[st[0]]
        lines += ["BEGIN:VEVENT", "UID:%s-%s@campaign-ops" % (drop_id, st[0]), "DTSTAMP:" + now,
                  "DTSTART;VALUE=DATE:" + d.strftime("%Y%m%d"), "DTEND;VALUE=DATE:" + (d + dt.timedelta(days=1)).strftime("%Y%m%d"),
                  fold("SUMMARY:" + esc("%s: %s (%s)" % (drop_id, short(st[6]), st[5]))),
                  fold("DESCRIPTION:" + esc(st[6] + "\nLog it in: " + st[7])),
                  "TRANSP:TRANSPARENT", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def fold(line):
    out, b = [], line.encode("utf-8")
    while len(b) > 74:
        cut = 74
        while (b[cut] & 0xC0) == 0x80:
            cut -= 1
        out.append(b[:cut].decode("utf-8"))
        b = b[cut:]
    out.append(b.decode("utf-8"))
    return "\r\n ".join(out)


def build(T, model, drop_id, out, company=""):
    p = opscal.problems(T)
    if p:
        print("REFUSED drop date %s:" % T)
        for x in p:
            print("  - " + x)
        print("  Next valid: " + ", ".join(d.strftime("%a %Y-%m-%d") for d in opscal.next_valid(T, 4)))
        return 2
    T = opscal.parse(T)
    ds = SS.dates(T, model)
    rows = []
    for st in sorted([s for s in SS.STEPS if s[0] in ds], key=lambda s: (ds[s[0]], SS.STEPS.index(s))):
        d = ds[st[0]]
        rel = "T" if d == T else ("T%+d" % (opscal.window_day(T, d) - 1) if d > T else "T-%d" % sum(1 for i in range((T - d).days) if opscal.is_business_day(d + dt.timedelta(days=i))))
        if st[3] == "cal":
            rel = "+%d cal" % (d - (T if st[1] == "T" else ds[st[1]])).days
        if st[1] == "ship_req":
            rel = "ship-by" + ("" if st[2] == 0 else " %+d" % st[2])
        rows.append("<tr><td class='small' style='white-space:nowrap'>%s<br><b>%s</b></td><td class='small'>%s%s</td><td class='small'>%s</td><td class='small'>%s</td><td><span class='chk'></span></td></tr>" % (
            E(d.strftime("%a %Y-%m-%d")), E(rel), "<b>By</b> " if st[3] == "by" else "", E(st[6]), E(st[5]), E(st[7] + ((" · " + st[8]) if st[8] else ""))))
    w = opscal.window(T)
    body = ("<h1>SOP · %s · %s</h1><p>Delivery model <b>%s</b>. Window %s to %s (day 1 to day 5). Report due %s, debrief %s, redemption check %s. "
            "Business days skip weekends and US federal holidays; this date passed the drop-day check.</p>"
            "<table><tr><th>Date</th><th>What</th><th>Who</th><th>Log it in / tool</th><th>Done</th></tr>%s</table>") % (
        E(drop_id), E(T.strftime("%a %Y-%m-%d")), E(model), E(w[0].strftime("%a %Y-%m-%d")), E(w[-1].strftime("%a %Y-%m-%d")),
        E(opscal.add_bd(T, 7).strftime("%a %Y-%m-%d")), E(opscal.add_bd(T, 10).strftime("%a %Y-%m-%d")),
        E((T + dt.timedelta(days=30)).strftime("%a %Y-%m-%d")), "".join(rows))
    os.makedirs(out, exist_ok=True)
    hp = common.write(os.path.join(out, "sop-%s.html" % drop_id), common.page("SOP " + drop_id, body, out, sample=common.is_sample(drop_id)))
    common.render(hp, hp[:-5] + ".pdf")
    with open(os.path.join(out, "sop-%s.ics" % drop_id), "w", newline="", encoding="utf-8") as f:
        f.write(ics(drop_id, model, T, ds, company))
    print("sop %s %s %s: %d steps -> %s" % (drop_id, T, model, len(rows), hp))
    return 0


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 1
    if argv[1].endswith(".xlsx"):
        import tracker as TR
        tr = TR.Tracker(argv[1])
        did = argv[2]
        r = tr.drops[did]
        return build(TR._d(r["drop_date"]), TR._s(r["delivery_model"]), did, argv[3], tr.company_name)
    did = argv[argv.index("--drop-id") + 1] if "--drop-id" in argv else "DRP"
    return build(argv[1], argv[2], did, argv[3])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
