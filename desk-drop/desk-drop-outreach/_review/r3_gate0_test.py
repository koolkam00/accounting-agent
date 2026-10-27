"""Round 3 reviewer test of the tracker's Gate 0 formulas (cases not covered by rounds 1 and 2).
Writes SAMPLE rows into a COPY of the blank workbook, recalculates it with LibreOffice headless,
and prints the Scorecard values beside a hand count.
Run: python3 -I r3_gate0_test.py <path to conversation-tracker.xlsx> <scratch dir>
It writes only to the scratch dir. Never point it at the deliverable folder as the scratch dir."""
import datetime as dt, os, shutil, subprocess, sys
import openpyxl

SRC, WORK = sys.argv[1], sys.argv[2]
os.makedirs(WORK, exist_ok=True)
D = lambda s: dt.datetime.fromisoformat(s)


def build(name, offices, brands, as_of='2026-11-20'):
    copy = os.path.join(WORK, name + '.xlsx')
    shutil.copy(SRC, copy)
    wb = openpyxl.load_workbook(copy)
    cfg = wb['Config']
    for r in range(1, 40):
        if cfg.cell(r, 1).value == 'as_of_date':
            cfg.cell(r, 2).value = D(as_of)
        if cfg.cell(r, 1).value == 'include_sample':
            cfg.cell(r, 2).value = 'Y'
    for ws, rows in ((wb['Office_Log'], offices), (wb['Brand_Log'], brands)):
        hdr = [c.value for c in ws[1]]
        for i, row in enumerate(rows):
            for k, v in row.items():
                ws.cell(2 + i, hdr.index(k) + 1).value = v
    wb.save(copy)
    out = os.path.join(WORK, 'out')
    os.makedirs(out, exist_ok=True)
    subprocess.run(['soffice', '--headless', '--calc', '--convert-to', 'xlsx', '--outdir', out, copy],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    return openpyxl.load_workbook(os.path.join(out, name + '.xlsx'), data_only=True)


def row(sc, label):
    for i in range(1, 200):
        if sc.cell(i, 1).value == label:
            return [sc.cell(i, c).value for c in range(2, 6)]
    return None


O = lambda rid, co, d, **kw: dict(row_id=rid, company=co, call_date=d, **kw)
B = lambda rid, co, d, **kw: dict(row_id=rid, company=co, call_date=d, **kw)

# Scenario E: neutral follow-up rows, a yes completed on a second call, and the designed
# "wrong person -> new Clay row" flow, which gives one office (or brand) two row_ids.
offices_e = [
    O('SAMPLE-R3-E1', 'SAMPLE Alpha', D('2026-11-02'), yes_in_principle='Y', pantry_owner_named='Y', receiving_window='Tue 9-11'),
    O('SAMPLE-R3-E1', 'SAMPLE Alpha', D('2026-11-09'), pantry_owner_named='Y'),  # follow-up, no answer: neutral
    O('SAMPLE-R3-E2', 'SAMPLE Beta', D('2026-11-03'), yes_in_principle='Y', pantry_owner_named='N', receiving_window=''),
    O('SAMPLE-R3-E2', 'SAMPLE Beta', D('2026-11-10'), yes_in_principle='Y', pantry_owner_named='Y', receiving_window='Wed 8'),
    # one company, two contacts: the office manager (wrong person for the pantry) and the workplace lead she named
    O('SAMPLE-R3-E3a', 'SAMPLE Gamma', D('2026-11-04'), yes_in_principle='Y', pantry_owner_named='Y', receiving_window='Tue 10'),
    O('SAMPLE-R3-E3b', 'SAMPLE Gamma', D('2026-11-06'), yes_in_principle='Y', pantry_owner_named='Y', receiving_window='Tue 10'),
    O('SAMPLE-R3-E5', 'SAMPLE Epsilon', D('2026-11-14'), yes_in_principle='Y', pantry_owner_named='Y', receiving_window='Tue 9'),  # Saturday after Gate 0
    O('SAMPLE-R3-E8', 'SAMPLE Theta', D('2026-11-04'), yes_in_principle='maybe', pantry_owner_named='N', receiving_window=''),
    O('SAMPLE-R3-E8', 'SAMPLE Theta', D('2026-11-11'), yes_in_principle='Y', pantry_owner_named='Y', receiving_window='Tue 8'),  # maybe then yes
]
brands_e = [
    B('SAMPLE-R3-F1', 'SAMPLE One', D('2026-11-02'), controls_budget='Y', wtp_before_usd=700),
    B('SAMPLE-R3-F1', 'SAMPLE One', D('2026-11-09')),  # follow-up, nothing named: neutral
    B('SAMPLE-R3-F2', 'SAMPLE Two', D('2026-11-03'), controls_budget='Y', wtp_before_usd=700),
    B('SAMPLE-R3-F2', 'SAMPLE Two', D('2026-11-10'), wtp_before_usd=800),  # later number, control not re-asked
    B('SAMPLE-R3-F3a', 'SAMPLE Three', D('2026-11-04'), controls_budget='Y', wtp_before_usd=600),  # founder
    B('SAMPLE-R3-F3b', 'SAMPLE Three', D('2026-11-05'), controls_budget='Y', wtp_before_usd=600),  # co-founder, same brand
    B('SAMPLE-R3-F4', 'SAMPLE Four', D('2026-11-06'), controls_budget='y', wtp_before_usd=500),
    B('SAMPLE-R3-F5', 'SAMPLE Five', D('2026-11-09'), controls_budget='Y', wtp_before_usd=300, wtp_after_usd=600),
    B('SAMPLE-R3-F7', 'SAMPLE Seven', D('2026-11-12'), controls_budget='Y', wtp_after_usd=500),
]
# Hand count at Gate 0 (Fri 2026-11-13), distinct organisations, as the plan reads "5 of 15 offices":
#   office conversations: Alpha, Beta, Gamma, Theta = 4 offices (5 row_ids); yes: Alpha, Beta, Gamma, Theta = 4.
#   brand conversations: One, Two, Three, Four, Five, Seven = 6 brands (7 row_ids); yes (lenient): 6; strict: One, Two, Three, Four = 4.

# Scenario G: an office below the hard floor (30 on a Tuesday) and one inside coworking say yes.
offices_g = [O('SAMPLE-R3-G%d' % i, 'SAMPLE G%d' % i, D('2026-11-0%d' % (i + 1)), yes_in_principle='Y', pantry_owner_named='Y',
               receiving_window='Tue 9', tuesday_headcount=60) for i in range(1, 5)]
offices_g.append(O('SAMPLE-R3-G5', 'SAMPLE G5', D('2026-11-09'), yes_in_principle='Y', pantry_owner_named='Y', receiving_window='Tue 9',
                   tuesday_headcount=12, headcount_verbatim='SAMPLE: about twelve of us in on a Tuesday'))
brands_g = []
# Hand count: 4 qualifying offices (G5 is under the plan's hard floor of 30); a reader of the plan would not call this PASS.

for name, off, br in (('r3-E', offices_e, brands_e), ('r3-G', offices_g, brands_g)):
    wb = build(name, off, br)
    sc = wb['Scorecard']
    print('==', name, '(columns: Fri wk1, Fri wk2, Gate 0, As of 2026-11-20)')
    for lab in ['Office conversations held', 'Yes in principle, pantry owner named, receiving window named',
                'Gate 0, office side', 'Yes in principle, any (owner or window may be missing)',
                'Withdrawn after a yes (latest answer N or maybe): not counted',
                'Brand conversations held', 'Would pay $500 or more and controls the budget', 'Gate 0, brand side',
                'Strict read: named $500 or more BEFORE hearing $1,500, and controls the budget',
                'Withdrawn after saying $500 or more (a later call: no budget control, or a lower number): not counted',
                'Gate 0 result']:
        print('  ', lab, row(sc, lab))
    for i in range(1, 200):
        v = sc.cell(i, 1).value
        if v and str(v).startswith('Sentence for the Gate 0'):
            print('  ', v, sc.cell(i, 2).value)
    # any data check that mentions headcount or duplicate company
    for i in range(100, 200):
        v = sc.cell(i, 1).value
        if v and any(w in str(v).lower() for w in ('headcount', 'duplicate', 'same company', 'floor')):
            print('   data check', i, v, [sc.cell(i, c).value for c in range(2, 4)])
