#!/usr/bin/env python3
"""Dry runs: replay a SAMPLE scenario day by day through the tracker and every generator.

  python3 tools/dryrun.py zero        # campaign zero: 2 brands x 5 offices, founder model
  python3 tools/dryrun.py standard    # first standard run: 3 brands x 10 offices, courier model
  python3 tools/dryrun.py exception   # second standard run: a short shipment and an office that declines at the door
  python3 tools/dryrun.py zero --final-only

For each day on the scenario's calendar, the tracker is built with only the rows the founder would
have logged by that day (today_override = that day), recalculated with LibreOffice, read back, and
compared with tools/tracker.py's independent arithmetic. The day's documents are generated from it.
Problems counted: formula errors, disagreements, every tool that exits non-zero (a refusal), and any check
left on the dashboard at the final state (review round 1: a refused report must never pass as "0 problems").
Outputs: dry-run/<scenario>/ (SAMPLE only).
"""
import copy
import datetime as dt
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_tracker as B  # noqa: E402
import common  # noqa: E402
import opscal  # noqa: E402
import recalc as RC  # noqa: E402
import scenarios as S  # noqa: E402
import tracker as TR  # noqa: E402

ROOT = common.ROOT
# The dry runs use reserved example domains so QR codes can be drawn and decoded; real use keeps [DOMAIN].
SAMPLE_CONFIG = {"short_link_domain": "go.example.com", "survey_privacy_url": "https://example.com/survey-privacy"}


def snapshot(scn, day):
    rows = {}
    for tab, lst in scn["rows"].items():
        keep = []
        for r in lst:
            if r.get("_on") and r["_on"] > day:
                continue
            x = {k: v for k, v in r.items() if not k.startswith("_")}
            for f, on in (r.get("_fields_on") or {}).items():
                if on and on > day:
                    x.pop(f, None)
            # A field whose value changes over time (for example a revised ship-date email): the latest value by that day.
            for f, hist in (r.get("_fields_history") or {}).items():
                vals = [v for (on, v) in sorted(hist, key=lambda h: h[0]) if on <= day]
                if vals:
                    x[f] = vals[-1]
                else:
                    x.pop(f, None)
            keep.append(x)
        rows[tab] = keep
    # A campaign's response tab exists from the day its survey form is made (its drop's T-4).
    drop_t = {r["drop_id"]: r["drop_date"] for r in scn["rows"]["drops"]}
    camp_t = {r["campaign_id"]: drop_t.get(r["drop_id"]) for r in scn["rows"]["campaigns"]}
    resp = {}
    for cid, (brand, rr) in scn["responses"].items():
        if day < opscal.add_bd(camp_t.get(cid) or scn["T"], -4):
            continue
        resp[cid] = (brand, [r[:7] for r in rr if r[7] <= day and r[0].date() <= day])
    return rows, resp


def build_snapshot(scn, day, path):
    rows, resp = snapshot(scn, day)
    free = {k: v for k, v in rows.items() if k in ("office_form", "brand_form")}
    tabs = {k: v for k, v in rows.items() if k not in free}
    B.build(path, sample=tabs, response_tabs=resp, today=day, config=SAMPLE_CONFIG)
    if free:
        import openpyxl
        wb = openpyxl.load_workbook(path)
        for tab, lst in free.items():
            ws = wb[tab]
            hdr = [c.value for c in ws[1]]
            for r, row in enumerate(lst, start=2):
                for k, v in row.items():
                    c = ws.cell(row=r, column=hdr.index(k) + 1, value=v)
                    if k == "Timestamp":
                        c.number_format = "yyyy-mm-dd hh:mm:ss"
        wb.save(path)
    return path


def make_photos(scn, out):
    """Stand-in SAMPLE photos: the identity workstream's simulated pantry photos, copied under each file name."""
    src = os.path.join(common.IDENTITY, "templates", "report", "samples", "photos")
    wide = sorted(x for x in os.listdir(src) if "wide" in x)
    close = sorted(x for x in os.listdir(src) if "close" in x)
    n = 0
    for r in scn["rows"].get("photos", []):
        d = os.path.join(out, "photos", r["campaign_id"])
        os.makedirs(d, exist_ok=True)
        pick = (wide if r["photo_type"] == "placement" else close)[n % 2]
        shutil.copy(os.path.join(src, pick), os.path.join(d, r["file_name"]))
        n += 1
    return os.path.join(out, "photos")


def last_day(scn):
    ds = []
    for lst in scn["rows"].values():
        for r in lst:
            if r.get("_on"):
                ds.append(r["_on"])
            ds += [v for v in (r.get("_fields_on") or {}).values() if v]
            ds += [on for hist in (r.get("_fields_history") or {}).values() for on, _ in hist]
    return max(ds)


def recalc_and_read(path, out):
    r = RC.recalc(path, out)
    errs, n = RC.errors(r)
    tr = TR.Tracker(r)
    return tr, errs, n


KEEP_SNAPSHOTS = ("confirm", "placement_confirm", "report")


TOOL_FAILURES = []


def run_tool(args, log):
    r = subprocess.run([sys.executable] + args, capture_output=True, text=True, cwd=ROOT, timeout=900)
    if r.returncode != 0:
        TOOL_FAILURES.append(" ".join(os.path.basename(a) if os.path.isabs(a) else a for a in args) + " -> exit %d" % r.returncode)
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    log.append("    $ python3 %s  ->  %s%s" % (" ".join(os.path.relpath(a, ROOT) if os.path.isabs(a) else a for a in args), tail,
                                              "" if r.returncode == 0 else "  [exit %d]" % r.returncode))
    if r.returncode not in (0,):
        log.append("      " + r.stdout.strip().replace("\n", "\n      ")[-1500:])
    return r.returncode


def dashboard_checks(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["dashboard"]
    out = {}
    r = 7
    while ws.cell(row=r, column=1).value:   # the check lines, down to the first empty row
        k, v = ws.cell(row=r, column=1).value, ws.cell(row=r, column=2).value
        if k and isinstance(v, (int, float)) and v:
            out[k] = v
        r += 1
    msgs = []
    import trackerdef as TD
    for tab in ("campaigns", "approvals", "stops", "inventory", "counts", "photos", "scans", "issues", "hours", "costs", "invoices", "links", "brands"):
        t = TD.TABS[tab]
        w = wb[tab]
        ci = t.index["checks" if "checks" in t.index else "e_payment_check"] + 1
        key = t.cols[0].name
        for row in range(t.first(), t.last() + 1):
            v = w.cell(row=row, column=ci).value
            if v and not str(v).startswith("info:"):
                msgs.append("%s row %d (%s %s): %s" % (tab, row, w.cell(row=row, column=1).value, w.cell(row=row, column=2).value or "", str(v).strip()))
    rel = {}
    t = TD.TABS["campaigns"]
    w = wb["campaigns"]
    for row in range(2, 2 + len([1 for x in w.iter_rows(min_row=2, max_col=1, values_only=True) if x[0]])):
        rel[w.cell(row=row, column=1).value] = w.cell(row=row, column=t.index["ship_release"] + 1).value
    return out, msgs, rel


def day_plan(scn):
    """Every SOP day for the scenario's drop, plus every day the scenario logs something."""
    import sop_steps as SS
    T = scn["T"]
    ds = SS.dates(T, scn["delivery_model"])
    days = {}
    for sid, d in ds.items():
        days.setdefault(d, []).append(sid)
    for lst in scn["rows"].values():
        for r in lst:
            for d in [r.get("_on")] + list((r.get("_fields_on") or {}).values()) + [on for h in (r.get("_fields_history") or {}).values() for on, _ in h]:
                if d and d >= T - dt.timedelta(days=60):
                    days.setdefault(d, [])
    return dict(sorted(days.items()))


def main(argv):
    name = argv[1] if len(argv) > 1 else "zero"
    scn = getattr(S, name)()
    out = os.path.join(ROOT, "dry-run", name)
    os.makedirs(out, exist_ok=True)
    work = os.path.join(ROOT, "_work", "dryrun-" + name)
    os.makedirs(work, exist_ok=True)
    photos = make_photos(scn, out)
    T, did = scn["T"], scn["drop_id"]
    log = ["# Dry run: %s" % name, "", "SAMPLE data only. Drop %s on %s, %s model, campaigns %s." % (did, T, scn["delivery_model"], ", ".join(scn["campaigns"])),
           "Each day: the tracker is rebuilt with only the rows logged by that day, recalculated (LibreOffice), and read back; "
           "the sheet's formulas are compared with tools/tracker.py; then that day's tools run.", ""]
    total_bad = 0
    released = set()
    days = day_plan(scn)
    if "--final-only" in argv:
        days = {}
    for day, steps in days.items():
        p = build_snapshot(scn, day, os.path.join(work, "in.xlsx"))
        snap = os.path.join(work, "day.xlsx")
        tr, errs, n = recalc_and_read(p, snap)
        bad = TR.compare(tr)
        bad = [b for b in bad if not b.startswith("no cached")]
        total_bad += len(bad) + n
        checks, msgs, rel = dashboard_checks(snap)
        rows, _ = snapshot(scn, day)
        prev, _ = snapshot(scn, day - dt.timedelta(days=1))
        new = {k: len(v) - len(prev.get(k, [])) for k, v in rows.items() if len(v) != len(prev.get(k, []))}
        log.append("## %s %s" % (day.strftime("%a %Y-%m-%d"), ("T" if day == T else "") + (" · " + ", ".join(steps) if steps else "")))
        log.append("- Logged today: %s" % (", ".join("%s +%d" % kv for kv in new.items()) or "nothing new"))
        log.append("- Sheet: %d formula errors; %d disagreements with the independent arithmetic." % (n, len(bad)))
        for b in bad[:10]:
            log.append("    - " + b)
        if checks:
            log.append("- Dashboard checks to fix: " + "; ".join("%s %s" % (k, v) for k, v in checks.items()))
        for m in msgs[:12]:
            log.append("    - " + m)
        for cid, v in rel.items():
            if v and str(v).startswith("RELEASED") and cid not in released:
                released.add(cid)
                log.append("- %s ship release: %s" % (cid, v))
                run_tool(["tools/make_messages.py", snap, did, "ship_release", os.path.join(out, "messages")], log)
        if any("units changed since the ship-date email" in m for m in msgs):
            log.append("- The route changed after a ship-date email: revised email drafted")
            run_tool(["tools/make_messages.py", snap, did, "ship_release", os.path.join(out, "messages")], log)
        dd = os.path.join(out, "days", day.isoformat())
        for inv in rows.get("invoices", []):
            if inv.get("issued_date") == day:
                run_tool(["tools/make_invoice.py", snap, inv["invoice_id"], os.path.join(out, "invoices")], log)
        for a in rows.get("approvals", []):
            if a.get("asked_date") == day and a is rows["approvals"][0]:
                run_tool(["tools/make_messages.py", snap, did, "approvals", os.path.join(out, "messages")], log)
        if "forms" in steps:
            run_tool(["tools/make_links.py", snap, did, os.path.join(out, "links")], log)
        if "kit_print" in steps:
            run_tool(["tools/make_kit.py", snap, did, os.path.join(out, "kit")], log)
            run_tool(["tools/make_messages.py", snap, did, "t3", os.path.join(out, "messages")], log)
        if "confirm" in steps:
            run_tool(["tools/make_route.py", snap, did, os.path.join(out, "route")], log)
            run_tool(["tools/make_messages.py", snap, did, "t1", os.path.join(out, "messages")], log)
        for st, msg in (("drop", "on_my_way"), ("placement_confirm", "placement_confirmation"), ("day3", "day3"), ("close", "day5"),
                        ("pass_on", "newsletter"), ("redemption", "redemption")):
            if st in steps:
                run_tool(["tools/make_messages.py", snap, did, msg, os.path.join(out, "messages")], log)
        if "report" in steps:
            for cid in scn["campaigns"]:
                run_tool(["tools/make_report.py", snap, cid, os.path.join(out, "reports"), "--photos", photos], log)
            run_tool(["tools/make_messages.py", snap, did, "report", os.path.join(out, "messages"), "--reports", os.path.join(out, "reports")], log)
        if "office_debrief" in steps or "debrief" in steps:
            run_tool(["tools/make_debrief.py", snap, did, os.path.join(out, "debriefs")], log)
        if "debrief" in steps or "redemption" in steps:
            run_tool(["tools/export_actuals.py", snap, os.path.join(out, "exports", "at-" + day.isoformat())], log)
        if set(steps) & set(KEEP_SNAPSHOTS):
            shutil.copy(snap, os.path.join(out, "SAMPLE-tracker-%s-%s.xlsx" % (name, day.isoformat())))
        log.append("")
    final = last_day(scn) + dt.timedelta(days=1)
    p = build_snapshot(scn, final, os.path.join(work, "final-in.xlsx"))
    fin = os.path.join(out, "SAMPLE-tracker-%s-final.xlsx" % name)
    tr, errs, n = recalc_and_read(p, fin)
    bad = [b for b in TR.compare(tr) if not b.startswith("no cached")]
    total_bad += len(bad) + n
    log.append("## Final state %s" % final)
    log.append("- Sheet: %d formula errors; %d disagreements." % (n, len(bad)))
    for b in bad[:10]:
        log.append("    - " + b)
    checks, msgs, rel = dashboard_checks(fin)
    log.append("- Dashboard checks to fix at the final state: %s" % ("; ".join("%s %s" % kv for kv in checks.items()) or "none"))
    for m in msgs[:20]:
        log.append("    - " + m)
    total_bad += sum(int(v) for v in checks.values())
    run_tool(["tools/export_actuals.py", fin, os.path.join(out, "exports")], log)
    run_tool(["tools/export_actuals.py", fin, os.path.join(ROOT, "exports", "SAMPLE-" + name)], log)
    run_tool(["tools/dump_forms.py", fin, name, os.path.join(out, "forms")], log)
    run_tool(["tools/make_calendar.py", fin, did, os.path.join(out, "sop")], log)
    shutil.copy(p, os.path.join(out, "SAMPLE-tracker-%s-final-for-import.xlsx" % name))
    total_bad += len(TOOL_FAILURES)
    log.append("- Tools that refused or failed during the replay: %s" % ("; ".join(TOOL_FAILURES) or "none"))
    log.append("- Problems in total (formula errors + disagreements + tool refusals + final dashboard checks): %d" % total_bad)
    common.write(os.path.join(out, "DRY-RUN-LOG.md"), "\n".join(log) + "\n")
    print("dry run %s: %d days, %d problems in total (formula errors + disagreements + tool refusals + final checks). Log: %s" % (
        name, len(days), total_bad, os.path.join(out, "DRY-RUN-LOG.md")))
    return 0 if total_bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
