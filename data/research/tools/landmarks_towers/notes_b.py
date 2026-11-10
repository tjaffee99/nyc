"""Hand-written research notes per landmark (part B)."""
from notes_a import N, WP, LPC

N['one_vanderbilt'] = dict(
    h=427.0, url=WP + 'One_Vanderbilt',
    csv='groundbreaking 18 Oct 2016, opened 14 Sep 2020; spire 1,401 ft, roof 1,301 ft',
    est='spire width; the faces are stepped where the real ones taper',
    src=[WP + 'One_Vanderbilt', 'city footprint BIN 1090825', 'OSM parts'],
    cited=['roof 1,301 ft (396.5 m), spire 1,401 ft (427.0 m), 62 floors numbered to 73 — Wikipedia', '"the tower tapers as it rises, with several pavilions and a pinnacle at the top" — Wikipedia', 'groundbreaking 18 Oct 2016; opened 14 Sep 2020 — Wikipedia'],
    measured=['base from the official footprint (65.7 × 61 m, 4,001 m²)', 'OSM part tops 75, 315, 330, 350, 397 m with their outlines (the four interlocking volumes)'],
    estimated=['the model steps where the building tapers: between 75 and 315 m the plan is constant', 'spire radius 1.6 → 0.25 m, placed on the centre of the top OSM part'],
)

N['central_park_tower'] = dict(
    h=472.4, url=WP + 'Central_Park_Tower',
    csv='excavation May 2014, topped out 17 Sep 2019, completed 2020; 1,550 ft',
    est='completion month (end of 2020)',
    src=[WP + 'Central_Park_Tower', 'city footprint BIN 1090180', 'OSM parts'],
    cited=['architectural 1,550 ft (472.4 m), 98 floors — Wikipedia infobox', 'a cantilever "extending 28 ft from the eastern side of the tower", starting "roughly 290 ft" up over the Art Students League — Wikipedia (OSM: 8.3 m from 89 m)', 'excavation May 2014; topped out 17 Sep 2019; completed 2020 — Wikipedia'],
    measured=['base: the official outline without the cantilever\'s shadow (3,679 m²), 23 m and 44 m (OSM part tops)', 'tower outlines and levels 89, 127, 163, 237, 332, 342, 433, 466, 472 m — OSM parts'],
    estimated=['`built` ends at 2020.9 (only the year is cited)', '`replaces` is cut back around the 85 m neighbour in the south-west notch (BIN 1024901) and excludes the cantilever\'s shadow', 'plan check by projection (cantilever)'],
)

N['steinway_hall'] = dict(
    h=67.0, url=WP + '111_West_57th_Street',
    csv='built 1924-25 (LPC), opened 27 Oct 1925 (Wikipedia infobox); 16 storeys; height 67 m from OpenStreetMap',
    est='split of the lot between the wings, storey 4.2 m, tower size',
    src=[LPC + '2100.pdf (LP-2100, 2001)', WP + '111_West_57th_Street', 'city footprint BIN 1023728', 'OSM / Overture building "Steinway Hall" (67 m)'],
    cited=[
        'sixteen storeys, built 1924–25; "L-shaped in plan, with a front portion clad in Indiana limestone that terminates in a set back, four-story colonnaded tower"; the 58th Street portion "has setbacks above the ninth and twelfth stories" — LPC',
        'completed 27 Oct 1925 — Wikipedia infobox',
    ],
    measured=['height 67 m — OSM/Overture building (no cited height found)', 'the official footprint (1,855 m², 30.4 × 61.1 m) is the whole lot including the 2022 tower'],
    estimated=['which part of the lot each wing covers (57th St front on the west 13 m; 58th St portion across the lot north of the tower)', 'storey height 4.2 m (67 m / 16); tower plan'],
)

N['west_57th_111'] = dict(
    h=435.3, url=WP + '111_West_57th_Street',
    csv='construction began 2014 (Wikipedia), topped out Oct 2019, completed 2021 (CTBUH; Wikipedia infobox 2022); 1,428 ft',
    est='months within 2014 and 2021',
    src=[WP + '111_West_57th_Street', 'OSM parts'],
    cited=['architectural 1,428 ft (435.3 m), 84 floors — Wikipedia infobox', '"The tower\'s northern elevation rises directly up to the pinnacle, and the southern elevation contains several setbacks" — Wikipedia', 'construction on the tower began in 2014; topped out October 2019; completed 2022 — Wikipedia'],
    measured=['tower 18.2 m wide (OSM; the 60 ft of the brief), 25 m deep at the base of the shaft; thirteen set-backs of the south face between 200 and 417 m, top 435 m — OSM parts', '30 m base on 57th St — OSM part'],
    estimated=['none in the geometry; rides on the Steinway Hall footprint (same lot, no `replaces` of its own)'],
)

N['hudson_yards_30'] = dict(
    h=387.1, url=WP + '30_Hudson_Yards',
    csv='start 2014 (CTBUH; the ceremony of 4 Dec 2012 was for the yards), opened 15 Mar 2019; 1,270 ft',
    est='height of the Shops (45 m); month of the 2014 start',
    src=[WP + '30_Hudson_Yards', 'city footprint BIN 1088961', 'OSM parts'],
    cited=['1,270 ft (387.1 m), 73 floors; groundbreaking ceremony 4 Dec 2012; opened 15 Mar 2019 — Wikipedia', 'the Edge: a triangular deck "jutting out from the 100th floor", at 1,100 ft (335 m), opened March 2020 — Wikipedia'],
    measured=['the official footprint (17,990 m²) is the tower and the Shops in one polygon recorded at 385.6 m', 'tower outlines and levels 10, 130, 140, 310, 335–340 (the deck), 387 m — OSM parts, clipped to the official outline'],
    estimated=['the Shops are extruded on the official outline to 45 m: no measured height was found (Overture lists 67 m with "4 floors", which is not credible)', 'the Edge is drawn from its start though it opened a year after the tower'],
)

N['hudson_yards_10'] = dict(
    h=267.6, url=WP + '10_Hudson_Yards',
    csv='groundbreaking 4 Dec 2012, completed 31 May 2016; roof 878 ft',
    est='none',
    src=[WP + '10_Hudson_Yards', 'city footprint BIN 1089323', 'OSM parts'],
    cited=['roof 878 ft (267.6 m), 52 floors; groundbreaking 4 Dec 2012; completed 31 May 2016 — Wikipedia infobox', 'the south facade cantilevers over the High Line spur — Wikipedia'],
    measured=['base from the official footprint (4,103 m²; the city records only 45.4 m for it)', 'levels 105, 120, 165, 240, 273 m — OSM parts; the top is drawn at the cited 267.6 m'],
    estimated=['nothing; the sloped roof is drawn flat'],
)

N['vessel'] = dict(
    h=45.7, url=WP + 'Vessel_(structure)',
    csv='groundbreaking Apr 2017, topped out Dec 2017, opened 15 Mar 2019; 150 ft',
    est='base width 15 m (from memory), shell thickness; stairs not modelled',
    src=[WP + 'Vessel_(structure)', 'city footprints BIN 1090391 and 1090967'],
    cited=['150 ft (45.7 m), 16 storeys, 154 flights, 80 landings; groundbreaking April 2017, topped out December 2017, opened 15 Mar 2019 — Wikipedia'],
    measured=['top 46 m across — the official footprint (1,595 m²)'],
    estimated=['base width 15 m (50 ft): from memory of the designer\'s published figure, not re-verified', 'two concentric copper shells and eight landing rings stand for the lattice of stairs', 'plan check by projection (the structure widens upward)'],
)

N['bank_of_america_tower'] = dict(
    h=365.8, url=WP + 'Bank_of_America_Tower_(Manhattan)',
    csv='groundbreaking 2 Aug 2004, completed 1 May 2009; spire 1,200 ft, roof 945 ft',
    est='crown facets stretched from OSM 279 m to the cited 288 m; spire widths',
    src=[WP + 'Bank_of_America_Tower_(Manhattan)', 'city footprint BIN 1087268', 'OSM parts'],
    cited=['"an architectural spire at its south end, rising 1200 ft; the roof height at that location is 945 ft" (365.8 m, 288.0 m); 55 floors — Wikipedia', 'groundbreaking 2 Aug 2004; completed 1 May 2009 — Wikipedia'],
    measured=['base from the official footprint (7,858 m², with the Stephen Sondheim Theatre)', 'podium 15 / 30 m, shaft to 236 m, crown facets 240–279 m — OSM parts'],
    estimated=['the crown levels above 236 m are stretched by 1.21 so that OSM\'s 279 m top meets the cited 288 m roof', 'spire radius 2.6 → 0.25 m from 245 m'],
)

N['new_york_times_building'] = dict(
    h=318.8, url=WP + 'The_New_York_Times_Building',
    csv='work began late 2004, opened 19 Nov 2007; mast 1,046 ft, roof 748 ft, screens 840 ft',
    est='mast width; screens on the faces longer than 18 m',
    src=[WP + 'The_New_York_Times_Building', 'city footprint BIN 1087186', 'OSM parts'],
    cited=['"rises 748 ft from the street to its roof, while the exterior curtain wall rises to 840 ft and its mast rises to 1046 ft" (228.0, 256.0, 318.8 m); 52 floors — Wikipedia', 'work began late 2004; opened 19 Nov 2007 — Wikipedia'],
    measured=['podium from the official footprint (6,583 m²), 25 m; cruciform tower to 227 m, core to 232 m — OSM parts, clipped to the official outline'],
    estimated=['mast radius 1.3 → 0.2 m'],
)

N['spruce_8'] = dict(
    h=265.2, url=WP + '8_Spruce',
    csv='construction 2006, opened Feb 2011 (Wikipedia; CTBUH completed 2011); 870 ft',
    est='month of the 2006 start',
    src=[WP + '8_Spruce', 'city footprint BIN 1087485', 'OSM parts'],
    cited=['roof 870 ft (265.2 m), 76 floors; construction start 2006, completion 2010; opened February 2011 — Wikipedia'],
    measured=['podium from the official footprint (2,880 m²), 26 m; set-backs at 29, 32, 37, 90, 140, 180 m — OSM parts; top drawn at the cited 265.2 m (OSM 272, city 262.4)'],
    estimated=['the rippling steel skin is not modelled'],
)

N['hearst_magazine_building'] = dict(
    h=30.0, url=WP + 'Hearst_Tower_(Manhattan)',
    csv='six-storey base: excavation by Jun 1927, completed 1928; height 30 m from OpenStreetMap',
    est='completion within 1928',
    src=[WP + 'Hearst_Tower_(Manhattan)', LPC + '1625.pdf (LP-1625, 1988)', 'city footprint BIN 1025451', 'OSM parts'],
    cited=['six-storey base built 1927–28 "of an office tower that was never constructed" — LPC', 'excavation had begun by June 1927 — Wikipedia'],
    measured=['official footprint 3,521 m² (59 × 60.5 m); 30 m high — OSM part'],
    estimated=['none in the geometry (a plain extrusion; the corner pylons are not modelled)'],
)

N['hearst_tower'] = dict(
    h=182.0, url=WP + 'Hearst_Tower_(Manhattan)',
    csv='work began 30 Apr 2003, completed 2006; 597 ft',
    est='diagrid start level (eight tiers measured down from the roof), clerestory zone',
    src=[WP + 'Hearst_Tower_(Manhattan)', 'OSM parts'],
    cited=[
        'roof 597 ft (182.0 m), 46 floors — Wikipedia infobox',
        '"Each of the upper stories has a footprint of 160 by 120 ft, with the longer dimension extending from east to west" — Wikipedia (OSM: 51.1 × 39.3 m)',
        '"The diagrid divides the tower\'s sides horizontally into eight tiers, each measuring four stories high"; "the diagonal beams are typically 57 ft long by 40 ft wide"; "The setbacks above the sixth floor contain a skylight 40 ft wide" — Wikipedia',
        'work began 30 Apr 2003; completed 2006 — Wikipedia',
    ],
    measured=['rides on the Hearst Magazine Building footprint'],
    estimated=['tier height 16.27 m from the 57 ft diagonal on a 40 ft base; the eight tiers are measured down from the roof, so the diagrid starts at 51.8 m with a glazed zone below', 'tower centred on the base; the chamfered "bird\'s-mouth" corners are not modelled'],
)

N['leonard_56'] = dict(
    h=250.2, url=WP + '56_Leonard_Street',
    csv='foundations 2008, construction resumed Oct 2012, completed 2016 (CTBUH; Wikipedia infobox 2017); roof 821 ft',
    est='schematic: base zone height, shaft plan, cantilevered slabs',
    src=[WP + '56_Leonard_Street', 'city footprint BIN 1088646'],
    cited=['roof 821 ft (250.2 m), 60 floors, 500,005 sq ft — Wikipedia infobox', 'foundation work 2008, shut down; construction resumed October 2012; completed 2017 — Wikipedia'],
    measured=['official footprint 1,418 m² (the city records only 77.7 m for it); no OSM parts'],
    estimated=['schematic model: a 30 m base zone on the official outline, a 31 × 25 m shaft (775 m² = floor area / floors) and pseudo-random slabs for the cantilevered floors'],
)

N['un_secretariat'] = dict(
    h=153.9, url=WP + 'United_Nations_Secretariat_Building',
    csv='groundbreaking 14 Sep 1948, completed June 1951; 505 ft',
    est='heights of the four mechanical bands',
    src=[WP + 'United_Nations_Secretariat_Building', 'city footprint BIN 1083875'],
    cited=['roof 505 ft (153.9 m), 39 floors; slab 72 × 287 ft; glass curtain walls west and east, marble north and south; mechanical storeys faced with latticed panels — Wikipedia', 'groundbreaking 14 Sep 1948; completed June 1951 — Wikipedia'],
    measured=['official footprint 21.0 × 86.1 m (1,805 m²); city roof 156.3 m'],
    estimated=['the mechanical bands are drawn at 21, 60, 107 and 149 m (6th, 16th, 28th, 39th floors from memory, at 3.9 m a storey)'],
)

N['un_general_assembly'] = dict(
    h=32.0, url=WP + 'United_Nations_General_Assembly_Building',
    csv='steelwork Feb 1950, dedicated 10 Oct 1952; heights from OpenStreetMap parts (dome 32 m)',
    est='terrace height (1.2 m), flat roofs, dome springing',
    src=[WP + 'United_Nations_General_Assembly_Building', 'city footprint BIN 1083872', 'OSM parts'],
    cited=['four-storey building about 380 × 160 ft with concave west and east walls and a dome; Assembly Hall 75 ft tall — Wikipedia', 'steelwork from February 1950; dedicated 10 Oct 1952 — Wikipedia'],
    measured=['the official footprint (18,841 m², recorded at 21.6 m) covers the General Assembly and Conference buildings and the terraces between and north of them', 'General Assembly 25 m with a 34 m dome to 32 m, Conference Building 20–23 m — OSM parts'],
    estimated=['terraces outside the OSM parts drawn 1.2 m high', 'flat roofs (the Assembly roof really sweeps up to the north); dome drawn from 22 m', 'the Conference Building is drawn from 1950 too (same footprint)'],
)

N['lever_house'] = dict(
    h=93.6, url=WP + 'Lever_House',
    csv='built 1950-1952, opened 29 Apr 1952; 307 ft',
    est='storey heights of the raised slab, column grid',
    src=[WP + 'Lever_House', LPC + '1277.pdf (LP-1277, 1982)', 'city footprint BIN 1035732', 'OSM parts'],
    cited=['307 ft (93.6 m), 21 floors (LPC: 24-storey); built 1950–52; opened 29 Apr 1952 — Wikipedia', '"a vertical slab rising above a horizontal base"; "open colonnaded space … with a planted courtyard open to the sky" — LPC'],
    measured=['lot from the official footprint (2,835 m²), whose interior ring is the garden court, 20.4 × 18.2 m (372 m²)', 'tower slab 51 × 16.8 m from 15 m — OSM part'],
    estimated=['raised slab between 5.2 and 10.4 m, recessed third storey to 15 m', 'columns on an 8.8 m grid', 'plan check by projection (the base stands on columns)'],
)

N['seagram_building'] = dict(
    h=157.0, url=WP + 'Seagram_Building',
    csv='demolition Sep 1955, steel from May 1956, opened 22 May 1958; 515 ft (CTBUH 156.97 m; Wikipedia infobox 516 ft)',
    est='none',
    src=[WP + 'Seagram_Building', LPC + '1664.pdf (LP-1664, 1989)', 'city footprint BIN 1036465', 'OSM parts'],
    cited=['roof 516 ft, 38 floors — Wikipedia infobox; the model uses CTBUH\'s 156.97 m (515 ft, the brief\'s figure)', '"backed by a ten-story bustle, full-height spine, and five-story wings" — LPC', 'demolition from September 1955, superstructure from May 1956; opened 22 May 1958 — Wikipedia'],
    measured=['plan from the official footprint (2,892 m²; the plaza is not part of it)', 'wings 20 m, bustle 40 m, slab with its spine (34.7 × 43 m) — OSM parts; top drawn at the cited 157.0 m (OSM 162, city 161.9 m)'],
    estimated=['nothing but the colour'],
)

N['metlife_building'] = dict(
    h=246.3, url=WP + 'MetLife_Building',
    csv='substructure from May 1960, topped out 9 May 1962, opened 7 Mar 1963; 808 ft',
    est='none',
    src=[WP + 'MetLife_Building', 'city footprint BIN 1085630', 'OSM parts'],
    cited=['roof 808 ft (246.3 m), 59 floors; an elongated octagon on a nine-storey base — Wikipedia', 'substructure from May 1960; topped out 9 May 1962; opened 7 Mar 1963 — Wikipedia'],
    measured=['base from the official footprint (10,016 m²; the city records only 47.9 m for it)', 'base 30 and 38 m, octagonal tower 90.8 × 42.4 m — OSM parts'],
    estimated=['nothing but the colour'],
)

N['municipal_building'] = dict(
    h=176.8, url=WP + 'Manhattan_Municipal_Building',
    csv='work started 17 Jul 1909, completed 1914; 580 ft with the statue',
    est='statue form; completion taken as mid-1914; arch not cut out',
    src=[WP + 'Manhattan_Municipal_Building', LPC + '0079.pdf (LP-0079, 1966)', 'city footprint BIN 1001394', 'OSM parts'],
    cited=['"The tower rises to around 560 ft above ground level; including the Civic Fame statue, the building stands at around 580 ft" (176.8 m); statue 25 ft; 40 storeys — Wikipedia', '"rising to a height of 25 stories with a tower above" — LPC', 'work officially started 17 Jul 1909 and continued through 1914 — Wikipedia'],
    measured=['plan from the official footprint (4,335 m²) to 107 m; tiers 107–113, 113–123, 123–135, 135–149, 149–165, 165–177 m — OSM parts'],
    estimated=['the top tier ends at the 170.7 m roof (CTBUH) and the statue is drawn as a gilded shaft above it to the cited 176.8 m', 'the vaulted passage of Chambers Street through the base is not cut out'],
)

N['park_row_building'] = dict(
    h=119.2, url=WP + 'Park_Row_Building',
    csv='built 1896-1899; 391 ft',
    est='cupola size and position; months within 1896 and 1899',
    src=[WP + 'Park_Row_Building', LPC + '2024.pdf (LP-2024, 1999)', 'city footprint BIN 1001249'],
    cited=['391 ft (119.2 m); "26 full floors, a partial 27th floor, and a pair of four-story cupolas"; built 1896–99 — Wikipedia', '"Each tower is comprised of three fully visible stories, with a fourth story located in the large dome" — LPC'],
    measured=['official footprint 1,246 m² (with its light courts); city roof 118.9 m; no OSM parts'],
    estimated=['cupolas 8.6 m across on the two front wings, rising from the 102.1 m main roof (CTBUH roof height), domes from 113.5 m', '`built` 1896.8–1899.55: only the years are cited'],
)

N['new_york_life_building'] = dict(
    h=187.5, url=WP + 'New_York_Life_Building',
    csv='start 1926 (CTBUH), foundations from Aug 1925, built 1927-1928 (LPC); 615 ft',
    est='finial; months within 1926-28',
    src=[WP + 'New_York_Life_Building', LPC + '2067.pdf (LP-2067, 2000)', 'city footprint BIN 1016880', 'OSM parts'],
    cited=['615 ft (187.5 m) — Wikipedia', '"The octagonal pyramidal roof at the top is 88 ft tall and includes the 35th through 40th stories" — Wikipedia (→ 160.7 m); 34 storeys plus the six-storey crown, constructed 1927–28 — LPC', 'foundation work from August 1925 — Wikipedia'],
    measured=['plan from the official footprint (7,427 m²); set-backs at 22, 60, 115, 148 m and the octagon (24 m across) — OSM parts'],
    estimated=['pyramid drawn to a 2.4 m finial base at 184.5 m'],
)

N['williamsburgh_savings_bank_tower'] = dict(
    h=156.0, url=WP + 'Williamsburgh_Savings_Bank_Tower',
    csv='start 1927 (CTBUH), cornerstone 9 Apr 1928, topped out Jul 1928, opened 1 Apr 1929; 512 ft',
    est='dome proportions; month of the 1927 start',
    src=[WP + 'Williamsburgh_Savings_Bank_Tower', LPC + '0971.pdf (LP-0971, 1977)', 'city footprint BIN 3059183', 'OSM parts'],
    cited=['roof 512 ft (156 m), 41 floors — Wikipedia; LPC: "Soaring 512 feet"', '"The centers of the clock faces are 430 ft high, and the faces measure 27 ft across" — Wikipedia', 'cornerstone 9 Apr 1928; topped out by the end of July 1928; opened 1 Apr 1929 — Wikipedia'],
    measured=['plan from the official footprint (1,649 m²); set-backs at 10, 24, 60, 69, 80, 85, 110, 115, 140, 145 m — OSM parts'],
    estimated=['`built` starts at 1927.5: CTBUH gives the year only', 'dome radius 5.4 m, rise 8 m from 145 m (CTBUH: highest occupied floor 145.39 m)'],
)

N['one_court_square'] = dict(
    h=205.1, url=WP + 'One_Court_Square',
    csv='construction began by 1987; completed 1990 (CTBUH and the brief; Wikipedia: completed and opened 1989); roof 673 ft',
    est='months within 1987 and 1990',
    src=[WP + 'One_Court_Square', 'city footprint BIN 4307108', 'OSM parts'],
    cited=['roof 673 ft (205.1 m), 50 floors; construction began by 1987; completed and opened 1989 — Wikipedia (the brief gives 1990)'],
    measured=['plan from the official footprint (2,418 m²) to 170 m; stepped top 170–200 m — OSM parts; the top is raised to the cited 205.1 m (OSM 200, city 192.9 m)'],
    estimated=['nothing but the colour'],
)
