#!/usr/bin/env node
/*
  swap-test.js: the brief's test. "Swap one brand's details into the card using only the guide;
  if that takes over ten minutes, fix the guide or the template."

  1. Reads USAGE-GUIDE.md section 2 and collects every box it names in bold.
  2. Opens the tent card in Chrome and checks each named box exists in the panel (so the guide
     and the template cannot drift apart).
  3. Follows the steps in order with a NEW brand (SAMPLE data): an ingredient-list-only drink
     with a code-only buy path, the harder allergen path. Ticks the allergen check box, reads the
     status, saves the JSON, loads it again for a second office and changes only the QR link and
     the office ID, as the guide says.
  4. Estimates person time with a stated model (below) and fails if the first card exceeds 10 min.
  The same label check runs for the documents (guide sections 8 to 12).

    node tests/guide-walkthrough/swap-test.js
*/
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '../..');
const OUT = __dirname;
const guide = fs.readFileSync(path.join(ROOT, 'USAGE-GUIDE.md'), 'utf8');
const section = (n) => { const m = new RegExp(`\\n## ${n}\\. [\\s\\S]*?(?=\\n## \\d+\\. |$)`).exec(guide); return m ? m[0] : ''; };
const bolds = (txt) => [...txt.matchAll(/\*\*([^*]+)\*\*/g)].map((m) => m[1].trim()).filter((b) => !/[.:]$/.test(b));
// Words in bold that are Chrome, Gmail or status text, not panel boxes
const NOT_BOXES = /^(Ready to print|Background graphics|Save as PDF|HOLD|go|Print|Print or save as PDF|Save as JSON|Load JSON|Remove|Choose picture|Add a row|See all settings|General|Signature|Create new|Save changes|the package itself|`avatar-cobalt-1024\.png`|`avatar-cobalt-400\.png`|No claims anywhere\.?|Measurement words stay exact\.?|Yellow means unfinished\.?|If something goes wrong|like this)$/i;

// SAMPLE brand for the swap. Typed fields are what a person types from the package; pasted
// fields come from the brand's email or the paid-brands row.
const CARD = [
  ['Brand name', 'SAMPLE Northgate Teas', 'paste'],
  ['Product (optional)', 'SAMPLE Peach Oolong, 12 oz can', 'paste'],
  ['Two sentences: who makes it and why', 'SAMPLE Two sisters in Sunset Park brew unsweetened oolong in small batches. They wanted a canned tea they would drink every afternoon at work.', 'paste'],
  ['Where the package declares allergens', 'ingredient_list', 'select'],
  ['Allergen statement, exactly as on the package', 'SAMPLE INGREDIENTS: BREWED OOLONG TEA (FILTERED WATER, OOLONG TEA LEAVES), PEACH JUICE CONCENTRATE, NATURAL FLAVOR, CITRIC ACID.', 'type'],
  ['"May contain" or facility line, exactly as on the package', 'SAMPLE PRODUCED IN A FACILITY THAT ALSO HANDLES MILK AND SOY.', 'type'],
  ['Discount code', 'SAMPLETEA10', 'paste'],
  ['Site for the code', 'example.com', 'paste'],
  ['QR link for THIS office', 'https://example.com/s/SAMPLE-O-004', 'paste'],
  ['Office ID', 'SAMPLE-O-004', 'type'],
  ['Campaign ID', 'SAMPLE-CMP-003', 'type'],
];
const CONFIRMS = ['I read the allergen text against the package itself, word for word', 'I read the brand name, product and two sentences for health and sales claims'];
const tickAll = async (page) => { for (const cb of await page.$$('input[data-act="confirm"]')) await cb.check(); };

// Person-time model (seconds). Stated, not measured: there is no person in this test.
const M = { open: 60, readWpm: 200, typeCps: 3.3, paste: 8, select: 6, readbackPerWord: 1, qrScan: 20, status: 15, save: 10, printDialog: 60, load: 15, tick: 3 };

(async () => {
  const { chromium } = require('playwright');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 }, acceptDownloads: true });
  const fails = [];
  const log = [];

  // ---- 1 and 2: every box the guide names exists ----
  const checkLabels = async (file, secs) => {
    await page.goto('file://' + path.join(ROOT, file));
    await page.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
    await page.evaluate(() => document.querySelectorAll('details.dd-row').forEach((d) => { d.open = true; }));
    const panelText = await page.$eval('.dd-panel', (el) => el.innerText);
    const names = [...new Set(secs.flatMap((n) => bolds(section(n))))].filter((b) => !NOT_BOXES.test(b));
    const missing = names.filter((b) => !panelText.includes(b.replace(/`/g, '')));
    log.push(`${file}: guide sections ${secs.join(', ')} name ${names.length} boxes or buttons; missing in the panel: ${missing.length ? missing.join(' | ') : 'none'}`);
    if (missing.length) fails.push(`${file}: the guide names boxes that do not exist: ${missing.join(' | ')}`);
  };
  await checkLabels('templates/tent-card/tent-card.html', [2, 19]);   // 19: two flavors (v1.3)
  await checkLabels('templates/discovery-one-pager/discovery-one-pager.html', [8]);
  await checkLabels('templates/office-one-pager/office-one-pager.html', [9]);
  await checkLabels('templates/brand-one-pager/brand-one-pager.html', [10]);
  await checkLabels('templates/proposal/proposal.html', [11]);
  await checkLabels('templates/report/report.html', [12]);
  const s2 = section(2);
  const guideBoxes = bolds(s2).filter((b) => !NOT_BOXES.test(b));
  for (const [label] of CARD) if (!guideBoxes.some((g) => g === label)) fails.push(`The swap needs the box "${label}" but guide section 2 does not name it.`);

  // ---- 3: follow section 2 with the new brand ----
  await page.goto('file://' + path.join(ROOT, 'templates/tent-card/tent-card.html'));
  await page.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  await page.screenshot({ path: path.join(OUT, 'swap-1-opened.png') });
  const status = async () => (await page.$eval('.dd-panel-status', (el) => el.innerText)).trim().replace(/\n+/g, ' | ');
  let t = M.open + (s2.split(/\s+/).length / M.readWpm) * 60;
  const parts = [`open the file ${M.open}s`, `read section 2 (${s2.split(/\s+/).length} words) ${Math.round((s2.split(/\s+/).length / M.readWpm) * 60)}s`];
  let typed = 0, pasted = 0;
  for (const [label, value, how] of CARD) {
    const box = page.locator('label.dd-field', { hasText: label }).locator('input, textarea, select').first();
    if (how === 'select') { await box.selectOption(value); t += M.select; continue; }
    await box.fill(value);
    if (how === 'type') { t += value.length / M.typeCps; typed += value.length; } else { t += M.paste; pasted++; }
  }
  const allergenWords = (CARD[4][1] + ' ' + CARD[5][1]).split(/\s+/).length;
  t += allergenWords * M.readbackPerWord + M.qrScan + M.status;
  parts.push(`type ${typed} characters from the package and IDs ${Math.round(typed / M.typeCps)}s`, `paste ${pasted} fields ${pasted * M.paste}s`, `choose the allergen option ${M.select}s`, `read back ${allergenWords} allergen words ${allergenWords * M.readbackPerWord}s`, `scan the QR ${M.qrScan}s`, `read the status ${M.status}s`);
  await page.waitForTimeout(300);
  log.push('After filling: ' + await status());
  await page.screenshot({ path: path.join(OUT, 'swap-2-filled.png') });
  // both tick boxes (v1.4): the allergen read-back, and reading the sentences for claims
  const claimWords = (CARD[0][1] + ' ' + CARD[1][1] + ' ' + CARD[2][1]).split(/\s+/).length;
  for (const c of CONFIRMS) if (!(await page.$eval('.dd-panel', (el) => el.innerText)).includes(c)) fails.push(`tick box missing: ${c}`);
  await tickAll(page);
  t += CONFIRMS.length * M.tick + (claimWords / M.readWpm) * 60;
  parts.push(`tick ${CONFIRMS.length} boxes ${CONFIRMS.length * M.tick}s`, `read the ${claimWords} words of name, product and sentences for claims ${Math.round((claimWords / M.readWpm) * 60)}s`);
  await page.waitForTimeout(200);
  const ready = await status();
  log.push('After the allergen check box: ' + ready);
  if (/Fix before printing|Still to fill in|Last step/.test(ready)) fails.push('First card not ready after following the guide: ' + ready);
  await page.screenshot({ path: path.join(OUT, 'swap-3-ready.png') });
  // save, as step 8 says
  const [dl] = await Promise.all([page.waitForEvent('download'), page.click('button[data-act="save"]')]);
  const saved = path.join(OUT, 'swap-saved-SAMPLE.json');
  await dl.saveAs(saved);
  t += M.save + M.printDialog;
  parts.push(`save JSON ${M.save}s`, `print dialog ${M.printDialog}s`);
  await page.emulateMedia({ media: 'print' });
  await page.pdf({ path: path.join(OUT, 'swap-4-printed-SAMPLE.pdf'), preferCSSPageSize: true, printBackground: true });
  await page.emulateMedia({ media: 'screen' });
  const first = Math.round(t);

  // ---- next office: Load JSON, change only the QR link and the office ID ----
  await page.goto('file://' + path.join(ROOT, 'templates/tent-card/tent-card.html'));
  await page.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  await page.setInputFiles('input[data-act="load"]', saved);
  await page.waitForTimeout(400);
  await page.locator('label.dd-field', { hasText: 'QR link for THIS office' }).locator('input').fill('https://example.com/s/SAMPLE-O-005');
  await page.locator('label.dd-field', { hasText: 'Office ID' }).locator('input').fill('SAMPLE-O-005');
  await tickAll(page);
  await page.waitForTimeout(300);
  const second = await status();
  log.push('Second office, after Load JSON and two changes: ' + second);
  if (/Fix before printing|Still to fill in|Last step/.test(second)) fails.push('Second card not ready: ' + second);
  const cardId = await page.$eval('.face.front .card-id', (el) => el.innerText);
  if (!/SAMPLE-O-005/.test(cardId)) fails.push('Second card does not carry the new office ID: ' + cardId);
  await page.screenshot({ path: path.join(OUT, 'swap-5-next-office.png') });
  const secondT = M.load + 8 + 12 / M.typeCps + 2 * M.tick + M.qrScan + M.status + M.printDialog;

  // ---- v1.4 (review round 3, R3-05): the same card with REAL values (no SAMPLE prefix) must
  // say "Ready to print" once both boxes are ticked, even with a permanent note on it ----
  await page.goto('file://' + path.join(ROOT, 'templates/tent-card/tent-card.html'));
  await page.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  for (const [label, value, how] of CARD) {
    const v = String(value).replace(/^SAMPLE[ -]?/, '');
    const box = page.locator('label.dd-field', { hasText: label }).locator('input, textarea, select').first();
    if (how === 'select') await box.selectOption(v); else await box.fill(v);
  }
  // the reviewer's case: a long ALL-CAPS ingredient list, so the product line is left off (a permanent note)
  await page.locator('label.dd-field', { hasText: 'Allergen statement, exactly as on the package' }).locator('textarea, input').first()
    .fill('INGREDIENTS: BREWED OOLONG TEA (FILTERED WATER, OOLONG TEA LEAVES), PEACH JUICE CONCENTRATE, CANE SUGAR, NATURAL FLAVOR, CITRIC ACID, ASCORBIC ACID (VITAMIN C), SODIUM CITRATE, SOY LECITHIN, MILK PROTEIN, ALMOND EXTRACT.');
  await page.waitForTimeout(300);
  const before = await status();
  await tickAll(page);
  await page.waitForTimeout(300);
  const real = await status();
  log.push('Real (non-SAMPLE) values, before the ticks: ' + before);
  log.push('Real (non-SAMPLE) values, both boxes ticked: ' + real);
  if (!/^Ready to print/.test(real)) fails.push('A correct card with real values does not say "Ready to print" first: ' + real);
  if (/Check:/.test(real) && !/Read these notes first/.test(real)) fails.push('Notes on a ready card are not introduced with "Read these notes first": ' + real);
  if (!/Last step/.test(before)) fails.push('Before the ticks, the status should name the last step (tick the boxes): ' + before);
  await page.screenshot({ path: path.join(OUT, 'swap-6-real-values-ready.png') });
  await browser.close();

  console.log(log.join('\n'));
  console.log(`Person-time estimate, first card: ${Math.floor(first / 60)} min ${first % 60} s (${parts.join('; ')}).`);
  console.log(`Person-time estimate, each next office: ${Math.round(secondT)} s.`);
  if (first > 600) fails.push(`First card estimate ${first} s is over 10 minutes.`);
  fs.writeFileSync(path.join(OUT, 'swap-result.json'), JSON.stringify({ date: new Date().toISOString().slice(0, 10), first_card_seconds: first, next_card_seconds: Math.round(secondT), model: M, parts, log, fails }, null, 2));
  if (fails.length) { console.log('FAIL:\n  ' + fails.join('\n  ')); process.exit(1); }
  console.log('PASS: the guide alone gets a new brand onto a ready card in under 10 minutes; every box the guide names exists.');
})().catch((e) => { console.error(e); process.exit(1); });
