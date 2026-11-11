S='/tmp/claude-0/-home-user-nyc/f18fa0a8-84a0-5e93-b4be-330efeee9c33/scratchpad'
import json, numpy as np, pandas as pd, geopandas as gpd
w=gpd.read_parquet('/home/user/nyc/data/interim/navy_yard/win.parquet'); w=w[w.end_year==9999].copy()
w['name']=w.name.astype('string'); wm=w.to_crs(32618); w['x']=wm.centroid.x; w['y']=wm.centroid.y; w['area']=wm.area
reg=json.load(open(f'{S}/reg.json'))['158']
import re
t=open(f'{S}/bb158.html').read()
ws=re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>',t)
lab={x[4]:((float(x[0])+float(x[2]))/2,(float(x[1])+float(x[3]))/2) for x in ws if re.fullmatch(r'R\d+|426|311|R103',x[4])}
for k,(px,py) in sorted(lab.items()):
    E=reg['cx'][0]*px+reg['cx'][1]*py+reg['cx'][2]; N=reg['cy'][0]*px+reg['cy'][1]*py+reg['cy'][2]
    d=np.hypot(w.x-E,w.y-N); i=d.nsmallest(3).index
    print(k,[(int(w.loc[j,'bin']),int(d[j]),int(w.loc[j,'area']),round(w.loc[j,'start_year']),w.loc[j,'year_src']) for j in i])
