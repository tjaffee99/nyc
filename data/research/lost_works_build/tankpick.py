"""python -I tankpick.py name dmin dmax insmin gap  -> filtered tanks (bright discs), overlay on tiles"""
import sys, pandas as pd, numpy as np, math
from PIL import Image, ImageDraw
n=sys.argv[1]; dmin,dmax,im_,gap=map(float,sys.argv[2:6])
t=pd.read_csv(f'data/interim/lost_works_raw/tanks_{n}.csv')
t=t[(t.diam_m>=dmin)&(t.diam_m<=dmax)&(t.inside>=im_)&(t.inside-t.outside>=gap)].sort_values('acc',ascending=False)
keep=[]
for r in t.itertuples():
    ok=True
    for k in keep:
        d=math.hypot((r.lon-k.lon)*84600,(r.lat-k.lat)*111000)
        if d<0.8*(r.diam_m+k.diam_m)/2: ok=False;break
    if ok: keep.append(r)
k=pd.DataFrame(keep); k.to_csv(f'data/interim/lost_works_raw/tankpick_{n}.csv',index=False); print(len(k)); print(k.diam_m.describe().round(1).to_dict())
