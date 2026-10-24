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
