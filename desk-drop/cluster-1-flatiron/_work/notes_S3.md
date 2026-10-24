# S3 research notes: 22nd to 26th Street, Sixth Ave (west side) to Park Ave S

Researcher: S3. Opened all sources on 2026-10-23 unless a row says otherwise.

## Conventions used in companies_S3.csv

- `address_source_date` is the publication date when the source is dated. For live pages with no date (company sites, Built In profiles, landlord pages) it is 2026-10-23, the day I opened them, and the note says "live".
- Built In profiles: headcount comes from the "Total Employees" figure on `builtinnyc.com/company/<slug>/offices`. It is always `whole-company` because Built In does not split NYC staff. Built In addresses are often stale (see dead ends), so a Built In address alone was never trusted when the company site or recent leasing press disagreed.
- Two articles that repeat one landlord press release (for example CO and NYREJ on the same Two Trees release) count as one source, not two.
- Leases signed but not yet occupied are recorded at the new address with the move-in caveat in `notes`.
- `slice_check`: 26th Street frontage counts as in-box. S4 also covers 26th Street, so I skipped rows S4 already had (dedupe by company name).

## Search strategies

(updated as I go)

1. Building-by-building leasing press: "<address> lease 2025 OR 2026" for 200 Fifth, 11 Madison, 1 Madison, 41 Madison, 360/345/315/300 PAS, 16 Madison Square West, 50/53/49/43/61 W 23rd.
2. Flatiron NoMad Partnership (BID) monthly news roundups, Oct 2023 to Oct 2026: the "Real Estate" section of each roundup lists every notable district lease with a link to the original article. This was the single most productive source. URLs: flatironnomad.nyc/YYYY/MM/DD/<month>-news-roundup-N/.
3. Built In NYC `/company/<slug>/offices` pages for headcount and a second address check.
4. Company websites: footer, contact, privacy and terms pages, which often carry the legal mailing address.
5. Landlord and building sites: Rockrose (300 PAS), Columbia Property Trust and 315pas.com (lobby and tenant resources), SL Green press releases (11 Madison, One Madison).
6. Wikipedia infoboxes for headcount of the large (over-500) tenants.
7. After the shared web-search budget ran out mid-task, Commercial Observer address tag pages (commercialobserver.com/tag/<number>-<street>/) fetched directly, no search engine. I generated about 1,440 candidate address tags for every plausible building number on W/E 22nd-25th St, Broadway 900-1159, Fifth 170-231, PAS 270-361, Sixth Ave 660-759 and Madison 1-51; 127 tags exist. Each tag page lists CO articles about that address; I opened the relevant 2022-2026 office articles.
8. Landlord sites fetched directly: Adams & Company (adamsre.com; 49/53 W 23rd, 30 W 24th, 16 Madison Square West, 121 E 24th), Williams Equities (28-40 W 23rd), Kaufman (track record only), Cure / Deerfield (345 PAS), GFP (175 and 230 Fifth).
9. Built In NYC size listings (builtinnyc.com/companies/size/201-500 and /51-200, paged with ?page=N) harvested for company slugs, then each company's /offices page scanned with a regex for in-slice street addresses. Every hit was then checked against the company's own site (footer, contact, privacy or terms pages) before recording; Built In-only rows are marked medium and say so.
10. Wikipedia building articles (200 Fifth Avenue, 11 Madison Avenue) for tenant names and physical details such as loading docks.

Dates: most sources were opened on 2026-10-23; the session clock rolled past midnight UTC, so pages opened later carry 2026-10-24. found_date stays 2026-10-23 as instructed.

## What worked

- FNP roundups plus the linked Commercial Observer articles. CO articles usually list other tenants in the same building, which surfaced more names than the lease itself.
- Company legal pages (privacy, terms) for the current mailing address.
- 315pas.com publishes lobby security, a security desk phone line and contractor insurance rules.

## Dead ends and corrections

- Built In addresses are often stale: Betterment (Built In says 8 W 24th St; betterment.com footer says 450 W 33rd St), Roland Foods (Built In 71 W 23rd St; rolandfoods.com/contact says 115 W 18th St Fl 5), Clinch (2023 lease at 50 W 23rd; Built In HQ 37 W 20th St), Cadre (CO Feb 2026 lists it at 315 PAS; cadre.com says 245 Fifth Ave Fl 21), Clay and Legora (Built In shows pre-move offices). None of these were recorded at the stale address.
- theSkimm: Built In says 53 W 23rd St, but theSkimm's legal pages point to parent Ziff Davis / Everyday Health at 360 PAS 17th floor. Not recorded (S4 has Ziff Davis at 360 PAS).
- William Grant & Sons: Rockrose still lists it at 300 PAS, but FNP Jan 2025 roundup (citing NY Business Journal) says its US HQ moved to 902 Broadway. Not recorded.
- Built In "purple" is the mattress company in Utah, not Purple PR. Built In "sapien" is a 5-person Berkeley firm, possibly not the Sapien AI that leased 48 W 25th St. Neither used.
- Landlord sites for SL Green (property pages), BXP and 1madisonnyc.com returned HTTP 403. traded.co and commercialcafe.com returned 403.
- newyorkyimby.com returned 403 to WebFetch and curl.
- Wikipedia API rate limited (HTTP 429) part of the time; WebFetch worked for the rest.
- The shared WebSearch budget (200 calls per turn across all agents) ran out partway through. After that I used only direct page fetches.

## Skipped on purpose

- Under 40 by source: Raycon (35 total, Built In; 1115 Broadway Fl 12), AI One (20, Built In; 49 W 23rd), Bluefish (29 per Built In, though its new 315 PAS 8th floor has 80+ workstations per CO Feb 2026; founder may revisit), Ergatta (15), Normal Computing (CO Sept 2026: about 30 employees at its new 61 W 23rd HQ from Nov 2026; this is the 30-39 founder's-call zone).
- Retail, restaurants and clubs: P.C. Richard & Son, Eataly, The Maze, Sunday Morning, Chi Chicken.
- Medical: EmblemHealth / AdvantageCare at 21 E 22nd St.

## Gaps

(updated at the end)
