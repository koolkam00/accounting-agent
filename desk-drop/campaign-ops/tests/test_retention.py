#!/usr/bin/env python3
"""The 12-month deletion of a campaign's raw survey answers keeps the campaign's record (review round 1, R1-12).

  python3 tests/test_retention.py

From campaign zero's final state (tools/scenarios.py zero(), built and recalculated here):
 1. tools/freeze_survey.py writes SAMPLE-CMP-001's per-office totals;
 2. they are appended to the survey_frozen tab, the campaign's survey tab is deleted, answers_deleted_date is set and
    today moves to 2028-01-25; after recalculation every survey number on campaigns and approvals is unchanged,
    the sheet and tools/tracker.py agree, the export's survey columns are unchanged, and no check is left;
 3. negative control: deleting the tab without the freeze turns the responses to 0 and the campaign's checks say
    "answers deleted but no frozen totals".
Writes only to a temporary folder.
"""
import csv
import datetime as dt
import os
import shutil
import subprocess
import sys
import tempfile

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import dryrun as DR  # noqa: E402
import recalc as RC  # noqa: E402
import scenarios as S  # noqa: E402
import tracker as TR  # noqa: E402
import trackerdef as T  # noqa: E402

CID = "SAMPLE-CMP-001"
NUMS = ["survey_responses", "survey_responses_min_office", "survey_tried_yes", "survey_rating_n", "survey_rating_avg",
        "survey_buy_yes", "survey_buy_maybe", "survey_buy_no", "comments_total", "offices_under_5", "gate2_responses"]


def camp(path):
    ws = openpyxl.load_workbook(path, data_only=True)["campaigns"]
    hdr = [c.value for c in ws[1]]
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[0] == CID:
            return dict(zip(hdr, r))
    return {}


def delete_tab(src, dst, frozen_csv=None):
    wb = openpyxl.load_workbook(src)
    del wb[CID]
    cfg = wb["config"]
    cfg.cell(row=T.CFG_ROW["today_override"], column=2, value=dt.date(2028, 1, 25))
    ws = wb["campaigns"]
    t = T.TABS["campaigns"]
    for r in range(2, ws.max_row + 1):
        if ws.cell(row=r, column=1).value == CID:
            ws.cell(row=r, column=t.index["answers_deleted_date"] + 1, value=dt.date(2028, 1, 19)).number_format = T.DATE
    if frozen_csv:
        fz = wb["survey_frozen"]
        ft = T.TABS["survey_frozen"]
        rows = list(csv.DictReader(open(frozen_csv, encoding="utf-8")))
        for i, row in enumerate(rows, start=ft.first()):
            for k, v in row.items():
                c = fz.cell(row=i, column=ft.index[k] + 1)
                c.value = int(v) if v.isdigit() else (dt.date.fromisoformat(v) if k == "frozen_date" else v)
    wb.save(dst)


def main():
    fails = []
    tmp = tempfile.mkdtemp(prefix="ops_ret_")
    scn = S.zero()
    final = DR.last_day(scn) + dt.timedelta(days=1)
    p = DR.build_snapshot(scn, final, os.path.join(tmp, "in.xlsx"))
    before_path = os.path.join(tmp, "before.xlsx")
    tr, errs, n = DR.recalc_and_read(p, before_path)
    before = camp(before_path)
    r = subprocess.run([sys.executable, "tools/freeze_survey.py", before_path, CID, tmp], capture_output=True, text=True, cwd=ROOT)
    fz = os.path.join(tmp, "survey-frozen-%s.csv" % CID)
    if r.returncode != 0 or not os.path.exists(fz):
        fails.append("freeze_survey refused: " + r.stdout[-300:])
    else:
        frozen_rows = list(csv.DictReader(open(fz, encoding="utf-8")))
        if sum(int(x["survey_responses"]) for x in frozen_rows) != before.get("survey_responses"):
            fails.append("frozen rows add up to %s, the campaign says %s" % (sum(int(x["survey_responses"]) for x in frozen_rows), before.get("survey_responses")))
        if any(k in frozen_rows[0] for k in ("comment", "Timestamp")):
            fails.append("the frozen file carries answers, not counts")
        # 2. freeze, delete, recalc
        delete_tab(p, os.path.join(tmp, "del-in.xlsx"), fz)
        after_path = RC.recalc(os.path.join(tmp, "del-in.xlsx"), os.path.join(tmp, "after.xlsx"))
        errs, n = RC.errors(after_path)
        if n:
            fails.append("after the deletion: %d formula errors %s" % (n, errs[:3]))
        after = camp(after_path)
        for k in NUMS:
            if after.get(k) != before.get(k):
                fails.append("after the deletion %s = %r, before %r" % (k, after.get(k), before.get(k)))
        chk = after.get("checks") or ""
        if "survey tab" in chk or "frozen" in chk:
            fails.append("after the deletion the campaign's checks say %r" % chk)
        tr2 = TR.Tracker(after_path)
        bad = [b for b in TR.compare(tr2) if not b.startswith("no cached")]
        if bad:
            fails.append("after the deletion the sheet and the arithmetic disagree: %s" % bad[:3])
        r1 = subprocess.run([sys.executable, "tools/export_actuals.py", before_path, os.path.join(tmp, "exp-before")], capture_output=True, text=True, cwd=ROOT)
        r2 = subprocess.run([sys.executable, "tools/export_actuals.py", after_path, os.path.join(tmp, "exp-after")], capture_output=True, text=True, cwd=ROOT)
        rows = lambda d: {x["campaign_id"]: x for x in csv.DictReader(open(os.path.join(tmp, d, "campaign_actuals.csv"), encoding="utf-8"))}
        if r1.returncode or r2.returncode:
            fails.append("export failed: %s %s" % (r1.stdout[-200:], r2.stdout[-200:]))
        else:
            eb, ea = rows("exp-before")[CID], rows("exp-after")[CID]
            for k in ("survey_responses", "survey_tried_yes", "survey_responses_min_office"):
                if eb[k] != ea[k]:
                    fails.append("export %s %s before, %s after the deletion" % (k, eb[k], ea[k]))
    # 3. negative control: deleted without the freeze
    delete_tab(p, os.path.join(tmp, "neg-in.xlsx"))
    neg_path = RC.recalc(os.path.join(tmp, "neg-in.xlsx"), os.path.join(tmp, "neg.xlsx"))
    neg = camp(neg_path)
    if neg.get("survey_responses") not in (0, None) or "no frozen totals" not in (neg.get("checks") or ""):
        fails.append("negative control: responses %r, checks %r" % (neg.get("survey_responses"), neg.get("checks")))
    print("SAMPLE-CMP-001: %s responses before; after freeze and deletion %s; without the freeze %s" % (
        before.get("survey_responses"), after.get("survey_responses") if "after" in dir() else "-", neg.get("survey_responses")))
    for f in fails:
        print("  FAIL " + f)
    print("PASS test_retention" if not fails else "FAIL test_retention")
    shutil.rmtree(tmp, ignore_errors=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
