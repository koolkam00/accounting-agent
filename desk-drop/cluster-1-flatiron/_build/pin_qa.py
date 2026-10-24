#!/usr/bin/env python3
"""Check every located row's pin against its address: side of street from house-number
parity, avenue side, and distance to the PLUTO lot centroid. Writes _build/out/pin_qa.csv."""
import json, math, os, re, sys
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import grid, router
pl = json.load(open(os.path.join(HERE, "out", "pluto_cache.json")))
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
    return "; ".join(out), dist, (p or {}).get("address", "")
rows = []
for f, idc, namec in (("companies.csv", "company_id", "company_name"), ("near_miss.csv", "company_id", "company_name"),
                      ("buildings.csv", "building_id", "building_name"), ("coworking.csv", "coworking_id", "location_name"),
                      ("retailers.csv", "retailer_id", "retailer_name")):
    d = pd.read_csv(os.path.join(ROOT, f), dtype=str).fillna("")
    for _, r in d.iterrows():
        issue, dist, pa = check(r.street_address.split(",")[0], r.lat, r.lon, r.get("bbl", ""))
        rows.append({"file": f, "id": r[idc], "name": r[namec], "street_address": r.street_address, "lat": r.lat, "lon": r.lon,
                     "pluto_address": pa, "pluto_centroid_m": dist, "issue": issue})
q = pd.DataFrame(rows)
q.to_csv(os.path.join(HERE, "out", "pin_qa.csv"), index=False)
bad = q[q.issue != ""]
print(len(q), "pins checked;", len(bad), "with an issue")
print(bad[["file", "id", "name", "street_address", "pluto_address", "issue"]].drop_duplicates(subset=["street_address", "issue"]).to_string())
