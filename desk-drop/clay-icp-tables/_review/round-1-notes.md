# Round 1 review working notes (reviewer scratch, 2026-10-24)

## Sample (seed 777; 5 top-list, 3 passed non-top, 2 gated per table)
Offices: AO-C-009, AO-C-128, AO-C-105, AO-C-072, AO-C-007, AO-C-121, AO-C-117, AO-C-240, AO-W-002, AO-C-261
Brands: AB-107, AB-210, AB-220, AB-082, AB-025, AB-283, AB-152, AB-282, AB-259, AB-257
Pages saved in _review/fetch/.

Offices: 74 checked, 3 wrong (4.1%) after dropping Spring Health attendance (gated rows were deliberately not enriched): Hub17 website=commercialobserver.com, Hub17 address_source_type operator-site (source is CO),
PitchBook lobby_type with no source, Spring Health attendance unknown (Built In says Hybrid, not specified).
Brands: 70 checked, 1 wrong (1.4%): Unhinged passes health gate though FAQ says L-theanine gives "steady focus ... no crash".

## Confirmed findings so far
- BLOCKER health-claim gate: top-60 brands with explicit S/F or disease claims on own product pages pass:
  Raaka (dv6) "Reishi supports a calm mood, lion's mane keeps you sharp", Focus & Energy line;
  Simply Gum (dv10) "xylitol to fight cavities and protect enamel";
  Ella's Flats (r17) "gut healthy, blood sugar stabilizing, balancing hormones" (no founder review at all);
  Hella (r25) "support healthy digestion by easing gas, bloating, and indigestion.*";
  Elements Truffles (r36) "Immunity Boosting", "Improves athletic performance", ashwagandha "stress relieving";
  Reelie (r47) "helps support gut health", "anti-inflammatory benefits" (no founder review; Maine Crisp failed for same word);
  Goodio (r55) ashwagandha 500 mg, valerian 500 mg, L-tryptophan per bar ("Natural Focus", "Sweet Dreams");
  Unhinged (r57) FAQ "steady focus ... no crash". Evidence _review/claims_scan_products_top60.csv.
- MAJOR onsite estimate ignores leased sf in the same row: 13 top-50 rows central > sf/150; Empathy dv5 5,508 sf vs 67-134;
  1stDibs dv9 13,671 sf vs 94-305; Personetics 7,004 sf vs 113-249.
- MAJOR The Org pages all say "Unverified" on the page itself; table labels contact_status verified-page (7/10 office dv rows).
- MAJOR group block ignores status=do_not_contact when flag left N (scenario: LesserEvil status DNC -> PRETZELIZED enters view #9).
- MAJOR known_to_founder: score +15 but channel never becomes warm-intro (no code path) and score_reason static.
- MAJOR linkedin_company_url 0/308; contact LinkedIn URLs 0/50 top offices; backup contact 18/50; marketing lead 25/60.
- MAJOR office ready pool 26; routine overruns 15 min (LinkedIn lookups + WFM store set).
- Coworking `website` derived from source domain (8 rows: commercialobserver.com, nyrej.com, rebusinessonline.com ...).
- 7 rows lobby_type without lobby_source_url (B-carried).
- LibreOffice 24.2 lacks SORT/FILTER: daily-view tabs never computed by any engine; Sheets compatibility unverified.
- Offices scenario in LibreOffice matched my independent expectation (contacted, status DNC, flag DNC, opt-out date, not_now, group block, founder OK).

## Evidence tables (generated 2026-10-24)

### R1-03 top-50 rows: central estimate above leased_sf/150

| row_id | company | leased sf | sf/150 | low | central | high | band | daily_view_rank |
|---|---|---|---|---|---|---|---|---|
| AO-C-085 | Empathy | 5508 | 36 | 67 | 95 | 134 | 76-150 | 5 |
| AO-C-091 | 1stDibs | 13671 | 91 | 94 | 169 | 305 | 151-250 | 9 |
| AO-C-096 | Inspiren | 8367 | 55 | 50 | 71 | 100 | 40-75 | 10 |
| AO-C-047 | The Vita Coco Company | 22530 | 150 | 113 | 167 | 247 | 151-250 |  |
| AO-C-151 | Carbyne | 5702 | 38 | 49 | 77 | 121 | 76-150 | 12 |
| AO-C-007 | Personetics | 7004 | 46 | 113 | 168 | 249 | 151-250 |  |
| AO-C-127 | accessiBe | 8700 | 58 | 70 | 112 | 180 | 76-150 |  |
| AO-C-030 | Prepared 911 | 7080 | 47 | 26 | 48 | 90 | 40-75 |  |
| AO-C-001 | HUMAN Security | 13809 | 92 | 132 | 186 | 263 | 151-250 | 21 |
| AO-C-055 | Stash | 12322 | 82 | 58 | 122 | 255 | 76-150 |  |
| AO-C-028 | Valon | 13815 | 92 | 142 | 207 | 302 | 151-250 | 24 |
| AO-C-153 | Seedtag | 5909 | 39 | 13 | 78 | 467 | 76-150 |  |
| AO-C-253 | Optiver | 23038 | 153 | 46 | 205 | 912 | 151-250 |  |

### R1-07 coverage

- offices linkedin_company_url known: 0 of 308
- top-50 office contact_linkedin_url filled: 0 of 50; primary named 31; backup named 18
- top-60 brands with a marketing lead named: 25 of 60; backup named 38
- ready_for_outreach: offices 26, brands 183
- top-50 office contact evidence: {'The Org (crowd-edited org chart)': 20, '': 18, "employer's own site": 10, 'search snippet only (not opened)': 1, 'press, event or podcast page': 1}

### R1-10 coworking website values

- AO-W-013 Cure, 345 Park Avenue South: website=https://wewillcure.com; address_source_url=https://wewillcure.com/community/residents; address_source_type=operator-site
- AO-W-007 Industrious 156 5th Ave: website=https://www.industriousoffice.com; address_source_url=https://www.industriousoffice.com/m/new-york-city; address_source_type=operator-site
- AO-W-016 Industrious 386 Park Ave S: website=https://www.industriousoffice.com; address_source_url=https://www.industriousoffice.com/m/new-york-city; address_source_type=operator-site
- AO-W-008 Industrious 902 Broadway: website=https://www.industriousoffice.com; address_source_url=https://www.industriousoffice.com/m/new-york-city; address_source_type=operator-site
- AO-W-014 Industrious NoMad: website=https://www.industriousoffice.com; address_source_url=https://www.industriousoffice.com/m/new-york-city; address_source_type=operator-site
- AO-W-005 Industrious Union Square on Park: website=https://www.industriousoffice.com; address_source_url=https://www.industriousoffice.com/m/new-york-city; address_source_type=operator-site
- AO-W-010 NeueHouse Madison Square: website=https://nyrej.com; address_source_url=https://nyrej.com/print/57154; address_source_type=operator-site
- AO-W-006 The Malin Flatiron: website=https://rebusinessonline.com; address_source_url=https://rebusinessonline.com/the-malin-opens-32700-sf-coworking-space-in-manhattans-flatiron-district/; address_source_type=operator-site
- AO-W-017 The Malin NoMad: website=https://commercialobserver.com; address_source_url=https://commercialobserver.com/2024/11/the-malin-lease-895-broadway; address_source_type=operator-site
- AO-W-001 Civic Hall, Union Square (Zero Irving): website=https://civichall.org; address_source_url=https://civichall.org/contact-us/; address_source_type=operator-site
- AO-W-003 Industrious Union Square on Broadway: website=https://www.industriousoffice.com; address_source_url=https://www.industriousoffice.com/m/new-york-city; address_source_type=operator-site
- AO-W-021 Luminary: website=https://www.weareluminary.com; address_source_url=https://www.weareluminary.com/home; address_source_type=operator-site
- AO-W-023 Nomadworks 1216 Broadway: website=https://nomadworks.com; address_source_url=https://nomadworks.com/; address_source_type=operator-site
- AO-W-022 Sage Workspace: website=https://www.sageworkspace.com; address_source_url=https://www.sageworkspace.com/; address_source_type=operator-site
- AO-W-011 Select Office Suites Flatiron: website=https://www.selectofficesuites.com; address_source_url=https://www.selectofficesuites.com/office-space-for-rent-flatiron-district-new-york-city/; address_source_type=operator-site
- AO-W-015 The Yard: Flatiron South: website=https://theyard.com; address_source_url=https://theyard.com/the-yard-new-york-city/; address_source_type=operator-site
- AO-W-004 WeWork 18 West 18th Street: website=https://www.wework.com; address_source_url=https://www.wework.com/buildings/18-west-18th-street--new-york-city--NY; address_source_type=operator-site
- AO-W-024 WeWork 450 Park Ave S: website=https://www.wework.com; address_source_url=https://www.wework.com/buildings/450-park-ave-s--new-york-city--NY; address_source_type=operator-site
- AO-W-018 WeWork 245 5th Ave: website=https://www.wework.com; address_source_url=https://www.wework.com/buildings/245-5th-ave--new-york-city--NY; address_source_type=operator-site
- AO-W-028 Resident Madison Park (Flatiron): website=https://residentcompanyclub.com; address_source_url=https://residentcompanyclub.com/; address_source_type=operator-site
- AO-W-025 Resident Union Square: website=https://commercialobserver.com; address_source_url=https://commercialobserver.com/2025/12/coworking-resident-company-club-lease-113-university-place/; address_source_type=operator-site
- AO-W-032 Corporate Suites Two Park Avenue: website=https://www.corporatesuites.com; address_source_url=https://www.corporatesuites.com/; address_source_type=operator-site
- AO-W-002 Hub Seventeen, 114 Fifth Avenue: website=https://commercialobserver.com; address_source_url=https://commercialobserver.com/2025/02/capital-one-expansion-114-fifth-avenue/; address_source_type=operator-site
- AO-W-027 Indy by Industrious Gramercy Park: website=https://www.industriousoffice.com; address_source_url=https://www.industriousoffice.com/m/new-york-city; address_source_type=operator-site
- AO-W-029 WeWork 135 Madison Ave: website=https://www.wework.com; address_source_url=https://www.wework.com/buildings/135-madison-ave--new-york-city--NY; address_source_type=operator-site
- AO-W-026 WeWork 33 Irving Pl: website=https://www.wework.com; address_source_url=https://www.wework.com/buildings/33-irving-pl--new-york-city--NY; address_source_type=operator-site
- AO-W-009 Le Parc Coworking Offices: website=https://flatironnomad.nyc; address_source_url=https://flatironnomad.nyc/2024/06/26/meet-le-parc/; address_source_type=operator-site
- AO-W-031 Regus 1250 Broadway: website=https://old.regus.com; address_source_url=https://old.regus.com/offices/united-states/new-york/new-york-city/office-space/ny-new-york-1250-broadway; address_source_type=operator-site
- AO-W-030 Regus 136 Madison Avenue: website=https://old.regus.com; address_source_url=https://old.regus.com/offices/united-states/new-york/new-york-city/office-space/ny-new-york-city-136-madison-avenue; address_source_type=operator-site
- AO-W-012 Regus 41 Madison Avenue: website=https://old.regus.com; address_source_url=https://old.regus.com/offices/united-states/new-york/new-york-city/office-space/ny-new-york-city-41-madison-avenue; address_source_type=operator-site
- AO-W-019 Spaces Midtown South (401 Park Avenue South): website=https://old.regus.com; address_source_url=https://old.regus.com/offices/united-states/new-york/new-york-city/office-space/ny-new-york-spaces-midtown-south; address_source_type=operator-site
- AO-W-020 WeWork 27 E 28th St (79 Madison Ave building): website=https://liquidspace.com; address_source_url=https://liquidspace.com/us/ny/new-york/wework-27-e-28th-st; address_source_type=operator-site

### R1-16 founder_review on top 60: 49
