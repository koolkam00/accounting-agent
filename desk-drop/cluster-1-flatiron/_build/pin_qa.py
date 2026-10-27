#!/usr/bin/env python3
"""Check every located row's pin against its address: side of street from house-number
parity, avenue side, distance to the PLUTO lot centroid, and (review round 1, R1-04) the
CSCL block-face test: the pin must be on the addressed side of the street and at least 15 m
nearer the addressed street than the parallel one, and (review round 3, R3-03) the lot test: the pin must sit
inside its own MapPLUTO tax-lot polygon, or within 3 m of it. Writes _build/out/pin_qa.csv."""
import json, math, os, re, sys
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import grid, router, frontage
pl = json.load(open(os.path.join(HERE, "out", "pluto_cache.json")))
LOTS = json.load(open(frontage.LOT_CACHE))
ST = re.compile(r"^\s*(\d+)[A-Za-z]?\s+(East|West)\s+(\d+)(st|nd|rd|th)?\s+Street", re.I)
AV = re.compile(r"^\s*(\d+)[A-Za-z]?\s+(.*)$")
# parity rules: avenue -> which side odd numbers are on (verified against sourced building sides)
ODD_SIDE = {"Fifth Ave": "east", "Sixth Ave": "west", "Park Ave S": "east", "Madison Ave": "east", "Broadway": "west",
            "Third Ave": "east", "Seventh Ave": "east", "Second Ave": "west", "Lexington Ave": "east"}
def check(addr, lat, lon, bbl):
    s, x = grid.sx(float(lat), float(lon))
    out = []
    m = ST.match(addr)
    if m:
        n, ew, k = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        want_north = n % 2 == 1
        if (s > k) != want_north: out.append(f"side: odd/even says {'north' if want_north else 'south'} of {k}th, pin is {'north' if s > k else 'south'}")
        if abs(s - k) > 0.65: out.append(f"pin {s:.2f} is not on {k}th St")
        W_B = [(-311, 5), (-590, -311), (-866, -585), (-1150, -861)]
        E_B = [(-5, 315), (305, 625), (615, 842), (832, 1100)]
        lo, hi = (W_B if ew == "west" else E_B)[min(3, n // 100)]
        if not (lo - 25 <= x <= hi + 25): out.append(f"crosstown {x:.0f} m outside the house-number block ({lo}..{hi})")
    else:
        a = AV.match(addr)
        name = None
        for rx, nm in router.AVE_PATTERNS:
            if rx.search(addr): name = nm; break
        if re.search(r"broadway", addr, re.I): name = "Broadway"
        if name in ODD_SIDE and a:
            n = int(a.group(1))
            ax = router.broadway_x(s) if name == "Broadway" else router.AVE_X[name]
            side = "east" if x > ax else "west"
            want = ODD_SIDE[name] if n % 2 == 1 else ("west" if ODD_SIDE[name] == "east" else "east")
            if side != want: out.append(f"side: {name} {'odd' if n % 2 else 'even'} numbers are on the {want} side, pin is {side}")
            if abs(x - ax) > 130: out.append(f"pin {abs(x - ax):.0f} m from the {name} line")
    p = pl.get(bbl) if bbl else None
    dist = ""
    if p and p.get("latitude"):
        dist = round(math.dist(grid.to_m(float(lat), float(lon)), grid.to_m(float(p["latitude"]), float(p["longitude"]))))
        if dist > 90: out.append(f"PLUTO centroid {dist} m away")
    t = frontage.face(lat, lon, addr)
    face = ""
    if t["testable"]:
        face = f"{t['d_addr']:.0f} m to {t['label']}, {t['d_par']:.0f} m to {t['par_label']}" + (f" (exempt: {t['exempt']})" if t.get("exempt") else "")
        if not t["ok"]:
            out.append("block face: " + ("wrong side of the street" if t["side_ok"] is False else f"only {t['margin']:.0f} m nearer {t['label']} than {t['par_label']}"))
    else:
        face = "not testable: " + t["why"]
    # review round 3 (R3-03): inside its own tax lot, or within 3 m of it
    rings = frontage.lot_rings(LOTS.get(str(bbl).split(".")[0])) if bbl else []
    if rings:
        P = grid.to_m(float(lat), float(lon))
        lot_in = frontage.in_rings(P, rings)
        lot_m = 0.0 if lot_in else round(frontage.dist_rings(P, rings), 1)
        lot = "inside own lot" if lot_in else f"{lot_m} m outside own lot"
        if lot_m > 3.0:
            out.append(f"lot: {lot}")
    else:
        lot = "no lot geometry"
    return "; ".join(out), dist, (p or {}).get("address", ""), face, lot
rows = []
for f, idc, namec in (("companies.csv", "company_id", "company_name"), ("near_miss.csv", "company_id", "company_name"),
                      ("buildings.csv", "building_id", "building_name"), ("coworking.csv", "coworking_id", "location_name"),
                      ("retailers.csv", "retailer_id", "retailer_name")):
    d = pd.read_csv(os.path.join(ROOT, f), dtype=str).fillna("")
    for _, r in d.iterrows():
        issue, dist, pa, face, lot = check(r.street_address.split(",")[0], r.lat, r.lon, r.get("bbl", ""))
        rows.append({"file": f, "id": r[idc], "name": r[namec], "street_address": r.street_address, "lat": r.lat, "lon": r.lon,
                     "pluto_address": pa, "pluto_centroid_m": dist, "block_face": face, "own_lot": lot, "issue": issue})
q = pd.DataFrame(rows)
q.to_csv(os.path.join(HERE, "out", "pin_qa.csv"), index=False)
bad = q[q.issue != ""]
print(len(q), "pins checked;", len(bad), "with an issue;", int((~q.block_face.str.startswith("not testable")).sum()), "block-face tested;",
      int((q.own_lot == "inside own lot").sum()), "inside own lot;", int((q.own_lot == "no lot geometry").sum()), "with no lot geometry")
print(bad[["file", "id", "name", "street_address", "pluto_address", "issue"]].drop_duplicates(subset=["street_address", "issue"]).to_string())
