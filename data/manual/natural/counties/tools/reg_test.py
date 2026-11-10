"""Registration experiment: shift of each sheet against (A) every edge of today's Water unit, (B) the soil survey's
original upland edge = boundary between {Water, tidal-marsh soils, organic / wet substratum fill} and upland soils."""
import sys
import geopandas as gpd, numpy as np, rasterio
from pyproj import Transformer
from rasterio import features
from scipy import ndimage
from shapely.geometry import Polygon
import rastools as rt
from common import D, RAW, SHEETS

def wet_only(rgb):
    r, g, b = (rgb[i].astype("float32") for i in range(3))
    v = b - r; lum = (r + g + b) / 3
    hist, edges = np.histogram(v[::4, ::4], bins=256, range=(-128, 128))
    paper = edges[np.argmax(hist)] + 0.5
    rng = np.percentile(v[::4, ::4], 99.5) - paper
    ink = (v > paper + 0.35 * rng) & (lum > 60)
    d9 = ndimage.uniform_filter(ink.astype("float32"), 9)
    return ndimage.binary_closing(ndimage.binary_opening(d9 > 0.18, structure=rt.disk(3)), structure=rt.disk(3))

def best(e_new, e_old, R=30):
    fa = np.fft.rfft2(ndimage.binary_dilation(e_new, structure=np.ones((3, 3), bool)).astype("float32")); fb = np.fft.rfft2(e_old.astype("float32"))
    cc = np.fft.irfft2(fa * np.conj(fb), s=e_old.shape)
    win = np.concatenate([np.concatenate([cc[-R:, -R:], cc[-R:, :R + 1]], axis=1), np.concatenate([cc[:R + 1, -R:], cc[:R + 1, :R + 1]], axis=1)], axis=0)
    win = ndimage.uniform_filter(win, 3)
    iy, ix = np.unravel_index(np.argmax(win), win.shape)
    dy, dx = int(iy - R), int(ix - R)
    near = ndimage.binary_dilation(e_old, structure=rt.disk(3))
    sh = lambda m: ndimage.shift(m.astype("uint8"), (-dy, -dx), order=0).astype(bool)
    a0 = (e_new & near).sum() / max(1, e_new.sum()); a1 = (sh(e_new) & near).sum() / max(1, e_new.sum())
    return dx, dy, round(float(win.max() / (np.median(win) + 1e-6)), 2), round(float(a0), 3), round(float(a1), 3), int(e_new.sum())

def main():
    soil = gpd.read_parquet(f"{D}/ssurgo_counties.parquet", columns=["code", "geometry"])
    for stem, (lon0, lat0, lon1, lat1, sid) in SHEETS.items():
        if len(sys.argv) > 1 and sid not in sys.argv[1:]:
            continue
        with rasterio.open(f"{RAW}/usgs/{stem}_62500_geo.tif") as s:
            rgb = s.read(); crs = s.crs; tr = s.transform; H, W = s.height, s.width
        wet = wet_only(rgb[:3]); del rgb
        tf = Transformer.from_crs("EPSG:4267", crs.to_wkt(), always_xy=True)
        t = np.linspace(0, 1, 30)
        ring = [(lon0 + (lon1 - lon0) * a, lat0) for a in t] + [(lon1, lat0 + (lat1 - lat0) * a) for a in t] + [(lon1 - (lon1 - lon0) * a, lat1) for a in t] + [(lon0, lat1 - (lat1 - lat0) * a) for a in t]
        qx, qy = tf.transform([p[0] for p in ring], [p[1] for p in ring]); qpoly = Polygon(list(zip(qx, qy)))
        quad = features.rasterize([(qpoly, 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
        sl = soil.to_crs(crs.to_wkt()); sl = sl[sl.intersects(qpoly.buffer(400))]
        code = features.rasterize(((g, int(c)) for g, c in zip(sl.geometry, sl.code)), out_shape=(H, W), transform=tr, fill=0, dtype="uint8")
        k3 = np.ones((3, 3), bool)
        w_today = code == 1
        eA_new = (w_today ^ ndimage.binary_erosion(w_today)) & (code != 0)
        eA_old = (wet ^ ndimage.binary_erosion(wet)) & quad & (code != 0)
        wetset = np.isin(code, (1, 3, 4, 5, 6))
        eB_new = wetset & ndimage.binary_dilation(code == 2, structure=k3) & quad
        eB_old = wet & ndimage.binary_dilation(~wet, structure=k3) & quad & (code != 0)
        print(sid, "px", round(tr.a, 2), "A(dx,dy,peak,agree0,agree1,n)", best(eA_new, eA_old), "B", best(eB_new, eB_old), flush=True)


if __name__ == "__main__":
    main()
