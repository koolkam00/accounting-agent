// Quality checks against the QA.md pass bar:
//  P5 axe-core WCAG 2.1 A/AA, every page, 390x844 and 1280x800, light and dark, form states
//  P6 page weight (cold cache, everything loaded after scrolling to the end)
//  P7 keyboard (skip link first, reading order, visible focus, arrows in radio groups, Enter submits, no trap)
//  P8 labels (every control labeled, groups in fieldset/legend, optional marked)
//  P16 layout (no horizontal scroll at 320/390/768/1280; tap targets at least 44 x 44)
//  P18 no third-party requests, no cookies, no storage
// Usage (from website/): node tests/quality.js     Writes tests/out/quality-results.json
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const PORT = 8124;
const SITE = `http://127.0.0.1:${PORT}/`;
const AXE = fs.readFileSync(path.join(__dirname, 'node_modules', 'axe-core', 'axe.min.js'), 'utf8');
const PAGES = ['index', 'brands', 'offices', 'privacy', 'survey-privacy', '404'];
const VIEWPORTS = [['phone', 390, 844, true], ['desktop', 1280, 800, false]];
const results = { date: new Date().toISOString(), axe: [], weight: [], keyboard: [], labels: [], layout: [], privacy: [] };
let failures = 0;
const fail = (where, msg) => { failures++; console.log('FAIL', where, msg); };

async function axe(page, where) {
  await page.addScriptTag({ content: AXE });
  const r = await page.evaluate(() => window.axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] }, resultTypes: ['violations'] }));
  const v = r.violations.map(x => ({ id: x.id, impact: x.impact, nodes: x.nodes.length, sample: x.nodes[0] && x.nodes[0].target.join(' ') }));
  results.axe.push({ where, violations: v.length, details: v });
  if (v.length) fail(where, 'axe: ' + JSON.stringify(v));
  return v.length;
}

async function formStates(page, kind, where) {
  const form = kind === 'office' ? '#office-form' : '#brand-form';
  // conditional fields open
  if (kind === 'office') {
    await page.check(`${form} input[name="pantry_owner_is_contact"][value="N"]`);
    await page.check(`${form} input[name="ui_receiving_window"][value="other"]`);
    await page.check(`${form} input[name="ui_categories_mode"][value="some"]`);
  } else {
    await page.check(`${form} input[name="budget_approver_is_contact"][value="N"]`);
  }
  await axe(page, where + ' conditional fields open');
  await page.click(`${form} button[type="submit"]`);
  await page.waitForTimeout(100);
  await axe(page, where + ' error summary shown');
  // sent panel (shown the way site.js shows it)
  await page.evaluate(f => { const form = document.querySelector(f); form.hidden = true; form.closest('section').querySelector('.form-done').hidden = false; }, form);
  await axe(page, where + ' sent panel');
}

(async () => {
  const site = spawn('python3', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1', '--directory', path.join(ROOT, 'site')], { stdio: 'ignore' });
  await new Promise(r => setTimeout(r, 1000));
  const browser = await chromium.launch();
  try {
    // ---------- P5 axe ----------
    for (const [label, w, h, mobile] of VIEWPORTS) {
      for (const scheme of ['light', 'dark']) {
        const ctx = await browser.newContext({ viewport: { width: w, height: h }, isMobile: mobile, hasTouch: mobile, colorScheme: scheme });
        const page = await ctx.newPage();
        for (const p of PAGES) {
          await page.goto(SITE + p + '.html', { waitUntil: 'networkidle' });
          const where = `${p} ${label} ${scheme}`;
          await axe(page, where);
          if (p === 'offices') await formStates(page, 'office', where);
          if (p === 'brands') await formStates(page, 'brand', where);
        }
        await ctx.close();
      }
    }
    console.log('axe runs:', results.axe.length, 'violations:', results.axe.reduce((a, b) => a + b.violations, 0));

    // ---------- P6 weight and P18 privacy ----------
    for (const p of PAGES) {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
      const page = await ctx.newPage();
      const cdp = await ctx.newCDPSession(page);
      await cdp.send('Network.enable');
      await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
      const sizes = {}; const urls = {};
      cdp.on('Network.responseReceived', e => { urls[e.requestId] = e.response.url; });
      cdp.on('Network.loadingFinished', e => { sizes[e.requestId] = e.encodedDataLength; });
      await page.goto(SITE + p + '.html', { waitUntil: 'networkidle' });
      await page.evaluate(async () => { for (let y = 0; y <= document.body.scrollHeight; y += 400) { scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); } });
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(300);
      const files = Object.keys(sizes).map(id => ({ url: (urls[id] || '').replace(SITE, ''), bytes: sizes[id] }));
      const total = files.reduce((a, b) => a + b.bytes, 0);
      const foreign = Object.values(urls).filter(u => !u.startsWith(SITE));
      const storage = await page.evaluate(() => ({ cookies: document.cookie, local: localStorage.length, session: sessionStorage.length }));
      results.weight.push({ page: p, total_bytes: total, total_kb: +(total / 1024).toFixed(1), requests: files.length, files });
      results.privacy.push({ page: p, third_party_requests: foreign, ...storage });
      if (total >= 300 * 1024) fail(p, 'page weight ' + total);
      if (foreign.length) fail(p, 'third-party requests ' + foreign.join(', '));
      if (storage.cookies || storage.local || storage.session) fail(p, 'storage used');
      await ctx.close();
    }
    console.log('weight (KB, uncompressed, all files):', results.weight.map(x => `${x.page} ${x.total_kb}`).join(', '));

    // ---------- P7 keyboard ----------
    for (const p of PAGES) {
      const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
      const page = await ctx.newPage();
      await page.goto(SITE + p + '.html', { waitUntil: 'networkidle' });
      const expected = await page.evaluate(() => {
        const sel = 'a[href], button, input, select, textarea, [tabindex]';
        const seen = new Set();
        return [...document.querySelectorAll(sel)].filter(el => {
          if (el.tabIndex < 0 || el.disabled || el.closest('[hidden]') || el.closest('[aria-hidden="true"]')) return false;
          const s = getComputedStyle(el); if (s.visibility === 'hidden' || s.display === 'none') return false;
          if (!el.getClientRects().length && !el.matches('.skip-link')) return false;
          if (el.type === 'radio') { if (seen.has(el.name)) return false; seen.add(el.name); }
          return true;
        }).map(el => el.id || el.name || el.getAttribute('href') || el.tagName);
      });
      const got = []; const noFocusRing = [];
      for (let i = 0; i < expected.length + 1; i++) {
        await page.keyboard.press('Tab');
        const info = await page.evaluate(() => {
          const el = document.activeElement; if (!el || el === document.body) return null;
          const target = (el.type === 'radio' || el.type === 'checkbox') ? el.closest('label') : el;
          const s = getComputedStyle(target);
          return { key: el.id || el.name || el.getAttribute('href') || el.tagName, ring: s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) >= 2 };
        });
        if (!info) break;
        got.push(info.key); if (!info.ring) noFocusRing.push(info.key);
      }
      const orderOk = JSON.stringify(got.slice(0, expected.length)) === JSON.stringify(expected);
      const first = got[0] === '#main';
      // Skip link moves focus to main
      await page.goto(SITE + p + '.html', { waitUntil: 'networkidle' });
      await page.keyboard.press('Tab'); await page.keyboard.press('Enter');
      const skipOk = await page.evaluate(() => document.activeElement && document.activeElement.id === 'main');
      const entry = { page: p, tab_stops: got.length, order_matches_dom: orderOk, skip_link_first: first, skip_link_moves_focus: skipOk, missing_focus_ring: noFocusRing };
      results.keyboard.push(entry);
      if (!orderOk || !first || !skipOk || noFocusRing.length) fail(p, 'keyboard ' + JSON.stringify(entry) + ' expected ' + JSON.stringify(expected) + ' got ' + JSON.stringify(got));
      await ctx.close();
    }
    // Radio arrows and Enter submits (office form, staging config)
    {
      const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
      const page = await ctx.newPage();
      await page.goto(SITE + 'offices.html', { waitUntil: 'networkidle' });
      await page.focus('#office-form input[name="coi_required"][value="yes"]');
      await page.keyboard.press('Space'); await page.keyboard.press('ArrowRight');
      const arrow = await page.$eval('#office-form input[name="coi_required"]:checked', e => e.value);
      await page.focus('#o-company'); await page.keyboard.press('Enter');
      const summary = await page.isVisible('#office-form .error-summary');
      results.keyboard.push({ radio_arrow_moves_choice: arrow === 'no', enter_submits_form: summary });
      if (arrow !== 'no' || !summary) fail('offices', 'radio arrows or Enter submit');
      await ctx.close();
    }
    console.log('keyboard:', results.keyboard.length, 'entries');

    // ---------- P8 labels ----------
    {
      const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
      const page = await ctx.newPage();
      for (const p of ['offices', 'brands']) {
        await page.goto(SITE + p + '.html', { waitUntil: 'networkidle' });
        const r = await page.evaluate(() => {
          const out = { controls: 0, unlabeled: [], ungrouped: [], optional_unmarked: [], required_marked_optional: [], described_missing: [] };
          for (const el of document.querySelectorAll('form input, form select, form textarea')) {
            if (el.type === 'hidden' || el.name === 'hp_url') continue;
            out.controls++;
            const lab = el.labels && el.labels.length ? el.labels[0].textContent.trim() : '';
            if (!lab) out.unlabeled.push(el.name);
            if (el.type === 'radio' || el.type === 'checkbox') {
              const fs = el.closest('fieldset.choice'); if (!fs || !fs.querySelector('legend')) out.ungrouped.push(el.name);
            } else {
              const req = el.required || el.hasAttribute('data-required-if');
              if (!req && !/optional/.test(lab)) out.optional_unmarked.push(el.name);
              if (req && /optional/.test(lab)) out.required_marked_optional.push(el.name);
              const ids = (el.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean);
              if (!ids.length || ids.some(id => !document.getElementById(id))) out.described_missing.push(el.name);
            }
          }
          return out;
        });
        results.labels.push({ page: p, ...r });
        if (r.unlabeled.length || r.ungrouped.length || r.optional_unmarked.length || r.required_marked_optional.length || r.described_missing.length) fail(p, 'labels ' + JSON.stringify(r));
      }
      await ctx.close();
    }
    console.log('labels:', JSON.stringify(results.labels.map(x => [x.page, x.controls, x.unlabeled.length])));

    // ---------- P16 layout and tap targets ----------
    for (const w of [320, 390, 768, 1280]) {
      const ctx = await browser.newContext({ viewport: { width: w, height: 800 }, isMobile: w < 800, hasTouch: w < 800 });
      const page = await ctx.newPage();
      for (const p of PAGES) {
        await page.goto(SITE + p + '.html', { waitUntil: 'networkidle' });
        if (p === 'offices') { await page.check('#office-form input[name="ui_categories_mode"][value="some"]'); }
        const r = await page.evaluate(() => {
          const vw = document.documentElement.clientWidth, sw = document.documentElement.scrollWidth;
          const small = [];
          for (const el of document.querySelectorAll('button, .btn, .options label, .site-nav a, input[type=text], input[type=email], input[type=tel], input[type=url], select')) {
            if (el.closest('[hidden]') || el.closest('.hp')) continue; // .hp = off-screen honeypot, not a target
            const b = el.getBoundingClientRect(); if (!b.width) continue;
            if (b.height < 44 || b.width < 44) small.push((el.className || el.tagName) + ' ' + Math.round(b.width) + 'x' + Math.round(b.height));
          }
          return { horizontal_scroll: sw > vw, small_targets: small };
        });
        results.layout.push({ width: w, page: p, ...r });
        if (r.horizontal_scroll || r.small_targets.length) fail(`${p}@${w}`, 'layout ' + JSON.stringify(r));
      }
      await ctx.close();
    }
    console.log('layout runs:', results.layout.length);
  } finally {
    await browser.close(); site.kill();
    fs.mkdirSync(path.join(__dirname, 'out'), { recursive: true });
    results.failures = failures;
    fs.writeFileSync(path.join(__dirname, 'out', 'quality-results.json'), JSON.stringify(results, null, 2));
  }
  console.log(failures ? `\n${failures} FAILURES` : '\nall quality checks passed');
  process.exitCode = failures ? 1 : 0;
})();
