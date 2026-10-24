# 12 · Startup CPG posts: sharing what discovery found

Version 1.2 · 2026-10-24 · Outreach engine (workstream E) · `desk-drop-outreach/messages/`

**What it is for.** Three short posts for the Startup CPG Slack that share what the discovery conversations found, with every number in a bracketed slot filled from your own notes. The plan calls an honest findings post "the best lead magnet you have" and is clear that cold selling inside the community is not allowed. These posts sell nothing.

**About the community.** Startup CPG describes itself as free to join, with a Slack of "40,000+ Members" (https://startupcpg.com/join/ and https://startupcpg.com/, opened 2026-10-24). The plan's figure of 15,000 to 22,000 is older; the posts state no member count. The community's own posting rules were not found on its public site (its Terms of Service page returned "not found" on 2026-10-24): **unverified, founder to confirm.** Read the workspace's pinned rules and each channel's description before the first post, and post only where findings and questions fit.

**When it is used.**

| Post | Post it when | Earliest likely date (derived, founder to confirm) |
| --- | --- | --- |
| 1 · Offices | At least 8 office conversations are logged (`call_date` filled on 8 office rows) | Tue 2026-11-10 |
| 2 · Brands | At least 8 brand conversations are logged | Thu 2026-11-12 |
| 3 · What founders want counted | After Gate 0 (Fri 2026-11-13), with 15 or more brand conversations logged | Tue 2026-11-17 |

Not before `startup_cpg_joined = Y`. Tuesday to Thursday, mid-morning.

## Rules for every post and every reply under it

1. **No pitch, no name, no link.** The business is not named (the name check holds public use: desk-drop-legal-pack/name-check-log.md), there is no website link, no "DM me", no "we're looking for brands", no price, and no advice on what to demand from a sampling service: that is this business's own selling point, and posting it to the people you will sell to is marketing dressed as a finding.
2. **Say who is posting, every time.** Each post carries one neutral line near the top: "Context: I'm researching whether to start an office sampling service, so weigh this accordingly. Not selling anything here." A reader who later meets you as a seller must not feel misled. If the pinned rules seem to forbid even that line, ask a moderator before posting, and do not post without it.
3. **Only numbers from your notes.** Every `[SLOT]` comes from the tracker (the table below). If a slot cannot be filled from the notes, delete that line. Never round up, never "about half" when it is 6 of 15: write "6 of 15".
4. **No one identifiable.** No company names, no names, no detail that points to one office or brand. A quote only with the person's yes, given on the call or by email, and without their name.
5. **The ask is a question to the community**, never "who wants to try it".
6. **If someone asks what you do**, answer in the thread, in one line, and move it to a direct message only if they ask: "I'm testing a way to get emerging brands into office pantries around Flatiron with photos and a short report. Still at the research stage. Happy to share more by DM if useful." Then follow their lead. Anyone who messages you this way may go into Clay with `channel = warm-intro` and `call_notes` "asked in Startup CPG".
7. **Never message someone because they reacted or replied.** Only if they ask.

## Where each slot comes from

The call guides and the post-call note template are in `calls/`. The counted slots come from the tracker's Scorecard block "Numbers for the Startup CPG posts" (`tracking/how-the-tracker-works.md`, Friday step 5), as of the Friday you post; print the tracker's number, not a count from Clay. The slots marked *read* are not coded: read them from the verbatims.

| Slot | Source (tracker field, Office_Log or Brand_Log, distinct offices or brands) |
| --- | --- |
| [OFFICE CONVERSATIONS] / [BRAND CONVERSATIONS] | Conversations logged on that side (a row with a `row_id` and a `call_date`) |
| [N GET BRAND OFFERS] | Office question 3: `q3_brands_reach_out` = Y |
| [WHAT HAPPENS TO IT] | *read*: question 3, `q3_free_product_verbatim`, the most common answer in your words |
| [N ONE PERSON DECIDES] | `owner_can_say_yes_alone` = Y |
| [WHO ELSE DECIDES] | The most common `other_approver` (facilities, HR, the CEO's assistant) |
| [TOP YES REASON] / [TOP NO REASON] | *read*: question 4, `q4_yes_needs_verbatim` and `q4_no_triggers_verbatim`; the top office objection code is the counted check on the second |
| [N WOULD PHOTO AND SURVEY] | Question 5: `q5_photo_and_survey` = Y |
| [TUESDAY RANGE] | Question 2: lowest to highest `tuesday_headcount` |
| [N USE A SERVICE] | Question 1: `uses_snack_service` = Y |
| [BRAND SPEND RANGE] | Brand question 2: lowest `q2_sampling_budget_quarter_low_usd` to highest `q2_sampling_budget_quarter_high_usd` |
| [WHO SIGNS OFF] | *read*: brand question 2, `budget_approver`, the most common answer |
| [N SEEDED OFFICES] | Brand question 3: `q3_seeded_offices` = Y |
| [WHAT HAPPENED] | *read*: brand question 3, `q3_verbatim`, the most common outcome |
| [MEDIAN NUMBER NAMED] | Brand question 4: median `wtp_before_usd`, first answer per brand, named before any price (the Gate 0 record; kept out of the posts, see Post 2) |
| [TOP REPORT NEED] / [TOP REPORTING COMPLAINT] | *read*: brand question 5, `q5_report_needs_verbatim` |
| [SECOND REPORT NEED], [THIRD REPORT NEED] and their counts [N TOP NEED], [N SECOND NEED], [N THIRD NEED] | *read*: brand question 5, `q5_report_needs_verbatim`. Group the answers by what founders asked to have counted (in their words: "photos", "what people said", "whether anyone used the code"), count distinct brands per group, and list the three most named. A need named by fewer than two founders is left out; so is a line you cannot fill |
| [TOP BLOCKER] | The top brand objection code (`objection_1` to `objection_3`) |
| [ONE SENTENCE THE NOTES SUPPORT] | *read*: one sentence you could defend from at least three founders' verbatims; if you can't, delete the line |
| [QUOTE] | One verbatim line, only from a row with `quote_ok_to_share` = Y, never with a name |
| [TIME PERIOD: two weeks] | The span of your call dates, in words |

---

## Post 1 · What [OFFICE CONVERSATIONS] office managers told me about free product from brands

```message
id: cpg-post-offices
side: community
stage: discovery
touch: post
channel: slack
ask: what has worked for founders who seeded offices
---
*What [OFFICE CONVERSATIONS] office managers in Flatiron told me about free product from brands*

Context: I'm researching whether to start an office sampling service, so weigh this accordingly. Not selling anything here.

Over the last [TIME PERIOD: two weeks] I've asked people who run office pantries around Flatiron, NoMad and Union Square how their pantries actually work. Sharing what I heard in case it helps anyone thinking about office sampling. Small sample, one neighborhood, so treat it as a field note, not research.

• [N GET BRAND OFFERS] of [OFFICE CONVERSATIONS] said brands already offer them free product. What usually happens to it: [WHAT HAPPENS TO IT].
• In [N ONE PERSON DECIDES] offices one person can say yes alone. In the rest it goes to [WHO ELSE DECIDES].
• What gets a yes: [TOP YES REASON]. What gets a no: [TOP NO REASON].
• Tuesday headcounts ran from [TUESDAY RANGE] people.
• [N WOULD PHOTO AND SURVEY] of [OFFICE CONVERSATIONS] said they'd take a shelf photo and post a short survey link if asked.

One line that stuck with me: "[QUOTE]"

Founders who've seeded offices in New York: what worked, and what didn't?
```

## Post 2 · What [BRAND CONVERSATIONS] snack and drink founders said about sampling

```message
id: cpg-post-brands
side: community
stage: discovery
touch: post
channel: slack
ask: what would make office sampling worth paying for
---
*What [BRAND CONVERSATIONS] snack and drink founders told me about sampling in New York*

Context: I'm researching whether to start an office sampling service, so weigh this accordingly. Not selling anything here.

I've spent the last [TIME PERIOD: three weeks] asking founders how they get people in New York to try their product. [THANKS LINE] A summary, with no names:

• Quarterly sampling spend ran from [BRAND SPEND RANGE], and in most cases [WHO SIGNS OFF] signs off on it.
• [N SEEDED OFFICES] of [BRAND CONVERSATIONS] have sent product to offices. The usual result: [WHAT HAPPENED].
• What founders want back from any sampling: [TOP REPORT NEED].
• What stops them: [TOP BLOCKER].

The pattern I keep hearing: [ONE SENTENCE THE NOTES SUPPORT].

If you've paid for sampling that you could actually measure, what did the report show you?
```

`[THANKS LINE]` is "Thank you to everyone here who gave me time." only if at least one of those founders came through this community (`call_notes` says "asked in Startup CPG"); otherwise delete it. `[WHO SIGNS OFF]` is brand question 2's second half (who approves the spend), the most common answer. The median number named for office placement is deliberately not in this post: it is pricing evidence for you, and posting it reads as an anchor for a sale.

## Post 3 · What [BRAND CONVERSATIONS] founders said they want counted

```message
id: cpg-post-counting
side: community
stage: discovery
touch: post
channel: slack
ask: what counts do founders get from their sampling today
---
*What [BRAND CONVERSATIONS] snack and drink founders said they want counted after sampling*

Context: I'm researching whether to start an office sampling service, so weigh this accordingly. Not selling anything here.

I asked [BRAND CONVERSATIONS] founders what a sampling report would need to show for them to do it again. What they named, most-mentioned first, in their words:

• [TOP REPORT NEED] ([N TOP NEED] of [BRAND CONVERSATIONS])
• [SECOND REPORT NEED] ([N SECOND NEED] of [BRAND CONVERSATIONS])
• [THIRD REPORT NEED] ([N THIRD NEED] of [BRAND CONVERSATIONS])

The most common complaint about reports they had received: [TOP REPORTING COMPLAINT].

What do you get counted from your sampling today?
```

Every line is something founders said, counted from `q5_report_needs_verbatim`: no list of what anyone "should" ask for, and no word about vendors. `[TOP REPORTING COMPLAINT]` is the most common answer to brand question 5 phrased as a complaint, in the founders' words; if fewer than three founders said anything like it, delete that sentence. If fewer than two needs were named by two or more founders, do not post this one.

---

## Why the posts read this way

- **The CPG founder** reading these has been pitched in this Slack before. Each post gives them something they can use without talking to you: counts from real conversations, in other founders' words. It says up front that the poster is researching a sampling service, so nobody later feels they were marketed to without knowing. The question at the end invites their experience, not their budget.
- **The moderator** sees no link, no name, no offer, no advice on what to buy and no DM bait.
- **Honesty**: "small sample, one neighborhood"; numbers as "6 of 15"; quotes only with permission. Post 3 used to list the counts "any sampling vendor" should give, which is this business's own selling point (the plan: keeping the rungs separate "is a selling point"); it now reports only what founders said they want counted.

## Changelog

- Round 1 (2026-10-24): drafted three posts with slots mapped to the plan's two call guides; community size and the missing public rules checked on startupcpg.com (opened 2026-10-24).
- Round 2 (2026-10-24): "the last two weeks" and the thank-you to the community became slots, so neither is claimed unless true.
- Merge (2026-10-24): every slot's source is now the tracker field that holds it (the Scorecard block "Numbers for the Startup CPG posts"), with the uncoded ones marked *read*; the leftover "name the field when the template is final" note removed.
- Review round 1 (2026-10-24): every post opens with a one-line disclosure that the poster is researching an office sampling service; Post 3 rewritten from "the counts I'd ask any sampling vendor for" (the service's own selling point, posted to its buyers) to what founders said they want counted, with counts from `q5_report_needs_verbatim`; the "vendor who blends them" line deleted.
