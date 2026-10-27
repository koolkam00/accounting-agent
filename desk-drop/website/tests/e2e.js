// End-to-end: serves site/ locally, starts tests/mock_endpoint.py on another origin, and drives
// both forms with Playwright at 390 x 844 (touch) and 1280 x 800. Checks rows, columns, one
// notification each, the analytics stub, staging behavior, validation, rename and founding tier.
// Usage (from website/): node tests/e2e.js      Writes tests/out/e2e-results.json and _shots/states/.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const { buildSample } = require('./sample_build');
const http = require('http');
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
// Required office fields only (P9 times the required path). The titles are optional since review round 2 (R2-10).
const OFFICE = { company: 'SAMPLE Studio', contact_name: 'SAMPLE Jo Park', contact_email: 'sample.jo@example.com', office_address: '123 Fifth Avenue', tuesday_headcount: '60' };
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

    // ---------- P9 (restated in review round 2): both pantry-owner paths, reading the hero, scrolling ----------
    {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
      await ctx.route('**/site.config.js', r => r.fulfill({ contentType: 'application/javascript', body: config(LIVE) }));
      const page = await ctx.newPage();
      let taps = 0, chars = 0;
      const settle = () => page.evaluate(() => new Promise(res => { let last = -1, same = 0; (function f() { if (scrollY === last && ++same > 4) return res(); if (scrollY !== last) same = 0; last = scrollY; requestAnimationFrame(f); })(); }));
      const press = async sel => { await settle(); await page.tap(sel); taps++; };
      const type = async (sel, text) => { await press(sel); await page.keyboard.type(text); chars += text.length; };
      await page.goto(SITE + 'offices.html', { waitUntil: 'networkidle' });
      const geo = await page.evaluate(() => ({ heroWords: document.querySelector('main .hero').innerText.split(/\s+/).filter(Boolean).length,
        introWords: [...document.querySelectorAll('#join > .wrap > p:not([hidden])')].filter(e => e.offsetParent).map(e => e.innerText).join(' ').split(/\s+/).filter(Boolean).length,
        formHeight: document.querySelector('#office-form').getBoundingClientRect().height, vh: innerHeight }));
      await press('.hero-actions a[href="#join"]');
      const f = '#office-form ';
      for (const [k, v] of Object.entries(OFFICE)) await type(`${f}[name="${k}"]`, v);
      await press(`${f}input[name="pantry_owner_is_contact"][value="N"]`);
      const OWNER = 'SAMPLE Ana Ruiz';
      await type(`${f}[name="pantry_owner_name"]`, OWNER);
      await press(`${f}input[name="receiving_type"][value="front desk"]`);
      await press(`${f}input[name="ui_receiving_window"][value="9 to 11 am"]`);
      await press(`${f}input[name="coi_required"][value="unsure"]`);
      await press(`${f}input[name="survey_channel"][value="slack"]`);
      await press(`${f}button[type="submit"]`);
      await page.waitForSelector('#join .form-done:not([hidden])', { timeout: 10000 });
      await wait(300);
      const rows = readCsv(path.join(OUT, 'office_intake.csv'));
      const o = Object.fromEntries(rows[0].map((c, i) => [c, rows[rows.length - 1][i]]));
      assert.strictEqual(o.pantry_owner_is_contact, 'N'); assert.strictEqual(o.pantry_owner_name, OWNER); assert.strictEqual(o.pantry_owner_title, '');
      // Rates fixed in the pass bar: 2.5 typed characters a second, 1.5 s a tap, 1.5 s a scroll swipe
      // of half a screen, and reading the hero and the form intro at 250 words a minute.
      const swipes = Math.ceil(geo.formHeight / (geo.vh / 2));
      const readS = (geo.heroWords + geo.introWords) / 250 * 60;
      const est = (c, t) => Math.round((c / 2.5 + t * 1.5 + swipes * 1.5 + readS) * 10) / 10;
      const yes = results.timing.phone;
      const p9 = { hero_words: geo.heroWords, intro_words: geo.introWords, reading_s: Math.round(readS * 10) / 10, form_height_px: Math.round(geo.formHeight), swipes,
        yes_me: { typed_chars: yes.typed_chars, taps: yes.taps_before_submit, estimate_s: est(yes.typed_chars, yes.taps_before_submit) },
        someone_else: { typed_chars: chars, taps, estimate_s: est(chars, taps) } };
      results.timing.p9 = p9;
      assert(p9.yes_me.estimate_s <= 90 && p9.someone_else.estimate_s <= 90, 'P9 over 90 s: ' + JSON.stringify(p9));
      ok(`P9 office form on a phone: "Yes, me" ${p9.yes_me.estimate_s} s, "Someone else" ${p9.someone_else.estimate_s} s (reading ${p9.reading_s} s, ${swipes} swipes), both under 90; pantry owner's title left blank is accepted`, { p9 });
      await ctx.close();
    }

    // ---------- P21 (added in review round 3, R3-08): the brand page's two-minute target ----------
    // A brand founder understands the offer, the price and the report in two minutes on a phone.
    // Path: read the hero, tap "See the price", read the price cards and the two lines under them
    // (sales tax; no free pilots and what you supply), scroll on to the report contents and read its
    // heading, intro line and list. Rates as P9: 250 words a minute, 1.5 s a tap, 1.5 s a half-screen
    // swipe (from the top of the price section to the bottom of the report list). Founding tier open
    // (three cards, the longer case). The scroll-from-the-top figure without the jump link is recorded too.
    {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
      await ctx.route('**/site.config.js', r => r.fulfill({ contentType: 'application/javascript', body: config(LIVE) }));
      const page = await ctx.newPage();
      await page.goto(SITE + 'brands.html', { waitUntil: 'networkidle' });
      const g = await page.evaluate(() => {
        const w = t => t.split(/\s+/).filter(Boolean).length;
        const vis = e => e.offsetParent !== null;
        const y = e => e.getBoundingClientRect().top + scrollY;
        const cards = [...document.querySelectorAll('#price .price-card')].filter(vis);
        const under = [...document.querySelectorAll('#price .price-grid ~ p')].filter(vis).slice(0, 2);
        const rep = document.querySelector('#report');
        const list = rep.querySelector('.report-sections');
        return { hero: w(document.querySelector('main .hero').innerText), cards: cards.length, cardWords: cards.reduce((a, c) => a + w(c.innerText), 0),
          underWords: under.reduce((a, e) => a + w(e.innerText), 0), underText: under.map(e => e.innerText.slice(0, 40)),
          reportWords: w(rep.querySelector('h2').innerText) + w(rep.querySelector('h2 + p').innerText) + w(list.innerText),
          priceTop: y(document.querySelector('#price')), reportBottom: list.getBoundingClientRect().bottom + scrollY, vh: innerHeight };
      });
      await page.tap('.hero-actions a[href="#price"]');
      await page.evaluate(() => new Promise(res => { let last = -1, same = 0; (function f() { if (scrollY === last && ++same > 4) return res(); if (scrollY !== last) same = 0; last = scrollY; requestAnimationFrame(f); })(); }));
      const landed = await page.evaluate(() => ({ top: Math.round(document.querySelector('#price').getBoundingClientRect().top), hash: location.hash }));
      assert(landed.hash === '#price' && Math.abs(landed.top) < 120, '"See the price" lands on the price section: ' + JSON.stringify(landed));
      const words = g.hero + g.cardWords + g.underWords + g.reportWords;
      const readS = words / 250 * 60;
      const swipes = Math.ceil((g.reportBottom - g.priceTop) / (g.vh / 2));
      const est = Math.round((readS + 1.5 + swipes * 1.5) * 10) / 10;
      const swipesTop = Math.ceil(g.reportBottom / (g.vh / 2));
      const estTop = Math.round((readS + swipesTop * 1.5) * 10) / 10;
      const p21 = { hero_words: g.hero, price_cards: g.cards, card_words: g.cardWords, under_card_words: g.underWords, report_words: g.reportWords, words,
        reading_s: Math.round(readS * 10) / 10, price_top_px: Math.round(g.priceTop), report_list_bottom_px: Math.round(g.reportBottom), swipes, estimate_s: est,
        from_top_without_jump: { swipes: swipesTop, estimate_s: estTop } };
      results.timing.p21 = p21;
      assert(g.cards === 3 && g.underWords > 20, 'P21 measured the founding-open page with the lines under the cards: ' + JSON.stringify(g));
      assert(est <= 120, 'P21 over 120 s: ' + JSON.stringify(p21));
      ok(`P21 brand page on a phone: offer, price and report in ${est} s (${words} words, reading ${p21.reading_s} s, 1 tap, ${swipes} swipes), under 120; scrolling from the top without the jump link: ${estTop} s`, { p21 });
      await ctx.close();
    }

    // ---------- R3-04: out-of-range headcount note; thank-you promises nothing to a sender who is ruled out ----------
    {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
      await ctx.route('**/site.config.js', r => r.fulfill({ contentType: 'application/javascript', body: config(LIVE) }));
      const page = await ctx.newPage();
      await page.goto(SITE + 'offices.html', { waitUntil: 'networkidle' });
      const note = '#o-tuesday_headcount-note';
      const h = '#office-form [name="tuesday_headcount"]';
      const states = [];
      for (const v of ['300', '25', '1,20', '60', '30', '250']) {
        await page.fill(h, v);
        states.push([v, (await page.textContent(note)).trim()]);
      }
      const msg = "Offices this size can't join yet. You can still send the form, and we will reply.";
      assert.deepStrictEqual(states, [['300', msg], ['25', msg], ['1,20', ''], ['60', ''], ['30', ''], ['250', '']], 'size note: ' + JSON.stringify(states));
      assert.strictEqual(await page.getAttribute(note, 'aria-live'), 'polite');
      assert(/o-tuesday_headcount-note/.test(await page.getAttribute(h, 'aria-describedby')), 'note tied to the field');
      const done = await page.textContent('#join .form-done');
      assert(/If your office fits \(40 to 250 people on a Tuesday, inside the area on the map\), that email carries the one-page participation agreement\. If it doesn't fit yet, we will say so plainly\./.test(done.replace(/\s+/g, ' ')), 'office thank-you is conditional: ' + done);
      await page.goto(SITE + 'brands.html', { waitUntil: 'networkidle' });
      const bdone = (await page.textContent('#apply .form-done')).replace(/\s+/g, ' ');
      assert(/If the seven checks fit, we will suggest a 20-minute call/.test(bdone) && !/Next step: a 20-minute call/.test(bdone), 'brand thank-you is conditional: ' + bdone);
      await ctx.close();
      ok('offices: a headcount under 30 or over 250 shows a polite, non-blocking note (tied to the field); both thank-you messages are conditional on fit');
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
      assert.strictEqual(items.length, 11, 'all 11 problems listed (both titles are optional): ' + items.join(' | '));
      assert.strictEqual(await page.getAttribute('#o-company', 'aria-invalid'), 'true');
      assert.strictEqual(await page.getAttribute('#o-pantry_owner_name', 'aria-invalid'), 'true');
      await page.waitForTimeout(900); // let the smooth scroll to the summary finish
      await page.screenshot({ path: path.join(SHOTS, 'office-errors-desktop.png') });
      await page.click('#office-form .error-summary li:first-child a');
      assert.strictEqual(await page.evaluate(() => document.activeElement.id), 'o-company', 'summary link focuses the field');
      ok('empty office form: error summary with 11 linked items, focus management, aria-invalid', { items });
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
      assert(!/founding (price|tier|brand)|founding ·|\$600 for|\$120|5 or 10/i.test(txt), 'founding tier still mentioned: ' + (txt.match(/.{40}(founding (price|tier|brand)|\$600 for|\$120).{40}/i) || [''])[0]);
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

    // ---------- founding tier retired: question 6 asks about $1,500 and the row says brand-2.0 ----------
    {
      const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
      await ctx.route('**/site.config.js', r => r.fulfill({ contentType: 'application/javascript', body: config([...LIVE, [/FOUNDING_TIER_OPEN: true/, 'FOUNDING_TIER_OPEN: false']]) }));
      const page = await ctx.newPage();
      await page.goto(SITE + 'brands.html#apply', { waitUntil: 'networkidle' });
      const q6 = await page.innerText('#b-q6_contact_can_approve_600 legend');
      const fit6 = await page.innerText('.fit-list li:nth-child(6)');
      assert(q6.includes('$1,500') && !q6.includes('$600'), 'q6 legend: ' + q6);
      assert(fit6.includes('$1,500') && !fit6.includes('$600'), 'check 6: ' + fit6);
      const fit4 = await page.innerText('.fit-list li:nth-child(4)');
      const q4 = await page.innerText('#b-q4_can_ship_275_in_10bd legend');
      assert(fit4.includes('550') && !fit4.includes('275') && q4.includes('550') && !q4.includes('275'), 'check 4 and question 4 follow the tier: ' + fit4 + ' | ' + q4);
      await page.click('#brand-form button[type="submit"]');
      const q6err = await page.$$eval('#brand-form .error-summary li', l => l.map(x => x.textContent).find(t => t.startsWith('6.')));
      assert(q6err && q6err.includes('$1,500') && !q6err.includes('$600'), 'error summary label for q6: ' + q6err);
      for (const [k, v] of Object.entries(BRAND)) await page.fill(`#brand-form [name="${k}"]`, v);
      await page.selectOption('#brand-form select[name="category"]', 'bars');
      for (const [n, v] of [['budget_approver_is_contact', 'Y'], ['can_issue_discount_code', 'N'], ['preferred_timing', 'Just exploring'],
        ['q1_sealed_shelf_stable_60d', 'Y'], ['q2_labeled_ingredients_allergens', 'Y'], ['q3_buy_path_near_cluster', 'Y'],
        ['q4_can_ship_275_in_10bd', 'Y'], ['q5_product_liability_insurance', 'Y'], ['q6_contact_can_approve_600', 'N']]) await page.check(`#brand-form input[name="${n}"][value="${v}"]`);
      await page.check('#brand-form input[name="excluded_category_confirmed"]');
      await page.click('#brand-form button[type="submit"]');
      await page.waitForSelector('#apply .form-done:not([hidden])', { timeout: 10000 });
      await wait(300);
      const rows = readCsv(path.join(OUT, 'brand_intake.csv'));
      const last = Object.fromEntries(rows[0].map((c, i) => [c, rows[rows.length - 1][i]]));
      assert.strictEqual(last.form_version, 'brand-2.0', 'form_version once the founding tier is closed');
      assert.strictEqual(last.q6_contact_can_approve_600, 'N');
      ok('founding tier closed: questions and checks 4 and 6 ask about 550 units and $1,500 (error summary too), and the row is marked brand-2.0');
      await ctx.close();
    }

    // ---------- production copy: no JavaScript, link previews, extension-less URLs, nested 404 ----------
    {
      const pub = buildSample(path.join(__dirname, 'out', 'tmp', 'publish-' + Date.now()), { brandName: 'Testname Collective' });
      // A small stand-in for Cloudflare Pages: /brands serves brands.html, a missing path gets /404.html.
      const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript', '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2', '.txt': 'text/plain', '.xml': 'application/xml' };
      const cf = http.createServer((req, res) => {
        let u = decodeURIComponent(req.url.split('?')[0]);
        if (u.endsWith('/')) u += 'index.html';
        let f = path.join(pub, u);
        if (!fs.existsSync(f) && fs.existsSync(f + '.html')) f += '.html';
        let status = 200;
        if (!f.startsWith(pub) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { f = path.join(pub, '404.html'); status = 404; }
        res.writeHead(status, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' });
        fs.createReadStream(f).pipe(res);
      }).listen(8129, '127.0.0.1');
      await wait(200);
      const CF = 'http://127.0.0.1:8129/';
      try {
        const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false });
        const page = await ctx.newPage();
        for (const p of ['index', 'brands', 'offices', 'privacy', 'survey-privacy']) {
          await page.goto(CF + (p === 'index' ? '' : p), { waitUntil: 'load' });
          const r = await page.evaluate(() => ({
            title: document.title, header: document.querySelector('.site-header .dd-brand-name').textContent,
            site: (document.querySelector('meta[property="og:site_name"]') || {}).content, robots: document.querySelectorAll('meta[name="robots"]').length,
            canonical: (document.querySelector('link[rel="canonical"]') || {}).href, text: document.body.innerText,
            footerMail: document.querySelector('.site-footer a[href^="mailto:"]') && document.querySelector('.site-footer a[href^="mailto:"]').textContent,
            phoneLines: [...document.querySelectorAll('[data-config-line="PHONE"]')].filter(e => !e.hidden).length }));
          assert(r.title.endsWith(' · Testname Collective'), p + ' title: ' + r.title);
          assert.strictEqual(r.header, 'Testname Collective', p + ' header name without JavaScript');
          assert.strictEqual(r.site, 'Testname Collective', p + ' og:site_name');
          assert.strictEqual(r.robots, 0, p + ' production copy has no robots noindex');
          assert.strictEqual(r.canonical, 'https://sample.example/' + (p === 'index' ? '' : p), p + ' canonical is extension-less');
          assert(!/Desk\s*Drop/i.test(r.text + r.title), p + ': old name in the production copy');
          assert(!/\[(EMAIL|FOUNDER NAME|POSTAL ADDRESS|PHONE|LINKEDIN URL|COMPANY NAME)\]/.test(r.text), p + ': config placeholder left in the production copy');
          assert.strictEqual(r.footerMail, 'hello@sample.example');
          assert.strictEqual(r.phoneLines, 0, p + ': PHONE "" hides the phone lines');
          // Review round 3 (R3-05): what link unfurlers and scrapers read. No staging text, internal note or builder comment in the raw HTML.
          const raw = fs.readFileSync(path.join(pub, (p === 'index' ? 'index' : p) + '.html'), 'utf8');
          const bad = raw.replace(/<!-- PRODUCTION COPY[^>]*-->/, '').match(/Staging|not yet cleared|working name|SETUP\.md|legal pack|draft notice|staging-bar|staging-only|data-staging-form|<!--/i);
          assert(!bad, p + ': staging or internal wording in the production HTML: ' + (bad && bad[0]));
        }
        for (const [p, form] of [['offices', '#office-form'], ['brands', '#brand-form']]) {
          await page.goto(CF + p, { waitUntil: 'load' });
          assert(await page.isDisabled(`${form} button[type="submit"]`), p + ': submit disabled without JavaScript');
          assert.strictEqual(await page.getAttribute(form, 'method'), 'post');
          assert(/address at the bottom of this page/.test(await page.innerText('#main')), p + ': noscript notice shown');
          await page.fill(`${form} input[type="text"] >> nth=0`, 'SAMPLE');
          await page.keyboard.press('Enter');
          await wait(300);
          assert.strictEqual(page.url(), CF + p, p + ': Enter without JavaScript does not send the form or put answers in the address bar');
        }
        // Founding tier open (shipped setting): only the founding amounts are in the HTML.
        await page.goto(CF + 'brands', { waitUntil: 'load' });
        const open = await page.evaluate(() => ({ fit4: document.querySelector('.fit-list li:nth-child(4)').textContent, fit6: document.querySelector('.fit-list li:nth-child(6)').textContent,
          q4: document.querySelector('#b-q4_can_ship_275_in_10bd legend').textContent, cards: document.querySelectorAll('.price-card').length, html: document.documentElement.outerHTML }));
        assert(open.fit4.includes('275') && !open.fit4.includes('550'), 'check 4 (founding open): ' + open.fit4);
        assert(open.fit6.includes('$600') && !open.fit6.includes('$1,500'), 'check 6 (founding open): ' + open.fit6);
        assert(open.q4.includes('275') && !open.q4.includes('550'), 'question 4 (founding open): ' + open.q4);
        assert.strictEqual(open.cards, 3);
        assert(!open.html.includes('data-standard-only'), 'founding open: standard-only text removed from the HTML');
        const sm = fs.readFileSync(path.join(pub, 'sitemap.xml'), 'utf8');
        assert(sm.includes('<loc>https://sample.example/brands</loc>') && !sm.includes('.html'), 'sitemap lists extension-less URLs');
        await ctx.close();
        ok('production copy without JavaScript: name, title, og:site_name, contact details and canonical (extension-less) are in the HTML; no noindex; no staging text, internal note or comment in the raw HTML; forms cannot be sent and say why');

        // P14 without JavaScript (review round 2, R2-04): the founding tier retired in the production copy.
        const pubClosed = buildSample(path.join(__dirname, 'out', 'tmp', 'publish-closed-' + Date.now()), { foundingClosed: true });
        const cf2 = http.createServer((req, res) => {
          let u = decodeURIComponent(req.url.split('?')[0]); if (u.endsWith('/')) u += 'index.html';
          let f = path.join(pubClosed, u); if (!fs.existsSync(f) && fs.existsSync(f + '.html')) f += '.html';
          if (!f.startsWith(pubClosed) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
          res.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res);
        }).listen(8130, '127.0.0.1');
        try {
          const ctx3 = await browser.newContext({ viewport: { width: 1280, height: 800 }, javaScriptEnabled: false });
          const p3 = await ctx3.newPage();
          await p3.goto('http://127.0.0.1:8130/brands', { waitUntil: 'load' });
          const c = await p3.evaluate(() => ({ text: document.body.innerText, html: document.documentElement.outerHTML, rootClass: document.documentElement.className,
            cards: [...document.querySelectorAll('.price-card')].filter(e => e.offsetParent).length,
            fit4: document.querySelector('.fit-list li:nth-child(4)').textContent, fit6: document.querySelector('.fit-list li:nth-child(6)').textContent,
            q4: document.querySelector('#b-q4_can_ship_275_in_10bd legend').textContent, q6: document.querySelector('#b-q6_contact_can_approve_600 legend').textContent }));
          assert(!/\$600|\$120|founding (price|tier|brand)|founding ·|about 275|5 or 10/i.test(c.text), 'founding offer still in the text without JavaScript: ' + (c.text.match(/.{40}(\$600|\$120|founding|about 275).{40}/i) || [''])[0]);
          assert(!/data-founding|\$600|\$120/.test(c.html), 'founding offer still in the raw HTML');
          assert(/\bfounding-closed\b/.test(c.rootClass), '<html> carries founding-closed');
          assert.strictEqual(c.cards, 2, 'two price cards (standard, extra office)');
          assert(c.fit4.includes('550') && c.q4.includes('550'), 'check 4 and question 4 ask about 550: ' + c.fit4 + ' | ' + c.q4);
          assert(c.fit6.includes('$1,500') && c.q6.includes('$1,500'), 'check 6 and question 6 ask about $1,500');
          await p3.screenshot({ path: path.join(SHOTS, 'brands-founding-closed-nojs-desktop.png'), fullPage: false });
          await p3.goto('http://127.0.0.1:8130/', { waitUntil: 'load' });
          assert(!/founding price|\$600/i.test(await p3.evaluate(() => document.body.innerText)), 'home page still shows the founding price without JavaScript');
          await ctx3.close();
          ok('production copy with the founding tier retired, JavaScript off: no $600 or $120 anywhere in the HTML, two price cards, checks 4 and 6 ask about 550 units and $1,500');
        } finally { cf2.close(); }

        const ctx2 = await browser.newContext({ viewport: { width: 390, height: 844 } });
        const p2 = await ctx2.newPage();
        const resp = await p2.goto(CF + 'brands/some/missing-page', { waitUntil: 'networkidle' });
        assert.strictEqual(resp.status(), 404);
        const nested = await p2.evaluate(() => ({ border: getComputedStyle(document.querySelector('.site-header')).borderBottomWidth,
          links: [...document.querySelectorAll('main a')].map(a => a.getAttribute('href')), fontsOk: [...document.styleSheets].length }));
        assert.strictEqual(nested.border, '3px', 'site.css applies on a nested 404');
        assert.deepStrictEqual(nested.links, ['/', '/brands', '/offices'], '404 links are root-absolute');
        await ctx2.close();
        ok('production 404 served for a nested missing path keeps its styles and working links');
      } finally { cf.close(); }
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
