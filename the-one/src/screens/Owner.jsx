import { useState } from 'react';
import { Copy, Eye, Heart, ImagePlus, LogOut, MessageCircle, Pencil, Share, X } from 'lucide-react';
import { Avatar, BackButton, Button, EmptyState, FloatingHearts, Moment, TopBar, useToast } from '../components/ui.jsx';
import { LikedItem, ProfileView } from '../components/ProfileView.jsx';
import { OwnerTabs } from '../components/Tabs.jsx';
import { ConvoRow } from './Chat.jsx';
import { LoadError, ProfileSkeleton } from './Discover.jsx';
import { useSession } from '../lib/session.jsx';
import { api, invalidate, useResource } from '../lib/api.js';
import { Link, navigate } from '../lib/router.jsx';
import { timeAgo } from '../lib/format.js';
import { dateIdea, likedWhat } from '../lib/content.js';

const siteLink = () => window.location.origin;

function useShare() {
  const toast = useToast();
  const { site } = useSession();
  const copy = async () => {
    try { await navigator.clipboard.writeText(siteLink()); toast('Link copied'); } catch { toast(siteLink()); }
  };
  const share = async () => {
    try { await navigator.share({ title: site.appName, text: `There’s only one profile on here. It’s mine.`, url: siteLink() }); } catch { /* cancelled */ }
  };
  return { copy, share, canShare: typeof navigator.share === 'function' };
}

export function OwnerLikes() {
  const { data, error, reload } = useResource('/owner/likes', { interval: 10_000 });
  const { copy } = useShare();
  const likes = data?.likes;
  return (
    <div className="screen">
      <TopBar left={<h1 className="topbar-h1">Likes you</h1>} right={likes?.length ? <span className="count-pill">{likes.length}</span> : null} />
      <main className="screen-body pad">
        {!likes ? (error ? <LoadError onRetry={reload} /> : (
          <ul className="likes-grid" aria-busy="true">{[0, 1, 2, 3].map((i) => <li key={i} className="skeleton like-tile-skeleton" />)}</ul>
        )) : likes.length === 0 ? (
          <EmptyState
            art={<Heart aria-hidden="true" />}
            title="No likes yet"
            action={<Button icon={Copy} onClick={copy}>Copy your link</Button>}
          >
            Share your link. Everyone who signs up only sees you, and their likes land here.
          </EmptyState>
        ) : (
          <>
            <p className="list-kicker">{likes.length === 1 ? 'Someone likes you.' : `${likes.length} people like you.`} Tap to see who.</p>
            <ul className="likes-grid">
              {likes.map(({ like, member, fresh }) => (
                <li key={like.id}>
                  <Link to={`/likes/${like.id}`} className="like-tile">
                    <span className="like-tile-photo">
                      {member.photo ? <img src={member.photo} alt="" draggable="false" /> : <span className="like-tile-initial">{member.name?.[0]}</span>}
                      {fresh && <span className="new-pill">New</span>}
                      <span className="like-tile-meta">
                        <b>{member.name}</b>
                        {member.age != null && <span>{member.age}</span>}
                      </span>
                    </span>
                    <span className="like-tile-what">
                      {like.comment
                        ? <span className="like-tile-comment">“{like.comment}”</span>
                        : <span className="like-tile-plain"><Heart aria-hidden="true" fill="currentColor" strokeWidth={0} /> Liked your {likedWhat(like.targetType)}</span>}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}
      </main>
      <OwnerTabs active="likes" />
    </div>
  );
}

function LikeContext({ like, name }) {
  const { site } = useSession();
  const idea = dateIdea(like.dateIdea);
  return (
    <section className="context-card">
      <p className="context-label">
        <Heart aria-hidden="true" fill="currentColor" strokeWidth={0} />
        {name} liked your {likedWhat(like.targetType)}
        <time>{timeAgo(like.createdAt)}</time>
      </p>
      <div className="context-row">
        <LikedItem like={like} ownerPhoto={site.heroPhoto} size="sm" />
        {like.comment
          ? <p className="bubble is-theirs context-bubble">{like.comment}</p>
          : <p className="context-none">No comment. Just a like.</p>}
      </div>
      {idea && (
        <p className="context-idea"><idea.icon aria-hidden="true" /> Suggested a first date: <b>{idea.label}</b></p>
      )}
    </section>
  );
}

export function OwnerPerson({ id }) {
  const { site, refresh } = useSession();
  const toast = useToast();
  const { data, error, reload } = useResource(`/owner/likes/${id}`);
  const [busy, setBusy] = useState('');
  const [matched, setMatched] = useState(null);
  const like = data?.like;
  const member = data?.member;

  const decide = async (action) => {
    setBusy(action);
    try {
      const res = await api(`/owner/likes/${id}/${action}`, { method: 'POST' });
      invalidate('/owner/likes');
      invalidate('/owner/matches');
      refresh().catch(() => {});
      if (action === 'match') setMatched(res.memberId);
      else { toast(`Removed ${member.name}`); navigate('/likes', { replace: true }); }
    } catch (err) {
      toast(err.message, { tone: 'error' });
      setBusy('');
    }
  };

  return (
    <div className="screen">
      <TopBar left={<BackButton fallback="/likes" />} title={member?.name ?? ''} />
      <main className="screen-body">
        {!data ? (error ? <LoadError onRetry={reload} /> : <ProfileSkeleton />) : (
          <>
            <div className="pad-x"><LikeContext like={like} name={member.name} /></div>
            <ProfileView profile={member} />
            {like.status === 'pending' && <div className="decide-spacer" />}
          </>
        )}
      </main>
      {like?.status === 'pending' && (
        <div className="decide-bar">
          <button type="button" className="decide-x" onClick={() => decide('remove')} disabled={!!busy} aria-label={`Remove ${member.name}`}>
            <X aria-hidden="true" />
          </button>
          <Button variant="cherry" block icon={Heart} loading={busy === 'match'} disabled={!!busy} onClick={() => decide('match')}>
            Match with {member.name}
          </Button>
        </div>
      )}
      {like && like.status !== 'pending' && !matched && (
        <div className="decide-bar is-note">
          {like.status === 'matched'
            ? <Button block icon={MessageCircle} onClick={() => navigate(`/chat/${member.id}`)}>Go to chat</Button>
            : <p>You passed on {member.name}.</p>}
        </div>
      )}

      <Moment open={!!matched} onClose={() => navigate(`/chat/${matched}`, { replace: true })} label="It’s a match" className="moment-match">
        <FloatingHearts count={18} />
        <div className="moment-inner">
          <div className="match-pair" aria-hidden="true">
            <Avatar src={site.heroPhoto} name={site.ownerName} size={128} className="match-a" />
            <Avatar src={member?.photos?.[0]?.src} name={member?.name} size={128} className="match-b" />
            <span className="match-heart"><Heart fill="currentColor" strokeWidth={0} /></span>
          </div>
          <h2 className="moment-title">It’s mutual.</h2>
          <p className="moment-body">You matched with {member?.name}. {member?.name} gets told right away.</p>
          <Button variant="light" block icon={MessageCircle} onClick={() => navigate(`/chat/${matched}`, { replace: true })}>Send a message</Button>
          <Button variant="ghost-light" block onClick={() => navigate('/likes', { replace: true })}>Back to likes</Button>
        </div>
      </Moment>
    </div>
  );
}

export function OwnerMatches() {
  const { data, error, reload } = useResource('/owner/matches', { interval: 8000 });
  const matches = data?.matches;
  const fresh = matches?.filter((m) => !m.lastMessage) ?? [];
  const convos = matches?.filter((m) => m.lastMessage) ?? [];
  return (
    <div className="screen">
      <TopBar left={<h1 className="topbar-h1">Matches</h1>} />
      <main className="screen-body">
        {!matches ? (error ? <LoadError onRetry={reload} /> : null) : matches.length === 0 ? (
          <EmptyState
            art={<MessageCircle aria-hidden="true" />}
            title="No matches yet"
            action={<Button onClick={() => navigate('/likes', { replace: true })}>See your likes</Button>}
          >
            Match with someone from your likes and the conversation starts here.
          </EmptyState>
        ) : (
          <>
            {fresh.length > 0 && (
              <section className="new-matches">
                <h2 className="list-kicker">New matches</h2>
                <ul className="new-match-row">
                  {fresh.map((m) => (
                    <li key={m.member.id}>
                      <Link to={`/chat/${m.member.id}`} className="new-match">
                        <Avatar src={m.member.photo} name={m.member.name} size={72} />
                        <span>{m.member.name}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </section>
            )}
            {convos.length > 0 && (
              <section>
                <h2 className="list-kicker">Conversations</h2>
                <ul className="convo-list">
                  {convos.map((m) => (
                    <ConvoRow
                      key={m.member.id}
                      to={`/chat/${m.member.id}`}
                      photo={m.member.photo}
                      name={m.member.name}
                      preview={`${m.lastMessage.mine ? 'You: ' : ''}${m.lastMessage.body}`}
                      time={timeAgo(m.lastMessage.createdAt)}
                      unread={m.unread}
                      tag={!m.lastMessage.mine ? 'Your turn' : null}
                    />
                  ))}
                </ul>
              </section>
            )}
          </>
        )}
      </main>
      <OwnerTabs active="matches" />
    </div>
  );
}

export function OwnerMatchProfile({ memberId }) {
  const { data, error, reload } = useResource(`/owner/threads/${memberId}`);
  return (
    <div className="screen">
      <TopBar left={<BackButton fallback={`/chat/${memberId}`} />} title={data?.member?.name ?? ''} />
      <main className="screen-body">
        {!data ? (error ? <LoadError onRetry={reload} /> : <ProfileSkeleton />) : (
          <>
            <div className="pad-x"><LikeContext like={data.like} name={data.member.name} /></div>
            <ProfileView profile={data.member} />
          </>
        )}
      </main>
    </div>
  );
}

export function OwnerYou() {
  const { site, signOut } = useSession();
  const { data } = useResource('/owner/stats', { interval: 30_000 });
  const { copy, share, canShare } = useShare();
  const stats = data?.stats;
  const items = [['members', 'Sign-ups'], ['likes', 'Likes'], ['matches', 'Matches'], ['messages', 'Messages']];
  return (
    <div className="screen">
      <TopBar left={<h1 className="topbar-h1">You</h1>} />
      <main className="screen-body pad stack">
        <section className="me-card">
          <Avatar src={site.heroPhoto} name={site.ownerName} size={104} className="me-avatar" />
          <h2 className="me-name">{site.ownerName}{site.ownerAge != null && <span>{site.ownerAge}</span>}</h2>
          <p className="me-sub">The one and only profile</p>
          <div className="me-actions">
            <Button variant="soft" icon={Eye} onClick={() => navigate('/you/preview')}>Preview your profile</Button>
          </div>
        </section>

        {site.heroPhoto?.includes('/placeholder-') && (
          <section className="note-card is-warn">
            <ImagePlus aria-hidden="true" />
            <p><b>You’re still using placeholder photos.</b> Drop yours into <code>public/me/</code> and list them in <code>profile.config.js</code>.</p>
          </section>
        )}

        <section className="stats" aria-label="Stats">
          {items.map(([k, label]) => (
            <div className="stat" key={k}>
              <b>{stats ? stats[k] : '–'}</b>
              <span>{label}</span>
            </div>
          ))}
        </section>

        <section className="share-card">
          <h2 className="share-title">Share your link</h2>
          <p className="share-body">Put it in your bio. Everyone who signs up only ever sees you.</p>
          <p className="share-link">{siteLink().replace(/^https?:\/\//, '')}</p>
          <div className="share-actions">
            <Button variant="light" icon={Copy} onClick={copy}>Copy link</Button>
            {canShare && <Button variant="ghost-light" icon={Share} onClick={share}>Share</Button>}
          </div>
        </section>

        <section className="note-card">
          <Pencil aria-hidden="true" />
          <p><b>Editing your profile:</b> swap photos, prompts and basics in <code>profile.config.js</code>, then restart the server.</p>
        </section>

        <section className="list-card" aria-label="Account">
          <button type="button" className="list-row" onClick={signOut}><LogOut aria-hidden="true" /> Log out</button>
        </section>
      </main>
      <OwnerTabs active="you" />
    </div>
  );
}

export function OwnerPreview() {
  const { data, error, reload } = useResource('/profile');
  return (
    <div className="screen">
      <TopBar left={<BackButton fallback="/you" />} title="Preview" />
      <main className="screen-body">
        <p className="preview-banner"><Eye aria-hidden="true" /> This is exactly what everyone sees.</p>
        {!data ? (error ? <LoadError onRetry={reload} /> : <ProfileSkeleton />) : <ProfileView profile={data.profile} />}
      </main>
    </div>
  );
}
