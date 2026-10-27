// Runs apps-script/Code.gs in Node with fake SpreadsheetApp, MailApp, LockService, CacheService,
// ContentService, PropertiesService, Session and Utilities, and checks the contract:
// one row per submission with the CONTRACTS 6.3 columns in exact order, one email per row,
// honeypot, validation, duplicates, header mismatch, derived fields, formula escaping.
// Usage: node tests/test_code_gs.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assertLib = require('assert');
// Values from the vm sandbox have their own Array/Object prototypes; compare plain JSON copies.
const plain = x => (x === undefined ? x : JSON.parse(JSON.stringify(x)));
const assert = Object.assign((...a) => assertLib(...a), assertLib, { deepStrictEqual: (a, b, m) => assertLib.deepStrictEqual(plain(a), plain(b), m) });

const ROOT = path.join(__dirname, '..');
const code = fs.readFileSync(path.join(ROOT, 'apps-script', 'Code.gs'), 'utf8');
const contracts = fs.readFileSync(path.join(ROOT, '..', 'CONTRACTS.md'), 'utf8');

// CONTRACTS 6.3 column lists, parsed from the markdown so this test fails if either side changes.
function contractColumns(sheet) {
  const line = contracts.split('\n').find(l => l.startsWith('**`' + sheet + '`**'));
  const body = line.slice(line.indexOf(':') + 1).replace(/\([^)]*\)/g, ''); // drop enum lists in parentheses
  return [...body.matchAll(/`([a-z0-9_]+)`/g)].map(m => m[1]);
}

function makeEnv() {
  const sheets = {};
  const mails = [];
  const cache = {};
  const props = {};
  const triggers = [];
  class Range {
    constructor(sheet, r, c, nr, nc) { Object.assign(this, { sheet, r, c, nr, nc }); }
    setValues(v) { for (let i = 0; i < this.nr; i++) { const row = this.sheet.rows[this.r - 1 + i] || (this.sheet.rows[this.r - 1 + i] = []); v[i].forEach((x, j) => { row[this.c - 1 + j] = x; }); } return this; }
    getValues() { const out = []; for (let i = 0; i < this.nr; i++) { const row = this.sheet.rows[this.r - 1 + i] || []; out.push(Array.from({ length: this.nc }, (_, j) => row[this.c - 1 + j] === undefined ? '' : row[this.c - 1 + j])); } return out; }
    setNumberFormats(f) { this.sheet.formats[this.r] = f[0]; return this; }
    setBackground(c) { for (let i = 0; i < this.nr; i++) this.sheet.backgrounds[this.r + i] = c; return this; }
  }
  class Sheet {
    constructor(name) { this.name = name; this.rows = []; this.formats = {}; this.backgrounds = {}; }
    getLastRow() { return this.rows.length; }
    getRange(r, c, nr, nc) { return new Range(this, r, c, nr || 1, nc || 1); }
    setFrozenRows() {}
  }
  const ss = {
    getId: () => 'SHEET-ID', getUrl: () => 'https://docs.google.com/spreadsheets/d/SHEET-ID',
    getSheetByName: n => sheets[n] || null,
    insertSheet: n => (sheets[n] = new Sheet(n)),
  };
  const env = {
    console: { error: () => {}, log: () => {} },
    SpreadsheetApp: { getActiveSpreadsheet: () => ss, openById: () => ss, flush: () => {} },
    MailApp: { sendEmail: m => mails.push(m), getRemainingDailyQuota: () => 100 },
    LockService: { getScriptLock: () => ({ waitLock: () => {}, releaseLock: () => {} }) },
    CacheService: { getScriptCache: () => ({ get: k => (k in cache ? cache[k] : null), put: (k, v) => { cache[k] = v; } }) },
    PropertiesService: { getScriptProperties: () => ({ getProperty: k => props[k] || null, setProperty: (k, v) => { props[k] = v; } }) },
    Session: { getEffectiveUser: () => ({ getEmail: () => 'owner@example.test' }) },
    ScriptApp: { getProjectTriggers: () => triggers.slice(), deleteTrigger: tr => triggers.splice(triggers.indexOf(tr), 1),
      newTrigger: fn => { const spec = { fn }; const b = { timeBased: () => b, onMonthDay: d => { spec.day = d; return b; }, atHour: h => { spec.hour = h; return b; }, create: () => { const tr = { ...spec, getHandlerFunction: () => fn }; triggers.push(tr); return tr; } }; return b; } },
    ContentService: { MimeType: { JSON: 'json' }, createTextOutput: s => ({ s, setMimeType() { return this; }, getContent() { return s; } }) },
    Utilities: { formatDate: (d, tz) => { const p = new Intl.DateTimeFormat('en-CA', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false, timeZoneName: 'longOffset' }).formatToParts(d); const g = t => p.find(x => x.type === t).value; const off = g('timeZoneName').replace('GMT', '') || '+00:00'; return `${g('year')}-${g('month')}-${g('day')}T${g('hour')}:${g('minute')}:${g('second')}${off}`; } },
  };
  vm.createContext(env);
  vm.runInContext(code, env);
  return { env, sheets, mails, cache, props, triggers };
}

const post = (env, params, multi) => JSON.parse(env.doPost({ parameter: params, parameters: multi || Object.fromEntries(Object.entries(params).map(([k, v]) => [k, [v]])) }).getContent());

const office = {
  form: 'office', form_version: 'office-1.0', submission_id: 'SAMPLE-0001-abcdef', hp_url: '',
  company: 'SAMPLE Co', contact_name: 'SAMPLE Person', contact_title: 'Office Manager', contact_email: 'sample@example.test',
  contact_phone: '+1 212 555 0100', office_address: '123 Fifth Avenue', floor_suite: '3-4', tuesday_headcount: '1,20',
  pantry_owner_is_contact: 'Y', pantry_owner_name: '', pantry_owner_title: '', receiving_type: 'front desk',
  receiving_window: '9 to 11 am', coi_required: 'unsure', survey_channel: 'slack',
  categories_wanted: 'bars;chips-crisps', vetoes: '=HYPERLINK("x")', notes: 'SAMPLE note\r\nline two',
};
const brand = {
  form: 'brand', form_version: 'brand-1.0', submission_id: 'SAMPLE-0002-abcdef', hp_url: '',
  brand_name: 'SAMPLE Brightside', website: 'example.com', contact_name: 'SAMPLE Founder', contact_title: 'Founder',
  contact_email: 'founder@example.test', contact_phone: '', product_sku: 'SAMPLE Crisps 1 oz', category: 'chips-crisps',
  hq_city: 'Queens, NY', nyc_retailers: 'SAMPLE Market, 1 Example St', online_store_url: '', can_issue_discount_code: 'Y',
  preferred_timing: 'In 1 to 3 months', budget_approver_is_contact: 'Y', budget_approver_name_title: '',
  q1_sealed_shelf_stable_60d: 'Y', q2_labeled_ingredients_allergens: 'Y', q3_buy_path_near_cluster: 'unsure',
  q4_can_ship_275_in_10bd: 'Y', q5_product_liability_insurance: 'N', q6_contact_can_approve_600: 'Y',
  q7_why_now: 'SAMPLE new store opening', excluded_category_confirmed: 'Y', notes: '',
};

let passed = 0;
function t(name, fn) { fn(); passed++; console.log('ok -', name); }

const schema = JSON.parse(code.match(/\/\*SCHEMA-JSON-START\*\/([\s\S]*?)\/\*SCHEMA-JSON-END\*\//)[1]);
t('schema columns equal CONTRACTS 6.3, in order (office_intake)', () => assert.deepStrictEqual(schema.forms.office.columns, contractColumns('office_intake')));
t('schema columns equal CONTRACTS 6.3, in order (brand_intake)', () => assert.deepStrictEqual(schema.forms.brand.columns, contractColumns('brand_intake')));

t('setup() creates both tabs with exact headers', () => {
  const { env, sheets } = makeEnv();
  env.setup();
  assert.deepStrictEqual(sheets.office_intake.rows[0], schema.forms.office.columns);
  assert.deepStrictEqual(sheets.brand_intake.rows[0], schema.forms.brand.columns);
});

t('office: one row, exact column order, one short email (no answers in it), derived pantry owner, escaping, text formats', () => {
  const { env, sheets, mails } = makeEnv();
  env.setup();
  const r = post(env, { ...office, tuesday_headcount: '120' });
  assert.deepStrictEqual(r, { ok: true });
  const sh = sheets.office_intake;
  assert.strictEqual(sh.rows.length, 2);
  const row = Object.fromEntries(schema.forms.office.columns.map((c, i) => [c, sh.rows[1][i]]));
  assert.strictEqual(sh.rows[1].length, 21);
  assert.match(row.submitted_at, /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d$/);
  assert.strictEqual(row.form_version, 'office-1.0');
  assert.strictEqual(row.source, 'website');
  assert.strictEqual(row.tuesday_headcount, 120);
  assert.strictEqual(row.pantry_owner_name, 'SAMPLE Person');
  assert.strictEqual(row.pantry_owner_title, 'Office Manager');
  assert.strictEqual(row.categories_wanted, 'chips-crisps;bars'); // stored in CONTRACTS order
  assert.strictEqual(row.contact_phone, "'+1 212 555 0100");
  assert.strictEqual(row.vetoes, "'=HYPERLINK(\"x\")");
  assert.strictEqual(row.floor_suite, '3-4');
  assert.strictEqual(row.notes, 'SAMPLE note\nline two');
  assert.strictEqual(sh.formats[2][schema.forms.office.columns.indexOf('tuesday_headcount')], '0');
  assert.strictEqual(sh.formats[2][schema.forms.office.columns.indexOf('floor_suite')], '@');
  assert.strictEqual(mails.length, 1);
  assert.strictEqual(mails[0].to, 'owner@example.test');
  assert.strictEqual(mails[0].replyTo, 'sample@example.test');
  assert.match(mails[0].subject, /^Office sign-up: SAMPLE Co \(120 on Tuesdays\)$/);
  // Review round 3 (R3-02): the email names the company and the contact email and links the row;
  // the answers stay in the Sheet only, so the deletion promise covers one full copy.
  const body = mails[0].body;
  assert.match(body, /Company: SAMPLE Co\n/);
  assert.match(body, /Contact email: sample@example\.test\n/);
  assert.match(body, /tab office_intake, row 2: https:\/\//);
  assert.match(body, /Gmail search: in:anywhere subject:"Office sign-up: SAMPLE Co"/);
  for (const answer of ['SAMPLE Person', 'Office Manager', '212 555 0100', '123 Fifth Avenue', '3-4', 'front desk', '9 to 11 am', 'HYPERLINK', 'SAMPLE note', 'chips-crisps', 'slack'])
    assert(!body.includes(answer), 'notification email carries an answer: ' + answer);
});

t('brand: one row, exact column order, one email, derived approver, url normalized', () => {
  const { env, sheets, mails } = makeEnv();
  env.setup();
  assert.deepStrictEqual(post(env, brand), { ok: true });
  const sh = sheets.brand_intake;
  const row = Object.fromEntries(schema.forms.brand.columns.map((c, i) => [c, sh.rows[1][i]]));
  assert.strictEqual(sh.rows[1].length, 27);
  assert.strictEqual(row.website, 'https://example.com');
  assert.strictEqual(row.budget_approver_name_title, 'SAMPLE Founder, Founder');
  assert.strictEqual(row.q5_product_liability_insurance, 'N');
  assert.strictEqual(row.excluded_category_confirmed, 'Y');
  assert.strictEqual(mails.length, 1);
  assert.strictEqual(mails[0].subject, 'Brand application: SAMPLE Brightside (chips-crisps)');
  assert.match(mails[0].body, /Brand: SAMPLE Brightside\nContact email: founder@example\.test\n/);
  for (const answer of ['SAMPLE Founder', 'SAMPLE Crisps', 'Queens', 'SAMPLE Market', 'In 1 to 3 months', 'new store opening'])
    assert(!mails[0].body.includes(answer), 'notification email carries an answer: ' + answer);
});

t('honeypot filled: ok to the bot, no row, no email', () => {
  const { env, sheets, mails } = makeEnv();
  env.setup();
  assert.deepStrictEqual(post(env, { ...office, hp_url: 'http://spam.example' }), { ok: true });
  assert.strictEqual(sheets.office_intake.rows.length, 1);
  assert.strictEqual(mails.length, 0);
});

t('server validation: bad enum, missing field, bad email, bad headcount, someone-else owner without name', () => {
  const { env, sheets, mails } = makeEnv();
  env.setup();
  const r = post(env, { ...office, receiving_type: 'drone', company: '', contact_email: 'nope', tuesday_headcount: '0', pantry_owner_is_contact: 'N' });
  assert.strictEqual(r.ok, false);
  assert.strictEqual(r.error, 'validation');
  // pantry_owner_title is optional since review round 2 (R2-10); the name is still required.
  assert.deepStrictEqual(r.fields, { company: 'required', contact_email: 'invalid', tuesday_headcount: 'invalid', pantry_owner_name: 'required', receiving_type: 'invalid' });
  const b = post(env, { ...brand, category: 'cbd-gummies', excluded_category_confirmed: '', q1_sealed_shelf_stable_60d: 'maybe' });
  assert.deepStrictEqual(b.fields, { category: 'invalid', q1_sealed_shelf_stable_60d: 'invalid', excluded_category_confirmed: 'required' });
  assert.strictEqual(sheets.office_intake.rows.length + sheets.brand_intake.rows.length, 2);
  assert.strictEqual(mails.length, 0);
});

t('repeat submission_id: one row, one email, second answer says duplicate', () => {
  const { env, sheets, mails } = makeEnv();
  env.setup();
  post(env, office);
  assert.deepStrictEqual(post(env, office), { ok: true, duplicate: true });
  assert.strictEqual(sheets.office_intake.rows.length, 2);
  assert.strictEqual(mails.length, 1);
});

t('categories sent as repeated fields are accepted the same way', () => {
  const { env, sheets } = makeEnv();
  env.setup();
  const p = { ...office, submission_id: 'SAMPLE-0003-abcdef' };
  const multi = Object.fromEntries(Object.entries(p).map(([k, v]) => [k, [v]]));
  multi.categories_wanted = ['tea-juice', 'bars'];
  assert.deepStrictEqual(JSON.parse(env.doPost({ parameter: { ...p, categories_wanted: 'tea-juice' }, parameters: multi }).getContent()), { ok: true });
  assert.strictEqual(sheets.office_intake.rows[1][schema.forms.office.columns.indexOf('categories_wanted')], 'bars;tea-juice');
});

t('header mismatch: refuses to write, no email', () => {
  const { env, sheets, mails } = makeEnv();
  env.setup();
  sheets.office_intake.rows[0][3] = 'name';
  assert.deepStrictEqual(post(env, office), { ok: false, error: 'sheet_header_mismatch' });
  assert.strictEqual(sheets.office_intake.rows.length, 1);
  assert.strictEqual(mails.length, 0);
});

t('unknown form and bad form_version', () => {
  const { env, sheets } = makeEnv();
  env.setup();
  assert.deepStrictEqual(post(env, { form: 'c' }), { ok: false, error: 'unknown_form' });
  post(env, { ...office, form_version: 'drop table' });
  assert.strictEqual(sheets.office_intake.rows[1][1], 'office-unknown');
});

t('mail failure keeps the row', () => {
  const { env, sheets } = makeEnv();
  env.setup();
  env.MailApp.sendEmail = () => { throw new Error('quota'); };
  assert.deepStrictEqual(post(env, office), { ok: true });
  assert.strictEqual(sheets.office_intake.rows.length, 2);
});

t('someone-else pantry owner: name required, title optional (blank is accepted)', () => {
  const { env, sheets, mails } = makeEnv();
  env.setup();
  assert.deepStrictEqual(post(env, { ...office, submission_id: 'SAMPLE-0010-abcdef', pantry_owner_is_contact: 'N', pantry_owner_name: 'SAMPLE Ana Ruiz', pantry_owner_title: '' }), { ok: true });
  const cols = schema.forms.office.columns;
  assert.strictEqual(sheets.office_intake.rows[1][cols.indexOf('pantry_owner_name')], 'SAMPLE Ana Ruiz');
  assert.strictEqual(sheets.office_intake.rows[1][cols.indexOf('pantry_owner_title')], '');
  assert.strictEqual(mails.length, 1);
});

t('extra columns after the contract ones, with a formula filled down, do not push new rows lower', () => {
  const { env, sheets } = makeEnv();
  env.setup();
  const sh = sheets.office_intake;
  sh.rows[0].push('f_owner_status');
  for (let r = 1; r <= 10; r++) { sh.rows[r] = Array(21).fill(''); sh.rows[r].push('=IF(A' + (r + 1) + '="","",1)'); }
  assert.deepStrictEqual(post(env, office), { ok: true });
  assert.strictEqual(sh.rows[1][0] !== '', true, 'the new row is row 2, right under the header');
  assert.strictEqual(sh.rows[1][21], '=IF(A2="","",1)', 'the added column is left alone');
  assert.deepStrictEqual(post(env, { ...office, submission_id: 'SAMPLE-0011-abcdef' }), { ok: true });
  assert.strictEqual(sh.rows[2][0] !== '', true, 'the next row is row 3');
  assert.strictEqual(sh.rows.length, 11, 'nothing appended below the formula rows');
});

t('APOSTROPHE_GUARD false: text is written as typed (cells stay plain text)', () => {
  const { env, sheets } = makeEnv();
  env.setup();
  vm.runInContext('SETTINGS.APOSTROPHE_GUARD = false;', env);
  post(env, office);
  const cols = schema.forms.office.columns;
  assert.strictEqual(sheets.office_intake.rows[1][cols.indexOf('contact_phone')], '+1 212 555 0100');
  assert.strictEqual(sheets.office_intake.formats[2][cols.indexOf('contact_phone')], '@');
});

t('markRowsToDelete: highlights rows older than 365 days in both tabs, deletes nothing, one summary email with each row\'s Gmail search', () => {
  const { env, sheets, mails, triggers } = makeEnv();
  env.setup();
  post(env, office);
  post(env, brand);
  const oc = schema.forms.office.columns, bc = schema.forms.brand.columns;
  sheets.office_intake.rows[1][oc.indexOf('submitted_at')] = '2025-09-01T10:00:00-04:00';
  const now = new Date('2026-10-24T12:00:00-04:00');
  mails.length = 0;
  const summary = env.markRowsToDelete(now);
  assert.strictEqual(summary, '1 row(s) older than 365 days');
  assert.strictEqual(sheets.office_intake.backgrounds[2], '#F4CCCC');
  assert.strictEqual(sheets.brand_intake.backgrounds[2], undefined, 'a recent row is not highlighted');
  assert.strictEqual(sheets.office_intake.rows.length, 2, 'nothing deleted');
  assert.strictEqual(mails.length, 1);
  assert.match(mails[0].body, /office_intake row 2: SAMPLE Co \(2025-09-01\)\n    notification email, Gmail search: in:anywhere subject:"Office sign-up: SAMPLE Co"/);
  assert.match(mails[0].body, /delete the notification email/);
  mails.length = 0;
  sheets.office_intake.rows[1][oc.indexOf('submitted_at')] = '2026-10-01T10:00:00-04:00';
  assert.strictEqual(env.markRowsToDelete(now), '0 row(s) older than 365 days');
  assert.strictEqual(mails.length, 0, 'no email when nothing is due');
  env.installRetentionReminder();
  env.installRetentionReminder();
  assert.strictEqual(triggers.length, 1, 'installing twice leaves one monthly trigger');
  assert.strictEqual(triggers[0].day, 1);
  assert.strictEqual(bc.length, 27);
});

t('doGet health check', () => {
  const { env } = makeEnv();
  assert.deepStrictEqual(JSON.parse(env.doGet().getContent()), { ok: true, service: 'website-intake', forms: ['office', 'brand'] });
});

console.log(`\n${passed} passed`);
