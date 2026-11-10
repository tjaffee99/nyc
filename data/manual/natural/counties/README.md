# The natural landscape c.1609 of the counties around the city

Hudson, Bergen, Essex, Union, Passaic (New Jersey), Westchester, Rockland (New York). Made 2026-11-10.
Same format and, as far as it carried over, the same method as the city's layer (`../README.md`). Nassau is not
on the map and was left out (its soil survey and sheets were downloaded and classified, not assembled).

## Files

| file | what |
|---|---|
| `natural_1609_counties.geojson` | polygons (WGS84). `cover`: water, tidal_marsh, tidal_flat, beach, dunes, pond, freshwater_wetland (as the city's file; only water, tidal_marsh and freshwater_wetland occur) and **dry_valley** (dry ground in 1609, under a reservoir today). `source`, `confidence` (high / medium / low), `note`, `county` |
| `natural_stats_counties.json` | hectares per county, cover and rule; reservoirs; how far each sheet lines its water |
| `usgs_sheets_counties.json` | per classified sheet: shift applied, agreement, discriminant accuracy |
| `tools/` | scripts (see "Reproducing") |

No polygon = dry upland. Nothing over today's water except `dry_valley`. "Land today" = the soil survey's land.
Cells of the five boroughs' survey areas, and cells under a polygon of the city's file (Ellis Island's New Jersey
side), are left out; the grid is the city's 6 m grid extended, so a cell belongs to one file or the other.

## Sources

| `source` | what | URL | licence |
|---|---|---|---|
| `ssurgo` | USDA NRCS soil survey (SSURGO): NJ003 Bergen, NJ013 Essex, NJ017 Hudson (saved 2026-08-24), NJ031 Passaic, NJ039 Union (2026-08-25), NY087 Rockland, NY119 Westchester (2026-09-01); hydric rating per map unit from Soil Data Access | `https://websoilsurvey.sc.egov.usda.gov/DSD/Download/Cache/SSA/wss_SSA_NJ017_[2026-08-24].zip` and the others; https://sdmdataaccess.sc.egov.usda.gov/ | public domain |
| `usgs_staten_island_1898` | USGS 1:62,500 Staten Island sheet, 1898 print | https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/NY/NJ_Staten%20Island_255388_1898_62500_geo.tif | public domain |
| `usgs_paterson_1888` | Paterson sheet, 1888 print | …/GeoTIFF/NJ/NJ_Paterson_255310_1888_62500_geo.tif | same |
| `usgs_harlem_1891` | Harlem sheet, 1891 print | …/GeoTIFF/NY/NJ_Harlem_472515_1891_62500_geo.tif | same |
| `usgs_oyster_bay_1897`, `usgs_tarrytown_1892` | Oyster Bay 1897 (`NY_Oyster%20Bay_136363`), Tarrytown 1892 (`NY_Tarrytown_144340`): classified, but they do not show usable water (see "Weak spots"); the polygons left with these ids lie on wet-substratum fill, and only their marsh / water label comes from the sheet | same bucket | same |
| `estimated_lowland` | not a map: urban land / unnamed fill below 4.5 m (USGS 3DEP 1/3 arc-second elevation) in a tidal setting | https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/ | public domain |
| `fill_zones_counties` | reservoir outlines, names and years from the project's `data/manual/fill_zones_counties.csv` (its `source_url` is quoted in each note); the polygon is the soil survey's Water inside that outline | project file | as that file |

Print years only: the survey years in the sheet margins were not read. Downloaded but **not classified** (the run was
killed for memory on the shared machine, then the budget ran out): Stamford 1892, West Point 1892, Carmel 1892,
Ramapo 1891, Greenwood Lake 1891, Morristown 1888, Plainfield 1888 (`tools/download.py` lists the files).

## Method, where it differs from the city's

Soil classes are read from the map unit **names** (`tools/ssurgo_load.py`), because these surveys do not have the
city's "reclaimed" / "tidal marsh substratum" units:

| soil survey unit | written as |
|---|---|
| *wet substratum* fill (Urban land, wet substratum in Hudson; Udorthents, wet substratum elsewhere) | what the sheet shows (marsh / water); where the sheet shows land already or is not usable: `water` within 150 m of open tidewater, `tidal_marsh` farther in, `freshwater_wetland` where not connected to tidewater — **estimated**, low |
| *Udorthents, organic substratum* (fill over marsh peat; Bergen, Union) | `tidal_marsh`, medium |
| Westbrook / Ipswich / Sandyhook tidal-marsh soils | `tidal_marsh`, high — still marsh today |
| natural units ≥ 85 % hydric (Catden, Timakwa, Natchaug mucks, Preakness, Parsippany, Great Piece, Hasbrouck, Alden, Sun, Sloan, Norwich, Passaic, Ridgebury of the NJ Highlands …) | `freshwater_wetland`, medium |
| fill and urban land that does not say what it covers (Urban land undifferentiated, Udorthents refuse / loamy / smoothed, Bigapple, Laguardia, Ladyliberty, Secaucus, Greenbelt …) | what the sheet shows, in the tidal zone only; else dry |
| everything else | dry |

Sheets (`tools/sheets.py`), changed after looking at the results:
- **Blue ink by chromaticity, away from black line work.** With the city's `B − R` on every pixel, the yellow New
  Jersey sheets read dense street grids as water (all of Jersey City on the Staten Island sheet).
- **Registration by area agreement** with the soil survey's wet set near natural upland, not by shoreline edges.
  The edge method gave shifts 70–90 m off where checked by eye (Hart Island on the Harlem sheet, the Hackensack at
  Little Ferry on the Paterson sheet); the shifts used here are under 35 m. **The city layer's Harlem shift
  (58 m W / 74 m S) is visibly wrong at Hart Island.**
- **Marsh against water is not reliable** (discriminant accuracy 0.59 / 0.71 on the Paterson sheet, 0.78 / 0.85 on
  Staten Island, 0.86 / 0.87 on Harlem): the edges of the meadows read as water. So sheet water on today's land is
  believed only within 150 m of today's tidal water or of blank-paper open water; farther in it is written as marsh.
- **Blank paper** (open water is not lined far from shore) is assigned by two fronts, from natural upland soils and
  from today's open tidewater; only on sheets that line their water (Staten Island, Paterson, Harlem).
- Wooded (cedar) swamp is drawn as blue tufts on blank paper; urban land with such marks beside tidal marsh is
  written as marsh (estimated).
- Inland, nothing is taken from the sheets (no ponds; stream lines gave false patches).

`tools/assemble.py` has the rules in order, in its docstring.

## Accuracy I believe was reached (position of the 1609 shore / marsh edge)

| county | basis | estimate |
|---|---|---|
| Hudson | soil survey's wet-substratum boundary + Staten Island 1898 / Paterson 1888 sheets | upland edge ± 40 m. Inside it, **marsh against water is a guess** wherever the ground was filled before 1888–98 (the Jersey City, Hoboken and Bayonne waterfronts): 150 m rule, low |
| Bergen | same; Meadowlands on the Paterson sheet and the organic-substratum units | upland edge ± 40–60 m; cedar swamp and salt marsh are not separated |
| Essex, Union | Newark and Elizabeth meadows on the Staten Island sheet; Union's organic-substratum units | ± 40–60 m; the old bay edge at Port Newark / Port Elizabeth may sit up to 350 m too far out as marsh |
| Westchester | Sound shore and Hudson to Hastings: Harlem sheet + soil survey, ± 40–60 m. East of 73°45′ W and north of 41° N: **soil survey only** (wet-substratum fill ± 40 m; fill mapped as plain Urban land is missed) |
| Rockland | soil survey only | as Westchester north of 41° N |
| Passaic | soil survey only; inland | wetland outlines ± 30 m (1:12,000–1:24,000 mapping) |

## Statistics (from `natural_stats_counties.json`; hectares)

| county | land today | `water` | `tidal_marsh` | `freshwater_wetland` | `dry_valley` | was water, land today | was tidal marsh, developed today | tidal marsh that is still marsh | land without a usable sheet |
|---|---|---|---|---|---|---|---|---|---|
| Hudson | 11508 | 2552 | 3110 | 35 | 3 | 2552 | 2330 | 780 | 0 |
| Bergen | 60199 | 758 | 4150 | 6162 | 609 | 758 | 3017 | 1133 | 21309 |
| Essex | 32632 | 428 | 1528 | 2400 | 25 | 428 | 1528 | 0 | 16338 |
| Union | 26672 | 571 | 1771 | 759 | 11 | 571 | 1565 | 206 | 20237 |
| Westchester | 111338 | 284 | 455 | 5467 | 3196 | 284 | 362 | 93 | 63150 |
| Rockland | 44821 | 85 | 366 | 2968 | 642 | 85 | 80 | 285 | 30706 |
| Passaic | 47481 | 5 | 2 | 4947 | 1259 | 5 | 2 | 0 | 33699 |
| all seven | 334650 | 4683 | 11382 | 22737 | 5745 | 4683 | 8885 | 2497 | 185439 |

"Land without a usable sheet" counts only ground outside every classified sheet; the Tarrytown and Oyster Bay sheets cover more ground but add nothing.

`natural_1609_counties.geojson`: 6285 polygons, 11.0 MB; by source: ssurgo 3858, usgs_paterson_1888 993, usgs_staten_island_1898 602, estimated_lowland 374, usgs_harlem_1891 302, usgs_tarrytown_1892 85, fill_zones_counties 41, usgs_oyster_bay_1897 30; by confidence: medium 3848, low 2306, high 131. The table above is counted on the rasters; 37 polygons (26 ha: Westchester 21 ha of water and marsh, Rockland 5 ha) that rested only on the Tarrytown or Oyster Bay sheet, on soil that does not say wet, were dropped from the file afterwards (`assemble.py merge`).

Reservoirs written as `dry_valley` (hectares = soil survey Water inside the fill-zone outline; "wet on sheet" = share of it the classified sheet shows as water or marsh, where one exists):

| reservoir | county | water from | ha | wet on sheet |
|---|---|---|---|---|
| Jersey City Reservoir No. 3 | Hudson | 1874 | 3 | 48% (staten_island_1898) |
| Oradell Reservoir | Bergen | 1923 | 239 | 38% (harlem_1891, paterson_1888) |
| Oradell Reservoir (part 2) | Bergen | 1923 | 42 | 63% (harlem_1891) |
| Lake Tappan (Bergen and Rockland counties) | Bergen | 1967 | 262 | – |
| Woodcliff Lake reservoir | Bergen | 1905 | 65 | – |
| Orange Reservoir (South Mountain Reservation) | Essex | 1885 | 25 | – |
| Lake Surprise (Watchung Reservation) | Union | 1845 | 11 | – |
| New Croton Reservoir | Westchester | 1906 | 853 | – |
| Titicus Reservoir | Westchester | 1893 | 274 | – |
| Muscoot Reservoir | Westchester | 1905 | 455 | – |
| Amawalk Reservoir | Westchester | 1897 | 235 | – |
| Cross River Reservoir | Westchester | 1908 | 368 | – |
| Kensico Reservoir / Rye Lake | Westchester | 1917 | 874 | – |
| Tarrytown Reservoir | Westchester | 1897 | 36 | – |
| Grassy Sprain Reservoir | Westchester | 1876 | 69 | 56% (harlem_1891) |
| Hillview Reservoir | Westchester | 1915 | 35 | 0% (harlem_1891) |
| Lake DeForest | Rockland | 1956 | 405 | – |
| Lake Sebago (Harriman State Park) | Rockland | 1925 | 118 | – |
| Lake Welch (Harriman State Park) | Rockland | 1942 | 82 | – |
| Lake Tappan (Bergen and Rockland counties) | Rockland | 1967 | 37 | – |
| Wanaque Reservoir | Passaic | 1928 | 886 | – |
| Monksville Reservoir | Passaic | 1987 | 208 | – |
| Pompton Lake | Passaic | 1908 | 74 | – |
| Charlotteburg Reservoir (Passaic and Morris counties) | Passaic | 1957 | 60 | – |
| Packanack Lake (Wayne) | Passaic | 1928 | 32 | – |

**Hackensack Meadowlands** (Hudson and Bergen polygons west of the Palisades ridge, 40.725–40.885° N, east of 74.16° W; today's open water not counted): 6065 ha tidal marsh (1879 ha of it still marsh) + 1771 ha water + 399 ha freshwater wetland = 8234 ha that was not dry land. The brief gives about 8,000 ha of marsh and cedar swamp for 1609, half of it filled; here 6356 ha are developed today, but marsh that has since become open water is missing from both numbers. No published figure was re-read (Wikipedia answered HTTP 429). The box also holds the Passaic River front of Kearny and Harrison and the head of Newark Bay, which is where most of the `water` is.

## Checks made (`tools/qa.py`, as run on the delivered file)

Point tests (expectation, what the file says, the soil unit at the point). A point marked "TODAY'S WATER" under a reservoir is where it should be; elsewhere it means my coordinate missed the land.

```
ok  Port Newark (container terminal)           expect wet        got tidal_marsh        usgs_staten_island_1898    low     soil: Urban land, Bigapple substratum, 0
ok  Newark Airport (terminals)                 expect wet        got tidal_marsh        usgs_staten_island_1898    low     soil: Urban land, Bigapple substratum, 0
ok  Port Elizabeth                             expect wet        got water              usgs_staten_island_1898    medium  soil: Urban land
ok  Liberty State Park                         expect wet        got water              usgs_staten_island_1898    low     soil: Ladyliberty fine sandy loam, 0 to 
ok  Liberty Science Center (Communipaw)        expect wet        got tidal_marsh        ssurgo                     low     soil: Urban land, wet substratum, 0 to 8
ok  Liberty State Park south (Black Tom side)  expect wet        got water              usgs_staten_island_1898    low     soil: Ladyliberty fine sandy loam, 0 to 
ok  Harsimus Cove (Newport)                    expect wet        got tidal_marsh        ssurgo                     low     soil: Urban land, wet substratum, 0 to 8
ok  Hoboken west side                          expect wet        got tidal_marsh        ssurgo                     low     soil: Urban land, wet substratum, 0 to 8
ok  Kearny Point                               expect wet        got tidal_marsh        usgs_staten_island_1898    medium  soil: Urban land, wet substratum, 0 to 8
NO  Meadowlands sports complex (stadium)       expect wet        got dry (no polygon)                                      soil: Urban land
ok  Teterboro Airport                          expect wet        got tidal_marsh        usgs_paterson_1888         medium  soil: Udorthents, wet substratum, 0 to 8
ok  Secaucus Junction (meadows)                expect wet        got tidal_marsh        usgs_paterson_1888         medium  soil: Urban land, wet substratum, 0 to 8
ok  Harmon Meadow, Secaucus                    expect wet        got tidal_marsh        usgs_paterson_1888         medium  soil: Urban land, wet substratum, 0 to 8
NO  Playland, Rye                              expect wet        got dry (no polygon)                                      soil: Urban land
NO  Piermont pier A                            expect wet        got dry (no polygon)                                      soil: TODAY'S WATER - bad test point
ok  Piermont pier B                            expect wet        got water              estimated_lowland          low     soil: Udorthents, smoothed
ok  Piermont marsh A                           expect wet        got tidal_marsh        ssurgo                     high    soil: Ipswich mucky peat, 0 to 2 percent
NO  Piermont marsh B                           expect wet        got dry (no polygon)                                      soil: Holyoke-Rock outcrop complex, roll
NO  Croton Point landfill A                    expect wet        got dry (no polygon)                                      soil: Fredon silt loam
ok  Croton Point landfill B                    expect wet        got tidal_marsh        ssurgo                     low     soil: Udorthents, wet substratum
ok  Croton-Harmon yard                         expect wet        got tidal_marsh        estimated_lowland          low     soil: Udorthents, smoothed
NO  Sleepy Hollow, General Motors site         expect wet        got dry (no polygon)                                      soil: Urban land
ok  Tarrytown waterfront (Pierson Park)        expect wet        got water              ssurgo                     low     soil: Udorthents, wet substratum
ok  Mamaroneck, Harbor Island Park             expect wet        got water              ssurgo                     low     soil: Udorthents, wet substratum
ok  Journal Square                             expect dry        got dry (no polygon)                                      soil: Urban land, till substratum, 0 to 
ok  Paulus Hook (Grand & Washington)           expect dry        got dry (no polygon)                                      soil: Urban land, till substratum, 0 to 
ok  Hoboken, Castle Point                      expect dry        got dry (no polygon)                                      soil: Greenbelt-Todthill-Urban land comp
ok  Snake Hill (Laurel Hill), Secaucus         expect dry        got dry (no polygon)                                      soil: Centralpark extremely gravelly san
ok  Newark, Broad & Market                     expect dry        got dry (no polygon)                                      soil: Urban land, Dunellen substratum, 0
ok  Elizabeth, Broad St                        expect dry        got dry (no polygon)                                      soil: Urban land
ok  Hackensack, Main St                        expect dry        got dry (no polygon)                                      soil: Urban land
ok  Fort Lee                                   expect dry        got dry (no polygon)                                      soil: Boonton-Urban land complex, 8 to 1
ok  Paterson, Great Falls overlook             expect dry        got dry (no polygon)                                      soil: Holyoke-Rock outcrop complex, 3 to
ok  White Plains, Main St                      expect dry        got dry (no polygon)                                      soil: Urban land
ok  Yonkers, Getty Square                      expect dry        got dry (no polygon)                                      soil: Urban land
ok  Nyack, Main & Broadway                     expect dry        got dry (no polygon)                                      soil: Wethersfield-Urban land complex, 2
ok  Haverstraw, Main St                        expect dry        got dry (no polygon)                                      soil: Hinckley-Urban land complex, 0 to 
ok  Tarrytown, Broadway & Main                 expect dry        got dry (no polygon)                                      soil: Urban land-Charlton complex, 3 to 
ok  Kensico Reservoir                          expect dry_valley got dry_valley         fill_zones_counties        medium  soil: TODAY'S WATER - bad test point
ok  Wanaque Reservoir                          expect dry_valley got dry_valley         fill_zones_counties        medium  soil: TODAY'S WATER - bad test point
ok  Oradell Reservoir                          expect dry_valley got dry_valley         fill_zones_counties        medium  soil: TODAY'S WATER - bad test point
ok  New Croton Reservoir                       expect dry_valley got dry_valley         fill_zones_counties        medium  soil: TODAY'S WATER - bad test point
ok  Lake DeForest                              expect dry_valley got dry_valley         fill_zones_counties        medium  soil: TODAY'S WATER - bad test point
points not as expected: 6 of 43 (counties in the file: ['Bergen', 'Essex', 'Hudson', 'Passaic', 'Rockland', 'Union', 'Westchester'] )
overlap with the city layer's polygons: m2 34 pieces 2 largest m2 17
polygon pairs that overlap: 4354 total m2 476157 largest m2 1739 ; pairs over 2000 m2: 0
invalid geometries: 0 ; polygons 6322 ; hectares by cover: {'dry_valley': 5744.0, 'freshwater_wetland': 22728.0, 'tidal_marsh': 11347.0, 'water': 4657.0}
```

Not as expected: the Meadowlands stadium, Playland and the Sleepy Hollow General Motors site are plain "Urban land" in the soil survey and blank on (or without) a usable sheet, so they stay dry; "Piermont pier A", "Piermont marsh B" and "Croton Point landfill A" are bad coordinates (water, rock, a natural soil).
Overlap with the city's polygons and between polygons: last lines of the block. Cells in both a county's and a borough's soil survey area: 0 in every county.

## Weak spots and what was not done

- **The Hudson shore north of Hastings and the Sound shore east of Mamaroneck have no usable sheet.** The Tarrytown
  1892 scan carries no blue (ink range 0.007); the Oyster Bay 1897 sheet lines too little of its water (13 %); West
  Point and Stamford were not classified. There, railroad causeways, the Sleepy Hollow General Motors site, Tarrytown's
  and Ossining's waterfront fill, Haverstraw's clay pits and Playland are in the file only where the soil survey maps
  wet-substratum fill or the lowland rule fires. The General Motors site and Playland came out dry.
- **Pre-railroad coves** (the Hudson River Railroad of 1849 cut them off) are older than every sheet; nothing
  reconstructs them.
- **Jersey City / Hoboken / Bayonne waterfront**: all filled before the sheets; the soil survey gives the outline of
  the made land, the split into water (within 150 m of today's open water) and marsh is an estimate. Communipaw
  Cove and Harsimus Cove were open shoal water in part and are mostly written as marsh.
- **Reservoirs**: `dry_valley` covers the reservoirs listed in `fill_zones_counties.csv` except Greenwood Lake (a
  natural lake raised by a dam), Weequahic Lake and Branch Brook lake (dug in marsh, from memory — not verified).
  The Oradell valley was not dry: the 1888 / 1891 sheets show 38–63 % of it wet (river meadows). Natural ponds inside
  Kensico (Rye Ponds) and the 1842 Croton Lake are not separated. No stream is drawn in the valleys.
- **Today's water that was marsh** (the flooded and dredged parts of the Meadowlands, the Port Newark and Elizabeth
  channels, Weequahic Lake) carries no polygon, as in the city's file: it shows as water in 1609.
- **Freshwater wetlands** are the soil survey's hydric units and (low, estimated) every wet-substratum fill not
  connected to tidewater; drained wetlands on soils the survey calls upland are missing.
- Polygons of different rules overlap by slivers up to about 5 m (each is simplified to 5 m on its own).
- Passaic, Westchester and Rockland were assembled before the wooded-swamp rule was added; it can only fire on the
  Paterson and Staten Island sheets beside tidal marsh, so at most a few hectares in Passaic would change.
- Wikipedia answered HTTP 429 to this client: no fact was checked against it. Reservoir years are the fill-zone
  file's, not mine.
- Not checked: any county at street scale; the survey years of the sheets; the join along the Bronx line by eye
  (numerically: see the checks).

## For the terrain stage

- Not-land in 1609 = `water`, `tidal_marsh` (as in the city's file). `freshwater_wetland` and `dry_valley` are land.
- `dry_valley` lies over today's water: the cells are land (forest fallback) until the reservoir's year.
- A `tidal_marsh` polygon with `confidence` = high is marsh that still exists; every other `water` / `tidal_marsh`
  polygon is land today and needs a fill year.
- Rasterise in any order; where two polygons overlap by a sliver, prefer `tidal_marsh` over `water`.

## Reproducing

```
cd data/manual/natural/counties/tools        # project venv; one process at a time, each under 1.6 GB
python download.py        # SSURGO zips, 16 GeoTIFFs -> data/raw/natural_counties/
python ssurgo_load.py     # -> data/interim/natural_counties/ssurgo_counties.parquet (needs the city's SSURGO zips too)
python dem.py             # 30 m elevation from 3DEP -> data/raw/natural_counties/dem30.tif
python waterbodies.py     # -> sea.tif (today's tidal water), inland_water.csv
python sheets.py usgs_staten_island_1898 usgs_harlem_1891 usgs_paterson_1888 usgs_oyster_bay_1897 usgs_tarrytown_1892
for a in NJ017 NJ003 NJ013 NJ039 NJ031 NY087 NY119; do python assemble.py $a; done
python assemble.py merge  # -> natural_1609_counties.geojson, natural_stats_counties.json, usgs_sheets_counties.json
python qa.py
```

`view.py`, `viewcls.py`, `probe.py`, `reg_test.py`, `reg_test2.py` are checking tools.
