"""Parses the four county tables and checks columns, years and coordinates (run after any rebuild)."""
import csv, collections, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
T = '/home/user/nyc/data/tables/'
def load(n):
    rows = list(csv.reader(open(T + n, encoding='utf-8', newline='')))
    assert len({len(r) for r in rows}) == 1, (n, collections.Counter(len(r) for r in rows))
    return rows[0], [dict(zip(rows[0], r)) for r in rows[1:]]
box = lambda la, lo: 40.47 <= float(la) <= 41.38 and -74.52 <= float(lo) <= -73.40
A = ('hudson', 'bergen', 'essex', 'union', 'passaic', 'westchester', 'nassau', 'rockland')
C = ('', 'Hudson', 'Bergen', 'Essex', 'Union', 'Passaic', 'Westchester', 'Nassau', 'Rockland')
h, pop = load('population_counties.csv'); assert h == ['year', 'area', 'population', 'source_url', 'note']
dec = [str(y) for y in range(1790, 2021, 10)]
for r in pop: assert 1600 <= float(r['year']) <= 2026 and int(r['population']) > 0 and r['source_url'].startswith('http') and r['area'] in A and r['note'], r
for a in A:
    ys = [r['year'] for r in pop if r['area'] == a]; assert len(ys) == len(set(ys)) and all(y in ys for y in dec) and '2025.5' in ys, a
print('population', len(pop), dict(collections.Counter(r['area'] for r in pop)), '| rows with "estimate":', sum('estimate' in r['note'].lower() for r in pop),
      '| per area:', {a: sum('estimate' in r['note'].lower() for r in pop if r['area'] == a) for a in A})
h, pl = load('places_counties.csv'); assert h == ['id', 'name', 'tier', 'lat', 'lon', 'year_start', 'year_end', 'replaced_by', 'county', 'note', 'source_url']
ids = {r['id'] for r in pl}; assert len(ids) == len(pl)
cid = {r['id'] for r in csv.DictReader(open(T + 'places.csv', encoding='utf-8'))}; assert not (ids & cid)
for r in pl:
    assert box(r['lat'], r['lon']) and 1609 <= int(r['year_start']) < int(r['year_end']) <= 9999 and r['tier'] in ('region', 'city', 'town', 'neighborhood', 'historic', 'landscape'), r
    assert (not r['replaced_by'] or r['replaced_by'] in ids) and r['source_url'].startswith('http') and r['note'] and r['county'] in C, r
    assert re.fullmatch(r'-?\d+\.\d{5}', r['lat']) and re.fullmatch(r'-?\d+\.\d{5}', r['lon']) and '\t' not in ''.join(r.values()), r
    assert r['id'].split('_')[0] in ('hud', 'ber', 'ess', 'uni', 'pas', 'wes', 'nas', 'roc', 'reg'), r['id']
byid = {r['id']: r for r in pl}
gaps = [(r['id'], r['year_end'], r['replaced_by'], byid[r['replaced_by']]['year_start']) for r in pl if r['replaced_by'] and byid[r['replaced_by']]['year_start'] != r['year_end']]
src = json.load(open(os.path.join(HERE, 'places_counties_coordsrc.json')))
print('places', len(pl), dict(collections.Counter(r['tier'] for r in pl)), dict(collections.Counter(r['county'] or 'shared' for r in pl)))
print('  estimated:', sum('estimated' in r['note'] for r in pl), '| nominal:', sum('nominal' in r['note'] for r in pl), '| approximate:', sum('approximate' in r['note'] for r in pl),
      '| none of the three:', sum(not re.search('estimated|nominal|approximate', r['note']) for r in pl), '| incorporation-year rows:', sum('year read from the cited article' in r['note'] for r in pl),
      '| "not found in the cited article":', sum('not found in the cited article' in r['note'] for r in pl))
print('  chains:', sum(1 for r in pl if r['replaced_by']), '| current:', sum(r['year_end'] == '9999' for r in pl), '| start 1609:', sum(r['year_start'] == '1609' for r in pl), '| chain gaps:', gaps)
print('  coordinates:', dict(collections.Counter(s.split(':')[0] for s in src.values())))
h, ev = load('events_counties.csv'); assert h == ['year', 'month', 'day', 'title', 'description', 'lat', 'lon', 'zoom', 'source_url']
ct = {r['title'] for r in csv.DictReader(open(T + 'events.csv', encoding='utf-8'))}
for r in ev:
    assert 1609 <= int(r['year']) <= 2026 and box(r['lat'], r['lon']) and 9 <= int(r['zoom']) <= 18 and r['source_url'].startswith('http') and r['title'] and r['description'] and r['title'] not in ct, r
    assert (r['month'] == '' or 1 <= int(r['month']) <= 12) and (r['day'] == '' or (1 <= int(r['day']) <= 31 and r['month'])), r
assert len({r['title'] for r in ev}) == len(ev)
print('events', len(ev), '| full date', sum(1 for r in ev if r['day']), '| month', sum(1 for r in ev if r['month'] and not r['day']), '| year only', sum(1 for r in ev if not r['month']))
h, pk = load('parks_counties.csv'); assert h == ['name', 'start_year', 'end_year', 'start_event', 'planting_note', 'source_url', 'confidence']
cp = {r['name'] for r in csv.DictReader(open(T + 'parks.csv', encoding='utf-8'))}
for r in pk: assert 1609 <= int(r['start_year']) < int(r['end_year']) <= 9999 and r['confidence'] in ('exact', 'estimated') and r['source_url'].startswith('http') and r['start_event'], r
assert len({r['name'] for r in pk}) == len(pk)
print('parks', len(pk), dict(collections.Counter(r['confidence'] for r in pk)), '| names also in the city parks.csv:', sorted({r['name'] for r in pk} & cp))
