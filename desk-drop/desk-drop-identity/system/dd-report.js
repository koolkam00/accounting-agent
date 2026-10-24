/*
  dd-report.js: the one-page campaign report (v1.3, 2026-10-24; review round 2: photo dates are
  printed only where recorded, and a late office's photo is never captioned "day 1"). Load after dd-template.js,
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
  R.LIMITATIONS = 'Each number is a separate step, counted as stated. ' +
    'Delivered: our count at handoff. Placed: units visible in the placement photo; an office may hold some back for later. ' +
    'Depleted: from photos or the pantry owner\'s count by day 5; one person may take several, and sharing and disposal are invisible. ' +
    'Tuesday headcount: a range the office reports; not everyone visits the pantry. ' +
    'Survey responses: anonymous and self-selected, from small samples, so one answer can move a share by several points. ' +
    'A QR scan is curiosity, not intent. Code redemptions: reported by the brand; some of those people would have bought anyway. ' +
    'Retailer sales, where shown, are confounded by everything else that happened that month and are suggestive only. ' +
    'Incremental purchases were not measured, so this report does not show whether the campaign caused any sale.';

  const BANDS = { '40-75': '40 to 75', '76-150': '76 to 150', '151-250': '151 to 250', '251-500': '251 to 500', 'under-40': 'under 40', 'over-500': 'over 500', 'unknown': 'unknown' };
  R.BAND_OPTIONS = [['[HEADCOUNT BAND]', 'choose'], ['40-75', '40 to 75'], ['76-150', '76 to 150'], ['151-250', '151 to 250'], ['under-40', 'under 40'], ['251-500', '251 to 500'], ['unknown', 'unknown']];
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

  // A recorded photo date (YYYY-MM-DD), or null when empty or not a date. Never computed.
  const photoDate = (v) => { const t = String(v == null ? '' : v).trim(); return ph(t) ? null : Dt.parse(t); };
  // Caption parts for one office's photos. A date is printed only where it was recorded; the
  // placement photo of an office placed late is never called "day 1".
  function captions(o, d) {
    const late = String(o.placed_within_1bd || '').trim() === 'N';
    const pd = photoDate(o.placement_photo_date), ld = photoDate(o.later_photo_date);
    const pk = d.ok && pd ? Dt.dayOf(d.d1, pd) : null, lk = d.ok && ld ? Dt.dayOf(d.d1, ld) : null;
    const lday = lk != null ? lk : (String(o.later_photo_day || '5').trim() === '3' ? 3 : 5);
    return {
      late,
      // page 1, short: "A · day 2" with a recorded date; "A · placed" (or "placed*" when late) without
      placeShort: pk != null ? `day ${pk}${late ? '*' : ''}` : `placed${late ? '*' : ''}`,
      laterShort: `day ${lday}`,
      // page 2, full
      placeLong: pd ? `placement photo · ${Dt.fmt(pd)}${pk != null ? ` (day ${pk})` : ''}` : `placement photo · ${late ? 'placed after the first business day' : 'placed within one business day'}; date not recorded`,
      laterLong: ld ? `later photo · ${Dt.fmt(ld)}${lk != null ? ` (day ${lk})` : ''}` : `later photo · day ${lday}; date not recorded`
    };
  }
  R.captions = captions;

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
      const p1 = String(o.placed_within_1bd == null ? '' : o.placed_within_1bd).trim();
      if (!ph(p1) && !/^[YN]$/.test(p1)) D.error(i, `${L}: "placed within one business day" must be Y or N.`);
      if (ph(p1)) D.placeholder(i, `${L}: placed within one business day`);
      for (const [key, what] of [['placement_photo', 'placement photo'], ['later_photo', 'later photo']]) {
        const v = String(o[key] == null ? '' : o[key]).trim();
        if (ph(v)) D.placeholder(i, `${L}: ${what}`);
        else if (!v) D.warn(i, `${L}: no ${what}. The report says "No photo received". Attach it if you have it.`);
      }
      // photo dates (optional): printed only when recorded, and checked against the roster
      const dd = dates(r);
      const pd = photoDate(o.placement_photo_date), ld = photoDate(o.later_photo_date);
      for (const [v, what] of [[o.placement_photo_date, 'placement photo date'], [o.later_photo_date, 'later photo date']]) {
        const t = String(v == null ? '' : v).trim();
        if (t && ph(t)) D.placeholder(i, `${L}: ${what}`);
        else if (t && !Dt.parse(t)) D.error(i, `${L}: ${what} "${t}" must be a date in the form YYYY-MM-DD, or empty if you do not know it.`);
      }
      if (dd.ok && pd) {
        const T = dd.d1, T1 = Dt.addBD(T, 1);
        if (pd < T) D.error(i, `${L}: the placement photo date ${Dt.fmt(pd)} is before the drop date ${Dt.fmt(T)}.`);
        else if (p1 === 'Y' && pd > T1) D.error(i, `${L}: the placement photo is dated ${Dt.fmt(pd)}, after the first business day (${Dt.fmt(T1)}), but "placed within one business day" is Y. Fix one of them.`);
        else if (p1 === 'N' && pd <= T1) D.error(i, `${L}: the placement photo is dated ${Dt.fmt(pd)}, within one business day, but "placed within one business day" is N. Fix one of them.`);
      }
      if (dd.ok && ld) {
        if (pd && ld < pd) D.error(i, `${L}: the later photo date ${Dt.fmt(ld)} is before the placement photo date ${Dt.fmt(pd)}.`);
        else if (ld < dd.d1) D.error(i, `${L}: the later photo date ${Dt.fmt(ld)} is before the drop date.`);
        const k = Dt.dayOf(dd.d1, ld), want = String(o.later_photo_day || '5').trim() === '3' ? 3 : 5;
        if (k != null && k !== want) D.warn(i, `${L}: the later photo is dated ${Dt.fmt(ld)}, which is day ${k}, but "Later photo taken on" says day ${want}. The caption prints the date and day ${k}.`);
        if (ld > dd.day5) D.warn(i, `${L}: the later photo is dated ${Dt.fmt(ld)}, after the window closed (${Dt.fmt(dd.day5)}). Say so in "What we learned" if it matters.`);
      }
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
    X.checkClaims(i, '"What we learned"', r.learned, r);
    X.checkClaims(i, '"Recommendation"', r.recommendation, r);
    X.checkClaims(i, '"Retailer velocity"', r.retailer_velocity, r);
    const d = dates(r);
    if (d.ok) { d.cal.errors.forEach((m) => D.error(i, m)); d.cal.warnings.forEach((m) => D.warn(i, m)); }
  };

  // A photo value: a picture, "[PHOTO]" (not attached yet: the template hint), or empty
  // (the office sent none: reported as "No photo received", never hidden).
  function photo(v, cls) {
    const s = String(v == null ? '' : v).trim();
    if (!s) return `<div class="img-slot none ${cls}"><span><b>No photo received</b></span></div>`;
    return X.imgSlot(s, '', cls);
  }
  R.photo = photo;

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
    const known1bd = rows.filter((o) => /^[YN]$/.test(String(o.placed_within_1bd || '').trim()) && n(o.units_placed) != null).length;
    // Gate 2 is unit-based: units placed within one business day over units delivered (handoff)
    const tPl1 = known1bd === rows.length && rows.length ? rows.reduce((a, o) => a + (String(o.placed_within_1bd).trim() === 'Y' ? n(o.units_placed) : 0), 0) : null;
    const respKnown = rows.every((o) => n(o.survey_responses) != null);
    const resp5 = rows.filter((o) => n(o.survey_responses) != null && n(o.survey_responses) >= 5).length;
    const redeem = String(r.code_redemptions_to_date == null ? '' : r.code_redemptions_to_date).trim();
    const asOf = r.code_redemptions_as_of ? D.text(r.code_redemptions_as_of) : (d.ok ? d.report : '<mark class="dd-ph">[DATE]</mark>');

    const rung = (name, value, hint, off) => `<div class="rung${off ? ' off' : ''}"><span class="rn">${name}</span><span class="rv">${value}</span><span class="rh">${hint}</span></div>`;
    const ladder = `<div class="ladder">
      ${rung('Delivered', totalOr(tDel), tTop ? `At handoff. Plus ${tTop} day-3 top-ups from reserve.` : 'Counted at handoff.')}
      ${rung('Placed', totalOr(tPl), tPl1 != null && tDel ? `${tPl1} of ${tDel} units (${pct(tPl1, tDel)}%) within one business day.` : `<mark class="dd-ph">[N]</mark> of ${totalOr(tDel)} units within one business day.`)}
      ${rung('Depleted', totalOr(tDep), onShelf ? `Gone by day 5: ${pct(tDep, onShelf) == null ? '[N]' : pct(tDep, onShelf) + '%'} of ${onShelf} on the shelf.` : 'Gone by day 5.')}
      ${rung('Responded', totalOr(tResp), respKnown && rows.length ? `${resp5} of ${rows.length} offices reached five.` : `<mark class="dd-ph">[N]</mark> of ${rows.length} offices reached five.`)}
      ${rung('Scanned', totalOr(tScan), 'By office in the roster.')}
      ${rung('Purchased', redeem ? show(redeem) : '<mark class="dd-ph">[N]</mark>', `Code redemptions, per the brand, to ${asOf}.`)}
      ${rung('Incremental', '<span class="rv-off">Not measured</span>', 'See limitations.', true)}
    </div>`;

    const cell = (o, key, dflt) => { const s = String(o[key] == null ? '' : o[key]).trim(); return s ? D.text(s) : (dflt != null ? dflt : '<mark class="dd-ph">[N]</mark>'); };
    const body = rows.map((o, k) => `<tr>
        <td><b>${label(o, k)}</b></td><td>${cell(o, 'industry', '<mark class="dd-ph">[INDUSTRY]</mark>')}</td><td class="${o.headcount_band && !ph(o.headcount_band) ? 'nowrap' : 'ph-wrap'}">${o.headcount_band ? D.text(band(o.headcount_band)) : '<mark class="dd-ph">[HEADCOUNT BAND]</mark>'}</td>
        <td class="r num">${cell(o, 'units_delivered')}</td>
        <td class="r num">${String(o.placed_within_1bd || '').trim() === 'N' ? '<span class="late">*</span>' : ''}${cell(o, 'units_placed')}</td>
        <td class="r num">${cell(o, 'units_topped_up', '0')}</td>
        <td class="r num">${cell(o, 'units_depleted_day5')}</td>
        <td class="r num">${cell(o, 'survey_responses')}</td>
        <td class="r num">${cell(o, 'qr_scans')}</td></tr>`).join('');
    const roster = `<table class="t roster"><colgroup><col style="width:.44in"><col><col style="width:.8in"><col span="6" style="width:.62in"></colgroup>
      <thead><tr><th>Office</th><th>Industry</th><th>Tuesday<br>headcount</th><th class="r">Delivered</th><th class="r">Placed</th><th class="r">Topped<br>up</th><th class="r">Depleted<br>by day 5</th><th class="r">Responses</th><th class="r">Scans</th></tr></thead>
      <tbody>${body}<tr class="total"><td colspan="3">All ${rows.length} offices${late ? `<span class="late-note"> · * placed after the first business day: ${late} of ${rows.length}</span>` : ''}</td><td class="r num">${totalOr(tDel)}</td><td class="r num">${totalOr(tPl)}</td><td class="r num">${totalOr(tTop)}</td><td class="r num">${totalOr(tDep)}</td><td class="r num">${totalOr(tResp)}</td><td class="r num">${totalOr(tScan)}</td></tr></tbody></table>
`;

    const many = rows.length > 5;
    const cap = (o) => captions(o, d);
    // up to five offices: a pair per office. Six or more: a strip, one column per office,
    // the placement photo on the top row and the later photo below, so ten or twelve offices fit.
    // v1.3: no caption says "day 1" unless a recorded photo date says so (review round 2, R2-02).
    const thumbs = !many ? rows.map((o, k) => `<div class="ev">
        <div class="ev-pair">
          <figure>${photo(mock ? '[PHOTO]' : o.placement_photo, 'ev-img')}<figcaption>${label(o, k)} · ${cap(o).placeShort}</figcaption></figure>
          <figure>${photo(mock ? '[PHOTO]' : o.later_photo, 'ev-img')}<figcaption>${label(o, k)} · ${cap(o).laterShort}</figcaption></figure>
        </div></div>`).join('')
      : `<span class="evs-l">Placement<br><i>the pantry</i></span>${rows.map((o, k) => `<figure class="evs-c">${photo(mock ? '[PHOTO]' : o.placement_photo, 'ev-img')}<span class="evs-tag">${label(o, k)}${/^day/.test(cap(o).placeShort) ? ' · ' + cap(o).placeShort : (cap(o).late ? '*' : '')}</span></figure>`).join('')}
         <span class="evs-l evs-later">Day 3 or 5<br><i>card and product</i></span>${rows.map((o, k) => `<figure class="evs-c evs-later">${photo(mock ? '[PHOTO]' : o.later_photo, 'ev-img')}<span class="evs-tag">${label(o, k)} · ${cap(o).laterShort}</span></figure>`).join('')}`;
    const anyPhoto = !mock && rows.some((o) => D.imgSrc(o.placement_photo) || D.imgSrc(o.later_photo));
    const got = (key) => rows.filter((o) => D.imgSrc(o[key])).length;
    const pending = !mock && rows.some((o) => ph(o.placement_photo) || ph(o.later_photo));
    const compliance = mock ? `Photos received: placement ${rows.length} of ${rows.length}, later ${rows.length} of ${rows.length}.` : pending ? `Photos received: placement <mark class="dd-ph">[N]</mark> of ${rows.length}, later <mark class="dd-ph">[N]</mark> of ${rows.length}.`
      : `Photos received: placement ${got('placement_photo')} of ${rows.length}, later ${got('later_photo')} of ${rows.length}.`;
    const evidence = `<p class="ev-head"><b class="runin">Evidence: two photos per office</b><span class="note ev-note">${compliance} No identifiable people.<span class="ev-later-note"> The later photos are on page 2.</span>${anyPhoto ? ' Every photo, larger, is on page 2.' : ''}</span><span class="note ev-moved-note">${compliance} All of them are on page 2.</span></p>
      <div class="evg ${many ? 'many' : 'few'}"${many ? ` style="grid-template-columns:.62in repeat(${rows.length}, minmax(0, 1fr))"` : ''}>${thumbs}</div>`;

    // survey
    const ry = n(r.survey_buy_yes), rm = n(r.survey_buy_maybe), rno = n(r.survey_buy_no);
    const buyN = [ry, rm, rno].every((x) => x != null) ? ry + rm + rno : null;
    const share = (a, b) => (a == null || b == null) ? '' : ` (${pct(a, b)}%)`;
    const ty = n(r.survey_tried_yes);
    const nos = [['didn\'t see it', 'tried_no_didnt_see'], ['not for me', 'tried_no_not_for_me'], ['gone by the time I looked', 'tried_no_gone']];
    const noLine = nos.some(([, k]) => String(r[k] || '').trim()) ? ` · Did not try: ${nos.map(([t, k]) => `${t} ${show(r[k])}`).join(', ')}` : '';
    const stats = `<p class="sv-stats"><b class="runin">Survey</b> <b>Responses ${totalOr(tResp)}</b> · Tried it ${show(r.survey_tried_yes)} of ${totalOr(tResp)}${share(ty, tResp)}
      · Average rating ${show(r.survey_rating_avg, '[N.N]')} of 5 (${show(r.survey_rating_n)} ratings)
      · Would buy: yes ${show(r.survey_buy_yes)}${share(ry, buyN)}, maybe ${show(r.survey_buy_maybe)}${share(rm, buyN)}, no ${show(r.survey_buy_no)}${share(rno, buyN)}${buyN != null && tResp != null && buyN < tResp ? ` of ${buyN} who answered` : ''}${noLine}</p>`;
    // mock page: grey examples, not the yellow "unfinished" mark (that means the founder must act)
    const ex = (t) => `<span class="dd-ex">${D.escape(t)}</span>`;
    const q = (k, j) => `<blockquote class="cm">${r[k] && String(r[k]).trim() ? '“' + D.text(String(r[k]).trim()) + '”' : mock ? ex(`Comment ${j}: a real comment from the survey, copied word for word.`) : `<mark class="dd-ph">[VERBATIM COMMENT ${j}]</mark>`}</blockquote>`;
    const comments = `<div class="cms">${q('comment_1', 1)}${q('comment_2', 2)}${q('comment_3', 3)}</div>
      <p class="note">Three ${r.comments_total ? `of ${D.text(r.comments_total)} ` : ''}comments, copied word for word; any name removed. Comments are not linked to an office.</p>`;

    const engagement = `<p class="eng"><b>Engagement:</b> ${totalOr(tScan)} QR scans across ${rows.length} offices · ${redeem ? show(redeem) : '<mark class="dd-ph">[N]</mark>'} code redemptions to ${asOf}, per the brand${d.ok ? ` (day-30 check ${d.redemption})` : ''}.${String(r.retailer_velocity || '').trim() ? `<br><b>Retailer velocity, the brand's own data, suggestive only:</b> ${D.text(r.retailer_velocity)}` : ''}</p>`;

    const learned = X.items(r.learned);
    const learnedHTML = `<ul class="plain lr">${learned.length ? learned.map((x) => `<li>${D.text(x)}</li>`).join('')
      : mock ? ['What we learned from the drop, in plain words.', 'Anything you might change: flavor, pack size, card copy.', 'What the offices told us about timing and supply.'].map((x) => `<li>${ex(x)}</li>`).join('')
      : ['[WHAT WE LEARNED 1]', '[WHAT WE LEARNED 2]', '[WHAT WE LEARNED 3]'].map((x) => `<li>${D.text(x)}</li>`).join('')}</ul>`;

    const tier = String(r.tier || '').trim();
    const meta = [
      D.text(r.cluster || 'Flatiron, NoMad and Union Square'),
      `Drop ${d.drop}`,
      d.ok ? (d.slot ? `Window <mark class="dd-ph">[WINDOW: ${Dt.fmt(d.d1)} to ${Dt.fmt(d.day5)}]</mark>` : `Window ${Dt.fmt(d.d1)} to ${Dt.fmt(d.day5)}`) : 'Window <mark class="dd-ph">[WINDOW]</mark>',
    ].join(' · ');
    const tierText = `${tier === 'founding' ? 'Founding' : tier === 'standard' ? 'Standard' : '<mark class="dd-ph">[TIER]</mark>'}, ${rows.length} offices`;
    const reportDate = r.report_date ? D.text(r.report_date) : (d.ok ? d.report : '<mark class="dd-ph">[REPORT DATE]</mark>');

    return `<div class="page rpt${mock ? ' mock' : ''}">
      ${mock ? `<div class="mock-band">Mock report page <span>·</span> Illustrative placeholders, not results</div><div class="mock-side">Illustrative placeholders, not results</div>` : '<div class="dd-sample-banner">Sample. Illustrative placeholders, not results.</div>'}
      ${X.header({ cap: 0.21, kicker: 'Campaign report', meta: `${mock && !r.campaign_id ? '' : D.text(r.campaign_id || '[CAMPAIGN ID]') + ' · '}${tierText} · report ${reportDate}` })}
      <div class="bd">
        <div class="rpt-title"><h1 class="title rt">${show(r.brand_name, '[BRAND]')} <span class="sku">· ${show(r.product_sku, '[SKU]')}</span></h1>
          <p class="rpt-meta">${meta}</p></div>
        <section class="sec">${ladder}</section>
        <section class="sec"><h2>Roster</h2>${roster}</section>
        <section class="sec ev-sec">${evidence}</section>
        <section class="sec sv">${stats}${comments}${engagement}</section>
        <section class="sec lr-row"><div class="lr-col"><h2>What we learned</h2>${learnedHTML}</div>
          <div class="box rec"><h2>Recommendation</h2><p>${mock && !String(r.recommendation || '').trim() ? ex('Renew into which offices, adjust what, or stop, with the reason.') : show(r.recommendation, '[RENEW INTO WHICH OFFICES, ADJUST WHAT, OR STOP]')}</p></div>
        </section>
        <section class="sec lim"><p class="lim-p"><b class="lim-h">Limitations.</b> <span class="lim-text">${D.escape(R.LIMITATIONS)}</span></p></section>
      </div>
      ${X.footer(`Prepared by ${D.text(r.prepared_by || D.contact('FOUNDER_NAME'))} · ${X.contact(' · ', ['PHONE', 'EMAIL'])}`, `${X.brandName()} · report template v1.3`)}
    </div>`;
  };

  // ---- page 2: every photo, larger ----
  R.appendix = function (r) {
    const rows = Array.isArray(r.offices) ? r.offices : [];
    if (!rows.some((o) => D.imgSrc(o.placement_photo) || D.imgSrc(o.later_photo))) return '';
    const d = dates(r);
    // v1.3 (review round 2, R2-02): a date is printed only when the photo's date was recorded.
    // It is never worked out from the drop date, and a late office is never captioned "day 1".
    const cells = rows.map((o, k) => {
      const L = D.text(o.office_label || String.fromCharCode(65 + k));
      const c = captions(o, d);
      return `<figure class="ap">${photo(o.placement_photo, 'ap-img')}<figcaption><b>${L}</b> · ${c.placeLong}</figcaption></figure>
              <figure class="ap">${photo(o.later_photo, 'ap-img')}<figcaption><b>${L}</b> · ${c.laterLong}</figcaption></figure>`;
    }).join('');
    return `<div class="page rpt-ap">
      <div class="dd-sample-banner">Sample. Illustrative placeholders, not results.</div>
      ${X.header({ kicker: 'Campaign report · evidence', meta: `${D.text(r.campaign_id || '[CAMPAIGN ID]')} · ${show(r.brand_name, '[BRAND]')}` })}
      <div class="bd"><h2>Evidence: every photo</h2><p class="note">Two photos per office. Dates are shown where recorded. No identifiable people. Cropped to fit; the original files are available on request.</p>
        <div class="apg">${cells}</div></div>
      ${X.footer(`Page 2 of the report for ${D.text(r.campaign_id || '[CAMPAIGN ID]')}`, `${X.brandName()} · report template v1.3`)}
    </div>`;
  };

  // ---- fit: the limitations paragraph, the ladder and the numbers never shrink ----
  R.fit = function (sheet, i, page) {
    const pg = page || sheet.querySelector('.page.rpt');
    if (!pg) return true;
    const all = (sel) => [...pg.querySelectorAll(sel)];
    const many = !!pg.querySelector('.evg.many');
    const canMove = many && !pg.classList.contains('mock') && !!sheet.querySelector('.page.rpt-ap');
    // thumbnails: a few offices get pairs 0.78 in tall (floor 0.5); a strip starts at 0.5 in (floor 0.38)
    const T0 = many ? 0.5 : 0.78, TMIN = many ? 0.38 : 0.5;
    let cmPt = 8.75, thumbIn = T0, lrPt = 9.5, tight = false, laterMoved = false, moved = false;
    const set = () => {
      all('.cm').forEach((e) => { e.style.fontSize = cmPt + 'pt'; });
      all('.ev-img').forEach((e) => { e.style.height = thumbIn + 'in'; });
      all('.lr li, .rec p').forEach((e) => { e.style.fontSize = lrPt + 'pt'; });
      pg.classList.toggle('tight', tight);
      pg.classList.toggle('ev-later-moved', laterMoved && !moved);
      pg.classList.toggle('ev-moved', moved);
    };
    set();
    // Give-way order, stated in the usage guide and the documents spec. Never touched: the
    // ladder, the numbers, the comments' words, the limitations paragraph.
    const steps = [
      () => { if (thumbIn > TMIN + 0.001) { thumbIn = Math.round((thumbIn - 0.02) * 100) / 100; set(); return true; } },
      () => { if (cmPt > 8.25) { cmPt -= 0.25; set(); return true; } },
      () => { if (!tight) { tight = true; set(); return true; } },
      () => { if (lrPt > 8.5) { lrPt -= 0.25; set(); return true; } },
      () => { if (canMove && !laterMoved) { laterMoved = true; set(); return true; } },   // the day-1 strip stays
      () => { if (cmPt > 8) { cmPt -= 0.25; set(); return true; } },
      () => { if (canMove && !moved) { moved = true; set(); return true; } },             // last resort
    ];
    const ok = X.fitPages(sheet, i, steps, pg.classList.contains('mock') ? 'The mock report page' : 'The report', [pg]);
    if (moved) D.warn(i, 'To keep the comments whole, every photo thumbnail moved to page 2; page 1 keeps the count of photos received. Shorten "What we learned" or the recommendation to bring the placement photos back.');
    else if (laterMoved) D.warn(i, 'To keep the comments whole, the later photos moved to page 2; page 1 keeps every placement photo.');
    // page 2 (evidence): the photos shrink to fit, 1.25 in down to 0.8 in tall; never off the page
    const ap = sheet.querySelector('.page.rpt-ap');
    let apIn = 1.25;
    if (ap) {
      const setAp = () => ap.querySelectorAll('.ap-img').forEach((e) => { e.style.height = apIn + 'in'; });
      setAp();
      X.fitPages(sheet, i, [() => { if (apIn > 0.8 + 0.001) { apIn = Math.round((apIn - 0.05) * 100) / 100; setAp(); return true; } }], 'The evidence page', [ap]);
    }
    const lim = pg.querySelector('.lim-text');
    if (!lim || lim.textContent !== R.LIMITATIONS) D.error(i, 'The limitations paragraph is missing or changed. It is fixed text in system/dd-report.js.');
    if (!pg.classList.contains('mock')) sheet.dataset.fit = JSON.stringify({ comment_pt: cmPt, thumb_in: thumbIn, learned_pt: lrPt, tight, later_photos_on_page_2: laterMoved || moved, thumbnails_on_page_2: moved, evidence_photo_in: ap ? apIn : null, fits: ok });
    return ok;
  };

  // ---- the report's own styles (kept here so the proposal's mock page gets the same layout) ----
  R.CSS = `
  .rpt .bd { padding-top: .12in; }
  .rpt .rpt-title { display: flex; flex-direction: column; }
  .rpt h1.rt { font-size: 19pt; line-height: 1.05; }
  .rpt h1.rt .sku { font: 700 13pt/1.1 var(--dd-font-text); color: var(--dd-ink-soft); letter-spacing: 0; }
  .rpt .rpt-meta { margin: .03in 0 0; font: 600 9pt/1.3 var(--dd-font-text); color: var(--dd-ink-soft); }
  .rpt .rpt-meta mark { white-space: nowrap; }
  .rpt .rung { padding: .04in .06in .05in; }
  .rpt .rung .rv { font-size: 14pt; margin-top: .02in; }
  .rpt .rung .rh { margin-top: .025in; line-height: 1.22; }
  .rpt .sec + .sec { margin-top: .13in; }
  .rpt h2 { font-size: 10pt; margin-bottom: .03in; }
  .rpt .ladder { margin-top: .02in; }
  .rpt .rung .rv-off { font-size: 11pt; line-height: 1.1; }
  .doc .img-slot.none { background: #fff; border-style: solid; border-color: var(--dd-stone); }
  .rpt table.roster { font-size: 8.5pt; line-height: 1.15; table-layout: fixed; }
  .rpt table.roster .late-note { font-weight: 400; font-size: 7.5pt; color: var(--dd-ink-soft); white-space: nowrap; }
  .rpt table.roster th { font-size: 7pt; line-height: 1.15; padding: .02in .04in .03in; }
  .rpt table.roster td { padding: .025in .04in; overflow-wrap: anywhere; }
  .rpt table.roster td.ph-wrap { overflow-wrap: normal; }   /* "[HEADCOUNT BAND]" breaks at the space, never mid-word */
  .rpt.tight table.roster td { padding: .008in .04in; line-height: 1.08; }
  .rpt table.roster .late { font-weight: 700; margin-right: .02in; }
  .rpt.tight .sec + .sec { margin-top: .09in; }
  .rpt .evg { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); column-gap: .1in; row-gap: .05in; }
  .rpt .evg.many { column-gap: .05in; row-gap: .03in; align-items: center; }
  .rpt .evs-l { font: 700 7pt/1.15 var(--dd-font-text); color: var(--dd-ink); }
  .rpt .evs-l i { font-style: normal; font-weight: 400; color: var(--dd-ink-soft); }
  .rpt .evs-h { font: 700 8pt/1 var(--dd-font-text); text-align: center; }
  .rpt .evs-c { min-width: 0; margin: 0; position: relative; }
  .rpt .evs-tag { position: absolute; left: 0; top: 0; background: var(--dd-ink); color: #fff; font: 700 6.5pt/1 var(--dd-font-text); padding: .012in .025in; white-space: nowrap; }
  .rpt .evg.many .img-slot { padding: .1in .02in .02in; }
  .rpt .evg.many .img-slot span { font-size: 5.5pt; }
  .rpt.ev-later-moved .evs-later { display: none; }
  .rpt .ev-later-note { display: none; }
  .rpt.ev-later-moved .ev-later-note { display: inline; }
  .rpt .ev-pair { display: grid; grid-template-columns: 1fr 1fr; gap: .04in; }
  .rpt .ev figure { min-width: 0; }
  .rpt .ev-img { width: 100%; height: .78in; font-size: 6pt; line-height: 1.15; }
  .rpt .ev .img-slot span { font-size: 6pt; }
  .rpt .ev figcaption { margin-top: .015in; font-size: 7pt; white-space: nowrap; }
  .rpt .runin { font: 800 10pt/1.15 var(--dd-font-display); font-variation-settings: "opsz" 96; color: var(--dd-ink); margin-right: .06in; }
  .rpt .ev-head { margin: 0 0 .04in; display: flex; align-items: baseline; gap: .1in; }
  .rpt .ev-head .runin { flex: none; }
  .rpt .ev-head .note { font-size: 7.5pt; line-height: 1.28; }
  .rpt .sv-stats { font-size: 9pt; line-height: 1.38; }
  .rpt .cms { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .1in; margin-top: .05in; }
  .rpt blockquote.cm { margin: 0; padding-left: .08in; border-left: 2px solid var(--dd-ink); font: 400 8.75pt/1.33 var(--dd-font-text); color: var(--dd-ink); }
  .rpt .ev-moved-note { display: none; }
  .rpt.ev-moved .evg, .rpt.ev-moved .ev-note { display: none; }
  .rpt.ev-moved .ev-head { margin: 0; }
  .rpt.ev-moved .ev-moved-note { display: block; font-size: 8.5pt; color: var(--dd-ink); }
  .rpt .cms + .note { margin-top: .04in; }
  .rpt .eng { margin-top: .07in; font-size: 9pt; line-height: 1.38; }
  .rpt .lr-row { display: grid; grid-template-columns: minmax(0, 1.65fr) minmax(0, 1fr); column-gap: .2in; align-items: start; }
  .rpt .lr li { font-size: 9.5pt; }
  .rpt .rec { padding: .07in .1in; }
  .rpt .rec p { font-size: 9.5pt; line-height: 1.35; }
  .rpt .lim { border-top: 1px solid var(--dd-ink); padding-top: .05in; }
  .rpt .lim h3 { font-size: 8pt; margin: 0 0 .02in; }
  .rpt .lim-p, .rpt .lim-text { font-size: 7.5pt; line-height: 1.36; color: var(--dd-ink); }
  .rpt .lim-h { font-weight: 700; }


  .page.rpt { padding: .45in .6in .4in; }
  .page.rpt.mock { padding-top: .48in; }
  .rpt .hd { padding-bottom: .07in; }
  .rpt.tight .sec + .sec { margin-top: .06in; }
  .rpt .rec { margin-top: 0; }
  .rpt .rec h2 { margin: 0 0 .03in; }
  .rpt .eng { margin-top: .05in; font-size: 8.75pt; }
  .rpt .lr li::before { width: .4em; height: .4em; top: .52em; }
  .rpt .rung .rv-off { font-size: 9.5pt; white-space: nowrap; }
  .rpt-ap .apg { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .1in .1in; margin-top: .1in; }
  .rpt-ap .ap-img { width: 100%; height: 1.25in; }
  .rpt-ap figcaption { font-size: 7pt; line-height: 1.25; margin-top: .02in; }
  `;
})();
