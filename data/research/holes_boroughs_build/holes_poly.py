"""recompute the holes of holes.py (detail grid) for the years given and save each hole's cells as polygons (WGS84) + bbox -> data/interim/holes_boroughs_raw/holes_poly.geojson"""
import sys, json, numpy as np, pandas as pd, duckdb, shapely, geopandas as gpd
sys.path.insert(0,'pipeline')
from scipy import ndimage
from common import INTERIM
from covers import SUBURB, URBAN
from holes import cover_at, R
YEARS=[int(y) for y in sys.argv[1:]]
m=json.loads((INTERIM/"grid_detail_meta.json").read_text())
covers=np.load(INTERIM/"grid_detail_covers.npy",mmap_mode="r"); years=np.load(INTERIM/"grid_detail_years.npy",mmap_mode="r")
rows,cols,res,X0,Y0=m["rows"],m["cols"],m["res"],m["X0"],m["Y0"]
con=duckdb.connect(); con.execute("SET memory_limit='2500MB'; INSTALL spatial; LOAD spatial;")
b=con.execute("select ST_X(ST_Centroid(geometry)) lon, ST_Y(ST_Centroid(geometry)) lat, start_year, end_year from 'data/interim/nyc_buildings.parquet'").df()
p=con.execute("select lon,lat,start_year,end_year from 'data/interim/nyc_building_points.parquet'").df()
cp=[con.execute(f"select lon,lat,start_year,end_year from 'data/interim/{f}.parquet'").df() for f in ('county_points_inner','county_points_outer')]
cb=con.execute("select ST_X(ST_Centroid(geometry)) lon, ST_Y(ST_Centroid(geometry)) lat, start_year, end_year from 'data/interim/county_buildings.parquet' where end_year<9000").df()
b=pd.concat([b,p,cb]+cp,ignore_index=True)
X=np.radians(b.lon.values)*R; Y=R*np.log(np.tan(np.pi/4+np.radians(b.lat.values)/2))
c=np.rint((X-X0)/res).astype(int); r=np.rint((Y0-Y)/res).astype(int)
ok=(c>=0)&(c<cols)&(r>=0)&(r<rows); b=b[ok]; c=c[ok]; r=r[ok]
# footprint fix: large buildings (>= 2000 m2) mark every cell they cover, not only the centroid's
import shapely.wkt
big=con.execute("select ST_AsText(geometry) w,start_year s,end_year e from 'data/interim/nyc_buildings.parquet' where area>=2000").fetchall()
ER,EC,ES,EE=[],[],[],[]
for w,s_,e_ in big:
    g=shapely.wkt.loads(w); x0_,y0_,x1_,y1_=g.bounds
    X0b=np.radians(x0_)*R; X1b=np.radians(x1_)*R; Yb0=R*np.log(np.tan(np.pi/4+np.radians(y0_)/2)); Yb1=R*np.log(np.tan(np.pi/4+np.radians(y1_)/2))
    cs=np.arange(int(np.floor((X0b-X0)/res)),int(np.ceil((X1b-X0)/res))+1); rs=np.arange(int(np.floor((Y0-Yb1)/res)),int(np.ceil((Y0-Yb0)/res))+1)
    CC,RR=np.meshgrid(cs,rs); CC=CC.ravel(); RR=RR.ravel()
    lo=np.degrees((X0+(CC+0.5)*res)/R); la=np.degrees(2*np.arctan(np.exp((Y0-(RR+0.5)*res)/R))-np.pi/2)
    m_=shapely.contains_xy(g,lo,la)
    ER.append(RR[m_]); EC.append(CC[m_]); ES.append(np.full(m_.sum(),s_)); EE.append(np.full(m_.sum(),e_))
ER=np.concatenate(ER); EC=np.concatenate(EC); ES=np.concatenate(ES); EE=np.concatenate(EE)
okk=(EC>=0)&(EC<cols)&(ER>=0)&(ER<rows); ER,EC,ES,EE=ER[okk],EC[okk],ES[okk],EE[okk]
print('large footprints',len(big),'cells',len(ER),flush=True)
cell_ha=(res*np.cos(np.radians(40.75)))**2/1e4
k=int(round(60/(res*0.758)))
inv=lambda x,y:(np.degrees(x/R),np.degrees(2*np.arctan(np.exp(y/R))-np.pi/2))
out=[]
for y in YEARS:
    urb=np.isin(cover_at(covers,years,y),[URBAN,SUBURB])
    alive=(b.start_year.values<=y)&(b.end_year.values>y)
    has=np.zeros((rows,cols),bool); has[r[alive],c[alive]]=True; al2=(ES<=y)&(EE>y); has[ER[al2],EC[al2]]=True
    hole=ndimage.binary_opening(urb&~ndimage.binary_dilation(has,iterations=max(k,1)),iterations=1)
    lab,n=ndimage.label(hole)
    sizes=ndimage.sum(hole,lab,index=np.arange(1,n+1))*cell_ha
    for i in np.where(sizes>=3)[0]:
        rr,cc=np.where(lab==i+1)
        lo0,la0=inv(X0+cc.min()*res,Y0-rr.max()*res); lo1,la1=inv(X0+(cc.max()+1)*res,Y0-(rr.min()-1)*res)
        out.append(dict(year=y,ha=round(float(sizes[i]),1),lon=round((lo0+lo1)/2,5),lat=round((la0+la1)/2,5),w=round(lo0,5),s=round(la0,5),e=round(lo1,5),n=round(la1,5)))
        np.save(f'data/interim/holes_boroughs_raw/holefp_{y}_{i}.npy',np.stack([rr,cc]).astype('int32'))
        out[-1]['id']=f'{y}_{i}'
pd.DataFrame(out).to_csv('data/interim/holes_boroughs_raw/holes_bbox_fp.csv',index=False)
print(len(out))
