**Draft for attorney review. Not legal advice.**

# Legal and admin pack: README

Version 0.6 · 2026-10-24 · Workstream G

Start with `00-index.md`: it says what each document is for and when you use it, in the plan's order of operations. This README says how to edit the pack and keep it consistent. `REPORT.md` is the report back (assumptions, changelog, questions). `HANDOFF.md` is what other workstreams take from here.

Nothing in this folder has been filed, sent, signed, bound, applied for or paid. Every step that needs your login, signature, card or phone is marked **[FOUNDER]** in its file and listed below.

## The files, in the order you use them

| # | File | What it is for | How to edit it |
| --- | --- | --- | --- |
| 00 | `00-index.md` | What each document is for and when it is used | Update a row when a file's timing changes |
| 01 | `01-name-check-log.md` | Trademark, state entity and domain searches; the name gate for print (D) and launch (C) | To check a new name: change the `BRAND_NAME` line, run `python3 desk-drop-legal-pack/_work/namecheck/scripts/name_check.py "<name>"` from `desk-drop/`, paste its table in as new rows with the date, keep the old rows as history. Keep `name-check-log.md` in step |
| 02 | `02-email-footer-and-checklist.md` | Footer and three-line CAN-SPAM checklist for every commercial email | Fill [POSTAL ADDRESS] once you choose it. The trading name is the one `BRAND_NAME` line |
| 03 | `03-office-participation-agreement.md` | One-page office agreement, no penalties | Send only after the attorney clears it (file 08, by Wed 2026-11-18). Fill the top table from the office's intake row before sending (`company` goes in both [OFFICE LEGAL NAME] slots). Keep it to one Letter page: re-render and look after any change |
| 04 | `04-formation-checklist.md` | Forming the LLC; county cost comparison; 120-day deadline | On the filing day, fill "Your real dates" in section 5 |
| 05 | `05-llc-operating-agreement.md` | Single-member operating agreement with Schedules A and B | Fill sections 1.3, 2, 12.1 and the schedules; list every pre-formation office agreement in Schedule B, item 6 |
| 06 | `06-gl-quote-request-script.md` | Honest description, 20 questions and a comparison table for three GL quotes | Fill the bracketed facts in section 1 (storage place, car) before the first call; never edit the description to get a cheaper class |
| 07 | `07-food-safety-call-script-and-log.md` | The state call: exact question, facts, follow-ups, answer log | Fill the facts sheet before you call; write the answer word for word in the log during the call |
| 08 | `08-attorney-hour-agenda.md` | The attorney hour: ranked questions, send-ahead note, answer log | Add a question only with the file and section it concerns |
| 09 | `09-accountant-question-list.md` | The accountant hour: ranked questions with facts checked, answer log, tax calendar | Fill the answer log and calendar during the meeting |
| 10 | `10-brand-campaign-agreement.md` | Brand agreement: Part 1 campaign sheet, Part 2 fixed terms | Fill Part 1 per campaign from the paid-brands row. Change Part 2 only after the attorney hour, and raise the version |
| 11 | `11-coi-request-brand-product-liability.md` | Certificate request to a brand, broker block, reminder, check | Fill the brackets per brand; the handling paragraph must stay word for word the same as files 06, 07 and 10 |
| 12 | `12-coi-request-own-carrier-building.md` | Building requirements, request to our carrier, check, no-employees statement | Copy the building's names exactly from its sheet |
| 13 | `13-survey-privacy-notice.md` | Survey notice (short and full), the optional email question, form settings | Fill per campaign; if any Part D setting changes, re-read the notice so it stays true |
| | `name-check-log.md` | Pointer to 01 at the CONTRACTS 6.7 path, with the gate status | Change the status line whenever 01's gate changes |
| | `figures.csv` | Every cost figure for the financial model, with status, source and timing | Replace a `needs quote` row with the quote, set `status` to `verified YYYY-MM-DD`, and put the quote's source in `source_url` or `notes` |
| | `rendered/` | PDF and DOCX of 03, 05, 10 and 13 | Never by hand: run the renderer below |
| | `_work/` | Research scratch, scripts, drafting and merge notes | Kept for the record; not sent to anyone |

## Conventions that keep the pack consistent

1. **One name, set once per file.** The legal name is the slot `[COMPANY NAME: Desk Drop LLC]` in each document's definition line; everywhere else the text says "the Company", "we" or "our company", or `[COMPANY NAME]` where you type the name into an email or form. The trading name, used only in files 01 and 02 and the pointer, is the line `BRAND_NAME = Desk Drop`. A rename is one edit per file: search the folder for the working name and change each hit. The check script below fails if any file has the name more than once.
2. **The review heading** "Draft for attorney review. Not legal advice." opens every file and every signable block. Remove it from a document only after an attorney has cleared that document, and record the date and the attorney's name in its changelog.
3. **Placeholders** keep the shared form: [FOUNDER NAME], [PHONE], [EMAIL], [POSTAL ADDRESS], [WEBSITE], [DOMAIN]. Dates in copy are slots with a derived value, such as [DROP DATE: Tue 2027-01-12]. Every bracket is replaced before anything is sent.
4. **Dates** come from the canonical calendar (CONTRACTS section 3) and are "derived, founder to confirm". Replace them with real dates as they happen.
5. **Sources.** Every researched fact names its source and the date it was opened (2026-10-23 unless stated). Anything that could not be opened says "unverified, founder to confirm". Plan figures say "plan".
6. **Dollar signs** are written `\$` in the .md files so GitHub and pandoc do not read "\$600 ... \$1,500" as a formula.
7. **Versions.** Each file shows a line such as "Version 0.6 · 2026-10-24" (files changed in review round 1 are 0.6; unchanged files stay 0.5). When you change a document's substance, raise its version (in the agreements, also in the first line of the agreement block; the check fails if the two differ) and add a changelog line.
8. **Ladder words.** Delivered, placed, depleted, responded, scanned, purchased and incremental stay separate. Nothing promises sales, scans or responses.

## Checks and rendering

From `desk-drop/`:

```text
python3 desk-drop-legal-pack/_work/check_pack.py     # consistency checks; expect "0 findings"
python3 desk-drop-legal-pack/_work/render_pack.py    # rebuilds rendered/ and _work/png/
```

The check covers: that `README.md`, `REPORT.md` and `HANDOFF.md` exist (CONTRACTS section 1); the review heading at the top and in each block; the version line, and that each agreement block's version matches its file; the name once per file and in the right form; heading numbers; changelogs; placeholder case; ladder words; escaped dollar signs; every file reference resolves; every weekday matches its date; the shared storage sentence in 06, 07, 10 and 11; and the `figures.csv` columns and statuses. It also prints, as warnings, any file in another workstream's folder that cites a `desk-drop-legal-pack/NN-….md` name that no longer exists (they are that workstream's to fix; the old-to-new map is in `HANDOFF.md`). The renderer needs pandoc, node with Playwright, and poppler (`pdfinfo`, `pdftotext`, `pdftoppm`); it stops if any dollar amount goes missing between the .md and the PDF. Look at the page images in `_work/png/` after every render; the office page must stay on one page.

## Steps that need you [FOUNDER]

| Step | File | Needs | Spend (stop for your written yes) |
| --- | --- | --- | --- |
| Department of State name search (row 12) | 01 | A normal browser | None |
| Buy the domain; set up the email address | 01, 02 | Registrar and email logins | Domain and email (plan: about \$100 for six months); premium prices possible |
| Choose and set up the mailing address | 02, 04 | A PO box or mailbox account | Needs quote (`figures.csv`) |
| E-signature account | 03, 10 | Free-tier login (plan: Dropbox Sign or PandaDoc) | \$0 on the free tier |
| File the Articles; EIN; bank account | 04 | Department of State login and card; IRS online (your own taxpayer number); a visit or login at the bank | \$200 filing; \$0 EIN; bank fees unknown |
| Order publication; file the Certificate of Publication | 04 | Publication service or newspapers; Department of State | \$345 to \$1,745 working figure; \$50 certificate |
| Three GL quotes; bind one | 06 | Phone, carrier sites, a broker | Premium (plan: \$500 to \$1,500 a year) |
| Call the state food safety office | 07 | Your phone | None (a license, if needed, is \$400 for two years) |
| Book the attorney and accountant hours | 08, 09 | Email or phone | Plan: \$300 to \$500 and \$200 to \$400 |
| Send brand certificate requests; check certificates | 11 | Your email | None |
| Request building certificates from our carrier | 12 | Carrier portal or broker | Any endorsement cost: stop and decide |
| Build the survey form to Part D's settings | 13 | Form-tool login (operations workstream) | \$0 |
