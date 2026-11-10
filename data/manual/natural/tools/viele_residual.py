"""Residual of the Viele georeference, measured street by street.

For a set of long straight streets, today's centreline (Overture) is put into the scan with the stored transform and
the scan's straight-line mask is averaged along the street into a cross profile.  Viele draws the two kerbs, so the
profile is symmetric about the true centre of the street; the offset of that axis of symmetry from zero is the
residual across that street.  Avenues give the residual across the island, cross streets the residual along it.
"""
import json

import duckdb
import geopandas as gpd
import numpy as np
from shapely import wkb
from shapely.ops import linemerge

import viele_georef as vg

D = "/home/user/nyc/data/interim/natural"
G = json.load(open(vg.OUT))
lines = np.load(f"{D}/viele_lines.npy")
H, W = lines.shape
MPP = 2.05
AVES = ["1st Avenue", "2nd Avenue", "3rd Avenue", "Lexington Avenue", "Madison Avenue", "5th Avenue", "6th Avenue", "7th Avenue", "8th Avenue",
        "9th Avenue", "10th Avenue", "Amsterdam Avenue", "Columbus Avenue", "Avenue A", "Avenue B", "Hudson Street", "Bowery"]
STS = [f"{s} {n} Street" for n in ("14th", "23rd", "34th", "42nd", "57th", "72nd", "79th", "86th", "96th", "106th", "116th", "125th", "135th", "145th") for s in ("East", "West")] + \
      ["Houston Street", "East Houston Street", "Canal Street", "Chambers Street", "Grand Street", "Delancey Street", "Wall Street", "Fulton Street"]

gx, gy = np.meshgrid(np.linspace(250, 9600, 60), np.linspace(150, 2900, 30))
inv = {}
for name, m in (("left", gx.ravel() < G["seam"]), ("right", gx.ravel() >= G["seam"])):
    e, n = vg.apply(G["halves"][name]["coef"], gx.ravel()[m], gy.ravel()[m])
    E, N = (e - 585000) / 10000, (n - 4510000) / 10000
    A = np.c_[np.ones_like(E), E, N, E * E, E * N, N * N]
    inv[name] = (np.linalg.lstsq(A, gx.ravel()[m], rcond=None)[0], np.linalg.lstsq(A, gy.ravel()[m], rcond=None)[0])


def to_px(e, n):
    E, N = (e - 585000) / 10000, (n - 4510000) / 10000
    A = np.c_[np.ones_like(E), E, N, E * E, E * N, N * N]
    xl, yl = A @ inv["left"][0], A @ inv["left"][1]
    xr, yr = A @ inv["right"][0], A @ inv["right"][1]
    left = xl < G["seam"]
    return np.where(left, xl, xr), np.where(left, yl, yr)


con = duckdb.connect(); con.execute("INSTALL spatial; LOAD spatial;")
T = np.arange(-20, 20.01, 0.5)
res = {}
for kind, names in (("avenue", AVES), ("street", STS)):
    for nm in names:
        rows = []
        for f in ("roads_local", "roads_region"):
            rows += con.execute(f"SELECT ST_AsWKB(geometry) FROM '{vg.OV}/{f}.parquet' WHERE name='{nm}' AND ST_XMin(geometry)>-74.02 AND ST_XMax(geometry)<-73.925 AND ST_YMin(geometry)>40.703 AND ST_YMax(geometry)<40.835").fetchall()
        if not rows:
            continue
        gs = gpd.GeoSeries([wkb.loads(bytes(r[0])) for r in rows], crs=4326).to_crs(32618)
        prof = np.zeros(len(T)); cnt = 0
        for l in gs:
            for part in getattr(l, "geoms", [l]):
                if part.length < 40:
                    continue
                d = np.arange(0, part.length, 6.0)
                p = np.array([part.interpolate(v).coords[0] for v in d])
                x, y = to_px(p[:, 0], p[:, 1])
                tx, ty = np.gradient(x), np.gradient(y)
                nrm = np.hypot(tx, ty) + 1e-9
                nx, ny = -ty / nrm, tx / nrm
                for i, t in enumerate(T):
                    xi, yi = np.round(x + t * nx).astype(int), np.round(y + t * ny).astype(int)
                    ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
                    prof[i] += lines[yi[ok], xi[ok]].sum()
                cnt += len(d)
        if cnt < 150 or prof.max() < 0.15 * cnt:
            continue
        best = (-1, 0)
        for ci in range(len(T)):
            c = T[ci]
            if abs(c) > 12:
                continue
            k = 16                         # +-8 px (16 m) either side of the trial axis, the same for every trial
            a_, b_ = prof[ci - k:ci][::-1], prof[ci + 1:ci + 1 + k]
            s = float(((a_ - prof.mean()) * (b_ - prof.mean())).sum())
            if s > best[0]:
                best = (s, c)
        res[nm] = (kind, round(best[1] * MPP, 1), cnt)
for kind in ("avenue", "street"):
    v = np.array([r[1] for r in res.values() if r[0] == kind])
    print(kind, "n", len(v), "offsets m", sorted(v.tolist()), "| median abs", np.median(np.abs(v)), "rms", round(float(np.sqrt((v ** 2).mean())), 1))
json.dump(res, open("/home/user/nyc/data/manual/natural/viele_residuals.json", "w"), indent=1)
