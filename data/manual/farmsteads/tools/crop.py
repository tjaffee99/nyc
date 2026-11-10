"""Crop a georeferenced USGS sheet around a point for looking at it.

  python -I crop.py <sheet.tif> <lon> <lat> <half-width m> <out.png> [zoom] [--marks farmsteads.geojson|detections.json]

The crop is in the sheet's own pixels (no resampling except the integer zoom), north up as printed.
Optional marks (WGS84 points) are drawn as red circles after the sheet's shift is removed.
"""
import json
import sys

import numpy as np
import pyproj
import rasterio
from PIL import Image, ImageDraw
from rasterio.windows import Window


def crop(path, lon, lat, half_m, zoom=3, shift=(0.0, 0.0)):
    with rasterio.open(path) as src:
        tr = pyproj.Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        x, y = tr.transform(lon, lat)
        x, y = x - shift[0], y - shift[1]
        col, row = ~src.transform * (x, y)
        r = half_m / src.res[0]
        c0, r0 = int(round(col - r)), int(round(row - r))
        n = int(round(2 * r))
        arr = src.read(window=Window(c0, r0, n, n), boundless=True, fill_value=255)
        if arr.shape[0] == 1 and src.colormap(1):
            cm = src.colormap(1)
            lut = np.array([cm.get(i, (0, 0, 0, 255))[:3] for i in range(256)], np.uint8)
            arr = np.moveaxis(lut[arr[0]], -1, 0)
        img = Image.fromarray(np.moveaxis(arr[:3], 0, -1)).resize((n * zoom, n * zoom), Image.LANCZOS)
        return img, (c0, r0, src.transform, src.crs)


if __name__ == "__main__":
    a = [v for v in sys.argv[1:] if not v.startswith("--")]
    path, lon, lat, half, out = a[0], float(a[1]), float(a[2]), float(a[3]), a[4]
    zoom = int(a[5]) if len(a) > 5 else 3
    img, (c0, r0, T, crs) = crop(path, lon, lat, half, zoom)
    if "--marks" in sys.argv:
        pts = json.load(open(sys.argv[sys.argv.index("--marks") + 1]))
        tr = pyproj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        d = ImageDraw.Draw(img)
        for f in pts["features"]:
            lo, la = f["geometry"]["coordinates"][:2]
            x, y = tr.transform(lo, la)
            c, r = ~T * (x, y)
            px, py = (c - c0) * zoom, (r - r0) * zoom
            if 0 <= px < img.width and 0 <= py < img.height:
                d.ellipse([px - 9, py - 9, px + 9, py + 9], outline=(255, 0, 0), width=2)
    img.save(out)
    print(out, img.size)
