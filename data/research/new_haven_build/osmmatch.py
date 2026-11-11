import json,pandas as pd,duckdb
from shapely import wkb
from shapely.geometry import Polygon,Point
ways=json.load(open('research/new_haven_build/osm_ways.json'));wd=json.load(open('research/new_haven_build/wd_osm.json'))
c=duckdb.connect();df=c.execute("select id,name,area_m2,year_raw,heap,geometry from 'interim/counties/ct_south_central_connecticut.parquet' where muni='New Haven'").fetchdf()
from shapely.strtree import STRtree
g=[wkb.loads(bytes(b)) for b in df.geometry];T=STRtree(g)
used=set(pd.read_csv('research/new_haven_build/ct_used_ids.csv').iloc[:,0])
for wid,v in ways.items():
    t=v['t'];q=t.get('wikidata');sd=t.get('start_date')
    e=wd.get(q,{}) if q else {}
    yrs=(e.get('inc') or [])+(e.get('op') or [])
    if not(sd or yrs) or 'building' not in t:continue
    p=Polygon(v['pts']).representative_point() if len(v['pts'])>3 else None
    if p is None:continue
    for i in T.query(p,predicate='within'):
        f=df.iloc[i]
        print(wid,'|',t.get('name'),'|osm sd',sd,'|wd',yrs,'|fp',f['name'],int(f.area_m2),f.year_raw,f.heap,'USED' if f.id in used else '')
