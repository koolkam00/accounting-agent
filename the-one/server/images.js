import fs from 'node:fs';
import path from 'node:path';

const MAX_BYTES = 6 * 1024 * 1024;

const TYPES = {
  'image/jpeg': { ext: 'jpg', check: (b) => b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff },
  'image/png': { ext: 'png', check: (b) => b.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])) },
  'image/webp': { ext: 'webp', check: (b) => b.subarray(0, 4).toString('latin1') === 'RIFF' && b.subarray(8, 12).toString('latin1') === 'WEBP' },
};

/**
 * Decode a `data:image/...;base64,` URL from the client.
 * The browser resizes photos before upload, so these are already small.
 */
export function decodeImage(dataUrl) {
  const m = /^data:(image\/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=\s]+)$/.exec(String(dataUrl || ''));
  if (!m) throw Object.assign(new Error('Photos need to be JPG, PNG or WebP.'), { status: 400 });
  const mime = m[1];
  const buf = Buffer.from(m[2], 'base64');
  if (buf.length > MAX_BYTES) throw Object.assign(new Error('That photo is too large.'), { status: 413 });
  if (buf.length < 64 || !TYPES[mime].check(buf)) {
    throw Object.assign(new Error('That file doesn’t look like a photo.'), { status: 400 });
  }
  return { buf, mime, ext: TYPES[mime].ext };
}

export function saveImage(dir, id, { buf, ext }) {
  const file = `${id}.${ext}`;
  fs.writeFileSync(path.join(dir, file), buf, { flag: 'wx' });
  return file;
}

export function removeImage(dir, file) {
  try { fs.unlinkSync(path.join(dir, path.basename(file))); } catch { /* already gone */ }
}
