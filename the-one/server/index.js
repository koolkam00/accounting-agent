// Runs the site as a regular Node server: `npm run dev` locally, or `npm start` on any host.
// (On Vercel, api/index.js is used instead.)
import express from 'express';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createApp } from './app.js';
import { ensureOwner } from './auth.js';
import { loadOwnerProfile } from './profile.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
try { process.loadEnvFile(path.join(ROOT, '.env')); } catch { /* no .env file */ }

const DEV = process.argv.includes('--dev');
const API_ONLY = process.env.API_ONLY === '1'; // used by the test suite
const PORT = /^\d+$/.test(process.env.PORT ?? '') ? Number(process.env.PORT) : 3000;
const SITE_URL = (process.env.SITE_URL || '').replace(/\/+$/, '');

// ── Owner account ────────────────────────────────────────────────────────────
let OWNER_EMAIL = (process.env.OWNER_EMAIL || '').trim();
let OWNER_PASSWORD = process.env.OWNER_PASSWORD || '';
if (!OWNER_EMAIL || !OWNER_PASSWORD) {
  if (!DEV && !API_ONLY) {
    console.error('\n  Set OWNER_EMAIL and OWNER_PASSWORD (in .env or the environment) before starting.\n');
    process.exit(1);
  }
  OWNER_EMAIL ||= 'me@example.com';
  OWNER_PASSWORD ||= 'change-me-please';
  console.warn(`\n  [dev] No OWNER_EMAIL/OWNER_PASSWORD set. Sign in as ${OWNER_EMAIL} / ${OWNER_PASSWORD}\n`);
}
if (OWNER_PASSWORD.length < 8) {
  console.error('\n  OWNER_PASSWORD must be at least 8 characters.\n');
  process.exit(1);
}

// ── Storage: Postgres if DATABASE_URL is set, otherwise a local SQLite file ───
let store;
if (process.env.DATABASE_URL) {
  const { openPgStore } = await import('./store-pg.js');
  store = openPgStore(process.env.DATABASE_URL);
} else {
  const dataDir = path.resolve(ROOT, process.env.DATA_DIR || 'data');
  fs.mkdirSync(dataDir, { recursive: true });
  const { openSqliteStore } = await import('./store-sqlite.js');
  store = openSqliteStore(path.join(dataDir, 'the-one.db'));
}
await ensureOwner(store, { email: OWNER_EMAIL, password: OWNER_PASSWORD });

let owner = await loadOwnerProfile(ROOT);
if (DEV) {
  // Pick up profile.config.js edits without a restart while developing.
  fs.watch(path.join(ROOT, 'profile.config.js'), async () => {
    try { owner = await loadOwnerProfile(ROOT); console.log('  [dev] profile.config.js reloaded'); }
    catch (err) { console.warn('  [dev] profile.config.js has an error:', err.message); }
  });
}

const app = createApp({
  store,
  getOwner: () => owner,
  dev: DEV,
  secureCookies: process.env.COOKIE_SECURE ? process.env.COOKIE_SECURE === 'true' : !DEV,
  siteUrl: SITE_URL,
  trustProxy: process.env.TRUST_PROXY ?? 'loopback, linklocal, uniquelocal',
});

app.get('/healthz', (_req, res) => res.type('text').send('ok'));
app.use('/me', express.static(path.join(ROOT, 'public', 'me'), { maxAge: '1h' }));

if (API_ONLY) {
  // Tests only need the API.
} else if (DEV) {
  const { createServer } = await import('vite');
  const vite = await createServer({ root: ROOT, server: { middlewareMode: true }, appType: 'custom' });
  app.use(vite.middlewares);
  app.use(async (req, res, next) => {
    if (req.method !== 'GET') return next();
    try {
      const html = await vite.transformIndexHtml(req.originalUrl, fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8'));
      res.type('html').send(html);
    } catch (err) {
      vite.ssrFixStacktrace(err);
      next(err);
    }
  });
} else {
  const dist = path.join(ROOT, 'dist');
  if (!fs.existsSync(path.join(dist, 'index.html'))) {
    console.error('\n  No build found. Run `npm run build` first (or `npm run dev` while developing).\n');
    process.exit(1);
  }
  const html = fs.readFileSync(path.join(dist, 'index.html'), 'utf8');
  app.use('/assets', express.static(path.join(dist, 'assets'), { immutable: true, maxAge: '1y' }));
  app.use(express.static(dist, { index: false, maxAge: '1h' }));
  app.use((req, res, next) => {
    if (req.method !== 'GET' && req.method !== 'HEAD') return next();
    res.setHeader('Cache-Control', 'no-cache');
    res.type('html').send(html);
  });
}

const server = app.listen(PORT, (err) => {
  if (err) {
    console.error(`\n  Couldn’t start on port ${PORT}: ${err.code === 'EADDRINUSE' ? 'something else is already using it.' : err.message}\n`);
    process.exit(1);
  }
  console.log(`\n  ${owner.appName} is running → http://localhost:${server.address().port}${DEV ? '  (dev mode)' : ''}\n`);
});
