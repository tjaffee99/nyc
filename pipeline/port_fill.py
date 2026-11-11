"""Generated structures for working yards: container stacks in the container terminals and rail cars in
the rail yards (data/manual/ports/README.md has the rules, the sources and what is real).

A container terminal is bare paved ground in every dataset: containers, cranes and rail cars are not
buildings. The terminal and its opening year are real (data/manual/ports/terminals.geojson, cited);
what stands on it is generated: blocks of stacked containers on the free yard, rows on the bearing of the
quay. Rail yards (yards.geojson) get rows of cars along the yard tracks of rail.parquet.

    python port_fill.py inputs     # write terminals.geojson / yards.geojson from the OSM land-use outlines (once)
    python port_fill.py            # terminals + yards -> data/interim/gapfill/gapfill_ports.parquet
    python port_fill.py check      # the invariants, counts per terminal / yard, standing counts
    python port_fill.py empty      # the 25 largest building-free paved / industrial patches (report only)

Output columns are those of gapfill_sites.parquet minus `site`. Deterministic: every choice is a hash of
the terminal id and the position (blake2b), no random generator.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box, shape, mapping
from shapely.ops import substring, unary_union
from shapely.prepared import prep
from shapely.strtree import STRtree

from common import INTERIM, MANUAL, RAW, OVERTURE_RELEASE, STILL_EXISTS

CRS_M = "EPSG:32618"
OV = RAW / "overture" / OVERTURE_RELEASE
PORTS = MANUAL / "ports"
WORK = INTERIM / "ports"
OUT = INTERIM / "gapfill" / "gapfill_ports.parquet"
WORK.mkdir(parents=True, exist_ok=True)

# ---- constants: every size and the fact it comes from ------------------------------------------------
TEU_LEN = 6.06            # m, a 20-foot ISO container (ISO 668)
FEU_LEN = 12.19           # m, a 40-foot ISO container (ISO 668): blocks and pieces are multiples of it
BOX_W = 2.44              # m, container width (ISO 668: 8 ft)
BOX_H = 2.59              # m, container height (ISO 668: 8 ft 6 in = 2.59 m; 2.6 used)
BLOCK_ROWS = 6            # containers side by side in a block: a rubber-tyred-gantry yard spans 6 rows + a lane
BLOCK_W = BLOCK_ROWS * BOX_W          # 14.6 m
BLOCK_LEN_FEU = (5, 20)   # a block is 5-20 forty-foot lengths: 61-244 m (brief: 60-250 m)
PIECE_FEU = (2, 4)        # a block is cut into pieces of 2-4 container lengths, each its own height
STACK_HIGH = (2, 5)       # containers high (brief; RTG yards stack 4-5 high, empties more)
AISLE = (8.0, 26.0)       # m between block rows (RTG travel lanes, truck lanes; brief)
CROSS_AISLE = (FEU_LEN, 2 * FEU_LEN)  # m between blocks of a row
BUILDING_MARGIN = 6.0     # m kept clear of today's buildings (brief)
QUAY_APRON = 35.0         # m left clear along the water: the cranes' rail gauge (30.5 m) plus a lane (brief)
ROAD_HALF = {"motorway": 12, "trunk": 10, "primary": 9, "secondary": 7, "tertiary": 6, "unclassified": 5,
             "residential": 4.5, "service": 4, "living_street": 3.5}   # m, half carriageway, assumed
ROAD_MARGIN = 3.0         # m clear of the roadway edge
RAIL_HALF = 2.5           # m, half the 5 m a single track and its ballast take
RAIL_MARGIN = 3.0         # m clear of the rail
CLIP_KEEP = 0.85          # a piece cut by an obstacle is kept if this share of it is free
SHRINK = 0.15             # m taken off every side of a piece so neighbouring pieces do not touch
OPEN_SPREAD = 9.0         # years over which a terminal's stacks appear after the opening, quay inland (brief)
CLOSE_SPREAD = 1.0        # years over which a closed terminal's stacks go
MIN_PIECE_AREA = 2 * FEU_LEN * 6 * BOX_W * 0.9
CAR_W = 3.0               # m, a freight car (brief; AAR plate B)
CAR_H = 4.0               # m (brief)
CAR_LEN = (18.0, 26.0)    # m (brief)
SUBWAY_CAR_LEN = (15.5, 22.9)  # m: A Division 15.5 m, B Division 18.3-22.9 m (R-type specifications)
CAR_GAP = 0.8             # m between coupled cars
RUN_CARS = (3, 10)        # cars in a run (brief)
YARD_COVER = 0.40         # share of track length that holds cars (brief)
YARD_SPREAD = 5.0         # years after the yard opens over which its cars appear
CAR_CLEAR_BUILDING = 1.5  # m kept off buildings
SUBWAY_YARDS = {"coney_island_yard", "yard_207th_street", "jamaica_yard", "corona_yard", "livonia_yard",
                "pitkin_yard", "concourse_yard", "canarsie_yard", "east_new_york_yard", "yard_239th_street",
                "unionport_yard", "morris_park_shops"}

TERM_BAND = {"newark_lat": 40.6835}   # Port Newark north of it, Port Elizabeth south (the slip between)


def h01(*parts) -> float:
    """Deterministic number in [0, 1) from the parts."""
    d = hashlib.blake2b("|".join(map(str, parts)).encode(), digest_size=8).digest()
    return int.from_bytes(d, "big") / 2 ** 64


def hrange(lo, hi, *parts):
    return lo + (hi - lo) * h01(*parts)


def hint(lo, hi, *parts):
    return int(lo + math.floor((hi - lo + 1) * h01(*parts)))


def con():
    c = duckdb.connect()
    c.execute("install spatial; load spatial; SET geometry_always_xy=true; SET memory_limit='1500MB'")
    return c


def gdf_from(c, sql):
    import time
    for attempt in range(40):          # the lead rewrites the building files during a rebuild: wait and retry
        try:
            df = c.execute(sql).df()
            break
        except duckdb.InvalidInputException:
            time.sleep(30)
    else:
        raise RuntimeError("building file unreadable")
    if not len(df):
        return gpd.GeoDataFrame(df.drop(columns="g", errors="ignore"), geometry=[], crs=4326)
    return gpd.GeoDataFrame(df.drop(columns="g"), geometry=gpd.GeoSeries.from_wkb(df.g.apply(bytes)), crs=4326)


def env_sql(b):
    return f"ST_MakeEnvelope({b[0]},{b[1]},{b[2]},{b[3]})"


# ---- inputs: terminals and yards -----------------------------------------------------------------------
# Each terminal: OSM land-use polygons (Overture ids, prefix) unioned; `minus` = polygons cut out of it;
# `lat_min` / `lat_max` clip a band. Years: `open` the first year of container handling; `periods` for a
# terminal that stood idle; year_basis says whether the year is read from a source or estimated.
TERMINALS = [
    dict(id="port_newark", name="Port Newark (container berths and yards)", operator="Port Authority of NY & NJ; Port Newark Container Terminal (Ports America) and others",
         polys=["69600123", "2dc025bb", "3fba567a", "cddcc407"], minus=["a35b024a", "abcfa8da", "12eb7e92", "2ddaa4c7"], lat_min=TERM_BAND["newark_lat"],
         periods=[[1956, 9999]], year_basis="source",
         source="https://en.wikipedia.org/wiki/Port_Newark%E2%80%93Elizabeth_Marine_Terminal",
         basis="Malcom McLean's Ideal X sailed from Port Newark on 26 April 1956, the first container voyage; the years of the many later berths are not separately sourced: all take 1956, the stacks spread over the ten years after.",
         outline="OpenStreetMap land use (Overture base_land_use): 'Port Newark-Elizabeth' with the Port Newark Container Terminal, Red Hook Terminal and C&C Yard 1 polygons, north of 40.6835 N, less the Maher, APM and Columbia polygons"),
    dict(id="elizabeth_pamt", name="Elizabeth-Port Authority Marine Terminal (Sea-Land's terminal and the rest of the Elizabeth side)", operator="Sea-Land (1962); today APM Terminals and Columbia Container Services share it with Maher",
         polys=["69600123", "abcfa8da", "12eb7e92", "2ddaa4c7"], minus=["a35b024a", "2dc025bb"], lat_max=TERM_BAND["newark_lat"],
         periods=[[1962, 9999]], year_basis="source",
         source="https://en.wikipedia.org/wiki/Port_of_New_York_and_New_Jersey",
         basis="'The nation's first facility for container shipping, which became the prototype, opened in 1962' (Port of New York and New Jersey); Sea-Land's Elizabeth terminal.",
         outline="OpenStreetMap land use: 'Port Newark-Elizabeth' south of 40.6835 N with the APM Terminals and Columbia Container Services polygons, less Maher"),
    dict(id="maher", name="Maher Terminals", operator="Maher Terminals", polys=["a35b024a"], minus=[], periods=[[1963, 9999]], year_basis="estimated",
         source="https://en.wikipedia.org/wiki/Port_Newark%E2%80%93Elizabeth_Marine_Terminal",
         basis="Maher is listed as a major operator in 2009; its opening year was not found in a source read here: 1963, the year after the first Elizabeth berths, is an estimate.",
         outline="OpenStreetMap land use: 'Maher Terminals'"),
    dict(id="port_jersey_bayonne", name="Port Jersey / Global Container Terminal Bayonne (Port Liberty Bayonne)", operator="Port Authority of NY & NJ; Global Container Terminals; CMA CGM since 2023",
         polys=["e781535f"], minus=[], periods=[[1977, 9999]], year_basis="estimated",
         source="https://en.wikipedia.org/wiki/Port_Jersey",
         basis="'The pier was created using landfill' 1972-1976 (Wikipedia, Port Jersey); the year container handling began is not in the article: 1977, the year after the pier, is an estimate.",
         outline="OpenStreetMap land use: 'Port Liberty Bayonne'"),
    dict(id="howland_hook", name="Howland Hook Marine Terminal / GCT New York (Port Liberty New York)", operator="United States Lines (1973-86); Port Authority from 1985; Global Container Terminals; CMA CGM since 2023",
         polys=["5ae57a65"], minus=[], periods=[[1973, 1987], [1996, 9999]], year_basis="source",
         source="https://en.wikipedia.org/wiki/Howland_Hook_Marine_Terminal",
         basis="Built by American Export Lines, 1949; 'United States Lines moved its container port operation there in 1973'; the Port Authority leased it in 1985; the terminal stood idle after United States Lines failed in 1986 and reopened in 1996 (the owner's brief; the reopening year was not checked in a second source).",
         outline="OpenStreetMap land use: 'Port Liberty New York'"),
    dict(id="red_hook", name="Red Hook Container Terminal", operator="Port Authority of NY & NJ; Red Hook Container Terminal LLC; City of New York since 2024",
         polys=["21c69de8"], minus=[], periods=[[1981, 9999]], year_basis="source",
         source="https://en.wikipedia.org/wiki/Red_Hook_Container_Terminal",
         basis="'The container terminal was built in the 1980s' (Wikipedia); 1981 is the owner's brief.",
         outline="OpenStreetMap land use: 'Red Hook Container Terminal'"),
    dict(id="south_brooklyn_mt", name="South Brooklyn Marine Terminal", operator="Port Authority of NY & NJ / NYC Economic Development Corporation",
         polys=["e46d5967"], minus=[], periods=[[1972, 9999]], year_basis="estimated",
         source="https://en.wikipedia.org/wiki/Port_of_New_York_and_New_Jersey",
         basis="Listed among the port's bulk and marine-transfer sites; no container opening year was found: 1972 is an estimate and the terminal handles mainly break-bulk, so the stacks here are the least certain.",
         outline="OpenStreetMap land use: 'South Brooklyn Marine Terminal'"),
]
YARDS_OSM = [  # yards not in data/manual/sites: id, name, Overture land-use id prefix, year, source, basis
    dict(id="oak_island_yard", name="Oak Island Yard", oid="a9bcfc65", start_year=1903, year_basis="source",
         source="https://en.wikipedia.org/wiki/Oak_Island_Yard", basis="'The yard was built by the Lehigh Valley Railroad and opened 1903.'"),
]


def load_osm_polys(c, ids):
    allp = {}
    L = f"'{OV}/base_land_use.parquet'"
    for i in ids:
        r = c.execute(f"select ST_AsWKB(geometry) g, id from {L} where id like '{i}%'").df()
        if not len(r):
            r = c.execute(f"select ST_AsWKB(geometry) g, id from '{OV}/region5_land_use.parquet' where id like '{i}%'").df()
        allp[i] = shapely.from_wkb(bytes(r.g[0]))
    return allp


def make_inputs():
    c = con()
    ids = {i for t in TERMINALS for i in t["polys"] + t["minus"]} | {y["oid"] for y in YARDS_OSM}
    P = load_osm_polys(c, ids)
    feats = []
    for t in TERMINALS:
        g = unary_union([P[i] for i in t["polys"]])
        for i in t["minus"]:
            g = g.difference(P[i])
        if "lat_min" in t:
            g = g.intersection(box(-75, t["lat_min"], -73, 41))
        if "lat_max" in t:
            g = g.intersection(box(-75, 40, -73, t["lat_max"]))
        if g.geom_type != "Polygon":
            g = max(g.geoms, key=lambda p: p.area) if hasattr(g, "geoms") else g
        props = {k: t[k] for k in ("id", "name", "operator", "periods", "year_basis", "source", "basis", "outline")}
        props["kind"] = "container_terminal"
        feats.append({"type": "Feature", "properties": props, "geometry": mapping(g)})
    (PORTS / "terminals.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    # yards: the rail yards of data/manual/sites (kind rail_yard, still there) + OSM ones
    sites = json.load(open(MANUAL / "sites" / "sites.geojson"))
    yf = []
    for f in sites["features"]:
        p = f["properties"]
        if p.get("kind") == "rail_yard" and p["end_year"] >= STILL_EXISTS:
            yf.append({"type": "Feature", "geometry": f["geometry"], "properties": {
                "id": p["id"], "name": p["name"], "start_year": p["start_year"], "year_basis": "source" if p.get("date_basis") == "text" else "estimated",
                "source": p["source_url"], "basis": p["note"], "outline": "data/manual/sites/sites.geojson",
                "kind": "subway" if p["id"] in SUBWAY_YARDS else "rail"}})
    for y in YARDS_OSM:
        yf.append({"type": "Feature", "geometry": mapping(P[y["oid"]]), "properties": {
            "id": y["id"], "name": y["name"], "start_year": y["start_year"], "year_basis": y["year_basis"], "source": y["source"], "basis": y["basis"],
            "outline": "OpenStreetMap land use (Overture base_land_use) " + y["oid"], "kind": "rail"}})
    (PORTS / "yards.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": yf}))
    print("terminals", len(feats), "yards", len(yf))


# ---- ground ------------------------------------------------------------------------------------------
def window_data(c, geom_m, pad=300.0):
    """Obstacles inside a window (UTM shapely geoms) around a metric polygon."""
    g4 = gpd.GeoSeries([geom_m.buffer(pad)], crs=CRS_M).to_crs(4326).iloc[0]
    b = g4.bounds
    env = env_sql(b)
    out = {}
    bl = []
    for f in ("county_buildings", "nyc_buildings"):
        # (standing buildings only, and no generated row: the built files hold this stage's own
        # containers and cars of the run before - with them as obstacles a rerun stood nothing
        # on the yards that already had cars: decision 38)
        q = gdf_from(c, f"select ST_AsWKB(geometry) g from '{INTERIM}/{f}.parquet' where ST_Intersects(geometry,{env}) "
                        f"and end_year > 9000 and year_confidence <> 'procedural'")
        if len(q):
            bl.append(q.to_crs(CRS_M).geometry)
    out["buildings"] = pd.concat(bl).tolist() if bl else []
    roads = []
    for f in ("roads_local", "roads_region"):
        cls = "class"
        q = gdf_from(c, f"select class cl, ST_AsWKB(geometry) g from '{OV}/{f}.parquet' where ST_Intersects(geometry,{env})")
        if len(q):
            q = q.to_crs(CRS_M)
            roads += [(r.cl, r.geometry) for r in q.itertuples()]
    out["roads"] = roads
    q = gdf_from(c, f"select ST_AsWKB(geometry) g, rail_flags rf, class cl from '{OV}/rail.parquet' where ST_Intersects(geometry,{env})")
    q = q.to_crs(CRS_M) if len(q) else q
    out["rail"] = [(r.cl, str(r.rf), r.geometry) for r in q.itertuples()]
    w = gdf_from(c, f"select ST_AsWKB(geometry) g from '{OV}/base_water.parquet' where ST_Intersects(geometry,{env})")
    out["water"] = unary_union(w.to_crs(CRS_M).geometry.tolist()) if len(w) else Polygon()
    return out


def obstacles(d, rail_cut=True):
    bld = unary_union([b.buffer(BUILDING_MARGIN) for b in d["buildings"]]) if d["buildings"] else Polygon()
    rd = unary_union([g.buffer(ROAD_HALF.get(cl, 5) + ROAD_MARGIN) for cl, g in d["roads"]]) if d["roads"] else Polygon()
    rl = unary_union([g.buffer(RAIL_HALF + RAIL_MARGIN) for cl, rf, g in d["rail"]]) if d["rail"] else Polygon()
    return bld, rd, rl


def quay_bearing(poly, water):
    """Dominant direction (degrees, 0-180, from +x) of the poly's boundary where it meets the water."""
    near = poly.boundary.intersection(water.buffer(4)) if not water.is_empty else Polygon()
    segs = []
    geoms = [near] if near.geom_type == "LineString" else list(getattr(near, "geoms", []))
    for g in geoms:
        if g.geom_type != "LineString":
            continue
        xy = np.asarray(g.coords)
        for a, b in zip(xy[:-1], xy[1:]):
            dx, dy = b - a
            L = math.hypot(dx, dy)
            if L > 5:
                segs.append((math.degrees(math.atan2(dy, dx)) % 180, L))
    if not segs:
        r = poly.minimum_rotated_rectangle
        xy = np.asarray(r.exterior.coords)
        e = max(zip(xy[:-1], xy[1:]), key=lambda ab: math.dist(ab[0], ab[1]))
        return math.degrees(math.atan2(e[1][1] - e[0][1], e[1][0] - e[0][0])) % 180
    ang = np.array([s[0] for s in segs]); w = np.array([s[1] for s in segs])
    # weight each angle by length, histogram in 3-degree bins on the doubled circle
    bins = np.zeros(60)
    for a, L in zip(ang, w):
        bins[int(a // 3) % 60] += L
    sm = bins + np.roll(bins, 1) + np.roll(bins, -1)
    k = int(np.argmax(sm))
    sel = [(a, L) for a, L in segs if abs(((a - (k * 3 + 1.5)) + 90) % 180 - 90) <= 6]
    # circular mean of doubled angles
    sx = sum(L * math.cos(math.radians(2 * a)) for a, L in sel); sy = sum(L * math.sin(math.radians(2 * a)) for a, L in sel)
    return (math.degrees(math.atan2(sy, sx)) / 2) % 180


def pieces_for(tid, free_rot, bbox):
    """Rectangles (in the rotated frame) that lie wholly in the free ground."""
    xmin, ymin, xmax, ymax = bbox
    pf = prep(free_rot)
    out = []
    y = ymin + hrange(0, BLOCK_W + 10, tid, "y0")
    k = 0
    while y < ymax:
        x = xmin + hrange(0, 2 * FEU_LEN, tid, "x0", k)
        j = 0
        while x < xmax:
            n_feu = hint(*BLOCK_LEN_FEU, tid, "L", k, j)
            blen = n_feu * FEU_LEN
            nb = hint(*STACK_HIGH, tid, "H", k, j)
            # cut the block into pieces of 2-4 container lengths
            px, rem = x, blen
            i = 0
            while rem >= PIECE_FEU[0] * FEU_LEN - 1e-6:
                m = min(hint(*PIECE_FEU, tid, "P", k, j, i), int(round(rem / FEU_LEN)))
                if rem - m * FEU_LEN < PIECE_FEU[0] * FEU_LEN - 1e-6:
                    m = int(round(rem / FEU_LEN))      # absorb a short remainder
                L = m * FEU_LEN
                r = box(px + SHRINK, y + SHRINK, px + L - SHRINK, y + BLOCK_W - SHRINK)
                if not pf.contains(r) and pf.intersects(r):      # a rim piece: keep what is free if nearly all of it is
                    cl = free_rot.intersection(r)
                    if cl.geom_type == "Polygon" and cl.area >= CLIP_KEEP * r.area:
                        r = cl.simplify(0.1)
                if pf.contains(r):
                    hh = nb + [-1, 0, 0, 1][hint(0, 3, tid, "d", k, j, i)]
                    hh = min(max(hh, STACK_HIGH[0]), STACK_HIGH[1])
                    out.append((r, hh, k, j, i))
                px += L; rem -= L; i += 1
            x += blen + hrange(*CROSS_AISLE, tid, "ca", k, j)
            j += 1
        y += BLOCK_W + hrange(*AISLE, tid, "ai", k)
        k += 1
    return out


def clean_free(t_poly_m, d):
    land = t_poly_m.difference(d["water"]) if not d["water"].is_empty else t_poly_m
    bld, rd, rl = obstacles(d)
    apron = d["water"].buffer(QUAY_APRON) if not d["water"].is_empty else Polygon()
    free = land.difference(unary_union([bld, rd, rl, apron]))
    return land, free


def build_terminals(c):
    T = json.load(open(PORTS / "terminals.geojson"))["features"]
    rows, stats = [], {}
    for f in T:
        p = f["properties"]; tid = p["id"]
        poly = gpd.GeoSeries([shape(f["geometry"])], crs=4326).to_crs(CRS_M).iloc[0]
        d = window_data(c, poly)
        land, free = clean_free(poly, d)
        theta = quay_bearing(land, d["water"])
        o = poly.centroid
        free_rot = affinity.rotate(free, -theta, origin=o)
        pcs = pieces_for(tid, free_rot, free_rot.bounds)
        wa = d["water"]
        wpre = prep(wa.buffer(0)) if not wa.is_empty else None
        recs = []
        for r, hh, k, j, i in pcs:
            g = affinity.rotate(r, theta, origin=o)
            dq = g.centroid.distance(wa) if not wa.is_empty else 100.0
            recs.append((g, hh, dq, k, j, i))
        if not recs:
            stats[tid] = dict(rows=0); continue
        dmax = float(np.percentile([r[2] for r in recs], 90)) or 1.0
        for (g, hh, dq, k, j, i) in recs:
            frac = min(dq / dmax, 1.0)
            pos = f"{round(g.centroid.x)}_{round(g.centroid.y)}"
            mix = 0.75 * frac + 0.25 * h01(tid, "yr", pos)
            for pi, (a, b) in enumerate(p["periods"]):
                start = a + 1 + OPEN_SPREAD * mix if pi == 0 else a + OPEN_SPREAD * mix
                end = float(STILL_EXISTS) if b >= STILL_EXISTS else b + CLOSE_SPREAD * h01(tid, "end", pos)
                rows.append(dict(id=f"port_{tid}_{pos}" + ("" if pi == 0 else f"_p{pi + 1}"), start_year=round(start, 2), end_year=end,
                                 height_m=round(hh * BOX_H, 1), storeys=int(hh), material="containers", evidence="port+containers",
                                 end_basis="open_today" if b >= STILL_EXISTS else "terminal_closed", area=round(g.area, 1),
                                 geometry=g, terminal=tid))
        stats[tid] = dict(rows=len(recs), theta=round(theta, 1), land_ha=round(land.area / 1e4, 1), free_ha=round(free.area / 1e4, 1),
                          cover_ha=round(sum(r[0].area for r in recs) / 1e4, 1), share_of_free=round(sum(r[0].area for r in recs) / max(free.area, 1), 3))
        print(tid, stats[tid], flush=True)
    return rows, stats


# ---- rail yards --------------------------------------------------------------------------------------
def build_yards(c):
    Y = json.load(open(PORTS / "yards.geojson"))["features"]
    # The waterfront yards that are gone (yards_historic.geojson: the Pennsylvania at Exchange
    # Place and Harsimus Cove, the Erie at Pavonia, the Jersey Central at Communipaw, the Lehigh
    # Valley at Black Tom, the West Shore at Weehawken): no track of theirs is in today's data,
    # so the tracks are drawn - parallel lines at the yard's bearing, every second track of a
    # yard laid at 4.6 m - and the cars stand until the yard closed. Outline and years are
    # researched (data/research/hudson_waterfront.md); tracks and cars are generated.
    hp = PORTS / "yards_historic.geojson"
    if hp.exists():
        for f in json.load(open(hp))["features"]:
            if float(f["properties"].get("end_year", 9999)) < 9000:
                f["properties"]["_lost"] = True
                Y.append(f)
    rows, stats = [], {}
    for f in Y:
        p = f["properties"]; yid = p["id"]
        lost = bool(p.get("_lost"))
        poly = gpd.GeoSeries([shape(f["geometry"])], crs=4326).to_crs(CRS_M).iloc[0].buffer(0)
        d = window_data(c, poly, pad=100)
        lines = []
        if lost:
            br = math.radians(float(p.get("track_bearing_deg", 90)))
            ux, uy = math.sin(br), math.cos(br)            # along the tracks
            px, py = math.cos(br), -math.sin(br)           # across them
            x0, y0, x1, y1 = poly.bounds
            cx, cy, half = (x0 + x1) / 2, (y0 + y1) / 2, math.hypot(x1 - x0, y1 - y0) / 2 + 10
            gap = 2 * max(float(p.get("track_gap_m", 4.6)), 4.6)
            k = -half
            while k <= half:
                ln = LineString([(cx + px * k - ux * half, cy + py * k - uy * half), (cx + px * k + ux * half, cy + py * k + uy * half)])
                gi = ln.intersection(poly.buffer(-4))
                for sgm in ([gi] if gi.geom_type == "LineString" else [x for x in getattr(gi, "geoms", []) if x.geom_type == "LineString"]):
                    if sgm.length > 40:
                        lines.append(sgm)
                k += gap
        for cl, rf, g in ([] if lost else d["rail"]):
            if "is_tunnel" in rf or "is_bridge" in rf:
                continue
            gi = g.intersection(poly)
            for s in ([gi] if gi.geom_type == "LineString" else [x for x in getattr(gi, "geoms", []) if x.geom_type == "LineString"]):
                if s.length > 25:
                    lines.append(s)
        if not lines:
            stats[yid] = dict(rows=0, note="no yard track in the outline"); continue
        bld = unary_union([b.buffer(CAR_CLEAR_BUILDING) for b in d["buildings"]]) if d["buildings"] else Polygon()
        rd = unary_union([g.buffer(ROAD_HALF.get(cl, 5)) for cl, g in d["roads"]]) if d["roads"] else Polygon()
        keep_out = unary_union([bld, rd, d["water"]]) if not d["water"].is_empty else unary_union([bld, rd])
        if lost:
            keep_out = Polygon()       # (today's streets and towers stand where the yard was)
        kp = prep(keep_out)
        lenr = SUBWAY_CAR_LEN if yid in SUBWAY_YARDS else CAR_LEN
        cars = []
        total_len = sum(s.length for s in lines)
        for si, s in enumerate(sorted(lines, key=lambda s: (round(s.centroid.x), round(s.centroid.y)))):
            key = f"{yid}|{round(s.centroid.x)}|{round(s.centroid.y)}"
            n = hint(*RUN_CARS, key, "n", 0)
            runlen = n * (sum(lenr) / 2 + CAR_GAP)
            gap_mean = runlen * (1 - YARD_COVER) / YARD_COVER
            sd = hrange(0, gap_mean, key, "off")
            ri = 0
            while sd < s.length - 8:
                n = hint(*RUN_CARS, key, "n", ri)
                for ci in range(n):
                    L = hrange(*lenr, key, "len", ri, ci)
                    if sd + L > s.length:
                        break
                    A = s.interpolate(sd); B = s.interpolate(sd + L)
                    dx, dy = B.x - A.x, B.y - A.y
                    dd = math.hypot(dx, dy)
                    if dd > 1:
                        nx, ny = -dy / dd * CAR_W / 2, dx / dd * CAR_W / 2
                        g = Polygon([(A.x + nx, A.y + ny), (B.x + nx, B.y + ny), (B.x - nx, B.y - ny), (A.x - nx, A.y - ny)])
                        if poly.contains(g) and not kp.intersects(g):
                            cars.append((g, f"{round(A.x)}_{round(A.y)}"))
                    sd += L + CAR_GAP
                ri += 1
                sd += hrange(0.5, 1.5, key, "gap", ri) * gap_mean
        # drop cars that overlap an earlier one (switches, parallel tracks closer than a car)
        accepted, tree = [], None
        geoms = [g for g, _ in cars]
        tree = STRtree(geoms)
        taken = set()
        for i, g in enumerate(geoms):
            if any(j in taken for j in tree.query(g, predicate="intersects") if j < i):
                continue
            taken.add(i)
        for i in sorted(taken):
            g, pos = cars[i]
            start = p["start_year"] + YARD_SPREAD * h01(yid, "yr", pos)
            end = float(p["end_year"]) + h01(yid, "end", pos) if lost else float(STILL_EXISTS)
            rows.append(dict(id=f"yard_{yid}_{pos}", start_year=round(start, 2), end_year=round(end, 2), height_m=CAR_H, storeys=1,
                             material="railcar", evidence="yard+railcars", end_basis="yard_closed" if lost else "open_today",
                             area=round(g.area, 1), geometry=g, terminal=yid))
        stats[yid] = dict(rows=len(taken), track_m=round(total_len), cover_m=round(sum(geoms[i].area for i in taken) / CAR_W),
                          track_share=round(sum(geoms[i].area for i in taken) / CAR_W / total_len, 3))
        print(yid, stats[yid], flush=True)
    return rows, stats


def run():
    c = con()
    tr, ts = build_terminals(c)
    yr, ys = build_yards(c)
    rows = tr + yr
    g = gpd.GeoDataFrame(rows, geometry="geometry", crs=CRS_M).to_crs(4326)
    g["storeys"] = g.storeys.astype("int64")
    # snap: no row may touch another alive at the same time (checked in `check`); write
    cols = ["id", "start_year", "end_year", "height_m", "storeys", "material", "evidence", "end_basis", "area", "geometry"]
    g[cols].to_parquet(OUT)
    g[["id", "terminal"]].to_parquet(WORK / "row_owner.parquet")
    json.dump({"terminals": ts, "yards": ys}, open(WORK / "stats.json", "w"), indent=1)
    print("wrote", OUT, len(g))


# ---- checks ------------------------------------------------------------------------------------------
def check():
    c = con()
    g = gpd.read_parquet(OUT)
    own = pd.read_parquet(WORK / "row_owner.parquet").set_index("id").terminal
    g["owner"] = g.id.map(own)
    gm = g.to_crs(CRS_M)
    rep = {"rows": len(g), "start_ge_end": int((g.start_year >= g.end_year).sum()), "duplicate_ids": int(g.id.duplicated().sum()),
           "storeys_range": [int(g.storeys.min()), int(g.storeys.max())]}
    per = {}
    for oid, sub in gm.groupby("owner"):
        hull = unary_union(sub.geometry.tolist()).convex_hull
        d = window_data(c, hull, pad=60)
        bt = STRtree(d["buildings"]) if d["buildings"] else None
        nb = 0
        if bt is not None:
            for geom in sub.geometry:
                if any(d["buildings"][j].intersection(geom).area > 0.01 for j in bt.query(geom, predicate="intersects")):
                    nb += 1
        # container rows: roads (centre line), rail; railcar rows: roads only; both: water
        cont = sub.material.iloc[0] == "containers"
        rt = STRtree([r[1] for r in d["roads"]]) if d["roads"] else None
        nr = sum(1 for geom in sub.geometry if rt is not None and len(rt.query(geom, predicate="intersects")))
        rl = STRtree([r[2] for r in d["rail"]]) if d["rail"] else None
        nl = sum(1 for geom in sub.geometry if rl is not None and len(rl.query(geom, predicate="intersects"))) if cont else None
        nw = int(sum(d["water"].intersects(geom) for geom in sub.geometry)) if not d["water"].is_empty else 0
        per[oid] = dict(rows=len(sub), ha=round(sub.area.sum() / 1e4, 2), with_building=nb, on_road_centre=nr, on_rail=nl, in_water=nw)
    rep["per_owner"] = per
    # overlaps between rows alive at the same time
    geoms = gm.geometry.tolist(); tree = STRtree(geoms)
    a, b = tree.query(geoms, predicate="intersects")
    sy, ey = g.start_year.values, g.end_year.values
    bad = 0
    for i, j in zip(a, b):
        if i < j and shapely.area(shapely.intersection(geoms[i], geoms[j])) > 0.01 and max(sy[i], sy[j]) < min(ey[i], ey[j]):
            bad += 1
    rep["overlapping_pairs_alive_together"] = bad
    rep["standing"] = {}
    for yv in (1950, 1965, 1980, 2000, 2026):
        m = (g.start_year <= yv) & (g.end_year > yv)
        rep["standing"][yv] = dict(containers=int((m & (g.material == "containers")).sum()), railcars=int((m & (g.material == "railcar")).sum()))
    json.dump(rep, open(WORK / "check.json", "w"), indent=1)
    print(json.dumps(rep, indent=1))


# ---- what else is empty --------------------------------------------------------------------------------
def empty(n=25, min_ha=5.0, open_m=8.0):
    from common import REGION_BBOX
    c = con()
    L = f"'{OV}/region5_land_use.parquet'"
    df = c.execute(f"select id, subtype, class, name, ST_AsWKB(geometry) g from {L} where subtype in ('developed','construction','transportation') "
                   f"and ST_Intersects(geometry,{env_sql(REGION_BBOX)}) and ST_Area_Spheroid(geometry)>{min_ha*1e4}").df()
    cand = gpd.GeoDataFrame(df.drop(columns="g"), geometry=gpd.GeoSeries.from_wkb(df.g.apply(bytes)), crs=4326).to_crs(CRS_M)
    mine = unary_union([shape(f["geometry"]) for f in json.load(open(PORTS / "terminals.geojson"))["features"] + json.load(open(PORTS / "yards.geojson"))["features"]]
                       if False else [gpd.GeoSeries([shape(f["geometry"])], crs=4326).to_crs(CRS_M).iloc[0]
                                      for f in json.load(open(PORTS / "terminals.geojson"))["features"] + json.load(open(PORTS / "yards.geojson"))["features"]])
    air = gdf_from(c, f"select ST_AsWKB(geometry) g from '{OV}/region_airports.parquet'")
    air = unary_union(air.to_crs(CRS_M).geometry.tolist()) if len(air) else Polygon()
    skip = unary_union([mine, air.buffer(30)])
    MAP_FIPS = {"36005", "36047", "36061", "36081", "36085", "34017", "34003", "34013", "34039", "34031", "36119", "36087"}  # 5 boroughs + 7 counties
    cty0 = gpd.read_file(RAW / "tiger" / "tl_2024_us_county.zip", bbox=tuple(REGION_BBOX)).to_crs(CRS_M)
    in_map = unary_union(cty0[(cty0.STATEFP + cty0.COUNTYFP).isin(MAP_FIPS)].geometry.tolist())
    cand = cand[[in_map.contains(g.representative_point()) for g in cand.geometry]]
    print(len(cand), "candidate land-use polygons in the map", flush=True)
    res = []
    for r in cand.itertuples():
        if r.geometry.intersection(skip).area > 0.5 * r.geometry.area:
            continue
        w = gpd.GeoSeries([r.geometry.buffer(20)], crs=CRS_M).to_crs(4326).iloc[0].bounds
        env = env_sql(w)
        bl = []
        for f in ("county_buildings", "nyc_buildings"):
            q = gdf_from(c, f"select ST_AsWKB(geometry) g from '{INTERIM}/{f}.parquet' where ST_Intersects(geometry,{env})")
            if len(q):
                bl += q.to_crs(CRS_M).geometry.tolist()
        rd = gdf_from(c, f"select class cl, ST_AsWKB(geometry) g from '{OV}/roads_local.parquet' where ST_Intersects(geometry,{env})")
        rds = [g.buffer(ROAD_HALF.get(cl, 5)) for cl, g in zip(rd.cl, rd.to_crs(CRS_M).geometry)] if len(rd) else []
        free = r.geometry.difference(unary_union([b.buffer(BUILDING_MARGIN) for b in bl] + rds + [skip]))
        free = free.buffer(-open_m).buffer(open_m)
        if len(res) % 20 == 0:
            print("  ...", r.Index, len(res), flush=True)
        for p in ([free] if free.geom_type == "Polygon" else list(getattr(free, "geoms", []))):
            if p.area >= 3e4:
                res.append(dict(ha=p.area / 1e4, id=r.id, subtype=r.subtype, cls=r.cls if hasattr(r, "cls") else r[3], name=r.name, geometry=p))
    gg = gpd.GeoDataFrame(res, geometry="geometry", crs=CRS_M).sort_values("ha", ascending=False)
    # drop duplicates from overlapping land-use polygons
    keep, seen = [], []
    for row in gg.itertuples():
        if any(row.geometry.intersection(s).area > 0.3 * row.geometry.area for s in seen):
            continue
        seen.append(row.geometry); keep.append(row.Index)
    top = gg.loc[keep].head(n).copy()
    cty = gpd.read_file(RAW / "tiger" / "tl_2024_us_county.zip", bbox=tuple(REGION_BBOX))
    cty = cty.to_crs(CRS_M)
    top["county"] = [next((f"{x.NAME} ({x.STATEFP})" for x in cty.itertuples() if x.geometry.contains(g.representative_point())), "") for g in top.geometry]
    ll = top.to_crs(4326)
    top["lon"] = [round(p.representative_point().x, 4) for p in ll.geometry]; top["lat"] = [round(p.representative_point().y, 4) for p in ll.geometry]
    out = top.drop(columns="geometry")
    out.to_csv(WORK / "largest_empty.csv", index=False)
    print(out.to_string())


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "inputs":
        make_inputs()
    elif cmd == "run":
        run()
    elif cmd == "check":
        check()
    elif cmd == "empty":
        empty()
