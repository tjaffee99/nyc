"""Today's street network (Overture roads) as a lookup for tracing historical maps.

intersection("Wall Street", "Broadway")      -> (lon, lat) where the two named streets meet
nearest_intersection(lon, lat, max_m=60)     -> (lon, lat, "A & B", distance_m) or None

Old streets below Houston St mostly keep their lines, so vertices of an extent are given as
intersections of today's streets wherever the edge of the built area follows a street.
Metric work in UTM 18N (EPSG:32618). Local map coordinates used by the tracing tools:
X = easting - 580000, Y = northing - 4500000 (metres).
"""
from __future__ import annotations
import re
from functools import lru_cache
from pathlib import Path
import duckdb
import numpy as np
import shapely
import shapely.ops
from pyproj import Transformer
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[4]
OVERTURE = ROOT / "data" / "raw" / "overture" / "2026-10-21.0"
X0, Y0 = 580000.0, 4500000.0
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)
TO_LL = Transformer.from_crs("EPSG:32618", "EPSG:4326", always_xy=True)
# the project's map box (all five boroughs)
BBOX = (-74.29, 40.47, -73.67, 40.94)
DROP = {"footway", "path", "steps", "cycleway", "bridleway", "track", "service", "motorway", "unknown"}
NEAR_DEFAULT = (-74.0080, 40.7095)  # City Hall Park


def local(lon, lat):
    e, n = TO_UTM.transform(lon, lat)
    return e - X0, n - Y0


def lonlat(x, y):
    return TO_LL.transform(x + X0, y + Y0)


_ABBR = {"st": "street", "ave": "avenue", "av": "avenue", "pl": "place", "sq": "square", "rd": "road",
         "blvd": "boulevard", "w": "west", "e": "east", "n": "north", "s": "south", "ln": "lane"}


def norm(name: str) -> str:
    t = re.sub(r"[.,']", "", name.lower()).split()
    return " ".join(_ABBR.get(w, w) for w in t)


@lru_cache(maxsize=1)
def roads():
    """(names, geoms_utm_local) of every named street segment in BBOX (not footways / service roads)."""
    con = duckdb.connect()
    con.execute("install spatial; load spatial;")
    rows = []
    for f in ("roads_local", "roads_region"):
        p = OVERTURE / f"{f}.parquet"
        q = f"""select name, class, ST_AsWKB(geometry) from '{p}'
                where name is not null and ST_XMax(geometry) > {BBOX[0]} and ST_XMin(geometry) < {BBOX[2]}
                  and ST_YMax(geometry) > {BBOX[1]} and ST_YMin(geometry) < {BBOX[3]}"""
        rows += con.execute(q).fetchall()
    names, geoms = [], []
    for name, cls, wkb in rows:
        if cls in DROP:
            continue
        names.append(norm(name))
        geoms.append(bytes(wkb))
    g = shapely.from_wkb(geoms)
    g = shapely.transform(g, lambda c: np.column_stack(local(c[:, 0], c[:, 1])))
    return np.array(names), g


@lru_cache(maxsize=1)
def _by_name():
    names, g = roads()
    d = {}
    for n, geom in zip(names, g):
        d.setdefault(n, []).append(geom)
    return d


@lru_cache(maxsize=1)
def _nodes():
    """Street-network nodes where two differently named streets meet: xy array, names list, KD-tree."""
    names, g = roads()
    acc = {}
    for n, geom in zip(names, g):
        c = shapely.get_coordinates(geom)
        for pt in (c[0], c[-1]):
            acc.setdefault((round(pt[0]), round(pt[1])), set()).add(n)
    keys = [k for k, v in acc.items() if len(v) >= 2]
    xy = np.array(keys, float)
    return xy, [" & ".join(sorted(acc[k])[:2]) for k in keys], cKDTree(xy)


def intersection_xy(a: str, b: str, near=None, tol=40.0):
    """Local (X, Y) of the meeting point of streets a and b nearest to `near` (local X, Y)."""
    d = _by_name()
    na, nb = norm(a), norm(b)
    if na not in d or nb not in d:
        raise KeyError(f"street not found: {a if na not in d else b}")
    if near is None:
        near = local(*NEAR_DEFAULT)
    p = shapely.Point(near)
    # only the pieces within 6 km of the hint: Broadway, Main St ... exist in every borough
    ga = [g for g in d[na] if g.distance(p) < 6000]
    gb = [g for g in d[nb] if g.distance(p) < 6000]
    if not ga or not gb:
        raise KeyError(f"{a} / {b}: nothing within 6 km of the hint")
    ua, ub = shapely.union_all(ga), shapely.union_all(gb)
    x = ua.intersection(ub)
    pts = [q for q in (x.geoms if hasattr(x, "geoms") else [x]) if not q.is_empty]
    pts = [q if q.geom_type == "Point" else q.centroid for q in pts]
    if not pts:
        # closest approach (a street that stops short, a renamed stub)
        best = None
        for g1 in ga:
            for g2 in gb:
                dist = g1.distance(g2)
                if dist < tol and (best is None or dist < best[0]):
                    q1, q2 = shapely.ops.nearest_points(g1, g2)
                    best = (dist, shapely.Point((q1.x + q2.x) / 2, (q1.y + q2.y) / 2))
        if best is None:
            # pedestrianised pieces (Wall St west of William St, Nassau St ...) are not in the road
            # extract: prolong each street's merged line 300 m beyond its ends and intersect again
            def prolong(u):
                m = shapely.ops.linemerge(u) if u.geom_type != "LineString" else u
                out = []
                for ln in (m.geoms if hasattr(m, "geoms") else [m]):
                    c = shapely.get_coordinates(ln)
                    for a0, a1 in ((c[1], c[0]), (c[-2], c[-1])):
                        v = (a1 - a0) / max(np.hypot(*(a1 - a0)), 1e-9)
                        out.append(shapely.LineString([a1, a1 + 300 * v]))
                    out.append(ln)
                return shapely.union_all(out)
            x = prolong(ua).intersection(prolong(ub))
            cand = [q for q in (x.geoms if hasattr(x, "geoms") else [x]) if not q.is_empty and q.geom_type == "Point"]
            if not cand:
                raise ValueError(f"{a} and {b} do not meet (within {tol} m, or prolonged 300 m) near the hint")
            best = (0, min(cand, key=lambda q: q.distance(p)))
        pts = [best[1]]
    q = min(pts, key=lambda q: q.distance(p))
    return q.x, q.y


def intersection(a: str, b: str, near=None):
    """(lon, lat) of the intersection of two named streets; `near` = (lon, lat) hint."""
    nl = local(*near) if near is not None else None
    return lonlat(*intersection_xy(a, b, nl))


def nearest_intersection_xy(x, y, max_m=60.0):
    xy, names, tree = _nodes()
    dist, i = tree.query([x, y])
    if dist > max_m:
        return None
    return xy[i][0], xy[i][1], names[i], float(dist)


def nearest_intersection(lon, lat, max_m=60.0):
    r = nearest_intersection_xy(*local(lon, lat), max_m=max_m)
    if r is None:
        return None
    lo, la = lonlat(r[0], r[1])
    return lo, la, r[2], r[3]


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        print(intersection(sys.argv[1], sys.argv[2]))
    else:
        for a, b in [("Wall Street", "Broadway"), ("Pearl Street", "Wall Street"), ("Canal Street", "Broadway"),
                     ("East Houston Street", "Bowery"), ("West 14th Street", "5th Avenue"), ("Fulton Street", "Front Street")]:
            lo, la = intersection(a, b)
            print(f"{a} & {b}: {lo:.5f}, {la:.5f}  local {local(lo, la)[0]:.0f}, {local(lo, la)[1]:.0f}",
                  nearest_intersection(lo, la))
        print(len(_nodes()[1]), "nodes")
