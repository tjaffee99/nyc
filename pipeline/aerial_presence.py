"""Did a building stand on each of today's footprints in 1924 and in 1951?

Evidence: the city's two historical aerial mosaics (NYC OTI, "NYC Orthos 1924" and "NYC Orthos
1951", public hosted tile layers of the city's ArcGIS Online account; see
data/manual/aerial/README.md for the source, the terms and the validation).

One idempotent stage in four steps, each cached:

    python aerial_presence.py tiles      # fetch the z17 tiles under the footprints (cached, never re-fetched)
    python aerial_presence.py features   # per z14 block: registration offset + per-footprint image features
    python aerial_presence.py model      # train / validate on the recorded-year buildings (district hold-out)
    python aerial_presence.py predict    # data/manual/aerial/presence.parquet
    python aerial_presence.py            # all four

Memory: one z14 block (8 x 8 tiles of 256 px, plus a one-tile margin) is processed at a time.
"""
from __future__ import annotations

import io
import json
import os
import math
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")       # several workers; one thread each
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
import requests

from common import INTERIM, MANUAL, RAW, log

# ----------------------------------------------------------------------------- sources
ARCGIS = "https://tiles.arcgis.com/tiles/yG5s3afENB5iO9fj/arcgis/rest/services"
SERVICES = {1924: "Ortho_1924_Mosaic", 1951: "NYC_Orthos_1951"}
YEARS = (1924, 1951)
USER_AGENT = "NYCThroughTime-research/0.1"
Z = 17                 # tile zoom fetched (0.905 m per pixel at 40.7 N)
ZB = 14                # block zoom: one block = 8 x 8 tiles
NB = 2 ** (Z - ZB)
TILE = 256

TILE_DIR = RAW / "aerial"
WORK = INTERIM / "aerial"
OUT_DIR = MANUAL / "aerial"
BUILDINGS = INTERIM / "nyc_buildings.parquet"

_session = None


def session() -> requests.Session:
    """One keep-alive connection for the whole run."""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers["User-Agent"] = USER_AGENT
        ad = requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=0)
        _session.mount("https://", ad)
    return _session


# ----------------------------------------------------------------------------- tile maths
def lonlat_to_pixel(lon, lat, z=Z):
    """Global pixel coordinates (float) of the web-mercator pyramid at zoom z."""
    n = TILE * 2.0 ** z
    x = (np.asarray(lon, dtype="float64") + 180.0) / 360.0 * n
    s = np.sin(np.radians(np.asarray(lat, dtype="float64")))
    y = (0.5 - np.log((1 + s) / (1 - s)) / (4 * math.pi)) * n
    return x, y


def metres_per_pixel(lat, z=Z):
    return 156543.03392804097 * math.cos(math.radians(lat)) / 2 ** z


# ----------------------------------------------------------------------------- tile cache
def tile_path(year: int, z: int, x: int, y: int):
    d = TILE_DIR / str(year) / str(z) / str(x)
    for ext in ("jpg", "png", "404"):
        p = d / f"{y}.{ext}"
        if p.exists():
            return p
    return None


def fetch_tile(year: int, z: int, x: int, y: int, pause: float = 0.0):
    """Path of the cached tile (a .404 marker when the service has none). Fetches at most once."""
    p = tile_path(year, z, x, y)
    if p is not None:
        return p
    d = TILE_DIR / str(year) / str(z) / str(x)
    d.mkdir(parents=True, exist_ok=True)
    url = f"{ARCGIS}/{SERVICES[year]}/MapServer/tile/{z}/{y}/{x}"
    last = None
    for attempt in range(5):
        try:
            r = session().get(url, timeout=30)
        except requests.RequestException as e:  # connection reset: wait and retry on a new connection
            last = e
            time.sleep(2 + 3 * attempt)
            continue
        if r.status_code == 200 and r.content[:3] == b"\xff\xd8\xff":
            p = d / f"{y}.jpg"
        elif r.status_code == 200 and r.content[:4] == b"\x89PNG":
            p = d / f"{y}.png"
        elif r.status_code == 404:
            p = d / f"{y}.404"
            p.write_bytes(b"")
            return p
        elif r.status_code in (429, 500, 502, 503, 504):
            last = r.status_code
            time.sleep(5 + 10 * attempt)
            continue
        else:
            raise RuntimeError(f"unexpected answer {r.status_code} for {url}")
        tmp = p.with_suffix(p.suffix + ".part")
        tmp.write_bytes(r.content)
        tmp.rename(p)
        if pause:
            time.sleep(pause)
        return p
    raise RuntimeError(f"tile {url} failed five times: {last}")


def read_tile(year: int, z: int, x: int, y: int):
    """(grey uint8 256x256, valid bool 256x256) or None when the tile is not cached / missing.
    Valid = the mosaic has a photograph there (opaque and not the blank fill)."""
    from PIL import Image
    p = tile_path(year, z, x, y)
    if p is None or p.suffix == ".404":
        return None
    im = Image.open(p)
    if im.mode in ("P", "LA", "RGBA", "PA") or "transparency" in im.info:
        rgba = np.asarray(im.convert("RGBA"))
        grey = (rgba[..., :3].astype("float32") @ np.array([0.299, 0.587, 0.114], dtype="float32"))
        valid = rgba[..., 3] > 200
    else:
        grey = np.asarray(im.convert("L")).astype("float32")
        valid = np.ones(grey.shape, bool)
    return grey, valid


# ----------------------------------------------------------------------------- blocks
PAD = 1  # tiles of margin around a block


def load_block(year: int, bx: int, by: int):
    """Mosaic of a z14 block with a one-tile margin: (grey float32, valid bool, x0, y0) where
    x0, y0 are the global pixel coordinates of the array's corner. None if no tile is cached."""
    n = NB + 2 * PAD
    grey = np.zeros((n * TILE, n * TILE), "float32")
    valid = np.zeros((n * TILE, n * TILE), bool)
    tx0, ty0 = bx * NB - PAD, by * NB - PAD
    got = 0
    for i in range(n):
        for j in range(n):
            t = read_tile(year, Z, tx0 + i, ty0 + j)
            if t is None:
                continue
            grey[j * TILE:(j + 1) * TILE, i * TILE:(i + 1) * TILE] = t[0]
            valid[j * TILE:(j + 1) * TILE, i * TILE:(i + 1) * TILE] = t[1]
            got += 1
    if not got:
        return None
    return grey, valid, tx0 * TILE, ty0 * TILE


def block_lonlat(bx: int, by: int, pad_tiles: float = 0.0):
    """lon_min, lat_min, lon_max, lat_max of a z14 block (optionally grown by tiles of zoom Z)."""
    n = 2.0 ** Z

    def lon(x):
        return x / n * 360.0 - 180.0

    def lat(y):
        return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    xa, xb = bx * NB - pad_tiles, (bx + 1) * NB + pad_tiles
    ya, yb = by * NB - pad_tiles, (by + 1) * NB + pad_tiles
    return lon(xa), lat(yb), lon(xb), lat(ya)


_con = None
SNAPSHOT = WORK / "footprints.parquet"


def snapshot():
    """The standing footprints, copied once from nyc_buildings.parquet (which every rebuild of the
    buildings rewrites - a block read in the middle of that would fail or mix two versions)."""
    import duckdb
    if SNAPSHOT.exists():
        return SNAPSHOT
    WORK.mkdir(parents=True, exist_ok=True)
    tmp = SNAPSHOT.with_suffix(".part")
    n = 2.0 ** ZB
    for attempt in range(6):
        try:
            con = duckdb.connect()
            con.execute("set memory_limit='1500MB'")
            con.execute(f"""copy (
                select doitt_id, bin, boro, lon, lat, start_year, year_src, year_confidence, raw_year, height_m, area,
                       ST_AsWKB(geometry) as wkb,
                       cast(floor((lon + 180) / 360 * {n}) as integer) as bkx,
                       cast(floor((0.5 - ln(tan(radians(lat)) + 1 / cos(radians(lat))) / (2 * pi())) * {n}) as integer) as bky
                from '{BUILDINGS}' where end_year = 9999 and doitt_id is not null
                order by bkx, bky) to '{tmp}' (format parquet, row_group_size 20000)""")
            break
        except (duckdb.IOException, duckdb.InvalidInputException) as e:  # the file is being rewritten: wait and retry
            log(f"snapshot: {str(e)[:120]} - retry in 60 s")
            time.sleep(60)
    else:
        raise RuntimeError("could not read nyc_buildings.parquet")
    tmp.rename(SNAPSHOT)
    return SNAPSHOT


def block_footprints(bx: int, by: int, pad_tiles: float = 0.0):
    """Standing footprints whose centre lies in the block (grown by `pad_tiles`): DataFrame with
    shapely geometry in global pixel coordinates of zoom Z (column `geom_px`)."""
    import duckdb
    import shapely
    global _con
    if _con is None:
        _con = duckdb.connect()
        _con.execute("set memory_limit='1GB'")
    lo0, la0, lo1, la1 = block_lonlat(bx, by, pad_tiles)
    df = _con.execute(f"""
        select doitt_id, bin, boro, lon, lat, start_year, year_src, year_confidence, raw_year, height_m, area, wkb
        from '{snapshot()}'
        where bkx between {bx - 1} and {bx + 1} and bky between {by - 1} and {by + 1}
          and lon >= {lo0} and lon < {lo1} and lat >= {la0} and lat < {la1}""").fetchdf()
    if len(df) == 0:
        df["geom_px"] = []
        return df
    g = shapely.from_wkb(df.pop("wkb").map(bytes).values)

    def tr(c):
        x, y = lonlat_to_pixel(c[:, 0], c[:, 1])
        return np.column_stack([x, y])
    df["geom_px"] = shapely.transform(g, tr)
    return df


# ----------------------------------------------------------------------------- pixel layers
MARGIN = 64       # pixels kept around a block (58 m): rings and context of the footprints at its edge
K_TEX = 32        # texture dictionary size
N_RESP = 6


def pixel_layers(g, valid):
    """Per-pixel layers shared by registration, features and the texture dictionary (float32):
    z = brightness as a local z-score (exposure differs from frame to frame), gradient of z."""
    from scipy import ndimage as ndi
    vf = valid.astype("float32")
    k = 101
    wv = ndi.uniform_filter(vf, k) + 1e-6
    mu = ndi.uniform_filter(g * vf, k) / wv
    sd = np.sqrt(np.maximum(ndi.uniform_filter(g * g * vf, k) / wv - mu * mu, 0)) + 4.0
    z = ((g - mu) / sd).astype("float32")
    z1 = ndi.gaussian_filter(z, 1.0)
    gx = ndi.sobel(z1, 1) / 8.0
    gy = ndi.sobel(z1, 0) / 8.0
    return {"z": z, "z1": z1, "gx": gx, "gy": gy, "G": np.hypot(gx, gy), "mu": mu, "sd": sd}


def responses(P):
    """Filter responses for the texture dictionary (6 channels): brightness at two scales, edge
    strength, blobs at two scales, fine texture."""
    from scipy import ndimage as ndi
    z = P["z"]
    R = np.empty((N_RESP,) + z.shape, "float32")
    R[0] = P["z1"]
    R[1] = ndi.gaussian_filter(P["z1"], 2.8)
    R[2] = P["G"] * 4.0
    R[3] = ndi.gaussian_laplace(z, 1.5) * 4.0
    R[4] = ndi.gaussian_laplace(z, 3.0) * 12.0
    m = ndi.uniform_filter(z, 5)
    R[5] = np.sqrt(np.maximum(ndi.uniform_filter(z * z, 5) - m * m, 0)) * 2.0
    return R


def texton_path(year: int) -> Path:
    return WORK / f"textons_{year}.npy"


def train_textons(year: int, n_blocks: int = 24, per_block: int = 10000, seed: int = 7):
    """k-means dictionary of the filter responses, from a fixed random sample of cached blocks."""
    out = texton_path(year)
    if out.exists():
        return np.load(out)
    t = tile_list()
    rng = np.random.default_rng(seed)
    blocks = sorted(set(zip(t.bx, t.by)))
    rng.shuffle(blocks)
    X = []
    for bx, by in blocks:
        if len(X) >= n_blocks:
            break
        if any(tile_path(year, Z, bx * NB + i, by * NB + i) is None for i in (1, 3, 6)):
            continue
        blk = load_block(year, bx, by)
        if blk is None:
            continue
        g, valid, _, _ = blk
        g, valid = g[::1, ::1][:1280, :1280], valid[:1280, :1280]     # a quarter of the block is plenty
        valid = blank_mask(g, valid)
        if valid.mean() < 0.5:
            continue
        R = responses(pixel_layers(g, valid))
        idx = rng.choice(np.flatnonzero(valid.ravel()), per_block, replace=False)
        X.append(R.reshape(N_RESP, -1)[:, idx].T.copy())
    X = np.concatenate(X).astype("float32")
    X = np.clip(X, -6, 6)
    C = X[rng.choice(len(X), K_TEX, replace=False)].copy()
    for _ in range(20):
        a = np.argmin((C * C).sum(1)[None, :] - 2.0 * (X @ C.T), axis=1)
        for k in range(K_TEX):
            if (a == k).any():
                C[k] = X[a == k].mean(0)
    C = C[np.argsort(C[:, 0])]           # dark to bright, so that the dictionary reads easily
    WORK.mkdir(parents=True, exist_ok=True)
    np.save(out, C)
    log(f"textons {year}: dictionary of {K_TEX} from {len(X)} pixels")
    return C


def assign_textons(R, C, chunk=500000):
    """Index of the nearest dictionary entry for every pixel."""
    shp = R.shape[1:]
    X = R.reshape(N_RESP, -1)
    out = np.empty(X.shape[1], "uint8")
    c2 = (C * C).sum(1)
    for a in range(0, X.shape[1], chunk):
        x = np.clip(X[:, a:a + chunk].T, -6, 6)
        out[a:a + chunk] = np.argmin(c2[None, :] - 2.0 * (x @ C.T), axis=1)
    return out.reshape(shp)


# ----------------------------------------------------------------------------- registration
REG_R = 10      # search radius, pixels (9 m)
REG_CELL = 512  # cell size, pixels (463 m)
REG_Z = 3.5     # a cell's peak counts when it stands this many sigmas above its correlation surface


def estimate_offset(G, valid, geoms, use):
    """Shift (dx, dy) in pixels by which the photograph is displaced against today's outlines:
    the peak of the correlation between the gradient magnitude and the outlines of the
    buildings thought to stand (`use`), per 512-pixel cell; the block's offset is the median of
    the cells with a clear peak (none applied with fewer than three). Returns dx, dy, clear cells."""
    import shapely
    from rasterio import features
    from scipy import ndimage as ndi
    if use.sum() < 30:
        return 0.0, 0.0, 0
    O = features.rasterize([(b, 1) for b in shapely.boundary(geoms[use])], out_shape=G.shape, fill=0,
                           dtype="uint8", all_touched=True).astype("float32")
    O = ndi.gaussian_filter(O, 0.7)
    Gn = G / (ndi.uniform_filter(G, 41) + 0.02)
    R = REG_R
    good = []
    for j in range(NB * TILE // REG_CELL):
        for i in range(NB * TILE // REG_CELL):
            sl = (slice(MARGIN + j * REG_CELL, MARGIN + (j + 1) * REG_CELL), slice(MARGIN + i * REG_CELL, MARGIN + (i + 1) * REG_CELL))
            if valid[sl].mean() < 0.9 or O[sl].sum() < 300:
                continue
            a, b = Gn[sl], O[sl]
            c = np.fft.irfft2(np.fft.rfft2(a - a.mean()) * np.conj(np.fft.rfft2(b - b.mean())), s=a.shape)
            c = np.roll(np.roll(c, R, 0), R, 1)[:2 * R + 1, :2 * R + 1]
            k = np.unravel_index(c.argmax(), c.shape)
            zc = (c.max() - np.median(c)) / (c.std() + 1e-9)
            if zc >= REG_Z and abs(k[1] - R) < R and abs(k[0] - R) < R:
                good.append((int(k[1] - R), int(k[0] - R)))
    if len(good) < 3:
        return 0.0, 0.0, len(good)
    return float(np.median([c[0] for c in good])), float(np.median([c[1] for c in good])), len(good)


# ----------------------------------------------------------------------------- features
RING = 3.0        # ring width outside the outline, pixels
FAR = 8.0         # outer ring, pixels
SHIFT = 3         # the outline score is also searched over +-SHIFT pixels
FEATS = ["in_mean", "in_std", "ring_mean", "ring_std", "far_mean", "far_std", "d_in_ring", "ad_in_ring",
         "band_grad", "far_grad", "band_far", "ctx_grad100", "ctx_std30", "ctx_std100",
         "rect4", "aniso2", "s0", "smax", "speak", "bright", "contrast"]
TEX_FEATS = [f"{w}_t{k:02d}" for w in ("in", "ring", "far", "ctx") for k in range(K_TEX)]
GEOM = ["log_area", "compact", "ring_share", "cov30", "cov100"]


def block_features(g, valid, P, geoms, C):
    """Image features of every footprint (`geoms`, in the array's pixel coordinates, already
    shifted onto the photograph). Returns dict name -> array, with `cover` (share of the
    footprint and its ring that the mosaic covers)."""
    import shapely
    from rasterio import features
    from scipy import ndimage as ndi
    n = len(geoms)
    N = n + 1
    H, W = g.shape
    L = features.rasterize([(gm, i + 1) for i, gm in enumerate(geoms)], out_shape=g.shape, fill=0, dtype="int32")
    cnt = np.bincount(L.ravel(), minlength=N)
    small = np.where(cnt[1:] < 4)[0]
    if len(small):  # footprints thinner than a pixel: take every pixel they touch, where nothing else is
        L2 = features.rasterize([(geoms[i], i + 1) for i in small], out_shape=g.shape, fill=0, dtype="int32", all_touched=True)
        L = np.where((L == 0) & (L2 > 0), L2, L)
    built = L > 0
    dist, (iy, ix) = ndi.distance_transform_edt(~built, return_indices=True)
    near = L[iy, ix]
    del iy, ix
    outside = ~built
    # zone code per pixel: 0 inside, 1 ring, 2 far; one label array for all three
    zone = np.where(built, 0, np.where(dist <= RING, 1, np.where(dist <= FAR, 2, 3))).astype("int64")
    lab = np.where(built, L, near).astype("int64")
    sel = np.flatnonzero((zone < 3).ravel())
    zl = zone.ravel()[sel] * N + lab.ravel()[sel]          # zone * N + label
    N3 = 3 * N

    def zsum(img):
        return np.bincount(zl, weights=img.ravel()[sel], minlength=N3)[:N3].reshape(3, N)[:, 1:]

    c = np.bincount(zl, minlength=N3)[:N3].reshape(3, N)[:, 1:].astype("float64")
    z = P["z"]
    G = P["G"]
    out = {}
    with np.errstate(invalid="ignore", divide="ignore"):
        m = zsum(z) / c
        sdv = np.sqrt(np.maximum(zsum(z * z) / c - m * m, 0))
        gm_ = zsum(G) / c
    out.update(in_mean=m[0], in_std=sdv[0], ring_mean=m[1], ring_std=sdv[1], far_mean=m[2], far_std=sdv[2],
               d_in_ring=m[0] - m[1], ad_in_ring=np.abs(m[0] - m[1]), far_grad=gm_[2])

    # the band along the outline: boundary pixels inside, and the first pixel outside
    inner = ndi.minimum_filter(L, 3) == ndi.maximum_filter(L, 3)
    bandL = np.where(built & ~inner, L, np.where(outside & (dist <= 1.5), near, 0))
    bidx = np.flatnonzero(bandL.ravel())
    blab = bandL.ravel()[bidx]
    bcnt = np.bincount(blab, minlength=N)[:N].astype("float64")
    Gf = G.ravel()
    S = np.zeros(((2 * SHIFT + 1) ** 2, n), "float32")
    q = 0
    for dy in range(-SHIFT, SHIFT + 1):
        for dx in range(-SHIFT, SHIFT + 1):
            j = np.clip(bidx + dy * W + dx, 0, Gf.size - 1)
            with np.errstate(invalid="ignore", divide="ignore"):
                S[q] = (np.bincount(blab, weights=Gf[j], minlength=N)[:N] / bcnt)[1:]
            q += 1
    s0 = S[S.shape[0] // 2]
    out["band_grad"] = s0
    out["band_far"] = s0 / (gm_[2] + 0.02)
    out["s0"] = s0
    out["smax"] = S.max(0)
    out["speak"] = S.max(0) - S.mean(0)

    # context sampled at the centre of the footprint
    cen = shapely.centroid(geoms)
    cx = np.clip(shapely.get_x(cen).astype(int), 0, W - 1)
    cy = np.clip(shapely.get_y(cen).astype(int), 0, H - 1)
    out["ctx_grad100"] = ndi.uniform_filter(G, 111)[cy, cx]
    for kk, nm in ((33, "ctx_std30"), (111, "ctx_std100")):
        mm = ndi.uniform_filter(z, kk)
        out[nm] = np.sqrt(np.maximum(ndi.uniform_filter(z * z, kk) - mm * mm, 0))[cy, cx]
    gv = g[valid]
    p10, p50, p90 = np.percentile(gv[::11], [10, 50, 90]) if gv.size > 1000 else (0, 0, 1)
    c0 = max(float(p90 - p10), 10.0)
    out["bright"] = ((P["mu"] - p50) / c0)[cy, cx]
    out["contrast"] = (P["sd"] / c0)[cy, cx]
    bf = built.astype("float32")
    out["cov30"] = ndi.uniform_filter(bf, 33)[cy, cx]
    out["cov100"] = ndi.uniform_filter(bf, 111)[cy, cx]

    # straight edges along the building's own axes (2- and 4-fold harmonics of the gradient direction)
    gx, gy = P["gx"], P["gy"]
    m2 = gx * gx + gy * gy
    q2c = gx * gx - gy * gy
    q2s = 2 * gx * gy
    q4c = (q2c * q2c - q2s * q2s) / (m2 + 1e-9)
    q4s = 2 * q2c * q2s / (m2 + 1e-9)
    sm2 = zsum(m2)[:2].sum(0) + 1e-9
    a4, b4, a2, b2 = (zsum(q)[:2].sum(0) for q in (q4c, q4s, q2c, q2s))
    mrr = shapely.minimum_rotated_rectangle(geoms)
    rc = shapely.get_coordinates(shapely.get_exterior_ring(mrr)).reshape(-1, 5, 2) if all(r.geom_type == "Polygon" for r in mrr) else None
    if rc is not None:
        e1, e2 = rc[:, 1] - rc[:, 0], rc[:, 2] - rc[:, 1]
        e = np.where(((e1 ** 2).sum(1) >= (e2 ** 2).sum(1))[:, None], e1, e2)
        theta = np.arctan2(e[:, 1], e[:, 0])
    else:
        theta = np.zeros(n)
    out["rect4"] = (a4 * np.cos(4 * theta) + b4 * np.sin(4 * theta)) / sm2
    out["aniso2"] = np.hypot(a2, b2) / sm2

    # texture words: shares of the dictionary entries inside, in the ring, further out, and ~18 m around
    tex = assign_textons(responses(P), C).astype("int64")
    hcount = np.bincount(zl * K_TEX + tex.ravel()[sel], minlength=N3 * K_TEX)[:N3 * K_TEX].reshape(3, N, K_TEX)[:, 1:].astype("float32")
    with np.errstate(invalid="ignore", divide="ignore"):
        hcount = hcount / hcount.sum(2, keepdims=True)
    for zi, nm in enumerate(("in", "ring", "far")):
        for k_ in range(K_TEX):
            out[f"{nm}_t{k_:02d}"] = hcount[zi, :, k_]
    cs = 8
    hc, wc = H // cs, W // cs
    cell = (np.arange(hc * cs)[:, None] // cs) * wc + (np.arange(wc * cs)[None, :] // cs)
    ch = np.bincount((cell * K_TEX + tex[:hc * cs, :wc * cs]).ravel(), minlength=hc * wc * K_TEX).reshape(hc, wc, K_TEX).astype("float32")
    ch = ndi.uniform_filter(ch, size=(5, 5, 1))
    ch /= ch.sum(2, keepdims=True) + 1e-9
    cc = ch[np.clip(cy // cs, 0, hc - 1), np.clip(cx // cs, 0, wc - 1)]
    for k_ in range(K_TEX):
        out[f"ctx_t{k_:02d}"] = cc[:, k_]

    # geometry of today's footprint (not evidence in itself; it tells how much the image can say)
    area = shapely.area(geoms)
    per = shapely.length(geoms)
    out["log_area"] = np.log(np.maximum(area, 1.0))
    out["compact"] = 4 * math.pi * area / np.maximum(per, 1.0) ** 2
    out["ring_share"] = c[1] / np.maximum(per * RING, 1.0)

    # coverage: share of the footprint and ring with a photograph
    out["cover"] = zsum(valid.astype("float32"))[:2].sum(0) / np.maximum(c[:2].sum(0), 1)
    return out


def blank_mask(g, valid):
    """The mosaics pad missing photographs with a flat fill (and the 1924 tiles are JPEG without
    transparency): a pixel is blank when its 9 x 9 surroundings are flat and extreme."""
    from scipy import ndimage as ndi
    m = ndi.uniform_filter(g, 9)
    sd = np.sqrt(np.maximum(ndi.uniform_filter(g * g, 9) - m * m, 0))
    blank = (sd < 1.0) & ((m < 4) | (m > 251))
    blank = ndi.binary_dilation(ndi.binary_opening(blank, iterations=2), iterations=3)
    return valid & ~blank


META = ["doitt_id", "bin", "boro", "lon", "lat", "start_year", "year_src", "year_confidence", "raw_year", "height_m", "area"]


def process_block_year(year: int, bx: int, by: int, apply_offset: bool = True):
    """Features of one year for the footprints centred in the block (None: no footprints)."""
    import pandas as pd
    import shapely
    df = block_footprints(bx, by, pad_tiles=MARGIN / TILE)
    if len(df) == 0:
        return None
    lo0, la0, lo1, la1 = block_lonlat(bx, by)
    inblock = ((df.lon >= lo0) & (df.lon < lo1) & (df.lat >= la0) & (df.lat < la1)).values
    if not inblock.any():
        return None
    res = df.loc[inblock, META].reset_index(drop=True)
    res["bx"] = np.int32(bx)
    res["by"] = np.int32(by)
    blk = load_block(year, bx, by)
    names = FEATS + TEX_FEATS + GEOM + ["cover"]
    if blk is None:
        cols = {f: np.full(len(res), np.nan, "float32") for f in names}
        cols["cover"][:] = 0
        dx = dy = ngood = 0.0
    else:
        g, valid, x0, y0 = blk
        cut = PAD * TILE - MARGIN
        g, valid = g[cut:-cut, cut:-cut], valid[cut:-cut, cut:-cut]
        x0, y0 = x0 + cut, y0 + cut
        valid = blank_mask(g, valid)
        P = pixel_layers(g, valid)
        geoms = shapely.transform(df.geom_px.values, lambda c: c - np.array([x0, y0], "float64"))
        dx = dy = ngood = 0.0
        if apply_offset:
            use = (df.start_year.values <= year - 1) & (df.area.values > 60)
            dx, dy, ngood = estimate_offset(P["G"], valid, geoms, use)
            if dx or dy:
                geoms = shapely.transform(geoms, lambda c: c + np.array([dx, dy]))
        f = block_features(g, valid, P, geoms, train_textons(year))
        cols = {name: f[name][inblock].astype("float32") for name in names}
    cols["offx"] = np.full(len(res), dx, "float32")
    cols["offy"] = np.full(len(res), dy, "float32")
    cols["reg_cells"] = np.full(len(res), ngood, "float32")
    return pd.concat([res, pd.DataFrame(cols)], axis=1)


def feature_path(year: int, bx: int, by: int) -> Path:
    return WORK / "features" / str(year) / f"{bx}_{by}.parquet"


def _block_job(job):
    year, bx, by = job
    out = feature_path(year, bx, by)
    if out.exists():
        return job, 0
    res = process_block_year(year, bx, by)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".part")
    if res is None:
        import pandas as pd
        res = pd.DataFrame({"doitt_id": []})
    res.to_parquet(tmp)
    tmp.rename(out)
    return job, len(res)


def step_features(workers: int = 3, follow: bool = False):
    """Every block-year whose tiles (with the margin) are all cached. With `follow`, waits for a
    running `tiles` step and goes on until every block is done."""
    from multiprocessing import Pool
    t = tile_list()
    blocks = sorted(set(zip(t.bx, t.by)), key=lambda b: (BORO_ORDER.index(t[(t.bx == b[0]) & (t.by == b[1])].bboro.iloc[0]), b))
    need = {}
    tset = set(zip(t.x, t.y))
    for bx, by in blocks:
        need[(bx, by)] = [(x, y) for x in range(bx * NB - PAD, (bx + 1) * NB + PAD) for y in range(by * NB - PAD, (by + 1) * NB + PAD) if (x, y) in tset]
    while True:
        todo, waiting = [], 0
        for year in YEARS:
            for b in blocks:
                if feature_path(year, *b).exists():
                    continue
                if all(tile_path(year, Z, x, y) is not None for x, y in need[b]):
                    todo.append((year, b[0], b[1]))
                else:
                    waiting += 1
        if todo:
            log(f"features: {len(todo)} block-years ready, {waiting} waiting for tiles")
            with Pool(workers) as pool:
                for k, (job, n) in enumerate(pool.imap_unordered(_block_job, todo)):
                    if k % 20 == 0:
                        log(f"  {k}/{len(todo)} {job} {n} footprints")
        if not waiting:
            break
        if not follow:
            log(f"features: {waiting} block-years still wait for tiles (run `tiles` first)")
            break
        time.sleep(30)
    log("features: done")


# ----------------------------------------------------------------------------- model
class GBM:
    """Gradient-boosted trees on histograms (logistic loss), numpy only: the build machine's
    environment has no scikit-learn. Level-wise trees of fixed depth; NaN is its own (last) bin."""

    def __init__(self, n_trees=300, depth=5, lr=0.08, min_hess=20.0, lam=2.0, subsample=0.5, colsample=0.7, n_bins=64, seed=0):
        self.n_trees, self.depth, self.lr, self.min_hess, self.lam = n_trees, depth, lr, min_hess, lam
        self.subsample, self.colsample, self.n_bins, self.seed = subsample, colsample, n_bins, seed

    def bin(self, X):
        Xb = np.empty(X.shape, "uint8")
        for f in range(X.shape[1]):
            col = X[:, f]
            b = np.searchsorted(self.edges[f], col, side="right").astype("uint8")
            b[np.isnan(col)] = self.n_bins
            Xb[:, f] = b
        return Xb

    def fit(self, X, y, w):
        rng = np.random.default_rng(self.seed)
        n, F = X.shape
        self.edges = []
        for f in range(F):
            col = X[:, f]
            col = col[~np.isnan(col)]
            q = np.unique(np.quantile(col[:: max(1, len(col) // 200000)], np.linspace(0, 1, self.n_bins + 1)[1:-1])) if len(col) else np.array([0.0])
            self.edges.append(q.astype("float64"))
        Xb = self.bin(X)
        NB1 = self.n_bins + 1
        y = y.astype("float64")
        w = w.astype("float64")
        self.base = float(np.log((w * y).sum() / (w * (1 - y)).sum()))
        Fx = np.full(n, self.base)
        nn_all = 2 ** (self.depth + 1) - 1
        self.feat = np.zeros((self.n_trees, nn_all), "int16")
        self.thr = np.full((self.n_trees, nn_all), 255, "uint8")
        self.val = np.zeros((self.n_trees, nn_all), "float32")
        self.gain = np.zeros(F)
        for t in range(self.n_trees):
            pr = 1.0 / (1.0 + np.exp(-Fx))
            rows = np.flatnonzero(rng.random(n) < self.subsample)
            g = (w * (pr - y))[rows]
            h = (w * pr * (1 - pr))[rows]
            feats = np.sort(rng.choice(F, max(1, int(round(F * self.colsample))), replace=False))
            node = np.zeros(len(rows), "int64")
            Xs = Xb[rows]
            for level in range(self.depth):
                nn = 2 ** level
                off = nn - 1
                loc = node - off
                best_gain = np.zeros(nn)
                best_f = np.zeros(nn, "int64")
                best_t = np.full(nn, 255, "int64")
                Gt = np.bincount(loc, weights=g, minlength=nn)
                Ht = np.bincount(loc, weights=h, minlength=nn)
                parent = Gt * Gt / (Ht + self.lam)
                for f in feats:
                    key = loc * NB1 + Xs[:, f]
                    GL = np.bincount(key, weights=g, minlength=nn * NB1).reshape(nn, NB1).cumsum(1)[:, :-1]
                    HL = np.bincount(key, weights=h, minlength=nn * NB1).reshape(nn, NB1).cumsum(1)[:, :-1]
                    GR = Gt[:, None] - GL
                    HR = Ht[:, None] - HL
                    gain = GL * GL / (HL + self.lam) + GR * GR / (HR + self.lam) - parent[:, None]
                    gain[(HL < self.min_hess) | (HR < self.min_hess)] = 0
                    bt = gain.argmax(1)
                    bg = gain[np.arange(nn), bt]
                    upd = bg > best_gain
                    best_gain[upd] = bg[upd]
                    best_f[upd] = f
                    best_t[upd] = bt[upd]
                self.feat[t, off:off + nn] = best_f
                self.thr[t, off:off + nn] = best_t
                np.add.at(self.gain, best_f[best_gain > 0], best_gain[best_gain > 0])
                node = 2 * node + 1 + (Xs[np.arange(len(rows)), best_f[loc]] > best_t[loc])
            off = 2 ** self.depth - 1
            loc = node - off
            nl = 2 ** self.depth
            leaf = -np.bincount(loc, weights=g, minlength=nl) / (np.bincount(loc, weights=h, minlength=nl) + self.lam) * self.lr
            self.val[t, off:off + nl] = leaf
            Fx += self._tree(Xb, t)
        return self

    def _tree(self, Xb, t):
        node = np.zeros(Xb.shape[0], "int64")
        ar = np.arange(Xb.shape[0])
        for _ in range(self.depth):
            node = 2 * node + 1 + (Xb[ar, self.feat[t, node]] > self.thr[t, node])
        return self.val[t, node].astype("float64")

    def decision(self, X, chunk=200000):
        out = np.empty(X.shape[0])
        for a in range(0, X.shape[0], chunk):
            Xb = self.bin(X[a:a + chunk])
            s = np.full(Xb.shape[0], self.base)
            for t in range(self.n_trees):
                s += self._tree(Xb, t)
            out[a:a + chunk] = s
        return out


def auc(y, s, w=None):
    """Weighted area under the ROC curve."""
    o = np.argsort(s, kind="stable")
    y, s = y[o], s[o]
    w = np.ones(len(y)) if w is None else w[o]
    wp, wn = w * y, w * (1 - y)
    # ties: average rank
    _, inv, cnt = np.unique(s, return_inverse=True, return_counts=True)
    cn = np.bincount(inv, weights=wn)
    below = np.concatenate([[0], np.cumsum(cn)[:-1]])
    return float((np.bincount(inv, weights=wp) * (below + cn / 2)).sum() / (wp.sum() * wn.sum() + 1e-12))


def isotonic(score, y, w, knots=120):
    """Monotone calibration (pool-adjacent-violators on quantile bins): (x knots, p knots)."""
    o = np.argsort(score)
    score, y, w = score[o], y[o], w[o]
    cw = np.cumsum(w)
    b = np.minimum((cw / cw[-1] * knots).astype(int), knots - 1)
    sw = np.bincount(b, weights=w, minlength=knots)
    keep = sw > 0
    xs = (np.bincount(b, weights=w * score, minlength=knots)[keep] / sw[keep]).tolist()
    ps = (np.bincount(b, weights=w * y, minlength=knots)[keep] / sw[keep]).tolist()
    ws = sw[keep].tolist()
    i = 0
    while i < len(ps) - 1:
        if ps[i] > ps[i + 1]:
            tot = ws[i] + ws[i + 1]
            ps[i] = (ps[i] * ws[i] + ps[i + 1] * ws[i + 1]) / tot
            xs[i] = (xs[i] * ws[i] + xs[i + 1] * ws[i + 1]) / tot
            ws[i] = tot
            del ps[i + 1], xs[i + 1], ws[i + 1]
            i = max(i - 1, 0)
        else:
            i += 1
    return np.array(xs), np.clip(np.array(ps), 0.005, 0.995)


MODEL_FEATS = FEATS + TEX_FEATS + ["log_area", "compact", "ring_share"]
GEOM_ONLY = ["log_area", "compact", "ring_share", "cov30", "cov100"]
GAP = 2            # recorded years within +-GAP of the photograph are not used as labels
COVER_MIN = 0.95   # the mosaic must cover this share of footprint and ring


def load_features(year: int, blocks=None):
    import pandas as pd
    files = sorted((WORK / "features" / str(year)).glob("*.parquet"))
    if blocks is not None:
        files = [f for f in files if tuple(int(v) for v in f.stem.split("_")) in blocks]
    parts = [pd.read_parquet(f) for f in files]
    parts = [p for p in parts if len(p)]
    df = pd.concat(parts, ignore_index=True)
    return df


NEG_SPAN = 15      # "not yet built" labels: recorded years up to this long after the photograph


def labels(df, year: int):
    """1 = recorded year before the photograph (the building itself stood); 0 = recorded in the
    NEG_SPAN years after it; -1 = not a label. Recorded = `year_src` lpc / assessor, exact.
    Later recorded years are not used as "absent": in built-up districts most of those
    buildings replaced an earlier one, which the photograph shows on the same outline."""
    rec = df.year_src.isin(["lpc", "assessor"]).values & (df.year_confidence.values == "exact")
    y = np.floor(df.start_year.values)
    lab = np.full(len(df), -1, "int8")
    lab[rec & (y <= year - GAP - 1)] = 1
    lab[rec & (y >= year + GAP + 1) & (y <= year + NEG_SPAN)] = 0
    return lab


def density_class(df):
    """Today's fabric around the footprint: share of the ground within ~50 m that is building."""
    c = df.cov100.values
    return np.where(c < 0.15, "open <15%", np.where(c < 0.30, "detached 15-30%", np.where(c < 0.45, "rows 30-45%", "dense >45%")))


def fold_of(df, k=5):
    """Whole districts are held out together: z13 squares (3.8 km) hashed into k folds."""
    h = (df.bx.values // 2).astype("int64") * 7919 + (df.by.values // 2).astype("int64") * 104729
    return (h % 1000003 % k).astype(int)


# ----------------------------------------------------------------------------- step 1: tiles
BORO_ORDER = ("3", "4", "5", "2", "1")     # Manhattan last: its blocks give the weakest evidence
MARGIN_M = 25.0                            # tiles within this distance of a footprint centre are fetched


def tile_list():
    """z17 tiles under today's footprints: DataFrame boro, bx, by (z14 block), x, y - in fetch order."""
    import duckdb
    import pandas as pd
    out = WORK / "tiles_needed.parquet"
    if out.exists():
        return pd.read_parquet(out)
    con = duckdb.connect()
    df = con.execute(f"select boro, lon, lat from '{snapshot()}'").fetchdf()
    px, py = lonlat_to_pixel(df.lon.values, df.lat.values)
    m = MARGIN_M / metres_per_pixel(40.7)
    parts = []
    for sx in (-m, m):
        for sy in (-m, m):
            parts.append(pd.DataFrame({"boro": df.boro.values, "x": ((px + sx) // TILE).astype("int64"),
                                       "y": ((py + sy) // TILE).astype("int64")}))
    t = pd.concat(parts, ignore_index=True)
    t = t.groupby(["x", "y"], as_index=False).agg(boro=("boro", lambda s: s.mode().iloc[0]), n=("boro", "size"))
    t["bx"] = t.x // NB
    t["by"] = t.y // NB
    # a block is fetched with the borough that has most of its tiles
    bb = t.groupby(["bx", "by"]).boro.agg(lambda s: s.mode().iloc[0]).rename("bboro").reset_index()
    t = t.merge(bb, on=["bx", "by"])
    t["order"] = t.bboro.map({b: i for i, b in enumerate(BORO_ORDER)})
    t = t.sort_values(["order", "bx", "by", "x", "y"]).reset_index(drop=True)
    WORK.mkdir(parents=True, exist_ok=True)
    t.to_parquet(out)
    return t


def step_tiles():
    t = tile_list()
    log(f"tiles: {len(t)} z{Z} tiles per year in {t.groupby(['bx', 'by']).ngroups} blocks")
    n = 0
    t0 = time.time()
    for boro in BORO_ORDER:
        tb = t[t.bboro == boro]
        for year in YEARS:
            new = 0
            for x, y in zip(tb.x.values, tb.y.values):
                if tile_path(year, Z, int(x), int(y)) is None:
                    fetch_tile(year, Z, int(x), int(y))
                    new += 1
                    n += 1
                    if n % 500 == 0:
                        log(f"  fetched {n} tiles, {(time.time() - t0) / n:.3f} s each (borough {boro}, {year})")
            log(f"tiles: borough {boro} {year}: {len(tb)} tiles, {new} fetched now")
    log("tiles: done")


if __name__ == "__main__":
    steps = sys.argv[1:] or ["tiles", "features", "model", "predict"]
    for st in steps:
        if st == "tiles":
            step_tiles()
        elif st == "features":
            step_features()
        elif st == "features-follow":
            step_features(workers=2, follow=True)
