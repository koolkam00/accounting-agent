#!/usr/bin/env python3
"""Assemble workstream B's master tables from the research slices in _work/.

Writes _build/out/*.pkl-free CSV intermediates (master_*.csv) that export.py turns into
the deliverables. Run from anywhere: python3 _build/assemble.py
"""
import json
import math
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from collections import defaultdict

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)              # cluster-1-flatiron/
DESK = os.path.dirname(ROOT)              # desk-drop/
WORK = os.path.join(ROOT, "_work")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, HERE)

import grid  # noqa: E402
import boundary  # noqa: E402
import frontage  # noqa: E402
import resolutions as R  # noqa: E402

SLICES = ["S1", "S2", "S3", "S4"]
BAND_OK = {"40-75", "76-150", "151-250", "251-500", "unknown"}


def geocode(addr):
    """Project geocoder (cached, rate limited). Run sequentially."""
    out = subprocess.run([sys.executable, os.path.join(DESK, "_shared", "geocode.py"), addr],
                         capture_output=True, text=True, cwd=DESK)
    return json.loads(out.stdout)


def domain(u):
    try:
        d = urllib.parse.urlparse(u).netloc.lower()
    except Exception:
        return ""
    return d[4:] if d.startswith("www.") else d


# ------------------------------------------------------------------ companies
def load_companies():
    fr = []
    for s in SLICES:
        d = pd.read_csv(os.path.join(WORK, f"companies_{s}.csv"), dtype=str).fillna("")
        d["research_slice"] = s
        fr.append(d)
    c = pd.concat(fr, ignore_index=True)
    c["notes_assembly"] = ""
    c["lease_status"] = ""
    c["move_in_date"] = ""
    c["candidate_status"] = ""
    return c


def apply_merges(c):
    for m in R.MERGES:
        keep = c.index[c.company_name == m["keep"]]
        assert len(keep) == 1, m["keep"]
        k = keep[0]
        drops = c.index[c.company_name.isin(m["drop"])]
        assert len(drops) == len(m["drop"]), m["drop"]
        sl = ";".join(sorted(set([c.at[k, "research_slice"]] + list(c.loc[drops, "research_slice"]))))
        for f in ("company_name", "website", "second_source_url", "second_source_date", "confidence",
                  "headcount_band", "headcount_scope", "headcount_source_url", "headcount_source_date"):
            if f in m:
                c.at[k, f] = m[f]
        c.at[k, "research_slice"] = sl
        c.at[k, "notes_assembly"] = m["note"]
        c.at[k, "_merged_from"] = m["keep"] + ";" + ";".join(m["drop"])
        c = c.drop(index=drops)
    return c.reset_index(drop=True)


def apply_overrides(c):
    for name, o in list(R.OVERRIDES.items()) + list(R.REVIEW1_OVERRIDES.items()) + list(R.REVIEW2_OVERRIDES.items()):
        idx = c.index[c.company_name == name]
        assert len(idx) == 1, name
        i = idx[0]
        for f, v in o.items():
            if f == "note_add":
                c.at[i, "notes_assembly"] = (c.at[i, "notes_assembly"] + " " + v).strip()
            else:
                c.at[i, f] = v
    return c


def headcount_updates(c):
    for name, (url, date, note) in R.HEADCOUNT_UPDATES.items():
        idx = c.index[c.company_name == name]
        assert len(idx) == 1, name
        i = idx[0]
        c.at[i, "headcount_band"], c.at[i, "headcount_scope"] = "over-500", "whole-company"
        c.at[i, "headcount_source_url"], c.at[i, "headcount_source_date"] = url, date
        c.at[i, "notes_assembly"] = (c.at[i, "notes_assembly"] + f" Band set at assembly to over-500 from {note} The NYC office size is unknown; the NYC office alone may fit, founder to confirm.").strip()
    return c


def lease_fields(c):
    for i, r in c.iterrows():
        key = r["_merged_from"].split(";")[0] if r.get("_merged_from") else r.company_name
        if r.lease_status:
            continue
        v = R.LEASE.get(key, R.LEASE.get(r.company_name, "occupancy-unconfirmed"))
        if isinstance(v, tuple):
            c.at[i, "lease_status"], c.at[i, "move_in_date"] = v
        else:
            c.at[i, "lease_status"] = v
    # R2-11: move_in_date is YYYY-MM or unknown (blank when occupied); a planned season moves into the notes
    for i, r in c.iterrows():
        v = str(c.at[i, "move_in_date"] or "")
        if v and v != "unknown" and not re.fullmatch(r"\d{4}-\d{2}", v):
            txt = R.MOVE_IN_FREE_TEXT.get(r.company_name, f"Move date given by the row's sources as '{v}'.")
            c.at[i, "move_in_date"] = "unknown"
            c.at[i, "notes_assembly"] = (c.at[i, "notes_assembly"] + " " + txt).strip()
    return c


def audit_confidence(c):
    """Apply the B confidence scale strictly. Downgrades only, each noted.
    Review round 1 (R1-05): an undated third-party profile (Built In, Deskpass, LiquidSpace) counts
    as one current source for medium, but it cannot be the under-24-month source of a high."""
    def fresh(url, date):
        return bool(url) and (date or "") >= R.CUTOFF_24M
    def dated_fresh(url, date):
        return fresh(url, date) and domain(url) not in R.UNDATED_PROFILE_DOMAINS
    for i, r in c.iterrows():
        a_url, a_date = r.address_source_url, r.address_source_date or ""
        b_url, b_date = r.second_source_url, r.second_source_date or ""
        recent = fresh(a_url, a_date) or fresh(b_url, b_date)
        recent_dated = dated_fresh(a_url, a_date) or dated_fresh(b_url, b_date)
        independent = bool(b_url) and domain(b_url) != domain(a_url)
        same_release = "same" in r.notes.lower() and ("announcement" in r.notes.lower() or "release" in r.notes.lower())
        conf = r.confidence
        new = conf
        why = []
        if conf == "high":
            if not recent:
                new = "low"; why.append("no source under 24 months old")
            elif not recent_dated:  # review round 2 (R2-04): an undated profile is never the under-24-month source
                new = "low"; why.append("the only current source is an undated third-party profile (Built In, Deskpass or LiquidSpace), which can only confirm a dated or own-site source")
            elif not independent:
                new = "medium"; why.append("second source is the same publisher or missing")
            elif same_release and r.research_slice.startswith("S1") and r.company_name in ("Selldorf Architects",):
                new = "medium"; why.append("both articles trace to one broker announcement")
        if conf == "medium" and not recent:
            new = "low"; why.append("no source under 24 months old")
        elif conf == "medium" and not recent_dated:  # review round 2 (R2-04)
            new = "low"; why.append("review round 2: the only source dated within 24 months is an undated third-party profile (Built In, Deskpass or LiquidSpace), which can only confirm a dated or own-site source")
        if new != conf:
            c.at[i, "confidence"] = new
            c.at[i, "notes_assembly"] = (c.at[i, "notes_assembly"] + f" Confidence lowered at assembly from {conf} to {new}: {'; '.join(why)}.").strip()
    return c


def note_edits(c):
    """R1-09 and R1-11: rewrite size guesses and the business name out of the notes."""
    for name, edits in R.NOTE_EDITS.items():
        idx = c.index[c.company_name == name]
        assert len(idx) == 1, name
        i = idx[0]
        for old, new in edits:
            hit = False
            for f in ("notes", "notes_assembly"):
                if old in c.at[i, f]:
                    c.at[i, f] = c.at[i, f].replace(old, new); hit = True
            assert hit, (name, old)
    return c


def normalise_company_fields(c):
    """R1-06 and R1-20: an unknown band has an unknown scope; a blank floor or website says unknown;
    SEC-cited rows say the agent will not re-open the source (R1-02)."""
    for i, r in c.iterrows():
        if r.headcount_band == "unknown" and r.headcount_scope != "unknown":
            c.at[i, "notes_assembly"] = (r.notes_assembly + f" Scope set to unknown at review round 1 (was {r.headcount_scope}): the band is unknown.").strip()
            c.at[i, "headcount_scope"] = "unknown"
        for f in ("floor", "website"):
            if not str(r[f]).strip():
                c.at[i, f] = "unknown"
        if any("sec.gov" in str(r[f]) for f in ("address_source_url", "second_source_url", "headcount_source_url")):
            c.at[i, "notes_assembly"] = (c.at[i, "notes_assembly"] + " " + R.SEC_NOTE).strip()
    return c


def hq_fields(c):
    """R1-06: hq_city and hq_in_nyc from each row's Built In offices page (opened 2026-10-24, saved in
    _work/builtin_hq_2026-10-24.csv). Unknown where the row has no Built In page or the page names no HQ."""
    t = pd.read_csv(os.path.join(WORK, "builtin_hq_2026-10-24.csv"), dtype=str).fillna("")
    by = {r.builtin_slug: r for r in t.itertuples()}
    hc, hn, hu = [], [], []
    for _, r in c.iterrows():
        row = None
        for u in (r.headcount_source_url, r.address_source_url, r.second_source_url):
            m = re.search(r"builtinnyc\.com/company/([^/?#]+)", u or "")
            if m and m.group(1) in by:
                row = by[m.group(1)]
                break
        if row is not None and row.hq_city != "unknown":
            hc.append(row.hq_city); hn.append(row.hq_in_nyc); hu.append(row.url)
        else:
            hc.append("unknown"); hn.append("unknown"); hu.append(row.url if row is not None else "")
    c["hq_city"], c["hq_in_nyc"], c["hq_source_url"] = hc, hn, hu
    # R2-07: where Built In is silent, the row's own sources, the company's page or the Revelio page
    for i, r in c.iterrows():
        if r.company_name in R.HQ_R2 and c.at[i, "hq_in_nyc"] == "unknown":
            c.at[i, "hq_city"], c.at[i, "hq_in_nyc"], c.at[i, "hq_source_url"] = R.HQ_R2[r.company_name]
    pc, ps = [], []
    for _, r in c.iterrows():
        p_ = R.PARENT_R2.get(r.company_name)
        pc.append(p_[0] if p_ else "unknown"); ps.append(p_[1] if p_ else "")
    c["parent_company"], c["parent_company_source"] = pc, ps
    return c


BAND_EDGES = [(40, 75, "40-75"), (76, 150, "76-150"), (151, 250, "151-250"), (251, 500, "251-500")]
FIRST_COUNT_RX = [r"([\d][\d,]*)\+?'? total employees", r"'([\d][\d,]*)-person firm'", r"upwards of (\d+) employees",
                  r"(\d[\d,]*) full-time employees", r"about (\d+) employees", r"'?(\d+) employees'?", r"(\d+)-person office"]


def band_of(n):
    if n < 40:
        return "under-40"
    if n > 500:
        return "over-500"
    return next(b for lo, hi, b in BAND_EDGES if lo <= n <= hi)


def first_label(url):
    d = domain(url)
    if "builtin" in d:
        return "Built In"
    if "sec.gov" in d:
        return "the FY2025 10-K"
    if "wikipedia" in d:
        return "Wikipedia"
    if "commercialobserver" in d:
        return "Commercial Observer"
    return "the company's own page"


def headcount_second(c):
    """Review round 2 (R2-02, R2-03): test every sourced band against a second, independent count.
    Same band: kept, headcount_check = agree. Second count over 500 against a third-party first source: the row
    becomes over-500 and goes to Near-miss. Any other disagreement: the band becomes unknown, with both counts."""
    for col in ("headcount_count", "headcount_check", "headcount_second_count", "headcount_second_source_url", "headcount_second_source_date"):
        c[col] = ""
    for i, r in c.iterrows():
        name = r.company_name
        if r.headcount_band not in ("40-75", "76-150", "151-250", "251-500", "under-40"):
            c.at[i, "headcount_check"] = "single-source" if r.headcount_band == "over-500" else "no-count"
            continue
        first = R.HEADCOUNT_FIRST_COUNT.get(name)
        if first is None:
            for rx in FIRST_COUNT_RX:
                m = re.search(rx, r.notes)
                if m:
                    first = int(m.group(1).replace(",", "")); break
        c.at[i, "headcount_count"] = str(first) if first is not None else ""
        sec = R.HEADCOUNT_SECOND.get(name)
        if not sec:
            c.at[i, "headcount_check"] = "single-source"
            continue
        n2 = sec["count"]
        lower_bound = sec["kind"] == "own-site"  # '130+', '150+': at least one more than the figure
        b2 = band_of(n2 + 1 if lower_bound else n2)
        flab = first_label(r.headcount_source_url)
        c.at[i, "headcount_second_count"] = f"{n2}+" if lower_bound else str(n2)
        c.at[i, "headcount_second_source_url"], c.at[i, "headcount_second_source_date"] = sec["url"], sec["date"]
        add = ""
        if name in R.SCOPE_DIFFERS_KEEP:
            c.at[i, "headcount_check"] = "scope-differs"
            add = (f"Review round 2: second count {sec['label']} is whole-company; the band rests on the NYC-office count "
                   f"({first}), so the two are not compared.")
        elif b2 == r.headcount_band:
            c.at[i, "headcount_check"] = "agree"
            add = f"Review round 2: a second count agrees with the band: {sec['label']}."
        elif b2 == "over-500" and name not in R.FIRST_SOURCE_OWN:
            old_b, old_u, old_d = r.headcount_band, r.headcount_source_url, r.headcount_source_date
            c.at[i, "headcount_band"], c.at[i, "headcount_scope"] = "over-500", "whole-company"
            c.at[i, "headcount_source_url"], c.at[i, "headcount_source_date"] = sec["url"], sec["date"]
            c.at[i, "headcount_count"] = str(n2)
            c.at[i, "headcount_second_count"] = str(first) if first is not None else ""
            c.at[i, "headcount_second_source_url"], c.at[i, "headcount_second_source_date"] = old_u, old_d
            c.at[i, "headcount_check"] = "over-500-second-source"
            fit = R.NYC_MAY_FIT_R2.get(name)
            add = (f"Review round 2: band moved from {old_b} to over-500, so the row moves to Near-miss. {sec['label']}. "
                   f"{flab} shows {first} total employees (stale against Revelio; it is now the second source)."
                   + (f" {fit}; the NYC office alone may fit the 40-250 band, founder to confirm." if fit else ""))
        else:
            c.at[i, "headcount_band"], c.at[i, "headcount_scope"] = "unknown", "unknown"
            c.at[i, "headcount_check"] = "disagree"
            reason = (f"Sources disagree: {flab} shows {first} ({r.headcount_band}) and {sec['label']} "
                      f"({b2}). Band left unknown; founder to confirm at intake.")
            R.UNKNOWN_BAND_REASON[name] = reason
            add = f"Review round 2: band changed from {r.headcount_band} to unknown. " + reason
        c.at[i, "notes_assembly"] = (c.at[i, "notes_assembly"] + " " + add).strip()
    return c


# ------------------------------------------------------------------ buildings
def load_buildings():
    fr = []
    for s in SLICES:
        d = pd.read_csv(os.path.join(WORK, f"buildings_{s}.csv"), dtype=str).fillna("")
        d["research_slice"] = s
        fr.append(d)
    return pd.concat(fr, ignore_index=True)


def pluto(bbls):
    bbls = sorted(set(b for b in bbls if b))
    cache = os.path.join(OUT, "pluto_cache.json")
    have = json.load(open(cache)) if os.path.exists(cache) else {}
    need = [b for b in bbls if b not in have]
    for k in range(0, len(need), 60):
        chunk = need[k:k + 60]
        where = "bbl in (" + ",".join(f"'{b}'" for b in chunk) + ")"
        q = urllib.parse.urlencode({
            "$where": where,
            "$select": "bbl,address,latitude,longitude,bldgclass,numfloors,yearbuilt,officearea,bldgarea,zipcode,version",
            "$limit": "5000"})
        url = "https://data.cityofnewyork.us/resource/64uk-42ks.json?" + q
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "cluster-research-script/0.1"}), timeout=60) as f:
            rows = json.load(f)
        for r in rows:
            have[str(int(float(r["bbl"])))] = r
        for b in chunk:
            have.setdefault(b, None)
    json.dump(have, open(cache, "w"), indent=1)
    return have


def norm_addr(a):
    a = a.lower().split(",")[0]
    a = a.replace("avenue of the americas", "sixth avenue").replace("6th avenue", "sixth avenue")
    a = re.sub(r"\b(street|st)\b", "st", a)
    a = re.sub(r"\b(avenue|ave)\b", "ave", a)
    a = re.sub(r"\bsouth\b", "s", a)
    a = re.sub(r"\beast\b", "e", a)
    a = re.sub(r"\bwest\b", "w", a)
    return " ".join(a.split())


def merge_buildings(b, c, pl):
    """One row per bbl (fall back to normalized address)."""
    b = b.copy()
    b["key"] = b.apply(lambda r: r.bbl or ("addr:" + norm_addr(r.street_address)), axis=1)
    rows = []
    lobby_rank = {"security desk": 3, "loading dock": 2, "walk-up": 1, "unknown": 0, "": 0}
    for key, g in b.groupby("key", sort=False):
        addrs = list(dict.fromkeys(g.street_address))
        comp_here = c[c.bbl == key] if not key.startswith("addr:") else c[c.street_address.map(norm_addr) == key[5:]]
        # canonical address: the one most company rows use
        counts = {a: int((comp_here.street_address == a).sum()) for a in addrs}
        canon = max(addrs, key=lambda a: (counts.get(a, 0), -addrs.index(a)))
        names = [n for n in g.building_name if n]
        bname = max(names, key=len) if names else canon
        sourced = g[(g.lobby_type != "unknown") & (g.lobby_type != "") & (g.lobby_source_url != "")]
        if len(sourced):
            types = set(sourced.lobby_type)
            top = max(sourced.itertuples(), key=lambda r: lobby_rank[r.lobby_type])
            lobby, lobby_url = top.lobby_type, top.lobby_source_url
            conflict = len(types) > 1
        else:
            lobby, lobby_url, conflict = "unknown", "", False
        coi_rows = g[g.coi_required.isin(["yes", "no"])]
        coi = coi_rows.coi_required.iloc[0] if len(coi_rows) else "unknown"
        coi_url = coi_rows.coi_source_url.iloc[0] if len(coi_rows) else ""
        notes = " ".join(f"[{r.research_slice}] {r.notes}" for r in g.itertuples() if r.notes)
        for o_, n_ in R.BUILDING_NOTE_EDITS:  # R2-05
            notes = notes.replace(o_, n_)
        if conflict:
            notes = f"Lobby sources differ ({'; '.join(sorted(types))}); the stricter type is shown. " + notes
        gr = g[g.street_address == canon].iloc[0]
        rows.append({
            "bbl": key if not key.startswith("addr:") else "",
            "street_address": canon,
            "also_known_as": "; ".join(a for a in addrs if a != canon),
            "building_name": bname,
            "lat": gr.lat, "lon": gr.lon,
            "lobby_type": lobby, "lobby_source_url": lobby_url,
            "coi_required": coi, "coi_source_url": coi_url,
            "research_slices": ";".join(sorted(set(g.research_slice))),
            "notes_research": notes,
        })
    bb = pd.DataFrame(rows)
    # PLUTO facts
    for i, r in bb.iterrows():
        p = pl.get(r.bbl) if r.bbl else None
        if p:
            bb.at[i, "pluto_address"] = p.get("address", "")
            bb.at[i, "pluto_bldgclass"] = p.get("bldgclass", "")
            bb.at[i, "pluto_numfloors"] = str(int(float(p["numfloors"]))) if p.get("numfloors") else ""
            bb.at[i, "pluto_yearbuilt"] = p.get("yearbuilt", "")
            bb.at[i, "pluto_office_sqft"] = p.get("officearea", "")
            bb.at[i, "zip"] = p.get("zipcode", "")
            if p.get("latitude"):
                bb.at[i, "pluto_lat"] = p["latitude"]
                bb.at[i, "pluto_lon"] = p["longitude"]
    return bb


# ------------------------------------------------------------------ coworking
def floors_of(text):
    """Set of floor numbers named in a floor string; empty if none named."""
    t = (text or "").lower()
    if not t or "unknown" in t or "not named" in t or "not stated" in t:
        nums = set()
    t = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", t)
    out = set()
    for a, b2 in re.findall(r"(\d+)\s*-\s*(\d+)", t):
        a, b2 = int(a), int(b2)
        if b2 >= a and b2 - a < 30:
            out.update(range(a, b2 + 1))
    t2 = re.sub(r"(\d+)\s*-\s*(\d+)", " ", t)
    t2 = re.sub(r"suite\s*\d+|room\s*\d+|#\d+|\d{3,}\s*(sf|square)", " ", t2)
    for n in re.findall(r"\b(\d{1,2})\b", t2):
        out.add(int(n))
    return out


def load_coworking():
    w = pd.read_csv(os.path.join(WORK, "coworking_research.csv"), dtype=str).fillna("")
    w["status"] = "open"
    w.loc[w.confidence == "low", "status"] = "unverified"
    w["floors"] = w.street_address.map(lambda a: ", ".join(p.strip() for p in a.split(",") if re.search(r"floor|suite", p, re.I)) or "unknown")
    w["second_source_url"] = ""
    w["pantry_note"] = ""
    for i, r in w.iterrows():
        o = R.COWORKING_OVERRIDES.get(r.coworking_id, {})
        for f, v in o.items():
            if f == "notes_add":
                w.at[i, "notes"] = (r.notes + " " + v).strip()
            else:
                w.at[i, f] = v
    for i, r in w.iterrows():
        for f, v in R.COWORKING_REVIEW1.get(r.coworking_id, {}).items():
            if f == "notes_add":
                w.at[i, "notes"] = (w.at[i, "notes"] + " " + v).strip()
            else:
                w.at[i, f] = v
    new = []
    for n in R.NEW_COWORKING:
        g = geocode(n["geocode"])
        row = {k: v for k, v in n.items() if k not in ("temp_id", "geocode")}
        row.update({"coworking_id": n["temp_id"], "lat": str(g["lat"]), "lon": str(g["lon"]), "bbl": g.get("bbl") or "",
                    "found_date": R.TODAY})
        new.append(row)
    w = pd.concat([w, pd.DataFrame(new)], ignore_index=True).fillna("")
    return w


COWORK_FLOORS = {  # floors per coworking location, from the rows' own sources
    "W-05": {2, 4, 5, 6}, "W-06": {4}, "W-07": {5, 6}, "W-08": {11}, "W-09": {2, 3}, "W-10": {4}, "W-11": {18, 19}, "W-12": {7},
    "W-13": {2}, "W-15": {5}, "W-16": {5}, "W-17": {9, 10, 11, 12}, "W-18": {2}, "W-19": {4, 5}, "W-20": {4, 5},
    "W-21": {4}, "W-22": {7}, "W-23": {2}, "W-24": {20}, "W-25": {31}, "W-26": {8, 9, 10}, "W-27": {6}, "W-28": {36},
}
LISTED_RESIDENTS = {  # company -> coworking id, where an operator or company source lists the company as inside
    "Lexeo Therapeutics": "W-30", "Insilico Medicine": "W-30", "Deerfield Management": "W-30",
    "Monte Carlo (Monte Carlo Data)": "W-31",
}
DIRECT_LEASE_DOCUMENTED = {  # same building as a coworking site, but the company's own lease is documented
    "Nayya", "Cognitiv", "Stellar Health", "Global Strategy Group", "Baseten", "Rakuten USA", "Charlie Health",
    "Matador Content", "Stone Source", "Alpine Investors", "GameChanger", "Senator Investment Group",
    "Selldorf Architects", "Valon", "Kaltura", "Wellcom Worldwide", "Green Mountain Energy", "Purple (PR)",
    "Capital One", "Acxiom", "Chainalysis", "SharkNinja", "Criteo",
}


def coworking_check(c, w):
    w_by_bbl = defaultdict(list)
    for r in w.itertuples():
        if r.bbl:
            w_by_bbl[r.bbl].append(r)
    for i, r in c.iterrows():
        name = r._merged_from.split(";")[0] if r._merged_from else r.company_name
        if name in LISTED_RESIDENTS or r.company_name in LISTED_RESIDENTS:
            wid = LISTED_RESIDENTS.get(name, LISTED_RESIDENTS.get(r.company_name))
            c.at[i, "in_coworking"], c.at[i, "_cw_temp"], c.at[i, "coworking_check"] = "Y", wid, "listed-as-resident"
            continue
        sites = w_by_bbl.get(r.bbl, [])
        if not sites:
            c.at[i, "in_coworking"], c.at[i, "coworking_check"] = "N", "no-coworking-in-building"
            continue
        cf = floors_of(r.floor)
        verdict, wid = None, sites[0].coworking_id
        for s in sites:
            wf = COWORK_FLOORS.get(s.coworking_id, set())
            if cf and wf and cf & wf:
                verdict, wid = "same-floor", s.coworking_id
                break
        if verdict == "same-floor":
            c.at[i, "in_coworking"] = "Y"
        elif name in DIRECT_LEASE_DOCUMENTED:
            verdict = "direct-lease-documented"
            c.at[i, "in_coworking"] = "N"
        elif cf and all(COWORK_FLOORS.get(s.coworking_id) for s in sites):
            verdict = "different-floor"
            c.at[i, "in_coworking"] = "N"
        else:
            verdict = "floor-unknown"
            c.at[i, "in_coworking"] = "N"
        c.at[i, "coworking_check"] = verdict
        c.at[i, "_cw_temp"] = wid
    return c


# ------------------------------------------------------------------ retailers
def load_retailers():
    r = pd.read_csv(os.path.join(WORK, "retailers_research.csv"), dtype=str).fillna("")
    r["buy_path_tier"] = r.notes.str.extract(r"Buy-path tier ([ABC])", expand=False).fillna("")
    for i, x in r.iterrows():
        for f, v in R.RETAILER_REVIEW2.get(x.retailer_name, {}).items():
            if f == "notes_replace":
                for o_, n_ in v:
                    assert o_ in r.at[i, "notes"], (x.retailer_name, o_)
                    r.at[i, "notes"] = r.at[i, "notes"].replace(o_, n_)
            elif f == "notes_add":
                r.at[i, "notes"] = (r.at[i, "notes"] + " " + v).strip()
            else:
                r.at[i, f] = v
    for i, x in r.iterrows():
        for f, v in R.RETAILER_REVIEW1.get(x.retailer_name, {}).items():
            if f == "notes_add":
                r.at[i, "notes"] = (r.at[i, "notes"] + " " + v).strip()
            else:
                r.at[i, f] = v
    return r


# ------------------------------------------------------------------ pin frontage fix
STREET_ADDR = re.compile(r"^\s*(\d+)[A-Za-z]?\s+(East|West)\s+(\d+)(st|nd|rd|th)?\s+Street", re.I)
PIN_LOG = []


def fix_pins(df, label):
    """Every pin must sit on the block face its address names (review round 1, R1-04).
    1) A published store coordinate (R.PIN_OVERRIDES) replaces the geocode outright.
    2) frontage.face(): the pin must be on the addressed side of the street (CSCL address
       ranges) and at least 15 m nearer the addressed street than the parallel one. A pin
       that fails moves to its frontage: the house number interpolated along the CSCL
       segment, 12 m inside the building line. The tax lot is unchanged.
    3) Addresses CSCL cannot test fall back to the round-3 grid parity rule (odd numbers
       on the north side of a numbered street)."""
    df["pin_note"] = df.get("pin_note", "")
    for i, r in df.iterrows():
        if not r.lat:
            continue
        addr = r.street_address.split(",")[0]
        name_key = r.get("retailer_name", "") or r.get("location_name", "")
        if name_key in R.PIN_OVERRIDES:
            la, lo, src = R.PIN_OVERRIDES[name_key]
            d0 = math.dist(grid.to_m(float(r.lat), float(r.lon)), grid.to_m(la, lo))
            t = frontage.face(la, lo, addr)
            fr = frontage.frontage(addr, la, lo) if (t["testable"] and not t["ok"]) else None
            if fr:  # the published point fails the block-face test (e.g. it sits in the roadway): keep its place along the street, on the address side
                la, lo, how = fr
                note = (f"Pin set at review round 1 from the store's own published coordinate ({src}), {d0:.0f} m from the geocode; "
                        f"that point sits {t['d_addr']:.0f} m from the {t['label']} centreline on the wrong side, so it was moved across to the address side ({how}).")
            else:
                note = f"Pin set at review round 1 to the store's own published coordinate ({src}), {d0:.0f} m from the geocode."
            df.at[i, "lat"], df.at[i, "lon"] = f"{la:.6f}", f"{lo:.6f}"
            df.at[i, "pin_note"] = note
            PIN_LOG.append((label, addr, "override", round(d0)))
            continue
        t = frontage.face(r.lat, r.lon, addr)
        if t["testable"] and t.get("range_found"):
            if t["ok"]:
                continue
            fr = frontage.frontage(addr, r.lat, r.lon)
            if fr:
                la, lo, how = fr
                t2 = frontage.face(la, lo, addr)
                df.at[i, "lat"], df.at[i, "lon"] = f"{la:.6f}", f"{lo:.6f}"
                why = ("wrong side of the street" if t["side_ok"] is False else
                       f"{t['d_addr']:.0f} m from {t['label']} but {t['d_par']:.0f} m from {t['par_label']}")
                df.at[i, "pin_note"] = (f"Pin moved to frontage at review round 1: the lot-centroid pin failed the block-face test ({why}); "
                                        f"{how}. Tax lot unchanged. New pin: {t2['d_addr']:.0f} m from {t2['label']}, "
                                        f"{t2['d_par']:.0f} m from {t2['par_label']}.")
                PIN_LOG.append((label, addr, "frontage", t["d_addr"], t["d_par"], t2["d_addr"], t2["d_par"], t2["ok"]))
                continue
        m = STREET_ADDR.match(addr)
        if not m:
            continue
        n, k = int(m.group(1)), int(m.group(3))
        s, x = grid.sx(float(r.lat), float(r.lon))
        north = n % 2 == 1
        if ((s > k) == north) and abs(s - k) <= 0.65:
            continue
        s2 = k + (0.25 if north else -0.25)
        la, lo = grid.latlon(s2, x)
        PIN_LOG.append((label, r.street_address, "grid-parity", round(s, 2), s2))
        df.at[i, "lat"], df.at[i, "lon"] = f"{la:.6f}", f"{lo:.6f}"
        df.at[i, "pin_note"] = (f"Pin moved at assembly from street index {s:.2f} to the {'north' if north else 'south'} "
                                f"frontage of {k}th St named by the address (tax lot unchanged; the geocoder had placed it on the far side of the lot).")
    # review round 2 (R2-10): a corner lot's centroid sits nearer the cross street than the avenue its address
    # names; move it to the avenue frontage near that corner and remember the cross street for the entrance note
    df["corner_side_street"] = ""
    for i, r in df.iterrows():
        if not r.lat:
            continue
        name_key = r.get("retailer_name", "") or r.get("location_name", "")
        if name_key in R.PIN_OVERRIDES:
            continue
        addr = r.street_address.split(",")[0]
        res = frontage.corner(addr, df.at[i, "lat"], df.at[i, "lon"])
        if res:
            la, lo, how, side = res
            df.at[i, "lat"], df.at[i, "lon"] = f"{la:.6f}", f"{lo:.6f}"
            df.at[i, "pin_note"] = (str(df.at[i, "pin_note"] or "") + f" Review round 2: {how}. Tax lot unchanged.").strip()
            df.at[i, "corner_side_street"] = side
            PIN_LOG.append((label, addr, "corner"))
    return df


# ------------------------------------------------------------------ main
def main():
    c = load_companies()
    c["_merged_from"] = ""
    c = apply_merges(c)
    c = apply_overrides(c)
    c = headcount_updates(c)
    c = lease_fields(c)
    c = audit_confidence(c)
    c = note_edits(c)
    c = normalise_company_fields(c)
    c = hq_fields(c)
    c = headcount_second(c)

    b_raw = load_buildings()
    # company rows whose tax lot has no slice building row: add a bare row from the company data
    extra = []
    for bbl in sorted(set(c.bbl) - set(b_raw.bbl)):
        cr = c[c.bbl == bbl].iloc[0]
        extra.append({"street_address": cr.street_address, "building_name": cr.street_address, "lat": cr.lat,
                      "lon": cr.lon, "bbl": bbl, "lobby_type": "unknown", "lobby_source_url": "",
                      "coi_required": "unknown", "coi_source_url": "",
                      "notes": "Building row added at assembly from the company row (no slice building row).",
                      "found_by": "assembly", "research_slice": "assembly"})
    b_raw = pd.concat([b_raw, pd.DataFrame(extra)], ignore_index=True)
    w = load_coworking()
    r = load_retailers()
    pl = pluto(list(c.bbl) + list(b_raw.bbl) + list(w.bbl) + list(r.bbl))
    b = merge_buildings(b_raw, c, pl)
    # every company bbl needs a building row
    missing = sorted(set(c.bbl) - set(b.bbl))
    assert not missing, missing

    c = fix_pins(c, "company"); b = fix_pins(b, "building"); w = fix_pins(w, "coworking"); r = fix_pins(r, "retailer")
    for row in sorted(set(PIN_LOG)):
        print("pin fix:", row)
    # geometry for everything
    for df in (c, b, w, r):
        ss, xs, ins, bo = [], [], [], []
        for _, row in df.iterrows():
            la, lo = float(row.lat), float(row.lon)
            s, x = grid.sx(la, lo)
            ss.append(round(s, 3)); xs.append(round(x, 1))
            ins.append("Y" if boundary.inside(la, lo) else "N")
            bo.append(round(boundary.blocks_outside(la, lo), 1))
        df["grid_s"], df["grid_x"], df["in_boundary"], df["blocks_outside"] = ss, xs, ins, bo

    c = coworking_check(c, w)

    # candidate status
    for i, row in c.iterrows():
        if row.candidate_status:
            continue
        if row.in_boundary == "N":
            st = "near-miss-outside"
        elif row.in_coworking == "Y":
            st = "excluded-coworking"
        elif row.headcount_band == "over-500":
            st = "near-miss-over-500"
        elif row.headcount_band == "under-40":
            st = "candidate" if row.company_name in R.FOUNDER_CALL_30_39 else "excluded-under-40"
        else:
            st = "candidate"
        c.at[i, "candidate_status"] = st
    # an outside row that is also over 500 keeps near-miss-outside; note both
    for i, row in c.iterrows():
        if row.candidate_status == "near-miss-outside" and row.headcount_band == "over-500":
            c.at[i, "notes_assembly"] = (row.notes_assembly + " Also over 500 company-wide.").strip()

    # unknown-band reason
    for i, row in c.iterrows():
        key = row._merged_from.split(";")[0] if row._merged_from else row.company_name
        if row.headcount_band == "unknown":
            c.at[i, "headcount_unknown_reason"] = R.UNKNOWN_BAND_REASON.get(row.company_name, R.UNKNOWN_BAND_REASON.get(key, R.UNKNOWN_BAND_DEFAULT))
        else:
            c.at[i, "headcount_unknown_reason"] = ""

    c.to_csv(os.path.join(OUT, "master_companies.csv"), index=False)
    b.to_csv(os.path.join(OUT, "master_buildings.csv"), index=False)
    w.to_csv(os.path.join(OUT, "master_coworking.csv"), index=False)
    r.to_csv(os.path.join(OUT, "master_retailers.csv"), index=False)

    # summary
    print("companies", len(c), c.candidate_status.value_counts().to_dict())
    cand = c[c.candidate_status == "candidate"]
    print("candidates by confidence", cand.confidence.value_counts().to_dict())
    print("candidates by band", cand.headcount_band.value_counts().to_dict())
    print("candidates by lease", cand.lease_status.value_counts().to_dict())
    print("buildings", len(b), "in", (b.in_boundary == "Y").sum())
    print("coworking", len(w), "in", (w.in_boundary == "Y").sum())
    print("retailers", len(r), "in", (r.in_boundary == "Y").sum(), "max blocks", r.blocks_outside.max())
    print(c[c.candidate_status.str.startswith("near-miss-outside")][["company_name", "street_address", "blocks_outside", "headcount_band"]].to_string())
    print(c[c.in_coworking == "Y"][["company_name", "street_address", "floor", "coworking_check", "_cw_temp"]].to_string())
    print(c[c.coworking_check == "floor-unknown"][["company_name", "street_address", "floor", "_cw_temp"]].to_string())


if __name__ == "__main__":
    main()
