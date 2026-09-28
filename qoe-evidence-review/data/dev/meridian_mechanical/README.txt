SYNTHETIC DEAL PACKAGE - NOT REAL DATA
SYNTHETIC — generated for QoE Evidence Review testing

Target: Meridian Mechanical Services, LLC (fictional)
Industry: Commercial and residential HVAC / plumbing services
Split: dev

Every company, person, amount, and document in this package is synthetic. It was
generated deterministically from data/specs/meridian_mechanical.yaml by
scripts/qoe_generate_deals.py for testing the QoE Evidence Review tool. Any
resemblance to real businesses or people is coincidental.

Contents
  deal.yaml                                     deal metadata (periods, file map)
  gl/general_ledger.csv                         general ledger export (qbo_gl_csv, 5618 rows, P&L accounts only)
  gl/chart_of_accounts.csv                      chart of accounts
  financials/monthly_pl.xlsx                    management's monthly P&L
  adjustments/management_adjusted_ebitda.xlsx   management's adjusted EBITDA schedule
  documents/                                    data-room documents (44 files)
  ground_truth.json                             answer key: evaluation only; the review pipeline must never read it

Scenario: Florida HVAC and plumbing contractor, FY Dec. QuickBooks Online exports.
Analysis periods FY2024, FY2025 and TTM Jun-26; the GL covers Jan 2024 - Jun 2026.

Regenerate:
  uv run python scripts/qoe_generate_deals.py --spec data/specs/meridian_mechanical.yaml --out data/dev
