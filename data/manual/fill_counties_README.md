# Made land, dug land and reservoirs in the eight counties: when each piece happened

The same job as `fill_README.md` did for the five boroughs, for Hudson, Bergen, Essex, Union and Passaic (New Jersey) and Westchester, Nassau and Rockland (New York). Read that file first: the format and the rules are the same. This file only says what is different.

Files:

- `data/manual/fill_zones_counties.csv`: 70 dated zones, exactly the columns of `fill_zones.csv`. `borough` holds the county name.
- `data/manual/fill_counties_tools/`: the scripts that built every ring from data on disk, and the checks.
- `data/raw/fill_counties/` (gitignored): this part's Overture extracts of the wider box, 328 Wikipedia articles as wikitext, and the other pages behind the dates.

| | |
|---|---|
| rows | 70 |
| reservoir outlines (`precise`) | 28 |
| rings that only bracket an area (`coarse`) | 42 |
| both dates stated by the source | 40 |
| one end stated, the other estimated | 21 |
| whole bracket estimated (the note says so) | 9 |

| county | fill | pond_fill | water_fill | excavation | reservoir | rows | documented | one end estimated | estimated bracket |
|---|---|---|---|---|---|---|---|---|---|
| Hudson | 22 |  |  |  | 1 | 23 | 8 | 8 | 7 |
| Bergen | 7 |  |  |  | 4 | 11 | 5 | 5 | 1 |
| Essex | 2 |  |  |  | 3 | 5 | 3 | 2 |  |
| Union | 1 |  |  |  | 1 | 2 | 2 |  |  |
| Passaic |  |  |  |  | 6 | 6 | 6 |  |  |
| Westchester | 5 |  |  |  | 9 | 14 | 12 | 1 | 1 |
| Nassau | 4 |  |  |  | 1 | 5 | 1 | 4 |  |
| Rockland | 1 |  |  |  | 3 | 4 | 3 | 1 |  |
| **all** | 42 | 0 | 0 | 0 | 28 | 70 | 40 | 21 | 9 |


There is no `pond_fill`, `water_fill` or `excavation` row: no filled channel or dug basin in these counties came with both a date and an outline (see "Noted, not in the file").

## Columns

`zone_id,name,borough,year_start,year_end,ring_type,ring,kind,precision,note,source_url`: as in `fill_README.md`. Prefixes: `hud_` Hudson, `ber_` Bergen, `ess_` Essex, `uni_` Union, `pas_` Passaic, `wes_` Westchester, `nas_` Nassau, `roc_` Rockland. For a reservoir `year_start` is the year the water rose and `year_end` is `9999` (all of them still hold water).

**No `fill` ring here is `precise`.** Unlike Lower Manhattan, no source at hand gives the fill of these shores street by street. Every fill ring is a bracket to be intersected with (today's land − 1609 land). The only `precise` rings are water outlines of reservoirs.

## How the rings were made

No coordinate was typed in. Every vertex comes from Overture Maps 2026-10-21.0, queried for the wider box (-74.52, 40.47, -73.40, 41.38) by `download_overture.py` (the lead's extracts cover only the city's box): roads, railways, water, land, land use, infrastructure outlines and municipal outlines (`theme=divisions`). `streets.py` and `zonelib.py` are copies of the city's tools with a few functions added (the list is at the end of `zonelib.py`).

- **Jersey City, downtown** (`zones_hud_a.py`): the base line is Marin Boulevard (Henderson Street), cut at Grand Street, Columbus Drive and 6th Street. East of it: Paulus Hook (south of Columbus Drive), Harsimus Cove in two bands (the first quarter mile = 402 m "from Henderson Street", and the rest), and the Long Dock fill (6th Street to the city line). West of it: a band 1 km deep, split at Grand Street into the Harsimus meadow and South Cove.
- **Hoboken**: the municipal outline on today's land, less the outline of the terminal and yard.
- **Communipaw to Constable Hook** (`zones_hud_b.py`): the inland line is the Turnpike's Newark Bay extension from Grand Street to Kennedy Boulevard, then Avenue E, which runs beside the old Central Railroad line along Bayonne's east shore. Today's land east of that line is cut into: the Central Railroad's ground; a 330 m band round Morris Pesin Drive (Black Tom); Caven Point, down to the line of Chapel Avenue; Greenville Yard, down to the line of Port Jersey Boulevard; the Port Jersey peninsula (land within 520 m of its boulevard, from 1.1 km out); the Ocean Terminal peninsula (land within 420–650 m of Port Terminal Boulevard and of its chord carried to the root); Constable Hook (land within 1.3 km of New Hook Road, plus the golf club outline).
- **Weehawken to Edgewater**: today's land east of the line Willow Avenue – Port Imperial Boulevard – River Road, which runs at the foot of the Palisades, cut by the municipal outlines.
- **Named outlines** as they stand in Overture: Lincoln Park, Kearny Point, the landfills (Keegan, Malanka, Kingsland, Avon, Erie), Teterboro and Newark airports, Port Newark–Elizabeth (cut at the Newark / Elizabeth line), Croton Point Park, the Edge-on-Hudson site (the General Motors plant), Glen Island, Jones Beach State Park.
- **Hulls**: the Sports Complex (footprints of the arena, the mall and the racetrack + 450 m), Overpeck (park and golf course outlines), Playland (amusement park and lake + 120 m), Droyers Point (the streets of Society Hill and Droyers Point + 150 m). These are estimated outlines and lie partly over water.
- **Hudson River Railroad**: the westernmost track of Overture's "Hudson Line" in every 120 m of northing from the Yonkers line to the north end of Croton Point Park; the ring is today's land west of that line plus 45 m east of it.
- **Whole municipalities on today's land**: Hoboken, Long Beach, Atlantic Beach, Island Park. **Piermont**: the village's land east of Piermont Avenue (the pier and its root).
- **Reservoirs**: the Overture water outline of that name. Outlines that a road causeway splits are joined by a 30 m closing; a part that stays separate is its own row (`ber_oradell_reservoir_b`). Rings are exterior only, so islands are inside them.

## Sources

Dates come from these pages (rows per page):

- <https://en.wikipedia.org/wiki/Harsimus> (2 rows)
- <https://en.wikipedia.org/wiki/Oradell_Reservoir> (2 rows)
- <https://en.wikipedia.org/wiki/Weehawken_Terminal> (2 rows)
- <https://19january2025snapshot.epa.gov/hwcorrectiveactioncleanups/hazardous-waste-cleanup-military-ocean-terminal-bayonne-new-jersey> (1 row)
- <https://betterwaterfront.org/in-the-1700s-hoboken-was-an-island-in-2012-during-superstorm-sandy-75-of-hoboken-was-again-under-water/> (1 row)
- <https://en.wikipedia.org/wiki/Amawalk_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/Atlantic_Beach,_New_York> (1 row)
- <https://en.wikipedia.org/wiki/Barnum_Island,_New_York> (1 row)
- <https://en.wikipedia.org/wiki/Black_Tom_explosion> (1 row)
- <https://en.wikipedia.org/wiki/Branch_Brook_Park> (1 row)
- <https://en.wikipedia.org/wiki/Constable_Hook> (1 row)
- <https://en.wikipedia.org/wiki/Cross_River_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/Croton_Point_Park> (1 row)
- <https://en.wikipedia.org/wiki/Droyer%27s_Point> (1 row)
- <https://en.wikipedia.org/wiki/Edgewater,_New_Jersey> (1 row)
- <https://en.wikipedia.org/wiki/Federal_Shipbuilding_and_Drydock_Company> (1 row)
- <https://en.wikipedia.org/wiki/Glen_Island_Park> (1 row)
- <https://en.wikipedia.org/wiki/Grassy_Sprain_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/Greenville_Yard> (1 row)
- <https://en.wikipedia.org/wiki/Greenwood_Lake> (1 row)
- <https://en.wikipedia.org/wiki/Hempstead_Lake_State_Park> (1 row)
- <https://en.wikipedia.org/wiki/Hillview_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/Hoboken_Terminal> (1 row)
- <https://en.wikipedia.org/wiki/Hudson_Line_(Metro-North)> (1 row)
- <https://en.wikipedia.org/wiki/Jersey_City_Reservoir_No._3> (1 row)
- <https://en.wikipedia.org/wiki/Jones_Beach_State_Park> (1 row)
- <https://en.wikipedia.org/wiki/Kensico_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/Lake_DeForest> (1 row)
- <https://en.wikipedia.org/wiki/Lake_Sebago> (1 row)
- <https://en.wikipedia.org/wiki/Lake_Surprise_(Watchung_Reservation)> (1 row)
- <https://en.wikipedia.org/wiki/Lake_Tappan> (1 row)
- <https://en.wikipedia.org/wiki/Liberty_Harbor> (1 row)
- <https://en.wikipedia.org/wiki/Lincoln_Park_(Jersey_City)> (1 row)
- <https://en.wikipedia.org/wiki/Long_Beach,_New_York> (1 row)
- <https://en.wikipedia.org/wiki/Meadowlands_Sports_Complex> (1 row)
- <https://en.wikipedia.org/wiki/Monksville_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/Muscoot_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/New_Croton_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/Newark_Liberty_International_Airport> (1 row)
- <https://en.wikipedia.org/wiki/North_Tarrytown_Assembly> (1 row)
- <https://en.wikipedia.org/wiki/Overpeck_County_Park> (1 row)
- <https://en.wikipedia.org/wiki/Packanack_Lake,_New_Jersey> (1 row)
- <https://en.wikipedia.org/wiki/Paulus_Hook> (1 row)
- <https://en.wikipedia.org/wiki/Pavonia_Terminal> (1 row)
- <https://en.wikipedia.org/wiki/Piermont,_New_York> (1 row)
- <https://en.wikipedia.org/wiki/Playland_(New_York)> (1 row)
- <https://en.wikipedia.org/wiki/Pompton_Lake> (1 row)
- <https://en.wikipedia.org/wiki/Port_Jersey> (1 row)
- <https://en.wikipedia.org/wiki/Port_Libert%C3%A9,_Jersey_City> (1 row)
- <https://en.wikipedia.org/wiki/Port_Newark%E2%80%93Elizabeth_Marine_Terminal> (1 row)
- <https://en.wikipedia.org/wiki/Sandyfield,_New_York> (1 row)
- <https://en.wikipedia.org/wiki/Tarrytown_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/Teterboro_Airport> (1 row)
- <https://en.wikipedia.org/wiki/Titicus_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/Wanaque_Reservoir> (1 row)
- <https://en.wikipedia.org/wiki/Weequahic_Park> (1 row)
- <https://en.wikipedia.org/wiki/Woodcliff_Lake,_New_Jersey> (1 row)
- <https://jclandmarks.org/?p=1950> (1 row)
- <https://meri.njmeadowlands.gov/mesic/sites/existingpotential-remediation-sites/avon-landfill-2/> (1 row)
- <https://meri.njmeadowlands.gov/mesic/sites/existingpotential-remediation-sites/erie-landfill-2/> (1 row)
- <https://meri.njmeadowlands.gov/mesic/sites/existingpotential-remediation-sites/keegan-landfill-2/> (1 row)
- <https://meri.njmeadowlands.gov/mesic/sites/existingpotential-remediation-sites/kingsland-landfill-2/> (1 row)
- <https://meri.njmeadowlands.gov/mesic/sites/existingpotential-remediation-sites/malanka-landfill-2/> (1 row)
- <https://nj.gov/dep/parksandforests/parks/liberty_state_park/liberty_history.html> (1 row)
- <https://thefouroranges.com/orange-and-west-orange-nearly-merged-over-this-reservoir> (1 row)
- <https://water.newarknj.gov/completed-projects/valve-replacement-at-the-pequannock-screen-building-9b8h8> (1 row)
- <https://www.urbanhabitats.org/v02n01/3centuries_full.html> (1 row)

What they are, and the terms:

| Source | Used for | Licence / terms |
|---|---|---|
| English Wikipedia, fetched as wikitext with `wiki_fetch.py` into `data/raw/fill_counties/wiki/` (410 titles asked, 328 exist; the row's `source_url` names the article used) | most dates; the quoted sentences in the notes | text CC BY-SA 4.0; cite the article |
| New Jersey Meadowlands Commission / MERI, *Meadowlands Environmental Site Information Compilation*, site pages (fetched through the site's public JSON listing) | closing years of the Keegan, Malanka, Kingsland, Avon and Erie landfills | New Jersey state agency pages; cited, not redistributed |
| S. Marshall, "The Meadowlands Before the Commission: Three Centuries of Human Use and Alteration of the Newark and Hackensack Meadows", *Urban Habitats* 2 (1), 2004 | Port Newark 1914, the Newark Meadows "totally filled in" 1914–1974, the dike schemes | journal article, free to read online; cited, not redistributed |
| US EPA, corrective action page for the Military Ocean Terminal Bayonne (January 2025 snapshot) | the peninsula's fill from 1939 | US Government work |
| New Jersey DEP, Liberty State Park history page | Communipaw Cove filled 1860–1928 | **read only through a search-result summary**: the page answered 404 on 2026-11-10 |
| Jersey City Landmarks Conservancy, Warehouse Historic District page | "early 1870s" for the Harsimus Yards | **read only through a search-result summary** (the page's text did not come through the fetch) |
| Fund for a Better Waterfront, on the Hoboken Historical Museum's exhibition "The Hoboken Meadows" | Hoboken as an island, the meadows filled west to the Palisades | organisation's web page; cited |
| City of Newark, Department of Water and Sewer Utilities (project page); *The Four Oranges* (local news) | Charlotteburg Reservoir 1957; Orange Reservoir "in the 1880s" | municipal page; news article; cited |
| Overture Maps 2026-10-21.0 (`data/raw/fill_counties/overture/`, and the lead's `region_building.parquet` for named footprints) | all geometry | OpenStreetMap-derived layers ODbL; Overture's own CDLA Permissive 2.0 |

## Rules for the terrain stage

Rules 1, 3, 4, 5 and 7 of `fill_README.md` apply unchanged (coarse rings are brackets; land grows from the old shore outward across the span; among overlapping `fill` rings the earliest `year_end` wins; a reservoir wins inside its own outline). In addition:

1. **Nothing here may be painted as drawn except reservoirs.** Many rings are whole towns, parks or peninsulas and contain natural upland: Paulus Hook's island, the Harsimus upland and the foot of Bergen Hill, Castle Point and a quarter of Hoboken, Constable Hook, Caven Point's beach, the east half of Lincoln Park, Croton Point, the beach ridges of Long Beach, Atlantic Beach and Jones Beach, and every natural point west of the Hudson Line's tracks.
2. **Reservoirs: paint water only on cells that are water today inside the ring.** The rings are exterior outlines closed across causeways: islands, causeways and (Kensico: 14 % of the ring) necks of land are inside. Before `year_start` those cells are land, with these exceptions:
   - `pas_greenwood_lake`: a natural lake before the dam of 1837. Keep water before 1837.
   - `ess_weequahic_lake`: tidal marsh and creek before 1903, not dry land.
   - `wes_new_croton_reservoir`: Croton Lake (Old Croton Dam, 1842) filled the upper part of the valley from 1842 to 1906. Its outline is not on disk; the ring makes the whole valley land until 1906.
   - `wes_kensico_reservoir` (1917): a smaller reservoir stood behind the old dam from 1885. Not drawn.
   - `ber_oradell_reservoir` (1923): a dredged mill pond from 1901, a larger pond from 1911. `pas_pompton_lake` (1908): a mill pond behind a wooden dam until 1903. Not drawn.
   - `hud_jersey_city_reservoir_3` and `wes_hillview_reservoir` are walled basins on hilltops, not flooded valleys.
3. **Rings that lie across open water** (`ber_overpeck_park`, `ber_meadowlands_sports_complex`, `wes_playland`, `hud_droyers_point`) are hulls. Use them only on cells that are land today.
4. **Thin rings.** `wes_hudson_river_railroad` is 45 m wide where the track runs on a causeway, less than a cell of the region grid (76 m): date a cell if the ring touches it. `roc_piermont_pier` is a pier 60–100 m wide.
5. **Rings on a county or state line**: `ber_lake_tappan` (Bergen and Rockland), `pas_greenwood_lake` (Passaic and Orange County, New York: 45 % inside Passaic), `pas_charlotteburg_reservoir` (Passaic and Morris), `ess_newark_airport` and the port rings (cut at the Newark / Elizabeth line).
6. **No overlaps.** The build lists none over 0.25 ha among these rings and none with the city's `fill_zones.csv`.
7. **The Meadowlands at large have no ring.** Only dated pieces are in the file (landfills, the Sports Complex, the airports, Kearny Point). For the rest the stage's own fallback (made land four years before the buildings around it) is better than a county-wide bracket: Marshall gives only "from the 1920s through the 1960s, more than half the acreage of the Meadowlands lying north of Newark Bay was filled in".

## Weak spots

- **Jersey City's bands are anchored on few facts.** Paulus Hook (1804–1892) is a bracket between two stated events, not a dated fill. Harsimus Cove's inner band starts in an estimated year; "a quarter mile from Henderson Street" by 1870 is the one measured line. The Long Dock ring carries the years of the tunnel and terminal (1856–1861) although later piers are inside it. The meadow west of Henderson Street and South Cove have estimated brackets.
- **Communipaw (1860–1928)** rests on a state page that could not be opened, read through a search-result summary. **Black Tom's outline** is a 330 m band round a park road, not the island's shape.
- **Caven Point (1917–1945)** is an estimated bracket. The Army terminal of the First World War and the Lehigh Valley's Claremont Terminal were not verified in any source opened.
- **Constable Hook (1877–1930)**: the Hook is natural; the bracket is estimated; the ring ends at Avenue E and a line due south of its end. The Ocean Terminal ring takes a small lobe of the Hook's north shore, south of the inlet.
- **Kearny Point (1916–1932)**: only the shipyard of 1917 is dated. The ring is all of South Kearny.
- **Landfill starts are estimated** (1945, 1950, 1957, 1960); the closing years are the agency's. The Kingsland outline (136 ha) is larger than the agency's 150 acres and takes in part of the 1-E landfill.
- **Teterboro (1917–1949), Newark Airport (1928–1974), Port Newark (1914–1930), Port Elizabeth (1958–1974)**: one bracket each for land made in several stages.
- **Hoboken (1820–1910) and Long Beach (1907–1913)** are whole-city rings with one bracket. For Long Beach the article says the channel was dredged, not where the sand went.
- **Westchester's Hudson shore** has one ring with the railroad's years. The later fill west of the tracks at Yonkers, Hastings, Dobbs Ferry, Irvington, Tarrytown and Ossining is not dated; the General Motors site has an estimated bracket.
- **Estimated reservoir years**: Woodcliff Lake (1905: the source only says before March 1910), Hempstead Lake (1873: the source only says proposed in 1870), Orange Reservoir (1885: "in the 1880s").
- **Sports Complex and Playland outlines** are hulls round footprints.

## Noted, not in the file

- **Dikes** (`kind` has no value for them). Hackensack Meadows: the Swartwouts' earthen dikes and tide gates between the lower Hackensack and Passaic, then Driggs and Pike's iron-cored dikes with pumps (1867), both for farmland lying below high tide (Marshall 2004). Saw Mill Creek marsh, Kearny / Lyndhurst: dikes and tide gates "built in the 1800's", tide gates of the 1920s, breached by a storm in 1950 (MERI). Overpeck Creek: tide gates in the 1950s.
- **Dundee Lake and Canal** (Passaic / Bergen): the dam was raised under an act of 1857, which "flooded adjacent areas and created Dundee Lake"; the canal "was built between 1858 and 1861". No outline of the lake apart from the river on disk.
- **Paterson raceways**: narrower than a cell; no date taken from a source opened.
- **Snake Hill** (Secaucus): "largely obliterated in the 1960s by quarrying" (height by a quarter, base by four fifths). Land stays land; no `kind` fits.
- **Port Washington sand pits** (Nassau): sand mining on the west shore of Hempstead Harbor "from 1865 until 1989". The pits are land today, so `excavation` (land becomes water) does not fit.
- **Port Liberté's canals** (1980s) are cut into the Caven Point fill; not separated.

## Not covered (no date, or no outline on disk)

- Hudson: Harmon Cove and the rest of Secaucus's filled meadow (no date found); the 1-D, 1-A, 15W and 1-E landfills (outlines on disk, no dates on the agency's pages); the Turnpike embankments (1951, western spur 1970: narrower than a cell); Bayonne's Newark Bay shore, Bergen Point and the Kill van Kull shore; the Hackensack shore between Lincoln Park and Droyers Point; the Croxton and North Bergen yards; Hackensack Reservoir No. 2 in Weehawken.
- Bergen: the Rutherford and Lyndhurst landfills ("closed early 1970s", no outline) and the BCUA landfill (outline, no date); Little Ferry and Moonachie; Mehrhof Pond (a clay pit).
- Essex / Union: the Doremus Avenue meadow north of the port and the Turnpike's ground; the Passaic River's banks; Elizabethport and the Arthur Kill shore; Bayway; Linden Airport; Cedar Grove and Canoe Brook reservoirs (no date found).
- Passaic: Point View Reservoir (the 1964 of the brief was not confirmed), Oak Ridge, Clinton and Echo Lake reservoirs (the Pequannock system "by 1892": no year per reservoir), the lake communities (Pines Lake, Upper Greenwood Lake, Erskine).
- Nassau: Lido Beach and Point Lookout; the canal estates of the south shore (Freeport, Merrick, Massapequa); the Oceanside and Merrick landfills (outlines on disk, no dates); Bar Beach; Glen Cove; the water works' ponds other than Hempstead Lake; the parkway causeways (1929, 1934).
- Westchester: the Yonkers, Hastings, Tarrytown and Ossining waterfronts apart from the railroad ring; Croton-Harmon yard; Davenport Neck, Mamaroneck harbor and Rye's shore apart from Playland; Byram Lake; the Bronx River Parkway lakes (1925) and Tibbetts Brook Park's lake.
- Rockland: Haverstraw's brick-yard shore and clay pits (the articles opened give no date), Nyack, Stony Point; Piermont Marsh is natural. Harriman lakes in Orange County are outside the eight counties.

## Checks (`build_zones.py`, `check_zones.py`, `qa_plot.py`)

- Every ring read back from the CSV is a valid polygon with its centre inside the wider box; ids are unique; the prefix matches the county; kinds and precisions are from the lists; every row has a source URL.
- No overlap over 0.25 ha among the rings or with the city's rings.
- Named footprints fall where they should: the Central Railroad terminal and Liberty Science Center in `hud_communipaw_cnj`, Hoboken Terminal in its ring, 30 Hudson Street in `hud_paulus_hook`, Harborside in `hud_harsimus_cove_outer`, Hoboken City Hall in the Hoboken ring, the Meadowlands Arena in the Sports Complex ring, a Newark terminal in the airport ring, Long Beach City Hall, a Playland building, The Shops at Lincoln Harbor. Nine other names tried are not in the footprint file.
- Reservoir rings are 92–100 % water today (Kensico 86 %); fill rings are 0–6 % water, except the hulls (Overpeck 21 %, Playland 36 %).
- Areas against the sources: the Ocean Terminal ring is 229 ha (EPA: a 652-acre = 264 ha peninsula); Croton Point Park 170 ha; Hempstead Lake 54 ha against 167 acres = 68 ha before the parkway dam of 1947.
- Plots of the zones over land, streets and railways were looked at for Jersey City and Hoboken, Bayonne, the whole of Hudson County, the Meadowlands, Newark's port and airport, the Hudson shore from Tarrytown to Croton, and Nassau's barrier beaches. They are scratch files in `data/interim/fill_counties/`.
- Not looked at on a plot: the reservoirs (checked by the water share only), Glen Island, Playland, Piermont at full size, Droyers Point.

## Rebuilding

```
P=../../../.venv/bin/python; cd data/manual/fill_counties_tools
$P download_overture.py                       # Overture extracts of the wider box (cached)
$P wiki_fetch.py wiki_titles.txt              # cached downloads
for m in zones_hud_a zones_hud_b zones_nj zones_ny; do $P $m.py; done     # zones_hud_a before zones_hud_b
$P build_zones.py && $P check_zones.py && $P make_readme.py
```

Each script saves `data/interim/fill_counties/rows_<area>.json`; street indexes and the land of the Hudson window are cached there as pickles.

## Every zone

"dates": `documented` = both years stated by a source; `one end estimated`; `estimated bracket` = no dated source for the fill itself, the note says so.

| zone_id | county | years | kind | ring | dates | ha |
|---|---|---|---|---|---|---|
| `hud_hoboken_terminal` | Hudson | 1860–1907 | fill | coarse | one end estimated | 31.3 |
| `hud_paulus_hook` | Hudson | 1804–1892 | fill | coarse | estimated bracket | 63.6 |
| `hud_harsimus_cove_inner` | Hudson | 1850–1870 | fill | coarse | one end estimated | 27.4 |
| `hud_harsimus_cove_outer` | Hudson | 1870–1875 | fill | coarse | one end estimated | 22.5 |
| `hud_pavonia_long_dock` | Hudson | 1856–1861 | fill | coarse | documented | 73.1 |
| `hud_harsimus_meadows` | Hudson | 1835–1880 | fill | coarse | estimated bracket | 234.8 |
| `hud_south_cove` | Hudson | 1836–1900 | fill | coarse | estimated bracket | 53.4 |
| `hud_hoboken_meadows` | Hudson | 1820–1910 | fill | coarse | one end estimated | 307.1 |
| `hud_communipaw_cnj` | Hudson | 1860–1928 | fill | coarse | documented | 242.7 |
| `hud_black_tom` | Hudson | 1876–1916 | fill | coarse | documented | 66.7 |
| `hud_port_jersey` | Hudson | 1972–1976 | fill | coarse | documented | 161.5 |
| `hud_military_ocean_terminal` | Hudson | 1939–1942 | fill | coarse | documented | 229.4 |
| `hud_caven_point` | Hudson | 1917–1945 | fill | coarse | estimated bracket | 94.5 |
| `hud_greenville_yard` | Hudson | 1900–1904 | fill | coarse | one end estimated | 191.9 |
| `hud_constable_hook` | Hudson | 1877–1930 | fill | coarse | estimated bracket | 372.9 |
| `hud_lincoln_park_west` | Hudson | 1904–1925 | fill | coarse | documented | 106.8 |
| `hud_droyers_point` | Hudson | 1925–1937 | fill | coarse | one end estimated | 60.4 |
| `hud_kearny_point` | Hudson | 1916–1932 | fill | coarse | estimated bracket | 385.1 |
| `hud_keegan_landfill` | Hudson | 1945–1972 | fill | coarse | one end estimated | 51.4 |
| `hud_malanka_landfill` | Hudson | 1960–1983 | fill | coarse | one end estimated | 42.5 |
| `hud_jersey_city_reservoir_3` | Hudson | 1874–9999 | reservoir | precise | documented | 3.2 |
| `hud_weehawken_waterfront` | Hudson | 1881–1884 | fill | coarse | documented | 50.5 |
| `hud_north_hudson_shore` | Hudson | 1884–1920 | fill | coarse | estimated bracket | 58.3 |
| `ber_edgewater_shore` | Bergen | 1900–1930 | fill | coarse | estimated bracket | 133.8 |
| `ber_meadowlands_sports_complex` | Bergen | 1972.88–1976.77 | fill | coarse | documented | 191.1 |
| `ber_teterboro_airport` | Bergen | 1917–1949 | fill | coarse | one end estimated | 274.0 |
| `ber_overpeck_park` | Bergen | 1954–2010 | fill | coarse | documented | 304.7 |
| `ber_kingsland_landfill` | Bergen | 1957–1988 | fill | coarse | one end estimated | 136.9 |
| `ber_avon_landfill` | Bergen | 1957–1980 | fill | coarse | one end estimated | 40.8 |
| `ber_erie_landfill` | Bergen | 1950–1969 | fill | coarse | one end estimated | 14.3 |
| `ber_oradell_reservoir` | Bergen | 1923–9999 | reservoir | precise | documented | 238.8 |
| `ber_oradell_reservoir_b` | Bergen | 1923–9999 | reservoir | precise | documented | 42.3 |
| `ber_lake_tappan` | Bergen | 1967–9999 | reservoir | precise | documented | 301.6 |
| `ber_woodcliff_lake` | Bergen | 1905–9999 | reservoir | precise | one end estimated | 68.9 |
| `ess_port_newark` | Essex | 1914–1930 | fill | coarse | one end estimated | 405.7 |
| `ess_newark_airport` | Essex | 1928–1974 | fill | coarse | documented | 801.5 |
| `ess_weequahic_lake` | Essex | 1903–9999 | reservoir | precise | documented | 30.5 |
| `ess_branch_brook_lake` | Essex | 1898–9999 | reservoir | precise | documented | 9.4 |
| `ess_orange_reservoir` | Essex | 1885–9999 | reservoir | precise | one end estimated | 25.2 |
| `uni_port_elizabeth` | Union | 1958–1974 | fill | coarse | documented | 462.0 |
| `uni_lake_surprise` | Union | 1845–9999 | reservoir | precise | documented | 11.2 |
| `pas_wanaque_reservoir` | Passaic | 1928–9999 | reservoir | precise | documented | 908.4 |
| `pas_monksville_reservoir` | Passaic | 1987.6–9999 | reservoir | precise | documented | 209.0 |
| `pas_pompton_lake` | Passaic | 1908–9999 | reservoir | precise | documented | 77.4 |
| `pas_greenwood_lake` | Passaic | 1837–9999 | reservoir | precise | documented | 775.0 |
| `pas_packanack_lake` | Passaic | 1928–9999 | reservoir | precise | documented | 33.3 |
| `pas_charlotteburg_reservoir` | Passaic | 1957–9999 | reservoir | precise | documented | 131.4 |
| `wes_croton_point_landfill` | Westchester | 1927–1986 | fill | coarse | documented | 169.7 |
| `wes_sleepy_hollow_gm` | Westchester | 1900–1960 | fill | coarse | estimated bracket | 30.8 |
| `wes_hudson_river_railroad` | Westchester | 1847–1849.75 | fill | coarse | documented | 263.3 |
| `wes_playland` | Westchester | 1927.7–1928.4 | fill | coarse | documented | 101.2 |
| `wes_glen_island` | Westchester | 1879–1925 | fill | coarse | one end estimated | 29.5 |
| `wes_new_croton_reservoir` | Westchester | 1906–9999 | reservoir | precise | documented | 872.9 |
| `wes_kensico_reservoir` | Westchester | 1917–9999 | reservoir | precise | documented | 1000.7 |
| `wes_titicus_reservoir` | Westchester | 1893–9999 | reservoir | precise | documented | 276.6 |
| `wes_muscoot_reservoir` | Westchester | 1905–9999 | reservoir | precise | documented | 446.9 |
| `wes_amawalk_reservoir` | Westchester | 1897–9999 | reservoir | precise | documented | 231.7 |
| `wes_cross_river_reservoir` | Westchester | 1908–9999 | reservoir | precise | documented | 377.2 |
| `wes_grassy_sprain_reservoir` | Westchester | 1876–9999 | reservoir | precise | documented | 67.8 |
| `wes_hillview_reservoir` | Westchester | 1915–9999 | reservoir | precise | documented | 35.0 |
| `wes_tarrytown_reservoir` | Westchester | 1897–9999 | reservoir | precise | documented | 35.4 |
| `nas_long_beach` | Nassau | 1907–1913 | fill | coarse | one end estimated | 588.4 |
| `nas_atlantic_beach` | Nassau | 1923–1927 | fill | coarse | documented | 130.2 |
| `nas_island_park` | Nassau | 1909–1925 | fill | coarse | one end estimated | 99.7 |
| `nas_jones_beach` | Nassau | 1926–1929.59 | fill | coarse | one end estimated | 1102.2 |
| `nas_hempstead_lake` | Nassau | 1873–9999 | reservoir | precise | one end estimated | 53.6 |
| `roc_lake_deforest` | Rockland | 1956–9999 | reservoir | precise | documented | 408.2 |
| `roc_lake_sebago` | Rockland | 1925–9999 | reservoir | precise | documented | 120.7 |
| `roc_lake_welch` | Rockland | 1942–9999 | reservoir | precise | documented | 88.3 |
| `roc_piermont_pier` | Rockland | 1838–1839 | fill | coarse | one end estimated | 43.8 |

