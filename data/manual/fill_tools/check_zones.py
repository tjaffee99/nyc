"""Sanity checks of fill_zones.csv against things whose place in the story is known:
named building footprints must fall in the zone they are documented to stand on, precise rings
must lie on today's land, and a park ring must match the park outline."""
import csv, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from zonelib import *
import duckdb
from shapely import wkb
from shapely.geometry import shape

rd = list(csv.DictReader(open(os.path.join(ROOT, 'data', 'manual', 'fill_zones.csv'), encoding='utf-8')))
geo = {r['zone_id']: parse_ring(r['ring']) for r in rd}
fp = os.path.join(ROOT, 'data', 'interim', 'nyc_footprints_raw.parquet')
tests = [('Fraunces Tavern%', 'mn_er_1_pearl_water'), ('%Schermerhorn Row%', 'mn_er_3_front_south'), ('Castle Clinton', 'mn_castle_clinton_island'),
         ('One World Trade Center', 'mn_hr_2_washington_west'), ('%Stuyvesant High School%', 'mn_battery_park_city'),
         ('%Brookfield Place%', 'mn_battery_park_city'), ('Pier A%', 'mn_battery_1855'),
         ('%India House%', 'mn_er_1_pearl_water'), ('%Battery Maritime%', None), ('%Whitehall Terminal%', None), ('%Tombs%', 'mn_collect_pond'),
         ('%Criminal Court%', 'mn_collect_pond'), ('%Liggett Hall%', 'hb_governors_island_fill'), ('%Castle Williams%', 'hb_governors_island_fill'),
         ('%Stuyvesant Town%', None), ('%United Nations Secretariat%', 'mn_er_42_49_turtle_bay'), ('%Javits%', 'mn_hr_23_59'),
         ('%Chelsea Piers%', None), ('%Waterside Plaza%', None), ('%Gracie Mansion%', None), ('%Ellis Island%Main%', 'hb_ellis_island_north'),
         ('%Marine Air Terminal%', 'qn_laguardia_airport'), ('%Unisphere%', None), ('%Brooklyn Army Terminal%', 'bk_sunset_park_waterfront')]
db = duckdb.connect()
for pat, want in tests:
    rows = db.execute(f"select name, lon, lat from '{fp}' where name ilike ? limit 3", [pat]).fetchall()
    if not rows:
        print(f'  ?? no footprint named {pat}'); continue
    for name, lo, la in rows[:1]:
        p = Point(utm(lo, la))
        inz = [z for z, g in geo.items() if g.contains(p)]
        flag = 'ok ' if (want is None or want in inz) else 'XX '
        print(f'  {flag}{name[:38]:38s} in {inz}' + (f'   (expected {want})' if want and want not in inz else ''))
S = mn(); isl = S.island
print('precise rings: share lying on today\'s Manhattan land')
for r in rd:
    if r['precision'] == 'precise' and r['zone_id'].startswith('mn_') and r['kind'] in ('fill', 'excavation'):
        g = geo[r['zone_id']]
        print(f"  {r['zone_id']:34s} {100 * g.intersection(isl).area / g.area:5.1f} %  of {g.area / 1e4:6.2f} ha")
parks = json.load(open(os.path.join(ROOT, 'data', 'raw', 'nyc', 'parks_properties.geojson')))
for sign, z in (('John V. Lindsay East River Park', 'mn_east_river_park'), ('The Battery', 'mn_battery_1855'), ('Stuyvesant Cove', 'mn_fdr_14_23'),
                ('Riverside Park', 'mn_riverside_park_fill'), ('Tompkins Square Park', 'mn_stuyvesant_meadows')):
    gs = [to_utm(shape(f['geometry'])).buffer(0) for f in parks['features'] if (f['properties'].get('signname') or '') == sign]
    if gs:
        g = unary_union(gs); zz = geo[z]
        print(f'  park {sign[:34]:34s} {g.area / 1e4:6.1f} ha; {100 * g.intersection(zz).area / g.area:5.1f} % inside {z}')
    else:
        print('  ?? no park named', sign)
