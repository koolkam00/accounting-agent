/*
  SITE SETTINGS: the one file to edit for name, contact details, forms and analytics.
  ---------------------------------------------------------------------------------
  - Change a value between the quotes and save. For staging, upload the site/ folder again.
    For production, run tools/make_production.py, which writes the upload folder publish/
    (SETUP.md section 10).
  - The working name lives ONLY here (BRAND_NAME). Every page reads it from here, so a
    rename is this one edit. "Desk Drop" is a working name, not cleared (see
    desk-drop-legal-pack/name-check-log.md).
  - Placeholders in [BRACKETS] show highlighted in yellow on the page until you fill them.
  - Page copy (headings, paragraphs) is in the .html files. See ../SETUP.md, section 5.
*/
window.SITE_CONFIG = {
  // Name and tagline. Rename = change BRAND_NAME. Nothing else.
  BRAND_NAME: "Desk Drop",
  TAGLINE: "Emerging brands. Delivered to your workday.",

  // Contact details shown in the footer, under the forms and in "Who runs this".
  DOMAIN: "[DOMAIN]",            // for example "example.com", no https://
  CONTACT_EMAIL: "[EMAIL]",
  PHONE: "[PHONE]",              // a business line; "" hides every phone line on the site
  POSTAL_ADDRESS: "[POSTAL ADDRESS]",
  FOUNDER_NAME: "[FOUNDER NAME]",
  FOUNDER_LINKEDIN: "[LINKEDIN URL]", // full https:// link to your profile; "" hides the link
  COMPANY_LEGAL_NAME: "[COMPANY NAME]", // the name on the filed Articles, used on both privacy pages

  // true = staging: a "noindex" robots tag and a staging bar on every page.
  // Leave this true. The publish step (SETUP.md section 10, tools/make_production.py) writes a
  // separate production copy with STAGING false; you never edit it here.
  STAGING: true,

  // The Google Apps Script web app URL (ends in /exec). Empty = forms say
  // "staging: submissions are not live yet" and send nothing.
  FORM_ENDPOINT: "",

  // Form versions written to the sheet (column form_version). Raise when you change a form.
  // brand_standard_only is sent once FOUNDING_TIER_OPEN is false: question 6 then asks about
  // $1,500 instead of $600 (same column, q6_contact_can_approve_600; see HANDOFF.md).
  FORM_VERSION: { office: "office-1.0", brand: "brand-1.0", brand_standard_only: "brand-2.0" },

  // The founding tier ($600 for 5 offices, first three brands only).
  // Set to false once three brands have taken it: the founding price disappears everywhere.
  FOUNDING_TIER_OPEN: true,

  // One honest line about where things stand. Shown on the home and brand pages.
  // Change it the day it stops being true, and put that day in ROSTER_STATUS_DATE
  // (tools/preflight.py refuses to publish if the date is more than 14 days old).
  ROSTER_STATUS: "No offices are signed yet and no campaign has run, so there are no results to show.",
  ROSTER_STATUS_DATE: "2026-10-24",

  // Analytics: GoatCounter (free, no cookies). Empty ENDPOINT = no analytics at all.
  // Example: "https://YOURCODE.goatcounter.com/count"
  ANALYTICS: {
    PROVIDER: "goatcounter",
    ENDPOINT: "",
    RESPECT_DO_NOT_TRACK: true   // skip counting for visitors with Do Not Track or Global Privacy Control on
  }
};
