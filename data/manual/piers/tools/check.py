"""Checks on data/manual/piers/piers.geojson (run after dates.py).  Prints one line per check; exits 1 on a failure.

 1. format: every property of the brief present, qualities in their vocabulary, start < end, years in 1600..2026 / 9999
 2. geometry: valid polygons, inside the five counties, 100 m2 or more, long and thin or an OpenStreetMap outline
 3. no two piers on one spot at once (overlap of 40 % of the smaller while both stand)
 4. ground: share of each vanished outline on land that the terrain grid makes before the pier's start (must be
    under 60 %), and how many outlines touch land of their years at all (reported: a pier root always does)
 5. known answers: named piers against the dates they should carry
"""
import json
import sys
from collections import Counter
from pathlib import Path

import geopandas as gpd
import numpy as np
import pyproj
import rasterio
import shapely
from shapely.geometry import shape
from shapely.strtree import STRtree

ROOT = Path("/home/user/nyc")
HERE = Path(__file__).resolve().parents[1]
UTM = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)
to_utm = lambda g: shapely.transform(g, lambda c: np.column_stack(UTM.transform(c[:, 0], c[:, 1])))
fails = 0


def report(name, bad, total, detail=""):
    global fails
    ok = not bad
    fails += 0 if ok else 1
    print(f"{'ok  ' if ok else 'FAIL'} {name}: {len(bad) if hasattr(bad, '__len__') else bad} of {total} {detail}")
    if not ok:
        print("     ", list(bad)[:8])


F = json.load(open(HERE / "piers.geojson"))["features"]
P = [f["properties"] for f in F]
G = [to_utm(shape(f["geometry"])) for f in F]
need = ["id", "name", "start_year", "end_year", "start_quality", "end_quality", "shed", "deck_m", "source", "source_url", "note", "borough"]
report("properties present", [p["id"] for p in P if any(k not in p for k in need)], len(P))
report("ids unique", [k for k, v in Counter(p["id"] for p in P).items() if v > 1], len(P))
report("qualities", [p["id"] for p in P if p["start_quality"] not in ("recorded", "bracket", "estimated") or p["end_quality"] not in ("recorded", "bracket", "estimated")], len(P))
report("shed vocabulary", [p["id"] for p in P if p["shed"] not in ("none", "shed", "headhouse")], len(P))
report("shed has a height", [p["id"] for p in P if p["shed"] != "none" and not p.get("shed_m")], len(P))
report("start year present", [p["id"] for p in P if p["start_year"] is None], len(P))
report("start < end", [p["id"] for p in P if p["start_year"] is not None and not p["start_year"] < p["end_year"]], len(P))
report("years in range", [p["id"] for p in P if p["start_year"] is not None and not (1600 <= p["start_year"] <= 2026 and (p["end_year"] == 9999 or 1600 < p["end_year"] <= 2026))], len(P))
report("shed years inside the pier's", [p["id"] for p in P if (p.get("shed_end") and not (p["start_year"] or 0) < p["shed_end"] <= (p["end_year"] if p["end_year"] != 9999 else 2027)) or
                                      (p.get("shed_start") and not (p["start_year"] or 0) <= p["shed_start"] < p["end_year"])], len(P))
report("every date has its source in the note", [p["id"] for p in P if len(p["note"]) < 20 or not p["source_url"].startswith("http")], len(P))
report("valid polygons", [p["id"] for p, g in zip(P, G) if not g.is_valid or g.is_empty or g.geom_type not in ("Polygon", "MultiPolygon")], len(P))
city = shapely.unary_union(list(gpd.read_file(ROOT / "data/interim/piers/boroughs.gpkg").to_crs("EPSG:32618").geometry))
report("inside the five counties", [p["id"] for p, g in zip(P, G) if not city.contains(g.centroid)], len(P))
report("100 m2 or more", [p["id"] for p, g in zip(P, G) if g.area < 100], len(P))


def dims(g):
    c = np.array(g.minimum_rotated_rectangle.exterior.coords)[:4]
    a, b = np.hypot(*(c[1] - c[0])), np.hypot(*(c[2] - c[1]))
    return max(a, b), min(a, b)


report("map outlines are long and thin (length >= 1.4 x width, width <= 105 m)",
       [p["id"] for p, g in zip(P, G) if p["source"] != "osm" and not (dims(g)[0] >= 1.35 * dims(g)[1] and dims(g)[1] <= 105)], sum(p["source"] != "osm" for p in P))
tree = STRtree(G)
clash = []
for i, g in enumerate(G):
    for j in tree.query(g):
        j = int(j)
        if j <= i:
            continue
        if g.intersection(G[j]).area >= 0.4 * min(g.area, G[j].area) and min(P[i]["end_year"], P[j]["end_year"]) - max(P[i]["start_year"] or 0, P[j]["start_year"] or 0) > 1:
            clash.append((P[i]["id"], P[j]["id"]))
report("no two piers on one spot at once", clash, len(P))

# ground
gm = json.load(open(ROOT / "data/interim/grid_detail_meta.json"))
ly = np.load(ROOT / "data/interim/grid_detail_landyear.npy")
gtr = rasterio.Affine(*gm["transform"])
wm = pyproj.Transformer.from_crs("EPSG:32618", "EPSG:3857", always_xy=True)
bad, touch = [], 0
for p, g in zip(P, G):
    if p["end_year"] == 9999 or p["start_year"] is None:
        continue
    x0, y0, x1, y1 = g.bounds
    xs, ys = np.meshgrid(np.arange(x0 + 3, x1, 6.0), np.arange(y0 + 3, y1, 6.0))
    m = shapely.contains_xy(g, xs.ravel(), ys.ravel())
    if not m.any():
        continue
    X, Y = wm.transform(xs.ravel()[m], ys.ravel()[m])
    c, r = ~gtr * (np.array(X), np.array(Y))
    v = ly[np.clip(r.astype(int), 0, ly.shape[0] - 1), np.clip(c.astype(int), 0, ly.shape[1] - 1)]
    share = float(np.mean(v <= p["start_year"]))
    touch += bool(np.any(v < p["end_year"]))
    if share > 0.6:
        bad.append(p["id"])
report("vanished piers on land older than themselves (terrain grid, > 60 % of the outline)", bad, sum(p["end_year"] != 9999 for p in P),
       f"; {touch} outlines touch a cell that is made land before their end (roots, and fills the maps date later than the terrain)")

# known answers
byname = {}
for p in P:
    byname.setdefault((p["borough"], p["name"]), []).append(p)
known = [("Manhattan", "Pier A", 1885, 9999), ("Manhattan", "Pier 40", 1962, 9999), ("Manhattan", "Pier 57", 1954, 9999), ("Manhattan", "Pier 57 (earlier pier)", 1907, 1947),
         ("Manhattan", "Pier 59 (Chelsea Piers)", 1910, 9999), ("Manhattan", "Pier 88", 1937, 9999), ("Manhattan", "Little Island (Pier 55)", 2021, 9999),
         ("Brooklyn", "Pier 3 (Brooklyn Bridge Park)", 1960, 9999), ("Brooklyn", "Canarsie Pier", 1926, 9999), ("Brooklyn", "Steeplechase Pier", 1958, 9999),
         ("Staten Island", "Homeport Pier (Naval Station New York)", 1990, 9999)]
miss = [k[:2] for k in known if not any(abs(p["start_year"] - k[2]) < 0.6 and p["end_year"] == k[3] for p in byname.get(k[:2], []))]
report("named piers carry their researched dates", miss, len(known))
print("features", len(P), "| standing", sum(p["end_year"] == 9999 for p in P), "| vanished", sum(p["end_year"] != 9999 for p in P))
sys.exit(1 if fails else 0)
