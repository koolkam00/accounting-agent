import crypto from 'node:crypto';

export const newId = () => crypto.randomBytes(12).toString('base64url');
export const now = () => Date.now();
