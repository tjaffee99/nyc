import duckdb,sys
con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
w,s,e,n,ma=map(float,sys.argv[1:6])
for r in con.execute(f"select id,name,round(lon,5),round(lat,5),round(area_m2),height_m,year_raw from read_parquet('data/interim/counties/nj_mercer.parquet') where lon between {w} and {e} and lat between {s} and {n} and area_m2>{ma} order by lat desc, lon").fetchall(): print(r)
