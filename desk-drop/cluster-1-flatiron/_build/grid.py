#!/usr/bin/env python3
"""Manhattan grid model for cluster 1, calibrated on NYC CSCL street centerlines.

Converts WGS84 lat/lon to two grid coordinates:
  s  = street index (14.0 is the 14th Street centerline, 23.5 is mid-block 23rd to 24th)
  x  = crosstown metres, 0 at the Fifth Avenue centerline, positive to the east
and back. Calibration: every intersection of a numbered street (E/W 10th to 40th) with
a grid avenue, taken from the NYC Street Centerline (CSCL), data.cityofnewyork.us
dataset inkn-q76z, fetched 2026-10-24 into _work/geo/streets_raw.geojson.

Run as a script to (re)build _work/geo/grid_model.json and print residuals.
"""
import json
import math
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEO = os.path.join(ROOT, "_work", "geo")
MODEL = os.path.join(GEO, "grid_model.json")

LAT0 = 40.7400
LON0 = -73.9900
M_PER_DEG_LAT = 111_132.0
M_PER_DEG_LON = 111_320.0 * math.cos(math.radians(LAT0))

AVENUES = {
    "7 AVE": "Seventh Ave",
    "AVE OF THE AMERICAS": "Sixth Ave",
    "5 AVE": "Fifth Ave",
    "MADISON AVE": "Madison Ave",
    "PARK AVE S": "Park Ave S",
    "PARK AVE": "Park Ave",
    "LEXINGTON AVE": "Lexington Ave",
    "IRVING PL": "Irving Pl",
    "3 AVE": "Third Ave",
    "2 AVE": "Second Ave",
    "8 AVE": "Eighth Ave",
    "UNIVERSITY PL": "University Pl",
}
STREET_RE = re.compile(r"^[EW]\s+(\d+)\s+ST$")


def to_m(lat, lon):
    return ((lon - LON0) * M_PER_DEG_LON, (lat - LAT0) * M_PER_DEG_LAT)


def from_m(e, n):
    return (LAT0 + n / M_PER_DEG_LAT, LON0 + e / M_PER_DEG_LON)


def build():
    d = json.load(open(os.path.join(GEO, "streets_raw.geojson")))
    ends = defaultdict(set)  # rounded point -> set of names
    for f in d["features"]:
        name = f["properties"].get("full_street_name", "")
        g = f["geometry"]
        if not g:
            continue
        lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        for line in lines:
            for pt in (line[0], line[-1]):
                ends[(round(pt[0], 5), round(pt[1], 5))].add(name)
    pts = []  # (street_no, avenue, e, n)
    for (lon, lat), names in ends.items():
        # review round 3: sorted, so the pick does not depend on Python's per-process string hashing
        streets = [int(STREET_RE.match(n).group(1)) for n in sorted(names) if STREET_RE.match(n)]
        aves = [AVENUES[n] for n in sorted(names) if n in AVENUES]
        if streets and aves:
            e, n = to_m(lat, lon)
            pts.append((streets[0], aves[0], e, n))
    # keep the grid core
    pts = [p for p in pts if 10 <= p[0] <= 40]
    # rotation angle from avenue lines: fit direction of each avenue's points
    angs = []
    by_ave = defaultdict(list)
    for s, a, e, n in pts:
        by_ave[a].append((s, e, n))
    for a, L in by_ave.items():
        if len(L) < 5 or a in ("Park Ave",):
            continue
        L.sort()
        (s1, e1, n1), (s2, e2, n2) = L[0], L[-1]
        angs.append(math.atan2(e2 - e1, n2 - n1))
    theta = sum(angs) / len(angs)  # clockwise from north, radians
    ux = (math.cos(theta), -math.sin(theta))  # crosstown unit (east-ish)
    uy = (math.sin(theta), math.cos(theta))   # uptown unit
    # street index fit: s = (y - y0) / spacing, least squares
    ys = [(s, e * uy[0] + n * uy[1]) for s, a, e, n in pts]
    k = len(ys)
    ms = sum(s for s, _ in ys) / k
    my = sum(y for _, y in ys) / k
    cov = sum((s - ms) * (y - my) for s, y in ys)
    var = sum((s - ms) ** 2 for s, _ in ys)
    spacing = cov / var  # metres per street
    y0 = my - spacing * ms
    # crosstown: x relative to Fifth Ave mean
    xs = defaultdict(list)
    for s, a, e, n in pts:
        xs[a].append(e * ux[0] + n * ux[1])
    x5 = sum(xs["Fifth Ave"]) / len(xs["Fifth Ave"])
    ave_x = {a: round(sum(v) / len(v) - x5, 1) for a, v in xs.items()}
    model = {
        "theta_deg": math.degrees(theta),
        "ux": ux, "uy": uy, "spacing_m": spacing, "y0": y0, "x5": x5,
        "avenue_x_m": ave_x,
        "n_points": len(pts),
        "source": "NYC Street Centerline (CSCL), data.cityofnewyork.us/resource/inkn-q76z, fetched 2026-10-24",
    }
    res = []
    for s, a, e, n in pts:
        S, X = _sx(model, e, n)
        res.append((abs(S - s), abs(X - ave_x[a]), s, a))
    model["max_street_residual"] = round(max(r[0] for r in res), 3)
    model["mean_street_residual"] = round(sum(r[0] for r in res) / len(res), 3)
    json.dump(model, open(MODEL, "w"), indent=1)
    return model, res, pts


def _sx(m, e, n):
    y = e * m["uy"][0] + n * m["uy"][1]
    x = e * m["ux"][0] + n * m["ux"][1]
    return (y - m["y0"]) / m["spacing_m"], x - m["x5"]


_M = None


def model():
    global _M
    if _M is None:
        _M = json.load(open(MODEL))
    return _M


def sx(lat, lon):
    """lat/lon -> (street index, crosstown metres from Fifth Ave, + east)."""
    m = model()
    e, n = to_m(lat, lon)
    return _sx(m, e, n)


def latlon(s, x):
    """(street index, crosstown metres) -> (lat, lon)."""
    m = model()
    y = s * m["spacing_m"] + m["y0"]
    X = x + m["x5"]
    e = X * m["ux"][0] + y * m["uy"][0]
    n = X * m["ux"][1] + y * m["uy"][1]
    return from_m(e, n)


def ave_x(name):
    return model()["avenue_x_m"][name]


if __name__ == "__main__":
    m, res, pts = build()
    print(json.dumps({k: v for k, v in m.items() if k not in ("ux", "uy")}, indent=1))
    res.sort(reverse=True)
    print("worst street residuals:", res[:8])
