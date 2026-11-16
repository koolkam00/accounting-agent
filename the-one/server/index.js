import express from 'express';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { openDb, newId, now, tx } from './db.js';
import * as auth from './auth.js';
import { decodeImage, saveImage, removeImage } from './images.js';
import { loadOwnerProfile, snapshotFor, ageFrom, formatHeight, LOOKING_FOR, DATE_IDEAS } from './profile.js';
import { notify } from './notify.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
try { process.loadEnvFile(path.join(ROOT, '.env')); } catch { /* no .env file */ }

const DEV = process.argv.includes('--dev');
const API_ONLY = process.env.API_ONLY === '1'; // used by the test suite
const PORT = /^\d+$/.test(process.env.PORT ?? '') ? Number(process.env.PORT) : 3000;
const DATA_DIR = path.resolve(ROOT, process.env.DATA_DIR || 'data');
const UPLOADS = path.join(DATA_DIR, 'uploads');
const SITE_URL = (process.env.SITE_URL || '').replace(/\/+$/, '');
const SECURE_COOKIES = process.env.COOKIE_SECURE ? process.env.COOKIE_SECURE === 'true' : !DEV;
fs.mkdirSync(UPLOADS, { recursive: true });

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

const db = openDb(path.join(DATA_DIR, 'the-one.db'));
await auth.ensureOwner(db, { email: OWNER_EMAIL, password: OWNER_PASSWORD });
let owner = await loadOwnerProfile(ROOT);

if (DEV) {
  // Pick up profile.config.js edits without a restart while developing.
  fs.watch(path.join(ROOT, 'profile.config.js'), async () => {
    try { owner = await loadOwnerProfile(ROOT); console.log('  [dev] profile.config.js reloaded'); }
    catch (err) { console.warn('  [dev] profile.config.js has an error:', err.message); }
  });
}

// ── Helpers ──────────────────────────────────────────────────────────────────
class HttpError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}
const fail = (status, message) => { throw new HttpError(status, message); };
const str = (v, max) => String(v ?? '').trim().slice(0, max);
const json = (s, fallback) => { try { return JSON.parse(s); } catch { return fallback; } };
const ownerRow = () => db.prepare("SELECT * FROM users WHERE role = 'owner'").get();

const siteInfo = () => ({
  appName: owner.appName,
  ownerName: owner.name,
  ownerAge: owner.age,
  pronoun: owner.pronoun,
  heroPhoto: owner.photos[0]?.src ?? null,
  minPhotos: owner.minPhotos,
  lookingFor: LOOKING_FOR,
});

const photosOf = (userId) => db.prepare('SELECT id FROM photos WHERE user_id = ? ORDER BY position').all(userId)
  .map((p) => ({ id: p.id, src: `/api/photos/${p.id}` }));

const likeOf = (userId) => db.prepare('SELECT * FROM likes WHERE user_id = ?').get(userId);

function publicLike(like, { forOwner = false } = {}) {
  if (!like) return null;
  let status = like.status;
  // Members never find out they were passed on; it just stays "sent".
  if (!forOwner && status === 'removed') status = 'pending';
  return {
    id: like.id,
    targetType: like.target_type,
    targetRef: like.target_ref,
    snapshot: json(like.target_snapshot, {}),
    comment: like.comment,
    dateIdea: like.date_idea,
    status,
    createdAt: like.created_at,
    decidedAt: like.decided_at,
    matchSeen: !!like.match_seen,
  };
}

function memberProfile(user) {
  const p = json(user.profile, {});
  const facts = [
    p.height && { key: 'height', value: formatHeight(p.height) },
    p.location && { key: 'location', value: p.location },
    p.job && { key: 'job', value: p.job },
    p.school && { key: 'school', value: p.school },
    p.lookingFor && { key: 'lookingFor', value: p.lookingFor },
    p.instagram && { key: 'instagram', value: `@${p.instagram}` },
  ].filter(Boolean);
  return {
    id: user.id,
    name: user.first_name,
    age: ageFrom(user.birthdate),
    photos: photosOf(user.id),
    prompts: (p.prompts ?? []).map((q, i) => ({ id: `q${i}`, question: q.question, answer: q.answer })),
    facts,
    joinedAt: user.created_at,
  };
}

function unreadFor(memberId, { forOwner }) {
  return db.prepare('SELECT COUNT(*) AS n FROM messages WHERE member_id = ? AND from_owner = ? AND read_at IS NULL')
    .get(memberId, forOwner ? 0 : 1).n;
}

function serializeSelf(user) {
  if (user.role === 'owner') {
    const pending = db.prepare("SELECT COUNT(*) AS n FROM likes WHERE status = 'pending'").get().n;
    const fresh = db.prepare("SELECT COUNT(*) AS n FROM likes WHERE status = 'pending' AND seen_by_owner = 0").get().n;
    const unread = db.prepare(`
      SELECT COUNT(*) AS n FROM messages m JOIN likes l ON l.user_id = m.member_id
      WHERE l.status = 'matched' AND m.from_owner = 0 AND m.read_at IS NULL`).get().n;
    return { id: user.id, role: 'owner', email: user.email, firstName: owner.name, counts: { pending, fresh, unread } };
  }
  const p = json(user.profile, {});
  const like = likeOf(user.id);
  return {
    id: user.id,
    role: 'member',
    email: user.email,
    firstName: user.first_name,
    birthdate: user.birthdate,
    age: ageFrom(user.birthdate),
    profile: {
      location: p.location ?? '', job: p.job ?? '', school: p.school ?? '', height: p.height ?? null,
      instagram: p.instagram ?? '', lookingFor: p.lookingFor ?? '', prompts: p.prompts ?? [],
    },
    photos: photosOf(user.id),
    onboarded: !!user.onboarded,
    like: publicLike(like),
    unread: like?.status === 'matched' ? unreadFor(user.id, { forOwner: false }) : 0,
  };
}

function threadMessages(memberId, viewerIsOwner) {
  return db.prepare('SELECT * FROM messages WHERE member_id = ? ORDER BY created_at, rowid').all(memberId)
    .map((m) => ({ id: m.id, mine: !!m.from_owner === viewerIsOwner, body: m.body, createdAt: m.created_at, readAt: m.read_at }));
}

function markRead(memberId, { byOwner }) {
  db.prepare('UPDATE messages SET read_at = ? WHERE member_id = ? AND from_owner = ? AND read_at IS NULL')
    .run(now(), memberId, byOwner ? 0 : 1);
}

function postMessage(memberId, fromOwner, rawBody) {
  const body = str(rawBody, 2000);
  if (!body) fail(400, 'Write something first.');
  const msg = { id: newId(), created_at: now() };
  db.prepare('INSERT INTO messages (id, member_id, from_owner, body, created_at) VALUES (?, ?, ?, ?, ?)')
    .run(msg.id, memberId, fromOwner ? 1 : 0, body, msg.created_at);
  return { id: msg.id, mine: true, body, createdAt: msg.created_at, readAt: null };
}

function deleteUserPhotos(userId) {
  for (const p of db.prepare('SELECT file FROM photos WHERE user_id = ?').all(userId)) removeImage(UPLOADS, p.file);
}

// ── Rate limits ──────────────────────────────────────────────────────────────
const limits = {
  login: auth.rateLimiter({ windowMs: 15 * 60_000, max: 30 }),
  signup: auth.rateLimiter({ windowMs: 60 * 60_000, max: 30 }), // generous: phones on one carrier often share an IP
  write: auth.rateLimiter({ windowMs: 60_000, max: 60 }),
};
const limit = (name, keyFn = (req) => req.ip) => (req, _res, next) => {
  if (!limits[name](`${name}:${keyFn(req)}`)) fail(429, 'Slow down a little and try again in a bit.');
  next();
};

// ── App ──────────────────────────────────────────────────────────────────────
const app = express();
app.disable('x-powered-by');
app.set('trust proxy', process.env.TRUST_PROXY ?? 'loopback, linklocal, uniquelocal');

app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Referrer-Policy', 'same-origin');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
  if (!DEV) {
    res.setHeader('Content-Security-Policy', [
      "default-src 'self'", "img-src 'self' data: blob:", "style-src 'self' 'unsafe-inline'",
      "font-src 'self' data:", "script-src 'self'", "connect-src 'self'", "frame-ancestors 'none'",
      "base-uri 'self'", "form-action 'self'", "object-src 'none'",
    ].join('; '));
  }
  next();
});

app.get('/healthz', (_req, res) => res.type('text').send('ok'));

const api = express.Router();
api.use(express.json({ limit: '9mb' }));

// Who's asking?
api.use((req, _res, next) => {
  req.sessionToken = auth.parseCookies(req.headers.cookie)[auth.COOKIE_NAME];
  req.user = auth.userForToken(db, req.sessionToken);
  if (req.user && (!req.user.last_seen_at || now() - req.user.last_seen_at > 60_000)) {
    db.prepare('UPDATE users SET last_seen_at = ? WHERE id = ?').run(now(), req.user.id);
  }
  next();
});

// CSRF: state-changing requests must come from our own JS (custom header ⇒ no cross-site forms).
api.use((req, _res, next) => {
  if (req.method !== 'GET' && req.method !== 'HEAD' && req.get('x-requested-with') !== 'the-one') {
    fail(403, 'Bad request origin.');
  }
  next();
});

const requireUser = (req, _res, next) => { if (!req.user) fail(401, 'Please sign in.'); next(); };
const requireMember = (req, _res, next) => {
  if (!req.user) fail(401, 'Please sign in.');
  if (req.user.role !== 'member') fail(403, 'That’s for visitors.');
  next();
};
const requireOnboarded = (req, _res, next) => { if (!req.user.onboarded) fail(403, 'Finish your profile first.'); next(); };
const requireOwner = (req, _res, next) => {
  if (!req.user) fail(401, 'Please sign in.');
  if (req.user.role !== 'owner') fail(403, 'Not allowed.');
  next();
};

api.get('/session', (req, res) => {
  res.json({ site: siteInfo(), user: req.user ? serializeSelf(req.user) : null });
});

// ── Auth ─────────────────────────────────────────────────────────────────────
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

api.post('/auth/signup', limit('signup'), async (req, res) => {
  const email = str(req.body?.email, 200).toLowerCase();
  const password = String(req.body?.password ?? '');
  if (!EMAIL_RE.test(email)) fail(400, 'That email doesn’t look right.');
  if (password.length < 8) fail(400, 'Use at least 8 characters for your password.');
  if (password.length > 200) fail(400, 'That password is a bit too long.');
  if (db.prepare('SELECT 1 FROM users WHERE email = ?').get(email)) {
    fail(409, 'There’s already an account with that email. Try signing in.');
  }
  const id = newId();
  db.prepare('INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)')
    .run(id, email, await auth.hashPassword(password), now());
  const token = auth.createSession(db, id);
  res.setHeader('Set-Cookie', auth.sessionCookie(token, { secure: SECURE_COOKIES }));
  res.json({ user: serializeSelf(db.prepare('SELECT * FROM users WHERE id = ?').get(id)) });
});

api.post('/auth/login', limit('login'), async (req, res) => {
  const email = str(req.body?.email, 200).toLowerCase();
  const password = String(req.body?.password ?? '');
  const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email);
  const ok = user ? await auth.verifyPassword(password, user.password_hash) : await auth.dummyVerify(password);
  if (!ok) fail(401, 'That email and password don’t match.');
  const token = auth.createSession(db, user.id);
  res.setHeader('Set-Cookie', auth.sessionCookie(token, { secure: SECURE_COOKIES }));
  res.json({ user: serializeSelf(user) });
});

api.post('/auth/logout', (req, res) => {
  auth.destroySession(db, req.sessionToken);
  res.setHeader('Set-Cookie', auth.clearCookie({ secure: SECURE_COOKIES }));
  res.json({ ok: true });
});

// ── Member: own profile ──────────────────────────────────────────────────────
api.patch('/me', requireMember, limit('write', (req) => req.user.id), (req, res) => {
  const b = req.body ?? {};
  const user = req.user;
  const profile = json(user.profile, {});
  let firstName = user.first_name;
  let birthdate = user.birthdate;

  if ('firstName' in b) {
    firstName = str(b.firstName, 30);
    if (!firstName) fail(400, 'Add your first name.');
  }
  if ('birthdate' in b) {
    birthdate = str(b.birthdate, 10);
    const age = ageFrom(birthdate);
    if (age === null || age > 100) fail(400, 'Enter a real birthday.');
    if (age < 18) fail(400, 'You need to be 18 or older to use this site.');
  }
  for (const k of ['location', 'job', 'school']) if (k in b) profile[k] = str(b[k], 60);
  if ('instagram' in b) profile.instagram = str(b.instagram, 40).replace(/^@+/, '').replace(/[^A-Za-z0-9._]/g, '').slice(0, 30);
  if ('height' in b) {
    const h = b.height === null || b.height === '' ? null : Math.round(Number(b.height));
    if (h !== null && !(h >= 48 && h <= 96)) fail(400, 'Pick a height from the list.');
    profile.height = h;
  }
  if ('lookingFor' in b) {
    if (b.lookingFor && !LOOKING_FOR.includes(b.lookingFor)) fail(400, 'Pick one of the options.');
    profile.lookingFor = b.lookingFor || '';
  }
  if ('prompts' in b) {
    if (!Array.isArray(b.prompts)) fail(400, 'Prompts look wrong.');
    profile.prompts = b.prompts
      .map((p) => ({ question: str(p?.question, 80), answer: str(p?.answer, 200) }))
      .filter((p) => p.question && p.answer)
      .slice(0, 3);
  }

  let onboarded = user.onboarded;
  if (b.onboarded === true && !onboarded) {
    const photoCount = db.prepare('SELECT COUNT(*) AS n FROM photos WHERE user_id = ?').get(user.id).n;
    if (!firstName) fail(400, 'Add your first name.');
    if (!birthdate) fail(400, 'Add your birthday.');
    if (photoCount < owner.minPhotos) fail(400, `Add at least ${owner.minPhotos} photo${owner.minPhotos === 1 ? '' : 's'}.`);
    onboarded = 1;
  }

  db.prepare('UPDATE users SET first_name = ?, birthdate = ?, profile = ?, onboarded = ? WHERE id = ?')
    .run(firstName, birthdate, JSON.stringify(profile), onboarded, user.id);
  res.json({ user: serializeSelf(db.prepare('SELECT * FROM users WHERE id = ?').get(user.id)) });
});

api.post('/me/photos', requireMember, limit('write', (req) => req.user.id), (req, res) => {
  const count = db.prepare('SELECT COUNT(*) AS n FROM photos WHERE user_id = ?').get(req.user.id).n;
  if (count >= 6) fail(400, 'You can add up to 6 photos.');
  const image = decodeImage(req.body?.dataUrl);
  const id = newId();
  const file = saveImage(UPLOADS, id, image);
  const pos = db.prepare('SELECT COALESCE(MAX(position), -1) + 1 AS p FROM photos WHERE user_id = ?').get(req.user.id).p;
  db.prepare('INSERT INTO photos (id, user_id, position, file, mime, created_at) VALUES (?, ?, ?, ?, ?, ?)')
    .run(id, req.user.id, pos, file, image.mime, now());
  res.json({ photos: photosOf(req.user.id) });
});

api.delete('/me/photos/:id', requireMember, (req, res) => {
  const photo = db.prepare('SELECT * FROM photos WHERE id = ? AND user_id = ?').get(req.params.id, req.user.id);
  if (!photo) fail(404, 'Photo not found.');
  const count = db.prepare('SELECT COUNT(*) AS n FROM photos WHERE user_id = ?').get(req.user.id).n;
  if (req.user.onboarded && count <= Math.max(1, owner.minPhotos)) {
    fail(400, 'Add another photo before removing this one.');
  }
  tx(db, () => {
    db.prepare('DELETE FROM photos WHERE id = ?').run(photo.id);
    db.prepare('SELECT id FROM photos WHERE user_id = ? ORDER BY position').all(req.user.id)
      .forEach((p, i) => db.prepare('UPDATE photos SET position = ? WHERE id = ?').run(i, p.id));
  });
  removeImage(UPLOADS, photo.file);
  res.json({ photos: photosOf(req.user.id) });
});

api.put('/me/photos/order', requireMember, (req, res) => {
  const ids = Array.isArray(req.body?.ids) ? req.body.ids.map(String) : [];
  const mine = db.prepare('SELECT id FROM photos WHERE user_id = ?').all(req.user.id).map((p) => p.id);
  if (ids.length !== mine.length || !ids.every((id) => mine.includes(id))) fail(400, 'Photo order looks wrong.');
  tx(db, () => ids.forEach((id, i) => db.prepare('UPDATE photos SET position = ? WHERE id = ?').run(i, id)));
  res.json({ photos: photosOf(req.user.id) });
});

api.delete('/me', requireMember, limit('login'), async (req, res) => {
  if (!(await auth.verifyPassword(String(req.body?.password ?? ''), req.user.password_hash))) {
    fail(401, 'That password isn’t right.');
  }
  deleteUserPhotos(req.user.id);
  db.prepare('DELETE FROM users WHERE id = ?').run(req.user.id);
  res.setHeader('Set-Cookie', auth.clearCookie({ secure: SECURE_COOKIES }));
  res.json({ ok: true });
});

// Members' photos are private: only the uploader and the owner can load them.
api.get('/photos/:id', requireUser, (req, res) => {
  const photo = db.prepare('SELECT * FROM photos WHERE id = ?').get(req.params.id);
  const allowed = photo && (photo.user_id === req.user.id || req.user.role === 'owner');
  if (!allowed) fail(404, 'Not found.');
  res.setHeader('Cache-Control', 'private, max-age=31536000, immutable');
  res.type(photo.mime).sendFile(path.join(UPLOADS, path.basename(photo.file)));
});

// ── The one profile ──────────────────────────────────────────────────────────
api.get('/profile', requireUser, (req, res) => {
  if (req.user.role === 'member' && !req.user.onboarded) fail(403, 'Finish your profile first.');
  const { minPhotos, ...profile } = owner;
  res.json({ profile });
});

api.post('/likes', requireMember, requireOnboarded, limit('write', (req) => req.user.id), (req, res) => {
  if (likeOf(req.user.id)) fail(409, 'You’ve already sent your like.');
  const type = String(req.body?.targetType ?? '');
  const ref = String(req.body?.targetRef ?? '');
  const snapshot = snapshotFor(owner, type, ref);
  if (!snapshot) fail(400, 'That part of the profile doesn’t exist anymore. Refresh and try again.');
  const comment = str(req.body?.comment, 240);
  const dateIdea = DATE_IDEAS.includes(req.body?.dateIdea) ? req.body.dateIdea : '';
  const id = newId();
  db.prepare(`INSERT INTO likes (id, user_id, target_type, target_ref, target_snapshot, comment, date_idea, created_at)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
    .run(id, req.user.id, type, ref, JSON.stringify(snapshot), comment, dateIdea, now());
  const what = type === 'photo' ? 'photo' : type === 'prompt' ? 'prompt' : 'profile';
  notify(`💌 ${req.user.first_name} liked your ${what}${comment ? `: “${comment}”` : ''}`, SITE_URL && `${SITE_URL}/likes`);
  res.json({ user: serializeSelf(req.user) });
});

// ── Member ↔ owner chat ──────────────────────────────────────────────────────
const requireMatch = (req, _res, next) => {
  const like = likeOf(req.user.id);
  if (like?.status !== 'matched') fail(403, 'You can chat once it’s a match.');
  req.like = like;
  next();
};

api.get('/thread', requireMember, requireMatch, (req, res) => {
  markRead(req.user.id, { byOwner: false });
  res.json({ messages: threadMessages(req.user.id, false), like: publicLike(req.like) });
});

api.post('/thread', requireMember, requireMatch, limit('write', (req) => req.user.id), (req, res) => {
  const message = postMessage(req.user.id, false, req.body?.body);
  notify(`💬 ${req.user.first_name}: ${message.body.slice(0, 140)}`, SITE_URL && `${SITE_URL}/chat/${req.user.id}`);
  res.json({ message });
});

api.post('/match/seen', requireMember, (req, res) => {
  db.prepare("UPDATE likes SET match_seen = 1 WHERE user_id = ? AND status = 'matched'").run(req.user.id);
  res.json({ user: serializeSelf(req.user) });
});

api.post('/unmatch', requireMember, requireMatch, (req, res) => {
  db.prepare("UPDATE likes SET status = 'unmatched', decided_at = ? WHERE id = ?").run(now(), req.like.id);
  res.json({ user: serializeSelf(req.user) });
});

// ── Owner ────────────────────────────────────────────────────────────────────
const ownerLike = (id) => {
  const like = db.prepare('SELECT * FROM likes WHERE id = ?').get(id);
  if (!like) fail(404, 'That like doesn’t exist anymore.');
  return like;
};
const memberRow = (id) => db.prepare("SELECT * FROM users WHERE id = ? AND role = 'member'").get(id);

function summary(like) {
  const m = memberRow(like.user_id);
  const p = json(m.profile, {});
  return {
    like: publicLike(like, { forOwner: true }),
    member: { id: m.id, name: m.first_name, age: ageFrom(m.birthdate), photo: photosOf(m.id)[0]?.src ?? null, location: p.location ?? '' },
  };
}

api.get('/owner/likes', requireOwner, (_req, res) => {
  const rows = db.prepare("SELECT * FROM likes WHERE status = 'pending' ORDER BY created_at DESC").all();
  res.json({ likes: rows.map((l) => ({ ...summary(l), fresh: !l.seen_by_owner })) });
});

api.get('/owner/likes/:id', requireOwner, (req, res) => {
  const like = ownerLike(req.params.id);
  db.prepare('UPDATE likes SET seen_by_owner = 1 WHERE id = ?').run(like.id);
  res.json({ like: publicLike(like, { forOwner: true }), member: memberProfile(memberRow(like.user_id)) });
});

api.post('/owner/likes/:id/match', requireOwner, (req, res) => {
  const like = ownerLike(req.params.id);
  if (like.status !== 'pending') fail(409, 'You already decided on this one.');
  db.prepare("UPDATE likes SET status = 'matched', decided_at = ?, seen_by_owner = 1 WHERE id = ?").run(now(), like.id);
  res.json({ memberId: like.user_id });
});

api.post('/owner/likes/:id/remove', requireOwner, (req, res) => {
  const like = ownerLike(req.params.id);
  if (like.status !== 'pending') fail(409, 'You already decided on this one.');
  db.prepare("UPDATE likes SET status = 'removed', decided_at = ?, seen_by_owner = 1 WHERE id = ?").run(now(), like.id);
  res.json({ ok: true });
});

api.get('/owner/matches', requireOwner, (_req, res) => {
  const rows = db.prepare("SELECT * FROM likes WHERE status = 'matched' ORDER BY decided_at DESC").all();
  const matches = rows.map((l) => {
    const last = db.prepare('SELECT * FROM messages WHERE member_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1').get(l.user_id);
    return {
      ...summary(l),
      lastMessage: last ? { body: last.body, mine: !!last.from_owner, createdAt: last.created_at } : null,
      unread: unreadFor(l.user_id, { forOwner: true }),
      sortKey: last?.created_at ?? l.decided_at,
    };
  }).sort((a, b) => b.sortKey - a.sortKey);
  res.json({ matches });
});

const requireOwnerMatch = (req, _res, next) => {
  const member = memberRow(req.params.memberId);
  const like = member && likeOf(member.id);
  if (like?.status !== 'matched') fail(404, 'No conversation here.');
  req.member = member;
  req.like = like;
  next();
};

api.get('/owner/threads/:memberId', requireOwner, requireOwnerMatch, (req, res) => {
  markRead(req.member.id, { byOwner: true });
  res.json({
    messages: threadMessages(req.member.id, true),
    like: publicLike(req.like, { forOwner: true }),
    member: memberProfile(req.member),
  });
});

api.post('/owner/threads/:memberId', requireOwner, requireOwnerMatch, (req, res) => {
  res.json({ message: postMessage(req.member.id, true, req.body?.body) });
});

api.post('/owner/threads/:memberId/unmatch', requireOwner, requireOwnerMatch, (req, res) => {
  db.prepare("UPDATE likes SET status = 'unmatched', decided_at = ? WHERE id = ?").run(now(), req.like.id);
  res.json({ ok: true });
});

api.get('/owner/stats', requireOwner, (_req, res) => {
  const one = (sql) => db.prepare(sql).get().n;
  res.json({
    stats: {
      members: one("SELECT COUNT(*) AS n FROM users WHERE role = 'member' AND onboarded = 1"),
      likes: one('SELECT COUNT(*) AS n FROM likes'),
      matches: one("SELECT COUNT(*) AS n FROM likes WHERE status IN ('matched', 'unmatched')"),
      messages: one('SELECT COUNT(*) AS n FROM messages'),
    },
  });
});

api.use((_req, _res, next) => next(new HttpError(404, 'Not found.')));
app.use('/api', api);

// ── Errors ───────────────────────────────────────────────────────────────────
app.use('/api', (err, _req, res, _next) => {
  let status = err.status || err.statusCode || 500;
  let message = err.message;
  if (err.type === 'entity.too.large') { status = 413; message = 'That photo is too large.'; }
  else if (err.type === 'entity.parse.failed') { status = 400; message = 'Bad request.'; }
  else if (status >= 500) { console.error(err); message = 'Something went wrong on our end.'; }
  res.status(status).json({ error: message });
});

// ── Owner photos & the web app ───────────────────────────────────────────────
app.use('/me', express.static(path.join(ROOT, 'public', 'me'), { maxAge: '1h' }));

const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function renderHtml(template, req) {
  const base = SITE_URL || `${req.protocol}://${req.get('host')}`;
  const title = `${owner.appName} · Meet ${owner.name}`;
  const desc = `One profile. No swiping. Make an account to see ${owner.name}’s profile and send a like.`;
  const head = [
    `<title>${escapeHtml(title)}</title>`,
    `<meta name="description" content="${escapeHtml(desc)}" />`,
    `<meta property="og:type" content="website" />`,
    `<meta property="og:title" content="${escapeHtml(title)}" />`,
    `<meta property="og:description" content="${escapeHtml(desc)}" />`,
    `<meta property="og:image" content="${escapeHtml(`${base}/og.png`)}" />`,
    `<meta property="og:url" content="${escapeHtml(base)}" />`,
    `<meta name="twitter:card" content="summary_large_image" />`,
    `<meta name="apple-mobile-web-app-title" content="${escapeHtml(owner.appName)}" />`,
  ].join('\n    ');
  return template.replace('<!--app-head-->', head);
}

if (API_ONLY) {
  // Tests only need the API.
} else if (DEV) {
  const { createServer } = await import('vite');
  const vite = await createServer({ root: ROOT, server: { middlewareMode: true }, appType: 'custom' });
  app.use(vite.middlewares);
  app.use(async (req, res, next) => {
    if (req.method !== 'GET') return next();
    try {
      const template = await vite.transformIndexHtml(req.originalUrl, fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8'));
      res.type('html').send(renderHtml(template, req));
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
  const template = fs.readFileSync(path.join(dist, 'index.html'), 'utf8');
  app.use('/assets', express.static(path.join(dist, 'assets'), { immutable: true, maxAge: '1y' }));
  app.use(express.static(dist, { index: false, maxAge: '1h' }));
  app.use((req, res, next) => {
    if (req.method !== 'GET' && req.method !== 'HEAD') return next();
    res.setHeader('Cache-Control', 'no-cache');
    res.type('html').send(renderHtml(template, req));
  });
}

const server = app.listen(PORT, (err) => {
  if (err) {
    console.error(`\n  Couldn’t start on port ${PORT}: ${err.code === 'EADDRINUSE' ? 'something else is already using it.' : err.message}\n`);
    process.exit(1);
  }
  console.log(`\n  ${owner.appName} is running → http://localhost:${server.address().port}${DEV ? '  (dev mode)' : ''}\n`);
});
