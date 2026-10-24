import sys, os, datetime as dt
SB = '/home/user/accounting-agent/desk-drop/campaign-ops/_review/sandbox/campaign-ops'
sys.path.insert(0, SB + '/tools')
os.chdir(SB)
import scenarios as S, dryrun as DR, opscal, openpyxl
out = '/home/user/accounting-agent/desk-drop/campaign-ops/_review/work/exc'
scn = S.exception()
day = dt.date.fromisoformat(sys.argv[1])
p = DR.build_snapshot(scn, day, os.path.join(out, 'in-%s.xlsx' % day))
snap = os.path.join(out, 'snap-%s.xlsx' % day)
tr, errs, n = DR.recalc_and_read(p, snap)
bad = [b for b in DR.TR.compare(tr) if not b.startswith('no cached')]
print('formula errors', n, errs[:5], 'disagreements', len(bad), bad[:5])
checks, msgs, rel = DR.dashboard_checks(snap)
print('dashboard', checks)
for m in msgs:
    if 'CMP-006' in m or 'DRP-003' in m: print('  ', m)
wb = openpyxl.load_workbook(snap, data_only=True)
ws = wb['campaigns']; hdr = [c.value for c in ws[1]]
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0] == 'SAMPLE-CMP-006':
        d = dict(zip(hdr, row))
        for k in ('offices_approved', 'offices_contracted', 'units_allocated', 'units_to_ship', 'units_received', 'reserve_on_hand', 'leftover_on_hand',
                  'units_delivered', 'units_placed', 'units_placed_within_1bd', 'placed_share_1bd', 'units_topped_up', 'units_depleted_day5',
                  'survey_responses', 'survey_responses_min_office', 'offices_under_5', 'qr_scans', 'revenue_usd', 'deposit_usd', 'invoice_paid_date',
                  'gate2_placed', 'gate2_responses', 'photo_compliance', 'contribution_usd', 'contribution_per_hour_usd', 'ship_release', 'checks'):
            print('  %-28s %s' % (k, d.get(k)))
ws = wb['approvals']; hdr = [c.value for c in ws[1]]
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0] == 'SAMPLE-CMP-006' and row[1] in ('SAMPLE-O-006', 'SAMPLE-O-001'):
        d = dict(zip(hdr, row))
        print('  approvals', row[1], {k: d[k] for k in ('approved', 'office_label', 'units_allocated', 'units_delivered', 'units_placed', 'remaining_day5', 'units_depleted_day5', 'survey_responses', 'qr_scans', 'checks')})
ws = wb['drops']; hdr = [c.value for c in ws[1]]
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0] == 'SAMPLE-DRP-003':
        d = dict(zip(hdr, row)); print('  drop', {k: d[k] for k in ('stops', 'revenue_usd', 'direct_cost_usd', 'cost_per_stop_usd', 'hours', 'contribution_usd', 'contribution_per_hour_usd', 'gate2_placed_share', 'gate2_min_responses')})
ws = wb['stops']; hdr = [c.value for c in ws[1]]
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0] == 'SAMPLE-DRP-003' and row[1] == 'SAMPLE-O-006':
        d = dict(zip(hdr, row)); print('  stop O-006', d.get('outcome'), d.get('checks'))
ws = wb['offices']; hdr = [c.value for c in ws[1]]
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0] == 'SAMPLE-O-006':
        d = dict(zip(hdr, row)); print('  office O-006 declines', d.get('declines'), 'drops_so_far', d.get('drops_so_far'))
