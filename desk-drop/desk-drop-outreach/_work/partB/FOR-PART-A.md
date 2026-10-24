# Coordination note from Part B to Part A (2026-10-24)

Part B owns: `tracking/`, `calls/`, `sending/`, `handoff/`, `exports/`, `tools/`, `_work/partB/`.
Part B does not touch any other path. Part A owns the message copy.

Values Part B's tracker reads from the Clay tables (CONTRACTS 6.2 conversation-tracking columns).
If your reply playbook or sequences name these, please use the same strings; tell the merge step if you need a change.

## `sequence` (Clay): `<side>-<stage>-<variant>`
- side: `office` or `brand`
- stage: `discovery` (weeks 1 to 3, no selling), `selling` (from Gate 0), `conversion` (post-call sequence)
- variant: one capital letter, `A`, `B`, ... (your subject-line or body variant)
- examples: `office-discovery-A`, `brand-discovery-B`, `brand-conversion-A`
- the channel (`email`, `linkedin`, `warm-intro`, `walk-in`) stays in the separate `channel` column

## `reply_type` (Clay), one value per row: the latest meaningful reply
`yes` (agrees to talk), `maybe`, `needs_approval` ("I need to ask facilities or HR"), `send_info`, `wrong_person`,
`referral`, `not_now`, `no`, `opt_out`, `obj_seed_ourselves`, `obj_price`, `obj_free_trial`, `obj_what_we_get`,
`obj_other`, `out_of_office`, `bounce`. Silence = blank.

## Status writes (CONTRACTS section 4 values only)
- reply `yes` -> `replied`, then `call_booked` once a time is set
- `maybe`, `needs_approval`, `send_info`, `referral`, any `obj_*` -> `replied`
- `not_now` -> `not_now` with `next_action_date`
- `no` -> `no`
- `wrong_person` -> `wrong_person`; the named person becomes a new row with `referral_from` = the old `row_id`
- `opt_out` -> status `do_not_contact`, `do_not_contact = Y`, `opt_out_date` = today, same day
- `bounce` -> `email_status = none`, status stays `contacted`, switch `channel` to `linkedin`

## `next_action` (Clay), one key
`send_touch_2`, `send_touch_3`, `book_call`, `run_call`, `send_one_pager`, `send_proposal`, `send_agreement`,
`send_materials_request`, `chase_payment`, `ask_referral`, `recontact`, `none`

## Deliverability points Part B's sending guide makes (please match in the copy)
- No attachment and no link in a first touch from the new domain. Offer the one-pager; send the PDF on reply.
- Plain text, no images, no tracking pixel, no link shortener. Signature: name, company, [PHONE], [POSTAL ADDRESS].
- Footer: legal pack `02` Footer B under the signature-outreach signature (or Footer A).
- Proposed drop dates in copy are slots, e.g. `[DROP DATE: Tue 2027-01-12]`.

## LinkedIn limit that affects the copy (added 2026-10-24)
LinkedIn Help, "Personalize invitations to connect" (https://www.linkedin.com/help/linkedin/answer/a563153,
opened 2026-10-24, page says "Last updated: 6 months ago"): "You can add a personalized message to up to three
connection requests per month. Each message can be up to 200 characters." Premium members: unlimited notes.
So on a free account the connection NOTE is for at most 3 people a month and must be 200 characters or fewer.
Part B's week-one plan therefore sends most LinkedIn invitations with no note, and the LinkedIn follow-up
message (sent once they accept) carries the ask.
