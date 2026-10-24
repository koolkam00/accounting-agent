import heapq, math, json, sys
from face import segs, xy, norm
# Build graph from CSCL segment vertices (all vertices, consecutive pairs).
nodes={}; adj={}
def nid(p):
    k=(round(p[0]),round(p[1]))  # 1 m snapping
    return k
def add(a,b,w):
    adj.setdefault(a,[]).append((b,w)); adj.setdefault(b,[]).append((a,w))
names={}
for nm,p,pts in segs:
    if p.get('rw_type') not in ('1',None):  # streets only
        continue
    for i in range(len(pts)-1):
        a,b=nid(pts[i]),nid(pts[i+1]); w=math.dist(pts[i],pts[i+1])
        add(a,b,w); names[(a,b)]=nm; names[(b,a)]=nm
# merge nodes within 3 m (intersections digitized slightly apart)
keys=list(adj)
def snap_to_street(P,street):
    best=None
    for nm,p,pts in segs:
        if nm!=street: continue
        for i in range(len(pts)-1):
            A,B=pts[i],pts[i+1]
            dx,dy=B[0]-A[0],B[1]-A[1]; L2=dx*dx+dy*dy
            t=max(0,min(1,((P[0]-A[0])*dx+(P[1]-A[1])*dy)/L2)) if L2 else 0
            Q=(A[0]+t*dx,A[1]+t*dy); d=math.dist(P,Q)
            if best is None or d<best[0]: best=(d,Q,nid(A),nid(B),t*math.sqrt(L2),(1-t)*math.sqrt(L2))
    return best
def dijkstra(src_links,dst_links):
    dist={};pq=[]
    for n,w in src_links: heapq.heappush(pq,(w,n))
    dst=dict(dst_links); best=1e18
    while pq:
        d,u=heapq.heappop(pq)
        if u in dist: continue
        dist[u]=d
        if u in dst: best=min(best,d+dst[u])
        if d>best: break
        for v,w in adj.get(u,[]):
            if v not in dist: heapq.heappush(pq,(d+w,v))
        # tolerance merge
    return best
def leg(a,b):
    (sa,la,loa),(sb,lb,lob)=a,b
    A=snap_to_street(xy(la,loa),sa); B=snap_to_street(xy(lb,lob),sb)
    return dijkstra([(A[2],A[4]),(A[3],A[5])],[(B[2],B[4]),(B[3],B[5])]),A[0],B[0]
if __name__=='__main__':
    for line in sys.stdin:
        x=json.loads(line); print(x['name'], [round(v) for v in leg(tuple(x['a']),tuple(x['b']))])
