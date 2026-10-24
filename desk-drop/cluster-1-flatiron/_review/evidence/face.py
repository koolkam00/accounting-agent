import json, math, csv, re, sys
S=json.load(open('/home/user/accounting-agent/desk-drop/cluster-1-flatiron/_work/geo/streets_raw.geojson'))
def xy(lat,lon,lat0=40.74):
    return (lon*111320*math.cos(math.radians(lat0)), lat*110540)
def norm(a):
    a=a.upper()
    a=a.replace('WEST','W').replace('EAST','E').replace('STREET','ST').replace('AVENUE','AVE')
    a=re.sub(r'(\d+)(ST|ND|RD|TH)\b',r'\1',a)
    a=a.replace('FIFTH AVE','5 AVE').replace('AVE OF THE AMERICAS','AVE OF THE AMERICAS').replace('PARK AVE SOUTH','PARK AVE S')
    return a
def parse(addr):
    m=re.match(r'(\d+)\s+(.*)',addr.strip()); hn=int(m.group(1)); st=norm(m.group(2)); return hn,st
def name_ok(st,f):
    lab=(f['properties']['stname_label'] or '').upper(); full=re.sub(r'\s+',' ',(f['properties']['full_street_name'] or '').upper())
    alts={st, st.replace('AVE OF THE AMERICAS','6 AVE'), st.replace('6 AVE','AVE OF THE AMERICAS')}
    return lab in alts or full in alts
rows=list(csv.DictReader(open(sys.argv[1])))
for r in rows:
    hn,st=parse(r['street_address']); P=xy(float(r['lat']),float(r['lon']))
    best=None
    for f in S['features']:
        if not name_ok(st,f): continue
        p=f['properties']
        try: lo=[int(p['l_low_hn'] or 0),int(p['l_high_hn'] or 0)]; ro=[int(p['r_low_hn'] or 0),int(p['r_high_hn'] or 0)]
        except: continue
        side=None
        if min(lo)<=hn<=max(lo) and lo[0]%2==hn%2: side='L'
        if min(ro)<=hn<=max(ro) and ro[0]%2==hn%2: side='R'
        if not side: continue
        g=f['geometry']; lines=g['coordinates'] if g['type']=='MultiLineString' else [g['coordinates']]
        for ln in lines:
            for a,b in zip(ln,ln[1:]):
                A=xy(a[1],a[0]); B=xy(b[1],b[0])
                dx,dy=B[0]-A[0],B[1]-A[1]; L2=dx*dx+dy*dy
                t=max(0,min(1,((P[0]-A[0])*dx+(P[1]-A[1])*dy)/L2)) if L2 else 0
                Q=(A[0]+t*dx,A[1]+t*dy); d=math.dist(P,Q)
                cross=dx*(P[1]-A[1])-dy*(P[0]-A[0])  # >0 = left of digitized direction
                pside='L' if cross>0 else 'R'
                if best is None or d<best[0]: best=(d,side,pside,p['stname_label'],lo,ro,t)
    if best:
        d,side,pside,lab,lo,ro,t=best
        print(f"{r['building_id']} {r['street_address']:28s} seg {lab} L{lo} R{ro}: addr on {side}, pin on {pside}, {d:.0f} m from centerline, t={t:.2f} -> {'PASS' if side==pside else 'WRONG SIDE'}")
    else: print(r['building_id'], r['street_address'], 'no segment found for', st)
