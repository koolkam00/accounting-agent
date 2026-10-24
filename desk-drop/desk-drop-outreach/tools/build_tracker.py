#!/usr/bin/env python3
"""Build the conversation tracker workbook.

    python3 tools/build_tracker.py            # writes tracking/conversation-tracker.xlsx (blank, ready to use)
    python3 tools/build_tracker.py --sample   # writes tracking/conversation-tracker-SAMPLE.xlsx (SAMPLE rows, banner)

The workbook is the conversation and notes log, keyed by the Clay row_id. It is not a status store:
status lives in the Clay tables only (CONTRACTS 6.2). The workbook reads a weekly paste of the Clay
export to check the two agree, to compute reply rates, and to build the pipeline log for the
financial model. Formulas use only functions that work in Google Sheets, LibreOffice and Excel 2010+
(no dynamic arrays, no MAXIFS, no XLOOKUP).
"""
import argparse
import datetime as dt
import os
import sys

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as CL
from openpyxl.worksheet.datavalidation import DataValidation

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # desk-drop-outreach/
sys.path.insert(0, HERE)

# ----------------------------------------------------------------------------- names in one place
COMPANY_NAME = "Desk Drop"                         # working name; also Config!B2 in the workbook
TAGLINE = "Emerging brands. Delivered to your workday."

# ----------------------------------------------------------------------------- sizes
LOG_N = 200            # log rows per side (rows 2..201)
CLAY_N = 600           # Clay paste rows per side (rows 2..601)
CLAY_LAST_COL = "FZ"   # paste area A:FZ (182 columns)
HAND_N = 50            # signed_offices / paid_brands rows
LATER_N = 100          # later_events rows
EXPORT_N = 1000        # pipeline_log rows

# ----------------------------------------------------------------------------- styles
F_HDR = Font(bold=True, color="FFFFFF")
FILL_HDR = PatternFill("solid", fgColor="1F3A5F")
FILL_CALC_HDR = PatternFill("solid", fgColor="7F7F7F")
FILL_CALC = PatternFill("solid", fgColor="F2F2F2")
FILL_SEC = PatternFill("solid", fgColor="DCE6F1")
FILL_SAMPLE = PatternFill("solid", fgColor="C00000")
FILL_PASS = PatternFill("solid", fgColor="C6EFCE")
FILL_FAIL = PatternFill("solid", fgColor="FFC7CE")
FILL_WAIT = PatternFill("solid", fgColor="EDEDED")
FILL_WARN = PatternFill("solid", fgColor="FFEB9C")
F_BOLD = Font(bold=True)
F_TITLE = Font(bold=True, size=14)
F_NOTE = Font(italic=True, color="595959")
F_WHITE_BOLD = Font(bold=True, color="FFFFFF", size=12)
WRAP = Alignment(wrap_text=True, vertical="top")
DATE_FMT = "yyyy-mm-dd"
THIN = Side(style="thin", color="BFBFBF")

# ----------------------------------------------------------------------------- lists
LISTS = {
    "yn": ["Y", "N"],
    "ynm": ["Y", "N", "maybe"],
    "yesno_unsure": ["yes", "no", "unsure"],
    "channel": ["email", "linkedin", "warm-intro", "walk-in"],
    "call_type": ["phone", "video", "in-person", "walk-in"],
    "receiving_type": ["walk-up", "front desk", "security desk", "loading dock", "other", "unknown"],
    "intake_receiving_type": ["walk-up", "front desk", "loading dock", "other"],
    "buy_path_type": ["retailer-in-cluster", "retailer-within-10-blocks", "online-with-code", "online-no-code", "none", "unknown"],
    "status": ["new", "queued", "contacted", "replied", "call_booked", "call_done", "yes_in_principle", "materials_sent",
               "signed", "paid", "not_now", "no", "wrong_person", "do_not_contact"],
    "status_rank": [1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 0, 0, 0, 0],
    "reply_type": ["yes", "maybe", "needs_approval", "send_info", "wrong_person", "referral", "not_now", "no", "opt_out",
                   "obj_seed_ourselves", "obj_price", "obj_free_trial", "obj_what_we_get", "obj_other", "out_of_office", "bounce"],
    "next_action": ["send_touch_2", "send_touch_3", "await_connection", "book_call", "run_call", "send_one_pager", "send_proposal",
                    "send_agreement", "send_materials_request", "chase_payment", "ask_referral", "recontact", "none"],
    "office_objection": ["needs_approval", "existing_vendor", "allergy_policy", "healthy_policy", "building_receiving",
                         "low_attendance", "commitments_too_much", "survey_concern", "vendor_fatigue", "space",
                         "supply_irregular", "quality_unknown", "other"],
    "office_objection_label": [
        "I need to ask facilities, HR or someone else", "We already have a pantry vendor or contract",
        "Allergy or food-safety worry", "We only stock healthy items (wellness policy)",
        "Building security, receiving or certificate rules", "Not enough people in on a given day",
        "Photos, survey or debrief are too much work", "Survey or employee-data worry",
        "We don't want vendors or marketing in the office", "No shelf or counter space",
        "Irregular, roughly monthly supply isn't useful", "Don't know these brands; quality worry", "Other (read the quotes)"],
    "brand_objection": ["seed_ourselves", "price_per_sample", "free_trial", "what_we_get", "budget_timing", "inventory",
                        "shelf_life", "not_our_audience", "want_proof", "want_sales_data", "no_buy_path", "insurance", "other"],
    "brand_objection_label": [
        "We can seed offices ourselves for free", "$600 / the price is more than we pay per sample elsewhere",
        "Can we do a free trial first?", "What do we actually get out of it?", "No budget now / budget timing",
        "Inventory or shipping the units", "Shelf life", "Office workers aren't our customer",
        "Show me results from other brands first", "We need sales or lift data, not feedback",
        "No store near the cluster and no online code", "No product liability certificate", "Other (read the quotes)"],
    "category": ["chips-crisps", "popcorn-puffs", "crackers-pretzels", "bars", "cookies-baked", "chocolate-candy",
                 "nuts-seeds-trail", "meat-snacks", "fruit-snacks", "sparkling-soda", "tea-juice", "coffee-rtd",
                 "other-snack", "other-drink"],
    "tier": ["founding", "standard"],
    "unused_product_election": ["return", "release"],
    "survey_channel": ["slack", "email", "other"],
    "intake_source": ["website", "founder"],
    "later_event": ["renewal_answer", "opt_out"],
    "side": ["office", "brand"],
    "renewal_value": ["yes", "maybe", "no"],
    "allergen_source": ["contains_statement", "ingredient_list", "single_ingredient"],
    "yes_signals": ["named_window_unprompted", "asked_when", "introduced_colleague"],
}
SEQUENCES = ["office-discovery-A", "office-discovery-B", "office-selling-A", "office-selling-B",
             "brand-discovery-A", "brand-discovery-B", "brand-selling-A", "brand-selling-B",
             "office-conversion-A", "brand-conversion-A"]

# ----------------------------------------------------------------------------- column specs
# (key, kind, width, help, maps_to). kind: id | text | date | num | list:<name>
OFFICE_COLS = [
    ("row_id", "id", 15, "Clay row_id of this contact. Required. One row per conversation; a second call with the same office is a second row with the same row_id.", "CONTRACTS 6.2 row_id (join key)"),
    ("company", "text", 20, "Company name as in Clay.", "plan: Contact, title, company, source"),
    ("contact_name", "text", 17, "First and last name of the person you spoke to (business contact only).", "plan: Contact"),
    ("contact_title", "text", 18, "Their title.", "plan: title"),
    ("source", "text", 16, "Where the contact came from: the Clay table, warm network, walk-in, or 'referral from <row_id>'.", "plan: source"),
    ("channel", "list:channel", 10, "How the conversation came about: email, linkedin, warm-intro, walk-in.", "CONTRACTS 6.2 channel"),
    ("call_date", "date", 11, "Date of the conversation (YYYY-MM-DD). Required; the Friday scorecard counts by this date.", "CONTRACTS 6.2 call_date"),
    ("call_type", "list:call_type", 9, "phone, video, in-person or walk-in.", ""),
    ("q1_pantry_today_verbatim", "text", 34, "Q1. How the pantry works today: who chooses, who delivers, how often. Their words.", "office guide Q1"),
    ("pantry_vendor", "text", 14, "Q1. Who supplies the pantry now, if they said.", "office guide Q1"),
    ("monthly_pantry_spend_usd", "num", 9, "Q1. Monthly pantry spend in USD if they named one. Number only; a range: its low end. Blank if not said.", "plan: Monthly pantry spend"),
    ("monthly_pantry_spend_verbatim", "text", 20, "Q1. Their words about cost.", "plan: Monthly pantry spend"),
    ("tuesday_headcount", "num", 9, "Q2. People actually in on a Tuesday. A range: its low end, with the range in headcount_verbatim.", "plan: Peak-day headcount"),
    ("headcount_verbatim", "text", 16, "Q2. Their words.", "plan: Peak-day headcount"),
    ("q3_free_product_verbatim", "text", 26, "Q3. Do brands offer free product, and what happens when they do.", "office guide Q3"),
    ("q4_yes_needs_verbatim", "text", 26, "Q4. What they would need to say yes.", "office guide Q4"),
    ("q4_no_triggers_verbatim", "text", 26, "Q4. What would make them say no.", "office guide Q4"),
    ("q5_photo_and_survey", "list:ynm", 8, "Q5. Would they photograph it on the shelf and post a three-question survey link? Y, N or maybe.", "office guide Q5"),
    ("q5_verbatim", "text", 18, "Q5. Their words.", "office guide Q5"),
    ("budget_probe_asked", "list:yn", 7, "Q6. Did you ask the budget probe word for word? Y or N.", "plan: The budget probe"),
    ("budget_probe_verbatim", "text", 32, "Q6. The answer, word for word.", "plan: Budget probe answer, verbatim"),
    ("budget_probe_low_usd", "num", 9, "Q6 as a number, USD per month. A range: its low end. 'No budget' or 'zero': 0. No number or 'don't know': blank.", "pipeline_log value_number (budget_probe)"),
    ("budget_probe_high_usd", "num", 9, "Q6 high end, USD per month. Same as low for a single number. Blank if none.", ""),
    ("referrals_given_count", "num", 7, "Q7. How many nearby pantry owners they named or introduced.", "plan: Referrals given"),
    ("referrals_given", "text", 22, "Q7. Who: company and title, semicolons. Each becomes a new Clay row with referral_from = this row_id.", "plan: Referrals given; Clay referral_from"),
    ("pantry_owner_named", "list:yn", 7, "Did they name the pantry owner (the person who receives a drop and can say yes)? Y or N.", "plan: Pantry owner named; Gate 0"),
    ("pantry_owner_name", "text", 15, "The pantry owner's name (business contact).", "office_intake pantry_owner_name"),
    ("pantry_owner_title", "text", 15, "The pantry owner's title.", "office_intake pantry_owner_title"),
    ("owner_can_say_yes_alone", "list:ynm", 7, "Can the owner say yes alone? 'I need to ask facilities or HR' is N.", "plan Phase 1 targeting"),
    ("receiving_window", "text", 15, "When a delivery can be received, in their words (e.g. Tue-Wed 9-11am). Blank if not named.", "plan: receiving window; Gate 0"),
    ("receiving_type", "list:receiving_type", 11, "walk-up, front desk, security desk, loading dock, other, unknown.", "plan: security; office_intake receiving_type"),
    ("coi_required", "list:yesno_unsure", 8, "Does the building require a certificate of insurance for deliveries? yes, no, unsure.", "office_intake coi_required"),
    ("security_notes", "text", 18, "Lobby, security or freight rules.", "plan: security"),
    ("veto_categories", "text", 18, "Categories they would refuse, as category keys separated by semicolons (Lists tab).", "plan: Veto categories"),
    ("veto_verbatim", "text", 18, "Their words about what they never want.", "plan: Veto categories"),
    ("objection_1", "list:office_objection", 14, "Main objection, as a code (Lists tab). Blank if none.", "plan: Objections"),
    ("objection_2", "list:office_objection", 14, "Second objection code.", "plan: Objections"),
    ("objection_3", "list:office_objection", 14, "Third objection code.", "plan: Objections"),
    ("objections_verbatim", "text", 30, "Every objection in their words.", "plan: Objections, verbatim"),
    ("yes_in_principle", "list:ynm", 7, "Y: would take a first drop in principle. maybe: interested but someone else must agree. N: no.", "plan: Yes in principle; Gate 0"),
    ("yes_signals", "text", 16, "Plan's yes signals seen: named_window_unprompted; asked_when; introduced_colleague.", "plan: A yes looks like"),
    ("note_minutes", "num", 7, "Minutes from hanging up to finishing this row and the Clay write-back. Target 10 or less.", "ten-minute rule"),
    ("clay_updated", "list:yn", 7, "Y once call_date, status, yes_in_principle, call_notes, next_action and next_action_date are written to the Clay row.", "sync"),
    ("notes", "text", 24, "Anything else.", ""),
]

BRAND_COLS = [
    ("row_id", "id", 15, "Clay row_id of this contact. Required. One row per conversation; a second call is a second row with the same row_id.", "CONTRACTS 6.2 row_id (join key)"),
    ("company", "text", 20, "Brand name as in Clay.", "plan: Contact, title, company, source"),
    ("contact_name", "text", 17, "First and last name of the person you spoke to.", "plan: Contact"),
    ("contact_title", "text", 18, "Their title.", "plan: title"),
    ("source", "text", 16, "Where the contact came from: Clay table, Startup CPG event, shelf photo, warm network, referral.", "plan: source"),
    ("channel", "list:channel", 10, "How the conversation came about.", "CONTRACTS 6.2 channel"),
    ("call_date", "date", 11, "Date of the conversation (YYYY-MM-DD). Required.", "CONTRACTS 6.2 call_date"),
    ("call_type", "list:call_type", 9, "phone, video, in-person or walk-in.", ""),
    ("q1_trial_now_verbatim", "text", 30, "Q1. How they get people to try the product now; what works and what doesn't.", "brand guide Q1"),
    ("q2_sampling_budget_quarter_low_usd", "num", 10, "Q2. Sampling or field-marketing spend per quarter, USD. A range: low end. Blank if not said.", "plan: Quarterly sampling budget"),
    ("q2_sampling_budget_quarter_high_usd", "num", 10, "Q2. High end of the range. Same as low for one number.", "plan: Quarterly sampling budget"),
    ("q2_budget_verbatim", "text", 24, "Q2. Their words about budget.", "plan: Quarterly sampling budget"),
    ("budget_approver", "text", 16, "Q2. Who signs off, in their words (business title).", "plan: who approves"),
    ("controls_budget", "list:yn", 7, "Does the person on this call control the budget? Y or N. Gate 0 counts a brand only if Y.", "plan Gate 0; pipeline controls_budget"),
    ("can_approve_600_alone", "list:ynm", 7, "Could they approve $600 without a committee? Y, N or maybe. (Qualification check 6.)", "plan Phase 2 checklist"),
    ("q3_seeded_offices", "list:yn", 7, "Q3. Have they ever seeded offices? Y or N.", "brand guide Q3"),
    ("q3_verbatim", "text", 22, "Q3. What happened.", "brand guide Q3"),
    ("wtp_before_usd", "num", 9, "Q4. The number they named BEFORE you said $1,500, as USD for the 10-office, 500-unit campaign. 'Nothing': 0. No number: blank.", "plan: Willingness to pay before $1,500; pipeline budget_probe"),
    ("wtp_before_verbatim", "text", 28, "Q4. Their words, before you said $1,500.", "plan: Willingness to pay, verbatim"),
    ("wtp_conversion_note", "text", 18, "If they gave a per-unit or per-store figure, how you turned it into a campaign number (e.g. $2 a unit x 500 = 1000).", ""),
    ("price_1500_mentioned", "list:yn", 7, "Did you then say the $1,500 standard price on this call? Y or N.", "plan: before and after hearing $1,500"),
    ("wtp_after_usd", "num", 9, "Q4. Their number AFTER hearing $1,500, USD per campaign. Blank if none.", "plan: Willingness to pay after $1,500; pipeline budget_probe (after_1500)"),
    ("wtp_after_verbatim", "text", 28, "Q4. Their words after hearing $1,500.", "plan: Willingness to pay, verbatim"),
    ("q5_report_needs_verbatim", "text", 26, "Q5. What the report would need to show for them to do it again.", "brand guide Q5"),
    ("q6_buy_path_type", "list:buy_path_type", 14, "Q6. Buy path near the cluster.", "plan: Buy path inside the cluster"),
    ("q6_buy_path_verbatim", "text", 22, "Q6. Store name and street, or the site, in their words.", "plan: Buy path inside the cluster"),
    ("q7_stoppers_verbatim", "text", 24, "Q7. What would stop them: budget timing, inventory, shelf life, something else.", "brand guide Q7"),
    ("objection_1", "list:brand_objection", 14, "Main objection, as a code (Lists tab).", "plan: Objections"),
    ("objection_2", "list:brand_objection", 14, "Second objection code.", "plan: Objections"),
    ("objection_3", "list:brand_objection", 14, "Third objection code.", "plan: Objections"),
    ("objections_verbatim", "text", 30, "Every objection in their words.", "plan: Objections, verbatim"),
    ("yes_in_principle", "list:ynm", 7, "Y: would buy a campaign in principle at a price they named. maybe. N.", "plan: Yes in principle"),
    ("referrals_given_count", "num", 7, "How many other founders they named or introduced.", "plan: Referrals given"),
    ("referrals_given", "text", 20, "Who: brand and title, semicolons. Each becomes a new Clay row with referral_from = this row_id.", "plan: Referrals given"),
    ("note_minutes", "num", 7, "Minutes from hanging up to finishing this row and the Clay write-back. Target 10 or less.", "ten-minute rule"),
    ("clay_updated", "list:yn", 7, "Y once call_date, status, yes_in_principle, call_notes, next_action and next_action_date are written to Clay.", "sync"),
    ("notes", "text", 24, "Anything else.", ""),
]

OFFICE_INTAKE = ["submitted_at", "form_version", "company", "contact_name", "contact_title", "contact_email", "contact_phone",
                 "office_address", "floor_suite", "tuesday_headcount", "pantry_owner_name", "pantry_owner_title",
                 "pantry_owner_is_contact", "receiving_type", "receiving_window", "coi_required", "survey_channel",
                 "categories_wanted", "vetoes", "notes", "source"]
BRAND_INTAKE = ["submitted_at", "form_version", "brand_name", "website", "contact_name", "contact_title", "contact_email",
                "contact_phone", "product_sku", "category", "hq_city", "nyc_retailers", "online_store_url",
                "can_issue_discount_code", "preferred_timing", "budget_approver_is_contact", "budget_approver_name_title",
                "q1_sealed_shelf_stable_60d", "q2_labeled_ingredients_allergens", "q3_buy_path_near_cluster",
                "q4_can_ship_275_in_10bd", "q5_product_liability_insurance", "q6_contact_can_approve_600", "q7_why_now",
                "excluded_category_confirmed", "notes", "source"]

SIGNED_EXTRA = [
    ("office_id", "id", 10, "O-### assigned at signing (CONTRACTS 6.4).", "CONTRACTS 6.4"),
    ("clay_row_id", "id", 15, "The Clay row_id of the office contact. Must match the row_id used in Office_Log.", "CONTRACTS 6.4; pipeline org_id"),
    ("agreement_signed_date", "date", 11, "Date the participation agreement was signed by both sides.", "CONTRACTS 6.4"),
    ("agreement_file", "text", 24, "File name of the signed PDF.", "CONTRACTS 6.4"),
    ("founding_roster_named", "list:yn", 7, "Y if the office ticked the box agreeing to be named on the founding roster (agreement section 6).", "CONTRACTS 6.4"),
    ("budget_probe_verbatim", "formula", 28, "Filled from Office_Log (first budget-probe answer for this clay_row_id). Overwrite only if there is no log row.", "CONTRACTS 6.4"),
    ("budget_probe_date", "formula", 11, "Filled from Office_Log: the date of that answer.", "CONTRACTS 6.4"),
    ("budget_probe_monthly_usd", "formula", 9, "Filled from Office_Log: USD per month if they named a number (0 for 'no budget'), else blank.", "CONTRACTS 6.4"),
    ("agreement_version", "text", 8, "Version of the participation agreement signed (e.g. 0.8). Added at the legal pack's suggestion.", "addition (G)"),
    ("owner_can_say_yes_alone", "list:yn", 7, "Y if the pantry owner can approve a brand alone.", "addition (plan Phase 1)"),
]
PAID_EXTRA = [
    ("brand_id", "id", 11, "BR-### assigned at payment (CONTRACTS 6.4).", "CONTRACTS 6.4"),
    ("clay_row_id", "id", 15, "The Clay row_id of the brand contact. Must match the row_id used in Brand_Log.", "CONTRACTS 6.4; pipeline org_id"),
    ("tier", "list:tier", 9, "founding or standard.", "CONTRACTS 6.4"),
    ("price_usd", "num", 8, "Campaign price in USD (600 founding, 1500 standard, plus 150 per extra office).", "CONTRACTS 6.4"),
    ("offices_count", "num", 7, "Offices in the campaign (5 founding, 10 standard, more if extra offices).", "CONTRACTS 6.4"),
    ("payment_terms", "text", 24, "As in the signed agreement.", "CONTRACTS 6.4"),
    ("agreement_signed_date", "date", 11, "Date the campaign agreement was signed by both sides.", "CONTRACTS 6.4"),
    ("invoice_id", "text", 12, "Invoice number.", "CONTRACTS 6.4"),
    ("invoice_date", "date", 11, "Invoice date.", "CONTRACTS 6.4"),
    ("payment_received_date", "formula", 11, "Date the payment that releases the ship date landed: founding = the full price; standard = the 50% deposit. Filled from payment_1_date.", "CONTRACTS 6.4"),
    ("coi_received_date", "date", 11, "Date the product liability certificate arrived (checked per legal pack file 11).", "CONTRACTS 6.4"),
    ("allergen_sheet_received_date", "date", 11, "Date the ingredient and allergen sheet arrived.", "CONTRACTS 6.4"),
    ("logo_received_date", "date", 11, "Date the logo files arrived.", "CONTRACTS 6.4"),
    ("card_sentences", "text", 30, "The brand's two sentences for the tent card, as sent (no health claims).", "CONTRACTS 6.4"),
    ("allergen_line_verbatim", "text", 26, "The allergen statement copied word for word from the label.", "CONTRACTS 6.4"),
    ("retailer_line", "text", 26, "'Find it at <store, street>' line for the card.", "CONTRACTS 6.4"),
    ("discount_code", "text", 12, "The campaign discount code.", "CONTRACTS 6.4"),
    ("landing_url", "text", 22, "Landing page for the QR, if the brand gave one.", "CONTRACTS 6.4"),
    ("unused_product_election", "list:unused_product_election", 9, "return or release, as elected in the agreement.", "CONTRACTS 6.4"),
    ("office_approvals", "text", 18, "office_ids that said yes to this brand, semicolons.", "CONTRACTS 6.4"),
    ("payment_1_usd", "num", 8, "First payment received, USD (founding: 600; standard: the 50% deposit).", "addition: pipeline 'paid' rows"),
    ("payment_1_date", "date", 11, "Date the first payment landed in the bank.", "addition: pipeline 'paid' rows"),
    ("payment_2_usd", "num", 8, "Second payment, USD (standard balance at placement confirmation). Blank for founding.", "addition: pipeline 'paid' rows"),
    ("payment_2_date", "date", 11, "Date the second payment landed.", "addition: pipeline 'paid' rows"),
    ("agreement_version", "text", 8, "Version of the campaign agreement signed.", "addition (G)"),
    ("coi_policy_end_date", "date", 11, "End date of the brand's product liability policy, from the certificate.", "addition (G)"),
    ("newsletter_option", "list:yn", 7, "Y if the brand chose the optional survey email box (agreement Part 1).", "addition (G)"),
    ("brand_privacy_url", "text", 22, "The brand's privacy policy URL (needed only if newsletter_option = Y).", "addition (G)"),
    ("allergen_source", "list:allergen_source", 14, "Where the allergen line comes from on the package.", "addition (D tent card)"),
    ("may_contain_verbatim", "text", 22, "Any 'may contain' line, word for word.", "addition (D tent card)"),
    ("flavor_name", "text", 12, "Two-flavor campaigns only: flavor 1 name.", "addition (D tent card)"),
    ("flavor_name_2", "text", 12, "Two-flavor campaigns only: flavor 2 name.", "addition (D tent card)"),
    ("allergen_source_2", "list:allergen_source", 14, "Two-flavor only: flavor 2 allergen source.", "addition (D tent card)"),
    ("allergen_line_verbatim_2", "text", 22, "Two-flavor only: flavor 2 allergen line.", "addition (D tent card)"),
    ("may_contain_verbatim_2", "text", 22, "Two-flavor only: flavor 2 'may contain' line.", "addition (D tent card)"),
    ("verified_q1_sealed_shelf_stable_60d", "list:yn", 7, "Founder checked: sealed, individually packaged, shelf-stable, 60+ days of shelf life at the drop date.", "addition: qualification check 1"),
    ("verified_q2_labeled_ingredients_allergens", "list:yn", 7, "Founder checked the label: ingredients and the nine major allergens.", "addition: qualification check 2"),
    ("verified_q3_buy_path_near_cluster", "list:yn", 7, "Founder checked the buy path: a store within ten blocks (evidence grade store_selector, brand_claim or seen_on_shelf) or an online store with a code.", "addition: qualification check 3"),
    ("verified_q4_can_ship_275_in_10bd", "list:yn", 7, "Brand confirmed in writing it can ship the units plus reserve to one Manhattan address within ten business days.", "addition: qualification check 4"),
    ("verified_q5_product_liability_insurance", "list:yn", 7, "Certificate received and checked (legal pack file 11).", "addition: qualification check 5"),
    ("verified_q6_contact_can_approve_600", "list:yn", 7, "The signer approved the price alone.", "addition: qualification check 6"),
    ("verified_q7_why_now", "list:yn", 7, "A real reason for New York trial now (new store, launch, local push), noted in verified_notes.", "addition: qualification check 7"),
    ("verified_not_excluded", "list:yn", 7, "Not alcohol, cannabis, CBD or THC, supplement, refrigerated, needing preparation, or carrying a health claim (CONTRACTS 4).", "addition: excluded list"),
    ("verified_date", "date", 11, "Date the founder finished the checks.", "addition"),
    ("verified_notes", "text", 30, "Evidence for the checks (best-by date seen, certificate details, store and street).", "addition"),
]
LATER_COLS = [
    ("date", "date", 11, "Date of the event.", "pipeline_log date"),
    ("side", "list:side", 8, "office or brand.", "pipeline_log side"),
    ("clay_row_id", "id", 15, "Clay row_id of the organization (same as in the logs and handoff tabs).", "pipeline_log org_id"),
    ("org_name", "text", 20, "Company or brand name.", "pipeline_log org_name"),
    ("event", "list:later_event", 14, "renewal_answer (a brand's answer at or after the debrief) or opt_out (a signed office or paid brand leaving the roster). Outreach unsubscribes are NOT logged here; they live in Clay only.", "pipeline_log event"),
    ("value_number", "num", 9, "renewal_answer: USD committed if the answer is yes, else blank. opt_out: blank.", "pipeline_log value_number"),
    ("value_text", "text", 22, "renewal_answer: yes, maybe or no. opt_out: the reason in their words.", "pipeline_log value_text"),
    ("notes", "text", 24, "Anything else.", "pipeline_log notes"),
]
PIPELINE_COLS = ["date", "side", "org_id", "org_name", "event", "value_number", "value_text", "controls_budget", "notes"]

CLAY_NEEDED = ["row_id", "company", "status", "do_not_contact", "channel", "sequence", "touch_1_date", "touch_2_date",
               "touch_3_date", "last_reply_date", "reply_type", "call_date", "yes_in_principle", "opt_out_date"]

CLAY_TRACKING = [
    # column, type, allowed values, written when, rule
    ("sequence", "text", "<side>-<stage>-<variant>, e.g. office-discovery-A (stage: discovery, selling, conversion)", "When the first touch is sent", "Never changed afterwards; a new sequence on the same person is a new value only if the old one ended (not_now recontact)"),
    ("touch_1_date", "date", "YYYY-MM-DD", "The day the first message with the ask is sent (email, LinkedIn message, walk-in conversation)", "A LinkedIn invitation with no note is not a touch: set next_action = await_connection instead"),
    ("touch_2_date", "date", "YYYY-MM-DD", "Day touch 2 is sent", "Skip if they replied"),
    ("touch_3_date", "date", "YYYY-MM-DD", "Day touch 3 is sent", "Last touch; then stop"),
    ("last_reply_date", "date", "YYYY-MM-DD", "Each time they reply", "Not for bounces or out-of-office auto-replies"),
    ("reply_type", "list", "yes, maybe, needs_approval, send_info, wrong_person, referral, not_now, no, opt_out, obj_seed_ourselves, obj_price, obj_free_trial, obj_what_we_get, obj_other, out_of_office, bounce", "Each reply (the latest meaningful one)", "Silence stays blank"),
    ("call_date", "date", "YYYY-MM-DD", "After each conversation, copied from the tracker row", "Equals the latest call_date for this row_id in the tracker"),
    ("call_notes", "text", "One line plus 'see tracker <call_date>'", "After each conversation", "The full notes live in the tracker, not in Clay"),
    ("yes_in_principle", "Y/N", "Y or N", "After each conversation, copied from the tracker", "Y if any tracker row for this row_id says Y; maybe in the tracker is N here"),
    ("next_action", "list", "send_touch_2, send_touch_3, await_connection, book_call, run_call, send_one_pager, send_proposal, send_agreement, send_materials_request, chase_payment, ask_referral, recontact, none", "Whenever the next step changes", "Clay is the only place next actions live"),
    ("next_action_date", "date", "YYYY-MM-DD", "With next_action", "Drives the follow-up list each morning"),
    ("opt_out_date", "date", "YYYY-MM-DD", "The same day anyone opts out, in any words, on any channel", "Also set do_not_contact = Y and status = do_not_contact. Never cleared"),
    ("referral_from", "text", "row_id of the person who referred them", "When you create a row for a referred person", "Lets the scorecard and you trace referrals"),
]


# ----------------------------------------------------------------------------- helpers
class Cols:
    def __init__(self, specs, calc_keys):
        self.keys = [s[0] for s in specs] + list(calc_keys)
        self.idx = {k: i + 1 for i, k in enumerate(self.keys)}

    def L(self, key):
        return CL(self.idx[key])


def header(ws, row, col, text, calc=False, comment=None, width=None):
    c = ws.cell(row=row, column=col, value=text)
    c.font = F_HDR
    c.fill = FILL_CALC_HDR if calc else FILL_HDR
    c.alignment = Alignment(wrap_text=True, vertical="center")
    if comment:
        c.comment = Comment(comment, "tracker")
        c.comment.width = 320
        c.comment.height = 120
    if width:
        ws.column_dimensions[CL(col)].width = width


def put(ws, ref, value, font=None, fill=None, fmt=None, align=None):
    c = ws[ref]
    c.value = value
    if font:
        c.font = font
    if fill:
        c.fill = fill
    if fmt:
        c.number_format = fmt
    if align:
        c.alignment = align
    return c


class Book:
    def __init__(self, sample):
        self.sample = sample
        self.wb = Workbook()
        self.wb.remove(self.wb.active)
        self.list_ref = {}
        self.cfg = {}
        for name in ["Start", "Scorecard", "Office_Log", "Brand_Log", "signed_offices", "paid_brands", "later_events",
                     "Clay_Offices", "Clay_Brands", "Sync", "pipeline_log", "Pipeline_Sort", "Pipeline_Calc",
                     "Config", "Lists", "Dictionary", "Clay_Columns"]:
            self.wb.create_sheet(name)
        self.ws = {ws.title: ws for ws in self.wb.worksheets}

    # ------------------------------------------------------------------ lists and config
    def build_lists(self):
        ws = self.ws["Lists"]
        col = 1
        for name, vals in LISTS.items():
            header(ws, 1, col, name, width=max(14, min(46, max(len(str(v)) for v in vals) + 2)))
            for i, v in enumerate(vals, start=2):
                ws.cell(row=i, column=col, value=v)
            self.list_ref[name] = f"Lists!${CL(col)}$2:${CL(col)}${len(vals) + 1}"
            col += 1
        ws.freeze_panes = "A2"

    def build_config(self):
        ws = self.ws["Config"]
        put(ws, "A1", "Config: change values in column B only. Dates are derived from CONTRACTS section 3 (derived, founder to confirm).", font=F_BOLD)
        rows = [
            ("company_name", COMPANY_NAME, "The working name, in one place. Rename here; every tab title follows."),
            ("tagline", TAGLINE, "Working tagline."),
            ("as_of_date", dt.date(2026, 11, 20) if self.sample else "=TODAY()", "The Friday you are reading. Default =TODAY(). Type a date to read an earlier week."),
            ("week1_readout", dt.date(2026, 10, 30), "Friday of week 1 (derived, founder to confirm)."),
            ("week2_readout", dt.date(2026, 11, 6), "Friday of week 2 (derived, founder to confirm)."),
            ("gate0_date", dt.date(2026, 11, 13), "Gate 0, Friday of week 3 (CONTRACTS section 3; derived, founder to confirm)."),
            ("discovery_start", dt.date(2026, 10, 26), "Monday of week 1."),
            ("target_office_conversations", 15, "Plan Phase 0."),
            ("target_office_yes", 5, "Gate 0: yes in principle AND pantry owner named AND receiving window named."),
            ("target_brand_conversations", 15, "Plan Phase 0."),
            ("target_brand_yes", 3, "Gate 0: would pay the threshold AND the speaker controls the budget."),
            ("brand_wtp_threshold_usd", 500, "Gate 0 brand threshold, USD per campaign."),
            ("office_paid_threshold_usd", 100, "Plan decision rule: offices naming $100 a month or more."),
            ("reply_rate_target", 0.2, "Plan cadence: 150 messages at 20% = 30 conversations."),
            ("min_first_touches_to_judge", 30, "Do not judge a reply rate on fewer first touches than this."),
            ("note_minutes_target", 10, "Plan: notes within ten minutes of each call."),
            ("include_sample", "Y" if self.sample else "N", "N: rows whose row_id starts with SAMPLE are ignored everywhere. Y only in the SAMPLE test copy."),
            ("sample_criterion", '=IF(B18="Y","<>","<>SAMPLE*")', "Calculated. Do not edit."),
            ("clay_offices_export_date", dt.date(2026, 11, 20) if self.sample else None, "Type the date you exported the Clay offices table into Clay_Offices."),
            ("clay_brands_export_date", dt.date(2026, 11, 20) if self.sample else None, "Type the date you exported the Clay brands table into Clay_Brands."),
            ("pipeline_export_rows", EXPORT_N, "Rows available on pipeline_log. A check turns red if events exceed this."),
        ]
        header(ws, 2, 1, "setting", width=30)
        header(ws, 2, 2, "value", width=46)
        header(ws, 2, 3, "what it means", width=90)
        for i, (k, v, note) in enumerate(rows, start=3):
            put(ws, f"A{i}", k, font=F_BOLD)
            c = put(ws, f"B{i}", v)
            if isinstance(v, dt.date) or k in ("as_of_date", "clay_offices_export_date", "clay_brands_export_date"):
                c.number_format = DATE_FMT
            if k == "reply_rate_target":
                c.number_format = "0%"
            put(ws, f"C{i}", note, font=F_NOTE)
            self.cfg[k] = f"Config!$B${i}"
        assert self.cfg["include_sample"] == "Config!$B$19", self.cfg["include_sample"]
        # sample_criterion formula must point at include_sample
        ws["B20"] = '=IF(B19="Y","<>","<>SAMPLE*")'
        ws.freeze_panes = "A3"

    # ------------------------------------------------------------------ log tabs
    def _validation(self, ws, kind, rng):
        if not kind.startswith("list:"):
            return
        name = kind.split(":", 1)[1]
        dv = DataValidation(type="list", formula1="=" + self.list_ref[name], allow_blank=True, showErrorMessage=False)
        ws.add_data_validation(dv)
        dv.add(rng)

    def _input_tab(self, ws, specs, nrows, first_calc_col=None):
        for i, (k, kind, w, helptext, maps) in enumerate(specs, start=1):
            header(ws, 1, i, k, calc=(kind == "formula"), comment=f"{helptext}" + (f"\n\nMaps to: {maps}" if maps else ""), width=w)
            L = CL(i)
            if kind == "date" or (kind == "formula" and k.endswith("_date")):
                for r in range(2, nrows + 2):
                    ws[f"{L}{r}"].number_format = DATE_FMT
            self._validation(ws, kind, f"{L}2:{L}{nrows + 1}")
        ws.freeze_panes = "B2"
        ws.row_dimensions[1].height = 42

    def build_log(self, side):
        name = "Office_Log" if side == "office" else "Brand_Log"
        ws = self.ws[name]
        specs = OFFICE_COLS if side == "office" else BRAND_COLS
        if side == "office":
            calc = ["calc_sync_issue", "calc_row", "calc_valid", "calc_conv_first", "calc_latest", "calc_q_yes", "calc_q_yes_first",
                    "calc_yes_incomplete", "calc_bp_has", "calc_bp_first", "calc_bp_w1", "calc_bp_w2", "calc_bp_g0", "calc_bp_asof",
                    "calc_bp100_first", "calc_spend_has", "calc_spend_first", "calc_spend_asof", "calc_probe_row", "calc_probe_first",
                    "calc_probe_key", "calc_probe_missing_text", "calc_obj1", "calc_obj2", "calc_obj3", "calc_note_min", "calc_yes_any",
                    "calc_maybe", "calc_maybe_first", "calc_yes_any_first", "calc_bp100",
                    "calc_clay_idx", "calc_clay_status", "calc_clay_rank", "calc_clay_yes", "calc_clay_call_date"]
        else:
            calc = ["calc_sync_issue", "calc_row", "calc_valid", "calc_conv_first", "calc_latest", "calc_g0", "calc_g0_first",
                    "calc_g0_strict", "calc_g0_strict_first", "calc_g0_noctrl", "calc_g0_noctrl_first",
                    "calc_wb_has", "calc_wb_first", "calc_wb_w1", "calc_wb_w2", "calc_wb_g0", "calc_wb_asof",
                    "calc_wa_has", "calc_wa_first", "calc_wa_w1", "calc_wa_w2", "calc_wa_g0", "calc_wa_asof",
                    "calc_q2_has", "calc_q2_first", "calc_q2_asof", "calc_wtp_missing_text",
                    "calc_obj1", "calc_obj2", "calc_obj3", "calc_note_min", "calc_yes_any", "calc_yes_any_first",
                    "calc_clay_idx", "calc_clay_status", "calc_clay_rank", "calc_clay_yes", "calc_clay_call_date"]
        C = Cols(specs, calc)
        self._input_tab(ws, specs, LOG_N)
        calc_help = {
            "calc_sync_issue": "Calculated. What disagrees with the latest Clay paste. Fix it in Clay (or fix this row), then re-paste on Friday. Blank = in sync.",
        }
        for k in calc:
            header(ws, 1, C.idx[k], k, calc=True, comment=calc_help.get(k, "Calculated. Do not type here."),
                   width=34 if k == "calc_sync_issue" else 11)
        N1, N2 = 2, LOG_N + 1
        R = lambda k: f"${C.L(k)}${N1}:${C.L(k)}${N2}"
        INC = self.cfg["include_sample"]
        W1, W2, G0, AS = self.cfg["week1_readout"], self.cfg["week2_readout"], self.cfg["gate0_date"], self.cfg["as_of_date"]
        clay = "Clay_Offices" if side == "office" else "Clay_Brands"
        sc = "C" if side == "office" else "D"          # column of Sync's header map for this side
        CR = f"{clay}!$A$2:${CLAY_LAST_COL}${CLAY_N + 1}"

        def earliest(flag, r):
            return (f'=IF({C.L(flag)}{r}=1,IF(COUNTIFS({R("row_id")},$A{r},{R(flag)},1,{R("call_date")},"<"&{C.L("call_date")}{r})'
                    f'+COUNTIFS({R("row_id")},$A{r},{R(flag)},1,{R("call_date")},{C.L("call_date")}{r},{R("calc_row")},"<"&{C.L("calc_row")}{r})=0,1,0),0)')

        def latest(flag, r):
            return (f'=IF({C.L(flag)}{r}=1,IF(COUNTIFS({R("row_id")},$A{r},{R(flag)},1,{R("call_date")},">"&{C.L("call_date")}{r})'
                    f'+COUNTIFS({R("row_id")},$A{r},{R(flag)},1,{R("call_date")},{C.L("call_date")}{r},{R("calc_row")},">"&{C.L("calc_row")}{r})=0,1,0),0)')

        def cut(first, val, cutoff, r):
            return f'=IF(AND({C.L(first)}{r}=1,{C.L("call_date")}{r}<={cutoff}),{C.L(val)}{r},"")'

        hdr_row = f"Sync!${sc}$"
        for r in range(N1, N2 + 1):
            f = {}
            d = f'{C.L("call_date")}{r}'
            f["calc_row"] = f"=ROW()"
            f["calc_valid"] = f'=IF(AND(TRIM($A{r})<>"",ISNUMBER({d})),IF(AND(LEFT($A{r},6)="SAMPLE",{INC}<>"Y"),0,1),0)'
            f["calc_conv_first"] = earliest("calc_valid", r)
            f["calc_latest"] = latest("calc_valid", r)
            f["calc_obj1"] = f'=IF({C.L("calc_valid")}{r}=1,{C.L("objection_1")}{r}&"","")'
            f["calc_obj2"] = f'=IF({C.L("calc_valid")}{r}=1,{C.L("objection_2")}{r}&"","")'
            f["calc_obj3"] = f'=IF({C.L("calc_valid")}{r}=1,{C.L("objection_3")}{r}&"","")'
            f["calc_note_min"] = f'=IF(AND({C.L("calc_valid")}{r}=1,ISNUMBER({C.L("note_minutes")}{r}),{d}<={AS}),{C.L("note_minutes")}{r},"")'
            f["calc_yes_any"] = (f'=IF({C.L("calc_valid")}{r}=1,IF(COUNTIFS({R("row_id")},$A{r},{R("yes_in_principle")},"Y",{R("calc_valid")},1)>0,"Y","N"),"")')
            f["calc_clay_idx"] = (f'=IF({C.L("calc_valid")}{r}=1,IFERROR(MATCH($A{r},INDEX({CR},0,{hdr_row}5),0),""),"")')
            for key, hrow in (("calc_clay_status", 7), ("calc_clay_yes", 17)):
                f[key] = f'=IF({C.L("calc_clay_idx")}{r}="","",IFERROR(INDEX({CR},{C.L("calc_clay_idx")}{r},{hdr_row}{hrow})&"",""))'
            f["calc_clay_call_date"] = f'=IF({C.L("calc_clay_idx")}{r}="","",IFERROR(N(INDEX({CR},{C.L("calc_clay_idx")}{r},{hdr_row}16)),0))'
            f["calc_clay_rank"] = (f'=IF({C.L("calc_clay_status")}{r}="","",IFERROR(INDEX({self.list_ref["status_rank"]},'
                                   f'MATCH({C.L("calc_clay_status")}{r},{self.list_ref["status"]},0)),""))')
            if side == "office":
                f["calc_q_yes"] = (f'=IF(AND({C.L("calc_valid")}{r}=1,{C.L("yes_in_principle")}{r}="Y",{C.L("pantry_owner_named")}{r}="Y",'
                                   f'TRIM({C.L("receiving_window")}{r})<>""),1,0)')
                f["calc_q_yes_first"] = earliest("calc_q_yes", r)
                f["calc_yes_incomplete"] = (f'=IF(AND({C.L("calc_valid")}{r}=1,{C.L("yes_in_principle")}{r}="Y",{C.L("calc_q_yes")}{r}=0),1,0)')
                f["calc_bp_has"] = f'=IF(AND({C.L("calc_valid")}{r}=1,ISNUMBER({C.L("budget_probe_low_usd")}{r})),1,0)'
                f["calc_bp_first"] = earliest("calc_bp_has", r)
                f["calc_bp_w1"] = cut("calc_bp_first", "budget_probe_low_usd", W1, r)
                f["calc_bp_w2"] = cut("calc_bp_first", "budget_probe_low_usd", W2, r)
                f["calc_bp_g0"] = cut("calc_bp_first", "budget_probe_low_usd", G0, r)
                f["calc_bp_asof"] = cut("calc_bp_first", "budget_probe_low_usd", AS, r)
                f["calc_bp100"] = (f'=IF(AND({C.L("calc_bp_has")}{r}=1,N({C.L("budget_probe_low_usd")}{r})>={self.cfg["office_paid_threshold_usd"]}),1,0)')
                f["calc_bp100_first"] = earliest("calc_bp100", r)
                f["calc_spend_has"] = f'=IF(AND({C.L("calc_valid")}{r}=1,ISNUMBER({C.L("monthly_pantry_spend_usd")}{r})),1,0)'
                f["calc_spend_first"] = earliest("calc_spend_has", r)
                f["calc_spend_asof"] = cut("calc_spend_first", "monthly_pantry_spend_usd", AS, r)
                f["calc_probe_row"] = (f'=IF(AND({C.L("calc_valid")}{r}=1,OR(TRIM({C.L("budget_probe_verbatim")}{r})<>"",'
                                       f'ISNUMBER({C.L("budget_probe_low_usd")}{r}))),1,0)')
                f["calc_probe_first"] = earliest("calc_probe_row", r)
                f["calc_probe_key"] = f'=IF({C.L("calc_probe_first")}{r}=1,$A{r},"")'
                f["calc_probe_missing_text"] = (f'=IF(AND({C.L("calc_valid")}{r}=1,{C.L("budget_probe_asked")}{r}="Y",'
                                                f'TRIM({C.L("budget_probe_verbatim")}{r})=""),1,0)')
                f["calc_maybe"] = f'=IF(AND({C.L("calc_valid")}{r}=1,{C.L("yes_in_principle")}{r}="maybe"),1,0)'
                f["calc_maybe_first"] = earliest("calc_maybe", r)
                f["calc_yes_any_first"] = (f'=IF(AND({C.L("calc_valid")}{r}=1,{C.L("yes_in_principle")}{r}="Y"),'
                                           f'IF(COUNTIFS({R("row_id")},$A{r},{R("yes_in_principle")},"Y",{R("calc_valid")},1,{R("call_date")},"<"&{d})'
                                           f'+COUNTIFS({R("row_id")},$A{r},{R("yes_in_principle")},"Y",{R("calc_valid")},1,{R("call_date")},{d},{R("calc_row")},"<"&{C.L("calc_row")}{r})=0,1,0),0)')
            else:
                thr = self.cfg["brand_wtp_threshold_usd"]
                wb_, wa_ = f'{C.L("wtp_before_usd")}{r}', f'{C.L("wtp_after_usd")}{r}'
                f["calc_g0"] = (f'=IF(AND({C.L("calc_valid")}{r}=1,{C.L("controls_budget")}{r}="Y",MAX(N({wb_}),N({wa_}))>={thr}),1,0)')
                f["calc_g0_first"] = earliest("calc_g0", r)
                f["calc_g0_strict"] = (f'=IF(AND({C.L("calc_valid")}{r}=1,{C.L("controls_budget")}{r}="Y",ISNUMBER({wb_})),IF({wb_}>={thr},1,0),0)')
                f["calc_g0_strict_first"] = earliest("calc_g0_strict", r)
                f["calc_g0_noctrl"] = (f'=IF(AND({C.L("calc_valid")}{r}=1,{C.L("controls_budget")}{r}<>"Y",MAX(N({wb_}),N({wa_}))>={thr}),1,0)')
                f["calc_g0_noctrl_first"] = earliest("calc_g0_noctrl", r)
                f["calc_wb_has"] = f'=IF(AND({C.L("calc_valid")}{r}=1,ISNUMBER({wb_})),1,0)'
                f["calc_wb_first"] = earliest("calc_wb_has", r)
                f["calc_wa_has"] = f'=IF(AND({C.L("calc_valid")}{r}=1,ISNUMBER({wa_})),1,0)'
                f["calc_wa_first"] = earliest("calc_wa_has", r)
                for tag, cutoff in (("w1", W1), ("w2", W2), ("g0", G0), ("asof", AS)):
                    f[f"calc_wb_{tag}"] = cut("calc_wb_first", "wtp_before_usd", cutoff, r)
                    f[f"calc_wa_{tag}"] = cut("calc_wa_first", "wtp_after_usd", cutoff, r)
                q2 = f'{C.L("q2_sampling_budget_quarter_low_usd")}{r}'
                f["calc_q2_has"] = f'=IF(AND({C.L("calc_valid")}{r}=1,ISNUMBER({q2})),1,0)'
                f["calc_q2_first"] = earliest("calc_q2_has", r)
                f["calc_q2_asof"] = cut("calc_q2_first", "q2_sampling_budget_quarter_low_usd", AS, r)
                f["calc_wtp_missing_text"] = (f'=IF(AND({C.L("calc_valid")}{r}=1,OR(AND(ISNUMBER({wb_}),TRIM({C.L("wtp_before_verbatim")}{r})=""),'
                                              f'AND(ISNUMBER({wa_}),TRIM({C.L("wtp_after_verbatim")}{r})=""))),1,0)')
                f["calc_yes_any_first"] = (f'=IF(AND({C.L("calc_valid")}{r}=1,{C.L("yes_in_principle")}{r}="Y"),'
                                           f'IF(COUNTIFS({R("row_id")},$A{r},{R("yes_in_principle")},"Y",{R("calc_valid")},1,{R("call_date")},"<"&{d})'
                                           f'+COUNTIFS({R("row_id")},$A{r},{R("yes_in_principle")},"Y",{R("calc_valid")},1,{R("call_date")},{d},{R("calc_row")},"<"&{C.L("calc_row")}{r})=0,1,0),0)')
            st, rk = f'{C.L("calc_clay_status")}{r}', f'{C.L("calc_clay_rank")}{r}'
            f["calc_sync_issue"] = (
                f'=IF(TRIM($A{r})="","",IF(AND(LEFT($A{r},6)="SAMPLE",{INC}<>"Y"),"",'
                f'IF(NOT(ISNUMBER({d})),"call_date is blank or not a date",'
                f'IF({hdr_row}5="","Clay paste is empty or has no row_id column: paste the Clay export on {clay}",'
                f'IF({C.L("calc_clay_idx")}{r}="","row_id not found in the Clay paste: add the Clay row or fix the row_id",'
                f'IF(AND(ISNUMBER({rk}),{rk}>=1,{rk}<=5),"Clay status is "&{st}&": set call_done or later",'
                f'IF(AND({C.L("calc_latest")}{r}=1,{C.L("calc_clay_yes")}{r}<>{C.L("calc_yes_any")}{r}),"Clay yes_in_principle should be "&{C.L("calc_yes_any")}{r},'
                f'IF(AND({C.L("calc_latest")}{r}=1,{C.L("calc_clay_call_date")}{r}<>{d}),"Clay call_date should be "&TEXT({d},"yyyy-mm-dd"),""))))))))')
            for k, formula in f.items():
                c = ws[f"{C.L(k)}{r}"]
                c.value = formula
                c.fill = FILL_CALC
            ws[f"{C.L('calc_clay_call_date')}{r}"].number_format = DATE_FMT
        # hide every calc column except the sync issue
        first_hidden = C.idx["calc_row"]
        last_hidden = C.idx[calc[-1]]
        ws.column_dimensions.group(CL(first_hidden), CL(last_hidden), hidden=True, outline_level=1)
        sync_col = C.L("calc_sync_issue")
        ws.conditional_formatting.add(f"{sync_col}2:{sync_col}{N2}",
                                      FormulaRule(formula=[f'LEN({sync_col}2)>0'], fill=FILL_FAIL))
        setattr(self, f"C_{side}", C)
        return C

    # ------------------------------------------------------------------ Clay pastes and sync
    def build_clay_paste(self, side):
        name = "Clay_Offices" if side == "office" else "Clay_Brands"
        ws = self.ws[name]
        put(ws, "A1", None)
        note = (f"Paste the whole Clay {side}s table export here every Friday: select A1, paste, header row included. "
                f"Columns are found by their header names, so their order does not matter. Area A1:{CLAY_LAST_COL}{CLAY_N + 1}. "
                f"Then type the export date on Config.")
        ws["A1"].comment = Comment(note, "tracker")
        ws.freeze_panes = "A2"

    def build_sync(self):
        ws = self.ws["Sync"]
        put(ws, "A1", "Sync: where the tracker and the Clay tables disagree. Clay is the status store; fix there, then re-paste.", font=F_TITLE)
        put(ws, "A2", "Rows 5 to 18 find each Clay column by its header. A blank number means that column is missing from the paste.", font=F_NOTE)
        header(ws, 4, 2, "Clay column", width=18)
        header(ws, 4, 3, "offices col #", width=12)
        header(ws, 4, 4, "brands col #", width=12)
        header(ws, 4, 5, "note", width=40)
        ws.column_dimensions["A"].width = 4
        self.sync_row = {}
        for i, h in enumerate(CLAY_NEEDED, start=5):
            put(ws, f"B{i}", h)
            put(ws, f"C{i}", f'=IFERROR(MATCH(B{i},Clay_Offices!$A$1:${CLAY_LAST_COL}$1,0),"")', fill=FILL_CALC)
            put(ws, f"D{i}", f'=IFERROR(MATCH(B{i},Clay_Brands!$A$1:${CLAY_LAST_COL}$1,0),"")', fill=FILL_CALC)
            put(ws, f"E{i}", f'=IF(AND(C{i}="",D{i}=""),"missing in both pastes",IF(C{i}="","missing in Clay_Offices",IF(D{i}="","missing in Clay_Brands","")))', fill=FILL_CALC)
            self.sync_row[h] = i
        # header rows used by the log formulas: 5 row_id, 7 status, 16 call_date, 17 yes_in_principle
        assert self.sync_row["row_id"] == 5 and self.sync_row["status"] == 7
        assert self.sync_row["call_date"] == 16 and self.sync_row["yes_in_principle"] == 17
        INC = self.cfg["include_sample"]
        # Clay-side checks, one row per pasted Clay row
        top = 22
        put(ws, f"A{top - 2}", "Clay rows that disagree with the tracker or with themselves", font=F_BOLD)
        for side, base, clay, sc, log, hand, hand_status in (
                ("office", 2, "Clay_Offices", "C", "Office_Log", "signed_offices", "signed"),
                ("brand", 9, "Clay_Brands", "D", "Brand_Log", "paid_brands", "paid")):
            cols = ["i", f"{side} row_id", "status", "do_not_contact", "in tracker", "issue"]
            for j, h in enumerate(cols):
                header(ws, top - 1, base + j, h, calc=True, width=[5, 16, 14, 8, 8, 40][j])
            CR = f"{clay}!$A$2:${CLAY_LAST_COL}${CLAY_N + 1}"
            for i in range(1, CLAY_N + 1):
                r = top + i - 1
                a, b, c, d, e, g = (CL(base + k) for k in range(6))
                ws[f"{a}{r}"] = i
                ws[f"{b}{r}"] = f'=IFERROR(INDEX({CR},{a}{r},${sc}$5)&"","")'
                ws[f"{c}{r}"] = f'=IFERROR(INDEX({CR},{a}{r},${sc}$7)&"","")'
                ws[f"{d}{r}"] = f'=IFERROR(INDEX({CR},{a}{r},${sc}$8)&"","")'
                ws[f"{e}{r}"] = f'=IF({b}{r}="","",IF(COUNTIF({log}!$A$2:$A${LOG_N + 1},{b}{r})>0,"Y","N"))'
                rank = f'IFERROR(INDEX({self.list_ref["status_rank"]},MATCH({c}{r},{self.list_ref["status"]},0)),-1)'
                ws[f"{g}{r}"] = (
                    f'=IF(OR({b}{r}="",AND(LEFT({b}{r},6)="SAMPLE",{INC}<>"Y")),"",'
                    f'IF({rank}=-1,"status \'"&{c}{r}&"\' is not a CONTRACTS status",'
                    f'IF(AND({c}{r}="{hand_status}",COUNTIF({hand}!$__HANDRID__$2:$__HANDRID__${HAND_N + 1},{b}{r})=0),'
                    f'"status {hand_status} but no {hand} row"&IF({e}{r}="N"," and no tracker row",""),'
                    f'IF(AND({rank}>=6,{e}{r}="N"),"status "&{c}{r}&" but no tracker row",'
                    f'IF(AND({d}{r}="Y",{c}{r}<>"do_not_contact"),"do_not_contact = Y but status is "&{c}{r},'
                    f'IF(AND({c}{r}="do_not_contact",{d}{r}<>"Y"),"status do_not_contact but do_not_contact is not Y",""))))))')
                for col_ in (a, b, c, d, e, g):
                    ws[f"{col_}{r}"].fill = FILL_CALC
            ws.conditional_formatting.add(f"{CL(base + 5)}{top}:{CL(base + 5)}{top + CLAY_N - 1}",
                                          FormulaRule(formula=[f'LEN({CL(base + 5)}{top})>0'], fill=FILL_FAIL))
        self.sync_top = top
        # handoff rows whose Clay status is not signed / paid
        put(ws, "P20", "Handoff rows whose Clay status is not signed / paid", font=F_BOLD)
        for j, h in enumerate(["signed_offices clay_row_id", "Clay status", "issue"]):
            header(ws, 21, 16 + j, h, calc=True, width=[18, 14, 36][j])
        for j, h in enumerate(["paid_brands clay_row_id", "Clay status", "issue"]):
            header(ws, 21, 20 + j, h, calc=True, width=[18, 14, 36][j])
        ws.freeze_panes = "A5"

    def fix_hand_refs(self):
        """Replace the placeholder for the handoff clay_row_id column once those tabs exist."""
        ws = self.ws["Sync"]
        so_col = CL(len(OFFICE_INTAKE) + 2)                 # clay_row_id is the 2nd extra column
        pb_col = CL(len(BRAND_INTAKE) + 2)
        top = self.sync_top
        for i in range(1, CLAY_N + 1):
            r = top + i - 1
            for col_, rc in ((CL(2 + 5), so_col), (CL(9 + 5), pb_col)):
                ws[f"{col_}{r}"].value = ws[f"{col_}{r}"].value.replace("__HANDRID__", rc)
        INC = self.cfg["include_sample"]
        for i in range(HAND_N):
            r = 22 + i
            for base, tab, rc, clay, sc, want in ((16, "signed_offices", so_col, "Clay_Offices", "C", "signed"),
                                                  (20, "paid_brands", pb_col, "Clay_Brands", "D", "paid")):
                a, b, c = CL(base), CL(base + 1), CL(base + 2)
                CR = f"{clay}!$A$2:${CLAY_LAST_COL}${CLAY_N + 1}"
                ws[f"{a}{r}"] = f'=IF({tab}!{rc}{i + 2}="","",{tab}!{rc}{i + 2}&"")'
                ws[f"{b}{r}"] = f'=IF({a}{r}="","",IFERROR(INDEX({CR},MATCH({a}{r},INDEX({CR},0,${sc}$5),0),${sc}$7)&"","not in Clay"))'
                ws[f"{c}{r}"] = (f'=IF(OR({a}{r}="",AND(LEFT({a}{r},6)="SAMPLE",{INC}<>"Y")),"",IF({b}{r}="{want}","",'
                                 f'"Clay status is "&{b}{r}&": set {want}"))')
                for col_ in (a, b, c):
                    ws[f"{col_}{r}"].fill = FILL_CALC
        self.hand_rid = {"office": so_col, "brand": pb_col}

    # ------------------------------------------------------------------ handoff tabs
    def build_handoff(self):
        # signed_offices
        ws = self.ws["signed_offices"]
        specs = [(k, "list:yn" if k == "pantry_owner_is_contact" else
                  "list:intake_receiving_type" if k == "receiving_type" else
                  "list:yesno_unsure" if k == "coi_required" else
                  "list:survey_channel" if k == "survey_channel" else
                  "list:intake_source" if k == "source" else
                  "num" if k == "tuesday_headcount" else "text", 14,
                  "Copied from the office_intake row (CONTRACTS 6.3), same column order, so the row pastes in one go.", "CONTRACTS 6.3 office_intake")
                 for k in OFFICE_INTAKE] + SIGNED_EXTRA
        self._input_tab(ws, specs, HAND_N)
        self.signed_cols = Cols(specs, [])
        S = self.signed_cols
        OL = self.C_office
        key_rng = f"Office_Log!${OL.L('calc_probe_key')}$2:${OL.L('calc_probe_key')}${LOG_N + 1}"
        for r in range(2, HAND_N + 2):
            rid = f"{S.L('clay_row_id')}{r}"
            m = f"MATCH({rid},{key_rng},0)"
            for k, src, kind in (("budget_probe_verbatim", "budget_probe_verbatim", "text"),
                                 ("budget_probe_date", "call_date", "date"),
                                 ("budget_probe_monthly_usd", "budget_probe_low_usd", "num")):
                srng = f"Office_Log!${OL.L(src)}$2:${OL.L(src)}${LOG_N + 1}"
                if kind == "text":
                    fml = f'=IF({rid}="","",IFERROR(INDEX({srng},{m})&"",""))'
                else:
                    fml = f'=IF({rid}="","",IFERROR(IF(ISNUMBER(INDEX({srng},{m})),INDEX({srng},{m}),""),""))'
                c = ws[f"{S.L(k)}{r}"]
                c.value = fml
                c.fill = FILL_CALC
                if kind == "date":
                    c.number_format = DATE_FMT
        # paid_brands
        ws = self.ws["paid_brands"]
        def bkind(k):
            if k in ("can_issue_discount_code", "budget_approver_is_contact", "excluded_category_confirmed"):
                return "list:yn"
            if k.startswith("q") and k[1].isdigit() and k[2] == "_" and not k.startswith("q7"):
                return "list:yesno_unsure_yn"
            if k == "category":
                return "list:category"
            if k == "source":
                return "list:intake_source"
            return "text"
        LISTS_EXTRA = {"yesno_unsure_yn": ["Y", "N", "unsure"]}
        for nm, vals in LISTS_EXTRA.items():
            if nm not in self.list_ref:
                wsl = self.ws["Lists"]
                col = wsl.max_column + 1
                header(wsl, 1, col, nm, width=14)
                for i, v in enumerate(vals, start=2):
                    wsl.cell(row=i, column=col, value=v)
                self.list_ref[nm] = f"Lists!${CL(col)}$2:${CL(col)}${len(vals) + 1}"
        specs = [(k, bkind(k), 14, "Copied from the brand_intake row (CONTRACTS 6.3), same column order.", "CONTRACTS 6.3 brand_intake")
                 for k in BRAND_INTAKE] + PAID_EXTRA
        self._input_tab(ws, specs, HAND_N)
        self.paid_cols = Cols(specs, [])
        P = self.paid_cols
        for r in range(2, HAND_N + 2):
            c = ws[f"{P.L('payment_received_date')}{r}"]
            c.value = f'=IF(ISNUMBER({P.L("payment_1_date")}{r}),{P.L("payment_1_date")}{r},"")'
            c.fill = FILL_CALC
            c.number_format = DATE_FMT
        # later_events
        ws = self.ws["later_events"]
        self._input_tab(ws, LATER_COLS, LATER_N)
        self.later_cols = Cols(LATER_COLS, [])

    # ------------------------------------------------------------------ pipeline
    def build_pipeline(self):
        calc = self.ws["Pipeline_Calc"]
        hdrs = ["key", "date", "side", "org_id", "org_name", "event", "value_number", "value_text", "controls_budget", "notes", "block"]
        for j, h in enumerate(hdrs, start=1):
            header(calc, 1, j, h, calc=True, width=[14, 11, 8, 15, 18, 16, 10, 24, 8, 26, 22][j - 1])
        put(calc, "M1", "One row per possible event, built from the logs, the handoff tabs and the Clay pastes. Sorted onto pipeline_log by key (date, then block, then row).", font=F_NOTE)
        INC = self.cfg["include_sample"]
        OL, BL, S, P, LT = self.C_office, self.C_brand, self.signed_cols, self.paid_cols, self.later_cols
        r = 2
        blocks = []

        def emit(block_no, block_name, n, gen):
            nonlocal r
            for i in range(1, n + 1):
                cells = gen(i)            # dict of column letter -> formula (B..J); B is the date
                for col_, v in cells.items():
                    calc[f"{col_}{r}"] = v
                calc[f"A{r}"] = f'=IF(B{r}="","",B{r}+({block_no}*1000+{i})/10000000)'
                calc[f"K{r}"] = block_name
                calc[f"B{r}"].number_format = DATE_FMT
                r += 1
            blocks.append((block_no, block_name, n))

        def txt(ref):
            return f'IF({ref}="","",{ref}&"")'

        def num(ref):
            return f'IF(ISNUMBER({ref}),{ref},"")'

        def log_gen(tab, C, side, cond, event, value=None, vtext=None, ctrl=None, notes=None):
            def g(i):
                rr = i + 1
                ok = cond(rr)
                return {
                    "B": f'=IF({ok},{tab}!{C.L("call_date")}{rr},"")',
                    "C": f'=IF(B{{R}}="","","{side}")',
                    "D": f'=IF(B{{R}}="","",{tab}!$A{rr}&"")',
                    "E": f'=IF(B{{R}}="","",{txt(f"{tab}!{C.L('company')}{rr}")})',
                    "F": f'=IF(B{{R}}="","","{event}")',
                    "G": f'=IF(B{{R}}="","",{value(rr) if value else chr(34)*2})',
                    "H": f'=IF(B{{R}}="","",{vtext(rr) if vtext else chr(34)*2})',
                    "I": f'=IF(B{{R}}="","",{ctrl(rr) if ctrl else chr(34)*2})',
                    "J": f'=IF(B{{R}}="","",{notes(rr) if notes else chr(34)*2})',
                }
            return g

        def fix_rowref(gen):
            def g(i):
                cells = gen(i)
                return {k: v.replace("{R}", str(r_now[0] + i - 1)) for k, v in cells.items()}
            return g

        # helper so the generated formulas can refer to their own row
        r_now = [r]

        def emit_log(block_no, name, gen):
            r_now[0] = r
            emit(block_no, name, LOG_N, fix_rowref(gen))

        V = lambda tab, C, rr: f"{tab}!{C.L('calc_valid')}{rr}=1"
        emit_log(1, "office conversation", log_gen("Office_Log", OL, "office", lambda rr: V("Office_Log", OL, rr), "conversation",
                                                    notes=lambda rr: txt(f"Office_Log!{OL.L('call_type')}{rr}")))
        emit_log(2, "office yes_in_principle", log_gen("Office_Log", OL, "office", lambda rr: f"Office_Log!{OL.L('calc_q_yes')}{rr}=1",
                                                        "yes_in_principle",
                                                        notes=lambda rr: f'"owner: "&Office_Log!{OL.L("pantry_owner_title")}{rr}&"; window: "&Office_Log!{OL.L("receiving_window")}{rr}'))
        emit_log(3, "office budget_probe", log_gen("Office_Log", OL, "office", lambda rr: f"Office_Log!{OL.L('calc_probe_row')}{rr}=1",
                                                    "budget_probe",
                                                    value=lambda rr: num(f"Office_Log!{OL.L('budget_probe_low_usd')}{rr}"),
                                                    vtext=lambda rr: txt(f"Office_Log!{OL.L('budget_probe_verbatim')}{rr}"),
                                                    notes=lambda rr: (f'IF(AND(ISNUMBER(Office_Log!{OL.L("budget_probe_high_usd")}{rr}),'
                                                                      f'N(Office_Log!{OL.L("budget_probe_high_usd")}{rr})>N(Office_Log!{OL.L("budget_probe_low_usd")}{rr})),'
                                                                      f'"range to "&Office_Log!{OL.L("budget_probe_high_usd")}{rr}&" per month","")')))
        emit_log(4, "brand conversation", log_gen("Brand_Log", BL, "brand", lambda rr: V("Brand_Log", BL, rr), "conversation",
                                                   notes=lambda rr: txt(f"Brand_Log!{BL.L('call_type')}{rr}")))
        emit_log(5, "brand yes_in_principle", log_gen("Brand_Log", BL, "brand",
                                                       lambda rr: f'AND({V("Brand_Log", BL, rr)},Brand_Log!{BL.L("yes_in_principle")}{rr}="Y")',
                                                       "yes_in_principle", ctrl=lambda rr: txt(f"Brand_Log!{BL.L('controls_budget')}{rr}")))
        emit_log(6, "brand budget_probe before $1,500", log_gen(
            "Brand_Log", BL, "brand",
            lambda rr: f'AND({V("Brand_Log", BL, rr)},OR(ISNUMBER(Brand_Log!{BL.L("wtp_before_usd")}{rr}),TRIM(Brand_Log!{BL.L("wtp_before_verbatim")}{rr})<>""))',
            "budget_probe", value=lambda rr: num(f"Brand_Log!{BL.L('wtp_before_usd')}{rr}"),
            vtext=lambda rr: txt(f"Brand_Log!{BL.L('wtp_before_verbatim')}{rr}"),
            ctrl=lambda rr: txt(f"Brand_Log!{BL.L('controls_budget')}{rr}"),
            notes=lambda rr: f'IF(Brand_Log!{BL.L("wtp_conversion_note")}{rr}="","","before_1500; "&Brand_Log!{BL.L("wtp_conversion_note")}{rr})'))
        emit_log(7, "brand budget_probe after $1,500", log_gen(
            "Brand_Log", BL, "brand",
            lambda rr: (f'AND({V("Brand_Log", BL, rr)},Brand_Log!{BL.L("price_1500_mentioned")}{rr}="Y",'
                        f'OR(ISNUMBER(Brand_Log!{BL.L("wtp_after_usd")}{rr}),TRIM(Brand_Log!{BL.L("wtp_after_verbatim")}{rr})<>""))'),
            "budget_probe", value=lambda rr: num(f"Brand_Log!{BL.L('wtp_after_usd')}{rr}"),
            vtext=lambda rr: txt(f"Brand_Log!{BL.L('wtp_after_verbatim')}{rr}"),
            ctrl=lambda rr: txt(f"Brand_Log!{BL.L('controls_budget')}{rr}"),
            notes=lambda rr: '"after_1500"'))

        def sample_ok(ref):
            return f'OR(LEFT({ref},6)<>"SAMPLE",{INC}="Y")'

        # signed offices
        def g_signed(i):
            rr = i + 1
            rid = f"signed_offices!{S.L('clay_row_id')}{rr}"
            dte = f"signed_offices!{S.L('agreement_signed_date')}{rr}"
            R_ = r_now[0] + i - 1
            return {"B": f'=IF(AND(ISNUMBER({dte}),TRIM({rid})<>"",{sample_ok(rid)}),{dte},"")',
                    "C": f'=IF(B{R_}="","","office")', "D": f'=IF(B{R_}="","",{rid}&"")',
                    "E": f'=IF(B{R_}="","",{txt("signed_offices!" + S.L("company") + str(rr))})',
                    "F": f'=IF(B{R_}="","","signed")',
                    "G": f'=IF(B{R_}="","",{num("signed_offices!" + S.L("tuesday_headcount") + str(rr))})',
                    "H": f'=IF(B{R_}="","","")', "I": f'=IF(B{R_}="","","")',
                    "J": f'=IF(B{R_}="","",{txt("signed_offices!" + S.L("office_id") + str(rr))})'}
        r_now[0] = r
        emit(8, "office signed", HAND_N, g_signed)

        def g_paid(k):
            def g(i):
                rr = i + 1
                rid = f"paid_brands!{P.L('clay_row_id')}{rr}"
                dte = f"paid_brands!{P.L(f'payment_{k}_date')}{rr}"
                amt = f"paid_brands!{P.L(f'payment_{k}_usd')}{rr}"
                R_ = r_now[0] + i - 1
                return {"B": f'=IF(AND(ISNUMBER({dte}),ISNUMBER({amt}),TRIM({rid})<>"",{sample_ok(rid)}),{dte},"")',
                        "C": f'=IF(B{R_}="","","brand")', "D": f'=IF(B{R_}="","",{rid}&"")',
                        "E": f'=IF(B{R_}="","",{txt("paid_brands!" + P.L("brand_name") + str(rr))})',
                        "F": f'=IF(B{R_}="","","paid")', "G": f'=IF(B{R_}="","",{amt})',
                        "H": f'=IF(B{R_}="","","")', "I": f'=IF(B{R_}="","","")',
                        "J": (f'=IF(B{R_}="","","payment {k}; "&paid_brands!{P.L("brand_id")}{rr}&"; "&'
                              f'paid_brands!{P.L("tier")}{rr}&"; invoice "&paid_brands!{P.L("invoice_id")}{rr})')}
            return g
        r_now[0] = r
        emit(9, "brand paid (payment 1)", HAND_N, g_paid(1))
        r_now[0] = r
        emit(10, "brand paid (payment 2)", HAND_N, g_paid(2))

        def g_later(i):
            rr = i + 1
            rid = f"later_events!{LT.L('clay_row_id')}{rr}"
            dte = f"later_events!{LT.L('date')}{rr}"
            ev = f"later_events!{LT.L('event')}{rr}"
            R_ = r_now[0] + i - 1
            return {"B": f'=IF(AND(ISNUMBER({dte}),TRIM({rid})<>"",OR({ev}="renewal_answer",{ev}="opt_out"),{sample_ok(rid)}),{dte},"")',
                    "C": f'=IF(B{R_}="","",later_events!{LT.L("side")}{rr}&"")', "D": f'=IF(B{R_}="","",{rid}&"")',
                    "E": f'=IF(B{R_}="","",{txt("later_events!" + LT.L("org_name") + str(rr))})',
                    "F": f'=IF(B{R_}="","",{ev}&"")',
                    "G": f'=IF(B{R_}="","",{num("later_events!" + LT.L("value_number") + str(rr))})',
                    "H": f'=IF(B{R_}="","",{txt("later_events!" + LT.L("value_text") + str(rr))})',
                    "I": f'=IF(B{R_}="","","")',
                    "J": f'=IF(B{R_}="","",{txt("later_events!" + LT.L("notes") + str(rr))})'}
        r_now[0] = r
        emit(11, "later events", LATER_N, g_later)

        def g_touch(side, clay, sc, k):
            def g(i):
                CR = f"{clay}!$A$2:${CLAY_LAST_COL}${CLAY_N + 1}"
                tr = self.sync_row[f"touch_{k}_date"]
                R_ = r_now[0] + i - 1
                rid = f'IFERROR(INDEX({CR},{i},Sync!${sc}$5)&"","")'
                dte = f'IFERROR(N(INDEX({CR},{i},Sync!${sc}${tr})),0)'
                return {"B": f'=IF(AND({dte}>0,{rid}<>"",OR(LEFT({rid},6)<>"SAMPLE",{INC}="Y")),{dte},"")',
                        "C": f'=IF(B{R_}="","","{side}")', "D": f'=IF(B{R_}="","",{rid})',
                        "E": f'=IF(B{R_}="","",IFERROR(INDEX({CR},{i},Sync!${sc}$6)&"",""))',
                        "F": f'=IF(B{R_}="","","outreach_sent")', "G": f'=IF(B{R_}="","","")', "H": f'=IF(B{R_}="","","")',
                        "I": f'=IF(B{R_}="","","")',
                        "J": (f'=IF(B{R_}="","","touch_{k}; "&IFERROR(INDEX({CR},{i},Sync!${sc}${self.sync_row["sequence"]})&"","")&"; "&'
                              f'IFERROR(INDEX({CR},{i},Sync!${sc}${self.sync_row["channel"]})&"",""))')}
            return g
        bno = 12
        for side, clay, sc in (("office", "Clay_Offices", "C"), ("brand", "Clay_Brands", "D")):
            for k in (1, 2, 3):
                r_now[0] = r
                emit(bno, f"{side} outreach touch {k}", CLAY_N, g_touch(side, clay, sc, k))
                bno += 1
        self.calc_last = r - 1
        for rr in range(2, r):
            for col_ in "ABCDEFGHIJ":
                calc[f"{col_}{rr}"].fill = FILL_CALC
        calc.freeze_panes = "A2"

        # sort helper
        srt = self.ws["Pipeline_Sort"]
        for j, h in enumerate(["j", "key", "calc row"], start=1):
            header(srt, 1, j, h, calc=True, width=12)
        keys = f"Pipeline_Calc!$A$2:$A${self.calc_last}"
        for j in range(1, EXPORT_N + 1):
            rr = j + 1
            srt[f"A{rr}"] = j
            srt[f"B{rr}"] = f'=IFERROR(SMALL({keys},A{rr}),"")'
            srt[f"C{rr}"] = f'=IF(B{rr}="","",MATCH(B{rr},{keys},0))'
        # export tab: exactly H's nine columns
        out = self.ws["pipeline_log"]
        for j, h in enumerate(PIPELINE_COLS, start=1):
            header(out, 1, j, h, width=[11, 8, 15, 20, 16, 10, 30, 9, 30][j - 1],
                   comment="Generated. Do not type here. File > Download > CSV (this tab only) and save as desk-drop-outreach/exports/pipeline_log.csv. Columns are exactly financial-model/HANDOFF.md section 3.")
        src_cols = "BCDEFGHIJ"
        for j in range(1, EXPORT_N + 1):
            rr = j + 1
            for k, sc_ in enumerate(src_cols, start=1):
                c = out.cell(row=rr, column=k)
                c.value = f'=IF(Pipeline_Sort!$C{rr}="","",INDEX(Pipeline_Calc!${sc_}$2:${sc_}${self.calc_last},Pipeline_Sort!$C{rr}))'
                if k == 1:
                    c.number_format = DATE_FMT
        out.freeze_panes = "A2"
        self.pipeline_blocks = blocks

    # ------------------------------------------------------------------ scorecard
    def build_scorecard(self):
        ws = self.ws["Scorecard"]
        cfg = self.cfg
        OL, BL = self.C_office, self.C_brand
        INC, SC = cfg["include_sample"], cfg["sample_criterion"]
        for col_, w in zip("ABCDEFGH", [58, 13, 13, 13, 13, 11, 60, 4]):
            ws.column_dimensions[col_].width = w
        sample_count = ("COUNTIF(Office_Log!$A$2:$A$201,\"SAMPLE*\")+COUNTIF(Brand_Log!$A$2:$A$201,\"SAMPLE*\")"
                        f"+COUNTIF(signed_offices!${self.hand_rid['office']}$2:${self.hand_rid['office']}${HAND_N + 1},\"SAMPLE*\")"
                        f"+COUNTIF(paid_brands!${self.hand_rid['brand']}$2:${self.hand_rid['brand']}${HAND_N + 1},\"SAMPLE*\")"
                        f"+COUNTIF(later_events!$C$2:$C${LATER_N + 1},\"SAMPLE*\")"
                        f"+IFERROR(COUNTIF(INDEX(Clay_Offices!$A$2:${CLAY_LAST_COL}${CLAY_N + 1},0,Sync!$C$5),\"SAMPLE*\"),0)"
                        f"+IFERROR(COUNTIF(INDEX(Clay_Brands!$A$2:${CLAY_LAST_COL}${CLAY_N + 1},0,Sync!$D$5),\"SAMPLE*\"),0)")
        ws.merge_cells("A1:G1")
        put(ws, "A1", f'=IF(({sample_count})>0,"SAMPLE: this file holds "&({sample_count})&" SAMPLE rows. Illustrative placeholders, not results. '
                      f'include_sample = "&{INC}&IF({INC}="Y"," (SAMPLE rows are counted)"," (SAMPLE rows are ignored)"),"")',
            font=F_WHITE_BOLD)
        ws.conditional_formatting.add("A1:G1", FormulaRule(formula=['LEN($A$1)>0'], fill=FILL_SAMPLE))
        put(ws, "A2", f'={cfg["company_name"]}&" · Friday scorecard"', font=F_TITLE)
        put(ws, "A3", f'="As of "&TEXT({cfg["as_of_date"]},"ddd yyyy-mm-dd")&". Gate 0 is "&TEXT({cfg["gate0_date"]},"ddd yyyy-mm-dd")&" (derived, founder to confirm). Counts are distinct offices or brands, by call_date."',
            font=F_NOTE)
        heads = ["Measure", "Fri wk 1", "Fri wk 2", "Gate 0", "As of", "Target", "How it is counted"]
        r = 5
        for j, h in enumerate(heads, start=1):
            header(ws, r, j, h)
        r = 6
        put(ws, f"A{r}", "Cut-off date", font=F_NOTE)
        for col_, ref in zip("BCDE", [cfg["week1_readout"], cfg["week2_readout"], cfg["gate0_date"], cfg["as_of_date"]]):
            put(ws, f"{col_}{r}", f"={ref}", fmt=DATE_FMT, font=F_NOTE)
        cut_row = 6
        self.sc = {}

        def rng(tab, C, k):
            return f"{tab}!${C.L(k)}$2:${C.L(k)}${LOG_N + 1}"

        def section(title):
            nonlocal r
            r += 1
            ws.merge_cells(f"A{r}:G{r}")
            put(ws, f"A{r}", title, font=F_BOLD, fill=FILL_SEC)
            r += 1

        def row_counts(label, tab, C, flag, target=None, how="", key=None, fmt="0"):
            nonlocal r
            put(ws, f"A{r}", label)
            for col_ in "BCDE":
                put(ws, f"{col_}{r}", f'=COUNTIFS({rng(tab, C, flag)},1,{rng(tab, C, "call_date")},"<="&{col_}${cut_row})', fmt=fmt, font=F_BOLD)
            if target is not None:
                put(ws, f"F{r}", f"={target}" if isinstance(target, str) else target)
            put(ws, f"G{r}", how, font=F_NOTE, align=WRAP)
            if key:
                self.sc[key] = r
            r += 1

        def row_status(label, count_row, target, key):
            nonlocal r
            put(ws, f"A{r}", label, font=F_BOLD)
            for col_ in "BCDE":
                put(ws, f"{col_}{r}", f'=IF({col_}{count_row}>={target},"PASS",IF({col_}${cut_row}<{cfg["gate0_date"]},"not yet","FAIL"))', font=F_BOLD)
            put(ws, f"G{r}", "PASS once the count reaches the target. Before Gate 0 a shortfall reads 'not yet'; on or after Gate 0 it reads FAIL.", font=F_NOTE, align=WRAP)
            self.sc[key] = r
            r += 1

        def row_median(label, tab, C, prefix, how, key, money=True):
            nonlocal r
            put(ws, f"A{r}", label)
            for col_, tag in zip("BCDE", ["w1", "w2", "g0", "asof"]):
                rg = rng(tab, C, f"{prefix}_{tag}")
                put(ws, f"{col_}{r}", f'=IF(COUNT({rg})=0,"none yet",MEDIAN({rg}))', fmt='"$"#,##0' if money else "0", font=F_BOLD)
            put(ws, f"G{r}", how, font=F_NOTE, align=WRAP)
            self.sc[key] = r
            r += 1

        def row_count_vals(label, tab, C, prefix, how, key, crit=None):
            nonlocal r
            put(ws, f"A{r}", label)
            for col_, tag in zip("BCDE", ["w1", "w2", "g0", "asof"]):
                rg = rng(tab, C, f"{prefix}_{tag}")
                put(ws, f"{col_}{r}", f'=COUNT({rg})' if crit is None else f'=COUNTIF({rg},{crit})', fmt="0", font=F_BOLD)
            put(ws, f"G{r}", how, font=F_NOTE, align=WRAP)
            self.sc[key] = r
            r += 1

        section("Offices (Gate 0: at least 5 of 15 say yes in principle AND name a pantry owner AND a receiving window)")
        row_counts("Office conversations held", "Office_Log", OL, "calc_conv_first", cfg["target_office_conversations"],
                   "Distinct row_ids in Office_Log with a call_date on or before the cut-off.", "o_conv")
        row_counts("Yes in principle, pantry owner named, receiving window named", "Office_Log", OL, "calc_q_yes_first",
                   cfg["target_office_yes"], "The Gate 0 count. One per office, from its first qualifying conversation.", "o_yes")
        row_status("Gate 0, office side", self.sc["o_yes"], cfg["target_office_yes"], "o_status")
        row_counts("Yes in principle, any (owner or window may be missing)", "Office_Log", OL, "calc_yes_any_first", None,
                   "Offices that said Y at least once. The gap to the row above is follow-up work: get the owner and the window.", "o_yes_any")
        row_counts("Said maybe at least once (someone else must agree)", "Office_Log", OL, "calc_maybe_first", None,
                   "Plan Phase 1: 'I need to ask facilities and HR' is a maybe, not a yes.", "o_maybe")
        row_median("Median budget-probe answer, USD a month", "Office_Log", OL, "calc_bp",
                   "First numeric answer per office; a range counts at its low end; 'no budget' counts as 0; no number is left out.", "o_bp_med")
        row_count_vals("Offices that gave a number (0 included)", "Office_Log", OL, "calc_bp",
                       "The n behind the median.", "o_bp_n")
        row_count_vals("Of those, said no budget (0)", "Office_Log", OL, "calc_bp", "Counted inside the median.", "o_bp_zero", crit="0")
        put(ws, f"A{r}", "Offices naming $100 a month or more (decision-rule input), as of")
        put(ws, f"E{r}", f'=COUNTIFS({rng("Office_Log", OL, "calc_bp100_first")},1,{rng("Office_Log", OL, "call_date")},"<="&E${cut_row})', fmt="0", font=F_BOLD)
        put(ws, f"G{r}", "Plan decision rule: office-paid tier is tested if at least five offices named $100 a month or more.", font=F_NOTE, align=WRAP)
        self.sc["o_bp100"] = r
        r += 1
        put(ws, f"A{r}", "Median monthly pantry spend today, USD, as of")
        rg = rng("Office_Log", OL, "calc_spend_asof")
        put(ws, f"E{r}", f'=IF(COUNT({rg})=0,"none yet",MEDIAN({rg}))', fmt='"$"#,##0', font=F_BOLD)
        put(ws, f"F{r}", f'=COUNT({rg})', fmt='"n="0')
        put(ws, f"G{r}", "First number per office, from Q1. Context for the budget probe.", font=F_NOTE, align=WRAP)
        self.sc["o_spend"] = r
        r += 1

        section("Brands (Gate 0: at least 3 of 15 say they would pay $500 or more AND the speaker controls the budget)")
        row_counts("Brand conversations held", "Brand_Log", BL, "calc_conv_first", cfg["target_brand_conversations"],
                   "Distinct row_ids in Brand_Log with a call_date on or before the cut-off.", "b_conv")
        row_counts("Would pay $500 or more and controls the budget", "Brand_Log", BL, "calc_g0_first", cfg["target_brand_yes"],
                   "The Gate 0 count: the higher of the before and after numbers is $500 or more, and controls_budget = Y. Same rule as the financial model.", "b_yes")
        row_status("Gate 0, brand side", self.sc["b_yes"], cfg["target_brand_yes"], "b_status")
        row_counts("Strict read: named $500 or more BEFORE hearing $1,500, and controls the budget", "Brand_Log", BL, "calc_g0_strict_first", None,
                   "Shown so an anchored answer is not mistaken for an unprompted one.", "b_strict")
        row_counts("Said $500 or more but the speaker does not control the budget", "Brand_Log", BL, "calc_g0_noctrl_first", None,
                   "Not counted for Gate 0 from that conversation. Ask for a call with the budget owner.", "b_noctrl")
        row_median("Median brand number before $1,500 was mentioned, USD per campaign", "Brand_Log", BL, "calc_wb",
                   "First numeric before-answer per brand; 'nothing' counts as 0; no number is left out.", "b_wb_med")
        row_count_vals("Brands that named a number before $1,500", "Brand_Log", BL, "calc_wb", "The n behind the median.", "b_wb_n")
        row_median("Median brand number after hearing $1,500, USD per campaign", "Brand_Log", BL, "calc_wa",
                   "First numeric after-answer per brand.", "b_wa_med")
        row_count_vals("Brands that answered after hearing $1,500", "Brand_Log", BL, "calc_wa", "The n behind the median.", "b_wa_n")
        put(ws, f"A{r}", "Median quarterly sampling budget, USD (low end), as of")
        rg = rng("Brand_Log", BL, "calc_q2_asof")
        put(ws, f"E{r}", f'=IF(COUNT({rg})=0,"none yet",MEDIAN({rg}))', fmt='"$"#,##0', font=F_BOLD)
        put(ws, f"F{r}", f'=COUNT({rg})', fmt='"n="0')
        put(ws, f"G{r}", "From Q2. Context: a $600 or $1,500 campaign against what they spend now.", font=F_NOTE, align=WRAP)
        self.sc["b_q2"] = r
        r += 1

        section("Gate 0 overall")
        o, b = self.sc["o_status"], self.sc["b_status"]
        put(ws, f"A{r}", "Gate 0 result", font=F_BOLD)
        for col_ in "BCDE":
            put(ws, f"{col_}{r}", f'=IF(AND({col_}{o}="PASS",{col_}{b}="PASS"),"PASS",IF(OR({col_}{o}="FAIL",{col_}{b}="FAIL"),"FAIL","not yet"))', font=F_BOLD)
        self.sc["g0"] = r
        r += 1
        put(ws, f"A{r}", "Sentence for the Gate 0 decision (as of)", font=F_BOLD)
        ws.merge_cells(f"B{r}:G{r}")
        oy, oc, by, bc = self.sc["o_yes"], self.sc["o_conv"], self.sc["b_yes"], self.sc["b_conv"]
        put(ws, f"B{r}", (f'="As of "&TEXT(E${cut_row},"yyyy-mm-dd")&": "&E{oy}&" of "&E{oc}&" offices said yes with a pantry owner and a receiving window (target "&F{oy}&"); "'
                          f'&E{by}&" of "&E{bc}&" brands would pay $"&{cfg["brand_wtp_threshold_usd"]}&" or more and control the budget (target "&F{by}&"). Gate 0: "&E{self.sc["g0"]}&"."'),
            align=WRAP)
        ws.row_dimensions[r].height = 32
        self.sc["sentence"] = r
        r += 1
        put(ws, f"A{r}", "If it fails (plan)", font=F_NOTE)
        ws.merge_cells(f"B{r}:G{r}")
        put(ws, f"B{r}", "Fewer than 3 brands: test the office-paid version for three more weeks. Fewer than 5 offices: change the cluster or the office size band, not the model.", font=F_NOTE, align=WRAP)
        ws.row_dimensions[r].height = 30
        r += 1

        # top objections
        section("Top three objections per side, as of (mentions across objection_1 to objection_3)")
        # layout: A rank+label, B mentions, C..G quote (merged)
        put(ws, f"A{r}", "Office", font=F_BOLD)
        put(ws, f"B{r}", "Mentions", font=F_BOLD)
        put(ws, f"C{r}", "First quote logged for that code", font=F_BOLD)
        r += 1
        obj_tables = {}
        # count tables live in columns J..M (office) and O..R (brand)
        for side, tab, C, lst, base in (("office", "Office_Log", OL, "office_objection", 10), ("brand", "Brand_Log", BL, "brand_objection", 15)):
            codes = LISTS[lst]
            labels = LISTS[lst + "_label"]
            h0 = 40
            for j, h in enumerate(["code", "label", "mentions", "score"]):
                header(ws, h0, base + j, f"{side} {h}", calc=True, width=[18, 36, 9, 10][j])
            for i, (code, lab) in enumerate(zip(codes, labels)):
                rr = h0 + 1 + i
                a, b_, c, d = (CL(base + k) for k in range(4))
                put(ws, f"{a}{rr}", code, fill=FILL_CALC)
                put(ws, f"{b_}{rr}", lab, fill=FILL_CALC)
                cnt = "+".join(f'COUNTIFS({rng(tab, C, f"calc_obj{k}")},{a}{rr},{rng(tab, C, "call_date")},"<="&$E${cut_row})' for k in (1, 2, 3))
                put(ws, f"{c}{rr}", "=" + cnt, fill=FILL_CALC)
                put(ws, f"{d}{rr}", f"={c}{rr}-{i + 1}/1000", fill=FILL_CALC)
            obj_tables[side] = (h0 + 1, h0 + len(codes), base)
        put(ws, "J39", "Objection counts used for the top three (as of). Ties go to the code listed first.", font=F_NOTE)
        for side, tab, C in (("office", "Office_Log", OL), ("brand", "Brand_Log", BL)):
            r0, r1, base = obj_tables[side]
            a, b_, c, d = (CL(base + k) for k in range(4))
            put(ws, f"A{r}", f"{side.capitalize()} side", font=F_BOLD)
            r += 1
            for k in (1, 2, 3):
                big = f"LARGE(${d}${r0}:${d}${r1},{k})"
                m = f"MATCH({big},${d}${r0}:${d}${r1},0)"
                put(ws, f"A{r}", f'=IF(INDEX(${c}${r0}:${c}${r1},{m})<1,"{k}. none logged yet","{k}. "&INDEX(${b_}${r0}:${b_}${r1},{m})&" ("&INDEX(${a}${r0}:${a}${r1},{m})&")")')
                put(ws, f"B{r}", f'=INDEX(${c}${r0}:${c}${r1},{m})', font=F_BOLD)
                code = f"INDEX(${a}${r0}:${a}${r1},{m})"
                q = lambda kk: f'INDEX({rng(tab, C, "objections_verbatim")},MATCH({code},{rng(tab, C, f"calc_obj{kk}")},0))'
                ws.merge_cells(f"C{r}:G{r}")
                put(ws, f"C{r}", f'=IF(B{r}<1,"",IFERROR({q(1)},IFERROR({q(2)},IFERROR({q(3)},""))))', align=WRAP)
                self.sc[f"top_{side}_{k}"] = r
                r += 1
        # pace
        section("Pace and reply rate (from the Friday Clay paste)")
        for j, h in enumerate(["Measure", "Fri wk 1", "Fri wk 2", "Gate 0", "As of", "", "How it is counted"], start=1):
            if h:
                header(ws, r, j, h)
        r += 1

        def clay_col(side, hname):
            clay = "Clay_Offices" if side == "office" else "Clay_Brands"
            sc = "C" if side == "office" else "D"
            return f"INDEX({clay}!$A$2:${CLAY_LAST_COL}${CLAY_N + 1},0,Sync!${sc}${self.sync_row[hname]})"

        for side in ("office", "brand"):
            ridc, t1, lr, rt, oo = (clay_col(side, h) for h in ("row_id", "touch_1_date", "last_reply_date", "reply_type", "opt_out_date"))
            conv_row = self.sc["o_conv" if side == "office" else "b_conv"]
            rows = [
                ("first", f"{side.capitalize()} first touches sent", lambda c: f'=IFERROR(COUNTIFS({t1},"<="&{c},{ridc},{SC}),0)', "0",
                 "Clay rows with touch_1_date on or before the cut-off."),
                ("replies", f"{side.capitalize()} replies (any human reply, opt-outs included)",
                 lambda c: f'=IFERROR(COUNTIFS({lr},"<="&{c},{ridc},{SC},{rt},"<>bounce",{rt},"<>out_of_office"),0)', "0",
                 "Rows with last_reply_date on or before the cut-off; bounces and auto-replies excluded."),
                ("rate", f"{side.capitalize()} reply rate", None, "0%", "Replies / first touches. The plan needs 20%."),
                ("positive", f"{side.capitalize()} positive replies",
                 lambda c: "=" + "+".join(f'IFERROR(COUNTIFS({lr},"<="&{c},{ridc},{SC},{rt},"{t}"),0)' for t in ("yes", "maybe", "needs_approval", "send_info", "referral")),
                 "0", "reply_type yes, maybe, needs_approval, send_info or referral."),
                ("convrate", f"{side.capitalize()} conversations per first touch", None, "0%", "Conversations (above) / first touches. 15 from about 75 first touches is 20%."),
                ("optout", f"{side.capitalize()} opt-outs", lambda c: f'=IFERROR(COUNTIFS({oo},"<="&{c},{ridc},{SC}),0)', "0",
                 "Rows with opt_out_date on or before the cut-off. Every one must have do_not_contact = Y."),
            ]
            first_r = r
            for key, label, fn, fmt, how in rows:
                put(ws, f"A{r}", label)
                for col_ in "BCDE":
                    c = f"{col_}${cut_row}"
                    if key == "rate":
                        v = f'=IF({col_}{first_r}=0,"",{col_}{first_r + 1}/{col_}{first_r})'
                    elif key == "convrate":
                        v = f'=IF({col_}{first_r}=0,"",{col_}{conv_row}/{col_}{first_r})'
                    else:
                        v = fn(c)
                    put(ws, f"{col_}{r}", v, fmt=fmt, font=F_BOLD)
                put(ws, f"G{r}", how, font=F_NOTE, align=WRAP)
                self.sc[f"{side}_{key}"] = r
                r += 1
            put(ws, f"A{r}", f"{side.capitalize()} reply-rate check (as of)", font=F_BOLD)
            ws.merge_cells(f"B{r}:G{r}")
            fr, rr_ = self.sc[f"{side}_first"], self.sc[f"{side}_rate"]
            put(ws, f"B{r}", (f'=IF(E{fr}<{cfg["min_first_touches_to_judge"]},"Too few first touches to judge ("&E{fr}&" of "&{cfg["min_first_touches_to_judge"]}&").",'
                              f'IF(E{rr_}<{cfg["reply_rate_target"]},"UNDER 20%: run sending/sending-setup.md section 6 before sending more.","OK: at or above 20%."))'),
                font=F_BOLD)
            self.sc[f"{side}_check"] = r
            r += 1
        bounce_o = f'IFERROR(COUNTIFS({clay_col("office", "reply_type")},"bounce",{clay_col("office", "row_id")},{SC}),0)'
        bounce_b = f'IFERROR(COUNTIFS({clay_col("brand", "reply_type")},"bounce",{clay_col("brand", "row_id")},{SC}),0)'
        put(ws, f"A{r}", "Email bounces to date (offices + brands) / first touches to date")
        put(ws, f"E{r}", f"=IF((E{self.sc['office_first']}+E{self.sc['brand_first']})=0,\"\",({bounce_o}+{bounce_b})/(E{self.sc['office_first']}+E{self.sc['brand_first']}))", fmt="0.0%", font=F_BOLD)
        put(ws, f"G{r}", "Stop cold email from the domain and check the list if this passes 2% (sending guide section 6).", font=F_NOTE, align=WRAP)
        self.sc["bounce"] = r
        r += 1

        section("By sequence variant and by channel, as of (pick winners only on large gaps; see sending guide 6.4)")
        for j, h in enumerate(["Sequence or channel", "Side", "First touches", "Replies", "Reply rate", "", "Positive replies"], start=1):
            if h:
                header(ws, r, j, h)
        r += 1
        AS_ = f"$E${cut_row}"
        for name in SEQUENCES + ["CH:email", "CH:linkedin", "CH:warm-intro", "CH:walk-in"]:
            for side in (["office", "brand"] if name.startswith("CH:") else [name.split("-")[0]]):
                ridc, t1, lr, rt, seq, ch = (clay_col(side, h) for h in ("row_id", "touch_1_date", "last_reply_date", "reply_type", "sequence", "channel"))
                if name.startswith("CH:"):
                    crit_col, crit = ch, f'"{name[3:]}"'
                    put(ws, f"A{r}", f"channel: {name[3:]}")
                else:
                    crit_col, crit = seq, f"A{r}"
                    put(ws, f"A{r}", name)
                put(ws, f"B{r}", side)
                put(ws, f"C{r}", f'=IFERROR(COUNTIFS({crit_col},{crit},{t1},"<="&{AS_},{ridc},{SC}),0)', fmt="0")
                put(ws, f"D{r}", f'=IFERROR(COUNTIFS({crit_col},{crit},{lr},"<="&{AS_},{ridc},{SC},{rt},"<>bounce",{rt},"<>out_of_office"),0)', fmt="0")
                put(ws, f"E{r}", f'=IF(C{r}=0,"",D{r}/C{r})', fmt="0%")
                put(ws, f"G{r}", "=" + "+".join(f'IFERROR(COUNTIFS({crit_col},{crit},{lr},"<="&{AS_},{ridc},{SC},{rt},"{t}"),0)'
                                                for t in ("yes", "maybe", "needs_approval", "send_info", "referral")), fmt="0")
                if name == SEQUENCES[0]:
                    self.sc["seq_first"] = r
                r += 1
        put(ws, f"A{r}", "Sequence names come from Clay's sequence column. Edit the names in column A to match the variants Part A's copy uses.", font=F_NOTE)
        r += 1

        section("Data checks (fix every FIX before reading the numbers above)")
        for j, h in enumerate(["Check", "", "", "", "Count", "Result", "What to do"], start=1):
            if h:
                header(ws, r, j, h)
        r += 1
        top = self.sync_top
        so, pb = self.hand_rid["office"], self.hand_rid["brand"]
        checks = [
            ("Office_Log rows with a sync issue", f'=COUNTIF(Office_Log!${OL.L("calc_sync_issue")}$2:${OL.L("calc_sync_issue")}${LOG_N + 1},"?*")', "fix", "Read calc_sync_issue on Office_Log; fix in Clay, then re-paste."),
            ("Brand_Log rows with a sync issue", f'=COUNTIF(Brand_Log!${BL.L("calc_sync_issue")}$2:${BL.L("calc_sync_issue")}${LOG_N + 1},"?*")', "fix", "Read calc_sync_issue on Brand_Log."),
            ("Clay office rows with an issue", f'=COUNTIF(Sync!$G${top}:$G${top + CLAY_N - 1},"?*")', "fix", "Sync tab, office list."),
            ("Clay brand rows with an issue", f'=COUNTIF(Sync!$N${top}:$N${top + CLAY_N - 1},"?*")', "fix", "Sync tab, brand list."),
            ("Handoff rows whose Clay status is not signed / paid", '=COUNTIF(Sync!$R$22:$R$71,"?*")+COUNTIF(Sync!$V$22:$V$71,"?*")', "fix", "Set the Clay status to signed or paid."),
            ("Clay columns missing from a paste", f'=COUNTIF(Sync!$E$5:$E${4 + len(CLAY_NEEDED)},"?*")', "fix", "Export all columns from Clay (CONTRACTS 6.2 names)."),
            ("Days since the Clay offices paste (as of)", f'=IF({cfg["clay_offices_export_date"]}="",999,{cfg["as_of_date"]}-{cfg["clay_offices_export_date"]})', "stale", "Paste a fresh export each Friday and type its date on Config."),
            ("Days since the Clay brands paste (as of)", f'=IF({cfg["clay_brands_export_date"]}="",999,{cfg["as_of_date"]}-{cfg["clay_brands_export_date"]})', "stale", "Same."),
            ("Offices that said Y but owner or window is missing", f'=SUM(Office_Log!${OL.L("calc_yes_incomplete")}$2:${OL.L("calc_yes_incomplete")}${LOG_N + 1})', "info", "They do not count for Gate 0 until both are named."),
            ("Budget probe asked but no verbatim", f'=SUM(Office_Log!${OL.L("calc_probe_missing_text")}$2:${OL.L("calc_probe_missing_text")}${LOG_N + 1})', "fix", "Type the answer word for word."),
            ("Brand number given but no verbatim", f'=SUM(Brand_Log!${BL.L("calc_wtp_missing_text")}$2:${BL.L("calc_wtp_missing_text")}${LOG_N + 1})', "fix", "Type the answer word for word."),
            ("Log rows with a row_id but no real call_date", f'=COUNTIF(Office_Log!${OL.L("calc_sync_issue")}$2:${OL.L("calc_sync_issue")}${LOG_N + 1},"call_date*")+COUNTIF(Brand_Log!${BL.L("calc_sync_issue")}$2:${BL.L("calc_sync_issue")}${LOG_N + 1},"call_date*")', "fix", "Type the date as YYYY-MM-DD."),
            ("Clay touch_1_date cells stored as text", f'=IFERROR(SUMPRODUCT(--ISTEXT({clay_col("office", "touch_1_date")})),0)+IFERROR(SUMPRODUCT(--ISTEXT({clay_col("brand", "touch_1_date")})),0)', "fix", "Reformat the column as a date in Clay or here, or they drop out of every count."),
            ("Pipeline events beyond the export rows", f'=MAX(0,COUNT(Pipeline_Calc!$A$2:$A${self.calc_last})-{EXPORT_N})', "fix", "Raise EXPORT_N in tools/build_tracker.py and rebuild, or split the file."),
            ("Notes over the ten-minute target (as of)", f'=COUNTIF(Office_Log!${OL.L("calc_note_min")}$2:${OL.L("calc_note_min")}${LOG_N + 1},">"&{cfg["note_minutes_target"]})+COUNTIF(Brand_Log!${BL.L("calc_note_min")}$2:${BL.L("calc_note_min")}${LOG_N + 1},">"&{cfg["note_minutes_target"]})', "info", "If this grows, trim the note template, not the verbatims."),
            ("Median minutes per note (as of)", f'=IFERROR(MEDIAN(Office_Log!${OL.L("calc_note_min")}$2:${OL.L("calc_note_min")}${LOG_N + 1},Brand_Log!${BL.L("calc_note_min")}$2:${BL.L("calc_note_min")}${LOG_N + 1}),"none yet")', "info", "Target 10 or less."),
            ("SAMPLE rows in this file", f"={sample_count}", "sample", "Delete them before real use, or keep include_sample = N so they are ignored."),
        ]
        for label, fml, kind, todo in checks:
            put(ws, f"A{r}", label)
            put(ws, f"E{r}", fml, font=F_BOLD)
            if kind == "fix":
                res = f'=IF(N(E{r})=0,"OK","FIX")'
            elif kind == "stale":
                res = f'=IF(N(E{r})<=1,"OK","FIX")'
            elif kind == "sample":
                res = f'=IF(N(E{r})=0,"OK",IF({INC}="Y","SAMPLE","ignored"))'
            else:
                res = '="info"'
            put(ws, f"F{r}", res, font=F_BOLD)
            put(ws, f"G{r}", todo, font=F_NOTE, align=WRAP)
            self.sc["chk_" + label] = r
            r += 1
        self.sc["last"] = r
        # colors
        rng_all = f"B7:F{r}"
        ws.conditional_formatting.add(rng_all, FormulaRule(formula=['B7="PASS"'], fill=FILL_PASS))
        ws.conditional_formatting.add(rng_all, FormulaRule(formula=['B7="OK"'], fill=FILL_PASS))
        ws.conditional_formatting.add(rng_all, FormulaRule(formula=['B7="FAIL"'], fill=FILL_FAIL))
        ws.conditional_formatting.add(rng_all, FormulaRule(formula=['B7="FIX"'], fill=FILL_FAIL))
        ws.conditional_formatting.add(rng_all, FormulaRule(formula=['B7="not yet"'], fill=FILL_WAIT))
        ws.conditional_formatting.add(f"B1:G{r}", FormulaRule(formula=['LEFT(B1,8)="UNDER 20"'], fill=FILL_WARN))
        ws.freeze_panes = "B7"
        ws.sheet_view.zoomScale = 90

    # ------------------------------------------------------------------ start, dictionary, clay columns
    def build_start(self):
        ws = self.ws["Start"]
        ws.column_dimensions["A"].width = 120
        lines = []
        if self.sample:
            lines.append(("SAMPLE COPY: every row in this file is SAMPLE data. Illustrative placeholders, not results. Use conversation-tracker.xlsx for real work.", "sample"))
        lines += [
            (f'={self.cfg["company_name"]}&" · conversation tracker"', "title"),
            ("What this is: the conversation and notes log for discovery and selling, one row per conversation, keyed by the Clay row_id.", ""),
            ("It is not a status store. Status, touches, replies, next actions and do-not-contact live in the Clay tables only (CONTRACTS 6.2).", "bold"),
            ("", ""),
            ("After every call (ten minutes, calls/post-call-note-template.md)", "bold"),
            ("1. Type one row on Office_Log or Brand_Log: verbatims first, then numbers and codes.", ""),
            ("2. Write back to the Clay row: call_date, status (call_done or yes_in_principle), yes_in_principle, call_notes ('see tracker <date>'), next_action, next_action_date.", ""),
            ("3. Set clay_updated = Y and note_minutes.", ""),
            ("", ""),
            ("Every Friday (15 minutes)", "bold"),
            ("1. Export the Clay offices table (all columns) and paste it on Clay_Offices at A1. Same for brands on Clay_Brands. Type both export dates on Config.", ""),
            ("2. Open Scorecard. Fix every FIX under Data checks (the Sync tab and the red calc_sync_issue cells show where).", ""),
            ("3. Read the Gate 0 block, the medians, the top objections and the reply rates. If a reply rate says UNDER 20%, run sending guide section 6.", ""),
            ("4. Download pipeline_log as CSV (File > Download > CSV, this tab only) to desk-drop-outreach/exports/pipeline_log.csv and paste it into the financial model's Pipeline tab.", ""),
            ("5. When an office signs or a brand pays: add the row on signed_offices or paid_brands, download that tab as CSV to desk-drop-outreach/handoff/.", ""),
            ("", ""),
            ("Tabs", "bold"),
            ("Scorecard: the Friday readout against Gate 0.  Office_Log, Brand_Log: one row per conversation.  signed_offices, paid_brands: handoff rows for operations (CONTRACTS 6.4).", ""),
            ("later_events: renewal answers and roster exits.  Clay_Offices, Clay_Brands: the weekly Clay paste.  Sync: disagreements between Clay and this file.", ""),
            ("pipeline_log: generated export for the financial model (exactly its nine columns).  Pipeline_Sort, Pipeline_Calc: helpers, do not edit.", ""),
            ("Config: dates, targets, the company name.  Lists: dropdown values and objection codes.  Dictionary: every column.  Clay_Columns: the 13 columns to add in Clay.", ""),
            ("", ""),
            ("Rules", "bold"),
            ("Business contacts only. No employee names or details, ever. Verbatims are the speaker's own words; write 'paraphrase:' if you could not catch them exactly.", ""),
            ("Grey columns are formulas. Hidden calc columns sit to the right of each log; unhide them only to debug.", ""),
            ("Dates as YYYY-MM-DD. Money as plain numbers. Rows whose row_id starts with SAMPLE are ignored while include_sample = N.", ""),
        ]
        for i, (text, kind) in enumerate(lines, start=1):
            c = put(ws, f"A{i}", text, align=Alignment(wrap_text=True))
            if kind == "title":
                c.font = F_TITLE
            elif kind == "bold":
                c.font = F_BOLD
            elif kind == "sample":
                c.font = F_WHITE_BOLD
                c.fill = FILL_SAMPLE

    def build_dictionary(self):
        ws = self.ws["Dictionary"]
        for j, (h, w) in enumerate([("tab", 16), ("column", 34), ("type", 22), ("meaning", 90), ("maps to", 40)], start=1):
            header(ws, 1, j, h, width=w)
        r = 2
        def add(tab, specs):
            nonlocal r
            for k, kind, w, helptext, maps in specs:
                t = kind if not kind.startswith("list:") else "list: " + ", ".join(str(v) for v in (LISTS.get(kind[5:]) or ["Y", "N", "unsure"]))[:200]
                for j, v in enumerate([tab, k, t, helptext, maps], start=1):
                    ws.cell(row=r, column=j, value=v).alignment = WRAP
                r += 1
        add("Office_Log", OFFICE_COLS)
        add("Brand_Log", BRAND_COLS)
        add("signed_offices", [(k, "text", 0, "From office_intake (CONTRACTS 6.3).", "CONTRACTS 6.3") for k in OFFICE_INTAKE] + SIGNED_EXTRA)
        add("paid_brands", [(k, "text", 0, "From brand_intake (CONTRACTS 6.3).", "CONTRACTS 6.3") for k in BRAND_INTAKE] + PAID_EXTRA)
        add("later_events", LATER_COLS)
        pl = [("date", "date", 0, "Date of the event.", "H section 3"), ("side", "text", 0, "office or brand.", "H section 3"),
              ("org_id", "text", 0, "The Clay row_id, the same for every event of one organization.", "H section 3 (recommended)"),
              ("org_name", "text", 0, "Company or brand name.", "H section 3"),
              ("event", "text", 0, "outreach_sent (one per touch), conversation, yes_in_principle (offices: only with owner and window), signed, paid (one per payment), budget_probe, renewal_answer, opt_out (roster exits only).", "H section 3"),
              ("value_number", "num", 0, "signed: Tuesday headcount. paid: USD received. office budget_probe: USD a month (low end; 0 = no budget). brand budget_probe: USD per campaign. renewal_answer: USD committed if yes.", "H section 3"),
              ("value_text", "text", 0, "Verbatim answer; renewal_answer: yes, maybe or no.", "H section 3"),
              ("controls_budget", "Y/N", 0, "Brand budget_probe and yes rows only.", "H section 3"),
              ("notes", "text", 0, "Brand budget_probe after hearing $1,500: exactly after_1500. Outreach: touch number, sequence, channel.", "H section 3")]
        add("pipeline_log", pl)
        ws.freeze_panes = "A2"

    def build_clay_columns(self):
        ws = self.ws["Clay_Columns"]
        put(ws, "A1", "The 13 conversation-tracking columns to add to BOTH Clay tables (CONTRACTS 6.2). Clay is the only status store; this tracker reads them every Friday.", font=F_BOLD)
        for j, (h, w) in enumerate([("column", 18), ("type", 8), ("allowed values", 60), ("written when", 44), ("rule", 60)], start=1):
            header(ws, 2, j, h, width=w)
        for i, row in enumerate(CLAY_TRACKING, start=3):
            for j, v in enumerate(row, start=1):
                ws.cell(row=i, column=j, value=v).alignment = WRAP
        n = 3 + len(CLAY_TRACKING) + 1
        put(ws, f"A{n}", "Columns A owns that this tracker also reads: row_id, company, status, do_not_contact, channel (CONTRACTS 6.2). Status values: CONTRACTS section 4 only.", font=F_NOTE)

    # ------------------------------------------------------------------ sample fill
    def fill_sample(self):
        import sample_data as S
        def write_rows(tab, cols, rows):
            ws = self.ws[tab]
            for i, row in enumerate(rows, start=2):
                for k, v in row.items():
                    if k not in cols.idx:
                        raise KeyError(f"{tab}: {k}")
                    if v is None or v == "":
                        continue
                    c = ws[f"{cols.L(k)}{i}"]
                    if c.value is not None and str(c.value).startswith("="):
                        raise ValueError(f"{tab}!{c.coordinate} is a formula; sample tried to write {k}")
                    c.value = v
        write_rows("Office_Log", self.C_office, S.OFFICE_LOG)
        write_rows("Brand_Log", self.C_brand, S.BRAND_LOG)
        write_rows("signed_offices", self.signed_cols, S.SIGNED_OFFICES)
        write_rows("paid_brands", self.paid_cols, S.PAID_BRANDS)
        write_rows("later_events", self.later_cols, S.LATER_EVENTS)
        for tab, rows in (("Clay_Offices", S.CLAY_OFFICES), ("Clay_Brands", S.CLAY_BRANDS)):
            ws = self.ws[tab]
            for j, h in enumerate(S.CLAY_HEADERS, start=1):
                ws.cell(row=1, column=j, value=h).font = F_BOLD
            for i, row in enumerate(rows, start=2):
                for j, h in enumerate(S.CLAY_HEADERS, start=1):
                    v = row.get(h, "")
                    if v == "" or v is None:
                        continue
                    c = ws.cell(row=i, column=j, value=v)
                    if isinstance(v, dt.date):
                        c.number_format = DATE_FMT

    def save(self, path):
        self.wb.active = 1 if not self.sample else 0
        self.wb.save(path)


def build(sample, path):
    b = Book(sample)
    b.build_lists()
    b.build_config()
    b.build_log("office")
    b.build_log("brand")
    b.build_clay_paste("office")
    b.build_clay_paste("brand")
    b.build_sync()
    b.build_handoff()
    b.fix_hand_refs()
    b.build_pipeline()
    b.build_scorecard()
    b.build_start()
    b.build_dictionary()
    b.build_clay_columns()
    if sample:
        b.fill_sample()
    b.save(path)
    return b


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    out = a.out or os.path.join(ROOT, "tracking", "conversation-tracker-SAMPLE.xlsx" if a.sample else "conversation-tracker.xlsx")
    b = build(a.sample, out)
    print("wrote", out, "| pipeline calc rows:", b.calc_last - 1)
