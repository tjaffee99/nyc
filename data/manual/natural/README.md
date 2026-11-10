# The natural landscape of the five boroughs, c.1609

What was land, water and marsh before any filling, and what covered the low ground.
Made 2026-11-10. Everything here is derived from three public-domain maps; nothing is drawn by hand
and nothing is generated.

## Files

| file | what |
|---|---|
| `natural_1609.geojson` | polygons (WGS84), 3.7 MB. Properties: `cover` (water, tidal_marsh, tidal_flat, beach, dunes, pond, freshwater_wetland), `source`, `confidence` (high / medium / low), `note`, `borough` (extra, for the statistics) |
| `streams_1609.geojson` | lines (WGS84), 0.6 MB. Properties: `name`, `source`, `confidence`, `ref` (URL for the name, empty if none was verified), `name_basis` |
| `natural_stats.json` | counts and hectares per borough and cover (written by `tools/assemble.py`) |
| `viele_georef.json`, `viele_residuals.json` | the georeference of the Viele map (pixel to UTM 18N polynomial) and its residual per street |
| `usgs_sheets.json` | per USGS sheet: the shift applied, and the accuracy of the marsh / water discriminant |
| `tools/` | the scripts (see "Reproducing") |

Only what was **not dry upland** is written. Every cell of today's land that no polygon covers was dry
ground in 1609 (the terrain stage's "forest" fallback). No `forest`, `grassland`, `shrub` or `rock`
polygons are delivered: I found no openly usable source that maps the upland vegetation (see Welikia below).

"Land today" means the land of the soil survey (everything that is not its `Water` unit, piers included).
Open water today is not covered: the stage already knows it is water. The 1609 land outline is therefore
`today's land − (water ∪ tidal_marsh ∪ tidal_flat polygons)`, marsh counted as not-land.

## Sources used

| id in `source` | what | URL | licence |
|---|---|---|---|
| `viele1865` | Egbert L. Viele, *Topographical map of the City of New York : showing original water courses and made land*, 1865. Library of Congress scan, IIIF at half size (9853 × 3027 px, about 2.05 m per pixel) | https://www.loc.gov/item/2006629795/ (image: https://tile.loc.gov/image-services/iiif/service:gmd:gmd380:g3804:g3804n:ct002003/full/pct:50/0/default.jpg) | public domain; LoC: "free to use and reuse", credit "Library of Congress, Geography and Map Division" |
| `ssurgo` | USDA NRCS Soil Survey Geographic database, survey areas NY005 Bronx, NY047 Kings, NY061 New York, NY081 Queens, NY085 Richmond (the New York City soil survey; versions saved 2026-08-31 to 2026-09-03) | zips: `https://websoilsurvey.sc.egov.usda.gov/DSD/Download/Cache/SSA/wss_SSA_NY061_[2026-09-01].zip` and the four others (dates from Soil Data Access, https://sdmdataaccess.sc.egov.usda.gov/) | public domain (US Government work) |
| `usgs_harlem_1891` | USGS 1:62,500 Harlem sheet, 1891 print | https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/NY/NJ_Harlem_472515_1891_62500_geo.tif | public domain (USGS Historical Topographic Map Collection) |
| `usgs_brooklyn_1897` | Brooklyn sheet, 1897 print | …/GeoTIFF/NY/NY_Brooklyn_123118_1897_62500_geo.tif | same |
| `usgs_staten_island_1898` | Staten Island sheet, 1898 print | …/GeoTIFF/NY/NJ_Staten%20Island_255388_1898_62500_geo.tif | same |
| `usgs_hempstead_1897` | Hempstead sheet (Queens east of 73°45′ W, south half) | …/GeoTIFF/NY/NY_Hempstead_129886_1897_62500_geo.tif | same |
| `usgs_oyster_bay_1897` | Oyster Bay sheet (Queens east of 73°45′ W, north half) | …/GeoTIFF/NY/NY_Oyster%20Bay_136363_1897_62500_geo.tif | same |
| (`usgs_paterson_1888`) | Paterson sheet (Hudson shore of Manhattan west of 74°00′ W, north of 40°45′); processed, but no polygon came out of it | …/GeoTIFF/NJ/NJ_Paterson_255310_1888_62500_geo.tif | same |
| `tiger_ny_enclave` | Census TIGER/Line 2024 county boundary: the New York enclave on Ellis Island (4.68 acres) | project file `data/raw/tiger/tl_2024_us_county.zip` (https://www2.census.gov/geo/tiger/TIGER2024/COUNTY/) | public domain |
| — | Overture Maps 2026-10-21.0 roads (georeferencing, checks) and the Ellis Island islet polygon | project files `data/raw/overture/2026-10-21.0/` | ODbL (OpenStreetMap-derived) for these themes |

The edition year of each USGS sheet is the print's year. I did **not** read the survey years off the sheet
margins; the surveys are a few years older than the prints. The 1897 Harlem and 1889 Brooklyn prints were
also downloaded and rejected: the "1897" Harlem scan is a later revised reprint (it shows Rikers Island
already enlarged and the borough lines of 1898), the 1889 Brooklyn scan is too pale to classify. The 1897
Brooklyn print shows the Bergen Beach development of the 1890s, so it is not untouched there.

## Sources evaluated and not used

- **Welikia / Mannahatta** (https://www.welikia.org/resources, now maintained by the New York Botanical
  Garden): the data-download section reads "Updated geographic data coming soon" for both the geographic
  data and the elevation models — nothing is downloadable (checked 2026-11-10). Use of the map explorer is
  subject to NYBG's terms and conditions. Not scraped, not used. It remains the best possible source for
  the upland vegetation and should replace the fallback if it is published.
- **NYPL Map Warper** (https://maps.nypl.org/warper/): redirects to an Archive-It capture; the service is
  no longer live. Not used. The Viele map was georeferenced here instead.
- **Wikimaps Warper**: HTTP 403 to this client. **web.archive.org**: blocked by the session's network policy.
- **NOAA historical T-sheet shorelines and charts** (nsde.ngs.noaa.gov, historicalcharts.noaa.gov): the
  hosts answer, but I did not get to them. They would improve on the USGS sheets (earlier and larger
  scale) and are the obvious next step for the Brooklyn / Queens East River front.
- **British Headquarters Map (c.1782)**, **David Rumsey** scans (CC BY-NC-SA): not used.

## Method

All metric work in UTM 18N. Grids: Viele 3 m, USGS mosaic and assembly 6 m.

### Manhattan island (`viele1865`)

1. **Georeference** (`viele_georef.py`). The scan is two sheets joined at x ≈ 4937 px; each half gets
   its own second-order polynomial. Start: two points read off the scan (centre of the Union Square oval,
   centre of the old Receiving Reservoir = Great Lawn). Refinement: the map's black line work is reduced
   to straight runs ≥ 63 m (which keeps street / block lines and drops hachures and lettering) and the
   transform is optimised so that those lines lie one kerb offset (about 11 m) from today's street
   centrelines (Overture roads).
   **Residual** (`viele_residual.py`, 47 long streets, measured as the offset of the axis of symmetry of
   Viele's two kerb lines from today's centreline): across the island (17 avenues) median 8 m, RMS 14 m;
   along the island (30 cross streets) median 7 m, RMS 10 m; worst about 25 m (the method saturates
   there, and 5 of 17 avenues sit near that limit). Three overlays were also eyeballed (Union Square,
   Harlem at 135th–147th St, the Financial District). The inset of the scan (the north tip of the
   island, beyond about Dyckman Street) is not used: that part falls to the citywide method.
2. **Classes by colour** (`viele_classify.py`), on the scan with the black ink masked out: pale tint =
   upland, salmon = Viele's "made land", green = marsh and the green band he washes along every
   watercourse, blue = ponds and river edge, cream = river.
3. **1609 land** (`manhattan.py`) = the largest connected body of upland + green, holes filled.
   The soil survey is a veto: cells more than 25 m inside a unit that records original dry ground
   (natural soils, urban land over till or outwash) are land whatever the colour says.
   `water` = today's island minus that land (so: Viele's made land, plus everything filled after 1865).
   Marsh = green wider than 84 m (narrower green is a watercourse band, about 50 m wide on the map) and
   ≥ 1.2 ha; `tidal_marsh` if within 120 m of the original shore or on the soil survey's "tidal marsh
   substratum", else `freshwater_wetland`. `pond` = blue inside the land (the Collect and Little
   Collect, the pond at Beekman's Swamp, …), minus the two Central Park reservoirs Viele also draws.
4. **Streams** = centre lines (thinning) of the green watercourse bands.

### Everywhere else (`ssurgo` + USGS sheets)

The soil survey maps what is under the city. Per map unit:

| soil survey unit | written as |
|---|---|
| *Urban land, tidal marsh substratum* (UmA, UmB) | `tidal_marsh`, medium |
| *Urban land, reclaimed substratum* (UrA) | where the 1890s sheet still shows it wet: what the sheet shows; where already filled: `water` within 150 m of open tidewater (water ≥ 120 m wide today), `tidal_marsh` (low, **estimated**) farther in — the survey does not say whether fill went into water or onto creek-side marsh (Gowanus, Newtown Creek, Wallabout, Red Hook) |
| tidal-marsh soils (Ipswich, Pawcatuck, Matunuck, Westbrook, Appoquinimink, Sandyhook) | `tidal_marsh`, high — still marsh today |
| Wassents tidal flat, Nagunt intertidal | `tidal_flat` |
| Catden, Natchaug, Timakwa, Wallkill, Preakness, Hasbrouck, Limerick, … | `freshwater_wetland` |
| Beaches; Hooksan / dune land | `beach` / `dunes` (low), unless the sheet shows water or marsh there |
| fill soils that do not say what they cover (Laguardia, Ebbets, Bigapple, Fortress, Jamaica, Barren, Verrazano, Freshkills, Greatkills, Secaucus, …, *sandy substratum*) | what the 1888–1898 USGS sheet shows: `water`, marsh, or dry |
| natural upland soils, urban land over till / outwash, upland fills (Greenbelt, …) | dry; except blocks ≥ 2 ha that the sheet shows wet ≥ 36 m inside the unit (low) |

**USGS sheets** (`usgs_sheets.py`): blue ink = `B − R` above a per-sheet threshold; *wet* = blue density
over 48 m > 18 %, thin lines removed. *Registration*: each sheet is shifted so that the edge of its wet
mask best coincides with today's shoreline (cross-correlation of the two edge images within ± 160 m);
shifts applied: Harlem 58 m W / 74 m S, Brooklyn 42 m W / 16 m S, Staten Island 48 m W / 69 m N,
Hempstead 37 m W / 26 m S, Oyster Bay 32 m W / 132 m N, Paterson 69 m E / 48 m S (they include the
NAD27 datum offset). *Marsh against water*: a linear discriminant on print texture, trained per sheet on
cells whose answer the soil survey gives (open water today → water; marsh soils and tidal-marsh
substratum → marsh). Accuracy on those cells, water / marsh: Harlem 0.87 / 0.89, Brooklyn 0.84 / 0.98,
Staten Island 0.95 / 0.97, Hempstead 0.73 / 0.81; Oyster Bay and Paterson have too few labelled cells and
use a fixed rule. Marsh narrower than 120 m is written as water (the first water lines along a shore
read as marsh). Marsh not connected to the sea through water or marsh is `freshwater_wetland`, enclosed
water is `pond` (five reservoirs excluded by hand).
**Streams** outside Manhattan = thin blue lines on dry land plus water channels under 70 m wide on the
sheets, thinned to centre lines, ≥ 300 m per connected group.

**Ellis Island** is outside the New York soil survey: today's island (Overture) minus the New York
enclave of the state line (the island as it stood in 1834, per *New Jersey v. New York*, 1998) is
written as `water`. Liberty Island is not covered (no polygon: it stays dry at today's outline).

## Checks made (`tools/qa_checks.py`, `tools/viele_residual.py`)

- Pearl Street (Whitehall to Peck Slip): 37 % of the centreline inside 1609 water, median 7 m landward
  of the shore (p10 −24 m, p90 +53 m). Greenwich Street (Battery to Canal): median 15 m inside the
  water, i.e. the shore runs about 15 m east of the centreline.
- Soil survey's reclaimed / upland boundary against the Viele-traced shore, Manhattan: median 24 m,
  75th percentile 36 m (two independent renderings of the same shore).
- Point tests (26 points, `qa_checks.py`). As expected: Collect (Centre & Worth) pond; Canal & West
  Broadway and Avenue C & 10th tidal marsh; Battery Park City, Front Street, LaGuardia, the east of
  Rikers Island, the south of Governors Island water; Flushing Meadows, JFK, Co-op City, Floyd Bennett
  Field, the Navy Yard, Red Hook, Greenpoint by Newtown Creek, the filled part of Coney Island Creek
  tidal marsh; the Fresh Kills landfill point water (wet, but I expected marsh); Times Square, City Hall
  Park, Prospect Park, Fort Jay dry.
  Three points I expected wet came back dry, and were looked into: East 108th St & 2nd Avenue is 118 m
  from the nearest marsh polygon (Viele tints that corner upland; the Harlem marsh is written at East
  107th & 1st Avenue as tidal marsh and at East 109th & 3rd Avenue); the Hunts Point market point lies
  on "Urban land, till substratum"; the Gowanus point (3rd Avenue & 3rd Street) fell in the canal's own
  water unit, 9 m from the `water` polygon. The Randalls Island centre point and Liberty Island are dry.
- Governors Island: 53 acres dry in 1609, against about 70 acres usually given (the line is the soil
  survey's; 25 % low, equivalent to a shore about 25–30 m too far in all round).
- Rikers Island: 126 acres dry, against the "under 90 acres" usually given (not verified here): filling
  with refuse began in the 1880s, before the 1891 print, and the sheet is the earliest evidence used.
- The Collect: 8.7 + 3.3 acres of pond (plus 3.0 acres at Beekman's Swamp) — only what Viele tints blue;
  the 48 acres often quoted for the Collect would include the marsh round it.
- Manhattan (soil-survey area NY061: the island plus Randalls / Wards, Roosevelt and Governors islands):
  2,851 acres of water or tidal marsh in 1609 that are developed land today — inside the 2,000–3,000
  acres usually quoted.

## Accuracy I believe was reached (position of the 1609 shore / marsh edge)

| area | basis | estimate |
|---|---|---|
| Manhattan below about Dyckman St | Viele 1865, georeference residual 7–8 m median, 10–14 m RMS; Viele's own compilation of older surveys is unknown | **± 25 m** typical, 50–60 m worst (pier-head areas, places where the tint is faint) |
| Manhattan north tip, Randalls / Wards, Roosevelt, Governors | soil survey + Harlem 1891 / Brooklyn 1897 sheets | ± 40 m |
| Brooklyn | East River / Gowanus / Red Hook: soil survey (1:12,000 mapping of a buried shore); Jamaica Bay, Coney Island, Sheepshead Bay: Brooklyn 1897 sheet | ± 30–40 m (soil survey), ± 40–60 m (sheet) |
| Queens | Newtown Creek / Long Island City: soil survey; Flushing Meadows, Flushing Bay, Jamaica Bay, JFK, Rockaways: sheets | ± 40–60 m; **± 60–130 m** east of 73°45′ W (Hempstead / Oyster Bay sheets: little city shoreline to register on, Oyster Bay shift of 132 m is not trustworthy) |
| Bronx | Harlem 1891 sheet + soil survey | ± 40–60 m |
| Staten Island | Staten Island 1898 sheet + soil survey | ± 40–60 m |

The marsh / water split is weaker than the land / not-land line everywhere outside Manhattan
(`confidence` low on sheet-derived marsh; see the discriminant accuracies above).

## What is uncertain, and what is not 1609

- **The sheets are 1888–1898, not 1609.** Outside the built-up waterfronts the shore of the 1890s is
  taken as the natural one. Natural change is not reconstructed: the Rockaway peninsula and Coney Island
  have grown westward since 1609 (land west of the 1890s point is `water` here, but the 1609 point lay
  farther east still), marsh islands in Jamaica Bay have changed, inlets have moved. `beach` and `dunes`
  are today's, marked low.
- **Fill made before the sheets and not recorded by the soil survey is missing.** The soil survey's
  "reclaimed" / "tidal marsh substratum" units are the only evidence for the Brooklyn and Queens East
  River front, Gowanus, Wallabout, Newtown Creek, Mott Haven and Port Morris; where the survey maps a
  housing estate or a park as a Laguardia or Greenbelt complex instead, an old shore under it is lost.
  Mill Brook (Bronx) was already sewered and does not appear.
- **Reclaimed substratum is not always former open water**; the 150 m rule that turns its interior into
  salt marsh is an estimate (noted in each polygon).
- **Rikers Island** as above; **Governors Island** 25 % small; **Liberty Island** not treated; the New
  Jersey part of Ellis Island comes from the state line, not from a map of 1609.
- **Paper-white open water**: far from shore the sheets' water lining thins to bare paper. Dry-looking
  patches ≥ 20 ha that are mostly water today, and patches < 3 ha on fill soils touching no upland soil,
  are treated as water; a bare islet smaller than 3 ha on what is now fill would be lost, and a patch
  between 3 and 20 ha inside a fill would wrongly stay dry (none seen in the areas I looked at: upper
  East River, Governors Island, Jamaica Bay, Staten Island, Bronx — at overview scale only).
- **Streams**: the Manhattan lines are fragments (502 pieces, 78 km) broken at confluences and where
  streets interrupt the green band; not joined into single named features. Sheet-derived lines (1,181
  pieces, 286 km) include some non-stream blue ink and are `low`. **Names** are attached by proximity
  to a named place (radius 300–1500 m), so a named set can include neighbouring tributaries.
  `ref` is filled only where the Wikipedia article was confirmed to exist (2026-11-10); "Saw Kill",
  "Harlem Creek", "Montayne's Rivulet" and "Fresh Creek" are from general knowledge with no reference
  verified. No line was found for the Lispenard drain or Mill Brook.
- **Freshwater wetlands and ponds** are incomplete outside Manhattan: only what the soil survey still
  maps as wet soil or the sheets show as marsh or water on what is now fill.
- Not checked: the survey dates of the sheets; every borough at street scale (only the windows listed
  above were looked at); the Paterson, Hempstead and Oyster Bay pieces visually.

## For the terrain stage

- Polygons of different covers do not overlap (they come from one raster), apart from slivers ≤ 6 m
  where the Viele area meets the citywide method. If an order is needed: `pond` > `freshwater_wetland` >
  `tidal_marsh` > `tidal_flat` > `beach` > `dunes` > `water`.
- Not-land in 1609 = `water`, `tidal_marsh`, `tidal_flat` (and `pond`). `beach` and `dunes` are land.
- No polygon = dry upland (fallback forest). No polygon over today's water.
- For made-land dating: a polygon with `confidence` = high and `source` = ssurgo is marsh that still
  exists; every other `water` / `tidal_marsh` polygon is land today and needs a fill year.
- Piers count as land in the soil survey, so pier decks carry `water` polygons.

## Reproducing

```
cd data/manual/natural/tools
../../../../.venv/bin/python download.py        # SSURGO zips, 6 GeoTIFFs, Viele scan -> data/raw/natural/
../../../../.venv/bin/python ssurgo_load.py     # -> data/interim/natural/ssurgo_all.parquet
../../../../.venv/bin/python viele_georef.py    # ~2 min -> viele_georef.json (copy kept beside this README)
../../../../.venv/bin/python viele_residual.py  # residual per street
../../../../.venv/bin/python viele_classify.py  # -> viele_class.tif
../../../../.venv/bin/python manhattan.py       # -> manhattan_polys / streams / coverage
../../../../.venv/bin/python usgs_sheets.py     # ~4 min, ~2 GB peak -> usgs_1890s.tif, usgs_sheets.json
../../../../.venv/bin/python assemble.py        # ~5 min -> natural_1609.geojson, streams_1609.geojson
../../../../.venv/bin/python qa_checks.py
```

Paths are absolute (`/home/user/nyc`). Packages: those of the project venv (numpy, scipy, rasterio,
geopandas, shapely, pyproj, duckdb, pillow, requests). `viewmap.py`, `qa_city.py`, `qa_man.py`,
`viele_overlay.py`, `crop.py`, `imcrop.py` only draw pictures for checking. `sda.py` is the Soil Data
Access client.

## Counts and areas (written from `natural_stats.json`)

Polygons / hectares by borough (soil-survey area) and cover:

| borough | water | tidal_marsh | tidal_flat | freshwater_wetland | pond | beach | dunes |
|---|---|---|---|---|---|---|---|
| Manhattan | 57 / 792 | 51 / 363 | 2 / 5 | 17 / 62 | 18 / 14 | – | – |
| Brooklyn | 206 / 426 | 226 / 3096 | 20 / 213 | 5 / 13 | 6 / 5 | 6 / 10 | 10 / 12 |
| Queens | 281 / 748 | 275 / 5119 | 26 / 108 | 22 / 75 | 24 / 65 | 6 / 68 | 6 / 96 |
| Bronx | 179 / 477 | 183 / 1239 | 1 / 1 | 18 / 35 | 7 / 8 | – | – |
| Staten Island | 182 / 376 | 211 / 2100 | 1 / 10 | 117 / 354 | 12 / 17 | 1 / 4 | 3 / 5 |
| Ellis Island (New Jersey side) | 1 / 9 | – | – | – | – | – | – |

Water or tidal marsh c.1609 that is developed land today (existing marsh excluded):

| borough | was water, ha | was tidal marsh, ha | total ha | total acres |
|---|---|---|---|---|
| Manhattan | 792 | 362 | 1154 | 2851 |
| Brooklyn | 426 | 2930 | 3356 | 8293 |
| Queens | 748 | 4551 | 5299 | 13094 |
| Bronx | 477 | 1144 | 1621 | 4006 |
| Staten Island | 376 | 1460 | 1836 | 4537 |
| Ellis Island (New Jersey side) | 9 | 0 | 9 | 23 |
| all | 2827 | 10448 | 13275 | 32803 |

`natural_1609.geojson`: 2180 polygons; by source: ssurgo 766, usgs_harlem_1891 479, usgs_brooklyn_1897 440, usgs_staten_island_1898 381, viele1865 69, usgs_hempstead_1897 37, usgs_oyster_bay_1897 7, tiger_ny_enclave 1; by confidence: medium 1123, low 885, high 172.
`streams_1609.geojson`: 1683 lines, 365 km; by source: usgs_staten_island_1898 658, viele1865 502, usgs_harlem_1891 252, usgs_brooklyn_1897 241, usgs_hempstead_1897 20, usgs_oyster_bay_1897 10.
