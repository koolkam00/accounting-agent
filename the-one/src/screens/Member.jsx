import { useState } from 'react';
import { Eye, Lock, LogOut, Mail, Pencil, Trash2 } from 'lucide-react';
import { Avatar, BackButton, Button, Sheet, TopBar, Wordmark, useToast } from '../components/ui.jsx';
import { ProfileView } from '../components/ProfileView.jsx';
import { BasicsFields, BirthdayInput, PhotoGrid, PromptList, basicsFrom, birthdayStatus, selfProfile } from '../components/ProfileFields.jsx';
import { MemberTabs } from '../components/Tabs.jsx';
import { useSession } from '../lib/session.jsx';
import { navigate, back } from '../lib/router.jsx';
import { api, clearCache } from '../lib/api.js';

export function MemberYou() {
  const { user, site, signOut } = useSession();
  const [deleting, setDeleting] = useState(false);
  const photo = user.photos[0]?.src;
  return (
    <div className="screen">
      <TopBar left={<h1 className="topbar-h1">You</h1>} />
      <main className="screen-body pad stack">
        <section className="me-card">
          <Avatar src={photo} name={user.firstName} size={104} className="me-avatar" />
          <h2 className="me-name">{user.firstName}{user.age != null && <span>{user.age}</span>}</h2>
          <div className="me-actions">
            <Button variant="primary" icon={Pencil} onClick={() => navigate('/you/edit')}>Edit profile</Button>
            <Button variant="soft" icon={Eye} onClick={() => navigate('/you/preview')}>Preview</Button>
          </div>
        </section>

        <section className="note-card">
          <Lock aria-hidden="true" />
          <p><b>Only {site.ownerName} can see your profile.</b> Nobody else, ever. Delete it whenever you like.</p>
        </section>

        <section className="list-card" aria-label="Account">
          <div className="list-row is-static"><Mail aria-hidden="true" /><span className="truncate">{user.email}</span></div>
          <button type="button" className="list-row" onClick={signOut}><LogOut aria-hidden="true" /> Log out</button>
          <button type="button" className="list-row is-danger" onClick={() => setDeleting(true)}><Trash2 aria-hidden="true" /> Delete account</button>
        </section>

        <footer className="fineprint">
          <Wordmark name={site.appName} />
          <span>A one-profile dating site, made by {site.ownerName}.</span>
        </footer>
      </main>
      <MemberTabs active="you" />
      <DeleteAccount open={deleting} onClose={() => setDeleting(false)} />
    </div>
  );
}

function DeleteAccount({ open, onClose }) {
  const { site, setUser } = useSession();
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      await api('/me', { method: 'DELETE', body: { password } });
      clearCache();
      setUser(null);
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };
  return (
    <Sheet open={open} onClose={onClose} variant="dialog" label="Delete account">
      <form onSubmit={submit}>
        <h2 className="dialog-title">Delete your account?</h2>
        <p className="dialog-body">Your profile, photos, like and messages are deleted for good. {site.ownerName} won’t be able to see any of it.</p>
        <label className="field-label" htmlFor="del-pw">Enter your password to confirm</label>
        <input id="del-pw" className="field" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="dialog-actions">
          <Button variant="soft" block onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="danger" block loading={busy} disabled={!password}>Delete</Button>
        </div>
      </form>
    </Sheet>
  );
}

export function EditProfile() {
  const { user, site, setUser } = useSession();
  const toast = useToast();
  const [firstName, setFirstName] = useState(user.firstName);
  const [birthdate, setBirthdate] = useState(user.birthdate ?? '');
  const [parts, setParts] = useState(null);
  const [prompts, setPrompts] = useState(user.profile.prompts ?? []);
  const [basics, setBasics] = useState(() => basicsFrom(user));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const dob = birthdayStatus(birthdate, parts);

  const save = async () => {
    setBusy(true);
    setError('');
    try {
      const res = await api('/me', { method: 'PATCH', body: { firstName, birthdate, prompts, ...basics } });
      setUser(res.user);
      toast('Saved');
      back('/you');
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };
  const canSave = firstName.trim() && dob.ok;

  return (
    <div className="screen">
      <TopBar
        left={<BackButton fallback="/you" />}
        title="Edit profile"
        right={<button type="button" className="topbar-action" onClick={save} disabled={!canSave || busy}>Save</button>}
      />
      <main className="screen-body pad edit">
        <section>
          <h2 className="section-title">Photos</h2>
          <PhotoGrid photos={user.photos} onChange={(photos) => setUser((u) => ({ ...u, photos }))} />
        </section>
        <section>
          <h2 className="section-title">Prompts</h2>
          <PromptList prompts={prompts} onChange={setPrompts} />
        </section>
        <section className="form-stack">
          <h2 className="section-title">About you</h2>
          <div>
            <label className="field-label" htmlFor="e-name">First name</label>
            <input id="e-name" className="field" value={firstName} onChange={(e) => setFirstName(e.target.value)} maxLength={30} autoComplete="given-name" />
          </div>
          <div>
            <p className="field-label">Birthday</p>
            <BirthdayInput value={birthdate} onChange={(v, p) => { setBirthdate(v); setParts(p); }} />
            <p className={`dob-status${dob.ok ? ' is-ok' : ''}`}>{dob.text}</p>
          </div>
        </section>
        <section>
          <h2 className="section-title">The basics</h2>
          <BasicsFields value={basics} onChange={setBasics} lookingForOptions={site.lookingFor} />
        </section>
        {error && <p className="form-error" role="alert">{error}</p>}
        <Button block loading={busy} disabled={!canSave} onClick={save}>Save changes</Button>
      </main>
    </div>
  );
}

export function MemberPreview() {
  const { user, site } = useSession();
  return (
    <div className="screen">
      <TopBar left={<BackButton fallback="/you" />} title="Preview" />
      <main className="screen-body">
        <p className="preview-banner"><Eye aria-hidden="true" /> This is exactly what {site.ownerName} sees.</p>
        <ProfileView profile={selfProfile(user)} />
      </main>
    </div>
  );
}
