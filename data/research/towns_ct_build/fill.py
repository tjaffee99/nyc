import re, math, duckdb, shapely
from shapely import wkb
from shapely.geometry import Point, box
from shapely.ops import nearest_points
F={'Stamford':'ct_western_connecticut','Bridgeport':'ct_greater_bridgeport'}
con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
cache={}
def fp(pre):
    if pre in cache: return cache[pre]
    for city,f in F.items():
        r=con.execute(f"select id,geometry,lon,lat from read_parquet('/home/user/nyc/data/interim/counties/{f}.parquet') where id like '{pre}%' and muni='{city}'").fetchall()
        if r:
            id,g,lon,lat=r[0]; lon=round(lon,6); lat=round(lat,6)
            p=wkb.loads(bytes(g)); p=max(p.geoms,key=lambda z:z.area) if p.geom_type=='MultiPolygon' else p
            kx=111320*math.cos(math.radians(lat))
            q=shapely.Polygon([((x-lon)*kx,(y-lat)*110574) for x,y in p.exterior.coords]).simplify(0.25)
            cache[pre]=(q,lon,lat); return cache[pre]
    raise KeyError(pre)
def ring(q): return 'P('+', '.join(f'{x:.1f}, {y:.1f}' for x,y in list(q.exterior.coords)[:-1])+')'
def inner(q,m,hint):
    s=q.buffer(-m); 
    if s.is_empty: s=q.buffer(-m/2)
    pt=nearest_points(s,Point(*hint))[0]; assert q.contains(pt); return f'{pt.x:.1f}, {pt.y:.1f}'
def big(g):
    return max(g.geoms,key=lambda z:z.area) if g.geom_type=='MultiPolygon' else g
src=open('ct-towns.tmpl.ts').read()
def sub(m):
    k=m.group(1)
    if k.startswith('R:'):
        a=k[2:].split(':'); q0=fp(a[0])[0]
        return ring(q0.simplify(float(a[1])) if len(a)>1 else q0)
    if k.startswith('A:'): _,lon,lat=fp(k[2:]); return f'[{lon}, {lat}]'
    q=lambda p:fp(p)[0]
    if k=='FISH_NAVE': return ring(big(q('74f16290').intersection(box(61,-50,140,50))).simplify(0.3))
    if k=='FISH_TOWER': return inner(q('74f16290'),6,(40,14))
    if k=='BC_RED': return ring(big(q('6f9ff273').intersection(box(-60,-100,60,10))).simplify(0.3))
    if k=='BC_WHITE': return ring(big(q('6f9ff273').intersection(box(-60,10,60,100))).simplify(0.3))
    if k=='CH_TOWER': return inner(q('3a230949'),5,(2,-17))
    if k=='SA_TOWER': return inner(q('449d69c0'),4,(-22,5))
    if k=='OTH_TOWER': return inner(q('aca65a09'),5,(19.1,11.0))
    raise KeyError(k)
out=re.sub(r'@([A-Za-z_:0-9.]+)@',sub,src)
open('/home/user/nyc/viewer/src/landmarks/ct-towns.ts','w').write(out)
print('ok',len(out))
