"""Sanity checks of fill_zones_counties.csv against things whose place is known: named footprints must fall
in the ring they stand on, reservoir rings must be water today, fill rings land, areas must match the sources."""
import csv, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from zonelib import *

rd = list(csv.DictReader(open(os.path.join(ROOT, 'data', 'manual', 'fill_zones_counties.csv'), encoding='utf-8')))
geo = {r['zone_id']: parse_ring(r['ring']) for r in rd}
tests = [('%Central Railroad of New Jersey Terminal%', 'hud_communipaw_cnj'), ('%Liberty Science Center%', 'hud_communipaw_cnj'), ('Hoboken Terminal%', 'hud_hoboken_terminal'),
         ('%Colgate Clock%', 'hud_paulus_hook'), ('%30 Hudson%', 'hud_paulus_hook'), ('%Newport Centre%', 'hud_pavonia_long_dock'), ('%Harborside%', None),
         ('%Hudson and Manhattan Railroad Powerhouse%', None), ('%Stevens%Howe%', 'hud_hoboken_meadows'), ('%Hoboken City Hall%', 'hud_hoboken_meadows'),
         ('%Cape Liberty%', 'hud_military_ocean_terminal'), ('%MetLife Stadium%', 'ber_meadowlands_sports_complex'), ('%Meadowlands Arena%', 'ber_meadowlands_sports_complex'),
         ('%Terminal C%', 'ess_newark_airport'), ('%Jones Beach%Theater%', 'nas_jones_beach'), ('%Jones Beach%Bathhouse%', 'nas_jones_beach'),
         ('%Long Beach City Hall%', 'nas_long_beach'), ('%Playland%', 'wes_playland'), ('%Lincoln Harbor%', 'hud_weehawken_waterfront'), ('%Bayonne Golf Club%', 'hud_constable_hook')]
box = (-74.52, 40.47, -73.40, 41.38)
for pat, want in tests:
    hits = bldg(pat, box)
    if not hits:
        print(f'  ?? no footprint named {pat}'); continue
    hits.sort(key=lambda h: min(g.distance(Point(h[1])) for g in geo.values()))
    name, p = hits[0]
    inz = [z for z, g in geo.items() if g.contains(Point(p))]
    print(f"  {'ok ' if (want is None or want in inz) else 'XX '}{name[:44]:44s} in {inz}" + (f'   (expected {want})' if want and want not in inz else ''))
print('share of each ring that is water today (reservoirs: high; fill: low):')
for r in rd:
    g = geo[r['zone_id']]
    if g.area > 3e7:
        continue
    land = land_at(g, 100)
    wet = 1 - g.intersection(land).area / g.area
    flag = '' if (r['kind'] == 'reservoir') == (wet > 0.8) else ('   <-- look' if r['kind'] == 'reservoir' or wet > 0.25 else '')
    print(f"  {r['zone_id']:34s} {r['kind']:9s} {r['precision']:7s} {g.area / 1e4:8.1f} ha  water {100 * wet:5.1f} %{flag}")
