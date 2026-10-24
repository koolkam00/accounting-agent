**Draft for attorney review. Not legal advice.**

# 02 · The commercial-email footer and signature

Version 1.0 · 2026-10-24 · Part A of workstream E · folder `desk-drop-outreach/messages/`

**What it is for.** The block that ends every outreach email: your signature with [POSTAL ADDRESS], and a visible opt-out line. In every message file here it is written `{SIGNATURE}`.

**Whose text it is.** The footer is the legal pack's, used exactly as written (`desk-drop-legal-pack/02-email-footer-and-checklist.md`, version 0.6, 2026-10-24; its handoff says "E: use the footer exactly as written"). The signature is the identity workstream's outreach signature (`desk-drop-identity/signature/signature-outreach.txt` and `.html`), which already carries the legal pack's Footer B line. Nothing here changes either; this file says which to use where, and how opt-outs are honored. The pasted footer itself carries no review heading (the legal pack's deviation, attorney item 12).

**When it is used.** Set it up once as your Gmail signature before the first send (identity workstream, `desk-drop-identity/USAGE-GUIDE.md` section 13, needs your login). From then on it is on every email in files 05, 06 and 08 to 11, first touch and every follow-up and reply.

---

## `{SIGNATURE}`: what goes under every email

Until the website is public, with [WEBSITE] left off:

```text
[FOUNDER NAME]
Founder, {BRAND_NAME}
[PHONE] | [EMAIL]
[POSTAL ADDRESS]

This is a business pitch, sent one to one. Not interested? Reply "no thanks" and I won't email you again.
```

- This is the identity workstream's outreach signature with [WEBSITE] removed. To remove it there, set `"WEBSITE": ""` in `desk-drop-identity/brand.json` and rebuild the signature (identity workstream's README); its `signature-outreach.txt` still prints `[WEBSITE]` on 2026-10-24. The legal pack says to leave the website out until the site is public.
- Once `site_live = Y` and `name_decided = Y`, put [WEBSITE] back on the third line: `[PHONE] | [EMAIL] | [WEBSITE]`.
- `{BRAND_NAME}` is the name in `desk-drop-identity/brand.json` (the one place it is set; the legal pack's `BRAND_NAME` line matches it). Type the name, do not paste the braces.
- If a signature without [POSTAL ADDRESS] is ever used, the legal pack's Footer A goes in its place:

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
| Replies (09) and conversion emails (10, 11) | Yes | The legal pack: an email that also pitches something new is commercial; "adding the footer to everything is simplest and costs nothing" |
| LinkedIn notes and messages (07) | No | Not email. A "no" there is honored the same way |
| Startup CPG posts (12) | No | Not email, and never a pitch |

## Honoring an opt-out (the legal pack's three lines, applied)

1. Every email carries the block above, in normal-size dark text (no grey small print).
2. The From name is [FOUNDER NAME], the address is at [DOMAIN] (or your existing address in week one, per `sending/`), replies reach you, and the subject says what the email is about. "Re:" only on a real reply in the same thread.
3. Any reply that says no thanks, not interested, stop, unsubscribe or remove me, in any words: `do_not_contact = Y` in the Clay row the same day, no reply, no confirmation, every channel stopped (09, I). Keep the reply address working for at least 30 days after each send. Never share an opted-out address.

## Conflict: the footer and the discovery emails

The footer says "This is a business pitch". The discovery emails (weeks 1 to 3) ask for a research call and sell nothing. The copy is written so the two do not contradict each other: discovery emails never say "no pitch" or "nothing to sell"; they say "questions only" and "there's nothing to buy yet", which is true. LinkedIn messages, which carry no footer, may say "no pitch".

**Recommended default:** keep the footer exactly as written on every email, discovery included, as the legal pack asks. **Question for the legal pack and the attorney (item 12):** for discovery emails, would "This is a business email, sent one to one." identify the email clearly enough? It reads better beside a research request. Do not change it without their answer.

## Changelog

- Round 1 (2026-10-24): took the legal pack's Footer B (v0.6) under the identity workstream's outreach signature, with [WEBSITE] left off until the site is public; listed which messages carry it; named the discovery-wording conflict with a default.
