// Reviewer round 2: the swap test, driving the Chrome panel using only the box names printed in bold in USAGE-GUIDE.md section 2.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const root = path.resolve(process.argv[2]); const out = path.resolve(process.argv[3]);
  const log = []; let actions = 0; const act = (s) => { actions++; log.push(`${actions}. ${s}`); };
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1500, height: 1100 }, acceptDownloads: true }); const p = await ctx.newPage();
  await p.goto('file://' + root + '/templates/tent-card/tent-card.html'); await p.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  act('open templates/tent-card/tent-card.html in Chrome (guide step 1)');
  const box = async (label) => {
    const h = await p.evaluateHandle((label) => { const l = [...document.querySelectorAll('label.dd-field')].find(x => x.querySelector('span').innerText.replace(/required$/, '').trim() === label); return l ? l.querySelector('input,textarea,select') : null; }, label);
    const el = h.asElement(); if (!el) throw new Error('Box not found by the guide name: ' + label); return el;
  };
  const fill = async (label, v) => { const el = await box(label); const tag = await el.evaluate(e => e.tagName); if (tag === 'SELECT') await el.selectOption(v); else { await el.fill(v); await el.dispatchEvent('input'); } act(`${label} = ${v.length > 60 ? v.slice(0, 57) + '...' : v}`); };
  const brand = {
    'Brand name': 'SAMPLE Oddfellow Pretzel',
    'Product (optional)': 'SAMPLE Everything Bagel Pretzel Thins',
    'Two sentences: who makes it and why': 'SAMPLE A former deli baker in Sunnyside makes these in a shared kitchen. He wanted the crunch of a pretzel with everything-bagel seasoning.',
  };
  for (const [k, v] of Object.entries(brand)) await fill(k, v);
  await fill('Where the package declares allergens', 'contains_statement');
  await fill('Allergen statement, exactly as on the package', 'SAMPLE CONTAINS: WHEAT, SESAME, SOY, MILK. PRODUCED IN A FACILITY THAT ALSO HANDLES PEANUTS, TREE NUTS (ALMONDS, CASHEWS), EGGS AND FISH.');
  await fill('"May contain" or facility line, exactly as on the package', 'SAMPLE MAY CONTAIN TRACES OF MUSTARD AND OTHER TREE NUTS.');
  await (await p.$('input[data-act="confirm"]')).check(); act('tick "I read the allergen text against the package itself, word for word"');
  await fill('Retailer and street', 'SAMPLE Eataly NYC Flatiron, 200 Fifth Avenue');
  await fill('Discount code', 'SAMPLEPRETZEL10');
  await fill('Site for the code', 'oddfellow.example.com');
  await fill('QR link for THIS office', 'https://example.com/s/SAMPLE-O-007');
  await fill('Office ID', 'SAMPLE-O-007');
  await fill('Campaign ID', 'SAMPLE-CMP-004');
  await p.waitForTimeout(800);
  const status = await p.$eval('.dd-panel-status', e => e.innerText); act('read the status box (guide step 7)');
  await p.screenshot({ path: out + '/swap-filled.png' });
  const [dl] = await Promise.all([p.waitForEvent('download'), p.click('button[data-act="save"]')]); await dl.saveAs(out + '/swap-saved.json'); act('Save as JSON (guide step 8)');
  act('Print (guide step 9: printer, Letter, Scale 100, Background graphics on)');
  // next office: Load JSON, change QR link and Office ID, re-tick
  const p2 = await ctx.newPage(); await p2.goto('file://' + root + '/templates/tent-card/tent-card.html'); await p2.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  let a2 = 0;
  await (await p2.$('input[data-act="load"]')).setInputFiles(out + '/swap-saved.json'); a2++; await p2.waitForTimeout(600);
  const confirmAfterLoad = await p2.$eval('input[data-act="confirm"]', e => e.checked);
  const st = await p2.evaluate(() => window.__DD_STATUS__);
  console.log(JSON.stringify({ actions, log, status, confirm_after_load: confirmAfterLoad, after_load_errors: st.errors, after_load_placeholders: st.placeholders }, null, 1));
  fs.writeFileSync(out + '/swap-log.txt', log.join('\n') + '\n\nStatus box:\n' + status + '\n');
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
