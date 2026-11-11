import sys, csv, duckdb, math, shapely
from shapely import wkb
sys.path.insert(0,'/home/user/nyc/data/research/towns_ny_build')
from rows import R
con=duckdb.connect(); con.execute("SET memory_limit='1500MB'")
out=[]; ok=0; bad=[]
for pq,pre,name,yr,kind,url,note in R:
    f=f'/home/user/nyc/data/interim/counties/{pq}.parquet'
    rs=con.execute(f"select id,name,area_m2,geometry,lon,lat from read_parquet('{f}') where id like '{pre}%'").fetchall()
    if len(rs)!=1: bad.append((pre,name,len(rs))); continue
    id_,fn,a,g,lon,lat=rs[0]
    p=wkb.loads(bytes(g))
    rp=p.representative_point(); lo,la=round(rp.x,6),round(rp.y,6)
    pt=shapely.Point(lo,la)
    inside=p.contains(pt); ok+=inside
    key=('nyht_'+''.join(c if c.isalnum() else '_' for c in name.lower())[:40]).strip('_')
    out.append([key,name,la,lo,'',yr,9999,url,note,inside,round(a)])
print('rows',len(out),'inside',ok,'bad',bad)
ids=set()
with open('/home/user/nyc/data/tables/known_building_dates.hudson_towns.csv','w',newline='') as fh:
    w=csv.writer(fh); w.writerow('id,name,lat,lon,bin,start_year,end_year,source_url,note'.split(','))
    for r in out:
        k=r[0]; i=2
        while k in ids: k=r[0]+str(i); i+=1
        ids.add(k); r[0]=k; w.writerow(r[:9])
for r in out:
    if not r[9]: print('NOT INSIDE',r[1])
import collections
print(collections.Counter('West Point/HF' if x[0] in('ny_orange',) else 'Pk' for x in R))
