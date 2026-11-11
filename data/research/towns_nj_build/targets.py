import duckdb,sys
from shapely import wkb
town=sys.argv[1]
f={'trenton':('nj_mercer',"muni ilike '%TRENTON%'"),'nb':('nj_middlesex',"muni ilike '%NEW BRUNSWICK%' or muni ilike '%PISCATAWAY%'")}[town]
c=duckdb.connect(); c.execute("SET memory_limit='1500MB'")
rows=c.execute(f"select id,name,muni,lon,lat,area_m2,height_m,year_raw,heap,prop_class from 'data/interim/counties/{f[0]}.parquet' where ({f[1]}) and (name is not null or area_m2>2500) and (year_raw is null or heap) order by area_m2 desc").fetchall()
print(len(rows))
for r in rows[:int(sys.argv[2])]: print(r[0],'|',r[1],'|',r[2][:6],round(r[3],4),round(r[4],4),round(r[5]),r[6],r[7],r[8],r[9])
