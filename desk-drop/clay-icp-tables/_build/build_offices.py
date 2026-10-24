#!/usr/bin/env python3
"""Stage 1: assemble, gate and score the Offices table.

Inputs (read-only): cluster-1-flatiron/companies.csv, near_miss.csv, coworking.csv,
buildings.csv; clay-icp-tables/_work/attendance_builtin.csv (if present).
Outputs: clay-icp-tables/offices.csv, clay-icp-tables/_work/top50_offices.csv.
"""
import csv
import math
import os
import re

import pandas as pd

import common as C
import config as K

B = C.B_DIR
REG_PATH = os.path.join(C.HERE, "id_registry_offices.json")

STABLE = ["row_id", "company", "first_name", "last_name", "title", "contact_linkedin_url", "work_email",
          "email_status", "channel", "score", "score_reason", "onsite_band", "nearest_stocked_retailer",
          "nearest_retailer_grade", "why_now", "why_now_url", "why_now_date", "known_to_founder",
          "startup_cpg_member", "do_not_contact", "status", "source_url", "found_date"]


def read(name):
    return pd.read_csv(os.path.join(B, name), dtype=str, keep_default_na=False)


# ------------------------------------------------------------------ attendance signals
ATT_PATTERNS = [
    (re.compile(r"(?:typical time )?on-site,? 5 days a week|on-site 5 days|in-office culture", re.I), "in-office-5"),
    (re.compile(r"hybrid,? 4 days", re.I), "hybrid-4"),
    (re.compile(r"hybrid,? 3 days", re.I), "hybrid-3"),
    (re.compile(r"jobs marked In-Office", re.I), "in-office-5"),
    (re.compile(r"remote-first|'Remote Workplace'", re.I), "remote"),
]


def attendance_from_notes(notes):
    for pat, key in ATT_PATTERNS:
        m = pat.search(notes or "")
        if m:
            s = max(0, m.start() - 90)
            e = min(len(notes), m.end() + 30)
            return key, notes[s:e].strip()
    return None, ""


def load_builtin_attendance():
    p = os.path.join(C.WORK, "attendance_builtin.csv")
    if not os.path.exists(p):
        return {}
    d = pd.read_csv(p, dtype=str, keep_default_na=False)
    return {r.company_id: r for r in d.itertuples()}


# ------------------------------------------------------------------ onsite estimate
BAND_EDGES = {"40-75": (40, 75), "76-150": (76, 150), "151-250": (151, 250), "251-500": (251, 500)}


def band_of(n):
    if n is None:
        return "unknown"
    if n < 40:
        return "under-40"
    if n <= 75:
        return "40-75"
    if n <= 150:
        return "76-150"
    if n <= 250:
        return "151-250"
    if n <= 500:
        return "251-500"
    return "over-500"


def size_class(n):
    if n is None:
        return "unknown"
    if n <= 500:
        return "le500"
    if n <= 1000:
        return "501-1000"
    if n < 5000:
        return "1001-4999"
    return "5000+"


def rate_for(n):
    if n is None or n <= 500:
        return K.RATE_UNDER_500, "67% (Partnership for NYC, firms under 500)"
    if n < 5000:
        return K.RATE_500_TO_4999, "57% (Partnership for NYC, all Manhattan firms; no figure for 500 to 4,999)"
    return K.RATE_5000_PLUS, "46% (Partnership for NYC, firms over 5,000)"


def estimate(r):
    """Returns dict: low, high, central, band, confidence, basis, flags, counts."""
    counts = []
    labels = []
    for col, lab in (("headcount_count", "first count"), ("headcount_second_count", "second count"),
                     ("company_wide_count_cited", "company-wide count cited")):
        v = C.num(r.get(col, ""))
        if v is not None and v not in counts:
            counts.append(v)
    src = []
    if r.get("headcount_count"):
        src.append(f"{r['headcount_count']} ({short_src(r.get('headcount_source_url',''))})")
    if r.get("headcount_second_count") and C.num(r["headcount_second_count"]) != C.num(r.get("headcount_count")):
        src.append(f"{r['headcount_second_count']} ({short_src(r.get('headcount_second_source_url',''))})")
    if not src and r.get("company_wide_count_cited"):
        src.append(f"{r['company_wide_count_cited']} ({short_src(r.get('headcount_source_url',''))})")
    band = r.get("headcount_band", "unknown")
    if counts:
        L, H = min(counts), max(counts)
        hc_text = " and ".join(src) if src else f"{L}"
    elif band in BAND_EDGES:
        L, H = BAND_EDGES[band]
        hc_text = f"band {band} (no count)"
    else:
        return dict(low=None, high=None, central=None, band="unknown", confidence="none",
                    basis="No sourced headcount, so no Tuesday estimate; ask the Tuesday count at intake.",
                    flags=[], company_size=None, scope="unknown", fit=None)
    scope = r.get("headcount_scope", "unknown")
    hq = r.get("hq_in_nyc", "unknown")
    if scope == "nyc-office":
        sh = K.SHARE_NYC_OFFICE_COUNT
        share_text = "the count is for the New York office"
        conf = "medium"
        company_size = None  # whole-company size not known from an NYC-office count
        # Normal Computing carries a second, company-wide count; use only the NYC count here
        L = H = C.num(r.get("headcount_count")) or L
        hc_text = f"{r.get('headcount_count')} in the New York office ({short_src(r.get('headcount_source_url',''))})"
        cw = C.num(r.get("headcount_second_count"))
        company_size = cw
    else:
        company_size = H
        if hq == "Y":
            sh = K.SHARE_HQ_NYC
            share_text = "50% to 100% of them in the New York office (HQ New York; share assumed)"
        else:
            sh = K.SHARE_HQ_ELSEWHERE
            where = "HQ outside New York" if hq == "N" else "HQ city unknown"
            share_text = f"5% to 100% of them in the New York office ({where}; share assumed)"
        conf = "low"
    rate, rate_text = rate_for(company_size if company_size else H)
    low = max(1, round(L * sh[0] * rate))
    high = max(1, round(H * sh[1] * rate))
    central = round(math.sqrt(low * high))
    # ---- space check (review round 1, R1-03): the row's own leased square footage bounds the estimate
    sf_vals = sorted({v for v in (C.num(x) for x in (r.get("leased_sf_mentioned", "") or "").split(";")) if v})
    space_text = ""
    if sf_vals:
        sf = sf_vals[-1]
        cap_hi = max(1, round(sf / K.SF_PER_PERSON_DENSE))
        cap_c = max(1, round(sf / K.SF_PER_PERSON_TYPICAL))
        sf_lo = max(1, round(sf / K.SF_PER_PERSON_ROOMY))
        hq_out = scope != "nyc-office" and hq != "Y"
        h_low, h_high = low, high
        if hq_out and len(sf_vals) == 1 and sf_lo <= high:
            # HQ outside New York (or unknown): the 5% to 100% share is a guess; the space is a fact
            low = max(low, sf_lo) if low <= cap_hi else sf_lo
            high = min(high, cap_hi)
            low = min(low, high)
            space_text = (f"; space-based for a company headquartered outside New York: {sf:,} sf seats "
                          f"{sf_lo} to {cap_hi} at {K.SF_PER_PERSON_ROOMY} to {K.SF_PER_PERSON_DENSE} sf per person, "
                          f"kept within the headcount math ({h_low} to {h_high})")
        elif hq_out and len(sf_vals) == 1:
            # the space seats more than the whole company's in-office staff: the share here stays unknown
            space_text = (f"; {sf:,} sf seats more than the whole company's in-office staff, so the space does not "
                          f"narrow the share in New York")
        elif low > cap_hi:
            low, high = sf_lo, cap_hi
            space_text = (f"; the headcount math ({h_low} to {h_high}) is more than {sf:,} sf can seat, so the "
                          f"range comes from the space: {sf_lo} to {cap_hi} at {K.SF_PER_PERSON_ROOMY} to "
                          f"{K.SF_PER_PERSON_DENSE} sf per person")
        elif high > cap_hi:
            high = cap_hi
            space_text = (f"; capped by {sf:,} sf at {K.SF_PER_PERSON_DENSE} sf per person (was {h_low} to {h_high})")
        central = round(math.sqrt(low * high))
        if central > cap_c:
            central = max(low, cap_c)
            space_text += f"; central capped at {sf:,} sf / {K.SF_PER_PERSON_TYPICAL} sf per person"
        if space_text:
            space_text += (" (largest square footage the sources mention at this address; if the company holds "
                           "more space here, intake corrects it)")
    flags = []
    if high < K.ONSITE_FLOOR:
        flags.append("under-30")
    elif low > K.ONSITE_CEILING:
        flags.append("over-250")
    else:
        if low < K.ONSITE_FLOOR:
            flags.append("may be under 30")
        if high > K.ONSITE_CEILING:
            flags.append("may exceed 250")
        if central < K.ONSITE_TARGET_LOW and central >= K.ONSITE_FLOOR:
            flags.append("30 to 39 is the founder's call")
        elif central < K.ONSITE_FLOOR:
            flags.append("central estimate under 30")
    # share of the range inside 40..250 on a ratio scale
    lo_, hi_ = math.log(low), math.log(high)
    a, b = math.log(K.ONSITE_TARGET_LOW), math.log(K.ONSITE_CEILING)
    if hi_ - lo_ < 1e-9:
        fit = 1.0 if a <= lo_ <= b else 0.0
    else:
        fit = max(0.0, min(hi_, b) - max(lo_, a)) / (hi_ - lo_)
    scope_word = "whole-company" if scope != "nyc-office" else "New York office"
    basis = (f"{hc_text} staff ({scope_word} count) x {share_text} x {rate_text} in on a weekday{space_text} "
             f"= {low} to {high}, central {central}; {conf} confidence; estimate until intake replaces it.")
    return dict(low=low, high=high, central=central, band=band_of(central), confidence=conf, basis=basis,
                flags=flags, company_size=company_size, scope=scope, fit=fit,
                space_capped="Y" if space_text else "N")


def short_src(url):
    u = url or ""
    for k, v in (("builtin", "Built In"), ("revelio", "Revelio Labs"), ("wikipedia", "Wikipedia"),
                 ("commercialobserver", "Commercial Observer"), ("linkedin", "LinkedIn")):
        if k in u:
            return v
    m = re.match(r"https?://(?:www\.)?([^/]+)", u)
    return m.group(1) if m else "source not stated"


COWORK_MOVE = re.compile(r"(?:moving|move|relocating) from (?:a |its )?(?:current location, a )?(?:WeWork|Industrious|"
                         r"coworking)", re.I)
NEWS = ("commercialobserver", "nyrej", "rebusinessonline", "connectcre", "therealdeal", "bisnow", "crainsnewyork",
        "globest", "mannpublications", "fnp", "costar")
STOP_OP = {"group", "hospitality", "services", "experience", "investment", "building", "office", "llc", "the",
           "deerfield", "affiliated", "company", "club"}


def _dom(u):
    m = re.match(r"https?://(?:www\.)?([^/]+)", (u or "").strip().lower())
    return m.group(1) if m else ""


def cowork_sites(cow):
    """Operator name -> the operator's own site, taken from any B source URL whose domain carries the
    operator's name (review round 1, R1-10). Operators with no such URL get 'unknown'."""
    out = {}
    for r in cow.to_dict("records"):
        toks = [t for t in re.findall(r"[a-z0-9]+", r["operator"].lower()) if len(t) >= 4 and t not in STOP_OP]
        for u in (r["source_url"], r["second_source_url"], r.get("pantry_source_url", "")):
            d = _dom(u)
            if d and any(t in d.replace("-", "") for t in toks) and not any(n in d for n in NEWS):
                out.setdefault(r["operator"], re.match(r"(https?://[^/]+)", u.strip()).group(1))
    # one operator name, several spellings (WeWork rows sourced from a directory)
    by_tok = {}
    for op, site in out.items():
        for t in re.findall(r"[a-z0-9]+", op.lower()):
            by_tok.setdefault(t, site)
    for r in cow.to_dict("records"):
        if r["operator"] not in out:
            for t in re.findall(r"[a-z0-9]+", r["operator"].lower()):
                if len(t) >= 4 and t not in STOP_OP and t in by_tok:
                    out[r["operator"]] = by_tok[t]
                    break
    return out


def source_type(url, website):
    """Class of an address source, from its domain (B's vocabulary plus operator-site)."""
    d, w = _dom(url), _dom(website)
    if d and w and (d == w or d.endswith("." + w) or w.endswith("." + d)):
        return "operator-site"
    if any(n in d for n in NEWS):
        return "leasing-press"
    return "other"


COWORK_SITE = {}


# ------------------------------------------------------------------ build
def main():
    comp = read("companies.csv")
    comp["table_origin"] = "companies.csv"
    near = read("near_miss.csv")
    near["table_origin"] = "near_miss.csv"
    cow = read("coworking.csv")
    COWORK_SITE.update(cowork_sites(cow))
    bld = read("buildings.csv").set_index("building_id")
    att_bi = load_builtin_attendance()
    reg = C.load_registry(REG_PATH)
    # stage 3: facts found during contact research, each with its source (stage3_corrections.csv)
    cor_p = os.path.join(C.WORK, "stage3_corrections.csv")
    cor = pd.read_csv(cor_p, dtype=str, keep_default_na=False) if os.path.exists(cor_p) else pd.DataFrame(
        columns=["table", "key", "field", "new_value", "source_url", "source_date", "reason"])
    cor = cor[cor.table == "offices"]

    rows = []
    for df in (comp, near):
        for r in df.to_dict("records"):
            rows.append(("company", r))
    for r in cow.to_dict("records"):
        rows.append(("coworking-operator", r))

    out = []
    for kind, r in rows:
        o = {}
        if kind == "company":
            bid = r["company_id"]
            o["row_id"] = "AO-" + bid[2:]  # B-C-001 -> AO-C-001
            o["org_type"] = "company"
            o["b_id"] = bid
            o["company"] = r["company_name"]
            o["website"] = r["website"] or "unknown"
            o["industry"] = r["industry"] or "unknown"
            o["street_address"] = r["street_address"]
            o["floor"] = r["floor"] or "unknown"
            o["zip"] = r["zip"]
            o["lat"], o["lon"] = r["lat"], r["lon"]
            o["building_id"] = r["building_id"]
            o["in_boundary"] = r["in_boundary"]
            o["blocks_outside"] = r["blocks_outside"]
            o["address_source_url"] = r["address_source_url"]
            o["address_source_date"] = r["address_source_date"]
            o["address_source_type"] = r["address_source_type"]
            o["second_source_url"] = r["second_source_url"]
            o["second_source_date"] = r["second_source_date"]
            o["confidence"] = r["confidence"]
            o["lease_status"] = r["lease_status"]
            o["move_in_date"] = r["move_in_date"]
            o["in_coworking"] = r["in_coworking"]
            o["coworking_id"] = r["coworking_id"]
            o["b_candidate_status"] = r["candidate_status"]
            o["near_miss_class"] = r.get("near_miss_class", "")
            o["nyc_office_may_fit"] = r.get("nyc_office_may_fit", "")
            o["employee_count"] = r["headcount_count"] or r.get("company_wide_count_cited", "") or "unknown"
            o["employee_count_second"] = r["headcount_second_count"] or ""
            o["headcount_band"] = r["headcount_band"]
            o["headcount_scope"] = r["headcount_scope"]
            o["headcount_check"] = r["headcount_check"]
            o["headcount_source_url"] = r["headcount_source_url"]
            o["headcount_second_source_url"] = r["headcount_second_source_url"]
            o["hq_city"] = r["hq_city"] or "unknown"
            o["hq_in_nyc"] = r["hq_in_nyc"] or "unknown"
            o["parent_company"] = r["parent_company"] or "unknown"
            o["linkedin_company_url"] = r["linkedin_company_url"] or "unknown"
            o["leased_sf_mentioned"] = r["leased_sf_mentioned"]
            o["b_notes"] = r["notes"]
            o["found_date"] = r["found_date"]
            o["source_url"] = r["address_source_url"]
            b = bld.loc[r["building_id"]] if r["building_id"] in bld.index else None
            o["building_name"] = b["building_name"] if b is not None else "unknown"
            o["lobby_type"] = r["building_lobby_type"] or "unknown"
            o["lobby_source_url"] = b["lobby_source_url"] if b is not None else ""
            o["lobby_note"] = ""
            if o["lobby_type"] != "unknown" and not o["lobby_source_url"]:
                # review round 1 (R1-13): a lobby type with no source is not a fact
                o["lobby_note"] = f"B lists '{o['lobby_type']}' with no lobby source: unknown until the walk"
                o["lobby_type"] = "unknown"
            o["coi_required"] = b["coi_required"] if b is not None else "unknown"
            est = estimate(r)
        else:
            cid = r["coworking_id"]
            o["row_id"] = "AO-" + cid[2:]
            o["org_type"] = "coworking-operator"
            o["b_id"] = cid
            o["company"] = f"{r['location_name']}"
            # review round 1 (R1-10): the operator's own domain only, never a news or directory domain
            o["website"] = COWORK_SITE.get(r["operator"], "unknown")
            o["industry"] = "coworking operator"
            o["street_address"] = r["street_address"]
            o["floor"] = r["floors"] or "unknown"
            o["zip"] = (re.findall(r"\b(100\d\d)\b", r["street_address"]) or [""])[-1]
            o["lat"], o["lon"] = r["lat"], r["lon"]
            o["building_id"] = r["building_id"]
            o["in_boundary"] = r["in_boundary"]
            o["blocks_outside"] = r["blocks_outside"]
            o["address_source_url"] = r["source_url"]
            o["address_source_date"] = r["source_date"]
            o["address_source_type"] = source_type(r["source_url"], o["website"])
            o["second_source_url"] = r["second_source_url"]
            o["second_source_date"] = ""
            o["confidence"] = r["confidence"]
            o["lease_status"] = r["status"]
            o["move_in_date"] = ""
            o["in_coworking"] = "N"
            o["coworking_id"] = cid
            o["b_candidate_status"] = "coworking-operator"
            o["near_miss_class"] = ""
            o["nyc_office_may_fit"] = ""
            o["employee_count"] = "unknown"
            o["employee_count_second"] = ""
            o["headcount_band"] = "unknown"
            o["headcount_scope"] = "unknown"
            o["headcount_check"] = ""
            o["headcount_source_url"] = ""
            o["headcount_second_source_url"] = ""
            o["hq_city"] = "n/a (operator site)"
            o["hq_in_nyc"] = "unknown"
            o["parent_company"] = r["operator"]
            o["linkedin_company_url"] = ""
            o["leased_sf_mentioned"] = ""
            o["b_notes"] = (r["notes"] + f" | pantry_control={r['pantry_control']} ({r['pantry_source_url']}); "
                            f"exclusive food contract signal: {r['exclusive_food_contract_signal']}")
            o["found_date"] = r["found_date"]
            o["source_url"] = r["source_url"]
            b = bld.loc[r["building_id"]] if r["building_id"] in bld.index else None
            o["building_name"] = b["building_name"] if b is not None else "unknown"
            o["lobby_type"] = b["lobby_type"] if b is not None else "unknown"
            o["lobby_source_url"] = b["lobby_source_url"] if b is not None else ""
            o["lobby_note"] = ""
            if o["lobby_type"] not in ("unknown", "") and not o["lobby_source_url"]:
                o["lobby_note"] = f"B lists '{o['lobby_type']}' with no lobby source: unknown until the walk"
                o["lobby_type"] = "unknown"
            o["coi_required"] = b["coi_required"] if b is not None else "unknown"
            o["pantry_control"] = r["pantry_control"]
            est = dict(low=None, high=None, central=None, band="unknown", confidence="none",
                       basis="Coworking site: member headcount not sourced; treat as one office if the operator "
                             "controls the pantry and ask the Tuesday count at intake.",
                       flags=[], company_size=None, scope="unknown", fit=None)
        o.setdefault("pantry_control", "")
        o["a_corrections"] = ""
        for c in cor[cor.key == o["row_id"]].to_dict("records"):
            o[c["field"]] = c["new_value"]
            o["a_corrections"] += f"{c['field']} <- {c['source_url']} ({c['source_date']}): {c['reason']} "
        o["a_corrections"] = o["a_corrections"].strip()
        o["onsite_low"] = est["low"] if est["low"] is not None else "unknown"
        o["onsite_high"] = est["high"] if est["high"] is not None else "unknown"
        o["onsite_central"] = est["central"] if est["central"] is not None else "unknown"
        o["onsite_band"] = est["band"]
        o["onsite_confidence"] = est["confidence"]
        o["onsite_basis"] = est["basis"]
        o["onsite_label"] = "estimate until intake replaces it"
        o["onsite_flags"] = ";".join(est["flags"])
        o["onsite_space_check"] = est.get("space_capped", "N")

        # ---------------- gates (before any enrichment)
        fails = []
        if o["in_boundary"] != "Y":
            fails.append(f"outside the cluster ({o['blocks_outside']} blocks outside the line)")
        if kind == "company" and o["in_coworking"] == "Y":
            fails.append(f"inside a coworking space ({o['coworking_id']})")
        if kind == "company" and COWORK_MOVE.search(r["notes"] or ""):
            # review round 1 (R1-15): still a coworking tenant today, so it fails the coworking gate until it moves
            fails.append("inside a coworking space until its move to this address (B notes); re-check after "
                         + (r["move_in_date"] or "the move") )
        if kind == "company" and r["candidate_status"] == "excluded-not-office":
            fails.append("no staffed office shown at the address (B: excluded-not-office)")
        if "under-30" in est["flags"]:
            fails.append(f"Tuesday estimate under 30 ({est['low']} to {est['high']})")
        if "over-250" in est["flags"]:
            fails.append(f"Tuesday estimate over 250 ({est['low']} to {est['high']})")
        if kind == "coworking-operator" and r["pantry_control"] != "operator":
            fails.append(f"operator control of the pantry not shown (pantry_control={r['pantry_control']})")
        if kind == "coworking-operator" and r["status"] == "possibly-closed":
            fails.append("site possibly closed (B status)")
        o["gate_result"] = "pass" if not fails else "fail"
        o["gate_reason"] = "; ".join(fails) if fails else "passes all hard gates"

        # ---------------- attendance signals (only from sources in the row or a fetched page)
        key, quote = (None, "")
        att_url, att_date = "", ""
        if kind == "company":
            key, quote = attendance_from_notes(r["notes"])
            if key:
                att_url = r["headcount_source_url"] if "builtin" in r["headcount_source_url"] else (
                    r["hq_source_url"] if "builtin" in r.get("hq_source_url", "") else r["address_source_url"])
                att_date = r.get("headcount_source_date") or r["found_date"]
            bi = att_bi.get(r["company_id"])
            if bi is not None and bi.attendance_key:
                if not key or key == "unknown":
                    key, quote, att_url, att_date = bi.attendance_key, bi.attendance_text, bi.url, bi.opened
                elif bi.attendance_key != key:
                    quote += f" | Built In page opened {bi.opened}: {bi.attendance_text}"
        tue_named = "N"
        if kind == "company":
            bi2 = att_bi.get(r["company_id"])
            if bi2 is not None and getattr(bi2, "tuesday_named", "N") == "Y":
                tue_named = "Y"
        o["tuesday_named_in_policy"] = tue_named
        o["attendance_signal"] = key or "unknown"
        o["attendance_evidence"] = quote if key else "unknown"
        o["attendance_source_url"] = att_url
        o["attendance_source_date"] = att_date

        # ---------------- office why-now: a lease or move reported in the last 12 months
        o["why_now"], o["why_now_url"], o["why_now_date"] = "", "", ""
        if kind == "company" and r["address_source_type"] in ("leasing-press", "landlord-release", "broker-release"):
            d = r["address_source_date"]
            slug = r["address_source_url"].lower()
            words = [w for w in re.findall(r"[a-z0-9]+", r["company_name"].lower().replace("&", " "))
                     if len(w) >= 4 and w not in ("group", "company", "worldwide", "partners", "international",
                                                   "office", "security", "health", "energy", "global")]
            own = any(w in slug for w in words[:2])
            if own and d and d[:7] >= "2025-11":
                o["why_now"] = f"New or renewed lease at {r['street_address']} reported {d}"
                o["why_now_url"] = r["address_source_url"]
                o["why_now_date"] = d

        # ---------------- stable columns
        o["first_name"] = o["last_name"] = o["title"] = ""
        o["contact_linkedin_url"] = o["work_email"] = ""
        o["email_status"] = "none"
        o["channel"] = "linkedin"
        o["nearest_stocked_retailer"] = ""
        o["nearest_retailer_grade"] = ""
        o["known_to_founder"] = "N"
        o["startup_cpg_member"] = "unknown"
        o["do_not_contact"] = "N"
        o["status"] = "new"
        for c in ("primary_contact_status", "backup_first_name", "backup_last_name", "backup_title",
                  "backup_linkedin_url", "backup_work_email", "backup_email_status", "contact_source_url",
                  "contact_found_date", "title_match"):
            o[c] = ""
        o["primary_contact_status"] = "none"
        o["backup_email_status"] = "none"
        o["title_match"] = "none"

        # ---------------- score
        pts = {}
        if est["fit"] is None:
            pts["onsite"] = K.P_ONSITE_UNKNOWN
        else:
            pts["onsite"] = K.W_ONSITE_FIT * est["fit"] + (K.W_ONSITE_NYC_COUNT if est["scope"] == "nyc-office" else 0)
        sc = size_class(est["company_size"]) if kind == "company" else "unknown"
        if kind == "company" and est["scope"] == "nyc-office" and est["company_size"] is None:
            sc = "unknown"
        pts["size"] = K.P_SIZE[sc] + (K.P_PARENT_NAMED if o["parent_company"] not in ("unknown", "") and kind == "company" else 0)
        pts["attend"] = min(K.W_ATTEND, K.P_ATTEND[o["attendance_signal"]] +
                            (K.P_TUESDAY_NAMED if o["tuesday_named_in_policy"] == "Y" else 0))
        conflict = bool(re.search(r"CONFLICT", o["b_notes"])) and "Conflict resolved" not in o["b_notes"]
        pts["address"] = (0 if conflict else K.P_LEASE.get(o["lease_status"], 0)) + K.P_CONF.get(o["confidence"], 0)
        holds = []
        if o["lease_status"] == "signed-not-occupied":
            holds.append("lease signed, move not confirmed: check the lobby directory before outreach (B)")
        if conflict:
            holds.append("address conflict in B's sources: check the lobby directory before outreach (B)")
        if o["lease_status"] == "moving-out":  # stage 3, at E's request: confirm the address it is moving to
            holds.append("moving out of this address: confirm where the office will be before outreach (B)")
        if o["lease_status"] == "possibly-closed":
            holds.append("site possibly closed: walk by first (B)")
        if COWORK_MOVE.search(o["b_notes"]):
            holds.append("still in a coworking space until the move")
        o["source_note"] = ""
        if "sec.gov" in (o["address_source_url"] or "") or "sec.gov" in (o["second_source_url"] or ""):
            o["source_note"] = ("cites a sec.gov filing: agents do not open it (EDGAR demands a contact email); "
                                "the founder may open it in a browser")
        o["hold_before_outreach"] = "Y" if holds else "N"
        o["hold_reason"] = "; ".join(holds)
        pts["title"] = K.P_TITLE[o["title_match"]]
        pts["known"] = K.W_KNOWN if o["known_to_founder"] == "Y" else 0
        total = round(sum(pts.values()), 1)
        o["score"] = total if o["gate_result"] == "pass" else 0
        o["score_raw"] = total
        o["score_onsite"] = round(pts["onsite"], 1)
        o["score_size"] = pts["size"]
        o["score_attendance"] = pts["attend"]
        o["score_address"] = pts["address"]
        o["score_title"] = pts["title"]
        o["score_known"] = pts["known"]
        o["size_class"] = sc
        o["score_reason"] = reason(o, est, sc)
        o["onsite_fit_share"] = round(est["fit"], 2) if est["fit"] is not None else "unknown"
        out.append(o)

    df = pd.DataFrame(out)
    # rank among passed rows
    df["_conf"] = df.confidence.map({"high": 0, "medium": 1, "low": 2}).fillna(3)
    df["_fit"] = pd.to_numeric(df.onsite_fit_share, errors="coerce").fillna(-1)
    df = df.sort_values(["gate_result", "score", "_fit", "_conf", "company"],
                        ascending=[False, False, False, True, True]).reset_index(drop=True)
    passed = df.gate_result == "pass"
    ranks, k = [], 0
    for ok in passed:
        if ok:
            k += 1
            ranks.append(str(k))
        else:
            ranks.append("")
    df["rank"] = ranks
    df["top50"] = ["Y" if (r != "" and int(r) <= 50) else "N" for r in ranks]
    df = df.drop(columns=["_conf", "_fit"])

    lead = STABLE + ["rank", "top50", "gate_result", "gate_reason", "org_type", "b_id", "website", "industry",
                     "employee_count", "employee_count_second", "headcount_band", "headcount_scope",
                     "headcount_check", "headcount_source_url", "headcount_second_source_url", "size_class",
                     "hq_city", "hq_in_nyc", "parent_company", "linkedin_company_url",
                     "street_address", "floor", "zip", "lat", "lon", "in_boundary", "blocks_outside",
                     "building_id", "building_name", "address_source_url", "address_source_date",
                     "address_source_type", "second_source_url", "second_source_date", "source_note", "confidence",
                     "lease_status", "move_in_date", "in_coworking", "coworking_id", "pantry_control",
                     "lobby_type", "lobby_source_url", "lobby_note", "coi_required",
                     "attendance_signal", "tuesday_named_in_policy", "attendance_evidence", "attendance_source_url",
                     "attendance_source_date", "hold_before_outreach", "hold_reason",
                     "onsite_low", "onsite_high", "onsite_central", "onsite_confidence", "onsite_flags", "onsite_space_check",
                     "onsite_basis", "onsite_label", "onsite_fit_share",
                     "score_raw", "score_onsite", "score_size", "score_attendance", "score_address",
                     "score_title", "score_known",
                     "primary_contact_status", "title_match", "contact_source_url", "contact_found_date",
                     "backup_first_name", "backup_last_name", "backup_title", "backup_linkedin_url",
                     "backup_work_email", "backup_email_status",
                     "b_candidate_status", "near_miss_class", "nyc_office_may_fit", "leased_sf_mentioned", "b_notes",
                     "a_corrections"]
    df = df[lead]
    df.to_csv(os.path.join(C.WORK, "stage1_offices.csv"), index=False, quoting=csv.QUOTE_MINIMAL)  # stage 3 merges contacts into offices.csv
    top = df[df.top50 == "Y"].copy()
    top_cols = ["rank", "row_id", "company", "score", "score_reason", "hold_before_outreach", "hold_reason",
                "onsite_band", "onsite_low", "onsite_high",
                "onsite_confidence", "street_address", "building_name", "lobby_type", "attendance_signal",
                "lease_status", "confidence", "website", "linkedin_company_url",
                "first_name", "last_name", "title", "contact_linkedin_url", "work_email", "email_status",
                "channel", "backup_first_name", "backup_last_name", "backup_title", "backup_linkedin_url",
                "known_to_founder", "do_not_contact", "status", "source_url", "found_date"]
    top[top_cols].to_csv(os.path.join(C.WORK, "top50_offices.csv"), index=False)
    print("offices", len(df), "passed", int(passed.sum()), "top50", len(top))
    print(df.gate_reason.value_counts().head(20).to_string())


def reason(o, est, sc):
    parts = []
    if est["low"] is None:
        parts.append("Tuesday headcount unknown (no sourced count)")
    else:
        parts.append(f"Tuesday estimate {est['low']} to {est['high']} ({est['confidence']} confidence)")
    size_txt = {"le500": "under 500 staff company-wide", "501-1000": "501 to 1,000 staff company-wide",
                "1001-4999": "1,001 to 4,999 staff company-wide", "5000+": "5,000+ staff company-wide",
                "unknown": "company size unknown"}[sc]
    if o["org_type"] == "coworking-operator":
        size_txt = "coworking operator site (one office if it controls the pantry)"
    if o["parent_company"] not in ("unknown", "") and o["org_type"] == "company":
        size_txt += f" with a named parent ({o['parent_company']})"
    parts.append(size_txt)
    att = {"in-office-5": "on-site 5 days a week per its profile", "hybrid-4": "hybrid 4 days",
           "hybrid-3": "hybrid 3 days", "hybrid-unspecified": "hybrid (days not stated)",
           "hybrid-2-or-less": "hybrid 2 days or fewer", "unknown": "no attendance signal",
           "remote": "remote-first signal"}[o["attendance_signal"]]
    if o.get("tuesday_named_in_policy") == "Y":
        att += " with Tuesday named as an office day"
    parts.append(att)
    parts.append(f"{o['lease_status']} at a {o['confidence']}-confidence address"
                 + (" (hold: " + o["hold_reason"].split(":")[0] + ")" if o.get("hold_before_outreach") == "Y" else ""))
    if o["gate_result"] == "pass":
        parts.append("no contact found yet")
        return C.one_sentence(", ".join(parts[:-1]) + "; " + parts[-1])
    return C.one_sentence(f"Gated out: {o['gate_reason']}")


if __name__ == "__main__":
    main()
