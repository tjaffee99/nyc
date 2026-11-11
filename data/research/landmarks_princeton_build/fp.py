import duckdb,json,math,sys
from shapely import wkb
con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
names=['Alexander Hall','East Pyne Hall','Chancellor Green','Holder Hall','Firestone Library','Robertson Hall','Lewis Library','Fine Hall','Jadwin Gymnasium','McCarter Theater Center','Whig Hall','Clio Hall','Princeton University Art Museum','Nassau Presbyterian Church','Nassau Inn']
rows=con.execute("select id,name,lon,lat,area_m2,height_m,year_raw,geometry from read_parquet('data/interim/counties/nj_mercer.parquet') where lon between -74.675 and -74.64 and lat between 40.33 and 40.36 and name in (%s)"%','.join("'%s'"%n for n in names)).fetchall() if False else None
import os
os.chdir('/home/user/nyc')
rows=con.execute("select id,name,lon,lat,area_m2,height_m,year_raw,geometry from read_parquet('data/interim/counties/nj_mercer.parquet') where lon between -74.675 and -74.64 and lat between 40.33 and 40.36 and name in (%s)"%','.join("'%s'"%n for n in names)).fetchall()
out={}
for i,n,lon,lat,a,h,y,g in rows:
    s=wkb.loads(bytes(g))
    if s.geom_type=='MultiPolygon': s=max(s.geoms,key=lambda p:p.area)
    rp=s.representative_point(); alon,alat=round(rp.x,6),round(rp.y,6)
    k=111320*math.cos(math.radians(alat))
    s2=s.simplify(0.35/111000)
    def loc(c): return [[round((x-alon)*k,1),round((y-alat)*110574,1)] for x,y in list(c)[:-1]]
    out.setdefault(n,[]).append(dict(id=i,anchor=[alon,alat],area=a,h=h,ext=loc(s2.exterior.coords),holes=[loc(r.coords) for r in s2.interiors]))
json.dump(out,open('data/research/landmarks_princeton_build/fps.json','w'))
for n,v in out.items():
    for o in v: print(n,o['id'][:8],o['anchor'],round(o['area']),o['h'],len(o['ext']),len(o['holes']))
