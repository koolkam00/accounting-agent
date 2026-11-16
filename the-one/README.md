# the one

A personal dating site with exactly one profile on it: yours.

Anyone can make an account, but the only profile they'll ever see is yours. They scroll your photos and prompts, like the specific thing that caught their eye (with a comment and an optional first-date idea), and it lands in your private **Likes you** inbox. Like them back and you match, and you can chat right on the site.

- **Visitors**: sign up → build a quick profile (name, birthday, photos, prompts, basics) → see your profile → send one like → chat if it's mutual.
- **You**: a Likes inbox, their full profiles, Match / Remove, a Matches list with chat, sign-up stats, and a share link.
- Visitor profiles and photos are private to you. Nobody can see anyone else, and visitors can delete their account at any time.
- Works great on phones (it's built like an app and can be added to the home screen) and shows as a phone-sized column on desktop.

## Run it locally

Needs **Node 22.13 or newer**.

```bash
cd the-one
npm install
npm run dev
```

Open http://localhost:3000. In dev mode, if you haven't set an owner login, you can sign in as `me@example.com` / `change-me-please` (the terminal prints this). To use your own, copy `.env.example` to `.env` and fill in `OWNER_EMAIL` and `OWNER_PASSWORD`.

To sign in as yourself, go to `/signin` (or tap "I already have an account" on the welcome screen).

## Make it yours

1. **Photos**: put your photos in `public/me/` (JPG, PNG or WebP; portrait 4:5 looks best).
2. **Profile**: edit `profile.config.js`. It holds your name, birthday (for your age), photos, up to 3 prompts, the basics (height, job, and so on), and the site name. Everything marked `EDIT ME` is placeholder.
3. Restart the server. In dev mode, edits to `profile.config.js` reload automatically.

The placeholder landscape images in `public/me/` are just stand-ins. Your owner "You" tab reminds you while you're still using them.

## Put it online

The app is a single Node server that keeps its database (SQLite, built into Node) and uploaded photos in `DATA_DIR`. **Deploy it anywhere that runs Node 22+ and gives you a persistent disk**, such as Railway, Render, Fly.io or any VPS. Serverless hosts such as Vercel and Netlify won't keep the database between requests, so they aren't a fit as-is.

Whichever host you pick:

- **App folder**: `the-one`
- **Build command**: `npm install && npm run build`
- **Start command**: `npm start`
- **Environment variables**: `OWNER_EMAIL`, `OWNER_PASSWORD`, `SITE_URL` (your public URL), and `DATA_DIR` pointed at the mounted persistent volume (for example `/data`)
- Serve it over **https** (all of the hosts above do this for you)

With Docker:

```bash
docker build -t the-one .
docker run -p 3000:3000 -v the-one-data:/app/data \
  -e OWNER_EMAIL=you@example.com -e OWNER_PASSWORD='a-long-password' \
  -e SITE_URL=https://your-domain.com the-one
```

### Get notified

Set `NOTIFY_WEBHOOK_URL` to get a ping whenever someone likes you or sends a message. It works with a Discord webhook, a Slack incoming webhook, or an [ntfy](https://ntfy.sh) topic URL (install the ntfy app and subscribe to a long, random topic name for free push notifications).

## Settings

| Variable | What it does |
| --- | --- |
| `OWNER_EMAIL`, `OWNER_PASSWORD` | Your login. Required in production. Changing them later updates your account and signs out old sessions. |
| `SITE_URL` | Public URL, used for link previews and in notifications. |
| `DATA_DIR` | Where the database and uploads live (default `./data`). |
| `PORT` | Port to listen on (default `3000`). |
| `NOTIFY_WEBHOOK_URL` | Optional push notifications (see above). |
| `COOKIE_SECURE` | Defaults to `true` in production. Only set `false` if you serve over plain http. |
| `TRUST_PROXY` | Express `trust proxy` setting, if your host's proxy needs something other than the default. |

In `profile.config.js`, `signup.minPhotos` controls how many photos a visitor must add before they can see you (default 1).

## How it's built

- `server/`: Express API, built-in `node:sqlite` storage, scrypt password hashing, session cookies (HttpOnly, SameSite, Secure in production), CSRF protection, rate limiting, and a strict Content Security Policy.
- `src/`: React app (Vite). Screens are in `src/screens`, shared pieces in `src/components`, styles in `src/styles`.
- `profile.config.js`: the one profile.

Run the API tests with `npm test`.

## Good to know

- Visitors must be 18+ (checked from their birthday).
- Each visitor gets **one like**. If you remove someone's like, they're never told. To them it just stays "sent".
- Either side can unmatch, which closes the chat for both.
- Visitors' photos are only ever served to them and to you.
