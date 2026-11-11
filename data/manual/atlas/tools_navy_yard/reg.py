import re, numpy as np, geopandas as gpd, pandas as pd, json
S='/tmp/claude-0/-home-user-nyc/f18fa0a8-84a0-5e93-b4be-330efeee9c33/scratchpad'
w=gpd.read_parquet('/home/user/nyc/data/interim/navy_yard/win.parquet')
w=w[w.end_year==9999].copy()
w['name']=w.name.astype('string')
c=w.geometry.to_crs(32618).centroid
w['x']=c.x; w['y']=c.y
bn={}
for _,r in w.iterrows():
    if pd.notna(r['name']): bn.setdefault(r['name'],[]).append((r.x,r.y,r.geometry.area))
byb={int(r.bin):(r.x,r.y) for _,r in w.iterrows() if pd.notna(r.bin)}
ctl={'A':byb[3057917],'R1':byb[3348106],'R95':byb[3395470]}
for k,v in bn.items():
    if len(v)==1: ctl[k]=(v[0][0],v[0][1])
print(sorted(ctl))
def labels(p):
    t=open(f'{S}/bb{p}.html').read()
    ws=re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>',t)
    return [(x[4],(float(x[0])+float(x[2]))/2,(float(x[1])+float(x[3]))/2) for x in ws]
out={}
for p in (156,157,158):
    L=[l for l in labels(p) if l[0] in ctl and not (l[0]=='I')]
    # drop legend area / duplicates
    seen={}
    for n,x,y in L: seen.setdefault(n,[]).append((x,y))
    pts=[(n,v[0]) for n,v in seen.items() if len(v)==1]
    keep=list(pts)
    for it in range(4):
        A=np.array([[x,y,1] for n,(x,y) in keep]); E=np.array([ctl[n][0] for n,_ in keep]); N=np.array([ctl[n][1] for n,_ in keep])
        cx=np.linalg.lstsq(A,E,rcond=None)[0]; cy=np.linalg.lstsq(A,N,rcond=None)[0]
        res=np.hypot(A@cx-E,A@cy-N)
        print(p,it,len(keep),'rms',round(float(np.sqrt((res**2).mean())),1),'max',round(float(res.max()),1),[ (k[0],round(float(r))) for k,r in zip(keep,res) if r>12])
        if res.max()<12 or len(keep)<8: break
        keep=[k for k,r in zip(keep,res) if r<=max(12,np.sort(res)[-2]-0.1)] if False else [k for k,r in zip(keep,res) if r<res.max()]
    out[p]=dict(cx=cx.tolist(),cy=cy.tolist(),n=len(keep),rms=float(np.sqrt((res**2).mean())),used=[k[0] for k in keep])
    print(p,'scale m/pt',np.hypot(cx[0],cy[0]),np.hypot(cx[1],cy[1]),'rot',np.degrees(np.arctan2(cy[0],cx[0])))
json.dump(out,open(f'{S}/reg.json','w'))
