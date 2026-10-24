"""SAMPLE scenarios for the dry runs. Every ID and text starts with SAMPLE. Nothing here is a result.

Each row carries "_on": the day the founder would log it. dryrun.py replays the calendar day by
day, building the tracker with only the rows known by that day.

zero:      campaign zero, 2 founding brands x 5 offices, founder-delivered, drop Tue 2027-01-12.
standard:  first standard run, 3 brands x 10 offices, courier, drop Tue 2027-02-09 (zero's rows are
           kept, as the real tracker would keep them).
exception: second standard run, 1 brand x 10 offices, courier, drop Tue 2027-02-23: a short shipment (480 of
           567) and one office that declines at the door (added in review round 1 from the reviewer's scenario).
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


def _approvals(cid, oids, asked, replies, on, overrides=None, override_on=None):
    out = []
    for oid in oids:
        rep, rd = replies.get(oid, ("yes", asked + dt.timedelta(days=2)))
        row = {"_on": asked, "campaign_id": cid, "office_id": oid, "asked_date": asked}
        if rep:
            row.update({"reply": rep, "reply_date": rd, "reply_note": "SAMPLE replied by email",
                        "_fields_on": {"reply": rd, "reply_date": rd, "reply_note": rd}})
        if overrides and oid in overrides:
            row["units_override"] = overrides[oid]
            if override_on:   # typed the day the reason happened (a short shipment), not at approval time
                row.setdefault("_fields_on", {})["units_override"] = override_on
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
    for r in rows["campaigns"]:
        r["_fields_history"] = {"ship_email_sent_date": [(d("2026-12-18"), d("2026-12-18"))], "ship_email_units": [(d("2026-12-18"), 275)]}
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


BRANDS["SAMPLE-BR-005"] = dict(name="SAMPLE Kettle Ridge", cat="chips-crisps", sku="SAMPLE Kettle Chips, Sea Salt, 1 oz bags", city="SAMPLE Albany, NY",
                               site="https://example.com/kettleridge", via="website", submitted="2026-12-28T10:20:00-05:00")


def standard():
    """First standard run: SAMPLE Tallgrass (bars), SAMPLE Orchard Row (dried fruit), SAMPLE Kettle Ridge (chips),
    10 offices (5 from campaign zero, 5 new), courier model, drop Tue 2027-02-09. Campaign zero's rows stay in the tracker."""
    import opscal
    import tracker as TR
    z = zero()
    T = d("2027-02-09")
    s = opscal.sop_dates(T)
    O10 = [o[0] for o in OFFICES]
    NEW = O10[5:]
    for k, v in (("SAMPLE-O-006", "2027-01-05"), ("SAMPLE-O-007", "2027-01-06"), ("SAMPLE-O-008", "2027-01-07"),
                 ("SAMPLE-O-009", "2027-01-08"), ("SAMPLE-O-010", "2027-01-13")):
        SIGNED[k] = v
    web, form, signed, roster = office_rows(NEW)
    for r in roster:
        if r["office_id"] == "SAMPLE-O-008":
            r.update(building_coi_status="received", building_coi_date=d("2027-01-29"))
    rows = copy_rows(z["rows"])
    rows["office_intake"] += web
    rows["office_form"] += form
    rows["in_signed_offices"] += signed
    rows["offices"] += roster
    for r in rows["in_signed_offices"]:
        if r["office_id"] == "SAMPLE-O-002":
            r["categories_wanted"] += ";fruit-snacks"
    bweb, bform, brands = brand_rows(["SAMPLE-BR-003", "SAMPLE-BR-004", "SAMPLE-BR-005"])
    rows["brand_intake"] += bweb
    rows["brand_form"] += bform
    rows["brands"] += brands
    rows["drops"].append({"_on": d("2026-12-14"), "drop_id": "SAMPLE-DRP-002", "drop_date": T, "delivery_model": "courier", "status": "confirmed",
                          "receiving_location": "SAMPLE receiving address (founder's home, sealed cases)",
                          "courier_or_van": "SAMPLE Example Courier, booking SAMPLE-BK-0209, pickup 7:45 am", "backup_person": "SAMPLE backup (briefed 2027-02-05)",
                          "notes": "SAMPLE first standard run"})
    CMP = {"SAMPLE-CMP-003": ("SAMPLE-BR-003", "2027-01-04", "2027-01-07", 80, "release", "N",
                              dict(card_sentences="SAMPLE Oat and date bars from a Jersey City bakery that started as a farmers-market stand. Four ingredients, no surprises.",
                                   allergen_source="contains_statement", allergen_line_verbatim="SAMPLE Contains: oats (gluten), almonds.",
                                   may_contain_verbatim="SAMPLE May contain peanuts.", retailer_line="SAMPLE Example Market, 1 Example Street",
                                   discount_code="SAMPLEBAR20", code_site="example.com")),
           "SAMPLE-CMP-004": ("SAMPLE-BR-004", "2027-01-06", "2027-01-11", 72, "return", "Y",
                              dict(card_sentences="SAMPLE Dried mango from one Hudson Valley co-op, cut thick and nothing added. Started by two sisters in 2022.",
                                   allergen_source="single_ingredient", allergen_line_verbatim="SAMPLE Dried Mango",
                                   may_contain_verbatim="SAMPLE Packed in a facility that also handles tree nuts.", retailer_line="SAMPLE Example Grocer, 20 Example Avenue",
                                   discount_code="SAMPLEMANGO", code_site="example.com", brand_privacy_url="https://example.com/orchardrow/privacy")),
           "SAMPLE-CMP-005": ("SAMPLE-BR-005", "2027-01-08", "2027-01-12", 80, "release", "N",
                              dict(card_sentences="SAMPLE Kettle chips fried in small batches near Albany, from one farm's potatoes. Salt, oil, potatoes, done.",
                                   allergen_source="ingredient_list", allergen_line_verbatim="SAMPLE Ingredients: potatoes, sunflower oil, sea salt.",
                                   may_contain_verbatim="", retailer_line="SAMPLE Example Market, 1 Example Street",
                                   discount_code="SAMPLECRUNCH", code_site="example.com"))}
    # The brand row (with billing details from the agreement's Part 1) is typed at the latest on the day the campaign
    # is signed and invoiced: an invoice never goes out without it (review round 1, R1-07; SAMPLE-INV-009 had).
    signed_by_brand = {v[0]: d(v[1]) for v in CMP.values()}
    for r in brands:
        r["_on"] = min(r["_on"], signed_by_brand.get(r["brand_id"], r["_on"]))
    # Ship-date emails as the founder logs them: sent on release (nine offices on the route). The tenth office (signed Wed
    # 2027-01-13) says yes on Thu 2027-01-14; the tracker then asks for a revised email, sent and logged Fri 2027-01-15.
    # Units = allocated + 10% reserve, rounded up.
    SHIP = {"SAMPLE-CMP-003": [("2027-01-11", 523), ("2027-01-15", 567)],
            "SAMPLE-CMP-004": [("2027-01-11", 457), ("2027-01-15", 501)],
            "SAMPLE-CMP-005": [("2027-01-12", 523), ("2027-01-15", 567)]}
    # Tallgrass shipped short (510 of 567): every office's allocation reduced by 3, reserve 25.
    base_units = {"SAMPLE-O-001": 40, "SAMPLE-O-002": 40, "SAMPLE-O-003": 50, "SAMPLE-O-004": 50, "SAMPLE-O-005": 70,
                  "SAMPLE-O-006": 45, "SAMPLE-O-007": 60, "SAMPLE-O-008": 45, "SAMPLE-O-009": 75, "SAMPLE-O-010": 40}
    for cid, (bid, signed_on, paid_on, kit, elect, nl, card) in CMP.items():
        rows["campaigns"].append(dict(_on=d(signed_on), campaign_id=cid, drop_id="SAMPLE-DRP-002", brand_id=bid, tier="standard",
                                      offices_contracted=10, agreement_signed_date=d(signed_on), agreement_version="0.8", product_sku=BRANDS[bid]["sku"],
                                      units_per_case=24 if cid == "SAMPLE-CMP-005" else "",
                                      coi_received_date=d(paid_on), allergen_sheet_received_date=d(paid_on), logo_received_date=d(paid_on),
                                      card_proof_sent_date=d("2027-01-29"), unused_product_election=elect, newsletter_option=nl,
                                      survey_form_url="https://docs.google.com/forms/d/e/%s-FORM/viewform" % cid,
                                      survey_prefill_template="https://docs.google.com/forms/d/e/%s-FORM/viewform?usp=pp_url&entry.1000001=CARDCODE" % cid,
                                      newsletter_form_url=("https://docs.google.com/forms/d/e/%s-NEWS/viewform" % cid) if nl == "Y" else "",
                                      _fields_on={"survey_form_url": s["forms"] if "forms" in s else opscal.add_bd(T, -4),
                                                  "survey_prefill_template": opscal.add_bd(T, -4)},
                                      _fields_history={"ship_email_sent_date": [(d(x), d(x)) for x, u in SHIP[cid]],
                                                       "ship_email_units": [(d(x), u) for x, u in SHIP[cid]]}, **card))
        n = len(rows["invoices"]) + 1
        rows["invoices"].append({"_on": d(signed_on), "invoice_id": "SAMPLE-INV-%03d" % n, "campaign_id": cid, "invoice_type": "standard_deposit",
                                 "issued_date": d(signed_on), "amount_usd": 750, "sales_tax_usd": 0, "sent_to": "SAMPLE-ap@example.com",
                                 "paid_date": d(paid_on), "paid_amount_usd": 750, "method": "bank_transfer", "bank_reference": "SAMPLE-ACH-%d" % n,
                                 "processing_fee_usd": 0, "_fields_on": {k: d(paid_on) for k in ("paid_date", "paid_amount_usd", "method", "bank_reference")}})
        paid_bal = {"SAMPLE-CMP-003": "2027-02-16", "SAMPLE-CMP-004": "2027-02-17", "SAMPLE-CMP-005": "2027-02-12"}[cid]
        n += 1
        rows["invoices"].append({"_on": s["placement_confirm"], "invoice_id": "SAMPLE-INV-%03d" % n, "campaign_id": cid, "invoice_type": "standard_balance",
                                 "issued_date": s["placement_confirm"], "amount_usd": 750, "sales_tax_usd": 0, "sent_to": "SAMPLE-ap@example.com",
                                 "paid_date": d(paid_bal), "paid_amount_usd": 750 if cid != "SAMPLE-CMP-004" else 600, "method": "bank_transfer",
                                 "bank_reference": "SAMPLE-ACH-%d" % n, "processing_fee_usd": 0,
                                 "_fields_on": {k: d(paid_bal) for k in ("paid_date", "paid_amount_usd", "method", "bank_reference")}})
        if cid == "SAMPLE-CMP-004":
            n += 1
            rows["invoices"].append({"_on": s["placement_confirm"], "invoice_id": "SAMPLE-INV-%03d" % n, "campaign_id": cid, "invoice_type": "credit_note",
                                     "issued_date": s["placement_confirm"], "amount_usd": -150, "sales_tax_usd": 0, "sent_to": "SAMPLE-ap@example.com",
                                     "note": "SAMPLE office SAMPLE-O-007 declined (tree-nut veto) and no roster office could replace it: taken off the balance, brand agreement section 8"})
        oids = [o for o in O10 if not (cid == "SAMPLE-CMP-004" and o == "SAMPLE-O-007")]
        replies = {}
        for i, o in enumerate(O10):
            asked = max(d(signed_on), d(SIGNED[o]))
            replies[o] = ("no", asked + dt.timedelta(days=2)) if (cid == "SAMPLE-CMP-004" and o == "SAMPLE-O-007") else ("yes", asked + dt.timedelta(days=1 + i % 3))
        for o in O10:
            asked = max(d(signed_on), d(SIGNED[o]))
            ov = {o2: base_units[o2] - 3 for o2 in O10} if cid == "SAMPLE-CMP-003" else None
            rows["approvals"] += _approvals(cid, [o], asked, replies, None, ov, override_on=d("2027-01-29") if ov else None)
    order = ["SAMPLE-O-001", "SAMPLE-O-006", "SAMPLE-O-010", "SAMPLE-O-003", "SAMPLE-O-002", "SAMPLE-O-007", "SAMPLE-O-008",
             "SAMPLE-O-004", "SAMPLE-O-005", "SAMPLE-O-009"]
    times = ["08:05", "08:22", "08:40", "09:02", "09:20", "09:38", "09:58", "10:18", "10:40", "11:02"]
    for i, (oid, t) in enumerate(zip(order, times), start=1):
        h, m = map(int, t.split(":"))
        a = tm(h, m + 1)
        b = tm(h + (m + 13) // 60, (m + 13) % 60)
        absent = oid == "SAMPLE-O-009"
        rows["stops"].append({"_on": s["kit_print"], "drop_id": "SAMPLE-DRP-002", "office_id": oid, "route_order": i, "planned_time": tm(h, m),
                              "slack_post_sent_date": s["kit_print"], "confirm_text_sent_date": s["confirm"], "arrival_time": a, "departure_time": b,
                              "handed_to_role": "pantry owner" if not absent else "other staff", "outcome": "handed_to_owner" if not absent else "owner_absent_return",
                              "notes": "SAMPLE owner out of the office; desk will not hold food; founder delivered Wed 08:40" if absent else "",
                              "office_debrief_date": d("2027-02-17"), "office_would_do_again": "yes",
                              "_fields_on": {k: T for k in ("arrival_time", "departure_time", "handed_to_role", "outcome", "notes")} | {"office_debrief_date": d("2027-02-17"), "office_would_do_again": d("2027-02-17")}})
    inv, cnt, ph = [], [], []
    recv = {"SAMPLE-CMP-003": (d("2027-01-29"), 510, "SAMPLE-TG-0115", d("2027-07-31")),
            "SAMPLE-CMP-004": (d("2027-01-28"), 501, "SAMPLE-OR-1220", d("2027-06-30")),
            "SAMPLE-CMP-005": (d("2027-02-01"), 567, "SAMPLE-KR-0122", d("2027-05-15"))}
    for cid, (day, q, lot, bb) in recv.items():
        inv.append({"_on": day, "date": day, "time": tm(14, 0), "campaign_id": cid, "movement": "received", "qty": q, "lot": lot, "best_by": bb,
                    "count_source": "founder_count"})
    alloc = {}
    for a in rows["approvals"]:
        if a["campaign_id"] in CMP and a.get("reply") == "yes":
            alloc[(a["campaign_id"], a["office_id"])] = a.get("units_override") or base_units[a["office_id"]]
    pid = [100]

    def photo(cid, oid, typ, day, t, src="office"):
        pid[0] += 1
        p = "SAMPLE-PH-%04d" % pid[0]
        ph.append({"_on": day, "photo_id": p, "campaign_id": cid, "office_id": oid, "photo_type": typ, "taken_date": day, "taken_time": t,
                   "source": src, "file_name": "%s_%s_%s_%s.jpg" % (cid, oid, typ, day.isoformat()), "received_date": day,
                   "card_visible": "Y", "no_people_or_screens": "Y"})
        return p

    rnd = random.Random(7)
    rem5 = {}
    for (cid, oid), u in sorted(alloc.items()):
        stop = next(x for x in rows["stops"] if x["drop_id"] == "SAMPLE-DRP-002" and x["office_id"] == oid)
        if oid == "SAMPLE-O-009":
            dday, dtime, src = s["placement_confirm"], tm(8, 40), "founder_count"
            pday, ptime = s["placement_confirm"], tm(9, 10)
        else:
            dday, dtime, src = T, stop["arrival_time"], "courier_count"
            pday, ptime = (s["placement_confirm"], tm(9, 30)) if oid == "SAMPLE-O-004" else (T, tm(13, 0))
        inv.append({"_on": dday, "date": dday, "time": dtime, "campaign_id": cid, "office_id": oid, "movement": "delivered", "qty": u, "count_source": src})
        p = photo(cid, oid, "placement", pday, ptime)
        cnt.append({"_on": pday, "date": pday, "time": ptime, "campaign_id": cid, "office_id": oid, "count_type": "placed", "units": u, "source": "photo", "photo_id": p})
        r3 = int(u * rnd.uniform(0.25, 0.6))
        cnt.append({"_on": s["check_day3"], "date": s["check_day3"], "time": tm(11, 0), "campaign_id": cid, "office_id": oid,
                    "count_type": "remaining_day3", "units": r3, "source": "owner_report"})
        top = 0
        if r3 < 0.3 * u and cid != "SAMPLE-CMP-003":
            top = 6
            inv.append({"_on": s["check_day3"], "date": s["check_day3"], "time": tm(13, 0), "campaign_id": cid, "office_id": oid, "movement": "topped_up", "qty": top, "count_source": "founder_count"})
        r5 = max(0, int(r3 * rnd.uniform(0.1, 0.45)))
        rem5[(cid, oid)] = r5
        p2 = photo(cid, oid, "later", s["close"], tm(15, 0))
        cnt.append({"_on": s["close"], "date": s["close"], "time": tm(16, 0), "campaign_id": cid, "office_id": oid, "count_type": "remaining_day5",
                    "units": r5, "source": "photo", "photo_id": p2})
    for cid in CMP:
        good = recv[cid][1]
        used = sum(u for (c, o), u in alloc.items() if c == cid) + sum(x["qty"] for x in inv if x["campaign_id"] == cid and x["movement"] == "topped_up")
        left = good - used
        if CMP[cid][4] == "release":
            inv.append({"_on": s["close"], "date": s["close"], "time": tm(17, 0), "campaign_id": cid, "office_id": "SAMPLE-O-005", "movement": "released_to_office",
                        "bucket": "reserve", "qty": left, "count_source": "founder_count", "note": "SAMPLE brand chose release: reserve to the largest office"})
        else:
            col = sum(v for (c, o), v in rem5.items() if c == cid)
            for (c, o), v in rem5.items():
                if c == cid and v:
                    inv.append({"_on": s["close"], "date": s["close"], "time": tm(16, 30), "campaign_id": cid, "office_id": o, "movement": "collected", "qty": v, "count_source": "founder_count"})
            inv += [{"_on": d("2027-02-19"), "date": d("2027-02-19"), "time": tm(10, 0), "campaign_id": cid, "movement": "returned_to_brand", "bucket": "reserve", "qty": left, "count_source": "founder_count"},
                    {"_on": d("2027-02-19"), "date": d("2027-02-19"), "time": tm(10, 0), "campaign_id": cid, "movement": "returned_to_brand", "bucket": "leftover", "qty": col, "count_source": "founder_count"}]
    rows["inventory"] += inv
    rows["counts"] += cnt
    rows["photos"] += ph
    plans = {}
    for cid in CMP:
        plans[cid] = {o: (6 + (_h((cid, o)) % 5)) for (c, o) in alloc if c == cid}
    plans["SAMPLE-CMP-005"]["SAMPLE-O-010"] = 4
    resp = dict(z["responses"])
    names = {"SAMPLE-CMP-003": "SAMPLE Tallgrass", "SAMPLE-CMP-004": "SAMPLE Orchard Row", "SAMPLE-CMP-005": "SAMPLE Kettle Ridge"}
    quotes = {"SAMPLE-CMP-003": ["SAMPLE Tastes like an oatmeal cookie, in a good way.", "SAMPLE Wish it came in a smaller size.", "SAMPLE Saved one for my kid."],
              "SAMPLE-CMP-004": ["SAMPLE Thick and chewy, nothing like the airport stuff.", "SAMPLE Too sweet for me.", "SAMPLE Where is it sold near here?"],
              "SAMPLE-CMP-005": ["SAMPLE Proper crunch.", "SAMPLE Bag was half air, but good chips.", "SAMPLE Bought a bag at the market after."]}
    for cid in CMP:
        rr = survey(cid, plans[cid], T, s["close"], int(cid[-1]) * 31)
        ensure_comments(rr, T, s["close"], quotes[cid])
        for r in rr:
            r.append(r[0].date())
        resp[cid] = (names[cid], rr)
    scans = []
    for (cid, oid) in sorted(alloc):
        for kind in ("q", "p"):
            close = 4 + (_h((cid, oid, kind)) % 12)
            sl = TR.slug(cid, oid, kind)
            for day, typ, v in ((s["confirm"], "baseline", 1), (s["check_day3"], "mid", max(1, close // 2)), (s["close"], "close", close)):
                scans.append({"_on": day, "read_date": day, "read_time": tm(17, 30), "slug": sl, "reading_type": typ, "clicks_to_date": v})
    rows["scans"] += scans
    rows["redemptions"] += [
        {"_on": s["report_due"], "campaign_id": c, "as_of_date": s["report_due"] - dt.timedelta(days=1), "redemptions_to_date": k, "reported_date": s["report_due"] - dt.timedelta(days=1), "reported_by_role": "SAMPLE brand marketing lead"}
        for c, k in (("SAMPLE-CMP-003", 9), ("SAMPLE-CMP-004", 5), ("SAMPLE-CMP-005", 12))] + [
        {"_on": T + dt.timedelta(days=30), "campaign_id": c, "as_of_date": T + dt.timedelta(days=30), "redemptions_to_date": k, "reported_date": T + dt.timedelta(days=30), "reported_by_role": "SAMPLE brand marketing lead"}
        for c, k in (("SAMPLE-CMP-003", 17), ("SAMPLE-CMP-004", 8), ("SAMPLE-CMP-005", 21))]
    rows["issues"] += [
        {"_on": d("2027-01-29"), "issue_id": "SAMPLE-ISS-004", "date": d("2027-01-29"), "time": tm(14, 30), "drop_id": "SAMPLE-DRP-002", "campaign_id": "SAMPLE-CMP-003",
         "issue_type": "short_shipment", "what_happened": "SAMPLE 510 units arrived; 567 were due (515 plus reserve).", "action_taken": "SAMPLE each office's units reduced by 3 (485), reserve 25; brand told the same day.",
         "brand_told_date": d("2027-01-29"), "closed_date": d("2027-01-29")},
        {"_on": d("2027-01-08"), "issue_id": "SAMPLE-ISS-005", "date": d("2027-01-08"), "time": tm(10, 0), "drop_id": "SAMPLE-DRP-002", "campaign_id": "SAMPLE-CMP-004", "office_id": "SAMPLE-O-007",
         "issue_type": "other", "what_happened": "SAMPLE office vetoes tree nuts; the package says packed in a facility that also handles tree nuts.", "action_taken": "SAMPLE office said no; no roster office free; $150 off the balance.",
         "office_told_date": d("2027-01-08"), "brand_told_date": d("2027-01-08"), "closed_date": s["placement_confirm"]},
        {"_on": T, "issue_id": "SAMPLE-ISS-006", "date": T, "time": tm(11, 3), "drop_id": "SAMPLE-DRP-002", "office_id": "SAMPLE-O-009", "issue_type": "owner_absent",
         "what_happened": "SAMPLE owner out; desk does not hold food (front desk not agreed). Courier brought all three cases back.", "action_taken": "SAMPLE founder delivered Wed 08:40; placed 09:10, inside one business day.",
         "office_told_date": T, "closed_date": s["placement_confirm"]},
    ]
    H = []

    def hrs(day, act, h, cid="", did="SAMPLE-DRP-002", note=""):
        H.append({"_on": day, "date": day, "drop_id": did, "campaign_id": cid, "activity": act, "hours": h, "note": note})
    for cid, (bid, signed_on, *_r) in CMP.items():
        for k in range(3):
            hrs(opscal.add_bd(d(signed_on), -5 * k), "brand_sales", 2.0, cid, note="SAMPLE calls, proposal, agreement")
        hrs(s["report_due"], "reporting_debriefs", 1.5, cid, note="SAMPLE report")
        hrs(s["debrief"], "reporting_debriefs", 0.5, cid, note="SAMPLE debrief and renewal proposal")
    for k, day in enumerate((d("2027-01-05"), d("2027-01-06"), d("2027-01-07"), d("2027-01-08"), d("2027-01-13"))):
        hrs(day, "office_coordination", 1.5, note="SAMPLE signing a new office")
    for day in (d("2027-01-20"), d("2027-02-01")):
        hrs(day, "office_coordination", 1.25, note="SAMPLE approvals, windows, certificates")
    hrs(d("2027-01-29"), "receiving_kitting", 1.0); hrs(d("2027-02-01"), "receiving_kitting", 1.0); hrs(s["confirm"], "receiving_kitting", 2.0)
    hrs(T, "drop_day", 6.5, note="SAMPLE meet the courier at five first-drop offices"); hrs(s["placement_confirm"], "drop_day", 1.5, note="SAMPLE redeliver office SAMPLE-O-009")
    hrs(s["check_day3"], "checks_pickup", 2.0); hrs(s["close"], "checks_pickup", 2.0)
    hrs(d("2027-01-04"), "admin_invoicing", 1.0); hrs(s["placement_confirm"], "admin_invoicing", 1.0)
    rows["hours"] += H
    rows["costs"] += [
        {"_on": s["kit_print"], "date": s["kit_print"], "drop_id": "SAMPLE-DRP-002", "campaign_id": "SAMPLE-CMP-003", "cost_type": "kit", "amount_usd": 80, "vendor": "SAMPLE copy shop"},
        {"_on": s["kit_print"], "date": s["kit_print"], "drop_id": "SAMPLE-DRP-002", "campaign_id": "SAMPLE-CMP-004", "cost_type": "kit", "amount_usd": 72, "vendor": "SAMPLE copy shop"},
        {"_on": s["kit_print"], "date": s["kit_print"], "drop_id": "SAMPLE-DRP-002", "campaign_id": "SAMPLE-CMP-005", "cost_type": "kit", "amount_usd": 80, "vendor": "SAMPLE copy shop"},
        {"_on": T, "date": T, "drop_id": "SAMPLE-DRP-002", "cost_type": "transport", "amount_usd": 320, "vendor": "SAMPLE Example Courier", "note": "SAMPLE 10 stops at $32"},
        {"_on": T, "date": T, "drop_id": "SAMPLE-DRP-002", "cost_type": "transport", "amount_usd": 38, "vendor": "SAMPLE car service", "note": "SAMPLE founder to first-drop offices"},
    ]
    learned = {"SAMPLE-CMP-003": "SAMPLE Shipped 57 short; every office got 3 fewer.\nSAMPLE Bars lasted longer than chips in most offices.\nSAMPLE Size came up: one comment asked for a smaller bar.",
               "SAMPLE-CMP-004": "SAMPLE One office declined over a tree-nut veto; ask about may-contain lines at approval.\nSAMPLE Went fastest in the two largest offices.\nSAMPLE Sweetness split the comments.",
               "SAMPLE-CMP-005": "SAMPLE Office J reached four responses, under the five it committed to.\nSAMPLE Chips ran out by day 3 in four offices.\nSAMPLE Fill level of the bag came up once."}
    rec = {"SAMPLE-CMP-003": "SAMPLE Renew into the same ten offices with a smaller bar if you make one.",
           "SAMPLE-CMP-004": "SAMPLE Renew into offices with no tree-nut veto; same card.",
           "SAMPLE-CMP-005": "SAMPLE Renew with 20% more units for the four offices that ran out."}
    for r in rows["campaigns"]:
        cid = r["campaign_id"]
        if cid not in CMP:
            continue
        r.update(comment_1=quotes[cid][0], comment_2=quotes[cid][1], comment_3=quotes[cid][2], learned=learned[cid], recommendation=rec[cid],
                 report_delivered_date=s["report_due"], debrief_date=s["debrief"], brand_would_buy_again="yes" if cid != "SAMPLE-CMP-004" else "maybe",
                 renewed="Y" if cid == "SAMPLE-CMP-003" else "pending", renewal_note="SAMPLE renews into the March drop" if cid == "SAMPLE-CMP-003" else "")
        f = r["_fields_on"]
        for k in ("comment_1", "comment_2", "comment_3", "learned", "recommendation"):
            f[k] = opscal.add_bd(T, 6)
        f.update(report_delivered_date=s["report_due"], debrief_date=s["debrief"], brand_would_buy_again=s["debrief"], renewed=s["debrief"], renewal_note=s["debrief"])
        if r["newsletter_option"] == "Y":
            r.update(newsletter_passed_date=s["pass_on"], newsletter_passed_count=4, newsletter_unticked_deleted_date=s["pass_on"], newsletter_deleted_date=s["newsletter_delete"])
            f.update(newsletter_passed_date=s["pass_on"], newsletter_passed_count=s["pass_on"], newsletter_unticked_deleted_date=s["pass_on"], newsletter_deleted_date=s["newsletter_delete"])
    return {"name": "standard", "T": T, "drop_id": "SAMPLE-DRP-002", "rows": rows, "responses": resp,
            "campaigns": list(CMP), "offices": O10, "delivery_model": "courier"}


def _h(x):
    """Deterministic stand-in for hash() (Python randomizes hash() per process)."""
    return sum((i + 1) * ord(ch) for i, ch in enumerate(str(x)))


def copy_rows(rows):
    import copy
    return copy.deepcopy(rows)


# ---------------------------------------------------------------- exception run (review round 1)
BRANDS["SAMPLE-BR-006"] = dict(name="SAMPLE Saltmarsh", cat="chips-crisps", sku="SAMPLE Salt and Vinegar Potato Chips, 1 oz bags",
                               city="SAMPLE Montauk, NY", site="https://example.com/saltmarsh", via="website", submitted="2027-01-11T09:40:00-05:00")


def exception():
    """SAMPLE Saltmarsh, standard, 10 offices, courier, drop Tue 2027-02-23 (SAMPLE-DRP-003). Built from the reviewer's
    round-1 scenario (campaign-ops/_review/work/scenario_exception.py), with the SOP as it now reads:
    - short shipment: 480 of 567 arrive on Fri 2027-02-12; every office gets 5 fewer (units_override), issue logged;
    - SAMPLE-O-006 declines at the door on T: stops outcome declined, NO delivered row (its case stays in reserve),
      issue declined_at_door, $150 credit note taken off the balance at T+1;
    - the courier writes the handed-over count on the route sheet (courier_count) and brings the case back."""
    import opscal
    import tracker as TR
    st = standard()
    T = d("2027-02-23")
    s = opscal.sop_dates(T)
    O10 = [o[0] for o in OFFICES]
    rows = copy_rows(st["rows"])
    cid, bid, signed_on, paid_on = "SAMPLE-CMP-006", "SAMPLE-BR-006", d("2027-01-25"), d("2027-01-28")
    bweb, bform, brands = brand_rows([bid])
    for r in brands:
        r["_on"] = min(r["_on"], signed_on)
    rows["brand_intake"] += bweb
    rows["brand_form"] += bform
    rows["brands"] += brands
    rows["drops"].append({"_on": d("2027-01-20"), "drop_id": "SAMPLE-DRP-003", "drop_date": T, "delivery_model": "courier", "status": "confirmed",
                          "receiving_location": "SAMPLE receiving address (founder's home, sealed cases)",
                          "courier_or_van": "SAMPLE Example Courier, booking SAMPLE-BK-0223, pickup 7:45 am", "backup_person": "SAMPLE backup (briefed 2027-02-19)",
                          "notes": "SAMPLE second standard run (exception run)"})
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
         "note": "SAMPLE one office declined at the door and was not placed by T+1: taken off the balance, brand agreement section 8"},
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
                              "notes": "SAMPLE owner declined at the door: office pausing snacks this month; courier brought the case back (0 handed over)" if dec else "",
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
    for oid in O10:
        u = ov[oid]
        stop = next(x for x in rows["stops"] if x["drop_id"] == "SAMPLE-DRP-003" and x["office_id"] == oid)
        if oid == "SAMPLE-O-006":
            continue   # SOP section 4: declined at the door = no delivered row; the case stays in reserve
        inv.append({"_on": T, "date": T, "time": stop["arrival_time"], "campaign_id": cid, "office_id": oid, "movement": "delivered", "qty": u, "count_source": "courier_count"})
        p = photo(oid, "placement", T, tm(13, 0))
        cnt.append({"_on": T, "date": T, "time": tm(13, 0), "campaign_id": cid, "office_id": oid, "count_type": "placed", "units": u, "source": "photo", "photo_id": p})
        r3 = int(u * rnd.uniform(0.2, 0.5))
        cnt.append({"_on": s["check_day3"], "date": s["check_day3"], "time": tm(11, 0), "campaign_id": cid, "office_id": oid, "count_type": "remaining_day3", "units": r3, "source": "owner_report"})
        if oid in tops:
            inv.append({"_on": s["check_day3"], "date": s["check_day3"], "time": tm(13, 0), "campaign_id": cid, "office_id": oid, "movement": "topped_up", "qty": tops[oid], "count_source": "founder_count"})
        r5 = max(0, int(r3 * rnd.uniform(0.1, 0.4)))
        p2 = photo(oid, "later", s["close"], tm(15, 0))
        cnt.append({"_on": s["close"], "date": s["close"], "time": tm(16, 0), "campaign_id": cid, "office_id": oid, "count_type": "remaining_day5", "units": r5, "source": "photo", "photo_id": p2})
    # Physical reserve at close: 480 received - delivered - top-ups (the declined case included). Counted and released (brand chose release).
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
         "action_taken": "SAMPLE each office's units reduced by 5 (465), reserve 15; brand told the same day; no price change (brand agreement section 8 is silent).",
         "brand_told_date": short_on, "closed_date": short_on},
        {"_on": T, "issue_id": "SAMPLE-ISS-021", "date": T, "time": tm(8, 23), "drop_id": "SAMPLE-DRP-003", "campaign_id": cid, "office_id": "SAMPLE-O-006",
         "issue_type": "declined_at_door", "what_happened": "SAMPLE owner declined at the door: the office is pausing snacks this month.",
         "action_taken": "SAMPLE courier took the case back (0 handed over) and returned it to the receiving address; it stayed in reserve; $150 taken off the balance.",
         "office_told_date": T, "brand_told_date": s["placement_confirm"], "closed_date": s["placement_confirm"]},
    ]
    H = []

    def hrs(day, act, h, c="", note=""):
        H.append({"_on": day, "date": day, "drop_id": "SAMPLE-DRP-003", "campaign_id": c, "activity": act, "hours": h, "note": note})
    for k in range(3):
        hrs(opscal.add_bd(signed_on, -3 * k), "brand_sales", 2.0, cid, "SAMPLE calls, proposal, agreement")
    hrs(d("2027-01-26"), "office_coordination", 1.5, note="SAMPLE approvals")
    hrs(short_on, "receiving_kitting", 1.5, note="SAMPLE receive, count, short shipment email")
    hrs(s["confirm"], "receiving_kitting", 1.5, note="SAMPLE pack ten cases")
    hrs(T, "drop_day", 4.0, note="SAMPLE courier route; founder on call")
    hrs(s["check_day3"], "checks_pickup", 1.5)
    hrs(s["close"], "checks_pickup", 1.5)
    hrs(s["report_due"], "reporting_debriefs", 1.5, cid, "SAMPLE report")
    hrs(s["debrief"], "reporting_debriefs", 0.5, cid, "SAMPLE debrief")
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
