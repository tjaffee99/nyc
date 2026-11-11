import duckdb,json,sys,pickle
import shapely.wkb as W
from shapely.geometry import Point
from shapely.strtree import STRtree
def load():
    c=duckdb.connect();c.execute("SET memory_limit='1500MB'")
    rows=c.execute("select id,name,area_m2,year_raw,heap,prop_class,geometry from 'data/interim/counties/nj_mercer.parquet' where muni ilike '%PRINCETON%'").fetchall()
    geoms=[W.loads(bytes(r[6])) for r in rows]
    return rows,geoms,STRtree(geoms)
if __name__=='__main__':
    rows,geoms,tree=load()
    items=json.load(open(sys.argv[1]))  # list of [name,lat,lon]
    for name,lat,lon in items:
        p=Point(lon,lat)
        idx=tree.query(p.buffer(0.0005))
        out=[]
        for i in idx:
            d=geoms[i].distance(p)*95000
            out.append((round(d),rows[i][0][:8],rows[i][1],round(rows[i][2]),rows[i][3],rows[i][5]))
        out.sort()
        print(name,'|',out[:4])
