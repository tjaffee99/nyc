"""Scratch: (footprint with holes) minus a frame rectangle list, in frame coords, as TS literals."""
import math, sys, duckdb, numpy as np, shapely
from fr import toframe
FP='/home/user/nyc/data/interim/nyc_footprints_raw.parquet'
con=duckdb.connect()
def full(bin_, a):
    out=[]
    for (w,) in con.execute(f"select geometry from '{FP}' where bin={bin_}").fetchall():
        g=shapely.from_wkb(bytes(w)); kx=111320*math.cos(math.radians(a[1]))
        out.append(shapely.transform(g, lambda xy: np.column_stack([(xy[:,0]-a[0])*kx,(xy[:,1]-a[1])*110574])))
    return shapely.union_all(out)
def ts(r): return '[' + ', '.join(f"[{x:.1f}, {y:.1f}]" for x,y in np.asarray(r.coords)[:-1]) + ']'
name,bin_,a,o,brg,tol,minus=sys.argv[1:8]
a=tuple(float(v) for v in a.split(',')); ox,oy=(float(v) for v in o.split(','))
p=toframe(full(bin_,a),ox,oy,float(brg))
print('full area with holes', round(p.area), 'holes', sum(len(g.interiors) for g in getattr(p,'geoms',[p])))
for m in minus.split(';'):
    x0,y0,x1,y1=(float(v) for v in m.split(','))
    p=p.difference(shapely.box(x0,y0,x1,y1))
p=p.simplify(float(tol))
for g in getattr(p,'geoms',[p]):
    if g.area<40: continue
    print(f"// piece area {g.area:.0f}")
    print('{outer: '+ts(g.exterior)+', holes: ['+', '.join(ts(h) for h in g.interiors if shapely.Polygon(h).area>30)+']},')
