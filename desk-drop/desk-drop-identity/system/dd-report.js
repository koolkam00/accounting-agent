/*
  dd-report.js: the one-page campaign report (v1.1, 2026-10-24). Load after dd-template.js,
  dd-dates.js and dd-docs.js. Used by templates/report/report.html and, in mock mode, by the
  proposal's mock page, so the mock is always exactly the real layout.

  Layout follows plan.md appendix M and "Measurement and the brand report":
    1 header (brand, SKU, cluster, drop date, window)   2 the ladder, rung by rung
    3 roster table by office                              4 evidence, two photos per office
    5 survey (counts beside every share, three comments word for word)
    6 engagement (scans, code redemptions, retailer velocity if the brand has it)
    7 what we learned   8 recommendation   9 limitations: the fixed paragraph, every time
  Optional page 2: the evidence appendix (every photo, larger), when photos are attached.

  Ladder words are fixed: delivered, placed, depleted, responded, scanned, purchased, incremental.
*/
(function () {
  'use strict';
  const D = window.DD, X = window.DDDocs, Dt = window.DDDates;
  const R = {};
  window.DDReport = R;

  // THE LIMITATIONS PARAGRAPH. Fixed text: not a field, never edited per report.
  // Built from plan.md "Measurement and the brand report", one limitation per rung.
  R.LIMITATIONS = 'Each number is a separate step, counted as described, and none of them is a sale. ' +
    'Delivered is our count at handoff. Placed is the count of units visible in the placement photo; an office may hold some back for later. ' +
    'Depleted (gone by day 5) comes from photos or the pantry owner\'s count; one person may take several, and sharing and disposal are invisible. ' +
    'Tuesday headcount is a range the office reports; not everyone visits the pantry. ' +
    'Survey responses are anonymous and self-selected, and the samples are small, so one answer can move a share by several points. ' +
    'A QR scan is curiosity, not intent. Code redemptions are reported by the brand, and some of those people would have bought anyway. ' +
    'Retailer sales, where shown, are confounded by everything else that happened that month and are suggestive only. ' +
    'We did not measure incremental purchases, so this report does not show whether the campaign caused any sale.';

  const BANDS = { '40-75': '40 to 75', '76-150': '76 to 150', '151-250': '151 to 250', '251-500': '251 to 500', 'under-40': 'under 40', 'over-500': 'over 500', 'unknown': 'unknown' };
  R.BAND_OPTIONS = [['[BAND]', 'choose'], ['40-75', '40 to 75'], ['76-150', '76 to 150'], ['151-250', '151 to 250'], ['under-40', 'under 40'], ['251-500', '251 to 500'], ['unknown', 'unknown']];
  const band = (v) => BANDS[String(v || '').trim()] || String(v || '');

  // ---- numbers ----
  const n = (v) => X.num(v);
  const ph = (v) => D.isPlaceholder(String(v == null ? '' : v));
  const show = (v, dflt) => { const s = String(v == null ? '' : v).trim(); return s ? D.text(s) : `<mark class="dd-ph">${dflt || '[N]'}</mark>`; };
  function sum(rows, key, emptyIsZero) {
    let t = 0;
    for (const r of rows) { const s = String(r[key] == null ? '' : r[key]).trim(); if (!s && emptyIsZero) continue; const x = n(s); if (x == null) return null; t += x; }
    return t;
  }
  const pct = (a, b) => (a == null || !b) ? null : Math.round(100 * a / b);
  const totalOr = (t, label) => t == null ? `<mark class="dd-ph">${label || '[N]'}</mark>` : t.toLocaleString('en-US');

  // ---- dates ----
  function dates(r) {
    const f = Dt.readDateField(r.drop_date);
    if (!f.iso) return { ok: false, slot: true, drop: show(r.drop_date, '[DROP DATE]') };
    const c = Dt.campaign(f.iso);
    const w = (label, d) => f.slot ? `<mark class="dd-ph">[${label}: ${Dt.fmt(d)}]</mark>` : Dt.fmt(d);
    return Object.assign({ ok: true, slot: f.slot, cal: c, w }, {
      drop: f.slot ? D.text(r.drop_date) : Dt.fmt(c.dates.drop),
      close: w('WINDOW CLOSES', c.dates.close), report: w('REPORT', c.dates.report), redemption: w('REDEMPTION CHECK', c.dates.redemption),
      day3: c.dates.day3, day5: c.dates.close, d1: c.dates.drop
    });
  }

  // ---- checks (errors block the PDF, warnings show in the panel and the render output) ----
  R.validate = function (r, i) {
    const rows = Array.isArray(r.offices) ? r.offices : [];
    if (!rows.length) D.error(i, 'The report needs at least one office row.');
    rows.forEach((o, k) => {
      const L = `Office ${o.office_label || String.fromCharCode(65 + k)}`;
      for (const key of ['units_delivered', 'units_placed', 'units_depleted_day5', 'survey_responses', 'qr_scans', 'units_topped_up']) {
        const s = String(o[key] == null ? '' : o[key]).trim();
        if (!s && key !== 'units_topped_up') D.error(i, `${L}: "${COLS[key]}" is empty. Enter the count (0 if none).`);
        else if (s && !ph(s) && !/^\d+$/.test(s)) D.error(i, `${L}: "${COLS[key]}" must be a whole number, not "${s}".`);
      }
      const del = n(o.units_delivered), pl = n(o.units_placed), top = n(o.units_topped_up) || 0, dep = n(o.units_depleted_day5), resp = n(o.survey_responses);
      if (del != null && pl != null && pl > del) D.error(i, `${L}: placed (${pl}) is more than delivered (${del}).`);
      if (pl != null && dep != null && dep > pl + top) D.error(i, `${L}: depleted by day 5 (${dep}) is more than placed plus topped up (${pl + top}).`);
      if (resp != null && resp < 5) D.warn(i, `${L} has ${resp} survey responses, under the five the office committed to. Report it as it is.`);
      if (o.placed_within_1bd && !/^[YN]$/.test(String(o.placed_within_1bd).trim())) D.error(i, `${L}: "placed within one business day" must be Y or N.`);
    });
    const total = sum(rows, 'survey_responses');
    const ty = n(r.survey_tried_yes);
    if (total != null && ty != null && ty > total) D.error(i, `"Tried it" (${ty}) is more than the survey responses (${total}).`);
    const nos = ['tried_no_didnt_see', 'tried_no_not_for_me', 'tried_no_gone'].map((k) => n(r[k]));
    if (total != null && ty != null && nos.every((x) => x != null) && nos.reduce((a, b) => a + b, 0) > total - ty) D.error(i, 'The "did not try" reasons add up to more than the people who did not try.');
    const by = ['survey_buy_yes', 'survey_buy_maybe', 'survey_buy_no'].map((k) => n(r[k]));
    if (total != null && by.every((x) => x != null) && by.reduce((a, b) => a + b, 0) > total) D.error(i, 'The "would buy" answers add up to more than the survey responses.');
    const avg = n(r.survey_rating_avg), rn = n(r.survey_rating_n);
    if (avg != null && (avg < 1 || avg > 5)) D.error(i, `Average rating ${avg} is outside 1 to 5.`);
    if (rn != null && ty != null && rn > ty) D.warn(i, `${rn} ratings but only ${ty} said they tried it. Check the survey export.`);
    ['comment_1', 'comment_2', 'comment_3'].forEach((k, j) => {
      const c = String(r[k] || '');
      if (/[\w.+-]+@[\w-]+\.[\w.]+/.test(c) || /\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}/.test(c)) D.error(i, `Comment ${j + 1} contains what looks like an email address or phone number. Choose a different comment; never edit a comment's words.`);
    });
    X.checkClaims(i, '"What we learned"', r.learned);
    X.checkClaims(i, '"Recommendation"', r.recommendation);
    X.checkClaims(i, '"Retailer velocity"', r.retailer_velocity);
    const d = dates(r);
    if (d.ok) { d.cal.errors.forEach((m) => D.error(i, m)); d.cal.warnings.forEach((m) => D.warn(i, m)); }
  };

  const COLS = {
    units_delivered: 'Delivered', units_placed: 'Placed', units_topped_up: 'Topped up', units_depleted_day5: 'Depleted by day 5',
    survey_responses: 'Responses', qr_scans: 'Scans'
  };

  // ---- page 1 ----
  R.page = function (r, opts) {
    opts = opts || {};
    const mock = !!opts.mock;
    const rows = Array.isArray(r.offices) ? r.offices : [];
    const d = dates(r);
    const label = (o, k) => D.text(o.office_label || String.fromCharCode(65 + k));
    const tDel = sum(rows, 'units_delivered'), tTop = sum(rows, 'units_topped_up', true), tPl = sum(rows, 'units_placed'),
      tDep = sum(rows, 'units_depleted_day5'), tResp = sum(rows, 'survey_responses'), tScan = sum(rows, 'qr_scans');
    const onShelf = (tPl == null || tTop == null) ? null : tPl + tTop;
    const late = rows.filter((o) => String(o.placed_within_1bd || '').trim() === 'N').length;
    const known1bd = rows.filter((o) => /^[YN]$/.test(String(o.placed_within_1bd || '').trim())).length;
    const resp5 = rows.filter((o) => n(o.survey_responses) != null && n(o.survey_responses) >= 5).length;
    const redeem = String(r.code_redemptions_to_date == null ? '' : r.code_redemptions_to_date).trim();
    const asOf = r.code_redemptions_as_of ? D.text(r.code_redemptions_as_of) : (d.ok ? d.report : '<mark class="dd-ph">[DATE]</mark>');

    const rung = (name, value, hint, off) => `<div class="rung${off ? ' off' : ''}"><span class="rn">${name}</span><span class="rv">${value}</span><span class="rh">${hint}</span></div>`;
    const ladder = `<div class="ladder">
      ${rung('Delivered', totalOr(tDel == null || tTop == null ? null : tDel + tTop), `Counted at handoff.${tTop ? ` Includes ${tTop} day-3 top-ups from reserve.` : ''}`)}
      ${rung('Placed', totalOr(tPl), known1bd === rows.length && rows.length ? `In the placement photos. ${rows.length - late} of ${rows.length} offices within one business day.` : 'In the placement photos.')}
      ${rung('Depleted', totalOr(tDep), onShelf ? `Gone by day 5: ${pct(tDep, onShelf) == null ? '[N]' : pct(tDep, onShelf) + '%'} of the ${onShelf} on the shelf.` : 'Gone by day 5.')}
      ${rung('Responded', totalOr(tResp), rows.length ? `Survey responses. ${resp5} of ${rows.length} offices reached five.` : 'Survey responses.')}
      ${rung('Scanned', totalOr(tScan), 'QR scans, across all offices. By office below.')}
      ${rung('Purchased', redeem ? show(redeem) : '<mark class="dd-ph">[N]</mark>', `Code redemptions the brand reported, to ${asOf}.${d.ok ? ` Final check ${d.redemption}.` : ''}`)}
      ${rung('Incremental', 'Not measured', 'Purchases caused by the campaign. Not measured; see limitations.', true)}
    </div>`;

    const cell = (o, key, dflt) => { const s = String(o[key] == null ? '' : o[key]).trim(); return s ? D.text(s) : (dflt != null ? dflt : '<mark class="dd-ph">[N]</mark>'); };
    const body = rows.map((o, k) => `<tr>
        <td><b>${label(o, k)}</b></td><td>${cell(o, 'industry', '<mark class="dd-ph">[INDUSTRY]</mark>')}</td><td class="nowrap">${o.headcount_band ? D.text(band(o.headcount_band)) : '<mark class="dd-ph">[BAND]</mark>'}</td>
        <td class="r num">${cell(o, 'units_delivered')}</td>
        <td class="r num">${cell(o, 'units_placed')}${String(o.placed_within_1bd || '').trim() === 'N' ? '<sup>*</sup>' : ''}</td>
        <td class="r num">${cell(o, 'units_topped_up', '0')}</td>
        <td class="r num">${cell(o, 'units_depleted_day5')}</td>
        <td class="r num">${cell(o, 'survey_responses')}</td>
        <td class="r num">${cell(o, 'qr_scans')}</td></tr>`).join('');
    const roster = `<table class="t roster">
      <thead><tr><th>Office</th><th>Industry</th><th>Tuesday headcount</th><th class="r">Delivered</th><th class="r">Placed</th><th class="r">Topped up</th><th class="r">Depleted by day 5</th><th class="r">Responses</th><th class="r">Scans</th></tr></thead>
      <tbody>${body}<tr class="total"><td colspan="3">All ${rows.length} offices</td><td class="r num">${totalOr(tDel)}</td><td class="r num">${totalOr(tPl)}</td><td class="r num">${totalOr(tTop)}</td><td class="r num">${totalOr(tDep)}</td><td class="r num">${totalOr(tResp)}</td><td class="r num">${totalOr(tScan)}</td></tr></tbody></table>
      ${late ? `<p class="note"><sup>*</sup> Placed after the first business day.</p>` : ''}`;

    const thumbs = rows.map((o, k) => `<div class="ev">
        <div class="ev-pair">
          <figure>${X.imgSlot(mock ? '' : o.placement_photo, '', 'ev-img')}<figcaption>${label(o, k)} · day 1</figcaption></figure>
          <figure>${X.imgSlot(mock ? '' : o.later_photo, '', 'ev-img')}<figcaption>${label(o, k)} · day ${String(o.later_photo_day || '5').trim() === '3' ? '3' : '5'}</figcaption></figure>
        </div></div>`).join('');
    const anyPhoto = !mock && rows.some((o) => D.imgSrc(o.placement_photo) || D.imgSrc(o.later_photo));
    const evidence = `<div class="evg ${rows.length > 5 ? 'many' : 'few'}">${thumbs}</div>
      <p class="note">Wide shot of the pantry on day 1, close shot of card and product later. Real pantry photos, no identifiable people.${anyPhoto ? ' Every photo, larger, is on the evidence page that follows.' : ''}</p>`;

    // survey
    const ry = n(r.survey_buy_yes), rm = n(r.survey_buy_maybe), rno = n(r.survey_buy_no);
    const buyN = [ry, rm, rno].every((x) => x != null) ? ry + rm + rno : null;
    const share = (a, b) => (a == null || b == null) ? '' : ` (${pct(a, b)}%)`;
    const ty = n(r.survey_tried_yes);
    const nos = [['didn\'t see it', 'tried_no_didnt_see'], ['not for me', 'tried_no_not_for_me'], ['gone by the time I looked', 'tried_no_gone']];
    const noLine = nos.some(([, k]) => String(r[k] || '').trim()) ? ` · Did not try: ${nos.map(([t, k]) => `${t} ${show(r[k])}`).join(', ')}` : '';
    const stats = `<p class="sv-stats"><b>Responses ${totalOr(tResp)}</b> · Tried it ${show(r.survey_tried_yes)} of ${totalOr(tResp)}${share(ty, tResp)}
      · Average rating ${show(r.survey_rating_avg, '[N.N]')} of 5 (${show(r.survey_rating_n)} ratings)
      · Would buy: yes ${show(r.survey_buy_yes)}${share(ry, buyN)}, maybe ${show(r.survey_buy_maybe)}${share(rm, buyN)}, no ${show(r.survey_buy_no)}${share(rno, buyN)}${buyN != null && tResp != null && buyN < tResp ? ` of ${buyN} who answered` : ''}${noLine}</p>`;
    const q = (k, j) => `<blockquote class="cm">${r[k] && String(r[k]).trim() ? '“' + D.text(String(r[k]).trim()) + '”' : `<mark class="dd-ph">[VERBATIM COMMENT ${j}]</mark>`}</blockquote>`;
    const comments = `<div class="cms">${q('comment_1', 1)}${q('comment_2', 2)}${q('comment_3', 3)}</div>
      <p class="note">Three ${r.comments_total ? `of ${D.text(r.comments_total)} ` : ''}comments, copied word for word, not edited. Comments are not linked to an office.</p>`;

    const engagement = `<p class="eng"><b>Engagement:</b> ${totalOr(tScan)} scans across ${rows.length} offices (by office in the table) · ${redeem ? show(redeem) : '<mark class="dd-ph">[N]</mark>'} code redemptions to date, reported by the brand to ${asOf}${d.ok ? `; final check ${d.redemption}` : ''}.
      ${String(r.retailer_velocity || '').trim() ? `<br><b>Retailer velocity (the brand's own data, suggestive only):</b> ${D.text(r.retailer_velocity)}` : ''}</p>`;

    const learned = X.items(r.learned);
    const learnedHTML = `<ul class="plain lr">${(learned.length ? learned : ['[WHAT WE LEARNED 1]', '[WHAT WE LEARNED 2]', '[WHAT WE LEARNED 3]']).map((x) => `<li>${D.text(x)}</li>`).join('')}</ul>`;

    const tier = String(r.tier || '').trim();
    const meta = [
      D.text(r.cluster || 'Flatiron, NoMad and Union Square'),
      `Drop ${d.drop}`,
      d.ok ? `Window ${d.slot ? '' : ''}${Dt.fmt(d.d1)} to ${Dt.fmt(d.day5)}` : 'Window <mark class="dd-ph">[WINDOW]</mark>',
      `${tier === 'founding' ? 'Founding' : tier === 'standard' ? 'Standard' : '<mark class="dd-ph">[TIER]</mark>'} campaign, ${rows.length} offices`
    ].join(' · ');
    const reportDate = r.report_date ? D.text(r.report_date) : (d.ok ? d.report : '<mark class="dd-ph">[REPORT DATE]</mark>');

    return `<div class="page rpt${mock ? ' mock' : ''}">
      ${mock ? `<div class="mock-band">Mock report page <span>·</span> Illustrative placeholders, not results</div><div class="mock-side">Illustrative placeholders, not results</div>` : '<div class="dd-sample-banner">Sample. Illustrative placeholders, not results.</div>'}
      ${X.header({ kicker: 'Campaign report', meta: `${D.text(r.campaign_id || '[CAMPAIGN ID]')} · report ${reportDate}` })}
      <div class="bd">
        <div class="rpt-title"><h1 class="title rt">${show(r.brand_name, '[BRAND]')} <span class="sku">· ${show(r.product_sku, '[SKU]')}</span></h1>
          <p class="rpt-meta">${meta}</p></div>
        <section class="sec">${ladder}</section>
        <section class="sec"><h2>Roster</h2>${roster}</section>
        <section class="sec"><h2>Evidence: two photos per office</h2>${evidence}</section>
        <section class="sec"><h2>Survey</h2>${stats}${comments}${engagement}</section>
        <section class="sec g6 lr-row">
          <div class="s4"><h2>What we learned</h2>${learnedHTML}</div>
          <div class="s2 box rec"><h2>Recommendation</h2><p>${show(r.recommendation, '[RENEW INTO WHICH OFFICES, ADJUST WHAT, OR STOP]')}</p></div>
        </section>
        <section class="sec lim"><h3>Limitations</h3><p class="lim-text">${D.escape(R.LIMITATIONS)}</p></section>
      </div>
      ${X.footer(`Prepared by ${D.text(r.prepared_by || D.contact('FOUNDER_NAME'))} · ${X.contact(' · ', ['PHONE', 'EMAIL'])}`, `${X.brandName()} · report template v1.1`)}
    </div>`;
  };

  // ---- page 2: every photo, larger ----
  R.appendix = function (r) {
    const rows = Array.isArray(r.offices) ? r.offices : [];
    if (!rows.some((o) => D.imgSrc(o.placement_photo) || D.imgSrc(o.later_photo))) return '';
    const d = dates(r);
    const when = (o, first) => d.ok ? Dt.fmt(first ? d.d1 : (String(o.later_photo_day || '5').trim() === '3' ? d.day3 : d.day5)) : '';
    const cells = rows.map((o, k) => {
      const L = D.text(o.office_label || String.fromCharCode(65 + k));
      return `<figure class="ap">${X.imgSlot(o.placement_photo, '', 'ap-img')}<figcaption><b>${L}</b> · placement, day 1${when(o, true) ? ' · ' + when(o, true) : ''}</figcaption></figure>
              <figure class="ap">${X.imgSlot(o.later_photo, '', 'ap-img')}<figcaption><b>${L}</b> · day ${String(o.later_photo_day || '5').trim() === '3' ? '3' : '5'}${when(o, false) ? ' · ' + when(o, false) : ''}</figcaption></figure>`;
    }).join('');
    return `<div class="page rpt-ap">
      <div class="dd-sample-banner">Sample. Illustrative placeholders, not results.</div>
      ${X.header({ kicker: 'Campaign report · evidence', meta: `${D.text(r.campaign_id || '[CAMPAIGN ID]')} · ${show(r.brand_name, '[BRAND]')}` })}
      <div class="bd"><h2>Evidence: every photo</h2><p class="note">Two photos per office, as taken. No identifiable people. Cropped to fit; the original files are available on request.</p>
        <div class="apg">${cells}</div></div>
      ${X.footer(`Page 2 of the report for ${D.text(r.campaign_id || '[CAMPAIGN ID]')}`, `${X.brandName()} · report template v1.1`)}
    </div>`;
  };

  // ---- fit: the limitations paragraph, the ladder and the numbers never shrink ----
  R.fit = function (sheet, i) {
    const pg = sheet.querySelector('.page.rpt');
    if (!pg) return true;
    const all = (sel) => [...pg.querySelectorAll(sel)];
    let cmPt = 9, thumbIn = pg.querySelector('.evg.many') ? 0.56 : 0.78, lrPt = 9.5, tight = false;
    const set = () => {
      all('.cm').forEach((e) => { e.style.fontSize = cmPt + 'pt'; });
      all('.ev-img').forEach((e) => { e.style.height = thumbIn + 'in'; });
      all('.lr li, .rec p').forEach((e) => { e.style.fontSize = lrPt + 'pt'; });
      pg.classList.toggle('tight', tight);
    };
    set();
    const steps = [
      () => { if (thumbIn > 0.46) { thumbIn = Math.round((thumbIn - 0.04) * 100) / 100; set(); return true; } },
      () => { if (cmPt > 8) { cmPt -= 0.25; set(); return true; } },
      () => { if (!tight) { tight = true; set(); return true; } },
      () => { if (lrPt > 8.5) { lrPt -= 0.25; set(); return true; } },
      () => { if (thumbIn > 0.4) { thumbIn = Math.round((thumbIn - 0.02) * 100) / 100; set(); return true; } },
    ];
    const ok = X.fitPages(sheet, i, steps, 'The report');
    const lim = pg.querySelector('.lim-text');
    if (!lim || lim.textContent !== R.LIMITATIONS) D.error(i, 'The limitations paragraph is missing or changed. It is fixed text in system/dd-report.js.');
    sheet.dataset.fit = JSON.stringify({ comment_pt: cmPt, thumb_in: thumbIn, learned_pt: lrPt, tight, fits: ok });
    return ok;
  };

  // ---- the report's own styles (kept here so the proposal's mock page gets the same layout) ----
  R.CSS = `
  .rpt .bd { padding-top: .12in; }
  .rpt .rpt-title { display: flex; flex-direction: column; }
  .rpt h1.rt { font-size: 21pt; line-height: 1.05; }
  .rpt h1.rt .sku { font: 700 13pt/1.1 var(--dd-font-text); color: var(--dd-ink-soft); letter-spacing: 0; }
  .rpt .rpt-meta { margin: .04in 0 0; font: 600 9pt/1.3 var(--dd-font-text); color: var(--dd-ink-soft); }
  .rpt .sec + .sec { margin-top: .13in; }
  .rpt h2 { font-size: 10.5pt; margin-bottom: .04in; }
  .rpt .ladder { margin-top: .02in; }
  .rpt table.roster { font-size: 8.5pt; }
  .rpt table.roster td { padding: .03in .05in; }
  .rpt.tight table.roster td { padding: .018in .05in; }
  .rpt.tight .sec + .sec { margin-top: .09in; }
  .rpt .evg { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); column-gap: .1in; row-gap: .05in; }
  .rpt .ev-pair { display: grid; grid-template-columns: 1fr 1fr; gap: .04in; }
  .rpt .ev figure { min-width: 0; }
  .rpt .ev-img { width: 100%; height: .78in; font-size: 6pt; line-height: 1.15; }
  .rpt .ev .img-slot span { font-size: 6pt; }
  .rpt .ev figcaption { margin-top: .015in; font-size: 7pt; white-space: nowrap; }
  .rpt .evg + .note { margin-top: .03in; }
  .rpt .sv-stats { font-size: 9pt; line-height: 1.38; }
  .rpt .cms { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .14in; margin-top: .06in; }
  .rpt blockquote.cm { margin: 0; padding-left: .08in; border-left: 2px solid var(--dd-ink); font: 400 9pt/1.34 var(--dd-font-text); font-style: italic; color: var(--dd-ink); }
  .rpt .cms + .note { margin-top: .04in; }
  .rpt .eng { margin-top: .07in; font-size: 9pt; line-height: 1.38; }
  .rpt .lr-row { row-gap: 0; }
  .rpt .lr li { font-size: 9.5pt; }
  .rpt .rec { padding: .07in .1in; }
  .rpt .rec p { font-size: 9.5pt; line-height: 1.35; }
  .rpt .lim { border-top: 1px solid var(--dd-ink); padding-top: .05in; }
  .rpt .lim h3 { font-size: 8pt; margin: 0 0 .02in; }
  .rpt .lim-text { font-size: 7.5pt; line-height: 1.36; color: var(--dd-ink); }
  .rpt-ap .apg { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .1in .1in; margin-top: .1in; }
  .rpt-ap .ap-img { width: 100%; height: 1.25in; }
  .rpt-ap figcaption { font-size: 7.5pt; }
  `;
})();
