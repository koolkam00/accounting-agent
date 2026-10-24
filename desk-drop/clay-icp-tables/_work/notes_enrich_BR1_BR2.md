# Enrichment notes: BR1 and BR2 (methods and gaps)

Run date 2026-10-24. Scope: the 116 rows with `excluded = N` (BR1 60, BR2 56). Output: `enrich_BR1_BR2.csv` (331 rows, one per changed field, 84 brands touched: BR1 40, BR2 44). The `brands_BR1.csv` and `brands_BR2.csv` files were not edited. `old_value` is copied from those files. Where two enrichment rows exist for one brand and field, the later row wins and its note says so (Good Crisp `why_now`, Jack & Friends `founder_title`).

## Counts

| Field type | Rows | Brands (opened) | Brands (snippet only) |
| --- | --- | --- | --- |
| HQ city and state | 88 | 50 | 4 |
| Founder name, title, profile URL | 75 | 32 | 7 |
| Marketing name, title, profile URL | 31 | 6 | 5 |
| Shelf-life statement (`shelf_stable_basis`, plus 9 `shelf_stable` likely-to-Y upgrades) | 37 | 28 | 0 |
| Why-now from press (`why_now`, `_url`, `_date`) | 60 | 19 | 1 (Mamame) |
| `startup_cpg_member` = Y with evidence URL | 10 | 5 | 0 |
| Revenue from a press quote | 2 | 1 (Tierra Farm) | 0 |
| Other: website (8), funding_stage (4), founder_review (3), notes (13) | 28 | | |

Confidence: 289 rows `opened`, 42 rows `snippet-unverified`. Every `snippet-unverified` value also says "unverified, founder to confirm" in the value or the note.

## Methods (in the order run)

1. **Startup CPG feed (free).** Searched `startupcpg.com/wp-json/wp/v2/posts?search=<brand>` for every target row not already Y. A Y needs a brand newswire release or a Shelfie finalist listing. A passing mention in an editorial list does not count: Joolies, Magic Spoon and Coditos stay `unknown`. New Y rows: Daily Crunch, Righteous Felon, Harken Sweets, Mavericks Snacks, Sfizi. The newswire datelines also gave HQ cities.
2. **Brand-site sweep (free, curl).** Fetched 16 standard paths per brand: home, contact, about, our-story, FAQ, press, team, wholesale, and the Shopify `/policies/contact-information`, terms and refund pages. Then a second pass of 13 alternate FAQ and shipping paths, plus `products.json` descriptions. Grepped for City, ST ZIP, shelf-life wording and marketing titles. Only city and state are recorded, never the street. Several addresses are apartments or P.O. boxes.
3. **Snack & Bakery site search (free).** Ran `snackandbakery.com/search?q=<brand>` for all 116 brands. Then opened every article from about the last 18 months and kept only the dated pieces inside 2025-10-24 to 2026-10-24 for why-now. Articles also gave CEO and brand-manager names (Firehook, Go Raw, Solely, Mavericks, Joyride).
4. **WebSearch (about 78 calls).** Used for missing domains (Firehook, Good Crisp, Simply 7, Go Raw, Stellar, Jack & Friends, Louisville, Every Body Eat), unknown HQs, LinkedIn-restricted searches for marketing leads, and press for New York brands. Every search hit was then opened with curl or WebFetch where possible. What could not be opened is marked `snippet-unverified`. That covers NOSH, BevNET, LinkedIn, Craft and Press Hook, which return 403 or 404.
5. **Why-now rule.** Press or an announcement replaces a Shopify publish-date signal, as the task asked. For seasonal pieces (Unreal Easter, MarieBelle Valentine's, Fruition's Cambridge pop-up, Mavericks), the note says the Shopify signal is fresher and leaves the choice to the founder.

## Flags the assembler should carry over

- **New York brands found or confirmed:** Beyond Good (Brooklyn, clean row), Harken Sweets, Magic Spoon, Mezcla, Jack & Friends, Steve & Andy's (Manhattan) and Zack's Mighty (Brooklyn, third-party profile). S'NOODS is New York per a snippet only.
- **Ownership and scale signals (founder_review):** Emmy's Organics (Grupo Bimbo since 2021, snippet), Vermont Smoke & Cure (Johnsonville since 2020, opened), Good Crisp (MPearlRock, Jan 2026), RIND (Keep It Real Foods platform, Mar 2026), Nick's Sticks (Wenzel's Farm), Tierra Farm (about $30M revenue in 2021), Solely (Walmart nationwide), Harken (about 5,000 doors), Daily Crunch (10,000+ doors).
- **Shelf-life risks:** truffle and bonbon SKUs fail the 60-day rule (Knipschildt 7 days, Elements truffle boxes 2 months, Lagusta's bonbons 1 month, Jacques Torres 3-4 weeks, Li-Lac filled 21 days). Pitch bars only. SuperSeedz says "several weeks" in an airtight container, which is ambiguous. Mamame has a clearance lot with a Sept 2026 best-before date.
- **Imported or overseas HQ (affects the 10-business-day ship test):** Mamame (Indonesia) and Inka Crops (Peru, with a US importer per snippet).
- **Conflicts left for the founder:** Little Latke (Chicago site vs "Dallas-based" in the press), Partake (Jersey City vs New York), Blue Stripes (Cedar Falls IA LLC address vs New York), Peeled (Cumberland RI vs Brooklyn), Nantucket (interim CEO listing vs May 2026 CEO), Mast (now a Westchester market).

## Gaps

- **HQ still unknown or unverified (14):** Beefy's Own, Ella's Flats (FL confirmed, city snippet), Goodie Girl, Humble, Inka Crops, KIND, Mamame, Nantucket, PRETZELIZED, Partake, Peeled, S'NOODS, Sour Strips, Good Crisp (Longmont returns address vs Boulder snippet).
- **Founder still unknown (21):** Blake's, Chifles, ChocXO, Crispy Green, DANG, Fat Witch, Ghips (two searches, nothing), Go Raw, Inka Crops, KIND, Kate's, Mast, NuGo, Pa's Peanuts, Peeled, Sour Strips, SuperSeedz, The Hermit, Thunderbird, Unique Snacks, Vermont Smoke & Cure.
- **Marketing leads.** 21 of 116 rows now name one: 10 were already in BR1 and 11 are new. 5 of the new ones are snippet-only (Rip Van, Partake, Magic Spoon, PRETZELIZED, Taza). Small brands are founder-led and show no marketing title, so the founder is the contact. LinkedIn was never opened.
- **Shelf-life figure** still missing for about 86 rows. The intake question q1 must confirm 60+ days.
- **Why-now** still empty for 28 rows. These include New York brands Rule Breaker, Seed + Mill, Joyva, Jack & Friends, BobbySue's and By the Way. Searches for 2026 news on them found nothing dated.
- **Revenue.** Only Tierra Farm was added (over-10m, a 2021 quote). No current figure was found for Partake, Daily Crunch or Strip Jerky. Nothing was inferred from door counts.
- **Not attempted:** Ghips and Veggie Vice founders after one or two failed searches, Every Body Eat shelf life, and Wegmans or Target store checks.

## Dead ends

NOSH, BevNET, bakingbusiness.com, nombase newswire, Craft and Press Hook returned 403 or 404. PR Newswire search is JavaScript-only. Two Startup CPG newswire posts and the Snack & Bakery search pages were the most productive free sources.
