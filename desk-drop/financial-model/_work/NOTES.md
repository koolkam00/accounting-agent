# Working notes (workstream H). Scratch, kept per CONTRACTS section 1.

## Plan readings verified by hand (2026-10-23)
- (a) kit $8 per OFFICE per drop. 3-brand courier: 80+300+75+30+50+135 = 670. Per brand would be 240 -> 830.
- (b) C0: 40+120+0+30+50+36 = 276 (plan 280). Contribution 924 (plan 920), 924/57 = 16.2.
- (c) direct ship 3 brands: 80+0+75+30+50+135 = 370. Keeps storage 75, transport 0.
- (d) $1,000 x3: no processing 535 -> 2465/52 = 47.4; with 3% 625 -> 2375/52 = 45.7.
- (e) steady state 2 x 670 = 1340; 9000-1340 = 7660; 104 h.
- Capital low 3360, high 6510 reproduce from the table.
- Overhead/month: software 60 + insurance 100 + storage 150 + phone 0 = 310 (inside plan's 200-350). Home storage: 160.

## Calendar (python check)
- Founding payment lead: 20 business days before C0 (2027-01-12) = 2026-12-11 = Gate 1.
- C0 T-10 = 2026-12-28, T-3 = 2027-01-07, T+7 = 2027-01-22 (Gate 2), T+10 = 2027-01-27.
- S1 2027-02-09: T-10 2027-01-26, T+1 2027-02-10. S2 2027-02-23: T-10 2027-02-08.
- Derived D4 2027-03-23 and D5 2027-04-06 (post Gate 3, two drops in the decision window).

## Hours decomposition (reproduces plan table exactly)
- brand_sales: 10 per first (founding) brand, 6 per standard win (=5 conv x 0.75 h + 2.25 paperwork at 20% close), 2 per renewal.
- office: 4 per new office, 1 per existing office.
- receiving: base by model (founder 2.0, courier 2.5, direct 0.5) + 0.5 per brand.
- drop day per office: founder 1.0, courier 0.8, direct 0.3.
- checks per office: founder 0.6, courier 0.4, direct 0.4.
- reporting 2 per brand; admin 2 per drop.

## Status log
- legal-pack figures.csv: not present at start (2026-10-23). Re-check before finishing.

## Research (opened 2026-10-23)
- Google Sheets function list https://support.google.com/docs/table/25273 : SUM, SUMIFS, COUNTIFS, COUNTIF, SUMPRODUCT, INDEX, MATCH, IF, IFERROR, AND, OR, NOT, MIN, MAX, ROUND, ROUNDUP, INT, ABS, DATE, YEAR, MONTH, DAY, WEEKDAY, WORKDAY, NETWORKDAYS, EOMONTH, EDATE, TEXT, ISNUMBER, ISBLANK, ISERROR, COUNTA, COUNT, AVERAGE, MEDIAN, VALUE, LEFT, LEN, TRIM, CHOOSE, N, TODAY, ISTEXT, UPPER, SUBSTITUTE, MAXIFS, MINIFS all listed.
- Toggl Detailed report article https://support.toggl.com/en-us/article/detailed-report-k9bzy2/ (updated 2026-08-05): "CSV and Excel exports are a paid plan feature."
- Toggl payment plans https://support.toggl.com/en-us/article/payment-plans-at-toggl-track-1ghiwye/ (updated 2026-07-24): Starter starts at $9 per license per month.
- Toggl CSV column names: NOT documented on pages opened -> unverified, founder to confirm. Import tab maps headers by name.
- WebSearch budget exhausted for this run; only WebFetch/curl used.
- LibreOffice 24.2 headless convert recalculates openpyxl formulas (tested).

## Round 1 result (2026-10-24)
- Audit 0 literals, 0 non-Sheets functions; 28/28 checks; low point -4,476 wk13; commit 5,476; gap 1,034.
- legal pack figures.csv appeared 2026-10-24 (index v0.4). Pull: articles 200 verified; certificate 50 verified (by day 100);
  publication 1,745 working (200-2,000) needs quote, order within 10 bd of filing; GL 1,200/yr (500-1,500) needs quote, bind latest 2026-12-21;
  license 400 fee verified, requirement unknown; attorney 400 (300-500), accountant 300 (200-400) plan estimates; trademark 350 verified but
  "not in the first six months"; IT-204-LL $25 verified, first possibly 2027-03-15; HNOA and additional-insured add-ons unknown (needs quote).

## Round 1 critique -> round 2 fixes
1 legal figures; 2 blank cash dates when amount 0; 3 month labels; 4 Capital reserve not cash; 5 recon wording + overhead range;
6 Gate 3 model renewals signed by Gate 3; 7 office-fatigue flag (12 offices, two drops in 14 days); 8 scenario-driven cells styled;
9 Scenarios defaults/changed; 10 schedule changed flags; 11 dashboard: unabsorbed overhead + all-in per hour incl. discovery;
12 README: taxes, refunds not modeled; 13 tests; 14 visual; 15 deliverable files.

## Round 2-3 (2026-10-24)
- Google Sheets list re-opened 2026-10-24: DATEVALUE, TIMEVALUE, FIND, COUNTA, SUMIFS, EDATE, EOMONTH, MEDIAN, ROUNDUP, WORKDAY all listed. All 37 functions used are on the list.
- Final figures: low -3,871 (week 12, Mon 2027-01-11); commit 4,871; gap to 6,510 = 1,639; week-26 cash 12,014; unabsorbed overhead 1,310;
  all-in 50.3/h (38.9 after startup); standard runs 61.3/h; steady 7,660/mo at 81.1/h (plan reading 73.65); startup 3,520; b* 1.81; price* 107.73.
- Scenarios: A steady 9,406/mo 99.6/h; B 7,660 + 500 office-paid (cost unknown) 73.7/h; C week-26 cash 7,729; D week-26 cash 3,444, steady -310/mo.
- Goal 20 offices -> run 2 = 82 h, 46.7/h; Gate 3 combined 51.4/h.
- Tests 54/54; audit clean; 28/28 checks.

## Review round 1 response (2026-10-24)
- Reviewer: _review/round-1.md (2 blockers, 5 majors, 11 minors). All fixed except the decision-date move itself, which is a founder question (CONTRACTS fixes 2027-04-09 for every workstream).
- Publication default = plan high end $2,000 (low $250). Low point -4,126 (wk 12), commit 5,126, gap 1,384, one-brand campaigns to recover 5 (reviewer's numbers reproduce).
- Steady_State row 8 = standard drop on Inputs; break-even reads it. Price 180 -> Dashboard 'A standard drop at that price' 73.65 -> 90.44.
- Paste buffers: AC helpers AL, DC helper U, Hours_Log totals Q, Pipeline helpers T, Toggl paste A:AD. Header checks via Lists rows 34-37.
- Six months all-in, expensed basis (insurance 5 cover months in window = $500; $700 prepaid): roadmap only 33.76/h, with DW drops 52.54/h.
  Cash basis would be 30.68 and 50.27 (reviewer's figures). Week-26 cash: roadmap 3,189, all 11,759.
- Gate 3 rate with a fatigue-free roster: 7,660 / (125 + 8 x 3) = 51.41.
- Decision rule: Stop only after both tests fail; 'not yet: the switch test needs N more extra drop(s)' while renewal < 30% and < 2 extra drops have actuals.
- DRP-005 T+10 = Tue 2027-04-20 > decision 2027-04-09 -> Dashboard warning; REPORT question 1 (default: move review to 2027-04-20).
- Founding renewals stay 0 by default (assumption 18): DRP-002 T-10 = 2027-01-26 is 2 bd after the C0 report; DRP-003 founding payment at T-20 = 2027-01-25, before the C0 debrief 2027-01-27.
- Arithmetic check: 10 business days after Fri 2026-11-20 skipping Thanksgiving = Mon 2026-12-07 (my first test expectation of 12-04 was wrong; the model was right).
- Audit: 16,789 formulas, 0 literals, 38 functions (NOT added; on Google's list). 34 checks. 102 behaviour tests.

## Review round 2 response (2026-10-24), in progress
- Reviewer: _review/round-2.md (0 blockers, 3 majors, 6 minors). Plan: fix all nine.
- R2-01 INDEX on one-row ranges -> explicit INDEX(range,1,col) everywhere (Scenarios H/R, Cash_Flow low week/date and bank variance, Toggl_Import AF:AI); audit rule added.
- R2-02 Gate 3 coverage row (standard runs by Gate 3 with actuals: n of m); per-hour status 'not yet: k standard run(s) without actuals' until n = m; same coverage on the all-drops rate and pointer.
- R2-03 all-in denominators: MAX(planned discovery hours, logged hours not tied to a drop inside the 26 weeks).
- R2-04 Gate 1 'paid in full': cumulative paid per brand >= founding package price.
- R2-05 probes: notes = after_1500 marks the after-anchor answer; medians use one before-anchor answer per org.
- R2-06 storage starts with the first standard drop that runs.
- R2-07 legal pack re-read (figures.csv modified 01:52): mailbox and registered-agent lines; filing WORKDAY(Gate 0, 4) = Thu 2026-11-19; attorney by Wed 11-18; accountant by Fri 11-20; GL status 'plan estimate'.
- R2-08 Dashboard block: cash spent before each review date (stop there) and cumulative cash at the end of each review week.
- R2-09 README price text live; AA:AK buffer; break-even label + standard drops row; Cash_Ledger banner.
- Result (2026-10-24): all nine fixed. Audit 19,848 formulas, 0 literals, 0 one-row INDEX without a row (6,027 in the 3-argument form). 34/34 checks. 125/125 tests.
- Defaults unchanged: low -4,126 wk 12, commit 5,126, gap 1,384, Gate 3 plan 61.3, steady 7,660, all-in 33.8 / 52.5.
- Stop points: Gate 0 -160, Gate 1 -3,120 (receipts 1,200 that day; week end -3,856), Gate 2 -5,326, Gate 3 -6,844, decision -7,441 vs 19,200 received.
- Google INDEX page opened 2026-10-24: syntax INDEX(reference, [row], [column]); row 'OPTIONAL - 0 by default'; nothing on one-dimensional references.

## Review round 3 response (2026-10-24)
- Reviewer: _review/round-3.md (0 blockers, 4 majors, 6 minors and one polish item). Fixed all eleven; one remedy wording changed (R3-01: a format change does not convert stored text, so the README gives DATEVALUE/VALUE plus paste values).
- R3-01 text checks: COUNTA-COUNT per date/number range (AC C, G:U, X:Z; DC B, D:H; HL A, E; PL A, F). Dashboard G5 names data failures ("N data check(s) failing ...") and is red; green text is now "all integrity and data checks pass".
- R3-02 legal pack figures.csv re-read after its 02:33 update (trademark timing now inside six months; new fda_food_facility_registration $0). Trademark Include = Y at Gate 2: low -4,476 wk 13 (Mon 2027-01-18), commit 5,476, gap 1,034, week-26 cash 11,409 (roadmap only 2,839). Include = N restores -4,126 wk 12.
- Timing choice: Gate 2 day (Fri 2027-01-22). Legal pack says "from about Mon 2027-01-25"; in week 14 the DRP-002 deposits (2027-01-26) would net it away from the weekly low; Gate 2 is the cautious reading.
- R3-03 Drop_PnL BJ next_date; Dashboard next drop = MATCH(MIN(BJ)); "Drop dates out of order" now an Info row (E = "info"; recalc.py treats it as non-failing).
- R3-04 Scenarios D:F rows 11, 15, 16 and D:G row 21 = $C (blue). Test: std brands 2 + scenario A -> K10 = 2, steady 2 brands.
- R3-05 stop points: Gate 1 net -3,120 (refund 1,200), Gate 2 net -4,126, Gate 3 paid -7,194, received 12,450, refunds 2,250, net +3,007; decision 11,409.
- R3-06 Inputs unpriced count = 5 (mailbox, HNOA, endorsements, kit mail, extra cards).
- R3-07 AC helpers AQ (brand's first Y/N), AR (brand's first Y); rate = SUM(AR)/SUM(AQ).
- R3-08 scenario A new offices 4 per DW drop (roster 12 -> 20), +12 office hours each.
- R3-09 Schedule check: week 1 changed while gates 0, 1, 3, decision and DRP-001 date are unchanged.
- R3-10 HANDOFF cites the brief for E's file; REPORT lists the conflict with CONTRACTS s6.
- R3-11 Drop_Actuals banner; README row 7; import route = File, Import, Replace spreadsheet (support.google.com/docs/answer/40608 opened 2026-10-24: six import options listed; no text-conversion option documented); C13/C14 "n/a".
- Google DATEVALUE page (support.google.com/docs/answer/3093039, opened 2026-10-24): "Converts a provided date string in a known format to a date value"; understood formats = those autoconverted when typed.
- WebSearch unavailable this round (turn budget used up); only WebFetch.
- Result: audit 20,306 formulas, 0 literals, 38 functions all on Google's list, 0 one-row INDEX without a row. 38/38 checks (+1 info). 151/151 tests.
