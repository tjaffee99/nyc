"""QA: draw today's street centrelines (red) on a pixel window of the Viele scan, with the stored georeference
(or the two-point start transform with 'start').  usage: python viele_overlay.py x0 y0 x1 y1 out.png [scale] [start]
"""
import json
import sys

import duckdb
import geopandas as gpd
import numpy as np
from PIL import Image, ImageDraw
from pyproj import Transformer
from scipy import optimize
from shapely import wkb

sys.path.insert(0, "/home/user/nyc/data/manual/natural/tools")
import viele_georef as vg

Image.MAX_IMAGE_PIXELS = None
x0, y0, x1, y1 = map(int, sys.argv[1:5])
out = sys.argv[5]
scale = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
start = len(sys.argv) > 7
tf = Transformer.from_crs(4326, 32618, always_xy=True)
if start:
    (p1, g1), (p2, g2) = vg.GCP
    e1, n1 = tf.transform(*g1)
    e2, n2 = tf.transform(*g2)
    s = complex(e2 - e1, n2 - n1) / complex(p2[0] - p1[0], -(p2[1] - p1[1]))
    a, b = s.real, s.imag
    fwd = lambda x, y: (e1 + a * (x - p1[0]) + b * (y - p1[1]), n1 + b * (x - p1[0]) - a * (y - p1[1]))
else:
    G = json.load(open(vg.OUT))
    def fwd(x, y):
        x, y = np.atleast_1d(np.asarray(x, float)), np.atleast_1d(np.asarray(y, float))
        e = np.empty_like(x); n = np.empty_like(x)
        for name, m in (("left", x < G["seam"]), ("right", x >= G["seam"])):
            if m.any():
                e[m], n[m] = vg.apply(G["halves"][name]["coef"], x[m], y[m])
        return e, n
# corners -> lon/lat box
cx, cy = np.array([x0, x1, x0, x1], float), np.array([y0, y0, y1, y1], float)
ce, cn = fwd(cx, cy)
inv = Transformer.from_crs(32618, 4326, always_xy=True)
lo, la = inv.transform(ce, cn)
con = duckdb.connect(); con.execute("INSTALL spatial; LOAD spatial;")
geoms = []
for f in ("roads_local", "roads_region"):
    rows = con.execute(f"SELECT ST_AsWKB(geometry) FROM '{vg.OV}/{f}.parquet' WHERE ST_XMax(geometry)>{min(lo)} AND ST_XMin(geometry)<{max(lo)} AND ST_YMax(geometry)>{min(la)} AND ST_YMin(geometry)<{max(la)}").fetchall()
    geoms += [wkb.loads(bytes(r[0])) for r in rows]
gs = gpd.GeoSeries(geoms, crs=4326).to_crs(32618)
# local affine inverse fitted on a grid of the window
gx, gy = np.meshgrid(np.linspace(x0, x1, 8), np.linspace(y0, y1, 8))
ge, gn = fwd(gx.ravel(), gy.ravel())
A = np.c_[ge, gn, np.ones(len(ge))]
cxi = np.linalg.lstsq(A, gx.ravel(), rcond=None)[0]
cyi = np.linalg.lstsq(A, gy.ravel(), rcond=None)[0]
im = Image.open(vg.SRC).crop((x0, y0, x1, y1))
im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
d = ImageDraw.Draw(im)
for l in gs:
    for part in getattr(l, "geoms", [l]):
        c = np.asarray(part.coords)
        px = (c[:, 0] * cxi[0] + c[:, 1] * cxi[1] + cxi[2] - x0) * scale
        py = (c[:, 0] * cyi[0] + c[:, 1] * cyi[1] + cyi[2] - y0) * scale
        d.line(list(zip(px, py)), fill=(255, 0, 0), width=1)
im.save(out)
print(out, im.size)
