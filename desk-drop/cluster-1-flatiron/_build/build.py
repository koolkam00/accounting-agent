#!/usr/bin/env python3
"""Turn _build/out/master_*.csv into the final tables, the model route and the walk plan.

Writes CSVs into cluster-1-flatiron/ and JSON intermediates into _build/out/.
"""
import itertools
import json
import math
import random
import os
import re
import sys
import urllib.parse
import urllib.request

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
sys.path.insert(0, HERE)
import grid  # noqa: E402
import boundary  # noqa: E402
import router  # noqa: E402
import resolutions as R  # noqa: E402

# ------------------------------------------------------------------ parameters (also written to the Route tab)
P = {
    "hand_truck_pace_m_per_min": 64.0,   # MUTCD 2009 4E.06: 3.5 ft/s design walking speed = 64 m/min
    "walk_pace_m_per_min": 73.0,         # MUTCD 2009 4E.06 option: up to 4 ft/s = 73 m/min, for the unloaded verification walk
    "wait_avenue_crossing_s": 25.0,      # assumption: expected signal wait crossing an avenue, incl. curb ramps with a hand truck
    "wait_street_crossing_s": 15.0,      # assumption: expected wait crossing a side street while walking along an avenue
    "minutes_per_stop": 15.0,            # plan.md, Phase 3 per-stop procedure
    "route_start": "08:00", "route_end": "11:00",
    "car_overhead_min": 8.0,             # assumption: 5 min to hail and load the hand truck, 3 min to unload at the curb
    "car_speed_mph": 9.7,                # NBER Digest 2025-06-01: CBD average speed rose from 8.2 to 9.7 mph after congestion pricing
    "car_detour_factor": 1.3,            # assumption: one-way streets and turns
    "walk_session_cap_min": 90.0,
    "same_building_transfer_min": 3.0,   # assumption: down one elevator and up another with a hand truck
    "cases_per_load": 5,                 # review round 2 (R2-06): plan.md puts five offices at five to eight cases and two car rides; 5 cases a load for drinks
    "reload_minutes": 20.0,              # review round 2 (R2-06): assumption, to be timed on the walk: meet the car or van, reload, re-strap
}
RELOAD_POINT = ("Reload point (model): the second five cases ride in a car or van that meets you at the kerb of the last stop "
                "of load 1, or wait at the consolidation address if it is inside the cluster. Founder to choose and time it.")
NBER_URL = "https://www.nber.org/digest/202506/impact-new-york-citys-congestion-pricing-program"
MUTCD_URL = "https://mutcd.fhwa.dot.gov/htm/2009/part4/part4e.htm"

CONTRACT_COMPANY = ["company_id", "company_name", "website", "industry", "building_id", "street_address", "floor", "zip",
                    "lat", "lon", "in_boundary", "headcount_band", "headcount_scope", "headcount_source_url",
                    "address_source_url", "address_source_date", "second_source_url", "confidence", "in_coworking",
                    "coworking_id", "linkedin_company_url", "notes", "found_date"]
EXTRA_COMPANY = ["hq_city", "hq_in_nyc", "hq_source_url",
                 "headcount_count", "headcount_check", "headcount_second_count", "headcount_second_source_url",
                 "headcount_second_source_date", "parent_company", "parent_company_source",
                 "building_lobby_type", "candidate_status", "lease_status", "move_in_date", "headcount_source_date", "headcount_unknown_reason",
                 "address_source_type", "second_source_date", "coworking_check", "bbl", "blocks_outside",
                 "leased_sf_mentioned", "research_slice"]
CONTRACT_BUILDING = ["building_id", "street_address", "building_name", "lat", "lon", "lobby_type", "lobby_source_url",
                     "coi_required", "coi_source_url", "candidate_company_count", "verified_on_foot", "notes"]
EXTRA_BUILDING = ["bbl", "also_known_as", "zip", "in_boundary", "candidate_company_ids", "other_company_count",
                  "coworking_ids", "retailer_ids", "pluto_numfloors", "pluto_yearbuilt", "pluto_bldgclass",
                  "pluto_office_sqft", "pluto_address", "pin_check", "entrance_note", "research_slices"]
CONTRACT_COWORK = ["coworking_id", "operator", "location_name", "street_address", "lat", "lon", "pantry_control",
                   "pantry_source_url", "source_url", "source_date", "confidence", "notes"]
EXTRA_COWORK = ["in_boundary", "blocks_outside", "status", "floors", "building_id", "bbl", "tenant_company_ids",
                "second_source_url", "exclusive_food_contract_signal", "research_id", "found_date"]
CONTRACT_RETAIL = ["retailer_id", "retailer_name", "street_address", "lat", "lon", "inside_boundary", "blocks_outside",
                   "shelf_set", "source_url", "source_date", "confidence", "notes"]
EXTRA_RETAIL = ["buy_path_tier", "public_map", "public_map_reason", "public_description", "walk_minutes_from_cluster_edge", "candidates_within_5_blocks", "nearest_candidate_building_id",
                "nearest_candidate_blocks", "emerging_brand_evidence", "operating_evidence_url", "bbl", "research_id",
                "found_date"]


REG = os.path.join(HERE, "id_registry.json")
ILS_KICKS = 400  # route search: random two-swap kicks after the seeded local search


def assign_ids(keys, prefix, kind):
    """Stable IDs: a key seen before keeps its ID; new keys get the next free number."""
    reg = json.load(open(REG)) if os.path.exists(REG) else {}
    m = reg.setdefault(kind, {})
    nxt = max([int(v.split("-")[-1]) for v in m.values()] + [0]) + 1
    out = []
    for k in keys:
        if k not in m:
            m[k] = f"{prefix}-{nxt:03d}"; nxt += 1
        out.append(m[k])
    json.dump(reg, open(REG, "w"), indent=1, sort_keys=True)
    return out


def walk_m(a, b):
    return router.leg(a, b)["metres"]


def sf_mentions(text):
    hits = re.findall(r"(\d{1,3}(?:,\d{3})+|\d{4,6})\s*(?:sf|SF|square feet|-square-foot)", text or "")
    vals = []
    for h in hits:
        v = int(h.replace(",", ""))
        if 1000 <= v <= 2_000_000 and v not in vals:
            vals.append(v)
    return "; ".join(f"{v:,} sf" for v in vals[:3])


def main():
    c = pd.read_csv(os.path.join(OUT, "master_companies.csv"), dtype=str).fillna("")
    b = pd.read_csv(os.path.join(OUT, "master_buildings.csv"), dtype=str).fillna("")
    w = pd.read_csv(os.path.join(OUT, "master_coworking.csv"), dtype=str).fillna("")
    r = pd.read_csv(os.path.join(OUT, "master_retailers.csv"), dtype=str).fillna("")
    for df in (c, b, w, r):
        df["grid_s"] = df.grid_s.astype(float)
        df["grid_x"] = df.grid_x.astype(float)
        df["blocks_outside"] = df.blocks_outside.astype(float)

    # ---------------- companies: notes, ids
    c["notes"] = c.apply(lambda x: (x.notes + (" | Assembly 2026-10-24: " + x.notes_assembly if x.notes_assembly else "")
                                    + (" " + x.pin_note if x.get("pin_note") else "")).strip(), axis=1)
    c["leased_sf_mentioned"] = c.notes.map(sf_mentions)
    c["linkedin_company_url"] = ""
    tab_order = {"candidate": 0, "excluded-coworking": 1, "excluded-not-office": 2, "near-miss-over-500": 3, "near-miss-outside": 4}
    c["_t"] = c.candidate_status.map(tab_order)
    c = c.sort_values(["_t", "grid_s", "grid_x", "company_name"]).reset_index(drop=True)
    c["company_id"] = assign_ids([f"{x.company_name}|{x.street_address}" for x in c.itertuples()], "B-C", "company")

    # ---------------- buildings: which go in the tab
    cand = c[c.candidate_status == "candidate"]
    w_in = w[w.in_boundary == "Y"]
    b["candidate_company_count"] = b.bbl.map(lambda k: int((cand.bbl == k).sum()))
    b["has_cowork"] = b.bbl.map(lambda k: bool(k) and (w_in.bbl == k).any())
    keep = (b.in_boundary == "Y") & ((b.candidate_company_count > 0) | b.has_cowork)
    b_other = b[~keep].copy()
    b = b[keep].copy().sort_values(["grid_s", "grid_x"]).reset_index(drop=True)
    b["building_id"] = assign_ids([x.bbl or x.street_address for x in b.itertuples()], "B-B", "building")
    bid = dict(zip(b.bbl, b.building_id))
    c["building_id"] = c.bbl.map(lambda k: bid.get(k, ""))

    # ---------------- coworking ids
    w["_o"] = (w.in_boundary != "Y").astype(int)
    w = w.sort_values(["_o", "grid_s", "grid_x"]).reset_index(drop=True)
    w["research_id"] = w.coworking_id
    w["coworking_id"] = assign_ids(list(w.research_id), "B-W", "coworking")
    wmap = dict(zip(w.research_id, w.coworking_id))
    # coworking_id names the site a company is inside (in_coworking = Y). Same-building, not-inside cases are
    # described by coworking_check plus the building's coworking_ids.
    c["coworking_id"] = [wmap.get(t, "") if (t and ic == "Y") else "" for t, ic in zip(c._cw_temp, c.in_coworking)]
    w["building_id"] = w.bbl.map(lambda k: bid.get(k, ""))
    w["notes"] = w.apply(lambda x: (x.notes + (" " + x.pin_note if x.get("pin_note") else "")).strip(), axis=1)
    w["tenant_company_ids"] = w.coworking_id.map(lambda k: "; ".join(c[(c.coworking_id == k) & (c.in_coworking == "Y")].company_id))
    b["coworking_ids"] = b.bbl.map(lambda k: "; ".join(w[w.bbl == k].coworking_id))

    # ---------------- retailers
    r["_o"] = r.in_boundary.map(lambda v: 0 if v == "Y" else 1)
    r = r.sort_values(["_o", "blocks_outside", "retailer_name"]).reset_index(drop=True)
    r["research_id"] = r.retailer_id
    r["retailer_id"] = assign_ids(list(r.research_id), "B-R", "retailer")
    r["inside_boundary"] = r.in_boundary
    r["blocks_outside_f"] = r.blocks_outside
    r["blocks_outside"] = r.blocks_outside.map(lambda v: int(math.floor(v + 0.5)) if v > 0 else 0)
    r["notes"] = r.apply(lambda x: (x.notes + (" " + x.pin_note if x.get("pin_note") else "")).strip(), axis=1)
    r["public_map"] = r.apply(lambda x: "Y" if x.buy_path_tier in ("A", "B") and x.confidence in ("high", "medium")
                              and x.retailer_name not in R.PUBLIC_EXCLUDE else "N", axis=1)
    r["public_map_reason"] = r.apply(lambda x: "" if x.public_map == "Y" else R.PUBLIC_EXCLUDE.get(
        x.retailer_name, "Tier C (mass, conventional or private label): a landmark, not a buy path." if x.buy_path_tier == "C"
        else "Low confidence: the store may have closed; walk it first."), axis=1)
    r["public_description"] = r.retailer_name.map(lambda n: R.PUBLIC_DESC.get(n, ""))
    r["walk_minutes_from_cluster_edge"] = r.blocks_outside_f.map(
        lambda v: 0 if v <= 0 else max(1, int(round(v * grid.model()["spacing_m"] / P["walk_pace_m_per_min"]))))
    miss = r[(r.public_map == "Y") & (r.public_description == "")]
    assert miss.empty, list(miss.retailer_name)
    b["retailer_ids"] = b.bbl.map(lambda k: "; ".join(r[r.bbl == k].retailer_id))
    cand_b = b[b.candidate_company_count > 0]
    near_n, near_b, near_d = [], [], []
    for _, x in r.iterrows():
        ds = [(walk_m(x, y) / grid.model()["spacing_m"], y.building_id, y.candidate_company_count) for _, y in cand_b.iterrows()]
        near_n.append(int(sum(n for d, _, n in ds if d <= 5.0)))
        d0 = min(ds)
        near_b.append(d0[1]); near_d.append(round(d0[0], 1))
    r["candidates_within_5_blocks"], r["nearest_candidate_building_id"], r["nearest_candidate_blocks"] = near_n, near_b, near_d

    # ---------------- building fields
    b["candidate_company_ids"] = b.bbl.map(lambda k: "; ".join(cand[cand.bbl == k].index.map(lambda i: c.at[i, "company_id"]) if False else c[(c.bbl == k) & (c.candidate_status == "candidate")].company_id))
    b["other_company_count"] = b.bbl.map(lambda k: int(((c.bbl == k) & (c.candidate_status != "candidate")).sum()))
    b["verified_on_foot"] = ""
    b["notes"] = b.notes_research
    # pin check against PLUTO lot centroid
    pc = []
    for _, x in b.iterrows():
        if x.get("pluto_lat"):
            d = math.dist(grid.to_m(float(x.lat), float(x.lon)), grid.to_m(float(x.pluto_lat), float(x.pluto_lon)))
            pc.append(f"PLUTO lot {x.pluto_address}, centroid {d:.0f} m from pin")
        else:
            pc.append("no PLUTO match")
    b["pin_check"] = [p + ("; " + n if n else "") for p, n in zip(pc, b.get("pin_note", [""] * len(b)))]
    b["entrance_note"] = b.apply(entrance_note, axis=1)
    lob_by_bbl = dict(zip(b.bbl, b.lobby_type))
    allb = pd.read_csv(os.path.join(OUT, "master_buildings.csv"), dtype=str).fillna("")
    lob_all = dict(zip(allb.bbl, allb.lobby_type))
    c["building_lobby_type"] = c.bbl.map(lambda k: lob_by_bbl.get(k, lob_all.get(k, "unknown")) or "unknown")
    c["zip"] = c.apply(lambda x: x.zip or (b[b.bbl == x.bbl].zip.iloc[0] if (b.bbl == x.bbl).any() else ""), axis=1)

    # ---------------- route
    try:
        route, legs = model_route(c, b)
        route_rule = "one 40-75 and one 76-150 office"
        main_bands = ("40-75", "76-150")
    except ValueError:
        # review round 2: after the second headcounts no high-confidence, occupied 40-75 office with a sourced band
        # remains, so the main route asks for a 76-150 office and three bands; the high-or-medium variant keeps both
        main_bands = ("76-150",)
        route, legs = model_route(c, b, bands_required=main_bands)
        route_rule = ("one 76-150 office and at least three bands (no high-confidence, occupied 40-75 office with a sourced band "
                      "remains after review round 2's second headcounts; the high-or-medium variant below keeps a 40-75 office)")
    variants = {}
    for key, kw in (("no_security_minimum", {"min_security": 0}),
                    ("no_band_rule", {"bands_required": ()}),
                    ("high_or_medium", {"confs": ("high", "medium")}),
                    ("high_or_medium_no_security_minimum", {"confs": ("high", "medium"), "min_security": 0})):
        kw = dict(kw)
        if "bands_required" not in kw and "confs" not in kw:
            kw["bands_required"] = main_bands
        try:
            rv, _ = model_route(c, b, kicks=120, **kw)
        except ValueError:
            kw["bands_required"] = main_bands
            rv, _ = model_route(c, b, kicks=120, **kw)
        tot = rv.leg_minutes_est.sum() + P["minutes_per_stop"] * len(rv)
        variants[key] = {"total_minutes": round(float(tot + rv.reload_minutes_before.sum()), 1), "total_one_load": round(float(tot), 1),
                         "end": rv.depart_est.iloc[-1],
                         "stops": "; ".join(f"{x.company_name} ({x.street_address})" for x in rv.itertuples())}
        print("variant", key, variants[key]["total_minutes"], variants[key]["end"])
    # ---------------- walk
    walk = walk_plan(b, w, r, c)

    # ---------------- write
    comp_tab = c[c.candidate_status.isin(["candidate", "excluded-coworking", "excluded-not-office"])]
    near = c[c.candidate_status.str.startswith("near-miss")].copy()
    near["near_miss_reason"] = near.apply(near_reason, axis=1)
    near["near_miss_class"] = near.apply(near_class, axis=1)
    near["company_wide_count_cited"] = near.apply(lambda x: company_count(x)[0] or "", axis=1)
    near["nyc_office_may_fit"] = near.apply(nyc_may_fit, axis=1)
    cols_c = CONTRACT_COMPANY + EXTRA_COMPANY
    comp_tab[cols_c].to_csv(os.path.join(ROOT, "companies.csv"), index=False)
    near[cols_c + ["near_miss_reason", "near_miss_class", "company_wide_count_cited", "nyc_office_may_fit"]].to_csv(os.path.join(ROOT, "near_miss.csv"), index=False)
    b[CONTRACT_BUILDING + EXTRA_BUILDING].to_csv(os.path.join(ROOT, "buildings.csv"), index=False)
    w[CONTRACT_COWORK + EXTRA_COWORK].to_csv(os.path.join(ROOT, "coworking.csv"), index=False)
    r[CONTRACT_RETAIL + EXTRA_RETAIL].to_csv(os.path.join(ROOT, "retailers.csv"), index=False)
    route.to_csv(os.path.join(ROOT, "route.csv"), index=False)
    walk.drop(columns=["_s", "_x"]).to_csv(os.path.join(ROOT, "walk.csv"), index=False)
    b_other.to_csv(os.path.join(ROOT, "_work", "buildings_no_candidate.csv"), index=False)
    json.dump({"legs": legs, "params": P, "variants": variants, "rule": route_rule}, open(os.path.join(OUT, "route_legs.json"), "w"), indent=1)
    # grid coordinates for the map builder
    for name, df in (("companies", c), ("buildings", b), ("coworking", w), ("retailers", r)):
        df.to_csv(os.path.join(OUT, f"final_{name}.csv"), index=False)
    walk.to_csv(os.path.join(OUT, "final_walk.csv"), index=False)

    content_checks()
    # summary
    print("companies tab", len(comp_tab), "near-miss", len(near))
    print("buildings tab", len(b), "other buildings", len(b_other))
    print("coworking", len(w), "retailers", len(r))
    print(route[["stop", "company_id", "company_name", "street_address", "lobby_type", "leg_minutes_est", "arrive_est", "depart_est"]].to_string())
    print("walk sessions", walk.session.nunique(), "total min", round(walk.groupby("session").session_minutes_est.first().sum()))
    print(walk.groupby("session").agg(phase=("phase", "first"), stops=("order", "count"), mins=("session_minutes_est", "first"), start=("start_point", "first"), end=("end_point", "first")).to_string())


COUNT_RX = [r"([\d][\d,]*)\+?'? total employees", r"Wikipedia[^.|]*?'?([\d][\d,]*)\+?'?\s*(?:employees|staff)",
            r"employing over ([\d][\d,]*)", r"'?([\d][\d,]{2,})\+?'?\s*(?:employees|staff|FTE|people)"]


def company_count(x):
    """Company-wide count cited for a near-miss row: (number, where it comes from)."""
    if x.company_name in R.NEAR_COUNT_OVERRIDES:
        return R.NEAR_COUNT_OVERRIDES[x.company_name]
    if x.get("headcount_check") == "over-500-second-source" and str(x.get("headcount_count", "")).isdigit():
        return int(x.headcount_count), "Revelio Labs page in headcount_source_url, as of March 2026, added at review round 2"
    for rx in COUNT_RX:
        m = re.search(rx, x.notes, re.I)
        if m:
            return int(m.group(1).replace(",", "")), "the count quoted in this row's notes"
    return None, ""


def near_class(x):
    """R1-16: 'just over 500' means 501 to 1,000. Bigger firms stay visible but are tagged."""
    if x.candidate_status == "near-miss-outside":
        return "outside-line"
    n, _ = company_count(x)
    if n is None:
        return "over-500-count-not-cited"
    if n <= 1000:
        return "just-over-500 (501 to 1,000)"
    if n < 5000:
        return "over-1,000 (1,001 to 4,999)"
    return "not-near (5,000 or more)"


def nyc_may_fit(x):
    if x.company_name in R.NYC_MAY_FIT_R2:
        return "Y"
    return "Y" if re.search(r"NYC office (itself )?may|in New York|NYC office size unknown|NYC team|New York headcount",
                            x.notes) else "N"


def content_checks():
    """Review round 1 (R1-09, R1-11): fail the build if a data file guesses at size in its notes
    or carries the working business name (the name lives in one config cell per deliverable)."""
    bad = []
    for f in ("companies.csv", "near_miss.csv", "buildings.csv", "coworking.csv", "retailers.csv", "route.csv", "walk.csv"):
        d = pd.read_csv(os.path.join(ROOT, f), dtype=str).fillna("")
        for col in d.columns:
            for i, v in d[col].items():
                for rx in R.BANNED_NOTE_PATTERNS:
                    if re.search(rx, v, re.I):
                        bad.append(f"{f} row {i + 2} {col}: '{rx}'")
    if bad:
        raise SystemExit("content check failed:\n" + "\n".join(bad))
    print("content checks: no size guesses and no business name in the data files")


def near_reason(x):
    cls = near_class(x)
    if x.candidate_status == "near-miss-outside":
        why = f"outside-line: outside the boundary by {x.blocks_outside:.1f} blocks"
        a = x.street_address
        if re.search(r"West 2\dth|West 1\dth", a) and float(x.grid_x) < -300:
            why += " (side street west of Sixth Ave)"
        elif float(x.grid_s) > 30.5:
            why += " (31st St frontage, north of the 30th St line)"
        elif float(x.grid_x) > 376:
            why += " (east of the Park Ave S frontage)"
        if x.headcount_band == "over-500":
            why += "; also over 500 company-wide"
        return why
    n, src = company_count(x)
    s = f"{cls}: over 500 company-wide" + (f" ({n:,}; {src})" if n else " (no count cited; over 500 per the row's source)")
    if nyc_may_fit(x) == "Y":
        s += "; the NYC office alone may fit the 40-250 band, founder to confirm"
    return s


LOBBY_RANK = {"walk-up": 0, "unknown": 1, "loading dock": 2, "security desk": 3}


def leg_minutes(lg, pace):
    walk = lg["metres"] / pace + (lg["avenue_crossings"] * P["wait_avenue_crossing_s"] + lg["street_crossings"] * P["wait_street_crossing_s"]) / 60.0
    return walk


def car_minutes(lg):
    m_per_min = P["car_speed_mph"] * 1609.344 / 60.0
    return P["car_overhead_min"] + lg["metres"] * P["car_detour_factor"] / m_per_min


def model_route(c, b, min_security=2, bands_required=("40-75", "76-150"), confs=("high",), kicks=None):
    """Pick ten compact, high-confidence, occupied candidates (band known) and order them by
    lobby class: walk-up, unknown, loading dock, security desk. Minimises estimated minutes.
    Search: every seed's nearest set, then swap-based local search; the winner's order inside
    each lobby class is solved exactly."""
    lob = dict(zip(b.building_id, b.lobby_type))
    pool = c[(c.candidate_status == "candidate") & (c.confidence.isin(confs)) & (c.lease_status == "occupied")
             & (c.headcount_band.isin(["40-75", "76-150", "151-250", "251-500"])) & (c.building_id != "")
             & ~c.industry.str.contains(R.CPG_INDUSTRY_RX, case=False, regex=True)].copy()  # R1-17: no food or drink brand offices
    pool["lobby_type"] = pool.building_id.map(lob)
    recs = pool.reset_index(drop=True).to_dict("records")
    n = len(recs)
    L = [[None] * n for _ in range(n)]
    T = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if recs[i]["building_id"] == recs[j]["building_id"]:
                L[i][j] = {"path": [(recs[i]["grid_s"], recs[i]["grid_x"])], "metres": 0.0, "avenue_crossings": 0, "street_crossings": 0, "same_building": True}
                T[i][j] = P["same_building_transfer_min"]
            else:
                L[i][j] = router.leg(recs[i], recs[j])
                T[i][j] = leg_minutes(L[i][j], P["hand_truck_pace_m_per_min"])

    def feasible(S):
        per_b = {}
        for j in S:
            per_b[recs[j]["building_id"]] = per_b.get(recs[j]["building_id"], 0) + 1
        if max(per_b.values()) > 2:
            return False
        bands = [recs[j]["headcount_band"] for j in S]
        if len(set(bands)) < 3 or any(bq not in bands for bq in bands_required):  # R1-17: offices near 50 and 100 too
            return False
        return sum(1 for j in S if recs[j]["lobby_type"] == "security desk") >= min_security

    def order(S, exact=False):
        groups = {}
        for i in S:
            groups.setdefault(LOBBY_RANK[recs[i]["lobby_type"]], []).append(i)
        seq = []
        for k in sorted(groups):
            g = groups[k]
            if exact and len(g) <= 8:
                best = None
                for pm in itertools.permutations(g):
                    cst = (T[seq[-1]][pm[0]] if seq else 0) + sum(T[a][b2] for a, b2 in zip(pm, pm[1:]))
                    if best is None or cst < best[0]:
                        best = (cst, list(pm))
                seq += best[1]
            else:
                starts = g if not seq else [min(g, key=lambda j: T[seq[-1]][j])]
                best = None
                for s0 in starts:
                    pm = greedy(g, s0, T)
                    pm = two_opt(pm, T, fixed_prev=seq[-1] if seq else None)
                    cst = (T[seq[-1]][pm[0]] if seq else 0) + sum(T[a][b2] for a, b2 in zip(pm, pm[1:]))
                    if best is None or cst < best[0]:
                        best = (cst, pm)
                seq += best[1]
        return sum(T[a][b2] for a, b2 in zip(seq, seq[1:])), seq

    cache = {}

    def cost_of(S):
        k = frozenset(S)
        if k not in cache:
            cache[k] = order(sorted(S))[0] if feasible(S) else 1e9
        return cache[k]

    def improve(S):
        cur = cost_of(S)
        while True:  # best-improvement swap search
            cand = None
            for out_ in S:
                for in_ in range(n):
                    if in_ in S:
                        continue
                    S2 = [q for q in S if q != out_] + [in_]
                    cst = cost_of(S2)
                    if cst < cur - 1e-9 and (cand is None or cst < cand[0]):
                        cand = (cst, S2)
            if cand is None:
                return cur, S
            cur, S = cand

    best = None
    for s0 in range(n):
        near = sorted(range(n), key=lambda j: (T[s0][j] if j != s0 else -1, j))
        S = []

        def room(j):
            return j not in S and sum(1 for q in S if recs[q]["building_id"] == recs[j]["building_id"]) < 2
        # seed with s0 and the stops the constraints need (nearest first), then fill with the nearest others
        S.append(s0)
        preds = []
        for bq in bands_required:
            if recs[s0]["headcount_band"] != bq:
                preds.append(lambda j, bq=bq: recs[j]["headcount_band"] == bq)
        for _ in range(max(0, min_security - (recs[s0]["lobby_type"] == "security desk"))):
            preds.append(lambda j: recs[j]["lobby_type"] == "security desk")
        for pred in preds:
            hit = next((j for j in near if pred(j) and room(j)), None)
            if hit is not None:
                S.append(hit)
        for j in near:
            if len(S) >= 10:
                break
            if room(j):
                S.append(j)
        if len(S) < 10:
            continue
        S = S[:10]
        cur, S = improve(S)
        if cur < 1e9 and (best is None or cur < best[0] - 1e-9):
            best = (cur, sorted(S))
    if best is None:
        raise ValueError("no ten-stop set meets the route constraints")
    # iterated local search (review round 1): kick the best set by two random swaps, re-improve, keep the better
    rng = random.Random(20261024)
    for _ in range(ILS_KICKS if kicks is None else kicks):
        S = list(best[1])
        for _k in range(2):
            out_ = rng.choice(S)
            in_ = rng.choice([j for j in range(n) if j not in S])
            S = [q for q in S if q != out_] + [in_]
        cur, S = improve(S)
        if cur < best[0] - 1e-9:
            best = (cur, sorted(S))
    cost, seq = order(best[1], exact=True)
    rows, legs = [], []
    t = 8 * 60.0
    prev = None
    ent = dict(zip(b.building_id, b.get("entrance_note", [""] * len(b))))
    for k, i in enumerate(seq):
        x = recs[i]
        if prev is None:
            lg = {"path": [(x["grid_s"], x["grid_x"])], "metres": 0.0, "avenue_crossings": 0, "street_crossings": 0}
            lm, cm = 0.0, None
        else:
            lg = L[prev][i]
            # review round 2 (R2-09): the same rounded formula as the Route tab (whole metres, one decimal)
            if lg.get("same_building"):
                lm = P["same_building_transfer_min"]
            else:
                lm = round(round(lg["metres"]) / P["hand_truck_pace_m_per_min"]
                           + (lg["avenue_crossings"] * P["wait_avenue_crossing_s"] + lg["street_crossings"] * P["wait_street_crossing_s"]) / 60.0, 1)
            cm = None if lg.get("same_building") else round(P["car_overhead_min"] + round(lg["metres"]) * P["car_detour_factor"] / (P["car_speed_mph"] * 1609.344 / 60.0), 1)
        reload = P["reload_minutes"] if (k > 0 and k % int(P["cases_per_load"]) == 0) else 0.0
        t += lm + reload
        arrive = t
        t += P["minutes_per_stop"]
        rows.append({
            "stop": k + 1, "company_id": x["company_id"], "company_name": x["company_name"],
            "building_id": x["building_id"], "street_address": x["street_address"], "floor": x["floor"],
            "lobby_type": x["lobby_type"], "headcount_band": x["headcount_band"], "confidence": x["confidence"],
            "lat": x["lat"], "lon": x["lon"],
            "leg_metres_est": round(lg["metres"]), "avenue_crossings": lg["avenue_crossings"],
            "street_crossings": lg["street_crossings"], "same_building": "Y" if lg.get("same_building") else ("" if prev is None else "N"),
            "leg_minutes_est": round(lm, 1),
            "car_minutes_est": round(cm, 1) if cm is not None else "",
            "load": 1 + k // int(P["cases_per_load"]),
            "reload_minutes_before": reload,
            "car_faster": ("Y" if cm is not None and cm < lm else "N") if prev is not None else "",
            "stop_minutes": P["minutes_per_stop"],
            "arrive_est": hhmm(arrive), "depart_est": hhmm(t),
            "receiving_window_from_intake": "",
            "entrance_note": ent.get(x["building_id"], ""),
            "notes": RELOAD_POINT if reload else "",
            "label": "estimate",
        })
        legs.append({"stop": k + 1, "path": router.path_lonlat(lg["path"])})
        prev = i
    route = pd.DataFrame(rows)
    return route, legs


def two_opt(seq, T, fixed_prev=None):
    seq = list(seq)
    improved = True
    while improved:
        improved = False
        for i in range(0, len(seq) - 1):
            for j in range(i + 1, len(seq)):
                new = seq[:i] + seq[i:j + 1][::-1] + seq[j + 1:]
                def cost(q):
                    return (T[fixed_prev][q[0]] if fixed_prev is not None else 0) + sum(T[a][b] for a, b in zip(q, q[1:]))
                if cost(new) < cost(seq) - 1e-9:
                    seq, improved = new, True
    return seq


def hhmm(t):
    # review round 2 (R2-09): truncate to the minute, as the Route tab's hh:mm cells display
    t = int(math.floor(t + 1e-6))
    return f"{t // 60:02d}:{t % 60:02d}"


def greedy(g, s0, D):
    seq, rest = [s0], [j for j in g if j != s0]
    while rest:
        nx = min(rest, key=lambda j: D[seq[-1]][j])
        seq.append(nx); rest.remove(nx)
    return seq


def _pretty_street(lab):
    m = re.match(r"^([EW]) (\d+) ST$", lab or "")
    if not m:
        return lab
    k = int(m.group(2))
    suf = "th" if 10 <= k % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(k % 10, "th")
    return f"{'East' if m.group(1) == 'E' else 'West'} {k}{suf} Street"


def entrance_note(x):
    """Review round 2 (R2-10): a corner building's address names the avenue; say so where the founder reads the pin."""
    side = x.get("corner_side_street", "")
    if not side:
        return ""
    ave = re.sub(r"^\d+[A-Za-z]?\s+", "", x.street_address.split(",")[0])
    return (f"Corner building: the address is on {ave}, and the building also fronts {_pretty_street(side)}. "
            f"The pin sits on the {ave} side; check which door takes deliveries.")


# ------------------------------------------------------------------ walk plan
CHECK_BUILDING = ("Lobby type (walk-up, security desk, loading dock); security desk staffed at 8 am? (Y/N); "
                  "loading dock or freight entrance and its posted hours; any COI or vendor-insurance signage; "
                  "posted receiving or delivery hours; candidate names on the lobby directory; photo of the entrance")
CHECK_RETAIL = ("Store open; photo of the local or emerging snack and drink set (aisle and shelf tags); "
                "note which shelf it is in; any 'local' or 'new' shelf signage")
CHECK_COWORK = ("Operator signage in the lobby; floors listed on the directory; front-desk hours; "
                "who receives deliveries for members")


def walk_plan(b, w, r, c):
    """Every Buildings-tab building, every in-boundary coworking site and every retailer,
    in 90-minute sessions. Phase 1 (core) covers everything inside the boundary; phase 2
    (outer) covers retailers outside the line. Each phase is one open tour (nearest neighbour
    plus 2-opt on estimated minutes), cut into sessions of balanced length."""
    stops = {}

    def add(key, kind, ident, name, addr, lat, lon, s, x, dwell, check, phase):
        if key not in stops:
            stops[key] = {"items": [], "street_address": addr, "lat": lat, "lon": lon, "grid_s": s, "grid_x": x,
                          "dwell": 0.0, "checks": [], "kinds": [], "phase": phase}
        st = stops[key]
        st["items"].append(f"{ident} {name}")
        st["dwell"] = max(st["dwell"], dwell) + (1.0 if st["dwell"] else 0.0)
        if check not in st["checks"]:
            st["checks"].append(check)
        st["kinds"].append(kind)
        st["phase"] = min(st["phase"], phase)

    for _, x in b.iterrows():
        n = x.candidate_company_count
        add(x.bbl or x.building_id, "building", x.building_id, x.building_name, x.street_address, x.lat, x.lon, x.grid_s,
            x.grid_x, min(6.0, 3.0 + 0.5 * max(0, n - 1)), "BUILDING: " + CHECK_BUILDING, 1)
        if x.get("entrance_note"):
            stops[x.bbl or x.building_id]["checks"].insert(0, "ENTRANCE: " + x.entrance_note)
    for _, x in w[w.in_boundary == "Y"].iterrows():
        add(x.bbl or x.coworking_id, "coworking", x.coworking_id, x.location_name, x.street_address.split(",")[0], x.lat,
            x.lon, x.grid_s, x.grid_x, 3.0, "COWORKING: " + CHECK_COWORK, 1)
    for _, x in r.iterrows():
        dwell = {"A": 10.0, "B": 6.0, "C": 3.0}.get(x.buy_path_tier, 5.0)
        add(x.bbl or x.retailer_id, "retailer", x.retailer_id, x.retailer_name, x.street_address.split(",")[0], x.lat,
            x.lon, x.grid_s, x.grid_x, dwell, "RETAILER: " + CHECK_RETAIL, 1 if x.inside_boundary == "Y" else 2)
    pace = P["walk_pace_m_per_min"]
    stations = subway_stations()
    rows, sess0, order = [], 1, 0
    for phase in (1, 2):
        S = [s for s in stops.values() if s["phase"] == phase]
        n = len(S)
        T = [[0.0 if i == j else leg_minutes(router.leg(S[i], S[j]), pace) for j in range(n)] for i in range(n)]
        if phase == 1:
            first = min(range(n), key=lambda i: abs(S[i]["grid_s"] - 13.7) + abs(S[i]["grid_x"] - 240) / 79.4)
        else:
            first = min(range(n), key=lambda i: (S[i]["grid_s"], S[i]["grid_x"]))
        tour = [first]
        rest = set(range(n)) - {first}
        while rest:
            nx = min(rest, key=lambda j: T[tour[-1]][j])
            tour.append(nx); rest.remove(nx)
        tour = two_opt_open(tour, T)
        legs = [0.0] + [T[a][b2] for a, b2 in zip(tour, tour[1:])]
        dw = [S[i]["dwell"] for i in tour]
        cuts = balanced_cuts(legs, dw, P["walk_session_cap_min"])
        for k, idx in enumerate(tour):
            st = S[idx]
            sess = sess0 + cuts[k]
            new_session = k == 0 or cuts[k] != cuts[k - 1]
            lm = 0.0 if new_session else legs[k]
            order += 1
            rows.append({"session": sess, "phase": "core (inside the boundary)" if phase == 1 else "outer retailers (within ten blocks)",
                         "order": order, "stops_here": "; ".join(st["items"]),
                         "stop_types": "; ".join(sorted(set(st["kinds"]))), "street_address": st["street_address"],
                         "lat": st["lat"], "lon": st["lon"], "walk_minutes_from_previous_est": round(lm, 1),
                         "dwell_minutes_est": st["dwell"], "verify_checklist": " || ".join(st["checks"]),
                         "observed_lobby_type": "", "security_desk": "", "loading_dock_hours": "", "coi_signage": "",
                         "receiving_hours": "", "emerging_set_photo_taken": "", "founder_notes": "",
                         "_s": st["grid_s"], "_x": st["grid_x"]})
        sess0 = max(rw["session"] for rw in rows) + 1
    walk = pd.DataFrame(rows)
    walk["cumulative_minutes_est"] = walk.groupby("session").apply(
        lambda g: (g.walk_minutes_from_previous_est + g.dwell_minutes_est).cumsum()).reset_index(level=0, drop=True).round(1)
    tot = walk.groupby("session").cumulative_minutes_est.max()
    walk["session_minutes_est"] = walk.session.map(tot)
    starts, ends = {}, {}
    for sid, g in walk.groupby("session"):
        for which, f in (("start", g.iloc[0]), ("end", g.iloc[-1])):
            best = min(stations, key=lambda z: abs(z["s"] - f._s) * 79.4 + abs(z["x"] - f._x))
            dm = abs(best["s"] - f._s) * 79.4 + abs(best["x"] - f._x)
            txt = f"{best['name']} ({best['routes']}), about {max(1, round(dm / pace))} min walk"
            (starts if which == "start" else ends)[sid] = txt
    walk["start_point"] = walk.session.map(starts)
    walk["end_point"] = walk.session.map(ends)
    cols = ["session", "phase", "order", "stops_here", "stop_types", "street_address", "lat", "lon",
            "walk_minutes_from_previous_est", "dwell_minutes_est", "cumulative_minutes_est", "session_minutes_est",
            "start_point", "end_point", "verify_checklist", "observed_lobby_type", "security_desk", "loading_dock_hours",
            "coi_signage", "receiving_hours", "emerging_set_photo_taken", "founder_notes", "_s", "_x"]
    return walk[cols]


def two_opt_open(tour, T):
    n = len(tour)
    improved = True
    while improved:
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                a, b2 = tour[i - 1], tour[i]
                c2 = tour[j]
                d = tour[j + 1] if j + 1 < n else None
                old = T[a][b2] + (T[c2][d] if d is not None else 0)
                new = T[a][c2] + (T[b2][d] if d is not None else 0)
                if new < old - 1e-9:
                    tour[i:j + 1] = reversed(tour[i:j + 1]); improved = True
    return tour


def balanced_cuts(legs, dwell, cap):
    """Session index per stop. Uses the fewest sessions that respect the cap, then the
    smallest per-session limit that still needs no more sessions (balances lengths).
    The leg into a session's first stop is not counted (the founder starts there)."""
    def greedy_cut(limit):
        out, s, acc = [], 0, 0.0
        for k in range(len(dwell)):
            add = (legs[k] if k and acc > 0 else 0.0) + dwell[k]
            if k and acc + add > limit:
                s += 1; acc = dwell[k]
            else:
                acc += add
            out.append(s)
        return out
    base = greedy_cut(cap)
    k_needed = base[-1]
    lo, hi = max(dwell), cap
    for _ in range(40):
        mid = (lo + hi) / 2
        if greedy_cut(mid)[-1] <= k_needed:
            hi = mid
        else:
            lo = mid
    return greedy_cut(hi)


def subway_stations():
    cache = os.path.join(OUT, "subway_cache.json")
    if os.path.exists(cache):
        d = json.load(open(cache))
    else:
        q = urllib.parse.urlencode({"$where": "borough='M' AND gtfs_latitude > 40.725 AND gtfs_latitude < 40.755", "$limit": "300"})
        with urllib.request.urlopen("https://data.ny.gov/resource/39hk-dx4f.json?" + q, timeout=60) as f:
            d = json.load(f)
        json.dump(d, open(cache, "w"), indent=1)
    out = []
    for z in d:
        la, lo = float(z["gtfs_latitude"]), float(z["gtfs_longitude"])
        s, x = grid.sx(la, lo)
        out.append({"name": z["stop_name"], "routes": z.get("daytime_routes", ""), "s": s, "x": x, "lat": la, "lon": lo})
    return out


if __name__ == "__main__":
    main()
