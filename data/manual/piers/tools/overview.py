"""All piers of piers.geojson as dots on today's land / water (one picture of the whole city, 25 m a pixel) - to see at a
glance where the outlines are (standing blue, vanished magenta).   usage: overview.py out.png [lon0,lat0,lon1,lat1]"""
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image, ImageDraw
from rasterio import features

sys.path.insert(0, str(Path(__file__).parent))
import extract as E
from chart import GeoWM, WM

box = [float(v) for v in sys.argv[2].split(",")] if len(sys.argv) > 2 else [-74.27, 40.49, -73.69, 40.92]
px = float(sys.argv[3]) if len(sys.argv) > 3 else 33.0
X0, Y0 = WM.transform(box[0], box[1])
X1, Y1 = WM.transform(box[2], box[3])
w, h = int((X1 - X0) / px), int((Y1 - Y0) / px)
tr = rasterio.Affine(px, 0, X0, 0, -px, Y1)
water = features.rasterize([(p, 1) for p in E.today_water(GeoWM(), box)], out_shape=(h, w), transform=tr, fill=0, dtype="uint8")
im = Image.fromarray(np.where(water[..., None] == 1, np.array([205, 225, 240], "uint8"), np.array([245, 243, 235], "uint8")).astype("uint8"))
dr = ImageDraw.Draw(im)
for f in json.load(open(Path(__file__).resolve().parents[1] / "piers.geojson"))["features"]:
    g = f["geometry"]
    rings = [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
    col = (0, 80, 255) if f["properties"]["end_year"] == 9999 else (220, 0, 180)
    for ring in rings:
        c = np.array(ring)
        X, Y = WM.transform(c[:, 0], c[:, 1])
        pts = [(~tr) * (a, b) for a, b in zip(X, Y)]
        if px > 12:
            cx, cy = np.mean([p[0] for p in pts]), np.mean([p[1] for p in pts])
            dr.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=col)
        else:
            dr.polygon(pts, outline=col)
im.save(sys.argv[1])
print(sys.argv[1], im.size)
