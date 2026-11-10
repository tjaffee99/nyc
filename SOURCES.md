# Sources

Every dataset the map is built from: where it comes from, its licence, and what it is used
for. Short ids (in `code`) are the values of the `source` fields. Researched tables under
`data/tables/` and `data/manual/` carry a source URL on every row; their READMEs list the
references in full.

## Buildings

| id | What | From | Licence | Used for |
|---|---|---|---|---|
| `nyc_footprints` | Building Footprints (1.08 M outlines; BIN, construction year, measured roof height, ground elevation; photogrammetric, ± 2 ft) | NYC Office of Technology and Innovation, NYC Open Data `5zhs-2jue` — https://data.cityofnewyork.us/d/5zhs-2jue ; metadata https://github.com/CityOfNewYork/nyc-geo-metadata/blob/master/Metadata/Metadata_BuildingFootprints.md | NYC Open Data terms of use (public, no restriction on reuse) | Every building standing today: outline, height, recorded year |
| `pluto` | PLUTO tax lots (year built, floors, building class, attachment) | NYC Department of City Planning, NYC Open Data `64uk-42ks` — https://data.cityofnewyork.us/d/64uk-42ks | NYC Open Data terms of use | Year where the footprint has none; use, storeys, facade material rules |
| `lpc` | Individual Landmark and Historic District Building Database (38,105 buildings: construction date range, primary material, style, architect) | NYC Landmarks Preservation Commission, NYC Open Data `gpmc-yuvp` — https://data.cityofnewyork.us/d/gpmc-yuvp | NYC Open Data terms of use | Construction years (above the assessor's) and wall materials of landmark and historic-district buildings |
| `osm_parts` | OpenStreetMap 3D building parts (set-backs, towers, crowns) | Overture Maps buildings theme, release 2026-10-21.0 — https://overturemaps.org | ODbL (© OpenStreetMap contributors) | Stepped massing of towers where it agrees with the measured roof height |
| `ohm` | OpenHistoricalMap buildings in the map box (documented lost buildings; volunteers' tracings of the Castello Plan 1660, the 1728 survey, Grim 1742, Maerschalck 1755, Dripps 1852, Sanborn and Bromley sheets; NYPL's 1854 footprints of Manhattan to 42nd St) | https://www.openhistoricalmap.org via https://overpass-api.openhistoricalmap.org/api/interpreter, fetched 2026-11-10; `data/manual/ohm/README.md` | CC0 1.0 | What stood before today's buildings; OHM's dates are used only where they are specific to the building |
| `nypl_building_inspector` | Building Inspector: footprints read from the Perris fire-insurance atlases (Manhattan 1857, Brooklyn 1855) and later atlases (1890, 1894) | NYPL Labs / NYC Space/Time Directory — http://spacetime.nypl.org ; https://github.com/nypl-spacetime | CC0 (NYPL public-domain data) | What stood before today's buildings |

The built building files mix OpenStreetMap parts with city data and are offered under ODbL.

### How a building gets its year

1. A researched row (`data/tables/known_building_dates.csv`).
2. The LPC building database (`exact` when the range is two years or less and not "circa").
3. The year on the footprint / tax lot, **if it is not a heap**. Four fifths of the city's
   recorded years sit on 1899, 1900, 1901, 1910, 1915, 1920, 1925, 1930, 1931, 1935, 1940 …:
   the assessor's estimates. A heap year is detected per borough and treated as a range
   ("by 1900", "about 1920"), refined by the recorded years around it, and marked `estimated`.
4. Neighbours of a comparable size.

## Terrain, land and water

| id | What | From | Licence | Used for |
|---|---|---|---|---|
| `3dep` | 1/3 arc-second DEM | US Geological Survey 3D Elevation Program — https://www.usgs.gov/3d-elevation-program | Public domain | Ground elevation |
| `worldcover` | WorldCover 2021 v200, 10 m land cover | European Space Agency — https://esa-worldcover.org | CC BY 4.0 (© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data) | Today's tree canopy, grass, wetland, built-up ground |
| `osm_land` | Land and water polygons (coastline, rivers, lakes), land use (parks, cemeteries, pitches) | OpenStreetMap via Overture Maps base theme, release 2026-10-21.0 | ODbL (© OpenStreetMap contributors) | Today's shoreline and inland water, green outlines |
| `tiger` | County outlines 2024 | US Census Bureau TIGER/Line — https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html | Public domain | The map's extent, borough outlines |
| `nyc_parks` | Parks Properties (outlines, acquisition dates) | NYC Department of Parks and Recreation, NYC Open Data `enfh-gkve` — https://data.cityofnewyork.us/d/enfh-gkve | NYC Open Data terms of use | When each park became a park |

| `ssurgo` | Soil survey of the five counties (NY005, NY047, NY061, NY081, NY085): fill over tidal marsh / reclaimed land | USDA NRCS SSURGO, Web Soil Survey — https://websoilsurvey.nrcs.usda.gov | Public domain | The 1609 marsh and shore outside Manhattan |
| `viele1865` | Egbert Viele, *Sanitary & Topographical Map of the City and Island of New York* (1865): original shore, marsh, ponds, watercourses | Library of Congress, Geography and Map Division — https://www.loc.gov/item/2006629795/ | Public domain | Manhattan's 1609 shore, marshes and streams (georeferenced here, residual ~10 m) |
| `usgs_htmc` | Historical Topographic Map Collection: Harlem 1891 / 1897, Brooklyn 1897, Staten Island 1898, Hempstead 1897, Oyster Bay 1897, Flushing 1947 / 1966, The Narrows 1955 | US Geological Survey — https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/ | Public domain | Shore and marsh before the 20th-century fills; streams; built-up extents of 1889 and 1897; vanished airfields |
| `nypl_maps` | Castello Plan (1660), Grim (1742-44), Ratzer (1766-67), Taylor-Roberts (1797), Dripps (1852, 1867) with the Map Warper's control points | NYPL Digital Collections; NYC Space/Time Directory dump https://s3.amazonaws.com/spacetime-nypl-org/datasets/mapwarper/mapwarper.objects.ndjson | Public domain scans; CC0 control points | Built-up extent snapshots (`data/manual/extents/`) |
| `loc_colton_1836` | Colton, *Topographical Map of the City and County of New-York* (1836) | Library of Congress — https://www.loc.gov/item/2007627512/ | Public domain | Built-up extent of 1836 (Manhattan, Brooklyn, Williamsburgh) |

The natural landscape of 1609 (`data/manual/natural/`), the dated made-land zones
(`data/manual/fill_zones.csv`) and the built-up extents (`data/manual/extents/`) are researched
layers; each has a README with its own sources.

## Transit, streets

| id | What | From | Licence | Used for |
|---|---|---|---|---|
| `osm_rail`, `osm_roads` | Rail and road segments | OpenStreetMap via Overture Maps transportation theme, release 2026-10-21.0 | ODbL | Tracks, streets, bridges |
| `ohm_roads` | Vanished roads with dates (the Bloomingdale Road's old line, lanes on the Central Park site, Brooklyn's town roads, the West Side Elevated Highway) | OpenHistoricalMap | CC0 | Researched routes (`data/manual/routes.csv`); OHM's years are often placeholders and are flagged |
| `highway_dates` | Opening years of highways, parkways and bridge approaches, section by section | Wikipedia articles, nycroads.com (URL per row in `data/manual/routes.csv`, `data/tables/street_dates.csv`) | Facts | Dating today's highway geometry; streets opened at a documented date |
| `mta_gtfs` | Subway GTFS (stations, shapes) | Metropolitan Transportation Authority — https://www.mta.info/developers | MTA developer terms | Stations and service lines |

| `mta_stations` | Subway Stations table | MTA Open Data, data.ny.gov `39hk-dx4f` | MTA / New York State open data terms | Station identifiers and structure |
| `wikidata` | Opening dates of stations | Wikidata — https://www.wikidata.org | CC0 | Cross-check of station dates |
| `ohm_rail` | Dated railway ways (subway segments, the demolished elevated lines) | OpenHistoricalMap | CC0 | Geometry of the Ninth, Sixth, Third and Second Avenue and Brooklyn elevated lines; cross-check of opening dates |

Opening and closing dates of lines and stations: `data/tables/transit_*.csv`, each row with its
source (the Wikipedia station and line articles first, checked against Wikidata and
OpenHistoricalMap). Demolished elevated lines and closed railroads: `data/manual/transit/`
(README there). Where no traced line exists an elevated route follows the centre line of the
street it ran above.

## Tables and research

A source URL on every row. Readmes: `data/tables/places_README.md`, `data/manual/fill_README.md`,
`data/manual/ohm/README.md`; landmark dimensions per model in `data/research/landmarks_*.md`.

| What | From | Licence |
|---|---|---|
| Population 1790–1990 by county (present borough areas) | US Census Bureau, Forstall 1996, *Population of States and Counties of the United States: 1790 to 1990* | Public domain |
| Colonial censuses 1698–1786 by county | US Census Bureau 1909, *A Century of Population Growth*, tables 88–99 — https://archive.org/details/centuryofpopulat00unit | Public domain |
| Population 1900–2010 by borough | NYC Department of City Planning, "Total Population New York City & Boroughs 1900 to 2010" | City publication |
| 2020 counts, Vintage 2025 estimates | US Census Bureau | Public domain |
| Early counts and estimates (New Amsterdam, the occupation) | Museum of the City of New York, New Netherland Institute, Wikipedia articles (URL per row) | Facts only |
| Events, eras, place names, park openings | English Wikipedia articles (URL per row) | CC BY-SA 4.0 (facts and coordinates) |
| Made-land dates (`data/manual/fill_zones.csv`) | Wikipedia articles; Battery Park City Authority Phase 1A archaeological study; East Side Coastal Resiliency FEIS ch. 5.4 (URL per row); ring coordinates from OpenStreetMap street lines via Overture | Facts; ODbL for the geometry |
| Landmark dimensions | Wikipedia articles, NIST NCSTAR 1 (World Trade Center), Carstensen & Gildemeister *New York Crystal Palace* (1854), LPC designation data, OpenHistoricalMap outlines (CC0), OpenStreetMap parts (ODbL) — per model in `data/research/landmarks_*.md` | Facts; CC0 / ODbL for outlines |
| Skyscraper heights and years | CTBUH Skyscraper Center — https://www.skyscrapercenter.com/city/new-york-city ; LPC designation reports https://s-media.nyc.gov/agencies/lpc/lp/NNNN.pdf (2000, 0992, 1273, 0219, 1446, 1530, 1936, 2441, 2582, 1625, 1277, 1664, 0079, 2024, 2067, 0971, 2100) | Facts |
| Bridge dimensions, tower and pier positions | Wikipedia bridge articles; NYC DOT bridge fact pages; OpenStreetMap `bridge:support` outlines (ODbL) | Facts; ODbL |
| Storeys by era (generated and traced buildings) | LPC *Rowhouse Manual* — https://www.nyc.gov/assets/lpc/downloads/pdf/pubs/rowhouse.pdf ; `data/manual/extents/README.md` | Facts |
| Golf course, airport and park-name years | Wikipedia articles, nysga.org, sichamber.com, baysidehistorical.org, airfields-freeman.com (URL per row in `data/tables/golf_courses.csv`, `airports.csv`, `park_names.csv`) | Facts |


## Added in the second round (2026-11)

| id | What | From | Licence | Used for |
|---|---|---|---|---|
| `aerial_1924`, `aerial_1951` | Aerial mosaics of the city, 1924 and 1951 | NYC OTI (1924 from the Department of City Planning, 1951 from the Municipal Archives), ArcGIS tile layers `Ortho_1924_Mosaic` and `NYC_Orthos_1951` (items `afbb5db6b3fd494384357923e6c72622`, `bca6c3f866f844b490925cc9c26d2e40`) | © City of New York, CC BY 4.0 per finder.nyc.gov/nyc-lib/tiles; tiles are not redistributed | `data/manual/aerial/presence.parquet`: was a building on each footprint's outline in 1924 / 1951 |
| `oti_building_historic` | Retired building footprints (demolitions 1996-2026) | NYC OTI building footprints, historic layer — NYC Open Data | NYC Open Data terms of use | Buildings removed since the 1990s (`data/manual/demolished`) |
| `dob_jobs`, `nycha`, `ll84`, `dof_roll`, `hpd_buildings` | New-building jobs and certificates of occupancy; housing authority developments; energy benchmarking filings (owner-reported year); the assessment roll's estimate flag; the housing department's building file with the tenement class (`kj4p-ruqc`) | NYC Department of Buildings, NYCHA, Mayor's Office of Climate, Department of Finance, HPD — NYC Open Data (URL per row; `data/research/building_records.md`) | NYC Open Data terms of use | Recorded years, bounds on estimated years (`data/tables/known_building_dates.records.csv`, `data/manual/records`) |
| `usgs_htmc_farmsteads` | USGS sheets at 1:62,500 surveyed 1888-89 and 1897 (Brooklyn, Harlem, Staten Island, Hempstead, Oyster Bay) and 26 sheets at 1:24,000 of 1947-57 | USGS Historical Topographic Map Collection (GeoPDF); NADCON grid from cdn.proj.org | Public domain; open | Building marks outside the built-up city (`data/manual/farmsteads`), piers (`data/manual/piers`), sites |
| `atlas_traced` | Atlas sheets traced for this map: Harlem 1897, the 23rd ward of the Bronx 1887, the towns of Kings County 1890 | NYPL Digital Collections with the Map Warper's control points (sheet list in `data/manual/atlas`) | Public domain scans; CC0 control points | What stood before today's buildings in those districts |
| `bolton1922`, `bolton1920`, `parker1922`, `danckaerts1679`, `stokes_manatus` | R. P. Bolton, *Indian Paths in the Great Metropolis* (1922) and *New York City in Indian Possession* (1920); A. C. Parker, *The Archeological History of New York* (1922); Jasper Danckaerts' journal (1679-80); I. N. P. Stokes, *Iconography of Manhattan Island* vol. 2 (the Manatus map of 1639) | archive.org (URL per row in `data/tables/early_nyc.csv`; notes in `data/research/early_nyc.md`) | Public domain | Lenape settlements and the colony's outlying farms, mills and villages |
| `tree_inventory` | Forestry tree points and planting spaces (`hn5i-inap`, `82zj-84is`); growth equations: McPherson, van Doorn & Peper 2016, Urban Tree Database (RDS-2016-0005) | NYC Parks — NYC Open Data; USDA Forest Service | NYC Open Data terms of use; public domain | Street and park trees with planting years (`data/research/street_trees.md`) |
| `nj_modiv` | MOD-IV tax list and parcels of Hudson, Bergen, Essex, Union and Passaic counties | New Jersey Office of GIS / Division of Taxation (URLs in `pipeline/counties_nj.py`) | Public | Construction years of the New Jersey counties' buildings |
| `nys_parcels_2025`, `nys_bf`, `cris`, `nys_civil` | NYS Tax Parcels Public (2025 rolls: year built), the state's building footprints, the historic-resource inventory, civil boundaries | New York State GIS (URLs and dates in `data/research/counties_ny.md`) | "Available to the public", as-is | Construction years in Rockland and the dated municipalities of Westchester |
| `overture_region` | Every Overture footprint, land, water, land use, roads, rail of the wider box | Overture Maps release 2026-10-21.0 (OpenStreetMap, Microsoft footprints) | ODbL / CDLA | Footprints, streets, tracks, greens of the counties |
| `ssurgo_counties`, `usgs_counties` | Soil survey of the seven counties; USGS sheets Paterson 1888, Harlem 1891, Staten Island 1898, Tarrytown 1892 | USDA NRCS; USGS | Public domain | The landscape of 1609 in the counties (`data/manual/natural/counties`) |
| `osm_overpass`, `ohm_region`, `wikidata_stations`, `path_gtfs` | Stations, route relations and abandoned railways; dated railway ways; station opening dates; PATH schedule | OpenStreetMap via Overpass (ODbL); OpenHistoricalMap (CC0); Wikidata (CC0); Port Authority GTFS (data.trilliumtransit.com/gtfs/path-nj-us) | as stated | Railroads, PATH and light rail of the counties (`data/manual/transit/README.md`) |
| `airfields_freeman` | Abandoned & Little-Known Airfields | airfields-freeman.com (page URL per row) | Facts only | Vanished airfields of the counties |
| county tables | NJ Department of State 1906, *Compendium of Censuses 1726-1905* (archive.org/details/101270621.nlm.nih.gov); Samuel Smith 1765, *History of the Colony of Nova-Caesaria*; Census Bureau county totals; English Wikipedia articles for places, events, parks, highways, lines and stations (URL per row) | as cited per row | Public domain; CC BY-SA 4.0 (facts) | Population, labels, events, park, highway and railroad dates of the counties |

Made-land dates of the counties: `data/manual/fill_counties_README.md` (a source per zone).
Military and industrial sites: `data/manual/sites/README.md`. Story captions:
`data/tables/story_README.md`.
