#!/usr/bin/env python3
"""Assemble workstream B's master tables from the research slices in _work/.

Writes _build/out/*.pkl-free CSV intermediates (master_*.csv) that export.py turns into
the deliverables. Run from anywhere: python3 _build/assemble.py
"""
import json
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
    for name, o in R.OVERRIDES.items():
        idx = c.index[c.company_name == name]
        assert len(idx) == 1, name
        i = idx[0]
        for f, v in o.items():
            if f == "note_add":
                c.at[i, "notes_assembly"] = (c.at[i, "notes_assembly"] + " " + v).strip()
            else:
                c.at[i, f] = v
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
    return c


def audit_confidence(c):
    """Apply the B confidence scale strictly. Downgrades only, each noted."""
    for i, r in c.iterrows():
        a_date = r.address_source_date or ""
        b_date = r.second_source_date or ""
        recent = (a_date >= R.CUTOFF_24M) or (b_date >= R.CUTOFF_24M)
        independent = bool(r.second_source_url) and domain(r.second_source_url) != domain(r.address_source_url)
        same_release = "same" in r.notes.lower() and ("announcement" in r.notes.lower() or "release" in r.notes.lower())
        conf = r.confidence
        new = conf
        why = []
        if conf == "high":
            if not recent:
                new = "low"; why.append("no source under 24 months old")
            elif not independent:
                new = "medium"; why.append("second source is the same publisher or missing")
            elif same_release and r.research_slice.startswith("S1") and r.company_name in ("Selldorf Architects",):
                new = "medium"; why.append("both articles trace to one broker announcement")
        if conf == "medium" and not recent:
            new = "low"; why.append("no source under 24 months old")
        if new != conf:
            c.at[i, "confidence"] = new
            c.at[i, "notes_assembly"] = (c.at[i, "notes_assembly"] + f" Confidence lowered at assembly from {conf} to {new}: {'; '.join(why)}.").strip()
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
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "desk-drop-cluster-research/0.1"}), timeout=60) as f:
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
    "W-06": {4}, "W-07": {5, 6}, "W-08": {11}, "W-09": {2, 3}, "W-10": {4}, "W-11": {18, 19}, "W-12": {7},
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
    "Capital One", "Acxiom", "Chainalysis",
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
    return r


# ------------------------------------------------------------------ main
def main():
    c = load_companies()
    c["_merged_from"] = ""
    c = apply_merges(c)
    c = apply_overrides(c)
    c = lease_fields(c)
    c = audit_confidence(c)

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
            st = "excluded-under-40"
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
