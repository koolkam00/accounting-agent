# BR3 enrichment: methods and gaps

Input: `brands_BR3.csv` (60 rows with `excluded=N`). Output: `enrich_BR3.csv`, 264 rows, one row per changed field. Research date: 2026-10-24. `brands_BR3.csv` was not edited.

## How to read `enrich_BR3.csv`

- `old_value` is copied from `brands_BR3.csv`. `new_value` replaces it.
- For `notes` and `founder_review_reason`, `new_value` is the full new text: the old value plus "Added 2026-10-24: ...".
- `confidence=opened`: I opened the source URL myself (curl GET or WebFetch) on 2026-10-24.
- `confidence=snippet-unverified`: the fact came from a search snippet only, and the value says "unverified, founder to confirm". There are 20 such rows. Opened values always replace snippet values where both exist.
- Each brand and field pair appears only once.

## Counts

- Brands enriched: 55 of 60 live rows. No new facts were found for Foxon Park, Maine Root, Death Wish, Little Green Cyclo and Lantern.
- Rows by field group:
  - HQ: 68 rows across 39 brands.
  - Founder name, title or profile: 73 rows across 32 brands.
  - Marketing lead: 39 rows across 18 brands.
  - Shelf life: 18 rows across 9 brands.
  - Why-now: 35 rows across 13 brands.
  - Startup CPG: 6 rows across 3 brands.
  - Revenue: 8 rows across 6 brands.
  - Other (funding, notes, review reasons, one exclusion): 17 rows.
- WebSearch calls: 57 of the roughly 95 allowed. Most facts came from free GET requests.

## Methods, cheapest first

1. **Shopify policy pages** (`/policies/privacy-policy`, `terms-of-service`, `refund-policy`, `contact-information`) and `/pages/contact`. These gave the business address for about 40 brands.
   - Registered-agent addresses do not count as HQ: OOZ and Sunbear (Albany), and Neat Soda (Dover, DE).
   - Where a street address looked residential, I recorded only the city and state.
2. **About, story, team, FAQ and press pages, plus `products.json`.** These gave founder names, and shelf-life statements for Boylan, JUST, Vita Coco, Luba, nero, Pop & Bottle, Nixie and COUP'd.
3. **Startup CPG sitemap, Newswire posts and podcast RSS feed.** These gave the Startup CPG flag for Hoplark, Luba and CHUH, why-now signals for Banagua, Luba, CHUH and Laurel's, and Hoplark's marketing lead.
4. **Natural Products Expo West 2026 exhibitor directory** (Swapcard). Its GET search returns server-rendered results, and each exhibitor page lists staff with job titles. This gave current marketing contacts for:
   - Moshi and Brooklyn Crafted
   - Beekeeper
   - Vita Coco
   - Nixie
   - Elmhurst
   - Saint James
   - Pop & Bottle
   - Kimino
   - Steaz

   Staff profile pages need a login, so they are not used as profile URLs.
5. **WebSearch**, used only on live rows, to find press for why-now signals and full names. I then opened the article wherever the site allowed it.

## Findings that change a row's standing

- **Red Jacket Orchards**: the FAQ says all products must be refrigerated. I recommend `excluded=Y`.
- **St. Agrestis**: The Wine Group bought the Phony Negroni line on 2026-04-29 (acquirer's release, opened). The brand is no longer independent.
- **COAQUA** is based in Ponte Vedra Beach, FL, not NYC.
- **Good Twin** is owned by AMASS, which also sells gin.
- **Harney & Sons** sells CBD bottled teas. Only its non-CBD SKUs could be placed.
- **MODA**: $500k revenue since its 2026 launch, and co-founder Grace Hachigian is based in NYC (Entrepreneur, 2026-10-08).
- **Banagua**: expects a little over $5M in its first year, and raised $5.5M (New Hope, 2026-07-22). Both figures are company quotes; the $5M is a projection.
- **Wandering Bear**: offices were 50 to 60% of its revenue before the pandemic (snippet only). That makes it a strong fit.

## Gaps

- **HQ still unknown (8):** Sunbear, Neat Soda, Pop & Bottle (city), Beekeeper (city), Steaz, Maine Root, Lantern, Red Jacket.
- **Founder missing or first name only:** OOZ and Esprizio (surname unverified), Taply, nero, Neat Soda, COUP'd, Lantern, and the heritage sodas. Some `founder_title` cells still say "first name only" and need cleanup after a surname is added.
- **No marketing lead (41 live rows).** Most small brands are founder-run, so the founder is the contact.
- **No public profile URLs** were found for marketing leads, and no LinkedIn URLs were collected. I did not guess any.
- **Shelf life still unstated (37 live rows),** mostly canned sodas. Ask Q1 on the call.
- **No why-now in the last 12 months (14):** Sanzo, Rockaway, Sunbear, KACE, Halmi, Tilden, plus heritage and large brands.
- **Startup CPG:** flag is Y on 10 rows (7 from BR3, 3 new). The rest stay unknown, not N.
- **Revenue:** a sourced press figure exists only for MODA and Banagua (projection). The Good Twin parent figure and the Wandering Bear aggregator estimate are unverified, so `revenue_band` stays unknown for both.
- **Blocked sources:** BevNET, Brewbound, Nombase, Faire, Progressive Grocer and Wine Industry Advisor return 403. The University of Richmond page for Tranquila returned 503 and a TLS error. Press seen only through these is marked snippet-unverified.
