// Reviewer swap test: fill the tent card in the Chrome panel using ONLY the box names in USAGE-GUIDE.md section 2.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const OUT = __dirname; const TPL = path.resolve(OUT, '../../../templates/tent-card/tent-card.html');
const log = []; let actions = 0; const act = (what) => { actions++; log.push(`${actions}. ${what}`); };
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true }); const p = await ctx.newPage();
  const errs = []; p.on('pageerror', e => errs.push(String(e)));
  p.on('dialog', d => { log.push('DIALOG: ' + d.message().slice(0, 120)); d.dismiss(); });
  await p.goto('file://' + TPL); await p.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready); act('open tent-card.html in Chrome');
  await p.screenshot({ path: path.join(OUT, 'r-1-opened.png') });
  // find a box by the label text the guide prints in bold
  async function box(labelText) {
    const lab = p.locator('label.dd-field').filter({ has: p.locator('span', { hasText: labelText }) }).first();
    if (await lab.count() === 0) throw new Error('No box labelled: ' + labelText);
    return lab.locator('input, textarea, select').first();
  }
  const fill = async (label, v) => { const el = await box(label); const tag = await el.evaluate(e => e.tagName); if (tag === 'SELECT') await el.selectOption(v); else await el.fill(v); act(`"${label}" <- ${v.length > 50 ? v.slice(0, 50) + '...' : v}`); };
  const D = {
    name: 'SAMPLE Kettle & Fig', product: 'SAMPLE Fig and Sea Salt Oat Bars', story: 'SAMPLE A Harlem baker and her brother make oat bars in a shared kitchen on 116th Street. They wanted a lunch-bag snack that keeps for two months without a fridge.',
    allergen: 'SAMPLE Contains: wheat, oats processed with wheat, milk, eggs, soy, almonds, cashews and sesame. Made with butter from cows not treated with rBST.',
    may: 'SAMPLE May contain peanuts, other tree nuts and fish. Produced in a facility that also handles crustacean shellfish.',
    ret: 'SAMPLE Union Market, 240 East Houston Street', code: 'SAMPLEFIG20', site: 'kettlefig.example.com', qr: 'https://example.com/s/SAMPLE-O-004-CMP-003', office: 'SAMPLE-O-004', camp: 'SAMPLE-CMP-003' };
  await fill('Brand name', D.name); await fill('Product (optional)', D.product); await fill('Two sentences: who makes it and why', D.story);
  await fill('Where the package declares allergens', 'contains_statement');
  await fill('Allergen statement, exactly as on the package', D.allergen);
  await fill('"May contain" or facility line, exactly as on the package', D.may);
  await fill('Retailer and street', D.ret); await fill('Discount code', D.code); await fill('Site for the code', D.site);
  await fill('QR link for THIS office', D.qr); await fill('Office ID', D.office); await fill('Campaign ID', D.camp);
  const cb = p.locator('input[data-act="confirm"]'); await cb.check(); act('tick "I read the allergen text against the package itself, word for word"');
  await p.waitForTimeout(400);
  const status = await p.evaluate(() => (document.querySelector('.dd-status') || document.querySelector('[class*=status]') || {}).innerText || '');
  log.push('STATUS BOX: ' + status.replace(/\s+/g, ' ').slice(0, 400));
  await p.screenshot({ path: path.join(OUT, 'r-2-filled.png') });
  const [dl] = await Promise.all([p.waitForEvent('download'), p.click('button[data-act="save"]')]); const saved = path.join(OUT, 'r-saved.json'); await dl.saveAs(saved); act('press Save as JSON');
  // next office: Load JSON, change QR link and Office ID, tick box again
  await p.reload(); await p.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  await p.setInputFiles('input[data-act="load"]', saved); act('press Load JSON (next office)'); await p.waitForTimeout(500);
  const ticked = await cb.isChecked(); log.push('allergen box ticked after load: ' + ticked);
  await fill('QR link for THIS office', 'https://example.com/s/SAMPLE-O-005-CMP-003'); await fill('Office ID', 'SAMPLE-O-005'); await cb.check(); act('tick allergen box again');
  await p.waitForTimeout(400);
  const st2 = await p.evaluate(() => window.__DD_STATUS__); log.push('STATUS 2: errors=' + JSON.stringify(st2.errors) + ' warnings=' + JSON.stringify(st2.warnings) + ' sample=' + st2.sample);
  const qrShown = await p.evaluate(() => document.querySelector('.face.front .qr-url').innerText); log.push('QR text on card: ' + qrShown);
  await p.screenshot({ path: path.join(OUT, 'r-3-next-office.png') });
  const fit = await p.evaluate(() => document.querySelector('.dd-sheet').dataset.fit); log.push('fit: ' + fit);
  log.push('page errors: ' + JSON.stringify(errs));
  fs.writeFileSync(path.join(OUT, 'r-log.txt'), log.join('\n') + '\n'); console.log(log.join('\n')); await b.close();
})().catch(e => { console.error('FAILED', e.message); fs.writeFileSync(path.join(OUT, 'r-log.txt'), log.join('\n') + '\nFAILED ' + e.message); process.exit(1); });
