const { chromium } = require('playwright');
const OUT='/tmp/claude-0/-home-user-accounting-agent/35161228-045e-5c59-97cb-d166fe4ca4c5/scratchpad/r3/';
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const p = await ctx.newPage();
  const errs=[]; p.on('pageerror',e=>errs.push('pageerror '+e.message)); p.on('console',m=>{if(m.type()==='error')errs.push('console '+m.text())});
  await p.goto('file:///home/user/accounting-agent/desk-drop/cluster-1-flatiron/map-private.html', { waitUntil: 'networkidle' });
  await p.waitForTimeout(3000);
  const sw=await p.evaluate(()=>[document.documentElement.scrollWidth, document.body.scrollWidth, innerWidth]);
  console.log('scrollWidth',sw);
  await p.screenshot({ path: OUT+'r3-phone-default.png' });
  // Key
  await p.tap('#btnKey'); await p.waitForTimeout(800);
  await p.screenshot({ path: OUT+'r3-phone-key.png' });
  await p.tap('#btnKey'); await p.waitForTimeout(500);
  // Find 381 Park
  await p.tap('#btnFind'); await p.waitForTimeout(500);
  await p.fill('#q','381 Park'); await p.waitForTimeout(800);
  await p.screenshot({ path: OUT+'r3-phone-find.png' });
  const items = await p.$$('#results div');
  console.log('results', items.length);
  if(items.length){ await items[0].tap(); await p.waitForTimeout(2500); }
  await p.screenshot({ path: OUT+'r3-phone-popup-381pas.png' });
  const pop = await p.evaluate(()=>{const w=document.querySelector('.leaflet-popup'); if(!w) return null; const r=w.getBoundingClientRect(); const sc=w.querySelector('[style*="overflow"], .list, .scroll'); return {top:r.top,bottom:r.bottom,left:r.left,right:r.right,text:w.innerText.slice(0,600)}});
  console.log('popup381', JSON.stringify(pop));
  // close popup
  await p.evaluate(()=>{const c=document.querySelector('.leaflet-popup-close-button'); if(c) c.click();});
  // Find 215 Park
  await p.tap('#btnFind'); await p.waitForTimeout(400);
  await p.fill('#q','215 Park'); await p.waitForTimeout(800);
  const it2 = await p.$$('#results div'); console.log('results215', it2.length);
  if(it2.length){ await it2[0].tap(); await p.waitForTimeout(2500); }
  await p.screenshot({ path: OUT+'r3-phone-popup-215pas.png' });
  const pop2 = await p.evaluate(()=>{const w=document.querySelector('.leaflet-popup'); if(!w) return null; const r=w.getBoundingClientRect(); return {top:r.top,bottom:r.bottom,left:r.left,right:r.right,text:w.innerText.slice(0,900)}});
  console.log('popup215', JSON.stringify(pop2));
  await p.evaluate(()=>{const c=document.querySelector('.leaflet-popup-close-button'); if(c) c.click();});
  // walk session 5
  await p.tap('#btnFind'); await p.waitForTimeout(400);
  const opts = await p.$$eval('#sess option', os=>os.map(o=>o.value+'|'+o.textContent));
  console.log('sess options', opts.join(' ; '));
  await p.selectOption('#sess', opts[5].split('|')[0]); await p.waitForTimeout(2500);
  // hide panel if open
  await p.screenshot({ path: OUT+'r3-phone-walk5.png' });
  console.log('errors', errs.join('\n'));
  await b.close();
})();
