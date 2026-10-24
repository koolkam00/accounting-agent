// Renders: node _build/render.js <cluster folder>
// 1) public-map.svg -> public-map.png  2) _build/out/route_sheet.html -> route-private.png
// 3) QA screenshots of map-private.html at phone and desktop width into _build/out/qa/
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
(async () => {
  const dir = process.argv[2];
  const qa = path.join(dir, '_build', 'out', 'qa'); fs.mkdirSync(qa, { recursive: true });
  const browser = await chromium.launch();
  // public map
  const svg = fs.readFileSync(path.join(dir, 'public-map.svg'), 'utf8');
  const [, w, h] = svg.match(/viewBox="0 0 (\d+) (\d+)"/).map(Number);
  let page = await browser.newPage({ viewport: { width: w, height: h } });
  await page.setContent(`<!doctype html><html><body style="margin:0">${svg}</body></html>`);
  await page.evaluate(() => document.fonts.ready); await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(dir, 'public-map.png'), clip: { x: 0, y: 0, width: w, height: h } });
  await page.close();
  // route sheet
  page = await browser.newPage({ viewport: { width: 1400, height: 960 } });
  const errs = []; page.on('pageerror', e => errs.push(String(e)));
  await page.goto('file://' + path.join(dir, '_build', 'out', 'route_sheet.html'), { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: path.join(dir, 'route-private.png'), fullPage: true });
  await page.close();
  // private map QA
  for (const [name, vw, vh] of [['phone', 390, 844], ['desktop', 1280, 860]]) {
    page = await browser.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: 2 });
    page.on('pageerror', e => errs.push(name + ': ' + String(e)));
    page.on('console', m => { if (m.type() === 'error') errs.push(name + ' console: ' + m.text()); });
    await page.goto('file://' + path.join(dir, 'map-private.html'), { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(qa, `private-${name}.png`) });
    if (name === 'phone') {
      await page.click('#btnFind'); await page.fill('#q', 'brain'); await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(qa, 'private-phone-search.png') });
      await page.click('#results div'); await page.waitForTimeout(2500);
      await page.screenshot({ path: path.join(qa, 'private-phone-popup.png') });
      await page.selectOption('#sess', '3').catch(() => {});
      await page.waitForTimeout(500);
      await page.click('#btnFind'); await page.selectOption('#sess', '3'); await page.waitForTimeout(2500);
      await page.screenshot({ path: path.join(qa, 'private-phone-walk3.png') });
    }
    await page.close();
  }
  await browser.close();
  console.log('rendered; errors:', JSON.stringify(errs));
})();
