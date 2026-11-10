"""QA image of the Manhattan build (1609 land grey, soil-survey upland core darker, water blue, tidal marsh green,
freshwater wetland olive, ponds dark blue, streams red).  usage: python qa_man.py out.png [x0 y0 x1 y1 in 12 m cells]"""
import sys

import geopandas as gpd
import numpy as np
import rasterio
from PIL import Image
from rasterio import features

D = "/home/user/nyc/data/interim/natural"
dbg = np.load(D + "/man_debug.npy")
with rasterio.open(D + "/viele_class.tif") as s:
    tr = s.transform
tr4 = tr * tr.scale(4, 4)
g = gpd.read_parquet(D + "/manhattan_polys.parquet")
st = gpd.read_parquet(D + "/manhattan_streams.parquet")
code = {"water": 1, "tidal_marsh": 2, "freshwater_wetland": 3, "pond": 4}
r = features.rasterize(((geom, code[c]) for geom, c in zip(g.geometry, g.cover)), out_shape=dbg.shape, transform=tr4, fill=0, dtype="uint8")
sr = features.rasterize(((geom, 1) for geom in st.geometry), out_shape=dbg.shape, transform=tr4, fill=0, dtype="uint8")
img = np.full(dbg.shape + (3,), 255, "uint8")
img[(dbg & 2) > 0] = (250, 225, 225)
img[(dbg & 1) > 0] = (235, 235, 220)
img[(dbg & 4) > 0] = (215, 215, 200)
for k, c in {1: (90, 140, 240), 2: (60, 180, 110), 3: (150, 150, 40), 4: (20, 40, 200)}.items():
    img[r == k] = c
img[sr > 0] = (255, 0, 0)
im = Image.fromarray(img)
if len(sys.argv) > 5:
    im = im.crop(tuple(map(int, sys.argv[2:6])))
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
im.save(sys.argv[1])
print(im.size)
