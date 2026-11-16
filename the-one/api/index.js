// Vercel entry point: the whole API runs as one serverless function.
// Needs DATABASE_URL (Postgres), OWNER_EMAIL and OWNER_PASSWORD in the project's environment variables.
import { createApp } from '../server/app.js';
import { ensureOwner } from '../server/auth.js';
import { openPgStore } from '../server/store-pg.js';
import { normalizeProfile } from '../server/profile.js';
import profileConfig from '../profile.config.js';

const owner = normalizeProfile(profileConfig);
const productionUrl = process.env.VERCEL_PROJECT_PRODUCTION_URL;
const siteUrl = (process.env.SITE_URL || (productionUrl ? `https://${productionUrl}` : '')).replace(/\/+$/, '');

let store;
let ready;

function init() {
  ready ??= (async () => {
    const email = (process.env.OWNER_EMAIL || '').trim();
    const password = process.env.OWNER_PASSWORD || '';
    if (!email || password.length < 8) throw new Error('Set OWNER_EMAIL and OWNER_PASSWORD (8+ characters).');
    store ??= openPgStore(process.env.DATABASE_URL);
    await ensureOwner(store, { email, password });
    return createApp({
      store,
      getOwner: () => owner,
      secureCookies: true,
      siteUrl,
      trustProxy: true,
      // Vercel sets x-real-ip to the visitor's address and doesn't pass through spoofed values.
      clientIp: (req) => req.headers['x-real-ip'] || req.ip,
    });
  })().catch((err) => {
    ready = undefined;
    throw err;
  });
  return ready;
}

export default async function handler(req, res) {
  let app;
  try {
    app = await init();
  } catch (err) {
    console.error('[startup]', err);
    res.statusCode = 503;
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Cache-Control', 'no-store');
    res.end(JSON.stringify({ error: 'The site is having trouble starting. Try again in a moment.' }));
    return;
  }
  app(req, res);
}
