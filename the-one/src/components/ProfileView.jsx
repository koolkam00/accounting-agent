import { useMemo } from 'react';
import { Heart } from 'lucide-react';
import { factMeta } from '../lib/content.js';

/**
 * Lay a profile out as one scroll: main photo, an answer, the basics,
 * then photos and answers alternating so nothing gets buried.
 */
function layout({ photos = [], prompts = [], facts = [] }) {
  const P = [...photos];
  const Q = [...prompts];
  const blocks = [];
  blocks.push(P.length ? { kind: 'hero', photo: P.shift() } : { kind: 'name' });
  if (Q.length) blocks.push({ kind: 'prompt', prompt: Q.shift(), tint: 0 });
  if (facts.length) blocks.push({ kind: 'facts' });
  let tint = 1;
  let turn = 0;
  while (P.length || Q.length) {
    if (P.length) blocks.push({ kind: 'photo', photo: P.shift() });
    if (Q.length && (turn % 2 === 0 || !P.length)) blocks.push({ kind: 'prompt', prompt: Q.shift(), tint: tint++ });
    turn += 1;
  }
  return blocks;
}

export function LikeButton({ onClick, label, liked = false }) {
  if (liked) {
    return (
      <span className="like-btn is-liked" role="img" aria-label="You liked this">
        <Heart aria-hidden="true" fill="currentColor" strokeWidth={0} />
      </span>
    );
  }
  return (
    <button type="button" className="like-btn" aria-label={label} onClick={onClick}>
      <Heart aria-hidden="true" fill="currentColor" strokeWidth={0} />
    </button>
  );
}

function subline(facts) {
  const pick = (k) => facts.find((f) => f.key === k)?.value;
  return [pick('location'), pick('job')].filter(Boolean).join(' · ');
}

export function ProfileView({ profile, onLike, likedKey = null, canLike = false, children }) {
  const blocks = useMemo(() => layout(profile), [profile]);
  const name = profile.name;
  const sub = subline(profile.facts ?? []);
  const like = (type, ref, item) => onLike?.({ type, ref, item });
  const likeProps = (type, ref, item, what) => ({
    liked: likedKey === `${type}:${ref}`,
    show: canLike || likedKey === `${type}:${ref}`,
    onClick: () => like(type, ref, item),
    label: `Like ${name}’s ${what}`,
  });

  return (
    <div className="profile">
      {blocks.map((b) => {
        if (b.kind === 'hero') {
          const lp = likeProps('photo', b.photo.id, b.photo, 'photo');
          return (
            <figure className="card photo-card hero-card" key={b.photo.id}>
              <img src={b.photo.src} alt={`${name}’s main photo`} draggable="false" />
              <figcaption className="hero-meta">
                <h1 className="hero-name">
                  {name}
                  {profile.age != null && <span className="hero-age">{profile.age}</span>}
                </h1>
                {sub && <p className="hero-sub">{sub}</p>}
              </figcaption>
              {lp.show && <LikeButton {...lp} />}
            </figure>
          );
        }
        if (b.kind === 'name') {
          return (
            <div className="card name-card" key="name">
              <h1 className="hero-name">
                {name}
                {profile.age != null && <span className="hero-age">{profile.age}</span>}
              </h1>
              {sub && <p className="hero-sub">{sub}</p>}
            </div>
          );
        }
        if (b.kind === 'photo') {
          const lp = likeProps('photo', b.photo.id, b.photo, 'photo');
          return (
            <figure className="card photo-card" key={b.photo.id}>
              <img src={b.photo.src} alt={b.photo.caption || `${name}’s photo`} loading="lazy" draggable="false" />
              {b.photo.caption && <figcaption className="photo-caption">{b.photo.caption}</figcaption>}
              {lp.show && <LikeButton {...lp} />}
            </figure>
          );
        }
        if (b.kind === 'prompt') {
          const lp = likeProps('prompt', b.prompt.id, b.prompt, 'answer');
          return (
            <article className={`card prompt-card tone-${b.tint % 2 === 0 ? 'ink' : 'light'}`} key={b.prompt.id}>
              <p className="prompt-q">{b.prompt.question}</p>
              <p className="prompt-a">{b.prompt.answer}</p>
              {lp.show && <LikeButton {...lp} />}
            </article>
          );
        }
        return <FactsCard facts={profile.facts} key="facts" />;
      })}
      {children}
    </div>
  );
}

export function FactsCard({ facts }) {
  return (
    <section className="card facts-card" aria-label="The basics">
      <h2 className="card-kicker">The basics</h2>
      <ul className="facts">
        {facts.map((f) => {
          const meta = factMeta(f.key);
          const Icon = meta.icon;
          return (
            <li className="fact" key={f.key} title={meta.label}>
              <Icon aria-hidden="true" />
              <span><span className="sr-only">{meta.label}: </span>{f.value}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

/** Small preview of whatever was liked: a photo, an answer, or the whole profile. */
export function LikedItem({ like, ownerPhoto, size = 'md' }) {
  const s = like.snapshot ?? {};
  if (like.targetType === 'photo' && s.src) {
    return (
      <div className={`liked-item liked-photo liked-${size}`}>
        <img src={s.src} alt="" draggable="false" />
      </div>
    );
  }
  if (like.targetType === 'prompt') {
    return (
      <div className={`liked-item liked-prompt liked-${size}`}>
        <p className="prompt-q">{s.question}</p>
        <p className="prompt-a">{s.answer}</p>
      </div>
    );
  }
  return (
    <div className={`liked-item liked-photo liked-${size}`}>
      {ownerPhoto ? <img src={ownerPhoto} alt="" draggable="false" /> : null}
    </div>
  );
}
