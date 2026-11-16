import { useEffect, useSyncExternalStore } from 'react';

const listeners = new Set();
const emit = () => listeners.forEach((fn) => fn());

// Count how deep we are inside the app, so "back" never leaves the site
// (e.g. when someone opened a link straight from Instagram).
let depth = window.history.state?.depth ?? 0;
window.addEventListener('popstate', (e) => {
  depth = e.state?.depth ?? 0;
  emit();
});

const subscribe = (fn) => { listeners.add(fn); return () => listeners.delete(fn); };
const snapshot = () => window.location.pathname;

export function navigate(to, { replace = false } = {}) {
  if (to === window.location.pathname) return;
  if (replace) {
    window.history.replaceState({ depth }, '', to);
  } else {
    depth += 1;
    window.history.pushState({ depth }, '', to);
  }
  emit();
  window.scrollTo(0, 0);
}

export function back(fallback = '/') {
  if ((window.history.state?.depth ?? 0) > 0) window.history.back();
  else navigate(fallback, { replace: true });
}

export const usePath = () => useSyncExternalStore(subscribe, snapshot);

/** Match "/likes/:id" style patterns. Returns params or null. */
export function match(pattern, path) {
  const p = pattern.split('/').filter(Boolean);
  const s = path.split('/').filter(Boolean);
  if (p.length !== s.length) return null;
  const params = {};
  for (let i = 0; i < p.length; i += 1) {
    if (p[i].startsWith(':')) {
      try { params[p[i].slice(1)] = decodeURIComponent(s[i]); } catch { return null; }
    } else if (p[i] !== s[i]) return null;
  }
  return params;
}

export function Redirect({ to }) {
  useEffect(() => { navigate(to, { replace: true }); }, [to]);
  return null;
}

export function Link({ to, replace, onClick, ...props }) {
  return (
    <a
      href={to}
      onClick={(e) => {
        onClick?.(e);
        if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
        e.preventDefault();
        navigate(to, { replace });
      }}
      {...props}
    />
  );
}
