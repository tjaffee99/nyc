import json, math, duckdb, numpy as np, shapely, sys
from shapely import wkb
L=json.load(open('/home/user/nyc/data/research/landmarks_new_haven_build/meshes.json'))
only=sys.argv[1:]
con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
F='/home/user/nyc/data/interim/counties/ct_south_central_connecticut.parquet'
for lm in L:
    if only and lm['id'] not in only: continue
    a=lm['anchor']; kx=111320*math.cos(math.radians(a[1]))
    pos=np.array(lm['pos']).reshape(-1,3,3); zmax=pos[:,:,2].max()
    tri=[shapely.Polygon(t[:,:2]) for t in pos]; tri=[t for t in tri if t.area>1e-3]
    sil=shapely.union_all([t.buffer(0.02) for t in tri])
    r=float(np.abs(pos[:,:,:2]).max())+40; dx=r/kx; dy=r/110574
    fps=con.execute(f"select id,name,height_m,area_m2,geometry from read_parquet('{F}') where lon between {a[0]-dx} and {a[0]+dx} and lat between {a[1]-dy} and {a[1]+dy}").fetchall()
    gs=[]
    for id,n,h,ar,g in fps:
        p=wkb.loads(bytes(g)); p=max(p.geoms,key=lambda z:z.area) if p.geom_type=='MultiPolygon' else p
        gs.append((id,n,h,ar,shapely.Polygon([((x-a[0])*kx,(y-a[1])*110574) for x,y in p.exterior.coords])))
    reps=[shapely.Polygon(p) for p in lm['replaces']]
    inside=[(i,n,h,ar,q) for i,n,h,ar,q in gs if any(rp.buffer(1).contains(q.representative_point()) for rp in reps)]
    s=f"{lm['id']:30s} {lm['nverts']//3:4d}f zmax {zmax:6.1f}  plan {sil.area:6.0f}"
    if inside:
        u=shapely.union_all([q for *_,q in inside])
        s+=f" fp {u.area:6.0f} (area_m2 {sum(x[3] for x in inside):.0f}) ratio {sil.area/u.area:.3f} dcen {math.hypot(sil.centroid.x-u.centroid.x,sil.centroid.y-u.centroid.y):.1f}m outside {sil.difference(u.buffer(0.5)).area:.0f}m2 ids {[i[:8] for i,*_ in inside]}"
    else:
        c=sil.centroid; hit=[(n,round(q.distance(c),1)) for i,n,h,ar,q in gs if q.distance(c)<25]
        s+=f" no replaces; centre near {hit[:3]}"
    print(s)
