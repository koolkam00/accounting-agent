// R3 reviewer swap test: drive the tent card panel in Chrome using ONLY the box names that
// USAGE-GUIDE.md section 2 prints in bold. Counts actions; screenshots the result.
const fs = require('fs'), path = require('path'), { chromium } = require('playwright');
const SB = path.resolve(__dirname, '../sb/desk-drop-identity');
const OUT = path.resolve(__dirname, '../swap-nosample'); fs.mkdirSync(OUT, { recursive: true });
const guide = fs.readFileSync(path.join(SB, 'USAGE-GUIDE.md'), 'utf8');
const sec2 = guide.split('## 2.')[1].split('\n## 3.')[0];
const bold = [...new Set([...sec2.matchAll(/\*\*([^*]+)\*\*/g)].map((m) => m[1]))];
const words = sec2.split(/\s+/).filter(Boolean).length;
const log = [];
let actions = 0;
const act = (s) => { actions++; log.push(`${actions}. ${s}`); };
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
  const pg = await ctx.newPage();
  const errs = []; pg.on('pageerror', (e) => errs.push(String(e)));
  await pg.goto('file://' + SB + '/templates/tent-card/tent-card.html');
  act('open tent-card.html in Chrome');
  await pg.waitForFunction(() => window.__DD_STATUS__, null, { timeout: 30000 });
  const panelText = await pg.evaluate(() => document.body.innerText);
  const missing = bold.filter((n) => !panelText.includes(n.replace(/^"|"$/g, '')) );
  log.push('bold names in section 2: ' + bold.length + '; not found in page text: ' + JSON.stringify(missing));
  const fieldByLabel = async (label) => {
    const h = await pg.evaluateHandle((label) => {
      const f = [...document.querySelectorAll('label.dd-field')].find((l) => l.querySelector('span') && l.querySelector('span').textContent.replace(/\s*required\s*$/, '').trim() === label);
      return f ? f.querySelector('input,textarea,select') : null;
    }, label);
    const el = h.asElement(); if (!el) throw new Error('no box named ' + label); return el;
  };
  const fill = async (label, v) => { const el = await fieldByLabel(label); await el.fill(v); act(`type into "${label}" (${v.split(/\s+/).length} words)`); };
  await fill('Brand name', 'Hollow Pine');
  await fill('Product (optional)', 'Black Pepper Turkey Stick');
  await fill('Two sentences: who makes it and why', 'A butcher and a chef in the Bronx make these from turkey raised in upstate New York. They wanted a meat stick that tastes like real food.');
  const src = await fieldByLabel('Where the package declares allergens'); await src.selectOption('contains_statement'); act('choose "Where the package declares allergens": Contains statement');
  await fill('Allergen statement, exactly as on the package', 'CONTAINS: MILK, SOY, WHEAT, SESAME, EGG AND MUSTARD (NOT A MAJOR ALLERGEN, LISTED BY THE MAKER) FROM THE SPICE BLEND AND THE CASING GLAZE USED ON EVERY STICK.');
  await fill('"May contain" or facility line, exactly as on the package', 'PRODUCED IN A FACILITY THAT ALSO HANDLES PEANUTS, TREE NUTS, FISH AND SHELLFISH.');
  await fill('Retailer and street', 'Union Market, 240 E Houston Street');
  await fill('Discount code', 'PINE15');
  await fill('Site for the code', 'hollowpine.example.com');
  await fill('QR link for THIS office', 'https://example.com/s/O-004');
  await fill('Office ID', 'O-004');
  await fill('Campaign ID', 'CMP-003');
  const tick = await pg.$('input[data-act="confirm"]');
  if (tick) { await tick.check(); act('tick the allergen read-back box'); }
  await pg.waitForTimeout(1500);
  const status = await pg.evaluate(() => { const s = document.querySelector('.dd-status, [class*=status]'); return s ? s.innerText : ''; });
  act('read the status box');
  const st = await pg.evaluate(() => window.__DD_STATUS__);
  await pg.screenshot({ path: path.join(OUT, 'swap-filled.png'), fullPage: false });
  // Save as JSON
  const btnSave = await pg.$('text=Save as JSON');
  let saved = null;
  if (btnSave) { const [dl] = await Promise.all([pg.waitForEvent('download', { timeout: 5000 }).catch(() => null), btnSave.click()]); act('press Save as JSON'); if (dl) { saved = path.join(OUT, 'swap-saved.json'); await dl.saveAs(saved); } }
  // next office: Load JSON, change QR link + Office ID, re-tick
  let next = {};
  if (saved) {
    const inp = await pg.$('input[data-act="load"]'); await inp.setInputFiles(saved); act('next office: Load JSON');
    await pg.waitForTimeout(800);
    next.tick_after_load = tick ? await pg.$eval('input[data-act="confirm"]', (e) => e.checked) : null;
    await fill('QR link for THIS office', 'https://example.com/s/O-005');
    await fill('Office ID', 'O-005');
    if (tick) { await pg.check('input[data-act="confirm"]'); act('re-tick the allergen box'); }
    await pg.waitForTimeout(800);
    next.status = await pg.evaluate(() => window.__DD_STATUS__);
    await pg.screenshot({ path: path.join(OUT, 'swap-next-office.png') });
  }
  const res = { guide_section2_words: words, bold_names: bold, missing, actions, log, status_text: status, status: { errors: st.errors, warnings: st.warnings, placeholders: st.placeholders, sample: st.sample }, next, page_errors: errs };
  fs.writeFileSync(path.join(OUT, 'swap-result.json'), JSON.stringify(res, null, 1));
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})().catch((e) => { console.error(e); process.exit(1); });
