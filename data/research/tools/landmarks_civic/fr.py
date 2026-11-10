"""Scratch: footprint (by BIN) in a model frame. Usage: fr.py name:bin:alon,alat:ox,oy:bearing[:tol] ...  (origin in anchor-local metres; +y of frame -> bearing)"""
import math, sys, duckdb, numpy as np, shapely
FP='/home/user/nyc/data/interim/nyc_footprints_raw.parquet'
con=duckdb.connect()
def ring_local(bin_, a):
    wkb=con.execute(f"select geometry from '{FP}' where bin={bin_}").fetchall()
    out=[]
    for (w,) in wkb:
        g=shapely.from_wkb(bytes(w)); kx=111320*math.cos(math.radians(a[1]))
        for p in getattr(g,'geoms',[g]):
            out.append(shapely.Polygon([((x-a[0])*kx,(y-a[1])*110574) for x,y in np.asarray(p.exterior.coords)[:,:2]]))
    return shapely.union_all(out)
def toframe(p, ox, oy, brg):
    a=math.radians(brg); c,s=math.cos(a),math.sin(a)
    # world = R(-brg)*(local) + o ; inverse: local = R(brg)*(world-o)  [x' = c*dx - s*dy ; y' = s*dx + c*dy]
    return shapely.transform(p, lambda xy: np.column_stack([c*(xy[:,0]-ox)-s*(xy[:,1]-oy), s*(xy[:,0]-ox)+c*(xy[:,1]-oy)]))
if __name__=='__main__':
    for arg in [a for a in sys.argv[1:] if not a.startswith('--')]:
        f=arg.split(':'); name=f[0]; bins=f[1].split('+'); a=tuple(float(v) for v in f[2].split(',')); ox,oy=(float(v) for v in f[3].split(',')); brg=float(f[4]); tol=float(f[5]) if len(f)>5 else 0.5
        p=shapely.union_all([ring_local(b,a) for b in bins]); q=toframe(p,ox,oy,brg).simplify(tol)
        print(f"=== {name} frame o=({ox},{oy}) brg {brg}: area {p.area:.0f} cen_frame=({q.centroid.x:.1f},{q.centroid.y:.1f}) bounds {tuple(round(v,1) for v in q.bounds)}")
        for g in getattr(q,'geoms',[q]):
            if '--ts' in sys.argv: print('   P(' + ', '.join(f"{x:.1f}, {y:.1f}" for x,y in np.asarray(g.exterior.coords)[:-1]) + ')')
            else: print('   '+' '.join(f"[{x:.1f},{y:.1f}]" for x,y in np.asarray(g.exterior.coords)[:-1]))
