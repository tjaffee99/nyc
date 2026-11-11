import duckdb,shapely.wkb as w
c=duckdb.connect();c.execute("SET memory_limit='1500MB'")
r=c.execute("select id,name,lon,lat,area_m2,year_raw,heap,prop_class,geometry from 'data/interim/counties/nj_mercer.parquet' where muni ilike '%PRINCETON%' and (name is not null or area_m2>1500) order by area_m2 desc").fetchall()
import csv
o=csv.writer(open('data/research/princeton_build/targets.csv','w'))
o.writerow('id name lon lat area year_raw heap cls'.split())
for x in r: o.writerow(x[:8])
print(len(r))
