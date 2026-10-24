import sys, csv, math
sys.dont_write_bytecode=True
sys.path.insert(0,'/home/user/accounting-agent/desk-drop/cluster-1-flatiron/_build')
import grid, router
rows=list(csv.DictReader(open('/home/user/accounting-agent/desk-drop/cluster-1-flatiron/route.csv')))
sp=router.sp(); T=0; T2=0; off=0
for a,b in zip(rows,rows[1:]):
    sa,xa=grid.sx(float(a['lat']),float(a['lon'])); sb,xb=grid.sx(float(b['lat']),float(b['lon']))
    lg=router.leg({'street_address':a['street_address'],'grid_s':sa,'grid_x':xa},{'street_address':b['street_address'],'grid_s':sb,'grid_x':xb})
    Q=lg['path']
    def seg(p,q): return abs(q[1]-p[1])+abs(q[0]-p[0])*sp
    o=seg(Q[0],Q[1])+seg(Q[-2],Q[-1]) if len(Q)>2 else 0
    T+=lg['metres']; off+=o
    print(f"{a['stop']}->{b['stop']} {lg['metres']:.0f} m (file {b['leg_metres_est']}), centroid-to-sidewalk {o:.0f} m, kerb-to-kerb {lg['metres']-o:.0f} m")
print('total',round(T),'of which centroid offsets',round(off), 'minutes saved at 64 m/min', round(off/64,1))
