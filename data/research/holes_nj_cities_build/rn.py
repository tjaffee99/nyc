import duckdb,sys
x0,y0,x1,y1=map(float,sys.argv[1:5]);pat=sys.argv[5] if len(sys.argv)>5 else '%'
con=duckdb.connect();con.execute('install spatial;load spatial')
for f in ('roads_local','roads_region'):
    O=f'/home/user/nyc/data/raw/overture/2026-10-21.0/{f}.parquet'
    r=con.execute(f"""select name, round(avg(ST_X(ST_Centroid(geometry))),4), round(avg(ST_Y(ST_Centroid(geometry))),4), round(min(ST_XMin(geometry)),4),round(min(ST_YMin(geometry)),4),round(max(ST_XMax(geometry)),4),round(max(ST_YMax(geometry)),4) from '{O}' where ST_Intersects(geometry,ST_MakeEnvelope({x0},{y0},{x1},{y1})) and name is not null and name ilike '{pat}' group by name order by name""").fetchall()
    for a in r: print(f[6:],a)
