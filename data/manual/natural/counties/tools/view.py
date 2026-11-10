"""Checking picture: crops of USGS sheets with today's shoreline (edge of the soil survey's Water unit) drawn on
top, unshifted (red) and under candidate shifts (other colours).  usage: python view.py out.png sid,lon,lat,half_m[,dxE,dyN;dxE,dyN...] ..."""
import sys
import geopandas as gpd, numpy as np, rasterio
from PIL import Image, ImageDraw
from pyproj import Transformer
from rasterio.windows import Window
from shapely.geometry import box
from common import D, RAW, SHEETS

COL = [(255, 0, 0), (0, 160, 0), (255, 0, 255), (255, 140, 0)]

def panel(spec, soil):
    p = spec.split(",")
    sid, lon, lat, half = p[0], float(p[1]), float(p[2]), float(p[3])
    shifts = [(0.0, 0.0)] + [tuple(float(v) for v in s.split("/")) for s in (p[4].split(";") if len(p) > 4 else [])]
    stem = [k for k, v in SHEETS.items() if v[4] == sid][0]
    with rasterio.open(f"{RAW}/usgs/{stem}_62500_geo.tif") as s:
        x, y = Transformer.from_crs(4326, s.crs.to_wkt(), always_xy=True).transform(lon, lat)
        c, r = ~s.transform * (x, y)
        n = int(half / s.transform.a)
        win = Window(int(c) - n, int(r) - n, 2 * n, 2 * n)
        rgb = s.read([1, 2, 3], window=win, boundless=True, fill_value=255)
        wt = s.window_transform(win); crs = s.crs
    im = Image.fromarray(np.moveaxis(rgb, 0, -1)).resize((760, 760), Image.LANCZOS)
    sc = 760 / (2 * n)
    dr = ImageDraw.Draw(im)
    bx = box(x - half, y - half, x + half, y + half)
    w = soil[soil.code == 1].to_crs(crs.to_wkt())
    w = w[w.intersects(bx)]
    if len(w):
        edge = w.geometry.union_all().boundary.intersection(bx)
        geoms = list(edge.geoms) if hasattr(edge, "geoms") else [edge]
        for k, (de, dn) in enumerate(shifts):   # (de, dn): metres the SHEET must move east / north = today's line drawn at -(de, dn)
            for g in geoms:
                if g.geom_type != "LineString":
                    continue
                pts = [((px - de - wt.c) / wt.a * sc, (py - dn - wt.f) / wt.e * sc) for px, py in g.coords]
                dr.line(pts, fill=COL[k % 4], width=1)
    dr.text((6, 6), f"{sid} {lon},{lat} +-{half:.0f} m  shifts(E,N): " + " ".join(f"{COL[k % 4]}={s}" for k, s in enumerate(shifts)), fill=(0, 0, 0))
    return im

soil = gpd.read_parquet(f"{D}/ssurgo_counties.parquet", columns=["code", "geometry"])
ims = [panel(s, soil) for s in sys.argv[2:]]
W = Image.new("RGB", (760 * len(ims), 760), (255, 255, 255))
for i, im in enumerate(ims):
    W.paste(im, (760 * i, 0))
W.save(sys.argv[1])
