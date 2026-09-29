# QoE Evidence Review

This tool verifies seller-proposed EBITDA adjustments against the general ledger and supporting documents. Its output is a workpaper that a transaction-advisory associate can review, defend, and hand to a manager.

The first job, and the only job in this version, is the add-back review in a quality-of-earnings (QoE) engagement. Management sends an adjusted EBITDA schedule. For each add-back the associate has to answer three questions:

1. Is the amount in the ledger?
2. Do the documents support management's explanation?
3. What amount should diligence carry, and what is still open?

This repo is separate from the AP three-way-match agent in the parent directory. Nothing here imports from it.

> **Everything in `data/` is synthetic.** Company names, people, vendors, invoices, and ledgers are fabricated and labeled SYNTHETIC. No client data was used.

## What it does

```
IMPORT → RECONCILE → TRACE → CHALLENGE → PROPOSE → REVIEW → EXPORT
```

| Step | What happens | Who decides |
| --- | --- | --- |
| Import | GL exports in QuickBooks Online (CSV), NetSuite (CSV) and Xero (XLSX) formats are detected automatically. Also loaded: chart of accounts, management's monthly P&L, management's adjusted EBITDA schedule, and the data room (PDF, email, text). | code |
| Reconcile | The GL is tied to the P&L by account-month. The step flags missing months, duplicate postings, and schedules that don't foot, and recomputes reported EBITDA from the GL. | code |
| Trace | Each add-back is linked to GL entries and documents. The step finds which entries management's number is made of (an exact-cents subset fit) and scans other periods for recurrence. | code, with AI proposing document facts |
| Challenge | Flags cover: contradicting documents, continuing obligations, recurring "one-time" costs, overlaps between adjustments, items already excluded from EBITDA, unadjusted recoveries, out-of-period and wrong-period items, draft support, pro forma items not yet realized, and sign errors. | code decides; AI proposes contradictions |
| Propose | The tool proposes a treatment (Accept / Revise / Reject / Request info) and amounts for each period. What the evidence shows is kept separate from what still needs judgment, and questions for management are drafted. | code |
| Review | The reviewer accepts, revises, rejects, or requests information, and records a rationale and a *correction type*: tool error or judgment difference. | **the reviewer** |
| Export | An Excel workpaper: EBITDA bridge, adjustment summary, one support schedule per adjustment with tie-outs and tickmarks, open questions, reconciliation, data quality, and the review log. Every total is a live formula. | code |

**The split between AI, code, and reviewer is the design.** AI reads documents and narrative and may propose facts, links, and question wording. Every quote it returns must appear verbatim on the cited page, or it is dropped. Code does all arithmetic and chooses the proposed treatment. The reviewer makes the call. Tool errors that reviewers correct become regression cases (`scripts/qoe_corrections_to_evals.py`).

The default AI mode (`rules`) is deterministic and runs offline. An OpenAI-compatible LLM mode (`--ai llm`, configured by `QOE_LLM_BASE_URL`, `QOE_LLM_API_KEY`, and `QOE_LLM_MODEL`) can stand in for it. Even there, rule-based findings are a floor: the LLM may add evidence but cannot remove it. The LLM path has been tested against fake clients only; it has not been run against a live model.

## Quick start

```bash
cd qoe-evidence-review
uv sync                    # Python 3.12
make test                  # full test suite
make run                   # review the Meridian dev deal; writes workpapers/meridian_mechanical/
make ui                    # reviewer app at http://127.0.0.1:8501
make eval                  # score the tool against the dev answer keys -> reports/eval_dev.md
```

Excel recalculation checks need LibreOffice Calc (`libreoffice-calc`). Without it the workbook is still written; the checks are skipped.

## Data: three synthetic deal packages

| Package | Split | Industry | GL export | Adjustments | Role |
| --- | --- | --- | --- | --- | --- |
| Meridian Mechanical Services (D1) | dev | HVAC / plumbing services | QuickBooks Online CSV | 14 management adjustments + 1 diligence item | Built alongside the engine |
| Tidewell Distribution Group (D2) | dev | Foodservice packaging distribution | NetSuite CSV, March fiscal year | 16 + 3 | Authored without access to the engine; used for tuning after a recorded first-contact baseline |
| Held-out deal (D3) | holdout | Outpatient physical therapy | Xero XLSX | 16 + 1 | Authored by a separate agent that never read the engine; scored once, after development was frozen |

Each package has an answer key, `ground_truth.json`, and **only the evaluator reads it**. Every key was checked by an AI review panel: three independent agents took the roles of a Deals senior manager, a buy-side investor, and an audit senior who recomputed the numbers, and an adjudicator ruled on their findings. See `docs/answer_key_review_D1.md` and the deal notes. **No human practitioner has reviewed these keys yet.** The benchmark protocol requires that before any results are cited.

These packages are built from YAML specs by a generator (`scripts/qoe_generate_deals.py`, format in `scripts/qoe_synth/SPEC_FORMAT.md`). A practitioner can therefore write a new, truly independent held-out package without touching Python.

## Results

{{RESULTS}}

## How to evaluate it properly

The automated scores above measure the tool's first-pass proposals on synthetic data. They say nothing about time saved. `docs/benchmark_protocol.md` sets out the study that would, and it has not been run yet. It compares three approaches on the same packages:

- normal manual work;
- a general-purpose AI assistant;
- this tool plus a reviewer.

It uses a Latin-square assignment, preparation and review timing, answer-sheet scoring, and pre-registered reading rules.

`docs/practitioner_interview_guide.md` is the workflow-discovery interview to run first.

`reports/commercial_model.xlsx` (generated by `make commercial`) translates a *measured* time reduction into capacity and economics. Its inputs are blank until measured. It keeps capacity (freed hours) apart from value, because freed hours are worth money only if they are redeployed, avoid a hire, or change fixed-fee margins.

## What this version does not do

- Working capital, revenue recognition, proof of cash, net debt, valuation, or report drafting.
- Diligence adjustments the seller did not propose, except mechanical ones: reversing duplicate postings, documented GL-export gaps, and supported top-sides.
- OCR. Scanned PDFs without a text layer produce no facts.
- Authentication. The app binds to localhost; put an authenticating proxy in front before sharing it.
- A live-LLM run, or any run on real client data.

## Map

```
qoe/            engine: ingest, reconcile, trace, challenge, propose, bridge, review store, export, UI, eval
scripts/        CLI: run, evaluate, generate deals, commercial model, corrections -> regression cases
data/           synthetic deal packages (dev/, holdout/) and their YAML specs
docs/           SPEC (the contract), benchmark protocol, interview guide, demo script, answer-key reviews
reports/        evaluation reports and the commercial model
tests/          unit and integration tests
```
