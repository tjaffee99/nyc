"""Research helper: assemble the routes of the elevated lines that are gone.

  geometry  1. OpenHistoricalMap railway ways with an end date (CC0), where OHM has the line;
            2. elsewhere the centre line of the street the structure stood over (Overture /
               OpenStreetMap roads, ODbL): the route is the shortest street path through the
               line's stations (their coordinates: Wikidata) and through the documented corners
               listed in LINES below. OHM geometry is preferred wherever it lies along the way.
  dates     every stretch between two neighbouring stations opens with the later of the two
            stations and closes with the earlier (data/tables/transit_stations.csv: station
            infoboxes / Wikidata). A station opened later / closed earlier than both neighbours
            is an infill station / a station closed while trains still ran through.

Writes data/manual/transit/elevated_lines.geojson (one LineString per line, with its sources) and
the rows of system `el` in data/tables/transit_openings.csv.

    ../../../../.venv/bin/python build_elevated.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data" / "raw"
TABLES = ROOT / "data" / "tables"
OUT = ROOT / "data" / "manual" / "transit"
UTM = "EPSG:32618"
WP = "https://en.wikipedia.org/wiki/"
OHM_EL = ("IRT Ninth", "IRT Sixth", "IRT Second", "IRT Third", "IRT City Hall", "NYC Elevated", "BMT Fifth", "BMT Fulton",
          "BMT Lexington", "IRT West Farms")

# Stations the tables do not have as closed stations of their own (they are part of a complex
# that is still open): name -> (lon, lat, opened, closed, source)
VIRTUAL = {
    "149th Street": (-73.9176, 40.8161, "1887-06-16", "1973-04-29", WP + "149th_Street_station_(IRT_Third_Avenue_Line)"),
}
# closing days the automatic table has wrong: the City Hall branch served the Third Avenue
# elevated until 31 Dec 1953 (the infobox row carries the 1942 end of Second Avenue service)
CLOSE_FIX = {"Q5123191": "1953-12-31"}

# Each line: the station group(s) of transit_stations.csv (column `line`) it is strung through,
# where the chain starts, stations of other groups it also calls at (codes), corners (lon, lat)
# where it turned between two stations, and its article.
LINES = [
    {"id": "ninth", "name": "Ninth Avenue elevated (IRT Ninth Avenue Line)", "groups": ["IRT Ninth Avenue Line"],
     "article": "IRT_Ninth_Avenue_Line", "exclude": ["Sedgwick", "Anderson"],
     # stations that outlived this line: South Ferry served the Third Avenue trains until 1950, 155th Street the shuttle until 1958
     "late": ["South Ferry", "155th Street"],
     "guide": [(-74.0131, 40.7012), (-74.0145, 40.7060), (-74.0060, 40.7405), (-73.9853, 40.7690), (-73.9619, 40.8005), (-73.9581, 40.8003), (-73.9382, 40.8300)],
     # the curve at 110th Street: Columbus Avenue -> Eighth Avenue
     "corners": [(-73.9619, 40.8005, ["Columbus Avenue"], ["Cathedral Parkway", "West 110th Street"]),
                 (-73.9581, 40.8003, ["Frederick Douglass Boulevard", "Frederick Douglass Circle", "Central Park West", "8th Avenue"],
                  ["Cathedral Parkway", "West 110th Street", "Central Park North", "Frederick Douglass Circle"])],
     "route": "South Ferry - Battery Place - Greenwich Street - Ninth Avenue - Columbus Avenue - 110th Street - Eighth Avenue - 155th Street"},
    {"id": "sixth", "name": "Sixth Avenue elevated (IRT Sixth Avenue Line)", "groups": ["IRT Sixth Avenue Line"],
     "article": "IRT_Sixth_Avenue_Line", "exclude": ["58th", "South Ferry"], "first": "Battery Place", "last": "Eighth Avenue",
     "late": ["Battery Place"],
     "guide": [(-74.0145, 40.7060), (-74.0095, 40.7135), (-73.9983, 40.7297), (-74.0007, 40.7308), (-73.9785, 40.7612), (-73.9868, 40.7647)],
     "corners": [(-73.9785, 40.7612, ["6th Avenue", "Avenue of the Americas"], ["West 53rd Street"])],
     "end": (-73.9868, 40.7647, ["9th Avenue"], ["West 53rd Street"]),
     "route": "Battery Place - Trinity Place - Church Street - Murray Street - West Broadway - West 3rd Street - Sixth Avenue - 53rd Street - Ninth Avenue"},
    {"id": "third", "name": "Third Avenue elevated (IRT Third Avenue Line)", "groups": ["IRT Third Avenue Line"],
     "article": "IRT_Third_Avenue_Line", "exclude": ["City Hall", "Bronx Park", "34th Street Ferry", "Grand Central", "Second Avenue"], "end_code": "208",
     "include": ["Hanover Square"], "virtual": ["149th Street"],
     "guide": [(-74.0131, 40.7012), (-73.9985, 40.7130), (-73.9915, 40.7280), (-73.9340, 40.8060), (-73.9175, 40.8160), (-73.8910, 40.8610), (-73.8723, 40.8790), (-73.8663, 40.8776)],
     "corners": [],
     "route": "South Ferry - Pearl Street - Chatham Square - Bowery - Third Avenue - 129th Street - Harlem River - Third Avenue (Bronx) - Fordham Road - Webster Avenue - Gun Hill Road"},
    {"id": "second", "name": "Second Avenue elevated (IRT Second Avenue Line)", "groups": ["IRT Second Avenue Line"],
     "article": "IRT_Second_Avenue_Line", "exclude": ["Queensboro", "Bridge", "City Hall", "Hanover", "South Ferry", "Fulton", "Franklin Square"],
     "first": "Chatham Square", "anchors": ["Chatham Square", "129th Street"],
     "guide": [(-73.9985, 40.7130), (-73.9923, 40.7146), (-73.9779, 40.7367), (-73.9806, 40.7379), (-73.9345, 40.8045)],
     # Division Street -> Allen Street; First Avenue -> 23rd Street -> Second Avenue
     "corners": [(-73.9923, 40.7146, ["Division Street"], ["Allen Street"]), (-73.9779, 40.7367, ["1st Avenue"], ["East 23rd Street"]),
                 (-73.9806, 40.7379, ["2nd Avenue"], ["East 23rd Street"])],
     "route": "Chatham Square - Division Street - Allen Street - First Avenue - 23rd Street - Second Avenue - 129th Street"},
    {"id": "cityhall", "name": "City Hall branch of the Second and Third Avenue elevateds", "groups": ["IRT Third Avenue Line", "IRT Second Avenue Line"],
     "article": "City_Hall_station_(IRT_Second_Avenue_Line)", "only": ["City Hall", "Chatham Square"],
     "guide": [(-73.9985, 40.7130), (-74.0045, 40.7122)], "corners": [], "route": "Chatham Square - Park Row - City Hall"},
    {"id": "branch34", "name": "34th Street branch of the Third Avenue elevated", "groups": ["34th Street Branch", "IRT Third Avenue Line"],
     "article": "34th_Street_Ferry_station", "only": ["34th Street", "Second Avenue"], "anchors": ["34th Street"], "exclude": [], "max_off": 150,
     "guide": [(-73.9772, 40.7460), (-73.9715, 40.7437)], "corners": [], "route": "Third Avenue - East 34th Street - 34th Street Ferry"},
    {"id": "branch42", "name": "42nd Street branch of the Third Avenue elevated", "groups": ["42nd Street Branch", "IRT Third Avenue Line"],
     "article": "Grand_Central_station_(IRT_Third_Avenue_Line)", "only": ["Grand Central", "42nd Street"], "anchors": ["42nd Street"], "exclude": [], "max_off": 150,
     "guide": [(-73.9733, 40.7508), (-73.9775, 40.7525)], "corners": [], "route": "Third Avenue - East 42nd Street - Grand Central Depot"},
    {"id": "queensboro", "name": "Queensboro Bridge branch of the Second Avenue elevated", "groups": ["IRT Second Avenue Line"],
     "article": "IRT_Second_Avenue_Line", "only": ["57th Street"], "anchors": ["57th Street"], "end_code": "R09", "exclude": [],
     "dates": ("1917-07-23", "1942-06-13"), "bridge": "Queensboro Bridge",
     "guide": [(-73.9655, 40.7597), (-73.9668, 40.7613), (-73.9401, 40.7508)], "corners": [],
     "route": "Second Avenue at 59th Street - Queensboro Bridge - Queensboro Plaza"},
    {"id": "brooklyn_bridge", "name": "Brooklyn Bridge elevated tracks (Park Row - Sands Street)", "groups": ["BMT Myrtle Avenue Line", "BMT Brighton Line", "BMT Fulton Street Line", "BMT Fifth Avenue Line", "BMT Lexington Avenue Line"],
     "article": "Park_Row_Terminal", "only": ["Park Row", "Sands Street"], "exclude": [], "bridge": "Brooklyn Bridge",
     "guide": [(-74.0044, 40.7122), (-73.9883, 40.6999)], "corners": [],
     "route": "Park Row terminal - Brooklyn Bridge - Sands Street (elevated trains from 18 Jun 1898; the bridge's cable railway of 24 Sep 1883 used the same tracks)"},
    {"id": "polo_grounds", "name": "Ninth Avenue elevated extension to Jerome Avenue (Polo Grounds Shuttle)", "groups": ["IRT Ninth Avenue Line"],
     "article": "IRT_Ninth_Avenue_Line", "only": ["155th Street", "Sedgwick", "Anderson"], "anchors": ["155th Street"], "exclude": [], "straight": True,
     "guide": [(-73.9382, 40.8301), (-73.9323, 40.8314), (-73.9262, 40.8327), (-73.9253, 40.8312)], "end": (-73.9253, 40.8312), "corners": [],
     "route": "155th Street - Putnam Bridge - Sedgwick Avenue - tunnel - Anderson-Jerome Avenues - Jerome Avenue line at 162nd Street"},
    {"id": "fulton", "name": "Fulton Street elevated (BMT Fulton Street Line)", "groups": ["BMT Fulton Street Line", "Fulton Street Line"],
     "article": "BMT_Fulton_Street_Line", "exclude": ["Park Row", "Sands"], "end_code": "A59", "max_off": 350,
     "guide": [(-73.9950, 40.7030), (-73.9905, 40.6925), (-73.9812, 40.6887), (-73.9565, 40.6808), (-73.9053, 40.6786), (-73.9010, 40.6715),
               (-73.8720, 40.6753), (-73.8655, 40.6770), (-73.8590, 40.6792)],
     "corners": [],
     "route": "Fulton Ferry - Fulton Street - East New York - Pitkin Avenue - Liberty Avenue - Grant Avenue (City Line)"},
    {"id": "fifth", "name": "Fifth Avenue elevated (BMT Fifth Avenue Line)", "groups": ["BMT Fifth Avenue Line"],
     "article": "BMT_Fifth_Avenue_Line", "exclude": ["Park Row", "Sands", "Adams", "Bridge"],
     "guide": [(-73.9806, 40.6935), (-73.9790, 40.6880), (-73.9775, 40.6840), (-74.0011, 40.6527), (-74.0053, 40.6551), (-74.0235, 40.6405)],
     # Fifth Avenue -> 38th Street -> Third Avenue
     "corners": [(-74.0011, 40.6527, ["5th Avenue"], ["38th Street"]), (-74.0053, 40.6551, ["3rd Avenue"], ["38th Street"])],
     "route": "Hudson Avenue - Flatbush Avenue - Fifth Avenue - 38th Street - Third Avenue - 65th Street"},
    {"id": "lexington", "name": "Lexington Avenue elevated (BMT Lexington Avenue Line)", "groups": ["BMT Lexington Avenue Line"],
     "article": "BMT_Lexington_Avenue_Line", "exclude": ["Franklin"], "max_off": 200,
     "end": (-73.9290, 40.6903, ["Lexington Avenue"], ["Broadway"]),  # joins the Broadway elevated (still standing) there
     "guide": [(-73.9627, 40.6934), (-73.9626, 40.6878), (-73.9290, 40.6903)],
     "corners": [(-73.9626, 40.6878, ["Grand Avenue"], ["Lexington Avenue"])],
     "route": "Myrtle Avenue - Grand Avenue - Lexington Avenue - Broadway (Gates Avenue)"},
    {"id": "myrtle", "name": "Myrtle Avenue elevated west of Broadway (BMT Myrtle Avenue Line)", "groups": ["BMT Myrtle Avenue Line"],
     "article": "BMT_Myrtle_Avenue_Line", "exclude": ["Evergreen", "Sands", "Park Row"], "end_code": "M11",
     "guide": [(-73.9885, 40.6945), (-73.9357, 40.6975)], "corners": [],
     "route": "Adams Street - Myrtle Avenue - Broadway"},
    {"id": "jamaica_east", "name": "Jamaica Avenue elevated east of 121st Street (BMT Jamaica Line)", "groups": ["BMT Jamaica Line"],
     "start_code": "J12", "article": "BMT_Jamaica_Line", "exclude": ["Broadway Ferry", "Driggs", "Park Avenue"],
     "guide": [(-73.8284, 40.7005), (-73.7930, 40.7070)], "corners": [], "route": "Jamaica Avenue, 121st Street - 168th Street"},
    {"id": "broadway_ferry", "name": "Broadway elevated to Broadway Ferry (BMT Jamaica Line)", "groups": ["BMT Jamaica Line"],
     "start_code": "M16", "article": "BMT_Jamaica_Line", "only": ["Broadway Ferry", "Driggs"],
     "guide": [(-73.9578, 40.7083), (-73.9680, 40.7110)], "corners": [], "route": "Broadway, Marcy Avenue - Broadway Ferry"},
    {"id": "culver_shuttle", "name": "Culver Shuttle (BMT Culver Line)", "groups": ["IND Culver Line", "BMT Culver Line"],
     "start_code": "F29", "article": "Culver_Shuttle", "exclude": [], "end_code": "B12",
     "guide": [(-73.9785, 40.6360), (-73.9945, 40.6465)], "corners": [], "route": "Ditmas Avenue - 37th Street - Ninth Avenue"},
]


def to_utm(lon, lat):
    s = gpd.GeoSeries(gpd.points_from_xy(np.atleast_1d(lon), np.atleast_1d(lat)), crs=4326).to_crs(UTM)
    return np.column_stack([s.x.values, s.y.values])


def to_ll(xy):
    s = gpd.GeoSeries(gpd.points_from_xy(xy[:, 0], xy[:, 1]), crs=UTM).to_crs(4326)
    return np.column_stack([s.x.values, s.y.values])


def load_roads():
    parts = []
    for f in ("roads_region", "roads_local"):
        g = gpd.read_parquet(RAW / "overture" / "2026-10-21.0" / f"{f}.parquet", columns=["name", "class", "geometry"])
        g = g.set_crs(4326, allow_override=True)
        g = g[g.geometry.geom_type == "LineString"].cx[-74.06:-73.75, 40.57:40.91]
        parts.append(g[~g["class"].isin(["footway", "path", "steps", "cycleway", "pedestrian", "track", "bridleway"])])
    r = pd.concat(parts, ignore_index=True).to_crs(UTM)
    return r


def load_ohm():
    out = []
    for w in json.load(open(RAW / "transit" / "ohm" / "ohm_rail.json"))["elements"]:
        t = w.get("tags", {})
        if w["type"] != "way" or not t.get("end_date") or t.get("railway") not in ("rail", "subway"):
            continue
        nm = t.get("name", "")
        if not (nm.startswith(OHM_EL) or (nm == "" and t.get("start_date") == "1883")):
            continue
        g = w["geometry"]
        out.append((w["id"], to_utm([p["lon"] for p in g], [p["lat"] for p in g])))
    return out


class Graph:
    def __init__(self, roads, ohm, box):
        x0, y0, x1, y1 = box
        self.xy, self.kind = [], []
        idx = {}
        rows, cols, w = [], [], []

        def node(p, kind):
            key = (round(p[0]), round(p[1]), kind)
            if key not in idx:
                idx[key] = len(self.xy)
                self.xy.append((p[0], p[1]))
                self.kind.append(kind)
            return idx[key]

        b = roads.bounds
        sel = roads[(b.maxx >= x0) & (b.minx <= x1) & (b.maxy >= y0) & (b.miny <= y1)]
        for g in sel.geometry.values:
            c = np.array(g.coords)[:, :2]
            for p, q in zip(c[:-1], c[1:]):
                a, bb = node(p, 0), node(q, 0)
                rows.append(a)
                cols.append(bb)
                w.append(max(float(np.hypot(*(q - p))), 0.1))
        ohm_nodes = []
        for _, c in ohm:
            if c[:, 0].max() < x0 or c[:, 0].min() > x1 or c[:, 1].max() < y0 or c[:, 1].min() > y1:
                continue
            # densify so streets can be joined along the way
            d = [c[0]]
            for p, q in zip(c[:-1], c[1:]):
                n = max(1, int(np.hypot(*(q - p)) / 25))
                d += [p + (q - p) * k / n for k in range(1, n + 1)]
            for p, q in zip(d[:-1], d[1:]):
                a, bb = node(p, 1), node(q, 1)
                rows.append(a)
                cols.append(bb)
                w.append(max(float(np.hypot(*(q - p))), 0.1) * 0.25)
                ohm_nodes += [a, bb]
        self.xy = np.array(self.xy)
        self.kind = np.array(self.kind)
        road_n = np.nonzero(self.kind == 0)[0]
        self.rtree = cKDTree(self.xy[road_n]) if len(road_n) else None
        self.road_n = road_n
        on = np.unique(ohm_nodes) if ohm_nodes else np.zeros(0, int)
        if len(on) and self.rtree is not None:
            dd, ii = self.rtree.query(self.xy[on], distance_upper_bound=45.0)
            for a, d_, i_ in zip(on, dd, ii):
                if np.isfinite(d_):
                    rows.append(a)
                    cols.append(road_n[i_])
                    w.append(d_ * 2.0 + 5.0)
            # OHM pieces to each other (parallel tracks, small gaps)
            ot = cKDTree(self.xy[on])
            for a, b_ in ot.query_pairs(12.0):
                rows.append(on[a])
                cols.append(on[b_])
                w.append(float(np.hypot(*(self.xy[on[a]] - self.xy[on[b_]]))) + 1.0)
        self.on = on
        self.otree = cKDTree(self.xy[on]) if len(on) else None
        n = len(self.xy)
        self.m = coo_matrix((w, (rows, cols)), shape=(n, n)).tocsr()

    def snap(self, p):
        if self.otree is not None:
            d, i = self.otree.query(p)
            if d < 45:
                return int(self.on[i])
        d, i = self.rtree.query(p)
        return int(self.road_n[i])

    def path(self, a, b):
        dist, pred = dijkstra(self.m, directed=False, indices=a, return_predecessors=True)
        if not np.isfinite(dist[b]):
            return None, 0.0
        out = [b]
        while out[-1] != a:
            out.append(pred[out[-1]])
        out = out[::-1]
        k = self.kind[out]
        seg = np.hypot(*np.diff(self.xy[out], axis=0).T) if len(out) > 1 else np.zeros(0)
        ohm_len = float(seg[(k[:-1] == 1) & (k[1:] == 1)].sum()) if len(out) > 1 else 0.0
        return self.xy[out], ohm_len


def corner(roads, c):
    """A documented corner: the crossing of two named streets nearest the given point (the point
    itself when the names are not found)."""
    p = to_utm(c[0], c[1])[0]
    if len(c) < 4:
        return p
    b = roads.bounds
    near = roads[(b.maxx >= p[0] - 200) & (b.minx <= p[0] + 200) & (b.maxy >= p[1] - 200) & (b.miny <= p[1] + 200)]
    A = near[near["name"].isin(c[2])]
    B = near[near["name"].isin(c[3])]
    best, bd = None, 1e9
    for ga in A.geometry.values:
        for gb in B.geometry.values:
            if ga.distance(gb) < 15:
                from shapely.ops import nearest_points
                q = nearest_points(ga, gb)[0]
                d = float(np.hypot(q.x - p[0], q.y - p[1]))
                if d < bd:
                    best, bd = np.array([q.x, q.y]), d
    if best is None:
        print(f"   corner {c[2]} x {c[3]} not found: using the given point", file=sys.stderr)
        return p
    return best


def remove_spurs(p, tol=7.0, back=60):
    """Drop out-and-back excursions (a station snapped to a side street) from a path."""
    out = [p[0]]
    for q in p[1:]:
        out.append(q)
        i = len(out) - 1
        for j in range(i - 2, max(-1, i - back), -1):
            if np.hypot(*(out[j] - q)) < tol:
                del out[j + 1:]
                break
    return np.array(out)


def drop_kinks(p, angle=75.0, short=45.0):
    """Drop the vertices of short zigzags (the path hopping between an OpenHistoricalMap piece and
    the street centre line beside it); real corners between long straight runs stay."""
    p = [np.asarray(q, float) for q in p]
    changed = True
    while changed and len(p) > 3:
        changed = False
        for i in range(1, len(p) - 1):
            a, b = p[i] - p[i - 1], p[i + 1] - p[i]
            la, lb = np.hypot(*a), np.hypot(*b)
            if la < 0.5 or lb < 0.5:
                del p[i]
                changed = True
                break
            turn = abs((np.degrees(np.arctan2(b[1], b[0]) - np.arctan2(a[1], a[0])) + 180) % 360 - 180)
            if turn > angle and min(la, lb) < short:
                del p[i]
                changed = True
                break
    return np.array(p)


def chain(pts, start):
    """Nearest-neighbour order of points from a start point."""
    left = list(range(len(pts)))
    cur = np.array(start, float)
    order = []
    while left:
        j = min(left, key=lambda k: np.hypot(*(pts[k] - cur)))
        order.append(j)
        left.remove(j)
        cur = pts[j]
    return order


def main():
    st = pd.read_csv(TABLES / "transit_stations.csv", dtype=str, keep_default_na=False)
    st = st[st.lon != ""].copy()
    sxy = to_utm(st.lon.astype(float).values, st.lat.astype(float).values)
    st["x"], st["y"] = sxy[:, 0], sxy[:, 1]
    by_code = {r.code: r for _, r in st.iterrows()}
    roads = load_roads()
    ohm = load_ohm()
    feats, rows = [], []
    for ln in LINES:
        g = st[st.line.map(lambda v: any(x in v.split("; ") for x in ln["groups"])) & (st.closed != "")]
        if ln.get("only"):
            g = g[g.name.map(lambda n: any(x in n for x in ln["only"]))]
        g = g[~g.name.map(lambda n: any(x in n for x in ln.get("exclude", [])))]
        if ln.get("include"):
            g = pd.concat([g, st[st.name.isin(ln["include"]) & (st.closed != "") & st.system.isin(["el", "subway"])]]).drop_duplicates("code")
        for v in ln.get("virtual", []):
            lon, lat, o, c, _ = VIRTUAL[v]
            x, y = to_utm(lon, lat)[0]
            row = {"system": "el", "code": f"{lon} {lat}", "name": v, "opened": o, "closed": c, "x": x, "y": y}
            g = pd.concat([g, pd.DataFrame([row])], ignore_index=True)
            by_code[row["code"]] = pd.Series(row)
        from shapely.geometry import LineString, Point
        guide = LineString(to_utm([p[0] for p in ln["guide"]], [p[1] for p in ln["guide"]]))
        g = g.assign(s=[guide.project(Point(x, y)) for x, y in zip(g.x, g.y)], off=[guide.distance(Point(x, y)) for x, y in zip(g.x, g.y)])
        g = g[g.off < ln.get("max_off", 600)].sort_values("s")
        if ln.get("first"):
            g = g[g.s >= g[g.name.str.contains(ln["first"])].s.min()]
        if ln.get("last"):
            g = g[g.s <= g[g.name.str.contains(ln["last"])].s.max()]
        way = [(np.array([r.x, r.y]), r.code, r.s) for r in g.itertuples()]  # (xy, station code or None, position on the guide)
        for key, pos in (("start_code", -1.0), ("end_code", 1e9)):
            if key in ln:
                e = by_code[ln[key]]
                way.append((np.array([e["x"], e["y"]]), ln[key], pos))
        for c in ln["corners"] + ([ln["end"]] if "end" in ln else []):
            cp = corner(roads, c)
            way.append((cp, None, 1e8 if c is ln.get("end") else guide.project(Point(cp))))
        way = [(w[0], w[1]) for w in sorted(way, key=lambda w: w[2])]
        allp = np.array([w[0] for w in way])
        box = (allp[:, 0].min() - 500, allp[:, 1].min() - 500, allp[:, 0].max() + 500, allp[:, 1].max() + 500)
        G = Graph(roads, ohm, box)
        if ln.get("straight"):  # no street left to follow: the stations themselves
            G.xy = np.array([w[0] for w in way])
            nodes = list(range(len(way)))
        else:
            nodes = [G.snap(w[0]) for w in way]
        geom, ohm_len, tot, straight = [G.xy[nodes[0]]], 0.0, 0.0, 0
        at = [0]  # vertex index of every waypoint
        for a, b in zip(nodes[:-1], nodes[1:]):
            p, ol = (None, 0.0) if ln.get("straight") else G.path(a, b)
            if p is None or len(p) < 2:
                p, ol = np.array([G.xy[a], G.xy[b]]), 0.0
                straight += 1
            L = float(np.hypot(*np.diff(p, axis=0).T).sum())
            direct = float(np.hypot(*(G.xy[b] - G.xy[a])))
            if L > 1.6 * direct + 150:  # a detour round a missing street: go straight
                p, ol, L = np.array([G.xy[a], G.xy[b]]), 0.0, direct
                straight += 1
            geom += list(p[1:])
            ohm_len += ol
            tot += L
            at.append(len(geom) - 1)
        geom = drop_kinks(remove_spurs(np.array(geom)))
        names = [by_code[c]["name"] if c else "-" for _, c in way]
        print(f"{ln['id']}: {tot / 1000:.1f} km, {ohm_len / max(tot, 1) * 100:.0f}% on OHM geometry, {straight} straight joins; "
              + " > ".join(names), file=sys.stderr)
        ll = to_ll(geom)
        src = (f"OpenHistoricalMap railway ways with an end date (CC0) for {ohm_len / max(tot, 1) * 100:.0f}% of the length; "
               f"the rest is the street centre line (OpenStreetMap roads via Overture, ODbL) through the stations"
               + (f"; {straight} stretch(es) joined by a straight line where no street remains" if straight else ""))
        if ln.get("straight"):
            src = "straight lines between the station coordinates (estimated: the bridge and structure are gone and no street follows the route)"
        feats.append({"type": "Feature", "properties": {
            "id": ln["id"], "name": ln["name"], "route": ln["route"], "geometry_source": src,
            "source": WP + ln["article"], "stations_source": "Wikidata coordinates (data/tables/transit_stations.csv)",
            "structure": "elevated", "track_spacing_m": 3.8, **({"bridge": ln["bridge"]} if ln.get("bridge") else {})},
            "geometry": {"type": "LineString", "coordinates": [[round(float(a), 6), round(float(b), 6)] for a, b in ll]}})
        # stretches between neighbouring stations: in use while a station of this line is open on
        # each side. Stations of another line that this one only meets (anchors) carry no date; an
        # end stretch takes the dates of the station next to it.
        stn = [c for _, c in way if c]
        anchor = [c in (ln.get("start_code"), ln.get("end_code")) or by_code[c]["name"] in ln.get("anchors", []) for c in stn]
        op = [by_code[c].opened for c in stn]
        cl = [CLOSE_FIX.get(c) or by_code[c].closed or "9999-12-31" for c in stn]
        n = len(stn)
        first_wp = None if way[0][1] else way[0][0]
        last_wp = None if way[-1][1] else way[-1][0]
        run = None
        for k in range(n - 1):
            a, b = stn[k], stn[k + 1]
            if ln.get("dates"):
                o, c = ln["dates"]
            else:
                left = [j for j in range(k + 1) if not anchor[j]]
                right = [j for j in range(k + 1, n) if not anchor[j]]
                late = ln.get("late", [])
                lc = [j for j in left if by_code[stn[j]]["name"] not in late]
                rc = [j for j in right if by_code[stn[j]]["name"] not in late]
                if left and right:
                    o = max(min(op[j] for j in left), min(op[j] for j in right))
                elif left or right:
                    o = op[left[-1] if left else right[0]]
                else:
                    continue
                if lc and rc:
                    c = min(max(cl[j] for j in lc), max(cl[j] for j in rc))
                elif lc or rc:
                    c = cl[lc[-1] if lc else rc[0]]
                else:
                    continue
            if c.startswith("9999") or o >= c:
                print(f"   skipped {by_code[a]['name']} - {by_code[b]['name']}: {o} .. {c}", file=sys.stderr)
                run = None
                continue
            if run and run["opened"] == o and run["closed"] == c:
                run["to"] = b
            else:
                run = {"from": a, "to": b, "opened": o, "closed": c}
                rows.append((ln, run))
            if k == 0 and first_wp is not None:
                run["from_pt"] = first_wp
            if k == n - 2 and last_wp is not None:
                run["to_pt"] = last_wp
    out = []
    for ln, r in rows:
        ends = []
        for key, pt in (("from", "from_pt"), ("to", "to_pt")):
            if pt in r:
                q = to_ll(np.array([r[pt]]))[0]
                ends.append(f"{q[0]:.5f} {q[1]:.5f}")
            else:
                ends.append(r[key])
        out.append({"route_id": f"el_{ln['id']}_{r['from']}_{r['to']}".replace(" ", "_"), "opened": r["opened"],
                    "note": f"{by_code[r['from']]['name']} - {by_code[r['to']]['name']}", "source": WP + ln["article"], "system": "el",
                    "line": ln["name"], "from_stop": ends[0], "to_stop": ends[1], "via": ln["id"], "closed": r["closed"]})
    (OUT / "elevated_lines.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, indent=1))
    tab = pd.read_csv(TABLES / "transit_openings.csv", dtype=str, keep_default_na=False)
    tab = pd.concat([tab[tab.system != "el"], pd.DataFrame(out)], ignore_index=True)
    tab.to_csv(TABLES / "transit_openings.csv", index=False)
    print(f"{len(feats)} lines, {len(out)} dated stretches", file=sys.stderr)
    for r in out:
        print(f"   {r['via']:14s} {r['opened']} .. {r['closed']}  {r['note']}", file=sys.stderr)


if __name__ == "__main__":
    main()
