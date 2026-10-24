# Coordination note from Part A to Part B (2026-10-24)

Part A owns: `messages/` (all message copy, field map, slot table, rendered examples, the fill script in `messages/_render/`) and `_work/partA/`. Part A does not touch any other path.

Adopted from your FOR-PART-A.md, exactly: `sequence` = `<side>-<stage>-<variant>`; the `reply_type` list; the status writes; the `next_action` keys; the deliverability points (no link or attachment in a first touch, plain text, no images, no pixel, no shortener, Footer B under signature-outreach).

What Part A defines that your tracker may want to read:
1. `messages/04-slot-state.csv`: one row per progress switch the copy depends on (key, value, as_of, set_by, how_to_set). Counts (offices signed, brands paid, combined Tuesday headcount) are derived from the Clay tables / handoff CSVs; switches (llc_formed, attorney_cleared, gl_bound, name_decided, site_live, domain_ready, mock_card_photo_ready, startup_cpg_joined, drop_date_confirmed) are set by the founder. If your workbook has a settings tab, mirror these keys there and say which file wins; Part A's default is that the CSV wins until the merge decides.
2. E personalization columns added to the Clay tables (beside the tracking columns): `why_now_hook`, `call_note_hook`, `street_short`. Defined in `messages/03-personalization-fields.csv`. All optional; every one has a fallback.
3. Variant letters: A and B are subject-line variants on touch 1; bodies are shared. A row keeps its letter for all three touches.
4. Touch timing: touch 2 = touch 1 + 3 business days, touch 3 = touch 1 + 7 business days (CONTRACTS business days, holidays excluded). Silence after touch 3 -> status `not_now`, `next_action = recontact`, `next_action_date` = Tue 2027-01-19 for anything parked before Fri 2026-12-11 (derived, founder to confirm).
