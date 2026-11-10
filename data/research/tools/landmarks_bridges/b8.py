import sys; sys.path.insert(0,'data/interim/landmarks_bridges')
from blib import *
import blib
blib.ov('rail','false')
from shapely import wkb as _w
def water(bb): return [(c,_w.loads(bytes(g))) for a,b,c,g in blib.con.execute(f"select subtype,class,name,st_aswkb(geometry) from '{OV}/base_water.parquet' where st_intersects(geometry, st_makeenvelope({bb[0]},{bb[1]},{bb[2]},{bb[3]}))").fetchall()]
def show(where, bb, label, file='roads_region'):
    wat=water(bb)
    for n,c,ls,i in ov(file,where,bb):
        cs=list(ls.coords)
        if length(ls)<150: continue
        M=LineString([loc(cs[0],p) for p in cs]); ln=LineString(cs)
        cr=[]
        for nm,g in wat:
            if g.geom_type not in('Polygon','MultiPolygon'): continue
            it=ln.intersection(g)
            for prt in (list(it.geoms) if hasattr(it,'geoms') else [it]):
                if prt.geom_type=='LineString' and not prt.is_empty:
                    d0=M.project(Point(loc(cs[0],prt.coords[0]))); d1=M.project(Point(loc(cs[0],prt.coords[-1])))
                    if abs(d1-d0)>20: cr.append((nm,round(min(d0,d1)),round(max(d0,d1))))
        print(f' {label} {n} {c} {i[:8]} len {length(ls):.0f} npts {len(cs)} {cs[0][0]:.6f},{cs[0][1]:.6f} -> {cs[-1][0]:.6f},{cs[-1][1]:.6f} ground {elev(*cs[0]):.1f}/{elev(*cs[-1]):.1f} water {sorted(set(cr))}')
show("name='Brooklyn-Queens Expressway'",(-73.9345,40.7235,-73.9235,40.7325),'KOS')
show("name like 'Marine Parkway%'",(-73.905,40.560,-73.890,40.585),'MAR')
o=osm('kosciuszko')
for r in o['rels']: print(' rel',r[0],r[2].get('name'),r[2].get('type'),[(m[0],m[1],m[2]) for m in r[1]][:8])
for w in o['ways']: print(' way',w[0],w[2])
