"""Block-face tests and frontage pins from NYC Street Centerline (CSCL) address ranges.

Added in review round 1 (finding R1-04). A pin must sit on the block face its address
names, so a stranger reading the map walks to the right street:

  side test : the pin is on the side of the addressed street that the CSCL address
              range for that house number names (left or right of the segment).
  face test : the pin is at least FACE_MARGIN_M nearer the addressed street than the
              nearest parallel street (for "W 23rd St": W 22nd and W 24th; for an
              avenue: every other north-south avenue line, Broadway included).

A pin that fails is moved to its frontage: the house number's position along the CSCL
segment (interpolated between the low and high numbers of that side), set back from the
centreline by half the roadway, a 4.6 m (15 ft) sidewalk and 12 m inside the building
line. The tax lot (bbl) never changes.

Source: NYC Street Centerline (CSCL), data.cityofnewyork.us dataset inkn-q76z, fetched
2026-10-24 into _work/geo/streets_raw.geojson (fields stname_label, l_low_hn, l_high_hn,
r_low_hn, r_high_hn, streetwidth in feet).
"""
import json
import math
import os
import re

import grid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FACE_MARGIN_M = 15.0
SIDEWALK_M = 4.6
INSIDE_M = 12.0

AVENUE_LABELS = ["AVE OF THE AMERICAS", "5 AVE", "7 AVE", "8 AVE", "MADISON AVE", "PARK AVE S", "PARK AVE", "BROADWAY",
                 "UNIVERSITY PL", "IRVING PL", "3 AVE", "2 AVE", "LEXINGTON AVE", "UNION SQ W", "UNION SQ E", "4 AVE"]
NAME_MAP = [
    (r"^(avenue of the americas|sixth avenue|6th avenue|sixth ave|6th ave)$", "AVE OF THE AMERICAS"),
    (r"^(fifth avenue|5th avenue|fifth ave|5th ave)$", "5 AVE"),
    (r"^(seventh avenue|7th avenue|seventh ave|7th ave)$", "7 AVE"),
    (r"^(eighth avenue|8th avenue|eighth ave|8th ave)$", "8 AVE"),
    (r"^(third avenue|3rd avenue|third ave|3rd ave)$", "3 AVE"),
    (r"^(second avenue|2nd avenue|second ave|2nd ave)$", "2 AVE"),
    (r"^madison (avenue|ave)$", "MADISON AVE"),
    (r"^park (avenue|ave) (south|s)$", "PARK AVE S"),
    (r"^park (avenue|ave)$", "PARK AVE"),
    (r"^lexington (avenue|ave)$", "LEXINGTON AVE"),
    (r"^broadway$", "BROADWAY"),
    (r"^university (place|pl)$", "UNIVERSITY PL"),
    (r"^irving (place|pl)$", "IRVING PL"),
    (r"^union (square|sq) west$", "UNION SQ W"),
    (r"^union (square|sq) east$", "UNION SQ E"),
]
SIDE_RE = re.compile(r"^(east|west|e\.?|w\.?)\s+(\d+)(st|nd|rd|th)?\s+(street|st)$", re.I)

_SEGS = None
# Lots that front two converging streets, where no pin can be 15 m nearer one than the other
FACE_EXEMPT = {
    "175 Fifth Avenue": "Flatiron Building: a triangular lot between Fifth Ave and Broadway; the pin sits inside the wedge",
}


def segs():
    global _SEGS
    if _SEGS is None:
        d = json.load(open(os.path.join(ROOT, "_work", "geo", "streets_raw.geojson")))
        out = []
        for f in d["features"]:
            p, g = f["properties"], f["geometry"]
            if not g:
                continue
            lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]

            def num(k):
                try:
                    return int(str(p.get(k) or "").split("-")[0])
                except ValueError:
                    return None
            for ln in lines:
                out.append({"label": p.get("stname_label") or "", "rw": p.get("rw_type"),
                            "w_ft": float(p.get("streetwidth") or 0) or None,
                            "l": (num("l_low_hn"), num("l_high_hn")), "r": (num("r_low_hn"), num("r_high_hn")),
                            "pts": [grid.to_m(la, lo) for lo, la in ln]})
        _SEGS = out
    return _SEGS


def parse(addr):
    """'<n> <street>' -> (house number, CSCL label, 'street'|'avenue') or None."""
    a = (addr or "").split(",")[0].strip()
    a = re.sub(r"\s*\(.*\)$", "", a)
    m = re.match(r"^(\d+)(?:-\d+)?[A-Za-z]?\s+(.+)$", a)
    if not m:
        return None
    hn, rest = int(m.group(1)), m.group(2).strip()
    sm = SIDE_RE.match(rest)
    if sm:
        ew = "E" if sm.group(1).lower().startswith("e") else "W"
        return hn, f"{ew} {int(sm.group(2))} ST", "street"
    for rx, lab in NAME_MAP:
        if re.match(rx, rest, re.I):
            return hn, lab, "avenue"
    return None


def _proj(P, A, B):
    dx, dy = B[0] - A[0], B[1] - A[1]
    L2 = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((P[0] - A[0]) * dx + (P[1] - A[1]) * dy) / L2)) if L2 else 0.0
    Q = (A[0] + t * dx, A[1] + t * dy)
    cross = dx * (P[1] - A[1]) - dy * (P[0] - A[0])
    return math.dist(P, Q), t, ("L" if cross > 0 else "R")


def nearest(P, label):
    """(distance, unit direction) of the nearest piece of a named street, or (None, None)."""
    best = None
    for s in segs():
        if s["label"] != label:
            continue
        for A, B in zip(s["pts"], s["pts"][1:]):
            d = _proj(P, A, B)[0]
            if best is None or d < best[0]:
                L = math.dist(A, B) or 1.0
                best = (d, ((B[0] - A[0]) / L, (B[1] - A[1]) / L))
    return best if best else (None, None)


def dist_to(P, label):
    return nearest(P, label)[0]


def beside(P, label, tol_m=5.0):
    """(distance, direction) to the named street, counting only pieces the pin stands beside
    (its perpendicular foot falls on the piece, give or take tol_m). A street that ends at the
    cross street in front of the pin (University Place at 14th St) is not beside it."""
    best = None
    for s in segs():
        if s["label"] != label:
            continue
        for A, B in zip(s["pts"], s["pts"][1:]):
            dx, dy = B[0] - A[0], B[1] - A[1]
            L = math.hypot(dx, dy)
            if not L:
                continue
            t_m = ((P[0] - A[0]) * dx + (P[1] - A[1]) * dy) / L
            if t_m < -tol_m or t_m > L + tol_m:
                continue
            d = _proj(P, A, B)[0]
            if best is None or d < best[0]:
                best = (d, (dx / L, dy / L))
    return best if best else (None, None)


def _parallel(u, v, max_deg=30.0):
    c = abs(u[0] * v[0] + u[1] * v[1])
    return c >= math.cos(math.radians(max_deg))


def parallels(label, kind):
    if kind == "street":
        k = int(label.split()[1])
        return [f"{ew} {j} ST" for j in (k - 1, k + 1) for ew in ("E", "W")]
    same = [{"PARK AVE S", "PARK AVE", "4 AVE", "UNION SQ E"}, {"BROADWAY", "UNION SQ W"}]  # one frontage, two names
    return [x for x in AVENUE_LABELS if x != label and not any(label in g and x in g for g in same)]


def _side_of_range(s, hn):
    """'L' or 'R' when that side's range holds hn. A side counts only when both ends are real
    numbers of hn's parity: CSCL writes 0 as the low end of an unnumbered side (e.g. L 0-199)."""
    for side in ("l", "r"):
        lo, hi = s[side]
        if not lo or not hi:
            continue
        if min(lo, hi) <= hn <= max(lo, hi) and lo % 2 == hn % 2 and hi % 2 == hn % 2:
            return side.upper()
    return None


def address_segments(hn, label):
    out = []
    for s in segs():
        if s["label"] == label:
            side = _side_of_range(s, hn)
            if side:
                out.append((s, side))
    return out


def face(lat, lon, addr):
    """Block-face test for one pin. Returns a dict; testable is False when the address has no CSCL match."""
    pa = parse(addr)
    if not pa or not lat:
        return {"testable": False, "why": "address form not testable"}
    hn, label, kind = pa
    P = grid.to_m(float(lat), float(lon))
    d_addr = dist_to(P, label)
    if d_addr is None:
        return {"testable": False, "why": f"no CSCL street {label}"}
    _, u = nearest(P, label)
    par = []
    for q in parallels(label, kind):
        dq, v = beside(P, q)
        # only a street that runs parallel to the addressed one here counts (Union Square's
        # labels wrap round the park, and Broadway crosses the grid)
        if dq is not None and _parallel(u, v):
            par.append((dq, q))
    d_par, par_label = min(par) if par else (1e9, "")
    # side test on the nearest segment that carries this house number
    side_ok, seg_side, pin_side = None, None, None
    best = None
    for s, side in address_segments(hn, label):
        for A, B in zip(s["pts"], s["pts"][1:]):
            d, t, ps = _proj(P, A, B)
            if best is None or d < best[0]:
                best = (d, side, ps)
    if best:
        _, seg_side, pin_side = best
        side_ok = seg_side == pin_side
    margin = d_par - d_addr
    exempt = FACE_EXEMPT.get(f"{hn} {(addr or '').split(',')[0].split(' ', 1)[1].strip()}", "")
    ok = (margin >= FACE_MARGIN_M or bool(exempt)) and side_ok is not False
    return {"testable": True, "label": label, "kind": kind, "hn": hn, "d_addr": round(d_addr, 1), "d_par": round(d_par, 1),
            "par_label": par_label, "margin": round(margin, 1), "side_ok": side_ok, "ok": ok, "exempt": exempt,
            "range_found": best is not None}


def frontage(addr, lat, lon):
    """Frontage point for an address: (lat, lon, note) or None if CSCL has no range for it.

    Along the street the pin keeps the lot's own position: the current pin (the PLUTO lot
    centroid) is projected onto the CSCL segment that carries this house number. Across the
    street it moves to the address's side, half the roadway plus a 4.6 m sidewalk plus 12 m
    inside the building line from the centreline. Review round 1 tried interpolating the house
    number between the segment's low and high numbers instead, but house numbers are not evenly
    spaced: it put 53 W 23rd St 40 m east of its own lot, so the lot position is used."""
    pa = parse(addr)
    if not pa:
        return None
    hn, label, kind = pa
    cands = address_segments(hn, label)
    if not cands:
        return None
    P0 = grid.to_m(float(lat), float(lon))
    best = None
    for s, side in cands:
        for A, B in zip(s["pts"], s["pts"][1:]):
            d, t, _ = _proj(P0, A, B)
            if best is None or d < best[0]:
                best = (d, s, side, A, B, t)
    d, s, side, A, B, t = best
    L = math.dist(A, B) or 1.0
    dx, dy = (B[0] - A[0]) / L, (B[1] - A[1]) / L
    Q = (A[0] + t * (B[0] - A[0]), A[1] + t * (B[1] - A[1]))
    nx, ny = (-dy, dx) if side == "L" else (dy, -dx)
    w = (s["w_ft"] or (60.0 if kind == "avenue" else 32.0)) * 0.3048
    off = w / 2 + SIDEWALK_M + INSIDE_M
    F = (Q[0] + nx * off, Q[1] + ny * off)
    la, lo = grid.from_m(*F)
    return la, lo, (f"pin moved to frontage: the lot's position along {label} kept, set {off:.0f} m from the centreline "
                    f"on the side CSCL gives house number {hn} ({math.dist(F, P0):.0f} m from the old pin)")


# ------------------------------------------------------------------ review round 2 (R2-10): corner lots
CORNER_SIDE_MIN_M = 26.0   # from the side street's centreline: about half a 60 ft roadway, the sidewalk and 12 m inside
CORNER_INSIDE_M = 4.0      # just inside the avenue building line, so the pin reads as the avenue frontage


def side_streets(P):
    """(distance, label) of the nearest numbered cross streets beside point P (metres)."""
    s, _ = grid.sx(*grid.from_m(*P))
    out = []
    for k in (int(math.floor(s)), int(math.ceil(s))):
        for ew in ("E", "W"):
            d, _ = beside(P, f"{ew} {k} ST")
            if d is not None:
                out.append((d, f"{ew} {k} ST"))
    return sorted(out)


def corner(addr, lat, lon):
    """For an avenue address whose pin sits nearer a cross street than the avenue (a corner lot's
    centroid), return (lat, lon, note, side_label) on the avenue frontage near that corner; else None."""
    pa = parse(addr)
    if not pa or not lat:
        return None
    hn, label, kind = pa
    if kind != "avenue":
        return None
    P0 = grid.to_m(float(lat), float(lon))
    d_addr = dist_to(P0, label)
    sides = side_streets(P0)
    if d_addr is None or not sides or sides[0][0] >= d_addr:
        return None
    d_side, side_label = sides[0]
    cands = address_segments(hn, label)
    if not cands:
        return None
    best = None
    for s, side in cands:
        for A, B in zip(s["pts"], s["pts"][1:]):
            d, t, _ = _proj(P0, A, B)
            if best is None or d < best[0]:
                best = (d, s, side, A, B, t)
    d, s, side, A, B, t = best
    L = math.dist(A, B) or 1.0
    ux, uy = (B[0] - A[0]) / L, (B[1] - A[1]) / L
    Q = (A[0] + t * (B[0] - A[0]), A[1] + t * (B[1] - A[1]))
    nx, ny = (-uy, ux) if side == "L" else (uy, -ux)
    w = (s["w_ft"] or 60.0) * 0.3048
    off = w / 2 + SIDEWALK_M + CORNER_INSIDE_M
    F = (Q[0] + nx * off, Q[1] + ny * off)
    # slide along the avenue, away from the cross street, until the pin is CORNER_SIDE_MIN_M from it
    for _ in range(40):
        ds, _ = beside(F, side_label)
        if ds is None or ds >= CORNER_SIDE_MIN_M:
            break
        G1 = (F[0] + ux * 1.0, F[1] + uy * 1.0)
        G2 = (F[0] - ux * 1.0, F[1] - uy * 1.0)
        F = max((G1, G2), key=lambda G: beside(G, side_label)[0] or 0)
    la, lo = grid.from_m(*F)
    ds_new = beside(F, side_label)[0]
    return la, lo, (f"corner lot: the lot-centroid pin sat {d_side:.0f} m from {side_label} but {d_addr:.0f} m from {label}, "
                    f"so it was moved to the {label} frontage near the corner ({off:.0f} m from the {label} centreline, "
                    f"{ds_new:.0f} m from {side_label}; {math.dist(F, P0):.0f} m from the old pin)"), side_label


# ------------------------------------------------------------------ review round 3 (R3-03): keep the pin on its own tax lot
# The round-2 corner rule (26 m from the cross street) could push a pin past a short corner lot onto the neighbour's
# frontage. Every pin now has to sit inside its own MapPLUTO lot polygon. A pin outside it moves to the lot's frontage
# on the addressed street, LOT_INSIDE_M inside the lot line: the middle of that frontage for a corner lot whose frontage is
# LONG_FRONTAGE_M or shorter, else the nearest point that keeps CORNER_SIDE_MIN_M from the cross street; for any other
# pin, the frontage point nearest the old pin. The tax lot (bbl) never changes.
LOT_INSIDE_M = 3.0
LONG_FRONTAGE_M = 35.0
LOT_CACHE = os.path.join(HERE, "out", "lots_cache.json")
LOT_SOURCE = ("NYC MapPLUTO (Department of City Planning) tax-lot polygons, version 26v2, from the public "
              "planninglabs.carto.com SQL endpoint that ZoLa uses, fetched 2026-10-24")


def lots(bbls):
    """MapPLUTO lot polygons by bbl (GeoJSON geometry), cached in _build/out/lots_cache.json. GET only."""
    import subprocess
    import urllib.parse
    have = json.load(open(LOT_CACHE)) if os.path.exists(LOT_CACHE) else {}
    need = sorted({str(b).split(".")[0] for b in bbls if b and str(b).split(".")[0].isdigit()} - set(have))
    for k in range(0, len(need), 40):
        chunk = need[k:k + 40]
        q = "SELECT bbl,address,version,the_geom FROM dcp_mappluto WHERE bbl IN (%s)" % ",".join(chunk)
        url = "https://planninglabs.carto.com/api/v2/sql?format=geojson&q=" + urllib.parse.quote(q)
        out = subprocess.run(["curl", "-sS", "--max-time", "90", "-A", "cluster-research-script/0.1", url],
                             capture_output=True, text=True).stdout
        got = {str(int(f["properties"]["bbl"])): {"address": f["properties"].get("address"), "version": f["properties"].get("version"),
                                                  "geometry": f["geometry"]} for f in json.loads(out)["features"]}
        for b in chunk:
            have[b] = got.get(b)
    json.dump(have, open(LOT_CACHE, "w"))
    return have


def lot_rings(lot):
    """Outer rings of a lot, in grid metres."""
    if not lot or not lot.get("geometry"):
        return []
    g = lot["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    return [[grid.to_m(la, lo) for lo, la in poly[0]] for poly in polys]


def in_rings(P, rings):
    ins = False
    for ring in rings:
        for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
            if (y1 > P[1]) != (y2 > P[1]) and P[0] < (x2 - x1) * (P[1] - y1) / (y2 - y1) + x1:
                ins = not ins
    return ins


def dist_rings(P, rings):
    best = None
    for ring in rings:
        for A, B in zip(ring, ring[1:]):
            d = _proj(P, A, B)[0]
            best = d if best is None or d < best else best
    return best if best is not None else 1e9


def lot_frontage(rings, label):
    """The lot's frontage on the addressed street: (F0, F1, u, n_in, length) in metres, or None.
    Frontage edges run parallel to the street (within 30 degrees) and are the lot edges nearest its centreline."""
    edges = []
    for ring in rings:
        for A, B in zip(ring, ring[1:]):
            L = math.dist(A, B)
            if L < 0.5:
                continue
            M = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
            d, u = nearest(M, label)
            if d is None:
                continue
            e = ((B[0] - A[0]) / L, (B[1] - A[1]) / L)
            if _parallel(e, u):
                edges.append((d, A, B, u))
    if not edges:
        return None
    dmin = min(e[0] for e in edges)
    if dmin > 45.0:   # the lot does not front this street
        return None
    front = [e for e in edges if e[0] <= dmin + 3.0]
    u = front[0][3]
    n = (-u[1], u[0])
    pts = [p for e in front for p in (e[1], e[2])]
    O = pts[0]
    ts = [(p[0] - O[0]) * u[0] + (p[1] - O[1]) * u[1] for p in pts]
    ns = [(p[0] - O[0]) * n[0] + (p[1] - O[1]) * n[1] for p in pts]
    t0, t1, nn = min(ts), max(ts), sum(ns) / len(ns)
    F0 = (O[0] + u[0] * t0 + n[0] * nn, O[1] + u[1] * t0 + n[1] * nn)
    F1 = (O[0] + u[0] * t1 + n[0] * nn, O[1] + u[1] * t1 + n[1] * nn)
    allp = [p for ring in rings for p in ring]
    C = (sum(p[0] for p in allp) / len(allp), sum(p[1] for p in allp) / len(allp))
    side = (C[0] - F0[0]) * n[0] + (C[1] - F0[1]) * n[1]
    n_in = n if side > 0 else (-n[0], -n[1])
    return F0, F1, u, n_in, t1 - t0


def clamp_to_lot(addr, lat, lon, lot, corner_side=""):
    """(lat, lon, note) when the pin lies outside its own lot, else None. See the block comment above."""
    rings = lot_rings(lot)
    if not rings or not lat:
        return None
    P = grid.to_m(float(lat), float(lon))
    if in_rings(P, rings):
        return None
    out_m = dist_rings(P, rings)
    pa = parse(addr)
    fr = lot_frontage(rings, pa[1]) if pa else None
    if fr:
        F0, F1, u, n_in, length = fr
        tP = (P[0] - F0[0]) * u[0] + (P[1] - F0[1]) * u[1]
        lo_t, hi_t = (LOT_INSIDE_M, length - LOT_INSIDE_M) if length > 2 * LOT_INSIDE_M else (length / 2, length / 2)
        how = ""
        if corner_side and length <= LONG_FRONTAGE_M:
            t = length / 2
            how = f"the middle of the lot's {length:.0f} m {pa[1]} frontage"
        elif corner_side:
            ok = [k * 0.5 for k in range(int(lo_t * 2), int(hi_t * 2) + 1)
                  if (beside((F0[0] + u[0] * k * 0.5, F0[1] + u[1] * k * 0.5), corner_side)[0] or 0) >= CORNER_SIDE_MIN_M]
            t = min(ok, key=lambda k: abs(k - tP)) if ok else length / 2
            how = (f"the point of the lot's {length:.0f} m {pa[1]} frontage nearest the old pin that is at least "
                   f"{CORNER_SIDE_MIN_M:.0f} m from {corner_side}") if ok else f"the middle of the lot's {length:.0f} m {pa[1]} frontage"
        else:
            t = min(max(tP, lo_t), hi_t)
            how = f"the point of the lot's {length:.0f} m {pa[1]} frontage nearest the old pin"
        Q = (F0[0] + u[0] * t, F0[1] + u[1] * t)
        for inset in (LOT_INSIDE_M, 5.0, 8.0, 12.0):
            Qi = (Q[0] + n_in[0] * inset, Q[1] + n_in[1] * inset)
            if in_rings(Qi, rings):
                la, lo = grid.from_m(*Qi)
                return la, lo, (f"Review round 3: the pin sat {out_m:.1f} m outside its own tax lot ({LOT_SOURCE.split(',')[0]}), "
                                f"so it was moved to {how}, {inset:.0f} m inside the lot line ({math.dist(Qi, P):.0f} m from the old pin). Tax lot unchanged.")
    # no frontage on the addressed street (an address form CSCL cannot test, such as Union Square South): the point
    # inside the lot, at least LOT_INSIDE_M from every lot line, nearest the old pin (1 m search grid)
    xs = [p[0] for ring in rings for p in ring]; ys = [p[1] for ring in rings for p in ring]
    best = None
    for gx in range(int(min(xs)), int(max(xs)) + 1):
        for gy in range(int(min(ys)), int(max(ys)) + 1):
            G = (float(gx), float(gy))
            if in_rings(G, rings) and dist_rings(G, rings) >= LOT_INSIDE_M:
                d = math.dist(G, P)
                if best is None or d < best[0]:
                    best = (d, G)
    if best is None:
        return None
    la, lo = grid.from_m(*best[1])
    return la, lo, (f"Review round 3: the pin sat {out_m:.1f} m outside its own tax lot ({LOT_SOURCE.split(',')[0]}), "
                    f"so it was moved to the nearest point {LOT_INSIDE_M:.0f} m inside the lot line ({best[0]:.0f} m from the old pin). Tax lot unchanged.")
