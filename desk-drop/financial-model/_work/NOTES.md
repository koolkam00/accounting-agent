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
