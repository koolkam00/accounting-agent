import { useCallback, useEffect, useRef, useState } from 'react';

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

export async function api(path, { method = 'GET', body } = {}) {
  let res;
  try {
    res = await fetch(`/api${path}`, {
      method,
      credentials: 'same-origin',
      headers: {
        'X-Requested-With': 'the-one',
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, 'You seem to be offline. Check your connection and try again.');
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, data.error || 'Something went wrong.');
  return data;
}

// Stale-while-revalidate cache so going back to a screen doesn't flash a spinner.
const cache = new Map();
export const invalidate = (path) => cache.delete(path);
export const clearCache = () => cache.clear();

export function useResource(path, { interval = 0 } = {}) {
  const [state, setState] = useState(() => ({ data: path ? cache.get(path) : undefined, error: null }));
  const current = useRef(path);
  current.current = path;

  const load = useCallback(async () => {
    if (!path) return undefined;
    try {
      const data = await api(path);
      cache.set(path, data);
      if (current.current === path) setState({ data, error: null });
      return data;
    } catch (error) {
      if (current.current === path) setState((s) => ({ data: s.data, error }));
      return undefined;
    }
  }, [path]);

  useEffect(() => {
    setState({ data: path ? cache.get(path) : undefined, error: null });
    load();
    if (!interval) return undefined;
    const t = setInterval(() => { if (document.visibilityState === 'visible') load(); }, interval);
    const onVisible = () => { if (document.visibilityState === 'visible') load(); };
    document.addEventListener('visibilitychange', onVisible);
    return () => { clearInterval(t); document.removeEventListener('visibilitychange', onVisible); };
  }, [path, interval, load]);

  const mutate = useCallback((updater) => {
    setState((s) => {
      const data = typeof updater === 'function' ? updater(s.data) : updater;
      if (path) cache.set(path, data);
      return { ...s, data };
    });
  }, [path]);

  return { data: state.data, error: state.error, loading: state.data === undefined && !state.error, reload: load, mutate };
}
