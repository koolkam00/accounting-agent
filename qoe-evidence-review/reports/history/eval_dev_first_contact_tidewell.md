> **Snapshot:** the committed engine (tuned on Meridian only) run on Tidewell the first time it saw it, before any tuning on Tidewell. Kept as an honest generalization baseline; see results note.

# QoE Evidence Review: automated evaluation (dev)

> **Read this first.** These are automated scores of the tool's first-pass proposals, compared with answer keys written for SYNTHETIC deal packages. They are not practitioner-timed results, they say nothing about time saved, and they ignore any reviewer overrides. Each answer key records one careful senior's judgment; items marked medium or high ambiguity could reasonably be carried differently.

- Deals: 2 (meridian_mechanical, tidewell_distribution); management adjustments scored: 30; diligence-identified items in the keys: 4
- AI mode: `rules`; tool version: `0.1.0`
- meridian_mechanical: amount columns read `FY2024 / FY2025 / TTM Jun-26` (USD)
- tidewell_distribution: amount columns read `FY2025 / FY2026 / TTM Jun-26` (USD)

## 1. False accepts

The tool proposed ACCEPT where the answer key says REVISE, REJECT or REQUEST_INFO. This is the costliest error: an unsupported add-back would reach the buyer's EBITDA if the reviewer relied on the proposal.

**2 false accept(s) out of 20 adjustments that needed challenge (10.0%).**

| Deal | Ref | Case type | Answer key | Key amounts | Tool amounts | Missing flags |
| --- | --- | --- | --- | --- | --- | --- |
| tidewell_distribution | 11 | UNDERSTATED | REVISE | 0 / 84,000 / 84,000 | 0 / 54,000 / 54,000 | - |
| tidewell_distribution | 13 | OUT_OF_PERIOD | REVISE | 0 / 0 / 19,200 | 0 / 38,400 / 38,400 | OUT_OF_PERIOD |

## 2. Misses

### Missed challenges (1 of 16 expected)

Expected CONTRADICTORY_EVIDENCE, RECURRING_PATTERN, CONTINUING_OBLIGATION, OFFSETTING_RECOVERY, OVERLAP_WITH_OTHER_ADJUSTMENT or ALREADY_EXCLUDED_FROM_EBITDA flags that the tool did not raise on the right adjustment.

| Deal | Ref | Missing flag | Tool treatment |
| --- | --- | --- | --- |
| tidewell_distribution | 2 | CONTRADICTORY_EVIDENCE | REQUEST_INFO |

### Wrong treatment or wrong amount

| Deal | Ref | Case type | Answer key | Tool | Key amounts | Tool amounts | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tidewell_distribution | 2 | CONTRADICTED | REVISE | REQUEST_INFO | (60,000) / (60,000) / (60,000) | none (pending) | WRONG_TREATMENT |
| tidewell_distribution | 7 | RECOVERY_OFFSET | REVISE | REVISE | 0 / 72,000 / 42,000 | 0 / 81,659 / 50,526 | WRONG_AMOUNT |
| tidewell_distribution | 8 | ADEQUATE | ACCEPT | REJECT | 0 / 148,600 / 148,600 | 0 / 0 / 0 | WRONG_TREATMENT |
| tidewell_distribution | 9 | ADEQUATE | ACCEPT | REJECT | 0 / 51,000 / 34,200 | 0 / 0 / 0 | WRONG_TREATMENT |
| tidewell_distribution | 10 | CONTRADICTED | REVISE | REJECT | 0 / 64,000 / 64,000 | 0 / 0 / 0 | WRONG_TREATMENT |
| tidewell_distribution | 14 | EBITDA_EXCLUDED | REVISE | REJECT | 0 / 42,000 / 42,000 | 0 / 0 / 0 | WRONG_TREATMENT |

### Missed data-quality issues (0 of 9 planted)

None.

### Diligence-identified items (2 of 4 correct)

Adjustments the tool proposes beyond management's schedule (SPEC §5.7, e.g. reversing a duplicate posting), matched to the key by shared GL rows. Correct = every period within 1.00. A key item the tool did not identify is MISSED; a tool item the key does not expect is EXTRA and counts against accuracy.

| Deal | Key item | Tool item | Matched on | Key amounts | Tool amounts | Missing flags | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| meridian_mechanical | D-1 | D-1 | supporting rows | 0 / 18,400 / 0 | 0 / 18,400 / 0 | - | CORRECT |
| tidewell_distribution | D-1 | D-1 | supporting rows | 0 / 32,000 / 32,000 | 0 / 32,000 / 32,000 | - | CORRECT |
| tidewell_distribution | D-2 | - | - | 0 / (186,000) / 0 | - | - | MISSED |
| tidewell_distribution | D-3 | - | - | (363,586) / 0 / 0 | - | - | MISSED |

### Diligence adjusted EBITDA vs answer key

Tool figure = GL EBITDA + every tool proposal that is not REQUEST_INFO, management items and diligence-identified items alike (SPEC §5.6 identity), before any reviewer decision.

| Deal | Period | GL EBITDA (tool) | GL EBITDA (key) | Diligence items (tool) | (key) | Diligence adj. EBITDA (tool) | (key) | Abs. error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meridian_mechanical | FY2024 | 4,262,398 | 4,262,398 | 0 | 0 | 4,278,398 | 4,278,398 | 0 |
| meridian_mechanical | FY2025 | 4,539,300 | 4,539,300 | 18,400 | 18,400 | 4,893,400 | 4,893,400 | 0 |
| meridian_mechanical | TTM Jun-26 | 4,846,859 | 4,846,859 | 0 | 0 | 5,091,059 | 5,091,059 | 0 |
| tidewell_distribution | FY2025 | 8,021,818 | 8,021,818 | 0 | (363,586) | 8,561,818 | 8,138,232 | 423,586 |
| tidewell_distribution | FY2026 | 7,418,030 | 7,418,030 | 32,000 | (154,000) | 8,321,089 | 8,362,630 | 41,541 |
| tidewell_distribution | TTM Jun-26 | 7,443,815 | 7,443,815 | 32,000 | 32,000 | 8,447,171 | 8,678,245 | 231,074 |

## 3. Headline accuracy

| Metric | Result | Count | What it measures |
| --- | --- | --- | --- |
| False accept rate | 10.0% | 2/20 | tool ACCEPT where the key does not accept (lower is better) |
| Treatment accuracy | 76.7% | 23/30 | tool treatment equals the key |
| Amount accuracy | 73.1% | 19/26 | every period within 1.00, where neither side is REQUEST_INFO |
| Missed challenges | 6.2% | 1/16 | expected challenge flags not raised (lower is better) |
| Flag recall | 92.9% | 26/28 | expected flags raised on the right adjustment |
| GL link precision | 76.5% | 192/251 | supporting tool links that the key also supports |
| GL link recall | 75.6% | 192/254 | key supporting rows the tool linked as supporting |
| GL surfaced recall | 100.0% | 361/361 | key supporting + related rows shown anywhere in the evidence |
| Document precision | 94.4% | 67/71 | documents the tool relies on that the key lists as support |
| Document recall | 90.5% | 67/74 | key support documents the tool relies on |
| Document surfaced recall | 98.8% | 82/83 | key supporting + related documents shown anywhere |
| Data-quality recall | 100.0% | 9/9 | planted data issues detected |
| Diligence item accuracy | 50.0% | 2/4 | items beyond management's schedule, right amounts |
| Max diligence EBITDA error | 423,586 | - | largest absolute error across deals and periods |

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
| tidewell_distribution | 1 | ADEQUATE | low | ACCEPT | ACCEPT | medium | 540,000 / 540,000 / 540,000 | 540,000 / 540,000 / 540,000 | n/a / 0.00 | n/a / 0.00 | - | PASS |
| tidewell_distribution | 2 | CONTRADICTED | medium | REVISE | REQUEST_INFO | high | (60,000) / (60,000) / (60,000) | none (pending) | 0.33 / 1.00 | 1.00 / 1.00 | CONTRADICTORY_EVIDENCE | WRONG_TREATMENT |
| tidewell_distribution | 3 | NEEDS_INFO | medium | REQUEST_INFO | REQUEST_INFO | high | none (pending) | none (pending) | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 4 | ADEQUATE | low | ACCEPT | ACCEPT | high | 0 / 0 / 88,230 | 0 / 0 / 88,230 | 1.00 / 1.00 | 1.00 / 0.67 | - | PASS |
| tidewell_distribution | 5 | PARTIAL | low | REVISE | REVISE | high | 0 / 0 / 43,200 | 0 / 0 / 43,200 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 6 | ADEQUATE | low | ACCEPT | ACCEPT | high | 0 / 90,000 / 90,000 | 0 / 90,000 / 90,000 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 7 | RECOVERY_OFFSET | low | REVISE | REVISE | medium | 0 / 72,000 / 42,000 | 0 / 81,659 / 50,526 | 0.40 / 1.00 | 1.00 / 1.00 | - | WRONG_AMOUNT |
| tidewell_distribution | 8 | ADEQUATE | medium | ACCEPT | REJECT | medium | 0 / 148,600 / 148,600 | 0 / 0 / 0 | n/a / 0.00 | 1.00 / 0.33 | - | WRONG_TREATMENT |
| tidewell_distribution | 9 | ADEQUATE | low | ACCEPT | REJECT | medium | 0 / 51,000 / 34,200 | 0 / 0 / 0 | n/a / 0.00 | 0.80 / 0.80 | - | WRONG_TREATMENT |
| tidewell_distribution | 10 | CONTRADICTED | low | REVISE | REJECT | medium | 0 / 64,000 / 64,000 | 0 / 0 / 0 | n/a / 0.00 | 0.60 / 1.00 | - | WRONG_TREATMENT |
| tidewell_distribution | 11 | UNDERSTATED | medium | REVISE | ACCEPT | high | 0 / 84,000 / 84,000 | 0 / 54,000 / 54,000 | 1.00 / 0.67 | 1.00 / 1.00 | - | FALSE_ACCEPT |
| tidewell_distribution | 12 | SIGN_ERROR | low | REVISE | REVISE | medium | 0 / (46,500) / (46,500) | 0 / (46,500) / (46,500) | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 13 | OUT_OF_PERIOD | low | REVISE | ACCEPT | high | 0 / 0 / 19,200 | 0 / 38,400 / 38,400 | 1.00 / 1.00 | 1.00 / 1.00 | OUT_OF_PERIOD | FALSE_ACCEPT |
| tidewell_distribution | 14 | EBITDA_EXCLUDED | low | REVISE | REJECT | medium | 0 / 42,000 / 42,000 | 0 / 0 / 0 | n/a / 0.00 | 0.67 / 1.00 | - | WRONG_TREATMENT |
| tidewell_distribution | 15 | ADEQUATE | low | ACCEPT | ACCEPT | high | 0 / 18,500 / 18,500 | 0 / 18,500 / 18,500 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |
| tidewell_distribution | 16 | ADEQUATE | low | ACCEPT | ACCEPT | high | 0 / 95,000 / 95,000 | 0 / 95,000 / 95,000 | 1.00 / 1.00 | 1.00 / 1.00 | - | PASS |

## 5. Treatment accuracy by case type

| Case type | Correct | Accuracy |
| --- | --- | --- |
| ADEQUATE | 8/10 | 80.0% |
| CONTRADICTED | 2/4 | 50.0% |
| EBITDA_EXCLUDED | 1/2 | 50.0% |
| NEEDS_INFO | 3/3 | 100.0% |
| OUT_OF_PERIOD | 1/2 | 50.0% |
| OVERLAP | 1/1 | 100.0% |
| PARTIAL | 1/1 | 100.0% |
| RECOVERY_OFFSET | 2/2 | 100.0% |
| RECURRING | 2/2 | 100.0% |
| SIGN_ERROR | 1/1 | 100.0% |
| UNDERSTATED | 0/1 | 0.0% |
| WRONG_PERIOD | 1/1 | 100.0% |

### By the tool's own confidence

| Tool confidence | Correct | Accuracy |
| --- | --- | --- |
| high | 16/19 | 84.2% |
| medium | 7/11 | 63.6% |

## 6. How these numbers are computed

- A tool GL link is *supporting* when `supports_claim` is true and the entry is not listed on a removing flag (already excluded, overlap, contradiction, continuing obligation, recurring pattern) for the same adjustment. Links map to GL rows via `GL-R<row>`.
- *Surfaced* rows are rows shown anywhere in the adjustment's evidence (links, flag entries, recurrence observations), measured against the key's supporting and related rows.
- The documents the tool *relies on* depend on what it carries. A non-zero amount: documents linked to supporting entries, stand-alone agreements no removing flag cites, and documents behind a recovery or out-of-period effect. Zero (REJECT): the documents that took the claim out. Pending (REQUEST_INFO): the documents the request rests on. Documents that argue against part of a carried amount are not support; *surfaced* documents (any doc link or flag citation) are measured against supporting + related documents.
- Management-item metrics exclude diligence-identified items. Those are matched to the key one-to-one by shared supporting GL rows (then any shared GL row) and scored on amounts only; both kinds of item enter the diligence adjusted EBITDA check.
- Deal and overall rates pool the underlying counts (micro-average). The false accept rate's denominator is the number of adjustments the key does not accept.
- Extra flags are not penalized; the key lists the flags that must be raised, not the only acceptable ones.
- Amounts are USD, rounded to the dollar here; the JSON report carries cents.

