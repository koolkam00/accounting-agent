# Reviewer round 3: independent block-face test against NYC CSCL address ranges.
import json, math, re, sys
G='/home/user/accounting-agent/desk-drop/cluster-1-flatiron/_work/geo/streets_raw.geojson'
g=json.load(open(G))
LAT0,LON0=40.74,-73.99
KX=math.cos(math.radians(LAT0))*111320; KY=110574
def xy(lat,lon): return ((lon-LON0)*KX,(lat-LAT0)*KY)
segs=[]
for f in g['features']:
    p=f['properties']; geom=f['geometry']
    lines=geom['coordinates'] if geom['type']=='MultiLineString' else [geom['coordinates']]
    for ln in lines:
        segs.append((p.get('stname_label') or '',p,[xy(c[1],c[0]) for c in ln]))
def i(s):
    try: return int(re.sub(r'\D','',str(s).split('-')[0]))
    except: return None
def near(P,pts):
    best=(1e9,0,0,0)
    for k in range(len(pts)-1):
        (ax,ay),(bx,by)=pts[k],pts[k+1]; dx,dy=bx-ax,by-ay; L2=dx*dx+dy*dy
        t=0 if L2==0 else ((P[0]-ax)*dx+(P[1]-ay)*dy)/L2
        tc=max(0,min(1,t)); qx,qy=ax+tc*dx,ay+tc*dy
        d=math.hypot(P[0]-qx,P[1]-qy); cr=dx*(P[1]-ay)-dy*(P[0]-ax)
        if d<best[0]: best=(d,cr,t,k)
    return best
MAP={'FIFTH AVENUE':'5 AVE','PARK AVENUE SOUTH':'PARK AVE S','SIXTH AVENUE':'AVE OF THE AMERICAS','AVENUE OF THE AMERICAS':'AVE OF THE AMERICAS','THIRD AVENUE':'3 AVE','UNION SQUARE WEST':'UNION SQ W','MADISON AVENUE':'MADISON AVE','BROADWAY':'BROADWAY'}
def parse(addr):
    a=addr.upper().split(',')[0].strip()
    m=re.match(r'(\d+)\s+(.*)',a); hn=int(m.group(1)); st=m.group(2).strip()
    m2=re.match(r'(WEST|EAST)\s+(\d+)(ST|ND|RD|TH)?\s+STREET',st)
    if m2: st=('W ' if m2.group(1)=='WEST' else 'E ')+m2.group(2)+' ST'
    else: st=MAP.get(st,st)
    return hn,st
def test(addr,lat,lon):
    hn,st=parse(addr); P=xy(lat,lon)
    cands=[]
    for name,p,pts in segs:
        if name!=st: continue
        for side in ('l','r'):
            lo,hi=i(p.get(side+'_low_hn')),i(p.get(side+'_high_hn'))
            if lo is None or hi is None: continue
            if min(lo,hi)<=hn<=max(lo,hi) and (lo%2==hn%2):
                d,cr,t,k=near(P,pts); cands.append((d,side,cr,t,p,pts))
    if not cands: return dict(addr=addr,street=st,result='no CSCL range')
    d,side,cr,t,p,pts=min(cands,key=lambda x:x[0])
    onside = (cr>0 and side=='l') or (cr<0 and side=='r')
    inblock = -0.02<=t<=1.02 if len(pts)==2 else True
    # nearest other street
    other=(1e9,'')
    for name,pp,pts2 in segs:
        if name in (st,'') or name.startswith('PEDESTRIAN') or 'CONNECTOR' in name: continue
        dd=near(P,pts2)[0]
        if dd<other[0]: other=(dd,name)
    half=float(p.get('streetwidth') or 0)*0.3048/2
    return dict(addr=addr,street=st,seg=f"{p.get('l_low_hn')}-{p.get('l_high_hn')}/{p.get('r_low_hn')}-{p.get('r_high_hn')}",side=side,onside=onside,t=round(t,2),d_addr=round(d,1),curb_half=round(half,1),nearest_other=other[1],d_other=round(other[0],1),
                result='PASS' if onside and d+15<=other[0] or (onside and d<other[0]) else 'CHECK')
if __name__=='__main__':
    import pandas as pd
    for line in sys.stdin:
        a,lat,lon=line.rstrip('\n').split('|'); print(test(a,float(lat),float(lon)))
