import csv, json, duckdb, geopandas as gpd, shapely, math
from shapely.geometry import Point
rows = list(csv.DictReader(open('/home/user/nyc/data/tables/places.csv', encoding='utf-8')))
src = json.load(open('places_coordsrc.json'))
co = gpd.read_file('zip:///home/user/nyc/data/raw/tiger/tl_2024_us_county.zip', where="STATEFP='36' AND COUNTYFP IN ('005','047','061','081','085')").to_crs(32618)
name = {'005': 'The Bronx', '047': 'Brooklyn', '061': 'Manhattan', '081': 'Queens', '085': 'Staten Island'}
poly = {name[r.COUNTYFP]: r.geometry for r in co.itertuples()}
pts = gpd.GeoSeries([Point(float(r['lon']), float(r['lat'])) for r in rows], crs=4326).to_crs(32618)
con = duckdb.connect()
con.execute("CREATE TABLE p AS SELECT * FROM read_csv_auto('/home/user/nyc/data/tables/places.csv')")
q = con.execute("""
SELECT p.id, count(f.lon) AS n, quantile_cont(CASE WHEN f.year_raw BETWEEN 1650 AND 2026 THEN f.year_raw END, 0.1) AS y10
FROM p LEFT JOIN read_parquet('/home/user/nyc/data/interim/nyc_footprints_raw.parquet') f
 ON f.lon BETWEEN p.lon - 0.0036 AND p.lon + 0.0036 AND f.lat BETWEEN p.lat - 0.0027 AND p.lat + 0.0027
GROUP BY p.id""").fetchall()
fp = {i: (n, y) for i, n, y in q}
bad = []
for r, pt in zip(rows, pts):
    b = r['county']
    d = poly[b].distance(pt) if b else min(g.distance(pt) for g in poly.values())
    n, y10 = fp.get(r['id'], (0, None))
    flag = []
    if d > 0: flag.append(f'outside {b or "city"} by {d:.0f} m')
    if r['tier'] in ('neighborhood', 'town', 'city') and n < 15: flag.append(f'only {n} footprints within ~300 m')
    if flag: bad.append((r['id'], r['name'], r['tier'], r['lat'], r['lon'], src.get(r['id']), '; '.join(flag)))
print(len(rows), 'rows;', len(bad), 'flagged')
for b in bad: print(b)
json.dump({i: [n, y] for i, (n, y) in fp.items()}, open('places_fpcheck.json', 'w'))
