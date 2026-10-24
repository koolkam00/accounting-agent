# S3 research notes: 22nd to 26th Street, Sixth Ave (west side) to Park Ave S

Researcher: S3. Sources were opened on 2026-10-23, or on 2026-10-24 after the session clock passed midnight UTC. Each row's dates say which.

Output: `companies_S3.csv` (63 rows), `buildings_S3.csv` (31 rows).

## Conventions used in companies_S3.csv

- `address_source_date` is the publication date when the source is dated. For live pages with no date (company sites, Built In profiles, landlord pages) it is the day I opened the page, and the note says "live".
- Built In headcount is the "Total Employees" figure on `builtinnyc.com/company/<slug>/offices`. It is always `whole-company`, because Built In does not split out NYC staff. No headcount was estimated from square footage or from my own sense of a company.
- Two articles that repeat one landlord press release (for example CO and NYREJ on the same Two Trees release, or two CO articles) count as one source. `high` needed two independent sources, at least one dated after 2024-10-23.
- Leases signed but not yet occupied are recorded at the new address. The move-in caveat is in `notes` and confidence is held at medium. Examples: Clay, Legora, Goodwin, Hunter Point Capital, Grammarly, Trexquant, Chalk, Normal Computing, Betches, Orbital.
- Where a newer source contradicted the address, I downgraded the row: Instacart is `low` because it signed at 111 W 33rd St in July 2026.
- `slice_check`: frontage on 26th Street and on both sides of Park Ave S counts as in-box. RepRally (137 E 25th) and At-Bay (220 Fifth at 26th, north side) are `margin`. S2 covers 22nd Street and S4 covers 26th Street as well, so I skipped any company another slice had already recorded. The helper checks normalized names before each append.

## Search strategies, in the order used

1. Leasing press, building by building ("<address> lease 2025 OR 2026") for 200 Fifth, 11 Madison, One Madison, 41 Madison, 360/345/315/300 PAS, 16 Madison Square West, and 50/53/49/43/61 W 23rd. This used WebSearch until the shared budget ran out.
2. Flatiron NoMad Partnership (BID) monthly news roundups, Oct 2023 to Oct 2026 and then 2021 to 2023. The "Real Estate" section of each roundup lists the district's notable leases with links to the original articles. This was the most productive single source. URL pattern: flatironnomad.nyc/YYYY/MM/DD/<month>-news-roundup-N/.
3. The linked Commercial Observer articles. Each one usually names other tenants in the same building, which surfaced more firms than the lease itself.
4. Built In NYC `/company/<slug>/offices` for headcount and as a second address check.
5. Company websites: footer, contact, privacy and terms pages, which usually carry the legal mailing address. This was the best check against stale data.
6. Landlord and building sites: Rockrose (300 PAS), Columbia Property Trust and 315pas.com, Adams & Company (adamsre.com: 49/53 W 23rd, 30 W 24th, 16 Madison Square West, 121 E 24th), Williams Equities (28-40 W 23rd, 104 E 25th, 120 E 23rd), BXP (360 PAS page), 1madisonnyc.com amenities, Cure / Deerfield (345 PAS), GFP (175 Fifth). SL Green press releases for 11 Madison and One Madison.
7. Wikipedia: infoboxes for the headcount of large tenants, and building articles (200 Fifth Avenue, 11 Madison Avenue) for tenant names and physical details such as loading docks.
8. After the WebSearch budget ran out, I fetched Commercial Observer address tag pages directly (commercialobserver.com/tag/<number>-<street>/), with no search engine. I generated about 1,440 candidate tags covering every plausible building number on W/E 22nd-25th St, Broadway 900-1159, Fifth 170-231, PAS 270-361, Sixth Ave 660-759 and Madison 1-51. 127 tags exist, and I opened the relevant 2022-2026 office articles. I also used CO's Flatiron District market page.
9. REBusiness Online leasing-activity category pages (400 pages), filtered for Manhattan, Flatiron and NoMad slugs. These gave second sources for Franklin Templeton and Suntory.
10. Built In NYC size listings (builtinnyc.com/companies/size/201-500, 1,522 slugs; /51-200, 2,717 slugs) and Built In NYC listicles (fintech, AI, ecommerce, marketing hiring). I harvested company slugs from them and scanned each /offices page with a regex for in-slice addresses. Every hit was then checked on the company's own site.
11. Direct checks of about 250 company domains (agencies, PR, adtech, fintech, proptech, consumer brands, nonprofits, architecture, VC) for in-slice addresses on their contact and legal pages. Yield was low (see gaps).

## What worked

- FNP roundups followed by the CO articles they link to.
- Company privacy and terms pages for the current mailing address. These found TripleLift (53 W 23rd Fl 12), BrainPOP (71 W 23rd Fl 17), 1stDibs (300 PAS Fl 10), Rogo (360 PAS Fl 7), Pilot Fiber (1115 Broadway Fl 12), RepRally (137 E 25th Fl 6), Kodansha USA (25 E 22nd), TKO (200 Fifth) and e.l.f.'s NYC HQ (16 W 22nd Fl 4, already recorded by S2).
- Building pages with lobby facts: 315pas.com ("24-hour attended lobby security", security desk line), Rockrose 300 PAS ("24-hour Attended Lobby"), Adams & Co (24/7 guard; 53 W 23rd has turnstiles), Williams Equities 28-40 W 23rd ("three attended lobbies"), the 2025 Two Trees release for 50 W 23rd ("24/7 attendant"), and Wikipedia for 11 Madison (loading docks on 25th St).
- Pantry signals the founder should know about: One Madison has a Daniel Boulud grab-and-go cafe in its tenant lounge. 11 E 26th has a grab-and-go kitchen (S4 note). Cure at 345 PAS runs a "fully stocked pantry" for its coworking residents, so Cure is an operator-controlled pantry, which makes it a candidate single office. Betterment's Built In page mentions free lunch and snacks, but Betterment has moved out of the slice.

## Dead ends and corrections

- Built In addresses are often stale, so a Built In address was never recorded when the company site disagreed:
  - Betterment: Built In says 8 W 24th St; betterment.com footer says 450 W 33rd St.
  - Roland Foods: Built In says 71 W 23rd St; rolandfoods.com says 115 W 18th St.
  - Clinch: Built In lists 37 W 20th St.
  - Cadre: CO Feb 2026 places it at 315 PAS; cadre.com says 245 Fifth Ave Fl 21.
  - EvolutionIQ: moved to 250 Hudson.
  - At-Bay: Built In says 19 W 24th; its site gives 220 Fifth Fl 8, which is how it was recorded.
  - AppsFlyer: its site says 180 Madison.
  - Bonobos: its site says 260 Madison.
  - 3Q Digital: now DEPT, at 470 PAS.
  - Addition Wealth: its site says 130 W 15th.
  - Gemini: its site says 600 Third Ave.
  - Codecademy: its site says 600 Broadway.
  - Figma (Built In "33 W 23rd St", which the geocoder matched to 23 W 23rd) and Blend (1140 Broadway): Built In only. Not recorded.
- theSkimm: Built In says 53 W 23rd, but its legal pages point to parent Ziff Davis / Everyday Health at 360 PAS 17th floor (S4 has Ziff Davis). Not recorded.
- William Grant & Sons: Rockrose still lists it at 300 PAS, but its US HQ moved to 902 Broadway (S2 has it).
- Wrong-company Built In profiles: "purple" is the mattress company, "sapien" is a 5-person Berkeley firm, "rogo" is in Indiana, and "flex" is in LA. None were used for headcount.
- Blocked: SL Green and BXP property pages (403 to curl; WebFetch worked for BXP's 360 PAS page and 1madisonnyc.com), traded.co, commercialcafe.com, newyorkyimby.com, TRD tag pages, withpersona.com, and NYREJ tag pages (500).
- Built In rate-limited (HTTP 429) heavily once several agents were scanning it, which capped the Built In size-list scan. Wikipedia's API also rate-limited; WebFetch worked instead.
- The shared WebSearch budget (200 calls per turn across all agents) ran out early. After that I used only direct fetches of known URLs and site navigation pages, and never queried a search engine.

## Skipped on purpose

- Under 40 by source: Raycon (35 per Built In; 1115 Broadway Fl 12), AI One (20; 49 W 23rd), Bluefish (29 per Built In, although its new 315 PAS 8th floor has 80+ workstations per CO Feb 2026; the founder may revisit), Ergatta (15), Protara Therapeutics (30; in Cure), Curex (3,100 sf; no count).
- Normal Computing was recorded after all: about 30 NYC staff, but 51 company-wide, so it is in the 30-39 founder's-call zone.
- Retail, restaurants and clubs: P.C. Richard & Son, Eataly, The Maze, Sunday Morning, Chi Chicken, Hearts of Gold.
- Medical: EmblemHealth / AdvantageCare at 21 E 22nd St.
- Coworking found but not in coworking_research.csv: Cure (Cure Experience Services LLC, Deerfield) at 345 PAS, with a hot-desk and private-office "Collaboration Residency", labs and a stocked pantry. Its residents Lexeo Therapeutics and Insilico Medicine are recorded with in_coworking=Y. The other listed residents (Advancium, ANVIA, Apertura, Ascertain, Buckle Therapeutics, CobiCure, Concerto Care, Deerfield Catalyst, Helaina, Hop Labs, Panacea Capital, Plum Alley Ventures, Protara, Sparian, Wandercraft) were not recorded. NeueHouse is at 104 E 25th St; Williams Equities' page places it there, while coworking_research lists 110 E 25th.

## Spot check (5 random rows re-opened on 2026-10-24, seed 20261024)

| Row | Source re-opened | Result |
| --- | --- | --- |
| Rogo, 360 PAS | rogo.com/legal/privacy-policy | Pass: "360 Park Avenue South, Floor 7" |
| Tiffany & Co., 200 Fifth | TRD 2025-04-03 | Pass: lists Tiffany among tenants |
| TripleLift, 53 W 23rd | triplelift.com/contact-us | Pass: "53 W. 23rd St., 12th Floor"; also says "400+ Talented Workers", added to notes |
| Harvey, 1 Madison | CO 2026-03-09 | Pass: 185,326 sf at One Madison |
| Green Mountain Energy, 16 MSW | CO 2026-01-08 | Pass: "the New York City offices of Green Mountain Energy" |

All five passed, so no downgrades came from the spot check. Separately, during research I downgraded Instacart (to low), Hunter Point Capital and Sigma (to medium), removed a duplicate Flex row that S2 already had, and corrected several Built In-only addresses (listed above).

## Gaps

- The target was 45 plausibly sized hosts (40 to 500, not in coworking). I reached 29. Another 32 rows are over 500 company-wide (near-miss) and 2 are in coworking. The core blocks (23rd to 25th St) are dominated by a few large towers (11 Madison, One Madison, 200 Fifth, 360 PAS) whose tenants are mostly over 500.
- 11 of the plausible rows have unknown headcount (Pilot Fiber, Purple PR, Kodansha USA, Betches, Rogo, Hunter Point, Grammarly, LaForce, Sapien AI, MediaCo, Madison Square Park Conservancy). LinkedIn was off-limits and none of these publish a count.
- Built In scanning covered about 850 company /offices pages: 553 from hand-built lists, 58 from listicles, and 237 of the 1,522 slugs on the 201-500 size list. The 2,717-slug 51-200 list was harvested but not scanned, because Built In started returning HTTP 429 (shared with other agents). Slugs are saved at /tmp/claude-0/-home-user-accounting-agent/35161228-045e-5c59-97cb-d166fe4ca4c5/scratchpad/slugs_201-500.txt and /tmp/claude-0/-home-user-accounting-agent/35161228-045e-5c59-97cb-d166fe4ca4c5/scratchpad/slugs_51-200.txt (session scratch, may not persist), so a later run could finish this. It is the most systematic remaining way to find 40 to 250 person tech firms in the slice, but every hit still needs a company-site check, because most Built In addresses I checked were stale.
- Sixth Avenue (west and east sides, 22nd to 26th) and the cross streets east of Park Ave S (to Lexington and Third) produced almost nothing in leasing press. These blocks are mostly retail, residential, Baruch College and SVA, so the east margin is thin by nature.
- No building source states a vendor or delivery COI requirement, so every coi_required is unknown. 315 PAS publishes contractor insurance minimums ($3M CGL, COI naming Columbia), which may apply to vendors; the founder should ask.
- Lobby type is sourced for 8 buildings (security desk) and 1 (loading dock, 11 Madison). The other 22 are unknown and need the on-foot walk.
- Move-in timing is unknown for several 2026 leases (Clay, Legora, Goodwin late 2026, Grammarly, Trexquant, Chalk, Betches, Orbital, Sapien AI, Normal Computing in Nov 2026). The founder should confirm who is actually in the building before walking in.
