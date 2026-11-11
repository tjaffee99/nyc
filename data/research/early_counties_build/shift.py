import geopandas as gpd, pandas as pd, numpy as np, math, json
from spec import SPEC
T='/home/user/nyc/data/tables/'
pl=pd.concat([pd.read_csv(T+'places_counties.csv'),pd.read_csv(T+'places_outer.csv')]).set_index('id')
g=gpd.read_file('/home/user/nyc/data/manual/natural/counties/natural_1609_counties.geojson')
wet=g[g.cover.isin(['tidal_marsh','freshwater_wetland','water'])][['geometry']]
sidx=wet.sindex
def wetfrac(lat,lon,R=160,n=40):
    rng=np.random.default_rng(7); a=rng.uniform(0,2*math.pi,n); d=R*np.sqrt(rng.uniform(size=n))
    P=gpd.GeoSeries(gpd.points_from_xy(lon+d*np.sin(a)/(111320*math.cos(math.radians(lat))), lat+d*np.cos(a)/110540),crs=4326)
    return len(gpd.sjoin(gpd.GeoDataFrame(geometry=P),wet,predicate='within'))/n
out={}
for line in SPEC.strip().split('\n'):
    f=line.split('|'); k=f[0]; loc=f[3]
    lat,lon=(map(float,loc.split(',')) if ',' in loc else pl.loc[loc,['lat','lon']])
    if not (-74.45<lon<-73.55 and 40.55<lat<41.35): continue
    w0=wetfrac(lat,lon)
    if w0<0.15: continue
    best=(w0,0,lat,lon)
    for dist in range(50,751,50):
        for ang in range(0,360,30):
            la=lat+dist*math.cos(math.radians(ang))/110540; lo=lon+dist*math.sin(math.radians(ang))/(111320*math.cos(math.radians(lat)))
            w=wetfrac(la,lo)
            if w<best[0]-0.05 or (w<=best[0] and False): best=(w,dist,la,lo)
        if best[0]<0.05: break
    out[k]={'w0':round(w0,2),'w':round(best[0],2),'moved_m':best[1],'lat':round(float(best[2]),5),'lon':round(float(best[3]),5)}
    print(k,out[k])
json.dump(out,open('shift.json','w'))
