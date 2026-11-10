"""Refine a rough georeference of a street map against today's street centrelines.

For maps that are not in the Map Warper dump (Colton 1836 from the Library of Congress): start from
a few rough control points, render the map with the current fit, and in overlapping windows find the
shift that best puts the map's light street strips (streets are paper-white between shaded blocks or
block outlines) on today's centrelines (normalised cross-correlation, FFT). Each trusted window gives
a control point: pixel under the window centre <-> window centre + shift. Refit (affine / polynomial /
thin-plate spline chosen by cross-validation, blunders dropped) and repeat with a smaller search.

  python -I autoalign.py <start_id> <new_id> <x0,y0,x1,y1> [--win 500] [--step 250] [--search 120,45,20]
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy import signal, ndimage as ndi
from rasterio import features
from affine import Affine
import shapely
sys.path.insert(0, str(Path(__file__).resolve().parent))
import warp, streets as S


def street_raster(box, mpp, width=8.0):
    x0, y0, x1, y1 = box
    names, g = S.roads()
    b = shapely.bounds(g)
    sel = (b[:, 2] > x0) & (b[:, 0] < x1) & (b[:, 3] > y0) & (b[:, 1] < y1)
    shp = (int(round((y1 - y0) / mpp)), int(round((x1 - x0) / mpp)))
    geoms = [(geom, 1) for geom in shapely.buffer(g[sel], width / 2)]
    return features.rasterize(geoms, out_shape=shp, transform=Affine(mpp, 0, x0, 0, -mpp, y1), dtype="uint8").astype(np.float32)


def windows_shift(m, box, mpp, win, step, search, min_q=3.3):
    x0, y0, x1, y1 = box
    pad = search + win / 2
    big = (x0 - pad, y0 - pad, x1 + pad, y1 + pad)
    rgb = m.render(*big, mpp)
    L = rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    L = ndi.gaussian_filter(L, 1.0)
    R = street_raster(big, mpp)
    w, s = int(win / mpp), int(search / mpp)
    h = w // 2
    out = []
    for cy in np.arange(y0, y1 + 1, step):
        for cx in np.arange(x0, x1 + 1, step):
            j, i = int((cx - big[0]) / mpp), int((big[3] - cy) / mpp)
            if i - h - s < 0 or j - h - s < 0:
                continue
            A = L[i - h:i + h, j - h:j + h]
            B = R[i - h - s:i + h + s, j - h - s:j + h + s]
            if A.shape != (2 * h, 2 * h) or B.shape != (2 * h + 2 * s, 2 * h + 2 * s):
                continue
            if A.std() < 8 or B.mean() < 0.05 or (A > 250).mean() > 0.5:
                continue
            A0 = (A - A.mean()) / A.std()
            c = signal.correlate(B - B.mean(), A0, mode="valid", method="fft")
            k = np.unravel_index(np.argmax(c), c.shape)
            q = (c[k] - c.mean()) / c.std()
            dy_px, dx_px = k[0] - s, k[1] - s          # where the map window sits best in the street raster
            if q >= min_q and abs(dy_px) < s - 1 and abs(dx_px) < s - 1:
                out.append((cx, cy, dx_px * mpp, -dy_px * mpp, q))
    return np.array(out)


def main(a):
    start, new, box = a[0], a[1], [float(v) for v in a[2].split(",")]
    opt = {a[i][2:]: a[i + 1] for i in range(3, len(a) - 1) if a[i].startswith("--")}
    win, step = float(opt.get("win", 500)), float(opt.get("step", 250))
    searches = [float(v) for v in opt.get("search", "120,45,20").split(",")]
    own = json.loads(warp.OWN.read_text())
    rec = dict(own[start])
    m = warp.MapWarp(start)
    for it, search in enumerate(searches):
        mpp = 3.0 if search > 60 else 2.0
        sh = windows_shift(m, box, mpp, win, step, search, min_q=float(opt.get("minq", 3.3)))
        if len(sh) < 6:
            print("too few trusted windows:", len(sh))
            break
        px = m.inv(sh[:, :2])
        true = sh[:, :2] + sh[:, 2:4]
        # consensus: the peak of a window can sit on a neighbouring street; keep the windows that
        # agree with one affine fit (trimmed three times), then within 25 m (or 2.5 x median) of it
        keep = np.ones(len(px), bool)
        for _ in range(4):
            f = warp.Fit(px[keep], true[keep], "affine")
            e = np.hypot(*(f(px) - true).T)
            keep = e <= np.quantile(e[keep], 0.8)
        f = warp.Fit(px[keep], true[keep], "affine")
        e = np.hypot(*(f(px) - true).T)
        keep = e < max(25.0, 2.5 * np.median(e[keep]))
        print(f"   consensus keeps {keep.sum()} of {len(px)} windows (median residual to the affine fit {np.median(e[keep]):.1f} m)")
        px, true, sh = px[keep], true[keep], sh[keep]
        print("   windows kept, x range %.0f-%.0f, y range %.0f-%.0f; south-east of the East River (x > 5200, y < 6800): %d"
              % (sh[:, 0].min(), sh[:, 0].max(), sh[:, 1].min(), sh[:, 1].max(), ((sh[:, 0] > 5200) & (sh[:, 1] < 6800)).sum()))
        lon, lat = S.lonlat(true[:, 0], true[:, 1])
        rec = dict(rec, id=new, gcps=[[float(p[0]), float(p[1]), float(la), float(lo)] for p, la, lo in zip(px, lat, lon)])
        print(f"iteration {it}: search +-{search:.0f} m, {len(sh)} windows, median shift "
              f"{np.median(np.hypot(sh[:, 2], sh[:, 3])):.1f} m, median quality {np.median(sh[:, 4]):.1f}")
        own[new] = rec
        warp.OWN.write_text(json.dumps(own, indent=1))
        m = warp.MapWarp(new)
    return m


if __name__ == "__main__":
    main(sys.argv[1:])
