"""One edition of a 1:10,000 harbour chart (US Coast & Geodetic Survey / NOAA): georeference it, take its land tint,
find the piers.

  python chart.py 745-10-1967 [...]        (no argument: every downloaded chart without an output yet)

The scans (data/raw/piers/noaa/<id>.jpg) carry no georeference.  The charts are Mercator; chart 745 / 12335 is turned
so that Manhattan's avenues run up the sheet (about 29 degrees), chart 541 / 12334 is north up.  A pixel therefore maps to
web-Mercator coordinates through an affine transform, found here from the picture itself:
 1. land = the chart's land tint (buff / yellow): Otsu threshold of (R+G)/2-B, dark ink decided by its neighbours;
 2. coarse fit: the shoreline of the land mask at 1/8 size (piers opened away) is compared with today's shoreline
    (Overture water polygons) over a set of rotations and scales by FFT cross-correlation; the first chart of a series
    is searched widely, the others around the series' rotation and scale (frame width); best rotation, scale, offset win;
 3. fine fit, three passes: the chart's land without its piers (opened by 45 m) against today's land in 7 x 5 blocks,
    +-230 m, then +-60 m, then +-25 m; affine by least squares over the blocks, outliers dropped.  The datum (the
    charts before the 1990s are on NAD27 or older) is absorbed by the fit.
 4. the same finger analysis as the USGS sheets (extract.analyse).
Outputs: data/interim/piers/cand/chart_<id>.geojson, cls/chart_<id>.tif (web-Mercator), cls/chart_<id>.json (the
affine, the fit's block residuals in metres).
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pyproj
import rasterio
import shapely
import shapely.affinity
from PIL import Image
from rasterio import features
from rasterio.warp import Resampling, reproject
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))
import extract as E

Image.MAX_IMAGE_PIXELS = None
WM = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
BOX = (-74.17, 40.55, -73.84, 40.88)
G = 16.0                      # web-Mercator units per pixel of the coarse target
LAT0 = 40.71
UNIT_M = math.cos(math.radians(LAT0))


class GeoWM:
    def to_wgs(self, x, y):
        return WM.transform(x, y, direction="INVERSE")

    def from_wgs(self, lon, lat):
        return WM.transform(lon, lat)

    def geom_from_wgs(self, g):
        return shapely.transform(g, lambda c: np.column_stack(self.from_wgs(c[:, 0], c[:, 1])))

    def geom_to_wgs(self, g):
        return shapely.transform(g, lambda c: np.column_stack(self.to_wgs(c[:, 0], c[:, 1])))


def otsu(v, lo=-30, hi=200):
    h, e = np.histogram(np.clip(v, lo, hi), bins=230, range=(lo, hi))
    p = h / h.sum()
    c = (e[:-1] + e[1:]) / 2
    w0 = np.cumsum(p)
    m = np.cumsum(p * c)
    with np.errstate(divide="ignore", invalid="ignore"):
        s = (m[-1] * w0 - m) ** 2 / (w0 * (1 - w0))
    i = int(np.nanargmax(s))
    return float(c[i]), float(m[i] / w0[i]), float((m[-1] - m[i]) / (1 - w0[i])), float(w0[i])


def frame(dark):
    """inner edge of the thick border on each side (or a 3 % inset), plus the graduation band."""
    H, W = dark.shape
    out = []
    for prof, n, m in ((dark[H // 4:3 * H // 4].mean(0), W, H), (dark[:, W // 4:3 * W // 4].mean(1), H, W)):
        idx = np.nonzero(prof > 0.3)[0]
        lo = idx[idx < 0.2 * n]
        hi = idx[idx > 0.8 * n]
        out.append((int(lo.max()) if len(lo) else int(0.03 * n), int(hi.min()) if len(hi) else int(0.97 * n)))
    band = int(0.0105 * W)
    (x0, x1), (y0, y1) = out
    return x0 + band, x1 - band, y0 + band, y1 - band


def rot_img(img, theta, order=1):
    """img turned clockwise (as seen) by theta about its centre, canvas grown to fit."""
    h, w = img.shape
    c, s = math.cos(theta), math.sin(theta)
    W2, H2 = int(math.ceil(abs(w * c) + abs(h * s))), int(math.ceil(abs(w * s) + abs(h * c)))
    M = np.array([[c, -s], [s, c]])                     # output (row, col) -> input (row, col), about the centres
    cin, cout = np.array([(h - 1) / 2, (w - 1) / 2]), np.array([(H2 - 1) / 2, (W2 - 1) / 2])
    return ndimage.affine_transform(img, M, offset=cin - M @ cout, output_shape=(H2, W2), order=order)


def edge_map(m, r):
    b = m > 0.5
    er = ndimage.distance_transform_edt(b) > r
    core = ndimage.distance_transform_edt(~er) <= r
    return np.hypot(*np.gradient(ndimage.gaussian_filter(core.astype("float32"), 1.5)))


def to_px(polys, A):
    inv = ~A
    return [shapely.affinity.affine_transform(p, [inv.a, inv.b, inv.d, inv.e, inv.c, inv.f]) for p in polys]


def fit_affine(src, dst, w):
    A = np.column_stack([src, np.ones(len(src))]) * w[:, None]
    mx, *_ = np.linalg.lstsq(A, dst[:, 0] * w, rcond=None)
    my, *_ = np.linalg.lstsq(A, dst[:, 1] * w, rcond=None)
    return rasterio.Affine(mx[0], mx[1], mx[2], my[0], my[1], my[2])


def run(cid):
    tok = cid.split("-")[-1]
    year = int(tok) if len(tok) == 4 else (1800 + int(tok) if int(tok) >= 90 else 1900 + int(tok))
    series = "745" if ("745" in cid or cid.startswith("12335")) else "541"
    fn = f"chart_{cid}.tif"
    im = Image.open(E.RAW / "noaa" / f"{cid}.jpg")
    full = im.size
    im.draft("RGB", (im.size[0] // 2, im.size[1] // 2))
    a = np.asarray(im.convert("RGB"))
    H, W = a.shape[:2]
    r, g, b = (a[..., i].astype("int16") for i in range(3))
    lum = ((r + g + b) // 3).astype("uint8")
    yel = ndimage.uniform_filter(((r + g) // 2 - b).astype("float32"), 3)
    del r, g, b
    dark = lum < 95
    x0, x1, y0, y1 = frame(lum < 110)
    quad = np.zeros((H, W), bool)
    quad[y0:y1, x0:x1] = True
    thr, m_lo, m_hi, w_lo = otsu(yel[y0:y1:5, x0:x1:5])
    raw = (yel > thr) & ~dark
    den = ndimage.uniform_filter((~dark).astype("float32"), 7)
    land = (ndimage.uniform_filter(raw.astype("float32"), 7) > 0.5 * np.maximum(den, 1e-3)) & quad
    del raw, den, yel
    meta = dict(sheet=fn, edition=f"c{year}", quad=f"chart {series}", chart=cid, date_on_map=year, photo_year=year, tinted=True,
                water_rgb=[int(v) for v in np.median(a[y0:y1:9, x0:x1:9][~land[y0:y1:9, x0:x1:9]], axis=0)],
                paper_rgb=[int(v) for v in np.median(a[:max(y0 - 40, 5):3, ::3].reshape(-1, 3), axis=0)],
                land_rgb=[int(v) for v in np.median(a[y0:y1:9, x0:x1:9][land[y0:y1:9, x0:x1:9]], axis=0)],
                tint_threshold=round(thr, 1), tint_means=[round(m_lo, 1), round(m_hi, 1)], land_share=round(1 - w_lo, 3),
                full_size=list(full), half_size=[W, H], frame=[x0, x1, y0, y1])
    land_lum = float(np.median(lum[y0:y1:9, x0:x1:9][land[y0:y1:9, x0:x1:9]]))
    ink = lum < 0.72 * land_lum

    # today's water in web-Mercator
    geo = GeoWM()
    wpolys = E.today_water(geo, BOX)
    X0, Y0 = WM.transform(BOX[0], BOX[1])
    X1, Y1 = WM.transform(BOX[2], BOX[3])
    tw, th = int((X1 - X0) / G), int((Y1 - Y0) / G)
    T = 1.0 - features.rasterize([(p, 1) for p in wpolys], out_shape=(th, tw), transform=rasterio.Affine(G, 0, X0, 0, -G, Y1), fill=0, dtype="uint8").astype("float32")

    # 2. coarse: rotation, scale and offset
    ds = 8
    h8, w8 = (y1 - y0) // ds, (x1 - x0) // ds
    Lc = land[y0:y0 + h8 * ds, x0:x0 + w8 * ds].reshape(h8, ds, w8, ds).mean((1, 3)).astype("float32")
    ET = edge_map(T, 3.5)
    FT = np.fft.rfft2(ET - ET.mean())
    ones = np.ones_like(Lc)

    def search(angles, ks):
        best = (-1.0,)
        for ang in angles:
            R, V = rot_img(Lc, math.radians(ang)), rot_img(ones, math.radians(ang), order=0)
            for k in ks:
                z = k / G
                P = ndimage.zoom(R, z, order=1)
                if P.shape[0] >= th or P.shape[1] >= tw:
                    continue
                EP = edge_map(P, 3.5) * ndimage.binary_erosion(ndimage.zoom(V, z, order=0)[:P.shape[0], :P.shape[1]] > 0.5, iterations=5)
                pad = np.zeros_like(T)
                pad[:P.shape[0], :P.shape[1]] = EP
                cc = np.fft.irfft2(FT * np.conj(np.fft.rfft2(pad)), s=T.shape)[:th - P.shape[0] + 1, :tw - P.shape[1] + 1]
                iy, ix = np.unravel_index(np.argmax(cc), cc.shape)
                sc = float(cc[iy, ix] / (np.sum(EP * EP) + 1e-6))
                if sc > best[0]:
                    best = (sc, ang, k, int(ix), int(iy), R.shape)
        return best

    refp = E.OUT / f"chart_ref_{series}.json"
    if refp.exists():
        ref = json.load(open(refp))
        k0 = ref["k"] * ref["frame_w"] / (x1 - x0)
        best = search(np.arange(ref["angle"] - 1.0, ref["angle"] + 1.01, 0.5), k0 * 1.015 ** np.arange(-3, 4))
        if best[0] < 0.2:                         # another scan size or frame: look wider
            best = search(np.arange(ref["angle"] - 2.0, ref["angle"] + 2.01, 1.0), k0 * 1.03 ** np.arange(-8, 9))
    else:
        ks = 10.0 * 1.04 ** np.arange(0, 16)          # 1:10,000 scanned at 300-500 dpi
        best = search([-4, -2, 0, 2, 4], ks)
        if best[0] < 0.25:
            best = search(list(np.arange(-12, 12.1, 2)) + list(np.arange(21, 37.1, 2)), 6.0 * 1.04 ** np.arange(0, 38))
        best = search(np.arange(best[1] - 1.5, best[1] + 1.51, 0.5), best[2] * 1.01 ** np.arange(-4, 5))
    sc, ang, k, ix, iy, rshape = best
    if not refp.exists() and sc > 0.2:
        json.dump(dict(angle=float(ang), k=float(k), frame_w=int(x1 - x0), chart=cid), open(refp, "w"))
    z, c_, s_ = k / G, math.cos(math.radians(ang)), math.sin(math.radians(ang))
    src, dst = [], []
    for u, v in ((x0, y0), (x1, y0), (x0, y1), (x1, y1), ((x0 + x1) / 2, (y0 + y1) / 2)):
        px_, py_ = (u - x0) / ds - (w8 - 1) / 2, (v - y0) / ds - (h8 - 1) / 2
        qx, qy = c_ * px_ - s_ * py_ + (rshape[1] - 1) / 2, s_ * px_ + c_ * py_ + (rshape[0] - 1) / 2
        src.append((u, v))
        dst.append((X0 + G * (qx * z + ix + 0.5), Y1 - G * (qy * z + iy + 0.5)))
    A = fit_affine(np.array(src, float), np.array(dst), np.ones(len(src)))
    s = math.sqrt(abs(A.a * A.e - A.b * A.d))               # web-Mercator units per half-size pixel
    meta.update(coarse_score=round(sc, 3), coarse_angle=float(ang), coarse_units_per_px=round(s, 4))

    # 3. fine: blocks of the pier-less land against today's land
    l2 = land[::2, ::2]
    rc = 22.5 / (s * UNIT_M * 2)
    er = ndimage.distance_transform_edt(l2) > rc
    core2 = (ndimage.distance_transform_edt(~er) <= rc).astype("float32")
    q2 = quad[::2, ::2]
    res = []
    for search_m in (230, 60, 25):
        S = int(search_m / (s * UNIT_M * 2))
        t2 = 1.0 - features.rasterize([(p, 1) for p in to_px(wpolys, A)], out_shape=l2.shape, transform=rasterio.Affine.scale(2), fill=0, dtype="uint8").astype("float32")
        ny, nx = 7, 5
        bh, bw = (y1 - y0) // 2 // ny, (x1 - x0) // 2 // nx
        src, dst, wt = [], [], []
        for j in range(ny):
            for i in range(nx):
                r0_, c0_ = y0 // 2 + j * bh, x0 // 2 + i * bw
                c = core2[r0_:r0_ + bh, c0_:c0_ + bw]
                t = t2[r0_:r0_ + bh, c0_:c0_ + bw]
                if not (0.04 < c.mean() < 0.96 and 0.04 < t.mean() < 0.96):
                    continue
                c0, t0 = c - c.mean(), t - t.mean()
                cc = np.fft.irfft2(np.fft.rfft2(c0) * np.conj(np.fft.rfft2(t0)), s=c.shape)
                win = np.concatenate([np.concatenate([cc[-S:, -S:], cc[-S:, :S + 1]], axis=1), np.concatenate([cc[:S + 1, -S:], cc[:S + 1, :S + 1]], axis=1)], axis=0)
                py, px = np.unravel_index(np.argmax(win), win.shape)
                dy, dx = py - S, px - S                                        # chart(x + d) = today(x)
                strength = float(win[py, px] / (np.linalg.norm(c0) * np.linalg.norm(t0) + 1e-6))
                pc = np.array([(c0_ + bw / 2) * 2, (r0_ + bh / 2) * 2])
                src.append(pc + 2 * np.array([dx, dy]))
                dst.append(np.array(A * (pc[0], pc[1])))
                wt.append(strength)
        src, dst, wt = np.array(src), np.array(dst), np.array(wt)
        keep = wt > 0.5 * np.median(wt)
        for _ in range(3):
            A2 = fit_affine(src[keep], dst[keep], np.sqrt(wt[keep]))
            pred = np.array([A2 * (u, v) for u, v in src])
            err = np.hypot(*(pred - dst).T) * UNIT_M
            keep = (wt > 0.5 * np.median(wt)) & (err < max(3 * np.median(err[keep]), 6.0))
        A = A2
        res.append(dict(search_m=search_m, blocks=int(len(src)), used=int(keep.sum()), median_shift_m=round(float(np.median(np.hypot(*(src - np.array([[(~A2 * (X, Y))[0], (~A2 * (X, Y))[1]] for X, Y in dst])).T)) * s * UNIT_M), 1),
                        rms_m=round(float(np.sqrt(np.mean(err[keep] ** 2))), 1), max_m=round(float(err[keep].max()), 1)))
    del core2, er, t2, l2
    px_m = math.sqrt(abs(A.a * A.e - A.b * A.d)) * UNIT_M
    meta.update(affine=[A.a, A.b, A.c, A.d, A.e, A.f], px_m=round(px_m, 3), rotation_deg=round(math.degrees(math.atan2(A.d, A.a)), 3), fit=res)
    ll = np.array([WM.transform(*(A * p), direction="INVERSE") for p in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))])
    meta["bbox"] = dict(minX=float(ll[:, 0].min()), minY=float(ll[:, 1].min()), maxX=float(ll[:, 0].max()), maxY=float(ll[:, 1].max()))
    meta["corners"] = [[float(a), float(b)] for a, b in ll]

    w_today = features.rasterize([(p, 1) for p in to_px(wpolys, A)], out_shape=(H, W), transform=rasterio.Affine.identity(), fill=0, dtype="uint8").astype(bool)
    gm = json.load(open(E.ROOT / "data/interim/grid_detail_meta.json"))
    ly = np.load(E.ROOT / "data/interim/grid_detail_landyear.npy").astype("float32")
    ly_s = np.full((H, W), np.nan, "float32")
    reproject(ly, ly_s, src_transform=rasterio.Affine(*gm["transform"]), src_crs="EPSG:3857", dst_transform=A, dst_crs="EPSG:3857",
              resampling=Resampling.nearest, src_nodata=np.nan, dst_nodata=np.nan)
    later = ly_s > year
    del ly, ly_s
    info = dict(edition=meta["edition"], quad=meta["quad"])
    # piers are land-tinted on the later editions and hatched on white on the earlier ones: dense ink counts as well
    nonwater = (land | (ndimage.uniform_filter(dark.astype("float32"), 9) > 0.3)) & quad
    E.analyse(nonwater, quad, ink, later, w_today, A, "EPSG:3857", geo, fn, info, meta, False, px_m, UNIT_M)
    print("   ", cid, "tint", meta["tint_means"], "coarse", meta["coarse_score"], meta["coarse_angle"], "px_m", meta["px_m"], "rot", meta["rotation_deg"], res, flush=True)


if __name__ == "__main__":
    todo = sys.argv[1:] or sorted(p.stem for p in (E.RAW / "noaa").glob("*.jpg") if not (E.OUT / "cls" / f"chart_{p.stem}.json").exists())
    for c in todo:
        try:
            run(c)
        except Exception as e:
            print("FAILED", c, repr(e), flush=True)
