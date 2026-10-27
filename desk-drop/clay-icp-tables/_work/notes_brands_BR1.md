# BR1 notes: savory snacks brand prospects

Slice: chips and crisps, popcorn and puffs, crackers and pretzels, shelf-stable meat snacks, nuts, seeds and trail mix.
File: `clay-icp-tables/_work/brands_BR1.csv` (64 rows). Researched 2026-10-23 into the early hours of 2026-10-24. Every row carries `found_date` 2026-10-23, as the task asked.

## Counts

| Measure | Count |
| --- | --- |
| Rows | 64 |
| HQ in New York State | 8 (NYC 4: Strip Jerky, Cob, Zack's Mighty [Brooklyn, unverified], Kings County Jerky [excluded]; rest of the state 4: BjornQorn, Eccentric Bagel Chips, Tierra Farm, BobbySue's Nuts) |
| HQ elsewhere in the Northeast (NJ, CT, PA, MA, VT, ME, NH) | 12 |
| HQ unknown | 19 |
| excluded = Y | 4 (Cob, MASA Chips and Unbothered Foods on health-claim wording; Kings County Jerky on no working store) |
| founder_review = Y | 41 |
| Clean rows (not excluded, no founder review) | 21 |
| nearest_retailer_grade = store_selector | 46 (31 at a cluster Whole Foods, 15 at PopUp Grocer, which sits just outside the band) |
| nearest_retailer_grade = brand_claim | 1 (Veggie Vice at 38 E 23rd St) |
| nearest_retailer_grade = unverified | 17 |
| Rows with a dated why_now | 46 |
| startup_cpg_member = Y | 14 |
| revenue_band set | 1 (WILDE over-10m, from trade press: "surpassed $100 million in sales") |
| Founder name found | 43 |
| Marketing or other second contact found | 10 |

Categories: chips-crisps 20, crackers-pretzels 15, meat-snacks 11, nuts-seeds-trail 7, popcorn-puffs 6, other-snack 5 (lupini-style legume, chickpea and edamame, roasted corn, crunchy macaroni, snack mix).

## Sources and methods

1. **Whole Foods store-context check (main retailer evidence).** The WFM site keeps the shopper's store in a cookie, `wfm_store_d8`, holding base64 JSON `{"id": "<store code>"}`. With that cookie, `https://www.wholefoodsmarket.com/search?text=<brand>` returns that store's assortment, with `availability` set to IN_STOCK. Store codes, read from each store page on wholefoodsmarket.com:
   - Union Square, 4 Union Sq S: 10162
   - NoMad, 63 Madison Ave: 10773
   - Chelsea, 250 7th Ave: 10131
   - also found but not used: Manhattan West, 368 10th Ave (10713); Bryant Park, 1095 6th Ave (10578, at 41st to 42nd St, outside the band); Bowery (10236, south of the band).
   - Negative control: BjornQorn and Kings County Jerky return nothing in the Austin Lamar store context (10145), and the Union Square and Lamar lists differ. The results really are store-specific.
   - Grade: `store_selector`, since the retailer's own site shows the product at that store. The founder can reproduce this by picking the store on wholefoodsmarket.com and searching. Caveat: this is the store's pickup and delivery assortment. A shelf check would confirm the physical facing (`seen_on_shelf`, founder only).
   - The first wide scan ran category searches ("potato chips", "popcorn", "crackers", "jerky" and so on) in the Union Square context to find candidate brands. Each brand was then re-checked by name in all three stores.
2. **PopUp Grocer directory.** `https://popupgrocer.com/pages/directory` embeds `listingData` for 1,644 brands, each with an availability of "NYC Flagship" or "Past Brands". 283 are at the NYC Flagship, 205 Bleecker St. That store geocodes to lat 40.729658, lon -74.00181 (bbl 1005427501), just south of the 4th-to-40th St band. It is therefore never listed in `nyc_retailers_near_cluster`. When it is the only NYC store found, it appears as `nearest_stocked_retailer` with the note "just south of the 4th-40th St band". The grade is `store_selector`, because the retailer's own site lists the brand at that specific store. Brand websites came from the links on each brand's PopUp Grocer page.
3. **Shopify `products.json`** on brand sites. The `published_at` and `created_at` dates give a dated why_now for new flavors, new snack packs and relaunches. Rows note "date is Shopify published_at" where that is the basis.
4. **Shopify policy pages** (`/policies/contact-information`, privacy, terms, refund) give the business city. Only city and state are recorded, never the street address, because several are likely home addresses.
5. **Startup CPG.** Newswire posts were listed through the site's own WordPress post feed (`startupcpg.com/wp-json/wp/v2/posts`, 600 posts from 2025-04 to 2026-10). The "Chipsplosion: 14 Chip Brands" feature (2026-07-21) was also used. `startup_cpg_member = Y` means the brand has a Startup CPG newswire release or a startupcpg.com feature, or, for Strip Jerky only, the founder names the Startup CPG community as a resource in an Entrepreneur Q&A. It is a participation flag, not a membership list.
6. **Trade press.** Snack Food & Wholesale Bakery topic pages (chips, pretzels, popcorn, puffs, crackers, nuts and seeds, other snacks), with articles opened and dated. Green Queen covered the Brami funding (that row went to BR4 as a duplicate), Entrepreneur covered Strip Jerky, and EcoWatch reposted Modern Farmer on BjornQorn.

## Decisions and conventions

- `individually_packaged`: Y means a single-serve or snack-pack unit was seen. N means only share-size bags or boxes were found. unknown means the pack size was not confirmed.
- `revenue_band` is set only from a published sales figure. Two rows were downgraded to unknown during the build. Strip Jerky's article says "more than $200,000" projected, which could fall on either side of $500k. The Hermit's 500-bag batch is not a sales figure. The basis text stays in `revenue_basis`.
- The health-claim gate was applied to brand-site copy (CONTRACTS section 4): "for Energy, Digestion & Performance" (Cob), tallow fats "have functions for nervous system health, anti-inflammation and anti-bacterial immune function" (MASA Chips), and "Gut-Friendly ... gut benefit" (Unbothered Foods). Where the wording may live only on the website and not on the pack, the row also carries founder_review = Y.
- Nutrient-content claims (protein grams, "Packed with Protein + Fiber", "8g Protein", "Antioxidant Boost") set founder_review = Y, not an exclusion.
- Big-brand or out-of-band signals set founder_review = Y: WILDE (over $100M sales), LesserEvil, Saffron Road (frozen-entree parent), 34 Degrees, Unique Snacks, Chifles, LOVE CORN, Vermont Smoke & Cure (Kraft A.1. and Lea & Perrins licensed sticks), DANG ("at Safe Catch" office).
- Veggie Vice: its homepage lists a store at 38 E 23rd St beside an image file named "Rooted_Logo". The store name "Rooted" is inferred from that file name. Founder to confirm.
- Websites that were guessed and did not respond are marked "unverified, founder to confirm (guessed ... did not respond)": Firehook, The Good Crisp Company, Simply 7, Go Raw, Every Body Eat. Jack & Friends, Louisville Vegan Jerky and Stellar Snacks have website = unknown.

## Dead ends

- **WebSearch budget.** The shared per-turn limit of 200 searches ran out after 15 BR1 searches. From then on there were no search-engine queries. Discovery used retailer catalogs (WFM store search, the PopUp Grocer directory), trade-press listing pages and Startup CPG pages, plus known brand domains.
- NOSH (nosh.com) and BevNET return HTTP 403 behind Cloudflare, so NOSH press releases could not be opened.
- brami.com now resolves to an unrelated Italian site; Brami is at enjoybrami.com. The row went to BR4.
- kingscountyjerky.com returned HTTP 521. kitchentablebakers.com failed with a TLS error. eatenlightened.com did not respond. namssnacks.com gave a proxy 502. elnachochips.com and humblepotatochips.com show "Coming Soon".
- Most store locators (Stockist, effectify, Find a Dealer) render with JavaScript and could not be read with curl. Retailer lists therefore come from brand homepages, trade press, Startup CPG features or WFM.
- Not attempted for lack of time: Wegmans Astor Place (770 Broadway) and Target Herald Square and Kips Bay store-level checks, and Eataly Flatiron. Trader Joe's was skipped as private label only.
- Already recorded by other slices, so skipped here: Pip's Heirloom Snacks (BR4), Brami (BR4), Hal's New York (BR3), North Fork Potato Chips (BR4), WildBoard (BR4, added while BR1 was writing its row).

## Gaps

- HQ unknown for 19 rows. Several more rows carry an unverified city taken from a returns address or a search snippet.
- Marketing lead found for only 10 rows. No LinkedIn profiles were opened (blocked by policy and bots), so profile URLs point to brand or press pages.
- `instagram_url` is filled only where a brand or retailer page linked it (20 rows).
- Revenue is unknown for 63 of 64 rows.
- 17 rows have no retailer evidence near the cluster. Most are online-only or regional, and they need a discount-code buy path to pass the gate.
- Leads not yet researched for a second pass: Kitchen Table Bakers (Syosset NY), Enlightened Bada Bean Bada Boom (Bronx NY), El Nacho (MA), Nams Snacks (Northeast DSD), Keya's Snacks, Green Sahara, Perfectly Crisp (WFM Union Square and NoMad; the WFM URL names "Raison d'Etre Bakery"), Kim's Magic Pop (WFM all three), Mi Niña tortilla chips (WFM all three), Lark Ellen Farm, Purely Sprouted, Miss Kay's Meat Sticks, BeeFree, Croots, Maui Nui, Meet the Source, root foods, Bangkok Bites, Deep River Snacks, Effie's Homemade, Grandy Oats, Bazzini.

## Spot check (5 rows, chosen with Python random.sample, seed 20261023)

| Row | Re-opened | Result |
| --- | --- | --- |
| 34 Degrees | our-story page; WFM search in all three cluster stores | Denver HQ, retailer list and WFM IN_STOCK (6 SKUs per store) confirmed. **Fix:** founder name was "unknown" but the page names Craig Lieberman; added. |
| Reelie (formerly Artisan Tropic) | contact-us, reelie-about-us, products.json, WFM | Charlotte NC office, rename from Artisan Tropic, Serrano Lime product date 2026-03-25 and WFM IN_STOCK confirmed. **Fix:** source_url pointed to /pages/about-us; the matching text now sits on /pages/reelie-about-us, so the URL was updated. |
| Righteous Felon | refund policy, products.json, WFM | Exton PA returns address, variety-pack dates 2026-08-05 and no WFM listing confirmed. No change. |
| Simply 7 | WFM search in all three stores | Sea Salt and Jalapeño 4 oz IN_STOCK confirmed in Union Square, NoMad and Chelsea. No change. |
| LOVE CORN | WFM search, refund policy, Love Story page | WFM IN_STOCK (4, 5 and 3 items) and Middletown PA returns address confirmed. Founders still not on any opened page, so they stay unverified. **Added:** Instagram handle, plus the page's 3-year goal to donate 1 million samples, a strong sampling-budget signal. |

Errors found: 2 of about 40 key fields checked (one omitted founder name, one stale source URL), about 5%. No fabricated field was found.
