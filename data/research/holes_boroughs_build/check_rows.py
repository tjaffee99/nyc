import sys, math, pandas as pd
from PIL import Image, ImageDraw
img,lon0,lat0,half,sc,pref,year=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5]),sys.argv[6],sys.argv[7]
im=Image.open(img).convert('RGB'); dr=ImageDraw.Draw(im)
Z=17; N=2**Z; R=6378137.0
mpp=2*math.pi*R*math.cos(math.radians(lat0))/(N*256)/sc
def tp(lo,la): return (im.width/2+(lo-lon0)*111320*math.cos(math.radians(lat0))/mpp, im.height/2-(la-lat0)*111320/mpp)
t=pd.read_csv('data/tables/notable_demolished.boroughs2.csv')
for r in t.itertuples():
    if not r.id.startswith(pref): continue
    if isinstance(r.outline,str) and r.outline.strip():
        pts=[tuple(float(v) for v in q.split()) for q in r.outline.split(';')]; dr.polygon([tp(*p) for p in pts],outline=(255,0,255))
    else:
        d=float(r.footprint_m.split('x')[0]); c=tp(r.lon,r.lat); rad=d/2/mpp; dr.ellipse([c[0]-rad,c[1]-rad,c[0]+rad,c[1]+rad],outline=(255,0,255),width=2)
im.save(sys.argv[8])
