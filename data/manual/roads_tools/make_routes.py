"""Builds data/manual/routes.csv: the researched years (hw_defs.py, ferry_defs.py, ohm_roads.py) with lines
taken from Overture's road geometry (never from memory):

  * a highway section = the shortest path along the named motorway / trunk segments of freeways.parquet
    (through their connectors) between two anchors; an anchor is the point of the highway nearest to a named
    cross street / crossing highway, or an end of the named highway;
  * `all` = every mainline segment carrying a name (bridge and tunnel approaches), merged.

Outside the city most highways have no name in Overture, only a route number: a name "ref:US:I 684" selects
the segments of that route ("ref0:..." = only the unnamed ones); the numbers come from fetch_refs.py
(data/raw/roads/overture/freeway_refs.parquet: network + number, as OpenStreetMap's route relations have them).

Usage (from data/manual/roads_tools; prints one line per row):
  ../../../.venv/bin/python make_routes.py            rebuild the rows of hw_defs_counties.py, keep every other
                                                      row of data/manual/routes.csv as it is
  ../../../.venv/bin/python make_routes.py all        rebuild everything (hw_defs, hw_defs_counties, ferries, OHM)
  ../../../.venv/bin/python make_routes.py cross "Name[|Name]" ...   named roads crossing a highway, in order
"""
import csv
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import linemerge, nearest_points, substring

import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OV = f"{ROOT}/data/raw/overture/2026-10-21.0"
UTM = "EPSG:32618"
TO_LL = Transformer.from_crs(UTM, 4326, always_xy=True)
TO_UTM = Transformer.from_crs(4326, UTM, always_xy=True)

fw = gpd.read_parquet(f"{OV}/freeways.parquet")
fw = fw[fw.geometry.geom_type == "LineString"].reset_index(drop=True).to_crs(UTM)
fw["name"] = fw["name"].fillna("")
fw["link"] = fw.subclass.fillna("") == "link"
# route numbers ("US:I 80", "US:NJ 17", "US:US 46" ...) per segment, if fetch_refs.py has been run
REFS = f"{ROOT}/data/raw/roads/overture/freeway_refs.parquet"
fw["keys"] = [frozenset()] * len(fw)
if os.path.exists(REFS):
    _r = pd.read_parquet(REFS)
    _k = {i: frozenset(f"{n} {r}" for n, r in zip(nn, rr) if r) for i, nn, rr in zip(_r.id, _r.networks, _r.refs)}
    fw["keys"] = [_k.get(i, frozenset()) for i in fw["id"].values]
    del _r, _k
KEYS = fw["keys"].values
streets = pd.concat([gpd.read_parquet(f"{OV}/{f}.parquet", columns=["name", "geometry"]) for f in ("roads_region", "roads_local")],
                    ignore_index=True)
streets = gpd.GeoDataFrame(streets[streets.name.notna()], geometry="geometry", crs=4326).to_crs(UTM)
streets = streets[streets.geometry.geom_type == "LineString"]
by_name = {k.upper(): v for k, v in streets.groupby(streets.name.str.strip()).indices.items()}
sgeom = streets.geometry.values

# graph over connectors
node = {}
npos = []
edges = []  # (u, v, seg, at_a, at_b)
seg_nodes = {}
for i, (g, conns) in enumerate(zip(fw.geometry.values, fw.connectors.values)):
    cs = sorted({(float(c["at"]), c["connector_id"]) for c in (conns if conns is not None else [])})
    ids = []
    for at, cid in cs:
        if cid not in node:
            node[cid] = len(npos)
            p = g.interpolate(at, normalized=True)
            npos.append((p.x, p.y))
        ids.append((node[cid], at))
    seg_nodes[i] = ids
    for (u, a), (v, b) in zip(ids[:-1], ids[1:]):
        edges.append((u, v, i, a, b))
npos = np.array(npos)
E = pd.DataFrame(edges, columns=["u", "v", "seg", "a", "b"])
E["len"] = (E.b - E.a) * fw.geometry.length.values[E.seg.values]


def ll(line, tol=8.0):
    line = line.simplify(tol)
    x, y = np.asarray(line.coords).T[:2]
    lon, lat = TO_LL.transform(x, y)
    return "; ".join(f"{a:.5f} {b:.5f}" for a, b in zip(lon, lat))


def _select(names):
    """mask of the segments carrying one of the names; "ref:<network> <number>" = the segments of a route,
    "ref0:..." = only its unnamed segments"""
    up = {n.upper() for n in names if not n.startswith(("ref:", "ref0:"))}
    m = fw.name.str.upper().isin(up).values
    refs = {n[4:] for n in names if n.startswith("ref:")}
    refs0 = {n[5:] for n in names if n.startswith("ref0:")}
    if (refs or refs0) and not os.path.exists(REFS):
        raise ValueError("route numbers needed: run fetch_refs.py first")
    if refs:
        m = m | np.array([bool(k & refs) for k in KEYS])
    if refs0:
        m = m | (np.array([bool(k & refs0) for k in KEYS]) & (fw.name.values == ""))
    return m


def named(names):
    return np.nonzero(_select(names) & ~fw.link.values)[0]


_COUNTY = {}


def county(fips):
    """TIGER county polygon (UTM)"""
    if fips not in _COUNTY:
        co = gpd.read_file(f"zip://{ROOT}/data/raw/tiger/tl_2024_us_county.zip", where=f"GEOID = '{fips}'")
        _COUNTY[fips] = co.to_crs(UTM).geometry.iloc[0]
    return _COUNTY[fips]


def street_geom(name, near=None, radius=700.0, hint=None):
    """union of the segments named `name` (streets, or highways of freeways.parquet) near a geometry / hint"""
    gs = []
    if name.startswith(("ref:", "ref0:")):
        gs += list(fw.geometry.values[np.nonzero(_select({name}))[0]])
    else:
        idx = by_name.get(name.upper())
        if idx is not None:
            gs += list(sgeom[idx])
        gs += list(fw.geometry.values[np.nonzero((fw.name.str.upper() == name.upper()).values)[0]])
    if hint is not None:
        hx, hy = TO_UTM.transform(*hint)
        gs = [g for g in gs if g.distance(Point(hx, hy)) < 1500]
    if near is not None:
        gs = [g for g in gs if g.distance(near) < radius]
    return shapely.union_all(gs) if gs else None


def anchor(spec, names, route_u):
    kind = spec[0]
    idx = named(names)
    nodes = sorted({n for i in idx for n, _ in seg_nodes[i]})
    P = npos[nodes]
    if kind == "end":
        d = spec[1]
        k = {"N": P[:, 1].argmax(), "S": P[:, 1].argmin(), "E": P[:, 0].argmax(), "W": P[:, 0].argmin()}[d]
        return Point(P[k])
    if kind == "pt":
        return Point(TO_UTM.transform(spec[1], spec[2]))
    pick = lambda Q, d: Q[{"N": Q[:, 1].argmax(), "S": Q[:, 1].argmin(), "E": Q[:, 0].argmax(), "W": Q[:, 0].argmin()}[d]]
    if kind == "endof":
        # the N / S / E / W end of another named highway (where a spur joins, a section begins), on this one
        other = sorted({n for i in named(spec[1]) for n, _ in seg_nodes[i]})
        return nearest_points(route_u, Point(pick(npos[other], spec[2])))[0]
    if kind == "border":
        # where the highway crosses a county line (TIGER): the N / S / E / W-most crossing
        hit = route_u.intersection(county(spec[1]).boundary)
        pts = [g for g in getattr(hit, "geoms", [hit]) if g.geom_type == "Point"]
        if not pts:
            raise ValueError(f"{sorted(names)} does not cross the line of county {spec[1]}")
        return Point(pick(np.array([(q.x, q.y) for q in pts]), spec[2]))
    if kind == "x":
        sg = street_geom(spec[1], near=route_u, hint=spec[2] if len(spec) > 2 else None)
        if sg is None:
            raise ValueError(f"no street {spec[1]!r} within 700 m of {sorted(names)}")
        p_route, p_street = nearest_points(route_u, sg)
        if p_route.distance(p_street) > 60:
            # the street stops short of the highway: extend its line to it
            comp = min(getattr(sg, "geoms", [sg]), key=lambda g: g.distance(p_route))
            if comp.geom_type == "LineString" and comp.length > 60:
                s1 = comp.project(p_street)
                p0 = comp.interpolate(s1 - 150 if s1 > comp.length / 2 else s1 + 150)
                dx, dy = p_street.x - p0.x, p_street.y - p0.y
                n = max(np.hypot(dx, dy), 1e-6)
                ray = LineString([(p_street.x, p_street.y), (p_street.x + dx / n * 900, p_street.y + dy / n * 900)])
                hit = ray.intersection(route_u)
                if not hit.is_empty:
                    pts = [g for g in getattr(hit, "geoms", [hit]) if g.geom_type == "Point"]
                    if pts:
                        return min(pts, key=lambda g: g.distance(p_street))
        return p_route
    raise ValueError(spec)


def path(names, A, B):
    """Shortest path along the named highway between two anchors. Each anchor becomes a temporary node on
    every named segment within 60 m of it (both carriageways), so the line starts and ends exactly there."""
    idx = named(names)
    if not len(idx):
        raise ValueError(f"no segments named {sorted(names)}")
    geoms = fw.geometry.values
    route_u = shapely.union_all(geoms[idx])
    pa, pb = anchor(A, names, route_u), anchor(B, names, route_u)
    on = np.zeros(len(fw), bool)
    on[idx] = True
    n0 = len(npos)
    virt = []  # (node id, seg, at, which anchor)
    for which, p in ((0, pa), (1, pb)):
        d = np.array([geoms[i].distance(p) for i in idx])
        near = [i for i, dd in zip(idx, d) if dd < 60] or [idx[int(d.argmin())]]
        for i in near:
            virt.append((n0 + len(virt), i, float(geoms[i].project(p, normalized=True)), which))
    extra = []
    for i in {v[1] for v in virt}:
        chain = sorted([(at, n) for n, at in seg_nodes[i]] + [(v[2], v[0]) for v in virt if v[1] == i])
        for (a, u), (b, v) in zip(chain[:-1], chain[1:]):
            extra.append((u, v, i, a, b, (b - a) * geoms[i].length))
    X = pd.DataFrame(extra, columns=["u", "v", "seg", "a", "b", "len"])
    src = [v[0] for v in virt if v[3] == 0]
    dst = [v[0] for v in virt if v[3] == 1]
    N = n0 + len(virt)
    for with_links in (False, True):
        e = pd.concat([E if with_links else E[~fw.link.values[E.seg.values]], X], ignore_index=True)
        w = np.maximum(e.len.values, 0.01) * np.where(on[e.seg.values], 1.0, np.where(fw.link.values[e.seg.values], 12.0, 5.0))
        G = csr_matrix((w, (e.u.values, e.v.values)), shape=(N, N))
        dist, pred, _ = dijkstra(G, directed=False, indices=src, return_predecessors=True, min_only=True)
        if np.isfinite(dist[dst]).any():
            break
    else:
        raise ValueError("no path")
    end = dst[int(np.argmin(dist[dst]))]
    seq = [end]
    while pred[seq[-1]] >= 0:
        seq.append(pred[seq[-1]])
    seq = seq[::-1]
    best = {}
    for u, v, s, a, b, ln in zip(e.u.values, e.v.values, e.seg.values, e.a.values, e.b.values, w):
        for key, val in (((u, v), (ln, s, a, b)), ((v, u), (ln, s, b, a))):
            if key not in best or val[0] < best[key][0]:
                best[key] = val
    coords = []
    for u, v in zip(seq[:-1], seq[1:]):
        _, s, a, b = best[(u, v)]
        if abs(a - b) < 1e-9:
            continue
        part = substring(geoms[s], min(a, b), max(a, b), normalized=True)
        c = list(part.coords)
        if a > b:
            c = c[::-1]
        coords.extend(c if not coords else c[1:])
    if len(coords) < 2:
        raise ValueError("empty path (both anchors at one point)")
    line = LineString(coords)
    return line, pa.distance(Point(coords[0])), pb.distance(Point(coords[-1]))


def corridor(names, line, width=260.0):
    """The other carriageways of a path: the named mainline segments running along it (middle within `width`
    of the line and between its ends, parallel to it), merged. roads.py dates a segment by the row running
    within 150 m of it: one carriageway does not reach the other across a wide median."""
    idx = named(names)
    geoms = fw.geometry.values[idx]
    if not len(geoms):
        return []
    mids = shapely.line_interpolate_point(geoms, 0.5, normalized=True)
    d = shapely.distance(mids, line)
    s = shapely.line_locate_point(line, mids)
    keep = np.nonzero((d > 12) & (d < width) & (s > 1) & (s < line.length - 1))[0]
    out = []
    for k in keep:
        a, b = np.asarray(geoms[k].coords[0]), np.asarray(geoms[k].coords[-1])
        p0, p1 = line.interpolate(max(s[k] - 60, 0)), line.interpolate(min(s[k] + 60, line.length))
        t, u = b - a, np.array([p1.x - p0.x, p1.y - p0.y])
        if abs(float(t @ u)) > 0.7 * np.linalg.norm(t) * np.linalg.norm(u):
            out.append(geoms[k])
    if not out:
        return []
    m = linemerge(MultiLineString(out))
    return [g for g in getattr(m, "geoms", [m]) if g.length >= 120]


def crossings(names):
    """named main roads and highways crossing a highway, in order along it (to choose anchors)"""
    idx = named(names)
    route_u = shapely.union_all(fw.geometry.values[idx])
    b = route_u.bounds
    along_y = (b[3] - b[1]) > (b[2] - b[0])
    main = gpd.read_parquet(f"{OV}/roads_region.parquet", columns=["name", "class", "geometry"])
    main = main[main.name.notna() & main["class"].isin(["primary", "secondary"])].to_crs(UTM)
    tree = shapely.STRtree(main.geometry.values)
    hit = tree.query(route_u, predicate="dwithin", distance=20.0)
    rows = {}
    for j in hit:
        p = nearest_points(route_u, main.geometry.values[j])[0]
        nm = main.name.values[j]
        key = (nm, int((p.y if along_y else p.x) // 600))
        rows.setdefault(key, p)
    fwn = fw[(fw.name != "") & ~fw.link.values & ~_select(names)]
    for g, nm in zip(fwn.geometry.values, fwn.name.values):
        if g.distance(route_u) < 20:
            p = nearest_points(route_u, g)[0]
            rows.setdefault(("*" + nm, int((p.y if along_y else p.x) // 600)), p)
    out = sorted(rows.items(), key=lambda kv: kv[1].y if along_y else kv[1].x)
    txt = []
    for (nm, _), p in out:
        lon, lat = TO_LL.transform(p.x, p.y)
        txt.append(f"{nm} ({lon:.3f},{lat:.3f})")
    print(f"=== {sorted(names)}: {len(idx)} segments, {'S -> N' if along_y else 'W -> E'}")
    print("  " + " | ".join(txt))


def all_named(names, min_len=120.0):
    idx = named(names)
    if not len(idx):
        raise ValueError(f"no segments named {sorted(names)}")
    m = linemerge(MultiLineString(list(fw.geometry.values[idx])))
    return [g for g in getattr(m, "geoms", [m]) if g.length >= min_len]


def far(names):
    """the path between the two ends of the named highway that are farthest apart"""
    idx = named(names)
    nodes = np.array(sorted({n for i in idx for n, _ in seg_nodes[i]}))
    P = npos[nodes]
    c = P.mean(axis=0)
    a = P[np.argmax(np.hypot(*(P - c).T))]
    b = P[np.argmax(np.hypot(*(P - a).T))]
    a = P[np.argmax(np.hypot(*(P - b).T))]
    la, lb = TO_LL.transform(*a), TO_LL.transform(*b)
    return path(names, ("pt", la[0], la[1]), ("pt", lb[0], lb[1]))


# selection windows for `all` rows: (lon0, lat0, lon1, lat1), or a list of county FIPS codes (the stretch
# inside those counties, from the TIGER outlines)
CLIP = {"nj_turnpike": (-74.32, 40.52, -74.15, 40.68)}


def build_highways(defs, both=False):
    """both: add the other carriageways running along a path (corridor)"""
    rows = []
    for d in defs:
        rid, name, mode, names, A, B, y0, y1, elev, note, url = d
        try:
            if A == "all":
                lines = [(g, 0, 0) for g in all_named(names)]
            elif A == "far":
                lines = [far(names)]
            else:
                lines = [path(names, A, B)]
            if both and A != "all":
                lines += [(g, 0, 0) for g in corridor(names, lines[0][0])]
        except Exception as e:  # noqa: BLE001
            print(f"!! {rid}: {e}")
            continue
        if rid in CLIP:  # a named road that runs far beyond the stretch the row is about
            from shapely.geometry import box
            if isinstance(CLIP[rid], list):
                win = shapely.union_all([county(f) for f in CLIP[rid]])
            else:
                x0, y0_, x1, y1_ = CLIP[rid]
                (ax, bx), (ay, by) = TO_UTM.transform([x0, x1], [y0_, y1_])
                win = box(ax, ay, bx, by)
            cut = []
            for g, da, db in lines:
                part = g.intersection(win)
                cut += [(p, da, db) for p in getattr(part, "geoms", [part]) if p.geom_type == "LineString" and p.length > 120]
            lines = cut
        for k, (g, da, db) in enumerate(lines):
            rows.append([rid, name, mode, y0, y1, elev, k + 1, "lonlat", ll(g), note, url])
        if not lines:
            print(f"!! {rid}: nothing left inside its window")
            continue
        tot = sum(g.length for g, _, _ in lines) / 1000
        g0 = lines[0][0]
        a = TO_LL.transform(*g0.coords[0])
        b = TO_LL.transform(*g0.coords[-1])
        print(f"{rid:34s} {y0:8.2f} {len(lines):2d} line(s) {tot:6.2f} km  {a[0]:.4f},{a[1]:.4f} -> {b[0]:.4f},{b[1]:.4f}"
              + (f"  anchors off by {lines[0][1]:.0f} / {lines[0][2]:.0f} m" if max(lines[0][1], lines[0][2]) > 150 else ""))
    return rows


HEADER = ["route_id", "name", "mode", "year_start", "year_end", "elevated", "segment_seq", "geom_type", "geom", "note",
          "source_url"]

if __name__ == "__main__":
    sys.path.insert(0, HERE)
    import hw_defs
    import hw_defs_counties
    CLIP.update(hw_defs_counties.CLIP)
    out = f"{ROOT}/data/manual/routes.csv"
    if len(sys.argv) > 1 and sys.argv[1] == "cross":
        for a in sys.argv[2:]:
            crossings(set(a.split("|")))
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        # everything from scratch. The city's rows were built on the extract of the city box: with the wider
        # extract an anchor "end of the named highway" lies further out (hw_defs_counties redefines those rows)
        gone = {d[0] for d in hw_defs_counties.DEFS} | set(hw_defs_counties.REPLACED)
        rows = build_highways([d for d in hw_defs.DEFS if d[0] not in gone])
        for mod in ("ferry_defs", "ohm_roads"):
            try:
                m = __import__(mod)
                rows += m.rows(globals())
            except ImportError:
                print(f"(no {mod}.py yet)")
    else:
        # the counties' rows only: every other row stays as it is in the file
        gone = {d[0] for d in hw_defs_counties.DEFS} | set(hw_defs_counties.REPLACED)
        with open(out, newline="") as f:
            old = list(csv.reader(f))
        assert old[0] == HEADER, old[0]
        rows = [r for r in old[1:] if r[0] not in gone]
        print(f"kept {len(rows)} of {len(old) - 1} rows of routes.csv")
    rows += build_highways(hw_defs_counties.DEFS, both=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    print(f"{len(rows)} rows -> data/manual/routes.csv")
