"""Nassau, Westchester and Rockland counties: the dredge-filled barrier beaches, the Hudson River
Railroad's shore, Croton Point, Playland, Glen Island, Piermont pier and the reservoirs."""
from zonelib import *
from shapely import wkb
R = Registry(); WIKI = 'https://en.wikipedia.org/wiki/'

# ---------------------------------------------------------------- Nassau
def barrier(zid, title, town, y0, y1, note, url):
    m = muni(town); g = biggest(m.intersection(land_at(m, 200)))
    R.add(zid, title, y0, y1, g, 'fill', 'coarse', note + f' Ring = the municipal outline of {town} on today\'s land; the natural beach ridge is inside.', url, tol=6, close=30)

run_zone(lambda: barrier('nas_long_beach', 'Long Beach: the barrier island raised and bulkheaded for the resort', 'Long Beach', 1907, 1913,
    'William H. Reynolds "acquired the oceanfront from private owners and the rest of the island from the Town of Hempstead in 1907; he planned to build a boardwalk, '
    'homes, and hotels"; "dredges created a channel 1000 ft wide on the north side of the island" (Reynolds Channel); "the community became an incorporated village in '
    '1913". Start documented; end year estimated (the incorporation stands for the end of the dredging; the article does not say where the dredged sand went).',
    WIKI + 'Long_Beach,_New_York'))
run_zone(lambda: barrier('nas_atlantic_beach', 'Atlantic Beach', 'Atlantic Beach', 1923, 1927,
    '"In 1923, the village\'s first developer, Atlantic Beach Associates", began; in 1926 Austin and Talbot "completed Pettit\'s preliminary dredging and shoring work, '
    'and proceeded to subdivide the property"; the bridge "was opened and dedicated on June 29, 1927". Both years documented.', WIKI + 'Atlantic_Beach,_New_York'))
run_zone(lambda: barrier('nas_island_park', 'Island Park (Barnum Island)', 'Island Park', 1909, 1925,
    'The island was sold to developers in 1909 and 1911: "minimal development at that time included construction of several canals, before work was abandoned. New '
    'developers bought the island in 1921, and started building ... starting in 1922." Start documented; end year estimated.', WIKI + 'Barnum_Island,_New_York'))

def jones_beach():
    p = named('Jones Beach State Park'); g = biggest(p.intersection(land_at(p, 200)))
    R.add('nas_jones_beach', 'Jones Beach State Park: the island raised with dredged sand', 1926, 1929.59, g, 'fill', 'coarse',
          '"When Moses\' group first surveyed Jones Island in the 1920s, it was swampy and only 2 ft above sea level"; "huge dredgers brought sand from the bay bottom, '
          'eventually raising the island to 12 ft above sea level"; "in the summer of 1928, thousands of men worked on the beach planting the grass by hand"; "the park '
          'opened to the public on August 4, 1929, along with the causeway". End documented; start year estimated. Ring = the park outline on today\'s land.',
          WIKI + 'Jones_Beach_State_Park', tol=10, close=40)
run_zone(jones_beach)
run_zone(lambda: add_reservoir(R, 'nas_hempstead_lake', 'Hempstead Lake (the Brooklyn water works\' storage reservoir)', 'Hempstead Lake', 1873,
    'The lake was "first proposed in 1870 to supply water to Brooklyn"; "the Mill River ... was dammed to form the 167-acre reservoir"; in 1947 a dam for the Southern '
    'State Parkway cut off its northern third. Start year estimated: the article gives no completion year (1873 is the usual one and was not verified).',
    WIKI + 'Hempstead_Lake_State_Park', tol=5))

# ---------------------------------------------------------------- Westchester
def railroad():
    c = con(); WES = muni('Westchester County', 'county'); cp = named('Croton Point Park'); YON = muni('Yonkers')
    y_lo, y_hi = YON.bounds[1], cp.bounds[3]
    box = bbox_ll(Polygon([(cp.bounds[0] - 9000, y_lo), (cp.bounds[2] + 4000, y_lo), (cp.bounds[2] + 4000, y_hi), (cp.bounds[0] - 9000, y_hi)]), 300)
    segs = [to_utm(wkb.loads(bytes(g))) for g, in c.execute(f"select ST_AsWKB(geometry) from '{OV}/rail.parquet' where name = 'Hudson Line' and ST_XMax(geometry) >= {box[0]} "
            f"and ST_XMin(geometry) <= {box[2]} and ST_YMax(geometry) >= {box[1]} and ST_YMin(geometry) <= {box[3]}").fetchall()]
    track = unary_union(segs).intersection(WES)
    pts = [l.interpolate(d) for l in getattr(track, 'geoms', [track]) for d in np.arange(0, l.length, 25)]
    pts = [p for p in pts if y_lo <= p.y <= y_hi]
    bins = {}
    for p in pts:
        bins.setdefault(int(p.y // 120), []).append(p.x)
    # westernmost track in each 120 m of northing (the river-side track; yards and branches lie east of it)
    centre = [(float(np.percentile(xs, 10)), k * 120 + 60.0) for k, xs in sorted(bins.items())]
    centre = [p for p in LineString(centre).simplify(20).coords]
    land = land_of(box)
    g = side_of(centre, 'W', 4000).intersection(land).intersection(WES).union(LineString(centre).buffer(45).intersection(land))
    g = part_at(g, centre[len(centre) // 2])
    print('   Hudson Line: %d track points, centre line %.1f km from %.4f to %.4f N' % (len(pts), LineString(centre).length / 1e3, ll(centre[0])[1], ll(centre[-1])[1]))
    return g, cp
def westchester_shore():
    g, cp = railroad()
    R.add('wes_croton_point_landfill', 'Croton Point: the county landfill on the marsh of the neck', 1927, 1986, cp, 'fill', 'coarse',
          '"A substantial portion of the land on which the park is situated today was the site of a landfill, which was operated by the Westchester County government '
          'from 1927 to 1986. A 1931 map shows the landfill area as marsh." Both years documented. Ring = the whole park outline; the point itself is natural.',
          WIKI + 'Croton_Point_Park', tol=6)
    def gm():
        e = any_named('Edge-on-Hudson').buffer(30)
        R.add('wes_sleepy_hollow_gm', 'Sleepy Hollow: the General Motors plant site', 1900, 1960, e, 'fill', 'coarse',
              '"The 90 acre plant was in operation, with short interruptions, from 1900 to 1996" on the former Kingsland estate\'s waterfront. No source at hand dates '
              'the filling of the river for the plant: estimated bracket (start = the first factory). Ring = the Overture outline of the redevelopment site + 30 m.',
              WIKI + 'North_Tarrytown_Assembly', tol=4)
    run_zone(gm)
    R.add('wes_hudson_river_railroad', 'Hudson River Railroad: the causeways, the coves cut off and the made land west of the tracks (Yonkers to Croton)', 1847, 1849.75,
          g, 'fill', 'coarse',
          'The company was "not fully organized until March 4, 1847"; "service began on the first 41 mi of the line from Chambers Street ... to Peekskill on September '
          '29, 1849". The line runs on fill along and across the river\'s coves. Both dates documented for the railroad; later fill west of the tracks (Yonkers, '
          'Hastings, Dobbs Ferry, Irvington, Tarrytown, Ossining) is inside the ring and not dated. Ring = today\'s land west of the westernmost track of the Hudson '
          'Line (Overture rail, sampled every 120 m of northing) and 45 m east of it, from the Yonkers line to Croton Point; natural points are inside.',
          WIKI + 'Hudson_Line_(Metro-North)', tol=6, minus=['wes_croton_point_landfill'] + (['wes_sleepy_hollow_gm'] if 'wes_sleepy_hollow_gm' in R.geom else []), close=20)
run_zone(westchester_shore)

def playland():
    pk = any_named('Rye Playland'); lk = unary_union(water_parts('Playland Lake'))
    h = unary_union([pk, lk]).convex_hull.buffer(120)
    g = biggest(h.intersection(land_at(h, 100)))
    R.add('wes_playland', 'Playland, Rye', 1927.7, 1928.4, g, 'fill', 'coarse',
          '"Construction commenced in September 1927, and was completed in six months"; "built in 1928, the 280 acre park". The park was laid out on the shore and '
          'marsh of Manursing; how much of it is made land is not stated (estimated outline). Ring = the hull of the amusement park and Playland Lake + 120 m, on today\'s land.',
          WIKI + 'Playland_(New_York)', tol=5)
run_zone(playland)
def glen_island():
    g = named('Glen Island', table='base_land')
    R.add('wes_glen_island', 'Glen Island, New Rochelle: five islands joined', 1879, 1925, g, 'fill', 'coarse',
          '"Although now one island, the site originally consisted of one large main island in close proximity to at least four smaller nearby islands, a number of '
          'rocky outcroppings, low-lying flats, and salt marshes"; John H. Starin made it a resort from 1879. Start = Starin; end year estimated (Westchester County '
          'made it a park in the 1920s). Ring = the island outline.', WIKI + 'Glen_Island_Park', tol=4)
run_zone(glen_island)

for zid, nm, y0, note, page in [
    ('wes_new_croton_reservoir', 'New Croton Reservoir', 1906, '"Construction on a New Croton Dam began in 1892"; "in 1906, the New Croton Dam was completed, expanding the existing '
     'impoundment into the New Croton Reservoir". Croton Lake, behind the Old Croton Dam of 1842 ("built ... between 1837 and 1842"; "submerged to a depth of 34 ft" in 1906), '
     'filled the upper part of this outline from 1842: its outline is not on disk and is not drawn.', 'New_Croton_Reservoir'),
    ('wes_kensico_reservoir', 'Kensico Reservoir / Rye Lake', 1917, '"In 1885, the old Kensico Dam was built"; "the construction of the new dam began in 1913 and was concluded in 1917". '
     'Start = the new dam, which made today\'s outline; the smaller reservoir of 1885 behind the old dam is not drawn.', 'Kensico_Reservoir'),
    ('wes_titicus_reservoir', 'Titicus Reservoir', 1893, '"It has been supplying the system since 1893."', 'Titicus_Reservoir'),
    ('wes_muscoot_reservoir', 'Muscoot Reservoir', 1905, '"The reservoir was constructed at the beginning of the 20th century, and was completed in 1905."', 'Muscoot_Reservoir'),
    ('wes_amawalk_reservoir', 'Amawalk Reservoir', 1897, '"Formed by impounding the middle of the Muscoot River ... and put into service in 1897."', 'Amawalk_Reservoir'),
    ('wes_cross_river_reservoir', 'Cross River Reservoir', 1908, '"The reservoir was finally put into service in 1908."', 'Cross_River_Reservoir'),
    ('wes_grassy_sprain_reservoir', 'Grassy Sprain Reservoir', 1876, '"It was completed in 1876 by the City of Yonkers as the city\'s main storage reservoir."', 'Grassy_Sprain_Reservoir'),
    ('wes_hillview_reservoir', 'Hillview Reservoir', 1915, '"It was built within a six-year period from 1909-1915 by the New York City Board of Water Supply to receive water from '
     'the newly constructed Catskill Aqueduct." A basin on a hilltop, not a flooded valley.', 'Hillview_Reservoir'),
    ('wes_tarrytown_reservoir', 'Tarrytown Reservoir', 1897, '"The reservoir was completed in 1897 by the village of Tarrytown"; decommissioned in 1993, it still holds water.', 'Tarrytown_Reservoir'),
    ('roc_lake_deforest', 'Lake DeForest', 1956, '"A reservoir in Clarkstown, New York, created in 1956 by impounding the Hackensack River"; dedicated 13 March 1957.', 'Lake_DeForest'),
    ('roc_lake_sebago', 'Lake Sebago (Harriman State Park)', 1925, '"The lake was created in 1925 by the Palisades Interstate Park Commission."', 'Lake_Sebago'),
    ('roc_lake_welch', 'Lake Welch (Harriman State Park)', 1942, '"By 1942, the lake was completed using workers from the Civilian Conservation Corps"; it drowned the hamlet of Sandyfield.', 'Sandyfield,_New_York')]:
    run_zone(lambda zid=zid, nm=nm, y0=y0, note=note, page=page: add_reservoir(R, zid, nm, nm.split(' (')[0], y0, note, WIKI + page, tol=10 if 'Croton' in nm or 'Kensico' in nm else 6))

# ---------------------------------------------------------------- Rockland
def piermont():
    m = muni('Piermont'); T = Streets(bbox_ll(m, 200)); land = T.land()
    a, b = end_of(T, 'Piermont Avenue', 'S'), end_of(T, 'Piermont Avenue', 'N')
    line = T.along('Piermont Avenue', a, b, bridge=300)
    east = side_of(line, 'E', 3000).intersection(land).intersection(m)
    g = max(getattr(east, 'geoms', [east]), key=lambda q: q.area)
    print('   Piermont Avenue %.0f m; land east of it in the village: %.1f ha, largest part %.1f ha' % (LineString(line).length, east.area / 1e4, g.area / 1e4))
    R.add('roc_piermont_pier', 'Piermont: the Erie Railroad pier', 1838, 1839, g, 'fill', 'coarse',
          '"The railroad built a long pier into the river near the creek in 1839 as its principal terminal." End documented; start year estimated (a year of work). '
          'Ring = the largest piece of the village\'s land east of Piermont Avenue: the mile-long pier with the made ground at its root.', WIKI + 'Piermont,_New_York', tol=4, close=20)
run_zone(piermont)
R.save('ny')
