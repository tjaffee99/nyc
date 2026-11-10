# New York made land, dug land and reservoirs: when each piece happened

Files covered here:

- `data/manual/fill_zones.csv`: 118 dated zones, one row per stage, for landfill, filled ponds and marshes, filled channels, excavations and reservoirs in the five boroughs.
- `data/manual/fill_tools/`: the scripts that built every ring from data on disk, and the checks.
- `data/raw/fill/` (gitignored): the downloads behind the dates. They are listed under "Sources".

## What the zones are for

The map's rule is "nothing stands before its ground". The terrain stage computes **made land = today's land − 1609 land** (the 1609 shore and marshes are another part, `data/manual/natural/`). The zones in this file supply the **dates**: when each piece of that difference became land, when a pond or marsh was filled, when upland was dug away, and when a reservoir held water.

So most rings are deliberately coarse. A coarse ring only has to cover its piece of made land and keep clear of neighbours with different dates. It usually contains natural upland as well, and it must be intersected with the data-derived difference. Lower Manhattan is the exception: there the fill went out in documented bands, street by street, and the rings follow those streets.

| | |
|---|---|
| rows | 118 |
| rings that follow real lines (`precise`) | 23 |
| rings that only bracket an area (`coarse`) | 95 |
| both dates stated by the source | 49 |
| one end stated, the other estimated | 31 |
| whole bracket estimated (the note says so) | 38 |

| borough | fill | pond_fill | water_fill | excavation | reservoir | rows |
|---|---|---|---|---|---|---|
| Manhattan | 34 | 4 | 1 | 4 | 4 | 47 |
| Harbour islands | 11 |  | 2 |  |  | 13 |
| Brooklyn | 18 | 1 | 3 | 1 | 1 | 24 |
| Queens | 13 | 2 | 1 |  | 3 | 19 |
| Bronx | 8 |  | 1 |  | 1 | 10 |
| Staten Island | 4 |  |  |  | 1 | 5 |
| **all** | 88 | 7 | 8 | 5 | 10 | 118 |


## Columns

`zone_id,name,borough,year_start,year_end,ring_type,ring,kind,precision,note,source_url`

- **zone_id**: stable. Prefix `mn_` Manhattan, `bk_` Brooklyn, `qn_` Queens, `bx_` Bronx, `si_` Staten Island, `hb_` harbour and river islands (Governors, Ellis, Randalls and Wards, Rikers, Roosevelt, U Thant, Mill Rock, Hoffman, Swinburne).
- **year_start / year_end**: when filling (or digging) began and when it was essentially done. Decimal years are allowed (1895.46 = 17 June 1895). The land grows across the span. Where the source only gives a bracket, or where a year is my estimate, the note says so.
- **ring_type**: always `lonlat`. **ring**: `lon lat; lon lat; …`, WGS84, 6 decimals, not closed, exterior only (no holes).
- **kind**:
  - `fill`: water or marsh becomes land.
  - `pond_fill`: a freshwater pond or a wetland inside the land is filled (the Collect, Lispenard Meadows, the Stuyvesant meadows, Harlem Marsh, Sunswick Meadows, Dyker Beach swamp, Alley Pond).
  - `water_fill`: a channel is filled (Spuyten Duyvil Creek round Marble Hill, Little Hell Gate, Bronx Kill, the middle of Coney Island Creek, Hog Creek, Bushwick Creek, Mott Haven Canal, Mill Creek at College Point).
  - `excavation`: land becomes water (the 1895 ship canal, the 1937–38 cut at Spuyten Duyvil, Paerdegat Basin, the Thirteenth Avenue fill taken out again for the Chelsea Piers).
  - `reservoir`: a made water body. `year_end` is when it was drained, or `9999` if it still holds water.
- **precision**:
  - `precise`: the ring follows real lines (named street centre lines, today's bulkhead, a water outline) and may be painted as drawn.
  - `coarse`: the ring only brackets the area. Intersect it with the data-derived fill.
- **note**: what the dates mean, with the source's words in quotation marks, and "estimated" for anything the source does not state.
- **source_url**: the page that supports the dates.

## How the rings were made

No coordinate was typed in from memory. Every vertex comes from data on disk, through `fill_tools/streets.py` and `fill_tools/zonelib.py`:

- **Street lines**: Overture `roads_region` + `roads_local` (2026-10-21.0). `Streets.x(a, b)` gives the crossing of two named streets, `Streets.along(name, p, q)` the shortest path along a named street's own segments. Streets are restricted to one land mass first (Manhattan Island, Long Island, the west Bronx), so that Brooklyn's Water Street cannot be picked up for Manhattan's; in Brooklyn and Queens a lon/lat box per neighbourhood tells apart streets that share a name. The boxes only filter. They never supply a vertex.
- **Today's shore**: the window minus Overture `base_water` polygons. A strip "from a street to the bulkhead" is the band between the street line and its offset, clipped to that land.
- **Outlines of parks, airports, islands, lakes**: Overture `region5_land_use`, `region_airports`, `base_land`, `base_water` by name; two NYC Parks outlines (`parks_properties.geojson`); three building footprints (Castle Clinton, Highbridge water tower and recreation centre); the Marble Hill tax lots from PLUTO.

Lower Manhattan, the rings that carry the story:

- **East River bands** (`mn_er_1` … `mn_er_3`, State St / Whitehall St to Dover St): Pearl St → Water St → Front St → South St and the bulkhead. Front St no longer exists south-west of Old Slip; there the line is Water St offset by the Water–Front spacing measured at Old Slip (59 m).
- **Two Bridges** (`mn_er_4`, `mn_er_5`, Dover St to Jackson St): Cherry St → Water St → South St. Cherry St no longer exists between Dover and Catherine St (straight line used).
- **Hudson bands** (`mn_hr_1` … `mn_hr_3`, Battery Place to Gansevoort St): Greenwich St → Washington St → the west side of old West St → the Department of Docks bulkhead. Old West St is taken as today's northbound carriageway (east side of Route 9A); its west side is 10.7 m beyond (half of 70 ft). The 1871 bulkhead line was "250 feet west of the line of West Street"; measured on the data, today's wall is a constant 61–63 m west of the northbound carriageway from Tribeca to Gansevoort St, so the bulkhead line is that carriageway + 62 m. Washington St is closed between Barclay and Hubert St, and south of Rector St the mapped street wanders round the tunnel plaza: straight lines are used there.
- **Battery Park City**: today's land west of that bulkhead line (34.9 ha against the 92 acres = 37.2 ha in the sources).
- **The Battery**: today's land south of Battery Place and west of Whitehall St. The 10 acres nearest State St / Whitehall St stand for the Battery before 1855 (a real area, an estimated outline: a 76 m band); the rest is the 1855–70 extension; Castle Clinton's footprint + 12 m is its artificial island.
- **Thirteenth Avenue**: the only surviving piece is the Gansevoort peninsula. Its outer face, carried north and south, is the line of the avenue (95 m beyond today's bulkhead). The strips between that line and today's bulkhead, W 11th St to W 22nd St, are the fill of 1837 that was removed again.
- **East River Drive strips** (`mn_east_river_park`, `mn_fdr_14_23`, `mn_bristol_basin`): today's land east of the FDR Drive centre line, which stands for the old bulkhead ("the area between the historic bulkhead line and the current bulkhead line … was landfilled in the 20th century").

## Sources

Dates come from these pages (rows per page):

- <https://en.wikipedia.org/wiki/FDR_Drive> (5 rows)
- <https://www.nyc.gov/assets/escr/downloads/pdf/FEIS/ESCR-EIS-Chapter-5.4-Historic-and-Cultural-Resources.pdf> (5 rows)
- <https://en.wikipedia.org/wiki/Land_reclamation_in_Lower_Manhattan> (4 rows)
- <https://en.wikipedia.org/wiki/Thirteenth_Avenue_(Manhattan)> (4 rows)
- <https://media.bpca.ny.gov/wp-content/uploads/2024/08/06043742/Appendix-D-Historic-and-Cultural-Resources.pdf> (4 rows)
- <https://en.wikipedia.org/wiki/Harlem_River> (3 rows)
- <https://en.wikipedia.org/wiki/Randalls_and_Wards_Islands> (3 rows)
- <https://en.wikipedia.org/wiki/Riverside_Park_(Manhattan)> (3 rows)
- <https://en.wikipedia.org/wiki/Spuyten_Duyvil_Creek> (3 rows)
- <https://en.wikipedia.org/wiki/Bush_Terminal> (2 rows)
- <https://en.wikipedia.org/wiki/Ellis_Island> (2 rows)
- <https://en.wikipedia.org/wiki/Ferry_Point_Park> (2 rows)
- <https://en.wikipedia.org/wiki/Flushing_Meadows%E2%80%93Corona_Park> (2 rows)
- <https://en.wikipedia.org/wiki/Howard_Beach,_Queens> (2 rows)
- <https://en.wikipedia.org/wiki/Jacob_Riis_Park> (2 rows)
- <https://en.wikipedia.org/wiki/Port_Morris,_Bronx> (2 rows)
- <https://en.wikipedia.org/wiki/Shirley_Chisholm_State_Park> (2 rows)
- <https://en.wikipedia.org/wiki/Spring_Creek_Park> (2 rows)
- <https://content.govdelivery.com/accounts/NYSDEC/bulletins/1b23eec> (1 row)
- <https://en.wikipedia.org/wiki/Alley_Pond_Park> (1 row)
- <https://en.wikipedia.org/wiki/Alphabet_City,_Manhattan> (1 row)
- <https://en.wikipedia.org/wiki/Battery_Park_City> (1 row)
- <https://en.wikipedia.org/wiki/Belt_Parkway> (1 row)
- <https://en.wikipedia.org/wiki/Broad_Channel,_Queens> (1 row)
- <https://en.wikipedia.org/wiki/Bronx_Kill> (1 row)
- <https://en.wikipedia.org/wiki/Brooklyn_Navy_Yard> (1 row)
- <https://en.wikipedia.org/wiki/Bushwick_Inlet> (1 row)
- <https://en.wikipedia.org/wiki/Calvert_Vaux_Park> (1 row)
- <https://en.wikipedia.org/wiki/Canal_Street_(Manhattan)> (1 row)
- <https://en.wikipedia.org/wiki/Canarsie,_Brooklyn> (1 row)
- <https://en.wikipedia.org/wiki/Castle_Clinton> (1 row)
- <https://en.wikipedia.org/wiki/Co-op_City,_Bronx> (1 row)
- <https://en.wikipedia.org/wiki/Collect_Pond> (1 row)
- <https://en.wikipedia.org/wiki/College_Point,_Queens> (1 row)
- <https://en.wikipedia.org/wiki/Coney_Island_Creek> (1 row)
- <https://en.wikipedia.org/wiki/Cross_Island_Parkway> (1 row)
- <https://en.wikipedia.org/wiki/Croton_Distributing_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/Dyker_Beach_Park> (1 row)
- <https://en.wikipedia.org/wiki/Edgemere_Landfill> (1 row)
- <https://en.wikipedia.org/wiki/Floyd_Bennett_Field> (1 row)
- <https://en.wikipedia.org/wiki/Franklin_D._Roosevelt_Boardwalk> (1 row)
- <https://en.wikipedia.org/wiki/Fresh_Kills_Landfill> (1 row)
- <https://en.wikipedia.org/wiki/Front_Street_(Manhattan)> (1 row)
- <https://en.wikipedia.org/wiki/Fulton_Ferry,_Brooklyn> (1 row)
- <https://en.wikipedia.org/wiki/Governors_Island> (1 row)
- <https://en.wikipedia.org/wiki/Gowanus_Canal> (1 row)
- <https://en.wikipedia.org/wiki/Great_Kills_Park> (1 row)
- <https://en.wikipedia.org/wiki/Great_Lawn_and_Turtle_Pond> (1 row)
- <https://en.wikipedia.org/wiki/Greenpoint,_Brooklyn> (1 row)
- <https://en.wikipedia.org/wiki/Harlem_Meer> (1 row)
- <https://en.wikipedia.org/wiki/Harlem_River_Drive> (1 row)
- <https://en.wikipedia.org/wiki/Henry_Hudson_Parkway> (1 row)
- <https://en.wikipedia.org/wiki/Highbridge_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/Hoffman_Island> (1 row)
- <https://en.wikipedia.org/wiki/Hunters_Point,_Queens> (1 row)
- <https://en.wikipedia.org/wiki/Hunts_Point,_Bronx> (1 row)
- <https://en.wikipedia.org/wiki/Jacqueline_Kennedy_Onassis_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/Jerome_Park_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/John_F._Kennedy_International_Airport> (1 row)
- <https://en.wikipedia.org/wiki/Kips_Bay,_Manhattan> (1 row)
- <https://en.wikipedia.org/wiki/LaGuardia_Airport> (1 row)
- <https://en.wikipedia.org/wiki/Marine_Park_(Brooklyn_park)> (1 row)
- <https://en.wikipedia.org/wiki/Meadow_Lake_(Queens)> (1 row)
- <https://en.wikipedia.org/wiki/Meatpacking_District,_Manhattan> (1 row)
- <https://en.wikipedia.org/wiki/Mill_Basin,_Brooklyn> (1 row)
- <https://en.wikipedia.org/wiki/Mill_Rock> (1 row)
- <https://en.wikipedia.org/wiki/Mount_Prospect_Park> (1 row)
- <https://en.wikipedia.org/wiki/Orchard_Beach_(Bronx)> (1 row)
- <https://en.wikipedia.org/wiki/Paerdegat_Basin> (1 row)
- <https://en.wikipedia.org/wiki/Plumb_Beach,_Brooklyn> (1 row)
- <https://en.wikipedia.org/wiki/Red_Hook,_Brooklyn> (1 row)
- <https://en.wikipedia.org/wiki/Ridgewood_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/Rikers_Island> (1 row)
- <https://en.wikipedia.org/wiki/Roosevelt_Island> (1 row)
- <https://en.wikipedia.org/wiki/Soundview_Park> (1 row)
- <https://en.wikipedia.org/wiki/Starrett_City> (1 row)
- <https://en.wikipedia.org/wiki/Sunswick_Creek> (1 row)
- <https://en.wikipedia.org/wiki/Swinburne_Island> (1 row)
- <https://en.wikipedia.org/wiki/The_Battery_(Manhattan)> (1 row)
- <https://en.wikipedia.org/wiki/Turtle_Bay,_Manhattan> (1 row)
- <https://en.wikipedia.org/wiki/U_Thant_Island> (1 row)
- <https://en.wikipedia.org/wiki/Williamsburg,_Brooklyn> (1 row)
- <https://en.wikipedia.org/wiki/Willow_Lake_(Queens)> (1 row)
- <https://storymaps.arcgis.com/stories/916b995ed91040e99dab72964fa2a188> (1 row)

What they are, and the terms:

| Source | Used for | Licence / terms |
|---|---|---|
| English Wikipedia articles, fetched as wikitext with `fill_tools/wiki_fetch.py` into `data/raw/fill/wiki/` (about 290 articles; the row's `source_url` names the one used) | most dates; quoted sentences in the notes | text CC BY-SA 4.0; cite the article |
| Battery Park City Authority, *North/West Battery Park City Resiliency Project — Phase 1A Archaeological Documentary Study* (AKRF, 2024), Appendix D of the project's environmental review. `data/raw/fill/pdf/bpca_appendix_d_historic.pdf` | Hudson side: high-water mark at Greenwich St, water-lot grants of 1805–07, West St filled by 1836, bulkhead lines of 1857 and 1871, bulkhead wall 1871–1935 | New York State public authority document, published for public review; cited, not redistributed |
| City of New York, *East Side Coastal Resiliency Project FEIS*, chapter 5.4 Historic and Cultural Resources. `data/raw/fill/pdf/escr_feis_5_4_historic.pdf` | East River, Montgomery St to E 25th St: filled "between the 1810s and about 1850", East River Park fill of the 1930s, E 23rd–25th St piers and fill | NYC government publication; cited, not redistributed |
| NYS DEC bulletin on the Brookfield Avenue Landfill; ArcGIS StoryMap "Silver Lake Reservoir" | `si_brookfield_landfill`, `si_silver_lake_reservoir` | read **only through a search-result summary**, the pages themselves were not opened: treat these two dates as lightly verified |
| Overture Maps 2026-10-21.0 extracts already on disk (`data/raw/overture/`) | all geometry | OpenStreetMap-derived layers ODbL; Overture's own CDLA Permissive 2.0 |
| NYC Open Data: building footprints, Parks properties, PLUTO (already on disk) | Castle Clinton, Highbridge, Mount Prospect Park, Marble Hill lots | NYC Open Data terms of use (public) |

Not found: a GIS dataset of dated Manhattan shorelines. One web search turned up only scanned maps (the 1865 Viele map, the 1873 Department of Docks map of the original high- and low-water lines). Tracing those two maps is the way to replace the estimated inner edges and to split the bands block by block.

## Rules for the terrain stage

1. **Coarse rings** are brackets. Use them only on cells of (today's land − 1609 land), or of the 1609 pond / marsh / channel layer for `pond_fill` and `water_fill`. They contain natural upland (all of Governors Island's old half, Rikers' core, the bluff along the East River Drive, Port Morris, Inwood…).
2. **Precise rings** may be painted as drawn, with one caution: the inner edge of the innermost bands (`mn_er_1_pearl_water` along Pearl St, `mn_hr_1_greenwich_washington` along Greenwich St, `mn_battery_early` along State St) is a street that *approximates* the pre-fill shore. Where the mapped 1609 shore disagrees, the 1609 layer wins. Do not make water inland of it.
3. **Grow each band from its inland edge outward** across its span. Houses on the south side of Water St (for example the Rose house of the 1770s at 273 Water St) stood on band 2 long before its outer edge was land.
4. **Overlaps inside `fill`**: the earliest `year_end` wins. This is what puts Castle Clinton (1811) on its island inside `mn_battery_1855`, and it settles the few slivers where neighbouring strips share an end.
5. **A ring of another kind inside or across a `fill` ring wins inside its own outline**: `hb_little_hell_gate` and `hb_bronx_kill_fill` against the Randalls / Wards island rings, `bk_bushwick_creek` against the Williamsburg and Greenpoint shore rings, `bx_mott_haven_canal` and `mn_marble_hill_creek_bed` against `bx_harlem_river_shore`, `mn_stuyvesant_meadows`, `qn_sunswick_meadows`, `mn_east_harlem_flats`, and every `reservoir`.
6. **`excavation`** rings apply to cells that are water today. Before `year_start` those cells are land if the 1609 layer or an earlier fill row says so:
   - `mn_hr_13th_avenue_fill` (1837–1860) makes land in what is water today; `mn_hr_13th_avenue_cut_s` and `_cut_n` (1902–1910) take it away again. The three rings are precise and are meant to be painted. The Gansevoort peninsula is inside the fill ring and outside both cuts.
   - `mn_ship_canal_1895`, `mn_spuyten_duyvil_cut_1938`, `bk_paerdegat_basin` are coarse: only the part that was land in 1609 was dug.
7. **`reservoir`**: water from `year_start` to `year_end`, land before and after. Exception: Silver Lake was a natural lake before 1917.
8. **Natural accretion** is in the file as `fill` with "Not made land" in the note (`qn_rockaway_point_accretion`, `qn_breezy_point_tip`): the sand spit grew westward by itself. Paint it as beach, not as a bulkheaded shore.
9. **Piers that Overture counts as land.** Along the Hudson, piers are not land in the data (the bulkhead check above shows it). But some decks on piles are land polygons and fall inside rings: the Brooklyn Bridge Park piers in `bk_fulton_ferry_dumbo`, Waterside Plaza (a 1970s platform) in `mn_bristol_basin`, the ferry slips at the tip of `mn_battery_1855`, finger piers in `bk_red_hook`, `bk_sunset_park_waterfront` and `bk_wallabout_navy_yard`. Along South St the bands stop 80–90 m outside the street centre line so that Pier 15–17 stay out.

## Weak spots

- **Band dates in Lower Manhattan are anchors, not a surveyed progression.** Sources give "waterfront at Water St in 1730, Front St in 1780, South St in 1800", a slip filled "by 1788", West St "largely filled by the 1836 map". Inside a band the order of blocks is unknown.
- **`mn_hr_1_greenwich_washington` start (1739)** and the whole of `mn_hr_1n` (north of Chambers St) are estimated. North of Chambers St fast land reached west of Greenwich St in places, so that band is coarse.
- **Two Bridges and the Lower East Side** (`mn_er_4`, `mn_er_5`, `mn_er_corlears_14th`): the dates are brackets from an archaeological study of the river strip; the corner at Corlears St / Water St (East River Park amphitheatre) was only filled in the 1870s–80s and is not split off.
- **Old West St = today's northbound carriageway** is an assumption (±5 m). It moves the line between bands 2 and 3, not the outer edge.
- **Everything north of 14th St on Manhattan and most of the outer boroughs is coarse**, and many brackets are estimates with no dated source (the table says which). They are meant to keep buildings off the water, not to tell the story.
- **Whole-island and whole-park rings** (Governors, Ellis, Rikers, Roosevelt, Randalls / Wards, JFK, LaGuardia, Floyd Bennett Field, Fresh Kills, Marine Park, Great Kills) carry one bracket for everything inside. Later enlargements inside them are not dated separately (JFK after 1948, LaGuardia's runways 1965–66, Floyd Bennett Field 1936–42, Bergen Beach 1980s, the Twin Islands gap at Orchard Beach 1946–47).
- **`mn_marble_hill_creek_bed`** is a 230 m collar round the hull of the Marble Hill tax lots, not the creek's outline. **`bk_coney_island_creek_middle`** is a straight corridor where the creek wound.
- **Reservoir outlines**: only the Central Park, Jerome Park and Silver Lake reservoirs and the two Flushing Meadows lakes are real outlines. The Croton receiving reservoir is a rectangle round today's Great Lawn and Turtle Pond; the distributing reservoir is a square on Fifth Avenue; Highbridge is a 7-acre circle; Ridgewood is the hull of the wooded basin floors.

## Not covered (no date, or no outline on disk)

- Manhattan: Minetta Creek and its ponds; Sunfish Pond; Beekman's Swamp; the filled loop of Spuyten Duyvil Creek behind the north end of Inwood Hill Park; the Dyckman St marsh on the Hudson side; lakes and ponds made inside Central Park (the Lake, Harlem Meer, the Pond).
- Islands: Liberty Island (its south-western 4.17 acres are reclaimed; no date found); North and South Brother; Hart; Shooters; the Jamaica Bay islands changed by dredging.
- Brooklyn: Atlantic Basin and Erie Basin as water bodies (they are inside `bk_red_hook`); Sheepshead Bay bulkheads; Coney Island's west end; Newtown Creek and Mussel Island (dredged away by the 1930s).
- Queens: Hallets Cove and the Astoria shore; Whitestone and Powells Cove; the bay side of the Rockaway peninsula; Willets Point apart from the ash dump ring.
- Bronx: Clason Point and Throgs Neck; the Pelham Bay (Tallapoosa Point) landfill, opened 1963, no outline on disk; the head of Westchester Creek; Williamsbridge Reservoir (the article calls it a natural lake; left out).
- Staten Island: the north and west shores (St George, Howland Hook, Port Ivory, Bloomfield, Travis), the Stapleton piers of 1920, Miller Field.

## Checks (`fill_tools/build_zones.py`, `check_zones.py`, `qa_plot.py`)

- Every ring read back from the CSV is a valid polygon with its centroid inside the map box; ids are unique; kinds and precisions are from the lists.
- Band order: going outward no band is older than the one inland of it (East River 1730 < 1788 < 1815; Hudson 1797 < 1836 < 1903 < 1976).
- Overlaps over 0.25 ha are listed by the build. Between precise rings only the two deliberate ones remain (Thirteenth Avenue fill / cuts, Castle Clinton's island inside the Battery extension).
- Known buildings fall where they should: Fraunces Tavern in band 1 (its block was a water lot of 1686), Castle Clinton on its island, the Marine Air Terminal in LaGuardia, the Javits Center in the West Side fill.
- Precise rings lie on today's land (97–100 %), except the Thirteenth Avenue rings, which lie in today's water on purpose.
- 89 % of the NYC Parks outline of East River Park lies inside `mn_east_river_park`.
- Plots of the zones over land and streets were looked at (Lower Manhattan, East Side, West Side, the northern tip, the Harlem River, western Brooklyn, Jamaica Bay, the north-east). They are scratch files in `data/interim/fill/`.

## Rebuilding

```
P=.venv/bin/python; T=data/manual/fill_tools
$P $T/wiki_fetch.py $T/wiki_titles.txt; $P $T/wiki_fetch.py $T/wiki_titles2.txt   # cached downloads
$P - <<<'import sys; sys.path.insert(0,"data/manual/fill_tools"); from zonelib import *; import pickle,os
S=island_streets((-74.03,40.695,-73.905,40.882),"Broadway","Chambers Street"); S.con=None
pickle.dump(S,open(os.path.join(INTERIM,"mn_streets.pkl"),"wb"))
S=island_streets((-73.935,40.785,-73.765,40.918),"Grand Concourse","East 161st Street"); S.con=None
pickle.dump(S,open(os.path.join(INTERIM,"bx_streets.pkl"),"wb"))'
(cd $T && ../../../$P li_load.py)                      # Brooklyn + Queens street index
$P $T/west_st_nb.py                                    # northbound carriageway of West St
for m in zones_mn_a zones_mn_b zones_misc zones_hb zones_bk zones_qn zones_bx_si; do $P $T/$m.py; done
$P $T/build_zones.py && $P $T/check_zones.py && $P $T/make_readme.py
```

`zones_mn_a.py` must run before `zones_mn_b.py` only for reading order; the scripts are independent and each saves `data/interim/fill/rows_<area>.json`.

## Every zone

"dates": `documented` = both years stated by the source; `one end estimated`; `estimated bracket` = no dated source, the note says so.

| zone_id | years | kind | ring | dates | ha |
|---|---|---|---|---|---|
| `mn_er_1_pearl_water` | 1686–1730 | fill | precise | documented | 9.1 |
| `mn_er_2_water_front` | 1731–1788 | fill | precise | documented | 7.5 |
| `mn_er_3_front_south` | 1798–1815 | fill | precise | documented | 15.5 |
| `mn_er_4_cherry_water` | 1780–1810 | fill | coarse | estimated bracket | 11.1 |
| `mn_er_5_water_south_two_bridges` | 1800–1850 | fill | precise | estimated bracket | 20.6 |
| `mn_er_corlears_14th` | 1810–1850 | fill | coarse | documented | 50.4 |
| `mn_east_river_park` | 1936–1939.57 | fill | precise | one end estimated | 22.5 |
| `mn_stuyvesant_meadows` | 1820–1845 | pond_fill | coarse | estimated bracket | 90.2 |
| `mn_er_stuyvesant_cove` | 1830–1880 | fill | coarse | estimated bracket | 49.3 |
| `mn_er_23_34` | 1835–1900 | fill | coarse | documented | 20.7 |
| `mn_fdr_14_23` | 1938–1940.4 | fill | precise | one end estimated | 4.0 |
| `mn_bristol_basin` | 1940–1941.8 | fill | precise | one end estimated | 9.3 |
| `mn_hr_1_greenwich_washington` | 1739–1797 | fill | precise | one end estimated | 9.5 |
| `mn_hr_1n_greenwich_washington` | 1760–1800 | fill | coarse | estimated bracket | 22.5 |
| `mn_hr_2_washington_west` | 1795–1836 | fill | precise | documented | 43.4 |
| `mn_hr_3_west_bulkhead` | 1871–1903 | fill | precise | documented | 19.4 |
| `mn_battery_park_city` | 1967–1976.5 | fill | precise | one end estimated | 34.9 |
| `mn_battery_early` | 1683–1826 | fill | coarse | documented | 4.0 |
| `mn_battery_1855` | 1855–1870 | fill | precise | one end estimated | 11.4 |
| `mn_hr_13th_avenue_fill` | 1837–1860 | fill | precise | one end estimated | 22.3 |
| `mn_hr_13th_avenue_cut_s` | 1902–1910 | excavation | precise | one end estimated | 5.0 |
| `mn_hr_13th_avenue_cut_n` | 1902–1910 | excavation | precise | one end estimated | 15.8 |
| `mn_hr_chelsea` | 1825–1855 | fill | coarse | estimated bracket | 22.5 |
| `mn_hr_23_59` | 1837–1880 | fill | coarse | estimated bracket | 167.4 |
| `mn_hr_59_72` | 1870–1890 | fill | coarse | estimated bracket | 35.2 |
| `mn_riverside_park_fill` | 1934–1937 | fill | coarse | documented | 89.8 |
| `mn_hr_122_155` | 1850–1937 | fill | coarse | estimated bracket | 52.6 |
| `mn_hr_155_dyckman` | 1934–1937 | fill | coarse | estimated bracket | 73.0 |
| `mn_er_34_42_kips_bay` | 1850–1880 | fill | coarse | estimated bracket | 8.9 |
| `mn_er_42_49_turtle_bay` | 1850–1868 | fill | coarse | one end estimated | 24.0 |
| `mn_fdr_34_49` | 1940–1942.4 | fill | coarse | one end estimated | 5.6 |
| `mn_fdr_49_96` | 1938–1940.5 | fill | coarse | one end estimated | 15.8 |
| `mn_fdr_96_125` | 1934–1936.9 | fill | coarse | one end estimated | 10.8 |
| `mn_east_harlem_flats` | 1870–1890 | pond_fill | coarse | estimated bracket | 311.6 |
| `mn_harlem_river_125_155` | 1870–1900 | fill | coarse | estimated bracket | 141.3 |
| `mn_harlem_river_speedway` | 1894–1898.5 | fill | coarse | documented | 21.3 |
| `mn_sherman_creek_flats` | 1900–1935 | fill | coarse | estimated bracket | 44.8 |
| `mn_ship_canal_1895` | 1888–1895.46 | excavation | coarse | documented | 15.4 |
| `mn_marble_hill_creek_bed` | 1913–1914 | water_fill | coarse | documented | 36.6 |
| `mn_spuyten_duyvil_cut_1938` | 1937–1938 | excavation | coarse | documented | 23.7 |
| `mn_collect_pond` | 1803–1811 | pond_fill | coarse | documented | 24.2 |
| `mn_lispenard_meadows` | 1805–1819 | pond_fill | coarse | one end estimated | 27.3 |
| `mn_central_park_reservoir` | 1862–9999 | reservoir | precise | documented | 38.7 |
| `mn_croton_receiving_reservoir` | 1842.49–1930 | reservoir | coarse | documented | 14.2 |
| `mn_croton_distributing_reservoir` | 1842–1899 | reservoir | coarse | documented | 2.1 |
| `mn_castle_clinton_island` | 1808–1811 | fill | precise | documented | 0.5 |
| `mn_highbridge_reservoir` | 1872–1934 | reservoir | coarse | documented | 2.8 |
| `hb_governors_island_fill` | 1901–1913 | fill | coarse | one end estimated | 69.6 |
| `hb_ellis_island_north` | 1890–1896 | fill | coarse | documented | 5.4 |
| `hb_ellis_island_south` | 1898–1934 | fill | coarse | one end estimated | 5.8 |
| `hb_little_hell_gate` | 1955–1962 | water_fill | coarse | documented | 34.6 |
| `hb_randalls_island_shore` | 1934–1962 | fill | coarse | estimated bracket | 84.6 |
| `hb_wards_island_shore` | 1934–1962 | fill | coarse | estimated bracket | 98.5 |
| `hb_rikers_island` | 1884–1943 | fill | coarse | documented | 167.1 |
| `hb_roosevelt_island_shore` | 1830–1975 | fill | coarse | estimated bracket | 57.9 |
| `hb_u_thant_island` | 1905–1907 | fill | precise | documented | 0.1 |
| `hb_mill_rock` | 1890–1890.9 | fill | coarse | documented | 1.0 |
| `hb_hoffman_island` | 1860–1873 | fill | precise | documented | 4.1 |
| `hb_swinburne_island` | 1860–1870 | fill | precise | documented | 1.0 |
| `hb_bronx_kill_fill` | 1936–1965 | water_fill | coarse | estimated bracket | 19.1 |
| `bk_mount_prospect_reservoir` | 1856–1938 | reservoir | coarse | documented | 1.8 |
| `bk_fulton_ferry_dumbo` | 1800–1860 | fill | coarse | estimated bracket | 58.9 |
| `bk_wallabout_navy_yard` | 1801–1942 | fill | coarse | estimated bracket | 248.6 |
| `bk_red_hook` | 1840–1880 | fill | coarse | estimated bracket | 258.8 |
| `bk_gowanus` | 1849–1869 | fill | coarse | one end estimated | 111.2 |
| `bk_bush_terminal_piers_infill` | 1974–1978 | fill | coarse | one end estimated | 13.5 |
| `bk_sunset_park_waterfront` | 1890–1919.7 | fill | coarse | one end estimated | 142.3 |
| `bk_shore_parkway` | 1934–1940.5 | fill | coarse | one end estimated | 64.1 |
| `bk_dyker_beach` | 1918–1934 | pond_fill | coarse | one end estimated | 87.4 |
| `bk_coney_island_creek_middle` | 1920–1937 | water_fill | coarse | estimated bracket | 91.1 |
| `bk_calvert_vaux_park` | 1962–1965 | fill | coarse | one end estimated | 36.8 |
| `bk_plumb_beach_hog_creek` | 1937–1940 | water_fill | coarse | estimated bracket | 38.9 |
| `bk_floyd_bennett_field` | 1928–1931.4 | fill | coarse | documented | 520.3 |
| `bk_marine_park` | 1931–1939 | fill | coarse | estimated bracket | 335.3 |
| `bk_mill_basin_bergen_beach` | 1895–1939 | fill | coarse | documented | 376.2 |
| `bk_paerdegat_basin` | 1925–1931 | excavation | coarse | estimated bracket | 72.6 |
| `bk_canarsie_shore` | 1900–1940 | fill | coarse | estimated bracket | 132.5 |
| `bk_starrett_city` | 1955–1972 | fill | coarse | estimated bracket | 145.9 |
| `bk_pennsylvania_avenue_landfill` | 1956–1985 | fill | coarse | documented | 38.8 |
| `bk_fountain_avenue_landfill` | 1961–1985 | fill | coarse | documented | 125.0 |
| `bk_spring_creek_park` | 1948–1954 | fill | coarse | one end estimated | 55.5 |
| `bk_williamsburg_shore` | 1830–1890 | fill | coarse | estimated bracket | 29.7 |
| `bk_greenpoint_shore` | 1830–1890 | fill | coarse | estimated bracket | 41.9 |
| `bk_bushwick_creek` | 1896–1913 | water_fill | coarse | documented | 88.5 |
| `qn_ridgewood_reservoir` | 1858.88–1989 | reservoir | coarse | documented | 27.5 |
| `qn_hunters_point_shore` | 1850–1900 | fill | coarse | estimated bracket | 60.4 |
| `qn_sunswick_meadows` | 1871–1915 | pond_fill | coarse | documented | 69.6 |
| `qn_laguardia_airport` | 1937–1939.8 | fill | coarse | documented | 281.8 |
| `qn_corona_ash_dump` | 1910–1934 | fill | coarse | documented | 436.9 |
| `qn_flushing_meadows_south` | 1936–1939.3 | fill | coarse | one end estimated | 225.2 |
| `qn_meadow_lake` | 1938–9999 | reservoir | precise | one end estimated | 39.4 |
| `qn_willow_lake` | 1938–9999 | reservoir | precise | one end estimated | 18.1 |
| `qn_college_point_mill_creek` | 1930–1965 | water_fill | coarse | estimated bracket | 137.3 |
| `qn_cross_island_little_neck_bay` | 1938–1940.5 | fill | coarse | one end estimated | 72.2 |
| `qn_alley_pond` | 1952–1954 | pond_fill | coarse | one end estimated | 45.1 |
| `qn_jfk_airport` | 1943–1948.5 | fill | coarse | documented | 1606.9 |
| `qn_howard_beach_east` | 1897–1914 | fill | coarse | documented | 193.8 |
| `qn_howard_beach_west` | 1950–1962 | fill | coarse | estimated bracket | 270.4 |
| `qn_spring_creek_park_howard_beach` | 1949.05–1954 | fill | coarse | documented | 102.9 |
| `qn_broad_channel` | 1915–1925 | fill | coarse | estimated bracket | 95.6 |
| `qn_edgemere_landfill` | 1938.4–1991 | fill | coarse | documented | 81.2 |
| `qn_rockaway_point_accretion` | 1830–1933 | fill | coarse | estimated bracket | 513.0 |
| `qn_breezy_point_tip` | 1933–1975 | fill | coarse | estimated bracket | 141.8 |
| `bx_jerome_park_reservoir` | 1906–9999 | reservoir | precise | documented | 37.7 |
| `bx_mott_haven_canal` | 1896–1965 | water_fill | coarse | documented | 12.5 |
| `bx_hunts_point_markets` | 1950–1972 | fill | coarse | estimated bracket | 217.5 |
| `bx_port_morris_oak_point` | 1870–1920 | fill | coarse | estimated bracket | 299.4 |
| `bx_harlem_river_shore` | 1870–1956 | fill | coarse | estimated bracket | 159.8 |
| `bx_soundview_park` | 1939–1960 | fill | coarse | one end estimated | 93.5 |
| `bx_ferry_point_west` | 1937–1940 | fill | coarse | documented | 49.6 |
| `bx_ferry_point_east` | 1950–1970 | fill | coarse | one end estimated | 76.3 |
| `bx_co_op_city` | 1950–1968 | fill | coarse | one end estimated | 169.4 |
| `bx_orchard_beach` | 1935–1938 | fill | coarse | documented | 130.8 |
| `si_silver_lake_reservoir` | 1917–9999 | reservoir | coarse | documented | 19.0 |
| `si_brookfield_landfill` | 1966–1980 | fill | coarse | documented | 99.0 |
| `si_fresh_kills_landfill` | 1948.3–2001 | fill | coarse | documented | 968.4 |
| `si_great_kills_park` | 1929–1949 | fill | coarse | documented | 365.0 |
| `si_south_midland_beach` | 1935–1937 | fill | coarse | documented | 76.3 |

