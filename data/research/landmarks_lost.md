# Lost landmarks — research notes

Models: `viewer/src/landmarks/nyc-lost.ts` (47 landmark objects). Table: `data/tables/landmarks_lost.csv`.

Every model stands on a real site: an outline traced in OpenHistoricalMap (OHM, CC0 — its tracings of the Castello Plan, Sanborn 1905, Bromley 1930 and the "Map of City Hall Park"), today's lot from the city footprints, or street lines from the Overture road centre lines (avenues 100 ft, cross streets 60 ft unless noted). Dimensions come from the Wikipedia articles (CC BY-SA; article URL given), the architects' description of the Crystal Palace (public domain, archive.org), NIST NCSTAR 1 (US government) and a few web pages named below. Raw downloads: `data/raw/landmarks_lost/` (OHM Overpass extracts `ohm_named.json`, `ohm_more.json`, `ohm_pitch.json`; Wikipedia wikitext `wp/`; `cp_carstensen.txt`; `img/fairmap.jpg`).

What "as reported by a web search" means: the figure was returned by a search summary and the page itself was not opened. "Recalled" means the figure is from memory and has no checked source — it is flagged in the model's facts or only used for a date.

## Numeric checks

Site = area of the `replaces` outline(s) in the model. Cited plot = area implied by the cited dimensions. Top = highest vertex of the mesh (flagpoles and finials included). Produced by `data/interim/landmarks_lost/make_docs.py` from the built meshes.

| id | conf. | site m² | cited plot m² | Δ | mesh top m | cited height m | Δ m | cited height is |
|---|---|---:|---:|---:|---:|---:|---:|---|
| wtc_1_north_tower | HIGH | 4277 | 4010 | +7% | 417.0 | 417.0 | +0.1 | roof 1,368 ft |
| wtc_2_south_tower | HIGH | 4277 | 4010 | +7% | 415.2 | 415.1 | +0.1 | roof 1,362 ft |
| wtc_1_antenna | MEDIUM | 0 | – |  | 527.3 | 527.3 | -0.0 | tip 1,730 ft (roof 1,368 + mast 362 ft; infobox 1,728 ft) |
| wtc_tobin_plaza | MEDIUM | 58707 | 64750 | -9% | 9.0 | – (estimated) |  |  |
| wtc_3_marriott | MEDIUM | 2926 | – |  | 73.8 | 73.7 | +0.0 | roof 73.7 m (242 ft) |
| wtc_4_1975 | MEDIUM | 6310 | – |  | 36.0 | 36.0 | +0.1 | 118 ft |
| wtc_5_1972 | MEDIUM | 8435 | 11148 | -24% | 36.0 | 36.0 | +0.1 | 118 ft |
| wtc_6_1973 | MEDIUM | 6680 | – |  | 33.6 | 33.5 | +0.1 | 110 ft (complex infobox; OHM tags 28 m) |
| wtc_7_1987 | MEDIUM | 3548 | 4292 | -17% | 186.0 | 185.9 | +0.1 | 610 ft |
| penn_station_1910 | MEDIUM | 33718 | 31546 | +7% | 46.6 | 46.6 | -0.0 | maximum height 153 ft (waiting-room roof) |
| singer_building_1908 | MEDIUM | 2238 | – |  | 205.4 | 186.5 | +18.9 | top of lantern 612 ft (flagpole to 674 ft) |
| city_investing_building_1908 | LOW | 1734 | 2479 | -30% | 148.1 | 148.1 | -0.0 | 486 ft above Broadway |
| crystal_palace_1853 | HIGH | 21830 | – |  | 37.5 | 37.5 | -0.0 | dome crown about 123 ft (springing 71 ft + 50 ft radius = 121 ft by the architects) |
| latting_observatory_1853 | LOW | 618 | 523 | +18% | 96.0 | 96.0 | -0.0 | 315 ft |
| latting_observatory_1855 | LOW | 618 | 523 | +18% | 73.2 | 73.2 | -0.0 | 315 - 75 = 240 ft |
| croton_distributing_reservoir | HIGH | 15691 | 16187 | -3% | 18.2 | 15.2 | +3.0 | walls 50 ft |
| madison_square_garden_1890 | LOW | 7424 | 9012 | -18% | 96.6 | 92.7 | +4.0 | tower 304 ft to the observation deck |
| madison_square_garden_1925 | LOW | 8964 | 6968 | +29% | 26.5 | – (estimated) |  |  |
| polo_grounds_1911 | LOW | 26805 | – |  | 23.0 | – (estimated) |  |  |
| polo_grounds_1923 | LOW | 26805 | – |  | 23.0 | – (estimated) |  |  |
| ebbets_field_1913 | LOW | 22108 | – |  | 27.0 | – (estimated) |  |  |
| yankee_stadium_1923 | MEDIUM | 32952 | 32375 | +2% | 35.7 | 35.7 | -0.0 | frieze "117 feet high" (one secondary source) |
| yankee_stadium_1976 | LOW | 32952 | 32375 | +2% | 35.7 | – (estimated) |  |  |
| shea_stadium_1964 | LOW | 42829 | – |  | 34.0 | – (estimated) |  |  |
| fort_amsterdam | LOW | 5728 | – |  | 20.5 | – (estimated) |  |  |
| fort_amsterdam_church_1642 | MEDIUM | 348 | 348 | +0% | 17.4 | 4.9 | +12.5 | walls 16 ft above the ground (1642 contract) |
| stadt_huys_1642 | LOW | 203 | 203 | +0% | 19.4 | – (estimated) |  |  |
| wall_street_palisade_1653 | MEDIUM | 0 | – |  | 4.7 | 2.7 | +1.9 | 9 ft |
| trinity_church_1698 | MEDIUM | 1017 | 1038 | -2% | 54.9 | 54.9 | -0.0 | spire 180 ft |
| trinity_church_1790 | MEDIUM | 867 | – |  | 61.0 | 61.0 | +0.0 | 200 ft |
| city_hall_wall_street_1703 | LOW | 419 | – |  | 21.5 | – (estimated) |  |  |
| federal_hall_1789 | LOW | 419 | – |  | 27.5 | – (estimated) |  |  |
| government_house_1790 | LOW | 798 | – |  | 14.0 | – (estimated) |  |  |
| the_tombs_1838 | MEDIUM | 4715 | 4715 | +0% | 14.0 | – (estimated) |  |  |
| bridewell_1775 | LOW | 402 | – |  | 12.6 | – (estimated) |  |  |
| almshouse_1797 | LOW | 1397 | – |  | 15.8 | – (estimated) |  |  |
| kings_college_hall_1760 | LOW | 573 | 502 | +14% | 21.9 | – (estimated) |  |  |
| park_theatre_1798 | MEDIUM | 942 | 1226 | -23% | 18.5 | – (estimated) |  |  |
| hippodrome_1905 | LOW | 4415 | – |  | 38.6 | – (estimated) |  |  |
| metropolitan_opera_house_1883 | LOW | 4590 | – |  | 37.0 | – (estimated) |  |  |
| world_building_1890 | MEDIUM | 1831 | 1718 | +7% | 106.7 | 94.5 | +12.2 | dome 310 ft (pinnacle 350 ft, flat roof 191 ft) |
| tribune_building_1875 | MEDIUM | 1454 | – |  | 79.2 | 79.2 | +0.0 | tower 260 ft (roof 155 ft) |
| tribune_building_1905 | MEDIUM | 1454 | – |  | 102.1 | 102.1 | +0.0 | finial 335 ft (roof 231 ft, tower 273 ft) |
| equitable_life_building_1870 | LOW | 4452 | – |  | 52.4 | 52.4 | +0.0 | final height perhaps 172 ft (155 ft after 1885-87; 130-142 ft in 1870) |
| grand_central_depot_1871 | LOW | 16077 | – |  | 36.0 | 30.5 | +5.5 | shed crown 100 ft (the mansard towers above it are estimated) |
| grand_central_station_1900 | LOW | 16077 | – |  | 46.0 | 30.5 | +15.5 | shed crown 100 ft (the mansard towers above it are estimated) |
| trylon_perisphere_1939 | MEDIUM | 9166 | – |  | 185.9 | 185.9 | +0.0 | Trylon 610 ft (the sphere is drawn 54.86 m = 180 ft across) |

Reading the table: where the mesh top exceeds the cited height the difference is a flagpole, finial, statue or lantern named in the model (Singer +18.9 m flagpole; World +12.2 m pinnacle to the cited 350 ft; Madison Square Garden +4 m Diana; Grand Central towers; the church turret; Trinity spires are the cited height itself). Site differences: the Twin Towers' `replaces` is the plan + 1 m; Penn Station's is the block, 7 % larger than the building; 5 and 7 WTC are 19–24 % smaller in OHM than the cited floor plates; City Investing −30 % (LOW); MSG II −18 % because the cited 485 ft cannot fit the 412 ft block; Park Theatre −23 % and College Hall +14 % (OHM tracings against the usual descriptions); the Yankee Stadium outline is within 2 % of the cited 8 acres; the Wall measures 713 m against the cited 2,340 ft (713.2 m). Tops above a cited height that is not the top: the Croton reservoir's corner pylons (+3 m over the 50 ft walls, estimated), the fort church's roofs and turret over its 16 ft walls, the Wall's gate posts over the 9 ft palisade, the Latting and Twin Tower sites are the plan + 1 m, MSG III's site is the whole lot (the arena is the cited 375 ft of it), the Trylon and Perisphere's site is a 52 m circle round the sphere and a 16 m circle round the Trylon.

## Street check

`data/interim/landmarks_lost/street_check.py` intersects every site outline (shrunk 3 m) with today's 192,259 Overture street centre lines. Streets run inside only where history says they should: Fulton and Greenwich streets through the World Trade Center superblock and the sites of 4, 5, 6 and 7 WTC (reopened after 2001); State Street (58 m) and Battery Place (17 m) across the west bastions of Fort Amsterdam (laid out after 1790); the Park Row / Brooklyn Bridge approach (50–58 m) through the World Building (demolished for it in 1955); the Park Avenue viaduct (263 m) through Grand Central Depot. No other outline is crossed by a street: Penn Station, the Singer and City Investing buildings, the Equitable, the Opera House, the Hippodrome, both Gardens, the Tombs, the ballparks, the colonial buildings and the rest all sit inside present blocks.

Other position checks: the Twin Tower centres equal the centroids of the 9/11 Memorial pools to 0.1 m; the Croton reservoir outline (OHM) and the New York Public Library footprint share a centroid to 1 m; the Tombs rectangle is centred 11 m from the centroid of Collect Pond Park; Yankee Stadium's cited foul lines (281 / 295 ft) end within 5 m of the mapped stands from the derived home plate.

## Per landmark

### One World Trade Center (North Tower, 1972–2001) — `wtc_1_north_tower` — HIGH

- Years: construction 1968.6, complete 1972, gone 2001.69. Anchor 40.712139, -74.013175.
- Site outline: centre = centroid of OHM way 198201501 = centroid of the 9/11 Memorial North Pool (Overture base_water), to 0.1 m; faces at 29.3° from the OHM outline; `replaces` is the tower square + 1 m.
- Dimension: roof 1,368 ft (417 m); 110 storeys; construction 6 Aug 1968, topped out 23 Dec 1970 — https://en.wikipedia.org/wiki/World_Trade_Center_(1973%E2%80%932001)
- Dimension: plan "approximately 208 ft" square — https://en.wikipedia.org/wiki/World_Trade_Center_(1973%E2%80%932001)
- Dimension: "The footprint of each tower was a square, about 210 ft on a side ..., with the corners of the tower beveled 9 ft 9 in. Internally, each floor was a square, about 206 ft on a side"; 59 columns on each face; roof of WTC 1 1,368 ft, 6 ft taller than WTC 2; antenna mast 360 ft — https://doi.org/10.6028/NIST.NCSTAR.1 (sec. 1.2.2, read in the PDF)
- Dimension: OHM draws the tower only 58.5 m square (3,393 m2): the cited 63.1 m was used — https://www.openhistoricalmap.org/way/198201501
- Estimated: lobby height 72 ft (six 12-ft storeys); levels of the four mechanical-floor bands (from the floor numbers 7-8, 41-42, 75-76, 108-110); every other window bay drawn.
- Sources in the model: https://en.wikipedia.org/wiki/World_Trade_Center_(1973%E2%80%932001), https://www.openhistoricalmap.org/way/198201501, https://doi.org/10.6028/NIST.NCSTAR.1

### Two World Trade Center (South Tower, 1973–2001) — `wtc_2_south_tower` — HIGH

- Years: construction 1969.05, complete 1973, gone 2001.69. Anchor 40.711030, -74.013082.
- Site outline: centre = centroid of OHM way 198201503 = centroid of the Memorial South Pool; same orientation.
- Dimension: roof 1,362 ft (415 m); construction Jan 1969, topped out 19 Jul 1971 — https://en.wikipedia.org/wiki/World_Trade_Center_(1973%E2%80%932001)
- Dimension: plan as 1 WTC; 6 ft lower than WTC 1 — https://doi.org/10.6028/NIST.NCSTAR.1
- Estimated: as 1 WTC.
- Sources in the model: https://en.wikipedia.org/wiki/World_Trade_Center_(1973%E2%80%932001), https://www.openhistoricalmap.org/way/198201503, https://doi.org/10.6028/NIST.NCSTAR.1

### One World Trade Center antenna mast — `wtc_1_antenna` — MEDIUM

- Years: construction 1978.4, complete 1979.45, gone 2001.69. Anchor 40.712139, -74.013175.
- Site outline: on 1 WTC.
- Dimension: 362 ft mast, added 1978-79 (in service late May - early June 1979), tip 1,730 ft — https://en.wikipedia.org/wiki/World_Trade_Center_(1973%E2%80%932001)
- Dimension: mast 360 ft — https://doi.org/10.6028/NIST.NCSTAR.1
- Estimated: mast widths and its base.
- Sources in the model: https://en.wikipedia.org/wiki/World_Trade_Center_(1973%E2%80%932001)

### World Trade Center plaza (Austin J. Tobin Plaza) — `wtc_tobin_plaza` — MEDIUM

- Years: construction 1966.22, complete 1973.26, gone 2001.69. Anchor 40.712139, -74.013175.
- Site outline: `replaces` = convex hull of the OHM outlines of 1-6 WTC (so nothing from the street grid survives inside it from the 1966 clearance); paving and fountain from OHM relation 2965688.
- Dimension: 16-acre superblock; 5-acre plaza; Radio Row demolition from 21 Mar 1966; dedicated 4 Apr 1973 — https://en.wikipedia.org/wiki/World_Trade_Center_(1973%E2%80%932001)
- Dimension: The Sphere (Fritz Koenig) in the fountain — https://en.wikipedia.org/wiki/Austin_J._Tobin_Plaza
- Estimated: the Sphere is a plain globe; plaza drawn 0.4 m thick.
- Sources in the model: https://en.wikipedia.org/wiki/Austin_J._Tobin_Plaza, https://www.openhistoricalmap.org/relation/2965688, https://en.wikipedia.org/wiki/World_Trade_Center_(1973%E2%80%932001)

### Marriott World Trade Center (Three World Trade Center; Vista International Hotel, 1981–2001) — `wtc_3_marriott` — MEDIUM

- Years: construction 1979.2, complete 1981.5, gone 2001.69. Anchor 40.711354, -74.013690.
- Site outline: OHM way 198590238 (2,925 m2).
- Dimension: roof 73.7 m, 22 storeys; Mar 1979 - 1 Jul 1981 — https://en.wikipedia.org/wiki/Marriott_World_Trade_Center
- Estimated: none beyond the plain extrusion with storey bands.
- Sources in the model: https://en.wikipedia.org/wiki/Marriott_World_Trade_Center, https://www.openhistoricalmap.org/way/198590238

### Four World Trade Center (Southeast Plaza Building, 1975–2001) — `wtc_4_1975` — MEDIUM

- Years: construction 1972.5, complete 1975.5, gone 2001.69. Anchor 40.710661, -74.012132.
- Site outline: OHM way 198590237 (6,310 m2).
- Dimension: nine storeys, 118 ft (36 m); c. 1972-1975, opened Jan 1977 — https://en.wikipedia.org/wiki/4_World_Trade_Center_(1975%E2%80%932001)
- Estimated: plain extrusion.
- Sources in the model: https://en.wikipedia.org/wiki/4_World_Trade_Center_(1975%E2%80%932001), https://www.openhistoricalmap.org/way/198590237

### Five World Trade Center (Northeast Plaza Building, 1972–2001) — `wtc_5_1972` — MEDIUM

- Years: construction 1970, complete 1972.2, gone 2001.69. Anchor 40.711974, -74.011413.
- Site outline: OHM way 198590239 (L-shape, bounding box 125.8 x 95.7 m against the cited 420 x 330 ft = 128.0 x 100.6 m).
- Dimension: 118 ft, nine storeys; 330 x 420 ft overall, 120,000 sq ft per floor; 1970-72 — https://en.wikipedia.org/wiki/5_World_Trade_Center
- Estimated: plain extrusion.
- Sources in the model: https://en.wikipedia.org/wiki/5_World_Trade_Center, https://www.openhistoricalmap.org/way/198590239

### Six World Trade Center (US Custom House, 1973–2001) — `wtc_6_1973` — MEDIUM

- Years: construction 1969, complete 1973.5, gone 2001.69. Anchor 40.712780, -74.012858.
- Site outline: OHM way 198590240 (6,680 m2).
- Dimension: 6 WTC: 110 ft, eight storeys, construction from 1969 — https://en.wikipedia.org/wiki/World_Trade_Center_(1973%E2%80%932001)
- Estimated: plain extrusion; completion 1973.5 from "1973".
- Sources in the model: https://en.wikipedia.org/wiki/World_Trade_Center_(1973%E2%80%932001), https://www.openhistoricalmap.org/way/198590240

### Seven World Trade Center (1987–2001) — `wtc_7_1987` — MEDIUM

- Years: construction 1984.75, complete 1987.2, gone 2001.69. Anchor 40.713286, -74.011900.
- Site outline: OHM way 198590241 (trapezoid 95.2 x 42.3 m).
- Dimension: 610 ft, 47 storeys, trapezoid 330 ft long and 140 ft wide; 2 Oct 1984 - Mar 1987 — https://en.wikipedia.org/wiki/7_World_Trade_Center_(1987%E2%80%932001)
- Estimated: plain extrusion.
- Sources in the model: https://en.wikipedia.org/wiki/7_World_Trade_Center_(1987%E2%80%932001), https://www.openhistoricalmap.org/way/198590241

### Pennsylvania Station (1910–1963) — `penn_station_1910` — MEDIUM

- Years: construction 1904.5, complete 1910.9, gone 1963.83. Anchor 40.750298, -73.992949.
- Site outline: `replaces` = the two blocks between street lines: Overture centre lines of 7th/8th Av (273.5 m apart) less 100 ft, of 31st/33rd St (156.9 m apart) less 60 ft = 243.1 x 138.7 m; the building is centred in it (1.3 m and 3.7 m margins). OHM way 198645203 (Bromley land book) measures 237.1 x 132.7 m, 30,144 m2.
- Dimension: 788.75 x 430.5 ft (also 788 x 432 and 780 x 430); average height 69 ft, maximum 153 ft — https://en.wikipedia.org/wiki/Pennsylvania_Station_(1910%E2%80%931963)
- Dimension: General Waiting Room 314 ft 4 in x 108 ft 8 in x 150 ft; lunettes 38 ft 4 in radius — https://en.wikipedia.org/wiki/Pennsylvania_Station_(1910%E2%80%931963)
- Dimension: Concourse glass roof 210 x 340 ft; arcade 225 x 45 ft; carriageways 63 ft wide; side colonnades 230 ft; columns 35 ft x 4.5 ft; clock 61 ft above the sidewalk — https://en.wikipedia.org/wiki/Pennsylvania_Station_(1910%E2%80%931963)
- Dimension: men's and women's waiting rooms 100 x 58 ft; exit concourse 60 ft — https://en.wikipedia.org/wiki/Pennsylvania_Station_(1910%E2%80%931963)
- Estimated: order of the rooms along the axis is real, their exact east-west positions are not (the arcade is started 13 m inside the front); depth of the perimeter ranges (17 m); eaves of the waiting room (37.5 m) under the cited 153 ft ridge; concourse roof crown (27-29.5 m); number of columns drawn.
- Sources in the model: https://en.wikipedia.org/wiki/Pennsylvania_Station_(1910%E2%80%931963), https://www.openhistoricalmap.org/way/198645203

### Singer Building (1908–1968) — `singer_building_1908` — MEDIUM

- Years: construction 1906.7, complete 1908.35, gone 1968. Anchor 40.709581, -74.010797.
- Site outline: OHM way 198552870, traced from Sanborn 1905 vol. 1 (2,243 m2: 119 ft on Broadway, 231 ft on Liberty St). Tower placed from the cited setbacks: 30 ft behind Broadway and 10 ft clear of the City Investing Building on the north lot line.
- Dimension: lantern top 612 ft; flagpole 62 ft above (674 ft); tower 65 x 65 ft, set back 30 ft from Broadway; 10 ft gap to the City Investing Building — https://en.wikipedia.org/wiki/Singer_Building
- Dimension: dome 50 ft covering the top three storeys; lantern 63.75 ft tall, 9 ft across at the base; balcony at the 36th floor cantilevered 8.5 ft; base buildings about 200 ft; five 12-ft bays per face — https://en.wikipedia.org/wiki/Singer_Building
- Estimated: level of the 36th-floor balcony (144 m); curve of the mansard dome; mansard on the base.
- Sources in the model: https://en.wikipedia.org/wiki/Singer_Building, https://www.openhistoricalmap.org/way/198552870

### City Investing Building (1908–1968) — `city_investing_building_1908` — LOW

- Years: construction 1906.5, complete 1908.3, gone 1968. Anchor 40.709903, -74.010747.
- Site outline: OHM way 198552871 (1,735 m2) - about 30 % smaller than the cited frontages imply, and a plain hexagon without the light courts.
- Dimension: 486 ft above Broadway; 26-storey bulk + seven-storey gabled centre; 209 ft on Cortlandt, 109 ft on Church, 37.5 ft on Broadway, 313 ft deep — https://en.wikipedia.org/wiki/City_Investing_Building
- Estimated: height of the bulk (103 m = 26/33 of the height); form and place of the gabled centre.
- Sources in the model: https://en.wikipedia.org/wiki/City_Investing_Building, https://www.openhistoricalmap.org/way/198552871

### New York Crystal Palace (1853–1858) — `crystal_palace_1853` — HIGH

- Years: construction 1852.83, complete 1853.53, gone 1858.76. Anchor 40.753781, -73.983646.
- Site outline: centre and axes from OHM way 198109868: in the street-grid frame its octagon spans 111.0 m north-south (the cross), 45.5 m per arm, with entrance halls on three sides and a 14 x 137 m strip on the reservoir side; `replaces` = the west part of Reservoir Square (OHM relation 2696410).
- Dimension: naves 41 ft 5 in wide, 67 ft to the ridge; aisles 54 ft wide, two storeys, 50 ft; lean-tos 24 ft; eight octagonal towers 8 ft across, 71 ft high, flagstaffs 24 ft; dome 100 ft, springing 71 ft; entrance halls 27 ft deep with offices 27 x 18 ft; no entrance on the reservoir side — https://archive.org/details/newyorkcrystalp00carsa (Carstensen & Gildemeister 1854, "General description of the building")
- Dimension: Greek cross, dome 100 ft — https://en.wikipedia.org/wiki/New_York_Crystal_Palace
- Dimension: dome 123 ft high (other figures: 148 ft with the lantern) — https://daytoninmanhattan.blogspot.com/2011/11/lost-1853-crystal-palace.html ("a dome rose 123 feet from the floor with a 100-foot diameter"; three entrances on 6th Avenue, 40th and 42nd streets - page read)
- Dimension: cross 365 ft 5 in across - contemporary accounts, not found in the 1854 text; the OHM outline gives 364 ft — measured
- Estimated: height of the annex along the reservoir (10 m); the lantern; glass and iron colours.
- Sources in the model: https://archive.org/details/newyorkcrystalp00carsa, https://en.wikipedia.org/wiki/New_York_Crystal_Palace, https://www.openhistoricalmap.org/way/198109868

### Latting Observatory (1853–1855, full height) — `latting_observatory_1853` — LOW

- Years: construction 1853, complete 1853.5, gone 1855.5. Anchor 40.754698, -73.983074.
- Site outline: NOT from a map: sources say only "north side of 42nd Street between Fifth and Sixth avenues", adjoining the palace. Placed on the palace's north-south axis, 13.5 m north of the 42nd Street line (Overture centre line + 50 ft). Could be 100 m off along the street.
- Dimension: 315 ft; base 75 ft square; octagonal, tapering to 6-8 ft; landings at 125, 225, 300 ft; opened 1 Jul 1853; top 75 ft removed 1855; burned 30 Aug 1856 — https://en.wikipedia.org/wiki/Latting_Observatory
- Estimated: position; height of the base building (9 m); drawn as a solid tapering octagon.
- Sources in the model: https://en.wikipedia.org/wiki/Latting_Observatory

### Latting Observatory (1855–1856, shortened) — `latting_observatory_1855` — LOW

- Years: construction 1855.49, complete 1855.5, gone 1856.66. Anchor 40.754698, -73.983074.
- Site outline: NOT from a map: sources say only "north side of 42nd Street between Fifth and Sixth avenues", adjoining the palace. Placed on the palace's north-south axis, 13.5 m north of the 42nd Street line (Overture centre line + 50 ft). Could be 100 m off along the street.
- Dimension: 315 ft; base 75 ft square; octagonal, tapering to 6-8 ft; landings at 125, 225, 300 ft; opened 1 Jul 1853; top 75 ft removed 1855; burned 30 Aug 1856 — https://en.wikipedia.org/wiki/Latting_Observatory
- Estimated: position; height of the base building (9 m); drawn as a solid tapering octagon.
- Sources in the model: https://en.wikipedia.org/wiki/Latting_Observatory

### Croton Distributing Reservoir (1842–1900) — `croton_distributing_reservoir` — HIGH

- Years: construction 1839, complete 1842.5, gone 1899.5. Anchor 40.753205, -73.982246.
- Site outline: OHM relation 2689733: outer wall 137.0 x 115.1 m and the two basins.
- Dimension: 4 acres, 20 million gallons, walls 50 ft high and 25 ft thick, Egyptian style; 1839-1842; demolished 1899-1900 — https://en.wikipedia.org/wiki/Croton_Distributing_Reservoir
- Estimated: batter of the walls (2.4 m), corner pylons and entrance pavilion (2-3 m above the walls), water level.
- Sources in the model: https://en.wikipedia.org/wiki/Croton_Distributing_Reservoir, https://www.openhistoricalmap.org/relation/2689733

### Madison Square Garden II (1890–1925) — `madison_square_garden_1890` — LOW

- Years: construction 1889.5, complete 1890.46, gone 1925.4. Anchor 40.742754, -73.985583.
- Site outline: the block = footprint of the New York Life Building (city footprints BIN 1016880, 125.6 x 59.2 m = 412 x 194 ft); street lines give 127.8 x 60.2 m (Madison 80 ft, Fourth Av 100 ft, streets 60 ft).
- Dimension: 200 x 485 ft; main hall 200 x 350 ft; opened 16 Jun 1890; Diana 18 ft, then 13 ft (1893) — https://en.wikipedia.org/wiki/Madison_Square_Garden_(1890)
- Dimension: tower "completed to the 304 ft high observation deck" — https://thearchitectureprofessor.com/2021/09/16/1-6-madison-square-garden/
- Estimated: all wall and roof heights (18-24.5 m); tower width (11.6 m), its stages and its exact place on the 26th Street side; cupolas; arcade.
- Sources in the model: https://en.wikipedia.org/wiki/Madison_Square_Garden_(1890), https://thearchitectureprofessor.com/2021/09/16/1-6-madison-square-garden/

### Madison Square Garden III (1925–1968) — `madison_square_garden_1925` — LOW

- Years: construction 1925.03, complete 1925.95, gone 1968.5. Anchor 40.762362, -73.987253.
- Site outline: OHM way 198759004 (Bromley 1930): 147.3 x 61.0 m lot; the arena box is the cited 375 ft at the west end, the rest the Eighth Avenue entrance building.
- Dimension: 200 x 375 ft, three tiers, 18,496 seats; opened 15 Dec 1925; begun 9 Jan 1925 — https://en.wikipedia.org/wiki/Madison_Square_Garden_(1925)
- Estimated: all heights (walls 21 m, roof crown 26.5 m); the entrance building.
- Sources in the model: https://en.wikipedia.org/wiki/Madison_Square_Garden_(1925), https://www.openhistoricalmap.org/way/198759004

### Polo Grounds (1911–1923) — `polo_grounds_1911` — LOW

- Years: construction 1911.3, complete 1911.5, gone 1923.3. Anchor 40.831549, -73.936967.
- Site outline: OHM way 198180427 (the horseshoe of stands) and way 198180426 (the field); `replaces` = the outer line of the stands closed across centre field.
- Dimension: left 279 ft, right 258 ft, gaps 450 ft, clubhouse 483 ft, bleacher corners 425 ft; fire 14 Apr 1911; double deck carried round in 1923 — https://en.wikipedia.org/wiki/Polo_Grounds
- Estimated: home plate (on the horseshoe axis, 16 m from the backstop; the OHM field is 98 m wide where the foul lines imply ~115 m); which part had two decks before 1923; all heights (deck 19 m, roof 23 m, bleachers 6-10 m, clubhouse 17 m).
- Sources in the model: https://en.wikipedia.org/wiki/Polo_Grounds, https://www.openhistoricalmap.org/way/198180427, https://www.openhistoricalmap.org/way/198180426

### Polo Grounds (1923–1964) — `polo_grounds_1923` — LOW

- Years: construction 1923.29, complete 1923.3, gone 1964.27. Anchor 40.831549, -73.936967.
- Site outline: OHM way 198180427 (the horseshoe of stands) and way 198180426 (the field); `replaces` = the outer line of the stands closed across centre field.
- Dimension: left 279 ft, right 258 ft, gaps 450 ft, clubhouse 483 ft, bleacher corners 425 ft; fire 14 Apr 1911; double deck carried round in 1923 — https://en.wikipedia.org/wiki/Polo_Grounds
- Estimated: home plate (on the horseshoe axis, 16 m from the backstop; the OHM field is 98 m wide where the foul lines imply ~115 m); which part had two decks before 1923; all heights (deck 19 m, roof 23 m, bleachers 6-10 m, clubhouse 17 m).
- Sources in the model: https://en.wikipedia.org/wiki/Polo_Grounds, https://www.openhistoricalmap.org/way/198180427, https://www.openhistoricalmap.org/way/198180426

### Ebbets Field (1913–1960) — `ebbets_field_1913` — LOW

- Years: construction 1912.2, complete 1913.27, gone 1960.15. Anchor 40.665028, -73.958047.
- Site outline: OHM relation 2690259 = the block Bedford Av / Sullivan Pl / McKeever Pl / Montgomery St (matches the Overture street centre lines).
- Dimension: right 297 ft (301); left 419 ft and centre 508 ft in 1913, 356 and 406 ft after the added stands; opened 9 Apr 1913 — https://en.wikipedia.org/wiki/Ebbets_Field
- Estimated: home plate (right-field line parallel to Sullivan Place, 297 ft from the Bedford Avenue wall, 40 m from Sullivan Place: +-8 m); left-centre and right-centre distances; deck and roof heights (19 / 23 m); wall 38 ft; rotunda 23 m across.
- Sources in the model: https://en.wikipedia.org/wiki/Ebbets_Field, https://www.openhistoricalmap.org/relation/2690259

### Yankee Stadium (1923–1973) — `yankee_stadium_1923` — MEDIUM

- Years: construction 1922.35, complete 1923.3, gone 1973.75. Anchor 40.826893, -73.928003.
- Site outline: OHM relation 2690448: outer wall and field. Home plate set on the bisector of the mapped field 82 ft from the backstop; the cited foul lines (281 and 295 ft) then end within 5 m of the mapped stands, 490 ft reaches the bleacher wall.
- Dimension: right 295 ft, deepest centre 490 ft, backstop 82 ft; 8-acre site; frieze 15 ft; begun 5 May 1922, opened 18 Apr 1923; rebuilt 30 Sep 1973 - 15 Apr 1976 — https://en.wikipedia.org/wiki/Yankee_Stadium_(1923)
- Dimension: left field 281 ft (1923) - recalled, not in the article extract
- Dimension: frieze 117 ft above the field — https://www.americanheritage.com/node/133629 ("a 15-foot copper frieze"; Mantle 1963 "smashing off the copper frieze, 117 feet high" - page read)
- Estimated: deck heights below the roof; the decks are drawn at their 1937 extent from the start.
- Sources in the model: https://en.wikipedia.org/wiki/Yankee_Stadium_(1923), https://www.openhistoricalmap.org/relation/2690448, https://www.americanheritage.com/node/133629

### Yankee Stadium (rebuilt 1976–2009) — `yankee_stadium_1976` — LOW

- Years: construction 1973.76, complete 1976.29, gone 2010. Anchor 40.826893, -73.928003.
- Site outline: OHM relation 2690448: outer wall and field. Home plate set on the bisector of the mapped field 82 ft from the backstop; the cited foul lines (281 and 295 ft) then end within 5 m of the mapped stands, 490 ft reaches the bleacher wall.
- Dimension: right 295 ft, deepest centre 490 ft, backstop 82 ft; 8-acre site; frieze 15 ft; begun 5 May 1922, opened 18 Apr 1923; rebuilt 30 Sep 1973 - 15 Apr 1976 — https://en.wikipedia.org/wiki/Yankee_Stadium_(1923)
- Dimension: left field 281 ft (1923) - recalled, not in the article extract
- Dimension: frieze 117 ft above the field — https://www.americanheritage.com/node/133629 ("a 15-foot copper frieze"; Mantle 1963 "smashing off the copper frieze, 117 feet high" - page read)
- Estimated: height of the rebuilt upper deck (drawn at the old roof line).
- Sources in the model: https://en.wikipedia.org/wiki/Yankee_Stadium_(1923), https://www.openhistoricalmap.org/relation/2690448

### Shea Stadium (1964–2009) — `shea_stadium_1964` — LOW

- Years: construction 1961.82, complete 1964.29, gone 2009.13. Anchor 40.755688, -73.847767.
- Site outline: OHM relation 2691041: a circle 233 m across.
- Dimension: 341 ft down both lines (338 from 1978); opened 17 Apr 1964 — https://en.wikipedia.org/wiki/Shea_Stadium
- Dimension: centre field 410 ft - recalled, not in the article extract
- Estimated: direction of centre field (60 deg, inferred from the OHM-mapped left-field bleachers, way 201437224) and home plate (50 m from the centre): +-10 deg; height of the stands (34 m); scoreboard.
- Sources in the model: https://en.wikipedia.org/wiki/Shea_Stadium, https://www.openhistoricalmap.org/relation/2691041, https://www.openhistoricalmap.org/way/201437224

### Fort Amsterdam (Fort James, Fort George; 1625–1790) — `fort_amsterdam` — LOW

- Years: construction 1625.5, complete 1635, gone 1790. Anchor 40.704149, -74.014026.
- Site outline: OHM relation 2690942 (Castello Plan 1660 via mapwarper 4625): bastioned trace 5,730 m2 and parade; houses from ways 198590263-5.
- Dimension: four sides with a bastion at each corner; barracks, church, director's house, warehouse; 1625 laid out; demolished 1790 — https://en.wikipedia.org/wiki/Fort_Amsterdam
- Estimated: rampart height (4.5 m) and parapet; heights of the houses; gate; flagstaff.
- Sources in the model: https://en.wikipedia.org/wiki/Fort_Amsterdam, https://www.openhistoricalmap.org/relation/2690942, https://en.wikipedia.org/wiki/Castello_Plan

### Church in the Fort (St. Nicholas, 1642–1741) — `fort_amsterdam_church_1642` — MEDIUM

- Years: construction 1642.33, complete 1643.5, gone 1741.21. Anchor 40.704013, -74.013806.
- Site outline: position and axis of OHM way 198590262 (which draws it 20.1 x 9.9 m, 199 m2); footprint from the contract.
- Dimension: 72 ft long, 52 ft broad (50 in an older translation, per a web search), 16 ft high above the ground, 2,500 guilders — https://encyclopedia.nahc-mapping.org/document/contract-john-and-richard-ogden-stamford-connecticut-build-stone-church-fort-amsterdam (New York State Archives calendar entry, contract of 1 May 1642 - page read)
- Estimated: twin gabled roofs (5 m) and turret, from the Castello Plan drawing; burned 18 Mar 1741 (recalled).
- Sources in the model: https://encyclopedia.nahc-mapping.org/document/contract-john-and-richard-ogden-stamford-connecticut-build-stone-church-fort-amsterdam, https://www.openhistoricalmap.org/way/198590262, https://en.wikipedia.org/wiki/Castello_Plan

### Stadt Huys (City Tavern 1642; city hall 1653–1699) — `stadt_huys_1642` — LOW

- Years: construction 1641.5, complete 1642.5, gone 1699.5. Anchor 40.703813, -74.010705.
- Site outline: position and axis of OHM way 198590337 (Castello Plan; drawn 11.8 x 6.5 m).
- Dimension: 1979-80 excavation found foundations of about 42 x 52 ft; five storeys — https://www.waymarking.com/waymarks/WM31V1_Unearthing_Gotham_Stadt_Huys (single popular source - page read: "five stories", "foundations, only 42 feet by 52 feet", tavern 1642, city hall 1653-1699)
- Dimension: city hall 1653-1697 — https://en.wikipedia.org/wiki/Stadt_Huys_Site
- Estimated: which side lay along Pearl Street; eaves 10 m, ridge 17 m, stepped gables, cupola.
- Sources in the model: https://en.wikipedia.org/wiki/Stadt_Huys_Site, https://www.waymarking.com/waymarks/WM31V1_Unearthing_Gotham_Stadt_Huys, https://www.openhistoricalmap.org/way/198590337

### The wall of New Amsterdam (Wall Street, 1653–1699) — `wall_street_palisade_1653` — MEDIUM

- Years: construction 1653.2, complete 1653.55, gone 1699.5. Anchor 40.706639, -74.009665.
- Site outline: OHM ways 198538378 (Broadway - East River) and 198538377 (Broadway - Hudson): 713 m including the bastions against the cited 2,340 ft = 713.2 m.
- Dimension: 2,340 ft long, 15 ft planks, 9 ft tall; ditch; 1653; stone bastions Hollandia and Zeelandia; demolished 1699 — https://en.wikipedia.org/wiki/Wall_Street
- Estimated: gates are symbolic posts; the bastions are those of the later plans OHM traced, shown from 1653.
- Sources in the model: https://en.wikipedia.org/wiki/Wall_Street, https://www.openhistoricalmap.org/way/198538378, https://www.openhistoricalmap.org/way/198538377

### Trinity Church (first, 1698–1776) — `trinity_church_1698` — MEDIUM

- Years: construction 1696.5, complete 1698.2, gone 1776.72. Anchor 40.707874, -74.012092.
- Site outline: OHM way 198588234 (mapwarper 49065): 52.6 x 24.7 m, 1,017 m2.
- Dimension: body 105 ft, chancel 16 ft, steeple 32 ft square: 153 ft in all; breadth 73 ft; spire 180 ft (as enlarged 1737) — https://geographicguide.com/united-states/nyc/antique/trinity-church/first-temple.htm (as reported by a web search; the page could not be opened from this machine: expired TLS certificate)
- Dimension: built 1698, burned 21 Sep 1776; steeple toward the Hudson — https://en.wikipedia.org/wiki/Trinity_Church_(Manhattan)
- Estimated: eaves (11 m), ridge (17 m), masonry tower height (27 m); shown as enlarged from 1698.
- Sources in the model: https://geographicguide.com/united-states/nyc/antique/trinity-church/first-temple.htm, https://en.wikipedia.org/wiki/Trinity_Church_(Manhattan), https://www.openhistoricalmap.org/way/198588234

### Trinity Church (second, 1790–1839) — `trinity_church_1790` — MEDIUM

- Years: construction 1788.6, complete 1790.23, gone 1839.6. Anchor 40.707960, -74.012100.
- Site outline: OHM way 198782077: 42.0 x 20.6 m.
- Dimension: 200 ft tall, facing Wall Street, longer and wider than the first; consecrated 1790; demolished 1839 — https://en.wikipedia.org/wiki/Trinity_Church_(Manhattan)
- Estimated: eaves, ridge, tower width and masonry height.
- Sources in the model: https://en.wikipedia.org/wiki/Trinity_Church_(Manhattan), https://www.openhistoricalmap.org/way/198782077

### City Hall on Wall Street (1703–1789) — `city_hall_wall_street_1703` — LOW

- Years: construction 1699.5, complete 1703, gone 1789.17. Anchor 40.707249, -74.010541.
- Site outline: OHM way 198588178 (mapwarper 49065): 27.4 x 15 m.
- Dimension: built 1699-1703; stone from the wall's bastions — https://en.wikipedia.org/wiki/Federal_Hall
- Estimated: all heights (eaves 9.5 m, cupola).
- Sources in the model: https://en.wikipedia.org/wiki/Federal_Hall, https://www.openhistoricalmap.org/way/198588178

### Federal Hall (1789–1812) — `federal_hall_1789` — LOW

- Years: construction 1788.76, complete 1789.17, gone 1812.5. Anchor 40.707249, -74.010541.
- Site outline: as the 1703 City Hall (L'Enfant's rear extension is not in the outline).
- Dimension: L'Enfant 1788-89: arcade with four Tuscan columns under the balcony, four Doric columns, eagle pediment, third storey, hip roof and cupola; House chamber 60 x 60 ft; demolished 1812 — https://en.wikipedia.org/wiki/Federal_Hall
- Estimated: all heights (eaves 13 m, cupola to 27.5 m).
- Sources in the model: https://en.wikipedia.org/wiki/Federal_Hall, https://www.openhistoricalmap.org/way/198588178

### Government House (1790–1815) — `government_house_1790` — LOW

- Years: construction 1790.4, complete 1791.5, gone 1815.5. Anchor 40.704284, -74.013737.
- Site outline: OHM way 198589844: 37.8 x 21.1 m.
- Dimension: "elegant two-story brick building"; 1790; demolished 1815 — https://en.wikipedia.org/wiki/Government_House_(New_York_City)
- Estimated: all heights (eaves 11 m); portico.
- Sources in the model: https://en.wikipedia.org/wiki/Government_House_(New_York_City), https://www.openhistoricalmap.org/way/198589844

### The Tombs (Halls of Justice, 1838–1902) — `the_tombs_1838` — MEDIUM

- Years: construction 1835.5, complete 1838.5, gone 1902. Anchor 40.716285, -74.001969.
- Site outline: the cited rectangle set on the block: east side on the Centre Street line (Overture centre line less 40 ft), centred between Franklin and Leonard (centre lines 72.2 m apart). Today the block is Collect Pond Park (Overture land use: 5,012 m2).
- Dimension: 253 ft 3 in x 200 ft 5 in, full block Centre / Franklin / Elm / Leonard; 1838; replaced 1902 — https://en.wikipedia.org/wiki/The_Tombs
- Estimated: all heights (walls 11 m, portico 14 m, prison block 14 m); courtyard layout.
- Sources in the model: https://en.wikipedia.org/wiki/The_Tombs, https://www.openhistoricalmap.org/way/198158994

### Bridewell (1775–1838) — `bridewell_1775` — LOW

- Years: construction 1775.2, complete 1776.2, gone 1838.5. Anchor 40.713148, -74.006543.
- Site outline: OHM way 198751651 ("Map of City Hall Park"): 43.8 m long.
- Dimension: 1775; replaced by the Tombs 1838 — https://en.wikipedia.org/wiki/Bridewell_(New_York_City_jail)
- Estimated: height (10.5 m) and roof.
- Sources in the model: https://en.wikipedia.org/wiki/Bridewell_(New_York_City_jail), https://www.openhistoricalmap.org/way/198751651

### Second Almshouse (1797–1857; New York Institution from 1816) — `almshouse_1797` — LOW

- Years: construction 1795.5, complete 1797, gone 1857. Anchor 40.713452, -74.005408.
- Site outline: OHM way 198751661 (LPC African Burial Ground and the Commons report): 78.5 x 18.2 m.
- Dimension: Second Almshouse 1796-1830 (OHM tags; source: LPC African Burial Ground and the Commons Historic District designation report) — https://www.openhistoricalmap.org/way/198751661
- Estimated: height (13 m); the year it came down (1857) is recalled, OHM ends it as an almshouse in 1830.
- Sources in the model: https://www.openhistoricalmap.org/way/198751661, https://www.openhistoricalmap.org/relation/2697412

### College Hall, King's College / Columbia College (1760–1857) — `kings_college_hall_1760` — LOW

- Years: construction 1756.64, complete 1760.4, gone 1857.4. Anchor 40.713708, -74.009715.
- Site outline: OHM way 198103779 / relation 2697337: 57.3 x 10.0 m.
- Dimension: King's College 1760-1776, Columbia College 1784-1857 on this site — https://www.openhistoricalmap.org/way/198103779
- Estimated: heights (eaves 11.5 m, cupola to 22 m); dates of the cornerstone and demolition are recalled.
- Sources in the model: https://www.openhistoricalmap.org/way/198103779, https://en.wikipedia.org/wiki/History_of_Columbia_University

### Park Theatre (1798–1848) — `park_theatre_1798` — MEDIUM

- Years: construction 1795.4, complete 1798.08, gone 1848.96. Anchor 40.711261, -74.007496.
- Site outline: OHM way 198589840: 46.0 x 23.4 m.
- Dimension: three storeys, 80 ft wide x 165 ft deep, plain dressed stone; opened Jan 1798; burned 16 Dec 1848 — https://en.wikipedia.org/wiki/Park_Theatre_(Manhattan)
- Estimated: height (15 m eaves).
- Sources in the model: https://en.wikipedia.org/wiki/Park_Theatre_(Manhattan), https://www.openhistoricalmap.org/way/198589840

### New York Hippodrome (1905–1939) — `hippodrome_1905` — LOW

- Years: construction 1904.5, complete 1905.28, gone 1939.65. Anchor 40.755606, -73.982854.
- Site outline: today's lot: city footprints BIN 1034202 (72.8 x 60.8 m = 239 x 199.5 ft); 43rd-44th Street centre lines 79.3 m apart less 60 ft = 61.0 m.
- Dimension: 5,300 seats; stage 100 x 200 ft; tank 60 ft across, 14 ft deep; 1905-1939 — https://en.wikipedia.org/wiki/New_York_Hippodrome
- Estimated: all heights (22-30 m), corner towers and globes (38.6 m).
- Sources in the model: https://en.wikipedia.org/wiki/New_York_Hippodrome

### Metropolitan Opera House (1883–1967) — `metropolitan_opera_house_1883` — LOW

- Years: construction 1881.3, complete 1883.81, gone 1967.05. Anchor 40.754193, -73.987516.
- Site outline: OHM way 198759005 (Bromley 1930): 86.6 x 58.7 m, 4,590 m2.
- Dimension: whole block Broadway / Seventh Av / 39th / 40th; opened 22 Oct 1883; razed 1967 — https://en.wikipedia.org/wiki/Metropolitan_Opera_House_(39th_Street)
- Estimated: all heights (27 m, stage house 37 m).
- Sources in the model: https://en.wikipedia.org/wiki/Metropolitan_Opera_House_(39th_Street), https://www.openhistoricalmap.org/way/198759005

### New York World Building (Pulitzer Building, 1890–1955) — `world_building_1890` — MEDIUM

- Years: construction 1889.77, complete 1890.94, gone 1955.5. Anchor 40.711848, -74.004737.
- Site outline: OHM way 198589815 (mapwarper 41751), with the 1908 annex.
- Dimension: flat roof 191 ft; dome 310 ft; pinnacle 350 ft; 115 ft on Park Row, 136 ft on Frankfort St; lot 18,496 sq ft with the annex — https://en.wikipedia.org/wiki/New_York_World_Building
- Estimated: diameter and position of the dome (16.5 m, over the Park Row front); the annex is shown from 1890.
- Sources in the model: https://en.wikipedia.org/wiki/New_York_World_Building, https://www.openhistoricalmap.org/way/198589815

### New-York Tribune Building (1875–1905, as built) — `tribune_building_1875` — MEDIUM

- Years: construction 1873, complete 1875.3, gone 1905.5. Anchor 40.711643, -74.005345.
- Site outline: OHM way 198589816 (mapwarper 41751) - includes the later extensions (1,454 m2; the 1875 building was about 90 x 98 ft).
- Dimension: roof 155 ft; clock tower 260 ft incl. 16 ft pyramid roof and iron finial; tower 17 ft square, second bay of the Nassau Street front — https://en.wikipedia.org/wiki/New_York_Tribune_Building
- Estimated: finial length (20 ft); outline is the enlarged one.
- Sources in the model: https://en.wikipedia.org/wiki/New_York_Tribune_Building, https://www.openhistoricalmap.org/way/198589816

### New-York Tribune Building (enlarged, 1905–1966) — `tribune_building_1905` — MEDIUM

- Years: construction 1903.5, complete 1905.5, gone 1966.5. Anchor 40.711643, -74.005345.
- Site outline: as above.
- Dimension: nineteen storeys; flat roof 231 ft; clock tower 273 ft; finial 335 ft — https://en.wikipedia.org/wiki/New_York_Tribune_Building
- Estimated: none beyond the massing.
- Sources in the model: https://en.wikipedia.org/wiki/New_York_Tribune_Building, https://www.openhistoricalmap.org/way/198589816

### Equitable Life Building (1870–1912) — `equitable_life_building_1870` — LOW

- Years: construction 1868.5, complete 1870.33, gone 1912.02. Anchor 40.708218, -74.010522.
- Site outline: OHM way 198592110 = the whole block, as after 1887.
- Dimension: 130-142 ft, seven storeys (1870); 155 ft, nine storeys (1885); final perhaps 172 ft; burned 9 Jan 1912 — https://en.wikipedia.org/wiki/Equitable_Life_Building_(Manhattan)
- Estimated: shown in the enlarged form from 1870 (the 1870 footprint is not mapped); the Broadway pavilion.
- Sources in the model: https://en.wikipedia.org/wiki/Equitable_Life_Building_(Manhattan), https://www.openhistoricalmap.org/way/198592110

### Grand Central Depot (1871–1900) — `grand_central_depot_1871` — LOW

- Years: construction 1869.87, complete 1871.8, gone 1900.8. Anchor 40.752700, -73.977200.
- Site outline: cited dimensions set on street lines: Vanderbilt Av east line (Overture centre line + 30 ft), 42nd St north line (centre line + 50 ft); 695 ft reaches to 9 m short of the 45th Street line.
- Dimension: train shed 530 x 200 ft, 100 ft at the crown; 695 ft along Vanderbilt Avenue; three-storey L-shaped head house; 1871 — https://en.wikipedia.org/wiki/History_of_Grand_Central_Terminal
- Estimated: 42nd Street frontage (249 ft, recalled); head-house height (17 m) and towers (30-36 m).
- Sources in the model: https://en.wikipedia.org/wiki/History_of_Grand_Central_Terminal

### Grand Central Station (1900–1910) — `grand_central_station_1900` — LOW

- Years: construction 1898.5, complete 1900.8, gone 1910.45. Anchor 40.752700, -73.977200.
- Site outline: cited dimensions set on street lines: Vanderbilt Av east line (Overture centre line + 30 ft), 42nd St north line (centre line + 50 ft); 695 ft reaches to 9 m short of the 45th Street line.
- Dimension: head house raised from three to six storeys 1898-1900; old station demolished in stages to 1910 — https://en.wikipedia.org/wiki/History_of_Grand_Central_Terminal
- Estimated: six storeys = 30 m; domed towers (to 46 m).
- Sources in the model: https://en.wikipedia.org/wiki/History_of_Grand_Central_Terminal

### Trylon and Perisphere (1939–1941) — `trylon_perisphere_1939` — MEDIUM

- Years: construction 1938.27, complete 1939.33, gone 1941. Anchor 40.746398, -73.845071.
- Site outline: Perisphere centre = centroid of the Unisphere's pool (Overture base_water "Fountain of the Continents"); the Unisphere stands on the Perisphere's piling ring. Trylon: read off the 1939 newspaper map on Wikimedia Commons (south-east of the sphere, about 73 deg clockwise from the Constitution Mall axis, ~68 m).
- Dimension: Perisphere 180 ft; Trylon 610 ft; Helicline 950 ft — https://en.wikipedia.org/wiki/Trylon_and_Perisphere
- Dimension: Unisphere built on the Perisphere's foundation — https://en.wikipedia.org/wiki/Unisphere
- Dimension: relative position of the Trylon — https://commons.wikimedia.org/wiki/File:Worlds-fair-map.jpg
- Estimated: Trylon position (+-15 m) and base (19 m sides); sphere 2.5 m above its pool; Helicline course (drawn 230 m long instead of 290 m); bridge height 15 m.
- Sources in the model: https://en.wikipedia.org/wiki/Trylon_and_Perisphere, https://en.wikipedia.org/wiki/Unisphere, https://commons.wikimedia.org/wiki/File:Worlds-fair-map.jpg

## Left out for lack of citable dimensions

- Cornelius Vanderbilt II House (Fifth Avenue, 57th–58th Street, 1883/1893–1927): the article gives only "six stories" and "the entire block front"; no plan or height found; not in OHM.
- Charles M. Schwab House (Riverside Drive, 73rd–74th Street, 1906–1948): "an entire city block", 75 rooms, 50,000 sq ft; sources disagree on the tower (100 ft / 166 ft); no plan of the house within its garden block; not in OHM.
- Ziegfeld Theatre (1927–1966): OHM has the outline (way 198777204, 1,315 m², Bromley 1930) but no height or storey count was found.
- Luna Park (1903–1944): no dimensioned plan was found (the article was only searched for tower heights); not in OHM.
- Dreamland tower (1904–1911): cited 375 ft on a 50 × 50 ft base, but its position inside the park could not be fixed from a map; not in OHM.
- The Equitable Life Building as first built (1870–1885): its smaller footprint is not mapped, so the one model shows the enlarged block-filling form from 1870.
- Grand Central Depot's 1885 annex on the east side: no dimensions.

## Not checked

- Nothing was looked at in the running viewer (headless rendering does not work on this machine). The meshes were rendered to top and oblique views off-line (`data/interim/landmarks_lost/render.py`, sheets 1–5) for Penn Station, Singer, Crystal Palace, MSG II and III, the four ballparks, Grand Central Depot, Trylon and Perisphere, Fort Amsterdam, Federal Hall, 1 WTC, the World and Tribune buildings, the Tombs, the Hippodrome, the Croton reservoir and the Stadt Huys; the others were checked only numerically.
- loc.gov (HABS/HAER) answered 403 to this machine and the Overpass mirrors of OpenStreetMap were unreachable, so no HABS data pages and no OSM home-plate markers were used.
- Ground elevation: every model is drawn on a flat base at its anchor; sloping sites (Ebbets Field, Polo Grounds under Coogan's Bluff, the City Investing Building) are not terraced.
