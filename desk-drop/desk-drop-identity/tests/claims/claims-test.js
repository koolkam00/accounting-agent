#!/usr/bin/env node
/*
  claims-test.js: the shared claims net (DD.claimsIn in system/dd-template.js), phrase by phrase.
  v1.4, 2026-10-24 (review round 3, R3-02). Run from anywhere:  node tests/claims/claims-test.js
  Three groups, each phrase with its expected result:
    1. claims that must be caught: FDA's own structure or function examples, the round-3
       reviewer's 32 phrases (_review/work-r3/claims-probe.txt), and more of the same families;
    2. ordinary copy that must pass (the reviewer's two controls and more);
    3. every sentence the templates ship, in every sample and built-in data block (our own
       negations such as "No sales guarantee" included): none may be flagged.
  The net is a net, not a review. The founder still reads every sentence (USAGE-GUIDE rule 3).
*/
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '../..');
const CLAIMS = [
  // FDA, "Structure/Function Claims" (opened 2026-10-24): its three examples
  'Calcium builds strong bones.', 'Fiber maintains bowel regularity.', 'Antioxidants maintain cell integrity.',
  // the round-3 reviewer's phrases
  'Each bite promotes healthy digestion.', 'Each bite promotes digestion.', 'It aids digestion after lunch.', 'Good for your gut.', 'A gut-friendly snack.',
  'Builds strong bones.', 'Improves focus through the afternoon.', 'Helps you sleep better.', 'Lowers cholesterol.', 'Reduces bloating.',
  'Rich in antioxidants that protect your cells.', 'Good for your heart.', 'Strengthens your immune system.', 'Fuel for your brain.', 'Packed with probiotics for digestive balance.',
  'Keeps you full until dinner.', 'Gives you steady energy all afternoon.', 'Electrolytes for hydration and recovery.', 'Made to calm stress.', 'Clinically studied adaptogens.',
  'Our best flavor yet.', 'The number one jerky in Brooklyn.',
  'Sales rose 20% after the drop.', 'The campaign generated 40 new buyers.', 'Redemptions show a 3x return on spend.', 'We saw uplift at the store.', 'Converted 12% of tasters into buyers.', 'Drove trial-to-purchase of 30%.', 'Incremental sales of 31 units.',
  // the reviewer's report sentences, end to end in _review/work-r3/data/r3-claim-report.json
  'Sales rose 20% at the Union Square store after the drop.', 'The card converted 12% of tasters into buyers.', 'We saw clear uplift and a 3x return on spend.',
  // the reviewer's card sentence (r3-claim-card.json)
  'The fiber maintains bowel regularity and promotes digestion.',
  // the CONTRACTS section 4 examples and round 2's list (kept)
  'Each bite supports gut health.', 'Each bite boosts immunity.', 'A healthy snack for your desk.', 'Guaranteed to be the best you have tried.',
  'The campaign drove a 20% sales lift.', 'It acquired new customers.', 'Renew. Guaranteed to grow sales.',
  // more of the same families
  'A better-for-you chip.', 'Guilt-free snacking.', 'Soothes your stomach after a big lunch.', 'Helps keep your energy up.', 'Supports a healthy heart.',
  'Nourishing ingredients only.', 'A nutritious afternoon pick-me-up.', 'Reduces the risk of heart disease.', 'Helps prevent colds.', 'Made for recovery after the gym.',
  'Our #1 seller.', 'The best-selling bar in Brooklyn.', 'The drop lifted sales at Whole Foods.', 'Velocity jumped the week of the drop.', 'Revenue doubled in February.',
  'A 2.5x return on investment.', 'Our ROI was strong.', 'Drove trial across ten offices.', 'Clinically proven.', 'Doctor-recommended.', 'Sales up 30% in the cluster.',
  'Real lift at the nearest store.', 'This campaign converts tasters into fans.', 'Lifts your mood.', 'Promotes a sense of calm.', 'Elevates your mood at 3 pm.'
];
const PLAIN = [
  'Lift the lid and take one.', 'A resealable bag prevents crumbs at your desk.', 'We bake in a converted Brooklyn warehouse.', 'Best by 2027-03-01.', 'Best before the date on the bag.',
  'Two friends bake these in Queens.', 'Lift up the flap.', 'We started making jerky in 2019 because we could not find one we liked.',
  'Sea salt, olive oil and lentils, nothing else.', 'Brewed in small batches in Red Hook.', 'Take one. Tell us what you think.', 'A family recipe from Oaxaca.',
  'We keep our focus on flavor.', 'It delivers the full flavor of the pepper.', 'Made for the 3 pm slump at your desk.', 'Find it at Whole Foods Market Union Square.',
  'Incremental: not measured.', 'Incremental sales are not measured.', 'We do not claim lift.', 'No sales guarantee.', 'We never promise: sales, lift or new customers.',
  'Zero cholesterol per serving.', 'Redemptions: 19 codes used by day 30.', 'Eleven of twelve offices placed it on day 1.', 'The pantry at office D ran out on day 3.',
  'Three offices asked for a second flavor.', 'Our first two campaigns ran in the same week.', 'Most comments named the crunch.', 'Give it a try.',
  'Hand-cooked in small batches, so each chip stays crisp.', 'Our cold brew gives you a smooth cup with no bitterness.', 'Helps you find a snack you like.', 'Supports small farms in the Hudson Valley.',
  'We protect the chips from breaking with a stiff box.', 'A balanced blend of sweet and salty.', 'Reduces waste: the bag is compostable.', 'Made with ingredients you can pronounce.', 'A treat for the whole team.', 'Lift the tab to open.'
];
const NUTRIENT = ['10g protein per bar.', 'Low sugar.', 'With electrolytes.', 'Zero cholesterol per serving.'];

// group 3: every shipped sentence the claims check reads
const CHECKED = {
  'tent-card': ['card_sentences', 'product_name', 'brand_name'], 'proposal': ['product_sku'], 'report': ['learned', 'recommendation', 'retailer_velocity'],
  'office-one-pager': ['headline', 'lead', 'gets', 'gives', 'steps', 'product', 'founding', 'next'],
  'brand-one-pager': ['headline', 'lead', 'includes', 'ladder_note', 'fit', 'send', 'next', 'roster_status'],
  'discovery-one-pager': ['s1', 's2', 's3', 's4', 's5']
};
const MUST_FLAG_FILES = /must-block|claim/i;   // samples built to be refused
const shipped = [];
for (const [t, keys] of Object.entries(CHECKED)) {
  const dir = path.join(ROOT, 'templates', t);
  const files = fs.readdirSync(path.join(dir, 'samples')).filter((f) => f.endsWith('.json')).map((f) => path.join(dir, 'samples', f));
  const blocks = [];
  for (const f of files) if (!MUST_FLAG_FILES.test(path.basename(f))) blocks.push([path.relative(ROOT, f), JSON.parse(fs.readFileSync(f, 'utf8'))]);
  const html = fs.readFileSync(path.join(dir, t + '.html'), 'utf8');
  blocks.push([`templates/${t}/${t}.html (built-in data)`, JSON.parse(/<script type="application\/json" id="dd-data">([\s\S]*?)<\/script>/.exec(html)[1])]);
  for (const [name, d] of blocks) for (const rec of (Array.isArray(d) ? d : [d])) for (const k of keys) if (typeof rec[k] === 'string' && rec[k].trim()) shipped.push([`${name} ${k}`, rec[k]]);
}
for (const f of fs.readdirSync(path.join(ROOT, 'tests/documents/cases'))) {
  if (!f.endsWith('.json')) continue;
  const d = JSON.parse(fs.readFileSync(path.join(ROOT, 'tests/documents/cases', f), 'utf8'));
  for (const k of ['learned', 'recommendation', 'retailer_velocity', 'product_sku', 'headline', 'lead', 'includes', 'ladder_note', 'fit', 'send', 'next', 'roster_status']) if (typeof d[k] === 'string' && d[k].trim()) shipped.push([`tests/documents/cases/${f} ${k}`, d[k]]);
}

(async () => {
  const { chromium } = require('playwright');
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + path.join(ROOT, 'templates/tent-card/tent-card.html'));
  await p.waitForFunction(() => window.DD && window.DD.claimsIn);
  const run = (arr) => p.evaluate((a) => a.map((s) => [s, DD.claimsIn(s), DD.nutrientIn(s)]), arr);
  let pass = 0, fail = 0; const log = [];
  for (const [s, c] of await run(CLAIMS)) { if (c.length) pass++; else { fail++; log.push(`MISSED a claim: ${s}`); } }
  for (const [s, c] of await run(PLAIN)) { if (!c.length) pass++; else { fail++; log.push(`FLAGGED plain copy: ${s}  -> ${JSON.stringify(c)}`); } }
  for (const [s, c, nu] of await run(NUTRIENT)) { if (!c.length && nu.length) pass++; else { fail++; log.push(`nutrient wording should warn, not refuse: ${s} -> claims ${JSON.stringify(c)}, nutrient ${JSON.stringify(nu)}`); } }
  const sh = await run(shipped.map(([, v]) => v));
  sh.forEach(([s, c], k) => { if (!c.length) pass++; else { fail++; log.push(`FLAGGED shipped copy (${shipped[k][0]}): ${JSON.stringify(c)} in "${s.slice(0, 120)}"`); } });
  await b.close();
  log.forEach((l) => console.log('FAIL  ' + l));
  console.log(`claims net: ${CLAIMS.length} claims caught ${CLAIMS.length - log.filter((l) => l.startsWith('MISSED')).length}; ${PLAIN.length} plain phrases, ${log.filter((l) => l.startsWith('FLAGGED plain')).length} flagged; ${NUTRIENT.length} nutrient lines; ${shipped.length} shipped sentences, ${log.filter((l) => l.startsWith('FLAGGED shipped')).length} flagged`);
  console.log(`----\n${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
