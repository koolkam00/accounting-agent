#!/usr/bin/env node
/*
  render.js: turn a JSON file into a print-ready PDF (and optional PNG proofs) from any template.

  Usage (from the desk-drop-identity folder):
    node render/render.js <template> <data.json> <out.pdf> [options]

    <template>   tent-card | case-label | a path to any template .html in templates/
    <data.json>  one object, or an array of objects (one printed sheet each; for the
                 case label, two labels per sheet)
    <out.pdf>    the PDF to write

  Options
    --mode home|pro     tent card only. home (default): US Letter with crop and fold marks,
                        for a home printer. pro: trim size plus 0.125 in bleed, no marks,
                        for a print shop (only after the name is cleared).
    --png <file>        also save a PNG proof of the first sheet
    --face-png <file>   tent card: also save the front face alone (7 x 5 in)
    --dpi <n>           resolution for PNGs (default 200)
    --final             refuse to render if any [PLACEHOLDER] or SAMPLE value remains
    --force             write the PDF even if the template reports errors (for debugging only)
    --json              print the status as JSON (for the operations generator)

  Exit codes: 0 ok, 1 usage or crash, 2 template errors (no PDF written), 3 --final check failed.
  Needs Node 18+ and Playwright (npm install, then npx playwright install chromium).
*/
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const argv = process.argv.slice(2);
const positional = [];
const opts = {};
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a.startsWith('--')) {
    const k = a.slice(2);
    if (['final', 'force', 'json'].includes(k)) opts[k] = true;
    else opts[k] = argv[++i];
  } else positional.push(a);
}
if (positional.length < 3) {
  console.error('Usage: node render/render.js <tent-card|case-label|path.html> <data.json> <out.pdf> [--mode home|pro] [--png f] [--face-png f] [--dpi n] [--final] [--json]');
  process.exit(1);
}
const [tpl, dataPath, outPdf] = positional;
const tplPath = fs.existsSync(tpl) && tpl.endsWith('.html')
  ? path.resolve(tpl)
  : path.join(ROOT, 'templates', tpl, `${tpl}.html`);
if (!fs.existsSync(tplPath)) { console.error(`No template at ${tplPath}`); process.exit(1); }

let data;
try { data = JSON.parse(fs.readFileSync(dataPath, 'utf8')); }
catch (e) { console.error(`Cannot read ${dataPath}: ${e.message}`); process.exit(1); }

(async () => {
  const { chromium } = require('playwright');
  const browser = await chromium.launch();
  const dpi = Number(opts.dpi || 200);
  const context = await browser.newContext({ deviceScaleFactor: dpi / 96, viewport: { width: 1400, height: 1200 } });
  const page = await context.newPage();
  const consoleErrors = [];
  page.on('pageerror', (e) => consoleErrors.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  await page.addInitScript(({ data, mode }) => {
    window.__DD_DATA__ = data;
    window.__DD_HEADLESS__ = true;
    window.__DD_MODE__ = mode;
  }, { data, mode: opts.mode || 'home' });
  const url = 'file://' + tplPath + (opts.mode ? `?mode=${encodeURIComponent(opts.mode)}` : '');
  await page.goto(url, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready, null, { timeout: 30000 });
  await page.evaluate(() => document.fonts.ready);
  const status = await page.evaluate(() => window.__DD_STATUS__);
  const fits = await page.evaluate(() => [...document.querySelectorAll('.dd-sheet')].map(s => s.dataset.fit ? JSON.parse(s.dataset.fit) : null));
  status.fit = fits;
  status.console_errors = consoleErrors;
  status.template = path.relative(ROOT, tplPath);
  status.records = Array.isArray(data) ? data.length : 1;

  const report = () => {
    if (opts.json) { console.log(JSON.stringify(status, null, 2)); return; }
    status.errors.forEach(m => console.log('ERROR   ' + m));
    status.warnings.forEach(m => console.log('WARNING ' + m));
    if (status.placeholders.length) console.log('PLACEHOLDERS left: ' + status.placeholders.join(', '));
    if (status.sample) console.log('NOTE    SAMPLE data: output carries the SAMPLE banner.');
    consoleErrors.forEach(m => console.log('PAGE    ' + m));
  };

  if ((status.errors.length || consoleErrors.length) && !opts.force) {
    report();
    console.error('No PDF written. Fix the errors above (or pass --force to see the broken layout).');
    await browser.close();
    process.exit(2);
  }
  if (opts.final && (status.placeholders.length || status.sample)) {
    report();
    console.error('--final: placeholders or SAMPLE values remain. No PDF written.');
    await browser.close();
    process.exit(3);
  }

  await page.emulateMedia({ media: 'print' });
  fs.mkdirSync(path.dirname(path.resolve(outPdf)), { recursive: true });
  await page.pdf({ path: outPdf, preferCSSPageSize: true, printBackground: true });

  if (opts.png) {
    const el = await page.$('.dd-sheet');
    await el.screenshot({ path: opts.png });
  }
  if (opts['face-png']) {
    const el = await page.$('.dd-sheet .face.front');
    if (el) await el.screenshot({ path: opts['face-png'] });
  }
  report();
  if (!opts.json) console.log(`Wrote ${outPdf}${opts.png ? ' and ' + opts.png : ''}${opts['face-png'] ? ' and ' + opts['face-png'] : ''}`);
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
