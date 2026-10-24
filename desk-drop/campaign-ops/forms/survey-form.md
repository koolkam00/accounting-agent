**Draft for attorney review. Not legal advice.** (The notice text on these forms is the legal pack's, file 13 v0.6. Use the live form only after the attorney hour has cleared file 13.)

# The employee survey and the optional newsletter sign-up (Google Forms)

One survey form per campaign, copied from a master, writing to its own tab in the tracker. The office is carried by the link: each office's QR code and post link open the form with a **Card code** already filled in, for example `CMP-003.O-007`. Nothing about a person is in the link or the form. The source of every question, option and setting below is `spec/forms.json`.

Why Google Forms: you already have the Google account (Workspace), it writes straight into the tracker, it has no sign-in when set up as below, and you can fix it from a phone. Why one form per campaign: the brand's name is in the questions, exactly as the plan words them ("Did you try [Brand]?"), each campaign's answers land in their own tab, and the newsletter link (only for brands that chose it) can sit on that campaign's thank-you screen.

## How the office is captured, exactly

1. Each campaign's form has a short-answer question **Card code (filled in for you)**.
2. Google's pre-filled link puts a value into that question from the web address: `...viewform?usp=pp_url&entry.123456789=CMP-003.O-007`. The number after `entry.` is Google's ID for the question; you never type it, you copy it once per campaign (step 9 below).
3. The tracker builds every office's address from that one link (`links` tab, `destination_url`): it replaces the text `CARDCODE` with `<campaign_id>.<office_id>` and adds labels (`utm_source=office-pantry`, `utm_medium=qr` or `post`, `utm_campaign`, `utm_content`). Google Forms ignores the `utm_` labels; they keep each address self-describing in the link tool, and they work unchanged if the survey ever moves to a web page that reads them.
4. The short link on the card (`https://go.[DOMAIN]/c003-o007-q`) redirects to that address. The Slack or email post uses a second short link (`...-p`) to the same address, so a click from Slack is never counted as a QR scan.
5. The answer arrives in the campaign's tab with the card code in column B. The tracker counts an answer for an office only when column B is exactly that office's card code and the time is inside the window (T to the end of T+4). An edited or missing code is shown as "unmatched" and is not counted for any office.

What this cannot do: stop one person answering twice (only a sign-in could, and a sign-in would end the anonymity), or stop someone editing the code (then the answer is simply not counted). The report's fixed limitations paragraph already says the survey is anonymous and self-selected.

## Part 1 · Build the master survey once [FOUNDER LOGIN: Google]

1. forms.google.com, Blank form. Drive file name: `survey master` (never the company name in a file name).
2. Title: `Three quick questions about [BRAND]`.
3. Description, word for word (legal pack file 13, Part A): *Anonymous. No name, no login, no email needed. Your answers go into a short report for [BRAND] and a summary for your office. We may quote your comment word for word, so please leave your name out of it. How we handle this: [PRIVACY URL]*. `[PRIVACY URL]` is `survey_privacy_url` on the tracker's config tab (`https://[DOMAIN]/survey-privacy`, hosted by the website).
4. Settings > Responses: **Restrict to users in [your domain] and its trusted organizations: OFF.** This one matters most. A form made in a Google Workspace account is restricted to your own organization by default: with it on, every employee of an office who scans a card meets a Google sign-in and cannot answer, so no responses, Gate 2 missed, and the notice's "no login" untrue (Google Workspace help, support.google.com/a/users/answer/9303071, opened 2026-10-24: "By default, access is restricted to people inside your organization"; to let outsiders respond, "turn off 'Restrict to users in [your-company.com] and its trusted organizations'"). A copy of the master keeps the setting, but check it on every campaign's form (Part 2, step 8). **Collect email addresses: Do not collect.** **Limit to 1 response: off** (it would force a Google sign-in; Google's help, support.google.com/docs/answer/2839588, opened 2026-10-24). **Allow response editing: off.**
5. Settings > Presentation: progress bar off; **Show link to submit another response: off**; **View results summary: off** (respondents must never see other people's answers); confirmation message: set per campaign (Part 2).
6. Settings > Defaults: "Make questions required by default" off.
7. The questions, in this order (the column letters are where Google will write them, and the tracker reads them by position):

| Section | Question | Type | Required | Options | Column |
| --- | --- | --- | --- | --- | --- |
| 1 | Card code (filled in for you) · help: *From the card's link, so we know which office this came from. Please leave it as it is.* | Short answer | No | | B |
| 1 | Did you try [BRAND]? · help: *[PRODUCT]* | Multiple choice | Yes | Yes → go to section 2; No → go to section 3 | C |
| 2 "You tried it" | How was it? | Linear scale 1 to 5, labels *Not for me* and *Loved it* | Yes | | D |
| 2 | Would you buy it? | Multiple choice | Yes | Yes, Maybe, No | E |
| 3 "You didn't try it" | What happened? | Multiple choice | Yes | Didn't see it, Not for me, Gone by the time I looked | F |
| 4 "Last one" | Anything you'd tell [BRAND]? (optional) · help: *Please leave out your name and anyone else's.* | Paragraph | No | | G |

   After section 2, continue to section 4; after section 3, continue to section 4; after section 4, submit. Column A is Google's Timestamp.
8. No file-upload question, ever (file 13, D3). Do not link the master to a spreadsheet.

## Part 2 · One survey per campaign, at T-4 (about 10 minutes) [FOUNDER LOGIN: Google]

1. In Drive, right-click `survey master` > Make a copy. Name it `<campaign_id> survey`, for example `CMP-003 survey`.
2. Replace `[BRAND]` in the title, the description, "Did you try [BRAND]?" and "Anything you'd tell [BRAND]?". Replace `[PRODUCT]` in the help line under "Did you try" with the product as on the card. Copy both from the campaign row (brand_name, product_sku).
3. Settings > Presentation > Confirmation message: `Thank you. Your answers are anonymous.` Then, only if the brand chose the newsletter (campaigns, newsletter_option = Y), a second line: `Want [BRAND]'s newsletter and a discount code? Optional, ten seconds: [NEWSLETTER FORM LINK]` (Part 3). Then, only if the brand gave a landing page: `More from [BRAND]: [landing_url]?utm_source=office-pantry&utm_medium=survey&utm_campaign=<campaign_id in lower case>`. Whether Google makes links in the confirmation message clickable is unverified, founder to confirm in step 8; if it does not, put the same line in a final "title and description" item at the end of section 4 instead.
4. Responses > Link to Sheets > **Select existing spreadsheet** > the tracker. Google adds a new tab (for example `Form Responses 3`). Rename that tab to exactly the campaign_id (`CMP-003`). Never insert, delete or move columns in it.
5. Check the new tab's first row reads: Timestamp, Card code (filled in for you), Did you try [your brand]?, How was it?, Would you buy it?, What happened?, Anything you'd tell [your brand]? (optional). The campaigns tab's `checks` column warns if column B is not the card code.
6. Copy the form's Send link (the eye icon > address bar) into campaigns, `survey_form_url`.
7. More (⋮) > **Get pre-filled link**. In "Card code", type exactly `CARDCODE` (capitals, nothing else). Get link > Copy link. Paste it into campaigns, `survey_prefill_template`. (Google's steps: support.google.com/docs/answer/2839588, opened 2026-10-24.)
8. Test it as an outsider, never signed in: open any office's `destination_url` from the links tab **in a private or incognito window, or on a phone signed out of Google**. It must open with no sign-in (a test signed in to your own Workspace account passes even when outsiders are blocked: step 4 of Part 1). The card code must show that office and campaign; the brand name must be right. Do the same with the sign-up form's link, if there is one. Answer it if you like, then delete that test answer (Responses > Individual > Delete; support.google.com/docs/answer/2917686, opened 2026-10-24). A test before the drop day would not be counted anyway.
9. Run `python3 tools/make_links.py` (README, step 12) and import the links into the link tool.

## Part 3 · The newsletter sign-up, only for brands that chose it [FOUNDER LOGIN: Google]

Where the consented emails live (this workstream's decision): **only in this one small Google Form's own responses, for that campaign.** The form is never linked to a spreadsheet, so no address ever reaches the tracker, a survey tab, a report or an export. It has no card code and no office, so no address is ever stored with an answer. The tracker records only dates and a count.

**What this does not do, said plainly (review round 1, R1-08).** Google time-stamps every response in both forms, and the sign-up is reached from the survey's thank-you screen, so a sign-up usually arrives seconds after that person's survey answer. Someone holding both forms' responses could match the two by time, and so link an address to an answer and its office. The build keeps that from happening in practice, not in principle: you never open the sign-up responses and the survey tab side by side, never compare their times, never download the sign-up responses with their time stamps, and you open the sign-up form only at T+5, to copy the ticked addresses into an alphabetical list with nothing else (D7); the brand gets the list only, with no times. The notice must not say an email "cannot be joined" to answers.

Master (once): a new form, Drive name `newsletter master`, title `[BRAND] newsletter (optional)`, description: *Want [BRAND]'s newsletter and a discount code? Your email goes to [BRAND] once, as a list of addresses only, kept apart from survey answers. How we handle this: [PRIVACY URL]* (file 13, Part B and Part C). Settings as the survey: **Restrict to users in [your domain]: OFF** (as in Part 1, step 4), no email collection, no sign-in, no editing, no summary. Two questions:

| Question | Type | Required | Options |
| --- | --- | --- | --- |
| Email (optional) | Short answer, response validation: text, email address | No | |
| Consent (optional) · help: *[BRAND]'s privacy policy: [BRAND PRIVACY POLICY URL]* | Checkboxes | No | One box: **Share my email with [BRAND] under its privacy policy.** (file 13, Part B, word for word; it starts unticked) |

Confirmation message: *Thanks. If you ticked the box, [BRAND] gets your email once, within a week; after that its privacy policy applies. To change your mind, write to [EMAIL].*

Per campaign: copy the master, name it `<campaign_id> newsletter sign-up`, fill `[BRAND]` and the brand's privacy link (campaigns, brand_privacy_url), **do not link it to a spreadsheet**, copy its Send link into campaigns `newsletter_form_url` and into the survey's confirmation message (Part 2, step 3).

How the addresses pass to the brand, once (T+5; file 13, D7):
1. Open the sign-up form > Responses > Individual. For each response: box ticked and a real address: copy the address into the draft from `tools/make_messages.py ... newsletter` (template 09), one per line. Box not ticked: delete that response now (it is never passed on; D8).
2. Sort the list alphabetically. No answers, dates, offices or anything else. Send it to the brand contact.
3. On the campaigns tab log `newsletter_passed_date`, `newsletter_passed_count` (a number only) and `newsletter_unticked_deleted_date`.
4. Turn off "Accepting responses" on the sign-up form.

When they are deleted: unticked ones at T+5 (above). Everything else **30 days after passing on** (the date is in the tracker's checks and in the SOP calendar): Responses > More > Delete all responses; then delete the form itself and empty Drive's trash; delete the sent email from Sent and empty Gmail's trash. Log `newsletter_deleted_date`. If someone writes to withdraw before then: if not yet passed on, delete their response; if passed on, ask the brand to delete it (file 13, Part C).

## Part 4 · Closing and keeping

- **T+4, end of day:** Responses > turn off "Accepting responses" on the campaign's survey (and its sign-up form). Answers that still arrive later are not counted (the tracker shows them as outside the window).
- **12 months after the campaign** (file 13, D8): first freeze its totals: `python3 tools/freeze_survey.py tracker.xlsx CMP-003 out/` and import `survey-frozen-CMP-003.csv` into the tracker's `survey_frozen` tab (File > Import > Upload > Append to current sheet). The campaign's numbers on the campaigns tab must not change. Then delete the campaign's tab in the tracker, Delete all responses in the form, delete the form. Log `answers_deleted_date`. Without the freeze, deleting the tab would turn every survey number for that campaign into 0, in the tracker and in any later export; the campaign's checks say so. Note: Google Sheets keeps version history, so a deleted tab can still be restored from an old version until the file itself is deleted (a question for the attorney hour, below).

## Settings that keep the notice true (legal pack file 13, Part D)

| D | How this build meets it |
| --- | --- |
| D1 no sign-in | **Restrict to users in [your domain] and its trusted organizations: OFF** on every form (a Workspace form is restricted to your organization by default), checked by opening the link signed out (Part 2, step 8); Limit to 1 response off; nothing else here needs a sign-in. The optional script also calls `setRequireLogin(false)`, which Google's reference marks deprecated, so the manual check stays |
| D2 no email collection | Collect email addresses: Do not collect, on every form |
| D3 no file upload | No upload question |
| D4 office from the link | Card code pre-filled from the short link; it carries only `<campaign_id>.<office_id>` |
| D5 email optional, only for brands that chose it, unticked | Separate sign-up form, made only when newsletter_option = Y; both fields optional; the box starts unticked |
| D6 response sheet shared with no one | The tracker and its survey tabs are the founder's only; a backup person gets the printed route sheet, not the tracker |
| D7 list of addresses only, once, within seven days of T+4 | T+5, template 09, from the sign-up form, never from a sheet |
| D8 deletion reminders | In the tracker's checks and in every drop's SOP calendar (.ics) |
| D9 brand gets totals and at most three comments; offices never get rows | Report generator; office summaries list totals and comments only, give only the count where an office gave fewer than five answers for a brand, and show no rating or would-buy split drawn from fewer than five people (config `office_summary_min_answers`, raised from three in review round 1: with three raters a split is one person per answer), so no one's rating or comment can be picked out |
| D10 names removed before quoting | Brand report: the comment fields on campaigns; the report generator refuses a quote that is not word for word apart from [name removed] and [...]. Office summaries: the generator replaces every capitalized word that does not start a sentence (other than the brand, product, retailer, office and weekday names) with [name removed]; it over-removes on purpose and cannot see a name that starts a sentence, so you still read each summary once before sending |
| D11 aggregate link counts only | The scans tab holds totals read from the link tool's dashboard; no per-click log is ever exported |

## For the attorney hour (legal pack file 08)

1. This build keeps the optional email in a separate sign-up form, never stored with answers. File 13, Part C says "Because answers are anonymous, we cannot find yours to change or delete it unless you gave an email address." **Keep that caveat** (an earlier draft of this page suggested dropping it; withdrawn in review round 1): both forms time-stamp every response, so a sign-up made from the survey's thank-you screen could be matched to the answer just before it. The founder never does so (Part 3), but it is possible. Optional, the attorney's call: delete the sign-up responses right after passing the list on at T+5, instead of 30 days later (D8), which removes the window in which they could be matched.
2. Processors to name in the notice (file 13, open point 2): Google (Forms, Sheets, Gmail, Drive) and the link tool (Short.io by default; links/QR-AND-LINKS.md).
3. Google Sheets version history keeps deleted rows and tabs until the file is deleted. Is deleting the tab and the form's responses enough for "we delete answers after 12 months", or should the tracker be copied to a fresh file each year (a copy starts with no history)?
