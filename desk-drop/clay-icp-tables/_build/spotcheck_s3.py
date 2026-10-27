#!/usr/bin/env python3
"""Stage 3 spot-check helper: draw ten random rows per table from the top lists, re-open every source each
row cites, and print the evidence field by field for a human verdict.

    python3 -B spotcheck_s3.py sample r6 20261101      # writes _work/spotcheck_r6_{offices,brands}_sample.csv
    python3 -B spotcheck_s3.py evidence r6             # opens every source, writes _work/spotcheck_r6_evidence.txt

Pages are saved gzipped under _work/fetch/spotcheck/<round>/ (file name: first 12 hex of the URL's MD5).
LinkedIn and sec.gov are never opened (CONTRACTS privacy rule; EDGAR demands a contact email). Generic
User-Agent, one request at a time, no personal identifier in any request.
"""
import gzip
import hashlib
import html
import json
import math
import os
import random
import re
import subprocess
import sys
import time
import urllib.parse

import pandas as pd

import common as C
import recheck_wfm as W

FIELDS_OFF = ["address", "in_cluster", "headcount", "attendance", "gate", "contact", "contact_title",
              "backup", "title_match", "why_now"]
FIELDS_BR = ["retailer_grade", "ten_blocks", "shelf_stable", "health_claim_gate", "contact", "contact_title",
             "backup", "why_now", "hq", "online_store"]
CLAIM_WORDS = re.compile(r"(supports? (?:your )?(?:gut|immune|immunity|digest|brain|focus|energy|metabolism|heart)|"
                         r"boosts? (?:your )?(?:immun|energy|metabolism|focus|mood)|gut health|immune support|"
                         r"detox|cognitive|reduces? (?:bloating|stress|anxiety|inflammation)|promotes? "
                         r"(?:healthy|digest|sleep|calm))", re.I)


def page_text(h):
    t = re.sub(r"<script.*?</script>", " ", h, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t)


def fetch(rnd, url):
    if not url or not url.startswith("http"):
        return "no-url", ""
    if "linkedin.com" in url or "sec.gov" in url:
        return "skipped (policy)", ""
    d = os.path.join(C.WORK, "fetch", "spotcheck", rnd)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, hashlib.md5(url.encode()).hexdigest()[:12] + ".html.gz")
    if os.path.exists(p):
        with gzip.open(p, "rt", encoding="utf-8", errors="ignore") as f:
            h = f.read()
        return "cache", h
    tmp = p[:-3]
    r = subprocess.run(["curl", "-sS", "-L", "-m", "35", "-A", "Mozilla/5.0", "-o", tmp, "-w", "%{http_code}", url],
                       capture_output=True, text=True)
    time.sleep(0.4)
    code = r.stdout.strip() or ("ERR " + r.stderr.strip()[:60])
    h = open(tmp, encoding="utf-8", errors="ignore").read() if os.path.exists(tmp) else ""
    if os.path.exists(tmp):
        with gzip.open(p, "wt", encoding="utf-8") as f:
            f.write(h)
        os.remove(tmp)
    return code, h


def snip(h, terms, width=110):
    t = page_text(h)
    out = []
    for term in terms:
        if not term:
            continue
        m = re.search(re.escape(term), t, re.I)
        if m:
            out.append(f"+ '{term}': ...{t[max(0, m.start() - width):m.end() + width]}...")
        else:
            m2 = re.search(re.escape(term), h, re.I)
            out.append(f"~ '{term}' (raw): ...{h[max(0, m2.start() - width):m2.end() + width]}..." if m2 else
                       f"- '{term}': not found")
    return out


def sample(rnd, seed):
    random.seed(int(seed))
    for name, top in (("offices", "top50"), ("brands", "top60")):
        df = pd.read_csv(os.path.join(C.A_DIR, f"{name}.csv"), dtype=str, keep_default_na=False)
        pool = df[df[top] == "Y"]
        prior = set()
        for f in os.listdir(C.WORK):
            m = re.match(rf"spotcheck_(r\d+)_{name}_sample\.csv$", f)
            if m and m.group(1) >= "r6" and m.group(1) != rnd:  # stage 3 rounds only
                prior |= set(pd.read_csv(os.path.join(C.WORK, f), dtype=str).row_id)
        fresh = pool[~pool.row_id.isin(prior)]
        src = fresh if len(fresh) >= 10 else pool
        ids = random.sample(sorted(src.row_id), 10)
        df[df.row_id.isin(ids)].to_csv(os.path.join(C.WORK, f"spotcheck_{rnd}_{name}_sample.csv"), index=False)
        print(name, ids)


def sample_touched(rnd, seed):
    """Review round 1 (round 9 onward): five rows per table that this round changed (new contacts, the space
    check, the claims re-scan) and five others, none drawn in rounds 6 to 8."""
    random.seed(int(seed))
    r9o = pd.read_csv(os.path.join(C.WORK, "contacts_r9_offices.csv"), dtype=str).row_id
    r9b = pd.read_csv(os.path.join(C.WORK, "contacts_r9_brands.csv"), dtype=str).row_id
    for name, top in (("offices", "top50"), ("brands", "top60")):
        df = pd.read_csv(os.path.join(C.A_DIR, f"{name}.csv"), dtype=str, keep_default_na=False)
        pool = df[df[top] == "Y"]
        prior = set()
        for f in os.listdir(C.WORK):
            m = re.match(rf"spotcheck_(r\d+)_{name}_sample\.csv$", f)
            if m and int(m.group(1)[1:]) >= 6 and m.group(1) != rnd:
                prior |= set(pd.read_csv(os.path.join(C.WORK, f), dtype=str).row_id)
        pool = pool[~pool.row_id.isin(prior)]
        if name == "offices":
            touched = pool[pool.row_id.isin(r9o) | (pool.onsite_space_check == "Y")]
        else:
            touched = pool[pool.row_id.isin(r9b) | pool.founder_review_reason.str.contains("Claims review")
                           | (pool.founder_review_type.str.contains("format"))]
        a = random.sample(sorted(touched.row_id), min(5, len(touched)))
        rest = pool[~pool.row_id.isin(a)]
        b = random.sample(sorted(rest.row_id), 10 - len(a))
        ids = a + b
        df[df.row_id.isin(ids)].to_csv(os.path.join(C.WORK, f"spotcheck_{rnd}_{name}_sample.csv"), index=False)
        print(name, "touched", a, "other", b)


def claims_fresh(rnd, website):
    """The R1-01 gate check, re-opened: homepage, Shopify catalog, About and FAQ, scanned with the gate's patterns."""
    import scan_claims as SC
    base = SC.base_of(website)
    hits = []
    pages = []
    for u in (website, base + "/products.json?limit=250", base + "/pages/about", base + "/pages/faq"):
        code, h = fetch(rnd, u)
        pages.append(f"{code}")
        if not h:
            continue
        if u.endswith("limit=250"):
            prods = SC.products_text(h, base)
            texts = prods or []
        else:
            texts = [(u, SC.text(h))]
        for pu, t in texts:
            d = {}
            SC.scan_text(t, pu, d)
            hits += [f"{v['cls']}: {v['phrase']} @ {v['url'][-50:]}" for v in d.values() if v["cls"] != "nutrient"]
    return pages, sorted(set(hits))[:12]


def first_url(s):
    m = re.search(r"https?://[^\s;|)'\"]+", s or "")
    return m.group(0).rstrip(".,") if m else ""


def log_src(log, field):
    m = re.search(re.escape(field) + r" <- (https?://\S+)", log or "")
    return m.group(1) if m else ""


def street_terms(addr):
    a = addr.split(",")[0]
    m = re.match(r"(\d+)\s+(\S+)", a)
    return [f"{m.group(1)} {m.group(2)}" if m else a, m.group(1) if m else ""]


def wfm_check(brand, store, ev):
    code = next((v for k, v in W.STORES.items() if store.startswith(k)), None)
    if not code:
        return "not a Whole Foods store"
    hits_all = []
    for q in W.queries(ev, brand):
        u = ("https://www.wholefoodsmarket.com/api/search?text=" + urllib.parse.quote(q) + f"&store={code}&limit=60&offset=0")
        r = subprocess.run(["curl", "-sS", "-m", "30", "-A", "Mozilla/5.0", u], capture_output=True, text=True)
        time.sleep(0.6)
        try:
            d = json.loads(r.stdout)
            hits = [x.get("name", "") for x in d.get("results", []) if W.brand_match(brand, x.get("brand", ""))]
        except Exception:
            hits = None
        if hits:
            hits_all += hits
            break
    return f"store {code}: {len(hits_all)} items, e.g. {hits_all[:3]}" if hits_all else f"store {code}: brand NOT found"


def evidence(rnd):
    out = []
    links = pd.read_csv(os.path.join(C.WORK, "brand_store_links.csv"), dtype=str, keep_default_na=False)
    o = pd.read_csv(os.path.join(C.WORK, f"spotcheck_{rnd}_offices_sample.csv"), dtype=str, keep_default_na=False)
    for r in o.to_dict("records"):
        out.append(f"\n=== OFFICE {r['row_id']} {r['company']} (rank {r['rank']}, score {r['score']})")
        out.append(f"address: {r['street_address']} floor {r['floor']} | lease {r['lease_status']} | conf {r['confidence']}")
        name_terms = [w for w in re.findall(r"[A-Za-z0-9]+", r["company"]) if len(w) > 2][:1]
        for lab, u in (("address_source", r["address_source_url"]), ("second_source", r["second_source_url"])):
            code, h = fetch(rnd, u)
            out.append(f"  [{lab} {code}] {u}")
            out += ["     " + s for s in snip(h, street_terms(r["street_address"])[:1] + name_terms)] if h else []
        ins = C.inside(r["lat"], r["lon"])
        g = C.geocode(r["street_address"].split(",")[0] + ", New York, NY")
        dist = ""
        if g:
            dlat = (float(g["lat"]) - float(r["lat"])) * 111000
            dlon = (float(g["lon"]) - float(r["lon"])) * 111000 * math.cos(math.radians(40.74))
            dist = f"{math.hypot(dlat, dlon):.0f} m from the row's pin; geocoder pin inside: {C.inside(g['lat'], g['lon'])}"
        out.append(f"  in_cluster: row pin inside boundary = {ins}; re-geocode: {dist or 'no result'}")
        out.append(f"  headcount: {r['employee_count']} / {r['employee_count_second']} scope {r['headcount_scope']} hq_nyc {r['hq_in_nyc']}")
        code, h = fetch(rnd, r["headcount_source_url"])
        out.append(f"  [headcount_source {code}] {r['headcount_source_url']}")
        if h:
            out += ["     " + s for s in snip(h, [re.sub(r"\D", "", r["employee_count"])[:4] or r["employee_count"], "Employees"])]
        out.append(f"  attendance: {r['attendance_signal']} | {r['attendance_evidence'][:160]}")
        if r["attendance_source_url"] and r["attendance_source_url"] not in (r["headcount_source_url"],):
            code, h = fetch(rnd, r["attendance_source_url"])
            out.append(f"  [attendance_source {code}] {r['attendance_source_url']}")
            if h:
                out += ["     " + s for s in snip(h, ["Typical time on-site", "days", "hybrid", "office"])]
        elif r["attendance_source_url"]:
            out += ["     " + s for s in snip(h, ["Typical time on-site", "days a week", "Hybrid", "In-Office"])] if h else []
        out.append(f"  gate: {r['gate_result']} | onsite {r['onsite_low']}-{r['onsite_high']} band {r['onsite_band']} | {r['onsite_basis'][:400]}")
        if r.get("leased_sf_mentioned"):
            code, h = fetch(rnd, r["address_source_url"])
            sfs = [x.strip() for x in r["leased_sf_mentioned"].split(";")]
            out.append(f"  space: leased_sf {r['leased_sf_mentioned']} | space_check {r.get('onsite_space_check', '')}")
            out += ["     " + s for s in snip(h, [x.replace(' sf', '') for x in sfs])] if h else []
        if r.get("linkedin_company_url", "unknown") not in ("", "unknown"):
            code, h = fetch(rnd, r["website"])
            slug = r["linkedin_company_url"].rstrip("/").split("/")[-1]
            out.append(f"  linkedin_company_url: {r['linkedin_company_url']} | site [{code}] links it: "
                       f"{bool(h) and slug.lower() in h.lower()}")
        out.append(f"  contact: {r['first_name']} {r['last_name']} | {r['title']} | {r['contact_status']} | {r['contact_evidence']} | ny_base {r['contact_ny_base']} | title_match {r['title_match']}")
        code, h = fetch(rnd, r["contact_source_url"])
        out.append(f"  [contact_source {code}] {r['contact_source_url']}")
        if h:
            tw = [w for w in re.findall(r"[A-Za-z]+", r["title"]) if len(w) > 3][:2]
            out += ["     " + s for s in snip(h, [r["last_name"] if r["last_name"] != "unknown" else r["first_name"]] + tw + ["New York"])]
        out.append(f"  backup: {r['backup_first_name']} {r['backup_last_name']} | {r['backup_title']} | {r['backup_contact_status']}")
        if r["backup_contact_source_url"]:
            code, h = fetch(rnd, r["backup_contact_source_url"])
            out.append(f"  [backup_source {code}] {r['backup_contact_source_url']}")
            if h:
                tw = [w for w in re.findall(r"[A-Za-z]+", r["backup_title"]) if len(w) > 3][:2]
                out += ["     " + s for s in snip(h, [r["backup_last_name"] or r["backup_first_name"]] + tw)]
        if r["why_now_url"]:
            code, h = fetch(rnd, r["why_now_url"])
            out.append(f"  why_now: {r['why_now']} ({r['why_now_date']}) [{code}] {r['why_now_url']}")
            if h:
                out += ["     " + s for s in snip(h, name_terms + street_terms(r["street_address"])[:1])]
        else:
            out.append("  why_now: none")
    b = pd.read_csv(os.path.join(C.WORK, f"spotcheck_{rnd}_brands_sample.csv"), dtype=str, keep_default_na=False)
    for r in b.to_dict("records"):
        out.append(f"\n=== BRAND {r['row_id']} {r['company']} (rank {r['rank']}, score {r['score']}) {r['website']}")
        out.append(f"  retailer: {r['nearest_stocked_retailer']} ({r['nearest_retailer_grade']}, {r['nearest_retailer_blocks_outside']} blocks out)")
        st = r["nearest_stocked_retailer"].split(",")[0]
        if r["nearest_retailer_grade"] == "store_selector":
            out.append("  WFM catalog now: " + wfm_check(r["company"], st, r["retailer_evidence_urls"]))
        elif r["nearest_retailer_grade"] == "brand_claim":
            u = first_url(r["retailer_evidence_urls"])
            code, h = fetch(rnd, u)
            out.append(f"  [retailer_evidence {code}] {u}")
            if h:
                out += ["     " + s for s in snip(h, [st, r["nearest_stocked_retailer"].split(",")[-1].strip()[:12]])]
        lk = links[(links.row_id == r["row_id"]) & (links.store == st)]
        if len(lk):
            out.append(f"  ten_blocks: {lk.iloc[0].blocks_outside} blocks, placed by {lk.iloc[0].placed_by}")
        out.append(f"  shelf_stable: {r['shelf_stable']} | {r['shelf_stable_basis'][:200]}")
        u = log_src(r["enrichment_log"], "shelf_stable") or first_url(r["shelf_stable_basis"]) or r["source_url"]
        code, h = fetch(rnd, u)
        out.append(f"  [shelf_source {code}] {u}")
        if h:
            out += ["     " + s for s in snip(h, ["shelf", "refrigerat", "best by"])]
        pages, hits = claims_fresh(rnd, r["website"])
        out.append(f"  health_claim_gate: homepage, catalog, about, faq [{', '.join(pages)}] claim or ingredient "
                   f"phrases: {hits or 'none'} | review_blocking {r.get('review_blocking', '')} | "
                   f"{r['founder_review_type']}")
        out.append(f"  contact: {r['first_name']} {r['last_name']} | {r['title']} | {r['contact_role']} | {r['contact_status']} | {r['contact_evidence']}")
        code, h = fetch(rnd, r["contact_source_url"])
        out.append(f"  [contact_source {code}] {r['contact_source_url']}")
        if h:
            tw = [w for w in re.findall(r"[A-Za-z]+", r["title"]) if len(w) > 3][:2]
            out += ["     " + s for s in snip(h, [r["last_name"] if r["last_name"] != "unknown" else r["first_name"]] + tw)]
        out.append(f"  backup: {r['backup_first_name']} {r['backup_last_name']} | {r['backup_title']} | {r['backup_contact_role']} | {r['backup_contact_status']}")
        if r["backup_contact_source_url"]:
            code, h = fetch(rnd, r["backup_contact_source_url"])
            out.append(f"  [backup_source {code}] {r['backup_contact_source_url']}")
            if h:
                tw = [w for w in re.findall(r"[A-Za-z]+", r["backup_title"]) if len(w) > 3][:2]
                out += ["     " + s for s in snip(h, [r["backup_last_name"] if r["backup_last_name"] not in ("", "unknown") else r["backup_first_name"]] + tw)]
        if r["why_now_url"]:
            code, h = fetch(rnd, r["why_now_url"])
            out.append(f"  why_now: {r['why_now'][:200]} ({r['why_now_date']}, {r['why_now_type']}) [{code}] {r['why_now_url']}")
            if h:
                kw = [w for w in re.findall(r"[A-Za-z]{5,}", r["why_now"])][:2]
                out += ["     " + s for s in snip(h, [r["company"].split(" (")[0]] + kw)]
        else:
            out.append(f"  why_now: none ({r['why_now_type']})")
        u = log_src(r["enrichment_log"], "hq_city")
        out.append(f"  hq: {r['hq_city'][:160]} | {r['hq_state']} | class {r['hq_class']} | source {u or 'research row'}")
        if u:
            code, h = fetch(rnd, u)
            out.append(f"  [hq_source {code}] {u}")
            if h:
                out += ["     " + s for s in snip(h, [re.split(r"[ (,]", r["hq_city"])[0]])]
        if r["online_store_url"]:
            code, h = fetch(rnd, r["online_store_url"])
            ok = bool(h) and bool(re.search(r"add to cart|add-to-cart|cart|checkout|shop now", h, re.I))
            out.append(f"  online_store: {r['online_store']} [{code}] {r['online_store_url']} cart/shop words: {ok}")
        else:
            out.append(f"  online_store: {r['online_store']} (no URL)")
    p = os.path.join(C.WORK, f"spotcheck_{rnd}_evidence.txt")
    open(p, "w").write("\n".join(out))
    print("wrote", p, len(out), "lines")


if __name__ == "__main__":
    if sys.argv[1] == "sample":
        sample(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "sample_touched":
        sample_touched(sys.argv[2], sys.argv[3])
    else:
        evidence(sys.argv[2])
