// Optional: get a push notification when someone likes you or messages you.
// Set NOTIFY_WEBHOOK_URL to a Discord webhook, a Slack incoming webhook,
// or an ntfy.sh topic URL (e.g. https://ntfy.sh/some-long-random-topic).

export async function notify(text, siteUrl) {
  const url = process.env.NOTIFY_WEBHOOK_URL;
  if (!url) return;
  const full = siteUrl ? `${text}\n${siteUrl}` : text;
  let body;
  let headers;
  if (url.includes('discord.com/api/webhooks')) {
    body = JSON.stringify({ content: full });
    headers = { 'content-type': 'application/json' };
  } else if (url.includes('hooks.slack.com')) {
    body = JSON.stringify({ text: full });
    headers = { 'content-type': 'application/json' };
  } else {
    body = text;
    headers = { 'content-type': 'text/plain', ...(siteUrl ? { Click: siteUrl } : {}) };
  }
  try {
    await fetch(url, { method: 'POST', body, headers, signal: AbortSignal.timeout(2500) });
  } catch (err) {
    console.warn('[notify] webhook failed:', err.message);
  }
}
