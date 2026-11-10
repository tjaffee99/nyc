"""Coordinates from data on disk, never from memory.

Copied from data/manual/fill_tools/streets.py (the city's fill zones); only the data folder differs.
Named street centre lines come from the Overture extracts (roads_region + roads_local), today's
water from base_water.  Everything metric is UTM 18N (EPSG:32618); rings are written as WGS84.

  S = Streets((-74.03, 40.69, -73.96, 40.76))     # lon/lat window
  p = S.x('Pearl Street', 'Whitehall Street')      # intersection (closest approach) -> (x, y)
  line = S.along('Pearl Street', p, q)             # polyline along the named street p -> q
  S.land()                                         # today's land in the window = window - water
"""
import heapq, math, os
import duckdb
import numpy as np
from pyproj import Transformer
from shapely import wkb
from shapely.geometry import LineString, MultiLineString, Point, Polygon, box
from shapely.ops import linemerge, unary_union, transform as shp_transform

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OV = os.path.join(ROOT, 'data', 'raw', 'fill_counties', 'overture')   # this part's extracts of the wider box (download_overture.py)
_fwd = Transformer.from_crs(4326, 32618, always_xy=True)
_inv = Transformer.from_crs(32618, 4326, always_xy=True)


def to_utm(g):
    return shp_transform(lambda x, y, z=None: _fwd.transform(x, y), g)


def to_ll(g):
    return shp_transform(lambda x, y, z=None: _inv.transform(x, y), g)


def ll(p):
    """(x, y) UTM -> (lon, lat)."""
    return _inv.transform(p[0], p[1])


def utm(lon, lat):
    return _fwd.transform(lon, lat)


def _q(con, file, bbox, cols, where='true'):
    w, s, e, n = bbox
    return con.execute(
        f"select {cols}, ST_AsWKB(geometry) from '{OV}/{file}.parquet' "
        f"where {where} and ST_XMax(geometry) >= {w} and ST_XMin(geometry) <= {e} "
        f"and ST_YMax(geometry) >= {s} and ST_YMin(geometry) <= {n}").fetchall()


def con():
    c = duckdb.connect()
    c.execute('install spatial; load spatial;')
    return c


class Streets:
    def __init__(self, bbox):
        self.bbox = bbox
        self.con = con()
        self.by = {}
        for f in ('roads_region', 'roads_local'):
            for name, g in _q(self.con, f, bbox, 'name', 'name is not null'):
                self.by.setdefault(name, []).append(to_utm(wkb.loads(bytes(g))))
        self._land = None

    def geom(self, name):
        if name not in self.by:
            cand = [n for n in self.by if name.lower() in n.lower()]
            raise KeyError(f'{name!r} not in window; similar: {cand[:8]}')
        return unary_union(self.by[name])

    def x(self, a, b, near=None, tol=40.0):
        """Intersection of streets a and b; closest approach if they stop short (<= tol m).
        near=(x, y) UTM picks one of several crossings."""
        ga, gb = self.geom(a), self.geom(b)
        it = ga.intersection(gb)
        pts = []
        if not it.is_empty:
            for g in getattr(it, 'geoms', [it]):
                c = g.centroid if g.geom_type != 'Point' else g
                pts.append((c.x, c.y))
        if not pts:
            from shapely.ops import nearest_points
            pa, pb = nearest_points(ga, gb)
            d = pa.distance(pb)
            if d > tol:
                raise ValueError(f'{a} & {b}: closest approach {d:.0f} m')
            pts = [((pa.x + pb.x) / 2, (pa.y + pb.y) / 2)]
        if near is not None:
            pts.sort(key=lambda p: math.hypot(p[0] - near[0], p[1] - near[1]))
        elif len(pts) > 1:
            # several crossings (dual carriageway): take the mean if they are close together
            xs, ys = zip(*pts)
            if max(xs) - min(xs) < 60 and max(ys) - min(ys) < 60:
                pts = [(sum(xs) / len(xs), sum(ys) / len(ys))]
            else:
                raise ValueError(f'{a} & {b}: {len(pts)} crossings, give near=: '
                                 + '; '.join('%.5f %.5f' % ll(p) for p in pts))
        return pts[0]

    def along(self, name, p, q, bridge=45.0):
        """Shortest path along the named street's own segments from p to q (UTM points).
        Gaps up to `bridge` m between pieces are jumped."""
        g = self.geom(name)
        lines = list(getattr(g, 'geoms', [g]))
        nodes, idx, adj = [], {}, {}

        def nid(c):
            k = (round(c[0], 1), round(c[1], 1))
            if k not in idx:
                idx[k] = len(nodes); nodes.append(k); adj[idx[k]] = []
            return idx[k]
        ends = []
        for l in lines:
            cs = list(l.coords)
            ids = [nid(c) for c in cs]
            for i in range(len(ids) - 1):
                d = math.dist(nodes[ids[i]], nodes[ids[i + 1]])
                adj[ids[i]].append((ids[i + 1], d)); adj[ids[i + 1]].append((ids[i], d))
            ends += [ids[0], ids[-1]]
        ends = sorted(set(ends))
        for i in ends:
            for j in ends:
                if i < j:
                    d = math.dist(nodes[i], nodes[j])
                    if 0 < d <= bridge:
                        adj[i].append((j, d * 3)); adj[j].append((i, d * 3))
        arr = np.array(nodes)
        a = int(np.argmin(np.hypot(arr[:, 0] - p[0], arr[:, 1] - p[1])))
        b = int(np.argmin(np.hypot(arr[:, 0] - q[0], arr[:, 1] - q[1])))
        dist, prev, pq = {a: 0.0}, {}, [(0.0, a)]
        while pq:
            d, u = heapq.heappop(pq)
            if u == b:
                break
            if d > dist.get(u, 1e18):
                continue
            for v, w in adj[u]:
                nd = d + w
                if nd < dist.get(v, 1e18):
                    dist[v] = nd; prev[v] = u; heapq.heappush(pq, (nd, v))
        if b not in dist:
            raise ValueError(f'{name}: no path between the two points (gap > {bridge} m)')
        path, u = [b], b
        while u != a:
            u = prev[u]; path.append(u)
        pts = [nodes[i] for i in reversed(path)]
        if math.dist(pts[0], p) > 1:
            pts.insert(0, tuple(p))
        if math.dist(pts[-1], q) > 1:
            pts.append(tuple(q))
        return pts

    def between(self, name, a, b, **kw):
        """along(name) from its crossing with street a to its crossing with street b."""
        return self.along(name, self.x(name, a), self.x(name, b), **kw)

    def crossings(self, name, lo=None, hi=None):
        """Named streets that meet `name`, with the crossing point."""
        g = self.geom(name)
        out = []
        for n, gs in self.by.items():
            if n == name:
                continue
            u = unary_union(gs)
            if u.distance(g) < 1.0:
                it = u.intersection(g.buffer(1.0)).centroid
                out.append((n, (it.x, it.y)))
        return out

    def water(self):
        rows = _q(self.con, 'base_water', self.bbox, 'subtype',
                  "subtype not in ('human_made')")
        return unary_union([polygonal(to_utm(wkb.loads(bytes(g)))) for _, g in rows
                            if wkb.loads(bytes(g)).geom_type in ('Polygon', 'MultiPolygon')])

    def land(self):
        """Today's land inside the window: window minus Overture water polygons."""
        if self._land is None:
            w, s, e, n = self.bbox
            self._land = to_utm(box(w, s, e, n)).difference(self.water())
        return self._land


def polygonal(g):
    """Valid polygonal version of g.  (Changed from the city's tools: buffer(0) silently dropped most
    of a self-touching outline, e.g. the Morris Canal Basin, which then counted as land.)"""
    if g.is_valid:
        return g
    from shapely import make_valid
    m = make_valid(g)
    ps = [p for p in getattr(m, 'geoms', [m]) if p.geom_type in ('Polygon', 'MultiPolygon')]
    return unary_union(ps) if ps else g.buffer(0)


def offset(p, q, d):
    """Point d metres to the LEFT of p when walking p -> q (negative = right)."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    h = math.hypot(dx, dy)
    return (p[0] - dy / h * d, p[1] + dx / h * d)


def extend(p, q, d):
    """Point d metres beyond q on the line p -> q."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    h = math.hypot(dx, dy)
    return (q[0] + dx / h * d, q[1] + dy / h * d)


def poly(*parts):
    """Polygon from points and point lists (UTM), in order."""
    pts = []
    for part in parts:
        if isinstance(part, tuple) and len(part) == 2 and not isinstance(part[0], tuple):
            pts.append(part)
        else:
            pts.extend(part)
    out = [pts[0]]
    for c in pts[1:]:
        if math.dist(c, out[-1]) > 0.5:
            out.append(c)
    return Polygon(out)


def biggest(g):
    if g.geom_type == 'Polygon':
        return g
    return max(g.geoms, key=lambda x: x.area)


def ring_str(pg, tol=2.0, dec=6):
    """UTM polygon -> 'lon lat; lon lat; ...' (exterior only, simplified, not closed)."""
    pg = biggest(pg).simplify(tol)
    cs = list(pg.exterior.coords)[:-1]
    return '; '.join(f'{lo:.{dec}f} {la:.{dec}f}' for lo, la in (ll(c) for c in cs))


def parse_ring(s):
    return Polygon([utm(*map(float, t.split())) for t in s.split(';') if t.strip()])


def describe(name, pg):
    c = ll((pg.centroid.x, pg.centroid.y))
    return f'{name:38s} valid={pg.is_valid} area={pg.area/1e4:8.2f} ha  centroid {c[0]:.5f} {c[1]:.5f}  n={len(pg.exterior.coords)-1}'


def island_streets(bbox, seed_a, seed_b, pad=40.0):
    """Streets of a window restricted to the land mass (window minus water) that contains the
    crossing of seed_a & seed_b -- e.g. Manhattan Island only, so that Brooklyn's Water Street
    or Front Street cannot be picked up by name."""
    S = Streets(bbox)
    land = S.land()
    seed = Point(S.x(seed_a, seed_b))
    comp = [g for g in getattr(land, 'geoms', [land]) if g.contains(seed)][0]
    S.island = comp
    from shapely.prepared import prep
    pc = prep(comp.buffer(pad))
    for n in list(S.by):
        keep = [g for g in S.by[n] if pc.intersects(g)]
        if keep:
            S.by[n] = keep
        else:
            del S.by[n]
    return S
