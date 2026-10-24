**Draft for attorney review. Not legal advice.**

# 13 · Survey privacy notice

Version 0.2 · 2026-10-24

**What it is for.** The employee survey promises anonymity (plan, "The employee survey"; legal table row "Privacy"). This file is what employees read before they answer, in two layers: a short notice at the top of the form and a full notice one tap away. It also fixes the exact consent wording for the optional email and the form settings that keep every sentence here true.

**When it is used.** Built when the survey form is built (plan, setup checklist "At Gate 0 pass"); live from campaign zero (drop Tuesday 2027-01-12, derived, founder to confirm). The operations workstream builds the form; the website workstream hosts the full notice if there is a site, otherwise it is a public page in the form tool or a shared document.

**How to edit.** Replace `[BRAND]`, `[BRAND PRIVACY POLICY URL]`, `[EMAIL]`, `[POSTAL ADDRESS]` and `[PRIVACY URL]` per campaign. The company's name appears once, in the full notice's first line. If any setting in Part D changes, re-read the notice: it must still be true.

---

## Part A · Short notice: the first thing on the survey form

> **Anonymous. No name, no login, no email needed.** Your answers go into a short report for [BRAND] and a summary for your office. We may quote your comment word for word, so please leave your name out of it. How we handle this: [PRIVACY URL]

(45 words. Keep it above the first question.)

## Part B · The optional email question, word for word

Show only if the brand chose the newsletter option in its agreement (file 12, Part 1).

> Want [BRAND]'s newsletter and a discount code? Email (optional): [ field ]
> ☐ Share my email with [BRAND] under its privacy policy. [link: BRAND PRIVACY POLICY URL]

Rules: the box starts unticked. An email with the box left unticked is deleted, not passed on. The checkbox text is the plan's text (appendix I, item 5) and must not be pre-ticked or reworded into a broader consent.

## Part C · Full notice: the page at [PRIVACY URL]

<!-- NOTICE START -->

**Draft for attorney review. Not legal advice.**

### Survey privacy notice

Last updated [DATE]. This survey is run by **Desk Drop LLC** ("**we**", "**us**"), which brings products from emerging snack and drink brands to offices. Questions: [EMAIL], [POSTAL ADDRESS].

#### What we collect

- Your answers to the survey questions, and your comment if you write one.
- Which office the survey link came from (it is built into the link on the card and in your office's post) and when you answered.
- Your email address, only if you choose to give it for the brand's newsletter.

#### What we do not collect

We do not ask for your name, your work email, a login or an employee ID. We do not ask your employer for anything about you, and your employer does not see your individual answers from us except comments, which we may quote word for word in the office summary.

#### Technical information

The services that run the survey form and the short link on the card process technical information, such as IP address and device type, to deliver the page, under their own privacy policies. We set them up not to ask you to sign in. From the short link we see only totals, such as how many times it was opened and on which days.

#### How we use your answers

To write a one-page report for the brand and a summary for your office, and to improve how we run these drops. We do not sell your answers or use them for advertising to you.

#### Who sees what

- **The brand** gets totals (how many people answered, how many tried it, the average rating, how many would buy) and up to three comments quoted word for word, without any email address.
- **Your office** gets a summary of your team's answers, which may include comments quoted word for word.
- Comments are quoted as written, except that we remove any name we find. Please leave out your name and anything that identifies you or anyone else.

#### If you give your email

We pass it to [BRAND] only if you tick the box. We send the brand those addresses once, as a list kept separate from survey answers, within seven days after the survey closes. After that, [BRAND]'s privacy policy applies ([BRAND PRIVACY POLICY URL]) and you can unsubscribe from [BRAND] at any time. We delete our copy within 30 days after passing it on. If you change your mind, write to [EMAIL]: if we have not passed your email on yet, we delete it; if we have, we ask [BRAND] to delete it too.

#### How long we keep answers

We keep survey answers for 12 months after the campaign, then delete them. Reports keep only totals and quoted comments.

#### Your choices

The survey is optional. You can skip it, skip any question or stop at any time. Because answers are anonymous, we cannot find yours to change or delete it unless you gave an email address.

#### Changes

If we change this notice, we update the date above. We will not use answers already given in a way this notice does not describe.

<!-- NOTICE END -->

---

## Part D · Settings that keep this notice true

For the operations workstream (survey form, short links, response sheet) and the website workstream (hosting). Each line is a requirement, not a suggestion. Tool behaviors marked "confirm" were not verified from the tool's own documentation (sources at the end).

| # | Setting | Why |
| --- | --- | --- |
| D1 | No sign-in to open or submit the form. Leave off any setting that requires sign-in (confirm: third-party guides say Google Forms' "Limit to 1 response" requires sign-in) | "No login" |
| D2 | Email collection is off in the form's settings (in Google Forms, Settings > Responses > Collect email addresses, set to not collect) | "No email needed" |
| D3 | No file-upload question | Uploads can require sign-in and could carry identifying data |
| D4 | The office is filled in from the link (a hidden or pre-filled field), never asked as a question; the link carries only office and campaign codes, nothing about a person | "Which office the link came from" |
| D5 | The email field and checkbox are optional and appear only for brands that chose the newsletter option; the box starts unticked | Part B |
| D6 | The response sheet is shared with no one but the founder | "Your employer does not see your individual answers" |
| D7 | Consented emails are exported as a list of addresses only, sorted alphabetically, with no answers, timestamps or office codes, sent to the brand once, within seven days after the survey closes at T+4 | "A list kept separate from survey answers" |
| D8 | Calendar reminders: delete the consented emails 30 days after they are passed on; delete raw answers 12 months after the campaign | Retention promises |
| D9 | Reports show totals and at most three verbatim comments for the brand; office summaries never list answers row by row | "Who sees what" |
| D10 | Before quoting a comment, remove any name or identifying detail that slipped in, and note "[name removed]" | "Leave your name out" is a request, not a guarantee |
| D11 | Short links: use only the link tool's aggregate counts (opens by day). Do not export or keep per-click logs (confirm what the free plan shows) | "We see only totals" |

## Open points for the attorney hour

1. Is "anonymous" the right word when the office can be inferred and comments are quoted? The notice discloses both; the attorney may prefer "we don't ask who you are."
2. Should the notice name the form and link providers (for example Google, Tally, Bitly) once the operations workstream has chosen them? Recommended default: yes, by name, with links to their policies.
3. Retention periods (seven days to pass emails on, 30 days to delete our copy, 12 months for answers) are my defaults; the plan sets none.

## Sources

- Plan, "The employee survey" and appendix I (survey wording and the checkbox text), legal table row "Privacy". plan.md, read 2026-10-23.
- Google Forms help, "View & manage form responses", https://support.google.com/docs/answer/139706 (opened 2026-10-23): describes the "Collect email addresses" options ("Verified", "Responder input"). It did not address sign-in for "Limit to 1 response" or IP addresses, so D1's example is unverified, founder to confirm.
- Bitly analytics (link clicks over time, referrers, aggregated location): Bitly blog pages seen only in a search summary, https://bitly.com/blog/analytics-launch/ : not opened, unverified, founder to confirm.
