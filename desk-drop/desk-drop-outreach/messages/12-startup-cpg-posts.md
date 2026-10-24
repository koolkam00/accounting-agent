# 12 · Startup CPG posts: sharing what discovery found

Version 1.0 · 2026-10-24 · Part A of workstream E · folder `desk-drop-outreach/messages/`

**What it is for.** Three short posts for the Startup CPG Slack that share what the discovery conversations found, with every number in a bracketed slot filled from your own notes. The plan calls an honest findings post "the best lead magnet you have" and is clear that cold selling inside the community is not allowed. These posts sell nothing.

**About the community.** Startup CPG describes itself as free to join, with a Slack of "40,000+ Members" (https://startupcpg.com/join/ and https://startupcpg.com/, opened 2026-10-24). The plan's figure of 15,000 to 22,000 is older; the posts state no member count. The community's own posting rules were not found on its public site (its Terms of Service page returned "not found" on 2026-10-24): **unverified, founder to confirm.** Read the workspace's pinned rules and each channel's description before the first post, and post only where findings and questions fit.

**When it is used.**

| Post | Post it when | Earliest likely date (derived, founder to confirm) |
| --- | --- | --- |
| 1 · Offices | At least 8 office conversations are logged (`call_date` filled on 8 office rows) | Tue 2026-11-10 |
| 2 · Brands | At least 8 brand conversations are logged | Thu 2026-11-12 |
| 3 · Counting | After Gate 0 (Fri 2026-11-13), with 15 or more of each logged | Tue 2026-11-17 |

Not before `startup_cpg_joined = Y`. Tuesday to Thursday, mid-morning.

## Rules for every post and every reply under it

1. **No pitch, no name, no link.** The business is not named (the name check holds public use: desk-drop-legal-pack/name-check-log.md), there is no website link, no "DM me", no "we're looking for brands", no price.
2. **Only numbers from your notes.** Every `[SLOT]` comes from the tracker (the table below). If a slot cannot be filled from the notes, delete that line. Never round up, never "about half" when it is 6 of 15: write "6 of 15".
3. **No one identifiable.** No company names, no names, no detail that points to one office or brand. A quote only with the person's yes, given on the call or by email, and without their name.
4. **The ask is a question to the community**, never "who wants to try it".
5. **If someone asks what you do**, answer in the thread, in one line, and move it to a direct message only if they ask: "I'm testing a way to get emerging brands into office pantries around Flatiron with photos and a short report. Still at the research stage. Happy to share more by DM if useful." Then follow their lead. Anyone who messages you this way may go into Clay with `channel = warm-intro` and `call_notes` "asked in Startup CPG".
6. **Never message someone because they reacted or replied.** Only if they ask.

## Where each slot comes from

The call guides and post-call note template are in `calls/` (Part B); the counts below are what those notes record. Name the field in the note template that holds each one when the template is final.

| Slot | Source |
| --- | --- |
| [OFFICE CONVERSATIONS] / [BRAND CONVERSATIONS] | Count of Clay rows on that side with `call_date` filled and `status` at `call_done` or later |
| [N GET BRAND OFFERS] | Office guide question 3 ("Do brands ever reach out offering free product?"): count of yes |
| [WHAT HAPPENS TO IT] | Question 3, second half: the most common answer, in your words |
| [N ONE PERSON DECIDES] | Count of offices where the person said they can say yes alone (the Gate 0 "pantry owner" test) |
| [WHO ELSE DECIDES] | The most common other approver named (facilities, HR, the CEO's assistant) |
| [TOP YES REASON] / [TOP NO REASON] | Question 4: the most common answer on each side |
| [N WOULD PHOTO AND SURVEY] | Question 5: count of yes |
| [TUESDAY RANGE] | Question 2: lowest and highest Tuesday headcount given, as a range |
| [N USE A SERVICE] | Question 1: count using a snack delivery service or vendor |
| [BRAND SPEND RANGE] | Brand guide question 2: lowest and highest quarterly sampling spend named, as a range |
| [N SEEDED OFFICES] | Brand guide question 3: count who have seeded offices |
| [WHAT HAPPENED] | Brand question 3, the most common outcome |
| [MEDIAN NUMBER NAMED] | Brand question 4: the median of the numbers named before any price was mentioned (the Gate 0 record) |
| [TOP REPORT NEED] | Brand question 5: the most common answer |
| [TOP BLOCKER] | Brand question 7: the most common answer |
| [QUOTE] | One verbatim line from `call_notes`, used only with that person's yes, no name |

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

I've spent the last [TIME PERIOD: three weeks] asking founders how they get people in New York to try their product. [THANKS LINE] A summary, with no names:

• Quarterly sampling spend ran from [BRAND SPEND RANGE], and in most cases [WHO SIGNS OFF] signs off on it.
• [N SEEDED OFFICES] of [BRAND CONVERSATIONS] have sent product to offices. The usual result: [WHAT HAPPENED].
• What founders want back from any sampling: [TOP REPORT NEED].
• What stops them: [TOP BLOCKER].

The pattern I keep hearing: [ONE SENTENCE THE NOTES SUPPORT].

If you've paid for sampling that you could actually measure, what did the report show you?
```

`[THANKS LINE]` is "Thank you to everyone here who gave me time." only if at least one of those founders came through this community (`call_notes` says "asked in Startup CPG"); otherwise delete it. `[WHO SIGNS OFF]` is brand question 2's second half (who approves the spend), the most common answer. The median number named for office placement is deliberately not in this post: it is pricing evidence for you, and posting it reads as an anchor for a sale.

## Post 3 · Delivered is not tried: the counts I'd want from any sampling

```message
id: cpg-post-counting
side: community
stage: discovery
touch: post
channel: slack
ask: what counts do founders get from their sampling today
---
*Delivered is not tried: the counts I'd ask for from any sampling program*

After [BRAND CONVERSATIONS] founder conversations, the most common complaint about sampling was [TOP REPORTING COMPLAINT]. Here's the list of counts I'd ask any sampling vendor for, kept separate:

1. Delivered: how many units reached the location.
2. Placed: how many were actually put out, with a photo.
3. Depleted: how many were gone by a set day.
4. Responded: how many people answered a question about it, and how many of them say they tried it.
5. Scanned: how many scanned a code.
6. Purchased: how many used a discount code.
7. Incremental: whether any of those purchases would not have happened anyway. Almost nobody measures this, and a report should say so.

Each number answers a different question, and a vendor who blends them is selling you the biggest one.

What counts do you get from your sampling today?
```

`[TOP REPORTING COMPLAINT]` is the most common answer to brand question 5 phrased as a complaint ("reports that count boxes shipped, not samples tried"). If fewer than three founders said anything like it, delete the first sentence and start at "Here's the list".

---

## Why the posts read this way

- **The CPG founder** reading these has been pitched in this Slack before. Each post gives them something they can use without talking to you: counts from real conversations, a list they can hand to any vendor. The question at the end invites their experience, not their budget.
- **The moderator** sees no link, no name, no offer and no DM bait.
- **Honesty**: "small sample, one neighborhood"; numbers as "6 of 15"; quotes only with permission; Post 3's seven counts are the plan's measurement ladder, in its own words.

## Changelog

- Round 1 (2026-10-24): drafted three posts with slots mapped to the plan's two call guides; community size and the missing public rules checked on startupcpg.com (opened 2026-10-24).
- Round 2 (2026-10-24): "the last two weeks" and the thank-you to the community became slots, so neither is claimed unless true.
