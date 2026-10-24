#!/usr/bin/env python3
"""Per-campaign actuals for the financial model, in exactly the layout financial-model/HANDOFF.md
section 2 asks for (it wins over CONTRACTS 6.5): three files, these columns, this order, nothing else.

  python3 tools/export_actuals.py TRACKER.xlsx [OUT_DIR]      # default OUT_DIR: exports/
  python3 tools/export_actuals.py TRACKER.xlsx OUT_DIR --pipeline   # also brand payment events for E

Writes campaign_actuals.csv, drop_costs.csv, hours_log.csv (and pipeline_paid_events.csv with
--pipeline: CONTRACTS 6.6 columns, event = paid, one row per payment received).
Dates YYYY-MM-DD, numbers plain, blank where not yet known. Every value is recomputed from the
tracker's rows (tools/tracker.py); nothing is typed. SAMPLE rows are refused into exports/.
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
            "offices": num(lad["offices_approved"]), "units_received": num(lad["units_received"]),
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


def paid_events(tr):
    out = []
    for r in tr.rows["invoices"]:
        if not TR._d(r.get("paid_date")) or TR._n(r.get("paid_amount_usd")) <= 0:
            continue
        c = tr.campaigns.get(TR._s(r["campaign_id"]))
        if not c:
            continue
        b = tr.brand(TR._s(c["brand_id"]))
        e_row = tr._paste("in_paid_brands", "brand_id").get(TR._s(c["brand_id"]), {})
        org = TR._s(e_row.get("clay_row_id")) or TR._s(c["brand_id"])
        out.append({"date": day(r["paid_date"]), "side": "brand", "org_id": org, "org_name": TR._s(b.get("brand_name")),
                    "event": "paid", "value_number": num(TR._n(r["paid_amount_usd"])), "value_text": "",
                    "controls_budget": "Y", "notes": "%s %s %s" % (TR._s(r["invoice_id"]), TR._s(c["brand_id"]), TR._s(r["invoice_type"]))})
    return out


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
    tr = TR.Tracker(argv[1])
    out = argv[2] if len(argv) > 2 and not argv[2].startswith("--") else os.path.join(common.ROOT, "exports")
    os.makedirs(out, exist_ok=True)
    cr, dr, hr = campaign_rows(tr), drop_rows(tr), hours_rows(tr)
    if os.path.abspath(out) == os.path.abspath(os.path.join(common.ROOT, "exports")):
        if any(common.is_sample(*r.values()) for r in cr + dr + hr):
            raise SystemExit("REFUSED: SAMPLE rows never go into exports/. Write them elsewhere (dry-run/).")
    write(os.path.join(out, "campaign_actuals.csv"), T.H_CAMPAIGN_ACTUALS, cr)
    write(os.path.join(out, "drop_costs.csv"), T.H_DROP_COSTS, dr)
    write(os.path.join(out, "hours_log.csv"), T.H_HOURS, hr)
    if "--pipeline" in argv:
        write(os.path.join(out, "pipeline_paid_events.csv"),
              ["date", "side", "org_id", "org_name", "event", "value_number", "value_text", "controls_budget", "notes"], paid_events(tr))
    print("exports: %d campaigns, %d drops, %d hour rows -> %s" % (len(cr), len(dr), len(hr), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
