// R3 reviewer script: render a tent card JSON in the sandbox template, measure every allergen
// paragraph's computed style on both faces, element positions vs trim, and save face PNGs.
// Usage: node measure-card.js <data.json> <outstem> [dpi]
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const SB = path.resolve(__dirname, '../sb/desk-drop-identity');
const [dataPath, outStem, dpiArg] = process.argv.slice(2);
const dpi = Number(dpiArg || 300);
(async () => {
  const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
  (function walk(v, p, k) {
    if (Array.isArray(v)) return v.forEach((x, i) => walk(x, v, i));
    if (v && typeof v === 'object') return Object.keys(v).forEach((kk) => walk(v[kk], v, kk));
    if (typeof v === 'string' && /\.(svg|png|jpe?g)$/i.test(v) && !/^file:/.test(v)) p[k] = 'file://' + path.resolve(path.dirname(dataPath), v);
  })(data, null, null);
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ deviceScaleFactor: dpi / 96, viewport: { width: 1400, height: 1200 } });
  const page = await ctx.newPage();
  await page.addInitScript((d) => { window.__DD_DATA__ = d; window.__DD_HEADLESS__ = true; window.__DD_MODE__ = 'home'; }, data);
  await page.goto('file://' + SB + '/templates/tent-card/tent-card.html');
  await page.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready, null, { timeout: 30000 });
  await page.evaluate(() => document.fonts.ready);
  await page.emulateMedia({ media: 'print' });
  const res = await page.evaluate(() => {
    const out = { status: window.__DD_STATUS__, faces: [] };
    const sheet = document.querySelector('.dd-sheet');
    out.fit = sheet && sheet.dataset.fit ? JSON.parse(sheet.dataset.fit) : null;
    document.querySelectorAll('.dd-sheet .face').forEach((f) => {
      const fr = f.getBoundingClientRect();
      const face = { cls: f.className, w_in: fr.width / 96, h_in: fr.height / 96, allergen: [], other: {} };
      f.querySelectorAll('.allergen-text').forEach((a) => {
        const cs = getComputedStyle(a);
        face.allergen.push({ text: a.textContent.slice(0, 60), pt: parseFloat(cs.fontSize) * 0.75, weight: cs.fontWeight, color: cs.color, family: cs.fontFamily.split(',')[0] });
      });
      const name = f.querySelector('.name, .brand-name, .dd-brand-name');
      if (name) { const cs = getComputedStyle(name); const r = name.getBoundingClientRect(); face.other.name = { pt: parseFloat(cs.fontSize) * 0.75, px_css: parseFloat(cs.fontSize), stretch: cs.fontStretch, text: name.textContent, h_in: r.height / 96 }; }
      // every text-bearing element: smallest font size, and items within 0.25 in of trim
      let minPt = 99, minEl = '';
      const nearTrim = [];
      f.querySelectorAll('*').forEach((el) => {
        if (!el.childNodes.length) return;
        const hasText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
        if (!hasText) return;
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') return;
        const r = el.getBoundingClientRect();
        if (!r.width) return;
        const pt = parseFloat(cs.fontSize) * 0.75;
        if (pt < minPt) { minPt = pt; minEl = (el.className || el.tagName) + ': ' + el.textContent.trim().slice(0, 40); }
        const d = Math.min(r.left - fr.left, fr.right - r.right, r.top - fr.top, fr.bottom - r.bottom) / 96;
        if (d < 0.249) nearTrim.push({ el: (el.className || el.tagName), text: el.textContent.trim().slice(0, 40), d_in: +d.toFixed(3), pt });
      });
      face.other.min_text_pt = +minPt.toFixed(2); face.other.min_text_el = minEl; face.other.near_trim = nearTrim;
      out.faces.push(face);
    });
    return out;
  });
  fs.writeFileSync(outStem + '.json', JSON.stringify(res, null, 1));
  const faces = await page.$$('.dd-sheet .face');
  for (let i = 0; i < faces.length; i++) await faces[i].screenshot({ path: `${outStem}-face${i + 1}.png` });
  const sheet = await page.$('.dd-sheet');
  await ctx.close();
  // sheet at 100 dpi for an overview
  const ctx2 = await browser.newContext({ deviceScaleFactor: 100 / 96, viewport: { width: 1400, height: 1200 } });
  const p2 = await ctx2.newPage();
  await p2.addInitScript((d) => { window.__DD_DATA__ = d; window.__DD_HEADLESS__ = true; window.__DD_MODE__ = 'home'; }, data);
  await p2.goto('file://' + SB + '/templates/tent-card/tent-card.html');
  await p2.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready, null, { timeout: 30000 });
  await p2.evaluate(() => document.fonts.ready);
  await p2.emulateMedia({ media: 'print' });
  await p2.pdf({ path: outStem + '.pdf', preferCSSPageSize: true, printBackground: true });
  await browser.close();
  const s = res.status;
  console.log(JSON.stringify({ errors: s.errors, warnings: s.warnings, fit: res.fit, faces: res.faces.map((f) => ({ cls: f.cls, allergen: f.allergen.map((a) => `${a.pt.toFixed(2)}pt w${a.weight} ${a.color}`), name: f.other.name && `${f.other.name.pt.toFixed(1)}pt ${f.other.name.stretch}`, min_text_pt: f.other.min_text_pt, min_el: f.other.min_text_el, near_trim: f.other.near_trim })) }, null, 1));
})().catch((e) => { console.error(e); process.exit(1); });
