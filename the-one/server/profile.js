import path from 'node:path';
import { pathToFileURL } from 'node:url';

export const PRONOUNS = {
  he: { subject: 'he', object: 'him', possessive: 'his' },
  she: { subject: 'she', object: 'her', possessive: 'her' },
  they: { subject: 'they', object: 'them', possessive: 'their' },
};

export const LOOKING_FOR = ['Something serious', 'Seeing where it goes', 'Something casual', 'Not sure yet'];
export const DATE_IDEAS = ['coffee', 'drinks', 'dinner', 'walk', 'surprise'];

export function ageFrom(birthdate, at = new Date()) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(birthdate || ''));
  if (!m) return null;
  const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])];
  let age = at.getFullYear() - y;
  if (at.getMonth() + 1 < mo || (at.getMonth() + 1 === mo && at.getDate() < d)) age -= 1;
  return age;
}

export function formatHeight(inches) {
  const n = Number(inches);
  if (!Number.isFinite(n) || n <= 0) return '';
  return `${Math.floor(n / 12)}'${n % 12}"`;
}

const str = (v, max) => String(v ?? '').trim().slice(0, max);

/** Read profile.config.js fresh from disk (used locally, so edits show up without a restart). */
export async function loadOwnerProfile(rootDir) {
  const file = path.join(rootDir, 'profile.config.js');
  const mod = await import(`${pathToFileURL(file).href}?v=${Date.now()}`);
  return normalizeProfile(mod.default ?? {});
}

/** Normalise profile.config.js into the shape the client renders. */
export function normalizeProfile(cfg = {}) {

  const photos = (Array.isArray(cfg.photos) ? cfg.photos : [])
    .map((p) => (typeof p === 'string' ? { src: p } : p))
    .filter((p) => p && p.src)
    .slice(0, 6)
    .map((p, i) => ({ id: `p${i}`, src: String(p.src), caption: str(p.caption, 120) }));

  const prompts = (Array.isArray(cfg.prompts) ? cfg.prompts : [])
    .filter((p) => p && p.question && p.answer)
    .slice(0, 3)
    .map((p, i) => ({ id: `q${i}`, question: str(p.question, 80), answer: str(p.answer, 300) }));

  const facts = Object.entries(cfg.facts ?? {})
    .filter(([, v]) => v !== null && v !== undefined && String(v).trim() !== '')
    .map(([key, value]) => ({ key, value: str(value, 60) }));

  return {
    appName: str(cfg.appName, 30) || 'the one',
    name: str(cfg.name, 30) || 'Me',
    age: ageFrom(cfg.birthdate),
    pronoun: PRONOUNS[cfg.pronoun] ?? PRONOUNS.they,
    photos,
    prompts,
    facts,
    minPhotos: Math.max(0, Math.min(6, Number(cfg.signup?.minPhotos ?? 1) || 0)),
  };
}

/** The bit of the owner's profile a liked item points at, frozen at like-time. */
export function snapshotFor(owner, type, ref) {
  if (type === 'photo') {
    const p = owner.photos.find((x) => x.id === ref);
    return p ? { src: p.src, caption: p.caption } : null;
  }
  if (type === 'prompt') {
    const q = owner.prompts.find((x) => x.id === ref);
    return q ? { question: q.question, answer: q.answer } : null;
  }
  if (type === 'profile') return {};
  return null;
}
