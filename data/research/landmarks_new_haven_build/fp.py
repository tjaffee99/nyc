import sys, duckdb, shapely
from shapely import wkb
from shapely.geometry import Point
import math
# usage: fp.py lon lat radius_m [minarea]
lon, lat, r = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
mina = float(sys.argv[4]) if len(sys.argv) > 4 else 0
dl = r/111320/math.cos(math.radians(lat)); dt = r/110574
con = duckdb.connect(); con.execute("SET memory_limit='1500MB'")
rows = con.execute(f"""select id,name,area_m2,height_m,year_raw,prop_class,geometry,lon,lat from read_parquet('/home/user/nyc/data/interim/counties/ct_south_central_connecticut.parquet')
 where lon between {lon-dl} and {lon+dl} and lat between {lat-dt} and {lat+dt} and muni='New Haven' and area_m2>={mina} order by area_m2 desc""").fetchall()
k = 111320*math.cos(math.radians(lat))
for id,name,a,h,y,pc,g,lo,la in rows:
    print(f"{id} | {name} | area {a:.0f} | h {h} | yr {y} | {pc} | ({(lo-lon)*k:.0f},{(la-lat)*110574:.0f})")
