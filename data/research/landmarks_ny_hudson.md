# Landmarks of Westchester, Rockland and the Hudson valley — research notes and numeric checks

Models: `viewer/src/landmarks/ny-hudson.ts` (`NY_HUDSON`, 23 entries, about 22,800 faces / 68,000 vertices before the last edits). Dates: `data/tables/known_building_dates.ny_hudson.csv` (28 rows).

## Method

- **Plans**: building footprints from Overture Maps 2026-10-21.0 (`data/raw/overture/2026-10-21.0/outer_building.parquet`, read by lon/lat window; OpenStreetMap contributors, ODbL). Each footprint is re-expressed in metres east / north of the anchor given in the code comment (the point the window was centred on); the model uses the ring as read, so plan and orientation are the real ones. Tool: `data/interim/landmarks_ny_hudson/fp.py <lon> <lat> <radius> <min area> --ring --top=N`.
- **Bridge lines**: the bridge-flagged segments of Overture's `outer_freeways.parquet` (`road_flags` `is_bridge`, `between` fractions) for the Tappan Zee roadways, Bear Mountain, Mid-Hudson and Newburgh-Beacon (end points and centre lines); OpenStreetMap way 24185107 (Walkway Over the Hudson, 14 nodes, 2,070 m) for the Poughkeepsie bridge; OpenStreetMap ways 1005972999 / 1005973000 / 1005973001 / 1005973002 (`bridge:support=pylon`, height 128 m) for the Tappan Zee main-span pylons; OpenStreetMap way 177603533 (`waterway=dam`, "New Croton Dam", height 91, start_date 1906) for the dam. Overpass was fetched through `maps.mail.ru/osm/tools/overpass` (the other mirrors returned nothing); results are in `data/interim/landmarks_ny_hudson/` (scratch).
- **Cited dimensions and dates**: the English Wikipedia articles named in each model's `sources` (CC BY-SA 4.0, facts only), read as wikitext on 2026-11-11 (copies in `data/raw/landmarks_ny_hudson/*.txt`, gitignored). Every figure below is from the article read in this session; no NPS, HABS or LPC document was opened.
- **Estimates** are listed per model and repeated in each `facts.Model` (shown in the popup). Heights of buildings are estimated unless a figure is named: the articles give almost none. Overture's `height` for these footprints is often a rough OpenStreetMap value (e.g. 8.3 m for the Cadet Chapel, which is not used).
- Kind/placement: bridges are modelled from sea level (the viewer does not lift them), everything else stands on the terrain at the anchor (`index.ts`); `replaces` carries the footprints so the generic extrusions are dropped.

## Numeric check

`data/interim/landmarks_ny_hudson/check_entry.ts` (bundled with esbuild, run with node) builds every mesh with the kit and writes `check.json`; the plan outline is the union of all triangles projected to the ground, filled, compared with the footprints in `replaces`. "Inside" is the share of the official footprint covered by the model's outline.

| id | faces | top of model (m) | cited / measured top | plan (m2) | official (m2) | ratio | inside | centroid offset (m) |
|---|---|---|---|---|---|---|---|---|
| kykuit | 116 | 19.3 | roof 17.07 (OSM); chimneys above it | 1,959 (incl. a garden terrace, estimated) | 869 | walls exactly the ring | 1.00 | 3.3 (terrace) |
| old_dutch_church_sleepy_hollow | 95 | 15.6 | none cited | 225 | 192 | 1.17 (gable roof over the ring's bounding box) | 1.00 | 0.7 |
| philipsburg_manor_upper_mills | 48 | 9.8 | none | 320 | 240 | 1.33 (roof overhang, dam stub) | 1.00 | 2.0 |
| lyndhurst_1838 | 94 | 14.4 | none | 558 | 710 (whole house) | 0.79 (south block only) | 0.77 | 5.0 |
| lyndhurst | 150 | 21.0 | 21.03 (OSM / Overture) | 831 | 710 | 1.17 | 1.00 | 2.1 |
| cadet_chapel_west_point | 136 | 36.0 | none (tower estimated) | 1,286 | 1,185 | 1.09 | 1.00 | 1.1 |
| washington_hall_west_point | 264 | 27.1 | none | 8,488 | 8,286 | 1.02 | 1.00 | 0.8 |
| michie_stadium | 64 | 26.5 | none | 24,097 (incl. the 8.6 k m2 field) | 17,934 (two footprints) | 0.87 without the field | 0.77 | 14.8 (field) |
| fort_putnam_west_point | 220 | 5.2 | none | 4,437 | 4,306 | 1.03 | 1.00 | 0.9 |
| bannermans_castle | 310 | 31.0 | none | 1,798 | 1,753 | 1.03 | 1.00 | 0.2 |
| vassar_main_building | 568 | 26.0 | none | 6,125 | 5,839 | 1.05 | 1.00 | 0.9 |
| springwood_hyde_park | 83 | 14.6 | none | 970 | 931 | 1.04 | 1.00 | 0.3 |
| vanderbilt_mansion_hyde_park | 190 | 14.6 | 11.0 (OSM, 3 storeys) to the eaves | 1,204 | 1,154 | 1.04 | 1.00 | 0.2 |
| new_croton_dam | 282 | 3.6 above the anchor (body to -88 m) | height 90.5 m (297 ft) = 88 + 2.5 crest | 12,630 | 12,564 | 1.01 | 1.00 | 1.0 |
| mohonk_mountain_house | 362 | 33.0 | none | 5,507 | 5,235 | 1.05 | 1.00 | 0.8 |

Bridges (extents from the built mesh, local metres around the anchor):

| id | cited | model |
|---|---|---|
| cuomo_bridge_north_span / south_span | main span 1,200 ft (365.8 m), towers 419 ft (127.7 m), 139 ft clear (42.4 m), length 16,368 ft (4,989 m) | pylons at x = +-182.9 m (365.8 m apart, OSM pylons 365.7 m), top 127.7 m, deck 45.4 m over the channel; path 4,447 m long in the model (x from -3,208 to +1,239; the cited length includes approaches on land) |
| tappan_zee_bridge | cantilever span 1,212 ft (369.4 m), 138 ft clear (42.1 m), 16,013 ft (4,881 m), 90 ft wide | truss from x = -370 to +370 (740 m, the cantilever + anchor arms: estimated), deck 44.6 m over the channel, top chord 75.1 m; path 4,440 m |
| bear_mountain_bridge | main span 1,632 ft (497.4 m), length 2,255 ft (687 m), towers 360 ft (109.7 m), 155 ft clear (47.2 m), 48 ft wide | towers at y = +-248.7 (497.4 m), deck ends at +-343.5 (687 m), tower top 109.7, deck 14.6 m wide (hw 7.3), mid-span deck 49.2 m |
| mid_hudson_bridge | main span 457.3 m, 3,000 ft (914.4 m), towers 315 ft (96.0 m), 135 ft clear (41.1 m) | towers at +-228.65 (457.3 m), ends at +-457.2 (914.4 m), tower top 96.0 m, mid-span deck 43.6 m |
| poughkeepsie_railroad_bridge | 6,768 ft (2,063 m), deck 212 ft (64.6 m), 35 ft wide | path 2,070 m (OSM way), deck 64.6 m, 10.7 m wide |
| newburgh_beacon_bridge_1963 / 1980 | main span 1,000 ft (304.8 m), 7,855 / 7,789 ft (2,394 / 2,374 m), 135 ft clear (41.1 m) | axis 2,388 m (Overture flagged ends), main piers 304.8 m apart, deck 42.4 m at mid-span, trusses to 67.8 m |

## Models

Years are `built` (start, completion) and `end`.

| id | name | years | faces | what is cited | what is estimated |
|---|---|---|---|---|---|
| kykuit | Kykuit | 1906-1913, standing | 116 | completed 1913 (Delano & Aldrich), four storeys, 40 rooms, grounds from 1906; roof 17.07 m | eave 13.6 m, hip roof, chimneys, terrace; start 1906 is the grounds design date |
| old_dutch_church_sleepy_hollow | Old Dutch Church of Sleepy Hollow | 1685-1697, standing | 95 | bell dated 1685, congregation 1697 (built between), fieldstone walls 60 cm, octagonal wooden belfry at the west end | wall height 5.2 m, pitch, belfry size and height 15.6 m |
| philipsburg_manor_upper_mills | Philipsburg Manor house and mill | 1685-1693, standing | 48 | 1693 grant, stone manor house and mill, doubled house, stone gristmill by 1750 | heights, roofs; start year; the present mill is a later reconstruction (not verified) |
| lyndhurst_1838 | Lyndhurst, original house | 1838-1842, ends 1864 | 94 | designed 1838, completed 1842 (A. J. Davis) | division of the footprint at y = 7 m, eave 10.2 m, turrets |
| lyndhurst | Lyndhurst, enlarged | 1864-1865.9, standing | 150 | 1864-65 doubled with a north wing and four-storey tower; tower top 21.03 m | stage heights, roofs, completion within 1865 |
| cadet_chapel_west_point | Cadet Chapel | 1906-1910, standing | 136 | groundbreaking 1906, completed 1910 (Cram, Goodhue & Ferguson) | all heights (nave ridge 15.7, tower 36 m) |
| washington_hall_west_point | Washington Hall | 1925-1929, standing | 264 | 1925-29 (Arnold Brunner) | footprint is today's (with the 1971 expansion); heights; roof ridges |
| michie_stadium | Michie Stadium | 1924-1924.8, standing | 64 | opened 1924, expanded 1962 / 1969 / 2003; north-south field | stands' height and slope, end blocks; plan is today's |
| fort_putnam_west_point | Fort Putnam | 1778-1779.5, standing | 220 | built 1778 by Putnam's 5th Massachusetts; restored from 1907 | wall height 5.2 m, thickness; the outline is the restoration's |
| bannermans_castle | Bannerman's Castle | 1901.3-1918, standing | 310 | island bought Nov 1900, arsenal begun spring 1901, residence castle beside it | heights (22 / 31 m), turrets, completion 1918 |
| vassar_main_building | Vassar Main Building | 1861-1865.7, standing | 568 | begun 1861 (Renwick), completed 1865, four storeys + mansard, 500 ft centre, 164 ft wings | eave 17 m, mansard 5 m, pavilion; completion within 1865 |
| springwood_hyde_park | Springwood | 1915-1916, standing | 83 | farmhouse c.1800; 1915 enlargement and remodelling; south tower | heights, roofs, wing extent; the pre-1915 house is not modelled |
| vanderbilt_mansion_hyde_park | Vanderbilt Mansion | 1896-1899, standing | 190 | built between 1896 and 1899 (McKim, Mead & White), 54 rooms, 3 storeys, 11 m | roof, balustrade, portico |
| new_croton_dam | New Croton Dam | 1892-1906, standing | 282 | begun 1892, completed 1906; 2,188 ft long, 297 ft high | crest 2.5 m above anchor ground, straight-sided prism, parapet; only the masonry outline of the OSM way is drawn |
| mohonk_mountain_house | Mohonk Mountain House | 1869-1910, standing | 362 | main structure built 1869-1910 (Smiley brothers); 28 tower rooms | eave 15.5 m, roof, three towers, one growth curve |
| cuomo_bridge_north_span | Cuomo Bridge, northbound / westbound span | 2013.8-2017.65, standing | ~3,290 | began 2013; opened Aug 26, 2017; main span, towers, clearance, 87 ft deck | grades, trestle 14 m, pier spacing 69 m, stay fan; the four lower pylons not modelled |
| cuomo_bridge_south_span | Cuomo Bridge, southbound / eastbound span | 2014.5-2018.7, standing | ~3,280 | opened Sept 11, 2018; 96 ft deck | as above; start 2014.5 |
| tappan_zee_bridge | Tappan Zee Bridge | 1952.2-1955.96, ends 2019.4 | ~5,080 | March 1952 - Dec 15, 1955; traffic left Oct 6, 2017; east half imploded Jan 15, 2019, west half removed May 2019; 1,212 ft cantilever, 138 ft, 90 ft | **the line of the bridge** (new eastbound roadway shifted 78 m south), truss panel and top chord, trestle heights, pier spacing |
| bear_mountain_bridge | Bear Mountain Bridge | 1923-1924.9, standing | ~1,580 | authorised 1922, opened Nov 27, 1924; spans, towers, clearance, width | deck heights at towers / ends, tower and strut sizes, sag; start 1923 |
| mid_hudson_bridge | Mid-Hudson Bridge | 1925-1930.65, standing | ~1,530 | begun 1925, opened Aug 25, 1930; spans, towers, clearance | deck width, heights at towers / ends, tower and strut sizes |
| poughkeepsie_railroad_bridge | Poughkeepsie Railroad Bridge / Walkway | 1886-1889, standing | ~2,650 | begun 1886, opened Jan 1, 1889; length, deck height, width, 548 ft spans; OSM line | the seven main-span positions (equal 160 m), truss depths, piers, trestle |
| newburgh_beacon_bridge_1963 | Newburgh-Beacon Bridge, northern span | 1960-1963.84, standing | ~1,190 | opened Nov 2, 1963; main span, length, clearance | deck heights, truss depths, pier spacing, 42 m between the spans; start 1960 |
| newburgh_beacon_bridge_1980 | Newburgh-Beacon Bridge, southern span | 1977-1980.84, standing | ~1,190 | opened Nov 1, 1980 | as above; start 1977 |

## Dates table

`data/tables/known_building_dates.ny_hudson.csv`: 28 rows, 21 for the United States Military Academy's central area and 7 for Vassar's campus (every row has a point inside the Overture footprint of the named building, taken as `representative_point`, and the article's wording in `note`; `exact:` where the article gives the year, `estimated:` for the Arvin Gymnasium core and Fort Putnam). Sources: the Wikipedia article "United States Military Academy grounds and facilities" (central area), "West Point Cadet Chapel", "Michie Stadium", "Fort Putnam", "Vassar College", "Main Building (Vassar College)", "Vassar College Observatory". Not dated here, though listed in the article: Cullum Hall and the other buildings the article names without a year, Superintendent's and Commandant's quarters (the article says 1820 / 1819 in its table and 1821 in its text; the footprints were not identified), Nininger Hall (1882; footprint not identified), the Old Cadet Chapel (1836, moved 1911), Eisenhower Hall, Jefferson Hall (2008; which Overture footprint it is was not settled).

## Not done / not checked

- Planned but not built: the Kensico Dam (1917; Wikipedia: 562 m long, 307 ft high, built 1913-1917, old dam 1885; no dam geometry could be fetched, Overpass failed), Playland's Music Tower in Rye (1928; the article gives opening and architects but no tower height), the Poughkeepsie Railroad Bridge's real span layout, the other four lower pylons of the Cuomo Bridge.
- The whole round was done without a screenshot; nothing was looked at on a screen. Heights of every building (except Lyndhurst's tower, Kykuit's roof, the dam, and the bridges' cited tower heights and clearances) are estimates.
- The old Tappan Zee Bridge's line is an estimate (78 m south of the new eastbound roadway); its actual piers are in no dataset at hand.
- Ground elevation: bridges are drawn from sea level with deck ends in the air or on abutment boxes (`-10 m` to the deck); where a shore is high (Bear Mountain, Newburgh) the anchorages are boxes that may be partly buried.
- The Overture footprints for Washington Hall, Michie Stadium, the Cadet Chapel (which reads as 8.3 m high) and Vassar's Main Building include later additions; the stages of the historical buildings are not reconstructed.
- No landmarks were modelled in Putnam, Sullivan, Orange outside West Point; West Point's other buildings (Cullum Hall, the Superintendent's quarters, the Old Cadet Chapel) are only in the dates table where a year is cited.
