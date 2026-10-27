when: T+5, once, only if the brand chose the newsletter option and someone ticked the box (legal pack file 13, D7)
to: {brand_contact_name} <{brand_contact_email}>
subject: {count} newsletter sign-ups from the {drop_date_long} campaign
---
Hi {brand_contact_first},

{count} people at the offices asked for your newsletter and ticked "Share my email with {brand_name} under its privacy policy." Their addresses are below, sorted alphabetically. This is the only time we send them: no answers, dates or offices are attached, and from now on your privacy policy applies. We delete our copy within 30 days.

[PASTE THE ADDRESSES HERE, ONE PER LINE, FROM THE SIGN-UP FORM: TICKED BOXES ONLY]

{founder_name}
---
After sending: log newsletter_passed_date and newsletter_passed_count (a number, never the addresses) on the campaigns tab; delete the unticked responses in the sign-up form today; set a reminder for {delete_by_long} to delete every response, the form and this sent email (and empty the trash).
