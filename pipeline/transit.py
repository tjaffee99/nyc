"""Stage: transit — rail transit through time: the subway and the Staten Island Railway (real tracks,
every station, the service lines the viewer runs its trains on), the elevated lines that are gone, the
railroads of the city and of the counties around it, PATH and New Jersey's two light rail systems.

Sources
  * Track geometry of what exists: Overture transportation `rail` segments (OpenStreetMap,
    ODbL) of the region box — each track is its own line, with is_bridge / is_tunnel flags,
    level_rules and connectors (the track graph the height profile is smoothed over).
  * Service lines: MTA subway GTFS (shapes + stop order), one line per route, re-centred
    between its tracks; PATH, the Hudson-Bergen Light Rail and the Newark Light Rail on
    OpenStreetMap's route relations (RAPID; headways of PATH from the Port Authority's GTFS).
  * Dates: data/tables/transit_openings.csv — every stretch between two stations with its
    opening day (and closing day for what is gone), located by GTFS stop ids along a GTFS
    shape, or by stations along a line of data/manual/transit/elevated_lines.geojson; railroad,
    PATH and light rail rows (system `rail`) by line name inside a box;
    data/tables/transit_stations.csv — every station with opening / closing day.
    How the tables were assembled: data/manual/transit/README.md.
  * Demolished elevated lines: data/manual/transit/elevated_lines.geojson (OpenHistoricalMap
    geometry, CC0, or the centre line of the street the structure stood over).
  * Railroads: Overture standard-gauge tracks inside the map outline (extent.py), dated by the
    `rail` rows, else from OpenHistoricalMap's dated railway ways (CC0) by position, else from
    the nearest dated track; closed railroads from data/manual/transit/former_railroads.geojson
    (OpenHistoricalMap ways with an end date; OpenStreetMap's abandoned roadbeds with cited dates).

Outputs (formats unchanged from the Bay stage; the viewer reads them as they are)
  viewer/public/data/transit.bin.gz       tracks (BAYT columns: kind 6 railroad, 8 subway / el / PATH,
                                          10 light rail; width; years [start, end]; elevated: 0 ground,
                                          2 aerial, 4 tunnel)
  viewer/public/data/transit-lines.json   service lines: centreline (lon/lat offsets, z,
                                          cumulative m, opening year, tunnel flag, half track
                                          spacing), stop knots, vehicle, headway, closed gap
  viewer/public/data/transit-stations.json
  data/interim/transit/county_rail_*.csv  how the counties' track was dated, the rows against
                                          OpenHistoricalMap, track older than its ground

Viewer names: the viewer treats system 'bart' as heavy rail (platforms, label tier `station`)
and everything else as 'muni' (label only). Until the viewer learns New York's names the subway,
the Staten Island Railway, the elevated lines and PATH are written as 'bart', railroad and light
rail stations as 'muni'; vehicle keys 'bart' (B Division car), 'ebart' (A Division car; PATH's
cars are the same size), 'el' and 'lrv' (light rail) are used because the viewer keys platform
length and livery on them.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import zipfile
from collections import Counter, defaultdict

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from scipy.ndimage import median_filter
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point, Polygon, shape

from common import INTERIM, MANUAL, NYC_BBOX, NYC_CRS, OVERTURE_RELEASE, RAW, REGION_BBOX, TABLES, VIEWER_DATA, log, session
from export_columnar import write_columnar

ORIGIN = (-73.97, 40.73)
UTM = NYC_CRS
# kinds and elevation classes of the viewer's path sets (viewer/src/layers/roads.ts)
K_RAIL, K_BART, K_LIGHTRAIL = 6, 8, 10
EL_GROUND, EL_AERIAL, EL_TUNNEL = 0, 2, 4
GROUND_H = 0.45
EL_H = 8.5          # rail height of an elevated structure above the street (m)
SLOPE = 0.04        # steepest ramp between levels
TRANSIT = RAW / "transit"
GTFS_ZIP = RAW / "mta" / "gtfs_subway.zip"
OHM_URL = "https://overpass-api.openhistoricalmap.org/api/interpreter"
UA = "NYCThroughTime-research/0.1"
OHM_QUERY = ('[out:json][timeout:240];(way["railway"]({s},{w},{n},{e});'
             'node["railway"~"station|halt|stop"]({s},{w},{n},{e}););out body geom;')

# Vehicles: car [length, width, height] m, gap between cars, cruise speed (m/s), acceleration
# (m/s^2), dwell (s). Real car dimensions; the running is procedural.
VEHICLES = {
    # B Division (lettered lines, Staten Island Railway): 60 ft cars, R160: 18.35 x 2.98 x 3.70 m
    "bart": {"car": [18.35, 2.98, 3.7], "gap": 0.6, "vmax": 20.0, "acc": 1.1, "dwell": 30},
    # A Division (numbered lines, 42 St shuttle): 51 ft cars, R142: 15.65 x 2.62 x 3.62 m
    "ebart": {"car": [15.65, 2.62, 3.62], "gap": 0.6, "vmax": 20.0, "acc": 1.1, "dwell": 30},
    # Manhattan Railway / BRT elevated cars: about 47 ft x 8 ft 9 in
    "el": {"car": [14.3, 2.67, 3.6], "gap": 0.6, "vmax": 11.0, "acc": 0.6, "dwell": 25},
    # NJ Transit's light rail car (Kinki Sharyo, 90 ft as delivered): the dimensions are from memory of the
    # fleet's data sheet - estimated, not cited
    "lrv": {"car": [27.4, 2.68, 3.7], "gap": 0.8, "vmax": 16.0, "acc": 1.0, "dwell": 20},
}
# Rapid transit of the counties: service lines on OpenStreetMap's route relations (one per direction; the
# centreline is the middle between the two), trains like the subway's. PATH is written as system 'bart'
# with the A Division car key 'ebart' (PA5 cars are 51 ft, as the IRT's); the two light rail systems as
# 'muni' with 'lrv'. Headways: PATH from the Port Authority's GTFS (weekday trips), light rail 10 minutes
# (estimated: NJ Transit's GTFS is behind a login and is not used). Cars per train: PATH 8 on the Newark
# line (Wikipedia, PATH), 7 elsewhere (estimated); light rail 2 / 1 (estimated).
RAPID = [
    # id, name, system, vehicle, cars, headway s (None: GTFS), colour, track set, relations (out, back), GTFS route
    ("PATH-NWK", "PATH Newark - World Trade Center", "bart", "ebart", 8, None, "d93a30", "path", (1468867, 7943864), "862"),
    ("PATH-HOB-WTC", "PATH Hoboken - World Trade Center", "bart", "ebart", 7, None, "65c100", "path", (1468847, 7943872), "860"),
    ("PATH-JSQ-33", "PATH Journal Square - 33rd Street", "bart", "ebart", 7, None, "ff9900", "path", (1468832, 7943925), "861"),
    ("PATH-HOB-33", "PATH Hoboken - 33rd Street", "bart", "ebart", 7, None, "4d92fb", "path", (1468831, 7943884), "859"),
    ("HBLR-WS", "Hudson-Bergen Light Rail Tonnelle Avenue - West Side Avenue", "muni", "lrv", 2, 600, "0f6cb7", "lr", (1468928, 9997056), None),
    ("HBLR-8", "Hudson-Bergen Light Rail Hoboken Terminal - 8th Street", "muni", "lrv", 2, 600, "0f6cb7", "lr", (1378219, 9997058), None),
    ("NLR-GS", "Newark Light Rail Newark Penn Station - Grove Street", "muni", "lrv", 1, 600, "7b2b83", "lr", (1380716, 9821042), None),
    ("NLR-BS", "Newark Light Rail Newark Penn Station - Broad Street Station", "muni", "lrv", 1, 600, "7b2b83", "lr", (2634557, 9821064), None),
]
RAPID_ROUTES = TRANSIT / "osm" / "osm_routes_region.json"   # data/manual/transit/tools/fetch_region.py
PATH_GTFS = TRANSIT / "gtfs_path"
CITY_RING = MANUAL / "transit" / "city_ring.json"            # the five boroughs' outline (for the counties' statistics)
CARS = {"7": 11, "GS": 6, "FS": 2, "H": 5, "SI": 5, "G": 5, "C": 8, "J": 8, "M": 8, "L": 8}
# routes with trains; a route with two branches runs two lines at twice the headway each
LINES = [
    # id, GTFS route, shape (None: the most used of its longest shapes), headway factor
    ("1", "1", None, 1), ("2", "2", None, 1), ("3", "3", None, 1), ("4", "4", None, 1), ("5", "5", "5..S08R", 1),
    ("6", "6", None, 1), ("7", "7", None, 1), ("GS", "GS", None, 1),
    ("A", "A", "A..S58R", 2), ("A-Lefferts", "A", "A..S57R", 2), ("B", "B", None, 1), ("C", "C", None, 1),
    ("D", "D", None, 1), ("E", "E", None, 1), ("F", "F", None, 1), ("G", "G", None, 1), ("J", "J", None, 1),
    ("L", "L", None, 1), ("M", "M", None, 1), ("N", "N", None, 1), ("Q", "Q", None, 1), ("R", "R", None, 1),
    ("W", "W", "N..N72R", 1), ("FS", "FS", None, 1), ("H", "H", None, 1), ("SI", "SI", None, 1),
]
# Decks of the big bridges (clearance above mean high water): tracks flagged as bridge inside
# the box ride at this height; ramps come from the track graph.
BRIDGE_DECKS = [
    # name, lon0, lat0, lon1, lat1, deck m, source
    ("Manhattan Bridge", -73.9955, 40.7005, -73.9840, 40.7165, 41.0, "https://en.wikipedia.org/wiki/Manhattan_Bridge"),
    ("Williamsburg Bridge", -73.9850, 40.7085, -73.9620, 40.7190, 41.0, "https://en.wikipedia.org/wiki/Williamsburg_Bridge"),
    ("Culver Viaduct (Smith-Ninth Streets)", -74.0005, 40.6725, -73.9925, 40.6760, 26.7, "https://en.wikipedia.org/wiki/Smith–Ninth_Streets_station"),
    ("Hell Gate Bridge", -73.9300, 40.7775, -73.9150, 40.7870, 41.0, "https://en.wikipedia.org/wiki/Hell_Gate_Bridge"),
    ("Queensboro Bridge", -73.9650, 40.7520, -73.9440, 40.7620, 40.0, "https://en.wikipedia.org/wiki/Queensboro_Bridge"),
    ("Brooklyn Bridge", -74.0040, 40.7020, -73.9920, 40.7120, 38.7, "https://en.wikipedia.org/wiki/Brooklyn_Bridge"),
]
PATH_NAMES = ("PATH", "Newark - World Trade Center", "Hoboken - World Trade Center", "Journal Square - 33rd Street",
              "Hoboken - 33rd Street", "Uptown Hudson Tubes", "Downtown Hudson Tubes")
STRUCT_KIND = {"Subway": "underground", "Elevated": "elevated", "Viaduct": "elevated", "Open Cut": "surface",
               "At Grade": "surface", "Embankment": "surface"}


def decyear(s: str) -> float:
    s = str(s).strip()
    if len(s) == 4:
        s += "-07-01"
    elif len(s) == 7:
        s += "-15"
    d = dt.date.fromisoformat(s[:10])
    return round(d.year + (d.timetuple().tm_yday - 1) / 365.25, 3)


# ---------------------------------------------------------------- ground, extent
class Ground:
    """Terrain height (terrain_grid.py grids); 0.9 m everywhere when the grids are missing."""

    def __init__(self):
        self.grids = []
        for name in ("detail", "region"):
            f, m = INTERIM / f"grid_{name}_elev.npy", INTERIM / f"grid_{name}_meta.json"
            if f.exists() and m.exists():
                e = np.load(f)
                self.grids.append((json.loads(m.read_text()), np.where(e < -500, 0, e)))
        if not self.grids:
            log("transit: elevation grids missing - ground = 0")

    def __call__(self, lon, lat):
        lon = np.asarray(lon, float)
        lat = np.asarray(lat, float)
        X = np.radians(lon) * 6378137.0
        Y = 6378137.0 * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
        out = np.full(lon.shape, np.nan)
        for g, e in self.grids:
            c = (X - g["X0"]) / g["res"]
            r = (g["Y0"] - Y) / g["res"]
            ok = np.isnan(out) & (c >= 0) & (r >= 0) & (c < g["cols"] - 1) & (r < g["rows"] - 1)
            c0 = np.floor(c[ok]).astype(int)
            r0 = np.floor(r[ok]).astype(int)
            fx = c[ok] - c0
            fy = r[ok] - r0
            out[ok] = (e[r0, c0] * (1 - fx) + e[r0, c0 + 1] * fx) * (1 - fy) + (e[r0 + 1, c0] * (1 - fx) + e[r0 + 1, c0 + 1] * fx) * fy
        return np.maximum(np.nan_to_num(out), 0.9)


def extent_poly():
    """The map's outline (extent.py writes it for the viewer); the download box without it."""
    for f in (MANUAL / "extent_ring.json", VIEWER_DATA / "map-extent.json"):
        if f.exists():
            return Polygon(json.loads(f.read_text())["ring"]).buffer(0.004)
    lon0, lat0, lon1, lat1 = NYC_BBOX
    return Polygon([(lon0, lat0), (lon1, lat0), (lon1, lat1), (lon0, lat1)])


def to_utm(lon, lat):
    s = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs=4326).to_crs(UTM)
    return np.column_stack([s.x.values, s.y.values])


def to_ll(xy):
    s = gpd.GeoSeries(gpd.points_from_xy(xy[:, 0], xy[:, 1]), crs=UTM).to_crs(4326)
    return s.x.values, s.y.values


def densify_xy(xy, step=20.0):
    out = [xy[0]]
    for a, b in zip(xy[:-1], xy[1:]):
        d = float(np.hypot(*(b - a)))
        if d < 0.5:
            continue
        n = int(math.ceil(d / step))
        for k in range(1, n + 1):
            out.append(a + (b - a) * (k / n))
    return np.array(out)


def offset_xy(xy, d):
    """The polyline moved d metres to its left (averaged normals)."""
    t = np.gradient(xy, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-6)
    return xy + np.column_stack([-t[:, 1], t[:, 0]]) * d


def flag_ranges(rules, key=None):
    """Overture rail_flags / level_rules -> list of (lo, hi, value)."""
    out = []
    if rules is None:
        return out
    for r in rules:
        b = r.get("between")
        lo, hi = (0.0, 1.0) if b is None else (float(b[0]), float(b[1]))
        if key is None:
            out.append((lo, hi, float(r.get("value", 0) or 0)))
        else:
            vals = r.get("values")
            if vals is not None and key in list(vals):
                out.append((lo, hi, 1.0))
    return out


# ---------------------------------------------------------------- downloads
def downloads():
    g = TRANSIT / "gtfs"
    if not (g / "shapes.txt").exists():
        g.mkdir(parents=True, exist_ok=True)
        zipfile.ZipFile(GTFS_ZIP).extractall(g)
    ohm = TRANSIT / "ohm" / "ohm_rail.json"
    if not ohm.exists():
        ohm.parent.mkdir(parents=True, exist_ok=True)
        lon0, lat0, lon1, lat1 = NYC_BBOX
        r = session().post(OHM_URL, data={"data": OHM_QUERY.format(s=lat0, w=lon0, n=lat1, e=lon1)}, timeout=400)
        r.raise_for_status()
        ohm.write_bytes(r.content)
    ohm_r = TRANSIT / "ohm" / "ohm_rail_region.json"  # the counties (the wider box); also written by tools/fetch_region.py
    if not ohm_r.exists():
        lon0, lat0, lon1, lat1 = REGION_BBOX
        se = session()
        se.headers["User-Agent"] = UA
        r = se.post(OHM_URL, data={"data": OHM_QUERY.format(s=lat0, w=lon0, n=lat1, e=lon1)}, timeout=600)
        r.raise_for_status()
        ohm_r.write_bytes(r.content)
    return g, [ohm, ohm_r]


# ---------------------------------------------------------------- GTFS
def load_gtfs(g):
    stops = pd.read_csv(g / "stops.txt", dtype=str)
    parent = dict(zip(stops.stop_id, stops.parent_station.fillna("")))
    par = stops[stops.location_type == "1"]
    pxy = dict(zip(par.stop_id, to_utm(par.stop_lon.astype(float).values, par.stop_lat.astype(float).values)))
    trips = pd.read_csv(g / "trips.txt", dtype=str)
    rep = trips.groupby("shape_id").agg(trip=("trip_id", "first"), route=("route_id", "first"), n=("trip_id", "size")).reset_index()
    st = pd.read_csv(g / "stop_times.txt", dtype=str, usecols=["trip_id", "stop_id", "stop_sequence"])
    st = st[st.trip_id.isin(rep.trip)]
    st["stop_sequence"] = st.stop_sequence.astype(int)
    seqs = {t: s.sort_values("stop_sequence").stop_id.map(lambda x: parent.get(x) or x).tolist() for t, s in st.groupby("trip_id")}
    shapes = pd.read_csv(g / "shapes.txt")
    sxy = to_utm(shapes.shape_pt_lon.values, shapes.shape_pt_lat.values)
    shapes["x"], shapes["y"] = sxy[:, 0], sxy[:, 1]
    geo = {sid: s.sort_values("shape_pt_sequence")[["x", "y"]].values for sid, s in shapes.groupby("shape_id")}
    routes = pd.read_csv(g / "routes.txt", dtype=str).set_index("route_id")
    wk = trips[(trips.service_id == "Weekday") & (trips.direction_id == "0")].groupby("route_id").size().to_dict()
    info = {}
    for r in rep.itertuples():
        if r.shape_id in geo:
            km = float(np.hypot(*np.diff(geo[r.shape_id], axis=0).T).sum()) / 1000
            info[r.shape_id] = {"route": r.route, "n": r.n, "km": km, "stops": seqs[r.trip]}
    return {"pxy": pxy, "geo": geo, "info": info, "routes": routes, "weekday_trips": wk}


def shape_stops(xy, stops, pxy):
    """Vertex index of each stop along a densified shape, in travel order."""
    idx, prev = [], 0
    for s in stops:
        d = np.hypot(*(xy[prev:] - pxy[s]).T)
        k = prev + int(np.argmin(d))
        idx.append(k)
        prev = k
    return idx


def division(line: str) -> str:
    """'A' numbered lines, 'B' lettered lines, 'S' Staten Island Railway, '' unknown."""
    if line.startswith("IRT"):
        return "A"
    if line.startswith(("BMT", "IND")):
        return "B"
    if line.startswith("Staten Island") or line.startswith("SIR"):
        return "S"
    return ""


# ---------------------------------------------------------------- dated network (subway, SIR)
def dated_network(openings, gt, stations):
    """Every stretch of transit_openings.csv traced along its GTFS shape -> points with a year,
    a division and a level ('u' between two underground stations, 'e' between two stations in the
    open, 'm' where the stretch changes level)."""
    under = {r.code: r.structure == "Subway" for r in stations.itertuples()}
    P, Y, D, L = [], [], [], []
    cache = {}
    for r in openings[openings.system.isin(["subway", "sir"])].itertuples():
        if r.via not in gt["geo"]:
            log(f"transit: {r.route_id}: shape {r.via} not in GTFS")
            continue
        if r.via not in cache:
            xy = densify_xy(gt["geo"][r.via], 10.0)
            stops = gt["info"][r.via]["stops"]
            cache[r.via] = (xy, dict(zip(stops, shape_stops(xy, stops, gt["pxy"]))))
        xy, at = cache[r.via]

        def locate(v):
            if v in at:
                return at[v]
            lon, lat = map(float, v.split())
            return int(np.argmin(np.hypot(*(xy - to_utm([lon], [lat])[0]).T)))

        try:
            a, b = sorted((locate(r.from_stop), locate(r.to_stop)))
        except (ValueError, KeyError):
            log(f"transit: {r.route_id}: cannot place {r.from_stop} / {r.to_stop} on {r.via}")
            continue
        if b - a < 1:
            continue
        ends = [under.get(r.from_stop), under.get(r.to_stop)]
        lvl = "u" if ends == [True, True] else "e" if ends == [False, False] else "m"
        P.append(xy[a:b + 1])
        Y.append(np.full(b - a + 1, decyear(r.opened)))
        D += [division(r.line)] * (b - a + 1)
        L += [lvl] * (b - a + 1)
    P, Y, D, L = np.concatenate(P), np.concatenate(Y), np.array(D), np.array(L)
    trees = {}
    for d in ("A", "B", "S", ""):
        for lv in ("u", "e", ""):
            m = ((D == d) if d else np.ones(len(D), bool)) & (np.isin(L, (lv, "m")) if lv else np.ones(len(D), bool))
            if m.any():
                trees[(d, lv)] = (cKDTree(P[m]), Y[m])
    log(f"transit: dated network: {len(P) * 10 / 1000:.0f} km of stretches from transit_openings.csv")
    return trees


def year_from(trees, xy, div, reach, tn=None):
    """Opening year of the dated stretch at each point: of the same division and level where
    there is one (then any level, then any division). Where several stretches meet or overlap (a
    junction station, a branch leaving a trunk) the earliest of those about as near as the
    nearest wins."""
    y = np.full(len(xy), np.nan)
    groups = [(np.ones(len(xy), bool), "")] if tn is None else [(np.asarray(tn, bool), "u"), (~np.asarray(tn, bool), "e")]
    for mask, lvl in groups:
        if not mask.any():
            continue
        yy = np.full(int(mask.sum()), np.nan)
        for key in [(d, lv) for d in ([div, ""] if div else [""]) for lv in ([lvl, ""] if lvl else [""])]:
            if key not in trees:
                continue
            t, ty = trees[key]
            k = min(10, len(ty))
            dd, ii = t.query(xy[mask], k=k, distance_upper_bound=reach)
            dd, ii = dd.reshape(len(yy), -1), ii.reshape(len(yy), -1)
            near = np.isfinite(dd) & (dd <= np.maximum(dd[:, :1] + 10.0, 12.0))
            cand = np.where(near, ty[np.minimum(ii, len(ty) - 1)], np.inf).min(axis=1)
            ok = np.isfinite(cand) & np.isnan(yy)
            yy[ok] = cand[ok]
        y[mask] = yy
    return y


def ohm_dated(ohm_files):
    """OpenHistoricalMap railway ways still standing: sample points with their start year (the city's
    download first, then the ways only the region download has)."""
    P, Y, seen = [], [], set()
    ways = [w for f in ohm_files for w in json.load(open(f))["elements"]]
    for w in ways:
        t = w.get("tags", {})
        if w["type"] != "way" or t.get("railway") not in ("subway", "rail", "light_rail") or t.get("end_date") or not t.get("start_date"):
            continue
        if w["id"] in seen:
            continue
        seen.add(w["id"])
        try:
            y = decyear(t["start_date"])
        except ValueError:
            continue
        g = w["geometry"]
        xy = densify_xy(to_utm([p["lon"] for p in g], [p["lat"] for p in g]), 15.0)
        P.append(xy)
        Y.append(np.full(len(xy), y))
    return cKDTree(np.concatenate(P)), np.concatenate(Y)


# ---------------------------------------------------------------- tracks (Overture)
def read_rail(poly):
    r = gpd.read_parquet(RAW / "overture" / OVERTURE_RELEASE / "rail.parquet")
    r = r.set_crs(4326, allow_override=True)
    r = r[r.geometry.geom_type == "LineString"]

    def has(f, key):
        return f is not None and any(key in list(e.get("values", [])) for e in f)

    bad = r.rail_flags.map(lambda f: has(f, "is_abandoned") or has(f, "is_disused") or has(f, "is_under_construction"))
    r = r[~bad.values]
    shapely.prepare(poly)
    r = r[shapely.intersects(poly, r.geometry.values)].reset_index(drop=True)
    r["name"] = r["name"].fillna("")
    # PATH: its named tracks, and every rapid transit track on the New Jersey side (the Staten Island
    # Railway lies south of 40.65)
    mid = shapely.line_interpolate_point(r.geometry.values, 0.5, normalized=True)
    nj = (shapely.get_x(mid) < -74.02) & (shapely.get_y(mid) > 40.68)
    r["is_path"] = (r["class"] == "subway").values & (r["name"].isin(PATH_NAMES).values | nj)
    return r


def sample_tracks(r, step=15.0):
    """Segments -> samples with bridge / tunnel / level, joined into a graph by the connectors."""
    ru = r.to_crs(UTM)
    segs, conn = [], defaultdict(list)
    n0 = 0
    for i, row in enumerate(r.itertuples()):
        g = ru.geometry.iloc[i]
        L = g.length
        if L < 2:
            continue
        n = max(2, int(math.ceil(L / step)) + 1)
        f = np.linspace(0, 1, n)
        xy = np.array([g.interpolate(x, normalized=True).coords[0][:2] for x in f])
        lev = np.zeros(n)
        for lo, hi, v in flag_ranges(row.level_rules):
            lev[(f >= lo - 1e-9) & (f <= hi + 1e-9)] = v
        br = np.zeros(n, bool)
        for lo, hi, _ in flag_ranges(row.rail_flags, "is_bridge"):
            br[(f >= lo - 1e-9) & (f <= hi + 1e-9)] = True
        tn = np.zeros(n, bool)
        for lo, hi, _ in flag_ranges(row.rail_flags, "is_tunnel"):
            tn[(f >= lo - 1e-9) & (f <= hi + 1e-9)] = True
        tn |= lev <= -1
        up = (br | (lev >= 1)) & ~tn
        s = {"xy": xy, "f": f, "L": L, "lev": lev, "tn": tn, "up": up, "name": row.name, "cls": row[r.columns.get_loc("class") + 1],
             "n0": n0, "div": division(row.name), "path": bool(getattr(row, "is_path", False))}
        if row.connectors is not None:
            for c in row.connectors:
                conn[c["connector_id"]].append(n0 + int(round(float(c.get("at") or 0) * (n - 1))))
        segs.append(s)
        n0 += n
    return segs, conn, n0


def height_profile(segs, conn, n, ground):
    """Rail height above ground for every sample: flat on its structure, ramps of at most SLOPE
    between levels, carried across segments over the track graph (h_i = min_j T_j + SLOPE*d_ij)."""
    T = np.full(n, GROUND_H)
    rows, cols, w = [], [], []
    lon0, lat0, lon1, lat1, deck = (np.array([b[k] for b in BRIDGE_DECKS]) for k in (1, 2, 3, 4, 5))
    for s in segs:
        k = np.arange(s["n0"], s["n0"] + len(s["xy"]))
        t = np.where(s["up"], EL_H + 4.5 * np.maximum(s["lev"] - 1, 0), GROUND_H)
        if s["up"].any():
            lon, lat = to_ll(s["xy"])
            g = ground(lon, lat)
            for b in range(len(deck)):
                inside = s["up"] & (lon >= lon0[b]) & (lon <= lon1[b]) & (lat >= lat0[b]) & (lat <= lat1[b])
                t[inside] = np.maximum(t[inside], deck[b] - g[inside])
        T[k] = t
        d = np.hypot(*np.diff(s["xy"], axis=0).T)
        rows += list(k[:-1])
        cols += list(k[1:])
        w += list(np.maximum(d, 0.01))
    for nodes in conn.values():
        for a in nodes[1:]:
            rows.append(nodes[0])
            cols.append(a)
            w.append(0.01)
    # virtual source n: reaching node j costs T_j / SLOPE
    rows += [n] * n
    cols += list(range(n))
    w += list(T / SLOPE)
    m = coo_matrix((w, (rows, cols)), shape=(n + 1, n + 1))
    dist = dijkstra(m, directed=False, indices=n)
    h = np.minimum(T, SLOPE * dist[:n])
    for s in segs:
        k = slice(s["n0"], s["n0"] + len(s["xy"]))
        s["h"] = np.where(s["tn"], GROUND_H, h[k])
    return segs


def subway_tracks(r, ground, trees, ohm):
    sub = r[(r["class"] == "subway") & ~r["is_path"]].reset_index(drop=True)
    segs, conn, n = sample_tracks(sub)
    height_profile(segs, conn, n, ground)
    otree, oy = ohm
    undated = 0
    for s in segs:
        y = year_from(trees, s["xy"], s["div"], 45.0, s["tn"])
        miss = np.isnan(y)
        if miss.any():  # yard and connecting tracks: OpenHistoricalMap's date, else the nearest dated stretch
            dd, ii = otree.query(s["xy"][miss], distance_upper_bound=12.0)
            ok = np.isfinite(dd)
            y[np.nonzero(miss)[0][ok]] = oy[ii[ok]]
            miss = np.isnan(y)
            if miss.any():
                y[miss] = year_from(trees, s["xy"][miss], s["div"], 1500.0)
                undated += int(np.isnan(y).sum())
        s["year"] = y
        s["end"] = np.full(len(y), 9999.0)
    segs = [s for s in segs if not np.isnan(s["year"]).any()]
    log(f"transit: {len(segs)} subway track segments ({sum(s['L'] for s in segs) / 1000:.0f} km of track), {undated} samples undated")
    return segs


# ---------------------------------------------------------------- service lines
def pick_shape(gt, route, shape):
    if shape:
        return shape
    c = [(k, v) for k, v in gt["info"].items() if v["route"] == route]
    top = max(v["km"] for _, v in c)
    return max((kv for kv in c if kv[1]["km"] >= 0.85 * top), key=lambda kv: kv[1]["n"])[0]


def build_line(spec, xy, segs, tr, ground, years, stops_s, knots_veh):
    """One service line from a centreline: centred between its tracks, heights from them."""
    tr_xy, tr_h, tr_tn, tr_seg, tree = tr
    xy = densify_xy(xy, 20.0)
    tang = np.gradient(xy, axis=0)
    tang /= np.maximum(np.linalg.norm(tang, axis=1, keepdims=True), 1e-6)
    nrm = np.column_stack([-tang[:, 1], tang[:, 0]])
    div = spec["div"]
    ok_seg = np.array([(not s["div"]) or (not div) or s["div"] == div for s in segs]) if segs else np.zeros(0, bool)
    shift = np.zeros(len(xy))
    half = np.full(len(xy), np.nan)
    if tree is not None:
        for k, idx in enumerate(tree.query_ball_point(xy, 7.0)):
            idx = [j for j in idx if ok_seg[tr_seg[j]]]
            if not idx:
                continue
            off = (tr_xy[idx] - xy[k]) @ nrm[k]
            pos, neg = off[off > 0.6], off[off < -0.6]
            if len(pos) and len(neg):
                shift[k] = (pos.max() + neg.min()) / 2
                half[k] = (pos.max() - neg.min()) / 2
        shift = pd.Series(shift).rolling(5, center=True, min_periods=1).median().values
        xy = xy + nrm * shift[:, None]
    half = pd.Series(half).rolling(7, center=True, min_periods=1).median().fillna(spec.get("half", 2.0)).values
    half = np.clip(half, 1.4, 9.0)
    h = np.full(len(xy), spec.get("h", GROUND_H))
    tn = np.zeros(len(xy), bool)
    if tree is not None:
        # which tracks are the line's own where lines are stacked (an elevated line over a subway):
        # the nearest tunnel track or the nearest track in the open, without switching between
        # the two more often than the tracks force it to (two-state shortest path along the line)
        mine = ok_seg[tr_seg]
        P, H, TN = tr_xy[mine], tr_h[mine], tr_tn[mine]
        cost, pick = np.full((len(xy), 2), 60.0), np.full((len(xy), 2), -1)
        for state, m in ((0, TN), (1, ~TN)):
            if m.any():
                d, i = cKDTree(P[m]).query(xy, distance_upper_bound=25.0)
                ok = np.isfinite(d)
                cost[ok, state] = d[ok]
                pick[ok, state] = np.nonzero(m)[0][i[ok]]
        acc, back = cost[0].copy(), np.zeros((len(xy), 2), int)
        for k in range(1, len(xy)):
            stay, switch = acc, acc[::-1] + 150.0
            back[k] = np.where(stay <= switch, [0, 1], [1, 0])
            acc = np.minimum(stay, switch) + cost[k]
        state = np.zeros(len(xy), int)
        state[-1] = int(np.argmin(acc))
        for k in range(len(xy) - 1, 0, -1):
            state[k - 1] = back[k][state[k]]
        j = pick[np.arange(len(xy)), state]
        tn = state == 0
        h = np.where(j >= 0, H[np.maximum(j, 0)], GROUND_H)
        h[tn] = GROUND_H
    lon, lat = to_ll(xy)
    # wheels on the drawn rails: ground tracks are lifted 0.9 m in the viewer (terrain bulge)
    z = ground(lon, lat) + np.where(tn, GROUND_H, np.where(h > 4, h, GROUND_H + 0.9))
    cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
    yv = years(xy, tn)
    line = LineString(xy)
    knots = knots_for([line.project(Point(p)) for p in stops_s], float(cum[-1]), knots_veh)
    out = {"id": spec["id"], "name": spec["name"], "system": spec["system"], "veh": spec["veh"], "cars": spec["cars"],
           "headway": spec["headway"], "color": spec["color"], "gap": spec.get("gap"),
           "lon": np.round(lon - ORIGIN[0], 6).tolist(), "lat": np.round(lat - ORIGIN[1], 6).tolist(),
           "z": np.round(z, 1).tolist(), "cum": np.round(cum, 1).tolist(), "year": np.round(yv, 2).tolist(),
           "tunnel": tn.astype(int).tolist(), "half": np.round(half, 1).tolist(), "knots": knots}
    log(f"transit: line {spec['id']}: {cum[-1] / 1000:.1f} km, {len(knots)} stops, {tn.mean() * 100:.0f}% tunnel, "
        f"{(h > 4).mean() * 100:.0f}% aerial, opens {np.nanmin(yv):.2f}-{np.nanmax(yv):.2f}")
    return out, xy


def run_time(D, vmax, acc):
    d_acc = vmax * vmax / (2 * acc)
    if D < 2 * d_acc:
        return 2 * math.sqrt(D / acc)
    return 2 * vmax / acc + (D - 2 * d_acc) / vmax


def knots_for(stops_s, total, veh):
    v = VEHICLES[veh]
    s = [0.0] + sorted(float(x) for x in stops_s if 60 < float(x) < total - 60) + [total]
    merged = [s[0]]
    for x in s[1:]:
        if x - merged[-1] > 60:
            merged.append(x)
    t, out = 0.0, []
    for k, x in enumerate(merged):
        if k:
            t += run_time(x - merged[k - 1], v["vmax"], v["acc"])
        dwell = 0.0 if k in (0, len(merged) - 1) else v["dwell"]
        out.append([round(x, 1), round(t, 1), round(t + dwell, 1)])
        t += dwell
    return out


def subway_lines(gt, segs, ground, trees):
    tr = (np.concatenate([s["xy"] for s in segs]), np.concatenate([s["h"] for s in segs]),
          np.concatenate([s["tn"] for s in segs]), np.concatenate([np.full(len(s["xy"]), q) for q, s in enumerate(segs)]))
    tr = (*tr, cKDTree(tr[0]))
    out, geo = [], []
    for lid, route, shp, hf in LINES:
        sid = pick_shape(gt, route, shp)
        info = gt["info"][sid]
        rt = gt["routes"].loc[route]
        div = "S" if route == "SI" else "A" if route[0].isdigit() or route == "GS" else "B"
        veh = "ebart" if div == "A" else "bart"
        headway = 20 * 3600 / max(gt["weekday_trips"].get(route, 60), 1) * hf
        spec = {"id": lid, "name": f"{rt.route_short_name} {rt.route_long_name}".strip(), "system": "bart", "veh": veh,
                "cars": CARS.get(route, 10), "headway": int(round(headway / 30) * 30), "color": rt.route_color or "808183",
                "div": div}

        def years(xy, tn, div=div):
            y = year_from(trees, xy, div, 60.0, tn)
            miss = np.isnan(y)
            if miss.any():
                y[miss] = year_from(trees, xy[miss], div, 5000.0)
            return median_filter(y, size=13, mode="nearest")

        ol, xy = build_line(spec, gt["geo"][sid], segs, tr, ground, years, [gt["pxy"][s] for s in info["stops"]], veh)
        out.append(ol)
        geo.append(xy)
    return out, geo


# ---------------------------------------------------------------- track runs -> paths
def path_items(segs, ground, kind, width, poly):
    """Split every segment where its class (tunnel / aerial / ground) or its years change, and
    where it leaves the map."""
    items = []
    for s in segs:
        lon, lat = to_ll(s["xy"])
        z = ground(lon, lat) + s["h"]
        y0 = np.round(median_filter(s["year"], size=9, mode="nearest"), 2)
        y1 = np.round(s["end"], 2)
        cls = np.where(s["tn"], EL_TUNNEL, np.where(s["h"] > 4, EL_AERIAL, EL_GROUND))
        cls = np.where(shapely.contains_xy(poly, lon, lat), cls, -1)
        a = 0
        for k in range(1, len(cls) + 1):
            if k == len(cls) or cls[k] != cls[a] or y0[k] != y0[a] or y1[k] != y1[a]:
                if cls[a] < 0:
                    a = k
                    continue
                b = min(k + 1, len(cls)) if k == len(cls) or cls[k] >= 0 else k
                if b - a >= 2 and y0[a] < y1[a]:
                    items.append((lon[a:b], lat[a:b], z[a:b], kind, width, float(y0[a]), float(y1[a]), int(cls[a])))
                a = k
    return items


def write_paths3d(path, items):
    starts, pos, kinds, widths, years, elev = [0], [], [], [], [], []
    for lon, lat, z, kind, width, y0, y1, el in items:
        pos.append(np.column_stack([lon - ORIGIN[0], lat - ORIGIN[1], z]).ravel())
        starts.append(starts[-1] + len(lon))
        kinds.append(kind)
        widths.append(width)
        years.extend((y0, y1))
        elev.append(el)
    write_columnar(path, {
        "start_indices|shuffle": np.asarray(starts, np.uint32),
        "positions|shuffle": np.concatenate(pos).astype(np.float32),
        "kind": np.asarray(kinds, np.uint8),
        "width": np.clip(np.rint(widths), 1, 255).astype(np.uint8),
        "years": np.asarray(years, np.float32),
        "elevated": np.asarray(elev, np.uint8),
    }, origin=ORIGIN, counts={"paths": len(kinds), "vertices": starts[-1]})
    log(f"transit: wrote {path.name}: {len(kinds)} paths, {starts[-1]} vertices")


# ---------------------------------------------------------------- lines that are gone
def manual_lines(openings, stations, ground):
    """Demolished elevated lines: transit_openings.csv rows of system 'el', each a stretch between
    two stations (or lon/lat points) along a line of elevated_lines.geojson, with opening and
    closing day. -> track segments (two tracks on a deck) and one service line per run of
    stretches that closed together."""
    f = MANUAL / "transit" / "elevated_lines.geojson"
    rows = openings[openings.system == "el"]
    if not f.exists() or not len(rows):
        return [], [], []
    feats = {x["properties"]["id"]: x for x in json.load(open(f))["features"]}
    st_ll = {r.code: (float(r.lon), float(r.lat)) for r in stations.itertuples() if r.lon}
    segs, lines, geo = [], [], []
    by_line = defaultdict(list)
    for r in rows.itertuples():
        ft = feats.get(r.via)
        if ft is None:
            log(f"transit: {r.route_id}: no line {r.via} in elevated_lines.geojson")
            continue
        g = shape(ft["geometry"])
        xy = densify_xy(to_utm(*np.array(g.coords)[:, :2].T), 10.0)

        def locate(v):
            lon, lat = st_ll[v] if v in st_ll else map(float, v.split())
            return int(np.argmin(np.hypot(*(xy - to_utm([lon], [lat])[0]).T)))

        try:
            a, b = sorted((locate(r.from_stop), locate(r.to_stop)))
        except (KeyError, ValueError):
            log(f"transit: {r.route_id}: cannot place {r.from_stop} / {r.to_stop}")
            continue
        if b - a < 2:
            continue
        y0, y1 = decyear(r.opened), decyear(r.closed) if r.closed else 9999.0
        by_line[r.via].append((a, b, y0, y1, ft))
    for via, parts in by_line.items():
        ft = parts[0][4]
        pr = ft["properties"]
        g = shape(ft["geometry"])
        xy = densify_xy(to_utm(*np.array(g.coords)[:, :2].T), 10.0)
        lon, lat = to_ll(xy)
        deck = np.full(len(xy), float(pr.get("height_m") or EL_H))
        for name, lon0, lat0, lon1, lat1, dk, _ in BRIDGE_DECKS:
            if pr.get("bridge") == name:
                inside = (lon >= lon0) & (lon <= lon1) & (lat >= lat0) & (lat <= lat1)
                deck[inside] = np.maximum(deck[inside], dk - ground(lon, lat)[inside])
        cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
        for k in range(1, len(deck)):  # ramps onto a bridge deck
            deck[k] = min(deck[k], deck[k - 1] + SLOPE * (cum[k] - cum[k - 1]))
        for k in range(len(deck) - 2, -1, -1):
            deck[k] = min(deck[k], deck[k + 1] + SLOPE * (cum[k + 1] - cum[k]))
        y0v, y1v = np.full(len(xy), np.nan), np.full(len(xy), np.nan)
        for a, b, y0, y1, _ in parts:
            y0v[a:b + 1] = np.fmin(y0v[a:b + 1], y0)
            y1v[a:b + 1] = np.fmax(y1v[a:b + 1], y1)
        have = ~np.isnan(y0v)
        spacing = float(pr.get("track_spacing_m") or 3.8)
        # tracks: runs of dated vertices, two tracks
        k = 0
        while k < len(xy):
            if not have[k]:
                k += 1
                continue
            e = k
            while e + 1 < len(xy) and have[e + 1]:
                e += 1
            if e - k >= 2:
                for side in (-1, 1):
                    o = offset_xy(xy[k:e + 1], side * spacing / 2)[::2]
                    segs.append({"xy": o, "h": deck[k:e + 1][::2], "tn": np.zeros(len(o), bool),
                                 "year": y0v[k:e + 1][::2], "end": y1v[k:e + 1][::2], "L": cum[e] - cum[k], "div": "E"})
            k = e + 1
        # service lines: runs with one closing year
        k = 0
        while k < len(xy):
            if not have[k]:
                k += 1
                continue
            e = k
            while e + 1 < len(xy) and have[e + 1] and y1v[e + 1] == y1v[k]:
                e += 1
            if cum[e] - cum[k] > 250:
                lines.append({"via": via, "name": pr["name"], "xy": xy[k:e + 1], "h": deck[k:e + 1], "year": y0v[k:e + 1],
                              "end": float(y1v[k]), "half": spacing / 2, "color": pr.get("color", "6E6259")})
            k = e + 1
    out = []
    el_st = stations[stations.system.isin(["el", "subway"]) & (stations.closed != "") & (stations.lon != "")]
    sxy = to_utm(el_st.lon.astype(float).values, el_st.lat.astype(float).values) if len(el_st) else np.zeros((0, 2))
    for n, ln in enumerate(lines):
        spec = {"id": f"el{n}", "name": ln["name"], "system": "bart", "veh": "el", "cars": 5, "headway": 300,
                "color": ln["color"], "div": "E", "half": ln["half"], "h": EL_H, "gap": [round(ln["end"], 2), 9999.0]}
        d, _ = cKDTree(ln["xy"]).query(sxy) if len(sxy) else (np.zeros(0), None)
        stops = sxy[d < 45.0] if len(sxy) else []
        yv, hv = ln["year"], ln["h"]

        def years(xy, tn, src=ln["xy"], yv=yv):
            return yv[cKDTree(src).query(xy)[1]]

        ol, xy = build_line(spec, ln["xy"], [], (None, None, None, None, None), ground, years, list(stops), "el")
        # height from the deck profile (no Overture tracks under a line that is gone)
        hz = hv[cKDTree(ln["xy"]).query(xy)[1]]
        lon, lat = to_ll(xy)
        ol["z"] = np.round(ground(lon, lat) + hz, 1).tolist()
        out.append(ol)
        geo.append(xy)
    log(f"transit: {len(segs)} tracks of lines that are gone ({sum(s['L'] for s in segs) / 2000:.0f} km of route), {len(out)} service lines")
    return segs, out, geo


# ---------------------------------------------------------------- railroads
def city_poly():
    """The five boroughs' outline (the map before the counties): what lies outside it is "the counties"."""
    if CITY_RING.exists():
        return Polygon(json.loads(CITY_RING.read_text())["ring"]).buffer(0.004)
    lon0, lat0, lon1, lat1 = NYC_BBOX
    return Polygon([(lon0, lat0), (lon1, lat0), (lon1, lat1), (lon0, lat1)])


def railroad_tracks(r, ground, ohm, openings):
    """Standing railroad, PATH and light rail tracks inside the map. Dates, point by point along a track:
    (1) the first row of transit_openings.csv (system `rail`) that names the track's line (`line`: names
    separated by `|`, `*` = any) and whose box holds the point; (2) else OpenHistoricalMap's dated way at
    that place (at least half of the undated points within 20 m of one: its commonest day); (3) else -
    yards, sidings, lines nobody has dated - the nearest dated track within 400 m (estimated). Tracks
    with none of the three are left out. Each track carries `sys` (rail / path / hblr / nlr / lr) and each
    point `src` (1 row, 2 OpenHistoricalMap, 3 nearest)."""
    rr = r[r["class"].isin(["standard_gauge", "light_rail", "monorail", "narrow_gauge"]) | r["is_path"]].reset_index(drop=True)
    segs, conn, n = sample_tracks(rr, step=20.0)
    height_profile(segs, conn, n, ground)
    lon, lat = to_ll(np.concatenate([s["xy"] for s in segs]))
    city = city_poly()
    shapely.prepare(city)
    county = ~shapely.contains_xy(city, lon, lat)
    rules = []
    for o in openings[openings.system == "rail"].itertuples():
        box = None
        if o.from_stop and o.to_stop:
            (x0, y0), (x1, y1) = (map(float, v.split()) for v in (o.from_stop, o.to_stop))
            box = (x0, y0, x1, y1)
        rules.append((None if o.line == "*" else set(o.line.split("|")), box, decyear(o.opened), o.route_id))
    otree, oy = ohm
    k0 = 0
    for s in segs:
        k = len(s["xy"])
        s["lon"], s["lat"], s["county"] = lon[k0:k0 + k], lat[k0:k0 + k], county[k0:k0 + k]
        k0 += k
        nj = s["lon"][k // 2] < -74.02
        lr = s["cls"] == "light_rail" and nj
        s["sys"] = "path" if s["path"] else ("hblr" if "Hudson" in s["name"] else "nlr" if "Newark" in s["name"] else "lr") if lr else "rail"
        name = s["name"] or ("PATH" if s["path"] else "")
        y, src, rid = np.full(k, np.nan), np.zeros(k, np.uint8), np.full(k, -1)
        for q, (names, box, yr, _) in enumerate(rules):
            if names is not None and name not in names:
                continue
            m = np.isnan(y)
            if box:
                m &= (s["lon"] >= box[0]) & (s["lon"] <= box[2]) & (s["lat"] >= box[1]) & (s["lat"] <= box[3])
            y[m], src[m], rid[m] = yr, 1, q
        miss = np.isnan(y)
        if miss.any():
            dd, ii = otree.query(s["xy"][miss], distance_upper_bound=20.0)
            o = np.where(np.isfinite(dd), oy[np.minimum(ii, len(oy) - 1)], np.nan)
            if np.isfinite(o).mean() >= 0.5:
                y[miss] = Counter(np.round(o[np.isfinite(o)], 3)).most_common(1)[0][0]
                src[miss] = 2
        s["year"], s["src"], s["rule"] = y, src, rid
        s["end"] = np.full(k, 9999.0)
    have = np.concatenate([~np.isnan(s["year"]) for s in segs])
    if have.any():
        t = cKDTree(np.concatenate([s["xy"] for s in segs])[have])
        ty = np.concatenate([s["year"] for s in segs])[have]
        for s in segs:
            miss = np.isnan(s["year"])
            if miss.any():
                dd, ii = t.query(s["xy"][miss], distance_upper_bound=400.0)
                ok = np.isfinite(dd)
                at = np.nonzero(miss)[0][ok]
                s["year"][at] = ty[ii[ok]]
                s["src"][at] = 3
    keep = [s for s in segs if not np.isnan(s["year"]).any()]
    km = defaultdict(float)
    for s in segs:
        w = s["L"] / len(s["xy"]) / 1000
        for c in (False, True):
            for v in (0, 1, 2, 3):
                km[(c, v)] += w * float(((s["county"] == c) & (s["src"] == v)).sum())
    for c in (False, True):
        log(f"transit: railroad / PATH / light rail track {'in the counties' if c else 'in the city'}: {km[(c, 1)]:.0f} km dated by a row of "
            f"transit_openings.csv, {km[(c, 2)]:.0f} km by OpenHistoricalMap, {km[(c, 3)]:.0f} km from the nearest dated track, "
            f"{km[(c, 0)]:.0f} km undated (left out with their track)")
    county_report(segs, rules, ohm)
    return keep


def county_report(segs, rules, ohm):
    """data/interim/transit/: how the counties' track was dated, line by line; the rows against
    OpenHistoricalMap's dates; track that opens before its ground (made land; reported, not changed)."""
    out = INTERIM / "transit"
    out.mkdir(parents=True, exist_ok=True)
    rows, chk, gr = defaultdict(lambda: np.zeros(4)), defaultdict(list), defaultdict(lambda: np.zeros(2))
    otree, oy = ohm
    try:
        from ground_rule import land_year_at
    except Exception as e:  # noqa: BLE001
        land_year_at = None
        log(f"transit: ground_rule not available ({e})")
    for s in segs:
        c = s["county"]
        if not c.any():
            continue
        w = s["L"] / len(s["xy"]) / 1000
        for v in range(4):
            rows[(s["sys"], s["name"])][v] += w * float((c & (s["src"] == v)).sum())
        m = c & (s["src"] == 1)
        if m.any():
            dd, ii = otree.query(s["xy"][m], distance_upper_bound=20.0)
            ok = np.isfinite(dd)
            for q, d in zip(s["rule"][m][ok], s["year"][m][ok] - oy[ii[ok]]):
                chk[rules[q][3]].append(d)
        if land_year_at is not None:
            ly = land_year_at(s["lon"], s["lat"])
            bad = c & np.isfinite(ly) & np.isfinite(s["year"]) & (s["year"] < ly)
            gr[(s["sys"], s["name"])] += [w * float(bad.sum()), w * float((c & np.isfinite(ly)).sum())]
    t = pd.DataFrame([{"system": k[0], "line": k[1], "km_row": v[1], "km_ohm": v[2], "km_nearest": v[3], "km_undated": v[0]} for k, v in rows.items()])
    t.round(2).sort_values("km_nearest", ascending=False).to_csv(out / "county_rail_dating.csv", index=False)
    c = pd.DataFrame([{"route_id": k, "samples": len(v), "median_row_minus_ohm": float(np.median(v)), "share_within_1y": float((np.abs(v) <= 1).mean()),
                       "max_abs": float(np.abs(v).max())} for k, v in chk.items()])
    c.round(3).to_csv(out / "county_rail_ohm_check.csv", index=False)
    g = pd.DataFrame([{"system": k[0], "line": k[1], "km_before_ground": v[0], "km_on_made_land": v[1]} for k, v in gr.items() if v[1] > 0])
    if len(g):
        g.round(2).sort_values("km_before_ground", ascending=False).to_csv(out / "county_rail_ground.csv", index=False)
        log(f"transit: counties: {g.km_before_ground.sum():.1f} km of track open before its ground of {g.km_on_made_land.sum():.1f} km on made land "
            f"(data/interim/transit/county_rail_ground.csv; causeways across the marsh are real - reported, not changed)")
    else:
        log("transit: counties: no track on made land found (is data/interim/grid_region_landyear.npy built?)")


# ---------------------------------------------------------------- rapid transit of the counties
def relation_line(rel):
    """An OpenStreetMap route relation (out body geom) -> its ways joined in order (lon/lat), the largest
    gap between two consecutive ways (m), the stop positions."""
    ways = [np.array([(q["lon"], q["lat"]) for q in m["geometry"]]) for m in rel["members"]
            if m["type"] == "way" and m.get("role", "") in ("", "forward", "backward") and m.get("geometry")]
    k = np.array([84400.0, 111320.0])

    def d(p, q):
        return float(np.hypot(*((p - q) * k)))

    line = ways[0]
    if len(ways) > 1 and min(d(line[0], ways[1][0]), d(line[0], ways[1][-1])) < min(d(line[-1], ways[1][0]), d(line[-1], ways[1][-1])):
        line = line[::-1]
    gap = 0.0
    for w in ways[1:]:
        if d(line[-1], w[-1]) < d(line[-1], w[0]):
            w = w[::-1]
        g = d(line[-1], w[0])
        gap = max(gap, g)
        line = np.vstack([line, w[1:] if g < 0.5 else w])
    stops = np.array([(m["lon"], m["lat"]) for m in rel["members"] if m["type"] == "node" and m.get("role", "").startswith("stop") and "lon" in m])
    return line, gap, stops


def rapid_lines(rr, ground):
    """Service lines of PATH, the Hudson-Bergen Light Rail and the Newark Light Rail (RAPID) on
    OpenStreetMap's route relations; heights, tunnels and opening years from the dated tracks."""
    if not RAPID_ROUTES.exists():
        log("transit: no OpenStreetMap route relations (tools/fetch_region.py routes): the counties get tracks and stations only")
        return [], [], []
    rels = {e["id"]: e for e in json.load(open(RAPID_ROUTES))["elements"] if e["type"] == "relation"}
    trips = {}
    if (PATH_GTFS / "trips.txt").exists():
        t = pd.read_csv(PATH_GTFS / "trips.txt", dtype=str)
        cal = pd.read_csv(PATH_GTFS / "calendar.txt", dtype=str)
        wk = set(cal[(cal.monday == "1") & (cal.friday == "1")].service_id)
        trips = t[t.service_id.isin(wk) & (t.direction_id == "0")].groupby("route_id").size().to_dict()
    out, geo, grp = [], [], []
    for lid, name, system, veh, cars, headway, color, tset, (ra, rb), route in RAPID:
        segs = [s for s in rr if (s["sys"] == "path") == (tset == "path") and s["sys"] != "rail"]
        if ra not in rels or rb not in rels or not segs:
            log(f"transit: line {lid}: relation or tracks missing - no trains")
            continue
        (la, gap_a, stops), (lb, gap_b, _) = relation_line(rels[ra]), relation_line(rels[rb])
        A = densify_xy(to_utm(la[:, 0], la[:, 1]), 10.0)
        B = densify_xy(to_utm(lb[:, 0], lb[:, 1]), 5.0)
        la_m, lb_m = (float(np.hypot(*np.diff(x, axis=0).T).sum()) for x in (A, B))
        if max(gap_a, gap_b) > 60 or abs(la_m - lb_m) > 0.15 * la_m:
            log(f"transit: line {lid}: the route relations do not join up (gaps {gap_a:.0f} / {gap_b:.0f} m, {la_m / 1000:.1f} / {lb_m / 1000:.1f} km) - no trains")
            continue
        dd, ii = cKDTree(B).query(A, distance_upper_bound=15.0)
        off = np.where(np.isfinite(dd)[:, None], (B[np.minimum(ii, len(B) - 1)] - A) / 2, 0.0)
        off = pd.DataFrame(off).rolling(7, center=True, min_periods=1).mean().values
        xy = A + off
        tr = (np.concatenate([s["xy"] for s in segs]), np.concatenate([s["h"] for s in segs]), np.concatenate([s["tn"] for s in segs]),
              np.concatenate([np.full(len(s["xy"]), q) for q, s in enumerate(segs)]))
        tr = (*tr, cKDTree(tr[0]))
        ty = np.concatenate([s["year"] for s in segs])
        if headway is None:
            headway = int(round(20 * 3600 / max(trips.get(route, 120), 1) / 30) * 30)
        spec = {"id": lid, "name": name, "system": system, "veh": veh, "cars": cars, "headway": headway, "color": color, "div": ""}

        def years(pts, tn, tree=tr[4], ty=ty):
            return median_filter(ty[tree.query(pts)[1]], size=13, mode="nearest")

        sxy = to_utm(stops[:, 0], stops[:, 1]) if len(stops) else np.zeros((0, 2))
        ol, lxy = build_line(spec, xy, segs, tr, ground, years, list(sxy), veh)
        out.append(ol)
        geo.append(lxy)
        grp.append(tset)
    return out, geo, grp


def former_railroads(ground):
    """Railroads that are gone (former_railroads.geojson: OpenHistoricalMap ways with an end date)."""
    f = MANUAL / "transit" / "former_railroads.geojson"
    if not f.exists():
        return []
    segs = []
    for ft in json.load(open(f))["features"]:
        pr = ft["properties"]
        xy = densify_xy(to_utm(*np.array(shape(ft["geometry"]).coords)[:, :2].T), 20.0)
        if len(xy) < 2:
            continue
        st = pr.get("structure", "ground")
        h = np.full(len(xy), EL_H if st == "elevated" else GROUND_H)
        if st == "elevated" and len(xy) > 3:  # ramps at both ends
            cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(xy, axis=0).T))])
            if not pr.get("joins_elevated"):
                h = np.minimum(h, GROUND_H + SLOPE * np.minimum(cum, cum[-1] - cum) + 4.2)
        segs.append({"xy": xy, "h": h, "tn": np.full(len(xy), st == "tunnel"), "year": np.full(len(xy), decyear(pr["start"])),
                     "end": np.full(len(xy), decyear(pr["end"])), "L": 0.0, "div": "R", "kind": pr.get("kind", "rail")})
    log(f"transit: {len(segs)} pieces of railroad and subway that are gone")
    return segs


# ---------------------------------------------------------------- stations
def station_rows(stations, out_lines, geo, ground, poly, groups, track_year):
    """`groups`: 'subway' / 'el' / 'path' / 'lr' per line - a station stands on a line of its own system.
    `track_year(lon, lat)`: opening year of the railroad track at a place, for stations without a date."""
    lv_xy = np.concatenate(geo)
    lv_li = np.concatenate([np.full(len(g), i) for i, g in enumerate(geo)])
    lv_k = np.concatenate([np.arange(len(g)) for g in geo])
    live = np.array([ol.get("gap") is None for ol in out_lines])
    lv_grp = np.array(groups)[lv_li]

    def tree_of(mask):
        idx = np.nonzero(mask)[0]
        return (cKDTree(lv_xy[idx]), idx) if len(idx) else None

    trees = {"subway": tree_of(live[lv_li] & (lv_grp == "subway")), "gone": tree_of(~live[lv_li]), "path": tree_of(lv_grp == "path")}
    n_line_year = 0
    names = pd.read_csv(TABLES / "transit_station_names.csv", dtype=str, keep_default_na=False)
    out = []
    for r in stations.itertuples():
        if not r.lon:
            continue
        lon, lat = float(r.lon), float(r.lat)
        if not poly.contains(Point(lon, lat)):
            continue
        if r.opened:
            start = decyear(r.opened)
        else:  # no opening date found: the opening year of the track it stands on (estimated; see the row's note)
            start = track_year(lon, lat)
            if not np.isfinite(start):
                continue
            n_line_year += 1
        p = to_utm([lon], [lat])[0]
        heavy = r.system in ("subway", "sir", "el", "path")
        reach = 200 if r.system == "path" else 45  # PATH's station points are entrances and halls, far from the track
        d, li, k = np.inf, 0, 0
        if heavy:
            # a closed station sits on a line that is gone when one passes; else on today's line
            for key in (("path",) if r.system == "path" else ("gone",) if r.system == "el" else ("gone", "subway") if r.closed else ("subway", "gone")):
                t = trees[key]
                if t is None:
                    continue
                dd, j = t[0].query(p)
                if dd < reach:
                    j = t[1][j]
                    d, li, k = dd, int(lv_li[j]), int(lv_k[j])
                    break
        ol = out_lines[li]
        gz = float(ground([lon], [lat])[0])
        st = (r.structure or "").strip()
        kind = STRUCT_KIND.get(st) or ("elevated" if "levated" in st else "underground" if "nderground" in st else
                                       "surface" if st else "elevated" if r.system == "el" else "surface")
        if d < reach:
            a, b = geo[li][max(0, k - 2)], geo[li][min(len(geo[li]) - 1, k + 2)]
            heading = math.degrees(math.atan2(b[0] - a[0], b[1] - a[1]))
            ll = to_ll(geo[li][k:k + 1])
            lon, lat = float(ll[0][0]), float(ll[1][0])
            zt = float(ol["z"][k])
            if ol["tunnel"][k]:
                kind = "underground"
            elif zt - gz > 4:
                kind = "elevated"
            elif kind == "elevated":
                kind = "surface"
        else:
            heading, zt = 0.0, gz + (EL_H if kind == "elevated" else GROUND_H)
            if heavy:
                kind = "underground" if kind != "elevated" or not r.closed else kind
        if heavy and d >= reach and kind != "underground":
            kind = "underground"  # no line to stand on: label only (the viewer draws platforms on a line)
        end = decyear(r.closed) if r.closed else 9999.0
        if end <= start:
            continue
        s = {"code": r.code, "name": r.name, "system": "bart" if heavy else "muni", "lon": round(lon, 6), "lat": round(lat, 6),
             "z": round(zt, 1), "ground": round(gz, 1), "heading": round(heading, 1), "kind": kind, "start": start, "end": end,
             "line": ol["id"], "veh": "bart" if ol["veh"] == "bart" else "ebart"}
        if heavy:  # typical platform length of its division (m), for a viewer that reads it
            # (PATH: eight 51 ft cars, about 125 m - estimated)
            s["platform"] = 61 if r.system == "el" else 91 if r.system == "sir" else 125 if r.system == "path" else 160 if r.line.startswith("IRT") else 183
        old = names[(names.system == r.system) & (names.code == r.code)].sort_values("until")
        if len(old):
            per = [{"name": o["name"], "start": round(max(start, decyear(o["from"])), 2), "end": round(decyear(o["until"]), 2)}
                   for _, o in old.iterrows()]
            per.append({"name": r.name, "start": per[-1]["end"], "end": end})
            s["names"] = per
        out.append(s)
    if n_line_year:
        log(f"transit: {n_line_year} stations without an opening date took the year of their track (estimated)")
    return out


# ---------------------------------------------------------------- main
def main():
    g, ohm_files = downloads()
    ground = Ground()
    poly = extent_poly()
    openings = pd.read_csv(TABLES / "transit_openings.csv", dtype=str, keep_default_na=False)
    stations = pd.read_csv(TABLES / "transit_stations.csv", dtype=str, keep_default_na=False)
    gt = load_gtfs(g)
    trees = dated_network(openings, gt, stations)
    ohm = ohm_dated(ohm_files)
    rail = read_rail(poly)

    segs = subway_tracks(rail, ground, trees, ohm)
    out_lines, geo = subway_lines(gt, segs, ground, trees)
    gone, gone_lines, gone_geo = manual_lines(openings, stations, ground)
    rr = railroad_tracks(rail, ground, ohm, openings)
    rapid, rapid_geo, rapid_grp = rapid_lines(rr, ground)
    old_rr = former_railroads(ground)

    items = (path_items(segs, ground, K_BART, 3.0, poly) + path_items(gone, ground, K_BART, 3.0, poly)
             + path_items([x for x in rr if x["sys"] == "rail"], ground, K_RAIL, 3.0, poly)
             + path_items([x for x in rr if x["sys"] == "path"], ground, K_BART, 3.0, poly)
             + path_items([x for x in rr if x["sys"] in ("hblr", "nlr", "lr")], ground, K_LIGHTRAIL, 3.0, poly)
             + path_items([x for x in old_rr if x["kind"] == "rail"], ground, K_RAIL, 3.0, poly)
             + path_items([x for x in old_rr if x["kind"] != "rail"], ground, K_BART, 3.0, poly))
    write_paths3d(VIEWER_DATA / "transit.bin.gz", items)
    all_lines = out_lines + gone_lines + rapid
    meta = {"origin": list(ORIGIN), "vehicles": VEHICLES, "lines": all_lines}
    (VIEWER_DATA / "transit-lines.json").write_text(json.dumps(meta, separators=(",", ":")))
    rr_tree, rr_year = cKDTree(np.concatenate([x["xy"] for x in rr])), np.concatenate([x["year"] for x in rr])

    def track_year(lon, lat):
        dd, ii = rr_tree.query(to_utm([lon], [lat])[0], distance_upper_bound=250.0)
        return float(rr_year[ii]) if np.isfinite(dd) else float("nan")

    st = station_rows(stations, all_lines, geo + gone_geo + rapid_geo, ground, poly,
                      ["subway"] * len(out_lines) + ["el"] * len(gone_lines) + rapid_grp, track_year)
    (VIEWER_DATA / "transit-stations.json").write_text(json.dumps(st, separators=(",", ":")))

    # ---- report
    km = defaultdict(float)
    for lon, lat, z, kind, width, y0, y1, el in items:
        d = float(np.hypot(np.diff(lon) * 84400, np.diff(lat) * 111320).sum()) / 1000
        km[({K_BART: "subway/el/PATH", K_LIGHTRAIL: "light rail"}.get(kind, "railroad"), {0: "ground", 2: "aerial", 4: "tunnel"}[el],
            "standing" if y1 > 9000 else "gone")] += d
    for k_, v in sorted(km.items()):
        log(f"transit: {' / '.join(k_)}: {v:.0f} km of track")
    kinds = Counter((s["system"], s["kind"]) for s in st)
    log(f"transit: {len(st)} stations {dict(kinds)}; {len(all_lines)} service lines ({len(out_lines)} subway / SIR, {len(gone_lines)} gone, "
        f"{len(rapid)} PATH / light rail), {sum(len(l['lon']) for l in all_lines)} line vertices")


if __name__ == "__main__":
    main()
