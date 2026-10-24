/*
  dd-dates.js: the campaign calendar rules from CONTRACTS.md section 3 (v1.1, 2026-10-24).
  Used by the proposal and the report to work out dates from the drop day, and by the tests.

  - Business days: Monday to Friday, not a US federal holiday in HOLIDAYS.
  - T is the drop day and day 1 of the window. T+n and T-n count business days.
    T+2 is "day 3", T+4 is "day 5" and closes the window. Report T+7, debrief T+10.
    The code-redemption check is T+30 CALENDAR days.
  - Drop days are Tuesday or Wednesday only.
  - Blackouts (no drop day, and no part of the window): 18 to 31 December; 18 to 31 August;
    the Monday-to-Friday week containing 4 July or its observed federal holiday.
  The holiday list covers 2026-11 to 2027-09 (CONTRACTS). Dates after HOLIDAYS_UNTIL warn.
*/
(function (root) {
  'use strict';
  const HOLIDAYS = ['2026-11-11', '2026-11-26', '2026-12-25', '2027-01-01', '2027-01-18', '2027-02-15',
    '2027-05-31', '2027-06-18', '2027-07-05', '2027-09-06'];
  const HOLIDAYS_FROM = '2026-10-01', HOLIDAYS_UNTIL = '2027-09-30';
  const DAY = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  const parse = (s) => { const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s || '').trim()); return m ? new Date(Date.UTC(+m[1], +m[2] - 1, +m[3])) : null; };
  const iso = (d) => d.toISOString().slice(0, 10);
  const fmt = (d) => `${DAY[d.getUTCDay()]} ${iso(d)}`;
  const addDays = (d, n) => new Date(d.getTime() + n * 86400000);
  const isWeekend = (d) => d.getUTCDay() === 0 || d.getUTCDay() === 6;
  const isHoliday = (d) => HOLIDAYS.includes(iso(d));
  const isBusinessDay = (d) => !isWeekend(d) && !isHoliday(d);

  // n business days after (n > 0) or before (n < 0) d.
  function addBD(d, n) {
    let x = d, step = n >= 0 ? 1 : -1, left = Math.abs(n);
    while (left > 0) { x = addDays(x, step); if (isBusinessDay(x)) left--; }
    return x;
  }

  function july4Week(year) {
    let obs = new Date(Date.UTC(year, 6, 4));
    if (obs.getUTCDay() === 6) obs = addDays(obs, -1); else if (obs.getUTCDay() === 0) obs = addDays(obs, 1);
    const mon = addDays(obs, -(obs.getUTCDay() - 1));
    return [mon, addDays(mon, 4)];
  }
  // Returns the blackout name for a date, or ''.
  function blackout(d) {
    const m = d.getUTCMonth(), day = d.getUTCDate();
    if (m === 11 && day >= 18) return 'last two weeks of December (18 to 31 December)';
    if (m === 7 && day >= 18) return 'last two weeks of August (18 to 31 August)';
    const [a, b] = july4Week(d.getUTCFullYear());
    if (d >= a && d <= b) return `the week of 4 July (${iso(a)} to ${iso(b)})`;
    return '';
  }

  // Everything the documents need from one drop day. Returns { ok, errors[], warnings[], dates{} }.
  function campaign(dropIso) {
    const T = parse(dropIso);
    const out = { ok: false, errors: [], warnings: [], dates: {} };
    if (!T) { out.errors.push(`Drop date "${dropIso}" is not a date in the form YYYY-MM-DD.`); return out; }
    if (![2, 3].includes(T.getUTCDay())) out.errors.push(`Drop date ${fmt(T)} is not a Tuesday or Wednesday.`);
    if (isHoliday(T)) out.errors.push(`Drop date ${fmt(T)} is a federal holiday.`);
    const win = [T, addBD(T, 4)];
    for (let x = win[0]; x <= win[1]; x = addDays(x, 1)) {
      const b = blackout(x);
      if (b) { out.errors.push(`The five-day window (${iso(win[0])} to ${iso(win[1])}) overlaps a blackout: ${b}.`); break; }
    }
    if (iso(T) < HOLIDAYS_FROM || iso(addBD(T, 10)) > HOLIDAYS_UNTIL) out.warnings.push(`The holiday list in system/dd-dates.js covers ${HOLIDAYS_FROM} to ${HOLIDAYS_UNTIL}; add the federal holidays for these dates.`);
    const d = out.dates;
    d.ship_by = addBD(T, -10); d.receive = addBD(T, -5); d.cards = addBD(T, -3); d.confirm = addBD(T, -1);
    d.drop = T; d.day3 = addBD(T, 2); d.close = addBD(T, 4); d.report = addBD(T, 7); d.debrief = addBD(T, 10);
    d.redemption = addDays(T, 30);
    out.ok = out.errors.length === 0;
    return out;
  }

  // A date field may hold a plain date ("2027-01-12") or a bracketed slot
  // ("[DROP DATE: Tue 2027-01-12]"). Returns { iso, slot } where slot = true for the bracketed form.
  function readDateField(v) {
    const s = String(v || '').trim();
    const m = /(\d{4}-\d{2}-\d{2})/.exec(s);
    return { iso: m ? m[1] : '', slot: /^\[/.test(s) };
  }

  const api = { HOLIDAYS, HOLIDAYS_UNTIL, parse, iso, fmt, addDays, addBD, isBusinessDay, blackout, campaign, readDateField, july4Week };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.DDDates = api;
})(typeof window !== 'undefined' ? window : this);
