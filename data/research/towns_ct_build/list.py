import sys, duckdb
city=sys.argv[1]; f={'Stamford':'ct_western_connecticut','Bridgeport':'ct_greater_bridgeport'}[city]
con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
for r in con.execute(f"select id,name,round(area_m2),height_m,year_raw,heap,round(lon,5),round(lat,5) from read_parquet('/home/user/nyc/data/interim/counties/{f}.parquet') where muni='{city}' and (name is not null or area_m2>3000) order by area_m2 desc").fetchall(): print(*r,sep=' | ')
