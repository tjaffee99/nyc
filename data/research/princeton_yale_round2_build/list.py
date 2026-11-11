import duckdb,sys,csv,shapely
from shapely import wkb
town=sys.argv[1]
if town=='p':
    f='data/interim/counties/nj_mercer.parquet'; w="muni ilike '%PRINCETON%'"; mn=2500; tabs=['nj_outer','princeton']
else:
    f='data/interim/counties/ct_south_central_connecticut.parquet'; w="muni='New Haven'"; mn=3000; tabs=['ct','new_haven']
con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
rows=con.execute(f"select id,name,lon,lat,area_m2,height_m,year_raw,heap,prop_class,geometry from '{f}' where {w} and area_m2>{mn} order by area_m2 desc").fetchall()
pts=[]
for t in tabs:
    for r in csv.DictReader(open(f'data/tables/known_building_dates.{t}.csv')): pts.append(shapely.Point(float(r['lon']),float(r['lat'])))
from shapely.strtree import STRtree
tr=STRtree(pts)
for r in rows:
    g=wkb.loads(bytes(r[9]))
    if len(tr.query(g,predicate='contains')): continue
    print(r[0][:8],r[1],round(r[2],5),round(r[3],5),int(r[4]),r[5],r[6],r[7],r[8])
