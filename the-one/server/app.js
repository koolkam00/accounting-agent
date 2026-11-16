import express from 'express';
import * as auth from './auth.js';
import { newId, now } from './util.js';
import { decodeImage } from './images.js';
import { snapshotFor, ageFrom, formatHeight, LOOKING_FOR, DATE_IDEAS } from './profile.js';
import { notify } from './notify.js';

class HttpError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}
const fail = (status, message) => { throw new HttpError(status, message); };
const str = (v, max) => String(v ?? '').trim().slice(0, max);
const json = (s, fallback) => { try { return JSON.parse(s); } catch { return fallback; } };
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const SECURITY_HEADERS = {
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'same-origin',
  'X-Frame-Options': 'DENY',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
};
export const CSP = [
  "default-src 'self'", "img-src 'self' data: blob:", "style-src 'self' 'unsafe-inline'",
  "font-src 'self' data:", "script-src 'self'", "connect-src 'self'", "frame-ancestors 'none'",
  "base-uri 'self'", "form-action 'self'", "object-src 'none'",
].join('; ');

/**
 * The whole API as an Express app. Used by the local server (server/index.js)
 * and by the Vercel function (api/index.js).
 *
 * @param {object} o
 * @param {object} o.store      storage from store-sqlite.js or store-pg.js
 * @param {() => object} o.getOwner  the normalised owner profile
 */
export function createApp({ store, getOwner, dev = false, secureCookies = true, siteUrl = '', trustProxy = false, clientIp }) {
  const ipOf = clientIp ?? ((req) => req.ip);

  // ── Data helpers ───────────────────────────────────────────────────────────
  const photosOf = async (userId) => (await store.all('SELECT id FROM photos WHERE user_id = ? ORDER BY position', [userId]))
    .map((p) => ({ id: p.id, src: `/api/photos/${p.id}` }));
  const likeOf = (userId) => store.one('SELECT * FROM likes WHERE user_id = ?', [userId]);
  const count = async (sql, params = []) => Number((await store.one(sql, params))?.n ?? 0);
  const userById = (id) => store.one('SELECT * FROM users WHERE id = ?', [id]);
  const memberRow = (id) => store.one("SELECT * FROM users WHERE id = ? AND role = 'member'", [id]);

  function publicLike(like, { forOwner = false } = {}) {
    if (!like) return null;
    let status = like.status;
    // Visitors never find out they were passed on; it just stays "sent".
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

  async function memberProfile(user) {
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
      photos: await photosOf(user.id),
      prompts: (p.prompts ?? []).map((q, i) => ({ id: `q${i}`, question: q.question, answer: q.answer })),
      facts,
      joinedAt: user.created_at,
    };
  }

  const unreadFor = (memberId, { forOwner }) => count(
    'SELECT COUNT(*) AS n FROM messages WHERE member_id = ? AND from_owner = ? AND read_at IS NULL',
    [memberId, forOwner ? 0 : 1],
  );

  async function serializeSelf(user) {
    const owner = getOwner();
    if (user.role === 'owner') {
      const [pending, fresh, unread] = await Promise.all([
        count("SELECT COUNT(*) AS n FROM likes WHERE status = 'pending'"),
        count("SELECT COUNT(*) AS n FROM likes WHERE status = 'pending' AND seen_by_owner = 0"),
        count(`SELECT COUNT(*) AS n FROM messages m JOIN likes l ON l.user_id = m.member_id
               WHERE l.status = 'matched' AND m.from_owner = 0 AND m.read_at IS NULL`),
      ]);
      return { id: user.id, role: 'owner', email: user.email, firstName: owner.name, counts: { pending, fresh, unread } };
    }
    const p = json(user.profile, {});
    const [like, photos] = await Promise.all([likeOf(user.id), photosOf(user.id)]);
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
      photos,
      onboarded: !!user.onboarded,
      like: publicLike(like),
      unread: like?.status === 'matched' ? await unreadFor(user.id, { forOwner: false }) : 0,
    };
  }

  const threadMessages = async (memberId, viewerIsOwner) => (
    await store.all('SELECT * FROM messages WHERE member_id = ? ORDER BY created_at, id', [memberId])
  ).map((m) => ({ id: m.id, mine: !!m.from_owner === viewerIsOwner, body: m.body, createdAt: m.created_at, readAt: m.read_at }));

  const markRead = (memberId, { byOwner }) => store.run(
    'UPDATE messages SET read_at = ? WHERE member_id = ? AND from_owner = ? AND read_at IS NULL',
    [now(), memberId, byOwner ? 0 : 1],
  );

  async function postMessage(memberId, fromOwner, rawBody) {
    const body = str(rawBody, 2000);
    if (!body) fail(400, 'Write something first.');
    const id = newId();
    const createdAt = now();
    await store.run('INSERT INTO messages (id, member_id, from_owner, body, created_at) VALUES (?, ?, ?, ?, ?)',
      [id, memberId, fromOwner ? 1 : 0, body, createdAt]);
    return { id, mine: true, body, createdAt, readAt: null };
  }

  // ── Rate limits (per instance; best-effort on serverless hosts) ────────────
  const limits = {
    login: auth.rateLimiter({ windowMs: 15 * 60_000, max: 30 }),
    signup: auth.rateLimiter({ windowMs: 60 * 60_000, max: 30 }), // generous: phones on one carrier often share an IP
    write: auth.rateLimiter({ windowMs: 60_000, max: 60 }),
  };
  const limit = (name, keyFn = ipOf) => (req, _res, next) => {
    if (!limits[name](`${name}:${keyFn(req)}`)) fail(429, 'Slow down a little and try again in a bit.');
    next();
  };

  // ── App ────────────────────────────────────────────────────────────────────
  const app = express();
  app.disable('x-powered-by');
  app.set('trust proxy', trustProxy);

  app.use((_req, res, next) => {
    for (const [k, v] of Object.entries(SECURITY_HEADERS)) res.setHeader(k, v);
    if (!dev) res.setHeader('Content-Security-Policy', CSP);
    next();
  });

  const api = express.Router();
  api.use(express.json({ limit: '5mb' }));

  // Who's asking?
  api.use(async (req, _res, next) => {
    req.sessionToken = auth.parseCookies(req.headers.cookie)[auth.COOKIE_NAME];
    req.user = await auth.userForToken(store, req.sessionToken);
    if (req.user && (!req.user.last_seen_at || now() - req.user.last_seen_at > 5 * 60_000)) {
      await store.run('UPDATE users SET last_seen_at = ? WHERE id = ?', [now(), req.user.id]);
    }
    next();
  });

  // CSRF: state-changing requests must come from our own JS (custom header, so no cross-site forms).
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

  api.get('/healthz', async (_req, res) => {
    await store.one('SELECT 1 AS ok');
    res.setHeader('Cache-Control', 'no-store');
    res.type('text').send('ok');
  });

  api.get('/session', async (req, res) => {
    const owner = getOwner();
    res.json({
      site: {
        appName: owner.appName,
        ownerName: owner.name,
        ownerAge: owner.age,
        pronoun: owner.pronoun,
        heroPhoto: owner.photos[0]?.src ?? null,
        minPhotos: owner.minPhotos,
        lookingFor: LOOKING_FOR,
      },
      user: req.user ? await serializeSelf(req.user) : null,
    });
  });

  // ── Auth ───────────────────────────────────────────────────────────────────
  api.post('/auth/signup', limit('signup'), async (req, res) => {
    const email = str(req.body?.email, 200).toLowerCase();
    const password = String(req.body?.password ?? '');
    if (!EMAIL_RE.test(email)) fail(400, 'That email doesn’t look right.');
    if (password.length < 8) fail(400, 'Use at least 8 characters for your password.');
    if (password.length > 200) fail(400, 'That password is a bit too long.');
    if (await store.one('SELECT 1 AS ok FROM users WHERE email = ?', [email])) {
      fail(409, 'There’s already an account with that email. Try signing in.');
    }
    const id = newId();
    try {
      await store.run('INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
        [id, email, await auth.hashPassword(password), now()]);
    } catch (err) {
      if (await store.one('SELECT 1 AS ok FROM users WHERE email = ?', [email])) {
        fail(409, 'There’s already an account with that email. Try signing in.');
      }
      throw err;
    }
    const token = await auth.createSession(store, id);
    res.setHeader('Set-Cookie', auth.sessionCookie(token, { secure: secureCookies }));
    res.json({ user: await serializeSelf(await userById(id)) });
  });

  api.post('/auth/login', limit('login'), async (req, res) => {
    const email = str(req.body?.email, 200).toLowerCase();
    const password = String(req.body?.password ?? '');
    const user = await store.one('SELECT * FROM users WHERE email = ?', [email]);
    const ok = user ? await auth.verifyPassword(password, user.password_hash) : await auth.dummyVerify(password);
    if (!ok) fail(401, 'That email and password don’t match.');
    const token = await auth.createSession(store, user.id);
    res.setHeader('Set-Cookie', auth.sessionCookie(token, { secure: secureCookies }));
    res.json({ user: await serializeSelf(user) });
  });

  api.post('/auth/logout', async (req, res) => {
    await auth.destroySession(store, req.sessionToken);
    res.setHeader('Set-Cookie', auth.clearCookie({ secure: secureCookies }));
    res.json({ ok: true });
  });

  // ── Visitor: own profile ───────────────────────────────────────────────────
  api.patch('/me', requireMember, limit('write', (req) => req.user.id), async (req, res) => {
    const b = req.body ?? {};
    const user = req.user;
    const owner = getOwner();
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

    let onboarded = user.onboarded ? 1 : 0;
    if (b.onboarded === true && !onboarded) {
      const photoCount = await count('SELECT COUNT(*) AS n FROM photos WHERE user_id = ?', [user.id]);
      if (!firstName) fail(400, 'Add your first name.');
      if (!birthdate) fail(400, 'Add your birthday.');
      if (photoCount < owner.minPhotos) fail(400, `Add at least ${owner.minPhotos} photo${owner.minPhotos === 1 ? '' : 's'}.`);
      onboarded = 1;
    }

    await store.run('UPDATE users SET first_name = ?, birthdate = ?, profile = ?, onboarded = ? WHERE id = ?',
      [firstName, birthdate, JSON.stringify(profile), onboarded, user.id]);
    res.json({ user: await serializeSelf(await userById(user.id)) });
  });

  api.post('/me/photos', requireMember, limit('write', (req) => req.user.id), async (req, res) => {
    const image = decodeImage(req.body?.dataUrl);
    await store.tx(async (q) => {
      const { n } = await q.one('SELECT COUNT(*) AS n FROM photos WHERE user_id = ?', [req.user.id]);
      if (Number(n) >= 6) fail(400, 'You can add up to 6 photos.');
      const { p } = await q.one('SELECT COALESCE(MAX(position), -1) + 1 AS p FROM photos WHERE user_id = ?', [req.user.id]);
      await q.run('INSERT INTO photos (id, user_id, position, mime, data, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        [newId(), req.user.id, Number(p), image.mime, image.buf, now()]);
    });
    res.json({ photos: await photosOf(req.user.id) });
  });

  api.delete('/me/photos/:id', requireMember, async (req, res) => {
    const owner = getOwner();
    const photo = await store.one('SELECT id FROM photos WHERE id = ? AND user_id = ?', [req.params.id, req.user.id]);
    if (!photo) fail(404, 'Photo not found.');
    const photoCount = await count('SELECT COUNT(*) AS n FROM photos WHERE user_id = ?', [req.user.id]);
    if (req.user.onboarded && photoCount <= Math.max(1, owner.minPhotos)) {
      fail(400, 'Add another photo before removing this one.');
    }
    await store.tx(async (q) => {
      await q.run('DELETE FROM photos WHERE id = ?', [photo.id]);
      const rest = await q.all('SELECT id FROM photos WHERE user_id = ? ORDER BY position', [req.user.id]);
      for (const [i, p] of rest.entries()) await q.run('UPDATE photos SET position = ? WHERE id = ?', [i, p.id]);
    });
    res.json({ photos: await photosOf(req.user.id) });
  });

  api.put('/me/photos/order', requireMember, async (req, res) => {
    const ids = Array.isArray(req.body?.ids) ? req.body.ids.map(String) : [];
    const mine = (await store.all('SELECT id FROM photos WHERE user_id = ?', [req.user.id])).map((p) => p.id);
    if (ids.length !== mine.length || !ids.every((id) => mine.includes(id))) fail(400, 'Photo order looks wrong.');
    await store.tx(async (q) => {
      for (const [i, id] of ids.entries()) await q.run('UPDATE photos SET position = ? WHERE id = ?', [i, id]);
    });
    res.json({ photos: await photosOf(req.user.id) });
  });

  api.delete('/me', requireMember, limit('login'), async (req, res) => {
    if (!(await auth.verifyPassword(String(req.body?.password ?? ''), req.user.password_hash))) {
      fail(401, 'That password isn’t right.');
    }
    // Photos, sessions, the like and messages go with the account (ON DELETE CASCADE).
    await store.run('DELETE FROM users WHERE id = ?', [req.user.id]);
    res.setHeader('Set-Cookie', auth.clearCookie({ secure: secureCookies }));
    res.json({ ok: true });
  });

  // Visitors' photos are private: only the uploader and the owner can load them.
  api.get('/photos/:id', requireUser, async (req, res) => {
    const photo = await store.one('SELECT user_id, mime, data FROM photos WHERE id = ?', [req.params.id]);
    const allowed = photo && (photo.user_id === req.user.id || req.user.role === 'owner');
    if (!allowed) fail(404, 'Not found.');
    res.setHeader('Cache-Control', 'private, max-age=31536000, immutable');
    res.type(photo.mime).send(Buffer.from(photo.data));
  });

  // ── The one profile ────────────────────────────────────────────────────────
  api.get('/profile', requireUser, (req, res) => {
    if (req.user.role === 'member' && !req.user.onboarded) fail(403, 'Finish your profile first.');
    const { minPhotos, ...profile } = getOwner();
    res.json({ profile });
  });

  api.post('/likes', requireMember, requireOnboarded, limit('write', (req) => req.user.id), async (req, res) => {
    if (await likeOf(req.user.id)) fail(409, 'You’ve already sent your like.');
    const type = String(req.body?.targetType ?? '');
    const ref = String(req.body?.targetRef ?? '');
    const snapshot = snapshotFor(getOwner(), type, ref);
    if (!snapshot) fail(400, 'That part of the profile doesn’t exist anymore. Refresh and try again.');
    const comment = str(req.body?.comment, 240);
    const dateIdea = DATE_IDEAS.includes(req.body?.dateIdea) ? req.body.dateIdea : '';
    try {
      await store.run(`INSERT INTO likes (id, user_id, target_type, target_ref, target_snapshot, comment, date_idea, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [newId(), req.user.id, type, ref, JSON.stringify(snapshot), comment, dateIdea, now()]);
    } catch (err) {
      if (await likeOf(req.user.id)) fail(409, 'You’ve already sent your like.');
      throw err;
    }
    const what = type === 'photo' ? 'photo' : type === 'prompt' ? 'prompt' : 'profile';
    await notify(`💌 ${req.user.first_name} liked your ${what}${comment ? `: “${comment}”` : ''}`, siteUrl && `${siteUrl}/likes`);
    res.json({ user: await serializeSelf(req.user) });
  });

  // ── Visitor ↔ owner chat ───────────────────────────────────────────────────
  const requireMatch = async (req, _res, next) => {
    const like = await likeOf(req.user.id);
    if (like?.status !== 'matched') fail(403, 'You can chat once it’s a match.');
    req.like = like;
    next();
  };

  api.get('/thread', requireMember, requireMatch, async (req, res) => {
    await markRead(req.user.id, { byOwner: false });
    res.json({ messages: await threadMessages(req.user.id, false), like: publicLike(req.like) });
  });

  api.post('/thread', requireMember, requireMatch, limit('write', (req) => req.user.id), async (req, res) => {
    const message = await postMessage(req.user.id, false, req.body?.body);
    await notify(`💬 ${req.user.first_name}: ${message.body.slice(0, 140)}`, siteUrl && `${siteUrl}/chat/${req.user.id}`);
    res.json({ message });
  });

  api.post('/match/seen', requireMember, async (req, res) => {
    await store.run("UPDATE likes SET match_seen = 1 WHERE user_id = ? AND status = 'matched'", [req.user.id]);
    res.json({ user: await serializeSelf(req.user) });
  });

  api.post('/unmatch', requireMember, requireMatch, async (req, res) => {
    await store.run("UPDATE likes SET status = 'unmatched', decided_at = ? WHERE id = ?", [now(), req.like.id]);
    res.json({ user: await serializeSelf(req.user) });
  });

  // ── Owner ──────────────────────────────────────────────────────────────────
  const ownerLike = async (id) => {
    const like = await store.one('SELECT * FROM likes WHERE id = ?', [id]);
    if (!like) fail(404, 'That like doesn’t exist anymore.');
    return like;
  };

  async function summary(like) {
    const m = await memberRow(like.user_id);
    const p = json(m.profile, {});
    return {
      like: publicLike(like, { forOwner: true }),
      member: { id: m.id, name: m.first_name, age: ageFrom(m.birthdate), photo: (await photosOf(m.id))[0]?.src ?? null, location: p.location ?? '' },
    };
  }

  api.get('/owner/likes', requireOwner, async (_req, res) => {
    const rows = await store.all("SELECT * FROM likes WHERE status = 'pending' ORDER BY created_at DESC");
    res.json({ likes: await Promise.all(rows.map(async (l) => ({ ...(await summary(l)), fresh: !l.seen_by_owner }))) });
  });

  api.get('/owner/likes/:id', requireOwner, async (req, res) => {
    const like = await ownerLike(req.params.id);
    await store.run('UPDATE likes SET seen_by_owner = 1 WHERE id = ?', [like.id]);
    res.json({ like: publicLike(like, { forOwner: true }), member: await memberProfile(await memberRow(like.user_id)) });
  });

  const decide = (status) => async (req, res) => {
    const like = await ownerLike(req.params.id);
    const { changes } = await store.run(
      "UPDATE likes SET status = ?, decided_at = ?, seen_by_owner = 1 WHERE id = ? AND status = 'pending'",
      [status, now(), like.id],
    );
    if (!changes) fail(409, 'You already decided on this one.');
    res.json(status === 'matched' ? { memberId: like.user_id } : { ok: true });
  };
  api.post('/owner/likes/:id/match', requireOwner, decide('matched'));
  api.post('/owner/likes/:id/remove', requireOwner, decide('removed'));

  api.get('/owner/matches', requireOwner, async (_req, res) => {
    const rows = await store.all("SELECT * FROM likes WHERE status = 'matched' ORDER BY decided_at DESC");
    const matches = (await Promise.all(rows.map(async (l) => {
      const last = await store.one('SELECT * FROM messages WHERE member_id = ? ORDER BY created_at DESC, id DESC LIMIT 1', [l.user_id]);
      return {
        ...(await summary(l)),
        lastMessage: last ? { body: last.body, mine: !!last.from_owner, createdAt: last.created_at } : null,
        unread: await unreadFor(l.user_id, { forOwner: true }),
        sortKey: last?.created_at ?? l.decided_at,
      };
    }))).sort((a, b) => b.sortKey - a.sortKey);
    res.json({ matches });
  });

  const requireOwnerMatch = async (req, _res, next) => {
    const member = await memberRow(req.params.memberId);
    const like = member && await likeOf(member.id);
    if (like?.status !== 'matched') fail(404, 'No conversation here.');
    req.member = member;
    req.like = like;
    next();
  };

  api.get('/owner/threads/:memberId', requireOwner, requireOwnerMatch, async (req, res) => {
    await markRead(req.member.id, { byOwner: true });
    res.json({
      messages: await threadMessages(req.member.id, true),
      like: publicLike(req.like, { forOwner: true }),
      member: await memberProfile(req.member),
    });
  });

  api.post('/owner/threads/:memberId', requireOwner, requireOwnerMatch, async (req, res) => {
    res.json({ message: await postMessage(req.member.id, true, req.body?.body) });
  });

  api.post('/owner/threads/:memberId/unmatch', requireOwner, requireOwnerMatch, async (req, res) => {
    await store.run("UPDATE likes SET status = 'unmatched', decided_at = ? WHERE id = ?", [now(), req.like.id]);
    res.json({ ok: true });
  });

  api.get('/owner/stats', requireOwner, async (_req, res) => {
    const [members, likes, matches, messages] = await Promise.all([
      count("SELECT COUNT(*) AS n FROM users WHERE role = 'member' AND onboarded = 1"),
      count('SELECT COUNT(*) AS n FROM likes'),
      count("SELECT COUNT(*) AS n FROM likes WHERE status IN ('matched', 'unmatched')"),
      count('SELECT COUNT(*) AS n FROM messages'),
    ]);
    res.json({ stats: { members, likes, matches, messages } });
  });

  // Change your own login (email and/or password) without touching the host's settings.
  api.patch('/owner/account', requireOwner, limit('login'), async (req, res) => {
    if (!(await auth.verifyPassword(String(req.body?.currentPassword ?? ''), req.user.password_hash))) {
      fail(401, 'Your current password isn’t right.');
    }
    const email = str(req.body?.email, 200).toLowerCase() || req.user.email;
    const newPassword = String(req.body?.newPassword ?? '');
    if (!EMAIL_RE.test(email)) fail(400, 'That email doesn’t look right.');
    if (newPassword && newPassword.length < 8) fail(400, 'Use at least 8 characters for your new password.');
    if (newPassword.length > 200) fail(400, 'That password is a bit too long.');
    if (email !== req.user.email && await store.one('SELECT 1 AS ok FROM users WHERE email = ?', [email])) {
      fail(409, 'Another account already uses that email.');
    }
    const hash = newPassword ? await auth.hashPassword(newPassword) : req.user.password_hash;
    await store.tx(async (q) => {
      await q.run('UPDATE users SET email = ?, password_hash = ? WHERE id = ?', [email, hash, req.user.id]);
      if (newPassword) {
        // Sign out everywhere else.
        await q.run('DELETE FROM sessions WHERE user_id = ? AND token_hash <> ?', [req.user.id, auth.tokenHash(req.sessionToken)]);
      }
    });
    res.json({ user: await serializeSelf({ ...req.user, email }) });
  });

  api.use((_req, _res, next) => next(new HttpError(404, 'Not found.')));
  app.use('/api', api);

  app.use('/api', (err, _req, res, _next) => {
    let status = err.status || err.statusCode || 500;
    let message = err.message;
    if (err.type === 'entity.too.large') { status = 413; message = 'That photo is too large.'; }
    else if (err.type === 'entity.parse.failed') { status = 400; message = 'Bad request.'; }
    else if (status >= 500) { console.error(err); message = 'Something went wrong on our end.'; }
    res.status(status).json({ error: message });
  });

  return app;
}
