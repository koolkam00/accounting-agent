#!/usr/bin/env python3
"""Public map for the website: the boundary and the public stores only. No company names,
no brand name (so a rename never touches it). Drawn on the Manhattan grid, so avenues run
up the page. Writes public-map.svg (fonts embedded as subsets) and public-map.png.

Usage: python3 public_map.py [path to a python that has fontTools]
"""
import base64
import json
import os
import subprocess
import sys
import tempfile

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DESK = os.path.dirname(ROOT)
GEO = os.path.join(ROOT, "_work", "geo")
sys.path.insert(0, HERE)
import grid  # noqa: E402
import boundary  # noqa: E402
import router  # noqa: E402

FT_PY = sys.argv[1] if len(sys.argv) > 1 else sys.executable
FONT_DIR = os.path.join(DESK, "desk-drop-identity", "fonts", "static")
# D's tokens (desk-drop-identity/tokens/tokens.css)
INK, STONE, MIST, PAPER, PAPER_WARM = "#1F1D1A", "#6B675F", "#E6E1D6", "#FFFFFF", "#F7F3EA"
COBALT, COBALT_TINT, APRICOT = "#2E47C9", "#E3E8FB", "#F4B183"
PARK = "#DDE7D3"   # map-only neutral green for parks (not a brand token)
STREET, AVENUE = "#E2DCCF", "#D2CBBB"

W = 1200
PAD = 48
S_MIN, S_MAX = 7.6, 32.2
X_MIN, X_MAX = -720.0, 940.0
MAP_W = W - 2 * PAD
SCALE = MAP_W / (X_MAX - X_MIN)          # px per metre
SP = grid.model()["spacing_m"]
MAP_H = (S_MAX - S_MIN) * SP * SCALE
TOP = 190                                  # map top y


def P(s, x):
    return (PAD + (x - X_MIN) * SCALE, TOP + (S_MAX - s) * SP * SCALE)


def from_ll(lat, lon):
    s, x = grid.sx(lat, lon)
    return P(s, x)


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    r = pd.read_csv(os.path.join(ROOT, "retailers.csv"), dtype=str).fillna("")
    pub = r[r.public_map == "Y"].copy()
    pub["s"] = pub.apply(lambda x: grid.sx(float(x.lat), float(x.lon))[0], axis=1)
    pub["x"] = pub.apply(lambda x: grid.sx(float(x.lat), float(x.lon))[1], axis=1)
    pub = pub.sort_values(["buy_path_tier", "s"], ascending=[True, True]).reset_index(drop=True)
    pub["n"] = range(1, len(pub) + 1)
    out = []
    used = set()

    def text(x, y, t, size, weight=400, fill=INK, anchor="start", family="text", extra=""):
        used.update(str(t))
        fam = "DDDisplay" if family == "display" else "DDText"
        out.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}, Arial, sans-serif" font-size="{size}" '
                   f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{esc(t)}</text>')

    # background and clip
    out.append(f'<rect x="0" y="0" width="{W}" height="__H__" fill="{PAPER_WARM}"/>')
    out.append(f'<clipPath id="mapclip"><rect x="{PAD}" y="{TOP}" width="{MAP_W:.1f}" height="{MAP_H:.1f}" rx="8"/></clipPath>')
    out.append(f'<rect x="{PAD}" y="{TOP}" width="{MAP_W:.1f}" height="{MAP_H:.1f}" rx="8" fill="{PAPER}"/>')
    out.append('<g clip-path="url(#mapclip)">')
    # parks
    parks = json.load(open(os.path.join(GEO, "parks_raw.geojson")))
    for f in parks["features"]:
        g = f["geometry"]
        if not g:
            continue
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            for ring in poly[:1]:
                pts = [from_ll(la, lo) for lo, la in ring]
                if all(not (PAD - 50 < px < W - PAD + 50 and TOP - 50 < py < TOP + MAP_H + 50) for px, py in pts):
                    continue
                out.append('<path d="M' + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + f' Z" fill="{PARK}"/>')
    # streets
    st = json.load(open(os.path.join(GEO, "streets_raw.geojson")))
    minor, major = [], []
    for f in st["features"]:
        p = f["properties"]
        if p.get("rw_type") != "1" or not f["geometry"]:
            continue
        name = p.get("full_street_name", "")
        is_major = any(k in name for k in (" AVE", "AVE ", "BROADWAY", "AMERICAS", "IRVING PL", "UNIVERSITY PL", "BOWERY")) or name.endswith("AVE S")
        g = f["geometry"]
        for line in (g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]):
            pts = [from_ll(la, lo) for lo, la in line]
            d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
            (major if is_major else minor).append(d)
    out.append(f'<path d="{" ".join(minor)}" stroke="{STREET}" stroke-width="2.2" fill="none" stroke-linecap="round"/>')
    out.append(f'<path d="{" ".join(major)}" stroke="{AVENUE}" stroke-width="4.5" fill="none" stroke-linecap="round"/>')
    # boundary
    ring = boundary.polygon_lonlat()
    bpts = [from_ll(la, lo) for lo, la in ring]
    bd = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in bpts) + " Z"
    out.append(f'<path d="{bd}" fill="{COBALT_TINT}" fill-opacity="0.72" stroke="{COBALT}" stroke-width="3.5" stroke-linejoin="round"/>')
    # park labels
    for s, x, lab in ((15.55, 236, "Union"), (15.15, 236, "Square"), (24.85, 75, "Madison"), (24.45, 75, "Square Park")):
        px, py = P(s, x)
        text(px, py, lab, 13, 600, "#55704A", "middle")
    # neighbourhood labels inside the boundary
    for s, x, lab in ((19.6, -175, "FLATIRON"), (28.6, -175, "NOMAD"), (13.45, 470, "UNION SQ")):
        px, py = P(s, x)
        text(px, py, lab, 17, 700, COBALT, "middle", "text", 'letter-spacing="2.5"')
    out.append("</g>")
    # avenue labels along the top edge of the map
    for name, x in (("Eighth Ave", -861.4), ("Seventh Ave", -585), ("Sixth Ave", -310.6), ("Fifth Ave", 0),
                    ("Madison", 152), ("Park Ave S", 311.4), ("Lexington", 465), ("Third Ave", 621.1), ("Second Ave", 837.5)):
        if X_MIN + 30 < x < X_MAX - 30:
            px, _ = P(S_MAX, x)
            text(px, TOP - 10, name, 14, 600, STONE, "middle")
    bx, by_ = P(21.0, router.broadway_x(21.0))
    text(bx + 6, by_, "Broadway", 13, 600, STONE, "start", "text", f'transform="rotate(-21 {bx + 6:.1f} {by_:.1f})"')
    # street labels on the left edge
    for k in (8, 10, 12, 14, 16, 18, 20, 23, 26, 28, 30, 32):
        if S_MIN + 0.2 < k < S_MAX - 0.2:
            _, py = P(k, X_MIN)
            text(PAD - 8, py + 5, f"{k}", 13, 600, STONE, "end")
    text(PAD - 8, TOP - 10, "St", 13, 600, STONE, "end")
    # stores
    placed = []
    for x in pub.itertuples():
        px, py = from_ll(float(x.lat), float(x.lon))
        for qx, qy in placed:  # next-door stores: nudge apart so both numbers show
            if abs(px - qx) < 28 and abs(py - qy) < 28:
                px = qx + 30
        placed.append((px, py))
        if x.buy_path_tier == "A":
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="15" fill="{COBALT}" stroke="{PAPER}" stroke-width="3"/>')
            text(px, py + 5.5, x.n, 15, 700, PAPER, "middle")
        else:
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="14" fill="{PAPER}" stroke="{COBALT}" stroke-width="3.5"/>')
            text(px, py + 5.5, x.n, 15, 700, COBALT, "middle")
    # north arrow (true north is 29.4 degrees counterclockwise from up)
    ax, ay = PAD + 46, TOP + 52
    th = grid.model()["theta_deg"]
    out.append(f'<g transform="rotate({-th:.1f} {ax} {ay})"><path d="M{ax},{ay - 30} L{ax + 11},{ay + 12} L{ax},{ay + 5} L{ax - 11},{ay + 12} Z" fill="{INK}"/></g>')
    text(ax, ay + 40, "True north", 12, 600, INK, "middle")
    # scale bar: 400 m = about 5 minutes on foot
    sx0, sy0 = W - PAD - 400 * SCALE - 150, TOP + MAP_H + 40
    L = 400 * SCALE
    out.append(f'<rect x="{sx0 - 10}" y="{sy0 - 26}" width="{L + 150:.1f}" height="44" rx="6" fill="{PAPER}" fill-opacity="0.9"/>')
    out.append(f'<path d="M{sx0},{sy0} h{L:.1f}" stroke="{INK}" stroke-width="4"/>')
    out.append(f'<path d="M{sx0},{sy0 - 6} v12 M{sx0 + L:.1f},{sy0 - 6} v12" stroke="{INK}" stroke-width="2"/>')
    text(sx0 + L + 10, sy0 + 5, "400 m, about 5 min", 13, 600, INK)
    # title
    text(PAD, 70, "Flatiron, NoMad and Union Square", 40, 800, INK, "start", "display")
    text(PAD, 108, "The office cluster, and natural and specialty food stores within about ten blocks of it.", 18, 400, INK)
    yk = 148
    out.append(f'<path d="M{PAD},{yk - 12} h34 v20 h-34 Z" fill="{COBALT_TINT}" stroke="{COBALT}" stroke-width="3"/>')
    text(PAD + 44, yk + 3, "Office cluster", 15, 600, INK)
    out.append(f'<circle cx="{PAD + 220}" cy="{yk - 2}" r="11" fill="{COBALT}" stroke="{PAPER}" stroke-width="2"/>')
    text(PAD + 238, yk + 3, "Grocer with a documented natural, local or emerging set", 15, 600, INK)
    out.append(f'<circle cx="{PAD + 650}" cy="{yk - 2}" r="10" fill="{PAPER}" stroke="{COBALT}" stroke-width="3"/>')
    text(PAD + 668, yk + 3, "Specialty, gourmet or natural-format market", 15, 600, INK)
    # list
    y0 = TOP + MAP_H + 46
    text(PAD, y0, "Stores on this map", 20, 700, INK, "start", "display")
    col_w = (W - 2 * PAD) / 2
    per_col = (len(pub) + 1) // 2
    for i, x in enumerate(pub.itertuples()):
        cx = PAD + (i // per_col) * col_w
        cy = y0 + 36 + (i % per_col) * 46
        addr = x.street_address.split(",")[0]
        text(cx, cy, f"{x.n}.", 15, 700, COBALT)
        text(cx + 30, cy, x.retailer_name, 15, 600, INK)
        text(cx + 30, cy + 19, addr, 14, 400, STONE)
    yf = y0 + 36 + per_col * 46 + 14
    foot = [
        "Store list researched on 2026-10-24 from each store's own website and the New York State retail food store licence list.",
        "A store on this map is not an endorsement, and being on the map does not mean it carries any particular brand.",
        "Map is turned so the avenues run up the page. Streets and parks: NYC Street Centerline (CSCL) and NYC Parks Properties, NYC Open Data.",
    ]
    for i, t in enumerate(foot):
        text(PAD, yf + i * 22, t, 13, 400, STONE)
    H = int(yf + len(foot) * 22 + 30)
    body = "\n".join(out).replace("__H__", str(H))
    css = font_css(used)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-labelledby="t d"><title id="t">Map of the Flatiron, NoMad and Union Square office cluster with nearby stores</title>'
           f'<desc id="d">The cluster runs from 14th to 30th Street between Sixth Avenue and Park Avenue South, plus the blocks around '
           f'Union Square. {len(pub)} stores within about ten blocks are numbered and listed below the map.</desc>'
           f"<style>{css}</style>\n{body}\n</svg>\n")
    open(os.path.join(ROOT, "public-map.svg"), "w").write(svg)
    pub[["n", "retailer_id", "retailer_name", "street_address", "buy_path_tier"]].to_csv(os.path.join(HERE, "out", "public_map_numbers.csv"), index=False)
    # write the map numbers into map-public.geojson so a text list on the site matches the picture
    gj_path = os.path.join(ROOT, "map-public.geojson")
    gj = json.load(open(gj_path))
    num = dict(zip(pub.retailer_id, pub.n))
    for f in gj["features"]:
        if f["properties"].get("kind") == "retailer":
            f["properties"]["map_number"] = int(num[f["properties"]["retailer_id"]])
    gj["features"] = [gj["features"][0]] + sorted(gj["features"][1:], key=lambda f: f["properties"]["map_number"])
    json.dump(gj, open(gj_path, "w"), indent=1)
    print("public stores", len(pub), "svg bytes", len(svg), "height", H)


def font_css(chars):
    text = "".join(sorted(chars | set("0123456789 .,")))
    faces = [("DDDisplay", "Bricolage-96-Normal-800.ttf", 800), ("DDDisplay", "Bricolage-96-Normal-700.ttf", 700),
             ("DDText", "AtkinsonNext-400.ttf", 400), ("DDText", "AtkinsonNext-600.ttf", 600), ("DDText", "AtkinsonNext-700.ttf", 700)]
    css = []
    with tempfile.TemporaryDirectory() as td:
        tf = os.path.join(td, "chars.txt")
        open(tf, "w").write(text)
        for fam, fn, wt in faces:
            o = os.path.join(td, fn + ".woff")
            subprocess.run([FT_PY, "-m", "fontTools.subset", os.path.join(FONT_DIR, fn), f"--text-file={tf}",
                            "--flavor=woff", f"--output-file={o}", "--layout-features=kern,liga"], check=True)
            b64 = base64.b64encode(open(o, "rb").read()).decode()
            css.append(f"@font-face{{font-family:{fam};font-weight:{wt};src:url(data:font/woff;base64,{b64}) format('woff');}}")
    return "".join(css) + " /* Fonts: Bricolage Grotesque and Atkinson Hyperlegible Next, SIL Open Font License 1.1, subset. */"


if __name__ == "__main__":
    main()
