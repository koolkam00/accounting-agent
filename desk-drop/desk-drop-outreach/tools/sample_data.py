"""SAMPLE data for the conversation tracker test.

Every ID and every free-text value starts with SAMPLE. Nothing here is a real
office, brand, person, quote or result. Illustrative placeholders, not results.
Generic words (job titles, category keys) are not prefixed.
"""
import datetime as dt

D = dt.date
AS_OF = D(2026, 12, 11)   # Gate 1 day; fixed so the test does not depend on the day it runs
START = D(2026, 10, 26)   # week 1 Monday; no outreach before this
DOMAIN_EMAIL_FROM = D(2026, 11, 9)   # week 3 Monday: the earliest first cold email from the new domain (sending guide, review round 1)
HOLIDAYS = {D(2026, 11, 11)}


def add_bd(d, n):
    """Add n business days (negative to go back), skipping weekends and the federal holiday."""
    step = 1 if n >= 0 else -1
    k = 0
    while k != n:
        d += dt.timedelta(days=step)
        if d.weekday() < 5 and d not in HOLIDAYS:
            k += step
    return d

# ---------------------------------------------------------------- office log
# one row per conversation; SAMPLE-O-001 has two calls (second row near the end)
_o = [
    # rid, date, yes, owner_named, window, headcount, bp_verbatim, bp_low, bp_high, asked, spend, objections (codes), note_min, call_type, channel
    ("SAMPLE-O-001", D(2026, 10, 27), "Y", "Y", "SAMPLE Tue-Wed 9-11am", 60, "SAMPLE: maybe $100 to $200 a month", 100, 200, "Y", 800, ["allergy_policy"], 9, "video", "warm-intro"),
    ("SAMPLE-O-002", D(2026, 10, 28), "Y", "Y", "", 45, "SAMPLE: honestly, no budget for that", 0, 0, "Y", 400, ["existing_vendor", "allergy_policy"], 12, "phone", "linkedin"),
    ("SAMPLE-O-003", D(2026, 10, 29), "N", "N", "", 120, "SAMPLE: I don't know", None, None, "Y", None, ["vendor_fatigue"], 8, "walk-in", "walk-in"),
    ("SAMPLE-O-004", D(2026, 11, 2), "Y", "Y", "SAMPLE mornings before 10", 90, "SAMPLE: around $300 a month", 300, 300, "Y", 1500, ["needs_approval"], 10, "video", "linkedin"),
    ("SAMPLE-O-005", D(2026, 11, 3), "maybe", "N", "", 150, "SAMPLE: zero, it would come out of my budget", 0, 0, "Y", None, ["needs_approval", "building_receiving"], 7, "phone", "linkedin"),
    ("SAMPLE-O-006", D(2026, 11, 4), "Y", "Y", "SAMPLE Tue 8-10am", 55, "SAMPLE: fifty dollars, maybe", 50, 50, "Y", 300, ["allergy_policy"], 11, "in-person", "walk-in"),
    ("SAMPLE-O-007", D(2026, 11, 5), "N", "Y", "", 200, "SAMPLE: wouldn't want to say", None, None, "Y", 2500, ["commitments_too_much"], 6, "video", "linkedin"),
    ("SAMPLE-O-008", D(2026, 11, 9), "Y", "Y", "SAMPLE Wed 9-12", 70, "SAMPLE: we would not pay", 0, 0, "Y", 600, ["allergy_policy", "needs_approval"], 10, "phone", "warm-intro"),
    ("SAMPLE-O-009", D(2026, 11, 10), "N", "N", "", 35, "", None, None, "N", None, ["existing_vendor"], 5, "phone", "linkedin"),
    ("SAMPLE-O-010", D(2026, 11, 10), "Y", "Y", "SAMPLE Tue 10-11", 110, "SAMPLE: $200 to $400 if the team votes on it", 200, 400, "Y", 1200, [], 9, "video", "warm-intro"),
    ("SAMPLE-O-011", D(2026, 11, 12), "Y", "N", "SAMPLE Tue 9-11", 80, "", None, None, "N", None, ["needs_approval"], 8, "phone", "linkedin"),
    ("SAMPLE-O-012", D(2026, 11, 12), "maybe", "Y", "", 95, "SAMPLE: a hundred a month, tops", 100, 100, "Y", 900, ["building_receiving"], 13, "video", "linkedin"),
    ("SAMPLE-O-013", D(2026, 11, 13), "Y", "Y", "SAMPLE Tue 9am", 65, "", None, None, "N", None, [], 9, "in-person", "walk-in"),
    ("SAMPLE-O-001", D(2026, 11, 6), "Y", "Y", "SAMPLE Tue-Wed 9-11am", 62, "SAMPLE: $150 a month", 150, 150, "Y", 800, ["allergy_policy"], 6, "phone", "warm-intro"),
    ("SAMPLE-O-014", D(2026, 11, 16), "Y", "Y", "SAMPLE Wed 8-9am", 75, "", None, None, "N", None, ["needs_approval"], 9, "video", "email"),
    # review round 2 (R2-02): a withdrawn yes. O-004 said yes with an owner and a window on 11-02, then no on 11-12;
    # it must not count for Gate 0 on 11-13, and the pipeline export must not carry its yes
    ("SAMPLE-O-004", D(2026, 11, 12), "N", "Y", "", 90, "", None, None, "N", None, ["needs_approval"], 8, "phone", "linkedin"),
]

OFFICE_LOG = []
for i, (rid, d, yes, own, win, hc, bpv, lo, hi, asked, spend, objs, nm, ct, ch) in enumerate(_o, start=1):
    n = int(rid[-3:])
    OFFICE_LOG.append({
        "row_id": rid, "company": f"SAMPLE Office {n:02d}", "contact_name": f"SAMPLE Contact O{n:02d}",
        "contact_title": "Office Manager" if n % 2 else "Workplace Experience Manager",
        "source": "SAMPLE warm network" if ch == "warm-intro" else "SAMPLE Clay offices table",
        "channel": ch, "call_date": d, "call_type": ct,
        "q1_pantry_today_verbatim": f"SAMPLE: pantry answer {n:02d}", "pantry_vendor": "SAMPLE snack service" if n % 3 == 0 else "SAMPLE grocery order",
        "uses_snack_service": "Y" if n % 3 == 0 else "N", "q3_brands_reach_out": "Y" if n % 2 else "N",
        "monthly_pantry_spend_usd": spend, "monthly_pantry_spend_verbatim": f"SAMPLE: about ${spend} a month" if spend else "",
        "tuesday_headcount": hc, "headcount_verbatim": f"SAMPLE: around {hc} on a Tuesday",
        "q3_free_product_verbatim": "SAMPLE: brands email us, we ignore most",
        "q4_yes_needs_verbatim": "SAMPLE: allergen info and no work for me", "q4_no_triggers_verbatim": "SAMPLE: anything with nuts",
        "q5_photo_and_survey": "Y" if yes == "Y" else "maybe", "q5_verbatim": "SAMPLE: a photo is fine",
        "budget_probe_asked": asked, "budget_probe_verbatim": bpv, "budget_probe_low_usd": lo, "budget_probe_high_usd": hi,
        "referrals_given_count": 1 if n in (1, 10) else 0, "referrals_given": "SAMPLE Office 30 - Office Manager" if n in (1, 10) else "",
        "pantry_owner_named": own, "pantry_owner_name": f"SAMPLE Owner O{n:02d}" if own == "Y" else "",
        "pantry_owner_title": "Office Manager" if own == "Y" else "", "owner_can_say_yes_alone": "Y" if yes == "Y" else "N",
        "other_approver": "" if yes == "Y" else ("facilities" if n % 2 else "hr"),
        "receiving_window": win, "receiving_type": "front desk" if n % 3 else "walk-up", "coi_required": "unsure" if n % 4 == 0 else "no",
        "security_notes": "SAMPLE: sign in at desk" if n % 3 else "",
        "veto_categories": "meat-snacks" if n % 2 else "chocolate-candy;sparkling-soda", "veto_verbatim": "SAMPLE: no jerky",
        "objection_1": objs[0] if len(objs) > 0 else "", "objection_2": objs[1] if len(objs) > 1 else "",
        "objection_3": objs[2] if len(objs) > 2 else "",
        "objections_verbatim": ("SAMPLE: " + " / ".join(objs) + f" (office {n:02d})") if objs else "",
        "yes_in_principle": yes, "yes_signals": "asked_when" if yes == "Y" else "",
        "shortlist": "Y" if (yes == "Y" and own == "Y") or n in (5, 12) else "",
        "quote_ok_to_share": "Y" if n in (1, 4, 8) else "",
        "note_minutes": nm, "clay_updated": "Y", "notes": "",
    })

# ---------------------------------------------------------------- brand log
_b = [
    # rid, date, before_usd, before_verbatim, controls, mentioned, after_usd, after_verbatim, objections, note_min
    ("SAMPLE-B-001", D(2026, 10, 27), 500, "SAMPLE: maybe $500 for that", "Y", "Y", 800, "SAMPLE: $1,500 is steep, $800 maybe", ["price_per_sample", "what_we_get"], 10),
    ("SAMPLE-B-002", D(2026, 10, 28), 250, "SAMPLE: a couple hundred", "Y", "Y", 600, "SAMPLE: at $600 for five offices, yes", ["price_per_sample"], 9),
    ("SAMPLE-B-003", D(2026, 10, 29), None, "SAMPLE: no idea what that's worth", "Y", "Y", 0, "SAMPLE: not at that price", ["seed_ourselves", "price_per_sample"], 8),
    ("SAMPLE-B-004", D(2026, 11, 2), 1000, "SAMPLE: a thousand, but my cofounder decides", "N", "Y", 1500, "SAMPLE: $1,500 could work", ["what_we_get"], 11),
    ("SAMPLE-B-005", D(2026, 11, 3), 0, "SAMPLE: we would want it free", "Y", "N", None, "", ["free_trial", "seed_ourselves"], 7),
    ("SAMPLE-B-006", D(2026, 11, 4), 750, "SAMPLE: $750 feels right", "Y", "Y", 1200, "SAMPLE: we could stretch to $1,200", ["what_we_get"], 10),
    ("SAMPLE-B-007", D(2026, 11, 5), 300, "SAMPLE: $300", "Y", "Y", 300, "SAMPLE: still $300", ["price_per_sample", "budget_timing"], 9),
    ("SAMPLE-B-008", D(2026, 11, 9), 2000, "SAMPLE: we spend $2,000 a weekend on demos", "Y", "N", None, "", ["want_sales_data"], 12),
    ("SAMPLE-B-009", D(2026, 11, 10), None, "", "Y", "N", None, "", [], 6),
    ("SAMPLE-B-010", D(2026, 11, 11), 400, "SAMPLE: $400 tops", "N", "N", None, "", ["seed_ourselves", "free_trial"], 8),
    ("SAMPLE-B-011", D(2026, 11, 12), 600, "SAMPLE: $600", "Y", "Y", 900, "SAMPLE: $900", ["budget_timing"], 10),
    ("SAMPLE-B-002", D(2026, 11, 12), None, "", "Y", "Y", 700, "SAMPLE: $700 on reflection", [], 5),
    ("SAMPLE-B-012", D(2026, 11, 13), 100, "SAMPLE: a hundred bucks", "Y", "N", None, "", ["inventory"], 9),
    ("SAMPLE-B-013", D(2026, 11, 13), 500, "SAMPLE: five hundred", "Y", "N", None, "", [], 9),
    ("SAMPLE-B-014", D(2026, 11, 17), 900, "SAMPLE: $900", "Y", "Y", 1500, "SAMPLE: fine at $1,500", ["shelf_life"], 10),
    ("SAMPLE-B-015", D(2026, 11, 18), 50, "SAMPLE: fifty", "N", "N", None, "", ["not_our_audience"], 7),
]

BRAND_LOG = []
for (rid, d, wb, wbv, ctl, men, wa, wav, objs, nm) in _b:
    n = int(rid[-3:])
    BRAND_LOG.append({
        "row_id": rid, "company": f"SAMPLE Brand {n:02d}", "contact_name": f"SAMPLE Contact B{n:02d}",
        "contact_title": "Founder" if n % 2 else "Head of Marketing", "source": "SAMPLE Clay brands table",
        "channel": ("email" if d >= D(2026, 11, 16) else "warm-intro") if n % 3 else "linkedin", "call_date": d, "call_type": "video",
        "q1_trial_now_verbatim": "SAMPLE: demos at two stores", "q2_sampling_budget_quarter_low_usd": 1000 * (n % 5),
        "q2_sampling_budget_quarter_high_usd": 1000 * (n % 5) + 500, "q2_budget_verbatim": "SAMPLE: a few thousand a quarter",
        "budget_approver": "SAMPLE: me" if ctl == "Y" else "SAMPLE: my cofounder", "controls_budget": ctl,
        "q3_seeded_offices": "N", "q3_verbatim": "SAMPLE: never tried offices",
        "qual_q1_sealed_shelf_stable_60d": "Y" if n % 4 else "unsure", "qual_q2_labeled_ingredients_allergens": "Y",
        "qual_q3_buy_path_near_cluster": "Y" if n != 12 else "N", "qual_q4_can_ship_275_in_10bd": "Y" if n % 5 else "unsure",
        "qual_q5_product_liability_insurance": "Y" if n != 7 else "N", "qual_q6_contact_can_approve_600": ctl,
        "qual_q7_why_now": "SAMPLE: new store near the cluster" if n % 2 else "", "qual_not_excluded": "Y",
        "wtp_before_usd": wb, "wtp_before_verbatim": wbv, "wtp_unit_note": "",
        "price_1500_mentioned": men, "wtp_after_usd": wa, "wtp_after_verbatim": wav,
        "q5_report_needs_verbatim": "SAMPLE: photos and what people said", "q6_buy_path_type": "retailer-in-cluster" if n % 2 else "online-with-code",
        "q6_buy_path_verbatim": "SAMPLE Store, SAMPLE street", "q7_stoppers_verbatim": "SAMPLE: budget timing",
        "objection_1": objs[0] if len(objs) > 0 else "", "objection_2": objs[1] if len(objs) > 1 else "",
        "objection_3": objs[2] if len(objs) > 2 else "",
        "objections_verbatim": ("SAMPLE: " + " / ".join(objs) + f" (brand {n:02d})") if objs else "",
        "yes_in_principle": "Y" if (ctl == "Y" and max(wb or 0, wa or 0) >= 500) else "N",
        "shortlist": "Y" if (ctl == "Y" and max(wb or 0, wa or 0) >= 500) else "",
        "quote_ok_to_share": "Y" if n in (1, 6) else "",
        "referrals_given_count": 0, "referrals_given": "", "note_minutes": nm, "clay_updated": "Y", "notes": "",
    })

# ---------------------------------------------------------------- Clay pastes
# Columns deliberately in a different order from CONTRACTS, with one extra enrichment column,
# to prove the tracker finds columns by header name.
CLAY_HEADERS = ["SAMPLE_extra_enrichment", "company", "row_id", "first_name", "last_name", "title", "contact_linkedin_url",
                "work_email", "email_status", "channel", "score", "score_reason", "onsite_band", "nearest_stocked_retailer",
                "nearest_retailer_grade", "why_now", "why_now_url", "why_now_date", "known_to_founder", "startup_cpg_member",
                "status", "do_not_contact", "source_url", "found_date",
                "touch_1_date", "sequence", "touch_2_date", "touch_3_date", "last_reply_date", "reply_type", "call_date",
                "call_notes", "yes_in_principle", "next_action", "next_action_date", "opt_out_date", "referral_from",
                "company_group"]      # A's group key: the row_id for a row on its own (review round 3)


def _clay_rows(side, log):
    letter = "O" if side == "office" else "B"
    rows = []
    logged = {}
    for r in log:
        logged.setdefault(r["row_id"], []).append(r)
    reply_cycle = ["", "", "no", "opt_out", "bounce", "out_of_office", "not_now", "", "maybe", ""]
    days = [START + dt.timedelta(days=k) for k in range(0, 26)]
    weekdays = [d for d in days if d.weekday() < 5 and d not in HOLIDAYS]
    for n in range(1, 41):
        rid = f"SAMPLE-{letter}-{n:03d}"
        if side == "office" and n == 14:
            continue                       # planted: logged office missing from the Clay paste
        t1 = weekdays[(n * 3) % len(weekdays)]
        row = {h: "" for h in CLAY_HEADERS}
        row.update({"SAMPLE_extra_enrichment": f"SAMPLE enrichment {n}", "company": f"SAMPLE {'Office' if side == 'office' else 'Brand'} {n:02d}",
                    "row_id": rid, "first_name": "SAMPLE", "last_name": f"Contact {letter}{n:02d}", "title": "Office Manager" if side == "office" else "Founder",
                    "email_status": "verified", "channel": "email" if n % 4 else "linkedin", "score": 100 - n,
                    "score_reason": "SAMPLE: score reason", "do_not_contact": "N", "status": "contacted",
                    "sequence": f"{side}-discovery-{'A' if n % 2 else 'B'}", "touch_1_date": t1, "found_date": D(2026, 10, 22),
                    "company_group": rid})
        if row["channel"] == "email" and t1 < DOMAIN_EMAIL_FROM:
            row["channel"] = "linkedin"
        if n % 5 != 0:
            row["touch_2_date"] = add_bd(t1, 3)
        if n % 7 == 1:
            row["touch_3_date"] = add_bd(t1, 7)
        if rid in logged:
            calls = sorted(logged[rid], key=lambda r: r["call_date"])
            first, last = calls[0], calls[-1]
            row["touch_1_date"] = max(add_bd(first["call_date"], -4), START)
            row["touch_2_date"] = ""
            row["touch_3_date"] = ""
            row["last_reply_date"] = min(add_bd(row["touch_1_date"], 1), first["call_date"])
            row["reply_type"] = "yes"
            row["call_date"] = last["call_date"]
            # Clay's yes_in_principle follows the latest answer (review round 2, R2-02)
            answered = [c for c in calls if c["yes_in_principle"] in ("Y", "N", "maybe")]
            standing = bool(answered) and answered[-1]["yes_in_principle"] == "Y"
            row["yes_in_principle"] = "Y" if standing else "N"
            row["status"] = "yes_in_principle" if standing else "call_done"
            row["call_notes"] = f"SAMPLE: see tracker {last['call_date'].isoformat()}"
            row["channel"] = first["channel"]
        else:
            rt = reply_cycle[n % len(reply_cycle)]
            row["reply_type"] = rt
            if rt in ("no", "opt_out", "not_now", "maybe", "out_of_office"):
                row["last_reply_date"] = add_bd(t1, 1)
            if rt == "opt_out":
                row["status"], row["do_not_contact"], row["opt_out_date"] = "do_not_contact", "Y", add_bd(t1, 1)
            elif rt == "no":
                row["status"] = "no"
            elif rt == "not_now":
                row["status"], row["next_action"], row["next_action_date"] = "not_now", "recontact", D(2027, 1, 19)
            elif rt == "maybe":
                row["status"] = "replied"
            elif rt == "bounce":
                row["email_status"] = "none"
        rows.append(row)
    return rows


CLAY_OFFICES = _clay_rows("office", OFFICE_LOG)
CLAY_BRANDS = _clay_rows("brand", BRAND_LOG)


def _set(rows, rid, **kw):
    for r in rows:
        if r["row_id"] == rid:
            r.update(kw)
            return
    raise KeyError(rid)


# planted sync problems (each must show up on the tracker's checks)
_set(CLAY_OFFICES, "SAMPLE-O-004", status="replied")                    # logged call, Clay still says replied
_set(CLAY_OFFICES, "SAMPLE-O-006", yes_in_principle="")                 # Clay yes_in_principle not copied
_set(CLAY_OFFICES, "SAMPLE-O-020", status="call_done", reply_type="yes", last_reply_date=D(2026, 11, 3))  # no tracker row
_set(CLAY_OFFICES, "SAMPLE-O-030", do_not_contact="Y")                  # flag Y but status contacted
for _rid in ("SAMPLE-O-001", "SAMPLE-O-006", "SAMPLE-O-008", "SAMPLE-O-010", "SAMPLE-O-013"):
    _set(CLAY_OFFICES, _rid, status="signed")                           # match signed_offices (five, review round 2)
_set(CLAY_BRANDS, "SAMPLE-B-009", status="call_booked")                 # logged call, Clay still says call_booked
_set(CLAY_BRANDS, "SAMPLE-B-021", status="paid")                        # no paid_brands row
_set(CLAY_BRANDS, "SAMPLE-B-001", status="paid")                        # matches paid_brands

# ---------------------------------------------------------------- handoff rows
SIGNED_OFFICES = [{
    "submitted_at": "2026-11-23 10:14", "form_version": "office-1.0", "company": "SAMPLE Office 01",
    "contact_name": "SAMPLE Contact O01", "contact_title": "Office Manager", "contact_email": "SAMPLE-contact@SAMPLE-office-01.example",
    "contact_phone": "SAMPLE 000-000-0000", "office_address": "SAMPLE 1 Example Street, New York, NY", "floor_suite": "SAMPLE Floor 4",
    "tuesday_headcount": 62, "pantry_owner_name": "SAMPLE Owner O01", "pantry_owner_title": "Office Manager",
    "pantry_owner_is_contact": "N", "receiving_type": "front desk", "receiving_window": "SAMPLE Tue-Wed 9-11am",
    "coi_required": "no", "survey_channel": "slack", "categories_wanted": "bars;sparkling-soda;chips-crisps",
    "vetoes": "meat-snacks", "notes": "SAMPLE: prefers low-sugar options", "source": "founder",
    "office_id": "SAMPLE-O-###", "clay_row_id": "SAMPLE-O-001", "agreement_signed_date": D(2026, 11, 24),
    "agreement_file": "SAMPLE-participation-agreement-office-01.pdf", "founding_roster_named": "N",
    # budget_probe_verbatim, budget_probe_date, budget_probe_monthly_usd are formulas from Office_Log
    "agreement_version": "0.8", "owner_can_say_yes_alone": "Y",
    "industry": "SAMPLE software", "pantry_owner_phone": "SAMPLE 000-000-0002", "pantry_owner_email": "SAMPLE-owner@SAMPLE-office-01.example",
    "public_naming_ok": "N", "building_id": "SAMPLE-B-B-001",
}]
SIGNED_OFFICES[0]["office_id"] = "SAMPLE-O-101"
# review round 2 (R2-16): the SAMPLE data obeys the gate it illustrates. Five offices sign before any brand agreement
# (the paid brand's agreement is Tue 2026-12-01), and all five approve the brand (office_approvals).
for _k, (_rid, _signed, _hc, _win) in enumerate((("SAMPLE-O-006", D(2026, 11, 23), 55, "SAMPLE Tue 8-10am"),
                                                  ("SAMPLE-O-008", D(2026, 11, 24), 70, "SAMPLE Wed 9-12"),
                                                  ("SAMPLE-O-010", D(2026, 11, 25), 110, "SAMPLE Tue 10-11"),
                                                  ("SAMPLE-O-013", D(2026, 11, 30), 65, "SAMPLE Tue 9am")), start=2):
    _n = int(_rid[-2:])
    _row = dict(SIGNED_OFFICES[0])
    _row.update({"submitted_at": f"{(_signed - dt.timedelta(days=3)).isoformat()} 11:0{_k}", "company": f"SAMPLE Office {_n:02d}",
                 "contact_name": f"SAMPLE Contact O{_n:02d}", "contact_email": f"SAMPLE-contact@SAMPLE-office-{_n:02d}.example",
                 "office_address": f"SAMPLE {_n} Example Street, New York, NY", "floor_suite": f"SAMPLE Floor {_k + 2}",
                 "tuesday_headcount": _hc, "pantry_owner_name": f"SAMPLE Owner O{_n:02d}", "receiving_window": _win,
                 "office_id": f"SAMPLE-O-10{_k}", "clay_row_id": _rid, "agreement_signed_date": _signed,
                 "agreement_file": f"SAMPLE-participation-agreement-office-{_n:02d}.pdf",
                 "pantry_owner_email": f"SAMPLE-owner@SAMPLE-office-{_n:02d}.example", "building_id": f"SAMPLE-B-B-00{_k}"})
    SIGNED_OFFICES.append(_row)

PAID_BRANDS = [{
    "submitted_at": "2026-11-25 15:40", "form_version": "brand-1.0", "brand_name": "SAMPLE Brand 01",
    "website": "https://SAMPLE-brand-01.example", "contact_name": "SAMPLE Contact B01", "contact_title": "Founder",
    "contact_email": "SAMPLE-founder@SAMPLE-brand-01.example", "contact_phone": "SAMPLE 000-000-0001",
    "product_sku": "SAMPLE Crunch Bar, Sea Salt, 1.4 oz", "category": "bars", "hq_city": "SAMPLE Brooklyn",
    "nyc_retailers": "SAMPLE Store, SAMPLE street", "online_store_url": "https://SAMPLE-brand-01.example/shop",
    "can_issue_discount_code": "Y", "preferred_timing": "SAMPLE January", "budget_approver_is_contact": "Y",
    "budget_approver_name_title": "SAMPLE Contact B01, Founder",
    "q1_sealed_shelf_stable_60d": "Y", "q2_labeled_ingredients_allergens": "Y", "q3_buy_path_near_cluster": "Y",
    "q4_can_ship_275_in_10bd": "Y", "q5_product_liability_insurance": "Y", "q6_contact_can_approve_600": "Y",
    "q7_why_now": "SAMPLE: new placement at a store near the cluster", "excluded_category_confirmed": "Y",
    "notes": "SAMPLE", "source": "founder",
    "brand_id": "SAMPLE-BR-101", "clay_row_id": "SAMPLE-B-001", "tier": "founding", "price_usd": 600, "offices_count": 5,
    "payment_terms": "founding: in full within five business days of invoice, before shipping",
    "agreement_signed_date": D(2026, 12, 1), "invoice_id": "SAMPLE-INV-0001", "invoice_date": D(2026, 12, 1),
    # payment_received_date is a formula (= payment_1_date)
    "coi_received_date": D(2026, 12, 4), "allergen_sheet_received_date": D(2026, 12, 2), "logo_received_date": D(2026, 12, 2),
    "card_sentences": "SAMPLE: two sentences from the brand about who makes it and why.",
    "allergen_line_verbatim": "SAMPLE: Contains: almonds, milk.", "retailer_line": "SAMPLE: Find it at SAMPLE Store, SAMPLE street",
    "discount_code": "SAMPLECODE10", "landing_url": "https://SAMPLE-brand-01.example/office",
    "unused_product_election": "release", "office_approvals": "SAMPLE-O-101;SAMPLE-O-102;SAMPLE-O-103;SAMPLE-O-104;SAMPLE-O-105",
    "payment_1_usd": 600, "payment_1_date": D(2026, 12, 3), "payment_2_usd": None, "payment_2_date": None,
    "agreement_version": "0.8", "coi_policy_end_date": D(2027, 9, 30), "newsletter_option": "N",
    "brand_privacy_url": "https://SAMPLE-brand-01.example/privacy", "allergen_source": "contains_statement",
    "may_contain_verbatim": "SAMPLE: May contain peanuts.", "flavor_name": "", "flavor_name_2": "", "allergen_source_2": "",
    "allergen_line_verbatim_2": "", "may_contain_verbatim_2": "",
    "verified_q1_sealed_shelf_stable_60d": "Y", "verified_q2_labeled_ingredients_allergens": "Y",
    "verified_q3_buy_path_near_cluster": "Y", "verified_q4_can_ship_275_in_10bd": "Y",
    "verified_q5_product_liability_insurance": "Y", "verified_q6_contact_can_approve_600": "Y",
    "verified_q7_why_now": "Y", "verified_not_excluded": "Y", "verified_date": D(2026, 12, 4),
    "verified_notes": "SAMPLE: unit seen, best-by 2027-06; certificate checked",
    "campaign_id": "SAMPLE-CMP-001", "brand_legal_name": "SAMPLE Brand 01 LLC", "billing_address": "SAMPLE 2 Example Avenue, Brooklyn, NY",
    "billing_email": "SAMPLE-billing@SAMPLE-brand-01.example", "code_site": "SAMPLE-brand-01.example",
}]

LATER_EVENTS = [{
    "date": D(2027, 1, 27), "side": "brand", "clay_row_id": "SAMPLE-B-001", "org_name": "SAMPLE Brand 01",
    "event": "renewal_answer", "value_number": None, "value_text": "maybe", "notes": "SAMPLE: debrief, wants the report first",
}]
