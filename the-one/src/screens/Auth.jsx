import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { BackButton, Button, Wordmark } from '../components/ui.jsx';
import { useSession } from '../lib/session.jsx';
import { navigate } from '../lib/router.jsx';
import { api } from '../lib/api.js';

export function Welcome() {
  const { site } = useSession();
  return (
    <div className="welcome">
      {site.heroPhoto && <img className="welcome-photo" src={site.heroPhoto} alt="" draggable="false" />}
      <div className="welcome-shade" aria-hidden="true" />
      <header className="welcome-top">
        <Wordmark name={site.appName} className="wordmark-light" />
      </header>
      <main className="welcome-body">
        <p className="welcome-kicker"><span className="live-dot" aria-hidden="true" />1 profile · 0 swiping</p>
        <h1 className="welcome-title">There’s only one profile here. <em>It’s a good one.</em></h1>
        <p className="welcome-lede">Make an account to see {site.ownerName}’s profile, like what you like, and maybe match.</p>
        <div className="welcome-actions">
          <Button variant="light" block onClick={() => navigate('/join')}>Create an account</Button>
          <Button variant="ghost-light" block onClick={() => navigate('/signin')}>I already have an account</Button>
        </div>
        <p className="welcome-fine">18+ only. Your profile is only ever visible to {site.ownerName}.</p>
      </main>
    </div>
  );
}

export function StepLayout({ progress, onBack, children, footer, className = '' }) {
  return (
    <div className={`screen step ${className}`}>
      <header className="step-top">
        {onBack ? <BackButton onClick={onBack} /> : <span className="icon-btn-spacer" />}
        {progress != null && (
          <div className="step-progress" role="progressbar" aria-label="Progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progress * 100)}>
            <span style={{ transform: `scaleX(${progress})` }} />
          </div>
        )}
        <span className="icon-btn-spacer" />
      </header>
      <main className="step-body">{children}</main>
      {footer && <footer className="step-footer">{footer}</footer>}
    </div>
  );
}

function PasswordField({ id, value, onChange, autoComplete, placeholder = 'Password' }) {
  const [show, setShow] = useState(false);
  return (
    <div className="field-suffix">
      <input
        id={id}
        className="field"
        type={show ? 'text' : 'password'}
        autoComplete={autoComplete}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        maxLength={200}
        required
      />
      <button type="button" className="field-eye" onClick={() => setShow(!show)} aria-label={show ? 'Hide password' : 'Show password'}>
        {show ? <EyeOff aria-hidden="true" /> : <Eye aria-hidden="true" />}
      </button>
    </div>
  );
}

export function Join() {
  const { site, setUser } = useSession();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()) && password.length >= 8;

  const submit = async (e) => {
    e.preventDefault();
    if (!valid) return;
    setBusy(true);
    setError('');
    try {
      const res = await api('/auth/signup', { method: 'POST', body: { email: email.trim(), password } });
      setUser(res.user);
      navigate('/start/name', { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <StepLayout
      progress={1 / 6}
      onBack={() => navigate('/', { replace: true })}
      footer={<Button type="submit" form="join" block loading={busy} disabled={!valid}>Continue</Button>}
    >
      <form id="join" onSubmit={submit} noValidate>
        <h1 className="step-title">First, an account.</h1>
        <p className="step-sub">Takes about a minute. Then you get to meet {site.ownerName}.</p>
        <div className="form-stack">
          <div>
            <label className="field-label" htmlFor="join-email">Email</label>
            <input id="join-email" className="field" type="email" inputMode="email" autoComplete="email" autoCapitalize="none" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
          </div>
          <div>
            <label className="field-label" htmlFor="join-password">Password</label>
            <PasswordField id="join-password" value={password} onChange={setPassword} autoComplete="new-password" placeholder="At least 8 characters" />
          </div>
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <p className="fine">By continuing you confirm you’re 18 or older. Your profile is only visible to {site.ownerName}, and you can delete it anytime.</p>
      </form>
    </StepLayout>
  );
}

export function SignIn() {
  const { site, setUser } = useSession();
  const subject = site.pronoun.subject;
  const tagline = subject === 'they' ? `${site.ownerName}’s right where you left them.` : `${subject[0].toUpperCase()}${subject.slice(1)}’s right where you left ${site.pronoun.object}.`;
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const res = await api('/auth/login', { method: 'POST', body: { email: email.trim(), password } });
      setUser(res.user);
      navigate(res.user.role === 'owner' ? '/likes' : '/discover', { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <StepLayout
      onBack={() => navigate('/', { replace: true })}
      footer={(
        <>
          <Button type="submit" form="signin" block loading={busy} disabled={!email || !password}>Sign in</Button>
          <button type="button" className="text-link" onClick={() => navigate('/join', { replace: true })}>New here? <b>Create an account</b></button>
        </>
      )}
    >
      <form id="signin" onSubmit={submit}>
        <h1 className="step-title">Welcome back.</h1>
        <p className="step-sub">{tagline}</p>
        <div className="form-stack">
          <div>
            <label className="field-label" htmlFor="si-email">Email</label>
            <input id="si-email" className="field" type="email" inputMode="email" autoComplete="email" autoCapitalize="none" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
          </div>
          <div>
            <label className="field-label" htmlFor="si-password">Password</label>
            <PasswordField id="si-password" value={password} onChange={setPassword} autoComplete="current-password" />
          </div>
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
      </form>
    </StepLayout>
  );
}
