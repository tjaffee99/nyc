"""Reservoirs outside Central Park, Castle Clinton's island, Brookfield landfill."""
from zonelib import *
from shapely import wkb
import duckdb
R = Registry(); WIKI = 'https://en.wikipedia.org/wiki/'; Z = run_zone
c = con()
fp = os.path.join(ROOT, 'data', 'interim', 'nyc_footprints_raw.parquet')


def foot(pattern):
    rows = duckdb.connect().execute(f"select name, geometry from '{fp}' where name ilike ? order by name", [pattern]).fetchall()
    print('footprints', pattern, [r[0] for r in rows][:6])
    return [to_utm(wkb.loads(bytes(r[1]))) for r in rows]


cc = unary_union(foot('%Castle Clinton%'))
Z(lambda: R.add('mn_castle_clinton_island', 'Castle Clinton (West Battery) on its artificial island', 1808, 1811, cc.convex_hull.buffer(12), 'fill', 'precise',
    'The West Battery was "erected on a small artificial offshore island" in 1808-1811, 200 ft from the shore and reached by a bridge. '
    'Ring = today\'s footprint of the fort + 12 m. It lies inside mn_battery_1855: the earlier zone wins.', WIKI + 'Castle_Clinton', tol=1))
ws = lambda n: named(n, 'base_water')
Z(lambda: R.add('bx_jerome_park_reservoir', 'Jerome Park Reservoir', 1906, 9999, ws('Jerome Park Reservoir'), 'reservoir', 'precise',
    '"Completed in 1906" on the site of the Jerome Park racetrack (closed 1889) for the New Croton Aqueduct. Outline = Overture water.',
    WIKI + 'Jerome_Park_Reservoir', tol=3))
Z(lambda: R.add('si_silver_lake_reservoir', 'Silver Lake Reservoir', 1917, 9999, ws('Silver Lake Reservoir'), 'reservoir', 'coarse',
    'A natural lake made into a reservoir of the Catskill system; Catskill water first reached it in 1917 (source read through a search '
    'summary). Before that the ring held the natural lake. Outline = Overture water.',
    'https://storymaps.arcgis.com/stories/916b995ed91040e99dab72964fa2a188', tol=3))
rw = ws('Ridgewood Reservoir')
q = c.execute(f"select ST_AsWKB(geometry) from '{OV}/base_land.parquet' where class in ('wood','wetland') and ST_X(ST_Centroid(geometry)) between -73.893 and -73.880 "
              "and ST_Y(ST_Centroid(geometry)) between 40.6875 and 40.693").fetchall()
basins = unary_union([to_utm(wkb.loads(bytes(g))) for g, in q] + [rw])
basins = unary_union([g for g in getattr(basins, 'geoms', [basins]) if g.distance(rw) < 450]).convex_hull
Z(lambda: R.add('qn_ridgewood_reservoir', 'Ridgewood Reservoir (three basins, Brooklyn / Queens line)', 1858.88, 1989, basins, 'reservoir', 'coarse',
    'Ground broken 11 July 1856, "water was initially raised on November 18, 1858"; third basin 1891; backup only from 1959; "finally '
    'decommissioned and drained in 1989" (the middle basin still holds a pond). Ring = hull of the wooded and wet basin floors and the '
    'remaining water in Overture (%.0f ha); the basin walls were not traced.' % (basins.area / 1e4), WIKI + 'Ridgewood_Reservoir'))
import json
from shapely.geometry import shape
parks = json.load(open(os.path.join(ROOT, 'data', 'raw', 'nyc', 'parks_properties.geojson')))
mp = [to_utm(shape(f['geometry'])) for f in parks['features'] if (f['properties'].get('signname') or '') == 'Mount Prospect Park']
Z(lambda: R.add('bk_mount_prospect_reservoir', 'Mount Prospect Reservoir', 1856, 1938, mp[0].buffer(-25), 'reservoir', 'coarse',
    'Brooklyn\'s reservoir on Mount Prospect, built 1856; made redundant by Water Tunnel No. 2 (1936); "demolition of the reservoir '
    'began in 1938". Ring = Mount Prospect Park (NYC Parks outline) shrunk by 25 m; the basin itself was not traced.', WIKI + 'Mount_Prospect_Park'))
hb = foot('Highbridge Recreation Center-Building') + foot('Highbridge Water Tower')
cx = (hb[0].centroid.x + hb[1].centroid.x) / 2; cy = (hb[0].centroid.y + hb[1].centroid.y) / 2
Z(lambda: R.add('mn_highbridge_reservoir', 'Highbridge Reservoir (site of the Highbridge pool)', 1872, 1934, Point(cx, cy).buffer(95), 'reservoir', 'coarse',
    'High-service reservoir of about 7 acres beside the water tower: built 1866-1872, unused for some fifteen years by 1934, when it was '
    'taken for the Highbridge Play Center pool (opened 1936). Ring = 7-acre circle centred between the recreation centre and the water '
    'tower footprints; the real basin was a rounded rectangle.', WIKI + 'Highbridge_Reservoir'))
Z(lambda: R.add('si_brookfield_landfill', 'Brookfield Avenue Landfill (Brookfield Park)', 1966, 1980, named('Brookfield Park'), 'fill', 'coarse',
    'Municipal landfill run by the Department of Sanitation "from 1966 until 1980" (NYS DEC, read through a search summary). '
    'Ring = Brookfield Park.', 'https://content.govdelivery.com/accounts/NYSDEC/bulletins/1b23eec', tol=4))
R.save('misc')
