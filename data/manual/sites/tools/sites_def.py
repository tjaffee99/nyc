"""New York's military and industrial sites: definitions for build.py.

S(id, name, kind, start, end, after, ground, label, src, note, geom, basis="text", floor=False)

  kind    fort | military_base | navy_yard | rail_yard | gasworks | power_plant | refinery | shipyard |
          factory | terminal | landfill | quarry | prison | hospital_campus | asylum | other
  start / end   years the NAME was in use on this ground (end 9999 = still that)
  after   what the ground became: park | city | vacant | same (same: the ground stays as `ground`)
  ground  paved | yard | open - how the terrain should show it while it existed
  src     Wikipedia article title (-> https://en.wikipedia.org/wiki/<title>, text cached in
          data/raw/sites/wp/) or a full URL
  geom    a callable returning the outline (tools/geom.py); "outline estimated" in the note
          when it is not a mapped outline
  basis   text (year stated in the source) | map (bracketed by map editions) | estimated
  floor   True: no building inside may predate `start` (a site_floor row is written)

Every year below was checked against the cached article text (tools/wp_facts.py grep / years).
"""
import geom as G

SITES = []


def S(id, name, kind, start, end, after, ground, label, src, note, geom, basis="text", floor=False):
    SITES.append(dict(id=id, name=name, kind=kind, start=start, end=end, after=after, ground=ground, label=label,
                      src=src, note=note, geom=geom, basis=basis, floor=floor))


# ---------------------------------------------------------------------------------------- forts and bases
_GOV_N = lambda: G.lpc("Governors Island Historic District")          # the historic island (north of Division Road)
_GOV = lambda: G.osm("c5234c30")                                      # the island with the 1900s fill

S("governors_island_fort_jay_1794", "Fort Jay (Governors Island)", "fort", 1794, 1809, "same", "open", True,
  "Governors_Island",
  "Fort Jay begun 1794 on the Revolutionary earthworks; rebuilt 1806-1809 as the star fort and renamed Fort Columbus "
  "shortly afterwards (end year = end of the rebuilding: estimated). Outline: the LPC historic district = the island "
  "before the fill.", _GOV_N)
S("governors_island_fort_columbus", "Fort Columbus (Governors Island)", "fort", 1809, 1904, "same", "open", True,
  "Governors_Island",
  "The rebuilt fort (1806-1809) was known as Fort Columbus until 1904 (start year estimated: 'shortly after' the "
  "rebuilding). Castle Williams 1807-1811, South Battery 1812. Outline: the LPC historic district.", _GOV_N, floor=False)
S("governors_island_army_1904", "Fort Jay (Governors Island Army post)", "military_base", 1904, 1966, "same", "open", True,
  "Governors_Island",
  "Renamed Fort Jay in 1904; Army post until 1966. Outline: the whole island - its southern part is fill finished "
  "by 1912 (the terrain's land year decides when that ground exists).", _GOV)
S("governors_island_coast_guard", "Coast Guard Support Center Governors Island", "military_base", 1966, 1996, "park", "open",
  True, "Governors_Island", "Coast Guard base 1966-1996; sold to the public 2003, opened 2005.", _GOV)
S("fort_wood", "Fort Wood (Bedloe's Island)", "fort", 1806, 1937, "park", "open", True, "Liberty_Island",
  "Eleven-point star fort begun 1806, completed 1811, named Fort Wood after the War of 1812; the statue stands on it "
  "since 1886; the Army left in two stages, 1933 and 1937.", lambda: G.osm("8e2a24b7"), floor=True)
S("fort_gibson", "Fort Gibson (Ellis Island)", "fort", 1808, 1890, "same", "open", True, "Ellis_Island",
  "Island ceded to the United States 1808; battery named Fort Gibson by the end of the War of 1812; a naval magazine "
  "until ordered torn down in April 1890. Outline estimated: the original 3.3-acre island under today's main building.",
  lambda: G.circle(-74.03955, 40.69905, 65))
S("ellis_island_station", "Ellis Island immigration station", "other", 1892, 1954, "park", "paved", False, "Ellis_Island",
  "Federal immigration station 1892-1954 (main building 1900, hospitals 1902-1909) on an island enlarged by fill "
  "from the 1890s to the 1930s (the terrain's land year decides when the ground exists). Label: the place label exists.",
  lambda: G.osm("08ee3a88"), floor=True)
S("fort_hamilton", "Fort Hamilton", "fort", 1825, 9999, "same", "open", True, "Fort_Hamilton",
  "Cornerstone 11 June 1825, the casemate fort completed 1831; still an Army post.", lambda: G.osm("5ae3174e"), floor=True)
_WADS = lambda: G.union(G.osm("61855514"), G.osm("78ff871f"), G.osm("054b9489"), G.osm("94bb3e4d"))
S("fort_wadsworth_1806", "Fort Tompkins and Fort Richmond (New York State works)", "fort", 1806, 1865, "same", "open", True,
  "Fort_Wadsworth",
  "Taken over by New York State in 1806, four forts ready by 1808; federal rebuilding of Fort Richmond (Battery "
  "Weed) and Fort Tompkins from 1847. A Dutch blockhouse stood here from 1663.", _WADS)
S("fort_wadsworth", "Fort Wadsworth", "fort", 1865, 1994, "park", "open", True, "Fort_Wadsworth",
  "Named Fort Wadsworth in 1865; Navy from 1979 (headquarters of Naval Station New York); closed 1994 and passed to "
  "Gateway National Recreation Area (Coast Guard and Army Reserve remain as tenants).", _WADS)
_TOTTEN = lambda: G.union(G.osm("fb47e1bd"), G.osm("108e1134"), G.lpc("Fort Totten Historic District")).convex_hull
S("fort_at_willets_point", "Fort at Willets Point (Camp Morgan)", "fort", 1862, 1898, "same", "open", True,
  "Fort_Totten_(Queens)", "Construction began 1862; named Fort Totten in 1898. Outline: hull of the park, the Army "
  "Reserve centre and the LPC historic district, clipped to land.", lambda: G.land(_TOTTEN()), floor=True)
S("fort_totten", "Fort Totten", "fort", 1898, 1974, "park", "open", True, "Fort_Totten_(Queens)",
  "Named 1898; closed as a Regular Army post 1974 (Army Reserve, Coast Guard and the Fire Department stayed; city "
  "park since 2005).", lambda: G.land(_TOTTEN()))
S("fort_schuyler", "Fort Schuyler", "fort", 1833, 1934, "same", "open", True, "Fort_Schuyler",
  "Begun 1833, dedicated 1856, garrisoned 1861; disarmed and turned over to the State in 1934.",
  lambda: G.osm("ef96b25d"), floor=True)
S("suny_maritime_college", "New York State Maritime College (Fort Schuyler)", "other", 1934, 9999, "same", "open", False,
  "Fort_Schuyler", "Site transferred to the State 1934, restored by the WPA, dedicated to the school 1938.",
  lambda: G.osm("ef96b25d"))
S("fort_tilden", "Fort Tilden", "fort", 1917, 1974, "park", "open", True, "Fort_Tilden",
  "Established 1917 (Camp Rockaway Beach), built 1917-1924; decommissioned and turned over to Gateway National "
  "Recreation Area. End year 1974 estimated: the hand-over year is not in the cached article, whose infobox counts "
  "Army Reserve use to 1995.",
  lambda: G.osm("87d994f1"), floor=True)
S("fort_lafayette", "Fort Lafayette (Fort Diamond)", "fort", 1812, 1960, "city", "paved", True, "Fort_Lafayette",
  "Island fort on Hendricks Reef in the Narrows: begun during the War of 1812, completed 1822, demolished 1960 for "
  "the Brooklyn tower of the Verrazzano-Narrows Bridge. Outline: the island as drawn on the USGS The Narrows "
  "1:24,000 sheet of 1955 (photographs 1954), +-10 m (the reef is water in today's data).",
  lambda: G.local(-74.03861, 40.60833, [(22.5, 37.5), (97.5, 22.5), (100, 5), (112.5, -2.5), (96, -70), (60, -62.5),
                                        (0, -46), (10, 0)]))
S("nas_new_york", "Naval Air Station New York (Floyd Bennett Field)", "military_base", 1941, 1971, "park", "open", True,
  "Floyd_Bennett_Field",
  "Municipal airport dedicated 1930, opened 23 May 1931; Naval Air Station New York from 2 June 1941; the Navy "
  "stopped using the field in 1970 (the cached article) and deactivated the station in 1971 - end year estimated "
  "between the two; Gateway National Recreation Area 1972, park opened 1974.",
  lambda: G.osm("db15271f"))
S("miller_field", "Miller Field (Army airfield)", "military_base", 1919, 1969, "park", "open", True,
  "Miller_Field_(Staten_Island)", "Founded November 1919, completed 1921; closed as an air base 1969 (Gateway NRA).",
  lambda: G.osm("d671151f"), floor=True)
S("nas_rockaway", "Naval Air Station Rockaway", "military_base", 1917, 1930, "park", "open", True,
  "Naval_Air_Station_Rockaway",
  "Established 1917, demolished 1930 for Jacob Riis Park. Outline estimated: today's Riis Park (the station stood on "
  "its bay side).", lambda: G.osm("9480e185"))
_BNY = lambda: G.union(G.osm("b9558563"), G.osm("26e0648b"), G.osm("a6f83d98"), G.osm("e174fbb3"), G.osm("7eb0d8a6"))
S("brooklyn_navy_yard", "New York Navy Yard (Brooklyn Navy Yard)", "navy_yard", 1801, 1966, "same", "paved", True,
  "Brooklyn_Navy_Yard",
  "40 acres bought 7 February 1801 at the west end of Wallabout Bay; the yard grew east over fill (the terrain's "
  "land year decides when ground exists; the 25 acres of the Wallabout Market at the east end came back in 1941); "
  "decommissioned 30 June 1966.", _BNY, floor=True)
S("brooklyn_navy_yard_industrial", "Brooklyn Navy Yard (industrial park)", "factory", 1969, 9999, "same", "paved", True,
  "Brooklyn_Navy_Yard", "Sold to the city (contract December 1969); industrial park since.", _BNY)
S("brooklyn_naval_hospital", "Brooklyn Naval Hospital", "hospital_campus", 1838, 1948, "vacant", "open", True,
  "Brooklyn_Naval_Hospital", "Main building completed 1838; hospital closed 1948 (grounds used as a Navy annex "
  "afterwards; ruins today).", lambda: G.osm("486c0124"), floor=True)
S("brooklyn_army_base", "Brooklyn Army Base (New York Port of Embarkation)", "military_base", 1919, 1966, "same", "paved",
  True, "Brooklyn_Army_Terminal", "Construction from 15 May 1918, completed September 1919; decommissioned "
  "9 December 1966 (fully vacated 1975).", lambda: G.osm("7a7fa665"), floor=True)
S("brooklyn_army_terminal", "Brooklyn Army Terminal", "terminal", 1981, 9999, "same", "paved", True,
  "Brooklyn_Army_Terminal", "Bought by the city in 1981 and let to industry.", lambda: G.osm("7a7fa665"))
S("naval_station_new_york", "Naval Station New York (Stapleton home port)", "military_base", 1990, 1994, "vacant", "paved",
  True, "Naval_Station_New_York", "Opened 1990 under the Strategic Homeport programme, closed 1994.",
  lambda: G.union(G.osm("3a84716e"), G.osm("5f14f09b"), G.osm("0cf6216c")), floor=True)
S("stapleton_piers", "Stapleton piers (Foreign-Trade Zone No. 1)", "terminal", 1920, 1975, "vacant", "paved", False,
  "Stapleton,_Staten_Island", "City piers built 1920; the first Foreign Trade Zone in the United States 1937-1942 "
  "and again after the war; most piers demolished by the 1970s (end year estimated). Outline estimated: the later "
  "naval station.", lambda: G.union(G.osm("3a84716e"), G.osm("5f14f09b"), G.osm("0cf6216c")))
S("halloran_general_hospital", "Halloran General Hospital (Army)", "hospital_campus", 1942, 1947, "same", "open", True,
  "Halloran_General_Hospital", "Built 1938-1942 as a state school, used first as an Army hospital (1942-1947).",
  lambda: G.osm("8c0eea90"), floor=True)
S("willowbrook_state_school", "Willowbrook State School", "asylum", 1947, 1987, "city", "open", True,
  "Willowbrook_State_School", "Opened by the State October 1947, closed 17 September 1987; the grounds became the "
  "College of Staten Island (early 1990s).", lambda: G.osm("8c0eea90"))
S("quarantine_tompkinsville", "New York Marine Hospital (the Quarantine)", "hospital_campus", 1799, 1858, "city", "open",
  True, "Staten_Island_Quarantine_War",
  "Quarantine law of 1799; burned by local residents 1-2 September 1858. Outline estimated: a 12 ha (30 acre) "
  "circle at the later lighthouse depot in St. George - no mapped outline was traced.",
  lambda: G.land(G.circle(-74.0750, 40.6410, 195)))
S("hoffman_island_quarantine", "Hoffman Island quarantine station", "hospital_campus", 1873, 1938, "vacant", "open", True,
  "Hoffman_Island", "Artificial island made 1873 for the quarantine; Merchant Marine training station from 1938 "
  "(end year = that hand-over).", lambda: G.osm("3109321b"))
S("swinburne_island_quarantine", "Swinburne Island quarantine hospital", "hospital_campus", 1870, 1938, "vacant", "open",
  True, "Swinburne_Island", "Island heaped up from 1860, developed 1870 into the quarantine hospital; Merchant Marine "
  "training station from 1938 (end year = that hand-over).", lambda: G.osm("b7e6eee1"))
S("seamens_retreat", "Seamen's Retreat / U.S. Marine Hospital (Bayley Seton)", "hospital_campus", 1831, 9999, "same",
  "open", False, "Bayley_Seton_Hospital", "Opened 1 October 1831; a private hospital from 1981. Outline: the street "
  "block of today's campus.", lambda: G.block((-74.07542, 40.62233)), floor=True)
S("sailors_snug_harbor", "Sailors' Snug Harbor", "other", 1831, 1976, "park", "open", True, "Sailors'_Snug_Harbor",
  "Site bought May 1831, Building C opened August 1833; home for retired seamen until 1976 (cultural centre since).",
  lambda: G.osm("70be5c64"), floor=True)
S("creedmoor_rifle_range", "Creedmoor Rifle Range", "military_base", 1873, 1907, "same", "open", True,
  "Creedmoor_Rifle_Range", "National Rifle Association / National Guard range opened 21 June 1873; given up in 1907 "
  "(the State hospital followed in 1912). Outline: the hospital campus that took its ground.",
  lambda: G.union(G.osm("d3b1a60b"), G.osm("79c964b2"), G.osm("e8186071")))

# ---------------------------------------------------------------------------------------- rail yards
S("sunnyside_yard", "Sunnyside Yard", "rail_yard", 1910, 9999, "same", "yard", True, "Sunnyside_Yard",
  "Built 1903-1910 by the Pennsylvania Railroad, completed 1910 (192 acres).",
  lambda: G.union(G.osm("47409597"), G.osm("5d1afcb7")), floor=True)
_WSY = lambda: G.union(G.osm("d3322ebe"), G.block((-74.0012, 40.7535)))
S("thirtieth_street_yard", "30th Street Yard (Hudson River Railroad, New York Central)", "rail_yard", 1851, 1987, "same",
  "yard", True, "West_Side_Yard", "The Hudson River Railroad built the 30th Street Yard around 1851 (year estimated: "
  "'around 1851'); the LIRR's West Side Yard took the ground in 1987. Outline: today's yard between 30th and 33rd "
  "Streets, Tenth and Twelfth Avenues.", _WSY, basis="estimated")
S("west_side_yard", "West Side Yard (John D. Caemmerer)", "rail_yard", 1987, 9999, "same", "yard", True, "West_Side_Yard",
  "Opened 1987; decked over for Hudson Yards from 2012.", _WSY)
S("st_johns_park_freight_terminal", "St. John's Park Freight Depot", "rail_yard", 1867, 1927, "city", "paved", True,
  "St._John's_Park", "The park was sold in 1866; construction of the 4-acre depot began 1867 (opened 1868); "
  "demolished 1927 for the Holland Tunnel exit. Outline estimated: hull of today's street blocks of the tunnel exit "
  "plaza (Hudson, Laight, Varick, Beach streets).",
  lambda: G.union(G.block((-74.0080, 40.7213)), G.block((-74.0068, 40.7216)), G.block((-74.0072, 40.7209))).convex_hull)
S("sixtieth_street_yard", "60th Street Yard (New York Central)", "rail_yard", 1880, 1975, "vacant", "yard", True,
  "Riverside_South,_Manhattan",
  "'By 1880' river had become the New York Central's 60th Street Yard (start = that year: by then); industrial "
  "'until the 1970s' (end year estimated: 1975); Riverside South was built on it from 1997. Outline estimated: "
  "59th to 72nd Street between the river and Freedom Place / West End Avenue.",
  lambda: G.land(G.ring([(-73.9950, 40.7722), (-73.9905, 40.7712), (-73.9893, 40.7742), (-73.9889, 40.7763),
                         (-73.9869, 40.7790), (-73.9872, 40.7808), (-73.9900, 40.7815), (-73.9930, 40.7770)])),
  basis="estimated")
S("bay_ridge_65th_street_yard", "Bay Ridge (65th Street) Yard", "rail_yard", 1876, 9999, "same", "yard", True,
  "65th_Street_Yard", "New York, Bay Ridge and Jamaica Railroad begun November 1875, opened 23 August 1876; the Long "
  "Island Rail Road's car-float terminal.", lambda: G.osm("da023e1b"), floor=True)
S("coney_island_yard", "Coney Island Yard and Shops", "rail_yard", 1926, 9999, "same", "yard", True,
  "New_York_City_Subway_yards", "Built 1926 on the marsh of Coney Island Creek.",
  lambda: G.union(G.osm("e13fae98"), G.osm("e615093f")), floor=True)
S("yard_207th_street", "207th Street Yard", "rail_yard", 1932, 9999, "same", "yard", True, "IND_Eighth_Avenue_Line",
  "Independent Subway yard, opened with the Eighth Avenue Line on 10 September 1932.", lambda: G.osm("cf302ef0"),
  floor=True)
S("jamaica_yard", "Jamaica Yard", "rail_yard", 1936, 9999, "same", "yard", True, "New_York_City_Subway_yards",
  "Opened 1936 with the Queens Boulevard Line.", lambda: G.osm("12d8d8fa"), floor=True)
S("corona_yard", "Corona Yard", "rail_yard", 1928, 9999, "same", "yard", True, "New_York_City_Subway_yards",
  "Opened 1928.", lambda: G.osm("b926d737"), floor=True)
S("livonia_yard", "Livonia Yard", "rail_yard", 1923, 9999, "same", "yard", False, "New_York_City_Subway_yards",
  "Built 1922, opened 1923.", lambda: G.osm("760ccf21"), floor=True)
S("pitkin_yard", "Pitkin Yard", "rail_yard", 1948, 9999, "same", "yard", False, "New_York_City_Subway_yards",
  "Opened 28 November 1948 (apartment towers built over it 1972-73).", lambda: G.osm("40b433a6"))
S("concourse_yard", "Concourse Yard", "rail_yard", 1933, 9999, "same", "yard", False, "New_York_City_Subway_yards",
  "Built 1933 on the unbuilt eastern basin of the Jerome Park Reservoir.", lambda: G.osm("7ba4e795"), floor=True)
S("canarsie_yard", "Canarsie (Rockaway Parkway) Yard", "rail_yard", 1917, 9999, "same", "yard", False,
  "New_York_City_Subway_yards", "Opened 26 October 1917.", lambda: G.osm("11fb34b7"), floor=True)
S("east_new_york_yard", "East New York Yard", "rail_yard", 1885, 9999, "same", "yard", True, "New_York_City_Subway_yards",
  "Portions date back to 1885 (Lexington Avenue Elevated).", lambda: G.osm("1c72aee2"), floor=True)
S("yard_239th_street", "239th Street Yard", "rail_yard", 1916, 9999, "same", "yard", False, "New_York_City_Subway_yards",
  "Opened 1916.", lambda: G.osm("9a91857e"), floor=True)
S("unionport_yard", "East 180th Street and Unionport Yards", "rail_yard", 1918, 9999, "same", "yard", False,
  "New_York_City_Subway_yards", "The original shop building dated from 1918 (year of the yard estimated from it).",
  lambda: G.osm("ecd27cab"), basis="estimated", floor=True)
S("morris_park_shops", "Morris Park Shops (Long Island Rail Road)", "rail_yard", 1889, 9999, "same", "yard", True,
  "Morris_Park_Facility", "Opened 1 November 1889.", lambda: G.union(G.osm("5b009c46"), G.osm("2f459f1c")), floor=True)
S("hillside_facility", "Hillside Maintenance Complex (Long Island Rail Road)", "rail_yard", 1991, 9999, "same", "yard",
  False, "Hillside_Facility", "Opened 22 July 1991.", lambda: G.osm("154ffce1"), floor=True)
S("brooklyn_eastern_district_terminal", "Brooklyn Eastern District Terminal", "rail_yard", 1906, 1983, "park", "yard",
  True, "Brooklyn_Eastern_District_Terminal",
  "Organised 1906 out of Palmer's Dock (car-float yard on Kent Avenue, North 3rd to North 10th Street); operated "
  "until 1983; now Marsha P. Johnson (East River) State Park, whose outline is used.",
  lambda: G.named("Marsha P. Johnson State Park"))
S("harlem_river_yard", "Harlem River Yard", "rail_yard", 1991, 9999, "same", "yard", True, "Harlem_River_Intermodal_Yard",
  "The New Haven's (Penn Central's from 1969) 96-acre Harlem River freight yard, leased by the State to Harlem River "
  "Yard Ventures in 1991 (start = the lease: the 19th-century founding year of the railroad yard is not stated in "
  "the source and was not researched). Outline estimated: the waterfront between the Robert F. Kennedy and Hell Gate "
  "bridges south of East 132nd Street.",
  lambda: G.land(G.ring([(-73.9285, 40.8030), (-73.9200, 40.8032), (-73.9120, 40.8012), (-73.9085, 40.7985),
                         (-73.9100, 40.7968), (-73.9180, 40.7985), (-73.9265, 40.8005)])))
