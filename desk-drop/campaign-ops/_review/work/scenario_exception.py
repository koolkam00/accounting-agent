# ---------------------------------------------------------------- REVIEWER ADDITION (campaign-ops/_review, round 1)
# A third SAMPLE campaign with two exceptions: a short shipment and one office declining at the door.
# Written by the independent reviewer in the sandbox copy only. Every ID and text starts with SAMPLE.
BRANDS["SAMPLE-BR-006"] = dict(name="SAMPLE Saltmarsh", cat="chips-crisps", sku="SAMPLE Salt and Vinegar Potato Chips, 1 oz bags",
                               city="SAMPLE Montauk, NY", site="https://example.com/saltmarsh", via="website", submitted="2027-01-11T09:40:00-05:00")


def exception():
    """SAMPLE Saltmarsh, standard, 10 offices, courier, drop Tue 2027-02-23 (SAMPLE-DRP-003).
    Short shipment (480 of 567: every office 5 fewer) and SAMPLE-O-006 declines at the door on T.
    The founder follows sop/SOP.md section 4 literally: stops outcome declined; inventory correction back to reserve;
    not placed by T+1 -> credit note taken off the balance."""
    import opscal
    import tracker as TR
    st = standard()
    T = d("2027-02-23")
    s = opscal.sop_dates(T)
    O10 = [o[0] for o in OFFICES]
    rows = copy_rows(st["rows"])
    bweb, bform, brands = brand_rows(["SAMPLE-BR-006"])
    rows["brand_intake"] += bweb
    rows["brand_form"] += bform
    rows["brands"] += brands
    rows["drops"].append({"_on": d("2027-01-20"), "drop_id": "SAMPLE-DRP-003", "drop_date": T, "delivery_model": "courier", "status": "confirmed",
                          "receiving_location": "SAMPLE receiving address (founder's home, sealed cases)",
                          "courier_or_van": "SAMPLE Example Courier, booking SAMPLE-BK-0223, pickup 7:45 am", "backup_person": "SAMPLE backup (briefed 2027-02-19)",
                          "notes": "SAMPLE second standard run (reviewer exception run)"})
    cid, bid, signed_on, paid_on = "SAMPLE-CMP-006", "SAMPLE-BR-006", d("2027-01-25"), d("2027-01-28")
    rows["campaigns"].append(dict(_on=signed_on, campaign_id=cid, drop_id="SAMPLE-DRP-003", brand_id=bid, tier="standard", offices_contracted=10,
                                  agreement_signed_date=signed_on, agreement_version="0.8", product_sku=BRANDS[bid]["sku"],
                                  coi_received_date=paid_on, allergen_sheet_received_date=paid_on, logo_received_date=paid_on,
                                  card_proof_sent_date=s["receive"], unused_product_election="release", newsletter_option="N",
                                  card_sentences="SAMPLE Potato chips cut and fried near Montauk by a former fishing family. Sharp vinegar, sea salt, nothing else.",
                                  allergen_source="ingredient_list", allergen_line_verbatim="SAMPLE Ingredients: potatoes, sunflower oil, vinegar powder, sea salt.",
                                  may_contain_verbatim="", retailer_line="SAMPLE Example Market, 1 Example Street", discount_code="SAMPLESALT10", code_site="example.com",
                                  survey_form_url="https://docs.google.com/forms/d/e/%s-FORM/viewform" % cid,
                                  survey_prefill_template="https://docs.google.com/forms/d/e/%s-FORM/viewform?usp=pp_url&entry.1000001=CARDCODE" % cid,
                                  _fields_on={"survey_form_url": opscal.add_bd(T, -4), "survey_prefill_template": opscal.add_bd(T, -4)},
                                  _fields_history={"ship_email_sent_date": [(paid_on, paid_on)], "ship_email_units": [(paid_on, 567)]}))
    rows["invoices"] += [
        {"_on": signed_on, "invoice_id": "SAMPLE-INV-020", "campaign_id": cid, "invoice_type": "standard_deposit", "issued_date": signed_on, "amount_usd": 750,
         "sales_tax_usd": 0, "sent_to": "SAMPLE-ap-006@example.com", "paid_date": paid_on, "paid_amount_usd": 750, "method": "bank_transfer",
         "bank_reference": "SAMPLE-ACH-6020", "processing_fee_usd": 0, "_fields_on": {k: paid_on for k in ("paid_date", "paid_amount_usd", "method", "bank_reference")}},
        {"_on": s["placement_confirm"], "invoice_id": "SAMPLE-INV-021", "campaign_id": cid, "invoice_type": "standard_balance", "issued_date": s["placement_confirm"],
         "amount_usd": 750, "sales_tax_usd": 0, "sent_to": "SAMPLE-ap-006@example.com", "paid_date": d("2027-02-26"), "paid_amount_usd": 600,
         "method": "bank_transfer", "bank_reference": "SAMPLE-ACH-6021", "processing_fee_usd": 0,
         "_fields_on": {k: d("2027-02-26") for k in ("paid_date", "paid_amount_usd", "method", "bank_reference")}},
        {"_on": s["placement_confirm"], "invoice_id": "SAMPLE-INV-022", "campaign_id": cid, "invoice_type": "credit_note", "issued_date": s["placement_confirm"],
         "amount_usd": -150, "sales_tax_usd": 0, "sent_to": "SAMPLE-ap-006@example.com",
         "note": "SAMPLE office SAMPLE-O-006 declined at the door and was not placed by T+1: taken off the balance, brand agreement section 8"},
    ]
    base_units = {"SAMPLE-O-001": 40, "SAMPLE-O-002": 40, "SAMPLE-O-003": 50, "SAMPLE-O-004": 50, "SAMPLE-O-005": 70,
                  "SAMPLE-O-006": 45, "SAMPLE-O-007": 60, "SAMPLE-O-008": 45, "SAMPLE-O-009": 75, "SAMPLE-O-010": 40}
    short_on = d("2027-02-12")
    ov = {o: base_units[o] - 5 for o in O10}
    for o in O10:
        rows["approvals"] += _approvals(cid, [o], signed_on, {o: ("yes", d("2027-01-27"))}, None, ov, override_on=short_on)
    order = ["SAMPLE-O-001", "SAMPLE-O-006", "SAMPLE-O-010", "SAMPLE-O-003", "SAMPLE-O-002", "SAMPLE-O-007", "SAMPLE-O-008",
             "SAMPLE-O-004", "SAMPLE-O-005", "SAMPLE-O-009"]
    times = ["08:05", "08:22", "08:40", "09:02", "09:20", "09:38", "09:58", "10:18", "10:40", "11:02"]
    for i, (oid, t) in enumerate(zip(order, times), start=1):
        h, m = map(int, t.split(":"))
        dec = oid == "SAMPLE-O-006"
        rows["stops"].append({"_on": s["kit_print"], "drop_id": "SAMPLE-DRP-003", "office_id": oid, "route_order": i, "planned_time": tm(h, m),
                              "slack_post_sent_date": s["kit_print"], "confirm_text_sent_date": s["confirm"], "arrival_time": tm(h, m + 1),
                              "departure_time": tm(h + (m + 12) // 60, (m + 12) % 60), "handed_to_role": "pantry owner",
                              "outcome": "declined" if dec else "handed_to_owner",
                              "notes": "SAMPLE owner declined at the door: office pausing snacks this month; courier brought the case back" if dec else "",
                              "office_debrief_date": d("2027-03-04"), "office_would_do_again": "maybe" if dec else "yes",
                              "_fields_on": {k: T for k in ("arrival_time", "departure_time", "handed_to_role", "outcome", "notes")} | {"office_debrief_date": d("2027-03-04"), "office_would_do_again": d("2027-03-04")}})
    inv, cnt, ph = [], [], []
    inv.append({"_on": short_on, "date": short_on, "time": tm(14, 0), "campaign_id": cid, "movement": "received", "qty": 480, "lot": "SAMPLE-SM-0201",
                "best_by": d("2027-08-31"), "count_source": "founder_count", "note": "SAMPLE 20 cases of 24; 567 were due"})
    pid = [500]

    def photo(oid, typ, day, t):
        pid[0] += 1
        p = "SAMPLE-PH-%04d" % pid[0]
        ph.append({"_on": day, "photo_id": p, "campaign_id": cid, "office_id": oid, "photo_type": typ, "taken_date": day, "taken_time": t,
                   "source": "office", "file_name": "%s_%s_%s_%s.jpg" % (cid, oid, typ, day.isoformat()), "received_date": day,
                   "card_visible": "Y", "no_people_or_screens": "Y"})
        return p
    rnd = random.Random(66)
    tops = {"SAMPLE-O-005": 6, "SAMPLE-O-009": 6}
    rem5 = {}
    for oid in O10:
        u = ov[oid]
        stop = next(x for x in rows["stops"] if x["drop_id"] == "SAMPLE-DRP-003" and x["office_id"] == oid)
        if oid == "SAMPLE-O-006":
            # SOP section 4, "Office declines at the door": stops outcome declined; inventory correction back to reserve.
            inv.append({"_on": T, "date": T, "time": tm(8, 30), "campaign_id": cid, "office_id": oid, "movement": "correction", "bucket": "reserve",
                        "qty": u, "count_source": "courier_count", "note": "SAMPLE case taken back after the office declined at the door"})
            continue
        inv.append({"_on": T, "date": T, "time": stop["arrival_time"], "campaign_id": cid, "office_id": oid, "movement": "delivered", "qty": u, "count_source": "courier_count"})
        p = photo(oid, "placement", T, tm(13, 0))
        cnt.append({"_on": T, "date": T, "time": tm(13, 0), "campaign_id": cid, "office_id": oid, "count_type": "placed", "units": u, "source": "photo", "photo_id": p})
        r3 = int(u * rnd.uniform(0.2, 0.5))
        cnt.append({"_on": s["check_day3"], "date": s["check_day3"], "time": tm(11, 0), "campaign_id": cid, "office_id": oid, "count_type": "remaining_day3", "units": r3, "source": "owner_report"})
        if oid in tops:
            inv.append({"_on": s["check_day3"], "date": s["check_day3"], "time": tm(13, 0), "campaign_id": cid, "office_id": oid, "movement": "topped_up", "qty": tops[oid], "count_source": "founder_count"})
        r5 = max(0, int(r3 * rnd.uniform(0.1, 0.4)))
        rem5[oid] = r5
        p2 = photo(oid, "later", s["close"], tm(15, 0))
        cnt.append({"_on": s["close"], "date": s["close"], "time": tm(16, 0), "campaign_id": cid, "office_id": oid, "count_type": "remaining_day5", "units": r5, "source": "photo", "photo_id": p2})
    # Physical reserve at close: 480 received - delivered - top-ups. The founder counts it and releases it (brand chose release).
    delivered = sum(ov[o] for o in O10 if o != "SAMPLE-O-006")
    physical_left = 480 - delivered - sum(tops.values())
    inv.append({"_on": s["close"], "date": s["close"], "time": tm(17, 0), "campaign_id": cid, "office_id": "SAMPLE-O-005", "movement": "released_to_office",
                "bucket": "reserve", "qty": physical_left, "count_source": "founder_count", "note": "SAMPLE brand chose release: counted reserve to the largest office"})
    rows["inventory"] += inv
    rows["counts"] += cnt
    rows["photos"] += ph
    plan = {o: 5 + (_h((cid, o)) % 5) for o in O10 if o != "SAMPLE-O-006"}
    rr = survey(cid, plan, T, s["close"], 606)
    ensure_comments(rr, T, s["close"], ["SAMPLE Really sharp vinegar, loved it.", "SAMPLE Too salty for an afternoon snack.", "SAMPLE Is this sold at the market on the corner?"])
    for r in rr:
        r.append(r[0].date())
    resp = dict(st["responses"])
    resp[cid] = ("SAMPLE Saltmarsh", rr)
    scans = []
    for oid in O10:
        for kind in ("q", "p"):
            close = 1 if oid == "SAMPLE-O-006" else 4 + (_h((cid, oid, kind)) % 10)
            sl = TR.slug(cid, oid, kind)
            for day, typ, v in ((s["confirm"], "baseline", 1), (s["check_day3"], "mid", max(1, close // 2)), (s["close"], "close", close)):
                scans.append({"_on": day, "read_date": day, "read_time": tm(17, 30), "slug": sl, "reading_type": typ, "clicks_to_date": v})
    rows["scans"] += scans
    rows["redemptions"] += [
        {"_on": s["report_due"], "campaign_id": cid, "as_of_date": s["report_due"] - dt.timedelta(days=1), "redemptions_to_date": 7,
         "reported_date": s["report_due"] - dt.timedelta(days=1), "reported_by_role": "SAMPLE brand co-founder"},
        {"_on": T + dt.timedelta(days=30), "campaign_id": cid, "as_of_date": T + dt.timedelta(days=30), "redemptions_to_date": 13,
         "reported_date": T + dt.timedelta(days=30), "reported_by_role": "SAMPLE brand co-founder"}]
    rows["issues"] += [
        {"_on": short_on, "issue_id": "SAMPLE-ISS-020", "date": short_on, "time": tm(14, 30), "drop_id": "SAMPLE-DRP-003", "campaign_id": cid,
         "issue_type": "short_shipment", "what_happened": "SAMPLE 480 units arrived; 567 were due (515 plus reserve).",
         "action_taken": "SAMPLE each office's units reduced by 5 (465), reserve 15; brand told the same day.", "brand_told_date": short_on, "closed_date": short_on},
        {"_on": T, "issue_id": "SAMPLE-ISS-021", "date": T, "time": tm(8, 23), "drop_id": "SAMPLE-DRP-003", "campaign_id": cid, "office_id": "SAMPLE-O-006",
         "issue_type": "declined_at_door", "what_happened": "SAMPLE owner declined at the door: the office is pausing snacks this month.",
         "action_taken": "SAMPLE courier took the case back; units back to reserve; $150 taken off the balance.", "office_told_date": T,
         "brand_told_date": s["placement_confirm"], "closed_date": s["placement_confirm"]},
    ]
    H = []

    def hrs(day, act, h, c="", note=""):
        H.append({"_on": day, "date": day, "drop_id": "SAMPLE-DRP-003", "campaign_id": c, "activity": act, "hours": h, "note": note})
    for k in range(3):
        hrs(opscal.add_bd(signed_on, -3 * k), "brand_sales", 2.0, cid, "SAMPLE calls, proposal, agreement")
    hrs(d("2027-01-26"), "office_coordination", 1.5, note="SAMPLE approvals")
    hrs(short_on, "receiving_kitting", 1.5, note="SAMPLE receive, count, short shipment email")
    hrs(s["confirm"], "receiving_kitting", 1.5, note="SAMPLE pack nine cases plus one")
    hrs(T, "drop_day", 4.0, note="SAMPLE courier route; founder on call")
    hrs(s["check_day3"], "checks_pickup", 1.5); hrs(s["close"], "checks_pickup", 1.5)
    hrs(s["report_due"], "reporting_debriefs", 1.5, cid, "SAMPLE report"); hrs(s["debrief"], "reporting_debriefs", 0.5, cid, "SAMPLE debrief")
    hrs(s["placement_confirm"], "admin_invoicing", 1.0, note="SAMPLE balance and credit note")
    rows["hours"] += H
    rows["costs"] += [
        {"_on": s["kit_print"], "date": s["kit_print"], "drop_id": "SAMPLE-DRP-003", "campaign_id": cid, "cost_type": "kit", "amount_usd": 80, "vendor": "SAMPLE copy shop"},
        {"_on": T, "date": T, "drop_id": "SAMPLE-DRP-003", "cost_type": "transport", "amount_usd": 300, "vendor": "SAMPLE Example Courier", "note": "SAMPLE 10 stops at $30 (one declined)"},
    ]
    for r in rows["campaigns"]:
        if r["campaign_id"] != cid:
            continue
        r.update(comment_1="SAMPLE Really sharp vinegar, loved it.", comment_2="SAMPLE Too salty for an afternoon snack.",
                 comment_3="SAMPLE Is this sold at the market on the corner?",
                 learned="SAMPLE Shipped 87 short; every office got 5 fewer.\nSAMPLE One office declined at the door; it was not billed.\nSAMPLE Vinegar strength split the comments.",
                 recommendation="SAMPLE Renew into the nine offices that took it; ship the full count.",
                 report_delivered_date=s["report_due"], debrief_date=s["debrief"], brand_would_buy_again="yes", renewed="pending")
        f = r["_fields_on"]
        for k in ("comment_1", "comment_2", "comment_3", "learned", "recommendation"):
            f[k] = opscal.add_bd(T, 6)
        f.update(report_delivered_date=s["report_due"], debrief_date=s["debrief"], brand_would_buy_again=s["debrief"], renewed=s["debrief"])
    return {"name": "exception", "T": T, "drop_id": "SAMPLE-DRP-003", "rows": rows, "responses": resp,
            "campaigns": [cid], "offices": O10, "delivery_model": "courier"}
