# Reviewer scratch notes, round 1 (2026-10-24)
Started. Read brief, CONTRACTS, plan sections, README, HANDOFF.
Candidate issues (to verify):
- Rename: README says printed pieces take name from desk-drop-identity/brand.json, tracker from config!B2 -> two places?
- builder tests/run_all.sh in sandbox copy: ALL PASS (1m49s). log _review/run_all-sandbox.log
- opscal check: 2026-12-22, 2027-07-06, 2026-08-25, Mon 2027-01-11, Fri 2027-01-15, Thu, holiday all REFUSED; sheet date_check agrees (work/test_sheet_dates.py, LibreOffice) incl. all T offsets for 2027-01-12 and 2027-08-11
- name: config!B2 only cell in tracker; BUT printed pieces use D brand.json; post text/invoice/route use config cell -> two sources, no mismatch check (MAJOR candidate)
- SOP short shipment: "No money changes" vs plan "Credit the difference on the next campaign" (check G agreement)
- Workspace forms: "Restrict to users in org" default? survey-form.md doesn't mention (verify)
- VERIFIED BLOCKER: Workspace Google Forms default "restricted to people inside your organization" (support.google.com/a/users/answer/9303071, opened 2026-10-24). survey-form.md Part 1 step 4, office/brand form docs step 3 and build-forms.template.gs (no setRequireLogin(false)) omit turning it off. Founder's own phone test (Part 2 step 8) passes while signed in -> hides it.
- Verified sources: short.io/pricing (1,000 lifetime, 50k clicks/mo, 5 domains; CSV import for free unclear), bitly pricing (5 links/2 QR/mo, Core $10/mo annual only $120), Dropbox Sign help (3/30 days, bundle = 1). All match.
- Independent QR audit (zxing-cpp, Short.io import CSV, card text): zero 20/20, standard 58/58 OK.
- Exception dry run running in sandbox (tools/scenarios.py exception()), out -> _review/dryrun-exception.out
- Exports headers == H templates (live, SAMPLE-zero, SAMPLE-standard).
- MAJOR candidate: paid events produced by both E (pipeline_log from payment_1/2) and F (--pipeline, org_id fallback brand_id) -> double count / mis-key in H Pipeline; payments typed in E tracker and F invoices (twice).
- Route sheet (standard, PDF+phone PNG viewed): good; stranger questions: "Certificate sent ahead: carry the PDF" (courier has none, stop 4/9 not first drop); no handed-over count box separate from shelf count (SOP says courier_count written on route sheet).
- Reports viewed (zero CMP-001, standard CMP-004): numbers add up, ladder separate, limitations present.
- G agreement s.8: no short-shipment credit; plan says "credit the difference on the next campaign"; SOP says "No money changes" -> unlisted deviation (minor)
- EXCEPTION RUN (quick snapshots, work/exc_quick.py): decline at door O-006 (approved Y, outcome declined, SOP literal correction +40 reserve):
  * make_report T+7 REFUSED "SAMPLE-O-006: no day-5 count" (exit 2); dashboard 0 checks -> no guidance. BLOCKER
  * campaigns units_depleted_day5 blank forever -> export blank; survey_responses_min_office 0 -> gate2_responses miss; offices_under_5 1; offices_approved 10 (H offices 10)
  * reserve_on_hand 95 at T+1 (physical 55); final 40 -> "units still on hand after T+14" phantom from SOP "correction back to reserve"
  * placement confirmation + INV-021 (less credit) + INV-022 credit note: correct and clear.
- standard dry-run INV-009 (deposit, issued 2027-01-08) Bill to "[BRAND LEGAL NAME] [BRAND ADDRESS]": campaign signed before brand row existed; no campaign check for brand_id not on brands or brand not qualified; ship_release ignores brands.qualified.
- Ladder words clean (only prohibitions). Dashboard has contribution/hour per drop and per campaign, cost per stop.
- No check at receipt that received < units_to_ship (short shipment prompt) - minor
- Independent H load (work/h_load.py) of builder SAMPLE-standard exports: 0 errors, 0 failing checks, DRP-001 contribution 848, DRP-002 3605, H file SHA unchanged. Builder claim verified.
- G Part A matches survey description; G D1 "no sign-in" -> Workspace default breaks it (blocker confirmed).
- Office summary O-001 Brightside: "40 delivered ... 44 gone by day 5" (top-ups not shown) -> minor; O-004 Northbound "yes 1, maybe 1, no 1" from 3 people (threshold 3 is thin) minor
- Volatile load: 87,013 formulas, 11,900 INDIRECT, 2,784 SUMPRODUCT, 2,482 TODAY (Google Sheets speed unverified)
- Timestamp linkage: sign-up form responses timestamped, reached from survey confirmation -> joinable to survey row by time; "cannot be joined" claim false (survey-form.md Part 3, HANDOFF To G)
- RENAME TEST (work/rename-*): config!B2 -> "SAMPLE Newname", recalc, make_kit exit 0 "QR all match": Slack posts + route sheet say Newname; tent card + case label still print "Desk Drop" wordmark (D brand.json). No warning. MAJOR.
- Text drafts (.md/.txt messages, debriefs, office summaries, posts) carry no SAMPLE banner; check_folder only checks HTML -> minor
- Short-link domain go.[DOMAIN]: if the domain carries the name, every link name does -> minor (recommend neutral link domain)
- Exception replay: day-3 text drafted to SAMPLE-O-006 (declined at the door) asking how many are left + nudge for survey answers (messages/day3/SAMPLE-O-006.md in sandbox). Decline not propagated.
- Exception QR audit (zxing): 20/20 OK; post links in posts/*.txt all match their office (zero, standard, exception)
- courier "When the route is done" never says where returned cases (declined/owner absent) go
- RETENTION TEST (work/retention-*): delete tab SAMPLE-CMP-001 as SOP answers_delete says, today 2028-01-25 -> campaign responses 34 -> 0, min_office 0, permanent check "no survey tab named SAMPLE-CMP-001". Minor (beyond 6-month horizon) but corrupts record/exports.
- founding_rank computed, nothing checks a 4th founding brand / lock used >2 times (minor)
- Dub pricing page (dub.co/pricing opened 2026-10-24) shows no free plan, Business $90: matches builder.
- Exception replay complete (18m44s): "0 problems" reported although make_report REFUSED (log line 346-347) -> dryrun.py total_bad ignores tool exit codes.
  Day-5 email + day-3 text + office debrief to O-006 as if delivered; report email says "report attached" though no PDF; brand debrief cites "from the report".
- H load of exception exports (work/h-exception): 0 errors, 0 failing checks, but DRP-003 units_depleted_day5 = 0 in Drop_Actuals (CSV blank; raw arithmetic over 9 offices = 408) and CMP-006 counted under responses-per-office threshold (min office 0 from the declined office).
- Raw recompute (scenario rows): received 480, delivered 425, topped 12, responses 62, tried 49, qr 71 -> all match tracker.
- round-1.md written 09:55: 2 blockers, 6 majors, 9 minors
