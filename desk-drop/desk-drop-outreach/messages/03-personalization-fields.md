# 03 · Personalization fields: what each `{token}` is, where it comes from, and its fallback

Version 1.0 · 2026-10-24 · Part A of workstream E · folder `desk-drop-outreach/messages/`

**What it is for.** Every `{token}` in the message files, mapped to a Clay column, with the rule for using it and the fallback when the column is blank, stale or unproven. The machine-readable copy is `03-personalization-fields.csv`; the fill script in `_render/` reads it.

**Which columns.** The Clay tables' stable columns are fixed by CONTRACTS section 6.2. On 2026-10-24 `clay-icp-tables/` had no `HANDOFF.md` and no daily views yet (only research files in `_work/`), so the few non-stable source columns below are **provisional**: `street_address` (the office address, as cluster-1-flatiron/companies.csv names it and A is told to import unchanged), `product_example`, `category` and `hq_city` (as A's brand research files name them). Check them against `clay-icp-tables/HANDOFF.md` when it exists and change only the `source_column` cells.

**Columns E adds to the Clay tables.** CONTRACTS 6.2 lists E's conversation-tracking columns (`sequence`, `touch_1_date` ... `referral_from`). For personalization E also adds, to the same tables (never a second store):

| Column | Table | What it holds | Who fills it, when |
| --- | --- | --- | --- |
| `street_short` | Offices | The street name, no number: "Park Avenue South" | A Clay formula on the address column, or you, when the row is queued |
| `why_now_hook` | both | One sentence of plain fact from `why_now`: "Congratulations on the Target launch." | You, when the row is queued (about 15 seconds), after opening `why_now_url`; or a Clay AI column you read before use |
| `product_short` | Brands | The product's own name in two to four words | A Clay formula or you, when queued |
| `call_note_hook` | both | Twelve words or fewer the person said on the call | You, within ten minutes of the call |
| `how_we_know` | both | Fifteen words or fewer, true and checkable | You, for `known_to_founder = Y` rows |
| `referrer_ok_to_name` | both | Y once the referrer agreed to be named | You, from their reply |

All six are optional. Every one has a fallback, so a blank never breaks a message.

**The floor.** A fallback keeps the copy readable; it does not make a message personal. If a touch 1 would go out with nothing about the person or company in it (no name, no company, no street, no store, no why-now), `_render/fill.py` warns "fix the row before sending". In a real daily view that means the row is missing its company or contact and should not have been queued.

---

## The printed fields

| Token | Clay column | Rule | Fallback |
| --- | --- | --- | --- |
| `{greeting}` | `first_name` | "Hi {first_name}," for a real first name | "Hello," (blank, or a role word such as team, office, info, admin, hr) |
| `{company}` | `company` | Trailing Inc, LLC, Corp, Co, Ltd, PBC removed. Sentences are built so the fallback reads: "the pantry at {company}", never "the {company} pantry" | "your office" (offices), "your brand" (brands) |
| `{area}` | `street_short`, else the address column | Street name only, W and E spelled out | the cluster name: "Flatiron, NoMad and Union Square" |
| `{?why_now_hook}` | `why_now_hook` with `why_now_date`, `why_now_url` | Only if filled, under 120 days old on the send date, and you opened the source | left out |
| `{product}` | `product_short` (from `product_example`) | Two to four words, the product's own name | the brand name, then "your product" |
| `{?retailer_line}` | `nearest_stocked_retailer`, `nearest_retailer_grade` | By grade, below | left out (grade `unverified` or blank) |
| `{category_phrase}` | `category` (brand intake `category` later) | "a chips and crisps brand" (CONTRACTS section 4 label) | "an emerging brand" |
| `{category_short}`, `{category_only_phrase}` | `category` | "chips and crisps"; "the only chips and crisps brand" | "brand in your category"; "the only brand in your category" |
| `{brand_name}`, `{brand_category_phrase}`, `{?brand_from_city}`, `{?retailer_for_office}` | the brand's row, inside an office email (10, step 7) | so the brand's fields never mix with the office's `{company}` | "the brand"; "an emerging brand"; left out; left out |
| `{first_name_or_founder}` | `first_name` | the founder's first name, in an ask to a connector (08) | "the founder" |
| `{?from_city}` | `hq_city` | " from Queens"; never a value marked unverified | left out |
| `{call_note_hook_line}` | `call_note_hook` | "Thanks again for today, and for the detail about {call_note_hook}." | "Thanks again for the time today." |
| `{referrer_name}` | `referral_from` → that row, plus `referrer_ok_to_name` | Named only with Y | not named; ordinary first touch |
| `[HOW WE KNOW EACH OTHER]` | `how_we_know` | True, checkable | warm template not used |

Config tokens, not from Clay: `{BRAND_NAME}` (from `desk-drop-identity/brand.json`, the one place the name is set), `{CLUSTER}` and `{CLUSTER_SHORT}` (from `04-slot-state.csv`, `cluster_name` and `cluster_short`), `{SIGNATURE}` (file 02).

### The retailer sentence, by evidence grade

The grade decides the verb. A sentence never claims more than its evidence (CONTRACTS section 4).

| `nearest_retailer_grade` | Discovery wording | Selling wording |
| --- | --- | --- |
| `seen_on_shelf` (only you set it, after seeing it) | "I saw {product} on the shelf at {retailer}, near the offices I'm writing to." | "I saw {product} on the shelf at {retailer}, a short walk from them." |
| `store_selector` | "{retailer}'s store page lists {product}, and that store is near the offices I'm writing to." | "{retailer}'s store page lists {product}, a short walk from them." |
| `brand_claim` | "Your store locator lists {retailer}, near the offices I'm writing to." | "Your store locator lists {retailer}, a short walk from them." |
| `unverified` or blank | left out | left out |

`{retailer}` is the part of `nearest_stocked_retailer` before the first comma ("Whole Foods Market Union Square"). "Near" and "a short walk" are true because the Clay table only records a nearest retailer inside or within ten blocks of the cluster (A's gate). In selling copy the retailer sentence comes after the roster sentence, so "them" means the offices.

## The routing fields (never printed)

| Clay column | What it decides |
| --- | --- |
| `channel` | Which file: `email` 05 or 06, `linkedin` 07, `warm-intro` 08 part 1, `walk-in` 08 part 3 |
| `email_status` | `verified`: email allowed. `unverified` or `none`: LinkedIn or walk-in |
| `known_to_founder` | Y with `how_we_know`: the warm direct email (08, 1c) |
| `startup_cpg_member` | Never printed, never used as a hook |
| `do_not_contact` | Y: nothing, on any channel, ever |
| `status` | Touch 1 only from `queued`; touches 2 and 3 only from `contacted` with no reply |
| `onsite_band` | Never printed. `under-40` needs your yes before queueing |
| `why_now_date` | The 120-day freshness rule |

## Two filled examples per sequence

`examples/` holds each sequence filled twice at phone width (390 px): once from a full SAMPLE row and once with every fallback triggered. Their rows are in `examples/SAMPLE-rows.csv`; no real daily view existed on 2026-10-24. `_render/HOW-TO-RUN.md` says how to rebuild them, and how to make paste-ready drafts from a real daily view.

## Changelog

- Round 1 (2026-10-24): mapped every token to the CONTRACTS 6.2 stable columns; six optional E columns added to the same tables; fallbacks for every field; the retailer sentence tied to the evidence grade.
- Round 2 (2026-10-24): after the fallback renders, sentences built so the company fallback reads everywhere ("the pantry at your office"); category and city tokens split; the brand's own tokens inside office emails; capital letters restored where a sentence starts with a fallback.
- Round 3 (2026-10-24): the personalization floor (a warning when a touch 1 prints nothing about the person); CSV regenerated to list every token the fill script implements.
