#!/usr/bin/env python3
"""Per-campaign actuals for the financial model, in exactly the layout financial-model/HANDOFF.md
section 2 asks for (it wins over CONTRACTS 6.5): three files, these columns, this order, nothing else.

  python3 tools/export_actuals.py TRACKER.xlsx [OUT_DIR]      # default OUT_DIR: exports/

Writes campaign_actuals.csv, drop_costs.csv, hours_log.csv. Brand payment ("paid") events for the financial model's
Pipeline come only from the outreach workstream's pipeline_log.csv (payment_1/2 on its paid_brands row); the old
--pipeline output here was withdrawn in review round 1 (R1-06) because it counted every payment twice. The tracker's
dashboard compares E's payments with the invoices tab instead (brands, e_payment_check).
offices = offices on the drop: approved and not turned away at the door (R1-02).
Dates YYYY-MM-DD, numbers plain, blank where not yet known. Every value is recomputed from the
tracker's rows (tools/tracker.py); nothing is typed. SAMPLE rows are refused into the live exports/ files;
the dry runs write theirs to exports/SAMPLE-<scenario>/ (and dry-run/<scenario>/exports/).
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402
import trackerdef as T  # noqa: E402
import tracker as TR  # noqa: E402


def num(v):
    if v in (None, ""):
        return ""
    if isinstance(v, float):
        return ("%.2f" % v).rstrip("0").rstrip(".") if not v.is_integer() else str(int(v))
    return str(v)


def day(v):
    d = TR._d(v)
    return d.isoformat() if d else ""


def campaign_rows(tr):
    out = []
    for cid in tr.campaigns:
        lad = tr.ladder(cid)
        c = lad["campaign"]
        if lad["drop_date"] is None:
            continue
        out.append({
            "campaign_id": cid, "drop_id": TR._s(c["drop_id"]), "drop_date": day(lad["drop_date"]),
            "delivery_model": c["delivery_model"], "tier": TR._s(c["tier"]), "brand_id": TR._s(c["brand_id"]),
            "offices": num(lad["offices_on_drop"]), "units_received": num(lad["units_received"]),
            "units_delivered": num(lad["units_delivered"]), "units_placed": num(lad["units_placed"]),
            "units_placed_within_1bd": num(lad["units_placed_within_1bd"]), "units_topped_up": num(lad["units_topped_up"]),
            "units_depleted_day5": num(lad["units_depleted_day5"]), "survey_responses": num(lad["survey_responses"]),
            "survey_tried_yes": num(lad["survey_tried_yes"]), "qr_scans": num(lad["qr_scans"]),
            "code_redemptions_day30": num(lad["code_redemptions_day30"]), "revenue_usd": num(lad["revenue_usd"]),
            "invoice_paid_date": day(lad["invoice_paid_date"]), "processing_fee_usd": num(lad["processing_fee_usd"]),
            "report_delivered_date": day(c.get("report_delivered_date")),
            "brand_would_buy_again": TR._s(c.get("brand_would_buy_again")),
            "renewed": TR._s(c.get("renewed")) or "pending",
            "deposit_usd": num(lad["deposit_usd"]), "deposit_paid_date": day(lad["deposit_paid_date"]),
            "survey_responses_min_office": num(lad["survey_responses_min_office"]),
        })
    return out


def drop_rows(tr):
    out = []
    for did, r in tr.drops.items():
        dd = tr.drop_date(did)
        if dd is None:
            continue
        m = tr.drop_money(did)
        notes = TR._s(r.get("notes"))
        out.append({"drop_id": did, "drop_date": dd.isoformat(), "delivery_model": TR._s(r["delivery_model"]),
                    "offices": num(m["stops"]), "brands": num(len(m["campaigns"])), "kit_cost_usd": num(m["kit_cost_usd"]),
                    "transport_cost_usd": num(m["transport_cost_usd"]), "other_direct_cost_usd": num(m["other_direct_cost_usd"]),
                    "notes": notes})
    return out


def hours_rows(tr):
    return [{"date": day(r["date"]), "drop_id": TR._s(r["drop_id"]), "campaign_id": TR._s(r["campaign_id"]),
             "activity": TR._s(r["activity"]), "hours": num(TR._n(r["hours"])), "note": TR._s(r["note"])}
            for r in tr.rows["hours"] if TR._d(r["date"])]


def write(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    if "--pipeline" in argv:
        print("REFUSED: --pipeline was withdrawn (review round 1, R1-06). Brand payments reach the financial model once, through "
              "desk-drop-outreach/exports/pipeline_log.csv; the tracker's dashboard checks E's payments against the invoices tab.")
        return 1
    tr = TR.Tracker(argv[1])
    out = argv[2] if len(argv) > 2 and not argv[2].startswith("--") else os.path.join(common.ROOT, "exports")
    os.makedirs(out, exist_ok=True)
    cr, dr, hr = campaign_rows(tr), drop_rows(tr), hours_rows(tr)
    live = os.path.abspath(os.path.join(common.ROOT, "exports"))
    sample_rows = any(common.is_sample(*r.values()) for r in cr + dr + hr)
    if os.path.abspath(out) == live and sample_rows:
        raise SystemExit("REFUSED: SAMPLE rows never go into the live exports/ files. Write them to exports/SAMPLE-<name>/ or dry-run/.")
    if os.path.dirname(os.path.abspath(out)) == live and os.path.basename(out.rstrip("/")).startswith("SAMPLE") and not sample_rows and (cr or dr or hr):
        raise SystemExit("REFUSED: real rows never go into a SAMPLE folder. Write them to exports/.")
    write(os.path.join(out, "campaign_actuals.csv"), T.H_CAMPAIGN_ACTUALS, cr)
    write(os.path.join(out, "drop_costs.csv"), T.H_DROP_COSTS, dr)
    write(os.path.join(out, "hours_log.csv"), T.H_HOURS, hr)
    print("exports: %d campaigns, %d drops, %d hour rows -> %s" % (len(cr), len(dr), len(hr), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
