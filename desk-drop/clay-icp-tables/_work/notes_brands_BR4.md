# BR4 notes: New York-first brand sweep (all categories)

Slice: BR4. Output: `clay-icp-tables/_work/brands_BR4.csv` (59 rows, 41 columns, header as specified).
Research date: 2026-10-23 (`found_date` is 2026-10-23 on every row, as the task fixed it; the system clock rolled to 2026-10-24 near the end of the run).
Read-only research. Nothing was sent, posted or signed up for. No connector tools were used and no git writes were made.

## Counts

| Measure | Count |
| --- | --- |
| Rows | 59 |
| HQ in NYC (5 boroughs, as sourced) | 36 |
| HQ elsewhere in New York State | 8 |
| HQ elsewhere in the Northeast (NJ, CT, MA, PA) | 11 |
| HQ not confirmed on any page opened | 4 (Brooklyn Biltong, Simply Gum, Hella Cocktail Co., Graza) |
| Pass the category gates (`excluded = N`) | 40 (21 of them NYC-based) |
| Excluded (`excluded = Y`), recorded so the gate is visible | 19 |
| `founder_review = Y` | 40 (38 of the 40 that pass the gates) |
| `health_claim_flag = Y` | 7 |
| `startup_cpg_member = Y` (public Startup CPG page opened) | 31 |
| Dated why-now inside the 12-month window | 33 |
| `revenue_band` set (sales-volume quote) | 2 (KEANU, Unrefined Foods, both `under-500k`); 57 `unknown` |

Nearest-retailer grade: `store_selector` 23, `brand_claim` 2, `unverified` 34. Among the 40 rows that pass the gates: 19, 2 and 19.

Excluded reasons: needs preparation (4), frozen (3), alcohol (3), refrigerated or fresh (3), explicit health or structure-function wording (4: Brami, Chlorophyll Water, Journée, Bear's Fruit), dietary supplement (1), cocktail mixer (1).

**The goal was not fully met.** There are 59 rows, but only 40 pass the category gates. Of those, Pip's, RISE, Graza, Tate's and Hu are probably above the $10M ceiling. That leaves about 35 rows close to the paying-customer profile, short of the 50 asked for. Two things caused the shortfall. The shared WebSearch budget ran out early (see Dead ends). The three category slices were also recording the obvious New York names at the same time: ten brands I had already researched were taken before my row landed, and about fifteen more were already recorded when I checked.

## Method

1. A helper script normalises brand names and website domains and checks all `brands_*.csv` files before every batch. Rows are appended in small batches with Python's `csv` module. Ten brands I had begun were already in BR1, BR2 or BR3 and were skipped: Hal's New York, Raaka, Fine & Raw, Nantucket Crisps, KIND, CHUH Matcha, RIND, Taza, Grady's Cold Brew and Little Latke. Several more were caught at the check stage: Greyston, Fruition, Beyond Good, Elements Truffles, Knipschildt, Jonesbar, By the Way, Red Jacket, Superseedz, Elmhurst, Mezcla, Solely, Peeled, Mast and Jacques Torres. A final pass found no overlap between BR4 and the other slices.
2. **Whole Foods store-scoped catalog.** The WFM site's own search endpoint, `https://www.wholefoodsmarket.com/api/search?text=<q>&store=<code>`, returns only what that store lists. I confirmed it is store-scoped: Stiller's Soda appears at the cluster stores and is absent at Venice, CA (10333). Cluster store codes: NoMad 10773 (63 Madison Ave), Union Square 10162 (4 Union Sq S), Chelsea 10131 (250 7th Ave) and Manhattan West 10713 (368 10th Ave). Bryant Park (10578, 1095 6th Ave at 42nd St) is outside the 4th to 40th Street band and was not used. Each hit is graded `store_selector`. **A catalog listing is not proof the product is on the shelf today.**
3. **WFM local and new sets.** The same endpoint takes `&featured=local` and `&featured=new` ("Latest & Greatest"), and each result carries an `isLocal` flag. I swept snack and drink terms at Union Square, NoMad, Chelsea, Manhattan West, Williamsburg (10487), Harlem, Bowery and Tribeca to build the "Whole Foods local set" list. When the WFM "new" tag is the only why-now signal, `why_now_date` is the date I observed it (2026-10-23), not a launch date (Taza; it was taken by BR2 before my row landed).
4. **Brand store locators.** I queried the Stockist public API (`stockist.co/api/v1/<tag>/locations/search`) and the Storemapper API (`storemapper.co/api/users/<id>/stores.js`) around Flatiron. I kept Manhattan ZIP codes and projected each store onto the street grid (calibrated on 5th Ave at 14th and 34th Streets), keeping 4th to 40th Street only. These are graded `brand_claim`. Used for Stiller's Soda (map_63vzj673) and B-SIDES (map_g3yz85zq); Raaka (Storemapper 1035) went to BR2.
5. **Startup CPG public pages.** startupcpg.com runs WordPress, and its own REST API (`/wp-json/wp/v2/posts`) returned all 391 posts since 2025-10-23. I filtered press-release datelines for NY, NJ, CT, PA, MA and ME. Newswire releases, the 2026 Shelfie finalists page, the Summer Fancy Food 2026 pavilion page and the "Chipsplosion" roundup count as public participation pages for `startup_cpg_member = Y`. `why_now_date` for these rows is the post's publish date. The Slack is not public and was not used.
6. **Pearl River Mart.** The store's own Shopify catalog (`pearlriver.com/products.json`) gave AAPI snack vendors and their maker notes ("Based in NYC", "Queens, NY", "Brooklyn, NY"). Pearl River Mart Foods is in Chelsea Market (75 9th Ave). The online listing does not show what the Chelsea store stocks, so those rows are graded `unverified`.
7. **Brand sites.** I read about, FAQ, storage and contact pages for HQ, founders, shelf life, pack format and claims. Shopify `products.json` gave launch dates where needed (Graza's chips were published 2026-05-13; RIND's legacy SKUs show as unavailable).
8. **Geocoding.** `_shared/geocode.py` was not needed. No brand row carries a building address that needs a BBL, and retailer coordinates came from the locator APIs.

## Field conventions and assumptions

1. `store_selector` comes only from the WFM store-scoped endpoint for a named store code. `brand_claim` comes from a brand's own locator, or from its own press release naming a store and street (UMAMI GRANOLA at Pearl River Mart Foods, Chelsea Market). Anything else is `unverified`. No row uses `seen_on_shelf`.
2. `nearest_stocked_retailer` prefers the nearest `store_selector` store over a nearer `brand_claim` store, because the evidence is stronger. Stiller's Soda: Fairway at 55 W 25th St is nearer but only a brand claim.
3. `revenue_band` is `unknown` unless a sales figure or sales-volume quote exists. Store counts, funding and launch timing went into `revenue_basis` only. Nine rows first written as `under-500k` from launch timing were corrected to `unknown` before finishing.
4. Website wording such as "detox", "supports digestion", "gut health" or "cognitive wellness" sets `health_claim_flag = Y` and `excluded = Y`. Where the wording was seen only on the website, not on the pack, `founder_review = Y` asks the founder to check the pack.
5. Contacts are business only: names and titles from brand pages or press releases, with the URL of that page. No emails, phones or guessed addresses. Press-release contacts whose role is not stated are named in `notes`, not as founder or marketing lead.
6. `hq_city` says where the location comes from (address, dateline or brand wording) and adds "unverified" or "founder to confirm" when it rests on a dateline or a search snippet.

## Sources that worked

- Whole Foods Market store pages and the store-scoped catalog API (wholefoodsmarket.com).
- Startup CPG Newswire and features via the WordPress REST API (startupcpg.com).
- Pearl River Mart Shopify catalog (pearlriver.com).
- Stockist and Storemapper locator APIs.
- Brand websites, including about pages, FAQs, locators and products.json.
- Trade press opened directly: Beverage Industry (Stiller's Shirley Cola, 2026-03-30), Food Dive press release (Pip's rebrand, 2025-10-07), FoodNavigator (Solely, 2025-12-02, used for checking only), Bakery & Snacks (Startup CPG Pitch II, 2020).
- Whole Foods newsroom (Williamsburg Daily Shop local brands) and a WFM supplier story (Rule Breaker, which went to BR2).

## Dead ends

- **WebSearch budget.** After about a dozen searches the shared 200-per-turn WebSearch limit was used up. I did not work around it: no search engines through curl and no reader or proxy services. Everything afterwards came from sites opened directly and from the sites' own catalog and search endpoints.
- NOSH, BevNET and QSR Magazine return 403 (Cloudflare) to both WebFetch and curl. Facts seen only in their headlines or snippets are marked "unverified, founder to confirm": the Stiller's co-founder, the Katz's Deli deal and the BevNET Live NYC Showdown semifinalists.
- Pop Up Grocer's site is offline ("store unavailable", HTTP 402), so its emerging-brand assortment could not be read.
- These locators are not machine-readable: Roseperl (Rule Breaker, Brooklyn Biltong), Destini (Pip's), Secomapp (Simply Gum, Unhinged), Hal's static list, and RISE's Storemapper id 18418, which returned no data.
- Brand sites unreachable or unhelpful: dayoutsnacks.com (proxy 502), drinkyate.com (403 to curl; WebFetch worked), and undercoversnacks.com and therylco.com (503). Mezcla.com is a parked domain.
- Not reached, so these remain gaps: Wegmans Astor Place (app needs a session), Eataly Flatiron's local set (catalog is mostly imports), Summer Fancy Food Show exhibitor directory, sofi winners list on specialtyfood.com (page rendered without the list), Brooklyn FoodWorks, Hot Bread Kitchen and Entrepreneur Space alumni lists, Eater NY, Time Out and Grub Street roundups, LinkedIn, Instagram and Crunchbase.

## Gaps

1. Revenue is unknown for 57 of 59 rows. No press quote of sales was found for any brand that passes the gates.
2. Contacts: founder names on 42 rows, but full names are missing on some (RISE, Bear's Fruit, Simply Gum and Sol Cacao give first names or surnames only). Marketing leads on only 2 rows (Pip's, The Matzo Project). No LinkedIn profile URLs were collected (LinkedIn blocks bots and search was unavailable).
3. 19 rows that pass the gates have no retailer between 4th and 40th Street beyond `unverified`. Most are online-only or have locators that could not be read. Target's Manhattan stores (relevant for Häppy Candy and Day Out Snacks) were not checked.
4. Shelf life is `unknown` or inferred from ambient retail on most rows. Only a few state a figure: Pip's (8 to 12 months), Brooklyn Biltong (12 months), Brothers All Natural (1 year or longer), RISE and The Purple Drop ("shelf stable"). The 60-day test needs the founder or the brand.
5. Single-serve format is unconfirmed for the granola brands and Z Crackers (share-size bags and boxes).

## Spot-check (required, five rows at random)

Rows were chosen with `random.seed(20261023)`, and each source was re-opened on 2026-10-23:

| Row | Brand | Re-checked | Result |
| --- | --- | --- | --- |
| 16 | The Purple Drop | Startup CPG release: dateline "DANBURY, CT (JULY 2026)", "shelf-stable can", "Maria Velasquez, Co-Founder" | Pass |
| 49 | Small Town Cultures | Release: "PLATTSBURGH, NY (JUNE 2026)", "Cori Deans, founder", "living fermented", "support gut health" | Pass. The exclusion stands; the post's URL slug is mislabelled (WIPS), as noted in the row |
| 12 | The Lucky Ox | About page "Born in NYC"; WFM lists the brand at all four cluster stores | Pass |
| 34 | Nomi Crunch | Homepage "crafted in nyc", "50g of protein per bag"; Pearl River listing "Born in New York City... founder Sarah Harasaki" | Pass |
| 22 | Pitara Co. | Release dateline "NEW YORK, NY (NOVEMBER 2025)", "founder Aditi Luthra", "four signature coffee blends" | Pass |

Result: 5 of 5 rows confirmed, 0 field errors, no changes needed. Separately, during the final review I corrected 9 `revenue_band` values to `unknown`, replaced 3 source URLs I had not opened (Brami funding, Quincy locations, a guessed B-SIDES Startup CPG slug), and reworded Stiller's `hq_city` to cite only pages that were opened.
