import sys, duckdb, math
# usage: fp.py file lonmin latmin lonmax latmax [minarea]
f,a,b,c,d=sys.argv[1],*map(float,sys.argv[2:6]); m=float(sys.argv[6]) if len(sys.argv)>6 else 2500
con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
rows=con.execute(f"""select id,name,muni,area_m2,height_m,year_raw,heap,prop_class,lon,lat from read_parquet('/home/user/nyc/data/interim/counties/{f}.parquet')
 where lon between {a} and {c} and lat between {b} and {d} and (name is not null and name<>'' or area_m2>={m}) order by area_m2 desc""").fetchall()
for r in rows: print(r[0][:8],'|',r[1],'|',r[2],'|a',round(r[3]),'|h',r[4],'|y',r[5],r[6],'|',r[7],'|',round(r[8],5),round(r[9],5))
