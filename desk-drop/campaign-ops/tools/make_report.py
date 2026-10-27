#!/usr/bin/env python3
"""The one-page brand report: tracker rows -> the identity workstream's report JSON -> PDF.

  python3 tools/make_report.py TRACKER.xlsx CAMPAIGN_ID OUT_DIR --photos PHOTOS_DIR [--final]

  TRACKER.xlsx  the tracker downloaded from Google Sheets (File > Download > .xlsx)
  PHOTOS_DIR    the folder holding photos/<campaign_id>/<file_name> (the synced Drive folder)
  --final       a real report: refuses SAMPLE data and placeholders (D's --final)

Writes OUT_DIR/<campaign_id>/:
  report.json           exactly the fields in desk-drop-identity/templates/report/FIELDS.md
  report.pdf            rendered by desk-drop-identity/render/render.js (the layout is D's, unchanged)
  trace.csv             every number in the report and the tracker rows (or photo) it came from
  office-summary-<office>.md   each office's own summary for the team (counts and its comments)

An office that turned the brand away at the door (stop outcome declined, building_refused or not_delivered, nothing
delivered) is not on the drop: it gets no letter and no row, and trace.csv and the output say so in a roster note
(the report email carries the same note). Its people's survey answers (the post link may already be out) are counted
nowhere: every survey number, and every quoted comment, comes from offices on the drop only (review round 2, R2-01).

Two lines are put ahead of the founder's "What we learned" lines on the page itself, until the report template has fields
for them (review round 2, R2-03 and R2-07): a roster line when fewer offices are in the report than the agreement names,
and a delivered line when an office counted its own carton (direct-ship) or nobody counted (packing list), because the
template's fixed text says "our count at handoff".

Refuses (exit 2) when: the drop date is invalid; an office on the drop has no day-5 count or no close link reading;
a quoted comment is not word for word from an in-window response; the sheet's own formulas disagree
with this arithmetic; or D's template refuses (claims, impossible numbers, photo dates).
"""
import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402
import opscal  # noqa: E402
import tracker as TR  # noqa: E402

MARK = re.compile(r"\[name removed\]|\[\.\.\.\]")
CAPWORD = re.compile(r"[A-Z][a-z]+(?:['\u2019-][A-Za-z]+)*")
ALWAYS_SAFE = set("""I I'm I'll I've I'd OK Monday Tuesday Wednesday Thursday Friday Saturday Sunday January February March April
May June July August September October November December""".split())


def redact(text, safe=()):
    """Office summaries quote comments word for word, so a name that slipped in would reach the pantry owner.
    Replace every capitalized word that does not start a sentence (and is not a safe word such as the brand or
    product) with [name removed]. It over-removes on purpose (file 13, D10: remove any name before quoting)."""
    keep = ALWAYS_SAFE | {w for x in safe for w in CAPWORD.findall(x or "")}
    lead = "SAMPLE " if text.startswith("SAMPLE ") else ""
    body = text[len(lead):]
    out, last = [], 0
    for m in CAPWORD.finditer(body):
        before = body[:m.start()].rstrip()
        starts = before == "" or before[-1] in ".!?:;\"'(\u201c"
        if starts or m.group(0) in keep:
            continue
        out.append(body[last:m.start()] + "[name removed]")
        last = m.end()
    out.append(body[last:])
    fixed = re.sub(r"(\[name removed\])(\s+\[name removed\])+", r"\1", "".join(out))
    return lead + fixed


def verbatim(quote, sources):
    """A quote is verbatim when, after taking out [name removed] and [...], every remaining piece
    appears, in order, inside one source comment. Returns the matching source or None."""
    pieces = [p.strip() for p in MARK.split(quote) if p.strip()]
    if not pieces:
        return None
    for src in sources:
        pos, ok = 0, True
        for p in pieces:
            i = src.find(p, pos)
            if i < 0:
                ok = False
                break
            pos = i + len(p)
        if ok:
            return src
    return None


def build(tr, cid, out_dir, photos_dir):
    lad = tr.ladder(cid)
    c = lad["campaign"]
    problems, trace = [], []
    T = lad["drop_date"]
    if T is None:
        raise SystemExit("REFUSED: %s has no valid drop date (drops tab, date_check)" % cid)
    if os.environ.get("OPS_SKIP_COMPARE") != "1":
        bad = [b for b in TR.compare(tr) if cid in b]
        if bad and not bad[0].startswith("no cached"):
            problems += ["sheet and arithmetic disagree: " + b for b in bad]
    resp = tr.response_rows(cid) or []
    win_end = lad["window_end"]
    inwin = [x for x in resp if T <= x["ts"].date() <= win_end]
    codes = {o["card_code"] for o in lad["offices"] if o["on_drop"] == "Y"}
    sources = [x["comment"] for x in inwin if x["code"] in codes and x["comment"].strip()]
    comments = []
    for i in (1, 2, 3):
        q = TR._s(c.get("comment_%d" % i)).strip()
        if not q:
            continue
        src = verbatim(q, sources)
        if not src:
            problems.append("comment_%d is not word for word from an in-window response from an office on the drop (%s's survey tab): %r" % (i, cid, q))
        else:
            row = next(x["_row"] for x in inwin if x["comment"] == src and x["code"] in codes)
            trace.append(("comment_%d" % i, q, "%s!G%d" % (cid, row)))
        comments.append(q)
    pdir = os.path.join(out_dir, "photos")
    os.makedirs(pdir, exist_ok=True)

    def photo(fn):
        if not fn:
            return ""
        src = os.path.join(photos_dir, cid, fn)
        if not os.path.exists(src):
            problems.append("photo file not found: %s" % src)
            return "[PHOTO]"
        shutil.copy(src, os.path.join(pdir, fn))
        return "photos/" + fn

    offices = []
    for o in lad["offices"]:
        oid = o["office_id"]
        if o["on_drop"] != "Y":
            continue
        if o["units_depleted_day5"] is None:
            problems.append("%s: no day-5 count (counts tab, remaining_day5)" % oid)
        if o["qr_scans"] is None:
            problems.append("%s: no close reading for %s (scans tab)" % (oid, o["qr_slug"]))
        offices.append({
            "office_label": o["office_label"], "industry": o["industry"], "headcount_band": o["headcount_band"],
            "units_delivered": str(int(o["units_delivered"])), "units_placed": str(int(o["units_placed"])),
            "placed_within_1bd": o["placed_within_1bd"], "units_topped_up": str(int(o["units_topped_up"])) if o["units_topped_up"] else "",
            "units_depleted_day5": "" if o["units_depleted_day5"] is None else str(int(o["units_depleted_day5"])),
            "survey_responses": str(o["survey_responses"]), "qr_scans": "" if o["qr_scans"] is None else str(int(o["qr_scans"])),
            "placement_photo": photo(o["placement_photo_file"]),
            "placement_photo_date": o["placement_photo_date"].isoformat() if o["placement_photo_date"] else "",
            "later_photo": photo(o["later_photo_file"]), "later_photo_day": str(o["later_photo_day"] or 5),
            "later_photo_date": o["later_photo_date"].isoformat() if o["later_photo_date"] else "",
        })
        for k, src in (("units_delivered", "inventory movement=delivered"), ("units_placed", "photos %s + counts placed" % o["placement_photo_file"]),
                       ("units_topped_up", "inventory movement=topped_up"), ("units_depleted_day5", "placed + topped up - counts remaining_day5"),
                       ("survey_responses", "%s!B card code %s, T to T+4" % (cid, o["card_code"])), ("qr_scans", "scans %s close - baseline" % o["qr_slug"])):
            trace.append(("%s %s" % (o["office_label"], k), o[k], src + rows_for(tr, cid, oid, k, o)))
    rpt = {
        "brand_name": c["brand_name"], "product_sku": TR._s(c.get("product_sku")),
        "cluster": TR._s(tr.config.get("cluster_name")), "tier": TR._s(c.get("tier")), "campaign_id": cid,
        "drop_date": T.isoformat(),
        "report_date": TR._d(c.get("report_delivered_date")).isoformat() if TR._d(c.get("report_delivered_date")) else "",
        "prepared_by": "" if TR._s(tr.config.get("founder_name")).startswith("[") else TR._s(tr.config.get("founder_name")),
        "offices": offices,
        "survey_tried_yes": str(lad["survey_tried_yes"]), "tried_no_didnt_see": str(lad["tried_no_didnt_see"]),
        "tried_no_not_for_me": str(lad["tried_no_not_for_me"]), "tried_no_gone": str(lad["tried_no_gone"]),
        "survey_rating_avg": "" if lad["survey_rating_avg"] is None else ("%.1f" % lad["survey_rating_avg"]),
        "survey_rating_n": str(lad["survey_rating_n"]), "survey_buy_yes": str(lad["survey_buy_yes"]),
        "survey_buy_maybe": str(lad["survey_buy_maybe"]), "survey_buy_no": str(lad["survey_buy_no"]),
        "comments_total": str(lad["comments_total"]),
        "comment_1": comments[0] if len(comments) > 0 else "", "comment_2": comments[1] if len(comments) > 1 else "",
        "comment_3": comments[2] if len(comments) > 2 else "",
        "code_redemptions_to_date": "" if lad["code_redemptions_to_date"] is None else str(int(lad["code_redemptions_to_date"])),
        "code_redemptions_as_of": lad["code_redemptions_as_of"].isoformat() if lad["code_redemptions_as_of"] else "",
        "retailer_velocity": TR._s(c.get("retailer_velocity")),
        "learned": "\n".join(page_notes(lad, tr) + ([TR._s(c.get("learned"))] if TR._s(c.get("learned")).strip() else [])),
        "recommendation": TR._s(c.get("recommendation")),
        "claims_reviewed": TR._s(c.get("claims_reviewed")), "claims_review_reason": TR._s(c.get("claims_review_reason")),
    }
    note = roster_note(lad)
    if note:
        trace.append(("roster note", note, "stops outcome " + ", ".join("%s %s" % (o["office_id"], o["stop_outcome"]) for o in lad["turned_away"])))
    for line in page_notes(lad, tr):
        trace.append(("learned, line added by the tool", line, "campaigns offices_contracted %s; approvals on_drop; inventory delivered count_source" % TR._s(c.get("offices_contracted"))))
    for k in ("survey_tried_yes", "survey_rating_avg", "survey_buy_yes", "survey_buy_maybe", "survey_buy_no", "comments_total"):
        trace.append((k, rpt[k], "%s!A:G, in-window rows whose card code matches an office on the drop" % cid))
    nod = lad.get("responses_office_not_on_drop") or 0
    if nod:
        offs = [o for o in lad["offices"] if o["on_drop"] != "Y" and o["survey_responses"]]
        trace.append(("not counted: answers from an office not on the drop", nod,
                      "%s!B card code %s (on_drop N): in no survey number and no quote" % (cid, ", ".join(o["card_code"] for o in offs))))
    trace.append(("code_redemptions_to_date", rpt["code_redemptions_to_date"], "redemptions, latest as_of " + rpt["code_redemptions_as_of"]))
    return rpt, problems, trace, lad


def page_notes(lad, tr=None):
    """Lines the report page itself must carry until D's template has fields for them (review round 2, R2-03 and R2-07)."""
    c = lad["campaign"]
    out = []
    ondrop = [o for o in lad["offices"] if o["on_drop"] == "Y"]
    contracted = int(TR._n(c.get("offices_contracted")) or 0)
    missing = contracted - len(ondrop)
    if contracted and missing > 0:
        away = lad["turned_away"]
        how = {"declined": "declined it at the door on the drop day", "building_refused": "could not take it (the building refused the delivery)",
               "not_delivered": "did not receive it"}
        sent = []
        if away:
            sent.append("%s that had approved %s %s." % ("One office" if len(away) == 1 else "%d offices" % len(away), c["brand_name"],
                                                       " or ".join(sorted({how.get(o["stop_outcome"], "did not take it") for o in away}))))
        rest = missing - len(away)
        if rest > 0:
            said_no = any(o["approved"] == "N" for o in lad["offices"])
            sent.append("%s not filled: %s, and no roster office could take %s place." % (
                "One place was" if rest == 1 else "%d places were" % rest, "an office said no" if said_no else "no office was free",
                "its" if rest == 1 else "their"))
        credited = True
        if tr is not None:
            share = TR._n(tr.config.get("founding_lock_per_office_usd")) if TR._s(c.get("tier")) == "founding" else TR._n(tr.config.get("extra_office_usd"))
            cred = -sum(TR._n(r["amount_usd"]) for r in tr.rows["invoices"] if TR._s(r["campaign_id"]) == TR._s(c["campaign_id"])
                        and TR._s(r["invoice_type"]) == "credit_note")
            credited = cred >= share * missing - 0.005
        out.append("Roster: %d of the %d offices in the agreement. %s %s" % (
            len(ondrop), contracted, " ".join(sent),
            ("A missing office is not charged: its share was credited." if missing == 1 else "Missing offices are not charged: their share was credited.")
            if credited else ("A missing office is not charged: a credit note follows." if missing == 1 else "Missing offices are not charged: a credit note follows.")))
    src = [o["delivered_count_source"] for o in ondrop if o["units_delivered"]]
    office, plist = src.count("office_count"), src.count("packing_list")
    others = len(src) - office - plist  # counted by us (founder or courier) at handoff
    if office:
        out.append(("Delivered: each office counted its own carton on arrival (the brand shipped direct), not us at handoff." if office == len(src) else
                    "Delivered: %d of the %d offices counted their own cartons on arrival (the brand shipped direct)%s." % (
                        office, len(src), ("; we counted %s%s at handoff" % ("" if plist else "the other ", "one" if others == 1 else str(others))) if others else "")))
    if plist:
        out.append("Delivered: at %d office%s the count is the brand's packing list; nobody counted it." % (plist, "" if plist == 1 else "s"))
    return out


def roster_note(lad):
    """One line for an office that approved the brand but turned it away at the door (R1-02). The report template has
    no roster-note field, so this goes into trace.csv and the report email (template 10, {roster_note})."""
    n = len(lad["turned_away"])
    if not n:
        return ""
    how = {"declined": "declined it at the door", "building_refused": "could not take it (the building refused the delivery)",
           "not_delivered": "did not receive it"}
    kinds = sorted({how.get(o["stop_outcome"], "did not take it") for o in lad["turned_away"]})
    return ("%s that had approved %s %s on the drop day. %s not in this report and %s not billed for %s: the credit is on the "
            "placement confirmation." % ("One office" if n == 1 else "%d offices" % n, lad["campaign"]["brand_name"], " or ".join(kinds),
                                         "It is" if n == 1 else "They are", "was" if n == 1 else "were", "it" if n == 1 else "them"))


def rows_for(tr, cid, oid, k, o):
    tab = {"units_delivered": ("inventory", "delivered"), "units_topped_up": ("inventory", "topped_up")}.get(k)
    if tab:
        rows = [r["_row"] for r in tr.rows[tab[0]] if TR._s(r["campaign_id"]) == cid and TR._s(r.get("office_id")) == oid and TR._s(r["movement"]) == tab[1]]
        return " (rows %s)" % ",".join(map(str, rows)) if rows else ""
    if k == "units_depleted_day5":
        rows = [r["_row"] for r in tr.rows["counts"] if TR._s(r["campaign_id"]) == cid and TR._s(r["office_id"]) == oid]
        return " (counts rows %s)" % ",".join(map(str, rows)) if rows else ""
    if k == "qr_scans":
        rows = [r["_row"] for r in tr.rows["scans"] if TR._s(r["slug"]) == o["qr_slug"]]
        return " (scans rows %s)" % ",".join(map(str, rows)) if rows else ""
    return ""


def office_summaries(tr, drop_id, out_dir):
    """One plain-text summary per office for its team (file 13, D9: totals and comments, never answers row by row)."""
    paths = []
    camps = [cid for cid, c in tr.campaigns.items() if TR._s(c["drop_id"]) == drop_id]
    offices = []
    for cid in camps:
        for a in tr.approvals_for(cid):
            if TR._s(a["office_id"]) not in offices:
                offices.append(TR._s(a["office_id"]))
    min_n = int(TR._n(tr.config.get("office_summary_min_answers")) or 5)
    for oid in offices:
        o = tr.office(oid)
        lines = ["%s: what your team said" % TR._s(o.get("company")), ""]
        shown = 0
        for cid in camps:
            lad = tr.ladder(cid)
            row = next((x for x in lad["offices"] if x["office_id"] == oid), None)
            if not row or row["on_drop"] != "Y":
                continue
            shown += 1
            resp = [x for x in (tr.response_rows(cid) or []) if x["code"] == row["card_code"] and lad["drop_date"] <= x["ts"].date() <= lad["window_end"]]
            n = len(resp)
            lines.append("%s (%s)" % (lad["campaign"]["brand_name"], TR._s(lad["campaign"].get("product_sku"))))
            lines.append("- %d answers from your team." % n + (" %d said they tried it." % row["tried_yes"] if n >= min_n else ""))
            if n < min_n:
                lines.append("- Fewer than %d answers, so they are not broken down here: that keeps each person's answer private." % min_n)
                lines.append(units_line(row))
                lines.append("")
                continue
            # The same rule for every figure: no rating or would-buy split from fewer people than the threshold.
            if row["rating_n"] >= min_n:
                lines.append("- Average rating %.1f of 5, from %d ratings." % (TR.xround(row["rating_sum"] / row["rating_n"], 1), row["rating_n"]))
                lines.append("- Would buy it: yes %d, maybe %d, no %d." % (row["buy_yes"], row["buy_maybe"], row["buy_no"]))
            else:
                lines.append("- Fewer than %d people rated it, so the ratings and would-buy answers are not shown here." % min_n)
            lines.append(units_line(row))
            safe = (lad["campaign"]["brand_name"], TR._s(lad["campaign"].get("product_sku")), TR._s(lad["campaign"].get("retailer_line")),
                    TR._s(tr.config.get("cluster_name")), TR._s(o.get("company")), tr.company_name)
            cm = [redact(x["comment"].strip(), safe) for x in resp if x["comment"].strip()]
            if cm:
                lines.append("- What people wrote, word for word, with anything that may be a name taken out:")
                lines += ["  \"%s\"" % x for x in cm]
            lines.append("")
        if not shown:
            continue   # nothing reached this office on this drop (it turned the brands away at the door): no summary
        lines += ["Answers are anonymous. This summary has totals and comments only, never anyone's individual answers, and no figure",
                  "drawn from fewer than %d people." % min_n,
                  "BEFORE SENDING: read every comment once more; replace anything else that could identify a person with [name removed] (legal pack file 13, D10)."]
        p = os.path.join(out_dir, "office-summary-%s.md" % oid)
        common.write(p, "\n".join(lines) + "\n")
        paths.append(p)
    return paths


def units_line(row):
    """Delivered, top-ups, placed and gone, so the numbers add up for a pantry owner (R1-11)."""
    top = int(row["units_topped_up"] or 0)
    gone = "not counted" if row["units_depleted_day5"] is None else "%d" % int(row["units_depleted_day5"])
    return "- Units: %d delivered%s, %d on the shelf in the placement photo, %s gone by day 5%s." % (
        row["units_delivered"], (", plus %d topped up on day 3" % top) if top else "", row["units_placed"], gone,
        " (of the shelf count plus the top-ups)" if top else "")


def render(json_path, pdf_path, final=False):
    cmd = ["node", os.path.join(common.IDENTITY, "render", "render.js"), "report", os.path.abspath(json_path), os.path.abspath(pdf_path), "--json"]
    if final:
        cmd.append("--final")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=common.IDENTITY, timeout=180)
    try:
        status = json.loads(r.stdout[r.stdout.index("{"):])
    except Exception:
        status = {"ready": False, "errors": [r.stdout[-400:] + r.stderr[-400:]]}
    return r.returncode, status


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("tracker")
    ap.add_argument("campaign_id")
    ap.add_argument("out_dir")
    ap.add_argument("--photos", required=True)
    ap.add_argument("--final", action="store_true")
    a = ap.parse_args(argv[1:])
    tr = TR.Tracker(a.tracker)
    common.require_same_name(tr)
    out = os.path.join(a.out_dir, a.campaign_id)
    os.makedirs(out, exist_ok=True)
    rpt, problems, trace, lad = build(tr, a.campaign_id, out, a.photos)
    jp = os.path.join(out, "report.json")
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(rpt, f, indent=2, ensure_ascii=False)
    with open(os.path.join(out, "trace.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["number", "value", "from"])
        w.writerows(trace)
    if problems:
        print("REFUSED %s:" % a.campaign_id)
        for p in problems:
            print("  - " + p)
        return 2
    code, status = render(jp, os.path.join(out, "report.pdf"), a.final)
    for wmsg in status.get("warnings", []):
        print("  warning: " + wmsg)
    c = lad["campaign"]
    safe = (c["brand_name"], TR._s(c.get("product_sku")), TR._s(c.get("retailer_line")), TR._s(tr.config.get("cluster_name")), tr.company_name)
    for i in (1, 2, 3):
        q = TR._s(rpt.get("comment_%d" % i))
        if q and redact(q, safe) != q:
            print("  warning: comment_%d may still hold a name: %r (replace it with [name removed] if it is one)" % (i, q))
    if code != 0:
        print("REFUSED by the report template (exit %d):" % code)
        for e in status.get("errors", []) + status.get("placeholders", [])[:5]:
            print("  - " + e)
        return 2
    office_summaries(tr, TR._s(lad["campaign"]["drop_id"]), a.out_dir)
    note = roster_note(lad)
    if note:
        print("  roster note (for the report email): " + note)
    print("report %s -> %s (sample=%s)" % (a.campaign_id, os.path.join(out, "report.pdf"), status.get("sample")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
