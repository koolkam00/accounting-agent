import { Heart, MessageCircle, Sparkles } from 'lucide-react';
import { Avatar } from './ui.jsx';
import { Link } from '../lib/router.jsx';
import { useSession } from '../lib/session.jsx';

function TabBar({ tabs }) {
  return (
    <nav className="tabbar" aria-label="Main">
      {tabs.map((t) => {
        const Icon = t.icon;
        return (
          <Link key={t.to} to={t.to} replace className={`tab${t.active ? ' is-active' : ''}`} aria-current={t.active ? 'page' : undefined}>
            <span className="tab-icon">
              {Icon ? <Icon aria-hidden="true" /> : <Avatar src={t.avatar} name={t.name} size={28} className="tab-avatar" />}
              {t.badge ? <span className="badge" aria-label={`${t.badge} new`}>{t.badge > 9 ? '9+' : t.badge}</span> : null}
            </span>
            <span className="tab-label">{t.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

export function MemberTabs({ active }) {
  const { user, site } = useSession();
  const newMatch = user.like?.status === 'matched' && !user.like.matchSeen ? 1 : 0;
  return (
    <TabBar
      tabs={[
        { to: '/discover', label: site.ownerName, icon: Sparkles, active: active === 'discover' },
        { to: '/matches', label: 'Matches', icon: MessageCircle, active: active === 'matches', badge: user.unread || newMatch },
        { to: '/you', label: 'You', avatar: user.photos[0]?.src, name: user.firstName, active: active === 'you' },
      ]}
    />
  );
}

export function OwnerTabs({ active }) {
  const { user, site } = useSession();
  return (
    <TabBar
      tabs={[
        { to: '/likes', label: 'Likes you', icon: Heart, active: active === 'likes', badge: user.counts?.fresh },
        { to: '/matches', label: 'Matches', icon: MessageCircle, active: active === 'matches', badge: user.counts?.unread },
        { to: '/you', label: 'You', avatar: site.heroPhoto, name: site.ownerName, active: active === 'you' },
      ]}
    />
  );
}
