import sys,json
sys.path.insert(0,'data/manual/extents/tools')
import warp
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
pid,img=sys.argv[1],sys.argv[2]
out=f'data/raw/atlas/brooklyn3/{img}.tif'
t=warp.fetch(f'https://images.nypl.org/index.php?id={img}&t=u',__import__('pathlib').Path(out))
im=Image.open(t).convert('RGB'); print(im.size)
im.save(f'data/raw/atlas/brooklyn3/{img}.jpg',quality=92)
w=900/max(im.size); im.resize((int(im.size[0]*w),int(im.size[1]*w))).save(f'data/interim/atlas_brooklyn3/probe_{pid}.png')
import os; os.remove(t)
