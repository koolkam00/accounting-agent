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
