"""python -I sheet.py year out.png half_m lon,lat ... (up to 4: 2x2 contact sheet)"""
import sys, subprocess
from PIL import Image
year,out,half=sys.argv[1],sys.argv[2],sys.argv[3]
ims=[]
for i,p in enumerate(sys.argv[4:]):
    lo,la=p.split(',')
    f=f'data/interim/holes_boroughs_raw/_s{i}.png'
    subprocess.run([sys.executable,'-I','data/research/holes_boroughs_build/view.py',lo,la,half,year,f,'0.75'],check=True,capture_output=True)
    ims.append(Image.open(f))
W=max(i.width for i in ims); H=max(i.height for i in ims)
sh=Image.new('RGB',(W*2,H*((len(ims)+1)//2)))
for k,im in enumerate(ims): sh.paste(im,((k%2)*W,(k//2)*H))
sh.save(out); print(sh.size)
