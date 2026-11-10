"""Merge the per-area rows (written by zones_*.py) into data/manual/fill_zones_counties.csv and check the file.

  cd data/manual/fill_counties_tools; for m in zones_hud_a zones_hud_b zones_nj zones_ny; do ../../../.venv/bin/python $m.py; done
  ../../../.venv/bin/python build_zones.py
"""
import collections, csv, itertools, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from zonelib import COLS, INTERIM, KINDS, ROOT, BORO, parse_ring, write_csv, ll, muni, Point

ORDER = ['hud_a', 'hud_b', 'nj', 'ny']
COUNTIES = ['Hudson', 'Bergen', 'Essex', 'Union', 'Passaic', 'Westchester', 'Nassau', 'Rockland']
OUT = os.path.join(ROOT, 'data', 'manual', 'fill_zones_counties.csv')
BOX = (-74.52, 40.47, -73.40, 41.38)          # pipeline/common.REGION_BBOX

rows = []
for tag in ORDER:
    rows += json.load(open(os.path.join(INTERIM, f'rows_{tag}.json')))
rows.sort(key=lambda r: COUNTIES.index(r['borough']))          # stable: keeps the order inside a county
for r in rows:
    for k in ('year_start', 'year_end'):
        v = float(r[k]); r[k] = int(v) if v == int(v) else round(v, 2)
write_csv(OUT, rows)

rd = list(csv.DictReader(open(OUT, encoding='utf-8')))
assert list(rd[0].keys()) == COLS
ids = [r['zone_id'] for r in rd]
assert len(ids) == len(set(ids)), 'duplicate zone_id'
geo, bad = {}, 0
cty = {c: muni(c + ' County', 'county') for c in COUNTIES}
for r in rd:
    pg = parse_ring(r['ring'])
    lo, la = ll((pg.centroid.x, pg.centroid.y))
    ok = (pg.is_valid and pg.area > 0 and BOX[0] < lo < BOX[2] and BOX[1] < la < BOX[3] and r['kind'] in KINDS
          and r['precision'] in ('precise', 'coarse') and r['ring_type'] == 'lonlat' and float(r['year_start']) <= float(r['year_end'])
          and BORO.get(r['zone_id'][:3]) == r['borough'] and r['source_url'].startswith('http') and len(r['note']) > 30
          and len(r['ring'].split(';')) >= 4)
    if not ok:
        bad += 1; print('BAD', r['zone_id'])
    share = pg.intersection(cty[r['borough']]).area / pg.area
    if share < 0.5:
        print(f"  note: {r['zone_id']} lies only {100 * share:.0f} % inside {r['borough']} County")
    geo[r['zone_id']] = pg
print(f'{len(rd)} rows written to {OUT}; {bad} failed the basic checks; file {os.path.getsize(OUT) / 1e3:.0f} kB')
by = collections.Counter((r['borough'], r['kind']) for r in rd)
for b in COUNTIES:
    print(f'  {b:12s}', {k: by[(b, k)] for k in sorted(KINDS) if by[(b, k)]}, 'total', sum(v for (bb, _), v in by.items() if bb == b))
print('  precision', dict(collections.Counter(r['precision'] for r in rd)))
print('  total area (ha) by kind', {k: round(sum(geo[r['zone_id']].area for r in rd if r['kind'] == k) / 1e4) for k in sorted(KINDS)})

# ---- overlaps among the counties' rings, and with the city's rings
K = {r['zone_id']: (r['kind'], r['precision'], r['year_start'], r['year_end']) for r in rd}
ov = [(geo[a].intersection(geo[b]).area / 1e4, a, b) for a, b in itertools.combinations(ids, 2) if geo[a].intersects(geo[b])]
ov = [o for o in ov if o[0] > 0.25]
print(f'  overlaps over 0.25 ha among these rings: {len(ov)}')
for ar, a, b in sorted(ov, reverse=True):
    print(f'    {ar:7.1f} ha  {a} [{K[a][0]} {K[a][2]}-{K[a][3]}]  x  {b} [{K[b][0]} {K[b][2]}-{K[b][3]}]')
city = list(csv.DictReader(open(os.path.join(ROOT, 'data', 'manual', 'fill_zones.csv'), encoding='utf-8')))
n = 0
for c in city:
    g = parse_ring(c['ring'])
    for z in ids:
        if geo[z].intersects(g) and geo[z].intersection(g).area > 2500:
            n += 1; print(f"    overlap with the city's {c['zone_id']}: {z} {geo[z].intersection(g).area / 1e4:.1f} ha")
print(f"  overlaps over 0.25 ha with the city's fill_zones.csv: {n}")
