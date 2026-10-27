# BR3 notes: shelf-stable beverages

Slice: sparkling water and craft soda, RTD tea, shelf-stable juice and coconut water, RTD coffee, other non-alcoholic drinks.
Researcher: BR3. Research date: 2026-10-23 (every `found_date` is 2026-10-23).
Output: `clay-icp-tables/_work/brands_BR3.csv`, 79 rows, header exactly as specified.

## Counts

| Measure | Count |
| --- | --- |
| Rows recorded | 79 |
| Excluded (`excluded=Y`) | 19 |
| Not excluded | 60 |
| `founder_review=Y` | 63 (nearly every live row has at least one open question) |
| `health_claim_flag=Y` | 19 |
| HQ in New York State (`hq_state=NY`) | 21 |
| HQ in New York City (Manhattan, Brooklyn or Queens, as stated by the brand or press) | 16 |
| HQ unknown | 47 |
| `startup_cpg_member=Y` (Shelfie Award pages) | 7 |
| Rows naming at least one store between 4th and 40th St | 13 |

Retailer grade (`nearest_retailer_grade`), all rows: `brand_claim` 13, `store_selector` 10, `unverified` 56. Not-excluded rows: `brand_claim` 10, `store_selector` 8, `unverified` 42. No row uses `seen_on_shelf`.

Categories: sparkling-soda 27, tea-juice 20, other-drink 18, coffee-rtd 14.

### How many really fit

60 rows pass the exclusion gates. About 19 of those are weak fits and should probably not get outreach:
- Heritage or large brands: Manhattan Special, Boylan, Avery's, Foxon Park, Hank's, Harney & Sons, Steaz, Vita Coco, JUST Water, Death Wish, and Hal's (owned by a distributor).
- No buy path, or dormant: Brooklyn Crafted (no online store found), Halmi (drink sold out), Maine Root (Buy Online link returns 404).
- Probably fails a gate: Red Jacket (cold-pressed juice, likely refrigerated), COUP'd and Tilden (multi-serve bottles).
- Too little information: MODA (no buy path yet) and Lantern (nothing readable on the brand site).

That leaves about 41 plausible prospects, short of the 55 target. The shortfall is mostly a search-budget problem (see the dead ends below), not a lack of candidates.

Best leads, meaning not excluded, a named store inside or near the cluster, and a dated why-now:
- OOZ Birch Water: Fairway Chelsea, TMPL Madison and Pearl River Mart; shelf-stable; NYC-heavy footprint.
- COAQUA: Westside Market W 23rd St, D'Agostino and Gristedes; Pop Up Grocer flagship 2026-07.
- Moshi (Brooklyn Food & Beverage, NYC): Westside Market 3rd Ave, H Mart W 32nd St, Merci Market; DAN DA DAN collab 2026-09.
- Sunbear: Tompkins Square Bagels at 23 E 17th St, inside the cluster.
- St. Agrestis Phony Negroni (Greenpoint): Eataly Flatiron, but the locator mixes NA and alcoholic SKUs.
- Hoplark: Wegmans Astor Place.
- Bruce Cost Ginger Ale: Pearl River Mart, 75 9th Ave.
- Irving Farm (flagship cafe at 71 Irving Place): new shelf-stable cold brew cans 2026-04.
- Wandering Bear (NYC): Target national 2026-08; already sells B2B office subscriptions.

Two strong NYC footprints are excluded on one line of copy each. The founder may reinstate them if the card and landing page avoid the claim:
- WAVA Water (Brooklyn): '100 mg l-theanine for increased focus'.
- Pari: FAQ says agave is 'great for brain function and metabolism'.

## Sources and methods

1. **Brand sites, read with curl.** The useful pages were about, story, FAQ, locator and shop. Shopify `products.json` gave each product's publish date, which is the basis for most why-now dates. Rows say "Shopify publish date" in notes when that is the case. It is the date a product appeared in the brand's own store, not a press date.
2. **Store locators, through their public JSON endpoints.** Only the near-cluster points (roughly 4th to 40th St) were copied into `nyc_retailers_near_cluster`. These are graded `brand_claim`.
   - Stockist (`stockist.co/api/v1/<tag>/locations/search`): St. Agrestis, COAQUA, WAVA, Pari, Sunbear, Tilden, Brause, Fruitbelt, Little Green Cyclo, Esprizio, Freedom Fluid.
   - Storepoint (`api.storepoint.co/v1/<id>/locations`): Bruce Cost, Moshi, Hoplark, Corpse Reviver.
   - OOZ's theme `stockists.json` file.
   - JONI's closeBy page text.
3. **Pop Up Grocer directory** (popupgrocer.com/products/<brand>). All 998 public entries were scraped. Each entry gives the brand site, a one-line description, a category, and availability: "NYC Flagship" (carried now) or "Past Brands". The flagship is at 205 Bleecker St, which is outside the 4th to 40th St band.
   - Where it is the nearest known store, the grade is `store_selector`, because the retailer's own site names its store. Every such row also says "brand-level listing": the directory names the brand, not a SKU. Workstream A may downgrade these to `brand_claim` if it reads the contract strictly.
4. **Startup CPG public pages.** Sources were the Shelfie Awards 2026 finalists (2026-08-06) and winners (2026-08-24), and the 2025 winners (2025-09-03). Participation in these awards is the basis for `startup_cpg_member=Y` (7 rows).
5. **Trade press, opened directly:**
   - Food Business News (Sanzo Series A).
   - FoodNavigator-USA (Wandering Bear Series A).
   - Beverage Business Insights archive teaser (Wandering Bear at Target, 2026-08-11).
   - foodindustryexecutive.com (sofi 2026 finalists).
   - Edible Brooklyn (Brooklyn Crafted).
   - Natural Products Expo West 2026 exhibitor page (Brooklyn Food & Beverage and Moshi, via WebFetch).
   - Summer Fancy Food Show 2026 exhibitor list (GoodMood Kombucha, via WebFetch).
6. **Target.com product page** (WebFetch) for Wandering Bear's shelf-stable statement.

Rules applied:
- Revenue is `unknown` on every row, because no row had a sourced sales figure. No band was inferred from store counts or funding.
- Contacts are founder names as printed on brand sites. First names only where the site gives only a first name. No emails or phones were collected.
- Facts seen only in search snippets are marked "unverified, founder to confirm" in the field or in notes. Examples: Wandering Bear's CEO title, Halmi's founder, Boylan's CEO, Hal's brand lead, Red Jacket's sofi Gold.

## Exclusion calls (CONTRACTS section 4)

- **Cannabis or hemp:** Recess.
- **Structure or function wording:**
  - Asarasi and Sap! (gut health, immunity).
  - Superfrau ('good for gut health').
  - Moment, Curious Elixirs and Ghia (adaptogens: calm, mood, immunity).
  - Phocus and WAVA (L-theanine 'focus').
  - Corpse Reviver (zinc 'to support immunity').
  - Lemon Perfect (vitamin C 'for immune support').
  - Twrl (antioxidants 'support health', 'improved focus').
  - Pari (agave 'great for brain function and metabolism').
- **Supplement-style:**
  - Proper Wild: energy shots with asterisked claims, plus a multivitamin.
  - Zest Tea: creatine powders and gut or immunity blends.
  - JAS: ashwagandha and lion's mane. The exclusion is ingredient-based, so this row also carries founder_review.
- **Refrigerated:** GoodMood Kombucha, Mía, Grady's Cold Brew. Grady's is also a concentrate that needs preparation.

Borderline calls left as `founder_review` rather than excluded:
- Protein or nutrient-content claims: Slate, Elmhurst, Wandering Bear lattes.
- Caffeine-heavy products: Death Wish, Steaz.
- NA beer-adjacent: Hoplark, Brause.
- Wine-adjacent: Good Twin, JONI.
- Cocktail-style NA drinks: St. Agrestis, Mingle, Spirited, Luba.
- Soft wellness copy: Halmi, OOZ, Banagua, Purple Drop (BR4 row), Ample, Taply, Sunbear.

## Dead ends

- **The WebSearch budget ran out** about a quarter of the way through. The limit is 200 searches per turn, shared by all agents. After that, I used no search engines, by any route. Candidates came from my own brand knowledge (domains opened directly), the Pop Up Grocer directory, and Startup CPG award pages. This is the main reason HQ is `unknown` on 47 rows and founders are thin.
- **Target store-level stock** is blocked by PerimeterX bot protection. I did not try to get around it. target.com product pages opened through WebFetch show online listings only, never stock at a named store.
- **Whole Foods and Wegmans** product pages are script-rendered and have no store context, so they could not give a `store_selector` grade.
- **BevNET and NOSH** return 403 to both curl and WebFetch. **Nombase** also returns 403. **Beverage Business Insights** archives need a login beyond the teaser.
- **Locators with no public JSON**, so not read:
  - GoToAisle: Sanzo, Boylan, Mingle, Slate, Vita Coco, Death Wish, Steaz, Pop & Bottle, Beekeeper.
  - Destini: Nixie, Elmhurst, Banagua, Saint James, Bubbl'r.
  - VTInfo: Tost, Good Twin. The iframe refuses requests that do not come from the brand's page; I did not spoof headers.
  - storelocators.com: Wandering Bear.
  - Storemapper: Grady's, Proper Wild.
  - Dathic: Explorer.
  - Wix: Lantern.
- **Dead or redirected sites, not recorded:**
  - minnatea.com returns 502, and drinkminna.com is an expired Squarespace site.
  - drinksweetreason.com is now an unrelated blog.
  - drinkgorgie.com redirects to icalm.com, a supplement.
  - spylt.com is behind a password page.
  - uglydrinks.com and toromatcha.com are spam domains.
  - drinktaika.com, upmountainswitchel.com, gusdrinks.com, mayawell.com and capteli.com fail to connect.
  - Inko's has relocated to Chicago and lists no products.
  - matchako.com returns 404, drinkfauxmo.com returns 402, and drinkspicycoffee.com returns 402.
- **Checked and skipped (low fit, not recorded):**
  - Heritage sodas: Yacht Club (RI), Kutztown (PA), Saranac (brewery soda).
  - Small or remote: Freedom Fluid (no NYC stockists), Sidekick (New Zealand), Bollygood (newest products 2023), Soulstice (no products listed), MyMuse, Anew, AMASS (also makes gin), Yerba Madre (large), Aura Bora (no HQ or retail found).
  - Already in other slices: RISE Brewing, Shinzo Matcha, The Purple Drop, Stiller's Soda (BR4 has them).

## Gaps for the founder

1. HQ city is unknown on 47 rows. Many brands have NYC-heavy locators but do not state an address, for example COAQUA, OOZ, Sunbear and Pari.
2. Shelf stability is stated by the brand on only 15 of the 60 live rows. The rest are cans or bottles with no statement, so ask Q1 on the call.
3. No revenue figures at all. No marketing-lead names except Hal's (unverified) and Explorer's COO.
4. Only 13 rows name a store inside the band, and none is `store_selector` inside the band. Brand locators can be checked on foot later as `seen_on_shelf`.
5. The why-now signal is a Shopify publish date or a Pop Up Grocer directory date on most rows. These are real dated signals, but they are weaker than press.

## Spot check (re-opened 2026-10-23, 5 rows chosen at random, seed 20261023)

| Row | Fields re-checked | Result |
| --- | --- | --- |
| Nixie Sparkling Water | founder 'Nicole' on about page; Strawberry Cream and Cherry Cola published 2026-02-25 | confirmed |
| Death Wish Coffee | HQ Saratoga Springs (about); founder Mike Brown; Caramel Cold Brew Latte published 2026-04-03 | confirmed |
| Maine Root | fair trade copy on our-roots; Buy Online link 404 | confirmed |
| Tilden | FAQ '18 months unopened'; founder Mariah; Stockist 8 points, restaurants | confirmed; founder upgraded to full name 'Mariah Hilton Wood' from the same page |
| JONI | Big Night West Village, 236 W 10th St on find-joni; listed as a Shelfie 2026 Non-Alcoholic finalist | confirmed |

Result: no field was wrong; one field was made more complete. Earlier self-review fixes, made before the spot check:
- Removed HQ values I had from memory or from search snippets only: Red Jacket (city), Avery's (state), Maine Root (state), Elmhurst (state), Manhattan Special (city and state), Halmi (city and state).
- Moved Rockaway's why-now to notes, because its 2025-08-19 date is outside the 12-month window.
- Corrected GoodMood's and Mía's Pop Up Grocer URLs.
