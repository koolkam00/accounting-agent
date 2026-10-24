/*
  dd-template.js: shared runtime for every print template in this folder (v1.0, 2026-10-23).

  A template page calls DD.init({ fields, render, sheetClass }) once. This file then:
    1. reads the data: window.__DD_DATA__ (set by render/render.js) or the inline
       <script type="application/json" id="dd-data"> block (what you edit by hand);
    2. builds the fill-in panel from `fields` (screen only, never printed);
    3. renders one printed sheet per record (the data may be one object or an array);
    4. marks unfilled [PLACEHOLDERS] with a yellow highlighter, on screen and on paper;
    5. shows a SAMPLE banner whenever any value starts with "SAMPLE";
    6. publishes window.__DD_STATUS__ = { ready, errors, warnings } for the render script.

  Field definition: { key, label, required, help, multiline, maxChars, group }
  Nothing here talks to the network. It works from file:// in Chrome.
*/
(function () {
  'use strict';
  const DD = {};
  window.DD = DD;

  // [PHONE], [RETAILER, STREET], [DROP DATE: Tue 2027-01-12] ...
  const PH_SRC = "\\[[A-Z][A-Z0-9 ,.'&_\\-/]*(?::[^\\]]*)?\\]";
  const PH_RE = new RegExp(PH_SRC, 'g');
  DD.isPlaceholder = (v) => typeof v === 'string' && new RegExp(PH_SRC).test(v);
  DD.isSampleValue = (v) => typeof v === 'string' && /^\s*SAMPLE\b/.test(v);

  DD.escape = (s) => String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

  // Escape text, keep line breaks, highlight placeholders.
  DD.text = (s) => DD.escape(s).replace(PH_RE, (m) => `<mark class="dd-ph">${m}</mark>`).replace(/\n/g, '<br>');

  // Wordmark sized by CAP HEIGHT (inches), never by box height, so a longer or two-line
  // name keeps readable letters. Returns an <img> tag pointing at the light or dark file.
  DD.wordmarkImg = function (capIn, variant, relRoot) {
    const b = DD.brand();
    const frac = b.wordmark_cap_fraction || 0.78;
    const h = capIn / frac;
    const file = (relRoot || '../../') + 'wordmark/wordmark-' + (variant || 'light') + '.svg';
    return `<img class="dd-wordmark" src="${file}" alt="${DD.escape(b.BRAND_NAME)}" style="height:${h.toFixed(3)}in;width:auto">`;
  };

  DD.brand = () => window.DD_BRAND || { BRAND_NAME: '[BRAND_NAME missing: run node render/build-brand.js]', contact: {} };

  // ---------- QR ----------
  // Returns an SVG string, `sizePx` square, with the 4-module quiet zone the QR spec requires.
  DD.qrSvg = function (text, sizePx, opts) {
    opts = opts || {};
    const ec = opts.ec || 'M';
    if (!text || DD.isPlaceholder(text)) return `<svg class="dd-qr" width="${sizePx}" height="${sizePx}" viewBox="0 0 10 10"><rect width="10" height="10" fill="#fff" stroke="#B3261E" stroke-width="0.2" stroke-dasharray="0.6 0.4"/><text x="5" y="5.6" font-size="1.4" text-anchor="middle" fill="#B3261E" font-family="sans-serif">[QR URL]</text></svg>`;
    const qr = window.qrcode(0, ec);
    qr.addData(text, 'Byte');
    qr.make();
    const n = qr.getModuleCount();
    const q = 4; // quiet zone, modules
    const total = n + 2 * q;
    let d = '';
    for (let r = 0; r < n; r++) {
      for (let c = 0; c < n; c++) {
        if (qr.isDark(r, c)) d += `M${c + q} ${r + q}h1v1h-1z`;
      }
    }
    return `<svg class="dd-qr" xmlns="http://www.w3.org/2000/svg" width="${sizePx}" height="${sizePx}" viewBox="0 0 ${total} ${total}" shape-rendering="crispEdges" data-modules="${n}" data-version="${(n - 17) / 4}"><rect width="${total}" height="${total}" fill="#fff"/><path d="${d}" fill="#000"/></svg>`;
  };

  // ---------- data ----------
  function readInline() {
    const el = document.getElementById('dd-data');
    if (!el) return {};
    try { return JSON.parse(el.textContent); } catch (e) {
      DD.fatal = 'The JSON block in this file has a typo: ' + e.message;
      return {};
    }
  }
  DD.records = function () {
    const d = window.__DD_DATA__ !== undefined ? window.__DD_DATA__ : (DD._edited || readInline());
    return Array.isArray(d) ? d : [d];
  };

  // ---------- status ----------
  function newStatus() { return { ready: false, errors: [], warnings: [], sample: false, placeholders: [] }; }
  DD.status = newStatus();
  const push = (list, rec, msg) => { const m = (rec != null ? `record ${rec + 1}: ` : '') + msg; if (!list.includes(m)) list.push(m); };
  DD.error = (rec, msg) => push(DD.status.errors, rec, msg);
  DD.warn = (rec, msg) => push(DD.status.warnings, rec, msg);

  function scan(rec, i, fields) {
    for (const f of fields) {
      const v = rec[f.key];
      const empty = v == null || String(v).trim() === '';
      if (f.required && empty) DD.error(i, `"${f.label}" is empty.`);
      if (!empty && DD.isPlaceholder(String(v))) DD.status.placeholders.push(`record ${i + 1}: ${f.key}`);
      if (!empty && f.maxChars && String(v).length > f.maxChars) DD.warn(i, `"${f.label}" is ${String(v).length} characters; aim for ${f.maxChars} or fewer.`);
    }
    if (Object.values(rec).some(DD.isSampleValue) || rec._sample === true) DD.status.sample = true;
  }

  // ---------- panel (screen only) ----------
  function buildPanel(cfg) {
    const panel = document.createElement('aside');
    panel.className = 'dd-panel dd-noprint';
    const rec = DD.records()[0] || {};
    const multi = DD.records().length > 1;
    let html = `<h2>Fill in this ${DD.escape(cfg.title || 'template')}</h2>
      <p class="dd-panel-help">Type in the boxes; the page updates as you type. Grey text under a box says where the value comes from. When it looks right, press <b>Print</b> and follow the print settings below the button.</p>
      <div class="dd-panel-actions">
        <button type="button" data-act="print">Print</button>
        <button type="button" data-act="save">Save as JSON</button>
        <label class="dd-file">Load JSON<input type="file" accept=".json,application/json" data-act="load"></label>
      </div>
      ${cfg.confirmBeforePrint ? `<label class="dd-confirm"><input type="checkbox" data-act="confirm"> ${DD.escape(cfg.confirmBeforePrint)}</label>` : ''}
      <p class="dd-panel-print">${cfg.printHelp || ''}</p>
      <div class="dd-panel-status" aria-live="polite"></div>`;
    if (multi) html += `<p class="dd-panel-help"><b>${DD.records().length} records loaded.</b> The boxes edit record 1 only. Edit the JSON file for the others.</p>`;
    let group = null;
    for (const f of cfg.fields) {
      if (f.group && f.group !== group) { group = f.group; html += `<h3>${DD.escape(group)}</h3>`; }
      // A [PLACEHOLDER] shows as a grey hint in an empty box, so nobody types after the brackets.
      const raw = rec[f.key] == null ? '' : String(rec[f.key]);
      const isPh = DD.isPlaceholder(raw) && /^\s*\[[^\]]*\]\s*$/.test(raw);
      const val = isPh ? '' : raw;
      const hint = isPh ? ` placeholder="${DD.escape(raw)}" data-ph="${DD.escape(raw)}"` : '';
      const input = f.multiline
        ? `<textarea name="${f.key}" rows="${f.rows || 3}"${hint}>${DD.escape(val)}</textarea>`
        : `<input name="${f.key}" value="${DD.escape(val)}"${hint}>`;
      html += `<label class="dd-field"><span>${DD.escape(f.label)}${f.required ? ' <i>required</i>' : ''}</span>${input}${f.help ? `<small>${DD.escape(f.help)}</small>` : ''}</label>`;
    }
    panel.innerHTML = html;
    document.body.appendChild(panel);

    panel.addEventListener('input', (e) => {
      const t = e.target;
      if (!t.name) return;
      const recs = DD.records().map((r) => Object.assign({}, r));
      // an emptied box goes back to its placeholder, so the card shows what is still missing
      recs[0][t.name] = (t.value === '' && t.dataset.ph) ? t.dataset.ph : t.value;
      if ((cfg.confirmResetKeys || []).includes(t.name)) { const cb = panel.querySelector('input[data-act="confirm"]'); if (cb) cb.checked = false; }
      DD._edited = recs.length === 1 ? recs[0] : recs;
      DD.renderAll(cfg);
    });
    panel.addEventListener('click', (e) => {
      const act = e.target.getAttribute && e.target.getAttribute('data-act');
      if (act === 'print') {
        const box = panel.querySelector('input[data-act="confirm"]');
        if (box && !box.checked && !window.confirm(cfg.confirmBeforePrint + '?\n\nPress Cancel to go back and check.')) return;
        window.print();
      }
      if (act === 'save') {
        const data = DD._edited || (window.__DD_DATA__ !== undefined ? window.__DD_DATA__ : readInline());
        const blob = new Blob([JSON.stringify(data, null, 2) + '\n'], { type: 'application/json' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        const r0 = Array.isArray(data) ? data[0] : data;
        a.download = (cfg.fileStem ? cfg.fileStem(r0 || {}) : 'template-data') + '.json';
        document.body.appendChild(a); a.click(); a.remove();
      }
    });
    panel.addEventListener('change', (e) => {
      if (e.target.getAttribute('data-act') === 'confirm') { showStatus(); return; }
      if (e.target.getAttribute('data-act') !== 'load') return;
      const file = e.target.files[0];
      if (!file) return;
      const rd = new FileReader();
      rd.onload = () => {
        try { DD._edited = JSON.parse(rd.result); } catch (err) { alert('That file is not valid JSON: ' + err.message); return; }
        panel.remove();
        buildPanel(cfg);
        DD.renderAll(cfg);
      };
      rd.readAsText(file);
    });
    DD._panel = panel;
  }

  function showStatus() {
    const box = DD._panel && DD._panel.querySelector('.dd-panel-status');
    if (!box) return;
    const s = DD.status;
    const items = [];
    const single = DD.records().length === 1;
    const plain = (m) => single ? m.replace(/^record 1: /, '') : m;   // no jargon for one card
    const labelOf = (m) => { const k = m.replace(/^record \d+: /, ''); const f = (DD.cfg.fields || []).find(x => x.key === k); return plain(f ? m.replace(k, f.label) : m); };
    s.errors.forEach((m) => items.push(`<li class="err">Fix before printing: ${DD.escape(plain(m))}</li>`));
    s.warnings.forEach((m) => items.push(`<li class="warn">Check: ${DD.escape(plain(m))}</li>`));
    if (s.placeholders.length) items.push(`<li class="warn">Still to fill in (yellow on the page): ${DD.escape(s.placeholders.map(labelOf).join('; '))}</li>`);
    if (s.sample) items.push(`<li class="warn">This is SAMPLE data. It prints with a SAMPLE banner.</li>`);
    const cb = DD._panel.querySelector('input[data-act="confirm"]');
    if (!items.length && cb && !cb.checked) items.push(`<li class="warn">Last step: ${DD.escape(DD.cfg.confirmBeforePrint)} (tick the box above).</li>`);
    if (!items.length) items.push('<li class="ok">Ready to print.</li>');
    box.innerHTML = `<ul>${items.join('')}</ul>`;
  }

  // ---------- render ----------
  DD.renderAll = function (cfg) {
    DD.status = newStatus();
    if (DD.fatal) DD.error(null, DD.fatal);
    const root = document.getElementById('dd-sheets');
    root.innerHTML = '';
    const recs = DD.records().map((r) => r || {});
    const per = cfg.perSheet || 1;               // e.g. 2 case labels per Letter sheet
    recs.forEach((rec, i) => { if (!rec._skip) scan(rec, i, cfg.fields); });
    const groups = [];
    for (let i = 0; i < recs.length; i += per) groups.push(recs.slice(i, i + per));
    groups.forEach((g, gi) => {
      const sheet = document.createElement('section');
      sheet.className = 'dd-sheet ' + (cfg.sheetClass || '');
      root.appendChild(sheet);
      if (per === 1) cfg.render(sheet, g[0], gi); else cfg.render(sheet, g, gi * per);
    });
    document.body.classList.toggle('dd-is-sample', DD.status.sample);
    // let layout-dependent fitting run after fonts are ready
    const fit = cfg.fit ? cfg.fit : () => {};
    return document.fonts.ready.then(() => {
      root.querySelectorAll('.dd-sheet').forEach((sheet, gi) => fit(sheet, per === 1 ? groups[gi][0] : groups[gi], gi * per));
      DD.status.ready = true;
      window.__DD_STATUS__ = DD.status;
      showStatus();
    });
  };

  DD.init = function (cfg) {
    DD.cfg = cfg;
    const start = () => {
      if (!window.__DD_HEADLESS__) buildPanel(cfg);
      DD.renderAll(cfg);
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
  };
})();
