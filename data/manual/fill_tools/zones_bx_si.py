"""The Bronx and Staten Island: coarse rings, mostly outlines of named parks from Overture."""
from zonelib import *
R = Registry(); WIKI = 'https://en.wikipedia.org/wiki/'; Z = run_zone
S = pickle.load(open(os.path.join(INTERIM, 'bx_streets.pkl'), 'rb')); landw = S.island
lande = land_of((-73.885, 40.79, -73.76, 40.90))

# ---------------- west Bronx
Z(lambda: R.add('bx_mott_haven_canal', 'Mott Haven Canal (along Canal Place)', 1896, 1965, S.geom('Canal Place').buffer(75), 'water_fill', 'coarse',
    'A canal dug north from the Harlem River in the mid-19th century (no date found for the digging). "After being declared a nuisance by the '
    'Board of Health in 1896 the canal was slowly re-filled, its last segment being in use until 1960s." Ring = 75 m round Canal Place, '
    'which keeps its line; the reach south of E 135th St is not covered.', WIKI + 'Port_Morris,_Bronx'))
hp = unary_union([named(n) for n in ('NYC Produce Terminal Market in Hunts Point', 'Hunts Point Cooperative Market', 'The New Fulton Fish Market',
                                      'Hunts Point Wastewater Treatment Plant')]).convex_hull.buffer(150)
Z(lambda: R.add('bx_hunts_point_markets', 'Hunts Point: marsh under the markets and the treatment plant', 1950, 1972, hp.intersection(landw.union(lande)),
    'fill', 'coarse',
    'Low ground on the Bronx River side of the point under the sewage works and the wholesale markets. Estimated bracket; no source '
    'found with dates. Ring = hull of the market and plant sites + 150 m.', WIKI + 'Hunts_Point,_Bronx'))
br0 = end_of(S, 'Bruckner Boulevard', 'W'); br1 = XX(S, 'Bruckner Boulevard', 'Tiffany Street')
Z(lambda: R.add('bx_port_morris_oak_point', 'Port Morris and Oak Point: south of Bruckner Boulevard to the East River', 1870, 1920,
    seaward(S.along('Bruckner Boulevard', br0, br1, bridge=400), 1500, XX(S, 'East 149th Street', 'Park Avenue'), landw), 'fill', 'coarse',
    'Shore flats under the rail yards and piers. Estimated bracket; no source found with dates. The ring also holds natural '
    'upland: intersect with the 1609 shore.', WIKI + 'Port_Morris,_Bronx', minus=['bx_hunts_point_markets']))
md0 = near_on(S, 'Major Deegan Expressway', end_of(S, 'East 138th Street', 'W')); md1 = near_on(S, 'Major Deegan Expressway', end_of(S, 'West 230th Street', 'W'))
Z(lambda: R.add('bx_harlem_river_shore', 'Bronx shore of the Harlem River: Major Deegan Expressway to the bulkhead', 1870, 1956,
    seaward(S.along('Major Deegan Expressway', md0, md1, bridge=500), 450, XX(S, 'Grand Concourse', 'East 161st Street'), landw, back=30), 'fill', 'coarse',
    'Low shore along the river under the rail yards and the expressway. Estimated bracket only; no source found with dates.', WIKI + 'Harlem_River'))
rw = named('Randalls and Wards Islands', 'base_land')
Z(lambda: R.add('hb_bronx_kill_fill', 'Bronx Kill narrowed by fill on the Randalls Island side', 1936, 1965,
    named('Bronx Kill', 'base_water').buffer(140).intersection(rw), 'water_fill', 'coarse',
    'In 1917 the kill was still to be dredged to 480 ft wide; "much of the Bronx Kill was later filled in to expand the parkland on '
    'Randalls Island". No dated source found: estimated bracket. Ring = Randalls Island within 140 m of today\'s kill.', WIKI + 'Bronx_Kill'))
# ---------------- east Bronx
Z(lambda: R.add('bx_soundview_park', 'Soundview Park: landfill over the marsh at the mouth of the Bronx River', 1939, 1960,
    named('Soundview Park').buffer(80).intersection(lande), 'fill', 'coarse',
    '"Built on landfill over intertidal marshland": dredge-and-fill planned 1938, funding approved March 1939, refuse fill in place by '
    '1942. End year estimated.', WIKI + 'Soundview_Park'))
FP = WIKI + 'Ferry_Point_Park'
Z(lambda: R.add('bx_ferry_point_west', 'Ferry Point Park, western part along Westchester Creek', 1937, 1940, named('Ferry Point Park'), 'fill', 'coarse',
    'Land acquired 1937 for the Bronx-Whitestone Bridge; "the western part of the park along Westchester Creek opened in 1940". Ring = '
    'the park west of the bridge; only its marsh edge is made land.', FP, tol=4))
Z(lambda: R.add('bx_ferry_point_east', 'Ferry Point Park, eastern part: the cove of Baxter Creek (now the golf links)', 1950, 1970,
    named("Bally's Golf Links at Ferry Point"), 'fill', 'coarse',
    '"The eastern portion was originally a cove that was filled in with landfill by 1970." Start year estimated.', FP, tol=4))
coop = unary_union([named('Co-Op City', all_parts=True), named('Bay Plaza Shopping Center')]).convex_hull
Z(lambda: R.add('bx_co_op_city', 'Co-op City and Bay Plaza (Freedomland site): fill on the Hutchinson River marsh', 1950, 1968, coop.intersection(lande),
    'fill', 'coarse',
    'Marshland of Rattlesnake Creek and the Hutchinson River; "a former municipal landfill" before Freedomland (1960-64); Co-op City '
    '(from 1966) "was built on landfill, and the original marshland still surrounds it". Start year estimated.', WIKI + 'Co-op_City,_Bronx', tol=5))
Z(lambda: R.add('bx_orchard_beach', 'Orchard Beach: LeRoy\'s Bay and Pelham Bay filled, Hunter Island and Rodman\'s Neck joined', 1935, 1938,
    named('Orchard Beach', 'base_land').buffer(520).intersection(lande), 'fill', 'coarse',
    'About one third of Pelham Bay was filled "from 1934 to 1938": refuse fill from early 1935 round Rodman\'s Neck, Twin Island and '
    'Hunter Island, sand from 1936, beach opened 1937. The water between Hunter and Twin Islands was filled in 1946-47 (inside the ring, '
    'not split). Ring = 520 m round today\'s beach.', WIKI + 'Orchard_Beach_(Bronx)'))
# ---------------- Staten Island
Z(lambda: R.add('si_fresh_kills_landfill', 'Fresh Kills Landfill', 1948.3, 2001, named('Freshkills Park'), 'fill', 'coarse',
    'Tidal marsh bought 1946 (2,200 acres); the marsh was dredged for the scows and "the landfill accepted its first scow in April 1948"; '
    'closed 2001. The mounds grew section by section across the span (not split). Ring = Freshkills Park.', WIKI + 'Fresh_Kills_Landfill', tol=8, close=250))
gk = named('Great Kills Park', all_parts=True)
Z(lambda: R.add('si_great_kills_park', 'Great Kills Park and Crooke\'s Point', 1929, 1949, gk.convex_hull.intersection(land_of((-74.16, 40.52, -74.09, 40.57))),
    'fill', 'coarse',
    '"In 1929, the city bought Crooke\'s Point and adjacent land and started to build a public park"; marsh was raised with 15 million '
    'tons of "Sanitation-controlled fill"; opened 1949. Ring = hull of the park.', WIKI + 'Great_Kills_Park', tol=6))
bch = unary_union([named('South Beach', 'base_land'), named('Midland Beach', 'base_land')])
Z(lambda: R.add('si_south_midland_beach', 'South Beach and Midland Beach: beach and boardwalk fill', 1935, 1937,
    bch.convex_hull.buffer(60).intersection(land_of((-74.11, 40.56, -74.05, 40.60))), 'fill', 'coarse',
    'A 1930 state law paid for "a beach and boardwalk" from Fort Wadsworth to Miller Field; boardwalk built 1935-37. The beach has been '
    'widened with sand since; no dated source found for that. Ring = hull of today\'s two beaches + 60 m.', WIKI + 'Franklin_D._Roosevelt_Boardwalk'))
R.save('bx_si')
