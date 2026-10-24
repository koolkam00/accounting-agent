#!/usr/bin/env node
/*
  render-page.js: print any static HTML page in this folder (spec sheets, guides, one-pagers)
  to PDF, using the page's own @page size. For data-driven templates use render.js instead.

    node render/render-page.js <page.html> <out.pdf> [--png out.png] [--dpi 110]
*/
const fs = require('fs');
const path = require('path');
const args = process.argv.slice(2);
const pos = args.filter((a, i) => !a.startsWith('--') && !(args[i - 1] || '').startsWith('--'));
const opt = (k) => { const i = args.indexOf('--' + k); return i === -1 ? null : args[i + 1]; };
if (pos.length < 2) { console.error('usage: node render/render-page.js <page.html> <out.pdf> [--png out.png] [--dpi n]'); process.exit(1); }
(async () => {
  const { chromium } = require('playwright');
  const browser = await chromium.launch();
  const dpi = Number(opt('dpi') || 110);
  const page = await browser.newPage({ deviceScaleFactor: dpi / 96, viewport: { width: 816, height: 1056 } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('requestfailed', r => errors.push('failed to load ' + r.url()));
  await page.goto('file://' + path.resolve(pos[0]), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  if (errors.length) { console.error(errors.join('\n')); await browser.close(); process.exit(2); }
  fs.mkdirSync(path.dirname(path.resolve(pos[1])), { recursive: true });
  await page.emulateMedia({ media: 'print' });
  await page.pdf({ path: pos[1], preferCSSPageSize: true, printBackground: true });
  if (opt('png')) { await page.emulateMedia({ media: 'screen' }); await page.screenshot({ path: opt('png'), fullPage: true }); }
  console.log('Wrote ' + pos[1] + (opt('png') ? ' and ' + opt('png') : ''));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
