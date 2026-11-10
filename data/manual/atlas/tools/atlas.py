"""Trace building footprints from the coloured real-estate atlases of the 1880s-1900s (NYPL scans).

Not a pipeline stage: it writes hand-checked data into data/manual/atlas/ (committed).

    python -I atlas.py fetch   <layer> [plate ...]      # NYPL master scans -> data/raw/atlas/nypl_u/<imageId>.jpg
    python -I atlas.py refine  <layer> [plate ...]      # street match -> data/interim/atlas/<layer>/<plate>_corr.json
    python -I atlas.py trace   <layer> [plate ...]      # per plate -> data/interim/atlas/<layer>/<plate>.pkl + stats
    python -I atlas.py refine_buildings <layer> [plate ...]   # city plates: fine registration on standing buildings
    python -I atlas.py regeo   <layer> [plate ...]      # ground outlines again after a change of registration
    python -I atlas.py score_frames <layer>             # yellow strength of frame outlines (washed lots, Bronx)
    python -I atlas.py export  <layer>                  # -> data/manual/atlas/<layer>.geojson + _coverage.geojson + _stats.json
    python -I atlas.py readme                           # the per-plate tables of data/manual/atlas/README.md
    python -I atlas.py overlay <layer> <plate> <x,y> <size_m> <out.png> [--px] [--scale 3] [--final]
                                                        # plate crop with traced outlines (red = frame, magenta = brick;
                                                        # --final: the exported layer) and today's footprints (cyan),
                                                        # for checking by eye
    python -I atlas.py colours <layer> <plate> <x0,y0,x1,y1 px> <out.png>   # class picture of a crop (calibration)

<layer> = a key of layers.json (next to this file); <plate> = NYPL Map Warper map id, or an id of gcps_own.json
(plates that are not in the Map Warper dump, with control points made here: 900019, 900035).
layers.json per layer: atlas, map_year, source, style, style_override, plates (id, sheet, skip), and optionally
clip (north_of: two lon / lat points; outside_layers: coverage of other layers to stay out of), frame_yellow,
stone_min_m2 / stone_min_width_m / stone_max_aspect.

Method (details, residuals and what was seen in data/manual/atlas/README.md):
  * scan and control points: the Map Warper record of each plate in the NYC Space/Time Directory dump (CC0) and
    NYPL's full-size master scan, as worked out for data/manual/extents (tools/warp.py is reused from there).
  * registration: the Map Warper control points (affine / 2nd order / thin-plate spline by cross-validation), then
    `refine`: the plate's street tint is matched to today's street centrelines in windows and the consensus of the
    window shifts corrects the fit (constant shift, or affine when enough windows agree); `refine_buildings`: the
    same on today's footprints of pre-war buildings, for city plates. The residual reported per plate is measured
    on buildings that still stand (traced outline against today's footprint).
  * footprints: pixel classes in CIE Lab relative to the plate's paper colour (frame = the yellow / ochre fill,
    brick = the rose / carmine fill, stone = grey, ink). County plates: property bands of the same pigments are
    removed by width and by the ink outline a building has all round. City plates: the fill of a row is cut at
    the party walls (the connected thin lines); with a `blue` setting, round pale blue fills are gasholders.
    The export drops band pieces, lettering, washed lots and water, and applies the layer's clip.
Local coordinates: X = UTM 18N easting - 580000, Y = northing - 4500000 (metres), as in the extents tools.
"""
from __future__ import annotations

import json
import os
import pickle
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import shapely
import shapely.affinity
import shapely.geometry as sg
from shapely import wkb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "data" / "manual" / "extents" / "tools"))  # warp.py, streets.py (read-only reuse)
import warp  # noqa: E402
import streets as S  # noqa: E402

# control points made here, for plates that are not in the Map Warper dump (same record format as the dump's;
# the extents tools keep their own file of this kind, which is not used or changed here)
warp.OWN = HERE / "gcps_own.json"

Image.MAX_IMAGE_PIXELS = None
RAW = ROOT / "data" / "raw" / "atlas" / "nypl_u"
WORK = ROOT / "data" / "interim" / "atlas"
OUT = ROOT / "data" / "manual" / "atlas"
FOOT = ROOT / "data" / "interim" / "nyc_footprints_raw.parquet"
UA = {"User-Agent": "NYCThroughTime-research/0.1"}

# --------------------------------------------------------------------------------------------- styles
# Thresholds are offsets from the plate's paper colour (Lab mode of the light pixels), so that a browner or
# paler copy reads the same. All lengths in source pixels unless they end in _m.
STYLES = {
    # E. Robinson, county atlases at 300 ft to the inch (0.48 m per pixel): ochre frame buildings, carmine brick,
    # property bands in orange / carmine / green 3-5 m wide, streets and laid-out blocks tinted peach or grey.
    # Measured on plate 22 (paper Lab 87, 0, 9): frame fill L 61-73, a 5-10, b 28-40; orange band a 10-14, b 27-30
    # (redder: a / b over paper 0.5-0.6 against 0.2-0.33); peach tint L 77-82, b 18-21 (9-12 over paper: under the
    # frame threshold of 15); carmine L 66, a 21, b 13. The frame fill is pale on some sheets (plate 21, Coney
    # Island: L 78-79, b 28), so lightness does not limit it.
    "robinson_300ft": dict(
        frame=dict(db_min=15.0, hue=0.42, L_min=36, L_max=84.0),
        band=dict(db_min=12.0),                      # the orange property band (warm, redder than the frame fill)
        brick=dict(da_min=12.0, db_max=9.0, L_min=42),
        ink=dict(L_max=47, db_max=9.0),
        ink_grow=2, hole_px=150,
        core_frame=9, core_brick=11, outline=0.62, outline_low=0.3, compact=14.0, outline_brick=0.72, outline_warm=0.7, line_depth=8.0,                # a building is wider than a band: opening by this many pixels
        small_open=5, small_r=2.6, band_grow=2,      # narrower frame buildings (sheds): by colour, away from bands
        split_by_ink=False, min_m2=15.0, max_m2=5000.0,
    ),
    # G. W. Bromley, city atlases at about 160 ft to the inch (0.24 m per pixel): rows of houses in rose (brick)
    # with a grey strip along the street front (stone front), grey (stone) and yellow (frame) buildings; party
    # walls are the lot lines drawn through the fill; streets and empty lots are left paper.
    # Measured on plate 40 of 1897 (paper Lab 83, -1, 10): rose L 64-67, a 12-17, b 3-6; grey L 60-65, a 2, b 6.5;
    # yellow L 75, a -5, b 24-27; party-wall lines dip to L 52-58 on the rose.
    "bromley_city": dict(
        frame=dict(db_min=9.0, hue=0.42, L_min=50, L_max=84),
        band=None,
        brick=dict(da_min=7.5, db_max=4.0, L_min=45),
        stone=dict(da_abs=5.5, db_min=-9.0, db_max=0.5, dL_min=-28.0, dL_max=-11.0),
        ink=dict(L_max=47, db_max=9.0),
        line_depth=5.0, wall_px=120, hole_px=150, core=7, outline=0.55, front_px=900,
        split_by_ink=True, min_m2=15.0, max_m2=5000.0,
    ),
}


def layers() -> dict:
    return json.loads((HERE / "layers.json").read_text())


# --------------------------------------------------------------------------------------------- pixels
_LIN = None


def rgb2lab(rgb):
    """CIE Lab (D65) of an sRGB uint8 array."""
    global _LIN
    if _LIN is None:
        c = np.arange(256, dtype=np.float32) / 255
        _LIN = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92).astype(np.float32)
    c = _LIN[rgb]
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]], np.float32)
    xyz = c @ (M.T / np.array([0.95047, 1.0, 1.08883], np.float32))
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def paper_colour(img, inside=None):
    """Lab mode of the plate's light pixels (the paper), from a 1-in-7 subsample."""
    sub = img[::7, ::7]
    lab = rgb2lab(sub)
    ok = lab[..., 0] > 60
    if inside is not None:
        ok &= inside[::7, ::7]
    q = np.round(lab[ok]).astype(int)
    key = q[:, 0] * 1000000 + (q[:, 1] + 500) * 1000 + (q[:, 2] + 500)
    u, n = np.unique(key, return_counts=True)
    k = u[np.argmax(n)]
    return np.array([k // 1000000, (k // 1000) % 1000 - 500, k % 1000 - 500], float)


def classes(img, paper, st, lab_all=None):
    """uint8 per pixel: 0 other, 1 ink, 2 frame fill, 3 brick fill, 4 stone (grey) fill, 5 orange band,
    6 pale blue (iron: gasholders - and the water wash; city plates with a `blue` setting only)."""
    H = img.shape[0]
    out = np.zeros(img.shape[:2], np.uint8)
    for r0 in range(0, H, 1024):
        lab = rgb2lab(img[r0:r0 + 1024]) if lab_all is None else lab_all[r0:r0 + 1024]
        L, da, db = lab[..., 0], lab[..., 1] - paper[1], lab[..., 2] - paper[2]
        c = np.zeros(L.shape, np.uint8)
        k = st["ink"]
        c[(L < k["L_max"]) & (db < k["db_max"])] = 1
        k = st["frame"]
        warm = (L > k["L_min"]) & (L < k["L_max"])
        c[warm & (db > k["db_min"]) & (da < k["hue"] * db)] = 2
        if st.get("band"):
            c[warm & (db > st["band"]["db_min"]) & (da >= k["hue"] * db)] = 5
        if st.get("stone"):
            k = st["stone"]
            dL = L - paper[0]
            c[(np.abs(da) < k["da_abs"]) & (db > k["db_min"]) & (db < k["db_max"]) & (dL > k["dL_min"]) & (dL < k["dL_max"])] = 4
        if st.get("blue"):
            k = st["blue"]
            dL = L - paper[0]
            c[(db < k["db_max"]) & (db > k["db_min"]) & (da > k["da_min"]) & (da < k["da_max"]) & (dL > k["dL_min"]) & (dL < k["dL_max"])] = 6
        k = st["brick"]
        c[(da > k["da_min"]) & (db < k["db_max"]) & (L > k["L_min"])] = 3
        out[r0:r0 + 1024] = c
    return out


def thin_lines(img, depth=8.0, L=None):
    """Drawn lines 1-3 pixels wide, whatever they are drawn on: darker than their surroundings by `depth` in L
    (black top-hat over 5 x 5). The outline of a building on its own fill is found this way; the ink class alone
    (dark and neutral) misses it."""
    if L is None:
        L = np.concatenate([rgb2lab(img[r0:r0 + 1024])[..., 0] for r0 in range(0, img.shape[0], 1024)])
    return ndi.grey_closing(L, size=(5, 5)) - L > depth


SQ3 = np.ones((3, 3), bool)
CROSS = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)


def _open(m, n):
    return ndi.maximum_filter(ndi.minimum_filter(m.view(np.uint8), size=n), size=n).view(bool)


def _close(m, n):
    return ndi.minimum_filter(ndi.maximum_filter(m.view(np.uint8), size=n), size=n).view(bool)


def _dil(m, k):
    return ndi.maximum_filter(m.view(np.uint8), size=2 * k + 1).view(bool)


def _grow(f, ink, st):
    """A fill with the ink lying on it (the X of a stable, lettering, hatching) filled in: ink pixels between fill
    on both sides (closing by 5 x 5). The outline is not taken in - that would widen property bands past the
    width test - so a traced building is about one line width smaller all round; `fills` adds it back."""
    g = f | (_close(f, 5) & ink)
    g = _close(g, 3)
    holes = ndi.binary_fill_holes(g) & ~g
    lab, n = ndi.label(holes)
    if n:
        small = np.zeros(n + 1, bool)
        small[1:] = ndi.sum(holes, lab, np.arange(1, n + 1)) <= st["hole_px"]
        g |= small[lab]
    return g


def _wide(g, n_core):
    """The parts of a mask wider than n_core pixels, with their corners back (bands and lettering drop out)."""
    return _dil(_open(g, n_core), n_core // 2) & g


def select(mask, ink, hi, lo=None, compact=14.0):
    """Components of a fill mask that are buildings.
    A building has an ink outline all round; a property band of the same pigment has the lot line along one side
    only. Kept: outline share >= hi; or >= lo when the shape is compact (area / inscribed radius^2 <= compact,
    about 3.5 : 1 - a piece of band is long)."""
    lab, n = ndi.label(mask, structure=CROSS)
    if n == 0:
        return mask
    idx = np.arange(1, n + 1)
    edge = mask & ~ndi.binary_erosion(mask, CROSS)
    near = _dil(ink, 2)
    share = ndi.sum(edge & near, lab, idx) / np.maximum(ndi.sum(edge, lab, idx), 1)
    good = share >= hi
    if lo is not None:
        area = ndi.sum(mask, lab, idx)
        r = ndi.maximum(ndi.distance_transform_edt(mask), lab, idx)
        good |= (share >= lo) & (area / np.maximum(r, 1) ** 2 <= compact)
    ok = np.zeros(n + 1, bool)
    ok[1:] = good
    return ok[lab]


def fills(c, line, st, inside):
    """Binary masks of frame and brick buildings from the class raster and the thin-line raster."""
    ink = (c == 1) | line
    res = {}
    # frame: the frame hue only (a building standing on an orange band is cut from it by hue), wide ...
    g = _grow((c == 2) & inside, ink, st)
    wide = _wide(g, st["core_frame"])
    # ... plus narrower fills that do not hug a band (the band's fringe has the frame hue)
    band = _open(c == 5, 3)
    strict = g & ~_dil(band, st["band_grow"])
    small = _open(strict, st["small_open"])
    lab, n = ndi.label(small, structure=CROSS)
    if n:
        idx = np.arange(1, n + 1)
        r = ndi.maximum(ndi.distance_transform_edt(small), lab, idx)
        touch = ndi.sum(wide, lab, idx)
        ok = np.zeros(n + 1, bool)
        ok[1:] = (r >= st["small_r"]) & (touch == 0)
        small = ok[lab]
    A = select(wide | small, ink, st["outline"], st["outline_low"], st["compact"])
    # ... plus compact wide fills of either warm hue with a full outline, where the first path found nothing
    # (a building of a redder ochre standing on or beside an orange band)
    # (only in tiles where such fills are common - see trace_window; elsewhere it would mostly add band pieces)
    if st.get("warm_path"):
        B = select(_wide(_grow(((c == 2) | (c == 5)) & inside, ink, st), st["core_frame"]), ink, 2.0, st["outline_warm"], st["compact"])
        lab, n = ndi.label(B, structure=CROSS)
        if n:
            ok = np.zeros(n + 1, bool)
            ok[1:] = ndi.sum(A, lab, np.arange(1, n + 1)) == 0
            B = ok[lab]
        A = A | B
    res["frame"] = A
    res["brick"] = select(_wide(_grow((c == 3) & inside, ink, st), st["core_brick"]), ink, st["outline_brick"])
    for k in res:  # the outline belongs to the building
        res[k] = ndi.binary_dilation(res[k], CROSS, mask=res[k] | ink)
    return res


def fills_rows(c, line, st, inside):
    """Buildings of a city atlas: label raster (one label per building) and the material of each label.
    The fill of a row runs through from house to house; the party walls are the lot lines drawn across it. Walls =
    the thin drawn lines that hang together (the lot-line network: connected components of st['wall_px'] pixels or
    more, without strokes 3 pixels thick or more, which are figures); figures and ditto marks on the fill are
    filled in. Each connected piece of fill between walls is a building; its material is the pigment that prevails;
    a small grey piece against a rose one is that house's stone front and is joined to it."""
    ink = (c == 1) | line
    fill = ((c == 2) | (c == 3) | (c == 4) | (c == 6)) & inside
    thin = ink & ~_dil(_open(c == 1, 3), 1)
    lab, n = ndi.label(thin, structure=SQ3)
    if n:
        big = np.zeros(n + 1, bool)
        big[1:] = np.bincount(lab.ravel(), minlength=n + 1)[1:] >= st["wall_px"]
        walls = big[lab]
    else:
        walls = thin
    g = (fill | (_close(fill, 5) & ink)) & ~walls
    g = _open(g, 3)
    # buildings are wider than st['core'] pixels (pencil lines, tinted strips and specks are not)
    g = _dil(_open(g, st["core"]), st["core"] // 2) & g
    lab, n = ndi.label(g, structure=CROSS)
    if n == 0:
        return lab, np.array([], object)
    idx = np.arange(1, n + 1)
    edge = g & ~ndi.binary_erosion(g, CROSS)
    share = ndi.sum(edge & _dil(ink, 2), lab, idx) / np.maximum(ndi.sum(edge, lab, idx), 1)
    counts = np.stack([ndi.sum(c == k, lab, idx) for k in (2, 3, 4, 6)], 1)
    kind = np.argmax(counts, 1)                      # 0 frame, 1 brick, 2 stone, 3 iron (pale blue)
    area = counts.sum(1)
    ok = np.zeros(n + 1, bool)
    ok[1:] = share >= st["outline"]
    if st.get("outline_big"):
        # a large, wide fill (a church, a depot, a factory) is a building with less of its outline found: bold
        # lettering stands on it and the wash is uneven (St Patrick's Cathedral came out with 48 %)
        rmax = ndi.maximum(ndi.distance_transform_edt(g), lab, idx)
        ok[1:] |= (area >= st["big_px"]) & (rmax >= st["big_r"]) & (share >= st["outline_big"])
    lab = np.where(ok[lab], lab, 0)
    # stone fronts: a small grey piece joins the rose piece it lies against
    isbrick = np.zeros(n + 1, bool)
    isbrick[1:] = kind == 1
    near = ndi.grey_dilation(np.where(isbrick[lab], lab, 0), size=(9, 9))
    sl = ndi.find_objects(lab)
    target = {}
    for i in np.flatnonzero((kind == 2) & (area <= st["front_px"]) & ok[1:]):
        s_ = sl[i]
        if s_ is None:
            continue
        m = lab[s_] == i + 1
        v = near[s_][m]
        v = v[v > 0]
        if len(v) >= max(6, 0.04 * m.sum()):
            target[i + 1] = int(np.bincount(v).argmax())
    for src, dst in target.items():
        lab[sl[src - 1]][lab[sl[src - 1]] == src] = dst
    for dst in set(target.values()):                 # close the line between the two parts
        y, x = sl[dst - 1]
        y = slice(max(0, y.start - 12), y.stop + 12)
        x = slice(max(0, x.start - 12), x.stop + 12)
        m = lab[y, x] == dst
        m2 = ndi.binary_closing(m, np.ones((7, 7), bool)) & (lab[y, x] == 0)
        lab[y, x][m2] = dst
    return lab, np.array(["frame", "brick", "stone", "iron"], object)[kind]


def label_polygons(lab, min_px, max_px):
    """(polygon in pixel coordinates, label) for each label of a label raster within the size limits."""
    from rasterio import features
    n = int(lab.max())
    if n == 0:
        return []
    area = np.bincount(lab.ravel(), minlength=n + 1)
    keep = (area >= min_px) & (area <= max_px)
    keep[0] = False
    lab2 = np.where(keep[lab], lab, 0).astype(np.int32)
    out = []
    for geom, v in features.shapes(lab2, mask=lab2 > 0, connectivity=4):
        p = sg.shape(geom)
        if not p.is_valid:
            p = p.buffer(0)
        if p.is_empty:
            continue
        p = sg.Polygon(p.exterior) if p.geom_type == "Polygon" else sg.Polygon(max(p.geoms, key=lambda g: g.area).exterior)
        out.append((p, int(v)))
    return out


def polygons(mask, min_r, min_px, max_px):
    """Vector outlines (pixel coordinates, y down) of the components of a mask: (polygon, area_px)."""
    from rasterio import features
    lab, n = ndi.label(mask, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    if n == 0:
        return []
    idx = np.arange(1, n + 1)
    area = ndi.sum(mask, lab, idx)
    dist = ndi.distance_transform_edt(mask)
    rmax = ndi.maximum(dist, lab, idx)
    good = (area >= min_px) & (area <= max_px) & (rmax >= min_r)
    keep = np.zeros(n + 1, bool)
    keep[1:] = good
    lab2 = np.where(keep[lab], lab, 0).astype(np.int32)
    out = []
    for geom, v in features.shapes(lab2, mask=lab2 > 0, connectivity=4):
        p = sg.shape(geom)
        if not p.is_valid:
            p = p.buffer(0)
        if p.is_empty:
            continue
        p = sg.Polygon(p.exterior) if p.geom_type == "Polygon" else max(p.geoms, key=lambda g: g.area)
        out.append((p, float(area[int(v) - 1])))
    return out


def tidy(p, tol=1.1, rect_iou=0.84):
    """Outline simplified; a plain rectangle where the shape is one."""
    q = p.simplify(tol)
    if not q.is_valid or q.is_empty:
        q = p
    r = q.minimum_rotated_rectangle
    if r.geom_type == "Polygon" and r.area > 0 and q.area / r.area >= rect_iou:
        # the rectangle of the same area as the traced fill, on the fill's axes
        k = (q.area / r.area) ** 0.5
        c = r.centroid
        return shapely.affinity.scale(r, k, k, origin=c)
    return q


# --------------------------------------------------------------------------------------------- plates
class Plate:
    def __init__(self, layer, pid, verbose=True):
        self.layer, self.id = layer, str(pid)
        self.spec = layers()[layer]
        self.style = dict(STYLES[self.spec["style"]], **self.spec.get("style_override", {}))
        self.m = warp.MapWarp(int(pid), verbose=verbose)
        self.m.rec["image_path"] = str(RAW / f"{self.m.rec['imageId']}.jpg")
        self.corr = None  # (A 2x2, t 2) correction applied after the control-point fit, local metres
        cf = WORK / layer / f"{self.id}_corr.json"
        if cf.exists():
            d = json.loads(cf.read_text())
            self.corr = (np.array(d["A"]), np.array(d["t"]))

    def fetch(self):
        jpg = Path(self.m.rec["image_path"])
        if jpg.exists():
            return jpg
        RAW.mkdir(parents=True, exist_ok=True)
        tif = warp.fetch(f"https://images.nypl.org/index.php?id={self.m.rec['imageId']}&t=u", RAW / f"{self.m.rec['imageId']}.tif")
        im = Image.open(tif).convert("RGB")
        im.save(jpg, quality=95, subsampling=0)
        tif.unlink()
        print("fetched", self.id, self.m.rec["imageId"], im.size, flush=True)
        return jpg

    def img(self):
        return self.m.image(1)

    # pixel <-> local metres, with the correction
    def fwd(self, px):
        xy = self.m.fwd(px)
        if self.corr is not None:
            xy = xy @ self.corr[0].T + self.corr[1]
        return xy

    def _minv(self, g):
        """Ground -> pixel as the inverse of the forward fit. warp.py fits the two directions separately; with a
        spline or 2nd-order model they are not each other's inverse (3-4 m apart on plate 21 of Kings County), so
        the ground -> pixel fit is only the first guess here and the forward fit is inverted by iteration."""
        g = np.atleast_2d(g)
        px = self.m.inv(g)
        if self.m.model != "affine":
            if getattr(self, "_Jinv", None) is None:
                c = self.m.px_all[self.m.keep].mean(0)
                h = 200.0
                J = np.column_stack([(self.m.fwd(c + [h, 0]) - self.m.fwd(c - [h, 0]))[0] / (2 * h),
                                     (self.m.fwd(c + [0, h]) - self.m.fwd(c - [0, h]))[0] / (2 * h)])
                self._Jinv = np.linalg.inv(J)
            for _ in range(4):
                px = px + (g - self.m.fwd(px)) @ self._Jinv.T
        return px

    def inv(self, xy):
        xy = np.atleast_2d(xy)
        if self.corr is not None:
            xy = (xy - self.corr[1]) @ np.linalg.inv(self.corr[0]).T
        return self._minv(xy)

    def mask_local(self):
        g = self.m.rec.get("mask")
        if not g:
            return None
        p = sg.shape(g)
        p = shapely.transform(p, lambda c: np.column_stack(S.local(c[:, 0], c[:, 1])))
        return p.buffer(0)

    def mask_px(self, grow_m=0.0):
        """The Map Warper mask in the plate's pixel coordinates (it was drawn on the uncorrected fit)."""
        ml = self.mask_local()
        if ml is None:
            return None
        if grow_m:
            ml = ml.buffer(grow_m)
        parts = [sg.Polygon(self._minv(np.asarray(g.exterior.coords)[:-1])) for g in getattr(ml, "geoms", [ml]) if not g.is_empty]
        return shapely.union_all([q.buffer(0) for q in parts])

    def coverage_local(self):
        """The plate's mask on the ground with the plate's correction applied."""
        mp = self.mask_px()
        if mp is None:
            return None
        parts = [sg.Polygon(self.fwd(np.asarray(g.exterior.coords)[:-1])).buffer(0) for g in getattr(mp, "geoms", [mp])]
        return shapely.union_all(parts)

    def inside(self, shape, grow_m=15.0):
        """Pixel mask of the plate's map area: the Map Warper mask grown by grow_m, so that a building on the mask
        edge is traced whole; `trace` then keeps the buildings whose centre lies inside the mask itself."""
        from rasterio import features
        mp = self.mask_px(grow_m)
        if mp is None:
            return np.ones(shape, bool)
        return features.rasterize([(mp, 1)], out_shape=shape, dtype="uint8").astype(bool)


# --------------------------------------------------------------------------------------------- registration
def street_raster(P, shape, f, half_m=8.0):
    """Today's street centrelines (Overture, as the extents tools load them), drawn into the plate's pixel grid
    reduced by f, half_m either side."""
    from rasterio import features
    H, W = shape
    c = P.fwd(np.array([[0, 0], [W * f, 0], [W * f, H * f], [0, H * f]], float))
    box = (c[:, 0].min(), c[:, 1].min(), c[:, 0].max(), c[:, 1].max())
    names, g = S.roads()
    b = shapely.bounds(g)
    g = g[(b[:, 2] > box[0]) & (b[:, 0] < box[2]) & (b[:, 3] > box[1]) & (b[:, 1] < box[3])]
    if len(g) == 0:
        return np.zeros(shape, np.float32)
    g = shapely.segmentize(g, 25.0)
    px = [shapely.LineString(P.inv(shapely.get_coordinates(x)) / f) for x in g]
    r = half_m / (P.m.src_mpp * f)
    return features.rasterize([(x.buffer(r), 1) for x in px], out_shape=shape, dtype="uint8").astype(np.float32)


def wash_raster(img, paper, f, cool=None):
    """Share of 'wash' per reduced pixel: lightly tinted, not ink, not a strong fill - on these atlases the streets
    (peach, grey or lilac tint; blocks are left paper). Read on every second pixel."""
    H, W = img.shape[:2]
    g = f // 2
    sub = img[:H - H % f:2, :W - W % f:2]
    out = np.zeros((H // f, W // f), np.float32)
    for r0 in range(0, sub.shape[0], 512 * g):
        lab = rgb2lab(sub[r0:r0 + 512 * g])
        dL, da, db = lab[..., 0] - paper[0], lab[..., 1] - paper[1], lab[..., 2] - paper[2]
        if cool is None:
            w = (dL < -3.5) & (dL > -14) & (np.abs(da) < 7) & (db < 14)
        else:   # streets tinted lilac-grey on a greyish sheet: bluer than the paper, hardly darker
            w = (db < cool) & (dL > -14) & (np.abs(da) < 7)
        out[r0 // g:r0 // g + w.shape[0] // g] = w.reshape(w.shape[0] // g, g, w.shape[1] // g, g).mean((1, 3))
    return out


def window_shifts(P, f=4, win_m=400.0, search_m=30.0, min_q=0.4, F=None):
    """Where the plate's street wash sits best on today's streets, window by window:
    rows (u, v, du, dv, q) in full-resolution pixels (the map content at u, v belongs at u + du, v + dv)."""
    from scipy import signal
    if F is None:
        img = P.img()
        paper = paper_colour(img, P.inside(img.shape[:2]))
        F = wash_raster(img, paper, f, P.style.get("wash_cool"))
        F = ndi.gaussian_filter(F, 1.0)  # the whole sheet: what lies outside the Map Warper mask is map all the same
        P._wash = F
    R = street_raster(P, F.shape, f)
    k = P.m.src_mpp * f
    w, sr = int(win_m / k) // 2 * 2, int(round(search_m / k))
    h = w // 2
    out = []
    for cy in range(h + sr, F.shape[0] - h - sr, h):
        for cx in range(h + sr, F.shape[1] - h - sr, h):
            A = F[cy - h:cy + h, cx - h:cx + h]
            B = R[cy - h - sr:cy + h + sr, cx - h - sr:cx + h + sr]
            if A.std() < 0.05 or B.mean() < 0.04:
                continue
            c = signal.correlate(B - B.mean(), (A - A.mean()) / A.std(), mode="valid", method="fft")
            j = np.unravel_index(np.argmax(c), c.shape)
            dy, dx = j[0] - sr, j[1] - sr
            Bs = B[j[0]:j[0] + w, j[1]:j[1] + w]
            q = c[j] / (A.size * max(Bs.std(), 1e-6))   # correlation coefficient at the peak
            if q >= min_q and abs(dy) < sr - 1 and abs(dx) < sr - 1:
                # sub-pixel peak (parabola through the neighbours)
                def sub(m1, m0, p1):
                    d = m1 - 2 * m0 + p1
                    return 0.0 if d >= 0 else 0.5 * (m1 - p1) / d
                dy += sub(c[j[0] - 1, j[1]], c[j], c[j[0] + 1, j[1]])
                dx += sub(c[j[0], j[1] - 1], c[j], c[j[0], j[1] + 1])
                out.append((cx * f, cy * f, dx * f, dy * f, q))
    return np.array(out).reshape(-1, 5)


def _fit_corr(old, new, tol0=15.0):
    """Correction old -> new from window pairs: affine when at least 10 windows agree, a constant shift when at
    least 4 do. Returns (A, t, kind, median residual of the agreeing windows, their number)."""
    d = new - old
    keep = np.hypot(*(d - np.median(d, 0)).T) < tol0
    A, t, kind, res = np.eye(2), np.zeros(2), "none", None
    if keep.sum() >= 10:
        for _ in range(4):
            X = np.column_stack([old[keep], np.ones(keep.sum())])
            C = np.linalg.lstsq(X, new[keep], rcond=None)[0]
            e = np.hypot(*(np.column_stack([old, np.ones(len(old))]) @ C - new).T)
            keep2 = e < max(6.0, 2.5 * np.median(e[keep]))
            if keep2.sum() < 10 or (keep2 == keep).all():
                break
            keep = keep2
        A, t, kind, res = C[:2].T, C[2], "affine", float(np.median(e[keep]))
    elif keep.sum() >= 4:
        t, kind = d[keep].mean(0), "shift"
        res = float(np.median(np.hypot(*(d[keep] - t).T)))
    return A, t, kind, res, int(keep.sum())


def refine(layer, pid, verbose=True, min_q=None, win_m=None, init_t=None):
    """Correct a plate's control-point fit with the street match, in two passes (search 30 m, then 15 m on the
    corrected fit): an affine correction when at least 10 windows agree, a constant shift when at least 4 do,
    nothing otherwise. Writes <plate>_corr.json (replacing any earlier correction); returns a report."""
    cf = WORK / layer / f"{pid}_corr.json"
    if cf.exists():
        cf.unlink()
    if init_t is not None:   # a plate the Map Warper placed in the wrong part of town: start from `locate`'s shift
        (WORK / layer).mkdir(parents=True, exist_ok=True)
        cf.write_text(json.dumps(dict(A=np.eye(2).tolist(), t=[float(init_t[0]), float(init_t[1])])))
    P = Plate(layer, pid, verbose=False)
    q = min_q if min_q is not None else P.style.get("street_min_q", 0.4)
    win = win_m if win_m is not None else P.style.get("street_win_m", 400.0)
    rep = dict(plate=str(pid), min_q=q, win_m=win, gcps=int(P.m.keep.sum()), model=P.m.model, cv_rms=round(P.m.cv_rms, 1), mpp=round(P.m.src_mpp, 3))
    A, t = np.eye(2), (np.zeros(2) if init_t is None else np.array(init_t, float))
    if init_t is not None:
        rep["located_shift_m"] = [round(float(v)) for v in init_t]
    wash = None
    for k, search in enumerate((30.0, 15.0)):
        sh = window_shifts(P, search_m=search, min_q=q, win_m=win, F=wash)
        wash = P._wash if wash is None else wash
        if k == 0:
            rep["windows"] = len(sh)
        if len(sh) < 4:
            break
        old, new = P.fwd(sh[:, :2]), P.fwd(sh[:, :2] + sh[:, 2:4])
        d = new - old
        if k == 0:
            rep["shift_median"] = [round(float(v), 1) for v in np.median(d, 0)]
            rep["shift_abs_median"] = round(float(np.median(np.hypot(d[:, 0], d[:, 1]))), 1)
        A1, t1, kind, res, agree = _fit_corr(old, new)
        if kind == "none" or (res is not None and res > 5.0):
            break
        A, t = A1 @ A, A1 @ t + t1
        rep["kind" if k == 0 else "kind2"], rep["agree" if k == 0 else "agree2"] = kind, agree
        rep["fit_residual_m" if k == 0 else "fit_residual2_m"] = round(res, 1)
        (WORK / layer).mkdir(parents=True, exist_ok=True)
        cf.write_text(json.dumps(dict(A=A.tolist(), t=t.tolist(), report=rep)))
        P = Plate(layer, pid, verbose=False)
    rep.setdefault("kind", "none")
    if rep["kind"] != "none":   # what is left after the correction
        sh = window_shifts(P, search_m=15.0, min_q=q, win_m=win, F=wash)
        if len(sh):
            d = P.fwd(sh[:, :2] + sh[:, 2:4]) - P.fwd(sh[:, :2])
            rep["after_windows"] = len(sh)
            rep["after_abs_median"] = round(float(np.median(np.hypot(d[:, 0], d[:, 1]))), 1)
        cf.write_text(json.dumps(dict(A=A.tolist(), t=t.tolist(), report=rep)))
    if verbose:
        print(json.dumps(rep), flush=True)
    return rep


def locate(layer, pid, search_km=8.0, f=12, verbose=True, hint=None, hint_km=1.0):
    """Where a plate really lies, when its Map Warper control points put it in the wrong part of town (scale and
    bearing right, place wrong): the plate's street tint, reduced by f, is matched to today's streets over
    +- search_km. Returns the ground shift (m) of the best match and its lead over the second best."""
    from rasterio import features
    from scipy import signal
    P = Plate(layer, pid, verbose=False)
    img = P.img()
    paper = paper_colour(img, P.inside(img.shape[:2]))
    F = ndi.gaussian_filter(wash_raster(img, paper, f, P.style.get("wash_cool")), 1.0)
    k = P.m.src_mpp * f
    Sx = int(search_km * 1000 / k)
    H, W = F.shape
    c0 = P.fwd(np.array([[W * f / 2, H * f / 2]]))[0]
    names, g = S.roads()
    b = shapely.bounds(g)
    r = search_km * 1000 + max(W, H) * k
    g = g[(b[:, 2] > c0[0] - r) & (b[:, 0] < c0[0] + r) & (b[:, 3] > c0[1] - r) & (b[:, 1] < c0[1] + r)]
    g = shapely.segmentize(g, 50.0)
    px = [shapely.LineString(P.inv(shapely.get_coordinates(x)) / f + Sx) for x in g]
    R = features.rasterize([(x.buffer(max(1.0, 8.0 / k)), 1) for x in px], out_shape=(H + 2 * Sx, W + 2 * Sx), dtype="uint8").astype(np.float32)
    c = signal.correlate(R - R.mean(), (F - F.mean()) / F.std(), mode="valid", method="fft")
    if hint is not None:   # look only near an expected ground shift (m), e.g. from the plate's title
        hp = (P.inv(c0[None] + np.array(hint, float)) - P.inv(c0[None]))[0] / f + Sx
        yy, xx = np.ogrid[:c.shape[0], :c.shape[1]]
        c = np.where(np.hypot(xx - hp[0], yy - hp[1]) <= hint_km * 1000 / k, c, -np.inf)
    j = np.unravel_index(np.argmax(c), c.shape)
    best = c[j]
    c2 = c.copy()
    c2[max(0, j[0] - 15):j[0] + 16, max(0, j[1] - 15):j[1] + 16] = -np.inf
    lead = float(best / c2.max())
    dpx = np.array([(j[1] - Sx) * f, (j[0] - Sx) * f], float)
    ctr = np.array([[W * f / 2, H * f / 2]])
    t = (P.fwd(ctr + dpx) - P.fwd(ctr))[0]
    if verbose:
        print(json.dumps(dict(plate=str(pid), shift_m=[round(float(v)) for v in t], lead_over_second=round(lead, 3))), flush=True)
    return t, lead


def footprints(box_local, pad=30.0):
    """Today's footprints in a local box: (polygons in local metres, year_raw, bin)."""
    import duckdb
    x0, y0, x1, y1 = box_local
    lo, la = S.lonlat(np.array([x0 - pad, x1 + pad, x0 - pad, x1 + pad]), np.array([y0 - pad, y0 - pad, y1 + pad, y1 + pad]))
    q = (f"select bin, year_raw, geometry from read_parquet('{FOOT}') where lon between {lo.min()} and {lo.max()} "
         f"and lat between {la.min()} and {la.max()}")
    rows = duckdb.sql(q).fetchall()
    if not rows:
        return np.array([], object), np.array([]), np.array([])
    g = shapely.from_wkb([bytes(r[2]) for r in rows])
    g = shapely.transform(g, lambda c: np.column_stack(S.local(c[:, 0], c[:, 1])))
    g = shapely.make_valid(g)
    return g, np.array([r[1] or 0 for r in rows]), np.array([r[0] or 0 for r in rows])


def match(polys, box):
    """Each traced polygon against today's footprints: best IoU, centroid offset to that footprint, its recorded
    year, and the share of the traced outline lying on pre-war footprints (recorded year <= 1940 or none)."""
    fp, yr, _ = footprints(box)
    n = len(polys)
    iou = np.zeros(n)
    off = np.full((n, 2), np.nan)
    fyear = np.zeros(n, int)
    cover = np.zeros(n)
    if len(fp) == 0 or n == 0:
        return iou, off, fyear, cover
    tree = shapely.STRtree(fp)
    pa = np.asarray(polys, object)
    a, b = tree.query(pa, predicate="intersects")
    inter = shapely.area(shapely.intersection(pa[a], fp[b]))
    union = shapely.area(pa[a]) + shapely.area(fp[b]) - inter
    v = inter / np.maximum(union, 1e-9)
    pre = (yr[b] == 0) | (yr[b] <= 1940)
    np.add.at(cover, a[pre], inter[pre])
    cover = np.minimum(1.0, cover / np.maximum(shapely.area(pa), 1e-9))
    for i, j, w in zip(a, b, v):
        if w > iou[i]:
            iou[i] = w
            ci, cj = polys[i].centroid, fp[j].centroid
            off[i] = (cj.x - ci.x, cj.y - ci.y)
            fyear[i] = yr[j]
    return iou, off, fyear, cover


def trace_window(P, full, inside, paper, win, core=None):
    """Buildings of one pixel window (x0, y0, x1, y1) of a plate: [(pixel polygon, material)]; with `core`, only
    those whose centre lies in the core box (the plate is traced in overlapping tiles to keep memory small)."""
    st = P.style
    x0, y0, x1, y1 = [int(v) for v in win]
    x0, y0 = max(0, x0), max(0, y0)
    img, ins = full[y0:y1, x0:x1], inside[y0:y1, x0:x1]
    if not ins.any():
        return []
    lab_all = rgb2lab(img)
    c = classes(img, paper, st, lab_all)
    line = thin_lines(img, st["line_depth"], lab_all[..., 0])
    del lab_all
    mpp = P.m.src_mpp
    lo, hi = 0.6 * st["min_m2"] / mpp ** 2, 1.5 * st["max_m2"] / mpp ** 2
    # Only the neighbourhoods of fill are worked on (most of a county plate is empty paper): groups of fill
    # at least 3 pixels wide, grown by 30 pixels; each group is traced in its own box, restricted to itself.
    cand5 = None
    if st.get("band") and not st.get("split_by_ink"):
        # Is there an orange property band nearby? Bands are the long thin warm structures (not part of a fill
        # 13 pixels wide, 150 pixels long or more, mostly of the band hue). Where there is none, the band hue
        # is just the sheet's frame pigment (the colourists' ochre runs to orange on some sheets and some
        # buildings): read it as frame. (Deciding this pixel by pixel - band hue counts as band only within 12
        # pixels of a detected band - was tried and dropped: bands wider than 13 pixels are not detected and
        # came out as buildings. Deciding it per tile of 2400 pixels lost the orange buildings of Coney Island.)
        m5 = (c == 5) & ins
        warm = ((c == 2) & ins) | m5
        thin = warm & ~_dil(_open(warm, 13), 6)
        tl, tn = ndi.label(thin, structure=SQ3)
        band = np.zeros(c.shape, bool)
        if tn:
            n_all = np.bincount(tl.ravel(), minlength=tn + 1)
            n_5 = np.bincount(tl.ravel(), weights=m5.ravel(), minlength=tn + 1)
            isband = np.zeros(tn + 1, bool)
            for k, sl in enumerate(ndi.find_objects(tl), 1):
                if sl is not None and max(sl[0].stop - sl[0].start, sl[1].stop - sl[1].start) >= 150 and n_5[k] >= 0.5 * n_all[k]:
                    isband[k] = True
            band = isband[tl]
        # decided in cells of 500 pixels (with 100 pixels around): a cell without band pixels has no band hue
        warm_cells = False
        for cy in range(0, c.shape[0], 500):
            for cx in range(0, c.shape[1], 500):
                near = band[max(0, cy - 100):cy + 600, max(0, cx - 100):cx + 600]
                cell = (slice(cy, cy + 500), slice(cx, cx + 500))
                if int(near.sum()) < 150:
                    c[cell][c[cell] == 5] = 2
                elif not warm_cells:
                    # bands and band-hued fills together: the second frame path of `fills` is used where wide
                    # band-hued fills are a quarter or more of the wide warm fills of the tile
                    w5, w2 = int(_open(m5, 13).sum()), int(_open((c == 2) & ins, 13).sum())
                    warm_cells = True
                    if w5 > 0.25 * (w5 + w2):
                        st = dict(st, warm_path=True)
                        cand5 = _open((c == 5) & ins, st["core_frame"])
        if cand5 is not None:
            cand5 = _open((c == 5) & ins, st["core_frame"])
    fillc = (c == 2) | (c == 3) | (c == 4) | (c == 6)
    cand = _open(fillc & ins, 3)
    if cand5 is not None:
        cand |= cand5
    if not cand.any():
        return []
    rl, rn = ndi.label(_dil(cand, 30))
    found = []
    for k, sl in enumerate(ndi.find_objects(rl), 1):
        ys = slice(max(0, sl[0].start - 40), min(c.shape[0], sl[0].stop + 40))
        xs = slice(max(0, sl[1].start - 40), min(c.shape[1], sl[1].stop + 40))
        cc, ll = c[ys, xs], line[ys, xs]
        ii = ins[ys, xs] & (rl[ys, xs] == k)
        if st.get("split_by_ink"):
            lab, mat = fills_rows(cc, ll, st, ii)
            part = [(p, mat[v - 1]) for p, v in label_polygons(lab, lo, hi)]
        else:
            f = fills(cc, ll, st, ii)
            part = [(p, name) for name in ("frame", "brick") for p, apx in polygons(f[name], 0.0, lo, hi)]
        found += [(shapely.affinity.translate(p, xs.start, ys.start), name) for p, name in part]
    out = []
    for p, name in found:
        q = shapely.affinity.translate(tidy(p), x0, y0)
        if core is not None:
            cx, cy = q.centroid.x, q.centroid.y
            if not (core[0] <= cx < core[2] and core[1] <= cy < core[3]):
                continue
        out.append((q, name))
    return out


def trace(layer, pid, save=True, verbose=True, window=None, tile=2400, margin=180):
    """Trace one plate (or, for checking, a pixel window x0, y0, x1, y1 of it)."""
    t0 = time.time()
    P = Plate(layer, pid, verbose=verbose)
    st = P.style
    full = P.img()
    inside = P.inside(full.shape[:2])
    paper = paper_colour(full, inside)
    if window is not None:
        found = trace_window(P, full, inside, paper, window)
    else:
        found = []
        H, W = full.shape[:2]
        for ty in range(0, H, tile):
            for tx in range(0, W, tile):
                core = (tx, ty, min(W, tx + tile), min(H, ty + tile))
                found += trace_window(P, full, inside, paper, (tx - margin, ty - margin, core[2] + margin, core[3] + margin), core)
    out = []
    mp = P.mask_px()
    if mp is not None and window is None:
        cen = shapely.points([(q.centroid.x, q.centroid.y) for q, _ in found]) if found else []
        found = [f for f, k in zip(found, shapely.contains(mp, cen))if k] if found else []
    for q, name in found:
        g = sg.Polygon(P.fwd(np.asarray(q.exterior.coords)))
        if not g.is_valid:
            g = g.buffer(0)
        if g.is_empty or g.geom_type != "Polygon" or not (st["min_m2"] <= g.area <= st["max_m2"]):
            continue
        out.append(dict(material=name, px=wkb.dumps(q), geom=wkb.dumps(g), area=g.area))
    if window is None:
        stats = _stats(P, out, paper)
    else:
        polys = [wkb.loads(o["geom"]) for o in out]
        iou, off, fy, cov = match(polys, shapely.MultiPolygon(polys).bounds if polys else (0, 0, 1, 1))
        for o, i in zip(out, iou):
            o["iou"] = float(i)
        stats = dict(plate=P.id, n=len(out), coincide=int((iou > 0.5).sum()))
    cf = WORK / layer / f"{P.id}_corr.json"
    if cf.exists():
        stats["street"] = json.loads(cf.read_text()).get("report")
    if verbose:
        print(json.dumps(stats), "%.0fs" % (time.time() - t0), flush=True)
    if save and window is None:
        (WORK / layer).mkdir(parents=True, exist_ok=True)
        ml = P.coverage_local()
        pickle.dump(dict(stats=stats, items=out, mask=wkb.dumps(ml) if ml is not None else None), open(WORK / layer / f"{P.id}.pkl", "wb"))
    return P, out, stats, None


def _stats(P, out, paper=None):
    polys = [wkb.loads(o["geom"]) for o in out]
    ml = P.mask_local()
    box = ml.bounds if ml is not None else shapely.MultiPolygon(polys).bounds
    iou, off, fy, cov = match(polys, box)
    for o, i, d, y, cv in zip(out, iou, off, fy, cov):
        o["iou"], o["off"], o["fyear"], o["cover"] = float(i), (float(d[0]), float(d[1])), int(y), float(cv)
    hit = iou > 0.5
    stats = dict(plate=P.id, image=P.m.rec["imageId"], name=P.m.rec["name"][:90], gcps=int(P.m.keep.sum()), model=P.m.model,
                 cv_rms=round(P.m.cv_rms, 1), mpp=round(P.m.src_mpp, 3), n=len(out),
                 frame=sum(o["material"] == "frame" for o in out), brick=sum(o["material"] == "brick" for o in out),
                 stone=sum(o["material"] == "stone" for o in out),
                 coincide=int(hit.sum()), share=round(float(hit.mean()), 3) if len(out) else 0.0, corrected=P.corr is not None)
    if paper is not None:
        stats["paper"] = [float(v) for v in paper]
    if hit.sum():
        d = off[hit]
        stats["off_median_vec"] = [round(float(v), 2) for v in np.median(d, 0)]
        stats["off_median_m"] = round(float(np.median(np.hypot(d[:, 0], d[:, 1]))), 2)
    return stats


def regeo(layer, pid, verbose=True):
    """Recompute the ground geometry and the match against today's footprints of a traced plate with the plate's
    current correction (after refine / refine_buildings); the tracing itself (pixel outlines) is not redone."""
    f = WORK / layer / f"{pid}.pkl"
    d = pickle.load(open(f, "rb"))
    P = Plate(layer, pid, verbose=False)
    st = P.style
    out = []
    for o in d["items"]:
        g = sg.Polygon(P.fwd(np.asarray(wkb.loads(o["px"]).exterior.coords)))
        if not g.is_valid:
            g = g.buffer(0)
        if g.is_empty or g.geom_type != "Polygon" or not (st["min_m2"] <= g.area <= st["max_m2"]):
            continue
        out.append(dict(material=o["material"], px=o["px"], geom=wkb.dumps(g), area=g.area))
        if "yellow" in o:
            out[-1]["yellow"] = o["yellow"]
    stats = _stats(P, out, d["stats"].get("paper"))
    for k in ("street", "bld"):
        if k in d["stats"]:
            stats[k] = d["stats"][k]
    cf = WORK / layer / f"{pid}_corr.json"
    if cf.exists():
        r = json.loads(cf.read_text())
        stats["street"] = r.get("report", stats.get("street"))
        if r.get("bld"):
            stats["bld"] = r["bld"]
    if verbose:
        print(json.dumps(stats), flush=True)
    ml = P.coverage_local()
    pickle.dump(dict(stats=stats, items=out, mask=wkb.dumps(ml) if ml is not None else None), open(f, "wb"))
    return stats


def refine_buildings(layer, pid, cell=0.5, win_m=240.0, search_m=6.0, min_q=0.25, verbose=True):
    """Fine registration of a city plate on the buildings that still stand: the traced building mask is matched to
    today's footprints of pre-war buildings (recorded year <= 1940, or none), window
    by window (filled masks, so the rhythm of equal row houses cannot alias; the row ends, yards and corner
    buildings give the position). The consensus of the window shifts corrects the plate (affine with >= 10
    windows, constant shift with >= 3), on top of any street correction. Then regeo."""
    from rasterio import features
    from affine import Affine
    from scipy import signal
    d = pickle.load(open(WORK / layer / f"{pid}.pkl", "rb"))
    P = Plate(layer, pid, verbose=False)
    polys = [sg.Polygon(P.fwd(np.asarray(wkb.loads(o["px"]).exterior.coords))).buffer(0) for o in d["items"]]
    polys = [q for q in polys if not q.is_empty]
    rep = dict(plate=str(pid), n=len(polys))
    if len(polys) < 50:
        rep["kind"] = "none"
        return rep
    b = shapely.total_bounds(np.asarray(polys, object))
    x0, y0, x1, y1 = np.floor(b[0]) - 20, np.floor(b[1]) - 20, np.ceil(b[2]) + 20, np.ceil(b[3]) + 20
    fp, yr, _ = footprints((x0, y0, x1, y1), pad=0)
    old = (yr == 0) | (yr <= 1940)   # the recorded years are heaps (1900, 1910, 1920 ...): only post-war is surely new
    shp = (int((y1 - y0) / cell), int((x1 - x0) / cell))
    tr = Affine(cell, 0, x0, 0, -cell, y1)
    A = features.rasterize([(q, 1) for q in polys], out_shape=shp, transform=tr, dtype="uint8").astype(np.float32)
    B = features.rasterize([(q, 1) for q in fp[old]], out_shape=shp, transform=tr, dtype="uint8").astype(np.float32)
    w, sr = int(win_m / cell) // 2 * 2, int(round(search_m / cell))
    h = w // 2
    rows = []
    for cy in range(h + sr, shp[0] - h - sr, h):
        for cx in range(h + sr, shp[1] - h - sr, h):
            a = A[cy - h:cy + h, cx - h:cx + h]
            bb = B[cy - h - sr:cy + h + sr, cx - h - sr:cx + h + sr]
            if a.mean() < 0.04 or bb.mean() < 0.04:
                continue
            c = signal.correlate(bb - bb.mean(), (a - a.mean()) / a.std(), mode="valid", method="fft")
            j = np.unravel_index(np.argmax(c), c.shape)
            bs = bb[j[0]:j[0] + w, j[1]:j[1] + w]
            q = c[j] / (a.size * max(bs.std(), 1e-6))
            if q < min_q or not (0 < j[0] < 2 * sr and 0 < j[1] < 2 * sr):
                continue
            def sub(m1, m0, p1):
                dd = m1 - 2 * m0 + p1
                return 0.0 if dd >= 0 else 0.5 * (m1 - p1) / dd
            dy = j[0] - sr + sub(c[j[0] - 1, j[1]], c[j], c[j[0] + 1, j[1]])
            dx = j[1] - sr + sub(c[j[0], j[1] - 1], c[j], c[j[0], j[1] + 1])
            rows.append((x0 + cx * cell, y1 - cy * cell, dx * cell, -dy * cell, q))
    rows = np.array(rows).reshape(-1, 5)
    rep["windows"] = len(rows)
    A1, t1, kind = np.eye(2), np.zeros(2), "none"
    if len(rows) >= 3:
        o, dlt = rows[:, :2], rows[:, 2:4]
        rep["shift_median"] = [round(float(v), 2) for v in np.median(dlt, 0)]
        keep = np.hypot(*(dlt - np.median(dlt, 0)).T) < 3.0
        if keep.sum() >= 10:
            for _ in range(3):
                X = np.column_stack([o[keep], np.ones(keep.sum())])
                C = np.linalg.lstsq(X, (o + dlt)[keep], rcond=None)[0]
                e = np.hypot(*(np.column_stack([o, np.ones(len(o))]) @ C - (o + dlt)).T)
                k2 = e < max(1.5, 2.5 * np.median(e[keep]))
                if k2.sum() < 10 or (k2 == keep).all():
                    break
                keep = k2
            A1, t1, kind = C[:2].T, C[2], "affine"
            rep["fit_residual_m"] = round(float(np.median(e[keep])), 2)
        elif keep.sum() >= 3:
            t1, kind = dlt[keep].mean(0), "shift"
            rep["fit_residual_m"] = round(float(np.median(np.hypot(*(dlt[keep] - t1).T))), 2)
        rep["agree"] = int(keep.sum())
    rep["kind"] = kind
    if kind != "none":
        cf = WORK / layer / f"{pid}_corr.json"
        prev = json.loads(cf.read_text()) if cf.exists() else dict(A=np.eye(2).tolist(), t=[0.0, 0.0])
        A0, t0 = np.array(prev["A"]), np.array(prev["t"])
        prev.update(A=(A1 @ A0).tolist(), t=(A1 @ t0 + t1).tolist(), bld=rep)
        cf.write_text(json.dumps(prev))
    if verbose:
        print(json.dumps(rep), flush=True)
    regeo(layer, pid, verbose=verbose)
    return rep


def score_frames(layer, pid, verbose=True):
    """Yellow strength of every traced frame outline, from the scan: median over the outline's pixels of
    (b - b_paper) - 3 (a - a_paper). The Bronx atlas washes some lots in a pale olive that passes the pixel
    threshold for the frame yellow; a building's yellow is stronger and greener (measured on plate 5: buildings
    11-21, washed lots 5.5-9). Stored on the items as `yellow`; `export` applies the layer's `frame_yellow_min`."""
    from rasterio import features
    f = WORK / layer / f"{pid}.pkl"
    d = pickle.load(open(f, "rb"))
    P = Plate(layer, pid, verbose=False)
    img = P.img()
    paper = paper_colour(img, P.inside(img.shape[:2]))
    vals = []
    for o in d["items"]:
        if o["material"] != "frame":
            continue
        q = wkb.loads(o["px"])
        x0, y0, x1, y1 = [int(v) for v in q.bounds]
        x0, y0 = max(0, x0 - 1), max(0, y0 - 1)
        crop = img[y0:y1 + 2, x0:x1 + 2]
        m = features.rasterize([(shapely.affinity.translate(q, -x0, -y0), 1)], out_shape=crop.shape[:2], dtype="uint8").astype(bool)
        if m.sum() < 10:
            continue
        lab = rgb2lab(crop)[m]
        lab = lab[lab[:, 0] > 55]                      # not the figures written on it
        if len(lab) < 10:
            continue
        o["yellow"] = float(np.median((lab[:, 2] - paper[2]) - 3.0 * (lab[:, 1] - paper[1])))
        vals.append((o["yellow"], o["area"]))
    pickle.dump(d, open(f, "wb"))
    v = np.array(vals).reshape(-1, 2)
    if verbose and len(v):
        print(pid, "frame", len(v), "yellow p5/25/50/75", np.round(np.percentile(v[:, 0], [5, 25, 50, 75]), 1),
              "| < 8:", int((v[:, 0] < 8).sum()), "8-10:", int(((v[:, 0] >= 8) & (v[:, 0] < 10)).sum()), "10-12:", int(((v[:, 0] >= 10) & (v[:, 0] < 12)).sum()),
              "| area > 600 m2:", int((v[:, 1] > 600).sum()), "of them < 10:", int(((v[:, 1] > 600) & (v[:, 0] < 10)).sum()), flush=True)


# --------------------------------------------------------------------------------------------- export
def _ll(geom, nd=6):
    return shapely.transform(geom, lambda c: np.round(np.column_stack(S.lonlat(c[:, 0], c[:, 1])), nd))


def _written(g):
    """A ground polygon as it will be written (WGS84, 6 decimals) and that written shape back in local metres;
    rounding can make a ragged outline cross itself, so validity and area are checked on what is written."""
    for _ in range(3):
        ll = _ll(g)
        back = shapely.transform(ll, lambda c: np.column_stack(S.local(c[:, 0], c[:, 1])))
        if back.is_valid and ll.is_valid and back.geom_type == "Polygon" and not back.is_empty:
            return ll, back
        g = back.buffer(0)
        if g.geom_type == "MultiPolygon":
            g = max(g.geoms, key=lambda q: q.area)
        if g.is_empty or g.geom_type != "Polygon":
            return None, None
        g = sg.Polygon(g.exterior)
    return None, None


def export(layer, max_off=8.0):
    """Merge the traced plates of a layer -> data/manual/atlas/<layer>.geojson, <layer>_coverage.geojson (one
    feature per plate read) and <layer>_stats.json. A plate whose standing buildings sit more than max_off metres
    (median) from their footprints is left out. Where the masks of two plates overlap, a building traced on both
    is kept once (from the plate listed first)."""
    spec = layers()[layer]
    feats, cov, rep = [], [], []
    acc = []                                                  # accepted polygons (local metres)
    mx = dict(STYLES[spec["style"]], **spec.get("style_override", {}))["max_m2"]
    # optional clip of the layer: north of a line (two lon / lat points, west then east) and outside the
    # coverage of other layers of the same atlas (so that no building is in two layers)
    clip = None
    if spec.get("clip"):
        c_ = spec["clip"]
        clip = sg.box(-1e7, -1e7, 1e7, 1e7)
        if c_.get("north_of"):
            a_, b_ = [np.array(S.local(*pt)) for pt in c_["north_of"]]
            u_ = (b_ - a_) / np.hypot(*(b_ - a_))
            n_ = np.array([-u_[1], u_[0]])
            clip = sg.Polygon([a_ - 2e4 * u_, b_ + 2e4 * u_, b_ + 2e4 * u_ + 4e4 * n_, a_ - 2e4 * u_ + 4e4 * n_])
        for other in c_.get("outside_layers", []):
            oc = json.loads((OUT / f"{other}_coverage.geojson").read_text())
            og = [shapely.transform(sg.shape(f_["geometry"]), lambda c: np.column_stack(S.local(c[:, 0], c[:, 1]))) for f_ in oc["features"]]
            clip = clip.difference(shapely.union_all(og).buffer(0))
    for pl in spec["plates"]:
        f = WORK / layer / f"{pl['id']}.pkl"
        if pl.get("skip"):
            rep.append(dict(plate=str(pl["id"]), sheet=pl["sheet"], status="left out: " + pl["skip"]))
            continue
        if not f.exists():
            rep.append(dict(plate=str(pl["id"]), sheet=pl["sheet"], status="not traced"))
            continue
        d = pickle.load(open(f, "rb"))
        st = dict(d["stats"], sheet=pl["sheet"])
        if st.get("coincide", 0) >= 5 and st.get("off_median_m", 0) > max_off:
            st["status"] = "rejected: standing buildings %.1f m from their footprints" % st["off_median_m"]
            rep.append(st)
            continue
        polys = [wkb.loads(o["geom"]) for o in d["items"]]
        keep = np.ones(len(polys), bool)
        if clip is not None and polys:
            keep &= shapely.contains(clip, shapely.centroid(np.asarray(polys, object)))
            st["clipped"] = int((~keep).sum())
        if acc and polys:
            tree = shapely.STRtree(acc)
            i, j = tree.query(polys, predicate="intersects")
            if len(i):
                inter = shapely.area(shapely.intersection(np.asarray(polys, object)[i], np.asarray(acc, object)[j]))
                small = np.minimum(shapely.area(np.asarray(polys, object)[i]), shapely.area(np.asarray(acc, object)[j]))
                keep[i[inter > 0.3 * small]] = False
        # grey ("stone") outlines: bold block numbers and street lettering print in the same grey and come out as
        # small ragged pieces; a stone building is kept only if it is 80 m2 or more and fills 60 % of its rectangle
        # ... and, where the layer sets them (`stone_min_m2`, `stone_min_width_m`, `stone_max_aspect`), is large,
        # wide and compact enough not to be the grey strip of a row's stone fronts or a grey line along a kerb.
        # Pale blue ("iron") outlines are gasholders when round - about as long as wide, filling 60-90 % of their
        # rectangle (a circle fills 79 %), 250 m2 or more; every other blue outline is water between piers.
        lettering, water = 0, 0
        for k, (o, g) in enumerate(zip(d["items"], polys)):
            if not keep[k] or o["material"] not in ("stone", "iron"):
                continue
            r_ = g.minimum_rotated_rectangle
            xy_ = np.asarray(r_.exterior.coords)
            e1_, e2_ = np.hypot(*(xy_[1] - xy_[0])), np.hypot(*(xy_[2] - xy_[1]))
            w_, l_ = min(e1_, e2_), max(e1_, e2_)
            fr_ = g.area / max(r_.area, 1e-9)
            if o["material"] == "stone" and (g.area < spec.get("stone_min_m2", 80.0) or fr_ < 0.6 or w_ < spec.get("stone_min_width_m", 0.0)
                                             or l_ >= spec.get("stone_max_aspect", 1e9) * w_):
                keep[k] = False
                lettering += 1
            elif o["material"] == "iron" and not (g.area >= 250.0 and l_ <= 1.3 * w_ and 0.6 <= fr_ <= 0.9):
                keep[k] = False
                water += 1
        st["lettering_dropped"], st["water_dropped"] = lettering, water
        # county plates: pieces of carmine property band read as brick are ragged or long; a brick building is
        # kept only if it is 50 m2 or more and fills 75 % of its rectangle
        # ... and pieces of orange band read as frame are long and narrow or hook-shaped: a frame outline under
        # 5 m wide and 4.5 times as long, or one under 400 m2 filling less than 45 % of its rectangle, is dropped
        bands = 0
        if spec["style"] == "robinson_300ft":
            for k, (o, g) in enumerate(zip(d["items"], polys)):
                if not keep[k]:
                    continue
                r = g.minimum_rotated_rectangle
                if o["material"] == "brick":
                    bad = g.area < 50.0 or g.area < 0.75 * r.area
                else:
                    xy = np.asarray(r.exterior.coords)
                    e1, e2 = np.hypot(*(xy[1] - xy[0])), np.hypot(*(xy[2] - xy[1]))
                    w, l = min(e1, e2), max(e1, e2)
                    bad = (w < 5.0 and l >= 4.5 * w) or (g.area < 400.0 and g.area < 0.45 * r.area)
                if bad:
                    keep[k] = False
                    bands += 1
        st["band_pieces_dropped"] = bands
        # frame outlines of weak yellow (score_frames): washed lots, stains. The scores of a plate fall in two
        # groups with a gap at 8-10; the cut is 9.5, or 8 on a plate whose buildings are pale (median under 13).
        washed = 0
        ys = np.array([o.get("yellow", np.nan) if o["material"] == "frame" else np.nan for o in d["items"]])
        if spec.get("frame_yellow") and np.isfinite(ys).any():
            hi = ys[np.isfinite(ys) & (ys >= 8)]
            cut = 8.0 if (len(hi) and np.median(hi) < 13) else 9.5
            for k in np.flatnonzero(np.isfinite(ys) & (ys < cut) & keep):
                keep[k] = False
                washed += 1
            st["yellow_cut"] = cut
        st["washed_dropped"] = washed
        # two outlines of one plate on one spot (a rectangle fitted over its neighbour): the larger stays
        kk = np.flatnonzero(keep)
        if len(kk) > 1:
            pk = np.asarray(polys, object)[kk]
            i, j = shapely.STRtree(pk).query(pk, predicate="intersects")
            m = i < j
            i, j = i[m], j[m]
            ai, aj = shapely.area(pk[i]), shapely.area(pk[j])
            hit = shapely.area(shapely.intersection(pk[i], pk[j])) > 0.3 * np.minimum(ai, aj)
            keep[kk[np.where(ai[hit] < aj[hit], i[hit], j[hit])]] = False
        n0 = len(feats)
        for k, (o, g) in enumerate(zip(d["items"], polys)):
            if not keep[k]:
                continue
            ll, g = _written(g.simplify(0.25))
            if g is None or not (15.0 <= g.area <= mx):
                continue
            acc.append(g)
            feats.append(dict(type="Feature", properties=dict(
                id=f"{spec['source']}_{pl['sheet']}_{k}", map_year=spec["map_year"],
                material="" if o["material"] == "iron" else o["material"], kind="gasholder" if o["material"] == "iron" else "building",
                source=spec["source"], sheet=pl["sheet"], plate=int(pl["id"]), area_m2=round(g.area, 1),
                on_today=bool(o.get("iou", 0) > 0.5), today_cover=round(o.get("cover", 0.0), 2)), geometry=sg.mapping(ll)))
        st["exported"], st["duplicates_dropped"], st["status"] = len(feats) - n0, int((~keep).sum()) - lettering - water - washed - bands - st.get("clipped", 0), "ok"
        for m_ in ("frame", "brick", "stone"):
            st[m_] = sum(f["properties"]["material"] == m_ for f in feats[n0:])
        st["coincide"] = sum(f["properties"]["on_today"] for f in feats[n0:])
        st["share"] = round(st["coincide"] / max(len(feats) - n0, 1), 3)
        rep.append(st)
        if d.get("mask"):
            m = wkb.loads(d["mask"]).simplify(0.5)
            if clip is not None:
                m = m.intersection(clip)
                if m.is_empty:
                    continue
                if m.geom_type not in ("Polygon", "MultiPolygon"):
                    m = shapely.union_all([q for q in m.geoms if q.geom_type in ("Polygon", "MultiPolygon")])
            cov.append(dict(type="Feature", properties=dict(
                layer=layer, map_year=spec["map_year"], source=spec["source"], sheet=pl["sheet"], plate=int(pl["id"]),
                buildings=len(feats) - n0, registration_m=st.get("off_median_m"), coincide_share=st.get("share"),
                street_match_left_m=(st.get("street") or {}).get("after_abs_median"),
                building_match_residual_m=(st.get("bld") or {}).get("fit_residual_m"),
                registration=" + ".join(
                    [n_ for n_, k_ in (("street match", "street"), ("building match", "bld")) if (st.get(k_) or {}).get("kind", "none") != "none"])
                or "control points only, not checked"),
                geometry=sg.mapping(_ll(m))))
    crs = {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}
    OUT.mkdir(parents=True, exist_ok=True)
    def put(name, text):                                      # written whole or not at all (a rebuild may be reading)
        tmp = OUT / (name + ".tmp")
        tmp.write_text(text)
        os.replace(tmp, OUT / name)
    put(f"{layer}.geojson", json.dumps(dict(type="FeatureCollection", name=layer, crs=crs, features=feats), separators=(",", ":")))
    put(f"{layer}_coverage.geojson", json.dumps(dict(type="FeatureCollection", name=layer + "_coverage", crs=crs, features=cov), separators=(",", ":")))
    # checks on the written layer
    g = np.asarray(acc, object)
    area = shapely.area(g) if len(g) else np.array([])
    union = shapely.union_all([shapely.transform(sg.shape(c["geometry"]), lambda q: np.column_stack(S.local(q[:, 0], q[:, 1]))) for c in cov]).buffer(0) if cov else None
    inside = shapely.contains(union.buffer(1.0), shapely.centroid(g)) if (union is not None and len(g)) else np.array([])
    tot = dict(layer=layer, plates=len(cov), buildings=len(feats),
               frame=sum(f["properties"]["material"] == "frame" for f in feats),
               brick=sum(f["properties"]["material"] == "brick" for f in feats),
               stone=sum(f["properties"]["material"] == "stone" for f in feats),
               gasholders=sum(f["properties"]["kind"] == "gasholder" for f in feats),
               on_today=sum(f["properties"]["on_today"] for f in feats),
               invalid=int((~shapely.is_valid(g)).sum()) if len(g) else 0,
               area_out_of_range=int(((area < 15) | (area > mx)).sum()), outside_coverage=int((~inside).sum()),
               coverage_km2=round(union.area / 1e6, 2) if union is not None else 0)
    put(f"{layer}_stats.json", json.dumps(dict(total=tot, plates=rep), indent=1))
    print(json.dumps(tot))
    for r in rep:
        print(r.get("sheet"), r.get("plate"), r.get("status"), "n", r.get("n"), "exp", r.get("exported"), "coinc", r.get("coincide"), r.get("share"),
              "off", r.get("off_median_m"), "| street", (r.get("street") or {}).get("kind"), (r.get("street") or {}).get("agree"),
              (r.get("street") or {}).get("shift_abs_median"), (r.get("street") or {}).get("after_abs_median"), "| bld", (r.get("bld") or {}).get("kind"),
              (r.get("bld") or {}).get("shift_median"), (r.get("bld") or {}).get("fit_residual_m"))


def readme_tables():
    """Fill the per-plate tables of README.md (between <!-- TABLE layer --> and <!-- /TABLE -->) from the
    <layer>_stats.json files written by export."""
    f = OUT / "README.md"
    txt = f.read_text()
    for layer in layers():
        sf = OUT / f"{layer}_stats.json"
        a, b = f"<!-- TABLE {layer} -->", f"<!-- /TABLE {layer} -->"
        if not sf.exists() or a not in txt:
            continue
        st = json.loads(sf.read_text())
        rows = ["| sheet | Map Warper id | NYPL image | control points (fit, CV rms m) | m / px | street match: windows agreeing, shift found m, left m | "
                "building match: windows, residual m | buildings (frame / brick / stone) | on a standing footprint (IoU > 0.5) | their median offset m | status |",
                "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in st["plates"]:
            sr, br = r.get("street") or {}, r.get("bld") or {}
            street = "none" if sr.get("kind", "none") == "none" else f"{sr.get('kind')}: {sr.get('agree2', sr.get('agree'))}, {sr.get('shift_abs_median')}, {sr.get('after_abs_median')}"
            bld = "none" if br.get("kind", "none") == "none" else f"{br.get('kind')}: {br.get('agree')}, {br.get('fit_residual_m')}"
            n = r.get("exported", r.get("n", 0)) or 0
            rows.append(f"| {r.get('sheet')} | {r.get('plate')} | {r.get('image', '')} | {r.get('gcps', '')} ({r.get('model', '')}, {r.get('cv_rms', '')}) | {r.get('mpp', '')} | "
                        f"{street} | {bld} | {n} ({r.get('frame', 0)} / {r.get('brick', 0)} / {r.get('stone', 0)}) | "
                        f"{r.get('coincide', 0)} ({100 * (r.get('share') or 0):.0f} %) | {r.get('off_median_m', '')} | {r.get('status')} |")
        t = st["total"]
        rows.append(f"| **all** | | | | | | | **{t['buildings']}** ({t['frame']} / {t['brick']} / {t['stone']}) | {t['on_today']} ({100 * t['on_today'] / max(t['buildings'], 1):.0f} %) | | "
                    f"{t['plates']} plates, {t['coverage_km2']} km2 |")
        i, j = txt.index(a) + len(a), txt.index(b)
        txt = txt[:i] + "\n" + "\n".join(rows) + "\n" + txt[j:]
    f.write_text(txt)
    print("README tables written")


# --------------------------------------------------------------------------------------------- pictures
def overlay(layer, pid, cx, cy, size_m, out_png, px=False, scale=3, final=False):
    """Plate crop with outlines and today's footprints. final=True draws the exported layer (what the pipeline
    gets, after the export's filters) instead of tracing the window afresh."""
    P = Plate(layer, pid, verbose=False)
    img = P.img()
    if not px:
        u, v = P.inv(np.array([[cx, cy]]))[0]
    else:
        u, v = cx, cy
    h = size_m / P.m.src_mpp / 2
    x0, y0, x1, y1 = int(max(0, u - h)), int(max(0, v - h)), int(min(img.shape[1], u + h)), int(min(img.shape[0], v + h))
    if final:
        fc = json.loads((OUT / f"{layer}.geojson").read_text())
        items = []
        for ft in fc["features"]:
            if ft["properties"]["plate"] != int(pid):
                continue
            c_ = np.asarray(ft["geometry"]["coordinates"][0])
            q = sg.Polygon(P.inv(np.column_stack(S.local(c_[:, 0], c_[:, 1]))))
            if q.bounds[2] < x0 or q.bounds[0] > x1 or q.bounds[3] < y0 or q.bounds[1] > y1:
                continue
            items.append(dict(material=ft["properties"]["material"], px=wkb.dumps(q), iou=1.0 if ft["properties"]["on_today"] else 0.0))
        print("exported outlines in the window:", len(items))
    else:
        P, items, stats, c = trace(layer, pid, save=False, verbose=False, window=(x0 - 60, y0 - 60, x1 + 60, y1 + 60))
        print(json.dumps(stats))
    im = Image.fromarray(img[y0:y1, x0:x1]).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.LANCZOS)
    d = ImageDraw.Draw(im, "RGBA")
    corners = P.fwd(np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], float))
    box = (corners[:, 0].min(), corners[:, 1].min(), corners[:, 0].max(), corners[:, 1].max())
    fp, yr, _ = footprints(box, pad=10)
    for g in fp:
        for poly in getattr(g, "geoms", [g]):
            if poly.geom_type != "Polygon":
                continue
            q = P.inv(np.asarray(poly.exterior.coords))
            d.line([((a - x0) * scale, (b - y0) * scale) for a, b in q], fill=(0, 170, 255, 255), width=1)
    for o in items:
        q = np.asarray(wkb.loads(o["px"]).exterior.coords)
        col = {"frame": (255, 0, 0, 255), "brick": (200, 0, 200, 255), "stone": (0, 0, 160, 255)}[o["material"]]
        if o["iou"] > 0.5:
            col = (0, 150, 0, 255)
        d.line([((a - x0) * scale, (b - y0) * scale) for a, b in q], fill=col, width=2)
    im.save(out_png)
    print(out_png, im.size, "box local %.0f,%.0f,%.0f,%.0f" % box)


def colours(layer, pid, box, out_png, scale=2):
    P = Plate(layer, pid)
    img = P.img()
    x0, y0, x1, y1 = box
    crop = img[y0:y1, x0:x1]
    paper = paper_colour(img, P.inside(img.shape[:2]))
    c = classes(crop, paper, P.style)
    o = crop.copy()
    o[c == 2] = (0, 0, 255); o[c == 3] = (0, 200, 0); o[c == 5] = (255, 0, 255); o[c == 1] = (0, 0, 0)
    Image.fromarray(o).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.NEAREST).save(out_png)
    print("paper", paper, out_png)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "fetch":
        for pid in (a[2:] or [p["id"] for p in layers()[a[1]]["plates"]]):
            Plate(a[1], pid, verbose=False).fetch()
    elif a[0] == "refine":
        # optional: --q 0.25 --win 300 (a looser match for plates where the standard one finds too few windows)
        kw = {}
        if "--q" in a:
            kw["min_q"] = float(a[a.index("--q") + 1])
        if "--win" in a:
            kw["win_m"] = float(a[a.index("--win") + 1])
        ids = [v for i, v in enumerate(a[2:], 2) if v.isdigit() and not a[i - 1].startswith("--")]
        for pid in (ids or [p["id"] for p in layers()[a[1]]["plates"]]):
            try:
                if "--locate" in a:   # first find the plate (see locate); --hint dx,dy in metres
                    hint = [float(v) for v in a[a.index("--hint") + 1].split(",")] if "--hint" in a else None
                    t0, lead = locate(a[1], pid, hint=hint)
                    kw["init_t"] = t0
                refine(a[1], pid, **kw)
            except Exception as e:  # noqa
                print(json.dumps(dict(plate=str(pid), error=str(e))), flush=True)
    elif a[0] == "refine_buildings":
        for pid in (a[2:] or [p["id"] for p in layers()[a[1]]["plates"]]):
            refine_buildings(a[1], pid)
    elif a[0] == "regeo":
        for pid in (a[2:] or [p["id"] for p in layers()[a[1]]["plates"]]):
            regeo(a[1], pid)
    elif a[0] == "score_frames":
        for pid in (a[2:] or [p["id"] for p in layers()[a[1]]["plates"]]):
            score_frames(a[1], pid)
    elif a[0] == "export":
        export(a[1])
    elif a[0] == "readme":
        readme_tables()
    elif a[0] == "trace":
        for pid in (a[2:] or [p["id"] for p in layers()[a[1]]["plates"]]):
            trace(a[1], pid)
    elif a[0] == "overlay":
        cx, cy = [float(v) for v in a[3].split(",")]
        sc = int(a[a.index("--scale") + 1]) if "--scale" in a else 3
        overlay(a[1], a[2], cx, cy, float(a[4]), a[5], px="--px" in a, scale=sc, final="--final" in a)
    elif a[0] == "colours":
        colours(a[1], a[2], [int(v) for v in a[3].split(",")], a[4])
