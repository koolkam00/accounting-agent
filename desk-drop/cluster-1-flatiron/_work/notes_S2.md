# Slice S2 research notes (18th to 22nd Street, Sixth Avenue to Park Avenue South)

Researcher: S2. Dates opened: 2026-10-23 and 2026-10-24. Files: `companies_S2.csv` (72 rows), `buildings_S2.csv` (62 rows).

## What the slice covers

- In-box: 6th Ave (both sides) east to Park Ave S, buildings on 18th through 22nd St and avenue frontage between them.
- Margin: Irving Place, Lexington and Third Ave, plus one block past each end (the 17th St and 22nd-23rd St blocks).
- Overlap with other slices. S1 is also recording 18th St buildings (111 and 115 Fifth, 215 and 225 PAS, 37 E 18th, 25 W 18th). S3 is also recording 22nd St (16 W 22nd, 25 E 22nd) and 300 PAS. I checked every row against `companies_S1/S3/S4.csv` before adding it, by name and by name plus address. Skipped as already recorded: Phia, Galvanize Climate Solutions, Radar, Kodansha USA, M&C Saatchi, 1stDibs, Nayya, Stellar Health, Global Strategy Group, monday.com, Adyen, Prophet and Palantir. I removed one duplicate of my own: I had added Radar Labs before S1's "Radar" row appeared, and the row was dropped.

## Confidence scale used (stricter than CONTRACTS section 4)

- **high**: a recent source (after 2024-10-23, or a live company, Built In or SEC page opened now) plus an independent confirmation of a different kind. Two outlets that repeat the same landlord press release count as **one** source.
- **medium**: one recent source, or two sources that conflict on move timing. Example: a lease is signed but the company website still shows the old address.
- **low**: lease sources older than 2024-10-23 with no current confirmation, or conflicting sources.

## Search strategies and what worked

1. **Commercial Observer WordPress REST API** (`/wp-json/wp/v2/posts?search=...&after=...`). This was the best source. I pulled full article text for searches like "Flatiron lease", "Park Avenue South", "Avenue of the Americas", "Gramercy" and street names, then used a regex to keep only addresses in the slice. Years covered: 2016-2026. It produced most of the lease rows and the co-tenant lists ("other tenants include...").
2. **The Real Deal and REBusiness WP APIs**: same method. Used for second sources (TRD top-lease lists, REBusiness lease briefs).
3. **Built In NYC `/company/<slug>/offices` pages.** These show the street address and "Total Employees". That count is whole-company, so headcount_scope is always whole-company. The main company page no longer shows a street. I guessed slugs from company names and checked the page title or website link to be sure it was the right company. Wrong-company matches I rejected: `extend` (extend.com, not Extend AI), `manifest` (manifest.com, not Manifest Law), `phia` (Fairfax VA), `flex` (LA), `img` (Alexandria VA).
4. **Company websites**: contact, terms, privacy and studio pages, plus schema.org PostalAddress. These confirmed Pentagram, Extend AI, Actively AI, Vivaldi, Farmacy, ZGF, Phipps, The Information, 32BJ Funds, Dashlane, Perkins Eastman, Heard City and GTS. They also exposed stale lease-only rows: Wilson Daniels, Hudson Companies, Options Group and Argentic still list their old addresses.
5. **SEC EDGAR** full-text search plus `data.sec.gov` submissions, giving business addresses of public companies in slice ZIP codes, plus 10-K/10-Q cover pages. This found The Vita Coco Company (10-K: 111 Fifth Ave, 2nd fl; 336 FTE), WW International (10-Q: 18 W 18th St, 7th fl), WBD (230 PAS) and 1stDibs (300 PAS, already in S3).
6. **Metro Manhattan building pages** (WP custom type `buildings`): used for lobby and security wording and loading docks. Their tenant lists are broker marketing copy and are often stale. Vault49 is listed at 36 W 20th, but its own site shows 180 Varick. I did not use them alone for a company row. They count only as a weak confirmation (General Assembly, SeatGeek).
7. **Geocoding**: `_shared/geocode.py`, run sequentially, once per new address. Useful finds:
   - 25 W 18th and 45 W 18th share a tax lot with 620 Avenue of the Americas (BBL 1008207505).
   - 881 Broadway shares a lot with 115 Fifth (1008470062).
   - 111 E 18th shares a lot with 225 PAS (1008740001).
   - 635 and 641 Avenue of the Americas are one building on two lots.

## Dead ends

- **WebSearch ran out.** The shared 200-call budget for this run was used up early, and I did not try to work around it. Everything after that point came from direct publisher APIs, Built In, SEC, company sites and WebFetch of known URLs. More web searches by building ("900 Broadway", "920 Broadway", "935 Broadway", "160 Fifth", 233-270 PAS) would probably add 10 to 20 mid-size rows.
- **Sites that blocked us:**
  - Blocked outright: traded.co (Cloudflare 403), PincusCo, Connect CRE and Mann Report APIs (401), Crain's (403), and LinkedIn (not tried, per the rules). The linkedin_company_url column is blank everywhere.
  - Built In rate-limited after about 150 requests (HTTP 429).
  - Wikipedia API rate-limited too, so I used WebFetch instead.
- **Form D (EDGAR) search**: it mostly returned pooled investment funds and mail-drop addresses. Low value, dropped.
- **228 Park Avenue South** is a virtual mailbox (PMB and suite numbers used by Phia, SPACs and others). It is not an office.
- **Stale or moved, not recorded:**
  - Bitly: Built In says 139 Fifth, but its own site says 250 W 34th.
  - Moved out of the slice: Union Square Ventures, Oak View Group and Alpine Investors (from 920 Broadway); Athena Club (915 Broadway); Arch (111 E 18th); Codat (156 Fifth, which Built In lists at 215 PAS); Vault49 and Atelier Ten.
  - Current is moving to Penn 2.
  - Plaid: Built In says 215 PAS, but it moved to 530 Broadway.
  - Innovid is at 30 Irving Place, which is south of the margin.
- **Not companies or not pantry fits, skipped:** MoMath (museum; admin office at 134 W 26th), Bam Labs (gym), Saatva (mostly showroom), medical practices (MD2, Union Square Eye Center, AdvantageCare), and small funds or biotechs at 149 Fifth Suite 500.

## Coworking

- No company row is flagged in_coworking=Y; none of the recorded addresses is a coworking location.
- Coworking locations seen in the slice, listed in building notes for the coworking file:
  - Industrious at 902 Broadway, 7th fl (CO Feb 2026), and at 215 PAS (S1's building).
  - The Malin Flatiron at 895 Broadway (opened 2025).
  - Spaces (IWG) at 287 PAS (margin, 2018 lease, not re-confirmed).
- Former WeWork sites: 35 E 21st St (WeWork exit per CO Oct 2023; Airtable is now listed there), 38 W 21st and 7 W 18th (leases rejected in 2023), 67 Irving Place (now an office-to-residential conversion), and WeWork at 620 6th Ave (2019, status unknown).
- Stash is currently in a WeWork at 450 PAS, outside the slice. Its row is at its new direct lease at 641 6th Ave.

## Conflicts for the merge step

- **Kaltura**: S1 records it at 860 Broadway (lease press), but its SEC business address is 250 Park Avenue South, 10th Floor (opened 2026-10-23).
- **Adyen**: S1 records it at 71 Fifth, but CO and TRD (Apr 2026) have it leasing 90K sf across 111 and 115 Fifth Ave. That is in this slice's 18th-19th St block.
- **WW International**: SEC 10-Q gives 18 W 18th St; Built In gives 675 6th Ave. Both are in this slice; the row uses SEC.
- **Hex Technologies**: lease for 250 PAS fl 7 (Jan 2026), but Built In still lists 44 W 18th. Both are in this slice.
- **32BJ**: S1 has the union (SEIU 32BJ) at 25 W 18th St; I have the Benefit Funds at the same address, which is the 620 6th Ave lot. Probably one pantry.
- **Warner Bros. Discovery**: wbd.com redirected to skydance.com on 2026-10-24, so ownership may have changed.

## Spot check (5 random rows, seed 20261024, re-opened 2026-10-24 by fetching the live article page)

| Row | Source re-opened | Result |
| --- | --- | --- |
| Varley, 155 Fifth Ave | CO 2025-04-25 | Pass: "the offices of fashion retailer Varley" |
| Broadway Builders, 902 Broadway | CO 2026-03-24 | Pass: 12th floor, joint tenancy with Hudson Companies |
| Fenwick & West, 902 Broadway | CO 2026-06-16 | Pass on address. Floor corrected from "18" to "13-15, 18" (the 13th floor was added in 2026) |
| Wilson Daniels, 250 PAS | CO 2025-06-05 | Pass: entire 8th floor |
| Cobalt Service Partners, 53 W 21st St | CO 2025-02-06 | Pass: five-year, 5,000 sf lease |

No row failed. One row was corrected (Fenwick floors).

Other checks I ran:
- I opened every website URL. christiesrealestategroup.com and generalassembly.ly did not connect, so those fields were blanked.
- ZIP codes are filled only where a source for that building shows the ZIP. Otherwise they are blank.
- GTS was upgraded to high after its locations page confirmed 625 Sixth Avenue.

## Gaps

- **Headcount**: 32 of 72 rows are unknown, because Built In has no page or the company is not tech (architects, law, fashion, real estate, nonprofits). No headcount was estimated from square footage. Only one nyc-office count exists: Christie's IREG, "75-person office", CO 2024.
- **Lobby type** is sourced for 14 of 62 buildings (13 security desk, 1 loading dock at 620 6th Ave). The rest are unknown. I found no certificate-of-insurance requirement anywhere, so coi_required is unknown everywhere. Landlord property pages (Feil, GFP, Koeppel Rosen, Winter, HRC) are JavaScript apps or 404 to curl.
- **Thin coverage**:
  - Side streets (W 19th-22nd mid-block lofts, E 19th-21st) and Broadway 920-940.
  - 160-175 Fifth (retail and condo).
  - 233-270 PAS (233 PAS is hospitality and medical; 260 PAS was not researched).
  - 6th Ave 636-700.
- **Margin**: east of PAS between 17th and 23rd is mostly residential, hotels, schools and conversions. Only 3 margin rows: Flexible Finance and IMG Worldwide at 300/304 PAS, and Similarweb at 50 W 17th.
- **Lease-only rows** (Synthesia, Candid Health, Stash, Hex, Hudson Companies, Argentic, Options Group, Manifest Law, Wilson Daniels) have signed leases, but move-in is unconfirmed. The founder should check the lobby directory on the walk.
- **Over-500 rows** (19), for the near-miss list: Netflix, Airbnb, Mastercard, Fenwick & West, Tory Burch, Cole Haan, Infor, dsm-firmenich, WBD, MillerKnoll, Ro, Reaktor, AngelList (518), Airtable, Perkins Eastman, WW International, SeatGeek, e.l.f. Beauty and Similarweb (margin).
