import { DatabaseSync } from 'node:sqlite';
import crypto from 'node:crypto';

const SCHEMA = `
CREATE TABLE IF NOT EXISTS users (
  id            TEXT PRIMARY KEY,
  email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
  password_hash TEXT NOT NULL,
  role          TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'member')),
  first_name    TEXT NOT NULL DEFAULT '',
  birthdate     TEXT,
  profile       TEXT NOT NULL DEFAULT '{}',
  onboarded     INTEGER NOT NULL DEFAULT 0,
  created_at    INTEGER NOT NULL,
  last_seen_at  INTEGER
);

CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_user ON sessions(user_id);

CREATE TABLE IF NOT EXISTS photos (
  id         TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  position   INTEGER NOT NULL,
  file       TEXT NOT NULL,
  mime       TEXT NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS photos_user ON photos(user_id, position);

-- One like per member. A like becomes a match when the owner likes back.
CREATE TABLE IF NOT EXISTS likes (
  id              TEXT PRIMARY KEY,
  user_id         TEXT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  target_type     TEXT NOT NULL CHECK (target_type IN ('photo', 'prompt', 'profile')),
  target_ref      TEXT NOT NULL DEFAULT '',
  target_snapshot TEXT NOT NULL DEFAULT '{}',
  comment         TEXT NOT NULL DEFAULT '',
  date_idea       TEXT NOT NULL DEFAULT '',
  status          TEXT NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'matched', 'removed', 'unmatched')),
  created_at      INTEGER NOT NULL,
  decided_at      INTEGER,
  seen_by_owner   INTEGER NOT NULL DEFAULT 0,
  match_seen      INTEGER NOT NULL DEFAULT 0
);

-- Every conversation is between the owner and one member, so a thread is keyed by member.
CREATE TABLE IF NOT EXISTS messages (
  id         TEXT PRIMARY KEY,
  member_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  from_owner INTEGER NOT NULL,
  body       TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  read_at    INTEGER
);
CREATE INDEX IF NOT EXISTS messages_member ON messages(member_id, created_at);
`;

export function openDb(file) {
  const db = new DatabaseSync(file);
  db.exec('PRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON; PRAGMA busy_timeout = 5000;');
  db.exec(SCHEMA);
  return db;
}

export const newId = () => crypto.randomBytes(12).toString('base64url');
export const now = () => Date.now();

/** Run fn inside a transaction. */
export function tx(db, fn) {
  db.exec('BEGIN');
  try {
    const result = fn();
    db.exec('COMMIT');
    return result;
  } catch (err) {
    db.exec('ROLLBACK');
    throw err;
  }
}
