#!/usr/bin/env python3
"""Drop-day route sheet, from the tracker. One page a briefed stranger can run a route from.

  python3 tools/make_route.py TRACKER.xlsx DROP_ID OUT_DIR

Writes OUT_DIR/route-<drop>.html (works on a phone) and route-<drop>.pdf (print it).
The sheet changes with the drop's delivery model:
  founder      you carry it: stops in order, receiving windows, owner phones, what to hand over, boxes to log
  courier      the same, written for the courier, with proof-of-delivery rules and when to call you
  direct-ship  a tracking sheet: carrier tracking per office, kit mailed, the office's count and photo,
               and an in-person visit for any office's first drop
Refuses when the drop date is invalid, a stop has no owner phone, or a stop has no approved brand.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402
import opscal  # noqa: E402
import tracker as TR  # noqa: E402

E = common.E


def walk_minutes(a, b):
    if None in (a[0], a[1], b[0], b[1]) or "" in (a[0], a[1], b[0], b[1]):
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, (float(a[0]), float(a[1]), float(b[0]), float(b[1])))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    m = 2 * 6371000 * math.asin(math.sqrt(h))
    return max(1, round(m * 1.3 / 80))   # Manhattan grid factor 1.3, 80 m a minute with a hand truck (assumption)


def stops_for(tr, drop_id):
    T = tr.drop_date(drop_id)
    camps = [cid for cid, c in tr.campaigns.items() if TR._s(c["drop_id"]) == drop_id]
    lads = {cid: tr.ladder(cid) for cid in camps}
    rows = sorted([s for s in tr.rows["stops"] if TR._s(s["drop_id"]) == drop_id], key=lambda s: TR._n(s.get("route_order")) or 99)
    out, problems, prev = [], [], None
    for s in rows:
        oid = TR._s(s["office_id"])
        o = tr.office(oid)
        items = []
        for cid in camps:
            lad = lads[cid]
            row = next((x for x in lad["offices"] if x["office_id"] == oid and x["approved"] == "Y"), None)
            if row:
                upc = int(TR._n(lad["campaign"].get("units_per_case"))) or int(row["units_allocated"] or 1)
                items.append((lad["campaign"]["brand_name"], TR._s(lad["campaign"].get("product_sku")), int(row["units_allocated"] or 0),
                              max(1, math.ceil((row["units_allocated"] or 0) / upc)), cid))
        if not items:
            problems.append("%s has no approved brand on this drop" % oid)
        if not o["owner_phone"]:
            problems.append("%s has no owner phone" % oid)
        first = tr.office_drop_number(oid, T) == 1
        here = (o.get("lat"), o.get("lon"))
        wm = walk_minutes(prev, here) if prev else None
        prev = here
        out.append({"s": s, "o": o, "oid": oid, "items": items, "first": first, "walk": wm})
    return T, camps, lads, out, problems


def door_rules(model):
    who = "you" if model == "founder" else "the courier"
    rules = [
        "Arrive inside the receiving window. Security desk: give the pantry owner's name and your ID. Walk-up: go straight to the owner.",
        "Hand the case to the owner, or place it yourself if they say so: eye level beside the snacks, never in a cabinet, card in front, allergen line showing.",
        ("Owner not there: leave it at the front desk ONLY where this sheet says Front desk OK: Y. Otherwise take it back, text the owner, "
         "and deliver again next morning before 10 am (still inside one business day). Never leave food unattended in a lobby.") if model == "founder" else
        ("Owner not there: leave it at the front desk ONLY where this sheet says Front desk OK: Y. Otherwise take it back and call the founder "
         "before you leave the building. Never leave food unattended in a lobby."),
        "Office declines at the door: take the case back, say thank you, note it below.",
        "Anyone reports a problem with a product: take that product back, note what was said and when, call the founder now. Give no medical advice.",
        "Two photos at every stop: one wide of the pantry, one close of the card and product. No people, faces, screens or whiteboards in the frame.",
        "Count the units you can see on the shelf before you leave, and write it below.",
    ]
    if model == "courier":
        rules.insert(0, "You are delivering sealed, shelf-stable food for {company}. Keep cases upright and off the floor of the vehicle. Hand each case to the person named, never to a stranger.")
    return rules


def html_for(tr, drop_id, out_dir):
    T, camps, lads, stops, problems = stops_for(tr, drop_id)
    if T is None:
        raise SystemExit("REFUSED: %s has no valid drop date" % drop_id)
    d = tr.drops[drop_id]
    model = TR._s(d["delivery_model"])
    name = tr.company_name
    phone = TR._s(tr.config.get("founder_phone"))
    hdr = ["<h1>Route sheet · %s · %s</h1>" % (E(common.fmt_date(T, "%A %Y-%m-%d")), E(drop_id)),
           "<p><b>%s</b> · delivery model <b>%s</b> · %d stops · founder %s · backup %s</p>" % (
               E(name), E(model), len(stops), E(phone), E(TR._s(d.get("backup_person")) or "none named"))]
    if model == "courier":
        hdr.append("<p>Courier: <b>%s</b>. Pick up at the receiving address 7:45 am; the founder meets you at every stop marked <b>FIRST DROP</b>.</p>" % E(TR._s(d.get("courier_or_van")) or "[COURIER]"))
    reserve = []
    for cid in camps:
        lad = lads[cid]
        reserve.append("%s: %d" % (lad["campaign"]["brand_name"], max(0, int(lad["units_received"] - lad["units_rejected"] - lad["units_allocated"]))))
    load = {}
    for st in stops:
        for (b, p, u, n, cid) in st["items"]:
            x = load.setdefault(b, [0, 0])
            x[0] += u
            x[1] += n
    hdr.append("<p class='small'><b>Load</b>: %s.</p>" % E(" · ".join("%s %d units in %d cases" % (b, v[0], v[1]) for b, v in load.items())))
    if model != "direct-ship":
        hdr.append("<p class='small'>Reserve carried (stays with you): %s. Call %s for anything this sheet does not answer.</p>" % (E(" · ".join(reserve)), E(phone)))
        hdr.append("<div class='box2'><b>At every door</b><ol class='small'>%s</ol></div>" % "".join("<li>%s</li>" % E(r.replace("{company}", name)) for r in door_rules(model)))
    body = []
    for i, st in enumerate(stops, start=1):
        s, o, oid = st["s"], st["o"], st["oid"]
        coi = TR._s(o.get("coi_required"))
        coi_txt = {"yes": "Building needs our certificate: %s" % (TR._s(o.get("building_coi_status")) or "to request"),
                   "unsure": "Certificate: building unsure (status %s)" % (TR._s(o.get("building_coi_status")) or "to request")}.get(coi, "No certificate needed")
        fd = TR._s(o.get("front_desk_fallback_ok")) == "Y"
        cases = "".join("<tr><td>%s</td><td class='small'>%s</td><td>%d units</td><td>%d case%s</td><td>placed <span class='box'></span></td></tr>" % (
            E(b), E(p), u, n, "" if n == 1 else "s", ) for (b, p, u, n, cid) in st["items"])
        walk = (" · about %d min from the last stop" % st["walk"]) if st["walk"] else ""
        if model == "direct-ship":
            body.append("""<div class='stop'><h2>%d. %s %s</h2>
<div class='grid small'><div>%s, %s<br>%s</div><div>Owner <b>%s</b> · <b>%s</b><br>Kit mailed: %s · tracking %s</div></div>
<table class='small'>%s</table>
<p class='small'>%s Confirm with the owner: case arrived (count), placed (photo with the card), by T+1 %s.</p>
<p class='small'>Arrived <span class='box'></span> · counted <span class='box'></span> · placement photo <span class='chk'></span> · issue <span class='box' style='min-width:2.5in'></span></p></div>""" % (
                i, E(TR._s(o.get("company"))), "<span class='warn'>FIRST DROP: visit in person on T</span>" if st["first"] else "",
                E(TR._s(o.get("office_address"))), E(TR._s(o.get("floor_suite"))), E(TR._s(o.get("delivery_point_note"))),
                E(TR._s(o.get("pantry_owner_name"))), E(o["owner_phone"]), E(common.fmt_date(TR._d(s.get("kit_mailed_date")))) or "<span class='warn'>not yet</span>",
                E(TR._s(s.get("carrier_tracking"))) or "<span class='warn'>missing</span>", cases, E(coi_txt + "."), E(common.fmt_date(opscal.add_bd(T, 1)))))
            continue
        body.append("""<div class='stop'><h2>%d. %s · %s <span class='small muted'>%s</span> %s</h2>
<div class='grid small'><div><b>%s</b>%s<br>%s<br><i>%s</i></div>
<div>Owner <b>%s</b> · <b>%s</b><br>Receiving: %s · window <b>%s</b><br>Front desk OK: <b>%s</b> · %s</div></div>
<table class='small'>%s</table>
<p class='small'>Arrived <span class='box'></span> Left <span class='box'></span> Handed to: owner <span class='chk'></span> front desk <span class='chk'></span> other <span class='chk'></span> · photos wide <span class='chk'></span> close <span class='chk'></span> · Slack post confirmed <span class='chk'></span></p>
<p class='small'>Issue <span class='box' style='min-width:5in'></span></p></div>""" % (
            i, E(common.fmt_time(TR._t(s.get("planned_time")))), E(TR._s(o.get("company"))), E(oid),
            "<span class='warn'>FIRST DROP</span>" if st["first"] else "",
            E(TR._s(o.get("office_address"))), (", " + E(TR._s(o.get("floor_suite")))) if TR._s(o.get("floor_suite")) else "",
            E(TR._s(o.get("delivery_point_note"))), E(walk.strip(" ·")),
            E(TR._s(o.get("pantry_owner_name"))), E(o["owner_phone"]), E(TR._s(o.get("receiving_type"))), E(TR._s(o.get("receiving_window"))),
            "Y" if fd else "N, the owner must take it", E(coi_txt), cases))
    tail = ["<h2>After the route (same day)</h2><ol class='small'>",
            "<li>Tracker, stops tab: arrival, departure, handed to, outcome for every stop.</li>",
            "<li>Inventory tab: one <i>delivered</i> row per office per brand with the count and who counted.</li>",
            "<li>Photos: save as &lt;campaign_id&gt;_&lt;office_id&gt;_placement_&lt;date&gt;.jpg; one row each on the photos tab; the shelf count on the counts tab.</li>",
            "<li>Issues tab: anything on this sheet's Issue lines. Hours tab: drop_day hours.</li>",
            "<li>Tomorrow (T+1): placement confirmation to each brand (tools/make_messages.py).</li></ol>"]
    css = ".box2{border:2px solid var(--ink);padding:4pt 8pt;margin:6pt 0}.box2 ol{margin:2pt 0 0 14pt;padding:0}"
    if problems:
        hdr.insert(1, "<p class='warn'>Fix before printing: %s</p>" % E("; ".join(problems)))
    return common.page("Route " + drop_id, "".join(hdr + body + tail), out_dir, sample=common.is_sample(drop_id), extra_css=css), problems


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 1
    tr = TR.Tracker(argv[1])
    drop_id, out = argv[2], argv[3]
    html, problems = html_for(tr, drop_id, out)
    hp = common.write(os.path.join(out, "route-%s.html" % drop_id), html)
    res = common.render(hp, os.path.join(out, "route-%s.pdf" % drop_id), png_path=os.path.join(out, "route-%s-phone.png" % drop_id), width=390)
    print("route %s -> %s %s" % (drop_id, hp, ("PROBLEMS: " + "; ".join(problems)) if problems else "ok"), "" if res.get("ok") else res)
    return 2 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
