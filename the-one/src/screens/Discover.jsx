import { useState } from 'react';
import { Heart, Info, MessageCircle, X } from 'lucide-react';
import { Avatar, Button, FloatingHearts, IconButton, Moment, Sheet, TopBar, Wordmark } from '../components/ui.jsx';
import { LikedItem, ProfileView } from '../components/ProfileView.jsx';
import { LikeSheet } from '../components/LikeSheet.jsx';
import { MemberTabs } from '../components/Tabs.jsx';
import { useSession } from '../lib/session.jsx';
import { useResource, api } from '../lib/api.js';
import { navigate } from '../lib/router.jsx';
import { likedWhat } from '../lib/content.js';

export function ProfileSkeleton() {
  return (
    <div className="profile" aria-busy="true" aria-label="Loading profile">
      <div className="card skeleton skeleton-photo" />
      <div className="card skeleton skeleton-prompt" />
      <div className="card skeleton skeleton-facts" />
    </div>
  );
}

export function LoadError({ onRetry }) {
  return (
    <div className="empty">
      <h2 className="empty-title">Couldn’t load that</h2>
      <p className="empty-body">Check your connection and try again.</p>
      <div className="empty-action"><Button variant="soft" onClick={onRetry}>Try again</Button></div>
    </div>
  );
}

export function Discover() {
  const { user, site, setUser } = useSession();
  const { data, error, reload } = useResource('/profile');
  const [target, setTarget] = useState(null);
  const [sent, setSent] = useState(false);
  const [skip, setSkip] = useState(false);
  const [info, setInfo] = useState(false);
  const [closingMatch, setClosingMatch] = useState(false);

  const P = site.pronoun;
  const name = site.ownerName;
  const like = user.like;
  const profile = data?.profile;
  const likedKey = like && like.targetType !== 'profile' ? `${like.targetType}:${like.targetRef}` : null;
  const matchOpen = like?.status === 'matched' && !like.matchSeen && !closingMatch;

  const onSent = (u) => {
    setTarget(null);
    setUser(u);
    setTimeout(() => setSent(true), 120);
  };

  const dismissMatch = async (toChat) => {
    setClosingMatch(true);
    try { setUser((await api('/match/seen', { method: 'POST' })).user); } catch { /* try again next time */ }
    if (toChat) navigate('/chat');
  };

  return (
    <div className="screen">
      <TopBar
        left={<Wordmark name={site.appName} />}
        right={<IconButton icon={Info} label="How this works" onClick={() => setInfo(true)} />}
      />
      <main className="screen-body">
        {like && <LikeStatus like={like} site={site} />}
        {!profile ? (error ? <LoadError onRetry={reload} /> : <ProfileSkeleton />) : (
          <ProfileView profile={profile} canLike={!like} likedKey={likedKey} onLike={setTarget}>
            <section className="profile-end">
              <p className="profile-end-kicker">1 of 1</p>
              <h2 className="profile-end-title">That’s {name}. <em>Your move.</em></h2>
              {!like ? (
                <div className="profile-end-actions">
                  <Button variant="cherry" icon={Heart} onClick={() => setTarget({ type: 'profile', ref: '', item: null })}>Send a like</Button>
                  <Button variant="soft" icon={X} onClick={() => setSkip(true)}>Not for me</Button>
                </div>
              ) : (
                <p className="profile-end-note">
                  {like.status === 'matched' ? 'You two matched. Go say something.' : 'Your like is in. Now we wait.'}
                </p>
              )}
            </section>
          </ProfileView>
        )}
      </main>
      <MemberTabs active="discover" />

      <LikeSheet target={target} ownerName={name} ownerPhoto={site.heroPhoto} onClose={() => setTarget(null)} onSent={onSent} />

      <Moment open={sent} onClose={() => setSent(false)} label="Like sent" className="moment-like">
        <FloatingHearts />
        <div className="moment-inner">
          <div className="moment-badge"><Heart aria-hidden="true" fill="currentColor" strokeWidth={0} /></div>
          <h2 className="moment-title">Like sent.</h2>
          <p className="moment-body">
            {name} will see it in {P.possessive} likes. If {P.subject} likes you back, it’s a match and you can chat right here.
          </p>
          <Button variant="light" block onClick={() => setSent(false)}>Back to {name}</Button>
        </div>
      </Moment>

      <Moment open={matchOpen} onClose={() => dismissMatch(false)} label="It’s a match" className="moment-match">
        <FloatingHearts count={18} />
        <div className="moment-inner">
          <div className="match-pair" aria-hidden="true">
            <Avatar src={user.photos[0]?.src} name={user.firstName} size={128} className="match-a" />
            <Avatar src={site.heroPhoto} name={name} size={128} className="match-b" />
            <span className="match-heart"><Heart fill="currentColor" strokeWidth={0} /></span>
          </div>
          <h2 className="moment-title">It’s mutual.</h2>
          <p className="moment-body">You and {name} like each other. Don’t overthink it. Say hi.</p>
          <Button variant="light" block icon={MessageCircle} onClick={() => dismissMatch(true)}>Send a message</Button>
          <Button variant="ghost-light" block onClick={() => dismissMatch(false)}>Maybe later</Button>
        </div>
      </Moment>

      <Sheet open={skip} onClose={() => setSkip(false)} variant="dialog" label="There’s no one else">
        <div className="skip">
          <div className="skip-art" aria-hidden="true"><span>1</span></div>
          <h2 className="dialog-title">There’s no one else.</h2>
          <p className="dialog-body">
            Seriously. This site has exactly one profile. Swipe all you want, it’s {name} all the way down.
          </p>
          <Button block onClick={() => { setSkip(false); window.scrollTo({ top: 0, behavior: 'smooth' }); }}>Fine, I’ll look again</Button>
        </div>
      </Sheet>

      <Sheet open={info} onClose={() => setInfo(false)} label="How this works">
        <h2 className="sheet-title">How this works</h2>
        <ol className="how">
          <li><b>There’s one profile here.</b> {name}’s. No swiping, no algorithm, no endless scrolling.</li>
          <li><b>Like something specific.</b> Tap <Heart className="inline-heart" aria-label="the heart" fill="currentColor" strokeWidth={0} /> on a photo or an answer and add a comment. You get one like, so pick well.</li>
          <li><b>If it’s mutual, you match.</b> Then you can chat with {name} right here.</li>
          <li><b>Your profile stays private.</b> Only {name} can see it, and you can delete it anytime.</li>
        </ol>
        <Button block onClick={() => setInfo(false)}>Got it</Button>
      </Sheet>
    </div>
  );
}

function LikeStatus({ like, site }) {
  const P = site.pronoun;
  if (like.status === 'matched') {
    return (
      <button type="button" className="status-card is-match" onClick={() => navigate('/chat')}>
        <Avatar src={site.heroPhoto} name={site.ownerName} size={48} />
        <span className="status-text">
          <b>It’s mutual</b>
          <span>You and {site.ownerName} matched. Say hi.</span>
        </span>
        <span className="status-cta"><MessageCircle aria-hidden="true" /></span>
      </button>
    );
  }
  if (like.status === 'unmatched') {
    return (
      <div className="status-card">
        <span className="status-text">
          <b>This match has ended</b>
          <span>The conversation is closed, but thanks for stopping by.</span>
        </span>
      </div>
    );
  }
  return (
    <div className="status-card">
      <LikedItem like={like} ownerPhoto={site.heroPhoto} size="xs" />
      <span className="status-text">
        <b>Like sent <Heart className="inline-heart" aria-hidden="true" fill="currentColor" strokeWidth={0} /></b>
        <span>You liked {P.possessive} {likedWhat(like.targetType)}. We’ll tell you if it’s mutual.</span>
      </span>
    </div>
  );
}
