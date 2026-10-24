# BR2 notes: sweet snacks and bars

Slice: snack bars, cookies and baked snacks, chocolate and candy, dried fruit and fruit snacks.
File: `clay-icp-tables/_work/brands_BR2.csv` (64 rows, 41 columns, the exact header from the task).
Researched 2026-10-23 into the early hours of 2026-10-24 UTC. Every row carries `found_date = 2026-10-23` as the task instructed. A few late pages were opened just after midnight UTC.

## Counts

| Measure | Count |
| --- | --- |
| Rows | 64 |
| New York State HQ | 22 (17 NYC, 5 elsewhere in NY State: Fruition, Greyston, Emmy's, Lagusta's, By the Way) |
| Partake Foods | HQ given as NY or NJ (sources conflict), not counted above |
| Other Northeast / Mid-Atlantic | 6 (Crispy Green NJ, Jonesbar NJ, Bakery on Main CT, 88 Acres MA, Taza MA, Amazi DC) |
| excluded = Y | 8 (Belgian Boys, Greyston, Mid-Day Squares, Nelly's, Honey Mama's, Hail Merry: refrigerated or short shelf life. Munk Pack, IQBAR: health or function claims) |
| founder_review = Y | 48 (see "Why so many founder_review flags") |
| Not excluded and no founder flag | 10 (Fine & Raw, Eleni's, Fruition, Emmy's, Steve & Andy's, Mayana, Jonesbar, Beyond Good, Taza, Amazi) |
| health_claim_flag = Y | 4 (Seed + Mill, Munk Pack, IQBAR, Harken Sweets) |
| nearest_retailer_grade | store_selector 41, brand_claim 2, unverified 21 |
| why_now filled | 40 |
| Founder named (full or first name) | 41 |
| Marketing lead named | 0 |
| revenue_band | 500k-10m 1 (Rule Breaker), over-10m 1 (Rip Van), unknown 62 |
| startup_cpg_member | unknown for all 64 |
| Categories | chocolate-candy 29, cookies-baked 14, bars 14, fruit-snacks 6, other-snack 1 |

## Methods

1. **Whole Foods store catalogs (main evidence for `store_selector`).** wholefoodsmarket.com runs a store-scoped product search at `https://www.wholefoodsmarket.com/api/search?text=<query>&store=<code>`. I read the store codes from the stores' own pages:
   - Union Square, 4 Union Sq S: `10162`
   - NoMad, 63 Madison Ave: `10773`
   - Chelsea, 250 7th Ave: `10131`

   I confirmed that the store filter is real. The same query gives different results at different stores (Rip Van: 4 items at Union Square, 2 at Chelsea). A row gets `store_selector` for a store only when that store's results include the brand. Every such URL is listed in `retailer_evidence_urls`. A final automated pass re-ran all 41 store_selector rows and every claimed store returned at least one item.
   - Caveat: this is the store's online catalog, not proof the item is on the shelf today. Notes say so where it matters.
   - Avoid `&` in queries. "spring & mulberry" returned 0 at Union Square, but "spring mulberry" returned 4.
2. **Catalog sweeps for discovery.** I listed every brand in the Union Square catalog for cookies, chocolate bar, candy, gummies, bars, dried fruit, brownie, marshmallow, toffee, caramels, wafer and date. Emerging brands from those lists were then researched on their own sites. This is why many rows outside New York have strong evidence.
3. **Brand store locators, graded `brand_claim`.** I read the public locator data behind the brand's own locator page:
   - Stockist: `stockist.co/api/v1/<tag>/locations/search`, used for Seed + Mill, Eleni's, Fruition, Good Word, Steve & Andy's and Harken.
   - Storemapper: `storemapper.co/api/users/<id>/stores.js`, used for Raaka.
   - Storepoint: `api.storepoint.co/v1/<id>/locations`, used for Mayana.

   Only Manhattan stores between 4th and 40th Street are listed in `nyc_retailers_near_cluster`. Destini, Secomapp/roseperl and iframe locators could not be read, and this is noted in each row.
4. **Brand sites.** I opened the about, story, FAQ, contact and locator pages. On Shopify sites I also read `products.json` for product names, pack formats and publish dates.
5. **Trade press**, where it was reachable: Shelby Report (Rip Van), Bakery and Snacks (Rule Breaker), Green Queen (Blue Stripes), Food Navigator (Partake), WOWT (Partake / Girl Scouts).
6. **Dedupe.** Before every append, I checked brand name and website domain against every other `brands_*.csv` in `_work`. A final cross-check found no duplicates. Brothers All Natural was skipped because BR4 already has it.

## Field conventions used in this file (for the assembler)

- `shelf_stable`:
  - `Y`: the brand states room-temperature storage or a shelf life.
  - `likely`: an ambient category sold ambient at retail, with no published shelf-life figure. The 60-day rule still needs founder confirmation.
  - `N`: the brand says refrigerate, or gives a shelf life under 60 days.
  - `unknown`: nothing found.

  The basis is always in `shelf_stable_basis`.
- `why_now`: 37 of the 40 dated signals come from the brand's own Shopify product publish dates (`products.json`, `published_at`), recorded as "new X added to brand store". This shows a new SKU went live online. It is weaker than a press release, and each row's notes say so. Good Word's launch wording is also on its about page. Only 3 signals come from press: Rip Van (2026-10-07, Shelby Report: new CEO and 1,800 doors), Partake (2026-09-08, WOWT: Girl Scout Sparkables), and Belgian Boys (NOSH release seen in search results but blocked, marked unverified). Phase 2 wants a launch, a retail placement or a local push, so the outreach workstream should re-confirm these Shopify-dated signals before using them in copy.
- `nearest_stocked_retailer`: the most central evidenced store for the provisional cluster (14th to 30th St, 6th Ave to Park Ave S). That is usually WFM NoMad (63 Madison Ave at 27th St). Union Square is used where NoMad has no evidence. The grade matches the store named.
- `instagram_url`: the handle the brand links from its own site. Instagram itself was not opened, because it blocks bots. Sour Strips is left blank: its site is Hershey's and links a Hershey account.
- `founder_name`: when the brand page gives only first names, the row says so. Surnames found only in search snippets are marked "unverified, founder to confirm" (Belgian Boys, Raaka).

## Why so many founder_review flags

The task asks for a flag on every borderline case. These are the main reasons, and many rows have more than one:
- Protein, low-sugar or "better-for-you" nutrient positioning. These are nutrient-content claims, not health claims, per CONTRACTS section 4.
- Probably above the $10M ceiling, by scale signals only: thousands of doors, 10+ SKUs per store, Costco or Walmart. Revenue was never inferred from these. The band stays `unknown` and only the flag is set.
- Kids' positioning.
- Big-brand ownership: Sour Strips (Hershey), KIND (Mars), jcoco (Seattle Chocolate Co.).
- Heritage or luxury chocolatiers that are not emerging CPG: Joyva, Jacques Torres, MarieBelle, Li-Lac, Knipschildt.
- Unclear shelf life (fresh bakery).
- Wellness wording close to the claim line: Harken "gut-lovin' prebiotic fiber", NuGo "GLP-1 Protein Bar", Raaka's adaptogen "Functional" bars, Goodio "Natural Focus" / "Calm & Balanced".

The assembler should treat founder_review as "look before outreach", not as a rejection.

## Dead ends and blocks

- **WebSearch budget.** The shared per-turn WebSearch limit (200 calls across all agents) ran out early in this slice, after about 14 of my searches. After that I used no search engine at all. Discovery switched to the Whole Foods catalogs and to brand domains I typed in directly. As a result, many rows are missing HQ city, founder surname, funding and press-based why-now signals.
- **Blocked by Cloudflare or bot protection (403):** nosh.com, bevnet.com, bakingbusiness.com, bcorporation.net, and wawa.com's locator. NOSH and BevNET facts appear only where a search snippet was the source, and they are marked unverified.
- **Defunct or changed:**
  - nunuchocolates.com is now an unrelated editorial site, so Nunu Chocolates may have closed. Not recorded.
  - mastbrothers.com redirects to mastmarket.com, which is now an organic market.
  - sourstrips.com redirects to hersheyland.com.
- **Not a fit or not reachable, so not recorded:**
  - Kika's Treats: San Francisco per search results, and the site was unreachable.
  - Uncle Wally's: owned by Give and Go per search results, site unreachable.
  - Crown Maple: maple syrup, not a snack.
  - Ovenly: no packaged retail evidence.
  - Little Rae's Bakery: seasonal wholesale only.
  - Eating Evolved, Antidote, Superior on Main and Joydays: JavaScript-only sites with no readable text.
  - Sweet Riot: HTTP 526.
  - Little Secrets, Malvi, Every Body Eat, Olyra, Jeca, Wandel, Happy Candy and Lilly's Homestyle: no domain found by direct guess.
  - Hu Kitchen and Tate's Bake Shop: NY brands believed to be big-brand owned, but ownership could not be confirmed on their sites without search. Not recorded. Founder to add if wanted.
- **Partake Foods HQ:** search snippets conflict (New York vs Jersey City). Recorded as "unverified, founder to confirm".

## Gaps

- No marketing lead names. Brand sites rarely list them, and LinkedIn is blocked.
- `startup_cpg_member` is unknown for all rows. I found no public Startup CPG page for any of these brands, and with the search budget gone I could not look further.
- `revenue_band` is unknown for 62 of 64 rows. Only two rows have a sourced figure.
- HQ city is unknown or vague for about 24 rows, mostly non-New York brands found through the Whole Foods sweeps.
- Shelf-life figures are published by only 11 brands. The other 43 ambient rows are `likely` and need the founder or the brand's intake answer (q1) to confirm 60+ days.
- Individually wrapped format is confirmed for 48 rows. Several Whole Foods SKUs are multi-serve bags or boxes (Emmy's 6 oz, Steve & Andy's 5.5 oz, Eleni's pouches). The brand would need to supply a single-serve SKU.
- Trader Joe's (own label only), Eataly (Italian imports), Wegmans Astor Place and Target were not checked at store level. Wegmans and Target store catalogs need a session.

## Spot check (5 random rows, seed 20261023)

Re-opened 2026-10-23/24. I checked 8 key fields per row: brand, HQ, founder, product, shelf basis, retailer and grade, why_now, why_now_date. That is 40 fields.

| Row | Result |
| --- | --- |
| Magic Spoon | Founders "Greg and Gabi" confirmed on Our Story. WFM NoMad lists cereal only, as recorded. Treats publish date 2026-08-26 confirmed. **Error:** `individually_packaged = Y` was not supported, because the Treats description is empty. Downgraded to `unknown`. |
| Beyond Good | Pistachio Crunch bar publish date 2026-10-02 confirmed. WFM NoMad lists 4+ Beyond Good bars. OK. |
| Maxine's Heavenly | Story page ("Our mom, Maxine", "Sweetened By Nature") confirmed. WFM Chelsea lists 2 creme sandwich cookies. Seasonal SKUs dated 2026-10-07 and 2026-10-13 confirmed. OK. |
| Kate's Real Food | "Born in the Rocky Mountains" and "High in protein" confirmed. Variety Pack 2026-09-18 confirmed. OK. |
| Lagusta's Luscious | Fall collections dated 2026-10-17 confirmed. **Error:** HQ was recorded as unknown, but the about page shows "New Paltz, NY 12561". Corrected. It also lists a "New York, New York" location, noted for the founder. |

Result: 2 wrong fields out of 40 (5%), no fabricated values, both fixed in the CSV.

Separate automated check: all 41 store_selector claims were re-queried live. Two rows (Seed + Mill and Mid-Day Squares) claimed Chelsea without the Chelsea URL in `retailer_evidence_urls`. I added the URLs, and both stores returned the brand.
