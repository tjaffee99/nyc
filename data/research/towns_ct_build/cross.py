import sys, json, duckdb
from shapely import wkb, STRtree
from shapely.geometry import Point
city=sys.argv[1]; f={'Stamford':'ct_western_connecticut','Bridgeport':'ct_greater_bridgeport'}[city]
pts=json.load(open(f'/home/user/nyc/data/interim/towns_ct_raw/cris_{city.lower()}.json'))
P=[(Point(x['geometry']['x'],x['geometry']['y']),x['attributes']) for x in pts if x.get('geometry')]
con=duckdb.connect()
rows=con.execute(f"select id,name,area_m2,height_m,year_raw,heap,geometry from read_parquet('/home/user/nyc/data/interim/counties/{f}.parquet') where muni='{city}' and (name is not null or area_m2>1500)").fetchall()
polys=[]
for id,n,ar,h,y,hp,g in rows:
    p=wkb.loads(bytes(g)); polys.append(p)
tree=STRtree([p for p,_ in P])
out=[]
for (id,n,ar,h,y,hp,g),p in zip(rows,polys):
    idx=tree.query(p,predicate='contains')
    if len(idx)==0: continue
    a=[P[i][1] for i in idx]
    out.append((ar,id,n,y,hp,[(x['NAME'],x['STNUM'],x['ST_NAME'],x['ConstructD']) for x in a][:4]))
out.sort(reverse=True)
for ar,id,n,y,hp,a in out:
    if (y is None or hp) or '-all' in sys.argv: print(f"{id[:8]} {ar:.0f} nm={n} yr={y}{'H' if hp else ''} :: {a}")
print(len(out),file=sys.stderr)
