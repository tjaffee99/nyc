"""Stage: streets, roads and highways with lifespans, draped on the terrain (New York City
and the counties around it that are on the map: extent.map_counties).

  * Streets and roads — Overture / OpenStreetMap segments of the five boroughs and the map's
    counties (roads_region.parquet: tertiary and up; roads_local.parquet: residential streets,
    living streets, unclassified lanes, alleys). A street is cut a year before the
    second-earliest building within 45 m of it goes up (today's buildings and the vanished
    ones traced from the atlases: nyc_building_points.parquet; the counties' buildings:
    county_building_points.parquet), never before its ground (land-year grids: the fine grid
    over the city box, the region grid beyond it). In the counties houses stand back from the
    road: a street without a building within 45 m takes the buildings within 90 m
    (COUNTY_RADIUS). Without buildings along it: the year of the nearest building-dated
    street (<= 300 m), else a default (1900 local streets, 1870 main roads) — both
    `estimated`, both counted.
    Researched streets: data/tables/street_dates.csv (a street cut through older blocks: not
    before its year; a road older than its buildings, or a parkway without any: rule = set).
  * Routes — data/manual/routes.csv (researched, every row with its source): the highways and
    parkways section by section, ferries, vanished roads. A standing highway only DATES
    Overture's geometry (the motorway / trunk segments running along the row's line take its
    year); what is gone or is not a road (the elevated West Side Highway, ferries, colonial
    roads) is drawn from the row's line.
  * Motorways, trunks and ramps in 3D (freeway_items): viaduct decks from Overture's level /
    bridge / tunnel flags, ramps coming down to the streets they join.
  * The decks of the bridges modelled as landmarks (data/tables/landmarks_bridges.csv: road
    names and segment ids in each model's notes) are left out of every file; where a model
    ends high above the terrain grid the generic highway takes over at its deck height
    (BRIDGE_END_PINS). Other road bridges over water or across a valley get a plain deck.
  Elevated railways, subways, railroads and streetcars are transit.py's, not drawn here.

Outputs (BAYT; the file names are the viewer's, kept from the Bay Area map):
  roads-sf.bin.gz       every street of Manhattan (always loaded)
  roads-region.bin.gz   main roads (always loaded): tertiary and up in the Bronx, Brooklyn, Queens
                        and Staten Island; primary and secondary roads in the counties
  region-streets/       residential streets of those boroughs and the counties, and the counties'
                        tertiary roads: z12 tiles + simplified z10 tiles + index.json
  freeways.bin.gz       motorways, trunks and ramps (3D)
  routes.bin.gz         researched routes that are gone or are not roads
    start_indices u32 (path vertex starts), positions f32[3] (lon/lat offsets from ORIGIN,
    z metres), kind u8, width u8 (m), years f32[2], elevated u8
  data/interim/roads/report.json           counts, dating shares, highway segments left on the default
  data/interim/roads/street_years.parquet  every street segment: name, borough / county, year, how it was dated
  data/interim/roads/highway_years.csv     every motorway / trunk mainline segment likewise
  data/interim/roads/bridge_model_ends.csv where the landmark bridge decks end: ground, generic deck, pin
  data/interim/roads/ground_conflicts.csv  researched roads on ground the land-year grid dates later

The researched tables are written by the scripts in data/manual/roads_tools/ (README:
data/manual/routes_README.md).

Usage:  ../.venv/bin/python roads.py          everything (about 2 minutes, under 3 GB)
        ../.venv/bin/python roads.py check    invariants of the built files
"""
from __future__ import annotations

import json
import math
import re
import shutil
import sys
import time

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import LineString, MultiLineString
from shapely.ops import linemerge, substring

from common import (CURRENT_YEAR, INTERIM, MANUAL, NYC_BBOX, NYC_CRS, RAW, REGION_BBOX, TABLES, VIEWER_DATA, YEAR_MIN,
                    log)
from download_overture import RELEASE
from export_columnar import read_bayt, write_columnar
from extent import in_extent, map_counties
from terrain_grid import grid_def

ORIGIN = (-73.97, 40.74)
UTM = NYC_CRS
_TO_LL = Transformer.from_crs(UTM, 4326, always_xy=True)
_TO_UTM = Transformer.from_crs(4326, UTM, always_xy=True)

# kinds (keep in sync with viewer/src/layers/roads.ts; 4-8 and 10 are the Bay map's cable cars,
# streetcars, railways, Key System, BART and light rail: unused here, the numbers stay)
K_STREET, K_MAJOR, K_FREEWAY, K_HIGHWAY, K_CABLE, K_STREETCAR, K_RAIL, K_KEY, K_BART, K_FERRY, K_LIGHTRAIL = range(11)
MODE_KIND = {"freeway": K_FREEWAY, "highway": K_HIGHWAY, "bridge": K_HIGHWAY, "ferry": K_FERRY,
             # a road that is gone (colonial roads erased by the street grid): drawn like a street
             "road": K_STREET}
# elevated railways, subways, railroads and streetcars are drawn by transit.py from the real
# tracks (transit.bin.gz): rows with these modes in routes.csv are never drawn here
TRANSIT_TAKES_OVER = True
TRANSIT_MODES = {"elevated", "subway", "railroad", "steam_railroad", "rail", "streetcar", "horsecar", "cable_car",
                 "interurban", "light_rail"}
# edge of the Overture extracts (download_overture.REGION_BBOX): highway ends there are cuts
REGION_BBOX_ROADS = REGION_BBOX
# routes drawn by a landmark model instead of a line (none so far)
LANDMARK_ROUTES: set[str] = set()
ELEV = {"ground": 0, "embankment": 1, "viaduct": 2, "bridge": 3, "tunnel": 4}
WIDTH = {K_STREET: 9, K_MAJOR: 14, K_FREEWAY: 24, K_HIGHWAY: 16, K_FERRY: 6}
ROAD_WIDTH = 7  # mode `road`: a colonial road
DEFAULT_LOCAL, DEFAULT_MAIN, DEFAULT_FREEWAY = 1900.0, 1870.0, 1960.0
BRIDGE_SAG = 0.03  # a motorway / trunk bridge deck falls at most 3 % below its abutments' level
COUNTY_BORO = {"061": "1", "005": "2", "047": "3", "081": "4", "085": "5"}
BORO_NAME = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"}
# the counties around the city: houses stand back from the road, so a street without a
# building within 45 m is dated by the buildings within COUNTY_RADIUS
COUNTY_RADIUS = 90.0
# vertex spacing (m) of a draped road: the terrain is the ~29 m grid inside the city box and
# the ~58 m grid beyond it; outlines are simplified to 1 m in the city, 2.5 m in the counties
STEP_CITY, STEP_OUTER = 30.0, 60.0
SIMPLIFY_COUNTY = 2.5
# written coordinates are rounded to 2^-18 degree (0.42 m north-south, 0.32 m east-west) and
# heights to 0.25 m: float32 offsets then gzip to about 63 % of their unrounded size (the site
# has a size budget: CLAUDE.md, decision 20)
QUANT_XY, QUANT_Z = 2.0 ** -18, 0.25
# how a year was found (report)
SRC_BUILDINGS, SRC_NEIGHBOUR, SRC_DEFAULT, SRC_RESEARCHED, SRC_BUILDINGS_WIDE = 0, 1, 2, 3, 4
SRC_NAMES = (("buildings", SRC_BUILDINGS), ("buildings_90m", SRC_BUILDINGS_WIDE), ("neighbour", SRC_NEIGHBOUR),
             ("default", SRC_DEFAULT), ("researched", SRC_RESEARCHED))
SCRATCH = INTERIM / "roads"


def to_ll(x, y):
    return _TO_LL.transform(np.asarray(x, float), np.asarray(y, float))


# ---------------------------------------------------------------- ground
_LANDYEAR = None


def land_year(lon, lat):
    """Year the ground at each point became dry land (terrain land-year grids, read at run
    time: made-land zones are still being added), NaN where it always was land."""
    global _LANDYEAR
    if _LANDYEAR is None:
        _LANDYEAR = []
        for name in ("detail", "region"):
            p = INTERIM / f"grid_{name}_landyear.npy"
            if p.exists():
                _LANDYEAR.append((grid_def(name), np.load(p)))
    lon = np.asarray(lon, float)
    lat = np.asarray(lat, float)
    out = np.full(lon.shape, np.nan)
    done = np.zeros(lon.shape, bool)
    X = np.radians(lon) * 6378137.0
    Y = 6378137.0 * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
    # the fine grid where it covers the point (the city box), else the region grid (the
    # counties beyond it: the Meadowlands north of the box, the Hudson shore, the Sound)
    for g, ly in _LANDYEAR:
        c = np.rint((X - g["X0"]) / g["res"]).astype(int)
        r = np.rint((g["Y0"] - Y) / g["res"]).astype(int)
        ok = ~done & (c >= 0) & (r >= 0) & (c < g["cols"]) & (r < g["rows"])
        out[ok] = ly[r[ok], c[ok]]
        done |= ok
    return out


def boroughs():
    """Area code -> county polygon (TIGER 2024; includes each county's water): "1".."5" for
    the five boroughs, the five-digit FIPS code ("34017" Hudson ...) for the counties on the
    map (extent.map_counties). The counties are outside the boroughs: everything keyed on a
    borough (the researched street rows without a county, the Manhattan file) skips them."""
    co = gpd.read_file(f"zip://{RAW / 'tiger' / 'tl_2024_us_county.zip'}", where="STATEFP IN ('36', '34')")
    fips = (co.STATEFP + co.COUNTYFP).values
    out = {}
    co = co.to_crs(4326)
    for f, c, st, g in zip(fips, co.COUNTYFP, co.STATEFP, co.geometry):
        if st == "36" and c in COUNTY_BORO:
            out[COUNTY_BORO[c]] = g
        elif f in AREA_NAME:
            out[f] = g
    return out


AREA_NAME = {**BORO_NAME, **map_counties()}


def boro_of(points, boros):
    """area code of each point ("" outside the boroughs and the map's counties)"""
    out = np.full(len(points), "", dtype=object)
    for code, poly in boros.items():
        shapely.prepare(poly)
        out[shapely.contains(poly, points)] = code
    return out


def in_city_box(lon, lat):
    """inside the box of the fine terrain grid (common.NYC_BBOX)"""
    return (lon > NYC_BBOX[0]) & (lon < NYC_BBOX[2]) & (lat > NYC_BBOX[1]) & (lat < NYC_BBOX[3])


# ---------------------------------------------------------------- dating
def building_tree():
    """Every building of the city, standing or vanished (nyc_building_points.parquet), and of
    the counties (county_building_points.parquet, same columns): a KD-tree of the centroids
    (UTM) and their start years. The files are rewritten by the buildings stages: a failed
    read is retried."""
    parts = []
    for name in ("nyc_building_points.parquet", "county_building_points.parquet"):
        p = INTERIM / name
        if not p.exists():
            log(f"roads: no {name}: its streets go undated")
            continue
        b = None
        for attempt in range(30):
            try:
                b = pd.read_parquet(p, columns=["lon", "lat", "start_year"])
                break
            except Exception as e:  # noqa: BLE001
                log(f"roads: {p.name} not readable ({type(e).__name__}); retry in 30 s")
                time.sleep(30)
        if b is None:
            raise RuntimeError(f"{p} could not be read")
        b = b[np.isfinite(b.start_year.values) & (b.start_year.values >= YEAR_MIN)]
        log(f"roads: {len(b)} buildings of {name} date the streets")
        parts.append(b)
    b = pd.concat(parts, ignore_index=True)
    x, y = _TO_UTM.transform(b.lon.values, b.lat.values)
    xy = np.column_stack([x, y]).astype(np.float64)
    return cKDTree(xy), b.start_year.values.astype(np.float32)


def _second_earliest(seg, px, py, bld, radius, n, chunk=30_000):
    """Year of the 2nd-earliest building within `radius` of each line (the earliest where
    there is only one; NaN without any). seg: line index of each sample point, ascending.
    Worked through in chunks of lines: the pair table of the whole region is large."""
    tree, byear = bld
    year = np.full(n, np.nan)
    for a in range(0, n, chunk):
        lo, hi = np.searchsorted(seg, [a, min(a + chunk, n)])
        if hi <= lo:
            continue
        d, idx = tree.query(np.column_stack([px[lo:hi], py[lo:hi]]), k=8, distance_upper_bound=radius, workers=2)
        ok = np.isfinite(d)
        pairs = pd.DataFrame({"s": np.broadcast_to(seg[lo:hi, None], d.shape)[ok], "b": idx[ok]}).drop_duplicates()
        pairs["y"] = byear[pairs.b.values]
        pairs = pairs.sort_values(["s", "y"])
        pairs["r"] = pairs.groupby("s").cumcount()
        first = pairs[pairs.r == 0]
        second = pairs[pairs.r == 1]
        year[first.s.values] = first.y.values
        year[second.s.values] = second.y.values
    return year


def date_lines(lines, default, bld, neighbours=None, wide=None):
    """A street is cut a year before the 2nd-earliest building within 45 m of it goes up
    (today's footprints and the vanished ones); with one building, a year before it. `wide`
    (mask: the lines in the counties, where houses stand back from the road): without a
    building within 45 m, the same rule on the buildings within COUNTY_RADIUS. Without any,
    the year of the nearest building-dated street within 300 m (`neighbours` = (tree of
    their middles, years); by default the building-dated lines of this call), else `default`
    (scalar or array). Returns (year, source code per line, land year of the ground under it
    — NaN where it always was land —, the (tree, years) of the building-dated lines).
    The ground rule is applied by the caller, after the researched overrides."""
    lines = np.asarray(lines, dtype=object)
    n = len(lines)
    L = shapely.length(lines)
    m = np.maximum(2, (L // 20).astype(int) + 1)
    seg = np.repeat(np.arange(n), m)
    k = np.arange(len(seg)) - np.repeat(np.cumsum(m) - m, m)
    pts = shapely.line_interpolate_point(lines[seg], k / np.repeat(m - 1, m), normalized=True)
    px, py = shapely.get_x(pts), shapely.get_y(pts)
    del pts
    year = _second_earliest(seg, px, py, bld, 45.0, n) - 1.0
    src = np.where(np.isfinite(year), SRC_BUILDINGS, SRC_DEFAULT)
    if wide is not None:
        todo = np.asarray(wide, bool) & ~np.isfinite(year)
        if todo.any():
            sel = todo[seg]
            y2 = _second_earliest(seg[sel], px[sel], py[sel], bld, COUNTY_RADIUS, n) - 1.0
            got = todo & np.isfinite(y2)
            year[got] = y2[got]
            src[got] = SRC_BUILDINGS_WIDE
    mid = shapely.line_interpolate_point(lines, 0.5, normalized=True)
    mxy = np.column_stack([shapely.get_x(mid), shapely.get_y(mid)])
    dated = np.isfinite(year)
    own = (cKDTree(mxy[dated]), year[dated]) if dated.any() else None
    nb = neighbours or own
    if nb is not None and (~dated).any():
        dd, ii = nb[0].query(mxy[~dated], distance_upper_bound=300)
        hit = np.isfinite(dd)
        w = np.nonzero(~dated)[0][hit]
        year[w] = nb[1][ii[hit]]
        src[w] = SRC_NEIGHBOUR
    year = np.where(np.isfinite(year), year, default)
    # the ground under it: the land year that at least half of the line lies on or after (the
    # ~38 m land-year grid is coarse for a street: cells of later fill beside it, or a creek or
    # marsh it crosses on its own causeway, do not hold a whole street back)
    lon, lat = to_ll(px, py)
    ly = pd.Series(np.nan_to_num(land_year(lon, lat), nan=-np.inf)).groupby(seg).quantile(0.5, interpolation="lower")
    ly = ly.reindex(np.arange(n)).values
    return year, src, np.where(np.isfinite(ly), ly, np.nan), own


GROUND_CONFLICTS = []  # researched roads on ground the land-year grid dates later (for the made-land stage)


def after_ground(year, ly, fixed=None, label=None):
    """Nothing estimated is drawn before its ground; years stay inside the slider. A researched
    opening (`fixed`) stands — a documented road is better evidence than the ~38 m land-year
    grid, which misses a causeway through a marsh — and the disagreement is recorded
    (label = (kind, names, lon, lat, metres)) in data/interim/roads/ground_conflicts.csv."""
    year = np.asarray(year, float)
    later = np.isfinite(ly) & (ly + 0.5 > year)
    if fixed is None:
        fixed = np.zeros(len(year), bool)
    if label is not None:
        kind, names, lon, lat, m = label
        for i in np.nonzero(later & fixed & (ly > year + 1.0))[0]:
            GROUND_CONFLICTS.append({"kind": kind, "name": names[i], "year": round(float(year[i]), 2), "land_year": round(float(ly[i]), 1),
                                     "lon": round(float(lon[i]), 5), "lat": round(float(lat[i]), 5), "m": round(float(m[i]), 1)})
    year = np.where(later & ~fixed, ly + 0.5, year)
    return np.clip(year, float(YEAR_MIN), CURRENT_YEAR + 1.0)


def street_overrides(names, boro, lon, lat, year, src, quiet=False):
    """data/tables/street_dates.csv (researched): `street` is the Overture name upper-cased
    ("re:<regex>" = every name the expression matches: the numbered streets of the 1811 grid);
    `boro` = the boroughs (1-5) and / or counties (five-digit FIPS: 36119 Westchester ...)
    a row is about, separated by spaces — blank = the five boroughs, never the counties (a
    Broadway or a Kings Highway there is another road); `bbox` ("lon0 lat0 lon1 lat1": the
    stretch concerned, by the segment's middle) narrows a row. rule blank = not before that year (a street cut through
    older blocks); `set` = the researched year replaces the estimate (a road older than the
    buildings along it, a parkway or park drive without any). Later rows win.
    Returns (year, source, mask of the segments whose year a `set` row fixed)."""
    sd = TABLES / "street_dates.csv"
    fixed = np.zeros(len(year), bool)
    if not sd.exists():
        return year, src, fixed
    t = pd.read_csv(sd, dtype=str).fillna("")
    hit = np.zeros(len(year), bool)
    city = np.isin(boro, list(BORO_NAME))
    for r in t.itertuples():
        key = str(r.street).strip()
        if key.startswith("re:"):
            rx = re.compile(key[3:])
            m = np.array([bool(rx.search(n_)) for n_ in names])
        else:
            m = names == key.upper()
        b = str(getattr(r, "boro", "")).strip()
        m &= np.isin(boro, b.split()) if b else city
        box = str(getattr(r, "bbox", "")).split()
        if len(box) == 4:
            x0, y0, x1, y1 = map(float, box)
            m &= (lon >= x0) & (lon <= x1) & (lat >= y0) & (lat <= y1)
        if not m.any():
            if not quiet:
                log(f"roads: street_dates.csv: no segment matches {r.street!r} (boro {b or 'any'})")
            continue
        y = float(r.year_start)
        if str(getattr(r, "rule", "")).strip().lower() == "set":
            year = np.where(m, y, year)
            src = np.where(m, SRC_RESEARCHED, src)
            hit |= m
            fixed |= m
        else:
            later = m & (year < y)
            year = np.where(later, y, year)
            src = np.where(later, SRC_RESEARCHED, src)
            hit |= later
            fixed &= ~later
    return year, src, fixed


# ---------------------------------------------------------------- Overture flags, bridges
def _flag_ranges(rules, key=None):
    """Overture road_flags / level_rules -> list of (lo, hi, value)."""
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


# Overture road names of the bridges modelled as landmarks, used when the landmark table does
# not list them (data/tables/landmarks_bridges.csv, notes column)
LANDMARK_BRIDGE_NAMES = [
    "Brooklyn Bridge", "Manhattan Bridge", "Manhattan Bridge Upper Roadway", "Manhattan Bridge Lower Roadway",
    "Williamsburg Bridge", "Ed Koch Queensboro Bridge", "Ed Koch Queensboro Bridge Upper Level",
    "Ed Koch Queensboro Bridge Lower Level", "Ed Koch Queensboro Bridge Lower Roadway",
    "George Washington Bridge", "George Washington Bridge Upper Level", "George Washington Bridge Lower Level",
    "Verrazzano-Narrows Bridge", "Robert F. Kennedy Bridge", "Throgs Neck Bridge", "Bronx-Whitestone Bridge",
    "Bayonne Bridge", "Goethals Bridge", "Outerbridge Crossing",
]


class LandmarkBridges:
    """The bridges drawn by landmark models (viewer/src/landmarks/nyc-bridges.ts): their decks
    are left out of every road file, for the whole life of today's geometry.
    data/tables/landmarks_bridges.csv says which roads they are, at the end of each model's
    notes ("Overture names.primary: ..."): quoted road names, and segment ids (first 8
    characters) where a bridge shares its name with the rest of the road (Manhattan Bridge =
    'Canal Street', Broadway Bridge, Henry Hudson Bridge, Kosciuszko Bridge, the three
    Triborough spans). A clause saying "not modelled" lists ids whose generic deck is kept
    (the Williamsburg Bridge's connector to the BQE, the Queensboro upper-level ramps).
    Without the table: a built-in list of names, plus unnamed roadways and ramps inside a
    45 m corridor around the named decks."""

    def __init__(self):
        import re
        self.names = {n.upper() for n in LANDMARK_BRIDGE_NAMES}
        self.ids_in, self.ids_out = {}, set()
        self.table = False
        self.corridor = None
        p = TABLES / "landmarks_bridges.csv"
        if p.exists():
            t = pd.read_csv(p, dtype=str).fillna("")
            names, by_id = set(), set()
            for note, mlon, mlat in zip(t["notes"].values, pd.to_numeric(t.lon, errors="coerce"), pd.to_numeric(t.lat, errors="coerce")):
                centre = _TO_UTM.transform(mlon, mlat) if np.isfinite(mlon) and np.isfinite(mlat) else None
                k = note.find("Overture names.primary")
                if k < 0:
                    continue
                for clause in note[k:].split(";"):
                    keep = "not modelled" in clause or "generic deck" in clause
                    last = None
                    for m in re.finditer(r"(?<![A-Za-z])'([^']+)'|\b([0-9a-f]{8})\u2026", clause):
                        if m.group(1):
                            last = m.group(1).upper().strip()
                            names.add(last)
                        elif keep:
                            self.ids_out.add(m.group(2))
                        else:
                            self.ids_in.setdefault(m.group(2), []).append(centre)
                            if last:
                                by_id.add(last)
            names = {n for n in names - by_id if re.search(r"BRIDGE|CROSSING", n)}
            if names or self.ids_in:
                self.table = True
                self.names = names
        if not self.table:
            base = RAW / "overture" / RELEASE
            parts = []
            for f in ("roads_region", "roads_local"):
                g = gpd.read_parquet(base / f"{f}.parquet", columns=["name", "road_flags", "geometry"])
                parts.append(g[g.name.notna() & g.road_flags.notna()])
            g = pd.concat(parts, ignore_index=True)
            g = g[g.geometry.geom_type == "LineString"]
            sel = g[g.name.str.upper().str.strip().isin(self.names).values].to_crs(UTM)
            decks = []
            for geom, fl in zip(sel.geometry.values, sel.road_flags.values):
                for lo, hi, _ in _flag_ranges(fl, "is_bridge"):
                    if hi - lo > 1e-6:
                        part = substring(geom, lo, hi, normalized=True)
                        if part.geom_type == "LineString":
                            decks.append(part)
            if decks:
                self.corridor = shapely.union_all(shapely.buffer(np.array(decks, dtype=object), 45.0))
                shapely.prepare(self.corridor)
        log(f"roads: landmark bridges: {len(self.names)} road names, {len(self.ids_in)} segment ids, "
            f"{len(self.ids_out)} ids kept generic ({'landmarks_bridges.csv' if self.table else 'built-in list'})")

    ID_RADIUS = 1150.0  # a segment listed by id is long: only its bridge stretches near the model count

    def _by_id(self, sid, x, y):
        """None = the id is not listed; else a mask: listed to keep (False) or part of a model (True
        for the vertices within ID_RADIUS of the model's centre)"""
        s8 = str(sid)[:8]
        x, y = np.atleast_1d(x), np.atleast_1d(y)
        if s8 in self.ids_out:
            return np.zeros(len(x), bool)
        if s8 not in self.ids_in:
            return None
        out = np.zeros(len(x), bool)
        for c in self.ids_in[s8]:
            out |= np.ones(len(x), bool) if c is None else (np.hypot(x - c[0], y - c[1]) <= self.ID_RADIUS)
        return out

    def covers(self, name, link, part, sid=""):
        """a bridge stretch (UTM line) that belongs to a modelled bridge"""
        mid = part.interpolate(0.5, normalized=True)
        hit = self._by_id(sid, mid.x, mid.y)
        if hit is not None:
            return bool(hit[0])
        if name and name.upper().strip() in self.names:
            return True
        if self.corridor is None or (name and not link):
            return False
        return bool(shapely.contains(self.corridor, part.interpolate(0.5, normalized=True)))

    def vertex_mask(self, name, link, x, y, sid=""):
        """the same per vertex (UTM arrays)"""
        hit = self._by_id(sid, x, y)
        if hit is not None:
            return hit
        if name and name.upper().strip() in self.names:
            return np.ones(len(x), bool)
        if self.corridor is None or (name and not link):
            return np.zeros(len(x), bool)
        return shapely.contains(self.corridor, shapely.points(x, y))


# Deck height (m above sea level) of the landmark bridge models where they end above the
# terrain grid and a generic approach takes over (from the bridge modeller, viewer/src/
# landmarks/nyc-bridges.ts): (road name contains, test on the end's lon / lat, height).
BRIDGE_END_PINS = [
    ("GEORGE WASHINGTON BRIDGE UPPER", lambda lon, lat: lon > -73.95, 68.0),   # roadway over the New York anchorage
    ("VERRAZZANO", lambda lon, lat: lon > -74.04, 45.0),                        # Brooklyn end
    ("THROGS NECK BRIDGE", lambda lon, lat: lat < 40.80, 22.0),                 # Queens end
    ("ROBERT F. KENNEDY", lambda lon, lat: lat < 40.775, 20.0),                 # Triborough: Queens end
    ("ROBERT F. KENNEDY", lambda lon, lat: lat > 40.8005 and lon > -73.92, 16.0),   # Bronx end
    ("ROBERT F. KENNEDY", lambda lon, lat: lon < -73.9285, 18.6),               # Manhattan side of the lift span
    ("d6042242", lambda lon, lat: lat > 40.874, 50.0),                          # Henry Hudson Bridge, upper level
    ("b8d3d9ec", lambda lon, lat: lat > 40.874, 43.5),                          # Henry Hudson Bridge, lower level
    ("e2ac78e7", lambda lon, lat: True, 24.5),                                  # Kosciuszko Bridge (ends 23-26 m)
    ("8f4b1e93", lambda lon, lat: True, 24.5),
]


def bridge_end_height(name, sid, lon, lat):
    """the model's deck height at one of its ends (BRIDGE_END_PINS), or None"""
    for key, test, z in BRIDGE_END_PINS:
        if (key in name.upper() or sid.startswith(key)) and test(lon, lat):
            return z
    return None


def cut_roads(r, ru, lm):
    """Cut every road at its tunnels and bridges (Overture road_flags). Returns (whole: rows
    drawn as they are, pieces: [(row, UTM line, is_bridge)]). Tunnels are left out
    (underground: nothing to see), and so are the decks of the landmark bridges and roads
    under construction."""
    n = len(r)
    whole = np.ones(n, bool)
    pieces = []
    flags = r.road_flags.values
    names = r.name_u.values
    ids = r["id"].values
    geoms = ru.geometry.values
    n_tunnel = n_landmark = 0
    for i in np.nonzero(r.road_flags.notna().values)[0]:
        fl = flags[i]
        if _flag_ranges(fl, "is_under_construction") or _flag_ranges(fl, "is_abandoned"):
            whole[i] = False
            continue
        tn = _flag_ranges(fl, "is_tunnel")
        br = _flag_ranges(fl, "is_bridge")
        if not tn and not br:
            continue
        whole[i] = False
        link = bool(_flag_ranges(fl, "is_link"))
        cuts = sorted({0.0, 1.0} | {min(max(v, 0.0), 1.0) for lo, hi, _ in tn + br for v in (lo, hi)})
        for a, b in zip(cuts[:-1], cuts[1:]):
            if b - a < 1e-6:
                continue
            mid = (a + b) / 2
            if any(lo <= mid <= hi for lo, hi, _ in tn):
                n_tunnel += 1
                continue
            part = substring(geoms[i], a, b, normalized=True)
            if part.geom_type != "LineString" or part.length < 1:
                continue
            isb = any(lo <= mid <= hi for lo, hi, _ in br)
            if isb and lm.covers(names[i], link, part, ids[i]):
                n_landmark += 1
                continue
            pieces.append((int(i), part, isb))
    log(f"roads: {n_tunnel} tunnel stretches and {n_landmark} stretches on landmark bridges left out")
    return whole, pieces


def bridge_decks(pieces, year, kind, width, ground):
    """Road bridges that are not landmarks: the bridge stretches of adjoining segments are
    chained, and a chain that crosses water or a valley becomes a plain deck — straight from
    one abutment's ground to the other's, with a hump of at most 7 m (5 % approaches) over
    water (clearances are not recorded: `estimated`). Flat overpasses stay on the ground.
    Returns (3D items with the rows of their pieces, indices of the pieces they replace)."""
    idx = [k for k, (_, g, b) in enumerate(pieces) if b and g.length >= 30]
    if not idx:
        return [], set()
    lines = [pieces[k][1] for k in idx]
    deg = {}
    for g in lines:
        for c in (g.coords[0], g.coords[-1]):
            key = (round(c[0], 1), round(c[1], 1))
            deg[key] = deg.get(key, 0) + 1
    merged = linemerge(MultiLineString(lines))
    chains = list(getattr(merged, "geoms", [merged]))
    tree = shapely.STRtree(chains)
    member = tree.nearest(np.array([g.interpolate(0.5, normalized=True) for g in lines], dtype=object))
    items, used = [], set()
    for c, chain in enumerate(chains):
        mem = [idx[j] for j in np.nonzero(member == c)[0]]
        L = chain.length
        if not mem or L < 40:
            continue
        nv = max(2, int(math.ceil(L / 15)) + 1)
        d = np.linspace(0, L, nv)
        pts = shapely.line_interpolate_point(chain, d)
        lon, lat = to_ll(shapely.get_x(pts), shapely.get_y(pts))
        gz = ground(lon, lat)
        ends = []
        for cc, z in ((chain.coords[0], gz[0]), (chain.coords[-1], gz[-1])):
            # an end where three decks meet is a junction on the structure, not an abutment
            ends.append(z + (6.0 if deg.get((round(cc[0], 1), round(cc[1], 1)), 1) >= 3 else 0.0))
        z = ends[0] + (ends[1] - ends[0]) * d / L
        if (gz <= 1.0).mean() >= 0.3:
            z = z + np.minimum(7.0, 0.05 * np.minimum(d, L - d))
        z = np.maximum(z, gz) + 0.5
        if (z - gz).max() <= 4.5:
            continue
        rows = [pieces[k][0] for k in mem]
        items.append(((lon, lat, z, int(kind[rows].max()), float(width[rows].max()), float(year[rows].max()), 9999.0,
                       ELEV["viaduct"]), rows))
        used.update(mem)
    return items, used


# ---------------------------------------------------------------- writer
def dense_coords(lines, step):
    """Vertices of UTM lines (simplified to 1 m) plus extra ones, so that no edge is longer
    than `step` (scalar or one per line) and the ribbon follows the terrain it is draped on.
    Returns (xy, vertex count per line)."""
    lines = shapely.simplify(np.asarray(lines, dtype=object), 1.0)
    c, li = shapely.get_coordinates(lines, return_index=True)
    step = np.broadcast_to(np.asarray(step, float), (len(lines),))
    same = li[1:] == li[:-1]
    d = np.hypot(c[1:, 0] - c[:-1, 0], c[1:, 1] - c[:-1, 1])
    m = np.where(same, np.maximum(1, np.ceil(d / step[li[:-1]])), 1).astype(int)
    m = np.append(m, 1)
    rep = np.repeat(np.arange(len(c)), m)
    k = np.arange(len(rep)) - np.repeat(np.cumsum(m) - m, m)
    t = (k / np.repeat(m, m))[:, None]
    nxt = np.minimum(rep + 1, len(c) - 1)
    xy = c[rep] + (c[nxt] - c[rep]) * t
    return xy, np.bincount(li[rep], minlength=len(lines))


def write_paths(path, items, ground, z_offset_fn, step=25.0, step_outer=None):
    """items: (utm LineString, kind, width, start, end, elevated), draped on the ground, or
    (lon[], lat[], z[], kind, width, start, end, elevated) with its own heights.
    step: vertex spacing (m) so paths follow the terrain grid they drape on; step_outer:
    the spacing of the paths outside the city box (the ~58 m region grid), if different."""
    flat = [it for it in items if len(it) == 6 and it[0] is not None and it[0].length >= 1]
    deep = [it for it in items if len(it) == 8]
    pos, counts, meta = [], [], []
    if flat:
        ferry = np.array([it[1] == K_FERRY for it in flat])
        lines = np.array([it[0] for it in flat], dtype=object)
        steps = np.full(len(flat), float(step))
        if step_outer is not None:
            mid = shapely.line_interpolate_point(lines, 0.5, normalized=True)
            mlon, mlat = to_ll(shapely.get_x(mid), shapely.get_y(mid))
            steps = np.where(in_city_box(mlon, mlat), steps, float(step_outer))
        xy, n = dense_coords(lines, np.where(ferry, 400.0, steps))
        lon, lat = to_ll(xy[:, 0], xy[:, 1])
        off = np.array([z_offset_fn(it[1], it[5]) for it in flat])
        z = np.where(np.repeat(ferry, n), 1.2, ground(lon, lat) + np.repeat(off, n))
        pos.append(np.column_stack([lon - ORIGIN[0], lat - ORIGIN[1], z]))
        counts.append(n)
        meta += [it[1:] for it in flat]
    for lon, lat, z, *rest in deep:
        pos.append(np.column_stack([np.asarray(lon) - ORIGIN[0], np.asarray(lat) - ORIGIN[1], z]))
        counts.append([len(lon)])
        meta.append(tuple(rest))
    if not meta:
        return 0
    counts = np.concatenate(counts)
    starts = np.concatenate([[0], np.cumsum(counts)])
    pos = np.vstack(pos)
    pos[:, :2] = np.round(pos[:, :2] / QUANT_XY) * QUANT_XY
    pos[:, 2] = np.round(pos[:, 2] / QUANT_Z) * QUANT_Z
    write_columnar(path, {
        "start_indices|shuffle": starts.astype(np.uint32),
        "positions|shuffle": pos.astype(np.float32).ravel(),
        "kind": np.asarray([m[0] for m in meta], np.uint8),
        "width": np.clip(np.rint([m[1] for m in meta]), 1, 255).astype(np.uint8),
        "years": np.asarray([(m[2], m[3]) for m in meta], np.float32).ravel(),
        "elevated": np.asarray([m[4] for m in meta], np.uint8),
    }, origin=ORIGIN, counts={"paths": len(meta), "vertices": int(starts[-1])})
    return len(meta)


def write_paths3d(path, items):
    """items: (lon array, lat array, z array, kind, width, start, end, elevated)."""
    n = write_paths(path, items, None, None)
    log(f"roads: wrote {path.name}: {n} paths")


def z_offset(kind, el):
    if el == ELEV["viaduct"]:
        return 9.0  # researched routes on a viaduct (the elevated West Side Highway): estimated deck height
    if el == ELEV["bridge"]:
        return 20.0
    if el == ELEV["embankment"]:
        return 3.0
    return {K_FREEWAY: 0.7, K_HIGHWAY: 0.6, K_MAJOR: 0.5}.get(kind, 0.45)


# ---------------------------------------------------------------- routes
def read_routes():
    """data/manual/routes.csv -> rows (id, UTM line, kind, width, start, end, elevated).
    geom_type `lonlat`: "lon lat; lon lat; ..." (taken from Overture / street centre lines)."""
    p = MANUAL / "routes.csv"
    if not p.exists():
        log("roads: no data/manual/routes.csv")
        return []
    t = pd.read_csv(p, dtype=str).fillna("")
    out, skipped = [], {}
    for r in t.itertuples():
        mode = r.mode.strip()
        k = MODE_KIND.get(mode)
        if k is None or (mode in TRANSIT_MODES and TRANSIT_TAKES_OVER):
            skipped[mode] = skipped.get(mode, 0) + 1
            continue
        if r.geom_type.strip() != "lonlat":
            skipped[r.geom_type] = skipped.get(r.geom_type, 0) + 1
            continue
        pts = [tuple(map(float, q.split()[:2])) for q in r.geom.split(";") if q.strip()]
        if len(pts) < 2:
            continue
        x, y = _TO_UTM.transform([q[0] for q in pts], [q[1] for q in pts])
        y0 = pd.to_numeric(r.year_start, errors="coerce")
        y1 = pd.to_numeric(r.year_end, errors="coerce")
        if not np.isfinite(y0):
            continue
        out.append((r.route_id, LineString(np.column_stack([x, y])), k, ROAD_WIDTH if mode == "road" else WIDTH[k],
                    float(y0), float(y1) if np.isfinite(y1) else 9999.0, ELEV.get(r.elevated.strip(), 0)))
    if skipped:
        log(f"roads: routes.csv rows not drawn here: {skipped}")
    return out


# ---------------------------------------------------------------- freeways in 3D
def freeway_items(ground, fw_routes, lm, date_trunk, streets=None, report=None, areas=None):
    """Motorways, trunks and ramps (Overture) with a height profile per vertex.

    Height above ground: level 1 viaducts ~12.5 m, level 2 ~22 m (+5.5 m for each level
    above), other bridges 6.5 m, at grade 0.7 m. Approaches climb at most ~5.5 % (the profile is dilated with that
    slope cone), junctions share one height (connectors), and ramp ends that meet a
    surface street (a connector no other freeway segment uses), mainline ends and tunnel
    portals come down to grade through the network (see below). Tunnel portions and the
    decks of the landmark bridges are dropped. Dates: the parallel researched route; ramps
    open with the latest mainline they connect; a trunk road without a researched route is an
    arterial street and is dated like the main roads (date_trunk)."""
    fwy = gpd.read_parquet(RAW / "overture" / RELEASE / "freeways.parquet")
    if fwy.crs is None:
        fwy = fwy.set_crs(4326)
    fwy = fwy[fwy.geometry.geom_type == "LineString"].reset_index(drop=True)
    fwu = fwy.to_crs(UTM)
    SLOPE, DOWN = 0.055, 0.08
    segs = []
    conn_count = {}
    for i, row in fwy.iterrows():
        g = fwu.geometry.iloc[i]
        L = g.length
        if L < 1 or _flag_ranges(row.road_flags, "is_under_construction"):
            continue
        n = max(2, int(math.ceil(L / 25.0)) + 1)
        f = np.linspace(0, 1, n)
        lev = np.zeros(n)
        for lo, hi, v in _flag_ranges(row.level_rules):
            lev[(f >= lo) & (f <= hi)] = v
        br = np.zeros(n, bool)
        for lo, hi, _ in _flag_ranges(row.road_flags, "is_bridge"):
            br[(f >= lo) & (f <= hi)] = True
        tn = np.zeros(n, bool)
        for lo, hi, _ in _flag_ranges(row.road_flags, "is_tunnel"):
            tn[(f >= lo) & (f <= hi)] = True
        # levels above 2 mostly tell the ramps of a stack interchange apart: 5.5 m each
        h = np.where(lev >= 1, 3.0 + 9.5 * np.minimum(lev, 2) + 5.5 * np.maximum(lev - 2, 0), np.where(br, 6.5, 0.7))
        tn_real = tn.copy()
        nm = row["name"] if isinstance(row["name"], str) else ""
        if br.any():
            # the decks of the big bridges belong to their landmark models
            pts = shapely.line_interpolate_point(g, f, normalized=True)
            tn = tn | (br & lm.vertex_mask(nm, row.subclass == "link", shapely.get_x(pts), shapely.get_y(pts), row["id"]))
        conns = [(c["connector_id"], float(c["at"])) for c in (row.connectors if row.connectors is not None else [])]
        for cid, _ in conns:
            conn_count[cid] = conn_count.get(cid, 0) + 1
        segs.append({"i": i, "g": g, "f": f, "s": f * L, "h": h, "tn": tn, "tn_real": tn_real, "conns": conns,
                     "cls": row["class"], "sub": row.subclass, "bounds": row.geometry.bounds, "name": nm,
                     "id": str(row["id"]), "br": bool(br.mean() >= 0.5), "brv": br & ~tn})
    # the extract is wider than the map: heights and junctions are worked out on the whole
    # network, but only roads inside the map's extent (+ margin) are written
    inside = in_extent(shapely.points([(sg["bounds"][0] + sg["bounds"][2]) / 2 for sg in segs],
                                      [(sg["bounds"][1] + sg["bounds"][3]) / 2 for sg in segs]))
    area = (boro_of(shapely.points([(sg["bounds"][0] + sg["bounds"][2]) / 2 for sg in segs],
                                   [(sg["bounds"][1] + sg["bounds"][3]) / 2 for sg in segs]), areas)
            if areas else [""] * len(segs))
    for sg, ok, ar in zip(segs, inside, area):
        sg["in"] = bool(ok)
        sg["area"] = AREA_NAME.get(ar, "(edge band)")

    def dilate(seg):
        h, s_ = seg["h"], seg["s"]
        for k in range(1, len(h)):
            h[k] = max(h[k], h[k - 1] - SLOPE * (s_[k] - s_[k - 1]))
        for k in range(len(h) - 2, -1, -1):
            h[k] = max(h[k], h[k + 1] - SLOPE * (s_[k + 1] - s_[k]))

    def idx_at(seg, at):
        return int(np.argmin(np.abs(seg["f"] - at)))

    for seg in segs:
        dilate(seg)
    for _ in range(2):  # junction heights: highest wins, then re-dilate
        node_h = {}
        for seg in segs:
            for cid, at in seg["conns"]:
                node_h[cid] = max(node_h.get(cid, 0.0), seg["h"][idx_at(seg, at)])
        for seg in segs:
            for cid, at in seg["conns"]:
                k = idx_at(seg, at)
                seg["h"][k] = max(seg["h"][k], node_h[cid])
            dilate(seg)
    # Where a freeway meets the ground: ends that no other freeway segment uses (ramp or
    # mainline meeting a surface street) and tunnel portals are pinned at grade, and the
    # road comes down to them through the network (graph distance across connectors):
    #   * ramps (links) blend from the mainline height at their junction to the street
    #     (at most 8 % where they are long enough, steeper on short ramps so they never
    #     detach from the mainline);
    #   * mainline ends descend at 5 %;
    #   * tunnel approaches descend at 5.5 % to meet the ground at the portal.
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import dijkstra
    x0, y0_, x1, y1_ = REGION_BBOX_ROADS
    offs = np.cumsum([0] + [len(sg["f"]) for sg in segs])
    N = int(offs[-1])
    is_link = np.zeros(N, bool)
    real_tn = np.zeros(N, bool)
    rows, cols, wts = [], [], []
    for q, sg in enumerate(segs):
        o = int(offs[q])
        is_link[o:o + len(sg["f"])] = sg["sub"] == "link"
        real_tn[o:o + len(sg["f"])] = sg["tn_real"]
        ds = np.maximum(np.diff(sg["s"]), 1e-3)
        a = np.arange(o, o + len(ds))
        rows.append(a)
        cols.append(a + 1)
        wts.append(ds)
    members = {}
    for q, sg in enumerate(segs):
        for cid, at in sg["conns"]:
            members.setdefault(cid, []).append((int(offs[q]) + idx_at(sg, at), q))
    jr, jc = [], []
    for mem in members.values():
        for (a, _), (b, _) in zip(mem[:-1], mem[1:]):
            jr.append(a)
            jc.append(b)
    rows = np.concatenate(rows + [np.array(jr, int)])
    cols = np.concatenate(cols + [np.array(jc, int)])
    wts = np.concatenate(wts + [np.full(len(jr), 1e-3)])
    G = csr_matrix((wts, (rows, cols)), shape=(N, N))
    H = np.concatenate([sg["h"] for sg in segs])
    street_link, street_main = [], []
    for q, sg in enumerate(segs):
        for cid, at in sg["conns"]:
            if conn_count.get(cid, 0) > 1 or at not in (0.0, 1.0):
                continue
            pt = sg["g"].interpolate(at, normalized=True)
            lon_, lat_ = to_ll(pt.x, pt.y)
            if not (x0 + 0.004 < lon_ < x1 - 0.004 and y0_ + 0.004 < lat_ < y1_ - 0.004):
                continue  # cut by the edge of the extract, not a real end
            v = int(offs[q]) + idx_at(sg, at)
            (street_link if sg["sub"] == "link" else street_main).append(v)
    cap = np.full(N, np.inf)
    if real_tn.any():
        d = dijkstra(G, directed=False, indices=np.nonzero(real_tn)[0], min_only=True)
        cap = np.minimum(cap, 0.7 + SLOPE * d)
    if street_main:
        d = dijkstra(G, directed=False, indices=street_main, min_only=True)
        cap = np.minimum(cap, 0.7 + 0.05 * d)
    if street_link:
        # ramps only: distances inside the link network
        lk = np.nonzero(is_link)[0]
        pos_in = -np.ones(N, int)
        pos_in[lk] = np.arange(len(lk))
        sub = G[lk][:, lk]
        d_pin = dijkstra(sub, directed=False, indices=pos_in[street_link], min_only=True)
        # link vertices at a junction with a mainline segment
        jn = sorted({a for mem in members.values() if any(not is_link[a2] for a2, _ in mem) for a, _ in mem if is_link[a]})
        if jn:
            d_main, _, src = dijkstra(sub, directed=False, indices=pos_in[jn], min_only=True, return_predecessors=True)
            Hsrc = np.where(src >= 0, H[lk[np.maximum(src, 0)]], 0.7)
            t = np.where(np.isfinite(d_main) & np.isfinite(d_pin), d_pin / np.maximum(d_pin + d_main, 1e-3), 1.0)
            interp = 0.7 + (Hsrc - 0.7) * t
        else:
            interp = np.full(len(lk), 0.7)
        c = np.where(np.isfinite(d_pin), np.maximum(0.7 + DOWN * d_pin, interp), np.inf)
        cap[lk] = np.minimum(cap[lk], c)
    H = np.minimum(H, cap)
    # Where a landmark bridge model ends high above the terrain grid, the generic road takes
    # over at the model's deck height and comes down from there at 5 % (in absolute height:
    # where the ground rises to meet it, as on the Palisades or Washington Heights, it is at
    # grade sooner). The ends are the dropped vertices next to a kept one; BRIDGE_END_PINS
    # gives the deck height of the ends that need it.
    lm_mask = np.concatenate([sg["tn"] & ~sg["tn_real"] for sg in segs])
    vxy = np.vstack([np.column_stack([shapely.get_x(p_), shapely.get_y(p_)]) for p_ in
                     (shapely.line_interpolate_point(sg["g"], sg["f"], normalized=True) for sg in segs)])
    vlon, vlat = to_ll(vxy[:, 0], vxy[:, 1])
    vground = ground(vlon, vlat)
    seg_of = np.repeat(np.arange(len(segs)), np.diff(offs))
    a_, b_ = rows, cols
    edge = lm_mask[a_] != lm_mask[b_]
    ends = np.unique(np.where(lm_mask[a_[edge]], a_[edge], b_[edge]))
    pins = {}
    dump = []
    for v in ends:
        sg = segs[seg_of[v]]
        z = bridge_end_height(sg["name"], sg["id"], vlon[v], vlat[v])
        dump.append({"name": sg["name"], "id": sg["id"][:8], "lon": round(float(vlon[v]), 5), "lat": round(float(vlat[v]), 5),
                     "ground_m": round(float(vground[v]), 1), "generic_deck_m": round(float(vground[v] + H[v]), 1),
                     "pinned_m": z})
        if z is not None:
            pins.setdefault(float(z), []).append(int(v))
    pd.DataFrame(dump).to_csv(SCRATCH / "bridge_model_ends.csv", index=False)
    n_pin = 0
    dist = {z: dijkstra(G, directed=False, indices=vs, min_only=True, limit=900.0) for z, vs in pins.items()}
    for z, d in dist.items():  # not above the model's end ...
        cap = np.maximum((z + 0.05 * d) - vground, 0.7)
        low = np.isfinite(d) & (cap < H)
        H[low] = cap[low]
    for z, d in dist.items():  # ... and not below it
        lift = (z - 0.05 * d) - vground
        up = np.isfinite(d) & (lift > H)
        H[up] = lift[up]
        n_pin += len(pins[z])
    log(f"roads: {len(ends)} ends of landmark bridge decks, {n_pin} pinned at the model's deck height")
    # A bridge is level between its abutments. The heights so far are above the ground under
    # each vertex: over a gorge or a river between high banks (the Bear Mountain Bridge, the
    # east end of the Tappan Zee Bridge) the deck would follow the ground down to the water.
    # Every bridge vertex is at least as high as each abutment less BRIDGE_SAG of the way to
    # it — one shortest-path pass over the bridge vertices, the abutments (the vertices next
    # to a bridge stretch) as sources. Clearances are not recorded: `estimated`.
    brm = np.concatenate([sg["brv"] for sg in segs])
    zabs = vground + H
    eb = brm[a_] | brm[b_]
    ea, eb2 = a_[eb], b_[eb]
    abut = np.unique(np.concatenate([ea[~brm[ea]], eb2[~brm[eb2]]]))
    abut = abut[~lm_mask[abut] & ~real_tn[abut]]
    n_lift = 0
    if len(abut):
        ztop = float(zabs[abut].max()) + 1.0
        gb = csr_matrix((np.concatenate([np.maximum(BRIDGE_SAG * wts[eb], 1e-6), ztop - zabs[abut]]),
                         (np.concatenate([ea, np.full(len(abut), N)]), np.concatenate([eb2, abut]))), shape=(N + 1, N + 1))
        level = ztop - dijkstra(gb, directed=False, indices=N)[:N]
        up = brm & np.isfinite(level) & (level - vground > H + 0.5)
        H[up] = (level - vground)[up]
        n_lift = int(up.sum())
    log(f"roads: {n_lift} bridge vertices raised to the level of their abutments")
    # keep junctions continuous after lowering: the lowest member wins, and a road may
    # climb away from a lowered junction at no more than 8 %
    for _ in range(4):
        for mem in members.values():
            idx = [a for a, _ in mem]
            H[idx] = H[idx].min()
        for q, sg in enumerate(segs):
            o, n_ = int(offs[q]), len(sg["f"])
            hs, s_ = H[o:o + n_], sg["s"]
            for k in range(1, n_):
                hs[k] = min(hs[k], hs[k - 1] + DOWN * (s_[k] - s_[k - 1]))
            for k in range(n_ - 2, -1, -1):
                hs[k] = min(hs[k], hs[k + 1] + DOWN * (s_[k + 1] - s_[k]))
    for q, sg in enumerate(segs):
        sg["h"] = H[int(offs[q]):int(offs[q + 1])]
    log(f"roads: freeway grade pins: {len(street_main)} mainline ends, {len(street_link)} ramp ends, "
        f"{int(real_tn.sum())} tunnel vertices")

    # Dates: a mainline segment takes the year of the researched route running along it
    # (parallel, <= 150 m; a crossing highway at an interchange doesn't count); ramps open
    # with the latest of the mainlines they connect.
    fw_routes_tree = cKDTree(fw_routes[0]) if fw_routes is not None else None

    def vote(seg):
        if fw_routes is None:
            return None
        _, T, Y = fw_routes
        ys = []
        for fr in (0.1, 0.3, 0.5, 0.7, 0.9):
            g = seg["g"]
            a = g.interpolate(max(fr - 0.02, 0), normalized=True)
            b = g.interpolate(min(fr + 0.02, 1), normalized=True)
            tv = np.array([b.x - a.x, b.y - a.y])
            tv /= max(np.linalg.norm(tv), 1e-6)
            m = g.interpolate(fr, normalized=True)
            dd, ii = fw_routes_tree.query((m.x, m.y), k=12, distance_upper_bound=150)
            for d_, j in zip(np.atleast_1d(dd), np.atleast_1d(ii)):
                if np.isfinite(d_) and abs(float(T[j] @ tv)) > 0.8:
                    ys.append(Y[j])
                    break
        return float(np.median(ys)) if ys else None

    for sg in segs:
        sg["year"] = vote(sg) if sg["sub"] != "link" else None
        sg["src"] = SRC_RESEARCHED if sg["year"] is not None else SRC_DEFAULT
    # mainlines without a parallel route: the nearest route within 60 m, else the default
    # (motorways: a missing row in routes.csv, reported) — a trunk road without a researched
    # route is an arterial street (Linden Boulevard, West Street, Canal Street, the Conduit
    # avenues…), dated like the other main roads by the buildings along it
    undated = []
    for q, sg in enumerate(segs):
        if sg["sub"] != "link" and sg["year"] is None:
            sg["year"] = DEFAULT_FREEWAY
            if fw_routes_tree is not None:
                m = sg["g"].interpolate(0.5, normalized=True)
                dd, ii = fw_routes_tree.query((m.x, m.y))
                if dd < 60:
                    sg["year"] = float(fw_routes[2][ii])
                    sg["src"] = SRC_RESEARCHED
                    continue
            if sg["cls"] == "trunk":
                undated.append(q)
    if undated:
        yrs, src = date_trunk([segs[q]["g"] for q in undated], [segs[q]["name"] for q in undated])
        # one road, one year: a through road does not open house by house — every stretch of a
        # named road takes the early quartile of its building-dated stretches
        by_name = {}
        for q, y, s in zip(undated, yrs, src):
            if segs[q]["in"] and s in (SRC_BUILDINGS, SRC_BUILDINGS_WIDE):
                by_name.setdefault(segs[q]["name"], []).append(float(y))
        for q, y, s in zip(undated, yrs, src):
            ys = by_name.get(segs[q]["name"]) if segs[q]["name"] else None
            segs[q]["year"] = float(np.quantile(ys, 0.25)) if ys and len(ys) >= 4 and s != SRC_RESEARCHED else float(y)
            segs[q]["src"] = int(s)
        log(f"roads: {len(undated)} trunk road segments without a researched route dated like main roads "
            f"({int(np.isin(src, (SRC_BUILDINGS, SRC_BUILDINGS_WIDE)).sum())} by the buildings along them)")
    # nothing before its ground (the river drives stand on fill)
    mids = [sg["g"].interpolate(fr, normalized=True) for sg in segs for fr in (0.1, 0.5, 0.9)]
    lon_, lat_ = to_ll([p.x for p in mids], [p.y for p in mids])
    ly = np.median(np.nan_to_num(land_year(lon_, lat_), nan=-np.inf).reshape(-1, 3), axis=1)
    main = [q for q, sg in enumerate(segs) if sg["sub"] != "link" and not sg["br"] and sg["in"]]
    yy = after_ground([segs[q]["year"] for q in main], np.where(np.isfinite(ly[main]), ly[main], np.nan),
                      np.array([segs[q]["src"] == SRC_RESEARCHED for q in main]),
                      ("highway", [segs[q]["name"] for q in main], lon_[1::3][main], lat_[1::3][main],
                       [segs[q]["g"].length for q in main]))
    n_ground = 0
    for q, y in zip(main, yy):
        n_ground += y > segs[q]["year"] + 0.01
        segs[q]["year"] = float(y)
    for q, sg in enumerate(segs):
        sg["ly"] = float(ly[q]) if np.isfinite(ly[q]) else None
    missing = {}
    for sg in segs:
        if sg["sub"] != "link" and sg["in"] and sg["src"] == SRC_DEFAULT:
            k = f"{sg['cls']}: {sg['name'] or '(unnamed)'}"
            e = missing.setdefault(k, [0, 0.0, set()])
            e[0] += 1
            e[1] += sg["g"].length
            e[2].add(sg["area"])
    pd.DataFrame([{"id": sg["id"], "name": sg["name"], "class": sg["cls"], "area": sg["area"], "year": round(sg["year"], 2),
                   "src": sg["src"], "land_year": sg["ly"], "bridge": sg["br"],
                   "m": round(sg["g"].length, 1), "lon": round((sg["bounds"][0] + sg["bounds"][2]) / 2, 5),
                   "lat": round((sg["bounds"][1] + sg["bounds"][3]) / 2, 5)}
                  for sg in segs if sg["sub"] != "link" and sg["in"]]).to_csv(SCRATCH / "highway_years.csv", index=False)
    n_def = sum(e[0] for e in missing.values())
    log(f"roads: {n_def} motorway / trunk mainline segments inside the map left on a default year "
        f"({sum(e[1] for e in missing.values()) / 1000:.1f} km): missing rows in routes.csv")
    if report is not None:
        main_in = [sg for sg in segs if sg["sub"] != "link" and sg["in"]]
        km = {}
        for sg in main_in:
            e = km.setdefault(sg["area"], {}).setdefault(sg["cls"], {name: 0.0 for name, _ in SRC_NAMES})
            e[next(name for name, code in SRC_NAMES if code == sg["src"])] += sg["g"].length / 1000
        report["freeways"] = {
            "mainline_segments_in_map": len(main_in),
            "by_source": {name: int(sum(sg["src"] == code for sg in main_in)) for name, code in SRC_NAMES},
            # motorway / trunk mainline km by area and by how they were dated (researched = a row of
            # routes.csv; buildings / neighbour = a trunk road dated like a main road; default = no row)
            "km_by_area": {a: {c: {k: round(v, 1) for k, v in e.items()} for c, e in sorted(d.items())}
                           for a, d in sorted(km.items())},
            "moved_later_by_ground": int(n_ground),
            "on_default": {k: {"segments": e[0], "km": round(e[1] / 1000, 2), "areas": sorted(e[2])} for k, e in
                           sorted(missing.items(), key=lambda kv: -kv[1][1])},
        }
    # ramps: connected components of link segments
    parent = list(range(len(segs)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for mem in members.values():
        lq = [q for _, q in mem if segs[q]["sub"] == "link"]
        for a, b in zip(lq[:-1], lq[1:]):
            parent[find(a)] = find(b)
    comp_year = {}
    for mem in members.values():
        mains = [segs[q]["year"] for _, q in mem if segs[q]["sub"] != "link"]
        links = [q for _, q in mem if segs[q]["sub"] == "link"]
        if mains and links:
            for q in links:
                r = find(q)
                comp_year[r] = max(comp_year.get(r, -1e9), max(mains))
    for q, sg in enumerate(segs):
        if sg["sub"] == "link":
            sg["year"] = comp_year.get(find(q))
            if sg["year"] is None:
                sg["year"] = vote(sg) or DEFAULT_FREEWAY
    for sg in segs:
        sg["year"] = float(min(max(sg["year"], YEAR_MIN), CURRENT_YEAR + 1.0))

    # sample positions once
    for sg in segs:
        pts = shapely.line_interpolate_point(sg["g"], sg["f"], normalized=True)
        sg["xy"] = np.column_stack([shapely.get_x(pts), shapely.get_y(pts)])

    # ramp / mainline ends meeting a street: one more vertex on the street centreline,
    # so the ramp visibly joins it instead of stopping beside it
    if streets is not None:
        from shapely.geometry import Point as _P
        stree = shapely.STRtree(streets)
        n_snap = 0
        for sg in segs:
            if not sg["in"]:
                continue
            for cid, at in sg["conns"]:
                if conn_count.get(cid, 0) > 1 or at not in (0.0, 1.0) or sg["tn"][0 if at == 0.0 else -1]:
                    continue
                e = sg["xy"][0] if at == 0.0 else sg["xy"][-1]
                cand = stree.query(_P(e).buffer(30))
                if not len(cand):
                    continue
                best = min(cand, key=lambda j: streets[j].distance(_P(e)))
                line = streets[best]
                d = line.distance(_P(e))
                if d < 2 or d > 30:
                    continue
                q = line.interpolate(line.project(_P(e)))
                extra = np.array([[q.x, q.y]])
                hh = np.array([0.7])
                if at == 0.0:
                    sg["xy"] = np.vstack([extra, sg["xy"]])
                    sg["h"] = np.concatenate([hh, sg["h"]])
                    sg["tn"] = np.concatenate([[False], sg["tn"]])
                    sg["f"] = np.concatenate([[0.0], sg["f"]])
                else:
                    sg["xy"] = np.vstack([sg["xy"], extra])
                    sg["h"] = np.concatenate([sg["h"], hh])
                    sg["tn"] = np.concatenate([sg["tn"], [False]])
                    sg["f"] = np.concatenate([sg["f"], [1.0]])
                n_snap += 1
        log(f"roads: {n_snap} freeway / ramp ends extended onto their street")

    # Draw continuous roads: chain segments end to end through connectors joining exactly
    # two segments of the same road kind and date (Overture splits a road at every
    # connector; drawn one by one they read as loose straight pieces with gaps).
    end_nodes = {}
    for q, sg in enumerate(segs):
        for cid, at in sg["conns"]:
            if at in (0.0, 1.0):
                end_nodes.setdefault(cid, []).append((q, at))

    def key_of(sg):
        return (sg["cls"], sg["sub"] == "link", float(sg["year"]))

    def next_seg(q, at):
        """the segment continuing segment q beyond its end `at` (0 or 1), or None"""
        sg = segs[q]
        cid = next((c for c, a in sg["conns"] if a == at), None)
        if cid is None or conn_count.get(cid, 0) != 2:
            return None
        mem = end_nodes.get(cid, [])
        others = [(q2, a2) for q2, a2 in mem if q2 != q]
        if len(others) != 1:
            return None
        q2, a2 = others[0]
        if key_of(segs[q2]) != key_of(sg):
            return None
        return q2, a2

    used = np.zeros(len(segs), bool)
    chains = []
    for q in range(len(segs)):
        if used[q]:
            continue
        # walk back to the start of the chain
        cur, cur_at = q, 0.0
        seen = {q}
        while True:
            nx = next_seg(cur, cur_at)
            if nx is None or nx[0] in seen or used[nx[0]]:
                break
            cur, cur_at = nx[0], 1.0 - nx[1]
            seen.add(cur)
        # now walk forward from cur, entering at cur_at
        chain = []
        c, enter = cur, cur_at
        while c is not None and not used[c]:
            used[c] = True
            chain.append((c, enter == 1.0))  # reversed if we enter at its end
            nx = next_seg(c, 1.0 - enter)
            if nx is None:
                break
            c, enter = nx
        chains.append(chain)

    items = []
    for chain in chains:
        if not any(segs[q]["in"] for q, _ in chain):
            continue  # outside the map
        XY, Hh, TN = [], [], []
        for k_, (q, rev) in enumerate(chain):
            sg = segs[q]
            xy, hq, tq = sg["xy"], sg["h"], sg["tn"]
            if rev:
                xy, hq, tq = xy[::-1], hq[::-1], tq[::-1]
            if k_ > 0:
                xy, hq, tq = xy[1:], hq[1:], tq[1:]
            XY.append(xy)
            Hh.append(hq)
            TN.append(tq)
        XY = np.vstack(XY)
        Hh = np.concatenate(Hh)
        TN = np.concatenate(TN)
        sg0 = segs[chain[0][0]]
        lon, lat = to_ll(XY[:, 0], XY[:, 1])
        z = ground(lon, lat) + Hh
        y0 = float(sg0["year"])
        link = sg0["sub"] == "link"
        k = K_FREEWAY if sg0["cls"] == "motorway" else K_HIGHWAY
        width = 6.5 if link else (13.0 if sg0["cls"] == "motorway" else 11.0)
        # split at tunnels (and at the spans the landmark models draw)
        keep = ~TN
        start = None
        for j in range(len(keep) + 1):
            if j < len(keep) and keep[j]:
                start = j if start is None else start
            elif start is not None:
                if j - start >= 2:
                    sl = slice(start, j)
                    hmax = float(Hh[sl].max())
                    items.append((lon[sl], lat[sl], z[sl], k, width, y0, 9999.0, 2 if hmax > 4 else 0))
                start = None
    log(f"roads: {len(items)} freeway / ramp paths in 3D")
    return items


# ---------------------------------------------------------------- main
LOCAL_Z = 12  # tiles of the residential street grid (~7.4 km), loaded from zoom 12.5
LOCAL_LOW_Z = 10  # simplified street grid for city scale


def _tile(lon, lat, z):
    n = 2 ** z
    la = np.radians(lat)
    return (np.floor((lon + 180) / 360 * n).astype(int),
            np.floor((1 - np.log(np.tan(la) + 1 / np.cos(la)) / np.pi) / 2 * n).astype(int))


def main():
    from nyc_buildings import Ground
    t0 = time.time()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    report = {}
    ground = Ground()
    boros = boroughs()
    lm = LandmarkBridges()
    bld = building_tree()

    # ---- every ordinary road of the five boroughs and the map's counties (the extracts cover
    # the whole region box: each is cut down to the map before the next is read)
    base = RAW / "overture" / RELEASE
    cols = ["id", "class", "name", "road_flags", "geometry"]
    parts = []
    for fname, is_local in (("roads_region", False), ("roads_local", True)):
        a = gpd.read_parquet(base / f"{fname}.parquet", columns=cols)
        if not is_local:
            a = a[~a["class"].isin(["motorway", "trunk"])]  # drawn in 3D from freeways.bin.gz
        a = a[(a.geometry.geom_type == "LineString") & (shapely.length(a.geometry.values) > 0)]
        mid = shapely.line_interpolate_point(a.geometry.values, 0.5, normalized=True)
        a = a.assign(local=is_local, boro=boro_of(mid, boros), lon=shapely.get_x(mid), lat=shapely.get_y(mid))
        parts.append(a[a.boro != ""])
        del a, mid
    r = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), geometry="geometry", crs=parts[0].crs or 4326)
    del parts
    if r.crs is None:
        r = r.set_crs(4326)
    r["name_u"] = r["name"].fillna("").str.upper().str.strip()
    ru = r.to_crs(UTM)
    county = ~np.isin(r.boro.values, list(BORO_NAME))  # outside the five boroughs
    main_road = r["class"].isin(["primary", "secondary"]).values
    kind = np.where(main_road, K_MAJOR, K_STREET)
    width = np.where(main_road, WIDTH[K_MAJOR], WIDTH[K_STREET]) - np.where(r["class"].values == "service", 2, 0)
    default = np.where(r.local.values, DEFAULT_LOCAL, DEFAULT_MAIN)
    year, src, ly, dated_tree = date_lines(ru.geometry.values, default, bld, wide=county)
    year, src, fixed = street_overrides(r.name_u.values, r.boro.values, r.lon.values, r.lat.values, year, src)
    n_res = int((src == SRC_RESEARCHED).sum())
    bridge_share = np.array([sum(hi - lo for lo, hi, _ in _flag_ranges(fl, "is_bridge")) if fl is not None else 0.0
                             for fl in r.road_flags.values])
    year0 = year.copy()
    year = after_ground(year, np.where(bridge_share >= 0.5, np.nan, ly), fixed,  # a bridge needs no ground
                        ("street", r.name_u.values, r.lon.values, r.lat.values, shapely.length(ru.geometry.values)))
    log(f"roads: {len(r)} street segments ({int((~county).sum())} in the five boroughs, {int(county.sum())} in the counties); "
        f"{n_res} take a researched year")
    seg_m = shapely.length(ru.geometry.values)

    # every segment with its year, for checks and for researching data/tables/street_dates.csv
    # (boro: "1".."5", or the county's FIPS code; src: SRC_NAMES)
    pd.DataFrame({"id": r["id"].values, "name": r.name_u.values, "boro": r.boro.values, "class": r["class"].values,
                  "year": np.round(year, 2), "src": src, "land_year": np.round(ly, 1), "by_ground": year0 < year - 0.01,
                  "fixed": fixed, "bridge": bridge_share >= 0.5,
                  "lon": r.lon.values.round(5), "lat": r.lat.values.round(5),
                  "m": np.round(seg_m, 1)}).to_parquet(SCRATCH / "street_years.parquet")

    whole, pieces = cut_roads(r, ru, lm)
    decks, used = bridge_decks(pieces, year, kind, width, ground)
    log(f"roads: {len(decks)} plain bridge decks over water / valleys ({len(used)} stretches)")
    manh = r.boro.values == "1"
    # the tile set: residential streets everywhere outside Manhattan, and the counties'
    # tertiary roads (the always-loaded file keeps their primary and secondary roads only)
    local = r.local.values | (county & ~main_road)
    geoms = ru.geometry.values.copy()
    geoms[county] = shapely.simplify(geoms[county], SIMPLIFY_COUNTY)

    def item(i, line):
        return (line, int(kind[i]), float(width[i]), float(year[i]), 9999.0, 0)

    sets = {"manhattan": [], "region": [], "local": []}

    def set_of(i):
        return "manhattan" if manh[i] else ("local" if local[i] else "region")

    drawn = np.zeros(len(r), bool)
    for i in np.nonzero(whole)[0]:
        sets[set_of(i)].append(item(i, geoms[i]))
        drawn[i] = True
    for k, (i, line, _) in enumerate(pieces):
        if k not in used:
            sets[set_of(i)].append(item(i, line))
            drawn[i] = True
    local_decks = []
    for it, rows in decks:
        drawn[rows] = True
        if manh[rows].any():
            sets["manhattan"].append(it)
        elif (~local[rows]).any():
            sets["region"].append(it)
        else:
            local_decks.append(it)

    n = write_paths(VIEWER_DATA / "roads-sf.bin.gz", sets["manhattan"], ground, z_offset, step=25.0)
    log(f"roads: wrote roads-sf.bin.gz: {n} paths (Manhattan)")
    n = write_paths(VIEWER_DATA / "roads-region.bin.gz", sets["region"], ground, z_offset, step=STEP_CITY, step_outer=STEP_OUTER)
    log(f"roads: wrote roads-region.bin.gz: {n} paths (main roads of the other boroughs and the counties)")
    n_tiles = local_tiles(sets["local"], local_decks, ground)

    def shares(mask):
        tot = int(mask.sum())
        return {"segments": tot, **{name: int((src[mask] == code).sum()) for name, code in SRC_NAMES}}

    def km_shares(mask):
        """street length (km) by how it was dated, and the share of each (%)"""
        tot = float(seg_m[mask].sum())
        out = {"km": round(tot / 1000, 1)}
        for name, code in SRC_NAMES:
            out[name + "_pct"] = round(100 * float(seg_m[mask & (src == code)].sum()) / max(tot, 1e-9), 2)
        return out
    report["streets"] = {"manhattan": shares(drawn & manh), "region_main": shares(drawn & ~manh & ~local),
                         "region_local": shares(drawn & ~manh & local), "all": shares(drawn),
                         "paths": {k: len(v) for k, v in sets.items()}, "bridge_decks": len(decks), "tiles": n_tiles}
    for k, v in report["streets"].items():
        if isinstance(v, dict) and "segments" in v:
            log(f"roads: {k}: {v['segments']} segments — {100 * (v['buildings'] + v['buildings_90m']) / max(v['segments'], 1):.1f} % "
                f"dated by buildings, {100 * v['researched'] / max(v['segments'], 1):.1f} % researched, "
                f"{100 * v['neighbour'] / max(v['segments'], 1):.1f} % by the nearest street, "
                f"{100 * v['default'] / max(v['segments'], 1):.1f} % default")
    by_area = {"five boroughs": km_shares(drawn & ~county), "counties": km_shares(drawn & county)}
    for code, name in AREA_NAME.items():
        by_area[name] = km_shares(drawn & (r.boro.values == code))
    report["streets"]["length_by_area"] = by_area
    for name, v in by_area.items():
        log(f"roads: {name}: {v['km']} km — buildings {v['buildings_pct']} % (+ {v['buildings_90m_pct']} % within 90 m), "
            f"nearest street {v['neighbour_pct']} %, default {v['default_pct']} %, researched {v['researched_pct']} %")
    # nothing estimated before its ground (researched rows stand: ground_conflicts.csv; a bridge needs none)
    held = ~fixed & (bridge_share < 0.5) & np.isfinite(ly)
    report["streets"]["ground"] = {"segments_on_made_land": int(np.isfinite(ly).sum()),
                                   "moved_later_by_ground": int((year0 < year - 0.01).sum()),
                                   "moved_later_in_counties": int(((year0 < year - 0.01) & county).sum()),
                                   "estimated_before_ground": int((held & (year < ly + 0.5 - 0.01) & (year < CURRENT_YEAR + 1.0)).sum())}
    log(f"roads: ground rule: {report['streets']['ground']}")

    # ---- researched routes
    routes = read_routes()
    is_standing = [rt[2] in (K_FREEWAY, K_HIGHWAY) and rt[5] >= 9999 for rt in routes]
    standing = [rt for rt, s_ in zip(routes, is_standing) if s_]
    draw = [rt[1:] for rt, s_ in zip(routes, is_standing)
            if not s_ and rt[0] not in LANDMARK_ROUTES and rt[6] != ELEV["tunnel"]]
    if draw:
        n = write_paths(VIEWER_DATA / "routes.bin.gz", draw, ground, z_offset, step=25.0)
        log(f"roads: wrote routes.bin.gz: {n} paths")
    report["routes"] = {"rows": len(routes), "date_overture": len(standing), "drawn": len(draw)}
    # researched highway lines with their direction, to date Overture's real geometry: only
    # roads that still stand — a replaced road is drawn from its own line and must not hand
    # its year to the road built in its place
    fw_routes = None
    if standing:
        P, T, Y = [], [], []
        for _, g, _, _, y0, _, _ in standing:
            xy, _n = dense_coords([g], 40.0)
            if len(xy) < 2:
                continue
            tg = np.gradient(xy, axis=0)
            tg /= np.maximum(np.linalg.norm(tg, axis=1, keepdims=True), 1e-6)
            P.append(xy)
            T.append(tg)
            Y += [y0] * len(xy)
        fw_routes = (np.concatenate(P), np.concatenate(T), np.array(Y))

    def date_trunk(lines, names):
        """arterial streets classed trunk: the building rule, the researched street dates,
        the ground rule — as for the main roads"""
        m = shapely.line_interpolate_point(np.asarray(lines, dtype=object), 0.5, normalized=True)
        lo, la = to_ll(shapely.get_x(m), shapely.get_y(m))
        area = boro_of(shapely.points(lo, la), boros)
        y, s, ly_, _ = date_lines(lines, DEFAULT_MAIN, bld, neighbours=dated_tree, wide=~np.isin(area, list(BORO_NAME)))
        nm_ = np.array([str(n_).upper().strip() for n_ in names], dtype=object)
        y, s, fx = street_overrides(nm_, area, lo, la, y, s, quiet=True)
        return after_ground(y, ly_, fx, ("trunk road", nm_, lo, la, shapely.length(np.asarray(lines, dtype=object)))), s

    street_lines = [it[0] for k in ("manhattan", "region", "local") for it in sets[k] if len(it) == 6]
    write_paths3d(VIEWER_DATA / "freeways.bin.gz", freeway_items(ground, fw_routes, lm, date_trunk, street_lines, report, boros))
    gc = pd.DataFrame(GROUND_CONFLICTS, columns=["kind", "name", "year", "land_year", "lon", "lat", "m"])
    gc.to_csv(SCRATCH / "ground_conflicts.csv", index=False)
    report["ground_conflicts"] = {"segments": len(gc), "km": round(float(gc.m.sum()) / 1000, 1),
                                  "by_kind": {k: int(v) for k, v in gc.kind.value_counts().items()}}
    log(f"roads: {len(gc)} researched segments ({gc.m.sum() / 1000:.1f} km) stand on ground the land-year grid dates later "
        f"-> {SCRATCH / 'ground_conflicts.csv'}")
    report["seconds"] = round(time.time() - t0)
    (SCRATCH / "report.json").write_text(json.dumps(report, indent=1))
    log(f"roads: done in {report['seconds']} s; report -> {SCRATCH / 'report.json'}")


def local_tiles(items, decks, ground):
    """Residential streets, lanes and alleys of the Bronx, Brooklyn, Queens, Staten Island and
    the counties (and the counties' tertiary roads) in z12 tiles (viewer/public/data/
    region-streets/), and the same streets simplified to 8 m in z10 tiles for city scale."""
    out = VIEWER_DATA / "region-streets"
    if out.exists():
        shutil.rmtree(out)
    mid = shapely.line_interpolate_point(np.array([it[0] for it in items], dtype=object), 0.5, normalized=True)
    lon, lat = to_ll(shapely.get_x(mid), shapely.get_y(mid))
    dlon = np.array([it[0][len(it[0]) // 2] for it in decks])
    dlat = np.array([it[1][len(it[1]) // 2] for it in decks])
    result = {}
    for z, step, simp in ((LOCAL_Z, 30.0, None), (LOCAL_LOW_Z, 400.0, 8.0)):
        tx, ty = _tile(lon, lat, z)
        df = pd.DataFrame({"tx": tx, "ty": ty, "i": np.arange(len(items))})
        dt = _tile(dlon, dlat, z) if len(decks) else (np.array([]), np.array([]))
        index = []
        for (x, y), grp in df.groupby(["tx", "ty"]):
            its = [items[i] for i in grp.i.values]
            if simp:
                its = [(it[0].simplify(simp), K_STREET, WIDTH[K_STREET]) + it[3:] for it in its]
            its += [decks[j] for j in np.nonzero((dt[0] == x) & (dt[1] == y))[0]]
            p = out / str(z) / str(x) / f"{y}.bin.gz"
            p.parent.mkdir(parents=True, exist_ok=True)
            write_paths(p, its, ground, z_offset, step=step, step_outer=None if simp else STEP_OUTER)
            index.append({"x": int(x), "y": int(y), "n": len(its)})
        result[z] = index
    (out / "index.json").write_text(json.dumps({"z": LOCAL_Z, "tiles": result[LOCAL_Z],
                                                "low": {"z": LOCAL_LOW_Z, "tiles": result[LOCAL_LOW_Z]}}))
    log(f"roads: local streets: {len(items)} paths in {len(result[LOCAL_Z])} z{LOCAL_Z} tiles + "
        f"{len(result[LOCAL_LOW_Z])} z{LOCAL_LOW_Z} tiles -> {out}")
    return {"z12": len(result[LOCAL_Z]), "z10": len(result[LOCAL_LOW_Z])}


def check():
    """Invariants of the built files: no start >= end, years inside the slider, sizes,
    paths per decade."""
    files = [VIEWER_DATA / f for f in ("roads-sf.bin.gz", "roads-region.bin.gz", "freeways.bin.gz", "routes.bin.gz")]
    tiles = sorted((VIEWER_DATA / "region-streets").glob("*/*/*.bin.gz"))
    total = 0
    bad = 0
    groups = [(f.name, [f]) for f in files if f.exists()]
    for z in (LOCAL_Z, LOCAL_LOW_Z):
        groups.append((f"region-streets/{z}", [t for t in tiles if t.parts[-3] == str(z)]))
    for name, fs in groups:
        size = sum(f.stat().st_size for f in fs)
        total += size
        ys, n, nv, el = [], 0, 0, 0
        for f in fs:
            h, c = read_bayt(f)
            y = c["years"].reshape(-1, 2)
            ys.append(y)
            n += h["counts"]["paths"]
            nv += h["counts"]["vertices"]
            el += int((c["elevated"] == 2).sum())
            assert len(c["start_indices"]) == h["counts"]["paths"] + 1 and len(c["positions"]) == 3 * h["counts"]["vertices"]
            assert np.isfinite(c["positions"]).all()
        if not ys:
            continue
        y = np.vstack(ys)
        n_bad = int((y[:, 0] >= y[:, 1]).sum()) + int(((y[:, 0] < YEAR_MIN) | (y[:, 0] > CURRENT_YEAR + 1)).sum())
        bad += n_bad
        dec = pd.Series((y[:, 0] // 10 * 10).astype(int)).value_counts().sort_index()
        print(f"{name}: {len(fs)} file(s), {size / 1e6:.2f} MB, {n} paths, {nv} vertices, {el} elevated; "
              f"start {y[:, 0].min():.1f}..{y[:, 0].max():.1f}; start >= end or outside {YEAR_MIN}..{CURRENT_YEAR + 1}: {n_bad}")
        print("   by decade: " + " ".join(f"{d}:{c_}" for d, c_ in dec.items()))
    print(f"total {total / 1e6:.2f} MB; violations: {bad}")
    # nothing estimated before its ground (the tables of the last run: data/interim/roads/)
    sy = SCRATCH / "street_years.parquet"
    if sy.exists():
        t = pd.read_parquet(sy)
        if {"fixed", "bridge"} <= set(t.columns):
            held = ~t.fixed.values & ~t.bridge.values & np.isfinite(t.land_year.values) & (t.year.values < CURRENT_YEAR + 1.0)
            early = held & (t.year.values < t.land_year.values + 0.5 - 0.02)
            outside = ~np.isin(t.boro.values, list(BORO_NAME))
            print(f"streets on made land: {int(np.isfinite(t.land_year.values).sum())} ({int((np.isfinite(t.land_year.values) & outside).sum())} "
                  f"in the counties); estimated year before its ground: {int(early.sum())}; researched years before the grid's "
                  f"land year (kept, ground_conflicts.csv): {int((t.fixed.values & (t.year.values < t.land_year.values - 1.0)).sum())}")
            bad += int(early.sum())
    hy = SCRATCH / "highway_years.csv"
    if hy.exists():
        t = pd.read_csv(hy)
        if "land_year" in t.columns:
            early = (t.src.values != SRC_RESEARCHED) & ~t.bridge.values & (t.year.values < t.land_year.values + 0.5 - 0.02)
            print(f"highway mainline segments on made land: {int(t.land_year.notna().sum())}; estimated year before its ground: {int(early.sum())}")
            bad += int(early.sum())
    return bad


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        sys.exit(1 if check() else 0)
    main()
