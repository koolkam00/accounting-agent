/*
  dd-docs.js: shared pieces for the Letter documents (v1.1, 2026-10-24). Load after dd-template.js.
    DDDocs.header({ kicker, meta })        wordmark left, kicker and meta right, cobalt rule under
    DDDocs.footer(left, right)              hairline footer
    DDDocs.contact(sep)                     "[FOUNDER NAME] · [PHONE] · [EMAIL]" from brand.json
    DDDocs.imgSlot(src, label)              a real picture, or the grey slot that says
                                            "real pantry photo, no identifiable people"
    DDDocs.cardDiagram(opts)                a drawn tent card with numbered pins (not a photo)
    DDDocs.fitPages(sheet, i, steps)        shrink in a stated order until every page fits; else error
    DDDocs.claimsIn(text)                   claims or soft-ladder words found in a text, if any
    DDDocs.items(text)                      one list item per line
    DDDocs.usd(n)                           "$1,500"
  The name never appears in this file. It comes from system/brand.js.
*/
(function () {
  'use strict';
  const D = window.DD;
  const X = {};
  window.DDDocs = X;

  X.header = function (o) {
    o = o || {};
    return `<header class="hd">${D.wordmarkImg(o.cap || 0.25)}
      <div class="hd-right">${o.kicker ? `<p class="kicker">${D.text(o.kicker)}</p>` : ''}${o.meta ? `<p class="hd-meta">${o.meta}</p>` : ''}</div></header>`;
  };
  X.footer = (left, right) => `<footer class="ft"><div class="ft-l">${left || ''}</div><div class="ft-r">${right || ''}</div></footer>`;
  X.contact = function (sep, keys) {
    keys = keys || ['FOUNDER_NAME', 'PHONE', 'EMAIL'];
    return keys.map((k) => D.contact(k)).filter((v) => String(v).trim() !== '').map(D.text).join(sep || ' · ');
  };
  X.brandName = () => D.escape(D.brand().BRAND_NAME);

  X.imgSlot = function (src, label, cls) {
    const s = D.imgSrc(src);
    if (s) return `<img class="img-fill ${cls || ''}" src="${D.escape(s)}" alt="${D.escape(label || 'photo')}">`;
    return `<div class="img-slot ${cls || ''}"><span>${label ? `<b>${D.escape(label)}</b>` : ''}Real pantry photo, no identifiable people</span></div>`;
  };

  // A QR-like pattern for drawings only: finder squares and a fixed module pattern.
  // It encodes nothing on purpose, so nobody scans a diagram.
  X.pseudoQR = function () {
    let d = '';
    const fin = (x, y) => `M${x} ${y}h7v7h-7z M${x + 1} ${y + 1}v5h5v-5z M${x + 2} ${y + 2}h3v3h-3z`;
    d += fin(0, 0) + fin(14, 0) + fin(0, 14);
    let seed = 7;
    for (let r = 0; r < 21; r++) for (let c = 0; c < 21; c++) {
      if ((r < 8 && c < 8) || (r < 8 && c > 12) || (r > 12 && c < 8)) continue;
      seed = (seed * 1103515245 + 12345) & 0x7fffffff;
      if (seed % 5 < 2) d += `M${c} ${r}h1v1h-1z`;
    }
    return `<svg class="cd-qr" viewBox="-1 -1 23 23" aria-hidden="true"><rect x="-1" y="-1" width="23" height="23" fill="#fff"/><path fill-rule="evenodd" d="${d}" fill="#1F1D1A"/></svg>`;
  };

  // The tent card, drawn. opts: { widthIn, brand, pins: true }. Pins are numbered to match a key list.
  X.cardDiagram = function (o) {
    o = o || {};
    const w = o.widthIn || 2.6;
    const fs = (w * 0.115).toFixed(3); // em base so everything scales with the drawing
    const pin = (n, x, y) => o.pins === false ? '' : `<span class="cd-pin" style="left:${x}%;top:${y}%">${n}</span>`;
    return `<div class="card-dg" style="width:${w}in;font-size:${fs}in" role="img" aria-label="Drawing of the display card">
      <div class="cd-in">
        <div class="cd-band"></div>
        <div class="cd-name">${D.escape(o.brand || 'Brand name')}</div>
        <div class="cd-mid">
          <div class="cd-lines"><i style="width:96%"></i><i style="width:90%"></i><i style="width:94%"></i><i style="width:62%"></i></div>
          <div class="cd-take">Take one.</div>
          ${X.pseudoQR()}
        </div>
        <div class="cd-allergen">Contains: as printed on the package, word for word.</div>
        <div class="cd-foot"><span>Find it at [Retailer], or use code [CODE]</span>${D.wordmarkImg(w * 0.03)}</div>
      </div>
      ${pin(1, 4, 18)}${pin(2, 4, 48)}${pin(3, 97, 46)}${pin(4, 4, 79)}${pin(5, 4, 92)}
    </div>`;
  };
  X.cardKey = [
    'The brand name, big enough to read across the pantry.',
    'Two sentences: who makes it and why.',
    '"Take one. Tell us what you think." The QR opens three questions, no login.',
    'The allergen statement, copied word for word from the package, at a locked 14 pt.',
    'Where to buy it nearby, or a code for the brand\'s own site.'
  ];

  // Fit every .page of a sheet. steps: functions that make one thing smaller and return true,
  // or return false when they have nothing left to give. The fixed parts are never in `steps`.
  X.fitPages = function (sheet, i, steps, what, only) {
    const pages = only || [...sheet.querySelectorAll('.page')];
    const over = () => pages.filter((p) => { const b = p.querySelector('.bd'); return b && b.scrollHeight > b.clientHeight + 1; });
    let guard = 0;
    while (over().length && guard++ < 200) {
      let changed = false;
      for (const s of steps) { if (s()) { changed = true; break; } }
      if (!changed) break;
    }
    const left = over();
    left.forEach((p) => {
      const f = document.createElement('div'); f.className = 'overflow-flag';
      f.textContent = 'DOES NOT FIT ON THE PAGE. Shorten the text named in the panel. No PDF until it fits.';
      p.appendChild(f);
    });
    if (left.length) D.error(i, `${what || 'The text'} runs past the bottom of the page even at the smallest sizes. Shorten it.`);
    return left.length === 0;
  };

  // Claims and soft words. Negations we write ourselves ("no sales guarantee") are allowed.
  const BAD = /\b(healthy|healthier|guarantee[sd]?|guaranteeing|best[- ]?selling|the best|boosts?|immun\w*|cures?|detox\w*|clinically|proven|superfood\w*|lift|ROI|conversions?|converts?|acquisition|acquire[sd]?|viral|skyrocket\w*|explod\w*)\b/gi;
  const OK = /\b(no|not|never|nor|without|isn't|is not|do not|don't|cannot|can't|we never)\b[^.;:]{0,40}?\b(guarantee[sd]?|lift|acquisition|ROI|conversions?)\b/gi;
  X.claimsIn = function (text) {
    const t = String(text || '').replace(OK, ' ');
    const m = t.match(BAD);
    return m ? [...new Set(m.map((x) => x.toLowerCase()))] : [];
  };
  X.checkClaims = function (i, label, text) {
    const found = X.claimsIn(text);
    if (found.length) D.warn(i, `${label} uses "${found.join('", "')}". No health, sales, lift, acquisition or "guaranteed" claims; measurement words come from the ladder.`);
  };

  // Editable copy: {BRAND_NAME} becomes the name from brand.json (so a rename never touches copy),
  // **words** become bold, [PLACEHOLDERS] are highlighted.
  X.t = (s) => D.text(String(s == null ? '' : s).replace(/\{BRAND_NAME\}/g, D.brand().BRAND_NAME)).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
  X.items = (text) => String(text || '').split(/\n+/).map((s) => s.replace(/^\s*[-*•]\s*/, '').trim()).filter(Boolean);
  X.usd = (n) => '$' + Math.round(Number(n)).toLocaleString('en-US');
  X.num = (v) => { const s = String(v == null ? '' : v).trim(); return /^-?\d+(\.\d+)?$/.test(s) ? Number(s) : null; };
})();
