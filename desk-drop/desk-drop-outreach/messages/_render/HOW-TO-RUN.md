# How to run the fill script

`fill.py` fills the message templates with a Clay row, checks every message, renders the phone-width examples, and makes paste-ready drafts. It never sends anything and makes no network calls. Python 3, standard library only; the PNGs need node with Playwright.

Run everything from `desk-drop/desk-drop-outreach/messages/`.

## 1. Check every message (after any edit to a message file)

```bash
python3 _render/fill.py lint
```

Fills all 67 message blocks with the SAMPLE rows in a state that unlocks them and prints every finding. It fails (exit 1) on: more than one question (one ask per message; a numbered questionnaire counts as one), an exclamation mark, a banned word (guarantee outside "no guarantees", free trial outside "no free trial", lift, ROI, conversions, acquisition, "we work with", "spots left", "limited time", "best", "just checking in" and others), a touch 1 over 125 words or a follow-up over 75, a LinkedIn note over 200 characters or message over 600, "free" or "Re:" in a cold touch 1 subject, a link or attachment in touch 1, a follow-up not sent as a reply, a wrong weekday or an illegal drop date in any date slot, a missing footer, a message the tracker state does not unlock (`domain_ready`, `office_selling_on`, `brand_selling_on`, `attorney_cleared`, `llc_formed`, `startup_cpg_joined`), a campaign zero offer to a brand after the last-offer date, and any computed slot sentence whose wording is not in `04-slot-table.csv` or a message file. It warns when a touch 1 prints nothing about the person or company.

## 2. Rebuild the examples

```bash
python3 _render/fill.py examples
NODE_PATH=$(npm root -g) node _render/shoot.js
```

Writes `examples/*.html` from `examples/SAMPLE-examples.json` (which sequence, which SAMPLE row, which SAMPLE state, which start date), then `examples/png/*.png` at 390 px wide. Blue is from the row, amber dashed is a fallback, yellow is a slot, grey is your detail. Each card lists the fallbacks that fired and the checks it passed. Every page carries the SAMPLE banner.

## 3. Make today's drafts from a real daily view

```bash
python3 _render/fill.py drafts \
  --daily ../../clay-icp-tables/daily-view-offices.csv \
  --message office-discovery-1 \
  --date 2026-11-03 \
  --out drafts/2026-11-03
```

One `.txt` per row (To, Subject, body, signature), ready to paste into Gmail. `--message` is a block id from the message files (`office-discovery-1`, `brand-selling-1`, `li-office-discovery-1` ...). The variant (A or B) comes from the row's `sequence` column, or `--variant`. The state is `04-slot-state.csv` unless `--state` names another file. Rows are skipped, with the reason printed, when `do_not_contact` is not N, the status is wrong for the touch, the row is for the other side, the message is not unlocked, or nothing personal would print. Drafts go in `drafts/`, which you can delete at any time; do not commit drafts that hold real contacts.

Dates in drafts are written as the reader should see them ("Tuesday, January 12"; "January 12" in a subject). Your own details ([FOUNDER NAME], [PHONE], [EMAIL], [POSTAL ADDRESS]) stay bracketed: fill them once in your Gmail signature.

## Files

| File | What it is |
| --- | --- |
| `fill.py` | The engine: field rules and fallbacks (03), slot sentences (04), checks, HTML, drafts |
| `shoot.js` | HTML to 390 px PNG with Playwright |
| `../examples/SAMPLE-rows.csv` | Four SAMPLE rows: an office and a brand with every field filled, and an office and a brand with every fallback triggered |
| `../examples/SAMPLE-states.json` | SAMPLE tracker states layered over `../04-slot-state.csv` |
| `../examples/SAMPLE-examples.json` | The 20 examples: two per sequence |

When you change a slot sentence, change it in `fill.py` (function `slot_sentence`) and in `04-slot-table.csv`; the lint fails until both agree.
