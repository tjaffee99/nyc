# New York made land, dug land and reservoirs: when each piece happened

Files covered here:

- `data/manual/fill_zones.csv`: {{ROWS}} dated zones, one row per stage, for landfill, filled ponds and marshes, filled channels, excavations and reservoirs in the five boroughs.
- `data/manual/fill_tools/`: the scripts that built every ring from data on disk, and the checks.
- `data/raw/fill/` (gitignored): the downloads behind the dates. They are listed under "Sources".

## What the zones are for

The map's rule is "nothing stands before its ground". The terrain stage computes **made land = today's land − 1609 land** (the 1609 shore and marshes are another part, `data/manual/natural/`). The zones in this file supply the **dates**: when each piece of that difference became land, when a pond or marsh was filled, when upland was dug away, and when a reservoir held water.

So most rings are deliberately coarse. A coarse ring only has to cover its piece of made land and keep clear of neighbours with different dates. It usually contains natural upland as well, and it must be intersected with the data-derived difference. Lower Manhattan is the exception: there the fill went out in documented bands, street by street, and the rings follow those streets.

| | |
|---|---|
| rows | {{ROWS}} |
| rings that follow real lines (`precise`) | {{N_PRECISE}} |
| rings that only bracket an area (`coarse`) | {{N_COARSE}} |
| both dates stated by the source | {{N_DOC}} |
| one end stated, the other estimated | {{N_ONE}} |
| whole bracket estimated (the note says so) | {{N_EST}} |

{{TABLE_COUNTS}}

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

{{SOURCES}}
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

{{TABLE_ZONES}}
