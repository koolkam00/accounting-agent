# Stage 2 notes: brand contacts, ranks 1 to 60

Workstream A, stage 2 of 3, 2026-10-24. Paths are relative to `desk-drop/`.

**Output:** `clay-icp-tables/_work/contacts_b1.csv` (160 rows), built by `clay-icp-tables/_work/contacts_b1_tools/build_contacts_b1.py`.
Columns: `row_id,company,contact_rank,first_name,last_name,title,contact_linkedin_url,source_url,source_date,confidence,notes`.

Nothing was sent, posted or signed up for. No email was guessed or built. No connector tool was used. LinkedIn was never opened.

## Scope

The 60 brands in `clay-icp-tables/_work/top60_brands.csv`. For each: the founder and the marketing lead. Existing stage-1 contacts were re-verified; missing slots were researched.

## Row layout

- Exactly one `founder` row and one `marketing` row per brand (120 rows). The builder fails if a brand has more or fewer.
- `marketing` row with `first_name = none found` when no marketing lead was found. `confidence = n/a` on those rows. At small, founder-run brands the founder is the marketing contact.
- Extra `backup` rows (40) keep second co-founders, CEOs who are not founders, and second marketing names, so the stage-3 merge loses nothing. Stage 3 should map `founder` to the primary slot and `marketing` to the backup slot, falling back to the first `backup` row when marketing is `none found`.
- `source_date` is the date the source was opened or seen (2026-10-24). The source's own date (article date or The Org `updatedAt`) is in `notes`.

## Sources, in the order used

1. **Re-open every stage-1 source** (`contacts_b1_tools/verify_existing.py`, log `_work/contacts_b1_verify_existing.csv`, pages in `_work/fetch/contacts_b1/verify/`). 70 contacts re-opened: 64 pages returned 200 with the name present; Wikipedia (Beyond Good) and supermarketnews.co.nz (Bruce Cost) returned 429, Goldbelly (Seed + Mill) 403. Beyond Good was re-confirmed through the mobile Wikipedia URL and The Org; Seed + Mill through the brand's own press kit; the Bruce Cost 2017 article was not re-confirmed (row marked snippet-unverified).
2. **The Org** (theorg.com): company pages found by slug and matched to the brand's own domain (`contacts_b1_tools/theorg_scan.py`, `theorg_parse.py`), then each candidate's position page (`theorg_person.py`) for role timeline and `updatedAt`. 39 company pages matched a top-60 brand or its parent company by domain (33 with named positions); 53 position pages opened. Home locations shown on The Org were not stored.
3. **Brand team, about and press pages** (`contacts_b1_tools/site_scan.py`): homepage plus up to eight about/team/story/press links per brand, all 60 brands.
4. **Public podcast pages that list guest LinkedIn URLs**: the Startup CPG podcast RSS feed (`https://feeds.transistor.fm/startupcpg`, 517 episodes, one request) matched to brand names and domains, and The Kara Goldin Show episode pages found through its public `podcasts-sitemap.xml`. These pages are where most founder LinkedIn URLs came from.
5. **WebSearch**: 37 calls (budget about 60), logged in `_work/contacts_b1_searchlog.csv`. Yield was low: the search tool returns article lists and a summary, rarely LinkedIn profiles. Articles it pointed to were opened with curl where the site allowed it (Nosh, BevNET, Delimarketnews and some directories return 403; those rows stay snippet-unverified).

## Counts

| Slot | Rows | Found | None found | Opened | Snippet-unverified | LinkedIn URL | Surname unknown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| founder | 60 | 59 | 1 (Goody's Granola) | 57 | 2 (Reelie, Bruce Cost) | 14 | 1 (Cirrus 9) |
| marketing | 60 | 26 | 34 | 20 | 6 | 3 | 0 |
| backup | 40 | 40 | 0 | 37 | 3 | 3 | 3 |

Against stage 1: 51 founders confirmed as they were (some now with surnames), 7 changed, 1 new (Gigantic: Stu Davidoff). Stage-1 marketing leads: 9 kept, 5 moved out of the marketing slot because the page gave a different role, 16 new marketing leads found.

**Founder slot changes:** Eleni's spelling (Gianopulos per The Org and press; brand page says Gianopulous), Raaka (Nathan Hodge, CEO, replaces the unverified Ryan Cheney, who stays as backup), Go Raw (Robert Freeland, founder; stage 1 had the brand manager), Seed + Mill (Rachel Simons, CEO and co-founder), Reelie (Juan Pablo Guzman, CEO, snippet only; stage 1 had the 2021 marketing director), OOSO (Oliver Spring, CEO; Sophia Racciatti moves to marketing), GoMacro (Jola Sonkin, CEO and co-founder). Surnames filled: LesserEvil (Charles Coristine), Sweet Loren's (Loren Castle), Effie's (Joan MacIsaac, Irene Costello), GoMacro (Jola Sonkin), Raaka.

**Moved out of the marketing slot:** BjornQorn (Jamie O'Shea is a co-founder), Explorer Cold Brew (Matt Adams is COO), Nantucket Crisps (Paul Nardone is CEO), Cirrus 9 (Makenna is co-founder, tech). Bruce Cost: the 2017 marketing director is replaced by the parent company's current brand marketing manager (brand link unverified).

## Things stage 3 and the founder must know

1. **Same person under two brands.** Horin Yip is the marketing row for Moshi (rank 32) and Bruce Cost Ginger Ale (rank 57); both are made by Brooklyn Food and Beverage (BevNET 2020, search summary). Treat the two brands as one company for "one contact in flight". Caitlin Mack is the marketing row for both PRETZELIZED (rank 9, snippet: joined about two months ago) and LesserEvil (rank 44, Snack and Bakery 2025). Confirm which brand she is at before either is contacted.
2. **Stale sources.** These marketing rows rest on a The Org page last updated more than a year ago, with no newer confirmation: Simply Gum (Jeannie Kim, 2024-10; also a 2022 article), Raaka (William Mullan, 2024-10), Biena (Samantha Sieloff, 2024-11), Solely (Manish Amin, 2024-11). Mavericks (Tina Pate, 2022) and Reelie (Juan Nino, 2021) are older still.
3. **Revenue found while researching contacts (stage 1 has `revenue_band = unknown`):** LesserEvil sales $169M in 2024 and $225M projected for 2025 (Snack and Bakery, 2025 Snack Producer of the Year, opened). Sweet Loren's: CNBC headline on the brand's own press page, 2025-02-18, "set to bring in $120 million this year". Both are far over the $10M ceiling in the brief.
4. **Sweet Loren's** calls itself "America's #1 natural refrigerated dough brand"; the gated SKU is its shelf-stable breakfast biscuits. Fine for the gate, but the pitch should name that SKU.
5. **Unhinged HQ conflict.** A Newport Beach business directory (search summary, 403) lists Always Unhinged, Inc. in Orange County; the table says New York.
6. **Gigantic HQ** is unknown in the table; its press page calls the founder a lifelong New Yorker. Not enough to set New York.
7. **Goody's Granola** has no named person anywhere found. Channel falls back to the brand's contact form.
8. LinkedIn URLs come from search results, the brand's own site (B-SIDES), Startup CPG pages and podcast episode links, and The Kara Goldin Show pages. None was opened.

## Running log

- Verification pass: 70 existing contacts re-opened, 64 confirmed on the stage-1 page, 3 blocked (429/403) and re-sourced, 3 had no URL (snippet rows).
- The Org pass, first slugs: 26 brands matched by domain (6 more slugs hit a different company with the same name and were discarded), 22 with named positions; a second slug pass matched 13 more pages (Fine & Raw, Zack's Mighty, Ella's Flats, Stiller's, Hella, FitJoy, Jack & Friends, Brooklyn Food and Beverage, Biena Snacks, Green Park Brands, Sweet Loren's, Maxine's, BCGA Concept Corp), 11 with named positions.
- Site pass: 60 homepages and about/team pages read; found Seed + Mill's CEO, Sweet Loren's surname, Goodio's founder title, Elements' second co-founder, B-SIDES' LinkedIn link.
- Podcast pass: 15 LinkedIn URLs on contact rows come from Startup CPG feed episode links and Kara Goldin pages (2 of them already known in stage 1); one more from the Startup CPG chip-brands page (Nantucket) and one from the B-SIDES homepage.
- Search pass: 37 queries; useful for Harken (VP Marketing, snippet), LesserEvil (VP Marketing), Sweet Loren's, Treat House, Gigantic, Raaka, Effie's, Firehook, Matzo Project (spokeswoman), Reelie (CEO, snippet), Unhinged (co-founder, snippet). The rest returned nothing usable.
- Cache: all pages gzipped (`_work/fetch/contacts_b1/`, 27 MB, README there).
- Self-check: every `opened` row (114) was re-matched to its cached source page by first and last name; one mismatch (Eleni's spelling) was fixed by pointing the row at The Org page.
