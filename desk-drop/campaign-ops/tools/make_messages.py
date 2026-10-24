#!/usr/bin/env python3
"""Fill the message templates (templates/messages/) from the tracker for one drop and one step.
Drafts only: nothing is sent. You copy each draft into your email or phone.

  python3 tools/make_messages.py TRACKER.xlsx DROP_ID STEP OUT_DIR
  python3 tools/make_messages.py TRACKER.xlsx DROP_ID report OUT_DIR --reports REPORTS_DIR

STEP is one of: approvals, ship_release, t3, t1, on_my_way, placement_confirmation, day3, day5,
newsletter, report, redemption, slip.  Writes OUT_DIR/<step>/<recipient>.md

The report step needs --reports (the folder make_report.py wrote): it drafts the email only for a campaign whose
report.pdf is there, and refuses (exit 2, a <campaign>-NO-REPORT.md note) for one that has none, so no email says
"attached" without a report. Offices that turned a brand away at the door get no day-3 or day-5 ask about it.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402
import make_kit as MK  # noqa: E402
import make_links as ML  # noqa: E402
import make_report as MR  # noqa: E402
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


def and_list(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def excluded(lad):
    """Say plainly what was not counted (brand finance asks)."""
    out_w, unm = lad["responses_outside_window"], lad["responses_unmatched_code"]
    if not (out_w or unm):
        return ""
    parts = []
    if out_w:
        parts.append("%d outside the window (before the drop day or after day 5)" % out_w)
    if unm:
        parts.append("%d with a card code that matched no office" % unm)
    return "\n%d survey answers were not counted: %s.\n" % (out_w + unm, " and ".join(parts))


def run(tr, drop_id, step, out, reports=None):
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
    refused = []
    offices = []
    for cid in camps:
        for o in lads[cid]["offices"]:
            if o["office_id"] not in offices:
                offices.append(o["office_id"])

    def office_ctx(oid):
        o = tr.office(oid)
        # On the drop only: an office that turned a brand away at the door is not asked about it (R1-02).
        mine = [(cid, lads[cid]) for cid in camps if any(x["office_id"] == oid and x["on_drop"] == "Y" for x in lads[cid]["offices"])]
        names = [l["campaign"]["brand_name"] for c, l in mine]
        return o, mine, dict(base, pantry_owner_name=TR._s(o.get("pantry_owner_name")), pantry_owner_first=first(o.get("pantry_owner_name")),
                             owner_email=TR._s(o.get("pantry_owner_email")) or TR._s(o.get("contact_email")), owner_phone=o["owner_phone"],
                             receiving_window=TR._s(o.get("receiving_window")), survey_channel={"slack": "Slack", "email": "an email to the team"}.get(TR._s(o.get("survey_channel")), "your usual channel"),
                             brand_list="; ".join("%s (%s)" % (l["campaign"]["brand_name"], TR._s(l["campaign"].get("product_sku"))) for c, l in mine),
                             brand_list_short=and_list(names) if names else "")

    if step == "approvals":
        for oid in offices:
            off, mine, ctx = office_ctx(oid)
            blocks, modes, names = [], set(), []
            for cid in camps:
                lad = lads[cid]
                c = lad["campaign"]
                o = next((x for x in lad["offices"] if x["office_id"] == oid), None)
                if not o:
                    continue
                mc = TR._s(c.get("may_contain_verbatim"))
                what = {"contains_statement": "Allergen statement on the package, word for word",
                        "ingredient_list": "No allergen statement on the package; its ingredient list, word for word",
                        "single_ingredient": "Single-ingredient product; the package, word for word"}.get(TR._s(c.get("allergen_source")), "On the package, word for word")
                blocks.append("- %s: %s. %s. %s: \"%s\"%s. About %d units." % (
                    c["brand_name"], TR._s(c.get("product_sku")), CAT.get(c["category"], c["category"]), what,
                    TR._s(c.get("allergen_line_verbatim")), (" and \"%s\"" % mc) if mc else "", int(o["units_allocated"] or 0)))
                modes.add(o["approval_mode"])
                names.append(c["brand_name"])
            if not blocks:
                continue
            ctx.update(brand_blocks="\n".join(blocks) + "\n", brand_names=and_list(names),
                       approval_line=("Nothing comes unless you say yes. A one-word reply is perfect: yes to all, or which ones." if "explicit" in modes else
                                      "These come unless you say no by %s. A one-word reply is enough." % L(opscal.add_bd(T, -5))))
            written.append(write_msg(out, step, oid, meta, body, ctx))
    elif step == "ship_release":
        for cid in camps:
            lad = lads[cid]
            c = lad["campaign"]
            rel = MK.release_text(tr, cid, lad)
            if not rel.startswith("RELEASED"):
                common.write(os.path.join(out, step, "%s-NOT-RELEASED.md" % cid), "Not released: %s\nDo not confirm a ship date yet.\n" % rel)
                continue
            import math
            reserve0 = int(math.ceil(lad["units_allocated"] * TR._n(tr.config["reserve_share"]) - 1e-9))
            now_units = int(lad["units_allocated"]) + reserve0
            sent_units, sent_on = c.get("ship_email_units"), TR._d(c.get("ship_email_sent_date"))
            revised = ""
            if sent_units not in (None, "") and int(TR._n(sent_units)) != now_units and not lad["units_received"]:
                revised = ("**This replaces my ship-date email of %s.** The route changed: %d offices now take %s, so please ship %d units in all, "
                           "not %d.\n\n" % (L(sent_on) if sent_on else "earlier", lad["offices_approved"], c["brand_name"], now_units, int(TR._n(sent_units))))
            elif sent_units not in (None, "") and sent_on and sent_on < tr.today:
                continue   # already sent and nothing changed: no new draft
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
                       brand_contact_email=TR._s(b.get("contact_email")), offices=lad["offices_approved"], revised_line=revised,
                       revised_subject="Revised: " if revised else "", ship_lines=("- Office cartons: one per office to its own address (table below), each marked with our case label for that office (attached), "
                                   "by a service that delivers on %s itself, not earlier: offices hold nothing for us before the drop. One tracking number per office by %s.\n"
                                   "- Reserve (%d units): to %s, to arrive by %s.\n- Cancel-by date: %s." % (
                                       L(T), L(opscal.add_bd(T, -2)), reserve, TR._s(tr.config.get("receiving_address")), L(s["receive"]), L(s["ship_by"])))
                       if model == "direct-ship" else
                       ("- Ship by: %s. It must arrive by %s.\n- Ship to: %s" % (
                           L(s["ship_by_requested"]) + ("" if s["ship_by_requested"] == s["ship_by"] else " (latest %s)" % L(s["ship_by"])),
                           L(s["receive"]), TR._s(tr.config.get("receiving_address")))),
                       units_allocated=int(lad["units_allocated"]), reserve=reserve, units_to_ship=int(lad["units_allocated"]) + reserve,
                       best_by_min=(T + __import__("datetime").timedelta(days=int(TR._n(tr.config["min_shelf_life_days"])))).isoformat(),
                       units_table="\n".join(rows), card_text=card)
            written.append(write_msg(out, step, cid + ("-revised-%s" % tr.today.isoformat() if revised else ""), meta, body, ctx))
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
            if step == "t1":
                fd = TR._s(off.get("front_desk_fallback_ok")) == "Y"
                ctx["who_brings"] = {"founder": "I'll bring", "courier": "our courier will bring"}.get(model, "the carrier delivers")
                ctx["fallback_line"] = ("If you're out, it goes to the front desk, as we agreed." if fd else
                                        "If you'll be out, just tell me and we'll come the next morning instead." if model != "direct-ship" else
                                        "If you'll be out, tell me today and I'll ask the carrier to deliver the next morning instead.")
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
            placed = [o for o in lad["offices"] if o["on_drop"] == "Y" and o["placed_within_1bd"] == "Y"]
            notp = [o for o in lad["offices"] if o["on_drop"] == "Y" and o["placed_within_1bd"] != "Y"]
            away = lad["turned_away"]
            tab = ["| Office | Industry | Units on the shelf | Photo taken |", "| --- | --- | --- | --- |"]
            tab += ["| %s | %s | %d | %s |" % (o["office_label"], o["industry"], o["units_placed"], o["placement_photo_date"].isoformat()) for o in placed]
            share = TR._n(tr.config["founding_lock_per_office_usd"]) if TR._s(c["tier"]) == "founding" else TR._n(tr.config["extra_office_usd"])
            nb = ""
            if notp:
                nb = ("\nNot placed by the end of %s: %s. As the agreement says (section 8), we refund or take off the invoice $%d for each: $%d in all. "
                      "If a photo shows one was placed by then after all, I'll send it in a short follow-up and nothing changes.\n") % (
                    L(s["placement_confirm"]), ", ".join("office %s" % o["office_label"] for o in notp), share, share * len(notp))
            if away:
                how = {"declined": "declined it at the door", "building_refused": "could not take it: the building refused the delivery",
                       "not_delivered": "did not receive it"}
                nb += ("\n%s on the route %s on %s, so %s not placed and %s no letter in your report. As the agreement says (section 8), "
                       "we refund or take off the invoice $%d for %s: $%d in all.\n") % (
                    "One office" if len(away) == 1 else "%d offices" % len(away),
                    " or ".join(sorted({how.get(o["stop_outcome"], "did not take it") for o in away})), L(T),
                    "it was" if len(away) == 1 else "they were", "it has" if len(away) == 1 else "they have",
                    share, "it" if len(away) == 1 else "each", share * len(away))
            contracted = int(TR._n(c.get("offices_contracted")) or lad["offices_approved"])
            short = contracted - lad["offices_approved"]
            if short > 0:
                nb += ("\n%s of the %d offices in your agreement %s not on this drop for %s (an office declined it, or none was free), and no "
                       "roster office could take %s place. As the agreement says (section 8), $%d comes off for each: $%d in all.\n") % (
                    "One" if short == 1 else str(short), contracted, "was" if short == 1 else "were", c["brand_name"],
                    "its" if short == 1 else "their", share, share * short)
            today = tr.today
            credits = [r for r in tr.rows["invoices"] if TR._s(r["campaign_id"]) == cid and TR._s(r["invoice_type"]) == "credit_note"
                       and TR._d(r.get("issued_date")) and TR._d(r.get("issued_date")) <= today]
            bal = ""
            balinv = [r for r in tr.rows["invoices"] if TR._s(r["campaign_id"]) == cid and TR._s(r["invoice_type"]) == "standard_balance"]
            if TR._s(c["tier"]) == "standard" and balinv:
                applied = [r for r in credits if not TR._d(r.get("paid_date"))]
                gross = TR._n(balinv[0]["amount_usd"]) + TR._n(balinv[0].get("sales_tax_usd"))
                net = gross + sum(TR._n(r["amount_usd"]) for r in applied)
                bal = "\nDue today, on this confirmation: $%s by bank transfer (invoice %s attached%s).\n" % (
                    "{:,.2f}".format(net), TR._s(balinv[0]["invoice_id"]),
                    (", $%s second half less credit note %s" % ("{:,.2f}".format(gross), " and ".join(TR._s(r["invoice_id"]) for r in applied))) if applied else "")
            elif TR._s(c["tier"]) == "standard":
                bal = "\nThe second half of the price is due today, on this confirmation: invoice to follow, by bank transfer.\n"
            refunds = [r for r in credits if TR._d(r.get("paid_date")) or TR._s(c["tier"]) == "founding"]
            if refunds and TR._s(c["tier"]) == "founding":
                bal += "\nWe refund $%s to the account your payment came from within five business days (credit note %s attached).\n" % (
                    "{:,.2f}".format(-sum(TR._n(r["amount_usd"]) for r in refunds)), " and ".join(TR._s(r["invoice_id"]) for r in refunds))
            ctx = dict(base, brand_contact_name=TR._s(b.get("contact_name")), brand_contact_first=first(b.get("contact_name")),
                       brand_contact_email=TR._s(b.get("contact_email")), brand_name=c["brand_name"], placed_count=len(placed),
                       offices=contracted, placed_table="\n".join(tab), not_placed_block=nb, balance_block=bal)
            written.append(write_msg(out, step, cid, meta, body, ctx))
    elif step in ("report", "redemption", "newsletter"):
        for cid in camps:
            lad = lads[cid]
            c = lad["campaign"]
            b = tr.brand(TR._s(c["brand_id"]))
            if step == "newsletter" and TR._s(c.get("newsletter_option")) != "Y":
                continue
            if step == "report":
                pdf = os.path.join(reports, cid, "report.pdf") if reports else ""
                if not (pdf and os.path.exists(pdf)):
                    common.write(os.path.join(out, step, "%s-NO-REPORT.md" % cid),
                                 "No report email for %s: there is no report PDF (%s). Run tools/make_report.py first, and fix whatever "
                                 "it refuses; this email says the report is attached.\n" % (cid, pdf or "no --reports folder given"))
                    refused.append(cid)
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
                       discount_code=TR._s(c.get("discount_code")), count=TR._s(c.get("newsletter_passed_count")) or "[N]",
                       excluded_line=excluded(lad), roster_note=("\n" + MR.roster_note(lad) + "\n") if lad["turned_away"] else "")
            written.append(write_msg(out, step, cid, meta, body, ctx))
    elif step == "slip":
        new = opscal.slip(T)
        names = " and ".join(l["campaign"]["brand_name"] for l in lads.values())
        for oid in offices:
            off = tr.office(oid)
            ctx = dict(base, name_first=first(off.get("pantry_owner_name")), brand_list_short=names, old_date_long=L(T), new_date_long=L(new))
            written.append(write_msg(out, step, oid, meta, body, ctx))
    run.refused = refused
    return written


def main(argv):
    if len(argv) < 5:
        print(__doc__)
        return 1
    reports = argv[argv.index("--reports") + 1] if "--reports" in argv else None
    if argv[3] == "report" and not reports:
        print("usage: the report step needs --reports REPORTS_DIR (the folder make_report.py wrote)")
        return 1
    tr = TR.Tracker(argv[1])
    common.require_same_name(tr)
    w = run(tr, argv[2], argv[3], argv[4], reports)
    print("%s: %d drafts -> %s" % (argv[3], len(w), os.path.join(argv[4], argv[3])))
    if getattr(run, "refused", None):
        print("REFUSED (no report PDF): " + ", ".join(run.refused))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
