#!/usr/bin/env python3
"""Stage 3: merge the researched contacts into both tables, re-score, re-rank, mark which rows are ready for
outreach, group rows that must never be in flight together, and write the final tables, the daily views and
the Clay import files.

Inputs (all inside clay-icp-tables/):
  _work/stage1_offices.csv, _work/stage1_brands.csv   (written by build_offices.py, build_brands.py)
  _work/contacts_o1.csv, _work/contacts_o2.csv        (office contacts, stage 2)
  _work/contacts_r9_offices.csv                       (review round 1: contacts for offices that entered the
                                                       top 110, and backups; optional)
  _work/contacts_b1.csv, _work/contacts_s3_entrants.csv, _work/contacts_r9_brands.csv   (brand contacts)
  _work/stage3_contact_fixes.csv                      (sourced corrections to single contact fields)
  _work/linkedin_company_r9.csv                       (company LinkedIn pages linked from the company's own site)
  live/offices-live.csv, live/brands-live.csv, live/enrichment-live.csv  (the founder's live Sheet, if saved)
Outputs:
  offices.csv, brands.csv, daily-view-offices.csv, daily-view-brands.csv, walk-list-offices.csv,
  founder-review-brands.csv, clay-import/offices-clay-import.csv, clay-import/brands-clay-import.csv,
  _work/enrichment_build.csv (the Enrichment tab's starting rows)

Review round 1 restructured the contact columns: the researched people sit in primary_* and backup_*; the
CONTRACTS 6.2 columns (first_name, last_name, title, contact_linkedin_url, work_email, email_status, channel,
score_reason and the daily-view contact block) are computed from them, from promote_backup (the founder's
one-cell swap after a wrong_person reply), known_to_founder and the Enrichment tab. derive() below is the
Python twin of the workbook formulas; build_xlsx.py writes the same logic as formulas and test_workbook.py
checks the two agree. Nothing here opens the network.
"""
import os
import re
import urllib.parse

import pandas as pd

import common as C
import config as K

TODAY = C.TODAY
STALE_BEFORE = "2025-10-24"  # a contact record older than 12 months gets a check before sending

STABLE = ["row_id", "company", "first_name", "last_name", "title", "contact_linkedin_url", "work_email",
          "email_status", "channel", "score", "score_reason", "onsite_band", "nearest_stocked_retailer",
          "nearest_retailer_grade", "why_now", "why_now_url", "why_now_date", "known_to_founder",
          "startup_cpg_member", "do_not_contact", "status", "source_url", "found_date"]
IN_FLIGHT = ["queued", "contacted", "replied", "call_booked", "call_done", "yes_in_principle", "materials_sent"]
STATUSES = {"office": ["new", "queued", "contacted", "replied", "call_booked", "call_done", "yes_in_principle",
                       "materials_sent", "signed", "not_now", "no", "wrong_person", "do_not_contact"],
            "brand": ["new", "queued", "contacted", "replied", "call_booked", "call_done", "yes_in_principle",
                      "materials_sent", "paid", "not_now", "no", "wrong_person", "do_not_contact"]}
E_TRACKING = ["sequence", "touch_1_date", "touch_2_date", "touch_3_date", "last_reply_date", "reply_type",
              "call_date", "call_notes", "yes_in_principle", "next_action", "next_action_date", "opt_out_date",
              "referral_from"]
E_PERSONAL = {"office": ["street_short", "why_now_hook", "call_note_hook", "how_we_know", "referrer_ok_to_name"],
              "brand": ["why_now_hook", "product_short", "call_note_hook", "how_we_know", "referrer_ok_to_name",
                        "office_approvals_complete"]}

# The daily view's columns after the stable ones (the same names, in this order, on the view tabs and CSVs).
DV_EXTRA = {
    "office": ["side", "daily_view_rank", "rank", "top50", "check_before_send", "contact_role", "contact_status",
               "contact_evidence", "contact_source_url", "contact_source_date", "title_match", "street_address",
               "floor", "lease_status", "onsite_low", "onsite_high", "onsite_confidence", "attendance_signal",
               "company_group", "hold_before_outreach", "hold_reason", "opt_out_date"],
    "brand": ["side", "daily_view_rank", "rank", "top60", "check_before_send", "contact_role", "contact_status",
              "contact_evidence", "contact_source_url", "contact_source_date", "product_example", "category",
              "hq_city", "online_store_url", "founder_review", "founder_review_reason", "company_group",
              "hold_before_outreach", "hold_reason", "opt_out_date"],
}
# Founder controls (yellow) and readiness (formula), right after the view block.
CONTROL = {"office": ["ready_for_outreach", "ready_reason", "founder_ok_to_queue", "promote_backup",
                      "onsite_founder_call"],
           "brand": ["ready_for_outreach", "ready_reason", "promote_backup", "review_blocking",
                     "founder_review_cleared", "retailer_checked_date", "retailer_check_url"]}
PERSON = ["first_name", "last_name", "title", "linkedin_url", "work_email", "email_status", "contact_role",
          "contact_status", "contact_evidence", "contact_source_url", "contact_source_date", "title_match",
          "check_before_send", "reason_who"]


def person_cols(pre, side):
    return [f"{pre}_{c}" for c in PERSON if not (c == "title_match" and side == "brand")]


SWAP = {  # computed column -> (primary input, backup input)
    "first_name": "first_name", "last_name": "last_name", "title": "title", "contact_linkedin_url": "linkedin_url",
    "work_email": "work_email", "email_status": "email_status", "contact_role": "contact_role",
    "contact_status": "contact_status", "contact_evidence": "contact_evidence",
    "contact_source_url": "contact_source_url", "contact_source_date": "contact_source_date",
    "title_match": "title_match", "check_before_send": "check_before_send"}
EXTRAS = ["contact_name_as_found", "contact_record_date", "contact_note", "contact_ny_base", "linkedin_status",
          "backup_contact_name_as_found", "backup_contact_record_date", "backup_contact_note", "backup_contact_ny_base",
          "backup_linkedin_status", "contacts_researched"]
REASON = {"office": ["score_reason_core", "channel_base"],
          "brand": ["score_reason_core", "score_reason_tail", "channel_base"]}
HELPERS = {"office": ["in_flight", "dnc_any", "group_key", "group_blocked", "eligible", "view_pick", "in_daily_view",
                      "view_slot", "walk_ok", "walk_slot", "intact", "row_order"],
           "brand": ["in_flight", "dnc_any", "group_key", "group_blocked", "eligible", "view_pick", "in_daily_view",
                     "view_slot", "review_ok", "review_slot", "intact", "row_order"]}
ENRICH_COLS = ["row_id", "work_email", "email_status", "backup_work_email", "backup_email_status", "note"]
WALK_VIEW = ["row_id", "company", "score", "street_address", "floor", "building_name", "lobby_type", "lobby_note",
             "coi_required", "website", "linkedin_company_url", "check_before_send", "status", "walk_slot"]
REVIEW_VIEW = ["row_id", "company", "score", "founder_review_type", "founder_review_reason", "website",
               "nearest_stocked_retailer", "first_name", "last_name", "title", "status", "review_slot"]
WALK_SIZE = 25
REVIEW_SIZE = 30


def rd(name):
    p = os.path.join(C.WORK, name)
    return pd.read_csv(p, dtype=str, keep_default_na=False) if os.path.exists(p) else None


def domain(u):
    m = re.match(r"https?://(?:www\.)?([^/]+)", (u or "").strip().lower())
    return m.group(1) if m else ""


def same_site(u, website):
    a, b = domain(u), domain(website)
    return bool(a and b and (a == b or a.endswith("." + b) or b.endswith("." + a)))


def evidence_of(url, website, confidence):
    """Where the name comes from, in words a founder can weigh."""
    if confidence.startswith("snippet"):
        return "search snippet only (not opened)"
    u = domain(url)
    if not u:
        return "unknown"
    if "linkedin.com" in u:
        return "LinkedIn (not opened)"
    if "theorg.com" in u:
        return "The Org (crowd-edited org chart)"
    if same_site(url, website):
        return "employer's own site"
    return "press, event or podcast page"


DATE_PATS = [r"updated (\d{4}-\d{2}-\d{2})", r"updatedAt[^\d]{0,4}(\d{4}-\d{2}-\d{2})",
             r"(?:dated|release dated|bio posted|posted) (\d{4}-\d{2}-\d{2})",
             r"(?:Mann Report|Commercial Observer|BevNET|Modern Retail|Snack and Bakery|CNBC|Food Business News|"
             r"Food Industry Executive|S&FWB|Boston Globe) (\d{4}(?:-\d{2}){0,2})",
             r"(?:interview|article|release|profile|post) \((20[0-2]\d)\)",  # round 6: 'interview (2021)'
             r"(?:DNAinfo|Untapped Cities|Modern Farmer|EcoWatch|Grit Daily|Kitchn|Eater|New York Times|Forbes|"
             r"Entrepreneur) \(?(20[0-2]\d)", r"[Ss]ources are (20[0-2]\d)"]  # round 8: 'DNAinfo 2015'


def record_date(note):
    """The source's own date when the note gives one (The Org updatedAt, an article date); else ''."""
    for p in DATE_PATS:
        m = re.search(p, note or "")
        if m:
            return m.group(1)
    return ""


# ------------------------------------------------------------------ office titles
EXACT_TITLE = re.compile(r"office (manager|coordinator|services|operations|administrator|lead)|workplace|facilities|"
                         r"people operations|people ops|executive assistant to (the )?(global )?(ceo|chief executive)|"
                         r"\bea to the ceo\b|head of workplace", re.I)


def office_title_match(title, status, ny_base):
    """exact: one of the five target titles or its direct form (office manager or coordinator, office services,
    workplace, facilities, people operations, EA to the CEO), named on an opened page and placed in New York.
    adjacent: any other named person (people or HR lead, chief of staff, operations lead, office leader),
    a target title whose New York base is not shown, or a name seen only in a snippet. none: nobody named."""
    if status in ("none", ""):
        return "none"
    if status == "unverified":
        return "adjacent"
    if EXACT_TITLE.search(title or "") and ny_base != "unconfirmed":
        return "exact"
    return "adjacent"


def ny_base_of(note):
    m = re.search(r"ny_base=(confirmed|likely|unconfirmed)", note or "")
    if m:
        return m.group(1)
    if re.search(r"location NOT stated|may not sit in New York|not placed in New York|located in (?!New York)", note or "", re.I):
        return "unconfirmed"
    if re.search(r"city not stated|does not state (?:each person's|her|his|their) city|city of this person not stated",
                 note or "", re.I):
        return "likely"  # spot check round 6: a New York firm's page that gives no city is 'likely', not 'confirmed'
    if re.search(r"location New York|New York office|New York City office|NY office|names the NY office|"
                 r"is a New York firm|New York HQ|HQ is|headquartered in New York|lives in the NYC area", note or "", re.I):
        return "confirmed"
    return "likely"  # employer page of a New York-HQ firm that does not state the person's city


FIXES = None


def contact_fix(r):
    """Apply _work/stage3_contact_fixes.csv (spot-check corrections, each with its source) to a contact row."""
    global FIXES
    if FIXES is None:
        FIXES = rd("stage3_contact_fixes.csv")
        if FIXES is None:
            FIXES = pd.DataFrame(columns=["row_id", "contact_rank", "first_name", "field", "new_value"])
    r = dict(r)
    for f in FIXES[(FIXES.row_id == r["row_id"]) & (FIXES.contact_rank == r["contact_rank"])
                   & (FIXES.first_name == r["first_name"])].to_dict("records"):
        r[f["field"]] = f["new_value"]
        r["notes"] = (r.get("notes", "") + f" | Stage 3 fix: {f['reason']}").strip(" |")
        if f["field"] == "source_url":
            r["_live"] = True  # a live page replaced a dated one: the old date no longer applies
    return r


def status_of(conf, last, url, note, website):
    """verified-page: the employer's own page or a dated press, event or podcast page names the person.
    crowd-listed: the only page is a crowd-edited directory (The Org prints 'Unverified' beside the name; review
    round 1, R1-04). first-name-only: an opened page gives the first name only. unverified: a snippet only."""
    if conf.startswith("snippet"):
        return "unverified"
    if "theorg.com" in domain(url):
        # by the source alone: where the employer's own page also shows the person, a sourced fix in
        # stage3_contact_fixes.csv points source_url at that page (spot check round 10: a note that merely
        # mentioned the company's domain had been read as employer confirmation)
        return "crowd-listed"
    if last.lower() == "unknown":
        return "first-name-only"
    return "verified-page"


def person(r, website):
    """One contact row from a contact file -> dict, or None when the slot says 'none found'."""
    r = contact_fix(r)
    fn = (r["first_name"] or "").strip()
    if not fn or fn.lower() == "none found":
        return None
    ln = (r["last_name"] or "").strip() or "unknown"
    conf = r["confidence"] or ""
    url = r["source_url"] if r["source_url"].startswith("http") else ""
    status = status_of(conf, ln, url, r["notes"], website)
    li = r["contact_linkedin_url"] if "linkedin.com/in/" in (r["contact_linkedin_url"] or "") else ""
    how = (r.get("linkedin_how") or "").strip()
    if li and not how:
        how = "listed on an opened page or in search results; LinkedIn itself not opened"
    ev = evidence_of(url or r["source_url"], website, conf)
    return dict(first=fn, last=ln, name=f"{fn} {ln}" if ln != "unknown" else fn, title=r["title"], url=url,
                li=li, li_how=how, status=status, note=r["notes"], rank=r["contact_rank"], conf=conf, evidence=ev,
                rec="" if r.get("_live") else record_date(r["notes"]), src_date=r["source_date"] or TODAY)


def put(o, pre, p, role):
    """Write a person into the primary_ or backup_ block. first/last/title only when an opened page (employer,
    press or a crowd-edited directory) supports the name; a snippet-only name stays in *_name_as_found."""
    ok = p is not None and p["status"] in ("verified-page", "first-name-only", "crowd-listed")
    xp = "" if pre == "primary" else "backup_"
    o[f"{pre}_first_name"] = p["first"] if ok else ""
    o[f"{pre}_last_name"] = p["last"] if ok else ""
    o[f"{pre}_title"] = p["title"] if ok else ""
    o[f"{pre}_linkedin_url"] = p["li"] if p else ""
    o[f"{pre}_contact_role"] = role if p else ""
    o[f"{pre}_contact_status"] = p["status"] if p else "none"
    o[f"{pre}_contact_evidence"] = p["evidence"] if p else ""
    o[f"{pre}_contact_source_url"] = p["url"] if p else ""
    o[f"{pre}_contact_source_date"] = p["src_date"] if p else ""
    o[f"{xp}contact_name_as_found"] = p["name"] if p else ""
    o[f"{xp}contact_record_date"] = p["rec"] if p else ""
    o[f"{xp}contact_note"] = p["note"] if p else ""
    o[f"{xp}linkedin_status"] = p["li_how"] if p and p["li"] else ""
    o[f"{pre}_work_email"] = ""
    o[f"{pre}_email_status"] = "none"


# ------------------------------------------------------------------ groups (never two in flight)
class DSU:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def norm_person(s):
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()


def groups(df, side):
    """Rows that share a named parent, an operator, a normalized company name or a named person are one
    group: the daily view takes at most one row per group and skips a group with anyone in flight."""
    d = DSU()
    why = {}
    keys = {}
    for r in df.itertuples():
        d.find(r.row_id)
        ks = [("name", re.sub(r"[^a-z0-9]", "", r.company.lower()))]
        if side == "office" and r.parent_company not in ("", "unknown"):
            ks.append(("parent", re.sub(r"\s*\(.*\)", "", r.parent_company).strip().lower()))
        for c in ("contact_name_as_found", "backup_contact_name_as_found"):
            nm = norm_person(getattr(r, c))
            if nm and len(nm.split()) >= 2:
                ks.append(("person", nm))
        if side == "brand" and r.row_id in K.BRAND_PARENT_GROUPS:
            ks.append(("parent", K.BRAND_PARENT_GROUPS[r.row_id].lower()))
        for k in ks:
            keys.setdefault(k, []).append(r.row_id)
    for k, ids in keys.items():
        for x in ids[1:]:
            d.union(ids[0], x)
        if len(ids) > 1:
            for x in ids:
                why.setdefault(x, set()).add(f"{k[0]} '{k[1]}' shared with {', '.join(i for i in ids if i != x)}")
    root = {r: d.find(r) for r in df.row_id}
    members = {}
    for r, g in root.items():
        members.setdefault(g, []).append(r)
    label = {}
    for g, ids in members.items():
        # AO-C-030 -> C030, AO-W-003 -> W003, AB-130 -> 130: no two tables or ID series can collide
        lab = ids[0] if len(ids) == 1 else "grp-" + "-".join(sorted(i.split("-", 1)[1].replace("-", "") for i in ids))
        for i in ids:
            label[i] = lab
    return label, {k: "; ".join(sorted(v)) for k, v in why.items()}


# ------------------------------------------------------------------ the formulas, in Python (mirrors the workbook)
def _s(v):
    return "" if v is None else str(v)


def enrich_lookup(enrich):
    """Enrichment tab rows -> {row_id: {field: value}}. Mirrors the INDEX/MATCH formulas: the first row with a
    matching row_id wins; a column that is missing reads as blank."""
    out = {}
    if enrich is None or not len(enrich):
        return out
    for r in enrich.to_dict("records"):
        rid = _s(r.get("row_id")).strip()
        if rid and rid not in out:
            out[rid] = {k: _s(v) for k, v in r.items()}
    return out


def email_status_of(email, raw):
    if email == "":
        return "none"
    return raw if raw in ("verified", "unverified") else "unverified"


def derive(df, side, enrich=None):
    """Compute every formula column from the inputs, exactly as the workbook does."""
    df = df.copy()
    E = enrich_lookup(enrich)
    for pre, ek, sk in (("primary", "work_email", "email_status"), ("backup", "backup_work_email", "backup_email_status")):
        em = [E.get(r, {}).get(ek, "") for r in df.row_id]
        rs = [E.get(r, {}).get(sk, "") for r in df.row_id]
        df[f"{pre}_work_email"] = em
        df[f"{pre}_email_status"] = [email_status_of(a, b) for a, b in zip(em, rs)]
    promo = df.promote_backup == "Y"
    for out, src in SWAP.items():
        if out == "title_match" and side == "brand":
            continue
        df[out] = [_s(b) if p else _s(a) for a, b, p in zip(df[f"primary_{src}"], df[f"backup_{src}"], promo)]
    known = df.known_to_founder == "Y"
    df["channel"] = ["warm-intro" if k else ("email" if es == "verified" else ("linkedin" if fn != "" else _s(cb)))
                     for k, es, fn, cb in zip(known, df.email_status, df.first_name, df.channel_base)]
    who = [_s(b) if p else _s(a) for a, b, p in zip(df.primary_reason_who, df.backup_reason_who, promo)]
    if side == "office":
        df["score_title"] = df.title_match.map(lambda x: K.P_TITLE.get(x, 0))
        df["score_known"] = known.map({True: K.W_KNOWN, False: 0})
        parts = ["score_onsite", "score_size", "score_attendance", "score_address", "score_title", "score_known"]
        tot = sum(pd.to_numeric(df[p], errors="coerce").fillna(0) for p in parts)
        df["score"] = [round(t + 1e-9, 1) if g == "pass" else 0 for t, g in zip(tot, df.gate_result)]
        df["score_raw"] = [round(t + 1e-9, 1) for t in tot]
        df["score_reason"] = [c if g != "pass" else f"{c}; {w}{'; known to the founder (+' + str(K.W_KNOWN) + ')' if k else ''}."
                              for c, g, w, k in zip(df.score_reason_core, df.gate_result, who, known)]
        df["ready_for_outreach"] = ["Y" if (g == "pass" and h != "Y" and fn != "" and (fc != "Y" or ok == "Y")) else "N"
                                    for g, h, fn, fc, ok in zip(df.gate_result, df.hold_before_outreach, df.first_name,
                                                                df.onsite_founder_call, df.founder_ok_to_queue)]
        rr = []
        for g, h, hr, fn, fc, ok, band in zip(df.gate_result, df.hold_before_outreach, df.hold_reason, df.first_name,
                                              df.onsite_founder_call, df.founder_ok_to_queue, df.onsite_band):
            bits = []
            if g != "pass":
                bits.append("gated out")
            if h == "Y":
                bits.append("on hold: " + _s(hr))
            if fn == "":
                bits.append("no contact named on an opened page")
            if fc == "Y" and ok != "Y":
                bits.append(f"Tuesday estimate band {band}: founder's call")
            rr.append("; ".join(bits))
        df["ready_reason"] = rr
    else:
        df["score_known"] = known.map({True: K.B_KNOWN, False: 0})
        parts = ["score_buy", "score_ny", "score_why", "score_rev", "score_fit", "score_contact", "score_known",
                 "score_review"]
        tot = sum(pd.to_numeric(df[p], errors="coerce").fillna(0) for p in parts)
        df["score"] = [int(round(t)) if g == "pass" else 0 for t, g in zip(tot, df.gate_result)]
        df["score_raw"] = [int(round(t)) for t in tot]
        df["score_reason"] = [c if g != "pass" else f"{c}, {w}{_s(t)}{'; known to the founder (+' + str(K.B_KNOWN) + ')' if k else ''}."
                              for c, g, w, t, k in zip(df.score_reason_core, df.gate_result, who, df.score_reason_tail, known)]
        df["ready_for_outreach"] = ["Y" if (g == "pass" and h != "Y" and fn != "" and (rb != "Y" or cl == "Y")) else "N"
                                    for g, h, fn, rb, cl in zip(df.gate_result, df.hold_before_outreach, df.first_name,
                                                                df.review_blocking, df.founder_review_cleared)]
        rr = []
        for g, h, hr, fn, rb, cl in zip(df.gate_result, df.hold_before_outreach, df.hold_reason, df.first_name,
                                        df.review_blocking, df.founder_review_cleared):
            bits = []
            if g != "pass":
                bits.append("gated out")
            if h == "Y":
                bits.append("on hold: " + _s(hr))
            if fn == "":
                bits.append("no contact named on an opened page")
            if rb == "Y" and cl != "Y":
                bits.append("founder review pending (Founder review tab)")
            rr.append("; ".join(bits))
        df["ready_reason"] = rr
    return view(df, side)


def _rank_in(df, mask, n):
    """Rank rows where mask is True by score (desc), then row_order (asc); '' elsewhere or beyond n."""
    sc = pd.to_numeric(df.score, errors="coerce").fillna(0)
    ro = df.row_order.astype(int)
    out = []
    sel = df[mask]
    ssc, sro = sc[mask], ro[mask]
    for i in df.index:
        if not mask[i]:
            out.append("")
            continue
        k = int(((ssc > sc[i]) | ((ssc == sc[i]) & (sro < ro[i]))).sum()) + 1
        out.append(str(k) if k <= n else "")
    return out


def view(df, side):
    df = df.copy()
    df["row_order"] = [str(i + 1) for i in range(len(df))]
    df["in_flight"] = df.status.isin(IN_FLIGHT).map({True: "Y", False: "N"})
    dnc = (df.do_not_contact == "Y") | (df.status == "do_not_contact") | (df.opt_out_date.fillna("") != "")
    df["dnc_any"] = dnc.map({True: "Y", False: "N"})
    df["group_key"] = [g if g != "" else r for g, r in zip(df.company_group, df.row_id)]
    blocked = set(df.loc[(df.in_flight == "Y") | (df.dnc_any == "Y"), "group_key"])
    df["group_blocked"] = df.group_key.isin(blocked).map({True: "Y", False: "N"})
    el = ((df.row_id != "") & (df.status == "new") & (df.do_not_contact == "N") & (df.dnc_any == "N")
          & (df.ready_for_outreach == "Y") & (df.group_blocked == "N"))
    df["eligible"] = el.map({True: "Y", False: "N"})
    sc = pd.to_numeric(df.score, errors="coerce").fillna(0)
    ro = df.row_order.astype(int)
    pick = []
    for i in df.index:
        if df.at[i, "eligible"] != "Y":
            pick.append("N")
            continue
        g = (df.group_key == df.at[i, "group_key"]) & (df.eligible == "Y")
        better = g & ((sc > sc[i]) | ((sc == sc[i]) & (ro < ro[i])))
        pick.append("N" if better.any() else "Y")
    df["view_pick"] = pick
    vp = df.view_pick == "Y"
    df["daily_view_rank"] = _rank_in(df, vp, 10 ** 6)
    df["in_daily_view"] = ["Y" if (e == "Y" and p == "Y" and k != "" and int(k) <= K.DAILY_VIEW_SIZE) else "N"
                           for e, p, k in zip(df.eligible, df.view_pick, df.daily_view_rank)]
    df["view_slot"] = [k if v == "Y" else "" for k, v in zip(df.daily_view_rank, df.in_daily_view)]
    if side == "office":
        m = ((df.channel == "walk-in") & (df.gate_result == "pass") & (df.status == "new") & (df.dnc_any == "N")
             & (df.group_blocked == "N") & (df.hold_before_outreach != "Y"))
        df["walk_ok"] = m.map({True: "Y", False: "N"})
        df["walk_slot"] = _rank_in(df, m, WALK_SIZE)
    else:
        m = ((df.gate_result == "pass") & (df.review_blocking == "Y") & (df.founder_review_cleared != "Y")
             & (df.status == "new") & (df.dnc_any == "N"))
        df["review_ok"] = m.map({True: "Y", False: "N"})
        df["review_slot"] = _rank_in(df, m, REVIEW_SIZE)
    df["intact"] = "Y"  # in the workbook: N when a paste has replaced this row's formulas
    return df


def rerank(df, keys, asc, topcol, n):
    df = df.sort_values(keys, ascending=asc).reset_index(drop=True)
    ranks, k = [], 0
    for ok in df.gate_result == "pass":
        if ok:
            k += 1
            ranks.append(str(k))
        else:
            ranks.append("")
    df["rank"] = ranks
    df[topcol] = ["Y" if (x != "" and int(x) <= n) else "N" for x in ranks]
    df["row_order"] = [str(i + 1) for i in range(len(df))]
    return df


EV_RANK = {"verified-page": 0, "first-name-only": 1, "crowd-listed": 2, "unverified": 3, "none": 4}


# ------------------------------------------------------------------ offices
def office_contacts():
    """Stage-2 files, then review round 1's file; per (row, slot) the last named person wins, and a later
    'none found' never erases an earlier name."""
    fr = [rd("contacts_o1.csv"), rd("contacts_o2.csv"), rd("contacts_r9_offices.csv")]
    cts = pd.concat([f for f in fr if f is not None], ignore_index=True).fillna("")
    keep = {}
    for i, r in cts.iterrows():
        k = (r.row_id, r.contact_rank)
        named = r.first_name.strip() and r.first_name.strip().lower() != "none found"
        if k not in keep or named:
            keep[k] = i
    return cts.loc[sorted(keep.values())]


def offices():
    df = rd("stage1_offices.csv")
    cts = office_contacts()
    web = dict(zip(df.row_id, df.website))
    researched = set(cts.row_id)
    lk = rd("linkedin_company_r9.csv")
    lk = {} if lk is None else {r["row_id"]: r for r in lk.to_dict("records") if r["linkedin_company_url"]}
    # second source: the LinkedIn page The Org's company record lists (opened 2026-10-24 for the contact research)
    tor = rd("r9_theorg_candidates.csv")
    if tor is not None:
        for r in tor.to_dict("records"):
            if r["company_linkedin"] and r["org"] and r["row_id"] not in lk:
                u = r["company_linkedin"].replace("http://", "https://").rstrip("/")
                if not u.startswith("https://www."):
                    u = u.replace("https://", "https://www.")
                lk[r["row_id"]] = dict(linkedin_company_url=u, opened="2026-10-24",
                                       source_url=f"https://theorg.com/org/{r['org']}", via="The Org's company record")
    rows = []
    for o in df.to_dict("records"):
        o["side"] = "office"
        o["contacts_researched"] = "Y" if o["row_id"] in researched else "N"
        prim = back = None
        if o["row_id"] in researched:
            for r in cts[cts.row_id == o["row_id"]].to_dict("records"):
                p = person(r, web[o["row_id"]])
                if p is None:
                    continue
                p["ny_base"] = ny_base_of(r["notes"])
                if re.search(r"\b(NY|New York|NYC|Flatiron|Manhattan)\b", p["title"] or ""):
                    p["ny_base"] = "confirmed"  # spot check round 7: the title itself names the New York office
                if r["contact_rank"] == "primary":
                    prim = p
                else:
                    back = p
            # an employer-page backup outranks a weaker primary (snippet only, or crowd-listed)
            if prim is not None and back is not None and EV_RANK[back["status"]] < EV_RANK[prim["status"]] \
                    and not (prim["status"] == "crowd-listed" and EXACT_TITLE.search(prim["title"] or "")
                             and not EXACT_TITLE.search(back["title"] or "")):
                prim, back = back, prim
            if prim is None and back is not None:
                prim, back = back, None
        put(o, "primary", prim, "pantry or office lead (primary)" if prim else "")
        put(o, "backup", back, "pantry or office lead (backup)" if back else "")
        o["contact_ny_base"] = prim["ny_base"] if prim else ""
        o["backup_contact_ny_base"] = back["ny_base"] if back else ""
        for pre, p in (("primary", prim), ("backup", back)):
            o[f"{pre}_title_match"] = office_title_match(p["title"] if p else "", p["status"] if p else "none",
                                                         p["ny_base"] if p else "")
        o["score_title"] = K.P_TITLE[o["primary_title_match"]]
        o["score_known"] = K.W_KNOWN if o["known_to_founder"] == "Y" else 0
        parts = [float(o[c]) for c in ("score_onsite", "score_size", "score_attendance", "score_address")]
        total = round(sum(parts) + o["score_title"] + o["score_known"], 1)
        o["score_raw"] = total
        o["score"] = total if o["gate_result"] == "pass" else 0
        o["_ev"] = EV_RANK[o["primary_contact_status"]]
        if o["row_id"] in lk and o.get("linkedin_company_url", "unknown") in ("", "unknown"):
            o["linkedin_company_url"] = lk[o["row_id"]]["linkedin_company_url"]
            via = lk[o["row_id"]].get("via") or "the company's own site"
            o["linkedin_company_source"] = (f"linked from {via} ({lk[o['row_id']]['source_url']}, "
                                            f"opened {lk[o['row_id']]['opened']}); LinkedIn not opened")
        else:
            o["linkedin_company_source"] = "" if o.get("linkedin_company_url", "") in ("", "unknown") else "B's file"
        rows.append(o)
    df = pd.DataFrame(rows)
    df["_conf"] = df.confidence.map({"high": 0, "medium": 1, "low": 2}).fillna(3)
    df["_fit"] = pd.to_numeric(df.onsite_fit_share, errors="coerce").fillna(-1)
    # ties: employer-page contacts before crowd-listed ones (R1-04), then the estimate's fit, confidence, name
    df = rerank(df, ["gate_result", "score", "_ev", "_fit", "_conf", "company"],
                [False, False, True, False, True, True], "top50", 50)
    df = df.drop(columns=["_conf", "_fit", "_ev"])
    lab, why = groups(df, "office")
    df["company_group"] = df.row_id.map(lab)
    df["company_group_reason"] = df.row_id.map(lambda x: why.get(x, ""))
    out = []
    for o in df.to_dict("records"):
        o["score_reason_core"] = office_core(o)
        for pre in ("primary", "backup"):
            o[f"{pre}_reason_who"] = office_who(o, pre)
            o[f"{pre}_check_before_send"] = office_check(o, pre)
        o["channel_base"] = "walk-in" if (o["top50"] == "Y" and o["primary_first_name"] == "") else "linkedin"
        o["onsite_founder_call"] = "Y" if o["onsite_band"] in ("under-40", "251-500", "over-500") else "N"
        o["founder_ok_to_queue"] = ""
        o["promote_backup"] = ""
        for c in E_TRACKING + E_PERSONAL["office"]:
            o[c] = ""
        out.append(o)
    df = pd.DataFrame(out)
    df, nl = apply_live(df, "office")
    if nl:
        print(f"offices: carried {nl} rows from the live table")
    return df


def office_core(o):
    base = o["score_reason"]
    if o["gate_result"] != "pass":
        return base
    return re.sub(r"; no contact found yet\.$", "", base).rstrip(".")


def _clean(s):
    return re.sub(r"\.\s", " ", s or "").strip()


def office_who(o, pre):
    tm, fn, title = o[f"{pre}_title_match"], o[f"{pre}_first_name"], _clean(o[f"{pre}_title"])
    crowd = " (crowd-listed on The Org)" if o[f"{pre}_contact_status"] == "crowd-listed" else ""
    if tm == "exact":
        return f"contact in the target titles named ({title}){crowd}"
    if tm == "adjacent":
        return f"adjacent contact named ({title}){crowd}" if fn else "contact seen only in a search snippet"
    if pre == "backup":
        return "no backup contact named"
    if o["contacts_researched"] == "Y":
        return "no contact found in public sources (walk-in)"
    return "contacts not researched yet"


def li_step(o, pre, company):
    """The one LinkedIn step left at send time (agents never open LinkedIn)."""
    fn, ln = o[f"{pre}_first_name"], o[f"{pre}_last_name"]
    nm = f"{fn} {ln}" if ln not in ("", "unknown") else fn
    title = o[f"{pre}_title"]
    if o[f"{pre}_linkedin_url"]:
        return (f"open the LinkedIn URL and confirm it is {nm}, {title} at {company} (found on another page, "
                f"never opened)")
    step = f"find {nm} at {company} on LinkedIn and paste the profile URL into {pre}_linkedin_url"
    if o[f"{pre}_contact_status"] == "crowd-listed":
        step += " (this also confirms the name: The Org is crowd-edited and marks it Unverified)"
    return step


def office_check(o, pre):
    if o["gate_result"] != "pass":
        return ""
    xp = "" if pre == "primary" else "backup_"
    bits = []
    fn = o[f"{pre}_first_name"]
    if fn:
        bits.append(li_step(o, pre, o["company"]))
        rec = o.get(f"{xp}contact_record_date", "")
        if rec and rec < STALE_BEFORE:
            bits.append(f"the source is dated {rec}: check {fn} still holds the role")
        if o.get(f"{xp}contact_ny_base") == "unconfirmed":
            bits.append(f"check {fn} works from the New York office")
        if o[f"{pre}_title_match"] == "adjacent":
            bits.append("adjacent title: ask who runs the pantry")
    elif pre == "primary" and o["top50"] == "Y":
        bits.append("no named contact: on the Walk list tab (ask for whoever runs the pantry), or use the company "
                    "contact form")
    elif pre == "backup":
        bits.append("no backup named: back to research")
    if o["onsite_band"] in ("under-40", "251-500", "over-500"):
        bits.append(f"Tuesday estimate band {o['onsite_band']}: founder's call (set founder_ok_to_queue = Y to queue)")
    return "; ".join(bits)


# ------------------------------------------------------------------ brands
def brand_contacts():
    fr = [rd("contacts_b1.csv"), rd("contacts_s3_entrants.csv"), rd("contacts_r9_brands.csv")]
    tags = ["stage 2", "stage 3", "review round 1"]
    parts = []
    for f, t in zip(fr, tags):
        if f is not None and len(f):
            f = f.copy()
            f["_tag"] = t
            parts.append(f)
    cts = pd.concat(parts, ignore_index=True).fillna("")
    keep = {}
    for i, r in cts.iterrows():
        k = (r.row_id, r.contact_rank)
        named = r.first_name.strip() and r.first_name.strip().lower() != "none found"
        if k not in keep or named:
            keep[k] = i
    return cts.loc[sorted(keep.values())]


def stage1_person(o, pre):
    """A stage-1 contact (researcher's sheet) in the shape person() returns."""
    sp = "" if pre == "primary" else "backup_"
    name = o.get(f"{sp}contact_name_as_found", "")
    if not name:
        return None
    url = o.get(f"{sp}contact_profile_url", "")
    st = o.get(f"{sp}contact_status", "none")
    if st in ("verified-page", "first-name-only") and "theorg.com" in domain(url):
        st = "crowd-listed"
    first = o.get(f"{sp}first_name", "")
    li_col = "contact_linkedin_url" if pre == "primary" else "backup_linkedin_url"
    ev = ("LinkedIn (not opened)" if "linkedin" in url else
          evidence_of(url, o["website"], "unverified" if st == "unverified" else "opened"))
    return dict(first=first, last=o.get(f"{sp}last_name", ""), name=name, title=o.get(f"{sp}title", ""), url=url,
                li=o.get(li_col, ""), li_how=o.get(f"{sp}linkedin_status", ""), status=st,
                note=o.get(f"{sp}contact_note", ""), evidence=ev, rec="",
                src_date=o["found_date"], role=o.get(f"{sp}contact_role", ""))


def brands():
    df = rd("stage1_brands.csv")
    cts = brand_contacts()
    web = dict(zip(df.row_id, df.website))
    researched = dict(zip(cts.row_id, cts._tag))
    rows = []
    for o in df.to_dict("records"):
        o["side"] = "brand"
        o["contacts_researched"] = researched.get(o["row_id"], "stage 1 only")
        if o["row_id"] in researched:
            sub = cts[cts.row_id == o["row_id"]].to_dict("records")
            fr = [person(r, web[o["row_id"]]) for r in sub if r["contact_rank"] == "founder"]
            mk = [person(r, web[o["row_id"]]) for r in sub if r["contact_rank"] == "marketing"]
            bk = [person(r, web[o["row_id"]]) for r in sub if r["contact_rank"] == "backup"]
            f = fr[0] if fr else None
            m = mk[0] if mk else None
            bk = [b for b in bk if b is not None]
            good = ("verified-page", "first-name-only", "crowd-listed")
            frole = "founder"
            if f is not None and not re.search(r"found|owner", f["title"] or "", re.I):
                frole = "CEO or owner (not shown as a founder)"  # spot check round 6: Firehook's CEO
            if f is not None and f["status"] in good:
                prim, prole = f, frole
            elif m is not None and m["status"] in ("verified-page", "crowd-listed"):
                prim, prole = m, "marketing lead"
            elif any(b["status"] in ("verified-page", "crowd-listed") for b in bk):
                prim = sorted([b for b in bk if b["status"] in ("verified-page", "crowd-listed")],
                              key=lambda b: EV_RANK[b["status"]])[0]
                prole = "co-founder or executive"
            else:
                prim, prole = f, frole
            rest = [(f, frole), (m, "marketing lead")] + [(b, "co-founder or executive") for b in bk]
            rest = [(p, r) for p, r in rest if p is not None and p is not prim]
            # backup: the marketing lead, else the best remaining person (opened page first)
            rest.sort(key=lambda x: (0 if x[1] == "marketing lead" else 1, EV_RANK[x[0]["status"]]))
            back, brole = (rest[0] if rest else (None, ""))
            put(o, "primary", prim, prole)
            put(o, "backup", back, brole)
            fpts = 0 if f is None else (K.B_CONTACT["founder_full"] if f["status"] in ("verified-page", "crowd-listed")
                                        else K.B_CONTACT["founder_partial"])
            mpts = 0 if m is None else (K.B_CONTACT["marketing"] if m["status"] in ("verified-page", "crowd-listed")
                                        else K.B_CONTACT["marketing_snippet"])
            o["score_contact"] = min(10, fpts + mpts)
        else:
            p1, p2 = stage1_person(o, "primary"), stage1_person(o, "backup")
            put(o, "primary", p1, p1["role"] if p1 else "")
            put(o, "backup", p2, p2["role"] if p2 else "")
            o["score_contact"] = int(float(o["score_contact"]))
        for c in ("contact_profile_url", "backup_contact_profile_url"):
            o.pop(c, None)
        m_u = re.match(r"^(https?://\S+)\s+(.+)$", o.get("online_store_url", "") or "")
        o["online_store_note"] = ""
        if m_u:  # spot check round 6: a note had been written into the URL column
            o["online_store_url"], o["online_store_note"] = m_u.group(1), m_u.group(2).strip("() ")
        if o["company"] == "Sweet Loren's":
            o["revenue_band_type"] = "press headline: a 2025 projection (CNBC, 2025-02-18), not actuals"
        o["score_known"] = K.B_KNOWN if o["known_to_founder"] == "Y" else 0
        total = sum(int(float(o[c])) for c in ("score_buy", "score_ny", "score_why", "score_rev", "score_fit",
                                                "score_contact", "score_known", "score_review"))
        o["score_raw"] = total
        o["score"] = total if o["gate_result"] == "pass" else 0
        o["_ev"] = EV_RANK[o["primary_contact_status"]]
        rows.append(o)
    df = pd.DataFrame(rows)
    df["_g"] = df.nearest_retailer_grade.map({"store_selector": 0, "brand_claim": 1}).fillna(2)
    df["_why"] = pd.to_numeric(df.score_why, errors="coerce").fillna(0)
    df = rerank(df, ["gate_result", "score", "_ev", "_g", "_why", "company"],
                [False, False, True, True, False, True], "top60", 60)
    df = df.drop(columns=["_g", "_why", "_ev"])
    lab, why = groups(df, "brand")
    df["company_group"] = df.row_id.map(lab)
    df["company_group_reason"] = df.row_id.map(lambda x: why.get(x, ""))
    out = []
    for o in df.to_dict("records"):
        o["score_reason_core"], o["score_reason_tail"] = brand_core(o)
        for pre in ("primary", "backup"):
            o[f"{pre}_reason_who"] = brand_who(o, pre)
            o[f"{pre}_check_before_send"] = brand_check(o, pre)
        o["channel_base"] = ""
        o["promote_backup"] = ""
        o["founder_review_cleared"] = ""
        o["retailer_checked_date"] = ""
        o["retailer_check_url"] = retailer_check_url(o)
        o["hold_before_outreach"] = "N"
        o["hold_reason"] = ""
        for c in E_TRACKING + E_PERSONAL["brand"]:
            o[c] = ""
        out.append(o)
    df = pd.DataFrame(out)
    df, nl = apply_live(df, "brand")
    if nl:
        print(f"brands: carried {nl} rows from the live table")
    return df


def brand_core(o):
    """The stage-1 reason, split around its contact clause: (core, tail)."""
    s = o["score_reason"]
    if o["gate_result"] != "pass":
        return s, ""
    s = s.rstrip(".")
    m = re.search(r", (contact named|contact unverified|no contact named)(?=[;]|$)", s)
    if not m:
        return s, ""
    return s[:m.start()], s[m.end():]


def brand_who(o, pre):
    st = o[f"{pre}_contact_status"]
    if pre == "backup" and st == "none":
        return "no backup contact named"
    who = {"verified-page": "contact named", "first-name-only": "contact named (first name only)",
           "crowd-listed": "contact named (crowd-listed on The Org)",
           "unverified": "contact seen only in a snippet", "none": "no contact named"}[st]
    role = o[f"{pre}_contact_role"]
    if role == "marketing lead" and pre == "primary":
        who = who.replace("contact named", "marketing lead named (founder not confirmed)")
    other = "backup" if pre == "primary" else "primary"
    if (o[f"{other}_contact_role"] == "marketing lead" and role != "marketing lead"
            and o[f"{other}_contact_status"] in ("verified-page", "first-name-only", "crowd-listed")):
        who += " plus a marketing lead"
    return who


STORE_IDS = {"Whole Foods Market Union Square": "10162", "Whole Foods Market NoMad": "10773",
             "Whole Foods Market Chelsea": "10131", "Whole Foods Market Manhattan West": "10713"}


def retailer_check_url(o):
    """One click: the retailer's own store-scoped catalog answer for the nearest store (R1-09)."""
    if o["nearest_retailer_grade"] != "store_selector":
        return ""
    st = o["nearest_stocked_retailer"]
    sid = next((v for k, v in STORE_IDS.items() if st.startswith(k)), None)
    if not sid:
        return ""
    for u in re.split(r";\s*", o.get("retailer_evidence_urls", "") or ""):
        if "wholefoodsmarket.com/api/search" in u and f"store={sid}" in u:
            return u.split(" ")[0]
    q = urllib.parse.quote(re.sub(r"\s*\(.*\)", "", o["company"]).lower())
    return f"https://www.wholefoodsmarket.com/api/search?text={q}&store={sid}&limit=60&offset=0"


def brand_check(o, pre):
    if o["gate_result"] != "pass":
        return ""
    bits = []
    fn = o[f"{pre}_first_name"]
    xp = "" if pre == "primary" else "backup_"
    if fn:
        bits.append(li_step(o, pre, re.sub(r"\s*\(.*\)", "", o["company"])))
        rec = o.get(f"{xp}contact_record_date", "")
        if rec and rec < STALE_BEFORE:
            bits.append(f"the source is dated {rec}: check {fn} still holds the role")
        if o[f"{pre}_last_name"] == "unknown":
            bits.append("surname not public: take it from LinkedIn")
    else:
        bits.append("no person named on an opened page: not ready" if pre == "primary"
                    else "no backup named: back to research")
    if o["nearest_retailer_grade"] == "store_selector":
        st = o["nearest_stocked_retailer"].split(",")[0]
        bits.append(f"use the {st} line only if retailer_checked_date is this week's Friday check")
    elif o["nearest_retailer_grade"] == "brand_claim":
        bits.append("the retailer line rests on the brand's own store locator: say 'your store locator lists ...'")
    return "; ".join(bits)


# ------------------------------------------------------------------ live carry-over
LIVE_DIR = os.environ.get("A_LIVE_DIR", os.path.join(C.A_DIR, "live"))
CARRY_ALWAYS = ["status", "do_not_contact", "opt_out_date", "known_to_founder", "founder_ok_to_queue",
                "hold_before_outreach", "promote_backup", "primary_linkedin_url", "backup_linkedin_url",
                "founder_review_cleared", "retailer_checked_date", "company_group"]
PERSON_IN = ["first_name", "last_name", "title", "contact_role", "contact_status", "contact_evidence",
             "contact_source_url", "contact_source_date", "title_match", "check_before_send", "reason_who"]


def apply_live(df, side):
    """Carry what the founder and the outreach engine wrote in the live Sheet (saved as CSV in
    clay-icp-tables/live/<offices|brands>-live.csv) into a rebuild, so a rebuild never resets status.
    do_not_contact = Y and a filled opt_out_date are never undone; status do_not_contact is never undone.
    A primary or backup the founder typed differently is kept. Rows only in the live table (referrals) are
    appended as they are."""
    name = "offices" if side == "office" else "brands"
    p = os.path.join(LIVE_DIR, f"{name}-live.csv")
    if not os.path.exists(p):
        return df, 0
    live = pd.read_csv(p, dtype=str, keep_default_na=False)
    live = live[live.row_id != ""].drop_duplicates("row_id", keep="last").set_index("row_id")
    cols = [c for c in CARRY_ALWAYS + E_TRACKING + E_PERSONAL[side] if c in live.columns and c in df.columns]
    n = 0
    for i, r in df.iterrows():
        rid = r.row_id
        if rid not in live.index:
            continue
        lv = live.loc[rid]
        for c in cols:
            if c == "company_group" and lv[c] == "":
                continue
            df.at[i, c] = lv[c]
        if lv.get("do_not_contact", "") == "Y" or r["do_not_contact"] == "Y":
            df.at[i, "do_not_contact"] = "Y"
        if lv.get("status", "") == "do_not_contact":
            df.at[i, "do_not_contact"] = "Y"
        for pre in ("primary", "backup"):
            k1, k2 = f"{pre}_first_name", f"{pre}_last_name"
            if k1 in live.columns and (lv[k1], lv.get(k2, "")) != (r[k1], r[k2]):
                for c in PERSON_IN:
                    cc = f"{pre}_{c}"
                    if cc in live.columns and cc in df.columns:
                        df.at[i, cc] = lv[cc]
        n += 1
    extra = live[~live.index.isin(df.row_id)].reset_index()
    if len(extra):
        extra = extra[[c for c in extra.columns if c in df.columns]]
        df = pd.concat([df, extra], ignore_index=True).fillna("")
    # opted out anywhere means do_not_contact
    df.loc[(df.opt_out_date.fillna("") != "") | (df.status == "do_not_contact"), "do_not_contact"] = "Y"
    return df, n + len(extra)


def live_enrichment():
    """The Enrichment tab's rows for a rebuild: the saved live tab if present, else none."""
    p = os.path.join(LIVE_DIR, "enrichment-live.csv")
    if os.path.exists(p):
        e = pd.read_csv(p, dtype=str, keep_default_na=False)
        return e
    return pd.DataFrame(columns=ENRICH_COLS)


# ------------------------------------------------------------------ order and write
def order(df, side):
    lead = STABLE + DV_EXTRA[side] + CONTROL[side] + person_cols("primary", side) + person_cols("backup", side) \
        + REASON[side]
    drop = ["contact_found_date"]
    e_cols = [c for c in E_TRACKING + E_PERSONAL[side] if c not in lead]
    tail = HELPERS[side]
    extras = [c for c in EXTRAS if c in df.columns]
    rest = [c for c in df.columns if c not in lead + extras + tail + e_cols + drop]
    out = df[lead + extras + rest + e_cols + tail]
    assert len(set(out.columns)) == len(out.columns), "duplicate column"
    return out


IMPORT_DROP = {"score", "score_reason", "score_raw", "score_title", "score_known", "daily_view_rank",
               "ready_for_outreach", "ready_reason", "status", "do_not_contact", "opt_out_date", "known_to_founder",
               "hold_before_outreach", "founder_ok_to_queue", "promote_backup", "founder_review_cleared",
               "retailer_checked_date", "channel", "check_before_send", "contact_linkedin_url", "work_email",
               "email_status", "primary_work_email", "primary_email_status", "backup_work_email",
               "backup_email_status", "first_name", "last_name", "title", "contact_role", "contact_status",
               "contact_evidence", "contact_source_url", "contact_source_date", "title_match"}


def clay_import(df, side):
    """Clay is the research and email engine, never the table of record (review round 1, R1-02): the import
    carries no status, opt-out, founder control, formula or tracking column, so nothing Clay exports can
    overwrite them. Rows: ready rows first by score, then the other passed rows by rank, 175 in all."""
    p = df[df.gate_result == "pass"].copy()
    p["_r"] = (p.ready_for_outreach != "Y").astype(int)
    p["_k"] = p["rank"].astype(int)
    p = p.sort_values(["_r", "_k"]).head(K.CLAY_IMPORT_ROWS)
    p["ready_at_build"] = p.ready_for_outreach
    p["score_at_build"] = p.score
    p["domain"] = p.website.map(domain)
    keep = ["row_id", "company", "website", "domain", "rank", "score_at_build", "ready_at_build"]
    keep += [c for c in df.columns if c.startswith(("primary_", "backup_")) and c not in IMPORT_DROP
             and not c.endswith(("check_before_send", "reason_who", "title_match"))]
    keep += [c for c in (["street_address", "floor", "industry", "employee_count", "linkedin_company_url",
                          "top50", "onsite_band", "contacts_researched"] if side == "office" else
                         ["category", "product_example", "hq_city", "top60", "founder_review_type",
                          "contacts_researched"]) if c in p.columns]
    bad = [c for c in keep if c in IMPORT_DROP or c in E_TRACKING]
    assert not bad, bad
    return p[keep]


def main():
    res = {}
    enrich = live_enrichment()
    for side, fn, topcol in (("office", offices, "top50"), ("brand", brands, "top60")):
        df = fn()
        df = derive(df, side, enrich)
        df = order(df, side)
        name = "offices" if side == "office" else "brands"
        df.to_csv(os.path.join(C.A_DIR, f"{name}.csv"), index=False)
        dv = df[df.in_daily_view == "Y"].copy()
        dv["_k"] = dv.daily_view_rank.astype(int)
        dv = dv.sort_values("_k")[STABLE + DV_EXTRA[side]]
        dv.to_csv(os.path.join(C.A_DIR, f"daily-view-{name}.csv"), index=False)
        if side == "office":
            w = df[df.walk_slot != ""].copy()
            w["_k"] = w.walk_slot.astype(int)
            w.sort_values("_k")[WALK_VIEW].to_csv(os.path.join(C.A_DIR, "walk-list-offices.csv"), index=False)
        else:
            w = df[df.review_slot != ""].copy()
            w["_k"] = w.review_slot.astype(int)
            w.sort_values("_k")[REVIEW_VIEW].to_csv(os.path.join(C.A_DIR, "founder-review-brands.csv"), index=False)
        imp = clay_import(df, side)
        os.makedirs(os.path.join(C.A_DIR, "clay-import"), exist_ok=True)
        imp.to_csv(os.path.join(C.A_DIR, "clay-import", f"{name}-clay-import.csv"), index=False)
        res[side] = df
        print(f"{name}: {len(df)} rows, passed {int((df.gate_result == 'pass').sum())}, "
              f"{topcol} {int((df[topcol] == 'Y').sum())}, ready {int((df.ready_for_outreach == 'Y').sum())}, "
              f"daily view {len(dv)}, clay import {len(imp)}")
    enrich.to_csv(os.path.join(C.WORK, "enrichment_build.csv"), index=False)
    return res


if __name__ == "__main__":
    main()
