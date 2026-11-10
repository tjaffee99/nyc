"""Pier candidates of every sheet and chart -> one dated pier per structure: data/manual/piers/piers.geojson.

  python build.py            (after extract.py and chart.py; rewrites piers.geojson, review.csv, stats.json)

 1. candidates: the fingers of every full edition (USGS 1935, 1947, 1955-57, 1966-69, 1994-95 where the sheet was really
    revised; chart editions) that look like piers (reach 35 m or more from the bulkhead, attached at one end only,
    length >= 1.4 x width, width <= 100 m, at least 55 % of their bounding rectangle; USGS: 62 %), inside the five
    boroughs, over today's tidal water or over land made after the sheet; not at a marsh unless roofed; not a beach
    groyne (natural_ok).  Today's piers: OpenStreetMap man_made=pier polygons.
 2. one pier across sources = one track: two outlines match when half of the smaller lies in the larger, or each
    one's centre lies in the other (10 m slack), and their areas are within a factor 3.
 2b. registration: see step 1b in main() (control piers per sheet, local offsets).
 3. every track is then looked up on every source that covers it (the classified rasters of extract.py / chart.py):
    'pier' (60 % or more of the outline is solid, with water beside it), 'water' (30 % or less solid), 'land'
    (the outline lies in land wider than 90 m, or is solid with solid ground on its sides: filled), else unknown.  The lookup tolerates 6 m of misregistration.
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
            self.use = fit["used"] >= 8 and fit["rms_m"] <= 30
            self.trusted = fit["rms_m"] <= 5          # fitted to today's shore within 5 m: its outlines are control
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
            self.trusted = False
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

    def _window(self, g_utm, pad_m):
        if self.ds is None:
            self.ds = rasterio.open(E.OUT / "cls" / self.name)
            self.pxm = self.m.get("px_m") or abs(self.ds.transform.a)
        gp = self.px(g_utm)
        pad = int(pad_m / self.pxm) + 5
        x0, y0, x1, y1 = gp.bounds
        c0, r0, c1, r1 = int(math.floor(x0)) - pad, int(math.floor(y0)) - pad, int(math.ceil(x1)) + pad, int(math.ceil(y1)) + pad
        if c0 < 0 or r0 < 0 or c1 > self.ds.width or r1 > self.ds.height:
            return None
        win = Window(c0, r0, c1 - c0, r1 - r0)
        return gp, win, shapely.affinity.translate(gp, -c0, -r0)

    def ground(self, dx_px, dy_px):
        """a pixel offset as ground metres (east, north)."""
        if self.chart:
            c = math.cos(math.radians(40.71))
            return (self.A.a * dx_px + self.A.b * dy_px) * c, (self.A.d * dx_px + self.A.e * dy_px) * c
        return self.tr.a * dx_px, self.tr.e * dy_px

    def best_shift(self, g_utm, reach_m=36.0):
        """where a trusted outline sits on this source: the offset (ground metres) that puts it on solid with water
        around it (score = solid share inside - solid share in a 12 m ring), and that score."""
        w = self._window(g_utm, reach_m + 14)
        if w is None:
            return None
        gp, win, gl = w
        cls = self.ds.read(1, window=win)
        if (cls == 255).mean() > 0.02:
            return None
        solid = ((cls == 1) | (cls == 2)).astype("float32")
        inside = features.rasterize([(gl, 1)], out_shape=cls.shape, fill=0, dtype="uint8").astype(bool)
        ring = features.rasterize([(gl.buffer(12 / self.pxm), 1)], out_shape=cls.shape, fill=0, dtype="uint8").astype(bool) & ~inside
        if inside.sum() < 12 or ring.sum() < 12:
            return None
        yi, xi = np.nonzero(inside)
        yr, xr = np.nonzero(ring)
        step = max(1, int(round(3.0 / self.pxm)))
        n = int(reach_m / self.pxm / step)
        best = (-9, 0, 0)
        zero = None
        for a in range(-n, n + 1):
            for b in range(-n, n + 1):
                dy, dx = a * step, b * step
                sc = float(solid[yi + dy, xi + dx].mean() - solid[yr + dy, xr + dx].mean())
                if a == 0 and b == 0:
                    zero = sc
                if sc > best[0]:
                    best = (sc, dx, dy)
        e, nth = self.ground(best[1], best[2])
        return e, nth, best[0], zero

    def local(self, pt):
        """offset of this source's drawing from the truth around a point (median of the 8 nearest control piers
        within 2 km; nothing without 3 of them)."""
        c = getattr(self, "ctrl", None)
        if c is None or len(c) < 3:
            return 0.0, 0.0
        d = np.hypot(c[:, 0] - pt.x, c[:, 1] - pt.y)
        idx = np.argsort(d)[:8]
        idx = idx[d[idx] <= 2000]
        if len(idx) < 3:
            return 0.0, 0.0
        return float(np.median(c[idx, 2])), float(np.median(c[idx, 3]))

    def look(self, g_utm):
        """(state, solid share, core share, ink share of the interior) of an outline on this source."""
        g_utm = shapely.affinity.translate(g_utm, *self.local(g_utm.centroid))
        w = self._window(g_utm, 0)
        if w is None:
            return None
        gp, win, gl = w
        c0, r0 = win.col_off, win.row_off
        cls = self.ds.read(1, window=win)
        m = features.rasterize([(gl, 1)], out_shape=cls.shape, fill=0, dtype="uint8").astype(bool)
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
        # water beside it: a pier has water along its sides, made land and wharves do not
        ring = features.rasterize([(gl.buffer(12 / self.pxm), 1)], out_shape=cls.shape, fill=0, dtype="uint8").astype(bool) & ~m
        rv = cls[np.roll(np.roll(ring, dy, axis=0), dx, axis=1)]
        beside = float(((rv == 1) | (rv == 2)).mean()) if rv.size else 0.0
        ink = self.ds.read(2, window=win)
        inner = shapely.affinity.translate(gl, dx, dy).buffer(-4.0 / self.pxm)
        inkshare = None
        if not inner.is_empty:
            mi = features.rasterize([(inner, 1)], out_shape=cls.shape, fill=0, dtype="uint8").astype(bool)
            if mi.sum() >= 6:
                inkshare = float(ink[mi].mean())
        state = "land" if (core >= 0.7 or (solid >= 0.6 and beside > 0.6)) else ("pier" if solid >= 0.6 else ("water" if solid <= 0.3 else "unknown"))
        return state, round(solid, 2), round(core, 2), None if inkshare is None else round(inkshare, 2)


def load_sources():
    out = []
    for p in sorted((E.OUT / "cls").glob("*.json")):
        s = Source(json.load(open(p)))
        if s.use:
            out.append(s)
    return out


class Boroughs:
    """inside the city = inside one of the five counties (TIGER, water included); which borough = the borough of the
    nearest building (the county lines put the whole East River in New York County, so a Brooklyn pier is not in Kings)."""

    def __init__(self):
        from scipy.spatial import cKDTree
        g = gpd.read_file(E.OUT / "boroughs.gpkg").to_crs("EPSG:32618")
        self.city = shapely.unary_union(list(g.geometry))
        con = duckdb.connect()
        lon, lat, boro = con.execute(f"SELECT lon, lat, CAST(boro AS VARCHAR) FROM '{E.ROOT}/data/interim/nyc_building_points.parquet' WHERE end_year = 9999").fetchnumpy().values()
        x, y = UTM.transform(np.asarray(lon, float), np.asarray(lat, float))
        self.tree, self.boro = cKDTree(np.column_stack([x, y])), np.asarray(boro)
        self.names = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"}

    def of(self, pt):
        if not self.city.contains(pt):
            return None
        return self.names[str(self.boro[self.tree.query([pt.x, pt.y])[1]])[:1]]


def osm_piers(boros):
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    rows = con.execute(f"""SELECT id, name, CAST(tags AS VARCHAR), ST_AsWKB(geometry), source_record FROM '{E.RAW}/overture_piers.parquet'
                           WHERE subtype = 'pier' AND ST_GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON')""").fetchall()
    out = []
    for oid, name, tags, wkb, rec in rows:
        g = to_utm(shapely.from_wkb(bytes(wkb)))
        if not g.is_valid:
            g = g.buffer(0)
        b = boros.of(g.centroid)
        if b is None or g.area < (120 if name else 150):
            continue
        t = json.loads(tags) if tags else {}
        if t.get("floating") == "yes":
            continue
        out.append(dict(kind="osm", id=oid, name=name or "", tags=t, geom=g, borough=b, record=rec))
    return out


def context():
    """today's tidal water (every water polygon connected to the Upper Bay), the open ocean, today's wetlands (UTM)."""
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    base = f"{E.ROOT}/data/raw/overture/2026-10-21.0"
    box = "ST_XMax(geometry) > -74.30 AND ST_XMin(geometry) < -73.65 AND ST_YMax(geometry) > 40.45 AND ST_YMin(geometry) < 40.95"
    rows = con.execute(f"""SELECT subtype, class, ST_AsWKB(geometry) FROM '{base}/base_water.parquet'
        WHERE class NOT IN ('swimming_pool', 'wastewater', 'reflecting_pool', 'shoal', 'stream', 'drain', 'ditch') AND {box}
          AND (subtype IN ('ocean', 'physical', 'river', 'canal') OR ST_Area(geometry) > 3e-7)""").fetchall()
    clip = shapely.box(-74.30, 40.45, -73.65, 40.95)
    polys, ocean = [], []
    for st, cl, w in rows:
        g = shapely.from_wkb(bytes(w))
        g = (g if g.is_valid else g.buffer(0)).intersection(clip)
        if g.is_empty:
            continue
        g = to_utm(g)
        polys.append(g)
        if st == "ocean":
            ocean.append(g)
    tree = STRtree(polys)
    seed = to_utm(shapely.Point(-74.045, 40.665))
    start = [int(i) for i in tree.query(seed) if polys[int(i)].contains(seed)]
    seen, stack = set(start), list(start)
    while stack:
        i = stack.pop()
        for j in tree.query(polys[i].buffer(3)):
            j = int(j)
            if j not in seen and polys[j].distance(polys[i]) <= 3:
                seen.add(j)
                stack.append(j)
    tidal = [polys[i] for i in seen]
    wet = [to_utm(shapely.from_wkb(bytes(w)).buffer(0)) for (w,) in con.execute(f"SELECT ST_AsWKB(geometry) FROM '{base}/base_land.parquet' WHERE subtype = 'wetland' AND {box}").fetchall()]
    print(len(polys), "water polygons,", len(tidal), "tidal,", len(ocean), "ocean,", len(wet), "wetlands")
    return STRtree(tidal), tidal, STRtree(ocean), ocean, STRtree(wet), wet


def flags(g, ctx):
    ttree, tidal, otree, ocean, wtree, wet = ctx
    share = lambda tree, polys: sum(g.intersection(polys[int(i)]).area for i in tree.query(g)) / g.area
    return dict(tidal=round(min(share(ttree, tidal), 1.0), 2), ocean=round(min(share(otree, ocean), 1.0), 2),
                wetland=bool(len([i for i in wtree.query(g.buffer(40)) if wet[int(i)].distance(g) <= 40])))


def natural_ok(c):
    """drops what the finger test also finds on natural shores: marsh edges, creek banks, ponds, beach groynes."""
    p, f = c["p"], c["f"]
    chart = c["src"].startswith("chart_")
    if f["tidal"] < 0.5 and p["on_made_land"] < 0.5:
        return False                                   # not over the harbour's water (a pond, a lake, dry land)
    if chart:
        return True
    x, y = c["lonlat"]
    core = -74.10 <= x <= -73.93 and 40.60 <= y <= 40.79      # the working port: Manhattan, Brooklyn, north-east Staten Island
    if p["rect_fill"] < (0.55 if core else 0.62) or p["length_m"] > 520:
        return False
    if f["wetland"] and p["ink"] < 0.3:
        return False                                   # an open, unroofed finger at a marsh: marsh
    if y < 40.60 and (p["length_m"] < 4 * p["width_m"] or p["length_m"] < 60):
        return False                                   # the ocean beaches: groynes and bars
    return True


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
    boros = Boroughs()
    sources = load_sources()
    by_name = {s.name: s for s in sources}
    print(len(sources), "sources:", Counter("chart" if s.chart else E.SHEETS[s.name]["edition"] for s in sources))
    with open(HERE / "sources_used.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["source", "kind", "label", "content_from", "content_to", "role", "registration", "url"])
        for s in sorted(sources, key=lambda s: (s.chart, s.lo, s.name)):
            if s.chart:
                cid = s.name[6:-4]
                fit = s.m["fit"][-1]
                w.writerow([cid, "nautical chart 1:10,000", s.label, s.lo, s.hi, "outlines + presence", f"fitted here, {fit['used']} blocks, rms {fit['rms_m']} m" + ("" if s.trusted else "; then control piers"),
                            f"https://historicalcharts.noaa.gov/includes/downloadsingle.php?filename={cid}&fileExt=.jpg"])
            else:
                w.writerow([s.name.replace("_geo.tif", ""), "USGS topographic sheet", s.label, s.lo, s.hi, "additions only (photorevision / office edit)" if s.positive_only else "outlines + presence",
                            "sheet georeference (NAD27, NADCON) + control piers", E.SHEETS[s.name]["url"]])
    # 1. candidates
    osm = osm_piers(boros)
    ctx = context()
    cands, dropped = {}, Counter()
    for s in sources:
        if s.positive_only:
            continue
        out = []
        for f in json.load(open(E.OUT / "cand" / s.name.replace(".tif", ".geojson")))["features"]:
            p = f["properties"]
            if not keep(p):
                continue
            g = to_utm(shape(f["geometry"]))
            if not s.chart and s.shift != (0.0, 0.0):
                g = shapely.affinity.translate(g, *s.shift)
            b = boros.of(g.centroid)
            if b is not None:
                c = dict(kind="map", src=s.name, geom=g.buffer(0), borough=b, p=p)
                c["f"] = flags(c["geom"], ctx)
                c["lonlat"] = UTM.transform(c["geom"].centroid.x, c["geom"].centroid.y, direction="INVERSE")
                if natural_ok(c):
                    out.append(c)
                else:
                    dropped[s.name] += 1
        cands[s.name] = out
    # 1b. the USGS scans sit up to 30 m off in places: where each sheet draws the piers whose position is known
    # (OpenStreetMap's and the charts', fitted to 2-3 m) gives its local offset; its own outlines are moved back by it
    trusted = [o["geom"] for o in osm if o["geom"].area >= 400] + [c["geom"] for s in sources if s.trusted for c in cands.get(s.name, [])]
    tw = [to_wgs(g).centroid for g in trusted]
    rep = {}
    for s in sources:
        if s.trusted:
            continue
        ctrl = []
        for g, c in zip(trusted, tw):
            if not s.box.contains(c):
                continue
            r = s.best_shift(g)
            if r is not None and r[2] >= 0.55:
                ctrl.append((g.centroid.x, g.centroid.y, r[0], r[1]))
        s.ctrl = np.array(ctrl) if ctrl else None
        if s.ctrl is not None and len(s.ctrl) >= 3:
            rep[s.name] = dict(n=len(ctrl), median_east=round(float(np.median(s.ctrl[:, 2])), 1), median_north=round(float(np.median(s.ctrl[:, 3])), 1),
                               p90_abs=round(float(np.percentile(np.hypot(s.ctrl[:, 2], s.ctrl[:, 3]), 90)), 1))
        for c in cands.get(s.name, []):
            e, n = s.local(c["geom"].centroid)
            if e or n:
                c["geom"] = shapely.affinity.translate(c["geom"], -e, -n)
    json.dump(rep, open(E.OUT / "sheet_offsets.json", "w"), indent=1)
    print("sheet offsets (m):", {k.split("_24000")[0].split("_25000")[0]: (v["n"], v["median_east"], v["median_north"], v["p90_abs"]) for k, v in rep.items()})
    print("dropped as natural shore:", sum(dropped.values()))
    items = [c for s in sources for c in cands.get(s.name, [])]
    n_map = len(items)
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
            inter = g.intersection(gj).area / min(g.area, gj.area)
            if 0.33 <= ra <= 3.0 and (inter >= 0.5 or (gj.buffer(10).contains(cents[i]) and g.buffer(10).contains(cents[j]))):
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
                if k == 0 and maps:
                    bm = max(maps, key=lambda m: m["p"]["rect_fill"] + (1.0 if by_name[m["src"]].trusted else 0.0))
                    tracks[-1]["map_geom"], tracks[-1]["outline_src"] = rectish(bm["geom"]), bm["src"]
        else:
            best = max(maps, key=lambda m: m["p"]["rect_fill"] + (1.0 if by_name[m["src"]].trusted else 0.0))
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
    json.dump([dict(geom=mapping(to_wgs(t["geom"])), map_geom=None if t.get("map_geom") is None else mapping(to_wgs(t["map_geom"])), borough=t["borough"],
                    osm=None if t["osm"] is None else dict(id=t["osm"]["id"], name=t["osm"]["name"], tags=t["osm"]["tags"], record=t["osm"].get("record")),
                    outline_src=t.get("outline_src"), n_maps=len(t["maps"]), best_rect=max([m["p"]["rect_fill"] for m in t["maps"]], default=None),
                    ocean=max([m["f"]["ocean"] for m in t["maps"]], default=0), map_srcs=sorted({m["src"] for m in t["maps"]}), obs=t["obs"]) for t in tracks],
              open(E.OUT / "tracks.json", "w"))
    print("tracks.json written")


if __name__ == "__main__":
    main()
