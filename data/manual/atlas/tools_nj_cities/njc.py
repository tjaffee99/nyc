"""Sanborn sheets of Paterson / Newark: registration by matching the traced building mask to today's footprints (no control points exist).
  python -I njc.py add <layer> <tag> <sheet> [<sheet> ...]     placeholder entries (gcps_own.json, layers.json)
  python -I njc.py locate <layer> <sheet> ... [--city paterson|newark] [--prior x,y --pr m]   rotation / scale / shift search; writes the fit as control points
  python -I njc.py rest ... see main
The sheet's scale (50 ft to the inch, about 0.1 m per pixel at 50 %), its rotation (north arrow) and its position are searched by normalised
cross-correlation of the traced mask with a raster of today's footprints, coarse (4 m cells) then fine (1 m cells); the lead of the best peak over
the best peak elsewhere is printed. refine_buildings (atlas.py) then polishes the fit on standing buildings."""
import json, sys, pickle, os
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import atlas as A
import shapely
from shapely import wkb
from scipy import signal, ndimage as ndi
from rasterio import features
from affine import Affine
S = A.S
S.BBOX = (-74.40, 40.55, -73.9, 41.1)
ROOT = A.ROOT
CITY = {"paterson": (-74.23, 40.86, -74.10, 40.96), "newark": (-74.26, 40.67, -74.10, 40.80)}
CENTRE = {"paterson": (-74.1715, 40.9165), "newark": (-74.1700, 40.7350)}
STYLE = {"core": 12, "wall_px": 240, "hole_px": 500, "front_px": 2500, "frame": {"db_min": 6.5, "hue": 0.42, "L_min": 50, "L_max": 92}}
own_p = HERE / "gcps_own.json"; lay_p = HERE / "layers.json"
def jl(p): return json.loads(p.read_text())
def pid_of(layer, sheet): return int(f"{jl(lay_p)[layer]['id0']}{int(sheet):04d}") if str(sheet).isdigit() else None

def add(layer, tag, sheets):
    L = jl(lay_p); own = jl(own_p); d = L[layer]
    for sh in sheets:
        pid = int(f"{d['id0']}{int(sh):04d}")
        im = ROOT / f"data/raw/atlas/nj_cities/{tag}_{int(sh):04d}.jpg"
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        W, H = Image.open(im).size
        lo0, la0 = CENTRE[d["city"]]; x0, y0 = S.local(lo0, la0)
        T = lambda p: (np.array(p) - [W / 2, H / 2]) * [0.1, -0.1] + [x0, y0]
        pts = [(0, 0), (W, 0), (W, H), (0, H), (W / 2, H / 2)]
        g = []
        for p in pts:
            X, Y = T(p); lo, la = S.lonlat(X, Y); g.append([p[0], p[1], la, lo])
        m = 0.03; cs = [(W * m, H * m), (W * (1 - m), H * m), (W * (1 - m), H * (1 - m)), (W * m, H * (1 - m)), (W * m, H * m)]
        ll = [list(S.lonlat(*T(c))) for c in cs]
        own[str(pid)] = dict(id=pid, name=f"{d['name']} sheet {int(sh)}", year=d["map_year"], imageId=f"{tag}_{int(sh):04d}", uuid=None, url=d["source_url"],
                             gcps=g, mask=dict(type="Polygon", coordinates=[ll]), description=d["atlas"], placeholder=True)
        if not any(str(p["id"]) == str(pid) for p in d["plates"]):
            d["plates"].append(dict(id=pid, sheet=str(int(sh)), name=f"{d['name']} sheet {int(sh)}"))
    own_p.write_text(json.dumps(own)); lay_p.write_text(json.dumps(L, indent=1))

_foot = {}
def city_raster(city, cell):
    key = (city, cell)
    if key in _foot: return _foot[key]
    p = ROOT / f"data/interim/atlas_nj_cities/F_{city}_{cell:g}.npy"
    b = CITY[city]
    x0, y0 = S.local(b[0], b[1]); x1, y1 = S.local(b[2], b[3])
    x0, y0, x1, y1 = [np.floor(v / 100) * 100 for v in (x0, y0, x1 + 100, y1 + 100)]
    tr = Affine(cell, 0, x0, 0, -cell, y1)
    if p.exists():
        F = np.load(p)
    else:
        import duckdb
        fp = ROOT / "data/interim/atlas_nj_cities/nj_footprints.parquet"
        rows = duckdb.sql(f"select geometry from '{fp}' where lon between {b[0]} and {b[2]} and lat between {b[1]} and {b[3]}").fetchall()
        g = shapely.from_wkb([bytes(r[0]) for r in rows])
        g = shapely.transform(g, lambda c: np.column_stack(S.local(c[:, 0], c[:, 1])))
        g = shapely.make_valid(g)
        shp = (int((y1 - y0) / cell), int((x1 - x0) / cell))
        F = features.rasterize([(q, 1) for q in g if not q.is_empty], out_shape=shp, transform=tr, dtype="uint8").astype(np.float32)
        np.save(p, F)
    _foot[key] = (F, tr)
    return F, tr

def load_px(layer, pid):
    d = pickle.load(open(A.WORK / layer / f"{pid}.pkl", "rb"))
    return [wkb.loads(o["px"]) for o in d["items"]]

def tmpl(polys_px, Amat, cell, blur):
    """Raster of the traced mask in metres about its own centre: returns (array, offset of array origin (x_min,y_max) in metres relative to image-centre ground)."""
    g = [shapely.affinity.affine_transform(p, [Amat[0, 0], Amat[0, 1], Amat[1, 0], Amat[1, 1], 0, 0]) for p in polys_px]
    b = shapely.total_bounds(np.array(g, object))
    x0, y1 = np.floor(b[0] / cell) * cell - 2 * cell, np.ceil(b[3] / cell) * cell + 2 * cell
    w = int((np.ceil(b[2] / cell) * cell + 2 * cell - x0) / cell); h = int((y1 - (np.floor(b[1] / cell) * cell - 2 * cell)) / cell)
    T = features.rasterize([(q, 1) for q in g], out_shape=(h, w), transform=Affine(cell, 0, x0, 0, -cell, y1), dtype="uint8").astype(np.float32)
    if blur: T = ndi.gaussian_filter(T, blur / cell)
    return T, (x0, y1)

def amat(theta, s):
    c, sn = np.cos(np.radians(theta)), np.sin(np.radians(theta))
    return s * np.array([[c, -sn], [sn, c]]) @ np.diag([1, -1])   # px (x right, y down) -> E, N, with rotation theta (counter-clockwise)

def ncc(F, T, win):
    T0 = T - T.mean()
    num = signal.fftconvolve(F, T0[::-1, ::-1], mode="valid")
    one = np.ones_like(T)
    s1 = signal.fftconvolve(F, one[::-1, ::-1], mode="valid"); s2 = signal.fftconvolve(F * F, one[::-1, ::-1], mode="valid")
    var = np.maximum(s2 - s1 * s1 / T.size, 1e-6)
    return num / (np.sqrt(var) * np.sqrt((T0 ** 2).sum()) + 1e-9)

def locate(layer, pid, city, prior=None, pr=None, rots=None, scales=None, verbose=True):
    polys = load_px(layer, pid)
    P = A.Plate(layer, pid, verbose=False); W, H = P.img().shape[1], P.img().shape[0]
    polys = [shapely.affinity.translate(p, -W / 2, -H / 2) for p in polys]
    rots = rots if rots is not None else np.arange(-12, 12.1, 3.0)
    scales = scales if scales is not None else [0.097, 0.1, 0.103, 0.106]
    cell = 4.0
    F, tr = city_raster(city, cell); F = ndi.gaussian_filter(F, 1.5)
    if prior is not None:
        # restrict by masking the score map later
        cx, cy = prior
    cand = []
    for th in rots:
        for s in scales:
            T, (ox, oy) = tmpl(polys, amat(th, s), cell, 4.0)
            if T.shape[0] >= F.shape[0] or T.shape[1] >= F.shape[1]: continue
            C = ncc(F, T, None)
            # centre ground of the image for window origin (i, j): window top-left at tr * (j, i); template origin is (ox, oy) rel. centre
            if prior is not None:
                ii, jj = np.mgrid[0:C.shape[0], 0:C.shape[1]]
                gx = tr.c + jj * cell - ox; gy = tr.f - ii * cell - oy
                C = np.where(np.hypot(gx - cx, gy - cy) <= pr, C, -1)
            j = np.unravel_index(np.argmax(C), C.shape)
            cand.append((float(C[j]), th, s, tr.c + j[1] * cell - ox, tr.f - j[0] * cell - oy, C.shape, j))
    cand.sort(reverse=True)
    best = cand[0]
    # lead: best candidate more than 40 m from the best
    lead = next((c[0] for c in cand if np.hypot(c[3] - best[3], c[4] - best[4]) > 40), 0.0)
    if verbose: print(layer, pid, "coarse best", [round(v, 3) if isinstance(v, float) else v for v in best[:5]], "second place (>40 m away) %.3f" % lead, flush=True)
    # fine
    cell = 1.0
    F1, tr1 = city_raster(city, cell); F1 = ndi.gaussian_filter(F1, 1.0)
    sc0, th0, s0, gx0, gy0 = best[:5]
    # window of the fine raster around the coarse position (template extent + 60 m)
    res = []
    for th in np.arange(th0 - 2, th0 + 2.01, 0.5):
        for s in (s0 - 0.003, s0 - 0.0015, s0, s0 + 0.0015, s0 + 0.003):
            T, (ox, oy) = tmpl(polys, amat(th, s), cell, 1.5)
            # sub-raster of F1 around expected window
            wx0 = gx0 + ox - 50; wy1 = gy0 + oy + 50
            i0 = int((tr1.f - wy1) / cell); j0 = int((wx0 - tr1.c) / cell)
            hh, ww = T.shape[0] + 100, T.shape[1] + 100
            i0 = max(0, i0); j0 = max(0, j0)
            sub = F1[i0:i0 + hh, j0:j0 + ww]
            if sub.shape[0] <= T.shape[0] or sub.shape[1] <= T.shape[1]: continue
            C = ncc(sub, T, None)
            j = np.unravel_index(np.argmax(C), C.shape)
            res.append((float(C[j]), th, s, tr1.c + (j0 + j[1]) * cell - ox, tr1.f - (i0 + j[0]) * cell - oy))
    res.sort(reverse=True)
    sc, th, s, gx, gy = res[0]
    if verbose: print(layer, pid, "fine best score %.3f rot %.2f scale %.4f ground centre (%.1f, %.1f)" % (sc, th, s, gx, gy), flush=True)
    return dict(score=sc, coarse=best[0], lead=lead / best[0], rot=th, scale=s, cx=gx, cy=gy)

def write_fit(layer, pid, fit):
    own = jl(own_p); e = own[str(pid)]
    P = A.Plate(layer, pid, verbose=False); W, H = P.img().shape[1], P.img().shape[0]
    Am = amat(fit["rot"], fit["scale"])
    T = lambda p: (Am @ (np.array(p, float) - [W / 2, H / 2])) + [fit["cx"], fit["cy"]]
    pts = [(0, 0), (W, 0), (W, H), (0, H), (W / 2, H / 2), (W / 4, H / 4), (3 * W / 4, H / 4), (3 * W / 4, 3 * H / 4), (W / 4, 3 * H / 4)]
    e["gcps"] = [[p[0], p[1], S.lonlat(*T(p))[1], S.lonlat(*T(p))[0]] for p in pts]
    m = 0.03; cs = [(W * m, H * m), (W * (1 - m), H * m), (W * (1 - m), H * (1 - m)), (W * m, H * (1 - m)), (W * m, H * m)]
    e["mask"] = dict(type="Polygon", coordinates=[[list(S.lonlat(*T(c))) for c in cs]])
    e["placeholder"] = False; e["fit"] = {k: round(float(v), 4) for k, v in fit.items()}
    own_p.write_text(json.dumps(own))

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "add": add(a[1], a[2], a[3:])
    elif a[0] == "layer":   # layer <name> <city> <map_year> <source> <url> <atlas text>
        L = jl(lay_p); L[a[1]] = dict(city=a[2], map_year=int(a[3]), source=a[4], source_url=a[5], atlas=a[6], style="bromley_city", style_override=STYLE, id0=a[7], name=a[8], plates=L.get(a[1], {}).get("plates", []))
        lay_p.write_text(json.dumps(L, indent=1))
    elif a[0] == "locate":
        layer = a[1]; city = jl(lay_p)[layer]["city"]
        prior = None; pr = None
        if "--prior" in a: prior = [float(v) for v in a[a.index("--prior") + 1].split(",")]; pr = float(a[a.index("--pr") + 1])
        for sh in [x for x in a[2:] if x.isdigit()]:
            pid = pid_of(layer, sh)
            f = locate(layer, pid, city, prior, pr)
            write_fit(layer, pid, f)
            print(json.dumps(dict(sheet=sh, **{k: round(float(v), 4) for k, v in f.items()})), flush=True)

def ovr(layer, sheets, out, w=760, items=False):
    """Montage: each sheet reduced to w px wide with today's footprints (cyan) over it (and the traced outlines if items)."""
    from PIL import Image, ImageDraw
    ims = []
    for sh in sheets:
        pid = pid_of(layer, sh); P = A.Plate(layer, pid, verbose=False); img = P.img(); H, W = img.shape[:2]; f = W / w
        im = Image.fromarray(img).resize((w, int(H / f)), Image.LANCZOS); d = ImageDraw.Draw(im, "RGBA")
        cs = P.fwd(np.array([[0, 0], [W, 0], [W, H], [0, H]], float))
        fp, yr, _ = A.footprints((cs[:, 0].min(), cs[:, 1].min(), cs[:, 0].max(), cs[:, 1].max()), pad=10)
        for g in fp:
            for poly in getattr(g, "geoms", [g]):
                if poly.geom_type != "Polygon": continue
                q = P.inv(np.asarray(poly.exterior.coords)) / f
                d.line([tuple(p) for p in q], fill=(0, 170, 255, 255), width=1)
        if items:
            for o in pickle.load(open(A.WORK / layer / f"{pid}.pkl", "rb"))["items"]:
                q = np.asarray(wkb.loads(o["px"]).exterior.coords) / f
                d.line([tuple(p) for p in q], fill=(255, 0, 0, 255), width=1)
        d.text((w // 2, 3), f"sheet {sh}", fill=(255, 0, 0, 255))
        ims.append(im)
    o = Image.new("RGB", (w * len(ims), max(i.height for i in ims)), "white")
    for n, i in enumerate(ims): o.paste(i, (w * n, 0))
    o.save(out); print(out, o.size)
if __name__ == "__main__" and sys.argv[1] == "ov":
    ovr(sys.argv[2], [x for x in sys.argv[4:] if x.isdigit()], sys.argv[3], items="--items" in sys.argv)

def run(layer, tag, item, sheets, rest=False):
    """fetch -> add -> trace -> locate -> refine_buildings for each sheet; one JSON line per sheet in the layer's work folder."""
    import fetch as Fe, io, time
    city = jl(lay_p)[layer]["city"]
    (A.WORK / layer).mkdir(parents=True, exist_ok=True)
    for sh in sheets:
        nm = "%04d" % int(sh); pid = pid_of(layer, sh); t0 = time.time(); rep = dict(sheet=sh, pid=pid)
        try:
            if not (A.WORK / layer / f"{pid}.pkl").exists():
                if not (ROOT / f"data/raw/atlas/nj_cities/{tag}_{nm}.jpg").exists():
                    sys.argv = ["fetch", "get", item, tag, nm]; N = Fe.names(item)
                    import requests
                    from PIL import Image
                    for tr in range(5):
                        try:
                            r = requests.get(N[nm] + "/full/pct:50/0/default.jpg", headers=Fe.UA, timeout=240); r.raise_for_status()
                            Image.open(io.BytesIO(r.content)).convert("RGB").save(ROOT / f"data/raw/atlas/nj_cities/{tag}_{nm}.jpg", quality=92); break
                        except Exception as e:
                            time.sleep(3 + 3 * tr)
                add(layer, tag, [sh])
                A.trace(layer, pid, verbose=False)
            st = pickle.load(open(A.WORK / layer / f"{pid}.pkl", "rb"))["stats"]; rep["n"] = st["n"]
            if st["n"] >= 40:
                pri = os.environ.get("PRIOR"); f = locate(layer, pid, city, prior=[float(v) for v in pri.split(",")[:2]] if pri else None, pr=float(pri.split(",")[2]) if pri else None, verbose=False); write_fit(layer, pid, f); rep.update(fit={k: round(float(v), 3) for k, v in f.items()})
                r = A.refine_buildings(layer, pid, win_m=140.0, min_q=0.2, verbose=False); rep["bld"] = r
                st = pickle.load(open(A.WORK / layer / f"{pid}.pkl", "rb"))["stats"]
                rep.update(coincide=st["coincide"], share=st["share"], off=st.get("off_median_m"))
        except Exception as e:
            rep["error"] = str(e)[:200]
        rep["sec"] = round(time.time() - t0)
        with open(A.WORK / layer / "log.jsonl", "a") as fh: fh.write(json.dumps(rep) + "\n")
        print(json.dumps(rep), flush=True)
if __name__ == "__main__" and sys.argv[1] == "run":
    run(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
