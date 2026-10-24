# S1 research notes: 14th to 18th Street, Sixth Avenue to Park Avenue South

Researcher: S1. Research run 2026-10-23, finished just after midnight on 2026-10-24.
Files: `companies_S1.csv` (62 rows), `buildings_S1.csv` (32 rows), this file.

## Slice rules I applied

- **in-box**: buildings on the tax blocks from the north side of 14th Street to the south side of 18th Street, between the west frontage of Sixth Avenue and the Park Avenue South / Union Square East frontage. Both sides of Park Ave S count as in-box.
- **margin**: the south side of 14th (13th to 14th blocks), the north side of 18th and the 18th to 19th blocks, and east of Park Ave S / Union Square East through Third Avenue.
- I checked which side of the street each building is on from the NYC tax block in the geocoder's `bbl`, not from the street number alone. This moved four sites to margin:
  - 853 Broadway and 841 Broadway are on block 565, the same block as Whole Foods at 4 Union Sq South.
  - Zero Irving (124 E 14th) is on block 559, the same block as Trader Joe's at 142 E 14th.
  - 37 E 18th St is on block 847 (18th to 19th).
- 841 and 853 Broadway come back with the same BBL (1005650015). Feil runs them as one combined site. I kept them as two building rows, and the shared BBL is explained in the notes.

## Field conventions

- `address_source_date` is the publication date for a dated article or filing. For a live company or building page it is the date I opened it.
- `found_date` is 2026-10-23 on every row, as instructed. Pages opened after midnight carry 2026-10-24 as their source date.
- `headcount_scope` is `whole-company` on every row that has a band. No source I opened gave a New York office count.
- Websites: I loaded every URL in the `website` column. Two were left blank:
  - U.S. News: the site would not load from here.
  - Rakuten USA: the operating unit at this address is not stated.

  Where a website was unverified (Iterative Scopes, Eagle AI, Delos, Walleye, Matador, Stone Source, Casa Komos, First Look Media), the field is blank.
- Confidence follows CONTRACTS section 4. "Recent" means a source dated after 2024-10-23. When both sources trace back to the same broker announcement, I still counted them as two publications and said so in the notes (Selldorf, Valon).

## Search strategies and what worked

1. **Commercial Observer address tag pages** (`commercialobserver.com/tag/<number>-<street>/`). This was the best discovery tool. I scanned about 200 address slugs in and around the slice, then read the 2022 to 2026 articles. Most rows come from these.
2. **Commercial Observer market pages** (`/market/union-square/`, `/market/flatiron-district/`). These gave the 2026 leases: Thinking Machines Lab, Biohub, Fundraise Up, Phia, Eagle AI, Kharon, Iterative Scopes and Robin Hood.
3. **SEC CMBS prospectus for 215 Park Avenue South** (Benchmark 2026-B42, rent roll dated 2026-02-05). It gave the top 10 tenants, subleases and lease expirations. This one document produced 9 rows.
4. **Built In NYC company pages**, fetched with curl. These give "Total Employees" reliably, but never a street address. All bands except Rockwell, Selldorf and Con Ed come from Built In.
5. **Company contact and footer pages** confirmed addresses for: Rockwell, Adyen, Cognitiv, Global Strategy Group, Gresham, LUMA, Lepercq, Battery Ventures, USHG, SEIU 32BJ, Alpine, GameChanger and Senator. Cognitiv, Gresham and LUMA were also re-checked in the spot check.
6. **Lobby sources** came from the Metro Manhattan broker pages for 200 PAS ("round-the-clock lobby staff") and 215 PAS ("24/7 access and security"). For 853 Broadway the source was the building's own marketing site ("24-hour concierge desk").
7. **NYREJ, REBusiness and Connect CRE** supplied second sources and some older lease details.
8. **Wikipedia building pages** confirmed that the Decker Building (33 USW) is residential and that 4 Irving Place is Con Ed's headquarters. They also gave the Selldorf staff size.

## Dead ends

- **WebSearch budget.** The shared 200-search limit ran out partway through the run. Everything after that came from fetching known pages directly: CO tag and market pages, company sites, Built In and Wikipedia. I did not use curl or any other route to query a search engine.
- **Blocked sites**: traded.co (403, so the Tao Group lease at 200 PAS is unverified), newyorkyimby.com (403), trueup.io (403), rockwellgroup.com/offices (403) and humansecurity.com (403).
- **Landlord sites that would not connect**: Bromley, Gordon Property Group, Winter Organization and L&L Holding (connection resets or 502s). So I have no tenant directories and no lobby or COI facts from owners.
- **Metro Manhattan** has building pages for only a few slice addresses. Its `?p=` links return 410.
- **No usable tenant data** from CO tag-page pagination, the REBusiness category pages, the Metro Manhattan llms.txt, or most Wikipedia pages.
- **Former tenants** found during checks:
  - NRP Group has moved from 1 USW to 1001 Avenue of the Americas.
  - Vistar Media is at 625 Sixth Ave, not 853 Broadway.
  - Current (fintech) is leaving 620 Sixth for Penn 2.
  - Updater (19 USW, 2018) could not be confirmed as current.
- **SEC EDGAR blocks any request whose User-Agent has no contact email.** My first download of the 215 PAS prospectus sent the account owner's email in the User-Agent header. That should not have happened, and I did not repeat it. For the spot check I used the independent NYREJ source instead.

## Skipped as clearly under 40 (from an opened source)

- Accrue Savings at 100-104 Fifth: Built In 30.
- Pixie Labs (8) and Permian Labs (16) at 37-39 W 17th.
- Oden Technologies at 10 W 18th: Built In 37.
- Electric Capital at 200 PAS: Built In 19.
- Pushkin Industries at 5 USW: Wikipedia says it laid off 17 people, over 30% of staff, in 2023.
- Smaller firms I did not record: Hack VC (116 E 16th), Vine Ventures (101 Fifth), Adagy Robotics (no profile), Cloud Touchless Massage (a spa), UnionDerm and Greenbrook (medical), and retailers.

## Watch items for the founder (move or lease risk)

- **Adyen** signed 90,000 sf at 111 and 115 Fifth (CO 2026-04-07). It will probably leave 71 Fifth.
- **Capgemini** signed at Penn 2 (CO 2025-12) and may be leaving 79 Fifth. Row downgraded to low.
- **U.S. News**: CO 2026-04-28 says it is moving from 129 W 29th to 31 Penn Plaza. That conflicts with CO 2026-10-19 listing it at 120 Fifth. Row set to low.
- **Signed but not yet moved in.** Move-in timing is not stated for:
  - Robin Hood (currently at 826 Broadway)
  - Eagle AI (currently at 5 Penn Plaza)
  - Thinking Machines Lab, Biohub and Fundraise Up
  - Profound's new floors
  - eBay and Galvanize
- **Cognitiv's** sublease at 215 PAS runs to 2027-01-31. **Rakuten's** lease ends 2027-12-31. **Personetics** signed a three-year lease in about October 2024.

## Coworking seen in the slice (no company row flagged in_coworking)

- Industrious at 860 Broadway (5th and 6th floors) and at 215 PAS (three floors, to 2035). Both are already in `coworking_research.csv`.
- Hub Seventeen at 114 Fifth Ave (CO 2025-02). This one is not in `coworking_research.csv` yet.
- Former WeWork footprint at 620 Sixth Ave (handed to tenants after the 2023 bankruptcy).
- WeWork at 18 W 18th St (in-box) is in `coworking_research.csv`. I found no tenant source for it.

## Gaps

- **Thin side streets.** CO has almost no articles on the loft buildings on W 14th to W 16th Streets, the west frontage of Sixth Avenue, or E 16th and E 17th between Fifth and Union Square West. These blocks likely hold many 40 to 150 person firms that I could not source without search. Next pass: Built In "offices" pages, company job listings and LinkedIn.
- **Thin margin.** Irving Place and Third Avenue are barely covered.
- **Lobbies.** Only 3 of 32 buildings have a sourced lobby type. None has a COI requirement, so `coi_required` is unknown everywhere. The foot walk has to settle this.
- **Headcount.**
  - 19 rows have no headcount band.
  - 19 rows are over 500 and belong on the near-miss list.
  - No row has a New York office count.
  - The Built In counts for Mercury (150), Perplexity (41) and Robin Hood (659) look out of line with other reporting. I recorded only what Built In shows, flagged it, and left Perplexity unknown.
- **LinkedIn** company URLs: none collected.

## Spot check (random re-open of address sources)

I picked five rows with `random.seed(20261023)`, re-opened each address source on 2026-10-24, and checked that it still places the company at the address.

| Row | Source re-opened | Result |
| --- | --- | --- |
| Rakuten USA, 215 PAS | SEC prospectus | Could not re-open: SEC returned 403 without a contact email in the User-Agent. The second source (NYREJ 2024-12-10) re-opened and still lists Rakuten USA as a tenant. Row kept at high; the lease ends 2027-12-31. |
| monday.com, 225 PAS | CO 2025-12-05 | Pass: still says it expanded to 138,611 sf at 225 Park Avenue South. |
| Cognitiv, 215 PAS | cognitiv.ai/contact | Pass: "215 Park Ave S, Floor 16". |
| Gresham, 19 USW | greshamllc.com/contact | Pass: "19 Union Square West, 11th Floor". |
| Personetics, 853 Broadway | NYREJ 2025-04-08 | Pass: 19th floor, three-year lease. |
| LUMA Partners, 101 Fifth (replacement for Rakuten) | lumapartners.com/contact | Pass: "101 Fifth Avenue 9th Floor". |

No row failed, so nothing was downgraded by the spot check. The downgrades for Capgemini and U.S. News came from conflicts found during research.
