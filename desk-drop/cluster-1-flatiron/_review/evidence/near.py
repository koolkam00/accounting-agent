import json, math, csv, sys
S=json.load(open('/home/user/accounting-agent/desk-drop/cluster-1-flatiron/_work/geo/streets_raw.geojson'))
def xy(lat,lon,lat0=40.74): return (lon*111320*math.cos(math.radians(lat0)), lat*110540)
segs=[]
for f in S['features']:
    g=f['geometry']; lines=g['coordinates'] if g['type']=='MultiLineString' else [g['coordinates']]
    for ln in lines:
        for a,b in zip(ln,ln[1:]): segs.append((f['properties']['stname_label'],xy(a[1],a[0]),xy(b[1],b[0])))
def dist(P,A,B):
    dx,dy=B[0]-A[0],B[1]-A[1]; L2=dx*dx+dy*dy
    t=max(0,min(1,((P[0]-A[0])*dx+(P[1]-A[1])*dy)/L2)) if L2 else 0
    return math.dist(P,(A[0]+t*dx,A[1]+t*dy))
for r in csv.DictReader(open(sys.argv[1])):
    P=xy(float(r['lat']),float(r['lon'])); best={}
    for n,A,B in segs:
        d=dist(P,A,B)
        if n not in best or d<best[n]: best[n]=d
    top=sorted(best.items(),key=lambda x:x[1])[:4]
    print(r['building_id'], r['street_address'], ' | '.join(f'{n} {d:.0f}m' for n,d in top))
