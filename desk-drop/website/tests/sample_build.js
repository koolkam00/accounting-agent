// Builds a production copy of site/ with SAMPLE settings, the way the founder's publish step does
// (tools/make_production.py), so tests can check the copy that would be uploaded.
// Used by e2e.js and lighthouse.js.  buildSample(outDir, { brandName, foundingClosed }) -> outDir
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const ROOT = path.join(__dirname, '..');

function sampleConfig(brandName, foundingClosed) {
  const swaps = [
    [/DOMAIN: "\[DOMAIN\]"/, 'DOMAIN: "sample.example"'],
    [/CONTACT_EMAIL: "\[EMAIL\]"/, 'CONTACT_EMAIL: "hello@sample.example"'],
    [/PHONE: "\[PHONE\]"/, 'PHONE: ""'],
    [/POSTAL_ADDRESS: "\[POSTAL ADDRESS\]"/, 'POSTAL_ADDRESS: "SAMPLE 1 Example Street, New York, NY 10010"'],
    [/FOUNDER_NAME: "\[FOUNDER NAME\]"/, 'FOUNDER_NAME: "SAMPLE Founder"'],
    [/FOUNDER_LINKEDIN: "\[LINKEDIN URL\]"/, 'FOUNDER_LINKEDIN: "https://www.linkedin.com/in/sample-founder"'],
    [/COMPANY_LEGAL_NAME: "\[COMPANY NAME\]"/, 'COMPANY_LEGAL_NAME: "SAMPLE Company LLC"'],
  ];
  if (brandName) swaps.push([/BRAND_NAME: "[^"]*"/, `BRAND_NAME: "${brandName}"`]);
  if (foundingClosed) swaps.push([/FOUNDING_TIER_OPEN: true/, 'FOUNDING_TIER_OPEN: false']);
  let c = fs.readFileSync(path.join(ROOT, 'site', 'site.config.js'), 'utf8');
  for (const [re, val] of swaps) { if (!re.test(c)) throw new Error('config pattern not found: ' + re); c = c.replace(re, val); }
  return c;
}

function buildSample(outDir, opts = {}) {
  fs.mkdirSync(path.dirname(outDir), { recursive: true });
  const cfg = outDir + '.config.js';
  fs.writeFileSync(cfg, sampleConfig(opts.brandName, opts.foundingClosed));
  execFileSync('python3', [path.join(ROOT, 'tools', 'make_production.py'), '--draft', '--out', outDir, '--config', cfg], { stdio: 'ignore' });
  return outDir;
}
module.exports = { buildSample, sampleConfig };
