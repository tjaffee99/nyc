S='/tmp/claude-0/-home-user-nyc/f18fa0a8-84a0-5e93-b4be-330efeee9c33/scratchpad'
import re, json, numpy as np, geopandas as gpd, pandas as pd
w=gpd.read_parquet('/home/user/nyc/data/interim/navy_yard/win.parquet'); w=w[w.end_year==9999].copy()
w['name']=w.name.astype('string'); wm=w.to_crs(32618); w['x']=wm.centroid.x; w['y']=wm.centroid.y
byb={int(r.bin):(r.x,r.y) for _,r in w.iterrows() if pd.notna(r.bin)}
ctl={'A':byb[3057917],'R1':byb[3348106],'R95':byb[3395470],'92':None}
for n in ['10','11','12','20','22','92','74','16','28','120','121','127','131']:
    s=w[w.name==n]
    if len(s)==1: ctl[n]=(s.x.iloc[0],s.y.iloc[0])
ctl={k:v for k,v in ctl.items() if v}
t=open(f'{S}/bb155.html').read()
ws=re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>',t)
L={}
for x in ws:
    if x[4] in ctl: L.setdefault(x[4],[]).append(((float(x[0])+float(x[2]))/2,(float(x[1])+float(x[3]))/2))
keep=[(n,v[0]) for n,v in L.items() if len(v)==1]
print([k[0] for k in keep])
for it in range(5):
    A=np.array([[x,y,1] for n,(x,y) in keep]); E=np.array([ctl[n][0] for n,_ in keep]); N=np.array([ctl[n][1] for n,_ in keep])
    cx=np.linalg.lstsq(A,E,rcond=None)[0]; cy=np.linalg.lstsq(A,N,rcond=None)[0]
    res=np.hypot(A@cx-E,A@cy-N); print(len(keep),'rms',round(float(np.sqrt((res**2).mean())),1),[(k[0],round(float(r))) for k,r in zip(keep,res)])
    if res.max()<14 or len(keep)<7: break
    keep=[k for k,r in zip(keep,res) if r<res.max()]
r=json.load(open(f'{S}/reg.json')); r['155']=dict(cx=cx.tolist(),cy=cy.tolist(),n=len(keep),rms=float(np.sqrt((res**2).mean())),used=[k[0] for k in keep]); json.dump(r,open(f'{S}/reg.json','w'))
