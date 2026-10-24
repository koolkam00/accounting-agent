/*
  dd-template.js: shared runtime for every print template in this folder (v1.1, 2026-10-24).

  A template page calls DD.init({ fields, render, fit, ... }) once. This file then:
    1. reads the data: window.__DD_DATA__ (set by render/render.js) or the inline
       <script type="application/json" id="dd-data"> block (what you edit by hand);
    2. builds the fill-in panel from `fields` (screen only, never printed);
    3. renders one printed sheet per record (the data may be one object or an array);
    4. marks unfilled [PLACEHOLDERS] with a yellow highlighter, on screen and on paper;
    5. shows a SAMPLE banner whenever any value (at any depth) starts with "SAMPLE";
    6. publishes window.__DD_STATUS__ = { ready, errors, warnings, sample, placeholders }.

  Field definition: { key, label, required, help, multiline, rows, maxChars, group, options,
                      type: 'text' (default) | 'image' | 'table', columns, minRows, maxRows, rowLabel }
    type 'image': a photo or picture. The value is a file path (relative to the JSON file when
                  rendered from the terminal) or an embedded picture chosen in the panel.
    type 'table': a list of rows. `columns` are field definitions (text or image) for one row.
                  The panel shows one fold-out group per row, with Add and Remove buttons.
    picture: 'logo' on an image field keeps SVG as is and PNG transparency (no JPEG conversion).
  Record options (cfg): recordLabel ('Card', 'Label'): the panel then has a picker to edit any
    record, plus "Add" and "Remove" buttons; recordName(rec, k) names one in the picker;
    newRecord(rec, k) makes the record that "Add" inserts (default: a copy of the current one).
  Messages carry a "Card 3: " prefix only when there is more than one record.
  v1.1 adds image and table fields and the deep scan; v1.0 templates work unchanged.
  v1.2 (2026-10-24, review round 1): record picker, plain single-record messages, logo pictures.
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
  // A value that is only a placeholder slot, e.g. "[N]" or "[DROP DATE: Tue 2027-01-12]"
  DD.isOnlyPlaceholder = (v) => typeof v === 'string' && new RegExp('^\\s*' + PH_SRC + '\\s*$').test(v);

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
  // A founder contact value from brand.json, e.g. DD.contact('PHONE') -> "[PHONE]" until filled.
  // An unfilled contact counts as a placeholder, so --final refuses a document without it.
  DD.contact = (k) => {
    const c = (DD.brand().contact || {});
    const v = c[k] == null ? `[${k.replace(/_/g, ' ')}]` : c[k];
    if (DD.isPlaceholder(String(v))) { const m = `brand.json: ${k} (fill it in brand.json, then run node render/build-brand.js)`; if (DD.status && !DD.status.placeholders.includes(m)) DD.status.placeholders.push(m); }
    return v;
  };

  // Image source for a photo value: embedded data, a URL, or a path. Empty -> null.
  DD.imgSrc = (v) => {
    const s = (v == null ? '' : String(v)).trim();
    if (!s || DD.isPlaceholder(s)) return null;
    return s;
  };

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
  DD.recLabel = () => (DD.cfg && DD.cfg.recordLabel) || 'Record';
  // "Card 3: " when several records are loaded; nothing for a single record (no jargon).
  DD.prefix = (rec) => (rec != null && DD.records().length > 1) ? `${DD.recLabel()} ${rec + 1}: ` : '';
  const push = (list, rec, msg) => { const m = DD.prefix(rec) + msg; if (!list.includes(m)) list.push(m); };
  DD.error = (rec, msg) => push(DD.status.errors, rec, msg);
  DD.warn = (rec, msg) => push(DD.status.warnings, rec, msg);
  DD.placeholder = (rec, what) => push(DD.status.placeholders, rec, what);

  const isEmpty = (v) => v == null || (Array.isArray(v) ? v.length === 0 : String(v).trim() === '');
  function anySample(v) {
    if (typeof v === 'string') return DD.isSampleValue(v);
    if (Array.isArray(v)) return v.some(anySample);
    if (v && typeof v === 'object') return Object.values(v).some(anySample);
    return false;
  }
  DD.rowName = (f, k) => (f.rowLabel ? f.rowLabel(k) : `row ${k + 1}`);

  function scanValue(f, v, i, where) {
    const empty = isEmpty(v);
    if (f.required && empty) DD.error(i, `"${where || f.label}" is empty.`);
    if (empty) return;
    if (f.type === 'image') return; // pictures: the template decides what an empty or [PHOTO] value means
    if (DD.isPlaceholder(String(v))) DD.placeholder(i, where ? where : f.key);
    if (f.maxChars && String(v).length > f.maxChars) DD.warn(i, `"${where || f.label}" is ${String(v).length} characters; aim for ${f.maxChars} or fewer.`);
  }
  function scan(rec, i, fields) {
    for (const f of fields) {
      const v = rec[f.key];
      if (f.type === 'table') {
        const rows = Array.isArray(v) ? v : [];
        if (f.required && !rows.length) DD.error(i, `"${f.label}" has no rows.`);
        rows.forEach((row, k) => (f.columns || []).forEach((c) => scanValue(c, (row || {})[c.key], i, `${DD.rowName(f, k)}: ${c.label}`)));
      } else scanValue(f, v, i, null);
    }
    if (anySample(rec) || rec._sample === true) DD.status.sample = true;
  }

  // ---------- panel (screen only) ----------
  const val = (v) => (v == null ? '' : String(v));
  function inputHTML(f, raw, name) {
    // A [PLACEHOLDER] shows as a grey hint in an empty box, so nobody types after the brackets.
    const isPh = DD.isOnlyPlaceholder(raw);
    const v = isPh ? '' : raw;
    const hint = isPh ? ` placeholder="${DD.escape(raw)}" data-ph="${DD.escape(raw)}"` : (f.hint ? ` placeholder="${DD.escape(f.hint)}"` : '');
    if (f.type === 'image') {
      const src = DD.imgSrc(raw);
      const what = DD.isPlaceholder(raw) ? 'Not attached yet.' : !src ? 'None (prints as "No photo received").' : (src.startsWith('data:') ? `Picture chosen (${Math.round(src.length * 0.75 / 1024)} KB, kept inside the saved JSON).` : `Picture file: ${DD.escape(src.split('/').pop())}`);
      return `<span class="dd-img-pick"><span class="dd-img-what">${what}</span>
        <label class="dd-file dd-file-sm">Choose picture<input type="file" accept="image/jpeg,image/png,image/webp${f.picture === 'logo' ? ',image/svg+xml' : ''}" data-img="${name}" data-kind="${f.picture || 'photo'}"></label>
        ${src ? `<button type="button" data-act="img-clear" data-name="${name}">Remove</button>` : ''}</span>`;
    }
    if (f.options) return `<select name="${name}">${f.options.map(([o, t]) => `<option value="${DD.escape(o)}"${o === (v || f.options[0][0]) ? ' selected' : ''}>${DD.escape(t)}</option>`).join('')}</select>`;
    if (f.multiline) return `<textarea name="${name}" rows="${f.rows || 3}"${hint}>${DD.escape(v)}</textarea>`;
    return `<input name="${name}" value="${DD.escape(v)}"${hint}>`;
  }
  function fieldHTML(f, raw, name) {
    return `<label class="dd-field"><span>${DD.escape(f.label)}${f.required ? ' <i>required</i>' : f.requiredHint ? ` <i>${DD.escape(f.requiredHint)}</i>` : ''}</span>${inputHTML(f, raw, name)}${f.help ? `<small>${DD.escape(f.help)}</small>` : ''}</label>`;
  }
  function tableHTML(f, rows) {
    const max = f.maxRows || 99, min = f.minRows || 0;
    let h = `<div class="dd-table"><p class="dd-table-title">${DD.escape(f.label)}${f.required ? ' <i>required</i>' : ''}</p>${f.help ? `<small class="dd-table-help">${DD.escape(f.help)}</small>` : ''}`;
    rows.forEach((row, k) => {
      const sum = (f.summary ? f.summary(row || {}, k) : DD.rowName(f, k));
      h += `<details class="dd-row"${k === 0 || f.openAll ? ' open' : ''}><summary>${DD.escape(DD.rowName(f, k))}<em>${DD.escape(sum === DD.rowName(f, k) ? '' : sum)}</em></summary>`;
      for (const c of f.columns) h += fieldHTML(c, val((row || {})[c.key]), `${f.key}.${k}.${c.key}`);
      if (rows.length > min) h += `<button type="button" class="dd-row-del" data-act="row-del" data-table="${f.key}" data-row="${k}">Remove ${DD.escape(DD.rowName(f, k))}</button>`;
      h += `</details>`;
    });
    if (rows.length < max) h += `<button type="button" class="dd-row-add" data-act="row-add" data-table="${f.key}">Add a row</button>`;
    return h + '</div>';
  }
  function setPath(obj, name, value) {
    const parts = name.split('.');
    if (parts.length === 1) { obj[name] = value; return; }
    const [key, row, col] = parts;
    obj[key] = (Array.isArray(obj[key]) ? obj[key] : []).map((r) => Object.assign({}, r));
    while (obj[key].length <= +row) obj[key].push({});
    obj[key][+row][col] = value;
  }
  function editable() { return DD.records().map((r) => JSON.parse(JSON.stringify(r || {}))); }
  function commit(cfg, recs) { DD._edited = recs.length === 1 ? recs[0] : recs; DD.renderAll(cfg); }
  // the record the panel edits (a picker chooses it when several are loaded)
  DD._cur = 0;
  const cur = () => Math.max(0, Math.min(DD._cur || 0, DD.records().length - 1));
  const recName = (cfg, k) => { const r = DD.records()[k] || {}; return cfg.recordName ? cfg.recordName(r, k) : `${DD.recLabel()} ${k + 1}`; };
  // Downscale a photo in the browser so the saved JSON stays small (long edge 1600 px, JPEG).
  function readPicture(file, cb, kind) {
    const rd = new FileReader();
    // a logo keeps its own format: SVG as is, PNG with its transparency
    if (kind === 'logo' && /svg/i.test(file.type)) { rd.onload = () => cb(rd.result); rd.readAsDataURL(file); return; }
    rd.onload = () => {
      const img = new Image();
      img.onload = () => {
        const k = Math.min(1, 1600 / Math.max(img.width, img.height));
        const cv = document.createElement('canvas');
        cv.width = Math.round(img.width * k); cv.height = Math.round(img.height * k);
        cv.getContext('2d').drawImage(img, 0, 0, cv.width, cv.height);
        cb(kind === 'logo' ? cv.toDataURL('image/png') : cv.toDataURL('image/jpeg', 0.85));
      };
      img.onerror = () => alert('That picture could not be read. Use a JPEG or PNG (iPhone: share the photo as "Most Compatible", or export it as JPEG).');
      img.src = rd.result;
    };
    rd.readAsDataURL(file);
  }

  function buildPanel(cfg) {
    const old = DD._panel; const scroll = old ? old.scrollTop : 0;
    if (old) old.remove();
    const panel = document.createElement('aside');
    panel.className = 'dd-panel dd-noprint';
    const n = DD.records().length;
    const rec = DD.records()[cur()] || {};
    const multi = n > 1;
    let html = `<h2>Fill in this ${DD.escape(cfg.title || 'template')}</h2>
      <p class="dd-panel-help">${cfg.panelIntro || 'Type in the boxes; the page updates as you type. Grey text under a box says where the value comes from. When it looks right, press <b>Print</b> and follow the print settings below the button.'}</p>
      <div class="dd-panel-actions">
        <button type="button" data-act="print">${DD.escape(cfg.printLabel || 'Print')}</button>
        <button type="button" data-act="save">Save as JSON</button>
        <label class="dd-file">Load JSON<input type="file" accept=".json,application/json" data-act="load"></label>
      </div>
      ${cfg.confirmBeforePrint ? `<label class="dd-confirm"><input type="checkbox" data-act="confirm"> ${DD.escape(cfg.confirmBeforePrint)}</label>` : ''}
      <p class="dd-panel-print">${cfg.printHelp || ''}</p>
      <div class="dd-panel-status" aria-live="polite"></div>`;
    if (multi || cfg.recordLabel) {
      const L = DD.recLabel(), l = L.toLowerCase();
      html += `<div class="dd-rec">${multi ? `<label class="dd-field"><span>${DD.escape(L)} you are editing</span><select data-act="rec">${DD.records().map((r, k) => `<option value="${k}"${k === cur() ? ' selected' : ''}>${DD.escape(recName(cfg, k))}</option>`).join('')}</select><small>${n} ${l}s. The boxes below edit the one chosen here. Print prints all of them.</small></label>` : ''}
        <div class="dd-rec-actions">${cfg.recordLabel ? `<button type="button" data-act="rec-add">Add a ${DD.escape(l)}</button>` : ''}${multi ? `<button type="button" data-act="rec-del">Remove ${DD.escape(recName(cfg, cur()))}</button>` : ''}</div></div>`;
    }
    let group = null;
    for (const f of cfg.fields) {
      if (f.group && f.group !== group) { group = f.group; html += `<h3>${DD.escape(group)}</h3>`; }
      if (f.type === 'table') html += tableHTML(f, Array.isArray(rec[f.key]) ? rec[f.key] : []);
      else html += fieldHTML(f, val(rec[f.key]), f.key);
    }
    panel.innerHTML = html;
    document.body.appendChild(panel);
    panel.scrollTop = scroll;

    panel.addEventListener('input', (e) => {
      const t = e.target;
      if (!t.name) return;
      if (t.dataset.act === 'rec') return;
      const recs = editable();
      // an emptied box goes back to its placeholder, so the page shows what is still missing
      setPath(recs[cur()], t.name, (t.value === '' && t.dataset.ph) ? t.dataset.ph : t.value);
      const top = t.name.split('.')[0], col = t.name.split('.')[2];
      if ((cfg.confirmResetKeys || []).some((k) => k === top || k === col)) { const cb = panel.querySelector('input[data-act="confirm"]'); if (cb) cb.checked = false; }
      commit(cfg, recs);
      const sumEl = t.closest('details') && t.closest('details').querySelector('summary em');
      const tf = cfg.fields.find((x) => x.key === top);
      if (sumEl && tf && tf.summary) { const k = +t.name.split('.')[1]; const s = tf.summary(recs[cur()][top][k] || {}, k); sumEl.textContent = s === DD.rowName(tf, k) ? '' : s; }
      if (multi) { const o = panel.querySelector('select[data-act="rec"] option[value="' + cur() + '"]'); if (o) o.textContent = recName(cfg, cur()); }
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
        a.download = (cfg.fileStem ? cfg.fileStem(r0 || {}) : 'template-data').replace(/[^\w.-]+/g, '-') + '.json';
        document.body.appendChild(a); a.click(); a.remove();
      }
      if (act === 'row-add' || act === 'row-del') {
        const key = e.target.getAttribute('data-table');
        const f = cfg.fields.find((x) => x.key === key);
        const recs = editable();
        const rows = Array.isArray(recs[cur()][key]) ? recs[cur()][key] : [];
        if (act === 'row-add') rows.push(f.newRow ? f.newRow(rows.length) : {});
        else rows.splice(+e.target.getAttribute('data-row'), 1);
        recs[cur()][key] = rows;
        DD._edited = recs.length === 1 ? recs[0] : recs;
        buildPanel(cfg); DD.renderAll(cfg);
      }
      if (act === 'img-clear') {
        const recs = editable(); setPath(recs[cur()], e.target.getAttribute('data-name'), '');
        DD._edited = recs.length === 1 ? recs[0] : recs; buildPanel(cfg); DD.renderAll(cfg);
      }
      if (act === 'rec-add') {
        const recs = editable(); const k = cur();
        const add = cfg.newRecord ? cfg.newRecord(recs[k] || {}, recs.length) : JSON.parse(JSON.stringify(recs[k] || {}));
        recs.splice(k + 1, 0, add); DD._cur = k + 1; DD._edited = recs;
        buildPanel(cfg); DD.renderAll(cfg);
      }
      if (act === 'rec-del') {
        const recs = editable(); if (recs.length < 2) return;
        if (!window.confirm(`Remove ${recName(cfg, cur())}?`)) return;
        recs.splice(cur(), 1); DD._cur = Math.max(0, cur() - 1); DD._edited = recs.length === 1 ? recs[0] : recs;
        buildPanel(cfg); DD.renderAll(cfg);
      }
    });
    panel.addEventListener('change', (e) => {
      const t = e.target;
      if (t.getAttribute('data-act') === 'confirm') { showStatus(); return; }
      if (t.getAttribute('data-act') === 'rec') { DD._cur = +t.value; buildPanel(cfg); showStatus(); return; }
      if (t.tagName === 'SELECT') { t.dispatchEvent(new Event('input', { bubbles: true })); return; }
      if (t.dataset && t.dataset.img) {
        const file = t.files[0]; if (!file) return;
        readPicture(file, (url) => { const recs = editable(); setPath(recs[cur()], t.dataset.img, url); DD._edited = recs.length === 1 ? recs[0] : recs; buildPanel(cfg); DD.renderAll(cfg); }, t.dataset.kind);
        return;
      }
      if (t.getAttribute('data-act') !== 'load') return;
      const file = t.files[0];
      if (!file) return;
      const rd = new FileReader();
      rd.onload = () => {
        try { DD._edited = JSON.parse(rd.result); } catch (err) { alert('That file is not valid JSON: ' + err.message); return; }
        DD._cur = 0;
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
    // a placeholder entry is a field key (or a table cell's label): show the box's label instead
    const labelOf = (m) => { const mm = /^([A-Z][a-z]+ \d+: )?([\s\S]*)$/.exec(m); const f = (DD.cfg.fields || []).find(x => x.key === mm[2]); return (mm[1] || '') + (f ? f.label : mm[2]); };
    s.errors.forEach((m) => items.push(`<li class="err">Fix before printing: ${DD.escape(m)}</li>`));
    s.warnings.forEach((m) => items.push(`<li class="warn">Check: ${DD.escape(m)}</li>`));
    if (s.placeholders.length) {
      const list = s.placeholders.map(labelOf);
      const shown = list.slice(0, 12).join('; ') + (list.length > 12 ? `; and ${list.length - 12} more` : '');
      items.push(`<li class="warn">Still to fill in (yellow on the page): ${DD.escape(shown)}</li>`);
    }
    if (s.sample) items.push(`<li class="warn">This is SAMPLE data. It prints with a SAMPLE banner.</li>`);
    const cb = DD._panel.querySelector('input[data-act="confirm"]');
    if (!items.length && cb && !cb.checked) items.push(`<li class="warn">Last step: ${DD.escape(DD.cfg.confirmBeforePrint)} (tick the box above).</li>`);
    if (!items.length) items.push(`<li class="ok">${DD.escape(DD.cfg.readyText || 'Ready to print.')}</li>`);
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
    // let layout-dependent fitting run after fonts and pictures are ready
    const fit = cfg.fit ? cfg.fit : () => {};
    // Load EVERY declared face first: the print fonts are static files (one per width), and a
    // face that is not loaded yet would be measured in a fallback font and fit wrongly.
    const all = []; document.fonts.forEach((f) => all.push(f.load().catch(() => null)));
    const imgs = [...root.querySelectorAll('img')].map((im) => im.complete ? null : new Promise((res) => { im.onload = im.onerror = res; }));
    return Promise.all(all.concat(imgs)).then(() => document.fonts.ready).then(() => {
      root.querySelectorAll('.dd-sheet').forEach((sheet, gi) => fit(sheet, per === 1 ? groups[gi][0] : groups[gi], gi * per));
      root.querySelectorAll('img').forEach((im) => { if (im.complete && im.naturalWidth === 0 && !im.classList.contains('dd-wordmark')) DD.error(null, `A picture could not be loaded: ${(im.getAttribute('src') || '').slice(0, 80)}`); });
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
