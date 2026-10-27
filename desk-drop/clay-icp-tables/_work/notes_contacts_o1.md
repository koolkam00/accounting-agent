# Stage 2 notes: office contacts, ranks 1 to 25

Workstream A, stage 2 of 3, 2026-10-24. Paths are relative to `desk-drop/`. Output: `clay-icp-tables/_work/contacts_o1.csv`.

## Scope

The 25 offices ranked 1 to 25 in `clay-icp-tables/_work/top50_offices.csv`. For each: one primary and one backup contact who works in the New York office, with a title in the target family (Office Manager, Workplace Experience Manager, Head of Workplace, People Operations, Executive Assistant to the CEO) or a variant (Office Coordinator, Workplace Coordinator, Facilities Manager, People and Culture, Office Services, Chief of Staff at small firms).

## Sources, in the order used

1. **Company team pages** (opened with curl GET, generic User-Agent). Best evidence: the employer names the person and title itself.
2. **The Org** (theorg.com), a public org-chart directory edited by companies and users. Each position page carries the current role, a role timeline, the office it is attached to and a last-updated timestamp. Pages opened with curl GET. Titles here can lag reality; the `notes` column gives the page's `updatedAt` date so the founder can judge staleness.
   - The Org's public position sitemaps (`https://cdn.theorg.com/sitemap.xml`, 410 position files, allowed by its robots.txt) were streamed once and filtered to these 25 companies' slugs, so every listed person at each company could be checked, not only the few shown on the company's chart page.
3. **WebSearch** (budget about 60 calls for this slice), for companies where 1 and 2 found nobody in New York with a fitting title.

LinkedIn was never opened. A LinkedIn URL is recorded only when it appeared on a company page or in search results.

## Rules applied

- Business data only: first name, last name, title, a business profile URL, the source and its date. No emails were guessed or constructed. No phone numbers. Nothing about the person beyond the job title. Home-city fields on The Org were read only to judge whether the person works from the New York office and were not stored.
- `confidence = opened` when the title was confirmed on a page opened today (company page or The Org position page). `snippet-unverified, founder to confirm` when seen only in a search snippet.
- "Works in the New York office" is judged from the company page or The Org's office attachment. Where the only signal is weak, `notes` says so.
- Primary is the closest title match who sits in New York; backup is the next best. Where nobody fits, the row says `none found` and the channel falls back to walk-in or a company contact form.

## Flags in `notes` (for stage 3 scoring)

Every found contact's `notes` starts with two machine-readable flags:
- `ny_base=confirmed`: the employer's own page for a New York-HQ firm, or The Org attaches the position to the company's New York office. `ny_base=likely`: The Org places the person in the New York area but attaches no office. `ny_base=unconfirmed`: no location, "United States" only, or the commuting region outside the city.
- `title_fit=family`: Office Manager or office services, Workplace Experience, Head of Workplace, People Operations, Executive Assistant to the CEO. `title_fit=variant`: Workplace or Office Coordinator, people or HR lead, HR business partner, an executive assistant The Org shows reporting to the CEO, chief of staff to the CEO at a small firm, office administrator. `title_fit=adjacent`: an operations lead, or a chief of staff at a larger firm or to someone other than the CEO.
- Suggested scoring (stage 3 decides): `family` or `variant` with `ny_base` confirmed or likely = full title points (10); anything `adjacent` or `ny_base=unconfirmed` = adjacent points (5); `none found` = 0.

People The Org places outside the New York region (Israel, Egypt, Atlanta, Denver, San Francisco) were not used, even with a fitting title.

## Results (2026-10-24)

| Measure | Count |
| --- | --- |
| Offices covered | 25 (ranks 1 to 25), 2 rows each, 50 rows |
| Contacts found | 28: 18 primary, 10 backup |
| Not found | 22 rows: 7 primary (GTS, Aterian, Personetics, Simplebet, Candid Health, accessiBe, Morning Brew), 15 backup |
| Offices with both contacts | 10 (GSG, Cognitiv, K Health, CompStak, Nayya, Stellar Health, Signal AI, 1stDibs, Bombas, BrainPOP) |
| Offices with a primary only | 8 (Empathy, Carbyne, Dashlane, Inspiren, Vita Coco, Butterfly Network, Daily Harvest, Wellcom Worldwide) |
| Offices with no contact | 7 (channel falls back to walk-in or company contact form) |
| Confidence of found contacts | opened 27, snippet-unverified 1 (Vita Coco) |
| `ny_base` of found contacts | confirmed 13, likely 8, unconfirmed 7 |
| `title_fit` of found contacts | family 9, variant 14, adjacent 5 |
| LinkedIn URLs | 1 (GSG backup, linked from the employer's own page). The search tool does not index LinkedIn profiles and declines name lookups, so the rest are blank. |
| Sources | 2 contacts from employer pages (GSG), 2 more confirmed on employer pages (Cognitiv, Carbyne), 23 from The Org position pages, 1 from a search snippet |
| WebSearch calls used | 30 of about 60 |
| Pages opened | about 1,040 The Org pages (981 position pages from the sitemap pass, about 33 position pages and 28 company chart pages read first), 410 sitemap files, about 15 company and job pages |

## Files

- `contacts_o1.csv`: the deliverable.
- `contacts_o1_build.py`: writes the CSV (every row and note is in it, so a fix is one edit and a rerun).
- `contacts_o1_theorg_candidates.csv`: the 116 The Org positions at these 25 companies whose titles touched office, people, HR, admin, operations or chief of staff, with The Org URL, attached office, a New York Y/N and The Org's last-updated date. This is the audit trail for "none found" and for the choices made. Person home cities were not stored.
- `contacts_o1_theorg_raw.jsonl`: the first 33 position pages read from org charts (name, current title, attached office, updated date, URL only).

## Things found that matter beyond contacts (open issues)

1. **Simplebet (AO-C-128)**: search results citing DraftKings' filings say DraftKings completed its acquisition of Simplebet on 2024-12-03 (SEC pages not opened). Company size under 500 and pantry control may be wrong for this row.
2. **Carbyne (AO-C-151)**: carbyne.com carries Axon 911 co-branding (2026-06 image files) and one The Org title reads "Acquired by Axon". Possible parent company: size score and pantry control to recheck.
3. **Empathy (AO-C-085)**: is hiring a New York "Workplace Experience Associate" to own the NYC office experience (posted 2026-10-06, opened). The pantry seat is vacant now; the Head of People is the first contact, and the new hire becomes the primary once named.
4. **K Health (AO-C-160)**: a temporary "Executive Assistant and Office Manager" New York role was posted 2026-09-04 (search snippet) and is gone from the Greenhouse board today; someone new may hold it.
5. **GTS (AO-C-050)**: The Org's "gts" page is an unrelated Egyptian IT firm; do not use it. GTS's own Facilities Manager posting now returns HTTP 410.
6. **Address records on The Org differ from B's** for Empathy (1178 Broadway vs 56 West 22nd Street), Stellar Health (127 West 26th Street vs 215 Park Avenue South), Signal AI (154 W 14th St vs 440 Park Avenue South; 154 W 14th is west of Sixth Avenue, outside the boundary), Carbyne (276 Fifth Avenue vs 45 West 27th Street) and Daily Harvest (1115 Broadway vs 37 West 20th Street). B's addresses come from the companies' own sites or Built In dated 2026-10 and are kept; The Org office records are probably stale. Daily Harvest is already occupancy-unconfirmed.
7. **Stale The Org records**: Bombas primary (updated 2024-11-14), 1stDibs primary (2024-11-24), CompStak backup (2023-02-26), Daily Harvest primary (2024-03-04). Founder to check on LinkedIn before sending.
8. **Truncated surname**: Cognitiv backup "Rebecca Aliab D." as shown on The Org.
9. **Stage 3**: no emails were looked up or guessed. Verified work emails for the top 50 still need the Clay waterfall (founder login and credits).
