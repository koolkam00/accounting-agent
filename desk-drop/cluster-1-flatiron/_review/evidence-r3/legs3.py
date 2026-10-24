# Reviewer round 3: shortest path on NYC CSCL centrelines (own code), for two route legs.
import json, math, heapq, sys
G='/home/user/accounting-agent/desk-drop/cluster-1-flatiron/_work/geo/streets_raw.geojson'
g=json.load(open(G))
LAT0,LON0=40.74,-73.99
KX=math.cos(math.radians(LAT0))*111320; KY=110574
def xy(lat,lon): return ((lon-LON0)*KX,(lat-LAT0)*KY)
SKIP=('PEDESTRIAN','CONNECTOR','HIGH LINE','EXIT','ENTRANCE','DRIVEWAY','FDR','ROOSEVELT','TUNNEL','RAMP')
adj={}; segs=[]
def key(p): return (round(p[0],0),round(p[1],0))
for f in g['features']:
    p=f['properties']; name=p.get('stname_label') or ''
    if any(s in name for s in SKIP) or not name: continue
    geom=f['geometry']; lines=geom['coordinates'] if geom['type']=='MultiLineString' else [geom['coordinates']]
    for ln in lines:
        pts=[xy(c[1],c[0]) for c in ln]
        for a,b in zip(pts,pts[1:]):
            ka,kb=key(a),key(b); d=math.dist(a,b)
            adj.setdefault(ka,[]).append((kb,d,name)); adj.setdefault(kb,[]).append((ka,d,name))
            segs.append((name,a,b))
def snap(P,street):
    best=None
    for name,a,b in segs:
        if name!=street: continue
        dx,dy=b[0]-a[0],b[1]-a[1]; L2=dx*dx+dy*dy; t=max(0,min(1,((P[0]-a[0])*dx+(P[1]-a[1])*dy)/L2)) if L2 else 0
        q=(a[0]+t*dx,a[1]+t*dy); d=math.dist(P,q)
        if best is None or d<best[0]: best=(d,q,a,b,name)
    return best
def route(p1,s1,p2,s2):
    A=snap(xy(*p1),s1); B=snap(xy(*p2),s2)
    S=('S',); T=('T',)
    extra={S:[(key(A[2]),math.dist(A[1],A[2]),s1),(key(A[3]),math.dist(A[1],A[3]),s1)]}
    tgt={key(B[2]):(math.dist(B[1],B[2]),s2),key(B[3]):(math.dist(B[1],B[3]),s2)}
    dist={S:0}; prev={}; pq=[(0,S)]; best=(1e9,None)
    while pq:
        d,u=heapq.heappop(pq)
        if d>dist.get(u,1e18): continue
        if u in tgt and d+tgt[u][0]<best[0]: best=(d+tgt[u][0],u)
        for v,w,nm in (extra.get(u) or adj.get(u,[])):
            nd=d+w
            if nd<dist.get(v,1e18): dist[v]=nd; prev[v]=(u,nm); heapq.heappush(pq,(nd,v))
    # path names
    names=[s2]; u=best[1]
    while u in prev:
        u,nm=prev[u]
        if names[-1]!=nm: names.append(nm)
    return best[0], list(reversed(names)), A[0], B[0]
if __name__=='__main__':
    legs=[((40.742199,-73.991720),'W 23 ST',(40.739819,-73.986885),'PARK AVE S','7->8 50 W 23rd St to 300 Park Ave S'),
          ((40.739819,-73.986885),'PARK AVE S',(40.736860,-73.988546),'PARK AVE S','8->9 300 Park Ave S to 215 Park Ave S'),
          ((40.740240,-73.994996),'AVE OF THE AMERICAS',(40.741838,-73.992892),'W 22 ST','2->3 625 Sixth Ave to 56 W 22nd St')]
    for p1,s1,p2,s2,lab in legs:
        d,names,o1,o2=route(p1,s1,p2,s2)
        print(lab, 'centreline metres', round(d), 'via', ' > '.join(names), '| pin offsets', round(o1),round(o2))
