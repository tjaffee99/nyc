import sys,duckdb
from shapely import wkb
from shapely.geometry import Point
par={'t':'nj_mercer','n':'nj_middlesex'}[sys.argv[1]]
con=duckdb.connect(); 
for a in sys.argv[2:]:
    lon,lat,r=map(float,a.split(','))
    e=r/90000
    rows=con.execute(f"select id,name,area_m2,height_m,year_raw,heap,lon,lat,geometry from 'data/interim/counties/{par}.parquet' where lon between ? and ? and lat between ? and ?",[lon-e,lon+e,lat-e,lat+e]).fetchall()
    print('--',a)
    pt=Point(lon,lat)
    for r_ in sorted(rows,key=lambda r:-r[2])[:7]:
        g=wkb.loads(bytes(r_[8])); print(' ',r_[0][:8],str(r_[1])[:34],round(r_[2]),r_[3] and round(r_[3]),r_[4],r_[5],'d=%.0f'%(g.distance(pt)*111000),'IN' if g.contains(pt) else '')
