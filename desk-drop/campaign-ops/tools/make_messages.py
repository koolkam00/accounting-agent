#!/usr/bin/env python3
"""Fill the message templates (templates/messages/) from the tracker for one drop and one step.
Drafts only: nothing is sent. You copy each draft into your email or phone.

  python3 tools/make_messages.py TRACKER.xlsx DROP_ID STEP OUT_DIR

STEP is one of: approvals, ship_release, t3, t1, on_my_way, placement_confirmation, day3, day5,
newsletter, report, redemption, slip.  Writes OUT_DIR/<step>/<recipient>.md
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402
import make_kit as MK  # noqa: E402
import make_links as ML  # noqa: E402
import opscal  # noqa: E402
import tracker as TR  # noqa: E402

TPL = os.path.join(common.ROOT, "templates", "messages")
FILES = {"approvals": "01-approval-request.md", "ship_release": "02-ship-release.md", "t3": "03-office-window-and-post.md",
         "t1": "04-t-minus-1-text.md", "on_my_way": "05-on-my-way-text.md", "placement_confirmation": "06-placement-confirmation.md",
         "day3": "07-day3-photo-request.md", "day5": "08-day5-close.md", "newsletter": "09-newsletter-pass-on.md",
         "report": "10-report.md", "redemption": "11-redemption-check.md", "slip": "12-slip-notice.md"}
CAT = {k: lab for k, lab, b in __import__("json").load(open(os.path.join(common.ROOT, "spec", "forms.json")))["categories"]}


def load(step):
    txt = open(os.path.join(TPL, FILES[step]), encoding="utf-8").read()
    head, body = txt.split("\n---\n", 1)
    meta = dict(line.split(": ", 1) for line in head.strip().splitlines() if ": " in line)
    return meta, body


def fill(text, ctx):
    def rep(m):
        k = m.group(1)
        if k not in ctx:
            raise KeyError("template field {%s} has no value" % k)
        return str(ctx[k])
    return re.sub(r"\{([a-z0-9_]+)\}", rep, text)


def first(name):
    n = TR._s(name)
    return n.split(" ")[1] if n.startswith("SAMPLE ") and len(n.split(" ")) > 1 else (n.split(" ")[0] if n else "there")


def L(d):
    return common.fmt_date(d, "%A %B %-d") if d else ""


def base_ctx(tr):
    return {"founder_name": TR._s(tr.config.get("founder_name")), "founder_first": TR._s(tr.config.get("founder_name")).strip("[]").split(" ")[0] if not TR._s(tr.config.get("founder_name")).startswith("[") else "[FOUNDER NAME]",
            "founder_phone": TR._s(tr.config.get("founder_phone")), "company_name": tr.company_name,
            "min_shelf_life_days": int(TR._n(tr.config.get("min_shelf_life_days")))}


def write_msg(out, step, who, meta, body, ctx):
    subject = fill(meta.get("subject", ""), ctx) if meta.get("subject") else ""
    to = fill(meta.get("to", ""), ctx)
    parts = body.split("\n---\n")
    text = "DRAFT (not sent). When: %s\nTo: %s\n%s\n%s" % (meta.get("when", ""), to, ("Subject: " + subject + "\n") if subject else "", fill(parts[0], ctx))
    if len(parts) > 1:
        text += "\n--- for you, not for the email ---\n" + fill(parts[1], ctx)
    p = os.path.join(out, step, "%s.md" % who)
    common.write(p, text)
    return p


def run(tr, drop_id, step, out):
    T = tr.drop_date(drop_id)
    s = opscal.sop_dates(T)
    meta, body = load(step)
    camps = [cid for cid, c in tr.campaigns.items() if TR._s(c["drop_id"]) == drop_id]
    lads = {cid: tr.ladder(cid) for cid in camps}
    links = {(r["campaign_id"], r["office_id"], r["link_type"]): r for r in ML.links_for_drop(tr, drop_id)} if all(
        TR._s(tr.campaigns[c].get("survey_prefill_template")) for c in camps) else {}
    model = TR._s(tr.drops[drop_id]["delivery_model"])
    base = base_ctx(tr)
    base.update(drop_date_long=L(T), drop_date_short=common.fmt_date(T, "%a %b %-d"), day3_long=L(s["check_day3"]),
                close_long=L(s["close"]), report_due_long=L(s["report_due"]), t1_long=L(s["placement_confirm"]),
                debrief_long=L(s["debrief"]), receive_by_long=L(s["receive"]), kit_print_long=L(s["kit_print"]),
                card_reply_by_long=L(opscal.add_bd(T, -4)), cancel_by_long=L(s["ship_by"]),
                ship_by_requested_long=L(s["ship_by_requested"]), delete_by_long=L(s["newsletter_delete"]))
    written = []
    offices = []
    for cid in camps:
        for o in lads[cid]["offices"]:
            if o["office_id"] not in offices:
                offices.append(o["office_id"])

    def office_ctx(oid):
        o = tr.office(oid)
        mine = [(cid, lads[cid]) for cid in camps if any(x["office_id"] == oid and x["approved"] == "Y" for x in lads[cid]["offices"])]
        names = [l["campaign"]["brand_name"] for c, l in mine]
        return o, mine, dict(base, pantry_owner_name=TR._s(o.get("pantry_owner_name")), pantry_owner_first=first(o.get("pantry_owner_name")),
                             owner_email=TR._s(o.get("pantry_owner_email")) or TR._s(o.get("contact_email")), owner_phone=o["owner_phone"],
                             receiving_window=TR._s(o.get("receiving_window")), survey_channel={"slack": "Slack", "email": "an email to the team"}.get(TR._s(o.get("survey_channel")), "your usual channel"),
                             brand_list="; ".join("%s (%s)" % (l["campaign"]["brand_name"], TR._s(l["campaign"].get("product_sku"))) for c, l in mine),
                             brand_list_short=" and ".join(names))

    if step == "approvals":
        for cid in camps:
            lad = lads[cid]
            c = lad["campaign"]
            for o in lad["offices"]:
                off, mine, ctx = office_ctx(o["office_id"])
                mc = TR._s(c.get("may_contain_verbatim"))
                ctx.update(brand_name=c["brand_name"], product_sku=TR._s(c.get("product_sku")), category_label=CAT.get(c["category"], c["category"]),
                           allergen_line=TR._s(c.get("allergen_line_verbatim")), may_contain_line=(" " + mc) if mc else "",
                           units=int(o["units_allocated"] or 0),
                           approval_line=("Nothing comes unless you say yes: a one-word reply is perfect." if o["approval_mode"] == "explicit" else
                                          "It comes unless you say no by %s. A one-word reply is enough." % L(opscal.add_bd(T, -5))))
                written.append(write_msg(out, step, "%s-%s" % (cid, o["office_id"]), meta, body, ctx))
    elif step == "ship_release":
        for cid in camps:
            lad = lads[cid]
            c = lad["campaign"]
            rel = MK.release_text(tr, cid, lad)
            if not rel.startswith("RELEASED"):
                common.write(os.path.join(out, step, "%s-NOT-RELEASED.md" % cid), "Not released: %s\nDo not confirm a ship date yet.\n" % rel)
                continue
            b = tr.brand(TR._s(c["brand_id"]))
            rows = ["| Office | Units | Address |", "| --- | --- | --- |"]
            for o in lad["offices"]:
                if o["approved"] == "Y":
                    off = tr.office(o["office_id"])
                    rows.append("| %s | %d | %s |" % (o["office_label"], o["units_allocated"], ("%s, %s" % (TR._s(off.get("office_address")), TR._s(off.get("floor_suite")))) if model == "direct-ship" else "with the rest, to the address above"))
            card = "> %s\n> %s\n> %s %s\n> %s" % (c["brand_name"], TR._s(c.get("card_sentences")), TR._s(c.get("allergen_line_verbatim")),
                                                TR._s(c.get("may_contain_verbatim")), TR._s(c.get("retailer_line")))
            import math
            reserve = int(math.ceil(lad["units_allocated"] * TR._n(tr.config["reserve_share"]) - 1e-9))
            ctx = dict(base, brand_contact_name=TR._s(b.get("contact_name")), brand_contact_first=first(b.get("contact_name")),
                       brand_contact_email=TR._s(b.get("contact_email")), offices=lad["offices_approved"],
                       ship_to=("each office's own address (table below), each carton marked with our case label for that office, to arrive on %s" % L(T)) if model == "direct-ship" else TR._s(tr.config.get("receiving_address")),
                       units_allocated=int(lad["units_allocated"]), reserve=reserve, units_to_ship=int(lad["units_allocated"]) + reserve,
                       best_by_min=(T + __import__("datetime").timedelta(days=int(TR._n(tr.config["min_shelf_life_days"])))).isoformat(),
                       direct_ship_block=("\nDirect to offices: please use a service that delivers on %s, send one tracking number per office by %s, and ship the %d reserve units to %s by %s.\n" % (
                           L(T), L(opscal.add_bd(T, -2)), reserve, TR._s(tr.config.get("receiving_address")), L(s["receive"]))) if model == "direct-ship" else "",
                       units_table="\n".join(rows), card_text=card)
            written.append(write_msg(out, step, cid, meta, body, ctx))
    elif step in ("t3", "t1", "on_my_way", "day3", "day5"):
        for oid in offices:
            off, mine, ctx = office_ctx(oid)
            if not mine:
                continue
            if step == "t3":
                items = [(l["campaign"], links[(c, oid, "post")]) for c, l in mine] if links else []
                ctx["post_text"] = MK.post_text(tr, oid, items) if items else "[POST TEXT: add the survey prefill templates first]"
                stop = next((x for x in tr.rows["stops"] if TR._s(x["drop_id"]) == drop_id and TR._s(x["office_id"]) == oid), {})
                ctx["placement_photo_who"] = "I'll take it if I place it myself" if model == "founder" else "you or the courier"
            if step == "day3":
                low = [l["campaign"]["brand_name"] for c, l in mine for x in l["offices"] if x["office_id"] == oid and x["survey_responses"] < 5]
                ctx["responses_nudge"] = (" Also: %s has under five survey answers from your team so far. If you can, a one-line reminder in %s would help." % (
                    " and ".join(low), ctx["survey_channel"])) if low else ""
            if step == "day5":
                coll = [l["campaign"]["brand_name"] for c, l in mine if TR._s(l["campaign"].get("unused_product_election")) == "return"]
                rel = [l["campaign"]["brand_name"] for c, l in mine if TR._s(l["campaign"].get("unused_product_election")) != "return"]
                asks = []
                if rel:
                    asks.append("Could you send one more photo of the %s shelf and how many are left? Whatever is left is yours to keep." % " and ".join(rel))
                if coll:
                    asks.append("I'll come by in your window to collect what's left of %s and count it myself, so no photo needed for that one." % " and ".join(coll))
                ctx["close_ask"] = " ".join(asks)
            written.append(write_msg(out, step, oid, meta, body, ctx))
    elif step == "placement_confirmation":
        for cid in camps:
            lad = lads[cid]
            c = lad["campaign"]
            b = tr.brand(TR._s(c["brand_id"]))
            placed = [o for o in lad["offices"] if o["approved"] == "Y" and o["placed_within_1bd"] == "Y"]
            notp = [o for o in lad["offices"] if o["approved"] == "Y" and o["placed_within_1bd"] != "Y"]
            tab = ["| Office | Industry | Units on the shelf | Photo taken |", "| --- | --- | --- | --- |"]
            tab += ["| %s | %s | %d | %s |" % (o["office_label"], o["industry"], o["units_placed"], o["placement_photo_date"].isoformat()) for o in placed]
            share = TR._n(tr.config["founding_lock_per_office_usd"]) if TR._s(c["tier"]) == "founding" else TR._n(tr.config["extra_office_usd"])
            nb = ""
            if notp:
                nb = ("\nNot placed by the end of %s: %s. As the agreement says (section 8), we refund or take off the invoice $%d for each: $%d in all. "
                      "If a photo shows one was placed by then after all, I'll send it in a short follow-up and nothing changes.\n") % (
                    L(s["placement_confirm"]), ", ".join("office %s" % o["office_label"] for o in notp), share, share * len(notp))
            bal = ""
            if TR._s(c["tier"]) == "standard":
                bal = "\nThe second half of the price is due today, on this confirmation: invoice attached, by bank transfer.\n"
            ctx = dict(base, brand_contact_name=TR._s(b.get("contact_name")), brand_contact_first=first(b.get("contact_name")),
                       brand_contact_email=TR._s(b.get("contact_email")), brand_name=c["brand_name"], placed_count=len(placed),
                       offices=lad["offices_approved"], placed_table="\n".join(tab), not_placed_block=nb, balance_block=bal)
            written.append(write_msg(out, step, cid, meta, body, ctx))
    elif step in ("report", "redemption", "newsletter"):
        for cid in camps:
            lad = lads[cid]
            c = lad["campaign"]
            b = tr.brand(TR._s(c["brand_id"]))
            if step == "newsletter" and TR._s(c.get("newsletter_option")) != "Y":
                continue
            if step == "redemption" and not TR._s(c.get("discount_code")):
                continue
            red = lad["code_redemptions_to_date"]
            ctx = dict(base, brand_contact_name=TR._s(b.get("contact_name")), brand_contact_first=first(b.get("contact_name")),
                       brand_contact_email=TR._s(b.get("contact_email")), brand_name=c["brand_name"],
                       delivered=int(lad["units_delivered"]), placed=int(lad["units_placed"]), placed_1bd=int(lad["units_placed_within_1bd"]),
                       depleted="not counted" if lad["units_depleted_day5"] is None else int(lad["units_depleted_day5"]),
                       responses=lad["survey_responses"], scans=int(lad["qr_scans"]),
                       redemptions_part=(", and %d code redemptions so far, as you reported them" % red) if red is not None else "",
                       discount_code=TR._s(c.get("discount_code")), count=TR._s(c.get("newsletter_passed_count")) or "[N]")
            written.append(write_msg(out, step, cid, meta, body, ctx))
    elif step == "slip":
        new = opscal.slip(T)
        names = " and ".join(l["campaign"]["brand_name"] for l in lads.values())
        for oid in offices:
            off = tr.office(oid)
            ctx = dict(base, name_first=first(off.get("pantry_owner_name")), brand_list_short=names, old_date_long=L(T), new_date_long=L(new))
            written.append(write_msg(out, step, oid, meta, body, ctx))
    return written


def main(argv):
    if len(argv) < 5:
        print(__doc__)
        return 1
    tr = TR.Tracker(argv[1])
    w = run(tr, argv[2], argv[3], argv[4])
    print("%s: %d drafts -> %s" % (argv[3], len(w), os.path.join(argv[4], argv[3])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
