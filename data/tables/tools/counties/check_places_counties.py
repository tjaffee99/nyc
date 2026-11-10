"""Checks on places_counties.csv: bounding box, county containment (TIGER 2024), footprints within ~300 m (Overture region extract), hand anchors vs article coordinates."""
import csv, json, math, os, duckdb, geopandas as gpd
HERE = os.path.dirname(os.path.abspath(__file__))
from shapely.geometry import Point
rows = list(csv.DictReader(open('/home/user/nyc/data/tables/places_counties.csv', encoding='utf-8')))
src = json.load(open(os.path.join(HERE, 'places_counties_coordsrc.json')))
cache = json.load(open('/home/user/nyc/data/raw/tables_counties/wp_coords.json'))
FP = {'Bergen': ('34', '003'), 'Essex': ('34', '013'), 'Hudson': ('34', '017'), 'Passaic': ('34', '031'), 'Union': ('34', '039'), 'Nassau': ('36', '059'), 'Rockland': ('36', '087'), 'Westchester': ('36', '119')}
co = gpd.read_file('zip:///home/user/nyc/data/raw/tiger/tl_2024_us_county.zip', where="STATEFP IN ('34','36')").to_crs(32618)
poly = {n: co[(co.STATEFP == s) & (co.COUNTYFP == c)].geometry.iloc[0] for n, (s, c) in FP.items()}
pts = gpd.GeoSeries([Point(float(r['lon']), float(r['lat'])) for r in rows], crs=4326).to_crs(32618)
con = duckdb.connect()
con.execute("CREATE TABLE p AS SELECT id, CAST(lat AS DOUBLE) lat, CAST(lon AS DOUBLE) lon FROM read_csv('/home/user/nyc/data/tables/places_counties.csv', all_varchar=true)")
q = con.execute("""SELECT p.id, count(f.lon) FROM p LEFT JOIN read_parquet('/home/user/nyc/data/raw/overture/2026-10-21.0/region_building.parquet') f
 ON f.lon BETWEEN p.lon - 0.0036 AND p.lon + 0.0036 AND f.lat BETWEEN p.lat - 0.0027 AND p.lat + 0.0027 GROUP BY p.id""").fetchall()
fp = dict(q)
def dist(a, b):
    return math.hypot((a[0] - b[0]) * 111000, (a[1] - b[1]) * 111000 * math.cos(math.radians(a[0])))
bad = []; far = []
for r, pt in zip(rows, pts):
    flag = []
    la, lo = float(r['lat']), float(r['lon'])
    if not (40.47 <= la <= 41.38 and -74.52 <= lo <= -73.40): flag.append('out of box')
    if r['county']:
        d = poly[r['county']].distance(pt)
        if d > 0: flag.append(f'outside {r["county"]} by {d:.0f} m')
    else:
        d = min(g.distance(pt) for g in poly.values())
        if d > 0: flag.append(f'outside the eight counties by {d:.0f} m')
    n = fp.get(r['id'], 0)
    if r['tier'] in ('town', 'city', 'neighborhood') and n < 15: flag.append(f'only {n} footprints within ~300 m')
    if flag: bad.append((r['id'], r['tier'], r['lat'], r['lon'], src[r['id']][:28], '; '.join(flag)))
    if src[r['id']] == 'hand':
        t = __import__('urllib.parse').parse.unquote(r['source_url'].split('/wiki/')[1]).replace('_', ' ')
        v = cache.get(t)
        if v and v != 'MISSING':
            dd = dist((la, lo), v)
            if dd > 1500: far.append((r['id'], round(dd), t))
print(len(rows), 'rows;', len(bad), 'flagged')
for b in bad: print(' ', b)
print('hand anchors more than 1.5 km from the cited article coordinates:', far)
import collections
print('coordinate sources:', collections.Counter(s.split(':')[0] for s in src.values()))
json.dump(fp, open(os.path.join(HERE, 'places_counties_fpcheck.json'), 'w'))
