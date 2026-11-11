"""python -I blobs.py x0 y0 x1 y1 minarea  -> empty-ground blobs (land with no standing building within 12 m, not water, not park?) in UTM-ish metres"""
import sys, numpy as np, duckdb, shapely, geopandas as gpd
from scipy import ndimage
x0,y0,x1,y1=map(float,sys.argv[1:5]); amin=float(sys.argv[5])
c=duckdb.connect(); c.execute("install spatial; load spatial; SET geometry_always_xy=true")
env=f"ST_MakeEnvelope({x0},{y0},{x1},{y1})"; R="/home/user/nyc"
def q(sql):
    df=c.execute(sql).df(); return gpd.GeoSeries.from_wkb(df.g.apply(bytes),crs=4326)
b=q(f"select ST_AsWKB(geometry) g from '{R}/data/interim/county_buildings.parquet' where ST_Intersects(geometry,{env}) and end_year>2000")
w=q(f"select ST_AsWKB(geometry) g from '{R}/data/raw/overture/2026-10-21.0/base_water.parquet' where ST_Intersects(geometry,{env})")
r=q(f"select ST_AsWKB(ST_Buffer(geometry,0.00004)) g from '{R}/data/raw/overture/2026-10-21.0/roads_local.parquet' where ST_Intersects(geometry,{env})")
kx=111320*np.cos(np.radians((y0+y1)/2)); ky=110540; step=8
nx=int((x1-x0)*kx/step); ny=int((y1-y0)*ky/step)
from rasterio import features
from affine import Affine
tr=Affine((x1-x0)/nx,0,x0,0,-(y1-y0)/ny,y1)
def rast(g,buf=0): 
    gg=list(g.geometry if hasattr(g,'geometry') else g)
    return features.rasterize([(x,1) for x in gg if x is not None],out_shape=(ny,nx),transform=tr,fill=0).astype(bool) if len(gg) else np.zeros((ny,nx),bool)
B=rast(b); W=rast(w); Rd=rast(r)
occ=ndimage.binary_dilation(B,iterations=2)|W|Rd
lab,n=ndimage.label(~occ)
sizes=ndimage.sum(~occ,lab,range(1,n+1))*step*step
for i in np.argsort(-sizes)[:8]:
    if sizes[i]<amin: break
    ys,xs=np.where(lab==i+1); print(f"blob {sizes[i]:.0f} m2 centre lon {x0+xs.mean()*(x1-x0)/nx:.5f} lat {y1-ys.mean()*(y1-y0)/ny:.5f} extent x {x0+xs.min()*(x1-x0)/nx:.5f}..{x0+xs.max()*(x1-x0)/nx:.5f} y {y1-ys.max()*(y1-y0)/ny:.5f}..{y1-ys.min()*(y1-y0)/ny:.5f}")
