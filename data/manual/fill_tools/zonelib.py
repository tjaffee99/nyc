"""Shared helpers for the zone builders: registry, line offsets, clipping to today's land."""
import csv, json, math, os, pickle, sys
import numpy as np
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(__file__))
from streets import (Streets, island_streets, to_utm, to_ll, ll, utm, offset, extend, poly,
                     biggest, ring_str, parse_ring, describe, ROOT, OV, con, _q)

INTERIM = os.path.join(ROOT, 'data', 'interim', 'fill')
COLS = ['zone_id', 'name', 'borough', 'year_start', 'year_end', 'ring_type', 'ring', 'kind',
        'precision', 'note', 'source_url']
KINDS = {'fill', 'pond_fill', 'excavation', 'water_fill', 'reservoir'}
BORO = {'mn': 'Manhattan', 'bk': 'Brooklyn', 'qn': 'Queens', 'bx': 'Bronx',
        'si': 'Staten Island', 'hb': 'Harbour islands'}


class Registry:
    def __init__(self):
        self.rows, self.geom = [], {}

    def add(self, zid, name, y0, y1, pg, kind, precision, note, url, tol=2.0, borough=None, minus=(), close=0.0):
        assert kind in KINDS and precision in ('precise', 'coarse'), (zid, kind, precision)
        assert zid not in self.geom, zid
        assert y0 <= y1, zid
        for other in minus:                 # keep clear of zones registered earlier
            pg = pg.difference(self.geom[other].buffer(0.3))
        pg = pg.buffer(0)
        if close:                           # coarse rings: bridge creeks and slips so that one ring covers all the parts
            assert precision == 'coarse'
            pg = pg.buffer(close).buffer(-close)
        parts = sorted(getattr(pg, 'geoms', [pg]), key=lambda g: -g.area)
        lost = sum(g.area for g in parts[1:])
        if lost > max(3000.0, 0.03 * parts[0].area):     # a ring is one polygon: say so when real area is dropped
            print(f'   WARNING {zid}: kept {parts[0].area / 1e4:.2f} ha, dropped {lost / 1e4:.2f} ha:',
                  ['%.1f ha at %.4f %.4f' % ((g.area / 1e4,) + ll((g.centroid.x, g.centroid.y))) for g in parts[1:4]])
        pg = biggest(pg).simplify(tol)
        pg = Polygon(pg.exterior)          # exterior only
        for k in range(6):                 # the ring must still be a valid polygon after rounding to 6 decimals
            s = ring_str(pg, tol=0)
            if parse_ring(s).is_valid and pg.is_valid:
                break
            pg = Polygon(biggest(pg.buffer(0.6 + k).buffer(-(0.6 + k))).simplify(tol + k).exterior)
        pg = parse_ring(s)
        assert pg.is_valid and pg.area > 0, zid
        self.geom[zid] = pg
        self.rows.append(dict(zone_id=zid, name=name, borough=borough or BORO[zid[:2]],
                              year_start=y0, year_end=y1, ring_type='lonlat',
                              ring=s, kind=kind, precision=precision,
                              note=note, source_url=url))
        print(describe(f'{zid} {y0}-{y1}', pg))

    def save(self, tag):
        json.dump(self.rows, open(os.path.join(INTERIM, f'rows_{tag}.json'), 'w'), indent=0)
        print(f'saved {len(self.rows)} rows -> rows_{tag}.json')


def mn():
    return pickle.load(open(os.path.join(INTERIM, 'mn_streets.pkl'), 'rb'))


def line_offset(pts, d, away_from):
    """Offset polyline by d metres on the side AWAY from the point/geometry away_from.
    The side is read where the line passes closest to that point (cross product), so a reference
    point anywhere on the inland side works, also for long curved lines."""
    l = LineString(pts)
    ref = away_from if hasattr(away_from, 'geom_type') else Point(away_from)
    if ref.geom_type != 'Point':
        ref = ref.interpolate(0.5, normalized=True) if ref.geom_type == 'LineString' else ref.representative_point()
    sp = l.project(ref)
    sp = min(max(sp, 1.0), l.length - 1.0)
    p, q = l.interpolate(sp - 1.0), l.interpolate(sp + 1.0)
    cross = (q.x - p.x) * (ref.y - p.y) - (q.y - p.y) * (ref.x - p.x)      # > 0: ref lies to the left
    best = l.offset_curve(-d if cross > 0 else d)                           # shapely: positive = left
    if best.geom_type != 'LineString':
        best = max(best.geoms, key=lambda g: g.length)
    cs = list(best.coords)
    if math.dist(cs[0], pts[0]) > math.dist(cs[-1], pts[0]):
        cs.reverse()
    return cs


def band(inner, outer):
    """Polygon between two polylines that run in the same direction."""
    return poly(list(inner), list(reversed(list(outer)))).buffer(0)


def seaward(line, d, inland_pt, land, back=0.0):
    """Today's land on the seaward side of `line` (out to d metres), i.e. the strip between a
    street / bulkhead line and the present shore.  back>0 starts the strip that far inland."""
    inner = line if back == 0 else line_offset(line, back, LineString(line_offset(line, 50, inland_pt)))
    outer = line_offset(line, d, inland_pt)
    return band(inner, outer).intersection(land)


def end_of(S, name, side):
    """Extreme end of a named street: side in 'E','W','N','S'."""
    cs = [c for g in S.by[name] for c in g.coords]
    k = {'E': lambda c: c[0], 'W': lambda c: -c[0], 'N': lambda c: c[1], 'S': lambda c: -c[1]}[side]
    return max(cs, key=k)


def write_csv(path, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def land_of(bbox):
    """Today's land (window minus Overture water), UTM."""
    return Streets.land(type('T', (), {'bbox': bbox, 'con': con(), '_land': None,
                                       'water': Streets.water})())


def near_on(S, name, pt):
    from shapely.ops import nearest_points
    p, _ = nearest_points(S.geom(name), Point(pt))
    return (p.x, p.y)


def XX(S, a, b):
    """x() that averages several crossings instead of failing."""
    try:
        return S.x(a, b)
    except ValueError as e:
        if 'crossings' not in str(e):
            raise
        it = S.geom(a).intersection(S.geom(b))
        pts = [(g.centroid.x, g.centroid.y) for g in it.geoms]
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def nb_line(S, name, A, B, inland_side=+1, step=50.0, reach=70.0):
    """The carriageway of a dual road lying furthest to the RIGHT (inland_side=+1) when walking A -> B."""
    L = LineString(S.along(name, A, B, bridge=200)); W = S.geom(name); out = []
    for s in np.arange(0, L.length, step):
        p = L.interpolate(s); q = L.interpolate(min(s + 5, L.length))
        dx, dy = q.x - p.x, q.y - p.y; h = math.hypot(dx, dy)
        if h == 0: continue
        nx, ny = dy / h * inland_side, -dx / h * inland_side
        it = W.intersection(LineString([(p.x - nx * reach, p.y - ny * reach), (p.x + nx * reach, p.y + ny * reach)]))
        pts = [g for g in getattr(it, 'geoms', [it]) if g.geom_type == 'Point']
        if pts:
            e = max(pts, key=lambda g: (g.x - p.x) * nx + (g.y - p.y) * ny); out.append((e.x, e.y))
    return out


def li():
    return pickle.load(open(os.path.join(INTERIM, 'li_streets.pkl'), 'rb'))


_c = None


def named(name, table='region5_land_use', cls=None, all_parts=False, near=None):
    """Polygon(s) of a named Overture feature, UTM.  near=(x, y) picks the closest one."""
    global _c
    from shapely import wkb as _wkb
    _c = _c or con()
    q = f"select ST_AsWKB(geometry) from '{OV}/{table}.parquet' where name = ?" + (f" and class='{cls}'" if cls else '')
    gs = [to_utm(_wkb.loads(bytes(g))).buffer(0) for g, in _c.execute(q, [name]).fetchall()]
    gs = [g for g in gs if g.geom_type in ('Polygon', 'MultiPolygon')]
    if not gs:
        raise KeyError(f'no polygon named {name!r} in {table}')
    if near is not None:
        gs.sort(key=lambda g: g.distance(Point(near)))
        return gs[0]
    return unary_union(gs) if all_parts else max(gs, key=lambda g: g.area)


def run_zone(fn):
    import traceback
    try:
        fn()
    except Exception as e:
        print('!! FAILED', repr(e)[:260])


def sub(S, w, s, e, n):
    """Copy of a street index restricted to a lon/lat box (to tell apart streets that share a
    name in different neighbourhoods).  The box only filters; coordinates still come from data."""
    import copy
    from shapely.geometry import box as _box
    b = to_utm(_box(w, s, e, n))
    T = copy.copy(S)
    T.by = {}
    for k, gs in S.by.items():
        keep = [g for g in gs if g.intersects(b)]
        if keep:
            T.by[k] = keep
    return T


def corridor(a, b, width):
    """Buffer round the shortest line between two geometries."""
    from shapely.ops import nearest_points
    p, q = nearest_points(a, b)
    return LineString([p, q]).buffer(width)


def trim_path(path, p0, p1, slack=60.0):
    """Drop detours at the ends of a path returned by Streets.along (dual carriageways can make the
    shortest path run past its start and come back): keep from the LAST vertex near p0 to the
    FIRST later vertex near p1."""
    d0 = min(math.dist(v, p0) for v in path) + slack
    d1 = min(math.dist(v, p1) for v in path) + slack
    i = max(k for k, v in enumerate(path) if math.dist(v, p0) <= d0)
    js = [k for k, v in enumerate(path) if k > i and math.dist(v, p1) <= d1]
    j = js[0] if js else len(path) - 1
    return path[i:j + 1]


def fdr_segments(S):
    """FDR Drive centre line from Jackson St to E 125th St as one path, cut at the east ends of the
    cross streets, so that neighbouring East River zones share their corner vertices."""
    names = ['Jackson', '14th', '23rd', '34th', '42nd', '49th', '96th', '125th']
    pts = [S.x('South Street', 'Jackson Street')] + [end_of(S, f'East {n} Street', 'E') for n in names[1:]]
    full = trim_path(S.along('FDR Drive', pts[0], pts[-1], bridge=500), pts[0], pts[-1])
    idx = [min(range(len(full)), key=lambda i: math.dist(full[i], p)) for p in pts]
    assert idx == sorted(idx), idx
    return {(names[i], names[i + 1]): full[idx[i]:idx[i + 1] + 1] for i in range(len(names) - 1)}
