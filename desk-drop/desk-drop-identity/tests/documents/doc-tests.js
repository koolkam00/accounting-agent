#!/usr/bin/env node
/*
  doc-tests.js: tests for the part-2 documents (one-pagers, discovery, proposal, report),
  the signature and the avatar. Run from anywhere:  node tests/documents/doc-tests.js
  v1.2 (review round 1): every document with REAL-LENGTH details in brand.json; the proposal with a
  landscape map for 10, 11 and 12 offices; the report's photo strip for 10 to 12 offices with long
  text; Delivered as the handoff count; the mock page free of yellow; legal versions in step.
  Stress inputs in tests/documents/cases/ (several from the round-1 reviewer's own files).
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
  if (r.code === 0 && fit && fit.fits && whole && !fit.later_photos_on_page_2 && /SAMPLE\. ILLUSTRATIVE PLACEHOLDERS, NOT RESULTS/i.test(tx)) ok(`ten offices with three long comments fit on page 1 WITH both photo rows (comments ${fit.comment_pt} pt, thumbnails ${fit.thumb_in} in); every comment printed whole; SAMPLE banner present`);
  else bad('ten-office long-comment report', r.out);
  const lad = ['DELIVERED', 'PLACED', 'DEPLETED', 'RESPONDED', 'SCANNED', 'PURCHASED', 'INCREMENTAL', 'Not measured'];
  lad.every((w) => tx.includes(w)) ? ok('report shows every ladder rung, and "Incremental: Not measured"') : bad('ladder rungs missing', lad.filter((w) => !tx.includes(w)).join(', '));
  /500 495 428 77 103/.test(tx) && !/515/.test(tx) ? ok('report totals computed from the office rows: Delivered 500 is the handoff count, the same in the ladder and the roster (495 placed, 428 depleted, 77 responses, 103 scans)') : bad('report totals');
  /Plus 15 day-3 top-ups from reserve/.test(tx) && /455 of 500 units \(91%\) within one business day/.test(tx) ? ok('top-ups shown beside Delivered, never added to it; Placed shows the Gate 2 unit share (455 of 500, 91%)') : bad('Delivered and Placed hints');
  !/none of them is a sale/.test(tx) ? ok('the limitations paragraph no longer says "none of them is a sale" (Purchased is code redemptions)') : bad('old limitations sentence');
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
  ['report: far too much text refuses instead of shrinking past the floors', 'report', (() => { const d = r10(); const long = 'SAMPLE ' + 'This is a very long verbatim comment that keeps going and going. '.repeat(16); d.comment_1 = long; d.comment_2 = long; d.comment_3 = long; return d; })(), /runs past the bottom of the page/],
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

// ---------- 3b. stress cases: they must FIT, at or above the stated floors ----------
const C = (f) => path.join(__dirname, 'cases', f + '.json');
for (const [name, file, want] of [
  ['report: 10 offices, three ~70-word comments and a retailer-velocity line keep the day-1 photo strip', 'report-10-offices-velocity', (f) => !f.thumbnails_on_page_2],
  ['report: 12 offices with the sample comments keep the day-1 photo strip', 'report-12-offices', (f) => !f.thumbnails_on_page_2],
  ['report: 11 offices keep the day-1 photo strip', 'report-11-offices', (f) => !f.thumbnails_on_page_2],
  ['report: 10 offices with 100-word "learned" and a 55-word recommendation fit (photos may move, counts stay)', 'report-10-offices-long-learned', () => true],
  ['report: 10 offices with every text field long still fit (photos may move, counts stay)', 'report-10-offices-everything-long', () => true],
]) {
  const r = render('report', C(file), path.join(TMP, file + '.pdf'));
  const f = r.status && r.status.fit && r.status.fit[0];
  r.code === 0 && f && f.fits && f.comment_pt >= 8 && f.learned_pt >= 8.5 && f.thumb_in >= 0.38 && want(f) ? ok(`${name} (comments ${f.comment_pt} pt, learned ${f.learned_pt} pt, later photos on page 2: ${f.later_photos_on_page_2}, all photos on page 2: ${f.thumbnails_on_page_2})`) : bad(name, r.out.slice(0, 600));
}
for (const [name, file, n] of [
  ['proposal: standard, 10 offices, landscape map, 2 stores', 'proposal-standard-10-map-2stores', 10],
  ['proposal: standard, 10 offices, landscape map, 4 stores', 'proposal-standard-10-map-4stores', 10],
  ['proposal: standard plus 1 extra, 11 offices, map, 2 stores', 'proposal-standard-11-map-2stores', 11],
  ['proposal: standard plus 2 extra, 12 offices, map, 4 stores', 'proposal-standard-12-map-4stores', 12],
  ['proposal: founding, 5 offices, map, 4 stores', 'proposal-founding-map-4stores', 5],
]) {
  const out = path.join(TMP, file + '.pdf');
  const r = render('proposal', C(file), out);
  const f = r.status && r.status.fit && r.status.fit[0];
  r.code === 0 && pages(out) === 2 ? ok(`${name}: fits, two pages (layout ${f.arrangement}, map ${Math.round(f.map_in * 100) / 100} in tall, shown whole)`) : bad(name, r.out.slice(0, 600));
}
{
  const d = JSON.parse(fs.readFileSync(C('proposal-standard-12-map-4stores'), 'utf8'));
  d.extra_offices = '3'; d.offices.push({ neighborhood: 'Flatiron', industry: 'Retail', headcount_band: '40-75', planned_units: '40' });
  d.map_image = path.resolve(__dirname, 'cases', d.map_image);
  const r = render('proposal', d, path.join(TMP, 'p13.pdf'));
  r.code === 2 && /more than one proposal holds \(12\)/.test((r.status && r.status.errors || []).join(' ')) ? ok('proposal: 13 offices is refused with a plain message (12 is the tested maximum)') : bad('13-office proposal', r.out.slice(0, 400));
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
// every document with real-length details: a 20-character name, a 14-character phone, a
// 25-character email, a 45-character postal address (round-1 review, R1-02), and a longer set for headroom
for (const [label, det] of [
  ['real-length details', { FOUNDER_NAME: 'Patricia Example-Lee', PHONE: '(212) 555-0100', EMAIL: 'patricia.lee@examples.com', WEBSITE: 'example.com', POSTAL_ADDRESS: 'PO Box 1234, Madison Square Station, NY 10010' }],
  ['longer details (headroom)', { FOUNDER_NAME: 'Alexandra Example-Whitfield', PHONE: '+1 (212) 555-0100', EMAIL: 'alexandra.whitfield@examplemail.com', WEBSITE: 'www.example-website.com', POSTAL_ADDRESS: 'PMB 123, 1270 Avenue of the Americas, Suite 7, New York, NY 10020' }],
]) {
  const T = copyRoot(path.join(TMP, 'real-' + label.split(' ')[0]));
  const b = JSON.parse(fs.readFileSync(path.join(T, 'brand.json'), 'utf8'));
  Object.assign(b.contact, det);
  fs.writeFileSync(path.join(T, 'brand.json'), JSON.stringify(b, null, 2));
  execFileSync('node', [path.join(T, 'render/build-brand.js'), '--no-png'], { cwd: T });
  const fails = [];
  for (const [t, file] of [['brand-one-pager', C('brand-one-pager-guide-roster')], ['brand-one-pager', C('brand-one-pager-none-signed')], ['brand-one-pager', S('brand-one-pager', 'BLANK-placeholders')],
    ['office-one-pager', S('office-one-pager', 'BLANK-placeholders')], ['discovery-one-pager', S('discovery-one-pager', 'DEFAULT')],
    ['proposal', S('proposal', 'SAMPLE-founding')], ['proposal', S('proposal', 'SAMPLE-standard-10-offices')], ['proposal', C('proposal-standard-12-map-4stores')], ['proposal', C('proposal-founding-map-4stores')],
    ['report', S('report', 'SAMPLE-5-offices')], ['report', S('report', 'SAMPLE-10-offices-long-comments')], ['report', C('report-12-offices')]]) {
    const r = render(t, file, path.join(TMP, 'real.pdf'), [], T);
    if (r.code !== 0) fails.push(`${t} ${path.basename(file)}: exit ${r.code} ${(r.status && r.status.errors || []).join(' ')}`);
  }
  fails.length ? bad(`with ${label} in brand.json, every document still fits`, fails.join('\n')) : ok(`with ${label} in brand.json, all 12 document cases fit (brand one-pager with the guide's own roster example, proposals with a map, 12-office report)`);
  if (label.startsWith('real')) {
    // R1-07: a finished proposal's mock page shows the brand's own name and nothing yellow
    const d = JSON.parse(JSON.stringify(load('proposal', 'SAMPLE-founding')).replace(/SAMPLE[ -]?/g, ''));
    d.map_image = '';
    const out = path.join(TMP, 'final-proposal.pdf');
    const r = render('proposal', d, out, ['--final'], T);
    const p2 = r.code === 0 ? text(out).split('\f')[1] : '';
    r.code === 0 && p2.includes('Prepared by ' + det.FOUNDER_NAME) && p2.includes(d.brand_name) && !/\[[A-Z]/.test(p2) ? ok('a finished proposal (--final) prints the brand\'s name and the founder\'s on the mock page, and no [PLACEHOLDER] at all') : bad('mock page of a finished proposal', r.out.slice(0, 300) + ' | ' + (p2.match(/\[[A-Z][^\]]*\]/g) || []).join(', '));
  }
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

  // ---------- 7b. the legal files D restates: versions in step with HANDOFF.md ----------
  {
    const H = fs.readFileSync(path.join(ROOT, 'HANDOFF.md'), 'utf8');
    const stale = [];
    for (const f of ['01-name-check-log.md', '02-email-footer-and-checklist.md', '03-office-participation-agreement.md', '10-brand-campaign-agreement.md', '13-survey-privacy-notice.md']) {
      const v = (/Version (\d+\.\d+)/.exec(fs.readFileSync(path.resolve(ROOT, '../desk-drop-legal-pack', f), 'utf8')) || [])[1];
      const row = H.split('\n').find((l) => l.includes('desk-drop-legal-pack/' + f));
      const cited = row && (/\(v(\d+\.\d+); rechecked (\d{4}-\d{2}-\d{2})\)/.exec(row) || []);
      if (!cited || cited[1] !== v) stale.push(`${f}: legal pack is v${v}, HANDOFF cites ${cited && cited[1] ? 'v' + cited[1] : 'nothing'}`);
    }
    stale.length ? bad('legal files changed since D last rechecked them: recheck the restated terms, then update the version and date in HANDOFF.md', stale.join('\n')) : ok('every legal file D restates is at the version HANDOFF.md says was rechecked (01, 02, 03, 10, 13)');
  }

  // ---------- 8. signature and avatar ----------
  const sig = fs.readFileSync(path.join(ROOT, 'signature/signature.html'), 'utf8');
  const out = fs.readFileSync(path.join(ROOT, 'signature/signature-outreach.html'), 'utf8');
  const txt = fs.readFileSync(path.join(ROOT, 'signature/signature.txt'), 'utf8');
  const legal = fs.readFileSync(path.resolve(ROOT, '../desk-drop-legal-pack/02-email-footer-and-checklist.md'), 'utf8');
  const fb = (/###\s*Footer B[\s\S]*?```text\s*\n([\s\S]*?)\n```/.exec(legal) || [])[1];
  ['[PHONE]', '[WEBSITE]', '[POSTAL ADDRESS]'].every((k) => sig.includes(k) && txt.includes(k)) ? ok('signature (HTML and text) carries [PHONE], [WEBSITE] and [POSTAL ADDRESS]') : bad('signature placeholders');
  fb && out.includes(fb.trim().replace(/"/g, '&quot;').replace(/'/g, "'")) || (fb && out.includes(fb.trim())) ? ok('outreach signature carries the legal pack\'s Footer B line verbatim') : bad('Footer B line missing or changed');
  const fbjs = fs.readFileSync(path.join(ROOT, 'system/signature-footer.js'), 'utf8');
  fb && fbjs.includes(JSON.stringify(fb.trim()).slice(1, -1)) ? ok('details.html\'s copy of Footer B (system/signature-footer.js) matches the legal pack') : bad('system/signature-footer.js is stale: run node render/build-signature.js');
  const body = sig.slice(sig.indexOf('<table'), sig.lastIndexOf('</table>') + 8);
  body.length < 10000 && !/<style|class=/.test(body) ? ok(`signature HTML is ${body.length} characters (Gmail limit 10,000), inline styles only`) : bad('signature size or style sheet');
  const want = ['cobalt', 'paper', 'ink'].flatMap((v) => [1024, 512, 400, 320, 160, 80, 40].map((s) => [v, s]));
  const wrong = want.filter(([v, s]) => { try { return execFileSync('identify', ['-format', '%wx%h', path.join(ROOT, `avatar/avatar-${v}-${s}.png`)], { encoding: 'utf8' }) !== `${s}x${s}`; } catch (e) { return true; } });
  wrong.length ? bad('avatar sizes', JSON.stringify(wrong)) : ok('avatar PNGs exist at 1024, 512, 400, 320, 160, 80 and 40 px in three variants');

  fs.rmSync(TMP, { recursive: true, force: true });
  console.log(`----\n${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
