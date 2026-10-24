#!/usr/bin/env python3
"""Invoices by bank transfer, from the invoices tab. Numbers come from the campaign row; nothing is retyped.

  python3 tools/make_invoice.py TRACKER.xlsx INVOICE_ID OUT_DIR        # one invoice
  python3 tools/make_invoice.py TRACKER.xlsx --campaign CAMPAIGN_ID OUT_DIR   # every invoice of a campaign

Writes OUT_DIR/<invoice_id>.html and .pdf. Refuses an amount that differs from the price list
(founding_full = price; standard_deposit = 50%; standard_balance = the rest), except a credit note.
Payment: bank transfer only (card only if a brand insists: log the fee). The pre-ship invoice says
plainly that the ship date is confirmed when the money lands.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402
import opscal  # noqa: E402
import tracker as TR  # noqa: E402

E = common.E
TITLE = {"founding_full": "Office Placement Campaign, founding tier: paid in full before shipping",
         "standard_deposit": "Office Placement Campaign, standard tier: first 50%, due on signing",
         "standard_balance": "Office Placement Campaign, standard tier: second 50%, due at placement confirmation (T+1)",
         "credit_note": "Credit note"}


def expected(tr, inv, c):
    p = c["price_usd"] or 0
    half = TR.xround(p * TR._n(tr.config["deposit_share"]), 2)
    return {"founding_full": p, "standard_deposit": half, "standard_balance": p - half}.get(TR._s(inv["invoice_type"]))


def html(tr, inv, out_dir):
    cid = TR._s(inv["campaign_id"])
    c = tr.campaign(cid)
    lad = tr.ladder(cid)
    b = tr.brands.get(TR._s(c["brand_id"]), {})
    ty = TR._s(inv["invoice_type"])
    amt, tax = TR._n(inv["amount_usd"]), TR._n(inv.get("sales_tax_usd"))
    exp = expected(tr, inv, c)
    if ty != "credit_note" and exp is not None and abs(amt - exp) > 0.005:
        raise SystemExit("REFUSED %s: amount %.2f differs from the price list (%.2f). Put any credit on its own credit-note row." % (inv["invoice_id"], amt, exp))
    issued = TR._d(inv["issued_date"])
    due = opscal.add_bd(issued, int(TR._n(tr.config["founding_due_bd"]))) if ty == "founding_full" else issued
    T = lad["drop_date"]
    n = int(TR._n(c.get("offices_contracted")))
    desc = "%s<br><span class='small'>%s · %d offices in %s · drop %s, window %s to %s · campaign %s</span>" % (
        E(TITLE[ty]), E(c["brand_name"] + " " + TR._s(c.get("product_sku"))), n, E(TR._s(tr.config.get("cluster_name"))),
        E(common.fmt_date(T)), E(common.fmt_date(T)), E(common.fmt_date(lad["window_end"])), E(cid))
    lines = [(desc, amt)]
    if ty == "standard_balance":
        lines[0] = (desc + "<br><span class='small'>Placement confirmation sent %s.</span>" % E(common.fmt_date(opscal.add_bd(T, 1)) if T else ""), amt)
    if ty == "credit_note":
        lines = [("Credit: %s<br><span class='small'>Against campaign %s. Brand agreement section 8.</span>" % (E(TR._s(inv.get("note"))), E(cid)), amt)]
    rows = "".join("<tr><td>%s</td><td class='num'>%s</td></tr>" % (d, money(a)) for d, a in lines)
    pay = TR._s(tr.config.get("bank_details"))
    ship_line = ""
    if ty in ("founding_full", "standard_deposit"):
        ship_line = "<p><b>Your ship date is confirmed on the day this payment reaches our account.</b> Please ship by %s (latest %s).</p>" % (
            E(common.fmt_date(TR._d(lad["campaign"].get("ship_by_requested")) or opscal.sop_dates(T)["ship_by_requested"])) if T else "",
            E(common.fmt_date(opscal.add_bd(T, -10))) if T else "")
    body = """
<div style='display:flex;justify-content:space-between;align-items:flex-start'>
 <div><h1>%s</h1><div class='small'>%s<br>%s · %s</div></div>
 <div style='text-align:right'><h1>%s</h1><div class='small'>No. <b>%s</b><br>Issued %s<br>Due <b>%s</b></div></div>
</div>
<h2>Bill to</h2><p>%s<br>%s<br>%s</p>
<table><tr><th>Description</th><th class='num'>Amount (USD)</th></tr>%s
<tr><td>Sales tax</td><td class='num'>%s</td></tr>
<tr><td><b>Total</b></td><td class='num'><b>%s</b></td></tr></table>
<p class='small'>%s</p>
%s
<h2>How to pay</h2>
<p>By bank transfer (ACH or wire) to: %s<br>Reference: <b>%s</b>. No card fees on a bank transfer.</p>
<p class='small muted'>Questions: %s · %s. Terms: the signed campaign agreement (version %s) for campaign %s.</p>
""" % (E(tr.company_name), E(TR._s(tr.config.get("postal_address"))), E(TR._s(tr.config.get("founder_email"))), E(TR._s(tr.config.get("founder_phone"))),
       "Credit note" if ty == "credit_note" else "Invoice", E(TR._s(inv["invoice_id"])), E(common.fmt_date(issued)),
       E(common.fmt_date(due)) + ("" if ty != "founding_full" else " (five business days, and before shipping)") if ty != "credit_note" else "n/a",
       E(TR._s(b.get("brand_legal_name")) or "[BRAND LEGAL NAME]"), E(TR._s(b.get("billing_address")) or "[BRAND ADDRESS]"),
       E(TR._s(b.get("billing_email")) or TR._s(inv.get("sent_to"))), rows, money(tax), money(amt + tax),
       E(TR._s(tr.config.get("sales_tax_note"))), ship_line, E(pay), E(TR._s(inv["invoice_id"])),
       E(TR._s(tr.config.get("founder_email"))), E(TR._s(tr.config.get("founder_phone"))), E(TR._s(c.get("agreement_version"))), E(cid))
    css = ".num{text-align:right;white-space:nowrap}"
    return common.page("%s %s" % ("Credit note" if ty == "credit_note" else "Invoice", inv["invoice_id"]), body, out_dir,
                       sample=common.is_sample(inv["invoice_id"], cid), extra_css=css)


def money(x):
    return ("-$%s" % "{:,.2f}".format(-x)) if x < 0 else "$%s" % "{:,.2f}".format(x)


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 1
    tr = TR.Tracker(argv[1])
    if argv[2] == "--campaign":
        invs = [r for r in tr.rows["invoices"] if TR._s(r["campaign_id"]) == argv[3]]
        out = argv[4]
    else:
        invs = [r for r in tr.rows["invoices"] if TR._s(r["invoice_id"]) == argv[2]]
        out = argv[3]
    if not invs:
        raise SystemExit("no such invoice")
    for inv in invs:
        hp = common.write(os.path.join(out, "%s.html" % TR._s(inv["invoice_id"])), html(tr, inv, out))
        common.render(hp, hp[:-5] + ".pdf")
        print("invoice", inv["invoice_id"], "->", hp[:-5] + ".pdf")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
