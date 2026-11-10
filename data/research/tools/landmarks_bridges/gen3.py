import sys; sys.path.insert(0,'data/interim/landmarks_bridges')
from blib import *
import blib
blib.ov('rail','false')
from shapely import wkb as _w
out=[]
def emit(name, pts, comment=''):
    out.append(f"const {name}: V2[] = {fmt(pts)};{' // '+comment if comment else ''}")
def water(bb): return [_w.loads(bytes(g)) for (g,) in blib.con.execute(f"select st_aswkb(geometry) from '{OV}/base_water.parquet' where st_intersects(geometry, st_makeenvelope({bb[0]},{bb[1]},{bb[2]},{bb[3]}))").fetchall()]
def line(where, bb, pick, rev=False, tol=1.0):
    wat=[g for g in water(bb) if g.geom_type in('Polygon','MultiPolygon')]
    cand=[x for x in ov('roads_region',where,bb) if x[3].startswith(pick)]
    cand.sort(key=lambda x:-length(x[2]))
    for n,c,ls,i in cand[:1]:
        cs=list(ls.coords)
        if rev: cs=cs[::-1]
        a=cs[0]; M=LineString([loc(a,p) for p in cs]).simplify(tol)
        ll=[unloc(a,p) for p in M.coords]; ln=LineString(ll); cr=set()
        for g in wat:
            it=ln.intersection(g)
            for prt in (list(it.geoms) if hasattr(it,'geoms') else [it]):
                if prt.geom_type=='LineString' and not prt.is_empty:
                    d0=M.project(Point(loc(a,prt.coords[0]))); d1=M.project(Point(loc(a,prt.coords[-1])))
                    if abs(d1-d0)>20: cr.add((round(min(d0,d1)),round(max(d0,d1))))
        print(f'  {pick} len {M.length:.0f} npts {len(ll)} start {ll[0][0]:.6f},{ll[0][1]:.6f} end {ll[-1][0]:.6f},{ll[-1][1]:.6f} ground {elev(*ll[0]):.1f}/{elev(*ll[-1]):.1f} water {sorted(cr)}')
        return ll,M
bb=(-73.9345,40.7235,-73.9235,40.7325)
print('KOSCIUSZKO (Brooklyn -> Queens)')
ll,M=line("name='Brooklyn-Queens Expressway'",bb,'e2ac78e7'); emit('KZ_EB',ll,'Overture e2ac78e7 (Brooklyn-Queens Expressway, bridge flag): eastbound bridge, Brooklyn → Queens')
ll,M=line("name='Brooklyn-Queens Expressway'",bb,'8f4b1e93',rev=True); emit('KZ_WB',ll,'Overture 8f4b1e93: westbound bridge, drawn Brooklyn → Queens')
print('MARINE (Brooklyn -> Rockaway)')
bb=(-73.892,40.566,-73.878,40.581)
ll,M=line("name like 'Marine Parkway%'",bb,'8e44ec36'); emit('MP_SB',ll,'Overture 8e44ec36 (Marine Parkway–Gil Hodges Memorial Bridge, bridge flag), Brooklyn → Rockaway')
ll2,M2=line("name like 'Marine Parkway%'",bb,'300d9e99',rev=True); emit('MP_NB',ll2,'Overture 300d9e99, drawn Brooklyn → Rockaway')
o=osm('marine')
for w in o['ways']:
    if 'bridge:support' in w[2] or w[2].get('man_made')=='bridge':
        c,_=centroid(w[1]); a=ll[0]; q=Point(loc(a,c)); print('   osm',w[0],f'{c[0]:.6f},{c[1]:.6f}','d',round(M.project(q),1),'off',round(M.distance(q),1),[(round(x,1),round(y)) for x,y in mrr(w[1])],{k:v for k,v in w[2].items() if k in('bridge:support','man_made','name','height')})
open(f'{D}/gen3.ts.txt','w').write('\n'.join(out)+'\n')

# ---- Marine Parkway: centre line between the two carriageways, tower positions
a=ll[0]; Ms=LineString([loc(a,p) for p in ll]); Mn=LineString([loc(a,p) for p in ll2])
best=None
for off in (4,-4):
    O=Ms.offset_curve(off); d=O.distance(Mn.interpolate(0.5,normalized=True))
    if best is None or d<best[0]: best=(d,O)
O=best[1]
if Point(O.coords[0]).distance(Point(Ms.coords[0]))>Point(O.coords[-1]).distance(Point(Ms.coords[0])): O=LineString(list(O.coords)[::-1])
dC=618+9.5
half=540*0.3048/2+3.5
T=[unloc(a,(O.interpolate(dC-half).x,O.interpolate(dC-half).y)), unloc(a,(O.interpolate(dC+half).x,O.interpolate(dC+half).y))]
ax=Axis(*T)
e0=unloc(a,O.coords[0]); e1=unloc(a,O.coords[-1])
print('MARINE centre line len',round(O.length),'towers',T,'frame ends',ax.sa(e0),ax.sa(e1),'max across of line pts',[ax.sa(unloc(a,p)) for p in O.coords])
out.append(f"const MP_T: V2[] = {fmt(T)}; // lift-tower centres: the cited 540 ft span centred on OpenStreetMap's movable span, on the line midway between Overture's two carriageways")
# ---- Kosciuszko anchors (middle of each main span)
for nm,pts,dT in (('KZ_EB',None,442),('KZ_WB',None,344)):
    pass
import re
src='\n'.join(out)
def pts_of(name):
    m=re.search(r'const '+name+r': V2\[\] = \[(.*?)\];',src); return [tuple(map(float,x.split(','))) for x in re.findall(r'\[([-\d\., ]+)\]',m.group(1))]
for nm,dT in (('KZ_EB',442),('KZ_WB',344)):
    P=pts_of(nm); a0=P[0]; M=LineString([loc(a0,p) for p in P]); q=M.interpolate(dT+624*0.3048/2); an=unloc(a0,(q.x,q.y))
    out.append(f"const {nm}_MID: V2 = [{an[0]:.6f}, {an[1]:.6f}]; // middle of the main span: {dT} + 95.1 m along the line")
    print(nm,'len',round(M.length),'anchor',an)
# ---- Pulaski paths
from shapely.geometry import box as sbox
pk=Axis((-73.952698,40.739007),(-73.952582,40.739473))
res=[]
for n,c,ls,i in ov('roads_region',"name = 'Pulaski Bridge'",(-73.96,40.733,-73.945,40.745)):
    M=LineString([(pk.al(p),pk.ac(p)) for p in ls.coords]); d=M.difference(sbox(-27,-60,27,60))
    for p in (list(d.geoms) if hasattr(d,'geoms') else [d]):
        if p.is_empty or p.length<20: continue
        p=p.simplify(1.0); cc=list(p.coords)
        if abs(cc[-1][0])<abs(cc[0][0]): cc=cc[::-1]
        l2=[unloc(pk.anchor,(s*pk.ux+o*pk.uy, s*pk.uy-o*pk.ux)) for s,o in cc]; res.append(l2)
        print(f'  PK {i[:8]} {p.length:.0f} m from ({cc[0][0]:.0f},{cc[0][1]:.0f}) to ({cc[-1][0]:.0f},{cc[-1][1]:.0f}) npts {len(cc)} end ground {elev(*l2[-1]):.1f}')
out.append("const PK_PATHS: V2[][] = [\n  "+',\n  '.join(fmt(p) for p in res)+"\n]; // Overture carriageways of the approach viaducts, from the bascule piers outward")
open(f'{D}/gen3.ts.txt','w').write('\n'.join(out)+'\n'); print('chars',sum(len(x) for x in out))
