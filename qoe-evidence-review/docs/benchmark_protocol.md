# QoE Evidence Review: benchmark protocol

Status: **draft for pre-registration.** Freeze this file before the first scored session, and record the protocol version (commit or sha256) in the report. If you change the protocol after that, log the change as a deviation. Don't edit it silently.

This protocol compares three ways of reviewing seller-proposed EBITDA adjustments on the synthetic deal packages in `data/`. The goal is to find out, with honest numbers, whether the tool helps a practitioner reach the right answer faster **without adding dangerous errors**. Metric definitions follow `docs/SPEC.md` §9 exactly, so the human arms and the automated evaluation can be read side by side.

---

## 1. The question

For a management adjusted-EBITDA schedule and its data room, does **tool + reviewer** (arm C) produce correct diligence conclusions at least as often as the way associates work today (arm A) and as a general-purpose AI assistant given the same files (arm B)? Does it make fewer dangerous errors? And does it take less practitioner time?

**Primary endpoints.** These are pre-registered and reported first, in this order:

1. **False accepts.** The participant (or tool) carries management's number when the key says REVISE, REJECT or REQUEST_INFO. This is the error that hurts a buyer.
2. **Incorrect adjustment recommendations.** A count and a dollar amount (§9.2).
3. **Total practitioner time per package.** Preparation plus review, in minutes.

Every other metric is secondary.

**What this study can and cannot show.** With 2–4 participants it can surface failure modes, give a rough sense of time magnitudes (20% faster or 5× faster?), and collect practitioner reactions. It cannot establish that one arm is better in a statistical sense. See §11.

---

## 2. Roles and independence

| Role | Does | Must not |
| --- | --- | --- |
| **Developer** | Builds and tunes the tool. May answer factual questions about what the tool did. | Author or review the held-out package or its key. See the held-out package before the code freeze. Adjudicate. Observe sessions. |
| **Key author** | Writes the package spec and `ground_truth.json` for a package. | Participate as a benchmark participant. |
| **Key reviewer** | A second practitioner. Reviews every answer key before it is locked, and is adjudicator 1. | Participate. Author the key they review. |
| **Study lead / observer** | Runs sessions, keeps the timing log, answers procedural questions only. | Answer substantive questions ("is this recurring?"). Be the developer. |
| **Scorer** | Scores answer sheets against the locked key. Should not be the developer. | Change the key. |
| **Adjudicator 2** | A practitioner who is neither developer nor participant. | Be told the arm before the classification is recorded (§10). |

If you have four people available and one of them has never seen the packages, consider using that person as the key reviewer rather than as a fourth participant. Once they have reviewed a key, they cannot participate.

---

## 3. Arms

| Arm | Participant has | Not allowed | Deliverable |
| --- | --- | --- | --- |
| **A: Manual** | A read-only copy of the data room, Excel, a PDF viewer, and templates rebuilt from memory. No firm IP is brought in. | Any AI feature, including Copilot in Excel or Windows and browser AI sidebars. This tool. Internet. | `answer_sheet.csv`, plus any working Excel they want to keep. |
| **B: General AI assistant** | Everything in A, plus **one** assistant account supplied by the study lead. The product, model and version are pinned and recorded. File upload and code execution are allowed. Memory and personalisation are off, and every session starts in a fresh chat. | This tool. Other assistants. Internet beyond the assistant. | `answer_sheet.csv`, plus an export of the full assistant transcript. |
| **C: Tool + reviewer** | Everything in A, plus QoE Evidence Review at the pinned commit and AI mode. The participant starts the run, reviews in the Streamlit app (`uv run streamlit run qoe/ui.py`), records decisions and exports. Any source file can be opened to check the tool. | A general AI assistant. Internet. | `answer_sheet.csv`, the `review_log.jsonl`, and the exported workbook. |

**Rules common to all arms:**

- Every arm gets the same brief (Appendix A), the same time box (§6), and the same answer sheet.
- Nobody answers management questions. Participants write them on the answer sheet and that is where they stay. Real engagements have management calls, and this benchmark does not (§12).
- The data room copy excludes `ground_truth.json` and any generator spec. The observer checks the folder against a manifest before each session.
- Participants don't discuss packages with each other until everyone has finished.

**Arm C failures are results.** If the tool fails to run, the observer may restart it once (time counted). If it still fails, the participant continues with the data room alone. The session is reported as **"C (tool failed)"**. It is neither excluded nor merged into arm A.

**Arm B's starting point.** The assistant gets the same brief as every other arm, and participants may paste it in as their opening prompt. After that they prompt however they normally would. Nobody gives arm B a prompt written by the developer, because it would carry the tool's checklist into the comparison. Prompt skill is a threat to validity, not something the protocol can control (§12).

---

## 4. Packages

| Code | deal_id | Split | GL format | Key author | Key reviewer | # adjustments | Package sha256 | Key sha256 (locked) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D0 | *(practice)* | practice | any | | | | | *(not scored)* |
| D1 | `meridian_mechanical` | dev | `qbo_gl_csv` | | | 14 | | |
| D2 | *(dev deal 2)* | dev | `netsuite_csv` | | | | | |
| D3 | *(held-out deal)* | holdout | `xero_xlsx` | | | | | |

The study lead fills this table in before session 1 and copies it into the report.

**Practice package D0.** Build D0 with `scripts/qoe_generate_deals.py` from a spec that contains **only clean (ADEQUATE) adjustments**. It exists to teach the mechanics: the data-room layout, the answer sheet, the citation format, the assistant account, and the tool UI. It must not teach what to look for, so it contains no planted issue types. D0 is not scored.

### 4.1 Held-out package rule

A package counts as **held out** only if all of the following are true. If any one is not, the report says so in its first paragraph and the package is called a dev package.

1. **Independent author.** Someone other than the developer authored and answer-keyed it. "Developer" means anyone who wrote or tuned engine, AI or prompt code, or chose thresholds.
2. **Not viewed during development.** The package stays out of the working tree until the code freeze. It is handed over as an archive, with its sha256 recorded at handover. Before the freeze, the developer never opens its files, a workpaper run on it, or any evaluation output for it.
3. **One-shot evaluation.** At the code freeze, record the commit hash. The developer runs the tool-only evaluation on D3 **once**. Arm C sessions that rerun the same frozen commit do not use up the holdout. **Any** change under `qoe/` after that first run does use it up, including a "tiny" fix. From then on, results on D3 are reported as dev results, with the reason.
4. **Key reviewed by a second practitioner** before any run or session (§4.2).

Dev packages D1 and D2 go through the same key review. Even so, they remain dev packages: the developer wrote them and the tool was tuned on them. **The headline comparison uses D3.** D1 and D2 results are reported in their own columns, labelled "tool developed against this package".

### 4.2 Answer-key review and lock

- The key reviewer reads the package and the key independently and records **agree / disagree / comment** for every adjustment. Items the key marks `ambiguity: medium` or `high` get particular attention. For each one, the reviewer writes down what a careful senior could defensibly conclude instead.
- The author and reviewer resolve each disagreement. The outcome is either a corrected key, or `ambiguity: high` plus a pre-registered alternative.
- **Pre-registered alternatives** go in `key_alternatives.csv` in the study folder (§14), with the columns `package, adj_id, alt_treatment, alt_amounts, rationale, approved_by`. Example: Meridian M-14 bad debt has the key **ACCEPT 0 / 52,000 / 52,000**, and SPEC §10 notes that some seniors accept only the excess over normal monthly bad debt. That REVISE is a legitimate pre-registered alternative.
- Lock the key before session 1 by recording the sha256 of `ground_truth.json` and `key_alternatives.csv` in the package table. Once locked, alternatives cannot be added. Anything discovered later goes through adjudication (§10).

---

## 5. Participants and assignment

### 5.1 Participants

- **Who.** 2–4 current or former Deals associates or seniors, with roughly 2–7 years of QoE work. At least one should have run add-back review as the senior on an engagement.
- **Exclusions.** The developer. Key authors and reviewers. Anyone who has seen the tool, the packages, the keys or the demo (`docs/demo_script.md` shows D1's answers).
- **What to record, bucketed and anonymised.** The most recent Deals title, years in transaction services (2–3 / 4–5 / 6+), main sectors, a self-rated Excel level, and how often they use general AI assistants at work (none / occasional / daily).
- **Pay.** A professional hourly rate, not tied to performance.
- **Consent.** Participants consent to screen recording and to publication of anonymised results. IDs run `P01`–`P04`. Names never appear in study files.
- **Participants who are also interviewed.** Run the discovery interview (`practitioner_interview_guide.md` Part 1) before session 0. Run the tool walkthrough (Part 2) only **after** their last scored session, because it uses D1.

### 5.2 Latin-square assignment (3 packages × 3 arms)

The design is a 3 × 3 Graeco-Latin square. Rows are participants, columns are session order, and each cell is an arm × package pair.

| Row | Session 1 | Session 2 | Session 3 |
| --- | --- | --- | --- |
| R1 | A · D1 | B · D2 | C · D3 |
| R2 | B · D3 | C · D1 | A · D2 |
| R3 | C · D2 | A · D3 | B · D1 |

Properties:

- Each participant sees each package once and each arm once, so nobody reviews the same package twice.
- Each arm meets each package exactly once across R1–R3.
- Each arm and each package appears once in each session position, which balances order.

| Participants | Rows used | What is lost |
| --- | --- | --- |
| 3 (preferred) | R1, R2, R3 | Nothing. This is the full square. |
| 2 | R1, R3 | The cells A·D2, B·D3 and C·D1. Both A and C are still tested on the held-out D3, so the headline "tool vs current practice" comparison survives. B vs C is compared on dev packages only. Say so in the report. |
| 4 | R1, R2, R3, plus **R4 = C · D3, B · D2, A · D1** | R4 has R1's pairs in reverse order, which gives a direct check on order and carryover for identical cells. C·D3 gets two observations and the other D3 cells get one. Report R4 both separately and pooled. |

**Assigning rows.** Assign participants to rows with a seeded shuffle, and record both the seed and the result in `assignment.csv`.

**Scheduling.**

- Hold one session per participant per day, with sessions at least 2 and at most 14 days apart.
- Keep the same time of day where possible.
- Run **session 0 (familiarisation, 45 minutes)** before session 1. Every participant sees all three setups on D0 in that session, whatever their row. This way arm C's UI is not brand-new for some participants and familiar for others.

---

## 6. Session procedure

**Before the session:**

- Make a fresh read-only copy of the package, and check it against the manifest.
- Arm B: open a new chat, and confirm that memory is off.
- Arm C: check the pinned commit and AI mode, and prepare an empty workpaper output folder for this session, for example `workpapers/benchmark/<participant>_<package>/`. The review log starts empty. Write the run command on the arm card, so running it is part of the timed work: `uv run python scripts/qoe_run.py --deal <session copy> --out workpapers/benchmark/<participant>_<package> --ai <pinned mode> --xlsx`. If the app has its own run control, use that instead. Keep these folders out of any review log that `scripts/qoe_corrections_to_evals.py` reads, until adjudication has confirmed the correction labels (§9.2).
- Start the screen recording.

**During the session:**

| Step | Minutes | Timed? |
| --- | --- | --- |
| Read the brief (Appendix A) and ask procedural questions | ≤ 10 | No |
| Work: preparation and review, in any order the participant would use on a real engagement | **180 soft cap / 240 hard stop** | Yes |
| Per-session feedback (`templates/participant_feedback.md`, Part A) | ≤ 5 | No |

**The time box:**

- The observer gives a warning at minute 170.
- At minute 180, the observer saves a copy of the answer sheet as it stands. This snapshot is scored as **@180**.
- The participant may keep going to the hard stop at 240 minutes to finish. The final sheet is scored as **final**.
- Adjustments not reached by the hard stop get the treatment `NOT_REACHED`.
- Both snapshots are reported. @180 answers "what did the budget buy?", and final answers "how accurate is the work when it is finished?"

**During the work:**

- The observer answers only procedural questions, such as where a file is or how to cite something. Every question asked is logged in the timing-log `notes`.
- Breaks are allowed. They are logged as interruptions and the clock stops.
- **Technical outages** (laptop, network, assistant service) are logged as interruptions for up to 30 minutes. Beyond that, the session ends and is reported as *incomplete, with reason*. Waiting for the tool to run or for the assistant to answer is **not** an interruption: it is part of what the arm costs.

---

## 7. Timing: preparation vs review

The **observer keeps the timing log live** (`templates/timing_log.csv`). Participants say "starting M-03" or "back to the GL" as they switch, and the observer reconciles the log against the screen recording within 48 hours. Participants don't keep time themselves, because logging your own time costs time and adds error.

**Definitions.** The test: *if you are looking at a specific adjustment's evidence, it's review. If you are getting data into a shape where you could look at evidence, it's prep.* Checking the tool's or the assistant's output is **review**, never prep.

| | Preparation (`phase = prep`) | Review (`phase = review`) |
| --- | --- | --- |
| All arms | Opening and indexing the data room. Reading the schedule to plan. | Reading documents against GL entries. Tying out. Deciding treatment and amount. Writing questions. Filling the answer sheet. |
| A | Importing the GL into Excel, cleaning it, adding a row-number column, building pivots, mapping accounts, and GL-to-P&L reconciliation set-up. | Filtering to one adjustment's activity and working it. |
| B | Uploading files, writing the opening prompts, and waiting for a package-level answer. | Interrogating the assistant about one adjustment, and checking what it says against the source. |
| C | Starting the run, waiting for it, and loading the workpaper in the app. | Reading one adjustment's links, quotes and flags, checking them against the source, and recording the decision. |

**Logging rules:**

- Start a new row whenever the participant switches `adj_id` or `phase`. A switch shorter than 1 minute is folded into the current row.
- Package-level work uses `adj_id = PKG`. Prep that serves one adjustment only (for example, pulling one vendor's detail) is logged against that `adj_id` with `phase = prep`.
- Data-quality work uses `adj_id = PKG`. The GL/P&L reconciliation is package-level prep. Writing up a DQ finding is `review` against `PKG`.
- `start_iso` and `end_iso` are ISO 8601 with an offset, for example `2026-10-06T14:05:00-04:00`.
- `interruptions` is the **whole minutes** of interruption inside the row's interval. `minutes = round((end − start) / 60 s) − interruptions`. Describe each interruption in `notes`.
- After the session, the observer fills in `time_minutes` on each answer-sheet row. It is the sum of that adjustment's `review` and adjustment-level `prep` minutes.

---

## 8. The answer sheet

`templates/answer_sheet.csv` is the deliverable in **every** arm. Filling it in counts as review time in every arm. Real work includes documenting conclusions, and the burden is the same across arms.

| Column | Content |
| --- | --- |
| `participant_id`, `arm`, `package` | Filled in by the observer (`P01`, `A`/`B`/`C`, `D1`–`D3`). |
| `adj_id` | Management's Ref, verbatim. Special rows are listed below. |
| `treatment` | `ACCEPT`: carry management's amounts. `REVISE`: carry a different amount in at least one period. `REJECT`: carry zero in every period. `REQUEST_INFO`: can't conclude without more information, and the item is excluded from diligence-adjusted EBITDA pending a response. `NOT_REACHED` is entered by the observer. |
| `amount_p1` … `amount_p3` | The amount diligence would carry for each analysis period, in `deal.yaml` order (the header note says the same). Amounts are **EBITDA-signed**: + increases EBITDA. Write every period, including zeros. Blank is read as 0.00, except on REQUEST_INFO rows, where amounts are ignored. Put a provisional view for a REQUEST_INFO row in `key_evidence`. If a package has more periods, add `amount_p4` and so on. The scorer parses amounts with `qoe.money.D`, so `84500`, `84,500.00`, `$84,500` and `(40,000)` all work. |
| `key_evidence` | What you relied on and what it shows, in the form `Support: …; Context: …; Docs: …; Basis: …` (explained below). |
| `open_questions` | Questions for management, separated by ` \| `. |
| `confidence` | `high`, `medium` or `low`: the participant's own confidence in this row. |
| `time_minutes` | Filled in by the observer from the timing log. |

**Citation format in `key_evidence`.** Separate sections with `;` and items within a section with `,`. For example: `Support: GL-R2210, GL-R2245; Context: none; Docs: 9.9 Example Movers Invoice 1182.pdf p1; Basis: two invoices tie to 6100.`

- **`Support:`** lists the GL rows that make up the amount you carry, written as `GL-R<row>`. The row number is the one the source file shows when opened in a spreadsheet (SPEC §3.3), so add a row-number column **before** sorting. A filter description is acceptable instead of a list, for example `6400 where memo contains "Matter 2291", FY2025`. The scorer resolves filters to rows and logs how.
- **`Context:`** lists the rows you cite for another reason: comparables, recoveries, overlaps, or the prior-year pattern.
- **`Docs:`** gives `<file name> p<page>`. If you add a quote, put it in double quotes, copied from the document.
- **`Basis:`** is one line on why.

**Special rows.** These are optional but scored. They map to SPEC §9's `data_quality_recall` and `ebitda_error`.

| `adj_id` | `treatment` | Amounts | Evidence |
| --- | --- | --- | --- |
| `DQ-1`, `DQ-2`, … | `DATA_QUALITY` | EBITDA effect if it can be quantified, otherwise blank. | What the issue is and where: month, account, GL rows. |
| `EBITDA_GL` | `TOTAL` | Reported EBITDA recomputed from the GL, by period. | How it was built. |
| `EBITDA_DILIGENCE` | `TOTAL` | Diligence-adjusted EBITDA by period, excluding REQUEST_INFO items. | The starting point used. |

The scorer drops any leading line that starts with `#`, which is the template's note line, and any row where `participant_id = EXAMPLE`. Don't read these files with a blanket `#`-comment option: a `#` inside a field, as in "claim #FL-…", would truncate the field. The example row in the template is fictional (package `D0`, adjustment `X-01`), so that the template leaks nothing about a scored package.

---

## 9. Metrics

Every metric is computed for **four rows**:

- **Tool only.** `qoe/evaluate.py` on the same commit and AI mode, with no reviewer.
- **Arm A, arm B and arm C.** Arm C uses the reviewer's final answers.

Each metric is reported per package and overall, with D3 shown separately.

### 9.1 SPEC §9 metrics, applied identically

| Metric (SPEC §9 name) | Definition (from SPEC) | Human arms: source and method |
| --- | --- | --- |
| `false_accept_rate` | The answer is ACCEPT when the expected treatment is anything else. **Reported first.** | `treatment` vs key. Report it as a count over a denominator (for example 2/11). The denominator is the one `evaluate.py` uses: attempted adjustments the key does **not** accept. `NOT_REACHED` items are listed separately. |
| `treatment_accuracy` | The answer's treatment equals the expected treatment. | `treatment` vs key. `NOT_REACHED` counts as wrong in "all items" and is excluded in "attempted". Report both. |
| `amount_accuracy` | Over items whose key is not REQUEST_INFO and whose answer is not REQUEST_INFO: every period satisfies abs(answer − expected) ≤ 1.00. | `amount_p*` vs key amounts. |
| `gl_link_precision` / `gl_link_recall` | Claimed-and-supporting links vs `supporting_gl_rows`. Surfaced recall is measured over supporting ∪ related, using every linked row. | `Support:` rows vs `supporting_gl_rows`. Surfaced recall uses `Support:` ∪ `Context:` rows vs supporting ∪ related. |
| `doc_link_precision` / `doc_link_recall` | Doc links vs `supporting_docs`. | `Docs:` file names vs `supporting_docs`. |
| `flag_recall` | The share of `expected_flags` raised on the right adjustment. | Flags coded from the answer-sheet text (§9.3). |
| `missed_contradictions` | Expected CONTRADICTORY_EVIDENCE, RECURRING_PATTERN, CONTINUING_OBLIGATION, OFFSETTING_RECOVERY, OVERLAP_WITH_OTHER_ADJUSTMENT or ALREADY_EXCLUDED_FROM_EBITDA flags that were not raised. | The same list, coded per §9.3. List each miss by package and `adj_id`. |
| `data_quality_recall` | Planted data-quality issues detected, matched on code and month or account. | `DQ-n` rows, coded to a `DataQualityCode` and matched on month or account. |
| `ebitda_error` | abs(answer diligence-adjusted EBITDA − key) for each period, plus agreement on `gl_ebitda`. | The `EBITDA_DILIGENCE` and `EBITDA_GL` rows. If a row is missing, report "not produced", not zero. |
| `by_case_type` | Treatment accuracy grouped by the key's `case_type`. | The same grouping. |

### 9.2 Human-only metrics

| Metric | Definition |
| --- | --- |
| **Practitioner time per package** | The sums of `prep`, `review` and total minutes, net of interruptions. Also the number of adjustments completed by the 180-minute snapshot and by the hard stop. |
| **Practitioner time per adjustment** | *Direct* time is the adjustment's review plus its adjustment-level prep. *Fully loaded* time is direct time plus the package-level (`PKG`) prep divided by the number of adjustments attempted. State which one a table shows. |
| **Time per correct adjustment** | Total package minutes divided by the number of adjustments whose treatment and amounts are correct. This one figure captures the speed–accuracy trade-off. |
| **Incorrect adjustment recommendations** | Answers where the treatment differs from the key, or where the amounts are off by more than 1.00 in any period on a concluded item. Split them into: **false accept**; **wrong amount** (right direction, wrong number); **over-reduction** (REJECT, or REVISE down, where the key accepts); **unnecessary REQUEST_INFO** (the key concludes); **missed REQUEST_INFO** (concluded where the key says REQUEST_INFO). **Dollar error** is Σ abs(answer − key) by period over concluded items. Report it by period, with no multiple applied. |
| **REQUEST_INFO rate** | The share of attempted items answered REQUEST_INFO, compared with the key's share. A review that asks for more information on everything is not useful, even though it never falsely accepts. |
| **Missed contradictions** | As defined in §9.1 and listed item by item. This is the qualitative core of the comparison. |
| **Evidence-link accuracy** | Every citation in `key_evidence` (a GL row, a resolved filter, a document and page, or a quote) is checked and classed as **correct** (it exists and supports the point), **wrong** (it exists but does not support the point) or **fabricated** (the row, file or page does not exist, or a quoted string is not on the cited page). Quotes are compared with whitespace collapsed and case kept, against the same canonicalised page text the tool uses (`qoe.pdf_text`). Report correct/total, and report fabricated as its own count. Arm B's fabricated quotes are the headline number here. |
| **Reviewer corrections (arm C)** | Taken from `review_log.jsonl`: the number of adjustments where the reviewer's final answer differs from the tool's proposal, broken down by the `correction_type` the reviewer chose. Each one is then adjudicated against the key and classed as: **fixed tool error** (the tool was wrong and the reviewer corrected it); **uncorrected tool error** (the tool was wrong and the reviewer let it stand, which is automation bias and the most important arm C failure); **introduced error** (the tool was right and the reviewer made it wrong); **judgment difference**; or **new information** (this should be about zero, because nobody answers questions). The **reviewer's net effect** is fixed minus introduced. |
| **Correction-label accuracy (arm C)** | The share of overrides where the reviewer's label (tool error vs `JUDGMENT_DIFFERENCE` / `NEW_INFORMATION`) matches the adjudicated class. This matters because tool-error labels feed `scripts/qoe_corrections_to_evals.py` as regression cases, and a mislabelled correction teaches the eval set the wrong thing. |
| **Confidence calibration** | The error rate within each stated confidence level. In arm C, look for wrong answers marked `high`, where they only agree with the tool. |
| **Assistant errors carried (arm B, optional)** | Wrong factual claims by the assistant, coded from the transcript, that ended up on the answer sheet. |

### 9.3 Coding flags from answer-sheet text

The tool raises flags directly. Human answers are coded:

- **Two coders** code independently and resolve disagreements by discussion. Report their raw agreement.
- **Substance, not vocabulary.** A flag counts as raised if the row's `key_evidence` or `open_questions` identifies the issue **specifically for this adjustment**.
- **Generic questions don't count.** "Is this recurring?" does not count. "The prior year shows $40,000 from the same vendor for the same service. Why is it non-recurring?" does.

| Flag | Counts as raised when the answer… |
| --- | --- |
| NO_GL_SUPPORT | says the claimed amount cannot be found in the GL. |
| PARTIAL_GL_SUPPORT | says the GL supports less than the claim, and roughly how much less. |
| EXCESS_GL_ACTIVITY | notes that the GL holds more related activity than was claimed, and identifies the claimed subset. |
| NO_DOCUMENT_SUPPORT | says a material part of the claim has no supporting document. |
| DOC_GL_AMOUNT_MISMATCH | notes that a document's amount differs from the GL entry it supports. |
| PERIOD_MISMATCH | says the claim sits in a period where the cost was not incurred. |
| OUT_OF_PERIOD | says a cost booked in one period relates to service in another, and moves it. |
| RECURRING_PATTERN | identifies comparable activity in another period, naming the period or the amount. |
| CONTINUING_OBLIGATION | cites a term, retainer or renewal showing that the cost continues. |
| OVERLAP_WITH_OTHER_ADJUSTMENT | identifies the same entry claimed in two adjustments, and names the other one. |
| ALREADY_EXCLUDED_FROM_EBITDA | notes that the cost sits in interest, tax or D&A, so it is already outside EBITDA. |
| OFFSETTING_RECOVERY | identifies a related recovery or income that management did not adjust. |
| CONTRADICTORY_EVIDENCE | cites a document that contradicts management's characterisation. |
| UNSIGNED_OR_DRAFT_SUPPORT | notes that the support is a draft or unsigned. |
| PRO_FORMA_NOT_REALIZED | notes that the saving or event has not happened in the GL. |
| SIGN_ERROR | notes that the claim's sign is wrong for the entries behind it. |
| DUPLICATE_GL_ENTRY | notes that a claimed entry is posted twice. |
| NORMALIZATION_BENCHMARK_MISSING | notes that nothing supports the normalised level. |

---

## 10. Scoring and adjudication

1. **Mechanical scoring.** The scorer compares every answer sheet with the locked key, whether by script or spreadsheet. Inconsistent rows are logged but not corrected. An example is a REJECT row with non-zero amounts. `treatment_accuracy` scores the treatment the participant wrote, and `amount_accuracy` scores the amounts they wrote.
2. **Mismatches go to adjudication.** Participant and arm are replaced with codes first. Adjudicators 1 and 2 classify each mismatch independently. Blinding is only partial, because arm C answers can read like tool output. Record whether each adjudicator believed they could tell the arm.
3. **Classes:**
   - **PARTICIPANT_ERROR**: the key is right.
   - **KEY_ERROR**: the key is wrong. For example, it has an arithmetic slip, or the participant found evidence the author missed.
   - **JUDGMENT_DIFFERENCE**: the answer is defensible and was not pre-registered.
   - **PACKAGE_DEFECT**: the package doesn't contain what the key assumes, such as a missing page or a GL row that doesn't match its document.
   - **NOT_REACHED**.
4. **A disagreement can mean the key is wrong.** Don't presume the key is right. When both adjudicators agree on KEY_ERROR:
   - correct `ground_truth.json` and bump the key version;
   - log the change;
   - **re-score every arm and the tool-only row** under the corrected key;
   - report results under both the original and the corrected key.

   Never correct the key for one arm only.
5. **JUDGMENT_DIFFERENCE** still counts as incorrect in the primary scoring, because the locked key is the standard. It is listed separately, and it counts as correct in a secondary, clearly labelled *post hoc* scoring. It does not become a pre-registered alternative after the fact.
6. **PACKAGE_DEFECT** items are scored as usual. They are listed and fixed in the generator for the next study.
7. **The developer's role.** The developer may answer factual questions about what the tool did (for example, "why did it link GL-R2210?"). The developer does not vote.

`adjudication_log.csv` (in the study folder) has these columns: `case_id, package, adj_id, participant_code, arm (hidden until end), key_answer, participant_answer, class_adj1, class_adj2, agreed, resolution, key_changed, key_version_after, adjudicator_could_tell_arm, notes`.

---

## 11. Sample-size honesty

**What the study has.** With three participants there are nine sessions and about 14 adjustments per package. The decisions are clustered by participant and by package, so they are **not** independent observations.

**Reporting rules:**

- Report **raw counts with denominators** (2/11, not "18%"), every session as its own row, and the **range** across participants (min–max) next to any median.
- Don't report p-values, confidence intervals, or the word "significant".
- Call a direction "consistent in this sample" only if every participant shows it **and** the gap is larger than the spread within an arm. Even then it is an observation, not an effect estimate.
- One uncorrected false accept in arm C on D3 is a finding at any n. Report it prominently.

**What a real claim would need.** The following is rough planning arithmetic, not a power analysis for this design:

- **Time.** Use a paired, within-person comparison of total minutes per package. At 80% power and two-sided α = 0.05, that takes roughly **10–14 participants** for a large effect (standardised d ≈ 0.8–1.0) and **about 35** for a moderate one (d ≈ 0.5).
- **False-accept rate.** To tell 10% from 3%, you need about **200 decisions per arm** where the key is not ACCEPT, before allowing for clustering. The design effect from clustering by participant could plausibly double that. At about 10 non-ACCEPT items per package, this means around 20–40 package-sessions per arm, on **six or more held-out packages from at least two independent authors**, with a pre-registered primary endpoint. That is a funded study, not a favour from friends.

**What the small study is good for:**

- surfacing failure modes;
- checking whether time savings are large enough to matter;
- learning what practitioners need before they would trust the output;
- producing a first batch of reviewer corrections for the regression set.

---

## 12. Threats to validity

| Threat | Likely direction | Mitigation in this design | What the report must show |
| --- | --- | --- | --- |
| **Learning effects.** Participants learn the packages' style and the kinds of issue planted, so later sessions go better whatever the arm. | Favours whichever arm comes later. | The Graeco-Latin square balances position. D0 teaches mechanics, not traps. Sessions are ≤ 14 days apart. | Accuracy and time by **session position**, pooled across arms. |
| **Priming by the tool.** Seeing the tool's flags teaches a participant what to look for in later manual or assistant sessions. | Against the tool: later A and B look better. | Order is balanced. R4, when used, reverses R1. | A/B results split by whether arm C came earlier. |
| **Synthetic data is easier than real.** The PDFs have a clean text layer, file names are consistent, the entity and GL are single, nothing arrives mid-review, and there are no scans, TB/GL breaks or system conversions. | Favours tools, arms B and C, over manual. | None within this study. | A plain statement, with the specific ways the packages are cleaner than a real data room. Ask participants (feedback Part B, Q10). |
| **Trap density.** Most synthetic adjustments hide an issue. In real schedules most add-backs are fine. | Inflates the value of a trap-finder. It also changes false-accept denominators. | Report `by_case_type`. | The share of ADEQUATE items per package, compared with what participants call typical. |
| **Developer-authored dev packages.** The tool was tuned on D1 and D2. | Strongly favours arm C and tool only on D1 and D2. | D3 held out (§4.1). The headline uses D3. | D3 in its own column, with D1 and D2 labelled "developed against". |
| **Assistant prompt skill and model choice.** Arm B depends on who is prompting and which model is used. | Either way. | One pinned assistant, a common brief, familiarisation on D0, transcripts kept. | The model and version, each participant's AI-usage bucket, and transcript excerpts for every B miss. Don't generalise to "AI assistants can't do this". |
| **Hawthorne / observer effect.** Being watched changes how carefully and how fast people work, and trust in the tool may shift when its builder is watching. | It inflates absolute numbers, and could favour or hurt C. | The observer is the same in every arm and is never the developer. Participants are told they are not being evaluated. | An observer log, and any participant remarks on it. |
| **Novelty asymmetry.** Participants have used Excel for years and the tool for 15 minutes. | Against C on time. | Session 0. | Arm C time split into first-hour and later minutes. |
| **Time-box truncation.** | Against the slowest arm on accuracy. | 180 soft / 240 hard, with @180 and final both scored. | Both snapshots. |
| **No management Q&A.** REQUEST_INFO can't be resolved. | Neutral-ish. It caps achievable accuracy on REQUEST_INFO items. | The key reflects what the data room alone supports. | A note. |
| **The key is one senior's judgment.** | Unknown. | A second-practitioner review, pre-registered alternatives, and adjudication that can change the key. | Every key change. |
| **Scorer and coder bias.** | Toward the developer's tool, if the scorer is invested. | An independent scorer, two coders, and partial blinding. | Coder agreement, and whether adjudicators could tell the arm. |
| **Selection.** Participants come from the developer's network. They may be former rather than current practitioners. | Unknown. | Record the buckets in §5.1. | The participant table. |
| **Configuration drift.** The tool commit, AI mode or assistant model changes between sessions. | Either way. | Pin everything and record it every session. | A configuration table per session. |

---

## 13. Reporting

Write the report to `reports/benchmark/<study_id>/report.md`, next to the anonymised raw files (§14).

**Publish what you actually got.** Every session appears in the tables. A tool crash, an assistant hallucination, a participant who ran out of time: each of these is a result.

**Pre-registered exclusions (only these):**

- the participant withdrew;
- a protocol breach (the participant saw a key or another participant's work, or used a forbidden aid);
- an environment failure outside the arm lasting more than 30 minutes.

Everything else stays in. Excluded sessions are still listed, with the reason.

### Pre-registered reading rules

These are fixed before session 1.

- If arm C has **any uncorrected false accept on D3**, the tool is not ready for a pilot on a real engagement, whatever the time savings.
- If arm C is not faster than arm A on fully loaded time per package **for every participant** who did both on comparable packages, we make no claim about time savings.
- If arm B matches arm C on both primary accuracy endpoints and on time, the tool's case rests on its audit trail and workpaper, not its analysis. The report says so.

### Template

```markdown
# QoE Evidence Review benchmark: <study_id>

Protocol version: <commit/sha256>. Dates: <first>–<last session>.
Held-out status of D3: <met / NOT met: reason>.
Deviations from protocol: <none | list>.

## Headline (D3, held out)
| | Tool only | A: Manual | B: AI assistant | C: Tool + reviewer |
| --- | --- | --- | --- | --- |
| False accepts (n / N) | | | | |
| Incorrect recommendations (n / N) · $ error by period | | | | |
| Total minutes (prep + review) | n/a | | | |
| Uncorrected tool errors | n/a | n/a | n/a | |

## Every session
| Participant | Row | Pos | Arm | Pkg | Prep min | Review min | Reached @180 / final | Treatment correct | Amount correct | False accepts | Missed contradictions | Fabricated citations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## SPEC §9 metrics by arm and package
(treatment_accuracy, amount_accuracy, false_accept_rate, gl/doc link P/R, flag_recall,
missed_contradictions, data_quality_recall, ebitda_error, by_case_type:
counts with denominators, D1 / D2 / D3 columns, tool-only row included)

## Time
Per package and per adjustment (direct and fully loaded), median with min–max, and time per correct adjustment.
Results by session position (learning effect check).

## Misses, listed
Every false accept and every missed contradiction: package, adj_id, arm, what was missed, why (from notes/transcript).

## Reviewer corrections (arm C)
| Class | Count | Examples |
(fixed tool error / uncorrected tool error / introduced error / judgment difference / new information),
reviewer net effect, correction-label accuracy.

## Answer-key changes
| Key version | Package | adj_id | Before | After | Reason | Decided by |
Results under original and corrected key.

## Failures and surprises
Tool crashes, assistant outages or refusals, participants who ran out of time, package defects.

## Threats that materialised
From §12, with evidence.

## What we can claim / what we cannot
Two short lists. With n = <n>, no statistical claims.

## Participants (anonymised)
| ID | Title bucket | Years | Sectors | AI-use bucket |
```

---

## 14. Study folder and pre-registration checklist

```
reports/benchmark/<study_id>/
  protocol_version.txt          commit or sha256 of this file at freeze
  packages.csv                  the §4 table, including sha256s of packages and keys
  key_alternatives.csv          pre-registered alternatives (§4.2)
  assignment.csv                participant_id, row, seed
  config.csv                    per session: tool commit, AI mode, assistant product/model/version
  timing_log.csv
  answer_sheets/<participant>_<package>_{at180,final}.csv
  review_logs/<participant>_<package>.jsonl        arm C
  exports/<participant>_<package>.xlsx             arm C
  assistant_transcripts/<participant>_<package>.*  arm B
  adjudication_log.csv
  feedback/<participant>.md
  report.md
```

Screen recordings are never committed. Store them outside the repo, and delete them once timing reconciliation and adjudication are closed. State the retention period in the consent form.

**Before session 1, check each item:**

- [ ] This protocol is frozen and `protocol_version.txt` is written.
- [ ] D3 meets §4.1. If it doesn't, that is written down.
- [ ] Every key has been reviewed by a second practitioner. Alternatives are registered. The key sha256 values are recorded.
- [ ] The tool commit and AI mode are pinned. The tool-only evaluation has run once on D3 at the freeze.
- [ ] The assistant product, model and version are pinned. Memory is off.
- [ ] Rows are assigned with a recorded seed.
- [ ] D0 is built with clean adjustments only. Session 0 is scheduled.
- [ ] The manifests exclude `ground_truth.json`.
- [ ] Consent forms are signed, and recording works.
- [ ] Exclusion criteria and reading rules are copied into the report draft.

---

## Appendix A: participant brief (identical for every arm)

Participants receive only this brief, their arm card and the templates in `docs/templates/`. They never receive the full protocol, which contains examples from D1, or the demo script.

> You are the senior on a buy-side quality-of-earnings engagement. Management has provided an adjusted EBITDA schedule and a data room: general ledger, chart of accounts, monthly P&L, and supporting documents. Everything is synthetic.
>
> For each management adjustment, decide what diligence would carry and record it on the answer sheet: the treatment (ACCEPT / REVISE / REJECT / REQUEST_INFO), the amount for each analysis period, the key evidence (GL rows and documents, in the format shown), your open questions for management, and your confidence. Amounts are EBITDA-signed: positive increases EBITDA.
>
> If you have time, also record any data-quality issues you find (`DQ-n` rows), reported EBITDA recomputed from the GL (`EBITDA_GL`), and diligence-adjusted EBITDA (`EBITDA_DILIGENCE`).
>
> Work in whatever order you would on a real engagement. Nobody will answer management questions during the session; write them down. You have 180 minutes, and can continue to 240 to finish. Say out loud when you switch between adjustments, or between setting up and reviewing.

**Arm cards** (one paragraph each, handed out with the brief):

- **A.** Excel and a PDF viewer only. No AI features.
- **B.** You may also use the assistant in the open browser tab. Upload whatever you like, and paste this brief if you want to. Check anything it tells you against the source before relying on it. Its transcript is kept.
- **C.** You may also use QoE Evidence Review. Start the run, review each adjustment in the app, record your decision there, and export the workbook. You can open any source file to check the tool. Record your final answers on the answer sheet as well.
