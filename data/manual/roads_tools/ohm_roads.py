"""Vanished roads traced in OpenHistoricalMap (CC0): data/raw/roads/ohm/highways_enddate.json (Overpass:
way[highway][end_date] in the map box) -> rows for data/manual/routes.csv (mode `road`).

Kept: road-like ways inside the five boroughs, at least 150 m long, begun before 1870 (colonial and pre-grid
roads) or named in KEEP_NAMES, whose line is mostly (>= 60 %) NOT on a road of today (within 15 m): a renamed
or rebuilt street is carried by today's street, a vanished line is drawn from OHM's.
Years: OHM's start_date / end_date. OHM marks many of them `arbitrary` (a placeholder 1600 start on the old
town roads of Kings County; an end near the date of the map the line was traced from): a placeholder start
becomes 1704 — the year the colony's highway act had the King's Highway and the county's public roads laid
out — and both are flagged `estimated` in the note."""
import json
import math

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from shapely.geometry import LineString

import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OV = f"{ROOT}/data/raw/overture/2026-10-21.0"
ROADLIKE = {"unclassified", "residential", "tertiary", "secondary", "primary", "trunk", "living_street", "road", "track"}
KEEP_NAMES = {"Long Island Motor Parkway"}
# way 198423801 crosses the north of Central Park but is end-dated 1902 (the park was laid out there by 1863)
DROP = {198423801}
# OHM leaves the old Bloomingdale Road unnamed (W 86th St to Manhattanville) and estimates its start
# Bloomingdale Road: opened 1703; from 1868 the Boulevard (Broadway) was laid out on a straighter line
# (https://en.wikipedia.org/wiki/Broadway_(Manhattan)); OHM: start estimated, end "almost certainly before 1902"
YEARS = {198783226: (1703.0, 1868.0)}
RENAME = {198783226: "Bloomingdale Road (old line, 86th St - Manhattanville)"}
PLACEHOLDER_START = 1704.0


def year(s):
    s = (s or "").strip()
    try:
        p = s.split("-")
        y = float(p[0])
        if len(p) > 1:
            y += (int(p[1]) - 1) / 12
        if len(p) > 2:
            y += (int(p[2]) - 1) / 365
        return round(y, 2)
    except Exception:  # noqa: BLE001
        return None


def rows(G=None, verbose=False):
    to_utm = Transformer.from_crs(4326, "EPSG:32618", always_xy=True)
    to_ll = Transformer.from_crs("EPSG:32618", 4326, always_xy=True)
    cache = f"{ROOT}/data/raw/roads/ohm/highways_enddate.json"
    if not os.path.exists(cache):  # OpenHistoricalMap Overpass (CC0): every highway way with an end date in the map box
        import requests
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        q = '[out:json][timeout:240];way["highway"]["end_date"](40.47,-74.29,40.94,-73.67);out tags geom;'
        ca = "/root/.ccr/ca-bundle.crt"
        r = requests.post("https://overpass-api.openhistoricalmap.org/api/interpreter", data={"data": q}, timeout=300,
                          headers={"User-Agent": "NYCThroughTime-research/0.1"}, verify=ca if os.path.exists(ca) else True)
        r.raise_for_status()
        open(cache, "wb").write(r.content)
    els = json.load(open(cache))["elements"]
    co = gpd.read_file(f"zip://{ROOT}/data/raw/tiger/tl_2024_us_county.zip", where="STATEFP = '36'")
    city = shapely.union_all(co[co.COUNTYFP.isin(["061", "005", "047", "081", "085"])].to_crs(4326).geometry.values)
    shapely.prepare(city)
    today = pd.concat([gpd.read_parquet(f"{OV}/{f}.parquet", columns=["geometry"]) for f in ("roads_region", "roads_local")])
    today = gpd.GeoSeries(today.geometry.values).to_crs("EPSG:32618")
    tree = shapely.STRtree(today.values)
    out, stats = [], []
    for e in els:
        t = e.get("tags", {})
        if t.get("highway") not in ROADLIKE or e["id"] in DROP:
            continue
        g = e["geometry"]
        lon = [p["lon"] for p in g]
        lat = [p["lat"] for p in g]
        if len(lon) < 2 or not shapely.contains(city, shapely.Point(lon[len(lon) // 2], lat[len(lat) // 2])):
            continue
        y0, y1 = year(t.get("start_date")), year(t.get("end_date"))
        if y1 is None:
            continue
        name = RENAME.get(e["id"], t.get("name", ""))
        if e["id"] in YEARS:
            y0, y1 = YEARS[e["id"]]
        arbitrary0 = t.get("start_date:source", "").startswith("arbitrary") or y0 is None or y0 <= 1600
        if arbitrary0:
            y0 = PLACEHOLDER_START
        if not (y0 < 1870 or name in KEEP_NAMES) or y1 <= y0 + 1:
            continue
        x, y = to_utm.transform(lon, lat)
        line = LineString(np.column_stack([x, y]))
        if line.length < 150:
            continue
        n = max(3, int(line.length // 20))
        pts = shapely.line_interpolate_point(line, np.linspace(0, line.length, n))
        # share of the line that runs ALONG a road of today (within 15 m and within ~25 degrees of its
        # direction: crossing the street grid does not count)
        dd = np.linspace(0, line.length, n)
        pair = tree.query_nearest(pts, max_distance=15, all_matches=False)
        hits = 0
        for k, j in zip(pair[0], pair[1]):
            road = today.values[j]
            s0 = road.project(pts[k])
            a, b = road.interpolate(max(s0 - 6, 0)), road.interpolate(min(s0 + 6, road.length))
            p, q = line.interpolate(max(dd[k] - 6, 0)), line.interpolate(min(dd[k] + 6, line.length))
            u = np.array([b.x - a.x, b.y - a.y])
            v = np.array([q.x - p.x, q.y - p.y])
            if abs(u @ v) > 0.9 * max(np.linalg.norm(u) * np.linalg.norm(v), 1e-9):
                hits += 1
        on = hits / n
        if on > 0.4:
            continue
        line = line.simplify(4.0)
        lo, la = to_ll.transform(*np.asarray(line.coords).T[:2])
        arbitrary1 = "arbitrary" in t.get("end_date:source", "") or "arbitrary" in t.get("note", "") or "fixme" in t
        if e["id"] in YEARS:
            arbitrary0 = False
        note = f"Traced in OpenHistoricalMap (way {e['id']}, CC0)"
        src = t.get("source:name") or t.get("source") or ""
        if src:
            note += f" from: {src[:110]}"
        note += "."
        if arbitrary0:
            note += (" Start estimated: OHM's start date is a placeholder; 1704 is the year the colonial highway act had the "
                     "King's Highway and the county's public roads laid out (the road itself is older).")
        if arbitrary1:
            note += " End estimated: OHM's end date is approximate (about the date of the map that no longer shows the road)."
        if e["id"] in YEARS:
            note += (" Years researched: opened 1703 (Bloomingdale Road); given up when the Boulevard (Broadway) was laid out on a "
                     "straighter line from 1868 (end estimated; https://en.wikipedia.org/wiki/Broadway_(Manhattan)).")
        if "accuracy" in t.get("source:note", "") + t.get("source:1:note", ""):
            note += " Line accuracy low (schematic source map)."
        out.append([f"ohm_{e['id']}", name or "(unnamed old road)", "road", y0, y1, "ground", 1, "lonlat",
                    "; ".join(f"{a:.5f} {b:.5f}" for a, b in zip(lo, la)), note, f"https://www.openhistoricalmap.org/way/{e['id']}"])
        stats.append((name or "(unnamed)", line.length, y0, y1, round(on, 2), lo.mean(), la.mean()))
    if verbose:
        s = pd.DataFrame(stats, columns=["name", "m", "y0", "y1", "on", "lon", "lat"])
        print(len(s), "OHM roads kept,", round(s.m.sum() / 1000, 1), "km")
        print(s[s.name == "(unnamed)"].round(4).to_string())
        print(s.groupby("name").agg(n=("m", "size"), km=("m", lambda v: round(v.sum() / 1000, 2)), y0=("y0", "min"), y1=("y1", "max"),
                                    lon=("lon", "mean"), lat=("lat", "mean")).sort_values("km", ascending=False).head(45).to_string())
    else:
        print(f"{len(out)} OHM roads")
    return out


if __name__ == "__main__":
    rows(verbose=True)
