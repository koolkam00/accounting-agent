import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { ChevronLeft, Heart } from 'lucide-react';
import { back } from '../lib/router.jsx';

// ── Brand ────────────────────────────────────────────────────────────────────
export function Wordmark({ name = 'the one', className = '' }) {
  const [first, ...rest] = name.trim().split(/\s+/);
  return (
    <span className={`wordmark ${className}`} role="img" aria-label={name}>
      {rest.length ? (
        <>
          <em aria-hidden="true">{first}</em>
          <b aria-hidden="true">{rest.join(' ')}</b>
        </>
      ) : (
        <b aria-hidden="true">{first}</b>
      )}
      <i className="wordmark-dot" aria-hidden="true" />
    </span>
  );
}

// ── Buttons ──────────────────────────────────────────────────────────────────
export function Spinner({ className = '' }) {
  return <span className={`spinner ${className}`} role="progressbar" aria-label="Loading" />;
}

export function Button({ variant = 'primary', block, loading, children, className = '', icon: Icon, type = 'button', disabled, ...props }) {
  return (
    <button
      type={type}
      {...props}
      className={`btn btn-${variant}${block ? ' btn-block' : ''}${loading ? ' is-loading' : ''} ${className}`}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
    >
      <span className="btn-content">
        {Icon && <Icon className="btn-icon" aria-hidden="true" />}
        {children}
      </span>
      {loading && <Spinner className="btn-spinner" />}
    </button>
  );
}

export function IconButton({ icon: Icon, label, className = '', ...props }) {
  return (
    <button type="button" className={`icon-btn ${className}`} aria-label={label} title={label} {...props}>
      <Icon aria-hidden="true" />
    </button>
  );
}

// ── Layout ───────────────────────────────────────────────────────────────────
function useScrolled(threshold = 4) {
  const [scrolled, setScrolled] = useState(() => window.scrollY > threshold);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > threshold);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, [threshold]);
  return scrolled;
}

export function TopBar({ left, title, right, className = '' }) {
  const scrolled = useScrolled();
  return (
    <header className={`topbar${scrolled ? ' is-scrolled' : ''} ${className}`}>
      <div className="topbar-side">{left}</div>
      {title != null && <div className="topbar-title">{title}</div>}
      <div className="topbar-side topbar-right">{right}</div>
    </header>
  );
}

export function BackButton({ fallback = '/', onClick }) {
  return <IconButton icon={ChevronLeft} label="Back" className="icon-btn-back" onClick={onClick ?? (() => back(fallback))} />;
}

export function Avatar({ src, name, size = 48, className = '' }) {
  return (
    <span className={`avatar ${className}`} style={{ width: size, height: size }}>
      {src ? <img src={src} alt="" draggable="false" /> : <span className="avatar-initial" style={{ fontSize: size * 0.42 }}>{name?.[0] ?? '?'}</span>}
    </span>
  );
}

export function EmptyState({ art, title, children, action }) {
  return (
    <div className="empty">
      {art && <div className="empty-art">{art}</div>}
      <h2 className="empty-title">{title}</h2>
      {children && <p className="empty-body">{children}</p>}
      {action && <div className="empty-action">{action}</div>}
    </div>
  );
}

// ── Overlays ─────────────────────────────────────────────────────────────────
function useDelayedUnmount(open, ms) {
  const [mounted, setMounted] = useState(open);
  const [closing, setClosing] = useState(false);
  useEffect(() => {
    if (open) { setMounted(true); setClosing(false); return undefined; }
    if (!mounted) return undefined;
    setClosing(true);
    const t = setTimeout(() => { setMounted(false); setClosing(false); }, ms);
    return () => clearTimeout(t);
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps
  return { mounted, closing };
}

let openOverlays = 0;
function useBodyLock(active) {
  useEffect(() => {
    if (!active) return undefined;
    openOverlays += 1;
    document.documentElement.classList.add('is-locked');
    return () => {
      openOverlays -= 1;
      if (openOverlays === 0) document.documentElement.classList.remove('is-locked');
    };
  }, [active]);
}

/**
 * Bottom sheet (default) or centred dialog. Keeps showing its last content while
 * animating out, so callers can clear their state the moment it closes.
 */
export function Sheet({ open, onClose, label, children, variant = 'sheet', className = '' }) {
  const { mounted, closing } = useDelayedUnmount(open, 280);
  const last = useRef(children);
  if (open) last.current = children;
  const panel = useRef(null);
  const drag = useRef(null);
  useBodyLock(mounted);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => { if (e.key === 'Escape') onClose?.(); };
    document.addEventListener('keydown', onKey);
    const prev = document.activeElement;
    requestAnimationFrame(() => {
      const el = panel.current;
      if (el && !el.contains(document.activeElement)) el.focus({ preventScroll: true });
    });
    return () => { document.removeEventListener('keydown', onKey); prev?.focus?.({ preventScroll: true }); };
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!mounted) return null;

  // Drag the grabber down to dismiss.
  const onPointerDown = (e) => {
    if (variant !== 'sheet') return;
    drag.current = { y: e.clientY, dy: 0 };
    e.currentTarget.setPointerCapture(e.pointerId);
  };
  const onPointerMove = (e) => {
    if (!drag.current) return;
    drag.current.dy = Math.max(0, e.clientY - drag.current.y);
    panel.current.style.transform = `translateY(${drag.current.dy}px)`;
  };
  const onPointerUp = () => {
    if (!drag.current) return;
    const { dy } = drag.current;
    drag.current = null;
    panel.current.style.transform = '';
    if (dy > 90) onClose?.();
  };

  return createPortal(
    <div className={`overlay overlay-${variant}${closing ? ' is-closing' : ''}`} role="dialog" aria-modal="true" aria-label={label}>
      <div className="overlay-backdrop" onClick={onClose} />
      <div className={`panel panel-${variant} ${className}`} ref={panel} tabIndex={-1}>
        {variant === 'sheet' && (
          <div className="sheet-grab" onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerCancel={onPointerUp}>
            <span className="sheet-handle" />
          </div>
        )}
        {open ? children : last.current}
      </div>
    </div>,
    document.body,
  );
}

/** Full-screen moment (like sent, it's a match). */
export function Moment({ open, onClose, label, className = '', children }) {
  const { mounted, closing } = useDelayedUnmount(open, 320);
  const last = useRef(children);
  if (open) last.current = children;
  useBodyLock(mounted);
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => { if (e.key === 'Escape') onClose?.(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!mounted) return null;
  return createPortal(
    <div className={`moment ${className}${closing ? ' is-closing' : ''}`} role="dialog" aria-modal="true" aria-label={label}>
      {open ? children : last.current}
    </div>,
    document.body,
  );
}

export function FloatingHearts({ count = 14 }) {
  return (
    <div className="float-hearts" aria-hidden="true">
      {Array.from({ length: count }, (_, i) => {
        const duration = 6 + ((i * 7) % 6);
        return (
          <Heart
            key={i}
            className="float-heart"
            fill="currentColor"
            strokeWidth={0}
            style={{
              left: `${(i * 37 + 11) % 100}%`,
              '--s': String(0.55 + ((i * 13) % 9) / 10),
              '--r': `${((i * 29) % 50) - 25}deg`,
              animationDuration: `${duration}s`,
              animationDelay: `${-((i * 1.7) % duration)}s`,
            }}
          />
        );
      })}
    </div>
  );
}

// ── Toasts ───────────────────────────────────────────────────────────────────
const ToastContext = createContext(() => {});

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null);
  const show = useCallback((message, { tone = 'default', duration = 2600 } = {}) => {
    const id = Math.random();
    setToast({ id, message, tone });
    setTimeout(() => setToast((t) => (t?.id === id ? null : t)), duration);
  }, []);
  return (
    <ToastContext.Provider value={show}>
      {children}
      {toast && createPortal(
        <div className={`toast toast-${toast.tone}`} role="status" key={toast.id}>{toast.message}</div>,
        document.body,
      )}
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
