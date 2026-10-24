import json,sys,re
sys.path.insert(0,'.')
from face import segs, xy, dist_line, hn, norm
AVES=['5 AVE','AVE OF THE AMERICAS','PARK AVE S','MADISON AVE','BROADWAY','UNIVERSITY PL','UNION SQ W','UNION SQ E','IRVING PL','LEXINGTON AVE','7 AVE','3 AVE','4 AVE']
def dname(P,name):
    best=1e9
    for nm,p,pts in segs:
        if nm==name:
            best=min(best,dist_line(P,pts)[0])
    return round(best)
def test(addr,lat,lon):
    m=re.match(r'(\d+)\s+(.*)',addr.strip()); n=int(m.group(1)); st=norm(m.group(2))
    P=xy(lat,lon)
    cand=[]
    for name,p,pts in segs:
        if name!=st: continue
        for side in ('l','r'):
            lo,hi=hn(p[side+'_low_hn']),hn(p[side+'_high_hn'])
            if lo is None or hi is None: continue
            if min(lo,hi)<=n<=max(lo,hi) and lo%2==n%2:
                d,cr,i=dist_line(P,pts); cand.append((d,side,cr))
    if not cand: return dict(addr=addr,result='no range')
    cand.sort(); d,side,cr=cand[0]; pin_side='l' if cr>0 else 'r'
    mm=re.match(r'([EW]) (\d+) ST',st)
    if mm:
        k=int(mm.group(2)); par={f'{mm.group(1)} {k-1} ST':None,f'{mm.group(1)} {k+1} ST':None}
    else:
        par={a:None for a in AVES if a!=st}
    for k in par: par[k]=dname(P,k)
    near_par=min(par.items(),key=lambda kv:kv[1])
    return dict(addr=addr,street=st,d_addr=round(d),side_ok=side==pin_side,nearest_parallel=near_par,margin=near_par[1]-round(d),PASS=(side==pin_side and near_par[1]-round(d)>=15))
for line in sys.stdin:
    a,lat,lon=line.rstrip('\n').split('|'); print(json.dumps(test(a,float(lat),float(lon))))
