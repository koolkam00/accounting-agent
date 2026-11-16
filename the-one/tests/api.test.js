// End-to-end API tests: auth, privacy rules, likes, matching and chat.
// Run with `npm test`. Starts a throwaway server with its own database.
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DATA_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'the-one-test-'));
const OWNER = { email: 'owner@example.test', password: 'owner-password-1' };
let base;
let server;

before(async () => {
  server = spawn(process.execPath, ['--no-warnings=ExperimentalWarning', 'server/index.js'], {
    cwd: ROOT,
    env: { ...process.env, API_ONLY: '1', PORT: '0', DATA_DIR, OWNER_EMAIL: OWNER.email, OWNER_PASSWORD: OWNER.password, NOTIFY_WEBHOOK_URL: '' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  base = await new Promise((resolve, reject) => {
    let out = '';
    server.stdout.on('data', (d) => {
      out += d;
      const m = /http:\/\/localhost:(\d+)/.exec(out);
      if (m) resolve(`http://localhost:${m[1]}`);
    });
    server.stderr.on('data', (d) => { out += d; });
    server.on('exit', (code) => reject(new Error(`server exited (${code}): ${out}`)));
    setTimeout(() => reject(new Error(`server did not start: ${out}`)), 10_000);
  });
});

after(() => {
  server?.kill();
  fs.rmSync(DATA_DIR, { recursive: true, force: true });
});

/** A tiny cookie-keeping client, like one browser. */
function client() {
  let cookie = '';
  return async (method, url, body, { csrf = true } = {}) => {
    const headers = {};
    if (cookie) headers.cookie = cookie;
    if (csrf) headers['x-requested-with'] = 'the-one';
    if (body !== undefined) headers['content-type'] = 'application/json';
    const res = await fetch(base + url, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
    const set = res.headers.get('set-cookie');
    if (set) cookie = set.split(';')[0];
    const type = res.headers.get('content-type') || '';
    const data = type.includes('json') ? await res.json() : await res.arrayBuffer();
    return { status: res.status, data, headers: res.headers };
  };
}

// Smallest thing that passes the JPEG signature check.
const fakeJpeg = `data:image/jpeg;base64,${Buffer.concat([Buffer.from([0xff, 0xd8, 0xff, 0xe0]), Buffer.alloc(200, 7)]).toString('base64')}`;

async function onboardedMember(name, email) {
  const c = client();
  assert.equal((await c('POST', '/api/auth/signup', { email, password: 'correct horse battery' })).status, 200);
  assert.equal((await c('PATCH', '/api/me', { firstName: name, birthdate: '1998-02-03' })).status, 200);
  const up = await c('POST', '/api/me/photos', { dataUrl: fakeJpeg });
  assert.equal(up.status, 200);
  const done = await c('PATCH', '/api/me', { onboarded: true, location: 'Brooklyn', height: 66, lookingFor: 'Something serious' });
  assert.equal(done.status, 200);
  assert.equal(done.data.user.onboarded, true);
  return { c, photoId: up.data.photos[0].id, userId: done.data.user.id };
}

test('public session shows the site but no user', async () => {
  const { status, data } = await client()('GET', '/api/session');
  assert.equal(status, 200);
  assert.equal(data.user, null);
  assert.ok(data.site.ownerName);
  assert.ok(data.site.appName);
});

test('signup validates input and blocks duplicates', async () => {
  const c = client();
  assert.equal((await c('POST', '/api/auth/signup', { email: 'nope', password: 'longenough' })).status, 400);
  assert.equal((await c('POST', '/api/auth/signup', { email: 'a@b.co', password: 'short' })).status, 400);
  assert.equal((await c('POST', '/api/auth/signup', { email: 'dup@example.test', password: 'longenough1' })).status, 200);
  assert.equal((await client()('POST', '/api/auth/signup', { email: 'DUP@example.test', password: 'longenough1' })).status, 409);
});

test('state-changing requests need the app header (CSRF)', async () => {
  const res = await client()('POST', '/api/auth/signup', { email: 'csrf@example.test', password: 'longenough1' }, { csrf: false });
  assert.equal(res.status, 403);
});

test('wrong password is rejected; right one signs in', async () => {
  await client()('POST', '/api/auth/signup', { email: 'login@example.test', password: 'the-right-one' });
  assert.equal((await client()('POST', '/api/auth/login', { email: 'login@example.test', password: 'the-wrong-one' })).status, 401);
  assert.equal((await client()('POST', '/api/auth/login', { email: 'nobody@example.test', password: 'whatever123' })).status, 401);
  const ok = await client()('POST', '/api/auth/login', { email: 'LOGIN@example.test', password: 'the-right-one' });
  assert.equal(ok.status, 200);
  assert.equal(ok.data.user.role, 'member');
});

test('under-18s cannot join, and the profile stays locked until onboarding is done', async () => {
  const c = client();
  await c('POST', '/api/auth/signup', { email: 'young@example.test', password: 'longenough1' });
  const year = new Date().getFullYear() - 17;
  assert.equal((await c('PATCH', '/api/me', { birthdate: `${year}-01-01` })).status, 400);
  assert.equal((await c('GET', '/api/profile')).status, 403);
  assert.equal((await c('PATCH', '/api/me', { firstName: 'Sam', birthdate: '2000-01-01', onboarded: true })).status, 400, 'needs a photo');
  assert.equal((await c('POST', '/api/me/photos', { dataUrl: 'data:image/gif;base64,R0lGODlh' })).status, 400);
  assert.equal((await c('POST', '/api/me/photos', { dataUrl: `data:image/png;base64,${Buffer.alloc(100).toString('base64')}` })).status, 400);
});

test('the full journey: like → match → chat → unmatch, with privacy rules enforced', async () => {
  const maya = await onboardedMember('Maya', 'maya@example.test');
  const zoe = await onboardedMember('Zoe', 'zoe@example.test');
  const anon = client();

  // Everyone signed in sees the one profile.
  const profile = await maya.c('GET', '/api/profile');
  assert.equal(profile.status, 200);
  assert.ok(profile.data.profile.photos.length > 0);
  const photoRef = profile.data.profile.photos[0].id;

  // Members can't reach owner tools or each other.
  assert.equal((await maya.c('GET', '/api/owner/likes')).status, 403);
  assert.equal((await maya.c('GET', '/api/owner/stats')).status, 403);
  assert.equal((await zoe.c('GET', `/api/photos/${maya.photoId}`)).status, 404);
  assert.equal((await anon('GET', `/api/photos/${maya.photoId}`)).status, 401);
  assert.equal((await maya.c('GET', `/api/photos/${maya.photoId}`)).status, 200);

  // One like each, aimed at something that exists.
  assert.equal((await maya.c('POST', '/api/likes', { targetType: 'photo', targetRef: 'p99' })).status, 400);
  const like = await maya.c('POST', '/api/likes', { targetType: 'photo', targetRef: photoRef, comment: 'Hi!', dateIdea: 'coffee' });
  assert.equal(like.status, 200);
  assert.equal(like.data.user.like.status, 'pending');
  assert.equal(like.data.user.like.comment, 'Hi!');
  assert.equal((await maya.c('POST', '/api/likes', { targetType: 'profile' })).status, 409);
  assert.equal((await maya.c('GET', '/api/thread')).status, 403, 'no chat before a match');

  // The owner sees it, and can see Maya's photo now.
  const owner = client();
  const login = await owner('POST', '/api/auth/login', OWNER);
  assert.equal(login.status, 200);
  assert.equal(login.data.user.role, 'owner');
  assert.equal(login.data.user.counts.fresh, 1);
  const likes = await owner('GET', '/api/owner/likes');
  assert.equal(likes.data.likes.length, 1);
  assert.equal(likes.data.likes[0].member.name, 'Maya');
  const likeId = likes.data.likes[0].like.id;
  const detail = await owner('GET', `/api/owner/likes/${likeId}`);
  assert.equal(detail.data.member.name, 'Maya');
  assert.equal(detail.data.like.dateIdea, 'coffee');
  assert.equal((await owner('GET', `/api/photos/${maya.photoId}`)).status, 200);
  assert.equal((await owner('POST', '/api/likes', { targetType: 'profile' })).status, 403, 'owner can’t like himself');

  // Match, then chat both ways.
  assert.equal((await owner('POST', `/api/owner/likes/${likeId}/match`)).status, 200);
  assert.equal((await owner('POST', `/api/owner/likes/${likeId}/match`)).status, 409);
  const me = await maya.c('GET', '/api/session');
  assert.equal(me.data.user.like.status, 'matched');
  assert.equal(me.data.user.like.matchSeen, false);
  assert.equal((await maya.c('POST', '/api/match/seen')).data.user.like.matchSeen, true);

  assert.equal((await owner('POST', `/api/owner/threads/${maya.userId}`, { body: '   ' })).status, 400);
  assert.equal((await owner('POST', `/api/owner/threads/${maya.userId}`, { body: 'Coffee Saturday?' })).status, 200);
  assert.equal((await maya.c('GET', '/api/session')).data.user.unread, 1);
  const thread = await maya.c('GET', '/api/thread');
  assert.equal(thread.data.messages.length, 1);
  assert.equal(thread.data.messages[0].mine, false);
  assert.equal((await maya.c('GET', '/api/session')).data.user.unread, 0, 'reading clears unread');
  assert.equal((await maya.c('POST', '/api/thread', { body: 'Yes!' })).status, 200);

  const matches = await owner('GET', '/api/owner/matches');
  assert.equal(matches.data.matches.length, 1);
  assert.equal(matches.data.matches[0].unread, 1);
  assert.equal(matches.data.matches[0].lastMessage.body, 'Yes!');
  const ownerThread = await owner('GET', `/api/owner/threads/${maya.userId}`);
  assert.deepEqual(ownerThread.data.messages.map((m) => [m.body, m.mine]), [['Coffee Saturday?', true], ['Yes!', false]]);

  // Zoe can't read Maya's conversation, and the owner can't open a thread with someone he hasn't matched.
  assert.equal((await zoe.c('GET', '/api/thread')).status, 403);
  assert.equal((await owner('GET', `/api/owner/threads/${zoe.userId}`)).status, 404);

  const stats = await owner('GET', '/api/owner/stats');
  assert.equal(stats.data.stats.matches, 1);

  // Unmatching closes the chat for both.
  assert.equal((await maya.c('POST', '/api/unmatch')).status, 200);
  assert.equal((await maya.c('POST', '/api/thread', { body: 'hello?' })).status, 403);
  assert.equal((await owner('GET', `/api/owner/threads/${maya.userId}`)).status, 404);
});

test('a passed-on like still looks "sent" to the visitor', async () => {
  const lia = await onboardedMember('Lia', 'lia@example.test');
  await lia.c('POST', '/api/likes', { targetType: 'profile' });
  const owner = client();
  await owner('POST', '/api/auth/login', OWNER);
  const { data } = await owner('GET', '/api/owner/likes');
  const mine = data.likes.find((l) => l.member.name === 'Lia');
  assert.equal((await owner('POST', `/api/owner/likes/${mine.like.id}/remove`)).status, 200);
  assert.equal((await lia.c('GET', '/api/session')).data.user.like.status, 'pending');
});

test('deleting an account needs the password and removes photos from disk', async () => {
  const kim = await onboardedMember('Kim', 'kim@example.test');
  const files = () => fs.readdirSync(path.join(DATA_DIR, 'uploads')).filter((f) => f.startsWith(kim.photoId));
  assert.equal(files().length, 1);
  assert.equal((await kim.c('DELETE', '/api/me', { password: 'nope-nope' })).status, 401);
  assert.equal((await kim.c('DELETE', '/api/me', { password: 'correct horse battery' })).status, 200);
  assert.equal(files().length, 0);
  assert.equal((await kim.c('GET', '/api/session')).data.user, null);
  assert.equal((await client()('POST', '/api/auth/login', { email: 'kim@example.test', password: 'correct horse battery' })).status, 401);
});

test('logging out ends the session', async () => {
  const c = client();
  await c('POST', '/api/auth/signup', { email: 'bye@example.test', password: 'longenough1' });
  assert.ok((await c('GET', '/api/session')).data.user);
  await c('POST', '/api/auth/logout');
  assert.equal((await c('GET', '/api/session')).data.user, null);
});
