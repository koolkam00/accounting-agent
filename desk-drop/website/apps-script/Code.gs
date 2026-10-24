/**
 * Website intake: one Google Apps Script web app for both website forms.
 * ---------------------------------------------------------------------
 * doPost writes ONE row to the "office_intake" or "brand_intake" tab of the spreadsheet
 * this script is attached to, with the columns of CONTRACTS.md section 6.3 in exact
 * order, then sends ONE short email notification for that row (company or brand, contact
 * email and the row link only: the Sheet is the one full copy of the answers).
 *
 * Setup (founder, needs your Google login): ../SETUP.md section 3. In short:
 *   1. Create a Google Sheet. Extensions > Apps Script. Paste this file over Code.gs.
 *   2. Run setup() once from the editor and approve the permissions.
 *   3. Deploy > New deployment > Web app. Execute as: Me. Who has access: Anyone.
 *   4. Copy the /exec URL into site/site.config.js as FORM_ENDPOINT.
 *
 * Contract (the same one tests/mock_endpoint.py implements):
 *   Request:  POST, body application/x-www-form-urlencoded. Field names are the sheet
 *             column names, plus "form" (office | brand), "submission_id" and the
 *             honeypot "hp_url". (Apps Script reserves the names "c" and "sid".)
 *   Response: JSON. {"ok":true} or {"ok":false,"error":"validation","fields":{"name":"required"}}
 *             Other errors: unknown_form, busy, sheet_header_mismatch, server.
 *   Honeypot: if hp_url is not empty, nothing is written or sent and {"ok":true} is returned.
 *   Repeats:  a submission_id seen in the last 6 hours returns {"ok":true,"duplicate":true}
 *             without a second row or email.
 *
 * Draft for attorney review. Not legal advice. (The form notices this serves are drafts.)
 */

var SETTINGS = {
  NOTIFY_TO: "",              // empty = the Google account that deployed the script
  TIMEZONE: "America/New_York",
  RATE_LIMIT_PER_10_MIN: 30,  // more than this many accepted submissions in 10 minutes = "busy"
  DUPLICATE_WINDOW_SECONDS: 21600,
  // Text starting with = + - @ gets a leading apostrophe, so Sheets never runs it as a formula.
  // The cells are also set to plain text first. If the SETUP.md section 3 step 6 check shows the
  // apostrophe inside the stored value, set this to false, redeploy and run the check again.
  APOSTROPHE_GUARD: true,
  // The form notices promise: "If we do not end up working together, we delete your answers,
  // and the email about them, within 12 months." markRowsToDelete() highlights rows older than
  // this and lists the Gmail search for each row's notification (SETUP.md section 3).
  RETENTION_DAYS: 365,
  RETENTION_HIGHLIGHT: "#F4CCCC"
};

// SCHEMA is strict JSON between the two markers. tests/ read it from this file, so edit it here only.
var SCHEMA = /*SCHEMA-JSON-START*/{
  "honeypot": "hp_url",
  "forms": {
    "office": {
      "sheet": "office_intake",
      "columns": ["submitted_at", "form_version", "company", "contact_name", "contact_title", "contact_email", "contact_phone", "office_address", "floor_suite", "tuesday_headcount", "pantry_owner_name", "pantry_owner_title", "pantry_owner_is_contact", "receiving_type", "receiving_window", "coi_required", "survey_channel", "categories_wanted", "vetoes", "notes", "source"],
      "fields": {
        "company": {"label": "Company", "required": true, "max": 200},
        "contact_name": {"label": "Contact name", "required": true, "max": 120},
        "contact_title": {"label": "Contact title", "max": 120},
        "contact_email": {"label": "Work email", "required": true, "type": "email", "max": 254},
        "contact_phone": {"label": "Work phone", "type": "phone", "max": 40},
        "office_address": {"label": "Office address", "required": true, "max": 200},
        "floor_suite": {"label": "Floor or suite", "max": 60},
        "tuesday_headcount": {"label": "People in on a Tuesday", "required": true, "type": "int", "min_value": 1, "max_value": 10000},
        "pantry_owner_is_contact": {"label": "Contact is the pantry owner", "required": true, "enum": ["Y", "N"]},
        "pantry_owner_name": {"label": "Pantry owner name", "required_if": {"pantry_owner_is_contact": "N"}, "max": 120},
        "pantry_owner_title": {"label": "Pantry owner title", "max": 120},
        "receiving_type": {"label": "Receiving", "required": true, "enum": ["walk-up", "front desk", "loading dock", "other"]},
        "receiving_window": {"label": "Receiving window", "required": true, "max": 120},
        "coi_required": {"label": "Certificate of insurance needed", "required": true, "enum": ["yes", "no", "unsure"]},
        "survey_channel": {"label": "Survey post channel", "required": true, "enum": ["slack", "email", "other"]},
        "categories_wanted": {"label": "Categories wanted", "required": true, "type": "list", "enum": ["chips-crisps", "popcorn-puffs", "crackers-pretzels", "bars", "cookies-baked", "chocolate-candy", "nuts-seeds-trail", "meat-snacks", "fruit-snacks", "sparkling-soda", "tea-juice", "coffee-rtd", "other-snack", "other-drink"]},
        "vetoes": {"label": "Never send", "multiline": true, "max": 1000},
        "notes": {"label": "Notes", "multiline": true, "max": 2000}
      },
      "derived": [
        {"target": "pantry_owner_name", "when": {"pantry_owner_is_contact": "Y"}, "template": "{contact_name}"},
        {"target": "pantry_owner_title", "when": {"pantry_owner_is_contact": "Y"}, "template": "{contact_title}"}
      ],
      "subject": "Office sign-up: {company} ({tuesday_headcount} on Tuesdays)"
    },
    "brand": {
      "sheet": "brand_intake",
      "columns": ["submitted_at", "form_version", "brand_name", "website", "contact_name", "contact_title", "contact_email", "contact_phone", "product_sku", "category", "hq_city", "nyc_retailers", "online_store_url", "can_issue_discount_code", "preferred_timing", "budget_approver_is_contact", "budget_approver_name_title", "q1_sealed_shelf_stable_60d", "q2_labeled_ingredients_allergens", "q3_buy_path_near_cluster", "q4_can_ship_275_in_10bd", "q5_product_liability_insurance", "q6_contact_can_approve_600", "q7_why_now", "excluded_category_confirmed", "notes", "source"],
      "fields": {
        "brand_name": {"label": "Brand", "required": true, "max": 120},
        "website": {"label": "Website", "required": true, "type": "url", "max": 300},
        "contact_name": {"label": "Contact name", "required": true, "max": 120},
        "contact_title": {"label": "Contact title", "required": true, "max": 120},
        "contact_email": {"label": "Work email", "required": true, "type": "email", "max": 254},
        "contact_phone": {"label": "Work phone", "type": "phone", "max": 40},
        "product_sku": {"label": "Product", "required": true, "max": 200},
        "category": {"label": "Category", "required": true, "enum": ["chips-crisps", "popcorn-puffs", "crackers-pretzels", "bars", "cookies-baked", "chocolate-candy", "nuts-seeds-trail", "meat-snacks", "fruit-snacks", "sparkling-soda", "tea-juice", "coffee-rtd", "other-snack", "other-drink"]},
        "hq_city": {"label": "Based in", "required": true, "max": 120},
        "nyc_retailers": {"label": "NYC stores", "multiline": true, "max": 1000},
        "online_store_url": {"label": "Online store", "type": "url", "max": 300},
        "can_issue_discount_code": {"label": "Can issue a discount code", "required": true, "enum": ["Y", "N"]},
        "preferred_timing": {"label": "Timing", "required": true, "enum": ["Next available drop", "In 1 to 3 months", "In 3 to 6 months", "Just exploring"]},
        "budget_approver_is_contact": {"label": "Contact approves the budget", "required": true, "enum": ["Y", "N"]},
        "budget_approver_name_title": {"label": "Budget approver", "required_if": {"budget_approver_is_contact": "N"}, "max": 200},
        "q1_sealed_shelf_stable_60d": {"label": "1. Sealed, shelf-stable, 60+ days", "required": true, "enum": ["Y", "N", "unsure"]},
        "q2_labeled_ingredients_allergens": {"label": "2. Ingredients and 9 allergens labeled", "required": true, "enum": ["Y", "N", "unsure"]},
        "q3_buy_path_near_cluster": {"label": "3. Buy path near the cluster", "required": true, "enum": ["Y", "N", "unsure"]},
        "q4_can_ship_275_in_10bd": {"label": "4. Can ship 275 (founding) or 550 (standard) in 10 business days", "required": true, "enum": ["Y", "N", "unsure"]},
        "q5_product_liability_insurance": {"label": "5. Product liability insurance", "required": true, "enum": ["Y", "N", "unsure"]},
        "q6_contact_can_approve_600": {"label": "6. Can approve $600 (founding) or $1,500 (standard) alone", "required": true, "enum": ["Y", "N", "unsure"]},
        "q7_why_now": {"label": "7. Why New York, why now", "required": true, "multiline": true, "max": 1000},
        "excluded_category_confirmed": {"label": "Not an excluded product", "required": true, "enum": ["Y"]},
        "notes": {"label": "Notes", "multiline": true, "max": 2000}
      },
      "derived": [
        {"target": "budget_approver_name_title", "when": {"budget_approver_is_contact": "Y"}, "template": "{contact_name}, {contact_title}"}
      ],
      "subject": "Brand application: {brand_name} ({category})"
    }
  }
}/*SCHEMA-JSON-END*/;

/* ------------------------------------------------------------------ entry points */

function doPost(e) {
  var params = {};
  var multi = {};
  if (e && e.parameter) params = e.parameter;
  if (e && e.parameters) multi = e.parameters;
  var result;
  try {
    result = handle_(params, multi);
  } catch (err) {
    console.error("intake error: " + (err && err.stack ? err.stack : err));
    result = { ok: false, error: "server" };
  }
  return ContentService.createTextOutput(JSON.stringify(result)).setMimeType(ContentService.MimeType.JSON);
}

/** A GET to the /exec URL answers with a short health check (no data). */
function doGet() {
  return ContentService.createTextOutput(JSON.stringify({ ok: true, service: "website-intake", forms: Object.keys(SCHEMA.forms) }))
    .setMimeType(ContentService.MimeType.JSON);
}

/** Run once from the editor: creates both tabs with their header rows and remembers this spreadsheet. */
function setup() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) throw new Error("Open this script from the Google Sheet (Extensions > Apps Script), then run setup again.");
  PropertiesService.getScriptProperties().setProperty("SPREADSHEET_ID", ss.getId());
  Object.keys(SCHEMA.forms).forEach(function (key) {
    var def = SCHEMA.forms[key];
    var sheet = ss.getSheetByName(def.sheet) || ss.insertSheet(def.sheet);
    ensureHeader_(sheet, def.columns, true);
    sheet.setFrozenRows(1);
  });
  return "Ready: tabs " + Object.keys(SCHEMA.forms).map(function (k) { return SCHEMA.forms[k].sheet; }).join(" and ") +
    ". Notifications go to " + notifyTo_() + ".";
}

/* ------------------------------------------------------------------ core */

function handle_(params, multi) {
  var formKey = str_(params.form);
  var def = SCHEMA.forms[formKey];
  if (!def) return { ok: false, error: "unknown_form" };

  // Honeypot: people never see this field. Answer as if all is well, store nothing.
  if (str_(params[SCHEMA.honeypot]).trim() !== "") return { ok: true };

  var checked = validate_(def, params, multi);
  if (!checked.ok) return { ok: false, error: "validation", fields: checked.errors };
  var row = checked.row;

  var version = str_(params.form_version).trim();
  row.form_version = new RegExp("^" + formKey + "-\\d{1,3}\\.\\d{1,3}$").test(version) ? version : formKey + "-unknown";
  row.source = "website";
  row.submitted_at = Utilities.formatDate(new Date(), SETTINGS.TIMEZONE, "yyyy-MM-dd'T'HH:mm:ssXXX");

  var subId = str_(params.submission_id).trim();
  if (!/^[A-Za-z0-9-]{8,64}$/.test(subId)) subId = "";

  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(20000);
  } catch (err) {
    return { ok: false, error: "busy" };
  }
  try {
    var cache = CacheService.getScriptCache();
    if (subId && cache.get("sub:" + subId)) return { ok: true, duplicate: true };

    var bucket = "rate:" + Math.floor(Date.now() / 600000);
    var count = Number(cache.get(bucket) || 0);
    if (count >= SETTINGS.RATE_LIMIT_PER_10_MIN) return { ok: false, error: "busy" };

    var ss = spreadsheet_();
    var sheet = ss.getSheetByName(def.sheet);
    if (!sheet) {
      sheet = ss.insertSheet(def.sheet);
      ensureHeader_(sheet, def.columns, true);
    }
    if (!ensureHeader_(sheet, def.columns, false)) return { ok: false, error: "sheet_header_mismatch" };

    var values = def.columns.map(function (col) { return cell_(row[col]); });
    var rowNumber = nextRow_(sheet);
    var range = sheet.getRange(rowNumber, 1, 1, values.length);
    // Plain-text format first, so Sheets never turns "3-4" into a date or a long number into 1E+12.
    range.setNumberFormats([def.columns.map(function (col) { return typeof row[col] === "number" ? "0" : "@"; })]);
    range.setValues([values]);
    SpreadsheetApp.flush();

    cache.put(bucket, String(count + 1), 900);
    if (subId) cache.put("sub:" + subId, "1", SETTINGS.DUPLICATE_WINDOW_SECONDS);
  } finally {
    lock.releaseLock();
  }

  notify_(def, row, ss, rowNumber);
  return { ok: true };
}

/** Validates and normalizes. Returns {ok, row, errors}. Same rules as tests/mock_endpoint.py. */
function validate_(def, params, multi) {
  var row = {};
  var errors = {};
  var names = Object.keys(def.fields);

  names.forEach(function (name) {
    var spec = def.fields[name];
    var raw;
    if (spec.type === "list") {
      var arr = multi && multi[name] && multi[name].length > 1 ? multi[name] : [str_(params[name])];
      raw = arr.join(";");
    } else {
      raw = str_(params[name]);
    }
    row[name] = clean_(raw, !!spec.multiline);
  });

  (def.derived || []).forEach(function (d) {
    if (matches_(row, d.when)) {
      row[d.target] = d.template.replace(/\{(\w+)\}/g, function (_, k) { return row[k] || ""; });
    }
  });

  names.forEach(function (name) {
    var spec = def.fields[name];
    var v = row[name];
    var needed = spec.required === true || (spec.required_if && matches_(row, spec.required_if));
    if (v === "") {
      if (needed) errors[name] = "required";
      return;
    }
    if (spec.type === "list") {
      var picked = v.split(";").map(function (s) { return s.trim(); }).filter(function (s) { return s !== ""; });
      var bad = picked.filter(function (s) { return spec.enum.indexOf(s) === -1; });
      if (bad.length) { errors[name] = "invalid"; return; }
      row[name] = spec.enum.filter(function (s) { return picked.indexOf(s) !== -1; }).join(";");
      if (row[name] === "" && needed) errors[name] = "required";
      return;
    }
    if (spec.enum && spec.enum.indexOf(v) === -1) { errors[name] = "invalid"; return; }
    if (spec.type === "int") {
      var digits = v.replace(/[,\s]/g, "");
      if (!/^\d{1,6}$/.test(digits)) { errors[name] = "invalid"; return; }
      var n = parseInt(digits, 10);
      if (n < spec.min_value || n > spec.max_value) { errors[name] = "invalid"; return; }
      row[name] = n;
      return;
    }
    if (spec.max && v.length > spec.max) { errors[name] = "too_long"; return; }
    if (spec.type === "email" && !/^[^\s@<>()",;:]+@[^\s@<>()",;:]+\.[A-Za-z]{2,}$/.test(v)) { errors[name] = "invalid"; return; }
    if (spec.type === "phone" && !/^[0-9+().\-\s/x#ext]{7,40}$/i.test(v)) { errors[name] = "invalid"; return; }
    if (spec.type === "url") {
      if (/\s/.test(v) || !/^(https?:\/\/)?[^\/\s.]+\.[^\s]{2,}$/i.test(v)) { errors[name] = "invalid"; return; }
      if (!/^https?:\/\//i.test(v)) row[name] = "https://" + v;
    }
  });

  return { ok: Object.keys(errors).length === 0, row: row, errors: errors };
}

/* ------------------------------------------------------------------ helpers */

function str_(v) {
  if (v === undefined || v === null) return "";
  return String(v);
}

/** Trims, removes control characters; single-line fields also collapse runs of whitespace. */
function clean_(v, multiline) {
  v = str_(v).replace(/\r\n?/g, "\n").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, "");
  if (multiline) {
    v = v.replace(/\t/g, " ").split("\n").map(function (l) { return l.replace(/\s+$/, ""); }).join("\n");
    return v.replace(/\n{3,}/g, "\n\n").trim();
  }
  return v.replace(/\s+/g, " ").trim();
}

function matches_(row, when) {
  return Object.keys(when).every(function (k) { return row[k] === when[k]; });
}

/** Text that starts with = + - @ is stored with a leading apostrophe so Sheets never runs it as a formula. */
function cell_(v) {
  if (v === undefined || v === null) return "";
  if (typeof v === "number") return v;
  return SETTINGS.APOSTROPHE_GUARD && /^[=+\-@]/.test(v) ? "'" + v : v;
}

/** The first row after the last one with a submitted_at (column A). Columns another workstream
 *  adds after the contract columns, even with formulas filled down, do not push rows lower. */
function nextRow_(sheet) {
  var last = sheet.getLastRow();
  if (last < 2) return 2;
  var colA = sheet.getRange(1, 1, last, 1).getValues();
  for (var i = colA.length - 1; i >= 1; i--) if (String(colA[i][0]).trim() !== "") return i + 2;
  return 2;
}

function ensureHeader_(sheet, columns, writeIfEmpty) {
  if (sheet.getLastRow() === 0) {
    if (!writeIfEmpty) return false;
    sheet.getRange(1, 1, 1, columns.length).setValues([columns]);
    return true;
  }
  var have = sheet.getRange(1, 1, 1, columns.length).getValues()[0].map(function (x) { return String(x); });
  for (var i = 0; i < columns.length; i++) if (have[i] !== columns[i]) return false;
  return true;
}

/* ------------------------------------------------------------------ retention */

/**
 * Run from the editor, or monthly by installRetentionReminder(). Highlights every row whose
 * submitted_at is more than SETTINGS.RETENTION_DAYS old, in both tabs, and emails one summary
 * with the Gmail search that finds each row's notification email.
 * It deletes nothing: check each highlighted company against the operations tracker, delete the
 * rows of companies that never signed (offices) or paid (brands) and their notification emails,
 * and clear the highlight on the rest (SETUP.md section 3, step 10).
 */
function markRowsToDelete(now) {
  var ss = spreadsheet_();
  var cutoff = (now instanceof Date ? now : new Date()).getTime() - SETTINGS.RETENTION_DAYS * 86400000;
  var lines = [];
  var total = 0;
  Object.keys(SCHEMA.forms).forEach(function (key) {
    var def = SCHEMA.forms[key];
    var sheet = ss.getSheetByName(def.sheet);
    if (!sheet || sheet.getLastRow() < 2) return;
    var col = def.columns.indexOf("submitted_at") + 1;
    var nameCol = def.columns.indexOf(nameKey_(def));
    var data = sheet.getRange(2, 1, sheet.getLastRow() - 1, def.columns.length).getValues();
    data.forEach(function (r, i) {
      var t = new Date(String(r[col - 1])).getTime();
      if (!isNaN(t) && t < cutoff) {
        sheet.getRange(i + 2, 1, 1, def.columns.length).setBackground(SETTINGS.RETENTION_HIGHLIGHT);
        var row = {};
        row[nameKey_(def)] = r[nameCol];
        lines.push(def.sheet + " row " + (i + 2) + ": " + String(r[nameCol]) + " (" + String(r[col - 1]).slice(0, 10) + ")" +
          "\n    notification email, Gmail search: " + gmailSearch_(def, row));
        total++;
      }
    });
  });
  var summary = total + " row(s) older than " + SETTINGS.RETENTION_DAYS + " days";
  if (total) {
    try {
      MailApp.sendEmail({ to: notifyTo_(), name: "Website intake", subject: "Intake rows to review for deletion: " + total,
        body: summary + ", highlighted in the Sheet. For each company that never signed (offices) or paid (brands): " +
          "delete its row, then paste its Gmail search into Gmail and delete the notification email it finds (and empty the Trash). " +
          "Clear the highlight on the rest. Delete this summary too when you are done.\n\n" +
          lines.join("\n") + "\n\n" + ss.getUrl() });
    } catch (err) {
      console.error("retention: summary email failed: " + err);
    }
  }
  return summary;
}

/** The column that names the sender's business: company (office) or brand_name (brand). */
function nameKey_(def) {
  return def.columns.indexOf("company") >= 0 ? "company" : "brand_name";
}

/** The Gmail search that finds one row's notification email, wherever it was filed. */
function gmailSearch_(def, row) {
  var prefix = def.subject.split("{")[0];
  return 'in:anywhere subject:"' + (prefix + str_(row[nameKey_(def)])).replace(/"/g, " ").trim() + '"';
}

/** Run once from the editor: runs markRowsToDelete() on the 1st of every month, around 9 am. */
function installRetentionReminder() {
  ScriptApp.getProjectTriggers().forEach(function (tr) {
    if (tr.getHandlerFunction() === "markRowsToDelete") ScriptApp.deleteTrigger(tr);
  });
  ScriptApp.newTrigger("markRowsToDelete").timeBased().onMonthDay(1).atHour(9).create();
  return "Monthly retention check installed (1st of each month, about 9 am).";
}

function spreadsheet_() {
  var id = PropertiesService.getScriptProperties().getProperty("SPREADSHEET_ID");
  if (id) return SpreadsheetApp.openById(id);
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) throw new Error("No spreadsheet. Run setup() from the editor first.");
  return ss;
}

function notifyTo_() {
  return SETTINGS.NOTIFY_TO || Session.getEffectiveUser().getEmail();
}

/** Exactly one email per accepted submission. A mail failure never loses the row.
 *  Review round 3 (R3-02): the email carries only the company or brand, the contact email and
 *  the row link, not the answers. The Sheet stays the one full copy, so the 12-month deletion
 *  promise and a deletion request cover one row plus this one short email. */
function notify_(def, row, ss, rowNumber) {
  try {
    if (MailApp.getRemainingDailyQuota() < 1) {
      console.error("intake: daily email quota used up; row " + rowNumber + " of " + def.sheet + " saved without an email");
      return;
    }
    var subject = def.subject.replace(/\{(\w+)\}/g, function (_, k) { return str_(row[k]); });
    var office = nameKey_(def) === "company";
    var body = [
      (office ? "New office sign-up" : "New brand application") + " from the website.",
      "",
      (office ? "Company: " : "Brand: ") + str_(row[nameKey_(def)]),
      "Contact email: " + str_(row.contact_email),
      "",
      "All the answers are in the Sheet, and only there: tab " + def.sheet + ", row " + rowNumber + ": " + ss.getUrl(),
      "",
      "Reply to this email to answer the sender directly.",
      "If you later delete this row (the 12-month promise, or the sender asks), delete this email too. Gmail search: " + gmailSearch_(def, row)
    ].join("\n");
    var msg = { to: notifyTo_(), subject: subject, body: body, name: "Website intake" };
    if (row.contact_email) msg.replyTo = row.contact_email;
    MailApp.sendEmail(msg);
  } catch (err) {
    console.error("intake: email failed for row " + rowNumber + " of " + def.sheet + ": " + err);
  }
}
