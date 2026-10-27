// Runs forms/build-forms.gs against a local mock of FormApp, SpreadsheetApp and DriveApp, and checks
// that the forms it would build match spec/forms.json and forms/survey-form.md. This proves the script
// is internally consistent; it does not prove Google behaves the same (unverified, founder to confirm).
// node tests/test_forms_gs.js
const fs = require('fs'), vm = require('vm'), path = require('path');
const root = path.join(__dirname, '..');
const code = fs.readFileSync(path.join(root, 'forms', 'build-forms.gs'), 'utf8');
const spec = JSON.parse(fs.readFileSync(path.join(root, 'spec', 'forms.json'), 'utf8'));
let fails = [];
const ok = (c, m) => { if (!c) fails.push(m); };
let idn = 0; const forms = [];
function Item(kind) { this.kind = kind; this.choices = []; this.req = false; this.nav = {}; }
Item.prototype = {
  setTitle(t) { this.title = t; return this; }, setHelpText(t) { this.help = t; return this; }, setRequired(b) { this.req = b; return this; },
  setChoiceValues(v) { this.choices = v.slice(); return this; }, showOtherOption(b) { this.other = b; return this; },
  setBounds(a, b) { this.bounds = [a, b]; return this; }, setLabels(a, b) { this.labels = [a, b]; return this; },
  createChoice(v, page) { return { v, page }; }, setChoices(cs) { this.choices = cs.map(c => c.v); cs.forEach(c => this.nav[c.v] = c.page); return this; },
  setGoToPage(p) { this.goTo = p; return this; }, createResponse(v) { return { item: this, v }; }
};
function Form(title) { this.id = 'F' + (++idn); this.title = title; this.items = []; this.flags = {}; forms.push(this); }
Form.prototype = {
  getId() { return this.id; }, setDescription(d) { this.desc = d; return this; },
  setCollectEmail(b) { this.flags.collectEmail = b; }, setLimitOneResponsePerUser(b) { this.flags.limitOne = b; },
  setRequireLogin(b) { this.flags.requireLogin = b; return this; },
  setAllowResponseEdits(b) { this.flags.edit = b; }, setPublishingSummary(b) { this.flags.summary = b; },
  setShowLinkToRespondAgain(b) { this.flags.again = b; }, setProgressBar(b) { this.flags.progress = b; },
  setConfirmationMessage(m) { this.confirm = m; },
  add(kind) { const i = new Item(kind); this.items.push(i); return i; },
  addTextItem() { return this.add('short'); }, addParagraphTextItem() { return this.add('paragraph'); },
  addMultipleChoiceItem() { return this.add('mc'); }, addCheckboxItem() { return this.add('checkbox'); },
  addListItem() { return this.add('dropdown'); }, addScaleItem() { return this.add('scale'); }, addPageBreakItem() { return this.add('page'); },
  setDestination(t, ssid) { this.dest = ssid; ss.addSheet('Form Responses ' + (ss.sheets.length + 1), this); },
  getPublishedUrl() { return 'https://docs.google.com/forms/d/e/' + this.id + '/viewform'; },
  createResponse() { const f = this; const parts = []; return { withItemResponse(r) { parts.push(r); return this; },
    toPrefilledUrl() { return f.getPublishedUrl() + '?usp=pp_url&' + parts.map(p => 'entry.' + (1000 + f.items.indexOf(p.item)) + '=' + p.v).join('&'); } }; }
};
// a tiny spreadsheet: config and campaigns
function Sheet(name, rows) { this.name = name; this.rows = rows || [[]]; this.id = Math.floor(Math.random() * 1e9); }
Sheet.prototype = {
  getName() { return this.name; }, setName(n) { this.name = n; }, getSheetId() { return this.id; },
  getLastRow() { return this.rows.length; }, getLastColumn() { return Math.max(...this.rows.map(r => r.length)); },
  getRange(r, c, nr, nc) { const s = this; nr = nr || 1; nc = nc || 1;
    return { getValues() { const out = []; for (let i = 0; i < nr; i++) { const row = []; for (let j = 0; j < nc; j++) row.push((s.rows[r - 1 + i] || [])[c - 1 + j] ?? ''); out.push(row); } return out; },
             getValue() { return (s.rows[r - 1] || [])[c - 1] ?? ''; },
             setValue(v) { while (s.rows.length < r) s.rows.push([]); s.rows[r - 1][c - 1] = v; } }; }
};
const campHead = ['campaign_id', 'drop_id', 'brand_id', 'brand_name', 'product_sku', 'newsletter_option', 'landing_url', 'brand_privacy_url', 'survey_form_url', 'survey_prefill_template', 'newsletter_form_url'];
const ss = { sheets: [new Sheet('config', [['key', 'value'], ['survey_privacy_url', 'https://example.com/survey-privacy'], ['founder_email', '[EMAIL]']]),
                      new Sheet('campaigns', [campHead, ['SAMPLE-CMP-004', 'SAMPLE-DRP-002', 'SAMPLE-BR-004', 'SAMPLE Orchard Row', 'SAMPLE Dried Mango Strips, 1 oz', 'Y', 'https://example.com/orchardrow', 'https://example.com/orchardrow/privacy', '', '', '']])],
  getSheetByName(n) { return this.sheets.find(s => s.name === n) || null; }, getSheets() { return this.sheets.slice(); }, getId() { return 'SS1'; },
  addSheet(n, form) { const s = new Sheet(n); s.form = form; this.sheets.push(s); return s; } };
const ctx = { Logger: { log() {} }, FormApp: { create: t => new Form(t), DestinationType: { SPREADSHEET: 'SPREADSHEET' } },
  SpreadsheetApp: { getActiveSpreadsheet: () => ss, flush() {} }, DriveApp: { getFileById: id => ({ setName(n) { forms.find(f => f.id === id).fileName = n; } }) } };
vm.createContext(ctx); vm.runInContext(code, ctx);
ctx.buildMasters();
const byName = n => forms.find(f => f.fileName === n);
const master = byName('survey master'), nlm = byName('newsletter master');
ok(master && nlm && byName('Office intake (founder copy)') && byName('Brand qualification (founder copy)'), 'four masters made');
for (const f of forms) { ok(f.flags.collectEmail === false && f.flags.limitOne === false && f.flags.summary === false && f.flags.edit === false, f.fileName + ': settings');
  ok(f.flags.requireLogin === false, f.fileName + ': open to people outside the organization (setRequireLogin(false), review round 1 R1-01)'); ok(!/desk ?drop/i.test(f.fileName), 'no company name in file name ' + f.fileName); }
ok(!nlm.dest, 'newsletter master is not linked to a spreadsheet');
ok(byName('Office intake (founder copy)').dest === 'SS1', 'office intake linked to the tracker');
const off = byName('Office intake (founder copy)');
ok(off.items.map(i => i.title).join('|') === spec.forms.office_intake.items.map(i => i.title).join('|'), 'office intake questions in spec order');
ok(off.items.find(i => i.title === 'Which categories do you want?').choices.length === 15, 'categories plus Any of them');
const msg = ctx.makeCampaignSurvey('SAMPLE-CMP-004');
const sv = byName('SAMPLE-CMP-004 survey'), sn = byName('SAMPLE-CMP-004 newsletter sign-up');
ok(sv && sn, 'campaign survey and sign-up made');
ok(sv.flags.requireLogin === false && sn.flags.requireLogin === false, 'campaign survey and sign-up open to people outside the organization (R1-01)');
const qs = sv.items.filter(i => i.kind !== 'page').map(i => i.title);
const want = spec.forms.survey.response_columns.slice(1).map(h => h.replace('{BRAND}', 'SAMPLE Orchard Row'));
ok(JSON.stringify(qs) === JSON.stringify(want), 'survey questions are the response columns B to G: ' + JSON.stringify(qs));
const pages = sv.items.filter(i => i.kind === 'page');
const tried = sv.items.find(i => i.title === 'Did you try SAMPLE Orchard Row?');
ok(tried.req && tried.nav.Yes === pages[0] && tried.nav.No === pages[1], 'Yes goes to section 2, No to section 3');
ok(pages[1].goTo === pages[2], 'end of section 2 goes to section 4');
ok(sv.items.find(i => i.kind === 'scale').bounds.join() === '1,5', 'rating 1 to 5');
ok(sv.desc.startsWith('Anonymous. No name, no login, no email needed.') && sv.desc.includes('https://example.com/survey-privacy'), 'Part A notice with the privacy URL');
ok(sv.confirm.includes(sn.getPublishedUrl()) && sv.confirm.includes('utm_medium=survey'), 'confirmation links the sign-up form and the landing page');
ok(ss.getSheetByName('SAMPLE-CMP-004') && ss.getSheetByName('SAMPLE-CMP-004').form === sv, 'response tab renamed to the campaign id');
ok(!sn.dest, 'sign-up form never linked to a spreadsheet');
ok(sn.items[1].choices[0] === 'Share my email with SAMPLE Orchard Row under its privacy policy.' && !sn.items[1].req && !sn.items[0].req, 'consent box word for word, optional');
const row = ss.getSheetByName('campaigns').rows[1];
ok(/CARDCODE/.test(row[campHead.indexOf('survey_prefill_template')]) && (row[campHead.indexOf('survey_prefill_template')].match(/CARDCODE/g) || []).length === 1, 'prefill template with CARDCODE once');
ok(row[campHead.indexOf('newsletter_form_url')] === sn.getPublishedUrl(), 'newsletter_form_url written');
let threw = false; try { ctx.makeCampaignSurvey('SAMPLE-CMP-004'); } catch (e) { threw = true; } ok(threw, 'refuses a second survey for the same campaign');
console.log(fails.length ? 'FAIL test_forms_gs\n  ' + fails.join('\n  ') : 'PASS test_forms_gs (' + forms.length + ' forms built against the mock)');
process.exit(fails.length ? 1 : 0);
