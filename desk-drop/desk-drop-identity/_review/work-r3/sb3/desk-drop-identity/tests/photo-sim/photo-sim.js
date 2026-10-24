#!/usr/bin/env node
/*
  photo-sim.js: simulates the two campaign photos to test the tent card (v1.0, 2026-10-23).

    node tests/photo-sim/photo-sim.js <face.png> <out-dir> [label]

  <face.png> must be a front-face render at 300 dpi (render.js --face-png ... --dpi 300).

  Wide pantry photo: a 26 mm-equivalent phone lens about 2.2 m from the shelf sees about
  120 x 90 in. Rendered at 24 px per inch (a 2880 x 2160 image), the 5 in card face is
  about 120 px tall, the size the brief asks us to judge. A second copy at half size
  (card about 60 px tall) stands in for the photo as it appears inside the report.
  Close photo: the same lens at arm's length (60 cm) sees about 32.7 x 24.5 in, so a
  4032 px wide photo carries about 123 px per inch. Copies at 2048 px and 1280 px wide
  stand in for messaging-app compression.
  Camera effects added with ImageMagick: slight perspective squash (card leans back),
  blur, sensor noise, uneven light and JPEG compression.
  The packaging around the card is invented shapes and generic words only.
*/
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const [facePng, outDir, label = 'card'] = process.argv.slice(2);
if (!facePng || !outDir) { console.error('usage: node photo-sim.js <face.png> <out-dir> [label]'); process.exit(1); }
fs.mkdirSync(outDir, { recursive: true });
const faceB64 = fs.readFileSync(facePng).toString('base64');
const faceUrl = `data:image/png;base64,${faceB64}`;

// deterministic pseudo-random
let seed = 7;
const rnd = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
const pick = (a) => a[Math.floor(rnd() * a.length)];
const WORDS = ['CRUNCH', 'OATS', 'POP', 'FIZZ', 'BITES', 'KETTLE', 'SPARK', 'CRISP', 'BAR', 'MIX', 'NUTS', 'COLD BREW', 'CHIPS', 'TRAIL', 'PUFFS', 'SODA', 'TEA', 'JERKY', 'COOKIE', 'MINTS', 'SELTZER', 'GRANOLA'];
const COLORS = ['#D93A2B', '#F2B705', '#F27405', '#1F7A3A', '#7A1FA2', '#0F5FA8', '#E94E8A', '#2B2B2B', '#8C5A2B', '#E5E5E5', '#14A0B4', '#C0D725', '#FF7F50', '#5B3A29'];
const FONTS = ['"Liberation Sans"', '"DejaVu Sans"', 'Carlito', 'Inter', '"FreeSans"'];

function pkg(xIn, wIn, hIn, S, shelfY, extra = '') {
  const c = pick(COLORS), w = pick(WORDS), f = pick(FONTS);
  const fg = ['#E5E5E5', '#F2B705', '#C0D725'].includes(c) ? '#222' : '#fff';
  const kind = rnd();
  const radius = kind < 0.3 ? `${wIn * S * 0.45}px ${wIn * S * 0.45}px 4px 4px` : kind < 0.55 ? '10px' : '2px';
  return `<div style="position:absolute;left:${xIn * S}px;top:${(shelfY - hIn) * S}px;width:${wIn * S}px;height:${hIn * S}px;background:${c};border-radius:${radius};box-shadow:inset -6px 0 10px rgba(0,0,0,.18);overflow:hidden;${extra}">
    <div style="position:absolute;left:6%;right:6%;top:${20 + rnd() * 30}%;font:900 ${Math.min(wIn * 0.28, hIn * 0.22) * S}px/1 ${f};color:${fg};text-align:center;word-break:break-all">${w}</div>
    <div style="position:absolute;left:10%;right:10%;bottom:12%;height:${0.3 * S}px;background:rgba(255,255,255,.35)"></div></div>`;
}

function wideScene(S) {
  // 120 x 90 in field (y measured from the top of the frame). Counter top at y=64 (36 in above
  // the floor), eye-level shelf at y=42 (58 in), upper shelf at y=28 (72 in).
  // Package sizes are real-world: snack bags 5 x 7 in, bars 1.5 x 6 in, cans 2.6 x 4.8 in, boxes up to 8 x 11 in.
  const W = 120, H = 90;
  let html = `<div style="position:relative;width:${W * S}px;height:${H * S}px;background:linear-gradient(180deg,#CFC8BC,#BDB5A7);overflow:hidden">`;
  // window light patch
  html += `<div style="position:absolute;left:${84 * S}px;top:${6 * S}px;width:${30 * S}px;height:${40 * S}px;background:rgba(255,255,240,.35);filter:blur(${4 * S}px)"></div>`;
  const shelves = [{ y: 28, x0: 10, x1: 106 }, { y: 42, x0: 10, x1: 106 }];
  for (const sh of shelves) {
    html += `<div style="position:absolute;left:${sh.x0 * S}px;top:${sh.y * S}px;width:${(sh.x1 - sh.x0) * S}px;height:${1.2 * S}px;background:#F4F1EA;box-shadow:0 ${0.6 * S}px ${1 * S}px rgba(0,0,0,.25)"></div>`;
  }
  // top shelf: packages all along
  const size = () => { const k = rnd(); return k < 0.35 ? [5 + rnd(), 7 + rnd() * 1.5] : k < 0.55 ? [2.6, 4.8] : k < 0.75 ? [3.5 + rnd(), 9 + rnd() * 2] : k < 0.9 ? [7 + rnd(), 10 + rnd()] : [1.6, 6]; };
  let x = 11;
  while (x < 104) { const [w, h] = size(); html += pkg(x, w, h, S, 28); x += w + 0.3 + rnd() * 0.6; }
  // eye-level shelf: packages, then the tent card with the brand's own bags beside it, then more packages
  x = 11;
  while (x < 46) { const [w, h] = size(); html += pkg(x, w, h, S, 42); x += w + 0.3 + rnd() * 0.6; }
  // brand product (generic orange bags labelled SAMPLE) left of the card
  for (let k = 0; k < 4; k++) html += `<div style="position:absolute;left:${(47 + k * 3.2) * S}px;top:${(42 - 7.5) * S}px;width:${3 * S}px;height:${7.5 * S}px;background:#E8823A;border-radius:${0.6 * S}px ${0.6 * S}px 3px 3px;box-shadow:inset -5px 0 8px rgba(0,0,0,.2)"><div style="margin-top:${2 * S}px;text-align:center;font:800 ${0.7 * S}px/1 Inter;color:#fff">SAMPLE</div></div>`;
  // the tent card: 7 x 5 in face, leaning back (vertical squash 0.93)
  html += `<img src="${faceUrl}" style="position:absolute;left:${60.5 * S}px;top:${(42 - 5 * 0.93) * S}px;width:${7 * S}px;height:${5 * 0.93 * S}px;box-shadow:0 0 ${0.6 * S}px rgba(0,0,0,.25)">`;
  x = 69;
  while (x < 104) { const [w, h] = size(); html += pkg(x, w, h, S, 42); x += w + 0.3 + rnd() * 0.6; }
  // counter, coffee machine, paper towels, fridge edge
  html += `<div style="position:absolute;left:0;top:${64 * S}px;width:${W * S}px;height:${26 * S}px;background:linear-gradient(180deg,#9C7A56,#7E6044)"></div>`;
  html += `<div style="position:absolute;left:${4 * S}px;top:${64 * S}px;width:${112 * S}px;height:${2 * S}px;background:#E9E3D6"></div>`;
  html += `<div style="position:absolute;left:${18 * S}px;top:${(64 - 14) * S}px;width:${10 * S}px;height:${14 * S}px;background:#2E2E2E;border-radius:${1 * S}px"></div>`;
  html += `<div style="position:absolute;left:${88 * S}px;top:${(64 - 11) * S}px;width:${5 * S}px;height:${11 * S}px;background:#F7F7F2;border-radius:${2.5 * S}px"></div>`;
  html += `<div style="position:absolute;left:${108 * S}px;top:${4 * S}px;width:${14 * S}px;height:${86 * S}px;background:#D9DCDD;box-shadow:inset 6px 0 10px rgba(0,0,0,.2)"></div>`;
  html += '</div>';
  return { html, w: W * S, h: H * S };
}

function closeScene(S) {
  // 32.7 x 24.5 in field; card centred-left, two product bags to its right, counter edge below.
  const W = 32.7, H = 24.5;
  let html = `<div style="position:relative;width:${W * S}px;height:${H * S}px;background:linear-gradient(180deg,#CBC4B8,#B8B0A2);overflow:hidden">`;
  html += `<div style="position:absolute;left:0;top:${17 * S}px;width:${W * S}px;height:${8 * S}px;background:linear-gradient(180deg,#F1EDE4,#DCD6CA)"></div>`;
  html += `<img src="${faceUrl}" style="position:absolute;left:${8 * S}px;top:${(17.3 - 5 * 0.92) * S}px;width:${7 * S}px;height:${5 * 0.92 * S}px;box-shadow:0 0 ${0.3 * S}px rgba(0,0,0,.3)">`;
  for (let k = 0; k < 3; k++) html += `<div style="position:absolute;left:${(16.2 + k * 3.3) * S}px;top:${(17.3 - 7.5) * S}px;width:${3.1 * S}px;height:${7.5 * S}px;background:#E8823A;border-radius:${0.6 * S}px ${0.6 * S}px 4px 4px;box-shadow:inset -8px 0 14px rgba(0,0,0,.2)"><div style="margin-top:${2 * S}px;text-align:center;font:800 ${0.6 * S}px/1 Inter;color:#fff">SAMPLE</div></div>`;
  html += '</div>';
  return { html, w: Math.round(W * S), h: Math.round(H * S) };
}

function magick(args) { execFileSync('convert', args, { stdio: 'inherit' }); }

(async () => {
  const { chromium } = require('playwright');
  const browser = await chromium.launch();
  const page = await browser.newPage();
  async function shoot(scene, file) {
    await page.setViewportSize({ width: Math.ceil(scene.w), height: Math.ceil(scene.h) });
    await page.setContent(`<html><body style="margin:0">${scene.html}</body></html>`);
    await page.waitForLoadState('load');
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: file, clip: { x: 0, y: 0, width: Math.ceil(scene.w), height: Math.ceil(scene.h) } });
  }
  const tmpW = path.join(outDir, `_raw-wide-${label}.png`);
  const tmpC = path.join(outDir, `_raw-close-${label}.png`);
  await shoot(wideScene(24), tmpW);
  await shoot(closeScene(123.3), tmpC);
  await browser.close();

  // camera effects: blur, noise, light falloff, JPEG
  const wide = path.join(outDir, `wide-${label}-2880.jpg`);
  magick([tmpW, '-blur', '0x0.8', '-attenuate', '0.35', '+noise', 'Gaussian', '(', '+clone', '-fill', 'black', '-colorize', '100', '-fill', 'white', '-draw', 'ellipse 1440,1080 1700,1300 0,360', '-blur', '0x300', ')', '-compose', 'multiply', '-composite', '-quality', '72', wide]);
  magick([wide, '-resize', '50%', '-quality', '70', path.join(outDir, `wide-${label}-1440-report-size.jpg`)]);
  // crops around the card for inspection (card at 60.5 in, shelf at 48 in -> px at 24/in)
  magick([wide, '-crop', `${Math.round(30 * 24)}x${Math.round(16 * 24)}+${Math.round(50 * 24)}+${Math.round(30 * 24)}`, '+repage', path.join(outDir, `wide-${label}-crop-card-region.png`)]);
  const close = path.join(outDir, `close-${label}-4032.jpg`);
  magick([tmpC, '-blur', '0x1.0', '-attenuate', '0.3', '+noise', 'Gaussian', '-quality', '82', close]);
  magick([close, '-resize', '2048x', '-quality', '70', path.join(outDir, `close-${label}-2048.jpg`)]);
  magick([close, '-resize', '1280x', '-quality', '65', path.join(outDir, `close-${label}-1280.jpg`)]);
  // crop the allergen panel region at native pixels of each version (card left 8 in, allergen ~3 in down)
  for (const [wpx, f] of [[4032, close], [2048, path.join(outDir, `close-${label}-2048.jpg`)], [1280, path.join(outDir, `close-${label}-1280.jpg`)]]) {
    const k = wpx / 4032, ppi = 123.3 * k;
    magick([f, '-crop', `${Math.round(7.4 * ppi)}x${Math.round(3.2 * ppi)}+${Math.round(7.8 * ppi)}+${Math.round(14.2 * ppi)}`, '+repage', path.join(outDir, `close-${label}-${wpx}-crop-allergen.png`)]);
  }
  fs.unlinkSync(tmpW); fs.unlinkSync(tmpC);
  console.log('photo simulations written to', outDir);
})().catch((e) => { console.error(e); process.exit(1); });
