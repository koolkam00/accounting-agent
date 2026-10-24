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
  class Range {
    constructor(sheet, r, c, nr, nc) { Object.assign(this, { sheet, r, c, nr, nc }); }
    setValues(v) { for (let i = 0; i < this.nr; i++) { this.sheet.rows[this.r - 1 + i] = v[i].slice(); } return this; }
    getValues() { const out = []; for (let i = 0; i < this.nr; i++) { const row = this.sheet.rows[this.r - 1 + i] || []; out.push(Array.from({ length: this.nc }, (_, j) => row[this.c - 1 + j] === undefined ? '' : row[this.c - 1 + j])); } return out; }
    setNumberFormats(f) { this.sheet.formats[this.r] = f[0]; return this; }
  }
  class Sheet {
    constructor(name) { this.name = name; this.rows = []; this.formats = {}; }
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
    ContentService: { MimeType: { JSON: 'json' }, createTextOutput: s => ({ s, setMimeType() { return this; }, getContent() { return s; } }) },
    Utilities: { formatDate: (d, tz) => { const p = new Intl.DateTimeFormat('en-CA', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false, timeZoneName: 'longOffset' }).formatToParts(d); const g = t => p.find(x => x.type === t).value; const off = g('timeZoneName').replace('GMT', '') || '+00:00'; return `${g('year')}-${g('month')}-${g('day')}T${g('hour')}:${g('minute')}:${g('second')}${off}`; } },
  };
  vm.createContext(env);
  vm.runInContext(code, env);
  return { env, sheets, mails, cache, props };
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

t('office: one row, exact column order, one email, derived pantry owner, escaping, text formats', () => {
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
  assert.deepStrictEqual(r.fields, { company: 'required', contact_email: 'invalid', tuesday_headcount: 'invalid', pantry_owner_name: 'required', pantry_owner_title: 'required', receiving_type: 'invalid' });
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

t('doGet health check', () => {
  const { env } = makeEnv();
  assert.deepStrictEqual(JSON.parse(env.doGet().getContent()), { ok: true, service: 'website-intake', forms: ['office', 'brand'] });
});

console.log(`\n${passed} passed`);
