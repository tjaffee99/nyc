"""Warp a scanned map with ground control points and render it in local metric coordinates.

Sources of control points:
  * NYPL Map Warper maps (the warper itself is retired; its control points and masks survive in the
    NYC Space/Time Directory dump `mapwarper.objects.ndjson`, CC0; scans from NYPL's IIIF server).
  * control points picked here against today's street intersections (gcps_own.json).

usage:
  python -I warp.py info <map_id>
  python -I warp.py view <map_id> <x0,y0,x1,y1> <m_per_px> <out.png> [--streets] [--grid 100] [--poly f.geojson ...] [--gcps]
Local coordinates: X = UTM18N easting - 580000, Y = northing - 4500000 (m). Grid labels are in hundreds of metres.
"""
from __future__ import annotations
import json, sys, io, time
from pathlib import Path
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
from scipy.interpolate import RBFInterpolator
from scipy.ndimage import map_coordinates
import shapely
import shapely.geometry
sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I leaves the script folder off the path
import streets as S

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data" / "raw" / "extents"
INTERIM = ROOT / "data" / "interim" / "extents"
DUMP = RAW / "spacetime" / "mapwarper.objects.ndjson"
OWN = Path(__file__).resolve().parent / "gcps_own.json"
UA = {"User-Agent": "NYCThroughTime-research/0.1"}


def record(map_id) -> dict:
    """Map Warper record (name, year, imageId, uuid, gcps [x, y, lat, lon], mask geometry) or an own entry."""
    if OWN.exists():
        own = json.loads(OWN.read_text())
        if str(map_id) in own:
            return own[str(map_id)]
    for line in open(DUMP):
        if line.startswith('{"id":%s,' % map_id):
            o = json.loads(line)
            d = o["data"]
            return {"id": o["id"], "name": o["name"], "year": o.get("validSince"), "imageId": d["imageId"],
                    "uuid": d.get("uuid"), "url": d.get("nyplUrl"), "gcps": d.get("gcps") or [],
                    "mask": o.get("geometry"), "description": d.get("description")}
    raise KeyError(map_id)


def fetch(url: str, path: Path, tries=4) -> Path:
    if path.exists() and path.stat().st_size > 1000:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    for k in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=180)
            if r.status_code == 200 and len(r.content) > 1000:
                path.write_bytes(r.content)
                return path
            err = f"HTTP {r.status_code}"
        except Exception as e:  # noqa
            err = str(e)
        time.sleep(2 + 3 * k)
    raise RuntimeError(f"download failed: {url}: {err}")


def master_image(image_id: str) -> Path:
    """The scan the Map Warper control points refer to: NYPL's full-size master (`t=u`, a TIFF),
    kept here as a JPEG. NYPL's IIIF `full` image of the same id is trimmed and smaller, so the
    control points do not fit it (checked on the Ratzer plan: IIIF 4736 x 6407, master 5046 x 6758)."""
    jpg = RAW / "nypl_u" / f"{image_id}.jpg"
    if jpg.exists():
        return jpg
    tif = fetch(f"https://images.nypl.org/index.php?id={image_id}&t=u", RAW / "nypl_u" / f"{image_id}.tif")
    im = Image.open(tif)
    im.convert("RGB").save(jpg, quality=92)
    print("master", image_id, im.size)
    tif.unlink()
    return jpg


class Fit:
    """2-D transform a -> b fitted to control points: affine, 2nd-order polynomial or thin-plate spline."""

    def __init__(self, a, b, model="affine", smoothing=0.0):
        self.model, self.smoothing = model, smoothing
        self.a0, self.b0 = a.mean(0), b.mean(0)
        A, B = (a - self.a0) / 1000.0, (b - self.b0) / 1000.0
        if model == "tps":
            self.f = RBFInterpolator(A, B, kernel="thin_plate_spline", smoothing=smoothing, degree=1)
        else:
            self.coef = np.linalg.lstsq(self._design(A), B, rcond=None)[0]

    def _design(self, A):
        x, y = A[:, 0], A[:, 1]
        cols = [np.ones_like(x), x, y]
        if self.model == "poly2":
            cols += [x * x, x * y, y * y]
        return np.column_stack(cols)

    def __call__(self, a):
        A = (np.atleast_2d(a) - self.a0) / 1000.0
        B = self.f(A) if self.model == "tps" else self._design(A) @ self.coef
        return B * 1000.0 + self.b0


def cv_errors(px, xy, model, smoothing, folds=10):
    """Cross-validated error (m) of each control point: predicted from a fit that did not see it."""
    n = len(px)
    k = n if n <= 60 else folds
    idx = np.arange(n)
    rng = np.random.default_rng(0)
    rng.shuffle(idx)
    err = np.zeros(n)
    for part in np.array_split(idx, k):
        keep = np.setdiff1d(idx, part)
        f = Fit(px[keep], xy[keep], model, smoothing)
        err[part] = np.hypot(*(f(px[part]) - xy[part]).T)
    return err


class MapWarp:
    def __init__(self, map_id, verbose=True):
        self.rec = record(map_id)
        self.id = map_id
        g = np.array(self.rec["gcps"], float)
        self.px_all = g[:, :2]
        X, Y = S.local(g[:, 3], g[:, 2])
        self.xy_all = np.column_stack([X, Y])
        self._fit(verbose)
        self._img = {}

    def _fit(self, verbose):
        px, xy = self.px_all, self.xy_all
        n = len(px)
        keep = np.ones(n, bool)
        if n >= 6:  # gross blunders against a plain affine fit
            for _ in range(3):
                f = Fit(px[keep], xy[keep], "affine")
                e = np.hypot(*(f(px) - xy).T)
                bad = e > max(6 * np.median(e[keep]), 150.0)
                if (bad == ~keep).all():
                    break
                keep = ~bad
        cands = [("affine", 0.0)]
        if keep.sum() >= 10:
            cands.append(("poly2", 0.0))
        if keep.sum() >= 12:
            cands += [("tps", s) for s in (0.0, 1e-4, 1e-3, 1e-2, 1e-1)]
        best = None
        for rnd in range(2):
            res = []
            for m, s in cands:
                if keep.sum() < 4:
                    e = np.hypot(*(Fit(px[keep], xy[keep], m, s)(px[keep]) - xy[keep]).T)  # no spare points: fit residual
                else:
                    e = cv_errors(px[keep], xy[keep], m, s)
                res.append((float(np.sqrt((e ** 2).mean())), m, s, e))
            best = min(res, key=lambda r: r[0])
            e = best[3]
            bad = e > max(5 * np.median(e), 30.0)
            if rnd == 0 and bad.any() and keep.sum() - bad.sum() >= 8:
                ii = np.flatnonzero(keep)
                keep[ii[bad]] = False
                continue
            break
        self.keep = keep
        self.model, self.smoothing = best[1], best[2]
        self.cv_rms, self.cv_median, self.cv_max = best[0], float(np.median(best[3])), float(best[3].max())
        self.fwd = Fit(px[keep], xy[keep], self.model, self.smoothing)   # pixel -> local metres
        self.inv = Fit(xy[keep], px[keep], self.model, self.smoothing)   # local metres -> pixel
        a = Fit(px[keep], xy[keep], "affine")
        self.src_mpp = float(np.sqrt(abs(np.linalg.det(a.coef[1:3, :]))))  # metres per source pixel
        if verbose:
            print(f"map {self.id}: {self.rec['name'][:70]} | image {self.rec['imageId']} | gcps {keep.sum()}/{n} | "
                  f"{self.model} s={self.smoothing} | CV rms {self.cv_rms:.1f} m, median {self.cv_median:.1f} m, max {self.cv_max:.1f} m | "
                  f"{self.src_mpp:.2f} m/px")

    def image(self, f=1):
        if f not in self._img:
            path = Path(self.rec["image_path"]) if self.rec.get("image_path") else master_image(self.rec["imageId"])
            im = Image.open(path).convert("RGB")
            if f > 1:
                im = im.reduce(f)
            self._img = {f: np.asarray(im)}
        return self._img[f]

    def render(self, x0, y0, x1, y1, mpp):
        """RGB array of the map over the local box, north up, `mpp` metres per pixel."""
        W, H = int(round((x1 - x0) / mpp)), int(round((y1 - y0) / mpp))
        step = 8
        gx, gy = np.arange(0, W + step, step), np.arange(0, H + step, step)
        XX, YY = np.meshgrid(x0 + (gx + 0.5) * mpp, y1 - (gy + 0.5) * mpp)
        p = self.inv(np.column_stack([XX.ravel(), YY.ravel()]))
        gpx, gpy = p[:, 0].reshape(XX.shape), p[:, 1].reshape(XX.shape)
        R, C = np.meshgrid(np.arange(H) / step, np.arange(W) / step, indexing="ij")
        PX = map_coordinates(gpx, [R, C], order=1)
        PY = map_coordinates(gpy, [R, C], order=1)
        f = max(1, int(mpp / self.src_mpp))
        img = self.image(f)
        cx, cy = (PX + 0.5) / f - 0.5, (PY + 0.5) / f - 0.5
        out = np.stack([map_coordinates(img[..., c], [cy, cx], order=1, cval=255) for c in range(3)], -1)
        return out.astype(np.uint8)


def font(size=13):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def annotate(arr, x0, y0, x1, y1, mpp, streets=False, grid=0, polys=(), gcps=None, street_rgb=(0, 150, 255)):
    im = Image.fromarray(arr).convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    def P(x, y):
        return ((x - x0) / mpp, (y1 - y) / mpp)
    if streets:
        names, g = S.roads()
        b = shapely.bounds(g)
        sel = (b[:, 2] > x0) & (b[:, 0] < x1) & (b[:, 3] > y0) & (b[:, 1] < y1)
        for geom in g[sel]:
            c = shapely.get_coordinates(geom)
            d.line([P(x, y) for x, y in c], fill=street_rgb + (170,), width=1)
    for path, rgb in polys:
        fc = json.loads(Path(path).read_text())
        feats = fc["features"] if fc.get("type") == "FeatureCollection" else [fc]
        for ft in feats:
            geom = shapely.geometry.shape(ft["geometry"])
            for poly in (geom.geoms if hasattr(geom, "geoms") else [geom]):
                for ring in [poly.exterior, *poly.interiors]:
                    c = np.array(ring.coords)
                    X, Y = S.local(c[:, 0], c[:, 1])
                    d.line([P(x, y) for x, y in zip(X, Y)], fill=rgb + (255,), width=2)
    if gcps is not None:
        for x, y in gcps:
            u, v = P(x, y)
            d.ellipse([u - 4, v - 4, u + 4, v + 4], outline=(255, 0, 255, 255), width=2)
    if grid:
        ft = font(13)
        for gx in np.arange(np.ceil(x0 / grid) * grid, x1, grid):
            u = (gx - x0) / mpp
            d.line([(u, 0), (u, im.height)], fill=(255, 220, 0, 110), width=1)
            for v in (2, im.height - 16):
                d.rectangle([u + 1, v, u + 26, v + 14], fill=(255, 255, 255, 200))
                d.text((u + 2, v), "%d" % round(gx / 100), fill=(200, 0, 0, 255), font=ft)
        for gy in np.arange(np.ceil(y0 / grid) * grid, y1, grid):
            v = (y1 - gy) / mpp
            d.line([(0, v), (im.width, v)], fill=(255, 220, 0, 110), width=1)
            for u in (2, im.width - 30):
                d.rectangle([u, v + 1, u + 27, v + 15], fill=(255, 255, 255, 200))
                d.text((u + 1, v + 1), "%d" % round(gy / 100), fill=(0, 0, 200, 255), font=ft)
    return im


def main(argv):
    if argv[0] == "info":
        for mid in argv[1:]:
            m = MapWarp(mid)
            print("   ", m.rec.get("url"), "| gcp px range x %.0f-%.0f y %.0f-%.0f" % (m.px_all[:, 0].min(), m.px_all[:, 0].max(), m.px_all[:, 1].min(), m.px_all[:, 1].max()),
                  "| local box x %.0f-%.0f y %.0f-%.0f" % (m.xy_all[:, 0].min(), m.xy_all[:, 0].max(), m.xy_all[:, 1].min(), m.xy_all[:, 1].max()))
    elif argv[0] == "view":
        mid, box, mpp, out = argv[1], [float(v) for v in argv[2].split(",")], float(argv[3]), argv[4]
        rest = argv[5:]
        grid = int(rest[rest.index("--grid") + 1]) if "--grid" in rest else 0
        polys = []
        cols = [(255, 0, 0), (0, 160, 0), (160, 0, 200), (255, 120, 0)]
        for i, a in enumerate(rest):
            if a == "--poly":
                polys.append((rest[i + 1], cols[len(polys) % 4]))
        m = MapWarp(mid)
        arr = m.render(*box, mpp)
        im = annotate(arr, *box, mpp, streets="--streets" in rest, grid=grid, polys=polys,
                      gcps=m.xy_all[m.keep] if "--gcps" in rest else None)
        im.save(out)
        print(out, im.size)


if __name__ == "__main__":
    main(sys.argv[1:])
