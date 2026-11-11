"""Nothing stands before its ground.

The terrain turns water / marsh into land cell by cell (terrain_tiles.py: natural 1609 layer
+ dated fill zones -> data/interim/grid_<name>_landyear.npy), blending each change in over
2.5 years (viewer/src/layers/terrain.ts), and the viewer shows a building as a construction
frame for clamp(0.25 + height / 55, 0.33, 3) years before its start
(viewer/src/layers/time-extension.ts). So a building may start no earlier than

    latest land year of ANY cell its outline touches + 2.5 + its construction time.

The check uses every vertex of the outline, an inner point and (for large outlines) a 20 m
grid of inner points, each against the 2 x 2 cells around it — not one point per building:
a warehouse half on the 1810 bulkhead and half on 1850 fill waits for 1850.

The other direction is evidence (`write_evidence`, read by terrain_tiles.fill_layers): a
building with a RECORDED year, or an outline traced from a dated map, proves the ground was
there. The terrain moves a cell's land year back to such evidence (one strong piece — a
landmark record, a researched row, a traced map — or two recorded assessor years against
a dated zone; one is enough where the land year was only a fallback guess).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import shapely

from common import INTERIM, log

BLEND_YEARS = 2.5
# a cell proven land by a dated building is land this long before it: the blend, the longest
# construction time, and a year
EVIDENCE_LEAD = 6.5
EVIDENCE = INTERIM / "ground_evidence.parquet"
_grids = None


def construction_years(height_m):
    return np.clip(0.25 + np.asarray(height_m, float) / 55.0, 0.33, 3.0)


def _load():
    global _grids
    if _grids is None:
        from terrain_grid import grid_def
        _grids = []
        for name in ("detail", "region"):
            p = INTERIM / f"grid_{name}_landyear.npy"
            if p.exists():
                _grids.append((grid_def(name), np.load(p)))
    return _grids


def land_year_at(lon, lat):
    """Latest land year among the 2 x 2 cells around each point (NaN: none of them is made land).
    Detail grid where it covers the point, else the region grid."""
    lon = np.asarray(lon, float)
    lat = np.asarray(lat, float)
    X = np.radians(lon) * 6378137.0
    Y = 6378137.0 * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
    out = np.full(lon.shape, np.nan)
    done = np.zeros(lon.shape, bool)
    for gd, ly in _load():
        c = (X - gd["X0"]) / gd["res"]
        r = (gd["Y0"] - Y) / gd["res"]
        ok = ~done & (c >= 0) & (r >= 0) & (c < gd["cols"] - 1) & (r < gd["rows"] - 1)
        if not ok.any():
            continue
        c0 = np.floor(c[ok]).astype(int)
        r0 = np.floor(r[ok]).astype(int)
        v = np.fmax(np.fmax(ly[r0, c0], ly[r0, c0 + 1]), np.fmax(ly[r0 + 1, c0], ly[r0 + 1, c0 + 1]))
        out[ok] = v
        done |= ok
    return out


def sample_points(geoms):
    """(lon, lat, index of the polygon) for every vertex of each outline, an inner point,
    and — for outlines wider than ~45 m — inner points every ~20 m (60 m for very large ones)."""
    geoms = np.asarray(geoms, dtype=object)
    xy, idx = shapely.get_coordinates(shapely.get_exterior_ring(geoms), return_index=True)
    rp = shapely.point_on_surface(geoms)
    lon = [xy[:, 0], shapely.get_x(rp)]
    lat = [xy[:, 1], shapely.get_y(rp)]
    ids = [idx, np.arange(len(geoms))]
    b = shapely.bounds(geoms)
    big = np.nonzero(((b[:, 2] - b[:, 0]) * 84_400 > 45) | ((b[:, 3] - b[:, 1]) * 110_574 > 45))[0]
    for i in big:
        x = np.arange(b[i, 0], b[i, 2], 20 / 84_400)
        y = np.arange(b[i, 1], b[i, 3], 20 / 110_574)
        if len(x) * len(y) > 4000:
            x, y = x[::3], y[::3]
        gx, gy = np.meshgrid(x, y)
        inside = shapely.contains_xy(geoms[i], gx.ravel(), gy.ravel())
        if inside.any():
            lon.append(gx.ravel()[inside])
            lat.append(gy.ravel()[inside])
            ids.append(np.full(int(inside.sum()), i))
    return np.concatenate(lon), np.concatenate(lat), np.concatenate(ids)


def ground_year(geoms):
    """Per polygon (EPSG:4326): the latest land year of any cell it touches (NaN: no made land)."""
    geoms = np.asarray(geoms, dtype=object)
    out = np.full(len(geoms), np.nan)
    if not _load() or not len(geoms):
        return out
    lon, lat, ids = sample_points(geoms)
    v = land_year_at(lon, lat)
    ok = np.isfinite(v)
    np.fmax.at(out, ids[ok], v[ok])
    return out


def earliest_start(geoms, height_m):
    """Earliest allowed start per polygon (NaN: stands on natural ground)."""
    return ground_year(geoms) + BLEND_YEARS + construction_years(height_m)


def write_evidence(geoms, years, strong):
    """Evidence that ground existed: the sample points (EPSG:4326) of dated buildings.
    strong = True for landmark records, researched rows and traced maps; False for a
    recorded assessor year."""
    geoms = np.asarray(geoms, dtype=object)
    years = np.asarray(years, float)
    strong = np.asarray(strong, bool)
    ok = np.isfinite(years) & ~shapely.is_missing(geoms)
    geoms, years, strong = geoms[ok], years[ok], strong[ok]
    lon, lat, ids = sample_points(geoms)
    df = pd.DataFrame({"lon": lon, "lat": lat, "year": years[ids].astype(np.float32), "strong": strong[ids],
                       "b": ids.astype(np.int32)})
    df.to_parquet(EVIDENCE)
    log(f"ground: evidence from {len(geoms)} dated outlines ({int(strong.sum())} strong, {len(df)} points) -> {EVIDENCE.name}")


def evidence_on(g):
    """Per cell of grid g: (strong_year, weak_year, weak_second) — the earliest strong
    evidence, the earliest and second-earliest recorded assessor year (different buildings)."""
    rows, cols = g["rows"], g["cols"]
    strong_y = np.full((rows, cols), np.nan, np.float32)
    weak1 = np.full((rows, cols), np.nan, np.float32)
    weak2 = np.full((rows, cols), np.nan, np.float32)
    if not EVIDENCE.exists():
        return strong_y, weak1, weak2
    e = pd.read_parquet(EVIDENCE)
    X = np.radians(e.lon.values.astype(float)) * 6378137.0
    Y = 6378137.0 * np.log(np.tan(np.pi / 4 + np.radians(e.lat.values.astype(float)) / 2))
    # (only the points on this grid: a window of the region is a tenth of it)
    on = (X >= g["X0"] - 2 * g["res"]) & (X <= g["X0"] + (cols + 1) * g["res"]) & (Y <= g["Y0"] + 2 * g["res"]) & (Y >= g["Y0"] - (rows + 1) * g["res"])
    e, X, Y = e[on], X[on], Y[on]
    # each point speaks for the 2 x 2 cells around it (as land_year_at reads them)
    c0 = np.floor((X - g["X0"]) / g["res"]).astype(np.int64)
    r0 = np.floor((g["Y0"] - Y) / g["res"]).astype(np.int64)
    parts = []
    for dr in (0, 1):
        for dc in (0, 1):
            r, c = r0 + dr, c0 + dc
            ok = (c >= 0) & (c < cols) & (r >= 0) & (r < rows)
            parts.append(e[ok].assign(cell=(r[ok] * cols + c[ok])))
    e = pd.concat(parts, ignore_index=True)
    s = e[e.strong].groupby("cell").year.min()
    strong_y.ravel()[s.index.values] = s.values
    # one year per building per cell, then the two earliest buildings
    w = e[~e.strong].groupby(["cell", "b"]).year.min().reset_index().sort_values(["cell", "year"])
    w["k"] = w.groupby("cell").cumcount()
    w1 = w[w.k == 0]
    w2 = w[w.k == 1]
    weak1.ravel()[w1.cell.values] = w1.year.values
    weak2.ravel()[w2.cell.values] = w2.year.values
    return strong_y, weak1, weak2
