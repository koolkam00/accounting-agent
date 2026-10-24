# SAMPLE exports loaded into a copy of the financial model

SAMPLE DATA. Illustrative placeholders, not results. Made by `python3 tests/test_h_import.py` on 2026-10-24.
H's workbook (`financial-model/Desk Drop financial model v1.xlsx`) is copied, never written: SHA-256 before e820db33e70b9175.
The SAMPLE drop IDs are mapped to the model's Schedule keys in the copy only (SAMPLE-DRP-001 to DRP-001).

## zero (as of 2027-02-12)

Pasted from `exports/SAMPLE-zero`: campaign_actuals.csv 2 rows, drop_costs.csv 1 rows, hours_log.csv 37 rows, pipeline_paid_events.csv 2 rows.

H's own checks after loading: 0 formula errors; 13 paste checks, 0 failing.
All H checks failing after loading: none.

| Drop_Actuals | drop | before | after | from the CSVs | match |
| --- | --- | --- | --- | --- | --- |
| Actuals in | DRP-001 | N | Y |  |  |
| Revenue | DRP-001 | 0 | 1080 | 1080 | yes |
| Card processing | DRP-001 | 0 | 0 | 0 | yes |
| Kit + transport + other direct | DRP-001 | 0 | 152 | 152 | yes |
| Overhead allocations (planned) | DRP-001 | 0 | 80 |  |  |
| Founder hours | DRP-001 | 0 | 57 | 57 | yes |
| Contribution (H: after allocations) | DRP-001 |  | 848 |  |  |
| Contribution per founder hour (H) | DRP-001 |  | 14.8772 |  |  |
| Placed within 1 bd, share | DRP-001 |  | 0.896 | 0.896 | yes |
| Campaigns under 5 per office | DRP-001 |  | 1 | 1 | yes |
| Reports late or missing | DRP-001 |  | 0 | 0 | yes |
| Brands that would buy again | DRP-001 |  | 1 | 1 | yes |
| Tracker dashboard contribution (before overhead) | DRP-001 | | 928 | 16.28 per founder hour | H lower by its planned allocation 80 |

| Dashboard | before | after |
| --- | --- | --- |
| Next scheduled drop | DRP-003 | DRP-003 |
| Standard runs to Gate 3: contribution per founder hour (plan / actual) | actual: not yet (0 of 2 standard runs with actuals in); target $50 | actual: not yet (0 of 2 standard runs with actuals in); target $50 |
| Lowest point of cumulative cash | -4476 | -4552 |
| Six months all-in per founder hour, roadmap drops | 33.7621 | 33.4273 |
| Cumulative cash at week 26, roadmap drops | 2839 | 2763 |
| Brand renewal rate |  | 0.5 |
| The rule says | not yet: no renewal answers | not yet: renewal clears the scale bar; Gate 3 is still open |

| Gate row | live value before | after | status before | after |
| --- | --- | --- | --- | --- |
| Gate 1 Offices signed | 0 | 0 | miss | miss |
| Gate 1 Combined Tuesday headcount of signed offices | 0 | 0 | miss | miss |
| Gate 1 Brands paid in full | 0 | 2 | miss | pass |
| Gate 2 Units placed within one business day (share of delivered) |  | 0.896 | miss | pass |
| Gate 2 Brand campaigns under 5 survey responses per office (must be 0) |  | 1 | miss | miss |
| Gate 2 Reports late (after T+7) or missing (must be 0) |  | 0 | miss | pass |
| Gate 2 Brands that would buy again |  | 1 | miss | pass |
| Gate 3 Renewals at $1,500 or more, signed by the review date | 0 | 0 | not yet | not yet |
| Gate 3 Contribution per founder hour, standard runs |  |  | not yet: 2 standard run(s) without actuals | not yet: 2 standard run(s) without actuals |
| Gate 3 Standard runs dated by the review date with actuals in (the rate above uses only these; threshold = all of them) | 0 | 0 | 2 without actuals | 2 without actuals |
| Gate 0 overall | | | miss | miss |
| Gate 1 overall | | | miss | miss |
| Gate 2 overall | | | miss | miss |
| Gate 3 overall | | | not yet | not yet |

Negative control (SAMPLE- drop IDs pasted as they are): H flags 2 campaign rows, 1 cost rows and 27 hour rows as not on Schedule, and no drop moves (none moved).

## standard (as of 2027-03-12)

Pasted from `exports/SAMPLE-standard`: campaign_actuals.csv 5 rows, drop_costs.csv 2 rows, hours_log.csv 68 rows, pipeline_paid_events.csv 8 rows.

H's own checks after loading: 0 formula errors; 13 paste checks, 0 failing.
All H checks failing after loading: none.

| Drop_Actuals | drop | before | after | from the CSVs | match |
| --- | --- | --- | --- | --- | --- |
| Actuals in | DRP-001 | N | Y |  |  |
| Revenue | DRP-001 | 0 | 1080 | 1080 | yes |
| Card processing | DRP-001 | 0 | 0 | 0 | yes |
| Kit + transport + other direct | DRP-001 | 0 | 152 | 152 | yes |
| Overhead allocations (planned) | DRP-001 | 0 | 80 |  |  |
| Founder hours | DRP-001 | 0 | 57 | 57 | yes |
| Contribution (H: after allocations) | DRP-001 |  | 848 |  |  |
| Contribution per founder hour (H) | DRP-001 |  | 14.8772 |  |  |
| Placed within 1 bd, share | DRP-001 |  | 0.896 | 0.896 | yes |
| Campaigns under 5 per office | DRP-001 |  | 1 | 1 | yes |
| Reports late or missing | DRP-001 |  | 0 | 0 | yes |
| Brands that would buy again | DRP-001 |  | 1 | 1 | yes |
| Tracker dashboard contribution (before overhead) | DRP-001 | | 928 | 16.28 per founder hour | H lower by its planned allocation 80 |
| Actuals in | DRP-002 | N | Y |  |  |
| Revenue | DRP-002 | 0 | 4350 | 4350 | yes |
| Card processing | DRP-002 | 0 | 0 | 0 | yes |
| Kit + transport + other direct | DRP-002 | 0 | 590 | 590 | yes |
| Overhead allocations (planned) | DRP-002 | 0 | 155 |  |  |
| Founder hours | DRP-002 | 0 | 52 | 52 | yes |
| Contribution (H: after allocations) | DRP-002 |  | 3605 |  |  |
| Contribution per founder hour (H) | DRP-002 |  | 69.3269 |  |  |
| Placed within 1 bd, share | DRP-002 |  | 1 | 1 | yes |
| Campaigns under 5 per office | DRP-002 |  | 1 | 1 | yes |
| Reports late or missing | DRP-002 |  | 0 | 0 | yes |
| Brands that would buy again | DRP-002 |  | 2 | 2 | yes |
| Tracker dashboard contribution (before overhead) | DRP-002 | | 3760 | 72.31 per founder hour | H lower by its planned allocation 155 |

| Dashboard | before | after |
| --- | --- | --- |
| Next scheduled drop | DRP-004 | DRP-004 |
| Standard runs to Gate 3: contribution per founder hour (plan / actual) | actual: not yet (0 of 2 standard runs with actuals in); target $50 | actual: $69.3 (1 of 2 standard runs with actuals in); target $50 |
| Lowest point of cumulative cash | -4476 | -4000 |
| Six months all-in per founder hour, roadmap drops | 33.7621 | 34.7311 |
| Cumulative cash at week 26, roadmap drops | 2839 | 2538 |
| Brand renewal rate |  | 0.6667 |
| The rule says | not yet: no renewal answers | not yet: renewal clears the scale bar; Gate 3 is still open |

| Gate row | live value before | after | status before | after |
| --- | --- | --- | --- | --- |
| Gate 1 Offices signed | 0 | 0 | miss | miss |
| Gate 1 Combined Tuesday headcount of signed offices | 0 | 0 | miss | miss |
| Gate 1 Brands paid in full | 0 | 2 | miss | pass |
| Gate 2 Units placed within one business day (share of delivered) |  | 0.896 | miss | pass |
| Gate 2 Brand campaigns under 5 survey responses per office (must be 0) |  | 1 | miss | miss |
| Gate 2 Reports late (after T+7) or missing (must be 0) |  | 0 | miss | pass |
| Gate 2 Brands that would buy again |  | 1 | miss | pass |
| Gate 3 Renewals at $1,500 or more, signed by the review date | 0 | 0 | not yet | not yet |
| Gate 3 Contribution per founder hour, standard runs |  | 69.3269 | not yet: 2 standard run(s) without actuals | not yet: 1 standard run(s) without actuals |
| Gate 3 Standard runs dated by the review date with actuals in (the rate above uses only these; threshold = all of them) | 0 | 1 | 2 without actuals | 1 without actuals |
| Gate 0 overall | | | miss | miss |
| Gate 1 overall | | | miss | miss |
| Gate 2 overall | | | miss | miss |
| Gate 3 overall | | | not yet | not yet |

Negative control (SAMPLE- drop IDs pasted as they are): H flags 5 campaign rows, 2 cost rows and 58 hour rows as not on Schedule, and no drop moves (none moved).

H's workbook SHA-256 after: e820db33e70b9175 (unchanged).

Result: pass
