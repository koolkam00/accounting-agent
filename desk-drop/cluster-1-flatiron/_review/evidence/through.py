import json, math, csv, re
S=json.load(open('/home/user/accounting-agent/desk-drop/cluster-1-flatiron/_work/geo/streets_raw.geojson'))
def xy(lat,lon,lat0=40.74): return (lon*111320*math.cos(math.radians(lat0)), lat*110540)
segs={}
for f in S['features']:
    g=f['geometry']; lines=g['coordinates'] if g['type']=='MultiLineString' else [g['coordinates']]
    n=f['properties']['stname_label']
    for ln in lines:
        for a,b in zip(ln,ln[1:]): segs.setdefault(n,[]).append((xy(a[1],a[0]),xy(b[1],b[0])))
def d(P,n):
    best=1e9
    for A,B in segs.get(n,[]):
        dx,dy=B[0]-A[0],B[1]-A[1]; L2=dx*dx+dy*dy
        t=max(0,min(1,((P[0]-A[0])*dx+(P[1]-A[1])*dy)/L2)) if L2 else 0
        best=min(best,math.dist(P,(A[0]+t*dx,A[1]+t*dy)))
    return best
rows=list(csv.DictReader(open('/home/user/accounting-agent/desk-drop/cluster-1-flatiron/buildings.csv')))
flag=[]
for r in rows:
    m=re.match(r'\d+\s+(East|West)\s+(\d+)\w*\s+Street',r['street_address'])
    if not m: continue
    k=int(m.group(2)); EW='E' if m.group(1)=='East' else 'W'
    P=xy(float(r['lat']),float(r['lon']))
    da=d(P,f'{EW} {k} ST'); dn=min(d(P,f'{EW} {k-1} ST'),d(P,f'{EW} {k+1} ST'))
    if da>=dn-8: flag.append((r['building_id'],r['street_address'],round(da),round(dn),r['pluto_address'],r['candidate_company_count']))
print(len(flag),'side-street buildings whose pin is not clearly on the addressed street face')
for x in flag: print(x)
