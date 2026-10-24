"""Independent QR audit (reviewer). Rasterize every tent-card page, decode every QR with zxing-cpp
(not the builder's jsQR), read the card's printed office/campaign line, resolve the short link through
the Short.io import CSV (the file the founder uploads), and check the destination form + card code.
Usage: python3 qr_audit.py <kit_dir> <links_dir> <tracker.xlsx>"""
import sys, os, re, csv, subprocess, tempfile, glob, urllib.parse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'py'))
import zxingcpp
from PIL import Image
import pypdf, openpyxl
kit, links, trk = sys.argv[1:4]
imp = {}
for f in glob.glob(os.path.join(links, 'shortio-import-*.csv')):
    for r in csv.DictReader(open(f)):
        imp[r['path']] = r['original_url']
wb = openpyxl.load_workbook(trk, data_only=True)
ws = wb['campaigns']; hdr = [c.value for c in ws[1]]
tpl = {}
for row in ws.iter_rows(min_row=2, values_only=True):
    if row[0]:
        tpl[row[0]] = row[hdr.index('survey_prefill_template')]
rd = pypdf.PdfReader(os.path.join(kit, 'cards.pdf'))
tmp = tempfile.mkdtemp()
subprocess.run(['pdftoppm', '-r', '150', '-png', os.path.join(kit, 'cards.pdf'), os.path.join(tmp, 'p')], check=True)
pages = sorted(glob.glob(os.path.join(tmp, 'p*.png')))
bad = 0; n = 0
for i, pg in enumerate(pages):
    txt = rd.pages[i].extract_text()
    m = re.search(r'Card (\S+) · (\S+)', txt)
    oid, cid = (m.group(1), m.group(2)) if m else (None, None)
    im = Image.open(pg)
    w, h = im.size
    res = []
    for crop in (im, im.crop((0, h//2, w, h)), im.crop((0, 0, w, h//2)).rotate(180)):
        for r in zxingcpp.read_barcodes(crop):
            res.append(r.text)
    found = sorted(set(res))
    probs = []
    if not oid: probs.append('no card id text')
    if len(found) != 1: probs.append('decoded %d distinct codes %s' % (len(found), found))
    for u in found:
        slug = u.rsplit('/', 1)[-1]
        dest = imp.get(slug)
        if not dest: probs.append('slug %s not in Short.io import' % slug); continue
        q = urllib.parse.parse_qs(urllib.parse.urlparse(dest).query)
        code = [v[0] for k, v in q.items() if k.startswith('entry.')]
        if code != ['%s.%s' % (cid, oid)]: probs.append('card code %s != %s.%s' % (code, cid, oid))
        t = tpl.get(cid) or ''
        if not t or dest.split('?')[0] != t.split('?')[0]: probs.append('form %s != campaign form %s' % (dest.split('?')[0], t.split('?')[0]))
        if not slug.endswith('-q'): probs.append('not a QR (-q) link')
        # the printed short text must match the QR
        flat = txt.replace('\n', '')
        if u.replace('https://', '') not in flat: probs.append('printed link text differs from QR')
    n += 1
    bad += bool(probs)
    print(('OK ' if not probs else 'BAD') + ' page %d %s %s %s %s' % (i + 1, oid, cid, found, '; '.join(probs)))
# PNG QR files
for f in sorted(glob.glob(os.path.join(links, 'qr', '*.png'))):
    r = zxingcpp.read_barcodes(Image.open(f))
    slug = os.path.basename(f)[:-4]
    ok = len(r) == 1 and r[0].text.endswith('/' + slug) and slug in imp
    n += 1; bad += not ok
    if not ok: print('BAD png', f, [x.text for x in r])
print('checked %d, bad %d' % (n, bad))
