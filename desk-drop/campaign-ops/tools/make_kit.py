#!/usr/bin/env python3
"""The kit for one drop, from the tracker: tent cards, case labels, Slack posts, kit checklist.

  python3 tools/make_kit.py TRACKER.xlsx DROP_ID OUT_DIR [--final]

Writes OUT_DIR/:
  cards.json, cards.pdf          one tent card per office per brand (desk-drop-identity tent card, unchanged)
  labels.json, labels.pdf        one label per case, plus one reserve label per brand
  posts/<office_id>.txt          the pre-written Slack or email post, with that office's post links
  kit-checklist.html / .pdf      what goes in each case, and the drop-day checklist (plan appendix J)
  qr-check.txt                   every QR on the printed cards decoded and matched to its office and campaign

Refuses when the drop date is invalid, a campaign is on ship HOLD, a card has no prefill template,
or the identity template refuses a card (a claim, an allergen line that does not fit at 14 pt).
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402
import make_links as ML  # noqa: E402
import opscal  # noqa: E402
import tracker as TR  # noqa: E402

DECODE_JS = r"""
const jsQR = require(process.argv[2] + '/jsqr'); const { PNG } = require(process.argv[2] + '/pngjs'); const fs = require('fs');
for (const f of process.argv.slice(3)) { const png = PNG.sync.read(fs.readFileSync(f));
  const r = jsQR(new Uint8ClampedArray(png.data), png.width, png.height); console.log(f + '\t' + (r ? r.data : 'NO DECODE')); }
"""


def ph(tr, key):
    v = TR._s(tr.config.get(key))
    return "" if v.startswith("[") else v


def kit(tr, drop_id, out, final=False):
    T = tr.drop_date(drop_id)
    if T is None:
        raise SystemExit("REFUSED: %s has no valid drop date" % drop_id)
    camps = [cid for cid, c in tr.campaigns.items() if TR._s(c["drop_id"]) == drop_id]
    links = {(r["campaign_id"], r["office_id"], r["link_type"]): r for r in ML.links_for_drop(tr, drop_id)}
    cards, labels, posts, rows, problems = [], [], {}, [], []
    stops = sorted([s for s in tr.rows["stops"] if TR._s(s["drop_id"]) == drop_id], key=lambda s: TR._n(s.get("route_order")) or 99)
    order = [TR._s(s["office_id"]) for s in stops]
    for cid in camps:
        lad = tr.ladder(cid)
        c = lad["campaign"]
        rel = release_text(tr, cid, lad)
        if not rel.startswith("RELEASED"):
            problems.append("%s is on %s" % (cid, rel))
        logo = TR._s(c.get("logo_file"))
        for o in lad["offices"]:
            if o["approved"] != "Y":
                continue
            oid = o["office_id"]
            q = links[(cid, oid, "qr")]
            card = {"brand_name": c["brand_name"], "product_name": TR._s(c.get("product_sku")),
                    "card_sentences": TR._s(c.get("card_sentences")), "allergen_source": TR._s(c.get("allergen_source")) or "contains_statement",
                    "allergen_line_verbatim": TR._s(c.get("allergen_line_verbatim")), "may_contain_verbatim": TR._s(c.get("may_contain_verbatim")),
                    "retailer_line": TR._s(c.get("retailer_line")), "discount_code": TR._s(c.get("discount_code")),
                    "code_site": TR._s(c.get("code_site")), "qr_url": q["short_url"], "qr_display": q["short_url"].replace("https://", ""),
                    "office_id": oid, "campaign_id": cid}
            if logo:
                card["brand_logo"] = logo
            for k in ("flavor_name", "flavor_name_2", "allergen_source_2", "allergen_line_verbatim_2", "may_contain_verbatim_2",
                      "claims_reviewed", "claims_review_reason"):
                if TR._s(c.get(k)):
                    card[k] = TR._s(c.get(k))
            cards.append(card)
            units = int(o["units_allocated"] or 0)
            upc = int(TR._n(c.get("units_per_case"))) or units or 1
            n_cases = max(1, math.ceil(units / upc))
            left = units
            off = tr.office(oid)
            for k in range(1, n_cases + 1):
                u = min(upc, left)
                left -= u
                labels.append({"label_type": "office", "office_name": TR._s(off.get("company")), "office_address": TR._s(off.get("office_address")),
                               "floor_suite": TR._s(off.get("floor_suite")), "deliver_to": TR._s(off.get("pantry_owner_name")),
                               "brand_name": c["brand_name"], "product_name": TR._s(c.get("product_sku")), "units_in_case": str(u),
                               "case_number": str(k) if n_cases > 1 else "", "case_total": str(n_cases) if n_cases > 1 else "",
                               "drop_date": T.isoformat(), "office_id": oid, "campaign_id": cid, "drop_id": drop_id, "phone": ph(tr, "founder_phone")})
            rows.append((oid, cid, c["brand_name"], units, n_cases, upc))
            posts.setdefault(oid, []).append((c, links[(cid, oid, "post")]))
        reserve = max(0, int(lad["units_received"] - lad["units_rejected"] - lad["units_allocated"]))
        labels.append({"label_type": "reserve", "brand_name": c["brand_name"], "product_name": TR._s(c.get("product_sku")),
                       "units_in_case": str(reserve), "case_number": "", "case_total": "", "drop_date": T.isoformat(),
                       "campaign_id": cid, "drop_id": drop_id, "phone": ph(tr, "founder_phone")})
    order += [o for o in posts if o not in order]
    cards.sort(key=lambda x: (order.index(x["office_id"]) if x["office_id"] in order else 99, x["campaign_id"]))
    labels.sort(key=lambda x: (x["label_type"] == "reserve", order.index(x["office_id"]) if x.get("office_id") in order else 99, x["campaign_id"], x.get("case_number", "")))
    return T, camps, cards, labels, posts, rows, problems, order


def release_text(tr, cid, lad):
    """The same release rule as the sheet's ship_release column, recomputed (tools/tracker.py, release_status)."""
    return tr.release_status(cid, lad)


def post_text(tr, office, items):
    name = tr.company_name
    if len(items) == 1:
        c, l = items[0]
        return ("New in the pantry today: %s %s, an emerging brand from %s. Take one, and if you have 20 seconds, "
                "tell them what you think: %s\nThree questions, anonymous, no login.\nCourtesy of %s.\n") % (
            c["brand_name"], TR._s(c.get("product_sku")), TR._s(tr.brand(TR._s(c["brand_id"])).get("hq_city")), l["short_url"], name)
    lines = ["New in the pantry today, %d emerging brands. Take one, and if you have 20 seconds, tell them what you think:" % len(items)]
    for c, l in items:
        lines.append("- %s %s: %s" % (c["brand_name"], TR._s(c.get("product_sku")), l["short_url"]))
    lines.append("Three questions each, anonymous, no login. Courtesy of %s." % name)
    return "\n".join(lines) + "\n"


def render(kind, json_path, pdf_path, final):
    cmd = ["node", os.path.join(common.IDENTITY, "render", "render.js"), kind, os.path.abspath(json_path), os.path.abspath(pdf_path), "--json"]
    if final:
        cmd.append("--final")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=common.IDENTITY, timeout=300)
    try:
        st = json.loads(r.stdout[r.stdout.index("{"):])
    except Exception:
        st = {"errors": [r.stdout[-300:] + r.stderr[-300:]]}
    return r.returncode, st


def qr_check(pdf, expected, out):
    """Rasterize every card page, decode its QR and match it to the card's office and campaign."""
    tmp = os.path.join(out, "_qr")
    os.makedirs(tmp, exist_ok=True)
    subprocess.run(["pdftoppm", "-r", "110", "-png", pdf, os.path.join(tmp, "p")], check=True)
    from PIL import Image
    pages = sorted(os.path.join(tmp, f) for f in os.listdir(tmp) if f.endswith(".png"))
    pngs = []
    for pg in pages:
        im = Image.open(pg)
        w, h = im.size
        front, back = pg[:-4] + "-front.png", pg[:-4] + "-back.png"
        im.crop((0, h // 2, w, h)).save(front)                       # the face that reads upright on the table
        im.crop((0, 0, w, h // 2)).rotate(180).save(back)            # the other face, turned the right way up
        pngs += [front, back]
        os.remove(pg)
    js = os.path.join(tmp, "decode.js")
    open(js, "w").write(DECODE_JS)
    nm = os.path.join(common.ROOT, "_work", "node", "node_modules")
    r = subprocess.run(["node", js, nm] + pngs, capture_output=True, text=True)
    got = [line.split("\t")[1] for line in r.stdout.strip().splitlines()]
    lines, bad = [], 0
    for i, card in enumerate(expected):
        g1 = got[2 * i] if 2 * i < len(got) else "missing page"
        g2 = got[2 * i + 1] if 2 * i + 1 < len(got) else "missing page"
        ok = g1 == card["qr_url"] and g2 == card["qr_url"]
        bad += 0 if ok else 1
        lines.append("%s  page %d  %s %s  expected %s  front %s  back %s" % ("OK  " if ok else "FAIL", i + 1, card["office_id"], card["campaign_id"], card["qr_url"], g1, g2))
    for f in pngs:
        os.remove(f)
    os.remove(js)
    os.rmdir(tmp)
    return bad, lines


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 1
    tr = TR.Tracker(argv[1])
    common.require_same_name(tr)
    drop_id, out = argv[2], argv[3]
    final = "--final" in argv
    os.makedirs(os.path.join(out, "posts"), exist_ok=True)
    T, camps, cards, labels, posts, rows, problems, order = kit(tr, drop_id, out, final)
    if problems:
        print("REFUSED kit for %s:" % drop_id)
        for p in problems:
            print("  - " + p)
        return 2
    json.dump(cards, open(os.path.join(out, "cards.json"), "w"), indent=2, ensure_ascii=False)
    json.dump(labels, open(os.path.join(out, "labels.json"), "w"), indent=2, ensure_ascii=False)
    code, st = render("tent-card", os.path.join(out, "cards.json"), os.path.join(out, "cards.pdf"), final)
    warn = st.get("warnings", [])
    if code not in (0,):
        print("REFUSED by the tent card template (exit %d):" % code)
        for e in st.get("errors", []):
            print("  - " + e)
        return 2
    code2, st2 = render("case-label", os.path.join(out, "labels.json"), os.path.join(out, "labels.pdf"), final)
    if code2 != 0:
        print("REFUSED by the case label template (exit %d):" % code2)
        for e in st2.get("errors", []):
            print("  - " + e)
        return 2
    bad, lines = qr_check(os.path.join(out, "cards.pdf"), cards, out)
    common.write(os.path.join(out, "qr-check.txt"), "\n".join(lines) + "\n")
    for oid, items in posts.items():
        common.write(os.path.join(out, "posts", "%s.txt" % oid), post_text(tr, oid, items))
    checklist(tr, drop_id, T, camps, rows, order, out, warn + st2.get("warnings", []), st.get("fit", []), cards)
    print("kit %s: %d cards, %d labels, %d posts, QR %s" % (drop_id, len(cards), len(labels), len(posts), "all match" if not bad else "%d FAIL" % bad))
    return 0 if not bad else 2


def checklist(tr, drop_id, T, camps, rows, order, out, warnings, fit, cards):
    sample = common.is_sample(drop_id)
    model = TR._s(tr.drops[drop_id]["delivery_model"])
    body = ["<h1>Kit checklist · %s · %s</h1>" % (common.E(drop_id), common.fmt_date(T)),
            "<p>Delivery model: <b>%s</b>. Pack on T-1 (%s). One labeled case per office per brand. Counts must match this sheet.</p>" % (
                common.E(model), common.fmt_date(opscal.add_bd(T, -1)))]
    faces = {(c["office_id"], c["campaign_id"]): (f or {}) for c, f in zip(cards, fit + [{}] * len(cards))}
    body.append("<table><tr><th>Stop</th><th>Office</th><th>Brand</th><th>Units</th><th>Cases</th><th>Tent card</th><th>Packed</th></tr>")
    for oid in order:
        for (o, cid, brand, units, n_cases, upc) in [r for r in rows if r[0] == oid]:
            f = faces.get((oid, cid), {})
            note = "front face carries the ingredient list: <b>this side faces the room</b>" if f.get("ingredients_on_front_face") else ""
            body.append("<tr><td>%s</td><td>%s<br><span class='small muted'>%s</span></td><td>%s</td><td>%d</td><td>%d%s</td><td>1 + 1 spare %s</td><td><span class='chk'></span></td></tr>" % (
                order.index(oid) + 1, common.E(TR._s(tr.office(oid).get("company"))), common.E(oid), common.E(brand), units, n_cases,
                (" (%d a case)" % upc) if n_cases > 1 else "", note))
    body.append("</table>")
    body.append("<h2>Reserve (stays with you, never left at an office)</h2><table><tr><th>Brand</th><th>Reserve units</th><th>Bagged and labeled</th></tr>")
    for cid in camps:
        lad = tr.ladder(cid)
        body.append("<tr><td>%s</td><td>%d</td><td><span class='chk'></span></td></tr>" % (
            common.E(lad["campaign"]["brand_name"]), int(lad["units_received"] - lad["units_rejected"] - lad["units_allocated"])))
    body.append("</table>")
    body.append("<h2>Before you leave (plan appendix J)</h2><ul>" + "".join("<li><span class='chk'></span>%s</li>" % common.E(x) for x in [
        "Cases labeled per office; counts match this sheet",
        "Tent cards: print cards.pdf twice (one to place, one spare per office and brand); qr-check.txt says OK on every line; test-scan one card per brand",
        "Allergen line on each card checked word for word against the package in your hand",
        "Reserve units bagged, labeled RESERVE, per brand",
        "Route sheet printed: receiving windows and owner phone numbers",
        "Certificate of insurance PDF on your phone (and sent ahead to buildings that require it)",
        "Phone charged, battery pack, tape, box cutter, marker, hand truck",
        "Text each owner 'on my way' 20 minutes out",
        "Two photos per stop (wide pantry, close card and product); count logged before you leave"]) + "</ul>")
    if warnings:
        body.append("<h2>Template warnings to read</h2><ul>" + "".join("<li>%s</li>" % common.E(w) for w in warnings) + "</ul>")
    hp = os.path.join(out, "kit-checklist.html")
    common.write(hp, common.page("Kit " + drop_id, "".join(body), out, sample=sample))
    common.render(hp, os.path.join(out, "kit-checklist.pdf"))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
