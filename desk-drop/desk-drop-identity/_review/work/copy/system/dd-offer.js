/*
  dd-offer.js: THE ONE PLACE THE PRICES AND CAMPAIGN NUMBERS LIVE (v1.1, 2026-10-24).
  Source: plan.md "The revised model" (What brands buy, Price) and the brand campaign agreement
  (desk-drop-legal-pack/10-brand-campaign-agreement.md, sections 3 and 8).
  The proposal and the brand one-pager read these. Change a number here, then rebuild the PDFs
  (bash render/build-pdfs.sh) and change the same number in the agreement.
  All prices are hypotheses to test (plan.md), not validated numbers.
*/
window.DD_OFFER = {
  founding: { price: 600, offices: 5, per_office: 120, brands_offered: 3, locked_campaigns: 2 },
  standard: { price: 1500, offices: 10, per_office: 150, deposit_pct: 50 },
  extra_office: 150,
  units_per_office: 50, units_min: 30, units_max: 80, reserve_pct: 10,
  cancel_fee_before_ship_by: 100, cancel_kept_pct_after_ship_by: 50
};
