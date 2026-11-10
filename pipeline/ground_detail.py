"""Stage: ground detail — the small real features a satellite view shows and the terrain
grid (38 m) can't: golf fairways, greens, tees and bunkers, sports pitches, running
tracks, playgrounds, plazas, gardens and lawns (OpenStreetMap outlines via Overture
base land_use), draped on the terrain. Plus labels for every dated park, cemetery and green
(one per name period where data/tables/park_names.csv gives a name history).

Dating (outlines are real; dates are researched for golf courses and listed parks, the
rest estimated):
  * golf features inside a golf course -> the course's opening year
                            (data/tables/golf_courses.csv, researched)
  * in a park (30 % of the feature or more) -> the park's researched year
                            (data/tables/parks.csv, `name` = the NYC Parks `signname`, or the
                            OpenStreetMap name of a park / cemetery that is not a city
                            property), else the year NYC Parks acquired the property
                            (parks_properties.geojson `acquisitiondate`).
                            Pitches, tracks and playgrounds not before 1903 (Seward Park, the
                            first municipal playground), dog runs not before 1990 (Tompkins
                            Square) — estimated era floors: a square of 1826 had no ball fields.
  * on an open airfield  -> the airfield's opening year (data/interim/airports.parquet)
  * in a stadium         -> pitches not before the largest building of the stadium ground
                            (OpenStreetMap `stadium` outline): Yankee Stadium's field 2009
  * otherwise            -> when the buildings that stand around it were built (2nd earliest
                            of the four nearest standing buildings within 60 m; widened to
                            150 m and 400 m where nothing stands that close), else 1950.
                            Vanished buildings are NOT counted here (in Manhattan they date
                            a tower plaza of 1970 by the row of 1850 it replaced: median plaza
                            1851 with them, 1974 without); instead:
  * always               -> not before a vanished building whose centroid lies inside the
                            outline came down, and not before its ground (made land: the
                            terrain land-year grids, read at run time; the latest year under
                            the outline and inner point of each drawn piece).

Outlines are simplified to 1 m, pieces under 20 m2 dropped, holes cut open (a running track
is a ring around its pitch), edges split at 25 m so the flat polygons follow the terrain.

The counties around the city (data/manual/extent_counties.json; `boro` = "9", `county` = name):
the same features and rules, with these differences —
  * no Parks Department: a park / reservation / cemetery is dated only by a researched row —
    data/tables/parks_counties.csv (another stage's table, parks.csv columns, by name; a row
    with lon / lat or a `county` column applies to that outline only) or
    data/tables/park_names.csv rows that carry a point (the outline of that name within
    1.5 km of the point; the park starts with its first listed name). No official acquisition
    dates are on disk for the counties, so that tier is empty there.
  * golf features of a course without a researched year: the whole course at once, at the
    median of what the buildings around its holes give (`golf_estimated`; a course does not
    appear hole by hole).
  * where nothing stands within 400 m the search widens to 1 km before the 1950 fallback.
  * to keep the file small, outlines there are simplified to 2 m and the smallest pieces
    dropped (COUNTY_MIN_AREA: lawns, gardens and plazas under 150 m2, the rest under 40 m2).
  * labels: researched greens (as the city's greens that are not city properties: no
    researched year, no label), golf courses with a researched year, and airfields
    (data/interim/airports.parquet; name periods from park_names.csv). A label that repeats a
    site of data/manual/sites/sites.geojson (drawn by another stage) is left out.
Building years come from nyc_building_points.parquet and county_building_points.parquet.
Everything keyed on the five boroughs (Parks properties, parks.csv, Manhattan's own file)
applies to the city only; city features and labels are the same as before the counties.

Outputs (BAYT: start_indices, positions f32[3] offsets from ORIGIN with z = ground + 0.3 m,
kind u8, years f32[2]):
  viewer/public/data/ground-detail.bin.gz          Manhattan (loaded at start)
  viewer/public/data/region-ground-detail.bin.gz   the Bronx, Brooklyn, Queens, Staten Island
                                                   and the counties
  viewer/public/data/park-labels.json              [{name, lon, lat, start, end?, ha, tier?}]
  data/interim/ground_detail/report.json           counts by class and by dating rule, per county
  data/interim/ground_detail/features.parquet      every feature: class, county, rule, year

Run after pipeline/airports.py (lawns on airfields) and after the terrain grids, the
buildings (nyc_building_points.parquet) and data/tables/parks.csv: re-run when any changes.
"""
from __future__ import annotations

import json
import time

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import box

from common import BORO_COUNTY, CURRENT_YEAR, INTERIM, MANUAL, NYC_CRS, OVERTURE_RELEASE, RAW, TABLES, VIEWER_DATA, YEAR_MIN, log
from export_columnar import write_columnar
from extent import in_extent, map_counties

UTM = NYC_CRS
# offsets in the binary files are degrees from here (the header carries it; the viewer reads it)
ORIGIN = (-73.97, 40.75)
MANHATTAN = "061"
COUNTY_BORO = "9"     # `boro` of the counties around the city (as county_building_points.parquet)
# outside the city (the file is loaded at start: see CLAUDE.md, the site must stay small)
COUNTY_SIMPLIFY_M = 2.0
COUNTY_MIN_AREA = {"grass": 150.0, "garden": 150.0, "flowerbed": 150.0, "pedestrian": 150.0, "plaza": 150.0,
                   "recreation_ground": 150.0, "village_green": 150.0}
COUNTY_MIN_AREA_DEFAULT = 40.0
COUNTY_RADIUS_M = 1000.0   # last search radius for the buildings around a feature
MATCH_M = 1500.0           # a table row's point belongs to the outline of its name this close
AIRPORT_LABELS_CITY = False   # JFK / LaGuardia had no label before the counties: unchanged

# kinds — keep in sync with viewer/src/layers/ground-detail.ts
KINDS = {"fairway": 0, "green": 1, "tee": 2, "rough": 3, "bunker": 4, "driving_range": 5, "pitch": 6, "track": 7,
         "playground": 8, "dog_park": 9, "pedestrian": 10, "plaza": 10, "garden": 11, "flowerbed": 11, "grass": 12,
         "recreation_ground": 12, "village_green": 12, "water_hazard": 14, "lateral_water_hazard": 14}
K_DIRT = 13
GOLF = {"fairway", "green", "tee", "rough", "bunker", "driving_range", "water_hazard", "lateral_water_hazard"}
PLAY = ["pitch", "track", "playground"]
# draw order (the viewer drapes these without depth writes: later draws on top) — lawns and
# plazas under fields, running tracks under the pitch they surround, fairways under tees and
# greens, bunkers and ponds last
DRAW_RANK = {12: 0, 11: 1, 10: 2, 3: 3, 0: 4, 5: 5, 13: 6, 7: 7, 6: 8, 8: 9, 9: 10, 2: 11, 1: 12, 14: 13, 4: 14}

MIN_AREA = 20.0       # m2: smaller pieces (planters, door-yard gardens) are dropped
SIMPLIFY_M = 1.0      # outline tolerance
SEG_M = 25.0          # longest edge, so flat polygons follow the terrain
PLAY_FLOOR = 1903.0   # Seward Park, first municipal playground (https://en.wikipedia.org/wiki/Seward_Park_(Manhattan))
DOG_FLOOR = 1990.0    # Tompkins Square dog run, the city's first (https://en.wikipedia.org/wiki/Tompkins_Square_Park)
RACETRACK_M2 = 30000  # an oval this big is a horse / motor track (dirt), not a running track
DEFAULT_YEAR = 1950.0
# Parks and cemeteries that are not city properties and have no researched year: the buildings
# around them date them badly (Calvary Cemetery of 1848 came out as 1947, a state park of
# 2007 as 1877), so they get no label until parks.csv or park_names.csv dates them.
ESTIMATE_OSM_LABELS = False
NOW = 2027.0
# Parks properties that are not parks to label
NO_LABEL_TYPES = {"Operations", "Lot", "Undeveloped", "Strip", "Managed Sites", "Buildings/Institutions"}
GENERIC_NAMES = {"park", "lot", "garden", "plaza", "triangle", "sitting area", "playground", "mall", "strip"}
# OpenStreetMap classes that can carry a park / cemetery / green label
# parks.csv name -> the OpenStreetMap name of the same ground, where they differ
OSM_ALIASES = {
    "Franklin D. Roosevelt Four Freedoms Park": "FDR Four Freedoms State Park",
    "St. Paul's Chapel Churchyard": "St. Paul's Churchyard",
    "The Evergreens Cemetery": "Cemetery of the Evergreens",
    "Trinity Church Cemetery and Mausoleum": "Trinity Cemetery",
    "First Shearith Israel Graveyard": "Chatham Square Cemetery",
}
GREEN_CLASSES = ["park", "cemetery", "grave_yard", "zoo", "nature_reserve", "state_park", "national_park", "garden",
                 "recreation_ground", "protected_landscape_seascape", "village_green"]
COUNTY_GREEN_CLASSES = GREEN_CLASSES + ["theme_park"]   # Playland


def norm(s):
    return " ".join(str(s).replace("’", "'").lower().split())


def to_utm():
    return Transformer.from_crs(4326, UTM, always_xy=True)


def to_ll():
    return Transformer.from_crs(UTM, 4326, always_xy=True)


_counties = None


def counties():
    """County outlines on the map (TIGER): the five boroughs (`boro` = the county code, as
    before the counties) and the counties around them (extent_counties.json: `boro` = "9"),
    each with its name (`county`)."""
    global _counties
    if _counties is None:
        co = gpd.read_file(f"zip://{RAW / 'tiger' / 'tl_2024_us_county.zip'}")
        fips = (co.STATEFP + co.COUNTYFP).values
        city = ((co.STATEFP == "36") & co.COUNTYFP.isin(list(BORO_COUNTY))).values
        around = map_counties()
        more = np.array([f in around for f in fips]) & ~city
        co = co.assign(boro=np.where(city, co.COUNTYFP.values, COUNTY_BORO),
                       county=[BORO_COUNTY[c] if ci else around.get(f, "") for c, f, ci in zip(co.COUNTYFP, fips, city)])
        _counties = co[city | more].to_crs(4326)[["boro", "county", "geometry"]].reset_index(drop=True)
    return _counties


def in_city(points):
    """Boolean mask: shapely points (EPSG:4326) inside the five boroughs."""
    c = counties()
    poly = shapely.union_all(c.geometry.values[c.boro.values != COUNTY_BORO])
    shapely.prepare(poly)
    return shapely.contains(poly, np.asarray(getattr(points, "values", points)))


def land_use():
    """OpenStreetMap land use polygons (Overture base/land_use) inside the five boroughs and
    the counties on the map, with the county code of each (`boro`; "9" outside the city),
    the county's name (`county`) and `city` (inside the five boroughs)."""
    lu = pd.read_parquet(RAW / "overture" / OVERTURE_RELEASE / "base_land_use.parquet")
    lu = gpd.GeoDataFrame(lu, geometry=gpd.GeoSeries.from_wkb(lu.geometry), crs=4326)
    rp = lu.geometry.representative_point()
    keep = in_extent(rp)
    lu, rp = lu[keep], rp[keep]
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=rp, crs=4326), counties(), predicate="within", how="left")
    j = j[~j.index.duplicated()]
    lu["boro"] = j.boro.reindex(lu.index).values
    lu["county"] = j.county.reindex(lu.index).values
    # outside the counties of the map nothing can date a feature (no building years): left out
    lu = lu[lu.boro.notna()].reset_index(drop=True)
    lu["city"] = (lu.boro != COUNTY_BORO).values
    return lu


def researched_parks():
    """data/tables/parks.csv (another stage's table, read only): {normalised name: (start, end)}."""
    p = TABLES / "parks.csv"
    if not p.exists():
        return {}
    t = pd.read_csv(p)
    y0 = pd.to_numeric(t.start_year, errors="coerce")
    y1 = pd.to_numeric(t.end_year, errors="coerce").fillna(9999.0)
    return {norm(n): (float(a), float(b)) for n, a, b in zip(t.name, y0, y1) if np.isfinite(a)}


def county_researched(lu):
    """Researched years of the counties' greens (see the module docstring): {row label of lu:
    {"year", "end", "rows" (name periods of park_names.csv, may be empty), "src"}}, and the
    table names that matched no outline."""
    g = lu[~lu.city & lu["class"].isin(COUNTY_GREEN_CLASSES) & lu["name"].notna()]
    if not len(g):
        return {}, []
    gu = g.to_crs(UTM)
    key = g["name"].map(norm).values
    area = gu.geometry.area.values
    rows_of = {}
    for i, k in enumerate(key):
        rows_of.setdefault(k, []).append(i)
    geom = gu.geometry.values
    tr = to_utm()
    out, missing = {}, []
    p = TABLES / "parks_counties.csv"
    if p.exists():
        t = pd.read_csv(p)
        y0 = pd.to_numeric(t.start_year, errors="coerce")
        y1 = pd.to_numeric(t.end_year, errors="coerce").fillna(9999.0)
        lon = pd.to_numeric(t["lon"], errors="coerce") if "lon" in t else pd.Series(np.nan, index=t.index)
        lat = pd.to_numeric(t["lat"], errors="coerce") if "lat" in t else pd.Series(np.nan, index=t.index)
        cty = t["county"].astype(str) if "county" in t else pd.Series("", index=t.index)
        for nm, a, b, x, y, c in zip(t.name, y0, y1, lon, lat, cty):
            if not np.isfinite(a) or b < 9999:
                continue
            cand = np.array(rows_of.get(norm(nm), rows_of.get(norm(OSM_ALIASES.get(str(nm), nm)), [])), dtype=int)
            if len(cand) and np.isfinite(x) and np.isfinite(y):
                pt = shapely.Point(*tr.transform(x, y))
                cand = cand[shapely.distance(geom[cand], pt) <= MATCH_M]
            elif len(cand) and c.strip() and c != "nan":
                cc = norm(c).replace(" county", "")
                cand = cand[np.array([norm(v) == cc for v in g.county.values[cand]])]
            elif len(cand):
                big = cand[np.argmax(area[cand])]
                cand = cand[shapely.distance(geom[cand], geom[big]) <= 3000.0]
            if not len(cand):
                missing.append(str(nm))
                continue
            for i in cand:
                out[g.index[i]] = {"year": float(a), "end": float(b), "rows": [], "src": "parks_counties"}
    hist, _ = park_name_periods()
    for k, periods in hist.items():
        cand = rows_of.get(k)
        pts = [(r, shapely.Point(*tr.transform(r[3], r[4]))) for r in periods if np.isfinite(r[3]) and np.isfinite(r[4])]
        if not cand or not pts:
            continue
        for i in cand:
            rows = [r for r, pt in pts if geom[i].distance(pt) <= MATCH_M]
            if not rows:
                continue
            end = max(r[2] for r in rows)
            prev = out.get(g.index[i])
            if prev is not None:
                prev["rows"] = rows
            elif end >= 9999:
                out[g.index[i]] = {"year": min(r[1] for r in rows), "end": 9999.0, "rows": rows, "src": "park_names"}
    return out, missing


def load_parks(lu):
    """Dated green outlines: NYC Parks properties (researched year, else acquisition year)
    plus OpenStreetMap parks / cemeteries / gardens named in parks.csv that are not city
    properties (Green-Wood Cemetery, Gramercy Park, Hudson River Park...).
    Columns: name, year, end, dated ('researched' | 'acquired' | ''), kind, city, geometry."""
    res = researched_parks()
    pk = gpd.read_file(RAW / "nyc" / "parks_properties.geojson")
    pk = pk[pk.geometry.notna() & ~pk.geometry.is_empty].copy()
    pk["name"] = pk.signname.fillna("").str.strip()
    key = pk.name.map(norm)
    acq = pd.to_datetime(pk.acquisitiondate, errors="coerce").dt.year.astype(float)
    acq = acq.where((acq >= YEAR_MIN) & (acq <= NOW))
    # a park that ended (St. John's Park, 1803-1867) is not today's property of the same name
    live = {k: v for k, v in res.items() if v[1] >= 9999}
    ry = key.map(lambda k: live.get(k, (np.nan, 9999.0))[0])
    pk["year"] = ry.where(ry.notna(), acq)
    pk["end"] = 9999.0
    pk["dated"] = np.where(ry.notna(), "researched", np.where(acq.notna(), "acquired", ""))
    pk["kind"] = pk.typecategory.fillna("")
    pk["city"] = True
    out = [pk[["name", "year", "end", "dated", "kind", "city", "geometry"]]]
    have = set(key[ry.notna()])
    rest = {k for k in live if k not in have}
    alias = {norm(v): k for k, v in OSM_ALIASES.items() if norm(k) in rest}   # OSM name -> parks.csv name
    g = lu[lu.city & lu["class"].isin(GREEN_CLASSES) & lu["name"].notna()].copy()
    g["name"] = g["name"].map(lambda n: alias.get(norm(n), n))
    g = g[g["name"].map(norm).isin(rest)].copy()
    if len(g):
        k2 = g["name"].map(norm)
        g["year"] = k2.map(lambda k: live[k][0])
        g["end"] = 9999.0
        g["dated"] = "researched"
        g["kind"] = g["class"]
        g["city"] = False
        g["name"] = g["name"].str.strip()
        out.append(g[["name", "year", "end", "dated", "kind", "city", "geometry"]])
        rest -= set(k2)
    if rest:
        log(f"ground detail: parks.csv names with no outline in the Parks dataset or OpenStreetMap: {sorted(rest)}")
    # the counties: OpenStreetMap greens with a researched year
    cres, missing = county_researched(lu)
    if cres:
        gc = lu.loc[list(cres)].copy()
        gc["year"] = [cres[i]["year"] for i in gc.index]
        gc["end"] = 9999.0
        gc["dated"] = "researched"
        gc["kind"] = gc["class"]
        gc["city"] = False
        gc["name"] = gc["name"].str.strip()
        out.append(gc[["name", "year", "end", "dated", "kind", "city", "geometry"]])
    log(f"ground detail: {len(cres)} green outlines of the counties with a researched year "
        f"({sum(1 for v in cres.values() if v['src'] == 'parks_counties')} by parks_counties.csv, "
        f"{sum(1 for v in cres.values() if v['src'] == 'park_names')} by park_names.csv)"
        + (f"; parks_counties.csv names with no OpenStreetMap outline: {sorted(set(missing))}" if missing else ""))
    parks = gpd.GeoDataFrame(pd.concat(out, ignore_index=True), geometry="geometry", crs=4326)
    parks["area_m2"] = parks.to_crs(UTM).geometry.area.values
    parks.attrs["county_researched"] = cres
    parks.attrs["county_missing"] = sorted(set(missing))
    return parks


def building_points():
    """Building centroids with their years (nyc_building_points.parquet, vanished ones
    included, and county_building_points.parquet where the counties were built). The files
    are rewritten by the buildings stages: retry while one is being replaced."""
    parts = []
    for p in (INTERIM / "nyc_building_points.parquet", INTERIM / "county_building_points.parquet"):
        if not p.exists() and p.name.startswith("county"):
            log("ground detail: no county_building_points.parquet — the counties are dated without buildings")
            continue
        for attempt in range(12):
            try:
                parts.append(pd.read_parquet(p, columns=["lon", "lat", "start_year", "end_year", "area_m2"]))
                break
            except Exception as e:  # noqa: BLE001 — half-written file
                log(f"ground detail: building points not readable ({e!r}), waiting")
                time.sleep(30)
        else:
            raise RuntimeError(f"cannot read {p}")
    b = pd.concat(parts, ignore_index=True) if len(parts) > 1 else parts[0]
    b = b[b.start_year.notna() & (b.start_year >= YEAR_MIN)]
    x, y = to_utm().transform(b.lon.values, b.lat.values)
    return (np.column_stack([x, y]), b.start_year.values.astype(float), b.end_year.fillna(9999.0).values.astype(float),
            b.area_m2.fillna(0.0).values.astype(float))


class Neighbourhood:
    """When the buildings around a point were built."""

    def __init__(self):
        self.xy, self.y0, self.y1, self.area = building_points()
        # the buildings that stand today date what lies between them today; the vanished
        # ones (62,000 in Manhattan) would date a 1970 tower plaza by the 1850 row it replaced
        self.standing = np.flatnonzero(self.y1 >= 9999)
        self.tree = cKDTree(self.xy[self.standing])

    def second_earliest(self, xy, radii=(60.0, 150.0, 400.0), k=4):
        """2nd earliest of the k nearest standing buildings within r (the only one if just one),
        trying each radius in turn; NaN where nothing stands within the last."""
        out = np.full(len(xy), np.nan)
        for r in radii:
            todo = np.flatnonzero(np.isnan(out))
            if not len(todo):
                break
            d, idx = self.tree.query(xy[todo], k=k, distance_upper_bound=r)
            ny = np.where(np.isfinite(d), self.y0[self.standing[np.minimum(idx, len(self.standing) - 1)]], np.inf)
            ny.sort(axis=1)
            v = np.where(np.isfinite(ny[:, 1]), ny[:, 1], ny[:, 0])
            out[todo] = np.where(np.isfinite(v), v, np.nan)
        return out

    def biggest_inside(self, polys_utm, min_area=2000.0):
        """Start year of the largest standing building (min_area m2 or more) whose centroid
        lies inside each polygon, NaN if none: a stadium's stands date its field."""
        m = self.standing[self.area[self.standing] >= min_area]
        out = np.full(len(polys_utm), np.nan)
        if not len(m) or not len(polys_utm):
            return out
        pts = gpd.GeoDataFrame({"y0": self.y0[m], "a": self.area[m]}, geometry=gpd.points_from_xy(self.xy[m, 0], self.xy[m, 1]), crs=UTM)
        j = gpd.sjoin(pts, gpd.GeoDataFrame(geometry=np.asarray(polys_utm), crs=UTM), predicate="within", how="inner")
        j = j.sort_values("a", ascending=False).groupby("index_right").first()
        out[j.index.values] = j.y0.values
        return out

    def vanished_inside(self, polys_utm):
        """Latest end year of the vanished buildings whose centroid lies inside each polygon
        (NaN if none): the ground feature there today cannot be older."""
        gone = self.y1 < 9999
        out = np.full(len(polys_utm), np.nan)
        if not gone.any():
            return out
        pts = gpd.GeoDataFrame({"end": self.y1[gone]}, geometry=gpd.points_from_xy(self.xy[gone, 0], self.xy[gone, 1]), crs=UTM)
        j = gpd.sjoin(pts, gpd.GeoDataFrame(geometry=np.asarray(polys_utm), crs=UTM), predicate="within", how="inner")
        m = j.groupby("index_right").end.max()
        out[m.index.values] = m.values
        return out


def land_year_of(polys_ll, q=0.8):
    """Year the ground under each polygon became land (terrain land-year grids; NaN = always
    land): the q-quantile over its representative point and up to 16 outline vertices, so a
    pitch mostly on a fill waits for the fill and one stray cell does not hold back a lawn."""
    from airports import land_year
    polys_ll = np.array([max(g.geoms, key=lambda p: p.area) if g.geom_type == "MultiPolygon" else g for g in polys_ll], dtype=object)
    xy, idx = shapely.get_coordinates(shapely.get_exterior_ring(polys_ll), return_index=True)
    first = np.flatnonzero(np.r_[True, idx[1:] != idx[:-1]])
    n = np.diff(np.r_[first, len(idx)])
    rp = shapely.get_coordinates(shapely.point_on_surface(polys_ll))
    ly_rp = land_year(rp[:, 0], rp[:, 1])
    ly_v = land_year(xy[:, 0], xy[:, 1])
    out = np.full(len(polys_ll), np.nan)
    any_fill = np.flatnonzero(np.maximum.reduceat(np.isfinite(ly_v).astype(int), first) + np.isfinite(ly_rp))
    for i in any_fill:
        v = ly_v[first[i]: first[i] + n[i] - 1]
        if len(v) > 16:
            v = v[np.linspace(0, len(v) - 1, 16).astype(int)]
        v = np.r_[ly_rp[i], v]
        v = np.where(np.isfinite(v), v, -1e4)
        y = np.quantile(v, q, method="higher")
        out[i] = y if y > 0 else np.nan
    return out


def cut_holes(poly, depth=0):
    """A polygon with holes as hole-free pieces (the binary format carries simple rings):
    cut by a vertical line through each hole. Slivers of holes are simply dropped."""
    if poly.is_empty or poly.geom_type != "Polygon":
        return [g for p in getattr(poly, "geoms", []) for g in cut_holes(p, depth)]
    holes = [h for h in poly.interiors if shapely.Polygon(h).area >= 25.0]
    if not holes or depth > 12:
        return [shapely.Polygon(poly.exterior)]
    if len(holes) < len(poly.interiors):
        poly = shapely.Polygon(poly.exterior, holes)
    x = shapely.Polygon(holes[0]).representative_point().x
    x0, y0, x1, y1 = poly.bounds
    out = []
    for half in (box(x0 - 1, y0 - 1, x, y1 + 1), box(x, y0 - 1, x1 + 1, y1 + 1)):
        out += cut_holes(poly.intersection(half), depth + 1)
    return out


def write_outlines(path, polys_utm, kinds, years, ends, ground, z_extra=0.3):
    """Rings of hole-free UTM polygons -> BAYT file in drawing order."""
    polys_utm = np.asarray(polys_utm, dtype=object)
    kinds = np.asarray(kinds)
    area = shapely.area(polys_utm)
    rank = np.array([DRAW_RANK.get(int(k), 8) for k in kinds])
    order = np.lexsort((-area, rank))
    polys_utm, kinds = polys_utm[order], kinds[order]
    years, ends = np.asarray(years, float)[order], np.asarray(ends, float)[order]
    xy, idx = shapely.get_coordinates(shapely.get_exterior_ring(polys_utm), return_index=True)
    lon, lat = to_ll().transform(xy[:, 0], xy[:, 1])
    z = ground(lon, lat) + z_extra
    n = np.bincount(idx, minlength=len(polys_utm))
    starts = np.r_[0, np.cumsum(n)]
    write_columnar(path, {
        "start_indices|shuffle": starts.astype(np.uint32),
        "positions|shuffle": np.column_stack([lon - ORIGIN[0], lat - ORIGIN[1], z]).astype(np.float32).ravel(),
        "kind": kinds.astype(np.uint8),
        "years": np.column_stack([years, ends]).astype(np.float32).ravel(),
    }, origin=ORIGIN, counts={"polygons": int(len(kinds)), "vertices": int(starts[-1])})
    return int(len(kinds)), int(starts[-1])


def golf_courses(lu):
    """Golf course outlines with their researched years (data/tables/golf_courses.csv: `name`
    = the OpenStreetMap name; lon / lat = a point inside the course, which also dates the
    unnamed duplicate outlines and tells two courses in one outline apart — a feature takes
    the year of the nearest row of its course). Returns (courses gdf in UTM with `rows` =
    list of (x, y, open, close)), table."""
    courses = lu[lu["class"] == "golf_course"].copy().to_crs(UTM)
    p = TABLES / "golf_courses.csv"
    t = pd.read_csv(p) if p.exists() else pd.DataFrame(columns=["name", "year_open", "year_close", "lon", "lat"])
    t["year_open"] = pd.to_numeric(t.year_open, errors="coerce")
    t["year_close"] = pd.to_numeric(t.year_close, errors="coerce").fillna(9999.0)
    t = t[t.year_open.notna()]
    tx, ty = to_utm().transform(pd.to_numeric(t.lon, errors="coerce").values, pd.to_numeric(t.lat, errors="coerce").values)
    rows_of = []
    for nm, geom in zip(courses["name"], courses.geometry.values):
        rows = []
        for r, x, y in zip(t.itertuples(), tx, ty):
            by_name = isinstance(nm, str) and norm(nm) == norm(r.name)
            inside = np.isfinite(x) and geom.contains(shapely.Point(x, y))
            if (by_name and (not np.isfinite(x) or geom.distance(shapely.Point(x, y)) < 1500)) or inside:
                rows.append((x, y, float(r.year_open), float(r.year_close)))
        rows_of.append(rows)
    courses["rows"] = rows_of
    missing = sorted({str(n) for n, r in zip(courses["name"], rows_of) if not r})
    if missing:
        log(f"ground detail: golf courses without a researched year: {missing}")
    return courses, t


def date_features(feats, fu, parks, courses, hood, stadiums=None):
    """Start / end year and the rule that gave it, for every feature."""
    n = len(feats)
    cls = feats["class"].values
    rp_u = fu.geometry.representative_point()
    pxy = np.column_stack([rp_u.x.values, rp_u.y.values])
    pts_u = gpd.GeoDataFrame(geometry=rp_u.values, crs=UTM)
    year = np.full(n, np.nan)
    end = np.full(n, 9999.0)
    rule = np.full(n, "", dtype=object)
    # golf features: their course (nearest researched row of that course)
    is_golf = np.isin(cls, list(GOLF))
    j = gpd.sjoin(pts_u[is_golf], courses[["rows", "geometry"]], predicate="within", how="inner")
    for i, rows in zip(j.index.values, j.rows.values):
        if not rows or np.isfinite(year[i]):
            continue
        d = [np.hypot(pxy[i, 0] - x, pxy[i, 1] - y) if np.isfinite(x) else 1e9 for x, y, _, _ in rows]
        _, _, y0, y1 = rows[int(np.argmin(d))]
        year[i], end[i], rule[i] = y0, y1, "golf"
    # inside a dated park (the smallest property that contains the point)
    sf_names, _ = park_name_periods()
    play_y = {}
    for pk, periods in sf_names.items():
        ys = [y0 for nm, y0, _y1, _x, _y in periods if any(w in nm.lower() for w in ("playground", "recreation", "field", "athletic"))]
        if ys:
            play_y[norm(pk)] = min(ys)
    # (a feature belongs to a park that covers 30 % of it or more; of several, the smallest)
    pp = parks[parks.year.notna()].to_crs(UTM).reset_index(drop=True)
    jp = gpd.sjoin(fu[["geometry"]], pp[["name", "year", "dated", "area_m2", "geometry"]], predicate="intersects", how="inner")
    fg = fu.geometry.values[jp.index.values]
    share = shapely.area(shapely.intersection(fg, pp.geometry.values[jp.index_right.values])) / np.maximum(shapely.area(fg), 1e-6)
    jp = jp[share >= 0.3].sort_values("area_m2").groupby(level=0).first()
    ip = jp.index.values
    todo = np.isnan(year[ip])
    ip, jp = ip[todo], jp[todo]
    py = jp.year.values.astype(float)
    kind_floor = np.select([np.isin(cls[ip], PLAY), cls[ip] == "dog_park"], [PLAY_FLOOR, DOG_FLOOR], -np.inf)
    named_play = jp.name.map(lambda s: play_y.get(norm(s), np.nan)).values.astype(float)
    kind_floor = np.where(np.isfinite(named_play) & np.isin(cls[ip], PLAY), np.maximum(named_play, 1898.0), kind_floor)
    year[ip] = np.maximum(py, kind_floor)
    rule[ip] = np.where(jp.dated.values == "researched", "park_researched", "park_acquired")
    floored = int((kind_floor > py).sum())
    # on an airfield (pipeline/airports.py, run first): lawns between the runways
    ap = INTERIM / "airports.parquet"
    if ap.exists():
        a = gpd.read_parquet(ap).to_crs(UTM)
        a = a[a.closed >= 9999]   # a closed field (Floyd Bennett) is a park now: its pitches are not the airfield's
        ja = gpd.sjoin(pts_u[np.isnan(year)], a[["opened", "closed", "geometry"]], predicate="within", how="inner")
        ja = ja[~ja.index.duplicated()]
        year[ja.index.values], rule[ja.index.values] = ja.opened.values, "airfield"
    # otherwise: when the buildings around it were built
    todo = np.flatnonzero(np.isnan(year))
    nb = hood.second_earliest(pxy[todo])
    year[todo] = np.where(np.isfinite(nb), nb, DEFAULT_YEAR)
    rule[todo] = np.where(np.isfinite(nb), "buildings", "default")
    # the field of a stadium (OpenStreetMap stadium grounds) is no older than its stands:
    # Yankee Stadium's diamond of 2009 lies in a park of 1897
    n_stadium = 0
    if stadiums is not None and len(stadiums):
        sy = hood.biggest_inside(stadiums.geometry.values)
        st = stadiums[np.isfinite(sy)].assign(sy=sy[np.isfinite(sy)])
        if len(st):
            js = gpd.sjoin(pts_u[np.isin(cls, ["pitch", "track", "grass"])], st[["sy", "geometry"]], predicate="within", how="inner")
            js = js.groupby(level=0).sy.max()
            later = js.values > year[js.index.values]
            year[js.index.values[later]] = js.values[later]
            rule[js.index.values[later]] = "stadium"
            n_stadium = int(later.sum())
    # never before a vanished building on the spot came down, never before its ground
    gone = hood.vanished_inside(fu.geometry.values)
    late = np.isfinite(gone) & (gone > year)
    year = np.where(late, gone, year)
    year = np.clip(year, YEAR_MIN, float(CURRENT_YEAR))   # mapped today: there by today
    stats = {"era_floor_applied": floored, "after_vanished_building": int(late.sum()), "stadium_fields": n_stadium}
    return year, end, rule, stats


def park_name_periods():
    """Name histories (data/tables/park_names.csv): one row per name a park went by.
    `park` is the park's key — the NYC Parks `signname`, or the OpenStreetMap name of a park /
    cemetery that is not a city property; `name` is the label for [from_year, to_year). Rows
    with lon / lat apply only to the park of that name within ~1 km of the point (names
    repeat between boroughs). A park listed here is labelled only for its listed periods (a
    gap = no known name, no label). Returns ({norm park: [(name, y0, y1, lon, lat)]}, table)."""
    p = TABLES / "park_names.csv"
    if not p.exists():
        return {}, None
    t = pd.read_csv(p)
    t["from_year"] = pd.to_numeric(t.from_year, errors="coerce")
    t["to_year"] = pd.to_numeric(t.to_year, errors="coerce").fillna(9999.0)
    t = t[t.from_year.notna() & t.name.notna() & t.park.notna()]
    lon = pd.to_numeric(t.get("lon"), errors="coerce")
    lat = pd.to_numeric(t.get("lat"), errors="coerce")
    out = {}
    for r, x, y in zip(t.itertuples(), lon, lat):
        out.setdefault(norm(r.park), []).append((str(r.name).strip(), float(r.from_year), float(r.to_year), float(x), float(y)))
    for v in out.values():
        v.sort(key=lambda a: a[1])
    return out, t


def periods_for(hist, name, lon, lat):
    rows = [r for r in hist.get(norm(name), ())
            if not np.isfinite(r[3]) or (abs(r[3] - lon) < 0.012 and abs(r[4] - lat) < 0.01)]
    return rows


def park_labels(parks, lu, courses, hood):
    """One label per park / cemetery / green and name period:
      1. NYC Parks properties (several properties of one name within 2 km are one label)
         from the researched year, else the acquisition year (cemeteries the city took over
         in 2003 are not dated by that transfer: researched or no label);
      2. OpenStreetMap parks, cemeteries, zoos and gardens that are not city properties:
         researched year (parks.csv by name, park_names.csv by name and point), else no
         label (ESTIMATE_OSM_LABELS would date them by the buildings around: unreliable);
      3. golf courses from their opening year;
      4. park_names.csv rows with lon / lat that match no outline (vanished parks)."""
    hist, _ = park_name_periods()
    used_hist = set()
    labels = []
    stats = {"city_researched": 0, "city_acquired": 0, "osm_researched": 0, "osm_estimated": 0, "golf": 0,
             "name_history": 0, "vanished": 0}
    early = []

    def emit(name, c, y0, y1, ha, researched, tier=None):
        """Append the label(s) of one park; True if any."""
        rows = periods_for(hist, name, c.x, c.y)
        n0 = len(labels)
        if rows:
            used_hist.add(norm(name))
            stats["name_history"] += 1
            if not researched and np.isfinite(y0) and rows[0][1] < y0:
                early.append(f"{name} (names from {rows[0][1]:.0f}, park dated {y0:.0f})")
            for nm, a, b, _x, _y in rows:
                s = max(a, y0) if (researched and np.isfinite(y0)) else a
                e = b
                if s < e:
                    lab = {"name": nm, "lon": round(c.x, 6), "lat": round(c.y, 6), "start": s, "ha": round(ha, 2)}
                    if e < 9999:
                        lab["end"] = e
                    if tier:
                        lab["tier"] = tier
                    labels.append(lab)
        elif np.isfinite(y0) and y0 < y1:
            lab = {"name": name, "lon": round(c.x, 6), "lat": round(c.y, 6), "start": float(y0), "ha": round(ha, 2)}
            if y1 < 9999:
                lab["end"] = float(y1)
            if tier:
                lab["tier"] = tier
            labels.append(lab)
        return len(labels) > n0

    # 1. city properties, biggest first; same name within 2 km = one park
    city = parks[parks.city & ~parks.kind.isin(NO_LABEL_TYPES)].copy()
    city = city[(city.name.str.len() >= 3) & ~city.name.map(norm).isin(GENERIC_NAMES)]
    city.loc[(city.kind == "Cemetery") & (city.dated == "acquired"), "year"] = np.nan
    # parkway strips are labelled by the road; only the researched ones (Eastern Parkway) here
    city = city[(city.kind != "Parkway") | (city.dated == "researched")]
    cu = city.to_crs(UTM)
    biggest = [max(getattr(g, "geoms", [g]), key=lambda p: p.area).representative_point() for g in cu.geometry.values]
    bx = np.array([p.x for p in biggest]); by = np.array([p.y for p in biggest])
    lon, lat = to_ll().transform(bx, by)
    groups = {}
    for i in np.argsort(-city.area_m2.values):
        k = norm(city.name.values[i])
        for g in groups.setdefault(k, []):
            if np.hypot(bx[i] - g["x"], by[i] - g["y"]) < 2000:
                g["ha"] += city.area_m2.values[i] / 1e4
                if np.isfinite(city.year.values[i]):
                    g["y0"] = np.nanmin([g["y0"], city.year.values[i]])
                    g["res"] = g["res"] or city.dated.values[i] == "researched"
                break
        else:
            groups[k].append({"name": city.name.values[i], "x": bx[i], "y": by[i], "c": shapely.Point(lon[i], lat[i]),
                              "ha": city.area_m2.values[i] / 1e4, "y0": city.year.values[i], "y1": city.end.values[i],
                              "res": city.dated.values[i] == "researched"})
    for gs in groups.values():
        for g in gs:
            if emit(g["name"], g["c"], g["y0"], g["y1"], g["ha"], g["res"]):
                stats["city_researched" if g["res"] else "city_acquired"] += 1
    # 2. OpenStreetMap greens that are not city properties
    osm = lu[lu["class"].isin(GREEN_CLASSES) & lu["name"].notna()].copy()
    res = researched_parks()
    alias = {norm(v): k for k, v in OSM_ALIASES.items() if norm(k) in res}
    osm["name"] = osm["name"].map(lambda n: alias.get(norm(n), n))
    osm = osm[osm["name"].astype(str).str.len().between(3, 44)]
    ou = osm.to_crs(UTM)
    ha = ou.geometry.area.values / 1e4
    rp = ou.geometry.representative_point()
    in_city = gpd.sjoin(gpd.GeoDataFrame(geometry=rp.values, crs=UTM), parks[parks.city].to_crs(UTM)[["geometry"]],
                        predicate="within", how="left")
    in_city = in_city[~in_city.index.duplicated()].index_right.notna().values
    rl = rp.to_crs(4326)
    est = hood.second_earliest(np.column_stack([rp.x.values, rp.y.values]), radii=(150.0,))
    ly = land_year_of(osm.geometry.values)
    seen = {}
    for lab in labels:
        seen.setdefault(norm(lab["name"]), []).append((lab["lon"], lab["lat"]))
    for gs in groups.values():
        for g in gs:
            seen.setdefault(norm(g["name"]), []).append((g["c"].x, g["c"].y))
    estimated = []
    for i in np.argsort(-ha):
        nm, c = str(osm["name"].values[i]).strip(), rl.values[i]
        k = norm(nm)
        if any(abs(c.x - x) < 0.02 and abs(c.y - y) < 0.02 for x, y in seen.get(k, ())):
            continue
        cls = osm["class"].values[i]
        has_hist = bool(periods_for(hist, nm, c.x, c.y))
        if k in res:
            y0, y1, researched = res[k][0], res[k][1], True
        elif has_hist:
            y0, y1, researched = np.nan, 9999.0, False
        elif (not ESTIMATE_OSM_LABELS or in_city[i] or ha[i] < 1.0 or cls in ("garden", "recreation_ground", "village_green")
              or not np.isfinite(est[i])):
            continue
        else:
            y0, y1, researched = est[i], 9999.0, False
            if np.isfinite(ly[i]):
                y0 = max(y0, ly[i] + 0.5)
        if in_city[i] and not (cls in ("cemetery", "grave_yard") or has_hist):
            continue   # the city property carries the label
        if emit(nm, c, y0, y1, float(ha[i]), researched):
            seen.setdefault(k, []).append((c.x, c.y))
            stats["osm_researched" if (researched or has_hist) else "osm_estimated"] += 1
            if not (researched or has_hist):
                estimated.append(f"{nm} [{cls}] {y0:.0f}")
    # 3. golf courses
    cl = courses.to_crs(4326)
    for nm, gu, gl, rows in zip(courses["name"], courses.geometry.values, cl.geometry.values, courses.rows):
        if not isinstance(nm, str) or not rows:
            continue
        c = gl.representative_point()
        if emit(nm.strip(), c, min(r[2] for r in rows), max(r[3] for r in rows), gu.area / 1e4, True):
            stats["golf"] += 1
    # 4. name-history rows with a point that matched no outline: vanished parks
    for k, rows in hist.items():
        if k in used_hist:
            continue
        for nm, a, b, x, y in rows:
            if np.isfinite(x) and np.isfinite(y) and a < b and in_extent(np.array([shapely.Point(x, y)]))[0]:
                lab = {"name": nm, "lon": round(x, 6), "lat": round(y, 6), "start": a, "ha": 1.0}
                if b < 9999:
                    lab["end"] = b
                labels.append(lab)
                stats["vanished"] += 1
    if early:
        log("ground detail: name histories that start before the park's acquisition date "
            f"(add the park to parks.csv to move its ground too): {early}")
    stats["estimated_list"] = estimated
    return labels, stats


def site_labels():
    """Names of large vanished / industrial sites, over the years they stood, if another
    stage has traced any (data/manual/{industrial,vanished}_sites/sites.geojson)."""
    out = []
    for f in (MANUAL / "industrial_sites" / "sites.geojson", MANUAL / "vanished_sites" / "sites.geojson"):
        if not f.exists():
            continue
        st = gpd.read_file(f).to_crs(4326)
        for _site_id, grp in st.groupby("site_id"):
            nm = next((str(v) for c in ("name_label", "name") if c in grp for v in grp[c] if isinstance(v, str) and v.strip()), None)
            if not nm or len(nm) > 40:
                continue
            y0 = pd.to_numeric(grp["label_start"] if "label_start" in grp else grp["year_start"], errors="coerce").min()
            y1 = pd.to_numeric(grp["label_end"] if "label_end" in grp else grp["year_end"], errors="coerce").max()
            geom = grp.geometry.union_all()
            if not np.isfinite(y0) or geom is None or geom.is_empty:
                continue
            c = geom.representative_point()
            if not in_extent(np.array([c]))[0]:
                continue
            ha = float(gpd.GeoSeries([geom], crs=4326).to_crs(UTM).area.iloc[0]) / 1e4
            out.append({"name": nm, "lon": round(c.x, 6), "lat": round(c.y, 6), "start": float(y0),
                        "end": float(y1) if np.isfinite(y1) else 9999.0, "ha": round(ha, 2), "tier": "site"})
    return out


def main():
    from nyc_buildings import Ground
    lu = land_use()
    parks = load_parks(lu)
    courses, _ = golf_courses(lu)
    hood = Neighbourhood()
    feats = lu[lu["class"].isin(KINDS)].explode(index_parts=False)
    feats = feats[feats.geometry.geom_type == "Polygon"].reset_index(drop=True)
    fu = feats.to_crs(UTM)
    keep = fu.geometry.area.values >= MIN_AREA
    feats, fu = feats[keep].reset_index(drop=True), fu[keep].reset_index(drop=True)
    stadiums = lu[lu["class"] == "stadium"].to_crs(UTM)
    year, end, rule, stats = date_features(feats, fu, parks, courses, hood, stadiums)

    # outlines: simplified, holes cut, long edges split so they follow the terrain
    kind0 = feats["class"].map(KINDS).values
    geoms = shapely.make_valid(shapely.simplify(fu.geometry.values, SIMPLIFY_M, preserve_topology=True))
    polys, src = [], []
    for i, g in enumerate(geoms):
        for p in cut_holes(g):
            if p.area >= MIN_AREA / 2 and p.exterior.length >= 8:
                polys.append(p)
                src.append(i)
    src = np.asarray(src)
    polys = shapely.segmentize(np.asarray(polys, dtype=object), SEG_M)
    kinds = kind0[src].copy()
    # the big ovals (Aqueduct's racetrack) are dirt, not a red synthetic running track
    filled = np.array([shapely.Polygon(g.exterior).area if g.geom_type == "Polygon" else g.area for g in geoms])
    big_oval = (kinds == KINDS["track"]) & (filled[src] > RACETRACK_M2)
    kinds[big_oval] = K_DIRT
    # never before its ground: every piece waits for the latest land year under its outline
    # and its inner point (terrain land-year grids, read now: made-land zones keep coming)
    from airports import land_year
    pyear = year[src].copy()
    xy, idx = shapely.get_coordinates(shapely.get_exterior_ring(polys), return_index=True)
    ip = shapely.get_coordinates(shapely.point_on_surface(polys))
    lon, lat = to_ll().transform(np.r_[xy[:, 0], ip[:, 0]], np.r_[xy[:, 1], ip[:, 1]])
    ly = np.nan_to_num(land_year(lon, lat), nan=-np.inf)
    ly_piece = np.full(len(polys), -np.inf)
    np.maximum.at(ly_piece, np.r_[idx, np.arange(len(polys))], ly)
    wait = ly_piece + 0.5 > pyear
    pyear = np.clip(np.where(wait, ly_piece + 0.5, pyear), YEAR_MIN, float(CURRENT_YEAR))
    stats["waits_for_made_land"] = int(wait.sum())
    ground = Ground()
    manh = (feats.boro.values == MANHATTAN)[src]
    VIEWER_DATA.mkdir(parents=True, exist_ok=True)
    report = {"dating": {k: int(v) for k, v in pd.Series(rule).value_counts().items()}, **stats, "files": {}}
    for path, m in ((VIEWER_DATA / "ground-detail.bin.gz", manh), (VIEWER_DATA / "region-ground-detail.bin.gz", ~manh)):
        n_poly, n_vert = write_outlines(path, polys[m], kinds[m], pyear[m], end[src][m], ground)
        report["files"][path.name] = {"polygons": n_poly, "vertices": n_vert, "bytes": path.stat().st_size,
                                      "by_kind": np.bincount(kinds[m], minlength=15).tolist()}
        log(f"ground detail: {path.name}: {n_poly} outlines, {n_vert} vertices, {path.stat().st_size / 1e6:.2f} MB "
            f"({np.bincount(kinds[m], minlength=15).tolist()})")
    report["by_class"] = {k: int(v) for k, v in feats["class"].value_counts().items()}
    report["by_class_rule"] = {f"{c}|{r}": int(v) for (c, r), v in pd.crosstab(feats["class"], rule).stack().items() if v}
    report["years"] = {"min": float(pyear.min()), "max": float(pyear.max()),
                       "by_century": {str(int(k)): int(v) for k, v in pd.Series(np.floor(pyear / 100) * 100).value_counts().sort_index().items()}}
    log(f"ground detail: {len(feats)} features dated: {report['dating']}; {stats}")

    labels, lstats = park_labels(parks, lu, courses, hood)
    n_parks = len(labels)
    # one label per name, place and time: the bigger outline keeps it
    kept = []
    for lab in sorted(labels, key=lambda a: -a["ha"]):
        if not any(k["name"] == lab["name"] and abs(k["lon"] - lab["lon"]) < 0.02 and abs(k["lat"] - lab["lat"]) < 0.02
                   and k["start"] < lab.get("end", 9999) and lab["start"] < k.get("end", 9999) for k in kept):
            kept.append(lab)
    labels = kept
    n_parks = len(labels)
    labels += site_labels()
    for lab in labels:
        lab["start"] = float(max(lab["start"], YEAR_MIN))
    (VIEWER_DATA / "park-labels.json").write_text(json.dumps(labels, ensure_ascii=False, separators=(",", ":")))
    report["labels"] = {"total": len(labels), "sites": len(labels) - n_parks, **lstats}
    out = INTERIM / "ground_detail"
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(report, indent=1))
    log(f"ground detail: {len(labels)} labels { {k: v for k, v in lstats.items() if k != 'estimated_list'} }")


if __name__ == "__main__":
    main()
