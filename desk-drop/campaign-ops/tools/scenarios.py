"""SAMPLE scenarios for the dry runs. Every ID and text starts with SAMPLE. Nothing here is a result.

Each row carries "_on": the day the founder would log it. dryrun.py replays the calendar day by
day, building the tracker with only the rows known by that day.

zero:      campaign zero, 2 founding brands x 5 offices, founder-delivered, drop Tue 2027-01-12.
standard:  first standard run, 3 brands x 10 offices, courier, drop Tue 2027-02-09 (zero's rows are
           kept, as the real tracker would keep them).
"""
import datetime as dt
import random

D = dt.date
tm = dt.time


def d(s):
    return D.fromisoformat(s)


def at(s, h, m):
    return dt.datetime.combine(d(s), tm(h, m))


# ---------------------------------------------------------------- offices (shared by both scenarios)
OFFICES = [
    # id, company, industry, headcount, receiving_type, window, coi, channel, cats, lat, lon, via
    ("SAMPLE-O-001", "SAMPLE Northpoint Software", "SAMPLE Software", 52, "walk-up", "8 to 10 am", "no", "slack",
     "chips-crisps;bars;sparkling-soda;fruit-snacks", 40.7398, -73.9893, "website"),
    ("SAMPLE-O-002", "SAMPLE Ferro Architecture", "SAMPLE Architecture", 48, "front desk", "9 to 11 am", "no", "email",
     "chips-crisps;crackers-pretzels;sparkling-soda;bars", 40.7411, -73.9874, "founder"),
    ("SAMPLE-O-003", "SAMPLE Halcyon Media", "SAMPLE Media", 95, "walk-up", "9 to 11 am", "unsure", "slack",
     "chips-crisps;popcorn-puffs;sparkling-soda;tea-juice;bars;fruit-snacks", 40.7389, -73.9917, "website"),
    ("SAMPLE-O-004", "SAMPLE Union Food Fund", "SAMPLE Nonprofit", 110, "loading dock", "10 am to noon", "no", "email",
     "chips-crisps;sparkling-soda;bars;fruit-snacks", 40.7376, -73.9879, "founder"),
    ("SAMPLE-O-005", "SAMPLE Studio Marlow", "SAMPLE Design studio", 190, "front desk", "10 am to noon", "yes", "slack",
     "chips-crisps;cookies-baked;sparkling-soda;coffee-rtd;bars;fruit-snacks", 40.7425, -73.9901, "website"),
    ("SAMPLE-O-006", "SAMPLE Kestrel Analytics", "SAMPLE Software", 65, "walk-up", "8 to 10 am", "no", "slack",
     "chips-crisps;bars;fruit-snacks;sparkling-soda", 40.7433, -73.9878, "website"),
    ("SAMPLE-O-007", "SAMPLE Brine & Bell PR", "SAMPLE Public relations", 140, "front desk", "9 to 11 am", "no", "slack",
     "chips-crisps;bars;fruit-snacks;chocolate-candy", 40.7402, -73.9851, "website"),
    ("SAMPLE-O-008", "SAMPLE Larch Legal", "SAMPLE Law firm", 80, "front desk", "9 to 11 am", "yes", "email",
     "chips-crisps;bars;fruit-snacks;nuts-seeds-trail", 40.7417, -73.9925, "founder"),
    ("SAMPLE-O-009", "SAMPLE Overlook Games", "SAMPLE Games studio", 220, "front desk", "10 am to noon", "no", "slack",
     "chips-crisps;bars;fruit-snacks;sparkling-soda;popcorn-puffs", 40.7381, -73.9937, "website"),
    ("SAMPLE-O-010", "SAMPLE Quill Nonprofit Press", "SAMPLE Publishing", 45, "walk-up", "8 to 10 am", "no", "email",
     "chips-crisps;bars;fruit-snacks;tea-juice", 40.7369, -73.9906, "founder"),
]
OWNERS = {o[0]: ("SAMPLE Owner " + o[0][-3:], "SAMPLE Office Manager", "SAMPLE (212) 555-01" + o[0][-2:]) for o in OFFICES}
FRONT_DESK_OK = {"SAMPLE-O-002": "Y", "SAMPLE-O-004": "Y", "SAMPLE-O-005": "Y", "SAMPLE-O-007": "Y", "SAMPLE-O-008": "Y", "SAMPLE-O-009": "N"}
DELIVERY_NOTE = {
    "SAMPLE-O-001": "SAMPLE 4th floor kitchen, left of the coffee machine",
    "SAMPLE-O-002": "SAMPLE front desk calls up; owner meets you in the lobby",
    "SAMPLE-O-003": "SAMPLE 2nd floor pantry, shelf by the window",
    "SAMPLE-O-004": "SAMPLE loading dock on the side street; mailroom signs, owner collects",
    "SAMPLE-O-005": "SAMPLE show the certificate at the desk; 9th floor kitchen",
    "SAMPLE-O-006": "SAMPLE 3rd floor, ring the bell",
    "SAMPLE-O-007": "SAMPLE desk sends you up to 11; pantry at the end of the hall",
    "SAMPLE-O-008": "SAMPLE certificate required at the desk; 6th floor",
    "SAMPLE-O-009": "SAMPLE owner must take it; desk will not hold food",
    "SAMPLE-O-010": "SAMPLE walk-up, 2nd floor, kitchen on the right",
}
SIGNED = {"SAMPLE-O-001": "2026-11-16", "SAMPLE-O-002": "2026-11-18", "SAMPLE-O-003": "2026-11-24", "SAMPLE-O-004": "2026-12-01",
          "SAMPLE-O-005": "2026-12-03", "SAMPLE-O-006": "2027-01-21", "SAMPLE-O-007": "2027-01-22", "SAMPLE-O-008": "2027-01-25",
          "SAMPLE-O-009": "2027-01-26", "SAMPLE-O-010": "2027-01-27"}


def office_rows(ids):
    intake_web, form_rows, signed, roster = [], [], [], []
    for (oid, co, ind, h, rt, win, coi, ch, cats, lat, lon, via) in OFFICES:
        if oid not in ids:
            continue
        on = d(SIGNED[oid]) - dt.timedelta(days=6)
        sub = on.isoformat() + "T10:%02d:00-05:00" % int(oid[-2:])
        oname, otitle, ophone = OWNERS[oid]
        base = {"form_version": "office-1.0", "company": co, "contact_name": oname, "contact_title": otitle,
                "contact_email": "SAMPLE-owner-%s@example.com" % oid[-3:], "contact_phone": ophone,
                "office_address": "SAMPLE %d Example Avenue" % (100 + int(oid[-3:]) * 10), "floor_suite": "SAMPLE Floor %d" % (2 + int(oid[-2:]) % 9),
                "tuesday_headcount": h, "pantry_owner_name": oname, "pantry_owner_title": otitle, "pantry_owner_is_contact": "Y",
                "receiving_type": rt, "receiving_window": win, "coi_required": coi, "survey_channel": ch,
                "categories_wanted": cats, "vetoes": "SAMPLE no tree nuts" if oid == "SAMPLE-O-007" else "",
                "notes": "SAMPLE intake note", "source": via}
        if via == "website":
            intake_web.append(dict(base, submitted_at=sub, _on=on))
            sa = sub
        else:
            labels = {"walk-up": "Walk-up, straight to us", "front desk": "Front desk", "loading dock": "Loading dock", "other": "Something else"}
            catlabels = {k: lab for k, lab, b in CATS}
            ts = dt.datetime.combine(on, tm(14, int(oid[-2:])))
            form_rows.append({"_on": on, "Timestamp": ts, "Company": co, "Your name": oname, "Your title (optional)": otitle,
                              "Work email": base["contact_email"], "Work phone (optional)": ophone,
                              "Office street address": base["office_address"], "Floor or suite (optional)": base["floor_suite"],
                              "People in the office on a typical Tuesday": h, "Are you the pantry owner?": "Yes, me",
                              "How do deliveries reach your office?": labels[rt],
                              "Best time to receive, on a Tuesday or Wednesday morning": win,
                              "Does your building ask for a certificate of insurance before a delivery?": {"yes": "Yes", "no": "No", "unsure": "Not sure"}[coi],
                              "Where would you post the three-question survey link?": {"slack": "Slack", "email": "Email", "other": "Other"}[ch],
                              "Which categories do you want?": ", ".join(catlabels[k] for k in cats.split(";")),
                              "Anything you never want? (optional)": base["vetoes"], "Anything else? (optional)": base["notes"]})
            sa = ts.strftime("%Y-%m-%dT%H:%M:%S")
            base = dict(base, form_version="office-gform-1.0", source="founder")
        signed.append(dict(base, submitted_at=sa, office_id=oid, clay_row_id="SAMPLE-CLAY-O-%s" % oid[-3:],
                           agreement_signed_date=d(SIGNED[oid]), agreement_file="SAMPLE-agreement-%s.pdf" % oid,
                           founding_roster_named="Y" if oid in ("SAMPLE-O-001", "SAMPLE-O-003") else "N",
                           budget_probe_verbatim="SAMPLE \"maybe a couple hundred a month\"" if oid == "SAMPLE-O-003" else "SAMPLE no budget named",
                           budget_probe_date=on, budget_probe_monthly_usd=200 if oid == "SAMPLE-O-003" else "",
                           industry=ind, pantry_owner_phone=ophone, pantry_owner_email=base["contact_email"],
                           public_naming_ok="N", agreement_version="0.8", building_id="", _on=d(SIGNED[oid])))
        roster.append({"_on": d(SIGNED[oid]), "office_id": oid, "lat": lat, "lon": lon,
                       "front_desk_fallback_ok": FRONT_DESK_OK.get(oid, "N"), "delivery_point_note": DELIVERY_NOTE[oid],
                       "building_coi_status": {"yes": "to_request", "unsure": "to_request", "no": "not_needed"}[coi],
                       "status": "active"})
    return intake_web, form_rows, signed, roster


CATS = [
    ["chips-crisps", "Chips and crisps", "Chips and crisps"], ["popcorn-puffs", "Popcorn and puffs", "Popcorn and puffs"],
    ["crackers-pretzels", "Crackers and pretzels", "Crackers and pretzels"], ["bars", "Bars", "Bars"],
    ["cookies-baked", "Cookies and baked snacks", "Cookies and baked snacks"], ["chocolate-candy", "Chocolate and candy", "Chocolate and candy"],
    ["nuts-seeds-trail", "Nuts, seeds and trail mix", "Nuts, seeds and trail mix"], ["meat-snacks", "Jerky and meat sticks", "Jerky and meat sticks, shelf-stable only"],
    ["fruit-snacks", "Dried fruit and fruit snacks", "Dried fruit and fruit snacks"], ["sparkling-soda", "Sparkling water and soda", "Sparkling water and soda"],
    ["tea-juice", "Tea, juice and other non-carbonated drinks", "Tea, juice and other non-carbonated drinks, shelf-stable"],
    ["coffee-rtd", "Ready-to-drink coffee", "Ready-to-drink coffee, shelf-stable"], ["other-snack", "Other snacks", "Another kind of snack"],
    ["other-drink", "Other drinks", "Another kind of drink"],
]


# ---------------------------------------------------------------- brands
BRANDS = {
    "SAMPLE-BR-001": dict(name="SAMPLE Brightside", cat="chips-crisps", sku="SAMPLE Sea Salt Lentil Crisps, 1 oz bags", city="SAMPLE Queens, NY",
                          site="https://example.com/brightside", via="website", submitted="2026-11-10T09:14:08-05:00"),
    "SAMPLE-BR-002": dict(name="SAMPLE Northbound", cat="sparkling-soda", sku="SAMPLE Grapefruit Sparkling Water, 12 oz cans", city="SAMPLE Brooklyn, NY",
                          site="https://example.com/northbound", via="founder", submitted="2026-11-19T14:05:00"),
    "SAMPLE-BR-003": dict(name="SAMPLE Tallgrass", cat="bars", sku="SAMPLE Oat & Date Bars, 1.4 oz", city="SAMPLE Jersey City, NJ",
                          site="https://example.com/tallgrass", via="website", submitted="2026-12-15T11:30:00-05:00"),
    "SAMPLE-BR-004": dict(name="SAMPLE Orchard Row", cat="fruit-snacks", sku="SAMPLE Dried Mango Strips, 1 oz", city="SAMPLE Hudson Valley, NY",
                          site="https://example.com/orchardrow", via="website", submitted="2026-12-21T16:45:00-05:00"),
}


def brand_rows(ids):
    web, form, brands = [], [], []
    for bid in ids:
        b = BRANDS[bid]
        on = d(b["submitted"][:10])
        q = {"q1_sealed_shelf_stable_60d": "Y", "q2_labeled_ingredients_allergens": "Y", "q3_buy_path_near_cluster": "Y",
             "q4_can_ship_275_in_10bd": "Y", "q5_product_liability_insurance": "Y", "q6_contact_can_approve_600": "Y"}
        common = {"brand_name": b["name"], "website": b["site"], "contact_name": "SAMPLE Founder of " + b["name"][7:],
                  "contact_title": "SAMPLE Co-founder", "contact_email": "SAMPLE-%s@example.com" % bid[-3:],
                  "contact_phone": "SAMPLE (718) 555-01%s" % bid[-2:], "product_sku": b["sku"], "category": b["cat"],
                  "hq_city": b["city"], "nyc_retailers": "SAMPLE Example Market, 1 Example Street",
                  "online_store_url": b["site"] + "/shop", "can_issue_discount_code": "Y", "preferred_timing": "Next available drop",
                  "budget_approver_is_contact": "Y", "q7_why_now": "SAMPLE new placement at a store near the cluster",
                  "excluded_category_confirmed": "Y", "notes": "", **q}
        if b["via"] == "website":
            web.append(dict(common, _on=on, submitted_at=b["submitted"], form_version="brand-1.0" if bid < "SAMPLE-BR-003" else "brand-2.0",
                            budget_approver_name_title=common["contact_name"] + ", " + common["contact_title"], source="website"))
        else:
            ts = dt.datetime.fromisoformat(b["submitted"])
            form.append({"_on": on, "Timestamp": ts, "Brand name": b["name"], "Brand website": b["site"].replace("https://", ""),
                         "Product for the campaign": b["sku"], "Category": next(x[2] for x in CATS if x[0] == b["cat"]),
                         "Where is the brand based?": b["city"], "Your name": common["contact_name"], "Your title": common["contact_title"],
                         "Work email": common["contact_email"], "Work phone (optional)": common["contact_phone"], "Who signs off on the budget?": "I do",
                         "Their name and title (only if someone else)": "", "New York stores that carry you (optional)": common["nyc_retailers"],
                         "Online store (optional)": common["online_store_url"], "Can you issue a discount code for the campaign?": "Yes",
                         "When would you want a campaign?": "Next available drop",
                         "1. Individually packaged, sealed and shelf-stable, with 60 or more days of shelf life left at delivery?": "Yes",
                         "2. Labeled with ingredients and the nine major allergens?": "Yes",
                         "3. Sold in a store inside or within ten blocks of the cluster, or online with a discount code?": "Yes",
                         "4. Able to ship 275 units to one Manhattan address within ten business days?": "Yes",
                         "5. Covered by product liability insurance?": "Yes",
                         "6. Can you approve $600 on your own, without a committee?": "Yes",
                         "7. Why New York, and why now?": common["q7_why_now"],
                         "Not an excluded product": "My product is none of these: alcohol; cannabis, CBD or THC; a dietary supplement; refrigerated or perishable; needs preparation; makes health claims.",
                         "Notes (optional)": ""})
        brands.append({"_on": on + dt.timedelta(days=14), "brand_id": bid, "intake_key": b["submitted"],
                       "brand_legal_name": b["name"] + " Foods LLC", "billing_address": "SAMPLE 1 Example Plaza, Example City",
                       "billing_email": "SAMPLE-ap-%s@example.com" % bid[-3:], "retailer_evidence_grade": "brand_claim",
                       "coi_check_ok": "Y", "coi_policy_end_date": d("2027-06-30") if bid == "SAMPLE-BR-001" else d("2028-03-31"),
                       "status": "active"})
    return web, form, brands


# ---------------------------------------------------------------- survey rows
def survey(cid, plan, T, close, seed, extra=()):
    """plan: {office_id: n}. Returns Google-Forms-shaped rows [ts, code, tried, rating, buy, why, comment]."""
    rnd = random.Random(seed)
    import opscal
    days = [opscal.add_bd(T, i) for i in range(5)]
    rows = []
    comments = [
        "SAMPLE Saw it by the coffee machine and took two. Really good.",
        "SAMPLE A bit too salty for me.",
        "SAMPLE Where can I buy these near the office?",
        "SAMPLE Asked Priya to save me a bag. Really good.",
        "SAMPLE Good crunch, would pick it up at the store.",
        "SAMPLE Not my thing but my team liked it.",
        "SAMPLE Gone before lunch on Wednesday.",
        "SAMPLE Nice that it lists the allergens on the card.",
    ]
    for oid, n in plan.items():
        for i in range(n):
            day = days[min(4, int(rnd.random() * 3.2))] if i < n - 1 else days[min(4, i % 5)]
            ts = dt.datetime.combine(day, tm(9 + int(rnd.random() * 8), int(rnd.random() * 59)))
            if ts.date() == close and ts.hour >= 23:
                ts = ts.replace(hour=17)
            tried = "Yes" if rnd.random() < 0.72 else "No"
            if tried == "Yes":
                rating = rnd.choice([3, 4, 4, 4, 5, 5])
                buy = rnd.choice(["Yes", "Yes", "Maybe", "Maybe", "No"])
                why = ""
            else:
                rating, buy = "", ""
                why = rnd.choice(["Didn't see it", "Not for me", "Gone by the time I looked"])
            comment = comments[int(rnd.random() * len(comments))] if rnd.random() < 0.35 else ""
            rows.append([ts, "%s.%s" % (cid, oid), tried, rating, buy, why, comment])
    rows.extend(extra)
    rows.sort(key=lambda r: r[0])
    return rows


def ensure_comments(rows, T, close, comments):
    """Put the comments the report quotes on in-window rows (the founder copies them from real rows)."""
    k = 0
    for r in rows:
        if k >= len(comments):
            break
        if T <= r[0].date() <= close and r[2] == "Yes" and not r[1].endswith(".SAMPLE-O-00"):
            r[6] = comments[k]
            k += 1


def _approvals(cid, oids, asked, replies, on, overrides=None):
    out = []
    for oid in oids:
        rep, rd = replies.get(oid, ("yes", asked + dt.timedelta(days=2)))
        row = {"_on": asked, "campaign_id": cid, "office_id": oid, "asked_date": asked}
        if rep:
            row.update({"reply": rep, "reply_date": rd, "reply_note": "SAMPLE replied by email"})
        if overrides and oid in overrides:
            row["units_override"] = overrides[oid]
        out.append(row)
    return out


def zero():
    """Campaign zero: SAMPLE Brightside (chips) and SAMPLE Northbound (sparkling water), 5 offices, founder."""
    import opscal
    T = d("2027-01-12")
    s = opscal.sop_dates(T)
    O5 = ["SAMPLE-O-001", "SAMPLE-O-002", "SAMPLE-O-003", "SAMPLE-O-004", "SAMPLE-O-005"]
    web, form, signed, roster = office_rows(O5)
    bweb, bform, brands = brand_rows(["SAMPLE-BR-001", "SAMPLE-BR-002"])
    for r in roster:
        if r["office_id"] in ("SAMPLE-O-003", "SAMPLE-O-005"):
            r.update(building_coi_status="received", building_coi_date=d("2026-12-23"))
    rows = {
        "office_intake": web, "office_form": form, "in_signed_offices": signed, "offices": roster,
        "brand_intake": bweb, "brand_form": bform, "brands": brands,
        "drops": [{"_on": d("2026-11-16"), "drop_id": "SAMPLE-DRP-001", "drop_date": T, "delivery_model": "founder",
                   "status": "confirmed", "receiving_location": "SAMPLE receiving address (founder's home, sealed cases)",
                   "courier_or_van": "SAMPLE car service between stops", "backup_person": "SAMPLE backup (briefed 2027-01-08)",
                   "notes": "SAMPLE campaign zero"}],
    }
    card = {
        "SAMPLE-CMP-001": dict(card_sentences="SAMPLE Two friends in Queens make lentil crisps that taste like a snack, not a compromise. Baked in small batches in Long Island City.",
                               allergen_source="contains_statement", allergen_line_verbatim="SAMPLE Contains: milk, sesame.",
                               may_contain_verbatim="SAMPLE Made in a facility that also processes tree nuts.",
                               retailer_line="SAMPLE Example Market, 1 Example Street", discount_code="SAMPLEDESK15", code_site="example.com",
                               landing_url="https://example.com/brightside/office", unused_product_election="release", newsletter_option="Y",
                               brand_privacy_url="https://example.com/brightside/privacy"),
        "SAMPLE-CMP-002": dict(card_sentences="SAMPLE A Brooklyn sparkling water with real grapefruit and nothing else. Started in a Red Hook kitchen in 2023.",
                               allergen_source="single_ingredient", allergen_line_verbatim="SAMPLE Sparkling Water, Grapefruit Juice",
                               may_contain_verbatim="", retailer_line="SAMPLE Example Grocer, 20 Example Avenue", discount_code="SAMPLEFIZZ10",
                               code_site="example.com", landing_url="", unused_product_election="return", newsletter_option="N",
                               brand_privacy_url="", units_per_case=24),
    }
    rows["campaigns"] = []
    for cid, bid, signed_on, prod in (("SAMPLE-CMP-001", "SAMPLE-BR-001", "2026-12-07", BRANDS["SAMPLE-BR-001"]["sku"]),
                                      ("SAMPLE-CMP-002", "SAMPLE-BR-002", "2026-12-08", BRANDS["SAMPLE-BR-002"]["sku"])):
        rows["campaigns"].append(dict(_on=d(signed_on), campaign_id=cid, drop_id="SAMPLE-DRP-001", brand_id=bid, tier="founding",
                                      offices_contracted=5, agreement_signed_date=d(signed_on), agreement_version="0.8", product_sku=prod,
                                      coi_received_date=d("2026-12-14") if cid.endswith("1") else d("2026-12-15"),
                                      allergen_sheet_received_date=d("2026-12-14"), logo_received_date=d("2026-12-14"),
                                      logo_file="", card_proof_sent_date=d("2026-12-21"),
                                      survey_form_url="https://docs.google.com/forms/d/e/%s-FORM/viewform" % cid,
                                      survey_prefill_template="https://docs.google.com/forms/d/e/%s-FORM/viewform?usp=pp_url&entry.1000001=CARDCODE" % cid,
                                      newsletter_form_url=("https://docs.google.com/forms/d/e/%s-NEWS/viewform" % cid) if card[cid]["newsletter_option"] == "Y" else "",
                                      **card[cid]))
    rows["invoices"] = [
        {"_on": d("2026-12-07"), "invoice_id": "SAMPLE-INV-001", "campaign_id": "SAMPLE-CMP-001", "invoice_type": "founding_full",
         "issued_date": d("2026-12-07"), "amount_usd": 600, "sales_tax_usd": 0, "sent_to": "SAMPLE-ap-001@example.com",
         "paid_date": d("2026-12-10"), "paid_amount_usd": 600, "method": "bank_transfer", "bank_reference": "SAMPLE-ACH-7781", "processing_fee_usd": 0},
        {"_on": d("2026-12-08"), "invoice_id": "SAMPLE-INV-002", "campaign_id": "SAMPLE-CMP-002", "invoice_type": "founding_full",
         "issued_date": d("2026-12-08"), "amount_usd": 600, "sales_tax_usd": 0, "sent_to": "SAMPLE-ap-002@example.com",
         "paid_date": d("2026-12-11"), "paid_amount_usd": 600, "method": "bank_transfer", "bank_reference": "SAMPLE-WIRE-3302", "processing_fee_usd": 0},
        {"_on": s["placement_confirm"], "invoice_id": "SAMPLE-INV-003", "campaign_id": "SAMPLE-CMP-001", "invoice_type": "credit_note",
         "issued_date": s["placement_confirm"], "amount_usd": -120, "sales_tax_usd": 0, "sent_to": "SAMPLE-ap-001@example.com",
         "paid_date": d("2027-01-15"), "paid_amount_usd": -120, "method": "bank_transfer", "bank_reference": "SAMPLE-REFUND-0001",
         "processing_fee_usd": 0, "note": "SAMPLE office D (SAMPLE-O-004) not placed by T+1: refund of that office's share, brand agreement section 8"},
    ]
    # paid rows are only known on their paid date
    for r in rows["invoices"]:
        r["_fields_on"] = {"paid_date": r["paid_date"], "paid_amount_usd": r["paid_date"], "method": r["paid_date"], "bank_reference": r["paid_date"]}
    rows["approvals"] = []
    for cid in ("SAMPLE-CMP-001", "SAMPLE-CMP-002"):
        rows["approvals"] += _approvals(cid, O5, d("2026-12-14"), {o: ("yes", d("2026-12-16") if o != "SAMPLE-O-004" else d("2026-12-18")) for o in O5}, None)
    order = ["SAMPLE-O-001", "SAMPLE-O-003", "SAMPLE-O-002", "SAMPLE-O-005", "SAMPLE-O-004"]
    times = {"SAMPLE-O-001": (tm(8, 10), tm(8, 20), tm(8, 38), "pantry owner", "placed_by_us"),
             "SAMPLE-O-003": (tm(8, 55), tm(8, 57), tm(9, 14), "pantry owner", "placed_by_us"),
             "SAMPLE-O-002": (tm(9, 30), tm(9, 31), tm(9, 46), "pantry owner", "handed_to_owner"),
             "SAMPLE-O-005": (tm(10, 10), tm(10, 14), tm(10, 36), "pantry owner", "handed_to_owner"),
             "SAMPLE-O-004": (tm(10, 50), tm(10, 52), tm(11, 4), "front desk", "front_desk_agreed")}
    rows["stops"] = []
    for i, oid in enumerate(order, start=1):
        pt, a, b, who, oc = times[oid]
        rows["stops"].append({"_on": s["kit_print"], "drop_id": "SAMPLE-DRP-001", "office_id": oid, "route_order": i, "planned_time": pt,
                              "slack_post_sent_date": s["kit_print"], "confirm_text_sent_date": s["confirm"],
                              "arrival_time": a, "departure_time": b, "handed_to_role": who, "outcome": oc,
                              "notes": "SAMPLE owner out; mailroom signed as agreed" if oid == "SAMPLE-O-004" else "",
                              "office_debrief_date": d("2027-01-25"), "office_would_do_again": "maybe" if oid == "SAMPLE-O-004" else "yes",
                              "_fields_on": {"arrival_time": T, "departure_time": T, "handed_to_role": T, "outcome": T,
                                             "office_debrief_date": d("2027-01-25"), "office_would_do_again": d("2027-01-25")}})
    alloc = {"SAMPLE-O-001": 40, "SAMPLE-O-002": 40, "SAMPLE-O-003": 50, "SAMPLE-O-004": 50, "SAMPLE-O-005": 70}
    inv, cnt, ph = [], [], []
    # Brightside: 276 received, all good. Northbound: 275 received, 12 short-dated + 4 dented rejected.
    inv += [{"_on": d("2026-12-28"), "date": d("2026-12-28"), "time": tm(15, 20), "campaign_id": "SAMPLE-CMP-001", "movement": "received", "qty": 276,
             "lot": "SAMPLE-L2401", "best_by": d("2027-06-30"), "count_source": "founder_count", "note": "SAMPLE 6 cases, counted, photographed"},
            {"_on": d("2026-12-30"), "date": d("2026-12-30"), "time": tm(11, 5), "campaign_id": "SAMPLE-CMP-002", "movement": "received", "qty": 263,
             "lot": "SAMPLE-NB-0921", "best_by": d("2027-09-01"), "count_source": "founder_count"},
            {"_on": d("2026-12-30"), "date": d("2026-12-30"), "time": tm(11, 5), "campaign_id": "SAMPLE-CMP-002", "movement": "received", "qty": 12,
             "lot": "SAMPLE-NB-0811", "best_by": d("2027-03-01"), "count_source": "founder_count", "note": "SAMPLE one case short-dated"},
            {"_on": d("2026-12-30"), "date": d("2026-12-30"), "time": tm(11, 30), "campaign_id": "SAMPLE-CMP-002", "movement": "rejected", "qty": 12,
             "lot": "SAMPLE-NB-0811", "note": "SAMPLE under 60 days left on the drop day"},
            {"_on": d("2026-12-30"), "date": d("2026-12-30"), "time": tm(11, 30), "campaign_id": "SAMPLE-CMP-002", "movement": "rejected", "qty": 4,
             "lot": "SAMPLE-NB-0921", "note": "SAMPLE dented cans, photographed"}]
    deliver_time = {o: times[o][1] for o in O5}
    for cid in ("SAMPLE-CMP-001", "SAMPLE-CMP-002"):
        for oid in O5:
            inv.append({"_on": T, "date": T, "time": deliver_time[oid], "campaign_id": cid, "office_id": oid, "movement": "delivered",
                        "qty": alloc[oid], "count_source": "founder_count"})
    inv += [{"_on": s["check_day3"], "date": s["check_day3"], "time": tm(12, 30), "campaign_id": "SAMPLE-CMP-001", "office_id": "SAMPLE-O-001", "movement": "topped_up", "qty": 5, "count_source": "founder_count"},
            {"_on": s["check_day3"], "date": s["check_day3"], "time": tm(12, 50), "campaign_id": "SAMPLE-CMP-002", "office_id": "SAMPLE-O-003", "movement": "topped_up", "qty": 6, "count_source": "founder_count"}]
    # Placement photos and counts.
    placed_photo = {  # office: (date, time, source, placed count for CMP-001, for CMP-002)
        "SAMPLE-O-001": (T, tm(8, 34), "founder", 40, 40),
        "SAMPLE-O-003": (T, tm(9, 10), "founder", 50, 50),
        "SAMPLE-O-002": (T, tm(11, 40), "office", 38, 40),
        "SAMPLE-O-005": (T, tm(14, 10), "office", 70, 70),
        "SAMPLE-O-004": (None, None, "office", 50, 50),
    }
    pid = [0]

    def photo(cid, oid, typ, day, t, src, usable=True, note=""):
        pid[0] += 1
        p = "SAMPLE-PH-%04d" % pid[0]
        ph.append({"_on": day, "photo_id": p, "campaign_id": cid, "office_id": oid, "photo_type": typ, "taken_date": day, "taken_time": t,
                   "source": src, "file_name": "%s_%s_%s_%s.jpg" % (cid, oid, typ, day.isoformat()), "received_date": day,
                   "card_visible": "Y", "no_people_or_screens": "Y" if usable else "N", "note": note})
        return p

    rem3 = {"SAMPLE-CMP-001": {"SAMPLE-O-001": 4, "SAMPLE-O-002": 15, "SAMPLE-O-003": 18, "SAMPLE-O-004": 41, "SAMPLE-O-005": 22},
            "SAMPLE-CMP-002": {"SAMPLE-O-001": 14, "SAMPLE-O-002": 16, "SAMPLE-O-003": 3, "SAMPLE-O-004": 28, "SAMPLE-O-005": 25}}
    rem5 = {"SAMPLE-CMP-001": {"SAMPLE-O-001": 1, "SAMPLE-O-002": 7, "SAMPLE-O-003": 9, "SAMPLE-O-004": 28, "SAMPLE-O-005": 8},
            "SAMPLE-CMP-002": {"SAMPLE-O-001": 3, "SAMPLE-O-002": 4, "SAMPLE-O-003": 6, "SAMPLE-O-004": 2, "SAMPLE-O-005": 3}}
    for k, cid in enumerate(("SAMPLE-CMP-001", "SAMPLE-CMP-002")):
        for oid in O5:
            day, t, src, n1, n2 = placed_photo[oid]
            if oid == "SAMPLE-O-004":
                day, t = (s["check_day3"], tm(9, 45)) if cid == "SAMPLE-CMP-001" else (s["placement_confirm"], tm(9, 5))
            p = photo(cid, oid, "placement", day, t, src)
            cnt.append({"_on": day, "date": day, "time": t, "campaign_id": cid, "office_id": oid, "count_type": "placed",
                        "units": n1 if k == 0 else n2, "source": "photo", "photo_id": p})
            cnt.append({"_on": s["check_day3"], "date": s["check_day3"], "time": tm(11, 0), "campaign_id": cid, "office_id": oid,
                        "count_type": "remaining_day3", "units": rem3[cid][oid], "source": "owner_report"})
            if cid == "SAMPLE-CMP-002" and oid == "SAMPLE-O-002":
                p2 = photo(cid, oid, "later", s["check_day3"], tm(15, 20), "office")   # day-3 photo only
            elif cid == "SAMPLE-CMP-002" and oid == "SAMPLE-O-003":
                p2 = None                                                            # no later photo received
            elif cid == "SAMPLE-CMP-001" and oid == "SAMPLE-O-005":
                photo(cid, oid, "later", s["close"], tm(15, 2), "office", usable=False, note="SAMPLE a person's face is visible: never used")
                p2 = photo(cid, oid, "later", s["close"], tm(16, 40), "office", note="SAMPLE resent on request")
            else:
                p2 = photo(cid, oid, "later", s["close"], tm(15, 30), "office" if cid == "SAMPLE-CMP-001" else "founder")
            cnt.append({"_on": s["close"], "date": s["close"], "time": tm(16, 0), "campaign_id": cid, "office_id": oid,
                        "count_type": "remaining_day5", "units": rem5[cid][oid],
                        "source": "photo" if (p2 and cid == "SAMPLE-CMP-001") else "founder_count", "photo_id": p2 if cid == "SAMPLE-CMP-001" else ""})
    # Closing the stock: Brightside released (reserve 26-5=21 given to two offices); Northbound collected and returned.
    left2 = sum(rem5["SAMPLE-CMP-002"].values())
    inv += [{"_on": s["close"], "date": s["close"], "time": tm(16, 30), "campaign_id": "SAMPLE-CMP-001", "office_id": "SAMPLE-O-001", "movement": "released_to_office", "bucket": "reserve", "qty": 10, "count_source": "founder_count", "note": "SAMPLE brand chose release"},
            {"_on": s["close"], "date": s["close"], "time": tm(16, 40), "campaign_id": "SAMPLE-CMP-001", "office_id": "SAMPLE-O-003", "movement": "released_to_office", "bucket": "reserve", "qty": 11, "count_source": "founder_count", "note": "SAMPLE brand chose release"}]
    for oid in O5:
        inv.append({"_on": s["close"], "date": s["close"], "time": tm(16, 0), "campaign_id": "SAMPLE-CMP-002", "office_id": oid, "movement": "collected",
                    "qty": rem5["SAMPLE-CMP-002"][oid], "count_source": "founder_count"})
    ret = d("2027-01-22")
    inv += [{"_on": ret, "date": ret, "time": tm(10, 0), "campaign_id": "SAMPLE-CMP-002", "movement": "returned_to_brand", "bucket": "reserve", "qty": 3, "count_source": "founder_count", "note": "SAMPLE prepaid label arrived 2027-01-21"},
            {"_on": ret, "date": ret, "time": tm(10, 0), "campaign_id": "SAMPLE-CMP-002", "movement": "returned_to_brand", "bucket": "leftover", "qty": left2, "count_source": "founder_count"},
            {"_on": ret, "date": ret, "time": tm(10, 0), "campaign_id": "SAMPLE-CMP-002", "movement": "returned_to_brand", "bucket": "rejected", "qty": 16, "count_source": "founder_count"}]
    rows["inventory"], rows["counts"], rows["photos"] = inv, cnt, ph
    # Survey answers, as the two Google Forms would write them.
    plan1 = {"SAMPLE-O-001": 9, "SAMPLE-O-002": 6, "SAMPLE-O-003": 8, "SAMPLE-O-004": 4, "SAMPLE-O-005": 7}
    plan2 = {"SAMPLE-O-001": 7, "SAMPLE-O-002": 5, "SAMPLE-O-003": 9, "SAMPLE-O-004": 5, "SAMPLE-O-005": 6}
    extra1 = [[at("2027-01-07", 16, 12), "SAMPLE-CMP-001.SAMPLE-O-001", "Yes", 5, "Yes", "", "SAMPLE founder test at kitting"],
              [at("2027-01-20", 8, 41), "SAMPLE-CMP-001.SAMPLE-O-003", "Yes", 4, "Maybe", "", ""],
              [at("2027-01-14", 13, 3), "SAMPLE-CMP-001.SAMPLE-O-00", "No", "", "", "Not for me", ""]]
    resp = {"SAMPLE-CMP-001": ("SAMPLE Brightside", survey("SAMPLE-CMP-001", plan1, T, s["close"], 11, extra1)),
            "SAMPLE-CMP-002": ("SAMPLE Northbound", survey("SAMPLE-CMP-002", plan2, T, s["close"], 22))}
    ensure_comments(resp["SAMPLE-CMP-001"][1], T, s["close"], ["SAMPLE Saw it by the coffee machine and took two. Really good.",
                                                              "SAMPLE A bit too salty for me.", "SAMPLE Asked Priya to save me a bag. Really good."])
    ensure_comments(resp["SAMPLE-CMP-002"][1], T, s["close"], ["SAMPLE Gone before lunch on Wednesday.", "SAMPLE Not my thing but my team liked it.",
                                                              "SAMPLE Nice that it lists the allergens on the card."])
    for cid, (b, rr) in resp.items():
        for r in rr:
            r.append(r[0].date())  # _on, stripped before writing
    # Link readings: baseline after the kitting test scan, mid at T+2, close at T+4, late at T+7.
    import tracker as TR
    scans = []
    qr_close = {"SAMPLE-CMP-001": [15, 8, 12, 5, 10], "SAMPLE-CMP-002": [10, 6, 13, 7, 8]}
    post_close = {"SAMPLE-CMP-001": [6, 3, 7, 2, 9], "SAMPLE-CMP-002": [5, 2, 6, 3, 4]}
    for cid in ("SAMPLE-CMP-001", "SAMPLE-CMP-002"):
        for i, oid in enumerate(O5):
            for kind, close in (("q", qr_close[cid][i]), ("p", post_close[cid][i])):
                sl = TR.slug(cid, oid, kind)
                for day, typ, v in ((s["confirm"], "baseline", 1), (s["check_day3"], "mid", max(1, close // 2)),
                                    (s["close"], "close", close), (s["report_due"], "late", close + 1)):
                    scans.append({"_on": day, "read_date": day, "read_time": tm(17, 30), "slug": sl, "reading_type": typ, "clicks_to_date": v})
    rows["scans"] = scans
    rows["redemptions"] = [
        {"_on": s["report_due"], "campaign_id": "SAMPLE-CMP-001", "as_of_date": d("2027-01-21"), "redemptions_to_date": 6, "reported_date": d("2027-01-21"), "reported_by_role": "SAMPLE brand co-founder"},
        {"_on": s["report_due"], "campaign_id": "SAMPLE-CMP-002", "as_of_date": d("2027-01-21"), "redemptions_to_date": 2, "reported_date": d("2027-01-21"), "reported_by_role": "SAMPLE brand co-founder"},
        {"_on": d("2027-02-11"), "campaign_id": "SAMPLE-CMP-001", "as_of_date": d("2027-02-11"), "redemptions_to_date": 11, "reported_date": d("2027-02-11"), "reported_by_role": "SAMPLE brand co-founder"},
        {"_on": d("2027-02-12"), "campaign_id": "SAMPLE-CMP-002", "as_of_date": d("2027-02-12"), "redemptions_to_date": 4, "reported_date": d("2027-02-12"), "reported_by_role": "SAMPLE brand co-founder"},
    ]
    rows["issues"] = [
        {"_on": d("2026-12-30"), "issue_id": "SAMPLE-ISS-001", "date": d("2026-12-30"), "time": tm(11, 30), "drop_id": "SAMPLE-DRP-001", "campaign_id": "SAMPLE-CMP-002",
         "issue_type": "damaged_or_short_dated", "what_happened": "SAMPLE 12 cans with best-by 2027-03-01 (under 60 days on the drop day) and 4 dented cans on arrival.",
         "action_taken": "SAMPLE photographed, set aside, counts sent; brand asked for return with the leftovers.", "brand_told_date": d("2026-12-30"), "closed_date": d("2027-01-22")},
        {"_on": T, "issue_id": "SAMPLE-ISS-002", "date": T, "time": tm(10, 52), "drop_id": "SAMPLE-DRP-001", "office_id": "SAMPLE-O-004",
         "issue_type": "owner_absent", "what_happened": "SAMPLE owner out; mailroom signed for both cases, as agreed at intake.", "action_taken": "SAMPLE texted owner; owner placed the drinks Wednesday and the crisps Thursday.",
         "office_told_date": T, "closed_date": s["check_day3"]},
        {"_on": s["placement_confirm"], "issue_id": "SAMPLE-ISS-003", "date": s["placement_confirm"], "time": tm(17, 0), "drop_id": "SAMPLE-DRP-001", "campaign_id": "SAMPLE-CMP-001", "office_id": "SAMPLE-O-004",
         "issue_type": "placement_late", "what_happened": "SAMPLE crisps not placed by T+1 at office D; placed on day 3.", "action_taken": "SAMPLE refunded $120 (credit note SAMPLE-INV-003); agree a placement time at intake.",
         "brand_told_date": s["placement_confirm"], "office_told_date": s["placement_confirm"], "closed_date": d("2027-01-15")},
    ]
    # Hours: the plan's campaign-zero shape (57 hours), plus discovery time with no drop.
    H = []

    def hrs(day, act, h, cid="", did="SAMPLE-DRP-001", note=""):
        H.append({"_on": d(day) if isinstance(day, str) else day, "date": d(day) if isinstance(day, str) else day, "drop_id": did,
                  "campaign_id": cid, "activity": act, "hours": h, "note": note})
    for day in ("2026-10-27", "2026-10-29", "2026-11-03", "2026-11-05", "2026-11-10"):
        hrs(day, "office_coordination", 1.5, did="", note="SAMPLE discovery calls (no drop)")
        hrs(day, "brand_sales", 1.5, did="", note="SAMPLE discovery calls (no drop)")
    for i, day in enumerate(("2026-11-17", "2026-11-24", "2026-12-01", "2026-12-04", "2026-12-07")):
        hrs(day, "brand_sales", 2.0, "SAMPLE-CMP-001", note="SAMPLE qualifying, proposal, agreement")
        hrs(opscal.add_bd(d(day), 1), "brand_sales", 2.0, "SAMPLE-CMP-002", note="SAMPLE qualifying, proposal, agreement")
    for day in ("2026-11-16", "2026-11-18", "2026-11-24", "2026-12-01", "2026-12-03"):
        hrs(day, "office_coordination", 4.0, note="SAMPLE signing a founding office")
    hrs("2026-12-28", "receiving_kitting", 1.0, note="SAMPLE receive Brightside")
    hrs("2026-12-30", "receiving_kitting", 1.0, note="SAMPLE receive Northbound, reject 16")
    hrs(s["confirm"], "receiving_kitting", 1.0, note="SAMPLE pack ten cases")
    hrs(T, "drop_day", 5.0, note="SAMPLE route, five stops")
    hrs(s["check_day3"], "checks_pickup", 1.5, note="SAMPLE day-3 photos, two top-ups")
    hrs(s["close"], "checks_pickup", 1.5, note="SAMPLE day 5, collect Northbound leftovers")
    hrs(s["report_due"], "reporting_debriefs", 1.5, "SAMPLE-CMP-001", note="SAMPLE report")
    hrs(s["report_due"], "reporting_debriefs", 1.5, "SAMPLE-CMP-002", note="SAMPLE report")
    hrs(s["debrief"], "reporting_debriefs", 0.5, "SAMPLE-CMP-001", note="SAMPLE brand debrief")
    hrs(s["debrief"], "reporting_debriefs", 0.5, "SAMPLE-CMP-002", note="SAMPLE brand debrief")
    hrs("2026-12-07", "admin_invoicing", 1.0, note="SAMPLE invoices, certificate requests")
    hrs("2027-01-15", "admin_invoicing", 1.0, note="SAMPLE refund, placement confirmations")
    rows["hours"] = H
    rows["costs"] = [
        {"_on": s["kit_print"], "date": s["kit_print"], "drop_id": "SAMPLE-DRP-001", "campaign_id": "SAMPLE-CMP-001", "cost_type": "kit", "amount_usd": 40, "vendor": "SAMPLE copy shop", "note": "SAMPLE 5 cards and labels"},
        {"_on": s["kit_print"], "date": s["kit_print"], "drop_id": "SAMPLE-DRP-001", "campaign_id": "SAMPLE-CMP-002", "cost_type": "kit", "amount_usd": 40, "vendor": "SAMPLE copy shop", "note": "SAMPLE 5 cards and labels"},
        {"_on": T, "date": T, "drop_id": "SAMPLE-DRP-001", "cost_type": "transport", "amount_usd": 34, "vendor": "SAMPLE car service", "note": "SAMPLE home to first stop"},
        {"_on": T, "date": T, "drop_id": "SAMPLE-DRP-001", "cost_type": "transport", "amount_usd": 29, "vendor": "SAMPLE car service", "note": "SAMPLE stop 3 to stop 4 with the hand truck"},
        {"_on": s["kit_print"], "date": s["kit_print"], "drop_id": "SAMPLE-DRP-001", "cost_type": "other_direct", "amount_usd": 9, "vendor": "SAMPLE stationer", "note": "SAMPLE card stock"},
    ]
    # Report inputs and the debrief, typed on the campaign rows on their day.
    pick = {"SAMPLE-CMP-001": ["SAMPLE Saw it by the coffee machine and took two. Really good.", "SAMPLE A bit too salty for me.",
                               "SAMPLE Asked [name removed] to save me a bag. Really good."],
            "SAMPLE-CMP-002": ["SAMPLE Gone before lunch on Wednesday.", "SAMPLE Not my thing but my team liked it.",
                               "SAMPLE Nice that it lists the allergens on the card."]}
    learned = {"SAMPLE-CMP-001": "SAMPLE Office D placed a day late; agree a placement time at intake.\nSAMPLE Four people found it gone by the time they looked.\nSAMPLE Salt level came up in comments more than once.",
               "SAMPLE-CMP-002": "SAMPLE Office C ran out by day 3 and needed a top-up.\nSAMPLE 16 cans could not be placed (short-dated or dented).\nSAMPLE Drinks went faster in the larger offices."}
    rec = {"SAMPLE-CMP-001": "SAMPLE Renew into offices A, C and E at the founding price. Same card.",
           "SAMPLE-CMP-002": "SAMPLE Renew only with fresher stock; ship 90 or more days of shelf life."}
    for r in rows["campaigns"]:
        cid = r["campaign_id"]
        avail = {}
        cs = pick[cid]
        r.update(comment_1=cs[0], comment_2=cs[1], comment_3=cs[2], learned=learned[cid], recommendation=rec[cid],
                 report_delivered_date=s["report_due"], debrief_date=s["debrief"],
                 brand_would_buy_again="yes" if cid.endswith("1") else "maybe", renewed="Y" if cid.endswith("1") else "N",
                 renewal_note="SAMPLE renews into the first standard run at the founding lock" if cid.endswith("1") else "SAMPLE not now; asked again in April")
        for f in ("comment_1", "comment_2", "comment_3", "learned", "recommendation"):
            avail[f] = s["close"] + dt.timedelta(days=2)
        avail.update(report_delivered_date=s["report_due"], debrief_date=s["debrief"], brand_would_buy_again=s["debrief"],
                     renewed=d("2027-02-01"), renewal_note=d("2027-02-01"))
        if r["newsletter_option"] == "Y":
            r.update(newsletter_passed_date=s["pass_on"], newsletter_passed_count=7, newsletter_unticked_deleted_date=s["pass_on"],
                     newsletter_deleted_date=s["newsletter_delete"])
            avail.update(newsletter_passed_date=s["pass_on"], newsletter_passed_count=s["pass_on"], newsletter_unticked_deleted_date=s["pass_on"],
                         newsletter_deleted_date=s["newsletter_delete"])
        r["_fields_on"] = avail
    return {"name": "zero", "T": T, "drop_id": "SAMPLE-DRP-001", "rows": rows, "responses": resp,
            "campaigns": ["SAMPLE-CMP-001", "SAMPLE-CMP-002"], "offices": O5, "delivery_model": "founder"}
