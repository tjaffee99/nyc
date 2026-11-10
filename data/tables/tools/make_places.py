"""Builds data/tables/places.csv from places_a/b/c.txt (hand-written rows) + Wikipedia article coordinates."""
import csv, json, os, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wp
BORO = {'M': 'Manhattan', 'B': 'Brooklyn', 'Q': 'Queens', 'X': 'The Bronx', 'S': 'Staten Island', '': ''}
CACHE = '/home/user/nyc/data/raw/tables/wp_coords.json'
OUT = '/home/user/nyc/data/tables/places.csv'
rows = []
for fn in ('places_a.txt', 'places_b.txt', 'places_c.txt', 'places_d.txt'):
    if not os.path.exists(fn): continue
    for ln in open(fn, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln.strip() or ln.startswith('#'): continue
        p = [x.strip().strip('​').strip() for x in ln.split('|')]
        assert len(p) == 10, (fn, len(p), ln[:80])
        rows.append(dict(zip(['id', 'name', 'tier', 'coord', 'y0', 'y1', 'repl', 'boro', 'title', 'note'], p)))
OVERRIDE = {}
if os.path.exists('places_fix.json'): OVERRIDE = json.load(open('places_fix.json'))
for r in rows:
    for k, v in OVERRIDE.get(r['id'], {}).items(): r[k] = v
rows = [r for r in rows if not OVERRIDE.get(r['id'], {}).get('drop')]
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
titles = sorted({r['title'].replace('_', ' ') for r in rows if not r['title'].startswith('http')})
need = [t for t in titles if t not in cache]
if need:
    got = wp.coords(need)
    for t in need: cache[t] = got.get(t, None)
    json.dump(cache, open(CACHE, 'w'), indent=0)
missing = [t for t in titles if cache.get(t) == 'MISSING']
print('titles', len(titles), 'missing:', missing)
# NOMINAL1664: Dutch -> English name switches are dated to the takeover unless a source dates them
_by = {r['id']: r for r in rows}
for r in rows:
    if r['y1'] == '1664' and r['repl'] and _by[r['repl']]['y0'] == '1664' and r['id'] not in ('mn_new_amsterdam', 'mn_fort_amsterdam'):
        for x in (r, _by[r['repl']]):
            if 'nominal' not in x['note']: x['note'] = x['note'].rstrip() + ' Name switch dated to the English takeover of 1664 (nominal).'
ids = {r['id'] for r in rows}
assert len(ids) == len(rows), [i for i in ids if sum(1 for r in rows if r['id'] == i) > 1]
out = []; nocoord = []
for r in rows:
    t = r['title'].replace('_', ' ')
    if r['coord']:
        lat, lon = map(float, r['coord'].split(','))
        src = 'hand'
    else:
        c = cache.get(t)
        if not c or c == 'MISSING': nocoord.append((r['id'], t)); continue
        lat, lon = c; src = 'wp'
    assert r['tier'] in ('region', 'city', 'town', 'neighborhood', 'historic', 'landscape'), r
    y0, y1 = int(r['y0']), int(r['y1'])
    assert 1609 <= y0 < y1 <= 9999, r
    if r['repl']: assert r['repl'] in ids, ('bad replaced_by', r['id'], r['repl'])
    if not (40.47 <= lat <= 40.94 and -74.29 <= lon <= -73.67): print('OUT OF BOX', r['id'], lat, lon)
    url = r['title'] if r['title'].startswith('http') else 'https://en.wikipedia.org/wiki/' + urllib.parse.quote(r['title'].replace(' ', '_'), safe="_,()'-.–:")
    out.append([r['id'], r['name'], r['tier'], f'{lat:.5f}', f'{lon:.5f}', y0, y1, r['repl'], BORO[r['boro']], r['note'], url, src])
print('rows', len(rows), 'written', len(out), 'no coords:', nocoord)
# chain check: replaced_by start should equal this end (report otherwise)
byid = {o[0]: o for o in out}
for o in out:
    if o[7] and o[7] in byid and byid[o[7]][5] != o[6]: print('chain gap', o[0], o[6], '->', o[7], byid[o[7]][5])
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['id', 'name', 'tier', 'lat', 'lon', 'year_start', 'year_end', 'replaced_by', 'county', 'note', 'source_url'])
    for o in out: w.writerow(o[:11])
json.dump({o[0]: o[11] for o in out}, open('places_coordsrc.json', 'w'))
import collections
print(collections.Counter(o[2] for o in out), collections.Counter(o[8] for o in out), 'estimated notes:', sum('estimated' in o[9] for o in out), 'hand coords:', sum(o[11] == 'hand' for o in out))
