# QoE Evidence Review: automated evaluation (dev)

> **Read this first.** These are automated scores of the tool's first-pass proposals, compared with answer keys written for SYNTHETIC deal packages. They are not practitioner-timed results, they say nothing about time saved, and they ignore any reviewer overrides. Each answer key records one careful senior's judgment; items marked medium or high ambiguity could reasonably be carried differently.

- Deals: 2 (meridian_mechanical, tidewell_distribution); management adjustments scored: 30; diligence-identified items in the keys: 4
- AI mode: `rules`; tool version: `0.1.0`
- meridian_mechanical: amount columns read `FY2024 / FY2025 / TTM Jun-26` (USD)
- tidewell_distribution: amount columns read `FY2025 / FY2026 / TTM Jun-26` (USD)

## 1. False accepts

The tool proposed ACCEPT where the answer key says REQUEST_INFO, or says REVISE or REJECT at an amount the accepted claim exceeds by more than 1.00 in at least one period. This is the costliest error: an unsupported add-back would reach the buyer's EBITDA if the reviewer relied on the proposal.

**0 false accept(s) out of 19 adjustments where accepting the claim would overstate EBITDA (0.0%).**

None.

## 2. Misses

### Missed revisions (0 of 1 items the key carries at or above the claim)

The tool proposed ACCEPT where the answer key says REVISE or REJECT but carries at least the claimed amount in every period (for example an understated add-back). Not a false accept: EBITDA is left understated, not overstated, but the revision is still missed.

None.

### Missed challenges (0 of 16 expected)

Expected CONTRADICTORY_EVIDENCE, RECURRING_PATTERN, CONTINUING_OBLIGATION, OFFSETTING_RECOVERY, OVERLAP_WITH_OTHER_ADJUSTMENT or ALREADY_EXCLUDED_FROM_EBITDA flags that the tool did not raise on the right adjustment.

None.

### Wrong treatment or wrong amount

None.

### Missed data-quality issues (0 of 9 planted)

None.

### Diligence-identified items (4 of 4 correct)

Adjustments the tool proposes beyond management's schedule (SPEC §5.7, e.g. reversing a duplicate posting), matched to the key by shared GL rows; a key item with no GL rows (e.g. a documented export gap) matches a tool item with no supporting GL links that is non-zero in the same periods. Correct = every period within 1.00. A key item the tool did not identify is MISSED; a tool item the key does not expect is EXTRA and counts against accuracy.

| Deal | Key item | Tool item | Matched on | Key amounts | Tool amounts | Missing flags | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| meridian_mechanical | D-1 | D-1 | supporting rows | 0 / 18,400 / 0 | 0 / 18,400 / 0 | - | CORRECT |
| tidewell_distribution | D-1 | D-1 | supporting rows | 0 / 32,000 / 32,000 | 0 / 32,000 / 32,000 | - | CORRECT |
| tidewell_distribution | D-2 | D-2 | supporting rows | 0 / (186,000) / 0 | 0 / (186,000) / 0 | - | CORRECT |
| tidewell_distribution | D-3 | D-3 | period labels | (363,586) / 0 / 0 | (363,586) / 0 / 0 | - | CORRECT |

### Diligence adjusted EBITDA vs answer key

Tool figure = GL EBITDA + every tool proposal that is not REQUEST_INFO, management items and diligence-identified items alike (SPEC §5.6 identity), before any reviewer decision.

| Deal | Period | GL EBITDA (tool) | GL EBITDA (key) | Diligence items (tool) | (key) | Diligence adj. EBITDA (tool) | (key) | Abs. error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meridian_mechanical | FY2024 | 4,262,398 | 4,262,398 | 0 | 0 | 4,278,398 | 4,278,398 | 0 |
| meridian_mechanical | FY2025 | 4,539,300 | 4,539,300 | 18,400 | 18,400 | 4,893,400 | 4,893,400 | 0 |
| meridian_mechanical | TTM Jun-26 | 4,846,859 | 4,846,859 | 0 | 0 | 5,091,059 | 5,091,059 | 0 |
| tidewell_distribution | FY2025 | 8,021,818 | 8,021,818 | (363,586) | (363,586) | 8,138,232 | 8,138,232 | 0 |
| tidewell_distribution | FY2026 | 7,418,030 | 7,418,030 | (154,000) | (154,000) | 8,362,630 | 8,362,630 | 0 |
| tidewell_distribution | TTM Jun-26 | 7,443,815 | 7,443,815 | 32,000 | 32,000 | 8,678,245 | 8,678,245 | 0 |

## 3. Headline accuracy

| Metric | Result | Count | What it measures |
| --- | --- | --- | --- |
| False accept rate | 0.0% | 0/19 | tool ACCEPT where accepting the claim overstates EBITDA vs the key (lower is better) |
| Missed revisions | 0.0% | 0/1 | tool ACCEPT where the key revises but carries at least the claim (lower is better) |
| Treatment accuracy | 100.0% | 30/30 | tool treatment equals the key |
| Amount accuracy | 100.0% | 27/27 | every period within 1.00, where neither side is REQUEST_INFO |
| Missed challenges | 0.0% | 0/16 | expected challenge flags not raised (lower is better) |
| Flag recall | 100.0% | 28/28 | expected flags raised on the right adjustment |
| GL link precision | 100.0% | 254/254 | supporting tool links that the key also supports |
| GL link recall | 100.0% | 254/254 | key supporting rows the tool linked as supporting |
| GL surfaced recall | 100.0% | 361/361 | key supporting + related rows shown anywhere in the evidence |
| Document precision | 98.6% | 71/72 | documents the tool relies on that the key lists as support |
| Document recall | 96.0% | 71/74 | key support documents the tool relies on |
| Document surfaced recall | 98.8% | 82/83 | key supporting + related documents shown anywhere |
| Data-quality recall | 100.0% | 9/9 | planted data issues detected |
| Diligence item accuracy | 100.0% | 4/4 | items beyond management's schedule, right amounts |
| Max diligence EBITDA error | 0 | - | largest absolute error across deals and periods |

## 4. Per-case results

| Deal | Ref | Case type | Ambiguity | Key | Tool | Conf. | Key amounts | Tool amounts | GL P / R | Doc P / R | Missing flags | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meridian_mechanical | M-01 | RECURRING | low | REVISE | REVISE | medium | 0 / 84,500 / 30,000 | 0 / 84,500 / 30,000 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-02 | NEEDS_INFO | medium | REQUEST_INFO | REQUEST_INFO | high | none (pending) | none (pending) | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-03 | CONTRADICTED | low | REVISE | REVISE | medium | 0 / 31,200 / 31,200 | 0 / 31,200 / 31,200 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-04 | ADEQUATE | low | ACCEPT | ACCEPT | high | 0 / 45,000 / 15,000 | 0 / 45,000 / 15,000 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-05 | ADEQUATE | low | ACCEPT | ACCEPT | high | 0 / 0 / 75,000 | 0 / 0 / 75,000 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-06 | CONTRADICTED | low | REJECT | REJECT | medium | 0 / 0 / 0 | 0 / 0 / 0 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-07 | EBITDA_EXCLUDED | low | REJECT | REJECT | high | 0 / 0 / 0 | 0 / 0 / 0 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-08 | OVERLAP | low | REVISE | REVISE | high | 0 / 41,000 / 41,000 | 0 / 41,000 / 41,000 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-09 | RECOVERY_OFFSET | medium | REVISE | REVISE | high | 58,000 / (40,000) / 0 | 58,000 / (40,000) / 0 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-10 | OUT_OF_PERIOD | low | REVISE | REVISE | high | (42,000) / 42,000 / 0 | (42,000) / 42,000 / 0 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-11 | WRONG_PERIOD | low | REVISE | REVISE | high | 0 / 80,000 / 0 | 0 / 80,000 / 0 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-12 | NEEDS_INFO | medium | REQUEST_INFO | REQUEST_INFO | high | none (pending) | none (pending) | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-13 | RECURRING | low | REJECT | REJECT | medium | 0 / 0 / 0 | 0 / 0 / 0 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-14 | ADEQUATE | medium | ACCEPT | ACCEPT | high | 0 / 52,000 / 52,000 | 0 / 52,000 / 52,000 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 1 | ADEQUATE | low | ACCEPT | ACCEPT | high | 540,000 / 540,000 / 540,000 | 540,000 / 540,000 / 540,000 | 1.00 / 1.00 | 1.00 / 0.50 | - | PASS |
| tidewell_distribution | 2 | CONTRADICTED | medium | REVISE | REVISE | medium | (60,000) / (60,000) / (60,000) | (60,000) / (60,000) / (60,000) | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 3 | NEEDS_INFO | medium | REQUEST_INFO | REQUEST_INFO | high | none (pending) | none (pending) | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 4 | ADEQUATE | low | ACCEPT | ACCEPT | high | 0 / 0 / 88,230 | 0 / 0 / 88,230 | 1.00 / 1.00 | 1.00 / 0.67 | - | PASS |
| tidewell_distribution | 5 | PARTIAL | low | REVISE | REVISE | high | 0 / 0 / 43,200 | 0 / 0 / 43,200 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 6 | ADEQUATE | low | ACCEPT | ACCEPT | high | 0 / 90,000 / 90,000 | 0 / 90,000 / 90,000 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 7 | RECOVERY_OFFSET | low | REVISE | REVISE | high | 0 / 72,000 / 42,000 | 0 / 72,000 / 42,000 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 8 | ADEQUATE | medium | ACCEPT | ACCEPT | high | 0 / 148,600 / 148,600 | 0 / 148,600 / 148,600 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 9 | ADEQUATE | low | ACCEPT | ACCEPT | high | 0 / 51,000 / 34,200 | 0 / 51,000 / 34,200 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 10 | CONTRADICTED | low | REVISE | REVISE | medium | 0 / 64,000 / 64,000 | 0 / 64,000 / 64,000 | 1.00 / 1.00 | 0.75 / 1.00 | - | PASS |
| tidewell_distribution | 11 | UNDERSTATED | medium | REVISE | REVISE | medium | 0 / 84,000 / 84,000 | 0 / 84,000 / 84,000 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 12 | SIGN_ERROR | low | REVISE | REVISE | medium | 0 / (46,500) / (46,500) | 0 / (46,500) / (46,500) | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 13 | OUT_OF_PERIOD | low | REVISE | REVISE | high | 0 / 0 / 19,200 | 0 / 0 / 19,200 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 14 | EBITDA_EXCLUDED | low | REVISE | REVISE | high | 0 / 42,000 / 42,000 | 0 / 42,000 / 42,000 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 15 | ADEQUATE | low | ACCEPT | ACCEPT | high | 0 / 18,500 / 18,500 | 0 / 18,500 / 18,500 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 16 | ADEQUATE | low | ACCEPT | ACCEPT | high | 0 / 95,000 / 95,000 | 0 / 95,000 / 95,000 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |

## 5. Treatment accuracy by case type

Case types are the answer-key vocabulary (`ExpectedAdjustment.case_type`), management items and the key's diligence-identified items together (a missed diligence item counts as wrong). A case type no key uses shows `-`.

| Case type | Correct | Accuracy |
| --- | --- | --- |
| ADEQUATE | 10/10 | 100.0% |
| PARTIAL | 1/1 | 100.0% |
| OVERLAP | 1/1 | 100.0% |
| EBITDA_EXCLUDED | 2/2 | 100.0% |
| CONTRADICTED | 4/4 | 100.0% |
| RECURRING | 2/2 | 100.0% |
| RECOVERY_OFFSET | 2/2 | 100.0% |
| OUT_OF_PERIOD | 2/2 | 100.0% |
| WRONG_PERIOD | 1/1 | 100.0% |
| NEEDS_INFO | 3/3 | 100.0% |
| UNDERSTATED | 1/1 | 100.0% |
| SIGN_ERROR | 1/1 | 100.0% |
| DUPLICATE_POSTING | 2/2 | 100.0% |
| SUPPORTED_TOPSIDE | 1/1 | 100.0% |
| MISSING_GL_MONTH | 1/1 | 100.0% |

### By the tool's own confidence

| Tool confidence | Correct | Accuracy |
| --- | --- | --- |
| high | 22/22 | 100.0% |
| medium | 8/8 | 100.0% |

## 6. How these numbers are computed

- A tool GL link is *supporting* when the tool carries the entry: claimed (audit role supporting or moved; `supports_claim` on older workpapers) and not removed by a flag (the link's `removed_by`, or a removing flag: already excluded, overlap, contradiction, continuing obligation, recurring pattern). An entry replaced by its out-of-period effect still counts as supporting. Links map to GL rows via `GL-R<row>`.
- *Surfaced* rows are rows shown anywhere in the adjustment's evidence (links, flag entries, recurrence observations), measured against the key's supporting and related rows.
- The documents the tool *relies on* depend on what it carries. A non-zero amount: documents linked to supporting entries, stand-alone agreements no removing flag cites, and documents behind a recovery or out-of-period effect. Zero (REJECT): the documents that took the claim out. Pending (REQUEST_INFO): the documents the request rests on. Documents that argue against part of a carried amount are not support; *surfaced* documents (any doc link or flag citation) are measured against supporting + related documents.
- Management-item metrics exclude diligence-identified items. Those are matched to the key one-to-one by shared supporting GL rows, then any shared GL row, then (for a key item with no GL rows) the same set of non-zero periods, and scored on amounts; both kinds of item enter the diligence adjusted EBITDA check and the case-type table.
- Deal and overall rates pool the underlying counts (micro-average). The false accept rate's denominator is the number of adjustments where an ACCEPT would overstate EBITDA: the key says REQUEST_INFO, or the accepted amount (the tool's proposal if it accepted, else management's claim) exceeds the key by more than 1.00 in some period. The key's other non-ACCEPT items are the denominator for missed revisions.
- Extra flags are not penalized; the key lists the flags that must be raised, not the only acceptable ones.
- Amounts are USD, rounded to the dollar here; the JSON report carries cents.

