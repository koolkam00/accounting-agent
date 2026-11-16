import { Fragment, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Ellipsis, HeartOff, Hourglass, MessageCircle, SendHorizontal, UserRound } from 'lucide-react';
import { Avatar, BackButton, Button, EmptyState, IconButton, Sheet, Spinner, TopBar, useToast } from '../components/ui.jsx';
import { LikedItem } from '../components/ProfileView.jsx';
import { MemberTabs } from '../components/Tabs.jsx';
import { useSession } from '../lib/session.jsx';
import { api, invalidate, useResource } from '../lib/api.js';
import { Link, navigate } from '../lib/router.jsx';
import { clockTime, dayLabel, timeAgo } from '../lib/format.js';
import { dateIdea, likedWhat } from '../lib/content.js';

export function Chat({ memberId }) {
  const { user, site, refresh } = useSession();
  const toast = useToast();
  const isOwner = user.role === 'owner';
  const path = isOwner ? `/owner/threads/${memberId}` : '/thread';
  const { data, error, reload } = useResource(path, { interval: 3000 });
  const [pending, setPending] = useState([]);
  const [text, setText] = useState('');
  const [menu, setMenu] = useState(false);
  const [confirmUnmatch, setConfirmUnmatch] = useState(false);
  const input = useRef(null);
  const first = useRef(true);

  const other = isOwner
    ? { name: data?.member?.name ?? '', photo: data?.member?.photos?.[0]?.src }
    : { name: site.ownerName, photo: site.heroPhoto };
  const messages = [...(data?.messages ?? []), ...pending];
  const like = data?.like;
  const closed = error?.status === 403 || error?.status === 404;

  useLayoutEffect(() => {
    if (!data) return;
    window.scrollTo({ top: document.documentElement.scrollHeight, behavior: first.current ? 'auto' : 'smooth' });
    first.current = false;
  }, [messages.length, !!data]); // eslint-disable-line react-hooks/exhaustive-deps

  // Reading the thread clears unread badges; refresh them.
  const unreadKey = data?.messages?.length;
  useEffect(() => { if (unreadKey !== undefined) refresh().catch(() => {}); }, [unreadKey, refresh]);

  // Auto-grow the composer.
  useLayoutEffect(() => {
    const el = input.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 132)}px`;
  }, [text]);

  const send = async (e) => {
    e?.preventDefault();
    const body = text.trim();
    if (!body) return;
    const temp = { id: `tmp-${Date.now()}`, mine: true, body, createdAt: Date.now(), pending: true };
    setText('');
    setPending((p) => [...p, temp]);
    try {
      await api(path, { method: 'POST', body: { body } });
      await reload();
    } catch (err) {
      setText(body);
      toast(err.message, { tone: 'error' });
    } finally {
      setPending((p) => p.filter((m) => m.id !== temp.id));
    }
    input.current?.focus();
  };

  const unmatch = async () => {
    try {
      if (isOwner) await api(`/owner/threads/${memberId}/unmatch`, { method: 'POST' });
      else await api('/unmatch', { method: 'POST' });
      invalidate('/owner/matches');
      await refresh();
      toast('Unmatched');
      navigate(isOwner ? '/matches' : '/discover', { replace: true });
    } catch (err) {
      toast(err.message, { tone: 'error' });
    }
  };

  const idea = like && dateIdea(like.dateIdea);
  const what = like && likedWhat(like.targetType);
  const P = site.pronoun;

  return (
    <div className="screen chat">
      <TopBar
        left={<BackButton fallback="/matches" />}
        title={other.name ? (
          <span className="chat-who">
            <Avatar src={other.photo} name={other.name} size={32} />
            <span>{other.name}</span>
          </span>
        ) : null}
        right={!closed && data ? <IconButton icon={Ellipsis} label="More" onClick={() => setMenu(true)} /> : null}
      />

      <main className="chat-body">
        {closed ? (
          <EmptyState title="This conversation has ended">You can’t send messages here anymore.</EmptyState>
        ) : !data ? (
          <div className="center-fill"><Spinner /></div>
        ) : (
          <>
            <section className="chat-intro">
              <Avatar src={other.photo} name={other.name} size={84} />
              <h2 className="chat-intro-title">You matched with {other.name}</h2>
              {like?.decidedAt && <p className="chat-intro-date">{dayLabel(like.decidedAt)}</p>}
              {like && (
                <div className="chat-like">
                  <p className="chat-like-label">
                    {isOwner ? `${other.name} liked your ${what}` : `You liked ${P.possessive} ${what}`}
                  </p>
                  <LikedItem like={like} ownerPhoto={site.heroPhoto} size="md" />
                  {like.comment && <p className={`bubble bubble-like ${isOwner ? 'is-theirs' : 'is-mine'}`}>{like.comment}</p>}
                  {idea && (
                    <p className="chat-like-idea">
                      <idea.icon aria-hidden="true" /> {isOwner ? 'Suggested' : 'You suggested'} {idea.label.toLowerCase()} for a first date
                    </p>
                  )}
                </div>
              )}
            </section>

            {messages.length === 0 && (
              <p className="chat-nudge">
                {isOwner ? `${other.name} is waiting. Say something good.` : `Say hi to ${other.name}. No pressure.`}
              </p>
            )}

            <ol className="messages">
              {messages.map((m, i) => {
                const prev = messages[i - 1];
                const next = messages[i + 1];
                const newDay = !prev || dayLabel(prev.createdAt) !== dayLabel(m.createdAt);
                const groupEnd = !next || next.mine !== m.mine || next.createdAt - m.createdAt > 5 * 60_000;
                const groupStart = !prev || prev.mine !== m.mine || m.createdAt - prev.createdAt > 5 * 60_000 || newDay;
                const lastMine = m.mine && !messages.slice(i + 1).some((x) => x.mine);
                return (
                  <Fragment key={m.id}>
                    {newDay && <li className="day-sep"><span>{dayLabel(m.createdAt)}</span></li>}
                    <li className={`msg ${m.mine ? 'is-mine' : 'is-theirs'}${groupStart ? ' is-start' : ''}${groupEnd ? ' is-end' : ''}${m.pending ? ' is-pending' : ''}`}>
                      <p className="bubble">{m.body}</p>
                      {groupEnd && (
                        <span className="msg-meta">
                          {clockTime(m.createdAt)}
                          {lastMine && !m.pending && (m.readAt ? ' · Read' : ' · Sent')}
                        </span>
                      )}
                    </li>
                  </Fragment>
                );
              })}
            </ol>
          </>
        )}
      </main>

      {!closed && data && (
        <form className="composer" onSubmit={send}>
          <textarea
            ref={input}
            className="composer-input"
            rows={1}
            placeholder={`Message ${other.name}`}
            aria-label="Message"
            value={text}
            maxLength={2000}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); send(); }
            }}
          />
          <button type="submit" className="composer-send" disabled={!text.trim()} aria-label="Send">
            <SendHorizontal aria-hidden="true" />
          </button>
        </form>
      )}

      <Sheet open={menu} onClose={() => setMenu(false)} label="Conversation options">
        <div className="action-list">
          {isOwner && (
            <button type="button" className="action-row" onClick={() => { setMenu(false); navigate(`/chat/${memberId}/profile`); }}>
              <UserRound aria-hidden="true" /> View {other.name}’s profile
            </button>
          )}
          <button type="button" className="action-row is-danger" onClick={() => { setMenu(false); setConfirmUnmatch(true); }}>
            <HeartOff aria-hidden="true" /> Unmatch
          </button>
          <button type="button" className="action-row is-muted" onClick={() => setMenu(false)}>Cancel</button>
        </div>
      </Sheet>

      <Sheet open={confirmUnmatch} onClose={() => setConfirmUnmatch(false)} variant="dialog" label="Unmatch?">
        <h2 className="dialog-title">Unmatch {other.name}?</h2>
        <p className="dialog-body">The conversation closes for both of you and can’t be undone.</p>
        <div className="dialog-actions">
          <Button variant="soft" block onClick={() => setConfirmUnmatch(false)}>Keep chatting</Button>
          <Button variant="danger" block onClick={unmatch}>Unmatch</Button>
        </div>
      </Sheet>
    </div>
  );
}

export function ConvoRow({ to, photo, name, preview, time, unread, tag }) {
  return (
    <li>
      <Link to={to} className={`convo${unread ? ' is-unread' : ''}`}>
        <Avatar src={photo} name={name} size={58} />
        <span className="convo-main">
          <span className="convo-top">
            <b>{name}</b>
            {tag && <span className="convo-tag">{tag}</span>}
            {time && <time>{time}</time>}
          </span>
          <span className="convo-preview">{preview}</span>
        </span>
        {unread ? <span className="convo-dot" aria-label={`${unread} unread`} /> : null}
      </Link>
    </li>
  );
}

export function MemberMatches() {
  const { user, site } = useSession();
  const like = user.like;
  const matched = like?.status === 'matched';
  const { data } = useResource(matched ? '/thread' : null, { interval: 8000 });
  const P = site.pronoun;
  const last = data?.messages?.[data.messages.length - 1];

  return (
    <div className="screen">
      <TopBar left={<h1 className="topbar-h1">Matches</h1>} />
      <main className="screen-body">
        {matched ? (
          <>
            <p className="list-kicker">1 match. The only one you need.</p>
            <ul className="convo-list">
              <ConvoRow
                to="/chat"
                photo={site.heroPhoto}
                name={site.ownerName}
                preview={last ? `${last.mine ? 'You: ' : ''}${last.body}` : 'New match. Say hi!'}
                time={last ? timeAgo(last.createdAt) : null}
                unread={user.unread}
                tag={!last ? 'New' : (!last.mine ? 'Your turn' : null)}
              />
            </ul>
          </>
        ) : like?.status === 'unmatched' ? (
          <EmptyState art={<MessageCircle aria-hidden="true" />} title="This match has ended">Thanks for stopping by.</EmptyState>
        ) : like ? (
          <EmptyState art={<Hourglass aria-hidden="true" />} title="Fingers crossed">
            Your like is with {site.ownerName}. The second {P.subject} likes you back, {P.subject === 'they' ? 'they’ll' : `${P.subject}’ll`} show up here.
          </EmptyState>
        ) : (
          <EmptyState
            art={<MessageCircle aria-hidden="true" />}
            title="No matches yet"
            action={<Button onClick={() => navigate('/discover')}>See {site.ownerName}’s profile</Button>}
          >
            You haven’t sent a like yet. Good news: there’s only one person to choose from.
          </EmptyState>
        )}
      </main>
      <MemberTabs active="matches" />
    </div>
  );
}
