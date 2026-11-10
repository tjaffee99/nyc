"""Crop a USGS historical topographic GeoTIFF (HTMC, public domain) to a lon / lat box,
warped to UTM 18N (EPSG:32618, NAD27 -> WGS84 by PROJ), and save a PNG with a UTM grid so
points can be read off in metres.
usage: topo_crop.py sheet.tif lon0 lat0 lon1 lat1 out.png [grid_m=200] [m_per_px=2] [overlay.geojson]"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.warp import Resampling, reproject
from rasterio.transform import from_origin

UTM = "EPSG:32618"


def crop(tif, lon0, lat0, lon1, lat1, res=2.0):
    T = Transformer.from_crs(4326, UTM, always_xy=True)
    xs, ys = T.transform([lon0, lon1, lon0, lon1], [lat0, lat0, lat1, lat1])
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = int((x1 - x0) / res), int((y1 - y0) / res)
    dst = np.zeros((3, h, w), np.uint8)
    tr = from_origin(x0, y1, res, res)
    with rasterio.open(tif) as ds:
        for b in range(3):
            reproject(rasterio.band(ds, min(b + 1, ds.count)), dst[b], dst_transform=tr, dst_crs=UTM, resampling=Resampling.bilinear)
    return dst.transpose(1, 2, 0), (x0, x1, y0, y1)


if __name__ == "__main__":
    tif, out = sys.argv[1], sys.argv[6]
    lon0, lat0, lon1, lat1 = map(float, sys.argv[2:6])
    grid = float(sys.argv[7]) if len(sys.argv) > 7 else 200.0
    res = float(sys.argv[8]) if len(sys.argv) > 8 else 2.0
    img, (x0, x1, y0, y1) = crop(tif, lon0, lat0, lon1, lat1, res)
    fig = plt.figure(figsize=(img.shape[1] / 100 + 1.2, img.shape[0] / 100 + 0.8), dpi=100)
    ax = fig.add_axes([0.07, 0.05, 0.92, 0.93])
    ax.imshow(img, extent=(x0, x1, y0, y1), interpolation="nearest")
    gx = np.arange(np.ceil(x0 / grid) * grid, x1, grid)
    gy = np.arange(np.ceil(y0 / grid) * grid, y1, grid)
    ax.set_xticks(gx); ax.set_yticks(gy)
    ax.set_xticklabels([f"{int(v) % 100000}" for v in gx], fontsize=7, rotation=90)
    ax.set_yticklabels([f"{int(v) % 100000}" for v in gy], fontsize=7)
    ax.grid(True, color="magenta", lw=0.4, alpha=0.6)
    if len(sys.argv) > 9:
        import geopandas as gpd
        g = gpd.read_file(sys.argv[9]).to_crs(UTM)
        g.boundary.plot(ax=ax, color="cyan", lw=1.0)
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    fig.savefig(out)
    print(out, img.shape, f"x {x0:.0f}-{x1:.0f} y {y0:.0f}-{y1:.0f} (tick labels = last 5 digits)")
