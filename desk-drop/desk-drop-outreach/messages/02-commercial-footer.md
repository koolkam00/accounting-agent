**Draft for attorney review. Not legal advice.**

# 02 · The commercial-email footer and signature

Version 1.4 · 2026-10-24 · Outreach engine (workstream E) · `desk-drop-outreach/messages/`

**What it is for.** The block that ends every outreach email: your signature with [POSTAL ADDRESS], and a visible opt-out line. In every message file here it is written `{SIGNATURE}`.

**Whose text it is.** The footer is the legal pack's, used exactly as written (`desk-drop-legal-pack/02-email-footer-and-checklist.md`, version 0.6, 2026-10-24; its handoff says "E: use the footer exactly as written"). The signature is the identity workstream's outreach signature (`desk-drop-identity/signature/signature-outreach.txt` and `.html`), which already carries the legal pack's Footer B line. Nothing here changes either; this file says which to use where, and how opt-outs are honored. The pasted footer itself carries no review heading (the legal pack's deviation, attorney item 12).

**[POSTAL ADDRESS] must be real before the first email** (review round 3). Every email carries it, and the legal pack warns that a home address printed on every cold email becomes public (`desk-drop-legal-pack/02-email-footer-and-checklist.md`, notes: "Which address to use"). Its options: a USPS post office box, or a private mailbox at a commercial mail receiving agency. Getting either is a spend whose price was not checked (the legal pack's `figures.csv` row `mailing_address_mailbox_annual`, "needs quote"; the financial model times it in week 1, before the first outreach email). What USPS asks for, from its own mailing standards (S20, opened 2026-10-24): a post office box takes PS Form 1093, online or at a Post Office, and two current IDs; a private mailbox takes PS Form 1583, and two IDs, filed through the agency. **Default:** rent one on Mon 2026-10-26 and stop at the payment step to decide (README, decision 5). Until it exists, make the day-one warm asks by phone or LinkedIn, and start email the day the address is real. Use a home address only if you accept it being printed on every cold email.

**When it is used.** Set it up once as your Gmail signature before the first send (identity workstream, `desk-drop-identity/USAGE-GUIDE.md` section 13, needs your login). From then on it is on every email in files 05, 06 and 08 to 11, first touch and every follow-up and reply.

---

## `{SIGNATURE}`: what goes under every email

**Until the name is decided** (`name_decided = N` in `04-slot-state.csv`; the working name is on hold, `desk-drop-legal-pack/name-check-log.md`), the signature names no business, so the people you write to in weeks 1 to 4 do not learn a name that may change on Wed 2026-11-18:

```text
[FOUNDER NAME]
Setting up an office sampling service in {CLUSTER_SHORT}
[PHONE] | [EMAIL]
[POSTAL ADDRESS]

This is a business pitch, sent one to one. Not interested? Reply "no thanks" and I won't email you again.
```

**Once `name_decided = Y`**, with [WEBSITE] still left off until the site is public:

```text
[FOUNDER NAME]
Founder, {BRAND_NAME}
[PHONE] | [EMAIL]
[POSTAL ADDRESS]

This is a business pitch, sent one to one. Not interested? Reply "no thanks" and I won't email you again.
```

- The footer line (the last line) is the legal pack's Footer B, word for word, in both. Only the second line changes, and only by the name rule. The From name, your own name, is the same in both, and [POSTAL ADDRESS] is on both, so the sender is always identified. If someone asks who you are with before the name is decided: "It's a small New York business I'm setting up. The working name is {BRAND_NAME}, and it may change." (the call guides say the same). `_render/fill.py` picks the signature by `name_decided` and fails any email that prints the working name while it is N.
- The second is the identity workstream's outreach signature with [WEBSITE] removed. To remove it there, set `"WEBSITE": ""` in `desk-drop-identity/brand.json` and rebuild the signature (identity workstream's README); its `signature-outreach.txt` still prints `[WEBSITE]` on 2026-10-24. The legal pack says to leave the website out until the site is public.
- Once `site_live = Y` and `name_decided = Y`, put [WEBSITE] back on the third line: `[PHONE] | [EMAIL] | [WEBSITE]`.
- `{BRAND_NAME}` is the name in `desk-drop-identity/brand.json` (the one place it is set; the legal pack's `BRAND_NAME` line matches it). Type the name, do not paste the braces.
- If a signature without [POSTAL ADDRESS] is ever used (only once `name_decided = Y`, because Footer A carries the name), the legal pack's Footer A goes in its place:

```text
[FOUNDER NAME] · {BRAND_NAME} · [PHONE]
[POSTAL ADDRESS]
This is a business pitch, sent one to one. Not interested? Reply "no thanks" and I won't email you again.
```

(Footer A as written in the legal pack, with `· [WEBSITE]` left off until the site is public.)

## Which messages carry it

| Message | Footer | Why |
| --- | --- | --- |
| Every cold email and follow-up (05, 06) | Yes | Commercial email under CAN-SPAM; no business-to-business exception (legal pack 02) |
| Warm intro asks, referral emails, walk-in follow-ups (08) | Yes | About the business, to a business contact. Simplest rule: every email carries it |
| Replies (09) and conversion emails (10, 11) | Yes, except 10 step 8 | The legal pack: an email that also pitches something new is commercial; "adding the footer to everything is simplest and costs nothing". Step 8 of 10 (the company takes over a signed agreement) is the legal pack's own relationship message, sent with no footer as its notes say |
| LinkedIn notes and messages (07) | No | Not email. A "no" there is honored the same way |
| Startup CPG posts (12) | No | Not email, and never a pitch |

## Honoring an opt-out (the legal pack's three lines, applied)

1. Every email carries the block above, in normal-size dark text (no grey small print).
2. The From name is [FOUNDER NAME], the address is at [DOMAIN] (or, on Mon to Wed of week 1 before the new address is authenticated, your existing address, per `sending/`), replies reach you, and the subject says what the email is about. "Re:" only on a real reply in the same thread.
3. Any reply that says no thanks, not interested, stop, unsubscribe or remove me, in any words: `do_not_contact = Y` in the Clay row the same day, no reply, no confirmation, every channel stopped (09, I). Keep the reply address working for at least 30 days after each send. Never share an opted-out address.

## Conflict: the footer and the discovery emails

The footer says "This is a business pitch". The discovery emails (weeks 1 to 3) ask for a research call and sell nothing. The copy is written so the two do not contradict each other: discovery emails never say "no pitch" or "nothing to sell"; they say "questions only" and "there's nothing to buy yet", which is true. LinkedIn messages, which carry no footer, may say "no pitch".

**Recommended default:** keep the footer exactly as written on every email, discovery included, as the legal pack asks. **Question for the legal pack and the attorney (item 12):** for discovery emails, would "This is a business email, sent one to one." identify the email clearly enough? It reads better beside a research request. Do not change it without their answer.

## Second question: Footer B under a signature with no business name

The legal pack writes Footer B for use "under an email signature that already shows your name, the company, [PHONE] and [POSTAL ADDRESS]". Until `name_decided = Y` E's signature names no company (above, and HANDOFF departure 16): it shows your name, "Setting up an office sampling service in {CLUSTER_SHORT}", [PHONE], [EMAIL] and [POSTAL ADDRESS]. Under CAN-SPAM the From name and a valid physical postal address may well identify the sender enough, but that is a legal judgment and it departs from the legal pack's instruction.

**Recommended default:** keep the signature and Footer B as they are until the attorney answers; the name decision (Wed 2026-11-18) ends the question for every email after it. **Question for the legal pack and the attorney (item 12):** before the name is decided, is the founder's name plus [POSTAL ADDRESS] enough sender identification under Footer B, or should Footer A's layout be used without the name? (HANDOFF section 2.4.)

## Changelog

- Round 1 (2026-10-24): took the legal pack's Footer B (v0.6) under the identity workstream's outreach signature, with [WEBSITE] left off until the site is public; listed which messages carry it; named the discovery-wording conflict with a default.
- Merge (2026-10-24): header line unified with the rest of the folder; no copy change.
- Review round 1 (2026-10-24): a signature that names no business until `name_decided = Y` ("Setting up an office sampling service in {CLUSTER_SHORT}"), so a rename on Wed 2026-11-18 does not leave 150 people knowing the old name; Footer A only after the name is decided; which address sends in week 1 restated.
- Review round 2 (2026-10-24): a second question for the attorney (Footer B under a signature that names no company before the name decision), with the default; the legal pack's step 8 office email carries no footer, as its notes say.
- Review round 3 (2026-10-24): [POSTAL ADDRESS] must be real before the first email: the options, the forms, the spend and the default (rent one on Mon 2026-10-26; phone or LinkedIn until then).
