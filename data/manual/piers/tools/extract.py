"""Pier candidates of one USGS 1:24,000 sheet.

  python extract.py <sheet.tif> [...]        (no argument: every sheet of sheets.json that has no output yet)

What a sheet shows: the 1955-67 sheets draw a pier as a black outline, hatched where a shed covers it, white where the
deck is open; the Army Map Service sheets of 1947 draw sheds solid black and open piers as outlines.  Water has a blue
tint on most sheets and none on some scans.

Steps (in the sheet's own pixels, 2.03 m):
 1. colours: water colour = median of today's open water 120 m off today's shore; paper = the collar; land colours =
    k-means of today's old land.  The sheet is "tinted" when water and paper differ.
 2. non-water: tinted sheet -> every pixel that is not water-coloured (5x5 majority);
               untinted sheet -> black ink closed by a pixel, holes of 5 ha or less filled (outlined piers, hatching),
               plus today's land that was land at the sheet's date (Overture water + the made-land grid).
 3. solid = non-water opened by 3 px (drops lines, lettering);  core land = non-water opened by 45 m (drops everything
    narrower than 90 m);  fingers = solid - core land.
 4. each finger: outline, axis rectangle, how far it reaches from the core land, where it touches it, ink share (shed).
Outputs (data/interim/piers/): cand/<sheet>.geojson (every finger of 250 m2 or more, unfiltered, WGS84),
cls/<sheet>.tif (0 water, 1 solid, 2 core land, 255 outside the neat line) and cls/<sheet>.json (colours, shift against
today's shoreline).
"""
import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pyproj
import rasterio
import shapely
from rasterio import features
from rasterio.warp import Resampling, reproject
from scipy import ndimage
from scipy.cluster.vq import kmeans2
from shapely.geometry import Polygon, shape

ROOT = Path("/home/user/nyc")
RAW = ROOT / "data/raw/piers"
OUT = ROOT / "data/interim/piers"
pyproj.datadir.append_data_dir(str(RAW / "proj"))
# NADCON grid (PROJ CDN, us_noaa_conus.tif, public domain): NAD27 -> NAD83 (taken as WGS84, < 1 m apart on this map)
NADCON = pyproj.Transformer.from_pipeline("+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad "
                                          "+step +proj=hgridshift +grids=us_noaa_conus.tif "
                                          "+step +proj=unitconvert +xy_in=rad +xy_out=deg")
SHEETS = json.load(open(Path(__file__).parent / "sheets.json"))
R_CORE = 22          # px: core land = opening by 45 m
R_SOLID = 3          # px
MIN_PX = 60          # 250 m2


class Geo:
    """sheet CRS (transverse Mercator / polyconic on NAD27) <-> WGS84 through NADCON."""

    def __init__(self, crs):
        self.t = pyproj.Transformer.from_crs(crs.to_wkt(), "EPSG:4267", always_xy=True)

    def to_wgs(self, x, y):
        lon, lat = self.t.transform(x, y)
        return NADCON.transform(lon, lat)

    def from_wgs(self, lon, lat):
        lon, lat = NADCON.transform(lon, lat, direction="INVERSE")
        return self.t.transform(lon, lat, direction="INVERSE")

    def geom_from_wgs(self, g):
        return shapely.transform(g, lambda c: np.column_stack(self.from_wgs(c[:, 0], c[:, 1])))

    def geom_to_wgs(self, g):
        return shapely.transform(g, lambda c: np.column_stack(self.to_wgs(c[:, 0], c[:, 1])))


def today_water(geo, bbox_wgs):
    x0, y0, x1, y1 = bbox_wgs
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    rows = con.execute(f"""SELECT ST_AsWKB(geometry) FROM '{ROOT}/data/raw/overture/2026-10-21.0/base_water.parquet'
        WHERE class NOT IN ('swimming_pool', 'wastewater', 'reflecting_pool', 'shoal', 'stream', 'drain', 'ditch')
          AND ST_XMax(geometry) > {x0} AND ST_XMin(geometry) < {x1} AND ST_YMax(geometry) > {y0} AND ST_YMin(geometry) < {y1}
          AND (subtype IN ('ocean', 'physical', 'river', 'canal') OR ST_Area(geometry) > 3e-7)""").fetchall()
    clip = shapely.box(x0, y0, x1, y1)
    out = []
    for (w,) in rows:
        g = shapely.from_wkb(bytes(w))
        if not g.is_valid:
            g = g.buffer(0)
        g = g.intersection(clip)
        if not g.is_empty:
            out.append(geo.geom_from_wgs(g))
    return out


def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def run(fn):
    info = SHEETS[fn]
    year = info["date_on_map"]
    photo = info.get("aerial_photo_year") or info.get("survey_year") or year
    with rasterio.open(RAW / "usgs" / fn) as s:
        rgb = s.read()
        tr, crs, H, W = s.transform, s.crs, s.height, s.width
    if rgb.shape[0] == 1:
        rgb = np.repeat(rgb, 3, axis=0)
    rgb = rgb[:3]
    geo = Geo(crs)
    b = info["bbox"]
    t = np.linspace(0, 1, 40)
    ring = [(b["minX"] + (b["maxX"] - b["minX"]) * a, b["minY"]) for a in t] + [(b["maxX"], b["minY"] + (b["maxY"] - b["minY"]) * a) for a in t] + \
           [(b["maxX"] - (b["maxX"] - b["minX"]) * a, b["maxY"]) for a in t] + [(b["minX"], b["maxY"] - (b["maxY"] - b["minY"]) * a) for a in t]
    qx, qy = geo.t.transform([p[0] for p in ring], [p[1] for p in ring], direction="INVERSE")
    quad_poly = Polygon(list(zip(qx, qy)))
    quad = features.rasterize([(quad_poly, 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
    wl, sl, el, nl = *NADCON.transform(b["minX"], b["minY"]), *NADCON.transform(b["maxX"], b["maxY"])
    wpolys = today_water(geo, (wl - 0.01, sl - 0.01, el + 0.01, nl + 0.01))
    w_today = features.rasterize([(g, 1) for g in wpolys], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool) if wpolys else np.zeros((H, W), bool)
    # made-land grid -> sheet pixels (cells of 38 m web-mercator; the 11 m of the grid-less datum shift do not matter here)
    meta = json.load(open(ROOT / "data/interim/grid_detail_meta.json"))
    ly = np.load(ROOT / "data/interim/grid_detail_landyear.npy").astype("float32")
    ly_s = np.full((H, W), np.nan, "float32")
    reproject(ly, ly_s, src_transform=rasterio.Affine(*meta["transform"]), src_crs="EPSG:3857", dst_transform=tr, dst_crs=crs,
              resampling=Resampling.nearest, src_nodata=np.nan, dst_nodata=np.nan)
    later = ly_s > photo            # land made after the sheet
    del ly, ly_s

    lum = ((rgb[0].astype("uint16") + rgb[1] + rgb[2]) // 3).astype("uint8")
    chroma = rgb.max(0) - rgb.min(0)
    paper_lum = float(np.median(lum[::7, ::7][~quad[::7, ::7]]))
    ink = (lum < paper_lum - 60) & (chroma < 100)     # thin lines are grey after resampling: threshold relative to the paper
    rng = np.random.default_rng(0)

    def sample(mask, n=150000):
        idx = np.flatnonzero(mask.ravel())
        if len(idx) == 0:
            return np.zeros((0, 3), "float32")
        idx = rng.choice(idx, min(n, len(idx)), replace=False)
        return np.stack([rgb[i].ravel()[idx] for i in range(3)], axis=1).astype("float32")

    # colours
    w4 = w_today[::4, ::4]
    deep = ndimage.distance_transform_edt(w4) > 15            # 120 m off today's shore
    inland = ndimage.distance_transform_edt(~w4) > 10
    up = lambda m: np.repeat(np.repeat(m, 4, axis=0), 4, axis=1)[:H, :W]
    light = lum > 130
    sw = sample(up(deep) & quad & light & ~later)
    c_w = np.median(sw, axis=0) if len(sw) > 500 else None
    c_p = np.median(sample(~quad & light), axis=0)
    sl_ = sample(up(inland) & quad & light & ~later)
    cents, _ = kmeans2(sl_, 5, minit="++", seed=1)
    tinted = c_w is not None and float(np.linalg.norm(c_w - c_p)) >= 28
    meta_out = dict(sheet=fn, edition=info["edition"], quad=info["quad"], date_on_map=year, photo_year=photo, tinted=bool(tinted),
                    water_rgb=None if c_w is None else [int(v) for v in c_w], paper_rgb=[int(v) for v in c_p],
                    land_rgb=[[int(v) for v in c] for c in cents])
    if tinted:
        others = [c for c in list(cents) + [c_p] if np.linalg.norm(c - c_w) >= 25]
        water = np.zeros((H, W), bool)
        for a in range(0, H, 1024):
            blk = np.stack([ndimage.uniform_filter(rgb[i, max(a - 2, 0):a + 1026].astype("float32"), 3) for i in range(3)], axis=-1)
            blk = blk[(a - max(a - 2, 0)):(a - max(a - 2, 0)) + min(1024, H - a)]
            dw = np.linalg.norm(blk - c_w, axis=-1)
            do = np.min(np.stack([np.linalg.norm(blk - c, axis=-1) for c in others], axis=0), axis=0)
            water[a:a + 1024] = (dw < do) & (dw < 55)
        water &= ~ink
        water = ndimage.uniform_filter(water.astype("float32"), 5) > 0.5
        nonwater = quad & ~water
        del water
    else:
        closed = ndimage.binary_closing(ink, structure=np.ones((3, 3), bool))
        closed |= ndimage.uniform_filter(ink.astype("float32"), 5) > 0.22      # hatching (sheds) without relying on a closed outline
        lab, n = ndimage.label(~closed)
        size = np.bincount(lab.ravel())
        small = size <= 12000
        small[0] = False
        filled = closed | small[lab]
        del lab
        nonwater = quad & (filled | (~w_today & ~later))
    analyse(nonwater, quad, ink, later, w_today, tr, crs, geo, fn, info, meta_out, tinted, abs(tr.a))


def analyse(nonwater, quad, ink, later, w_today, tr, crs, geo, fn, info, meta_out, register, px_m, unit_m=1.0):
    """Fingers of a non-water mask (see the module docstring, steps 3-4).  px_m = ground metres per pixel,
    unit_m = ground metres per CRS unit (1 for the USGS sheets, cos(latitude) for a chart kept in web-Mercator)."""
    H, W = nonwater.shape
    R_SOLID_, R_CORE_, MIN_PX_ = max(2, int(round(6.1 / px_m))), 2 * int(round(22.3 / px_m)), int(round(250 / px_m ** 2))
    solid = ndimage.binary_opening(nonwater, structure=disk(R_SOLID_)) & quad
    # core land at half resolution
    nw2 = nonwater[::2, ::2]
    er = ndimage.distance_transform_edt(nw2) > R_CORE_ / 2
    d_er = ndimage.distance_transform_edt(~er).astype("float32")      # px of 4 m from the eroded core
    up2 = lambda m: np.repeat(np.repeat(m, 2, axis=0), 2, axis=1)[:H, :W]
    core = up2(d_er <= R_CORE_ / 2) & nonwater
    fingers = solid & ~core

    # shift against today's shoreline (tinted sheets: the sheet's own water)
    if register:
        a_ = (~nw2 & quad[::2, ::2])
        e_old = a_ ^ ndimage.binary_erosion(a_)
        w2 = w_today[::2, ::2]
        e_new = ndimage.binary_dilation(w2 ^ ndimage.binary_erosion(w2), structure=np.ones((3, 3), bool))
        cc = np.fft.irfft2(np.fft.rfft2(e_new.astype("float32")) * np.conj(np.fft.rfft2(e_old.astype("float32"))), s=e_old.shape)
        R = 12
        win = np.concatenate([np.concatenate([cc[-R:, -R:], cc[-R:, :R + 1]], axis=1), np.concatenate([cc[:R + 1, -R:], cc[:R + 1, :R + 1]], axis=1)], axis=0)
        iy, ix = np.unravel_index(np.argmax(win), win.shape)
        meta_out["shift_m"] = [float((ix - R) * 2 * px_m), float(-(iy - R) * 2 * abs(tr.e))]    # east, north to add to the sheet
        meta_out["shift_peak"] = round(float(win.max() / (np.median(win) + 1e-6)), 2)
        del cc

    lab, n = ndimage.label(fingers, structure=np.ones((3, 3), bool))
    objs = ndimage.find_objects(lab)
    feats = []
    for i, sl in enumerate(objs, start=1):
        if sl is None:
            continue
        r0, r1, c0, c1 = max(sl[0].start - 8, 0), min(sl[0].stop + 8, H), max(sl[1].start - 8, 0), min(sl[1].stop + 8, W)
        r0, c0 = r0 - r0 % 2, c0 - c0 % 2
        m0 = lab[r0:r1, c0:c1] == i
        if int(m0.sum()) < MIN_PX_:
            continue
        # drop what is much thinner than the finger itself (lettering, ferry lines, fenders); joined fingers fall apart
        dt0 = ndimage.distance_transform_edt(m0)
        h = float(dt0.max())
        if h < 6.1 / px_m:
            continue
        rr = int(max(2, round(0.45 * h)))
        opened = ndimage.distance_transform_edt(dt0 <= rr) <= rr        # opening by a disk, through two distance transforms
        lab2, n2 = ndimage.label(opened & m0)
        d = d_er[r0 // 2:(r1 + 1) // 2, c0 // 2:(c1 + 1) // 2]
        for j in range(1, n2 + 1):
            m = lab2 == j
            npx = int(m.sum())
            if npx < MIN_PX_:
                continue
            mm = m[::2, ::2][:d.shape[0], :d.shape[1]]
            if not mm.any():
                continue
            dd = (d[:mm.shape[0], :mm.shape[1]][mm] - R_CORE_ / 2) * 2 * px_m
            reach, gap = float(dd.max()), float(max(dd.min(), 0.0))
            if reach < 20:
                continue
            ys, xs = np.nonzero(m)
            a0, a1, b0, b1 = max(ys.min() - rr - 4, 0), ys.max() + rr + 5, max(xs.min() - rr - 4, 0), xs.max() + rr + 5
            near = np.zeros_like(m)
            near[a0:a1, b0:b1] = ndimage.distance_transform_edt(~m[a0:a1, b0:b1]) <= rr + 3
            contact = near & core[r0:r1, c0:c1]
            polys = [shape(g) for g, v in features.shapes(m.astype("uint8"), mask=m, transform=tr * rasterio.Affine.translation(c0, r0)) if v == 1]
            poly = max(polys, key=lambda p: p.area).buffer(0)
            poly = Polygon(poly.exterior).simplify(1.5 * abs(tr.a))
            rect = poly.minimum_rotated_rectangle
            rc = np.array(rect.exterior.coords)[:4]
            e1, e2 = rc[1] - rc[0], rc[2] - rc[1]
            if np.hypot(*e1) < np.hypot(*e2):
                e1, e2 = e2, e1
            length, width = float(np.hypot(*e1)), float(np.hypot(*e2))
            ax = e1 / (length + 1e-9)
            both, root = False, 0.0
            n_contact = int(contact.sum())
            if n_contact:
                cy, cx = np.nonzero(contact)
                X, Y = tr * (cx + c0 + 0.5, cy + r0 + 0.5)
                sproj = ((np.column_stack([X, Y]) - rc[0]) @ ax - (np.array(poly.centroid.coords[0]) - rc[0]) @ ax) / (length + 1e-9)
                both = bool(sproj.min() < -0.3 and sproj.max() > 0.3)       # attached at both ends: a bridge, a causeway, a quay
                root = float(np.median(sproj))
            feats.append(dict(type="Feature", geometry=shapely.geometry.mapping(geo.geom_to_wgs(poly)),
                              properties=dict(sheet=fn, edition=info["edition"], quad=info["quad"], area_m2=round(poly.area * unit_m ** 2),
                                              length_m=round(length * unit_m, 1), width_m=round(width * unit_m, 1), rect_fill=round(poly.area / (rect.area + 1e-9), 3), reach_m=round(reach, 1),
                                              gap_m=round(gap, 1), contact_px=n_contact, both_ends=both, root_side=round(root, 2),
                                              ink=round(float(ink[r0:r1, c0:c1][m].mean()), 3),
                                              edge=bool((~quad[r0:r1, c0:c1] & near).any()),
                                              on_made_land=round(float(later[r0:r1, c0:c1][m].mean()), 2),
                                              on_today_land=round(float((~w_today[r0:r1, c0:c1])[m].mean()), 2))))
    (OUT / "cand").mkdir(parents=True, exist_ok=True)
    (OUT / "cls").mkdir(parents=True, exist_ok=True)
    json.dump(dict(type="FeatureCollection", features=feats), open(OUT / "cand" / fn.replace(".tif", ".geojson"), "w"))
    cls = np.zeros((H, W), "uint8")
    cls[solid] = 1
    cls[core] = 2
    cls[~quad] = 255
    with rasterio.open(OUT / "cls" / fn, "w", driver="GTiff", height=H, width=W, count=2, dtype="uint8", crs=crs, transform=tr, compress="deflate",
                       tiled=True) as dst:
        dst.write(cls, 1)
        dst.write(ink.astype("uint8"), 2)
    meta_out["n_candidates"] = len(feats)
    json.dump(meta_out, open(OUT / "cls" / fn.replace(".tif", ".json"), "w"), indent=1)
    print(fn, {k: meta_out[k] for k in ("edition", "tinted", "water_rgb", "paper_rgb", "n_candidates")}, meta_out.get("shift_m"), meta_out.get("shift_peak"), flush=True)


if __name__ == "__main__":
    todo = sys.argv[1:] or [f for f in SHEETS if not (OUT / "cls" / f.replace(".tif", ".json")).exists() and (RAW / "usgs" / f).exists()]
    for f in todo:
        try:
            run(f)
        except Exception as e:      # one broken scan must not stop the rest
            print("FAILED", f, repr(e), flush=True)
