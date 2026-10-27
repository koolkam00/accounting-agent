# BR5 notes: sources the first four slices did not reach

Slice: BR5. Output: `clay-icp-tables/_work/brands_BR5.csv` (45 rows, 41 columns, header exactly as specified).
Research date: 2026-10-24. `found_date` is 2026-10-24 and `found_by` is BR5 on every row.
Read-only research. Nothing was sent, posted or signed up for. No connector tools were used and no git writes were made. No personal identifier was put into any request. The default curl User-Agent was replaced with a plain `Mozilla/5.0` string.

## Counts

| Measure | Count |
| --- | --- |
| New brands (rows) | 45 |
| HQ in New York State | 27 |
| HQ in New York City (five boroughs, as sourced) | 20 (Namkeen Queens says only "packaged in New York") |
| HQ elsewhere in the Northeast (MA 5, VT 4, PA 3, NH, ME, CT, NJ) | 16 |
| HQ outside the Northeast (Keya's Snacks VA, Chef Poppin CA) | 2 |
| Excluded (`excluded = Y`) | 7 |
| Pass the category gates (`excluded = N`) | 38, of which 16 are NYC-based |
| `founder_review = Y` | 38 (36 of the 38 that pass; Figa Foods and Doosra are the only clean passes) |
| `health_claim_flag = Y` | 6 |
| `startup_cpg_member = Y` (public Startup CPG page opened) | 10 |
| Dated why-now inside the 12-month window | 42 (Nature's Best Snacks, Caltein and Oso Cacao have none) |
| `revenue_band` set | 0 (no sales figure found for any row) |

Nearest-retailer grade: `store_selector` 2 (Effie's Homemade, Vermont Nut Free Chocolates), `brand_claim` 5 (Gigantic, Figa Foods, Doosra, Caltein, Bixby Chocolate), `unverified` 38. No row uses `seen_on_shelf`.

Exclusions: explicit health or structure-function claims (MALAPOP, DrinkFolks, Freedom Fluid, Chikka Chikka), refrigerated (Junebar, Sourmilk), needs preparation (Cho's Bakeshop). MALAPOP and Freedom Fluid also carry `founder_review = Y`, because the claims were seen on the website, not the pack.

Before writing, every candidate was checked against the 266 brands in `brands_BR1` to `brands_BR4`, by normalized name and website domain. A final pass found no overlap. Brands found here that the other slices already had, and so not added: Fat Witch, Z Crackers, The Matzo Project, GoodMood Kombucha, Red Jacket (Berryfield Bottling), Fruition, Strip Jerky, Jöey, BEEST, Top Seedz, Rule Breaker, Defi Snacks, Goldholly, The Lucky Ox and Brooklyn Crafted (Brooklyn Food & Beverage).

## Method and sources

1. **Summer Fancy Food Show 2026 exhibitor directory.** The directory runs on Swapcard at `events.specialtyfood.com/event/2026-summer-fancy-food-show/exhibitors/RXZlbnRWaWV3XzEyNTgzMTk=`. Its server-rendered page embeds Apollo state (`__NEXT_DATA__`) and honours a `?search=` parameter, which also matches descriptions. About 120 GET searches covered NY and Northeast place names and snack and drink terms. They returned 959 distinct exhibitors, which I filtered for NY and Northeast wording. Each exhibitor detail page (`/exhibitor/<id>`) gives the website, the **State** field, product category, pavilion, "Has a New Product", "In The Fancy Bodega" and brand names. HQ state for SFFS rows comes from that State field, and every exhibitor id in the CSV was checked against the scraped set. Show dates (June 28 to 30, 2026) come from the Startup CPG pavilion post, so SFFS-based why-now rows use 2026-06-28. URL filter parameters (state, category, pavilion) are not applied server-side, so the directory could not be filtered by state directly.
2. **sofi Awards.** SFA's winners page (`specialtyfood.com/awards/sofi-awards/winners/`) lists the 2026 Gold winners and no 2025 year. SFA's own release of the **2027 sofi finalists** is dated 2026-10-19 (`/news-media/news-features/association-press-releases/2027-sofi-awards-finalists/`) and is the freshest why-now in this slice. The 2026 finalist list came from foodindustryexecutive.com (WebFetch; curl got 403). It is dated 2025-10-23, one day outside the 12-month window, so it is used as context only.
3. **Incubators.** Hot Bread Kitchen's Breadwinners Marketplace and HBKi pages. Entrepreneur Space's client list (`entrepreneurspace.org/clients`, a QEDC program). QEDC's Made in Queens maker directory (`madeinqueens.org/products`), which confirms Doosra, Sivaro, Nature's Best Snacks, Oso Cacao and Milène Jardine as Queens makers.
4. **Startup CPG public pages,** read through the site's WordPress REST API (`/wp-json/wp/v2/posts?search=` and `?slug=`). A search hit counted only after the brand name was confirmed in the post text. Pages used: the SFFS 2026 pavilion (2026-06-01), the 2026 Shelfie finalists (2026-08-06), Chipsplosion (2026-07-21), the female-founded beverage feature (2026-03-16) and the 2025 Shelfie finalists.
5. **Trade press opened directly:** Snack Food & Wholesale Bakery on Naturally New York's 2026 Naturally Rising pitch and Next Fairway Find (2026-06-02). It gave the Figa Foods and Keya's Snacks why-nows and the Sourmilk finalist status.
6. **Retail evidence.** The Whole Foods store-scoped catalog API (`/api/search?text=&store=`) at Union Square 10162, NoMad 10773, Chelsea 10131 and Manhattan West 10713. It matched only Effie's and Vermont Nut Free; the other candidates checked (about 25) returned nothing. Stockist locator API calls centred on 5th Ave and 23rd St: Figa `map_9q962p43`, Doosra `u18827`, Gigantic `u19294`, Caltein `map_93ezz7vq`, Bixby `map_93ezwnvq`. Oso Cacao's FAQ lists stockists by name.
7. **Brand sites.** About, FAQ, contact and locator pages, plus Shopify `products.json`. Product `published_at` dates are the why-now dates where no press item exists, and each row says so.

## Field conventions

- `revenue_band` is `unknown` on every row. Store counts (Effie's "4,000+ shops", Keya's "1,800 doors") are written in `revenue_basis` only.
- `store_selector` is used only for the WFM store-scoped catalog. Brand locators are graded `brand_claim`, and everything else is `unverified`. A catalog listing is not proof of stock on the shelf today.
- Contacts are names and titles as printed on brand pages, the SFFS directory or Startup CPG, with that page's URL. Where only first names are published, only first names are given. Two founder attributions rest on Hot Bread Kitchen testimonials (Keesha for Live Loud Foods, Tiffany for DrinkFolks) and are marked "unverified, founder to confirm". The Made in Queens directory shows personal contact emails and phones; none were recorded. No email or phone appears anywhere in the CSV.
- Soft wording such as "healthy snack", "nutrient-rich" or "guilt-free, energy-boosting" sets `founder_review = Y`, not an exclusion. Wording that names a body effect ("boosts metabolism", "immune boosting", "reduces bloating", "supports digestion") sets `excluded = Y`. Upstate Stock's "numerous health benefits" is flagged `health_claim_flag = Y` but left for founder review, because it is generic.

## Dead ends

- **Wegmans Astor Place (770 Broadway, store 156).** Product search runs on Algolia (app `QGPPR19V8V`), and the search key is not in the page; it is issued to a browser session. Not worked around, so no Wegmans grades.
- **Eataly NYC Flatiron.** The Magento GraphQL catalog answers GET queries (`/graphql?query=...`) but holds the online assortment, not a Flatiron store set. Searches for brooklyn, new york, chips, soda, snack, crackers, cookies and bar returned Italian imports, plus one US brand (Hayden Flour Mills, Arizona). No real fit was recorded.
- **Brooklyn FoodWorks.** The domain is parked and redirects to `/lander`.
- **Union Kitchen.** DC only. No NYC program or alumni list was found.
- **PepsiCo Greenhouse.** `greenhouseaccelerator.pepsico.com` was refused by the egress proxy. Search found only the first North American cohort (undated), whose NY brand, Rule Breaker, is already in BR2.
- **Chobani Incubator.** Search found only the 2016 and 2017 classes. Chops Snacks' domain is now a gambling spam page. Cissé Cocoa makes cocoa mixes (preparation). No row was added.
- **Food-X.** `food-x.com` has an expired TLS certificate, and curl refused it. Not bypassed.
- **NYC press roundups.** Grub Street is blocked for the search tool, and Eater NY returned nothing with domain filters. Time Out and Brooklyn Magazine hits were restaurant and bar lists, not packaged-goods roundups. No brand came from press roundups.
- **Unreadable or unusable sites:** Norwegian Baked's Storemapper id returned an empty list. Snackios, Keya's and Live Loud locators are script-rendered. Melville Candy, Brooklyn Bites NY and Venus Brands (mod_security 406) did not load. Shoop Beverages' site has expired. Nom Nom Kone is a placeholder page. supermarketperimeter.com returned 403.
- **Not recorded because they are not packaged CPG:** Desserts Before Dinner and Give & Bake (fresh local bakeries), Sol Kitchen NY (alfajores made to order, 2 to 3 days' notice), Gracie Baked (cheesecake cookie bars, likely perishable), Evanly Bakes (made-to-order), Paktli Foods (HQ and recent activity not confirmed) and Original Sin (mainly hard cider).

## Gaps

1. Revenue is unknown on all 45 rows.
2. Only 7 rows have a graded retailer near the cluster. Most brands are online-only for Manhattan or have locators that could not be read.
3. Founders are missing or first-name-only on about half the rows. Only Cirrus 9 has a second named contact, and it is an operations role, not marketing. No LinkedIn URLs were collected; LinkedIn was not used.
4. Shelf life is stated on only five rows: Heartland NY Popcorn 1 year, Chef Poppin 18 months, Keya's 6 months, Effie's Walnut Biscuits 6 months and Paktli 12 months (Paktli not recorded). The 60-day test needs the brand to confirm for the rest.
5. Single-serve format is confirmed for about 20 rows. Granola, crispbread and gift-led brands mostly sell share packs.
6. The SFFS directory could not be filtered by state. Search-based coverage misses NY exhibitors whose descriptions do not name a place. Fetching all detail pages (about 0.6 MB each) would close this.
7. About 9 WebSearch calls were used of the 95 allowed. The work leaned on directory, API and catalog endpoints instead.

## Spot-check (five rows at random, `random.seed(20261024)`; sources re-opened 2026-10-24)

| CSV line | Brand | Re-checked | Result |
| --- | --- | --- | --- |
| 6 | Figa Foods | SFFS detail (State: New York, website figafoods.com); S&FWB article "Ariel Altman, co-founder of Figa Foods, won the Audience Choice Award", dated June 2, 2026; Startup CPG founder feature title; Stockist row "Chelsea Market Baskets, 75 9th Ave" | Pass |
| 13 | Morito Chocolates | HBK marketplace "Handmade in Brooklyn"; products.json has two items published 2026-10-04; meta "Brooklyn-based ... low in sugar" | Pass |
| 21 | Effie's Homemade | SFA 2027 finalists "Gruyere Biscuits – Effie's Homemade" (October 19, 2026); WFM API at store 10162 returns Effies Homemade 7.2 oz SKUs; contact page "Hyde Park, MA 02136" | Pass |
| 39 | Chikka Chikka | SFA 2027 finalists "Fennel Seed Mouth Freshener – Chikka Chikka"; site text "reduces bloating", "support brain health"; meta "Hudson Valley NY" | Pass |
| 43 | Milène Jardine Chocolatier | Made in Queens listing; products.json | **One error:** why_now said "six vegan bars", but five were published on 2026-05-07. Corrected in the CSV |

Result: 1 field wrong out of about 40 checked, about 2.5%. No fabricated field.

A self-review pass before the spot-check also fixed these:
- Two SFFS exhibitor ids I had typed without looking up (Gigantic, Cho's Bakeshop) were replaced with the real ids. All 27 ids in the CSV now match the scraped directory.
- Fairway's cross street was removed for Gigantic.
- Retailers likely beyond ten blocks were taken out of `nyc_retailers_near_cluster` for Doosra and Figa.
- Four interpretive phrases were reworded: the Maple Brothers "relaunched", the Namkeen "for Diwali", the DrinkFolks "repriced" and the Dona "co-pack".
