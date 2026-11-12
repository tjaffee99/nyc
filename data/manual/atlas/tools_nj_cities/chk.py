"""Registration check against standing buildings: for each traced sheet, the share of traced area that lies on today's footprints at the fit and at every shift of +-45 m.
A fit is VERIFIED if the share at the fit is at least 1.5 x the mean share on the ring of shifts 12-45 m away, and the best shift within 15 m is under 3 m.
python -I chk.py <layer> [sheet ...]  -> data/interim/atlas_nj_cities/<layer>/chk.json"""
import sys, json, pickle
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import njc
from njc import A, jl, lay_p, pid_of
from rasterio import features
from affine import Affine
from scipy import signal
from shapely import wkb
import shapely
layer = sys.argv[1]; city = jl(lay_p)[layer]["city"]
F, tr = njc.city_raster(city, 1.0)
out = {}; cp = A.WORK / layer / "chk.json"
if cp.exists(): out = json.loads(cp.read_text())
sheets = sys.argv[2:] or [p["sheet"] for p in jl(lay_p)[layer]["plates"]]
for sh in sheets:
    pid = pid_of(layer, sh); f = A.WORK / layer / f"{pid}.pkl"
    if not f.exists(): continue
    d = pickle.load(open(f, "rb")); polys = [wkb.loads(o["geom"]) for o in d["items"]]
    polys = [p for p in polys if p.area > 15]
    if len(polys) < 30: out[sh] = dict(n=len(polys), verdict="too few outlines"); continue
    b = shapely.total_bounds(np.array(polys, object)); R = 45
    x0, y1 = np.floor(b[0]) - R, np.ceil(b[3]) + R; x1, y0 = np.ceil(b[2]) + R, np.floor(b[1]) - R
    j0, i0 = int((x0 - tr.c) / 1), int((tr.f - y1) / 1)
    h, w = int(y1 - y0), int(x1 - x0)
    if i0 < 0 or j0 < 0 or i0 + h > F.shape[0] or j0 + w > F.shape[1]: out[sh] = dict(n=len(polys), verdict="outside raster"); continue
    Fw = F[i0:i0 + h, j0:j0 + w]
    M = features.rasterize([(p, 1) for p in polys], out_shape=(h, w), transform=Affine(1, 0, x0, 0, -1, y1), dtype="uint8").astype(np.float32)
    ys, xs = np.nonzero(M); M = M[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    C = signal.fftconvolve(Fw, M[::-1, ::-1], mode="valid") / M.sum()
    cy, cx = (C.shape[0] - 1) // 2, (C.shape[1] - 1) // 2   # zero shift (window padded symmetrically by R)
    # the mask was cropped to its own bounds, so zero shift sits at (R - (ys.min() - R)) ... recompute explicitly
    oy, ox = R + ys.min() - R, R + xs.min() - R
    z = C[ys.min(), xs.min()] if False else None
    # direct: position of the mask crop inside Fw is (ys.min(), xs.min()); valid-corr index equals that offset
    iy0, ix0 = ys.min(), xs.min()
    base = float(C[iy0, ix0])
    yy, xx = np.mgrid[0:C.shape[0], 0:C.shape[1]]; dist = np.hypot(yy - iy0, xx - ix0)
    ring = C[(dist >= 12) & (dist <= 45)]
    near = (dist <= 15); k = np.unravel_index(np.argmax(np.where(near, C, -1)), C.shape)
    best = (int(k[1] - ix0), int(-(k[0] - iy0)))
    r = base / max(float(ring.mean()), 1e-6)
    ok = r >= 1.5 and np.hypot(*best) <= 3
    out[sh] = dict(n=len(polys), on_today=round(base, 3), ring=round(float(ring.mean()), 3), ratio=round(r, 2), best_shift_m=best, verdict="verified" if ok else "not verified")
    print(sh, out[sh], flush=True)
cp.write_text(json.dumps(out, indent=1))
