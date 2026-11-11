import duckdb,json,re,pandas as pd,shapely
from shapely import wkb
from shapely.strtree import STRtree
from shapely.geometry import Point
c=duckdb.connect();c.execute("SET memory_limit='1500MB'")
df=c.execute("""select id,name,area_m2,year_raw,heap,prop_class,geometry from 'interim/counties/ct_south_central_connecticut.parquet' where muni='New Haven'""").fetchdf()
df['g']=[wkb.loads(bytes(b)) for b in df.geometry];df=df.drop(columns='geometry')
tree=STRtree(list(df.g))
rows=json.load(open('research/new_haven_build/conncris_nh.json'))
out=[]
rows=[r for r in rows if r.get('geometry')]
print(len(rows))
for r in rows:
    a=r['attributes'];p=Point(r['geometry']['x'],r['geometry']['y'])
    for i in tree.query(p,predicate='within'):
        out.append(dict(cid=a['UNIQUE_ID'],cname=a['NAME'],cd=a['ConstructD'],per=a['Periods'],st=a['DesigStatu'],bi=int(i)))
m=pd.DataFrame(out);print(len(m),m.bi.nunique())
m.to_pickle('research/new_haven_build/join.pkl')
df.drop(columns='g').to_pickle('research/new_haven_build/df.pkl')
d=df.iloc[m.bi.values].reset_index(drop=True);m=m.reset_index(drop=True)
m['yr']=pd.to_numeric(m.cd.str.extract(r'^(\d{4})')[0]);m['circa']=m.cd.fillna('').str.contains('CIRCA')
m['year_raw']=d.year_raw;m['heap']=d.heap
print(m.yr.notna().sum())
x=m[m.yr.notna()&m.year_raw.notna()&~m.circa]
print('exact yr vs assessor diff abs<=2:',((x.yr-x.year_raw).abs()<=2).mean(),len(x))
print(x[x.heap.eq(True)].shape, ((x[x.heap.eq(True)].yr-x[x.heap.eq(True)].year_raw).abs()).describe())
print('heap rows w/ cd', (m.heap.eq(True)&m.yr.notna()).sum(), 'of heap total', df.heap.eq(True).sum(), 'footprints', len(df), 'missing year',df.year_raw.isna().sum())
