import json, math, sys, pandas as pd, duckdb
from spec import SPEC
T='/home/user/nyc/data/tables/'
pl=pd.concat([pd.read_csv(T+'places_counties.csv'),pd.read_csv(T+'places_outer.csv')]).set_index('id')
towns=[]
for l in SPEC.strip().split('\n'):
    f=l.split('|'); k=f[0]
    if ',' in f[3]: lat,lon=map(float,f[3].split(','))
    else: lat,lon=pl.loc[f[3],['lat','lon']]
    towns.append((k,float(lat),float(lon)))
import sys
WIN=0.0065
c=duckdb.connect(); c.execute("install spatial; load spatial; set memory_limit='1500MB'")
t=pd.DataFrame(towns,columns=['k','lat','lon']); c.register('t',t)
q=f"""select t.k, r.class, r.name, ST_X(ST_StartPoint(r.geometry)) x0, ST_Y(ST_StartPoint(r.geometry)) y0,
 ST_X(ST_EndPoint(r.geometry)) x1, ST_Y(ST_EndPoint(r.geometry)) y1
 from t join read_parquet('/home/user/nyc/data/raw/overture/2026-10-21.0/roads_region.parquet') r
 on ST_Intersects(r.geometry, ST_MakeEnvelope(t.lon-{WIN},t.lat-{WIN*0.77},t.lon+{WIN},t.lat+{WIN*0.77}))
 where r.subtype='road' and r.class not in ('motorway','trunk','footway','path','pedestrian','steps','cycleway','track','service','driveway')"""
d=c.execute(q).df()
print(len(d))
import re
RANK={'primary':3,'secondary':3,'tertiary':2}
out={}
MAIN=re.compile(r'(main|broad|high|market|front|church|water|king|queen|post|old |king.s highway|boston post|albany|hudson)',re.I)
tt=t.set_index('k')
for k,g in d.groupby('k'):
    la,lo=tt.loc[k,'lat'],tt.loc[k,'lon']
    kx=111320*math.cos(math.radians(la)); ky=110540
    def agg(gg):
        sx=sy=0;n=0
        for r in gg.itertuples():
            dx=(r.x1-r.x0)*kx; dy=(r.y1-r.y0)*ky; L=math.hypot(dx,dy)
            if L<5: continue
            mx=((r.x0+r.x1)/2-lo)*kx; my=((r.y0+r.y1)/2-la)*ky
            w=L/(1+math.hypot(mx,my)/150)
            a=2*math.atan2(dx,dy); sx+=w*math.sin(a); sy+=w*math.cos(a); n+=1
        return (round((math.degrees(math.atan2(sx,sy))/2)%180),n,round(math.hypot(sx,sy)/max(1e-9,sum(1 for _ in [0])))) if n else None
    nm=g[g['name'].fillna('').map(lambda x: bool(MAIN.search(x)))]
    r=agg(nm) if len(nm)>=2 else None
    how='main-street name' if r else None
    if not r:
        top=max(RANK.get(x,1) for x in g['class']); r=agg(g[[RANK.get(x,1)==top for x in g['class']]]); how='top road class'
    if r: out[k]={'rot':r[0],'n':r[1],'how':how,'names':sorted(set(nm['name'].dropna()))[:4]}
json.dump(out,open('rot2.json','w'))
print(len(out),'missing',[k for k,_,_ in towns if k not in out])
