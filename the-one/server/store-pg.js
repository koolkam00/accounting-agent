import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import pg from 'pg';

// BIGINT (timestamps, counts) back as plain numbers.
pg.types.setTypeParser(pg.types.builtins.INT8, (v) => Number(v));

const HERE = path.dirname(fileURLToPath(import.meta.url));

/**
 * TLS for the database connection.
 *   DATABASE_SSL=verify (default)  encrypt and verify, trusting Supabase's root CA
 *   DATABASE_SSL=off               plain connection (local test databases only)
 */
function sslOptions() {
  const mode = process.env.DATABASE_SSL || 'verify';
  if (mode === 'off') return false;
  const ca = fs.readFileSync(path.join(HERE, 'certs', 'supabase-root-2021.crt'), 'utf8');
  return { ca, rejectUnauthorized: true };
}

/**
 * Supabase runs its connection pooler on a few clusters (aws-0-…, aws-1-…).
 * If the one in DATABASE_URL doesn't know this project, try its siblings.
 */
function poolerCandidates(connectionString) {
  let url;
  try { url = new URL(connectionString); } catch { return [connectionString]; }
  const m = /^aws-(\d+)-(.+\.pooler\.supabase\.com)$/.exec(url.hostname);
  if (!m) return [connectionString];
  const others = ['0', '1', '2'].filter((n) => n !== m[1]).map((n) => {
    const alt = new URL(connectionString);
    alt.hostname = `aws-${n}-${m[2]}`;
    return alt.toString();
  });
  return [connectionString, ...others];
}

const wrongCluster = (err) => /tenant or user not found/i.test(String(err?.message));

/** Hosted storage: Postgres (e.g. Supabase). Same interface as the SQLite store. */
export function openPgStore(url) {
  if (!url) throw new Error('DATABASE_URL is not set.');
  // TLS is configured explicitly, so drop libpq-style ssl params from the URL.
  const connectionString = url.replace(/([?&])sslmode=[^&]*&?/, '$1').replace(/[?&]$/, '');
  const candidates = poolerCandidates(connectionString);
  let index = 0;

  const makePool = (cs) => {
    const p = new pg.Pool({
      connectionString: cs,
      ssl: sslOptions(),
      max: Number(process.env.PG_POOL_MAX) || 3,
      idleTimeoutMillis: 10_000,
      connectionTimeoutMillis: 10_000,
    });
    p.on('error', (err) => console.error('[db] idle connection error:', err.message));
    return p;
  };
  let pool = makePool(candidates[0]);

  // Run fn(pool); if the pooler says this project lives elsewhere, move to the next host once.
  const withPool = async (fn) => {
    for (;;) {
      try {
        return await fn(pool);
      } catch (err) {
        if (!wrongCluster(err) || index >= candidates.length - 1) throw err;
        const old = pool;
        index += 1;
        pool = makePool(candidates[index]);
        old.end().catch(() => {});
        console.warn(`[db] trying pooler host ${new URL(candidates[index]).hostname}`);
      }
    }
  };

  // Our SQL uses "?" placeholders; Postgres wants $1, $2, ...
  const convert = (sql) => {
    let i = 0;
    return sql.replace(/\?/g, () => `$${++i}`);
  };
  const wrap = (run) => ({
    one: async (sql, params = []) => (await run((c) => c.query(convert(sql), params))).rows[0],
    all: async (sql, params = []) => (await run((c) => c.query(convert(sql), params))).rows,
    run: async (sql, params = []) => ({ changes: (await run((c) => c.query(convert(sql), params))).rowCount ?? 0 }),
  });

  const tx = (fn) => withPool(async (p) => {
    const client = await p.connect();
    try {
      await client.query('BEGIN');
      const out = await fn(wrap((use) => use(client)));
      await client.query('COMMIT');
      return out;
    } catch (err) {
      await client.query('ROLLBACK').catch(() => {});
      throw err;
    } finally {
      client.release();
    }
  });

  return { kind: 'pg', ...wrap(withPool), tx, close: () => pool.end() };
}
