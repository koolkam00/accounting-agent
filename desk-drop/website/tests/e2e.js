// End-to-end: serves site/ locally, starts tests/mock_endpoint.py on another origin, and drives
// both forms with Playwright at 390 x 844 (touch) and 1280 x 800. Checks rows, columns, one
// notification each, the analytics stub, staging behavior, validation, rename and founding tier.
// Usage (from website/): node tests/e2e.js      Writes tests/out/e2e-results.json and _shots/states/.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const assert = require('assert');

const ROOT = path.join(__dirname, '..');
const SITE_PORT = 8123, MOCK_PORT = 8787;
const SITE = `http://127.0.0.1:${SITE_PORT}/`;
const MOCK = `http://127.0.0.1:${MOCK_PORT}`;
const OUT = path.join(__dirname, 'out', 'tmp', 'mock-' + Date.now());
const SHOTS = path.join(ROOT, '_shots', 'states');
fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(SHOTS, { recursive: true });
const schema = JSON.parse(fs.readFileSync(path.join(ROOT, 'apps-script', 'Code.gs'), 'utf8').match(/\/\*SCHEMA-JSON-START\*\/([\s\S]*?)\/\*SCHEMA-JSON-END\*\//)[1]);
const realConfig = fs.readFileSync(path.join(ROOT, 'site', 'site.config.js'), 'utf8');

function config(over) {
  let c = realConfig;
  for (const [re, val] of over) { assert(re.test(c), 'config pattern not found: ' + re); c = c.replace(re, val); }
  return c;
}
const LIVE = [[/FORM_ENDPOINT: ""/, `FORM_ENDPOINT: "${MOCK}/exec"`], [/ENDPOINT: "",/, `ENDPOINT: "${MOCK}/count",`]];

function readCsv(file) {
  if (!fs.existsSync(file)) return [];
  // Minimal CSV parser (quotes, commas, newlines in quotes).
  const s = fs.readFileSync(file, 'utf8'); const rows = []; let row = [], cell = '', q = false;
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (q) { if (ch === '"') { if (s[i + 1] === '"') { cell += '"'; i++; } else q = false; } else cell += ch; }
    else if (ch === '"') q = true; else if (ch === ',') { row.push(cell); cell = ''; }
    else if (ch === '\n') { row.push(cell); rows.push(row); row = []; cell = ''; } else if (ch !== '\r') cell += ch;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  return rows;
}
const lines = f => (fs.existsSync(f) ? fs.readFileSync(f, 'utf8').trim().split('\n').filter(Boolean) : []);
const wait = ms => new Promise(r => setTimeout(r, ms));

const results = { date: new Date().toISOString(), checks: [], timing: {} };
function ok(name, extra) { results.checks.push({ name, pass: true, ...(extra || {}) }); console.log('ok -', name); }

// Realistic SAMPLE answers (CONTRACTS: sample text starts with SAMPLE).
const OFFICE = { company: 'SAMPLE Studio', contact_name: 'SAMPLE Jo Park', contact_title: 'Office Manager', contact_email: 'sample.jo@example.com', office_address: '123 Fifth Avenue', tuesday_headcount: '60' };
const BRAND = { brand_name: 'SAMPLE Brightside', website: 'example.com', product_sku: 'SAMPLE Sea Salt Lentil Crisps, 1 oz', hq_city: 'Queens, NY', contact_name: 'SAMPLE Sam Lee', contact_title: 'Founder', contact_email: 'sample.sam@example.com', q7_why_now: 'SAMPLE New store opening on 14th Street' };

async function main() {
  const site = spawn('python3', ['-m', 'http.server', String(SITE_PORT), '--bind', '127.0.0.1', '--directory', path.join(ROOT, 'site')], { stdio: 'ignore' });
  const mock = spawn('python3', [path.join(__dirname, 'mock_endpoint.py'), '--port', String(MOCK_PORT), '--out', OUT], { stdio: 'ignore' });
  await wait(1200);
  const browser = await chromium.launch();
  try {
    for (const [label, vp, mobile] of [['phone', { width: 390, height: 844 }, true], ['desktop', { width: 1280, height: 800 }, false]]) {
      const ctx = await browser.newContext({ viewport: vp, isMobile: mobile, hasTouch: mobile, deviceScaleFactor: mobile ? 2 : 1 });
      await ctx.route('**/site.config.js', r => r.fulfill({ contentType: 'application/javascript', body: config(LIVE) }));
      const page = await ctx.newPage();
      const errors = []; page.on('pageerror', e => errors.push(String(e)));
      let taps = 0, chars = 0;
      // Wait until smooth scrolling has stopped, so a tap lands where a person would tap.
      const settle = () => page.evaluate(() => new Promise(res => { let last = -1, same = 0; (function f() { if (scrollY === last && ++same > 4) return res(); if (scrollY !== last) same = 0; last = scrollY; requestAnimationFrame(f); })(); }));
      const press = async sel => { await settle(); if (mobile) await page.tap(sel); else await page.click(sel); taps++; };
      const type = async (sel, text) => {
        await press(sel);
        assert(await page.evaluate(s => document.activeElement === document.querySelector(s), sel), 'tap did not focus ' + sel);
        await page.keyboard.type(text); chars += text.length;
      };

      // ---------- office form ----------
      await page.goto(SITE + 'offices.html?utm_source=SAMPLE-email', { waitUntil: 'networkidle' });
      await press('.hero-actions a[href="#join"]');
      const f = '#office-form ';
      for (const [k, v] of Object.entries(OFFICE)) await type(`${f}[name="${k}"]`, v);
      await press(`${f}input[name="pantry_owner_is_contact"][value="Y"]`);
      await press(`${f}input[name="receiving_type"][value="front desk"]`);
      await press(`${f}input[name="ui_receiving_window"][value="9 to 11 am"]`);
      await press(`${f}input[name="coi_required"][value="unsure"]`);
      await press(`${f}input[name="survey_channel"][value="slack"]`);
      results.timing[label] = { required_text_fields: Object.keys(OFFICE).length, typed_chars: chars, taps_before_submit: taps + 1 };
      const csvO = path.join(OUT, 'office_intake.csv'), notes = path.join(OUT, 'notifications.log'), an = path.join(OUT, 'analytics.log');
      const before = { rows: readCsv(csvO).length, notes: lines(notes).length };
      await press(`${f}button[type="submit"]`);
      await page.waitForSelector('#join .form-done:not([hidden])', { timeout: 10000 });
      assert.strictEqual(await page.evaluate(() => document.activeElement.classList.contains('form-done')), true, 'focus moves to the thank-you panel');
      await page.screenshot({ path: path.join(SHOTS, `office-sent-${label}.png`) });
      await wait(300);
      const rowsO = readCsv(csvO);
      assert.deepStrictEqual(rowsO[0], schema.forms.office.columns, 'office header = CONTRACTS 6.3 order');
      assert.strictEqual(rowsO.length, before.rows + (before.rows ? 1 : 2), 'exactly one new office row');
      const o = Object.fromEntries(rowsO[0].map((c, i) => [c, rowsO[rowsO.length - 1][i]]));
      assert.strictEqual(o.company, OFFICE.company); assert.strictEqual(o.tuesday_headcount, '60');
      assert.strictEqual(o.pantry_owner_name, OFFICE.contact_name); assert.strictEqual(o.receiving_type, 'front desk');
      assert.strictEqual(o.receiving_window, '9 to 11 am'); assert.strictEqual(o.source, 'website'); assert.strictEqual(o.form_version, 'office-1.0');
      assert.strictEqual(o.categories_wanted.split(';').length, 14, '"Any of them" writes all 14 category keys');
      assert.strictEqual(lines(notes).length, before.notes + 1, 'exactly one notification for the office row');
      ok(`office form submitted at ${label} width: one row, exact columns, one notification`, { row: o });

      // ---------- brand form ----------
      await page.goto(SITE + 'brands.html', { waitUntil: 'networkidle' });
      await press('.hero-actions a[href="#apply"]');
      const g = '#brand-form ';
      for (const [k, v] of Object.entries(BRAND)) await type(`${g}[name="${k}"]`, v);
      await page.selectOption(`${g}select[name="category"]`, 'chips-crisps');
      for (const [n, v] of [['budget_approver_is_contact', 'N'], ['can_issue_discount_code', 'Y'], ['preferred_timing', 'In 1 to 3 months'],
        ['q1_sealed_shelf_stable_60d', 'Y'], ['q2_labeled_ingredients_allergens', 'Y'], ['q3_buy_path_near_cluster', 'unsure'],
        ['q4_can_ship_275_in_10bd', 'Y'], ['q5_product_liability_insurance', 'N'], ['q6_contact_can_approve_600', 'Y']]) {
        await press(`${g}input[name="${n}"][value="${v}"]`);
      }
      await type(`${g}[name="budget_approver_name_title"]`, 'SAMPLE Alex Kim, CEO');
      await press(`${g}input[name="excluded_category_confirmed"]`);
      const csvB = path.join(OUT, 'brand_intake.csv');
      const beforeB = { rows: readCsv(csvB).length, notes: lines(notes).length };
      await press(`${g}button[type="submit"]`);
      try { await page.waitForSelector('#apply .form-done:not([hidden])', { timeout: 10000 }); }
      catch (e) { const dbg = await page.evaluate(() => [document.querySelector('#brand-form .error-summary').innerText, [...document.querySelectorAll('#brand-form input[type=text],#brand-form input[type=url],#brand-form input[type=email],#brand-form textarea')].map(e => e.name + '=' + e.value)]); throw new Error('brand not sent: ' + JSON.stringify(dbg)); }
      await page.screenshot({ path: path.join(SHOTS, `brand-sent-${label}.png`) });
      await wait(300);
      const rowsB = readCsv(csvB);
      assert.deepStrictEqual(rowsB[0], schema.forms.brand.columns, 'brand header = CONTRACTS 6.3 order');
      assert.strictEqual(rowsB.length, beforeB.rows + (beforeB.rows ? 1 : 2), 'exactly one new brand row');
      const b = Object.fromEntries(rowsB[0].map((c, i) => [c, rowsB[rowsB.length - 1][i]]));
      assert.strictEqual(b.website, 'https://example.com'); assert.strictEqual(b.category, 'chips-crisps');
      assert.strictEqual(b.budget_approver_is_contact, 'N'); assert.strictEqual(b.budget_approver_name_title, 'SAMPLE Alex Kim, CEO');
      assert.strictEqual(b.q3_buy_path_near_cluster, 'unsure'); assert.strictEqual(b.excluded_category_confirmed, 'Y');
      assert.strictEqual(lines(notes).length, beforeB.notes + 1, 'exactly one notification for the brand row');
      ok(`brand form submitted at ${label} width: one row, exact columns, one notification`, { row: b });

      const hits = lines(an).map(l => JSON.parse(l));
      for (const p of ['/offices', '/brands']) assert(hits.some(h => h.p === p && !h.e), 'page view ' + p);
      for (const ev of ['office-intake-started', 'office-intake-sent', 'brand-intake-started', 'brand-intake-sent']) assert(hits.some(h => h.p === ev && h.e === 'true'), 'event ' + ev);
      assert(hits.every(h => h.b === '153'), 'automated browser flagged with b=153');
      assert(hits.some(h => h.p === '/offices' && h.q === '?utm_source=SAMPLE-email'), 'campaign query passed as q');
      ok(`analytics stub received page views and the four form events at ${label} width`, { hits: hits.length });
      assert.deepStrictEqual(lines(path.join(OUT, 'preflight.log')), [], 'no CORS preflight sent');
      const cookies = await ctx.cookies(); assert.strictEqual(cookies.length, 0, 'no cookies');
      ok(`no CORS preflight and no cookies at ${label} width`);
      assert.deepStrictEqual(errors, [], 'no page errors');
      await ctx.close();
    }

    // ---------- staging: the real config sends nothing ----------
    {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
      const page = await ctx.newPage();
      const foreign = []; page.on('request', r => { if (!r.url().startsWith(SITE)) foreign.push(r.url()); });
      await page.goto(SITE + 'offices.html', { waitUntil: 'networkidle' });
      assert(await page.isVisible('#join [data-staging-form]'), 'staging notice visible above the form');
      for (const [k, v] of Object.entries(OFFICE)) await page.fill(`#office-form [name="${k}"]`, v);
      for (const [n, v] of [['pantry_owner_is_contact', 'Y'], ['receiving_type', 'walk-up'], ['ui_receiving_window', '8 to 10 am'], ['coi_required', 'no'], ['survey_channel', 'email']]) await page.check(`#office-form input[name="${n}"][value="${v}"]`);
      const before = lines(path.join(OUT, 'office_intake.csv')).length;
      await page.tap('#office-form button[type="submit"]');
      await wait(800);
      const msg = await page.textContent('#office-form .form-status');
      assert(/Staging: submissions are not live yet\. Nothing was sent\./.test(msg), 'staging message shown');
      assert(await page.isHidden('#join .form-done'), 'thank-you panel never shown in staging');
      assert.deepStrictEqual(foreign, [], 'no request leaves the site in staging');
      assert.strictEqual(lines(path.join(OUT, 'office_intake.csv')).length, before, 'no row written in staging');
      const robots = await page.getAttribute('meta[name="robots"]', 'content');
      assert.strictEqual(robots, 'noindex, nofollow');
      await page.screenshot({ path: path.join(SHOTS, 'office-staging-message-phone.png') });
      ok('staging config: notice shown, message on submit, no request, no row, robots noindex');
      await ctx.close();
    }

    // ---------- validation, error summary and focus ----------
    {
      const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
      await ctx.route('**/site.config.js', r => r.fulfill({ contentType: 'application/javascript', body: config(LIVE) }));
      const page = await ctx.newPage();
      await page.goto(SITE + 'offices.html#join', { waitUntil: 'networkidle' });
      await page.check('#office-form input[name="pantry_owner_is_contact"][value="N"]');
      await page.check('#office-form input[name="ui_categories_mode"][value="some"]');
      await page.click('#office-form button[type="submit"]');
      assert(await page.isVisible('#office-form .error-summary'));
      assert.strictEqual(await page.evaluate(() => document.activeElement.classList.contains('error-summary')), true, 'focus on error summary');
      const items = await page.$$eval('#office-form .error-summary li', l => l.map(x => x.textContent));
      assert.strictEqual(items.length, 13, 'all 13 problems listed: ' + items.join(' | '));
      assert.strictEqual(await page.getAttribute('#o-company', 'aria-invalid'), 'true');
      assert.strictEqual(await page.getAttribute('#o-pantry_owner_name', 'aria-invalid'), 'true');
      await page.waitForTimeout(900); // let the smooth scroll to the summary finish
      await page.screenshot({ path: path.join(SHOTS, 'office-errors-desktop.png') });
      await page.click('#office-form .error-summary li:first-child a');
      assert.strictEqual(await page.evaluate(() => document.activeElement.id), 'o-company', 'summary link focuses the field');
      ok('empty office form: error summary with 13 linked items, focus management, aria-invalid', { items });
      await page.fill('#o-tuesday_headcount', 'about sixty');
      await page.fill('#o-contact_email', 'jo at example');
      await page.click('#office-form button[type="submit"]');
      const msgs = await page.$$eval('#office-form .err', l => l.map(x => x.textContent).filter(Boolean));
      assert(msgs.includes('Enter a number, like 60.') && msgs.includes('Enter an email address like name@company.com.'));
      ok('format errors: headcount and email messages');
      await ctx.close();
    }

    // ---------- server-side checks against the mock (honeypot, bad value, duplicate) ----------
    {
      const base = { form: 'office', form_version: 'office-1.0', company: 'SAMPLE Direct', contact_name: 'SAMPLE A', contact_title: 'Ops', contact_email: 'a@example.com', office_address: '1 Example St', tuesday_headcount: '50', pantry_owner_is_contact: 'Y', receiving_type: 'walk-up', receiving_window: '8 to 10 am', coi_required: 'no', survey_channel: 'email', categories_wanted: 'bars' };
      const send = async p => (await fetch(`${MOCK}/exec`, { method: 'POST', body: new URLSearchParams(p) })).json();
      const csv = path.join(OUT, 'office_intake.csv'), notes = path.join(OUT, 'notifications.log');
      const n0 = [readCsv(csv).length, lines(notes).length];
      assert.deepStrictEqual(await send({ ...base, hp_url: 'spam', submission_id: 'SAMPLE-hp-000001' }), { ok: true });
      const bad = await send({ ...base, receiving_type: 'drone', submission_id: 'SAMPLE-bad-00001' });
      assert.strictEqual(bad.error, 'validation'); assert.strictEqual(bad.fields.receiving_type, 'invalid');
      assert.deepStrictEqual(await send({ ...base, submission_id: 'SAMPLE-dup-00001' }), { ok: true });
      assert.deepStrictEqual(await send({ ...base, submission_id: 'SAMPLE-dup-00001' }), { ok: true, duplicate: true });
      assert.deepStrictEqual([readCsv(csv).length, lines(notes).length], [n0[0] + 1, n0[1] + 1], 'only the first good submission wrote a row and a notification');
      ok('mock endpoint: honeypot writes nothing, bad value refused, repeat submission_id writes one row');
    }

    // ---------- rename in one edit ----------
    {
      const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
      await ctx.route('**/site.config.js', r => r.fulfill({ contentType: 'application/javascript', body: config([[/BRAND_NAME: "Desk Drop"/, 'BRAND_NAME: "Testname Collective"']]) }));
      const page = await ctx.newPage();
      for (const p of ['index', 'brands', 'offices', 'privacy', 'survey-privacy', '404']) {
        await page.goto(SITE + p + '.html', { waitUntil: 'networkidle' });
        const txt = await page.evaluate(() => document.body.innerText + ' ' + document.title + ' ' + [...document.querySelectorAll('meta')].map(m => m.content).join(' '));
        assert(!/Desk\s*Drop/i.test(txt), 'old name still visible on ' + p);
        assert(txt.includes('Testname Collective'), 'new name missing on ' + p);
      }
      ok('rename: BRAND_NAME changed in site.config.js only; old name gone from text, titles and meta on all 6 pages');
      await ctx.close();
    }

    // ---------- founding tier retired, and STAGING false ----------
    {
      const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
      await ctx.route('**/site.config.js', r => r.fulfill({ contentType: 'application/javascript', body: config([[/FOUNDING_TIER_OPEN: true/, 'FOUNDING_TIER_OPEN: false'], [/STAGING: true/, 'STAGING: false']]) }));
      const page = await ctx.newPage();
      await page.goto(SITE + 'brands.html', { waitUntil: 'networkidle' });
      const txt = await page.evaluate(() => document.body.innerText);
      assert(!/founding (price|tier|brand)|founding ·|\$600 for|\$120/i.test(txt), 'founding tier still mentioned: ' + (txt.match(/.{40}(founding (price|tier|brand)|\$600 for|\$120).{40}/i) || [''])[0]);
      assert(txt.includes('$1,500') && txt.includes('$150'));
      assert.strictEqual(await page.$$eval('.price-card', l => l.filter(e => e.offsetParent).length), 2);
      assert.strictEqual(await page.$('meta[name="robots"]'), null, 'no robots meta when STAGING is false');
      assert(await page.isHidden('.staging-bar'));
      await page.screenshot({ path: path.join(SHOTS, 'brands-founding-closed-desktop.png'), fullPage: false });
      await page.goto(SITE + 'index.html', { waitUntil: 'networkidle' });
      const home = await page.evaluate(() => document.body.innerText);
      assert(!/founding price|\$600/i.test(home), 'founding price still on the home page');
      ok('founding tier retired with one setting: founding price gone, standard and extra office stay; STAGING false removes noindex and bar');
      await ctx.close();
    }
  } finally {
    await browser.close();
    site.kill(); mock.kill();
    fs.mkdirSync(path.join(__dirname, 'out'), { recursive: true });
    fs.writeFileSync(path.join(__dirname, 'out', 'e2e-results.json'), JSON.stringify(results, null, 2));
  }
  console.log(`\n${results.checks.length} checks passed. Mock output: ${path.relative(ROOT, OUT)}`);
}
main().catch(e => { console.error('FAIL:', e.message); process.exitCode = 1; });
