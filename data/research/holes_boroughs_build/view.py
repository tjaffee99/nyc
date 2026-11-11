"""python -I view.py lon lat half_m year out.png [scale]  -- aerial mosaic (z17) with today's buildings standing in `year` (green) and others (red, thin), 100 m ticks"""
import sys, math, os, duckdb, numpy as np
from PIL import Image, ImageDraw
lon,lat,half,year,out=float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3]),int(sys.argv[4]),sys.argv[5]
sc=float(sys.argv[6]) if len(sys.argv)>6 else 1.0
Z=17; N=2**Z; R=6378137.0
def px(lo,la):
    x=(lo+180)/360*N*256; y=(1-math.log(math.tan(math.radians(la))+1/math.cos(math.radians(la)))/math.pi)/2*N*256; return x,y
cx,cy=px(lon,lat); mpp=2*math.pi*R*math.cos(math.radians(lat))/(N*256); h=half/mpp
x0,y0,x1,y1=int(cx-h),int(cy-h),int(cx+h),int(cy+h)
img=Image.new('RGB',(x1-x0,y1-y0),(40,40,40))
for tx in range(x0//256,x1//256+1):
  for ty in range(y0//256,y1//256+1):
    for ext in('png','jpg'):
      p=f'data/raw/aerial/{year if year in(1924,1951) else 1951}/{Z}/{tx}/{ty}.{ext}'
      if os.path.exists(p):
        t=Image.open(p).convert('RGB'); img.paste(t,(tx*256-x0,ty*256-y0)); break
dr=ImageDraw.Draw(img)
con=duckdb.connect(); con.execute("INSTALL spatial; LOAD spatial;")
dx=half*1.2/(111320*math.cos(math.radians(lat))); dy=half*1.2/111320
rows=con.execute(f"select ST_AsText(geometry),start_year,end_year from 'data/interim/nyc_buildings.parquet' where lon between {lon-dx} and {lon+dx} and lat between {lat-dy} and {lat+dy}").fetchall()
import shapely.wkt
for w,s,e in rows:
    g=shapely.wkt.loads(w)
    for q in (g.geoms if hasattr(g,'geoms') else [g]):
        pts=[(px(a,b)[0]-x0,px(a,b)[1]-y0) for a,b in q.exterior.coords]
        col=(0,255,0) if s<=year<e else (255,50,50)
        dr.line(pts,fill=col,width=1)
for k in range(-int(half//100),int(half//100)+1):
    X=h+k*100/mpp
    dr.line([(X,0),(X,8)],fill=(255,255,0)); dr.line([(0,X),(8,X)],fill=(255,255,0))
dr.text((10,10),f'{year} centre {lon},{lat} ticks 100 m, green=standing then, red=other',fill=(255,255,0))
if sc!=1: img=img.resize((int(img.width*sc),int(img.height*sc)))
if len(sys.argv)>7:
    step=float(sys.argv[7]); d2=ImageDraw.Draw(img); cxp=img.width/2; cyp=img.height/2; k=step/(mpp/sc)
    n=int(half//step)
    for i in range(-n,n+1):
        X=cxp+i*k; Y=cyp-i*k
        d2.line([(X,0),(X,img.height)],fill=(0,200,255) if i else (255,255,0),width=1); d2.line([(0,Y),(img.width,Y)],fill=(0,200,255) if i else (255,255,0),width=1)
        d2.text((X+2,2),f'E{int(i*step)}',fill=(255,255,0)); d2.text((2,Y+2),f'N{int(i*step)}',fill=(255,255,0))
img.save(out); print(out,img.size,'m/px',round(mpp/sc,2))
