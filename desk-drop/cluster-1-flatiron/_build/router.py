"""Walking legs on the Manhattan grid, in grid coordinates (s = street index, x = crosstown m).

Each stop gets a sidewalk anchor from its street address:
  "<n> East|West <k>th Street"  -> on the <k>th St line, on the building's side
  "<n> Fifth Avenue" etc.        -> on that avenue's line, on the building's side
  Broadway / squares / other     -> the address point itself (Broadway is diagonal)
A leg follows the grid: along the origin's street or avenue, turn once or twice, arrive
along the destination's street or avenue. Distance is the polyline length on the grid.
Signal crossings are counted per street line and avenue line crossed.
"""
import re

import grid

AVE_X = {  # crosstown metres from Fifth Ave, from NYC CSCL intersections (grid.py)
    "Seventh Ave": -585.0, "Sixth Ave": -310.6, "Fifth Ave": 0.0, "Madison Ave": 152.0,
    "Park Ave S": 311.4, "Lexington Ave": 465.0, "Irving Pl": 472.3, "Third Ave": 621.1,
    "Second Ave": 837.5, "University Pl": 182.0, "Union Sq W": 190.0,
}
# Broadway x by street index (CSCL intersections)
BWAY = [(10.0, 399), (11.0, 374), (12.0, 345), (13.0, 314), (14.16, 281), (15.2, 245), (16.2, 215),
        (17.18, 188), (18.09, 167), (19.02, 141), (19.97, 117), (20.9, 94), (21.89, 68), (22.97, 45),
        (24.99, -49), (25.99, -79), (26.97, -109), (27.95, -140), (28.94, -171), (29.94, -202),
        (30.92, -232), (31.91, -264), (32.88, -294), (33.94, -332)]

SP = None


def sp():
    global SP
    if SP is None:
        SP = grid.model()["spacing_m"]
    return SP


def broadway_x(s):
    if s <= BWAY[0][0]:
        return BWAY[0][1]
    for (s1, x1), (s2, x2) in zip(BWAY, BWAY[1:]):
        if s1 <= s <= s2:
            return x1 + (x2 - x1) * (s - s1) / (s2 - s1)
    return BWAY[-1][1]


def avenues_at(s):
    """Avenue lines that exist at street index s (x positions)."""
    xs = [AVE_X["Seventh Ave"], AVE_X["Sixth Ave"], AVE_X["Fifth Ave"], AVE_X["Park Ave S"],
          AVE_X["Third Ave"], AVE_X["Second Ave"]]
    if s >= 23:
        xs.append(AVE_X["Madison Ave"])
    if s >= 21:
        xs.append(AVE_X["Lexington Ave"])
    elif s >= 14:
        xs.append(AVE_X["Irving Pl"])
    if s < 14.2:
        xs.append(AVE_X["University Pl"])
    if 14 <= s <= 33.9:
        xs.append(broadway_x(s))
    return xs


STREET_RE = re.compile(r"^\s*\d+[A-Za-z]?\s+(East|West|E\.?|W\.?)\s+(\d+)(st|nd|rd|th)?\s+(Street|St)", re.I)
AVE_PATTERNS = [
    (re.compile(r"avenue of the americas|sixth ave|6th ave", re.I), "Sixth Ave"),
    (re.compile(r"fifth ave|5th ave", re.I), "Fifth Ave"),
    (re.compile(r"madison ave", re.I), "Madison Ave"),
    (re.compile(r"park ave(nue)? s", re.I), "Park Ave S"),
    (re.compile(r"lexington", re.I), "Lexington Ave"),
    (re.compile(r"irving pl", re.I), "Irving Pl"),
    (re.compile(r"third ave|3rd ave", re.I), "Third Ave"),
    (re.compile(r"second ave|2nd ave", re.I), "Second Ave"),
    (re.compile(r"seventh ave|7th ave", re.I), "Seventh Ave"),
    (re.compile(r"university pl", re.I), "University Pl"),
]


def anchor(address, s, x):
    """Return (kind, line, s_anchor, x_anchor). kind: street | avenue | free."""
    m = STREET_RE.match(address or "")
    if m:
        k = int(m.group(2))
        side = 1 if s > k else -1
        return ("street", k, k + side * 0.12, x)
    for rx, name in AVE_PATTERNS:
        if rx.search(address or ""):
            ax = AVE_X[name]
            side = 1 if x > ax else -1
            return ("avenue", ax, s, ax + side * 12)
    return ("free", None, s, x)


def _cross_avenues(s, x1, x2):
    lo, hi = sorted((x1, x2))
    return sum(1 for ax in avenues_at(s) if lo + 1 < ax < hi - 1)


def _cross_streets(s1, s2):
    lo, hi = sorted((s1, s2))
    return sum(1 for k in range(int(lo) - 1, int(hi) + 2) if lo < k < hi)


def leg(a, b):
    """a, b: dicts with street_address, grid_s, grid_x. Returns dict with path (s,x list),
    metres, avenue_crossings, street_crossings."""
    ka, la, sa, xa = anchor(a["street_address"], a["grid_s"], a["grid_x"])
    kb, lb, sb, xb = anchor(b["street_address"], b["grid_s"], b["grid_x"])
    P = [(a["grid_s"], a["grid_x"]), (sa, xa)]
    if abs(sa - sb) < 1e-6 and abs(xa - xb) < 1e-6:
        pass
    elif ka == "avenue" and kb == "avenue" and la == lb:
        P += [(sb, xb)]
    elif ka in ("street", "free") and kb in ("street", "free"):
        same_street = ka == kb == "street" and la == lb and abs(sa - sb) < 0.05
        if same_street:
            P += [(sb, xb)]
        else:
            # walk along A's street to the best avenue, up/down it, then along B's street
            cand = avenues_at((sa + sb) / 2)
            xt = min(cand, key=lambda ax: abs(xa - ax) + abs(ax - xb) + 0.001 * abs(ax - xb))
            P += [(sa, xt), (sb, xt), (sb, xb)]
    elif ka in ("street", "free") and kb == "avenue":
        P += [(sa, xb), (sb, xb)]
    elif ka == "avenue" and kb in ("street", "free"):
        P += [(sb, xa), (sb, xb)]
    else:  # two different avenues: cross at the street nearest B
        ks = [k for k in range(int(min(sa, sb)), int(max(sa, sb)) + 2) if min(sa, sb) <= k <= max(sa, sb)]
        st = min(ks, key=lambda k: abs(k - sb)) if ks else round((sa + sb) / 2)
        st = st + (0.12 if sb > st else -0.12)
        P += [(st, xa), (st, xb), (sb, xb)]
    P.append((b["grid_s"], b["grid_x"]))
    # clean duplicates
    Q = [P[0]]
    for p in P[1:]:
        if abs(p[0] - Q[-1][0]) > 1e-6 or abs(p[1] - Q[-1][1]) > 1e-6:
            Q.append(p)
    metres, ave_c, st_c = 0.0, 0, 0
    for (s1, x1), (s2, x2) in zip(Q, Q[1:]):
        metres += abs(x2 - x1) + abs(s2 - s1) * sp()
        if abs(x2 - x1) > 1:
            ave_c += _cross_avenues((s1 + s2) / 2, x1, x2)
        if abs(s2 - s1) > 0.01:
            st_c += _cross_streets(s1, s2)
    return {"path": Q, "metres": metres, "avenue_crossings": ave_c, "street_crossings": st_c}


def path_lonlat(path):
    out = []
    for s, x in path:
        la, lo = grid.latlon(s, x)
        out.append([round(lo, 6), round(la, 6)])
    return out
