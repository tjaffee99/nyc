"""Scratch: write data/research/landmarks_civic.md and data/tables/landmarks_civic.csv from the built meshes, the check summary and the notes below."""
import json, csv, math
L = json.load(open('/home/user/nyc/data/interim/landmarks_civic/meshes.json'))
S = json.load(open('/home/user/nyc/data/interim/landmarks_civic/check_summary.json'))
# id (or id prefix) -> (cited dimensions used, measured data used, estimated)
N = {
 'statue_of_liberty': ("Wikipedia physical-characteristics table (= NPS statue statistics), read in the wikitext [V]: copper statue 151 ft 1 in (46.05 m); ground to torch 305 ft 1 in (92.99 m); heel to top of head 111 ft 1 in; head chin to cranium 17 ft 3 in; right arm 42 ft long, 12 ft thick; waist 35 ft; tablet 2 ft thick; pedestal 89 ft; foundation 65 ft. Article text [V]: pedestal a truncated pyramid 62 ft square at the base, 39.4 ft at the top; foundation begun 1883. From the NPS table, not re-read [M]: head 10 ft ear to ear, tablet 23 ft 7 in x 13 ft 7 in, rays up to 9 ft.",
   "Star of Fort Wood: city footprint BIN 1000002 (5,588 m2). OSM 3D parts: pedestal square centred (-2.5, 0.4) m from the anchor, faces bearing 146.7/56.7 deg; fort terreplein 10 m, upper terrace 39.6 x 40.2 m at 10-14 m, foundation 25 m square.",
   "Taper of the pedestal between its cited base and top, the loggia panels, the pose of the figure (body rings, arm angles, tablet position, fan of the seven rays), flame shape. Fort wall height is OSM's 10 m, not a cited figure."),
 'ellis_island': ("Wikipedia 'Ellis Island', main building section [V]: three storeys; registry room 200 x 100 ft with a 56 ft ceiling; four corner towers with copper cupolas; railroad ticket office annex 1905-06; third storey of the wings early 1910s. Dates [M]: opened December 17, 1900; first station burned June 15, 1897.",
   "City footprint BIN 1085964 merges every connected building of Island 1 (17,234 m2 with courts): main block 118.4 x 50.6 m measured from it, roof 26.5 m.",
   "Tower height (40.5 m to the finials), wing and centre wall heights, arches; the other Island 1 buildings are plain 12 m blocks (heights not researched)."),
 'grand_central': ("Wikipedia 'Grand Central Terminal' [V]: Main Concourse 275 x 120 x 125 ft; station 'about 125 ft tall'; clock 13 ft; Glory of Commerce 48 ft; three 60 x 30 ft arched windows between ten Doric columns. Dates [M]: construction 1903-1913, opened February 2, 1913.",
   "City footprint BIN 1035381 (7,784 m2), roof 45.8 m (taken as the top of the sculpture group).",
   "Cornice level 27 m, window sill levels, massing of the sculpture group, position of the concourse within the block."),
 'park_avenue_viaduct': ("Wikipedia 'Park Avenue Viaduct' [V]: 600 ft from 40th to 42nd Street; deck 60 ft wide; girders 136 ft; western leg 35 ft, eastern leg 33 ft (53 ft north of 44th), 40 ft across the 42nd Street front; western leg built 1917-1919, eastern leg completed 1928.",
   "Alignment: OSM road centrelines (Overture roads_region 'Park Avenue', bridge flags). City footprint BIN 1085730 (564 m2, the building under the Pershing Square spans) is replaced.",
   "Deck level 8 m; three equal spans between 41st Street and the terminal; the solid base is drawn 14-15 m wide (roadway plus sidewalks) to meet the terminal wall."),
 'new_york_public_library': ("Wikipedia 'New York Public Library Main Branch' [V]: 390 ft north-south by 270 ft; Main Reading Room 78 x 297 ft, 52 ft high; courts 80 x 80 ft; six 11 ft attic figures. Dates [M]: cornerstone November 1902, opened May 23, 1911.",
   "City footprint BIN 1034194 (9,788 m2; its recorded year, 1940, is wrong), roof 38.2 m. OSM 3D parts: main roof 22 m, rear range and centre pavilion 35 m (the model tops out at OSM's 35 m, 3.2 m under the city-measured figure).",
   "Portico: column, entablature and attic levels; end-pavilion pediments."),
 'st_patricks': ("Wikipedia 'St. Patrick's Cathedral (Midtown Manhattan)' [V]: 332 ft long (396.7 ft with the Lady Chapel); 174 ft at the transepts (the footprint shows 45.8 m); towers 32 ft wide, spires 329.5 ft. Dates [M]: cornerstone August 15, 1858; dedicated May 25, 1879; spires 1885-1888; Lady Chapel 1901-1906.",
   "City footprint BIN 1081150 (4,119 m2), roof 42.0 m (the nave ridge).",
   "Aisle (15 m) and clerestory (31 m) levels, height of the square tower stage (44 m) and octagon (62 m), central gable (47.5 m), rose window and portal sizes. The 1879 and 1888 states are the same plan without the Lady Chapel / without the spires."),
 'trinity_church': ("Wikipedia 'Trinity Church (Manhattan)' [V]: spire and cross 281 ft, the tallest in the city until 1890. Dates [M]: 1839-1846, consecrated May 21, 1846.",
   "City footprint BIN 1001028 (1,802 m2), roof 84.0 m. OSM 3D parts: aisles 15 m, nave 25 m, All Saints' Chapel 17 m.",
   "Height at which the spire springs from the tower (42-47 m), pinnacles; later chapels and vestries shown from 1846."),
 'st_pauls_chapel': ("No published dimension was verified. Dates [M]: built 1764-1766 (opened October 30, 1766), steeple 1794.",
   "City footprint BIN 1001231 (931 m2), roof 60.7 m (used as the top of the steeple). OSM part: body 23.1 x 35.0 m, 15 m.",
   "All steeple stages, portico levels."),
 'st_john_the_divine': ("Wikipedia 'Cathedral of St. John the Divine' [V]: 601 ft long; narthex 50 x 207 ft; nave 248 x 146 ft, vault 124 ft, roof 177 ft; crossing 100 x 100 ft under a 93 ft dome; western towers reached the roof of the nave, the south tower 50 ft more; cornerstone December 27, 1892; nave cornerstone November 9, 1925; nave completed 1941. [M]: choir and crossing consecrated April 1911; opened full length November 30, 1941.",
   "City footprint BIN 1082706 (8,743 m2 with light courts, 9,141 m2 outline), roof 51.4 m (cited roof 177 ft = 53.9 m used).",
   "Chapel/aisle base 14 m, crossing 40 m and dome rise 8 m, choir 36-44 m, level of the tower stumps (38 m). The 1911 state is the part of the plan east of the nave."),
 'riverside_church': ("Wikipedia 'Riverside Church' [V]: tower 392 ft, 22 storeys; nave 100 ft high, 89 ft wide, 215 ft long; 60 ft between the clerestory walls. Dates [M]: 1927-1930, first service October 5, 1930.",
   "City footprint BIN 1081792 (3,026 m2), roof 118.0 m.",
   "Plan of the tower shaft (22 m square, centred on its 34.8 x 34 m base block) and its stages, nave eaves, the 7 m passage to Claremont Avenue. The 1959 south wing is a separate footprint and is not modelled."),
 'grants_tomb': ("Wikipedia 'Grant's Tomb' [V]: 150 ft tall; base 90 x 90 ft and 72 ft high; stairs 70 ft wide; dome 40 ft across inside. Dates [M]: ground broken April 27, 1891; dedicated April 27, 1897.",
   "City footprint BIN 1057391 (715 m2, 26.7 x 26.8 m, the roofed cube), roof 46.9 m.",
   "Drum, colonnade and stepped cone between the 72 ft and 150 ft levels. The portico and steps stand outside the roofed footprint, hence the plan/official ratio of 1.31."),
 'new_york_city_hall': ("No published dimension was verified. Dates [M]: cornerstone May 26, 1803; occupied 1811-1812.",
   "City footprint BIN 1079147 (1,978 m2), roof 36.6 m (top of the figure of Justice). OSM 3D parts: walls 13.7 m, attic 17 m, roof 20 m, cupola stages 20-27-31.5 m.",
   "Portico levels; cupola column ring."),
 'federal_hall': ("Wikipedia 'Federal Hall' [V]: columns 32 ft high and 5 ft 8 in across; rotunda 60 ft in diameter. Dates [M]: built 1834-1842.",
   "City footprint BIN 1001020 (1,576 m2, 28.4 x 55.5 m), roof 19.3 m. OSM parts: cella 28.4 x 46.5 m, eaves 12 m.",
   "Stepped base 2.6 m, entablature depth; both porticoes drawn alike."),
 'us_custom_house': ("Wikipedia 'Alexander Hamilton U.S. Custom House' [V]: side elevations 300 ft, front 200 ft, rear 290 ft; rusticated base 20 ft; attic sculptures 11 ft; light court 80-120 ft wide and 200 ft deep. Dates [M]: 1900-1907.",
   "City footprint BIN 1000042 (5,917 m2 with the court, 6,278 m2 outline), roof 39.8 m. OSM parts: walls 29 m, rotunda skylight 24.4 x 38.7 m.",
   "Mansard to 34 m (the city-measured 39.8 m is taken to be rooftop plant and is NOT matched), column levels, court floor at 12 m."),
 'tweed_courthouse': ("Wikipedia 'Tweed Courthouse' [V]: 258 x 149 ft; rotunda 53 ft across, 85 ft high. Dates [M]: 1861-1881.",
   "City footprint BIN 1079146 (3,536 m2), roof 25.0 m. OSM parts: walls 17 m, roofs 20 m, rotunda skylight 25 m.", "Portico and stair levels."),
 'new_york_stock_exchange': ("Wikipedia 'New York Stock Exchange Building' [V]: roof 156 ft above the sidewalk; six columns 52 ft tall, 5.5 ft across; windows 96 x 50 ft; pediment about 110 ft wide, about 100 ft above the sidewalk. Dates [M]: opened April 22, 1903.",
   "City footprint BIN 1078981 (1,698 m2), roof 44.5 m (model 47.55 m = the cited 156 ft).", "Podium 9 m, entablature, 36 m front block and the setback line."),
 'castle_clinton': ("Wikipedia 'Castle Clinton' [V]: walls 8 ft thick; roofed 'around 1845'. Dates [M]: built 1808-1811; Castle Garden 1824; immigrant depot 1855-1890; aquarium 1896-1941.",
   "City footprint BIN 1077335: outline 2,753 m2, walls and casemates 1,639 m2 (courtyard 1,114 m2), roof 7.8 m.", "Wall-walk level 6.5 m, gatehouse, embrasure positions."),
 'castle_garden_hall': ("No dimension found. Roofed about 1845 [V]; removed with the aquarium 1941 [M].", "Stands on the Castle Clinton outline.", "Everything: roof form and height (21.5 m) from nineteenth-century views."),
 'washington_square_arch': ("Wikipedia 'Washington Square Arch' [V]: 77 ft high; piers 30 ft apart; opening 47 ft high. Dates [M]: cornerstone May 30, 1890; completed 1892.",
   "City footprint BIN 1088400 (138 m2, 7.1 x 19.4 m), roof 20.4 m.", "Cornice level (17.4-18.3 m); statues shown from 1892. Cornice and statue plinths overhang the footprint (ratio 1.12)."),
 'soldiers_and_sailors_arch': ("Wikipedia 'Soldiers' and Sailors' Arch' [V]: 80 ft tall; opening 50 ft tall and 35 ft wide; footprint 80 x 50 ft narrowing to 25 ft. Dates [M]: cornerstone October 30, 1889; dedicated October 21, 1892.",
   "City footprint BIN 3347227 (147 m2: piers 5.1 x 7.5 m, vault 5.3 m deep, 23.4 m overall), roof 23.2 m.", "Cornice level; the quadriga (about 6.2 m, top of model 30.6 m)."),
 'metropolitan_museum': ("Wikipedia 'Metropolitan Museum of Art' [V]: Robert Lehman Wing opened 1975. [M, not re-read]: Hunt's Fifth Avenue pavilion December 1902; McKim, Mead & White wings 1909-1926; Sackler Wing 1978; American Wing 1980; Rockefeller Wing 1982; Wallace Wing 1987.",
   "City footprint BIN 1083810 (44,512 m2; outline 45,021 m2), roof 26.8 m. The four models together cover 45,451 m2 (ratio 1.02).",
   "The division of the single footprint into the 1926 building and the three park-side wings; every level except the 26.8 m at the Great Hall domes; the Fifth Avenue wings are shown from 1902."),
 'american_museum': ("No published dimension was verified. Dates [M]: cornerstone June 2, 1874; opened December 22, 1877; 77th Street front 1890-1908; Roosevelt Memorial 1936; Gilder Center 2023.",
   "City footprints BIN 1083846 (22,356 m2) and BIN 1090575 (9,765 m2), both with roof 44.8 m; the 77th Street front measures 214.7 m in the footprint.",
   "All range heights; the corner towers are assumed to be the measured 44.8 m. The phases are NOT separated: the model shows today's extent from 1877."),
 'rose_center': ("Wikipedia 'Rose Center for Earth and Space' [V]: six-storey glass cube; Hayden Sphere 87 ft. [M, unverified]: cube 95 ft high. Opened February 19, 2000 [M].",
   "Cube plan 36.8 x 37.4 m from the city footprint BIN 1083846.", "Mullion grid; height of the cube not verified."),
 'guggenheim': ("Wikipedia 'Solomon R. Guggenheim Museum' [V]: oculus about 95 ft high; annex tower 32 ft wide and 135 ft tall; the 1968 annex was cut to two storeys. Dates [M]: opened October 21, 1959; tower 1992.",
   "City footprint BIN 1046946 (1,983 m2), roof 41.6 m (the tower). Rotunda 37 m across at the top (from the outline).", "Heights of the four ramp bands and of the small rotunda; height of the 1968 annex (8.5 m)."),
 'madison_square_garden': ("No published dimension was verified. Opened February 11, 1968 [M].", "OSM 3D part: drum 128.0-128.6 m across. City footprint BIN 1082908 (16,619 m2), roof 44.4 m.", "Level of the lower structure (11 m), roof dish."),
 'low_memorial_library': ("Wikipedia 'Low Memorial Library' [V]: dome radius 52 ft; granite base 12 ft. Dates [M]: cornerstone December 7, 1895; completed 1897.",
   "City footprint BIN 1084472 (2,981 m2, 59.5 x 60.8 m), roof 40.9 m. OSM parts: walls 20 m, octagonal attic 25 m.", "Springing of the dome (32 m), portico column height."),
 'brooklyn_borough_hall': ("Wikipedia 'Brooklyn Borough Hall' [V]: cupola burned February 26, 1895; cast-iron cupola 1898. Dates [M]: built 1846-1848.",
   "City footprint BIN 3000256 (1,548 m2; recorded year 1920 is wrong), roof 41.3 m.", "Wall (16.5 m), portico and cupola-stage heights; today's cupola shown from 1848."),
 'unisphere': ("Wikipedia 'Unisphere' [V]: 140 ft high, 120 ft in diameter, on a 20 ft base; pool 310 ft across. Built 1963-64 [M].", "No building footprint; anchor at the centre of the pool.", "Land masses (15-degree mask), orbit rings, facing of the globe."),
 'new_york_state_pavilion': ("Wikipedia 'New York State Pavilion' [V]: Tent of Tomorrow 250 x 350 ft (or 240 x 320 ft); towers 60 ft (south), 150 ft (north), 226 ft (west).",
   "City footprints BIN 4464054 (tent, 76.0 x 98.7 m, roof 29.6 m), BIN 4541449 (towers, 31.3 m across, roof 64.3 m), BIN 4464056 (Theaterama, roof 17.7 m).", "Spacing of the towers inside their footprint, platform size, cable-roof geometry."),
 'lincoln_center': ("Wikipedia 'Metropolitan Opera House (Lincoln Center)' [V]: five concrete arches 96 ft above the plaza. [M]: Philharmonic Hall opened September 23, 1962 (44 columns); New York State Theater April 23, 1964; opera house September 16, 1966.",
   "City footprints BIN 1081023 (Geffen, 4,634 m2, roof 27.4 m), BIN 1028831 (Koch, 4,679 m2, 31.7 m), BIN 1081022 (opera, 7,539 m2, 37.7 m). OSM parts: 24 m colonnades, 25 m opera body, 27 m auditoria.", "Arch springing, column spacing, Koch front piers."),
 'gould_memorial_library': ("Wikipedia 'Gould Memorial Library' [V]: reading room 54 ft 3 in across inside the colonnade; columns 3 ft 5 in. Dates [M]: 1895-1899.",
   "City footprint BIN 2100243 (1,235 m2), roof 29.9 m.", "Walls 14 m, drum 20 m, dome 25 m across above the roof."),
 'hall_of_fame': ("Wikipedia 'Hall of Fame for Great Americans' [V]: loggia 630 ft long (original section 500 ft). Dedicated May 30, 1901 [M].",
   "City footprints BIN 2096464 (south half and hall, 889 m2, roof 19.5 m) and BIN 2100244 (north, 1,056 m2, 20.7 m): arc of radius 25-30 m about the dome centre.", "North half drawn as the mirror of the south (ratio 0.88, centroid 6 m off); colonnade height 6.2 m; end halls are plain blocks."),
 'brooklyn_museum': ("Wikipedia 'Brooklyn Museum' [V]: Eastern Parkway front 510 ft; cornice figures 12 ft. Dates [M]: first section 1897, pavilion 1905, east wing 1907, additions to 1927.",
   "City footprint BIN 3029667 (7,716 m2), roof 50.0 m - NOT matched (model 34 m): the figure was not understood.", "All heights (walls 24 m, pediment 27.5 m, dome 34 m)."),
 'brooklyn_academy': ("No published dimension was verified. Opened November 1908 [M].", "City footprint BIN 3059185 (3,130 m2), roof 21.7 m.", "Front composition and levels."),
 'yankee_stadium': ("Wikipedia 'Yankee Stadium' [V]: fences 318 / 399 / 408 / 385 / 314 ft. Dates [M]: ground broken August 16, 2006; opened April 2009.",
   "City footprint BIN 2114490 (outline 47,410 m2; 34,903 m2 without the field), roof 36.6 m. OSM pitch polygons for the field and infield.", "Outfield stand height (13 m), seating slope, frieze (3 m), scoreboard."),
 'citi_field': ("Wikipedia 'Citi Field' [V]: rotunda floor 160 ft across. Dates [M]: ground broken November 13, 2006; opened April 2009.",
   "City footprint BIN 4536844 (outline 47,201 m2), roof 24.3 m (not used as the rim). OSM pitch polygon.", "Stand heights (36 m / 14 m), rotunda 21 m, scoreboard."),
 'barclays_center': ("Wikipedia 'Barclays Center' [V]: oculus 117 x 56 ft. Dates [M]: ground broken March 11, 2010; opened September 21, 2012.", "City footprint BIN 3398156 (18,501 m2), roof 42.1 m.", "Band profile, canopy size and position."),
 'arthur_ashe_stadium': ("Wikipedia 'Arthur Ashe Stadium' [V]: roof superstructure 5,000 tons; two 800-ton fabric panels, 210,000 sq ft. No height was found. Opened August 25, 1997; roof 2016 [M].",
   "City footprint BIN 4467715 (16,560 m2 octagon, 137.9 x 138.1 m), roof 17.7 m (not the top of the stands). OSM court polygon.", "Bowl height 36 m; roof height 62 m, 76 m opening, column positions - all from photographs."),
 'wonder_wheel': ("Wikipedia 'Wonder Wheel' [V]: 150 ft tall, 200 tons; built 1918-1920; opened May 30, 1920.", "City footprint BIN 3347224 (platform, 293 m2).", "Wheel diameter 42.6 m, support frame, car positions."),
 'coney_island_cyclone': ("Wikipedia 'Coney Island Cyclone' [V]: track 2,640 ft, six fan turns, twelve drops; height 75 ft (note: some sources give 85 ft). Opened June 26, 1927 [M].", "City footprint BIN 3326898 (site, 2,541 m2).", "The course of the track (schematic). Skeletal structure: plan area not comparable with the site."),
 'parachute_jump': ("Wikipedia 'Parachute Jump' [V]: 250 ft tall, 170 tons; ribs at 7 ft intervals. Re-erected at Coney Island 1941 [M].", "OSM position (building 'Parachute Jump'); city footprint BIN 3404019 (base pavilion, 189 m2).", "Taper of the tower (6 m to 1.5 m radius), reach of the arms (14.5 m)."),
 'little_red_lighthouse': ("No published dimension was verified in text (usually described as 40 ft). Dates [M]: cast 1880, moved to Jeffrey's Hook 1921.", "OSM building 'Little Red Lighthouse': position, height 12.0 m. No city footprint.", "Base diameter and stages."),
 'coney_island_light': ("Wikipedia 'Coney Island Light' [V]: focal height 75 ft; skeletal white tower with black trim. First lit August 1, 1890 [M].", "OSM building 'Coney Island Lighthouse': position, height 22.9 m. No city footprint.", "Leg spread, watch-room size."),
 'blackwell_island_light': ("Wikipedia 'Blackwell Island Light' [V]: about 50 ft tall, grey gneiss. Built 1872 [M].", "City footprint BIN 1090953 (13 m2 octagon, 4.0 m across), roof 17.4 m (model 15.24 m = the cited 50 ft).", "Gallery and lantern stages."),
 'castle_williams': ("Wikipedia 'Castle Williams' [V]: 40 ft high, 210 ft in diameter, walls 7 to 8 ft thick. Built 1807-1811 [M].", "City footprint BIN 1086428 (outline 3,097 m2, walls 2,126 m2), roof 14.9 m.", "Embrasure positions; parapet between 12.2 m and 14.9 m."),
 'battery_weed': ("No published dimension was verified. Built 1847-1864 [M].", "City footprint BIN 5163514 (2,783 m2), roof 17.1 m; OSM 13.6 m.", "Tier levels not modelled; plain walls at the measured height."),
 'fort_tompkins': ("No published dimension was verified. Built 1859-1876 [M].", "City footprint BIN 5157556 (outline 13,461 m2, 7,551 m2 without the parade), roof 15.5 m.", "Shape of the parade (the outline shrunk about its centroid)."),
 'fort_hamilton': ("Wikipedia 'Fort Hamilton' [V]: built 1825-1831.", "City footprint BIN 3345704 (4,008 m2), roof 15.2 m.", "Drawn as a plain 8 m block; height not verified."),
 'wyckoff_house': ("No published dimension was verified. About 1652 [M].", "City footprint BIN 3221967 (205 m2), roof 7.5 m.", "Eaves, lower wing; chimneys rise 0.9 m above the measured ridge."),
 'conference_house': ("No published dimension was verified. About 1680 [M].", "City footprint BIN 5087656 (190 m2, 13.5 x 14.1 m), roof 11.8 m.", "Eaves height; chimneys rise 0.9 m above the measured ridge."),
 'morris_jumel': ("Wikipedia 'Morris-Jumel Mansion' [V]: octagonal annex at the rear. Built 1765 [M].", "City footprint BIN 1084189 (308 m2), roof 11.6 m.", "Eaves, roof, portico levels."),
 'dyckman_farmhouse': ("Wikipedia 'Dyckman House' [V]: built c. 1783-1785.", "City footprint BIN 1075616 (213 m2, 13.6 x 18.0 m), roof 8.6 m.", "Gambrel profile; the porch roof overhangs the footprint (ratio 1.16)."),
 'gracie_mansion': ("No published dimension was verified. Built 1799; Wagner Wing 1966 [M].", "City footprint BIN 1085796 (778 m2), roof 12.6 m.", "Eaves, roofs, porch; the 1966 wing is shown from 1799."),
}
def note(i):
    best = None
    for k in N:
        if i.startswith(k) and (best is None or len(k) > len(best)): best = k
    return N.get(best)
miss = [l['id'] for l in L if note(l['id']) is None]
assert not miss, miss
md = []
md.append("""# Civic landmarks — research notes and numeric checks

Models: `viewer/src/landmarks/nyc-civic.ts` (`CIVIC`, %d entries, %s vertices). Table: `data/tables/landmarks_civic.csv`.

## Method

- **Plan, anchor, orientation**: the city's building footprint (NYC Building Footprints, NYC Open Data — public data, NYC Open Data terms of use) read from `data/interim/nyc_footprints_raw.parquet`, re-expressed in a model frame (origin and bearing are in the code comment of each landmark). Its `height_m` is quoted below as the *city-measured* roof height.
- **Massing**: OpenStreetMap 3D building parts and road centrelines via Overture 2026-10-21.0 (`building_part`, `building`, `roads_region`, `base_land_use`; ODbL, (c) OpenStreetMap contributors).
- **Cited dimensions**: Wikipedia articles (CC BY-SA 4.0; facts only), the article URL is in each landmark's `sources`. **[V]** = the figure was read in the article's wikitext during this work (cached copies: `data/raw/landmarks_civic/wiki/`, gitignored). **[M]** = recalled from the cited source and not re-read in this session — treat as unverified until checked. National Park Service pages (public domain) and Landmarks Preservation Commission designation reports (`s-media.nyc.gov/agencies/lpc/lp/NNNN.pdf`; LP numbers taken from `data/raw/nyc/lpc_individual_landmarks.geojson`) are listed as sources for identification and dates; **no LPC or NPS PDF was opened in this session**, so no dimension below rests on them.
- **Estimates** are listed per landmark and repeated in each model's `facts.Model` (shown in the popup).

## Numeric check

`data/interim/landmarks_civic/check.py` (scratch): each mesh is built with the kit, its plan outline is the union of all its triangles projected to the ground, and that is compared with the city footprints whose centroids fall inside `replaces`. "Official" is the footprint area as recorded (courtyards excluded); "outline" fills the courtyards. Targets: area within about 5 %%, centroid within about 3 m, top against the cited or measured height. Rows outside the targets are explained in the per-landmark notes.

| id | top of model (m) | city-measured roof (m) | plan area (m2) | official (m2) | ratio | outline (m2) | ratio | centroid offset (m) |
|---|---|---|---|---|---|---|---|---|""" % (len(L), format(sum(l['nverts'] for l in L), ',')))
for l in L:
    s = S[l['id']]
    f = lambda k: ('%s' % s[k]) if s.get(k) is not None else '–'
    md.append(f"| {l['id']} | {s['zmax']} | {f('roof')} | {s['plan']} | {f('off')} | {f('ratio')} | {f('off_ext')} | {f('ratio_ext')} | {f('dcen')} |")
md.append("""
Rows with "–" have no footprint of their own: later or earlier states of a site whose footprint is replaced by the standing entry (St. Patrick's 1879/1888, St. Paul's 1766, St. John 1911, the Met's park wings, the Rose Center, the Guggenheim annexes, the Castle Garden hall, the Ashe roof), or structures the city does not map as buildings (Unisphere, the eastern viaduct leg, the Little Red Lighthouse, Coney Island Light).

Not checked: nothing was rendered (no screenshots on this machine); colours, proportions of estimated parts and the look of each model need an eye. `npx tsc --noEmit` reports no error in `nyc-civic.ts`.

## Per landmark
""")
for l in L:
    c, m, e = note(l['id'])
    s = S[l['id']]
    md.append(f"### {l['name']} (`{l['id']}`)\n")
    md.append(f"- Years: construction {l['built'][0]} – {l['built'][1]}; end {l['end']}. Anchor {l['anchor'][1]}, {l['anchor'][0]}.")
    md.append(f"- Cited: {c}")
    md.append(f"- Measured data: {m}")
    md.append(f"- Estimated: {e}")
    chk = f"top {s['zmax']} m"
    if s.get('off') is not None: chk += f"; plan {s['plan']} m2 vs official {s['off']} m2 (ratio {s['ratio']}; outline {s['off_ext']} m2, ratio {s['ratio_ext']}); centroid offset {s['dcen']} m; city-measured roof {s['roof']} m; BIN {', '.join(str(b) for b in s['bins'])}"
    else: chk += f"; plan {s['plan']} m2; no footprint of its own"
    md.append(f"- Check: {chk}.")
    md.append("- Sources: " + ' · '.join(l['sources']) + "\n")
md.append("""## Not modelled

- **Fort Jay** (Governors Island): its four barracks are ordinary footprints; the star-shaped scarp and moat are not in the footprint or Overture extracts, and no measured outline was found — it needs a traced plan (HABS or the NPS site plan).
- **Carnegie Hall** and **Radio City Music Hall**: boxy buildings whose footprint extrusions are close to right; the widths of Carnegie Hall's three parts (main hall 150 x 175 ft, 16-storey east wing, 13-storey south wing — Wikipedia) could not be placed inside its single footprint without guessing.
- The states of the Metropolitan Museum before 1902 and the phases of the American Museum of Natural History; the Hayden Planetarium of 1935 and Ellis Island's station of 1892 (demolished or burned — other files).
""")
open('/home/user/nyc/data/research/landmarks_civic.md', 'w').write('\n'.join(md) + '\n')
with open('/home/user/nyc/data/tables/landmarks_civic.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['id', 'name', 'kind', 'start_year', 'end_year', 'lat', 'lon', 'height_m', 'year_source_url', 'notes'])
    for l in L:
        s = S[l['id']]
        end = 9999 if l['end'] >= 9000 else l['end']
        notes = f"construction from {l['built'][0]}; " + (l['facts'].get('Model') or 'see data/research/landmarks_civic.md')
        w.writerow([l['id'], l['name'], l['kind'], l['built'][1], end, l['anchor'][1], l['anchor'][0], s['zmax'], l['sources'][0], notes])
print(len(L), 'landmarks written')
