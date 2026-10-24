# 01 · Your LinkedIn headline and profile

Version 1.0 · 2026-10-24 · Part A of workstream E · folder `desk-drop-outreach/messages/`

**What it is for.** People check a sender's LinkedIn before they reply (plan, Phase 0 setup). The profile has to say, in their first three seconds, the same thing the email said: who you are, what you are testing, and that you are not selling yet.

**When it is used.** Set it on day 1 (Mon 2026-10-26, derived), before the first message. Change it twice: when the name is decided, and when the first offices have signed.

**The name rule.** The legal pack holds any "public website or social profile under the working name" until the name is decided (desk-drop-legal-pack/name-check-log.md, status HOLD on 2026-10-23; a business called "DeskDrop" already sells chocolate gifts to offices). Your own profile is public. So version 1 does not name the business; your emails and calls do, one to one, which the log allows. Version 2 names it, from `{BRAND_NAME}` in `desk-drop-identity/brand.json`, only once `name_decided = Y` (`04-slot-state.csv`). This differs from the plan, which says to name it in the headline in week 1; the reason is the name check, and it is listed as a conflict in the report.

**Lengths.** LinkedIn's editor allows 220 characters for the headline and 2,600 for About (Hublead's 2026 list, https://www.hublead.io/linkedin-character-limit, opened 2026-10-24; these are editor limits, not published by LinkedIn; check in the editor). The headlines below are 120 to 125 characters with the working name and a two-digit office count.

---

## Version 1 · From day 1 until the name is decided

**Headline**

> Founder, pre-launch · Asking New York office managers and snack and drink founders how pantries and sampling really work

**About**

> I'm testing a small idea around Flatiron, NoMad and Union Square: emerging snack and drink brands send sealed product to a handful of nearby offices, the office puts it out the day it arrives, and the brand gets photos, counts and what employees thought, in a one-page report.
>
> Before I build any of it, I'm talking to 15 people who run office pantries and 15 founders of snack and drink brands. If that's you, I'd value 20 minutes of your experience. Questions only; there's nothing to buy.
>
> A few things I won't do: collect anything about employees, promise sales, or blur the numbers. Delivered, placed, depleted, tried, scanned and purchased are different counts, and a report should keep them apart.
>
> [ONE TRUE LINE ABOUT YOU: one or two sentences of real background, such as what you did before this. Leave it out rather than stretch it.]

**Experience entry**

- Title: Founder
- Company: Self-employed
- Dates: Oct 2026 to present
- Location: New York, New York
- Description: "Pre-launch. Testing an office sampling service for emerging snack and drink brands around Flatiron, NoMad and Union Square. October and November 2026: 30 research conversations, 15 with offices and 15 with brands, before building anything."

**Leave empty for now:** Featured, a company page, a banner with a logo, a website link. Use your own photo, not a logo or a stock image.

---

## Version 2 · Once `name_decided = Y`

**Headline**

> Founder, {BRAND_NAME} · Emerging snack and drink brands in Flatiron office pantries, with photos, counts and a one-page report

**About**: version 1, with the first sentence changed to "I run {BRAND_NAME}, a small New York service that brings emerging snack and drink brands to a handful of offices around Flatiron, NoMad and Union Square." and the second paragraph changed to "Offices get them free and choose what comes. Brands pay a fixed fee per office and get the report. If you run an office pantry or a snack or drink brand and want to hear more, message me here." Keep the third paragraph as it is.

**Experience entry**: Company {BRAND_NAME} (no company page until the name check allows public launch); description "A New York office sampling service for emerging snack and drink brands. Offices around Flatiron, NoMad and Union Square get free, sealed products and choose what comes; brands pay per office and get placement photos, counts, an anonymous employee survey and a one-page report."

**Featured**: the website, once `site_live = Y`.

---

## Version 3 · Once `offices_signed >= 1`

**Headline**

> Founder, {BRAND_NAME} · Placing emerging snack and drink brands in [OFFICES SIGNED] Flatiron office pantries, with photos, counts and a report

Only the number from `04-slot-state.csv`, updated the day it changes. Never "partnered with", never office names unless the office agreed to be named (desk-drop-legal-pack/03 section 6).

---

## Changelog

- Round 1 (2026-10-24): drafted three versions keyed to the name-check hold and the tracker state; About written around the plan's measurement ladder; background left as a slot rather than invented.
- Round 2 (2026-10-24): About restored to the ladder words (placed, depleted, purchased; "put out" and "gone" were softer renames); headline lengths restated from a count (120 to 125 characters).
