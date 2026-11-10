"""Sites, second part: gasworks, power plants, oil, shipyards, works, markets, landfills, quarries,
island institutions, hospital campuses, amusement grounds. Same format as sites_def.py."""
import geom as G
from sites_def import S

# ---------------------------------------------------------------------------------------- gas, power, oil
S("elmhurst_gas_tanks", "Elmhurst gas tanks (Newtown Holder Station)", "gasworks", 1910, 1996, "park", "paved", True,
  "Elmhurst_gas_tanks", "Two 200 ft gas holders built between 1910 and 1921; Brooklyn Union Gas began dismantling "
  "them in 1996; Elmhurst Park (2011) has the outline.", lambda: G.osm("1193467f"))
S("gashouse_district", "Gas House District (Consolidated Gas works and holders)", "gasworks", 1842, 1945, "city", "paved",
  True, "Stuyvesant_Town–Peter_Cooper_Village",
  "First gas tank at East 23rd Street and the river 1842, others followed; a district of gas works, holders and "
  "tenements cleared from 1945 for Stuyvesant Town (first building opened 1947), whose outline is used: the works "
  "themselves stood on its river side, so `paved` overstates the tenement blocks (outline estimated).",
  lambda: G.union(G.osm("8a300ebe"), G.osm("4aaa8de6")))
S("waterside_station", "Waterside Generating Station", "power_plant", 1901, 2005, "vacant", "paved", True,
  "Waterside_Generating_Station", "No. 1 (38th-39th Street) began operating October 1901, No. 2 (39th-40th) "
  "November 1906; decommissioned 2005 and demolished. Outline: the street blocks First Avenue - FDR Drive, 38th to "
  "41st Street.", lambda: G.block((-73.9712, 40.7462), (-73.9719, 40.7455), (-73.9707, 40.7470)))
S("east_river_station", "East River Generating Station", "power_plant", 1926, 9999, "same", "paved", True,
  "East_River_Generating_Station", "New York Edison plant at East 14th Street, operating from 23 November 1926.",
  lambda: G.osm("f836436a"), floor=True)
S("ravenswood_station", "Ravenswood Generating Station", "power_plant", 1963, 9999, "same", "paved", True,
  "Ravenswood_Generating_Station", "Units 10 and 20 built 1963, unit 30 ('Big Allis') 1965.",
  lambda: G.osm("da0141b8"), floor=True)
S("poletti_power_project", "Charles Poletti Power Project (Astoria 6)", "power_plant", 1977, 2010, "same", "paved", False,
  "Charles_Poletti_Power_Project", "Generating from 1977, shut 2010.", lambda: G.osm("9cae9487"), floor=True)
S("astral_oil_works", "Astral Oil Works (Charles Pratt, Standard Oil)", "refinery", 1867, 1949, "vacant", "paved", True,
  "Astral_Oil_Works",
  "Pratt's refinery of 1867 on the block between North 12th and North 13th Streets from First Street (Kent Avenue) "
  "to the river, at Bushwick Inlet; Standard Oil from 1874. End year estimated (the works are gone from the 1956 "
  "sheet; not researched). Outline estimated: that block and the inlet's north shore, clipped to land.",
  lambda: G.land(G.ring([(-73.9628, 40.7239), (-73.9590, 40.7228), (-73.9583, 40.7242), (-73.9622, 40.7254)])),
  basis="text")
S("standard_oil_brooklyn_refinery", "Standard Oil (Socony, Mobil) Brooklyn refinery", "refinery", 1870, 1966, "same",
  "paved", True, "Greenpoint_oil_spill",
  "Greenpoint's Newtown Creek shore held more than fifty refineries by 1870 (start = that year: by then); Standard "
  "Oil's successors refined here until 1966 and ran a storage terminal afterwards. Outline estimated: the creek "
  "shore between Kingsland Avenue and Apollo Street north of Norman Avenue.",
  lambda: G.land(G.ring([(-73.9445, 40.7345), (-73.9372, 40.7318), (-73.9362, 40.7275), (-73.9408, 40.7268),
                         (-73.9450, 40.7300)])), basis="estimated")

# ---------------------------------------------------------------------------------------- shipyards and iron works
S("burlee_staten_island_shipbuilding", "Burlee Dry Dock / Staten Island Shipbuilding (Mariners Harbor)", "shipyard", 1903,
  1938, "same", "yard", False, "Bethlehem_Staten_Island", "William Burlee opened the Mariners Harbor yard in 1903. "
  "Outline estimated: 220 m around the article's coordinates, clipped to land.",
  lambda: G.land(G.circle(-74.16222, 40.63912, 220)))
S("bethlehem_staten_island", "Bethlehem Steel Staten Island shipyard", "shipyard", 1938, 1959, "same", "yard", True,
  "Bethlehem_Staten_Island", "Bought by Bethlehem Steel June 1938, closed 1959. Outline estimated (as above).",
  lambda: G.land(G.circle(-74.16222, 40.63912, 220)))
S("morse_dry_dock", "Morse Dry Dock and Repair Company (56th Street)", "shipyard", 1900, 1938, "same", "yard", False,
  "Bethlehem_Brooklyn_56th_Street", "Morse Iron Works and Dry Dock Company incorporated 1900 with the yard at the "
  "foot of 56th Street (start year estimated from the incorporation); United Dry Docks 1929. Outline estimated: "
  "200 m around the article's coordinates, clipped to land.",
  lambda: G.land(G.circle(-74.02424, 40.64849, 200)), basis="estimated")
S("bethlehem_56th_street", "Bethlehem Steel 56th Street shipyard", "shipyard", 1938, 1963, "same", "yard", True,
  "Bethlehem_Brooklyn_56th_Street", "Bethlehem bought the Morse yard in 1938; closed 1963. Outline estimated.",
  lambda: G.land(G.circle(-74.02424, 40.64849, 200)))
S("erie_basin_dry_docks", "Erie Basin dry docks (Robins Dry Dock, Todd Shipyards)", "shipyard", 1866, 2008, "city",
  "yard", True, "Robins_Dry_Dock_and_Repair_Company", "Graving docks at Erie Basin from 1866; Todd Shipyards from 1916; "
  "the last dock was filled for the IKEA car park in 2008 (end = that year). Outline estimated: 260 m around the "
  "article's coordinates, clipped to land.", lambda: G.land(G.circle(-74.01373, 40.67161, 260)))
S("continental_iron_works", "Continental Iron Works", "shipyard", 1861, 1928, "same", "yard", True,
  "Continental_Iron_Works", "Founded 1861 at the foot of West and Calyer Streets, Greenpoint (USS Monitor, 1862); "
  "liquidated 1928. Outline estimated: 110 m circle at that corner, clipped to land.",
  lambda: G.land(G.circle(-73.9612, 40.7268, 110)))
S("morgan_iron_works", "Morgan Iron Works", "factory", 1838, 1907, "city", "yard", False, "Morgan_Iron_Works",
  "Established 1838 at Ninth Street on the East River; defunct 1907. Outline estimated: 80 m circle at the foot of "
  "East 9th Street.", lambda: G.land(G.circle(-73.9752, 40.7242, 80)))
S("allaire_iron_works", "Allaire Iron Works", "factory", 1816, 1869, "city", "yard", False, "Allaire_Iron_Works",
  "Founded 1816 at 466 Cherry Street, Corlears Hook; defunct 1869. Outline estimated: 70 m circle on Cherry Street "
  "near Corlears Hook.", lambda: G.land(G.circle(-73.9795, 40.7118, 70)))
S("shooters_island_shipyard", "Townsend-Downey Shipbuilding (Shooters Island)", "shipyard", 1898, 1910, "vacant", "yard",
  True, "Shooters_Island", "Shipyard 1898-1910 (Standard Shipbuilding bought the island in 1915; its closing year "
  "was not researched).", lambda: G.osm("e8b2397e"))

# ---------------------------------------------------------------------------------------- works
S("steinway_factory", "Steinway & Sons factory (Steinway village)", "factory", 1870, 9999, "same", "paved", True,
  "Steinway,_Queens", "Steinway built a piano factory, sawmill, foundry and workers' housing here from 1870.",
  lambda: G.osm("371937f7"), floor=True)
_DOMINO = lambda: G.land(G.union(G.osm("5c79299e"), G.ring([(-73.9690, 40.7172), (-73.9668, 40.7168), (-73.9655, 40.7122),
                                                             (-73.9677, 40.7118)])))
S("havemeyers_elder_refinery", "Havemeyers & Elder sugar refinery", "factory", 1856, 1882, "same", "paved", True,
  "Domino_Sugar_Refinery", "The Havemeyers' first Williamsburg refinery opened 1856; burned and rebuilt 1882-83. "
  "Outline estimated: Kent Avenue to the river, South 6th to Grand Street (the article: west side of Kent Avenue "
  "between South 2nd and South 6th Streets).", _DOMINO)
S("domino_sugar_refinery", "Domino Sugar Refinery (American Sugar Refining)", "factory", 1882, 2004, "city", "paved", True,
  "Domino_Sugar_Refinery", "Present complex built 1882-83; refining ended 2004 (Domino Park 2018). Outline estimated "
  "(as above).", _DOMINO)
S("pfizer_brooklyn", "Charles Pfizer & Company (Brooklyn plant)", "factory", 1849, 2008, "city", "paved", True, "Pfizer",
  "Founded 1849 on Bartlett Street, Williamsburg; the plant closed in 2008. Outline estimated: 110 m around "
  "630 Flushing Avenue (the plant spread over several blocks).",
  lambda: G.circle(-73.9478, 40.7003, 110))
S("eberhard_faber_pencil_factory", "Eberhard Faber Pencil Company", "factory", 1872, 1956, "city", "paved", True,
  "Eberhard_Faber_Pencil_Factory", "Moved to Greenpoint after the fire of 30 May 1872; left for Pennsylvania 1956. "
  "Outline: the LPC historic district.", lambda: G.lpc("Eberhard Faber Pencil Company Historic District"))
S("port_ivory", "Procter & Gamble, Port Ivory", "factory", 1907, 1991, "same", "paved", True, "Port_Ivory,_Staten_Island",
  "Soap works 1907-1991; the ground went to the Howland Hook container terminal. Outline estimated: 330 m around the "
  "article's coordinates, clipped to land.", lambda: G.land(G.circle(-74.179, 40.640, 330)))
S("kreischer_brick_works", "Kreischer brick works (Kreischerville)", "factory", 1854, 1927, "vacant", "paved", True,
  "Charleston,_Staten_Island", "Factory built 1854, burned 1877 and rebuilt, closed 1927. Outline estimated: 150 m "
  "circle on the Arthur Kill shore at Kreischer Street.", lambda: G.land(G.circle(-74.2408, 40.5378, 150)))
S("kreischer_clay_pits", "Kreischer clay pits", "quarry", 1854, 1927, "park", "open", False,
  "Clay_Pit_Ponds_State_Park_Preserve", "Clay dug for the Kreischer works (1854-1927); Clay Pit Ponds State Park "
  "Preserve since 1977 has the outline (the pits were only part of it: outline estimated).",
  lambda: G.osm("34926dca"), basis="estimated")
S("nassau_smelting", "Nassau Smelting and Refining (Tottenville)", "factory", 1900, 2001, "vacant", "paved", False,
  "Tottenville,_Staten_Island", "Plant built 1900; later Lucent Technologies' recycling works, closed 2001. Outline "
  "estimated: 200 m circle at Richmond Valley Road and Arthur Kill Road.",
  lambda: G.land(G.circle(-74.2395, 40.5215, 200)))

# ---------------------------------------------------------------------------------------- terminals and markets
S("bush_terminal", "Bush Terminal", "terminal", 1895, 9999, "same", "paved", True, "Bush_Terminal",
  "Irving T. Bush built the first six warehouses 1895-1897; piers, lofts and railroad followed from 1902 (Industry "
  "City today). Outline estimated: hull of Industry City, the South Brooklyn Marine Terminal, Sunset Industrial "
  "Park and Bush Terminal Park, clipped to land.",
  lambda: G.land(G.union(G.osm("9bb17a87"), G.osm("e46d5967"), G.osm("3ec15ec1"), G.osm("7d469a1e")).convex_hull),
  floor=True)
S("fulton_fish_market", "Fulton Market and Fulton Fish Market", "terminal", 1822, 2005, "city", "paved", True,
  "Fulton_Fish_Market", "Fulton Market opened 1822; the fish market moved to Hunts Point on 14 November 2005. "
  "Outline: the Fulton Market block and the market sheds on South Street (estimated).",
  lambda: G.land(G.union(G.block((-74.0033, 40.7068)), G.ring([(-74.0031, 40.7060), (-74.0012, 40.7071),
                                                                (-74.0017, 40.7077), (-74.0036, 40.7066)]))))
S("washington_market", "Washington Market", "terminal", 1813, 1967, "city", "paved", True, "Washington_Market",
  "Opened 1813 as the Bear Market; the produce trade moved to Hunts Point in the 1960s (end year estimated: the "
  "Hunts Point market opened 1967). Outline estimated: the block Fulton - Vesey - Washington - West Street.",
  lambda: G.rect(-74.0131, 40.7127, 90, 60, 28))
S("gansevoort_market", "Gansevoort Market", "terminal", 1879, 9999, "same", "paved", True,
  "Meatpacking_District,_Manhattan", "Open-air farmers' market from 1879 on the old freight yards; meat market "
  "later. Outline: the street block Gansevoort - Little West 12th - Washington - West Street.",
  lambda: G.block((-74.0085, 40.7397)))
S("hunts_point_produce_market", "Hunts Point Terminal Produce Market", "terminal", 1967, 9999, "same", "paved", True,
  "Hunts_Point,_Bronx", "Opened 1967.", lambda: G.osm("759cf6eb"), floor=True)
S("hunts_point_meat_market", "Hunts Point Cooperative (Meat) Market", "terminal", 1974, 9999, "same", "paved", False,
  "Hunts_Point,_Bronx", "Opened 1974.", lambda: G.osm("df3f4ea3"), floor=True)
S("new_fulton_fish_market", "New Fulton Fish Market", "terminal", 2005, 9999, "same", "paved", False,
  "Fulton_Fish_Market", "Opened 14 November 2005.", lambda: G.osm("11d740bf"), floor=True)
S("bronx_terminal_market", "Bronx Terminal Market", "terminal", 1935, 2006, "city", "paved", True, "Bronx_Terminal_Market",
  "City market built October 1934 - May 1935 (opened 1 May 1935); demolished from August 2006 for the shopping "
  "centre, whose outline is used.", lambda: G.osm("c383350a"))

# ---------------------------------------------------------------------------------------- landfills and dumps
S("fresh_kills_landfill", "Fresh Kills Landfill", "landfill", 1948, 2001, "park", "open", True, "Fresh_Kills_Landfill",
  "First scow April 1948; closed 2001 (Freshkills Park has the outline; the mounds grew over the decades).",
  lambda: G.osm("f3f9fbd4"))
S("brookfield_landfill", "Brookfield Avenue Landfill", "landfill", 1966, 1980, "park", "open", False,
  "Fresh_Kills_Landfill", "Opened 1966 (trucks only); closing year 1980 estimated - not in the cached source "
  "(Brookfield Park opened 2017).", lambda: G.osm("258830d4"))
S("corona_ash_dumps", "Corona Ash Dumps", "landfill", 1910, 1934, "park", "open", True, "Flushing_Meadows–Corona_Park",
  "Filled with coal ash and street sweepings from 1910 (Brooklyn Ash Removal Company); the city took the dumps in "
  "1934 and the World's Fair grounds followed. Outline estimated: Flushing Meadows north of the Long Island "
  "Expressway.", lambda: G.clip(G.osm("ad7baad7"), -73.87, 40.7385, -73.82, 40.77))
S("pelham_bay_landfill", "Pelham Bay Landfill (Tallapoosa Point)", "landfill", 1963, 1978, "vacant", "open", False,
  "Pelham_Bay_Park", "Landfilling on Tallapoosa Point began 1963 and ended 1978. Outline estimated: 330 m circle "
  "on the point, clipped to land.", lambda: G.land(G.circle(-73.8170, 40.8540, 330)))
_SCSP = lambda: G.osm("2812e9f6")
S("pennsylvania_avenue_landfill", "Pennsylvania Avenue Landfill", "landfill", 1956, 1979, "park", "open", True,
  "Shirley_Chisholm_State_Park", "Operated 1956-1979; Shirley Chisholm State Park (2019), western peninsula.",
  lambda: G.clip(_SCSP(), -73.90, 40.62, -73.868, 40.66))
S("fountain_avenue_landfill", "Fountain Avenue Landfill", "landfill", 1961, 1985, "park", "open", True,
  "Shirley_Chisholm_State_Park", "Operated 1961-1985; Shirley Chisholm State Park (2019), eastern peninsula.",
  lambda: G.clip(_SCSP(), -73.868, 40.62, -73.84, 40.66))
S("edgemere_landfill", "Edgemere Landfill", "landfill", 1938, 1991, "park", "open", True, "Edgemere_Landfill",
  "Operated June 1938 - 1991 (Rockaway Community Park).", lambda: G.osm("6f59f13e"))
S("ferry_point_landfill", "Ferry Point landfill", "landfill", 1952, 1970, "park", "open", False, "Ferry_Point_Park",
  "Department of Sanitation landfill on the east side, 1952-1970 (golf course since 2015, whose outline is used).",
  lambda: G.osm("b34110e0"))
S("barren_island_works", "Barren Island rendering and fertilizer works", "factory", 1859, 1934, "same", "open", True,
  "Barren_Island,_Brooklyn", "Fish-oil, rendering and fertilizer plants and the city's garbage works, 1859-1934, on "
  "the island that became the west of Floyd Bennett Field. Outline estimated: 450 m around the article's "
  "coordinates.", lambda: G.land(G.circle(-73.89306, 40.59278, 450)))
S("rikers_island_landfill", "Rikers Island (city farm and ash landfill)", "landfill", 1884, 1932, "same", "open", True,
  "Rikers_Island", "Bought by the city 1884 and enlarged with ashes from 90 to 415 acres until 1943 (the terrain's "
  "land year decides when ground exists).", lambda: G.osm("418ec08e"))

# ---------------------------------------------------------------------------------------- prisons and island institutions
S("rikers_island_jails", "Rikers Island (penitentiary and jails)", "prison", 1932, 9999, "same", "paved", True,
  "Rikers_Island", "Jail opened 1932 (penitentiary building completed 1935).", lambda: G.osm("418ec08e"), floor=True)
S("blackwells_island", "Blackwell's Island (penitentiary, asylum, almshouse, hospitals)", "prison", 1828, 1921, "same",
  "open", True, "Roosevelt_Island", "Bought by the city 19 July 1828; penitentiary opened 1830, lunatic asylum 1841, "
  "almshouse 1847, workhouse 1852, Smallpox Hospital 1856.", lambda: G.osm("594374de"))
S("welfare_island", "Welfare Island (city hospitals)", "hospital_campus", 1921, 1973, "city", "open", True,
  "Roosevelt_Island", "Renamed Welfare Island 1921 (penitentiary closed 1935); renamed Roosevelt Island 1973 and "
  "rebuilt as a residential town.", lambda: G.osm("594374de"))
S("hart_island", "Hart Island (potter's field, workhouse and institutions)", "other", 1868, 9999, "same", "open", True,
  "Hart_Island", "Army training ground and prison camp 1864-65; bought by the city 1868, first burials 1869.",
  lambda: G.osm("604af9b4"))
S("north_brother_island", "Riverside Hospital (North Brother Island)", "hospital_campus", 1885, 1963, "vacant", "open",
  True, "North_and_South_Brother_Islands_(New_York_City)",
  "Riverside Hospital moved here in 1885; the island's last institution closed in 1963.",
  lambda: G.osm("6ac020a3"), floor=True)
S("randalls_island_institutions", "Randall's Island (House of Refuge, almshouse and children's hospitals)", "asylum",
  1845, 1935, "park", "open", True, "Randalls_and_Wards_Islands", "Almshouse opened 1845, children's hospital 1848, "
  "House of Refuge 1854; the House of Refuge closed 11 May 1935 and the island became a park (Triborough Bridge 1936).",
  lambda: G.osm("4a374e78"))
S("wards_island_institutions", "Wards Island (State Emigrant Refuge, City Asylum for the Insane)", "asylum", 1847, 1899,
  "same", "open", True, "Randalls_and_Wards_Islands", "Leased December 1847 for the State Emigrant Refuge and "
  "Hospital; New York City Asylum for the Insane opened 1863.", lambda: G.osm("2308dee0"))
S("manhattan_state_hospital", "Manhattan State Hospital (Wards Island)", "asylum", 1899, 1936, "park", "open", True,
  "Manhattan_Psychiatric_Center", "Taken over by the State in 1899 as Manhattan State Hospital; end year estimated: "
  "the Triborough Bridge (1936) began the island's conversion to parkland.", lambda: G.osm("2308dee0"))
S("manhattan_psychiatric_center", "Manhattan Psychiatric Center", "asylum", 1936, 9999, "same", "open", False,
  "Manhattan_Psychiatric_Center", "The hospital's remaining campus (start year estimated, see Manhattan State Hospital).",
  lambda: G.osm("9d2de6ac"), basis="estimated")
_SEAVIEW = lambda: G.lpc("New York City Farm Colony- Seaview Hospital Historic District")
S("richmond_county_poor_farm", "Richmond County Poor Farm", "asylum", 1829, 1898, "same", "open", False,
  "New_York_City_Farm_Colony", "Farm bought by Richmond County 1829.", lambda: G.osm("3e9e499c"))
S("new_york_city_farm_colony", "New York City Farm Colony", "asylum", 1898, 1975, "vacant", "open", True,
  "New_York_City_Farm_Colony", "Renamed when Staten Island joined the city (1898); closed 1975.",
  lambda: G.osm("3e9e499c"))
S("seaview_hospital", "Sea View Hospital", "hospital_campus", 1905, 9999, "same", "open", True, "Seaview_Hospital",
  "Tuberculosis hospital planned and built 1905-1938 (administration building and pavilions 1913). Outline: the LPC "
  "historic district less the Farm Colony.", lambda: G.minus(_SEAVIEW(), G.osm("3e9e499c")), floor=True)
S("creedmoor_state_hospital", "Creedmoor State Hospital (Creedmoor Psychiatric Center)", "asylum", 1912, 9999, "same",
  "open", True, "Creedmoor_Psychiatric_Center", "Farm Colony of Brooklyn State Hospital opened 1912.",
  lambda: G.union(G.osm("d3b1a60b"), G.osm("79c964b2"), G.osm("e8186071")), floor=True)
S("kings_county_hospital", "Kings County Hospital (Kings County Almshouse)", "hospital_campus", 1831, 9999, "same", "open",
  True, "Kings_County_Hospital_Center", "County almshouse and hospital established 1830-31.",
  lambda: G.osm("56ab47ec"), floor=True)
S("long_island_state_hospital", "Long Island State Hospital (Kingsboro Psychiatric Center)", "asylum", 1895, 9999, "same",
  "open", False, "Kingsboro_Psychiatric_Center", "The Kings County Lunatic Asylum (mid-19th century) passed to the "
  "State in 1895 as Long Island State Hospital (start = the State hospital).", lambda: G.osm("4cf1720f"))
S("bellevue_hospital", "Bellevue Hospital", "hospital_campus", 1798, 9999, "same", "paved", True, "Bellevue_Hospital",
  "The city bought Belle Vue farm in 1798 for a fever hospital; almshouse and hospital followed on the site.",
  lambda: G.osm("dcfb7853"), floor=True)
S("bronx_state_hospital", "Bronx State Hospital (Bronx Psychiatric Center)", "asylum", 1963, 9999, "same", "open", False,
  "Bronx_Psychiatric_Center", "Opened 1963.", lambda: G.osm("0b2a02b0"), floor=True)
S("bronx_municipal_hospital", "Bronx Municipal Hospital Center (Jacobi)", "hospital_campus", 1955, 9999, "same", "paved",
  False, "Jacobi_Medical_Center", "Founded 1955.", lambda: G.osm("9d9689ed"), floor=True)
S("kingsbridge_veterans_hospital", "Veterans' Hospital, Kingsbridge Road", "hospital_campus", 1922, 9999, "same", "open",
  False, "James_J._Peters_VA_Medical_Center", "Opened 1922 on the grounds of the Roman Catholic Orphan Asylum.",
  lambda: G.osm("04f02ea9"))

# ---------------------------------------------------------------------------------------- amusement grounds (not modelled as landmarks)
S("freedomland", "Freedomland U.S.A.", "other", 1960, 1964, "city", "paved", True, "Freedomland_U.S.A.",
  "Opened 19 June 1960, closed after the 1964 season; Co-op City and the Bay Plaza shopping centre took the ground. "
  "Outline estimated: today's Bay Plaza.", lambda: G.osm("8af8b7dc"))
S("steeplechase_park", "Steeplechase Park", "other", 1897, 1964, "vacant", "paved", True, "Steeplechase_Park",
  "1897-1964 (burned 1907 and rebuilt). Outline estimated: the ballpark that stands on it.",
  lambda: G.union(G.osm("7e975aad"), G.osm("c871f6b3")).convex_hull)
S("luna_park_1903", "Luna Park", "other", 1903, 1944, "city", "paved", True, "Luna_Park_(Coney_Island,_1903)",
  "Opened 16 May 1903; burned August 1944 and closed. Outline: Luna Park Houses, built on its ground.",
  lambda: G.osm("78e24ec4"))
