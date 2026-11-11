S='/tmp/claude-0/-home-user-nyc/f18fa0a8-84a0-5e93-b4be-330efeee9c33/scratchpad'
import numpy as np, subprocess, json
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from shapely.geometry import MultiPoint
subprocess.run(['pdftoppm','-f','156','-l','156','-r','200','-gray','-png','/home/user/nyc/data/raw/navy_yard/nrhp_14000261.pdf',S+'/p156'],check=True)
im=Image.open(S+'/p156-156.png').convert('L'); k=200/72
x0,y0,x1,y1=[int(v*k) for v in (40,300,340,560)]
c=np.array(im.crop((x0,y0,x1,y1))).astype(float)
b=ndi.gaussian_filter(c,2.0); bg=ndi.gaussian_filter(c,25)
m=(bg-b)>14
m=ndi.binary_opening(m,np.ones((5,5))); m=ndi.binary_closing(m,np.ones((7,7)))
lab,n=ndi.label(m)
vis=Image.fromarray(c.astype(np.uint8)).convert('RGB'); dr=ImageDraw.Draw(vis); out=[]
for i in range(1,n+1):
    ys,xs=np.nonzero(lab==i); a=len(xs)
    if a<600 or a>40000: continue
    mp=MultiPoint(np.c_[xs,ys]).convex_hull
    r=mp.minimum_rotated_rectangle
    if mp.area/r.area<0.8: continue
    pts=list(r.exterior.coords); out.append(pts); dr.line(pts,fill=(255,0,0),width=2)
print(n,len(out)); vis.save(S+'/seg156.png')
json.dump(dict(origin=[40,300],k=k,boxes=out),open(S+'/seg156.json','w'))
