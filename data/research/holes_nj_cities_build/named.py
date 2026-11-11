import sys,duckdb,geopandas as gpd,matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt,shapely.wkt
n,lon,lat,half,yr=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),int(sys.argv[5])
dx=half/0.76
g=gpd.read_parquet('/home/user/nyc/data/interim/county_buildings.parquet',columns=['start_year','end_year','geometry']).cx[lon-dx:lon+dx,lat-half:lat+half]
g=g[(g.start_year<=yr)&(g.end_year>yr)]
fig,ax=plt.subplots(figsize=(9,9));g.plot(ax=ax,color='#999',linewidth=0)
con=duckdb.connect();con.execute('install spatial;load spatial')
for f in ('roads_local','roads_region'):
    for nm,w in con.execute(f"select name,ST_AsText(geometry) from '/home/user/nyc/data/raw/overture/2026-10-21.0/{f}.parquet' where ST_Intersects(geometry,ST_MakeEnvelope({lon-dx},{lat-half},{lon+dx},{lat+half}))").fetchall():
        for p in getattr(shapely.wkt.loads(w),'geoms',[shapely.wkt.loads(w)]):
            x,y=p.xy;ax.plot(x,y,color='#58c',lw=.6)
            if nm and p.length>0.002: m=p.interpolate(.5,normalized=True);ax.text(m.x,m.y,nm,fontsize=5,color='#036')
ax.set_xlim(lon-dx,lon+dx);ax.set_ylim(lat-half,lat+half);ax.set_aspect(1/0.76);ax.grid(True,lw=.3);ax.set_title(f'{n} {yr}')
plt.savefig(f'/home/user/nyc/data/interim/holes_nj_cities_raw/{n}.png',dpi=85);
