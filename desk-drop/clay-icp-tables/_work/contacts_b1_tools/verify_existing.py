import csv, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch import get, text
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
rows = [x for x in csv.DictReader(open(os.path.join(W, '..', 'brands.csv'))) if x['top60'] == 'Y']
rows.sort(key=lambda x: int(x['rank']))
def norm(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
out = []
for x in rows:
    for slot, fn, ln, ti, url, asfound, status in [
        ('founder', x['first_name'], x['last_name'], x['title'], x['contact_profile_url'], x['contact_name_as_found'], x['contact_status']),
        ('backup', x['backup_first_name'], x['backup_last_name'], x['backup_title'], x['backup_contact_profile_url'], x['backup_contact_name_as_found'], x['backup_contact_status'])]:
        if not asfound and not fn:
            continue
        name = asfound or (fn + ' ' + ln)
        if not url:
            out.append(dict(rank=x['rank'], row_id=x['row_id'], company=x['company'], slot=slot, name=name, title=ti, status_in=status, url='', http='', full_name_found='', first_found='', last_found='', context=''))
            continue
        st, p = get(url, 'verify')
        t = text(p); tn = norm(t)
        parts = name.split()
        first = parts[0]; last = parts[-1] if len(parts) > 1 else ''
        ff = norm(first) in tn
        lf = bool(last) and norm(last) in tn
        full = norm(name) in tn
        ctx = ''
        key = norm(last) if last else norm(first)
        i = tn.find(norm(name)) if full else tn.find(key)
        if i >= 0:
            ctx = t[max(0, i-160): i+200]
        out.append(dict(rank=x['rank'], row_id=x['row_id'], company=x['company'], slot=slot, name=name, title=ti, status_in=status, url=url, http=st.split()[0], full_name_found='Y' if full else 'N', first_found='Y' if ff else 'N', last_found='Y' if lf else 'N', context=ctx))
        print(x['rank'], slot, name, st.split()[0], full, ff, lf, flush=True)
with open(os.path.join(W, 'contacts_b1_verify_existing.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader(); w.writerows(out)
