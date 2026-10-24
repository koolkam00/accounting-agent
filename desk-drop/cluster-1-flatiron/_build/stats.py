#!/usr/bin/env python3
"""Numbers quoted in the Method tab, README and REPORT. Writes _build/out/stats.json."""
import json, os, sys
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
S["candidates_by_lease"] = cand.lease_status.value_counts().to_dict()
S["candidates_scope"] = cand.headcount_scope.value_counts().to_dict()
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
              "at_12_min_stops": round(legsum + 12 * len(route), 1),
              "nine_stops": round(route.leg_minutes_est.astype(float).iloc[:9].sum() + 15 * 9, 1)}
ws = walk.groupby("session").agg(phase=("phase", "first"), stops=("order", "count"), minutes=("session_minutes_est", "first"),
                                 start=("start_point", "first"), end=("end_point", "first"))
S["walk"] = {"sessions": int(len(ws)), "total_minutes": round(float(ws.minutes.astype(float).sum())), "stops": int(len(walk)),
             "table": ws.reset_index().to_dict("records"),
             "core_sessions": int((ws.phase.str.startswith("core")).sum()), "outer_sessions": int((ws.phase.str.startswith("outer")).sum()),
             "core_minutes": round(float(ws[ws.phase.str.startswith("core")].minutes.astype(float).sum())),
             "outer_minutes": round(float(ws[ws.phase.str.startswith("outer")].minutes.astype(float).sum()))}
json.dump(S, open(os.path.join(HERE, "out", "stats.json"), "w"), indent=1, default=str)
print(json.dumps({k: v for k, v in S.items() if k not in ("walk",)}, indent=1, default=str)[:4000])
print(json.dumps({k: v for k, v in S["walk"].items() if k != "table"}))
