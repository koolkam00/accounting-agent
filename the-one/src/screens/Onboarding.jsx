import { useState } from 'react';
import { Lock } from 'lucide-react';
import { Button, useToast } from '../components/ui.jsx';
import { StepLayout } from './Auth.jsx';
import { BasicsFields, BirthdayInput, PhotoGrid, PromptList, basicsFrom, birthdayStatus } from '../components/ProfileFields.jsx';
import { useSession } from '../lib/session.jsx';
import { navigate } from '../lib/router.jsx';
import { api } from '../lib/api.js';

export const STEPS = ['name', 'birthday', 'photos', 'prompts', 'basics'];

export function firstIncompleteStep(user, minPhotos) {
  if (!user.firstName) return 'name';
  if (!user.birthdate) return 'birthday';
  if (user.photos.length < minPhotos) return 'photos';
  return 'prompts';
}

export function Onboarding({ step }) {
  const { user, site, setUser } = useSession();
  const i = STEPS.indexOf(step);
  const props = {
    user,
    site,
    progress: (i + 2) / (STEPS.length + 1),
    onBack: i > 0 ? () => navigate(`/start/${STEPS[i - 1]}`, { replace: true }) : undefined,
    next: () => navigate(`/start/${STEPS[i + 1]}`),
    save: async (patch) => {
      const res = await api('/me', { method: 'PATCH', body: patch });
      setUser(res.user);
      return res.user;
    },
  };
  if (step === 'name') return <NameStep {...props} />;
  if (step === 'birthday') return <BirthdayStep {...props} />;
  if (step === 'photos') return <PhotosStep {...props} />;
  if (step === 'prompts') return <PromptsStep {...props} />;
  return <BasicsStep {...props} />;
}

function useSubmit(fn) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const run = async (e) => {
    e?.preventDefault();
    setBusy(true);
    setError('');
    try { await fn(); } catch (err) { setError(err.message); setBusy(false); }
  };
  return { busy, error, run };
}

function NameStep({ user, site, save, next, progress, onBack }) {
  const [name, setName] = useState(user.firstName);
  const { busy, error, run } = useSubmit(async () => { await save({ firstName: name }); next(); });
  return (
    <StepLayout progress={progress} onBack={onBack} footer={<Button type="submit" form="step" block loading={busy} disabled={!name.trim()}>Continue</Button>}>
      <form id="step" onSubmit={run}>
        <h1 className="step-title">What’s your first name?</h1>
        <p className="step-sub">It’s how you’ll show up to {site.ownerName}.</p>
        <input className="field-xl" autoFocus autoComplete="given-name" placeholder="First name" aria-label="First name" value={name} onChange={(e) => setName(e.target.value)} maxLength={30} />
        {error && <p className="form-error" role="alert">{error}</p>}
      </form>
    </StepLayout>
  );
}

function BirthdayStep({ user, save, next, progress, onBack }) {
  const [iso, setIso] = useState(user.birthdate ?? '');
  const [parts, setParts] = useState(null);
  const status = birthdayStatus(iso, parts);
  const { busy, error, run } = useSubmit(async () => { await save({ birthdate: iso }); next(); });
  return (
    <StepLayout progress={progress} onBack={onBack} footer={<Button type="submit" form="step" block loading={busy} disabled={!status.ok}>Continue</Button>}>
      <form id="step" onSubmit={run}>
        <h1 className="step-title">When’s your birthday?</h1>
        <p className="step-sub">Your profile shows your age, not the date.</p>
        <BirthdayInput value={iso} autoFocus onChange={(v, p) => { setIso(v); setParts(p); }} />
        <p className={`dob-status${status.ok ? ' is-ok' : ''}`} aria-live="polite">{status.text}</p>
        {error && <p className="form-error" role="alert">{error}</p>}
      </form>
    </StepLayout>
  );
}

function PhotosStep({ user, site, next, progress, onBack }) {
  const { setUser } = useSession();
  const min = site.minPhotos;
  const enough = user.photos.length >= min;
  return (
    <StepLayout
      progress={progress}
      onBack={onBack}
      footer={<Button block disabled={!enough} onClick={next}>{enough ? 'Continue' : `Add ${min - user.photos.length} more`}</Button>}
    >
      <h1 className="step-title">Add a few photos.</h1>
      <p className="step-sub">
        {min > 0 ? `At least ${min}. ` : ''}Ones where your face is easy to see work best.
      </p>
      <PhotoGrid photos={user.photos} onChange={(photos) => setUser((u) => ({ ...u, photos }))} />
      <p className="privacy-note"><Lock aria-hidden="true" /> Only {site.ownerName} will ever see these.</p>
    </StepLayout>
  );
}

function PromptsStep({ user, site, save, next, progress, onBack }) {
  const [prompts, setPrompts] = useState(user.profile.prompts ?? []);
  const { busy, error, run } = useSubmit(async () => { await save({ prompts }); next(); });
  const pronoun = site.pronoun.object;
  return (
    <StepLayout
      progress={progress}
      onBack={onBack}
      footer={<Button block loading={busy} onClick={run} variant={prompts.length ? 'primary' : 'soft'}>{prompts.length ? 'Continue' : 'Skip for now'}</Button>}
    >
      <h1 className="step-title">Give {pronoun} something to reply to.</h1>
      <p className="step-sub">Answer up to three prompts. Short and specific beats long and perfect.</p>
      <PromptList prompts={prompts} onChange={setPrompts} />
      {error && <p className="form-error" role="alert">{error}</p>}
    </StepLayout>
  );
}

function BasicsStep({ user, site, save, progress, onBack }) {
  const toast = useToast();
  const [basics, setBasics] = useState(() => basicsFrom(user));
  const { busy, error, run } = useSubmit(async () => {
    await save({ ...basics, onboarded: true });
    toast(`You’re in. Meet ${site.ownerName}.`);
    navigate('/discover', { replace: true });
  });
  return (
    <StepLayout progress={progress} onBack={onBack} footer={<Button block loading={busy} onClick={run}>Finish</Button>}>
      <h1 className="step-title">A few basics.</h1>
      <p className="step-sub">All optional. Fill in whatever you’d want {site.ownerName} to know.</p>
      <BasicsFields value={basics} onChange={setBasics} lookingForOptions={site.lookingFor} />
      {error && <p className="form-error" role="alert">{error}</p>}
    </StepLayout>
  );
}
