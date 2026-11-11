import sys,geopandas as gpd,matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt,pandas as pd,numpy as np
G=None
def load():
    global G
    if G is None:
        G=gpd.read_parquet('/home/user/nyc/data/interim/county_buildings.parquet',columns=['start_year','end_year','geometry'])
    return G
import duckdb
O='/home/user/nyc/data/raw/overture/2026-10-21.0/'
def lines(f,x0,y0,x1,y1,extra=''):
    con=duckdb.connect();con.execute('install spatial;load spatial')
    r=con.execute(f"select ST_AsText(geometry) from '{O}{f}.parquet' where ST_Intersects(geometry,ST_MakeEnvelope({x0},{y0},{x1},{y1})) {extra}").fetchall()
    import shapely.wkt
    return [shapely.wkt.loads(a[0]) for a in r]
def draw(name,lon,lat,half=0.012,years=(1940,1980)):
    g=load()
    dy=half;dx=half/0.76
    b=g.cx[lon-dx:lon+dx,lat-dy:lat+dy]
    h=pd.read_csv('/home/user/nyc/data/interim/reports/holes.csv')
    fig,ax=plt.subplots(1,len(years),figsize=(7*len(years)/1.0,7))
    for a,y in zip(np.atleast_1d(ax),years):
        s=b[(b.start_year<=y)&(b.end_year>y)]
        s.plot(ax=a,color='#555',linewidth=0)
        hh=h[(h.year==y)&(abs(h.lon-lon)<dx)&(abs(h.lat-lat)<dy)]
        for fn,c,w in (('roads_region','#9bd',.5),('rail','#c63',.9)):
            try:
                for l in lines(fn,lon-dx,lat-dy,lon+dx,lat+dy):
                    for p in getattr(l,'geoms',[l]):
                        xs,ys=p.xy;a.plot(xs,ys,color=c,lw=w)
            except Exception as e: print(fn,e)
        a.scatter(hh.lon,hh.lat,s=hh.ha*3,facecolors='none',edgecolors='r')
        a.set_xlim(lon-dx,lon+dx);a.set_ylim(lat-dy,lat+dy);a.set_title(f'{name} {y} n={len(s)}');a.set_aspect(1/0.76)
        a.grid(True,lw=.3);a.tick_params(labelsize=6)
    plt.tight_layout();plt.savefig(f'/home/user/nyc/data/interim/holes_nj_cities_raw/{name}.png',dpi=70);plt.close()
if __name__=='__main__':
    n,lon,lat=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]);half=float(sys.argv[4]) if len(sys.argv)>4 else .012
    yrs=tuple(int(v) for v in sys.argv[5].split(',')) if len(sys.argv)>5 else (1940,1980)
    draw(n,lon,lat,half,yrs)
