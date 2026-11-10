"""Registration experiment 2: area agreement. The sheet's wet mask against the soil survey's wet set (Water, tidal
marsh soils, organic / wet substratum fill), counted only within 150 m of the survey's boundary between that set and
natural upland soils; the shift that minimises the disagreeing area."""
import sys, json
import geopandas as gpd, numpy as np, rasterio
from pyproj import Transformer
from rasterio import features
from scipy import ndimage
from shapely.geometry import Polygon
import rastools as rt
from common import D, RAW, SHEETS
from reg_test import wet_only

def xor_surface(A, B, DB, R=40):
    """disagreeing area for every shift (dy, dx) in [-R, R]: sheet mask A must move by (dy, dx) to sit on B."""
    f = lambda a: np.fft.rfft2(a.astype("float32"))
    def corr(ref, mov):
        cc = np.fft.irfft2(f(ref) * np.conj(f(mov)), s=mov.shape)
        return np.concatenate([np.concatenate([cc[-R:, -R:], cc[-R:, :R + 1]], axis=1), np.concatenate([cc[:R + 1, -R:], cc[:R + 1, :R + 1]], axis=1)], axis=0)
    return corr(DB, A) + float((B & DB).sum()) - 2 * corr(B & DB, A)

def register(wet, code, quad, R=40):
    k3 = np.ones((3, 3), bool)
    wetset = np.isin(code, (1, 3, 4, 5, 6))
    bnd = wetset & ndimage.binary_dilation(code == 2, structure=k3)
    DB = (ndimage.distance_transform_edt(~bnd) <= 28) & (wetset | (code == 2)) & (ndimage.distance_transform_edt(quad) > 45)
    X = xor_surface(wet & quad, wetset, DB, R)
    iy, ix = np.unravel_index(np.argmin(X), X.shape)
    dy, dx = int(iy - R), int(ix - R)
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
    ring = (np.hypot(yy - dy, xx - dx) > 9) & (np.hypot(yy - dy, xx - dx) < 11)
    return dx, dy, dict(xor_best=int(X[iy, ix]), xor_zero=int(X[R, R]), xor_10px_off=int(X[ring].mean()) if ring.any() else 0, domain=int(DB.sum()), bnd=int(bnd.sum()))

if __name__ == "__main__":
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
        dx, dy, info = register(wet, code, quad)
        print(sid, "shift px", (dx, dy), "m E,N", (round(dx * tr.a), round(-dy * abs(tr.e))), info, flush=True)
