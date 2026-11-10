"""Pier candidates of every sheet and chart -> one dated pier per structure: data/manual/piers/piers.geojson.

  python build.py            (after extract.py and chart.py; rewrites piers.geojson, review.csv, stats.json)

 1. candidates: the fingers of every full edition (USGS 1935, 1947, 1955-57, 1966-69, 1994-95 where the sheet was really
    revised; chart editions) that look like piers (reach 35 m or more from the bulkhead, attached at one end only,
    length >= 1.4 x width, width <= 100 m, at least 55 % of their bounding rectangle), inside the five boroughs,
    over today's water or over land made after the sheet.  Today's piers: OpenStreetMap man_made=pier polygons.
 2. one pier across sources = one track: two outlines match when each one's centre lies in the other (10 m slack)
    and their areas are within a factor 2.5.
 3. every track is then looked up on every source that covers it (the classified rasters of extract.py / chart.py):
    'pier' (60 % or more of the outline is solid and it is not plain land), 'water' (30 % or less solid), 'land'
    (the outline lies in land wider than 90 m: filled), else unknown.  The lookup tolerates 6 m of misregistration.
 4. dates.  End: standing if OpenStreetMap has it; else between the last source that shows it and the first later one
    that does not (mid-point, `bracket`, both named in the note; `estimated` if the bracket is wider than 20 years).
    Start: between the last source that shows water and the first that shows the pier; a pier already on the first
    source that covers its place has no lower bound from maps: `estimated`, the note says "on the first source".
    research.csv (cited dates for named piers) overrides both.
"""
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import pyproj
import rasterio
import shapely
from rasterio import features
from rasterio.windows import Window
from shapely.geometry import mapping, shape
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).parent))
import extract as E

HERE = Path(__file__).resolve().parents[1]
UTM = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)
WMT = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
TODAY = 2026
to_utm = lambda g: shapely.transform(g, lambda c: np.column_stack(UTM.transform(c[:, 0], c[:, 1])))
to_wgs = lambda g: shapely.transform(g, lambda c: np.column_stack(UTM.transform(c[:, 0], c[:, 1], direction="INVERSE")))
BORO = {"061": "Manhattan", "047": "Brooklyn", "081": "Queens", "005": "Bronx", "085": "Staten Island"}


def keep(p):
    return (p["reach_m"] >= 35 and not p["both_ends"] and p["gap_m"] <= 12 and p["rect_fill"] >= 0.55 and
            p["length_m"] >= 1.4 * p["width_m"] and p["width_m"] <= 100 and p["area_m2"] >= 250 and
            (p["on_today_land"] <= 0.5 or p["on_made_land"] >= 0.5))


class Source:
    """one classified raster: a USGS sheet edition or a chart edition."""

    def __init__(self, meta):
        self.m = meta
        self.name = meta["sheet"]
        self.chart = self.name.startswith("chart_")
        self.use, self.positive_only = True, False
        if self.chart:
            self.lo = self.hi = meta["date_on_map"]
            self.label = f"C&GS / NOAA chart {meta['quad'].split()[-1] if meta['date_on_map'] < 1974 else {'745': '12335', '541': '12334'}[meta['quad'].split()[-1]]}, {meta['date_on_map']} edition"
            self.A = rasterio.Affine(*meta["affine"])
            fit = meta["fit"][-1]
            self.use = fit["used"] >= 8 and fit["rms_m"] <= 12
            self.shift = (0.0, 0.0)
        else:
            info = E.SHEETS[self.name]
            ed, y = info["edition"], info["date_on_map"]
            photo = info.get("aerial_photo_year")
            self.lo, self.hi = y, y
            if ed == "e1947":
                self.lo = photo or y - 6
            elif ed in ("e1955", "e1966"):
                if photo and photo < y - 5:           # reprinted with office edits only: shows what was there, not what went
                    self.positive_only = True
                elif photo:
                    self.lo = photo
            elif ed == "e1979":                       # photorevision: additions in purple, nothing removed
                self.positive_only, self.lo, self.hi = True, photo or y, info.get("photo_revision_year") or y
            elif ed == "e1995":
                if photo and photo < y - 5:           # photo-inspected reprint of the photorevised sheet: not a new state
                    self.use = False
            self.label = f"USGS {info['quad']} 1:{info['scale']} {y}" + (f" (photographs {photo})" if photo and photo != y else "")
            with rasterio.open(E.OUT / "cls" / self.name) as s:
                self.tr, self.geo = s.transform, E.Geo(s.crs)
            sm = meta.get("shift_m")
            self.shift = tuple(sm) if sm and meta.get("shift_peak", 0) >= 1.2 else (0.0, 0.0)
        b = meta["bbox"] if self.chart else E.SHEETS[self.name]["bbox"]
        self.box = shapely.box(b["minX"] - 0.002, b["minY"] - 0.002, b["maxX"] + 0.002, b["maxY"] + 0.002)
        self.ds = None

    def px(self, g_utm):
        """UTM geometry -> pixel coordinates of this raster."""
        if self.chart:
            def f(c):
                lon, lat = UTM.transform(c[:, 0], c[:, 1], direction="INVERSE")
                X, Y = WMT.transform(lon, lat)
                inv = ~self.A
                return np.column_stack([inv.a * X + inv.b * Y + inv.c, inv.d * X + inv.e * Y + inv.f])
        else:
            def f(c):
                lon, lat = UTM.transform(c[:, 0] - self.shift[0], c[:, 1] - self.shift[1], direction="INVERSE")
                x, y = self.geo.from_wgs(lon, lat)
                inv = ~self.tr
                return np.column_stack([inv.a * np.asarray(x) + inv.b * np.asarray(y) + inv.c, inv.d * np.asarray(x) + inv.e * np.asarray(y) + inv.f])
        return shapely.transform(g_utm, f)

    def look(self, g_utm):
        """(state, solid share, core share, ink share of the interior) of an outline on this source."""
        if self.ds is None:
            self.ds = rasterio.open(E.OUT / "cls" / self.name)
            self.pxm = self.m.get("px_m") or abs(self.ds.transform.a)
        gp = self.px(g_utm)
        x0, y0, x1, y1 = gp.bounds
        c0, r0, c1, r1 = int(math.floor(x0)) - 5, int(math.floor(y0)) - 5, int(math.ceil(x1)) + 5, int(math.ceil(y1)) + 5
        if c0 < 0 or r0 < 0 or c1 > self.ds.width or r1 > self.ds.height:
            return None
        win = Window(c0, r0, c1 - c0, r1 - r0)
        cls = self.ds.read(1, window=win)
        m = features.rasterize([(shapely.affinity.translate(gp, -c0, -r0), 1)], out_shape=cls.shape, fill=0, dtype="uint8").astype(bool)
        if m.sum() < 8 or (cls[m] == 255).mean() > 0.1:
            return None
        k = max(1, int(round(6.0 / self.pxm)))
        best = None
        for dy, dx in ((0, 0), (k, 0), (-k, 0), (0, k), (0, -k)):
            mm = np.roll(np.roll(m, dy, axis=0), dx, axis=1)
            v = cls[mm]
            solid, core = float(((v == 1) | (v == 2)).mean()), float((v == 2).mean())
            if best is None or solid > best[0]:
                best = (solid, core, dy, dx)
        solid, core, dy, dx = best
        ink = self.ds.read(2, window=win)
        inner = shapely.affinity.translate(gp, -c0 + dx, -r0 + dy).buffer(-4.0 / self.pxm)
        inkshare = None
        if not inner.is_empty:
            mi = features.rasterize([(inner, 1)], out_shape=cls.shape, fill=0, dtype="uint8").astype(bool)
            if mi.sum() >= 6:
                inkshare = float(ink[mi].mean())
        state = "land" if core >= 0.7 else ("pier" if solid >= 0.6 else ("water" if solid <= 0.3 else "unknown"))
        return state, round(solid, 2), round(core, 2), None if inkshare is None else round(inkshare, 2)


def load_sources():
    out = []
    for p in sorted((E.OUT / "cls").glob("*.json")):
        s = Source(json.load(open(p)))
        if s.use:
            out.append(s)
    return out


def boroughs():
    g = gpd.read_file(E.OUT / "boroughs.gpkg").to_crs("EPSG:32618")
    return [(BORO[r.COUNTYFP], r.geometry) for r in g.itertuples()]


def osm_piers(boros):
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    rows = con.execute(f"""SELECT id, name, CAST(tags AS VARCHAR), ST_AsWKB(geometry) FROM '{E.RAW}/overture_piers.parquet'
                           WHERE subtype = 'pier' AND ST_GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON')""").fetchall()
    out = []
    for oid, name, tags, wkb in rows:
        g = to_utm(shapely.from_wkb(bytes(wkb)))
        if not g.is_valid:
            g = g.buffer(0)
        b = next((n for n, poly in boros if poly.contains(g.centroid)), None)
        if b is None or (g.area < 150 and not name):
            continue
        t = json.loads(tags) if tags else {}
        if t.get("floating") == "yes":
            continue
        out.append(dict(kind="osm", id=oid, name=name or "", tags=t, geom=g, borough=b))
    return out


def rectish(g):
    """the outline as its bounding rectangle when it nearly is one (pier outlines read off a 2 m raster are ragged)."""
    r = g.minimum_rotated_rectangle
    if r.area > 0 and g.intersection(r).area / g.union(r).area >= 0.8:
        return r
    return g.simplify(2.5)


def dims(g):
    c = np.array(g.minimum_rotated_rectangle.exterior.coords)[:4]
    a, b = np.hypot(*(c[1] - c[0])), np.hypot(*(c[2] - c[1]))
    return max(a, b), min(a, b)


def main():
    boros = boroughs()
    sources = load_sources()
    by_name = {s.name: s for s in sources}
    print(len(sources), "sources:", Counter("chart" if s.chart else E.SHEETS[s.name]["edition"] for s in sources))
    # 1. candidates
    items = []
    for s in sources:
        if s.positive_only:
            continue
        fc = json.load(open(E.OUT / "cand" / s.name.replace(".tif", ".geojson")))
        for f in fc["features"]:
            p = f["properties"]
            if not keep(p):
                continue
            g = to_utm(shape(f["geometry"]))
            if not s.chart and s.shift != (0.0, 0.0):
                g = shapely.affinity.translate(g, *s.shift)
            b = next((n for n, poly in boros if poly.contains(g.centroid)), None)
            if b is None:
                continue
            items.append(dict(kind="map", src=s.name, geom=g.buffer(0), borough=b, p=p))
    n_map = len(items)
    osm = osm_piers(boros)
    items += osm
    print(n_map, "map candidates,", len(osm), "OpenStreetMap piers")

    # 2. tracks
    geoms = [it["geom"] for it in items]
    cents = [g.centroid for g in geoms]
    tree = STRtree(geoms)
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, g in enumerate(geoms):
        for j in tree.query(g.buffer(10)):
            j = int(j)
            if j <= i:
                continue
            if items[i]["kind"] == "osm" and items[j]["kind"] == "osm":
                continue
            if items[i].get("src") is not None and items[i].get("src") == items[j].get("src"):
                continue
            gj = geoms[j]
            ra = g.area / gj.area
            if 0.4 <= ra <= 2.5 and gj.buffer(10).contains(cents[i]) and g.buffer(10).contains(cents[j]):
                a, b = find(i), find(j)
                if a != b:
                    parent[a] = b
    groups = defaultdict(list)
    for i in range(len(items)):
        groups[find(i)].append(i)

    # one outline per track
    tracks = []
    for members in groups.values():
        ms = [items[i] for i in members]
        osm_m = [m for m in ms if m["kind"] == "osm"]
        maps = [m for m in ms if m["kind"] == "map"]
        if osm_m:
            for k, o in enumerate(sorted(osm_m, key=lambda m: -m["geom"].area)):
                tracks.append(dict(geom=o["geom"], osm=o, maps=maps if k == 0 else [], borough=o["borough"]))
        else:
            best = max(maps, key=lambda m: m["p"]["rect_fill"] + (0.1 if m["src"].startswith("chart_") else 0.0))
            tracks.append(dict(geom=rectish(best["geom"]), osm=None, maps=maps, borough=best["borough"], outline_src=best["src"]))
    print(len(tracks), "tracks,", sum(t["osm"] is not None for t in tracks), "standing")

    # 3. every track on every source
    wgs_boxes = [to_wgs(t["geom"]).centroid for t in tracks]
    for t in tracks:
        t["obs"] = []
    for s in sources:
        for t, c in zip(tracks, wgs_boxes):
            if not s.box.contains(c):
                continue
            r = s.look(t["geom"])
            if r is None:
                continue
            state = r[0]
            L, Wd = dims(t["geom"])
            if state == "land" and Wd > 80:
                state = "pier"                   # a pier wider than the 90 m of the land test
            if s.positive_only and state != "pier":
                continue
            t["obs"].append(dict(src=s.name, label=s.label, lo=s.lo, hi=s.hi, state=state, solid=r[1], core=r[2], ink=r[3], chart=s.chart))
        if s.ds is not None:
            s.ds.close()
            s.ds = None
    json.dump([dict(geom=mapping(to_wgs(t["geom"])), borough=t["borough"], osm=None if t["osm"] is None else dict(id=t["osm"]["id"], name=t["osm"]["name"], tags=t["osm"]["tags"]),
                    outline_src=t.get("outline_src"), n_maps=len(t["maps"]), map_srcs=sorted({m["src"] for m in t["maps"]}), obs=t["obs"]) for t in tracks],
              open(E.OUT / "tracks.json", "w"))
    print("tracks.json written")


if __name__ == "__main__":
    main()
