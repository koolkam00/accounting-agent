**Draft for attorney review. Not legal advice.** (The form's short notice repeats the website's notice; clear both at the attorney hour.)

# Office intake (founder copy)

The founder-side copy of the website's office form: the same questions and the same CONTRACTS 6.3 columns (`office_intake`), for offices that sign before the website is public, or when you take intake on a call. The website's own form writes to the tracker's `office_intake` tab directly when its script is bound to the tracker (website/SETUP.md section 3; runbook step 6).

Built from `spec/forms.json` by `tools/make_forms_docs.py`. Change the spec, not this page, and rebuild the tracker so its mapping formulas follow.

## Build it once [FOUNDER LOGIN: Google]

1. forms.google.com, Blank form. Drive file name: `Office intake (founder copy)` (no company name in a file name).
2. Title: `Join the drop: office details`. Description: *About 90 seconds. Business details only: please don't tell us about anyone's health or personal life (a veto by ingredient is enough). What this form collects, and why: your contact details and your office's delivery details, so we can plan drops. If we do not end up working together, we delete your answers within 12 months. Draft for attorney review. Not legal advice.*
3. Settings > Responses: **Restrict to users in [your domain] and its trusted organizations: OFF.** A Google Workspace form is restricted to your own organization by default, so with this on, an office manager or brand from another company meets a Google sign-in and cannot answer (Google Workspace help, support.google.com/a/users/answer/9303071, opened 2026-10-24: "By default, access is restricted to people inside your organization"). Collect email addresses: **Do not collect** (the form asks for a work email as a question instead); Limit to 1 response: off; Allow response editing: off. Presentation: View results summary: off.
4. Add the questions below, in this order. Google writes them in this column order on the response tab, and the tracker reads them by position.
5. Responses > Link to Sheets > Select existing spreadsheet > the tracker. Google adds a new tab. **Delete the tracker's placeholder tab `office_form` and rename Google's new tab to exactly `office_form`.** Every formula that reads this tab finds it by name (INDIRECT), so nothing breaks when the placeholder goes (review round 2). The tab `office_intake_founder` then shows each answer in CONTRACTS 6.3 columns, with `source = founder` and `form_version = office-gform-1.0`.
6. **Test it as an outsider:** open the form's Send link in a private or incognito window, or on a phone signed out of Google. It must open with no sign-in. Signed in to your own Workspace account, the test passes even when outsiders are blocked.
7. Send the form's link with the agreement (legal pack file 03) when the office says yes, or fill it in yourself during the call.

## Questions

| Col | Question | Type | Required | Options | Writes column |
| --- | --- | --- | --- | --- | --- |
| B | Company | Short answer | Yes |  | `company` |
| C | Your name | Short answer | Yes |  | `contact_name` |
| D | Your title (optional) | Short answer | No |  | `contact_title` |
| E | Work email | Short answer | Yes |  | `contact_email` |
| F | Work phone (optional) | Short answer | No |  | `contact_phone` |
| G | Office street address | Short answer | Yes |  | `office_address` |
| H | Floor or suite (optional) | Short answer | No |  | `floor_suite` |
| I | People in the office on a typical Tuesday · help: *A whole number. Your best estimate is fine.* | Short answer | Yes |  | `tuesday_headcount` |
| J | Are you the pantry owner? · help: *The person who can say yes to a drop on their own.* | Multiple choice | Yes | Yes, me (writes `Y`); Someone else (writes `N`) | `pantry_owner_is_contact` |
| K | Pantry owner's name (only if someone else) | Short answer | No |  | `pantry_owner_name` |
| L | Pantry owner's title (optional) | Short answer | No |  | `pantry_owner_title` |
| M | How do deliveries reach your office? | Multiple choice | Yes | Walk-up, straight to us (writes `walk-up`); Front desk (writes `front desk`); Loading dock (writes `loading dock`); Something else (writes `other`) | `receiving_type` |
| N | Best time to receive, on a Tuesday or Wednesday morning | Multiple choice, with 'Other' | Yes | 8 to 10 am; 9 to 11 am; 10 am to noon | `receiving_window` |
| O | Does your building ask for a certificate of insurance before a delivery? | Multiple choice | Yes | Yes (writes `yes`); No (writes `no`); Not sure (writes `unsure`) | `coi_required` |
| P | Where would you post the three-question survey link? | Multiple choice | Yes | Slack (writes `slack`); Email (writes `email`); Other (writes `other`) | `survey_channel` |
| Q | Which categories do you want? · help: *Tick "Any of them" or the ones you want.* | Checkboxes | Yes | Any of them; Chips and crisps; Popcorn and puffs; Crackers and pretzels; Bars; Cookies and baked snacks; Chocolate and candy; Nuts, seeds and trail mix; Jerky and meat sticks; Dried fruit and fruit snacks; Sparkling water and soda; Tea, juice and other non-carbonated drinks; Ready-to-drink coffee; Other snacks; Other drinks | `categories_wanted` |
| R | Anything you never want? (optional) · help: *A brand, a category or an ingredient. No one's health details, please.* | Paragraph | No |  | `vetoes` |
| S | Anything else? (optional) | Paragraph | No |  | `notes` |

Column A is Google's Timestamp; it becomes `submitted_at` (text, `YYYY-MM-DDTHH:MM:SS`), the key you copy into the tracker.

## Notes

- Pantry owner: when the answer is "Yes, me", the mapping copies the contact's name and title into `pantry_owner_name` and `pantry_owner_title`, as the website does.
- Categories: "Any of them" writes all 14 keys; otherwise the ticked labels become their keys, separated by semicolons, in CONTRACTS order.
- The pantry owner's own phone and email (when the owner is not the contact) are asked in the participation agreement's top table, not here; the outreach workstream passes them as `pantry_owner_phone` and `pantry_owner_email` (HANDOFF.md).
- Retention: the same 12-month promise as the website form. Rows of offices that never sign are deleted from the response tab and from the form (Responses > Individual > Delete).
