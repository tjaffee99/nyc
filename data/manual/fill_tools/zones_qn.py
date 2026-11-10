"""Queens: coarse rings (they bracket made land; intersect with the data-derived fill)."""
from zonelib import *
S0 = li(); land = S0.island; R = Registry(); WIKI = 'https://en.wikipedia.org/wiki/'
Z = run_zone
LIC = sub(S0, -73.965, 40.735, -73.92, 40.775)
FM = sub(S0, -73.87, 40.71, -73.81, 40.77)
NE = sub(S0, -73.80, 40.74, -73.72, 40.80)
HB = sub(S0, -73.87, 40.63, -73.81, 40.68)


def any_named(name):
    for t in ('region_airports', 'region5_land_use'):
        try:
            return named(name, t)
        except KeyError:
            pass
    raise KeyError(name)


# --- Long Island City
v0, v1 = end_of(LIC, 'Vernon Boulevard', 'S'), XX(LIC, 'Vernon Boulevard', 'Queens Plaza South') if 'Queens Plaza South' in LIC.by else near_on(LIC, 'Vernon Boulevard', named('Queensbridge Park').centroid.coords[0])
Z(lambda: R.add('qn_hunters_point_shore', 'Hunters Point / Long Island City waterfront: Vernon Boulevard to the bulkhead', 1850, 1900,
    seaward(LIC.along('Vernon Boulevard', v0, v1, bridge=300), 700, XX(LIC, '21st Street', '44th Drive'), land), 'fill', 'coarse',
    'Marsh and shore filled behind the bulkhead. Estimated bracket; no source found with dates.',
    WIKI + 'Hunters_Point,_Queens'))
qb = unary_union([named('Queensbridge North Houses'), named('Queensbridge South Houses'), named('Queensbridge Park')]).convex_hull
Z(lambda: R.add('qn_sunswick_meadows', 'Sunswick Meadows (Queensbridge / Ravenswood lowland)', 1871, 1915, qb.buffer(220).intersection(land),
    'pond_fill', 'coarse',
    'Marshes round Sunswick Creek were drained in the 1870s after outbreaks of disease in 1871 and 1875; "Sunswick Meadows, a lowland '
    'north of the present Queensboro Bridge, was infilled with the construction of the bridge in the 1900s and 1910s". Ring = hull of '
    'Queensbridge Houses and Park + 220 m.', WIKI + 'Sunswick_Creek'))
# --- LaGuardia, Flushing Meadows
lga = any_named('LaGuardia Airport')
Z(lambda: R.add('qn_laguardia_airport', 'LaGuardia Airport (North Beach): fill into Bowery Bay and Flushing Bay', 1937, 1939.8, lga, 'fill', 'coarse',
    'North Beach resort and the small airport of 1929-35 were enlarged to 550 acres: "construction began in 1937", with "landfill from '
    'Rikers Island, then a garbage dump, onto a metal reinforcing framework"; dedicated 15 October 1939. Runways were lengthened in '
    '1965-66 (inside the ring, not dated separately). Ring = today\'s airport; only the part beyond the 1609 shore is made land.',
    WIKI + 'LaGuardia_Airport', tol=5))
fm = named('Flushing Meadows-Corona Park')
lie = FM.geom('Long Island Expressway').buffer(40)
pieces = [g for g in getattr(fm.difference(lie), 'geoms', [fm.difference(lie)]) if g.area > 1e4]
ymid = lie.intersection(fm.buffer(200)).centroid.y
north = unary_union([g for g in pieces if g.centroid.y > ymid]); south = unary_union([g for g in pieces if g.centroid.y <= ymid])
print('Flushing Meadows north %.0f ha, south %.0f ha' % (north.area / 1e4, south.area / 1e4))
FMP = WIKI + 'Flushing_Meadows%E2%80%93Corona_Park'
Z(lambda: R.add('qn_corona_ash_dump', 'Corona ash dump: Flushing Meadow north of the Long Island Expressway, with Willets Point', 1910, 1934,
    unary_union([north, any_named('Citi Field').buffer(450)]).convex_hull.intersection(land), 'fill', 'coarse',
    'Salt meadow filled with coal ash and street sweepings: "beginning in 1910"; "the filling for the north meadow was complete in 1916"; '
    'the Brooklyn Ash Removal Company dumped until its contract ended in 1933 and the city took over 25 May 1934. Regraded 1936-39 for the '
    'World\'s Fair (no new land). Ring = hull of the park north of the expressway and the Citi Field / Willets Point block.', FMP))
Z(lambda: R.add('qn_flushing_meadows_south', 'Flushing Meadow south of the Long Island Expressway: fill round the new lakes', 1936, 1939.3,
    south.convex_hull.intersection(land), 'fill', 'coarse',
    'For the 1939 World\'s Fair "the southern portion of the river was expanded into the Meadow and Willow Lakes" and the marsh round '
    'them was filled and graded. Start year estimated (fair works 1936-39). Ring = hull of the park south of the expressway.', FMP))
for nm, zid in (('Meadow Lake', 'qn_meadow_lake'), ('Willow Lake', 'qn_willow_lake')):
    Z(lambda nm=nm, zid=zid: R.add(zid, nm + ' (made for the 1939 World\'s Fair)', 1938, 9999, named(nm, 'base_water'), 'reservoir', 'precise',
        'Artificial freshwater lake made from the upper Flushing River marsh "prior to the 1939 New York World\'s Fair"; start year '
        'estimated. Outline = Overture water.', WIKI + nm.replace(' ', '_') + '_(Queens)', tol=3))
Z(lambda: R.add('qn_college_point_mill_creek', 'College Point: Mill Creek and its marsh', 1930, 1965,
    unary_union([named('College Point Fields'), named('College Point Depot')]).convex_hull.buffer(350).intersection(land), 'water_fill', 'coarse',
    '"Until the mid-20th century, the partially infilled Mill Creek separated College Point from the rest of Queens." Estimated bracket. '
    'Ring = hull of College Point Fields and the bus depot + 350 m; it brackets the creek, it is not its outline.', WIKI + 'College_Point,_Queens'))
# --- Little Neck Bay
CIP = WIKI + 'Cross_Island_Parkway'
c0 = near_on(NE, 'Cross Island Parkway', XX(NE, 'Northern Boulevard', 'Cross Island Parkway')); c1 = near_on(NE, 'Cross Island Parkway', named('Little Bay Park').centroid.coords[0])
Z(lambda: R.add('qn_cross_island_little_neck_bay', 'Cross Island Parkway fill along Little Neck Bay', 1938, 1940.5,
    seaward(NE.along('Cross Island Parkway', c0, c1, bridge=400), 350, XX(NE, 'Bell Boulevard', '35th Avenue'), land, back=30), 'fill', 'coarse',
    'The west side of the bay had "extensive salt marshes"; the parkway was laid along it (26 % built by February 1939) and opened with '
    'the Belt system 29 June 1940. Start year estimated.', CIP))
Z(lambda: R.add('qn_alley_pond', 'Alley Pond', 1952, 1954,
    Point(XX(NE, 'Long Island Expressway', 'Cross Island Parkway')).buffer(380), 'pond_fill', 'coarse',
    '"By 1954, when the Long Island Expressway was built, Alley Pond was infilled to create the interchange between the two highways." '
    'Start year estimated. Ring = 380 m circle on the interchange.', WIKI + 'Alley_Pond_Park'))
# --- Jamaica Bay
jfk = any_named('John F. Kennedy International Airport')
Z(lambda: R.add('qn_jfk_airport', 'Idlewild (John F. Kennedy International Airport): fill on the Jamaica Bay marsh', 1943, 1948.5, jfk, 'fill', 'coarse',
    'Site on "a large area of marshland on Jamaica Bay" chosen late 1941; "construction began in 1943"; '
    'opened 1948. First 1,000 acres, 1,350 more condemned 1944; later enlargements to the present 5,200 acres are inside the ring and not '
    'dated separately. Ring = today\'s airport.', WIKI + 'John_F._Kennedy_International_Airport', tol=8))
cb0 = XX(HB, 'Cross Bay Boulevard', 'North Conduit Avenue'); cb1 = XX(HB, 'Cross Bay Boulevard', '165th Avenue')
cbl = HB.along('Cross Bay Boulevard', cb0, cb1, bridge=400)
scq = named('Spring Creek Park', cls='nature_reserve')
HBW = WIKI + 'Howard_Beach,_Queens'
Z(lambda: R.add('qn_howard_beach_east', 'Howard Beach east of Cross Bay Boulevard (Old Howard Beach, Hamilton Beach)', 1897, 1914,
    seaward(cbl, 1000, offset(cbl[0], cbl[-1], -500), land).difference(jfk.buffer(5)), 'fill', 'coarse',
    'William Howard "bought more land and filled it in" from 1897 and "dredged and filled the land until he was able to accumulate 500 '
    'acres by 1914". Ring = 1 km east of Cross Bay Boulevard, Belt Parkway to 165th Avenue.', HBW))
Z(lambda: R.add('qn_howard_beach_west', 'Howard Beach west of Cross Bay Boulevard (Rockwood Park)', 1950, 1962,
    seaward(cbl, 1100, offset(cbl[0], cbl[-1], 500), land).difference(scq.buffer(5)), 'fill', 'coarse',
    '"The marshland west of Cross Bay Boulevard was filled in" for post-war houses; Lindenwood to the north "was developed in the 1950s '
    'and 1960s on landfill". Estimated bracket.', HBW))
Z(lambda: R.add('qn_spring_creek_park_howard_beach', 'Spring Creek Park, Howard Beach side: refuse fill on the marsh', 1949.05, 1954, scq, 'fill', 'coarse',
    '"Landfilling began in Howard Beach on January 17, 1949"; the temporary landfills ran until the incinerator opened in 1954.',
    WIKI + 'Spring_Creek_Park', tol=4))
jb = land_of((-73.845, 40.585, -73.795, 40.625))
bc_line = LineString([named('Broad Channel American Park').centroid, named('Broad Channel Wetlands').centroid])
Z(lambda: R.add('qn_broad_channel', 'Broad Channel: fill on Big Egg Marsh', 1915, 1925, bc_line.buffer(420).intersection(jb), 'fill', 'coarse',
    'The neighbourhood "stands on Big Egg Marsh, an area of fill approximately 20 blocks long and 4 blocks wide"; the Broad Channel '
    'Corporation added landfill and laid out streets after leasing the island. Years estimated. Ring = 420 m round the line between '
    'Broad Channel American Park and Broad Channel Wetlands.', WIKI + 'Broad_Channel,_Queens'))
Z(lambda: R.add('qn_edgemere_landfill', 'Edgemere Landfill (Rockaway Community Park)', 1938.4, 1991, named('Rockaway Community Park'), 'fill', 'coarse',
    '"The landfill began operations in June 1938, merging several islands in the Jamaica Bay marshland and connecting them to the main '
    'Rockaway Peninsula"; it took waste until 1991.', WIKI + 'Edgemere_Landfill', tol=4))
# --- Rockaway point
tip = named('Breezy Point Tip')
west = unary_union([named('Fort Tilden'), named('Jacob Riis Park'), named('Rockaway Point'), named('Breezy Point')]).convex_hull.intersection(land).difference(tip.buffer(5))
JR = WIKI + 'Jacob_Riis_Park'
Z(lambda: R.add('qn_rockaway_point_accretion', 'Rockaway peninsula grown westward: Jacob Riis Park to Rockaway Point (natural accretion)', 1830, 1933,
    west, 'fill', 'coarse',
    'Not made land: "the peninsula was gradually expanded westward by the natural accretion of sand from tidal action". Estimated bracket '
    '(19th century to the building of the inlet jetty, taken as 1933); the sand spit grew from east to west across the span.', JR, tol=5))
Z(lambda: R.add('qn_breezy_point_tip', 'Breezy Point Tip (natural accretion behind the Rockaway Inlet jetty)', 1933, 1975, tip.intersection(land.buffer(30)), 'fill', 'coarse',
    'Not made land: sand built up against the jetty at Rockaway Point. Estimated bracket, no source found with dates; jetty year 1933 not verified.', JR, tol=5))
R.save('qn')
