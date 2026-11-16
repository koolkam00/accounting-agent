import { DatabaseSync } from 'node:sqlite';
import { SQLITE_SCHEMA } from './schema.js';

/**
 * Local storage: one SQLite file (built into Node 22.13+).
 * Exposes the same async interface as the Postgres store: one / all / run / tx.
 */
export function openSqliteStore(file) {
  const db = new DatabaseSync(file);
  db.exec('PRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON; PRAGMA busy_timeout = 5000;');
  db.exec(SQLITE_SCHEMA);

  const clean = (params) => params.map((p) => (p === undefined ? null : p));
  const q = {
    one: async (sql, params = []) => db.prepare(sql).get(...clean(params)) ?? undefined,
    all: async (sql, params = []) => db.prepare(sql).all(...clean(params)),
    run: async (sql, params = []) => ({ changes: Number(db.prepare(sql).run(...clean(params)).changes) }),
  };

  // One transaction at a time on the single connection.
  let queue = Promise.resolve();
  const tx = (fn) => {
    const job = queue.then(async () => {
      db.exec('BEGIN');
      try {
        const out = await fn(q);
        db.exec('COMMIT');
        return out;
      } catch (err) {
        db.exec('ROLLBACK');
        throw err;
      }
    });
    queue = job.catch(() => {});
    return job;
  };

  return { kind: 'sqlite', ...q, tx, close: () => db.close() };
}
