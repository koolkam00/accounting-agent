const { chromium } = require('playwright');
(async () => {
  const out = process.argv[2]; const file = 'file:///home/user/accounting-agent/desk-drop/cluster-1-flatiron/map-private.html';
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push('pageerror ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push('console ' + m.text()); });
  await page.goto(file, { waitUntil: 'networkidle' }); await page.waitForTimeout(2500);
  await page.screenshot({ path: out + '/r2-phone-default.png' });
  const sw = await page.evaluate(() => [document.documentElement.scrollWidth, innerWidth]);
  console.log('scrollWidth', sw);
  // Key
  await page.tap('#btnKey'); await page.waitForTimeout(600);
  await page.screenshot({ path: out + '/r2-phone-key.png' });
  await page.tap('#btnKey'); await page.waitForTimeout(400);
  // Find 860
  await page.tap('#btnFind'); await page.waitForTimeout(400);
  await page.fill('#q', '860'); await page.waitForTimeout(600);
  await page.screenshot({ path: out + '/r2-phone-find.png' });
  const first = await page.$('#results div');
  if (first) { await first.tap(); await page.waitForTimeout(1500); }
  await page.screenshot({ path: out + '/r2-phone-popup-860.png' });
  const pop = await page.evaluate(() => { const p = document.querySelector('.leaflet-popup'); if (!p) return null; const r = p.getBoundingClientRect(); const c = document.querySelector('.leaflet-popup-content'); return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, text: c ? c.innerText.slice(0, 600) : '' }; });
  console.log('popup', JSON.stringify(pop));
  // walk session options
  const opts = await page.evaluate(() => [...document.querySelectorAll('#sess option')].map(o => o.value + '|' + o.textContent));
  console.log('sess options', opts.join(' / '));
  await page.tap('#btnFind'); await page.waitForTimeout(300);
  if (opts.length > 1) { await page.selectOption('#sess', opts[1].split('|')[0]); await page.waitForTimeout(1500); }
  const panelOpen = await page.evaluate(() => document.querySelector('#panel').className);
  console.log('panel class', panelOpen);
  await page.screenshot({ path: out + '/r2-phone-walk1.png' });
  console.log('errors', errs.join(' || ') || 'none');
  await browser.close();
})();
