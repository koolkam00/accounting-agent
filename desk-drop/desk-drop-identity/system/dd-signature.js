/*
  dd-signature.js: the email signature, built from the name and your details (v1.2, 2026-10-24).
  One builder for both paths, so they always match:
    - the terminal: render/build-signature.js writes signature/*.html and *.txt with it;
    - Chrome only: details.html shows the same signature live, ready to copy into Gmail.
  DDSignature.html(brand, { outreach, logoUrl, footerB })  the signature as an HTML table, inline styles only
  DDSignature.text(brand, { outreach, footerB })            the plain-text signature
  DDSignature.missing(brand)                                contact keys still [PLACEHOLDERS]
  Commercial email needs a real postal address (CAN-SPAM; desk-drop-legal-pack/02-email-footer-and-checklist.md).
  An unfilled [PLACEHOLDER] prints with a yellow highlight so it cannot go out unnoticed.
  If contact.WEBSITE is "" (empty), the website is left out (legal pack: no website until it is public).
*/
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.DDSignature = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  // Footer B fallback: the legal pack's text as of v0.5, 2026-10-24. The real text is read from
  // the legal pack at build time (render/build-signature.js) and passed in as opts.footerB.
  const FOOTER_B_FALLBACK = 'This is a business pitch, sent one to one. Not interested? Reply "no thanks" and I won\'t email you again.';
  const PH = /\[[A-Z][A-Z0-9 ,.'&_\-/]*(?::[^\]]*)?\]/;
  const isPh = (v) => PH.test(String(v || ''));
  const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const hl = (s) => esc(s).replace(new RegExp(PH.source, 'g'), (m) => `<span style="background-color:#FFE45C;color:#1F1D1A;">${m}</span>`);
  const INK = '#1F1D1A', SOFT = '#3A3732', COBALT = '#2E47C9';
  const FONT = "'Atkinson Hyperlegible Next', Arial, Helvetica, sans-serif";

  function parts(brand) {
    const c = (brand && brand.contact) || {};
    const site = c.WEBSITE === '' ? null : (c.WEBSITE || '[WEBSITE]');
    return { c, NAME: brand.BRAND_NAME, TITLE: c.FOUNDER_TITLE || 'Founder', site };
  }
  function html(brand, opts) {
    opts = opts || {};
    const { c, NAME, TITLE, site } = parts(brand);
    const link = (href, text) => isPh(text) ? hl(text) : `<a href="${esc(href)}" style="color:${SOFT};text-decoration:none;">${esc(text)}</a>`;
    const telHref = 'tel:' + String(c.PHONE || '').replace(/[^\d+]/g, '');
    const contactLine = [link(telHref, c.PHONE || '[PHONE]'), link('mailto:' + (c.EMAIL || ''), c.EMAIL || '[EMAIL]'), site ? link(/^https?:/.test(site) ? site : 'https://' + site, site.replace(/^https?:\/\//, '')) : null]
      .filter(Boolean).map((x, k, all) => `<span style="white-space:nowrap;">${x}${k < all.length - 1 ? '&nbsp;&middot;' : ''}</span>`).join(' ');
    const nameLine = opts.logoUrl
      ? `<img src="${esc(opts.logoUrl)}" width="112" height="18" alt="${esc(NAME)}" style="display:block;border:0;width:112px;height:auto;margin:2px 0 4px 0;">`
      : '';
    return `<table cellpadding="0" cellspacing="0" border="0" role="presentation" style="border-collapse:collapse;font-family:${FONT};color:${INK};">
  <tr>
    <td style="border-left:3px solid ${COBALT};padding:1px 0 1px 10px;">
      <div style="font-size:14px;line-height:20px;font-weight:bold;color:${INK};">${hl(c.FOUNDER_NAME || '[FOUNDER NAME]')}</div>
      <div style="font-size:13px;line-height:19px;color:${INK};">${esc(TITLE)}, <b>${esc(NAME)}</b></div>
      ${nameLine}
      <div style="font-size:13px;line-height:19px;color:${SOFT};">${contactLine}</div>
      <div style="font-size:13px;line-height:19px;color:${SOFT};">${hl(c.POSTAL_ADDRESS || '[POSTAL ADDRESS]')}</div>
    </td>
  </tr>
</table>${opts.outreach ? `
<div style="font-family:${FONT};font-size:13px;line-height:19px;color:#333333;margin:12px 0 0 0;">${esc(opts.footerB || FOOTER_B_FALLBACK)}</div>` : ''}`;
  }
  function text(brand, opts) {
    opts = opts || {};
    const { c, NAME, TITLE, site } = parts(brand);
    const lines = [
      c.FOUNDER_NAME || '[FOUNDER NAME]',
      `${TITLE}, ${NAME}`,
      [c.PHONE || '[PHONE]', c.EMAIL || '[EMAIL]', site ? site.replace(/^https?:\/\//, '') : null].filter(Boolean).join(' | '),
      c.POSTAL_ADDRESS || '[POSTAL ADDRESS]'
    ];
    if (opts.outreach) lines.push('', opts.footerB || FOOTER_B_FALLBACK);
    return lines.join('\n') + '\n';
  }
  const missing = (brand) => ['FOUNDER_NAME', 'PHONE', 'EMAIL', 'POSTAL_ADDRESS', 'WEBSITE'].filter((k) => isPh(((brand && brand.contact) || {})[k]));
  return { html, text, missing, isPlaceholder: isPh, FOOTER_B_FALLBACK };
});
