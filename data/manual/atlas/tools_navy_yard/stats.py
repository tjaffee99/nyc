import pandas as pd, geopandas as gpd, json
from shapely.geometry import shape, Polygon
R='/home/user/nyc/'
k=pd.read_csv(R+'data/tables/known_building_dates.navy_yard.csv'); d=pd.read_csv(R+'data/tables/notable_demolished.navy_yard.csv')
b=gpd.read_parquet(R+'data/interim/navy_yard/yard_b.parquet'); w=gpd.read_parquet(R+'data/interim/navy_yard/win.parquet')
print(len(k),len(d))
# BIN exists / point inside footprint
bad=0
for _,r in k.iterrows():
    m=w[w.bin==r.bin]
    from shapely.geometry import Point
    ok=len(m)>0 and m.geometry.contains(Point(r.lon,r.lat)).any()
    if not ok: bad+=1; print('BAD',r.id,r.bin,len(m))
print('bad bin/point',bad)
yb=set(b.bin.dropna().astype(int)); inyard=k[k.bin.isin(yb)]; print('standing rows in yard polygon',len(inyard),'bins',inyard.bin.nunique(),'of',b[b.end_year==9999].bin.nunique(),'bins /',(b.end_year==9999).sum(),'footprints')
cov=b[(b.end_year==9999)&b.bin.isin(inyard.bin)]; print('footprints dated',len(cov))
# LPC conflicts
l=w[(w.year_src=='lpc')&w.bin.isin(k.bin)]; print('lpc overlap',l[['bin','start_year']].values.tolist())
# yard counts
ns=dict(zip(k.bin,k.start_year))
b=b.copy(); b['ns']=[ns.get(x,s) if x==x else s for x,s in zip(b.bin,b.start_year)]
dg=d.copy()
for y in (1810,1850,1880,1900,1925,1944,1966):
    old=((b.start_year<=y)&(b.end_year>y)).sum(); cur=((b.ns<=y)&(b.end_year>y)).sum(); lost=((d.start_year<=y)&(d.end_year>y)).sum()
    print(y,'map now',old,'with dated rows',cur,'+ lost rows',lost,'=',cur+lost)
print('lost by start decade',(d.start_year//10*10).value_counts().sort_index().to_dict()); print('lost by end decade',(d.end_year//10*10).value_counts().sort_index().to_dict())
print((d.start_year>=d.end_year).sum(),(k.start_year<1801).sum(),(d.start_year<1801).sum(),d.end_year.max(),k.start_year.max())
# admirals row
v=b[(b.end_year<9999)]; 
