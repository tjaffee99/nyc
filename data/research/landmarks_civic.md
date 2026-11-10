# Civic landmarks — research notes and numeric checks

Models: `viewer/src/landmarks/nyc-civic.ts` (`CIVIC`, 66 entries, 107,544 vertices). Table: `data/tables/landmarks_civic.csv`.

## Method

- **Plan, anchor, orientation**: the city's building footprint (NYC Building Footprints, NYC Open Data — public data, NYC Open Data terms of use) read from `data/interim/nyc_footprints_raw.parquet`, re-expressed in a model frame (origin and bearing are in the code comment of each landmark). Its `height_m` is quoted below as the *city-measured* roof height.
- **Massing**: OpenStreetMap 3D building parts and road centrelines via Overture 2026-10-21.0 (`building_part`, `building`, `roads_region`, `base_land_use`; ODbL, (c) OpenStreetMap contributors).
- **Cited dimensions**: Wikipedia articles (CC BY-SA 4.0; facts only), the article URL is in each landmark's `sources`. **[V]** = the figure was read in the article's wikitext during this work (cached copies: `data/raw/landmarks_civic/wiki/`, gitignored). **[M]** = recalled from the cited source and not re-read in this session — treat as unverified until checked. National Park Service pages (public domain) and Landmarks Preservation Commission designation reports (`s-media.nyc.gov/agencies/lpc/lp/NNNN.pdf`; LP numbers taken from `data/raw/nyc/lpc_individual_landmarks.geojson`) are listed as sources for identification and dates; **no LPC or NPS PDF was opened in this session**, so no dimension below rests on them.
- **Estimates** are listed per landmark and repeated in each model's `facts.Model` (shown in the popup).

## Numeric check

`data/interim/landmarks_civic/check.py` (scratch): each mesh is built with the kit, its plan outline is the union of all its triangles projected to the ground, and that is compared with the city footprints whose centroids fall inside `replaces`. "Official" is the footprint area as recorded (courtyards excluded); "outline" fills the courtyards. Targets: area within about 5 %, centroid within about 3 m, top against the cited or measured height. Rows outside the targets are explained in the per-landmark notes.

| id | top of model (m) | city-measured roof (m) | plan area (m2) | official (m2) | ratio | outline (m2) | ratio | centroid offset (m) |
|---|---|---|---|---|---|---|---|---|
| statue_of_liberty | 92.99 | 36.3 | 5584 | 5588 | 0.999 | 5588 | 0.999 | 0.0 |
| ellis_island_main_building | 40.5 | 26.5 | 17720 | 17234 | 1.028 | 18492 | 0.958 | 0.8 |
| grand_central_terminal | 45.8 | 45.8 | 7908 | 7784 | 1.016 | 7784 | 1.016 | 0.7 |
| park_avenue_viaduct | 9.0 | 3.7 | 7641 | 564 | 13.556 | 564 | 13.556 | 81.1 |
| park_avenue_viaduct_east | 9.0 | – | 3181 | – | – | – | – | – |
| new_york_public_library | 35.0 | 38.2 | 9876 | 9788 | 1.009 | 9788 | 1.009 | 0.0 |
| st_patricks_cathedral_1879 | 47.5 | – | 3983 | – | – | – | – | – |
| st_patricks_cathedral_1888 | 100.4 | – | 3983 | – | – | – | – | – |
| st_patricks_cathedral | 100.4 | 42.0 | 4134 | 4119 | 1.004 | 4119 | 1.004 | 0.2 |
| trinity_church | 85.6 | 84.0 | 1815 | 1802 | 1.007 | 1802 | 1.007 | 0.0 |
| st_pauls_chapel_1766 | 16.0 | – | 963 | – | – | – | – | – |
| st_pauls_chapel | 60.7 | 60.7 | 963 | 931 | 1.034 | 931 | 1.034 | 0.0 |
| st_john_the_divine_1911 | 48.0 | – | 5577 | – | – | – | – | – |
| st_john_the_divine | 53.95 | 51.4 | 9378 | 8743 | 1.073 | 9141 | 1.026 | 1.2 |
| riverside_church | 119.5 | 118.0 | 3096 | 3026 | 1.023 | 3026 | 1.023 | 0.7 |
| grants_tomb | 45.72 | 46.9 | 934 | 715 | 1.307 | 715 | 1.307 | 3.2 |
| new_york_city_hall | 36.6 | 36.6 | 2032 | 1978 | 1.028 | 1978 | 1.028 | 0.4 |
| federal_hall_national_memorial | 19.3 | 19.3 | 1580 | 1576 | 1.003 | 1576 | 1.003 | 0.1 |
| us_custom_house_bowling_green | 34.0 | 39.8 | 6537 | 5917 | 1.105 | 6278 | 1.041 | 1.5 |
| tweed_courthouse | 25.0 | 25.0 | 3646 | 3536 | 1.031 | 3536 | 1.031 | 0.7 |
| new_york_stock_exchange | 47.55 | 44.5 | 1761 | 1698 | 1.038 | 1698 | 1.038 | 0.8 |
| castle_clinton | 7.8 | 7.8 | 2705 | 1639 | 1.651 | 2753 | 0.983 | 1.4 |
| castle_garden_hall | 21.5 | – | 2534 | – | – | – | – | – |
| washington_square_arch | 23.47 | 20.4 | 154 | 138 | 1.116 | 138 | 1.116 | 0.1 |
| soldiers_and_sailors_arch | 30.58 | 23.2 | 164 | 147 | 1.117 | 147 | 1.117 | 0.0 |
| metropolitan_museum_of_art | 26.8 | 26.8 | 38000 | 44512 | 0.854 | 45021 | 0.844 | 13.8 |
| metropolitan_museum_lehman_wing | 25.0 | – | 1633 | – | – | – | – | – |
| metropolitan_museum_north_wings | 19.0 | – | 2937 | – | – | – | – | – |
| metropolitan_museum_south_wings | 19.0 | – | 2881 | – | – | – | – | – |
| american_museum_of_natural_history | 44.8 | 44.8 | 31454 | 32084 | 0.98 | 32084 | 0.98 | 3.3 |
| rose_center_for_earth_and_space | 29.26 | – | 1422 | – | – | – | – | – |
| guggenheim_museum | 28.96 | 41.6 | 1708 | 1983 | 0.861 | 1983 | 0.861 | 3.2 |
| guggenheim_annex_1968 | 8.5 | – | 292 | – | – | – | – | – |
| guggenheim_annex_tower | 41.15 | – | 292 | – | – | – | – | – |
| madison_square_garden_iv | 44.4 | 44.4 | 16525 | 16619 | 0.994 | 16619 | 0.994 | 0.2 |
| low_memorial_library | 40.9 | 40.9 | 2983 | 2981 | 1.001 | 2981 | 1.001 | 0.1 |
| brooklyn_borough_hall | 41.3 | 41.3 | 1554 | 1548 | 1.004 | 1548 | 1.004 | 0.0 |
| unisphere | 42.71 | – | 6994 | – | – | – | – | – |
| new_york_state_pavilion | 68.88 | 64.3 | 7386 | 7454 | 0.991 | 7454 | 0.991 | 2.3 |
| lincoln_center_geffen_hall | 27.4 | 27.4 | 4646 | 4634 | 1.003 | 4634 | 1.003 | 0.1 |
| lincoln_center_koch_theater | 31.7 | 31.7 | 4690 | 4679 | 1.002 | 4679 | 1.002 | 0.0 |
| lincoln_center_metropolitan_opera | 37.7 | 37.7 | 7560 | 7539 | 1.003 | 7539 | 1.003 | 0.1 |
| gould_memorial_library | 29.9 | 29.9 | 1244 | 1235 | 1.007 | 1235 | 1.007 | 0.1 |
| hall_of_fame_for_great_americans | 20.7 | 20.7 | 1711 | 1945 | 0.88 | 1945 | 0.88 | 6.2 |
| brooklyn_museum | 34.0 | 50.0 | 7736 | 7716 | 1.003 | 7716 | 1.003 | 0.0 |
| brooklyn_academy_of_music | 21.7 | 21.7 | 3230 | 3130 | 1.032 | 3130 | 1.032 | 0.9 |
| yankee_stadium_2009 | 39.6 | 36.6 | 47450 | 34903 | 1.359 | 47410 | 1.001 | 7.2 |
| citi_field | 36.0 | 24.3 | 47314 | 34708 | 1.363 | 47201 | 1.002 | 3.4 |
| barclays_center | 42.1 | 42.1 | 19069 | 18501 | 1.031 | 18501 | 1.031 | 2.2 |
| arthur_ashe_stadium | 36.0 | 17.7 | 16564 | 16560 | 1.0 | 16560 | 1.0 | 0.0 |
| arthur_ashe_stadium_roof | 62.0 | – | 18644 | – | – | – | – | – |
| wonder_wheel | 45.97 | 4.3 | 354 | 293 | 1.208 | 293 | 1.208 | 0.0 |
| coney_island_cyclone | 22.85 | 6.4 | 733 | 2541 | 0.289 | 2541 | 0.289 | 7.5 |
| parachute_jump | 76.3 | 10.1 | 252 | 189 | 1.331 | 189 | 1.331 | 0.0 |
| little_red_lighthouse | 12.0 | – | 22 | – | – | – | – | – |
| coney_island_light | 22.9 | – | 28 | – | – | – | – | – |
| blackwell_island_light | 15.24 | 17.4 | 16 | 13 | 1.218 | 13 | 1.218 | 0.1 |
| castle_williams | 14.9 | 14.9 | 3043 | 2126 | 1.431 | 3097 | 0.983 | 0.6 |
| battery_weed | 17.1 | 17.1 | 2786 | 2783 | 1.001 | 2783 | 1.001 | 0.2 |
| fort_tompkins | 15.5 | 15.5 | 13464 | 7551 | 1.783 | 13461 | 1.0 | 4.7 |
| fort_hamilton_casemate_fort | 8.0 | 15.2 | 3826 | 4008 | 0.955 | 4008 | 0.955 | 0.8 |
| wyckoff_house | 8.4 | 7.5 | 226 | 205 | 1.106 | 205 | 1.106 | 0.0 |
| conference_house | 12.7 | 11.8 | 208 | 190 | 1.098 | 190 | 1.098 | 0.0 |
| morris_jumel_mansion | 11.6 | 11.6 | 312 | 308 | 1.012 | 308 | 1.012 | 0.8 |
| dyckman_farmhouse | 9.4 | 8.6 | 247 | 213 | 1.161 | 213 | 1.161 | 0.9 |
| gracie_mansion | 12.6 | 12.6 | 788 | 778 | 1.012 | 778 | 1.012 | 0.1 |

Rows with "–" have no footprint of their own: later or earlier states of a site whose footprint is replaced by the standing entry (St. Patrick's 1879/1888, St. Paul's 1766, St. John 1911, the Met's park wings, the Rose Center, the Guggenheim annexes, the Castle Garden hall, the Ashe roof), or structures the city does not map as buildings (Unisphere, the eastern viaduct leg, the Little Red Lighthouse, Coney Island Light).

Not checked: nothing was rendered (no screenshots on this machine); colours, proportions of estimated parts and the look of each model need an eye. `npx tsc --noEmit` reports no error in `nyc-civic.ts`.

## Per landmark

### Statue of Liberty (`statue_of_liberty`)

- Years: construction 1883.3 – 1886.82; end 9999. Anchor 40.689249, -74.044502.
- Cited: Wikipedia physical-characteristics table (= NPS statue statistics), read in the wikitext [V]: copper statue 151 ft 1 in (46.05 m); ground to torch 305 ft 1 in (92.99 m); heel to top of head 111 ft 1 in; head chin to cranium 17 ft 3 in; right arm 42 ft long, 12 ft thick; waist 35 ft; tablet 2 ft thick; pedestal 89 ft; foundation 65 ft. Article text [V]: pedestal a truncated pyramid 62 ft square at the base, 39.4 ft at the top; foundation begun 1883. From the NPS table, not re-read [M]: head 10 ft ear to ear, tablet 23 ft 7 in x 13 ft 7 in, rays up to 9 ft.
- Measured data: Star of Fort Wood: city footprint BIN 1000002 (5,588 m2). OSM 3D parts: pedestal square centred (-2.5, 0.4) m from the anchor, faces bearing 146.7/56.7 deg; fort terreplein 10 m, upper terrace 39.6 x 40.2 m at 10-14 m, foundation 25 m square.
- Estimated: Taper of the pedestal between its cited base and top, the loggia panels, the pose of the figure (body rings, arm angles, tablet position, fan of the seven rays), flame shape. Fort wall height is OSM's 10 m, not a cited figure.
- Check: top 92.99 m; plan 5584 m2 vs official 5588 m2 (ratio 0.999; outline 5588 m2, ratio 0.999); centroid offset 0.0 m; city-measured roof 36.3 m; BIN 1000002.
- Sources: https://www.nps.gov/stli/learn/historyculture/statue-statistics.htm · https://en.wikipedia.org/wiki/Statue_of_Liberty · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Ellis Island — Main Building (`ellis_island_main_building`)

- Years: construction 1898.6 – 1900.96; end 9999. Anchor 40.699, -74.0397.
- Cited: Wikipedia 'Ellis Island', main building section [V]: three storeys; registry room 200 x 100 ft with a 56 ft ceiling; four corner towers with copper cupolas; railroad ticket office annex 1905-06; third storey of the wings early 1910s. Dates [M]: opened December 17, 1900; first station burned June 15, 1897.
- Measured data: City footprint BIN 1085964 merges every connected building of Island 1 (17,234 m2 with courts): main block 118.4 x 50.6 m measured from it, roof 26.5 m.
- Estimated: Tower height (40.5 m to the finials), wing and centre wall heights, arches; the other Island 1 buildings are plain 12 m blocks (heights not researched).
- Check: top 40.5 m; plan 17720 m2 vs official 17234 m2 (ratio 1.028; outline 18492 m2, ratio 0.958); centroid offset 0.8 m; city-measured roof 26.5 m; BIN 1085964.
- Sources: https://en.wikipedia.org/wiki/Ellis_Island · https://www.nps.gov/elis/learn/historyculture/index.htm · https://data.cityofnewyork.us/d/5zhs-2jue

### Grand Central Terminal (`grand_central_terminal`)

- Years: construction 1903.6 – 1913.09; end 9999. Anchor 40.7527, -73.97725.
- Cited: Wikipedia 'Grand Central Terminal' [V]: Main Concourse 275 x 120 x 125 ft; station 'about 125 ft tall'; clock 13 ft; Glory of Commerce 48 ft; three 60 x 30 ft arched windows between ten Doric columns. Dates [M]: construction 1903-1913, opened February 2, 1913.
- Measured data: City footprint BIN 1035381 (7,784 m2), roof 45.8 m (taken as the top of the sculpture group).
- Estimated: Cornice level 27 m, window sill levels, massing of the sculpture group, position of the concourse within the block.
- Check: top 45.8 m; plan 7908 m2 vs official 7784 m2 (ratio 1.016; outline 7784 m2, ratio 1.016); centroid offset 0.7 m; city-measured roof 45.8 m; BIN 1035381.
- Sources: https://en.wikipedia.org/wiki/Grand_Central_Terminal · https://s-media.nyc.gov/agencies/lpc/lp/0266.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Park Avenue Viaduct (Pershing Square Viaduct and western leg) (`park_avenue_viaduct`)

- Years: construction 1917.5 – 1919.3; end 9999. Anchor 40.7527, -73.97725.
- Cited: Wikipedia 'Park Avenue Viaduct' [V]: 600 ft from 40th to 42nd Street; deck 60 ft wide; girders 136 ft; western leg 35 ft, eastern leg 33 ft (53 ft north of 44th), 40 ft across the 42nd Street front; western leg built 1917-1919, eastern leg completed 1928.
- Measured data: Alignment: OSM road centrelines (Overture roads_region 'Park Avenue', bridge flags). City footprint BIN 1085730 (564 m2, the building under the Pershing Square spans) is replaced.
- Estimated: Deck level 8 m; three equal spans between 41st Street and the terminal; the solid base is drawn 14-15 m wide (roadway plus sidewalks) to meet the terminal wall.
- Check: top 9.0 m; plan 7641 m2 vs official 564 m2 (ratio 13.556; outline 564 m2, ratio 13.556); centroid offset 81.1 m; city-measured roof 3.7 m; BIN 1085730.
- Sources: https://en.wikipedia.org/wiki/Park_Avenue_Viaduct · https://s-media.nyc.gov/agencies/lpc/lp/1127.pdf · https://www.openstreetmap.org/

### Park Avenue Viaduct (eastern leg) (`park_avenue_viaduct_east`)

- Years: construction 1927 – 1928.7; end 9999. Anchor 40.7527, -73.97725.
- Cited: Wikipedia 'Park Avenue Viaduct' [V]: 600 ft from 40th to 42nd Street; deck 60 ft wide; girders 136 ft; western leg 35 ft, eastern leg 33 ft (53 ft north of 44th), 40 ft across the 42nd Street front; western leg built 1917-1919, eastern leg completed 1928.
- Measured data: Alignment: OSM road centrelines (Overture roads_region 'Park Avenue', bridge flags). City footprint BIN 1085730 (564 m2, the building under the Pershing Square spans) is replaced.
- Estimated: Deck level 8 m; three equal spans between 41st Street and the terminal; the solid base is drawn 14-15 m wide (roadway plus sidewalks) to meet the terminal wall.
- Check: top 9.0 m; plan 3181 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/Park_Avenue_Viaduct · https://s-media.nyc.gov/agencies/lpc/lp/1127.pdf · https://www.openstreetmap.org/

### New York Public Library — Stephen A. Schwarzman Building (`new_york_public_library`)

- Years: construction 1902.4 – 1911.39; end 9999. Anchor 40.7532, -73.98225.
- Cited: Wikipedia 'New York Public Library Main Branch' [V]: 390 ft north-south by 270 ft; Main Reading Room 78 x 297 ft, 52 ft high; courts 80 x 80 ft; six 11 ft attic figures. Dates [M]: cornerstone November 1902, opened May 23, 1911.
- Measured data: City footprint BIN 1034194 (9,788 m2; its recorded year, 1940, is wrong), roof 38.2 m. OSM 3D parts: main roof 22 m, rear range and centre pavilion 35 m (the model tops out at OSM's 35 m, 3.2 m under the city-measured figure).
- Estimated: Portico: column, entablature and attic levels; end-pavilion pediments.
- Check: top 35.0 m; plan 9876 m2 vs official 9788 m2 (ratio 1.009; outline 9788 m2, ratio 1.009); centroid offset 0.0 m; city-measured roof 38.2 m; BIN 1034194.
- Sources: https://en.wikipedia.org/wiki/New_York_Public_Library_Main_Branch · https://s-media.nyc.gov/agencies/lpc/lp/0246.pdf · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### St. Patrick's Cathedral (as dedicated in 1879, before the spires) (`st_patricks_cathedral_1879`)

- Years: construction 1858.62 – 1879.4; end 1888.8. Anchor 40.75845, -73.976.
- Cited: Wikipedia 'St. Patrick's Cathedral (Midtown Manhattan)' [V]: 332 ft long (396.7 ft with the Lady Chapel); 174 ft at the transepts (the footprint shows 45.8 m); towers 32 ft wide, spires 329.5 ft. Dates [M]: cornerstone August 15, 1858; dedicated May 25, 1879; spires 1885-1888; Lady Chapel 1901-1906.
- Measured data: City footprint BIN 1081150 (4,119 m2), roof 42.0 m (the nave ridge).
- Estimated: Aisle (15 m) and clerestory (31 m) levels, height of the square tower stage (44 m) and octagon (62 m), central gable (47.5 m), rose window and portal sizes. The 1879 and 1888 states are the same plan without the Lady Chapel / without the spires.
- Check: top 47.5 m; plan 3983 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/St._Patrick's_Cathedral_(Midtown_Manhattan) · https://s-media.nyc.gov/agencies/lpc/lp/0267.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### St. Patrick's Cathedral (with the spires of 1888, before the Lady Chapel) (`st_patricks_cathedral_1888`)

- Years: construction 1885.7 – 1888.8; end 1906.5. Anchor 40.75845, -73.976.
- Cited: Wikipedia 'St. Patrick's Cathedral (Midtown Manhattan)' [V]: 332 ft long (396.7 ft with the Lady Chapel); 174 ft at the transepts (the footprint shows 45.8 m); towers 32 ft wide, spires 329.5 ft. Dates [M]: cornerstone August 15, 1858; dedicated May 25, 1879; spires 1885-1888; Lady Chapel 1901-1906.
- Measured data: City footprint BIN 1081150 (4,119 m2), roof 42.0 m (the nave ridge).
- Estimated: Aisle (15 m) and clerestory (31 m) levels, height of the square tower stage (44 m) and octagon (62 m), central gable (47.5 m), rose window and portal sizes. The 1879 and 1888 states are the same plan without the Lady Chapel / without the spires.
- Check: top 100.4 m; plan 3983 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/St._Patrick's_Cathedral_(Midtown_Manhattan) · https://s-media.nyc.gov/agencies/lpc/lp/0267.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### St. Patrick's Cathedral (`st_patricks_cathedral`)

- Years: construction 1901.5 – 1906.5; end 9999. Anchor 40.75845, -73.976.
- Cited: Wikipedia 'St. Patrick's Cathedral (Midtown Manhattan)' [V]: 332 ft long (396.7 ft with the Lady Chapel); 174 ft at the transepts (the footprint shows 45.8 m); towers 32 ft wide, spires 329.5 ft. Dates [M]: cornerstone August 15, 1858; dedicated May 25, 1879; spires 1885-1888; Lady Chapel 1901-1906.
- Measured data: City footprint BIN 1081150 (4,119 m2), roof 42.0 m (the nave ridge).
- Estimated: Aisle (15 m) and clerestory (31 m) levels, height of the square tower stage (44 m) and octagon (62 m), central gable (47.5 m), rose window and portal sizes. The 1879 and 1888 states are the same plan without the Lady Chapel / without the spires.
- Check: top 100.4 m; plan 4134 m2 vs official 4119 m2 (ratio 1.004; outline 4119 m2, ratio 1.004); centroid offset 0.2 m; city-measured roof 42.0 m; BIN 1081150.
- Sources: https://en.wikipedia.org/wiki/St._Patrick's_Cathedral_(Midtown_Manhattan) · https://s-media.nyc.gov/agencies/lpc/lp/0267.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Trinity Church (third building) (`trinity_church`)

- Years: construction 1839.5 – 1846.39; end 9999. Anchor 40.7081, -74.0121.
- Cited: Wikipedia 'Trinity Church (Manhattan)' [V]: spire and cross 281 ft, the tallest in the city until 1890. Dates [M]: 1839-1846, consecrated May 21, 1846.
- Measured data: City footprint BIN 1001028 (1,802 m2), roof 84.0 m. OSM 3D parts: aisles 15 m, nave 25 m, All Saints' Chapel 17 m.
- Estimated: Height at which the spire springs from the tower (42-47 m), pinnacles; later chapels and vestries shown from 1846.
- Check: top 85.6 m; plan 1815 m2 vs official 1802 m2 (ratio 1.007; outline 1802 m2, ratio 1.007); centroid offset 0.0 m; city-measured roof 84.0 m; BIN 1001028.
- Sources: https://en.wikipedia.org/wiki/Trinity_Church_(Manhattan) · https://s-media.nyc.gov/agencies/lpc/lp/0048.pdf · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### St. Paul's Chapel (before the steeple) (`st_pauls_chapel_1766`)

- Years: construction 1764.4 – 1766.83; end 1794.5. Anchor 40.7113, -74.0092.
- Cited: No published dimension was verified. Dates [M]: built 1764-1766 (opened October 30, 1766), steeple 1794.
- Measured data: City footprint BIN 1001231 (931 m2), roof 60.7 m (used as the top of the steeple). OSM part: body 23.1 x 35.0 m, 15 m.
- Estimated: All steeple stages, portico levels.
- Check: top 16.0 m; plan 963 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/St._Paul's_Chapel · https://s-media.nyc.gov/agencies/lpc/lp/0075.pdf · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### St. Paul's Chapel (`st_pauls_chapel`)

- Years: construction 1793.5 – 1794.5; end 9999. Anchor 40.7113, -74.0092.
- Cited: No published dimension was verified. Dates [M]: built 1764-1766 (opened October 30, 1766), steeple 1794.
- Measured data: City footprint BIN 1001231 (931 m2), roof 60.7 m (used as the top of the steeple). OSM part: body 23.1 x 35.0 m, 15 m.
- Estimated: All steeple stages, portico levels.
- Check: top 60.7 m; plan 963 m2 vs official 931 m2 (ratio 1.034; outline 931 m2, ratio 1.034); centroid offset 0.0 m; city-measured roof 60.7 m; BIN 1001231.
- Sources: https://en.wikipedia.org/wiki/St._Paul's_Chapel · https://s-media.nyc.gov/agencies/lpc/lp/0075.pdf · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Cathedral of St. John the Divine (choir and crossing, before the nave) (`st_john_the_divine_1911`)

- Years: construction 1892.99 – 1911.3; end 1941.91. Anchor 40.8038, -73.9619.
- Cited: Wikipedia 'Cathedral of St. John the Divine' [V]: 601 ft long; narthex 50 x 207 ft; nave 248 x 146 ft, vault 124 ft, roof 177 ft; crossing 100 x 100 ft under a 93 ft dome; western towers reached the roof of the nave, the south tower 50 ft more; cornerstone December 27, 1892; nave cornerstone November 9, 1925; nave completed 1941. [M]: choir and crossing consecrated April 1911; opened full length November 30, 1941.
- Measured data: City footprint BIN 1082706 (8,743 m2 with light courts, 9,141 m2 outline), roof 51.4 m (cited roof 177 ft = 53.9 m used).
- Estimated: Chapel/aisle base 14 m, crossing 40 m and dome rise 8 m, choir 36-44 m, level of the tower stumps (38 m). The 1911 state is the part of the plan east of the nave.
- Check: top 48.0 m; plan 5577 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/Cathedral_of_St._John_the_Divine · https://s-media.nyc.gov/agencies/lpc/lp/2585.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Cathedral of St. John the Divine (`st_john_the_divine`)

- Years: construction 1925 – 1941.91; end 9999. Anchor 40.8038, -73.9619.
- Cited: Wikipedia 'Cathedral of St. John the Divine' [V]: 601 ft long; narthex 50 x 207 ft; nave 248 x 146 ft, vault 124 ft, roof 177 ft; crossing 100 x 100 ft under a 93 ft dome; western towers reached the roof of the nave, the south tower 50 ft more; cornerstone December 27, 1892; nave cornerstone November 9, 1925; nave completed 1941. [M]: choir and crossing consecrated April 1911; opened full length November 30, 1941.
- Measured data: City footprint BIN 1082706 (8,743 m2 with light courts, 9,141 m2 outline), roof 51.4 m (cited roof 177 ft = 53.9 m used).
- Estimated: Chapel/aisle base 14 m, crossing 40 m and dome rise 8 m, choir 36-44 m, level of the tower stumps (38 m). The 1911 state is the part of the plan east of the nave.
- Check: top 53.95 m; plan 9378 m2 vs official 8743 m2 (ratio 1.073; outline 9141 m2, ratio 1.026); centroid offset 1.2 m; city-measured roof 51.4 m; BIN 1082706.
- Sources: https://en.wikipedia.org/wiki/Cathedral_of_St._John_the_Divine · https://s-media.nyc.gov/agencies/lpc/lp/2585.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Riverside Church (`riverside_church`)

- Years: construction 1927 – 1930.76; end 9999. Anchor 40.81185, -73.96315.
- Cited: Wikipedia 'Riverside Church' [V]: tower 392 ft, 22 storeys; nave 100 ft high, 89 ft wide, 215 ft long; 60 ft between the clerestory walls. Dates [M]: 1927-1930, first service October 5, 1930.
- Measured data: City footprint BIN 1081792 (3,026 m2), roof 118.0 m.
- Estimated: Plan of the tower shaft (22 m square, centred on its 34.8 x 34 m base block) and its stages, nave eaves, the 7 m passage to Claremont Avenue. The 1959 south wing is a separate footprint and is not modelled.
- Check: top 119.5 m; plan 3096 m2 vs official 3026 m2 (ratio 1.023; outline 3026 m2, ratio 1.023); centroid offset 0.7 m; city-measured roof 118.0 m; BIN 1081792.
- Sources: https://en.wikipedia.org/wiki/Riverside_Church · https://s-media.nyc.gov/agencies/lpc/lp/2037.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### General Grant National Memorial (Grant's Tomb) (`grants_tomb`)

- Years: construction 1891.32 – 1897.32; end 9999. Anchor 40.8134, -73.96305.
- Cited: Wikipedia 'Grant's Tomb' [V]: 150 ft tall; base 90 x 90 ft and 72 ft high; stairs 70 ft wide; dome 40 ft across inside. Dates [M]: ground broken April 27, 1891; dedicated April 27, 1897.
- Measured data: City footprint BIN 1057391 (715 m2, 26.7 x 26.8 m, the roofed cube), roof 46.9 m.
- Estimated: Drum, colonnade and stepped cone between the 72 ft and 150 ft levels. The portico and steps stand outside the roofed footprint, hence the plan/official ratio of 1.31.
- Check: top 45.72 m; plan 934 m2 vs official 715 m2 (ratio 1.307; outline 715 m2, ratio 1.307); centroid offset 3.2 m; city-measured roof 46.9 m; BIN 1057391.
- Sources: https://en.wikipedia.org/wiki/Grant's_Tomb · https://www.nps.gov/gegr/index.htm · https://s-media.nyc.gov/agencies/lpc/lp/0900.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### New York City Hall (`new_york_city_hall`)

- Years: construction 1803.4 – 1812.5; end 9999. Anchor 40.71275, -74.00605.
- Cited: No published dimension was verified. Dates [M]: cornerstone May 26, 1803; occupied 1811-1812.
- Measured data: City footprint BIN 1079147 (1,978 m2), roof 36.6 m (top of the figure of Justice). OSM 3D parts: walls 13.7 m, attic 17 m, roof 20 m, cupola stages 20-27-31.5 m.
- Estimated: Portico levels; cupola column ring.
- Check: top 36.6 m; plan 2032 m2 vs official 1978 m2 (ratio 1.028; outline 1978 m2, ratio 1.028); centroid offset 0.4 m; city-measured roof 36.6 m; BIN 1079147.
- Sources: https://en.wikipedia.org/wiki/New_York_City_Hall · https://s-media.nyc.gov/agencies/lpc/lp/0080.pdf · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Federal Hall National Memorial (U.S. Custom House of 1842) (`federal_hall_national_memorial`)

- Years: construction 1834.5 – 1842.5; end 9999. Anchor 40.7073, -74.01025.
- Cited: Wikipedia 'Federal Hall' [V]: columns 32 ft high and 5 ft 8 in across; rotunda 60 ft in diameter. Dates [M]: built 1834-1842.
- Measured data: City footprint BIN 1001020 (1,576 m2, 28.4 x 55.5 m), roof 19.3 m. OSM parts: cella 28.4 x 46.5 m, eaves 12 m.
- Estimated: Stepped base 2.6 m, entablature depth; both porticoes drawn alike.
- Check: top 19.3 m; plan 1580 m2 vs official 1576 m2 (ratio 1.003; outline 1576 m2, ratio 1.003); centroid offset 0.1 m; city-measured roof 19.3 m; BIN 1001020.
- Sources: https://en.wikipedia.org/wiki/Federal_Hall · https://www.nps.gov/feha/index.htm · https://s-media.nyc.gov/agencies/lpc/lp/0047.pdf · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Alexander Hamilton U.S. Custom House (`us_custom_house_bowling_green`)

- Years: construction 1900.9 – 1907.75; end 9999. Anchor 40.70415, -74.0137.
- Cited: Wikipedia 'Alexander Hamilton U.S. Custom House' [V]: side elevations 300 ft, front 200 ft, rear 290 ft; rusticated base 20 ft; attic sculptures 11 ft; light court 80-120 ft wide and 200 ft deep. Dates [M]: 1900-1907.
- Measured data: City footprint BIN 1000042 (5,917 m2 with the court, 6,278 m2 outline), roof 39.8 m. OSM parts: walls 29 m, rotunda skylight 24.4 x 38.7 m.
- Estimated: Mansard to 34 m (the city-measured 39.8 m is taken to be rooftop plant and is NOT matched), column levels, court floor at 12 m.
- Check: top 34.0 m; plan 6537 m2 vs official 5917 m2 (ratio 1.105; outline 6278 m2, ratio 1.041); centroid offset 1.5 m; city-measured roof 39.8 m; BIN 1000042.
- Sources: https://en.wikipedia.org/wiki/Alexander_Hamilton_U.S._Custom_House · https://s-media.nyc.gov/agencies/lpc/lp/0020.pdf · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Tweed Courthouse (Old New York County Courthouse) (`tweed_courthouse`)

- Years: construction 1861.7 – 1881.9; end 9999. Anchor 40.71345, -74.0056.
- Cited: Wikipedia 'Tweed Courthouse' [V]: 258 x 149 ft; rotunda 53 ft across, 85 ft high. Dates [M]: 1861-1881.
- Measured data: City footprint BIN 1079146 (3,536 m2), roof 25.0 m. OSM parts: walls 17 m, roofs 20 m, rotunda skylight 25 m.
- Estimated: Portico and stair levels.
- Check: top 25.0 m; plan 3646 m2 vs official 3536 m2 (ratio 1.031; outline 3536 m2, ratio 1.031); centroid offset 0.7 m; city-measured roof 25.0 m; BIN 1079146.
- Sources: https://en.wikipedia.org/wiki/Tweed_Courthouse · https://s-media.nyc.gov/agencies/lpc/lp/1437.pdf · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### New York Stock Exchange Building (`new_york_stock_exchange`)

- Years: construction 1901.3 – 1903.31; end 9999. Anchor 40.7069, -74.01115.
- Cited: Wikipedia 'New York Stock Exchange Building' [V]: roof 156 ft above the sidewalk; six columns 52 ft tall, 5.5 ft across; windows 96 x 50 ft; pediment about 110 ft wide, about 100 ft above the sidewalk. Dates [M]: opened April 22, 1903.
- Measured data: City footprint BIN 1078981 (1,698 m2), roof 44.5 m (model 47.55 m = the cited 156 ft).
- Estimated: Podium 9 m, entablature, 36 m front block and the setback line.
- Check: top 47.55 m; plan 1761 m2 vs official 1698 m2 (ratio 1.038; outline 1698 m2, ratio 1.038); centroid offset 0.8 m; city-measured roof 44.5 m; BIN 1078981.
- Sources: https://en.wikipedia.org/wiki/New_York_Stock_Exchange_Building · https://s-media.nyc.gov/agencies/lpc/lp/1529.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Castle Clinton (West Battery) (`castle_clinton`)

- Years: construction 1808.5 – 1811.9; end 9999. Anchor 40.7035, -74.0168.
- Cited: Wikipedia 'Castle Clinton' [V]: walls 8 ft thick; roofed 'around 1845'. Dates [M]: built 1808-1811; Castle Garden 1824; immigrant depot 1855-1890; aquarium 1896-1941.
- Measured data: City footprint BIN 1077335: outline 2,753 m2, walls and casemates 1,639 m2 (courtyard 1,114 m2), roof 7.8 m.
- Estimated: Wall-walk level 6.5 m, gatehouse, embrasure positions.
- Check: top 7.8 m; plan 2705 m2 vs official 1639 m2 (ratio 1.651; outline 2753 m2, ratio 0.983); centroid offset 1.4 m; city-measured roof 7.8 m; BIN 1077335.
- Sources: https://en.wikipedia.org/wiki/Castle_Clinton · https://www.nps.gov/cacl/learn/historyculture/index.htm · https://s-media.nyc.gov/agencies/lpc/lp/0029.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Castle Garden / New York Aquarium (the roofed hall on Castle Clinton) (`castle_garden_hall`)

- Years: construction 1844 – 1845.5; end 1941.8. Anchor 40.7035, -74.0168.
- Cited: No dimension found. Roofed about 1845 [V]; removed with the aquarium 1941 [M].
- Measured data: Stands on the Castle Clinton outline.
- Estimated: Everything: roof form and height (21.5 m) from nineteenth-century views.
- Check: top 21.5 m; plan 2534 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/Castle_Clinton · https://www.nps.gov/cacl/learn/historyculture/index.htm · https://s-media.nyc.gov/agencies/lpc/lp/0029.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Washington Square Arch (`washington_square_arch`)

- Years: construction 1890.41 – 1892.3; end 9999. Anchor 40.7312, -73.99715.
- Cited: Wikipedia 'Washington Square Arch' [V]: 77 ft high; piers 30 ft apart; opening 47 ft high. Dates [M]: cornerstone May 30, 1890; completed 1892.
- Measured data: City footprint BIN 1088400 (138 m2, 7.1 x 19.4 m), roof 20.4 m.
- Estimated: Cornice level (17.4-18.3 m); statues shown from 1892. Cornice and statue plinths overhang the footprint (ratio 1.12).
- Check: top 23.47 m; plan 154 m2 vs official 138 m2 (ratio 1.116; outline 138 m2, ratio 1.116); centroid offset 0.1 m; city-measured roof 20.4 m; BIN 1088400.
- Sources: https://en.wikipedia.org/wiki/Washington_Square_Arch · https://data.cityofnewyork.us/d/5zhs-2jue

### Soldiers' and Sailors' Memorial Arch (Grand Army Plaza) (`soldiers_and_sailors_arch`)

- Years: construction 1889.83 – 1892.8; end 9999. Anchor 40.6729, -73.96995.
- Cited: Wikipedia 'Soldiers' and Sailors' Arch' [V]: 80 ft tall; opening 50 ft tall and 35 ft wide; footprint 80 x 50 ft narrowing to 25 ft. Dates [M]: cornerstone October 30, 1889; dedicated October 21, 1892.
- Measured data: City footprint BIN 3347227 (147 m2: piers 5.1 x 7.5 m, vault 5.3 m deep, 23.4 m overall), roof 23.2 m.
- Estimated: Cornice level; the quadriga (about 6.2 m, top of model 30.6 m).
- Check: top 30.58 m; plan 164 m2 vs official 147 m2 (ratio 1.117; outline 147 m2, ratio 1.117); centroid offset 0.0 m; city-measured roof 23.2 m; BIN 3347227.
- Sources: https://en.wikipedia.org/wiki/Soldiers'_and_Sailors'_Arch · https://s-media.nyc.gov/agencies/lpc/lp/0821.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Metropolitan Museum of Art — Fifth Avenue building (`metropolitan_museum_of_art`)

- Years: construction 1895.9 – 1902.96; end 9999. Anchor 40.77945, -73.9632.
- Cited: Wikipedia 'Metropolitan Museum of Art' [V]: Robert Lehman Wing opened 1975. [M, not re-read]: Hunt's Fifth Avenue pavilion December 1902; McKim, Mead & White wings 1909-1926; Sackler Wing 1978; American Wing 1980; Rockefeller Wing 1982; Wallace Wing 1987.
- Measured data: City footprint BIN 1083810 (44,512 m2; outline 45,021 m2), roof 26.8 m. The four models together cover 45,451 m2 (ratio 1.02).
- Estimated: The division of the single footprint into the 1926 building and the three park-side wings; every level except the 26.8 m at the Great Hall domes; the Fifth Avenue wings are shown from 1902.
- Check: top 26.8 m; plan 38000 m2 vs official 44512 m2 (ratio 0.854; outline 45021 m2, ratio 0.844); centroid offset 13.8 m; city-measured roof 26.8 m; BIN 1083810.
- Sources: https://en.wikipedia.org/wiki/Metropolitan_Museum_of_Art_Fifth_Avenue · https://s-media.nyc.gov/agencies/lpc/lp/0410.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Metropolitan Museum of Art — Robert Lehman Wing (`metropolitan_museum_lehman_wing`)

- Years: construction 1972.5 – 1975.4; end 9999. Anchor 40.77945, -73.9632.
- Cited: Wikipedia 'Metropolitan Museum of Art' [V]: Robert Lehman Wing opened 1975. [M, not re-read]: Hunt's Fifth Avenue pavilion December 1902; McKim, Mead & White wings 1909-1926; Sackler Wing 1978; American Wing 1980; Rockefeller Wing 1982; Wallace Wing 1987.
- Measured data: City footprint BIN 1083810 (44,512 m2; outline 45,021 m2), roof 26.8 m. The four models together cover 45,451 m2 (ratio 1.02).
- Estimated: The division of the single footprint into the 1926 building and the three park-side wings; every level except the 26.8 m at the Great Hall domes; the Fifth Avenue wings are shown from 1902.
- Check: top 25.0 m; plan 1633 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/Metropolitan_Museum_of_Art_Fifth_Avenue · https://s-media.nyc.gov/agencies/lpc/lp/0410.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Metropolitan Museum of Art — Sackler Wing and American Wing (`metropolitan_museum_north_wings`)

- Years: construction 1975 – 1980.4; end 9999. Anchor 40.77945, -73.9632.
- Cited: Wikipedia 'Metropolitan Museum of Art' [V]: Robert Lehman Wing opened 1975. [M, not re-read]: Hunt's Fifth Avenue pavilion December 1902; McKim, Mead & White wings 1909-1926; Sackler Wing 1978; American Wing 1980; Rockefeller Wing 1982; Wallace Wing 1987.
- Measured data: City footprint BIN 1083810 (44,512 m2; outline 45,021 m2), roof 26.8 m. The four models together cover 45,451 m2 (ratio 1.02).
- Estimated: The division of the single footprint into the 1926 building and the three park-side wings; every level except the 26.8 m at the Great Hall domes; the Fifth Avenue wings are shown from 1902.
- Check: top 19.0 m; plan 2937 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/Metropolitan_Museum_of_Art_Fifth_Avenue · https://s-media.nyc.gov/agencies/lpc/lp/0410.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Metropolitan Museum of Art — Rockefeller and Wallace Wings (`metropolitan_museum_south_wings`)

- Years: construction 1978 – 1987.1; end 9999. Anchor 40.77945, -73.9632.
- Cited: Wikipedia 'Metropolitan Museum of Art' [V]: Robert Lehman Wing opened 1975. [M, not re-read]: Hunt's Fifth Avenue pavilion December 1902; McKim, Mead & White wings 1909-1926; Sackler Wing 1978; American Wing 1980; Rockefeller Wing 1982; Wallace Wing 1987.
- Measured data: City footprint BIN 1083810 (44,512 m2; outline 45,021 m2), roof 26.8 m. The four models together cover 45,451 m2 (ratio 1.02).
- Estimated: The division of the single footprint into the 1926 building and the three park-side wings; every level except the 26.8 m at the Great Hall domes; the Fifth Avenue wings are shown from 1902.
- Check: top 19.0 m; plan 2881 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/Metropolitan_Museum_of_Art_Fifth_Avenue · https://s-media.nyc.gov/agencies/lpc/lp/0410.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### American Museum of Natural History (`american_museum_of_natural_history`)

- Years: construction 1874.42 – 1877.97; end 9999. Anchor 40.7813, -73.974.
- Cited: No published dimension was verified. Dates [M]: cornerstone June 2, 1874; opened December 22, 1877; 77th Street front 1890-1908; Roosevelt Memorial 1936; Gilder Center 2023.
- Measured data: City footprints BIN 1083846 (22,356 m2) and BIN 1090575 (9,765 m2), both with roof 44.8 m; the 77th Street front measures 214.7 m in the footprint.
- Estimated: All range heights; the corner towers are assumed to be the measured 44.8 m. The phases are NOT separated: the model shows today's extent from 1877.
- Check: top 44.8 m; plan 31454 m2 vs official 32084 m2 (ratio 0.98; outline 32084 m2, ratio 0.98); centroid offset 3.3 m; city-measured roof 44.8 m; BIN 1090575, 1083846.
- Sources: https://en.wikipedia.org/wiki/American_Museum_of_Natural_History · https://s-media.nyc.gov/agencies/lpc/lp/0282.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Rose Center for Earth and Space (Hayden Planetarium) (`rose_center_for_earth_and_space`)

- Years: construction 1997 – 2000.13; end 9999. Anchor 40.7813, -73.974.
- Cited: Wikipedia 'Rose Center for Earth and Space' [V]: six-storey glass cube; Hayden Sphere 87 ft. [M, unverified]: cube 95 ft high. Opened February 19, 2000 [M].
- Measured data: Cube plan 36.8 x 37.4 m from the city footprint BIN 1083846.
- Estimated: Mullion grid; height of the cube not verified.
- Check: top 29.26 m; plan 1422 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/Rose_Center_for_Earth_and_Space · https://data.cityofnewyork.us/d/5zhs-2jue

### Solomon R. Guggenheim Museum (`guggenheim_museum`)

- Years: construction 1956.6 – 1959.8; end 9999. Anchor 40.783, -73.95895.
- Cited: Wikipedia 'Solomon R. Guggenheim Museum' [V]: oculus about 95 ft high; annex tower 32 ft wide and 135 ft tall; the 1968 annex was cut to two storeys. Dates [M]: opened October 21, 1959; tower 1992.
- Measured data: City footprint BIN 1046946 (1,983 m2), roof 41.6 m (the tower). Rotunda 37 m across at the top (from the outline).
- Estimated: Heights of the four ramp bands and of the small rotunda; height of the 1968 annex (8.5 m).
- Check: top 28.96 m; plan 1708 m2 vs official 1983 m2 (ratio 0.861; outline 1983 m2, ratio 0.861); centroid offset 3.2 m; city-measured roof 41.6 m; BIN 1046946.
- Sources: https://en.wikipedia.org/wiki/Solomon_R._Guggenheim_Museum · https://s-media.nyc.gov/agencies/lpc/lp/1774.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Guggenheim Museum — annex of 1968 (`guggenheim_annex_1968`)

- Years: construction 1966.5 – 1968.5; end 1990. Anchor 40.783, -73.95895.
- Cited: Wikipedia 'Solomon R. Guggenheim Museum' [V]: oculus about 95 ft high; annex tower 32 ft wide and 135 ft tall; the 1968 annex was cut to two storeys. Dates [M]: opened October 21, 1959; tower 1992.
- Measured data: City footprint BIN 1046946 (1,983 m2), roof 41.6 m (the tower). Rotunda 37 m across at the top (from the outline).
- Estimated: Heights of the four ramp bands and of the small rotunda; height of the 1968 annex (8.5 m).
- Check: top 8.5 m; plan 292 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/Solomon_R._Guggenheim_Museum · https://s-media.nyc.gov/agencies/lpc/lp/1774.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Guggenheim Museum — annex tower (`guggenheim_annex_tower`)

- Years: construction 1990 – 1992.5; end 9999. Anchor 40.783, -73.95895.
- Cited: Wikipedia 'Solomon R. Guggenheim Museum' [V]: oculus about 95 ft high; annex tower 32 ft wide and 135 ft tall; the 1968 annex was cut to two storeys. Dates [M]: opened October 21, 1959; tower 1992.
- Measured data: City footprint BIN 1046946 (1,983 m2), roof 41.6 m (the tower). Rotunda 37 m across at the top (from the outline).
- Estimated: Heights of the four ramp bands and of the small rotunda; height of the 1968 annex (8.5 m).
- Check: top 41.15 m; plan 292 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/Solomon_R._Guggenheim_Museum · https://s-media.nyc.gov/agencies/lpc/lp/1774.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Madison Square Garden (the fourth) (`madison_square_garden_iv`)

- Years: construction 1964.8 – 1968.11; end 9999. Anchor 40.7505, -73.99345.
- Cited: No published dimension was verified. Opened February 11, 1968 [M].
- Measured data: OSM 3D part: drum 128.0-128.6 m across. City footprint BIN 1082908 (16,619 m2), roof 44.4 m.
- Estimated: Level of the lower structure (11 m), roof dish.
- Check: top 44.4 m; plan 16525 m2 vs official 16619 m2 (ratio 0.994; outline 16619 m2, ratio 0.994); centroid offset 0.2 m; city-measured roof 44.4 m; BIN 1082908.
- Sources: https://en.wikipedia.org/wiki/Madison_Square_Garden · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Low Memorial Library (Columbia University) (`low_memorial_library`)

- Years: construction 1895.93 – 1897.75; end 9999. Anchor 40.808223, -73.961835.
- Cited: Wikipedia 'Low Memorial Library' [V]: dome radius 52 ft; granite base 12 ft. Dates [M]: cornerstone December 7, 1895; completed 1897.
- Measured data: City footprint BIN 1084472 (2,981 m2, 59.5 x 60.8 m), roof 40.9 m. OSM parts: walls 20 m, octagonal attic 25 m.
- Estimated: Springing of the dome (32 m), portico column height.
- Check: top 40.9 m; plan 2983 m2 vs official 2981 m2 (ratio 1.001; outline 2981 m2, ratio 1.001); centroid offset 0.1 m; city-measured roof 40.9 m; BIN 1084472.
- Sources: https://en.wikipedia.org/wiki/Low_Memorial_Library · https://s-media.nyc.gov/agencies/lpc/lp/0304.pdf · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Brooklyn Borough Hall (Brooklyn City Hall) (`brooklyn_borough_hall`)

- Years: construction 1846 – 1848.5; end 9999. Anchor 40.6928, -73.9903.
- Cited: Wikipedia 'Brooklyn Borough Hall' [V]: cupola burned February 26, 1895; cast-iron cupola 1898. Dates [M]: built 1846-1848.
- Measured data: City footprint BIN 3000256 (1,548 m2; recorded year 1920 is wrong), roof 41.3 m.
- Estimated: Wall (16.5 m), portico and cupola-stage heights; today's cupola shown from 1848.
- Check: top 41.3 m; plan 1554 m2 vs official 1548 m2 (ratio 1.004; outline 1548 m2, ratio 1.004); centroid offset 0.0 m; city-measured roof 41.3 m; BIN 3000256.
- Sources: https://en.wikipedia.org/wiki/Brooklyn_Borough_Hall · https://s-media.nyc.gov/agencies/lpc/lp/0147.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Unisphere (`unisphere`)

- Years: construction 1963.2 – 1964.3; end 9999. Anchor 40.7464, -73.84505.
- Cited: Wikipedia 'Unisphere' [V]: 140 ft high, 120 ft in diameter, on a 20 ft base; pool 310 ft across. Built 1963-64 [M].
- Measured data: No building footprint; anchor at the centre of the pool.
- Estimated: Land masses (15-degree mask), orbit rings, facing of the globe.
- Check: top 42.71 m; plan 6994 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/Unisphere · https://s-media.nyc.gov/agencies/lpc/lp/1925.pdf

### New York State Pavilion (Tent of Tomorrow and observation towers) (`new_york_state_pavilion`)

- Years: construction 1962.8 – 1964.3; end 9999. Anchor 40.7439, -73.8443.
- Cited: Wikipedia 'New York State Pavilion' [V]: Tent of Tomorrow 250 x 350 ft (or 240 x 320 ft); towers 60 ft (south), 150 ft (north), 226 ft (west).
- Measured data: City footprints BIN 4464054 (tent, 76.0 x 98.7 m, roof 29.6 m), BIN 4541449 (towers, 31.3 m across, roof 64.3 m), BIN 4464056 (Theaterama, roof 17.7 m).
- Estimated: Spacing of the towers inside their footprint, platform size, cable-roof geometry.
- Check: top 68.88 m; plan 7386 m2 vs official 7454 m2 (ratio 0.991; outline 7454 m2, ratio 0.991); centroid offset 2.3 m; city-measured roof 64.3 m; BIN 4541449, 4464056, 4464054.
- Sources: https://en.wikipedia.org/wiki/New_York_State_Pavilion · https://data.cityofnewyork.us/d/5zhs-2jue

### David Geffen Hall (Philharmonic Hall), Lincoln Center (`lincoln_center_geffen_hall`)

- Years: construction 1959.37 – 1962.73; end 9999. Anchor 40.7729, -73.983.
- Cited: Wikipedia 'Metropolitan Opera House (Lincoln Center)' [V]: five concrete arches 96 ft above the plaza. [M]: Philharmonic Hall opened September 23, 1962 (44 columns); New York State Theater April 23, 1964; opera house September 16, 1966.
- Measured data: City footprints BIN 1081023 (Geffen, 4,634 m2, roof 27.4 m), BIN 1028831 (Koch, 4,679 m2, 31.7 m), BIN 1081022 (opera, 7,539 m2, 37.7 m). OSM parts: 24 m colonnades, 25 m opera body, 27 m auditoria.
- Estimated: Arch springing, column spacing, Koch front piers.
- Check: top 27.4 m; plan 4646 m2 vs official 4634 m2 (ratio 1.003; outline 4634 m2, ratio 1.003); centroid offset 0.1 m; city-measured roof 27.4 m; BIN 1081023.
- Sources: https://en.wikipedia.org/wiki/David_Geffen_Hall · https://en.wikipedia.org/wiki/Lincoln_Center · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### David H. Koch Theater (New York State Theater), Lincoln Center (`lincoln_center_koch_theater`)

- Years: construction 1961.9 – 1964.31; end 9999. Anchor 40.7719, -73.9836.
- Cited: Wikipedia 'Metropolitan Opera House (Lincoln Center)' [V]: five concrete arches 96 ft above the plaza. [M]: Philharmonic Hall opened September 23, 1962 (44 columns); New York State Theater April 23, 1964; opera house September 16, 1966.
- Measured data: City footprints BIN 1081023 (Geffen, 4,634 m2, roof 27.4 m), BIN 1028831 (Koch, 4,679 m2, 31.7 m), BIN 1081022 (opera, 7,539 m2, 37.7 m). OSM parts: 24 m colonnades, 25 m opera body, 27 m auditoria.
- Estimated: Arch springing, column spacing, Koch front piers.
- Check: top 31.7 m; plan 4690 m2 vs official 4679 m2 (ratio 1.002; outline 4679 m2, ratio 1.002); centroid offset 0.0 m; city-measured roof 31.7 m; BIN 1028831.
- Sources: https://en.wikipedia.org/wiki/David_H._Koch_Theater · https://en.wikipedia.org/wiki/Lincoln_Center · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Metropolitan Opera House, Lincoln Center (`lincoln_center_metropolitan_opera`)

- Years: construction 1963 – 1966.71; end 9999. Anchor 40.772855, -73.984696.
- Cited: Wikipedia 'Metropolitan Opera House (Lincoln Center)' [V]: five concrete arches 96 ft above the plaza. [M]: Philharmonic Hall opened September 23, 1962 (44 columns); New York State Theater April 23, 1964; opera house September 16, 1966.
- Measured data: City footprints BIN 1081023 (Geffen, 4,634 m2, roof 27.4 m), BIN 1028831 (Koch, 4,679 m2, 31.7 m), BIN 1081022 (opera, 7,539 m2, 37.7 m). OSM parts: 24 m colonnades, 25 m opera body, 27 m auditoria.
- Estimated: Arch springing, column spacing, Koch front piers.
- Check: top 37.7 m; plan 7560 m2 vs official 7539 m2 (ratio 1.003; outline 7539 m2, ratio 1.003); centroid offset 0.1 m; city-measured roof 37.7 m; BIN 1081022.
- Sources: https://en.wikipedia.org/wiki/Metropolitan_Opera_House_(Lincoln_Center) · https://en.wikipedia.org/wiki/Lincoln_Center · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Gould Memorial Library (Bronx Community College, formerly New York University) (`gould_memorial_library`)

- Years: construction 1895.8 – 1899.5; end 9999. Anchor 40.8586, -73.9141.
- Cited: Wikipedia 'Gould Memorial Library' [V]: reading room 54 ft 3 in across inside the colonnade; columns 3 ft 5 in. Dates [M]: 1895-1899.
- Measured data: City footprint BIN 2100243 (1,235 m2), roof 29.9 m.
- Estimated: Walls 14 m, drum 20 m, dome 25 m across above the roof.
- Check: top 29.9 m; plan 1244 m2 vs official 1235 m2 (ratio 1.007; outline 1235 m2, ratio 1.007); centroid offset 0.1 m; city-measured roof 29.9 m; BIN 2100243.
- Sources: https://en.wikipedia.org/wiki/Gould_Memorial_Library · https://s-media.nyc.gov/agencies/lpc/lp/0112.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Hall of Fame for Great Americans (colonnade) (`hall_of_fame_for_great_americans`)

- Years: construction 1900.3 – 1901.41; end 9999. Anchor 40.8586, -73.9141.
- Cited: Wikipedia 'Hall of Fame for Great Americans' [V]: loggia 630 ft long (original section 500 ft). Dedicated May 30, 1901 [M].
- Measured data: City footprints BIN 2096464 (south half and hall, 889 m2, roof 19.5 m) and BIN 2100244 (north, 1,056 m2, 20.7 m): arc of radius 25-30 m about the dome centre.
- Estimated: North half drawn as the mirror of the south (ratio 0.88, centroid 6 m off); colonnade height 6.2 m; end halls are plain blocks.
- Check: top 20.7 m; plan 1711 m2 vs official 1945 m2 (ratio 0.88; outline 1945 m2, ratio 0.88); centroid offset 6.2 m; city-measured roof 20.7 m; BIN 2096464, 2100244.
- Sources: https://en.wikipedia.org/wiki/Hall_of_Fame_for_Great_Americans · https://en.wikipedia.org/wiki/Gould_Memorial_Library · https://s-media.nyc.gov/agencies/lpc/lp/0113.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Brooklyn Museum (Brooklyn Institute of Arts and Sciences) (`brooklyn_museum`)

- Years: construction 1895.7 – 1897.75; end 9999. Anchor 40.670903, -73.963496.
- Cited: Wikipedia 'Brooklyn Museum' [V]: Eastern Parkway front 510 ft; cornice figures 12 ft. Dates [M]: first section 1897, pavilion 1905, east wing 1907, additions to 1927.
- Measured data: City footprint BIN 3029667 (7,716 m2), roof 50.0 m - NOT matched (model 34 m): the figure was not understood.
- Estimated: All heights (walls 24 m, pediment 27.5 m, dome 34 m).
- Check: top 34.0 m; plan 7736 m2 vs official 7716 m2 (ratio 1.003; outline 7716 m2, ratio 1.003); centroid offset 0.0 m; city-measured roof 50.0 m; BIN 3029667.
- Sources: https://en.wikipedia.org/wiki/Brooklyn_Museum · https://s-media.nyc.gov/agencies/lpc/lp/0155.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Brooklyn Academy of Music (Peter Jay Sharp Building) (`brooklyn_academy_of_music`)

- Years: construction 1906.5 – 1908.87; end 9999. Anchor 40.68645, -73.9779.
- Cited: No published dimension was verified. Opened November 1908 [M].
- Measured data: City footprint BIN 3059185 (3,130 m2), roof 21.7 m.
- Estimated: Front composition and levels.
- Check: top 21.7 m; plan 3230 m2 vs official 3130 m2 (ratio 1.032; outline 3130 m2, ratio 1.032); centroid offset 0.9 m; city-measured roof 21.7 m; BIN 3059185.
- Sources: https://en.wikipedia.org/wiki/Brooklyn_Academy_of_Music · https://data.cityofnewyork.us/d/5zhs-2jue

### Yankee Stadium (2009) (`yankee_stadium_2009`)

- Years: construction 2006.63 – 2009.25; end 9999. Anchor 40.8296, -73.9264.
- Cited: Wikipedia 'Yankee Stadium' [V]: fences 318 / 399 / 408 / 385 / 314 ft. Dates [M]: ground broken August 16, 2006; opened April 2009.
- Measured data: City footprint BIN 2114490 (outline 47,410 m2; 34,903 m2 without the field), roof 36.6 m. OSM pitch polygons for the field and infield.
- Estimated: Outfield stand height (13 m), seating slope, frieze (3 m), scoreboard.
- Check: top 39.6 m; plan 47450 m2 vs official 34903 m2 (ratio 1.359; outline 47410 m2, ratio 1.001); centroid offset 7.2 m; city-measured roof 36.6 m; BIN 2114490.
- Sources: https://en.wikipedia.org/wiki/Yankee_Stadium · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Citi Field (`citi_field`)

- Years: construction 2006.87 – 2009.25; end 9999. Anchor 40.7571, -73.84575.
- Cited: Wikipedia 'Citi Field' [V]: rotunda floor 160 ft across. Dates [M]: ground broken November 13, 2006; opened April 2009.
- Measured data: City footprint BIN 4536844 (outline 47,201 m2), roof 24.3 m (not used as the rim). OSM pitch polygon.
- Estimated: Stand heights (36 m / 14 m), rotunda 21 m, scoreboard.
- Check: top 36.0 m; plan 47314 m2 vs official 34708 m2 (ratio 1.363; outline 47201 m2, ratio 1.002); centroid offset 3.4 m; city-measured roof 24.3 m; BIN 4536844.
- Sources: https://en.wikipedia.org/wiki/Citi_Field · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Barclays Center (`barclays_center`)

- Years: construction 2010.19 – 2012.72; end 9999. Anchor 40.68265, -73.9752.
- Cited: Wikipedia 'Barclays Center' [V]: oculus 117 x 56 ft. Dates [M]: ground broken March 11, 2010; opened September 21, 2012.
- Measured data: City footprint BIN 3398156 (18,501 m2), roof 42.1 m.
- Estimated: Band profile, canopy size and position.
- Check: top 42.1 m; plan 19069 m2 vs official 18501 m2 (ratio 1.031; outline 18501 m2, ratio 1.031); centroid offset 2.2 m; city-measured roof 42.1 m; BIN 3398156.
- Sources: https://en.wikipedia.org/wiki/Barclays_Center · https://data.cityofnewyork.us/d/5zhs-2jue

### Arthur Ashe Stadium (`arthur_ashe_stadium`)

- Years: construction 1995.3 – 1997.65; end 9999. Anchor 40.7499, -73.8469.
- Cited: Wikipedia 'Arthur Ashe Stadium' [V]: roof superstructure 5,000 tons; two 800-ton fabric panels, 210,000 sq ft. No height was found. Opened August 25, 1997; roof 2016 [M].
- Measured data: City footprint BIN 4467715 (16,560 m2 octagon, 137.9 x 138.1 m), roof 17.7 m (not the top of the stands). OSM court polygon.
- Estimated: Bowl height 36 m; roof height 62 m, 76 m opening, column positions - all from photographs.
- Check: top 36.0 m; plan 16564 m2 vs official 16560 m2 (ratio 1.0; outline 16560 m2, ratio 1.0); centroid offset 0.0 m; city-measured roof 17.7 m; BIN 4467715.
- Sources: https://en.wikipedia.org/wiki/Arthur_Ashe_Stadium · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Arthur Ashe Stadium — retractable roof (`arthur_ashe_stadium_roof`)

- Years: construction 2013.6 – 2016.6; end 9999. Anchor 40.7499, -73.8469.
- Cited: Wikipedia 'Arthur Ashe Stadium' [V]: roof superstructure 5,000 tons; two 800-ton fabric panels, 210,000 sq ft. No height was found. Opened August 25, 1997; roof 2016 [M].
- Measured data: City footprint BIN 4467715 (16,560 m2 octagon, 137.9 x 138.1 m), roof 17.7 m (not the top of the stands). OSM court polygon.
- Estimated: Bowl height 36 m; roof height 62 m, 76 m opening, column positions - all from photographs.
- Check: top 62.0 m; plan 18644 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/Arthur_Ashe_Stadium · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Wonder Wheel (`wonder_wheel`)

- Years: construction 1918.5 – 1920.4; end 9999. Anchor 40.5742, -73.9791.
- Cited: Wikipedia 'Wonder Wheel' [V]: 150 ft tall, 200 tons; built 1918-1920; opened May 30, 1920.
- Measured data: City footprint BIN 3347224 (platform, 293 m2).
- Estimated: Wheel diameter 42.6 m, support frame, car positions.
- Check: top 45.97 m; plan 354 m2 vs official 293 m2 (ratio 1.208; outline 293 m2, ratio 1.208); centroid offset 0.0 m; city-measured roof 4.3 m; BIN 3347224.
- Sources: https://en.wikipedia.org/wiki/Wonder_Wheel · https://s-media.nyc.gov/agencies/lpc/lp/1708.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Coney Island Cyclone (`coney_island_cyclone`)

- Years: construction 1927.1 – 1927.49; end 9999. Anchor 40.5749, -73.9777.
- Cited: Wikipedia 'Coney Island Cyclone' [V]: track 2,640 ft, six fan turns, twelve drops; height 75 ft (note: some sources give 85 ft). Opened June 26, 1927 [M].
- Measured data: City footprint BIN 3326898 (site, 2,541 m2).
- Estimated: The course of the track (schematic). Skeletal structure: plan area not comparable with the site.
- Check: top 22.85 m; plan 733 m2 vs official 2541 m2 (ratio 0.289; outline 2541 m2, ratio 0.289); centroid offset 7.5 m; city-measured roof 6.4 m; BIN 3326898.
- Sources: https://en.wikipedia.org/wiki/Coney_Island_Cyclone · https://s-media.nyc.gov/agencies/lpc/lp/1636.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Parachute Jump (`parachute_jump`)

- Years: construction 1941 – 1941.4; end 9999. Anchor 40.572977, -73.984397.
- Cited: Wikipedia 'Parachute Jump' [V]: 250 ft tall, 170 tons; ribs at 7 ft intervals. Re-erected at Coney Island 1941 [M].
- Measured data: OSM position (building 'Parachute Jump'); city footprint BIN 3404019 (base pavilion, 189 m2).
- Estimated: Taper of the tower (6 m to 1.5 m radius), reach of the arms (14.5 m).
- Check: top 76.3 m; plan 252 m2 vs official 189 m2 (ratio 1.331; outline 189 m2, ratio 1.331); centroid offset 0.0 m; city-measured roof 10.1 m; BIN 3404019.
- Sources: https://en.wikipedia.org/wiki/Parachute_Jump · https://s-media.nyc.gov/agencies/lpc/lp/1638.pdf · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Little Red Lighthouse (Jeffrey's Hook Light) (`little_red_lighthouse`)

- Years: construction 1921 – 1921.8; end 9999. Anchor 40.850255, -73.946963.
- Cited: No published dimension was verified in text (usually described as 40 ft). Dates [M]: cast 1880, moved to Jeffrey's Hook 1921.
- Measured data: OSM building 'Little Red Lighthouse': position, height 12.0 m. No city footprint.
- Estimated: Base diameter and stages.
- Check: top 12.0 m; plan 22 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/Little_Red_Lighthouse · https://s-media.nyc.gov/agencies/lpc/lp/1654.pdf · https://www.openstreetmap.org/

### Coney Island Light (`coney_island_light`)

- Years: construction 1889.5 – 1890.58; end 9999. Anchor 40.576605, -74.011763.
- Cited: Wikipedia 'Coney Island Light' [V]: focal height 75 ft; skeletal white tower with black trim. First lit August 1, 1890 [M].
- Measured data: OSM building 'Coney Island Lighthouse': position, height 22.9 m. No city footprint.
- Estimated: Leg spread, watch-room size.
- Check: top 22.9 m; plan 28 m2; no footprint of its own.
- Sources: https://en.wikipedia.org/wiki/Coney_Island_Light · https://www.openstreetmap.org/

### Blackwell Island Light (Roosevelt Island Lighthouse) (`blackwell_island_light`)

- Years: construction 1872 – 1872.8; end 9999. Anchor 40.7727, -73.9402.
- Cited: Wikipedia 'Blackwell Island Light' [V]: about 50 ft tall, grey gneiss. Built 1872 [M].
- Measured data: City footprint BIN 1090953 (13 m2 octagon, 4.0 m across), roof 17.4 m (model 15.24 m = the cited 50 ft).
- Estimated: Gallery and lantern stages.
- Check: top 15.24 m; plan 16 m2 vs official 13 m2 (ratio 1.218; outline 13 m2, ratio 1.218); centroid offset 0.1 m; city-measured roof 17.4 m; BIN 1090953.
- Sources: https://en.wikipedia.org/wiki/Blackwell_Island_Light · https://s-media.nyc.gov/agencies/lpc/lp/0911.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Castle Williams (Governors Island) (`castle_williams`)

- Years: construction 1807.5 – 1811.9; end 9999. Anchor 40.692826, -74.01934.
- Cited: Wikipedia 'Castle Williams' [V]: 40 ft high, 210 ft in diameter, walls 7 to 8 ft thick. Built 1807-1811 [M].
- Measured data: City footprint BIN 1086428 (outline 3,097 m2, walls 2,126 m2), roof 14.9 m.
- Estimated: Embrasure positions; parapet between 12.2 m and 14.9 m.
- Check: top 14.9 m; plan 3043 m2 vs official 2126 m2 (ratio 1.431; outline 3097 m2, ratio 0.983); centroid offset 0.6 m; city-measured roof 14.9 m; BIN 1086428.
- Sources: https://en.wikipedia.org/wiki/Castle_Williams · https://www.nps.gov/gois/learn/historyculture/castle-williams.htm · https://s-media.nyc.gov/agencies/lpc/lp/0542.pdf · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Battery Weed (Fort Richmond), Fort Wadsworth (`battery_weed`)

- Years: construction 1847.5 – 1864; end 9999. Anchor 40.605511, -74.054172.
- Cited: No published dimension was verified. Built 1847-1864 [M].
- Measured data: City footprint BIN 5163514 (2,783 m2), roof 17.1 m; OSM 13.6 m.
- Estimated: Tier levels not modelled; plain walls at the measured height.
- Check: top 17.1 m; plan 2786 m2 vs official 2783 m2 (ratio 1.001; outline 2783 m2, ratio 1.001); centroid offset 0.2 m; city-measured roof 17.1 m; BIN 5163514.
- Sources: https://en.wikipedia.org/wiki/Fort_Wadsworth · https://www.nps.gov/gate/learn/historyculture/fort-wadsworth.htm · https://s-media.nyc.gov/agencies/lpc/lp/0379.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Fort Tompkins, Fort Wadsworth (`fort_tompkins`)

- Years: construction 1859 – 1876; end 9999. Anchor 40.60503, -74.056521.
- Cited: No published dimension was verified. Built 1859-1876 [M].
- Measured data: City footprint BIN 5157556 (outline 13,461 m2, 7,551 m2 without the parade), roof 15.5 m.
- Estimated: Shape of the parade (the outline shrunk about its centroid).
- Check: top 15.5 m; plan 13464 m2 vs official 7551 m2 (ratio 1.783; outline 13461 m2, ratio 1.0); centroid offset 4.7 m; city-measured roof 15.5 m; BIN 5157556.
- Sources: https://en.wikipedia.org/wiki/Fort_Wadsworth · https://s-media.nyc.gov/agencies/lpc/lp/0824.pdf · https://data.cityofnewyork.us/d/5zhs-2jue · https://www.openstreetmap.org/

### Fort Hamilton (the casemate fort of 1831) (`fort_hamilton_casemate_fort`)

- Years: construction 1825.45 – 1831.85; end 9999. Anchor 40.608817, -74.032489.
- Cited: Wikipedia 'Fort Hamilton' [V]: built 1825-1831.
- Measured data: City footprint BIN 3345704 (4,008 m2), roof 15.2 m.
- Estimated: Drawn as a plain 8 m block; height not verified.
- Check: top 8.0 m; plan 3826 m2 vs official 4008 m2 (ratio 0.955; outline 4008 m2, ratio 0.955); centroid offset 0.8 m; city-measured roof 15.2 m; BIN 3345704.
- Sources: https://en.wikipedia.org/wiki/Fort_Hamilton · https://s-media.nyc.gov/agencies/lpc/lp/0953.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Pieter Claesen Wyckoff House (`wyckoff_house`)

- Years: construction 1651 – 1652.5; end 9999. Anchor 40.6444, -73.9208.
- Cited: No published dimension was verified. About 1652 [M].
- Measured data: City footprint BIN 3221967 (205 m2), roof 7.5 m.
- Estimated: Eaves, lower wing; chimneys rise 0.9 m above the measured ridge.
- Check: top 8.4 m; plan 226 m2 vs official 205 m2 (ratio 1.106; outline 205 m2, ratio 1.106); centroid offset 0.0 m; city-measured roof 7.5 m; BIN 3221967.
- Sources: https://en.wikipedia.org/wiki/Wyckoff_House · https://s-media.nyc.gov/agencies/lpc/lp/0001.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Conference House (Billopp House) (`conference_house`)

- Years: construction 1675 – 1680; end 9999. Anchor 40.503129, -74.25322.
- Cited: No published dimension was verified. About 1680 [M].
- Measured data: City footprint BIN 5087656 (190 m2, 13.5 x 14.1 m), roof 11.8 m.
- Estimated: Eaves height; chimneys rise 0.9 m above the measured ridge.
- Check: top 12.7 m; plan 208 m2 vs official 190 m2 (ratio 1.098; outline 190 m2, ratio 1.098); centroid offset 0.0 m; city-measured roof 11.8 m; BIN 5087656.
- Sources: https://en.wikipedia.org/wiki/Conference_House · https://s-media.nyc.gov/agencies/lpc/lp/0393.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Morris–Jumel Mansion (`morris_jumel_mansion`)

- Years: construction 1765 – 1765.9; end 9999. Anchor 40.83445, -73.938574.
- Cited: Wikipedia 'Morris-Jumel Mansion' [V]: octagonal annex at the rear. Built 1765 [M].
- Measured data: City footprint BIN 1084189 (308 m2), roof 11.6 m.
- Estimated: Eaves, roof, portico levels.
- Check: top 11.6 m; plan 312 m2 vs official 308 m2 (ratio 1.012; outline 308 m2, ratio 1.012); centroid offset 0.8 m; city-measured roof 11.6 m; BIN 1084189.
- Sources: https://en.wikipedia.org/wiki/Morris%E2%80%93Jumel_Mansion · https://s-media.nyc.gov/agencies/lpc/lp/0308.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Dyckman Farmhouse (`dyckman_farmhouse`)

- Years: construction 1783.5 – 1785; end 9999. Anchor 40.8674, -73.9228.
- Cited: Wikipedia 'Dyckman House' [V]: built c. 1783-1785.
- Measured data: City footprint BIN 1075616 (213 m2, 13.6 x 18.0 m), roof 8.6 m.
- Estimated: Gambrel profile; the porch roof overhangs the footprint (ratio 1.16).
- Check: top 9.4 m; plan 247 m2 vs official 213 m2 (ratio 1.161; outline 213 m2, ratio 1.161); centroid offset 0.9 m; city-measured roof 8.6 m; BIN 1075616.
- Sources: https://en.wikipedia.org/wiki/Dyckman_House · https://s-media.nyc.gov/agencies/lpc/lp/0309.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

### Gracie Mansion (`gracie_mansion`)

- Years: construction 1799 – 1799.9; end 9999. Anchor 40.776104, -73.943054.
- Cited: No published dimension was verified. Built 1799; Wagner Wing 1966 [M].
- Measured data: City footprint BIN 1085796 (778 m2), roof 12.6 m.
- Estimated: Eaves, roofs, porch; the 1966 wing is shown from 1799.
- Check: top 12.6 m; plan 788 m2 vs official 778 m2 (ratio 1.012; outline 778 m2, ratio 1.012); centroid offset 0.1 m; city-measured roof 12.6 m; BIN 1085796.
- Sources: https://en.wikipedia.org/wiki/Gracie_Mansion · https://s-media.nyc.gov/agencies/lpc/lp/0179.pdf · https://data.cityofnewyork.us/d/5zhs-2jue

## Not modelled

- **Fort Jay** (Governors Island): its four barracks are ordinary footprints; the star-shaped scarp and moat are not in the footprint or Overture extracts, and no measured outline was found — it needs a traced plan (HABS or the NPS site plan).
- **Carnegie Hall** and **Radio City Music Hall**: boxy buildings whose footprint extrusions are close to right; the widths of Carnegie Hall's three parts (main hall 150 x 175 ft, 16-storey east wing, 13-storey south wing — Wikipedia) could not be placed inside its single footprint without guessing.
- The states of the Metropolitan Museum before 1902 and the phases of the American Museum of Natural History; the Hayden Planetarium of 1935 and Ellis Island's station of 1892 (demolished or burned — other files).

