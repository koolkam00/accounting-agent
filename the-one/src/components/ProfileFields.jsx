import { useEffect, useRef, useState } from 'react';
import { ChevronRight, Pencil, Plus, Star, Trash2, X } from 'lucide-react';
import { Button, Sheet, Spinner } from './ui.jsx';
import { api } from '../lib/api.js';
import { photoToDataUrl } from '../lib/image.js';
import { PROMPTS } from '../lib/content.js';
import { ageFrom, heightLabel, HEIGHTS, isRealDate } from '../lib/format.js';

// ── Photos ───────────────────────────────────────────────────────────────────
export function PhotoGrid({ photos, onChange }) {
  const input = useRef(null);
  const [uploading, setUploading] = useState(0);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);

  const add = async (files) => {
    setError('');
    const list = [...files].slice(0, Math.max(0, 6 - photos.length - uploading));
    for (const file of list) {
      setUploading((n) => n + 1);
      try {
        const dataUrl = await photoToDataUrl(file);
        const res = await api('/me/photos', { method: 'POST', body: { dataUrl } });
        onChange(res.photos);
      } catch (err) {
        setError(err.message);
      } finally {
        setUploading((n) => n - 1);
      }
    }
  };

  const remove = async (id) => {
    setSelected(null);
    try { onChange((await api(`/me/photos/${id}`, { method: 'DELETE' })).photos); } catch (err) { setError(err.message); }
  };

  const makeMain = async (id) => {
    setSelected(null);
    const ids = [id, ...photos.map((p) => p.id).filter((x) => x !== id)];
    try { onChange((await api('/me/photos/order', { method: 'PUT', body: { ids } })).photos); } catch (err) { setError(err.message); }
  };

  const slots = Array.from({ length: 6 }, (_, i) => i);
  return (
    <div>
      <div className="photo-grid">
        {slots.map((i) => {
          const p = photos[i];
          if (p) {
            return (
              <button type="button" className="photo-slot is-filled" key={p.id} onClick={() => setSelected(p)} aria-label={`Photo ${i + 1} options`}>
                <img src={p.src} alt="" draggable="false" />
                {i === 0 && <span className="photo-slot-tag">Main</span>}
              </button>
            );
          }
          if (i < photos.length + uploading) {
            return <div className="photo-slot is-loading" key={`u${i}`}><Spinner /></div>;
          }
          return (
            <button type="button" className={`photo-slot${i === photos.length + uploading ? ' is-next' : ''}`} key={`e${i}`} onClick={() => input.current?.click()} aria-label="Add a photo">
              <span className="photo-slot-plus"><Plus aria-hidden="true" /></span>
            </button>
          );
        })}
      </div>
      <input
        ref={input}
        type="file"
        accept="image/*"
        multiple
        hidden
        data-testid="photo-input"
        onChange={(e) => { add(e.target.files); e.target.value = ''; }}
      />
      {error && <p className="form-error" role="alert">{error}</p>}

      <Sheet open={!!selected} onClose={() => setSelected(null)} label="Photo options">
        {selected && (
          <div className="action-list">
            <img className="action-thumb" src={selected.src} alt="" />
            {photos[0]?.id !== selected.id && (
              <button type="button" className="action-row" onClick={() => makeMain(selected.id)}>
                <Star aria-hidden="true" /> Make this my main photo
              </button>
            )}
            <button type="button" className="action-row is-danger" onClick={() => remove(selected.id)}>
              <Trash2 aria-hidden="true" /> Remove photo
            </button>
            <button type="button" className="action-row is-muted" onClick={() => setSelected(null)}>
              Cancel
            </button>
          </div>
        )}
      </Sheet>
    </div>
  );
}

// ── Prompts ──────────────────────────────────────────────────────────────────
export function PromptList({ prompts, onChange }) {
  const [picking, setPicking] = useState(false);
  const [editing, setEditing] = useState(null);

  const save = (answer) => {
    const next = [...prompts];
    const entry = { question: editing.question, answer: answer.trim() };
    if (editing.index >= 0) next[editing.index] = entry; else next.push(entry);
    onChange(next);
    setEditing(null);
  };
  const remove = () => {
    onChange(prompts.filter((_, i) => i !== editing.index));
    setEditing(null);
  };

  return (
    <div className="prompt-list">
      {prompts.map((p, i) => (
        <button type="button" className={`card prompt-card prompt-card-edit tone-${i % 2 === 0 ? 'ink' : 'light'}`} key={p.question} onClick={() => setEditing({ index: i, ...p })}>
          <p className="prompt-q">{p.question}</p>
          <p className="prompt-a">{p.answer}</p>
          <span className="prompt-edit" aria-hidden="true"><Pencil /></span>
          <span className="sr-only">Edit</span>
        </button>
      ))}
      {prompts.length < 3 && (
        <button type="button" className="prompt-add" onClick={() => setPicking(true)}>
          <span className="prompt-add-icon"><Plus aria-hidden="true" /></span>
          <span>
            <b>{prompts.length ? 'Add another prompt' : 'Add a prompt'}</b>
            <small>{3 - prompts.length} left</small>
          </span>
        </button>
      )}

      <Sheet open={picking} onClose={() => setPicking(false)} label="Pick a prompt" className="sheet-tall">
        <h2 className="sheet-title">Pick a prompt</h2>
        <ul className="prompt-options">
          {PROMPTS.filter((q) => !prompts.some((p) => p.question === q)).map((q) => (
            <li key={q}>
              <button type="button" onClick={() => { setPicking(false); setEditing({ index: -1, question: q, answer: '' }); }}>
                <span>{q}</span>
                <ChevronRight aria-hidden="true" />
              </button>
            </li>
          ))}
        </ul>
      </Sheet>

      <Sheet open={!!editing} onClose={() => setEditing(null)} label="Answer the prompt">
        {editing && <AnswerForm key={`${editing.index}:${editing.question}`} editing={editing} onSave={save} onRemove={remove} />}
      </Sheet>
    </div>
  );
}

function AnswerForm({ editing, onSave, onRemove }) {
  const [answer, setAnswer] = useState(editing.answer);
  const ref = useRef(null);
  useEffect(() => { const t = setTimeout(() => ref.current?.focus(), 320); return () => clearTimeout(t); }, []);
  const MAX = 200;
  return (
    <form onSubmit={(e) => { e.preventDefault(); if (answer.trim()) onSave(answer); }}>
      <p className="sheet-kicker">{editing.question}</p>
      <div className="field-wrap">
        <textarea
          ref={ref}
          className="field field-area field-answer"
          rows={4}
          maxLength={MAX}
          placeholder="Your answer"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          aria-label={editing.question}
        />
        <span className="field-count">{MAX - answer.length}</span>
      </div>
      <div className="sheet-actions">
        {editing.index >= 0 && <Button variant="soft" icon={Trash2} onClick={onRemove}>Remove</Button>}
        <Button type="submit" variant="primary" block disabled={!answer.trim()}>Save answer</Button>
      </div>
    </form>
  );
}

// ── Birthday ─────────────────────────────────────────────────────────────────
const splitDate = (iso) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || '');
  return m ? { m: m[2], d: m[3], y: m[1] } : { m: '', d: '', y: '' };
};

export function toIso({ m, d, y }) {
  if (m.length < 1 || d.length < 1 || y.length !== 4) return '';
  const [Y, M, D] = [Number(y), Number(m), Number(d)];
  if (!isRealDate(Y, M, D) || Y < 1900) return '';
  return `${y}-${String(M).padStart(2, '0')}-${String(D).padStart(2, '0')}`;
}

export function BirthdayInput({ value, onChange, autoFocus }) {
  const [parts, setParts] = useState(() => splitDate(value));
  const refs = { m: useRef(null), d: useRef(null), y: useRef(null) };
  const order = ['m', 'd', 'y'];
  const len = { m: 2, d: 2, y: 4 };

  const set = (key, raw) => {
    const v = raw.replace(/\D/g, '').slice(0, len[key]);
    const next = { ...parts, [key]: v };
    setParts(next);
    onChange(toIso(next), next);
    const i = order.indexOf(key);
    if (v.length === len[key] && i < 2) refs[order[i + 1]].current?.focus();
  };
  const onKeyDown = (key) => (e) => {
    const i = order.indexOf(key);
    if (e.key === 'Backspace' && !parts[key] && i > 0) refs[order[i - 1]].current?.focus();
  };

  return (
    <div className="dob" role="group" aria-label="Birthday">
      {order.map((key, i) => (
        <div className={`dob-part dob-${key}`} key={key}>
          <input
            ref={refs[key]}
            className="dob-input"
            inputMode="numeric"
            autoComplete={key === 'm' ? 'bday-month' : key === 'd' ? 'bday-day' : 'bday-year'}
            placeholder={key === 'm' ? 'MM' : key === 'd' ? 'DD' : 'YYYY'}
            aria-label={key === 'm' ? 'Month' : key === 'd' ? 'Day' : 'Year'}
            value={parts[key]}
            autoFocus={autoFocus && i === 0}
            onChange={(e) => set(key, e.target.value)}
            onKeyDown={onKeyDown(key)}
          />
          {i < 2 && <span className="dob-sep" aria-hidden="true">/</span>}
        </div>
      ))}
    </div>
  );
}

export function birthdayStatus(iso, parts) {
  if (!iso) {
    const complete = parts && parts.y?.length === 4 && parts.m && parts.d;
    return complete ? { ok: false, text: 'That date doesn’t exist.' } : { ok: false, text: '' };
  }
  const age = ageFrom(iso);
  if (age < 18) return { ok: false, text: 'You need to be 18 or older to join.' };
  if (age > 100) return { ok: false, text: 'Double-check the year.' };
  return { ok: true, text: `You’re ${age}` };
}

// ── Basics ───────────────────────────────────────────────────────────────────
export function BasicsFields({ value, onChange, lookingForOptions }) {
  const set = (k) => (e) => onChange({ ...value, [k]: e.target.value });
  return (
    <div className="form-stack">
      <div>
        <label className="field-label" htmlFor="f-location">Where do you live?</label>
        <input id="f-location" className="field" placeholder="City or neighborhood" autoComplete="address-level2" value={value.location} onChange={set('location')} maxLength={60} />
      </div>
      <div>
        <label className="field-label" htmlFor="f-job">What do you do?</label>
        <input id="f-job" className="field" placeholder="Job title, or what keeps you busy" value={value.job} onChange={set('job')} maxLength={60} />
      </div>
      <div>
        <label className="field-label" htmlFor="f-school">School <span>optional</span></label>
        <input id="f-school" className="field" placeholder="Where you studied" value={value.school} onChange={set('school')} maxLength={60} />
      </div>
      <div>
        <label className="field-label" htmlFor="f-height">Height</label>
        <div className="select-wrap">
          <select id="f-height" className="field" value={value.height ?? ''} onChange={(e) => onChange({ ...value, height: e.target.value ? Number(e.target.value) : null })}>
            <option value="">Prefer not to say</option>
            {HEIGHTS.map((h) => <option key={h} value={h}>{heightLabel(h)}</option>)}
          </select>
          <ChevronRight className="select-chevron" aria-hidden="true" />
        </div>
      </div>
      <div>
        <p className="field-label">Looking for</p>
        <div className="chips" role="radiogroup" aria-label="Looking for">
          {lookingForOptions.map((o) => (
            <button
              key={o}
              type="button"
              role="radio"
              aria-checked={value.lookingFor === o}
              className={`chip${value.lookingFor === o ? ' is-on' : ''}`}
              onClick={() => onChange({ ...value, lookingFor: value.lookingFor === o ? '' : o })}
            >
              {o}
            </button>
          ))}
        </div>
      </div>
      <div>
        <label className="field-label" htmlFor="f-ig">Instagram <span>optional</span></label>
        <div className="field-prefix">
          <span aria-hidden="true">@</span>
          <input id="f-ig" className="field" placeholder="yourhandle" autoCapitalize="none" autoCorrect="off" spellCheck="false" value={value.instagram} onChange={(e) => onChange({ ...value, instagram: e.target.value.replace(/^@+/, '') })} maxLength={30} />
          {value.instagram && (
            <button type="button" className="field-clear" aria-label="Clear" onClick={() => onChange({ ...value, instagram: '' })}><X aria-hidden="true" /></button>
          )}
        </div>
      </div>
    </div>
  );
}

export const basicsFrom = (user) => ({
  location: user.profile.location ?? '',
  job: user.profile.job ?? '',
  school: user.profile.school ?? '',
  height: user.profile.height ?? null,
  lookingFor: user.profile.lookingFor ?? '',
  instagram: user.profile.instagram ?? '',
});

/** Build the same profile shape the owner sees, from the signed-in member's data. */
export function selfProfile(user) {
  const p = user.profile;
  const facts = [
    p.height && { key: 'height', value: heightLabel(p.height) },
    p.location && { key: 'location', value: p.location },
    p.job && { key: 'job', value: p.job },
    p.school && { key: 'school', value: p.school },
    p.lookingFor && { key: 'lookingFor', value: p.lookingFor },
    p.instagram && { key: 'instagram', value: `@${p.instagram}` },
  ].filter(Boolean);
  return {
    name: user.firstName,
    age: user.age,
    photos: user.photos,
    prompts: (p.prompts ?? []).map((q, i) => ({ id: `q${i}`, ...q })),
    facts,
  };
}
