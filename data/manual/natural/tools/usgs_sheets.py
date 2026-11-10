"""USGS 15-minute sheets of 1888-1898 -> land / water / marsh on one city grid (UTM 18N, 6 m).

Per sheet (own pixel grid, 5.3 m):
 1. wet = blue-ink density (see usgs_classify.classify), i.e. water lining, marsh ruling or tint;
 2. registration: the sheet is shifted so that the edge of its wet mask best coincides with today's shoreline
    (edge of the soil survey's "Water" unit), by cross-correlating the two edge images within +-160 m.  Unchanged
    shores vote together, filled shores scatter;
 3. marsh against water inside wet: a linear discriminant on texture features (mean tint, fine and coarse
    texture, ink density, ruling coherence), trained per sheet on pixels whose answer is known from the soil
    survey: still open water today -> water; tidal-marsh soils and "Urban land, tidal marsh substratum" -> marsh.
 4. warped (nearest) to the city grid with the shift applied.
outputs: data/interim/natural/usgs_1890s.tif (0 land, 1 water, 2 marsh, 3 thin blue line on land, 255 no sheet),
         usgs_sheets.json (shift, discriminant accuracy per sheet)
"""
import json

import geopandas as gpd
import numpy as np
import rasterio
from pyproj import Transformer
from rasterio import features
from rasterio.transform import Affine, from_origin
from rasterio.warp import Resampling, reproject
from scipy import ndimage
from shapely.geometry import Polygon

import rastools as rt

ROOT = "/home/user/nyc"
D = f"{ROOT}/data/interim/natural"
SHEETS = {  # stem: (quad lon0, lat0, lon1, lat1, source id)
    "NJ_Harlem_472515_1891": (-74.0, 40.75, -73.75, 41.0, "usgs_harlem_1891"),
    "NY_Brooklyn_123118_1897": (-74.0, 40.5, -73.75, 40.75, "usgs_brooklyn_1897"),
    "NJ_Staten_Island_255388_1898": (-74.25, 40.5, -74.0, 40.75, "usgs_staten_island_1898"),
    "NJ_Paterson_255310_1888": (-74.25, 40.75, -74.0, 41.0, "usgs_paterson_1888"),
    "NY_Hempstead_129886_1897": (-73.75, 40.5, -73.5, 40.75, "usgs_hempstead_1897"),
    "NY_Oyster_Bay_136363_1897": (-73.75, 40.75, -73.5, 41.0, "usgs_oyster_bay_1897"),
}
MARSH_SOILS = ["IwA", "IPA", "IPMA", "PaA", "MaA", "WbA", "ApA", "UmA", "UmB"]
GRID = dict(x0=562000.0, y1=4533000.0, px=6.0, w=8400, h=8000)  # UTM 18N; covers the five boroughs


def wet_and_features(rgb):
    r, g, b = (rgb[i].astype("float32") for i in range(3))
    v = b - r
    lum = (r + g + b) / 3
    hist, edges = np.histogram(v[::4, ::4], bins=256, range=(-128, 128))
    paper = edges[np.argmax(hist)] + 0.5
    top = np.percentile(v[::4, ::4], 99.5)
    rng = top - paper
    ink = (v > paper + 0.35 * rng) & (lum > 60)
    inkf = ink.astype("float32")
    d9 = ndimage.uniform_filter(inkf, 9)
    wet = ndimage.binary_closing(ndimage.binary_opening(d9 > 0.18, structure=rt.disk(3)), structure=rt.disk(3))
    gy, gx = np.gradient(v)
    jxx, jyy, jxy = (ndimage.gaussian_filter(a_, 4.0) for a_ in (gx * gx, gy * gy, gx * gy))
    coh = np.sqrt((jyy - jxx) ** 2 + 4 * jxy ** 2) / (jxx + jyy + 1e-3)
    ang = np.degrees(0.5 * np.arctan2(2 * jxy, jyy - jxx))
    strong = wet & (coh > 0.8) & ((jxx + jyy) > (0.06 * rng) ** 2)
    a0 = float(np.median(ang[strong])) if strong.sum() > 1000 else 0.0
    ruled = np.where(np.abs(ang - a0) < 3.5, coh, 0).astype("float32")
    vn = (v - paper) / rng
    m5 = ndimage.uniform_filter(vn, 5)
    sd5 = np.sqrt(np.maximum(ndimage.uniform_filter(vn * vn, 5) - m5 * m5, 0))
    m15 = ndimage.uniform_filter(vn, 15)
    sd15 = np.sqrt(np.maximum(ndimage.uniform_filter(vn * vn, 15) - m15 * m15, 0))
    feats = np.stack([m5, sd5, m15, sd15, d9, ndimage.uniform_filter(inkf, 25), ruled, np.sqrt(jxx + jyy) / rng], axis=0).astype("float32")
    thin_line = ink & ~wet & ~ndimage.binary_dilation(wet, structure=rt.disk(2))
    return wet, feats, thin_line


def main():
    soil = gpd.read_parquet(f"{D}/ssurgo_all.parquet")  # UTM 18N
    city = np.full((GRID["h"], GRID["w"]), 255, "uint8")
    src_id = np.zeros((GRID["h"], GRID["w"]), "uint8")
    ctr = from_origin(GRID["x0"], GRID["y1"], GRID["px"], GRID["px"])
    report = {}
    for si, (stem, (lon0, lat0, lon1, lat1, sid)) in enumerate(SHEETS.items(), start=1):
        with rasterio.open(f"{ROOT}/data/raw/natural/usgs/{stem}_62500_geo.tif") as s:
            rgb = s.read(); crs = s.crs; tr = s.transform; H, W = s.height, s.width
        wet, feats, thin_line = wet_and_features(rgb)
        del rgb
        # quad neat line in the sheet's CRS
        tf = Transformer.from_crs(crs.geodetic_crs if hasattr(crs, "geodetic_crs") else "EPSG:4267", crs, always_xy=True) if False else Transformer.from_crs("EPSG:4267", crs.to_wkt(), always_xy=True)
        t = np.linspace(0, 1, 30)
        ring = [(lon0 + (lon1 - lon0) * a, lat0) for a in t] + [(lon1, lat0 + (lat1 - lat0) * a) for a in t] + \
               [(lon1 - (lon1 - lon0) * a, lat1) for a in t] + [(lon0, lat1 - (lat1 - lat0) * a) for a in t]
        qx, qy = tf.transform([p[0] for p in ring], [p[1] for p in ring])
        quad = features.rasterize([(Polygon(list(zip(qx, qy))), 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
        sl = soil.to_crs(crs.to_wkt())
        sl = sl[sl.intersects(Polygon(list(zip(qx, qy))))]
        ras = lambda gs: features.rasterize(((x, 1) for x in gs), out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool) if len(gs) else np.zeros((H, W), bool)
        w_today = ras(sl[sl.MUSYM == "W"].geometry)
        surveyed = ras(sl.geometry)
        # 2. registration by shoreline votes
        e_old = (wet ^ ndimage.binary_erosion(wet)) & quad & surveyed
        e_new = ndimage.binary_dilation((w_today ^ ndimage.binary_erosion(w_today)) & surveyed, structure=np.ones((3, 3), bool))
        fa = np.fft.rfft2(e_new.astype("float32")); fb = np.fft.rfft2(e_old.astype("float32"))
        cc = np.fft.irfft2(fa * np.conj(fb), s=e_old.shape)
        R = 30
        win = np.concatenate([np.concatenate([cc[-R:, -R:], cc[-R:, :R + 1]], axis=1), np.concatenate([cc[:R + 1, -R:], cc[:R + 1, :R + 1]], axis=1)], axis=0)
        win = ndimage.uniform_filter(win, 3)
        iy, ix = np.unravel_index(np.argmax(win), win.shape)
        dy, dx = iy - R, ix - R            # e_old must move by (dy, dx) pixels to sit on today's shoreline
        peak = float(win.max() / (np.median(win) + 1e-6))
        shift = lambda m: ndimage.shift(m.astype("uint8"), (-dy, -dx), order=0).astype(bool)  # today's layer into sheet pixels
        # paper-white open water far from any shore (the lining thins out): a dry patch of 20 ha or more that is
        # mostly open water today is water.  Bare islands inside the lining stay land.
        lab, n = ndimage.label(~wet & quad)
        if n:
            idx = np.arange(1, n + 1)
            size = ndimage.sum(~wet & quad, lab, index=idx)
            fw = ndimage.mean(shift(w_today).astype("float32"), lab, index=idx)
            pale = np.isin(lab, 1 + np.nonzero((size >= 7000) & (fw >= 0.6))[0])
            wet |= pale
            feats[0][pale] = 0.0
        del lab
        # 3. marsh / water discriminant, trained on pixels with a known answer
        lab_w = shift(w_today) & wet & quad
        lab_w = ndimage.binary_erosion(lab_w, structure=rt.disk(3))
        lab_m = shift(ras(sl[sl.MUSYM.isin(MARSH_SOILS)].geometry)) & wet & quad
        lab_m = ndimage.binary_erosion(lab_m, structure=rt.disk(3))
        info = dict(source=sid, shift_px=[int(dx), int(dy)], shift_m=[float(dx * tr.a), float(-dy * abs(tr.e))], peak_ratio=round(peak, 2),
                    n_water=int(lab_w.sum()), n_marsh=int(lab_m.sum()))
        F = feats.reshape(feats.shape[0], -1)
        rng = np.random.default_rng(0)
        if lab_m.sum() > 5000 and lab_w.sum() > 5000:
            iw = rng.choice(np.flatnonzero(lab_w.ravel()), min(200000, int(lab_w.sum())), replace=False)
            im = rng.choice(np.flatnonzero(lab_m.ravel()), min(200000, int(lab_m.sum())), replace=False)
            Xw, Xm = F[:, iw].T.astype("float64"), F[:, im].T.astype("float64")
            mu_w, mu_m = Xw.mean(0), Xm.mean(0)
            S = (np.cov(Xw.T) + np.cov(Xm.T)) / 2 + 1e-6 * np.eye(F.shape[0])
            wv = np.linalg.solve(S, mu_m - mu_w)
            c = wv @ (mu_m + mu_w) / 2
            info.update(lda_acc_water=round(float(((Xw @ wv) < c).mean()), 3), lda_acc_marsh=round(float(((Xm @ wv) > c).mean()), 3))
            score = np.zeros(H * W, "float32")
            for a in range(0, H * W, 4_000_000):
                score[a:a + 4_000_000] = F[:, a:a + 4_000_000].T @ wv.astype("float32") - np.float32(c)
            marsh = (ndimage.uniform_filter((score.reshape(H, W) > 0).astype("float32"), 9) > 0.5) & wet
        else:
            info.update(lda="too few labelled pixels; flat-tint / ruling rule used")
            marsh = wet & ((feats[6] > 0.7) | ((feats[1] < 0.10) & (feats[4] > 0.9)))
            marsh = ndimage.binary_closing(ndimage.binary_opening(marsh, structure=rt.disk(2)), structure=rt.disk(4)) & wet
        cls = np.zeros((H, W), "uint8")
        cls[wet] = 1
        cls[marsh] = 2
        cls[thin_line] = 3
        cls[~quad] = 255
        # 4. to the city grid, shifted
        tr2 = Affine(tr.a, tr.b, tr.c + dx * tr.a, tr.d, tr.e, tr.f + dy * tr.e)
        tmp = np.full_like(city, 255)
        reproject(cls, tmp, src_transform=tr2, src_crs=crs, dst_transform=ctr, dst_crs="EPSG:32618", resampling=Resampling.nearest, src_nodata=255, dst_nodata=255)
        put = (tmp != 255) & (city == 255)
        city[put] = tmp[put]
        src_id[put] = si
        report[stem] = info
        print(stem, info, flush=True)
        del feats, F
    prof = dict(driver="GTiff", height=GRID["h"], width=GRID["w"], count=2, dtype="uint8", crs="EPSG:32618", transform=ctr, compress="deflate")
    with rasterio.open(f"{D}/usgs_1890s.tif", "w", **prof) as dst:
        dst.write(city, 1); dst.write(src_id, 2)
    json.dump(report, open(f"{D}/usgs_sheets.json", "w"), indent=1)


if __name__ == "__main__":
    main()
