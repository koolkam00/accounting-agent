SYNTHETIC DEAL PACKAGE - NOT REAL DATA
SYNTHETIC — generated for QoE Evidence Review testing

Target: Tidewell Distribution Group, LLC (fictional)
Industry: Specialty distribution - foodservice packaging and janitorial & sanitation supplies
Split: dev

Every company, person, amount, and document in this package is synthetic. It was
generated deterministically from data/specs/tidewell_distribution.yaml by
scripts/qoe_generate_deals.py for testing the QoE Evidence Review tool. Any
resemblance to real businesses or people is coincidental.

Contents
  deal.yaml                                     deal metadata (periods, file map)
  gl/general_ledger.csv                         general ledger export (netsuite_csv, 6027 rows, P&L accounts only)
  gl/chart_of_accounts.csv                      chart of accounts
  financials/monthly_pl.xlsx                    management's monthly P&L
  adjustments/management_adjusted_ebitda.xlsx   management's adjusted EBITDA schedule
  documents/                                    data-room documents (52 files)
  ground_truth.json                             answer key: evaluation only; the review pipeline must never read it

Scenario: Southeast US specialty distributor of foodservice packaging and janitorial &
sanitation supplies (Savannah GA distribution center; Jacksonville and Charleston branches).
LLC taxed as an S corporation with a Georgia pass-through entity tax election. NetSuite
saved-search GL export. Fiscal years end March 31. Analysis periods FY2025, FY2026 and
TTM Jun-26; the GL covers Apr 2024 - Jun 2026. Project Marlin is the sale process.

Regenerate:
  uv run python scripts/qoe_generate_deals.py --spec data/specs/tidewell_distribution.yaml --out data/dev
