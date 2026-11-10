"""Crop of a USGS sheet by a WGS84 box -> PNG (for looking at how a sheet draws piers).
usage: view.py <sheet.tif> lon0,lat0,lon1,lat1 out.png [max_px]"""
import sys
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
from PIL import Image

RAW = "/home/user/nyc/data/raw/piers/usgs/"


def crop(fn, box, max_px=1500):
    with rasterio.open(fn if "/" in fn else RAW + fn) as s:
        b = transform_bounds("EPSG:4326", s.crs, *box)
        w = from_bounds(*b, transform=s.transform).round_offsets().round_lengths()
        sc = max(1.0, max(w.width, w.height) / max_px)
        a = s.read(window=w, out_shape=(s.count, int(w.height / sc), int(w.width / sc)), boundless=True, fill_value=255)
        if s.count == 1 and s.colormap(1):
            cm = np.array([s.colormap(1).get(i, (0, 0, 0, 255))[:3] for i in range(256)], "uint8")
            a = np.moveaxis(cm[a[0]], -1, 0)
        return a, s.res, s.crs


if __name__ == "__main__":
    fn, box, out = sys.argv[1], [float(v) for v in sys.argv[2].split(",")], sys.argv[3]
    a, res, crs = crop(fn, box, int(sys.argv[4]) if len(sys.argv) > 4 else 1500)
    print(a.shape, res, crs.to_string()[:60])
    Image.fromarray(np.moveaxis(a[:3], 0, -1)).save(out)
