#!/usr/bin/env python3
"""Write boundary.geojson, map-private.geojson, map-public.geojson, the KML layers and
the phone-friendly private HTML map (map-private.html) from the final tables."""
import html
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
sys.path.insert(0, HERE)
import boundary  # noqa: E402

BRAND_NAME = "Desk Drop"  # the one place the working name lives in the map files
LEAFLET_JS = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"
LEAFLET_JS_SRI = "sha512-BwHfrr4c9kmRkLw6iXFdzcdWV/PGkVgiIyIWLLlTSXzWQzxuSg4DiQUCpauz/EWjgk5TYQqX/kvn9pG1NpYfqg=="
LEAFLET_CSS = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css"
LEAFLET_CSS_SRI = "sha512-Zcn6bjR/8RZbLEpLIeOwNtzREBAJnUKESxces60Mpoj+2okopSAcSUIUOseddDm0cxnGQzxIR7vJgsLZbdLE3w=="

LOBBY_COLOR = {"walk-up": "#1E8E3E", "security desk": "#B3261E", "loading dock": "#E37400", "unknown": "#6B675F"}
TIER_COLOR = {"A": "#2E47C9", "B": "#7A8FE8", "C": "#9C978C"}


def rd(path):
    return pd.read_csv(os.path.join(ROOT, path), dtype=str).fillna("")


def pt(lat, lon):
    return {"type": "Point", "coordinates": [round(float(lon), 6), round(float(lat), 6)]}


def feat(geom, props):
    return {"type": "Feature", "geometry": geom, "properties": props}


def main():
    c, n, b = rd("companies.csv"), rd("near_miss.csv"), rd("buildings.csv")
    w, r, route, walk = rd("coworking.csv"), rd("retailers.csv"), rd("route.csv"), rd("walk.csv")
    legs = json.load(open(os.path.join(OUT, "route_legs.json")))["legs"]
    bfeat = boundary.geojson_feature()

    # ---------------- boundary.geojson
    json.dump({"type": "FeatureCollection", "features": [bfeat]}, open(os.path.join(ROOT, "boundary.geojson"), "w"), indent=1)

    # ---------------- private
    F = [bfeat]
    for _, x in b.iterrows():
        F.append(feat(pt(x.lat, x.lon), {"layer": "building", **{k: x[k] for k in (
            "building_id", "building_name", "street_address", "also_known_as", "lobby_type", "lobby_source_url", "coi_required",
            "candidate_company_count", "candidate_company_ids", "coworking_ids", "retailer_ids", "pluto_numfloors", "bbl",
            "entrance_note")}}))
    for df, layer in ((c, "company"), (n, "near-miss")):
        for _, x in df.iterrows():
            F.append(feat(pt(x.lat, x.lon), {"layer": layer, **{k: x[k] for k in (
                "company_id", "company_name", "building_id", "street_address", "floor", "headcount_band", "headcount_scope",
                "confidence", "candidate_status", "lease_status", "move_in_date", "in_coworking", "coworking_id",
                "address_source_url", "address_source_date", "hq_city", "hq_in_nyc")}}))
    for _, x in w.iterrows():
        F.append(feat(pt(x.lat, x.lon), {"layer": "coworking", **{k: x[k] for k in (
            "coworking_id", "operator", "location_name", "street_address", "pantry_control", "status", "confidence",
            "in_boundary", "source_url", "tenant_company_ids")}}))
    for _, x in r.iterrows():
        F.append(feat(pt(x.lat, x.lon), {"layer": "retailer", **{k: x[k] for k in (
            "retailer_id", "retailer_name", "street_address", "inside_boundary", "blocks_outside", "buy_path_tier", "shelf_set",
            "confidence", "source_url", "candidates_within_5_blocks", "public_map")}}))
    for _, x in route.iterrows():
        F.append(feat(pt(x.lat, x.lon), {"layer": "route-stop", **{k: x[k] for k in (
            "stop", "company_id", "company_name", "street_address", "lobby_type", "arrive_est", "depart_est", "leg_minutes_est",
            "reload_minutes_before", "entrance_note")}}))
    line = []
    for lg in legs:
        line += lg["path"] if not line else lg["path"][1:]
    F.append(feat({"type": "LineString", "coordinates": line}, {"layer": "route-line", "label": "Model ten-stop route (estimate)"}))
    for _, x in walk.iterrows():
        F.append(feat(pt(x.lat, x.lon), {"layer": "walk-stop", **{k: x[k] for k in (
            "session", "order", "stops_here", "street_address", "walk_minutes_from_previous_est", "dwell_minutes_est")}}))
    json.dump({"type": "FeatureCollection", "name": "cluster-1-private (NEVER PUBLISH)", "features": F},
              open(os.path.join(ROOT, "map-private.geojson"), "w"), indent=1)

    # ---------------- public: boundary and retailers only (no company names, no notes)
    pub_r = r[r.public_map == "Y"]
    PF = [{"type": "Feature", "geometry": bfeat["geometry"], "properties": {"kind": "boundary", "name": "Flatiron, NoMad and Union Square"}}]
    for _, x in pub_r.iterrows():
        # public wording only (review round 1, R1-13): the store's format, never research hedges
        PF.append(feat(pt(x.lat, x.lon), {"kind": "retailer", "retailer_id": x.retailer_id, "name": x.retailer_name,
                                           "address": x.street_address.split(",")[0], "buy_path_tier": x.buy_path_tier,
                                           "shelf_set": x.public_description, "inside_boundary": x.inside_boundary,
                                           "blocks_outside": x.blocks_outside,
                                           "walk_minutes_from_cluster_edge": int(x.walk_minutes_from_cluster_edge),
                                           "as_of": "2026-10-24"}))
    json.dump({"type": "FeatureCollection", "name": "cluster-1-public", "features": PF},
              open(os.path.join(ROOT, "map-public.geojson"), "w"), indent=1)

    # ---------------- KML
    os.makedirs(os.path.join(ROOT, "kml"), exist_ok=True)
    write_kml_layers(bfeat, b, c, w, r, route, line, walk, pub_r)

    # ---------------- HTML
    write_html(F)
    write_route_sheet(route, line)
    print("features private", len(F), "public", len(PF))


# ------------------------------------------------------------------ KML
def kml_color(hexrgb, alpha="ff"):
    h = hexrgb.lstrip("#")
    return alpha + h[4:6] + h[2:4] + h[0:2]


def esc(s):
    return html.escape(str(s), quote=False)


def placemark(name, desc, style, geom_xml):
    return f"<Placemark><name>{esc(name)}</name><description><![CDATA[{desc}]]></description><styleUrl>#{style}</styleUrl>{geom_xml}</Placemark>"


def point_xml(lat, lon):
    return f"<Point><coordinates>{float(lon):.6f},{float(lat):.6f},0</coordinates></Point>"


def doc(name, styles, placemarks, desc=""):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
            f"<name>{esc(name)}</name><description><![CDATA[{desc}]]></description>{''.join(styles)}{''.join(placemarks)}</Document></kml>\n")


def icon_style(sid, color, scale=1.0, shape="placemark_circle"):
    return (f'<Style id="{sid}"><IconStyle><color>{kml_color(color)}</color><scale>{scale}</scale>'
            f"<Icon><href>http://maps.google.com/mapfiles/kml/shapes/{shape}.png</href></Icon></IconStyle></Style>")


def boundary_pm(bfeat):
    coords = " ".join(f"{lo},{la},0" for lo, la in bfeat["geometry"]["coordinates"][0])
    return placemark("Cluster 1 boundary", bfeat["properties"]["rule"], "bnd",
                     f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{coords}</coordinates></LinearRing></outerBoundaryIs></Polygon>")


BND_STYLE = ('<Style id="bnd"><LineStyle><color>ffc9472e</color><width>3</width></LineStyle>'
             '<PolyStyle><color>332e47c9</color></PolyStyle></Style>')


def write_kml_layers(bfeat, b, c, w, r, route, line, walk, pub_r):
    K = os.path.join(ROOT, "kml")
    priv_note = "PRIVATE. Never publish or share by link. Contains company names."
    # boundary
    open(os.path.join(K, "1-boundary.kml"), "w").write(doc("Cluster 1 boundary", [BND_STYLE], [boundary_pm(bfeat)]))
    # buildings
    styles = [icon_style("lob-" + k.replace(" ", "-"), v) for k, v in LOBBY_COLOR.items()]
    pms = []
    for _, x in b.iterrows():
        cs = c[c.building_id == x.building_id]
        lst = "".join(f"<li>{esc(y.company_name)} (floor {esc(y.floor or 'unknown')}; {esc(y.headcount_band)}; {esc(y.confidence)}; {esc(y.lease_status)})</li>"
                      for y in cs.itertuples() if y.candidate_status == "candidate")
        desc = (f"<b>{esc(x.building_id)}</b> {esc(x.street_address)}<br>Lobby: {esc(x.lobby_type)}"
                f"{' (' + esc(x.lobby_source_url) + ')' if x.lobby_source_url else ''}<br>COI required: {esc(x.coi_required)}<br>"
                f"{esc(x.entrance_note) + '<br>' if x.entrance_note else ''}"
                f"Candidates: {esc(x.candidate_company_count)}<ul>{lst}</ul>Coworking here: {esc(x.coworking_ids or 'none')}<br>{priv_note}")
        pms.append(placemark(f"{x.building_id} {x.building_name}", desc, "lob-" + x.lobby_type.replace(" ", "-"), point_xml(x.lat, x.lon)))
    open(os.path.join(K, "2-private-buildings.kml"), "w").write(doc("Cluster 1 buildings (PRIVATE)", styles, pms, priv_note))
    # coworking
    styles = [icon_style("cw", "#8E44AD", 1.0, "square")]
    pms = [placemark(f"{x.coworking_id} {x.location_name}",
                     f"{esc(x.operator)}<br>{esc(x.street_address)}<br>Pantry control: {esc(x.pantry_control)}<br>Status: {esc(x.status)}; confidence {esc(x.confidence)}<br>In boundary: {esc(x.in_boundary)}<br>{esc(x.source_url)}<br>{priv_note}",
                     "cw", point_xml(x.lat, x.lon)) for x in w.itertuples()]
    open(os.path.join(K, "3-private-coworking.kml"), "w").write(doc("Cluster 1 coworking (PRIVATE)", styles, pms, priv_note))
    # retailers (all)
    styles = [icon_style("tier-" + k, v, 1.1, "shopping") for k, v in TIER_COLOR.items()]
    pms = [placemark(f"{x.retailer_id} {x.retailer_name}",
                     f"{esc(x.street_address)}<br>Tier {esc(x.buy_path_tier)}; {esc(x.shelf_set)}<br>Inside boundary: {esc(x.inside_boundary)}; blocks outside: {esc(x.blocks_outside)}<br>Confidence {esc(x.confidence)}; {esc(x.source_url)}",
                     "tier-" + (x.buy_path_tier or "C"), point_xml(x.lat, x.lon)) for x in r.itertuples()]
    open(os.path.join(K, "4-private-retailers.kml"), "w").write(doc("Cluster 1 retailers, all tiers (PRIVATE)", styles, pms, priv_note))
    # route
    styles = [icon_style("stop", "#1F1D1A", 1.2, "placemark_circle"),
              '<Style id="rline"><LineStyle><color>ff0074e3</color><width>4</width></LineStyle></Style>']
    pms = [placemark(f"Stop {x.stop}: {x.company_name}",
                     f"{esc(x.street_address)}<br>Lobby: {esc(x.lobby_type)}<br>Arrive {esc(x.arrive_est)}, leave {esc(x.depart_est)} (estimates)<br>Leg from previous: {esc(x.leg_minutes_est)} min (estimate)<br>"
                     f"{('Reload before this stop: ' + esc(x.reload_minutes_before) + ' min (estimate)<br>') if float(x.reload_minutes_before or 0) > 0 else ''}"
                     f"{(esc(x.entrance_note) + '<br>') if x.entrance_note else ''}{priv_note}",
                     "stop", point_xml(x.lat, x.lon)) for x in route.itertuples()]
    coords = " ".join(f"{lo},{la},0" for lo, la in line)
    pms.append(placemark("Model route line", "Grid walking path, estimate", "rline", f"<LineString><tessellate>1</tessellate><coordinates>{coords}</coordinates></LineString>"))
    open(os.path.join(K, "5-private-route.kml"), "w").write(doc("Model ten-stop route (PRIVATE)", styles, pms, priv_note))
    # walk
    styles = [icon_style("walk", "#2E47C9", 0.8, "placemark_circle")]
    pms = [placemark(f"S{x.session}-{x.order}", f"Session {esc(x.session)}, stop {esc(x.order)}<br>{esc(x.stops_here)}<br>{esc(x.street_address)}<br>Walk from previous {esc(x.walk_minutes_from_previous_est)} min; at stop {esc(x.dwell_minutes_est)} min (estimates)",
                     "walk", point_xml(x.lat, x.lon)) for x in walk.itertuples()]
    open(os.path.join(K, "6-private-walk.kml"), "w").write(doc("Verification walk (PRIVATE)", styles, pms, priv_note))
    # public
    styles = [BND_STYLE] + [icon_style("tier-" + k, v, 1.1, "shopping") for k, v in TIER_COLOR.items() if k in "AB"]
    pms = [boundary_pm(bfeat)] + [placemark(x.retailer_name, f"{esc(x.street_address.split(',')[0])}<br>{esc(x.public_description)}<br>"
                                            + ("Inside the cluster" if x.inside_boundary == "Y" else f"About {esc(x.walk_minutes_from_cluster_edge)} min walk from the cluster edge"),
                                            "tier-" + x.buy_path_tier, point_xml(x.lat, x.lon)) for x in pub_r.itertuples()]
    open(os.path.join(ROOT, "map-public.kml"), "w").write(doc("Cluster 1: boundary and nearby stores (public)", styles, pms))
    # one combined private KML (Google Earth); My Maps imports one layer per file, so use kml/ for My Maps
    parts = []
    for f in sorted(os.listdir(K)):
        t = open(os.path.join(K, f)).read()
        body = t[t.index("<Document>") + 10:t.rindex("</Document>")]
        parts.append(f"<Folder>{body}</Folder>")
    open(os.path.join(ROOT, "map-private.kml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Cluster 1 private map (NEVER PUBLISH)</name>'
        + "".join(parts) + "</Document></kml>\n")


# ------------------------------------------------------------------ HTML
def write_html(F):
    data = json.dumps({"type": "FeatureCollection", "features": F}, separators=(",", ":"))
    page = open(os.path.join(HERE, "map_template.html")).read()
    page = page.replace("__BRAND_NAME__", BRAND_NAME).replace("__DATA__", data)
    page = page.replace("__LEAFLET_JS__", LEAFLET_JS).replace("__LEAFLET_JS_SRI__", LEAFLET_JS_SRI)
    page = page.replace("__LEAFLET_CSS__", LEAFLET_CSS).replace("__LEAFLET_CSS_SRI__", LEAFLET_CSS_SRI)
    open(os.path.join(ROOT, "map-private.html"), "w").write(page)


def write_route_sheet(route, line):
    S = json.load(open(os.path.join(OUT, "stats.json")))["route"]
    over = round(S["total_minutes"] - 180)
    fit = (f"fits the 3-hour window with about {-over} min spare." if over < 0 else
           "uses the whole 3-hour window, with no slack." if over == 0 else
           f"over the 3-hour window by about {over} min.")
    tot = (f"Total {S['total_minutes']:.0f} min: {S['stop_minutes']} at stops + {S['walking_minutes']} walking ({S['metres']} m) + "
           f"{S['reload_minutes']:.0f} reloading ({S['reloads']} reload, {S['cases_per_load']} cases a load). Finishes about {S['end']}: {fit} "
           f"On one loop with no reload (light snacks): {S['total_one_load']:.0f} min. "
           f"Ten stops do not fit 8 to 11 am on one loop with drinks: split them across Tuesday and Wednesday, or hand the second loop to a courier. "
           f"Legs where a car is faster: {S['car_faster_legs']}.")
    page = open(os.path.join(HERE, "route_sheet_template.html")).read()
    rows = route[["stop", "company_name", "street_address", "floor", "lobby_type", "arrive_est", "leg_minutes_est", "reload_minutes_before", "lat", "lon"]].to_dict("records")
    page = (page.replace("__BRAND_NAME__", BRAND_NAME).replace("__ROUTE__", json.dumps(rows)).replace("__LINE__", json.dumps(line))
            .replace("__TOT__", json.dumps(tot)).replace("__LEAFLET_JS__", LEAFLET_JS).replace("__LEAFLET_JS_SRI__", LEAFLET_JS_SRI)
            .replace("__LEAFLET_CSS__", LEAFLET_CSS).replace("__LEAFLET_CSS_SRI__", LEAFLET_CSS_SRI))
    open(os.path.join(OUT, "route_sheet.html"), "w").write(page)


if __name__ == "__main__":
    main()
