"""Export a lon/lat window of a GeoTIFF to PNG (for eyeballing a sheet).
usage: python crop.py <tif> <lon0> <lat0> <lon1> <lat1> <out.png> [scale]
"""
import sys

import numpy as np
import rasterio
from rasterio.warp import transform
from rasterio.windows import from_bounds
from PIL import Image

tif, lon0, lat0, lon1, lat1, out = sys.argv[1], *map(float, sys.argv[2:6]), sys.argv[6]
scale = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
with rasterio.open(tif) as s:
    xs, ys = transform("EPSG:4326", s.crs, [lon0, lon1, lon0, lon1], [lat0, lat0, lat1, lat1])
    w = from_bounds(min(xs), min(ys), max(xs), max(ys), s.transform)
    a = s.read(window=w, boundless=True, fill_value=255)
    if a.shape[0] == 1 and s.colormap(1):
        cm = s.colormap(1)
        lut = np.array([cm.get(i, (0, 0, 0, 255))[:3] for i in range(256)], dtype=np.uint8)
        a = lut[a[0]].transpose(2, 0, 1)
im = Image.fromarray(np.moveaxis(a[:3], 0, 2))
if scale != 1.0:
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
im.save(out)
print(out, im.size)
