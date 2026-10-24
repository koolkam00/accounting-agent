# Independent block-face test (reviewer round 2). Not the builder's code.
import json, math, sys, re
G='/home/user/accounting-agent/desk-drop/cluster-1-flatiron/_work/geo/streets_raw.geojson'
g=json.load(open(G))
LAT0,LON0=40.74,-73.99
KX=math.cos(math.radians(LAT0))*111320; KY=110540
def xy(lat,lon): return ((lon-LON0)*KX,(lat-LAT0)*KY)
segs=[]
for f in g['features']:
    p=f['properties']; geom=f['geometry']
    lines=geom['coordinates'] if geom['type']=='MultiLineString' else [geom['coordinates']]
    for ln in lines:
        pts=[xy(c[1],c[0]) for c in ln]
        segs.append((p['stname_label'],p,pts))
def hn(s):
    try: return int(re.sub(r'\D','',s.split('-')[0])) if s else None
    except: return None
def ptseg(P,A,B):
    ax,ay=A;bx,by=B;px,py=P
    dx,dy=bx-ax,by-ay; L2=dx*dx+dy*dy
    t=0 if L2==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L2))
    qx,qy=ax+t*dx,ay+t*dy
    cross=dx*(py-ay)-dy*(px-ax)  # >0 => left of A->B
    return math.hypot(px-qx,py-qy),cross,t
def dist_line(P,pts):
    best=(1e9,0,None)
    for i in range(len(pts)-1):
        d,cr,t=ptseg(P,pts[i],pts[i+1])
        if d<best[0]: best=(d,cr,i)
    return best
def norm(street):
    s=street.upper()
    s=s.replace('AVENUE OF THE AMERICAS','AVE OF THE AMERICAS').replace('FIFTH AVENUE','5 AVE').replace('PARK AVENUE SOUTH','PARK AVE S').replace('MADISON AVENUE','MADISON AVE')
    s=s.replace('UNION SQUARE WEST','UNION SQ W').replace('UNION SQUARE EAST','UNION SQ E').replace('SIXTH AVENUE','AVE OF THE AMERICAS').replace('UNIVERSITY PLACE','UNIVERSITY PL')
    m=re.match(r'(EAST|WEST) (\d+)(ST|ND|RD|TH) STREET',s)
    if m: s=('E' if m.group(1)=='EAST' else 'W')+' '+m.group(2)+' ST'
    m=re.match(r'(\d+)(ST|ND|RD|TH) AVENUE',s)
    if m: s=m.group(1)+' AVE'
    return s
def test(addr,lat,lon):
    m=re.match(r'(\d+)\s+(.*)',addr.strip()); n=int(m.group(1)); st=norm(m.group(2))
    P=xy(lat,lon)
    # segments of addressed street whose range holds n
    cand=[]
    for name,p,pts in segs:
        if name!=st: continue
        for side in ('l','r'):
            lo,hi=hn(p[side+'_low_hn']),hn(p[side+'_high_hn'])
            if lo is None or hi is None: continue
            if min(lo,hi)<=n<=max(lo,hi) and lo%2==n%2:
                d,cr,i=dist_line(P,pts)
                cand.append((d,side,cr,p))
    if not cand: return dict(addr=addr,street=st,result='no range match')
    cand.sort(key=lambda c:c[0]); d,side,cr,p=cand[0]
    pin_side='l' if cr>0 else 'r'
    # nearest other street (any other name) distance
    others=[]
    for name,pp,pts in segs:
        if name==st: continue
        dd=dist_line(P,pts)[0]
        others.append((dd,name))
    others.sort()
    seen=[];o2=[]
    for dd,nm in others:
        if nm not in seen: seen.append(nm); o2.append((round(dd),nm))
        if len(o2)==3: break
    return dict(addr=addr,street=st,dist_addr=round(d),range_side=side,pin_side=pin_side,side_ok=(side==pin_side),nearest_others=o2,
                face_ok=(side==pin_side) and all(d+15<=dd for dd,nm in o2 if not (nm.startswith(('W ','E ')) and st.startswith(('W ','E '))) or True))
if __name__=='__main__':
    for line in sys.stdin:
        a,lat,lon=line.rstrip('\n').split('|')
        print(json.dumps(test(a,float(lat),float(lon))))
