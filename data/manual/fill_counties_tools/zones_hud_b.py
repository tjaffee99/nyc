"""Hudson County, part B: Communipaw to Constable Hook (east shore), Lincoln Park and Droyers Point,
Kearny, the dated landfills of the Meadowlands inside the county, the reservoir, and the river front
under the Palisades from Weehawken to North Bergen."""
from zonelib import *
R = Registry(); WIKI = 'https://en.wikipedia.org/wiki/'; MERI = 'https://meri.njmeadowlands.gov/mesic/sites/existingpotential-remediation-sites/'
BB = (-74.17, 40.63, -73.96, 40.87)
S, LAND = window('hud', BB)
JCm, BAYm = muni('Jersey City'), muni('Bayonne')
JC, BAY = clip_streets(S, JCm), clip_streets(S, BAYm)
TP = 'New Jersey Turnpike Newark Bay Extension'
# the rings of part A (zones_hud_a.py must run first): the rings built here keep clear of them
import json
PART_A = [r['zone_id'] for r in json.load(open(os.path.join(INTERIM, 'rows_hud_a.json')))]
for r in json.load(open(os.path.join(INTERIM, 'rows_hud_a.json'))):
    R.geom[r['zone_id']] = parse_ring(r['ring'])

# ---- the inland line of the east shore: the Turnpike extension (Grand Street to Kennedy Boulevard), then Avenue E
def xall(T, a, b):
    it = T.geom(a).intersection(T.geom(b))
    return [(g.centroid.x, g.centroid.y) for g in getattr(it, 'geoms', [it]) if not g.is_empty]
w = max(xall(JC, 'Grand Street', TP), key=lambda p: p[0])
q = max(xall(S, 'John F. Kennedy Boulevard', TP), key=lambda p: p[0])
tp = trim_path(S.along(TP, w, q, bridge=400), w, q)
aN, aS = end_of(BAY, 'Avenue E', 'N'), end_of(BAY, 'Avenue E', 'S')
ave = BAY.along('Avenue E', aN, aS, bridge=400)
inland = [p for p in LineString(tp + ave).simplify(25).coords]
inland.append((inland[-1][0], inland[-1][1] - 2500))      # from the south end of Avenue E due south to the Kill van Kull
print('Turnpike path %.0f m (%d pts) from %.5f %.5f to %.5f %.5f; Avenue E %.0f m, N %.5f %.5f S %.5f %.5f'
      % ((LineString(tp).length, len(tp)) + ll(w) + ll(q) + (LineString(ave).length,) + ll(aN) + ll(aS)))
EAST = side_of(inland, 'E', 6000).intersection(LAND)
EAST = unary_union([g for g in getattr(EAST, 'geoms', [EAST]) if g.geom_type == 'Polygon' and g.area > 2e4])
print('land east of the line: %.0f ha in %d parts' % (EAST.area / 1e4, len(getattr(EAST, 'geoms', [EAST]))))

def lsp():
    bt = near_line(JC, 'Morris Pesin Drive', 330).intersection(EAST)
    north_anchor = midpoint(JC, 'Audrey Zapp Drive')
    rest = EAST.difference(bt.buffer(1)).difference(unary_union([R.geom[k] for k in PART_A]).buffer(2))     # not the land north of the canal basin
    # the park's ground north of the Black Tom band: everything reached from Audrey Zapp Drive
    n = part_at(rest, north_anchor)
    R.add('hud_communipaw_cnj', 'Communipaw Cove: the Central Railroad of New Jersey terminal and yards (Liberty State Park, north and middle)', 1860, 1928,
          n, 'fill', 'coarse',
          'New Jersey DEP, park history: the Central Railroad of New Jersey "purchased and began filling Communipaw Cove. Between 1860 and 1928, as the need to expand '
          'their facility grew, they continued filling the cove" (read through a search-result summary on 2026-11-10: the page itself answered 404). Wikipedia: the '
          'terminal "was built in 1889, replacing an earlier one that had been in use since 1864"; "the land on which the extensive yards were built was reclaimed, or '
          'filled". Both years documented; the Lehigh Valley terminal on the south side of the Morris Canal basin (opened 1889) is inside the ring. Ring = today\'s '
          'land east of the Turnpike extension from the Morris Canal basin to 330 m north of Morris Pesin Drive.',
          'https://nj.gov/dep/parksandforests/parks/liberty_state_park/liberty_history.html', tol=4, close=30)
    R.add('hud_black_tom', 'Black Tom: the island, its causeway and the Lehigh Valley fill (Liberty State Park, south end)', 1876, 1916, part_at(bt, midpoint(JC, 'Morris Pesin Drive')),
          'fill', 'coarse',
          'Standard Oil\'s National Storage Company built on Black Tom Island in 1876; "by 1880, the island had been transformed into a 25 acre promontory, and a '
          'causeway and railroad had been built to connect it with the mainland"; "between 1905 and 1916, the Lehigh Valley Railroad ... expanded the island with '
          'landfill". Both years documented. The outline is an estimate: today\'s land within 330 m of Morris Pesin Drive, which runs along the south end of the park '
          'where the causeway and island lay.', WIKI + 'Black_Tom_explosion', tol=4, minus=['hud_communipaw_cnj'])
    return rest
REST = None
def lsp_wrap():
    global REST
    REST = lsp()
run_zone(lsp_wrap)

def spine(T, name, d, east_of=500.0):
    """Land of EAST within d metres of a spine street, counting only the street further than east_of from the inland line."""
    far = T.geom(name).difference(LineString(inland).buffer(east_of))
    return far.buffer(d).intersection(EAST)

def port_jersey_motby():
    pj = part_at(spine(S, 'Port Jersey Boulevard', 520, east_of=1100), midpoint(BAY, 'Port Jersey Boulevard'))
    R.add('hud_port_jersey', 'Port Jersey (the peninsula along Port Jersey Boulevard)', 1972, 1976, pj, 'fill', 'coarse',
          '"The pier that become Port Jersey was created in the between 1972 and 1976 using landfill." Both years documented. Ring = today\'s land within 520 m '
          'of Port Jersey Boulevard, from 1.1 km east of the line Turnpike extension - Avenue E outward.', WIKI + 'Port_Jersey', tol=4)
    pw, pe = end_of(BAY, 'Port Terminal Boulevard', 'W'), end_of(BAY, 'Port Terminal Boulevard', 'E')
    axis = LineString([extend(pe, pw, 1300), pw, pe]).buffer(420, cap_style=2)            # the boulevard's chord, carried 1.3 km west to the root
    mo = part_at(spine(BAY, 'Port Terminal Boulevard', 650, east_of=150).union(axis.intersection(EAST)), midpoint(BAY, 'Port Terminal Boulevard'))
    print('   Ocean Terminal ring before clipping: %.0f ha (EPA: a 652 acre = 264 ha man-made peninsula)' % (mo.area / 1e4))
    R.add('hud_military_ocean_terminal', 'Military Ocean Terminal at Bayonne (the man-made peninsula along Port Terminal Boulevard)', 1939, 1942, mo, 'fill', 'coarse',
          'US EPA: "Site use as a port terminal extends back to 1939 when dredged fill material was first used to create the peninsula." Wikipedia: "In 1932, a basic '
          'plan was initiated to build a port terminal"; "the Bayonne Naval Drydock base was opened by the Navy in 1942". Both years documented. Ring = today\'s land '
          'east of Avenue E within 420-650 m of Port Terminal Boulevard and of its line carried west to the root of the peninsula.',
          'https://19january2025snapshot.epa.gov/hwcorrectiveactioncleanups/hazardous-waste-cleanup-military-ocean-terminal-bayonne-new-jersey', tol=4, minus=['hud_port_jersey'])
run_zone(port_jersey_motby)

def greenville_caven():
    done = unary_union([R.geom[k] for k in R.geom]).buffer(1)
    left = EAST.difference(done)
    golf = any_named('Liberty National Golf Club')
    main = part_at(left, (golf.centroid.x, golf.centroid.y))          # the land between Black Tom and Port Jersey
    c0, c1 = end_of(JC, 'Chapel Avenue', 'W'), end_of(JC, 'Chapel Avenue', 'E')
    cutline = [c0, c1, extend(c0, c1, 4000)]                          # Chapel Avenue, carried on east into the bay
    north = half_plane(c0, c1, 'left')                              # Chapel Avenue runs east-south-east: left = north
    cav = part_at(main.intersection(north), (golf.centroid.x, golf.centroid.y))
    pw = end_of(S, 'Port Jersey Boulevard', 'W')                      # the landward end of Port Jersey Boulevard
    pj = R.geom['hud_port_jersey']
    pe = min(pj.exterior.coords, key=lambda c: math.dist(c, pw))       # where the Port Jersey ring begins
    south = half_plane(pw, pe, 'right')
    gy = main.difference(north).difference(south)
    gy = max(getattr(gy, 'geoms', [gy]), key=lambda g: g.area)
    print('   Chapel Avenue %.5f %.5f -> %.5f %.5f; north of it %.1f ha, south %.1f ha' % (ll(c0) + ll(c1) + (cav.area / 1e4, gy.area / 1e4)))
    R.add('hud_caven_point', 'Caven Point: Liberty National golf course, Port Liberte and the Caven Point terminal', 1917, 1945, cav, 'fill', 'coarse',
          'Port Liberte stands "on Caven Point, formerly one of the last natural sand beaches on the Upper New York Bay"; the park\'s Caven Point section "is a '
          '22-acre man-made piece of land"; Port Liberte was "commenced in the 1980s" on the older fill. No source at hand dates the terminals\' fill (the Army\'s '
          'Caven Point terminal of the First World War and the Lehigh Valley\'s Claremont Terminal were not verified): estimated bracket. Ring = today\'s land '
          'east of the Turnpike extension between the Black Tom ring and the line of Chapel Avenue.', WIKI + 'Port_Libert%C3%A9,_Jersey_City', tol=4, close=25)
    R.add('hud_greenville_yard', 'Greenville Yard (Pennsylvania Railroad) and the shore of Greenville', 1900, 1904, gy, 'fill', 'coarse',
          '"The area, east of the Greenville section of Jersey City was originally tidal marshes and white cedar swamps"; "the yard was first developed in 1904 by '
          'the Pennsylvania Railroad". End = the yard; start year estimated. Ring = today\'s land east of the Turnpike extension and Avenue E between the line of '
          'Chapel Avenue and the line of Port Jersey Boulevard.', WIKI + 'Greenville_Yard', tol=4, close=25)
    return left, cav
LEFT = CAV = None
def gc_wrap():
    global LEFT, CAV
    LEFT, CAV = greenville_caven()
run_zone(gc_wrap)

def constable_hook():
    hk = part_at(spine(BAY, 'New Hook Road', 1300, east_of=250), midpoint(BAY, 'New Hook Road'))
    hk = hk.union(any_named('Bayonne Golf Club').intersection(EAST))
    R.add('hud_constable_hook', 'Constable Hook: the refineries\' ground and the Bayonne Golf Club landfill', 1877, 1930, hk, 'fill', 'coarse',
          'Standard Oil\'s works grew "from its original establishment in 1877"; Standard Oil "bought 176 acres of land on Constable Hook" and was "expanding '
          'their refinery" in 1906; Tidewater and Ocean Oil also built there. The Hook itself is natural upland with marsh behind it; no source dates the filling '
          'of the marsh and shore: estimated bracket (start = the first refinery). Ring = today\'s land east of Avenue E within 1.3 km of New Hook Road, plus the golf club outline.',
          WIKI + 'Constable_Hook', tol=5, minus=['hud_military_ocean_terminal', 'hud_port_jersey', 'hud_greenville_yard'], close=40)
run_zone(constable_hook)

def west_side():
    lp = any_named('Lincoln Park', near=midpoint(JC, 'Lincoln Highway'))
    print('   Lincoln Park outline %.1f ha' % (lp.area / 1e4))
    R.add('hud_lincoln_park_west', 'Lincoln Park West: land reclaimed from the Hackensack River', 1904, 1925, lp.intersection(LAND), 'fill', 'coarse',
          'The Hudson County Parks Commission "began work on the park in 1904"; "by 1925, 85 acre of land had been reclaimed from the Hackensack River in the '
          'western portion of the park". Both years documented. Ring = the whole park outline (east and west); only the western, low part is made land.',
          WIKI + 'Lincoln_Park_(Jersey_City)', tol=4)
run_zone(west_side)

def droyers_point():
    names = ['Society Hill Drive North', 'Society Hill Drive South', 'Droyers Pointe Boulevard']
    g = unary_union([JC.geom(n) for n in names] + [any_named('Thomas M. Gerrity Athletic Complex')]).convex_hull.buffer(150).intersection(LAND)
    R.add('hud_droyers_point', 'Droyers Point: the city\'s reclaimed land on Newark Bay (Jersey City Airport, Roosevelt Stadium, Society Hill)', 1925, 1937,
          part_at(g, midpoint(JC, 'Society Hill Drive North')), 'fill', 'coarse',
          '"Originally a tidal marsh"; "in the 1920s the land which was owned by the city became the object of development which included land reclamation and the '
          'construction of bulkhead"; the Jersey City Airport on it "opened in 1927" and Roosevelt Stadium "opened on April 23, 1937". End = the stadium; start year '
          'estimated inside "the 1920s". Ring = the hull of the streets of Society Hill and Droyers Point and of the Gerrity athletic complex + 150 m, on today\'s land.',
          WIKI + 'Droyer%27s_Point', tol=4)
run_zone(droyers_point)

def kearny():
    kp = any_named('Kearny Point')
    print('   Kearny Point outline %.1f ha' % (kp.area / 1e4))
    R.add('hud_kearny_point', 'Kearny Point (South Kearny): Federal Shipbuilding and the industrial fill of the meadow', 1916, 1932, kp.intersection(LAND), 'fill', 'coarse',
          'Federal Shipbuilding: "the ship-ways were completed by the fall of 1917 with keels being laid by November 1917". "From the 1920s through the 1960s, '
          'more than half the acreage of the Meadowlands lying north of Newark Bay was filled in to make new upland" (Marshall 2004). Start = a year before the '
          'ship-ways; end year estimated (estimated bracket for everything but the shipyard). Ring = the Overture outline named Kearny Point.',
          WIKI + 'Federal_Shipbuilding_and_Drydock_Company', tol=5)
    kg = any_named('Keegan Landfill')
    R.add('hud_keegan_landfill', 'Keegan Landfill, Kearny', 1945, 1972, kg, 'fill', 'coarse',
          '"NJMC documents indicate that the Keegan landfill began landfill operations in the 1940\'s, with the majority of landfilling operations taking place in '
          'the 1960\'s. The Keegan Landfill was closed in 1972" (it reopened for construction debris from 2009 and was ordered closed in 2019). Start year '
          'estimated inside "the 1940s". Ring = the Overture outline.', MERI + 'keegan-landfill-2/', tol=4)
    ml = unary_union([named('Malanka Landfill', table='region5_land_use'), named('Malanka Landfill', table='base_land')])
    R.add('hud_malanka_landfill', 'Malanka Landfill, Secaucus', 1960, 1983, ml.convex_hull if ml.geom_type != 'Polygon' else ml, 'fill', 'coarse',
          '"Size: 66 acres ... Closed to operations in 1983." End documented; start year estimated (no source; illegal and legal dumping in the Meadowlands grew '
          'after 1957, Marshall 2004). Ring = the two Overture outlines of that name.', MERI + 'malanka-landfill-2/', tol=4)
run_zone(kearny)

def reservoirs():
    r3 = named('Jersey City Reservoir No. 3', table='base_water')
    R.add('hud_jersey_city_reservoir_3', 'Jersey City Reservoir No. 3', 1874, 9999, r3, 'reservoir', 'precise',
          '"It was built between 1871 and 1874 as part of the city\'s waterworks system"; taken out of service in the 1980s, it still holds water (a lake in a '
          'walled park). Start = completion. Ring = the Overture water outline (the water inside the walls, 3.1 ha).', WIKI + 'Jersey_City_Reservoir_No._3', tol=1)
run_zone(reservoirs)

def north_hudson():
    WEE, WNY, GUT, NB = muni('Weehawken'), muni('West New York'), muni('Guttenberg'), muni('North Bergen')
    T = clip_streets(S, unary_union([WEE, WNY, GUT, NB, muni('Edgewater')]))
    HOB = clip_streets(S, muni('Hoboken'))
    a = end_of(HOB, 'Willow Avenue', 'N')
    p0, p1 = end_of(T, 'Port Imperial Boulevard', 'S'), end_of(T, 'Port Imperial Boulevard', 'N')
    pib = trim_path(T.along('Port Imperial Boulevard', p0, p1, bridge=400), p0, p1)
    r0, r1 = min([c for g in T.by['River Road'] for c in g.coords], key=lambda c: math.dist(c, p1)), end_of(T, 'River Road', 'N')
    rr = trim_path(T.along('River Road', r0, r1, bridge=600), r0, r1)
    line = [p for p in LineString([a] + pib + rr).simplify(20).coords]
    print('   foot-of-the-Palisades line %.0f m: Willow Ave N end %.5f %.5f, Port Imperial Blvd %.0f m, River Road %.0f m to %.5f %.5f'
          % ((LineString(line).length,) + ll(a) + (LineString(pib).length, LineString(rr).length) + ll(r1)))
    east = side_of(line, 'E', 3000).intersection(LAND)
    wk = part_at(east.intersection(WEE), midpoint(clip_streets(S, WEE), 'Harbor Boulevard'))
    R.add('hud_weehawken_waterfront', 'Weehawken waterfront: Slough\'s Meadow, the West Shore Railroad terminal and the Erie yard on Weehawken Cove', 1881, 1884, wk, 'fill', 'coarse',
          'The strip between the river and the Palisades "has been transformed from an estuary flood zone once called Slough\'s Meadow to an extensive rail and '
          'shipping port"; the West Shore\'s tunnel under Bergen Hill "had been built in 1881" and its Weehawken Terminal "opened in 1884". Lincoln Harbor stands on '
          '"the former Erie Railroad Weehawken Yard, which had partially filled the cove to be built" (not dated: estimated to be of the same years). '
          'Ring = Weehawken\'s land east of the line Willow Avenue - Port Imperial Boulevard.', WIKI + 'Weehawken_Terminal', tol=4, close=25)
    nh = east.intersection(unary_union([WNY, GUT, NB]))
    nh = part_at(nh, r0)
    R.add('hud_north_hudson_shore', 'River front under the Palisades: West New York, Guttenberg and North Bergen', 1884, 1920, nh, 'fill', 'coarse',
          'The railway yards and industry on the narrow shelf north of the West Shore terminal (opened 1884). No source dates this fill: estimated bracket. '
          'Ring = today\'s land east of Port Imperial Boulevard and River Road in the three towns.', WIKI + 'Weehawken_Terminal', tol=4, close=25, minus=['hud_weehawken_waterfront'])
    ed = part_at(east.intersection(muni('Edgewater')), midpoint(clip_streets(S, muni('Edgewater')), 'River Road'))
    R.add('ber_edgewater_shore', 'Edgewater river front (east of River Road)', 1900, 1930, ed, 'fill', 'coarse',
          '"Early in the 20th century the addition of landfill to the Hudson River changed the borough\'s appearance"; "in 1922, landfill was dumped into the '
          'Hudson River from the construction site of Yankee Stadium in the Bronx, which gives Veteran\'s Field its current dimensions"; industry "filled 3 mi of '
          'the shoreline". Years estimated inside "early in the 20th century" (estimated bracket). Ring = Edgewater\'s land east of River Road.',
          WIKI + 'Edgewater,_New_Jersey', tol=4, close=25, borough='Bergen')
run_zone(north_hudson)
R.save('hud_b')
