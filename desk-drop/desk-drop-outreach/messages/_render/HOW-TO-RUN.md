# How to run the fill script

`fill.py` fills the message templates with a Clay row, checks every message, renders the phone-width examples, and makes paste-ready drafts. It never sends anything and makes no network calls. Python 3, standard library only; the PNGs need node with Playwright.

Run everything from `desk-drop/desk-drop-outreach/messages/`.

## 1. Check every message (after any edit to a message file)

```bash
python3 _render/fill.py lint
```

Fills all 68 message blocks with the SAMPLE rows in a state that unlocks them (discovery copy with both selling switches off) and prints every finding. It fails (exit 1) on: more than one question (one ask per message; a numbered questionnaire counts as one), an exclamation mark, a banned word (guarantee outside "no guarantees", free trial outside "no free trial", lift, ROI, conversions, acquisition, "we work with", "spots left", "limited time", "best", "just checking in" and others), a touch 1 over 125 words or a follow-up over 75, a LinkedIn note over 200 characters or message over 600, "free" or "Re:" in a cold touch 1 subject, a link or attachment in touch 1, a follow-up not sent as a reply, a wrong weekday or an illegal drop date in any date slot, a missing footer, a message the tracker state does not unlock (`domain_ready`, `office_selling_on`, `brand_selling_on`, `attorney_cleared`, `llc_formed`, `name_decided`, `startup_cpg_joined`, the founding-price brand emails once `founding_taken = 3`, and the brand agreement and invoice until five offices have signed and the brand row has `office_approvals_complete = Y`), a cold touch 1 dated before Mon 2026-11-09, the working name printed while `name_decided = N`, a drop date written as fixed ("from [DROP DATE", "your [DROP DATE") while `drop_date_confirmed = N`, a campaign zero offer to a brand after the last-offer date (a selling touch 1 or proposal after Mon 2026-11-30; a step 2 or holding note after Thu 2026-12-03, the last verbal yes), any date slot that has passed on the send date, an agreement date that is not the one computed from the send date, a holding note (11 step 5) when every gate for the agreement is already met, discovery copy that says nothing is for sale once that side's selling switch is Y (05 and 06 touch 1, the two discovery LinkedIn openers, 08 1a, 1c and 2b, 09 D's discovery reply, and step 0 of 10 and 11; review round 3), a slot state the folder's own gates make impossible (below), and any computed slot sentence whose wording is not in `04-slot-table.csv` or a message file. It warns when a touch 1 prints nothing about the person or company. Two self-tests run with it: steps 1 and 5 of file 11 are filled in all 384 combinations of the agreement gates and four send dates, and must never promise a date while the offices are still signing or approving the brand, never print a past date and never say the registration is pending after `llc_formed = Y`; and the office and brand shares of every day in `sending/warmup-schedule.csv` must add up to the day's number (review round 2). Review round 3 added two more and a state check: every discovery-only block is filled under each combination of the two selling switches and must be refused exactly when its side's switch is Y; and every state (the live `04-slot-state.csv`, the lint state and each example step on its send date) must be possible: offices signed no more than offices at yes, an office signed only once `attorney_cleared` and `name_decided` are Y (with `tuesday_headcount` filled), a founding place or a paid brand only once five offices have signed and the company is formed, cleared and named, `brand_selling_on` only with two offices at yes, `drop_date_confirmed` only with two brands paid, and, for the examples, nothing signed before Thu 2026-11-19 and no name or attorney decision before Wed 2026-11-18 (the default calendar).

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
  --date 2026-11-09 \
  --out drafts/2026-11-09
```

One `.txt` per row (To, Subject, body, signature), ready to paste into Gmail. `--message` is a block id from the message files (`office-discovery-1`, `brand-selling-1`, `li-office-discovery-1` ...). The variant (A or B) comes from the row's `sequence` column, or `--variant`. The state is `04-slot-state.csv` unless `--state` names another file. It refuses a date nothing is sent on (a weekend, a federal holiday, Fri 2026-11-27, 18 December to 4 January) and names the next sending day. For a cold email touch 1 it writes no more drafts than the day allows in `sending/warmup-schedule.csv`: offices get half the day's number rounded up and brands the rest, so the two runs together never pass the day's number (`--side-share N` sets this side's share, `--over-cap` overrides, not recommended). When a touch 1 row has a fresh `why_now` (120 days or less, with its URL) but no `why_now_hook` written yet, it says so in its output and on the draft's first line ("# NOTE (delete this line before sending)"), so the hook is never dropped silently. The same NOTE line lists every bracket still yours to fill other than your own details (for example the broker block's [BRAND LEGAL NAME], [BRAND ADDRESS] and [PRODUCT NAME AND SKU] in 11 step 8), and, once `llc_formed = Y`, asks you to check the company name, which then prints bare ("... LLC"), letter for letter against the filed Articles (review round 3). It refuses to run at all on a slot state the gates make impossible (section 1), and it skips a touch 2 or 3 whose row is on the other kind of sequence (a discovery follow-up for a row on `brand-selling-A`, or the reverse): a thread ends the way it began. A touch 2 or 3 gets the subject "Re: " plus the touch 1 subject rebuilt from the row's `sequence` variant. Rows are skipped, with the reason printed, when `do_not_contact` is not N, `opt_out_date` is filled, `hold_before_outreach` = Y in A's table (its `hold_reason` is printed), the status is wrong for the touch, the row is for the other side, an office row's `lease_status` is `signed-not-occupied` or `moving-out`, the row has no address for the message's channel, a cold email row is not `email_status = verified`, a referral draft would name a referrer who has not agreed, the message is not unlocked, or nothing personal would print. Any cell that reads `unknown` or "unverified, founder to confirm" is treated as blank, so its fallback prints instead. Drafts go in `drafts/`, which you can delete at any time; do not commit drafts that hold real contacts.

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

## Changelog

- Review round 1 (2026-10-24): the draft maker refuses no-send days, caps cold first touches at the warm-up schedule, rebuilds the touch 1 subject for follow-ups, and skips rows with an opt-out date or A's outreach hold; the lint gained the new gates (first cold day, name, planned dates, office approvals).
- Review round 2 (2026-10-24): the lint fails a past date, an agreement date not computed from the send date, a holding note once every gate is met, and a January offer after Mon 2026-11-30 (a yes after Thu 2026-12-03); two self-tests; the side shares add up to the day's number; the fresh `why_now` note; the one-pagers and proposal count as ready only once they may name the business.
- Review round 3 (2026-10-24): discovery copy refused once its side sells (the lint self-test and the draft maker); the asks follow the attachment state (`[OUTLINE ASK]`, `[OUTLINE ASK SHORT]`, `[PROPOSAL ASK]`, `[PROPOSAL ASK REPLY]`, `[INFO PAGE LINE]`); brand step 0 says February after Mon 2026-11-30 (`[STEP 0 CAMPAIGN LINE]`); the state check on the live state, the lint state and every example step; the bare company name and the NOTE line of brackets left to fill; follow-ups matched to the row's sequence; the follow-up week never named inside 18 December to 4 January; no bytecode written (`sys.dont_write_bytecode`).
