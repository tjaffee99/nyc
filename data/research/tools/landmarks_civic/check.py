"""Scratch: numeric check of each landmark mesh against the official footprints. Usage: check.py [id-substring ...]"""
import json, math, sys, duckdb, numpy as np, shapely
FP='/home/user/nyc/data/interim/nyc_footprints_raw.parquet'
con=duckdb.connect()
L=json.load(open('/home/user/nyc/data/interim/landmarks_civic/meshes.json'))
want=[a for a in sys.argv[1:] if not a.startswith('--')]
SUM={}
for lm in L:
    if want and not any(w in lm['id'] for w in want): continue
    a=lm['anchor']; kx=111320*math.cos(math.radians(a[1]))
    pos=np.array(lm['pos']).reshape(-1,3,3)
    zmax=pos[:,:,2].max(); zmin=pos[:,:,2].min()
    tri=[shapely.Polygon(t[:,:2]) for t in pos]
    tri=[t for t in tri if t.area>1e-3]
    sil=shapely.union_all([t.buffer(0.01) for t in tri]) if tri else shapely.Polygon()
    r=float(np.abs(pos[:,:,:2]).max())+60
    dx=r/kx; dy=r/110574
    rows=con.execute(f"SELECT bin,name,year_raw,height_m,lon,lat,geometry FROM '{FP}' WHERE lon BETWEEN {a[0]-dx} AND {a[0]+dx} AND lat BETWEEN {a[1]-dy} AND {a[1]+dy}").fetchall()
    reps=[shapely.Polygon(p) for p in lm['replaces']]
    SUM[lm['id']]={'zmax':round(float(zmax),2),'plan':round(sil.area) if tri else 0,'nverts':lm['nverts']}
    inside=[]; poke=[]
    for bin_,nm,yr,h,lon,lat,wkb in rows:
        g=shapely.from_wkb(bytes(wkb)); g=shapely.transform(g, lambda xy: np.column_stack([(xy[:,0]-a[0])*kx,(xy[:,1]-a[1])*110574]))
        c=shapely.Point((lon-a[0])*kx,(lat-a[1])*110574)
        if any(p.contains(c) for p in reps): inside.append((bin_,nm,yr,h,g))
        elif g.intersects(sil) and g.intersection(sil).area>0.25*g.area: poke.append((bin_,nm,yr,h,g))
    print(f"## {lm['id']}  verts {lm['nverts']} bad {lm['bad']}  z {zmin:.2f}..{zmax:.2f}  plan area {sil.area:.0f} cen ({sil.centroid.x:.1f},{sil.centroid.y:.1f})" if tri else f"## {lm['id']} EMPTY")
    if inside:
        u=shapely.union_all([g for *_,g in inside]); hm=max((h or 0) for _,_,_,h,_ in inside)
        ext=shapely.union_all([shapely.Polygon(q.exterior) for *_,g in inside for q in getattr(g,'geoms',[g])])
        SUM[lm['id']].update({'off':round(u.area),'off_ext':round(ext.area),'ratio':round(sil.area/u.area,3),'ratio_ext':round(sil.area/ext.area,3),'dcen':round(math.hypot(sil.centroid.x-u.centroid.x, sil.centroid.y-u.centroid.y),1),'roof':round(hm,1),'bins':[b for b,*_ in inside]})
        print(f"   replaced: {len(inside)} footprints, area {u.area:.0f} cen ({u.centroid.x:.1f},{u.centroid.y:.1f}) max roof {hm:.1f} | plan/official {sil.area/u.area:.3f}  dcen {math.hypot(sil.centroid.x-u.centroid.x, sil.centroid.y-u.centroid.y):.1f} m  | official outside plan {u.difference(sil).area:.0f} m2, plan outside official {sil.difference(u).area:.0f} m2")
        for bin_,nm,yr,h,g in inside: print(f"      BIN {bin_} {nm or '-'} yr {yr} roof {h and round(h,1)} area {g.area:.0f}")
    elif reps: print('   replaces: NO footprint centroid inside!')
    for bin_,nm,yr,h,g in poke: print(f"   !! not replaced but under the model: BIN {bin_} {nm or '-'} yr {yr} roof {h and round(h,1)} area {g.area:.0f} cen ({g.centroid.x:.1f},{g.centroid.y:.1f})")

json.dump(SUM, open('/home/user/nyc/data/interim/landmarks_civic/check_summary.json','w'))
