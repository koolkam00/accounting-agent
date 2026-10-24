# S4 research notes: NoMad, 26th to 30th Street (margin 25th to 31st), Sixth Ave (west side) to Park Ave S

Researcher: S4. Sources were opened on 2026-10-23. The session ran past midnight UTC into 2026-10-24, but `found_date` and live-page dates stay at 2026-10-23, the date the task fixed.

## Output

- `companies_S4.csv`: 82 rows (72 in-box, 9 margin, 1 outside).
  - Confidence: 30 high, 37 medium, 15 low.
  - Headcount band: 46 unknown, 15 over-500, 9 at 151-250, 5 at 251-500, 4 at 76-150, 3 at 40-75.
  - Coworking: 1 row flagged (Monte Carlo, inside WeWork at 27 E 28th St).
  - Candidates that are not outside, not in coworking and not over 500: 65 (24 high, 28 medium, 13 low). 60 of them are in-box.
- `buildings_S4.csv`: 39 buildings, all geocoded with a BBL. Every company row's BBL has a building row.
  - Lobby type: 7 security desk (each from a broker building page that says 24/7 security, an attended lobby or concierge), 32 unknown.
  - Certificate of insurance: no source found for any building, so all 39 are `unknown`.

## Conventions

- `address_source_date` is the publication date when the source has one. Live pages with no date (company sites, Built In profiles) use 2026-10-23, the day I opened them.
- Confidence follows CONTRACTS section 4, applied more strictly in three ways:
  - Two items from the same publication, or a BID roundup that repeats a Commercial Observer (CO) item, count as one source.
  - A row is downgraded to `low` when the company's own current site contradicts the lease article, as with Suvretta, which still shows 540 Madison.
  - A row is also `low` when the lease is signed but the move is clearly in the future (Vestal Point, Zip in April 2027).
- High means a recent source plus an independent confirmation. Usually that is CO plus the company site or Built In. Where an older lease article (more than 24 months old) is confirmed by the company's live site, I counted the live site as the recent source and recorded both.
- Headcount comes only from Built In "Total Employees" (always `whole-company`), or from a press figure (Primary Ventures "40 employees", CO 2023, `nyc-office`). The Knot's "100 employees in New York" (CO 2025-11-07) is in its notes; its band is the whole-company over-500 figure so the near-miss rule works. No headcount was estimated from square footage.
- `slice_check` is computed from the geocoded point: I project lat/lon onto the rotated Manhattan grid and calibrate against geocoded points on W 22nd, W 26th, W 30th and E 33rd St, plus Sixth Ave, Park Ave S and Third Ave. Residuals are under 0.1 block.
  - In-box: street index 25.6 to 30.4 (lots fronting 26th St from the south and 30th St from the north), from the west side of Sixth Ave to the east side of Park Ave S.
  - Margin: street index 24.6 to 31.4, east to Third Ave.
  - 135 and 136 Madison (31.7) are outside. 104 W 27th St (west of Sixth Ave) is outside.
- Overlap with S3: 360 Park Ave S (BBL 1008550024) is in both slices because 26th Street frontage counts for both. S3 holds seven tenant rows there and S4 holds three, with no duplicate company. The building row is only in buildings_S4.csv. S3's Grammarly row is the same company as S4's Superhuman row.
- 27 E 28th St and 79 Madison Ave share BBL 1008580022. 28 E 28th St and 63 Madison Ave share BBL 1008570024. Deduplicate buildings on `bbl`.

## Search strategies, in order of yield

1. **Flatiron NoMad Partnership (BID) monthly news roundups.** The highest-yield source. I pulled every roundup from mid-2022 to October 2026 through the site's WordPress REST API, before the search budget ran out. I extracted each Real Estate item with its link to the original article (CO, NYREJ, Connect CRE, REBusiness, NY Business Journal). That produced about 60 NoMad and Flatiron office leads with direct article URLs.
2. **Commercial Observer address tag pages** (`commercialobserver.com/tag/<number>-<street>/`). These are browsable archive pages, not a search engine. I fetched them directly for about 120 addresses in the slice and margin. Each lists every CO article about that building.
   - CO articles often name other tenants in the building. That surfaced, for example, Warren, Suvretta, Reckoner, Holocene, Jump Trading, Butterfly, Mega 97.9 and Sierra at 11 E 26th St, and ICONIQ and Ziff Davis at 360 PAS.
3. **Built In NYC `/company/<slug>/offices` pages** fetched with curl. These give Total Employees and often a street address. Used for headcount and as an independent address confirmation. The "View Website" link on each profile verified the `website` field.
4. **Company contact, about and footer pages.** Used to confirm current addresses. Confirmed this way: Warren Equity, FCA, Grimshaw, TenBerke, Lee & Low, Prosek, Carbyne, OTTO, Ford Models, Polar, Primary Wave, CHN, Parloa, Collected Strategies, Full Picture, Ancillary Project, SL Home Fashions, Seedtag, Innovant and Signal AI.
5. **Metro Manhattan Office Space building pages**, found through their building sitemap. This is the only source that described lobbies: 24/7 security, an attended lobby or concierge at 261 Fifth, 245 Fifth, 63 Madison, 41 Madison, 1140 Broadway, 51 Madison and 1201 Broadway. These pages are undated broker marketing, so lobby types are a starting point for the founder's walk, not a verification.
6. WebSearch (early only): building-by-building lease searches and Built In site searches. The shared 200-search budget for the run was used up partway through. After that I used no search engine of any kind and only opened known URLs (tag pages, sitemaps, company sites, Built In profiles).

## Dead ends

- traded.co, nmrk.com (Newmark press releases), citybiz.co, rew-online.com, newyorkyimby.com and coworkingcafe.com returned 403 or a bot challenge.
  - The Zip lease (traded.co) was later confirmed via CO.
  - The Newmark 386 PAS release was covered by the CO article.
- LinkedIn: not attempted (blocked), so `linkedin_company_url` is blank on every row rather than guessed.
- WeWork building pages returned 403 to curl. WebFetch on the 27 E 28th St page was truncated and did not show the address. LiquidSpace's page "WeWork | 27 E 28th St, confirmed open" was used instead.
- Landlord sites (Rudin, Rockrose, TF Cornerstone, BXP, Moinian, Olmstead) are mostly JavaScript or have no lobby text. Feil's 261 Fifth page describes a gold-leaf lobby but not staffing.
- `11e26.com` is a spam domain, not the building site. Ignore it.
- Some company sites could not be read:
  - JavaScript-only sites: Holocene, Primary Ventures, BrightTower, Reckoner, Hanover Park.
  - TLS chain error: Suvretta's www domain and Clarick Gueron's site. I did not bypass TLS verification.
- Built In's neighborhood filter URL ignores the neighborhood, so there is no NoMad company list.
- Built In addresses are often stale. Found stale for Parloa, Grammarly/Superhuman, Hanover Park, Octus, Seedtag and Ziff Davis. Recent press or the company site won wherever they disagreed.

## Gaps and caveats for the assembler

- **Headcount unknown on 46 rows.** Mostly finance firms, agencies and brand offices without Built In profiles: Warren, Suvretta, Reckoner, Holocene, BrightTower, Urban Atelier, Polar, Tenex, GovWell, Full Picture, Collected Strategies, Mediaplus, AVP, Davies, SWA, IIN, CHN, TenBerke, Grimshaw, FCA, Lee & Low and others. These need intake or LinkedIn checks by the founder.
- **Signed but maybe not moved in.** Hanover Park, Sigma Computing, Order.co, Suvretta, Vestal Point, BrightTower, MCM, Corcoran, Mediaplus, Tenex, GovWell, Sierra (94,000 SF), Octus, The Knot and Zip (April 2027). Notes say which.
- **Address conflicts to resolve:**
  - K Health: CO renewal at 387 PAS versus Built In 298 Fifth.
  - Ziff Davis: CO at 360 PAS versus Built In 114 Fifth.
  - Superhuman/Grammarly: Built In 450 PAS versus CO 2025-09 at 29 W 30th St moving to 360 PAS. S3 has the Grammarly row at 360 PAS.
  - Full Picture: site 6th floor versus CO 11th floor.
- **Likely under 40 or not an office:** Augury (Built In says remote; "#169" suite looks like a mailbox), OTTO Brand Lab, Eton, Biologique Recherche, Ancillary Project, Idesco, Arca. Showroom-heavy rows: 230 Fifth tenants and Innovant.
- **Skipped on purpose:**
  - Under 40 per Built In: Stuut (20), Pace (12).
  - Retail, restaurants and fitness: Hero's Journey, Pixida, Stout and others.
  - Medical: Mount Sinai at 373 PAS.
  - TADA! Youth Theater: a theater, not an office. Noted in the buildings file.
  - Maria B. Campbell Associates: a 2,957 SF literary scout.
  - Civic Entertainment Group: the CO item was NoHo, not NoMad.
- **Coworking in the slice (for the coworking list, not company rows):**
  - Industrious, 386 PAS floors 18-19 (opening date not announced).
  - WeWork, 245 Fifth floors 2 and 4-6 (planned mid-2026).
  - WeWork, 27 E 28th St / 79 Madison. **Not yet in `coworking_research.csv`.**
  - Already in `coworking_research.csv`: The Malin (387 PAS, 5th floor), Regus (41 Madison, 31st floor) and WeWork (450 PAS).
- **Building risks:**
  - 79 Madison / 27 E 28th was marketed in March 2025 as a condo conversion.
  - 11 E 26th St has a tenant amenity club with a grab-and-go kitchen (CO), which competes with a pantry drop.
- **COI:** no building in the slice published vendor or delivery insurance rules that I could open.
- **Side streets west of Fifth** (W 26th to W 30th between Fifth and Sixth) are thin. CO tag pages exist for few of them. A walk or a broker list would add small and mid-size firms.

## Spot check (required: 5 random rows re-opened)

I chose 5 rows with `random.seed(20261023)` and re-opened each address source after all edits:

1. GovWell Technologies, 60 Madison (CO 2026-06-22): **pass**. The article still says a 17,500 SF lease on the entire eighth floor of 60 Madison.
2. Full Picture, 60 Madison (CO 2026-06-22): **pass**. The article says an 8,000 SF lease on part of the 11th floor. The company site shows 60 Madison, 6th Fl. The floor conflict is in the notes; the address holds.
3. Ziff Davis, 360 Park Ave S (CO 2025-05-20): **pass**. The article says "Other tenants in the building include media company Ziff Davis". The row stays medium because Built In conflicts.
4. Community Healthcare Network, 44 W 28th St (CO 2025-02-04): **pass**. The article says a lease on the entire fifth floor for administrative offices. It is also confirmed on chnnyc.org/contact.
5. TenBerke, 41 Madison (tenberke.com/contact): **pass**. The page shows "41 Madison Avenue, 17th Floor". curl got an intermittent 307 bot redirect, so I re-opened it with WebFetch.

No row failed, so nothing was downgraded by the spot check.

Other corrections made during the final review:
- Superhuman: downgraded to low over the address conflict.
- SharkNinja: replaced a derivative second source (a BID roundup quoting Built In) with CO 2025-01-30.
- Criteo: re-pointed the address source to the original CO article.
- Removed two facts I had only seen in search snippets: the 387 PAS story count and the "also 1150 Broadway" name for 230 Fifth.
- Monte Carlo's website corrected to montecarlo.ai, from Built In.
- Zip: the Built In "zip" profile (ZipHQ, procurement) is a different company, so I removed its headcount.
