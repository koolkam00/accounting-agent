import { Button, ToastProvider, Wordmark } from './components/ui.jsx';
import { SessionProvider, useSession } from './lib/session.jsx';
import { Redirect, match, usePath } from './lib/router.jsx';
import { Join, SignIn, Welcome } from './screens/Auth.jsx';
import { Onboarding, STEPS, firstIncompleteStep } from './screens/Onboarding.jsx';
import { Discover } from './screens/Discover.jsx';
import { Chat, MemberMatches } from './screens/Chat.jsx';
import { EditProfile, MemberPreview, MemberYou } from './screens/Member.jsx';
import { OwnerLikes, OwnerMatchProfile, OwnerMatches, OwnerPerson, OwnerPreview, OwnerYou } from './screens/Owner.jsx';

function Splash() {
  return (
    <div className="splash" aria-busy="true">
      <Wordmark />
    </div>
  );
}

function Offline({ onRetry }) {
  return (
    <div className="splash">
      <div className="empty">
        <h1 className="empty-title">Can’t reach the site</h1>
        <p className="empty-body">Check your connection and try again.</p>
        <div className="empty-action"><Button onClick={onRetry}>Try again</Button></div>
      </div>
    </div>
  );
}

function Routes() {
  const { status, user, site, refresh } = useSession();
  const path = usePath();
  let m;

  if (status === 'loading') return <Splash />;
  if (status === 'error') return <Offline onRetry={() => refresh().catch(() => {})} />;

  if (!user) {
    if (path === '/') return <Welcome />;
    if (path === '/join') return <Join />;
    if (path === '/signin') return <SignIn />;
    return <Redirect to="/" />;
  }

  if (user.role === 'owner') {
    if (path === '/likes') return <OwnerLikes />;
    if ((m = match('/likes/:id', path))) return <OwnerPerson id={m.id} key={m.id} />;
    if (path === '/matches') return <OwnerMatches />;
    if ((m = match('/chat/:memberId', path))) return <Chat memberId={m.memberId} key={m.memberId} />;
    if ((m = match('/chat/:memberId/profile', path))) return <OwnerMatchProfile memberId={m.memberId} />;
    if (path === '/you') return <OwnerYou />;
    if (path === '/you/preview') return <OwnerPreview />;
    return <Redirect to="/likes" />;
  }

  if (!user.onboarded) {
    const firstOpen = firstIncompleteStep(user, site.minPhotos);
    m = match('/start/:step', path);
    const allowed = m && STEPS.includes(m.step)
      && (STEPS.indexOf(m.step) <= STEPS.indexOf(firstOpen) || firstOpen === 'prompts');
    if (allowed) return <Onboarding step={m.step} key={m.step} />;
    return <Redirect to={`/start/${firstOpen}`} />;
  }

  if (path === '/discover') return <Discover />;
  if (path === '/matches') return <MemberMatches />;
  if (path === '/chat') return <Chat />;
  if (path === '/you') return <MemberYou />;
  if (path === '/you/edit') return <EditProfile />;
  if (path === '/you/preview') return <MemberPreview />;
  return <Redirect to="/discover" />;
}

export default function App() {
  return (
    <SessionProvider>
      <ToastProvider>
        <div className="shell">
          <Routes />
        </div>
      </ToastProvider>
    </SessionProvider>
  );
}
