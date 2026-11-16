import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api, clearCache } from './api.js';

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [state, setState] = useState({ status: 'loading', site: null, user: null });

  const refresh = useCallback(async () => {
    const data = await api('/session');
    setState({ status: 'ready', site: data.site, user: data.user });
    return data.user;
  }, []);

  useEffect(() => {
    refresh().catch(() => setState((s) => ({ ...s, status: 'error' })));
  }, [refresh]);

  // Keep badges (new likes, unread messages, matches) fresh.
  const signedIn = !!state.user;
  useEffect(() => {
    if (!signedIn) return undefined;
    const tick = () => { if (document.visibilityState === 'visible') refresh().catch(() => {}); };
    const t = setInterval(tick, 10_000);
    document.addEventListener('visibilitychange', tick);
    return () => { clearInterval(t); document.removeEventListener('visibilitychange', tick); };
  }, [signedIn, refresh]);

  const setUser = useCallback((user) => setState((s) => ({
    ...s,
    user: typeof user === 'function' ? user(s.user) : user,
  })), []);

  const signOut = useCallback(async () => {
    await api('/auth/logout', { method: 'POST' }).catch(() => {});
    clearCache();
    setState((s) => ({ ...s, user: null }));
  }, []);

  const value = useMemo(() => ({ ...state, refresh, setUser, signOut }), [state, refresh, setUser, signOut]);
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export const useSession = () => useContext(SessionContext);
