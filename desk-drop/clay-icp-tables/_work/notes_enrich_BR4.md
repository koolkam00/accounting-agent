# BR4 enrichment notes: methods and gaps

Slice: BR4, the 40 rows with `excluded = N` in `brands_BR4.csv`. That file was not edited.
Output: `clay-icp-tables/_work/enrich_BR4.csv`, 173 rows, one per changed field. Columns: `brand, field, old_value, new_value, source_url, source_date, confidence, notes`.
Research date: 2026-10-24. Every row has `source_date = 2026-10-24`.
This was read-only research. Nothing was sent or signed up for. No connector tools and no git writes were used. No personal identifier went into any request. curl used a generic browser User-Agent. No emails or phones were recorded, and no email was guessed. Several privacy policies list company inboxes and phones; those were read for the address only and left out of the file.

## How to apply the file

- A row replaces the BR4 value in `field` with `new_value`. Where `new_value` starts with `(append)`, or says "(existing WFM URLs); ...", add it to the current value instead of replacing it.
- `confidence = opened` means I opened `source_url` on 2026-10-24 and read the fact there. `confidence = snippet-unverified` (14 rows) means I saw the fact only in search results, because the page was blocked or not opened. Those values already say "unverified, founder to confirm".
- Some opened sources are more than 24 months old. They are flagged in `notes`: RISE (2023), Treat House (2013), Moon Man (2017), Simply Gum's marketing lead (2022) and Tate's (2018).
- Retailer grades follow CONTRACTS section 4. A brand locator gives `brand_claim`. Only the WFM store-scoped catalog gives `store_selector`. Nothing is set to `seen_on_shelf`.

## Counts

| Field type | Rows | Brands |
| --- | --- | --- |
| Founder name, title, profile URL | 49 | 18 |
| Marketing lead name, title, URL | 11 | 4 (RISE, Hella, Simply Gum, Graza) |
| Retailers near cluster, nearest retailer, grade, evidence | 22 | 11 |
| Shelf life or shelf stability | 11 | 8 |
| Why-now (text, URL, date) | 31 | 11 |
| HQ city or state | 29 | 23 |
| Other (funding, revenue, website, online store, format, review reason, notes) | 20 | 14 |

39 of the 40 rows got at least one change. Kelly's Four Plus Granola had nothing new to add.
Tools used: 39 WebSearch calls (under the ~95 share) and 8 WebFetch calls. Everything else was curl GET on brand pages and public JSON endpoints.

## Findings that change targeting (founder to review)

1. **RISE Brewing Co.** Its privacy policy names RISE Beverages LLC at 601 Arlington St, Houston TX. A BevNET headline (blocked) says UPTIME Energy bought RISE in early 2025. The budget owner may now sit at UPTIME. It is no longer a New York company.
2. **Brooklyn Biltong.** Its privacy-policy mailing address is in Goldsboro, North Carolina. The name says Brooklyn; the legal address does not.
3. **Early Bird Foods.** The FruitGuys (2025-05-10) says the founder and her partner run the business from their home in Michigan. The brand started in Brooklyn.
4. **Pip's.** The brand contact page gives 1 East Broad Street, Bethlehem PA. UpSnack Brands owns it.
5. **Graza.** CNBC (2024-06-07) reports a company projection of more than $48M in 2024 gross sales. `revenue_band` is set to `over-10m`, the first sourced revenue band in BR4.
6. **Tate's and Hu** are Mondelez brands: Tate's from 2018 (opened source), Hu from 2021 (snippet only). I recommend excluding both from outreach.
7. **Hella Bitters & Soda.** The brand FAQ says it contains "trace amounts of alcohol", below 0.5% ABV. The founder must decide whether that breaks the no-alcohol rule.
8. **Blind Tiger.** The brand's Storepoint locator still lists the four cluster WFM stores. The WFM catalog does not, so the locator probably reflects the Jan-Feb 2026 pilot. I graded it `brand_claim`.
9. **Issa's.** The chip brand was co-founded in 2016 by Andrew and James Issa (WKBW). Habib Issa, the BR4 founder, started the family pita bakery in 1981. A 2 oz single-serve bag exists (WebstaurantStore).
10. **The Purple Drop** won a 2026 Startup CPG Shelfie Award (Beverage, 2026-08-24). BR4 had it as a finalist only.
11. **Unhinged and Shinzo** both list mailbox-style suites at 169 Madison Ave (inside the cluster) on their privacy policies. A Newport Beach, CA directory snippet ties Unhinged to Orange County and to a second co-founder, Matt Paine (unverified).
12. **NouBon** sits in Deer Park, Long Island, not New York City. **Kim's Magic Pop** sits in Palisades Park, NJ (Delice Global). **Stiller's Soda** sits at 184 Kent Ave, Brooklyn. **Treat House** sits in Woodside, Queens. **Hu** sits at 78 5th Ave, inside the cluster. **Simply Gum** sits at 630 Flushing Ave, Brooklyn.

## Methods

1. **Brand legal pages.** Shopify `/policies/privacy-policy` and `/policies/terms-of-service` pages usually carry the company's mailing address. This was the most productive source for `hq_city` (14 brands). I checked whether each address is a mailbox (a "#11442" or "Ste 38135" style suite, a PO box or a Dover DE registered agent) and said so in `notes`.
2. **Store locators.** I detected the vendor in each brand's locator page, then queried the public data:
   - Stockist: `stockist.co/api/v1/<tag>/locations/search` (Lucky Ox, Bessou, Nomi Crunch, NouBon and WildBoard; the last two returned 0 stores within 3 mi).
   - Storepoint: `api.storepoint.co/v1/<id>/locations` (Issa's, Blind Tiger).
   - Storemapper: `www.storemapper.co/api/users/<id>/stores.js?callback=...` (Early Bird).
   I kept Manhattan stores between 4th and 40th Street. Distances are from 5th Ave and 21st St.
3. **WFM store-scoped catalog.** I swept the 4 cluster store codes again (NoMad 10773, Union Square 10162, Chelsea 10131, Manhattan West 10713) for 25 brands. Sanity checks on known brands (Lucky Ox, Chris's Cookies, Matzo Project) returned hits. No new `store_selector` links were found for the brands that were `unverified`.
4. **Brand catalogs for why-now.** Shopify `products.json` (`created_at` and `published_at`) and Squarespace `/store?format=json` (`addedOn`, `publishOn`) date new SKUs. These dates are recorded as listing dates, not press dates. Press or brand news was preferred where it existed: Simply Gum's own news post, the Brothers International press page and the Startup CPG Shelfie winners page.
5. **Shelf life.** I grepped FAQ, wholesale and product copy (`products.json` body_html). Wholesale pages proved useful (WildBoard, Purple Drop).
6. **Founders and marketing leads.** Sources were brand about and team pages, trade press opened directly (Food Business News, Food Dive, CNBC via NBC Chicago, FoodNavigator-USA, Candy Industry, CSP Daily News, WKBW, Untapped New York, The FruitGuys), the Bronx Chamber member listing, and Startup CPG podcast pages. The podcast pages list guests' LinkedIn URLs; LinkedIn itself was never opened.

## Dead ends

- Blocked (403, Cloudflare or stubs): BevNET (news and /pr), NOSH, QSR Magazine, Mastercard newsroom, Mondelez IR, Advertising Week, Nombase newswire, NJBIZ, Baking Business, ShopRite, Trendhunter, the Newport Beach directory and drinkyate.com's locator. These facts are `snippet-unverified` or left out.
- Wegmans Astor Place: the store and search pages return 500 or 404, and the app needs a session. Not checked.
- Target Manhattan stores (Häppy Candy, Day Out, Matzo Project holiday set): target.com renders on the client and exposes no store data without its private API. Not checked.
- Westside Market (Shinzo, Stiller's, B-SIDES): the site did not resolve through the proxy.
- Eataly Flatiron: no store-scoped catalog. The only Eataly evidence is Early Bird's own Storemapper list, graded `brand_claim`.
- Pearl River Mart: `products.json` has no store tags, so the Chelsea Market store can't be confirmed for Moon Man or Baabu. Its 2022 blog does name Pearl River Mart Foods for Bessou pantry items.
- These locators are not machine-readable: Destini (Hu, Day Out, Pip's), Roseperl (Brooklyn Biltong; its `wtb` JS file returned 404), Bold (Top Seedz), Secomapp with Google Maps (Simply Gum), BigCommerce (Brothers) and the Graza Stockist widget (empty).
- The 2027 sofi finalist list (2026-10-19) was blocked on all three hosts. Top Seedz was already known from its own blog; others may be on the list.

## Gaps left for the founder

1. **Founder names still missing:** Kim's Magic Pop, Goody's Granola and Brothers All Natural (surname "Betters" only). These are partial: Baabu (first names Lisa and Mayank), Sol Cacao (brothers named, no roles) and Chris's Cookies (Christian Gargiulo, snippet only, c.2016).
2. **Marketing leads:** 34 of the 40 rows still have none. Named so far: Pip's and Matzo Project (BR4); RISE, Hella and Simply Gum (2022 source, may have moved); Graza (unverified). Most of the rest are founder-led brands, and no page names a marketing owner. I did not assume the founder owns marketing.
3. **Retailers:** 16 rows have no retailer near the cluster above `unverified`: North Fork, Brooklyn Biltong, Brothers, WildBoard, Unhinged, Shinzo, Purple Drop, Day Out, Baabu, Moon Man, NouBon, DEFI, Whey Water, Sol Cacao, Top Seedz and Yaté. For WildBoard, NouBon and North Fork, the brands' own lists show nothing near the cluster, so they qualify only through online stores with discount codes. Day Out names ShopRite, which has 2 Manhattan stores in the band (766 6th Ave and 550 2nd Ave), not confirmed.
4. **Shelf life:** a brand-stated figure now exists for 10 rows: Pip's, Brooklyn Biltong, Brothers, Treat House, Häppy Candy, Tate's, WildBoard, B-SIDES, Day Out and Purple Drop. RISE and Whey Water say "shelf stable" with no figure. The other 28 rows have no brand statement; the founder or the brand must confirm 60+ days.
5. **Why-now:** 16 rows still lack a dated signal inside the 12-month window: Treat House, North Fork, Early Bird, Z Crackers, Hella, Nomi Crunch (flavors launched 2025-09, just outside), Baabu, Kelly's, Chris's Cookies, Tate's, Hu, Sol Cacao and Yaté. Stiller's has an unverified Katz's Deli deal that would be a stronger hook once a dated source is opened.
6. **HQ unconfirmed:** Graza (Brooklyn per directory snippet only), Hella (founders split across NY, LA and Ann Arbor), Early Bird (Michigan, city unknown), Day Out (Red Bank vs Montville, NJ), Baabu (New Jersey, city unknown) and Moon Man (Queens per market listing).

## Spot-check of this enrichment (five rows re-opened)

| Row | Re-checked on 2026-10-24 | Result |
| --- | --- | --- |
| Simply Gum hq_city | Privacy policy: "Simply Gum, 630 Flushing Ave, #16, Brooklyn NY 11206" | Pass |
| WildBoard shelf_stable_basis | products.json `aperitivo`: "12 months shelf life from production, shelf stable, no refrigeration" | Pass |
| Lucky Ox founder_name | Podcast page: "Fane He and Kyle Nguyen, co-founders of The Lucky Ox", 2025-06-20 | Pass |
| Issa's why_now_date | Squarespace store JSON: Garlic & Herb `addedOn` 2026-07-21 | Pass |
| Bessou nearest_stocked_retailer | Stockist map_p3x8ne63: Rose Bakery, 160 Lexington Avenue, 0.46 mi | Pass |

0 field errors in 5 rows. During the run I removed 9 rows that later evidence replaced or that overreached: a first-name-only RISE founder row, three Simply Gum why-now rows rebuilt from the dated brand news post, a dateline-only Stiller's HQ row, an "unknown, NJ" Kim's HQ row, and three Early Bird marketing rows (the partner has no stated marketing role, so she went into `notes`).
