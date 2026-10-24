import json, math
S=json.load(open('/home/user/accounting-agent/desk-drop/cluster-1-flatiron/_work/geo/streets_raw.geojson'))
def xy(lat,lon,lat0=40.74): return (lon*111320*math.cos(math.radians(lat0)), lat*110540)
pts={}
for f in S['features']:
    n=f['properties']['stname_label']; g=f['geometry']; lines=g['coordinates'] if g['type']=='MultiLineString' else [g['coordinates']]
    for ln in lines:
        for a in (ln[0],ln[-1]): pts.setdefault(n,[]).append(xy(a[1],a[0]))
def inter(a,b):
    best=None
    for p in pts.get(a,[]):
        for q in pts.get(b,[]):
            d=math.dist(p,q)
            if best is None or d<best[0]: best=(d,p)
    return best[1]
def proj(P,A,B):
    dx,dy=B[0]-A[0],B[1]-A[1]; L=math.hypot(dx,dy); t=((P[0]-A[0])*dx+(P[1]-A[1])*dy)/L; return t
F23=inter('W 23 ST','5 AVE'); S23=inter('W 23 ST','AVE OF THE AMERICAS')
print('Fifth-Sixth along 23rd', round(math.dist(F23,S23)))
for lab,ll in [('53 W 23rd',(40.742807,-73.991447)),('50 W 23rd',(40.742075,-73.991811))]:
    t=proj(xy(*ll),F23,S23); print(lab,'metres from Fifth corner along 23rd',round(t),'from Sixth',round(math.dist(F23,S23)-t))
F18=inter('W 18 ST','5 AVE'); S18=inter('W 18 ST','AVE OF THE AMERICAS'); F19=inter('W 19 ST','5 AVE')
print('Fifth-Sixth along 18th', round(math.dist(F18,S18)), '18th-19th along Fifth', round(math.dist(F18,F19)))
t=proj(xy(40.73921,-73.994384),F18,S18); print('44 W 18th from Fifth corner', round(t))
t=proj(xy(40.738502,-73.991191),F18,F19); print('111 Fifth from 18th corner along Fifth', round(t))
