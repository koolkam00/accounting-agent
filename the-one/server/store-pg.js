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

/** Hosted storage: Postgres (e.g. Supabase). Same interface as the SQLite store. */
export function openPgStore(url) {
  if (!url) throw new Error('DATABASE_URL is not set.');
  // Strip libpq-style ssl params; TLS is configured explicitly below.
  const connectionString = url.replace(/([?&])sslmode=[^&]*&?/, '$1').replace(/[?&]$/, '');
  const pool = new pg.Pool({
    connectionString,
    ssl: sslOptions(),
    max: Number(process.env.PG_POOL_MAX) || 3,
    idleTimeoutMillis: 10_000,
    connectionTimeoutMillis: 10_000,
  });
  pool.on('error', (err) => console.error('[db] idle connection error:', err.message));

  // Our SQL uses "?" placeholders; Postgres wants $1, $2, ...
  const convert = (sql) => {
    let i = 0;
    return sql.replace(/\?/g, () => `$${++i}`);
  };
  const wrap = (client) => ({
    one: async (sql, params = []) => (await client.query(convert(sql), params)).rows[0],
    all: async (sql, params = []) => (await client.query(convert(sql), params)).rows,
    run: async (sql, params = []) => ({ changes: (await client.query(convert(sql), params)).rowCount ?? 0 }),
  });

  const tx = async (fn) => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      const out = await fn(wrap(client));
      await client.query('COMMIT');
      return out;
    } catch (err) {
      await client.query('ROLLBACK').catch(() => {});
      throw err;
    } finally {
      client.release();
    }
  };

  return { kind: 'pg', ...wrap(pool), tx, close: () => pool.end() };
}
