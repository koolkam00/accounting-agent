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
        --message office-discovery-1 --date 2026-11-03 --out drafts/2026-11-03
      Writes one paste-ready .txt per row (subject, body, signature). It never
      sends anything. It refuses rows with do_not_contact = Y or status other
      than queued (touch 1) / contacted (touches 2 and 3), and any message the
      state does not unlock.

No network access. Standard library only.
"""
import csv, datetime as dt, html, json, os, re, sys

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
    try:
        return json.load(open(BRAND_JSON, encoding='utf-8'))['BRAND_NAME']
    except Exception:
        return 'Desk Drop'


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


def signature_block():
    txt = open(os.path.join(MSG_DIR, '02-commercial-footer.md'), encoding='utf-8').read()
    m = re.search(r'```text\n(.*?)\n```', txt, re.S)
    return m.group(1)


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


class Ctx:
    def __init__(self, row, state, side, stage, send_date, brand_row=None, slot_values=None):
        self.row, self.state, self.side, self.stage = row, state, side, stage
        self.date = send_date
        self.brand_row = brand_row or {}
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
        age = (c.date - dt.date.fromisoformat(d[:10])).days
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
    if v and 'unverified' not in v.lower() and v.lower() != 'unknown':
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
    'referrer_first_name': lambda c: mk('F', c.val('referrer_name').split()[0]) if c.val('referrer_name') else mk('B', '[NAME]'),
}
OPTIONAL = {'why_now_hook': opt_why_now, 'retailer_line': opt_retailer_line,
            'retailer_for_office': opt_retailer_for_office,
            'from_city': lambda c: opt_from_city(c, c.row), 'brand_from_city': lambda c: opt_from_city(c, c.brand_row)}


# ---------------------------------------------------------------- slots
SLOT_SEEN = set()


def S(text):
    SLOT_SEEN.add(text)
    return mk('S', text)


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
            return S(f'Five offices around {{CLUSTER}} have signed up, with about {hc} people in on a Tuesday by their own count.')
        if signed >= 1:
            n = 'One office' if signed == 1 else f'{NUMWORD[signed]} offices'
            verb = 'has' if signed == 1 else 'have'
            return S(f"{n} around {{CLUSTER}} {verb} signed up so far, with about {hc} people in on a Tuesday by their own count. No brand is invoiced until five have.")
        if yes >= 2:
            return S(f'{NUMWORD[yes]} offices around {{CLUSTER}} have said yes in principle; none has signed yet. No brand is invoiced until five have.')
        return S('[ROSTER LINE LOCKED: fewer than two offices have said yes; do not send brand selling copy]')
    if name == 'OFFER LINE':
        if ft < 3:
            return S("The founding offer: {product} in five offices for a week from [DROP DATE: Tue 2027-01-12], about 250 units. You get placement photos, depletion counts, an employee survey and a one-page report. It's $600 before you ship, plus your product and freight; your next two campaigns stay at $120 an office.")
        return S("The offer: {product} in ten offices for a week from [NEXT DROP DATE: Tue 2027-02-09], about 500 units. You get placement photos, depletion counts, an employee survey and a one-page report. It's $1,500 ($150 an office), half when you sign and half when we confirm placement, plus your product and freight.")
    if name == 'OFFER SHORT':
        if ft < 3:
            return S("Founding brands get five offices for a week from [DROP DATE: Tue 2027-01-12], about 250 units, with photos, counts, a short employee survey and a one-page report, for $600 plus the product.")
        return S("Ten offices for a week from [NEXT DROP DATE: Tue 2027-02-09], about 500 units, with photos, counts, a short employee survey and a one-page report, for $1,500 plus the product.")
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
    if name == 'FORMATION LINE':
        if st.get('llc_formed') == 'Y' and st.get('attorney_cleared') == 'Y':
            c.notes.append('FORMATION LINE: company formed and agreements cleared, left out'); return ''
        return S('The agreement and invoice come by [AGREEMENT DATE: Thu 2026-11-19]. Nothing is due before then.')
    if name == 'MOCK CARD LINE':
        cold = c.stage in ('selling', 'discovery')
        if st.get('mock_card_photo_ready') == 'Y' and not cold:
            return S('Attached is a photo of the card on a real pantry shelf.')
        if st.get('mock_card_photo_ready') != 'Y':
            c.notes.append('MOCK CARD LINE: no photo yet, the card described in words')
        return S("It's a 5 by 7 inch card: the brand's name, two sentences about it, the allergen line copied from the package, and a QR code to the survey.")
    if name == 'OFFICE ONE-PAGER LINE':
        if st.get('office_onepager_ready') == 'Y':
            return S(f"Attached is the one-page outline, with the first drop for {{company}} {planned(c)} the [FIRST DROP WEEK: week of Mon 2027-01-11].")
        c.notes.append('OFFICE ONE-PAGER LINE: one-pager not ready, nothing attached')
        return S("The first drop for {company} would be planned for the [FIRST DROP WEEK: week of Mon 2027-01-11].")
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
        c.notes.append('INTAKE PARAGRAPH: no intake form yet, six questions by reply')
        return S("The next step is six quick answers, which I'll turn into a one-page agreement for you to check and sign. {?[AGREEMENT TIMING LINE]}\n1. Roughly how many people are in on a Tuesday?\n2. Who receives deliveries, and in what window (for example, Tuesday 9 to 11)?\n3. Is it a walk-up, a front desk or a loading dock?\n4. Does your building need a certificate of insurance for deliveries: yes, no or unsure?\n5. Slack or email for the survey post?\n6. Any categories or allergens you want us to avoid?\n\nCould you reply with those this week?")
    if name == 'STEP 1 OPENER':
        if c.slot_values.get('_after_step0'):
            return S('As promised, here are the details.')
        return '{call_note_hook_line}'
    if name == 'DISCOVERY ONE-PAGER LINE':
        if st.get('discovery_onepager_ready') == 'Y':
            return S('Attached is the one-page description I mentioned.')
        c.notes.append('DISCOVERY ONE-PAGER LINE: one-pager not ready, left out'); return ''
    if name == 'PROPOSAL LINE':
        if st.get('proposal_ready') == 'Y':
            return S('Attached is the one-page proposal for {company}, with a map of the stores near the offices and a mock report page.')
        c.notes.append('PROPOSAL LINE: proposal not ready, short version in the email')
        return S('The full proposal follows; here is the short version.')
    if name == 'OFFICE HOURS LINE':
        h = st.get('office_hours_per_signing')
        if h:
            return S(f'Signing each office has taken me about {h} hours so far.')
        c.notes.append('OFFICE HOURS LINE: no hours logged yet, left out'); return ''
    return None


NUMWORD = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten'}


# ---------------------------------------------------------------- fill
def fill_text(text, c, sig=None):
    if '[PASTE desk-drop-legal-pack/11' in text:
        b = broker_block()
        if b:
            text = re.sub(r'\[PASTE desk-drop-legal-pack/11[^\]]*\]', lambda m: mk('X', b), text)
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
    # 4b. dates computed from the send date, so a slot never prints a day that has passed
    def later(base, n):
        return max(base, add_bd(c.date, n))
    agreement = later(dt.date(2026, 11, 19), 5) if not (c.state.get('attorney_cleared') == 'Y' and (c.side == 'office' or c.state.get('llc_formed') == 'Y')) else None
    if agreement:
        text = text.replace('[AGREEMENT DATE: Thu 2026-11-19]', f'[AGREEMENT DATE: {fmt(agreement)}]')
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


def fill_message(msg, c, variant='A', first_subject=None):
    sig = signature_block() if msg.get('channel') in ('email', 'warm-intro', 'walk-in') else ''
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
    for m in re.finditer(r'\[([A-Z][A-Z \-]+): (Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{4}-\d\d-\d\d)\]', full + ' ' + plain_subj):
        d = dt.date.fromisoformat(m.group(3))
        if DOW[d.weekday()] != m.group(2):
            f.append(('error', f'{m.group(0)}: weekday wrong'))
        if 'DROP DATE' in m.group(1) and not drop_ok(d):
            f.append(('error', f'{m.group(0)}: not a legal drop day (Tue or Wed, window clear of blackouts)'))
    if msg['side'] == 'brand' and msg.get('stage') in ('selling', 'conversion') and '2027-01-12' in full + ' ' + plain_subj \
            and msg['id'] not in ('brand-conversion-6', 'brand-conversion-7', 'brand-conversion-8', 'brand-conversion-9', 'brand-conversion-10') \
            and c.date > LAST_OFFER_CZ and not c.slot_values.get('_moved'):
        f.append(('error', f'sent {c.date} offering the Tue 2027-01-12 drop: after Tue 2026-12-08 a new brand cannot be invoiced, paid and insured before ship-by; offer [NEXT DROP DATE]'))
    if msg.get('stage') in ('discovery', 'selling') and touch == '1' and msg.get('channel') in ('email', 'linkedin') \
            and '\x01F' not in body.split('\x01G')[0]:
        f.append(('warn', 'nothing about this person or company is printed: fix the row before sending'))
    for name in COMPUTED_SLOTS:
        if f'[{name}]' in full:
            f.append(('error', f'computed slot [{name}] was not filled'))
    if 'LOCKED' in full:
        f.append(('error', 'a locked slot was used: this message is not unlocked by the state'))
    for g in gates(msg, c.state):
        f.append(('error', g))
    if ch in ('email', 'warm-intro', 'walk-in') and 'no thanks' not in full:
        f.append(('error', 'footer missing'))
    return f


COMPUTED_SLOTS = ['OFFICE OPENER', 'OFFICE PROGRESS LINE', 'ROSTER LINE', 'OFFER LINE', 'OFFER SHORT', 'FOUNDING LINE',
                  'FIRST BRAND LINE', 'INSURANCE LINE', 'FORMATION LINE', 'MOCK CARD LINE', 'OFFICE HOURS LINE',
                  'OFFICE ONE-PAGER LINE', 'LAST CHECK LINE', 'AGREEMENT TIMING LINE', 'INTAKE PARAGRAPH', 'PROPOSAL LINE',
                  'STEP 1 OPENER', 'DISCOVERY ONE-PAGER LINE']
LAST_OFFER_CZ = dt.date(2026, 12, 8)   # derived: yes + 5 business days to form + 5 to pay lands before ship-by Tue 2026-12-22


def gates(msg, st):
    g, i = [], msg['id']
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
    if i == 'office-conversion-6' and st.get('attorney_cleared') != 'Y':
        g.append('attorney_cleared = N: the office agreement cannot go out')
    if i in ('brand-conversion-6', 'brand-conversion-7', 'brand-conversion-8') and not (st.get('llc_formed') == 'Y' and st.get('attorney_cleared') == 'Y'):
        g.append('llc_formed or attorney_cleared = N: no agreement, invoice or certificate request yet')
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
        md = f'{MONTHS[x.month - 1]} {x.day}'
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
        c = Ctx(row, st_step, msg['side'] if msg['side'] in ('office', 'brand') else ex['side'], msg['stage'], d, brand_row, sv)
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


def cmd_lint():
    """Fill every message once with each SAMPLE row of its side, in a state that unlocks it."""
    msgs = load_messages()
    exdir, rows, states, exs = load_examples()
    st = dict(states['_base']); st.update(states['lint-all-unlocked'])
    bad = 0
    for mid, msg in msgs.items():
        side = msg['side'] if msg['side'] in ('office', 'brand') else 'office'
        for r in rows.values():
            if r['side'] != side:
                continue
            c = Ctx(r, st, side, msg['stage'], dt.date(2026, 11, 17), next((x for x in rows.values() if x['side'] == 'brand'), {}),
                    {'TIME OPTION 1': 'Tue 2026-11-24 at 10:00', 'TIME OPTION 2': 'Wed 2026-11-25 at 14:00'})
            subj, body = fill_message(msg, c, 'A', 'SAMPLE subject')
            for k, t in check(msg, subj, body, c, None):
                if k == 'error':
                    bad += 1
                print(f'{mid} [{r["row_id"]}] {k}: {t}')
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


def cmd_drafts(args):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--daily', required=True); ap.add_argument('--message', required=True)
    ap.add_argument('--date', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--state', default=os.path.join(MSG_DIR, '04-slot-state.csv'))
    ap.add_argument('--variant', default=None)
    a = ap.parse_args(args)
    msgs = load_messages(); msg = msgs[a.message]
    st = load_state(a.state)
    d = dt.date.fromisoformat(a.date)
    os.makedirs(a.out, exist_ok=True)
    n = 0
    for r in read_csv(a.daily):
        if r.get('side') and r['side'] != msg['side'] and msg['side'] in ('office', 'brand'):
            print(f'skip {r.get("row_id")}: a {r["side"]} row, and {a.message} is for {msg["side"]}s'); continue
        if (r.get('do_not_contact') or 'Y').strip().upper() != 'N':
            print(f'skip {r.get("row_id")}: do_not_contact is not N'); continue
        need = 'queued' if msg.get('touch') in ('1', '0') else 'contacted'
        if (r.get('status') or '').strip() not in (need, 'new' if need == 'queued' else need):
            print(f'skip {r.get("row_id")}: status {r.get("status")} (needs {need})'); continue
        c = Ctx(r, st, msg['side'], msg['stage'], d)
        variant = a.variant or (r.get('sequence', '')[-1:] if r.get('sequence') else 'A')
        subj, body = fill_message(msg, c, variant if variant in 'AB' else 'A')
        fnd = [x for x in check(msg, subj, body, c, None) if x[0] == 'error' or 'nothing about this person' in x[1]]
        if fnd:
            print(f'skip {r.get("row_id")}: ' + '; '.join(t for _, t in fnd)); continue
        to = r.get('work_email') if msg.get('channel') in ('email', 'warm-intro', 'walk-in') else r.get('contact_linkedin_url')
        out = f'To: {to}\nSubject: {natural_dates(strip_marks(subj), True)}\n\n{natural_dates(strip_marks(body))}\n'
        open(os.path.join(a.out, f'{r.get("row_id")}.txt'), 'w', encoding='utf-8').write(out)
        n += 1
    print(f'{n} drafts written to {a.out}. Nothing was sent.')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'lint'
    if cmd == 'examples':
        sys.exit(cmd_examples())
    if cmd == 'drafts':
        sys.exit(cmd_drafts(sys.argv[2:]))
    sys.exit(cmd_lint())
