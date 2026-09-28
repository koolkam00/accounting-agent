SYNTHETIC DEAL PACKAGE - NOT REAL DATA
SYNTHETIC — generated for QoE Evidence Review testing

Target: Kinetic Ridge Physical Therapy Partners, LLC (fictional)
Industry: Multi-site outpatient physical therapy (central Indiana; 12 clinics, 11 after the Feb-2026 Brownsburg closure)
Split: holdout

Every company, person, amount, and document in this package is synthetic. It was
generated deterministically from data/specs/kinetic_ridge_pt.yaml by
scripts/qoe_generate_deals.py for testing the QoE Evidence Review tool. Any
resemblance to real businesses or people is coincidental.

Contents
  deal.yaml                                     deal metadata (periods, file map)
  gl/general_ledger.xlsx                        general ledger export (xero_xlsx, 3768 rows, P&L accounts only)
  gl/chart_of_accounts.csv                      chart of accounts
  financials/monthly_pl.xlsx                    management's monthly P&L
  adjustments/management_adjusted_ebitda.xlsx   management's adjusted EBITDA schedule
  documents/                                    data-room documents (48 files)
  ground_truth.json                             answer key: evaluation only; the review pipeline must never read it

Scenario: central Indiana outpatient physical therapy group, FY Dec. Xero exports (Account
Transactions, chart of accounts) plus management's Excel reporting pack.
Analysis periods FY2024, FY2025 and TTM May-26 (Jun 2025 - May 2026); the GL covers Jan 2024 - May 2026.
The company is an LLC taxed as a partnership: there is no entity-level income tax.

Regenerate:
  uv run python scripts/qoe_generate_deals.py --spec data/specs/kinetic_ridge_pt.yaml --out data/holdout
