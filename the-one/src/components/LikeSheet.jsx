import { useEffect, useState } from 'react';
import { Heart } from 'lucide-react';
import { Button, Sheet } from './ui.jsx';
import { DATE_IDEAS } from '../lib/content.js';
import { api } from '../lib/api.js';

const MAX = 240;

export function LikeSheet({ target, ownerName, ownerPhoto, onClose, onSent }) {
  const [comment, setComment] = useState('');
  const [idea, setIdea] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (target) { setComment(''); setIdea(''); setError(''); setBusy(false); }
  }, [target]);

  const send = async () => {
    setBusy(true);
    setError('');
    try {
      const res = await api('/likes', {
        method: 'POST',
        body: { targetType: target.type, targetRef: target.ref ?? '', comment, dateIdea: idea },
      });
      onSent(res.user);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  const item = target?.item;
  const heading = target?.type === 'photo' ? `${ownerName}’s photo`
    : target?.type === 'prompt' ? `${ownerName}’s answer` : ownerName;

  return (
    <Sheet open={!!target} onClose={busy ? undefined : onClose} label={`Like ${heading}`} className="like-sheet">
      {target && (
        <>
          <div className="like-stage" aria-hidden="true">
            {target.type === 'prompt' ? (
              <div className="like-polaroid like-polaroid-prompt">
                <p className="prompt-q">{item.question}</p>
                <p className="prompt-a">{item.answer}</p>
              </div>
            ) : (
              <div className="like-polaroid">
                <img src={target.type === 'photo' ? item.src : ownerPhoto} alt="" draggable="false" />
              </div>
            )}
            <span className="like-stage-heart"><Heart fill="currentColor" strokeWidth={0} /></span>
          </div>

          <h2 className="sheet-title like-title">Like {heading}</h2>

          <label className="field-label" htmlFor="like-comment">Add a comment <span>optional</span></label>
          <div className="field-wrap">
            <textarea
              id="like-comment"
              className="field field-area"
              rows={3}
              maxLength={MAX}
              placeholder={target.type === 'prompt' ? 'Reply to this…' : 'Say something about this…'}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
            {comment.length > MAX - 60 && <span className="field-count">{MAX - comment.length}</span>}
          </div>

          <p className="field-label">Suggest a first date <span>optional</span></p>
          <div className="chips" role="radiogroup" aria-label="Suggest a first date">
            {DATE_IDEAS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                role="radio"
                aria-checked={idea === id}
                className={`chip${idea === id ? ' is-on' : ''}`}
                onClick={() => setIdea(idea === id ? '' : id)}
              >
                <Icon aria-hidden="true" />
                {label}
              </button>
            ))}
          </div>

          {error && <p className="form-error" role="alert">{error}</p>}

          <Button variant="cherry" block icon={Heart} loading={busy} onClick={send} className="like-send">
            Send like
          </Button>
          <p className="like-note">You get one like here. Make it count.</p>
        </>
      )}
    </Sheet>
  );
}
