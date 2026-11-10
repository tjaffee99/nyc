import sys; sys.path.insert(0,'data/interim/landmarks_bridges')
from blib import *
import json
# Hell Gate line ground profile
A=(-73.923383,40.783592); B=(-73.920608,40.781506); ax=Axis(A,B)
L=json.load(open('data/interim/landmarks_bridges/hellgate_line.json'))['line']
M=LineString([loc(ax.anchor,p) for p in L])
print('HG ground 1500-2500:',' '.join(f'{d}:{elev(*unloc(ax.anchor,(M.interpolate(d).x,M.interpolate(d).y))):.1f}' for d in range(1500,2501,50)))
print('HG ends ground', round(elev(*L[0]),1), round(elev(*L[-1]),1))
# water crossings of the rail line
import blib; blib.ov("rail","false"); W=blib.con.execute(f"select subtype,class,name,st_aswkb(geometry) from '{OV}/base_water.parquet' where st_intersects(geometry, st_makeenvelope(-73.94,40.765,-73.90,40.81))").fetchall() if True else []
from shapely import wkb as _w
wat=[(a,b,c,_w.loads(bytes(g))) for a,b,c,g in W]
print('water feats',len(wat))
def crossings(lonlat, anchor, label):
    ln=LineString(lonlat); Mm=LineString([loc(anchor,p) for p in lonlat])
    for a,b,c,g in wat:
        if g.geom_type not in('Polygon','MultiPolygon'): continue
        it=ln.intersection(g)
        if it.is_empty: continue
        parts=list(it.geoms) if hasattr(it,'geoms') else [it]
        for prt in parts:
            if prt.geom_type!='LineString': continue
            d0=Mm.project(Point(loc(anchor,prt.coords[0]))); d1=Mm.project(Point(loc(anchor,prt.coords[-1])))
            if abs(d1-d0)>15: print('   water',label,a,b,c,round(min(d0,d1)),round(max(d0,d1)))
crossings(L,ax.anchor,'HG rail')
# RFK
segs={s[3][:8]:s for s in ov('roads_region',"name = 'Robert F. Kennedy Bridge'")}
o=osm('rfk_north')
t1=centroid(way(o,1016646456)[1])[0]; t2=centroid(way(o,1016646459)[1])[0]
lax=Axis(t2,t1)  # Manhattan side tower -> Randalls side tower
print('lift towers',t1,t2,'dist',round(lax.len,1),'cited 94.5; bearing',round(lax.bearing,2),'anchor',lax.anchor, 'mrr',mrr(way(o,1016646456)[1]))
for k,(n,c,ls,i) in segs.items():
    cs=list(ls.coords); an=cs[0]
    print(' seg',k,round(length(ls)),'ground ends',round(elev(*cs[0]),1),round(elev(*cs[-1]),1), 'lift sa', lax.sa(cs[0]), lax.sa(cs[-1]))
    crossings(cs,an,k)
json.dump({k:list(s[2].coords) for k,s in segs.items()},open('data/interim/landmarks_bridges/rfk_lines.json','w'))
