"""Cluster 1 boundary, defined on the Manhattan street grid (see grid.py).

Grid units: s = street index (14.0 = the 14th Street centreline), x = crosstown metres
from the Fifth Avenue centreline (+ east). One street block = grid.spacing_m (79.4 m).

Rule: both frontages of every edge street and avenue are inside, so a building that
faces the boundary street from the far side still counts. Frontage depth = half the
roadway plus one standard 100 ft (30.5 m) lot:
  Sixth Ave   centreline x = -310.6  -> west line  x = -362  (about 51 m west)
  Park Ave S  centreline x = +311.4  -> east line  x = +376  (about 65 m east; 215 and
              225 Park Ave S have deep through-lots, address points at +359 and +363)
  30th St     centreline s = 30.0    -> north line s = 30.50
  14th St     centreline s = 14.0    -> south line s = 13.45 (14th St is a 100 ft street)
Union Square frame: from University Place (x = +182) to the Third Avenue centreline
(x = +621), everything from the 13th St centreline to the 15th St centreline is inside.
That takes in the square's south frame (Whole Foods, 841-853 Broadway, Zero Irving,
Trader Joe's) and its east frame (the Union Square East block with Target, and Con Ed's
headquarters block), which are the cluster's retail anchor at the plan's southern edge.
"""
import json
import math

import grid

WEST, EAST = -362.0, 376.0
NORTH, SOUTH = 30.50, 13.45
NOTCH_W, NOTCH_E, NOTCH_S, NOTCH_N = 182.0, 621.0, 13.0, 15.0

# polygon in (x, s), clockwise from the north-west corner
POLY_XS = [
    (WEST, NORTH), (EAST, NORTH), (EAST, NOTCH_N), (NOTCH_E, NOTCH_N),
    (NOTCH_E, NOTCH_S), (NOTCH_W, NOTCH_S), (NOTCH_W, SOUTH), (WEST, SOUTH),
]


def inside_xs(x, s):
    if WEST <= x <= EAST and SOUTH <= s <= NORTH:
        return True
    if NOTCH_W <= x <= NOTCH_E and NOTCH_S <= s <= NOTCH_N:
        return True
    return False


def inside(lat, lon):
    s, x = grid.sx(lat, lon)
    return inside_xs(x, s)


def _edge_points(step_m=5.0):
    pts = []
    n = len(POLY_XS)
    for i in range(n):
        (x1, s1), (x2, s2) = POLY_XS[i], POLY_XS[(i + 1) % n]
        dx_m = abs(x2 - x1)
        ds_m = abs(s2 - s1) * grid.model()["spacing_m"]
        k = max(1, int(max(dx_m, ds_m) / step_m))
        for j in range(k + 1):
            t = j / k
            pts.append((x1 + (x2 - x1) * t, s1 + (s2 - s1) * t))
    return pts


_EDGE = None


def blocks_outside(lat, lon):
    """Walking distance from the boundary on the grid, in street blocks (79.4 m).
    0 inside. Crosstown metres count at their length, so the long Sixth-to-Fifth block
    (about 310 m) counts as about 3.9 blocks."""
    global _EDGE
    s, x = grid.sx(lat, lon)
    if inside_xs(x, s):
        return 0.0
    if _EDGE is None:
        _EDGE = _edge_points()
    sp = grid.model()["spacing_m"]
    return min(abs(x - ex) / sp + abs(s - es) for ex, es in _EDGE)


def polygon_lonlat():
    """Exterior ring, counter-clockwise as RFC 7946 section 3.1.6 requires (review round 1, R1-14):
    POLY_XS runs clockwise, so it is reversed here. The grid transform is a rotation, so the
    winding is the same in lon/lat as in (x, s)."""
    ring = [grid.latlon(s, x) for x, s in reversed(POLY_XS)]
    ring = [[round(lon, 6), round(lat, 6)] for lat, lon in ring]
    ring.append(ring[0])
    return ring


def geojson_feature():
    return {
        "type": "Feature",
        "properties": {
            "name": "Cluster 1: Flatiron, NoMad and Union Square",
            "kind": "boundary",
            "rule": "14th St to 30th St, Sixth Ave to Park Ave S, both frontages of each edge street and avenue; plus the Union Square frame from University Pl to Third Ave between the 13th and 15th St centrelines.",
            "drawn": "2026-10-24",
            "grid_source": grid.model()["source"],
        },
        "geometry": {"type": "Polygon", "coordinates": [polygon_lonlat()]},
    }


def area_and_size():
    sp = grid.model()["spacing_m"]
    main = (EAST - WEST) * (NORTH - SOUTH) * sp
    notch = (NOTCH_E - EAST) * (NOTCH_N - NOTCH_S) * sp + (EAST - NOTCH_W) * (SOUTH - NOTCH_S) * sp
    return {
        "area_km2": round((main + notch) / 1e6, 3),
        "north_south_m": round((NORTH - NOTCH_S) * sp),
        "east_west_m": round(EAST - WEST),
        "corner_to_corner_walk_m": round((NORTH - NOTCH_S) * sp + (NOTCH_E - WEST)),
    }


if __name__ == "__main__":
    print(json.dumps(geojson_feature(), indent=1)[:800])
    print(area_and_size())
