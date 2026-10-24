#!/usr/bin/env python3
"""Test the conversation tracker with SAMPLE rows and a LibreOffice recalculation.

    python3 tools/test_tracker.py            # builds, recalculates, compares, writes _work/partB/test_log.txt

Expected values are computed here in Python from tools/sample_data.py, independently of the
spreadsheet formulas, then compared with what LibreOffice calculates from the workbook.
"""
import datetime as dt
import os
import shutil
import statistics
import subprocess
import sys
import tempfile

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_tracker as BT          # noqa: E402
import sample_data as S             # noqa: E402

ERRORS = ("#N/A", "#VALUE!", "#REF!", "#DIV/0!", "#NAME?", "#NUM!", "#NULL!", "Err:")
LOG = []
FAILS = []


def say(msg):
    LOG.append(msg)
    print(msg)


def check(label, got, want):
    ok = (got == want) or (isinstance(got, (int, float)) and isinstance(want, (int, float)) and abs(got - want) < 1e-9)
    say(f"{'ok  ' if ok else 'FAIL'} {label}: got {got!r} want {want!r}")
    if not ok:
        FAILS.append(label)


def recalc(path):
    tmp = tempfile.mkdtemp(prefix="ddtr_")
    src = os.path.join(tmp, "in.xlsx")
    shutil.copy(path, src)
    out = os.path.join(tmp, "out")
    os.makedirs(out)
    subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", out, src],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    res = os.path.join(out, "in.xlsx")
    return openpyxl.load_workbook(res, data_only=True), res


def errors(wb):
    errs = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith(ERRORS):
                    errs.append(f"{ws.title}!{c.coordinate}={c.value}")
    return errs


def as_date(v):
    if isinstance(v, dt.datetime):
        return v.date()
    return v


# ----------------------------------------------------------------------------- expected values
CUTS = {"B": dt.date(2026, 10, 30), "C": dt.date(2026, 11, 6), "D": dt.date(2026, 11, 13), "E": S.AS_OF}
QUAL = ("qual_q1_sealed_shelf_stable_60d", "qual_q2_labeled_ingredients_allergens", "qual_q3_buy_path_near_cluster",
        "qual_q4_can_ship_275_in_10bd", "qual_q5_product_liability_insurance", "qual_q6_contact_can_approve_600", "qual_not_excluded")


def first_per_org(rows, pred, cut):
    """Earliest row (by call_date, then sheet order) per row_id satisfying pred, with date <= cut."""
    best = {}
    for i, r in enumerate(rows):
        if not pred(r):
            continue
        key = (r["call_date"], i)
        if r["row_id"] not in best or key < best[r["row_id"]][0]:
            best[r["row_id"]] = (key, r)
    return [r for (k, r) in best.values() if k[0] <= cut]


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def median_or(vals):
    return statistics.median(vals) if vals else "none yet"


def expected_office(cut):
    L = S.OFFICE_LOG
    e = {}
    e["o_conv"] = len(first_per_org(L, lambda r: True, cut))
    e["o_yes"] = len(first_per_org(L, lambda r: r["yes_in_principle"] == "Y" and r["pantry_owner_named"] == "Y" and r["receiving_window"].strip(), cut))
    e["o_yes_any"] = len(first_per_org(L, lambda r: r["yes_in_principle"] == "Y", cut))
    e["o_maybe"] = len(first_per_org(L, lambda r: r["yes_in_principle"] == "maybe", cut))
    e["o_warm"] = len(first_per_org(L, lambda r: r["channel"] == "warm-intro", cut))
    e["o_short"] = len(first_per_org(L, lambda r: r.get("shortlist") == "Y", cut))
    bp = [r["budget_probe_low_usd"] for r in first_per_org(L, lambda r: num(r["budget_probe_low_usd"]), cut)]
    e["o_bp_med"] = median_or(bp)
    e["o_bp_n"] = len(bp)
    e["o_bp_zero"] = sum(1 for v in bp if v == 0)
    return e


def expected_office_asof():
    L, cut = S.OFFICE_LOG, S.AS_OF
    bp100 = len(first_per_org(L, lambda r: num(r["budget_probe_low_usd"]) and r["budget_probe_low_usd"] >= 100, cut))
    spend = [r["monthly_pantry_spend_usd"] for r in first_per_org(L, lambda r: num(r["monthly_pantry_spend_usd"]), cut)]
    return bp100, median_or(spend)


def expected_brand(cut):
    L = S.BRAND_LOG
    e = {}
    mx = lambda r: max(r["wtp_before_usd"] or 0, r["wtp_after_usd"] or 0)
    e["b_conv"] = len(first_per_org(L, lambda r: True, cut))
    e["b_yes"] = len(first_per_org(L, lambda r: r["controls_budget"] == "Y" and mx(r) >= 500, cut))
    e["b_strict"] = len(first_per_org(L, lambda r: r["controls_budget"] == "Y" and num(r["wtp_before_usd"]) and r["wtp_before_usd"] >= 500, cut))
    e["b_noctrl"] = len(first_per_org(L, lambda r: r["controls_budget"] != "Y" and mx(r) >= 500, cut))
    wb = [r["wtp_before_usd"] for r in first_per_org(L, lambda r: num(r["wtp_before_usd"]), cut)]
    wa = [r["wtp_after_usd"] for r in first_per_org(L, lambda r: num(r["wtp_after_usd"]), cut)]
    e["b_wb_med"], e["b_wb_n"] = median_or(wb), len(wb)
    e["b_wa_med"], e["b_wa_n"] = median_or(wa), len(wa)
    e["b_short"] = len(first_per_org(L, lambda r: r.get("shortlist") == "Y", cut))
    e["b_qualified"] = len(first_per_org(L, lambda r: all(r[k] == "Y" for k in QUAL) and r["qual_q7_why_now"].strip(), cut))
    return e


def expected_top3(rows, codes, labels, cut):
    counts = {c: 0 for c in codes}
    for r in rows:
        if r["call_date"] > cut:
            continue
        for k in ("objection_1", "objection_2", "objection_3"):
            if r[k]:
                counts[r[k]] += 1
    order = sorted(codes, key=lambda c: (-counts[c], codes.index(c)))
    out = []
    for k, c in enumerate(order[:3], start=1):
        if counts[c] < 1:
            out.append((f"{k}. none logged yet", counts[c], ""))
            continue
        quote = ""
        for col in ("objection_1", "objection_2", "objection_3"):
            hit = [r for r in rows if r[col] == c]
            if hit:
                quote = hit[0]["objections_verbatim"]
                break
        out.append((f"{k}. {labels[codes.index(c)]} ({c})", counts[c], quote))
    return out


def expected_pace(clay, cut, conv):
    first = sum(1 for r in clay if r["touch_1_date"] and r["touch_1_date"] <= cut)
    rep = sum(1 for r in clay if r["last_reply_date"] and r["last_reply_date"] <= cut and r["reply_type"] not in ("bounce", "out_of_office"))
    pos = sum(1 for r in clay if r["last_reply_date"] and r["last_reply_date"] <= cut and r["reply_type"] in ("yes", "maybe", "needs_approval", "send_info", "referral"))
    oo = sum(1 for r in clay if r["opt_out_date"] and r["opt_out_date"] <= cut)
    return {"first": first, "replies": rep, "rate": (rep / first) if first else "", "positive": pos,
            "convrate": (conv / first) if first else "", "optout": oo}


def expected_events():
    ev = []   # (date, block, i, side, org_id, org_name, event, value_number, value_text, controls, notes)
    for i, r in enumerate(S.OFFICE_LOG, start=1):
        ev.append((r["call_date"], 1, i, "office", r["row_id"], r["company"], "conversation", "", "", "", r["call_type"]))
        if r["yes_in_principle"] == "Y" and r["pantry_owner_named"] == "Y" and r["receiving_window"].strip():
            ev.append((r["call_date"], 2, i, "office", r["row_id"], r["company"], "yes_in_principle", "", "", "",
                       f"owner: {r['pantry_owner_title']}; window: {r['receiving_window']}"))
        if r["budget_probe_verbatim"].strip() or num(r["budget_probe_low_usd"]):
            lo, hi = r["budget_probe_low_usd"], r["budget_probe_high_usd"]
            note = f"range to {hi} per month" if (num(hi) and (hi or 0) > (lo or 0)) else ""
            ev.append((r["call_date"], 3, i, "office", r["row_id"], r["company"], "budget_probe", lo if num(lo) else "",
                       r["budget_probe_verbatim"], "", note))
    for i, r in enumerate(S.BRAND_LOG, start=1):
        ev.append((r["call_date"], 4, i, "brand", r["row_id"], r["company"], "conversation", "", "", "", r["call_type"]))
        if r["yes_in_principle"] == "Y":
            ev.append((r["call_date"], 5, i, "brand", r["row_id"], r["company"], "yes_in_principle", "", "", r["controls_budget"], ""))
        if num(r["wtp_before_usd"]) or r["wtp_before_verbatim"].strip():
            ev.append((r["call_date"], 6, i, "brand", r["row_id"], r["company"], "budget_probe",
                       r["wtp_before_usd"] if num(r["wtp_before_usd"]) else "", r["wtp_before_verbatim"], r["controls_budget"], ""))
        if r["price_1500_mentioned"] == "Y" and (num(r["wtp_after_usd"]) or r["wtp_after_verbatim"].strip()):
            ev.append((r["call_date"], 7, i, "brand", r["row_id"], r["company"], "budget_probe",
                       r["wtp_after_usd"] if num(r["wtp_after_usd"]) else "", r["wtp_after_verbatim"], r["controls_budget"], "after_1500"))
    for i, r in enumerate(S.SIGNED_OFFICES, start=1):
        ev.append((r["agreement_signed_date"], 8, i, "office", r["clay_row_id"], r["company"], "signed", r["tuesday_headcount"], "", "", r["office_id"]))
    for i, r in enumerate(S.PAID_BRANDS, start=1):
        for k, b in ((1, 9), (2, 10)):
            if r.get(f"payment_{k}_date") and num(r.get(f"payment_{k}_usd")):
                ev.append((r[f"payment_{k}_date"], b, i, "brand", r["clay_row_id"], r["brand_name"], "paid", r[f"payment_{k}_usd"], "", "",
                           f"payment {k}; {r['brand_id']}; {r['tier']}; invoice {r['invoice_id']}"))
    for i, r in enumerate(S.LATER_EVENTS, start=1):
        ev.append((r["date"], 11, i, r["side"], r["clay_row_id"], r["org_name"], r["event"],
                   r["value_number"] if num(r["value_number"]) else "", r["value_text"], "", r["notes"]))
    b = 12
    for side, clay in (("office", S.CLAY_OFFICES), ("brand", S.CLAY_BRANDS)):
        for k in (1, 2, 3):
            for i, r in enumerate(clay, start=1):
                d = r.get(f"touch_{k}_date")
                if d:
                    ev.append((d, b, i, side, r["row_id"], r["company"], "outreach_sent", "", "", "", f"touch_{k}; {r['sequence']}; {r['channel']}"))
            b += 1
    ev.sort(key=lambda x: (x[0], x[1], x[2]))
    return [(e[0], e[3], e[4], e[5], e[6], e[7], e[8], e[9], e[10]) for e in ev]


# ----------------------------------------------------------------------------- tests
def test_sample(b):
    path = os.path.join(ROOT, "tracking", "conversation-tracker-SAMPLE.xlsx")
    wb, recalced = recalc(path)
    errs = errors(wb)
    check("SAMPLE workbook: error cells after recalculation", len(errs), 0)
    for e in errs[:20]:
        say("   " + e)
    sc = wb["Scorecard"]
    v = lambda ref: sc[ref].value
    check("SAMPLE banner present", isinstance(v("A1"), str) and v("A1").startswith("SAMPLE: this file holds"), True)
    for col, cut in CUTS.items():
        eo, eb = expected_office(cut), expected_brand(cut)
        for k, want in eo.items():
            check(f"office {k} @ {cut}", v(f"{col}{b.sc[k]}"), want)
        for k, want in eb.items():
            check(f"brand {k} @ {cut}", v(f"{col}{b.sc[k]}"), want)
        o_pass = "PASS" if eo["o_yes"] >= 5 else ("not yet" if cut < dt.date(2026, 11, 13) else "FAIL")
        b_pass = "PASS" if eb["b_yes"] >= 3 else ("not yet" if cut < dt.date(2026, 11, 13) else "FAIL")
        check(f"office Gate 0 status @ {cut}", v(f"{col}{b.sc['o_status']}"), o_pass)
        check(f"brand Gate 0 status @ {cut}", v(f"{col}{b.sc['b_status']}"), b_pass)
        g = "PASS" if (o_pass == "PASS" and b_pass == "PASS") else ("FAIL" if "FAIL" in (o_pass, b_pass) else "not yet")
        check(f"Gate 0 overall @ {cut}", v(f"{col}{b.sc['g0']}"), g)
        for side, clay, conv_key in (("office", S.CLAY_OFFICES, "o_conv"), ("brand", S.CLAY_BRANDS, "b_conv")):
            conv = (eo if side == "office" else eb)[conv_key]
            ep = expected_pace(clay, cut, conv)
            for k, want in ep.items():
                check(f"{side} pace {k} @ {cut}", v(f"{col}{b.sc[f'{side}_{k}']}"), want)
    bp100, spend = expected_office_asof()
    check("offices naming $100+/month (as of)", v(f"E{b.sc['o_bp100']}"), bp100)
    check("median pantry spend (as of)", v(f"E{b.sc['o_spend']}"), spend)
    q2 = [r["q2_sampling_budget_quarter_low_usd"] for r in first_per_org(S.BRAND_LOG, lambda r: num(r["q2_sampling_budget_quarter_low_usd"]), S.AS_OF)]
    check("median quarterly sampling budget (as of)", v(f"E{b.sc['b_q2']}"), statistics.median(q2))
    # Gate 1 block (Gate 1 date and as of)
    g1 = dt.date(2026, 12, 11)
    for col, cut in (("D", g1), ("E", S.AS_OF)):
        signed = [r for r in S.SIGNED_OFFICES if r["agreement_signed_date"] <= cut]
        check(f"Gate 1 offices signed @ {cut}", v(f"{col}{b.sc['g1_signed']}"), len(signed))
        check(f"Gate 1 headcount @ {cut}", v(f"{col}{b.sc['g1_headcount']}"), sum(r["tuesday_headcount"] for r in signed))
        full = 0
        for r in S.PAID_BRANDS:
            tot = (r["payment_1_usd"] or 0) + (r["payment_2_usd"] or 0)
            dd = max(d for d in (r["payment_1_date"], r["payment_2_date"]) if d)
            if tot >= r["price_usd"] and dd <= cut:
                full += 1
        check(f"Gate 1 brands paid in full @ {cut}", v(f"{col}{b.sc['g1_paid']}"), full)
        o_st = "PASS" if (len(signed) >= 5 and sum(r["tuesday_headcount"] for r in signed) >= 350) else ("not yet" if cut < g1 else "FAIL")
        b_st = "PASS" if full >= 2 else ("not yet" if cut < g1 else ("SOFT PASS" if full == 1 else "FAIL"))
        check(f"Gate 1 office status @ {cut}", v(f"{col}{b.sc['g1_o_status']}"), o_st)
        check(f"Gate 1 brand status @ {cut}", v(f"{col}{b.sc['g1_b_status']}"), b_st)
    # numbers for the Startup CPG posts (as of)
    L, Lb, cut = S.OFFICE_LOG, S.BRAND_LOG, S.AS_OF
    f1 = lambda rows, pred: len(first_per_org(rows, pred, cut))
    check("post: office conversations", v(f"E{b.sc['post_office_conv']}"), expected_office(cut)["o_conv"])
    check("post: brands reach out", v(f"E{b.sc['post_reach']}"), f1(L, lambda r: r["q3_brands_reach_out"] == "Y"))
    check("post: one person decides", v(f"E{b.sc['post_alone']}"), f1(L, lambda r: r["owner_can_say_yes_alone"] == "Y"))
    check("post: photo and survey yes", v(f"E{b.sc['post_q5']}"), f1(L, lambda r: r["q5_photo_and_survey"] == "Y"))
    check("post: use a snack service", v(f"E{b.sc['post_svc']}"), f1(L, lambda r: r["uses_snack_service"] == "Y"))
    hcs = [r["tuesday_headcount"] for r in first_per_org(L, lambda r: num(r["tuesday_headcount"]), cut)]
    check("post: Tuesday range", v(f"E{b.sc['post_hc']}"), f"{min(hcs)} to {max(hcs)}")
    from collections import Counter
    ap = Counter(r["other_approver"] for r in L if r["call_date"] <= cut and r["other_approver"])
    order = BT.LISTS["other_approver"]
    best = max(ap.values())
    check("post: most common other approver", v(f"E{b.sc['post_appr']}"), [a for a in order if ap.get(a, 0) == best][0])
    lo = [r["q2_sampling_budget_quarter_low_usd"] for r in first_per_org(Lb, lambda r: num(r["q2_sampling_budget_quarter_low_usd"]), cut)]
    hi = [r["q2_sampling_budget_quarter_high_usd"] for r in first_per_org(Lb, lambda r: num(r["q2_sampling_budget_quarter_low_usd"]), cut)]
    check("post: brand spend range", v(f"E{b.sc['post_spend']}"), f"${min(lo):,} to ${max(hi + lo):,}")
    check("post: seeded offices", v(f"E{b.sc['post_seeded']}"), f1(Lb, lambda r: r["q3_seeded_offices"] == "Y"))
    check("post: median number named", v(f"E{b.sc['post_median']}"), expected_brand(cut)["b_wb_med"])
    check("post: top blocker equals top brand objection", v(f"E{b.sc['post_blocker']}"), v(f"A{b.sc['top_brand_1']}"))
    check("post: quotes allowed", v(f"E{b.sc['post_quotes']}"), f1(L, lambda r: r["quote_ok_to_share"] == "Y") + f1(Lb, lambda r: r["quote_ok_to_share"] == "Y"))
    # copy-slot counts
    oy = sum(1 for r in S.CLAY_OFFICES if r["status"] in ("yes_in_principle", "materials_sent", "signed"))
    check("slot offices_yes", v(f"E{b.sc['slot_offices_yes']}"), oy)
    check("slot offices_signed", v(f"E{b.sc['slot_offices_signed']}"), sum(1 for r in S.CLAY_OFFICES if r["status"] == "signed"))
    check("slot tuesday_headcount", v(f"E{b.sc['slot_headcount']}"), sum(r["tuesday_headcount"] for r in S.SIGNED_OFFICES))
    check("slot founding_taken", v(f"E{b.sc['slot_founding']}"), sum(1 for r in S.PAID_BRANDS if r["tier"] == "founding"))
    check("slot brands_paid", v(f"E{b.sc['slot_brands_paid']}"), len(S.PAID_BRANDS))
    eb_asof = expected_brand(S.AS_OF)
    check("slot brand_selling_on", v(f"E{b.sc['slot_brand_selling']}"), "Y" if (eb_asof["b_yes"] >= 3 and oy >= 2) else "N")
    check("check: duplicate handoff rows", v(f"E{b.sc['chk_Duplicate clay_row_id on signed_offices or paid_brands']}"), 0)
    # top three objections
    for side, rows, lst in (("office", S.OFFICE_LOG, "office_objection"), ("brand", S.BRAND_LOG, "brand_objection")):
        exp = expected_top3(rows, BT.LISTS[lst], BT.LISTS[lst + "_label"], S.AS_OF)
        for k in (1, 2, 3):
            r = b.sc[f"top_{side}_{k}"]
            check(f"top {side} objection {k} label", v(f"A{r}"), exp[k - 1][0])
            check(f"top {side} objection {k} mentions", v(f"B{r}"), exp[k - 1][1])
            check(f"top {side} objection {k} quote", v(f"C{r}") or "", exp[k - 1][2])
    # sentence
    sent = v(f"B{b.sc['sentence']}")
    eo, eb = expected_office(S.AS_OF), expected_brand(S.AS_OF)
    want = (f"As of {S.AS_OF.isoformat()}: {eo['o_yes']} of {eo['o_conv']} offices said yes with a pantry owner and a receiving window (target 5); "
            f"{eb['b_yes']} of {eb['b_conv']} brands would pay $500 or more and control the budget (target 3). Gate 0: PASS.")
    check("Gate 0 sentence", sent, want)
    # reply-rate check text
    for side, clay, conv_key in (("office", S.CLAY_OFFICES, "o_conv"), ("brand", S.CLAY_BRANDS, "b_conv")):
        ep = expected_pace(clay, S.AS_OF, 0)
        want = (f"Too few first touches to judge ({ep['first']} of 30)." if ep["first"] < 30 else
                ("UNDER 20%: run sending/sending-setup.md section 6 before sending more." if ep["rate"] < 0.2 else "OK: at or above 20%."))
        check(f"{side} reply-rate message", v(f"B{b.sc[f'{side}_check']}"), want)
    # sequence table: office-discovery-A
    r = b.sc["seq_first"]
    exp_sends = sum(1 for x in S.CLAY_OFFICES if x["sequence"] == "office-discovery-A" and x["touch_1_date"] and x["touch_1_date"] <= S.AS_OF)
    exp_rep = sum(1 for x in S.CLAY_OFFICES if x["sequence"] == "office-discovery-A" and x["last_reply_date"] and x["last_reply_date"] <= S.AS_OF
                  and x["reply_type"] not in ("bounce", "out_of_office"))
    check("sequence office-discovery-A first touches", v(f"C{r}"), exp_sends)
    check("sequence office-discovery-A replies", v(f"D{r}"), exp_rep)
    # sync flags on the logs
    OL, BL = b.C_office, b.C_brand
    ws = wb["Office_Log"]
    flags = {ws[f"A{i}"].value: ws[f"{OL.L('calc_sync_issue')}{i}"].value for i in range(2, 2 + len(S.OFFICE_LOG)) if ws[f"{OL.L('calc_sync_issue')}{i}"].value}
    check("office log sync flags (row_ids)", sorted(flags), ["SAMPLE-O-004", "SAMPLE-O-006", "SAMPLE-O-014"])
    check("office flag O-004 text", flags.get("SAMPLE-O-004"), "Clay status is replied: set call_done or later")
    check("office flag O-006 text", flags.get("SAMPLE-O-006"), "Clay yes_in_principle should be Y")
    check("office flag O-014 text", flags.get("SAMPLE-O-014"), "row_id not found in the Clay paste: add the Clay row or fix the row_id")
    ws = wb["Brand_Log"]
    flags = {ws[f"A{i}"].value: ws[f"{BL.L('calc_sync_issue')}{i}"].value for i in range(2, 2 + len(S.BRAND_LOG)) if ws[f"{BL.L('calc_sync_issue')}{i}"].value}
    check("brand log sync flags", flags, {"SAMPLE-B-009": "Clay status is call_booked: set call_done or later"})
    sy = wb["Sync"]
    top = b.sync_top
    off = {sy[f"C{r}"].value: sy[f"G{r}"].value for r in range(top, top + 60) if sy[f"G{r}"].value}
    brd = {sy[f"J{r}"].value: sy[f"N{r}"].value for r in range(top, top + 60) if sy[f"N{r}"].value}
    check("Clay office-side flags", off, {"SAMPLE-O-020": "status call_done but no tracker row",
                                         "SAMPLE-O-030": "do_not_contact = Y but status is contacted"})
    check("Clay brand-side flags", brd, {"SAMPLE-B-021": "status paid but no paid_brands row and no tracker row"})
    check("handoff status flags", [sy["R22"].value, sy["V22"].value], [None, None])
    # handoff formulas
    so = wb["signed_offices"]
    S_ = b.signed_cols
    first_probe = first_per_org([r for r in S.OFFICE_LOG if r["row_id"] == "SAMPLE-O-001"],
                                lambda r: bool(r["budget_probe_verbatim"].strip()) or num(r["budget_probe_low_usd"]), S.AS_OF)[0]
    check("signed_offices budget_probe_verbatim (from log)", so[f"{S_.L('budget_probe_verbatim')}2"].value, first_probe["budget_probe_verbatim"])
    check("signed_offices budget_probe_date", as_date(so[f"{S_.L('budget_probe_date')}2"].value), first_probe["call_date"])
    check("signed_offices budget_probe_monthly_usd", so[f"{S_.L('budget_probe_monthly_usd')}2"].value, first_probe["budget_probe_low_usd"])
    pb = wb["paid_brands"]
    check("paid_brands payment_received_date", as_date(pb[f"{b.paid_cols.L('payment_received_date')}2"].value), S.PAID_BRANDS[0]["payment_1_date"])
    # note entry tab: the row to paste equals the first office log row
    ne = wb["Note_Office"]
    nr = b.note_row_office
    got_row = [as_date(ne.cell(row=nr, column=j + 1).value) for j in range(len(BT.OFFICE_COLS))]
    want_row = [S.OFFICE_LOG[0].get(c[0]) for c in BT.OFFICE_COLS]
    want_row = ["" if v is None else v for v in want_row]
    got_row = ["" if v is None else v for v in got_row]
    check("Note_Office row to paste equals the log row", got_row, want_row)
    check("Note_Office check cell", ne.cell(row=nr - 2, column=2).value, "OK to paste")
    check("Note_Brand row to paste is blank when empty", all(wb["Note_Brand"].cell(row=b.note_row_brand, column=j + 1).value in (None, "") for j in range(len(BT.BRAND_COLS))), True)
    # pipeline export
    pl = wb["pipeline_log"]
    check("pipeline_log header", [pl.cell(row=1, column=j).value for j in range(1, 10)], BT.PIPELINE_COLS)
    got = []
    for rr in range(2, BT.EXPORT_N + 2):
        row = [pl.cell(row=rr, column=j).value for j in range(1, 10)]
        if all(x in (None, "") for x in row):
            continue
        row[0] = as_date(row[0])
        row = [("" if x is None else x) for x in row]
        got.append(tuple(row))
    exp = expected_events()
    check("pipeline_log event count", len(got), len(exp))
    mism = [(i, g, e) for i, (g, e) in enumerate(zip(got, exp)) if tuple(g) != tuple(e)]
    check("pipeline_log rows identical to independent computation", len(mism), 0)
    for i, g, e in mism[:5]:
        say(f"   row {i}: got {g}\n          want {e}")
    dates = [g[0] for g in got]
    check("pipeline_log in date order", dates == sorted(dates), True)
    check("pipeline_log has no outreach opt_out rows (roster exits only)", sum(1 for g in got if g[4] == "opt_out"), 0)
    # data checks block
    chk = lambda label: (v(f"E{b.sc['chk_' + label]}"), v(f"F{b.sc['chk_' + label]}"))
    check("check: office sync issues", chk("Office_Log rows with a sync issue"), (3, "FIX"))
    check("check: brand sync issues", chk("Brand_Log rows with a sync issue"), (1, "FIX"))
    check("check: Clay office issues", chk("Clay office rows with an issue"), (2, "FIX"))
    check("check: Clay brand issues", chk("Clay brand rows with an issue"), (1, "FIX"))
    check("check: missing Clay columns", chk("Clay columns missing from a paste"), (0, "OK"))
    check("check: clay paste age", chk("Days since the Clay offices paste (as of)"), (0, "OK"))
    n_over = sum(1 for r in S.OFFICE_LOG + S.BRAND_LOG if r["call_date"] <= S.AS_OF and r["note_minutes"] > 10)
    check("check: notes over ten minutes", chk("Notes over the ten-minute target (as of)")[0], n_over)
    med = statistics.median([r["note_minutes"] for r in S.OFFICE_LOG + S.BRAND_LOG if r["call_date"] <= S.AS_OF])
    check("check: median minutes per note", chk("Median minutes per note (as of)")[0], med)
    check("check: yes missing owner or window", chk("Offices that said Y but owner or window is missing")[0],
          sum(1 for r in S.OFFICE_LOG if r["yes_in_principle"] == "Y" and not (r["pantry_owner_named"] == "Y" and r["receiving_window"].strip())))
    check("check: SAMPLE rows flagged", chk("SAMPLE rows in this file")[1], "SAMPLE")
    return wb, recalced


def test_sample_ignored(b):
    """Same SAMPLE file with include_sample = N: every count must drop to zero."""
    src = os.path.join(ROOT, "tracking", "conversation-tracker-SAMPLE.xlsx")
    tmp = tempfile.mkdtemp(prefix="ddtr_n_")
    p = os.path.join(tmp, "sample_ignored.xlsx")
    wb0 = openpyxl.load_workbook(src)
    wb0["Config"]["B19"] = "N"
    wb0.save(p)
    wb, _ = recalc(p)
    sc = wb["Scorecard"]
    check("include_sample=N: error cells", len(errors(wb)), 0)
    for k in ("o_conv", "o_yes", "b_conv", "b_yes", "office_first", "brand_first", "g1_signed", "g1_paid", "slot_brands_paid", "slot_offices_yes"):
        check(f"include_sample=N: {k} as of", sc[f"E{b.sc[k]}"].value, 0)
    check("include_sample=N: median reads none yet", sc[f"E{b.sc['o_bp_med']}"].value, "none yet")
    pl = wb["pipeline_log"]
    n = sum(1 for rr in range(2, 50) if pl.cell(row=rr, column=1).value not in (None, ""))
    check("include_sample=N: pipeline_log empty", n, 0)
    check("include_sample=N: banner says ignored", "(SAMPLE rows are ignored)" in (sc["A1"].value or ""), True)
    check("include_sample=N: sync flags hidden", wb["Office_Log"][f"{b.C_office.L('calc_sync_issue')}2"].value in (None, ""), True)


def test_blank():
    path = os.path.join(ROOT, "tracking", "conversation-tracker.xlsx")
    b = BT.Book(False)   # only for row positions
    wb, _ = recalc(path)
    errs = errors(wb)
    check("blank workbook: error cells after recalculation", len(errs), 0)
    for e in errs[:20]:
        say("   " + e)
    sc = wb["Scorecard"]
    check("blank workbook: no SAMPLE banner", sc["A1"].value in (None, ""), True)
    check("blank workbook: include_sample", wb["Config"]["B19"].value, "N")
    return wb


def test_f_columns():
    """Every column operations (F) reads from signed_offices.csv and paid_brands.csv is in the files (parsed, not imported)."""
    import ast
    f = os.path.join(os.path.dirname(ROOT), "campaign-ops", "tools", "trackerdef.py")
    if not os.path.exists(f):
        say("skip F column check: campaign-ops/tools/trackerdef.py not found")
        return
    tree = ast.parse(open(f, encoding="utf-8").read())
    lists = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.List) and isinstance(node.targets[0], ast.Name):
            try:
                lists[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                pass
    import csv as _csv
    so = next(_csv.reader(open(os.path.join(ROOT, "handoff", "signed_offices.csv"), encoding="utf-8")))
    pb = next(_csv.reader(open(os.path.join(ROOT, "handoff", "paid_brands.csv"), encoding="utf-8")))
    need_so = lists.get("OFFICE_INTAKE_COLS", []) + lists.get("SIGNED_OFFICES_EXTRA", []) + lists.get("SIGNED_OFFICES_REQUESTED", [])
    need_pb = lists.get("BRAND_INTAKE_COLS", []) + lists.get("PAID_BRANDS_EXTRA", []) + lists.get("PAID_BRANDS_REQUESTED", [])
    check("F reads from signed_offices.csv: columns missing", [c for c in need_so if c not in so], [])
    check("F reads from paid_brands.csv: columns missing", [c for c in need_pb if c not in pb], [])
    check("signed_offices.csv starts with the office_intake columns in order", so[:21], BT.OFFICE_INTAKE)
    check("paid_brands.csv starts with the brand_intake columns in order", pb[:27], BT.BRAND_INTAKE)


def main():
    b = BT.build(True, os.path.join(ROOT, "tracking", "conversation-tracker-SAMPLE.xlsx"))
    BT.build(False, os.path.join(ROOT, "tracking", "conversation-tracker.xlsx"))
    say(f"tracker test run {dt.datetime.now().isoformat(timespec='seconds')}")
    say("== SAMPLE workbook, include_sample = Y")
    wb, recalced = test_sample(b)
    keep = os.path.join(ROOT, "_work", "partB", "recalc-SAMPLE.xlsx")
    shutil.copy(recalced, keep)
    say("== SAMPLE workbook, include_sample = N")
    test_sample_ignored(b)
    say("== blank workbook")
    test_blank()
    say("== operations (F) columns")
    test_f_columns()
    say(f"RESULT: {len(FAILS)} failing of {sum(1 for l in LOG if l.startswith(('ok  ', 'FAIL')))} checks")
    with open(os.path.join(ROOT, "_work", "partB", "test_log.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
