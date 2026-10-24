#!/usr/bin/env python3
"""Recalculate clay-icp-tables.xlsx in LibreOffice and check every formula against the Python twin
(stage3_merge.derive) and the CSVs.

The workbook's views are INDEX/MATCH lookups (no SORT or FILTER), so LibreOffice computes every cell: nothing
is emulated. Set A_SOFFICE to test with another LibreOffice build (review round 1 ran 24.2 and 25.8).

Scenarios, each recalculated in LibreOffice and compared cell by cell with derive() on the same edits:
  baseline   the file as built: every formula column equals offices.csv / brands.csv, the view tabs equal
             daily-view-*.csv, walk-list-offices.csv and founder-review-brands.csv, rows 310 to 1000 are blank
  edits      every way to say do-not-contact (the status alone, the flag alone, an opt-out date alone), contacted,
             not_now, a group in flight (Carbyne replied blocks Prepared 911; Bruce Cost call_booked blocks Moshi;
             LesserEvil's status do_not_contact blocks PRETZELIZED), founder_ok_to_queue, known_to_founder
             (warm-intro, +points, the reason sentence), promote_backup after wrong_person, a founder-review
             clearance, a hold cleared
  enrichment a Clay export pasted on the Enrichment tab (shuffled and extra columns): verified rows switch to
             channel email; an opted-out row with a verified email stays out
  paste      the misuse R1-02 found: the Clay import pasted over the Offices tab. The view must show the
             'pasted over' warning and no row at all
  few        only three ready office rows left, plus two referral rows typed below the data (a colleague at the
             first company, queued, and a new company): the colleague blocks the first company, the referral rows
             compute like any other row, the view shows the rest and blanks, no #N/A
It also checks the drop-down lists reject other input. Writes scratch files under _work/test_workbook/.
    python3 -B clay-icp-tables/_build/test_workbook.py
"""
import os
import re
import shutil
import subprocess
import sys

import pandas as pd
from openpyxl import load_workbook

import build_xlsx as X
import common as C
import config as K
import stage3_merge as M

SCR = os.path.join(C.WORK, "test_workbook")
XLSX = os.path.join(C.A_DIR, "clay-icp-tables.xlsx")
SOFFICE = os.environ.get("A_SOFFICE", "soffice")
FAIL = []
LOG = []
NUM = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?$")


def recalc(src, tag):
    d = os.path.join(SCR, tag)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    prof = os.path.join(SCR, "lo_profile_" + str(abs(hash(SOFFICE)) % 10 ** 6))
    subprocess.run([SOFFICE, f"-env:UserInstallation=file://{prof}", "--headless", "--calc", "--convert-to", "xlsx",
                    "--outdir", d, src], capture_output=True, timeout=1200)
    out = os.path.join(d, os.path.basename(src))
    if not os.path.exists(out):
        sys.exit(f"LibreOffice produced no file for {tag}")
    return load_workbook(out, data_only=True)


def norm(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        f = float(v)
        return str(int(f)) if f.is_integer() else f"{round(f, 1)}"
    s = str(v)
    if NUM.match(s):
        f = float(s)
        return str(int(f)) if f.is_integer() else f"{round(f, 1)}"
    return s


def sheet_df(ws, nrows=None):
    rows = list(ws.iter_rows(values_only=True))
    head = [str(h) for h in rows[0]]
    body = rows[1:] if nrows is None else rows[1:nrows + 1]
    return pd.DataFrame([[norm(v) for v in r] for r in body], columns=head)


def compare(tag, got, exp, cols):
    bad_total = 0
    for c in cols:
        a = got[c].tolist()[:len(exp)]
        b = [norm(x) for x in exp[c].tolist()]
        bad = [(exp.row_id.iloc[i], a[i], b[i]) for i in range(len(b)) if a[i] != b[i]]
        if bad:
            bad_total += len(bad)
            FAIL.append(f"{tag}: {c} differs on {len(bad)} rows, first {bad[:2]}")
    return bad_total


def view_rows(ws, cols, n):
    df = sheet_df(ws, n)
    return df[cols]


def expected_view(df, side, slot, cols, n):
    e = df[df[slot] != ""].copy()
    e["_k"] = e[slot].astype(int)
    e = e.sort_values("_k").head(n)
    return e[cols]


def check_views(tag, wv, exp_o, exp_b):
    specs = [("Daily view - Offices", exp_o, "office", "view_slot", M.STABLE + M.DV_EXTRA["office"], K.DAILY_VIEW_SIZE),
             ("Daily view - Brands", exp_b, "brand", "view_slot", M.STABLE + M.DV_EXTRA["brand"], K.DAILY_VIEW_SIZE),
             ("Walk list - Offices", exp_o, "office", "walk_slot", M.WALK_VIEW, M.WALK_SIZE),
             ("Founder review - Brands", exp_b, "brand", "review_slot", M.REVIEW_VIEW, M.REVIEW_SIZE)]
    out = {}
    for tab, exp, side, slot, cols, n in specs:
        if exp is None:
            continue
        got = view_rows(wv[tab], cols, n)
        e = expected_view(exp, side, slot, cols, n)
        k = len(e)
        ids_got = [x for x in got.row_id.tolist() if x]
        if ids_got != e.row_id.tolist():
            FAIL.append(f"{tag} {tab}: rows {ids_got} vs expected {e.row_id.tolist()}")
        else:
            compare(f"{tag} {tab}", got.head(k).reset_index(drop=True), e.reset_index(drop=True), cols)
        rest = got.iloc[k:]
        if k and (rest != "").any().any():
            FAIL.append(f"{tag} {tab}: rows after the last view row are not blank")
        if any("#N/A" in str(v) or "Err:" in str(v) for v in got.values.ravel()):
            FAIL.append(f"{tag} {tab}: an error value is showing")
        out[tab] = ids_got
    return out


def apply_edits(wb, df, tab, edits):
    """edits: list of (row_id, column, value). Writes both the workbook copy and the expected frame."""
    ws = wb[tab]
    head = [c.value for c in ws[1]]
    d2 = df.copy()
    for rid, col, new in edits:
        idx = d2.index[d2.row_id == rid]
        assert len(idx) == 1, (tab, rid)
        i = idx[0]
        d2.at[i, col] = new
        ws.cell(row=i + 2, column=head.index(col) + 1, value=new)
    return d2


def rid(df, **kw):
    q = df
    for k, v in kw.items():
        q = q[q[k] == v]
    assert len(q) >= 1, kw
    return q.row_id.iloc[0]


def main():
    os.makedirs(SCR, exist_ok=True)
    off = pd.read_csv(os.path.join(C.A_DIR, "offices.csv"), dtype=str, keep_default_na=False)
    br = pd.read_csv(os.path.join(C.A_DIR, "brands.csv"), dtype=str, keep_default_na=False)
    enrich0 = pd.read_csv(os.path.join(C.WORK, "enrichment_build.csv"), dtype=str, keep_default_na=False)
    cols_o = [c for c in off.columns if c in X.FORMULA_COLS["office"] and c != "intact"]
    cols_b = [c for c in br.columns if c in X.FORMULA_COLS["brand"] and c != "intact"]

    # ---- 1. baseline
    wv = recalc(XLSX, "baseline")
    go, gb = sheet_df(wv["Offices"]), sheet_df(wv["Brands"])
    n = compare("baseline offices", go, off, cols_o) + compare("baseline brands", gb, br, cols_b)
    blank_tail = [c for c in cols_o if c != "row_order" and (go[c].iloc[len(off):] != "").any()]
    if blank_tail:
        FAIL.append(f"baseline: rows below the data are not blank in {blank_tail[:5]}")
    if (go.intact.iloc[:len(off)] != "Y").any():
        FAIL.append("baseline: intact is not Y on every data row")
    v = check_views("baseline", wv, off, br)
    for tab, f in (("Daily view - Offices", "daily-view-offices.csv"), ("Daily view - Brands", "daily-view-brands.csv")):
        csv_ids = pd.read_csv(os.path.join(C.A_DIR, f), dtype=str).row_id.tolist()
        if v.get(tab) != csv_ids:
            FAIL.append(f"baseline {tab} differs from {f}")
    LOG.append(f"baseline: {len(cols_o)} office and {len(cols_b)} brand formula columns on {len(off)} + {len(br)} "
               f"rows compared, {n} cells differ; views: " + "; ".join(f"{k} {len(x)} rows" for k, x in v.items()))

    # ---- 2. edits
    po = off[off.ready_for_outreach == "Y"].copy()
    po["_r"] = po["rank"].astype(int)
    po = po.sort_values("_r")
    r = po.row_id.tolist()
    back = off[(off.ready_for_outreach == "Y") & (off.backup_first_name != "")].row_id.tolist()
    call = off[(off.onsite_founder_call == "Y") & (off.gate_result == "pass") & (off.primary_first_name != "")
               & (off.hold_before_outreach != "Y")].row_id.tolist()
    held = off[(off.hold_before_outreach == "Y") & (off.gate_result == "pass") & (off.primary_first_name != "")].row_id.tolist()
    carbyne, prepared = rid(off, company="Carbyne"), rid(off, company="Prepared 911")
    eo = [(r[0], "status", "contacted"),
          (r[1], "status", "do_not_contact"),                 # the status alone (flag left N)
          (r[2], "do_not_contact", "Y"),                      # the flag alone
          (r[3], "opt_out_date", "2026-10-30"),               # the opt-out date alone
          (r[4], "status", "not_now"),
          (carbyne, "status", "replied"),
          (call[0], "founder_ok_to_queue", "Y"),
          (r[6], "known_to_founder", "Y"),
          (back[-1], "promote_backup", "Y"),
          (held[0], "hold_before_outreach", "N")]
    pb = br[br.gate_result == "pass"].copy()
    pb["_r"] = pb["rank"].astype(int)
    pb = pb.sort_values("_r")
    rb = pb[pb.ready_for_outreach == "Y"].row_id.tolist()
    blocked = pb[(pb.review_blocking == "Y") & (pb.primary_first_name != "")].row_id.tolist()
    bback = br[(br.ready_for_outreach == "Y") & (br.backup_first_name != "")].row_id.tolist()
    eb = [(rb[0], "status", "queued"),
          (rid(br, company="Bruce Cost Ginger Ale"), "status", "call_booked"),
          (rid(br, company="LesserEvil"), "status", "do_not_contact"),   # flag left N: must still block PRETZELIZED
          (rb[5], "known_to_founder", "Y"),
          (blocked[0], "founder_review_cleared", "Y"),
          (bback[1], "promote_backup", "Y")]
    wb = load_workbook(XLSX)
    xo = M.derive(apply_edits(wb, off, "Offices", eo), "office", enrich0)
    xb = M.derive(apply_edits(wb, br, "Brands", eb), "brand", enrich0)
    scen = os.path.join(SCR, "scenario.xlsx")
    wb.save(scen)
    ws2 = recalc(scen, "scenario")
    n = compare("edits offices", sheet_df(ws2["Offices"]), xo, cols_o) + \
        compare("edits brands", sheet_df(ws2["Brands"]), xb, cols_b)
    v = check_views("edits", ws2, xo, xb)

    def g(df, rid_, col):
        return df[df.row_id == rid_][col].iloc[0]
    dv_o, dv_b = set(xo[xo.in_daily_view == "Y"].row_id), set(xb[xb.in_daily_view == "Y"].row_id)
    pretz = rid(br, company="PRETZELIZED")
    facts = [("status do_not_contact alone keeps the row out", r[1] not in dv_o),
             ("flag alone keeps the row out", r[2] not in dv_o),
             ("opt-out date alone keeps the row out", r[3] not in dv_o),
             ("Carbyne replied blocks Prepared 911", g(xo, prepared, "group_blocked") == "Y"),
             ("Bruce Cost call_booked blocks Moshi", g(xb, rid(br, company="Moshi"), "group_blocked") == "Y"),
             ("LesserEvil status do_not_contact blocks PRETZELIZED", g(xb, pretz, "group_blocked") == "Y"
              and pretz not in dv_b),
             ("known_to_founder makes the channel warm-intro", g(xo, r[6], "channel") == "warm-intro"),
             ("known_to_founder adds 15 points", abs(float(g(xo, r[6], "score")) - float(g(off, r[6], "score")) - 15) < 1e-6),
             ("score_reason names the known flag", "known to the founder (+15)" in g(xo, r[6], "score_reason")),
             ("promote_backup shows the backup", g(xo, back[-1], "first_name") == g(off, back[-1], "backup_first_name")),
             ("promote_backup re-grades the title", g(xo, back[-1], "title_match") == g(off, back[-1], "backup_title_match")),
             ("founder_ok_to_queue makes an out-of-band office ready", g(xo, call[0], "ready_for_outreach") == "Y"),
             ("founder_review_cleared makes a held brand ready", g(xb, blocked[0], "ready_for_outreach") == "Y")]
    for name, ok in facts:
        if not ok:
            FAIL.append("edits fact failed: " + name)
    LOG.append(f"edits: {len(eo)} office and {len(eb)} brand edits, {n} cells differ from derive(); "
               f"{sum(ok for _, ok in facts)} of {len(facts)} facts hold; office view now "
               + ", ".join(xo[xo.in_daily_view == 'Y'].sort_values('daily_view_rank', key=lambda s: s.astype(int)).company))

    # ---- 3. enrichment paste (a Clay export on the Enrichment tab)
    imp = pd.read_csv(os.path.join(C.A_DIR, "clay-import", "offices-clay-import.csv"), dtype=str, keep_default_na=False)
    pick = [r[5], r[7], r[2]]   # two ready rows and the flag-only opt-out row
    ex = imp[imp.row_id.isin(pick)].copy()
    stat = {pick[0]: "verified", pick[1]: "risky", pick[2]: "verified"}
    ex["work_email"] = [f"SAMPLE.person{i}@example.com" for i in range(len(ex))]
    ex["email_status"] = ex.row_id.map(stat)
    ex["clay_note"] = "SAMPLE"
    ex = ex[list(reversed(ex.columns))]  # columns in another order, extra columns kept
    wb = load_workbook(scen)
    ws = wb["Enrichment"]
    ws.delete_rows(1, ws.max_row)
    for j, c in enumerate(ex.columns, start=1):
        ws.cell(row=1, column=j, value=c)
    for i, rec in enumerate(ex.to_dict("records"), start=2):
        for j, c in enumerate(ex.columns, start=1):
            ws.cell(row=i, column=j, value=rec[c])
    en_path = os.path.join(SCR, "enrichment.xlsx")
    wb.save(en_path)
    ws3 = recalc(en_path, "enrichment")
    xo3 = M.derive(apply_edits(load_workbook(XLSX), off, "Offices", eo), "office", ex)
    n = compare("enrichment offices", sheet_df(ws3["Offices"]), xo3, cols_o)
    check_views("enrichment", ws3, xo3, None)
    facts = [("a verified email switches the channel to email", g(xo3, r[5], "channel") == "email"),
             ("a 'risky' result reads unverified", g(xo3, r[7], "email_status") == "unverified"),
             ("the opted-out row stays out with a verified email", r[2] not in set(xo3[xo3.in_daily_view == "Y"].row_id))]
    for name, ok in facts:
        if not ok:
            FAIL.append("enrichment fact failed: " + name)
    LOG.append(f"enrichment: {len(ex)} rows pasted with {len(ex.columns)} columns in another order, {n} cells differ")

    # ---- 4. the misuse: the Clay import pasted over the Offices tab
    wb = load_workbook(scen)
    ws = wb["Offices"]
    for j, c in enumerate(imp.columns, start=1):
        ws.cell(row=1, column=j, value=c)
    for i, rec in enumerate(imp.to_dict("records"), start=2):
        for j, c in enumerate(imp.columns, start=1):
            ws.cell(row=i, column=j, value=rec[c])
    pp = os.path.join(SCR, "paste.xlsx")
    wb.save(pp)
    ws4 = recalc(pp, "paste")
    dv = sheet_df(ws4["Daily view - Offices"], K.DAILY_VIEW_SIZE)[M.STABLE + M.DV_EXTRA["office"]]
    a2 = dv.iloc[0, 0]
    others = (dv.values.ravel()[1:] != "").sum()
    if "pasted over" not in a2 or others:
        FAIL.append(f"paste: the view did not fail safe (A2 = {a2[:60]!r}, {others} other cells filled)")
    LOG.append(f"paste: Clay import pasted over Offices!A1 ({len(imp)} rows x {len(imp.columns)} columns); the view "
               f"shows only the warning: {'yes' if 'pasted over' in a2 and not others else 'NO'}")

    # ---- 5. few rows left, plus two referral rows typed below the data (R1-17: the formulas reach row 1000)
    eo5 = [(x, "status", "contacted") for x in r[3:]]
    wb = load_workbook(XLSX)
    d5 = apply_edits(wb, off, "Offices", eo5)
    colleague = {"row_id": "AO-R-001", "company": g(off, r[0], "company"), "primary_first_name": "SAMPLE",
                 "primary_last_name": "Colleague", "primary_title": "Office Manager", "status": "queued",
                 "do_not_contact": "N", "referral_from": r[0], "company_group": g(off, r[0], "company_group")}
    other = {"row_id": "AO-R-002", "company": "SAMPLE Referred Co", "primary_first_name": "SAMPLE",
             "primary_last_name": "Referral", "primary_title": "Office Manager", "status": "new",
             "do_not_contact": "N", "referral_from": r[1]}
    ws = wb["Offices"]
    head = [c.value for c in ws[1]]
    refs = []
    for k, rec in enumerate((colleague, other)):
        row = len(off) + 2 + k
        for col, val in rec.items():
            ws.cell(row=row, column=head.index(col) + 1, value=val)
        full = {c: "" for c in d5.columns}
        full.update(rec)
        refs.append(full)
    d5 = pd.concat([d5, pd.DataFrame(refs)], ignore_index=True)
    xo5 = M.derive(d5, "office", enrich0)
    fp = os.path.join(SCR, "few.xlsx")
    wb.save(fp)
    ws5 = recalc(fp, "few")
    got5 = sheet_df(ws5["Offices"])
    n = compare("few offices", got5, xo5, cols_o)
    v = check_views("few", ws5, xo5, None)
    ref_rows = got5[got5.row_id.isin(["AO-R-001", "AO-R-002"])]
    facts = [("a colleague referral in flight blocks the referrer's company", r[0] not in v.get("Daily view - Offices", [])
              and g(xo5, r[0], "group_blocked") == "Y"),
             ("referral rows compute without error values",
              len(ref_rows) == 2 and not any("#" in str(x) or "Err:" in str(x) for x in ref_rows.values.ravel())),
             ("a referral row shows its typed contact", g(xo5, "AO-R-002", "first_name") == "SAMPLE")]
    for name, ok in facts:
        if not ok:
            FAIL.append("few fact failed: " + name)
    LOG.append(f"few: {len(eo5)} ready rows set contacted and 2 referral rows typed below the data; the view shows "
               f"{len(v.get('Daily view - Offices', []))} rows (expected {int((xo5.in_daily_view == 'Y').sum())}), "
               f"rest blank, {n} cells differ; {sum(ok for _, ok in facts)} of {len(facts)} referral facts hold")

    # ---- 6. validation lists refuse other input
    wbf = load_workbook(XLSX)
    for tab in ("Offices", "Brands"):
        ws = wbf[tab]
        head = [c.value for c in ws[1]]
        have = {}
        for dvv in ws.data_validations.dataValidation:
            for rg in str(dvv.sqref).split():
                have[rg.split(":")[0].rstrip("0123456789")] = dvv
        for col in ("status", "do_not_contact", "known_to_founder", "hold_before_outreach", "promote_backup"):
            letter = X.get_column_letter(head.index(col) + 1)
            d = have.get(letter)
            if d is None or not d.showErrorMessage or d.errorStyle not in (None, "stop"):
                FAIL.append(f"{tab}: {col} validation does not reject other input")
    LOG.append("validation: status, do_not_contact, known_to_founder, hold_before_outreach and promote_backup refuse "
               "other input (error style stop)")

    print(f"LibreOffice: {SOFFICE}")
    print("\n".join(LOG))
    print("FAIL:\n  " + "\n  ".join(FAIL[:40]) if FAIL else "PASS: every formula and view equals the Python twin in "
          "all five scenarios")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
