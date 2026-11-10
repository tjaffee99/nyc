"""Write data/tables/landmarks_lost.csv and data/research/landmarks_lost.md from the built
meshes (meshes.json, dumped from viewer/src/landmarks/nyc-lost.ts) and the research notes below."""
import csv, json, math
import numpy as np

ROOT = '/home/user/nyc/'
M = json.load(open(ROOT + 'data/interim/landmarks_lost/meshes.json'))
FT = 0.3048
WP = 'https://en.wikipedia.org/wiki/'
OHM = 'OpenHistoricalMap (CC0)'

def area(r):
    return abs(sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r)))) / 2

# id -> (confidence, cited height m or None, what the cited height is, cited plot area m2 or None, what it is,
#        site outline provenance, dimensions [(text, source)], estimated)
N = {}
def add(i, conf, h, hwhat, a, awhat, site, dims, est):
    N[i] = dict(conf=conf, h=h, hwhat=hwhat, a=a, awhat=awhat, site=site, dims=dims, est=est)

W_WTC = WP + 'World_Trade_Center_(1973%E2%80%932001)'
NIST = 'https://doi.org/10.6028/NIST.NCSTAR.1'
add('wtc_1_north_tower', 'HIGH', 1368 * FT, 'roof 1,368 ft', 63.398 ** 2 - 2 * 2.101 ** 2, 'tower plan 208 ft square less four bevelled corners (9 ft 9 in faces)',
    'centre = centroid of OHM way 198201501 = centroid of the 9/11 Memorial North Pool (Overture base_water), to 0.1 m; faces at 29.3° from the OHM outline; `replaces` is the tower square + 1 m',
    [('roof 1,368 ft (417 m); 110 storeys; construction 6 Aug 1968, topped out 23 Dec 1970', W_WTC),
     ('plan "approximately 208 ft" square', W_WTC),
     ('"The footprint of each tower was a square, about 210 ft on a side ..., with the corners of the tower beveled 9 ft 9 in. Internally, each floor was a square, about 206 ft on a side"; 59 columns on each face; roof of WTC 1 1,368 ft, 6 ft taller than WTC 2; antenna mast 360 ft', NIST + ' (sec. 1.2.2, read in the PDF)'),
     ('OHM draws the tower only 58.5 m square (3,393 m2): the cited 63.1 m was used', 'https://www.openhistoricalmap.org/way/198201501')],
    'lobby height 72 ft (six 12-ft storeys); levels of the four mechanical-floor bands (from the floor numbers 7-8, 41-42, 75-76, 108-110); every other window bay drawn')
add('wtc_2_south_tower', 'HIGH', 1362 * FT, 'roof 1,362 ft', 63.398 ** 2 - 2 * 2.101 ** 2, 'as 1 WTC',
    'centre = centroid of OHM way 198201503 = centroid of the Memorial South Pool; same orientation',
    [('roof 1,362 ft (415 m); construction Jan 1969, topped out 19 Jul 1971', W_WTC), ('plan as 1 WTC; 6 ft lower than WTC 1', NIST)],
    'as 1 WTC')
add('wtc_1_antenna', 'MEDIUM', 1730 * FT, 'tip 1,730 ft (roof 1,368 + mast 362 ft; infobox 1,728 ft)', None, '',
    'on 1 WTC', [('362 ft mast, added 1978-79 (in service late May - early June 1979), tip 1,730 ft', W_WTC), ('mast 360 ft', NIST)], 'mast widths and its base')
add('wtc_tobin_plaza', 'MEDIUM', None, '', 16 * 4046.86, 'superblock 16 acres',
    '`replaces` = convex hull of the OHM outlines of 1-6 WTC (so nothing from the street grid survives inside it from the 1966 clearance); paving and fountain from OHM relation 2965688',
    [('16-acre superblock; 5-acre plaza; Radio Row demolition from 21 Mar 1966; dedicated 4 Apr 1973', W_WTC), ('The Sphere (Fritz Koenig) in the fountain', WP + 'Austin_J._Tobin_Plaza')],
    'the Sphere is a plain globe; plaza drawn 0.4 m thick')
add('wtc_3_marriott', 'MEDIUM', 73.7, 'roof 73.7 m (242 ft)', None, '', 'OHM way 198590238 (2,925 m2)',
    [('roof 73.7 m, 22 storeys; Mar 1979 - 1 Jul 1981', WP + 'Marriott_World_Trade_Center')], 'none beyond the plain extrusion with storey bands')
add('wtc_4_1975', 'MEDIUM', 118 * FT, '118 ft', None, '', 'OHM way 198590237 (6,310 m2)',
    [('nine storeys, 118 ft (36 m); c. 1972-1975, opened Jan 1977', WP + '4_World_Trade_Center_(1975%E2%80%932001)')], 'plain extrusion')
add('wtc_5_1972', 'MEDIUM', 118 * FT, '118 ft', 120000 * 0.092903, 'average floor 120,000 sq ft',
    'OHM way 198590239 (L-shape, bounding box 125.8 x 95.7 m against the cited 420 x 330 ft = 128.0 x 100.6 m)',
    [('118 ft, nine storeys; 330 x 420 ft overall, 120,000 sq ft per floor; 1970-72', WP + '5_World_Trade_Center')], 'plain extrusion')
add('wtc_6_1973', 'MEDIUM', 110 * FT, '110 ft (complex infobox; OHM tags 28 m)', None, '', 'OHM way 198590240 (6,680 m2)',
    [('6 WTC: 110 ft, eight storeys, construction from 1969', W_WTC)], 'plain extrusion; completion 1973.5 from "1973"')
add('wtc_7_1987', 'MEDIUM', 610 * FT, '610 ft', 330 * 140 * 0.092903, '330 x 140 ft (rectangle; the plan was a trapezoid)',
    'OHM way 198590241 (trapezoid 95.2 x 42.3 m)',
    [('610 ft, 47 storeys, trapezoid 330 ft long and 140 ft wide; 2 Oct 1984 - Mar 1987', WP + '7_World_Trade_Center_(1987%E2%80%932001)')], 'plain extrusion')
W_PENN = WP + 'Pennsylvania_Station_(1910%E2%80%931963)'
add('penn_station_1910', 'MEDIUM', 153 * FT, 'maximum height 153 ft (waiting-room roof)', 788.75 * 430.5 * 0.092903, 'building 788.75 x 430.5 ft (1929 measurement)',
    '`replaces` = the two blocks between street lines: Overture centre lines of 7th/8th Av (273.5 m apart) less 100 ft, of 31st/33rd St (156.9 m apart) less 60 ft = 243.1 x 138.7 m; the building is centred in it (1.3 m and 3.7 m margins). OHM way 198645203 (Bromley land book) measures 237.1 x 132.7 m, 30,144 m2',
    [('788.75 x 430.5 ft (also 788 x 432 and 780 x 430); average height 69 ft, maximum 153 ft', W_PENN),
     ('General Waiting Room 314 ft 4 in x 108 ft 8 in x 150 ft; lunettes 38 ft 4 in radius', W_PENN),
     ('Concourse glass roof 210 x 340 ft; arcade 225 x 45 ft; carriageways 63 ft wide; side colonnades 230 ft; columns 35 ft x 4.5 ft; clock 61 ft above the sidewalk', W_PENN),
     ('men\'s and women\'s waiting rooms 100 x 58 ft; exit concourse 60 ft', W_PENN)],
    'order of the rooms along the axis is real, their exact east-west positions are not (the arcade is started 13 m inside the front); depth of the perimeter ranges (17 m); eaves of the waiting room (37.5 m) under the cited 153 ft ridge; concourse roof crown (27-29.5 m); number of columns drawn')
add('singer_building_1908', 'MEDIUM', 612 * FT, 'top of lantern 612 ft (flagpole to 674 ft)', None, '',
    'OHM way 198552870, traced from Sanborn 1905 vol. 1 (2,243 m2: 119 ft on Broadway, 231 ft on Liberty St). Tower placed from the cited setbacks: 30 ft behind Broadway and 10 ft clear of the City Investing Building on the north lot line',
    [('lantern top 612 ft; flagpole 62 ft above (674 ft); tower 65 x 65 ft, set back 30 ft from Broadway; 10 ft gap to the City Investing Building', WP + 'Singer_Building'),
     ('dome 50 ft covering the top three storeys; lantern 63.75 ft tall, 9 ft across at the base; balcony at the 36th floor cantilevered 8.5 ft; base buildings about 200 ft; five 12-ft bays per face', WP + 'Singer_Building')],
    'level of the 36th-floor balcony (144 m); curve of the mansard dome; mansard on the base')
add('city_investing_building_1908', 'LOW', 486 * FT, '486 ft above Broadway', (209 * 109 + 37.5 * 104) * 0.092903, 'from the cited frontages (209 x 109 ft block + 37.5 ft wide arm)',
    'OHM way 198552871 (1,735 m2) - about 30 % smaller than the cited frontages imply, and a plain hexagon without the light courts',
    [('486 ft above Broadway; 26-storey bulk + seven-storey gabled centre; 209 ft on Cortlandt, 109 ft on Church, 37.5 ft on Broadway, 313 ft deep', WP + 'City_Investing_Building')],
    'height of the bulk (103 m = 26/33 of the height); form and place of the gabled centre')
CARST = 'https://archive.org/details/newyorkcrystalp00carsa'
add('crystal_palace_1853', 'HIGH', 123 * FT, 'dome crown about 123 ft (springing 71 ft + 50 ft radius = 121 ft by the architects)', None, '',
    'centre and axes from OHM way 198109868: in the street-grid frame its octagon spans 111.0 m north-south (the cross), 45.5 m per arm, with entrance halls on three sides and a 14 x 137 m strip on the reservoir side; `replaces` = the west part of Reservoir Square (OHM relation 2696410)',
    [('naves 41 ft 5 in wide, 67 ft to the ridge; aisles 54 ft wide, two storeys, 50 ft; lean-tos 24 ft; eight octagonal towers 8 ft across, 71 ft high, flagstaffs 24 ft; dome 100 ft, springing 71 ft; entrance halls 27 ft deep with offices 27 x 18 ft; no entrance on the reservoir side', CARST + ' (Carstensen & Gildemeister 1854, "General description of the building")'),
     ('Greek cross, dome 100 ft', WP + 'New_York_Crystal_Palace'),
     ('dome 123 ft high (other figures: 148 ft with the lantern)', 'https://daytoninmanhattan.blogspot.com/2011/11/lost-1853-crystal-palace.html ("a dome rose 123 feet from the floor with a 100-foot diameter"; three entrances on 6th Avenue, 40th and 42nd streets - page read)'),
     ('cross 365 ft 5 in across - contemporary accounts, not found in the 1854 text; the OHM outline gives 364 ft', 'measured')],
    'height of the annex along the reservoir (10 m); the lantern; glass and iron colours')
add('latting_observatory_1853', 'LOW', 315 * FT, '315 ft', 75 * 75 * 0.092903, 'base 75 ft square',
    'NOT from a map: sources say only "north side of 42nd Street between Fifth and Sixth avenues", adjoining the palace. Placed on the palace\'s north-south axis, 13.5 m north of the 42nd Street line (Overture centre line + 50 ft). Could be 100 m off along the street',
    [('315 ft; base 75 ft square; octagonal, tapering to 6-8 ft; landings at 125, 225, 300 ft; opened 1 Jul 1853; top 75 ft removed 1855; burned 30 Aug 1856', WP + 'Latting_Observatory')],
    'position; height of the base building (9 m); drawn as a solid tapering octagon')
N['latting_observatory_1855'] = dict(N['latting_observatory_1853'], h=240 * FT, hwhat='315 - 75 = 240 ft')
add('croton_distributing_reservoir', 'HIGH', 50 * FT, 'walls 50 ft', 4 * 4046.86, '4 acres',
    'OHM relation 2689733: outer wall 137.0 x 115.1 m and the two basins',
    [('4 acres, 20 million gallons, walls 50 ft high and 25 ft thick, Egyptian style; 1839-1842; demolished 1899-1900', WP + 'Croton_Distributing_Reservoir')],
    'batter of the walls (2.4 m), corner pylons and entrance pavilion (2-3 m above the walls), water level')
add('madison_square_garden_1890', 'LOW', 304 * FT, 'tower 304 ft to the observation deck', 200 * 485 * 0.092903, 'cited 200 x 485 ft - longer than the block',
    'the block = footprint of the New York Life Building (city footprints BIN 1016880, 125.6 x 59.2 m = 412 x 194 ft); street lines give 127.8 x 60.2 m (Madison 80 ft, Fourth Av 100 ft, streets 60 ft)',
    [('200 x 485 ft; main hall 200 x 350 ft; opened 16 Jun 1890; Diana 18 ft, then 13 ft (1893)', WP + 'Madison_Square_Garden_(1890)'),
     ('tower "completed to the 304 ft high observation deck"', 'https://thearchitectureprofessor.com/2021/09/16/1-6-madison-square-garden/')],
    'all wall and roof heights (18-24.5 m); tower width (11.6 m), its stages and its exact place on the 26th Street side; cupolas; arcade')
add('madison_square_garden_1925', 'LOW', None, '', 200 * 375 * 0.092903, 'arena 200 x 375 ft (the lot is longer)',
    'OHM way 198759004 (Bromley 1930): 147.3 x 61.0 m lot; the arena box is the cited 375 ft at the west end, the rest the Eighth Avenue entrance building',
    [('200 x 375 ft, three tiers, 18,496 seats; opened 15 Dec 1925; begun 9 Jan 1925', WP + 'Madison_Square_Garden_(1925)')],
    'all heights (walls 21 m, roof crown 26.5 m); the entrance building')
POLO = WP + 'Polo_Grounds'
add('polo_grounds_1911', 'LOW', None, '', None, '',
    'OHM way 198180427 (the horseshoe of stands) and way 198180426 (the field); `replaces` = the outer line of the stands closed across centre field',
    [('left 279 ft, right 258 ft, gaps 450 ft, clubhouse 483 ft, bleacher corners 425 ft; fire 14 Apr 1911; double deck carried round in 1923', POLO)],
    'home plate (on the horseshoe axis, 16 m from the backstop; the OHM field is 98 m wide where the foul lines imply ~115 m); which part had two decks before 1923; all heights (deck 19 m, roof 23 m, bleachers 6-10 m, clubhouse 17 m)')
N['polo_grounds_1923'] = dict(N['polo_grounds_1911'])
add('ebbets_field_1913', 'LOW', None, '', None, '',
    'OHM relation 2690259 = the block Bedford Av / Sullivan Pl / McKeever Pl / Montgomery St (matches the Overture street centre lines)',
    [('right 297 ft (301); left 419 ft and centre 508 ft in 1913, 356 and 406 ft after the added stands; opened 9 Apr 1913', WP + 'Ebbets_Field')],
    'home plate (right-field line parallel to Sullivan Place, 297 ft from the Bedford Avenue wall, 40 m from Sullivan Place: +-8 m); left-centre and right-centre distances; deck and roof heights (19 / 23 m); wall 38 ft; rotunda 23 m across')
add('yankee_stadium_1923', 'MEDIUM', 117 * FT, 'frieze "117 feet high" (one secondary source)', 8 * 4046.86, '8-acre site',
    'OHM relation 2690448: outer wall and field. Home plate set on the bisector of the mapped field 82 ft from the backstop; the cited foul lines (281 and 295 ft) then end within 5 m of the mapped stands, 490 ft reaches the bleacher wall',
    [('right 295 ft, deepest centre 490 ft, backstop 82 ft; 8-acre site; frieze 15 ft; begun 5 May 1922, opened 18 Apr 1923; rebuilt 30 Sep 1973 - 15 Apr 1976', WP + 'Yankee_Stadium_(1923)'),
     ('left field 281 ft (1923) - recalled, not in the article extract', ''),
     ('frieze 117 ft above the field', 'https://www.americanheritage.com/node/133629 ("a 15-foot copper frieze"; Mantle 1963 "smashing off the copper frieze, 117 feet high" - page read)')],
    'deck heights below the roof; the decks are drawn at their 1937 extent from the start')
N['yankee_stadium_1976'] = dict(N['yankee_stadium_1923'], h=None, hwhat='', conf='LOW', est='height of the rebuilt upper deck (drawn at the old roof line)')
add('shea_stadium_1964', 'LOW', None, '', None, '',
    'OHM relation 2691041: a circle 233 m across',
    [('341 ft down both lines (338 from 1978); opened 17 Apr 1964', WP + 'Shea_Stadium'), ('centre field 410 ft - recalled, not in the article extract', '')],
    'direction of centre field (60 deg, inferred from the OHM-mapped left-field bleachers, way 201437224) and home plate (50 m from the centre): +-10 deg; height of the stands (34 m); scoreboard')
add('fort_amsterdam', 'LOW', None, '', None, '',
    'OHM relation 2690942 (Castello Plan 1660 via mapwarper 4625): bastioned trace 5,730 m2 and parade; houses from ways 198590263-5',
    [('four sides with a bastion at each corner; barracks, church, director\'s house, warehouse; 1625 laid out; demolished 1790', WP + 'Fort_Amsterdam')],
    'rampart height (4.5 m) and parapet; heights of the houses; gate; flagstaff')
add('fort_amsterdam_church_1642', 'MEDIUM', 16 * FT, 'walls 16 ft above the ground (1642 contract)', 72 * 52 * 0.092903, '72 x 52 ft (1642 contract)',
    'position and axis of OHM way 198590262 (which draws it 20.1 x 9.9 m, 199 m2); footprint from the contract',
    [('72 ft long, 52 ft broad (50 in an older translation, per a web search), 16 ft high above the ground, 2,500 guilders', 'https://encyclopedia.nahc-mapping.org/document/contract-john-and-richard-ogden-stamford-connecticut-build-stone-church-fort-amsterdam (New York State Archives calendar entry, contract of 1 May 1642 - page read)')],
    'twin gabled roofs (5 m) and turret, from the Castello Plan drawing; burned 18 Mar 1741 (recalled)')
add('stadt_huys_1642', 'LOW', None, '', 42 * 52 * 0.092903, 'foundations about 42 x 52 ft',
    'position and axis of OHM way 198590337 (Castello Plan; drawn 11.8 x 6.5 m)',
    [('1979-80 excavation found foundations of about 42 x 52 ft; five storeys', 'https://www.waymarking.com/waymarks/WM31V1_Unearthing_Gotham_Stadt_Huys (single popular source - page read: "five stories", "foundations, only 42 feet by 52 feet", tavern 1642, city hall 1653-1699)'),
     ('city hall 1653-1697', WP + 'Stadt_Huys_Site')],
    'which side lay along Pearl Street; eaves 10 m, ridge 17 m, stepped gables, cupola')
add('wall_street_palisade_1653', 'MEDIUM', 9 * FT, '9 ft', None, '',
    'OHM ways 198538378 (Broadway - East River) and 198538377 (Broadway - Hudson): 713 m including the bastions against the cited 2,340 ft = 713.2 m',
    [('2,340 ft long, 15 ft planks, 9 ft tall; ditch; 1653; stone bastions Hollandia and Zeelandia; demolished 1699', WP + 'Wall_Street')],
    'gates are symbolic posts; the bastions are those of the later plans OHM traced, shown from 1653')
add('trinity_church_1698', 'MEDIUM', 180 * FT, 'spire 180 ft', 153 * 73 * 0.092903, '153 x 73 ft',
    'OHM way 198588234 (mapwarper 49065): 52.6 x 24.7 m, 1,017 m2',
    [('body 105 ft, chancel 16 ft, steeple 32 ft square: 153 ft in all; breadth 73 ft; spire 180 ft (as enlarged 1737)', 'https://geographicguide.com/united-states/nyc/antique/trinity-church/first-temple.htm (as reported by a web search; the page could not be opened from this machine: expired TLS certificate)'),
     ('built 1698, burned 21 Sep 1776; steeple toward the Hudson', WP + 'Trinity_Church_(Manhattan)')],
    'eaves (11 m), ridge (17 m), masonry tower height (27 m); shown as enlarged from 1698')
add('trinity_church_1790', 'MEDIUM', 200 * FT, '200 ft', None, '',
    'OHM way 198782077: 42.0 x 20.6 m',
    [('200 ft tall, facing Wall Street, longer and wider than the first; consecrated 1790; demolished 1839', WP + 'Trinity_Church_(Manhattan)')],
    'eaves, ridge, tower width and masonry height')
add('city_hall_wall_street_1703', 'LOW', None, '', None, '', 'OHM way 198588178 (mapwarper 49065): 27.4 x 15 m',
    [('built 1699-1703; stone from the wall\'s bastions', WP + 'Federal_Hall')], 'all heights (eaves 9.5 m, cupola)')
add('federal_hall_1789', 'LOW', None, '', None, '', 'as the 1703 City Hall (L\'Enfant\'s rear extension is not in the outline)',
    [('L\'Enfant 1788-89: arcade with four Tuscan columns under the balcony, four Doric columns, eagle pediment, third storey, hip roof and cupola; House chamber 60 x 60 ft; demolished 1812', WP + 'Federal_Hall')],
    'all heights (eaves 13 m, cupola to 27.5 m)')
add('government_house_1790', 'LOW', None, '', None, '', 'OHM way 198589844: 37.8 x 21.1 m',
    [('"elegant two-story brick building"; 1790; demolished 1815', WP + 'Government_House_(New_York_City)')], 'all heights (eaves 11 m); portico')
add('the_tombs_1838', 'MEDIUM', None, '', (253 + 3 / 12) * (200 + 5 / 12) * 0.092903, '253 ft 3 in x 200 ft 5 in',
    'the cited rectangle set on the block: east side on the Centre Street line (Overture centre line less 40 ft), centred between Franklin and Leonard (centre lines 72.2 m apart). Today the block is Collect Pond Park (Overture land use: 5,012 m2)',
    [('253 ft 3 in x 200 ft 5 in, full block Centre / Franklin / Elm / Leonard; 1838; replaced 1902', WP + 'The_Tombs')],
    'all heights (walls 11 m, portico 14 m, prison block 14 m); courtyard layout')
add('bridewell_1775', 'LOW', None, '', None, '', 'OHM way 198751651 ("Map of City Hall Park"): 43.8 m long',
    [('1775; replaced by the Tombs 1838', WP + 'Bridewell_(New_York_City_jail)')], 'height (10.5 m) and roof')
add('almshouse_1797', 'LOW', None, '', None, '', 'OHM way 198751661 (LPC African Burial Ground and the Commons report): 78.5 x 18.2 m',
    [('Second Almshouse 1796-1830 (OHM tags; source: LPC African Burial Ground and the Commons Historic District designation report)', 'https://www.openhistoricalmap.org/way/198751661')], 'height (13 m); the year it came down (1857) is recalled, OHM ends it as an almshouse in 1830')
add('kings_college_hall_1760', 'LOW', None, '', 180 * 30 * 0.092903, '180 x 30 ft (usual description, not found online)',
    'OHM way 198103779 / relation 2697337: 57.3 x 10.0 m', [('King\'s College 1760-1776, Columbia College 1784-1857 on this site', 'https://www.openhistoricalmap.org/way/198103779')],
    'heights (eaves 11.5 m, cupola to 22 m); dates of the cornerstone and demolition are recalled')
add('park_theatre_1798', 'MEDIUM', None, '', 80 * 165 * 0.092903, '80 x 165 ft',
    'OHM way 198589840: 46.0 x 23.4 m', [('three storeys, 80 ft wide x 165 ft deep, plain dressed stone; opened Jan 1798; burned 16 Dec 1848', WP + 'Park_Theatre_(Manhattan)')],
    'height (15 m eaves)')
add('hippodrome_1905', 'LOW', None, '', None, '',
    'today\'s lot: city footprints BIN 1034202 (72.8 x 60.8 m = 239 x 199.5 ft); 43rd-44th Street centre lines 79.3 m apart less 60 ft = 61.0 m',
    [('5,300 seats; stage 100 x 200 ft; tank 60 ft across, 14 ft deep; 1905-1939', WP + 'New_York_Hippodrome')],
    'all heights (22-30 m), corner towers and globes (38.6 m)')
add('metropolitan_opera_house_1883', 'LOW', None, '', None, '', 'OHM way 198759005 (Bromley 1930): 86.6 x 58.7 m, 4,590 m2',
    [('whole block Broadway / Seventh Av / 39th / 40th; opened 22 Oct 1883; razed 1967', WP + 'Metropolitan_Opera_House_(39th_Street)')],
    'all heights (27 m, stage house 37 m)')
add('world_building_1890', 'MEDIUM', 310 * FT, 'dome 310 ft (pinnacle 350 ft, flat roof 191 ft)', 18496 * 0.092903, 'lot 18,496 sq ft with the annex',
    'OHM way 198589815 (mapwarper 41751), with the 1908 annex',
    [('flat roof 191 ft; dome 310 ft; pinnacle 350 ft; 115 ft on Park Row, 136 ft on Frankfort St; lot 18,496 sq ft with the annex', WP + 'New_York_World_Building')],
    'diameter and position of the dome (16.5 m, over the Park Row front); the annex is shown from 1890')
add('tribune_building_1875', 'MEDIUM', 260 * FT, 'tower 260 ft (roof 155 ft)', None, '', 'OHM way 198589816 (mapwarper 41751) - includes the later extensions (1,454 m2; the 1875 building was about 90 x 98 ft)',
    [('roof 155 ft; clock tower 260 ft incl. 16 ft pyramid roof and iron finial; tower 17 ft square, second bay of the Nassau Street front', WP + 'New_York_Tribune_Building')],
    'finial length (20 ft); outline is the enlarged one')
add('tribune_building_1905', 'MEDIUM', 335 * FT, 'finial 335 ft (roof 231 ft, tower 273 ft)', None, '', 'as above',
    [('nineteen storeys; flat roof 231 ft; clock tower 273 ft; finial 335 ft', WP + 'New_York_Tribune_Building')], 'none beyond the massing')
add('equitable_life_building_1870', 'LOW', 172 * FT, 'final height perhaps 172 ft (155 ft after 1885-87; 130-142 ft in 1870)', None, '',
    'OHM way 198592110 = the whole block, as after 1887',
    [('130-142 ft, seven storeys (1870); 155 ft, nine storeys (1885); final perhaps 172 ft; burned 9 Jan 1912', WP + 'Equitable_Life_Building_(Manhattan)')],
    'shown in the enlarged form from 1870 (the 1870 footprint is not mapped); the Broadway pavilion')
GCT = WP + 'History_of_Grand_Central_Terminal'
add('grand_central_depot_1871', 'LOW', 100 * FT, 'shed crown 100 ft (the mansard towers above it are estimated)', None, '',
    'cited dimensions set on street lines: Vanderbilt Av east line (Overture centre line + 30 ft), 42nd St north line (centre line + 50 ft); 695 ft reaches to 9 m short of the 45th Street line',
    [('train shed 530 x 200 ft, 100 ft at the crown; 695 ft along Vanderbilt Avenue; three-storey L-shaped head house; 1871', GCT)],
    '42nd Street frontage (249 ft, recalled); head-house height (17 m) and towers (30-36 m)')
N['grand_central_station_1900'] = dict(N['grand_central_depot_1871'], dims=[('head house raised from three to six storeys 1898-1900; old station demolished in stages to 1910', GCT)], est='six storeys = 30 m; domed towers (to 46 m)')
add('trylon_perisphere_1939', 'MEDIUM', 610 * FT, 'Trylon 610 ft (the sphere is drawn 54.86 m = 180 ft across)', None, '',
    'Perisphere centre = centroid of the Unisphere\'s pool (Overture base_water "Fountain of the Continents"); the Unisphere stands on the Perisphere\'s piling ring. Trylon: read off the 1939 newspaper map on Wikimedia Commons (south-east of the sphere, about 73 deg clockwise from the Constitution Mall axis, ~68 m)',
    [('Perisphere 180 ft; Trylon 610 ft; Helicline 950 ft', WP + 'Trylon_and_Perisphere'), ('Unisphere built on the Perisphere\'s foundation', WP + 'Unisphere'),
     ('relative position of the Trylon', 'https://commons.wikimedia.org/wiki/File:Worlds-fair-map.jpg')],
    'Trylon position (+-15 m) and base (19 m sides); sphere 2.5 m above its pool; Helicline course (drawn 230 m long instead of 290 m); bridge height 15 m')

def obb(pos):
    P = np.array(pos).reshape(-1, 3)
    return P[:, 2].max()

rows = []
for i, m in M.items():
    n = N[i]
    top = obb(m['pos'])
    site = sum(area(r) for r in m['replaces'])
    wp = next((s for s in m['sources'] if 'wikipedia' in s), m['sources'][0])
    if i == 'fort_amsterdam_church_1642': wp = m['sources'][0]
    note = f"construction from {m['built'][0]:g}; confidence {n['conf']}; " + ('height cited: ' + n['hwhat'] if n['h'] else 'height estimated') + '; ' + m['facts'].get('Model', '')
    hm = n['h'] if n['h'] else top
    rows.append([i, m['name'], m['kind'], f"{m['built'][1]:g}", f"{m['end']:g}", f"{m['anchor'][1]:.6f}", f"{m['anchor'][0]:.6f}", f"{hm:.1f}", wp, note])
with open(ROOT + 'data/tables/landmarks_lost.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['id', 'name', 'kind', 'start_year', 'end_year', 'lat', 'lon', 'height_m', 'year_source_url', 'notes']); w.writerows(rows)

L = []
L.append('# Lost landmarks — research notes\n')
L.append('Models: `viewer/src/landmarks/nyc-lost.ts` (47 landmark objects). Table: `data/tables/landmarks_lost.csv`.\n')
L.append('Every model stands on a real site: an outline traced in OpenHistoricalMap (OHM, CC0 — its tracings of the Castello Plan, Sanborn 1905, Bromley 1930 and the "Map of City Hall Park"), today\'s lot from the city footprints, or street lines from the Overture road centre lines (avenues 100 ft, cross streets 60 ft unless noted). Dimensions come from the Wikipedia articles (CC BY-SA; article URL given), the architects\' description of the Crystal Palace (public domain, archive.org), NIST NCSTAR 1 (US government) and a few web pages named below. Raw downloads: `data/raw/landmarks_lost/` (OHM Overpass extracts `ohm_named.json`, `ohm_more.json`, `ohm_pitch.json`; Wikipedia wikitext `wp/`; `cp_carstensen.txt`; `img/fairmap.jpg`).\n')
L.append('What "as reported by a web search" means: the figure was returned by a search summary and the page itself was not opened. "Recalled" means the figure is from memory and has no checked source — it is flagged in the model\'s facts or only used for a date.\n')
L.append('## Numeric checks\n')
L.append('Site = area of the `replaces` outline(s) in the model. Cited plot = area implied by the cited dimensions. Top = highest vertex of the mesh (flagpoles and finials included). Produced by `data/interim/landmarks_lost/make_docs.py` from the built meshes.\n')
L.append('| id | conf. | site m² | cited plot m² | Δ | mesh top m | cited height m | Δ m | cited height is |')
L.append('|---|---|---:|---:|---:|---:|---:|---:|---|')
for i, m in M.items():
    n = N[i]; top = obb(m['pos']); site = sum(area(r) for r in m['replaces'])
    d = f"{(site / n['a'] - 1) * 100:+.0f}%" if n['a'] and site else ''
    dh = f"{top - n['h']:+.1f}" if n['h'] else ''
    L.append(f"| {i} | {n['conf']} | {site:.0f} | {n['a']:.0f} | {d} | {top:.1f} | {n['h']:.1f} | {dh} | {n['hwhat']} |".replace('| 0 |', '| – |') if n['a'] and n['h'] else
             f"| {i} | {n['conf']} | {site:.0f} | {('%.0f' % n['a']) if n['a'] else '–'} | {d} | {top:.1f} | {('%.1f' % n['h']) if n['h'] else '– (estimated)'} | {dh} | {n['hwhat']} |")
L.append('')
L.append('Reading the table: where the mesh top exceeds the cited height the difference is a flagpole, finial, statue or lantern named in the model (Singer +18.9 m flagpole; World +12.2 m pinnacle to the cited 350 ft; Madison Square Garden +4 m Diana; Grand Central towers; the church turret; Trinity spires are the cited height itself). Site differences: the Twin Towers\' `replaces` is the plan + 1 m; Penn Station\'s is the block, 7 % larger than the building; 5 and 7 WTC are 19–24 % smaller in OHM than the cited floor plates; City Investing −30 % (LOW); MSG II −18 % because the cited 485 ft cannot fit the 412 ft block; Park Theatre −23 % and College Hall +14 % (OHM tracings against the usual descriptions); the Yankee Stadium outline is within 2 % of the cited 8 acres; the Wall measures 713 m against the cited 2,340 ft (713.2 m). Tops above a cited height that is not the top: the Croton reservoir\'s corner pylons (+3 m over the 50 ft walls, estimated), the fort church\'s roofs and turret over its 16 ft walls, the Wall\'s gate posts over the 9 ft palisade, the Latting and Twin Tower sites are the plan + 1 m, MSG III\'s site is the whole lot (the arena is the cited 375 ft of it), the Trylon and Perisphere\'s site is a 52 m circle round the sphere and a 16 m circle round the Trylon.\n')
L.append('## Street check\n')
L.append('`data/interim/landmarks_lost/street_check.py` intersects every site outline (shrunk 3 m) with today\'s 192,259 Overture street centre lines. Streets run inside only where history says they should: Fulton and Greenwich streets through the World Trade Center superblock and the sites of 4, 5, 6 and 7 WTC (reopened after 2001); State Street (58 m) and Battery Place (17 m) across the west bastions of Fort Amsterdam (laid out after 1790); the Park Row / Brooklyn Bridge approach (50–58 m) through the World Building (demolished for it in 1955); the Park Avenue viaduct (263 m) through Grand Central Depot. No other outline is crossed by a street: Penn Station, the Singer and City Investing buildings, the Equitable, the Opera House, the Hippodrome, both Gardens, the Tombs, the ballparks, the colonial buildings and the rest all sit inside present blocks.\n')
L.append('Other position checks: the Twin Tower centres equal the centroids of the 9/11 Memorial pools to 0.1 m; the Croton reservoir outline (OHM) and the New York Public Library footprint share a centroid to 1 m; the Tombs rectangle is centred 11 m from the centroid of Collect Pond Park; Yankee Stadium\'s cited foul lines (281 / 295 ft) end within 5 m of the mapped stands from the derived home plate.\n')
L.append('## Per landmark\n')
for i, m in M.items():
    n = N[i]
    L.append(f"### {m['name']} — `{i}` — {n['conf']}\n")
    L.append(f"- Years: construction {m['built'][0]:g}, complete {m['built'][1]:g}, gone {m['end']:g}. Anchor {m['anchor'][1]:.6f}, {m['anchor'][0]:.6f}.")
    L.append(f"- Site outline: {n['site']}.")
    for t, s in n['dims']:
        L.append(f"- Dimension: {t}" + (f" — {s}" if s else ''))
    L.append(f"- Estimated: {n['est']}.")
    L.append(f"- Sources in the model: {', '.join(m['sources'])}\n")
L.append('## Left out for lack of citable dimensions\n')
L.append('- Cornelius Vanderbilt II House (Fifth Avenue, 57th–58th Street, 1883/1893–1927): the article gives only "six stories" and "the entire block front"; no plan or height found; not in OHM.')
L.append('- Charles M. Schwab House (Riverside Drive, 73rd–74th Street, 1906–1948): "an entire city block", 75 rooms, 50,000 sq ft; sources disagree on the tower (100 ft / 166 ft); no plan of the house within its garden block; not in OHM.')
L.append('- Ziegfeld Theatre (1927–1966): OHM has the outline (way 198777204, 1,315 m², Bromley 1930) but no height or storey count was found.')
L.append('- Luna Park (1903–1944): no dimensioned plan was found (the article was only searched for tower heights); not in OHM.')
L.append('- Dreamland tower (1904–1911): cited 375 ft on a 50 × 50 ft base, but its position inside the park could not be fixed from a map; not in OHM.')
L.append('- The Equitable Life Building as first built (1870–1885): its smaller footprint is not mapped, so the one model shows the enlarged block-filling form from 1870.')
L.append('- Grand Central Depot\'s 1885 annex on the east side: no dimensions.')
L.append('\n## Not checked\n')
L.append('- Nothing was looked at in the running viewer (headless rendering does not work on this machine). The meshes were rendered to top and oblique views off-line (`data/interim/landmarks_lost/render.py`, sheets 1–5) for Penn Station, Singer, Crystal Palace, MSG II and III, the four ballparks, Grand Central Depot, Trylon and Perisphere, Fort Amsterdam, Federal Hall, 1 WTC, the World and Tribune buildings, the Tombs, the Hippodrome, the Croton reservoir and the Stadt Huys; the others were checked only numerically.')
L.append('- loc.gov (HABS/HAER) answered 403 to this machine and the Overpass mirrors of OpenStreetMap were unreachable, so no HABS data pages and no OSM home-plate markers were used.')
L.append('- Ground elevation: every model is drawn on a flat base at its anchor; sloping sites (Ebbets Field, Polo Grounds under Coogan\'s Bluff, the City Investing Building) are not terraced.')
open(ROOT + 'data/research/landmarks_lost.md', 'w').write('\n'.join(L) + '\n')
print('rows', len(rows), 'missing notes', [i for i in M if i not in N])
