import pandas as pd, geopandas as gpd, numpy as np, json
from shapely.geometry import Polygon, shape, Point
from shapely import affinity
from pyproj import Transformer
R='/home/user/nyc/'
d=pd.read_csv(R+'data/tables/notable_demolished.navy_yard.csv'); k=pd.read_csv(R+'data/tables/known_building_dates.navy_yard.csv')
w=gpd.read_parquet(R+'data/interim/navy_yard/win.parquet'); w=w.assign(g=w.to_crs(32618).geometry)
g=json.load(open(R+'data/manual/sites/sites.geojson')); yard=[shape(f['geometry']) for f in g['features'] if f['properties']['id']=='brooklyn_navy_yard'][0]
ym=gpd.GeoSeries([yard],crs=4326).to_crs(32618).iloc[0]
T=Transformer.from_crs(4326,32618,always_xy=True)
ns=dict(zip(k.bin,k.start_year))
nin=nsov=nvov=0
for _,r in d.iterrows():
    if isinstance(r.outline,str) and r.outline:
        pm=Polygon([T.transform(*map(float,p.split())) for p in r.outline.split(';')])
    else:
        W,D=map(float,r.footprint_m.split('x')); x,y=T.transform(r.lon,r.lat)
        pm=Polygon([(-W/2,-D/2),(W/2,-D/2),(W/2,D/2),(-W/2,D/2)]); pm=affinity.rotate(pm,-(r.rotation_deg-0),origin=(0,0)) if False else affinity.rotate(pm,90-r.rotation_deg-0,origin=(0,0)); pm=affinity.translate(pm,x,y)
        # long side D along bearing rotation_deg: base polygon has D along +y (bearing 0); rotate clockwise by rotation_deg
        pm=Polygon([(-W/2,-D/2),(W/2,-D/2),(W/2,D/2),(-W/2,D/2)]); pm=affinity.rotate(pm,-r.rotation_deg,origin=(0,0)); pm=affinity.translate(pm,x,y)
    fin=pm.intersection(ym).area/pm.area
    if fin>=0.5: nin+=1
    else: print('OUTSIDE',r.id,round(fin,2))
    for _,s in w.iterrows():
        if not s.g.intersects(pm): continue
        a=s.g.intersection(pm).area
        if a/min(s.g.area,pm.area)<0.3: continue
        sy=ns.get(s.bin,s.start_year) if s.bin==s.bin else s.start_year
        if sy<r.end_year and r.start_year<s.end_year:
            if s.end_year==9999: nsov+=1; print('stand-overlap',r.id,int(s.bin) if s.bin==s.bin else None,round(sy),s.year_src,round(a/min(s.g.area,pm.area),2))
            else: nvov+=1; print('van-overlap',r.id,round(a/min(s.g.area,pm.area),2))
print('inside yard',nin,'of',len(d),'| time-overlap pairs standing',nsov,'vanished',nvov)
