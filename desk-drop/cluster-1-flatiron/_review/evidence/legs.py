import json, math, heapq, re
S=json.load(open('/home/user/accounting-agent/desk-drop/cluster-1-flatiron/_work/geo/streets_raw.geojson'))
def xy(lat,lon,lat0=40.74): return (lon*111320*math.cos(math.radians(lat0)), lat*110540)
G={}; segs=[]
def key(p): return (round(p[0],1),round(p[1],1))
for f in S['features']:
    if f['properties'].get('rw_type') not in ('1',): continue
    g=f['geometry']; lines=g['coordinates'] if g['type']=='MultiLineString' else [g['coordinates']]
    n=f['properties']['stname_label']
    for ln in lines:
        pts=[xy(a[1],a[0]) for a in ln]
        for A,B in zip(pts,pts[1:]):
            a,b=key(A),key(B); d=math.dist(A,B)
            G.setdefault(a,[]).append((b,d,n)); G.setdefault(b,[]).append((a,d,n)); segs.append((n,A,B))
# merge near nodes (intersections digitized slightly apart)
def snap(P,name):
    best=None
    for n,A,B in segs:
        if n!=name: continue
        dx,dy=B[0]-A[0],B[1]-A[1]; L2=dx*dx+dy*dy
        t=max(0,min(1,((P[0]-A[0])*dx+(P[1]-A[1])*dy)/L2)) if L2 else 0
        Q=(A[0]+t*dx,A[1]+t*dy); d=math.dist(P,Q)
        if best is None or d<best[0]: best=(d,Q,A,B)
    return best
def route(p1,n1,p2,n2):
    s=snap(xy(*p1),n1); e=snap(xy(*p2),n2)
    S0=('S',); E0=('E',)
    H={k:list(v) for k,v in G.items()}
    for tag,(d,Q,A,B),n in ((S0,s,n1),(E0,e,n2)):
        H.setdefault(tag,[])
        for X in (A,B):
            dd=math.dist(Q,X); H[tag].append((key(X),dd,n)); H.setdefault(key(X),[]).append((tag,dd,n))
    if s[2]==e[2] and s[3]==e[3]:
        dd=math.dist(s[1],e[1]); H[S0].append((E0,dd,n1))
    dist={S0:0}; prev={}; pq=[(0,S0)]
    while pq:
        d,u=heapq.heappop(pq)
        if u==E0: break
        if d>dist.get(u,1e18): continue
        for v,w,n in H.get(u,[]):
            nd=d+w
            if nd<dist.get(v,1e18): dist[v]=nd; prev[v]=(u,n); heapq.heappush(pq,(nd,v))
    path=[]; u=E0
    while u in prev: u,n=prev[u]; path.append(n)
    names=[]
    for n in reversed(path):
        if not names or names[-1]!=n: names.append(n)
    return dist[E0], s[0], e[0], names
legs=[('111 Fifth -> 44 W 18th',(40.738502,-73.991191),'5 AVE',(40.73921,-73.994384),'W 18 ST'),
      ('53 W 23rd -> 50 W 23rd',(40.742807,-73.991447),'W 23 ST',(40.742075,-73.991811),'W 23 ST'),
      ('22 W 19th -> 111 Fifth',(40.739399,-73.992895),'W 19 ST',(40.738502,-73.991191),'5 AVE')]
for lab,p1,n1,p2,n2 in legs:
    d,o1,o2,names=route(p1,n1,p2,n2)
    print(lab, f'centerline path {d:.0f} m; pin offsets {o1:.0f}/{o2:.0f} m; streets used {names}')
