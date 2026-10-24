#!/usr/bin/env node
/*
  details-test.js: the Chrome-only path for your details works end to end (review round 1, R1-11).
  In a temp copy of the folder, as a founder without a terminal would:
    1. open details.html in Chrome, type name, phone, email and postal address;
    2. press Save brand.js and put the downloaded file in system/ (the test does the "move");
    3. reload a document template: no brand.json placeholder is left, and --final accepts it;
    4. the signature on the page carries the details and Footer B;
    5. later, a terminal build copies the details into brand.json and keeps them.
  Writes tests/details/details-page.png. Exit 0 when every check passes.
*/
const fs = require('fs'), os = require('os'), path = require('path');
const { execFileSync, spawnSync } = require('child_process');
const { chromium } = require('playwright');
const ROOT = path.resolve(__dirname, '../..');
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'dd-details-'));
let pass = 0, fail = 0;
const ok = (m) => { console.log('PASS  ' + m); pass++; };
const bad = (m, x) => { console.log('FAIL  ' + m + (x ? '\n      ' + String(x).slice(0, 400) : '')); fail++; };
for (const d of ['templates', 'system', 'fonts', 'tokens', 'wordmark', 'render', 'brand.json', 'details.html']) execFileSync('cp', ['-r', path.join(ROOT, d), TMP]);
const T = TMP;
const DET = { FOUNDER_NAME: 'Patricia Example-Lee', PHONE: '(212) 555-0100', EMAIL: 'patricia.lee@examples.com', POSTAL_ADDRESS: 'PO Box 1234, Madison Square Station, NY 10010' };
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ acceptDownloads: true, viewport: { width: 1280, height: 1100 } });
  const p = await ctx.newPage();
  await p.goto('file://' + path.join(T, 'details.html'));
  for (const [k, v] of Object.entries(DET)) await p.fill(`input[data-k="${k}"]`, v);
  await p.check('#no-site');
  const st = await p.textContent('#status');
  /All filled in/.test(st) ? ok('details.html: status says all filled in, not saved yet') : bad('status before save', st);
  const sig = await p.innerHTML('#sig-outreach');
  sig.includes('Patricia Example-Lee') && sig.includes('(212) 555-0100') && sig.includes('PO Box 1234') && /no thanks/.test(sig) && !/\[WEBSITE\]/.test(sig) ? ok('the outreach signature on the page carries the details and Footer B, website left off') : bad('signature', sig);
  await p.screenshot({ path: path.join(__dirname, 'details-page.png'), fullPage: false });
  const [dl] = await Promise.all([p.waitForEvent('download'), p.click('#save')]);
  dl.suggestedFilename() === 'brand.js' ? ok('Save brand.js downloads a file named brand.js') : bad('download name', dl.suggestedFilename());
  // the founder moves the file into system/ (a little later than brand.json was last changed)
  await new Promise((r) => setTimeout(r, 1100));
  await dl.saveAs(path.join(T, 'system/brand.js'));
  await p.reload();
  const st2 = await p.textContent('#status');
  /already has them/.test(st2) ? ok('after the move, details.html reads the details back from system/brand.js') : bad('status after save', st2);
  await b.close();
  // a document now prints the details and passes --final (discovery page has no other placeholders)
  const r = spawnSync('node', [path.join(T, 'render/render.js'), 'discovery-one-pager', path.join(T, 'templates/discovery-one-pager/samples/DEFAULT.json'), path.join(TMP, 'd.pdf'), '--final', '--json'], { cwd: T, encoding: 'utf8' });
  const txt = r.status === 0 ? execFileSync('pdftotext', [path.join(TMP, 'd.pdf'), '-'], { encoding: 'utf8' }) : '';
  r.status === 0 && txt.includes('Patricia Example-Lee') && txt.includes('(212) 555-0100') ? ok('without any terminal step, the discovery page prints the details and --final accepts it') : bad('document after Chrome-only save', r.stdout + r.stderr);
  // a later terminal build keeps them: build-brand copies them into brand.json
  const out = execFileSync('node', [path.join(T, 'render/build-brand.js'), '--no-png'], { cwd: T, encoding: 'utf8' });
  const bj = JSON.parse(fs.readFileSync(path.join(T, 'brand.json'), 'utf8'));
  /Took your details/.test(out) && bj.contact.PHONE === DET.PHONE && bj.contact.WEBSITE === '' ? ok('a later terminal build copies the details into brand.json instead of putting placeholders back') : bad('brand.json after build', out + JSON.stringify(bj.contact));
  const js = fs.readFileSync(path.join(T, 'system/brand.js'), 'utf8');
  js.includes(DET.EMAIL) && !/details_saved/.test(js) ? ok('the rebuilt brand.js keeps the details') : bad('brand.js after build', js.slice(0, 300));
  fs.rmSync(TMP, { recursive: true, force: true });
  console.log(`----\n${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
