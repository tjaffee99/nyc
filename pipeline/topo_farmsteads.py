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
DETECTOR_VERSION = 3

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
                      "dark": float(mx[sl][m].mean())})
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
                    "W": round(c["W"], 1), "fill": round(c["fill"], 2), "cls": c["cls"], "ctx": ctx, "dark": round(c["dark"]),
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
                 "mean_shift_m": [round(float(E.mean()), 1), round(float(N.mean()), 1)]})
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
        for sid in (sids or SHEETS):
            process(sid, a.force)


if __name__ == "__main__":
    main()
