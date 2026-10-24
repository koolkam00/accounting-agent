"""The SOP, T-10 to T+30, as data. sop/SOP.md and tools/make_calendar.py are both built from this list,
so the written SOP and each drop's dated checklist never disagree.

Each step: (id, anchor, offset, kind, models, owner, what, log, tool)
  anchor  "T" (the drop day), "ship_req" (the requested ship-by: T-10, or earlier when T-10 to T-5
          crosses the December blackout, CONTRACTS section 3) or another step id
  kind    "bd" business days, "cal" calendar days, "by" a deadline counted in business days
  models  "all" or a set of founder / courier / direct-ship
Dates come from tools/opscal.py, which refuses any drop day that is a Monday, Friday, holiday or blackout.
"""
ALL = "all"
F, C, DS = "founder", "courier", "direct-ship"

STEPS = [
    # ---- before T-10: from the brand's yes
    ("yes", "ship_req", -5, "by", ALL, "you",
     "Brand says yes: send the campaign agreement (legal pack file 10, Part 1 from the campaign row), the invoice (tools/make_invoice.py) and the certificate request (file 11), and ask for the allergen sheet, logo, two card sentences, discount code or landing page, the unused-product election and the newsletter choice. Latest date that still leaves five business days to pay before the requested ship date.",
     "campaigns row (tier, offices, terms); invoices row", "make_invoice.py"),
    ("approvals_ask", "ship_req", -5, "by", ALL, "you",
     "Ask each office on the route about this brand (template 01). An office's first three drops need its explicit yes; after that, notice at least five business days ahead and it comes unless they say no.",
     "approvals rows: asked_date", "make_messages.py approvals"),
    ("building_coi", "T", -15, "by", ALL, "you",
     "Offices whose building wants our certificate (coi_required yes or unsure): request it from our carrier at least 10 business days before that office's first drop (legal pack file 12), only once general liability is bound.",
     "offices: building_coi_status, building_coi_date", ""),
    ("paid", "ship_req", 0, "by", ALL, "brand",
     "Payment lands in the business account: log paid_date and paid_amount on invoices. Founding: due within five business days of the invoice and before shipping; standard: the first 50% on signing. Five business days late: you decide whether to cancel and refund (file 10, section 3).",
     "invoices: paid_date, paid_amount_usd, method, bank_reference", ""),
    ("coi_check", "ship_req", 0, "by", ALL, "you",
     "Brand's certificate in: the five-minute check in legal pack file 11. Tick coi_check_ok on brands. If the policy ends before 12 months after the window, diary the renewal certificate.",
     "campaigns: coi_received_date; brands: coi_check_ok, coi_policy_end_date", ""),
    ("release", "ship_req", 0, "by", ALL, "you",
     "When campaigns shows ship_release RELEASED (payment, agreement, certificate, every office approved), send the ship-date email (template 02) the same day. Never confirm a ship date on HOLD.",
     "campaigns: ship_release", "make_messages.py ship_release"),
    ("direct_plan", "T", -10, "by", {DS}, "you and brand",
     "Direct-ship: send the brand each office's address and case labels (labels.pdf), ask for a service that delivers on T, one tracking number per office by T-2, and the reserve shipped to you by T-5.",
     "stops: carrier_tracking later", "make_kit.py"),
    # ---- T-10 to T-1
    ("ship", "T", -10, "bd", ALL, "brand",
     "Hard ship-by and cancel-by date (T-10). Approvals due. If T-10 to T-5 crosses 18 to 31 December, brands were asked to ship earlier (ship_by_requested).",
     "approvals: reply, reply_date", ""),
    ("receive", "T", -5, "bd", {F, C}, "you",
     "Receive and count the day cases arrive (by T-5 at the latest): count against the packing list, best-by at least 60 days after T, lot numbers, damage; photograph the cases. Reject what fails and tell the brand the same day. Check the allergen line on the card text word for word against a package in your hand. Short shipment: reduce units per office evenly (units_override) and tell the brand.",
     "inventory: received (lot, best_by), rejected; issues", ""),
    ("receive_ds", "T", -5, "bd", {DS}, "you",
     "Direct-ship: receive the reserve and check one package of each flavor: best-by, lot, and the allergen line word for word.",
     "inventory: received (reserve)", ""),
    ("card_proof", "T", -5, "bd", ALL, "you",
     "Send the brand the card text before printing (brand agreement section 1): two sentences, allergen line, buy line.",
     "campaigns: card_proof_sent_date", ""),
    ("forms", "T", -4, "bd", ALL, "you",
     "Make each campaign's survey form (forms/survey-form.md) and, if the brand chose it, its newsletter sign-up form. Paste the prefill template into campaigns. Then make the links and QR codes and import them into the link tool.",
     "campaigns: survey_form_url, survey_prefill_template, newsletter_form_url", "make_links.py"),
    ("kit_print", "T", -3, "bd", ALL, "you",
     "Not arrived (founder, courier) = slip exactly one week (tools/opscal.py slip) and tell every office and the brand today (template 12). Otherwise print cards and labels (make_kit.py; qr-check.txt must say all OK), test-scan every card, and send each office its window and Slack post (template 03).",
     "stops: slack_post_sent_date; costs: kit", "make_kit.py; make_messages.py t3"),
    ("kit_mail", "T", -3, "bd", {DS}, "you",
     "Direct-ship: mail each office its tent cards and the Slack post, to arrive by T-1.",
     "stops: kit_mailed_date; costs: other_direct (postage)", ""),
    ("courier_brief", "T", -2, "bd", {C}, "you",
     "Courier: confirm the booking and send the route sheet (make_route.py). Send building certificates ahead where required.",
     "drops: courier_or_van", "make_route.py"),
    ("tracking", "T", -2, "bd", {DS}, "brand",
     "Direct-ship: one tracking number per office, delivering on T.",
     "stops: carrier_tracking", ""),
    ("confirm", "T", -1, "bd", ALL, "you",
     "Text each pantry owner to confirm (template 04). Pack one labeled case per office per brand against the kit checklist; bag and label the reserve. Print the route sheet. Charge the phone, load the hand truck. Read every link's total after your test scans and log it as the baseline.",
     "stops: confirm_text_sent_date; scans: baseline", "make_route.py; make_messages.py t1"),
    # ---- T to T+4
    ("drop", "T", 0, "bd", {F, C}, "you or courier",
     "Drop day, 8 to 11 am: route in order; 'on my way' 20 minutes out (template 05); the per-stop procedure on the route sheet. Courier: you meet the courier at every first-drop office. Log everything the same day.",
     "stops: arrival, departure, handed_to_role, outcome; inventory: delivered; photos; counts: placed; issues; hours: drop_day", "make_messages.py on_my_way"),
    ("drop_ds", "T", 0, "bd", {DS}, "carrier and office",
     "Direct-ship: watch tracking; each office confirms the count and sends the placement photo. Visit every office whose first drop this is.",
     "inventory: delivered (count_source office_count); photos; counts", ""),
    ("placement_confirm", "T", 1, "bd", ALL, "you",
     "Placement confirmation to each brand (template 06): the offices placed by today, each with its photo. Office not placed by today: credit note row and refund or take it off the balance ($120 founding, $150 standard). Standard: issue the balance invoice today.",
     "invoices: credit_note, standard_balance", "make_messages.py placement_confirmation; make_invoice.py"),
    ("day3", "T", 2, "bd", ALL, "you and office",
     "Day 3: ask each office for a count (template 07); top up from reserve where empty; nudge any office under five responses. Read the links (mid).",
     "counts: remaining_day3; inventory: topped_up; scans: mid", "make_messages.py day3"),
    ("close", "T", 4, "bd", ALL, "you and office",
     "Day 5: last photo and count (template 08); collect leftovers (brand chose return) or leave them (release). At the end of the day turn off 'Accepting responses' on every campaign survey form and read every link total (close).",
     "counts: remaining_day5; photos: later; inventory: collected or released_to_office; scans: close", "make_messages.py day5"),
    # ---- after the window
    ("pass_on", "T", 5, "bd", ALL, "you",
     "Newsletter (only where chosen): send the ticked addresses once (template 09), delete the unticked responses today, log the count only. Reconcile stock: reserve and leftovers on hand. Ask for the return label (brand chose return).",
     "campaigns: newsletter_passed_date, newsletter_passed_count, newsletter_unticked_deleted_date", "make_messages.py newsletter"),
    ("report_draft", "T", 6, "bd", ALL, "you",
     "Pick three comments word for word (replace names with [name removed]), write three 'learned' lines and the recommendation on the campaign row.",
     "campaigns: comment_1..3, learned, recommendation", ""),
    ("report", "T", 7, "bd", ALL, "you",
     "Report (make_report.py) to each brand with template 10; standard: after the balance is paid. Office summaries to each office. Log report_delivered_date.",
     "campaigns: report_delivered_date", "make_report.py; make_messages.py report"),
    ("office_debrief", "T", 9, "by", ALL, "you and office",
     "Ten-minute debrief with each office (templates/debrief-office.md). Log the date and the one-question answer.",
     "stops: office_debrief_date, office_would_do_again", "make_debrief.py"),
    ("debrief", "T", 10, "bd", ALL, "you and brand",
     "Brand debrief, 20 minutes (templates/debrief-brand.md); send the renewal proposal the same day. Export actuals for the financial model (export_actuals.py) and set Actuals in = Y there once money, costs and hours are final.",
     "campaigns: debrief_date, brand_would_buy_again, renewed; hours: reporting_debriefs", "make_debrief.py; export_actuals.py"),
    ("return_deadline", "T", 14, "bd", ALL, "you",
     "Ten business days after the window: no prepaid return label = unused reserve to roster offices, collected leftovers back to their own office or disposed (brand agreement section 9). Stock on hand must be zero.",
     "inventory: returned_to_brand / given_to_roster_office / released_to_office / disposed", ""),
    ("redemption", "T", 30, "cal", ALL, "brand",
     "Day 30 (calendar): ask the brand for code redemptions (template 11). Log them; export actuals again; update renewed.",
     "redemptions; campaigns: renewed", "make_messages.py redemption; export_actuals.py"),
    ("newsletter_delete", "pass_on", 30, "cal", ALL, "you",
     "Thirty days after passing the list on: delete every response in the sign-up form, the form itself and the sent email; empty the trash. Log the date.",
     "campaigns: newsletter_deleted_date", ""),
    ("testimonial", "debrief", 30, "cal", ALL, "brand",
     "Founding brands only, if we delivered everything in section 1: the short written statement is due (brand agreement section 3).",
     "campaigns: notes", ""),
    ("answers_delete", "close", 365, "cal", ALL, "you",
     "Twelve months after the campaign: delete the campaign's survey tab, the form's responses and the form. Log the date.",
     "campaigns: answers_deleted_date", ""),
]


def applies(step, model):
    m = step[4]
    return m == ALL or model in m


def dates(T, model):
    import datetime as dt
    import opscal
    out = {}
    for st in STEPS:
        sid, anchor, off, kind = st[0], st[1], st[2], st[3]
        if not applies(st, model):
            continue
        base = T if anchor == "T" else opscal.sop_dates(T)["ship_by_requested"] if anchor == "ship_req" else out.get(anchor)
        if base is None:
            continue
        if kind in ("bd", "by"):
            out[sid] = opscal.add_bd(base, off)
        else:
            out[sid] = base + dt.timedelta(days=off)
    return out
