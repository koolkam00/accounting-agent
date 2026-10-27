#!/usr/bin/env python3
"""Stage 1: merge, enrich, deduplicate, gate and score the Brands table.

Inputs (read-only): clay-icp-tables/_work/brands_BR1..BR5.csv, enrich_*.csv;
cluster-1-flatiron/retailers.csv and B's boundary (for the ten-block test).
Outputs: clay-icp-tables/brands.csv, clay-icp-tables/_work/top60_brands.csv,
clay-icp-tables/_work/brand_store_links.csv (every brand-to-store link with grade and blocks).
"""
import csv
import datetime as dt
import glob
import json
import math
import os
import re

import pandas as pd

import common as C
import config as K

REG_PATH = os.path.join(C.HERE, "id_registry_brands.json")
STORE_GEO = os.path.join(C.WORK, "store_geocodes.json")
TODAY = dt.date(2026, 10, 24)

STABLE = ["row_id", "company", "first_name", "last_name", "title", "contact_linkedin_url", "work_email",
          "email_status", "channel", "score", "score_reason", "onsite_band", "nearest_stocked_retailer",
          "nearest_retailer_grade", "why_now", "why_now_url", "why_now_date", "known_to_founder",
          "startup_cpg_member", "do_not_contact", "status", "source_url", "found_date"]

FILE_OF_ENRICH = {"enrich_BR1_BR2.csv": ("BR1", "BR2"), "enrich_BR3.csv": ("BR3",), "enrich_BR4.csv": ("BR4",)}


# ------------------------------------------------------------------ load and enrich
def load():
    fr = []
    for f in sorted(glob.glob(os.path.join(C.WORK, "brands_BR*.csv"))):
        d = pd.read_csv(f, dtype=str, keep_default_na=False)
        tag = os.path.basename(f)[7:10]
        d["research_slice"] = tag
        d["slice_row"] = [f"{tag}:{i + 2}" for i in range(len(d))]  # CSV line number
        fr.append(d)
    b = pd.concat(fr, ignore_index=True)
    b["enrichment_log"] = ""
    b["enrich_snippet_fields"] = ""
    for c in ("founder_profile_url", "marketing_profile_url"):
        b["_orig_" + c] = b[c]
    esrc = {i: {} for i in b.index}
    for f, tags in FILE_OF_ENRICH.items():
        e = pd.read_csv(os.path.join(C.WORK, f), dtype=str, keep_default_na=False)
        for r in e.to_dict("records"):  # later rows win (file order)
            idx = b.index[(b.brand == r["brand"]) & (b.research_slice.isin(tags))]
            if len(idx) != 1:
                raise SystemExit(f"enrichment row does not match one brand row: {r['brand']} ({f})")
            i = idx[0]
            field, new = r["field"], r["new_value"]
            if field not in b.columns:
                raise SystemExit(f"unknown field {field}")
            cur = b.at[i, field]
            if new.startswith("(append)"):
                val = (cur + " | " if cur else "") + new[len("(append)"):].strip()
            elif new.startswith("(existing WFM URLs);"):
                val = (cur + "; " if cur else "") + new[len("(existing WFM URLs);"):].strip()
            else:
                val = new
            b.at[i, field] = val
            esrc[i][field] = (r["source_url"], r["confidence"])
            b.at[i, "enrichment_log"] += (f"{field} <- {r['source_url'] or 'no url'} ({r['source_date']}, "
                                          f"{r['confidence']}); ")
            if r["confidence"] == "snippet-unverified":
                b.at[i, "enrich_snippet_fields"] += field + ";"
    b["_esrc"] = [json.dumps(esrc[i]) for i in b.index]
    # gate-input checks made in stage 1 (online store evidence), each with its source
    chk = pd.read_csv(os.path.join(C.WORK, "online_store_checks.csv"), dtype=str, keep_default_na=False)
    for r in chk.to_dict("records"):
        idx = b.index[b.brand == r["brand"]]
        if len(idx) != 1:
            raise SystemExit(f"online_store_checks row does not match one brand: {r['brand']}")
        i = idx[0]
        b.at[i, "online_store"] = r["online_store"]
        if r["online_store_url"]:
            b.at[i, "online_store_url"] = r["online_store_url"]
        b.at[i, "notes"] += f" | Stage 1 online-store check {r['opened']}: {r['basis']} ({r['source_url']})"
        b.at[i, "enrichment_log"] += f"online_store <- {r['source_url']} ({r['opened']}, opened, stage 1); "
    # stage 1 spot-check corrections, each with its source and reason
    cor = pd.read_csv(os.path.join(C.WORK, "stage1_corrections.csv"), dtype=str, keep_default_na=False)
    # stage 3 adds facts found during contact research, in the same format (stage3_corrections.csv)
    cor["stage"] = "stage 1"
    s3 = os.path.join(C.WORK, "stage3_corrections.csv")
    if os.path.exists(s3):
        c3 = pd.read_csv(s3, dtype=str, keep_default_na=False)
        c3["stage"] = "stage 3"
        cor = pd.concat([cor, c3], ignore_index=True)
    for r in cor[cor.table == "brands"].to_dict("records"):
        idx = b.index[b.brand == r["key"]]
        if len(idx) != 1:
            raise SystemExit(f"correction row does not match one brand: {r['key']}")
        i = idx[0]
        old_v = b.at[i, r["field"]]
        if r["new_value"].startswith("(append)"):
            add = r["new_value"][len("(append)"):].strip()
            b.at[i, r["field"]] = (old_v + " | " if old_v else "") + add
            if r["field"] == "founder_review_reason":
                b.at[i, "founder_review"] = "Y"
        else:
            b.at[i, r["field"]] = r["new_value"]
        if r["field"] == "why_now":
            b.at[i, "notes"] += f" | Stage 1 correction {r['source_date']}: {r['reason']} (was: {old_v[:160]})"
        b.at[i, "enrichment_log"] += f"{r['field']} <- {r['source_url']} ({r['source_date']}, {r['stage']} correction); "
    return b


# ------------------------------------------------------------------ dedupe
def norm_name(s):
    s = s.lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = s.replace("&", " and ").replace("'", "").replace("’", "")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    stop = {"the", "co", "company", "inc", "llc", "foods", "food", "snacks", "snack", "brand", "brands", "and"}
    return " ".join(w for w in s.split() if w not in stop)


def norm_domain(u):
    m = re.match(r"https?://(?:www\.)?([^/]+)", (u or "").strip().lower())
    return m.group(1) if m else ""


# ------------------------------------------------------------------ stores
B_RET = None


def b_retailers():
    global B_RET
    if B_RET is None:
        B_RET = pd.read_csv(os.path.join(C.B_DIR, "retailers.csv"), dtype=str, keep_default_na=False)
    return B_RET


STREET_ABBR = [(r"\bavenue\b", "ave"), (r"\bstreet\b", "st"), (r"\bplace\b", "pl"), (r"\bsquare\b", "sq"),
               (r"\bsouth\b", "s"), (r"\bnorth\b", "n"), (r"\beast\b", "e"), (r"\bwest\b", "w"),
               (r"\bfifth\b", "5th"), (r"\bsixth\b", "6th"), (r"\bseventh\b", "7th"), (r"\beighth\b", "8th"),
               (r"\bthird\b", "3rd"), (r"\bsecond\b", "2nd"), (r"\bninth\b", "9th"), (r"\btenth\b", "10th"),
               (r"\bfirst\b", "1st"), (r"\bpark ave s\b", "park ave s"), (r"\bof the americas\b", "6th")]


def norm_addr(a):
    a = a.lower().split(",")[0]
    a = re.sub(r"[.]", "", a)
    for p, rep in STREET_ABBR:
        a = re.sub(p, rep, a)
    a = re.sub(r"\b(\d+)(st|nd|rd|th)\b", r"\1", a)
    return re.sub(r"\s+", " ", a).strip()


def match_b(name, addr):
    na = norm_addr(addr) if addr else ""
    for r in b_retailers().itertuples():
        if na and norm_addr(r.street_address) == na:
            return r
    # name fallback for chains with branch names
    nn = name.lower()
    for r in b_retailers().itertuples():
        rn = r.retailer_name.lower()
        key = re.sub(r"\(.*?\)", "", rn).strip()
        if key and (key in nn or nn in key) and len(nn) > 8:
            return r
    return None


def store_geo_cache():
    try:
        return json.load(open(STORE_GEO))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


GEO = None


def locate(name, addr):
    """Returns (blocks_outside, inside, how). blocks None if the store cannot be placed."""
    global GEO
    if GEO is None:
        GEO = store_geo_cache()
    if "pop up grocer" in name.lower() or "popup grocer" in name.lower():
        return None, False, "Pop Up Grocer: brand-level listing outside the band; never near-cluster"
    r = match_b(name, addr)
    if r is not None:
        bo = float(r.blocks_outside)
        return bo, r.inside_boundary == "Y", f"B retailers.csv {r.retailer_id} ({r.retailer_name})"
    if not addr or not re.match(r"^\d", addr.strip()):
        return None, False, "no street address to place it"
    key = norm_addr(addr)
    if key not in GEO:
        g = C.geocode(addr.split(",")[0] + ", New York, NY")
        GEO[key] = g
        json.dump(GEO, open(STORE_GEO, "w"), indent=1, sort_keys=True)
    g = GEO[key]
    if not g:
        return None, False, "geocoder found no match"
    bo = C.blocks_outside(g["lat"], g["lon"])
    return bo, bo == 0, f"geocoded ({g.get('source', 'geocoder')}: {g.get('label', '')})"


GRADE_RE = re.compile(r"\((store_selector|brand_claim|unverified|seen_on_shelf)([^)]*)\)\s*$")


def parse_store_list(s):
    out = []
    if not s or s.lower().startswith(("unknown", "none")):
        return out
    parts, depth, cur = [], 0, ""
    for ch in s:
        depth += (ch == "(") - (ch == ")")
        if ch == ";" and depth <= 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    for part in [p.strip() for p in parts if p.strip()]:
        m = GRADE_RE.search(part)
        grade, extra = ("unverified", "") if not m else (m.group(1), m.group(2).strip(" ,:"))
        body = part[: m.start()].strip() if m else part
        body = re.sub(r"\s*\((?:name read|unconfirmed|outside|just south|brand-level|brand locator|cans not)[^)]*\)", "", body)
        bits = [x.strip() for x in body.split(",")]
        addr = ""
        for x in reversed(bits):
            if re.match(r"^\d", x):
                addr = re.split(r"\s+(?:is|likely|near|at the|which|beyond|per|-|–)\s", x)[0].strip()
                break
        name = bits[0]
        out.append(dict(name=name, addr=addr, grade=grade, extra=extra, raw=part))
    return out


def regrade(st, row_text):
    """CONTRACTS section 4 re-grade. Returns (grade, note)."""
    g = st["grade"]
    n = st["name"].lower()
    raw = st["raw"].lower()
    if g == "seen_on_shelf":
        return "unverified", "seen_on_shelf is founder-only; reset to unverified"
    if "pop up grocer" in n or "popup grocer" in n:
        return ("brand_claim" if g in ("store_selector", "brand_claim") else "unverified"), \
            "Pop Up Grocer directory lists the brand, not the SKU (capped at brand_claim)"
    if g == "store_selector" and "whole foods" not in n:
        return "brand_claim", "store_selector is kept only for a retailer's own store-scoped catalog (Whole Foods)"
    if "unconfirmed" in raw or "not confirmed" in raw:
        return "unverified", "listing does not confirm this store or item"
    if g == "store_selector" and ("only" in st["extra"].lower()):
        return "store_selector", f"store catalog covers a different SKU ({st['extra']})"
    return g, ""


# ------------------------------------------------------------------ classifiers
NE = {"NJ", "CT", "PA", "MA", "VT", "NH", "ME", "RI"}
NYC_WORDS = ("new york", "brooklyn", "queens", "bronx", "manhattan", "staten island", "long island city",
             "astoria", "harlem", "greenpoint", "williamsburg", "nyc", "woodside", "sunnyside", "ridgewood")


def ny_class(city, state):
    c, s = (city or "").lower(), (state or "").upper()
    unver = "unverified" in c or "founder to confirm" in c or "UNVERIFIED" in s or " OR " in s
    st = s.split(" ")[0]
    if st == "NY":
        if any(w in c for w in NYC_WORDS) and "hudson valley" not in c:
            cls = "nyc"
        elif c.startswith("unknown") or not c:
            cls = "nys"
        else:
            cls = "nys"
    elif st in NE:
        cls = "northeast"
    elif st in ("", "UNKNOWN"):
        cls = "nyc" if any(w in c for w in NYC_WORDS) else "unknown"
    else:
        cls = "elsewhere"
    return cls, unver


LISTING_HINTS = ("shopify", "products.json", "published_at", "added to", "listed on", "publish date",
                 "listing date", "pop up grocer", "popupgrocer", "featured=new", "'new' tag", "addedon",
                 "store?format=json", "new on store", "added new", "on brand store", "on its store",
                 "on own store", "listed at", "published on")


def why_now_class(why, url, date, notes, website=""):
    if not date or date == "unknown" or not re.match(r"^\d{4}-\d{2}", date):
        return "none", None, None
    y, m = int(date[:4]), int(date[5:7])
    d = int(date[8:10]) if len(date) >= 10 else 1
    try:
        age = (TODAY - dt.date(y, m, d)).days
    except ValueError:
        return "none", None, None
    if age > K.WHY_NOW_WINDOW_DAYS or age < -30:
        return "stale", age, None
    t = (why + " " + url + " " + notes).lower()
    u = url.lower()
    kind = "press"
    if any(h in (why + " " + u).lower() for h in LISTING_HINTS) or u.endswith("products.json"):
        kind = "listing"
    # the brand's own site (product page, homepage, own press page) is the brand's claim, not press
    bd, ud = norm_domain(website), norm_domain(url)
    if bd and ud and (ud == bd or ud.endswith("." + bd) or bd.endswith("." + ud)):
        kind = "listing"
    if "unverified" in why.lower() or "snippet" in why.lower() or "not opened" in why.lower():
        return "unverified", age, None  # an unverified why-now earns no points (spot check round 3)
    return kind, age, ("0-180" if age <= 180 else "181-365")


SEV_RULES = [  # (type, pattern) checked against the researcher's founder_review_reason, funding_stage, website
    ("owner", r"(acquired by|owned by|joined upsnack|part of seattle chocolate|grupo bimbo|mondelez|johnsonville|"
              r"the wine group|uptime energy|hersheyland|\(hershey\)|phony negroni line acquired)"),
    ("scale", r"(above the \$?10m|above \$10m|above the band|above size band|above the size band|well over the band|"
              r"\$100m|\d\d,\d{3}\+? doors|4,000\+ doors|thousands of retailers|national brand|broad national|"
              r"wide national|#1 freeze-dried|costco|scale suggests|hershey's among backers|celebrity co-founder|"
              r"larger marketing budget|33 to 39 skus)"),
    ("not-emerging", r"(luxury|heritage|not an emerging|founded 1998|cafe group|20-year-old|12 years old|"
                     r"long-established|30\+ years|established celebrity|established olive|established rather|"
                     r"established manufacturer|restaurant-led)"),
    ("dormant", r"(dormant|sold out|may be inactive|no new sku since)"),
    ("perishable-risk", r"(fresh-baked|cream-based|perishable|fresh or frozen|core line is refrigerated)"),
    ("under-floor", r"(under the \$500k|below the \$500k|below the \$?500k|under \$500k|very small|very early stage|"
                    r"market-stall)"),
    ("alcohol-adjacent", r"(trace amounts of alcohol|alcohol-adjacent|wine-adjacent|beer-adjacent|na cocktail|"
                         r"cocktail positioning|spirits|check alcohol)"),
    ("format", r"(share-size|share size|share bags|share packs|not single-serve|no single-serve|not individually|"
               r"single-serve format not|single-serve sku not|multi-serve|128 oz|8 oz pouches|bag size not)"),
    # review round 1 (R1-16): functional-ingredient and implied-effect wording needs the founder's decision before
    # outreach; nutrient-content wording ('5g protein', 'low sugar') is allowed by CONTRACTS section 4 and only
    # constrains copy, so it is information, not a block
    ("claim-functional", r"(adaptogen|prebiotic|probiotic|glp-1|nootropic|mushroom|gut-friendly|gut friendly|"
                         r"energy-boosting|boost of energy|steady energy|energy positioning|natural energy|energy lines?\b|"
                         r"functional (?:ingredient|line|chocolate|blend)|claims review|labels? for claims|"
                         r"dental health|healthy pick-me-up)"),
    ("nutrient-claim", r"(claim|protein|sugar|keto|superfood|antioxidant|wellness|health|nourish|fiber|electrolyte|"
                       r"caffeine|functional|energy)"),
]
# founder-review types that must be cleared (founder_review_cleared = Y) before a row can be queued; the others
# are notes for copy and intake
BLOCKING_TYPES = {"owner", "scale-reported", "scale", "not-emerging", "dormant", "perishable-risk",
                  "alcohol-adjacent", "format", "claim-functional"}
# information only (read on the Founder review tab or at intake): nutrient-claim, under-floor, other,
# format-unconfirmed (single-serve not shown; the first call asks), and the shelf-life and store-only notes
NAME_IN_DATA = re.compile(r"\bDesk Drop\b")  # CONTRACTS rename rule: the working name never sits in a data cell


# Stage 3 (outbound critique after spot check round 8): the scale rules above read only the researcher's
# founder-review reason, so a scale signal written into the why-now ("in 9,000+ US stores", a Series B,
# Costco) earned no penalty. These read the why-now as well. Threshold (assumption): 4,000 or more doors or
# stores, a Series B or later, or Costco = 'scale' (-12, as in stage 1); a national Target or Walmart launch
# below that is a founder-review note with no penalty.
WHY_SCALE = re.compile(r"(\b(?:[4-9]|\d{2}),\d{3}\+?\s*(?:US |U\.S\. )?(?:retail )?(?:doors|stores|locations)|"
                       r"nearly [4-9],\d{3} doors|\bSeries [B-Z]\b|\bcostco\b)", re.I)
WHY_NATIONAL = re.compile(r"(nationwide at (?:Target|Walmart|Kroger)|Target nationwide|\bWalmart\b|"
                          r"\b\d,\d{3}\+?\s*(?:US )?(?:retail )?(?:doors|stores))", re.I)


def review_severity(reason, funding, website, revenue_band):
    t = f"{reason} || {funding} || {website}".lower()
    sev = [k for k, pat in SEV_RULES if re.search(pat, t)]
    if revenue_band == "over-10m":
        sev.insert(0, "scale-reported")
    return sev


# ------------------------------------------------------------------ contacts
NONPERSON = re.compile(r"\b(family|team|brothers|sisters|founders|couple|owners|partners|company|unknown|"
                       r"husband|wife|mother|daughter|son|staff)\b", re.I)
ROLEWORD = re.compile(r"\b(director|marketing|vp|ceo|coo|cmo|founder|co-founder|president|manager|head|per|since|"
                      r"linkedin|profile|lead|chief|officer|post|about|months|old|joining|surname|name|page|site)\b", re.I)
PARTICLES = {"van", "de", "der", "den", "da", "di", "la", "le", "von", "bin", "al", "del", "dos"}


def looks_like_name(p):
    w = p.split()
    if not (1 <= len(w) <= 4) or NONPERSON.search(p) or ROLEWORD.search(p) or re.search(r"\d", p):
        return False
    return all((x[0].isupper() or x.lower() in PARTICLES) for x in w)


def split_people(s):
    """Names in a researcher's cell, in order. Parenthetical notes are kept as the note;
    words that are not a person's name (a family, a role, a phrase) are dropped."""
    s = (s or "").strip()
    if not s or s.lower().startswith("unknown") or s.lower() in ("none", "n/a"):
        return []
    s = re.sub(r"^first names? only:?\s*", "", s, flags=re.I)
    note = " ".join(re.findall(r"\(([^)]*)\)", s))
    core = re.sub(r"\([^)]*\)", "", s)
    parts = re.split(r";|\band\b|&|,|\.\s+|\bAlso\b", core)
    people = []
    for p in parts:
        p = p.strip(" .'\"")
        if p and looks_like_name(p) and p not in [x for x, _ in people]:
            people.append((p, note))
    return people


def person_status(name, note, title, snippet_fields, field):
    """Whether the NAME is supported by an opened page. Doubt about a title only (for example
    'CEO title seen only in a snippet') does not make the name unverified (spot check round 3)."""
    t = f"{name} {note}".lower()
    if "unverified" in t or "snippet" in t or "founder to confirm" in t or field in snippet_fields:
        return "unverified"
    if len(name.split()) == 1:
        return "first-name-only"
    return "verified-page"


def clean_title(t, default):
    t = (t or "").strip()
    if not t or t.lower().startswith("unknown"):
        return default
    t = re.split(r"\s*\(", t)[0].strip() or default
    # one person per contact slot: 'Co-founders' -> 'Co-founder', 'Owners' -> 'Owner'
    t = re.sub(r"\b(Co-founder|Founder|Owner|Cofounder|Co-Founder)s\b", r"\1", t)
    return t


def title_for(person, raw, default):
    """A title cell may hold one title for everyone, or 'Name: Title; Name2, Title2' segments."""
    segs = [x.strip() for x in re.split(r";", raw or "") if x.strip()]
    if len(segs) > 1 or re.match(r"^[A-Z][a-z]+ [A-Z][\w'-]+[:,] ", raw or ""):
        first = person.split()[0].lower()
        for sg in segs:
            m = re.match(r"^([^:,]+)[:,]\s*(.+)$", sg)
            if m and (m.group(1).strip().lower() == person.lower() or m.group(1).strip().lower().split()[0] == first):
                return clean_title(m.group(2), default)
        # a segment for someone else only: do not borrow their title
        if all(re.match(r"^[A-Z][^:,]+[:,]", sg) for sg in segs):
            return default
    return clean_title(raw, default)


# ------------------------------------------------------------------ main
def main():
    b = load()
    n_in = len(b)
    # dedupe on normalized name and domain
    b["_nn"] = b.brand.map(norm_name)
    b["_dom"] = b.website.map(norm_domain)
    seen, keep, dups, name_only = {}, [], [], []
    for i, r in b.iterrows():
        hit = seen.get(("d", r._dom)) if r._dom else None
        if hit is None and ("n", r._nn) in seen:
            j = seen[("n", r._nn)]
            # same normalized name: a duplicate only when one side has no domain
            if not r._dom or not b.at[j, "_dom"]:
                hit = j
            else:
                name_only.append((r.brand, r._dom, b.at[j, "brand"], b.at[j, "_dom"]))
        if hit is not None:
            dups.append((r.brand, r.research_slice, b.at[hit, "brand"], b.at[hit, "research_slice"]))
            continue
        seen.setdefault(("n", r._nn), i)
        if r._dom:
            seen[("d", r._dom)] = i
        keep.append(i)
    print("same normalized name, different domains (kept as two brands):", name_only)
    b = b.loc[keep].reset_index(drop=True)
    reg = C.load_registry(REG_PATH)
    nxt = max([int(v[3:]) for v in reg.values()] + [0]) + 1

    links = []
    out = []
    rc_path = os.path.join(C.WORK, "wfm_recheck_2026-10-24.csv")
    recheck = {}
    if os.path.exists(rc_path):
        for x in pd.read_csv(rc_path, dtype=str, keep_default_na=False).to_dict("records"):
            recheck[(x["brand"], x["store"])] = x
    for r in b.to_dict("records"):
        key = r["_dom"] or r["_nn"]
        if key not in reg:
            reg[key] = f"AB-{nxt:03d}"
            nxt += 1
        o = {"row_id": reg[key], "company": r["brand"]}
        for c in ("website", "hq_city", "hq_state", "category", "product_example", "individually_packaged",
                  "shelf_stable", "shelf_stable_basis", "online_store", "online_store_url", "revenue_band",
                  "revenue_basis", "funding_stage", "funding_source_url", "retailers_claimed",
                  "retailer_evidence_urls", "health_claim_flag", "founder_review", "founder_review_reason",
                  "startup_cpg_member", "startup_cpg_evidence_url", "instagram_url", "source_url", "found_date",
                  "research_slice", "slice_row", "notes", "enrichment_log"):
            o[c] = r.get(c, "")
        o["research_excluded"] = r["excluded"]
        o["research_exclusion_reason"] = r["exclusion_reason"]
        # normalize enrichment values that carry a parenthetical
        for c in ("shelf_stable", "online_store", "individually_packaged"):
            v = o[c]
            m = re.match(r"^(Y|N|likely|unknown)\b\s*(.*)$", v)
            if m:
                o[c] = m.group(1)
                if m.group(2) and c == "shelf_stable":
                    o["shelf_stable_basis"] = (o["shelf_stable_basis"] + " | " if o["shelf_stable_basis"] else "") + m.group(2).strip("() ")
        rv = o["revenue_band"]
        o["revenue_band_type"] = ""
        if rv.startswith(("under-500k", "500k-10m", "over-10m")):
            o["revenue_band"] = rv.split()[0]
            o["revenue_band_type"] = "reported"
        elif "projection" in rv:
            o["revenue_basis"] = (o["revenue_basis"] + " | " if o["revenue_basis"] else "") + rv
            o["revenue_band"] = "500k-10m"
            o["revenue_band_type"] = "company projection, not actuals"
        elif "500k since launch" in rv:
            o["revenue_basis"] = (o["revenue_basis"] + " | " if o["revenue_basis"] else "") + rv
            o["revenue_band"] = "500k-10m"
            o["revenue_band_type"] = "press quote, cumulative since launch (edge of band)"
        else:
            o["revenue_band"] = "unknown"
        if o["revenue_band"] == "unknown" and not o["revenue_basis"]:
            o["revenue_basis"] = "unknown"
        if "Tierra Farm" in o["company"] and o["revenue_band"] == "over-10m":
            o["revenue_band_type"] = "press quote from 2021 (over 24 months old)"

        # ---------------- stores and the ten-block test
        stores = parse_store_list(r["nyc_retailers_near_cluster"])
        ns = r["nearest_stocked_retailer"]
        if ns and not ns.lower().startswith(("unknown", "none")):
            st = parse_store_list(ns + f" ({r['nearest_retailer_grade'] or 'unverified'})")
            for s in st:
                if not any(norm_addr(s["addr"]) == norm_addr(x["addr"]) and s["addr"] for x in stores) and \
                        not any(s["name"] == x["name"] for x in stores):
                    s["raw"] = ns
                    stores.append(s)
        graded = []
        for s in stores:
            g, gnote = regrade(s, r["notes"])
            rc = recheck.get((r["brand"], s["name"]))
            if g == "store_selector" and rc is not None and rc["found_2026_10_24"] == "N":
                g = "unverified"
                gnote = ("the store's own catalog listed the brand on 2026-10-23 but not in the 2026-10-24 "
                         "re-check; catalogs change daily (founder to check the shelf)")
            elif g == "store_selector" and rc is not None and rc["found_2026_10_24"] == "Y":
                gnote = (gnote + "; " if gnote else "") + "re-confirmed in the store catalog 2026-10-24"
            bo, ins, how = locate(s["name"], s["addr"])
            within = bo is not None and bo <= 10
            links.append(dict(row_id=o["row_id"], brand=o["company"], store=s["name"], street=s["addr"],
                              research_grade=s["grade"], grade=g, grade_note=gnote, blocks_outside=bo if bo is not None else "",
                              inside_boundary="Y" if (bo == 0) else ("N" if bo is not None else "unknown"),
                              within_ten_blocks="Y" if within else "N", placed_by=how, raw=s["raw"]))
            graded.append((s, g, bo, within))
        near = [x for x in graded if x[3] and x[1] in ("store_selector", "brand_claim")]
        near.sort(key=lambda x: (0 if x[1] == "store_selector" else 1, x[2], x[0]["name"]))
        unv = [x for x in graded if x[3] and x[1] == "unverified"]
        unv.sort(key=lambda x: (x[2], x[0]["name"]))
        if near:
            s, g, bo, _ = near[0]
            o["nearest_stocked_retailer"] = f"{s['name']}, {s['addr']}"
            o["nearest_retailer_grade"] = g
            o["nearest_retailer_blocks_outside"] = bo
            o["nearest_retailer_inside_cluster"] = "Y" if bo == 0 else "N"
        elif unv:
            s, g, bo, _ = unv[0]
            o["nearest_stocked_retailer"] = f"{s['name']}, {s['addr']}"
            o["nearest_retailer_grade"] = "unverified"
            o["nearest_retailer_blocks_outside"] = bo
            o["nearest_retailer_inside_cluster"] = "Y" if bo == 0 else "N"
        else:
            o["nearest_stocked_retailer"] = "none found within ten blocks"
            o["nearest_retailer_grade"] = "unverified"
            o["nearest_retailer_blocks_outside"] = ""
            o["nearest_retailer_inside_cluster"] = "N"
        o["retailers_within_ten_blocks"] = ";".join(
            f"{x[0]['name']}, {x[0]['addr']} ({x[1]}, {('inside' if x[2] == 0 else str(x[2]) + ' blocks out')})"
            for x in sorted([x for x in graded if x[3]], key=lambda x: (x[2], x[0]["name"])))
        o["graded_retailer_count_within_ten"] = len(near)
        o["stores_beyond_ten_or_unplaced"] = ";".join(
            f"{x[0]['name']} ({x[1]}, {('unplaced' if x[2] is None else str(x[2]) + ' blocks out')})"
            for x in graded if not x[3])

        # ---------------- gates
        fails = []
        ex_reason = r["exclusion_reason"]
        text = (ex_reason + " " + r["founder_review_reason"]).lower()
        if r["excluded"] == "Y":
            el = ex_reason.lower()
            if re.search(r"alcohol|abv|cannabis|hemp|cbd|thc|supplement|multivitamin|creatine|needs preparation|"
                         r"to brew|to whisk|baking mix|drink-mix|cocktail mixer|concentrate", el):
                fails.append(("excluded-category", ex_reason))
            if re.search(r"claim|structure|function|health|immun|gut|detox|cognitive|wellness|focus|brain|"
                         r"metabolism|digest|bloat", el) and not re.search(r"^refrigerated|frozen", el):
                fails.append(("health-claim", ex_reason))
            if re.search(r"refrigerat|frozen|fridge|shelf life \d+ weeks|2 weeks|perishable|fresh|cold-pressed", el) \
                    or o["shelf_stable"] == "N":
                fails.append(("not-shelf-stable", ex_reason if re.search(r"refrigerat|frozen|fridge|weeks|fresh|cold", el)
                              else o["shelf_stable_basis"]))
            if re.search(r"no working online store|no retailer", el):
                fails.append(("no-buy-path", ex_reason))
            if not fails:
                fails.append(("excluded-category", ex_reason))
        elif o["shelf_stable"] == "N":
            fails.append(("not-shelf-stable", o["shelf_stable_basis"]))
        if o["online_store"] != "Y" and not near and not any(f[0] == "no-buy-path" for f in fails):
            fails.append(("no-buy-path", "no graded store within ten blocks and no online store shown"
                          + (" (online store unknown)" if o["online_store"] == "unknown" else "")))
        o["gate_result"] = "pass" if not fails else "fail"
        o["gate_failed"] = ";".join(dict.fromkeys(f[0] for f in fails))
        o["gate_reason"] = " | ".join(f"{f[0]}: {f[1]}" for f in fails) if fails else "passes all hard gates"

        # ---------------- founder review (carried) plus re-grade and gate notes
        sev = review_severity(r["founder_review_reason"], r["funding_stage"], r["website"], o["revenue_band"])
        if r["founder_review"] == "Y" and not sev:
            sev = ["other"]
        fr_add = []
        wn = r["why_now"] or ""
        ms, mn = WHY_SCALE.search(wn), WHY_NATIONAL.search(wn)
        if ms and not {"scale", "scale-reported"} & set(sev):
            sev = [x for x in sev if x != "other"] + ["scale"]
            fr_add.append(f"scale signal in the why-now ('{ms.group(0)}'): likely above the $10M band; ask at intake")
        elif mn and not {"scale", "scale-reported"} & set(sev):
            fr_add.append(f"national retail distribution in the why-now ('{mn.group(0)}'): check the revenue band at intake")
        if o["individually_packaged"] == "N" and "format" not in sev:
            # review round 1 (R1-16): individually packaged is one of the seven qualifiers
            sev = [x for x in sev if x != "other"] + ["format"]
            fr_add.append("no individually packaged single-serve SKU on the pages read (check for one before outreach)")
        elif o["individually_packaged"] == "unknown" and "format" not in sev:
            sev = sev + ["format-unconfirmed"]
            fr_add.append("single-serve pack not shown on the pages read: ask on the first call")
        o["founder_review_type"] = ";".join(sev)
        if o["shelf_stable"] in ("likely", "unknown"):
            fr_add.append("60-day shelf life not stated")
        if o["online_store"] != "Y" and near:
            fr_add.append("no online store: buy path is the store only")
        if fr_add or r["founder_review"] == "Y":
            o["founder_review"] = "Y"
        else:
            o["founder_review"] = "N"
        o["founder_review_reason"] = NAME_IN_DATA.sub("the office drop",
                                                     "; ".join(x for x in [r["founder_review_reason"]] + fr_add if x))
        o["review_blocking"] = "Y" if (o["founder_review"] == "Y" and set(sev) & BLOCKING_TYPES) else "N"

        # ---------------- why-now
        o["why_now"], o["why_now_url"], o["why_now_date"] = r["why_now"], r["why_now_url"], r["why_now_date"]
        if o["why_now"].lower().startswith(("none", "unknown")):
            o["why_now"], o["why_now_url"], o["why_now_date"] = "", "", ""
        if o["why_now_url"] == "unknown":
            o["why_now_url"] = ""
        if o["why_now_date"] == "unknown":
            o["why_now_date"] = ""
        # review round 1 (R1-14): a why-now is a dated, linked fact or nothing; the rest goes to notes
        wd = o["why_now_date"]
        mwd = re.match(r"^(\d{4}-\d{2}(?:-\d{2})?)\s*\(([^)]*)\)\s*$", wd)
        if mwd:
            o["why_now_date"] = mwd.group(1)
            o["why_now"] = (o["why_now"] + f" ({mwd.group(2)})").strip()
        if o["why_now"] and (not o["why_now_url"].startswith("http") or
                             not re.match(r"^\d{4}-\d{2}(?:-\d{2})?$", o["why_now_date"]) or
                             re.search(r"unverified|snippet|not opened", o["why_now"], re.I)):
            o["notes"] = (o["notes"] + " | " if o["notes"] else "") + (
                f"Why-now without an opened link and a date, kept as a note only: {o['why_now']} "
                f"(url: {o['why_now_url'] or 'none'}; date: {o['why_now_date'] or 'none'})")
            o["why_now"], o["why_now_url"], o["why_now_date"] = "", "", ""
        kind, age, win = why_now_class(o["why_now"], o["why_now_url"], o["why_now_date"], r["notes"], o["website"])
        o["why_now_type"] = kind
        o["why_now_age_days"] = age if age is not None else ""
        if kind == "stale":
            o["why_now_type"] = "stale (over 12 months)"

        # ---------------- contacts
        snip = r["enrich_snippet_fields"]
        es = json.loads(r["_esrc"])

        def src_for(name_field, url_field):
            """The page that supports the name: the enrichment source of the name if the name was
            enriched from an opened page, else the researcher's profile URL as first recorded."""
            if name_field in es and es[name_field][1] == "opened" and es[name_field][0]:
                return es[name_field][0]
            if url_field in es and es[url_field][1] != "opened":
                return r["_orig_" + url_field]
            return r[url_field]

        def li_for(url_field):
            u = r[url_field] or ""
            if "linkedin.com/in/" not in u:
                return "", ""
            how = "search result, not opened" if (url_field in es and es[url_field][1] != "opened") else \
                "listed on a page the researcher opened; LinkedIn not opened"
            return u, how
        fpeople = split_people(r["founder_name"])
        mpeople = split_people(r["marketing_name"])
        ftitle = clean_title(r["founder_title"], "Founder (exact title not stated)")
        mtitle = clean_title(r["marketing_title"], "unknown")
        prim, back = None, None
        if fpeople:
            n, note = fpeople[0]
            prim = dict(name=n, title=title_for(n, r["founder_title"], "Founder (exact title not stated)"),
                        url=src_for("founder_name", "founder_profile_url"), note=note,
                        li=li_for("founder_profile_url"),
                        status=person_status(n, note, r["founder_title"], snip, "founder_name"), role="founder")
            mp = [p for p in mpeople if p[0] != n]
            if mpeople and not mp:
                prim["role"] = "founder and marketing lead"
            if mp:
                n2, note2 = mp[0]
                back = dict(name=n2, title=title_for(n2, r["marketing_title"], "unknown"),
                            url=src_for("marketing_name", "marketing_profile_url"), note=note2,
                            li=li_for("marketing_profile_url"),
                            status=person_status(n2, note2, r["marketing_title"], snip, "marketing_name"), role="marketing")
            elif len(fpeople) > 1:
                n2, note2 = fpeople[1]
                back = dict(name=n2, title=title_for(n2, r["founder_title"], "Co-founder (exact title not stated)"),
                            url=src_for("founder_name", "founder_profile_url"), note=note2,
                            li=("", ""),
                            status=person_status(n2, note2, r["founder_title"], snip, "founder_name"), role="co-founder")
        elif mpeople:
            n, note = mpeople[0]
            prim = dict(name=n, title=title_for(n, r["marketing_title"], "unknown"),
                        url=src_for("marketing_name", "marketing_profile_url"), note=note,
                        li=li_for("marketing_profile_url"),
                        status=person_status(n, note, r["marketing_title"], snip, "marketing_name"), role="marketing")
        for pre, p in (("", prim), ("backup_", back)):
            if p:
                note = p.get("note", "")
                ms = re.search(r"spelled '([^']+)' on (?:the )?brand page", note)
                if ms:
                    p["name"] = " ".join(p["name"].split()[:-1] + [ms.group(1)])
                u = p["url"] if p["url"] and p["url"] != "unknown" else ""
                if "linkedin.com" in u and p["status"] in ("verified-page", "first-name-only"):
                    p["status"] = "unverified"  # the only page for this name is LinkedIn, never opened
                parts = p["name"].split()
                ok = p["status"] in ("verified-page", "first-name-only")
                o[pre + "contact_name_as_found"] = p["name"]
                o[pre + "first_name"] = parts[0] if ok else ""
                o[pre + "last_name"] = (" ".join(parts[1:]) if len(parts) > 1 else "unknown") if ok else ""
                o[pre + "title"] = p["title"] if ok else ""
                o[pre + "contact_role"] = p["role"]
                o[pre + "contact_note"] = p.get("note", "")
                o[pre + "contact_status"] = p["status"]
                o[pre + "contact_profile_url"] = "" if "linkedin.com" in u else u
                li, how = p.get("li", ("", ""))
                o[pre + ("contact_linkedin_url" if pre == "" else "linkedin_url")] = li
                o[pre + "linkedin_status"] = how
            else:
                for c in ("contact_name_as_found", "first_name", "last_name", "title", "contact_role",
                          "contact_profile_url", "contact_note"):
                    o[pre + c] = ""
                o[pre + "contact_status"] = "none"
                o[pre + ("contact_linkedin_url" if pre == "" else "linkedin_url")] = ""
                o[pre + "linkedin_status"] = ""
        o["work_email"] = ""
        o["email_status"] = "none"
        o["backup_work_email"] = ""
        o["backup_email_status"] = "none"
        o["channel"] = "linkedin"
        o["onsite_band"] = ""
        o["known_to_founder"] = "N"
        o["do_not_contact"] = "N"
        o["status"] = "new"
        o["startup_cpg_member"] = "Y" if o["startup_cpg_member"] == "Y" else "unknown"

        # ---------------- score
        pts = {}
        if near:
            g, bo = near[0][1], near[0][2]
            pts["buy"] = K.B_BUY_PATH[(g, "inside" if bo == 0 else "near")]
            buy_txt = f"{'store page' if g == 'store_selector' else 'brand locator'} shows {near[0][0]['name']}" + \
                      (" inside the cluster" if bo == 0 else f" {bo} blocks outside it")
        elif o["online_store"] == "Y":
            pts["buy"] = K.B_BUY_PATH[("online", None)]
            buy_txt = "no graded store within ten blocks, online store only"
        else:
            pts["buy"] = 0
            buy_txt = "no buy path shown"
        cls, unver = ny_class(o["hq_city"], o["hq_state"])
        o["hq_class"] = cls + (" (unverified)" if unver else "")
        pts["ny"] = K.B_NY[cls] + (K.B_NY_UNVERIFIED_PENALTY if unver and cls in ("nyc", "nys") else 0)
        wk = "none" if kind in ("none", "stale", "unverified") else kind
        pts["why"] = K.B_WHY_NOW[(wk, win)] if wk != "none" else 0
        pts["rev"] = K.B_REVENUE[o["revenue_band"]]
        pts["fit"] = (K.B_FIT["shelf"].get(o["shelf_stable"], 0) + K.B_FIT["single"].get(o["individually_packaged"], 0)
                      + K.B_FIT["online"].get(o["online_store"], 0))
        c = 0
        if prim:
            c += K.B_CONTACT["founder_full"] if prim["status"] == "verified-page" else (
                K.B_CONTACT["founder_partial"] if prim["status"] in ("first-name-only", "unverified") else 0)
        if (back and back["role"] == "marketing") or (prim and prim["role"] == "marketing"):
            c += K.B_CONTACT["marketing"]
        pts["contact"] = min(10, c)
        pts["known"] = K.B_KNOWN if o["known_to_founder"] == "Y" else 0
        pen = 0
        if o["founder_review"] == "Y":
            pen = min([K.B_REVIEW_PENALTY.get(x, K.B_REVIEW_PENALTY["other"]) for x in sev] or [0])
        pts["review"] = pen
        total = sum(pts.values())
        o["score_raw"] = total
        o["score"] = total if o["gate_result"] == "pass" else 0
        for k2, v in pts.items():
            o["score_" + k2] = v
        o["score_reason"] = brand_reason(o, buy_txt, cls, unver, kind, age, sev)
        out.append(o)

    C.save_registry(REG_PATH, reg)
    df = pd.DataFrame(out)
    df["_g"] = df.nearest_retailer_grade.map({"store_selector": 0, "brand_claim": 1}).fillna(2)
    df = df.sort_values(["gate_result", "score", "_g", "score_why", "company"],
                        ascending=[False, False, True, False, True]).reset_index(drop=True)
    ranks, k = [], 0
    for ok in df.gate_result == "pass":
        if ok:
            k += 1
            ranks.append(str(k))
        else:
            ranks.append("")
    df["rank"] = ranks
    df["top60"] = ["Y" if (x != "" and int(x) <= 60) else "N" for x in ranks]
    df = df.drop(columns=["_g"])
    for c in ("notes", "founder_review_reason", "why_now", "product_example"):
        df[c] = df[c].map(lambda v: NAME_IN_DATA.sub("the office drop", v))
    lead = STABLE + ["rank", "top60", "gate_result", "gate_failed", "gate_reason", "founder_review",
                     "founder_review_type", "review_blocking", "founder_review_reason", "website", "hq_city", "hq_state", "hq_class",
                     "category", "product_example", "funding_stage", "funding_source_url", "shelf_stable",
                     "shelf_stable_basis", "individually_packaged", "online_store", "online_store_url",
                     "revenue_band", "revenue_band_type", "revenue_basis", "health_claim_flag",
                     "research_excluded", "research_exclusion_reason",
                     "nearest_retailer_blocks_outside", "nearest_retailer_inside_cluster",
                     "graded_retailer_count_within_ten", "retailers_within_ten_blocks",
                     "stores_beyond_ten_or_unplaced", "retailers_claimed", "retailer_evidence_urls",
                     "why_now_type", "why_now_age_days", "startup_cpg_evidence_url",
                     "contact_name_as_found", "contact_role", "contact_status", "contact_profile_url", "contact_note", "linkedin_status",
                     "backup_contact_name_as_found", "backup_first_name", "backup_last_name", "backup_title",
                     "backup_contact_role", "backup_contact_status", "backup_contact_profile_url", "backup_contact_note",
                     "backup_linkedin_url", "backup_linkedin_status", "backup_work_email", "backup_email_status",
                     "score_raw", "score_buy", "score_ny", "score_why", "score_rev", "score_fit", "score_contact",
                     "score_known", "score_review", "instagram_url", "research_slice", "slice_row", "notes",
                     "enrichment_log"]
    df = df[lead]
    df.to_csv(os.path.join(C.WORK, "stage1_brands.csv"), index=False)  # stage 3 merges contacts into brands.csv
    pd.DataFrame(links).to_csv(os.path.join(C.WORK, "brand_store_links.csv"), index=False)
    top = df[df.top60 == "Y"]
    top_cols = ["rank", "row_id", "company", "score", "score_reason", "category", "hq_city", "hq_class",
                "nearest_stocked_retailer", "nearest_retailer_grade", "why_now", "why_now_url", "why_now_date",
                "founder_review", "founder_review_reason", "website", "first_name", "last_name", "title",
                "contact_linkedin_url", "contact_profile_url", "work_email", "email_status", "channel",
                "backup_first_name", "backup_last_name", "backup_title", "backup_linkedin_url",
                "startup_cpg_member", "known_to_founder", "do_not_contact", "status", "source_url", "found_date"]
    top[top_cols].to_csv(os.path.join(C.WORK, "top60_brands.csv"), index=False)
    print("input rows", n_in, "after dedupe", len(df), "dups", dups)
    print("passed", (df.gate_result == "pass").sum(), "top60", len(top))
    print(df.gate_failed.value_counts().to_string())


def brand_reason(o, buy_txt, cls, unver, kind, age, sev):
    if o["gate_result"] != "pass":
        return C.one_sentence("Gated out: " + o["gate_reason"].split(" | ")[0][:160])
    where = {"nyc": "New York City brand", "nys": "New York State brand", "northeast": "Northeast brand",
             "elsewhere": "brand based outside the Northeast", "unknown": "HQ unknown"}[cls]
    if unver:
        where += " (HQ unverified)"
    if kind in ("press", "listing"):
        wn = f"{'news' if kind == 'press' else 'a new store listing'} {age} days ago"
    else:
        wn = "no dated why-now in the last 12 months"
    rv = {"500k-10m": "revenue in band", "unknown": "revenue unknown", "under-500k": "revenue under $500k",
          "over-10m": "revenue over $10M"}[o["revenue_band"]]
    rev = f"; founder review: {', '.join(sev)}" if (o["founder_review"] == "Y" and sev) else (
        "; founder review: shelf life not stated" if o["founder_review"] == "Y" else "")
    who = "contact named" if o["contact_status"] in ("verified-page", "first-name-only") else (
        "contact unverified" if o["contact_status"] == "unverified" else "no contact named")
    return C.one_sentence(f"{where}, {buy_txt}, {wn}, {rv}, {who}{rev}")


if __name__ == "__main__":
    main()
