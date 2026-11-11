"""python -I tanks.py name lon lat half_m rmin_m rmax_m [year]  -> detect round tanks on the z17 aerial mosaic; writes data/interim/lost_works_raw/tanks_<name>.csv and overlay png"""
import sys, math, os, numpy as np
from PIL import Image, ImageDraw
from skimage.feature import canny
from skimage.transform import hough_circle, hough_circle_peaks
name=sys.argv[1]; lon,lat,half,rmin,rmax=[float(x) for x in sys.argv[2:7]]; year=int(sys.argv[7]) if len(sys.argv)>7 else 1951

import urllib.request
def fetch(year,Z,tx,ty,ext):
    loc=f'data/raw/aerial/{year}/{Z}/{tx}/{ty}.{ext}'
    if os.path.exists(loc): return loc
    c=f'data/interim/lost_works_raw/aer/{year}_{Z}_{tx}_{ty}.png'
    if ext!='png': return c+'x'
    if not os.path.exists(c):
        svc={'1951':'NYC_Orthos_1951','1924':'Ortho_1924_Mosaic'}[str(year)]
        try: open(c,'wb').write(urllib.request.urlopen(urllib.request.Request(f'https://tiles.arcgis.com/tiles/yG5s3afENB5iO9fj/arcgis/rest/services/{svc}/MapServer/tile/{Z}/{ty}/{tx}',headers={'User-Agent':'NYCThroughTime-research/0.1'}),timeout=30).read())
        except Exception as e: return c+'x'
    return c
Z=17; N=2**Z; R=6378137.0
def px(lo,la): return (lo+180)/360*N*256, (1-math.log(math.tan(math.radians(la))+1/math.cos(math.radians(la)))/math.pi)/2*N*256
def unpx(x,y):
    lo=x/(N*256)*360-180; la=math.degrees(math.atan(math.sinh(math.pi*(1-2*y/(N*256))))); return lo,la
cx,cy=px(lon,lat); mpp=2*math.pi*R*math.cos(math.radians(lat))/(N*256); h=half/mpp
x0,y0,x1,y1=int(cx-h),int(cy-h),int(cx+h),int(cy+h)
img=Image.new('L',(x1-x0,y1-y0),0); cov=np.zeros((y1-y0,x1-x0),bool)
for tx in range(x0//256,x1//256+1):
  for ty in range(y0//256,y1//256+1):
    for ext in('png','jpg'):
      p=fetch(year,Z,tx,ty,ext)
      if os.path.exists(p):
        t=Image.open(p).convert('L'); img.paste(t,(tx*256-x0,ty*256-y0)); cov[max(ty*256-y0,0):max(ty*256-y0+256,0),max(tx*256-x0,0):max(tx*256-x0+256,0)]=True; break
a=np.asarray(img).astype(float)/255
e=canny(a,sigma=2.0,low_threshold=0.08,high_threshold=0.2)
radii=np.arange(int(rmin/mpp),int(rmax/mpp)+1,1)
hs=hough_circle(e,radii)
acc,cxs,cys,rs=hough_circle_peaks(hs,radii,min_xdistance=int(rmin/mpp*1.6),min_ydistance=int(rmin/mpp*1.6),threshold=0.45*hs.max(),total_num_peaks=400)
rows=[]
im=Image.open(f'data/raw/aerial/{year}/{Z}/{x0//256}/{y0//256}.png') if False else img.convert('RGB')
dr=ImageDraw.Draw(im)
for ac,xx,yy,r in zip(acc,cxs,cys,rs):
    # brightness inside vs ring outside: tanks have bright roofs
    yy_,xx_=np.ogrid[:a.shape[0],:a.shape[1]]
    m=(xx_-xx)**2+(yy_-yy)**2<=r*r
    ring=((xx_-xx)**2+(yy_-yy)**2<=(r*1.35)**2)&~m
    ins=a[m].mean(); out=a[ring].mean()
    lo,la=unpx(x0+xx,y0+yy)
    rows.append((lo,la,2*r*mpp,ac,ins,out))
    dr.ellipse([xx-r,yy-r,xx+r,yy+r],outline=(255,0,0) if ins>out+0.05 else (255,255,0))
im.save(f'data/interim/lost_works_raw/tanks_{name}.png')
import csv
with open(f'data/interim/lost_works_raw/tanks_{name}.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow('lon lat diam_m acc inside outside'.split()); [w.writerow([round(v,6) if i<2 else round(v,2) for i,v in enumerate(r)]) for r in rows]
print(len(rows),'circles; image',im.size,'mpp',round(mpp,3))
