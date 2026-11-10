"""QA: window of the 1890s USGS class mosaic (land cream, water blue, marsh green, thin blue lines red) with today's
shoreline (soil survey Water unit) in black.  usage: qa_city.py lon0 lat0 lon1 lat1 out.png [scale]"""
import sys

import geopandas as gpd
import numpy as np
import rasterio
from PIL import Image
from pyproj import Transformer
from rasterio import features
from rasterio.windows import from_bounds
from scipy import ndimage

D = "/home/user/nyc/data/interim/natural"
lon0, lat0, lon1, lat1 = map(float, sys.argv[1:5])
out = sys.argv[5]
scale = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
tf = Transformer.from_crs(4326, 32618, always_xy=True)
x0, y0 = tf.transform(lon0, lat0); x1, y1 = tf.transform(lon1, lat1)
with rasterio.open(f"{D}/usgs_1890s.tif") as s:
    w = from_bounds(x0, y0, x1, y1, s.transform).round_offsets().round_lengths()
    a = s.read(1, window=w); tr = s.window_transform(w)
pal = np.array([[250, 240, 215], [110, 160, 240], [90, 190, 120], [255, 0, 0]] + [[255, 255, 255]] * 252, "uint8")
img = pal[a]
soil = gpd.read_parquet(f"{D}/ssurgo_all.parquet").cx[x0:x1, y0:y1]
wt = features.rasterize(((g, 1) for g in soil[soil.MUSYM == "W"].geometry), out_shape=a.shape, transform=tr, fill=0, dtype="uint8").astype(bool)
edge = wt ^ ndimage.binary_erosion(wt)
img[edge] = (0, 0, 0)
im = Image.fromarray(img)
im = im.resize((int(im.width * scale), int(im.height * scale)), Image.NEAREST)
im.save(out); print(out, im.size)
