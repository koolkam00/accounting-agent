# QoE Evidence Review: automated evaluation (dev)

> **Read this first.** These are automated scores of the tool's first-pass proposals, compared with answer keys written for SYNTHETIC deal packages. They are not practitioner-timed results, they say nothing about time saved, and they ignore any reviewer overrides. Each answer key records one careful senior's judgment; items marked medium or high ambiguity could reasonably be carried differently.

- Deals: 1 (meridian_mechanical); adjustments scored: 14
- AI mode: `rules`; tool version: `0.1.0`
- meridian_mechanical: amount columns read `FY2024 / FY2025 / TTM Jun-26` (USD)

## 1. False accepts

The tool proposed ACCEPT where the answer key says REVISE, REJECT or REQUEST_INFO. This is the costliest error: an unsupported add-back would reach the buyer's EBITDA if the reviewer relied on the proposal.

**0 false accept(s) out of 11 adjustments that needed challenge (0.0%).**

None.

## 2. Misses

### Missed challenges (0 of 11 expected)

Expected CONTRADICTORY_EVIDENCE, RECURRING_PATTERN, CONTINUING_OBLIGATION, OFFSETTING_RECOVERY, OVERLAP_WITH_OTHER_ADJUSTMENT or ALREADY_EXCLUDED_FROM_EBITDA flags that the tool did not raise on the right adjustment.

None.

### Wrong treatment or wrong amount

None.

### Missed data-quality issues (0 of 3 planted)

None.

### Diligence adjusted EBITDA vs answer key

Tool figure = GL EBITDA + every tool proposal that is not REQUEST_INFO (SPEC §5.6 identity), before any reviewer decision.

| Deal | Period | GL EBITDA (tool) | GL EBITDA (key) | Diligence adj. EBITDA (tool) | (key) | Abs. error |
| --- | --- | --- | --- | --- | --- | --- |
| meridian_mechanical | FY2024 | 4,262,398 | 4,262,398 | 4,278,398 | 4,278,398 | 0 |
| meridian_mechanical | FY2025 | 4,539,300 | 4,539,300 | 4,875,000 | 4,893,400 | 18,400 |
| meridian_mechanical | TTM Jun-26 | 4,846,859 | 4,846,859 | 5,091,059 | 5,091,059 | 0 |

## 3. Headline accuracy

| Metric | Result | Count | What it measures |
| --- | --- | --- | --- |
| False accept rate | 0.0% | 0/11 | tool ACCEPT where the key does not accept (lower is better) |
| Treatment accuracy | 100.0% | 14/14 | tool treatment equals the key |
| Amount accuracy | 100.0% | 12/12 | every period within 1.00, where neither side is REQUEST_INFO |
| Missed challenges | 0.0% | 0/11 | expected challenge flags not raised (lower is better) |
| Flag recall | 100.0% | 16/16 | expected flags raised on the right adjustment |
| GL link precision | 100.0% | 128/128 | supporting tool links that the key also supports |
| GL link recall | 100.0% | 128/128 | key supporting rows the tool linked as supporting |
| GL surfaced recall | 100.0% | 191/191 | key supporting + related rows shown anywhere in the evidence |
| Document link precision | 75.6% | 34/45 | linked documents the key lists as support |
| Document link recall | 100.0% | 34/34 | key support documents the tool linked |
| Data-quality recall | 100.0% | 3/3 | planted data issues detected |
| Max diligence EBITDA error | 18,400 | - | largest absolute error across deals and periods |

## 4. Per-case results

| Deal | Ref | Case type | Ambiguity | Key | Tool | Conf. | Key amounts | Tool amounts | GL P / R | Missing flags | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| meridian_mechanical | M-01 | RECURRING | low | REVISE | REVISE | medium | 0 / 84,500 / 30,000 | 0 / 84,500 / 30,000 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-02 | NEEDS_INFO | medium | REQUEST_INFO | REQUEST_INFO | high | none (pending) | none (pending) | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-03 | CONTRADICTED | low | REVISE | REVISE | medium | 0 / 31,200 / 31,200 | 0 / 31,200 / 31,200 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-04 | ADEQUATE | low | ACCEPT | ACCEPT | high | 0 / 45,000 / 15,000 | 0 / 45,000 / 15,000 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-05 | ADEQUATE | low | ACCEPT | ACCEPT | high | 0 / 0 / 75,000 | 0 / 0 / 75,000 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-06 | CONTRADICTED | low | REJECT | REJECT | medium | 0 / 0 / 0 | 0 / 0 / 0 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-07 | EBITDA_EXCLUDED | low | REJECT | REJECT | high | 0 / 0 / 0 | 0 / 0 / 0 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-08 | OVERLAP | low | REVISE | REVISE | high | 0 / 41,000 / 41,000 | 0 / 41,000 / 41,000 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-09 | RECOVERY_OFFSET | medium | REVISE | REVISE | high | 58,000 / (40,000) / 0 | 58,000 / (40,000) / 0 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-10 | OUT_OF_PERIOD | low | REVISE | REVISE | high | (42,000) / 42,000 / 0 | (42,000) / 42,000 / 0 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-11 | WRONG_PERIOD | low | REVISE | REVISE | high | 0 / 80,000 / 0 | 0 / 80,000 / 0 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-12 | NEEDS_INFO | medium | REQUEST_INFO | REQUEST_INFO | high | none (pending) | none (pending) | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-13 | RECURRING | low | REJECT | REJECT | medium | 0 / 0 / 0 | 0 / 0 / 0 | 1.00 / 1.00 | - | PASS |
| meridian_mechanical | M-14 | ADEQUATE | medium | ACCEPT | ACCEPT | high | 0 / 52,000 / 52,000 | 0 / 52,000 / 52,000 | 1.00 / 1.00 | - | PASS |

## 5. Treatment accuracy by case type

| Case type | Correct | Accuracy |
| --- | --- | --- |
| ADEQUATE | 3/3 | 100.0% |
| CONTRADICTED | 2/2 | 100.0% |
| EBITDA_EXCLUDED | 1/1 | 100.0% |
| NEEDS_INFO | 2/2 | 100.0% |
| OUT_OF_PERIOD | 1/1 | 100.0% |
| OVERLAP | 1/1 | 100.0% |
| RECOVERY_OFFSET | 1/1 | 100.0% |
| RECURRING | 2/2 | 100.0% |
| WRONG_PERIOD | 1/1 | 100.0% |

### By the tool's own confidence

| Tool confidence | Correct | Accuracy |
| --- | --- | --- |
| high | 10/10 | 100.0% |
| medium | 4/4 | 100.0% |

## 6. How these numbers are computed

- A tool GL link is *supporting* when `supports_claim` is true and the entry is not listed on a removing flag (already excluded, overlap, contradiction, continuing obligation, recurring pattern) for the same adjustment. Links map to GL rows via `GL-R<row>`.
- *Surfaced* rows are rows shown anywhere in the adjustment's evidence (links, flag entries, recurrence observations), measured against the key's supporting and related rows.
- Deal and overall rates pool the underlying counts (micro-average). The false accept rate's denominator is the number of adjustments the key does not accept.
- Extra flags are not penalized; the key lists the flags that must be raised, not the only acceptable ones.
- Amounts are USD, rounded to the dollar here; the JSON report carries cents.

