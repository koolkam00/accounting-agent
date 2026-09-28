# QoE Evidence Review: 2-minute demo script

**Audience:** transaction-advisory practitioners.

**Package:** Meridian Mechanical Services, LLC (SYNTHETIC), at `data/qoe/dev/meridian_mechanical`. Every number below comes from `docs/qoe/SPEC.md` §10.

**Headline case:** M-01. Management's $120,000 legal-fee add-back is really two matters. The tool ties the invoices to the ledger and separates the Dawson litigation, which is $84,500 in FY2025, from a general corporate retainer that recurs. It shows documented facts apart from the judgment call that remains open.

**How to talk about it.** Say "the tool proposes", "the evidence shows" and "I decide". Never say "the AI decided" or "the AI calculated": amounts and treatments are computed by code, and the reviewer makes the call.

> This script shows the answers for D1 (Meridian). Don't show it, or the demo, to anyone who will later be a benchmark participant (`benchmark_protocol.md` §5.1).

---

## Before you start (not on the clock)

1. **Build and run into a scratch workpaper folder.** Demo decisions go into an append-only `review_log.jsonl`. A review log that feeds `scripts/qoe_corrections_to_evals.py` must never contain demo clicks. Use a fresh `--out` folder for each demo day rather than deleting a log.

   ```bash
   uv run python scripts/qoe_generate_deals.py   # only if data/qoe/dev/meridian_mechanical is missing (check --help)
   uv run python scripts/qoe_run.py --deal data/qoe/dev/meridian_mechanical --out workpapers/demo --xlsx
   uv run streamlit run qoe/ui.py
   ```

   The run writes `workpapers/demo/meridian_mechanical/workpaper.json` and `QoE_Evidence_Review_meridian_mechanical.xlsx`. It runs in rules mode, which is deterministic and happens locally.

2. **Check the screen against the number sheet below** for M-01, M-08 and M-09. If anything differs, **don't demo that beat and don't improvise numbers**. Either the build has regressed or this sheet is stale.

3. **Set up the screen:**
   - browser zoom at 125%, with the sidebar open;
   - the demo workpaper selected, and the adjustment list showing;
   - Excel already running with an empty workbook, so the export opens in about 2 seconds.

4. **Put this M-01 rationale on the clipboard:**
   > Carry Matter 2291 (Dawson) only: five invoices tie to 6400 by invoice number. Matter 1004 is a general corporate retainer under a 2023 engagement letter continuing until terminated, and ran $36,000 in FY2024, so it is part of the ongoing cost base. Open: post-settlement fees; insurer payment of the settlement.

5. **Fallback.** If the app fails, open `workpapers/demo/meridian_mechanical/QoE_Evidence_Review_meridian_mechanical.xlsx` and run the same beats from the **Adj M-01**, **Adj M-08**, **Adj M-09** and **EBITDA Bridge** sheets.

### UI labels this script assumes

`qoe/ui.py` was being built at the same time as this script. At the first rehearsal, check each label against the app and **update this table**. The narration doesn't depend on the labels.

| Element | Assumed label in the app | Beat |
| --- | --- | --- |
| Workpaper picker (sidebar) | **Workpaper** → `meridian_mechanical` (demo folder) | setup |
| Adjustment list | **Adjustments** view: Ref, Title, Treatment colour, key flags | 0:00 |
| Open one adjustment | Click the row, or **Adjustment** select → `M-01` | 0:10 |
| Tie-out table | **Tie-out**: Claimed / Traced GL / Documented / Proposed by period | 0:10 |
| GL links grouped by matter | **GL links** (expander, grouped) | 0:22 |
| Documents and verbatim quotes | **Documents** (expander) | 0:22, 0:40 |
| Flags and recurrence | **Flags**, **Recurrence** | 0:40 |
| Facts vs judgment | **Documented facts**, **Judgment questions** (block names from SPEC §8) | 0:56 |
| Questions for management | **Open questions** | 0:56 |
| Review form | **Review decision**: Treatment, amounts (pre-filled with the tool's proposal), **Correction type**, **Rationale**, **Save decision** | 1:08 |
| Export | **Export** → **Download Excel workpaper** | 1:45 |

---

## The script

| Time | Click | Say |
| --- | --- | --- |
| **0:00–0:10** | The app is open on **Adjustments**, with the Meridian demo workpaper selected. | "Synthetic QoE: an HVAC contractor, fourteen management add-backs. The tool has checked each against the general ledger and the data room. I make the calls." |
| **0:10–0:22** | Click **M-01**. Point at the **Tie-out** rows *Claimed* and *Traced GL*. | "M-01: a $120,000 legal-fee add-back, described as Dawson litigation. Is it in the ledger? Yes. Traced GL ties to the claim: $120,000 in FY2025, $65,500 TTM." |
| **0:22–0:40** | Expand **GL links**. Point at the two groups, Matter 2291 and Matter 1004. Click invoice **25-0212** to show its linked document and quote. | "But it's two matters, not one. Matter 2291, Dawson: five invoices, each tied to its ledger line by invoice number. $84,500. Matter 1004, general corporate: a $2,500 monthly retainer, plus a $5,500 policy review." |
| **0:40–0:56** | Open **Flags**, then **Recurrence**: Matter 1004 FY2024 $36,000. Open **Documents** → the 2023 Matter 1004 engagement letter quote. Point at *Proposed*. | "Is the retainer one-time? Matter 1004 ran $36,000 in FY2024. The engagement letter, quoted verbatim: $2,500 per month, continuing until terminated. So the tool proposes $84,500 for FY2025 and $30,000 TTM: Dawson only." |
| **0:56–1:08** | Scroll to **Documented facts**, then **Judgment questions**, then **Open questions**. | "Facts carry a GL row or a verbatim quote. The judgment call, whether the retainer is ongoing cost, stays with me. For management: any fees after the November settlement, and did the insurer pay it?" |
| **1:08–1:15** | **Review decision**: leave Treatment = REVISE and the pre-filled amounts, set **Correction type** = NONE, paste the **Rationale**, click **Save decision**. | "I agree with the revision. Record it, rationale, save. It's in the review log." |
| **1:15–1:30** | Click **M-08**. Point at the CRITICAL **OVERLAP_WITH_OTHER_ADJUSTMENT** flag, which names M-01, then at *Proposed*. | "M-08: $62,000 of transaction fees. Critical flag: invoice 25-0910, $21,000, is a Dawson invoice already in M-01. Counted twice. The tool leaves it in M-01 and carries $41,000: Keel Harbor and Dunmore & Pike." |
| **1:30–1:45** | Click **M-09**. Point at the **OFFSETTING_RECOVERY** flag, then at *Proposed*: 58,000 / (40,000) / 0. | "M-09, storm repairs: $58,000 in FY2024, supported. But the insurer paid $40,000 in February 2025, booked to other income and not adjusted. If the loss comes out, so does the recovery: minus $40,000 in FY2025." |
| **1:45–2:00** | **Export** → **Download Excel workpaper** → open the file. Click a subtotal on **EBITDA Bridge** so the `=SUM(…)` shows in the formula bar. Click the **Adj M-01** tab, then **Review Log**. | "Everything exports to Excel. The bridge subtotals are live formulas. Each adjustment gets a support sheet: tie-out, GL rows, verbatim quotes, facts apart from judgment. And my decision is in the review log." |

**If you only get one sentence:** "The GL has the $120,000. The documents support $84,500 of it as Dawson litigation. The other $35,500 is a retainer the buyer keeps paying."

---

## Number sheet (SPEC §10: check it against the screen before every demo)

Periods are FY2024 (Jan–Dec 2024), FY2025 (Jan–Dec 2025) and TTM Jun-26 (Jul 2025–Jun 2026). TTM shares Jul–Dec 2025 with FY2025.

### M-01: Dawson litigation legal fees (acct 6400), treatment REVISE

| | FY2024 | FY2025 | TTM Jun-26 |
| --- | ---: | ---: | ---: |
| Claimed by management | 0 | 120,000 | 65,500 |
| Traced GL, as on screen (claimed entries only) | 0 | 120,000 | 65,500 |
| Memo: all Hollis & Crane activity in 6400 | 36,000 | 120,000 | 65,500 |
| Tool proposed / key | 0 | 84,500 | 30,000 |
| Revision | 0 | (35,500) | (35,500) |

- **Matter 2291, *Dawson v. Meridian*:**

  | Invoice | Month | Amount |
  | --- | --- | ---: |
  | 25-0212 | Feb 2025 | 14,500 |
  | 25-0418 | Apr 2025 | 22,000 |
  | 25-0615 | Jun 2025 | 18,000 |
  | 25-0910 | Sep 2025 | 21,000 |
  | 25-1120 | Nov 2025 | 9,000 |
  | **FY2025 total** | | **84,500** |
  | TTM portion (Sep and Nov) | | 30,000 |

- **Matter 1004, *General Corporate & Employment*.** The retainer is $2,500 a month, every month from 2024 to 2026, which is $30,000 a year. There are two ad hoc items: $6,000 in Oct 2024, and $5,500 in Aug 2025 for an employment policy review.

  | | FY2024 | FY2025 | TTM |
  | --- | ---: | ---: | ---: |
  | Retainer | 30,000 | 30,000 | 30,000 |
  | Ad hoc | 6,000 | 5,500 | 5,500 |
  | **Matter 1004 total** | **36,000** | **35,500** | **35,500** |

- **Tie-back.** FY2025: 84,500 + 35,500 = 120,000. TTM: 30,000 + 35,500 = 65,500.
- **Documents:**
  - the 2023 Matter 1004 engagement letter ("$2,500 per month … continuing until terminated by either party"; read the exact quote as it appears on screen);
  - the Jan 2025 Matter 2291 engagement letter;
  - all five litigation invoices;
  - a sample retainer invoice;
  - the Aug 2025 policy-review invoice;
  - the settlement agreement dated 2025-11-14, under which the insurer pays the settlement. It has no GL effect.
- **Flags:** RECURRING_PATTERN and CONTINUING_OBLIGATION.
- **Questions for management:** confirm there are no post-settlement fees or obligations, and confirm the insurer paid the settlement.

### M-08: transaction-related professional fees (accts 6400, 6410), treatment REVISE

| | FY2024 | FY2025 | TTM Jun-26 |
| --- | ---: | ---: | ---: |
| Claimed | 0 | 62,000 | 62,000 |
| Tool proposed / key | 0 | 41,000 | 41,000 |

- **What management claimed (62,000):**
  - Keel Harbor Advisors, sell-side retainer: 26,000 (Oct 2025, 6400).
  - Dunmore & Pike CPAs, sell-side readiness: 15,000 (Nov 2025, 6410).
  - Hollis & Crane invoice **25-0910**: 21,000 (Sep 2025, Matter 2291 Dawson). This is already in M-01.
- **Flag:** OVERLAP_WITH_OTHER_ADJUSTMENT (CRITICAL), related to M-01. M-01 keeps the entry because it has the stronger link: the matter number. Without the catch, adjusted EBITDA is overstated by 21,000 in both FY2025 and TTM.

### M-09: storm damage repairs (acct 6150), treatment REVISE

| | FY2024 | FY2025 | TTM Jun-26 |
| --- | ---: | ---: | ---: |
| Claimed | 58,000 | 0 | 0 |
| Tool proposed / key | 58,000 | (40,000) | 0 |

- **The cost:** Gulf Coast Roofing 38,000 and Tampa Bay Restoration 20,000, in Oct–Dec 2024, after an October 2024 hurricane.
- **The recovery:** Sunshine Mutual Insurance paid **40,000** in Feb 2025 on claim #FL-24-88172. The payment is booked to 8000 Other Income. The claim settlement letter shows 40,000 net, after a 10,000 deductible. Feb 2025 falls outside the TTM window, so TTM is 0.
- **Flag:** OFFSETTING_RECOVERY.

### Workbook (SPEC §8)

- **File:** `QoE_Evidence_Review_meridian_mechanical.xlsx`.
- **Sheets:** Cover (with a SYNTHETIC banner, run id, tool version, AI mode, input hashes) · EBITDA Bridge (subtotals are formulas) · Adjustment Summary · one support sheet per adjustment (`Adj M-01` …) · Open Questions · GL-P&L Reconciliation · Data Quality · Review Log.

---

## If asked

| Question | Answer |
| --- | --- |
| "Does the AI decide the amount?" | "No. The AI layer, or deterministic rules as in this run, reads documents and management's narrative and proposes facts, links and question wording. Code computes every amount and treatment from GL entries. I make the final call. Every quote is checked as an exact substring of the cited page. One that isn't found is dropped and counted, never repaired." |
| "How accurate is it?" | Point to `reports/qoe/eval_<split>.md`. Quote only numbers you've actually run, and say which split they come from. "Meridian is a development package: the tool was built against it, so I don't quote Meridian as accuracy. The held-out package is the honest number." |
| "Will it read our client's GL?" | "Today it reads QuickBooks Online GL CSVs, NetSuite saved-search CSVs, and Xero Account Transactions exports. Another system needs a reader." |
| "Scanned PDFs?" | "It reads the text layer only. An image-only page comes through as empty text, so you'll see missing document support rather than an invented quote." |
| "Where does the data go?" | "Rules mode runs locally. LLM mode sends document text to whichever OpenAI-compatible endpoint you configure. Whether that's allowed is a firm and client decision." |
| "What if I disagree with it?" | "I override it with a rationale and a correction type. The log is append-only. Corrections marked as tool errors become regression cases." |

## Don't say

- "Audit", "assurance", or "verified" in the assurance sense. Say *tied*, *traced*, *supported*.
- "The AI found $35,500." Code computed it from GL entries that the evidence classified.
- Any accuracy percentage from Meridian or other dev data.
- "It replaces the senior." It replaces the tie-out and the searching. The senior still makes the calls.
- Any real client, target or firm name.
