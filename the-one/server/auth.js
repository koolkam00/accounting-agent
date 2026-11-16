import crypto from 'node:crypto';
import { promisify } from 'node:util';
import { newId, now } from './util.js';

const scrypt = promisify(crypto.scrypt);
const SCRYPT = { N: 16384, r: 8, p: 1, maxmem: 64 * 1024 * 1024 };
const SESSION_DAYS = 60;
export const COOKIE_NAME = 'one_sid';

export async function hashPassword(password) {
  const salt = crypto.randomBytes(16);
  const hash = await scrypt(password.normalize('NFKC'), salt, 64, SCRYPT);
  return ['scrypt', SCRYPT.N, SCRYPT.r, SCRYPT.p, salt.toString('base64url'), hash.toString('base64url')].join('$');
}

export async function verifyPassword(password, stored) {
  const [alg, N, r, p, saltB64, hashB64] = String(stored).split('$');
  if (alg !== 'scrypt' || !saltB64 || !hashB64) return false;
  const expected = Buffer.from(hashB64, 'base64url');
  const actual = await scrypt(String(password).normalize('NFKC'), Buffer.from(saltB64, 'base64url'), expected.length, {
    N: Number(N), r: Number(r), p: Number(p), maxmem: SCRYPT.maxmem,
  });
  return actual.length === expected.length && crypto.timingSafeEqual(actual, expected);
}

// Compared against when an email has no account, so timing doesn't reveal which emails exist.
let dummyHash;
export async function dummyVerify(password) {
  dummyHash ??= await hashPassword('not-a-real-password');
  await verifyPassword(password, dummyHash);
  return false;
}

export const tokenHash = (token) => crypto.createHash('sha256').update(String(token)).digest('base64url');

export async function createSession(store, userId) {
  const token = crypto.randomBytes(32).toString('base64url');
  const t = now();
  await store.run('DELETE FROM sessions WHERE expires_at < ?', [t]);
  await store.run('INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)',
    [tokenHash(token), userId, t, t + SESSION_DAYS * 86400_000]);
  return token;
}

export async function destroySession(store, token) {
  if (token) await store.run('DELETE FROM sessions WHERE token_hash = ?', [tokenHash(token)]);
}

export async function userForToken(store, token) {
  if (!token) return null;
  const row = await store.one(`
    SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
    WHERE s.token_hash = ? AND s.expires_at > ?`, [tokenHash(token), now()]);
  return row ?? null;
}

export function parseCookies(header = '') {
  const out = {};
  for (const part of header.split(';')) {
    const i = part.indexOf('=');
    if (i < 0) continue;
    const k = part.slice(0, i).trim();
    if (!k) continue;
    try { out[k] = decodeURIComponent(part.slice(i + 1).trim()); } catch { /* ignore malformed */ }
  }
  return out;
}

export function sessionCookie(token, { secure }) {
  const attrs = [`${COOKIE_NAME}=${token}`, 'Path=/', 'HttpOnly', 'SameSite=Lax', `Max-Age=${SESSION_DAYS * 86400}`];
  if (secure) attrs.push('Secure');
  return attrs.join('; ');
}

export function clearCookie({ secure }) {
  return `${COOKIE_NAME}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0${secure ? '; Secure' : ''}`;
}

/**
 * Make sure the owner account exists, using OWNER_EMAIL / OWNER_PASSWORD.
 *
 * The env values are applied when the owner is first created and again whenever
 * they change (that's how you reset a forgotten password). If they haven't changed,
 * a login you updated inside the app is left alone.
 */
export async function ensureOwner(store, { email, password }) {
  const envEmail = String(email).trim().toLowerCase();
  const owner = await store.one("SELECT * FROM users WHERE role = 'owner'");
  const markerRow = await store.one("SELECT value FROM settings WHERE key = 'owner_env'");
  let marker = null;
  try { marker = markerRow ? JSON.parse(markerRow.value) : null; } catch { marker = null; }
  if (owner && marker?.email === envEmail && await verifyPassword(password, marker.hash)) return { changed: false };

  const hash = await hashPassword(password);
  try {
    await store.tx(async (q) => {
      if (!owner) {
        await q.run(`INSERT INTO users (id, email, password_hash, role, onboarded, created_at)
                     VALUES (?, ?, ?, 'owner', 1, ?)`, [newId(), envEmail, hash, now()]);
      } else {
        await q.run('UPDATE users SET email = ?, password_hash = ? WHERE id = ?', [envEmail, hash, owner.id]);
        await q.run('DELETE FROM sessions WHERE user_id = ?', [owner.id]);
      }
      await q.run(`INSERT INTO settings (key, value) VALUES ('owner_env', ?)
                   ON CONFLICT (key) DO UPDATE SET value = excluded.value`, [JSON.stringify({ email: envEmail, hash })]);
    });
  } catch (err) {
    // Two cold starts racing to create the owner: the loser can stop here.
    const exists = await store.one("SELECT 1 AS ok FROM users WHERE role = 'owner'");
    if (owner || !exists) throw err;
  }
  return { changed: true };
}

/** Tiny fixed-window rate limiter, keyed by whatever the caller chooses. */
export function rateLimiter({ windowMs, max }) {
  const hits = new Map();
  const sweep = setInterval(() => {
    const t = Date.now();
    for (const [k, v] of hits) if (v.reset < t) hits.delete(k);
  }, windowMs);
  sweep.unref?.();
  return (key) => {
    const t = Date.now();
    let entry = hits.get(key);
    if (!entry || entry.reset < t) {
      entry = { count: 0, reset: t + windowMs };
      hits.set(key, entry);
    }
    entry.count += 1;
    return entry.count <= max;
  };
}
