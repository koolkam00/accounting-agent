#!/usr/bin/env python3
"""Build the website's retailer map from the cluster workstream's public map.

Reads (all from ../cluster-1-flatiron/, workstream B):
  map-public.geojson               the boundary polygon and the public retailer points (required)
  _work/geo/streets_raw.geojson    NYC Street Centerline (CSCL) segments, for the street grid (optional)
  _work/geo/parks_raw.geojson      NYC Parks Properties, for the park shapes (optional)
  _work/geo/grid_model.json        B's rotation of the Manhattan grid, so avenues run up the page

Writes:
  site/assets/img/cluster-map.svg  a static map drawn from coordinates (no tiles, no API keys)
  site/brands.html                 the numbered store list, between <!-- MAP:START --> and <!-- MAP:END -->
  site/offices.html                the map figure only, between the same markers

Run from website/:  python3 tools/build_map.py
Re-run it whenever B updates map-public.geojson. The site itself needs no build step;
this only refreshes one image and one list.
"""
import html
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(HERE)
B = os.path.join(os.path.dirname(WEB), "cluster-1-flatiron")
SITE = os.path.join(WEB, "site")
OUT_SVG = os.path.join(SITE, "assets", "img", "cluster-map.svg")

LAT0, LON0 = 40.7400, -73.9900
M_LAT = 111_132.0
M_LON = 111_320.0 * math.cos(math.radians(LAT0))
FALLBACK_MODEL = {"ux": [0.8708604386447605, -0.49153036162932545], "uy": [0.49153036162932545, 0.8708604386447605],
                  "spacing_m": 79.35570477694782, "y0": -1653.7599731639134, "x5": -55.70962257190264,
                  "avenue_x_m": {"Seventh Ave": -585.0, "Sixth Ave": -310.6, "Fifth Ave": 0.0, "Madison Ave": 149.8,
                                 "Park Ave S": 311.4, "Lexington Ave": 462.5, "Third Ave": 621.1, "Second Ave": 837.5}}
AVE_LABELS = [("Seventh Ave", "7th Ave"), ("Sixth Ave", "6th Ave"), ("Fifth Ave", "5th Ave"), ("Madison Ave", "Madison"),
              ("Park Ave S", "Park Ave S"), ("Lexington Ave", "Lex"), ("Third Ave", "3rd Ave"), ("Second Ave", "2nd Ave")]
BIG_STREETS = {"5 AVE", "AVE OF THE AMERICAS", "7 AVE", "PARK AVE S", "PARK AVE", "BROADWAY", "MADISON AVE", "LEXINGTON AVE",
               "3 AVE", "2 AVE", "E  14 ST", "W  14 ST", "E  23 ST", "W  23 ST", "E  34 ST", "W  34 ST", "UNIVERSITY PL", "IRVING PL"}
PX_PER_M = 0.34
MARGIN_M = 60
TOP, LEFT, BOTTOM, RIGHT = 34, 44, 44, 10   # px reserved for labels and the scale bar

INK, STONE, COBALT, TINT, PAPER, STREET, STREET_BIG, PARK = "#1F1D1A", "#5C5850", "#2E47C9", "#E3E8FB", "#F7F3EA", "#E4DCCD", "#D3C8B4", "#DCE8D2"


def load(path, required=False):
    if not os.path.exists(path):
        if required:
            sys.exit("missing " + path + " (the cluster workstream has not published it yet; keep the labeled slot)")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def make_proj(model):
    ux, uy = model["ux"], model["uy"]

    def grid(lon, lat):
        e, n = (lon - LON0) * M_LON, (lat - LAT0) * M_LAT
        X = e * ux[0] + n * ux[1]
        Y = e * uy[0] + n * uy[1]
        return X - model["x5"], Y          # x: metres east of Fifth Ave; Y: metres up the avenues
    return grid


def ordinal(n):
    return str(n) + ("th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


def main():
    pub = load(os.path.join(B, "map-public.geojson"), required=True)
    model = load(os.path.join(B, "_work", "geo", "grid_model.json")) or FALLBACK_MODEL
    streets = load(os.path.join(B, "_work", "geo", "streets_raw.geojson"))
    parks = load(os.path.join(B, "_work", "geo", "parks_raw.geojson"))
    grid = make_proj(model)
    spacing, y0 = model["spacing_m"], model["y0"]

    boundary = None
    stores = []
    for f in pub["features"]:
        g, p = f["geometry"], f["properties"]
        if g["type"] == "Polygon" and p.get("kind") == "boundary":
            boundary = [grid(lon, lat) for lon, lat in g["coordinates"][0]]
        elif g["type"] == "Point" and p.get("kind") == "retailer":
            x, y = grid(*g["coordinates"][:2])
            stores.append({"x": x, "y": y, "name": p.get("name", ""), "address": p.get("address", ""),
                           "tier": p.get("buy_path_tier", ""), "inside": p.get("inside_boundary") == "Y",
                           "blocks": int(p.get("blocks_outside") or 0), "as_of": p.get("as_of", ""), "id": p.get("retailer_id", ""),
                           "map_number": int(p["map_number"]) if str(p.get("map_number", "")).isdigit() else None})
    if not boundary:
        sys.exit("no boundary polygon in map-public.geojson")
    as_of = sorted({s["as_of"] for s in stores if s["as_of"]})
    # Use the cluster workstream's own numbers (map_number) when present, so the site, B's map and
    # D's proposal agree. Otherwise: inside the cluster first, then by blocks outside, north to south.
    if all(s["map_number"] for s in stores):
        stores.sort(key=lambda s: s["map_number"])
        for s in stores:
            s["n"] = s["map_number"]
    else:
        stores.sort(key=lambda s: (0 if s["inside"] else 1, s["blocks"], -s["y"]))
        for i, s in enumerate(stores, 1):
            s["n"] = i

    xs = [p[0] for p in boundary] + [s["x"] for s in stores]
    ys = [p[1] for p in boundary] + [s["y"] for s in stores]
    x_min, x_max = min(xs) - MARGIN_M, max(xs) + MARGIN_M
    y_min, y_max = min(ys) - MARGIN_M, max(ys) + MARGIN_M
    W = round((x_max - x_min) * PX_PER_M) + LEFT + RIGHT
    H = round((y_max - y_min) * PX_PER_M) + TOP + BOTTOM

    def P(x, y):
        return (LEFT + (x - x_min) * PX_PER_M, TOP + (y_max - y) * PX_PER_M)

    def inside_box(x, y, pad=0):
        return x_min - pad <= x <= x_max + pad and y_min - pad <= y <= y_max + pad

    out = []
    a = out.append
    a('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="Atkinson Hyperlegible Next, Arial, Helvetica, sans-serif">' % (W, H, W, H))
    a('<title>Map of the Flatiron, NoMad and Union Square office cluster with nearby food stores</title>')
    a('<rect width="%d" height="%d" fill="%s"/>' % (W, H, PAPER))
    mx0, my0 = P(x_min, y_max)
    mx1, my1 = P(x_max, y_min)
    a('<clipPath id="c"><rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" rx="6"/></clipPath>' % (mx0, my0, mx1 - mx0, my1 - my0))
    a('<g clip-path="url(#c)">')
    a('<rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" fill="#FFFFFF"/>' % (mx0, my0, mx1 - mx0, my1 - my0))

    # Parks (NYC Parks Properties), only those at least 0.3 acres, to keep it calm.
    if parks:
        for f in parks["features"]:
            try:
                if float(f["properties"].get("acres") or 0) < 0.3:
                    continue
            except ValueError:
                continue
            g = f["geometry"]
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            for poly in polys:
                ring = [grid(lon, lat) for lon, lat in poly[0]]
                if not any(inside_box(x, y, 50) for x, y in ring):
                    continue
                d = "M" + "L".join("%.0f %.0f" % P(x, y) for x, y in ring) + "Z"
                a('<path d="%s" fill="%s"/>' % (d, PARK))

    # Streets (NYC CSCL), drawn as two merged paths: ordinary and major.
    if streets:
        small, big = [], []
        for f in streets["features"]:
            p, g = f["properties"], f["geometry"]
            if not g or p.get("rw_type") != "1":
                continue
            lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
            name = p.get("full_street_name", "")
            for line in lines:
                pts = [grid(lon, lat) for lon, lat in line]
                if not any(inside_box(x, y, 120) for x, y in pts):
                    continue
                seg = "M" + "L".join("%.0f %.0f" % P(x, y) for x, y in pts)
                (big if name in BIG_STREETS else small).append(seg)
        a('<path d="%s" fill="none" stroke="%s" stroke-width="3" stroke-linecap="round"/>' % ("".join(small), STREET))
        a('<path d="%s" fill="none" stroke="%s" stroke-width="5" stroke-linecap="round"/>' % ("".join(big), STREET_BIG))

    # The cluster boundary.
    d = "M" + "L".join("%.1f %.1f" % P(x, y) for x, y in boundary) + "Z"
    a('<path d="%s" fill="%s" fill-opacity="0.72" stroke="%s" stroke-width="3" stroke-linejoin="round"/>' % (d, TINT, COBALT))

    # Neighborhood labels, placed on the grid: (street index, crosstown metres east of Fifth).
    def at(s_idx, x_m):
        return P(x_m, s_idx * spacing + y0)
    for label, s_idx, x_m in [("NOMAD", 28.3, -150), ("FLATIRON", 20.5, -150), ("UNION SQ", 13.6, 470)]:
        x, y = at(s_idx, x_m)
        a('<text x="%.0f" y="%.0f" font-size="15" font-weight="700" fill="%s" text-anchor="middle" letter-spacing="2">%s</text>' % (x, y, COBALT, label))
    for lines, s_idx, x_m in [(("Madison", "Sq Park"), 24.6, 75), (("Union", "Square"), 15.6, 245)]:
        x, y = at(s_idx, x_m)
        a('<text x="%.0f" y="%.0f" font-size="11" font-weight="700" fill="#3F5E36" text-anchor="middle"><tspan x="%.0f">%s</tspan><tspan x="%.0f" dy="13">%s</tspan></text>' % (x, y, x, lines[0], x, lines[1]))
    x, y = at(21.3, 40)
    a('<text x="%.0f" y="%.0f" font-size="11" font-weight="700" fill="%s" transform="rotate(-71 %.0f %.0f)">Broadway</text>' % (x, y, STONE, x, y))
    a('</g>')
    a('<rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" rx="6" fill="none" stroke="#D3C8B4"/>' % (mx0, my0, mx1 - mx0, my1 - my0))

    # Avenue labels along the top, street numbers down the left.
    av = model.get("avenue_x_m", FALLBACK_MODEL["avenue_x_m"])
    placed = []
    for key, label in AVE_LABELS:
        if key not in av:
            continue
        x, _ = P(av[key], 0)
        half = len(label) * 3.6  # about half the label width at 13px bold
        if mx0 + half < x < mx1 - half and all(abs(x - qx) > half + qh + 8 for qx, qh in placed):
            placed.append((x, half))
            a('<text x="%.0f" y="%d" font-size="13" font-weight="700" fill="%s" text-anchor="middle">%s</text>' % (x, TOP - 10, STONE, label))
    s_lo = math.ceil((y_min - y0) / spacing)
    s_hi = math.floor((y_max - y0) / spacing)
    rows = []
    for s_idx in range(s_lo, s_hi + 1):
        if s_idx not in (8, 10, 12, 14, 16, 18, 20, 23, 26, 28, 30, 32):
            continue
        _, y = P(0, s_idx * spacing + y0)
        if my0 + 10 < y < my1 - 6:
            rows.append((y, s_idx))
    for y, s_idx in rows:
        # Street numbers only ("30th", "28th"): the old "St" header above them read as a clipped label.
        a('<text x="%d" y="%.0f" font-size="13" font-weight="700" fill="%s" text-anchor="end">%s</text>' % (LEFT - 6, y + 4, STONE, ordinal(s_idx)))

    # Store markers.
    for s in stores:
        x, y = P(s["x"], s["y"])
        filled = s["tier"] == "A"
        a('<circle cx="%.0f" cy="%.0f" r="11" fill="%s" stroke="%s" stroke-width="2.5"/>' % (x, y, COBALT if filled else "#FFFFFF", COBALT))
        a('<text x="%.0f" y="%.0f" font-size="%d" font-weight="700" fill="%s" text-anchor="middle">%d</text>' % (x, y + 4.5, 13 if s["n"] < 10 else 11.5, "#FFFFFF" if filled else COBALT, s["n"]))

    # True-north arrow (the map is turned about 29 degrees so the avenues run up the page) and scale bar.
    theta = math.degrees(math.atan2(model["ux"][1], model["ux"][0]))  # about -29
    # A conventional north arrow: a shaft with an arrowhead, turned to true north, with an upright "N"
    # just beyond the tip, on a small white disc so it reads over the streets.
    nx, ny = mx0 + 34, my0 + 44
    a('<circle cx="%.0f" cy="%.0f" r="28" fill="#FFFFFF" fill-opacity="0.92" stroke="#D3C8B4"/>' % (nx, ny))
    a('<g transform="translate(%.0f %.0f) rotate(%.1f)"><path d="M0 14 V-3" stroke="%s" stroke-width="2.5" stroke-linecap="round"/>'
      '<path d="M0 -12 L5.5 -2 L-5.5 -2 Z" fill="%s"/></g>' % (nx, ny, theta, INK, INK))
    tip = math.radians(theta)
    tx, ty = nx + 20 * math.sin(tip), ny - 20 * math.cos(tip)
    a('<text x="%.0f" y="%.0f" font-size="11" font-weight="700" fill="%s" text-anchor="middle">N</text>' % (tx, ty + 4, INK))
    bar_px = 400 * PX_PER_M
    bx, by = mx1 - bar_px - 4, H - 18
    a('<path d="M%.0f %d h%.0f M%.0f %d v-8 M%.0f %d v-8" stroke="%s" stroke-width="3" fill="none"/>' % (bx, by, bar_px, bx, by + 4, bx + bar_px, by + 4, INK))
    a('<text x="%.0f" y="%d" font-size="12" font-weight="700" fill="%s" text-anchor="end">400 m, about a 5-minute walk</text>' % (bx - 8, by + 4, INK))
    a('</svg>')
    svg = "".join(out)
    os.makedirs(os.path.dirname(OUT_SVG), exist_ok=True)
    with open(OUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg)

    n_inside = sum(1 for s in stores if s["inside"])
    alt = ("Map of the office cluster: Flatiron, NoMad and Union Square, about 14th to 30th Street between Sixth Avenue "
           "and Park Avenue South, plus the blocks around Union Square. %d numbered food stores, %d of them inside the cluster, "
           "are listed next to the map." % (len(stores), n_inside))
    date = as_of[-1] if as_of else "unknown"

    def figure(cls=""):
        return ('<figure class="map-figure%s">\n'
                '  <img src="assets/img/cluster-map.svg" width="%d" height="%d" loading="lazy" decoding="async" alt="%s">\n'
                '  <figcaption>\n'
                '    <ul class="map-legend">\n'
                '      <li><span class="lg lg-area" aria-hidden="true"></span>Office cluster</li>\n'
                '      <li><span class="lg" aria-hidden="true"></span>Grocer with a documented natural, local or emerging set</li>\n'
                '      <li><span class="lg lg-open" aria-hidden="true"></span>Specialty, gourmet or natural-format market</li>\n'
                '    </ul>\n'
                '  </figcaption>\n'
                '</figure>' % (cls, W, H, html.escape(alt, quote=True)))

    def li(s):
        bits = [html.escape(s["address"]),
                "inside the cluster" if s["inside"] else "%d block%s outside" % (s["blocks"], "" if s["blocks"] == 1 else "s")]
        return ('<li><span class="n">%d.</span><span>%s</span><span class="addr">%s</span></li>'
                % (s["n"], html.escape(s["name"]), " · ".join(bits)))

    groups = [("Grocers with a documented natural, local or emerging set", [s for s in stores if s["tier"] == "A"]),
              ("Specialty, gourmet or natural-format markets", [s for s in stores if s["tier"] != "A"])]
    brand_block = (
        '<!-- MAP:START (generated by tools/build_map.py from cluster-1-flatiron/map-public.geojson; edit there, not here) -->\n'
        '<div class="map-layout">\n' + figure() + '\n'
        '<div class="map-list">\n'
        + "".join('  <h3>%s</h3>\n  <ol class="stores">\n    %s\n  </ol>\n' % (title, "\n    ".join(li(s) for s in group)) for title, group in groups if group) +
        '  <p class="small muted">Store list researched on %s from each store\'s own website and the New York State retail food store license list. '
        'A store on this map is not an endorsement, and being on it does not mean the store carries any particular brand. '
        'Streets and parks: NYC Street Centerline and NYC Parks Properties, NYC Open Data.</p>\n'
        '</div>\n</div>\n<!-- MAP:END -->' % date)
    office_block = (
        '<!-- MAP:START (generated by tools/build_map.py; edit there, not here) -->\n' + figure(" map-small") + '\n<!-- MAP:END -->')

    for page, block in (("brands.html", brand_block), ("offices.html", office_block)):
        path = os.path.join(SITE, page)
        if not os.path.exists(path):
            print("skip", page, "(not written yet)")
            continue
        src = open(path, encoding="utf-8").read()
        new, n = re.subn(r"<!-- MAP:START.*?<!-- MAP:END -->", lambda m: block, src, flags=re.S)
        if n != 1:
            sys.exit("%s: expected exactly one MAP:START/MAP:END block, found %d" % (page, n))
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
        print("updated", page)
    print("wrote %s (%d x %d px, %.1f KB), %d stores (%d inside), data as of %s"
          % (os.path.relpath(OUT_SVG, WEB), W, H, len(svg) / 1024, len(stores), n_inside, date))


if __name__ == "__main__":
    main()
