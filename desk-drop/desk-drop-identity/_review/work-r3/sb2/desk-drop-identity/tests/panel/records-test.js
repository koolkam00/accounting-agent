#!/usr/bin/env node
/*
  records-test.js: the Chrome panel edits every record, not only the first (review round 1, R1-17).
  Opens the case label in a real browser page (no render.js), as the founder would:
    1. two labels load; the picker lists both; the status says which label is unfinished;
    2. choose Label 2 (reserve), type its units: the page's second label changes, the first does not;
    3. Add a label: a third label appears (a second sheet);
    4. Remove it again;
    5. a single-record template prints no "record 1:" prefix in its messages.
  Writes tests/panel/case-label-panel.png. Exit 0 when every check passes.
*/
const path = require('path');
const { chromium } = require('playwright');
const ROOT = path.resolve(__dirname, '../..');
let pass = 0, fail = 0;
const ok = (m) => { console.log('PASS  ' + m); pass++; };
const bad = (m, x) => { console.log('FAIL  ' + m + (x ? '\n      ' + x : '')); fail++; };
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  p.on('dialog', (d) => d.accept());
  await p.goto('file://' + path.join(ROOT, 'templates/case-label/case-label.html'));
  await p.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  const opts = await p.$$eval('select[data-act="rec"] option', (o) => o.map((x) => x.textContent));
  opts.length === 2 && /reserve/.test(opts[1]) ? ok(`picker lists both labels: ${opts.join(' | ')}`) : bad('picker', JSON.stringify(opts));
  const st = await p.evaluate(() => window.__DD_STATUS__.placeholders.join(' ; '));
  /Label 2: /.test(st) ? ok('status names the label each unfinished item belongs to ("Label 2: ...")') : bad('status prefix', st);
  await p.selectOption('select[data-act="rec"]', '1');
  await p.fill('input[name="units_in_case"]', '27');
  await p.waitForTimeout(300);
  const counts = await p.$$eval('.label .count .n', (n) => n.map((x) => x.textContent));
  counts[1] === '27' && counts[0] !== '27' ? ok('editing Label 2 changes only the second label') : bad('edit label 2', JSON.stringify(counts));
  await p.click('button[data-act="rec-add"]');
  await p.waitForTimeout(300);
  const sheets = await p.$$eval('.dd-sheet', (s) => s.length);
  const n3 = await p.$$eval('select[data-act="rec"] option', (o) => o.length);
  sheets === 2 && n3 === 3 ? ok('Add a label: three labels, two sheets') : bad('add label', `${sheets} sheets, ${n3} options`);
  await p.$eval('.dd-panel', (e) => { e.scrollTop = 0; });
  await p.screenshot({ path: path.join(__dirname, 'case-label-panel.png') });
  await p.click('button[data-act="rec-del"]');
  await p.waitForTimeout(300);
  const n2 = await p.$$eval('select[data-act="rec"] option', (o) => o.length);
  n2 === 2 ? ok('Remove: back to two labels') : bad('remove label', String(n2));
  await p.goto('file://' + path.join(ROOT, 'templates/report/report.html'));
  await p.waitForFunction(() => window.__DD_STATUS__ && window.__DD_STATUS__.ready);
  const msgs = await p.evaluate(() => [...window.__DD_STATUS__.errors, ...window.__DD_STATUS__.warnings, ...window.__DD_STATUS__.placeholders].join(' ; '));
  const panel = await p.$eval('.dd-panel-status', (e) => e.textContent);
  !/record \d+:/i.test(msgs + panel) ? ok('one record: no "record 1:" prefix in status or panel') : bad('record prefix', (msgs + panel).slice(0, 200));
  await b.close();
  console.log(`----\n${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
