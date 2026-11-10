"""USGS Historical Topographic Map Collection (public domain) for the sites: which editions
cover a point, and a sheet resampled into a local metre frame.

  python -I topo.py list LON LAT                 # editions covering the point
  python -I topo.py render LON LAT HALF_M RES OUT.png [--year 1947] [--grid 100]

The edition list is the TNM Access API listing cached by the natural-layer tools
(data/raw/natural/usgs/tnm_all.json; re-queried into data/raw/sites/usgs/ if missing).
The "map year" of an edition is its photo-revision / aerial-photo / survey year from the
sheet's FGDC metadata (cached in data/raw/sites/usgs/meta/), else the year in its title.
Sheets are read through /vsicurl/ (only the window needed) and cached as crops.
NAD27 -> WGS84 by PROJ's three-parameter shift (no grid files on this machine: +-10 m).
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RAW = ROOT / "data" / "raw" / "sites" / "usgs"
(RAW / "meta").mkdir(parents=True, exist_ok=True)
(RAW / "crops").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("CURL_CA_BUNDLE", "/root/.ccr/ca-bundle.crt")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "4")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("GDAL_HTTP_USERAGENT", "NYCThroughTime-research/0.1")
os.environ.setdefault("VSI_CACHE", "TRUE")
UA = "NYCThroughTime-research/0.1"
SCALES = (24000, 25000, 31680, 62500)


def curl(url, timeout=60):
    return subprocess.run(["curl", "-sS", "-L", "-m", str(timeout), "-A", UA, url], capture_output=True, check=True).stdout


def kfac(cy):
    return 111320 * math.cos(math.radians(cy))


def ll2loc(lon, lat, cx, cy):
    return (np.asarray(lon) - cx) * kfac(cy), (np.asarray(lat) - cy) * 110574


def loc2ll(x, y, cx, cy):
    return cx + np.asarray(x) / kfac(cy), cy + np.asarray(y) / 110574


_ITEMS = None


def items():
    global _ITEMS
    if _ITEMS is None:
        f = ROOT / "data" / "raw" / "natural" / "usgs" / "tnm_all.json"
        g = RAW / "tnm_all.json"
        if f.exists():
            _ITEMS = json.loads(f.read_text())
        elif g.exists():
            _ITEMS = json.loads(g.read_text())
        else:
            out, off = [], 0
            while True:
                u = ("https://tnmaccess.nationalmap.gov/api/v1/products?datasets=Historical%20Topographic%20Maps"
                     f"&bbox=-74.29,40.47,-73.67,40.94&outputFormat=JSON&max=100&offset={off}")
                d = json.loads(curl(u, 120))
                out += d["items"]
                off += 100
                if off >= d["total"]:
                    break
            g.write_text(json.dumps(out))
            _ITEMS = out
    return _ITEMS


def meta_years(it):
    """Imprint / aerial photo / field check / photo revision / survey years of a sheet."""
    key = RAW / "meta" / it["vendorMetaUrl"].split("/")[-1]
    if not key.exists():
        try:
            key.write_bytes(curl(it["vendorMetaUrl"], 40))
        except Exception:  # noqa: BLE001
            return {}
    x = key.read_text(errors="ignore")
    yrs = {}
    for desc, date in re.findall(r"<procdesc>([^<]*Year[^<]*)</procdesc>\s*<procdate>(\d{4})", x):
        yrs[desc.replace(" Year", "").strip()] = int(date)
    return yrs


def map_year(title_year, yrs):
    for k in ("Photo Revision", "Aerial Photo", "Field Check", "Survey", "Edit"):
        if k in yrs:
            if k == "Photo Revision" and "Aerial Photo" in yrs and yrs["Aerial Photo"] >= yrs[k] - 2:
                return yrs["Aerial Photo"], "Aerial Photo"
            return yrs[k], k
    return title_year, "title"


def editions(lon, lat):
    """[(scale, quad, map_year, kind, imprint, url, years)] covering the point, oldest first.
    Reprints of one survey are kept only once (the earliest imprint), except that a
    photorevision is its own edition."""
    out = {}
    for it in items():
        m = re.search(r"1:(\d+)-scale Quadrangle for (.*) (\d{4})$", it["title"])
        if not m or int(m.group(1)) not in SCALES or not it["urls"].get("GeoTIFF"):
            continue
        b = it["boundingBox"]
        if not (b["minX"] <= lon <= b["maxX"] and b["minY"] <= lat <= b["maxY"]):
            continue
        yrs = meta_years(it)
        y, kind = map_year(int(m.group(3)), yrs)
        sc = int(m.group(1))
        key = (sc, m.group(2), y, yrs.get("Photo Revision")) if sc <= 31680 else (sc, it["urls"]["GeoTIFF"])
        imp = yrs.get("Imprint")
        if key not in out or (imp or 9999) < (out[key][4] or 9999):
            out[key] = (sc, m.group(2), y, kind, imp, it["urls"]["GeoTIFF"], yrs)
    return sorted(out.values(), key=lambda t: (t[2], t[0]))


_TF = {}


def _tf(crs_wkt):
    import pyproj
    import warnings
    if crs_wkt not in _TF:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _TF[crs_wkt] = pyproj.Transformer.from_crs("EPSG:4326", pyproj.CRS.from_wkt(crs_wkt), always_xy=True)
    return _TF[crs_wkt]


def render(url, cx, cy, half, res=2.0, shift=(0.0, 0.0)):
    """Sheet resampled into the local frame centred on (cx, cy): RGB uint8 (n x n), None if
    the point is off the sheet. shift = metres added to the map's positions."""
    import rasterio
    from rasterio.windows import Window
    from scipy.ndimage import map_coordinates
    key = RAW / "crops" / (url.split("/")[-1].replace("%20", "_")[:-4] + f"_{cx:.5f}_{cy:.5f}_{int(half)}_{res}.npy")
    if key.exists() and shift == (0.0, 0.0):
        return np.load(key)
    n = int(round(2 * half / res))
    xs = -half + (np.arange(n) + 0.5) * res - shift[0]
    ys = half - (np.arange(n) + 0.5) * res - shift[1]
    X, Y = np.meshgrid(xs, ys)
    lon, lat = loc2ll(X, Y, cx, cy)
    with rasterio.open("/vsicurl/" + url) as r:
        px, py = _tf(r.crs.to_wkt()).transform(lon.ravel(), lat.ravel())
        col, row = ~r.transform * (np.asarray(px), np.asarray(py))
        col = col.reshape(X.shape)
        row = row.reshape(X.shape)
        c0, c1 = int(max(0, np.floor(col.min()) - 2)), int(min(r.width, np.ceil(col.max()) + 2))
        r0, r1 = int(max(0, np.floor(row.min()) - 2)), int(min(r.height, np.ceil(row.max()) + 2))
        if c1 <= c0 or r1 <= r0:
            return None
        arr = r.read(window=Window(c0, r0, c1 - c0, r1 - r0))
        if r.count == 1:
            try:
                cm = r.colormap(1)
                lut = np.array([cm.get(i, (0, 0, 0, 0))[:3] for i in range(256)], np.uint8)
                arr = np.moveaxis(lut[arr[0]], -1, 0)
            except ValueError:
                arr = np.repeat(arr, 3, 0)
    out = np.full((n, n, 3), 255, np.uint8)
    for b in range(3):
        out[:, :, b] = map_coordinates(arr[b], [row - r0, col - c0], order=1, mode="constant", cval=255)
    if shift == (0.0, 0.0):
        np.save(key, out)
    return out


def annotate(img, half, res, grid=100, polys=()):
    from PIL import Image, ImageDraw
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)

    def P(x, y):
        return ((x + half) / res, (half - y) / res)
    if grid:
        k = int(half // grid)
        for i in range(-k, k + 1):
            v = i * grid
            c = (0, 160, 255) if i else (0, 255, 255)
            d.line([P(v, -half), P(v, half)], fill=c, width=1)
            d.line([P(-half, v), P(half, v)], fill=c, width=1)
            if i % 2 == 0:
                d.text((P(v, half)[0] + 2, 2), str(int(v)), fill=(0, 0, 200))
                d.text((2, P(0, v)[1] + 2), str(int(v)), fill=(0, 0, 200))
    for x, y in polys:
        d.line([P(a, b) for a, b in zip(x, y)], fill=(255, 0, 0), width=2)
    return im


if __name__ == "__main__":
    a = sys.argv[1:]
    lon, lat = float(a[1]), float(a[2])
    if a[0] == "list":
        for sc, name, y, kind, imp, url, yrs in editions(lon, lat):
            print(f"{y} {kind[:8]:8s} 1:{sc:<6d} {name:22s} imprint {imp}  {url.split('/')[-1]}  {yrs}")
    elif a[0] == "render":
        half, res, out = float(a[3]), float(a[4]), a[5]
        want = int(a[a.index("--year") + 1]) if "--year" in a else None
        grid = int(a[a.index("--grid") + 1]) if "--grid" in a else 100
        eds = editions(lon, lat)
        ed = min(eds, key=lambda e: abs(e[2] - want)) if want else eds[-1]
        img = render(ed[5], lon, lat, half, res)
        annotate(img, half, res, grid).save(out)
        print(out, ed[:5], img.shape)
