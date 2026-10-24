#!/usr/bin/env python3
"""Fill, check and render the outreach messages.

Reads the message blocks in ../0*-*.md and ../1*-*.md (fenced ```message blocks),
the field rules (../03-personalization-fields.csv, implemented below), the
progress state (../04-slot-state.csv or a SAMPLE state), and a row.

Three commands (run from desk-drop/desk-drop-outreach/messages/):

  python3 _render/fill.py lint
      Fill every message with the SAMPLE rows and states, print every finding.

  python3 _render/fill.py examples
      Build examples/*.html from examples/SAMPLE-examples.json, then
      node _render/shoot.js turns them into 390 px PNGs.

  python3 _render/fill.py drafts --daily ../../clay-icp-tables/daily-view-offices.csv \
        --message office-discovery-1 --date 2026-11-09 --out drafts/2026-11-09
      Writes one paste-ready .txt per row (subject, body, signature). It never
      sends anything. It refuses a no-send day and any cold touch 1 before
      Mon 2026-11-09, writes no more cold first touches than
      ../sending/warmup-schedule.csv allows that day (--over-cap to override),
      and skips rows with do_not_contact = Y, an opt_out_date, A's
      hold_before_outreach = Y, a status other than queued (touch 1) /
      contacted (touches 2 and 3), and any message the state does not unlock.

No network access. Standard library only.
"""
import csv, datetime as dt, html, json, os, re, sys
sys.dont_write_bytecode = True   # no __pycache__ in the deliverable folder (review round 3, R3-11)

HERE = os.path.dirname(os.path.abspath(__file__))
MSG_DIR = os.path.dirname(HERE)                      # messages/
OUT_DIR = os.path.dirname(MSG_DIR)                   # desk-drop-outreach/
ROOT = os.path.dirname(OUT_DIR)                      # desk-drop/
BRAND_JSON = os.path.join(ROOT, 'desk-drop-identity', 'brand.json')

FOUNDER_PLACEHOLDERS = {'FOUNDER NAME', 'PHONE', 'EMAIL', 'POSTAL ADDRESS', 'WEBSITE', 'DOMAIN', 'LINKEDIN URL'}

# ---------------------------------------------------------------- calendar
HOLIDAYS = {dt.date.fromisoformat(d) for d in [
    '2026-11-11', '2026-11-26', '2026-12-25', '2027-01-01', '2027-01-18', '2027-02-15',
    '2027-05-31', '2027-06-18', '2027-07-05', '2027-09-06']}
NO_SEND = [(dt.date(2026, 11, 27), dt.date(2026, 11, 27)), (dt.date(2026, 12, 18), dt.date(2027, 1, 4))]
DOW = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def is_bd(d):
    return d.weekday() < 5 and d not in HOLIDAYS


def add_bd(d, n):
    x, k, step = d, 0, (1 if n >= 0 else -1)
    while k < abs(n):
        x += dt.timedelta(step)
        if is_bd(x):
            k += 1
    return x


def send_day(d):
    """Move a send date off non-business days and the no-send ranges."""
    while True:
        if not is_bd(d):
            d += dt.timedelta(1); continue
        moved = False
        for a, b in NO_SEND:
            if a <= d <= b:
                d = b + dt.timedelta(1); moved = True
        if not moved:
            return d


def in_blackout(d):
    if dt.date(d.year, 12, 18) <= d <= dt.date(d.year, 12, 31):
        return True
    if dt.date(d.year, 8, 18) <= d <= dt.date(d.year, 8, 31):
        return True
    j4 = dt.date(d.year, 7, 4)
    obs = j4 - dt.timedelta(1) if j4.weekday() == 5 else (j4 + dt.timedelta(1) if j4.weekday() == 6 else j4)
    mon = obs - dt.timedelta(obs.weekday())
    return mon <= d <= mon + dt.timedelta(4)


def drop_ok(d):
    if d.weekday() not in (1, 2) or in_blackout(d) or not is_bd(d):
        return False
    x = d
    for _ in range(4):
        x = add_bd(x, 1)
        if in_blackout(x):
            return False
    return True


def fmt(d):
    return f'{DOW[d.weekday()]} {d.isoformat()}'


# ---------------------------------------------------------------- inputs
def read_csv(p):
    with open(p, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_state(p):
    st = {}
    for r in read_csv(p):
        v = r['value']
        if r['kind'] == 'count':
            v = int(v) if str(v).strip() not in ('',) else None
        st[r['key']] = v
    return st


def brand_name():
    """The working name lives in desk-drop-identity/brand.json only. A missing or broken file is an error,
    never a silent fallback to an old name (review round 1, R1-19)."""
    try:
        return json.load(open(BRAND_JSON, encoding='utf-8'))['BRAND_NAME']
    except Exception as e:
        sys.exit(f'fill.py: cannot read BRAND_NAME from {BRAND_JSON} ({e}). Fix brand.json; no message is filled without it.')


def load_messages():
    msgs = {}
    for fn in sorted(os.listdir(MSG_DIR)):
        if not re.match(r'^\d\d-.*\.md$', fn):
            continue
        txt = open(os.path.join(MSG_DIR, fn), encoding='utf-8').read()
        for m in re.finditer(r'```message\n(.*?)\n```', txt, re.S):
            block = m.group(1)
            head, _, body = block.partition('\n---\n')
            meta = {}
            for line in head.splitlines():
                k, _, v = line.partition(':')
                meta[k.strip()] = v.strip()
            meta['file'] = fn
            meta['body'] = body
            msgs[meta['id']] = meta
    return msgs


def broker_block():
    p = os.path.join(ROOT, 'desk-drop-legal-pack', '11-coi-request-brand-product-liability.md')
    try:
        txt = open(p, encoding='utf-8').read()
        blk = txt.split('## Block to forward')[1].split('## Email 2')[0]
        lines = [re.sub(r'^> ?', '', l) for l in blk.splitlines()[1:] if l.startswith('>')]
        return re.sub(r'\*\*', '', '\n'.join(lines)).replace('\\$', '$').strip()
    except Exception:
        return None


def signature_block(state=None):
    """02 holds the signature twice: first as it reads before the name is decided (no business name),
    then with {BRAND_NAME} once name_decided = Y (review round 1, R1-02)."""
    txt = open(os.path.join(MSG_DIR, '02-commercial-footer.md'), encoding='utf-8').read()
    blocks = re.findall(r'```text\n(.*?)\n```', txt, re.S)
    decided = (state or {}).get('name_decided') == 'Y'
    return blocks[1] if decided else blocks[0]


# ---------------------------------------------------------------- markers
# \x01X opens a span of type X (F field, B fallback, S slot, P placeholder, D dropped note), \x02 closes it.
def mk(kind, text):
    return f'\x01{kind}{text}\x02'


def strip_marks(s):
    return re.sub(r'\x01[A-Z]|\x02', '', s)


ROLE_WORDS = {'team', 'office', 'info', 'hello', 'admin', 'hr', 'people', 'ops', 'contact', 'hi', 'there'}
SUFFIX_RE = re.compile(r',?\s+(inc\.?|llc|l\.l\.c\.|corp\.?|corporation|co\.|ltd\.?|pbc)$', re.I)
CATEGORY_LABEL = {
    'chips-crisps': 'chips and crisps', 'popcorn-puffs': 'popcorn and puffs', 'crackers-pretzels': 'crackers and pretzels',
    'bars': 'bars', 'cookies-baked': 'cookies and baked snacks', 'chocolate-candy': 'chocolate and candy',
    'nuts-seeds-trail': 'nuts, seeds and trail mix', 'meat-snacks': 'jerky and meat sticks', 'fruit-snacks': 'dried fruit and fruit snacks',
    'sparkling-soda': 'sparkling water and soda', 'tea-juice': 'tea and juice', 'coffee-rtd': 'ready-to-drink coffee',
    'other-snack': 'snack', 'other-drink': 'drink'}


def street_short(addr):
    if not addr or addr.strip().lower() in ('unknown', ''):
        return ''
    s = addr.split(',')[0].strip()
    s = re.sub(r'^\d+[A-Za-z\-]*\s+', '', s)
    rep = [(r'\bW\.?\b', 'West'), (r'\bE\.?\b', 'East'), (r'\bSt\.?$', 'Street'), (r'\bAve\.?\b', 'Avenue'),
           (r'\bPl\.?$', 'Place'), (r'\bSq\.?\b', 'Square'), (r'\bS\.?$', 'South')]
    for a, b in rep:
        s = re.sub(a, b, s)
    return s


ENUM_COLUMNS = {'email_status', 'nearest_retailer_grade', 'lease_status', 'status', 'channel', 'do_not_contact'}


def unknown_to_blank(row):
    """A field the Clay tables could not confirm reads 'unknown' or carries 'unverified, founder to confirm'
    (CONTRACTS section 2). Nothing like that is ever printed: treat it as blank, so its fallback is used."""
    out = {}
    for k, v in (row or {}).items():
        t = (v or '').strip()
        low = t.lower()
        if k in ENUM_COLUMNS:      # 'unverified' is a real value there (CONTRACTS 6.2 and section 4); keep it
            out[k] = t
            continue
        if (low == 'unknown' or low.startswith('unknown ') or low.startswith('unknown(') or low.startswith('unverified')
                or 'unverified, founder to confirm' in low or '(unverified' in low or low.startswith('none found')):
            t = ''
        out[k] = t
    return out


class Ctx:
    def __init__(self, row, state, side, stage, send_date, brand_row=None, slot_values=None):
        self.row, self.state, self.side, self.stage = unknown_to_blank(row), state, side, stage
        self.date = send_date
        self.brand_row = unknown_to_blank(brand_row)
        self.slot_values = slot_values or {}
        self.notes = []          # fallbacks and drops, for the annotations and the lint

    def val(self, k):
        return (self.row.get(k) or '').strip()


def f_greeting(c):
    fn = c.val('first_name')
    if fn and fn.split()[-1].lower() not in ROLE_WORDS and fn.lower() not in ROLE_WORDS:
        return 'Hi ' + mk('F', fn) + ','
    c.notes.append('greeting: no first name, "Hello," used')
    return mk('B', 'Hello,')


def f_company(c):
    v = SUFFIX_RE.sub('', c.val('company'))
    if v:
        return mk('F', v)
    fb = 'your office' if c.side == 'office' else 'your brand'
    c.notes.append(f'company: blank, "{fb}" used')
    return mk('B', fb)


def f_area(c):
    v = c.val('street_short') or street_short(c.val('street_address'))
    if v:
        return mk('F', v)
    c.notes.append('area: no street, the cluster name used')
    return mk('B', c.state['cluster_name'])


def f_product(c, row=None):
    row = row or c.row
    v = (row.get('product_short') or '').strip()
    if v:
        return mk('F', v)
    b = SUFFIX_RE.sub('', (row.get('company') or '').strip())
    if b:
        c.notes.append('product: no product name, the brand name used')
        return mk('B', b)
    c.notes.append('product: blank, "your product" used')
    return mk('B', 'your product')


def opt_why_now(c):
    hook, d = c.val('why_now_hook'), c.val('why_now_date')
    if not hook:
        c.notes.append('why_now_hook: blank, sentence left out'); return ''
    try:
        # a month-only date (YYYY-MM, allowed by CONTRACTS section 5) is read as the 1st: the oldest it can be
        age = (c.date - dt.date.fromisoformat(d[:10] if len(d) >= 10 else d[:7] + '-01')).days
    except Exception:
        c.notes.append('why_now_hook: no why_now_date, sentence left out'); return ''
    if age > 120 or age < 0:
        c.notes.append(f'why_now_hook: why_now_date {d} is {age} days before the send date (over 120), sentence left out')
        return ''
    return mk('F', hook)


def retailer_parts(row):
    v = (row.get('nearest_stocked_retailer') or '').strip()
    return v.split(',')[0].strip() if v else ''


def opt_retailer_line(c):
    grade = c.val('nearest_retailer_grade')
    r = retailer_parts(c.row)
    if not r or grade not in ('seen_on_shelf', 'store_selector', 'brand_claim'):
        c.notes.append(f'retailer_line: grade "{grade or "blank"}", sentence left out'); return ''
    near_d, near_s = ", near the offices I'm writing to.", ', a short walk from them.'
    selling = c.stage in ('selling',)
    p, R = f_product(c), mk('F', r)
    if grade == 'seen_on_shelf':
        s = f'I saw {p} on the shelf at {R}' + (near_s if selling else near_d)
    elif grade == 'store_selector':
        s = f"{R}'s store page lists {p}" + (near_s if selling else ", and that store is near the offices I'm writing to.")
    else:
        s = f'Your store locator lists {R}' + (near_s if selling else near_d)
    return s


def opt_retailer_for_office(c):
    br = c.brand_row
    grade = (br.get('nearest_retailer_grade') or '').strip()
    r = retailer_parts(br)
    if r and grade in ('seen_on_shelf', 'store_selector'):
        return ', and people can buy it at ' + mk('F', r)
    c.notes.append('retailer_for_office: no shelf or store-page evidence, clause left out')
    return ''


def f_category_phrase(c, row=None):
    row = row or c.row
    k = (row.get('category') or '').strip()
    if k in CATEGORY_LABEL:
        lab = CATEGORY_LABEL[k]
        art = 'an' if lab[0] in 'aeiou' else 'a'
        return mk('F', f'{art} {lab} brand')
    c.notes.append('category: blank, "an emerging brand" used')
    return mk('B', 'an emerging brand')


def f_category_short(c):
    k = c.val('category')
    if k in CATEGORY_LABEL:
        return mk('F', CATEGORY_LABEL[k])
    c.notes.append('category: blank, "brand in your category" wording used')
    return mk('B', 'brand in your category')


def f_category_only(c):
    k = c.val('category')
    if k in CATEGORY_LABEL:
        return mk('F', f'the only {CATEGORY_LABEL[k]} brand')
    c.notes.append('category: blank, "the only brand in your category" used')
    return mk('B', 'the only brand in your category')


def opt_from_city(c, row=None):
    row = row or c.row
    v = (row.get('hq_city') or '').strip()
    # A's table may annotate the city with its evidence: "Brooklyn (privacy policy: ...)". Print the place only.
    v = v.split(' (')[0].strip() if ' (' in v else v
    if v and 'unverified' not in (row.get('hq_city') or '').lower() and v.lower() != 'unknown' and re.fullmatch(r"[A-Za-z .,'\-]+", v):
        return ' from ' + mk('F', v)
    c.notes.append('from_city: unknown or unverified, left out')
    return ''


def f_call_note_hook_line(c):
    v = c.val('call_note_hook')
    if v:
        return 'Thanks again for today, and for the detail about ' + mk('F', v) + '.'
    c.notes.append('call_note_hook: blank, plain thanks used')
    return mk('B', 'Thanks again for the time today.')


def f_referrer_name(c):
    if c.val('referrer_ok_to_name').upper() == 'Y' and c.val('referrer_name'):
        return mk('F', c.val('referrer_name'))
    c.notes.append('referrer: not cleared to name, use the ordinary first touch')
    return mk('B', '[NOT CLEARED TO NAME]')


def f_brand_name(c):
    v = SUFFIX_RE.sub('', (c.brand_row.get('company') or '').strip())
    return mk('F', v) if v else mk('B', 'the brand')


FIELDS = {
    'greeting': f_greeting, 'company': f_company, 'area': f_area, 'product': f_product,
    'category_phrase': f_category_phrase, 'category_short': f_category_short, 'category_only_phrase': f_category_only,
    'call_note_hook_line': f_call_note_hook_line, 'referrer_name': f_referrer_name,
    'brand_name': f_brand_name, 'brand_category_phrase': lambda c: f_category_phrase(c, c.brand_row),
    'first_name_or_founder': lambda c: mk('F', c.val('first_name')) if c.val('first_name') else mk('B', 'the founder'),
    'referrer_first_name': lambda c: mk('F', c.val('referrer_name').split()[0]) if (c.val('referrer_name') and c.val('referrer_ok_to_name').upper() == 'Y') else mk('B', '[NOT CLEARED TO NAME]'),
}
OPTIONAL = {'why_now_hook': opt_why_now, 'retailer_line': opt_retailer_line,
            'retailer_for_office': opt_retailer_for_office,
            'from_city': lambda c: opt_from_city(c, c.row), 'brand_from_city': lambda c: opt_from_city(c, c.brand_row)}


# ---------------------------------------------------------------- slots
SLOT_SEEN = set()


def S(text):
    SLOT_SEEN.add(text)
    return mk('S', text)


def attachment_ready(st, key):
    """An attachment counts as ready only if it may be sent today (review round 2, R2-07): D's one-pagers and
    proposal print the working name, so they wait for name_decided = Y unless D has made name-free versions
    (onepagers_name_free = Y)."""
    return st.get(key) == 'Y' and (st.get('name_decided') == 'Y' or st.get('onepagers_name_free') == 'Y')


def planned(c):
    return 'set for' if c.state.get('drop_date_confirmed') == 'Y' else 'planned for'


def slot_sentence(name, c):
    st = c.state
    signed, yes = st.get('offices_signed') or 0, st.get('offices_yes') or 0
    ft = st.get('founding_taken') or 0
    if name == 'OFFICE OPENER':
        if signed < 5:
            return S(f"I'm signing up five founding offices around {{area}} for a first drop {planned(c)} the [FIRST DROP WEEK: week of Mon 2027-01-11].")
        return S("I'm adding offices around {area} for drops from [NEXT DROP DATE: Tue 2027-02-09].")
    if name == 'OFFICE PROGRESS LINE':
        if 1 <= signed <= 4:
            return S('One has signed so far.' if signed == 1 else f'{NUMWORD[signed]} have signed so far.')
        c.notes.append(f'OFFICE PROGRESS LINE: offices_signed = {signed}, left out'); return ''
    if name == 'ROSTER LINE':
        hc = st.get('tuesday_headcount')
        hc = (hc // 10) * 10 if hc else None
        if signed >= 5:
            return S(f'Five offices around {{CLUSTER_SHORT}} have signed up, with about {hc} people in on a Tuesday by their own count.')
        if signed >= 1:
            n = 'One office' if signed == 1 else f'{NUMWORD[signed]} offices'
            verb = 'has' if signed == 1 else 'have'
            return S(f"{n} around {{CLUSTER_SHORT}} {verb} signed up so far, with about {hc} people in on a Tuesday by their own count. No brand is invoiced until five have.")
        if yes >= 2:
            return S(f'{NUMWORD[yes]} offices around {{CLUSTER_SHORT}} have said yes in principle; none has signed yet. No brand is invoiced until five have.')
        return S('[ROSTER LINE LOCKED: fewer than two offices have said yes; do not send brand selling copy]')
    if name == 'OFFER LINE':
        if ft < 3:
            return S(f"Founding offer: {{product}} in five offices for a week from the drop {planned(c)} [DROP DATE: Tue 2027-01-12], about 250 units placed, with photos, depletion counts, an employee survey and a one-page report. It's $600, paid before you ship 275 units (10% spare, freight prepaid). Your next two campaigns stay at $120 an office. If it runs as promised, you write a short note we can publish with a case study.")
        return S("The offer: {product} in ten offices for a week from the drop planned for [NEXT DROP DATE: Tue 2027-02-09], about 500 units placed. You get photos, depletion counts, an employee survey and a one-page report. It's $1,500 ($150 an office), half when you sign and half when we confirm placement; you ship 550 units (10% spare, freight prepaid).")
    if name == 'OFFER SHORT':
        if ft < 3:
            return S(f"Founding brands get five offices for a week from the drop {planned(c)} [DROP DATE: Tue 2027-01-12], about 250 units placed, with photos, counts, a short survey and a one-page report, for $600, paid before you ship; you send 275 units (10% spare) and freight. If it runs as promised, you write a short note we can publish with a case study.")
        return S("Ten offices for a week from the drop planned for [NEXT DROP DATE: Tue 2027-02-09], about 500 units placed, with photos, counts, a short survey and a one-page report, for $1,500, half when you sign and half at placement; you send 550 units (10% spare) and freight.")
    if name == 'FOUNDING LINE':
        if ft == 0:
            return S('The founding price is open to the first three brands that sign.')
        if ft < 3:
            return S(f'{NUMWORD[ft]} of the three founding places {"is" if ft == 1 else "are"} taken.')
        return S('The next drop is [NEXT DROP DATE: Tue 2027-02-09].')
    if name == 'FIRST BRAND LINE':
        if c.brand_row:
            return S("The first brand I'd suggest is {brand_name}, {brand_category_phrase}{?brand_from_city}. You'll see it before it comes, and nothing comes unless you say yes.")
        return S("I'm lining up the first brands now. You'll see each one before it comes, and nothing comes unless you say yes.")
    if name == 'INSURANCE LINE':
        return S('We carry general liability insurance.' if st.get('gl_bound') == 'Y' else 'We will carry general liability insurance before your first drop.')
    if name in ('FORMATION LINE', 'HOLDING LINE'):
        # What a brand is told about when the agreement and invoice come (review round 2, R2-01). The agreement
        # waits for five signed offices, every office's yes to this brand, the company, the attorney and the name.
        # A date is printed only when the offices are done, because only the formation steps have a known length.
        wait = brand_agreement_wait(c)
        if wait == 'offices':
            return S('The agreement and invoice come once five offices have signed and each has said yes to {product}; nothing is due before then.')
        if wait == 'approvals':
            return S('The agreement and invoice come once each of the five offices has said yes to {product}; nothing is due before then.')
        if wait == 'none':
            c.notes.append(f'{name}: every gate for the agreement is met, left out (send step 6)'); return ''
        if name == 'HOLDING LINE' and c.state.get('llc_formed') != 'Y':
            return S("The agreement and invoice come by [AGREEMENT DATE: Thu 2026-11-19], once the company's registration is through; nothing is due before then.")
        if name == 'HOLDING LINE':
            return S('The agreement and invoice come by [AGREEMENT DATE: Thu 2026-11-19]; nothing is due before then.')
        return S('The agreement and invoice come by [AGREEMENT DATE: Thu 2026-11-19]. Nothing is due before then.')
    if name == 'MOCK CARD LINE':
        cold = c.stage in ('selling', 'discovery')
        if st.get('mock_card_photo_ready') == 'Y' and not cold:
            return S('Attached is a photo of the card on a real pantry shelf.')
        if st.get('mock_card_photo_ready') != 'Y':
            c.notes.append('MOCK CARD LINE: no photo yet, the card described in words')
        return S("It's a 5 by 7 inch card: the brand's name, two sentences about it, the allergen line copied from the package, and a QR code to the survey.")
    if name == 'OFFICE ONE-PAGER LINE':
        if attachment_ready(st, 'office_onepager_ready'):
            return S(f"Attached is the one-page outline, with the first drop for {{company}} {planned(c)} the [FIRST DROP WEEK: week of Mon 2027-01-11].")
        c.notes.append('OFFICE ONE-PAGER LINE: one-pager not ready, nothing attached')
        return S("The first drop for {company} would be planned for the [FIRST DROP WEEK: week of Mon 2027-01-11].")
    if name == 'STEP 0 SUBJECT':
        return S('Thank you, and the one-pager') if attachment_ready(st, 'discovery_onepager_ready') else S('Thank you, and what happens next')
    if name == 'STEP 1 SUBJECT':
        return S('The one-pager, and thank you') if attachment_ready(st, 'office_onepager_ready') else S('The details, and thank you')
    if name == 'JOIN ASK':
        if signed < 5:
            return S('Would you like {company} to be one of the five founding offices?')
        return S('Would you like {company} to join for a later drop?')
    if name == 'JOIN ASK SHORT':
        if signed < 5:
            return S('Shall I put {company} down as one of the five?')
        return S('Shall I put {company} down for a later drop?')
    if name == 'LAST CHECK LINE':
        if signed < 5:
            return S('One last check before I fill the five places: is {company} a yes, or is it a not-now?')
        return S('One last check: is {company} a yes for a later drop, or a not-now?')
    if name == 'AGREEMENT TIMING LINE':
        if st.get('attorney_cleared') == 'Y':
            return ''
        return S('The agreement comes by [AGREEMENT DATE: Thu 2026-11-19].')
    if name == 'INTAKE PARAGRAPH':
        if st.get('intake_form_ready') == 'Y':
            return S("The next step is a short form, about five minutes, with your Tuesday headcount, receiving window and the categories you want: [INTAKE FORM LINK]. I'll turn it into a one-page agreement for you to check and sign. {?[AGREEMENT TIMING LINE]}\n\nCould you fill it in this week?")
        c.notes.append('INTAKE PARAGRAPH: no intake form yet, seven questions by reply')
        return S("The next step is seven quick answers, which I'll turn into a one-page agreement for you to check and sign. {?[AGREEMENT TIMING LINE]}\n1. Roughly how many people are in on a Tuesday?\n2. Who looks after the pantry and can say yes to a brand (name and title)?\n3. Who receives deliveries, on which floor, and in what window (for example, Tuesday 9 to 11)?\n4. Is it a walk-up, a front desk or a loading dock?\n5. Does your building need a certificate of insurance for deliveries: yes, no or unsure?\n6. Slack or email for the survey post?\n7. Which categories would your team like, and any categories or allergens to avoid?\n\nCould you reply with those this week?")
    if name == 'STEP 1 OPENER':
        if c.slot_values.get('_after_step0'):
            return S('As promised, here are the details.')
        return '{call_note_hook_line}'
    if name == 'DISCOVERY ONE-PAGER LINE':
        if attachment_ready(st, 'discovery_onepager_ready'):
            return S('Attached is the one-page description I mentioned.')
        c.notes.append('DISCOVERY ONE-PAGER LINE: one-pager not ready, left out'); return ''
    if name == 'PROPOSAL LINE':
        if attachment_ready(st, 'proposal_ready'):
            return S('Attached is the one-page proposal for {company}, with a map of the stores near the offices and a mock report page.')
        c.notes.append('PROPOSAL LINE: proposal not ready, short version in the email')
        return S('The full proposal follows; here is the short version.')
    # review round 3 (R3-05): an ask never offers an attachment the state says cannot go yet
    if name == 'OUTLINE ASK':
        return S('Could I send you the one-page outline?') if attachment_ready(st, 'office_onepager_ready') else S('Could I send you the details?')
    if name == 'OUTLINE ASK SHORT':
        return S('Shall I send the outline?') if attachment_ready(st, 'office_onepager_ready') else S('Shall I send the details?')
    if name == 'PROPOSAL ASK':
        if attachment_ready(st, 'proposal_ready'):
            return S('Shall I send the one-page proposal, with a map of stores near the offices?')
        return S('Shall I send the details, with the stores near the offices?')
    if name == 'PROPOSAL ASK REPLY':
        return S('Shall I send the one-page proposal so you can see every term?') if attachment_ready(st, 'proposal_ready') else S('Shall I send you every term in writing?')
    if name == 'INFO PAGE LINE':
        key = 'discovery_onepager_ready' if c.stage == 'discovery' else ('office_onepager_ready' if c.side == 'office' else 'brand_onepager_ready')
        if attachment_ready(st, key):
            return S('Attached is a one-page description of the idea.' if c.stage == 'discovery' else 'Attached is the one-page outline.')
        c.notes.append(f'INFO PAGE LINE: {key} does not count as ready, nothing attached')
        return S('I can explain it better in 20 minutes than in a document.')
    if name == 'STEP 0 CAMPAIGN LINE':
        # review round 3 (R3-02): after the last campaign zero offer a brand new to the pipeline cannot join January
        if c.date <= LAST_OFFER_CZ:
            return S('If it goes ahead, the first campaign is planned for January, and only once the first offices have signed.')
        return S('If it goes ahead, the first campaign I could offer you is planned for February, and only once the offices have signed.')
    if name == 'OFFICE HOURS LINE':
        h = st.get('office_hours_per_signing')
        if h:
            return S(f'Signing each office has taken me about {h} hours so far.')
        c.notes.append('OFFICE HOURS LINE: no hours logged yet, left out'); return ''
    return None


NUMWORD = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten'}

AGREEMENT_EARLIEST = dt.date(2026, 11, 19)   # the day after the attorney hour and name decision (legal pack; derived)


def int_state(st, k):
    try:
        return int(st.get(k) or 0)
    except (TypeError, ValueError):
        return 0


def brand_agreement_wait(c):
    """What the brand agreement and invoice still wait for (review round 2, R2-01):
    'offices' (fewer than five signed), 'approvals' (five signed, not every office has said yes to this brand),
    'date' (only formation, the attorney hour or the name decision is left: a date can be promised), or
    'none' (every gate is met: the agreement goes now)."""
    return agreement_wait(c.state, c.row)


def agreement_wait(st, row):
    row = row or {}
    if int_state(st, 'offices_signed') < 5:
        return 'offices'
    if (row.get('office_approvals_complete') or '').strip().upper() != 'Y':
        return 'approvals'
    if all(st.get(k) == 'Y' for k in ('llc_formed', 'attorney_cleared', 'name_decided')):
        return 'none'
    return 'date'


def agreement_date(send_date):
    """The later of Thu 2026-11-19 and five business days after sending (filing, EIN, bank account; assumption)."""
    return max(AGREEMENT_EARLIEST, add_bd(send_date, 5))


# ---------------------------------------------------------------- fill
def fill_text(text, c, sig=None):
    if '[PASTE desk-drop-legal-pack/11' in text:
        b = broker_block()
        if b:
            b = fill_broker_slots(b, c)
            text = re.sub(r'\[PASTE desk-drop-legal-pack/11[^\]]*\]', lambda m: mk('X', b), text)
    # the LLC name is never typed into a template: it is the brand.json name plus " LLC", to be checked
    # letter for letter against the filed Articles (review round 1, R1-19)
    if re.search(r'\[COMPANY NAME: [^\]]*\]', text):
        if c.state.get('llc_formed') == 'Y':
            # review round 3 (R3-07): once the company exists the name prints bare; the check goes on the draft's NOTE line
            text = re.sub(r'\[COMPANY NAME: [^\]]*\]', lambda m: mk('S', f'{brand_name()} LLC'), text)
        else:
            text = re.sub(r'\[COMPANY NAME: [^\]]*\]', f'[COMPANY NAME: {brand_name()} LLC]', text)
        c.notes.append(f'COMPANY NAME: "{brand_name()} LLC" is desk-drop-identity/brand.json plus "LLC"; check it letter for letter against the filed Articles')
    # 1. computed slot sentences (may contain tokens)
    def slot_sub(m):
        inner = m.group(1)
        r = slot_sentence(inner, c)
        return m.group(0) if r is None else r
    for _ in range(3):
        text = re.sub(r'\{\?\[([A-Z0-9 \-]+)\]\}', lambda m: slot_sentence(m.group(1), c) or '', text)
        text = re.sub(r'\[([A-Z][A-Z0-9 \-]+[A-Z])\]', slot_sub, text)
    # 2. side alternatives [OFFICE: ...] [BRAND: ...]
    text = re.sub(r'\[(OFFICE|BRAND): ([^\]]+)\]', lambda m: m.group(2) if m.group(1).lower() == c.side else '', text)
    # 3. optional tokens
    text = re.sub(r'\{\?([a-z_]+)\}', lambda m: OPTIONAL[m.group(1)](c), text)
    # 4. config and field tokens
    def tok(m):
        k = m.group(1)
        if k == 'BRAND_NAME':
            return mk('C', brand_name())
        if k == 'CLUSTER':
            return mk('C', c.state['cluster_name'])
        if k == 'CLUSTER_SHORT':
            return mk('C', c.state['cluster_short'])
        if k == 'SIGNATURE':
            return sig if sig is not None else '{SIGNATURE}'
        if k in FIELDS:
            return FIELDS[k](c)
        return m.group(0)
    for _ in range(2):
        text = re.sub(r'\{([A-Za-z_]+)\}', tok, text)
    # 4b. dates computed from the send date, so a slot never prints a day that has passed. The slot sentences
    # decide whether a date is promised at all (R2-01); where one is, it is always computed here.
    text = text.replace('[AGREEMENT DATE: Thu 2026-11-19]', f'[AGREEMENT DATE: {fmt(agreement_date(c.date))}]')
    # the week the details follow a step 0 email: the week after Gate 0, or the next week if that has begun
    nxt = c.date + dt.timedelta(days=(7 - c.date.weekday()) % 7 or 7) if c.date.weekday() else c.date
    follow = max(dt.date(2026, 11, 16), nxt)
    follow = send_day(follow)
    follow -= dt.timedelta(days=follow.weekday())        # a "week of" is named by its Monday (review round 3)
    text = text.replace('[FOLLOW-UP WEEK: week of Mon 2026-11-16]', f'[FOLLOW-UP WEEK: week of {fmt(follow)}]')
    text = text.replace('[CHECK-BACK DATE]', f'[CHECK-BACK DATE: {fmt(send_day(add_bd(c.date, 5)))}]')
    text = text.replace('[SIGN-BY DATE]', f'[SIGN-BY DATE: {fmt(add_bd(c.date, 5))}]')
    text = text.replace('[INVOICE DUE: five business days from today]', f'[INVOICE DUE: {fmt(add_bd(c.date, 5))}]')
    # 5. example values for founder-time slots
    for k, v in c.slot_values.items():
        text = text.replace(f'[{k}]', mk('S', v))
    # 6. mark remaining bracketed slots and placeholders
    def br(m):
        inner = m.group(1)
        if inner in FOUNDER_PLACEHOLDERS:
            return mk('P', m.group(0))
        return mk('S', m.group(0))
    text = re.sub(r'(?<!\x01S)\[([^\[\]\x01\x02]+)\]', br, text)
    # tidy: empty lines from dropped sentences, double spaces
    lines = [re.sub(r'[ \t]{2,}', ' ', l).rstrip() for l in text.split('\n')]
    out, prev_blank = [], False
    for l in lines:
        blank = strip_marks(l).strip() == ''
        if blank and prev_blank:
            continue
        out.append(l.strip() if not blank else '')
        prev_blank = blank
    while out and out[0] == '':
        out.pop(0)
    t = '\n'.join(out).replace(' ,', ',').replace(' .', '.')
    # a sentence that now starts with a fallback ("your office ...") gets a capital letter
    t = re.sub(r'(^|\n|[.?] )((?:\x01[A-Z])+)([a-z])', lambda m: m.group(1) + m.group(2) + m.group(3).upper(), t)
    return t


CZ_SHIP_BY = dt.date(2026, 12, 22)      # CONTRACTS section 3: brands asked to ship by Tue 2026-12-22
CZ_WINDOW_CLOSE = dt.date(2027, 1, 19)  # T+4 of the campaign zero drop


def fill_broker_slots(b, c):
    """Fill the slots in the legal pack's broker block that the row and the state already know, so the founder
    types only the brand's legal name, its address and the product and SKU (review round 1, R1-20).
    The block's words are not changed."""
    brand = SUFFIX_RE.sub('', c.val('company'))
    if brand:
        b = b.replace("[BRAND]'s", brand + ("'" if brand.endswith('s') else "'s"))   # "Brightside Snacks' products"
        b = b.replace("[BRAND]", brand)
    else:
        c.notes.append('broker block: no brand name on the row, [BRAND] left for you')
    b = b.replace('[AGREEMENT DATE]', f'[AGREEMENT DATE: {fmt(c.date)}]')
    b = b.replace('[SHIP-BY DATE]', f'[SHIP-BY DATE: {fmt(CZ_SHIP_BY)}]')
    cover = dt.date(CZ_WINDOW_CLOSE.year + 1, CZ_WINDOW_CLOSE.month, CZ_WINDOW_CLOSE.day)
    b = re.sub(r'\[COVER-UNTIL DATE: [^\]]*\]', f'[COVER-UNTIL DATE: {fmt(cover)}] (12 months after the window closes) or the latest best-by date on the units, if later', b)
    b = b.replace('[COVER-UNTIL DATE]', f'[COVER-UNTIL DATE: {fmt(cover)}] (or the later best-by date)')
    c.notes.append('broker block: [BRAND LEGAL NAME], [BRAND ADDRESS] and [PRODUCT NAME AND SKU] are yours to fill from the brand intake; the dates are campaign zero\'s (change them for a later drop)')
    return b


def fill_message(msg, c, variant='A', first_subject=None):
    sig = signature_block(c.state) if msg.get('channel') in ('email', 'warm-intro', 'walk-in') else ''
    sig_filled = fill_text(sig, c) if sig else ''
    body = fill_text(msg['body'], c, sig=mk('G', sig_filled) if sig else '')
    subj = msg.get('subject_' + variant) or msg.get('subject') or ''
    if subj.startswith('Re: (touch 1 subject)') and first_subject is not None:
        subj = 'Re: ' + first_subject
    subj = fill_text(subj, c)
    return subj, body


# ---------------------------------------------------------------- checks
BANNED = [
    (r'\bguarantee[ds]?\b', r'\b(no|not a|nobody|no sales) guarantees?\b|\bno guarantees\b'),
    (r'\bfree trials?\b', r"\b(no|don't run|there's no) free trials?\b"),
    (r'\blift\b', None), (r'\bROI\b', None), (r'\bconversions?\b', None), (r'\bacquisition\b', None),
    (r'\bnew customers\b', None), (r'\bwe work with\b', None), (r'\bpartner(ed|s)? with\b', None),
    (r'\btrusted by\b', None), (r'\blimited time\b', None), (r'\bspots? left\b', None), (r'\bhurry\b', None),
    (r'\bact now\b', None), (r'\blast chance\b', None), (r'\bexclusive\b', None), (r'\bbest\b', r'\bno "best"|and no "best"'),
    (r'\bjust checking in\b', r'never "just checking in"'), (r'\bcircle back\b', None), (r'\btouch base\b', None),
    (r'\bbump(ing)?\b', r'"bumping this up"'), (r'\bquick question\b', None), (r'hope this (email )?finds you', None),
    (r'\brevolutionary\b|\bgame[- ]changer\b|\bamazing\b|\bincredible\b|\bboosts?\b', r'"boosts immunity"'),
    (r'\bdrive (trial|sales)\b', None), (r'\bsupports? gut\b', r'"supports gut health"'),
]


def slot_values_only(t):
    """What the reader sees once slots are filled: [DROP DATE: Tue 2027-01-12] reads as Tue 2027-01-12."""
    return re.sub(r'\[[A-Z][A-Z ,\-]+: ([^\]]+)\]', r'\1', t)


def body_core(body):
    """The message without signature and forwarded blocks, slots read as their values."""
    b = body.split('\x01G')[0]
    b = strip_marks(b)
    b = b.split('\n---\n')[0]
    return slot_values_only(b)


def check(msg, subj, body, c, touch_kind):
    f = []
    core = body_core(body)
    plain_subj = slot_values_only(strip_marks(subj))
    full = strip_marks(body)
    if re.search(r'\{[A-Za-z_?]+\}', full + plain_subj):
        f.append(('error', 'unfilled token'))
    q = sum(l.count('?') for l in core.split('\n') if not re.match(r'\s*\d+\.\s', l))  # a numbered questionnaire is one ask
    ask = msg.get('ask', '')
    if q > 1:
        f.append(('error', f'{q} question marks: more than one ask'))
    if q == 0 and not ask.startswith('none') and msg.get('channel') != 'linkedin-note':
        f.append(('warn', 'no question mark: check the one ask is clear'))
    if '!' in core:
        f.append(('error', 'exclamation mark'))
    words = len([w for w in re.findall(r"[A-Za-z0-9$'’]+", core) if w != 'SAMPLE'])  # SAMPLE prefixes are not part of a real email
    ch = msg.get('channel')
    touch = msg.get('touch')
    limits = {'linkedin-note': None, 'linkedin': None}
    if ch == 'linkedin-note':
        if len(core.strip()) > 200:
            f.append(('error', f'LinkedIn note {len(core.strip())} characters (limit 200)'))
    elif ch == 'linkedin':
        if len(core.strip()) > 600:
            f.append(('error', f'LinkedIn message {len(core.strip())} characters (aim 600 or fewer)'))
    elif msg.get('stage') in ('discovery', 'selling') and touch == '1':
        if words > 125:
            f.append(('error', f'touch 1 has {words} words (limit 125)'))
    elif msg.get('stage') in ('discovery', 'selling') and touch in ('2', '3'):
        if words > 75:
            f.append(('error', f'follow-up has {words} words (limit 75)'))
    elif msg['id'] != 'brand-conversion-8' and msg.get('touch') != 'post' and words > 175:
        f.append(('warn', f'{words} words'))
    for pat, ok in BANNED:
        for m in re.finditer(pat, core + ' ' + plain_subj, re.I):
            window = (core + ' ' + plain_subj)[max(0, m.start() - 30):m.end() + 20]
            if ok and re.search(ok, window, re.I):
                continue
            f.append(('error', f'banned word: "{m.group(0)}"'))
    if ch == 'email' and touch == '1' and msg.get('stage') in ('discovery', 'selling'):
        if plain_subj.lower().startswith('re:'):
            f.append(('error', 'touch 1 subject starts with Re:'))
        if re.search(r'\bfree\b', plain_subj, re.I):
            f.append(('error', '"free" in a cold subject line'))
        if re.search(r'https?://|attached|attachment|\[WEBSITE\]', core, re.I):
            f.append(('error', 'link or attachment in touch 1'))
    if ch == 'email' and touch in ('2', '3') and msg.get('stage') in ('discovery', 'selling') and not plain_subj.startswith('Re: '):
        f.append(('error', 'follow-up not sent as a reply in the thread'))
    if len(natural_dates(plain_subj, True).replace('SAMPLE ', '')) > 80:
        f.append(('warn', f'subject {len(plain_subj)} characters'))
    for m in re.finditer(r'\[([A-Z][A-Z \-]+): (week of )?(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{4}-\d\d-\d\d)\]', full + ' ' + plain_subj):
        d = dt.date.fromisoformat(m.group(4))
        if DOW[d.weekday()] != m.group(3):
            f.append(('error', f'{m.group(0)}: weekday wrong'))
        if 'DROP DATE' in m.group(1) and not drop_ok(d):
            f.append(('error', f'{m.group(0)}: not a legal drop day (Tue or Wed, window clear of blackouts)'))
        # a promised date never lies in the past on the day the message is sent (review round 2, R2-01)
        last_day = d + dt.timedelta(days=4) if m.group(2) else d
        if last_day < c.date:
            f.append(('error', f'{m.group(0)}: a date that has passed on the send date {c.date}'))
    # the agreement date, wherever it is promised, is the one computed from the send date (R2-01)
    for m in re.finditer(r'\[AGREEMENT DATE: (?:Mon|Tue|Wed|Thu|Fri) (\d{4}-\d\d-\d\d)\]', strip_marks(body.split('\x01X')[0]) + ' ' + strip_marks(subj)):
        if dt.date.fromisoformat(m.group(1)) != agreement_date(c.date):
            f.append(('error', f'{m.group(0)}: not the agreement date computed from the send date ({fmt(agreement_date(c.date))})'))
    if re.search(r'\[AGREEMENT DATE\]', strip_marks(body.split('\x01X')[0])):
        f.append(('error', '[AGREEMENT DATE] left unfilled'))
    # campaign zero's last offer and last yes (review round 2, R2-05): a verbal yes needs up to 3 business days of
    # office approvals, a 5-business-day sign-by and 5 to pay, all before the asked ship-by Tue 2026-12-22
    if msg['side'] == 'brand' and msg.get('stage') in ('selling', 'conversion') and '2027-01-12' in full + ' ' + plain_subj \
            and not c.slot_values.get('_moved'):
        mid = msg['id']
        offer = (msg.get('stage') == 'selling' and touch in ('0', '1')) or mid == 'brand-conversion-1'
        asks_yes = mid in ('brand-conversion-2', 'brand-conversion-5') or (msg.get('stage') == 'selling' and touch not in ('0', '1'))
        if offer and c.date > LAST_OFFER_CZ:
            f.append(('error', f'sent {c.date} offering the Tue 2027-01-12 drop: after {fmt(LAST_OFFER_CZ)} a new brand cannot get a yes, the office approvals, a signature and payment in before ship-by; offer [NEXT DROP DATE]'))
        elif asks_yes and c.date > LAST_YES_CZ:
            f.append(('error', f'sent {c.date} asking for a yes to the Tue 2027-01-12 drop: after {fmt(LAST_YES_CZ)} the approvals, signature and payment cannot all land before ship-by; offer [NEXT DROP DATE]'))
    if msg.get('stage') in ('discovery', 'selling') and touch == '1' and msg.get('channel') in ('email', 'linkedin') \
            and '\x01F' not in body.split('\x01G')[0]:
        f.append(('warn', 'nothing about this person or company is printed: fix the row before sending'))
    for name in COMPUTED_SLOTS:
        if f'[{name}]' in full:
            f.append(('error', f'computed slot [{name}] was not filled'))
    if 'LOCKED' in full:
        f.append(('error', 'a locked slot was used: this message is not unlocked by the state'))
    for g in gates(msg, c.state, c.row, c.side):
        f.append(('error', g))
    if ch in ('email', 'warm-intro', 'walk-in') and 'no thanks' not in full:
        f.append(('error', 'footer missing'))
    # no cold email from the new domain before the earliest first cold day, whatever the state says (R1-01)
    if ch == 'email' and touch == '1' and msg.get('stage') in ('discovery', 'selling') and c.date < EARLIEST_COLD:
        f.append(('error', f'cold email touch 1 on {c.date}: no cold email from [DOMAIN] before {fmt(EARLIEST_COLD)} (sending/sending-setup.md section 0)'))
    # the working name is not printed before the name is decided (R1-02)
    if c.state.get('name_decided') != 'Y' and ch in ('email', 'warm-intro', 'walk-in') and brand_name() in strip_marks(body):
        f.append(('error', f'"{brand_name()}" printed while name_decided = N'))
    # a drop date reads as fixed only once drop_date_confirmed = Y (04 rule 1, R1-15)
    if c.state.get('drop_date_confirmed') != 'Y' and msg['id'] not in POST_SIGNATURE:
        for m in re.finditer(r'(?:\bfrom|\byour|\bfor your)\s+\[(?:NEXT )?DROP DATE', strip_marks(subj) + ' ' + strip_marks(body)):
            f.append(('error', f'"{m.group(0)}" reads as a fixed date: write "the drop planned for" until drop_date_confirmed = Y'))
    return f


EARLIEST_COLD = dt.date(2026, 11, 9)   # sending/sending-setup.md section 0 (review round 1)
POST_SIGNATURE = ('brand-conversion-7', 'brand-conversion-8', 'brand-conversion-9', 'brand-conversion-10')   # the date is the signed agreement's


COMPUTED_SLOTS = ['OFFICE OPENER', 'OFFICE PROGRESS LINE', 'ROSTER LINE', 'OFFER LINE', 'OFFER SHORT', 'FOUNDING LINE',
                  'FIRST BRAND LINE', 'INSURANCE LINE', 'FORMATION LINE', 'MOCK CARD LINE', 'OFFICE HOURS LINE',
                  'OFFICE ONE-PAGER LINE', 'LAST CHECK LINE', 'AGREEMENT TIMING LINE', 'INTAKE PARAGRAPH', 'PROPOSAL LINE',
                  'STEP 1 OPENER', 'DISCOVERY ONE-PAGER LINE', 'JOIN ASK', 'JOIN ASK SHORT', 'STEP 0 SUBJECT', 'STEP 1 SUBJECT',
                  'HOLDING LINE', 'OUTLINE ASK', 'OUTLINE ASK SHORT', 'PROPOSAL ASK', 'PROPOSAL ASK REPLY', 'INFO PAGE LINE',
                  'STEP 0 CAMPAIGN LINE']
# Derived, founder to confirm (review round 2, R2-05). Working back from the asked ship-by, Tue 2026-12-22:
# payment due 5 business days after the invoice (invoice by Tue 2026-12-15, the day of signature), signature within
# 5 business days of the agreement (agreement by Tue 2026-12-08), and up to 3 business days of office approvals
# before the agreement (verbal yes by Thu 2026-12-03). A proposal needs a few days to get its yes: last one Mon 2026-11-30.
LAST_YES_CZ = dt.date(2026, 12, 3)
LAST_OFFER_CZ = dt.date(2026, 11, 30)


# review round 3 (R3-02): copy that is true only before that side sells. "There's nothing to buy yet", "Questions only",
# "I'm not selling anything yet" and "before I build anything" become false once the selling switch is Y. Follow-ups 2
# and 3 of a discovery thread already begun say none of this, so they may finish it (the draft maker matches every
# follow-up to the row's sequence).
DISCOVERY_ONLY = {
    'office': ('office-discovery-1', 'li-office-discovery-note', 'li-office-discovery-1', 'warm-ask-office', 'office-conversion-0'),
    'brand': ('brand-discovery-1', 'li-brand-discovery-note', 'li-brand-discovery-1', 'warm-ask-brand', 'brand-conversion-0'),
    'both': ('warm-direct', 'referral-first-touch', 'reply-send-info-discovery'),
}
SELLING_VERSION = {'office': '05 part 2, 07 office selling, or 10 step 1', 'brand': '06 part 2, 07 brand selling, or 11 step 1'}


def gates(msg, st, row=None, side=None):
    g, i = [], msg['id']
    row = row or {}
    sd = msg['side'] if msg['side'] in ('office', 'brand') else (side if side in ('office', 'brand') else None)
    if sd and (i in DISCOVERY_ONLY[sd] or i in DISCOVERY_ONLY['both']) and st.get(f'{sd}_selling_on') == 'Y':
        g.append(f'{sd}_selling_on = Y: this discovery copy says nothing is for sale, which is no longer true on the {sd} side; '
                 f'send the selling version ({SELLING_VERSION[sd]})')
    if msg.get('channel') == 'email' and msg.get('touch') == '1' and msg.get('stage') in ('discovery', 'selling') and st.get('domain_ready') != 'Y':
        g.append('domain_ready = N: no cold touch 1 from the new domain yet')
    if i.startswith(('office-selling', 'li-office-selling')) and st.get('office_selling_on') != 'Y':
        g.append('office_selling_on = N')
    if i.startswith(('brand-selling', 'li-brand-selling')) and st.get('brand_selling_on') != 'Y':
        g.append('brand_selling_on = N')
    if i in ('office-conversion-1', 'office-conversion-2', 'office-conversion-3') and st.get('office_selling_on') != 'Y':
        g.append('office_selling_on = N: before Gate 0 the post-call email is step 0 (no date proposed)')
    if i in ('brand-conversion-1', 'brand-conversion-2', 'brand-conversion-3', 'brand-conversion-4') and st.get('brand_selling_on') != 'Y':
        g.append('brand_selling_on = N: before then the post-call email is step 0 (nothing sold)')
    if i in ('office-conversion-6', 'brand-conversion-6', 'brand-conversion-7', 'brand-conversion-8') and st.get('name_decided') != 'Y':
        g.append('name_decided = N: agreements, invoices and the insurance request name the business, so they wait for the name decision')
    if i == 'office-conversion-6' and st.get('attorney_cleared') != 'Y':
        g.append('attorney_cleared = N: the office agreement cannot go out')
    if i in ('brand-conversion-6', 'brand-conversion-7', 'brand-conversion-8') and not (st.get('llc_formed') == 'Y' and st.get('attorney_cleared') == 'Y'):
        g.append('llc_formed or attorney_cleared = N: no agreement, invoice or certificate request yet')
    # the plan's order (How a campaign runs, steps 3 and 4): offices approve the brand, then agreement and payment;
    # and the selling copy promises "No brand is invoiced until five have" signed (review round 1, R1-04)
    if i in ('brand-conversion-6', 'brand-conversion-7'):
        try:
            signed = int(st.get('offices_signed') or 0)
        except (TypeError, ValueError):
            signed = 0
        if signed < 5:
            g.append(f'offices_signed = {signed}: no brand agreement or invoice until five offices have signed')
        if (row.get('office_approvals_complete') or '').strip().upper() != 'Y':
            g.append('office_approvals_complete is not Y on this brand row: every office on the route must say yes (10, step 7) before the agreement or invoice')
    # the holding note is for the wait; once every gate is met the agreement itself goes (R2-01)
    if i == 'brand-conversion-5' and agreement_wait(st, row) == 'none':
        g.append('every gate for the agreement is met (five offices signed and approved, company formed, attorney cleared, name decided): send step 6, not the holding note')
    try:
        ft = int(st.get('founding_taken') or 0)
    except (TypeError, ValueError):
        ft = 0
    if i in ('brand-conversion-1', 'brand-conversion-2', 'brand-conversion-4', 'brand-conversion-5', 'brand-conversion-6', 'brand-conversion-7') and ft >= 3:
        g.append('founding_taken = 3: these emails carry the founding price; the founding offer is closed (write the standard terms from [OFFER LINE] instead)')
    if msg.get('channel') == 'slack' and st.get('startup_cpg_joined') != 'Y':
        g.append('startup_cpg_joined = N')
    return g


# ---------------------------------------------------------------- html
CSS = """
*{box-sizing:border-box} body{margin:0;background:#e9e7e2;font:15px/1.45 -apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1d1d1f}
.wrap{width:390px;margin:0 auto;padding:12px 12px 24px}
.banner{background:#b3261e;color:#fff;font-weight:700;font-size:12px;letter-spacing:.06em;text-transform:uppercase;padding:8px 10px;border-radius:8px;margin-bottom:8px}
.title{font-weight:700;font-size:16px;margin:6px 2px 2px}
.meta{font-size:12px;color:#555;margin:0 2px 8px}
.legend{display:flex;flex-wrap:wrap;gap:6px;font-size:11px;margin:0 2px 10px}
.legend span{padding:1px 6px;border-radius:4px}
.card{background:#fff;border-radius:12px;padding:12px 14px 14px;margin:10px 0;box-shadow:0 1px 2px rgba(0,0,0,.12)}
.card.li{background:#fff;border-left:4px solid #0a66c2}
.card.slack{border-left:4px solid #611f69}
.hd{font-size:12px;color:#666;border-bottom:1px solid #eee;padding-bottom:6px;margin-bottom:8px}
.hd b{color:#1d1d1f}
.subj{font-weight:700;font-size:15px;margin:2px 0 4px;color:#1d1d1f}
.body{white-space:pre-wrap;word-wrap:break-word}
.F{background:#e3edfb;border-radius:3px}
.C{}
.B{background:#ffe7b3;border-radius:3px;outline:1px dashed #b36b00}
.S{background:#fff3a0;border-radius:3px}
.P{background:#ececec;border-radius:3px;font-family:ui-monospace,Menlo,monospace;font-size:13px}
.G{display:block;color:#222;font-size:14px;border-top:1px solid #eee;margin-top:6px;padding-top:6px}
.X{display:block;font-size:12.5px;color:#333;background:#f4f4f4;border-radius:6px;padding:6px 8px;margin-top:4px}
.notes{margin-top:8px;font-size:11.5px;color:#7a4b00;background:#fff8e8;border-radius:6px;padding:6px 8px}
.notes div.fb::before{content:'fallback · ';font-weight:700}
.notes div.st::before{content:'state · ';font-weight:700}
.findings{margin-top:8px;font-size:11.5px;border-radius:6px;padding:6px 8px}
.ok{background:#e8f5e9;color:#1b5e20}.bad{background:#fdecea;color:#8a1c14}
.foot{font-size:11px;color:#666;margin:12px 2px 0}
"""


MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
DAYNAME = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
VALUE_SLOTS = ('UNITS TO SHIP', 'TIME PERIOD')


def natural_dates(t, subject=False):
    """What the reader sees: [DROP DATE: Tue 2027-01-12] -> Tuesday, January 12 (January 12 in a subject)."""
    def nat(x, week=False):
        md = f'{MONTHS[x.month - 1]} {x.day}' + (f', {x.year}' if x.year >= 2028 else '')   # campaign dates are 2026-27; later ones carry the year
        if week:
            return f'week of {md}'
        return md if subject else f'{DAYNAME[x.weekday()]}, {md}'
    t = re.sub(r'\[[A-Z][A-Z ,\-]+: (week of )?(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{4}-\d\d-\d\d)\]',
               lambda m: nat(dt.date.fromisoformat(m.group(2)), bool(m.group(1))), t)
    t = re.sub(r'\b(?:Mon|Tue|Wed|Thu|Fri) (\d{4}-\d\d-\d\d)\b', lambda m: nat(dt.date.fromisoformat(m.group(1))), t)
    for k in VALUE_SLOTS:
        t = re.sub(r'\[' + k + r': ([^\]]+)\]', r'\1', t)
    return t


def to_html(s, subject=False):
    s = natural_dates(s, subject)
    s = html.escape(s, quote=False)
    s = re.sub(r'\x01([A-Z])', lambda m: f'<span class="{m.group(1)}">', s)
    return s.replace('\x02', '</span>')


def render_example(ex, msgs, rows, states):
    row = rows[ex['row_id']]
    st = dict(states['_base']); st.update(states[ex['state']])
    brand_row = rows.get(ex.get('brand_row_id', ''), {})
    start = dt.date.fromisoformat(ex['start_date'])
    cards, all_findings, first_subject = [], [], None
    for step in ex['messages']:
        mid, off = step['id'], step.get('offset_bd', 0)
        msg = msgs[mid]
        d = send_day(add_bd(start, off)) if off else send_day(start)
        if step.get('days_before'):
            d = add_bd(start, -int(step['days_before']))
        st_step = dict(st); st_step.update({k: (int(v) if isinstance(v, str) and v.isdigit() else v) for k, v in step.get('state', {}).items()})
        sv = dict(ex.get('slot_values') or {}); sv.update(step.get('slot_values', {}))
        row_step = dict(row); row_step.update(step.get('row', {}))
        c = Ctx(row_step, st_step, msg['side'] if msg['side'] in ('office', 'brand') else ex['side'], msg['stage'], d, brand_row, sv)
        subj, body = fill_message(msg, c, ex.get('variant', 'A'), first_subject)
        if msg.get('touch') == '1' and msg.get('channel') == 'email':
            first_subject = strip_marks(subj)
        fnd = check(msg, subj, body, c, None)
        all_findings += [(mid,) + x for x in fnd]
        ch = msg.get('channel')
        cls = 'li' if ch.startswith('linkedin') else ('slack' if ch == 'slack' else '')
        if ch.startswith('linkedin'):
            hd = f'<b>LinkedIn</b> · {"connection note" if ch == "linkedin-note" else "message"} · {fmt(d)} (example)'
        elif ch == 'slack':
            hd = f'<b>Startup CPG Slack</b> · post · {fmt(d)} (example)'
        else:
            to = html.escape(row.get('work_email') or '(no email)')
            hd = f'<b>From</b> [FOUNDER NAME] &lt;[EMAIL]&gt;<br><b>To</b> {to}<br><b>Sent</b> {fmt(d)} (example) · {html.escape(mid)}'
        notes = ''.join(f'<div class="{"st" if n.split(":")[0].isupper() else "fb"}">{html.escape(n)}</div>' for n in dict.fromkeys(c.notes))
        if step.get('branch'):
            hd += f'<br><b>Branch</b> {html.escape(step["branch"])}'
        fh = ''.join(f'<div>{html.escape(k)}: {html.escape(t)}</div>' for k, t in fnd)
        cards.append(f'<div class="card {cls}"><div class="hd">{hd}</div>'
                     + (f'<div class="subj">{to_html(subj, True)}</div>' if subj else '')
                     + f'<div class="body">{to_html(body)}</div>'
                     + (f'<div class="notes">{notes}</div>' if notes else '')
                     + (f'<div class="findings bad">{fh}</div>' if fh else f'<div class="findings ok">checks passed: one ask, length, banned words, dates, {"footer, " if ch in ("email", "warm-intro", "walk-in") else ""}gates</div>')
                     + '</div>')
    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=390">
<title>{html.escape(ex['id'])}</title><style>{CSS}</style></head><body><div class="wrap">
<div class="banner">SAMPLE · example, not a real send · {html.escape(ex['label'])}</div>
<div class="title">{html.escape(ex['title'])}</div>
<div class="meta">Row {html.escape(ex['row_id'])} · state "{html.escape(ex['state'])}" · subject variant {ex.get('variant', 'A')}</div>
<div class="legend"><span class="F">from the row</span><span class="B">fallback used</span><span class="S">slot (tracker state or date)</span><span class="P">[YOUR DETAIL]</span></div>
{''.join(cards)}
<div class="foot">Filled by messages/_render/fill.py from {html.escape(', '.join(sorted({msgs[s['id']]['file'] for s in ex['messages']})))} on {dt.date.today().isoformat()}. SAMPLE row and state from examples/SAMPLE-rows.csv and SAMPLE-states.json. Illustrative placeholders, not results.</div>
</div></body></html>"""
    return page, all_findings


def load_examples():
    exdir = os.path.join(MSG_DIR, 'examples')
    rows = {r['row_id']: r for r in read_csv(os.path.join(exdir, 'SAMPLE-rows.csv'))}
    states = json.load(open(os.path.join(exdir, 'SAMPLE-states.json'), encoding='utf-8'))
    base = load_state(os.path.join(MSG_DIR, '04-slot-state.csv'))
    states['_base'] = base
    for k, v in list(states.items()):
        if k != '_base' and isinstance(v, dict):
            for kk, vv in v.items():
                if isinstance(vv, str) and vv.isdigit():
                    v[kk] = int(vv)
    exs = json.load(open(os.path.join(exdir, 'SAMPLE-examples.json'), encoding='utf-8'))
    return exdir, rows, states, exs


def cmd_examples():
    msgs = load_messages()
    exdir, rows, states, exs = load_examples()
    total = []
    for ex in exs:
        page, fnd = render_example(ex, msgs, rows, states)
        open(os.path.join(exdir, ex['id'] + '.html'), 'w', encoding='utf-8').write(page)
        total += [(ex['id'],) + x for x in fnd]
    print(f'{len(exs)} examples written to {exdir}')
    for x in total:
        print(' · '.join(x))
    return 1 if any(x[2] == 'error' for x in total) else 0


# messages whose gates need more than the shared lint state (offices_signed = 0, name_decided = N)
LINT_OVERRIDES = {m: {'offices_signed': 5, 'offices_yes': 6, 'tuesday_headcount': 410, 'name_decided': 'Y'}
                  for m in ('office-conversion-6', 'brand-conversion-6', 'brand-conversion-7', 'brand-conversion-8')}
# discovery copy is filled with both selling switches off (review round 3, R3-02: it is refused once they are on)
LINT_DISCOVERY = {'office_selling_on': 'N', 'brand_selling_on': 'N'}


def state_problems(st, d=None):
    """Review round 3 (R3-06): a state the folder's own gates make impossible. The logical rules always apply (the live
    04-slot-state.csv, the lint state, every example); the calendar rules (default dates, derived, founder to confirm)
    apply when a send date d is given, as in the examples."""
    n = lambda k: int_state(st, k)
    p = []
    if n('offices_signed') > n('offices_yes'):
        p.append(f'offices_signed {n("offices_signed")} is more than offices_yes {n("offices_yes")} (a signed office is also a yes)')
    if n('offices_signed') > 0 and not (st.get('attorney_cleared') == 'Y' and st.get('name_decided') == 'Y'):
        p.append('offices_signed above 0 needs attorney_cleared = Y and name_decided = Y (no office agreement goes out before both)')
    if n('offices_signed') > 0 and not str(st.get('tuesday_headcount') or '').strip():
        p.append('offices_signed above 0 needs tuesday_headcount (the signed offices\' own numbers)')
    if n('offices_signed') == 0 and str(st.get('tuesday_headcount') or '').strip():
        p.append('tuesday_headcount is filled while offices_signed = 0 (it is blank until an office signs)')
    if n('founding_taken') > n('brands_paid'):
        p.append(f'founding_taken {n("founding_taken")} is more than brands_paid {n("brands_paid")}')
    if n('brands_paid') > 0 and n('offices_signed') < 5:
        p.append(f'brands_paid {n("brands_paid")} with offices_signed {n("offices_signed")}: no brand is invoiced until five offices have signed')
    if n('brands_paid') > 0 and not all(st.get(k) == 'Y' for k in ('llc_formed', 'attorney_cleared', 'name_decided')):
        p.append('brands_paid above 0 needs llc_formed, attorney_cleared and name_decided = Y (no brand agreement or invoice before them)')
    if st.get('brand_selling_on') == 'Y' and n('offices_yes') < 2:
        p.append('brand_selling_on = Y needs offices_yes of 2 or more (04-slot-state.csv)')
    if st.get('drop_date_confirmed') == 'Y' and n('brands_paid') < 2:
        p.append('drop_date_confirmed = Y needs both founding brands paid (brands_paid 2 or more)')
    if d is not None:
        if n('offices_signed') > 0 and d < AGREEMENT_EARLIEST:
            p.append(f'offices_signed above 0 on {fmt(d)}: no agreement is signed before {fmt(AGREEMENT_EARLIEST)}')
        for k, first in (('name_decided', dt.date(2026, 11, 18)), ('attorney_cleared', dt.date(2026, 11, 18)), ('llc_formed', AGREEMENT_EARLIEST)):
            if st.get(k) == 'Y' and d < first:
                p.append(f'{k} = Y on {fmt(d)}: by the default calendar not before {fmt(first)}')
    return p


def cmd_lint():
    """Fill every message once with each SAMPLE row of its side, in a state that unlocks it."""
    msgs = load_messages()
    exdir, rows, states, exs = load_examples()
    st0 = dict(states['_base']); st0.update(states['lint-all-unlocked'])
    bad = 0
    # review round 3 (R3-06): the live state, the lint state and every example state obey the folder's own gates
    for label, stx in [('04-slot-state.csv (live)', states['_base']), ('lint-all-unlocked', st0)] + \
            [(f'lint override {m}', dict(st0, **v)) for m, v in LINT_OVERRIDES.items()]:
        for prob in state_problems(stx):
            bad += 1
            print(f'state {label}: {prob}')
    bad += selftest_example_states(msgs, rows, states, exs)
    for mid, msg in msgs.items():
        st = dict(st0); st.update(LINT_OVERRIDES.get(mid, {}))
        if msg.get('stage') == 'discovery' or mid in DISCOVERY_ONLY['office'] + DISCOVERY_ONLY['brand']:
            st.update(LINT_DISCOVERY)
        side = msg['side'] if msg['side'] in ('office', 'brand') else 'office'
        for r in rows.values():
            if r['side'] != side:
                continue
            r = dict(r, office_approvals_complete='Y')     # the lint state unlocks everything, including R1-04's gate
            c = Ctx(r, st, side, msg['stage'], dt.date(2026, 11, 17), next((x for x in rows.values() if x['side'] == 'brand'), {}),
                    {'TIME OPTION 1': 'Tue 2026-11-24 at 10:00', 'TIME OPTION 2': 'Wed 2026-11-25 at 14:00'})
            subj, body = fill_message(msg, c, 'A', 'SAMPLE subject')
            for k, t in check(msg, subj, body, c, None):
                if k == 'error':
                    bad += 1
                print(f'{mid} [{r["row_id"]}] {k}: {t}')
    bad += selftest_agreement_promises(msgs, rows, st0)
    bad += selftest_discovery_refused(msgs, rows, st0)
    bad += selftest_side_caps()
    docs = ' '.join(open(os.path.join(MSG_DIR, f), encoding='utf-8').read() for f in os.listdir(MSG_DIR) if re.match(r'^\d\d-.*\.(md|csv)$', f))
    norm = lambda t: re.sub(r'\s+', ' ', t.replace('""', '"')).strip()
    docs_n = norm(docs)
    for t in sorted(SLOT_SEEN):
        raw = norm(strip_marks(t))
        probe = re.sub(r'\b(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|\d+)\b', '[N]', raw)
        parts = [p for p in re.split(r'\[N\]|\{[^}]+\}|\[[^\]]+\]', probe) if len(p.strip()) > 12]
        missing = [p.strip() for p in parts if norm(p) not in re.sub(r'\b(One|Two|Three|Four|Five|\d+)\b', '[N]', docs_n)]
        if missing:
            bad += 1
            print(f'slot wording not in the docs (04-slot-table.csv or a message file): "{missing[0][:90]}"')
    print(f'{len(msgs)} messages checked; {bad} errors')
    return 1 if bad else 0


def selftest_agreement_promises(msgs, rows, st0):
    """Review round 2 (R2-01): steps 1 and 5 never promise a date the gates make false. Every combination of the
    gates is filled on four send dates; a date may appear only when the offices are done, never in the past, and
    "registration" only while llc_formed = N."""
    bad, n = 0, 0
    brand = next(r for r in rows.values() if r['side'] == 'brand')
    for mid in ('brand-conversion-1', 'brand-conversion-5'):
        msg = msgs[mid]
        for signed in (0, 2, 5):
            for appr in ('N', 'Y'):
                for llc in ('N', 'Y'):
                    for att in ('N', 'Y'):
                        for name in ('N', 'Y'):
                            for d in (dt.date(2026, 11, 17), dt.date(2026, 11, 30), dt.date(2026, 12, 1), dt.date(2026, 12, 3)):
                                st = dict(st0, offices_signed=signed, llc_formed=llc, attorney_cleared=att, name_decided=name,
                                          offices_yes=max(signed, 2), founding_taken=0,
                                          tuesday_headcount={0: '', 2: 120, 5: 410}[signed])
                                row = dict(brand, office_approvals_complete=appr)
                                c = Ctx(row, st, 'brand', 'conversion', d)
                                subj, body = fill_message(msg, c, 'A', 'SAMPLE subject')
                                core = strip_marks(body.split('\x01G')[0])
                                wait = agreement_wait(st, row)
                                n += 1
                                errs = []
                                if '[AGREEMENT DATE' in core and wait != 'date':
                                    errs.append(f'a date is promised while the agreement waits for {wait}')
                                if wait == 'offices' and 'five offices have signed' not in core:
                                    errs.append('the wait for five signed offices is not stated')
                                if wait == 'approvals' and 'each of the five offices has said yes' not in core:
                                    errs.append('the wait for the office approvals is not stated')
                                if 'registration' in core and llc == 'Y':
                                    errs.append('says the registration is pending after llc_formed = Y')
                                errs += [t for k, t in check(msg, subj, body, c, None) if k == 'error'
                                         and ('passed' in t or 'AGREEMENT DATE' in t)]
                                for e in errs:
                                    bad += 1
                                    print(f'selftest {mid} signed={signed} approvals={appr} llc={llc} attorney={att} name={name} {d}: {e}')
    print(f'selftest: agreement and invoice promises in steps 1 and 5, {n} combinations filled')
    return bad


def selftest_example_states(msgs, rows, states, exs):
    """Review round 3 (R3-06): every example step's state is possible on its send date."""
    bad, n = 0, 0
    for ex in exs:
        st = dict(states['_base']); st.update(states[ex['state']])
        start = dt.date.fromisoformat(ex['start_date'])
        for step in ex['messages']:
            off = step.get('offset_bd', 0)
            d = send_day(add_bd(start, off)) if off else send_day(start)
            if step.get('days_before'):
                d = add_bd(start, -int(step['days_before']))
            st_step = dict(st); st_step.update({k: (int(v) if isinstance(v, str) and v.isdigit() else v) for k, v in step.get('state', {}).items()})
            n += 1
            for prob in state_problems(st_step, d):
                bad += 1
                print(f'selftest example state {ex["id"]} {step["id"]} {d}: {prob}')
    print(f'selftest: {n} example steps checked against the gates and the default calendar')
    return bad


def selftest_discovery_refused(msgs, rows, st0):
    """Review round 3 (R3-02): every discovery-only block is refused once its side's selling switch is Y, and only then."""
    bad, n = 0, 0
    sides = {'office': next(r for r in rows.values() if r['side'] == 'office'), 'brand': next(r for r in rows.values() if r['side'] == 'brand')}
    for side in ('office', 'brand'):
        for mid in DISCOVERY_ONLY[side] + DISCOVERY_ONLY['both']:
            msg = msgs[mid]
            for on in ('N', 'Y'):
                for other in ('N', 'Y'):
                    other_side = 'brand' if side == 'office' else 'office'
                    st = dict(st0, **{f'{side}_selling_on': on, f'{other_side}_selling_on': other})
                    c = Ctx(sides[side], st, side, msg['stage'], dt.date(2026, 11, 30))
                    subj, body = fill_message(msg, c, 'A', 'SAMPLE subject')
                    refused = any(k == 'error' and 'discovery copy says nothing is for sale' in t for k, t in check(msg, subj, body, c, None))
                    n += 1
                    if refused != (on == 'Y'):
                        bad += 1
                        print(f'selftest discovery {mid} as {side}, {side}_selling_on = {on}, {other_side}_selling_on = {other}: '
                              f'{"refused" if refused else "not refused"}')
    print(f'selftest: discovery-only copy refused under its side\'s selling switch, {n} combinations filled')
    return bad


def side_cap(day_n, side):
    """Each side's share of the day's cold first touches (review round 2, R2-04): offices get the odd one,
    so the two shares always add up to the day's number in sending/warmup-schedule.csv."""
    return (day_n + 1) // 2 if side == 'office' else day_n // 2


def selftest_side_caps():
    bad = 0
    p = os.path.join(OUT_DIR, 'sending', 'warmup-schedule.csv')
    days = read_csv(p) if os.path.exists(p) else []
    for r in days:
        n = int(r['cold_email_first_touches'] or 0)
        if side_cap(n, 'office') + side_cap(n, 'brand') != n:
            bad += 1
            print(f'selftest side caps {r["date"]}: {side_cap(n, "office")} + {side_cap(n, "brand")} is not {n}')
    print(f'selftest: office and brand shares add up to the day\'s number on {len(days)} schedule days')
    return bad


def warmup_first_touches(d):
    """The day's cold first-touch number from sending/warmup-schedule.csv (both sides together), or None."""
    p = os.path.join(OUT_DIR, 'sending', 'warmup-schedule.csv')
    try:
        for r in read_csv(p):
            if r['date'] == d.isoformat():
                return int(r['cold_email_first_touches'] or 0)
    except (OSError, KeyError, ValueError):
        return None
    return None


def first_subject_for(msgs, msg, row, c, variant):
    """The touch 1 subject this row was sent, rebuilt from its sequence variant, so a follow-up reads "Re: <it>"."""
    t1 = next((m for m in msgs.values() if m['side'] == msg['side'] and m.get('stage') == msg.get('stage')
               and m.get('channel') == msg.get('channel') and m.get('touch') == '1'), None)
    if not t1:
        return None
    s = t1.get('subject_' + variant) or t1.get('subject') or ''
    return strip_marks(fill_text(s, c)) if s else None


CONVERSION_STATUSES = ('replied', 'call_booked', 'call_done', 'yes_in_principle', 'materials_sent', 'signed', 'paid')


def fresh_why_now_note(c, msg):
    """A touch 1 whose row has a fresh why_now (120 days or less, with its URL) but no why_now_hook written yet."""
    if msg.get('touch') not in ('1',) or '{?why_now_hook}' not in msg['body']:
        return ''
    if c.val('why_now_hook') or not c.val('why_now_url'):
        return ''
    d = c.val('why_now_date')
    try:
        age = (c.date - dt.date.fromisoformat(d[:10] if len(d) >= 10 else d[:7] + '-01')).days
    except Exception:
        return ''
    if 0 <= age <= 120:
        return (f'fresh why_now ({d}, {c.val("why_now_url")}): "{c.val("why_now")[:90]}". Write why_now_hook in Clay '
                f'(one true sentence, 03-personalization-fields.md) and run the draft again, or send without it')
    return ''


def cmd_drafts(args):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--daily', required=True); ap.add_argument('--message', required=True)
    ap.add_argument('--date', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--state', default=os.path.join(MSG_DIR, '04-slot-state.csv'))
    ap.add_argument('--variant', default=None)
    ap.add_argument('--over-cap', action='store_true',
                    help="write more cold first touches than sending/warmup-schedule.csv allows for the day (not recommended)")
    ap.add_argument('--side-share', type=int, default=None,
                    help='cold first touches for this side today (default: offices get half the day\'s number rounded up, brands the rest)')
    a = ap.parse_args(args)
    msgs = load_messages(); msg = msgs[a.message]
    st = load_state(a.state)
    d = dt.date.fromisoformat(a.date)
    # review round 3 (R3-06): never write from a state the gates make impossible
    probs = state_problems(st)
    if probs:
        print('refused: the slot state is not possible under the folder\'s own gates (' + '; '.join(probs) + '). '
              'Fix messages/04-slot-state.csv (the Friday Scorecard has the counts). Nothing written.')
        return 1
    # R1-12 (b): never write drafts for a day nothing is sent
    if send_day(d) != d:
        print(f'refused: {fmt(d)} is not a sending day (weekend, federal holiday, Fri 2026-11-27 or 18 December to 4 January). '
              f'The next sending day is {fmt(send_day(d))}. Nothing written.')
        return 1
    cold_t1 = msg.get('channel') == 'email' and msg.get('touch') == '1' and msg.get('stage') in ('discovery', 'selling')
    if cold_t1 and d < EARLIEST_COLD:
        print(f'refused: no cold email from [DOMAIN] before {fmt(EARLIEST_COLD)} (sending/sending-setup.md section 0). '
              f'Weeks 1 and 2 run on warm asks, LinkedIn and walk-ins (files 07 and 08). Nothing written.')
        return 1
    cap = None
    if cold_t1 and not a.over_cap:
        day_n = warmup_first_touches(d)
        if day_n is None:
            print(f'refused: {d} is not in sending/warmup-schedule.csv, so the day\'s cold email number is unknown. '
                  f'Rebuild the schedule (tools/build_warmup.py) or pass --over-cap. Nothing written.')
            return 1
        cap = a.side_share if a.side_share is not None else side_cap(day_n, msg['side'])
        cap = min(cap, day_n)
        other = 'brand' if msg['side'] == 'office' else 'office'
        print(f'cap: {cap} cold first touches for {msg["side"]}s on {d} (sending/warmup-schedule.csv: {day_n} for both sides; '
              f'{side_cap(day_n, other)} for {other}s)')
    os.makedirs(a.out, exist_ok=True)
    n = 0
    for r in read_csv(a.daily):
        rid = r.get('row_id')
        if r.get('side') and r['side'] != msg['side'] and msg['side'] in ('office', 'brand'):
            print(f'skip {rid}: a {r["side"]} row, and {a.message} is for {msg["side"]}s'); continue
        if (r.get('do_not_contact') or 'Y').strip().upper() != 'N':
            print(f'skip {rid}: do_not_contact is not N'); continue
        # R1-12 (d): an opt-out date or a hold from the Clay tables stops the row, whatever do_not_contact says
        if (r.get('opt_out_date') or '').strip():
            print(f'skip {rid}: opt_out_date {r["opt_out_date"].strip()} is filled (an opt-out is never reversed; set do_not_contact = Y in Clay)'); continue
        if (r.get('hold_before_outreach') or '').strip().upper() == 'Y':
            why = (r.get('hold_reason') or r.get('hold_note') or '').strip()
            print(f'skip {rid}: hold_before_outreach = Y in the Clay table{": " + why if why else ""} (clear it in Clay first)'); continue
        ls = (r.get('lease_status') or '').strip()
        if msg['side'] == 'office' and ls in ('signed-not-occupied', 'moving-out'):
            print(f'skip {rid}: lease_status {ls} (not in its cluster office now: confirm on the lobby directory first, cluster-1-flatiron/HANDOFF.md)'); continue
        status = (r.get('status') or '').strip()
        if msg.get('stage') == 'conversion':
            # a post-call email goes to someone who has talked to you (review round 2: the cold-sequence rule refused them)
            if status not in CONVERSION_STATUSES:
                print(f'skip {rid}: status {status or "blank"} (a post-call email needs one of {", ".join(CONVERSION_STATUSES)})'); continue
        else:
            need = 'queued' if msg.get('touch') in ('1', '0') else 'contacted'
            if status not in (need, 'new' if need == 'queued' else need):
                print(f'skip {rid}: status {r.get("status")} (needs {need})'); continue
            # review round 3 (R3-02): a follow-up continues the thread the row is on, discovery or selling
            seq = (r.get('sequence') or '').strip()
            if msg.get('touch') in ('2', '3') and seq and msg.get('stage') in ('discovery', 'selling') and f'-{msg["stage"]}-' not in seq:
                print(f'skip {rid}: the row is on sequence {seq}; {a.message} belongs to a {msg["stage"]} thread (send that sequence\'s touch {msg["touch"]})'); continue
        if cap is not None and n >= cap:
            print(f'skip {rid}: the day\'s cap of {cap} cold first touches is reached (sending/warmup-schedule.csv; --over-cap to override)'); continue
        c = Ctx(r, st, msg['side'], msg['stage'], d)
        variant = a.variant or (r.get('sequence', '')[-1:] if r.get('sequence') else 'A')
        variant = variant if variant in ('A', 'B') else 'A'
        # R1-12 (a): a follow-up is "Re: <the subject touch 1 actually had>"
        first_subject = first_subject_for(msgs, msg, r, Ctx(r, st, msg['side'], msg['stage'], d), variant) if msg.get('touch') in ('2', '3') else None
        subj, body = fill_message(msg, c, variant, first_subject)
        fnd = [x for x in check(msg, subj, body, c, None) if x[0] == 'error' or 'nothing about this person' in x[1]]
        if fnd:
            print(f'skip {rid}: ' + '; '.join(t for _, t in fnd)); continue
        if 'NOT CLEARED TO NAME' in strip_marks(subj + body):
            print(f'skip {rid}: the referrer has not agreed to be named (referrer_ok_to_name); use the ordinary first touch'); continue
        if '(touch 1 subject)' in strip_marks(subj):
            print(f'skip {rid}: could not rebuild the touch 1 subject; copy it from the sent email'); continue
        is_mail = msg.get('channel', '').startswith('email') or msg.get('channel') in ('warm-intro', 'walk-in')
        to = r.get('work_email') if is_mail else r.get('contact_linkedin_url')
        if not (to or '').strip():
            print(f'skip {rid}: no {"work_email" if is_mail else "contact_linkedin_url"} on the row'); continue
        if msg.get('channel') == 'email' and msg.get('stage') in ('discovery', 'selling') and (r.get('email_status') or '').strip() != 'verified':
            print(f'skip {rid}: email_status is {r.get("email_status") or "blank"}, not verified (03: LinkedIn or walk-in instead)'); continue
        out = f'To: {to}\nSubject: {natural_dates(strip_marks(subj), True)}\n\n{natural_dates(strip_marks(body))}\n'
        # review round 2 (R2-18): A's row may hold a fresh reason to write that the founder has not turned into a hook yet
        hook_note = fresh_why_now_note(c, msg)
        if hook_note:
            print(f'note {rid}: {hook_note}')
            out = f'# NOTE (delete this line before sending): {hook_note}\n' + out
        # review round 3 (R3-07): what is still yours to fill or check goes on the draft itself, not only in this output
        left = [x for x in dict.fromkeys(re.findall(r'\[([^\[\]]+)\]', out)) if x not in FOUNDER_PLACEHOLDERS]
        todo = []
        if left:
            todo.append('fill before sending: ' + ', '.join(f'[{x}]' for x in left))
        if any(n_.startswith('COMPANY NAME:') for n_ in c.notes):
            todo.append(f'check "{brand_name()} LLC" letter for letter against the filed Articles')
        if todo:
            print(f'note {rid}: ' + '; '.join(todo))
            out = f'# NOTE (delete this line before sending): {"; ".join(todo)}\n' + out
        open(os.path.join(a.out, f'{rid}.txt'), 'w', encoding='utf-8').write(out)
        n += 1
    print(f'{n} drafts written to {a.out}. Nothing was sent.')
    return 0


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'lint'
    if cmd == 'examples':
        sys.exit(cmd_examples())
    if cmd == 'drafts':
        sys.exit(cmd_drafts(sys.argv[2:]))
    sys.exit(cmd_lint())
