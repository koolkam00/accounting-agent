/*
  SITE SETTINGS: the one file to edit for name, contact details, forms and analytics.
  ---------------------------------------------------------------------------------
  - Change a value between the quotes, save, upload the site folder again. No build step.
  - The working name lives ONLY here (BRAND_NAME). Every page reads it from here, so a
    rename is this one edit. "Desk Drop" is a working name, not cleared (see
    desk-drop-legal-pack/name-check-log.md): keep STAGING = true until the founder decides.
  - Placeholders in [BRACKETS] show highlighted in yellow on the page until you fill them.
  - Page copy (headings, paragraphs) is in the .html files. See ../SETUP.md, section 5.
*/
window.SITE_CONFIG = {
  // Name and tagline. Rename = change BRAND_NAME. Nothing else.
  BRAND_NAME: "Desk Drop",
  TAGLINE: "Emerging brands. Delivered to your workday.",

  // Contact details shown in the footer and under the forms.
  DOMAIN: "[DOMAIN]",            // for example "example.com", no https://
  CONTACT_EMAIL: "[EMAIL]",
  POSTAL_ADDRESS: "[POSTAL ADDRESS]",
  FOUNDER_NAME: "[FOUNDER NAME]",
  COMPANY_LEGAL_NAME: "[COMPANY NAME]", // the name on the filed Articles, used on the privacy pages

  // true = staging: every page gets a "noindex" robots tag and a staging bar.
  // Publish step (SETUP.md section 10): set false AND swap robots.txt and _headers.
  STAGING: true,

  // The Google Apps Script web app URL (ends in /exec). Empty = forms say
  // "staging: submissions are not live yet" and send nothing.
  FORM_ENDPOINT: "",

  // Form versions written to the sheet (column form_version). Raise when you change a form.
  FORM_VERSION: { office: "office-1.0", brand: "brand-1.0" },

  // The founding tier ($600 for 5 offices, first three brands only).
  // Set to false once three brands have taken it: the founding price disappears everywhere.
  FOUNDING_TIER_OPEN: true,

  // One honest line about where things stand. Shown on the home page.
  ROSTER_STATUS: "We are signing our founding offices now. No campaign has run yet, so there are no results to show.",

  // Analytics: GoatCounter (free, no cookies). Empty ENDPOINT = no analytics at all.
  // Example: "https://YOURCODE.goatcounter.com/count"
  ANALYTICS: {
    PROVIDER: "goatcounter",
    ENDPOINT: "",
    RESPECT_DO_NOT_TRACK: true   // skip counting for visitors with Do Not Track or Global Privacy Control on
  }
};
