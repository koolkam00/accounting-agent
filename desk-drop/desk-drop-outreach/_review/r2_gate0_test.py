"""Round 2 reviewer test of the tracker's Gate 0 formulas (independent of round 1's cases).
Writes SAMPLE rows into a COPY of the blank workbook, recalculates it with LibreOffice headless,
and prints the Scorecard values next to the values a hand count gives.
Run: python3 -I r2_gate0_test.py <path to conversation-tracker.xlsx> <scratch dir>
Never run it on the deliverable itself: it writes only to the scratch dir."""
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
    for r in range(1, 30):
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
    for i in range(1, 160):
        if sc.cell(i, 1).value == label:
            return [sc.cell(i, c).value for c in range(2, 6)]
    return None


O = lambda rid, d, **kw: dict(row_id=rid, company='SAMPLE co', call_date=d, **kw)
B = lambda rid, d, **kw: dict(row_id=rid, company='SAMPLE brand', call_date=d, **kw)

# Scenario A: edge cases on both sides.
offices_a = [
    O('SAMPLE-R2-O1', D('2026-10-27'), yes_in_principle='Y', pantry_owner_named='Y', receiving_window='Tue 9-11'),
    O('SAMPLE-R2-O2', D('2026-11-03'), yes_in_principle='Y', pantry_owner_named='Y', receiving_window='   '),  # blank window: not a yes
    O('SAMPLE-R2-O3', D('2026-11-05'), yes_in_principle='Y', pantry_owner_named='Y', receiving_window='Tue 8-10'),
    O('SAMPLE-R2-O3', D('2026-11-12'), yes_in_principle='N', pantry_owner_named='Y', receiving_window=''),  # retracted yes
    O('SAMPLE-R2-O4', D('2026-11-13T14:30'), yes_in_principle='Y', pantry_owner_named='Y', receiving_window='Wed 9'),  # Gate 0 day, with a time
    O('SAMPLE-R2-O5', D('2026-11-13'), yes_in_principle='Y', pantry_owner_named='Y', receiving_window='Tue'),
    O('SAMPLE-R2-O6', D('2026-11-06'), yes_in_principle='y', pantry_owner_named='y', receiving_window='Tue'),  # lower case
    O('SAMPLE-R2-O7', D('2026-11-10'), yes_in_principle='Y', pantry_owner_named='Y', receiving_window='Tue 9'),
    O('SAMPLE-R2-O8', D('2026-11-16'), yes_in_principle='Y', pantry_owner_named='Y', receiving_window='Tue 9'),  # after Gate 0
    O('SAMPLE-R2-O9', D('2026-11-09'), yes_in_principle='maybe', pantry_owner_named='N', receiving_window=''),
]
brands_a = [
    B('SAMPLE-R2-B1', D('2026-10-29'), controls_budget='Y', wtp_before_usd=500),
    B('SAMPLE-R2-B2', D('2026-11-02'), controls_budget='unsure', wtp_before_usd=900),  # not budget owner
    B('SAMPLE-R2-B3', D('2026-11-04'), controls_budget='Y', wtp_before_usd=450, wtp_after_usd=1500),  # lenient yes, strict no
    B('SAMPLE-R2-B4', D('2026-11-06'), controls_budget='Y', wtp_before_usd=600),
    B('SAMPLE-R2-B4', D('2026-11-11'), controls_budget='Y', wtp_before_usd=0, wtp_before_verbatim='SAMPLE: budget cut, nothing this year'),  # retracted
    B('SAMPLE-R2-B5', D('2026-11-12'), controls_budget='Y', wtp_before_usd='$600'),  # number typed as text
    B('SAMPLE-R2-B6', D('2026-11-13'), controls_budget='Y', wtp_before_usd=1000),
]
# Hand count at the Gate 0 cut-off (Fri 2026-11-13), as the plan reads Gate 0:
#  offices: O1, O5, O6, O7 = 4 sure; O3 retracted (plan: not a yes on 11-13); O4 is a Gate 0 day call.
#  brands: B1, B3 (lenient), B6 = 3 sure; B4 retracted on 11-11; B5 is a $600 answer typed as text.

# Scenario B: the Gate 0 day with too few conversations to run the plan's test.
offices_b = [O('SAMPLE-R2-P%d' % i, D('2026-11-0%d' % (i + 2)), yes_in_principle='Y' if i <= 3 else 'N',
               pantry_owner_named='Y', receiving_window='Tue 9') for i in range(1, 7)]
brands_b = [B('SAMPLE-R2-Q%d' % i, D('2026-11-0%d' % (i + 2)), controls_budget='Y',
              wtp_before_usd=600 if i <= 2 else 200) for i in range(1, 6)]

# Scenario C: a withdrawn yes decides the gate. Offices: five yeses, the fifth withdrawn on 11-12.
# Brands: three at $500 or more, the third withdrawn on 11-11. Plan reading on 11-13: 4 offices, 2 brands.
offices_c = [O('SAMPLE-R2-C%d' % i, D('2026-11-0%d' % (i + 1)), yes_in_principle='Y', pantry_owner_named='Y',
               receiving_window='Tue 9') for i in range(1, 6)]
offices_c.append(O('SAMPLE-R2-C5', D('2026-11-12'), yes_in_principle='N', pantry_owner_named='Y', receiving_window='',
                   objections_verbatim='SAMPLE: facilities said no after all'))
brands_c = [B('SAMPLE-R2-D%d' % i, D('2026-11-0%d' % (i + 1)), controls_budget='Y', wtp_before_usd=700,
              wtp_before_verbatim='SAMPLE: about 700') for i in range(1, 4)]
brands_c.append(B('SAMPLE-R2-D3', D('2026-11-11'), controls_budget='Y', wtp_before_usd=0,
                  wtp_before_verbatim='SAMPLE: budget frozen, nothing until Q3'))

for name, off, br in (('r2-A', offices_a, brands_a), ('r2-B', offices_b, brands_b), ('r2-C', offices_c, brands_c)):
    wb = build(name, off, br)
    sc = wb['Scorecard']
    print('==', name)
    for lab in ['Office conversations held', 'Yes in principle, pantry owner named, receiving window named',
                'Gate 0, office side', 'Yes in principle, any (owner or window may be missing)',
                'Brand conversations held', 'Would pay $500 or more and controls the budget', 'Gate 0, brand side',
                'Strict read: named $500 or more BEFORE hearing $1,500, and controls the budget',
                'Median brand number before $1,500 was mentioned, USD per campaign', 'Gate 0 result']:
        print('  ', lab, row(sc, lab))
    for i in range(1, 160):
        v = sc.cell(i, 1).value
        if v and (str(v).startswith('Sentence for the Gate 0') or 'text' in str(v).lower() or 'not a date' in str(v).lower()):
            print('  ', i, v, [sc.cell(i, c).value for c in range(2, 7)])
    bl = wb['Brand_Log']
    hdr = [c.value for c in bl[1]]
    for r in range(2, 2 + len(br)):
        print('   brand log', bl.cell(r, 1).value, 'sync:', bl.cell(r, hdr.index('calc_sync_issue') + 1).value,
              'missing_text:', bl.cell(r, hdr.index('calc_wtp_missing_text') + 1).value)
