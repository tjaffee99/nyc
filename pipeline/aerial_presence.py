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


# ----------------------------------------------------------------------------- registration
REG_R = 8          # search radius, pixels (7 m)
REG_MIN_PX = 12000  # outline pixels a group needs
REG_Q = 2          # quadrants per side of a block (each 1024 px = 930 m)


def estimate_offsets(G, valid, geoms, use, cx, cy):
    """Shift (dx, dy), in pixels, by which the photograph is displaced against today's outlines,
    for every footprint (centre cx, cy in array pixels).

    The mean (locally normalised) gradient magnitude along the outlines of the buildings thought
    to stand (`use`) is computed for every shift within +-REG_R pixels: its peak is where the
    roof edges of the photograph fall on the outlines. The buildings are split into two halves
    at random and a peak counts only when both halves find it (within a pixel, not on the border
    of the search window) - the chance that two noise peaks agree is about 3 %. A quadrant of
    the block (930 m) uses its own peak when it has one, else the block's, else no shift.
    Returns dx, dy (arrays) and level (2 = quadrant, 1 = block, 0 = none)."""
    import shapely
    from rasterio import features
    from scipy import ndimage as ndi
    n = len(geoms)
    dx = np.zeros(n)
    dy = np.zeros(n)
    level = np.zeros(n, "int8")
    ids = np.flatnonzero(use)
    if len(ids) < 100:
        return dx, dy, level
    half = np.random.default_rng(0).integers(0, 2, n)
    O = features.rasterize([(b, int(i) + 1) for b, i in zip(shapely.boundary(geoms[ids]), ids)], out_shape=G.shape, fill=0,
                           dtype="int32", all_touched=True)
    O[~valid] = 0
    idx = np.flatnonzero(O.ravel())
    if len(idx) < REG_MIN_PX:
        return dx, dy, level
    if len(idx) > 400000:
        idx = idx[:: len(idx) // 400000 + 1]
    H, W = G.shape
    py, px = np.divmod(idx, W)
    qs = NB * TILE // REG_Q
    quad = np.clip((py - MARGIN) // qs, 0, REG_Q - 1) * REG_Q + np.clip((px - MARGIN) // qs, 0, REG_Q - 1)
    grp = quad * 2 + half[O.ravel()[idx] - 1]
    ng = REG_Q * REG_Q * 2
    cnt = np.bincount(grp, minlength=ng)
    Gn = (G / (ndi.uniform_filter(G, 41) + 0.02)).ravel()
    R = REG_R
    surf = np.zeros((ng, 2 * R + 1, 2 * R + 1))
    for ddy in range(-R, R + 1):
        for ddx in range(-R, R + 1):
            surf[:, ddy + R, ddx + R] = np.bincount(grp, weights=Gn[np.clip(idx + ddy * W + ddx, 0, Gn.size - 1)], minlength=ng)

    def agreed(a, b, na, nb):
        if na < REG_MIN_PX / 2 or nb < REG_MIN_PX / 2:
            return None
        ka = np.unravel_index(a.argmax(), a.shape)
        kb = np.unravel_index(b.argmax(), b.shape)
        if max(abs(ka[0] - kb[0]), abs(ka[1] - kb[1])) > 1:
            return None
        k = np.unravel_index((a + b).argmax(), a.shape)
        if k[0] in (0, 2 * R) or k[1] in (0, 2 * R):
            return None
        return float(k[1] - R), float(k[0] - R)

    blk = agreed(surf[0::2].sum(0), surf[1::2].sum(0), cnt[0::2].sum(), cnt[1::2].sum())
    fq = np.clip((cy - MARGIN) // qs, 0, REG_Q - 1).astype(int) * REG_Q + np.clip((cx - MARGIN) // qs, 0, REG_Q - 1).astype(int)
    for q in range(REG_Q * REG_Q):
        o = agreed(surf[2 * q], surf[2 * q + 1], cnt[2 * q], cnt[2 * q + 1])
        lv = 2
        if o is None:
            o, lv = blk, 1
        if o is None:
            continue
        m = fq == q
        dx[m], dy[m], level[m] = o[0], o[1], lv
    return dx, dy, level


# ----------------------------------------------------------------------------- features
RING = 3.0        # ring width outside the outline, pixels
FAR = 8.0         # outer ring, pixels
SHIFT = 3         # the outline score is also searched over +-SHIFT pixels
FEATS = ["in_mean", "in_std", "ring_mean", "ring_std", "far_mean", "far_std", "d_in_ring", "ad_in_ring",
         "in_dark", "in_bright", "ring_dark", "ring_bright", "in_grad", "ring_grad",
         "band_grad", "far_grad", "band_far", "ctx_grad30", "ctx_grad100", "ctx_std30", "ctx_std100",
         "ctx_dark30", "ctx_bright30", "ctx_blob30", "ctx_blob100", "ctx_edge30", "ctx_edge100",
         "rect4", "aniso2", "smax", "speak", "bright", "contrast"]
GEOM = ["log_area", "compact", "ring_share", "cov30", "cov100"]


def block_features(g, valid, P, geoms):
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
        dk = zsum((z < -1.0).astype("float32")) / c
        br = zsum((z > 1.0).astype("float32")) / c
    out.update(in_mean=m[0], in_std=sdv[0], ring_mean=m[1], ring_std=sdv[1], far_mean=m[2], far_std=sdv[2],
               d_in_ring=m[0] - m[1], ad_in_ring=np.abs(m[0] - m[1]), far_grad=gm_[2], in_grad=gm_[0], ring_grad=gm_[1],
               in_dark=dk[0], in_bright=br[0], ring_dark=dk[1], ring_bright=br[1])

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
    out["smax"] = S.max(0)
    out["speak"] = S.max(0) - S.mean(0)

    # context sampled at the centre of the footprint
    cen = shapely.centroid(geoms)
    cx = np.clip(shapely.get_x(cen).astype(int), 0, W - 1)
    cy = np.clip(shapely.get_y(cen).astype(int), 0, H - 1)
    out["ctx_grad30"] = ndi.uniform_filter(G, 33)[cy, cx]
    out["ctx_grad100"] = ndi.uniform_filter(G, 111)[cy, cx]
    out["ctx_dark30"] = ndi.uniform_filter((z < -1.0).astype("float32"), 33)[cy, cx]
    out["ctx_bright30"] = ndi.uniform_filter((z > 1.0).astype("float32"), 33)[cy, cx]
    blob = np.abs(ndi.gaussian_laplace(z, 2.0))          # roofs and their shadows: blobs of house size
    out["ctx_blob30"] = ndi.uniform_filter(blob, 33)[cy, cx]
    out["ctx_blob100"] = ndi.uniform_filter(blob, 111)[cy, cx]
    edge = (G > 0.25).astype("float32")
    out["ctx_edge30"] = ndi.uniform_filter(edge, 33)[cy, cx]
    out["ctx_edge100"] = ndi.uniform_filter(edge, 111)[cy, cx]
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

    # geometry of today's footprint (not evidence in itself; it tells how much the image can say)
    area = shapely.area(geoms)
    per = shapely.length(geoms)
    out["log_area"] = np.log(np.maximum(area, 1.0))
    out["compact"] = 4 * math.pi * area / np.maximum(per, 1.0) ** 2
    out["ring_share"] = c[1] / np.maximum(per * RING, 1.0)

    # coverage: share of the footprint and ring with a photograph
    out["cover"] = zsum(valid.astype("float32"))[:2].sum(0) / np.maximum(c[:2].sum(0), 1)
    return out


def blank_mask(g, valid, year=1924):
    """Where the mosaic has no photograph although the tile is opaque. The 1924 mosaic is the
    city's sectional aerial map: between its sheets run pure-white gutters (3 to 10 m wide), and
    its tiles are JPEG without transparency. Blank = pure white in a connected patch of 25
    pixels or more (1924 only: the 1951 photographs have overexposed grounds, and their tiles
    carry transparency), or flat pure black; grown by 3 pixels."""
    from scipy import ndimage as ndi
    m = ndi.uniform_filter(g, 5)
    sd = np.sqrt(np.maximum(ndi.uniform_filter(g * g, 5) - m * m, 0))
    blank = (sd < 1.0) & (m <= 1.0)
    if year == 1924:
        lab, n = ndi.label(g >= 253.0)
        if n:
            size = np.bincount(lab.ravel())
            size[0] = 0
            blank |= size[lab] >= 25
    blank = ndi.binary_dilation(blank, iterations=3)
    return valid & ~blank


def cover_path(year: int, bx: int, by: int) -> Path:
    return WORK / "cover" / str(year) / f"{bx}_{by}.parquet"


def _cover_job(job):
    """Coverage of the footprints of a block again, from the photograph alone (used once, after
    the blank test was tightened: the feature files written before it miss the white gutters;
    a fresh `features` run has the right coverage and does not need this)."""
    import pandas as pd
    import shapely
    from rasterio import features
    from scipy import ndimage as ndi
    year, bx, by = job
    out = cover_path(year, bx, by)
    if not feature_path(year, bx, by).exists() or not _claim(out):
        return job, -1
    try:
        f = pd.read_parquet(feature_path(year, bx, by))
        res = pd.DataFrame({"doitt_id": [], "cover2": []})
        blk = load_block(year, bx, by) if len(f) else None
        if blk is not None:
            g, valid, x0, y0 = blk
            cut = PAD * TILE - MARGIN
            g, valid = g[cut:-cut, cut:-cut], valid[cut:-cut, cut:-cut]
            x0, y0 = x0 + cut, y0 + cut
            inv = ndi.uniform_filter((~blank_mask(g, valid, year)).astype("float32"), 7)
            df = block_footprints(bx, by).set_index("doitt_id").reindex(f.doitt_id.values)
            ok = df.geom_px.notna().values
            geoms = shapely.transform(df.geom_px.values[ok], lambda c: c - np.array([x0, y0], "float64"))
            xy = shapely.get_coordinates(geoms)
            rep = shapely.get_num_coordinates(geoms)
            geoms = shapely.set_coordinates(geoms.copy(), xy + np.column_stack([np.repeat(f.offx.values[ok], rep), np.repeat(f.offy.values[ok], rep)]))
            n = len(geoms)
            L = features.rasterize([(gm, i + 1) for i, gm in enumerate(geoms)], out_shape=g.shape, fill=0, dtype="int32")
            cnt = np.bincount(L.ravel(), minlength=n + 1)[1:n + 1]
            bad = np.bincount(L.ravel(), weights=inv.ravel(), minlength=n + 1)[1:n + 1]
            cen = shapely.centroid(geoms)
            cx = np.clip(shapely.get_x(cen).astype(int), 0, g.shape[1] - 1)
            cy = np.clip(shapely.get_y(cen).astype(int), 0, g.shape[0] - 1)
            cov = np.where(cnt > 0, 1 - bad / np.maximum(cnt, 1), 1 - inv[cy, cx])
            c2 = np.zeros(len(f), "float32")
            c2[ok] = cov
            res = pd.DataFrame({"doitt_id": f.doitt_id.values, "cover2": c2})
        tmp = out.with_suffix(".part%d" % os.getpid())
        res.to_parquet(tmp)
        tmp.rename(out)
    finally:
        out.with_suffix(".lock").unlink(missing_ok=True)
    return job, len(res)


def step_recover():
    t = tile_list()
    jobs = [(year, int(bx), int(by)) for year in YEARS for bx, by in sorted(set(zip(t.bx, t.by)))]
    k = 0
    for job in jobs:
        _, n = _cover_job(job)
        if n >= 0:
            k += 1
            if k % 25 == 0:
                log(f"recover: {k} blocks, at {job}")
    log("recover: done")


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
    names = FEATS + GEOM + ["cover"]
    if blk is None:
        cols = {f: np.full(len(res), np.nan, "float32") for f in names}
        cols["cover"][:] = 0
        dx = dy = level = np.zeros(len(df))
    else:
        g, valid, x0, y0 = blk
        cut = PAD * TILE - MARGIN
        g, valid = g[cut:-cut, cut:-cut], valid[cut:-cut, cut:-cut]
        x0, y0 = x0 + cut, y0 + cut
        valid = blank_mask(g, valid, year)
        P = pixel_layers(g, valid)
        geoms = shapely.transform(df.geom_px.values, lambda c: c - np.array([x0, y0], "float64"))
        dx = np.zeros(len(df))
        dy = np.zeros(len(df))
        level = np.zeros(len(df), "int8")
        if apply_offset:
            use = (df.start_year.values <= year - 1) & (df.area.values > 60)
            cen = shapely.centroid(geoms)
            dx, dy, level = estimate_offsets(P["G"], valid, geoms, use, shapely.get_x(cen), shapely.get_y(cen))
            if level.any():
                xy = shapely.get_coordinates(geoms)
                rep = shapely.get_num_coordinates(geoms)
                xy = xy + np.column_stack([np.repeat(dx, rep), np.repeat(dy, rep)])
                geoms = shapely.set_coordinates(geoms.copy(), xy)
        f = block_features(g, valid, P, geoms)
        cols = {name: f[name][inblock].astype("float32") for name in names}
    cols["offx"] = dx[inblock].astype("float32")
    cols["offy"] = dy[inblock].astype("float32")
    cols["reg_level"] = np.asarray(level)[inblock].astype("int8")
    return pd.concat([res, pd.DataFrame(cols)], axis=1)


# ----------------------------------------------------------------------------- "certainly no building" outlines
# Recorded years say where a building certainly stood (it is older than the photograph) but
# hardly ever where none stood: a later building often replaced an earlier one on the same
# outline, and the assessor's later years are themselves doubtful. Outlines that certainly held
# no building are made instead: real footprints of ordinary size moved onto the carriageway of
# the nearest street (turned to run along it), where the photograph shows the street - or the
# field that was there before the street. They train and test the "no building" side.
OVERTURE_DIR = RAW / "overture"
_roads = None
SYN_PER_BLOCK = 600


def road_lines():
    """Overture street centre lines (no motorways) in global pixel coordinates, with an STRtree."""
    global _roads
    if _roads is None:
        import duckdb
        import shapely
        d = sorted(OVERTURE_DIR.glob("*/roads_local.parquet"))[-1].parent
        con = duckdb.connect()
        rows = con.execute(f"select ST_AsWKB(geometry) from '{d}/roads_local.parquet' where class in ('residential', 'unclassified')").fetchall()
        rows += con.execute(f"select ST_AsWKB(geometry) from '{d}/roads_region.parquet' where class in ('tertiary', 'secondary')").fetchall()
        g = shapely.from_wkb([bytes(r[0]) for r in rows])
        g = g[shapely.get_type_id(g) == 1]

        def tr(c):
            x, y = lonlat_to_pixel(c[:, 0], c[:, 1])
            return np.column_stack([x, y])
        g = shapely.transform(g, tr)
        _roads = (shapely.STRtree(g), g)
    return _roads


def street_outlines(geoms, area_m2, seed):
    """Footprints moved onto the nearest street (global pixel coordinates). Returns the new
    geometries and the index of the footprint each was made from."""
    import shapely
    from shapely import affinity
    tree, lines = road_lines()
    rng = np.random.default_rng(seed)
    cand = np.flatnonzero((area_m2 >= 40) & (area_m2 <= 400))
    if len(cand) == 0:
        return np.array([], dtype=object), np.array([], dtype=int)
    cand = rng.choice(cand, min(len(cand), SYN_PER_BLOCK * 2), replace=False)
    cen = shapely.centroid(geoms[cand])
    pairs = tree.query_nearest(cen, max_distance=70.0, all_matches=False)
    out, src = [], []
    for k, li in zip(pairs[0], pairs[1]):
        gm = geoms[cand[k]]
        line = lines[li]
        d = shapely.line_locate_point(line, cen[k])
        pt = shapely.line_interpolate_point(line, d)
        a = shapely.line_interpolate_point(line, max(d - 3, 0))
        b = shapely.line_interpolate_point(line, min(d + 3, line.length))
        if a.equals(b):
            continue
        street = math.atan2(b.y - a.y, b.x - a.x)
        r = np.asarray(shapely.minimum_rotated_rectangle(gm).exterior.coords)
        e1, e2 = r[1] - r[0], r[2] - r[1]
        l1, l2 = math.hypot(*e1), math.hypot(*e2)
        if min(l1, l2) > 11 or max(l1, l2) > 33:           # must fit the street: 10 m wide, 30 m long
            continue
        e = e1 if l1 >= l2 else e2
        rot = street - math.atan2(e[1], e[0])
        c = cen[k]
        g2 = affinity.translate(affinity.rotate(gm, rot, origin=(c.x, c.y), use_radians=True), pt.x - c.x, pt.y - c.y)
        out.append(g2)
        src.append(cand[k])
    if not out:
        return np.array([], dtype=object), np.array([], dtype=int)
    out = np.array(out, dtype=object)
    src = np.array(src)
    # not on a real footprint, not on each other
    real = shapely.STRtree(geoms)
    hit = np.unique(real.query(out, predicate="intersects")[0])
    keep = np.ones(len(out), bool)
    keep[hit] = False
    st = shapely.STRtree(out)
    i, j = st.query(out, predicate="intersects")
    for a_, b_ in zip(i, j):
        if a_ < b_ and keep[a_]:
            keep[b_] = False
    out, src = out[keep], src[keep]
    return out[:SYN_PER_BLOCK], src[:SYN_PER_BLOCK]


def synthetic_path(year: int, bx: int, by: int) -> Path:
    return WORK / "synthetic" / str(year) / f"{bx}_{by}.parquet"


def process_block_synthetic(year: int, bx: int, by: int):
    """Features of the street outlines of one block (same code path as the real footprints: the
    real footprints are rasterised with them, so rings exclude today's buildings in both)."""
    import pandas as pd
    import shapely
    df = block_footprints(bx, by, pad_tiles=MARGIN / TILE)
    blk = load_block(year, bx, by)
    if len(df) < 50 or blk is None:
        return None
    lo0, la0, lo1, la1 = block_lonlat(bx, by)
    inblock = ((df.lon >= lo0) & (df.lon < lo1) & (df.lat >= la0) & (df.lat < la1)).values
    g, valid, x0, y0 = blk
    cut = PAD * TILE - MARGIN
    g, valid = g[cut:-cut, cut:-cut], valid[cut:-cut, cut:-cut]
    x0, y0 = x0 + cut, y0 + cut
    valid = blank_mask(g, valid, year)
    P = pixel_layers(g, valid)
    gpx = df.geom_px.values
    syn, src = street_outlines(gpx[inblock], df.area.values[inblock], seed=bx * 100003 + by)
    if len(syn) == 0:
        return None
    src = np.flatnonzero(inblock)[src]
    allg = np.concatenate([gpx, syn])
    geoms = shapely.transform(allg, lambda c: c - np.array([x0, y0], "float64"))
    use = np.zeros(len(allg), bool)
    use[:len(df)] = (df.start_year.values <= year - 1) & (df.area.values > 60)
    cen = shapely.centroid(geoms)
    dx, dy, level = estimate_offsets(P["G"], valid, geoms, use, shapely.get_x(cen), shapely.get_y(cen))
    if level.any():
        xy = shapely.get_coordinates(geoms)
        rep = shapely.get_num_coordinates(geoms)
        geoms = shapely.set_coordinates(geoms.copy(), xy + np.column_stack([np.repeat(dx, rep), np.repeat(dy, rep)]))
    f = block_features(g, valid, P, geoms)
    n0 = len(df)
    cols = {name: f[name][n0:].astype("float32") for name in FEATS + GEOM + ["cover"]}
    res = pd.DataFrame(cols)
    res.insert(0, "doitt_id", ["syn_" + s_ for s_ in df.doitt_id.values[src]])
    res["boro"] = df.boro.values[src]
    c = shapely.centroid(syn)
    res["px"] = shapely.get_x(c)
    res["py"] = shapely.get_y(c)
    res["bx"] = np.int32(bx)
    res["by"] = np.int32(by)
    return res


def _syn_job(job):
    import pandas as pd
    year, bx, by = job
    out = synthetic_path(year, bx, by)
    if not _claim(out):
        return job, -1
    try:
        res = process_block_synthetic(year, bx, by)
        if res is None:
            res = pd.DataFrame({"doitt_id": []})
        tmp = out.with_suffix(".part%d" % os.getpid())
        res.to_parquet(tmp)
        tmp.rename(out)
    finally:
        out.with_suffix(".lock").unlink(missing_ok=True)
    return job, len(res)


def block_tiles(t):
    """block -> the needed tiles it reads (with the margin)."""
    tset = set(zip(t.x, t.y))
    return {b: [(x, y) for x in range(b[0] * NB - PAD, (b[0] + 1) * NB + PAD) for y in range(b[1] * NB - PAD, (b[1] + 1) * NB + PAD) if (x, y) in tset]
            for b in set(zip(t.bx, t.by))}


def step_synthetic(workers: int = 3, n_blocks: int = 64, follow: bool = False):
    """Street outlines for a fixed sample of blocks (every borough), both years."""
    from multiprocessing import Pool
    t = tile_list()
    need = block_tiles(t)
    rng = np.random.default_rng(11)
    jobs = []
    for boro in BORO_ORDER:
        tb = t[t.bboro == boro]
        size = tb.groupby(["bx", "by"]).n.sum()
        bl = sorted(b for b in set(zip(tb.bx, tb.by)) if size[b] > 8000)      # blocks with at least ~2,000 footprints
        rng.shuffle(bl)
        for b in bl[: max(8, n_blocks * len(bl) // 220)]:
            jobs += [(year, int(b[0]), int(b[1])) for year in YEARS]
    while True:
        todo = [j for j in jobs if not synthetic_path(*j).exists()]
        ready = [j for j in todo if all(tile_path(j[0], Z, x, y) is not None for x, y in need[(j[1], j[2])])]
        if ready:
            log(f"synthetic: {len(ready)} block-years ready, {len(todo) - len(ready)} waiting for tiles")
            with Pool(workers) as pool:
                for k, (job, n) in enumerate(pool.imap_unordered(_syn_job, sorted(ready))):
                    if k % 10 == 0:
                        log(f"  {k}/{len(ready)} {job} {n} outlines")
        if len(ready) == len(todo) or not follow:
            break
        time.sleep(60)
    log("synthetic: done")


def feature_path(year: int, bx: int, by: int) -> Path:
    return WORK / "features" / str(year) / f"{bx}_{by}.parquet"


def _claim(out: Path):
    """True when this process may compute `out`: nobody finished it and nobody else is on it
    (a lock file; several single-worker runs can share the work)."""
    if out.exists():
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    lock = out.with_suffix(".lock")
    try:
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        return True
    except FileExistsError:
        try:
            if time.time() - lock.stat().st_mtime < 1500:
                return False
            lock.touch()        # a stale lock (its run was stopped): take the block over
            return True
        except FileNotFoundError:
            return False


def _block_job(job):
    import pandas as pd
    year, bx, by = job
    out = feature_path(year, bx, by)
    if not _claim(out):
        return job, -1
    try:
        res = process_block_year(year, bx, by)
        if res is None:
            res = pd.DataFrame({"doitt_id": []})
        tmp = out.with_suffix(".part%d" % os.getpid())
        res.to_parquet(tmp)
        tmp.rename(out)
    finally:
        out.with_suffix(".lock").unlink(missing_ok=True)
    return job, len(res)


def step_features(workers: int = 3, follow: bool = False):
    """Every block-year whose tiles (with the margin) are all cached. With `follow`, waits for a
    running `tiles` step and goes on until every block is done."""
    from multiprocessing import Pool
    t = tile_list()
    boro_of = dict(zip(zip(t.bx, t.by), t.bboro))
    blocks = sorted(set(zip(t.bx, t.by)), key=lambda b: (BORO_ORDER.index(boro_of[b]), b))
    need = block_tiles(t)
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
            if workers == 1:
                for k, job in enumerate(todo):
                    _, n = _block_job(job)
                    if n >= 0 and k % 10 == 0:
                        log(f"  {k}/{len(todo)} {job} {n} footprints")
            else:
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


MODEL_FEATS = FEATS          # image evidence only: no size, shape or density of today's footprint
GAP = 2                     # recorded years within +-GAP of the photograph are not used as labels
GREEN_AFTER = 25            # "open ground" labels: recorded this long after the photograph ...
COVER_MIN = 0.95            # the mosaic must cover this share of footprint and ring
N_FOLDS = 5


def load_features(year: int, kind: str = "features"):
    import pandas as pd
    files = sorted((WORK / kind / str(year)).glob("*.parquet"))
    parts = [pd.read_parquet(f) for f in files]
    df = pd.concat([p for p in parts if len(p)], ignore_index=True)
    cfiles = sorted((WORK / "cover" / str(year)).glob("*.parquet")) if kind == "features" else []
    if cfiles:      # coverage recomputed with the tightened blank test (step `recover`)
        c = pd.concat([pd.read_parquet(f) for f in cfiles], ignore_index=True)
        c2 = df.doitt_id.map(dict(zip(c.doitt_id, c.cover2)))
        df["cover"] = np.where(c2.notna(), c2.fillna(0).values, df.cover.values).astype("float32")
    return df


def recorded(df):
    return df.year_src.isin(["lpc", "assessor"]).values & (df.year_confidence.values == "exact")


def greenfield(df, year: int):
    """Footprints on ground that was certainly open in `year`: recorded GREEN_AFTER years or more
    after the photograph, in surroundings (a 3 x 3 window of 116 m cells) where at least 12
    buildings have recorded years, none of them before the photograph, and fewer than one
    building in ten carries a placeholder year (placeholder years mark the older stock)."""
    from scipy import ndimage as ndi
    px, py = lonlat_to_pixel(df.lon.values, df.lat.values)
    cx = (px // 128).astype("int64")
    cy = (py // 128).astype("int64")
    cx -= cx.min()
    cy -= cy.min()
    shape = (cy.max() + 1, cx.max() + 1)
    rec = recorded(df)
    y = np.floor(df.start_year.values)

    def grid(m):
        g = np.zeros(shape, "float32")
        np.add.at(g, (cy[m], cx[m]), 1)
        return ndi.uniform_filter(g, 3, mode="constant") * 9
    n_all = grid(np.ones(len(df), bool))
    n_rec = grid(rec)
    n_old = grid(rec & (y <= year + GAP))
    ok = (n_rec >= 12) & (n_old == 0) & ((n_all - n_rec) < 0.1 * n_all)
    return rec & (y >= year + GREEN_AFTER) & ok[cy, cx]


def training_set(year: int):
    """Rows and labels for one photograph: 1 = recorded year before it (the building itself
    stood); 0 = a street outline, or a footprint on certainly open ground. Weights: the two
    sides weigh the same, and the two kinds of 0 weigh the same."""
    import pandas as pd
    real = load_features(year)
    syn = load_features(year, "synthetic")
    rec = recorded(real)
    y = np.floor(real.start_year.values)
    pos = rec & (y <= year - GAP - 1)
    green = greenfield(real, year)
    cols = ["doitt_id", "boro", "bx", "by", "cover", "cov100"] + FEATS
    d = pd.concat([real.loc[pos, cols].assign(lab=1, kind="recorded before"),
                   real.loc[green, cols].assign(lab=0, kind="open ground"),
                   syn[cols].assign(lab=0, kind="street outline")], ignore_index=True)
    d = d[d.cover >= COVER_MIN].reset_index(drop=True)
    w = np.zeros(len(d))
    for kind, share in (("recorded before", 0.5), ("open ground", 0.25), ("street outline", 0.25)):
        m = (d.kind == kind).values
        w[m] = share / max(m.sum(), 1)
    d["w"] = w * len(d)
    return d, real


def density_class(cov100):
    """Today's fabric around the footprint: share of the ground within ~50 m that is building."""
    c = np.asarray(cov100)
    return np.where(c < 0.15, "open <15%", np.where(c < 0.30, "detached 15-30%", np.where(c < 0.45, "rows 30-45%", "dense >45%")))


def fold_of(bx, by, k=N_FOLDS):
    """Whole districts are held out together: z13 squares (3.8 km) hashed into k folds."""
    h = (np.asarray(bx) // 2).astype("int64") * 7919 + (np.asarray(by) // 2).astype("int64") * 104729
    return (h % 1000003 % k).astype(int)


def model_path(year: int) -> Path:
    return WORK / f"model_{year}.npz"


def step_model(years=YEARS, trees: int = 250):
    """Per photograph: district hold-out scores, the final model and its calibration."""
    import pandas as pd
    for year in years:
        d, _ = training_set(year)
        X = d[MODEL_FEATS].values.astype("float64")
        y = d.lab.values.astype("float64")
        w = d.w.values
        fold = fold_of(d.bx.values, d.by.values)
        oof = np.zeros(len(d))
        for k in range(N_FOLDS):
            tr, te = fold != k, fold == k
            if te.any():
                oof[te] = GBM(n_trees=trees, seed=k).fit(X[tr], y[tr], w[tr]).decision(X[te])
            log(f"model {year}: fold {k} done ({int(te.sum())} held out)")
        xs, ps = isotonic(oof, y, w)
        m = GBM(n_trees=trees, seed=99).fit(X, y, w)
        np.savez(model_path(year), edges=np.array(m.edges, dtype=object), feat=m.feat, thr=m.thr, val=m.val, base=m.base,
                 xs=xs, ps=ps, gain=m.gain, feats=np.array(MODEL_FEATS), allow_pickle=True)
        d["score"] = oof
        d["p"] = np.interp(oof, xs, ps)
        d[["doitt_id", "boro", "bx", "by", "cov100", "lab", "kind", "w", "score", "p"]].to_parquet(WORK / f"oof_{year}.parquet")
        log(f"model {year}: {len(d)} rows ({d.kind.value_counts().to_dict()}), hold-out AUC {auc(y, oof, w):.3f}")


def load_model(year: int):
    z = np.load(model_path(year), allow_pickle=True)
    m = GBM(n_trees=z["feat"].shape[0], depth=int(round(math.log2(z["feat"].shape[1] + 1))) - 1)
    m.edges, m.feat, m.thr, m.val, m.base = list(z["edges"]), z["feat"], z["thr"], z["val"], float(z["base"])
    return m, z["xs"], z["ps"]


# ----------------------------------------------------------------------------- output
def step_predict():
    """data/manual/aerial/presence.parquet: one row per standing footprint."""
    import pandas as pd
    out = None
    for year in YEARS:
        real = load_features(year).drop_duplicates("doitt_id")      # a handful of ids occur twice in the city's file
        m, xs, ps = load_model(year)
        p = np.interp(m.decision(real[MODEL_FEATS].values.astype("float64")), xs, ps)
        cov = real.cover.values >= COVER_MIN
        p[~cov] = np.nan
        mpp = 156543.03392804097 * np.cos(np.radians(real.lat.values)) / 2 ** Z
        part = pd.DataFrame({"doitt_id": real.doitt_id.values, "bin": real.bin.values,
                             "built_share_50m": np.round(real.cov100.values, 2).astype("float32"),
                             f"p{year}": np.round(p, 3).astype("float32"), f"cover{year}": cov,
                             f"offset_m_{year}": np.round(np.hypot(real.offx.values, real.offy.values) * mpp, 1).astype("float32")})
        if out is None:
            out = part
        else:
            out = out.merge(part.drop(columns=["bin", "built_share_50m"]), on="doitt_id", how="outer")
    for year in YEARS:
        out[f"cover{year}"] = out[f"cover{year}"].fillna(False).astype(bool)
    out = out[["doitt_id", "bin"] + [f"p{y}" for y in YEARS] + [f"cover{y}" for y in YEARS] + [f"offset_m_{y}" for y in YEARS] + ["built_share_50m"]]
    out = out.sort_values("doitt_id").reset_index(drop=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_DIR / "presence.parquet", compression="zstd", index=False)
    log(f"predict: {len(out)} rows -> {OUT_DIR / 'presence.parquet'} ({(OUT_DIR / 'presence.parquet').stat().st_size / 1e6:.1f} MB)")


# ----------------------------------------------------------------------------- report
BORO_NAME = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"}
T_HI, T_LO = 0.8, 0.2       # "stood" / "open ground" thresholds used in the tables


def _md(df, floatfmt="{:.2f}"):
    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(floatfmt.format(v) if isinstance(v, (float, np.floating)) else str(v) for v in row) + " |")
    return "\n".join(lines)


def hand_labels(year: int):
    """The hand-checked sample (data/manual/aerial/hand_check.csv): doitt_id -> P / A / U / X."""
    import pandas as pd
    f = OUT_DIR / "hand_check.csv"
    if not f.exists():
        return None
    h = pd.read_csv(f, dtype={"doitt_id": str, "boro": str})
    return h[["doitt_id", "boro", f"seen{year}"]].rename(columns={f"seen{year}": "hand"})


def step_report():
    """Validation and research tables -> data/interim/aerial/report.md (copied into the README
    and the research note by hand)."""
    import pandas as pd
    out = []
    pres = pd.read_parquet(OUT_DIR / "presence.parquet")
    for year in YEARS:
        real = load_features(year)
        real = real.merge(pres[["doitt_id", f"p{year}"]], on="doitt_id", how="left")
        pcol = real[f"p{year}"].values
        real["bname"] = real.boro.map(BORO_NAME)
        out.append(f"\n## {year}\n")
        # coverage and registration
        g = real.groupby("bname")
        mpp = metres_per_pixel(40.7)
        off = np.hypot(real.offx.values, real.offy.values) * mpp
        t = pd.DataFrame({"footprints": g.size(), "covered %": g.cover.apply(lambda c: 100 * (c >= COVER_MIN).mean()),
                          "shifted %": g.reg_level.apply(lambda c: 100 * (c > 0).mean())})
        real["off_m"] = off
        sh = real[real.reg_level > 0].groupby("bname").off_m
        t["median shift m"] = sh.median()
        t["90% shift m"] = sh.quantile(0.9)
        t.loc["all"] = [len(real), 100 * (real.cover >= COVER_MIN).mean(), 100 * (real.reg_level > 0).mean(),
                        real.off_m[real.reg_level > 0].median(), real.off_m[real.reg_level > 0].quantile(0.9)]
        out.append("Coverage and registration\n\n" + _md(t.reset_index().rename(columns={"bname": "borough"}), "{:.1f}"))
        # district hold-out
        o = pd.read_parquet(WORK / f"oof_{year}.parquet")
        o["bname"] = o.boro.map(BORO_NAME)
        o["dens"] = density_class(o.cov100.values)
        out.append(f"\nDistrict hold-out, {len(o)} labelled outlines: AUC {auc(o.lab.values.astype(float), o.score.values, o.w.values):.3f} "
                   f"(recorded-before vs street outlines {auc(*[o[o.kind != 'open ground'][c].values.astype(float) for c in ('lab', 'score')]):.3f}, "
                   f"vs open ground {auc(*[o[o.kind != 'street outline'][c].values.astype(float) for c in ('lab', 'score')]):.3f})\n")
        rows = []
        for key, grp in [("all", o)] + list(o.groupby("bname")) + list(o.groupby("dens")):
            r = {"group": key, "AUC": auc(grp.lab.values.astype(float), grp.score.values) if grp.lab.nunique() == 2 else np.nan}
            for kind, nm in (("recorded before", "stood"), ("street outline", "street"), ("open ground", "open")):
                k = grp[grp.kind == kind]
                r[f"n {nm}"] = len(k)
                r[f"{nm}: p>={T_HI} %"] = 100 * (k.p >= T_HI).mean() if len(k) else np.nan
                r[f"{nm}: p<={T_LO} %"] = 100 * (k.p <= T_LO).mean() if len(k) else np.nan
            rows.append(r)
        out.append(_md(pd.DataFrame(rows), "{:.1f}"))
        # calibration on the hold-out (weights: both sides equal)
        bins = [0, 0.1, 0.2, 0.35, 0.5, 0.65, 0.8, 0.9, 1.0]
        o["bin"] = pd.cut(o.p, bins, include_lowest=True)
        cal = o.groupby("bin", observed=True).apply(lambda k: pd.Series({"n": len(k), "mean p": np.average(k.p, weights=k.w), "share that stood": np.average(k.lab, weights=k.w)}), include_groups=False)
        out.append("\nCalibration (hold-out, both sides weighted equally)\n\n" + _md(cal.reset_index().astype({"bin": str}), "{:.2f}"))
        # hand check
        h = hand_labels(year)
        if h is not None:
            h = h.merge(real[["doitt_id", f"p{year}", "cov100", "year_src", "year_confidence"]], on="doitt_id", how="left").rename(columns={f"p{year}": "p"})
            h["bname"] = h.boro.map(BORO_NAME)
            hh = h[h.hand.isin(["P", "A"]) & h.p.notna()]
            out.append(f"\nHand check: {len(h)} sampled, seen: {h.hand.value_counts().to_dict()}; with a probability and a clear call: {len(hh)}; "
                       f"AUC {auc((hh.hand == 'P').values.astype(float), hh.p.values):.3f}\n")
            hh = hh.assign(call=np.where(hh.p >= T_HI, f"p>={T_HI}", np.where(hh.p <= T_LO, f"p<={T_LO}", "between")))
            out.append(_md(pd.crosstab(hh.hand.map({"P": "building seen", "A": "open ground seen"}), hh.call).reset_index()))
            rows = []
            for key, grp in [("all", hh)] + list(hh.groupby("bname")):
                P, A = grp[grp.hand == "P"], grp[grp.hand == "A"]
                hi, lo = grp[grp.p >= T_HI], grp[grp.p <= T_LO]
                rows.append({"group": key, "seen building": len(P), "seen open": len(A),
                             f"p>={T_HI}: n": len(hi), f"p>={T_HI}: building %": 100 * (hi.hand == "P").mean() if len(hi) else np.nan,
                             f"p<={T_LO}: n": len(lo), f"p<={T_LO}: open %": 100 * (lo.hand == "A").mean() if len(lo) else np.nan,
                             "buildings found %": 100 * (P.p >= T_HI).mean() if len(P) else np.nan,
                             "open found %": 100 * (A.p <= T_LO).mean() if len(A) else np.nan})
            out.append("\n" + _md(pd.DataFrame(rows), "{:.0f}"))
            rows = []
            for t_ in (0.95, 0.9, 0.8, 0.7, 0.6):
                k = hh[hh.p >= t_]
                rows.append({"call": f"p >= {t_}", "n": len(k), "right %": 100 * (k.hand == "P").mean() if len(k) else np.nan,
                             "share of its side found %": 100 * (hh.p[hh.hand == "P"] >= t_).mean()})
            for t_ in (0.05, 0.1, 0.2, 0.3, 0.4):
                k = hh[hh.p <= t_]
                rows.append({"call": f"p <= {t_}", "n": len(k), "right %": 100 * (k.hand == "A").mean() if len(k) else np.nan,
                             "share of its side found %": 100 * (hh.p[hh.hand == "A"] <= t_).mean()})
            out.append("\nHand check by threshold\n\n" + _md(pd.DataFrame(rows), "{:.0f}"))
            tpr = (hh.p[hh.hand == "P"] >= T_HI).mean()
            tnr = (hh.p[hh.hand == "A"] <= T_LO).mean()
            u = h[h.hand == "U"]
            out.append(f"\nUnclear by eye ({len(u)}): mean p {u.p.mean():.2f}")
        # recorded years just after the photograph: what does the photograph show?
        rec = recorded(real)
        y = np.floor(real.start_year.values)
        rows = []
        for a, b in ((year - 40, year - 3), (year + 3, year + 8), (year + 9, year + 15), (year + 16, year + 30), (year + 31, 2030)):
            for src in ("lpc", "assessor"):
                m = rec & (real.year_src.values == src) & (y >= a) & (y <= b) & ~np.isnan(pcol)
                if m.sum() >= 30:
                    rows.append({"recorded year": f"{a}-{b}", "source": src, "n": int(m.sum()),
                                 f"p>={T_HI} %": 100 * (pcol[m] >= T_HI).mean(), f"p<={T_LO} %": 100 * (pcol[m] <= T_LO).mean()})
        out.append("\nRecorded years against the photograph (all boroughs)\n\n" + _md(pd.DataFrame(rows), "{:.1f}"))
        # placeholder years
        heap = real.year_src.str.startswith("heap").values & ~np.isnan(pcol)
        hy = real.raw_year.values
        top = pd.Series(hy[heap]).value_counts()
        years_ = sorted(int(v) for v in top[top >= 3000].index)
        rows = []
        for yv in years_:
            r = {"placeholder": yv}
            for b in ("3", "4", "2", "5", "1"):
                m = heap & (hy == yv) & (real.boro.values == b)
                r[f"{BORO_NAME[b]} n"] = int(m.sum())
                st_ = (pcol[m] >= T_HI).mean() if m.sum() >= 200 else np.nan
                op_ = (pcol[m] <= T_LO).mean() if m.sum() >= 200 else np.nan
                r[f"{BORO_NAME[b]} stood %"] = 100 * st_
                r[f"{BORO_NAME[b]} open %"] = 100 * op_
                # both calls miss about a third of their side: scale each by the share the hand check found
                r[f"{BORO_NAME[b]} est. standing %"] = 100 * (st_ / tpr) / (st_ / tpr + op_ / tnr) if m.sum() >= 200 and (st_ + op_) > 0 else np.nan
            rows.append(r)
        out.append(f"\nPlaceholder years: share the {year} photograph shows standing (p>={T_HI}) / on open ground (p<={T_LO}); "
                   f"est. standing = (stood / {tpr:.2f}) / (stood / {tpr:.2f} + open / {tnr:.2f}), the two calls scaled by the share of their side the hand check found\n\n" + _md(pd.DataFrame(rows), "{:.0f}"))
    (WORK / "report.md").write_text("\n".join(out) + "\n")
    log(f"report: {WORK / 'report.md'}")


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
    steps = sys.argv[1:] or ["tiles", "features", "synthetic", "model", "predict"]
    for st in steps:
        if st == "tiles":
            step_tiles()
        elif st == "features":
            step_features()
        elif st == "synthetic":
            step_synthetic()
        elif st == "model":
            step_model()
        elif st == "predict":
            step_predict()
        elif st == "report":
            step_report()
        elif st == "recover":
            step_recover()
        elif st == "synthetic-follow":
            step_synthetic(workers=1, follow=True)
        elif st == "features-follow":
            step_features(workers=1, follow=True)
