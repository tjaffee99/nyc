"""python -I tankpick2.py name lon lat half  -> re-scores detector circles on the mosaic: bright uniform disc with a dark shadow side"""
import sys, math, os, numpy as np, pandas as pd
from PIL import Image, ImageDraw
exec(open('data/research/lost_works_build/tanks2.py').read().split("a=np.asarray")[0].split("name=sys.argv[1]")[0])
name=sys.argv[1]; lon,lat,half=map(float,sys.argv[2:5]); year=1951
import importlib
src=open('data/research/lost_works_build/tanks2.py').read()
pre=src.split("e=canny")[0].replace("name=sys.argv[1]; lon,lat,half,rmin,rmax=[float(x) for x in sys.argv[2:7]]; year=int(sys.argv[7]) if len(sys.argv)>7 else 1951","")
exec(pre)
t=pd.read_csv(f'data/interim/lost_works_raw/tanks_{name}.csv')
H,W=a.shape; out=[]
yy,xx=np.mgrid[:H,:W]
for r in t.itertuples():
    if not (22<=r.diam_m<=60): continue
    cx,cy=px(r.lon,r.lat); cx-=x0; cy-=y0; rp=r.diam_m/2/mpp
    if cx<rp*1.5 or cy<rp*1.5 or cx>W-rp*1.5 or cy>H-rp*1.5: continue
    d2=(xx-cx)**2+(yy-cy)**2; m=d2<=(0.85*rp)**2
    ins=a[m].mean(); sd=a[m].std()
    best=1
    for ang in range(0,360,45):
        s=(d2<=(1.4*rp)**2)&(d2>=(1.05*rp)**2)&(np.cos(np.arctan2(yy-cy,xx-cx)-math.radians(ang))>0.8)
        best=min(best,a[s].mean())
    out.append((r.lon,r.lat,r.diam_m,ins,sd,best))
o=pd.DataFrame(out,columns='lon lat diam_m ins sd shadow'.split())
o.to_csv(f'data/interim/lost_works_raw/tankscore_{name}.csv',index=False)
g=o[(o.ins>0.78)&(o.sd<0.09)&(o.shadow<0.42)].sort_values('ins',ascending=False)
keep=[]
for r in g.itertuples():
    if all(math.hypot((r.lon-k.lon)*84600,(r.lat-k.lat)*111000)>0.85*(r.diam_m+k.diam_m)/2 for k in keep): keep.append(r)
k=pd.DataFrame(keep); k.to_csv(f'data/interim/lost_works_raw/tankpick_{name}.csv',index=False); print(len(o),len(g),len(k)); print(k.round(2).head(40).to_string())
