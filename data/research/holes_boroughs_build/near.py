import sys, duckdb
lon,lat,r=float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3])
mn=int(sys.argv[4]) if len(sys.argv)>4 else 0
con=duckdb.connect(); con.execute("INSTALL spatial; LOAD spatial;")
dx=r/(111320*0.757); dy=r/111320
q=f"""select bin,name,start_year,end_year,year_confidence,year_src,round(area) a,round(height_m) h,round(lon,5) lon,round(lat,5) lat,bldgclass from 'data/interim/nyc_buildings.parquet'
where lon between {lon-dx} and {lon+dx} and lat between {lat-dy} and {lat+dy} and area>={mn} order by area desc limit 80"""
import pandas as pd; pd.set_option('display.width',250); pd.set_option('display.max_colwidth',40)
print(con.execute(q).df().to_string())
