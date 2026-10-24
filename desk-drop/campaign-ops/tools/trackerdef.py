"""Definition of every tracker tab: columns, input or formula, validation, help.

One source for tools/build_tracker.py (writes the workbook) and tools/tracker.py (reads it).
Formulas are written once here, by column name, and must work in Google Sheets and in
LibreOffice (the tests recalculate with LibreOffice): no FILTER, SORT, UNIQUE, LET, LAMBDA,
REGEX, XLOOKUP, MAXIFS or array entry. "Latest date" lookups use SUMPRODUCT(MAX(...)).

Column kinds:  I = you type it (white), A = formula (grey, never type over it),
               P = paste or form area (cream).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CATEGORY_KEYS = [c[0] for c in json.load(open(os.path.join(ROOT, "spec", "forms.json")))["categories"]]
ACTIVITIES = ["brand_sales", "office_coordination", "receiving_kitting", "drop_day",
              "checks_pickup", "reporting_debriefs", "admin_invoicing"]
DELIVERY_MODELS = ["founder", "courier", "direct-ship"]
TIERS = ["founding", "standard"]

OFFICE_INTAKE_COLS = ["submitted_at", "form_version", "company", "contact_name", "contact_title", "contact_email",
                      "contact_phone", "office_address", "floor_suite", "tuesday_headcount", "pantry_owner_name",
                      "pantry_owner_title", "pantry_owner_is_contact", "receiving_type", "receiving_window",
                      "coi_required", "survey_channel", "categories_wanted", "vetoes", "notes", "source"]
BRAND_INTAKE_COLS = ["submitted_at", "form_version", "brand_name", "website", "contact_name", "contact_title",
                     "contact_email", "contact_phone", "product_sku", "category", "hq_city", "nyc_retailers",
                     "online_store_url", "can_issue_discount_code", "preferred_timing", "budget_approver_is_contact",
                     "budget_approver_name_title", "q1_sealed_shelf_stable_60d", "q2_labeled_ingredients_allergens",
                     "q3_buy_path_near_cluster", "q4_can_ship_275_in_10bd", "q5_product_liability_insurance",
                     "q6_contact_can_approve_600", "q7_why_now", "excluded_category_confirmed", "notes", "source"]
SIGNED_OFFICES_EXTRA = ["office_id", "clay_row_id", "agreement_signed_date", "agreement_file", "founding_roster_named",
                        "budget_probe_verbatim", "budget_probe_date", "budget_probe_monthly_usd"]
SIGNED_OFFICES_REQUESTED = ["industry", "pantry_owner_phone", "pantry_owner_email", "public_naming_ok",
                            "agreement_version", "building_id"]
PAID_BRANDS_EXTRA = ["brand_id", "clay_row_id", "tier", "price_usd", "offices_count", "payment_terms",
                     "agreement_signed_date", "invoice_id", "invoice_date", "payment_received_date",
                     "coi_received_date", "allergen_sheet_received_date", "logo_received_date", "card_sentences",
                     "allergen_line_verbatim", "retailer_line", "discount_code", "landing_url",
                     "unused_product_election", "office_approvals"]
PAID_BRANDS_REQUESTED = ["campaign_id", "newsletter_option", "brand_privacy_url", "brand_legal_name",
                         "billing_address", "billing_email", "agreement_version", "coi_policy_end_date",
                         "may_contain_verbatim", "allergen_source", "code_site"]

# H's layouts (financial-model/HANDOFF.md section 2), exactly these columns in this order.
H_CAMPAIGN_ACTUALS = ["campaign_id", "drop_id", "drop_date", "delivery_model", "tier", "brand_id", "offices",
                      "units_received", "units_delivered", "units_placed", "units_placed_within_1bd",
                      "units_topped_up", "units_depleted_day5", "survey_responses", "survey_tried_yes", "qr_scans",
                      "code_redemptions_day30", "revenue_usd", "invoice_paid_date", "processing_fee_usd",
                      "report_delivered_date", "brand_would_buy_again", "renewed", "deposit_usd",
                      "deposit_paid_date", "survey_responses_min_office"]
H_DROP_COSTS = ["drop_id", "drop_date", "delivery_model", "offices", "brands", "kit_cost_usd",
                "transport_cost_usd", "other_direct_cost_usd", "notes"]
H_HOURS = ["date", "drop_id", "campaign_id", "activity", "hours", "note"]

MOVEMENTS = ["received", "rejected", "delivered", "topped_up", "collected", "returned_to_brand",
             "given_to_roster_office", "released_to_office", "disposed", "correction"]
BUCKETS = ["reserve", "rejected", "leftover"]
COUNT_TYPES = ["placed", "remaining_day3", "remaining_day5"]
PHOTO_TYPES = ["placement", "later"]
READING_TYPES = ["baseline", "mid", "close", "late"]
INVOICE_TYPES = ["founding_full", "standard_deposit", "standard_balance", "credit_note"]
ISSUE_TYPES = ["late_arrival", "short_shipment", "damaged_or_short_dated", "owner_absent", "declined_at_door",
               "complaint_or_reaction", "brand_asks_employee_data", "building_access", "photo_missing",
               "placement_late", "recall_or_pull", "other"]
OUTCOMES = ["handed_to_owner", "front_desk_agreed", "placed_by_us", "carrier_delivered", "owner_absent_return",
            "declined", "building_refused", "not_delivered"]

N = {  # data rows per tab (formulas are filled this far)
    "drops": 40, "brands": 60, "offices": 100, "campaigns": 100, "approvals": 400, "stops": 300,
    "inventory": 1500, "counts": 1200, "photos": 1200, "scans": 2000, "redemptions": 300, "issues": 300,
    "hours": 3000, "costs": 600, "invoices": 300, "office_form": 300, "brand_form": 300,
    "in_signed_offices": 150, "in_paid_brands": 150, "office_intake": 1000, "brand_intake": 1000,
    "responses_rows": 3000,
}
N["links"] = 2 * N["approvals"]
N["office_intake_founder"] = N["office_form"]
N["brand_intake_founder"] = N["brand_form"]


class Col:
    def __init__(self, name, kind="I", width=14, fmt=None, dv=None, f=None, help=""):
        self.name, self.kind, self.width, self.fmt, self.dv, self.f, self.help = name, kind, width, fmt, dv, f, help


class Tab:
    def __init__(self, name, cols, rows, purpose, header_row=1, color="FFFFFF", group="", freeze="B2"):
        self.name, self.cols, self.rows, self.purpose = name, cols, rows, purpose
        self.header_row, self.color, self.group, self.freeze = header_row, color, group, freeze
        self.index = {c.name: i for i, c in enumerate(cols)}

    def letter(self, name):
        return colletter(self.index[name] + 1)

    def first(self):
        return self.header_row + 1

    def last(self):
        return self.header_row + self.rows


def colletter(n):
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


TABS = {}


def R(tab, col):
    """Absolute bounded range of a column, e.g. inventory!$C$2:$C$1501."""
    t = TABS[tab]
    L = t.letter(col)
    return "%s!$%s$%d:$%s$%d" % (q(tab), L, t.first(), L, t.last())


def q(tab):
    return tab if tab.replace("_", "").isalnum() else "'%s'" % tab


def C(tab, col, row="{r}"):
    """Same-row cell reference inside a tab's own formula."""
    return "$%s%s" % (TABS[tab].letter(col), row)


def X(tab, col):
    """Absolute reference to the first data cell of another tab's column (for INDEX ranges)."""
    return R(tab, col)


# ---------------------------------------------------------------- config and calendar
CONFIG = [
    # key, value (None = filled by the builder), note
    ("company_name", None, "THE ONE PLACE the working name lives. Everything that prints the name reads this cell. Rename = change this cell (and BRAND_NAME in desk-drop-identity/brand.json for the printed pieces)."),
    ("tagline", "Emerging brands. Delivered to your workday.", "TAGLINE, working, may change."),
    ("founder_name", "[FOUNDER NAME]", ""),
    ("founder_phone", "[PHONE]", "Printed on case labels, route sheets and messages."),
    ("founder_email", "[EMAIL]", ""),
    ("postal_address", "[POSTAL ADDRESS]", "Mailing address (CAN-SPAM footer, invoices)."),
    ("receiving_address", "[RECEIVING ADDRESS]", "Where brands ship cases (founder and courier models). A street address that takes parcels; a PO box cannot receive carrier freight."),
    ("short_link_domain", "go.[DOMAIN]", "The short-link domain (links/QR-AND-LINKS.md). Never put the company name in a link's back-half."),
    ("survey_privacy_url", "https://[DOMAIN]/survey-privacy", "The full survey notice, hosted by the website (legal pack file 13, Part C)."),
    ("cluster_name", "Flatiron, NoMad and Union Square", "Printed in report headers."),
    ("time_zone", "America/New_York", "Set the same in File > Settings (Google Sheets) so form timestamps match."),
    ("units_base", 30, "Units per office = base + per_person x Tuesday headcount, rounded to 5, between min and max."),
    ("units_per_person", 0.2, ""),
    ("units_min", 30, "Plan: floor 30."),
    ("units_max", 80, "Plan: ceiling 80."),
    ("units_round", 5, ""),
    ("reserve_share", 0.1, "Brand ships 10% extra as reserve."),
    ("min_shelf_life_days", 60, "Days of shelf life left on the drop day (brand agreement section 2(b))."),
    ("founding_price_usd", 600, "Founding: 5 offices, first three brands only."),
    ("founding_offices", 5, ""),
    ("standard_price_usd", 1500, "Standard: 10 offices."),
    ("standard_offices", 10, ""),
    ("extra_office_usd", 150, "Each office beyond the package."),
    ("founding_lock_per_office_usd", 120, "A founding brand's next two campaigns: 120 per office up to 10 offices, then 150."),
    ("founding_lock_max_offices", 10, ""),
    ("founding_due_bd", 5, "Founding price due within five business days of the invoice, and before shipping."),
    ("deposit_share", 0.5, "Standard: 50% on signing, 50% at placement confirmation (T+1)."),
    ("approvals_explicit_drops", 3, "An office's first three drops need its explicit yes; after that, opt-out with five business days' notice."),
    ("min_responses_per_office", 5, "Office commitment; Gate 2."),
    ("gate2_placed_share", 0.8, "Gate 2: 80% of units placed within one business day."),
    ("newsletter_keep_days", 30, "Consented emails: our copy deleted 30 days after passing on (file 13, D8)."),
    ("answers_keep_months", 12, "Raw survey answers deleted 12 months after the campaign (file 13, D8)."),
    ("report_office_names", "letters", "letters = offices shown as A, B, C in brand reports; names_if_public = name only where public_naming_ok = Y."),
    ("brand_form_version", "brand-gform-1.0", "Founder-side brand form version (1.x asks about 275 units and $600; 2.x about 550 and $1,500)."),
    ("office_form_version", "office-gform-1.0", "Founder-side office form version."),
    ("today_override", "", "Leave empty. A date here replaces TODAY() everywhere (used by the dry runs)."),
    ("invoice_prefix", "INV-", ""),
    ("bank_details", "[BANK NAME] · Account name [ACCOUNT NAME] · Routing [ROUTING NUMBER] · Account [ACCOUNT NUMBER]", "Printed on invoices. Business account only (legal pack file 04)."),
    ("sales_tax_note", "Prices do not include sales tax; if tax applies it is shown on the invoice (accountant to confirm, legal pack file 09).", ""),
]
CFG_ROW = {k: i + 2 for i, (k, v, n) in enumerate(CONFIG)}


def cfg(key):
    return "config!$B$%d" % CFG_ROW[key]


TODAY = "IF(%s<>\"\",%s,TODAY())" % (cfg("today_override"), cfg("today_override"))
HOL = "calendar!$A$2:$A$80"
BL0 = "calendar!$D$2:$D$20"
BL1 = "calendar!$E$2:$E$20"


def wd(d, n):
    return "WORKDAY(%s,%s,%s)" % (d, n, HOL)


def dv_list(values):
    return ("list", '"' + ",".join(values) + '"')


YN = dv_list(["Y", "N"])
DATE = "yyyy-mm-dd"
TIME = "hh:mm"
MONEY = "0.00"


def lookup(tab, keycol, key, valcol, blank='""'):
    return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),%s)' % (R(tab, valcol), key, R(tab, keycol), blank)


def lk(tab, keycol, key, valcol):
    """Lookup that returns "" for empty source cells (INDEX of an empty cell is 0)."""
    v = 'INDEX(%s,MATCH(%s,%s,0))' % (R(tab, valcol), key, R(tab, keycol))
    return 'IFERROR(IF(%s="","",%s),"")' % (v, v)


def hdr_lookup(tab, idcol_name, key, field):
    """Look up a field by header NAME in a paste tab (robust to the producer's column order)."""
    t = TABS[tab]
    area = "%s!$A$2:$BZ$%d" % (q(tab), t.last())
    hdr = "%s!$A$1:$BZ$1" % q(tab)
    v = 'INDEX(%s,MATCH(%s,INDEX(%s,0,MATCH("%s",%s,0)),0),MATCH("%s",%s,0))' % (
        area, key, area, idcol_name, hdr, field, hdr)
    return 'IFERROR(IF(%s="","",%s),"")' % (v, v)


# ---------------------------------------------------------------- tab columns (pass 1: names and kinds)
def _cols(spec):
    out = []
    for s in spec:
        name, kind = s[0], s[1]
        kw = s[2] if len(s) > 2 else {}
        out.append(Col(name, kind, **kw))
    return out


def define():
    TABS.clear()
    d = lambda **k: k
    add = lambda t: TABS.__setitem__(t.name, t)

    add(Tab("drops", _cols([
        ("drop_id", "I", d(help="DRP-### from the financial model's Schedule tab (financial-model/HANDOFF.md section 1). Keep the ID if a drop slips.")),
        ("drop_date", "I", d(fmt=DATE, help="Tuesday or Wednesday, window clear of blackouts. Refused otherwise (date_check). Use tools/opscal.py next to pick one.")),
        ("delivery_model", "I", d(dv=dv_list(DELIVERY_MODELS))),
        ("status", "I", d(dv=dv_list(["planned", "confirmed", "slipped", "done", "cancelled"]))),
        ("receiving_location", "I", d(width=24, help="Where brands ship: the receiving address (founder, courier) or 'direct to offices' (direct-ship).")),
        ("courier_or_van", "I", d(width=18, help="Courier or van booked for this drop (courier model): name and booking reference.")),
        ("backup_person", "I", d(width=16, help="Briefed backup who can run the route from the route sheet and the kit.")),
        ("notes", "I", d(width=24)),
        ("date_check", "A", d(width=30)),
        ("weekday", "A", d(width=8)),
        ("t_minus_10", "A", d(fmt=DATE, help="Hard ship-by and cancel-by (T-10).")),
        ("ship_by_requested", "A", d(fmt=DATE, help="Earlier ship date asked of brands when T-10 to T-5 crosses the December blackout (CONTRACTS section 3).")),
        ("t_minus_5", "A", d(fmt=DATE)), ("t_minus_3", "A", d(fmt=DATE)), ("t_minus_1", "A", d(fmt=DATE)),
        ("t_plus_1", "A", d(fmt=DATE)), ("t_plus_2", "A", d(fmt=DATE)), ("t_plus_4", "A", d(fmt=DATE)),
        ("t_plus_5", "A", d(fmt=DATE)), ("t_plus_7", "A", d(fmt=DATE)), ("t_plus_10", "A", d(fmt=DATE)),
        ("t_plus_14", "A", d(fmt=DATE)), ("t_plus_30_cal", "A", d(fmt=DATE)),
        ("next_step", "A", d(width=34)), ("next_step_date", "A", d(fmt=DATE)),
        ("campaigns", "A", d(width=9)), ("stops", "A", d(width=7)), ("units_allocated", "A", d(width=9)),
        ("revenue_usd", "A", d(fmt=MONEY)), ("kit_cost_usd", "A", d(fmt=MONEY)), ("transport_cost_usd", "A", d(fmt=MONEY)),
        ("other_direct_cost_usd", "A", d(fmt=MONEY)), ("direct_cost_usd", "A", d(fmt=MONEY)), ("cost_per_stop_usd", "A", d(fmt=MONEY)),
        ("hours", "A", d(fmt="0.0")), ("contribution_usd", "A", d(fmt=MONEY)), ("contribution_per_hour_usd", "A", d(fmt=MONEY)),
    ]), N["drops"], "One row per drop (one route on one morning, one to three brands).", color="DDEBF7", group="Plan"))

    add(Tab("brands", _cols([
        ("brand_id", "I", d(help="BR-###, the same ID E uses (paid_brands.csv) and H keys renewals on. One ID per brand for life.")),
        ("intake_key", "I", d(width=22, help="Copy the brand's submitted_at from brand_intake or brand_intake_founder. Everything grey fills from that row.")),
        ("brand_legal_name", "I", d(width=20, help="From the signed agreement (Part 1). Printed on invoices.")),
        ("billing_address", "I", d(width=24)), ("billing_email", "I", d(width=22, help="Business email for invoices.")),
        ("retailer_evidence_grade", "I", d(dv=dv_list(["seen_on_shelf", "store_selector", "brand_claim", "unverified"]), help="Check 3 evidence (CONTRACTS section 4). seen_on_shelf only after you saw it yourself.")),
        ("coi_check_ok", "I", d(dv=YN, help="Legal pack file 11 five-minute check passed for the current certificate.")),
        ("coi_policy_end_date", "I", d(fmt=DATE)),
        ("status", "I", d(dv=dv_list(["qualifying", "qualified", "active", "paused", "declined"]))),
        ("notes", "I", d(width=24)),
        ("brand_name", "A", d(width=18)), ("website", "A", d(width=18)), ("category", "A", d(width=14)),
        ("product_sku", "A", d(width=22)), ("hq_city", "A"), ("contact_name", "A"), ("contact_title", "A"),
        ("contact_email", "A", d(width=20)), ("contact_phone", "A"), ("online_store_url", "A", d(width=18)),
        ("nyc_retailers", "A", d(width=22)), ("can_issue_discount_code", "A"), ("budget_approver_name_title", "A", d(width=18)),
        ("q1_sealed_shelf_stable_60d", "A"), ("q2_labeled_ingredients_allergens", "A"), ("q3_buy_path_near_cluster", "A"),
        ("q4_can_ship_275_in_10bd", "A"), ("q5_product_liability_insurance", "A"), ("q6_contact_can_approve_600", "A"),
        ("q7_why_now", "A", d(width=22)), ("excluded_category_confirmed", "A"),
        ("checks_yes", "A", d(width=8, help="Of the seven checks, how many are a plain yes (q7 counts when written).")),
        ("qualified", "A", d(width=10)), ("campaigns", "A", d(width=8)), ("founding_rank", "A", d(width=8, help="1, 2, 3 = the order founding brands first paid. The founding tier closes after 3.")),
    ]), N["brands"], "Paying customers: one row per brand, with the seven checks.", color="DDEBF7", group="Customers"))

    add(Tab("offices", _cols([
        ("office_id", "I", d(help="O-###, assigned at signing (E's signed_offices.csv). Everything grey fills from in_signed_offices.")),
        ("building_id", "I", d(help="B-B-### from the cluster map (cluster-1-flatiron/buildings.csv), if known.")),
        ("lat", "I", d(fmt="0.000000", help="From python3 _shared/geocode.py \"<address>\" (run from desk-drop/).")),
        ("lon", "I", d(fmt="0.000000")),
        ("industry_override", "I", d(help="Only if E did not send industry.")),
        ("pantry_owner_phone_override", "I", d(help="The pantry owner's business phone, from the agreement's top table, if E did not send it.")),
        ("front_desk_fallback_ok", "I", d(dv=YN, help="Y only if the owner agreed the front desk may take the case when they are out. Otherwise: no unattended food, come back next morning.")),
        ("delivery_point_note", "I", d(width=26, help="Floor, kitchen, which door, who to ask for. What a stranger needs at the door.")),
        ("building_coi_status", "I", d(dv=dv_list(["not_needed", "to_request", "requested", "received", "blocked"]), help="Legal pack file 12: start at least 10 business days before the first drop.")),
        ("building_coi_date", "I", d(fmt=DATE)),
        ("status", "I", d(dv=dv_list(["active", "paused", "left"]))),
        ("left_date", "I", d(fmt=DATE)),
        ("notes", "I", d(width=24)),
        ("company", "A", d(width=20)), ("office_address", "A", d(width=24)), ("floor_suite", "A"),
        ("tuesday_headcount", "A", d(width=9)), ("contact_name", "A"), ("contact_phone", "A"), ("contact_email", "A", d(width=20)),
        ("pantry_owner_name", "A"), ("pantry_owner_title", "A"), ("pantry_owner_is_contact", "A", d(width=7)),
        ("receiving_type", "A"), ("receiving_window", "A"), ("coi_required", "A", d(width=7)),
        ("survey_channel", "A", d(width=8)), ("categories_wanted", "A", d(width=24)), ("vetoes", "A", d(width=20)),
        ("agreement_signed_date", "A", d(fmt=DATE)), ("founding_roster_named", "A", d(width=7)),
        ("public_naming_ok", "A", d(width=7)), ("clay_row_id", "A"),
        ("industry", "A", d(width=14)), ("owner_phone", "A", d(width=14, help="Phone for the route sheet: the pantry owner's, or the contact's when they are the owner.")),
        ("headcount_band", "A", d(width=9)), ("size_check", "A", d(width=22)), ("default_units", "A", d(width=8)),
        ("drops_so_far", "A", d(width=8)), ("declines", "A", d(width=8)),
    ]), N["offices"], "Participating customers: the signed roster.", color="DDEBF7", group="Customers"))

    camp_inputs = [
        ("campaign_id", "I", d(help="CMP-###. One row per brand per drop.")),
        ("drop_id", "I"), ("brand_id", "I"),
        ("tier", "I", d(dv=dv_list(TIERS))),
        ("founding_lock", "I", d(dv=YN, help="Y for a founding brand's second or third campaign at $120 per office.")),
        ("offices_contracted", "I", d(width=9, help="Offices in the agreement (5 founding, 10 standard, plus extra offices).")),
        ("price_override_usd", "I", d(fmt=MONEY, help="Only if the signed price differs from price_expected. Leave empty otherwise.")),
        ("agreement_signed_date", "I", d(fmt=DATE)), ("agreement_version", "I", d(width=8)),
        ("product_sku", "I", d(width=22, help="As on the package, with pack size.")),
        ("card_sentences", "I", d(width=30, help="The brand's two sentences, no claims (desk-drop-identity/templates/tent-card/FIELDS.md).")),
        ("allergen_source", "I", d(dv=dv_list(["contains_statement", "ingredient_list", "single_ingredient"]))),
        ("allergen_line_verbatim", "I", d(width=30, help="Word for word from the package. Checked against the package at receiving.")),
        ("may_contain_verbatim", "I", d(width=22)),
        ("flavor_name", "I"), ("flavor_name_2", "I"), ("allergen_source_2", "I", d(dv=dv_list(["contains_statement", "ingredient_list", "single_ingredient"]))),
        ("allergen_line_verbatim_2", "I", d(width=22)), ("may_contain_verbatim_2", "I", d(width=18)),
        ("retailer_line", "I", d(width=24, help="'Retailer Name, 123 Street Name'. Only stores with evidence.")),
        ("discount_code", "I"), ("code_site", "I", d(help="Short form without https://, for example example.com.")),
        ("landing_url", "I", d(width=22)),
        ("unused_product_election", "I", d(dv=dv_list(["return", "release"]))),
        ("newsletter_option", "I", d(dv=YN, help="Brand agreement Part 1. Y = a newsletter sign-up form is made for this campaign.")),
        ("brand_privacy_url", "I", d(width=20)),
        ("coi_received_date", "I", d(fmt=DATE)), ("allergen_sheet_received_date", "I", d(fmt=DATE)),
        ("logo_received_date", "I", d(fmt=DATE)), ("logo_file", "I", d(width=16)),
        ("card_proof_sent_date", "I", d(fmt=DATE, help="Card text sent to the brand before printing (brand agreement section 1).")),
        ("survey_form_url", "I", d(width=20)),
        ("survey_prefill_template", "I", d(width=30, help="The pre-filled link with the literal text CARDCODE typed into the Card code field (forms/survey-form.md, step 9).")),
        ("newsletter_form_url", "I", d(width=20)),
        ("comment_1", "I", d(width=30, help="Word for word from the response tab. Replace a name with [name removed]; mark a cut with [...].")),
        ("comment_2", "I", d(width=30)), ("comment_3", "I", d(width=30)),
        ("learned", "I", d(width=30, help="Three lines, one per bullet (Alt+Enter between lines).")),
        ("recommendation", "I", d(width=30)),
        ("retailer_velocity", "I", d(width=20, help="Only store-level sales the brand shares, with its source.")),
        ("claims_reviewed", "I", d(dv=YN)), ("claims_review_reason", "I", d(width=18)),
        ("report_delivered_date", "I", d(fmt=DATE)), ("debrief_date", "I", d(fmt=DATE)),
        ("brand_would_buy_again", "I", d(dv=dv_list(["yes", "maybe", "no"]))),
        ("renewed", "I", d(dv=dv_list(["Y", "N", "pending"]))), ("renewal_note", "I", d(width=20)),
        ("newsletter_passed_date", "I", d(fmt=DATE, help="The one day the consented list went to the brand (file 13, D7).")),
        ("newsletter_passed_count", "I", d(width=8, help="How many addresses. Never the addresses themselves.")),
        ("newsletter_unticked_deleted_date", "I", d(fmt=DATE)),
        ("newsletter_deleted_date", "I", d(fmt=DATE, help="Form responses, the form and the sent email deleted (D8).")),
        ("answers_deleted_date", "I", d(fmt=DATE)),
        ("notes", "I", d(width=24)),
    ]
    camp_auto = [
        ("brand_name", 18), ("category", 12), ("drop_date", 11), ("delivery_model", 10), ("price_expected_usd", 10),
        ("price_usd", 10), ("payment_terms", 30), ("cancel_by", 11), ("ship_by_requested", 11),
        ("offices_on_route", 8), ("offices_approved", 8), ("approvals_pending", 8), ("units_allocated", 8), ("reserve_planned", 8),
        ("units_to_ship", 8), ("pre_ship_paid_usd", 9), ("pre_ship_due_usd", 9), ("ship_release", 36),
        ("units_received", 8), ("units_rejected", 8), ("reserve_on_hand", 8), ("leftover_on_hand", 8),
        ("units_delivered", 8), ("units_placed", 8), ("units_placed_within_1bd", 8), ("placed_share_1bd", 8),
        ("units_topped_up", 8), ("units_depleted_day5", 8), ("survey_responses", 8), ("survey_responses_min_office", 8),
        ("offices_under_5", 8), ("survey_tried_yes", 8), ("tried_no_didnt_see", 8), ("tried_no_not_for_me", 8),
        ("tried_no_gone", 8), ("survey_rating_n", 8), ("survey_rating_avg", 8), ("survey_buy_yes", 8),
        ("survey_buy_maybe", 8), ("survey_buy_no", 8), ("comments_total", 8), ("responses_outside_window", 8),
        ("responses_unmatched_code", 8), ("qr_scans", 8), ("post_link_opens", 8), ("code_redemptions_to_date", 8),
        ("code_redemptions_as_of", 11), ("code_redemptions_day30", 8), ("revenue_usd", 10), ("deposit_usd", 10),
        ("deposit_paid_date", 11), ("invoice_paid_date", 11), ("processing_fee_usd", 9), ("direct_cost_usd", 10),
        ("shared_cost_usd", 10), ("hours_direct", 8), ("hours_shared", 8), ("contribution_usd", 10),
        ("contribution_per_hour_usd", 10), ("photo_compliance", 8), ("placement_lag_hours_avg", 8),
        ("report_due", 11), ("debrief_due", 11), ("redemption_check_date", 11), ("gate2_placed", 7),
        ("gate2_responses", 7), ("gate2_report_on_time", 7), ("checks", 40),
    ]
    money = {"price_expected_usd", "price_usd", "pre_ship_paid_usd", "pre_ship_due_usd", "revenue_usd", "deposit_usd",
             "processing_fee_usd", "direct_cost_usd", "shared_cost_usd", "contribution_usd", "contribution_per_hour_usd"}
    dates = {"drop_date", "cancel_by", "ship_by_requested", "code_redemptions_as_of", "deposit_paid_date",
             "invoice_paid_date", "report_due", "debrief_due", "redemption_check_date"}
    pct = {"placed_share_1bd", "photo_compliance"}
    cols = _cols(camp_inputs)
    for name, w in camp_auto:
        fmt = MONEY if name in money else DATE if name in dates else "0%" if name in pct else (
            "0.0" if name in ("survey_rating_avg", "hours_direct", "hours_shared", "placement_lag_hours_avg") else None)
        cols.append(Col(name, "A", width=w, fmt=fmt))
    add(Tab("campaigns", cols, N["campaigns"], "One row per brand campaign: terms, card, survey, report inputs, and every ladder number.", color="DDEBF7", group="Plan"))

    add(Tab("approvals", _cols([
        ("campaign_id", "I"), ("office_id", "I"),
        ("asked_date", "I", d(fmt=DATE, help="The day you emailed the office about this brand.")),
        ("reply", "I", d(dv=dv_list(["yes", "no"]), help="Explicit yes needed for an office's first three drops. After that the brand goes unless they say no (notice at least five business days ahead).")),
        ("reply_date", "I", d(fmt=DATE)), ("reply_note", "I", d(width=20)),
        ("units_override", "I", d(width=8, help="Only to change the headcount-based number.")),
        ("drop_id", "A"), ("drop_date", "A", d(fmt=DATE)), ("brand_name", "A", d(width=16)), ("company", "A", d(width=18)),
        ("office_seq", "A", d(width=6)), ("office_label", "A", d(width=6)), ("office_drop_number", "A", d(width=7)),
        ("approval_mode", "A", d(width=9)), ("approved", "A", d(width=9)), ("fit_check", "A", d(width=24)),
        ("units_allocated", "A", d(width=8)), ("card_code", "A", d(width=24)),
        ("units_delivered", "A", d(width=8)), ("delivered_at", "A", d(fmt="yyyy-mm-dd hh:mm", width=15)),
        ("delivered_count_source", "A", d(width=12)),
        ("placement_photo_file", "A", d(width=24)), ("placement_photo_date", "A", d(fmt=DATE)), ("placed_count", "A", d(width=7)),
        ("units_placed", "A", d(width=7)), ("placed_within_1bd", "A", d(width=7)), ("placement_lag_hours", "A", d(fmt="0.0", width=7)),
        ("units_topped_up", "A", d(width=7)), ("remaining_day3", "A", d(width=7)), ("remaining_day5", "A", d(width=7)),
        ("units_depleted_day5", "A", d(width=7)), ("later_photo_file", "A", d(width=24)), ("later_photo_date", "A", d(fmt=DATE)),
        ("later_photo_day", "A", d(width=6)), ("both_photos", "A", d(width=6)),
        ("survey_responses", "A", d(width=7)), ("tried_yes", "A", d(width=7)), ("qr_scans", "A", d(width=7)),
        ("post_link_opens", "A", d(width=7)), ("checks", "A", d(width=40)),
    ]), N["approvals"], "One row per office per campaign: the office's yes, its units, and its whole ladder.", color="E2EFDA", group="Campaign"))

    add(Tab("stops", _cols([
        ("drop_id", "I"), ("office_id", "I"),
        ("route_order", "I", d(width=6, help="1 = first stop. Walk-up lobbies first, then by receiving window.")),
        ("planned_time", "I", d(fmt=TIME, width=8)),
        ("slack_post_sent_date", "I", d(fmt=DATE, help="T-3: window and pre-written Slack post sent to the owner.")),
        ("confirm_text_sent_date", "I", d(fmt=DATE, help="T-1: confirmation text to the owner.")),
        ("kit_mailed_date", "I", d(fmt=DATE, help="Direct-ship only: tent cards and Slack post mailed ahead.")),
        ("carrier_tracking", "I", d(width=18, help="Direct-ship only: the brand's tracking number for this office.")),
        ("arrival_time", "I", d(fmt=TIME, width=8)), ("departure_time", "I", d(fmt=TIME, width=8)),
        ("handed_to_role", "I", d(dv=dv_list(["pantry owner", "front desk", "other staff", "carrier"]))),
        ("outcome", "I", d(dv=dv_list(OUTCOMES))), ("notes", "I", d(width=24)),
        ("drop_date", "A", d(fmt=DATE)), ("company", "A", d(width=18)), ("office_address", "A", d(width=22)),
        ("floor_suite", "A"), ("receiving_window", "A"), ("receiving_type", "A"), ("pantry_owner_name", "A"),
        ("owner_phone", "A"), ("front_desk_fallback_ok", "A", d(width=7)), ("building_coi_status", "A"),
        ("campaigns_here", "A", d(width=7)), ("units_here", "A", d(width=7)), ("first_drop", "A", d(width=7)),
        ("minutes_on_site", "A", d(width=7)), ("checks", "A", d(width=34)),
    ]), N["stops"], "One row per office per drop: the route.", color="E2EFDA", group="Campaign"))

    add(Tab("inventory", _cols([
        ("date", "I", d(fmt=DATE)), ("time", "I", d(fmt=TIME, width=8)), ("campaign_id", "I"),
        ("office_id", "I", d(help="Blank for stock with you; the office for delivered, topped_up, collected.")),
        ("movement", "I", d(dv=dv_list(MOVEMENTS))),
        ("bucket", "I", d(dv=dv_list(BUCKETS), help="Only for returned_to_brand, disposed and correction: which pile it came from.")),
        ("qty", "I", d(width=6)), ("lot", "I"), ("best_by", "I", d(fmt=DATE)),
        ("count_source", "I", d(dv=dv_list(["founder_count", "courier_count", "office_count", "packing_list"]), help="Who counted. packing_list = nobody counted: it shows in the report as unverified.")),
        ("note", "I", d(width=24)),
        ("drop_date", "A", d(fmt=DATE)), ("reserve_delta", "A", d(width=7)), ("rejected_delta", "A", d(width=7)),
        ("leftover_delta", "A", d(width=7)), ("best_by_ok", "A", d(width=7)), ("checks", "A", d(width=30)),
    ]), N["inventory"], "Every unit that moves: received, rejected, delivered, topped up, collected, returned, given, disposed.", color="E2EFDA", group="Campaign"))

    add(Tab("counts", _cols([
        ("date", "I", d(fmt=DATE)), ("time", "I", d(fmt=TIME, width=8)), ("campaign_id", "I"), ("office_id", "I"),
        ("count_type", "I", d(dv=dv_list(COUNT_TYPES))), ("units", "I", d(width=6)),
        ("source", "I", d(dv=dv_list(["photo", "owner_report", "founder_count"]))),
        ("photo_id", "I"), ("note", "I", d(width=24)),
        ("window_day", "A", d(width=6)), ("checks", "A", d(width=30)),
    ]), N["counts"], "Shelf counts: placed (from the placement photo), remaining on day 3 and day 5.", color="E2EFDA", group="Campaign"))

    add(Tab("photos", _cols([
        ("photo_id", "I", d(help="PH-####.")), ("campaign_id", "I"), ("office_id", "I"),
        ("photo_type", "I", d(dv=dv_list(PHOTO_TYPES))),
        ("taken_date", "I", d(fmt=DATE, help="The day the photo was taken (from the photo, or the message it came in).")),
        ("taken_time", "I", d(fmt=TIME, width=8)),
        ("source", "I", d(dv=dv_list(["founder", "office", "courier"]))),
        ("file_name", "I", d(width=30, help="Saved as <campaign_id>_<office_id>_<placement|later>_<YYYY-MM-DD>.jpg in photos/<campaign_id>/.")),
        ("received_date", "I", d(fmt=DATE)),
        ("card_visible", "I", d(dv=YN)),
        ("no_people_or_screens", "I", d(dv=YN, help="Y only if no person, face, screen or whiteboard can be made out. N = never used.")),
        ("note", "I", d(width=20)),
        ("drop_date", "A", d(fmt=DATE)), ("window_day", "A", d(width=6)), ("usable", "A", d(width=7)),
        ("expected_file_name", "A", d(width=34)), ("checks", "A", d(width=30)),
    ]), N["photos"], "Evidence: one row per photo.", color="E2EFDA", group="Campaign"))

    add(Tab("links", _cols([
        ("campaign_id", "A"), ("office_id", "A"), ("link_type", "A", d(width=6)), ("slug", "A", d(width=20)),
        ("short_url", "A", d(width=30)), ("card_code", "A", d(width=24)), ("destination_url", "A", d(width=60)),
        ("qr_file", "A", d(width=28)), ("checks", "A", d(width=28)),
    ]), N["links"], "Made by formulas, two per office per campaign: qr (printed on the card) and post (the Slack or email post). Never typed.", color="EDEDED", group="Measure"))

    add(Tab("scans", _cols([
        ("read_date", "I", d(fmt=DATE)), ("read_time", "I", d(fmt=TIME, width=8)), ("slug", "I", d(width=20)),
        ("reading_type", "I", d(dv=dv_list(READING_TYPES), help="baseline = after your own test scan at kitting; close = end of day 5 (T+4).")),
        ("clicks_to_date", "I", d(width=8, help="The link tool's total for this link, read from its dashboard. Totals only, never per-click logs.")),
        ("note", "I", d(width=20)),
        ("campaign_id", "A"), ("office_id", "A"), ("link_type", "A", d(width=6)), ("checks", "A", d(width=24)),
    ]), N["scans"], "Link totals read from the short-link tool. Scans = close minus baseline.", color="E2EFDA", group="Measure"))

    add(Tab("redemptions", _cols([
        ("campaign_id", "I"), ("as_of_date", "I", d(fmt=DATE)), ("redemptions_to_date", "I", d(width=8)),
        ("reported_date", "I", d(fmt=DATE)), ("reported_by_role", "I", d(width=16)), ("note", "I", d(width=24)),
        ("days_after_drop", "A", d(width=7)), ("is_day30", "A", d(width=7)),
    ]), N["redemptions"], "Code redemptions as the brand reports them. Purchased, nothing more.", color="E2EFDA", group="Measure"))

    add(Tab("issues", _cols([
        ("issue_id", "I"), ("date", "I", d(fmt=DATE)), ("time", "I", d(fmt=TIME, width=8)), ("drop_id", "I"),
        ("campaign_id", "I"), ("office_id", "I"), ("issue_type", "I", d(dv=dv_list(ISSUE_TYPES))),
        ("what_happened", "I", d(width=34, help="Facts and times. No employee names or health details.")),
        ("action_taken", "I", d(width=30)), ("brand_told_date", "I", d(fmt=DATE)), ("office_told_date", "I", d(fmt=DATE)),
        ("closed_date", "I", d(fmt=DATE)), ("note", "I", d(width=20)),
        ("days_open", "A", d(width=7)), ("checks", "A", d(width=34)),
    ]), N["issues"], "Every deviation, as it happened (plan, 'When things go wrong').", color="FCE4D6", group="Campaign"))

    add(Tab("hours", _cols([
        ("date", "I", d(fmt=DATE)), ("drop_id", "I", d(help="Blank for time not tied to a drop.")), ("campaign_id", "I", d(help="Optional. Fill it for brand-specific work (selling, report, debrief).")),
        ("activity", "I", d(dv=dv_list(ACTIVITIES))), ("hours", "I", d(fmt="0.00", width=7, help="Decimal hours: 1.5, not 1:30.")), ("note", "I", d(width=30)),
        ("checks", "A", d(width=24)),
    ]), N["hours"], "Founder hours by the seven activities. Columns A to F are the financial model's hours_log.csv.", color="FFF2CC", group="Money"))

    add(Tab("costs", _cols([
        ("date", "I", d(fmt=DATE)), ("drop_id", "I"), ("campaign_id", "I", d(help="Blank = shared by the drop's brands (split by offices).")),
        ("cost_type", "I", d(dv=dv_list(["kit", "transport", "other_direct"]))), ("amount_usd", "I", d(fmt=MONEY)),
        ("vendor", "I", d(width=16)), ("receipt_file", "I", d(width=20)), ("note", "I", d(width=24)),
        ("checks", "A", d(width=24)),
    ]), N["costs"], "Direct costs of a drop only. Software, insurance, storage and phone are overhead, paid once in the financial model.", color="FFF2CC", group="Money"))

    add(Tab("invoices", _cols([
        ("invoice_id", "I", d(help="INV-###, in order, never reused.")), ("campaign_id", "I"),
        ("invoice_type", "I", d(dv=dv_list(INVOICE_TYPES))), ("issued_date", "I", d(fmt=DATE)),
        ("amount_usd", "I", d(fmt=MONEY, help="Before tax. A credit note is negative.")), ("sales_tax_usd", "I", d(fmt=MONEY)),
        ("sent_to", "I", d(width=20)), ("paid_date", "I", d(fmt=DATE, help="The day the money is in the business bank account. This releases the ship date.")),
        ("paid_amount_usd", "I", d(fmt=MONEY)), ("method", "I", d(dv=dv_list(["bank_transfer", "card", "check"]))),
        ("bank_reference", "I", d(width=16)), ("processing_fee_usd", "I", d(fmt=MONEY, help="0 for a bank transfer.")),
        ("note", "I", d(width=20)),
        ("brand_name", "A", d(width=16)), ("due_date", "A", d(fmt=DATE)), ("total_usd", "A", d(fmt=MONEY)),
        ("status", "A", d(width=10)), ("releases_ship", "A", d(width=7)), ("checks", "A", d(width=30)),
    ]), N["invoices"], "Invoices by bank transfer. The payment-received date releases the ship date.", color="FFF2CC", group="Money"))

    # Intake: exactly CONTRACTS 6.3, header in row 1 (the website's Apps Script writes here when bound to this file).
    add(Tab("office_intake", _cols([(c, "P") for c in OFFICE_INTAKE_COLS]), N["office_intake"],
            "Website office form rows (CONTRACTS 6.3). Written by the website's script; never edit columns A to U.", color="FFF9E5", group="Intake", freeze="C2"))
    add(Tab("brand_intake", _cols([(c, "P") for c in BRAND_INTAKE_COLS]), N["brand_intake"],
            "Website brand form rows (CONTRACTS 6.3). Written by the website's script; never edit columns A to AA.", color="FFF9E5", group="Intake", freeze="C2"))
    add(Tab("office_intake_founder", _cols([(c, "A") for c in OFFICE_INTAKE_COLS]), N["office_intake_founder"],
            "The founder-side office form's answers in CONTRACTS 6.3 columns (formulas over office_form).", color="EDEDED", group="Intake", freeze="C2"))
    add(Tab("brand_intake_founder", _cols([(c, "A") for c in BRAND_INTAKE_COLS]), N["brand_intake_founder"],
            "The founder-side brand form's answers in CONTRACTS 6.3 columns (formulas over brand_form).", color="EDEDED", group="Intake", freeze="C2"))
    add(Tab("in_signed_offices", _cols([(c, "P") for c in OFFICE_INTAKE_COLS + SIGNED_OFFICES_EXTRA + SIGNED_OFFICES_REQUESTED]),
            N["in_signed_offices"], "Paste E's signed_offices.csv here (File > Import > Replace current sheet). Read by header name.", color="FFF9E5", group="Intake", freeze="C2"))
    add(Tab("in_paid_brands", _cols([(c, "P") for c in BRAND_INTAKE_COLS + PAID_BRANDS_EXTRA + PAID_BRANDS_REQUESTED]),
            N["in_paid_brands"], "Paste E's paid_brands.csv here to check it against the tracker (Dashboard checks).", color="FFF9E5", group="Intake", freeze="C2"))
    return TABS


define()
