#!/usr/bin/env python3
"""Build calls/call-cards.pdf: one page per side to keep in front of you on a call.

    NODE_PATH=$(npm root -g) python3 tools/build_call_cards.py

The questions are pulled from plan.md at build time, so the card always carries the plan's exact words.
"""
import html
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PLAN = os.path.join(os.path.dirname(ROOT), "plan.md")
OUT = os.path.join(ROOT, "_work", "partB", "print")
sys.path.insert(0, HERE)


def plan_questions():
    s = open(PLAN, encoding="utf-8").read()
    def block(start, end):
        a = s.index(start)
        b = s.index(end, a)
        return [re.sub(r"^\d+\.\s*", "", l).strip() for l in s[a:b].splitlines() if re.match(r"^\d+\.\s", l)]
    office = block("**Office conversation guide**", "A yes looks like")
    brand = block("**Brand conversation guide**", "**Tracking sheet columns**")
    probe = re.search(r'ask: "(If this goes well.*?per month\?)"', s).group(1)
    return office, brand, probe


def esc(t):
    return html.escape(t)


def card(title, sub, rows, blocks):
    tr = "".join(f"<tr><td class=n>{i}</td><td class=q>{q}</td><td class=m>{m}</td><td class=c>{c}</td></tr>" for i, (q, m, c) in enumerate(rows, start=1))
    bl = "".join(f"<div class=box><h3>{h}</h3>{b}</div>" for h, b in blocks)
    return f"""<section><div class=hd><h1>{title}</h1><div class=sub>{sub}</div></div>
<table><tr><th>#</th><th>Ask exactly (plan wording)</th><th>Min</th><th>Capture</th></tr>{tr}</table>
<div class=grid>{bl}</div></section>"""


def main():
    office, brand, probe = plan_questions()
    assert len(office) == 7 and len(brand) == 7, (len(office), len(brand))
    o_rows = [
        (esc(office[0]), 4, "who decides, who delivers (snack service Y/N), how often, cost a month (number only if given); pantry owner's name and title if it comes up"),
        (esc(office[1]), 1, "Tuesday number (low end of a range) + their words"),
        (esc(office[2]), 2, "do brands reach out (Y/N); ignore / accept / block, and why"),
        (esc(office[3]), 4, "what yes needs; what no means; objection codes; vetoes; security desk, certificate, freight hours"),
        (esc(office[4]), 2, "Y / N / maybe + words"),
        ("Frame first: <i>\"One hypothetical question, and it changes nothing about the free drop.\"</i> Then word for word: <b>\"" + esc(probe) + "\"</b>", 2,
         "silence after reading it; never suggest a number; verbatim; low and high USD a month; no budget = 0; don't know = blank"),
        (esc(office[6]), 1, "company and title; \"may I say you suggested it?\""),
    ]
    b_rows = [
        (esc(brand[0]), 4, "what they do now; what has not worked"),
        (esc(brand[1]), 3, "USD a quarter (low, high); who approves; controls_budget = Y only if they approve alone"),
        (esc(brand[2]), 2, "Y / N + what happened"),
        (esc(brand[3]).replace("Let them name a number before you mention $1,500.", "<b>Let them name a number before you mention $1,500.</b>"), 5,
         "their number + words FIRST; convert to one 500-unit, 10-office campaign; then the $1,500 line and their answer"),
        (esc(brand[4]), 3, "photos, depletion, words, scans, codes; 'sales lift' = objection want_sales_data"),
        (esc(brand[5]), 2, "store + street, or online with a code; compare with Clay's grade"),
        (esc(brand[6]), 3, "each stopper as an objection code"),
    ]
    o_blocks = [
        ("Open (30 s)", "Who you are; you are looking at whether free emerging brands, in exchange for a shelf photo and three survey questions, would help offices; not selling today; seven questions, 20 minutes, OK to take notes?"),
        ("Close (3 min)", "If positive: <b>\"If we did a first drop, who would receive it, and what's a good window on a Tuesday or Wednesday morning?\"</b> Then: \"Can I send you a one-pager?\" Ask before ever quoting them (no name, no company). Stop on time."),
        ("Gate 0 counts this office only if", "<b>yes_in_principle = Y</b> and <b>pantry owner named</b> and <b>receiving window named</b>. \"I need to ask facilities or HR\" = maybe."),
        ("Say only what is true today", "No brands yet. First drop planned for [DROP DATE: Tue 2027-01-12], only once five offices and the first brands sign. No fees either way. Sealed, labeled products; allergen line from the package. Anonymous survey, no employee details. Insurance: \"we will carry it before your first drop\"."),
        ("Never", "Employee names or details. Photos of people. A health claim. A date, brand or office count the tracker does not show."),
        ("After (10 min)", "Note_Office tab, row to paste, Clay write-back: call_date, status, yes_in_principle, call_notes, call_note_hook, next_action, next_action_date. Referrals = new Clay rows."),
    ]
    b_blocks = [
        ("Open (30 s)", "Who you are; testing an idea (a week in a handful of New York offices, photos and feedback, near their stores); not asking them to buy today; <b>a price question is coming, and their number comes first</b>; seven questions, about 25 minutes."),
        ("The anchor rule", "Ask Q4, then wait. \"I'll tell you, but I'd like your number first.\" Write it. Then: <b>\"For reference, the standard price I'm testing is $1,500 for ten offices. How does that land?\"</b> Founding price only if asked: five offices for $600, paid up front, $120 an office for the next two campaigns."),
        ("Gate 0 counts this brand only if", "the higher of the two numbers is <b>$500 or more</b> and the speaker <b>controls the budget</b> alone."),
        ("Weeks 4 to 7: the seven checks", "1 sealed, shelf-stable, 60+ days at the drop · 2 ingredients and nine allergens on the label · 3 store within ten blocks or online code · 4 ship 275 units to one Manhattan address in ten business days · 5 product liability certificate · 6 approves $600 alone · 7 why New York now. Excluded: alcohol, cannabis/CBD/THC, supplements, refrigerated, preparation, health claims."),
        ("Say only what is true today", "No offices signed until the tracker says so; no results yet (\"I'd rather tell you that than make up a number\"); no sales guarantee; no free trial; no employee data."),
        ("After (10 min)", "Note_Brand tab, row to paste, Clay write-back. Close: \"Who else should I be talking to?\", \"Can I come back once five offices have signed?\" (recontact Mon 2026-11-16), and permission before ever quoting them."),
    ]
    css = """
@page { size: Letter landscape; margin: 0.35in 0.4in; }
body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 9.8pt; color: #111; margin: 0; }
section { page-break-after: always; }
.hd { display: flex; align-items: baseline; gap: 12pt; border-bottom: 2px solid #1f3a5f; margin-bottom: 4pt; }
h1 { font-size: 15pt; margin: 0; }
.sub { color: #444; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #bbb; padding: 2.4pt 4pt; vertical-align: top; text-align: left; }
th { background: #1f3a5f; color: #fff; }
td.n { width: 12pt; font-weight: bold; } td.q { width: 47%; } td.m { width: 18pt; text-align: center; } td.c { color: #333; }
.grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 4pt; margin-top: 5pt; }
.box { border: 1px solid #bbb; padding: 3pt 5pt; } .box h3 { font-size: 10pt; margin: 0 0 2pt; color: #1f3a5f; }
.foot { font-size: 7.5pt; color: #555; margin-top: 4pt; }
"""
    from build_tracker import COMPANY_NAME
    doc = f"""<!doctype html><html><head><meta charset=utf-8><title>Call cards</title><style>{css}</style></head><body>
{card("Office call card", f"{esc(COMPANY_NAME)} · 20 minutes · weeks 1 to 3: no selling · full guide: calls/office-call-guide.md", o_rows, o_blocks)}
{card("Brand call card", f"{esc(COMPANY_NAME)} · 20 to 30 minutes · weeks 1 to 3: no selling · full guide: calls/brand-call-guide.md", b_rows, b_blocks)}
</body></html>"""
    os.makedirs(OUT, exist_ok=True)
    h = os.path.join(OUT, "call-cards.html")
    open(h, "w", encoding="utf-8").write(doc)
    pdf = os.path.join(ROOT, "calls", "call-cards.pdf")
    js = ('const { chromium } = require("playwright"); (async () => { const b = await chromium.launch(); const p = await b.newPage();'
          'await p.goto("file://" + process.argv[1]); await p.pdf({ path: process.argv[2], landscape: true, format: "Letter", printBackground: true, preferCSSPageSize: true });'
          'await p.setViewportSize({ width: 1100, height: 850 }); await p.screenshot({ path: process.argv[3], fullPage: true }); await b.close(); })();')
    subprocess.run(["node", "-e", js, h, pdf, os.path.join(OUT, "call-cards.png")], check=True)
    print("wrote", pdf)


if __name__ == "__main__":
    main()
