const { chromium } = require('playwright');
const fs=require('fs');
const pins = JSON.parse(fs.readFileSync(process.argv[2]));
const lots = JSON.parse(fs.readFileSync(process.argv[3]));
const out = process.argv[4]; const z=+process.argv[5]||19;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1500, height: 640 } });
  const cells = pins.map((x,i)=>`<div class=c><div id=m${i} class=m></div><div class=l>${i+1}. ${x.label}</div></div>`).join('');
  const html = `<!doctype html><html><head><link rel=stylesheet href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css"><script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
  <style>body{margin:0;font:12px sans-serif;display:flex;flex-wrap:wrap}.c{width:300px;height:330px}.m{width:296px;height:296px;border:2px solid #333}.l{height:30px;overflow:hidden}</style></head><body>${cells}
  <script>const P=${JSON.stringify(pins)};const LOTS=${JSON.stringify(lots)};P.forEach((x,i)=>{const m=L.map('m'+i,{zoomControl:false,attributionControl:false}).setView([x.lat,x.lon],${z});L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19}).addTo(m);const f=LOTS[x.bbl];if(f)L.geoJSON(f,{style:{color:'#080',weight:3,fill:false}}).addTo(m);if(x.g)L.circleMarker([x.g[0],x.g[1]],{radius:5,color:'#00f',weight:2,fillOpacity:0.2}).addTo(m);L.circleMarker([x.lat,x.lon],{radius:7,color:'#d00',weight:3,fillOpacity:0.3}).addTo(m);});</script></body></html>`;
  await p.setContent(html, { waitUntil: 'networkidle' });
  await p.waitForTimeout(4000);
  await p.screenshot({ path: out, fullPage: true });
  await b.close();
})();
