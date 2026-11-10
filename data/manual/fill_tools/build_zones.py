"""Merge the per-area rows (written by zones_*.py) into data/manual/fill_zones.csv and check it.

  .venv/bin/python data/manual/fill_tools/zones_mn_a.py      # ... one script per area, each saves
  .venv/bin/python data/manual/fill_tools/build_zones.py     # rows_<area>.json in data/interim/fill
"""
import collections, csv, itertools, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from zonelib import COLS, INTERIM, KINDS, ROOT, parse_ring, write_csv, ll

ORDER = ['mn_a', 'mn_b', 'misc', 'hb', 'bk', 'qn', 'bx_si']
BORO_ORDER = ['Manhattan', 'Harbour islands', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island']
OUT = os.path.join(ROOT, 'data', 'manual', 'fill_zones.csv')

rows = []
for tag in ORDER:
    rows += json.load(open(os.path.join(INTERIM, f'rows_{tag}.json')))
rows.sort(key=lambda r: BORO_ORDER.index(r['borough']))          # stable: keeps the order inside a borough
for r in rows:
    for k in ('year_start', 'year_end'):
        v = float(r[k]); r[k] = int(v) if v == int(v) else round(v, 2)
write_csv(OUT, rows)

# ---- checks on the file as written
rd = list(csv.DictReader(open(OUT, encoding='utf-8')))
assert [c for c in rd[0].keys()] == COLS
ids = [r['zone_id'] for r in rd]
assert len(ids) == len(set(ids)), 'duplicate zone_id'
geo = {}
bad = 0
for r in rd:
    pg = parse_ring(r['ring'])
    lo, la = ll((pg.centroid.x, pg.centroid.y))
    ok = (pg.is_valid and pg.area > 0 and -74.29 < lo < -73.67 and 40.47 < la < 40.94 and r['kind'] in KINDS
          and r['precision'] in ('precise', 'coarse') and r['ring_type'] == 'lonlat' and float(r['year_start']) <= float(r['year_end'])
          and r['zone_id'][:3] in ('mn_', 'bk_', 'qn_', 'bx_', 'si_', 'hb_') and r['source_url'].startswith('http') and len(r['note']) > 30)
    if not ok:
        bad += 1; print('BAD', r['zone_id'])
    geo[r['zone_id']] = pg
print(f'{len(rd)} rows written to {OUT}; {bad} failed the basic checks')

by = collections.Counter((r['borough'], r['kind']) for r in rd)
for b in BORO_ORDER:
    print(f'  {b:16s}', {k: by[(b, k)] for k in sorted(KINDS) if by[(b, k)]}, 'total', sum(v for (bb, _), v in by.items() if bb == b))
print('  precision', dict(collections.Counter(r['precision'] for r in rd)))
est = [r for r in rd if 'stimated' in r['note']]
print(f'  notes that say "estimated": {len(est)}; without: {len(rd) - len(est)}')
print('  total area (ha) by kind', {k: round(sum(geo[r['zone_id']].area for r in rd if r['kind'] == k) / 1e4) for k in sorted(KINDS)})

# ---- band order: going outward the land must not get older
Y = {r['zone_id']: (float(r['year_start']), float(r['year_end'])) for r in rd}
for seq in (['mn_er_1_pearl_water', 'mn_er_2_water_front', 'mn_er_3_front_south'],
            ['mn_er_4_cherry_water', 'mn_er_5_water_south_two_bridges'],
            ['mn_er_corlears_14th', 'mn_east_river_park'],
            ['mn_er_stuyvesant_cove', 'mn_fdr_14_23'], ['mn_er_23_34', 'mn_bristol_basin'],
            ['mn_hr_1_greenwich_washington', 'mn_hr_2_washington_west', 'mn_hr_3_west_bulkhead', 'mn_battery_park_city'],
            ['mn_hr_1n_greenwich_washington', 'mn_hr_2_washington_west'],
            ['mn_battery_early', 'mn_battery_1855']):
    ok = all(Y[a][1] <= Y[b][1] and Y[a][0] <= Y[b][0] for a, b in zip(seq, seq[1:]))
    print('  band order', 'ok ' if ok else 'BAD', ' < '.join(f'{z.split("_", 1)[1]} {Y[z][0]:g}-{Y[z][1]:g}' for z in seq))

# ---- overlaps
K = {r['zone_id']: (r['kind'], r['precision']) for r in rd}
ov = []
for a, b in itertools.combinations(ids, 2):
    if geo[a].intersects(geo[b]):
        ar = geo[a].intersection(geo[b]).area / 1e4
        if ar > 0.25:
            ov.append((ar, a, b))
print(f'  overlaps over 0.25 ha: {len(ov)}')
for ar, a, b in sorted(ov, reverse=True):
    tag = 'precise-precise' if K[a][1] == K[b][1] == 'precise' else ''
    print(f'    {ar:7.1f} ha  {a} [{K[a][0]} {Y[a][0]:g}-{Y[a][1]:g}]  x  {b} [{K[b][0]} {Y[b][0]:g}-{Y[b][1]:g}]  {tag}')
