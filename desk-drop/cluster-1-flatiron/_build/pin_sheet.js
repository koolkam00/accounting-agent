// Review round 1 pin re-check: OpenStreetMap at zoom 19 around each listed pin, six per sheet.
// node _build/pin_sheet.js <cluster folder> <pins.json> <out prefix>
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const [dir, pinsFile, prefix] = process.argv.slice(2);
  const pins = JSON.parse(fs.readFileSync(pinsFile, 'utf8'));
  const browser = await chromium.launch();
  for (let k = 0; k < pins.length; k += 6) {
    const chunk = pins.slice(k, k + 6);
    const html = `<!doctype html><html><head><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css">
<style>body{margin:0;font:14px Arial;display:grid;grid-template-columns:repeat(3,420px);gap:8px;padding:8px;background:#fff}
.c{border:1px solid #999}.m{width:420px;height:340px}.t{padding:4px 6px;height:38px}</style></head><body>
${chunk.map((p, i) => `<div class="c"><div class="t"><b>${p.id}</b> ${p.addr}<br>${p.note}</div><div class="m" id="m${i}"></div></div>`).join('')}
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script><script>
const P=${JSON.stringify(chunk)};
P.forEach((p,i)=>{const m=L.map('m'+i,{zoomControl:false,attributionControl:false}).setView([p.lat,p.lon],19);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19}).addTo(m);
L.circleMarker([p.lat,p.lon],{radius:9,color:'#fff',weight:3,fillColor:'#B3261E',fillOpacity:1}).addTo(m);});
</script></body></html>`;
    const page = await browser.newPage({ viewport: { width: 1290, height: 2 * 390 + 24 } });
    await page.setContent(html, { waitUntil: 'networkidle' }); await page.waitForTimeout(2500);
    await page.screenshot({ path: `${prefix}-${k / 6 + 1}.png`, fullPage: true }); await page.close();
  }
  await browser.close();
})();
