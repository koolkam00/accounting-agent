#!/usr/bin/env node
/*
  doc-tests.js: tests for the part-2 documents (one-pagers, discovery, proposal, report),
  the signature and the avatar. Run from anywhere:  node tests/documents/doc-tests.js
  Needs Node 18+, Playwright, pdftotext and pdfinfo (poppler), ImageMagick identify.
  Writes PNGs for a person to look at in tests/rename-documents/.
*/
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync, spawnSync } = require('child_process');
const ROOT = path.resolve(__dirname, '../..');
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'dd-doc-tests-'));
let pass = 0, fail = 0;
const ok = (m) => { console.log('PASS  ' + m); pass++; };
const bad = (m, extra) => { console.log('FAIL  ' + m); if (extra) console.log('      ' + String(extra).split('\n').slice(0, 6).join('\n      ')); fail++; };
const render = (tpl, data, out, flags = [], root = ROOT) => {
  const file = typeof data === 'string' ? data : (() => { const f = path.join(TMP, `d-${Math.random().toString(36).slice(2)}.json`); fs.writeFileSync(f, JSON.stringify(data)); return f; })();
  const r = spawnSync('node', [path.join(root, 'render/render.js'), tpl, file, out, '--json', ...flags], { cwd: root, encoding: 'utf8' });
  let status = null; try { status = JSON.parse(r.stdout.slice(r.stdout.indexOf('{'))); } catch (e) { /* not json */ }
  return { code: r.status, status, out: r.stdout + r.stderr };
};
const pages = (pdf) => +(/Pages:\s+(\d+)/.exec(execFileSync('pdfinfo', [pdf], { encoding: 'utf8' })) || [0, 0])[1];
// reading-order text (columns kept apart), whitespace collapsed per page; pages split by \f
const text = (pdf) => execFileSync('pdftotext', [pdf, '-'], { encoding: 'utf8' }).split('\f').map((pg) => pg.replace(/\s+/g, ' ')).join('\f');
const S = (t, f) => path.join(ROOT, 'templates', t, 'samples', f + '.json');
const load = (t, f) => JSON.parse(fs.readFileSync(S(t, f), 'utf8'));

// ---------- 1. every sample renders, with the right page count ----------
const expectPages = [
  ['discovery-one-pager', 'DEFAULT', 1], ['office-one-pager', 'BLANK-placeholders', 1], ['brand-one-pager', 'BLANK-placeholders', 1],
  ['proposal', 'BLANK-placeholders', 2], ['proposal', 'SAMPLE-founding', 2], ['proposal', 'SAMPLE-standard-10-offices', 2],
  ['report', 'BLANK-placeholders', 1], ['report', 'SAMPLE-5-offices', 1], ['report', 'SAMPLE-10-offices-long-comments', 2],
];
for (const [t, f, n] of expectPages) {
  const out = path.join(TMP, `${t}-${f}.pdf`);
  const r = render(t, S(t, f), out);
  if (r.code !== 0) { bad(`${t} ${f} renders`, r.out); continue; }
  const p = pages(out);
  p === n ? ok(`${t} ${f} renders, ${p} page${p > 1 ? 's' : ''}`) : bad(`${t} ${f}: ${p} pages, wanted ${n}`);
}

// ---------- 1b. the BLANK sample of each template equals the template's own data block ----------
for (const [t, f] of [['report', 'BLANK-placeholders'], ['proposal', 'BLANK-placeholders'], ['office-one-pager', 'BLANK-placeholders'], ['brand-one-pager', 'BLANK-placeholders'], ['discovery-one-pager', 'DEFAULT'], ['tent-card', 'BLANK-placeholders']]) {
  const html = fs.readFileSync(path.join(ROOT, 'templates', t, t + '.html'), 'utf8');
  const block = JSON.parse(/<script type="application\/json" id="dd-data">([\s\S]*?)<\/script>/.exec(html)[1]);
  JSON.stringify(block) === JSON.stringify(load(t, f)) ? ok(`${t}: samples/${f}.json matches the template's built-in data`) : bad(`${t}: samples/${f}.json differs from the template's built-in data`);
}

// ---------- 2. the brief's report test: ten offices, long comments, SAMPLE ----------
{
  const out = path.join(TMP, 'r10.pdf');
  const r = render('report', S('report', 'SAMPLE-10-offices-long-comments'), out);
  const fit = r.status && r.status.fit && r.status.fit[0];
  const tx = r.code === 0 ? text(out) : '';
  const comments = load('report', 'SAMPLE-10-offices-long-comments');
  const norm = (s) => s.replace(/\s+/g, ' ').replace(/[“”]/g, '"').trim();
  const whole = ['comment_1', 'comment_2', 'comment_3'].every((k) => norm(tx).includes(norm(comments[k]).slice(0, 60)) && norm(tx).includes(norm(comments[k]).slice(-40)));
  if (r.code === 0 && fit && fit.fits && whole && /SAMPLE\. ILLUSTRATIVE PLACEHOLDERS, NOT RESULTS/i.test(tx)) ok(`ten offices with three long comments fit on page 1 (comments ${fit.comment_pt} pt, thumbnails on page 2: ${fit.thumbnails_on_page_2}); every comment printed whole; SAMPLE banner present`);
  else bad('ten-office long-comment report', r.out);
  const lad = ['DELIVERED', 'PLACED', 'DEPLETED', 'RESPONDED', 'SCANNED', 'PURCHASED', 'INCREMENTAL', 'Not measured'];
  lad.every((w) => tx.includes(w)) ? ok('report shows every ladder rung, and "Incremental: Not measured"') : bad('ladder rungs missing', lad.filter((w) => !tx.includes(w)).join(', '));
  /515[\s\S]*495[\s\S]*428[\s\S]*77[\s\S]*103[\s\S]*14/.test(tx) ? ok('report totals computed from the office rows (515 delivered incl. top-ups, 495 placed, 428 depleted, 77 responses, 103 scans, 14 redemptions)') : bad('report totals');
  /58 of 77 \(75%\)/.test(tx) && /yes 31 \(42%\), maybe 29 \(39%\), no 14 \(19%\) of 74 who answered/.test(tx) ? ok('survey shares printed beside their counts, with "of 74 who answered"') : bad('survey shares and counts');
  /No photo received/.test(text(out).split('\f')[1] || '') ? ok('a missing photo is reported as "No photo received", not hidden') : bad('missing photo not reported');
}

// ---------- 3. negative cases: the template must refuse (exit 2) ----------
// photo paths are relative to the sample file; a test JSON lives elsewhere, so make them absolute
const r10 = () => { const d = load('report', 'SAMPLE-10-offices-long-comments'); d.offices.forEach((o) => ['placement_photo', 'later_photo'].forEach((k) => { if (o[k] && !o[k].startsWith('[')) o[k] = path.join(ROOT, 'templates/report/samples', o[k]); })); return d; };
const neg = [
  ['report: placed more than delivered', 'report', (() => { const d = r10(); d.offices[0].units_placed = '60'; return d; })(), /placed \(60\) is more than delivered/],
  ['report: depleted more than placed plus topped up', 'report', (() => { const d = r10(); d.offices[1].units_depleted_day5 = '45'; return d; })(), /depleted by day 5 \(45\)/],
  ['report: a comment with an email address', 'report', (() => { const d = r10(); d.comment_2 = 'SAMPLE great, email me at person@example.com'; return d; })(), /email address or phone number/],
  ['report: a Monday drop date', 'report', (() => { const d = r10(); d.drop_date = '2027-02-08'; return d; })(), /not a Tuesday or Wednesday/],
  ['report: window in the December blackout', 'report', (() => { const d = r10(); d.drop_date = '2026-12-15'; return d; })(), /blackout/],
  ['report: more "tried" than responses', 'report', (() => { const d = r10(); d.survey_tried_yes = '90'; return d; })(), /more than the survey responses/],
  ['report: far too much text refuses instead of shrinking past the floors', 'report', (() => { const d = r10(); const long = 'SAMPLE ' + 'This is a very long verbatim comment that keeps going and going. '.repeat(9); d.comment_1 = long; d.comment_2 = long; d.comment_3 = long; return d; })(), /runs past the bottom of the page/],
  ['proposal: wrong number of offices for the tier', 'proposal', (() => { const d = load('proposal', 'SAMPLE-founding'); d.offices = d.offices.slice(0, 4); return d; })(), /lists 4 offices/],
  ['proposal: asked ship-by later than T-10', 'proposal', (() => { const d = load('proposal', 'SAMPLE-founding'); d.ship_by_requested = '2027-01-04'; return d; })(), /later than the latest ship-by/],
  ['proposal: drop window in a blackout', 'proposal', (() => { const d = load('proposal', 'SAMPLE-founding'); d.drop_date = '2027-08-17'; return d; })(), /blackout/],
  ['proposal: no buy path', 'proposal', (() => { const d = load('proposal', 'SAMPLE-founding'); d.retailers = []; d.online_site = ''; return d; })(), /buy path/],
  ['proposal: planned units outside 30 to 80', 'proposal', (() => { const d = load('proposal', 'SAMPLE-founding'); d.offices[0].planned_units = '120'; return d; })(), /outside 30 to 80/],
  ['discovery: two sentences in one box', 'discovery-one-pager', S('discovery-one-pager', 'SAMPLE-must-warn'), /reads as 2 sentences/],
  ['office one-pager: copy too long for the page', 'office-one-pager', (() => { const d = load('office-one-pager', 'BLANK-placeholders'); d.privacy = d.privacy.repeat(6); return d; })(), /runs past the bottom of the page/],
];
for (const [name, t, data, want] of neg) {
  const r = render(t, data, path.join(TMP, 'neg.pdf'));
  const msgs = r.status ? r.status.errors.join(' ') : r.out;
  r.code === 2 && want.test(msgs) ? ok(`refused: ${name}`) : bad(`not refused as expected: ${name} (exit ${r.code})`, msgs);
}
{
  const r = render('discovery-one-pager', S('discovery-one-pager', 'SAMPLE-must-warn'), path.join(TMP, 'w.pdf'));
  r.status && r.status.warnings.some((w) => /sounds like selling/.test(w)) ? ok('discovery: selling words raise a warning') : bad('discovery selling-word warning');
  const d = render('discovery-one-pager', S('discovery-one-pager', 'DEFAULT'), path.join(TMP, 'd5.pdf'));
  d.status && d.status.fit && d.status.fit[0].sentences === 5 ? ok('discovery: the shipped page has exactly five sentences') : bad('discovery sentence count', JSON.stringify(d.status && d.status.fit));
}

// ---------- 4. --final ----------
for (const [t, f] of [['report', 'BLANK-placeholders'], ['proposal', 'BLANK-placeholders'], ['office-one-pager', 'BLANK-placeholders'], ['brand-one-pager', 'BLANK-placeholders'], ['discovery-one-pager', 'DEFAULT'], ['report', 'SAMPLE-5-offices']]) {
  const r = render(t, S(t, f), path.join(TMP, 'f.pdf'), ['--final']);
  r.code === 3 ? ok(`--final refuses ${t} ${f} (placeholders, SAMPLE or unfilled brand.json contacts)`) : bad(`--final did not refuse ${t} ${f} (exit ${r.code})`);
}
// a complete, non-sample report and discovery page pass --final in a temp copy with brand.json filled
const copyRoot = (dir) => { fs.mkdirSync(dir, { recursive: true }); for (const d of ['templates', 'system', 'fonts', 'tokens', 'wordmark', 'render', 'brand.json']) execFileSync('cp', ['-r', path.join(ROOT, d), dir]); return dir; };
{
  const T = copyRoot(path.join(TMP, 'filled'));
  const b = JSON.parse(fs.readFileSync(path.join(T, 'brand.json'), 'utf8'));
  Object.assign(b.contact, { FOUNDER_NAME: 'Test Person', PHONE: '(212) 555-0100', EMAIL: 'test@example.com', WEBSITE: 'example.com', POSTAL_ADDRESS: '1 Example Plaza, New York, NY 10010' });
  fs.writeFileSync(path.join(T, 'brand.json'), JSON.stringify(b, null, 2));
  execFileSync('node', [path.join(T, 'render/build-brand.js'), '--no-png'], { cwd: T });
  const d = JSON.parse(JSON.stringify(load('report', 'SAMPLE-5-offices')).replace(/SAMPLE[ -]?/g, ''));
  d.offices.forEach((o) => { o.placement_photo = ''; o.later_photo = ''; });
  const r = render('report', d, path.join(TMP, 'final.pdf'), ['--final'], T);
  r.code === 0 ? ok('--final accepts a complete, non-sample report once brand.json is filled (temp copy, deleted)') : bad('--final on a complete report', r.out);
  const r2 = render('discovery-one-pager', S('discovery-one-pager', 'DEFAULT'), path.join(TMP, 'final2.pdf'), ['--final'], T);
  r2.code === 0 ? ok('--final accepts the discovery page once brand.json is filled') : bad('--final discovery', r2.out);
}

// ---------- 5. words: no claims, no soft ladder words, in any PDF ----------
{
  const ALLOWED = [/No sales guarantee/gi, /we do not claim lift/gi, /never promise: sales, lift or new customers/gi, /not a sales guarantee/gi];
  const BANNED = /\b(conversions?|ROI|sales lift|acquisition|guaranteed?|healthy|healthier|superfoods?|boosts?|best[- ]selling|immunity|detox|clinically|proven|lift)\b/gi;
  const found = [];
  for (const f of fs.readdirSync(path.join(ROOT, 'pdf')).filter((x) => x.endsWith('.pdf'))) {
    let t = text(path.join(ROOT, 'pdf', f)).replace(/\s+/g, ' ');
    ALLOWED.forEach((a) => { t = t.replace(a, ''); });
    const m = t.match(BANNED); if (m) found.push(`${f}: ${[...new Set(m)].join(', ')}`);
  }
  found.length ? bad('claims or soft-ladder words in the PDFs', found.join('\n')) : ok('no claims or soft-ladder words in any PDF in pdf/ (negations such as "No sales guarantee" allowed)');
}

// ---------- 6. the limitations paragraph is frozen ----------
(async () => {
  const { chromium } = require('playwright');
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + path.join(ROOT, 'templates/report/report.html'));
  await p.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  const lim = await p.evaluate(() => window.DDReport.LIMITATIONS);
  const frozen = fs.readFileSync(path.join(__dirname, 'limitations-frozen.txt'), 'utf8').trim();
  lim === frozen ? ok('the limitations paragraph matches tests/documents/limitations-frozen.txt (change both on purpose, never one)') : bad('the limitations paragraph changed', lim);
  const tx = text(path.join(ROOT, 'pdf/report-BLANK.pdf')).replace(/\s+/g, ' ');
  const pt = text(path.join(ROOT, 'pdf/proposal-SAMPLE-founding.pdf')).replace(/\s+/g, ' ');
  const n = (s) => s.replace(/\s+/g, ' ').replace(/-\s/g, '-');
  n(tx).includes(n(frozen).slice(0, 80)) && n(pt).includes(n(frozen).slice(-80)) ? ok('the paragraph prints on the blank report and on the proposal\'s mock page') : bad('limitations not printed');
  /MOCK REPORT PAGE · ILLUSTRATIVE PLACEHOLDERS, NOT RESULTS/i.test(pt) ? ok('the proposal\'s mock page carries "Illustrative placeholders, not results"') : bad('mock label missing');
  await b.close();

  // ---------- 7. rename: documents follow brand.json ----------
  const T = copyRoot(path.join(TMP, 'rename'));
  const bj = JSON.parse(fs.readFileSync(path.join(T, 'brand.json'), 'utf8')); bj.BRAND_NAME = 'Dropp'; fs.writeFileSync(path.join(T, 'brand.json'), JSON.stringify(bj, null, 2));
  execFileSync('node', [path.join(T, 'render/build-brand.js'), '--no-png'], { cwd: T });
  const RD = path.join(ROOT, 'tests/rename-documents'); fs.mkdirSync(RD, { recursive: true });
  let leaks = [];
  for (const [t, f] of [['discovery-one-pager', 'DEFAULT'], ['office-one-pager', 'BLANK-placeholders'], ['brand-one-pager', 'BLANK-placeholders'], ['proposal', 'SAMPLE-founding'], ['report', 'SAMPLE-5-offices']]) {
    const out = path.join(TMP, `rn-${t}.pdf`);
    const r = render(t, S(t, f), out, [], T);
    if (r.code !== 0) { leaks.push(`${t}: did not render (${r.out.slice(0, 200)})`); continue; }
    const tx = text(out);
    if (/Desk Drop/.test(tx)) leaks.push(`${t}: old name still printed`);
    if (!/Dropp/.test(tx)) leaks.push(`${t}: new name not printed`);
    execFileSync('pdftoppm', ['-r', '60', '-png', '-f', '1', '-l', '1', out, path.join(RD, `Dropp-${t}`)]);
  }
  leaks.length ? bad('documents follow a rename in brand.json', leaks.join('\n')) : ok('rename: with BRAND_NAME "Dropp", all five documents print "Dropp" and never "Desk Drop" (images in tests/rename-documents/)');

  // ---------- 8. signature and avatar ----------
  const sig = fs.readFileSync(path.join(ROOT, 'signature/signature.html'), 'utf8');
  const out = fs.readFileSync(path.join(ROOT, 'signature/signature-outreach.html'), 'utf8');
  const txt = fs.readFileSync(path.join(ROOT, 'signature/signature.txt'), 'utf8');
  const legal = fs.readFileSync(path.resolve(ROOT, '../desk-drop-legal-pack/02-email-footer-and-checklist.md'), 'utf8');
  const fb = (/###\s*Footer B[\s\S]*?```text\s*\n([\s\S]*?)\n```/.exec(legal) || [])[1];
  ['[PHONE]', '[WEBSITE]', '[POSTAL ADDRESS]'].every((k) => sig.includes(k) && txt.includes(k)) ? ok('signature (HTML and text) carries [PHONE], [WEBSITE] and [POSTAL ADDRESS]') : bad('signature placeholders');
  fb && out.includes(fb.trim().replace(/"/g, '&quot;').replace(/'/g, "'")) || (fb && out.includes(fb.trim())) ? ok('outreach signature carries the legal pack\'s Footer B line verbatim') : bad('Footer B line missing or changed');
  const body = sig.slice(sig.indexOf('<table'), sig.lastIndexOf('</table>') + 8);
  body.length < 10000 && !/<style|class=/.test(body) ? ok(`signature HTML is ${body.length} characters (Gmail limit 10,000), inline styles only`) : bad('signature size or style sheet');
  const want = ['cobalt', 'paper', 'ink'].flatMap((v) => [1024, 512, 400, 320, 160, 80, 40].map((s) => [v, s]));
  const wrong = want.filter(([v, s]) => { try { return execFileSync('identify', ['-format', '%wx%h', path.join(ROOT, `avatar/avatar-${v}-${s}.png`)], { encoding: 'utf8' }) !== `${s}x${s}`; } catch (e) { return true; } });
  wrong.length ? bad('avatar sizes', JSON.stringify(wrong)) : ok('avatar PNGs exist at 1024, 512, 400, 320, 160, 80 and 40 px in three variants');

  fs.rmSync(TMP, { recursive: true, force: true });
  console.log(`----\n${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
