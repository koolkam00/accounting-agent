#!/usr/bin/env python3
"""Rows a real founder will type that the SAMPLE stories never do: the tracker must show a check, not an error.

  python3 tests/test_edge_rows.py

Starts from campaign zero's full SAMPLE rows and adds the awkward cases:
  - the drop moved to a Friday (the date is refused, so every derived date is blank);
  - a second drop with no date yet, and a campaign on it;
  - a campaign whose drop_id is a typo;
  - an approval for an office that is not on the offices tab;
  - a stop and a count for a drop that does not exist.
Recalculates with LibreOffice (which, like Google Sheets, turns arithmetic on an empty text result into #VALUE!)
and requires 0 formula errors and the expected check texts.
"""
import copy
import datetime as dt
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import dryrun as DR  # noqa: E402
import scenarios as S  # noqa: E402


def main():
    scn = S.zero()
    rows = scn["rows"]
    friday = dt.date(2027, 1, 15)
    for r in rows["drops"]:
        if r["drop_id"] == scn["drop_id"]:
            r["drop_date"] = friday
    d2 = copy.deepcopy(rows["drops"][0])
    d2.update({"drop_id": "SAMPLE-DRP-077", "drop_date": None, "status": "planned"})
    rows["drops"].append(d2)
    c0 = rows["campaigns"][0]
    c_nodate = copy.deepcopy(c0)
    c_nodate.update({"campaign_id": "SAMPLE-CMP-077", "drop_id": "SAMPLE-DRP-077"})
    c_typo = copy.deepcopy(c0)
    c_typo.update({"campaign_id": "SAMPLE-CMP-078", "drop_id": "SAMPLE-DRP-0O1"})
    rows["campaigns"] += [c_nodate, c_typo]
    a0 = copy.deepcopy(rows["approvals"][0])
    a0.update({"campaign_id": "SAMPLE-CMP-077", "office_id": "SAMPLE-O-999"})
    rows["approvals"].append(a0)
    if rows.get("stops"):
        s0 = copy.deepcopy(rows["stops"][0])
        s0.update({"drop_id": "SAMPLE-DRP-078"})
        rows["stops"].append(s0)
    if rows.get("counts"):
        k0 = copy.deepcopy(rows["counts"][0])
        k0.update({"campaign_id": "SAMPLE-CMP-078"})
        rows["counts"].append(k0)
    # More rows with a typo or a blank where a key belongs: each must give a check, never an error.
    add = {
        "inventory": dict(rows["inventory"][0], campaign_id="SAMPLE-CMP-0X1", qty=12),
        "photos": dict(rows["photos"][0], photo_id="SAMPLE-PH-9999", office_id="SAMPLE-O-998", taken_date=None),
        "hours": dict(rows["hours"][0], activity="selling", hours=1, drop_id="SAMPLE-DRP-0X1"),
        "costs": dict(rows["costs"][0], drop_id="SAMPLE-DRP-0X1", amount_usd=None),
        "invoices": dict(rows["invoices"][0], invoice_id="SAMPLE-INV-099", campaign_id="", paid_date=None, paid_amount_usd=None),
        "scans": dict(rows["scans"][0], slug="SAMPLE-c999-o001-q"),
        "redemptions": dict(rows["redemptions"][0], campaign_id="SAMPLE-CMP-077"),
        "issues": dict(rows["issues"][0], issue_id="SAMPLE-ISS-099", drop_id="SAMPLE-DRP-077", campaign_id="", closed_date=None),
        "offices": {"office_id": "SAMPLE-O-950"},
    }
    for tab, row in add.items():
        rows[tab].append({k: v for k, v in row.items() if not k.startswith("_")})
    want_tab = {"inventory": "campaign_id not on campaigns", "photos": "office not on this campaign (approvals tab)", "hours": "seven keys", "costs": "drop_id not on drops", "scans": "slug not in links",
                "invoices": "campaign_id missing or not on campaigns"}
    day = dt.date(2027, 2, 20)
    tmp = tempfile.mkdtemp(prefix="ops_edge_")
    p = DR.build_snapshot(scn, day, os.path.join(tmp, "in.xlsx"))
    tr, errs, n = DR.recalc_and_read(p, os.path.join(tmp, "out.xlsx"))
    fails = ["formula error " + e for e in errs] if n else []
    camp = {r["campaign_id"]: c for r, c in zip(tr.rows["campaigns"], tr.cached["campaigns"])}
    drops = {r["drop_id"]: c for r, c in zip(tr.rows["drops"], tr.cached["drops"])}
    want = {"SAMPLE-CMP-001": "drop date missing or refused", "SAMPLE-CMP-077": "drop date missing or refused",
            "SAMPLE-CMP-078": "drop_id not on drops"}
    for cid, text in want.items():
        got = str((camp.get(cid) or {}).get("checks") or "")
        if text not in got:
            fails.append("%s checks %r lacks %r" % (cid, got[:200], text))
    for did in (scn["drop_id"], "SAMPLE-DRP-077"):
        c = drops.get(did) or {}
        if did == scn["drop_id"] and not str(c.get("date_check") or "").startswith("REFUSED"):
            fails.append("%s date_check is %r, expected a refusal" % (did, c.get("date_check")))
        if c.get("t_plus_7") not in (None, ""):
            fails.append("%s still has a T+7 date %r" % (did, c.get("t_plus_7")))
    appr = [c for r, c in zip(tr.rows["approvals"], tr.cached["approvals"]) if r["office_id"] == "SAMPLE-O-999"]
    if not appr or "office_id not on offices" not in str(appr[0].get("checks") or ""):
        fails.append("approval for an unknown office shows no check: %r" % (appr[0].get("checks") if appr else None))
    new_office = [c for r, c in zip(tr.rows["offices"], tr.cached["offices"]) if r["office_id"] == "SAMPLE-O-950"]
    if not new_office or "not on in_signed_offices" not in str(new_office[0].get("size_check") or ""):
        fails.append("office missing from the outreach file shows no flag: %r" % (new_office[0].get("size_check") if new_office else None))
    for tab, text in want_tab.items():
        got = [str(c.get("checks") or "") for c in tr.cached[tab]]
        if not any(text in g for g in got):
            fails.append("%s: no row check mentions %r" % (tab, text))
    for f in fails:
        print("FAIL " + f)
    print("%d formula errors; %d campaigns, %d drops checked" % (n, len(want), 2))
    print("PASS test_edge_rows" if not fails else "FAIL test_edge_rows")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
