"""Buildings drawn as separate marks on the USGS topographic sheets of New York City.

Outside the dense city the 15-minute sheets of the 1888-89 survey and of its 1897 revision
(1:62,500) draw every building as a small black square: farmhouses, village houses, hotels,
churches. This stage reads those marks off the scans, matches the editions with each other
and with today's footprints, and writes

  data/manual/farmsteads/farmsteads.geojson    one point per mapped building (see README.md)
  data/manual/farmsteads/coverage.geojson      per sheet: the ground it was read on
  data/interim/farmsteads/sheets/<id>.json     per-sheet detections (cache)

Sheets: USGS Historical Topographic Map Collection (public domain). The GeoPDFs carry the
600 ppi scan (the GeoTIFFs are a 300 ppi resample in which a mark is 5 px across) and their
own registration (LGIDict: CTM, neat line, NAD27 polyconic). They are rendered with poppler's
`pdftoppm` (the only tool outside the Python environment), NAD27 -> WGS84 through the NADCON
grid, and then shifted onto today's streets (`align`).

  python topo_farmsteads.py fetch      # GeoPDFs + NADCON grid -> data/raw/farmsteads/ (cached)
  python topo_farmsteads.py detect     # every sheet -> data/interim/farmsteads/sheets/<id>.json (cached)
  python topo_farmsteads.py export     # match editions, footprints, land -> data/manual/farmsteads/
  python topo_farmsteads.py all
  options: --sheet ID (one sheet), --force (ignore the caches)

Method, validation and known failures: data/manual/farmsteads/README.md.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))   # also when run with python -I
from common import INTERIM, MANUAL, RAW, ROOT, log, session  # noqa: E402

FARM_RAW = RAW / "farmsteads"
PDF_DIR = FARM_RAW / "pdf"
PROJ_DIR = FARM_RAW / "proj"
FARM_INTERIM = INTERIM / "farmsteads"
SHEET_CACHE = FARM_INTERIM / "sheets"
OUT_DIR = MANUAL / "farmsteads"
HTMC = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/PDF/"
UA = "NYCThroughTime-research/0.1"
DPI = 600                       # render resolution (the scans are 599-600 ppi)
DETECTOR_VERSION = 4

# id: (file under HTMC, quadrangle, scale, print year, survey year the sheet shows, collar text, period)
# Survey years were read off the collars (data/manual/farmsteads/README.md); the catalogue's
# "survey year" is given for comparison there.
SHEETS = {
    "brooklyn_1889": ("NY/62500/NY_Brooklyn_8033200_1889_62500_geo.pdf", "Brooklyn", 62500, 1889, 1889, "Surveyed in 1888-89", "early"),
    "brooklyn_1897": ("NY/62500/NY_Brooklyn_139309_1898_62500_geo.pdf", "Brooklyn", 62500, 1898, 1897, "Surveyed in 1888-89 and 1897", "early"),
    "harlem_1889": ("NJ/62500/NJ_Harlem_472515_1891_62500_geo.pdf", "Harlem", 62500, 1891, 1889, "Surveyed in 1888-89", "early"),
    "harlem_1897": ("NY/62500/NY_Harlem_139657_1898_62500_geo.pdf", "Harlem", 62500, 1898, 1897, "Surveyed in 1888-89 and 1897", "early"),
    "staten_island_1897": ("NJ/62500/NJ_Staten%20Island_255388_1898_62500_geo.pdf", "Staten Island", 62500, 1898, 1897, "Surveyed in 1888-89 and 1897", "early"),
    "hempstead_1897": ("NY/62500/NY_Hempstead_129886_1897_62500_geo.pdf", "Hempstead", 62500, 1897, 1897, "Surveyed in 1897 (read on the 1903 print)", "early"),
    "oyster_bay_1897": ("NY/62500/NY_Oyster%20Bay_136363_1897_62500_geo.pdf", "Oyster Bay", 62500, 1897, 1897, "collar cut off on the scans; catalogue: 1897", "early"),
}

# The 1:24,000 sheets that still draw single buildings in open country, used only to say when a
# building of the 1890s was gone: (file, quadrangle, scale, edition year, aerial photographs, field check / survey).
# The editions of 1947 were compiled from photographs of 1940-42; those of 1955-57 from photographs of 1953-57.
# (The 1954 editions of Far Rockaway, Lawrence, Lynbrook and Sea Cliff repeat the 1941 photographs and are not used.)
LATE = {
    "arthur_kill_1947": ("NY/24000/NY_Arthur%20Kill_136694_1947_24000_geo.pdf", "Arthur Kill", 24000, 1947, 1940, None),
    "arthur_kill_1955": ("NY/24000/NY_Arthur%20Kill_136697_1955_24000_geo.pdf", "Arthur Kill", 24000, 1955, 1954, 1955),
    "the_narrows_1947": ("NY/24000/NY_The%20Narrows_139982_1947_24000_geo.pdf", "The Narrows", 24000, 1947, 1941, None),
    "the_narrows_1955": ("NY/24000/NY_The%20Narrows_139984_1955_24000_geo.pdf", "The Narrows", 24000, 1955, 1954, 1955),
    "elizabeth_1947": ("NJ/24000/NJ_Elizabeth_254343_1947_24000_geo.pdf", "Elizabeth", 24000, 1947, 1941, None),
    "elizabeth_1955": ("NJ/24000/NJ_Elizabeth_254346_1955_24000_geo.pdf", "Elizabeth", 24000, 1955, 1953, 1955),
    "jersey_city_1947": ("NJ/24000/NJ_Jersey%20City_254499_1947_24000_geo.pdf", "Jersey City", 24000, 1947, 1940, None),
    "jersey_city_1955": ("NJ/24000/NJ_Jersey%20City_254501_1955_24000_geo.pdf", "Jersey City", 24000, 1955, 1954, 1955),
    "coney_island_1947": ("NY/24000/NY_Coney%20Island_137694_1947_24000_geo.pdf", "Coney Island", 24000, 1947, 1940, None),
    "coney_island_1955": ("NY/24000/NY_Coney%20Island_137695_1955_24000_geo.pdf", "Coney Island", 24000, 1955, 1954, 1955),
    "brooklyn_1947": ("NY/24000/NY_Brooklyn_123124_1947_24000_geo.pdf", "Brooklyn", 24000, 1947, 1940, None),
    "brooklyn_1956": ("NY/24000/NY_Brooklyn_123128_1956_24000_geo.pdf", "Brooklyn", 24000, 1956, None, 1956),
    "jamaica_1947": ("NY/24000/NY_Jamaica_129963_1947_24000_geo.pdf", "Jamaica", 24000, 1947, 1941, None),
    "jamaica_1957": ("NY/24000/NY_Jamaica_129966_1957_24000_geo.pdf", "Jamaica", 24000, 1957, 1957, 1957),
    "far_rockaway_1947": ("NY/24000/NY_Far%20Rockaway_138136_1947_24000_geo.pdf", "Far Rockaway", 24000, 1947, 1941, None),
    "flushing_1947": ("NY/24000/NY_Flushing_138246_1947_24000_geo.pdf", "Flushing", 24000, 1947, 1942, None),
    "flushing_1955": ("NY/24000/NY_Flushing_138249_1955_24000_geo.pdf", "Flushing", 24000, 1955, 1954, 1955),
    "central_park_1947": ("NY/24000/NY_Central%20Park_122894_1947_24000_geo.pdf", "Central Park", 24000, 1947, 1941, None),
    "central_park_1956": ("NY/24000/NY_Central%20Park_122895_1956_24000_geo.pdf", "Central Park", 24000, 1956, None, 1956),
    "mount_vernon_1947": ("NY/24000/NY_Mt%20Vernon_130724_1947_24000_geo.pdf", "Mount Vernon", 24000, 1947, 1941, None),
    "mount_vernon_1956": ("NY/24000/NY_Mount%20Vernon_130719_1956_24000_geo.pdf", "Mount Vernon", 24000, 1956, 1954, 1956),
    "yonkers_1947": ("NJ/24000/NJ_Yonkers_255024_1947_24000_geo.pdf", "Yonkers", 24000, 1947, 1941, None),
    "yonkers_1956": ("NJ/24000/NJ_Yonkers_472567_1956_24000_geo.pdf", "Yonkers", 24000, 1956, 1954, 1956),
    "lynbrook_1947": ("NY/24000/NY_Lynbrook_130380_1947_24000_geo.pdf", "Lynbrook", 24000, 1947, 1941, None),
    "sea_cliff_1947": ("NY/24000/NY_Sea%20Cliff_136120_1947_24000_geo.pdf", "Sea Cliff", 24000, 1947, 1941, None),
    "lawrence_1947": ("NY/24000/NY_Lawrence_130229_1947_24000_geo.pdf", "Lawrence", 24000, 1947, 1941, None),
}
LATE_DPI = 300                  # 2 m per pixel: a building square is 6 px


# ----------------------------------------------------------------------------- sheets
def pdf_path(sid: str) -> Path:
    return PDF_DIR / {**SHEETS, **LATE}[sid][0].split("/")[-1].replace("%20", "_")


def fetch(sids=None):
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    PROJ_DIR.mkdir(parents=True, exist_ok=True)
    s = session()
    s.headers["User-Agent"] = UA
    todo = [(HTMC + {**SHEETS, **LATE}[i][0], pdf_path(i)) for i in (sids or {**SHEETS, **LATE})]
    todo.append(("https://cdn.proj.org/us_noaa_conus.tif", PROJ_DIR / "us_noaa_conus.tif"))   # NADCON, open licence
    for url, path in todo:
        if path.exists() and path.stat().st_size > 100_000:
            continue
        r = s.get(url, timeout=300)
        r.raise_for_status()
        path.write_bytes(r.content)
        log("fetched", path.name, len(r.content))


def _nums(obj: str, key: str):
    m = re.search(r"/" + key + r"\s*\[(.*?)\]", obj, re.S)
    return [float(v) for v in re.findall(r"\(([-0-9.eE+]+)\)", m.group(1))] if m else None


class Sheet:
    """A scanned USGS GeoPDF: registration read from the page's LGIDict (plain text in these
    files), pixels rendered by pdftoppm at DPI. Pixel (col, row) -> PDF points -> projected
    NAD27 metres (CTM) -> WGS84 (NADCON) -> UTM 18N, plus the sheet's shift onto today's streets."""

    def __init__(self, sid: str, dpi: int = DPI):
        import pyproj
        self.sid = sid
        self.dpi = dpi
        self.path = pdf_path(sid)
        raw = self.path.read_bytes()
        i = raw.find(b"/LGIDict")
        obj = raw[i:i + 20000].decode("latin1")
        j = raw.rfind(b"/CropBox", 0, i + 200) if raw.rfind(b"/CropBox", 0, i) > i - 400 else raw.find(b"/CropBox", i)
        box = [float(v) for v in re.findall(rb"[-0-9.]+", raw[j:j + 80].split(b"]")[0])][-4:]
        self.page_w, self.page_h = box[2] - box[0], box[3] - box[1]
        self.ctm = _nums(obj, "CTM")
        nl = np.array(_nums(obj, "Neatline")).reshape(-1, 2)
        pm = re.search(r"/Projection\s*<<(.*?)>>", obj, re.S)
        proj = dict(re.findall(r"/(\w+)\s*\(([^)]*)\)", pm.group(1)))
        datum = "+datum=NAD27" if proj.get("Datum", "NAS").startswith("NAS") else "+datum=NAD83"
        lat0, lon0 = proj.get("OriginLatitude", 0), proj.get("CentralMeridian", 0)
        fe, fn = proj.get("FalseEasting", 0), proj.get("FalseNorthing", 0)
        if proj.get("ProjectionType") == "PH":          # polyconic: the 15-minute sheets
            p4 = f"+proj=poly +lat_0={lat0} +lon_0={lon0} +x_0={fe} +y_0={fn}"
        elif proj.get("ProjectionType") in ("TC", "TM"):  # transverse Mercator on the sheet's own meridian: the 7.5-minute sheets
            p4 = f"+proj=tmerc +lat_0={lat0} +lon_0={lon0} +k={proj.get('ScaleFactor', 1)} +x_0={fe} +y_0={fn}"
        else:
            raise ValueError(f"{sid}: projection {proj}")
        self.s = dpi / 72.0                                     # pixels per PDF point
        self.W, self.H = int(self.page_w * self.s), int(self.page_h * self.s)
        self.m_per_px = abs(self.ctm[0]) / self.s
        self.px_per_mm = dpi / 25.4
        self.neat_px = np.column_stack([nl[:, 0] * self.s, (self.page_h - nl[:, 1]) * self.s])
        pyproj.datadir.append_data_dir(str(PROJ_DIR))
        crs = pyproj.CRS.from_proj4(f"{p4} {datum} +units=m +no_defs")
        geo = crs.geodetic_crs
        from pyproj.transformer import TransformerGroup
        self._inv = pyproj.Transformer.from_crs(crs, geo, always_xy=True)
        self._dat = TransformerGroup(geo, "EPSG:4326", always_xy=True,
                                     area_of_interest=pyproj.aoi.AreaOfInterest(-74.3, 40.45, -73.4, 41.05)).transformers[0]
        self._utm = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)
        self.shift = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]         # metres added in UTM: east = e0 + e1 u + e2 v, north likewise (u, v = page position in -1..1)

    def _shift_at(self, col, row):
        u, v = np.asarray(col, float) / self.W * 2 - 1, np.asarray(row, float) / self.H * 2 - 1
        (e0, e1, e2), (n0, n1, n2) = self.shift
        return e0 + e1 * u + e2 * v, n0 + n1 * u + n2 * v

    # pixel <-> ground
    def px_to_utm(self, col, row):
        a, b, c, d, e, f = self.ctm
        x = np.asarray(col, float) / self.s
        y = self.page_h - np.asarray(row, float) / self.s
        lon, lat = self._inv.transform(a * x + c * y + e, b * x + d * y + f)
        lon, lat = self._dat.transform(lon, lat)
        E, N = self._utm.transform(lon, lat)
        dE, dN = self._shift_at(col, row)
        return np.asarray(E) + dE, np.asarray(N) + dN

    def utm_to_px(self, E, N):
        a, b, c, d, e, f = self.ctm
        E, N = np.asarray(E, float), np.asarray(N, float)
        dE, dN = self.shift[0][0], self.shift[1][0]
        for _ in range(3):                                      # the shift varies slowly over the page
            lon, lat = self._utm.transform(E - dE, N - dN, direction="INVERSE")
            lon, lat = self._dat.transform(lon, lat, direction="INVERSE")
            X, Y = self._inv.transform(lon, lat, direction="INVERSE")
            det = a * d - b * c
            x = (d * (X - e) - c * (Y - f)) / det
            y = (-b * (X - e) + a * (Y - f)) / det
            col, row = x * self.s, (self.page_h - y) * self.s
            dE, dN = self._shift_at(col, row)
        return col, row

    def lonlat_to_px(self, lon, lat):
        E, N = self._utm.transform(lon, lat)
        return self.utm_to_px(E, N)

    def render(self, x0, y0, w, h):
        """RGB pixels [y0:y0+h, x0:x0+w] of the page at DPI."""
        out = subprocess.run(["pdftoppm", "-r", str(self.dpi), "-x", str(int(x0)), "-y", str(int(y0)), "-W", str(int(w)), "-H", str(int(h)),
                              str(self.path)], capture_output=True, check=True).stdout
        m = re.match(rb"P6\s+(\d+)\s+(\d+)\s+255\s", out)
        ww, hh = int(m.group(1)), int(m.group(2))
        return np.frombuffer(out, np.uint8, offset=m.end(), count=ww * hh * 3).reshape(hh, ww, 3)


# ----------------------------------------------------------------------------- detection
def _disc(r):
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    return (x * x + y * y) <= r * r + 1


def ink_threshold(rgb):
    """Black-ink thresholds on the brightest channel (black is dark in all three; brown contours
    keep red, blue water keeps blue). Strict (solid ink: the marks' cores) at 40 % of the way from
    the ink level to the paper, loose (hairlines of lettering, faint casings) at 72 %."""
    mx = rgb[::7, ::7].max(-1).astype(np.float32)
    paper = float(np.median(mx))
    dark = mx[mx < 0.6 * paper]
    ink = float(np.percentile(dark, 10)) if dark.size > 100 else 30.0
    return ink + 0.40 * (paper - ink), ink + 0.72 * (paper - ink), paper, ink


# shape limits in pixels at 600 ppi (1 px = 0.042 mm on paper = 2.65 m on the ground at 1:62,500)
CORE_R = 2            # opening disc radius: a mark holds a 5 px disc; road casings (2-3 px) do not
MARK_L = (4.5, 15.0)  # length of the core of a single building mark (12-40 m on the ground)
BAR_L = 46.0          # longer cores are block fronts / heavy lines, not single buildings
WIN = 24              # half window for the context tests
_ANG = np.deg2rad(np.arange(0, 180, 15))
_DX, _DY = np.cos(_ANG), np.sin(_ANG)


def _through_line(ink_d, cy, cx, R):
    """A line of ink runs through the blob's centre and on beyond it on both sides (rail with
    ties, crossing of heavy lines): share of ink along the best direction, 0..1."""
    H, W = ink_d.shape
    d = np.arange(int(R) + 3, int(R) + 15)
    best = 0.0
    for sgn_pair in (1,):
        xa = np.rint(cx + np.outer(_DX, d)).astype(int)
        ya = np.rint(cy + np.outer(_DY, d)).astype(int)
        xb = np.rint(cx - np.outer(_DX, d)).astype(int)
        yb = np.rint(cy - np.outer(_DY, d)).astype(int)
        ok = (xa >= 0) & (xa < W) & (ya >= 0) & (ya < H) & (xb >= 0) & (xb < W) & (yb >= 0) & (yb < H)
        if not ok.all():
            return 0.0
        fa = ink_d[ya, xa].mean(1)
        fb = ink_d[yb, xb].mean(1)
        best = float(np.minimum(fa, fb).max())
    return best


def detect_tile(rgb, thr, thr_loose):
    """Building marks in one tile. Returns dicts in tile pixels: col, row, area, L, W, fill, cls
    ('mark' | 'bar'), ctx ('isolated' | 'local' | 'network'), keep, why.

    cores  = solid ink that holds a 5 px disc (strict threshold): marks, bars, block fronts, heavy strokes
    comps  = connected ink at the loose threshold: what a core is attached to (nothing, a letter, the road net)"""
    from scipy import ndimage as ndi
    mx = rgb.max(-1)
    sat = mx.astype(np.int16) - rgb.min(-1)                      # black ink is grey; dark brown index contours and dark blue streams are not
    blue = ndi.uniform_filter(((rgb[..., 2].astype(np.int16) - rgb[..., 0] > 25) & (rgb[..., 2] > 110)).astype(np.float32), 41)
    ink = mx < thr
    inkL = mx < thr_loose
    core = ndi.binary_opening(ink, _disc(CORE_R))
    thick4 = ndi.binary_opening(ink, np.ones((4, 4), bool))
    s8 = np.ones((3, 3), bool)
    lab_core, n = ndi.label(core, s8)
    if n == 0:
        return []
    lab_ink, n_ink = ndi.label(inkL, s8)
    area_ink = np.bincount(lab_ink.ravel(), minlength=n_ink + 1)
    box_ink = ndi.find_objects(lab_ink)
    objs = ndi.find_objects(lab_core)
    cores = []
    for k, sl in enumerate(objs, 1):
        m = lab_core[sl] == k
        ys, xs = np.nonzero(m)
        a = len(ys)
        cy, cx = ys.mean(), xs.mean()
        if a >= 3:
            cov = np.cov(np.vstack([xs, ys])) + np.eye(2) / 12.0
            ev = np.sort(np.linalg.eigvalsh(cov))
            L, Wd = math.sqrt(12 * ev[1]), math.sqrt(12 * ev[0])
        else:
            L = Wd = 1.0
        fill = a / max(L * Wd, 1.0)
        if a >= 24 and MARK_L[0] <= L <= MARK_L[1] and Wd >= 4.2 and L / Wd <= 2.1 and fill >= 0.78:
            cls = "mark"
        elif a >= 60 and MARK_L[1] < L <= BAR_L and 4.5 <= Wd <= 16 and fill >= 0.80:
            cls = "bar"
        elif L > BAR_L or a > 600:
            cls = "band"
        else:
            cls = "odd"
        iy, ix = sl[0].start + ys[len(ys) // 2], sl[1].start + xs[len(xs) // 2]
        cores.append({"k": k, "sl": sl, "area": a, "L": L, "W": Wd, "fill": fill, "cls": cls,
                      "row": sl[0].start + cy, "col": sl[1].start + cx, "cid": int(lab_ink[iy, ix]),
                      "dark": float(mx[sl][m].mean()), "sat": float(sat[sl][m].mean())})
    cls_of = np.array(["x"] + [c["cls"] for c in cores])
    is_mark = (cls_of == "mark")[lab_core]
    mark_halo = ndi.binary_dilation(is_mark, s8, iterations=3)
    # per loose component: how much of it lies within 3 px of a core (the rest is thin: hairlines, casings)
    core_halo = ndi.binary_dilation(core, s8, iterations=3) & inkL
    thick_area = np.bincount(lab_ink[core_halo], minlength=n_ink + 1)
    ink_d = ndi.binary_dilation(inkL, s8)
    # the body of each core: the ink at least 4 px wide it is part of (a bead of a letter stem or of a heavy line has a long body)
    lab_body, _ = ndi.label(thick4, s8)
    body_area = np.bincount(lab_body.ravel())
    # counters: small patches of paper closed in by ink (o, e, a, d, B ...; also the cells of a ladder of rails and ties)
    lab_bg, nbg = ndi.label(~inkL)
    bg_area = np.bincount(lab_bg.ravel(), minlength=nbg + 1)
    box_bg = ndi.find_objects(lab_bg)
    small = (bg_area >= 12) & (bg_area <= 450)
    small[0] = False
    for edge in (lab_bg[0], lab_bg[-1], lab_bg[:, 0], lab_bg[:, -1]):
        small[np.unique(edge)] = False
    hole = small[lab_bg]
    wide = np.zeros(nbg + 1, bool)          # a counter holds a 4 px square; the pinched-off inside of a cased road does not
    wide[np.unique(lab_bg[ndi.binary_opening(hole, np.ones((4, 4), bool))])] = True
    small &= wide
    for hid in np.nonzero(small)[0]:        # and it is compact: slivers of road interior are long or slanted
        sl = box_bg[hid - 1]
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if max(h, w) > 2.6 * min(h, w) or bg_area[hid] < 0.45 * h * w:
            small[hid] = False
    hole = small[lab_bg]
    hole_near = ndi.binary_dilation(hole, s8, iterations=3)
    at_hole = np.zeros(n + 1, bool)
    at_hole[np.unique(lab_core[hole_near & core])] = True
    hole_lab = np.where(hole, lab_bg, 0)
    ring = (ndi.grey_dilation(hole_lab, size=3) > 0) & inkL
    comp_of_hole = np.zeros(nbg + 1, np.int64)
    comp_of_hole[ndi.grey_dilation(hole_lab, size=3)[ring]] = lab_ink[ring]
    ids = np.nonzero(small)[0]
    out = []
    if len(ids):
        for hid, (hy, hx) in zip(ids, ndi.center_of_mass(hole, lab_bg, ids)):
            cid = int(comp_of_hole[hid])
            if cid == 0:
                continue
            bs = box_ink[cid - 1]
            if max(bs[0].stop - bs[0].start, bs[1].stop - bs[1].start) <= 110:       # a letter standing clear of the road net
                out.append({"col": round(float(hx), 1), "row": round(float(hy), 1), "area": int(bg_area[hid]), "L": 0, "W": 0,
                            "cls": "hole", "ctx": "local", "thin": 1.0, "keep": False, "why": "counter"})
    by_comp = {}
    for c in cores:
        by_comp.setdefault(c["cid"], []).append(c)
    H, W = ink.shape
    for c in cores:
        cid = c["cid"]
        aC = int(area_ink[cid])
        bs = box_ink[cid - 1]
        dimC = max(bs[0].stop - bs[0].start, bs[1].stop - bs[1].start)
        thin = aC - int(thick_area[cid])
        if c["cls"] not in ("mark", "bar"):
            if c["cls"] == "odd" and c["area"] >= 12 and dimC <= 110:      # a stroke of a letter, kept as context for text_pass
                out.append({"col": round(float(c["col"]), 1), "row": round(float(c["row"]), 1), "area": c["area"], "L": round(c["L"], 1),
                            "W": round(c["W"], 1), "cls": "odd", "ctx": "local", "thin": round(thin / aC, 2), "keep": False, "why": "shape"})
            continue
        others = [o for o in by_comp[cid] if o is not c]
        keep, why = True, ""
        if not others and thin <= max(12, 0.10 * aC):
            ctx = "isolated"
        elif dimC <= 110:
            ctx = "local"
            if any(o["cls"] != "mark" and o["area"] >= 12 for o in others) or thin > 0.22 * aC or (c["cls"] == "bar" and thin > 0.08 * aC):
                keep, why = False, "text"          # a letter: other strokes and hairlines hang on the blob
        else:
            ctx = "network"
        iy, ix = int(round(c["row"])), int(round(c["col"]))
        body = int(body_area[lab_body[iy, ix]]) if lab_body[iy, ix] else c["area"]
        if c["sat"] > 38:
            keep, why = False, "colour"
        ys_, xs_ = np.clip(iy + np.array([0, -20, 20, 0, 0]), 0, H - 1), np.clip(ix + np.array([0, 0, 0, -20, 20]), 0, W - 1)
        b5 = blue[ys_, xs_]
        if keep and b5[0] >= 0.25 and b5[1:].min() >= 0.15:
            keep, why = False, "water"                 # lettering and soundings in open water (a building on the shore has dry ground on one side)
        if keep and at_hole[c["k"]]:
            keep, why = False, "counter"               # the blob borders a closed counter: a letter (or a rail ladder)
        if keep and c["cls"] == "mark" and body > 2.0 * c["area"] + 15:
            keep, why = False, "attached"              # a bead of something longer and at least 4 px wide
        if keep:
            # anything thick within 8 px of the blob that is not another building mark: the rest of a letter (a ball
            # terminal sits 3-8 px from its arc), a letter stem, a heavy rail line, a block front
            r0, r1 = max(int(c["row"]) - WIN, 0), min(int(c["row"]) + WIN + 1, H)
            c0, c1 = max(int(c["col"]) - WIN, 0), min(int(c["col"]) + WIN + 1, W)
            own = lab_core[r0:r1, c0:c1] == c["k"]
            near = ndi.binary_dilation(own, s8, iterations=8)
            rest = thick4[r0:r1, c0:c1] & ~ndi.binary_dilation(own, s8, iterations=2)
            if c["cls"] == "mark":
                rest &= ~mark_halo[r0:r1, c0:c1]
            lab_r, nr = ndi.label(rest, s8)
            if nr:
                touching = np.unique(lab_r[near & rest])
                att = int(np.isin(lab_r, touching[touching > 0]).sum())
                if att > 0.6 * c["area"]:
                    keep, why = False, "attached"
        line = 0.0
        if ctx != "isolated":
            line = _through_line(ink_d, c["row"], c["col"], c["L"] / 2)
            if keep and line >= 0.84:
                keep, why = False, "line"
        out.append({"col": round(float(c["col"]), 1), "row": round(float(c["row"]), 1), "area": c["area"], "L": round(c["L"], 1),
                    "W": round(c["W"], 1), "fill": round(c["fill"], 2), "cls": c["cls"], "ctx": ctx, "dark": round(c["dark"]), "sat": round(c["sat"]),
                    "thin": round(thin / aC, 2), "line": round(line, 2), "keep": keep, "why": why})
    return out


def _inside(poly, x, y):
    """Points (x, y) inside polygon poly (n x 2), even-odd rule."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    inside = np.zeros(x.shape, bool)
    px, py = poly[:, 0], poly[:, 1]
    j = len(poly) - 1
    for i in range(len(poly)):
        cond = ((py[i] > y) != (py[j] > y)) & (x < (px[j] - px[i]) * (y - py[i]) / (py[j] - py[i] + 1e-12) + px[i])
        inside ^= cond
        j = i
    return inside


def text_pass(marks):
    """Second look at the kept blobs with the whole sheet in view: lettering.
    A text piece is a blob or stroke in a letter-sized ink component with hairlines. A kept blob
    lying between two text pieces (on the segment joining them) is a piece of the same label;
    a bar next to a text piece, or beside another stroke that is not in line with it, is a stem."""
    from scipy.spatial import cKDTree
    P = np.array([[m["col"], m["row"]] for m in marks], float).reshape(-1, 2)
    text = np.array([m["ctx"] == "local" and m.get("thin", 0) >= 0.12 and (m["why"] == "text" or m["cls"] in ("odd", "hole")) for m in marks])
    stroke = np.array([m["cls"] in ("bar", "odd") for m in marks])
    if not text.any():
        return marks
    tp = P[text]
    tree = cKDTree(tp)
    stree = cKDTree(P[stroke]) if stroke.any() else None
    sidx = np.nonzero(stroke)[0]
    for i, m in enumerate(marks):
        if not m["keep"]:
            continue
        if len(tree.query_ball_point(P[i], 55.0)) >= 2 and tree.query_ball_point(P[i], 24.0):
            m["keep"], m["why"] = False, "in_text"
            continue
        near = tree.query_ball_point(P[i], 70.0)
        if len(near) >= 2:
            Q = tp[near] - P[i]
            A, B = Q[:, None, :], Q[None, :, :]
            D = B - A
            dd = (D ** 2).sum(-1)
            with np.errstate(divide="ignore", invalid="ignore"):
                t = -(A * D).sum(-1) / dd
                dist = np.hypot(*(np.moveaxis(A + t[..., None] * D, -1, 0)))
            hit = (dd > 100) & (dd <= 110.0 ** 2) & (t > 0.08) & (t < 0.92) & (dist <= 12.0)
            if hit.any():
                m["keep"], m["why"] = False, "in_text"
                continue
        if m["cls"] == "bar":
            if tree.query_ball_point(P[i], 45.0):
                m["keep"], m["why"] = False, "near_text"
                continue
            for j in sidx[stree.query_ball_point(P[i], 60.0)]:
                if j != i and marks[j]["L"] >= 10 and marks[j]["cls"] != "hole":
                    m["keep"], m["why"] = False, "stems"
                    break
    return marks


def detect_sheet(sh: "Sheet", tile=2600, margin=80):
    """All marks of a sheet (page pixels), detected tile by tile inside the neat line, and the
    sheet's thin ink (casings, lines) at 1/4 resolution for the alignment."""
    from scipy import ndimage as ndi
    x0, y0 = np.floor(sh.neat_px.min(0)).astype(int)
    x1, y1 = np.ceil(sh.neat_px.max(0)).astype(int)
    probe = sh.render((x0 + x1) // 2 - 1500, (y0 + y1) // 2 - 1500, 3000, 3000)
    thr, thr_loose, paper, inkv = ink_threshold(probe)
    marks = []
    lines = np.zeros((sh.H // 4 + 1, sh.W // 4 + 1), np.uint8)
    thick = np.zeros_like(lines)            # any solid ink (marks, bars, block fronts, heavy strokes), 1/4 resolution
    for ty in range(y0, y1, tile):
        for tx in range(x0, x1, tile):
            ax0, ay0 = max(tx - margin, 0), max(ty - margin, 0)
            ax0, ay0 = ax0 - ax0 % 4, ay0 - ay0 % 4
            w, h = min(tx + tile + margin, sh.W) - ax0, min(ty + tile + margin, sh.H) - ay0
            w, h = w - w % 4, h - h % 4
            rgb = sh.render(ax0, ay0, w, h)
            for m in detect_tile(rgb, thr, thr_loose):
                c, r = m["col"] + ax0, m["row"] + ay0
                if tx <= c < tx + tile and ty <= r < ty + tile:
                    m["col"], m["row"] = round(c, 1), round(r, 1)
                    marks.append(m)
            mx = rgb.max(-1)
            core = ndi.binary_opening(mx < thr, _disc(CORE_R))
            thin = (mx < thr_loose) & ~ndi.binary_dilation(core, iterations=3)
            sm = thin.reshape(thin.shape[0] // 4, 4, thin.shape[1] // 4, 4).mean((1, 3))
            lines[ay0 // 4:ay0 // 4 + sm.shape[0], ax0 // 4:ax0 // 4 + sm.shape[1]] = (sm * 255).astype(np.uint8)
            sm = core.reshape(core.shape[0] // 4, 4, core.shape[1] // 4, 4).max((1, 3))
            thick[ay0 // 4:ay0 // 4 + sm.shape[0], ax0 // 4:ax0 // 4 + sm.shape[1]] = sm
    if marks:
        ins = _inside(sh.neat_px, [m["col"] for m in marks], [m["row"] for m in marks])
        marks = [m for m, i in zip(marks, ins) if i]
    marks = text_pass(marks)
    return {"thr": round(thr, 1), "thr_loose": round(thr_loose, 1), "paper": paper, "ink": inkv, "marks": marks}, lines, thick


# ----------------------------------------------------------------------------- alignment
ROADS = [RAW / "overture" / "2026-10-21.0" / "roads_local.parquet", RAW / "overture" / "2026-10-21.0" / "roads_region.parquet"]


def modern_roads_px(sh: "Sheet", x0=None, y0=None, w=None, h=None):
    """Today's road centrelines (OpenStreetMap via Overture) as page-pixel polylines, through the
    sheet's registration and shift."""
    import duckdb
    import shapely
    if x0 is None:
        x0, y0, w, h = 0, 0, sh.W, sh.H
    E, N = sh.px_to_utm(np.array([x0, x0 + w, x0, x0 + w]), np.array([y0, y0, y0 + h, y0 + h]))
    lon, lat = sh._utm.transform(E, N, direction="INVERSE")
    con = duckdb.connect()
    con.execute("install spatial; load spatial;")
    out = []
    for f in ROADS:
        rows = con.execute(f"""select ST_AsWKB(geometry) from '{f}' where ST_XMax(geometry) > {lon.min()} and ST_XMin(geometry) < {lon.max()}
                               and ST_YMax(geometry) > {lat.min()} and ST_YMin(geometry) < {lat.max()}""").fetchall()
        geoms = shapely.from_wkb([bytes(r[0]) for r in rows])
        for g in geoms:
            for part in (g.geoms if g.geom_type.startswith("Multi") else [g]):
                xy = np.asarray(part.coords)
                e, n = sh._utm.transform(xy[:, 0], xy[:, 1])
                c, r = sh.utm_to_px(e, n)
                out.append(np.column_stack([c, r]))
    return out


def align(sh: "Sheet", lines, win=240, search=12):
    """Constant shift (metres east, north) of the sheet onto today's streets: the sheet's thin
    ink against today's centrelines, cross-correlated in 2.5 km windows, +-130 m, consensus of
    the windows. Returns (shift, info)."""
    from rasterio import features
    from scipy import ndimage as ndi
    from scipy.signal import correlate
    import shapely
    sh.shift = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    polys = modern_roads_px(sh)
    geoms = [shapely.LineString(p / 4.0) for p in polys if len(p) >= 2]
    road = features.rasterize(geoms, out_shape=lines.shape, fill=0, default_value=1, dtype="uint8").astype(np.float32)
    road = ndi.uniform_filter(road, 3)
    ink = lines.astype(np.float32) / 255.0
    x0, y0 = np.floor(sh.neat_px.min(0) / 4).astype(int)
    x1, y1 = np.ceil(sh.neat_px.max(0) / 4).astype(int)
    wins = []
    for wy in range(y0 + search, y1 - win - search, win // 2):
        for wx in range(x0 + search, x1 - win - search, win // 2):
            a = ink[wy:wy + win, wx:wx + win]
            b = road[wy - search:wy + win + search, wx - search:wx + win + search]
            if a.mean() < 0.01 or b[search:-search, search:-search].mean() < 0.01:
                continue
            cc = correlate(b - b.mean(), a - a.mean(), mode="valid", method="fft")
            py, px = np.unravel_index(cc.argmax(), cc.shape)
            peak = cc[py, px]
            if not (0 < py < 2 * search and 0 < px < 2 * search):
                continue
            yy, xx = np.mgrid[:cc.shape[0], :cc.shape[1]]
            second = cc[(yy - py) ** 2 + (xx - px) ** 2 > 16].max()
            # parabolic sub-cell peak
            dy = 0.5 * (cc[py - 1, px] - cc[py + 1, px]) / (cc[py - 1, px] - 2 * peak + cc[py + 1, px])
            dx = 0.5 * (cc[py, px - 1] - cc[py, px + 1]) / (cc[py, px - 1] - 2 * peak + cc[py, px + 1])
            wins.append((wx + win / 2, wy + win / 2, px + dx - search, py + dy - search, peak / max(second, 1e-9)))
    wins = np.array(wins)
    cell = 4 * sh.m_per_px
    info = {"windows": int(len(wins))}
    if len(wins) < 6:
        return [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], info
    good = wins[wins[:, 4] > 1.15] if (wins[:, 4] > 1.15).sum() >= 6 else wins
    med = np.median(good[:, 2:4], 0)
    inl = good[np.hypot(good[:, 2] - med[0], good[:, 3] - med[1]) <= 4.0]           # within 42 m of the consensus
    E, N = inl[:, 2] * cell, -inl[:, 3] * cell
    rms0 = float(np.sqrt(((E - E.mean()) ** 2 + (N - N.mean()) ** 2).mean()))
    # shift as a plane over the page (u, v in -1..1): the paper's stretch and the survey's drift
    u, v = inl[:, 0] * 4 / sh.W * 2 - 1, inl[:, 1] * 4 / sh.H * 2 - 1
    A = np.column_stack([np.ones(len(u)), u, v])
    keep = np.ones(len(u), bool)
    for _ in range(3):
        ce, *_ = np.linalg.lstsq(A[keep], E[keep], rcond=None)
        cn, *_ = np.linalg.lstsq(A[keep], N[keep], rcond=None)
        res = np.hypot(A @ ce - E, A @ cn - N)
        keep = res <= max(2.0 * np.sqrt((res[keep] ** 2).mean()), 12.0)
    rms1 = float(np.sqrt((res[keep] ** 2).mean()))
    if len(inl) >= 12 and rms1 < 0.85 * rms0 and np.abs(ce[1:]).max() < 60 and np.abs(cn[1:]).max() < 60:
        model = [[round(float(x), 2) for x in ce], [round(float(x), 2) for x in cn]]
        info["model"], info["rms_m"] = "plane", round(rms1, 1)
    else:
        model = [[round(float(E.mean()), 2), 0.0, 0.0], [round(float(N.mean()), 2), 0.0, 0.0]]
        info["model"], info["rms_m"] = "constant", round(rms0, 1)
    info.update({"used": int(keep.sum()), "sharp": int(len(good)), "rms_constant_m": round(rms0, 1),
                 "mean_shift_m": [round(float(E.mean()), 1), round(float(N.mean()), 1)],
                 # per window: page x, page y (px), shift east, north (m), peak sharpness
                 "window_shifts_m": [[round(float(w[0] * 4)), round(float(w[1] * 4)), round(float(w[2] * cell), 1), round(float(-w[3] * cell), 1), round(float(w[4]), 2)] for w in wins]})
    return model, info


def process(sid: str, force=False) -> dict:
    """Detect + align one sheet (cached)."""
    SHEET_CACHE.mkdir(parents=True, exist_ok=True)
    path = SHEET_CACHE / f"{sid}.json"
    if path.exists() and not force:
        res = json.loads(path.read_text())
        if res.get("version") == DETECTOR_VERSION:
            return res
    sh = Sheet(sid)
    res, lines, thick = detect_sheet(sh)
    np.save(FARM_INTERIM / f"thick_{sid}.npy", thick)
    shift, info = align(sh, lines)
    f, quad, scale, printed, survey, collar, period = SHEETS[sid]
    res.update({"version": DETECTOR_VERSION, "sid": sid, "quad": quad, "scale": scale, "print_year": printed, "survey_year": survey,
                "collar": collar, "shift": shift, "align": info, "neat_px": sh.neat_px.round(1).tolist()})
    path.write_text(json.dumps(res))
    log(sid, "marks kept", sum(m["keep"] for m in res["marks"]), "of", len(res["marks"]), "shift", shift, info.get("model"), "rms", info.get("rms_m"), "constant", info.get("rms_constant_m"), "windows", info.get("used"))
    return res


# ----------------------------------------------------------------------------- the later sheets
def process_late(sid: str, force=False):
    """A 1:24,000 sheet reduced to three rasters at 1/4 of LATE_DPI (8 m cells), cached:
    compact = solid black blobs up to 28 m across (building squares; also pieces of lettering),
    large   = solid black longer than that (heavy road lines and the black blocks of the 1947
              editions, big buildings, large lettering),
    tint    = the pink built-up tint of the 1955-57 editions (inside it only landmark buildings are drawn)."""
    from scipy import ndimage as ndi
    path = FARM_INTERIM / f"late_{sid}.npz"
    if path.exists() and not force:
        return path
    sh = Sheet(sid, LATE_DPI)
    x0, y0 = np.floor(sh.neat_px.min(0)).astype(int)
    x1, y1 = np.ceil(sh.neat_px.max(0)).astype(int)
    thr = ink_threshold(sh.render((x0 + x1) // 2 - 1200, (y0 + y1) // 2 - 1200, 2400, 2400))[0]
    shape = (sh.H // 4 + 2, sh.W // 4 + 2)
    compact, large, tint = np.zeros(shape, bool), np.zeros(shape, bool), np.zeros(shape, bool)
    tile, margin, s8 = 2400, 40, np.ones((3, 3), bool)
    for ty in range(y0 - y0 % 4, y1, tile):
        for tx in range(x0 - x0 % 4, x1, tile):
            ax0, ay0 = max(tx - margin, 0), max(ty - margin, 0)
            w, h = min(tx + tile + margin, sh.W) - ax0, min(ty + tile + margin, sh.H) - ay0
            w, h = w - w % 4, h - h % 4
            if w < 8 or h < 8:
                continue
            rgb = sh.render(ax0, ay0, w, h)
            a = rgb.astype(np.int16)
            core = ndi.binary_opening(rgb.max(-1) < thr, np.ones((4, 4), bool))
            lab, n = ndi.label(core, s8)
            small = np.zeros(n + 1, bool)
            for k, sl in enumerate(ndi.find_objects(lab), 1):
                small[k] = max(sl[0].stop - sl[0].start, sl[1].stop - sl[1].start) <= 14
            pink = (a[..., 0] >= 200) & (a[..., 0] - a[..., 1] >= 30) & (a[..., 0] - a[..., 2] >= 30) & (a[..., 1] >= 140)
            for arr, dst, f in ((small[lab], compact, "max"), (core & ~small[lab], large, "max"), (pink, tint, "half")):
                b = arr.reshape(h // 4, 4, w // 4, 4)
                b = b.max((1, 3)) if f == "max" else b.mean((1, 3)) >= 0.5
                my, mx_ = (ty - ay0) // 4, (tx - ax0) // 4          # write the tile itself, not its margin
                b = b[my:my + tile // 4, mx_:mx_ + tile // 4]
                dst[ty // 4:ty // 4 + b.shape[0], tx // 4:tx // 4 + b.shape[1]] = b
    np.savez_compressed(path, compact=compact, large=large, tint=tint, neat_px=sh.neat_px)
    log(sid, "compact", int(compact.sum()), "large", int(large.sum()), "tint", int(tint.sum()))
    return path


# ----------------------------------------------------------------------------- export
MATCH_M = 35.0      # two editions show the same building
CLEAR_M = 40.0      # nothing solid within this distance on a 15-minute sheet = not shown there
LATE_M = 45.0       # ... on a 1:24,000 sheet (the early mark is good to about 20-25 m)
BIN_M = 25.0        # today's footprint under the mark: within the positional error
SITE_M = 60.0       # marks closer than this are one site (house and barns)
BORO = {"36061": "Manhattan", "36047": "Brooklyn", "36081": "Queens", "36005": "Bronx", "36085": "Staten Island"}
WET = {0: "water", 1: "water", 2: "tidal_flat", 3: "tidal_marsh", 14: "water", 21: "wetland", 22: "water"}   # terrain_tiles.COVER_NAMES


def _poly_utm(sh):
    import shapely
    E, N = sh.px_to_utm(sh.neat_px[:, 0], sh.neat_px[:, 1])
    return shapely.Polygon(np.column_stack([E, N]))


def _near(mask, radius_cells):
    from scipy import ndimage as ndi
    return ndi.maximum_filter(mask.astype(np.uint8), size=2 * radius_cells + 1).astype(bool)


def _sample(arr, col, row):
    """arr at 1/4-resolution cells of page pixels (col, row); False outside."""
    c, r = (np.asarray(col) // 4).astype(int), (np.asarray(row) // 4).astype(int)
    ok = (c >= 0) & (r >= 0) & (c < arr.shape[1]) & (r < arr.shape[0])
    out = np.zeros(len(c), arr.dtype)
    out[ok] = arr[r[ok], c[ok]]
    return out


def cover_at(E, N, year):
    """Ground cover name ('' = dry land) at UTM points in a year, from the built terrain's cover history
    (data/interim/grid_detail_covers / _years: cover k holds until years[k]). None where the grid is missing."""
    import pyproj
    cp, yp = INTERIM / "grid_detail_covers.npy", INTERIM / "grid_detail_years.npy"
    if not cp.exists():
        return None
    meta = json.loads((INTERIM / "grid_detail_meta.json").read_text())
    covers, years = np.load(cp, mmap_mode="r"), np.load(yp, mmap_mode="r")
    X, Y = pyproj.Transformer.from_crs("EPSG:32618", "EPSG:3857", always_xy=True).transform(E, N)
    c = np.rint((np.asarray(X) - meta["X0"]) / meta["res"]).astype(int)
    r = np.rint((meta["Y0"] - np.asarray(Y)) / meta["res"]).astype(int)
    ok = (c >= 1) & (r >= 1) & (c < meta["cols"] - 1) & (r < meta["rows"] - 1)
    out = np.array([""] * len(c), dtype=object)

    def at(rr, cc):
        cov = np.array(covers[0, rr, cc])
        for k in range(years.shape[0]):
            yk = np.array(years[k, rr, cc])
            step = ~np.isnan(yk) & (year >= yk)
            cov[step] = np.array(covers[k + 1, rr, cc])[step]
        return cov
    cov = at(r[ok], c[ok])
    wet = np.isin(cov, list(WET))
    dry_near = np.zeros(len(cov), bool)                    # the shore is good to a cell: dry ground next door counts
    for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        dry_near |= ~np.isin(at(r[ok] + dr, c[ok] + dc), list(WET))
    names = np.array([WET.get(int(v), "") for v in cov], dtype=object)
    names[wet & dry_near & np.isin(names, ["water"])] = "shore"
    out[ok] = names
    return out


def export():
    import duckdb
    import geopandas as gpd
    import pandas as pd
    import pyproj
    import shapely
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    from scipy.spatial import cKDTree
    to_ll = pyproj.Transformer.from_crs("EPSG:32618", "EPSG:4326", always_xy=True)
    to_utm = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)

    # --- the early sheets: kept marks in UTM
    sheets, res, per = {}, {}, {}
    for sid in SHEETS:
        path = SHEET_CACHE / f"{sid}.json"
        if not path.exists():
            log("export: no detections for", sid, "- run detect")
            continue
        res[sid] = json.loads(path.read_text())
        sh = sheets[sid] = Sheet(sid)
        sh.shift = res[sid]["shift"]
        ms = [m for m in res[sid]["marks"] if m["keep"]]
        E, N = sh.px_to_utm([m["col"] for m in ms], [m["row"] for m in ms])
        per[sid] = pd.DataFrame({"sid": sid, "E": E, "N": N, "col": [m["col"] for m in ms], "row": [m["row"] for m in ms],
                                 "cls": [m["cls"] for m in ms], "ctx": [m["ctx"] for m in ms], "area": [m["area"] for m in ms],
                                 "L": [m["L"] for m in ms]})
    thick = {sid: _near(np.load(FARM_INTERIM / f"thick_{sid}.npy"), int(math.ceil(CLEAR_M / (4 * sheets[sid].m_per_px)))) for sid in sheets}

    def shown(sid, E, N):
        """Any solid ink within CLEAR_M of the points on sheet sid."""
        c, r = sheets[sid].utm_to_px(E, N)
        return _sample(thick[sid], c, r)

    # --- one feature per building: match the two surveys of a quadrangle
    feats = []
    quads = {}
    for sid in sheets:
        quads.setdefault(SHEETS[sid][1], []).append(sid)
    for quad, sids in quads.items():
        sids = sorted(sids, key=lambda i: SHEETS[i][4])
        if len(sids) == 1:
            d = per[sids[0]]
            y = SHEETS[sids[0]][4]
            feats.append(d.assign(first_year=y, last_year=y, gone_by=np.nan, sheets=sids[0], earlier_unclear=False, later_unclear=False, new_since=np.nan))
            continue
        a_id, b_id = sids[0], sids[-1]
        A, B = per[a_id], per[b_id]
        ya, yb = SHEETS[a_id][4], SHEETS[b_id][4]
        tb = cKDTree(B[["E", "N"]].values)
        ta = cKDTree(A[["E", "N"]].values)
        da, ia = tb.query(A[["E", "N"]].values)
        db, ib = ta.query(B[["E", "N"]].values)
        pair = (da <= MATCH_M) & (ib[ia] == np.arange(len(A)))
        both = A[pair].copy()
        bm = B.iloc[ia[pair]]
        both["E"], both["N"] = (both["E"].values + bm["E"].values) / 2, (both["N"].values + bm["N"].values) / 2
        both["cls"] = np.where((both["cls"].values == "bar") & (bm["cls"].values == "bar"), "bar", "mark")
        feats.append(both.assign(first_year=ya, last_year=yb, gone_by=np.nan, sheets=f"{a_id}+{b_id}", earlier_unclear=False, later_unclear=False, new_since=np.nan))
        only_a = A[~pair].copy()
        still = shown(b_id, only_a["E"].values, only_a["N"].values)
        feats.append(only_a.assign(first_year=ya, last_year=ya, gone_by=np.where(still, np.nan, yb), sheets=a_id, earlier_unclear=False, later_unclear=still, new_since=np.nan))
        used_b = np.zeros(len(B), bool)
        used_b[ia[pair]] = True
        only_b = B[~used_b].copy()
        before = shown(a_id, only_b["E"].values, only_b["N"].values)
        feats.append(only_b.assign(first_year=yb, last_year=yb, gone_by=np.nan, sheets=b_id, earlier_unclear=before, later_unclear=False, new_since=np.where(before, np.nan, ya)))
    F = pd.concat(feats, ignore_index=True)

    # --- boroughs (marks outside the five boroughs stay in the per-sheet caches)
    g = gpd.read_file("zip://" + str(RAW / "tiger" / "tl_2024_us_county.zip"), where="STATEFP = '36' AND COUNTYFP IN ('061','047','081','005','085')").to_crs(32618)
    pts = gpd.GeoDataFrame(F, geometry=gpd.points_from_xy(F["E"], F["N"]), crs=32618)
    j = gpd.sjoin(pts, g[["GEOID", "geometry"]], how="left", predicate="within")
    F["borough"] = j["GEOID"].map(BORO).values
    region_n = int(F["borough"].isna().sum())
    F = F[F["borough"].notna()].reset_index(drop=True)

    # --- ground of the survey year
    F["ground"] = ""
    for y in sorted(F["first_year"].unique()):
        m = F["first_year"] == y
        cov = cover_at(F.loc[m, "E"].values, F.loc[m, "N"].values, int(y))
        if cov is not None:
            F.loc[m, "ground"] = cov
    in_water = int((F["ground"] == "water").sum())
    F = F[F["ground"] != "water"].reset_index(drop=True)

    # --- built-up extent of the same edition (data/manual/extents): frontages there are not separate marks
    F["builtup"] = False
    for y in (1889, 1897):
        polys = []
        for b in ("manhattan", "brooklyn", "queens", "bronx", "staten_island"):
            fp = MANUAL / "extents" / f"{b}_{y}.geojson"
            if fp.exists():
                polys.append(gpd.read_file(fp).to_crs(32618))
        if not polys:
            continue
        u = shapely.union_all(pd.concat(polys).geometry.values)
        shapely.prepare(u)
        m = F["last_year"] == y
        F.loc[m, "builtup"] = shapely.contains_xy(u, F.loc[m, "E"].values, F.loc[m, "N"].values)

    # --- the later sheets: gone by
    F["late_symbol"] = ""
    late_info = {}
    for sid in sorted(LATE, key=lambda i: LATE[i][3]):
        path = FARM_INTERIM / f"late_{sid}.npz"
        if not path.exists():
            continue
        z = np.load(path)
        sh = Sheet(sid, LATE_DPI)
        poly = _poly_utm(sh)
        shapely.prepare(poly)
        inside = shapely.contains_xy(poly, F["E"].values, F["N"].values)
        if not inside.any():
            continue
        cell = 4 * sh.m_per_px
        c, r = sh.utm_to_px(F.loc[inside, "E"].values, F.loc[inside, "N"].values)
        from scipy import ndimage as ndi
        symbol = _sample(_near(z["compact"], int(round(LATE_M / cell))), c, r)
        mass = _sample(_near(z["large"], int(round(30.0 / cell))), c, r)
        k = 2 * int(round(LATE_M / cell)) + 1
        tinted = _sample(ndi.uniform_filter(z["tint"].astype(np.float32), k) >= 0.2, c, r)
        blank = ~symbol & ~mass & ~tinted
        year = LATE[sid][3]
        idx = F.index[inside]
        gone = idx[blank & F.loc[idx, "gone_by"].isna().values]
        F.loc[gone, "gone_by"] = year
        seen = idx[symbol & ~mass & ~tinted & F.loc[idx, "gone_by"].isna().values]
        F.loc[seen, "late_symbol"] = F.loc[seen, "late_symbol"].where(F.loc[seen, "late_symbol"] == "", F.loc[seen, "late_symbol"] + "+") + str(year)
        late_info[sid] = {"inside": int(inside.sum()), "blank": int(blank.sum()), "symbol": int((symbol & ~mass & ~tinted).sum()),
                          "unclear": int((mass | tinted).sum()), "gone_set": int(len(gone))}

    # --- today's footprint under the mark
    con = duckdb.connect()
    con.execute("install spatial; load spatial;")
    bp = INTERIM / "nyc_buildings.parquet"
    F["standing_bin"] = np.nan
    for col in ("standing_basis", "standing_year_src"):
        F[col] = ""
    for col in ("standing_year", "standing_dist_m", "standing_n", "standing_area_m2"):
        F[col] = np.nan
    control = {}
    if bp.exists():
        Bd = con.execute(f"""select doitt_id, bin, lon, lat, start_year, year_confidence, year_src, raw_year, area, height_m
                             from '{bp}' where end_year = 9999 and area >= 45""").df()
        bE, bN = to_utm.transform(Bd["lon"].values, Bd["lat"].values)
        tree = cKDTree(np.column_stack([bE, bN]))

        def match(E, N, first_year, cls, want_geom=True):
            cand = tree.query_ball_point(np.column_stack([E, N]), BIN_M + 45.0)
            ii = np.repeat(np.arange(len(E)), [len(x) for x in cand])
            jj = np.fromiter((v for x in cand for v in x), int, count=len(ii))
            ids = Bd["doitt_id"].values[np.unique(jj)]
            con.register("ids", pd.DataFrame({"doitt_id": ids}))
            gdf = con.execute(f"select b.doitt_id, ST_AsWKB(b.geometry) wkb from '{bp}' b join ids using (doitt_id) where b.end_year = 9999").df()
            geom = dict(zip(gdf["doitt_id"], shapely.from_wkb([bytes(w) for w in gdf["wkb"]])))
            polys = shapely.transform(np.array([geom[i] for i in Bd["doitt_id"].values[jj]]),
                                      lambda xy: np.column_stack(to_utm.transform(xy[:, 0], xy[:, 1])))
            dist = shapely.distance(polys, shapely.points(E[ii], N[ii]))
            b = Bd.iloc[jj]
            fy = first_year[ii]
            exact = b["year_confidence"].values == "exact"
            sy = b["start_year"].values
            lpc = b["year_src"].values == "lpc"
            ok = (dist <= BIN_M) & ~(exact & (sy > fy)) & ~(lpc & (sy > fy)) & ((b["height_m"].fillna(0).values <= 22) | ((exact | lpc) & (sy <= fy)))
            ok &= (b["area"].values <= 1500) | (cls[ii] == "bar") | ((exact | lpc) & (sy <= fy))
            rank = np.where((exact | lpc) & (sy <= fy), 0, np.where(b["year_src"].str.startswith("heap_by").values | (sy <= fy), 1, 2))
            t = pd.DataFrame({"i": ii, "j": jj, "dist": dist, "rank": rank})[ok].sort_values(["i", "rank", "dist"])
            best = t.groupby("i").first()
            n_same = t.merge(best[["rank"]].rename(columns={"rank": "r0"}), left_on="i", right_index=True)
            n_same = n_same[n_same["rank"] == n_same["r0"]].groupby("i").size()
            return best.assign(n=n_same)

        best = match(F["E"].values, F["N"].values, F["first_year"].values, F["cls"].values)
        names = np.array(["recorded", "by_then", "later_estimate"])
        bb = Bd.iloc[best["j"].values]
        ix = best.index.values
        F.loc[ix, "standing_bin"] = bb["bin"].values
        F.loc[ix, "standing_basis"] = names[best["rank"].values]
        F.loc[ix, "standing_year"] = bb["start_year"].values
        F.loc[ix, "standing_year_src"] = bb["year_src"].values
        F.loc[ix, "standing_dist_m"] = best["dist"].round(1).values
        F.loc[ix, "standing_n"] = best["n"].values
        F.loc[ix, "standing_area_m2"] = bb["area"].round().values
        # chance: the same marks moved 150 m east and 100 m north
        ctl = match(F["E"].values + 150.0, F["N"].values + 100.0, F["first_year"].values, F["cls"].values)
        control = {names[k]: int(v) for k, v in ctl["rank"].value_counts().items()}
        control["marks"] = int(len(F))

    # --- sites, kind, confidence, id
    xy = F[["E", "N"]].values
    pairs = cKDTree(xy).query_pairs(SITE_M, output_type="ndarray")
    n = len(F)
    _, lab = connected_components(coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n)), directed=False)
    F["site"] = lab
    F["n_marks"] = np.bincount(lab)[lab]
    F["kind"] = np.where(F["cls"] == "bar", "large", "house")
    two = F["first_year"] != F["last_year"]
    F["confidence"] = np.where(two | (F["standing_basis"] == "recorded"), "high",
                               np.where((F["cls"] == "bar") | F["ground"].isin(["tidal_marsh", "tidal_flat", "wetland"]) | F["builtup"], "low", "medium"))
    abbr = {"Brooklyn": "bk", "Harlem": "ha", "Staten Island": "si", "Hempstead": "he", "Oyster Bay": "ob"}
    first_sid = F["sheets"].str.split("+").str[0]
    F["id"] = [f"{abbr[SHEETS[s][1]]}{SHEETS[s][4] % 100}_{int(c):05d}_{int(r):05d}" for s, c, r in zip(first_sid, F["col"], F["row"])]
    lon, lat = to_ll.transform(F["E"].values, F["N"].values)
    F["lon"], F["lat"] = np.round(lon, 6), np.round(lat, 6)
    F = F.sort_values("id").reset_index(drop=True)

    def val(v):
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        if isinstance(v, (np.integer,)) or (isinstance(v, float) and v == int(v)):
            return int(v)
        if isinstance(v, np.bool_):
            return bool(v)
        return v
    props = ["id", "first_year", "last_year", "gone_by", "new_since", "n_marks", "site", "kind", "sheet", "confidence", "borough",
             "standing_bin", "standing_basis", "standing_year", "standing_year_src", "standing_dist_m", "standing_n", "standing_area_m2",
             "late_symbol", "earlier_unclear", "later_unclear", "builtup", "ground"]
    F["sheet"] = F["sheets"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fc = {"type": "FeatureCollection", "name": "farmsteads",
          "description": "Buildings drawn as separate marks on the USGS 15-minute sheets of the 1888-89 survey and its 1897 revision; see README.md",
          "features": []}
    for row in F.itertuples(index=False):
        d = row._asdict()
        p = {k: val(d[k]) for k in props}
        for k in ("standing_basis", "standing_year_src", "late_symbol", "ground"):
            p[k] = p[k] or None
        if p["standing_dist_m"] is not None:
            p["standing_dist_m"] = float(d["standing_dist_m"])
        fc["features"].append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [float(d["lon"]), float(d["lat"])]}, "properties": p})
    (OUT_DIR / "farmsteads.geojson").write_text(json.dumps(fc, separators=(",", ":")).replace('},{"type":"Feature"', '},\n{"type":"Feature"'))

    # --- coverage and numbers
    cov = {"type": "FeatureCollection", "name": "coverage", "features": []}
    for sid, sh in sheets.items():
        E, N = sh.px_to_utm(sh.neat_px[:, 0], sh.neat_px[:, 1])
        lo, la = to_ll.transform(E, N)
        f, quad, scale, printed, survey, collar, period = SHEETS[sid]
        ring = [[round(float(x), 6), round(float(y), 6)] for x, y in zip(lo, la)]
        cov["features"].append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring + [ring[0]]]},
                                "properties": {"sheet": sid, "quadrangle": quad, "scale": scale, "print_year": printed, "survey_year": survey, "collar": collar,
                                               "source_url": HTMC + f, "shift_model": res[sid]["shift"], "shift_rms_m": res[sid]["align"].get("rms_m"),
                                               "marks_kept": int(sum(m["keep"] for m in res[sid]["marks"])),
                                               "marks_in_city": int((F["sheets"].str.contains(sid)).sum())}})
    (OUT_DIR / "coverage.geojson").write_text(json.dumps(cov, indent=1))
    stats = {"features": int(len(F)), "outside_five_boroughs": region_n, "dropped_in_water": in_water,
             "by_borough": F.groupby("borough").size().to_dict(),
             "by_borough_first_last": {f"{b}|{int(a)}|{int(c)}": int(v) for (b, a, c), v in F.groupby(["borough", "first_year", "last_year"]).size().items()},
             "by_confidence": F.groupby("confidence").size().to_dict(), "by_kind": F.groupby("kind").size().to_dict(),
             "gone_by": {str(int(k)): int(v) for k, v in F["gone_by"].dropna().value_counts().sort_index().items()},
             "new_since_1889": int(F["new_since"].notna().sum()), "builtup": int(F["builtup"].sum()),
             "ground": F.groupby("ground").size().to_dict(), "late_sheets": late_info,
             "standing": {f"{b}|{k}": int(v) for (b, k), v in F[F["standing_basis"] != ""].groupby(["borough", "standing_basis"]).size().items()},
             "standing_by_src": {f"{b}|{k}|{s_}": int(v) for (b, k, s_), v in F[F["standing_basis"] != ""].groupby(["borough", "standing_basis", "standing_year_src"]).size().items()},
             "standing_control_shifted_150m": control,
             "sheets": {sid: {"kept": int(sum(m["keep"] for m in res[sid]["marks"])), "shift": res[sid]["shift"], "align": {k: v for k, v in res[sid]["align"].items() if k != "window_shifts_m"},
                              "thr": res[sid]["thr"]} for sid in res}}
    (OUT_DIR / "stats.json").write_text(json.dumps(stats, indent=1))
    log("export:", len(F), "features;", stats["by_borough"])
    return F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch", "detect", "export", "all"])
    ap.add_argument("--sheet")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    sids = [a.sheet] if a.sheet else None
    if a.cmd in ("fetch", "all"):
        fetch(sids)
    if a.cmd in ("detect", "all"):
        for sid in (sids or {**SHEETS, **LATE}):
            if sid in SHEETS:
                process(sid, a.force)
            else:
                process_late(sid, a.force)
    if a.cmd in ("export", "all"):
        export()


if __name__ == "__main__":
    main()
