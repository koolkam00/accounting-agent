#!/usr/bin/env node
/*
  walkthrough.js: the "stranger swaps one brand into the card using only the guide" test.
  Follows USAGE-GUIDE.md section 2 step by step through the on-screen panel, exactly as a
  person would (typing into the labelled boxes, ticking the check box, reading the status),
  and screenshots each stage. The brand typed in is SAMPLE data.

    node tests/guide-walkthrough/walkthrough.js
*/
const path = require('path');
const ROOT = path.resolve(__dirname, '../..');
const OUT = __dirname;
const BRAND = {
  'Brand name': 'SAMPLE Hilltop',
  'Product (optional)': 'SAMPLE Honey Oat Bar',
  'Two sentences: who makes it and why': 'SAMPLE A Bronx couple bakes these bars in small batches. They started because the oat bars they found were too sweet for them.',
  'Allergen statement, exactly as on the package': 'SAMPLE CONTAINS: OATS (WHEAT), MILK, ALMONDS.',
  '"May contain" or facility line, exactly as on the package': 'SAMPLE MADE IN A FACILITY THAT ALSO PROCESSES PEANUTS, SOY AND SESAME.',
  'Retailer and street': 'SAMPLE Retailer, 123 Example Street',
  'Discount code': '',
  'Site for the code': '',
  'QR link for THIS office': 'https://example.com/s/SAMPLE-O-002',
  'Short link printed under the QR (optional)': '',
  'Office ID': 'SAMPLE-O-002',
  'Campaign ID': 'SAMPLE-CMP-002',
};
(async () => {
  const { chromium } = require('playwright');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
  const log = [];
  let actions = 0;
  await page.goto('file://' + path.join(ROOT, 'templates/tent-card/tent-card.html'));
  await page.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  await page.screenshot({ path: path.join(OUT, '1-opened.png') });
  const status = async () => (await page.$eval('.dd-panel-status', el => el.innerText)).trim();
  log.push('Opened. Status: ' + (await status()).replace(/\n/g, ' | '));
  for (const [label, value] of Object.entries(BRAND)) {
    const field = page.locator('label.dd-field', { hasText: label }).locator('input, textarea').first();
    await field.fill(value); actions++;
  }
  await page.waitForTimeout(400);
  log.push('After typing: ' + (await status()).replace(/\n/g, ' | '));
  await page.screenshot({ path: path.join(OUT, '2-filled.png') });
  for (const cb of await page.$$('input[data-act="confirm"]')) { await cb.check(); actions++; }   // v1.4: two tick boxes
  await page.waitForTimeout(200);
  const finalStatus = await status();
  log.push('After ticking the allergen check: ' + finalStatus.replace(/\n/g, ' | '));
  await page.screenshot({ path: path.join(OUT, '3-ready.png') });
  // what Print would produce
  await page.emulateMedia({ media: 'print' });
  await page.pdf({ path: path.join(OUT, '4-printed-SAMPLE.pdf'), preferCSSPageSize: true, printBackground: true });
  log.push(`Typed into ${Object.keys(BRAND).length} boxes (${actions} actions including the check box).`);
  console.log(log.join('\n'));
  await browser.close();
  if (/Fix before printing|Still to fill in|Last step/.test(finalStatus)) { console.log('FAIL: the card is not ready after following the guide.'); process.exit(1); }
  console.log('PASS: ready to print after following the guide (SAMPLE banner expected for test data).');
})().catch(e => { console.error(e); process.exit(1); });
