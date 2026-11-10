"""USGS 15-minute sheets of 1888-1901 -> land / water / marsh per sheet, registered on the soil survey.
The method is the city layer's (data/manual/natural/tools/usgs_sheets.py), with six changes:
  * blue ink by chromaticity away from black line work instead of B - R, and a tint test (see one());
  * no paper-white rule here (moved to the assembly);
  * the labels come from thirteen soil survey areas (the eight counties and the five boroughs);
  * every sheet is written as its own raster (sheet pixels, shift folded into the transform) instead of one mosaic;
  * registration by area agreement instead of shoreline edges (see register());
  * a sheet with too few labelled cells takes a discriminant pooled from the sheets that have enough (the city
    layer used a fixed rule there).
It is also written to stay under 1 GB (features are computed in strips and kept in a float16 scratch file): the
build machine is shared.

Per sheet (own pixel grid, about 5.3 m):
 1. wet = dense blue line work (water lining, marsh ruling) or a blue tint, thin lines removed; blue is measured by
    chromaticity against the paper's, away from black line work.  Blank paper (open water far from shore has no
    lining) is left as "land" here; the assembly decides whether it is land or open water;
 2. registration: the sheet is shifted so that its wet mask agrees best with the soil survey's wet set near the
    survey's upland boundary;
 3. marsh against water inside wet: a linear discriminant on print texture (mean tint, fine and coarse texture,
    ink density, ruling coherence), trained on cells whose answer the soil survey gives (open water today -> water;
    tidal-marsh soils and "organic substratum" fill -> marsh).
outputs: data/interim/natural_counties/sheet_<source id>.tif (0 land, 1 water, 2 marsh, 3 thin blue line, 255 off sheet),
         sheet_<source id>.json (shift, agreement, discriminant accuracy), samples_<source id>.npz (training samples)
usage: python sheets.py [source id ...]      (no argument: all sheets, in the order of common.SHEETS; the coastal
       sheets come first because the inland ones pool their samples)
"""
import glob
import json
import os
import sys

import geopandas as gpd
import numpy as np
import rasterio
import scipy.fft as sfft
from pyproj import Transformer
from rasterio import features
from rasterio.transform import Affine
from scipy import ndimage
from shapely.geometry import Polygon

import rastools as rt
from common import D, MARSHSUB, RAW, SHEETS, TMARSH, WATER

K3 = np.ones((3, 3), bool)
STRIP, PAD = 700, 40


def register(wet, code, quad, R=40, max_m=60.0, px=5.3):
    """Shift (dx, dy) in sheet pixels that the sheet must move by to agree best with the soil survey.
    Compared are the sheet's wet mask and the survey's wet set (Water, tidal-marsh soils, tidal flat, organic / wet
    substratum fill), counted only within about 150 m of the survey's boundary between that set and natural upland
    soils (so fill shores, whose line has moved, do not vote).  The shift minimising the disagreeing area is taken;
    if it is longer than 60 m, or the minimum is not at least 1 % below the mean 53 m away from it, the sheet stays
    where the USGS georeference puts it.  (The city layer registered on shoreline edges; checked on Hart Island and
    on the Hackensack at Little Ferry, that gave shifts 70-90 m off; the area agreement fits within about 20 m.)"""
    wetset = np.isin(code, (1, 3, 4, 5, 6))
    bnd = wetset & ndimage.binary_dilation(code == 2, structure=K3)
    DB = ndimage.binary_dilation(bnd, structure=K3, iterations=28) & (wetset | (code == 2)) & ndimage.binary_erosion(quad, structure=K3, iterations=R + 5)
    f = lambda a_: sfft.rfft2(a_.astype("float32"))
    A = f(wet & quad)

    def corr(ref):
        cc = sfft.irfft2(f(ref) * np.conj(A), s=wet.shape)
        return np.concatenate([np.concatenate([cc[-R:, -R:], cc[-R:, :R + 1]], axis=1), np.concatenate([cc[:R + 1, -R:], cc[:R + 1, :R + 1]], axis=1)], axis=0).astype("float64")

    X = corr(DB) + float((wetset & DB).sum()) - 2 * corr(wetset & DB)
    del A
    iy, ix = np.unravel_index(np.argmin(X), X.shape)
    dy, dx = int(iy - R), int(ix - R)
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
    ring = (np.hypot(yy - dy, xx - dx) > 9) & (np.hypot(yy - dy, xx - dx) < 11)
    depth = float(X[ring].mean() / max(1.0, X[iy, ix]) - 1) if ring.any() else 0.0
    info = dict(found_px=[dx, dy], found_m=[round(dx * px), round(-dy * px)], disagree_best=int(X[iy, ix]), disagree_unshifted=int(X[R, R]),
                depth_10px=round(depth, 4), domain_cells=int(DB.sum()), boundary_cells=int(bnd.sum()))
    if np.hypot(dx, dy) * px > max_m or depth < 0.01 or bnd.sum() < 5000:
        info["used"] = "unshifted (minimum too far or too shallow)"
        dx, dy = 0, 0
    else:
        info["used"] = "area agreement"
    return dx, dy, info


def strip_features(vn, ink, wet, r0, r1, eps, a0=None):
    """The eight texture features of rows r0:r1 (computed with a margin).  With a0 None, returns the ruling angles
    of the strongly ruled wet cells instead (to find the sheet's dominant ruling direction)."""
    H = vn.shape[0]
    p0, p1 = max(0, r0 - PAD), min(H, r1 + PAD)
    v = vn[p0:p1].astype("float32")
    gy, gx = np.gradient(v)
    jxx, jyy, jxy = (ndimage.gaussian_filter(a_, 4.0) for a_ in (gx * gx, gy * gy, gx * gy))
    del gx, gy
    coh = np.sqrt((jyy - jxx) ** 2 + 4 * jxy ** 2) / (jxx + jyy + eps)
    ang = np.degrees(0.5 * np.arctan2(2 * jxy, jyy - jxx))
    sl = slice(r0 - p0, r1 - p0)
    if a0 is None:
        strong = wet[p0:p1] & (coh > 0.8) & ((jxx + jyy) > 0.06 ** 2)
        return ang[sl][strong[sl]][::5]
    ruled = np.where(np.abs(ang - a0) < 3.5, coh, 0)
    inkf = ink[p0:p1].astype("float32")
    d9 = ndimage.uniform_filter(inkf, 9)
    m5 = ndimage.uniform_filter(v, 5)
    sd5 = np.sqrt(np.maximum(ndimage.uniform_filter(v * v, 5) - m5 * m5, 0))
    m15 = ndimage.uniform_filter(v, 15)
    sd15 = np.sqrt(np.maximum(ndimage.uniform_filter(v * v, 15) - m15 * m15, 0))
    return np.stack([m5[sl], sd5[sl], m15[sl], sd15[sl], d9[sl], ndimage.uniform_filter(inkf, 25)[sl], ruled[sl], np.sqrt(jxx + jyy)[sl]], axis=0)


def lda(Xw, Xm):
    mu_w, mu_m = Xw.mean(0), Xm.mean(0)
    S = (np.cov(Xw.T) + np.cov(Xm.T)) / 2 + 1e-6 * np.eye(Xw.shape[1])
    wv = np.linalg.solve(S, mu_m - mu_w)
    c = wv @ (mu_m + mu_w) / 2
    return wv, c, float(((Xw @ wv) < c).mean()), float(((Xm @ wv) > c).mean())


def one(stem, soil):
    lon0, lat0, lon1, lat1, sid = SHEETS[stem]
    with rasterio.open(f"{RAW}/usgs/{stem}_62500_geo.tif") as s:
        rgb = s.read([1, 2, 3]); crs = s.crs; tr = s.transform; H, W = s.height, s.width
    # Blue ink by chromaticity c = (B - R) / (R + G + B) against the paper's, counted only on cells that are not
    # black line work or its grey edge (within 2 px of a dark pixel).  The city layer used B - R on every pixel; on
    # the yellow-paper sheets (all the New Jersey ones) the grey edges of black lines have a higher B - R than the
    # paper, so dense street grids read as water (seen at Jersey City on the Staten Island sheet).
    r, b = rgb[0].astype("float32"), rgb[2].astype("float32")
    tot = r + rgb[1] + b
    del rgb
    valid = ~ndimage.binary_dilation(tot < 360, structure=rt.disk(2))        # lum < 120
    v = (b - r) / (tot + 1.0)
    del r, b, tot
    sub = v[::4, ::4][valid[::4, ::4]]
    hist, edges = np.histogram(sub, bins=480, range=(-0.6, 0.6))
    paper = float(edges[np.argmax(hist)] + 0.00125)
    rng = float(np.percentile(sub, 99.5) - paper)
    del sub
    v = np.where(valid, (v - paper) / rng, 0).astype("float32")              # 0 = paper, 1 = strong blue ink
    ink = v > 0.35
    # wet = dense blue line work (water lining, marsh ruling) or a blue tint (the pale marsh tint of the meadows):
    # ink on more than 18 % of the usable cells of a 48 m box, or a mean tint above 20 % of the ink range over 80 m (upland soils: 90 % of cells below 12 %; marsh: median 27-45 %)
    n9 = ndimage.uniform_filter(valid.astype("float32"), 9)
    wet = (ndimage.uniform_filter(ink.astype("float32"), 9) > 0.18 * np.maximum(n9, 0.25)) & (n9 > 0.25)
    n15 = ndimage.uniform_filter(valid.astype("float32"), 15)
    wet |= (ndimage.uniform_filter(v, 15) > 0.20 * np.maximum(n15, 0.25)) & (n15 > 0.25)
    del n9, n15, valid
    vn = v.astype("float16")
    del v
    wet = ndimage.binary_closing(ndimage.binary_opening(wet, structure=rt.disk(3)), structure=rt.disk(3))
    thin_line = ink & ~wet & ~ndimage.binary_dilation(wet, structure=rt.disk(2))
    tf = Transformer.from_crs("EPSG:4267", crs.to_wkt(), always_xy=True)
    t = np.linspace(0, 1, 30)
    ring = [(lon0 + (lon1 - lon0) * a, lat0) for a in t] + [(lon1, lat0 + (lat1 - lat0) * a) for a in t] + \
           [(lon1 - (lon1 - lon0) * a, lat1) for a in t] + [(lon0, lat1 - (lat1 - lat0) * a) for a in t]
    qx, qy = tf.transform([p[0] for p in ring], [p[1] for p in ring])
    qpoly = Polygon(list(zip(qx, qy)))
    quad = features.rasterize([(qpoly, 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
    sl = soil.to_crs(crs.to_wkt())
    sl = sl[sl.intersects(qpoly.buffer(400))]
    code = features.rasterize(((g_, int(c_)) for g_, c_ in zip(sl.geometry, sl.code)), out_shape=(H, W), transform=tr, fill=0, dtype="uint8")
    del sl
    # 2. registration
    dx, dy, reg = register(wet, code, quad)
    code = ndimage.shift(code, (-dy, -dx), order=0)          # today's layer into sheet pixels
    w_today = code == WATER
    # 3. features in strips -> scratch file
    eps = 1e-6
    rows = [(a, min(H, a + STRIP)) for a in range(0, H, STRIP)]
    angs = [strip_features(vn, ink, wet, a, b_, eps) for a, b_ in rows[::3]]
    angs = np.concatenate(angs) if angs else np.zeros(0)
    a0 = float(np.median(angs)) if len(angs) > 200 else 0.0
    scratch = f"{D}/tmp_feats_{sid}.dat"
    F = np.lib.format.open_memmap(scratch, mode="w+", dtype="float16", shape=(8, H, W))
    for a, b_ in rows:
        F[:, a:b_] = strip_features(vn, ink, wet, a, b_, eps, a0)
    F.flush()
    del vn, ink
    lab_w = ndimage.binary_erosion(w_today & wet & quad, structure=rt.disk(3))
    lab_m = ndimage.binary_erosion(np.isin(code, (TMARSH, MARSHSUB)) & wet & quad, structure=rt.disk(3))
    del code, w_today
    info = dict(source=sid, shift_px=[dx, dy], shift_m=[round(float(dx * tr.a), 1), round(float(-dy * abs(tr.e)), 1)], registration=reg,
                paper_chroma=round(paper, 3), ink_range=round(rng, 3), ruling_angle=round(a0, 1), n_water=int(lab_w.sum()), n_marsh=int(lab_m.sum()))
    rg = np.random.default_rng(0)

    def sample(mask, k):
        ii = np.sort(rg.choice(np.flatnonzero(mask.ravel()), min(k, int(mask.sum())), replace=False))
        rr, cc = np.unravel_index(ii, mask.shape)
        return np.stack([np.asarray(F[j])[rr, cc] for j in range(8)], axis=1).astype("float64")

    if lab_m.sum() > 5000 and lab_w.sum() > 5000:
        Xw, Xm = sample(lab_w, 120000), sample(lab_m, 120000)
        np.savez_compressed(f"{D}/samples_{sid}.npz", Xw=Xw[:60000].astype("float32"), Xm=Xm[:60000].astype("float32"))
        wv, c, aw, am = lda(Xw, Xm)
        info.update(discriminant="own", lda_acc_water=round(aw, 3), lda_acc_marsh=round(am, 3))
    else:
        files = sorted(f for f in glob.glob(f"{D}/samples_*.npz") if not f.endswith(f"samples_{sid}.npz"))
        if files:
            Xw = np.concatenate([np.load(f)["Xw"] for f in files]).astype("float64")
            Xm = np.concatenate([np.load(f)["Xm"] for f in files]).astype("float64")
            wv, c, aw, am = lda(Xw, Xm)
            info.update(discriminant="pooled from " + ", ".join(os.path.basename(f)[8:-4] for f in files),
                        pooled_acc_water=round(aw, 3), pooled_acc_marsh=round(am, 3))
            if lab_m.sum() > 500 and lab_w.sum() > 500:
                Xw2, Xm2 = sample(lab_w, 50000), sample(lab_m, 50000)
                info.update(acc_water_on_this_sheet=round(float(((Xw2 @ wv) < c).mean()), 3), acc_marsh_on_this_sheet=round(float(((Xm2 @ wv) > c).mean()), 3))
        else:
            wv = None
            info.update(discriminant="fixed flat-tint / ruling rule")
    del lab_w, lab_m
    marsh = np.zeros((H, W), bool)
    for a, b_ in rows:
        f_ = np.asarray(F[:, a:b_]).astype("float32")
        if wv is not None:
            marsh[a:b_] = (np.tensordot(wv.astype("float32"), f_, axes=(0, 0)) - np.float32(c)) > 0
        else:
            marsh[a:b_] = (f_[6] > 0.7) | ((f_[1] < 0.10) & (f_[4] > 0.9))
    del F
    os.remove(scratch)
    if wv is not None:
        marsh = (ndimage.uniform_filter(marsh.astype("float32"), 9) > 0.5) & wet
    else:
        marsh = ndimage.binary_closing(ndimage.binary_opening(marsh & wet, structure=rt.disk(2)), structure=rt.disk(4)) & wet
    cls = np.zeros((H, W), "uint8")
    cls[wet] = 1
    cls[marsh] = 2
    cls[thin_line] = 3
    cls[~quad] = 255
    info.update(wet_ha=round(float((wet & quad).sum() * tr.a * abs(tr.e) / 1e4)), marsh_ha=round(float((marsh & quad).sum() * tr.a * abs(tr.e) / 1e4)))
    tr2 = Affine(tr.a, tr.b, tr.c + dx * tr.a, tr.d, tr.e, tr.f + dy * tr.e)
    with rasterio.open(f"{D}/sheet_{sid}.tif", "w", driver="GTiff", height=H, width=W, count=1, dtype="uint8", crs=crs, transform=tr2, compress="deflate", nodata=255) as dst:
        dst.write(cls, 1)
    json.dump(info, open(f"{D}/sheet_{sid}.json", "w"), indent=1)
    print(stem, info, flush=True)


def main():
    soil = gpd.read_parquet(f"{D}/ssurgo_counties.parquet", columns=["code", "geometry"])
    want = sys.argv[1:]
    for stem, v in SHEETS.items():
        if want and v[4] not in want:
            continue
        one(stem, soil)


if __name__ == "__main__":
    main()
