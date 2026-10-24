#!/usr/bin/env python3
"""Numbers quoted in the Method tab, README and REPORT. Writes _build/out/stats.json."""
import json, math, os, sys
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import grid, boundary, router, build
rd = lambda f: pd.read_csv(os.path.join(ROOT, f), dtype=str).fillna("")
c, n, b, w, r, route, walk = (rd(f) for f in ("companies.csv", "near_miss.csv", "buildings.csv", "coworking.csv", "retailers.csv", "route.csv", "walk.csv"))
allc = pd.concat([c, n])
S = {}
S["boundary"] = boundary.area_and_size()
S["boundary"]["corner_walk_min_hand_truck"] = round(S["boundary"]["corner_to_corner_walk_m"] / build.P["hand_truck_pace_m_per_min"])
S["company_rows_total"] = len(allc)
S["company_rows_inside"] = int((allc.in_boundary == "Y").sum())
S["company_rows_outside"] = int((allc.in_boundary == "N").sum())
cand = c[c.candidate_status == "candidate"]
S["candidates"] = len(cand)
S["candidates_by_conf"] = cand.confidence.value_counts().to_dict()
S["candidates_by_band"] = cand.headcount_band.value_counts().to_dict()
S["candidates_conf_band"] = pd.crosstab(cand.confidence, cand.headcount_band).to_dict()
BAND_ORDER = ["40-75", "76-150", "151-250", "251-500", "under-40", "unknown"]
CONF_ORDER = ["high", "medium", "low"]
_xt = pd.crosstab(cand.headcount_band, cand.confidence).reindex(index=BAND_ORDER, columns=CONF_ORDER, fill_value=0)
S["conf_band_table"] = [{"band": bnd, **{k: int(_xt.at[bnd, k]) for k in CONF_ORDER}, "total": int(_xt.loc[bnd].sum())} for bnd in BAND_ORDER]
S["conf_band_table"].append({"band": "all", **{k: int(_xt[k].sum()) for k in CONF_ORDER}, "total": int(_xt.values.sum())})
S["candidates_by_parent"] = cand[cand.parent_company != "unknown"].parent_company.to_dict()
_walked = set(t.split(" ")[0] for v in walk.stops_here for t in v.split(";") if t)
S["walk_coverage"] = {"buildings": f"{len(set(b.building_id) & _walked)} of {len(b)}", "retailers": f"{len(set(r.retailer_id) & _walked)} of {len(r)}",
                      "coworking_inside": f"{len(set(w[w.in_boundary == 'Y'].coworking_id) & _walked)} of {int((w.in_boundary == 'Y').sum())}",
                      "coworking_outside": f"{len(set(w[w.in_boundary == 'N'].coworking_id) & _walked)} of {int((w.in_boundary == 'N').sum())}"}
S["coworking_by_conf_inside"] = w[w.in_boundary == "Y"].confidence.value_counts().to_dict()
S["candidates_by_lease"] = cand.lease_status.value_counts().to_dict()
S["candidates_scope"] = cand.headcount_scope.value_counts().to_dict()
# review round 2: second headcounts, HQ outside New York, parents
banded = cand[cand.headcount_band.isin(["40-75", "76-150", "151-250", "251-500", "under-40"])]
S["candidates_banded"] = len(banded)
S["candidates_by_check"] = cand.headcount_check.value_counts().to_dict()
S["banded_hq_not_nyc"] = int((banded.hq_in_nyc == "N").sum())
S["banded_hq_unknown"] = int((banded.hq_in_nyc == "unknown").sum())
S["candidates_with_parent"] = int((cand.parent_company != "unknown").sum())
S["moved_to_near_miss_r2"] = sorted(n[n.headcount_check == "over-500-second-source"].company_name)
S["occupied_banded"] = int(((banded.lease_status == "occupied")).sum())
S["status_counts"] = allc.candidate_status.value_counts().to_dict()
def area(s):
    s = float(s)
    return "13th-18th St" if s < 18 else "18th-23rd St" if s < 23 else "23rd-26th St" if s < 26 else "26th-30th St"
cand2 = cand.copy(); cand2["area"] = [area(grid.sx(float(a), float(o))[0]) for a, o in zip(cand.lat, cand.lon)]
S["candidates_by_area"] = cand2.area.value_counts().sort_index().to_dict()
S["buildings"] = len(b); S["buildings_lobby"] = b.lobby_type.value_counts().to_dict(); S["buildings_coi"] = b.coi_required.value_counts().to_dict()
S["buildings_with_candidates"] = int((b.candidate_company_count.astype(int) > 0).sum())
S["coworking"] = len(w); S["coworking_inside"] = int((w.in_boundary == "Y").sum())
S["coworking_by_conf"] = w.confidence.value_counts().to_dict(); S["coworking_pantry"] = w.pantry_control.value_counts().to_dict()
S["coworking_status"] = w.status.value_counts().to_dict()
S["retailers"] = len(r); S["retailers_inside"] = int((r.inside_boundary == "Y").sum())
S["retailers_by_tier"] = r.buy_path_tier.value_counts().to_dict(); S["retailers_by_conf"] = r.confidence.value_counts().to_dict()
S["retailers_public"] = int((r.public_map == "Y").sum())
S["retailers_max_blocks"] = int(r.blocks_outside.astype(int).max())
# distance from each candidate building to the nearest tier A store and to the nearest A/B store
sp = grid.model()["spacing_m"]
def pts(df):
    out = []
    for _, x in df.iterrows():
        s, xx = grid.sx(float(x.lat), float(x.lon)); out.append({"street_address": x.street_address, "grid_s": s, "grid_x": xx, "id": x.get("retailer_id", x.get("building_id"))})
    return out
cb = pts(b[b.candidate_company_count.astype(int) > 0])
ra = pts(r[(r.buy_path_tier == "A")]); rab = pts(r[r.public_map == "Y"])
dA = [min(router.leg(p, q)["metres"] for q in ra) / sp for p in cb]
dAB = [min(router.leg(p, q)["metres"] for q in rab) / sp for p in cb]
S["cand_bldg_to_tierA_blocks"] = {"max": round(max(dA), 1), "median": round(sorted(dA)[len(dA) // 2], 1), "share_within_5": round(sum(1 for d in dA if d <= 5) / len(dA), 2)}
S["cand_bldg_to_public_store_blocks"] = {"max": round(max(dAB), 1), "median": round(sorted(dAB)[len(dAB) // 2], 1), "share_within_3": round(sum(1 for d in dAB if d <= 3) / len(dAB), 2)}
# route
legsum = route.leg_minutes_est.astype(float).sum()
S["route"] = {"stops": len(route), "stop_minutes": 15 * len(route), "walking_minutes": round(legsum, 1),
              "total_minutes": round(legsum + 15 * len(route), 1), "end": route.depart_est.iloc[-1],
              "metres": int(route.leg_metres_est.astype(float).sum()),
              "car_faster_legs": int((route.car_faster == "Y").sum()), "longest_leg_min": float(route.leg_minutes_est.astype(float).max()),
              "lobby": route.lobby_type.value_counts().to_dict(), "bands": route.headcount_band.value_counts().to_dict(),
              "at_12_min_stops": round(legsum + 12 * len(route) + route.reload_minutes_before.astype(float).sum(), 1),
              "nine_stops": round(route.leg_minutes_est.astype(float).iloc[:9].sum() + 15 * 9 + route.reload_minutes_before.astype(float).iloc[:9].sum(), 1)}
# review round 2 (R2-06): reloads between loads of build.P["cases_per_load"] cases
rel = float(route.reload_minutes_before.astype(float).sum())
S["route"]["reload_minutes"] = round(rel, 1)
S["route"]["reloads"] = int((route.reload_minutes_before.astype(float) > 0).sum())
S["route"]["cases_per_load"] = int(build.P["cases_per_load"])
S["route"]["total_one_load"] = S["route"]["total_minutes"]
S["route"]["total_minutes"] = round(S["route"]["total_minutes"] + rel, 1)
S["route"]["end_one_load"] = build.hhmm(8 * 60 + S["route"]["total_one_load"])
S["route"]["over_minutes"] = round(S["route"]["total_minutes"] - 180)
S["route"]["over_one_load"] = round(S["route"]["total_one_load"] - 180)
_rl = json.load(open(os.path.join(HERE, "out", "route_legs.json")))
S["route"]["variants"] = _rl.get("variants", {})
S["route"]["rule"] = _rl.get("rule", "")
S["route"]["stop_list"] = [f"{x.stop}. {x.company_name}, {x.street_address} ({x.lobby_type}; {x.headcount_band})" for x in route.itertuples()]
# review round 1 numbers
band4 = ["40-75", "76-150", "151-250", "251-500"]
S["candidates_occupied_banded"] = int(((banded.lease_status == "occupied")).sum())
S["candidates_occupied_banded_4"] = int(((cand.lease_status == "occupied") & cand.headcount_band.isin(band4)).sum())
S["candidates_banded_4"] = int(cand.headcount_band.isin(band4).sum())   # review round 3 (R3-09): 45 banded = 44 in the four bands + 1 under-40
S["candidates_banded_hq"] = banded.hq_in_nyc.value_counts().to_dict()
S["candidates_hq"] = cand.hq_in_nyc.value_counts().to_dict()
S["candidates_under40_founder_call"] = cand[cand.headcount_band == "under-40"].company_name.tolist()
S["near_classes"] = n.near_miss_class.value_counts().to_dict()
S["near_nyc_may_fit"] = int((n.nyc_office_may_fit == "Y").sum())
allpins = pd.concat([c[["notes"]], n[["notes"]], b[["pin_check"]].rename(columns={"pin_check": "notes"}),
                     w[["notes"]], r[["notes"]]])
S["pins_moved_frontage"] = {f: int(d[col].str.contains("Pin moved to frontage at review round 1").sum())
                            for f, d, col in (("companies", c, "notes"), ("near_miss", n, "notes"), ("buildings", b, "pin_check"),
                                              ("coworking", w, "notes"), ("retailers", r, "notes"))}
S["corner_pins"] = {f: int(d[col].str.contains("Review round 2: corner lot").sum())
                     for f, d, col in (("companies", c, "notes"), ("near_miss", n, "notes"), ("buildings", b, "pin_check"),
                                       ("coworking", w, "notes"), ("retailers", r, "notes"))}
S["pins_published_coordinate"] = int(r.notes.str.contains("store's own published coordinate").sum())
S["public_walk_minutes"] = {x.retailer_name: int(x.walk_minutes_from_cluster_edge) for x in r[r.public_map == "Y"].itertuples()}
S["coworking_high_with_second"] = int(((w.confidence == "high") & (w.second_source_url != "")).sum())
S["coworking_high"] = int((w.confidence == "high").sum())
ws = walk.groupby("session").agg(phase=("phase", "first"), stops=("order", "count"), minutes=("session_minutes_est", "first"),
                                 start=("start_point", "first"), end=("end_point", "first"))
# review round 3: session minutes as the Walk tab computes them (sum of the rounded row values, rounded), so the totals agree
_wk = walk.assign(_m=walk.walk_minutes_from_previous_est.astype(float) + walk.dwell_minutes_est.astype(float))
ws["minutes"] = _wk.groupby("session")._m.sum().map(lambda v: int(math.floor(v + 0.5 + 1e-6)))   # half up, as the sheet's ROUND
ws = ws.reindex(sorted(ws.index, key=int))
S["walk"] = {"sessions": int(len(ws)), "total_minutes": round(float(ws.minutes.astype(float).sum())), "stops": int(len(walk)),
             "table": ws.reset_index().to_dict("records"),
             "core_sessions": int((ws.phase.str.startswith("core")).sum()), "outer_sessions": int((ws.phase.str.startswith("outer")).sum()),
             "core_minutes": round(float(ws[ws.phase.str.startswith("core")].minutes.astype(float).sum())),
             "outer_minutes": round(float(ws[ws.phase.str.startswith("outer")].minutes.astype(float).sum()))}
json.dump(S, open(os.path.join(HERE, "out", "stats.json"), "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in S.items() if k not in ("walk",)}, indent=1, default=str)[:4000])
print(json.dumps({k: v for k, v in S["walk"].items() if k != "table"}))
