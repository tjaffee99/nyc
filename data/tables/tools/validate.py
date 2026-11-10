import csv, collections, re
T = '/home/user/nyc/data/tables/'
def load(n):
    rows = list(csv.reader(open(T + n, encoding='utf-8', newline='')))
    assert len({len(r) for r in rows}) == 1, (n, collections.Counter(len(r) for r in rows))
    return rows[0], [dict(zip(rows[0], r)) for r in rows[1:]]
box = lambda la, lo: 40.47 <= float(la) <= 40.94 and -74.29 <= float(lo) <= -73.67
h, pop = load('population.csv'); assert h == ['year', 'area', 'population', 'source_url', 'note']
for r in pop:
    assert 1600 <= float(r['year']) <= 2026 and int(r['population']) > 0 and r['source_url'].startswith('http') and r['area'] in ('nyc', 'manhattan', 'bronx', 'brooklyn', 'queens', 'staten_island'), r
dec = [str(y) for y in range(1790, 2021, 10)]
for a in ('nyc', 'manhattan', 'bronx', 'brooklyn', 'queens', 'staten_island'):
    ys = {r['year'] for r in pop if r['area'] == a}; assert all(y in ys for y in dec), (a, [y for y in dec if y not in ys])
    assert len(ys) == sum(1 for r in pop if r['area'] == a), ('dup year', a)
for y in dec + ['2025.5']:
    v = {r['area']: int(r['population']) for r in pop if r['year'] == y}
    assert v['nyc'] == sum(v[k] for k in v if k != 'nyc'), y
print('population', len(pop), collections.Counter(r['area'] for r in pop), 'estimate rows:', sum('estim' in r['note'].lower() for r in pop))
h, ev = load('events.csv'); assert h == ['year', 'month', 'day', 'title', 'description', 'lat', 'lon', 'zoom', 'source_url']
for r in ev:
    assert 1609 <= int(r['year']) <= 2026 and box(r['lat'], r['lon']) and 9 <= int(r['zoom']) <= 18 and r['source_url'].startswith('http') and r['title'] and r['description'], r
    assert (r['month'] == '' or 1 <= int(r['month']) <= 12) and (r['day'] == '' or (1 <= int(r['day']) <= 31 and r['month'])), r
assert len({r['title'] for r in ev}) == len(ev)
print('events', len(ev), 'with full date', sum(1 for r in ev if r['day']), 'year only', sum(1 for r in ev if not r['month']))
h, er = load('eras.csv'); assert h == ['start_year', 'end_year', 'title', 'subtitle', 'source_url']
assert int(er[0]['start_year']) == 1609 and int(er[-1]['end_year']) == 9999 and all(a['end_year'] == b['start_year'] for a, b in zip(er, er[1:]))
print('eras', len(er))
h, pl = load('places.csv'); assert h == ['id', 'name', 'tier', 'lat', 'lon', 'year_start', 'year_end', 'replaced_by', 'county', 'note', 'source_url']
ids = {r['id'] for r in pl}; assert len(ids) == len(pl)
for r in pl:
    assert box(r['lat'], r['lon']) and 1609 <= int(r['year_start']) < int(r['year_end']) <= 9999 and r['tier'] in ('region', 'city', 'town', 'neighborhood', 'historic', 'landscape'), r
    assert (not r['replaced_by'] or r['replaced_by'] in ids) and r['source_url'].startswith('http') and r['note'] and r['county'] in ('', 'Manhattan', 'Brooklyn', 'Queens', 'The Bronx', 'Staten Island'), r
    assert re.fullmatch(r'-?\d+\.\d{5}', r['lat']) and re.fullmatch(r'-?\d+\.\d{5}', r['lon']) and not re.search(r'[​\t]', ''.join(r.values())), r
print('places', len(pl), dict(collections.Counter(r['tier'] for r in pl)), dict(collections.Counter(r['county'] or 'city-wide' for r in pl)), 'estimated:', sum('estimated' in r['note'] for r in pl), 'nominal:', sum('nominal' in r['note'] for r in pl), 'approximate location:', sum('approximate' in r['note'] for r in pl), 'chains:', sum(1 for r in pl if r['replaced_by']), 'current:', sum(r['year_end'] == '9999' for r in pl))
h, pk = load('parks.csv'); assert h == ['name', 'start_year', 'end_year', 'start_event', 'planting_note', 'source_url', 'confidence']
for r in pk: assert 1609 <= int(r['start_year']) < int(r['end_year']) <= 9999 and r['confidence'] in ('exact', 'estimated') and r['source_url'].startswith('http') and r['start_event'], r
assert len({r['name'] for r in pk}) == len(pk)
print('parks', len(pk), dict(collections.Counter(r['confidence'] for r in pk)))
