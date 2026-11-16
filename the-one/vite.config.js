import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/** Fill in the page title and link-preview tags from profile.config.js. */
function profileHead() {
  return {
    name: 'profile-head',
    async transformIndexHtml(html) {
      const file = pathToFileURL(path.join(ROOT, 'profile.config.js')).href;
      const cfg = (await import(`${file}?t=${Date.now()}`)).default ?? {};
      const appName = String(cfg.appName || 'the one');
      const name = String(cfg.name || 'me');
      const productionUrl = process.env.VERCEL_PROJECT_PRODUCTION_URL;
      const base = (process.env.SITE_URL || (productionUrl ? `https://${productionUrl}` : '')).replace(/\/+$/, '');
      const title = `${appName} · Meet ${name}`;
      const desc = `One profile. No swiping. Make an account to see ${name}’s profile and send a like.`;
      const tags = [
        `<title>${esc(title)}</title>`,
        `<meta name="description" content="${esc(desc)}" />`,
        '<meta property="og:type" content="website" />',
        `<meta property="og:title" content="${esc(title)}" />`,
        `<meta property="og:description" content="${esc(desc)}" />`,
        `<meta property="og:image" content="${esc(`${base}/og.png`)}" />`,
        base && `<meta property="og:url" content="${esc(base)}" />`,
        '<meta name="twitter:card" content="summary_large_image" />',
        `<meta name="apple-mobile-web-app-title" content="${esc(appName)}" />`,
      ].filter(Boolean);
      return html.replace('<!--app-head-->', tags.join('\n    '));
    },
  };
}

export default defineConfig({
  plugins: [react(), profileHead()],
  build: { outDir: 'dist', sourcemap: false },
});
