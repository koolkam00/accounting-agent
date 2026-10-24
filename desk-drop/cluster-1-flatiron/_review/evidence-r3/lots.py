import json, sys, math, urllib.parse, subprocess, pandas as pd
B='/home/user/accounting-agent/desk-drop/cluster-1-flatiron/'
def pip(x,y,poly):
    ins=False
    for ring in poly:
        n=len(ring)
        for i in range(n-1):
            x1,y1=ring[i];x2,y2=ring[i+1]
            if (y1>y)!=(y2>y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1: ins=not ins
    return ins
def dist_to_poly(lat,lon,mp):
    KX=math.cos(math.radians(lat))*111320; KY=110574
    best=1e9
    for poly in mp:
        for ring in poly:
            for i in range(len(ring)-1):
                ax,ay=(ring[i][0]-lon)*KX,(ring[i][1]-lat)*KY; bx,by=(ring[i+1][0]-lon)*KX,(ring[i+1][1]-lat)*KY
                dx,dy=bx-ax,by-ay; L2=dx*dx+dy*dy; t=0 if L2==0 else max(0,min(1,(-ax*dx-ay*dy)/L2))
                best=min(best,math.hypot(ax+t*dx,ay+t*dy))
    return best
rows=[]
for f,idc in [('buildings','building_id'),('retailers','retailer_id'),('coworking','coworking_id')]:
    d=pd.read_csv(B+f+'.csv',dtype=str,keep_default_na=False)
    for _,r in d.iterrows():
        if r.bbl and r.lat: rows.append((f,r[idc],r.street_address,r.bbl,float(r.lat),float(r.lon)))
bbls=sorted({r[3] for r in rows})
geo={}
for k in range(0,len(bbls),40):
    q="SELECT bbl,address,the_geom FROM dcp_mappluto WHERE bbl IN (%s)"%','.join(bbls[k:k+40])
    url="https://planninglabs.carto.com/api/v2/sql?format=geojson&q="+urllib.parse.quote(q)
    out=subprocess.run(['curl','-sS','--max-time','60',url],capture_output=True,text=True).stdout
    for ft in json.loads(out)['features']:
        geo[str(int(ft['properties']['bbl']))]=ft
json.dump(geo,open('lots_all.json','w'))
res=[]
for f,i,a,bbl,lat,lon in rows:
    ft=geo.get(bbl.split('.')[0])
    if not ft: res.append((f,i,a,bbl,'no lot geom',None)); continue
    mp=ft['geometry']['coordinates']
    inside=any(pip(lon,lat,p) for p in mp)
    res.append((f,i,a,bbl,'inside' if inside else 'OUTSIDE',round(dist_to_poly(lat,lon,mp),1)))
df=pd.DataFrame(res,columns=['file','id','address','bbl','in_own_lot','m_to_lot_edge'])
df.to_csv('pin_in_lot.csv',index=False)
print(df.in_own_lot.value_counts())
print(df[df.in_own_lot!='inside'].to_string())
