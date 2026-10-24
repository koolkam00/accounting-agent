#!/usr/bin/env python3
"""Freeze a campaign's survey totals before its raw answers are deleted (12 months after the campaign;
legal pack file 13, D8; SOP step answers_delete).

  python3 tools/freeze_survey.py TRACKER.xlsx CAMPAIGN_ID OUT_DIR

Writes OUT_DIR/survey-frozen-<campaign_id>.csv: one row per office on the campaign, with exactly the columns of the
tracker's survey_frozen tab (counts only: responses, tried, the three "did not try" answers, ratings, would buy,
comment count; never an answer or a comment). Import it into survey_frozen (File > Import > Upload > Append to current
sheet), check the dashboard, then delete the campaign's survey tab, its form's responses and the form, and log
answers_deleted_date. From then on every number the tracker, the report tab and the exports show for that campaign
comes from these rows (review round 1, R1-12).

Refuses (exit 2) when the campaign has no survey tab (nothing left to freeze), or when the sheet's own formulas
disagree with this arithmetic for the campaign (download the tracker again, after the sheet has recalculated).
"""
import csv
import datetime as dt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402
import tracker as TR  # noqa: E402
import trackerdef as T  # noqa: E402


def rows_for(tr, cid, today=None):
    lad = tr.ladder(cid)
    today = today or tr.today
    out = []
    for o in lad["offices"]:
        if o["approved"] != "Y":
            continue
        r = {"campaign_id": cid, "office_id": o["office_id"]}
        for k in TR.FROZEN_COLS:
            r[k] = int(o[k] or 0)
        r.update(frozen_date=today.isoformat(), note="frozen by tools/freeze_survey.py before the 12-month deletion", key="")
        out.append(r)
    return out


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 1
    tr = TR.Tracker(argv[1])
    cid, out = argv[2], argv[3]
    if cid not in tr.campaigns:
        print("REFUSED: %s is not on the campaigns tab" % cid)
        return 2
    if tr.response_rows(cid) is None:
        print("REFUSED: %s has no survey tab: there is nothing left to freeze (if it is already deleted, the numbers are lost "
              "unless survey_frozen holds them)" % cid)
        return 2
    if os.environ.get("OPS_SKIP_COMPARE") != "1":
        bad = [b for b in TR.compare(tr) if cid in b or b.startswith("no cached")]
        if bad:
            print("REFUSED: the sheet and the arithmetic disagree for %s:" % cid)
            for b in bad[:10]:
                print("  - " + b)
            return 2
    rows = rows_for(tr, cid)
    cols = [c.name for c in T.TABS["survey_frozen"].cols if c.kind != "A"]
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, "survey-frozen-%s.csv" % cid)
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("frozen %s: %d offices, %d responses -> %s" % (cid, len(rows), sum(r["survey_responses"] for r in rows), p))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
