import duckdb
c=duckdb.connect();c.execute("SET memory_limit='1500MB'")
df=c.execute("""select id,name,lon,lat,round(area_m2) a,year_raw,heap,prop_class from 'interim/counties/ct_south_central_connecticut.parquet' where muni='New Haven' and ((name is not null and name<>'') or area_m2>1500) order by area_m2 desc""").fetchdf()
df.to_csv('research/new_haven_build/targets.csv',index=False)
print(len(df),(df.name.fillna('')!='').sum())
print(df.head(60).to_string())
