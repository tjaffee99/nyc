"""Outline helpers for the sites (all WGS84 shapely geometries).

  osm(*ids)            OpenStreetMap land-use / land polygons (Overture 2026-10-21.0 `region5_land_use`,
                       `base_land`), by the first 8 characters of the Overture id (union)
  lpc(name)            a Landmarks Preservation Commission historic district outline
  park(name)           an NYC Parks property outline (sign name)
  block(lon, lat, ...) the street block(s) around the point(s): today's street network
                       (Overture roads) polygonized - a real outline for a works known by its block
  ring(pts)            a ring given as (lon, lat) pairs (read on a map; `estimated` unless said)
  local(cx, cy, pts)   a ring read on a map sheet in metres east / north of (cx, cy)
  rect(lon, lat, w, d, rot)   rectangle w x d metres, long side turned rot degrees clockwise from east
  circle(lon, lat, r)  circle of radius r metres
  hull(lon, lat, radius, buffer)  convex hull of today's footprints within radius, grown by buffer
  clip(g, w, s, e, n) / minus(g, h) / union(*gs) / land(g)  (land: minus today's water)
"""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

import duckdb
import shapely
import shapely.wkb
from shapely.geometry import Point, Polygon, box, shape
from shapely.ops import polygonize, unary_union

ROOT = Path(__file__).resolve().parents[4]
OV = ROOT / "data" / "raw" / "overture" / "2026-10-21.0"
FP = ROOT / "data" / "interim" / "nyc_footprints_raw.parquet"
BL = ROOT / "data" / "interim" / "nyc_buildings.parquet"


@lru_cache(None)
def con():
    c = duckdb.connect()
    c.sql("install spatial; load spatial")
    return c


def kx(lat):
    return 111320 * math.cos(math.radians(lat))


KY = 110574.0


def osm(*ids):
    gs = []
    for i in ids:
        got = False
        for f in ("region5_land_use", "base_land"):
            r = con().execute(f"select st_aswkb(geometry) from '{OV}/{f}.parquet' where starts_with(id, $1)", [i]).fetchall()
            for (w,) in r:
                g = shapely.wkb.loads(bytes(w))
                if g.geom_type in ("Polygon", "MultiPolygon"):
                    gs.append(g)
                    got = True
            if got:
                break
        if not got:
            raise KeyError(f"osm id {i} not found")
    return unary_union(gs)


@lru_cache(None)
def _lpc():
    d = json.loads((ROOT / "data/raw/nyc/lpc_historic_districts.geojson").read_text())
    out = {}
    for f in d["features"]:
        out.setdefault(f["properties"]["area_name"], []).append(shape(f["geometry"]))
    return out


def lpc(name):
    """LPC historic district outline. The city's file is in New York State Plane feet (EPSG:2263)
    although its header says CRS84."""
    import pyproj
    from shapely.ops import transform
    g = unary_union(_lpc()[name]).buffer(0)
    if abs(g.bounds[0]) > 360:
        tf = pyproj.Transformer.from_crs("EPSG:2263", "EPSG:4326", always_xy=True)
        g = transform(tf.transform, g)
    return g


@lru_cache(None)
def _parks():
    d = json.loads((ROOT / "data/raw/nyc/parks_properties.geojson").read_text())
    out = {}
    for f in d["features"]:
        if f["geometry"]:
            out.setdefault(f["properties"].get("signname"), []).append(shape(f["geometry"]))
    return out


def park(name):
    return unary_union(_parks()[name]).buffer(0)


def _roads(w, s, e, n):
    out = []
    for f in ("roads_local", "roads_region", "freeways"):
        try:
            r = con().execute(
                f"select st_aswkb(geometry) from '{OV}/{f}.parquet' where st_intersects(geometry, st_makeenvelope($1,$2,$3,$4))",
                [w, s, e, n]).fetchall()
        except Exception:  # noqa: BLE001
            continue
        out += [shapely.wkb.loads(bytes(x[0])) for x in r]
    return out


def block(*pts, reach=450.0, gap=14.0):
    """Union of the street blocks containing the points (lon, lat). Blocks are the faces of
    today's street network; `gap` metres closes the streets between adjoining blocks."""
    lon0 = sum(p[0] for p in pts) / len(pts)
    lat0 = sum(p[1] for p in pts) / len(pts)
    dx, dy = reach / kx(lat0), reach / KY
    w = min(p[0] for p in pts) - dx
    e = max(p[0] for p in pts) + dx
    s = min(p[1] for p in pts) - dy
    n = max(p[1] for p in pts) + dy
    lines = [l for l in _roads(w, s, e, n) if l.geom_type in ("LineString", "MultiLineString")]
    faces = list(polygonize(unary_union(lines)))
    got = []
    for p in pts:
        f = [g for g in faces if g.contains(Point(p))]
        if not f:
            raise ValueError(f"no closed street block at {p}")
        got.append(min(f, key=lambda g: g.area))
    if len(got) == 1:
        return got[0]
    d = gap / KY
    return unary_union([g.buffer(d / 2) for g in got]).buffer(-d / 2 * 0.9)


def ring(pts):
    return Polygon(pts).buffer(0)


def local(cx, cy, pts):
    """A ring read on a map in metres east / north of (cx, cy)."""
    return Polygon([(cx + x / kx(cy), cy + y / KY) for x, y in pts]).buffer(0)


def rect(lon, lat, w, d, rot=0.0):
    a = math.radians(-rot)
    c, s = math.cos(a), math.sin(a)
    out = []
    for x, y in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
        out.append((lon + (x * c - y * s) / kx(lat), lat + (x * s + y * c) / KY))
    return Polygon(out)


def circle(lon, lat, r, n=32):
    return Polygon([(lon + r * math.cos(2 * math.pi * i / n) / kx(lat), lat + r * math.sin(2 * math.pi * i / n) / KY)
                    for i in range(n)])


def footprints(g, cols="bin, name, year_raw, height_m, lon, lat", min_area=0.0):
    """Today's footprints whose centre lies in g: DataFrame with shapely `geometry`."""
    import geopandas as gpd
    w, s, e, n = g.bounds
    df = con().execute(
        f"select {cols}, geometry from '{FP}' where lon between $1 and $3 and lat between $2 and $4", [w, s, e, n]).df()
    if not len(df):
        return gpd.GeoDataFrame(df, geometry=[], crs=4326)
    geo = [shapely.wkb.loads(bytes(b)) for b in df.geometry]
    geo = [max(x.geoms, key=lambda p: p.area) if x.geom_type == "MultiPolygon" else x for x in geo]
    df = gpd.GeoDataFrame(df.drop(columns="geometry"), geometry=geo, crs=4326)
    pg = shapely.prepared.prep(g)
    df = df[[pg.contains(Point(x, y)) for x, y in zip(df.lon, df.lat)]]
    df["area_m2"] = [x.area * kx(y) * KY for x, y in zip(df.geometry, df.lat)]
    return df[df.area_m2 >= min_area].reset_index(drop=True)


def built(g):
    """The built file's years for the standing buildings whose centre lies in g."""
    w, s, e, n = g.bounds
    df = con().execute(
        f"select bin, name, start_year, year_confidence, year_src, raw_year, height_m, bldgclass, lon, lat, area "
        f"from '{BL}' where end_year = 9999 and lon between $1 and $3 and lat between $2 and $4", [w, s, e, n]).df()
    pg = shapely.prepared.prep(g)
    return df[[pg.contains(Point(x, y)) for x, y in zip(df.lon, df.lat)]].reset_index(drop=True)


def hull(lon, lat, radius, buffer=35.0):
    g = circle(lon, lat, radius)
    fp = footprints(g)
    h = unary_union(list(fp.geometry)).convex_hull
    return h.buffer(buffer / KY)


def clip(g, w, s, e, n):
    return g.intersection(box(w, s, e, n))


def minus(g, h):
    return g.difference(h)


def union(*gs):
    return unary_union(gs)


def land(g):
    w, s, e, n = g.bounds
    r = con().execute(
        f"select st_aswkb(geometry) from '{OV}/base_water.parquet' where st_intersects(geometry, st_makeenvelope($1,$2,$3,$4))",
        [w, s, e, n]).fetchall()
    ws = [shapely.wkb.loads(bytes(x[0])) for x in r]
    ws = [x for x in ws if x.geom_type in ("Polygon", "MultiPolygon")]
    return g.difference(unary_union(ws)) if ws else g


def area_ha(g):
    c = g.centroid
    return g.area * kx(c.y) * KY / 1e4


def named(rx, near=None, reach=3000.0, classes=None):
    """Land-use / land polygons whose name matches the regular expression (union); `near`
    (lon, lat) limits the search to `reach` metres, `classes` to Overture classes."""
    gs = []
    for f in ("region5_land_use", "base_land"):
        q = f"select st_aswkb(geometry), class from '{OV}/{f}.parquet' where regexp_matches(name, $1)"
        a = [rx]
        if near:
            dx, dy = reach / kx(near[1]), reach / KY
            q += " and st_intersects(geometry, st_makeenvelope($2,$3,$4,$5))"
            a += [near[0] - dx, near[1] - dy, near[0] + dx, near[1] + dy]
        for w, c in con().execute(q, a).fetchall():
            g = shapely.wkb.loads(bytes(w))
            if g.geom_type in ("Polygon", "MultiPolygon") and (not classes or c in classes):
                gs.append(g)
    if not gs:
        raise KeyError(f"no polygon named {rx}")
    return unary_union(gs)


def at(lon, lat, classes=("industrial", "works", "brownfield", "railway", "military", "base", "landfill", "quarry"),
       pick="smallest"):
    """The land-use polygon of one of the classes that contains the point."""
    r = con().execute(
        f"select st_aswkb(geometry), class, name, substr(id,1,8) from '{OV}/region5_land_use.parquet' "
        "where st_contains(geometry, st_point($1,$2))", [lon, lat]).fetchall()
    gs = [(shapely.wkb.loads(bytes(w)), c, nm, i) for w, c, nm, i in r if c in classes]
    if not gs:
        raise KeyError(f"no {classes} polygon at {lon},{lat}; there: {[(c, nm, i) for _, c, nm, i in [(0, *x[1:]) for x in r]]}")
    gs.sort(key=lambda t: t[0].area, reverse=(pick != "smallest"))
    return gs[0][0]
