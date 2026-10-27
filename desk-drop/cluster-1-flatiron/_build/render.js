// Renders: node _build/render.js <cluster folder>
// 1) public-map.svg -> public-map.png  2) _build/out/route_sheet.html -> route-private.png
// 3) QA screenshots of map-private.html at phone and desktop width into _build/out/qa/
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
(async () => {
  const dir = require('path').resolve(process.argv[2] || require('path').join(__dirname, '..'));  // review round 2: a relative path works too
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
  // brand maps (review round 1, R1-08): every brand-maps/*.svg to a PNG at twice the size
  // review round 3 (R3-02): the label QA maps in _build/out/qa/brand-map/ render the same way
  for (const bdir of [path.join(dir, 'brand-maps'), path.join(qa, 'brand-map')]) {
  if (fs.existsSync(bdir)) {
    for (const f of fs.readdirSync(bdir).filter(f => f.endsWith('.svg'))) {
      const bs = fs.readFileSync(path.join(bdir, f), 'utf8');
      const [, bw, bh] = bs.match(/viewBox="0 0 (\d+) (\d+)"/).map(Number);
      const bp = await browser.newPage({ viewport: { width: bw, height: bh }, deviceScaleFactor: 2 });
      await bp.setContent(`<!doctype html><html><body style="margin:0">${bs}</body></html>`);
      await bp.evaluate(() => document.fonts.ready); await bp.waitForTimeout(300);
      await bp.screenshot({ path: path.join(bdir, f.replace(/\.svg$/, '.png')), clip: { x: 0, y: 0, width: bw, height: bh } });
      await bp.close();
    }
  }
  }
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
      // review round 1 (R1-07): tall popups at 390 px. Each must sit inside the map, below the bar,
      // clear of the zoom and locate controls, with its heading visible.
      const checks = [];
      for (const [q, file] of [['853 Broadway', 'popup-853-broadway'], ['11 East 26th', 'popup-11-e-26th'], ['41 Madison', 'popup-41-madison'], ['53 West 23rd', 'popup-53-w-23rd']]) {
        await page.goto('file://' + path.join(dir, 'map-private.html'), { waitUntil: 'networkidle' });
        await page.waitForTimeout(1200);
        await page.click('#btnFind'); await page.fill('#q', q); await page.waitForTimeout(400);
        const items = await page.$$('#results div');
        let hit = null;
        for (const it of items) { const t = await it.innerText(); if (t.includes('building')) { hit = it; break; } }
        await (hit || items[0]).click(); await page.waitForTimeout(1800);
        const r = await page.evaluate(() => {
          const w = document.querySelector('.leaflet-popup'); if (!w) return null;
          const b = w.getBoundingClientRect(), h3 = w.querySelector('h3').getBoundingClientRect();
          const bar = document.getElementById('bar').getBoundingClientRect();
          const ctl = [...document.querySelectorAll('.leaflet-top.leaflet-left .leaflet-bar')].map(e => e.getBoundingClientRect());
          const overlap = ctl.some(c => !(c.right <= b.left || c.left >= b.right || c.bottom <= b.top || c.top >= b.bottom));
          const list = w.querySelector('.plist');
          return { top: Math.round(b.top), bottom: Math.round(b.bottom), left: Math.round(b.left), right: Math.round(b.right),
                   heading_visible: h3.top >= bar.bottom && h3.bottom <= innerHeight, overlaps_controls: overlap,
                   inside_view: b.top >= bar.bottom && b.bottom <= innerHeight && b.left >= 0 && b.right <= innerWidth,
                   list_scrolls: list ? list.scrollHeight > list.clientHeight : false, items: w.querySelectorAll('li').length };
        });
        checks.push({ query: q, ...r });
        await page.screenshot({ path: path.join(qa, `private-phone-${file}.png`) });
      }
      fs.writeFileSync(path.join(qa, 'popup_checks.json'), JSON.stringify(checks, null, 1));
      console.log('popup checks', JSON.stringify(checks));
    }
    await page.close();
  }
  await browser.close();
  console.log('rendered; errors:', JSON.stringify(errs));
})();
