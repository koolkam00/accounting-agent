// Lighthouse for every page: mobile (default preset) and desktop, on the site as staged
// (STAGING = true) and on the production copy written by tools/make_production.py with SAMPLE
// settings (STAGING = false), which is how SEO is judged
// (QA.md P1 to P4). Chromium comes from Playwright through CHROME_PATH.
// Usage (from website/): node tests/lighthouse.js      Writes tests/out/lighthouse/*.json and summary.json
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const { buildSample } = require('./sample_build');
const fs = require('fs');
const os = require('os');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const OUT = path.join(__dirname, 'out', 'lighthouse');
const LH = path.join(__dirname, 'node_modules', '.bin', 'lighthouse');
const PAGES = ['index', 'brands', 'offices', 'privacy', 'survey-privacy', '404'];
fs.mkdirSync(OUT, { recursive: true });

(async () => {
  // Production runs use the real production copy (tools/make_production.py) with SAMPLE settings.
  const prod = buildSample(path.join(os.tmpdir(), 'site-prod-' + Date.now()));
  const servers = [
    spawn('python3', ['-m', 'http.server', '8125', '--bind', '127.0.0.1', '--directory', path.join(ROOT, 'site')], { stdio: 'ignore' }),
    spawn('python3', ['-m', 'http.server', '8126', '--bind', '127.0.0.1', '--directory', prod], { stdio: 'ignore' }),
  ];
  await new Promise(r => setTimeout(r, 1000));
  const env = { ...process.env, CHROME_PATH: chromium.executablePath() };
  const summary = [];
  try {
    for (const [mode, port] of [['staging', 8125], ['production', 8126]]) {
      for (const preset of ['mobile', 'desktop']) {
        for (const p of PAGES) {
          const file = path.join(OUT, `${mode}-${preset}-${p}.json`);
          const args = [`http://127.0.0.1:${port}/${p}.html`, '--quiet', '--output=json', `--output-path=${file}`,
            '--only-categories=performance,accessibility,best-practices,seo', '--chrome-flags=--headless=new --no-sandbox'];
          if (preset === 'desktop') args.push('--preset=desktop');
          execFileSync(LH, args, { env, stdio: 'ignore', timeout: 180000 });
          const r = JSON.parse(fs.readFileSync(file, 'utf8'));
          const score = k => Math.round(r.categories[k].score * 100);
          const failedSeo = Object.values(r.audits).filter(a => r.categories.seo.auditRefs.some(x => x.id === a.id && x.weight > 0) && a.score !== null && a.score < 1).map(a => a.id);
          const row = { mode, preset, page: p, performance: score('performance'), accessibility: score('accessibility'), best_practices: score('best-practices'), seo: score('seo'),
            seo_failed_audits: failedSeo, lcp_ms: Math.round(r.audits['largest-contentful-paint'].numericValue), cls: +r.audits['cumulative-layout-shift'].numericValue.toFixed(3),
            tbt_ms: Math.round(r.audits['total-blocking-time'].numericValue), bytes: r.audits['total-byte-weight'].numericValue };
          summary.push(row);
          console.log([mode, preset, p, row.performance, row.accessibility, row.best_practices, row.seo, failedSeo.join('+') || '-', 'LCP ' + row.lcp_ms, 'CLS ' + row.cls].join('\t'));
          // Keep only the summary-relevant reports small: drop screenshots from the JSON.
          delete r.audits['final-screenshot']; delete r.audits['screenshot-thumbnails']; delete r.fullPageScreenshot;
          fs.writeFileSync(file, JSON.stringify(r));
        }
      }
    }
  } finally {
    servers.forEach(s => s.kill());
    fs.rmSync(prod, { recursive: true, force: true }); fs.rmSync(prod + '.config.js', { force: true });
    fs.writeFileSync(path.join(OUT, 'summary.json'), JSON.stringify(summary, null, 2));
  }
  const bad = summary.filter(r => r.performance < 95 || r.accessibility < 100 || r.best_practices < 95 ||
    (r.mode === 'production' && r.seo < 95) || (r.mode === 'staging' && r.seo_failed_audits.some(a => a !== 'is-crawlable')));
  console.log(bad.length ? `\n${bad.length} runs below the pass bar` : '\nall Lighthouse runs meet the pass bar');
  process.exitCode = bad.length ? 1 : 0;
})();
