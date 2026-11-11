"""The map's extent: the five boroughs of New York City and the counties around them that
have been built (data/manual/extent_counties.json).

The outline is the union of the TIGER 2024 county polygons of the five boroughs (New York,
Bronx, Kings, Queens, Richmond — they include each county's share of the rivers, the harbour
and the ocean to the state line), grown by 0.012 degrees (about 1 km) and simplified, so the
faded band lies beyond the county lines: Manhattan's Hudson shore is 500-700 m from the
state line and must not fade. The ring is computed once and committed
(data/manual/extent_ring.json); delete that file to recompute it from TIGER.

Pipeline stages drop features outside it (with a margin: the viewer fades the map out over
the last kilometre inside the line, like the edge of an old map); the viewer reads
viewer/public/data/map-extent.json (written by `python extent.py`).
"""
from __future__ import annotations

import json

import numpy as np
import shapely
from shapely.geometry import Polygon

from common import BORO_COUNTY, MANUAL, RAW, VIEWER_DATA

RING_FILE = MANUAL / "extent_ring.json"
GROW_DEG = 0.012
FADE_KM = 1.0


COUNTIES_FILE = MANUAL / "extent_counties.json"


def map_counties():
    """{state+county FIPS: name} of the counties on the map beside the five boroughs
    (data/manual/extent_counties.json; written by `python extent.py counties <fips> ...`)."""
    if COUNTIES_FILE.exists():
        return json.loads(COUNTIES_FILE.read_text()).get("counties", {})
    return {}


def _compute_ring():
    import geopandas as gpd
    co = gpd.read_file(f"zip://{RAW / 'tiger' / 'tl_2024_us_county.zip'}")
    fips = co.STATEFP + co.COUNTYFP
    co = co[((co.STATEFP == "36") & co.COUNTYFP.isin(list(BORO_COUNTY))) | fips.isin(list(map_counties()))].to_crs(4326)
    u = shapely.union_all(list(co.geometry)).buffer(GROW_DEG).simplify(0.002)
    poly = max(getattr(u, "geoms", [u]), key=lambda p: p.area)
    ring = [[round(x, 4), round(y, 4)] for x, y in np.asarray(poly.exterior.coords)[:-1, :2]]
    RING_FILE.parent.mkdir(parents=True, exist_ok=True)
    RING_FILE.write_text(json.dumps({"ring": ring, "source": "US Census TIGER/Line 2024 counties 36005, 36047, 36061, 36081, 36085",
                                     "grow_deg": GROW_DEG}))
    return ring


EXTENT = json.loads(RING_FILE.read_text())["ring"] if RING_FILE.exists() else _compute_ring()
POLY = Polygon(EXTENT)
MARGIN_DEG = 0.004  # keep features a little beyond the line: they sit in the faded band


def in_extent(points, margin=MARGIN_DEG):
    """Boolean mask: (Geo)Series / array of shapely points (EPSG:4326) inside the extent."""
    poly = POLY.buffer(margin)
    shapely.prepare(poly)
    return shapely.contains(poly, np.asarray(getattr(points, "values", points)))


CORE_FILE = MANUAL / "extent_core.json"
CORE_FIPS = ["34017"]      # with the five boroughs: Hudson County (the Hudson waterfront)


def core_ring():
    """The outline the page loads by default: the five boroughs and Hudson County. The whole map
    (26 counties more) is slow on a telephone; the page loads it when asked (viewer/src/scope.ts)."""
    if CORE_FILE.exists():
        return json.loads(CORE_FILE.read_text())["ring"]
    import geopandas as gpd
    co = gpd.read_file(f"zip://{RAW / 'tiger' / 'tl_2024_us_county.zip'}")
    fips = co.STATEFP + co.COUNTYFP
    co = co[((co.STATEFP == "36") & co.COUNTYFP.isin(list(BORO_COUNTY))) | fips.isin(CORE_FIPS)].to_crs(4326)
    u = shapely.union_all(list(co.geometry)).buffer(GROW_DEG).simplify(0.0015)
    poly = max(getattr(u, "geoms", [u]), key=lambda p: p.area)
    ring = [[round(x, 4), round(y, 4)] for x, y in np.asarray(poly.exterior.coords)[:-1, :2]]
    CORE_FILE.write_text(json.dumps({"ring": ring, "source": "US Census TIGER/Line 2024: the five boroughs and county 34017",
                                     "grow_deg": GROW_DEG}))
    return ring


def write_viewer_extent():
    VIEWER_DATA.mkdir(parents=True, exist_ok=True)
    (VIEWER_DATA / "map-extent.json").write_text(json.dumps({"ring": [list(p) for p in EXTENT], "fade_km": FADE_KM}))
    (VIEWER_DATA / "core-extent.json").write_text(json.dumps({"ring": [list(p) for p in core_ring()], "fade_km": FADE_KM}))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "counties":
        # set the counties on the map and recompute the outline
        from common import REGION_COUNTIES
        chosen = {f: REGION_COUNTIES[f] for f in sys.argv[2:]}
        COUNTIES_FILE.write_text(json.dumps({"counties": chosen}, indent=1))
        EXTENT = _compute_ring()
        POLY = Polygon(EXTENT)
    write_viewer_extent()
    print("map-extent.json written", POLY.bounds, len(EXTENT), "vertices")
