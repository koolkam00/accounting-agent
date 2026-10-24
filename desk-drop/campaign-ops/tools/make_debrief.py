#!/usr/bin/env python3
"""Debrief note sheets, filled from the tracker so you walk in with the numbers.

  python3 tools/make_debrief.py TRACKER.xlsx DROP_ID OUT_DIR

Writes OUT_DIR/debrief-brand-<campaign>.md for each brand and debrief-office-<office>.md for each office.
Templates: templates/debrief-brand.md, templates/debrief-office.md, and templates/debrief-office-declined.md for an
office that turned every brand away at the door (it is asked why, never how the product landed).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402
import make_messages as MM  # noqa: E402
import make_report as MR  # noqa: E402
import opscal  # noqa: E402
import tracker as TR  # noqa: E402


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 1
    tr = TR.Tracker(argv[1])
    common.require_same_name(tr)
    did, out = argv[2], argv[3]
    T = tr.drop_date(did)
    s = opscal.sop_dates(T)
    tb = open(os.path.join(common.ROOT, "templates", "debrief-brand.md"), encoding="utf-8").read()
    to = open(os.path.join(common.ROOT, "templates", "debrief-office.md"), encoding="utf-8").read()
    tdec = open(os.path.join(common.ROOT, "templates", "debrief-office-declined.md"), encoding="utf-8").read()
    camps = [cid for cid, c in tr.campaigns.items() if TR._s(c["drop_id"]) == did]
    n = 0
    for cid in camps:
        lad = tr.ladder(cid)
        c = lad["campaign"]
        b = tr.brand(TR._s(c["brand_id"]))
        founding_first = TR._s(c.get("tier")) == "founding" and TR._s(c.get("founding_lock")) != "Y"
        ctx = {"brand_name": c["brand_name"], "campaign_id": cid, "debrief_due": common.fmt_date(s["debrief"]),
               "brand_contact_name": TR._s(b.get("contact_name")), "brand_contact_title": TR._s(b.get("contact_title")),
               "founder_name": TR._s(tr.config.get("founder_name")),
               "report_date": common.fmt_date(TR._d(c.get("report_delivered_date")) or s["report_due"]),
               "delivered": int(lad["units_delivered"]), "placed": int(lad["units_placed"]), "placed_1bd": int(lad["units_placed_within_1bd"]),
               "depleted": "not counted" if lad["units_depleted_day5"] is None else int(lad["units_depleted_day5"]),
               "responses": lad["survey_responses"], "scans": int(lad["qr_scans"]),
               "redemptions": "none reported yet" if lad["code_redemptions_to_date"] is None else int(lad["code_redemptions_to_date"]),
               "red_as_of": common.fmt_date(lad["code_redemptions_as_of"]) or "-",
               "renewal_hint": "the next drop with offices that did best (see the roster), or new offices so they reach new people",
               "redemption_check": common.fmt_date(s["redemption_check"]), "discount_code": TR._s(c.get("discount_code")) or "(no code)",
               "roster_note": MR.roster_note(lad) or "Every office that approved the brand took it.",
               "testimonial_line": ("Founding brand: the short written statement is due by %s (brand agreement section 3), only if we delivered everything in section 1." % common.fmt_date(s["debrief"] + __import__("datetime").timedelta(days=30))) if founding_first else "No testimonial term for this tier."}
        common.write(os.path.join(out, "debrief-brand-%s.md" % cid), MM.fill(tb, ctx))
        n += 1
    stops = {TR._s(x["office_id"]): x for x in tr.rows["stops"] if TR._s(x["drop_id"]) == did}
    for oid, st in stops.items():
        o = tr.office(oid)
        parts, away = [], []
        for cid in camps:
            lad = tr.ladder(cid)
            row = next((x for x in lad["offices"] if x["office_id"] == oid and x["approved"] == "Y"), None)
            if row and row["on_drop"] == "Y":
                parts.append("%s: %d answers, %d tried, would buy yes %d" % (lad["campaign"]["brand_name"], row["survey_responses"], row["tried_yes"], row["buy_yes"]))
            elif row:
                away.append(lad["campaign"]["brand_name"])
                parts.append("%s: turned away at the door, not on the drop" % lad["campaign"]["brand_name"])
        if away and len(away) == len(parts):
            # Every brand at this stop was turned away at the door (R1-02): a short follow-up, not the usual debrief.
            ctx = {"company": TR._s(o.get("company")), "office_id": oid, "drop_id": did, "debrief_due": common.fmt_date(s["debrief"]),
                   "pantry_owner_name": TR._s(o.get("pantry_owner_name")), "founder_name": TR._s(tr.config.get("founder_name")),
                   "drop_date": common.fmt_date(T), "away_line": "turned away %s (stop outcome %s)" % (MM.and_list(away), TR._s(st.get("outcome"))),
                   "stop_note": TR._s(st.get("notes")) or "(no note on the stops tab)",
                   "categories": ", ".join(MM.CAT.get(k, k) for k in TR._s(o.get("categories_wanted")).split(";") if k),
                   "receiving_window": TR._s(o.get("receiving_window")),
                   "declines": sum(1 for x in tr.rows["stops"] if TR._s(x["office_id"]) == oid and TR._s(x.get("outcome")) == "declined")}
            common.write(os.path.join(out, "debrief-office-%s.md" % oid), MM.fill(tdec, ctx))
            n += 1
            continue
        # The budget question (plan appendix L, 4) at an office's first drop and then every third drop, about once a
        # quarter at a monthly pace, so a pantry owner is not asked the same thing every month (stage 2, R5).
        k = tr.office_drop_number(oid, T)
        if (k - 1) % 3 == 0:
            budget = ("4. If this were guaranteed twice a month with products your team voted on, is that something you would budget for? Roughly what range per month?\n"
                      "   - Answer, word for word: \n   - At intake they said: %s\n"
                      "   - A number only if they name one (E's pipeline_log, event budget_probe): ______" % (TR._s(o.get("budget_probe_verbatim")) or "(not recorded at intake)"))
        else:
            budget = ("4. (Not this time: this is their drop %d. The budget question is asked at drops 1, 4, 7 and so on; next at drop %d.)" % (k, k + 3 - (k - 1) % 3))
        ctx = {"company": TR._s(o.get("company")), "office_id": oid, "drop_id": did, "window_end": common.fmt_date(s["window_end"]),
               "budget_block": budget,
               "debrief_due": common.fmt_date(s["debrief"]), "pantry_owner_name": TR._s(o.get("pantry_owner_name")),
               "founder_name": TR._s(tr.config.get("founder_name")), "summary_line": "; ".join(parts) or "no brands placed",
               "receiving_window": TR._s(o.get("receiving_window")), "handed_to": TR._s(st.get("handed_to_role")) or "not logged",
               "categories": ", ".join(MM.CAT.get(k, k) for k in TR._s(o.get("categories_wanted")).split(";") if k),
               "budget_probe_verbatim": TR._s(o.get("budget_probe_verbatim")) or "(not recorded at intake)",
               "commitments_line": "Placement within one business day, two photos, one post of the survey link, five or more answers, this debrief: thank them for each one they kept; ask, never scold, about any they missed."}
        common.write(os.path.join(out, "debrief-office-%s.md" % oid), MM.fill(to, ctx))
        n += 1
    print("debrief notes: %d -> %s" % (n, out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
