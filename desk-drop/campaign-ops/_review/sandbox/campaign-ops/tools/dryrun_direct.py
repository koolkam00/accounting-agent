#!/usr/bin/env python3
"""The third delivery model: the standard SAMPLE run re-planned as direct-ship (brands ship to each office).

  python3 tools/dryrun_direct.py

Builds the standard scenario with DRP-002 set to direct-ship (kits mailed at T-3, one tracking number
per office, office counts), as of T-1, and makes that model's documents: the tracking sheet (route),
the ship-date emails with per-office addresses, the T-3 messages, the kit and the dated SOP.
Outputs: dry-run/standard/direct-ship-variant/.
"""
import datetime as dt
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dryrun as DR  # noqa: E402
import opscal  # noqa: E402
import scenarios as S  # noqa: E402


def main():
    scn = S.standard()
    T = scn["T"]
    for r in scn["rows"]["drops"]:
        if r["drop_id"] == scn["drop_id"]:
            r["delivery_model"] = "direct-ship"
            r["receiving_location"] = "SAMPLE direct to each office; reserve to the receiving address"
            r["courier_or_van"] = ""
    k3 = opscal.add_bd(T, -3)
    for i, r in enumerate(x for x in scn["rows"]["stops"] if x["drop_id"] == scn["drop_id"]):
        r["kit_mailed_date"] = k3
        r["carrier_tracking"] = "; ".join("SAMPLE %s SAMPLE-1Z%d%05d" % (b, k + 1, 100 + i) for k, b in enumerate(("Tallgrass", "Orchard Row", "Kettle Ridge")))
        r.setdefault("_fields_on", {})["carrier_tracking"] = opscal.add_bd(T, -2)
    scn["delivery_model"] = "direct-ship"
    out = os.path.join(DR.ROOT, "dry-run", "standard", "direct-ship-variant")
    os.makedirs(out, exist_ok=True)
    work = os.path.join(DR.ROOT, "_work", "dryrun-direct")
    os.makedirs(work, exist_ok=True)
    day = opscal.add_bd(T, -1)
    p = DR.build_snapshot(scn, day, os.path.join(work, "in.xlsx"))
    snap = os.path.join(out, "SAMPLE-tracker-direct-ship-%s.xlsx" % day.isoformat())
    tr, errs, n = DR.recalc_and_read(p, snap)
    log = ["# Direct-ship variant (SAMPLE)", "", "The standard run's drop %s re-planned as direct-ship, as of %s (T-1). Formula errors: %d." % (scn["drop_id"], day, n), ""]
    for args in (["tools/make_route.py", snap, scn["drop_id"], os.path.join(out, "route")],
                 ["tools/make_messages.py", snap, scn["drop_id"], "ship_release", os.path.join(out, "messages")],
                 ["tools/make_messages.py", snap, scn["drop_id"], "t3", os.path.join(out, "messages")],
                 ["tools/make_messages.py", snap, scn["drop_id"], "t1", os.path.join(out, "messages")],
                 ["tools/make_kit.py", snap, scn["drop_id"], os.path.join(out, "kit")],
                 ["tools/make_calendar.py", snap, scn["drop_id"], os.path.join(out, "sop")]):
        DR.run_tool(args, log)
    open(os.path.join(out, "VARIANT-LOG.md"), "w", encoding="utf-8").write("\n".join(log) + "\n")
    print("\n".join(log))


if __name__ == "__main__":
    main()
