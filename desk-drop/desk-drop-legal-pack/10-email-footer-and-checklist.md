**Draft for attorney review. Not legal advice.**

# 10 · Commercial-email footer and three-line checklist

Version 0.2 · 2026-10-24 · Part of the legal pack, file 10 of the founder's order of use.

**What it is for.** Every cold email and follow-up to an office or a brand is commercial email under the federal CAN-SPAM Act, which has no exception for business-to-business email (FTC guide, opened 2026-10-23, source at the end). This file holds the footer to paste under every such email and the three rules to follow every time you send.

**When it is used.** From the first outreach email in week 1 (Monday 2026-10-26, derived, founder to confirm) until the business stops sending commercial email. Set it up once in the email tool before the first send.

---

## The footer

Paste one of these versions at the bottom of every outreach email, first touch and every follow-up.

**The company name lives on this one line. A rename is this edit, then re-paste the footer:**

`BRAND_NAME = Desk Drop`

Every `{BRAND_NAME}` below means the name on that line. The outreach workstream's templates use the same variable name. When you paste a footer into Gmail by hand, type the name in place of `{BRAND_NAME}`.

The name is a working name. Run the name check first (file 01, the name-check log; plan, week 1 days 1 and 2). If it turns up a conflict, change the line above before the first send. Leave `[WEBSITE]` out until the site is public; the plan keeps it private until Gate 1 and name clearance.

### Footer A: use when the email has no signature block

```text
[FOUNDER NAME] · {BRAND_NAME} · [PHONE] · [WEBSITE]
[POSTAL ADDRESS]
This is a business pitch, sent one to one. Not interested? Reply "no thanks" and I won't email you again.
```

### Footer B: use under the brand-identity email signature

The signature from the identity workstream already shows your name, the company, [PHONE], [WEBSITE] and [POSTAL ADDRESS]. Add only the last line:

```text
This is a business pitch, sent one to one. Not interested? Reply "no thanks" and I won't email you again.
```

If the signature you are using does not show [POSTAL ADDRESS], use Footer A instead. The address is the one part the law requires in every message.

### HTML version, for an email tool that takes HTML

```html
<p style="font-size:13px;line-height:1.5;color:#333333;margin:16px 0 0 0;">
  [FOUNDER NAME] · {BRAND_NAME} · [PHONE] · [WEBSITE]<br>
  [POSTAL ADDRESS]<br>
  This is a business pitch, sent one to one. Not interested? Reply "no thanks" and I won't email you again.
</p>
```

Keep the opt-out line at normal size and dark text. The FTC says the opt-out explanation must be "clear and conspicuous"; tiny grey text works against that.

---

## The three-line checklist

1. **Every commercial email carries the footer**: a real [POSTAL ADDRESS] (a street address, a USPS post office box, or a private mailbox registered with a commercial mail receiving agency) and the "reply no thanks" line, in normal-size text.
2. **Nothing in the header or subject misleads**: the From name is [FOUNDER NAME], the address is at [DOMAIN], replies reach you, and the subject line says what the email is about (no "Re:" on a first email).
3. **Every opt-out is honored the same day and never reversed**: mark the contact `do_not_contact = Y` in the Clay table that day (the legal outer limit is 10 business days), keep the reply address working for at least 30 days after each send, and never sell or share an opted-out address.

---

## Notes behind the checklist

- **What counts as an opt-out.** Any reply that says, in any words, stop, no, not interested, unsubscribe or remove me. Do not ask for a reason. Do not ask them to confirm. Do not send a "sorry to see you go" email. The law does not allow you to require anything beyond a reply or a single web page, or to charge a fee.
- **Why "reply no thanks" and not an unsubscribe link.** A reply is an opt-out method the FTC guide names ("a return email address"). It needs no software and no paid plan. If the outreach tool later adds an unsubscribe link, keep the reply line as well.
- **"This is a business pitch."** The law asks that a commercial email be identified as an advertisement or solicitation, clearly and conspicuously, and gives "a lot of leeway" in how (FTC guide). One plain sentence does it without sounding like spam. Attorney to confirm the wording is enough.
- **Which address to use for [POSTAL ADDRESS].** Every cold email will carry it, so a home address becomes public. A USPS post office box or a registered private mailbox both qualify under the FTC guide. The cost of either was not researched: needs quote, founder to decide. Use the same address in the identity workstream's signature.
- **Emails that do not need the footer.** Messages whose main purpose is to run an agreed campaign (drop-day times, photo requests, invoices, the report) are "transactional or relationship" messages under the FTC guide and are exempt from most of the rules. The FTC reads that category narrowly: once an email also pitches something new (a renewal, another campaign), treat it as commercial and add the footer. Adding the footer to everything is simplest and costs nothing.
- **LinkedIn messages** are not email, but honor a "no" there the same way: mark `do_not_contact = Y`.
- **Penalties.** The FTC guide states up to $53,088 per separate email in violation (as adjusted in January 2024). This is why the rules are checked on every send, not occasionally.
- **Anyone sending for you.** If you ever use a sending service or a helper, you remain responsible (FTC guide: you "can't contract away your legal responsibility").

## Source

- FTC, "CAN-SPAM Act: A Compliance Guide for Business", page dated August 2023, edited January 2024. https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business (opened 2026-10-23). Supports every rule above: header, subject, ad identification, postal address types, opt-out method, 10 business days, 30 days, no fee, no selling addresses, no B2B exception, transactional messages, penalty amount.
