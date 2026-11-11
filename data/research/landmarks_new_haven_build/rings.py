import sys, duckdb, math, shapely
from shapely import wkb
# usage: rings.py id_prefix [id_prefix...]  -> prints anchor, rect info, ring as P(...)
con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
for pre in sys.argv[1:]:
    r=con.execute(f"select id,name,area_m2,height_m,geometry,lon,lat from read_parquet('/home/user/nyc/data/interim/counties/ct_south_central_connecticut.parquet') where id like '{pre}%' and muni='New Haven'").fetchall()
    for id,name,area,h,g,lon,lat in r:
        lon=round(lon,6); lat=round(lat,6)
        p=wkb.loads(bytes(g)); p=max(p.geoms,key=lambda z:z.area) if p.geom_type=='MultiPolygon' else p
        kx=111320*math.cos(math.radians(lat)); ky=110574
        q=shapely.Polygon([((x-lon)*kx,(y-lat)*ky) for x,y in p.exterior.coords])
        s=q.simplify(0.25)
        mr=q.minimum_rotated_rectangle; c=list(mr.exterior.coords)
        e=[(c[i+1][0]-c[i][0],c[i+1][1]-c[i][1]) for i in range(2)]
        L=[math.hypot(*v) for v in e]; k=0 if L[0]>=L[1] else 1
        brg=(math.degrees(math.atan2(e[k][0],e[k][1])))%180
        print(f"// {id} {name} area_m2 {area:.0f} (local {q.area:.0f}, simplified {s.area:.0f}) h {h} nv {len(q.exterior.coords)-1}->{len(s.exterior.coords)-1}")
        print(f"// anchor [{lon}, {lat}] rect {max(L):.1f} x {min(L):.1f} long-axis bearing {brg:.1f} rectcentre {mr.centroid.x:.1f},{mr.centroid.y:.1f} ({q.area/mr.area:.2f} fill)")
        pts=list(s.exterior.coords)[:-1]
        print("P("+", ".join(f"{x:.1f}, {y:.1f}" for x,y in pts)+")")
