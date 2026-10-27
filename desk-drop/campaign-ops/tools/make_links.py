#!/usr/bin/env python3
"""Short links and QR codes for one drop: two links per office per campaign.

  python3 tools/make_links.py TRACKER.xlsx DROP_ID OUT_DIR

Writes, in OUT_DIR:
  links-<drop>.csv              every link: campaign, office, type, slug, short URL, card code, destination
  shortio-import-<drop>.csv     path + original URL + title + tags, for the link tool's CSV import
  redirects-<drop>.txt          the same links as Cloudflare Pages _redirects lines (the no-tool fallback)
  qr/<slug>.png                 a QR for every qr link (segno, offline), for proofs and a spare sticker
  links-<drop>.html / .pdf      a proof sheet to test-scan at kitting

Rules (links/QR-AND-LINKS.md): the back-half never contains the company name; qr links are printed on
the card and counted as scans; post links go in the Slack or email post and are never called scans.
"""
import csv
import os
import sys
import urllib.parse

import segno

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402
import tracker as TR  # noqa: E402

UTM = "&utm_source=office-pantry&utm_medium={medium}&utm_campaign={campaign}&utm_content={office}"


def destination(template, card_code, cid, oid, kind):
    if not template:
        raise ValueError("%s: no survey_prefill_template on campaigns (forms/survey-form.md, step 9)" % cid)
    if template.count("CARDCODE") != 1:
        raise ValueError("%s: the prefill template must contain the text CARDCODE exactly once" % cid)
    if not template.startswith("https://docs.google.com/forms/"):
        raise ValueError("%s: the prefill template should start with https://docs.google.com/forms/" % cid)
    return template.replace("CARDCODE", urllib.parse.quote(card_code, safe=".-_")) + UTM.format(
        medium="qr" if kind == "q" else "post", campaign=cid.lower(), office=oid.lower())


SKIPPED = []


def links_for_drop(tr, drop_id):
    out = []
    domain = TR._s(tr.config.get("short_link_domain"))
    for cid, c in tr.campaigns.items():
        if TR._s(c["drop_id"]) != drop_id:
            continue
        tpl = TR._s(c.get("survey_prefill_template"))
        # Links only for offices that said yes: a declined office gets no card and no post (approvals close at T-10).
        yes = {o["office_id"] for o in tr.ladder(cid)["offices"] if o["approved"] == "Y"}
        for a in tr.approvals_for(cid):
            oid = TR._s(a["office_id"])
            if oid not in yes:
                SKIPPED.append("%s %s" % (cid, oid))
                continue
            code = "%s.%s" % (cid, oid)
            for kind in ("q", "p"):
                sl = TR.slug(cid, oid, kind)
                out.append({"campaign_id": cid, "office_id": oid, "company": TR._s(tr.office(oid).get("company")),
                            "brand_name": tr.campaign(cid)["brand_name"], "link_type": "qr" if kind == "q" else "post",
                            "slug": sl, "short_url": "https://%s/%s" % (domain, sl), "card_code": code,
                            "destination_url": destination(tpl, code, cid, oid, kind)})
    return out


def check_name(rows, company_name):
    bad = [r["slug"] for r in rows if company_name and company_name.lower().replace(" ", "") in r["slug"].lower().replace("-", "")]
    if bad:
        raise ValueError("company name found in link back-halves: %s" % bad)


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 1
    tr = TR.Tracker(argv[1])
    common.require_same_name(tr)
    drop_id, out = argv[2], argv[3]
    os.makedirs(os.path.join(out, "qr"), exist_ok=True)
    rows = links_for_drop(tr, drop_id)
    check_name(rows, tr.company_name)
    if len({r["slug"] for r in rows}) != len(rows):
        raise SystemExit("duplicate slugs")
    with open(os.path.join(out, "links-%s.csv" % drop_id), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(out, "shortio-import-%s.csv" % drop_id), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["path", "original_url", "title", "tags"])
        for r in rows:
            w.writerow([r["slug"], r["destination_url"], "%s %s %s" % (r["campaign_id"], r["office_id"], r["link_type"]),
                        "%s;%s" % (r["campaign_id"].lower(), r["link_type"])])
    with open(os.path.join(out, "redirects-%s.txt" % drop_id), "w", encoding="utf-8") as f:
        if common.is_sample(drop_id):
            f.write("# " + common.TEXT_BANNER + "\n")
        f.write("# Cloudflare Pages _redirects lines (fallback when no link tool is used). 302 so a destination can change.\n")
        for r in rows:
            f.write("/%s %s 302\n" % (r["slug"], r["destination_url"]))
    sample = common.is_sample(drop_id)
    cards = []
    for r in rows:
        if r["link_type"] != "qr":
            continue
        png = os.path.join(out, "qr", r["slug"] + ".png")
        segno.make(r["short_url"], error="m").save(png, scale=8, border=4)
        cards.append(r)
    body = ["<h1>Links and QR codes · %s</h1>" % common.E(drop_id),
            "<p class='small muted'>Test-scan every code at kitting (T-3) with your phone: it must open the survey for that brand with the card code shown. "
            "Then log one <b>baseline</b> reading per link on the scans tab (the link tool's total after your test).</p><table>"
            "<tr><th>QR</th><th>Office</th><th>Brand</th><th>Card code</th><th>Short link (on the card)</th><th>Post link (Slack or email)</th></tr>"]
    post = {(r["campaign_id"], r["office_id"]): r for r in rows if r["link_type"] == "post"}
    for r in cards:
        p = post[(r["campaign_id"], r["office_id"])]
        body.append("<tr><td><img src='qr/%s.png' width='90'></td><td>%s<br><span class='small muted'>%s</span></td><td>%s</td><td class='small'>%s</td>"
                    "<td class='small'>%s</td><td class='small'>%s</td></tr>" % (
                        common.E(r["slug"]), common.E(r["company"]), common.E(r["office_id"]), common.E(r["brand_name"]),
                        common.E(r["card_code"]), common.E(r["short_url"]), common.E(p["short_url"])))
    body.append("</table>")
    if SKIPPED:
        body.append("<p class='small muted'>No links for offices that said no: %s.</p>" % common.E(", ".join(SKIPPED)))
    hp = os.path.join(out, "links-%s.html" % drop_id)
    common.write(hp, common.page("Links " + drop_id, "".join(body), out, sample=sample))
    res = common.render(hp, os.path.join(out, "links-%s.pdf" % drop_id))
    print("links: %d (%d QR)%s -> %s %s" % (len(rows), len(cards), "; none for %d declined" % len(SKIPPED) if SKIPPED else "",
                                             out, "" if res.get("ok") else res))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
