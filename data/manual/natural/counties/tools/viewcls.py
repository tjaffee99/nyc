"""Checking picture: a crop of a USGS sheet beside its classification (white land, blue water, green marsh, red thin
blue line).  usage: python viewcls.py out.png sid,lon,lat,half_m ..."""
import sys
import numpy as np, rasterio
from PIL import Image
from pyproj import Transformer
from rasterio.windows import Window
from common import D, RAW, SHEETS

def panel(spec):
    p = spec.split(","); sid, lon, lat, half = p[0], float(p[1]), float(p[2]), float(p[3])
    stem = [k for k, v in SHEETS.items() if v[4] == sid][0]
    with rasterio.open(f"{RAW}/usgs/{stem}_62500_geo.tif") as s, rasterio.open(f"{D}/sheet_{sid}.tif") as c:
        x, y = Transformer.from_crs(4326, s.crs.to_wkt(), always_xy=True).transform(lon, lat)
        n = int(half / s.transform.a)
        col, row = ~s.transform * (x, y)
        rgb = s.read([1, 2, 3], window=Window(int(col) - n, int(row) - n, 2 * n, 2 * n), boundless=True, fill_value=255)
        col, row = ~c.transform * (x, y)
        cl = c.read(1, window=Window(int(col) - n, int(row) - n, 2 * n, 2 * n), boundless=True, fill_value=255)
    pal = np.zeros((256, 3), "uint8"); pal[0] = (255, 255, 255); pal[1] = (70, 120, 255); pal[2] = (60, 170, 60); pal[3] = (255, 90, 90); pal[255] = (120, 120, 120)
    a = Image.fromarray(np.moveaxis(rgb, 0, -1)).resize((700, 700), Image.LANCZOS)
    b = Image.fromarray(pal[cl]).resize((700, 700), Image.NEAREST)
    W = Image.new("RGB", (1400, 700)); W.paste(a, (0, 0)); W.paste(b, (700, 0))
    return W

ims = [panel(s) for s in sys.argv[2:]]
W = Image.new("RGB", (1400, 700 * len(ims)))
for i, im in enumerate(ims):
    W.paste(im, (0, 700 * i))
W.save(sys.argv[1])
