"""Brooklyn: coarse rings (they bracket made land; intersect with the data-derived fill)."""
from zonelib import *
S0 = li(); land = S0.island; R = Registry(); WIKI = 'https://en.wikipedia.org/wiki/'
Z = run_zone
NW = sub(S0, -74.03, 40.66, -73.96, 40.71)
SW = sub(S0, -74.05, 40.60, -73.985, 40.67)
SO = sub(S0, -74.05, 40.565, -73.93, 40.63)
SE = sub(S0, -73.95, 40.57, -73.85, 40.67)
NO = sub(S0, -73.975, 40.695, -73.93, 40.74)

# --- Fulton Ferry, Dumbo, the Heights piers
fur_s, fur_n = end_of(NW, 'Furman Street', 'S'), end_of(NW, 'Furman Street', 'N')
inl = XX(NW, 'Court Street', 'Atlantic Avenue')
Z(lambda: R.add('bk_fulton_ferry_dumbo', 'Brooklyn Heights piers, Fulton Ferry and Dumbo: Furman St / Front St to the bulkhead', 1800, 1860,
    seaward([fur_s, fur_n, XX(NW, 'Front Street', 'Old Fulton Street'), end_of(NW, 'Front Street', 'E')], 500, inl, land), 'fill', 'coarse',
    'Wharves and warehouse blocks built out from the foot of the Heights and the Fulton Ferry landing. Estimated bracket; no source '
    'found with dates. Inner line Furman St and Front St only brackets the area.', WIKI + 'Fulton_Ferry,_Brooklyn'))
navy = named('Brooklyn Navy Yard')
Z(lambda: R.add('bk_wallabout_navy_yard', 'Wallabout Bay: the Brooklyn Navy Yard and Wallabout Market flats', 1801, 1942,
    navy.buffer(380).intersection(land), 'fill', 'coarse',
    'The yard stands on "a mudflat and tidal marsh" of Wallabout Bay; in its wartime enlargement "extensive landfilling operations" '
    'removed the market and the Cob Dock and filled the market branch of Wallabout Basin and the Kent Avenue basin. Estimated bracket '
    '(founding of the yard to the wartime enlargement); the stages inside it are not mapped.', WIKI + 'Brooklyn_Navy_Yard'))
col_n = end_of(NW, 'Columbia Street', 'N'); col_h = XX(NW, 'Columbia Street', 'Hamilton Avenue'); ham_e = XX(NW, 'Hamilton Avenue', 'Smith Street')
RH = WIKI + 'Red_Hook,_Brooklyn'
Z(lambda: R.add('bk_red_hook', 'Red Hook and the Columbia Street waterfront: west of Columbia St and Hamilton Avenue', 1840, 1880,
    seaward(NW.along('Columbia Street', col_n, col_h, bridge=300) + NW.along('Hamilton Avenue', col_h, ham_e, bridge=300)[1:], 2600, inl, land)
    .intersection(unary_union([NW.geom('Van Brunt Street'), NW.geom('Columbia Street'), named('Erie Basin Auto Pound'), named('Red Hook Park'), named('Red Hook Container Terminal')]).convex_hull.buffer(350)),
    'fill', 'coarse',
    'Red Hook "was a low-lying area full of tidal mill ponds"; the hook itself was an island. Atlantic Basin was dredged in 1850 and '
    'Erie Basin in 1864, with the marsh round them filled for the docks. Estimated bracket; the basins are water and stay water.', RH))
gow = named('Gowanus Canal', 'base_water', all_parts=True)
Z(lambda: R.add('bk_gowanus', 'Gowanus Creek marsh along the canal', 1849, 1869,
    gow.buffer(260).intersection(land), 'fill', 'coarse',
    'The canal "was created in the mid-19th century from local tidal wetlands": the Legislature allowed the creek to be dredged in 1849, '
    'dredging "was completed in 1860", deepening allowed 1867; the marsh on both sides was drained and filled with it. '
    'Ring = 260 m round today\'s canal; end year estimated.', WIKI + 'Gowanus_Canal', minus=['bk_red_hook']))
# --- Sunset Park
a2s, a2n = end_of(SW, '2nd Avenue', 'S'), end_of(SW, '2nd Avenue', 'N')
inl2 = XX(SW, '5th Avenue', '39th Street')
Z(lambda: R.add('bk_bush_terminal_piers_infill', 'Bush Terminal: slips between Piers 1-4 filled (Bush Terminal Park)', 1974, 1978,
    named('Bush Terminal Park').buffer(90).intersection(land), 'fill', 'coarse',
    'In 1974 the city hired a company "to fill the spaces between Piers 1 through 4"; filling went on through the 1975 fiscal crisis. '
    'End year estimated. Ring = Bush Terminal Park + 90 m.', WIKI + 'Bush_Terminal'))
Z(lambda: R.add('bk_sunset_park_waterfront', 'Sunset Park waterfront: 2nd Avenue to the bulkhead (Bush Terminal, Army Terminal)', 1890, 1919.7,
    seaward([a2s, a2n], 1300, inl2, land), 'fill', 'coarse',
    'Bush Terminal: five piers complete by 1905 between 39th and 51st St; Brooklyn Army Terminal built 15 May 1918 - September 1919. '
    'Start year estimated. Inner line 2nd Avenue only brackets the area.', WIKI + 'Bush_Terminal', minus=['bk_bush_terminal_piers_infill']))
# --- Shore Parkway
BP = WIKI + 'Belt_Parkway'
b0 = near_on(SO, 'Belt Parkway', end_of(SW, 'Shore Road', 'N')); b1 = near_on(SO, 'Belt Parkway', XX(SO, 'Cropsey Avenue', 'Bay Parkway'))
Z(lambda: R.add('bk_shore_parkway', 'Shore Parkway (Belt Parkway) fill, Owl\'s Head to Bay Parkway', 1934, 1940.5,
    seaward(SO.along('Belt Parkway', b0, b1, bridge=400), 500, XX(SO, '86th Street', '4th Avenue'), land, back=35), 'fill', 'coarse',
    'The parkway along the Narrows and Gravesend Bay was built on fill (11.8 million cubic yards of hydraulic fill on the whole Belt '
    'system) and opened 29 June 1940. Start year estimated. Ring = from 35 m inland of the parkway centre line to the water.', BP))
Z(lambda: R.add('bk_dyker_beach', 'Dyker Beach Park: the swamp', 1918, 1934, named('Dyker Beach Park'), 'pond_fill', 'coarse',
    '"In 1918 work began to fill the swampy areas of the park." End year estimated. Ring = the park.', WIKI + 'Dyker_Beach_Park', close=120))
cic = named('Coney Island Creek', 'base_water'); shb = named('Sheepshead Bay', 'base_water')
CI = WIKI + 'Coney_Island_Creek'
Z(lambda: R.add('bk_coney_island_creek_middle', 'Coney Island Creek: the filled middle reach to Sheepshead Bay', 1920, 1937,
    corridor(cic, shb, 220).intersection(land), 'water_fill', 'coarse',
    'The creek once ran through to Sheepshead Bay and made Coney Island an island. "By 1924 local land owners had filled a portion"; '
    '"a major section was further filled in to allow construction of the Belt Parkway in the 1930s". Ring = a 440 m corridor on the '
    'straight line between today\'s creek head and Sheepshead Bay; the real bed wound. Years estimated inside "1920s and 1930s".', CI))
Z(lambda: R.add('bk_calvert_vaux_park', 'Calvert Vaux (Dreier-Offerman) Park fill at the creek mouth', 1962, 1965,
    named('Calvert Vaux Park').buffer(40).intersection(land), 'fill', 'coarse',
    '"The park was expanded in the 1960s by waste from the construction of the Verrazzano-Narrows Bridge"; "more fill was added in 1962". '
    'End year estimated.', WIKI + 'Calvert_Vaux_Park'))
Z(lambda: R.add('bk_plumb_beach_hog_creek', 'Plumb Beach joined to Brooklyn (Hog Creek filled)', 1937, 1940,
    named('Plumb Beach').buffer(60).intersection(land), 'water_fill', 'coarse',
    '"Plumb Beach was originally part of a small island until Hog Creek was filled in during the late 1930s." Years estimated inside '
    'that phrase. Ring = Plumb Beach park + 60 m.', WIKI + 'Plumb_Beach,_Brooklyn'))
# --- Jamaica Bay shore
fbf = named('Floyd Bennett Field')
Z(lambda: R.add('bk_floyd_bennett_field', 'Floyd Bennett Field: Barren Island joined to Brooklyn', 1928, 1931.4, fbf, 'fill', 'coarse',
    'Made "by connecting Barren Island and several smaller islands to the rest of Brooklyn by filling the channels between them with '
    'sand pumped from the bottom of Jamaica Bay": first contract May 1928 (4.45 million cubic yards over 350 acres), dedicated 26 June '
    '1930, opened 23 May 1931. Later enlargements (1930s, Navy 1941-42) are inside the ring but not dated separately.',
    WIKI + 'Floyd_Bennett_Field', tol=5))
Z(lambda: R.add('bk_marine_park', 'Marine Park: marsh filled for the park', 1931, 1939, named('Marine Park', near=XX(SE, 'Avenue U', 'Gerritsen Avenue')).difference(fbf.buffer(5)),
    'fill', 'coarse',
    'Land given 1920; "development was slow, but with new land purchases, the park grew" by 1937; it is still "mainly a fertile salt marsh". '
    'Estimated bracket, no source found with fill dates. Ring = the park.', WIKI + 'Marine_Park_(Brooklyn_park)', tol=5, close=250))
u0 = XX(SE, 'Avenue U', 'Flatbush Avenue'); u1 = end_of(SE, 'Avenue U', 'E')
Z(lambda: R.add('bk_mill_basin_bergen_beach', 'Mill Basin and Bergen Beach: south of Avenue U, Flatbush Avenue to Paerdegat Basin', 1895, 1939,
    seaward(SE.along('Avenue U', u0, u1, bridge=400), 2600, XX(SE, 'Flatlands Avenue', 'Ralph Avenue'), land).difference(fbf.buffer(5)),
    'fill', 'coarse',
    'Mill Island and Bergen Island lay in marsh: bulkheads from the late 1890s, Bergen Beach joined to the mainland by 1918 (some say '
    '1911), Mill Island by 1926, the dredge-and-fill "completed by the late 1930s"; more fill at Bergen Beach in the 1980s (not split).',
    WIKI + 'Mill_Basin,_Brooklyn', close=150))
Z(lambda: R.add('bk_paerdegat_basin', 'Paerdegat Basin, dredged out of Paerdegat Creek', 1925, 1931,
    named('Paerdegat Basin Park').convex_hull, 'excavation', 'coarse',
    'A tidal creek until it "came to its present form in the late 1920s" as a straight basin for the Jamaica Bay port scheme. Years '
    'estimated inside that phrase. Ring = hull of Paerdegat Basin Park; clip to today\'s water.', WIKI + 'Paerdegat_Basin'))
sv0 = end_of(SE, 'Seaview Avenue', 'W'); sv1 = XX(SE, 'Seaview Avenue', 'East 108th Street')
Z(lambda: R.add('bk_canarsie_shore', 'Canarsie shore: Seaview Avenue to the bay (Canarsie Park and Pier)', 1900, 1940,
    seaward(SE.along('Seaview Avenue', sv0, sv1, bridge=500), 900, XX(SE, 'Flatlands Avenue', 'Rockaway Parkway'), land), 'fill', 'coarse',
    'Marshy meadow in 1900; "in the early 20th century more than 1 mile of shoreline was filled in with a bulkhead"; park enlarged 1934. '
    'Estimated bracket.', WIKI + 'Canarsie,_Brooklyn'))
Z(lambda: R.add('bk_starrett_city', 'Starrett City (Spring Creek Towers) peninsula between Fresh Creek and Hendrix Creek', 1955, 1972,
    named('Spring Creek Towers').buffer(220).intersection(land), 'fill', 'coarse',
    'Marsh peninsula filled before the housing: site bought for development 1962, complex opened 1974. Estimated bracket, no source '
    'found with fill dates.', WIKI + 'Starrett_City'))
sc = named('Shirley Chisholm State Park', all_parts=True)
parts = sorted([g for g in getattr(sc, 'geoms', [sc]) if g.area > 5e4], key=lambda g: g.centroid.x)
print('Shirley Chisholm parts (ha):', [round(g.area / 1e4) for g in parts])
SCP = WIKI + 'Shirley_Chisholm_State_Park'
if len(parts) >= 2:
    Z(lambda: R.add('bk_pennsylvania_avenue_landfill', 'Pennsylvania Avenue Landfill', 1956, 1985, parts[0], 'fill', 'coarse',
        '"Filling at the Pennsylvania Avenue Landfill began in 1956"; the city was bound to close and cap both landfills by 1985. '
        'Western peninsula of Shirley Chisholm State Park.', SCP, tol=4))
    Z(lambda: R.add('bk_fountain_avenue_landfill', 'Fountain Avenue Landfill', 1961, 1985, parts[-1], 'fill', 'coarse',
        'Began operations "in 1961 or 1963"; closed and capped by 1985. Eastern peninsula of Shirley Chisholm State Park.', SCP, tol=4))
else:
    Z(lambda: R.add('bk_penn_fountain_landfills', 'Pennsylvania Avenue and Fountain Avenue landfills', 1956, 1985, sc.convex_hull, 'fill', 'coarse',
        'Pennsylvania Avenue Landfill from 1956, Fountain Avenue from 1961 or 1963; both closed and capped by 1985.', SCP, tol=4))
Z(lambda: R.add('bk_spring_creek_park', 'Spring Creek Park (Brooklyn / Queens line): marsh filled with refuse', 1948, 1954,
    named('Spring Creek Park', cls='park'), 'fill', 'coarse',
    '"By 1948, portions of the park in Brooklyn were landfilled"; temporary landfills ran until the incinerator opened in 1954. '
    'Start year is the "by" date.', WIKI + 'Spring_Creek_Park', tol=4, close=150))
# --- Williamsburg, Greenpoint
k0, k1 = end_of(NO, 'Kent Avenue', 'S'), end_of(NO, 'Kent Avenue', 'N')
inl_n = XX(NO, 'Bedford Avenue', 'Broadway')
GP = sub(S0, -73.966, 40.7235, -73.945, 40.74)      # Greenpoint only: another Franklin Street lies further south
Z(lambda: R.add('bk_williamsburg_shore', 'Williamsburg waterfront: Kent Avenue to the bulkhead (Navy Yard to Bushwick Inlet)', 1830, 1890,
    seaward(NO.along('Kent Avenue', k0, k1, bridge=400), 700, inl_n, land), 'fill', 'coarse',
    'Shore built out for shipyards, refineries and ferry slips. Estimated bracket; no source found with dates.', WIKI + 'Williamsburg,_Brooklyn',
    minus=['bk_wallabout_navy_yard']))
Z(lambda: R.add('bk_greenpoint_shore', 'Greenpoint waterfront: Franklin St / Commercial St to the bulkhead (Bushwick Inlet to Newtown Creek)', 1830, 1890,
    seaward([end_of(GP, 'Franklin Street', 'S'), end_of(GP, 'Franklin Street', 'N'), end_of(GP, 'Commercial Street', 'E')], 700,
            XX(GP, 'Manhattan Avenue', 'Greenpoint Avenue'), land), 'fill', 'coarse',
    'Shore built out for shipyards and factories. Estimated bracket; no source found with dates.', WIKI + 'Greenpoint,_Brooklyn'))
mcc = named('McCarren Park')
Z(lambda: R.add('bk_bushwick_creek', 'Bushwick Creek and its marsh (McCarren Park to Bushwick Inlet)', 1896, 1913,
    unary_union([mcc.buffer(250), LineString([(mcc.centroid.x, mcc.centroid.y), XX(NO, 'Kent Avenue', 'North 14th Street')]).buffer(200)]).intersection(land),
    'water_fill', 'coarse',
    'Filling the creek was proposed in 1896; 42 acres of the former marsh went to McCarren Park in 1905; "the infill operation was '
    'completed by 1913". Bushwick Inlet is what remains. Ring = McCarren Park + 250 m and a corridor to the inlet.', WIKI + 'Bushwick_Inlet'))
R.save('bk')
