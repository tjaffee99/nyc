"""Northbound (east) carriageway of West St, Battery Place to Gansevoort St -> data/interim/fill/west_st_nb.pkl,
and the measured distance from it to today's bulkhead (61-63 m from Tribeca to Gansevoort St)."""
from zonelib import *
S = mn(); isl = S.island
A = S.x('West Street', 'Battery Place'); B = S.x('West Street', 'Gansevoort Street')
east = nb_line(S, 'West Street', A, B)
pickle.dump(east, open(os.path.join(INTERIM, 'west_st_nb.pkl'), 'wb'))
for i in range(0, len(east) - 1, 6):
    e, f = east[i], east[i + 1]
    w = offset(e, f, 600)                              # 600 m to the left (west) of the walking direction
    out = LineString([e, w]).difference(isl)
    print('lat %.4f  land edge %4.0f m west of the northbound line' % (ll(e)[1], Point(e).distance(out) if not out.is_empty else -1))
