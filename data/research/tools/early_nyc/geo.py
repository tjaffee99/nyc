"""Geocoding and checks for early_nyc.csv (scratch tool, not a pipeline stage).

X(a, b, hint)   intersection of two named streets (Overture roads), nearest to hint (lon, lat)
LM(text)        centroid of an LPC individual landmark whose name contains text
PK(text)        representative point of a city park whose sign name contains text
check(lon,lat)  1609 cover at the point, open water today, footprints within 150 m, borough
"""
import json, math, os, pickle, zipfile
import duckdb, shapely
from shapely import wkb
from shapely.geometry import shape, Point
from shapely.ops import unary_union, nearest_points
from shapely.strtree import STRtree

ROOT = '/home/user/nyc'
OV = ROOT + '/data/raw/overture/2026-10-21.0'
HERE = os.path.dirname(os.path.abspath(__file__))
_c = {}

def roads():
    if 'roads' in _c: return _c['roads']
    pk = HERE + '/roads.pkl'
    if os.path.exists(pk):
        _c['roads'] = pickle.load(open(pk, 'rb')); return _c['roads']
    con = duckdb.connect(); con.execute('install spatial; load spatial')
    d = {}
    for f in ('roads_local', 'roads_region'):
        for name, g in con.execute(f"select name, ST_AsWKB(geometry) from '{OV}/{f}.parquet' where name is not null").fetchall():
            d.setdefault(name.lower(), []).append(wkb.loads(bytes(g)))
    pickle.dump(d, open(pk, 'wb'))
    _c['roads'] = d; return d

def _near(geoms, hint, r=0.03):
    if hint is None: return geoms
    p = Point(hint)
    return [g for g in geoms if g.distance(p) < r]

def X(a, b, hint=None, tol=0.0006):
    R = roads()
    ga, gb = R.get(a.lower()), R.get(b.lower())
    if not ga: raise KeyError('no street ' + a)
    if not gb: raise KeyError('no street ' + b)
    ga, gb = _near(ga, hint), _near(gb, hint)
    if not ga or not gb: raise KeyError(f'{a} x {b}: not near hint')
    ua, ub = unary_union(ga), unary_union(gb)
    it = ua.intersection(ub)
    pts = []
    if not it.is_empty:
        for g in getattr(it, 'geoms', [it]):
            pts.append(g.representative_point() if g.geom_type != 'Point' else g)
    if not pts:
        pa, pb = nearest_points(ua, ub)
        if pa.distance(pb) > tol: raise KeyError(f'{a} x {b}: no intersection (gap {pa.distance(pb)*111000:.0f} m)')
        pts = [Point((pa.x + pb.x) / 2, (pa.y + pb.y) / 2)]
    if hint is not None:
        h = Point(hint); pts.sort(key=lambda q: q.distance(h))
    return (round(pts[0].x, 6), round(pts[0].y, 6))

def streets_like(s, hint=None):
    R = roads(); out = []
    for k, v in R.items():
        if s.lower() in k:
            if hint is None or _near(v, hint): out.append(k)
    return sorted(out)

def _lm():
    if 'lm' not in _c:
        g = json.load(open(ROOT + '/data/raw/nyc/lpc_individual_landmarks.geojson'))
        _c['lm'] = [(f['properties'].get('lpc_name') or '', f['properties'].get('address') or '', f['properties'].get('borough'), Point(float(f['properties']['longitude']), float(f['properties']['latitude']))) for f in g['features'] if f['properties'].get('longitude')]
    return _c['lm']

def LM(text, all=False):
    hits = [(n, a, b, s) for n, a, b, s in _lm() if text.lower() in n.lower()]
    if all: return [(n, a, b, round(s.centroid.x, 6), round(s.centroid.y, 6)) for n, a, b, s in hits]
    if not hits: raise KeyError('no landmark ' + text)
    c = hits[0][3].centroid
    return (round(c.x, 6), round(c.y, 6))

def _pk():
    if 'pk' not in _c:
        g = json.load(open(ROOT + '/data/raw/nyc/parks_properties.geojson'))
        _c['pk'] = [(f['properties'].get('signname') or '', f['properties'].get('borough'), shape(f['geometry'])) for f in g['features'] if f['geometry']]
    return _c['pk']

def PK(text, all=False):
    hits = [(n, b, s) for n, b, s in _pk() if text.lower() in n.lower()]
    if all: return [(n, b, round(s.representative_point().x, 6), round(s.representative_point().y, 6), round(s.area * 111000 * 85000 / 1e4, 1)) for n, b, s in hits]
    if not hits: raise KeyError('no park ' + text)
    hits.sort(key=lambda h: -h[2].area)
    c = hits[0][2].representative_point()
    return (round(c.x, 6), round(c.y, 6))

def off(p, east_m=0, north_m=0):
    kx = 111320 * math.cos(math.radians(p[1]))
    return (round(p[0] + east_m / kx, 6), round(p[1] + north_m / 110574, 6))

def _nat():
    if 'nat' not in _c:
        g = json.load(open(ROOT + '/data/manual/natural/natural_1609.geojson'))
        geoms = [shape(f['geometry']) for f in g['features']]
        covers = [f['properties']['cover'] for f in g['features']]
        _c['nat'] = (STRtree(geoms), geoms, covers)
    return _c['nat']

def _water():
    if 'water' not in _c:
        con = duckdb.connect(); con.execute('install spatial; load spatial')
        rows = con.execute(f"select ST_AsWKB(geometry) from '{OV}/base_water.parquet' where subtype in ('water','river','ocean','lake','physical','canal','reservoir','pond') and class not in ('swimming_pool','wastewater','basin','shoal')").fetchall()
        geoms = [wkb.loads(bytes(r[0])) for r in rows]
        geoms = [g for g in geoms if g.geom_type in ('Polygon', 'MultiPolygon')]
        _c['water'] = (STRtree(geoms), geoms)
    return _c['water']

def _boro():
    if 'boro' not in _c:
        import geopandas as gpd
        df = gpd.read_file('zip://' + ROOT + '/data/raw/tiger/tl_2024_us_county.zip', where="STATEFP='36' AND COUNTYFP IN ('005','047','061','081','085')")
        names = {'005': 'Bronx', '047': 'Brooklyn', '061': 'Manhattan', '081': 'Queens', '085': 'Staten Island'}
        _c['boro'] = [(names[r.COUNTYFP], r.geometry) for r in df.to_crs(4326).itertuples()]
    return _c['boro']

def borough(lon, lat):
    p = Point(lon, lat)
    for n, g in _boro():
        if g.contains(p): return n
    best = min(_boro(), key=lambda r: r[1].distance(p))
    return best[0] + '?' if best[1].distance(p) < 0.01 else 'OUTSIDE'

def cover1609(lon, lat):
    tree, geoms, covers = _nat(); p = Point(lon, lat)
    hit = [covers[i] for i in tree.query(p) if geoms[i].contains(p)]
    return ','.join(sorted(set(hit))) or 'dry'

def dist_to_wet(lon, lat, kinds=('water', 'tidal_marsh', 'tidal_flat')):
    tree, geoms, covers = _nat(); p = Point(lon, lat)
    best = 9e9
    for i in tree.query(p.buffer(0.01)):
        if covers[i] in kinds:
            best = min(best, geoms[i].distance(p))
    return round(best * 96000) if best < 9e9 else 9999

def water_today(lon, lat):
    tree, geoms = _water(); p = Point(lon, lat)
    return any(geoms[i].contains(p) for i in tree.query(p))

_fp = None
def footprints(lon, lat, r=150):
    global _fp
    if _fp is None: _fp = duckdb.connect()
    dx = r / (111320 * math.cos(math.radians(lat))); dy = r / 110574
    rows = _fp.execute(f"""select name, year_raw, lon, lat from '{ROOT}/data/interim/nyc_footprints_raw.parquet'
        where lon between {lon-dx} and {lon+dx} and lat between {lat-dy} and {lat+dy}""").fetchall()
    kx = 111320 * math.cos(math.radians(lat))
    rows = [(n, y, math.hypot((x - lon) * kx, (yy - lat) * 110574)) for n, y, x, yy in rows]
    rows = [t for t in rows if t[2] <= r]
    names = sorted({t[0] for t in rows if t[0]})
    return len(rows), names[:3]

def check(lon, lat):
    n, names = footprints(lon, lat)
    return dict(boro=borough(lon, lat), c1609=cover1609(lon, lat), wet_m=dist_to_wet(lon, lat), water_today=water_today(lon, lat), n150=n, names=names)
