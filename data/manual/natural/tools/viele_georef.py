"""Georeference the Library of Congress scan of Egbert L. Viele's 1865 "Topographical map of the City of
New York : showing original water courses and made land" (loc.gov/item/2006629795, public domain) against
today's street centrelines (Overture roads), by chamfer matching of the map's black street lines.

The scan (IIIF pct:50 -> 9853 x 3027 px, ~2.05 m per pixel) is two sheets joined at x ~ 4937 px, so each half
gets its own second-order polynomial.  Output: data/interim/natural/viele_georef.json with the coefficients
(pixel -> UTM 18N) and the residuals measured in 600 m windows.

usage: python viele_georef.py
"""
import json

import duckdb
import geopandas as gpd
import numpy as np
from PIL import Image
from pyproj import Transformer
from rasterio import features
from rasterio.transform import from_origin
from scipy import ndimage, optimize
from shapely import wkb

Image.MAX_IMAGE_PIXELS = None
ROOT = "/home/user/nyc"
SRC = f"{ROOT}/data/raw/natural/viele/viele_1865_pct50.jpg"
OV = f"{ROOT}/data/raw/overture/2026-10-21.0"
OUT = f"{ROOT}/data/interim/natural/viele_georef.json"
SEAM = 4937
PX = 3.0  # metres per pixel of the street distance raster

# two rough control points read off the scan (pixel) -> lon/lat, only to start the search
GCP = [((2386, 1618), (-73.9905, 40.7359)),  # Union Square, centre of the oval
       ((5051, 1303), (-73.9665, 40.7814))]  # old Receiving Reservoir = today's Great Lawn, centre


def street_dt():
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    box = (-74.03, 40.695, -73.905, 40.885)
    geoms = []
    for f in ("roads_local", "roads_region"):
        rows = con.execute(
            f"SELECT ST_AsWKB(geometry) FROM '{OV}/{f}.parquet' WHERE ST_XMax(geometry)>{box[0]} AND ST_XMin(geometry)<{box[2]} "
            f"AND ST_YMax(geometry)>{box[1]} AND ST_YMin(geometry)<{box[3]}").fetchall()
        geoms += [wkb.loads(bytes(r[0])) for r in rows]
    gs = gpd.GeoSeries(geoms, crs=4326).to_crs(32618)
    x0, y0, x1, y1 = gs.total_bounds
    x0, y0, x1, y1 = x0 - 300, y0 - 300, x1 + 300, y1 + 300
    w, h = int((x1 - x0) / PX), int((y1 - y0) / PX)
    tr = from_origin(x0, y1, PX, PX)
    ras = features.rasterize(((g, 1) for g in gs), out_shape=(h, w), transform=tr, fill=0, dtype="uint8")
    dt = ndimage.distance_transform_edt(ras == 0).astype("float32") * PX
    return dt, x0, y1


def poly_terms(x, y, order):
    xs, ys = (x - 5000.0) / 5000.0, (y - 1500.0) / 5000.0
    t = [np.ones_like(xs), xs, ys]
    if order >= 2:
        t += [xs * xs, xs * ys, ys * ys]
    return np.stack(t, axis=1)


def apply(coef, x, y):
    c = np.asarray(coef).reshape(2, -1)
    order = 2 if c.shape[1] == 6 else 1
    T = poly_terms(x, y, order)
    return T @ c[0], T @ c[1]


def main():
    import os
    cache = f"{ROOT}/data/interim/natural/viele_lines.npy"
    im = np.asarray(Image.open(SRC).convert("L")).astype("float32")
    # black line work = darker than its surroundings; keep only straight runs >= 31 px (63 m) at any angle,
    # which drops hachures, lettering and stream lines and leaves the street / block lines
    ink = im < (ndimage.uniform_filter(im, 21) - 22)
    ink = ndimage.binary_dilation(ink, iterations=1)
    dark = np.zeros_like(ink)
    L = 31
    for ang in ([] if os.path.exists(cache) else np.arange(0, 180, 6.0)):
        se = np.zeros((L, L), bool)
        t = np.linspace(-(L - 1) / 2, (L - 1) / 2, 4 * L)
        cx = np.round((L - 1) / 2 + t * np.cos(np.radians(ang))).astype(int)
        cy = np.round((L - 1) / 2 - t * np.sin(np.radians(ang))).astype(int)
        se[cy, cx] = True
        dark |= ndimage.binary_opening(ink, structure=se)
    if os.path.exists(cache):
        dark = np.load(cache)
    else:
        np.save(cache, dark)
    print("line pixels", int(dark.sum()), "of ink", int(ink.sum()))
    ys, xs = np.nonzero(dark)
    keep = (ys > 150) & (ys < 2900) & (xs > 250) & (xs < 9600)
    # the inset (north end of the island) and the title block are not part of the main map
    keep &= ~((xs > 8150) & (ys > 1450)) & ~((xs < 1900) & (ys < 800)) & ~((xs > 7000) & (ys > 2100))
    xs, ys = xs[keep].astype("float64"), ys[keep].astype("float64")
    rng = np.random.default_rng(1)
    sel = rng.choice(len(xs), 400000, replace=False)
    xs, ys = xs[sel], ys[sel]
    dt, ox, oy = street_dt()
    H, W = dt.shape

    # The map draws the two kerb lines of every street, 9 m (60 ft streets) to 15 m (100 ft avenues) either
    # side of today's centreline, so the score is the share of line pixels that lie about that far from one.
    K = np.exp(-((dt - 11.0) / 5.5) ** 2).astype("float32")

    def score(coef, x, y, trunc=None):
        e, n = apply(coef, x, y)
        c = ((e - ox) / PX).astype(int)
        r = ((oy - n) / PX).astype(int)
        ok = (c >= 0) & (c < W) & (r >= 0) & (r < H)
        return -float(K[r[ok], c[ok]].sum() / len(x))

    tf = Transformer.from_crs(4326, 32618, always_xy=True)
    (p1, g1), (p2, g2) = GCP
    e1, n1 = tf.transform(*g1)
    e2, n2 = tf.transform(*g2)
    s = complex(e2 - e1, n2 - n1) / complex(p2[0] - p1[0], -(p2[1] - p1[1]))

    def sim(ds, dphi, tx, ty):
        S = s * (1 + ds) * np.exp(1j * np.radians(dphi))
        a_, b_ = S.real, S.imag
        cE = [e1 + tx + a_ * (5000 - p1[0]) + b_ * (1500 - p1[1]), a_ * 5000, b_ * 5000]
        cN = [n1 + ty + b_ * (5000 - p1[0]) - a_ * (1500 - p1[1]), b_ * 5000, -a_ * 5000]
        return np.array(cE + cN)

    sub = rng.choice(len(xs), 30000, replace=False)
    xq, yq = xs[sub], ys[sub]
    best = (0,)
    for ds in np.arange(-0.015, 0.0151, 0.0025):
        for dphi in np.arange(-0.75, 0.751, 0.125):
            e, n = apply(sim(ds, dphi, 0, 0), xq, yq)
            c0 = (e - ox) / PX
            r0 = (oy - n) / PX
            for tx in np.arange(-60, 61, 4.0):
                cc = (c0 + tx / PX).astype(int)
                okc = (cc >= 0) & (cc < W)
                for ty in np.arange(-60, 61, 4.0):
                    rr = (r0 - ty / PX).astype(int)
                    ok = okc & (rr >= 0) & (rr < H)
                    v = -float(K[rr[ok], cc[ok]].sum() / len(xq))
                    if v < best[0]:
                        best = (v, ds, dphi, tx, ty)
    print("start score", round(score(sim(0, 0, 0, 0), xs, ys), 4), "grid best", [round(float(v), 4) for v in best])
    coef = sim(*best[1:])
    sub = rng.choice(len(xs), 80000, replace=False)
    res = optimize.minimize(lambda c: score(c, xs[sub], ys[sub]), coef, method="Powell", options={"xtol": 0.01, "ftol": 1e-7, "maxiter": 60})
    coef = res.x
    print("affine score", round(res.fun, 4), "all", round(score(coef, xs, ys), 4))
    out = {"seam": SEAM, "crs": "EPSG:32618", "norm": "xs=(x-5000)/5000, ys=(y-1500)/5000; terms 1,xs,ys,xs2,xs*ys,ys2",
           "affine_all": coef.tolist(), "halves": {}}
    for name, m in (("left", xs < SEAM), ("right", xs >= SEAM)):
        c2 = np.concatenate([coef[:3], [0, 0, 0], coef[3:], [0, 0, 0]])
        xx, yy = xs[m], ys[m]
        sb = rng.choice(len(xx), min(60000, len(xx)), replace=False)
        for _ in range(2):
            res = optimize.minimize(lambda c: score(c, xx[sb], yy[sb]), c2, method="Powell",
                                    options={"xtol": 0.01, "ftol": 1e-8, "maxiter": 80})
            c2 = res.x
        print(name, "poly2 score", round(res.fun, 4), "n", int(m.sum()))
        # residuals: best local shift per 600 m window
        e, n = apply(c2, xx, yy)
        shifts = []
        for wx in np.arange(xx.min(), xx.max(), 300):
            for wy in np.arange(yy.min(), yy.max(), 300):
                w = (xx >= wx) & (xx < wx + 300) & (yy >= wy) & (yy < wy + 300)
                if w.sum() < 800:
                    continue
                vals = {}
                for dx in np.arange(-30, 31, 3.0):
                    c = ((e[w] + dx - ox) / PX).astype(int)
                    for dy in np.arange(-30, 31, 3.0):
                        r = ((oy - n[w] - dy) / PX).astype(int)
                        ok = (c >= 0) & (c < W) & (r >= 0) & (r < H)
                        vals[(dx, dy)] = float(K[r[ok], c[ok]].sum() / w.sum())
                (dx, dy), v = max(vals.items(), key=lambda kv: kv[1])
                mean = float(np.mean(list(vals.values())))
                if v > 0.45 and v > 1.25 * mean:  # a real optimum on a street pattern
                    shifts.append((float(wx), float(wy), float(dx), float(dy), v, vals[(0.0, 0.0)]))
        sh = np.array(shifts)
        mag = np.hypot(sh[:, 2], sh[:, 3]) if len(sh) else np.array([np.nan])
        print(name, "windows", len(sh), "residual median", np.median(mag), "p90", np.percentile(mag, 90), "max", mag.max())
        out["halves"][name] = {"coef": c2.tolist(), "windows": shifts,
                               "residual_median_m": float(np.median(mag)), "residual_p90_m": float(np.percentile(mag, 90))}
    json.dump(out, open(OUT, "w"))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
