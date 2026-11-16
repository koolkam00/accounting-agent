// The same tables in two dialects: SQLite for running locally, Postgres for hosting.
// Timestamps are milliseconds since the epoch; flags are 0/1 integers.

export const SQLITE_SCHEMA = `
CREATE TABLE IF NOT EXISTS users (
  id            TEXT PRIMARY KEY,
  email         TEXT NOT NULL UNIQUE,
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
  mime       TEXT NOT NULL,
  data       BLOB NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS photos_user ON photos(user_id, position);
CREATE TABLE IF NOT EXISTS likes (
  id              TEXT PRIMARY KEY,
  user_id         TEXT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  target_type     TEXT NOT NULL CHECK (target_type IN ('photo', 'prompt', 'profile')),
  target_ref      TEXT NOT NULL DEFAULT '',
  target_snapshot TEXT NOT NULL DEFAULT '{}',
  comment         TEXT NOT NULL DEFAULT '',
  date_idea       TEXT NOT NULL DEFAULT '',
  status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'matched', 'removed', 'unmatched')),
  created_at      INTEGER NOT NULL,
  decided_at      INTEGER,
  seen_by_owner   INTEGER NOT NULL DEFAULT 0,
  match_seen      INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS messages (
  id         TEXT PRIMARY KEY,
  member_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  from_owner INTEGER NOT NULL,
  body       TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  read_at    INTEGER
);
CREATE INDEX IF NOT EXISTS messages_member ON messages(member_id, created_at);
CREATE TABLE IF NOT EXISTS settings (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
`;

/** Postgres version, in its own schema so Supabase's public Data API never exposes it. */
export const pgSchema = (s = 'the_one') => `
CREATE SCHEMA IF NOT EXISTS ${s};
CREATE TABLE IF NOT EXISTS ${s}.users (
  id            TEXT PRIMARY KEY,
  email         TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role          TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'member')),
  first_name    TEXT NOT NULL DEFAULT '',
  birthdate     TEXT,
  profile       TEXT NOT NULL DEFAULT '{}',
  onboarded     INTEGER NOT NULL DEFAULT 0,
  created_at    BIGINT NOT NULL,
  last_seen_at  BIGINT
);
CREATE TABLE IF NOT EXISTS ${s}.sessions (
  token_hash TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES ${s}.users(id) ON DELETE CASCADE,
  created_at BIGINT NOT NULL,
  expires_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_user ON ${s}.sessions(user_id);
CREATE TABLE IF NOT EXISTS ${s}.photos (
  id         TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES ${s}.users(id) ON DELETE CASCADE,
  position   INTEGER NOT NULL,
  mime       TEXT NOT NULL,
  data       BYTEA NOT NULL,
  created_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS photos_user ON ${s}.photos(user_id, position);
CREATE TABLE IF NOT EXISTS ${s}.likes (
  id              TEXT PRIMARY KEY,
  user_id         TEXT NOT NULL UNIQUE REFERENCES ${s}.users(id) ON DELETE CASCADE,
  target_type     TEXT NOT NULL CHECK (target_type IN ('photo', 'prompt', 'profile')),
  target_ref      TEXT NOT NULL DEFAULT '',
  target_snapshot TEXT NOT NULL DEFAULT '{}',
  comment         TEXT NOT NULL DEFAULT '',
  date_idea       TEXT NOT NULL DEFAULT '',
  status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'matched', 'removed', 'unmatched')),
  created_at      BIGINT NOT NULL,
  decided_at      BIGINT,
  seen_by_owner   INTEGER NOT NULL DEFAULT 0,
  match_seen      INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS ${s}.messages (
  id         TEXT PRIMARY KEY,
  member_id  TEXT NOT NULL REFERENCES ${s}.users(id) ON DELETE CASCADE,
  from_owner INTEGER NOT NULL,
  body       TEXT NOT NULL,
  created_at BIGINT NOT NULL,
  read_at    BIGINT
);
CREATE INDEX IF NOT EXISTS messages_member ON ${s}.messages(member_id, created_at);
CREATE TABLE IF NOT EXISTS ${s}.settings (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
`;
