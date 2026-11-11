import sys, duckdb, math
from shapely import wkb
from shapely.geometry import Point
# usage: near.py City r minarea "label:lon,lat" ...
city=sys.argv[1]; r=float(sys.argv[2]); mina=float(sys.argv[3])
f={'Stamford':'ct_western_connecticut','Bridgeport':'ct_greater_bridgeport'}[city]
con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
for a in sys.argv[4:]:
    lab,c=a.split(':'); lon,lat=map(float,c.split(','))
    kx=111320*math.cos(math.radians(lat)); dl=r/kx; dt=r/110574
    print('##',lab,lon,lat)
    rows=con.execute(f"select id,name,area_m2,height_m,year_raw,heap,geometry from read_parquet('/home/user/nyc/data/interim/counties/{f}.parquet') where lon between {lon-dl*1.5} and {lon+dl*1.5} and lat between {lat-dt*1.5} and {lat+dt*1.5} and muni='{city}' and area_m2>={mina}").fetchall()
    out=[]
    for id,n,ar,h,y,hp,g in rows:
        p=wkb.loads(bytes(g)); P=Point(lon,lat)
        d=0 if p.contains(P) else p.distance(P)*111000*0.8
        if d<=r: out.append((d,id,n,ar,h,y,hp))
    for d,id,n,ar,h,y,hp in sorted(out)[:8]: print(f"  {id[:8]} d={d:.0f} area={ar:.0f} h={h and round(h,1)} yr={y} heap={hp} name={n}")
